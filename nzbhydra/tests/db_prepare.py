from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import

import os
import shutil

from future import standard_library
#standard_library.install_aliases()
from builtins import *
from peewee import OperationalError
from nzbhydra.database import Indexer, IndexerApiAccess, IndexerSearch, IndexerStatus, Search, IndexerNzbDownload, TvIdCache, MovieIdCache, SearchResult
from nzbhydra import database, config


def set_and_drop(dbfile="tests.db", tables=None):
    if tables is None:
        tables = [Indexer, IndexerNzbDownload, Search, IndexerSearch, IndexerApiAccess, IndexerStatus, TvIdCache, MovieIdCache, SearchResult]
    database.db.init(dbfile)
    database.db.connect()

    for t in tables:
        try:
            database.db.drop_table(t)
        except OperationalError as e:
            print(e)
            pass

    for t in tables:
        try:
            database.db.create_table(t)
        except OperationalError as e:
            print(e)
            pass

    database.db.close()

    if os.path.exists("testsettings.cfg"):
        os.remove("testsettings.cfg")
    shutil.copy("testsettings.cfg.orig", "testsettings.cfg")
    config.load("testsettings.cfg")
    pass
