from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import json
import logging
import os

import rison

from nzbhydra.searchmodules import omgwtf

sslImported = True
try:
    import ssl
except:
    sslImported = False
    print("Unable to import SSL")
import sys
import threading
import urllib
from builtins import dict
from builtins import str
from builtins import int
from builtins import *
from future import standard_library
from peewee import fn
from nzbhydra.exceptions import DownloaderException

standard_library.install_aliases()
from functools import wraps
from pprint import pprint
from time import sleep
from arrow import Arrow
from flask import Flask, render_template, request, jsonify, Response
from flask import send_file, redirect, make_response
from flask.ext.cache import Cache
from flask.json import JSONEncoder
from webargs import fields
from furl import furl
from webargs.flaskparser import use_args
from werkzeug.exceptions import Unauthorized
from flask.ext.session import Session
from nzbhydra import config, search, infos, database
from nzbhydra.api import process_for_internal_api, get_nfo, process_for_external_api, get_nzb_link, get_nzb_response, download_nzb_and_log, get_details_link, get_nzb_link_and_guid
from nzbhydra.config import NzbAccessTypeSelection, mainSettings, downloaderSettings, CacheTypeSelection
from nzbhydra.database import IndexerStatus, Indexer
from nzbhydra.downloader import Nzbget, Sabnzbd
from nzbhydra.indexers import read_indexers_from_config, clean_up_database
from nzbhydra.search import SearchRequest
from nzbhydra.stats import get_avg_indexer_response_times, get_avg_indexer_search_results_share, get_avg_indexer_access_success, get_nzb_downloads, get_search_requests, get_indexer_statuses
from nzbhydra.versioning import get_rep_version, get_current_version
from nzbhydra.searchmodules.newznab import test_connection
from nzbhydra.log import  getLogs


