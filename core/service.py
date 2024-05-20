# -*- coding: utf-8 -*-
import json

from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.aggregates import Count, Avg
from django.http.response import HttpResponse
from django.template import RequestContext, loader, Context
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from reversion.models import Version, Revision

from news.models import *
from catalog.models import *
from core.stat import stat, dyn_stat, stat_inside

from dateutil.relativedelta import relativedelta
import xlrd
import xlsxwriter
import datetime
from pytils import dt


@staff_member_required
def addkupidelivety(request):
    new_order = OutsideZakaz(
        summ=0,
        zakaz_id=request.GET['id'],
        store=2,
        status=2,
        paid_client=True,
        desired_time=request.GET['dtame'],
        phone=request.GET['phone'],
        fio=request.GET['customer'],
        city=request.GET['city'],
        street=request.GET['street'],
        dom=request.GET['home'],
        appart=request.GET['flat'],
    )
    new_order.save()
    return HttpResponseRedirect('/DgJrfdJg/catalog/outsidezakaz/%s/' % new_order.id)


@staff_member_required
def autozakaz(request, segment):
    suppliers = {'purina': 0, 'royal': 1, 'avrora': 2}
    zakazs = InsideZakaz.objects.filter(supplier=suppliers[segment], status=0).order_by('-date')
    if zakazs.count() > 0:
        zakaz = InsideZakaz.objects.get(id=zakazs.values()[0]['id'])
    else:
        zakaz = InsideZakaz(
            cost=0,
            status=0,
            supplier=suppliers[segment],
        )
        zakaz.save()

    items = Item.objects.filter(active=True, deckitem__segment=segment, minimum_need__gt=0).values()
    for item in items:
        if item['quantity_in_reserve'] < item['minimum_need']:
            count = 0
            coef = 1
            if item['count_for_zakaz'] < 1:
                count = item['minimum_need']
            else:
                while count == 0:
                    if (int(item['quantity_in_reserve']) + int(item['count_for_zakaz']) * coef) >= item['minimum_need']:
                        count = int(item['count_for_zakaz']) * coef
                        break
                    else:
                        coef += 1
                        continue
            new_line = InsideZakazGoods(
                zakaz=zakaz,
                item_id=item['id'],
                quantity=count,
                cost=item['real_price'] * count,
                action=item.get_action_online() or None
            )
            new_line.save()

    return HttpResponseRedirect('/DgJrfdJg/catalog/insidezakaz/%s' % zakaz.id)


MONTH_DICT = {
    1: u'Янв', 2: u'Фев', 3: u'Март', 4: u'Апр', 5: u'Май', 6: u'Июнь', 7: u'Июль', 8: u'Авг', 9: u'Сен', 10: u'Окт',
    11: u'Ноя', 12: u'Дек'
}


def test_permission(request):
    """
     36 - Саша
     142 - Рома Некрасов
     678 - Настя Некрасова

     2592 - Настя Балясникова
     2944 - Мария Силинских
     486 - Ермакова Евгения
     1608 - Лисинова Маргарита
     2971 - Юлия Шелепова
     3015 - Мария Кондратюк

     3272 - Анастасия Прокопчук
     3842 - Оля Ермакова

     3958 - Марков Данил

    """
    if request.user.id in [1, 36, 142, 678, 3272, 3842]:
        return True
    return False


@csrf_exempt
@staff_member_required
def check_zakaz_state(request):
    result = {'response': 0, 'notequal': {}}
    object_id = request.POST.get('object_id')
    content_type_id = request.POST.get('content_type_id')
    load_date = request.POST.get('load_date')

    if object_id and content_type_id and load_date:
        last_version = Version.objects.filter(object_id=object_id, content_type=content_type_id).select_related(
            'revision').order_by('-revision__date_created').values()
        if last_version:
            version_data = Revision.objects.filter(id=last_version[0]['revision_id']).first()
            if version_data:
                if version_data.date_created > datetime.datetime.strptime(load_date, "%Y-%m-%d %H:%M:%S"):
                    result['response'] = 1
                    result['version_date_created'] = version_data.date_created.strftime("%M %d %Y, %H:%M:%S")

                    if version_data.user:
                        result['version_user'] = version_data.user.username

                    result['comment'] = version_data.comment

    return HttpResponse(json.dumps(result), content_type='application/javascript')


