from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import random
import string
import threading

import arrow
import time
import requests


def startTest():
    try:
        print("Starting request")
        before = arrow.now()
        r = requests.get("http://127.0.0.1:5075/api?apikey=apikey&t=search")
        r.raise_for_status()
        after = arrow.now()
        took = (after - before).seconds * 1000 + (after - before).microseconds / 1000
        print("Request completed successfully in %dms" % took)
    except Exception as e:
        print(e)

threads = []
for i in range(0, 10):
    t = threading.Thread(target=startTest)
    threads.append(t)
    t.start()


