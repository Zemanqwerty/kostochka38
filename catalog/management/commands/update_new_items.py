from django.core.management import BaseCommand
from django.utils import timezone

from catalog.models import Item


class Command(BaseCommand):
    def handle(self, *args, **options):
        for item in Item.objects.filter(new=True):
            td = timezone.now() - item.date_created
            if td.days > 11:
                item.new = False
                item.save()