class ReverseProxied(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        old_path_info = environ["PATH_INFO"]
        path_info = environ['PATH_INFO']
        
        environ["URL_BASE"] = old_path_info
        if config.mainSettings.baseUrl.get() is not None and config.mainSettings.baseUrl.get() != "":
            baseUrlSetting = config.mainSettings.baseUrl.get()
            f = furl(baseUrlSetting)
            baseUrl = str(f.path)
            if baseUrl.endswith("/"):
                baseUrl = baseUrl[:len(baseUrl) - 1]
            if path_info.startswith(baseUrl):
                path_info = path_info[len(baseUrl):]
            environ["PATH_INFO"] = path_info
        
        return self.app(environ, start_response)


logger = logging.getLogger('root')

app = Flask(__name__)
app.wsgi_app = ReverseProxied(app.wsgi_app)
app.config["SESSION_TYPE"] = "filesystem"
app.config["PRESERVE_CONTEXT_ON_EXCEPTION"] = True
app.config["PROPAGATE_EXCEPTIONS"] = True
Session(app)
search_cache = Cache()
internal_cache = Cache(app, config={'CACHE_TYPE': "simple",  # Cache for internal data like settings, form, schema, etc. which will be invalidated on request
                                    "CACHE_DEFAULT_TIMEOUT": 60 * 30})


class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        try:
            if isinstance(obj, Arrow):
                return obj.timestamp
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder.default(self, obj)


app.json_encoder = CustomJSONEncoder


@app.before_request
def _db_connect():
    if not request.endpoint.endswith("static"):  # No point in opening a db connection if we only serve a static file
        database.db.connect()


@app.teardown_request
def _db_disconnect(esc):
    if not database.db.is_closed():
        database.db.close()


@app.after_request
def disable_caching(response):
    if mainSettings.debug:
        # Disable browser caching for development so resources are always served fresh :-)
        response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Epires'] = '0'
        return response


@app.errorhandler(Exception)
def all_exception_handler(exception):
    logger.exception(exception)
    try:
        return exception.message, 500
    except:
        return "Unknwon error", 500


@app.errorhandler(422)
def handle_bad_request(err):
    # webargs attaches additional metadata to the `data` attribute
    data = getattr(err, 'data')
    if data:
        # Get validations from the ValidationError object
        messages = data['exc'].messages
    else:
        messages = ['Invalid request']
    return jsonify({
        'messages': messages,
    }), 422


def authenticate():
    return Response(
        'Could not verify your access level for that URL. You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})


# TODO: use this to create generic responses. the gui should have a service to intercept this and forward only the data (if it was successful) or else show the error, possibly log it
def create_json_response(success=True, data=None, error_message=None):
    return jsonify({"success": success, "data": data, "error_message": error_message})


def isAdminLoggedIn():
    auth = request.authorization
    return auth and (auth.username == config.get(mainSettings.adminUsername) and auth.password == config.get(mainSettings.adminPassword))


def maySeeAdminArea():
    return (config.mainSettings.enableAdminAuth.get() and isAdminLoggedIn()) or (not config.mainSettings.enableAdminAuth.get())


def isLoggedIn():
    auth = request.authorization
    return auth and (auth.username == config.get(mainSettings.username) and auth.password == config.get(mainSettings.password))


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not mainSettings.enableAuth.get():
            return f(*args, **kwargs)
        if isLoggedIn() or (config.mainSettings.enableAdminAuth.get() and isAdminLoggedIn()):
            return f(*args, **kwargs)
        return authenticate()

    return decorated


def requires_admin_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # This could probably be simplified but I feel too dumb right now
        # If admin is enabled we need an admin logged in
        # If admin is not enabled but normal auth is enabled we need a normal user
        # In all other cases we don't care about the user
        if config.mainSettings.enableAdminAuth.get():
            if not isAdminLoggedIn():
                return authenticate()
            else:
                return f(*args, **kwargs)
        if mainSettings.enableAuth.get():
            if isLoggedIn():
                return f(*args, **kwargs)
            else:
                return authenticate()
        else:
            return f(*args, **kwargs)

    return decorated


def requires_stats_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if config.mainSettings.enableAdminAuth.get() and config.mainSettings.enableAdminAuthForStats.get():
            if not isAdminLoggedIn():
                return authenticate()
            else:
                return f(*args, **kwargs)
        if mainSettings.enableAuth.get():
            if isLoggedIn():
                return f(*args, **kwargs)
            else:
                return authenticate()
        else:
            return f(*args, **kwargs)

    return decorated

@app.route('/<path:path>')
@app.route('/', defaults={"path": None})
@requires_auth
def base(path):
    logger.debug("Sending index.html")
    # We build a protocol agnostic base href using the host and url base. This way we should be able to access the site directly and from behind a proxy without having to do any
    # further configuration or setting any extra headers
    host_url = "//" + request.host + request.environ['URL_BASE']
    return render_template("index.html", host_url=host_url, isAdmin=maySeeAdminArea())


def render_search_results_for_api(search_results, total, offset):
    xml = render_template("api.html", channel={}, items=search_results, total=total, offset=offset)
    return Response(xml, mimetype="text/xml")


externalapi_args = {
    "input": fields.String(missing=None),
    "apikey": fields.String(missing=None),
    "t": fields.String(missing=None),
    "q": fields.String(missing=None),
    "query": fields.String(missing=None),
    "group": fields.String(missing=None),
    "limit": fields.Integer(missing=100),
    "offset": fields.Integer(missing=0),
    "cat": fields.String(missing=None),
    "o": fields.String(missing=None),
    "attrs": fields.String(missing=None),
    "extended": fields.Bool(missing=None),
    "del": fields.String(missing=None),
    "rid": fields.String(missing=None),
    "genre": fields.String(missing=None),
    "imdbid": fields.String(missing=None),
    "tvdbid": fields.String(missing=None),
    "season": fields.String(missing=None),
    "ep": fields.String(missing=None),
    "id": fields.String(missing=None),

    # These aren't actually needed but the way we pass args objects along we need to have them because functions check their value
    "title": fields.String(missing=None),
    "category": fields.String(missing=None),
    "episode": fields.String(missing=None),
    "minsize": fields.Integer(missing=None),
    "maxsize": fields.Integer(missing=None),
    "minage": fields.Integer(missing=None),
    "maxage": fields.Integer(missing=None),
    "dbsearchid": fields.String(missing=None),
    "indexers": fields.String(missing=None),
    "indexer": fields.String(missing=None),
    "offsets": fields.String(missing=None),

}


@app.route('/api')
@use_args(externalapi_args)
def api(args):
    logger.debug(request.url)
    logger.debug("API request: %s" % args)
    # Map newznab api parameters to internal
    args["category"] = args["cat"]
    args["episode"] = args["ep"]
    
    if args["id"] is not None:
        #Sometimes the id is not parsed properly and contains other parts of the URL so we try to remove them here
        idDic = urllib.parse.parse_qs(args["id"])
        if "id" in idDic.keys():
            args["id"] = idDic["id"][0]
            logger.debug("Query ID was not properly parsed. Converted it to %s" % args["id"])
        else:
            #The other if path will unquote the id with parse_qs unqotes so we do it here do 
            args["id"] = urllib.parse.unquote(args["id"])
            

    if args["q"] is not None and args["q"] != "":
        args["query"] = args["q"]  # Because internally we work with "query" instead of "q"
    if mainSettings.apikey.get_with_default(None) and ("apikey" not in args or args["apikey"] != mainSettings.apikey.get()):
        logger.error("Tried API access with invalid or missing API key")
        raise Unauthorized("API key not provided or invalid")
    elif args["t"] in ("search", "tvsearch", "movie"):
        search_request = SearchRequest(category=args["cat"], offset=args["offset"], limit=args["limit"], query=args["q"])
        if args["t"] == "search":
            search_request.type = "general"
            logger.info("")
        elif args["t"] == "tvsearch":
            search_request.type = "tv"
            identifier_key = "rid" if args["rid"] else "tvdbid" if args["tvdbid"] else None
            if identifier_key is not None:
                identifier_value = args[identifier_key]
                search_request.identifier_key = identifier_key
                search_request.identifier_value = identifier_value
            search_request.season = int(args["season"]) if args["season"] else None
            search_request.episode = int(args["episode"]) if args["episode"] else None
        elif args["t"] == "movie":
            search_request.type = "movie"
            search_request.identifier_key = "imdbid" if args["imdbid"] is not None else None
            search_request.identifier_value = args["imdbid"] if args["imdbid"] is not None else None
        logger.info("API search request: %s" % search_request)
        result = search.search(False, search_request)
        results = process_for_external_api(result)
        content = render_search_results_for_api(results, result["total"], result["offset"])
        response = make_response(content)
        response.headers["Content-Type"] = "application/xml"
        return content
    elif args["t"] == "get":
        args = rison.loads(args["id"])
        logger.info("API request to download %s from %s" % (args["title"], args["indexer"]))
        return extract_nzb_infos_and_return_response(args["indexer"], args["guid"], args["title"], args["searchid"])
    elif args["t"] == "caps":
        xml = render_template("caps.html")
        return Response(xml, mimetype="text/xml")
    else:
        pprint(request)
        return "Unknown API request. Supported functions: search, tvsearch, movie, get, caps", 500


@app.route("/details/<path:guid>")
@requires_auth
def get_details(guid):
    # GUID is not the GUID-item from the RSS but the newznab GUID which in our case is just a rison string 
    d = rison.loads(urllib.parse.unquote(guid))
    details_link = get_details_link(d["indexer"], d["guid"])
    if details_link:
        return redirect(details_link)
    return "Unable to find details", 500


def process_and_jsonify_for_internalapi(results):
    if results is not None:
        results = process_for_internal_api(results)
        return jsonify(results)  # Flask cannot return lists
    else:
        return "No results", 500


internalapi_search_args = {
    "query": fields.String(missing=None),
    "category": fields.String(missing=None),
    "offset": fields.Integer(missing=0),
    "indexers": fields.String(missing=None),

    "minsize": fields.Integer(missing=None),
    "maxsize": fields.Integer(missing=None),
    "minage": fields.Integer(missing=None),
    "maxage": fields.Integer(missing=None)
}


@app.route('/internalapi/search')
@requires_auth
@use_args(internalapi_search_args, locations=['querystring'])
def internalapi_search(args):
    logger.debug("Search request with args %s" % args)
    if args["category"].lower() == "ebook":
        type = "ebook"
    else:
        type = "general"
    if args["indexers"] is not None:
        args["indexers"] = urllib.unquote(args["indexers"])
    search_request = SearchRequest(type=type, query=args["query"], offset=args["offset"], category=args["category"], minsize=args["minsize"], maxsize=args["maxsize"], minage=args["minage"], maxage=args["maxage"], indexers=args["indexers"])
    results = search.search(True, search_request)
    return process_and_jsonify_for_internalapi(results)


internalapi_moviesearch_args = {
    "query": fields.String(missing=None),
    "category": fields.String(missing=None),
    "title": fields.String(missing=None),
    "imdbid": fields.String(missing=None),
    "tmdbid": fields.String(missing=None),
    "offset": fields.Integer(missing=0),
    "indexers": fields.String(missing=None),

    "minsize": fields.Integer(missing=None),
    "maxsize": fields.Integer(missing=None),
    "minage": fields.Integer(missing=None),
    "maxage": fields.Integer(missing=None)
}


@app.route('/internalapi/moviesearch')
@requires_auth
@use_args(internalapi_moviesearch_args, locations=['querystring'])
def internalapi_moviesearch(args):
    logger.debug("Movie search request with args %s" % args)
    search_request = SearchRequest(type="movie", query=args["query"], offset=args["offset"], category=args["category"], minsize=args["minsize"], maxsize=args["maxsize"], minage=args["minage"], maxage=args["maxage"], indexers=urllib.unquote(args["indexers"]))
    if args["imdbid"]:
        search_request.identifier_key = "imdbid"
        search_request.identifier_value = args["imdbid"]
    elif args["tmdbid"]:
        logger.debug("Need to get IMDB id from TMDB id %s" % args["tmdbid"])
        imdbid = infos.get_imdbid_from_tmdbid(args["tmdbid"])
        search_request.identifier_key = "imdbid"
        search_request.identifier_value = imdbid

    results = search.search(True, search_request)
    return process_and_jsonify_for_internalapi(results)


internalapi_tvsearch_args = {
    "query": fields.String(missing=None),
    "category": fields.String(missing=None),
    "title": fields.String(missing=None),
    "rid": fields.String(missing=None),
    "tvdbid": fields.String(missing=None),
    "season": fields.String(missing=None),
    "episode": fields.String(missing=None),
    "offset": fields.Integer(missing=0),
    "indexers": fields.String(missing=None),

    "minsize": fields.Integer(missing=None),
    "maxsize": fields.Integer(missing=None),
    "minage": fields.Integer(missing=None),
    "maxage": fields.Integer(missing=None)
}


@app.route('/internalapi/tvsearch')
@requires_auth
@use_args(internalapi_tvsearch_args, locations=['querystring'])
def internalapi_tvsearch(args):
    logger.debug("TV search request with args %s" % args)
    indexers = urllib.unquote(args["indexers"]) if args["indexers"] is not None else None 
    search_request = SearchRequest(type="tv", query=args["query"], offset=args["offset"], category=args["category"], minsize=args["minsize"], maxsize=args["maxsize"], minage=args["minage"], maxage=args["maxage"], episode=args["episode"], season=args["season"], title=args["title"],
                                   indexers=indexers)
    if args["tvdbid"]:
        search_request.identifier_key = "tvdbid"
        search_request.identifier_value = args["tvdbid"]
    elif args["rid"]:
        search_request.identifier_key = "rid"
        search_request.identifier_value = args["rid"]
    results = search.search(True, search_request)
    return process_and_jsonify_for_internalapi(results)


internalapi__autocomplete_args = {
    "input": fields.String(missing=None),
    "type": fields.String(missing=None),
}


@app.route('/internalapi/autocomplete')
@requires_auth
@use_args(internalapi__autocomplete_args, locations=['querystring'])
@search_cache.memoize()
def internalapi_autocomplete(args):
    logger.debug("Autocomplete request with args %s" % args)
    if args["type"] == "movie":
        results = infos.find_movie_ids(args["input"])
        return jsonify({"results": results})
    elif args["type"] == "tv":
        results = infos.find_series_ids(args["input"])
        return jsonify({"results": results})
    else:
        return "No results", 500


internalapi__getnfo_args = {
    "guid": fields.String(missing=None),
    "indexer": fields.String(missing=None),
}


@app.route('/internalapi/getnfo')
@requires_auth
@use_args(internalapi__getnfo_args, locations=['querystring'])
@search_cache.memoize()
def internalapi_getnfo(args):
    logger.debug("Get NFO request with args %s" % args)
    nfo = get_nfo(args["indexer"], args["guid"])
    return jsonify(nfo)


internalapi__getnzb_args = {
    "input": fields.String(missing=None),
    "guid": fields.String(missing=None),
    "indexer": fields.String(missing=None),
    "searchid": fields.String(missing=None),
    "title": fields.String(missing=None)
}


@app.route('/internalapi/getnzb')
@requires_auth
@use_args(internalapi__getnzb_args, locations=['querystring'])
def internalapi_getnzb(args):
    logger.debug("Get NZB request with args %s" % args)
    return extract_nzb_infos_and_return_response(args["indexer"], args["guid"], args["title"], args["searchid"])


def extract_nzb_infos_and_return_response(indexer, guid, title, searchid):
    if downloaderSettings.nzbaccesstype.get() == NzbAccessTypeSelection.redirect:  # I'd like to have this in api but don't want to have to use redirect() there...
        link = get_nzb_link(indexer, guid, title, searchid)
        if link is not None:
            return redirect(link)
        else:
            return "Unable to build link to NZB", 404
    elif downloaderSettings.nzbaccesstype.get() == NzbAccessTypeSelection.serve.name:
        return get_nzb_response(indexer, guid, title, searchid)
    else:
        logger.error("Invalid value of %s" % downloaderSettings.nzbaccesstype)
        return "downloader.add_type has wrong value", 500  # "direct" would never end up here, so it must be a wrong value


internalapi__addnzb_args = {
    "guids": fields.String(missing=[]),
    "category": fields.String(missing=None)
}


@app.route('/internalapi/addnzbs', methods=['GET', 'PUT'])
@requires_auth
@use_args(internalapi__addnzb_args)
def internalapi_addnzb(args):
    logger.debug("Add NZB request with args %s" % args)
    guids = json.loads(args["guids"])
    if downloaderSettings.downloader.isSetting(config.DownloaderSelection.nzbget):
        downloader = Nzbget()
    elif downloaderSettings.downloader.isSetting(config.DownloaderSelection.sabnzbd):
        downloader = Sabnzbd()
    else:
        logger.error("Adding an NZB without set downloader should not be possible")
        return jsonify({"success": False})
    added = 0
    for guid in guids:
        guid = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(guid).query))["id"]
        guid = rison.loads(guid)
        if downloaderSettings.nzbAddingType.isSetting(config.NzbAddingTypeSelection.link):  # We send a link to the downloader. The link is either to us (where it gets answered or redirected, thet later getnzb will be called) or directly to the indexer
            link = get_nzb_link_and_guid(guid["indexer"], guid["guid"], guid["searchid"], guid["title"])[0]
            add_success = downloader.add_link(link, guid["title"], args["category"])

        else:  # We download an NZB send it to the downloader
            nzbdownloadresult = download_nzb_and_log(guid["indexer"], guid["guid"], guid["title"], guid["searchid"])
            if nzbdownloadresult is not None:
                add_success = downloader.add_nzb(nzbdownloadresult.content, guid["title"], args["category"])
            else:
                add_success = False
        if add_success:
            added += 1

    if added:
        return jsonify({"success": True, "added": added, "of": len(guids)})
    else:
        return jsonify({"success": False})


