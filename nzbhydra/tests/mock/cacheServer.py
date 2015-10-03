from flask import Flask, request
from flask.ext.cache import Cache
from furl import furl
import requests

app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'filesystem', 'CACHE_DIR': 'cache'})


@app.route('/nzbsorg')
@app.route('/nzbsorg/api')
def apinzbsorg():
    return handle_request(request.args.items(), "https://nzbs.org/api")


@app.route('/dognzb')
@app.route('/dognzb/api')
def apidog():
    return handle_request(request.args.items(), "https://api.dognzb.cr/api")


@app.route('/nzbclub/api/NFO/<path:guid>')
def nzbindexapi(guid):
    print("Get nfo from web via %s " % "https://www.nzbclub.com/api/NFO/" + guid)
    r = requests.get("https://www.nzbclub.com/api/NFO/" + guid)
    return r.text, r.status_code


@app.route('/nzbclub')
def nzbclubrss():
    return handle_request(request.args.items(), "https://www.nzbclub.com/nzbrss.aspx")


@app.route('/womble')
def womble():
    return handle_request(request.args.items(), "https://www.newshost.co.za/rss/")


@app.route('/nzbindex')
@app.route('/nzbindex/<path:path>')
def nzbindex(path):
    return handle_request(request.args.items(), "https://nzbindex.com/" + path, cookies={"agreed": "true", "lang": "2"})


@app.route('/binsearch')
@app.route('/binsearch/<path:file>')
def binsearch(file):
    return handle_request(request.args.items(), "https://www.binsearch.info/" + file)


@cache.memoize()
def get(url, cookies):
    print("Requesting URL " + url)
    r = requests.get(url, verify=False, cookies=cookies)
    if r.status_code != 200:
        return r.text, 500
    else:
        return r.text


def handle_request(argsitems, baseurl, cookies=None):
    if not cookies:
        cookies = []
    args = {}
    for i in argsitems:
        args[i[0]] = i[1]

    f = furl(baseurl)
    sortedkeys = sorted(args.keys())
    for key in sortedkeys:
        f.add({key: str(args[key])})
    return get(f.tostr(), cookies=cookies)


if __name__ == '__main__':
    app.run(port=5001, debug=True)
