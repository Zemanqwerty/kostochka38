from django.core.management import BaseCommand

from catalog.models import WareHouse, LeftItem, Item


class Command(BaseCommand):
    def handle(self, *args, **options):
        warehouse = WareHouse.objects.order_by('id').first()
        items = Item.objects.all()
        for item in items:
            left_item = LeftItem()
            left_item.item = item
            left_item.warehouse = warehouse
            left_item.left = item.quantity_in_reserve
            left_item.save()