from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

# standard_library.install_aliases()
import shutil

from builtins import *
from builtins import object
import json
import datetime
import logging
import arrow
from dateutil.tz import tzutc
from playhouse.migrate import *
from playhouse.sqliteq import SqliteQueueDatabase

logger = logging.getLogger('root')

db = SqliteQueueDatabase(None, autostart=True, queue_max_size=1024, readers=4, results_timeout=10.0)

DATABASE_VERSION = 10


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


class Indexer(Model):
    name = CharField(unique=True)  # The name of the indexer. So if the user changes the name all references get lost (except we handle that if he does it in the GUI).

    class Meta(object):
        database = db


class Search(Model):
    internal = BooleanField()  # true if from our gui, false if via newznab api
    query = CharField(null=True)
    time = DateTimeField()
    identifier_key = CharField(null=True)
    identifier_value = CharField(null=True)
    category = TextField(null=True)
    season = TextField(null=True)
    episode = TextField(null=True)
    type = CharField(default="general")
    username = CharField(null=True)

    class Meta(object):
        database = db

    def save(self, *args, **kwargs):
        if self.time is None:
            self.time = datetime.datetime.utcnow()  # Otherwise the time of the first run of this code is taken
        super(Search, self).save(*args, **kwargs)


class IndexerSearch(Model):
    indexer = ForeignKeyField(Indexer, related_name="searches")
    search = ForeignKeyField(Search, related_name="indexer_searches", null=True)
    time = DateTimeField()

    successful = BooleanField(default=False)
    resultsCount = IntegerField(null=True)  # number of results, we save this because SearchResult db rows are deleted after some time

    class Meta(object):
        database = db

    def save(self, *args, **kwargs):
        if self.time is None:
            self.time = datetime.datetime.utcnow()  # Otherwise the time of the first run of this code is taken
        super(IndexerSearch, self).save(*args, **kwargs)


class SearchResult(Model):
    indexer = ForeignKeyField(Indexer, related_name="results")
    firstFound = DateTimeField()
    title = CharField()
    guid = CharField()
    link = CharField()
    details = CharField(null=True)

    class Meta(object):
        database = db
        indexes = (
            (('indexer', 'guid'), True),  # Note the trailing comma!
        )

    def save(self, *args, **kwargs):
        if self.firstFound is None:
            self.firstFound = datetime.datetime.utcnow()  # Otherwise the time of the first run of this code is taken
        super(SearchResult, self).save(*args, **kwargs)


class IndexerApiAccess(Model):
    indexer = ForeignKeyField(Indexer)
    indexer_search = ForeignKeyField(IndexerSearch, related_name="apiAccesses", null=True)
    time = DateTimeUTCField()
    type = CharField()  # search, nzb, comments, nfo?
    url = CharField()
    response_successful = BooleanField(default=False, null=True)
    response_time = IntegerField(null=True)
    error = CharField(null=True)
    username = CharField(null=True)

    class Meta(object):
        database = db

    def save(self, *args, **kwargs):
        if self.time is None:  # Otherwise the time of the first run of this code is taken
            self.time = datetime.datetime.utcnow()
        super(IndexerApiAccess, self).save(*args, **kwargs)


class IndexerNzbDownload(Model):
    searchResult = ForeignKeyField(SearchResult, related_name="downloads")
    apiAccess = ForeignKeyField(IndexerApiAccess)  
    time = DateTimeField()
    title = CharField() #Redundant when the search result still exists but after it's deleted we still wanna see what the title is
    mode = CharField()  # "serve" or "redirect"
    
    class Meta(object):
        database = db

    def save(self, *args, **kwargs):
        if self.time is None:
            self.time = datetime.datetime.utcnow()  # Otherwise the time at the first run of this code is taken
        super(IndexerNzbDownload, self).save(*args, **kwargs)


class v5IndexerNzbDownload(Model):
    indexer = ForeignKeyField(Indexer, related_name="downloads")
    indexer_search = ForeignKeyField(IndexerSearch, related_name="downloads", null=True)
    api_access = ForeignKeyField(IndexerApiAccess)
    title = CharField()
    time = DateTimeField()
    mode = CharField()  # "serve" or "redirect"
    guid = CharField()

    class Meta(object):
        database = db
        db_table = "IndexerNzbDownload"

    def save(self, *args, **kwargs):
        if self.time is None:
            self.time = datetime.datetime.utcnow()  # Otherwise the time at the first run of this code is taken
        super(v5IndexerNzbDownload, self).save(*args, **kwargs)


