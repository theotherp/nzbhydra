from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import copy
import logging
from collections import namedtuple
from io import BytesIO

from builtins import *
from flask import request, send_file
from furl import furl
from marshmallow import Schema, fields
from requests import RequestException

from nzbhydra import config
from nzbhydra import indexers
from nzbhydra.database import IndexerApiAccess, IndexerNzbDownload, SearchResult
from nzbhydra.exceptions import IndexerNotFoundException, NzbDownloadException

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


class IndexerSchema(Schema):
    name = fields.String()
    module = fields.String()
    enabled = fields.Boolean()
    settings = fields.String()


class NzbSearchResultSchema(Schema):
    title = fields.String()
    link = fields.String()
    epoch = fields.Integer()
    pubdate_utc = fields.String()
    age = fields.String()
    age_days = fields.Integer()
    age_precise = fields.Boolean()
    indexer = fields.String()
    indexerscore = fields.String()
    searchResultId = fields.String()
    indexerguid = fields.String()
    size = fields.Integer()
    category = fields.String()
    has_nfo = fields.Integer()
    details_link = fields.String()
    hash = fields.Integer()
    dbsearchid = fields.Integer()
    downloadType = fields.String()
    comments = fields.Integer()
    grabs = fields.Integer()
    files = fields.Integer()


class IndexerApiAccessSchema(Schema):
    indexer = fields.Nested(IndexerSchema, only="name")
    time = fields.DateTime()
    type = fields.String()
    url = fields.String()
    response_successful = fields.Boolean()
    response_time = fields.Integer()
    error = fields.String()


class RejectionCountSchema(Schema):
    passworded = fields.Integer()
    forbiddenword = fields.Integer()
    requiredword = fields.Integer()
    forbiddenregex = fields.Integer()
    requiredregex = fields.Integer()
    size = fields.Integer()
    age = fields.Integer()
    missing = fields.Integer()
    category = fields.Integer()


class IndexerSearchSchema(Schema):
    indexer = fields.Nested(IndexerSchema, only="name")
    time = fields.DateTime()
    successful = fields.Boolean()
    results = fields.Integer()
    did_search = fields.Boolean()
    apiAccesses = fields.Nested(IndexerApiAccessSchema, many=True)


def get_root_url():
    f = furl()
    f.scheme = request.scheme
    f.host = furl(request.host_url).host
    f.port = config.settings.main.port
    if config.settings.main.urlBase:
        f.path = config.settings.main.urlBase
    return str(f) + "/"


def get_nzb_link_and_guid(searchResultId, external, downloader=None):
    externalUrl = config.settings.main.externalUrl
    if externalUrl and not (external and config.settings.main.useLocalUrlForApiAccess):
        f = furl(externalUrl)
    else:
        f = furl(get_root_url())
    f.path.add("getnzb")
    args = {"searchresultid": searchResultId}

    if external:
        apikey = config.settings.main.apikey
        if apikey is not None:
            args["apikey"] = apikey
    if downloader:
        args["downloader"] = downloader
    f.set(args=args)
    return f.url


def transform_results(results, external):
    transformed = []
    for j in results:
        if j.searchResultId is None:  # Quick fix
            continue
        i = copy.copy(j)
        i.link = get_nzb_link_and_guid(i.searchResultId, external)
        i.guid = i.searchResultId
        attributes = {x["name"]: x["value"] for x in i.attributes}
        attributes["guid"] = i.guid
        for attribute in ["size", "poster", "group"]:
            if getattr(i, attribute) and attribute not in attributes.keys():
                attributes[attribute] = getattr(i, attribute)
        if i.passworded is not None:
            attributes["password"] = 1 if i.passworded else 0
        i.attributes = [{"name": key, "value": value} for key, value in attributes.iteritems()]
        for category in i.category.newznabCategories:
            i.attributes.append({"name": "category", "value": category})

        i.category = i.category.pretty

        transformed.append(i)

    return transformed


def sizeof_fmt(num, suffix='B'):
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def process_for_external_api(results):
    logger.debug("Processing results for external search")
    results = transform_results(results["results"], True)

    return results


def process_for_internal_api(search_result):
    nzbsearchresults = search_result["results"]
    logger.debug("Processing results for internal search")
    indexersearchdbentries = []
    for indexer, indexer_info in search_result["indexer_infos"].items():
        indexer_search_info = IndexerSearchSchema().dump(indexer_info["indexer_search"]).data
        indexer_search_info["total"] = indexer_info["total"]
        indexer_search_info["offset"] = search_result["indexer_infos"][indexer]["search_request"].offset
        indexer_search_info["total_known"] = indexer_info["total_known"]
        indexer_search_info["has_more"] = indexer_info["has_more"]
        indexer_search_info["did_search"] = indexer_info["did_search"]
        indexer_search_info["indexer"] = indexer_info["indexer"]
        indexersearchdbentries.append(indexer_search_info)
    indexersearchdbentries = sorted(indexersearchdbentries, key=lambda x: x["indexer"])

    nzbsearchresults = transform_results(nzbsearchresults, False)
    nzbsearchresults = serialize_nzb_search_result(nzbsearchresults)

    return {"results": nzbsearchresults, "indexersearches": indexersearchdbentries, "searchentryid": search_result["dbsearchid"], "total": search_result["total"], "rejected": search_result["rejected"]}


