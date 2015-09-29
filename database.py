import json
import datetime
import arrow
from dateutil.tz import tzutc

from peewee import *

db = SqliteDatabase(None)


class JSONField(TextField):
    db_field = "text"

    def db_value(self, value):
        return json.dumps(value)

    def python_value(self, value):
        return json.loads(value)


class DateTimeUTCField(DateTimeField):
    db_field = "datetime"
    
    def db_value(self, value):
        return arrow.get(value).datetime if value is not None else None

    def python_value(self, value):
        return arrow.get(value, tzinfo=tzutc())


class Provider(Model):
    name = CharField(unique=True)
    module = CharField()
    enabled = BooleanField(default=True)
    settings = JSONField(default={})

    class Meta:
        database = db


class ProviderSearch(Model):
    provider = ForeignKeyField(Provider)
    time = DateTimeField(default=datetime.datetime.utcnow())

    query = CharField(null=True)
    query_generated = BooleanField(default=False)
    identifier_key = CharField(null=True)
    identifier_value = CharField(null=True)
    categories = JSONField(default=[])
    season = IntegerField(null=True)
    episode = IntegerField(null=True)

    successful = BooleanField(default=False)
    results = IntegerField(null=True)  # number of results returned

    class Meta:
        database = db  # This model uses the "people.db" database.


class ProviderApiAccess(Model):
    provider = ForeignKeyField(Provider)
    time = DateTimeUTCField(default=datetime.datetime.utcnow())
    type = CharField()  # search, download, comments, nfo?
    response_successful = BooleanField(default=False)
    response_time = IntegerField(null=True)
    error = CharField(null=True)

    class Meta:
        database = db


class ProviderSearchApiAccess(Model):
    search = ForeignKeyField(ProviderSearch, related_name="api_accesses")
    api_access = ForeignKeyField(ProviderApiAccess, related_name="api_accesses") 

    class Meta:
        database = db
        
        
class ProviderStatus(Model):
    provider = ForeignKeyField(Provider, related_name="status")
    first_failure = DateTimeUTCField(default=datetime.datetime.utcnow(), null=True)
    latest_failure = DateTimeUTCField(default=datetime.datetime.utcnow(), null=True)
    disabled_until = DateTimeUTCField(default=datetime.datetime.utcnow(), null=True)
    level = IntegerField(default=0)
    reason = CharField(null=True)
    disabled_permanently = BooleanField(default=False) #Set to true if an error occurred that probably won't fix itself (e.g. when the apikey is wrong) 
    
    def __repr__(self):
        return "%s in status %d. First failure: %s. Latest Failure: %s. Reason: %s. Disabled until: %s" % (self.provider, self.level, self.first_failure, self.latest_failure, self.reason, self.disabled_until)
    
    class Meta:
        database = db