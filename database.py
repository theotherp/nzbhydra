from peewee import *

db = SqliteDatabase('nzbhydra.db')


class SearchId(Model):
    id = CharField()


class SearchType(Model):
    id = CharField()


class Provider(Model):
    name = CharField(unique=True)
    module = CharField()
    settings = TextField()
    generate_queries = BooleanField()
    supports_queries = BooleanField()

    class Meta:
        database = db  # This model uses the "people.db" database.




class ProviderSearchTypes(Model):
    type = ForeignKeyField(SearchType)
    provider = ForeignKeyField(Provider)


class ProviderSearchIds(Model):
    id = ForeignKeyField(SearchId)
    provider = ForeignKeyField(Provider)


class ProviderSearch(Model):
    provider = ForeignKeyField(Provider)
    time = DateTimeField()
    response_time = IntegerField()
    response_successful = BooleanField()
    results = IntegerField()  # number of results returned

    class Meta:
        database = db  # This model uses the "people.db" database.


# TODO Remove later and use decorators on flask requests, this is just for developing
db.connect()
# #db.create_tables([Provider, ProviderSearch])
# nzbsorg = Provider(name="NZBs.org")
# nzbsorg.save()
# 
# dognzb = Provider(name="DOGNzb")
# dognzb.save()
# 
# nzbclub = Provider(name="NZBClub")
# nzbclub.save()
