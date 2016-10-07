import os
from playhouse.sqliteq import SqliteQueueDatabase

from peewee import CharField, Model
from playhouse.sqliteq import SqliteQueueDatabase

if os.path.exists("reproduce.db"):
    os.remove("reproduce.db")
if os.path.exists("peewee.db"):
    os.remove("peewee.db")

db = SqliteQueueDatabase(None)

class TestModel(Model):
    test = CharField(null=True)

    class Meta(object):
        database = db


db.init("reproduce.db")
TestModel.create_table()

was_started = db.start()
print("Database was started: %s" % was_started)
was_stopped = db.stop()
print("Database was stopped: %s" % was_stopped)
print("Database is stopped: %s" % db.is_stopped())
db.close()
is_closed = db.is_closed()
print("Database is closed: %s" % is_closed)
try:
    os.unlink("reproduce.db")
    print("Database file was deleted")
except Exception:
    print("Database file still locked")