internalapi__testdownloader_args = {
    "name": fields.String(missing=None),
    "ssl": fields.Boolean(missing=False),
    "host": fields.String(missing=None),
    "port": fields.String(missing=None),
    "username": fields.String(missing=None),
    "password": fields.String(missing=None),
    "apikey": fields.String(missing=None),
}


@app.route('/internalapi/test_downloader')
@use_args(internalapi__testdownloader_args)
@requires_auth
def internalapi_testdownloader(args):
    logger.debug("Testing connection to downloader %s" % args["name"])
    if args["name"] == "nzbget":
        if "ssl" not in args.keys():
            logger.error("Incomplete test downloader request")
            return "Incomplete test downloader request", 500
        success, message = Nzbget().test(args["host"], args["ssl"], args["port"], args["username"], args["password"])
        return jsonify({"result": success, "message": message})
    if args["name"] == "sabnzbd":
        success, message = Sabnzbd().test(args["host"], args["ssl"], args["port"], args["username"], args["password"], args["apikey"])
        return jsonify({"result": success, "message": message})
    logger.error("Test downloader request with unknown downloader %s" % args["name"])
    return jsonify({"result": False, "message": "Internal error. Sorry..."})


internalapi__testnewznab_args = {
    "host": fields.String(missing=None),
    "apikey": fields.String(missing=None),
}


