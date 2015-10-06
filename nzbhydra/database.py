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
    name = CharField(unique=True) #The name of the provider. So if the user changes the name all references get lost (except we handle that if he does it in the GUI).

    class Meta:
        database = db


class Search(Model):
    internal = BooleanField()  # true if from our gui, false if via newznab api
    query = CharField(null=True)
    time = DateTimeField()
    identifier_key = CharField(null=True)
    identifier_value = CharField(null=True)
    category = JSONField(null=True)
    season = IntegerField(null=True)
    episode = IntegerField(null=True)

    class Meta:
        database = db

    def save(self, *args, **kwargs):
        if self.time is None:
            self.time = datetime.datetime.utcnow()  # Otherwise the time of the first run of this code is taken
        super(Search, self).save(*args, **kwargs)


class ProviderSearch(Model):
    provider = ForeignKeyField(Provider, related_name="searches")
    search = ForeignKeyField(Search, related_name="provider_searches", null=True)
    time = DateTimeField()

    successful = BooleanField(default=False)
    results = IntegerField(null=True)  # number of results returned

    class Meta:
        database = db  # This model uses the "people.db" database.

    def save(self, *args, **kwargs):
        if self.time is None:
            self.time = datetime.datetime.utcnow()  # Otherwise the time of the first run of this code is taken
        super(ProviderSearch, self).save(*args, **kwargs)


class ProviderApiAccess(Model):
    provider = ForeignKeyField(Provider)
    provider_search = ForeignKeyField(ProviderSearch, related_name="api_accesses", null=True)
    time = DateTimeUTCField()
    type = CharField()  # search, nzb, comments, nfo?
    url = CharField()
    response_successful = BooleanField(default=False, null=True)
    response_time = IntegerField(null=True)
    error = CharField(null=True)

    class Meta:
        database = db

    def save(self, *args, **kwargs):
        if self.time is None:  # Otherwise the time of the first run of this code is taken
            self.time = datetime.datetime.utcnow()
        super(ProviderApiAccess, self).save(*args, **kwargs)


class ProviderNzbDownload(Model):
    provider = ForeignKeyField(Provider, related_name="downloads")
    provider_search = ForeignKeyField(ProviderSearch, related_name="downloads", null=True)
    api_access = ForeignKeyField(ProviderApiAccess)
    time = DateTimeField()
    mode = CharField() #"serve" or "redirect"
    
    
    class Meta:
        database = db

    def save(self, *args, **kwargs):
        if self.time is None:
            self.time = datetime.datetime.utcnow()  # Otherwise the time at the first run of this code is taken
        super(ProviderNzbDownload, self).save(*args, **kwargs)

# class ProviderSearchApiAccess(Model):
#     search = ForeignKeyField(ProviderSearch, related_name="api_accesses")
#     api_access = ForeignKeyField(ProviderApiAccess, related_name="api_accesses")
# 
#     class Meta:
#         database = db


class ProviderStatus(Model):
    provider = ForeignKeyField(Provider, related_name="status")
    first_failure = DateTimeUTCField(default=datetime.datetime.utcnow(), null=True)
    latest_failure = DateTimeUTCField(default=datetime.datetime.utcnow(), null=True)
    disabled_until = DateTimeUTCField(default=datetime.datetime.utcnow(), null=True)
    level = IntegerField(default=0)
    reason = CharField(null=True)
    disabled_permanently = BooleanField(default=False)  # Set to true if an error occurred that probably won't fix itself (e.g. when the apikey is wrong) 

    def __repr__(self):
        return "%s in status %d. First failure: %s. Latest Failure: %s. Reason: %s. Disabled until: %s" % (self.provider, self.level, self.first_failure, self.latest_failure, self.reason, self.disabled_until)

    class Meta:
        database = db
