from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import inspect
import os
import shutil

import peewee
from builtins import *
from playhouse.sqlite_ext import SqliteExtDatabase
from playhouse.sqliteq import SqliteQueueDatabase
from retry import retry

from nzbhydra import database, config
from nzbhydra.database import Indexer, IndexerApiAccess, IndexerSearch, IndexerStatus, Search, IndexerNzbDownload, TvIdCache, MovieIdCache, SearchResult


def set_and_drop(dbfile="tests2.db", tables=None):
    # if tables is None:
    #     tables = [Indexer, IndexerNzbDownload, Search, IndexerSearch, IndexerApiAccess, IndexerStatus, TvIdCache, MovieIdCache, SearchResult]
    # deleteDbFile(dbfile)
    # database.db = SqliteExtDatabase(dbfile)
    # database.db.connect()
    # #database.db.start()
    #
    # models = [
    #     obj for name, obj in inspect.getmembers(
    #         tables, lambda obj: type(obj) == type and issubclass(obj, peewee.Model)
    #     )
    #     ]
    # peewee.create_model_tables(models)
    # x = database.Indexer.select().count()
    if os.path.exists("testsettings.cfg"):
        os.remove("testsettings.cfg")
    shutil.copy("testsettings.cfg.orig", "testsettings.cfg")
    config.load("testsettings.cfg")
    # sleep(1)
    pass


@retry(WindowsError, delay=1, tries=5)
def deleteDbFile(dbfile):
    if os.path.exists(dbfile):
        os.remove(dbfile)