@app.route('/internalapi/test_newznab')
@use_args(internalapi__testnewznab_args)
@requires_auth
def internalapi_testnewznab(args):
    success, message = test_connection(args["host"], args["apikey"])
    return jsonify({"result": success, "message": message})


internalapi__testomgwtf_args = {
    "username": fields.String(missing=None),
    "apikey": fields.String(missing=None),
}


@app.route('/internalapi/test_omgwtf')
@use_args(internalapi__testomgwtf_args)
@requires_auth
def internalapi_testomgwtf(args):
    success, message = omgwtf.test_connection(args["apikey"], args["username"])
    return jsonify({"result": success, "message": message})


@app.route('/internalapi/getstats')
@requires_stats_auth
def internalapi_getstats():
    logger.debug("Get stats")
    return jsonify({"avgResponseTimes": get_avg_indexer_response_times(),
                    "avgIndexerSearchResultsShares": get_avg_indexer_search_results_share(),
                    "avgIndexerAccessSuccesses": get_avg_indexer_access_success()})


@app.route('/internalapi/getindexerstatuses')
@requires_stats_auth
def internalapi_getindexerstatuses():
    logger.debug("Get indexer statuses")
    return jsonify({"indexerStatuses": get_indexer_statuses()})


internalapi__getnzbdownloads_args = {
    "page": fields.Integer(missing=0),
    "limit": fields.Integer(missing=100),
    "type": fields.String(missing=None)
}