def serialize_nzb_search_result(results):
    return NzbSearchResultSchema(many=True).dump(results).data


def get_nfo(searchresultid):
    try:
        searchResult = SearchResult.get(SearchResult.id == searchresultid)
        indexer = indexers.getIndexerByName(searchResult.indexer.name)
        has_nfo, nfo, message = indexer.get_nfo(searchResult.guid)
        return {"has_nfo": has_nfo, "nfo": nfo, "message": message}
    except IndexerNotFoundException as e:
        logger.error(e.message)
        return {"has_nfo": False, "error": "Unable to find indexer"}


def get_details_link(indexer_name, guid):
    for p in indexers.enabled_indexers:
        if p.name == indexer_name:
            return p.get_details_link(guid)
    else:
        logger.error("Did not find indexer with name %s" % indexer_name)
        return None


def get_entry_by_id(indexer_name, guid, title):
    for p in indexers.enabled_indexers:
        if p.name == indexer_name:
            return p.get_entry_by_id(guid, title)
    else:
        logger.error("Did not find indexer with name %s" % indexer_name)
        return None


def get_indexer_nzb_link(searchResultId, mode, log_api_access, internal=False):
    """
    Build a link that leads to the actual NZB of the indexer using the given informations. We log this as indexer API access and NZB download because this is only called
    when the NZB will be actually downloaded later (by us or a downloader) 
    :return: str
    """
    searchResult = SearchResult.get(SearchResult.id == searchResultId)
    indexerName = searchResult.indexer.name
    indexer = indexers.getIndexerByName(indexerName)
    link = searchResult.link

    # Log to database
    papiaccess = IndexerApiAccess(indexer=indexer.indexer, type="nzb", url=link, response_successful=None) if log_api_access else None
    try:
        papiaccess.username = request.authorization.username if request.authorization is not None else None
    except RuntimeError:
        pass
    papiaccess.save()
    pnzbdl = IndexerNzbDownload(searchResult=searchResult, apiAccess=papiaccess, mode=mode, title=searchResult.title, internal=internal)
    pnzbdl.save()

    return link, papiaccess, pnzbdl


IndexerNzbDownloadResult = namedtuple("IndexerNzbDownload", "content headers")


def download_nzb_and_log(searchResultId):
    link, papiaccess, _ = get_indexer_nzb_link(searchResultId, "serve", True)
    indexerName = None
    try:
        indexerName = SearchResult.get(SearchResult.id == searchResultId).indexer.name
        indexer = indexers.getIndexerByName(indexerName)
        r = indexer.get(link, timeout=10)
        r.raise_for_status()

        papiaccess.response_successful = True
        papiaccess.response_time = r.elapsed.microseconds / 1000

        return IndexerNzbDownloadResult(content=r.content, headers=r.headers)
    except IndexerNotFoundException:
        if indexerName:
            logger.error("Unable to find indexer with name %s" % indexerName)
        else:
            logger.error("Unable to find indexer for search result id %s" % searchResultId)
        return None
    except SearchResult.DoesNotExist:
        logger.error("Unable to find search result with ID %s" % searchResultId)
        return None
    except RequestException as e:
        logger.error("Error while connecting to URL %s: %s" % (link, str(e)))
        papiaccess.error = str(e)
        return None
    finally:
        papiaccess.save()


def get_nzb_response(searchResultId):
    try:
        nzbdownloadresult, searchResult = getNzbById(searchResultId)
        
        bio = BytesIO(nzbdownloadresult.content)
        filename = searchResult.title + ".nzb" if searchResult.title is not None else "nzbhydra.nzb"
        response = send_file(bio, mimetype='application/x-nzb;', as_attachment=True, attachment_filename=filename, add_etags=False)
        response.headers["content-length"] = len(nzbdownloadresult.content)

        for header in nzbdownloadresult.headers.keys():
            if header.lower().startswith("x-dnzb") or header.lower() in ("content-disposition", "content-type"):
                response.headers[header] = nzbdownloadresult.headers[header]
        logger.info("Returning downloaded NZB %s from %s" % (searchResult.title, searchResult.indexer.name))
        return response
            
    except NzbDownloadException as e:
        return e.message, 500


def getNzbById(searchResultId):
    # type: (int) -> (IndexerNzbDownloadResult, SearchResult)
    """
    :rtype: (IndexerNzbDownloadResult, SearchResult)
    """
    try:
        searchResult = SearchResult.get(SearchResult.id == searchResultId)
    except SearchResult.DoesNotExist:
        logger.error("Unable to find search result with ID %s" % searchResultId)
        raise NzbDownloadException("Unable to find search result with ID %s" % searchResultId)
    nzbdownloadresult = download_nzb_and_log(searchResultId)
    if nzbdownloadresult is None:
        logger.error("Error while trying to download NZB %s from %s" % (searchResult.title, searchResult.indexer.name))
        raise NzbDownloadException("Unable to download NZB")
    return nzbdownloadresult, searchResult
