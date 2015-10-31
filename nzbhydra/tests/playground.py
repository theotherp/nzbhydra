from nzbhydra import database
from nzbhydra.database import Indexer, IndexerSearch, IndexerApiAccess, IndexerStatus, Search, IndexerNzbDownload
from nzbhydra.tests.db_prepare import set_and_drop

set_and_drop("nzbhydra.db", [Indexer, IndexerNzbDownload, IndexerApiAccess, IndexerStatus, IndexerSearch, Search])

database.db.init("nzbhydra.db")
database.db.connect()

nzbsorg = Indexer(name="nzbs.org")
nzbsorg.save()

dognzb = Indexer(name="dognzb")
dognzb.save()

nzbindex = Indexer(name="nzbindex")
nzbindex.save()

nzbclub = Indexer(name="nzbclub")
nzbclub.save()

binsearch = Indexer(name="binsearch")
binsearch.save()

womble = Indexer(name="newshost")
womble.save()
