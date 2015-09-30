import os
from time import sleep

from flask import Flask, send_file
from webargs.flaskparser import use_args
from webargs import core, Arg

app = Flask(__name__)

api_args = {
    # Todo: Throw exception on unsupported actions
    # TODO: validate using own code, web_args' return is not very helpful. Also we need to do a better consistency check anyway
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
    "imbdid": Arg(str),
    "tvdbid": Arg(str),
    "id": Arg(str),  
    "season": Arg(str),
    "ep": Arg(str),
    "sec": Arg(str),  # womble
    "fr": Arg(str),  # womble

    "ig": Arg(str),  # nzbclub
    "rpp": Arg(str),  # nzbclub
    "st": Arg(str),  # nzbclub
    "sp": Arg(str),  # nzbclub
    "ns": Arg(str),  # nzbclub

    "more": Arg(str),  # nzbindex
    "sort": Arg(str),  # nzbindex
    "max": Arg(str),  # nzbindex
    
    
    # TODO: Support comments, music search, book search, details, etc(?)

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


@app.route('/nzbclub')
@use_args(api_args)
def nzbclubrss(args):
    # todo http://member.nzbclub.com/nzbfeeds.aspx?q=avengers&ig=1&rpp=200&st=5&sp=1&ns=1
    return handle_request("nzbclub", args)
    pass


@app.route('/womble')
@use_args(api_args)
def womble(args):
    return handle_request("womble", args)


@app.route('/nzbindex')
@use_args(api_args)
def nzbindex(args):
    return handle_request("nzbindex", args)


@app.route('/binsearch')
@use_args(api_args)
def binsearch(args):
    return handle_request("binsearch", args)


def handle_request(provider, args):
    keys_sorted = sorted(args.keys())
    keys_sorted.remove("apikey")
    keys_sorted.remove("extended")
    keys_sorted.remove("o")
    keys_sorted.remove("fr")
    keys_sorted.remove("ig")
    keys_sorted.remove("rpp")
    keys_sorted.remove("st")
    keys_sorted.remove("sp")
    keys_sorted.remove("ns")
    keys_sorted.remove("sort")
    keys_sorted.remove("max")
    keys_sorted.remove("more")
    filename = provider
    for arg in keys_sorted:
        if args[arg] is not None:
            filename = "%s--%s-%s" % (filename, arg, args[arg])
    if os.path.exists(filename + ".json"):
        print("Sending " + filename)
        return send_file(filename + ".json", "application/javascript")
    if os.path.exists(filename + ".xml"):
        print("Sending " + filename)
        return send_file(filename + ".xml", "application/xm")
    if os.path.exists(filename + ".html"):
        print("Sending " + filename)
        return send_file(filename + ".html", "text/html")
    else:
        print("Cannot find respose " + filename)
        return "Unknown request", 404


if __name__ == '__main__':
    app.run(port=5001, debug=True)
