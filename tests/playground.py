import database
from database import Provider
database.db.drop_tables([Provider])
database.db.create_tables([Provider])

p = Provider(name="Hallo")
p.save()


