from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime
import hashlib
import json
import logging

import arrow
from builtins import *
from builtins import object
from dateutil.tz import tzutc
from playhouse.migrate import *
from playhouse.sqliteq import SqliteQueueDatabase

logger = logging.getLogger('root')

db = SqliteQueueDatabase(None, autostart=False, results_timeout=20.0)

DATABASE_VERSION = 18


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
        return arrow.get(value, tzinfo=tzutc()) if value is not None else None


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
    title = TextField(null=True)
    author = TextField(null=True)

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
    uniqueResults = IntegerField(null=True)  # number of results, we save this because SearchResult db rows are deleted after some time
    processedResults = IntegerField(null=True)  # number of results, we save this because SearchResult db rows are deleted after some time

    class Meta(object):
        database = db

    def save(self, *args, **kwargs):
        if self.time is None:
            self.time = datetime.datetime.utcnow()  # Otherwise the time of the first run of this code is taken
        super(IndexerSearch, self).save(*args, **kwargs)


class SearchResult(Model):
    id = CharField(primary_key=True)
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
    title = CharField()  # Redundant when the search result still exists but after it's deleted we still wanna see what the title is
    mode = CharField()  # "serve" or "redirect"
    internal = BooleanField(null=True)

    class Meta(object):
        database = db

    def save(self, *args, **kwargs):
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
    indexer = ForeignKeyField(Indexer, related_name="status", unique=True)
    first_failure = DateTimeUTCField(null=True)
    latest_failure = DateTimeUTCField(null=True)
    disabled_until = DateTimeUTCField(null=True)
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
    db.start()
    db.init(dbfile)

    logger.info("Initializing database and creating tables")
    for t in tables:
        try:
            t.create_table()
        except OperationalError:
            logger.exception("Error while creating table %s" % t)

    logger.info("Created new version info entry with database version %d" % DATABASE_VERSION)
    VersionInfo(version=DATABASE_VERSION).create()


def truncate_db():
    logger.warn("Truncating database")
    IndexerNzbDownload.delete().execute()
    SearchResult.delete().execute()
    TvIdCache.delete().execute()
    MovieIdCache.delete().execute()
    IndexerStatus.delete().execute()
    IndexerApiAccess.delete().execute()
    IndexerSearch.delete().execute()
    Search.delete().execute()
    Indexer.delete().execute()


