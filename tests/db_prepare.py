from peewee import OperationalError

import database
from database import Provider


def set_and_drop():
    database.db.init("tests.db")
    database.db.connect()

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
