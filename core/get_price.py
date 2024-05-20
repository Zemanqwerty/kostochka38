# -*- coding: utf-8 -*-
from django.shortcuts import render
from catalog.models import *
from news.models import *
from django.template import Context, engines, loader
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.encoding import force_str

import xlrd


@staff_member_required
def get_price(request):
    error = ''
    result = {
        'new_items': [],
        'good_items': [],
        'good_items_notactive': [],
        'new_price_items': [],
        'miss_items': [],
        'double_items': []
    }

    id_list = []

    obj_price_id = request.GET.get('obj')
    obj_price = PriceParser.objects.get(id=obj_price_id)

    if obj_price.status == 1:
        obj_price.status = 3
        obj_price.save()

        rx = 0
        row = 0

        try:
            file_path = obj_price.price_file.path
            if obj_price.segment_new.need_special_article:
                book = xlrd.open_workbook(file_path, formatting_info=True)
            else:
                book = xlrd.open_workbook(file_path)
            sh = book.sheet_by_index(0)

            n = 0
            m = 0
            for rx in range(sh.nrows):
                m += 1
                n += 1
                if n > 100:
                    n = 0
                    data = {
                        'm': m,
                        'items': result['new_items'],
                        'result': result,
                        'error': error,
                        'date': datetime.datetime.now()
                    }
                    template = loader.get_template('get_price/error.html')
                    message = template.render(data).encode('utf-8')
                    obj_price.error = force_str(message)

                    template = loader.get_template('get_price/result_1.html')
                    message = template.render(data).encode('utf-8')
                    obj_price.result_1 = force_str(message)

                    template = loader.get_template('get_price/result_2.html')
                    message = template.render(data).encode('utf-8')
                    obj_price.result_2 = force_str(message)

                    template = loader.get_template('get_price/result_3.html')
                    message = template.render(data).encode('utf-8')
                    obj_price.result_3 = force_str(message)

                    template = loader.get_template('get_price/result_4.html')
                    message = template.render(data).encode('utf-8')
                    obj_price.result_4 = force_str(message)

                    template = loader.get_template('get_price/result_5.html')
                    message = template.render(data).encode('utf-8')
                    obj_price.result_5 = force_str(message)

                    obj_price.save()

                if rx < (obj_price.segment_new.num_start - 1):
                    continue

                if obj_price.segment_new.num_check_empty:
                    if not sh.cell_value(rowx=rx, colx=(obj_price.segment_new.num_check_empty - 1)):
                        continue

                quantity = 99

                if obj_price.segment_new.need_quantity:  # если в прайсе есть количество
                    quantity = 0
                    if sh.cell_value(rowx=rx, colx=(obj_price.segment_new.num_quantity - 1)):
                        quantity = sh.cell_value(rowx=rx, colx=(obj_price.segment_new.num_quantity - 1))

                    if obj_price.segment_new.word_to_quantity:  # если в прайсе есть количество текстом
                        try:
                            if quantity == obj_price.segment_new.word_to_quantity:
                                quantity = 99
                            else:
                                quantity = 0
                        except:
                            quantity = 99
                    elif obj_price.segment_new.word_to_quantity_small:
                        try:
                            if quantity == obj_price.segment_new.word_to_quantity_small:
                                quantity = 10
                            else:
                                quantity = 99
                        except:
                            quantity = 99

                    try:
                        quantity = int(quantity)
                    except:
                        quantity = 99

                row = {
                    'title': sh.cell_value(rowx=rx, colx=(obj_price.segment_new.num_title - 1)),
                    'code': sh.cell_value(rowx=rx, colx=(obj_price.segment_new.num_code - 1)),
                    'article': sh.cell_value(rowx=rx, colx=(obj_price.segment_new.num_article - 1)),
                    'price': sh.cell_value(rowx=rx, colx=(obj_price.segment_new.num_price - 1)),
                    'quantity': quantity,
                }

                special_article = False
                if obj_price.segment_new.need_special_article:
                    format_str = book.format_map[book.xf_list[
                        sh.cell(rowx=rx, colx=(obj_price.segment_new.num_code - 1)).xf_index].format_key].format_str
                    try:
                        if str(format_str) != '0':
                            special_article = format_str.replace('"', '')
                            try:
                                row['article'] = int(row['article'])
                            except:
                                pass
                            special_article = special_article.replace('0', str(row['article']))
                            row['article'] = special_article
                    except:
                        pass

                try:
                    row['article'] = int(row['article'])
                except:
                    pass

                try:
                    row['code'] = int(row['code'])
                except:
                    pass

                code = row['code']
                article = row['article']
                if not row['price']:
                    continue

                item = Item.objects.filter(code=code, deckitem__segment_new__link=obj_price.segment_new.link).select_related('deckitem')
                # if item.count() == 0:
                #     # item = Item.objects.filter(article=article, deckitem__segment_new__link=obj_price.segment_new.link)
                #     t1 += 1
                # else:
                #     t15 += 1
                # if item.count() == 0:
                #     item = Item.objects.filter(article=code, deckitem__segment_new__link=obj_price.segment_new.link)
                #     t2 += 1
                # if item.count() == 0:
                #     item = Item.objects.filter(code=article, deckitem__segment_new__link=obj_price.segment_new.link)
                #     t3 += 1
                #
                # if item.count() == 0:
                #     try:
                #         article = str(row['article']).strip()
                #     except:
                #         pass
                #
                #     try:
                #         code = str(row['code']).strip()
                #     except:
                #         pass
                #     item = Item.objects.filter(article=article, deckitem__segment_new__link=obj_price.segment_new.link)
                #     t4 += 1
                # if item.count() == 0:
                #     item = Item.objects.filter(code=code, deckitem__segment_new__link=obj_price.segment_new.link)
                #     t5 += 1
                # if item.count() == 0:
                #     item = Item.objects.filter(article=code, deckitem__segment_new__link=obj_price.segment_new.link)
                #     t6 += 1
                # if item.count() == 0:
                #     item = Item.objects.filter(code=article, deckitem__segment_new__link=obj_price.segment_new.link)
                #     t7 += 1

                # pre_1 = '0'
                # pre_2 = '00'
                # pre_3 = '000'
                # pre_4 = '0000'
                # pre_5 = '00000'
                #
                # try:
                #     if item.count() == 0:
                #         code = pre_1 + str(row['code'])
                #         item = Item.objects.filter(code=code, deckitem__segment_new__link=obj_price.segment_new.link)
                #         t8 += 1
                #     if item.count() == 0:
                #         code = pre_2 + str(row['code'])
                #         item = Item.objects.filter(code=code, deckitem__segment_new__link=obj_price.segment_new.link)
                #         t9 += 1
                #     if item.count() == 0:
                #         code = pre_3 + str(row['code'])
                #         item = Item.objects.filter(code=code, deckitem__segment_new__link=obj_price.segment_new.link)
                #         t10 += 1
                #     if item.count() == 0:
                #         code = pre_4 + str(row['code'])
                #         item = Item.objects.filter(code=code, deckitem__segment_new__link=obj_price.segment_new.link)
                #         t11 += 1
                #     if item.count() == 0:
                #         code = pre_5 + str(row['code'])
                #         item = Item.objects.filter(code=code, deckitem__segment_new__link=obj_price.segment_new.link)
                #         t12 += 1
                # except:
                #     pass

                if item.count() == 1:
                    this_element = item.first()
                    this_element.quantity_in_stock = row['quantity']
                    if this_element.availability != 10:

                        if obj_price.segment_new.what_status == 3:
                            if this_element.quantity_in_stock > 0:
                                this_element.availability = 3
                            else:
                                this_element.availability = 0
                        elif obj_price.segment_new.what_status == 20:
                            if this_element.quantity_in_stock > 0:
                                this_element.availability = 20
                            else:
                                this_element.availability = 0
                    id_list.append(this_element.id)

                    if round(float(row['price']), 2) == float(this_element.real_price):  # товар нашелся, цена осталась прежней
                        if this_element.active:
                            result['good_items'].append({
                                'price_item': row,
                                'base_item': this_element
                            })
                        elif not this_element.active:
                            result['good_items_notactive'].append({
                                'price_item': row,
                                'base_item': this_element
                            })

                    else:  # товар нашелся, цена изменилась
                        this_element.real_price = row['price']
                        result['new_price_items'].append({
                            'price_item': row,
                            'base_item': this_element,
                            'diff_price': float(row['price']) - float(this_element.real_price)
                        })
                    this_element.save()  # сохраняем товар

                if item.count() == 0:  # товар не нашелся (новые элементы)
                    result['new_items'].append(row)

                if item.count() > 1:  # товар задублировался??
                    result['double_items'].append(row)
                    error += u', дубль: (%s, %s)' % (code, article)
                    for one_item in item.values():
                        id_list.append(one_item['id'])

            result['miss_items'] = Item.objects.filter(deckitem__segment_new__link=obj_price.segment_new.link).exclude(id__in=id_list).exclude(active=False).select_related('deckitem')  # товар есть в базе, нет в прайсе

            # автоматическое изменение наличия товара
            Item.objects.filter(deckitem__segment_new__link=obj_price.segment_new.link).exclude(id__in=id_list).exclude(active=False).update(quantity_in_stock=0)
            item_for_write_availability_log = Item.objects.filter(deckitem__segment_new__link=obj_price.segment_new.link).exclude(id__in=id_list).exclude(active=False).exclude(availability=10)
            for i in item_for_write_availability_log:
                if i.availability != 0:
                    new_itemavailabilitylog = ItemAvailabilityLog(
                        item_id=i.id,
                        availability=0
                    )
                    new_itemavailabilitylog.save()
            item_for_write_availability_log.update(availability=0)

            data = {
                'm': m,
                'items': result['new_items'],
                'result': result,
                'error': error,
                'date': datetime.datetime.now()
            }

            template = loader.get_template('get_price/error.html')
            message = template.render(data).encode('utf-8')
            obj_price.error = force_str(message)

            template = loader.get_template('get_price/result_1.html')
            message = template.render(data).encode('utf-8')
            obj_price.result_1 = force_str(message)

            template = loader.get_template('get_price/result_2.html')
            message = template.render(data).encode('utf-8')
            obj_price.result_2 = force_str(message)

            template = loader.get_template('get_price/result_3.html')
            message = template.render(data).encode('utf-8')
            obj_price.result_3 = force_str(message)

            template = loader.get_template('get_price/result_4.html')
            message = template.render(data).encode('utf-8')
            obj_price.result_4 = force_str(message)

            template = loader.get_template('get_price/result_5.html')
            message = template.render(data).encode('utf-8')
            obj_price.result_5 = force_str(message)

            obj_price.status = 2
            obj_price.save()

            return render(request, 'price_parsing_result.html', {
                'result': result,
                'error_text': error,
            })
        except Exception as e:
            obj_price.status = 4
            obj_price.extra = '%s, row# %s, row:%s' % (e, rx, row)
            obj_price.save()
            error = u'Обработка завершилась ошибкой, подробности смотри в объекте'

    else:
        error = u'Обработка не запущена, так как текущий статус %s' % obj_price.get_status_display()
    return render(request, 'price_parsing_result.html', {
        'result': result,
        'error': error,
    })


