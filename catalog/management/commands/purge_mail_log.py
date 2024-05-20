import logging
import datetime
from django.utils.timezone import now as datetime_now
from django.core.management.base import BaseCommand
from mailer.models import MessageLog

RESULT_SUCCESS = "1"

class Command(BaseCommand):
    help = "Delete mailer log"

    def add_arguments(self, parser):
        parser.add_argument('days', nargs=1, type=int)

    def handle(self, *args, **options):
        # Compatiblity with Django-1.6
        days = int(options.get('days', args)[0])
        limit = datetime_now() - datetime.timedelta(days=days)
        query = MessageLog.objects.filter(when_attempted__lt=limit, result=RESULT_SUCCESS)
        count = query.count()
        query.delete()
        logging.info("%s log entries deleted " % count)