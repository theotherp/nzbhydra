from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import random
import string

import arrow
import time
from peewee import OperationalError
from playhouse.migrate import SqliteMigrator, migrate

from nzbhydra import database
from nzbhydra.database import SearchResult, TvIdCache


def bla(preset, count):
    indexer, created = database.Indexer.get_or_create(name="indexer%s" % preset)
    print(created)
    for i in range(1, count):
        try:

            iaa = database.IndexerApiAccess(indexer=indexer, type="", url="", time=arrow.utcnow().datetime)
            # database.SearchResult.create(indexer=indexer, title="%s title %d" % (preset, i), guid="%s guid" % preset, link="%s link" % preset)
            print("Created %s %d" % (preset, i))
            try:
                indexer_status = indexer.status.get()
            except database.IndexerStatus.DoesNotExist:
                print("Creating new IndexerStatus")
                indexer_status = database.IndexerStatus(indexer=indexer)
            indexer_status.save()
            iaa.save()
        except Exception as e:
            print(str(e))


def rndstr(n):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(n))


database.db.init("c:\\temp\\playground.db")
database.db.connect()
database.Indexer.drop_table()
database.Indexer.create_table()
SearchResult.drop_table()
SearchResult.create_table()
TvIdCache.drop_table()
TvIdCache.create_table()


indexer1, created = database.Indexer.get_or_create(name="indexer1")
indexer2, created = database.Indexer.get_or_create(name="indexer2")
indexer3, created = database.Indexer.get_or_create(name="indexer3")
indexer4, created = database.Indexer.get_or_create(name="indexer4")
indexer5, created = database.Indexer.get_or_create(name="indexer5")
indexers = [indexer1, indexer2, indexer3, indexer4, indexer5]


now = time.time()
with database.db.atomic():
    # Prefil with 10000
    for x in range(1, 6):
        SearchResult.create(indexer=indexers[x - 1], title="hallo", guid="hallo", link="hallo")
        for i in range(0, 2000):
            pass
            SearchResult.create(indexer=indexers[x - 1], title="%s%d" % (rndstr(80), i), guid="%s%d" % (rndstr(100), i), link="%s%d" % (rndstr(120), i))
            # SearchResult.create(indexer=indexers[x - 1], title="%s" % i, guid="%s" % i, link="%s" % i)

after = time.time()
print(after - now)

now = time.time()
rows = []
with database.db.atomic():
    for x in range(1, 6):
        _, created = SearchResult.get_or_create(indexer=indexers[x - 1], title="hallo", guid="hallo", link="hallo")
        print(created)
        print(SearchResult.select().where(SearchResult.title == "hallo").count())
        for i in range(0, 100):
            pass

            #SearchResult.create_or_get(indexer=indexers[x - 1], title="%s%d" % (rndstr(80), i), guid="%s%d" % (rndstr(100), i), link="%s%d" % (rndstr(120), i))
            # SearchResult.get_or_create(indexer=indexers[x - 1], title="%s%d" % (rndstr(80), i), guid="%s%d" % (rndstr(100), i), link="%s%d" % (rndstr(120), i))
            _, created = SearchResult.get_or_create(indexer=indexers[x - 1], title="%s" % i, guid="%s" % i, link="%s" % i)




after = time.time()
print(after - now)
#

database.db.close()
