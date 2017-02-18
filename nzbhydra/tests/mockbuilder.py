from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import random
import string
from time import sleep

import arrow
from builtins import *
from bunch import Bunch
from flask import Response
from flask import render_template, Flask
from flask import request

mockapp = Flask(__name__)


def buildNewznabItem(title=None, guid=None, link=None, pubdate=None, description=None, size=None, indexer_name=None, categories=None):
    if title is None:
        ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
    if guid is None:
        guid = title + ".guid"
    if link is None:
        link = "http://www.%s.info/%s" % (indexer_name if indexer_name is not None else "aindexer", title)
    if description is None:
        description = title + ".description"
    if pubdate is None:
        # "pubDate": "Fri, 18 Sep 2015 14:11:15 -0600",
        pubdate = str(arrow.get(arrow.utcnow().timestamp - random.randint(10000)).format("ddd, DD MMM YYYY HH:mm:ss Z"))
    if not size:
        size = random.randint(10000, 10000000)
    if categories is None:
        categories = []
    size = str(size)

    attributes = [
        {
            "name": "size",
            "value": size
        },
        {"name": "guid",
         "value": guid
         },
        {"name": "files",
         "value": random.randint(1, 500)
         },
        {"name": "grabs",
         "value": random.randint(0, 100)
         },
        {"name": "comments",
         "value": random.randint(0, 3)
         },
        {"name": "poster",
         "value": random.randint(0, 100)
         },
        {"name": "group",
         "value": random.randint(0, 10)
         },

    ]
    attributes.extend([{"name": "category", "value": x} for x in categories])

    return Bunch.fromDict({
        "guid": guid,
        "title": title,
        "link": link,
        "comments": "",
        "pubDate": pubdate,
        "size": size,
        "description": description,
        "attributes": attributes,
        "poster": str(random.randint(1, 100)),
        "group": str(random.randint(1, 10))

    })


def buildNewznabResponse(title, items, offset=0, total=None):
    if total is None:
        total = str(len(items))
    with mockapp.test_request_context('/'):
        result = render_template("api.html", items=items, offset=offset, total=total, title=title, description=title + " - description")
        return result


indexers = {
    "a": {
        "name": "a",
        "numberOfTotalResults": 500,
        "delay": 0
    },
    "b": {
        "name": "b",
        "numberOfTotalResults": 400,
        "delay": 1
    },
    "c": {
        "name": "c",
        "numberOfTotalResults": 300,
        "delay": 2
    },
    "d": {
        "name": "d",
        "numberOfTotalResults": 200,
        "delay": 1
    },
    "e": {
        "name": "e",
        "numberOfTotalResults": 100,
        "delay": 0
    },
    "f": {
        "name": "f",
        "numberOfTotalResults": 50,
        "delay": 1
    },
    "g": {
        "name": "g",
        "numberOfTotalResults": 25,
        "delay": 2
    },
    "h": {
        "name": "h",
        "numberOfTotalResults": 50,
        "delay": 1
    },
    "i": {
        "name": "i",
        "numberOfTotalResults": 75,
        "delay": 0
    },
    "j": {
        "name": "j",
        "numberOfTotalResults": 100,
        "delay": 1
    },
    "k": {
        "name": "k",
        "numberOfTotalResults": 125,
        "delay": 2
    },
    "l": {
        "name": "l",
        "numberOfTotalResults": 150,
        "delay": 1
    },
    "m": {
        "name": "m",
        "numberOfTotalResults": 175,
        "delay": 0
    },
    "n": {
        "name": "n",
        "numberOfTotalResults": 200,
        "delay": 1
    },
    "o": {
        "name": "o",
        "numberOfTotalResults": 225,
        "delay": 2
    },
}

pubDates = None
sizes = None
titles = None


@mockapp.route('/api')
def serve():
    if request.args.get("t") == "caps":
        with open("mock/nocaps.xml") as f:
            return "Hallo"
            return f.read()

    global pubDates
    global sizes
    global titles

    doSleep = False
    doGenerateDuplicates = False
    generateDuplicateGroupRange = 5
    doGenerateNewGuids = True
    doSwitchGenerateNewGuidsDependingOnQuery = True
    doSendAll = True
    doThrowSomeErrors = False

    if doThrowSomeErrors and random.randint(0, 1) < 5:
        return "Nope"

    indexer = indexers[request.args.get("apikey")]

    if doSleep:
        sleep(indexer["delay"])
    if doGenerateDuplicates and pubDates is None:  # Only generate once
        pubDates = [arrow.get(random.randint(1412677738, 1475836139)).format("ddd, DD MMM YYYY HH:mm:ss Z") for x in xrange(0, generateDuplicateGroupRange)]
        sizes = [random.randint(100000, 10000000) for x in xrange(0, generateDuplicateGroupRange)]
        titles = ["title%d" % x for x in xrange(0, generateDuplicateGroupRange)]
    indexerName = indexer["name"]
    title = indexer["name"]
    query = str(request.args.get("q")) if "q" in request.args.keys() else None
    numberOfTotalResults = indexer["numberOfTotalResults"] if query != "0" else 0
    offset = int(request.args.get("offset")) if "offset" in request.args.keys() else 0
    resultBaseName = "indexer%s" % indexerName
    if query:
        resultBaseName += "-" + query
        if doSwitchGenerateNewGuidsDependingOnQuery:
            doGenerateNewGuids = int(query) % 2 == 0
            print("Switched generation of new GUIDs to " + str(doGenerateNewGuids))

    items = []

    if doSendAll:
        r = range(0, numberOfTotalResults)
    else:
        r = range(offset, min(offset + 100, numberOfTotalResults))
    for i in r:
        if doGenerateDuplicates:
            searchResultTitle = titles[random.randint(0, generateDuplicateGroupRange - 1)]
            searchResultPubDate = pubDates[random.randint(0, generateDuplicateGroupRange - 1)]
            searchResultSize = sizes[random.randint(0, generateDuplicateGroupRange - 1)]
        else:
            searchResultTitle = resultBaseName + " title" + str(i)
            searchResultPubDate = arrow.get(random.randint(1412677738, 1475836139)).format("ddd, DD MMM YYYY HH:mm:ss Z")
            searchResultSize = random.randint(100000, 10000000)
        if doGenerateNewGuids:
            searchResultguid = resultBaseName + "-guid-" + str(random.randint(1000, 10000000)) + str(i)
        else:
            searchResultguid = resultBaseName + "-guid-" + str(i)
        searchResultLink = "http://127.0.0.1:5000/download"
        searchResultDescription = resultBaseName + "-description-" + str(i)
        item = buildNewznabItem(title=searchResultTitle, guid=searchResultguid, link=searchResultLink, pubdate=searchResultPubDate, description=searchResultDescription, size=searchResultSize, indexer_name=indexerName, categories=[["2000", "3000", "4000", "5000", "6000"][random.randint(0, 4)]])
        items.append(item)
    result = render_template("api.html", items=items, offset=offset, total=numberOfTotalResults, title=title, description=title + " - description")

    return Response(result, mimetype='text/xml')


@mockapp.route('/download')
def download():
    randomNumber = random.randint(0, 100)
    name = "Some nzb content %d" % randomNumber
    return Response(name, mimetype="application/x-nzb",
                    headers={"Content-disposition":
                                 "attachment; filename=Some nzb %d.nzb" % randomNumber})


if __name__ == '__main__':
    mockapp.run(port=5000, use_reloader=True, threaded=True)