@csrf_exempt
@staff_member_required
def sr(request, month_count=12):
    month_count = int(month_count)
    now_month = datetime.datetime.now().month + 1
    now_year = datetime.datetime.now().year
    result = []
    all_types = ExpenseType.objects.all()

    real = False
    if request.GET.get('real'):
        real = True

    for i in range(month_count):
        now_month -= 1

        if now_month == 0:
            now_month = 12
            now_year -= 1

        if real:
            expensies = Expense.objects.filter(date__month=now_month, date__year=now_year, source=0).exclude(expensetype__id__in=[4, 16, 18, 19])
        else:
            expensies = Expense.objects.filter(date__month=now_month, date__year=now_year)
        # EXPENSE_TYPE = (
        #     (0, u'Расход'),
        #     (1, u'Доход'),
        # )

        minus_detail = expensies.filter(type=0)

        temp_detail_result = []
        for j in all_types.values():
            detail_result = minus_detail.filter(expensetype=j['id'])
            detail_result_sum = detail_result.aggregate(sum=Sum('value'))['sum']
            if detail_result_sum:
              temp_detail_result.append(
                    {
                        'title': j['title'],
                        'sum': detail_result_sum
                    }
                )
        real_poducer_sum = 0
        if real:
            real_poducer_sum = Zakaz.objects.filter(date_end__month=now_month, date_end__year=now_year).aggregate(sum=Sum('cost'))['sum']
            if not real_poducer_sum:
                real_poducer_sum = 0
            temp_detail_result.append(
                {
                    'title': u'Закуп проданного товара',
                    'sum': -real_poducer_sum
                }
            )

        minus = 0
        if expensies.filter(type=0).aggregate(sum=Sum('value'))['sum']:
            minus = expensies.filter(type=0).aggregate(sum=Sum('value'))['sum']

        plus = 0
        if expensies.filter(type=1).exclude(expensetype__id=3).aggregate(sum=Sum('value'))['sum']:
            plus = expensies.filter(type=1, source=0).exclude(expensetype__id=3).aggregate(sum=Sum('value'))['sum']

        temp_result = {
            'date': '%s.%s' % (now_month, now_year),
            'minus': minus - real_poducer_sum,
            'detail_result': temp_detail_result,
            'plus': plus,
            'revenue': plus + (minus - real_poducer_sum)
        }
        result.append(temp_result)

    response = render(request, 'admin_module/super_report.html', locals())
    response['Cache-Control'] = 'no-cache, must-revalidate'
    return response


@csrf_exempt
@staff_member_required
def statistics(request):
    if not test_permission(request):
        return HttpResponseRedirect('/DgJrfdJg/')

    if not request.user.is_superuser:
        return HttpResponseRedirect('/DgJrfdJg/')

    if request.method == 'POST':
        count = int(request.POST.get('count', '4'))
        typ = int(request.POST.get('type', '1'))
        end = datetime.datetime.now() + relativedelta(months=count - 1)
        start = end - relativedelta(months=count)
        if request.POST.get('end'):
            end = datetime.datetime.strptime(request.POST.get('end'), '%m/%d/%Y')
            if typ:
                end = datetime.datetime(end.year, end.month, 1) + relativedelta(months=1)
                start = end - relativedelta(months=count)
            else:
                end = end + datetime.timedelta(days=(7 - start.weekday()))
                start = end - relativedelta(weeks=count)
        if typ:
            interval = 'months'
            categories_format = '%b %Y'
            intervals = [start + relativedelta(months=i) for i in range(count)]
        else:
            interval = 'weeks'
            categories_format = '%W %d %b %Y'
            intervals = [start + relativedelta(weeks=i) for i in range(count)]
        block = request.POST.get('block')
        result = {'plot': [], 'selector': block, 'categories': [date.strftime(categories_format) for date in intervals]}
        if block == "order_sum":
            stat(result, start, end, interval, Sum('summ'), u'S')
        elif block == "order_sum_real_sum":
            stat(result, start, end, interval, Sum('real_sum'), u'[-sale] S')
        elif block == "order_count":
            stat(result, start, end, interval, Count('id'), u'Кол-во')
        elif block == "avg_sum":
            stat(result, start, end, interval, Avg('summ'), u'Средний чек')
        elif block == "order_sum_dyn":
            dyn_stat(result, start, end, interval, Sum('summ'), u'Процент роста суммы')
        elif block == "order_count_dyn":
            dyn_stat(result, start, end, interval, Count('id'), u'Процент роста кол-ва')
        elif block == "order_sum_supplier":
            stat_inside(result, start, end, interval)
        elif block == "order_count_supplier":
            stat_inside(result, start, end, interval, Count('id'), u'Кол-во заказов')
        elif block == "order_sum_supplier_dyn":
            stat_inside(result, start, end, interval, title=u'Динамика роста', dyn=True)
        response = HttpResponse(json.dumps(result, cls=DjangoJSONEncoder), content_type='application/json')
        response['Cache-Control'] = 'no-cache, must-revalidate'
        return response

    response = render(request, 'admin_module/grafics.html', {})
    response['Cache-Control'] = 'no-cache, must-revalidate'
    return response


