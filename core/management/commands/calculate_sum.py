# -*- coding: utf-8 -*-
import glob
import os
import inspect

from django.core.management import BaseCommand
from django.contrib.sitemaps import GenericSitemap, Sitemap
from django.template.loader import render_to_string
from catalog.models import *


class Command(BaseCommand):

    # def add_arguments(self, parser):
    #     parser.add_argument('sitemap_folder_path', type=str)

    def handle(self, *args, **options):
        segments_objects = Segment.objects.filter(in_balans=True)

        sale_sum = 0
        buy_sum = 0

        for i in segments_objects:
            if i.id == 16:
                continue
            items = Item.objects.filter(quantity_in_reserve__gt=0, deckitem__segment_new=i)
            items_sale_sum = 0
            items_buy_sum = 0
            for j in items:
                last_order_line = InsideZakazGoods.objects.filter(item=j, zakaz__status=6).order_by('-id').first()
                real_price = 0
                if last_order_line:
                    real_price = last_order_line.cost/last_order_line.quantity
                else:
                    print(u'товар не найден: ' + j.deckitem.title)
                    continue

                items_sale_sum += j.quantity_in_reserve * j.current_price()
                items_buy_sum += j.quantity_in_reserve * real_price

            i.sale_sum = items_sale_sum
            i.buy_sum = items_buy_sum
            procent = 0
            if items_sale_sum > 0:
                procent = round(((i.sale_sum - i.buy_sum) / i.sale_sum)*100, 2)
            print(i.title + ' ' + str(items_sale_sum) + '/' + str(items_buy_sum) + ' = ' + str(procent) + '%')

            sale_sum += items_sale_sum
            buy_sum += items_buy_sum

        print('---')
        print(u'продали: ' + str(sale_sum))
        print(u'купили: ' + str(buy_sum))
        print(u'процент: ' + str(round((((sale_sum*0.94)-buy_sum)/(sale_sum*0.94))*100, 2)) + '%')
