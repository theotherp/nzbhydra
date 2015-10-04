from nzbhydra import database
from nzbhydra.database import Provider, ProviderSearch, ProviderApiAccess, ProviderStatus, Search, ProviderNzbDownload
from nzbhydra.tests.db_prepare import set_and_drop

set_and_drop("nzbhydra.db", [ProviderNzbDownload, ProviderApiAccess])

database.db.init("nzbhydra.db")
database.db.connect()

# nzbsorg = Provider(module="newznab", name="NZBs.org", settings={"apikey": "apikeynzbsorg", "query_url": "http://127.0.0.1:5001/nzbsorg", "base_url": "http://127.0.0.1:5001/nzbsorg", "search_ids": ["imdbid", "tvdbid", "rid"]})
# nzbsorg.save()
# 
# dognzb = Provider(module="newznab", name="DOGNzb", settings={"apikey": "apikeydognzb", "query_url": "http://127.0.0.1:5001/dognzb", "base_url": "http://127.0.0.1:5001/dognzb", "search_ids": ["tvdbid", "rid"]})
# dognzb.save()
# 
# nzbindex = Provider(module="nzbindex", name="NZBIndex", settings={"query_url": "http://127.0.0.1:5001/nzbindex", "base_url": "http://127.0.0.1:5001/nzbindex", })
# nzbindex.save()
# 
# nzbclub = Provider(module="nzbclub", name="NZBClub", settings={"query_url": "http://127.0.0.1:5001/nzbclub", "base_url": "http://127.0.0.1:5001/nzbclub", "search_ids": []})
# nzbclub.save()

# binsearch = Provider(module="binsearch", name="Binsearch", settings={"query_url": "http://127.0.0.1:5001/binsearch", "base_url": "http://127.0.0.1:5001/binsearch", "search_ids": []})
# binsearch.save()
# 
# womble = Provider(module="womble", name="Womble", settings={"query_url": "http://127.0.0.1:5001/womble", "base_url": "http://127.0.0.1:5001/womble", "search_ids": []})
# womble.save()
