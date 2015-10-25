from functools import wraps
import json
import logging
import os
from pprint import pprint
import ssl
import threading
from time import sleep
import urllib
import sys

from flask import send_file, redirect, make_response
from flask import Flask, render_template, request, jsonify, Response

from flask.ext.cache import Cache

from webargs import fields

from webargs.flaskparser import use_args

from werkzeug.exceptions import Unauthorized

from flask.ext.session import Session
from nzbhydra.api import process_for_internal_api, get_nfo, process_for_external_api, get_nzb_link, get_nzb_response, download_nzb_and_log
from nzbhydra import config, search, infos, database
from nzbhydra.config import NzbAccessTypeSelection, NzbAddingTypeSelection, mainSettings, downloaderSettings, CacheTypeSelection
from nzbhydra.downloader import Nzbget, Sabnzbd
from nzbhydra.search import SearchRequest

logger = logging.getLogger('root')

app = Flask(__name__)
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
search_cache = Cache()
internal_cache = Cache(app, config={'CACHE_TYPE': "simple",  # Cache for internal data like settings, form, schema, etc. which will be invalidated on request
                                    "CACHE_DEFAULT_TIMEOUT": 60 * 30})


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


def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == config.get(mainSettings.username) and password == config.get(mainSettings.password)


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        'Could not verify your access level for that URL. You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})


# TODO: use this to create generic responses. the gui should have a service to intercept this and forward only the data (if it was successful) or else show the error, possibly log it
def create_json_response(success=True, data=None, error_message=None):
    return jsonify({"success": success, "data": data, "error_message": error_message})


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if mainSettings.enable_auth.get():
            auth = request.authorization
            if not auth or not check_auth(auth.username, auth.password):
                return authenticate()
        return f(*args, **kwargs)

    return decorated


@app.route('/<path:path>')
@app.route('/', defaults={"path": None})
@requires_auth
def base(path):
    logger.debug("Sending index.html")
    return send_file("static/index.html")


def render_search_results_for_api(search_results, total, offset):
    return render_template("api.html", channel={}, items=search_results, total=total, offset=offset)


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
    "providers": fields.String(missing=None),
    "provider": fields.String(missing=None),
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

    if args["q"] is not None:
        args["query"] = args["q"]  # Because internally we work with "query" instead of "q"
    if mainSettings.apikey.get_with_default(None) and ("apikey" not in args or args["apikey"] != mainSettings.apikey.get()):
        raise Unauthorized("API key not provided or invalid")

    elif args["t"] in ("search", "tvsearch", "movies"):
        search_request = SearchRequest(category=args["cat"], offset=args["offset"], limit=args["limit"], )
        if args["t"] == "search":
            search_request.query = args["query"]
            search_request.type = "general"
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
            search_request.identifier_key = "imdbid" if args["imdbid"] is not None else None
            search_request.identifier_value = args["imdbid"] if args["imdbid"] is not None else None
        result = search.search(False, search_request)
        results = process_for_external_api(result)
        content = render_search_results_for_api(results, result["total"], result["offset"])
        response = make_response(content)
        response.headers["Content-Type"] = "application/xml"
        return content

    elif args["t"] == "get":
        args = json.loads(urllib.parse.unquote(args["id"]))
        return extract_nzb_infos_and_return_response(args["provider"], args["guid"], args["title"], args["searchid"])
    elif args["t"] == "caps":
        return render_template("caps.html")
    else:
        pprint(request)
        return "hello api"


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

    "minsize": fields.Integer(missing=None),
    "maxsize": fields.Integer(missing=None),
    "minage": fields.Integer(missing=None),
    "maxage": fields.Integer(missing=None)
}


@app.route('/internalapi/search')
@requires_auth
@use_args(internalapi_search_args, locations=['querystring'])
@search_cache.memoize()
def internalapi_search(args):
    logger.debug("Search request with args %s" % args)
    search_request = SearchRequest(type="general", query=args["query"], offset=args["offset"], category=args["category"], minsize=args["minsize"], maxsize=args["maxsize"], minage=args["minage"], maxage=args["maxage"])
    results = search.search(True, search_request)
    return process_and_jsonify_for_internalapi(results)


internalapi_moviesearch_args = {
    "query": fields.String(missing=None),
    "category": fields.String(missing=None),
    "title": fields.String(missing=None),
    "imdbid": fields.String(missing=None),
    "offset": fields.Integer(missing=0),

    "minsize": fields.Integer(missing=None),
    "maxsize": fields.Integer(missing=None),
    "minage": fields.Integer(missing=None),
    "maxage": fields.Integer(missing=None)
}


@app.route('/internalapi/moviesearch')
@requires_auth
@use_args(internalapi_moviesearch_args, locations=['querystring'])
@search_cache.memoize()
def internalapi_moviesearch(args):
    logger.debug("Movie search request with args %s" % args)
    search_request = SearchRequest(type="movie", query=args["query"], offset=args["offset"], category=args["category"], minsize=args["minsize"], maxsize=args["maxsize"], minage=args["minage"], maxage=args["maxage"])
    if args["imdbid"]:
        search_request.identifier_key = "imdbid"
        search_request.identifier_value = args["imdbid"]
    results = search.search(True, search_request)
    return process_and_jsonify_for_internalapi(results)


internalapi_tvsearch_args = {
    "query": fields.String(missing=None),
    "category": fields.String(missing=None),
    "title": fields.String(missing=None),
    "tvdbid": fields.String(missing=None),
    "season": fields.String(missing=None),
    "episode": fields.String(missing=None),
    "offset": fields.Integer(missing=0),

    "minsize": fields.Integer(missing=None),
    "maxsize": fields.Integer(missing=None),
    "minage": fields.Integer(missing=None),
    "maxage": fields.Integer(missing=None)
}


