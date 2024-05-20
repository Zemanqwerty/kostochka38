# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta
import qsstats
from qsstats import QuerySetStats
from qsstats.exceptions import QuerySetStatsError
from catalog.models import Zakaz, InsideZakaz, Segment, WareHouse
from core.models import Account
from django.db.models.aggregates import Count, Sum
from django.db import DatabaseError, transaction
from django.views.decorators.csrf import csrf_exempt


def get_list(query):
    return [round(q[1], 2) for q in query[:-1]]


def process_query(query):
        result = []
        prev = query[0]
        for record in query[1:]:
            data = 100
            if prev != 0:
                data = round((record - prev)/float(prev) * 100, 2)
            if prev == record == 0:
                data = 0
            prev = record
            result.append(data)
        return result


@csrf_exempt
def stat(result, start, end, interval, aggregate, title):
    """
    1. Заказы по всем менеджерам
    """
    series = []
    qs = Zakaz.objects.filter(status=6)
    query = qsstats.QuerySetStats(qs, 'date_end', aggregate).time_series(start, end, interval)
    series.append({
        'name': u'{} завершенных заказов'.format(title),
        'data': get_list(query)
    })

    managers = Account.objects.filter(groups__permissions__codename='manager').values_list('id', flat=True)
    qs_2 = Zakaz.objects.filter(status=6, manager_id__in=managers)
    query_2 = qsstats.QuerySetStats(qs_2, 'date_end', aggregate).time_series(start, end, interval)
    series.append({
        'name': u'%s [менеджеры %s]' % (title, str(managers)),
        'data': get_list(query_2)
    })

    for i in managers:
        qs_3 = Zakaz.objects.filter(status=6, manager_id__in=[i])
        query_3 = qsstats.QuerySetStats(qs_3, 'date_end', aggregate).time_series(start, end, interval)
        manager = Account.objects.get(id=i)
        series.append({
            'name': u'%s [%s %s]' % (title, u"%s %s" % (manager.first_name, manager.last_name), manager.id),
            'data': get_list(query_3)
        })

    result['plot'].append({
        'series': series
    })

    """
    2. Заказы по продавцам 
    """
    sklads = WareHouse.objects.filter(type=1)
    managers = Account.objects.filter(groups__id=3)
    for i in sklads:
        series = []
        for j in managers:
            qs_22 = Zakaz.objects.filter(status=6, cashier=j).exclude(dostavkatype=1)
            query_22 = qsstats.QuerySetStats(qs_22, 'date_end', aggregate).time_series(start, end, interval)
            series.append({
                'name': u'%s [%s] - %s' % (title, i.name, u"%s %s" % (j.first_name, j.last_name)),
                'data': get_list(query_22)
            })

        result['plot'].append({
            'series': series
        })

    """
    3. Заказы по складам 
    """
    series = []
    sklads = WareHouse.objects.all()
    for i in sklads:
        qs = Zakaz.objects.filter(status=6, warehouse=i).exclude(dostavkatype=1)
        query = qsstats.QuerySetStats(qs, 'date_end', aggregate).time_series(start, end, interval)
        series.append({
            'name': u'%s [%s] (-самовывоз)' % (title, i.name),
            'data': get_list(query)
        })

    result['plot'].append({
        'series': series
    })

    series = []
    sklads = WareHouse.objects.all()
    for i in sklads:
        qs = Zakaz.objects.filter(status=6, warehouse=i)
        query = qsstats.QuerySetStats(qs, 'date_end', aggregate).time_series(start, end, interval)
        series.append({
            'name': u'%s [%s] (+самовывоз)' % (title, i.name),
            'data': get_list(query)
        })

    result['plot'].append({
        'series': series
    })

    series = []
    sklads = WareHouse.objects.all()
    for i in sklads:
        qs = Zakaz.objects.filter(status=6, warehouse=i, dostavkatype=1)
        query = qsstats.QuerySetStats(qs, 'date_end', aggregate).time_series(start, end, interval)
        series.append({
            'name': u'%s [%s] (самовывозы)' % (title, i.name),
            'data': get_list(query)
        })

    result['plot'].append({
        'series': series
    })


    """
    4. Заказы по Новый, Старый 
    """
    order_count_query = Account.objects.filter(zakaz__status=6).annotate(order_count=Count('zakaz'))
    qs = Zakaz.objects.filter(status=6).filter(
        owner__in=order_count_query.filter(order_count=1)
    )
    query1 = qsstats.QuerySetStats(qs, 'date_end', aggregate).time_series(start, end, interval)
    qs = Zakaz.objects.filter(status=6).filter(
        owner__in=order_count_query.filter(order_count__gt=1)
    )
    query2 = qsstats.QuerySetStats(qs, 'date_end', aggregate).time_series(start, end, interval)
    result['plot'].append({
        'series': [{
            'name': u'{} первых заказов'.format(title),
            'data': get_list(query1)
        }, {
            'name': u'{} повторных заказов'.format(title),
            'data': get_list(query2)
        }]
    })

    """
    5. Заказы по способу оплаты 
    """
    qs = Zakaz.objects.filter(status=6, paytype=0)
    query1 = qsstats.QuerySetStats(qs, 'date_end', aggregate).time_series(start, end, interval)

    qs = Zakaz.objects.filter(status=6, paytype=1)
    query2 = qsstats.QuerySetStats(qs, 'date_end', aggregate).time_series(start, end, interval)

    qs = Zakaz.objects.filter(status=6, paytype=3)
    query3 = qsstats.QuerySetStats(qs, 'date_end', aggregate).time_series(start, end, interval)

    qs = Zakaz.objects.filter(status=6, paytype=4)
    query4 = qsstats.QuerySetStats(qs, 'date_end', aggregate).time_series(start, end, interval)

    qs = Zakaz.objects.filter(status=6, paytype=5)
    query5 = qsstats.QuerySetStats(qs, 'date_end', aggregate).time_series(start, end, interval)

    qs = Zakaz.objects.filter(status=6, paytype=6)
    query6 = qsstats.QuerySetStats(qs, 'date_end', aggregate).time_series(start, end, interval)

    result['plot'].append({
        'series': [{
            'name': u'{} Наличная оплатой'.format(title),
            'data': get_list(query1)
        }, {
            'name': u'{} Оплатой по карте'.format(title),
            'data': get_list(query2)
        }, {
            'name': u'{} Перевод на карту Сбербанка'.format(title),
            'data': get_list(query3)
        }, {
            'name': u'{} Онлайн оплата'.format(title),
            'data': get_list(query4)
        }, {
            'name': u'{} Расчетный счет'.format(title),
            'data': get_list(query5)
        }, {
            'name': u'{} Смешанный тип'.format(title),
            'data': get_list(query6)
        }]
    })


