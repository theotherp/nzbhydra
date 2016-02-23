from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import json
import logging
import os
import urlparse
from StringIO import StringIO
from zipfile import ZipFile

import arrow
import datetime

import flask
import rison
from bunch import Bunch
from werkzeug.contrib.fixers import ProxyFix

from nzbhydra.searchmodules import omgwtf

sslImported = True
try:
    import ssl
except:
    sslImported = False
    print("Unable to import SSL")
import threading
import urllib
from builtins import *
from peewee import fn
from nzbhydra.exceptions import DownloaderException, IndexerResultParsingException

# standard_library.install_aliases()
from functools import update_wrapper
from pprint import pprint
from time import sleep
from arrow import Arrow
from flask import Flask, render_template, request, jsonify, Response
from flask import redirect, make_response, send_from_directory, send_file
from flask_cache import Cache
from flask.json import JSONEncoder
from webargs import fields
from furl import furl
from webargs.flaskparser import use_args
from werkzeug.exceptions import Unauthorized
from werkzeug.wrappers import ETagResponseMixin
from flask_session import Session
from nzbhydra import config, search, infos, database
from nzbhydra.api import process_for_internal_api, get_nfo, process_for_external_api, get_indexer_nzb_link, get_nzb_response, download_nzb_and_log, get_details_link, get_nzb_link_and_guid
from nzbhydra.config import NzbAccessTypeSelection, getAnonymizedConfig, getSettingsToHide
from nzbhydra.database import IndexerStatus, Indexer
from nzbhydra.downloader import Nzbget, Sabnzbd
from nzbhydra.indexers import read_indexers_from_config, clean_up_database
from nzbhydra.search import SearchRequest
from nzbhydra.stats import get_avg_indexer_response_times, get_avg_indexer_search_results_share, get_avg_indexer_access_success, get_nzb_downloads, get_search_requests, get_indexer_statuses
from nzbhydra.update import get_rep_version, get_current_version, update, getChangelog, getVersionHistory
from nzbhydra.searchmodules.newznab import test_connection, check_caps
from nzbhydra.log import getLogs, getAnonymizedLogFile



