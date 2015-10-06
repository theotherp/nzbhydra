from functools import wraps
import logging
from pprint import pprint
import ssl

from flask import send_file, redirect
from flask import Flask, render_template, request, jsonify, Response
from flask.ext.cache import Cache
from webargs import Arg

from webargs.flaskparser import use_args

from werkzeug.exceptions import Unauthorized

from nzbhydra.api import process_for_internal_api, get_nfo, process_for_external_api, get_nzb_link, get_nzb_response, download_nzb_and_log
from nzbhydra import config, search, infos
from nzbhydra.config import NzbAccessTypeSelection, NzbAddingTypeSelection, mainSettings, downloaderSettings, CacheTypeSelection
from nzbhydra.downloader import Nzbget

logger = logging.getLogger('root')

app = Flask(__name__)

cache = Cache()

externalapi_args = {
    "input": Arg(str),
    "apikey": Arg(str),
    "t": Arg(str),
    "q": Arg(str),
    "query": Arg(str),
    "group": Arg(str),
    "limit": Arg(int),
    "offset": Arg(str),
    "cat": Arg(str),
    "o": Arg(str),
    "attrs": Arg(str),
    "extended": Arg(bool),
    "del": Arg(str),
    "rid": Arg(str),
    "genre": Arg(str),
    "imdbid": Arg(str),
    "tvdbid": Arg(str),
    "season": Arg(str),
    "ep": Arg(str)
}

internalapi_args = {
    "apikey": Arg(str),
    "t": Arg(str),
    "query": Arg(str),
    "category": Arg(str),
    "title": Arg(str),
    "rid": Arg(str),
    "imdbid": Arg(str),
    "tvdbid": Arg(str),
    "season": Arg(str),
    "episode": Arg(str),

    "minsize": Arg(int),
    "maxsize": Arg(int),
    "minage": Arg(int),
    "maxage": Arg(int),

    "input": Arg(str),
    "guid": Arg(str),
    "provider": Arg(str),
    "searchid": Arg(str),

    "link": Arg(str),
    "downloader": Arg(str),

}

from webargs import core

parser = core.Parser()


class CustomError(Exception):
    pass


@parser.error_handler
def handle_error(error):
    print(error)
    raise CustomError(error)


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


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if config.get(mainSettings.enable_auth):
            auth = request.authorization
            if not auth or not check_auth(auth.username, auth.password):
                return authenticate()
        return f(*args, **kwargs)

    return decorated


@app.route('/<path:path>')
@app.route('/', defaults={"path": None})
@requires_auth
def base(path):
    return send_file("static/index.html")


def render_search_results_for_api(search_results):
    return render_template("api.html", channel={}, items=search_results)


@app.route('/api')
@use_args(externalapi_args)
def api(args):
    print(args)
    print(request.url)
    # Map newznab api parameters to internal
    if args["q"] is not None:
        args["query"] = args["q"]  # Because internally we work with "query" instead of "q"
    # todo: category mapping, completely forgot that
    if config.get(mainSettings.apikey, None) is not None and ("apikey" not in args or args["apikey"] != config.get(mainSettings.apikey)):
        raise Unauthorized("API key not provided or invalid")
    elif args["t"] == "search":
        results = search.search(False, args)
    elif args["t"] == "tvsearch":
        results = search.search_show(False, args)
    else:
        pprint(request)
        return "hello api"
    results = process_for_external_api(results)
    return render_search_results_for_api(results)


@app.route('/internalapi')
@requires_auth
@use_args(internalapi_args, locations=['querystring'])
@cache.memoize()
def internal_api(args):
    results = None

    if args["t"] in ("search", "tvsearch", "moviesearch"):
        if args["t"] == "search":
            results = search.search(True, args)
        if args["t"] == "tvsearch":
            results = search.search_show(True, args)
        if args["t"] == "moviesearch":
            results = search.search_movie(True, args)

        if results is not None:
            results = process_for_internal_api(results)
            return jsonify(results)  # Flask cannot return lists
        else:
            return "No results", 500
    if args["t"] == "autocompletemovie":
        results = infos.find_movie_ids(args["input"])
        return jsonify({"results": results})
    if args["t"] == "autocompleteseries":
        results = infos.find_series_ids(args["input"])
        return jsonify({"results": results})
    if args["t"] == "categories":
        return jsonify(search.categories)
    if args["t"] == "getnfo":
        nfo = get_nfo(args["provider"], args["guid"])
        return jsonify(nfo)
    if args["t"] == "getnzb":  # Returns an NZB. This will probably be only called (internally) if the user wants to download an NZB instead of adding it to the downloader
        if downloaderSettings.nzbaccesstype.isSetting(NzbAccessTypeSelection.redirect):  # I'd like to have this in api but don't want to have to use redirect() there...
            link = get_nzb_link(args["provider"], args["guid"], args["title"], args["searchid"])
            if link is not None:
                return redirect(link)
            else:
                return "Unable to build link to NZB", 404
        elif downloaderSettings.nzbaccesstype.isSetting(NzbAccessTypeSelection.serve):
            return get_nzb_response(args["provider"], args["guid"], args["title"], args["searchid"])
        else:
            logger.error("Invalid value of %s" % downloaderSettings.nzbaccesstype)
            return "downloader.add_type has wrong value", 500  # "direct" would never end up here, so it must be a wrong value
    if args["t"] == "addnzb":
        # todo read config
        downloader = Nzbget()
        if downloaderSettings.nzbAddingType.isSetting(NzbAddingTypeSelection.link):  # We send a link to the downloader. The link is either to us (where it gets answered or redirected, thet later getnzb will be called) or directly to the provider
            link = get_nzb_link(args["provider"], args["guid"], args["title"], args["searchid"])
            added = downloader.add_link(link, args["title"], args["category"])
            if added:
                return "Success"
            else:
                return "Error", 500
        elif downloaderSettings.nzbAddingType.isSetting(NzbAddingTypeSelection.nzb):  # We download an NZB send it to the downloader
            nzbdownloadresult = download_nzb_and_log(args["provider"], args["guid"], args["title"], args["searchid"])
            added = downloader.add_nzb(nzbdownloadresult.content, args["title"], args["category"])
            if added:
                return "Success"
            else:
                return "Error", 500
        else:
            logger.error("Invalid value of %s" % downloaderSettings.nzbAddingType)
            return "downloader.add_type has wrong value", 500  # "direct" would never end up here, so it must be a wrong value
    if args["t"] == "getsettings":
        return jsonify(config.get_settings_dict())

    return "hello internal api", 500


def run(host, port):
    context = create_context()

    configure_cache()

    app.run(host=host, port=port, debug=config.mainSettings.debug.get(), ssl_context=context)


def configure_cache():
    if mainSettings.cache_enabled.get():
        if mainSettings.cache_type.isSetting(CacheTypeSelection.memory):
            logger.info("Using memory based cache")
            cache_type = "simple"
        else:
            logger.info("Using file based cache with folder %s" % mainSettings.cache_folder)
            cache_type = "filesystem"
    else:
        logger.info("Not using any caching")
        cache_type = "null"
    cache.init_app(app, config={'CACHE_TYPE': cache_type,
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