@staff_member_required
def balans(request):
    if not test_permission(request):
        return HttpResponseRedirect('/DgJrfdJg/')

    segments_objects = Segment.objects.filter(in_balans=True)

    sum_balans = 0
    for i in segments_objects:
        sum_balans += i.get_balans()

    result = {}
    full_view = False
    warehouses = WareHouse.objects.all()
    if request.user.id == 1 or request.user.id == 142 or request.user.id == 678 or request.user.id == 36 or request.user.id == 3958:
        full_view = True
        sum_all = 0
        count_all = 0
        for i in segments_objects:
            i.count = i.get_item_count()
            count_all += i.count
            i.sum = i.get_items_sum()
            sum_all += i.sum

        result['kassa_nal'] = Expense.objects.filter(source=0, type_of_currency=0).aggregate(nal=Sum('value'))
        result['kassa_beznal'] = Expense.objects.filter(source=0, type_of_currency=1).aggregate(beznal=Sum('value'))
        if not result['kassa_beznal']['beznal']:
            result['kassa_beznal']['beznal'] = 0
        result['kassa'] = result['kassa_nal']['nal'] + result['kassa_beznal']['beznal']

        result['expens_vladimir'] = Expense.objects.filter(source=1).aggregate(sum=Sum('value'))
        if not result['expens_vladimir']['sum']:
            result['expens_vladimir']['sum'] = 0
        result['expens_roman'] = Expense.objects.filter(source=2).aggregate(sum=Sum('value'))
        if not result['expens_roman']['sum']:
            result['expens_roman']['sum'] = 0
        result['expens_sum'] = result['expens_vladimir']['sum'] + result['expens_roman']['sum']

    response = render(request, 'admin_module/current_balans.html', locals())
    response['Cache-Control'] = 'no-cache, must-revalidate'
    return response


def count_and_summ_item(items):
    count = 0
    summ = 0
    for item in items:
        count += item['quantity_in_reserve']
        summ += item['quantity_in_reserve'] * item['real_price']

    return count, summ


@staff_member_required
def get_lost_users(request):
    all_users = Account.objects.filter(is_active=True)

    user_count = 1
    for user in all_users.values():
        user_orders = Zakaz.objects.filter(owner=user['id'], status=6).order_by('date_end')

        if user_orders.count() > 2:

            # print('----------------')
            # print('order_count %s' % user_orders.count())

            iteration_numner = 1
            sum_date = 0
            prev_date = datetime.datetime.now()
            min_range = 99999
            max_range = 0
            mediana_for_order = 0
            for order in user_orders.values():
                if iteration_numner == 1:
                    pass
                else:
                    date_range = (order['date_end'] - prev_date).days

                    if date_range > max_range:
                        max_range = date_range
                    if date_range < min_range:
                        min_range = date_range

                    sum_date += date_range

                iteration_numner += 1
                prev_date = order['date_end']

            average_date_for_order = sum_date / (user_orders.count() - 1)

            if user_orders.count() > 6:
                mediana_for_order = (sum_date - max_range - min_range) / (user_orders.count() - 3)

            days_to_last_order = (datetime.datetime.now() - order['date_end']).days

            # print('avvarage - %s, mediana - %s, days_to_last_order - %s' % (average_date_for_order, mediana_for_order, days_to_last_order))
            # print('min_range - %s, max_range - %s' % (min_range, max_range))

            average_for_formula = average_date_for_order
            if mediana_for_order > 0:
                average_for_formula = mediana_for_order

            if average_for_formula * 2 < days_to_last_order and not LostUser.objects.filter(user=user['id'],
                                                                                            need_again=False).exists():
                new_lost_user = LostUser(
                    user_id=user['id'],
                    order_count=user_orders.count(),
                    average=average_date_for_order,
                    mediana=mediana_for_order,
                    last_order=days_to_last_order,
                )
                new_lost_user.save()

    return HttpResponseRedirect('/DgJrfdJg/core/lostuser/')


