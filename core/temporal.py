# -*- coding: utf-8 -*-
import xlrd
from django.db.models import Max

from django.template import RequestContext
from django.shortcuts import render
from catalog.models import *
from news.models import *
from django.conf import settings


def get_last_order_date(request):

    items = Item.objects.all().order_by('id').values()
    count = 0
    for i in items:
        last_order = ZakazGoods.objects.filter(item=i['id']).annotate(last_order_date=Max('zakaz__date_end')).order_by('-last_order_date')
        if last_order.count() > 0:
            this_item = Item.objects.get(id=i['id'])
            this_item.last_order_date = last_order.values()[0]['last_order_date']
            this_item.save()

        count += 1

    return render(request, 'newprice_parsing_result.html', {})


def set_all_tags(request):

    deckitems = Deckitem.objects.all().order_by('id').values()

    for i in deckitems:
        if int(i['tag_id']) != 0:
            if not DeckitemTag.objects.filter(tag=i['tag_id'], deckitem=i['id']):
                tagdeckitem = DeckitemTag(
                    tag_id=i['tag_id'],
                    deckitem_id=i['id']
                )
                tagdeckitem.save()

    return render(request, 'newprice_parsing_result.html', {})


def get_newitem_multiline(request, segment, path_to_file):

    path_to_price = os.path.join(settings.CURRPATH, '_new_price')
    path_to_image = '/var/www/vanger/data/www/104_kostochka38_napolnenie/media/photos/zooirkutsk'
    # path_to_image = '/kostochka38/media/photos/zooirkutsk'
    book = xlrd.open_workbook(path_to_price + "/" + path_to_file)
    result = {
        'new_items': [],
        'double_items': []
    }
    new_deckitem = False

    sh = book.sheet_by_index(0)

    for rx in range(sh.nrows):
        if not sh.cell_value(rowx=rx, colx=0) and not sh.cell_value(rowx=rx, colx=4):  # заголовок, пропускаем
            continue

        if not sh.cell_value(rowx=rx, colx=0) and sh.cell_value(rowx=rx, colx=4):  # заглавие товара
            row = {
                'title': sh.cell_value(rowx=rx, colx=1),
                'tag': int(sh.cell_value(rowx=rx, colx=5)),
                'all_tag': int(sh.cell_value(rowx=rx, colx=6)),
                'producer': int(sh.cell_value(rowx=rx, colx=4))
            }

            new_deckitem = Deckitem(
                title=row['title'],
                tag_id=row['tag'],
                producer_id=row['producer'],
                active=True,
                segment=segment,
                description='',
                composition='',
                ration=''
            )
            new_deckitem.save()

            tagdeckitem = DeckitemTag(
                tag_id=row['all_tag'],
                deckitem_id=new_deckitem.id
            )
            tagdeckitem.save()

            result['new_items'].append(new_deckitem)
            continue

        if sh.cell_value(rowx=rx, colx=0):  # вес товара с ценой
            row = {
                'code': sh.cell_value(rowx=rx, colx=0),
                'weight': sh.cell_value(rowx=rx, colx=2),
                'price': sh.cell_value(rowx=rx, colx=8),
                'quantity_in_stock': int(sh.cell_value(rowx=rx, colx=7)),
                'amount_in_block': 0
            }

            if sh.cell_value(rowx=rx, colx=3):
                row['amount_in_block'] = int(sh.cell_value(rowx=rx, colx=3))

            items = Item.objects.filter(code=row['code'])

            if items.count() > 0:
                result['double_items'].append(row)
                continue

            elif items.count() == 0:
                image = 'empty.png'
                if os.path.exists(path_to_image + '/' + row['code'] + '.jpg'):
                    image = row['code'] + '.jpg'
                if os.path.exists(path_to_image + '/' + row['code'] + '.jpeg'):
                    image = row['code'] + '.jpeg'
                if os.path.exists(path_to_image + '/' + row['code'] + '.png'):
                    image = row['code'] + '.png'
                if os.path.exists(path_to_image + '/' + row['code'] + '.gif'):
                    image = row['code'] + '.gif'
                if os.path.exists(path_to_image + '/' + row['code'] + '.JPG'):
                    image = row['code'] + '.JPG'
                if os.path.exists(path_to_image + '/' + row['code'] + '.bmp'):
                    image = row['code'] + '.bmp'

                new_item = Item(
                    deckitem_id=new_deckitem.id,
                    code=row['code'],
                    article=row['code'],
                    real_price=row['price'],
                    weight=row['weight'],
                    amount_in_block=row['amount_in_block'],
                    quantity_in_stock=row['quantity_in_stock'],
                    original_image='photos/zooirkutsk/' + image
                )
                new_item.save()
                result['new_items'].append(new_item)
            continue

    return render(request, 'newprice_parsing_result.html', {
        'result': result,
    })


