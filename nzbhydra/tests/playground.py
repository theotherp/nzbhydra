from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import random
import string

# standard_library.install_aliases()
import zlib
from builtins import *
from playhouse.sqlite_ext import SqliteExtDatabase, Model, CharField, IntegerField, BlobField

db = SqliteExtDatabase("nzbhydra/tests/playground.db", threadlocals=True, journal_mode="WAL")


class Test(Model):
    indexer = IntegerField()
    searchid = IntegerField()
    link = CharField()
    title = CharField()
    details = CharField()
    guid = CharField()

    class Meta(object):
        database = db


db.create_table(Test)

Test.delete().execute()


# title = zlib.compress(title)
# link = zlib.compress(link)
# details = zlib.compress(details)
# guid = zlib.compress(guid)
# 5mb fuer 99999 unkomprimiert
# 3.5mb fuer 9999 komprimiert. Nicht wert...
# 10000 TV releases per day
# 400 movie releases per day
# 100 audio releases per day

with db.atomic() as txn:
    for i in range(0, 10500 * 7):
        title = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(80))
        link = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(120))
        details = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(120))
        guid = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(120))

        # for i in range(0, 10000):
        Test().create(indexer=i, searchid=i, title=title, link=link, details=details, guid=guid)

print(Test.select().count())