@app.route('/internalapi/tvsearch')
@requires_auth
@use_args(internalapi_tvsearch_args, locations=['querystring'])
@search_cache.memoize()
def internalapi_tvsearch(args):
    logger.debug("TV search request with args %s" % args)
    search_request = SearchRequest(type="tv", query=args["query"], offset=args["offset"], category=args["category"], minsize=args["minsize"], maxsize=args["maxsize"], minage=args["minage"], maxage=args["maxage"], episode=args["episode"], season=args["season"], title=args["title"])
    if args["tvdbid"]:
        search_request.identifier_key = "tvdbid"
        search_request.identifier_value = args["tvdbid"]
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
    "provider": fields.String(missing=None),
}


@app.route('/internalapi/getnfo')
@requires_auth
@use_args(internalapi__getnfo_args, locations=['querystring'])
@search_cache.memoize()
def internalapi_getnfo(args):
    logger.debug("Get NFO  request with args %s" % args)
    nfo = get_nfo(args["provider"], args["guid"])
    return jsonify(nfo)


internalapi__getnzb_args = {
    "input": fields.String(missing=None),
    "guid": fields.String(missing=None),
    "provider": fields.String(missing=None),
    "searchid": fields.String(missing=None),
    "title": fields.String(missing=None)
}


@app.route('/internalapi/getnzb')
@requires_auth
@use_args(internalapi__getnzb_args, locations=['querystring'])
@search_cache.memoize()
def internalapi_getnzb(args):
    logger.debug("Get NZB request with args %s" % args)
    return extract_nzb_infos_and_return_response(args["provider"], args["guid"], args["title"], args["searchid"])


def extract_nzb_infos_and_return_response(provider, guid, title, searchid):
    if downloaderSettings.nzbaccesstype.get() == NzbAccessTypeSelection.redirect:  # I'd like to have this in api but don't want to have to use redirect() there...
        link = get_nzb_link(provider, guid, title, searchid)
        if link is not None:
            return redirect(link)
        else:
            return "Unable to build link to NZB", 404
    elif downloaderSettings.nzbaccesstype.get() == NzbAccessTypeSelection.serve.name:
        return get_nzb_response(provider, guid, title, searchid)
    else:
        logger.error("Invalid value of %s" % downloaderSettings.nzbaccesstype)
        return "downloader.add_type has wrong value", 500  # "direct" would never end up here, so it must be a wrong value


internalapi__addnzb_args = {
    "title": fields.String(missing=None),
    "providerguid": fields.String(missing=None),
    "provider": fields.String(missing=None),
    "searchid": fields.String(missing=None),
    "category": fields.String(missing=None)
}


@app.route('/internalapi/addnzb')
@requires_auth
@use_args(internalapi__addnzb_args, locations=['querystring'])
def internalapi_addnzb(args):
    logger.debug("Add NZB request with args %s" % args)
    if downloaderSettings.downloader.isSetting(config.DownloaderSelection.nzbget):
        downloader = Nzbget()
    else:
        downloader = Sabnzbd()

    if downloaderSettings.nzbAddingType.isSetting(config.NzbAddingTypeSelection.link):  # We send a link to the downloader. The link is either to us (where it gets answered or redirected, thet later getnzb will be called) or directly to the provider
        link = get_nzb_link(args["provider"], args["providerguid"], args["title"], args["searchid"])
        added = downloader.add_link(link, args["title"], args["category"])
        if added:
            return "Success"
        else:
            logger.error("Downloaded returned error while trying to add NZB for %s" % args["title"])
            return "Error", 500
    elif downloaderSettings.nzbAddingType.isSetting(NzbAddingTypeSelection.nzb):  # We download an NZB send it to the downloader
        nzbdownloadresult = download_nzb_and_log(args["provider"], args["providerguid"], args["title"], args["searchid"])
        if nzbdownloadresult is None:
            return "Error while downloading NZB"
        added = downloader.add_nzb(nzbdownloadresult.content, args["title"], args["category"])
        if added:
            return "Success"
        else:
            logger.error("Downloader returned error while trying to add NZB for %s" % args["title"])
            return "Error"
    else:
        logger.error("Invalid value of %s" % downloaderSettings.nzbAddingType)
        return "downloader.add_type has wrong value", 500  # "direct" would never end up here, so it must be a wrong value


@app.route('/internalapi/setsettings', methods=["PUT"])
@requires_auth
def internalapi_setsettings():
    logger.debug("Set settings request")
    try:
        config.import_config_data(request.get_json(force=True))
        internal_cache.delete_memoized(internalapi_getconfig)
        return "OK"
    except Exception as e:
        logger.exception("Error saving settings")
        return "Error: %s" % e


@app.route('/internalapi/getconfig')
@requires_auth
@internal_cache.memoize()
def internalapi_getconfig():
    logger.debug("Get config request")
    schema = config.get_settings_schema()
    settings = config.cfg
    form = config.get_settings_form()

    return jsonify({"schema": schema, "settings": settings, "form": form})


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
    app.run(host=host, port=port, debug=config.mainSettings.debug.get(), ssl_context=context)


def configure_cache():
    if mainSettings.cache_enabled.get():
        if mainSettings.cache_type == CacheTypeSelection.memory:
            logger.info("Using memory based cache")
            cache_type = "simple"
        else:
            logger.info("Using file based cache with folder %s" % mainSettings.cache_folder)
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
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        context.load_cert_chain(config.mainSettings.sslcert.get(), config.mainSettings.sslkey.get())
    return context