@staff_member_required
def inventory(request, type=False):
    path = settings.BASE_DIR

    if not test_permission(request):
        return HttpResponseRedirect('/DgJrfdJg/')

    margin = {1: 1.1, 2: 1.05, 3: 1.15, 4: 1.25}

    i = 3
    today = datetime.datetime.now()
    new_filename = 'inventory_%s%s%s_%s%s.xlsx' % (today.year, today.month, today.day, today.hour, today.minute)

    # Create an new Excel file and add a worksheet.
    workbook = xlsxwriter.Workbook(path + "/static/" + new_filename)
    ws = workbook.add_worksheet()
    ws.set_column('A:A', 8)
    ws.set_column('B:B', 16)
    ws.set_column('C:C', 100)
    ws.set_column('D:D', 10)
    ws.set_column('G:G', 15)
    ws.set_column('F:F', 15)

    cell_format = workbook.add_format({'bold': True})

    ws.write('A1', u'Артикул')
    ws.write('B1', u'Производитель')
    ws.write('C1', u'Название')
    ws.write('D1', u'Картинка')
    ws.write('E1', u'Тип')
    ws.write('F1', u'Остаток на складе')
    # ws.write('H4', u'У поставщика')
    ws.set_row(3, 20, cell_format)

    categories = Tag.objects.filter(deckitem__producer__active=True).distinct().order_by('section', 'sort', 'title')

    warehouses = WareHouse.objects.all()

    for warehouse in warehouses:

        ws.write('C%s' % i, warehouse.name)
        i += 1

        for category in categories.values():
            category = Tag.objects.get(id=category['id'])

            items = Item.objects.filter(active=True, deckitem__active=True, deckitem__producer__active=True, deckitem__tag=category.id).distinct().exclude(availability=0).values()

            ws.write('C%s' % i, '%s %s' % (category.title, category.get_section_display()))
            ws.set_row(i - 1, 25, cell_format)
            i += 1

            for item in items:
                item = Item.objects.get(id=item['id'])

                left = 0
                if LeftItem.objects.filter(item=item, warehouse=warehouse).exists():
                    left = LeftItem.objects.filter(item=item, warehouse=warehouse).first().left

                if left > 0:

                    ws.write('A%s' % i, item.id)
                    ws.write('B%s' % i, item.deckitem.producer.title)
                    ws.write('C%s' % i, item.deckitem.title)
                    if item.deckitem.cover():
                        image_name = item.deckitem.cover()[0].cart_thumbnail.url.split('.')
                        if image_name[-1] != 'gif' and image_name[-1] != 'GIF':
                            ws.set_row(i - 1, 40)
                            ws.insert_image('D%s' % i, path + item.deckitem.cover()[0].cart_thumbnail.url, {'x_offset': 10, 'y_offset': 2})
                    ws.write('E%s' % i, item.weight)
                    ws.write('F%s' % i, left)
                    i += 1
            i += 1


    workbook.close()

    return HttpResponseRedirect("/static/" + new_filename)


