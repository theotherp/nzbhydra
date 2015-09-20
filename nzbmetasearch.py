"""NZB Hydra
Usage:
    nzbhydra.py [--config=configfile]

Options:
  
  --config=<configfile>
  
"""
from functools import wraps
from pprint import pprint
from docopt import docopt
from flask import Flask, render_template, request, jsonify, Response
import profig
from webargs import Arg
from webargs.flaskparser import use_args
from werkzeug.exceptions import BadRequest, Unauthorized
from api import serialize_nzb_search_result

from config import cfg, init
import log
from search import Search

logger = log.setup_custom_logger('root')
search = Search()
app = Flask(__name__)


api_args = {
    #Todo: Throw exception on unsupported actions
    #TODO: validate using own code, web_args' return is not very helpful. Also we need to do a better consistency check anyway
    "apikey": Arg(str),
    "t": Arg(str),
    "q": Arg(str),
    "group": Arg(str),
    "limit": Arg(int), #for now we don't limit our results
    "offset": Arg(str), #so we dont use an offset
    "cat": Arg(str),
    "o": Arg(str),  #for now we only support xml which is what most tools ask for anyway
    "attrs": Arg(str),
    "extended": Arg(bool),  #TODO to test 
    "del": Arg(str),
    "maxage": Arg(str),
    "rid": Arg(str),
    "genre": Arg(str),
    "imbdid": Arg(str),
    "tvdbid": Arg(str),  #nzbs.org
    "season": Arg(str),
    "ep": Arg(str)

    #TODO: Support comments, music search, book search, details, etc(?)
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



init("main.username", "nzbhydra", str)
init("main.password", "hailhydra", str)
init("main.auth", True, bool)
def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return not cfg["main.auth"] or (username == cfg["main.username"] and password == cfg["main.password"])

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated        


@app.route('/')
@requires_auth
def base():
    return "hello"

@app.route('/api')
@use_args(api_args)
def api(args):
    
    
    if "apikey" not in args or args["apikey"] != cfg["main.apikey"]:
        print("Hallo")
        raise Unauthorized("API key not provided or invalid")
    if args["t"] == "search":
        results = search.search(args["q"], args["cat"])
        return render_search_results_for_api(results)
    if args["t"] == "tvsearch":
        results = search.search_show(args["rid"], args["season"], args["ep"], args["cat"])
        return render_search_results_for_api(results)
    pprint(request)
    return "hello api"

@app.route('/internalapi')
@requires_auth
@use_args(api_args)
def internal_api(args):
    from api import process_for_internal_api
    results = None
    if args["t"] == "search":
        results = search.search(args["q"], args["cat"])
    if args["t"] == "tvsearch":
        results = search.search_show(args["rid"], args["season"], args["ep"], args["cat"])
    if results is not None:
        results = process_for_internal_api(results)
        return jsonify(results)
    pprint(request)
    return "hello internal api"

    


init("main.port", 5050, int)
init("main.host", "0.0.0.0", str)
if __name__ == '__main__':
    arguments = docopt(__doc__, version='nzbhydra 0.0.1')
    
    if "--config" in arguments:
        from config import reload
        cfg = reload(arguments["--config"])
        #cfg.read(arguments["--config"])
        #cfg.sync()
    port = cfg["main.port"]
    host = cfg["main.host"]
    app.run(host=host, port=port, debug=False)
