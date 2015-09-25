import json
from peewee import *

db = SqliteDatabase(None)



class Provider(Model):
    name = CharField(unique=True)
    module = CharField()
    enabled = BooleanField(default=True)
    settings = TextField(default=json.dumps({}))
    generate_queries = BooleanField(default=False)
    query_url = CharField()
    base_url = CharField()
    search_types = CharField(default=json.dumps([]))
    search_ids = CharField(default=json.dumps([]))

    class Meta:
        database = db


class Settings(Model):
    class Meta:
        database = db



class ProviderSearch(Model):
    provider = ForeignKeyField(Provider)
    time = DateTimeField()
    response_time = IntegerField()
    response_successful = BooleanField()
    results = IntegerField()  # number of results returned

    class Meta:
        database = db  # This model uses the "people.db" database.

