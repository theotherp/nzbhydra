from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import threading
from time import sleep

import arrow
import requests


def startTest(query):
    try:
        print("Starting request")
        before = arrow.now()
        r = requests.get("http://127.0.0.1:5075/api?apikey=apikey&t=search&q=%s" % query)
        r.raise_for_status()
        after = arrow.now()
        took = (after - before).seconds * 1000 + (after - before).microseconds / 1000
        print("Request completed successfully in %dms" % took)
    except Exception as e:
        print(e)


threads = []
for i in range(0, 1):
    t = threading.Thread(target=startTest, args=(str(i),))
    sleep(1)
    threads.append(t)
    t.start()