class IndexerStatus(Model):
    indexer = ForeignKeyField(Indexer, related_name="status")
    first_failure = DateTimeUTCField(default=datetime.datetime.utcnow(), null=True)
    latest_failure = DateTimeUTCField(default=datetime.datetime.utcnow(), null=True)
    disabled_until = DateTimeUTCField(default=datetime.datetime.utcnow(), null=True)
    level = IntegerField(default=0)
    reason = CharField(null=True)
    disabled_permanently = BooleanField(default=False)  # Set to true if an error occurred that probably won't fix itself (e.g. when the apikey is wrong) 

    def __repr__(self):
        return "%s in status %d. First failure: %s. Latest Failure: %s. Reason: %s. Disabled until: %s" % (self.indexer, self.level, self.first_failure, self.latest_failure, self.reason, self.disabled_until)

    class Meta(object):
        database = db


class VersionInfo(Model):
    version = IntegerField(default=DATABASE_VERSION)

    class Meta(object):
        database = db


class TvIdCache(Model):
    tvdb = CharField(null=True)
    tvrage = CharField(null=True)
    tvmaze = CharField(null=True)
    title = CharField()

    class Meta(object):
        database = db
        indexes = (("tvdb", "tvrage", "tvmaze"), True),


class MovieIdCache(Model):
    imdb = CharField()
    tmdb = CharField()
    title = CharField()

    class Meta(object):
        database = db
        

class DummyTableDefinition(Model):
    idField = IntegerField(default=1, null=False)


def init_db(dbfile):
    tables = [Indexer, IndexerNzbDownload, Search, IndexerSearch, IndexerApiAccess, IndexerStatus, VersionInfo, TvIdCache, MovieIdCache, SearchResult]
    db.init(dbfile)

    logger.info("Initializing database and creating tables")
    for t in tables:
        try:
            t.create_table()
        except OperationalError:
            logger.exception("Error while creating table %s" % t)

    logger.info("Created new version info entry with database version 1")
    VersionInfo(version=DATABASE_VERSION).create()

    db.close()


