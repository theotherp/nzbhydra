from collections import namedtuple
from itertools import groupby
import json
import logging
from io import BytesIO
import urllib

from flask import request, send_file
from furl import furl
from marshmallow import Schema, fields
from requests import RequestException

from nzbhydra import config
from nzbhydra.config import resultProcessingSettings, downloaderSettings, NzbAccessTypeSelection
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
    sorted_results = sorted(results, key=lambda x: x.title.lower())
    grouped_by_title = groupby(sorted_results, key=lambda x: x.title.lower())
    grouped_by_sameness = []
    for key, group in grouped_by_title:
        group = list(group)
        #Elements cannot be duplicates of themselves...
        if len(group) == 1:
            grouped_by_sameness.append(group)
            continue
        #Sort by epoch
        group = sorted(group, key=lambda x: x.epoch)
        subgroups = []
        subgroup = set()
        for i in range(len(group) - 1):
            #Go through the group
            a = group[i]    
            b = group[i + 1]
            subgroup.add(a)
            if a.provider == b.provider:
                same = False
            else:
                same = test_for_duplicate_age(a, b)
            #If two elements are duplicates add them to the current set
            if same:
                subgroup.add(b)
            #Otherwise start a new set
            else:
                if len(subgroup) > 0:
                    subgroups.append(list(subgroup))
                subgroup = set()
                subgroup.add(b)
        #Add the last set if it contains elements
        if len(subgroup) > 0:
            subgroups.append(list(subgroup))
        
        #Do the same with size for the subgroups which contain potential duplicates.  
        for group in subgroups:
            if len(group) == 1:
                grouped_by_sameness.append(group)
                continue
            group = sorted(group, key=lambda x: x.size)
            subgroups = []
            subgroup = set()
            for i in range(len(group) - 1):
                a = group[i]    
                b = group[i + 1]
                subgroup.add(a)
                same_size = test_for_duplicate_size(a, b)
                if same_size:
                    subgroup.add(b)
                else:
                    if len(subgroup) > 0:
                        subgroups.append(list(subgroup))
                    subgroup = set()
                    subgroup.add(b)
            grouped_by_sameness.extend(subgroups)
            if len(subgroup) > 0:
                grouped_by_sameness.append(list(subgroup))
    return grouped_by_sameness
            
  


def test_for_duplicate_age(search_result_1, search_result_2):
    """

    :type search_result_1: NzbSearchResult
    :type search_result_2: NzbSearchResult
    """
    age_threshold = config.resultProcessingSettings.duplicateAgeThreshold.get()
    if search_result_1.epoch is None or search_result_2.epoch is None:
        return False
    same_age = abs(search_result_1.epoch - search_result_2.epoch) / (1000 * 60) <= age_threshold  # epoch difference (ms) to minutes

    return same_age

def test_for_duplicate_size(search_result_1, search_result_2):
    """

    :type search_result_1: NzbSearchResult
    :type search_result_2: NzbSearchResult
    """
    if not search_result_1.size or not search_result_2.size:
        return False
    size_threshold = config.resultProcessingSettings.duplicateSizeThresholdInPercent.get()
    size_difference = search_result_1.size - search_result_2.size
    size_average = (search_result_1.size + search_result_2.size) / 2
    size_difference_percent = abs(size_difference / size_average) * 100
    same_size = size_difference_percent <= size_threshold
    
    return same_size
        


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
    providerguid = fields.String()
    size = fields.Integer()
    category = fields.String()
    has_nfo = fields.Boolean()
    details_link = fields.String()


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


def transform_results(results, dbsearch):
    if downloaderSettings.nzbaccesstype.get() == NzbAccessTypeSelection.direct:  # We don't change the link, the results lead directly to the NZB
        return results
    transformed = []
    for i in results:
        f = furl(get_root_url())
        f.path.add("internalapi/getnzb")
        data_getnzb = {"provider": i.provider, "guid": i.guid, "searchid": dbsearch, "title": i.title} #All the data we would like to have when an NZB is downloaded
        f.add(data_getnzb)  #Here we insert it directly into the link as parameters
        i.link = f.url
        i.providerguid = i.guid #Save the provider's original GUID so that we can send it later from the GUI to identify the result
        i.guid = f.url #For now it's the same as the link to the NZB, later we might link to a details page that at the least redirects to the original provider's page
        
        #Add our pseudo-guid (not the one above, with the link, just an identifier) to the newznab attributes so that when any external tool uses it together with g=get or t=getnfo we can identify it
        has_guid = False
        has_size = False
        for a in i.attributes:
            if a["name"] == "guid":
                a["value"] = urllib.parse.quote(json.dumps(data_getnzb)) 
                has_guid = True
            if a["name"] == "size":
                has_size = True
        if not has_guid:
            i.attributes.append({"name": "guid", "value": urllib.parse.quote(json.dumps(data_getnzb))}) #If it wasn't set before now it is (for results from newznab-indexers)
        if not has_size:
            i.attributes.append({"name": "size", "value": i.size}) #If it wasn't set before now it is (for results from newznab-indexers)
        transformed.append(i)
        
    return transformed

def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)

def process_for_external_api(results):
    results = transform_results(results["results"], results["dbsearch"]) #todo dbsearchid
    
    return results


def process_for_internal_api(search_result):
    
    nzbsearchresults = search_result["results"]
    logger.debug("Processing %d results" % len(nzbsearchresults))
    providersearchdbentries = []
    for provider, provider_info in search_result["provider_infos"].items():
        provider_search_info = ProviderSearchSchema().dump(provider_info["provider_search"]).data
        provider_search_info["total"] = provider_info["total"]
        provider_search_info["offset"] = search_result["provider_infos"][provider]["search_request"].offset 
        provider_search_info["total_known"] = provider_info["total_known"]
        provider_search_info["has_more"] = provider_info["has_more"]
        providersearchdbentries.append(provider_search_info)

    nzbsearchresults = transform_results(nzbsearchresults, search_result["dbsearch"])

    grouped_by_sameness = find_duplicates(nzbsearchresults)
    logger.debug("Duplicate check left %d groups of separate results" % len(grouped_by_sameness))
    # Will be sorted by GUI later anyway but makes debugging easier
    results = sorted(grouped_by_sameness, key=lambda x: x[0].epoch, reverse=True)
    serialized = []
    for g in results:
        serialized.append(serialize_nzb_search_result(g).data)

    allresults = []
    # We give each group of results a unique value by which they can be identified later even if they're "taken apart"
    for group in serialized:
        for i in group:
            i["hash"] = hash(group[0]["guid"])
            allresults.append(i)
    return {"results": allresults, "providersearches": providersearchdbentries, "searchentryid": search_result["dbsearch"], "total": search_result["total"]}


def serialize_nzb_search_result(result):
    return NzbSearchResultSchema(many=True).dump(result)


def get_nfo(provider_name, guid):
    nfo = None
    result = {}
    for p in providers.configured_providers:
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
    for p in providers.configured_providers:
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
    for p in providers.configured_providers:
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
        
    
        
    