@staff_member_required
def royal_report(request, type=False):
    path = settings.BASE_DIR

    if not test_permission(request):
        return HttpResponseRedirect('/DgJrfdJg/')

    margin = {1: 1.1, 2: 1.05, 3: 1.15, 4: 1.25}

    i = 2
    today = datetime.datetime.now()
    new_filename = 'royal_report_%s%s%s_%s%s.xlsx' % (today.year, today.month, today.day, today.hour, today.minute)

    # Create an new Excel file and add a worksheet.
    workbook = xlsxwriter.Workbook(path + "/static/" + new_filename)
    ws = workbook.add_worksheet()
    ws.set_column('A:A', 8)
    ws.set_column('B:B', 16)
    ws.set_column('C:C', 16)
    ws.set_column('D:D', 10)
    ws.set_column('G:G', 15)
    ws.set_column('F:F', 15)

    cell_format = workbook.add_format({'bold': True})

    ws.write('A1', u'id')
    ws.write('B1', u'Наименование')
    ws.write('C1', u'Цена закуп')
    ws.write('D1', u'Цена - скидка')
    ws.write('E1', u'Сумма скидки')
    ws.write('F1', u'Кол-во')
    ws.write('G1', u'Сумма компенсации')

    start_date = datetime.datetime(2020,11,23,0,0,0,0)
    end_date = datetime.datetime(2020,12,6,23,59,0,0)

    zakazs = Zakaz.objects.filter(status=6, date__gte=start_date, date__lte=end_date)

    for zakaz in zakazs:

        items = ZakazGoods.objects.filter(zakaz=zakaz, item__deckitem__producer__id=16)

        for item in items:
            sale_d = float(100 - item.sale)/100
            sale_e = float(1) - sale_d
            ws.write('A%s' % i, item.item.id)
            ws.write('B%s' % i, item.item.deckitem.title)
            ws.write('C%s' % i, item.item.real_price)
            ws.write('D%s' % i, item.item.real_price * sale_d)
            ws.write('E%s' % i, item.item.real_price * sale_e)
            ws.write('F%s' % i, item.quantity)
            ws.write('G%s' % i, item.quantity*item.item.real_price * sale_e)
            i += 1

    workbook.close()

    return HttpResponseRedirect("/static/" + new_filename)


@staff_member_required
def export_to_xls(request, type=False):
    path = settings.BASE_DIR

    if not test_permission(request):
        return HttpResponseRedirect('/DgJrfdJg/')

    margin = {
        1: 1.1,
        2: 1.05,
        3: 1.15,
        4: 1.25
    }

    korm = [1, 5, 12, 13, 14, 15]
    napolnitel = 7

    today = datetime.datetime.now()

    if type == 'opt' or not type:
        new_filename = 'kostochka38_%s%s%s_%s%s_opt.xlsx' % (
        today.year, today.month, today.day, today.hour, today.minute)
    elif type == 'zavodchik':
        new_filename = 'kostochka38_%s%s%s_%s%s_pitomnik.xlsx' % (
        today.year, today.month, today.day, today.hour, today.minute)

    i = 5

    # Create an new Excel file and add a worksheet.
    workbook = xlsxwriter.Workbook(path + "/static/" + new_filename)
    ws = workbook.add_worksheet()
    ws.set_column('A:A', 8)
    ws.set_column('B:B', 16)
    ws.set_column('C:C', 100)
    ws.set_column('D:D', 10)
    ws.set_column('G:G', 15)
    ws.set_column('H:H', 15)

    cell_format = workbook.add_format({'bold': True})

    ws.write('C2', u'Kostochka38.ru')
    ws.write('B2', u'%s' % (dt.ru_strftime(u"%d %B %Y", today, inflected=True)))

    ws.write('A4', u'Артикул')
    ws.write('B4', u'Производитель')
    ws.write('C4', u'Название')
    ws.write('D4', u'Картинка')  # worksheet.insert_image('B2', 'python.png')
    ws.write('E4', u'Тип')
    ws.write('F4', u'Цена')
    ws.write('G4', u'Остаток на складе')
    # ws.write('H4', u'У поставщика')
    ws.set_row(3, 20, cell_format)

    if type == 'opt' or not type:
        categories = Tag.objects.filter(deckitem__producer__active=True,
                                        deckitem__producer__margin_opt__gt=0).distinct().order_by('section', 'sort',
                                                                                                  'title')
    elif type == 'zavodchik':
        categories = Tag.objects.filter(deckitem__producer__active=True,
                                        deckitem__producer__margin_zavodchiki__gt=0).distinct().order_by('section',
                                                                                                         'sort',
                                                                                                         'title')

    for category in categories.values():
        category = Tag.objects.get(id=category['id'])

        if type == 'opt' or not type:
            items = Item.objects.filter(active=True, deckitem__active=True, deckitem__producer__active=True,
                                        deckitem__producer__margin_opt__gt=0,
                                        deckitem__tag=category.id).distinct().exclude(availability=0).values()

        elif type == 'zavodchik':
            items = Item.objects.filter(active=True, deckitem__active=True, deckitem__producer__active=True,
                                        deckitem__producer__margin_zavodchiki__gt=0,
                                        deckitem__tag=category.id).distinct().exclude(availability=0).values()
        else:
            continue

        ws.write('C%s' % i, '%s %s' % (category.title, category.get_section_display()))
        ws.set_row(i - 1, 25, cell_format)
        i += 1

        for item in items:
            item = Item.objects.get(id=item['id'])

            ws.write('A%s' % i, item.id)
            ws.write('B%s' % i, item.deckitem.producer.title)
            ws.write('C%s' % i, item.deckitem.title)
            if item.deckitem.cover():
                image_name = item.deckitem.cover()[0].cart_thumbnail.url.split('.')
                if image_name[-1] != 'gif' and image_name[-1] != 'GIF':
                    ws.set_row(i - 1, 40)
                    ws.insert_image('D%s' % i, path + item.deckitem.cover()[0].cart_thumbnail.url,
                                    {'x_offset': 10, 'y_offset': 2})
            ws.write('E%s' % i, item.weight)

            if type == 'opt' or not type:
                ws.write_number('F%s' % i, item.current_price_opt())
            elif type == 'zavodchik':
                ws.write_number('F%s' % i, item.current_price_zavodchik())
            else:
                ws.write_number('F%s' % i, item.current_price_opt())

            ws.write('G%s' % i, item.quantity_in_reserve)
            # ws.write('H%s' % i, item.quantity_in_stock)
            i += 1
        i += 1
    workbook.close()

    return HttpResponseRedirect("/static/" + new_filename)


