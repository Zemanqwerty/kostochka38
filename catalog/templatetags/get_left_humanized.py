# -*- coding: utf-8 -*-

from django import template
from django.db.models import Q, Sum

from catalog.models import LeftItem


register = template.Library()


@register.filter
def get_left_humanized(item, warehouse=None):
    if warehouse is None:
        count_zakaz = item.zakazgoods_set.filter(zakaz__status__in=[2, 3, 4, 5, 31]).exclude(zakaz__owner__id=577).aggregate(sum=Sum('quantity'))['sum'] or 0
        if item.quantity_in_stock - count_zakaz < 1:
            return u'<td style="color: #777 !important;">Нет в наличии</td>'
        elif item.quantity_in_stock - count_zakaz == 1:
            return u'<td style="color: #a94442 !important;">Мало</td>'
        elif item.quantity_in_stock - count_zakaz > 1 and item.quantity_in_stock - count_zakaz < 5:
            return u'<td style="color: #8a6d3b; !important">Достаточно</td>'
        else:
            return u'<td style="color: #3c763d !important;">Много</td>'

    count_zakaz = item.zakazgoods_set.filter(zakaz__status__in=[2, 3, 4, 5, 31]).exclude(zakaz__owner__id=577).aggregate(sum=Sum('quantity'))['sum'] or 0
    left_item = LeftItem.objects.filter(Q(item=item) & Q(warehouse=warehouse)).first()
    if left_item is not None:
        if left_item.warehouse.type == 0:
            if item.availability == 20:
                return u'<td style="color: #3c763d !important;">Под заказ</td>'
            else:
                if left_item.left - count_zakaz < 1:
                    return u'<td style="color: #777 !important;">Нет в наличии</td>'
                elif left_item.left - count_zakaz == 1:
                    return u'<td style="color: #a94442 !important;">Мало</td>'
                elif left_item.left - count_zakaz > 1 and left_item.left - count_zakaz < 5:
                    return u'<td style="color: #8a6d3b; !important">Достаточно</td>'
                else:
                    return u'<td style="color: #3c763d !important;">Много</td>'
        if left_item.left - count_zakaz < 1:
            return u'<td style="color: #777 !important;">Нет в наличии</td>'
        elif left_item.left - count_zakaz == 1:
            return u'<td style="color: #a94442 !important;">Мало</td>'
        elif left_item.left - count_zakaz > 1 and left_item.left - count_zakaz < 5:
            return u'<td style="color: #8a6d3b; !important">Достаточно</td>'
        else:
            return u'<td style="color: #3c763d !important;">Много</td>'
    else:
        return u'<td style="color: #777 !important;">Нет в наличии</td>'
