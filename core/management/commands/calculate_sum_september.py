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
        # ИНТЕРНЕТ
        # orders_objects = Zakaz.objects.filter(warehouse_id=1, date_end__lte=datetime.datetime(2023, 11, 30), date_end__gte=datetime.datetime(2023, 9, 1), status=6)

        # РОЗНИЦА
        orders_objects = Zakaz.objects.filter(warehouse_id=2, date_end__lte=datetime.datetime(2023, 11, 30), date_end__gte=datetime.datetime(2023, 9, 1), status=6)

        # ИНТЕРНЕТ и РОЗНИЦА
        #orders_objects = Zakaz.objects.filter(date_end__lte=datetime.datetime(2023, 11, 30), date_end__gte=datetime.datetime(2023, 9, 1), status=6)

        sale_sum = 0
        buy_sum = 0

        for i in orders_objects:
            if i.owner.id == 1:
                continue

            items = ZakazGoods.objects.filter(zakaz=i)

            """
            ОБЩАЯ МАРЖИНАЛЬНОСТЬ
            """
            # items_sale_sum = 0
            items_buy_sum = 0

            for j in items:
                item = j.item
                last_order_line = InsideZakazGoods.objects.filter(item=item, zakaz__status=6, zakaz__date__lte=j.zakaz.date).order_by('-id').first()

                if last_order_line:
                    real_price = last_order_line.cost/last_order_line.quantity
                else:
                    print(u'товар не найден: ' + item.deckitem.title)
                    real_price = item.real_price

                # items_sale_sum += item.quantity_in_reserve * item.current_price()
                items_buy_sum += j.quantity * real_price

            procent = 0
            if i.k_oplate() > 0:
                procent = round(((i.k_oplate() - items_buy_sum) / i.k_oplate())*100, 2)
            # print(i.owner.username + ' ' + str(i.k_oplate()) + '/' + str(items_buy_sum) + ' = ' + str(procent) + '%')

            sale_sum += i.k_oplate()
            buy_sum += items_buy_sum

            """
            ТОЛЬКО ВЭЛКОРМ
            # """
            # items_sale_sum = 0
            # items_buy_sum = 0
            #
            # for j in items:
            #     item = j.item
            #
            #     if not item.deckitem.segment_new.id == 16:
            #         continue
            #
            #     last_order_line = InsideZakazGoods.objects.filter(item=item, zakaz__status=6, zakaz__date__lte=j.zakaz.date).order_by('-id').first()
            #
            #     if last_order_line:
            #         real_price = last_order_line.cost/last_order_line.quantity
            #     else:
            #         print(u'товар не найден: ' + item.deckitem.title)
            #         real_price = item.real_price
            #
            #     # items_sale_sum += item.quantity_in_reserve * item.current_price()
            #     items_buy_sum += j.quantity * real_price
            #
            # procent = 0
            # if i.k_oplate(only_velrokm=True) > 0:
            #     procent = round(((i.k_oplate(only_velrokm=True) - items_buy_sum) / i.k_oplate(only_velrokm=True))*100, 2)
            # # print(i.owner.username + ' ' + str(i.k_oplate()) + '/' + str(items_buy_sum) + ' = ' + str(procent) + '%')
            #
            # sale_sum += i.k_oplate(only_velrokm=True)
            # buy_sum += items_buy_sum


            """
            БЕЗ ВЭЛКОРМА
            """
            # items_sale_sum = 0
            # items_buy_sum = 0
            #
            # for j in items:
            #     item = j.item
            #
            #     if item.deckitem.segment_new.id == 16:
            #         continue
            #
            #     last_order_line = InsideZakazGoods.objects.filter(item=item, zakaz__status=6, zakaz__date__lte=j.zakaz.date).order_by('-id').first()
            #
            #     if last_order_line:
            #         real_price = last_order_line.cost/last_order_line.quantity
            #     else:
            #         print(u'товар не найден: ' + item.deckitem.title)
            #         real_price = item.real_price
            #
            #     # items_sale_sum += item.quantity_in_reserve * item.current_price()
            #     items_buy_sum += j.quantity * real_price
            #
            # procent = 0
            # if i.k_oplate(without_velrokm=True) > 0:
            #     procent = round(((i.k_oplate(without_velrokm=True) - items_buy_sum) / i.k_oplate(without_velrokm=True))*100, 2)
            # # print(i.owner.username + ' ' + str(i.k_oplate()) + '/' + str(items_buy_sum) + ' = ' + str(procent) + '%')
            #
            # sale_sum += i.k_oplate(without_velrokm=True)
            # buy_sum += items_buy_sum

        print('---')
        print(u'продали: ' + str(sale_sum))
        print(u'купили: ' + str(buy_sum))
        print(u'процент: ' + str(round((((sale_sum)-buy_sum)/(sale_sum))*100, 2)) + '%')