class ReverseProxied(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        environ["MY_URL_BASE"] = "/"
        base_url = config.settings.main.urlBase
        if base_url is not None and base_url.endswith("/"):
            base_url = base_url[:-1]
        if base_url is not None and base_url != "":
            script_name = str(furl(base_url).path)
            if environ['PATH_INFO'].startswith(script_name):
                environ["MY_URL_BASE"] = script_name + "/"
                environ['PATH_INFO'] = environ['PATH_INFO'][len(script_name):]

        return self.app(environ, start_response)


logger = logging.getLogger('root')

app = Flask(__name__)
app.wsgi_app = ReverseProxied(app.wsgi_app)
app.config["SESSION_TYPE"] = "filesystem"
app.config["PRESERVE_CONTEXT_ON_EXCEPTION"] = True
app.config["PROPAGATE_EXCEPTIONS"] = True
Session(app)
flask_cache = Cache(app, config={'CACHE_TYPE': "simple", "CACHE_THRESHOLD": 250, "CACHE_DEFAULT_TIMEOUT": 60 * 60 * 24 * 7}) #Used for autocomplete and nfos and such
internal_cache = Cache(app, config={'CACHE_TYPE': "simple",  # Cache for internal data like settings, form, schema, etc. which will be invalidated on request
                                    "CACHE_DEFAULT_TIMEOUT": 60 * 30})
proxyFix = ProxyFix(app)

failedLogins = {}


def getIp():
    if not request.headers.getlist("X-Forwarded-For"):
        return request.remote_addr
    else:
        return proxyFix.get_remote_addr(request.headers.getlist("X-Forwarded-For"))


def make_request_cache_key(*args, **kwargs):
    return str(hash(frozenset(request.args.items())))


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
    if request.endpoint is not None and not request.endpoint.endswith("static"):  # No point in opening a db connection if we only serve a static file
        database.db.connect()


@app.teardown_request
def _db_disconnect(esc):
    if not database.db.is_closed():
        database.db.close()


@app.after_request
def disable_caching(response):
    if "/static" not in request.path: #Prevent caching of control URLs
        response.cache_control.private = True
        response.cache_control.max_age = 0
        response.cache_control.must_revalidate = True
        response.cache_control.no_cache = True
        response.cache_control.no_store = True    
    response.headers["Expires"] = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
    response.cache_control.max_age = 0
    
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
    # Only if the request actually contains auth data we consider this a login try
    if request.authorization:
        global failedLogins
        ip = getIp()
         
        if ip in failedLogins.keys(): 
            lastFailedLogin = failedLogins[ip]["lastFailedLogin"]
            lastFailedLoginFormatted = lastFailedLogin.format("YYYY-MM-DD HH:mm:ss")
            failedLoginCounter = failedLogins[ip]["failedLoginCounter"]
            lastTriedUsername = failedLogins[ip]["lastTriedUsername"]
            lastTriedPassword = failedLogins[ip]["lastTriedPassword"]
            secondsSinceLastFailedLogin = (arrow.utcnow() - lastFailedLogin).seconds
            waitFor = 2 * failedLoginCounter
            failedLogins[ip]["lastFailedLogin"] = arrow.utcnow()
            failedLogins[ip]["lastTriedUsername"] = request.authorization.username
            failedLogins[ip]["lastTriedPassword"] = request.authorization.password
    
            if secondsSinceLastFailedLogin < waitFor:
                if lastTriedUsername == request.authorization.username and lastTriedPassword == request.authorization.password:
                    # We don't log this and don't increase the counter, it happens when the user reloads the page waiting for the counter to go down, so we don't change the lastFailedLogin (well, we set it back)
                    failedLogins[ip]["lastFailedLogin"] = lastFailedLogin
                    return Response("Please wait %d seconds until you try to authenticate again" % (waitFor - secondsSinceLastFailedLogin), 429)
                failedLogins[ip]["failedLoginCounter"] = failedLoginCounter + 1
                logger.warn("IP %s failed to authenticate. The last time was at %s. This was his %d. failed login attempt" % (ip, lastFailedLoginFormatted, failedLoginCounter + 1))
                return Response("Please wait %d seconds until you try to authenticate again" % (waitFor - secondsSinceLastFailedLogin), 429)
            else:
                failedLogins[ip]["failedLoginCounter"] = failedLoginCounter + 1
                logger.warn("IP %s failed to authenticate. The last time was at %s. This was his %d. failed login attempt" % (ip, lastFailedLoginFormatted, failedLoginCounter + 1))
    
        else:
            logger.warn("IP %s failed to authenticate. This was his first failed login attempt" % ip)
            failedLogins[ip] = {"lastFailedLogin": arrow.utcnow(), "failedLoginCounter": 1, "lastTriedUsername": request.authorization.username, "lastTriedPassword": request.authorization.password}
    
    return Response(
            'Could not verify your access level for that URL. You have to login with proper credentials', 401,
            {'WWW-Authenticate': 'Basic realm="Login Required"'})


# TODO: use this to create generic responses. the gui should have a service to intercept this and forward only the data (if it was successful) or else show the error, possibly log it
def create_json_response(success=True, data=None, error_message=None):
    return jsonify({"success": success, "data": data, "error_message": error_message})


def isAdminLoggedIn():
    auth = request.authorization
    return len(config.settings.auth.users) == 0 or (auth is not None and any([x.maySeeAdmin and x.username == auth.username and x.password == auth.password for x in config.settings.auth.users]))


def isAllowed(authType):
    if len(config.settings.auth.users) == 0:
        return True
    auth = Bunch.fromDict(request.authorization)
    
    for user in config.settings.auth.users:
        if authType == "main":
            if not user.username and not user.password: #"authless" user
                return True
            if auth and auth.username == user.username and auth.password == user.password:
                return True
        if authType == "stats":
            if not user.username and not user.password and user.maySeeStats:  # "authless" user
                return True
            if auth and auth.username == user.username and auth.password == user.password:
                return user.maySeeStats
        if authType == "admin":
            if not user.username and not user.password and user.maySeeAdmin:  # "authless" user
                return True
            if auth and auth.username == user.username and auth.password == user.password:
                return user.maySeeAdmin
        
    return False
    
    


def requires_auth(authType, allowWithSecretKey=False, allowWithApiKey=False):
    def decorator(f):
        def wrapped_function(*args, **kwargs):
            allowed = False
            if allowWithSecretKey and "SECRETACCESSKEY" in os.environ.keys():
                if "secretaccesskey" in request.args and request.args.get("secretaccesskey").lower() == os.environ["SECRETACCESSKEY"].lower():
                    logger.debug("Access granted by secret access key")
                    allowed = True
            elif allowWithApiKey and "apikey" in request.args:
                if request.args.get("apikey") == config.settings.main.apikey:
                    logger.debug("Access granted by API key")
                    allowed = True
                else:
                    logger.warn("API access qith invalid API key from %s" % getIp())
            else:
                allowed = isAllowed(authType)
            if allowed:
                try:
                    failedLogins.pop(getIp())
                    logger.info("Successful login from IP %s after failed login tries. Resetting failed login counter." % getIp())
                except KeyError:
                    pass
                return f(*args, **kwargs)
            else:
                return authenticate()

        return update_wrapper(wrapped_function, f)

    return decorator

@app.route('/<path:path>')
@app.route('/', defaults={"path": None})
@requires_auth("main")
def base(path):
    logger.debug("Sending index.html")
    host_url = "//" + request.host + request.environ['MY_URL_BASE']
    _, currentVersion = get_current_version()
    return render_template("index.html", host_url=host_url, isAdmin=isAdminLoggedIn(), onProd="false" if config.settings.main.debug else "true")


def render_search_results_for_api(search_results, total, offset):
    xml = render_template("api.html", channel={}, items=search_results, total=total, offset=offset)
    return Response(xml, mimetype="application/rss+xml, application/xml, text/xml")


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

    if args["q"] is not None and args["q"] != "":
        args["query"] = args["q"]  # Because internally we work with "query" instead of "q"
    if config.settings.main.apikey and ("apikey" not in args or args["apikey"] != config.settings.main.apikey):
        logger.error("Tried API access with invalid or missing API key")
        raise Unauthorized("API key not provided or invalid")
    elif args["t"] in ("search", "tvsearch", "movie"):
        return api_search(args)
    elif args["t"] == "get":
        args = rison.loads(args["id"])
        logger.info("API request to download %s from %s" % (args["title"], args["indexer"]))
        return extract_nzb_infos_and_return_response(args["indexer"], args["indexerguid"], args["title"], args["searchid"])
    elif args["t"] == "caps":
        xml = render_template("caps.html")
        return Response(xml, mimetype="text/xml")
    else:
        pprint(request)
        return "Unknown API request. Supported functions: search, tvsearch, movie, get, caps", 500


def api_search(args):
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


api_search.make_cache_key = make_request_cache_key

@app.route("/details/<path:guid>")
@requires_auth("main")
def get_details(guid):
    # GUID is not the GUID-item from the RSS but the newznab GUID which in our case is just a rison string 
    d = rison.loads(urlparse.unquote(guid))
    details_link = get_details_link(d["indexer"], d["guid"])
    if details_link:
        return redirect(details_link)
    return "Unable to find details", 500


getnzb_args = {
    "id": fields.String(missing=None)
}


@app.route('/getnzb')
@requires_auth("main", allowWithApiKey=True)
@use_args(getnzb_args, locations=['querystring'])
def getnzb(args):
    logger.debug("Get NZB request with args %s" % args)
    args = rison.loads(args["id"])
    logger.info("API request to download %s from %s" % (args["title"], args["indexer"]))
    return extract_nzb_infos_and_return_response(args["indexer"], args["indexerguid"], args["title"], args["searchid"])


def process_and_jsonify_for_internalapi(results):
    if results is not None:
        results = process_for_internal_api(results)
        return jsonify(results)  # Flask cannot return lists
    else:
        return "No results", 500


def cached_search(search_request):    
    results = search.search(True, search_request)
    return process_and_jsonify_for_internalapi(results)


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
@requires_auth("main")
@use_args(internalapi_search_args, locations=['querystring'])
def internalapi_search(args):
    logger.debug("Search request with args %s" % args)
    if args["category"].lower() == "ebook":
        type = "ebook"
    elif args["category"].lower() == "audiobook":
        type = "audiobook"
    else:
        type = "general"
    indexers = urllib.unquote(args["indexers"]) if args["indexers"] is not None else None
    search_request = SearchRequest(type=type, query=args["query"], offset=args["offset"], category=args["category"], minsize=args["minsize"], maxsize=args["maxsize"], minage=args["minage"], maxage=args["maxage"], indexers=indexers)
    return cached_search(search_request)


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
@requires_auth("main")
@use_args(internalapi_moviesearch_args, locations=['querystring'])
def internalapi_moviesearch(args):
    logger.debug("Movie search request with args %s" % args)
    indexers = urllib.unquote(args["indexers"]) if args["indexers"] is not None else None
    search_request = SearchRequest(type="movie", query=args["query"], offset=args["offset"], category=args["category"], minsize=args["minsize"], maxsize=args["maxsize"], minage=args["minage"], maxage=args["maxage"], indexers=indexers)

    if args["imdbid"]:
        search_request.identifier_key = "imdbid"
        search_request.identifier_value = args["imdbid"]
    elif args["tmdbid"]:
        logger.debug("Need to get IMDB id from TMDB id %s" % args["tmdbid"])
        imdbid = infos.convertId("tmdb", "imdb", args["tmdbid"])
        if imdbid is None:
            raise AttributeError("Unable to convert TMDB id %s" % args["tmdbid"])
        search_request.identifier_key = "imdbid"
        search_request.identifier_value = imdbid

    return cached_search(search_request)


internalapi_tvsearch_args = {
    "query": fields.String(missing=None),
    "category": fields.String(missing=None),
    "title": fields.String(missing=None),
    "rid": fields.String(missing=None),
    "tvdbid": fields.String(missing=None),
    "season": fields.Integer(missing=None),
    "episode": fields.Integer(missing=None),
    "offset": fields.Integer(missing=0),
    "indexers": fields.String(missing=None),

    "minsize": fields.Integer(missing=None),
    "maxsize": fields.Integer(missing=None),
    "minage": fields.Integer(missing=None),
    "maxage": fields.Integer(missing=None)
}


@app.route('/internalapi/tvsearch')
@requires_auth("main")
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
    return cached_search(search_request)


internalapi_autocomplete_args = {
    "input": fields.String(missing=None),
    "type": fields.String(missing=None),
}


@app.route('/internalapi/autocomplete')
@requires_auth("main")
@use_args(internalapi_autocomplete_args, locations=['querystring'])
@flask_cache.memoize()
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


internalapi_autocomplete.make_cache_key = make_request_cache_key

internalapi__getnfo_args = {
    "guid": fields.String(missing=None),
    "indexer": fields.String(missing=None),
}


@app.route('/internalapi/getnfo')
@requires_auth("main")
@use_args(internalapi__getnfo_args, locations=['querystring'])
@flask_cache.memoize()
def internalapi_getnfo(args):
    logger.debug("Get NFO request with args %s" % args)
    nfo = get_nfo(args["indexer"], args["guid"])
    return jsonify(nfo)


internalapi_getnfo.make_cache_key = make_request_cache_key

internalapi__getnzb_args = {
    "guid": fields.String(missing=None),
    "indexer": fields.String(missing=None),
    "searchid": fields.String(missing=None),
    "title": fields.String(missing=None)
}


#Obsolete?
@app.route('/internalapi/getnzb')
@requires_auth("main")
@use_args(internalapi__getnzb_args, locations=['querystring'])
def internalapi_getnzb(args):
    logger.debug("Get internal NZB request with args %s" % args)
    return extract_nzb_infos_and_return_response(args["indexer"], args["indexerguid"], args["title"], args["searchid"])


def extract_nzb_infos_and_return_response(indexer, indexerguid, title, searchid):
    if config.settings.downloader.nzbaccesstype == NzbAccessTypeSelection.redirect:
        link, _, _ = get_indexer_nzb_link(indexer, indexerguid, title, searchid, "redirect", True)
        if link is not None:
            logger.info("Redirecting to %s" % link)
            return redirect(link)
        else:
            return "Unable to build link to NZB", 404
    elif config.settings.downloader.nzbaccesstype == NzbAccessTypeSelection.serve:
        return get_nzb_response(indexer, indexerguid, title, searchid)
    else:
        logger.error("Invalid value of %s" % config.settings.downloader.nzbaccesstype)
        return "downloader.add_type has wrong value: %s" % config.settings.downloader.nzbaccesstype, 500


internalapi__addnzb_args = {
    "items": fields.String(missing=[]),
    "category": fields.String(missing=None)
}


@app.route('/internalapi/addnzbs', methods=['GET', 'PUT'])
@requires_auth("main")
@use_args(internalapi__addnzb_args)
def internalapi_addnzb(args):
    logger.debug("Add NZB request with args %s" % args)
    items = json.loads(args["items"])
    if config.settings.downloader.downloader == "nzbget":
        downloader = Nzbget()
    elif config.settings.downloader.downloader == "sabnzbd":
        downloader = Sabnzbd()
    else:
        logger.error("Adding an NZB without set downloader should not be possible")
        return jsonify({"success": False})
    added = 0
    for item in items:
        title = item["title"]
        indexerguid = item["indexerguid"]
        indexer = item["indexer"]
        category = args["category"]
        dbsearchid = item["dbsearchid"]
        link, _ = get_nzb_link_and_guid(indexer, indexerguid, dbsearchid, title, True)

        if config.settings.downloader.nzbAddingType == config.NzbAddingTypeSelection.link:  # We send a link to the downloader. The link is either to us (where it gets answered or redirected, thet later getnzb will be called) or directly to the indexer
            add_success = downloader.add_link(link, title, category)
        else:  # We download an NZB send it to the downloader
            nzbdownloadresult = download_nzb_and_log(indexer, indexerguid, title, dbsearchid)
            if nzbdownloadresult is not None:
                add_success = downloader.add_nzb(nzbdownloadresult.content, title, category)
            else:
                add_success = False
        if add_success:
            added += 1

    if added:
        return jsonify({"success": True, "added": added, "of": len(items)})
    else:
        return jsonify({"success": False})


internalapi__testdownloader_args = {
    "name": fields.String(missing=None),
    "ssl": fields.Boolean(missing=False),
    "host": fields.String(missing=None),
    "port": fields.String(missing=None),
    "url": fields.String(missing=None),
    "username": fields.String(missing=None),
    "password": fields.String(missing=None),
    "apikey": fields.String(missing=None),
}


@app.route('/internalapi/test_downloader')
@use_args(internalapi__testdownloader_args)
@requires_auth("main")
def internalapi_testdownloader(args):
    logger.debug("Testing connection to downloader %s" % args["name"])
    if args["name"] == "nzbget":
        if "ssl" not in args.keys():
            logger.error("Incomplete test downloader request")
            return "Incomplete test downloader request", 500
        success, message = Nzbget().test(args["host"], args["ssl"], args["port"], args["username"], args["password"])
        return jsonify({"result": success, "message": message})
    if args["name"] == "sabnzbd":
        success, message = Sabnzbd().test(args["url"], args["username"], args["password"], args["apikey"])
        return jsonify({"result": success, "message": message})
    logger.error("Test downloader request with unknown downloader %s" % args["name"])
    return jsonify({"result": False, "message": "Internal error. Sorry..."})


internalapi__testnewznab_args = {
    "host": fields.String(missing=None),
    "apikey": fields.String(missing=None),
}


@app.route('/internalapi/test_newznab')
@use_args(internalapi__testnewznab_args)
@requires_auth("main")
def internalapi_testnewznab(args):
    success, message = test_connection(args["host"], args["apikey"])
    return jsonify({"result": success, "message": message})


internalapi__testomgwtf_args = {
    "username": fields.String(missing=None),
    "apikey": fields.String(missing=None),
}


@app.route('/internalapi/test_omgwtf')
@use_args(internalapi__testomgwtf_args)
@requires_auth("main")
def internalapi_testomgwtf(args):
    success, message = omgwtf.test_connection(args["apikey"], args["username"])
    return jsonify({"result": success, "message": message})


internalapi_testcaps_args = {
    "indexer": fields.String(missing=None),
    "apikey": fields.String(missing=None),
    "host": fields.String(missing=None)
}


@app.route('/internalapi/test_caps')
@use_args(internalapi_testcaps_args)
@requires_auth("admin")
def internalapi_testcaps(args):
    indexer = urlparse.unquote(args["indexer"])
    apikey = args["apikey"]
    host = urlparse.unquote(args["host"])
    logger.debug("Check caps for %s" % indexer)

    try:
        result = check_caps(host, apikey)

        return jsonify({"success": True, "result": result})
    except IndexerResultParsingException as e:
        return jsonify({"success": False, "message": e.message})


@app.route('/internalapi/getstats')
@requires_auth("stats")
def internalapi_getstats():
    logger.debug("Get stats")
    return jsonify({"avgResponseTimes": get_avg_indexer_response_times(),
                    "avgIndexerSearchResultsShares": get_avg_indexer_search_results_share(),
                    "avgIndexerAccessSuccesses": get_avg_indexer_access_success()})


@app.route('/internalapi/getindexerstatuses')
@requires_auth("stats")
def internalapi_getindexerstatuses():
    logger.debug("Get indexer statuses")
    return jsonify({"indexerStatuses": get_indexer_statuses()})


internalapi__getnzbdownloads_args = {
    "page": fields.Integer(missing=0),
    "limit": fields.Integer(missing=100),
    "type": fields.String(missing=None)
}


@app.route('/internalapi/getnzbdownloads')
@requires_auth("stats")
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
@requires_auth("stats")
@use_args(internalapi__getsearchrequests_args)
def internalapi_search_requests(args):
    logger.debug("Get search requests")
    return jsonify(get_search_requests(page=args["page"], limit=args["limit"], type=args["type"]))


internalapi__enableindexer_args = {
    "name": fields.String(required=True)
}


@app.route('/internalapi/enableindexer')
@requires_auth("stats")
@use_args(internalapi__enableindexer_args)
def internalapi_enable_indexer(args):
    logger.debug("Enabling indexer %s" % args["name"])
    indexer_status = IndexerStatus().select().join(Indexer).where(fn.lower(Indexer.name) == args["name"].lower())
    indexer_status.disabled_until = 0
    indexer_status.reason = None
    indexer_status.level = 0
    indexer_status.save()
    return jsonify({"indexerStatuses": get_indexer_statuses()})


@app.route('/internalapi/setsettings', methods=["PUT"])
@requires_auth("admin")
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
@requires_auth("admin")
@internal_cache.memoize()
def internalapi_getconfig():
    logger.debug("Get config request")
    return jsonify(Bunch.toDict(config.settings))


@app.route('/internalapi/getsafeconfig')
@requires_auth("main")
def internalapi_getsafeconfig():
    logger.debug("Get safe config request")
    return jsonify(config.getSafeConfig())


@app.route('/internalapi/getlogfordebugging')
@requires_auth("admin")
def internalapi_getdebugginginfos():
    logger.debug("Get debugging log request")
    log = getAnonymizedLogFile(getSettingsToHide())
    response = make_response(log)
    response.headers["Content-Disposition"] = "attachment; filename=nzbhydralog.txt"
    return response


@app.route('/internalapi/getconfigfordebugging')
@requires_auth("admin")
def internalapi_getdebugginginfos():
    logger.debug("Get debugging config request")
    ac = json.dumps(getAnonymizedConfig())
    response = make_response(ac)
    response.headers["Content-Disposition"] = "attachment; filename=nzbhydrasettings.txt"
    return response


@app.route('/internalapi/mayseeadminarea')
@requires_auth("main")
def internalapi_maySeeAdminArea():
    logger.debug("Get isAdminLoggedIn request")
    return jsonify({"maySeeAdminArea": isAdminLoggedIn()})


@app.route('/internalapi/askforadmin')
@requires_auth("admin")
def internalapi_askforadmin():
    logger.debug("Get askforadmin request")
    return "Ok... or not"


@app.route('/internalapi/get_version_history')
@requires_auth("main")
def internalapi_getversionhistory():
    logger.debug("Get local changelog request")
    versionHistory = getVersionHistory()
    return jsonify({"versionHistory": versionHistory})


@app.route('/internalapi/get_changelog')
@requires_auth("main")
def internalapi_getchangelog():
    logger.debug("Get changelog request")
    _, current_version = get_current_version()
    changelog = getChangelog(current_version)
    return jsonify({"changelog": changelog})


@app.route('/internalapi/get_versions')
@requires_auth("main")
def internalapi_getversions():
    logger.debug("Get versions request")
    _, current_version = get_current_version()
    _, rep_version = get_rep_version()
    
    versionsInfo = {"currentVersion": str(current_version), "repVersion": str(rep_version), "updateAvailable": rep_version > current_version}
    
    if rep_version > current_version:
        changelog = getChangelog(current_version)
        versionsInfo["changelog"] = changelog

    return jsonify(versionsInfo)


@app.route('/internalapi/getlogs')
@requires_auth("admin")
def internalapi_getlogs():
    logger.debug("Get logs request")
    logs = getLogs()
    return jsonify(logs)


@app.route('/internalapi/getcategories')
@requires_auth("main")
def internalapi_getcategories():
    logger.debug("Get categories request")
    categories = []
    try:
        if config.settings.downloader.downloader == config.DownloaderSelection.nzbget:
            categories = Nzbget().get_categories()
        elif config.settings.downloader.downloader == config.DownloaderSelection.sabnzbd:
            categories = Sabnzbd().get_categories()
        return jsonify({"success": True, "categories": categories})
    except DownloaderException as e:
        return jsonify({"success": False, "message": e.message})


def restart(func=None, afterUpdate=False):
    logger.info("Restarting now")
    logger.debug("Setting env variable RESTART to 1")
    os.environ["RESTART"] = "1"
    if afterUpdate:
        logger.debug("Setting env variable AFTERUPDATE to 1")
        os.environ["AFTERUPDATE"] = "1"
    logger.debug("Sending shutdown signal to server")
    func()


@app.route("/internalapi/restart")
@requires_auth("admin", True)
def internalapi_restart():
    logger.info("User requested to restart. Sending restart command in 1 second")
    func = request.environ.get('werkzeug.server.shutdown')
    thread = threading.Thread(target=restart, args=(func,False))
    thread.daemon = True
    thread.start()
    return "Restarting"


def shutdown():
    logger.debug("Sending shutdown signal to server")
    sleep(1)
    os._exit(0)


@app.route("/internalapi/shutdown")
@requires_auth("admin", True)
def internalapi_shutdown():
    logger.info("Shutting down due to external request")
    thread = threading.Thread(target=shutdown)
    thread.daemon = True
    thread.start()
    return "Shutting down..."


@app.route("/internalapi/update")
@requires_auth("admin")
def internalapi_update():
    logger.info("Starting update")
    updated = update()
    if not updated:
        return jsonify({"success": False})
    logger.info("Will send restart command in 1 second")
    func = request.environ.get('werkzeug.server.shutdown')
    thread = threading.Thread(target=restart, args=(func, True))
    thread.daemon = True
    thread.start()
    return jsonify({"success": True})


def run(host, port, basepath):
    context = create_context()
    configureFolders(basepath)    
    for handler in logger.handlers:
        app.logger.addHandler(handler)
    if context is None:
        app.run(host=host, port=port, debug=config.settings.main.debug, threaded=config.settings.main.runThreaded, use_reloader=config.settings.main.flaskReloader)
    else:
        app.run(host=host, port=port, debug=config.settings.main.debug, ssl_context=context, threaded=config.settings.main.runThreaded, use_reloader=config.settings.main.flaskReloader)


def configureFolders(basepath):
    app.template_folder = os.path.join(basepath, "templates")
    app.static_folder = os.path.join(basepath, "static")


def create_context():
    context = None
    if config.settings.main.ssl:
        if not sslImported:
            logger.error("SSL could not be imported, sorry. Falling back to standard HTTP")
        else:
            context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
            context.load_cert_chain(config.settings.main.sslcert, config.settings.main.sslkey)
    return context
