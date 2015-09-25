import json
from peewee import OperationalError
import database
from database import Provider

tables = [Provider]

for t in tables:
    try:
        database.db.drop_table(t)
    except OperationalError as e:
        pass
    
for t in tables:
    try:
        database.db.create_table(t)
    except OperationalError as e:
        pass


Provider(module="newznab", name="dognzb", query_url="http://127.0.0.1:5001/dognzb", base_url="http://127.0.0.1:5001/dognzb", search_types=json.dumps(["general", "tv", "movie"])).save()
Provider(module="nzbclub", name="nzbclub", query_url="http://127.0.0.1:5001/nzbclub", base_url="http://127.0.0.1:5001/nzbclub", search_types=json.dumps(["general", "tv", "movie"])).save()


