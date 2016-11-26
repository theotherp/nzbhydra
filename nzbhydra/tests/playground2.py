from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import random
import threading
from time import sleep

import datetime

import arrow

from nzbhydra import database
database.init_db("nzbhydra.db")
database.db.start()
with database.db.atomic():
    for x in range(0, 500):
        apiaccess = database.IndexerApiAccess.create(indexer_id=random.randint(1,36), time=datetime.datetime.fromtimestamp(random.randint(1312677738, arrow.utcnow().timestamp)), response_successful=True, type="nzb", url="hallo", response_time=random.randint(50, 10000))
        download = database.IndexerNzbDownload.create(searchResult_id = 472, apiAccess_id=apiaccess.id, time=datetime.datetime.fromtimestamp(random.randint(1477501069, arrow.utcnow().timestamp)), title="Hallo", mode="redirect", internal=True)
        search = database.Search.create(internal=True, time=datetime.datetime.fromtimestamp(random.randint(1477501069, arrow.utcnow().timestamp)))

database.db.stop()