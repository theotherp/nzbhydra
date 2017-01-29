from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime
import random

import arrow

from nzbhydra import database

database.init_db("nzbhydra.db")
database.db.start()
onlySearches = False
for z in range(0, 100):
    with database.db.atomic():
        print(z)
        for x in range(0, 1000):
            search = database.Search.create(internal=random.randint(0, 1) == 0, time=datetime.datetime.fromtimestamp(random.randint(1477501069, arrow.utcnow().timestamp)))
            if not onlySearches:
                for y in range(0, random.randint(1, 26)):
                    indexer_id = y
                    # Create API access for search
                    apiaccess = database.IndexerApiAccess.create(indexer_id=indexer_id, time=datetime.datetime.fromtimestamp(random.randint(1312677738, arrow.utcnow().timestamp)), response_successful=True, type="nzb", url="hallo", response_time=random.randint(50, 10000))

                    # Create search
                    resultsCount = random.randint(0, 500)
                    uniqueResults = random.randint(0, resultsCount)
                    processedResults = random.randint(max(int((resultsCount + 1) / 2), 1), max(resultsCount, 1))
                    indexersearch = database.IndexerSearch.create(indexer_id=indexer_id, time=datetime.datetime.fromtimestamp(random.randint(1312677738, arrow.utcnow().timestamp)), search=search, successful=True, resultsCount=resultsCount, uniqueResults=uniqueResults,
                                                                  processedResults=processedResults)

                    if random.randint(0, 50) == 3:
                        # Create download
                        apiaccess = database.IndexerApiAccess.create(indexer_id=indexer_id, time=datetime.datetime.fromtimestamp(random.randint(1312677738, arrow.utcnow().timestamp)), response_successful=True, type="download", url="hallo", response_time=random.randint(50, 10000))
                        download = database.IndexerNzbDownload.create(searchResult_id=472, apiAccess_id=apiaccess.id, time=datetime.datetime.fromtimestamp(random.randint(1477501069, arrow.utcnow().timestamp)), title="Hallo", mode="redirect", internal=True)



# searchFor = []
# with database.db.atomic():
#     database.SearchResult.delete().execute()
#     before = arrow.now()
#     for x in range(0, 0000):
#         id = hash(''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(64)))
#         result = database.SearchResult().create(indexer_id=5, guid=id, title=id, link="link", details="details_link", firstFound=datetime.datetime.utcnow(), id=id)
#         if x % 20 == 0:
#             searchFor.append(result.id)
#
# after = arrow.now()
# took = (after - before).seconds * 1000 + (after - before).microseconds / 1000
#
# print("Writing took %d ms" % took)
# print(database.SearchResult.select().count())
#
# before = arrow.now()
# for x in searchFor:
#     database.SearchResult.get(database.SearchResult.id == x)
# after = arrow.now()
# took = (after - before).seconds * 1000 + (after - before).microseconds / 1000
# print(len(searchFor))
# print("Searching took %d ms" % took)
#
# database.db.stop()
