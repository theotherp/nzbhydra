import os

from flask import Flask, send_file, request
from flask.ext.cache import Cache
from furl import furl
import requests

app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'filesystem', 'CACHE_DIR': 'cache'})


@app.route('/nzbsorg')
@app.route('/nzbsorg/api')
@cache.memoize()
def apinzbsorg():
    return handle_request(request.args.items(), "https://nzbs.org/api")


@app.route('/dognzb')
@app.route('/dognzb/api')
def apidog():
    return handle_request(request.args.items(), "https://api.dognzb.cr/api")


@app.route('/nzbclub/api/NFO/<path:guid>')
@cache.memoize()
def nzbindexapi(guid):
    r = requests.get("https://www.nzbclub.com/api/NFO/" + guid)
    print("Get nfo from web")
    return r.text, r.status_code


@app.route('/nzbclub')
@cache.memoize()
def nzbclubrss():
    return handle_request(request.args.items(), "https://www.nzbclub.com/nzbrss.aspx")


@app.route('/womble')
@cache.memoize()
def womble():
    return handle_request(request.args.items(), "https://www.newshost.co.za/rss/")


@app.route('/nzbindex')
@cache.memoize()
def nzbindex():
    return handle_request(request.args.items(), "https://nzbindex.com/rss")


@app.route('/binsearch')
@cache.memoize()
def binsearch():
    return handle_request( request.args.items(), "https://www.binsearch.info/index.php")


def handle_request(argsitems,  baseurl):
    args = {}
    for i in argsitems:
        args[i[0]] = i[1]
    
    f = furl(baseurl)
    for key in args.keys():
        f.add({key: str(args[key])})

    print("Requesting URL " + f.tostr())
    r = requests.get(f.tostr(), verify=False)
    if r.status_code != 200:
        return r.text, 500
    else:
        return r.text
        

    


if __name__ == '__main__':
    app.run(port=5001, debug=True)
