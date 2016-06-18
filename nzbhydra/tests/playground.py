from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import arrow
import concurrent.futures

from nzbhydra import database

def bla(preset, count):
    
    indexer, created = database.Indexer.get_or_create(name="indexer%s" % preset)
    print(created)
    for i in range(1, count):
        try:
            
            iaa = database.IndexerApiAccess(indexer=indexer, type="", url="", time=arrow.utcnow().datetime)
            #database.SearchResult.create(indexer=indexer, title="%s title %d" % (preset, i), guid="%s guid" % preset, link="%s link" % preset)
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


database.db.init("playground.py")
database.db.connect()
#database.db.create_table(database.Indexer)
#database.db.create_table(database.SearchResult)
# database.db.create_table(database.IndexerStatus)
# database.db.create_table(database.IndexerApiAccess)
#database.Indexer.delete().execute()
#database.SearchResult.delete().execute()
#database.IndexerStatus.delete().execute()
#database.IndexerApiAccess.delete().execute()

with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    executor.submit(bla, "a", 10)
    executor.submit(bla, "b", 10)
    executor.submit(bla, "c", 10)
    executor.submit(bla, "d", 10)
    executor.submit(bla, "e", 10)