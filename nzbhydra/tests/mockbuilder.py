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
from flask import app, render_template, Flask
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
        utcnow = arrow.utcnow().replace(day=random.randint(1, 28), hour=random.randint(1, 23))
        pubdate = str(utcnow.format("ddd, DD MMM YYYY HH:mm:ss Z"))
    if size is None:
        size = random.randint(10000, 10000000)
    if categories is None:
        categories = []
    size = str(size)

    attributes = [{
        "name": "size",
        "value": size
    },
        {"name": "guid",
         "value": guid}
    ]
    attributes.extend([{"name": "category", "value": x} for x in categories])

    return Bunch.fromDict({
        "guid": guid,
        "title": title,
        "link": link,
        "comments": "",
        "pubDate": pubdate,
        "description": description,
        "attributes": attributes

    })


def buildNewznabResponse(title, items, offset=0, total=None):
    if total is None:
        total = str(len(items))
    with app.test_request_context('/'):
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
    }
}


@mockapp.route('/api')
def serve():
    doSleep = False
    doGenerateDuplicates = False
    generateDuplicateGroupRange = 5

    indexer = indexers[request.args.get("apikey")]

    if doSleep:
        sleep(indexer["delay"])
    if doGenerateDuplicates:
        pubDates = [arrow.get(random.randint(1412677738, 1475836139)).format("ddd, DD MMM YYYY HH:mm:ss Z") for x in range(0, generateDuplicateGroupRange)]
        sizes = [random.randint(100000, 10000000) for x in range(0, generateDuplicateGroupRange)]
        titles = ["title%d" % x for x in range(0, generateDuplicateGroupRange)]
    indexerName = indexer["name"]
    title = indexer["name"]
    numberOfTotalResults = indexer["numberOfTotalResults"]
    offset = int(request.args.get("offset")) if "offset" in request.args.keys() else 0
    resultBaseName = "indexer%s" % indexerName
    categories = ["2000"]

    items = []
    for i in range(offset, min(offset + 100, numberOfTotalResults)):
        if doGenerateDuplicates:
            searchResultTitle = titles[random.randint(0, generateDuplicateGroupRange - 1)]
            searchResultPubDate = pubDates[random.randint(0, generateDuplicateGroupRange - 1)]
            searchResultSize = sizes[random.randint(0, generateDuplicateGroupRange - 1)]
        else:
            searchResultTitle = resultBaseName + " title" + str(i)
            searchResultPubDate = arrow.get(random.randint(1412677738, 1475836139)).format("ddd, DD MMM YYYY HH:mm:ss Z")
            searchResultSize = random.randint(100000, 10000000)
        searchResultguid = resultBaseName + "-guid-" + str(random.randint(1000, 10000000)) + str(i)
        searchResultLink = resultBaseName + "-link-" + str(i)
        searchResultDescription = resultBaseName + "-description-" + str(i)
        item = buildNewznabItem(title=searchResultTitle, guid=searchResultguid, link=searchResultLink, pubdate=searchResultPubDate, description=searchResultDescription, size=searchResultSize, indexer_name=indexerName, categories=categories)
        items.append(item)
    result = render_template("api.html", items=items, offset=offset, total=numberOfTotalResults, title=title, description=title + " - description")
    return result


mockapp.run(port=5000, use_reloader=True, threaded=True)
