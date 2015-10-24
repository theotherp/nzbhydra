from random import randint

import arrow
from flask import Flask, request, redirect, send_file, render_template
from flask.ext.cache import Cache
from furl import furl
import requests

app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'filesystem', 'CACHE_DIR': 'cache', 'DEFAULT_THRESHOLD': 500, 'DEFAULT_TIMEOUT': 60 * 60 * 24 * 7})


@app.route('/rss/')
def nothing():
    return send_file("womble--sec-tv-dvd.xml")


@app.route('/nzbsorg')
@app.route('/nzbsorg/api')
def apinzbsorg():
    if "q" in request.args.keys() and request.args.get("q") == "pagingtest":
        start = int(request.args.get("offset") if "offset" in request.args.keys() else 0)
        end = start + 100
        print("Returning elements %d-%d from nzbsorg" % (start, end))
        return render_template("api.html", items=[{"count": x, "date": arrow.get(100000000-x*100000).format('ddd, DD MMM YYYY HH:mm:ss Z'), "guid":x} for x in range(start, end)], offset=request.args.get("offset"), total=500, provider="a title")
    if "q" in request.args.keys() and request.args.get("q") == "sortingtest":
        return render_template("api.html", items=[{"count": 1, "date": arrow.get(100000000-200000).format('ddd, DD MMM YYYY HH:mm:ss Z'), "guid":1, "size":100000}], offset=request.args.get("offset"), total=1, provider="a title")
    
    return handle_request(request.args.items(), "https://nzbs.org/api")


@app.route('/dognzb')
@app.route('/dognzb/api')
def apidog():
    if "q" in request.args.keys() and request.args.get("q") == "pagingtest":
        start = int(request.args.get("offset") if "offset" in request.args.keys() else 0)
        end = start + 100
        print("Returning elements %d-%d from dognzb" % (start, end))
        return render_template("api.html", items=[{"count": x, "date": arrow.get(100000000-x*100000).format('ddd, DD MMM YYYY HH:mm:ss Z'), "guid":x} for x in range(start, end)], offset=request.args.get("offset"), total=375, provider="a title")
    if "q" in request.args.keys() and request.args.get("q") == "sortingtest":
        return render_template("api.html", items=[{"count": 1, "date": arrow.get(100000000-100000).format('ddd, DD MMM YYYY HH:mm:ss Z'), "guid":1, "size":10000000}], offset=request.args.get("offset"), total=1, provider="a title")
    return handle_request(request.args.items(), "https://api.dognzb.cr/api")


@app.route('/drunken')
@app.route('/drunkenslug/api')
def apislug():
    return handle_request(request.args.items(), "https://drunkenslug.com/api")


@app.route('/nzbclub/api/NFO/<path:guid>')
def nzbindexapi(guid):
    print("Get nfo from web via %s " % "https://www.nzbclub.com/api/NFO/" + guid)
    r = requests.get("https://www.nzbclub.com/api/NFO/" + guid)
    return r.text, r.status_code


@app.route('/nzbclub/<path:path>')
def nzbclubrss(path):
    return handle_request(request.args.items(), "https://www.nzbclub.com/nzbrss.aspx")


@app.route('/womble')
@app.route('/womble/<path:path>')
def womble(path):
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
    r = requests.get(url, verify=False, cookies=cookies, timeout=5)
    if r.status_code != 200:
        return r.text, 500
    else:
        return r.text


def handle_request(argsitems, baseurl, cookies=None, doredirect=False):
    if not cookies:
        cookies = []
    args = {}
    for i in argsitems:
        args[i[0]] = i[1]

    f = furl(baseurl)
    sortedkeys = sorted(args.keys())
    for key in sortedkeys:
        f.add({key: str(args[key])})
    if doredirect:
        return redirect(f.tostr())
    return get(f.tostr(), cookies=cookies)


if __name__ == '__main__':
    app.run(port=5001, debug=True)
