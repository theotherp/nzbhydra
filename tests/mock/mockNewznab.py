import os
from flask import Flask, send_file
from webargs.flaskparser import use_args

from webargs import core, Arg
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


parser = core.Parser()

@app.route('/nzbsorg')
@use_args(api_args)
def apinzbsorg(args):
    return handle_request("nzbsorg", args)
    

@app.route('/dognzb')
@use_args(api_args)
def apidog(args):
    return handle_request("dognzb", args)

@app.route('/nzbclubrss')
def nzbclubrss():
    #todo
    pass

    
def handle_request(provider, args):
    keys_sorted = sorted(args.keys())
    keys_sorted.remove("apikey")
    keys_sorted.remove("extended")
    keys_sorted.remove("o")
    filename = provider
    for arg in keys_sorted:
        if args[arg] is not None:
            filename = "%s--%s-%s" % (filename, arg, args[arg])
    filename += ".json"
    
    if os.path.exists(filename):
        print("Sending " + filename)
        return send_file(filename, "application/javascript")
    else:
        print("Cannot find respose " + filename)
        return "Unknown request", 404


            
    

if __name__ == '__main__':
    app.run(port=5001, debug=True)