@csrf_exempt
def dyn_stat(result, start, end, interval, aggregate, title):    
    kwargs = {interval: 1}
    start = start - relativedelta(**kwargs)
    qs = Zakaz.objects.filter(status=6).all()
    query = qsstats.QuerySetStats(qs, 'date_end', aggregate).time_series(start, end, interval)
    result['plot'].append({
        'series': [{
            'name': u'{} завершенных заказов'.format(title),
            'data': process_query(get_list(query))
        }]
    })
    order_count_query = Account.objects.filter(zakaz__status=6).annotate(order_count=Count('zakaz'))
    qs = Zakaz.objects.filter(status=6).filter(
        owner__in=order_count_query.filter(order_count=1)
    ).all()
    query1 = qsstats.QuerySetStats(qs, 'date_end', aggregate).time_series(start, end, interval)
    qs = Zakaz.objects.filter(status=6).filter(
        owner__in=order_count_query.filter(order_count__gt=1)
    )
    query2 = qsstats.QuerySetStats(qs, 'date_end', aggregate).time_series(start, end, interval)
    result['plot'].append({
        'series': [{
            'name': u'{} первых заказов'.format(title),
            'data': process_query(get_list(query1))
        }, {
            'name': u'{} повторных заказов'.format(title),
            'data': process_query(get_list(query2))
        }]
    })


