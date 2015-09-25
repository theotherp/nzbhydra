import json
import database
from database import Provider, ProviderSearch, ProviderApiAccess, ProviderSearchApiAccess
from tests.db_prepare import set_and_drop

set_and_drop("nzbhydra.db", [Provider, ProviderSearch, ProviderApiAccess, ProviderSearchApiAccess])

database.db.init("nzbhydra.db")
database.db.connect()


nzbsorg = Provider(module="newznab", name="NZBs.org", query_url="http://127.0.0.1:5001/nzbsorg", base_url="http://127.0.0.1:5001/nzbsorg", settings=json.dumps({"apikey": "apikeynzbsorg"}), search_types=json.dumps(["tv", "general", "movie"]), search_ids=json.dumps(["imdbid", "tvdbid", "rid"]))
nzbsorg.save()
dognzb = Provider(module="newznab", name="DOGNzb", query_url="http://127.0.0.1:5001/dognzb", base_url="http://127.0.0.1:5001/dognzb", settings=json.dumps({"apikey": "apikeydognzb"}), search_types=json.dumps(["tv", "general"]), search_ids=json.dumps(["tvdbid", "rid"]))
dognzb.save()