@app.route('/internalapi/getnzbdownloads')
@requires_stats_auth
@use_args(internalapi__getnzbdownloads_args)
def internalapi_getnzb_downloads(args):
    logger.debug("Get NZB downloads")
    return jsonify(get_nzb_downloads(page=args["page"], limit=args["limit"], type=args["type"]))


internalapi__getsearchrequests_args = {
    "page": fields.Integer(missing=0),
    "limit": fields.Integer(missing=100),
    "type": fields.String(missing=None)
}


@app.route('/internalapi/getsearchrequests')
@requires_stats_auth
@use_args(internalapi__getsearchrequests_args)
def internalapi_search_requests(args):
    logger.debug("Get search requests")
    return jsonify(get_search_requests(page=args["page"], limit=args["limit"], type=args["type"]))


internalapi__enableindexer_args = {
    "name": fields.String(required=True)
}


@app.route('/internalapi/enableindexer')
@requires_stats_auth
@use_args(internalapi__enableindexer_args)
def internalapi_enable_indexer(args):
    logger.debug("Enabling indexer %s" % args["name"])
    indexer_status = IndexerStatus().select().join(Indexer).where(fn.lower(Indexer.name) == args["name"].lower()).get()
    indexer_status.disabled_until = 0
    indexer_status.reason = None
    indexer_status.level = 0
    indexer_status.save()
    return jsonify({"indexerStatuses": get_indexer_statuses()})