intervals = [
    (datetime(2019, 1, 1), datetime(2019, 1, 27)),
    (datetime(2019, 1, 28), datetime(2019, 2, 24)),
    (datetime(2019, 2, 25), datetime(2019, 3, 24)),
    (datetime(2019, 3, 25), datetime(2019, 4, 21)),
    (datetime(2019, 4, 22), datetime(2019, 5, 19)),
    (datetime(2019, 5, 20), datetime(2019, 6, 16)),
    (datetime(2019, 6, 17), datetime(2019, 7, 14)),
    (datetime(2019, 7, 15), datetime(2019, 8, 11)),
    (datetime(2019, 8, 12), datetime(2019, 9, 8)),
    (datetime(2019, 9, 9), datetime(2019, 10, 6)),
    (datetime(2019, 10, 7), datetime(2019, 11, 3)),
    (datetime(2019, 11, 4), datetime(2019, 12, 31))
]


@csrf_exempt
def rc_intervals_stat(qs, date_field, aggregate):
    result = []
    for interval in intervals:
        if interval[0] > datetime.now():
            break
        kwargs = {'%s__range' % date_field: interval}
        query = qs.filter(**kwargs).aggregate(agg=aggregate)
        val = 0
        if query['agg']:
            val = query['agg']
        result.append(round(val, 2))
    return result


@csrf_exempt
def stat_inside(result, start, end, interval, aggregate=Sum('cost'), title=u'Сумма', dyn=False):
    if dyn:
        kwargs = {interval: 1}
        start = start - relativedelta(**kwargs)
    qs = InsideZakaz.objects.filter(status=6).all()
    query = get_list(qsstats.QuerySetStats(qs, 'date_end', aggregate).time_series(start, end, interval))

    managers = Account.objects.filter(groups__permissions__codename='manager').values_list('id', flat=True)
    qs_2 = InsideZakaz.objects.filter(status=6, manager_id__in=managers).all()
    query_2 = qsstats.QuerySetStats(qs_2, 'date_end', aggregate).time_series(start, end, interval)

    result['plot'].append({
        'series': [{
            'name': u'{} всех поставщиков'.format(title),
            'data': process_query(query) if dyn else query
        }, {
            'name': u'%s [менеджеры %s]' % (title, str(managers)),
            'data': get_list(query_2)
        }]
    })

    series = []
    for i in managers:
        qs_3 = InsideZakaz.objects.filter(status=6, manager_id__in=[i]).all()
        query_3 = qsstats.QuerySetStats(qs_3, 'date_end', aggregate).time_series(start, end, interval)
        manager = Account.objects.get(id=i)
        series.append({
            'name': u'%s [%s %s]' % (title, u"%s %s" % (manager.first_name, manager.last_name), manager.id),
            'data': get_list(query_3)
        })

    result['plot'].append({
        'series': series
    })

    series = []
    segments = Segment.objects.filter(in_statistics=True)

    for i in segments:
        qs = InsideZakaz.objects.filter(status=6, segment_new=i)
        query = get_list(qsstats.QuerySetStats(qs, 'date_end', aggregate).time_series(start, end, interval))
        series.append({
            'name': u'{0} {1}'.format(title, i.title),
            'data': process_query(query) if dyn else query
        })

    result['plot'].append({
        'series': series
    })

    for i in segments:
        qs = InsideZakaz.objects.filter(status=6, segment_new=i)
        query = get_list(qsstats.QuerySetStats(qs, 'date_end', aggregate).time_series(start, end, interval))
        result['plot'].append({
            'series': [{
                'name': u'{0} {1}'.format(title, i.title),
                'data': process_query(query) if dyn else query
            }]
        })
