import random
import string

import arrow


def buildNewznabItem(id=None, title=None, guid=None, link=None, pubdate=None, description=None, size=None, provider_name=None, categories=[]):
    if title is None:
        ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
    if id is None:
        id = title + ".id"
    if guid is None:
        guid = title + ".guid"
    if link is None:
        link = "http://www.%s.info/%s" % (provider_name if provider_name is not None else "aprovider", title)
    if description is None:
        description = title + ".description"
    if pubdate is None:
        # "pubDate": "Fri, 18 Sep 2015 14:11:15 -0600",
        utcnow = arrow.utcnow().replace(day=random.randint(1, 28), hour=random.randint(1, 23))
        pubdate = str(utcnow.format("ddd, DD MMM YYYY HH:mm:ss Z"))
    if size is None:
        size = random.randint(10000, 10000000)
    size = str(size)

    attributes = [{"@attributes": {
        "name": "size",
        "value": size
    }}]
    attributes.extend([{"@attributes": {"name": "category", "value": x}} for x in categories])

    return {
        "id": id,
        "title": title,
        "guid": guid,
        "link": link,
        "comments": "",
        "pubDate": pubdate,
        "description": description,
        "enclosure": {
            "@attribute": {
                "url": link,
                "length": size,
                "type": "appplication/x-nzb"
            }
        },
        "attr": attributes

    }


def buildNewznabResponse(title, items, offset=0, total=None):
    if total is None:
        total = str(len(items))
    return {"@attributes": "2.0",
            "channel":
                {
                    "title": title,
                    "description": title + " - description",
                    "uuid": "uuid",
                    "response": {
                        "@attributes": {
                            "offset": str(offset),
                            "total": total}
                    },
                    "item": items
                }

            }
