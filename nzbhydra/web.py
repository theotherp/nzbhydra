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

externalapi_args = {
    "input": Arg(str),
    "apikey": Arg(str),
    "t": Arg(str),
    "q": Arg(str),
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
    
    "input": Arg(str)
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
@use_args(externalapi_args)
def api(args):
    if config.cfg["main.apikey"] and ("apikey" not in args or args["apikey"] != config.cfg["main.apikey"]):
        raise Unauthorized("API key not provided or invalid")
    if args["t"] == "search":
        results = search.search(False, args["q"], args["cat"])
        return render_search_results_for_api(results)
    if args["t"] == "tvsearch":
        # search_show(query=None, identifier_key=None, identifier_value=None, season=None, episode=None, categories=None)
        identifier_key = "rid" if args["rid"] else "tvdbid" if args["tvdbid"] else None
        identifier_value = args[identifier_key] if identifier_key else None
        results = search.search_show(False, args["q"], identifier_key, identifier_value, args["season"], args["ep"], args["cat"])
        return render_search_results_for_api(results)
    pprint(request)
    return "hello api"


@app.route('/internalapi')
@requires_auth
@use_args(internalapi_args)
def internal_api(args):
    
    
    results = None
    if args["t"] == "search":
        results = search.search(True, args)
    if args["t"] == "tvsearch":   
        results = search.search_show(True, args)
    if args["t"] == "moviesearch":
        results = search.search_movie(True, args)
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