def get_newitem_line(request, segment, path_to_file):
    path_to_price = os.path.join(settings.CURRPATH, '_new_price')
    path_to_image = '/var/www/vanger/data/www/104_kostochka38_napolnenie/media/photos/zooirkutsk'
    # path_to_image = '/kostochka38/media/photos/zooirkutsk'
    book = xlrd.open_workbook(path_to_price + "/" + path_to_file)
    result = {
        'new_items': [],
        'double_items': []
    }
    sh = book.sheet_by_index(0)

    for rx in range(sh.nrows):
        if not sh.cell_value(rowx=rx, colx=0):  # заголовок, пропускаем
            continue
        if sh.cell_value(rowx=rx, colx=0):  # заглавие товара
            row = {
                'code': sh.cell_value(rowx=rx, colx=0),
                'title': sh.cell_value(rowx=rx, colx=1),
                'amount_in_block': 0,
                'producer': sh.cell_value(rowx=rx, colx=4),
                'weight': sh.cell_value(rowx=rx, colx=2),
                'tag': int(sh.cell_value(rowx=rx, colx=5)),
                'all_tags': int(sh.cell_value(rowx=rx, colx=6)),
                'price': sh.cell_value(rowx=rx, colx=8),
                'quantity_in_stock': int(sh.cell_value(rowx=rx, colx=7)),
            }
            if sh.cell_value(rowx=rx, colx=3):
                row['amount_in_block'] = int(sh.cell_value(rowx=rx, colx=3))

            items = Item.objects.filter(code=row['code'])
            if items.count() > 0:
                result['double_items'].append(row)
                continue

            if items.count() == 0:
                new_deckitem = Deckitem(
                    title=row['title'],
                    tag_id=row['tag'],
                    producer_id=int(row['producer']),
                    active=True,
                    segment=segment,
                    description='',
                    composition='',
                    ration=''
                )
                new_deckitem.save()

                tagdeckitem = DeckitemTag(
                    tag_id=int(row['all_tags']),
                    deckitem_id=new_deckitem.id
                )
                tagdeckitem.save()
                result['new_items'].append(new_deckitem)

                image = 'empty.png'
                if os.path.exists(path_to_image + '/' + row['code'] + '.jpg'):
                    image = row['code'] + '.jpg'
                if os.path.exists(path_to_image + '/' + row['code'] + '.jpeg'):
                    image = row['code'] + '.jpeg'
                if os.path.exists(path_to_image + '/' + row['code'] + '.png'):
                    image = row['code'] + '.png'
                if os.path.exists(path_to_image + '/' + row['code'] + '.gif'):
                    image = row['code'] + '.gif'
                if os.path.exists(path_to_image + '/' + row['code'] + '.JPG'):
                    image = row['code'] + '.JPG'
                if os.path.exists(path_to_image + '/' + row['code'] + '.bmp'):
                    image = row['code'] + '.bmp'

                new_item = Item(
                    deckitem_id=new_deckitem.id,
                    code=row['code'],
                    article=row['code'],
                    real_price=row['price'],
                    weight=row['weight'],
                    amount_in_block=row['amount_in_block'],
                    quantity_in_stock=row['quantity_in_stock'],
                    original_image='photos/zooirkutsk/' + image
                )
                new_item.save()
                result['new_items'].append(new_item)

            continue

    return render(request, 'newprice_parsing_result.html', {
        'result': result,
    })


def royal_availability(request):
    error = {}
    if request.user.is_superuser:
        items = Item.objects.filter(deckitem__segment='royal', quantity_in_reserve=0)
        items.update(availability=3)
        error = {'text': str(items.count())}

    return render(request, 'price_parsing_result.html', {
        'error': error['text'],
    })