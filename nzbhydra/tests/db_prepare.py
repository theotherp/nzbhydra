from peewee import OperationalError
from nzbhydra.database import Provider, ProviderApiAccess, ProviderSearch, ProviderStatus, Search
from nzbhydra import database


def set_and_drop(dbfile="tests.db", tables=[Provider, ProviderApiAccess, ProviderSearch, ProviderStatus, Search]):
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
