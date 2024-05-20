from django.core.management import BaseCommand

from catalog.models import Item


class Command(BaseCommand):

    def handle(self, *args, **options):
        items = Item.objects.all()
        for item in items:
            item.barcode = item.article
            item.save()