from flask import Flask, render_template, request, send_file
from werkzeug.exceptions import Unauthorized
from nzbhydra.api import process_for_internal_api
from nzbhydra import config, search, infos
from functools import wraps
from pprint import pprint
from flask import Flask, render_template, request, jsonify, Response
from webargs import Arg
from webargs.flaskparser import use_args
from werkzeug.exceptions import Unauthorized

app = Flask(__name__)

api_args = {
    # Todo: Throw exception on unsupported actions
    # TODO: validate using own code, web_args' return is not very helpful. On the other side the api is only consumed by us or external tools which better know what they're doing...
    "input": Arg(str),
    "apikey": Arg(str),
    "t": Arg(str),
    "q": Arg(str),
    "group": Arg(str),
    "limit": Arg(int),  # for now we don't limit our results
    "offset": Arg(str),  # so we dont use an offset
    "cat": Arg(str),
    "o": Arg(str),  # for now we only support xml which is what most tools ask for anyway
    "attrs": Arg(str),
    "extended": Arg(bool),  # TODO to test 
    "del": Arg(str),
    "maxage": Arg(str),
    "rid": Arg(str),
    "genre": Arg(str),
    "imdbid": Arg(str),
    "tvdbid": Arg(str),  # nzbs.org
    "season": Arg(str),
    "ep": Arg(str)

    # TODO: Support comments, music search, book search, details, etc(?)
}

from webargs import core

parser = core.Parser()


class CustomError(Exception):
    pass


@parser.error_handler
def handle_error(error):
    print(error)
    raise CustomError(error)


def render_search_results_for_api(search_results):
    return render_template("api.html", channel={}, items=search_results)


config.init("main.username", "nzbhydra", str)
config.init("main.password", "hailhydra", str)
config.init("main.apikey", "hailhydra", str)
config.init("main.auth", True, bool)


def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == config.cfg["main.username"] and password == config.cfg["main.password"]


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        'Could not verify your access level for that URL. You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if config.cfg["main.auth"]:
            auth = request.authorization
            if not auth or not check_auth(auth.username, auth.password):
                return authenticate()
        return f(*args, **kwargs)

    return decorated


@app.route('/')
@requires_auth
def base():
    return send_file("static/index.html")


@app.route('/api')
@use_args(api_args)
def api(args):
    if config.cfg["main.apikey"] and ("apikey" not in args or args["apikey"] != config.cfg["main.apikey"]):
        raise Unauthorized("API key not provided or invalid")
    if args["t"] == "search":
        results = search.search(args["q"], args["cat"])
        return render_search_results_for_api(results)
    if args["t"] == "tvsearch":
        # search_show(query=None, identifier_key=None, identifier_value=None, season=None, episode=None, categories=None)
        identifier_key = "rid" if args["rid"] else "tvdbid" if args["tvdbid"] else None
        identifier_value = args[identifier_key] if identifier_key else None
        results = search.search_show(args["q"], identifier_key, identifier_value, args["season"], args["ep"], args["cat"])
        return render_search_results_for_api(results)
    pprint(request)
    return "hello api"


@app.route('/internalapi')
@requires_auth
@use_args(api_args)
def internal_api(args):
    
    results = None
    if args["t"] == "search":
        results = search.search(args["q"], args["cat"])
    if args["t"] == "tvsearch":
        #search_show(query=None, identifier_key=None, identifier_value=None, season=None, episode=None, categories=None):
        key = None
        value = None
        if "tvdbid" in args:
            key = "tvdbid"
            value = args[key]            
        results = search.search_show(args["q"], key, value, args["season"], args["ep"], args["cat"])
    if args["t"] == "moviesearch":
        results = search.search_movie(args["q"], args["imdbid"], args["cat"])
    if args["t"] == "autocompletemovie":
        results = infos.find_movie_ids(args["input"])
        return jsonify({"results": results})
    if args["t"] == "autocompleteseries":
        results = infos.find_series_ids(args["input"])
        return jsonify({"results": results})
    if args["t"] == "categories":
        return jsonify(search.categories)
    if results is not None:
        results = process_for_internal_api(results)
        return jsonify(results)  # Flask cannot return lists
    return "hello internal api"