@app.route('/internalapi/setsettings', methods=["PUT"])
@requires_admin_auth
def internalapi_setsettings():
    logger.debug("Set settings request")
    try:
        config.import_config_data(request.get_json(force=True))
        internal_cache.delete_memoized(internalapi_getconfig)
        internal_cache.delete_memoized(internalapi_getsafeconfig)
        read_indexers_from_config()
        clean_up_database()
        return "OK"
    except Exception as e:
        logger.exception("Error saving settings")
        return "Error: %s" % e


@app.route('/internalapi/getconfig')
@requires_admin_auth
@internal_cache.memoize()
def internalapi_getconfig():
    logger.debug("Get config request")
    return jsonify(config.cfg)


@app.route('/internalapi/getsafeconfig')
@requires_auth
@internal_cache.memoize()
def internalapi_getsafeconfig():
    logger.debug("Get safe config request")
    return jsonify(config.getSafeConfig())


@app.route('/internalapi/mayseeadminarea')
@requires_auth
def internalapi_maySeeAdminArea():
    logger.debug("Get isAdminLoggedIn request")
    return jsonify({"maySeeAdminArea": maySeeAdminArea()})


@app.route('/internalapi/get_versions')
@requires_auth
def internalapi_getversions():
    logger.debug("Get versions request")
    current_version = get_current_version()
    rep_version = get_rep_version()
    return jsonify({"currentVersion": str(current_version), "repVersion": str(rep_version), "updateAvailable": rep_version > current_version})