@csrf_exempt
def put_statistics(request):
    try:
        if request.user.is_authenticated and request.user.is_staff:
            pass
        else:
            filter_element = Filter.objects.get(id=request.POST.get('id'))
            filter_element.view += 1
            filter_element.save()
    except:
        pass

    response = HttpResponse(json.dumps(1), content_type='application/javascript')
    response['Cache-Control'] = 'no-cache, must-revalidate'
    return response


def deactivate_deckitems(request):
    deckitems = Deckitem.objects.filter(active=True).values()
    deactivated = []

    for deckitem in deckitems:
        this_deckitem = Deckitem.objects.get(id=deckitem['id'])
        items_count = Item.objects.filter(deckitem=this_deckitem.id, active=True).count()
        if items_count == 0:
            this_deckitem.active = False
            this_deckitem.save()
            deactivated.append(this_deckitem)

    response = render(request, 'service/deactivate-deckitems.html', locals())
    response['Cache-Control'] = 'no-cache, must-revalidate'
    return response


def deckitems_availability(request):
    deckitems = Deckitem.objects.filter(active=True).values()
    deactivated = []
    activated = []

    for deckitem in deckitems:
        this_deckitem = Deckitem.objects.get(id=deckitem['id'])
        items_count = Item.objects.filter(deckitem=this_deckitem.id, active=True).exclude(availability=0).count()
        if items_count == 0:
            this_deckitem.availability = 0
            this_deckitem.save()
            deactivated.append(this_deckitem)
        else:
            this_deckitem.availability = 3
            this_deckitem.save()
            activated.append(this_deckitem)

    response = render(request, 'service/deactivate-deckitems.html', locals())
    response['Cache-Control'] = 'no-cache, must-revalidate'
    return response


def deckitems_activate(request):
    deckitems = Deckitem.objects.filter(active=False).values()
    deactivated = []
    activated = []

    for deckitem in deckitems:
        this_deckitem = Deckitem.objects.get(id=deckitem['id'])
        items_count = Item.objects.filter(deckitem=this_deckitem.id, active=True).count()
        if items_count > 0:
            this_deckitem.active = True
            this_deckitem.save()
            activated.append(this_deckitem)

    response = render(request, 'service/deactivate-deckitems.html', locals())
    response['Cache-Control'] = 'no-cache, must-revalidate'
    return response


