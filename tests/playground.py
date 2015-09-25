import json
import database
from database import Provider, ProviderSearch, ProviderApiAccess, ProviderSearchApiAccess
from searchmodules.newznab import NewzNab
from tests.db_prepare import set_and_drop 

set_and_drop("nzbhydra.db", [Provider, ProviderSearch, ProviderApiAccess, ProviderSearchApiAccess])

database.db.init("nzbhydra.db")
database.db.connect()


nzbsorg = Provider(module="newznab", name="NZBs.org", query_url="http://127.0.0.1:5001/nzbsorg", base_url="http://127.0.0.1:5001/nzbsorg", settings={"apikey": "apikeynzbsorg"}, search_types=["tv", "general", "movie"], search_ids=["imdbid", "tvdbid", "rid"])
nzbsorg.save()
dognzb = Provider(module="newznab", name="DOGNzb", query_url="http://127.0.0.1:5001/dognzb", base_url="http://127.0.0.1:5001/dognzb", settings={"apikey": "apikeydognzb"}, search_types=["tv", "general"], search_ids=["tvdbid", "rid"])
dognzb.save()


test = Provider(module="newznab", name="t", query_url="http://127.0.0.1:5001/dognzb", base_url="http://127.0.0.1:5001/dognzb", settings={"apikey": "apikeydognzb"}, search_types=["tv", "general"], search_ids=["tvdbid", "rid"], settings2=["halo"])
test.save()

n = NewzNab(test.get())
print(n.settings["apikey"])
print(n.apikey)
print(n.search_types)
