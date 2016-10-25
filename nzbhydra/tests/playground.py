from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import threading
from time import sleep

import arrow
import requests

allSuccessful = True
successes = 0
failures = 0


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
        global allSuccessful
        allSuccessful = False


runs = 30
concurrent_searches = 3
for x in range(1, runs+1):
    threads = []
    allSuccessful = True

    print("Starting test run #%d/%d" % (x, runs))
    for i in range(1, concurrent_searches+1):
        beforerun = arrow.now()
        t = threading.Thread(target=startTest, args=(str(i),))
        sleep(1)
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    afterrun = arrow.now()
    took = (afterrun - beforerun).seconds * 1000 + (afterrun - beforerun).microseconds / 1000
    if allSuccessful:
        successes += 1
        print("Run successful. Took %dms" % took)
    else:
        failures += 1
        print("Run failed. Took %dms" % took)

print("Runs without failures: %d" % successes)
print("Runs with failures: %d" % failures)
