from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from bunch import Bunch
from future import standard_library

#standard_library.install_aliases()
from builtins import *
import random
import string
import arrow
from flask import app, render_template, Flask

app = Flask(__name__)


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