def calculate_price(request):
    items = Item.objects.filter(active=True, deckitem__active=True)

    for i in items:
        i.sort_price = i.current_price()
        i.save()

    response = render(request, 'service/items.html', locals())
    response['Cache-Control'] = 'no-cache, must-revalidate'
    return response


def check_availibility_status_date(request):
    result = []
    items = Item.objects.filter(active=True, availability=0)
    for i in items:
        availibility_date = datetime.datetime.now() - datetime.timedelta(days=180)
        if ItemAvailabilityLog.objects.filter(item=i.id).order_by('-date').exists():
            item_avalability_logs = ItemAvailabilityLog.objects.filter(item=i.id).order_by('-date')[0]
            if item_avalability_logs.date <= availibility_date and item_avalability_logs.availability == 0:
                result.append(i)
                i.active = False
                i.save()
    Deckitem.objects.exclude(
        id__in=Item.objects.filter(active=True).values_list('deckitem_id', flat=True)
    ).update(active=False)

    response = render(request, 'service/new_items_availibility_status_log.html', locals())
    response['Cache-Control'] = 'no-cache, must-revalidate'
    return response


def check_availibility_status_date_fix(request):
    result = []
    deckitems = Deckitem.objects.filter(active=False)

    for i in deckitems:
        items = Item.objects.filter(deckitem=i.id).values_list('id')
        logs = ReserveLog.objects.filter(item__id__in=items).order_by('-date')
        if logs:
            last_date = logs[0].date
            i.last_date = last_date
            availibility_date = datetime.datetime.now() - datetime.timedelta(days=180)
            if last_date >= availibility_date:
                result.append(i)

    response = render(request, 'service/new_items_availibility_status_log_fix.html', locals())
    response['Cache-Control'] = 'no-cache, must-revalidate'
    return response


def kill_kronos_service(request):
    deckitems = Deckitem.objects.filter(segment='kronos')

    for i in deckitems:
        Item.objects.filter(deckitem=i.id).update(active=False, availability=0)
        ItemPhoto.objects.filter(deckitem=i.id).delete()

    deckitems = Deckitem.objects.filter(segment='dogservice').update(active=False, availability=0)
    response = render(request, 'service/new_items_availibility_status_log_fix.html', locals())
    response['Cache-Control'] = 'no-cache, must-revalidate'
    return response


def calculate_revenue(request):
    zakaz_objects = Zakaz.objects.filter(status=6, date_end__gte=(datetime.datetime.now() - datetime.timedelta(days=224)))

    for zakaz in zakaz_objects:
        zakaz_revenue = 0

        zakaz_goods = ZakazGoods.objects.filter(zakaz=zakaz)

        for i in zakaz_goods:
            sale = SaleTable.objects.filter(segment_new=i.item.deckitem.segment_new).order_by('-date')[0:1]
            if not sale:
                sale = 1
            else:
                sale = sale[0].value
            cost = i.item.real_price * i.quantity * sale
            zakaz_revenue += cost

        zakaz.cost = zakaz_revenue
        zakaz.save()

    response = render(request, 'service/new_items_availibility_status_log_fix.html', locals())
    response['Cache-Control'] = 'no-cache, must-revalidate'
    return response


def show_revenue(request):
    zakaz_objects = Zakaz.objects.filter(status=6, date_end__gte=(datetime.datetime.now() - datetime.timedelta(days=93)))

    for zakaz in zakaz_objects:
        zakaz_revenue = 0

        zakaz_goods = ZakazGoods.objects.filter(zakaz=zakaz)

        for i in zakaz_goods:
            sale = SaleTable.objects.filter(segment_new=i.item.deckitem.segment_new).order_by('-date')[0:1]
            cost = i.item.real_price * i.quantity * sale[0].value
            zakaz_revenue += cost

        zakaz.revenue = zakaz_revenue
        zakaz.save()

    response = render(request, 'service/new_items_availibility_status_log_fix.html', locals())
    response['Cache-Control'] = 'no-cache, must-revalidate'
    return response


def facebook_xml(request):
    """
    returns an XML of the most latest posts
    """
    items = Item.objects.filter(active=True, deckitem__active=True).exclude(availability=0)

    t = loader.get_template('facebook/feed.xml')
    c = Context(
        {'items': items}
    )

    return HttpResponse(t.render(c), content_type="text/xml")
