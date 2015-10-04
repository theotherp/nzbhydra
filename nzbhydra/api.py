from collections import namedtuple
from itertools import groupby
import logging
from io import BytesIO

from flask import request, send_file
from furl import furl
from marshmallow import Schema, fields
from requests import RequestException

from nzbhydra import config
from nzbhydra.config import ResultProcessing, DownloaderSettings
from nzbhydra import providers
from nzbhydra.database import ProviderApiAccess, ProviderNzbDownload, Provider

logger = logging.getLogger('root')

categories = {'Console': {'code': [1000, 1010, 1020, 1030, 1040, 1050, 1060, 1070, 1080], 'pretty': 'Console'},
              'Movie': {'code': [2000, 2010, 2020], 'pretty': 'Movie'},
              'Movie_HD': {'code': [2040, 2050, 2060], 'pretty': 'HD'},
              'Movie_SD': {'code': [2030], 'pretty': 'SD'},
              'Audio': {'code': [3000, 3010, 3020, 3030, 3040], 'pretty': 'Audio'},
              'PC': {'code': [4000, 4010, 4020, 4030, 4040, 4050, 4060, 4070], 'pretty': 'PC'},
              'TV': {'code': [5000, 5020], 'pretty': 'TV'},
              'TV_SD': {'code': [5030], 'pretty': 'SD'},
              'TV_HD': {'code': [5040], 'pretty': 'HD'},
              'XXX': {'code': [6000, 6010, 6020, 6030, 6040, 6050], 'pretty': 'XXX'},
              'Other': {'code': [7000, 7010], 'pretty': 'Other'},
              'Ebook': {'code': [7020], 'pretty': 'Ebook'},
              'Comics': {'code': [7030], 'pretty': 'Comics'},
              }


def find_duplicates(results):
    """

    :type results: list[NzbSearchResult]
    """
    # TODO we might want to be able to specify more precisely what item we pick of a group of duplicates, for example by indexer priority 

    # Sort and group by title. We only need to check the items in each individual group against each other because we only consider items with the same title as possible duplicates
    sorted_results = sorted(results, key=lambda x: x.title.lower())
    grouped_by_title = groupby(sorted_results, key=lambda x: x.title.lower())
    grouped_by_sameness = []

    for key, group in grouped_by_title:
        seen2 = set()
        group = list(group)
        for i in range(len(group)):
            if group[i] in seen2:
                continue
            seen2.add(group[i])
            same_results = [group[i]]  # All elements in this list are duplicates of each other 
            for j in range(i + 1, len(group)):
                if group[j] in seen2:
                    continue
                seen2.add(group[j])
                if test_for_duplicate(group[i], group[j]):
                    same_results.append(group[j])
            grouped_by_sameness.append(same_results)

    return grouped_by_sameness


def test_for_duplicate(search_result_1, search_result_2):
    """

    :type search_result_1: NzbSearchResult
    :type search_result_2: NzbSearchResult
    """

    if search_result_1.title.lower() != search_result_2.title.lower():
        return False
    size_threshold = config.get(ResultProcessing.duplicateSizeThresholdInPercent)
    size_difference = search_result_1.size - search_result_2.size
    size_average = (search_result_1.size + search_result_2.size) / 2
    size_difference_percent = abs(size_difference / size_average) * 100


    # TODO: Ignore age threshold if no precise date is known or account for score (if we have sth like that...) 
    age_threshold = config.get(ResultProcessing.duplicateAgeThreshold)
    same_size = size_difference_percent <= size_threshold
    same_age = abs(search_result_1.epoch - search_result_2.epoch) / (1000 * 60) <= age_threshold  # epoch difference (ms) to minutes

    # If all nweznab providers would provide poster/group in their infos then this would be a lot easier and more precise
    # We could also use something to combine several values to a score, say that if a two posts have the exact size their age may differe more or combine relative and absolute size comparison
    if same_size and same_age:
        return True


class ProviderSchema(Schema):
    name = fields.String()
    module = fields.String()
    enabled = fields.Boolean()
    settings = fields.String()


class NzbSearchResultSchema(Schema):
    title = fields.String()
    link = fields.String()
    epoch = fields.Integer()
    pubdate_utc = fields.String()
    age_days = fields.Integer()
    age_precise = fields.Boolean()
    provider = fields.String()
    guid = fields.String()
    size = fields.Integer()
    category = fields.String()
    has_nfo = fields.Boolean()


class ProviderApiAccessSchema(Schema):
    provider = fields.Nested(ProviderSchema, only="name")
    time = fields.DateTime()
    type = fields.String()
    url = fields.String()
    response_successful = fields.Boolean()
    response_time = fields.Integer()
    error = fields.String()


class ProviderSearchSchema(Schema):
    provider = fields.Nested(ProviderSchema, only="name")
    time = fields.DateTime()
    successful = fields.Boolean()
    results = fields.Integer()

    api_accesses = fields.Nested(ProviderApiAccessSchema, many=True)


# todo: thsi needs to be expanded when we support reverse proxies / global urls / whatever
def get_root_url():
    return request.url_root