def update_db(dbfile):
    # CAUTION: Don't forget to increase the default value for VersionInfo
    logger.debug("Initing")
    db.start()
    db.init(dbfile)

    vi = VersionInfo.get()
    if vi.version < DATABASE_VERSION:
        logger.info("Migrating database")
        # Backup will be done by update code

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

            # TODO: Store all stuff before migrating and after fill it back in

            # Delete all instances of IndexerNzbDownload because we'll allow the reference to SearchResult to be empty but need to make it non-nullable afterwards
            # IndexerNzbDownload.delete().execute()
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

        # Well this is embarrassing
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
            cursor = db.execute_sql("SELECT t.id, t.season, t.episode FROM search t WHERE t.episode IS NOT NULL OR t.season IS NOT NULL")
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

        if vi.version == 10:
            logger.info("Upgrading database to version 11")
            migrator = SqliteMigrator(db)
            logger.info("Adding column type to store indexers' unique results and processed results counts and NZB download source")
            with db.transaction():
                migrate(
                    migrator.add_column("indexersearch", "uniqueresults", IndexerSearch.uniqueResults),
                    migrator.add_column("indexersearch", "processedresults", IndexerSearch.processedResults),
                    migrator.add_column("indexernzbdownload", "internal", IndexerNzbDownload.internal)
                )
            vi.version = 11
            vi.save()
            logger.info("Database migration completed successfully")

        if vi.version == 11:
            logger.info("Upgrading database to version 12")
            migrator = SqliteMigrator(db)
            logger.info("Adding columns to store author and title in search history")
            with db.transaction():
                migrate(
                    migrator.add_column("search", "author", Search.author),
                    migrator.add_column("search", "title", Search.title),
                )
            vi.version = 12
            vi.save()
            logger.info("Database migration completed successfully")

        if vi.version == 12:
            logger.info("Upgrading database to version 13")
            omgorg = None
            omg = None
            with db.transaction():
                try:
                    omgorg = Indexer.get(Indexer.name == "omgwtfnzbs.org")
                except Indexer.DoesNotExist:
                    logger.info("No database entry found for omgwtfnzbs.org")
                    pass
                try:
                    omg = Indexer.get(Indexer.name == "omgwtfnzbs")
                except Indexer.DoesNotExist:
                    logger.info("No entry for omgwtfnzbs found in database")
                except Exception as e:
                    print(e)
                if omgorg and not omg:
                    logger.info("Renaming omgwtfnzbs.org to omgwtfnzbs in database")
                    omgorg.name = "omgwtfnzbs"
                    omgorg.save()
                elif omgorg and omg:
                    db.execute_sql("UPDATE indexerapiaccess SET indexer_id = %d WHERE indexer_id = %d" % (omg.id, omgorg.id))
                    db.execute_sql("UPDATE indexersearch SET indexer_id = %d WHERE indexer_id = %d" % (omg.id, omgorg.id))
                    db.execute_sql("UPDATE searchresult SET indexer_id = %d WHERE indexer_id = %d" % (omg.id, omgorg.id))
                    omgorg.delete_instance()
                    logger.info("Changed references from omgwtfnzbs.org to omgwtfnzbs in database and deleted old indexer entry")

            vi.version = 13
            vi.save()
            logger.info("Database migration completed successfully")

        if vi.version == 13:
            logger.info("Upgrading database to version 14. Migrating to hash based search result IDs")

            class SearchResultOld(Model):
                indexer_id = IntegerField()
                firstFound = DateTimeField()
                title = CharField()
                guid = CharField()
                link = CharField()
                details = CharField(null=True)

                class Meta(object):
                    database = db
                    db_table = "searchresult"

            class SearchResultMigration(Model):
                id = CharField(primary_key=True)
                indexer_id = IntegerField()
                firstFound = DateTimeField()
                title = CharField()
                guid = CharField()
                link = CharField()
                details = CharField(null=True)

                class Meta(object):
                    database = db
                    db_table = "searchresult2"

            class IndexerNzbDownloadOld(Model):
                searchResult = ForeignKeyField(SearchResultOld, related_name="downloads")
                apiAccess = ForeignKeyField(IndexerApiAccess)
                time = DateTimeField()
                title = CharField()  # Redundant when the search result still exists but after it's deleted we still wanna see what the title is
                mode = CharField()  # "serve" or "redirect"
                internal = BooleanField(null=True)

                class Meta(object):
                    database = db
                    db_table = "indexernzbdownload"

            class IndexerNzbDownloadMigration(Model):
                searchResult = ForeignKeyField(SearchResultMigration, related_name="downloads")
                apiAccess = ForeignKeyField(IndexerApiAccess)
                time = DateTimeField()
                title = CharField()  # Redundant when the search result still exists but after it's deleted we still wanna see what the title is
                mode = CharField()  # "serve" or "redirect"
                internal = BooleanField(null=True)

                class Meta(object):
                    database = db
                    db_table = "indexernzbdownload2"

            with db.transaction():
                db.execute_sql("""
                CREATE TABLE searchresult2
                (
                  id         VARCHAR PRIMARY KEY NOT NULL,
                  indexer_id INTEGER             NOT NULL,
                  firstFound TEXT                NOT NULL,
                  title      TEXT                NOT NULL,
                  guid       TEXT                NOT NULL,
                  link       TEXT                NOT NULL,
                  details    TEXT,
                  FOREIGN KEY (indexer_id) REFERENCES indexer (id)
                    DEFERRABLE INITIALLY DEFERRED
                );
                """)

                db.execute_sql("""
                CREATE TABLE indexernzbdownload2
                (
                  id              INTEGER PRIMARY KEY NOT NULL,
                  searchResult_id VARCHAR             NOT NULL,
                  apiAccess_id    INTEGER             NOT NULL,
                  time            TEXT                NOT NULL,
                  title           TEXT                NOT NULL,
                  mode            TEXT                NOT NULL,
                  internal        INTEGER,
                  FOREIGN KEY (searchResult_id) REFERENCES searchresult (id)
                    DEFERRABLE INITIALLY DEFERRED,
                  FOREIGN KEY (apiAccess_id) REFERENCES indexerapiaccess (id)
                    DEFERRABLE INITIALLY DEFERRED);
                """)

                with db.atomic():
                    countSearchResults = SearchResultOld.select().count()
                    logger.info("Migrating %d search results" % countSearchResults)
                    for count, sr in enumerate(SearchResultOld.select()):
                        searchResultId = hashlib.sha1(str(sr.indexer_id) + sr.guid).hexdigest()
                        # Slow but was unable to do this with insert_from or insert_many
                        srMigrated = SearchResultMigration.create(**{"id": searchResultId, "indexer_id": sr.indexer_id, "firstFound": sr.firstFound, "title": sr.title, "guid": sr.guid, "link": sr.link, "details": sr.details})

                        for dl in IndexerNzbDownloadOld.select().where(IndexerNzbDownloadOld.searchResult == sr):  # Find all linked downloads
                            IndexerNzbDownloadMigration.create(searchResult=srMigrated, apiAccess=dl.apiAccess, time=dl.time, title=dl.title, mode=dl.mode, internal=dl.internal)
                        if count > 0 and count % 250 == 0:
                            logger.info("Migrated %d of %d search results" % (count, countSearchResults))
                    logger.info("Successfully migrated %d search results" % countSearchResults)

                db.execute_sql("DROP TABLE indexernzbdownload")
                db.execute_sql("ALTER TABLE indexernzbdownload2 RENAME TO indexernzbdownload")
                db.execute_sql("DROP TABLE searchresult")
                db.execute_sql("ALTER TABLE searchresult2 RENAME TO searchresult")

            vi.version = 14
            vi.save()
            logger.info("Database migration completed successfully")

        if vi.version == 14 or vi.version == 15:
            logger.info("Upgrading database to version 15/16")
            logger.info("Deleting duplicate indexer statuses and adding unique constraint")

            for indexer in Indexer.select():
                statuses = list(IndexerStatus.select().where(IndexerStatus.indexer == indexer).order_by(IndexerStatus.latest_failure.desc()))
                if len(statuses) == 0:
                    logger.info("Adding indexer status entry for indexer %s" % indexer.name)
                    IndexerStatus.create_or_get(indexer=indexer, first_failure=None, latest_failure=None, disabled_until=None)

                elif len(statuses) > 1:
                    logger.info("Deleting duplicate indexer status entries for %s" % indexer.name)
                    for status in statuses[1:]:
                        status.delete_instance()
            db.execute_sql("CREATE UNIQUE INDEX indexerstatus_indexer_id_uindex ON indexerstatus(indexer_id);")

            vi.version = 16
            vi.save()
            logger.info("Database migration completed successfully")

        if vi.version == 16 or vi.version == 17:
            try:
                migrator = SqliteMigrator(db)
                with db.transaction():
                    migrate(
                        migrator.drop_column('indexernzbdownload', 'time')
                    )
                    logger.info("Dropped time column for NZB downloads")
            except: #May not exist because I fucked up
                pass
            vi.version = 18
            vi.save()
            logger.info("Database migration completed successfully")
