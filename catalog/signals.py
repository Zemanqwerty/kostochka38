# -*- coding: utf-8 -*-

from django.dispatch import receiver
from django.db.models.signals import pre_save
from django.db.models import Sum

from catalog.models import Item, ItemPriceChange, TempZakaz


@receiver(pre_save, sender=Item, dispatch_uid='on_item_pre_save')
def on_item_pre_save(sender, instance, **kwargs):
    '''
    Хук для фикасации изменения состояния товара
    '''
    if instance.id:
        original = Item.objects.get(id=instance.id)

        if instance.real_price != original.real_price:
            # Фиксация изменения цены для всех розничных магазинов, в
            # которых данный товар есть в наличии
            for leftitem in instance.leftitem_set.all():
                if leftitem.warehouse.type == 1 and leftitem.left > 0:
                    ItemPriceChange.objects.create(
                        item=instance,
                        warehouse=leftitem.warehouse
                    )
            # Фиксация изменения цены для всех корзин, в которых
            # присутствует данный товар
            if instance.availability != 0:
                # Изменение необходимо фиксировать только, если
                # товар есть в наличии
                for zakaz in TempZakaz.objects.filter(tempzakazgoods__item=instance):
                    for goods in zakaz.tempzakazgoods_set.filter(item=instance):
                        goods.summ_changed = True
                        goods.save()