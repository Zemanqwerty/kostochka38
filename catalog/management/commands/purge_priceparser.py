import logging
import datetime
from django.utils.timezone import now as datetime_now
from django.core.management.base import BaseCommand
from catalog.models import PriceParser

class Command(BaseCommand):
    help = "Delete PriceParser entries"

    def add_arguments(self, parser):
        parser.add_argument('days', nargs=1, type=int)

    def handle(self, *args, **options):
        days = int(options.get('days', args)[0])
        limit = datetime_now() - datetime.timedelta(days=days)
        query = PriceParser.objects.filter(date__lt=limit)
        count = query.count()
        query.delete()
        logging.info("%s PriceParser entries deleted " % count)