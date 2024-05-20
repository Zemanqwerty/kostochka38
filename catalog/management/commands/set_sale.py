# -*- coding: utf-8 -*-
import datetime

from django.core.management import BaseCommand

from catalog.models import WareHouse, LeftItem, Item, ItemSale


class Command(BaseCommand):
    def handle(self, *args, **options):
        sale_size = 50
        now = datetime.datetime.now() + datetime.timedelta(days=360)

        left_items = LeftItem.objects.filter(left__gt=0).values_list('item_id', flat=True)
        items = Item.objects.filter(id__in=left_items).distinct()
        n = 0
        for item in items:
            n += 1
            print(item.title())
            # print(item.id)
            lefts = LeftItem.objects.filter(item_id=item.id)
            for left in lefts:
                print((str(left.warehouse.id) + ' - ' + str(left.left)))

            sales = ItemSale.objects.filter(item_id=item.id)
            # for sale in sales:
            #     print(sale.sale)
            ItemSale.objects.filter(item_id=item.id, sale__lt=sale_size).delete()

            if not ItemSale.objects.filter(item_id=item.id, sale__gte=sale_size).exists():
                # print('create sale')
                new_sale = ItemSale(
                    item_id=item.id,
                    sale_target=0,
                    sale=sale_size,
                    show=False,
                    date_end=now,
                    description=u'Ликвидация'
                )
                new_sale.save()

            # if n > 20:
            #     break