@staff_member_required
def get_price_barcode(request, segment):
    error = ''
    result = {
        'new_items': [],
        'good_items': [],
        'good_items_notactive': [],
        'new_price_items': [],
        'miss_items': [],
        'double_items': []
    }

    id_list = []
    rx = 0
    row = 0
    # file_path = '/Users/vanger/projects/kostochka38/price/%s.xls' % segment
    file_path = '/var/www/www-root/data/www/kostochka38/price/%s.xls' % segment
    book = xlrd.open_workbook(file_path)
    sh = book.sheet_by_index(0)

    for rx in range(sh.nrows):
        if not sh.cell_value(rowx=rx, colx=1) or not sh.cell_value(rowx=rx, colx=0):
            continue

        values = sh.row_values(rx)

        if type(values[0]) is float:
            code_str = repr(values[0]).split(".")[0]
        else:
            code_str = values[0]
        product_code = code_str.strip(' \t\n\r')

        row = {
            'code': sh.cell_value(rowx=rx, colx=1),
            'article': sh.cell_value(rowx=rx, colx=1),
            'barcode': product_code,
        }

        try:
            row['article'] = int(row['article'])
        except:
            pass

        try:
            row['code'] = int(row['code'])
        except:
            pass

        code = row['code']
        article = row['article']

        item = Item.objects.filter(article=article, deckitem__segment_new__link=segment)
        if item.count() == 0:
            item = Item.objects.filter(code=code, deckitem__segment_new__link=segment)
        if item.count() == 0:
            item = Item.objects.filter(article=code, deckitem__segment_new__link=segment)
        if item.count() == 0:
            item = Item.objects.filter(code=article, deckitem__segment_new__link=segment)

        if item.count() == 0:
            try:
                article = str(row['article']).strip()
            except:
                pass

            try:
                code = str(row['code']).strip()
            except:
                pass
            item = Item.objects.filter(article=article, deckitem__segment_new__link=segment)
        if item.count() == 0:
            item = Item.objects.filter(code=code, deckitem__segment_new__link=segment)
        if item.count() == 0:
            item = Item.objects.filter(article=code, deckitem__segment_new__link=segment)
        if item.count() == 0:
            item = Item.objects.filter(code=article, deckitem__segment_new__link=segment)

        pre_1 = '0'
        pre_2 = '00'
        pre_3 = '000'
        pre_4 = '0000'
        pre_5 = '00000'

        try:
            if item.count() == 0:
                code = pre_1 + str(row['code'])
                item = Item.objects.filter(code=code, deckitem__segment_new__link=segment)
            if item.count() == 0:
                code = pre_2 + str(row['code'])
                item = Item.objects.filter(code=code, deckitem__segment_new__link=segment)
            if item.count() == 0:
                code = pre_3 + str(row['code'])
                item = Item.objects.filter(code=code, deckitem__segment_new__link=segment)
            if item.count() == 0:
                code = pre_4 + str(row['code'])
                item = Item.objects.filter(code=code, deckitem__segment_new__link=segment)
            if item.count() == 0:
                code = pre_5 + str(row['code'])
                item = Item.objects.filter(code=code, deckitem__segment_new__link=segment)
        except:
            pass

        if item.count() == 1:
            this_element = Item.objects.get(id=item.values()[0]['id'])
            this_element.barcode = row['barcode']
            this_element.save()  # сохраняем товар

            result['new_price_items'].append({
                'price_item': row,
                'base_item': item.select_related('deckitem')[0],
                'diff_price': row['barcode']
            })

        if item.count() == 0:  # товар не нашелся (новые элементы)
            result['new_items'].append(row)

        if item.count() > 1:  # товар задублировался??
            result['double_items'].append(row)
            error += u', дубль: (%s, %s)' % (code, article)
            for one_item in item.values():
                id_list.append(one_item['id'])

    result['miss_items'] = Item.objects.filter(deckitem__segment_new__link=segment).exclude(id__in=id_list).exclude(active=False).select_related('deckitem')  # товар есть в базе, нет в прайсе

    return render(request, 'price_parsing_result_barcode.html', {
        'result': result,
        'error': error,
    })