@app.route('/internalapi/getlogs')
@requires_admin_auth
def internalapi_getlogs():
    logger.debug("Get logs request")
    logs = getLogs()
    return jsonify(logs)




@app.route('/internalapi/getcategories')
@requires_auth
def internalapi_getcategories():
    logger.debug("Get categories request")
    categories = []
    try:
        if downloaderSettings.downloader.isSetting(config.DownloaderSelection.nzbget):
            categories = Nzbget().get_categories()
        elif downloaderSettings.downloader.isSetting(config.DownloaderSelection.sabnzbd):
            categories = Sabnzbd().get_categories()
        return jsonify({"success": True, "categories": categories})
    except DownloaderException as e:
        return jsonify({"success": False, "message": e.message})


def restart():
    python = sys.executable
    print("Restarting with executable %s and args %s" % (python, sys.argv))
    os.execl(python, python, *sys.argv)
    print("Exiting")
    # sys.exit(0)


@app.route("/internalapi/restart")
@requires_auth
def internalapi_restart():
    # DOES NOT WORK CORRECTLY YET
    # Only works the first time, the second time it just hangs somewhere. Right now we don't need a restart function anyway (I hope)
    logger.info("Restarting due to external request")
    threading.Timer(1, restart).start()
    return send_file("static/restart.html")


def shutdown():
    sleep(1)
    print("Exiting")
    os._exit(0)


@app.route("/internalapi/shutdown")
@requires_auth
def internalapi_shutdown():
    logger.info("Shutting down due to external request")
    thread = threading.Thread(target=shutdown)
    thread.daemon = True
    thread.start()
    return "Shutting down..."


# Allows us to easily load a static class with results without having to load them
@app.route("/development/staticindex.html")
def development_staticindex():
    return send_file("static/index.html")


def run(host, port):
    context = create_context()
    configure_cache()
    for handler in logger.handlers:
        app.logger.addHandler(handler)
    if context is None:
        app.run(host=host, port=port, debug=config.mainSettings.debug.get())
    else:
        app.run(host=host, port=port, debug=config.mainSettings.debug.get(), ssl_context=context)


def configure_cache():
    if mainSettings.cache_enabled.get():
        if mainSettings.cache_type.get() == CacheTypeSelection.memory.name:
            logger.info("Using memory based cache")
            cache_type = "simple"
        else:
            logger.info("Using file based cache with folder %s" % mainSettings.cache_folder.get())
            cache_type = "filesystem"
    else:
        logger.info("Not using any caching")
        cache_type = "null"
    search_cache.init_app(app, config={'CACHE_TYPE': cache_type,
                                       "CACHE_DEFAULT_TIMEOUT": mainSettings.cache_timeout.get() * 60,
                                       "CACHE_THRESHOLD": mainSettings.cache_threshold.get(),
                                       "CACHE_DIR": mainSettings.cache_folder.get(),
                                       "CACHE_NO_NULL_WARNING": True})


def create_context():
    context = None
    if config.mainSettings.ssl.get():
        if not sslImported:
            logger.error("SSL could not be imported, sorry. Falling back to standard HTTP")
        else:
            context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
            context.load_cert_chain(config.mainSettings.sslcert.get(), config.mainSettings.sslkey.get())
    return context
