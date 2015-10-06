from nzbhydra import database
from nzbhydra.database import Provider, ProviderSearch, ProviderApiAccess, ProviderStatus, Search, ProviderNzbDownload
from nzbhydra.tests.db_prepare import set_and_drop

set_and_drop("nzbhydra.db", [Provider, ProviderNzbDownload, ProviderApiAccess])

database.db.init("nzbhydra.db")
database.db.connect()

nzbsorg = Provider(name="nzbs.org")
nzbsorg.save()

dognzb = Provider(name="dognzb")
dognzb.save()

nzbindex = Provider(name="nzbindex")
nzbindex.save()

nzbclub = Provider(name="nzbclub")
nzbclub.save()

binsearch = Provider(name="binsearch")
binsearch.save()

womble = Provider(name="newshost")
womble.save()
