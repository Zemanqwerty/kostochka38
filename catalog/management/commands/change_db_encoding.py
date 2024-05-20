from django.core.management import BaseCommand
from django.conf import settings
import MySQLdb


# class Command(BaseCommand):

#     def handle(self, *args, **options):
#         db = MySQLdb.connect(host=settings.DB_HOST, user=settings.DB_USER, passwd=settings.DB_PASS, db=settings.DB_NAME)
#         cursor = db.cursor()
#         dbname = settings.DB_NAME

#         cursor.execute("ALTER DATABASE `%s` CHARACTER SET 'utf8' COLLATE 'utf8_unicode_ci'" % dbname)

#         sql = "SELECT DISTINCT(table_name) FROM information_schema.columns WHERE table_schema = '%s'" % dbname
#         cursor.execute(sql)

#         results = cursor.fetchall()
#         for row in results:
#             sql = "ALTER TABLE `%s` convert to character set DEFAULT COLLATE DEFAULT" % (row[0])
#             cursor.execute(sql)
#         db.close()