def transform_links(results, dbsearchid):
    if config.get(DownloaderSettings.nzbaccesstype) == DownloaderSettings.NzbAccessTypeOptions.direct.value:  # We don't change the link, the results lead directly to the NZB
        return results

    for i in results:
        f = furl(get_root_url())
        f.path.add("internalapi")
        f.add({"t": "getnzb", "provider": i.provider, "guid": i.guid, "searchid": dbsearchid, "title": i.title})
        i.link = f.url

    return results


def process_for_external_api(results):
    results = transform_links(results, "todo")
    return results


def process_for_internal_api(search_result):
    # results: list of dicts, <provider>:dict "providersearchdbentry":<ProviderSearch>,"results":[<NzbSearchResult>]
    nzbsearchresults = []
    providersearchdbentries = []
    for results_and_dbentry in search_result["results"].values():
        nzbsearchresults.extend(results_and_dbentry.results)
        providersearchdbentries.append(ProviderSearchSchema().dump(results_and_dbentry.dbentry).data)

    nzbsearchresults = transform_links(nzbsearchresults, search_result["dbsearchid"])

    grouped_by_sameness = find_duplicates(nzbsearchresults)

    # Will be sorted by GUI later anyway but makes debugging easier
    results = sorted(grouped_by_sameness, key=lambda x: x[0].epoch, reverse=True)
    serialized = []
    for g in results:
        serialized.append(serialize_nzb_search_result(g).data)

    # We give each group of results a unique count value by which they can be identified later even if they're "taken apart"
    for count, group in enumerate(serialized):
        for i in group:
            i["count"] = count
    return {"results": serialized, "providersearches": providersearchdbentries, "searchentryid": search_result["dbsearchid"]}


def serialize_nzb_search_result(result):
    return NzbSearchResultSchema(many=True).dump(result)


def get_nfo(provider_name, guid):
    nfo = None
    result = {}
    for p in providers.providers:
        if p.name == provider_name:
            nfo = p.get_nfo(guid)
            break
    else:
        logger.error("Did not find provider with name %s" % provider_name)
        result["error"] = "Unable to find provider"
    if nfo is None:
        logger.info("Unable to find NFO for provider %s and guid %s" % (provider_name, guid))
        result["has_nfo"] = False
    else:
        result["has_nfo"] = True
        result["nfo"] = nfo
    return result


def get_nzb_link(provider_name, guid, title, searchid):
    """
    Build a link that leads to the actual NZB of the provider using the given informations. We log this as provider API access and NZB download because this is only called
    when the NZB will be actually downloaded later (by us or a downloader) 
    :return: str
    """
    for p in providers.providers:
        if p.name == provider_name:
            link = p.get_nzb_link(guid, title)

            # Log to database
            provider = Provider.get(Provider.name == provider_name)
            papiaccess = ProviderApiAccess(provider=p.provider, type="nzb", url=link, response_successful=None, provider_search=provider)
            papiaccess.save()
            pnzbdl = ProviderNzbDownload(provider=provider, provider_search=searchid, api_access=papiaccess, mode="redirect")
            pnzbdl.save()

            return link

    else:
        logger.error("Did not find provider with name %s" % provider_name)
        return None


ProviderNzbDownloadResult = namedtuple("ProviderNzbDownload", "content headers")





def download_nzb_and_log(provider_name, guid, title, searchid) -> ProviderNzbDownloadResult:
    """
    Gets the NZB link from the provider using the guid, downloads it and logs the download

    :param provider_name: name of the provider
    :param guid: guid to build link
    :param title: the title to build the link
    :param searchid: the id of the ProviderSearch entry so we can link the download to a search
    :return: ProviderNzbDownloadResult
    """
    for p in providers.providers:
        if p.name == provider_name:

            link = p.get_nzb_link(guid, title)
            provider = Provider.get(Provider.name == provider_name)
            papiaccess = ProviderApiAccess(provider=p.provider, type="nzb", url=link, provider_search=provider)
            papiaccess.save()
            pnzbdl = ProviderNzbDownload(provider=provider, provider_search=searchid, api_access=papiaccess, mode="serve")
            pnzbdl.save()
            try:
                r = p.get(link)
                r.raise_for_status()

                papiaccess.response_successful = True
                papiaccess.response_time = r.elapsed.microseconds / 1000

                return ProviderNzbDownloadResult(content=r.content, headers=r.headers)
            except RequestException as e:
                logger.error("Error while connecting to URL %s: %s" % (link, str(e)))
                papiaccess.error = str(e)
                return None
            finally:
                papiaccess.save()
    else:
        return "Unable to find NZB link"


def get_nzb_response(provider_name, guid, title, searchid):
    nzbdownloadresult = download_nzb_and_log(provider_name, guid, title, searchid)
    if nzbdownloadresult is not None:
        bio = BytesIO(nzbdownloadresult.content)
        filename = title + ".nzb" if title is not None else "nzbhydra.nzb"
        response = send_file(bio, mimetype='application/x-nzb;', as_attachment=True, attachment_filename=filename, add_etags=False)
        response.headers["content-length"] = len(nzbdownloadresult.content)

        for header in nzbdownloadresult.headers.keys():
            if header.lower().startswith("x-dnzb") or header.lower() in ("content-disposition", "content-type"):
                response.headers[header] = nzbdownloadresult.headers[header]
        return response
    else:
        return "Unable to download NZB", 500
        
    
        
    