def update_db(dbfile):
    # CAUTION: Don't forget to increase the default value for VersionInfo
    db.init(dbfile)

    vi = VersionInfo.get()
    if vi.version < DATABASE_VERSION:
        logger.info("Migrating database")
        #Backup will be done by update code
    
        if vi.version == 1:
            logger.info("Upgrading database to version 2")
            # Update from 1 to 2
            # Add tv id cache info 
            try:
                logger.info("Adding new table TvIdCache to database")
                db.create_table(TvIdCache)
            except OperationalError:
                logger.error("Error adding table TvIdCache to database")
                # TODO How should we handle this?
                pass
            vi.version = 2
            vi.save()
        if vi.version == 2:
            logger.info("Upgrading database to version 3")
            # Update from 2 to 3
            # Add tvmaze cache info column 
            try:
                logger.debug("Deleting all rows in TvIdCache")
                TvIdCache.delete().execute()
                migrator = SqliteMigrator(db)
                logger.info("Adding new column tvmaze to table TvIdCache, setting nullable columns and adding index")
                migrate(
                        migrator.add_column("tvidcache", "tvmaze", TvIdCache.tvmaze),
                        migrator.drop_not_null("tvidcache", "tvdb"),
                        migrator.drop_not_null("tvidcache", "tvrage"),
                        migrator.add_index("tvidcache", ("tvdb", "tvrage", "tvmaze"), True)
                )
                logger.info("Adding new table MovieIdCache")
                db.create_table(MovieIdCache)
            except OperationalError:
                logger.error("Error adding columb tvmaze to table TvIdCache")
                # TODO How should we handle this?
                pass
            vi.version = 3
            vi.save()
        if vi.version == 3:
            logger.info("Upgrading database to version 4")
            logger.info("Adding columns for usernames")
            migrator = SqliteMigrator(db)
            migrate(
                    migrator.add_column("indexerapiaccess", "username", IndexerApiAccess.username),
                    migrator.add_column("search", "username", Search.username)
                    )
            vi.version = 4
            vi.save()
        if vi.version == 4:
            logger.info("Upgrading database to version 5")
            logger.info("Dropping and recreating ID cache tables for movies and TV so they will be refilled with titles")
            
            db.drop_table(MovieIdCache)
            db.create_table(MovieIdCache)
            db.drop_table(TvIdCache)
            db.create_table(TvIdCache)
            
            vi.version = 5
            vi.save()

        if vi.version == 5:
            logger.info("Upgrading database to version 6 (this might take a couple of seconds)")
            logger.info("Migrating table columns")
            
            #TODO: Store all stuff before migrating and after fill it back in

            # Delete all instances of IndexerNzbDownload because we'll allow the reference to SearchResult to be empty but need to make it non-nullable afterwards
            #IndexerNzbDownload.delete().execute()
            indexerNzbDownloads = list(v5IndexerNzbDownload.select().dicts())

            logger.info("Converting search results to new schema")
            
            migrator = SqliteMigrator(db)
            migrate(
                
                migrator.rename_column('IndexerSearch', 'results', 'resultscount'),
                                
                migrator.drop_column('IndexerNzbDownload', 'indexer_id'),
                migrator.drop_column('IndexerNzbDownload', 'guid'),
                migrator.drop_column('IndexerNzbDownload', 'indexer_search_id'),

                migrator.rename_column('IndexerNzbDownload', 'api_access_id', 'apiaccess_id'),
                
                # Add foreign key to SearchResult
                migrator.add_column('IndexerNzbDownload', 'searchResult_id', DummyTableDefinition.idField),
            )
            
            logger.info("Creating table for search results")
            db.create_table(SearchResult)

            with db.transaction():
                logger.info("Converting download entries")
                for oldDownload in indexerNzbDownloads:
                    searchResult = SearchResult.create(indexer=oldDownload["indexer"], firstFound=oldDownload["time"], title=oldDownload["title"], guid="Not migrated", link="Not migrated", details="Not migrated")
                    newDownload = IndexerNzbDownload.get(IndexerNzbDownload.apiAccess == oldDownload["api_access"])
                    newDownload.searchResult = searchResult
                    newDownload.save()
            
                vi.version = 6
                vi.save()

        if vi.version == 6:
            logger.info("Upgrading database to version 7")
            migrator = SqliteMigrator(db)
            migrate(
                migrator.add_not_null("SearchResult", "details")
            )
            vi.version = 7
            vi.save()

        #Well this is embarrassing
        if vi.version == 7:
            logger.info("Upgrading database to version 8")
            migrator = SqliteMigrator(db)
            migrate(
                migrator.drop_not_null("SearchResult", "details")
            )
            vi.version = 8
            vi.save()

        if vi.version == 8:
            logger.info("Upgrading database to version 9")
            migrator = SqliteMigrator(db)
            cursor = db.execute_sql("select t.id, t.season, t.episode from search t where t.episode is not null or t.season is not null")
            rows = list(cursor.fetchall())
            logger.info("Changing column type of season and episode to text")
            with db.transaction():
                migrate(
                    migrator.drop_column('search', 'season'),
                    migrator.drop_column('search', 'episode'),
                    migrator.add_column('search', 'season', Search.season),
                    migrator.add_column('search', 'episode', Search.episode),
                )
                logger.info("Writing text value of season and episode for %d entries" % len(rows))
                for row in rows:
                    search = Search.get(id=row[0])
                    search.season = str(row[1])
                    search.episode = str(row[2])
                    search.save()
                
                vi.version = 9
                vi.save()

        if vi.version == 9:
            logger.info("Ensuring database indexes are set")
            migrator = SqliteMigrator(db)
            try:
                migrate(migrator.drop_index("searchresult", "searchresult_indexer_id_guid"))
            except OperationalError:
                logger.info("Index searchresult_indexer_id_guid doesn't exist so doesn't need to be dropped")

            logger.info("Removing duplicate results from search results")
            db.execute_sql("""
            DELETE FROM searchresult
            WHERE rowid NOT IN
                  (
                    SELECT min(rowid)
                    FROM searchresult
                    GROUP BY
                      indexer_id
                      , guid
                  )
            """)
            migrate(migrator.add_index("searchresult", ("indexer_id", "guid"), True))

            try:
                migrate(migrator.drop_index("tvidcache", "tvidcache_tvdb_tvrage_tvmaze"))
            except OperationalError:
                logger.info("Index tvidcache_tvdb_tvrage_tvmaze doesn't exist so doesn't need to be dropped")

            logger.info("Removing duplicate results from TV ID cache")
            db.execute_sql("""
            DELETE FROM tvidcache
            WHERE rowid NOT IN
                  (
                    SELECT min(rowid)
                    FROM tvidcache
                    GROUP BY
                      tvdb
                      , tvrage
                      , tvmaze
                  )
            """)
            migrate(migrator.add_index("tvidcache", ("tvdb", "tvrage", "tvmaze"), True))

            logger.info("Index migration completed successfully")
            vi.version = 10
            vi.save()


            
            
    db.close()
