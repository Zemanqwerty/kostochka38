# -*- coding: utf-8 -*-
import hashlib
import random
import json
import re
import cgi
import math
import ssl
import urllib
import logging
from collections import defaultdict

from reversion import revisions as reversion
from captcha import conf
from captcha.models import CaptchaStore
from django.db import transaction

from catalog.utils import shipping
from django.urls import reverse
from django.http.response import Http404
from django.db.models.aggregates import Count
from django.utils.encoding import force_str
from django.utils import timezone
from django.db.models import Sum, Q, ExpressionWrapper, BooleanField
# import sx.pisa3 as pisa
from xhtml2pdf import pisa
from xhtml2pdf.files import getFile, pisaFileObject
from io import StringIO
from django.template import RequestContext, loader, Context
from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect
from django.shortcuts import redirect, get_object_or_404, render
from django import forms
from django.conf import settings
from captcha.fields import CaptchaField
from django.contrib import auth
from django.core.mail import send_mail
from django.template.loader import render_to_string, get_template
from django.db.models import Max, Min, Prefetch

from sklad.models import Duty, Encashment
from catalog.models import *
from core.models import Menu, Static
from core.views import is_valid_email
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.models import LogEntry, CHANGE, ContentType
import datetime
import dateutil.parser
from django.db.models import Q
from django.contrib import messages

logger = logging.getLogger(__name__)


class CommentForm(forms.Form):
    captcha = CaptchaField()


class RegistrationForm(forms.Form):
    captcha = CaptchaField()


def intspace(value):
    orig = force_str(value)
    new = re.sub("^(-?\d+)(\d{3})", '\g<1> \g<2>', orig)
    if orig == new:
        return new
    else:
        return intspace(new)


def view_redirect(request, end_path, path):
    if end_path:
        get_request = ''
        if request.META['QUERY_STRING']:
            get_request = '?' + request.META['QUERY_STRING']
        return HttpResponsePermanentRedirect(path + end_path + '/' + get_request)
    else:
        return HttpResponsePermanentRedirect(path)


def view_item_review_add_complete_redirect(request, category_link, item_link):
    item = get_object_or_404(Deckitem, id=item_link, active=1)
    return HttpResponsePermanentRedirect(item.get_absolute_url())


def view_item_redirect(request, category_link, item_link):
    item = get_object_or_404(Deckitem, id=item_link, active=1)
    get_request = ''
    if request.META['QUERY_STRING']:
        get_request = '?' + request.META['QUERY_STRING']
    return HttpResponsePermanentRedirect(item.get_absolute_url() + get_request)


def catalog_view(request):
    flatpage = get_object_or_404(Static, link='catalog_main')
    current_link = 'c'

    menu_catalog = {'food': []}

    menu_catalog['food'].append({
        'title': u'Для собак',
        'class': 'dlya-sobak',
        'items': Tag.objects.filter(section='dlya-sobak').order_by('sort'),
        'id': 'dog'
    })

    menu_catalog['food'].append({
        'title': u'Для кошек',
        'class': 'dlya-koshek',
        'items': Tag.objects.filter(section='dlya-koshek').order_by('sort'),
        'id': 'cat'
    })

    menu_catalog['food'].append({
        'title': u'Для грызунов',
        'class': 'dlya-gryzunov-i-harkov',
        'items': Tag.objects.filter(section='dlya-gryzunov-i-harkov').order_by('sort'),
        'id': 'rat'
    })

    menu_catalog['food'].append({
        'title': u'Для птиц',
        'class': 'dlya-ptiz',
        'items': Tag.objects.filter(section='dlya-ptiz').order_by('sort'),
        'id': 'bird'
    })

    menu_catalog['food'].append({
        'title': u'Для рыбок',
        'class': 'dlya-rybok',
        'items': Tag.objects.filter(section='dlya-rybok').order_by('sort'),
        'id': 'fish'
    })

    menu_catalog['food'].append({
        'title': u'Для рептилий',
        'class': 'dlya-reptiliy',
        'items': Tag.objects.filter(section='dlya-reptiliy').order_by('sort'),
        'id': 'snake'
    })

    response = render(request, 'view_catalog.html', locals())
    response['Cache-Control'] = 'no-cache, must-revalidate'
    return response


def view_item_review_add_complete(request, item_link):
    item = Deckitem.objects.get(link=item_link)
    current_link = 'c'

    producer = ''
    if 'producer' in request.GET:
        producer = get_object_or_404(Producer, link=request.GET['producer'])
        submenu_active = request.GET['producer']

    response = render(request, 'view_review_add_complete.html', locals())
    response['Cache-Control'] = 'no-cache, must-revalidate'
    return response


def view_item(request, item_link):
    #  проверка на товар снятый с производства
    check_nonactive = Deckitem.objects.filter(link=item_link, active=0).count()
    if check_nonactive == 1:
        item = get_object_or_404(Deckitem, link=item_link, active=0)
        return HttpResponsePermanentRedirect('/c/%s/' % item.tag.link)
    # конец проверки

    item = get_object_or_404(Deckitem, link=item_link, active=1)
    if Item.objects.filter(deckitem=item.id, active=1).count() == 0:
        raise Http404

    category = item.tag

    # увеличим количество просмотров товара на 1
    item.views += 1
    item.save()

    # tracker = ViewTracker(request.user)
    # tracker.mark_instance_viewed(item)

    use_canonical = False

    if item.type:
        item.type = ITEM_TYPE_DICT[item.type]

    try:
        if 'c' in request.GET:
            category = Tag.objects.get(id=request.GET['c'])
    except:
        return HttpResponseRedirect(item.get_absolute_url())
    submenu_active = category.link

    producer = ''
    submenu_producer_active = ''

    filters = item.filters.all()

    if 'producer' in request.GET:
        producer = get_object_or_404(Producer, link=request.GET['producer'])
        submenu_active = request.GET['producer']
        use_canonical = True

    comments = Commentitem.objects.filter(deckitem=item.id, status='2').order_by('date').values()

    active_item = None
    item_id = request.GET.get('item_id')
    if item_id is not None:
        active_item = Item.objects.get(id=item_id)

    # работа с отзывами, вывод и добавление
    form = CommentForm(request.POST or None)
    errors = {}
    data = {}
    if request.method == 'POST':
        data['name'] = request.POST['name'].strip()
        data['text'] = request.POST['text'].strip()

        if not data['name'] or len(data['name']) < 2:
            errors['name'] = "true"

        if not data['text'] or len(data['text']) < 2 or data['text'].find('http') > 0 or data['text'].find(
                '.com') > 0 or data['text'].find('.ru') > 0:
            errors['text'] = "true"

        if not form.is_valid():
            errors['captcha'] = 'true'

        if not errors:
            form = form.cleaned_data
            new_comment = Commentitem(
                deckitem_id=item.id,
                status=1,
                text=data['text'],
                name=data['name']
            )
            new_comment.save()

            #  высылаем на почту информатор об отзыве
            subject_template = loader.get_template('subj_review.txt')
            message_template = loader.get_template('mess_review.txt')
            subject_context = {}
            message_context = {
                'new_comment': new_comment,
                'item_id': item.id
            }
            subject = subject_template.render(subject_context)
            message = message_template.render(message_context)
            send_mail(subject, message, settings.SENDER_EMAIL, [settings.REVIEW_EMAIL], fail_silently=True)

            if 'c' in request.GET:
                return redirect('/c/i/' + item_link + '/review_add_complete/?c=' + category.id)
            else:
                return redirect('/c/i/' + item_link + '/review_add_complete/')

    response = render(request, 'view_item.html', {
        'warehouse_list': WareHouse.objects.all(),
        'submenu_producer_active': submenu_producer_active,
        'item': item,
        'category': category,
        'submenu_active': submenu_active,
        "form": form,
        "errors": errors,
        'data': data,
        'comments': comments,
        'use_canonical': use_canonical,
        'menu_active': 'catalog',
        'producer': producer,
        'filters': filters,
        'current_link': 'c',
        'active_item': active_item
    })
    response['Cache-Control'] = 'no-cache, must-revalidate'
    return response


def filter_active_items_count(query):
    return query.filter(item__active=True).annotate(items_count=Count('item__id')).filter(items_count__gt=0)


def calculate_count(filter_element, category, group, groupfilters, query, original_query, get_query, producer_query,
                    catalog_group_view, show_availability, price_min, price_max):
    if group.active:
        query = original_query
        producer_filter_link = get_query.get('producer_filter')
        if producer_filter_link and producer_filter_link is not None:
            if len(producer_filter_link.split(',')) > 1:
                ids = []
                for one_producer_filter_link in producer_filter_link.split(','):
                    ids.append(producer_query.filter(link=one_producer_filter_link).values('id', 'link')[0]['id'])

                query = query.filter(producer_id__in=ids)
            else:
                try:
                    producer_filter = producer_query.filter(link=producer_filter_link).values('id', 'link')[0]
                    query = query.filter(producer_id=producer_filter['id'])
                except:
                    pass

        for group_element in groupfilters:
            if group_element.id == group.id:
                continue
            user_filter = get_query.get('f-' + group_element.link)
            if user_filter:
                try:
                    this_user_filter = Filter.objects.get(link=user_filter, tag_id=category.id)
                    filters_item = this_user_filter.deckitems.filter(active=1).values('id').distinct()
                    query = query.filter(id__in=filters_item)
                except Filter.DoesNotExist:
                    pass

    filters_item = Filter.objects.get(id=filter_element['id']).deckitems.filter(active=1).values('id').distinct()
    if catalog_group_view == 'no-group':
        ids = query.filter(id__in=filters_item, active=1).values_list('id', flat=True)
        if show_availability == 'show':
            if price_min and price_max:
                return Item.objects.filter(deckitem__id__in=ids, active=1, sort_price__gte=price_min,
                                           sort_price__lte=price_max).count()
            else:
                return Item.objects.filter(deckitem__id__in=ids, active=1).count()
        else:
            if price_min and price_max:
                return Item.objects.filter(deckitem__id__in=ids, active=1, sort_price__gte=price_min,
                                           sort_price__lte=price_max).exclude(availability=0).count()
            else:
                return Item.objects.filter(deckitem__id__in=ids, active=1).exclude(availability=0).count()
    else:
        sub_query = query.filter(id__in=filters_item)
        return filter_active_items_count(sub_query).count()


element_to_page = 1


def view_category(request, category_link=None, group_filter=False, filter_value=False, slug=None):
    #  опрелделим тип отображения каталога
    # if request.GET.get('catalog_group_view'):
    #     request.session["catalog_group_view"] = request.GET.get('catalog_group_view')

    # if not request.session.get("catalog_group_view"):
    request.session["catalog_group_view"] = 'no-group'
    catalog_group_view = request.session.get("catalog_group_view")

    #  опрелделим тип сортировки каталога
    # if request.GET.get('sort'):
    #     request.session["catalog_sort"] = request.GET.get('sort')
    #
    # if not request.session.get("catalog_sort"):
    #     request.session["catalog_sort"] = 'name'
    # catalog_sort = request.session.get("catalog_sort")

    #  определяем отображение товаров, который нет в наличии
    if request.GET.get('show_availability'):
        request.session["show_availability"] = request.GET.get('show_availability')

    if not request.session.get("show_availability"):
        request.session["show_availability"] = 'hide'
    show_availability = request.session.get("show_availability")

    #  определяем отображение новинок
    show_new = request.GET.get('show_new')
    if show_new is not None:
        request.session["show_new"] = show_new
    else:
        show_new = request.session.get('show_new', 'false')

    price_min = 0
    price_max = 0
    range_min = 0
    range_max = 0
    price_filter = False

    if request.GET.get('price'):
        if len(request.GET.get('price').split('-')) > 1:
            price_mass = request.GET.get('price').split('-')
            price_min = int(price_mass[0])
            price_max = int(price_mass[1])
            price_filter = True

    main_menu = Menu.objects.filter(menu_type=0).order_by('position')
    seo_enviroment = False

    seo_data = None

    if slug is not None:
        seo_data = get_object_or_404(FilterSitemapLink, slug=slug)
        category = seo_data.get_tag()
    else:
        category = get_object_or_404(Tag, link=category_link)

    aditional_menu = Tag.objects.filter(section=category.section).order_by('sort').values()

    #  определим переменные
    page = 1

    if 'page' in request.GET:
        page = int(request.GET['page'])
    start_query = int(page) * int(element_to_page) - int(element_to_page)
    stop_query = int(page) * int(element_to_page)
    iteration_count = 0

    #  получим все фильтры
    selected_filters = []
    all_groupfilters = GroupFilter.objects.filter(tag=category.id)
    groupfilters = all_groupfilters.filter(is_tag=False)
    tags = all_groupfilters.filter(is_tag=True)

    # query = Deckitem.objects.filter(active=1, tag=category.id)
    if request.user.is_authenticated:
        if request.user.optovik:
            query = category.deckitems.filter(active=1, producer__margin_opt__gt=0)
        elif request.user.zavodchik:
            query = category.deckitems.filter(active=1, producer__margin_zavodchiki__gt=0)
        else:
            query = category.deckitems.filter(active=1)
    else:
        query = category.deckitems.filter(active=1)

    original_query = query
    producer_filter_exists = query.values('producer').distinct().count() > 1
    producer_query = Producer.objects.filter(id__in=query.values('producer').distinct())

    if seo_data is not None:
        filters = seo_data.filters.all()
        if filters.count() > 0:
            query = query.filter(filters__in=filters).distinct()

        for groups in (tags, groupfilters):
            for group in groups:
                group.active = None
                user_filter = filters.filter(groupfilter=group).first()

                if user_filter is not None:
                    group.active = user_filter.link
                    user_filter.speciallink = group.link
                    user_filter.name = 'f-' + group.link
                    selected_filters.append(user_filter)
                    filters_item = user_filter.deckitems.filter(active=1).values_list('id', flat=True).distinct()
                    query = query.filter(id__in=filters_item).distinct()

                group.filters = group.filter.filter(hide=False).values()

                for f in group.filters:
                    f['checked'] = 0
                    if filters.filter(id=f['id']).exists():
                        f['checked'] = 1
    else:
        # отфильтруем товар
        for groups in (tags, groupfilters):
            for group in groups:
                user_filter = request.GET.get('f-' + group.link)
                if not user_filter and group_filter == group.link and filter_value:
                    try:
                        this_user_filter = Filter.objects.get(link=filter_value, tag_id=category.id)
                        if FilterDescription.objects.filter(filter=this_user_filter.id).exists():
                            seo_enviroment = FilterDescription.objects.get(filter=this_user_filter.id)
                            user_filter = filter_value
                        else:
                            return HttpResponseRedirect('/c/%s/' % category_link)
                    except Filter.DoesNotExist:
                        return HttpResponseRedirect('/c/%s/' % category_link)

                group.active = False
                if user_filter:
                    group.active = user_filter
                    try:
                        if len(user_filter.split(',')) > 1:
                            filters_item = []
                            user_filter_value = ''
                            for one_user_filter in user_filter.split(','):
                                this_user_filter = Filter.objects.filter(link=one_user_filter, tag_id=category.id).first()
                                user_filter_value += '%s,' % this_user_filter.link
                                temp_filters_item = this_user_filter.deckitems.filter(active=1).values_list('id',
                                                                                                            flat=True).distinct()
                                filters_item += temp_filters_item

                            this_user_filter.speciallink = group.link
                            this_user_filter.link = user_filter_value[0:-1]
                            this_user_filter.name = 'f-' + group.link
                            selected_filters.append(this_user_filter)
                        else:
                            this_user_filter = Filter.objects.get(link=user_filter, tag_id=category.id)
                            this_user_filter.speciallink = group.link
                            this_user_filter.name = 'f-' + group.link
                            selected_filters.append(this_user_filter)
                            filters_item = this_user_filter.deckitems.filter(active=1).values_list('id',
                                                                                                   flat=True).distinct()

                        query = query.filter(id__in=filters_item).distinct()
                    except Filter.DoesNotExist:
                        pass

                group.filters = group.filter.filter(hide=False).values()
                for one_filter in group.filters:
                    one_filter['checked'] = 0
                    if user_filter:
                        if len(user_filter.split(',')) > 1:
                            for one_user_filter in user_filter.split(','):
                                if one_user_filter == one_filter['link']:
                                    one_filter['checked'] = 1
                        else:
                            if one_filter['link'] == user_filter:
                                one_filter['checked'] = 1

    producer_pre_query = None
    producer_filter_link = None

    if seo_data is not None:
        if seo_data.producer is not None:
            producer_pre_query = query
            query = query.filter(producer=seo_data.producer)
            producer_filter_link = seo_data.producer.link
            selected_filters.append({
                'id': seo_data.producer.id,
                'link': seo_data.producer.link,
                'name': 'producer_filter'
            })
    else:
        producer_filter_link = request.GET.get('producer_filter')
        try:
            if producer_filter_link:
                producer_pre_query = query
                if producer_filter_link and producer_filter_link is not None:
                    if len(producer_filter_link.split(',')) > 1:
                        user_producer_value = ''
                        user_producer_ids = []
                        for one_producer_filter_link in producer_filter_link.split(','):
                            this_producer_filter = \
                            producer_query.filter(link=one_producer_filter_link).values('id', 'link')[0]
                            user_producer_value += '%s,' % this_producer_filter['link']
                            user_producer_ids.append(this_producer_filter['id'])

                        this_producer_filter['link'] = user_producer_value[0:-1]
                        this_producer_filter['name'] = 'producer_filter'
                        selected_filters.append(this_producer_filter)
                        query = query.filter(producer_id__in=user_producer_ids)
                    else:
                        producer_filter = producer_query.filter(link=producer_filter_link).values('id', 'link')[0]
                        producer_filter['name'] = 'producer_filter'
                        selected_filters.append(producer_filter)
                        query = query.filter(producer_id=producer_filter['id'])
        except:
            pass

    # сортируем товар
    if catalog_group_view == 'no-group':
        result = Item.objects.filter(deckitem__id__in=query.values_list('id', flat=True), active=1).select_related(
            'deckitem', 'deckitem__producer'
        ).annotate(
            is_available=ExpressionWrapper(~Q(availability=0), output_field=BooleanField()),
        )

        if show_availability == 'hide':
            result = result.exclude(availability=0)
        if show_new == 'true':
            result = result.filter(new=True)
        catalog_sort = ''
        # if catalog_sort == 'name':
        #     result = result.order_by('deckitem__order', 'deckitem__title')
        # elif catalog_sort == 'rate':
        #     result = result.order_by('-deckitem__number_of_purchases')
        # elif catalog_sort == 'price-desc':
        #     result = result.order_by('sort_price')
        # elif catalog_sort == 'price-asc':
        result = result.order_by('-quantity_in_reserve')

        range_max = result.aggregate(max=Max('sort_price'))['max']
        range_min = result.aggregate(min=Min('sort_price'))['min']

        if not range_max or not range_min:
            range_max = 0
            range_min = 0

        if price_min and price_max:
            result = result.filter(sort_price__gte=price_min, sort_price__lte=price_max)
    elif show_new == 'true':
        new_item_ids = Item.objects.filter(new=True).values_list('deckitem__id', flat=True)
        result = query.filter(id__in=new_item_ids).prefetch_related(
            Prefetch('item_set', queryset=Item.objects.filter(new=True))
        )
    else:
        result = query.prefetch_related(
            Prefetch(
                'item_set',
                queryset=Item.objects.filter(active=True).order_by('real_price')
            )
        )

    # соберем фильтры
    for groupfilter in (tags, groupfilters):
        for group in groupfilter:
            for one_filter in group.filters:
                one_filter['count'] = calculate_count(one_filter, category, group, all_groupfilters, query,
                                                      original_query, request.GET, producer_query, catalog_group_view,
                                                      show_availability, price_min, price_max)

    producer_query = producer_query.values('link', 'title', 'id', 'sort')
    for producer in producer_query:
        producer['checked'] = 0
        if producer_filter_link and producer_filter_link is not None:
            if len(producer_filter_link.split(',')) > 1:
                for one_producer_filter_link in producer_filter_link.split(','):
                    if one_producer_filter_link == producer['link']:
                        producer['checked'] = 1
            else:
                if producer_filter_link == producer['link']:
                    producer['checked'] = 1

        if catalog_group_view == 'no-group':
            if producer_pre_query:
                ids = producer_pre_query.filter(producer_id=producer['id'])
            else:
                ids = query.filter(producer_id=producer['id'])
            if show_availability == 'show':
                producer['count'] = Item.objects.filter(deckitem__id__in=ids).count()
            else:
                producer['count'] = Item.objects.filter(deckitem__id__in=ids).exclude(availability=0).count()
            if producer['count'] == 0:
                producer['sort'] = 999
        else:
            if producer_pre_query:
                producer['count'] = producer_pre_query.filter(producer_id=producer['id']).count()
            else:
                producer['count'] = query.filter(producer_id=producer['id']).count()
            if producer['count'] == 0:
                producer['sort'] = 999

    # query = filter_active_items_count(query)

    result_count = result.count()

    page_var = {'pages': []}

    if result_count > element_to_page:
        if catalog_group_view == 'no-group':
            result = result[start_query:stop_query]
        else:
            result = result.order_by('-availability', 'order', 'title')[start_query:stop_query]

        if result_count % element_to_page:
            iteration_count = math.trunc(result_count / element_to_page) + 1
        else:
            iteration_count = math.trunc(result_count / element_to_page)
        page_var['page_count'] = iteration_count

        if page == 1:  # первая страница
            page_var['next_page'] = page + 1
            page_var['first_page'] = True
            if iteration_count > 3:
                page_var['page_count'] = 3
            else:
                page_var['page_count'] = iteration_count

            for i in range(int(page_var['page_count'])):
                page_var['pages'].append(i + 1)

        elif page == iteration_count:  # последняя страница
            page_var['prev_page'] = page - 1
            page_var['not_next_page'] = True
            page_var['last_page'] = True
            if iteration_count > 3:
                page_var['page_count'] = 3
                for i in range(int(page_var['page_count'])):
                    page_var['pages'].append(page - 2 + i)
            elif iteration_count == 3:
                page_var['page_count'] = iteration_count
                for i in range(int(page_var['page_count'])):
                    page_var['pages'].append(page - 2 + i)
            else:
                page_var['page_count'] = iteration_count
                for i in range(int(page_var['page_count'])):
                    page_var['pages'].append(page - 1 + i)

        else:  # промежуточная страница
            page_var['next_page'] = page + 1
            page_var['prev_page'] = page - 1
            page_var['page_count'] = 5
            for i in range(int(page_var['page_count'])):
                this_page = page - 2 + i
                if this_page > 0 and this_page <= iteration_count:
                    page_var['pages'].append(page - 2 + i)

    else:
        if catalog_group_view == 'no-group':
            result = result
        else:
            result = result.order_by('-availability', 'order', 'title')
        stop_query = result_count

    if stop_query > result_count:
        stop_query = result_count

    # запрос на подгрузку новой страницы аяксом
    if request.GET.get('ajax_page'):
        # срендерим новый пагинатор
        new_paginator_template = loader.get_template('pageloader/paginator.html')
        new_paginator_context = {
            'pages': range(iteration_count),
            'page_var': page_var,
            'selected_filters': selected_filters,
            'category': category,
            'page': page,
            'result_count': result_count,
            'start_item': start_query,
            'end_item': stop_query,
            'catalog_group_view': catalog_group_view
        }
        new_paginator = new_paginator_template.render(new_paginator_context)

        # срендерим новую кнопку "загрузить еще"
        next_page_button_template = loader.get_template('pageloader/next_page_button.html')
        next_page_button_context = {
            'page_var': page_var,
            'selected_filters': selected_filters,
            'category': category,
            'price_min': price_min,
            'price_max': price_max,
        }
        next_page_button = next_page_button_template.render(next_page_button_context)

        # срендерим новые товары
        items_template = loader.get_template('pageloader/items.html')
        items_context = {
            'items': result,
            'catalog_group_view': catalog_group_view,
            'catalog_sort': catalog_sort,
            'request': request,
        }
        items = items_template.render(items_context)

        # срендерим новые фильтры
        filters_template = loader.get_template('pageloader/filters.html')
        filters_context = {
            'category': category,
            'groupfilters': groupfilters,
            'producer_filter_exists': producer_filter_exists,
            'producer_query': producer_query,
            'producer_filter': producer_filter_link,
            'catalog_group_view': catalog_group_view,
            'show_availability': show_availability,
            'show_new': show_new,
            'price_min': price_min,
            'price_max': price_max,
            'range_min': range_min,
            'range_max': range_max
        }
        filters = filters_template.render(filters_context)

        link = '/c/%s/?page=%s' % (category.link, page)
        for selected_filter in selected_filters:
            try:
                link += '&%s=%s' % (selected_filter.name, selected_filter.link)
            except AttributeError:
                link += '&%s=%s' % (selected_filter['name'], selected_filter['link'])
        if price_min > 0 and price_max > 0:
            link += '&price=%s-%s' % (price_min, price_max)

        # заполним заново переменные
        data_filters_template = loader.get_template('pageloader/data-filters.txt')
        data_filters = data_filters_template.render(next_page_button_context)

        next_page = False
        if 'next_page' in page_var:
            next_page = page_var['next_page']

        # срендерим новые теги
        tag_filters_template = loader.get_template('pageloader/tag_filters.html')
        tag_filters = tag_filters_template.render({'tags': tags})

        result_ajax_page = {
            'paginator': new_paginator,
            'next_page_button': next_page_button,
            'items': items,
            'page': page,
            'link': link,
            'data_filters': data_filters,
            'data_link': '/c/%s/' % category.link,
            'data_page': next_page,
            'filters': filters,
            'tag_filters': tag_filters,
            'catalog_group_view': catalog_group_view,
            'catalog_sort': catalog_sort,
            'price_filter': price_filter,
        }
        response = HttpResponse(json.dumps(result_ajax_page), content_type='application/javascript')
        response['Cache-Control'] = 'no-cache, must-revalidate'
        return response

    response = render(request, 'view_category.html', {
        'seo_data': seo_data,
        'aditional_menu': aditional_menu,
        'groupfilters': groupfilters,
        'tags': tags,
        'result_count': result_count,
        'selected_filters': selected_filters,
        'main_menu': main_menu,
        'category': category,
        'items': result,
        'menu_active': 'catalog',
        'submenu_active': category_link,
        'page': page,
        'pages': range(iteration_count),
        'page_var': page_var,
        'start_item': start_query,
        'end_item': stop_query,
        'producer_filter_exists': producer_filter_exists,
        'producer_query': producer_query,
        'producer_filter': producer_filter_link,
        'current_link': 'c',
        'seo_enviroment': seo_enviroment,
        'catalog_group_view': catalog_group_view,
        'show_availability': show_availability,
        'show_new': show_new,
        'catalog_sort': catalog_sort,
        'price_min': price_min,
        'price_max': price_max,
        'range_min': range_min,
        'range_max': range_max
    })
    response['Cache-Control'] = 'no-cache, must-revalidate'
    return response


def view_producer(request, producer_link):
    producer = get_object_or_404(Producer, link=producer_link)
    page = 1

    if 'page' in request.GET:
        page = int(request.GET['page'])

    start_query = int(page) * int(element_to_page) - int(element_to_page)
    stop_query = int(page) * int(element_to_page)

    iteration_count = 0

    query = Deckitem.objects.filter(producer=producer.id, active=1)
    query = filter_active_items_count(query)
    result_count = query.count()

    page_var = {'pages': []}
    if result_count > 20:
        result = query.order_by('-availability', 'order', 'title')[start_query:stop_query]
        if result_count % element_to_page:
            iteration_count = math.trunc(result_count / element_to_page) + 1
        else:
            iteration_count = math.trunc(result_count / element_to_page)
        page_var['page_count'] = iteration_count

        if page == 1:  # первая страница
            page_var['next_page'] = page + 1
            page_var['first_page'] = True
            if iteration_count > 3:
                page_var['page_count'] = 3
            else:
                page_var['page_count'] = iteration_count

            for i in range(int(page_var['page_count'])):
                page_var['pages'].append(i + 1)

        elif page == iteration_count:  # последняя страница
            page_var['prev_page'] = page - 1
            page_var['not_next_page'] = True
            page_var['last_page'] = True
            if iteration_count > 3:
                page_var['page_count'] = 3
                for i in range(int(page_var['page_count'])):
                    page_var['pages'].append(page - 2 + i)
            elif iteration_count == 3:
                page_var['page_count'] = iteration_count
                for i in range(int(page_var['page_count'])):
                    page_var['pages'].append(page - 2 + i)
            else:
                page_var['page_count'] = iteration_count
                for i in range(int(page_var['page_count'])):
                    page_var['pages'].append(page - 1 + i)

        else:  # промежуточная страница
            page_var['next_page'] = page + 1
            page_var['prev_page'] = page - 1
            page_var['page_count'] = 5
            for i in range(int(page_var['page_count'])):
                this_page = page - 2 + i
                if this_page > 0 and this_page <= iteration_count:
                    page_var['pages'].append(page - 2 + i)

    else:
        result = query.order_by('-availability', 'order', 'title')
        stop_query = result_count

    if stop_query > result_count:
        stop_query = result_count

    # запрос на подгрузку новой страницы аяксом
    if request.GET.get('ajax_page'):
        # срендерим новый пагинатор
        new_paginator_template = loader.get_template('pageloader/paginator.html')
        new_paginator_context = {
            'pages': range(iteration_count),
            'page_var': page_var,
            'producer': producer,
            'page': page,
            'result_count': result_count,
            'start_item': start_query,
            'end_item': stop_query,
        }
        new_paginator = new_paginator_template.render(new_paginator_context)

        # срендерим новую кнопку "загрузить еще"
        next_page_button_template = loader.get_template('pageloader/next_page_button.html')
        next_page_button_context = {
            'page_var': page_var,
            'producer': producer,
        }
        next_page_button = next_page_button_template.render(next_page_button_context)

        # срендерим новые товары
        items_template = loader.get_template('pageloader/items.html')
        items_context = {
            'items': result,
            'catalog_group_view': 'group'
        }
        items = items_template.render(items_context)

        next_page = False
        if 'next_page' in page_var:
            next_page = page_var['next_page']

        result_ajax_page = {
            'paginator': new_paginator,
            'next_page_button': next_page_button,
            'items': items,
            'page': page,
            'link': '/c/p/%s/?page=%s' % (producer.link, page),
            'data_page': next_page,
        }
        response = HttpResponse(json.dumps(result_ajax_page), content_type='application/javascript')
        response['Cache-Control'] = 'no-cache, must-revalidate'
        return response

    response = render(request, 'view_producer.html', {
        'result_count': result_count,
        'producer': producer,
        'items': result,
        'menu_active': 'catalog',
        'submenu_active': producer_link,
        'page': page,
        'pages': range(iteration_count),
        'page_var': page_var,
        'start_item': start_query,
        'end_item': stop_query,
        'current_link': 'c',
        'catalog_group_view': 'group'
    })
    response['Cache-Control'] = 'no-cache, must-revalidate'
    return response


@csrf_exempt
def cart_view(request):
    count = 0
    result = []
    zakaz = ''
    user_a_id = ''
    sale = ''
    sale_koef = 1
    real_zakaz_sum = 0
    sale_zakaz_sum = 0
    procent = ''
    dostavka = 0
    basket_of_goods = False

    if "user_a_id" in request.session:
        user_a_id = request.session["user_a_id"]
    if request.user.is_authenticated:
        user_a_id = request.user.id

        # SALE
        if request.user.sale:
            sale = True
            sale_koef = request.user.sale
            procent = int(100 - float(sale_koef) * 100)
            ## END SALE

    if request.method == 'POST':
        if int(request.POST['type']) == 2:  # ЗАКАЗ ОДОБРЕН, ОФОРМЛЯЕМ
            return HttpResponseRedirect("/cart/registration/")

    if request.user.is_authenticated and TempZakaz.objects.filter(owner=request.user.id):
        zakaz = TempZakaz.objects.get(owner=request.user.id)
    elif TempZakaz.objects.filter(hash=user_a_id) and not request.user.is_authenticated:
        zakaz = TempZakaz.objects.get(hash=user_a_id)

    if request.user.is_authenticated:
        basket_of_goods = request.user.basket_of_goods
    else:
        basket_of_goods = request.session.get('basket_of_goods')

    n = 1
    if zakaz:
        # Пересчёт корзины
        for goods in zakaz.tempzakazgoods_set.all():
            goods.save()

        if zakaz.tempzakazgoods_set.filter(summ_changed=True).exists():
            # Уведомление пользователя об изменении суммы заказа
            messages.warning(
                request=request,
                message=(
                    u'Обратите внимание! На одну или несколько позиций '
                    u'в корзине изменилась цена!'
                )
            )

        if zakaz.tempzakazgoods_set.filter(item__availability=0).exists():
            # Уведомление пользователя об изменении наличия товара
            messages.warning(
                request=request,
                message=(
                    u'Обратите внимание! У одной или нескольких позиций '
                    u'в корзине изменилось наличие!'
                )
            )

        ## подготавливаем товар в корзине для отображения
        data = TempZakazGoods.objects.filter(zakaz=zakaz.id)

        # Сохранение элементов корзины для перерасчёта их стоимости
        for i in data:
            i.save()

        # Применение изменений корзины и перерасчёт её суммы
        zakaz.save()

        count = data.count()
        for j in data.values():
            cart_line = TempZakazGoods.objects.get(id=j['id'])
            goods = Item.objects.get(id=j['item_id'])
            j['goods'] = goods
            if goods.availability != 0:
                j['real_sum'] = goods.current_price() * j['quantity']
                real_zakaz_sum += j['real_sum']
            else:
                j['real_sum'] = 0
            result.append(j)

    # Сортировка элементов корзины (товары, которых нет в наличии
    # должны оказаться в конце)
    result_sorted = []
    number = 1
    for i in result:
        if i['goods'].availability != 0:
            i['number'] = number
            result_sorted.append(i)
            number += 1
    for i in result:
        if i['goods'].availability == 0:
            i['number'] = len(result)
            result_sorted.append(i)

    basket_of_good_item = BasketOfGoodItem.objects.filter(
        Q(date_started__lte=timezone.now()) &
        Q(date_ended__gte=timezone.now())
    )

    summ_s_dostavkoy = 0
    summ_so_skidkoi = 0
    skidka = 0

    if zakaz:
        goods_items_ids = map(lambda i: i.item.id, zakaz.tempzakazgoods_set.all())
        basket_of_good_item = basket_of_good_item.exclude(item__id__in=goods_items_ids)

        ## СЧИТАЕМ ДОСТАВКУ
        dostavka = shipping(request.user, zakaz.summ)
        ## конец

        summ_s_dostavkoy = real_zakaz_sum + dostavka
        summ_so_skidkoi = zakaz.summ + dostavka

        skidka = summ_s_dostavkoy - summ_so_skidkoi

    empty = ''
    if int(count) == 0:
        empty = 'true'
        if zakaz:
            zakaz.delete()

    response = render(request, 'cart_view.html', {
        'summ_so_skidkoi': summ_so_skidkoi,
        'skidka': skidka,
        'procent': procent,
        'sale': sale,
        'count': count,
        'zakaz': zakaz,
        'result': result_sorted,
        'dostavka': dostavka,
        'empty': empty,
        'summ_s_dostavkoy': summ_s_dostavkoy,
        'real_zakaz_sum': real_zakaz_sum,
        'menu_active': 'cart',
        'basket_of_good_items': basket_of_good_item,
        "basket_of_goods": basket_of_goods
    })

    if isinstance(zakaz, TempZakaz):
        # После того как корзина отрендерилась, необходимо обновить флаги
        # у элементов корзины
        for goods in zakaz.tempzakazgoods_set.all():
            goods.summ_changed = False
            goods.save()

    response['Cache-Control'] = 'no-cache, must-revalidate'
    return response


@csrf_exempt
def edit_cart_line(request):
    result = {}
    result_temp = {}
    data = {}
    sale_koef = 1
    real_zakaz_sum = 0
    sale_zakaz_sum = 0

    if request.user.is_authenticated:
        if request.user.sale:
            sale_koef = request.user.sale

    if request.method == 'POST':
        data['count'] = request.POST['count'].strip()
        data['id'] = request.POST['id'].strip()
        try:
            line = TempZakazGoods.objects.get(id=data['id'])
        except TempZakazGoods.DoesNotExist:
            result['need_reload'] = True
            response = HttpResponse(json.dumps(result), content_type='application/javascript')
            response['Cache-Control'] = 'no-cache, must-revalidate'
            return response

        zakaz = TempZakaz.objects.get(id=line.zakaz.id)

        if not data['count']:
            data['count'] = 1

        if int(data['count']) == 0 or line.item.active == 0:
            data['count'] = 0
            line.delete()
        else:
            line.quantity = int(data['count'])
            line.save()
            result['real_line_summ'] = '%.2f' % round(line.quantity * line.item.current_price(), 2)
            result['line_summ'] = '%.2f' % round(line.summ, 2)

        cart_lines = TempZakazGoods.objects.filter(zakaz=zakaz.id)
        for j in cart_lines.values():
            goods = Item.objects.get(id=j['item_id'])
            if goods.availability != 0:
                j['real_sum'] = goods.current_price() * j['quantity']
                real_zakaz_sum += j['real_sum']

        zakaz.refresh_from_db()
        sale_zakaz_sum = zakaz.summ

        ## СЧИТАЕМ ДОСТАВКУ
        dostavka = shipping(request.user, sale_zakaz_sum)
        ## конец

        count = TempZakazGoods.objects.filter(zakaz=zakaz.id).count()

        if zakaz:
            result['summ_s_dostavkoy'] = real_zakaz_sum + dostavka
            result['summ_so_skidkoi'] = round(sale_zakaz_sum + dostavka, 2)
            result['skidka'] = round(result['summ_s_dostavkoy'] - result['summ_so_skidkoi'], 2)
            result['skidka'] = "%.2f" % result['skidka']
            result['skidka_na_meloch'] = round(result['summ_so_skidkoi'] - int(result['summ_so_skidkoi']), 2)
            if result['skidka_na_meloch'] < result['summ_so_skidkoi']:
                result['summ_so_skidkoi'] = int(result['summ_so_skidkoi'])
            else:
                result['skidka_na_meloch'] = False
            result['summ_so_skidkoi'] = "%.2f" % result['summ_so_skidkoi']
            result['skidka_na_meloch'] = "%.2f" % result['skidka_na_meloch']
        result['empty'] = ''

        if int(count) == 0:
            result['empty'] = True
            if zakaz:
                zakaz.delete()

        result['count'] = int(data['count'])
        result['dostavka'] = "%.2f" % dostavka
        result['real_zakaz_sum'] = "%.2f" % real_zakaz_sum

        response = HttpResponse(json.dumps(result), content_type='application/javascript')
        response['Cache-Control'] = 'no-cache, must-revalidate'
        return response


@csrf_exempt
def user_registration_in_cart(request, form, user_a_id):
    errors = {}
    user = ''
    ### test password
    if not request.POST['password_1'].strip() and len(request.POST['password_1'].strip()) < 3:
        errors['password_1'] = "true"
        errors['text'] = u"Пожалуйста, исправьте ошибки ниже. Слишком короткий пароль"
    else:
        password_1 = request.POST['password_1'].strip()
        password_2 = request.POST['password_2'].strip()
        if not password_1 == password_2:
            errors['password_2'] = "true"
            errors['text'] = u"Пожалуйста, исправьте ошибки ниже. Введенные пароли не совпадают"

    if not form.is_valid():
        errors['captcha'] = 'true'
        errors['text'] = u"Пожалуйста, исправьте ошибки ниже. Введите правильно символы с картинки."

    ### test username
    if not request.POST['username'].strip() or len(request.POST['username'].strip()) < 4:
        errors['username_1'] = "true"
        errors['text'] = u"Пожалуйста, исправьте ошибки ниже. Введите корректный e-mail."
    else:
        if Account.objects.filter(username=request.POST['username']):
            errors['username_2'] = "true"
            errors[
                'text'] = u"Пользователь с таким e-mail адресом уже зарегистрирован. <a class='recovery-link' href='/account/password/forget/'>Восстановить пароль</a>"

    if not is_valid_email(request.POST['username'].strip()):
        errors['username_3'] = "true"
        errors['text'] = u"Пожалуйста, исправьте ошибки ниже. Введите корректный e-mail."

    username = request.POST['username'].strip()

    if not errors:
        form = form.cleaned_data
        new_user = Account(
            username=username,
            email=username
        )
        new_user.set_password(password_2)
        new_user.save()

        user = auth.authenticate(username=username, password=password_2)
        auth.login(request, user)

        ## оформляем заказ новому юзеру
        if TempZakaz.objects.filter(hash=user_a_id):
            zakaz = TempZakaz.objects.get(hash=user_a_id)
            zakaz.owner_id = new_user.id
            zakaz.save()

        ## высылаем на почту регистрационные данные
        htmlmail_registration_data = {
            'username': username,
            'password': password_2,
            'user': request.user
        }
        htmlmail_sender('registration', htmlmail_registration_data, username)

    return errors, user


anonimous_user_id = 3229


@csrf_exempt
def cart_registration(request):
    user_a_id = ''
    form = RegistrationForm(request.POST or None)
    username = ''
    email = ''
    sale = False
    sale_koef = 1
    procent = False

    errors = {}
    data = {'paytype': 0, 'index': ''}

    if "user_a_id" in request.session:
        user_a_id = request.session["user_a_id"]
    if request.user.is_authenticated:
        user_a_id = request.user.id

    not_registration = ''
    if not request.user.is_authenticated:
        not_registration = 'true'

    if request.user.is_authenticated and TempZakaz.objects.filter(owner=request.user.id):
        zakaz = TempZakaz.objects.get(owner=request.user.id)
    elif TempZakaz.objects.filter(hash=user_a_id) and not request.user.is_authenticated:
        zakaz = TempZakaz.objects.get(hash=user_a_id)
    else:
        return HttpResponseRedirect("/")

    if request.method == 'POST':  # оформляем заказ

        # регистрируем нового пользователя
        if request.POST['type'] == '0':
            if request.POST.get('no_need_registration'):
                user = Account.objects.get(id=anonimous_user_id)
            else:
                errors, user = user_registration_in_cart(request, form, user_a_id)
                username = request.POST['username'].strip()
                if user:
                    not_registration = ''
        # /конец регистрации нового пользователя

        # cбор данных
        if request.POST['phone'].strip():
            data['phone'] = request.POST['phone'].strip()
        else:
            errors['phone'] = 'true'
        warehouse_id = int(request.POST.get('delivery_type', -1))  # -1 это доставка курьером
        data['city'] = request.POST['city'].strip()
        data['street'] = request.POST['street'].strip()
        data['dom'] = request.POST['dom'].strip()
        data['appart'] = request.POST['appart'].strip()
        data['fio'] = request.POST['fio'].strip()
        data['desired_time'] = request.POST['desired_time']
        data['comment'] = request.POST['comment']
        data['paytype'] = int(request.POST['paytype'])
        data['promocode'] = request.POST['promocode']
        if data['promocode']:
            data['comment'] += u"\n Промокод: %s" % data['promocode']

        if not errors:
            if request.POST.get('no_need_registration'):
                tempzakaz = TempZakaz.objects.get(hash=user_a_id)
                user_id = user.id
            else:
                tempzakaz = TempZakaz.objects.get(owner=request.user.id)
                user_id = request.user.id

            sale_koef = 1
            if not request.POST.get('no_need_registration'):
                if request.user.sale:
                    sale_koef = request.user.sale
                    if sale_koef != 1:
                        sale = True
                    procent = int(100 - float(sale_koef) * 100)

            new_zakaz = Zakaz(
                summ=tempzakaz.summ, status=0, owner_id=user_id,
                phone=data['phone'], fio=data['fio'],
                index=0, city=data['city'], street=data['street'],
                dom=data['dom'], appart=data['appart'],
                paytype=data['paytype'],
                dostavkatype=0,
                description=data['comment'],
                sale_koef=sale_koef,
                desired_time=data['desired_time'],
            )
            if warehouse_id < 0:
                delivery_type = 0
            else:
                warehouse = WareHouse.objects.filter(id=int(warehouse_id)).first()
                delivery_type = 1
                new_zakaz.pickup_warehouse = warehouse
            new_zakaz.dostavkatype = delivery_type
            new_zakaz.save()

            if not request.POST.get('no_need_registration'):
                if not request.user.first_name:  # если у Юзера не заполнено имя, заполним имя из заказа
                    request.user.first_name = data['fio']
                    request.user.save()

                if not request.user.phone:  # если у Юзера не заполнен телефон, заполним телефон из заказа
                    request.user.phone = data['phone']
                    request.user.save()

            temp_lines = TempZakazGoods.objects.filter(zakaz=tempzakaz.id).values()
            cost = 0
            real_sum = 0
            for line in temp_lines:
                if line['quantity'] > 0:
                    item = Item.objects.get(id=line['item_id'])
                    line['real_sum'] = round(item.current_price() * line['quantity'], 2)

                    line_sale = 0
                    if line['sale']:
                        line_sale = line['sale']
                    elif procent:
                        line_sale = procent

                    real_sum += line['real_sum']
                    cost += item.real_price * line['quantity']
                    new_line_order = ZakazGoods(
                        zakaz_id=new_zakaz.id,
                        item_id=line['item_id'],
                        quantity=line['quantity'],
                        summ=line['summ'],
                        sale=line_sale,
                        cost=item.real_price * line['quantity'],
                        presale=line['presale'],
                        action_id=line['action_id'],
                        basket_of_good=line['basket_of_good']
                    )

                    new_line_order.save()
            new_zakaz.summ = real_sum
            new_zakaz.save()
            TempZakazGoods.objects.filter(zakaz=tempzakaz.id).delete()
            tempzakaz.delete()

            result, summ_s_dostavkoy, summ_so_skidkoi, skidka, sale, procent, skidka_na_meloch = get_zakaz_parametr(
                request, new_zakaz)
            dostavka = shipping(request.user, summ_so_skidkoi)

            new_zakaz.cost = cost
            new_zakaz.dostavka = dostavka
            new_zakaz.revenue = summ_so_skidkoi + dostavka - cost
            new_zakaz.save()

            htmlmail_order_data = {
                'zakaz': new_zakaz,
                'zakaz_lines': result,
                'skidka': skidka,
                'procent': procent,
                'sale': sale,
                'dostavka': dostavka,
                'summ_so_skidkoi': summ_so_skidkoi,
                'summ_s_dostavkoy': summ_s_dostavkoy,
                'user': request.user,
                'skidka_na_meloch': skidka_na_meloch
            }

            if not request.POST.get('no_need_registration'):
                htmlmail_sender('order_complete', htmlmail_order_data, request.user.email,
                                request.user)  # высылаем информера клиенту

            htmlmail_sender('order_complete_manager', htmlmail_order_data,
                            settings.ORDER_EMAIL)  # высылаем информера менеджеру магазина

            return HttpResponseRedirect("/cart/complete/" + str(new_zakaz.id) + "/")

    elif not not_registration:
        if Zakaz.objects.filter(owner=user_a_id):
            data = Zakaz.objects.filter(owner=user_a_id).order_by('-id').values()[0]
            if data['paytype'] not in [0, 1, 4]:
                data['paytype'] = 0
        if request.user.first_name:
            data['fio'] = request.user.first_name
        if request.user.phone:
            data['phone'] = request.user.phone
    dostavka = shipping(request.user, zakaz.summ)
    warehouses = WareHouse.objects.all().order_by('-id')
    response = render(request, 'cart_registration.html', {
        'not_registration': not_registration,
        "form": form,
        "username": username,
        'dostavka': int(dostavka),
        "warehouses": warehouses,
        "errors": errors,
        'data': data,
        'menu_active': 'cart',
        'no_slider': True,
    })
    response['Cache-Control'] = 'no-cache, must-revalidate'
    return response


def cart_complete(request, zakaz_id):
    if request.user.is_authenticated and Zakaz.objects.filter(owner=request.user.id, id=zakaz_id):
        pass
    elif Zakaz.objects.filter(owner=anonimous_user_id, id=zakaz_id):
        pass
    else:
        return HttpResponseRedirect("/")

    zakaz = Zakaz.objects.get(id=zakaz_id)

    target_not_sended = False
    if not zakaz.target_sended:
        target_not_sended = True
        zakaz.target_sended = True
        zakaz.save()

    zakaz.paytype_text = PAY_TYPE_DICT[zakaz.paytype]
    zakaz.dostavkatype = DOSTAVKA_TYPE_DICT[zakaz.dostavkatype]

    zakaz.items = ZakazGoods.objects.filter(zakaz=zakaz).select_related('item', 'item__deckitem',
                                                                        'item__deckitem__producer',
                                                                        'item__deckitem__tag')

    sale = False
    sale_koef = 1
    procent = False
    if request.user.is_authenticated:
        # SALE
        if request.user.sale:
            sale = 'true'
            sale_koef = request.user.sale
            procent = int(100 - float(sale_koef) * 100)
            ## END SALE

    dostavka = shipping(request.user, zakaz.summ)

    summ_s_dostavkoy = zakaz.summ + dostavka
    summ_so_skidkoi = round(int(zakaz.summ) * float(sale_koef), 2) + dostavka
    skidka = summ_s_dostavkoy - summ_so_skidkoi

    skidka_na_meloch = False

    if zakaz.paytype != 4:
        skidka_na_meloch = summ_so_skidkoi - int(summ_so_skidkoi)
        if skidka_na_meloch < summ_so_skidkoi:
            summ_so_skidkoi = int(summ_so_skidkoi)

    response = render(request, 'cart_complete.html', {
        'target_not_sended': target_not_sended,
        'zakaz': zakaz,
        'skidka': skidka,
        'procent': procent,
        'sale': sale,
        'dostavka': dostavka,
        'summ_so_skidkoi': str(summ_so_skidkoi).replace(',', '.'),
        'summ_s_dostavkoy': summ_s_dostavkoy,
        'menu_active': 'cart',
        'user': request.user,
        'skidka_na_meloch': skidka_na_meloch
    })
    response['Cache-Control'] = 'no-cache, must-revalidate'
    return response


@csrf_exempt
def cart_add(request):
    kolvo = 1
    goods = Item.objects.get(id=request.POST['goods_id'])
    basket_of_good = False
    presale = 0
    if 'presale' in request.POST:
        presale = 1
    if "basket_of_good" in request.POST:
        basket_of_good = True

    if request.user.is_authenticated:
        if TempZakaz.objects.filter(owner=request.user.id):
            zakaz = TempZakaz.objects.get(owner=request.user.id)
            if TempZakazGoods.objects.filter(zakaz=zakaz.id, item=goods.id):
                zakaz_goods = TempZakazGoods.objects.get(zakaz=zakaz.id, item=goods.id)
                # zakaz_goods.summ = int(zakaz_goods.summ) + int(int(goods.price))*int(kolvo)
                zakaz_goods.quantity = int(kolvo) + int(zakaz_goods.quantity)
                zakaz_goods.save()
            else:
                new_zakaz_goods = TempZakazGoods(
                    zakaz_id=zakaz.id,
                    item_id=goods.id,
                    quantity=int(kolvo),
                    summ=0,
                    presale=presale,
                    basket_of_good=basket_of_good
                )
                new_zakaz_goods.save()
        else:
            zakaz = TempZakaz(
                owner_id=request.user.id,
                summ=0,
                date=datetime.datetime.now()
            )
            zakaz.save()

            zakaz_goods = TempZakazGoods(
                zakaz_id=zakaz.id,
                item_id=goods.id,
                quantity=int(kolvo),
                summ=0,
                presale=presale,
                basket_of_good=basket_of_good
            )
            zakaz_goods.save()
    else:
        if "user_a_id" in request.session:
            user_a_id = request.session["user_a_id"]
        else:
            date = datetime.datetime.now()
            hashstring = str(date) + str(random.randint(1, 100000))
            hashcode = hashlib.sha224(hashstring).hexdigest()
            request.session["user_a_id"] = hashcode
            user_a_id = hashcode

        if TempZakaz.objects.filter(hash=user_a_id):
            zakaz = TempZakaz.objects.get(hash=user_a_id)
            if TempZakazGoods.objects.filter(zakaz=zakaz.id, item=goods.id):
                zakaz_goods = TempZakazGoods.objects.get(zakaz=zakaz.id, item=goods.id)
                # zakaz_goods.summ = int(zakaz_goods.summ) + int(int(goods.price))*int(kolvo)
                zakaz_goods.quantity = int(kolvo) + int(zakaz_goods.quantity)
                zakaz_goods.save()
            else:
                new_zakaz_goods = TempZakazGoods(
                    zakaz_id=zakaz.id,
                    item_id=goods.id,
                    quantity=int(kolvo),
                    summ=0,
                    presale=presale,
                    basket_of_good=basket_of_good
                )
                new_zakaz_goods.save()
        else:
            zakaz = TempZakaz(
                summ=0,
                date=datetime.datetime.now(),
                hash=user_a_id
            )
            zakaz.save()

            zakaz_goods = TempZakazGoods(
                zakaz_id=zakaz.id,
                item_id=goods.id,
                quantity=int(kolvo),
                summ=0,
                presale=presale,
                basket_of_good=basket_of_good
            )
            zakaz_goods.save()

    zakaz_now = TempZakaz.objects.get(id=zakaz.id)
    kolvo_tovarov_v_korzine = TempZakazGoods.objects.filter(zakaz=zakaz_now.id).aggregate(quantity=Sum('quantity'))[
        'quantity']
    result = {'count': kolvo_tovarov_v_korzine, 'sum': int(zakaz_now.summ)}
    return HttpResponse(json.dumps(result), content_type='application/javascript')


def repeat(request, order_id):
    if request.user.is_authenticated and request.user.zakaz_set.filter(id=order_id).exists():
        if TempZakaz.objects.filter(owner=request.user.id):
            zakaz = TempZakaz.objects.get(owner=request.user.id)
        else:
            zakaz = TempZakaz(
                owner_id=request.user.id,
                summ=0,
                date=datetime.datetime.now()
            )
            zakaz.save()
        for goods in request.user.zakaz_set.filter(id=order_id).all()[0].zakazgoods_set.all():
            item = Item.objects.get(id=goods.item_id)
            if item.active and item.availability != 0 and item.deckitem.active and item.deckitem.availability != 0:
                if TempZakazGoods.objects.filter(zakaz=zakaz.id, item=goods.item_id):
                    zakaz_goods = TempZakazGoods.objects.get(zakaz=zakaz.id, item=goods.item_id)
                    zakaz_goods.quantity += goods.quantity
                    zakaz_goods.save()
                else:
                    new_zakaz_goods = TempZakazGoods(
                        zakaz_id=zakaz.id,
                        item_id=goods.item_id,
                        quantity=goods.quantity,
                        summ=0,
                    )
                    new_zakaz_goods.save()
    return HttpResponseRedirect('/cart/')


def create_zakaz(request, autozakaz_id, call_type):
    response = False
    if (request.user.is_authenticated and request.user.autozakaz_set.filter(
            id=autozakaz_id).exists()) or request.user.is_staff:
        zakaz = create_zakaz_from_autozakaz(autozakaz_id, datetime.datetime.now())

        if call_type == 'button_from_admin' and zakaz:
            response = HttpResponseRedirect('/DgJrfdJg/catalog/zakaz/%s/' % zakaz.id)
        elif call_type == 'button_from_admin' and not zakaz:
            response = HttpResponseRedirect('/DgJrfdJg/catalog/autozakaz/')

        if call_type == 'button_from_account' and zakaz:
            response = HttpResponseRedirect('/account/order/%s/' % zakaz.id)
        elif call_type == 'button_from_account' and not zakaz:
            response = HttpResponseRedirect('/account/orders/')

        if call_type == 'autocreate':
            response = True

    return response


def create_autozakaz(request, zakaz_id, call_type):
    if request.user.is_staff or (
        request.user.is_authenticated and request.user.zakaz_set.filter(id=zakaz_id).exists()):
        zakaz = get_object_or_404(Zakaz, id=zakaz_id)

        days = 30
        if 'days' in request.GET:
            days = request.GET['days']

        autozakaz = AutoZakaz(
            owner_id=zakaz.owner.id,
            repeat_period=days,
            zakaz=zakaz
        )
        autozakaz.save()

        zakaz_goods = ZakazGoods.objects.filter(zakaz=zakaz.id).values()

        count = 0
        for goods in zakaz_goods:
            item = Item.objects.get(id=goods['item_id'])
            if item.active and item.availability != 0 and item.deckitem.active:
                new_zakaz_goods = AutoZakazGoods(
                    zakaz_id=autozakaz.id,
                    item_id=goods['item_id'],
                    quantity=goods['quantity']
                )
                new_zakaz_goods.save()
                count += 1
        if count == 0:
            autozakaz.delete()

        if call_type == 'button_from_admin' and count > 0:
            return HttpResponseRedirect('/DgJrfdJg/catalog/autozakaz/%s/' % autozakaz.id)
        elif call_type == 'button_from_admin' and count == 0:
            return HttpResponseRedirect('/DgJrfdJg/catalog/autozakaz/')

        if call_type == 'button_from_account' and count > 0:
            return HttpResponseRedirect('/account/autoorder/%s/' % autozakaz.id)
        elif call_type == 'button_from_account' and count == 0:
            return HttpResponseRedirect('/account/orders/')

        if call_type == 'autocreate':
            pass

        return True

    return False


def create_zakaz_from_autozakaz(autozakaz_id, real_zakaz_date):
    autozakaz = get_object_or_404(AutoZakaz, id=autozakaz_id)

    data = {}
    if Zakaz.objects.filter(owner=autozakaz.owner.id):
        data = Zakaz.objects.filter(owner=autozakaz.owner.id).order_by('-id').values()[0]

    sale_koef = 1
    if autozakaz.owner.sale:
        sale_koef = autozakaz.owner.sale

    zakaz = Zakaz(
        owner_id=autozakaz.owner.id,
        summ=0,
        status=0,
        fio=data['fio'],
        phone=data['phone'],
        index=data['index'],
        city=data['city'],
        street=data['street'],
        dom=data['dom'],
        appart=data['appart'],
        district=data['district'],
        paytype=data['paytype'],
        need_call=data['need_call'],
        sale_koef=sale_koef,
        autocreate=True,
        extra=u'Дата наступления заказа %s' % real_zakaz_date
    )
    zakaz.save()

    autozakaz_goods = AutoZakazGoods.objects.filter(zakaz=autozakaz.id).values()

    count = 0
    for goods in autozakaz_goods:
        item = Item.objects.get(id=goods['item_id'])
        if item.active and item.availability != 0 and item.deckitem.active:
            new_zakaz_goods = ZakazGoods(
                zakaz_id=zakaz.id,
                item_id=goods['item_id'],
                quantity=goods['quantity'],
                summ=0,
            )
            new_zakaz_goods.save()
            count += 1

    if count == 0:
        zakaz.delete()
        zakaz = False
    else:
        autozakaz.last_order = real_zakaz_date
        autozakaz.repear_count += 1
        autozakaz.save()
    return zakaz


def delete_autozakaz(request, autozakaz_id, ):
    if request.user.is_staff or (
        request.user.is_authenticated and request.user.autozakaz_set.filter(id=autozakaz_id).exists()):
        autozakaz = get_object_or_404(AutoZakaz, id=autozakaz_id)
        autozakaz.delete()

    return HttpResponseRedirect('/account/orders/')


def autorepeat(request, order_id, days):
    if request.user.is_authenticated and request.user.zakaz_set.filter(id=order_id).exists():

        # создаем новый автозаказ
        zakaz = 0

        for goods in request.user.zakaz_set.filter(id=order_id).all()[0].zakazgoods_set.all():
            item = Item.objects.get(id=goods.item_id)
            if item.active:
                if TempZakazGoods.objects.filter(zakaz=zakaz.id, item=goods.item_id):
                    zakaz_goods = TempZakazGoods.objects.get(zakaz=zakaz.id, item=goods.item_id)
                    zakaz_goods.quantity += goods.quantity
                    zakaz_goods.save()
                else:
                    new_zakaz_goods = TempZakazGoods(
                        zakaz_id=zakaz.id,
                        item_id=goods.item_id,
                        quantity=goods.quantity,
                        summ=0,
                    )
                    new_zakaz_goods.save()
    return HttpResponseRedirect('/cart/')


def collect_autozakaz(request):
    autozakazes = AutoZakaz.objects.filter(active=True).values()
    now_date = datetime.datetime.now()

    for i in autozakazes:
        if i['last_order']:
            order_date = i['last_order'] + datetime.timedelta(days=i['repeat_period'])
        else:
            order_date = i['create_date'] + datetime.timedelta(days=i['repeat_period'])
        days = (order_date - now_date).days

        if i['repeat_period'] > 10:
            if days < 4:
                zakaz = create_zakaz_from_autozakaz(i['id'], order_date)
        else:
            if days < 3:
                zakaz = create_zakaz_from_autozakaz(i['id'], order_date)

    return HttpResponseRedirect('/')


def account(request):
    autorized = False
    sale = False
    if request.user.is_authenticated:
        autorized = True
        if request.user.sale:
            sale = int(100 - (float(request.user.sale) * 100))

    return render(request, 'account/profile.html', {'user': request.user, 'sale': sale, 'autorized': autorized})


def manage_change_status(request, zakaz_id, store_type, status_id):
    if request.user.is_authenticated and request.user.is_staff:
        if store_type == 'kostochka':
            zakaz = Zakaz.objects.get(id=zakaz_id)
            if zakaz.status in [3, 4]:
                zakaz.status = int(status_id)
                zakaz.save()
                new_zakazstatuslog = ZakazStatusLog(
                    zakaz=zakaz,
                    status=status_id,
                    user=request.user
                )
                new_zakazstatuslog.save()
        elif store_type == 'movement':
            zakaz = MovementOfGoods.objects.get(id=zakaz_id)
            if zakaz.status in [3, 4]:
                zakaz.status = int(status_id)
                zakaz.save(request)
                new_zakazstatuslog = MovementStatusLog(
                    movement=zakaz,
                    status=status_id,
                    user=request.user
                )
                new_zakazstatuslog.save()
        elif store_type == 'outside':
            zakaz = OutsideZakaz.objects.get(id=zakaz_id)
            if zakaz.status in [3, 4]:
                zakaz.status = int(status_id)
                zakaz.save()
                new_zakazstatuslog = OutsideZakazStatusLog(
                    zakaz=zakaz,
                    status=status_id,
                    user=request.user
                )
                new_zakazstatuslog.save()
        return HttpResponseRedirect('/mz/')
    return HttpResponseRedirect("/")


@transaction.atomic()
@reversion.create_revision()
def manage_change_status_from_collect_order(request, zakaz_id, status_id):
    if request.user.is_authenticated and request.user.is_staff:
        user = request.GET['user']

        date = False
        if 'date' in request.GET:
            date = request.GET['date']

        zakaz = Zakaz.objects.get(id=zakaz_id)
        if zakaz.status != 5 and zakaz.status != 6:
            zakaz.status = int(status_id)
        zakaz.save()

        reversion.set_user(request.user)
        reversion.set_comment("Change status")

        new_zakazstatuslog = ZakazStatusLog(
            zakaz=zakaz,
            status=status_id,
            user=request.user
        )
        new_zakazstatuslog.save()

        return HttpResponseRedirect('/manage/collect_orders/?user=%s&date=%s' % (user, date))
    return HttpResponseRedirect("/")


@transaction.atomic()
@reversion.create_revision()
def manage_change_status_movement_from_collect_order(request, zakaz_id, status_id):
    if request.user.is_authenticated and request.user.is_staff:
        user = request.GET['user']

        date = False
        if 'date' in request.GET:
            date = request.GET['date']

        zakaz = MovementOfGoods.objects.get(id=zakaz_id)
        if zakaz.status != 5 and zakaz.status != 6:
            zakaz.status = int(status_id)
        zakaz.save(request)

        reversion.set_user(request.user)
        reversion.set_comment("Change status")

        new_zakazstatuslog = MovementStatusLog(
            movement=zakaz,
            status=status_id,
            user=request.user
        )
        new_zakazstatuslog.save()

        return HttpResponseRedirect('/manage/collect_orders/?user=%s&date=%s' % (user, date))
    return HttpResponseRedirect("/")


def manage_change_status_inside(request, zakaz_id, status_id):
    if request.user.is_authenticated and request.user.is_staff:
        zakaz = InsideZakaz.objects.get(id=zakaz_id)
        zakaz.status = int(status_id)
        new_zakazstatuslog = InsideZakazStatusLog(
            zakaz=zakaz,
            status=zakaz.status,
            user=request.user
        )
        new_zakazstatuslog.save()
        zakaz.save()

        return HttpResponseRedirect('/mz/')
    return HttpResponseRedirect("/")


def calculate_courier(request, date=False):
    if request.user.is_authenticated and request.user.is_staff:
        warehouse = request.session.get('warehouse', -1)
        cur_warehouse_duty = Duty.get_current_duty_warehouse(warehouse)

        category = request.GET.get('category')

        if cur_warehouse_duty:
            default_courier_name = 'admin'
            if 'user' in request.GET:
                courier_name = request.GET['user']
            else:
                courier_name = default_courier_name

            if courier_name == 'pickup':
                courier_id = 0
                fix_zp_courier = 0
                fix_pay_courier = 0
                cash = 0
                delivery_costs = {
                    u'Иркутск': fix_pay_courier,
                }
            else:
                # if courier_name == 'kurier' or courier_name == 'maksim.solpin' or courier_name == 'antipin.aleksandr':
                fix_zp_courier = 0
                fix_pay_courier = 150
                cash = 0
                delivery_costs = {
                    u'Иркутск': fix_pay_courier,
                    u'Шелехов': 250,
                    u'Ангарск': 500
                }
                # else:
                #     fix_zp_courier = 0
                #     fix_pay_courier = 100
                #     cash = 0
                #     delivery_costs = {
                #         u'Иркутск': fix_pay_courier,
                #         u'Шелехов': 200,
                #         u'Ангарск': 500
                #     }

                courier_id = Account.objects.get(username=courier_name).id

            if 'cash' in request.GET:
                cash = float(request.GET['cash'])

            if not date:
                date = datetime.datetime.now() - datetime.timedelta(1)
                redirect_to = '/manage/calculate_courier/%s-%s-%s/?user=%s&category=%s' % (
                date.year, date.month, date.day, courier_name, category)
                return HttpResponseRedirect(redirect_to)

            date = dateutil.parser.parse(date)
            date_today = datetime.datetime.now()

            date_m_1 = date - datetime.timedelta(days=1)
            date_m_2 = date - datetime.timedelta(days=2)
            date_p_1 = date + datetime.timedelta(days=1)
            date_p_2 = date + datetime.timedelta(days=2)

            zakazs = []

            if courier_name == 'pickup':
                dict_zakazs = Zakaz.objects.filter(status__in=[5, 7, 10], dostavkatype=1, pickup_warehouse=1).values()
                dict_zakazs_move = []
                dict_movement = []
                insidezakazs_yesterday = {}
            else:
                dict_zakazs = Zakaz.objects.filter(status__in=[5, 7, 10], courier_id=courier_id).values()
                dict_zakazs_move = Zakaz.objects.filter(status__in=[31], courier_id=courier_id).values()
                dict_movement = MovementOfGoods.objects.filter(courier_paid=False, courier_id=courier_id,
                                                               status__in=[5, 6])
                insidezakazs_yesterday = InsideZakaz.objects.filter(status=6, courier_id=courier_id,
                                                                    date_pickup=date).select_related('segment_new')

            courier_zp_zakaz = 0
            courier_zp_insidezakaz = 0
            check_summ = 0

            check_sum_card = 0
            check_count_cash = 0
            check_count_card = 0

            for zakaz in dict_zakazs:
                this_zakaz = Zakaz.objects.get(id=zakaz['id'])
                this_zakaz.for_check_sum = 0
                this_zakaz.sdacha = 0
                this_zakaz.koplate = int(this_zakaz.k_oplate())
                if this_zakaz.status == 5:
                    cost = fix_pay_courier
                    if this_zakaz.city in delivery_costs:
                        cost = delivery_costs[this_zakaz.city]
                    courier_zp_zakaz += cost
                    this_zakaz.courier_cost = cost

                    if this_zakaz.paid_client:  # если заказ оплачен
                        this_zakaz.paytype = 4

                    elif this_zakaz.paytype == 0:
                        this_zakaz.for_check_sum = int(ceil(float(this_zakaz.k_oplate()) / 1000) * 1000)
                        check_summ += this_zakaz.for_check_sum
                        this_zakaz.sdacha = int(this_zakaz.for_check_sum - this_zakaz.k_oplate())

                        check_count_cash += 1
                    elif this_zakaz.paytype == 1:
                        check_sum_card += int(ceil(float(this_zakaz.k_oplate())))
                        check_count_card += 1
                else:
                    this_zakaz.courier_cost = 0
                    if this_zakaz.paytype == 0:
                        this_zakaz.for_check_sum = int(ceil(float(this_zakaz.k_oplate()) / 1000) * 1000)
                        this_zakaz.sdacha = int(this_zakaz.for_check_sum - this_zakaz.k_oplate())
                        this_zakaz.for_check_sum = this_zakaz.sdacha
                        check_summ += this_zakaz.for_check_sum
                zakazs.append(this_zakaz)

            for movement in dict_movement:
                movement.for_check_sum = 0
                movement.sdacha = 0
                movement.koplate = 0
                movement.movement = True
                cost = fix_pay_courier
                courier_zp_zakaz += cost
                movement.courier_cost = cost
                zakazs.append(movement)

            for zakaz in dict_zakazs_move:
                this_zakaz = Zakaz.objects.get(id=zakaz['id'])
                this_zakaz.for_check_sum = 0
                this_zakaz.sdacha = 0
                this_zakaz.koplate = int(this_zakaz.k_oplate())

                this_zakaz.courier_cost = 0
                if this_zakaz.paytype == 0:
                    this_zakaz.for_check_sum = int(ceil(float(this_zakaz.k_oplate()) / 1000) * 1000)
                    this_zakaz.sdacha = int(this_zakaz.for_check_sum - this_zakaz.k_oplate())
                    this_zakaz.for_check_sum = this_zakaz.sdacha
                    check_summ += this_zakaz.for_check_sum

                zakazs.append(this_zakaz)
            if courier_name != 'pickup':
                courier_zp_insidezakaz = fix_pay_courier * insidezakazs_yesterday.count()

            # SUPPLIERS = (
            #     (0, u'ПрокСервис (Пурина)'),
            #     (1, u'РоялКанин'),
            #     (2, u'Аврора'),
            #     (3, u'ЗооИркутск'), - налик
            #     (4, u'Слата'),
            #     (9, u'Валта'), - налик
            #     # (5, u'Бош'),
            #     (6, u'ДогСервис'), - налик
            #     (7, u'Кронос'),
            #     (8, u'ТаоБао'),
            #     (10, u'Спектр'),
            #     (11, u'Иванко'),
            #     (12, u'Пет-Континент'), - налик
            #     (13, u'Животный мир'),
            #     (14, u'Нордэкс'), - налик
            # )

            pay_insidezakazs = InsideZakaz.objects.filter(status=4, courier_id=courier_id, date_pickup=date_today,
                                                          segment_new_id__in=[999]).aggregate(sum=Sum('cost'))
            pay_insidezakazs['sum'] = str(pay_insidezakazs['sum']).replace(',', '.')

            if not pay_insidezakazs['sum'] or pay_insidezakazs['sum'] == 'None':
                pay_insidezakazs['sum'] = 0

            # for this_zakaz in insidezakazs_today:
            #     """
            #     SUPPLIERS = (
            #         (0, u'ПрокСервис (Пурина)'), - оплата в кредит
            #
            #         (1, u'РоялКанин'), - оплата с баланса
            #         (2, u'Аврора'), - оплата с баланса
            #
            #         (3, u'ЗооИркутск'), - оплата при получении
            #
            #         (9, u'Валта'), - оплата при получении
            #         (12, u'Пет-Континент'), - оплата при получении
            #         (14, u'Нордэкс'), - оплата при получении
            #
            #             (6, u'ДогСервис'), - оплата при получении
            #             (7, u'Кронос'), - оплата при получении
            #
            #         (4, u'Слата'), - заказной
            #         (8, u'ТаоБао'), - заказной
            #         (10, u'Спектр'), - заказной
            #         (11, u'Иванко'), - заказной
            #         (13, u'Животный мир'), - заказной
            #         (15, u'Карми'), - заказной
            #         (16, u'Велкорм'), - заказной
            #         (17, u'ТД Улан-Удэнские колбасы'),
            #
            #     )
            #     """
            #
            #     paid_type_2 = [1, 2, 3, 4, 9, 11, 12, 13, 15, 16, 17]
            #     paid_type_1 = [999]
            #     this_zakaz.cost = str(this_zakaz.cost).replace(',', '.')
            #     if this_zakaz.segment_new.id == 0:  # оплата в кредит
            #         this_zakaz.paid_type = 3
            #     elif this_zakaz.segment_new.id in paid_type_1:  # оплата при получении
            #         this_zakaz.paid_type = 1
            #     else:  # paid_type_2: # оплата с баланса безнала
            #         this_zakaz.paid_type = 2

            real_summ = cash + courier_zp_insidezakaz + courier_zp_zakaz + fix_zp_courier + float(
                pay_insidezakazs['sum'])
            zp_courier = courier_zp_insidezakaz + courier_zp_zakaz + fix_zp_courier

            balance = real_summ - check_summ

            #  завершенные заказы бьюти
            # try:
            if courier_name == 'pickup':
                data_bbox = False
            else:
                bcontext = ssl._create_unverified_context()
                json_string = urllib.request.urlopen(
                    'http://beautybox38.ru/admin/index.php?route=api/couriers_orders&key=beauty4kostochka&courier_id=' + str(
                        courier_id), context=bcontext).read()
                data_bbox = json.loads(json_string)
            # except:
            #     data_bbox = False

            bbox_courier_zp_zakaz = 0
            bbox_courier_zp_insidezakaz = 0
            bbox_check_summ = 0

            bbox_check_sum_card = 0
            bbox_check_count_cash = 0
            bbox_check_count_card = 0

            bbox = []

            if data_bbox:
                for i in data_bbox['delivered']:
                    i['id'] = i['order_number']
                    bbox_courier_zp_zakaz += int(i['courier_cost'])
                    # i['courier_cost'] = cost
                    i['for_check_sum'] = 0
                    i['sdacha'] = 0
                    i['koplate'] = int(i['total'])

                    if int(i['paytype']) == 0:
                        i['for_check_sum'] = int(ceil(float(int(i['koplate'])) / 1000) * 1000)
                        if int(i['change_from_5k']) == 1:
                            i['for_check_sum'] = 5000
                        bbox_check_summ += i['for_check_sum']
                        i['sdacha'] = int(i['for_check_sum'] - i['koplate'])

                        bbox_check_count_cash += 1

                    elif int(i['paytype']) == 1:
                        bbox_check_sum_card += i['koplate']
                        bbox_check_count_card += 1
                    bbox.append(i)

                for i in data_bbox['not_delivered']:
                    i['id'] = i['order_number']
                    i['sdacha'] = 0
                    i['koplate'] = int(i['total'])
                    i['for_check_sum'] = 0
                    if int(i['paytype']) == 0:
                        i['for_check_sum'] = int(ceil(float(int(i['total'])) / 1000) * 1000) - int(i['total'])

                        if int(i['change_from_5k']) == 1:
                            i['for_check_sum'] = 5000 - int(i['total'])

                        bbox_check_summ += i['for_check_sum']

                    bbox.append(i)

            finish_outside_zakaz = OutsideZakaz.objects.filter(store=1, status__in=[5, 7, 10],
                                                               courier_id=courier_id).values()
            if finish_outside_zakaz:
                bbox_courier_zp_zakaz += int(
                    OutsideZakaz.objects.filter(store=1, status__in=[5, 7, 10], courier_id=courier_id).aggregate(
                        sum=Sum('dostavka'))['sum'])
            for i in finish_outside_zakaz:
                if not i['paid_client']:
                    bbox_check_summ -= i['summ']

            response = render(request, 'calculate_courier.html', locals())
            response['Cache-Control'] = 'no-cache, must-revalidate'
            return response
        return HttpResponseRedirect("/s/")
    return HttpResponseRedirect("/")


def calculate_courier_finish(request, date):
    if request.user.is_authenticated and request.user.is_staff:
        warehouse = request.session.get('warehouse', -1)
        cur_warehouse_duty = Duty.get_current_duty_warehouse(warehouse)

        if cur_warehouse_duty:
            date = dateutil.parser.parse(date)
            date_today = datetime.datetime.now()
            category = request.POST.get('category')
            default_courier_name = 'admin'
            if 'user' in request.POST:
                courier_name = request.POST['user']
            else:
                courier_name = default_courier_name
            if category == 'bbox':
                courier_id = Account.objects.get(username=courier_name).id
                # завершенные заказы бьюти
                try:
                    if courier_name == 'pickup':
                        data_bbox = False
                    else:
                        bcontext = ssl._create_unverified_context()
                        json_string = urllib.request.urlopen(
                            'http://beautybox38.ru/admin/index.php?route=api/couriers_orders&key=beauty4kostochka&courier_id=' + str(
                                courier_id), context=bcontext).read()
                        data_bbox = json.loads(json_string)
                except:
                    data_bbox = False

                ids = ''

                bbxourl = 'http://beautybox38.ru/admin/index.php?route=api/couriers_orders/complete&key=beauty4kostochka&'
                if data_bbox:
                    for i in data_bbox['delivered']:
                        # bbox_courier_cost_{{ i.id }}
                        i['id'] = i['order_number']
                        ids += '%s,' % i['order_id']
                        check_sum = request.POST.get('zakaz' + str(i['id']))
                        courier_cost = request.POST.get('bbox_courier_cost_' + str(i['id']))
                        if check_sum:
                            bbxourl += '%s=%s,%s&' % (i['order_id'], check_sum, courier_cost)
                        else:
                            bbxourl += '%s=%s,%s&' % (i['order_id'], 99, courier_cost)

                bbxourl += 'orders=%s' % ids[0:-1]

                try:
                    if courier_name == 'pickup':
                        bbox_response = False
                    else:
                        bcontext = ssl._create_unverified_context()
                        json_string = urllib.request.urlopen(bbxourl, context=bcontext).read()
                        bbox_response = json.loads(json_string)

                except:
                    bbox_response = False

                finish_outside_zakaz_str = ''
                if courier_name != 'pickup':
                    finish_outside_zakaz = OutsideZakaz.objects.filter(store=1, status__in=[5, 7, 10],
                                                                    courier_id=courier_id).values()
                    for zakaz in finish_outside_zakaz:
                        this_zakaz = OutsideZakaz.objects.get(id=zakaz['id'])
                        check_sum = request.POST.get('outside' + str(this_zakaz.id))
                        if check_sum and this_zakaz != 6:
                            this_zakaz.status = 6
                            this_zakaz.paid_courier = True
                            this_zakaz.paid_client = True
                            this_zakaz.save()
                            finish_outside_zakaz_str += str(this_zakaz.id) + ', '
                
                # пишем лог приемки курьера
                text_for_log = u'Налички сдано: %s | ' \
                            u'bboxurl: %s | ' \
                            u'bbox response: %s | ' \
                            u'сторонние доставки: %s' % (
                            request.POST.get('cash'), bbxourl,
                            bbox_response, finish_outside_zakaz_str)


            elif category == 'kostochka':
                if courier_name == 'pickup':

                    courier_id = 0
                    zakazs = Zakaz.objects.filter(status=5, dostavkatype=1, pickup_warehouse=1).values()
                    zakazs_str = ''

                    dict_movement = []
                    dict_movement_str = ''

                    insidezakazs_yesterday = []
                    insidezakazs_yesterday_str = ''
                else:
                    courier_id = Account.objects.get(username=courier_name).id

                    zakazs = Zakaz.objects.filter(status=5, courier_id=courier_id).values()
                    zakazs_str = ''

                    dict_movement = MovementOfGoods.objects.filter(courier_paid=False, courier_id=courier_id,
                                                                status__in=[5, 6])
                    dict_movement_str = ''

                    insidezakazs_yesterday = InsideZakaz.objects.filter(status=6, courier_id=courier_id,
                                                                        date_pickup=date).values()
                    insidezakazs_yesterday_str = ''

                # insidezakazs_today = InsideZakaz.objects.filter(status=4, courier_id=courier_id, date_pickup=date_today).values()
                # insidezakazs_today_str = ''

                courier_zp_zakaz = 0
                courier_zp_insidezakaz = 0
                check_summ = 0
                for zakaz in zakazs:
                    this_zakaz = Zakaz.objects.get(id=zakaz['id'])
                    check_sum = request.POST.get('zakaz' + str(this_zakaz.id))
                    cash_input = request.POST.get('cash-input-{}'.format(this_zakaz.id), 0)
                    if cash_input is None:
                        cash_input = 0
                    if check_sum != '' and check_sum is not None:
                        check_sum = int(check_sum)
                    if cash_input == '':
                        cash_input = 0
                    cash_input = int(cash_input)
                    if check_sum == 0 or check_sum == 1 or check_sum == 4:
                        if int(check_sum) != 4:
                            this_zakaz.paytype = int(check_sum)
                        if cash_input > 0:
                            this_zakaz.paytype = 6
                        this_zakaz.status = 6
                        this_zakaz.paid_client = True

                        new_zakazstatuslog = ZakazStatusLog(
                            zakaz=this_zakaz,
                            status=6,
                            user=request.user
                        )
                        new_zakazstatuslog.save()

                        if not this_zakaz.cash_go_to_kassa:
                            this_zakaz.cash_go_to_kassa = True
                            if not Expense.objects.filter(description=u'заказ №' + str(this_zakaz.id)):
                                summ_so_skidkoi = this_zakaz.get_summ_with_sale()

                                if this_zakaz.paytype == 1:
                                    summ = ceil(summ_so_skidkoi * settings.BANK_COMMISSION) + this_zakaz.dostavka
                                else:
                                    summ = ceil(summ_so_skidkoi) + this_zakaz.dostavka
                                if this_zakaz.paytype != 6:
                                    new_expense = Expense(
                                        type=1,
                                        type_of_currency=this_zakaz.paytype,
                                        value=summ,
                                        description=u'заказ №' + str(this_zakaz.id),
                                        expensetype_id=1
                                    )
                                    new_expense.save()
                                else:
                                    non_cash = this_zakaz.summ - cash_input
                                    non_cash = non_cash * settings.BANK_COMMISSION
                                    this_zakaz.cash = cash_input
                                    this_zakaz.non_cash = non_cash
                                    new_expense_cash = Expense(
                                        type=1,
                                        type_of_currency=0,
                                        value=cash_input,
                                        description=u'заказ №{}'.format(this_zakaz.id),
                                        expensetype_id=1,
                                    )
                                    new_expense_cash.save()
                                    new_expense_non_cash = Expense(
                                        type=1,
                                        type_of_currency=1,
                                        value=non_cash,
                                        description=u'заказ №{}'.format(this_zakaz.id),
                                        expensetype_id=1,
                                    )
                                    new_expense_non_cash.save()

                        this_zakaz.paid_courier = True
                        this_zakaz.save()
                        zakazs_str += str(this_zakaz.id) + ', '

                for zakaz in dict_movement:
                    this_zakaz = MovementOfGoods.objects.get(id=zakaz.id)
                    check_sum = request.POST.get('movement' + str(this_zakaz.id))
                    if check_sum:
                        this_zakaz.courier_paid = True
                        dict_movement_str += str(this_zakaz.id) + ', '
                        this_zakaz.save(request)

                for zakaz in insidezakazs_yesterday:
                    this_zakaz = InsideZakaz.objects.get(id=zakaz['id'])
                    check_sum = request.POST.get('insidezakazs_yesterday' + str(this_zakaz.id))
                    if check_sum:
                        this_zakaz.paid_courier = True
                        this_zakaz.save()
                        insidezakazs_yesterday_str += str(this_zakaz.id) + ', '

                # пишем лог приемки курьера
                text_for_log = u'Заказы клиентов проведеы и закрыты: %s | ' \
                            u'Перемещения оплата курьера закрыта: %s | ' \
                            u'Заказы поставщиков за вчера проведены, оплата курьера закрыта: %s | ' \
                            u'Налички сдано: %s | ' % (
                            zakazs_str, dict_movement_str, insidezakazs_yesterday_str, request.POST.get('cash'))

            image = ''

            if 'screenshot' in request.POST:
                screenshot = request.POST.get('screenshot')
                screenshot = screenshot.replace('data:image/png;base64,', '')
                screenshot = screenshot.decode('base64')
                filename = "%s.png" % uuid.uuid4()

                directory_string_var = 'media/screenshot_courier'
                filename = os.path.join(directory_string_var, filename)
                filename = os.path.join(settings.BASE_DIR, filename)
                fh = open(filename, "wb")
                fh.write(screenshot)
                fh.close()
                image = fh.name.replace(settings.BASE_DIR + '/media/', '')

            if courier_name != 'pickup':
                new_log = LogingCourierFinish(
                    textlog=text_for_log,
                    courier_id=courier_id,
                    image=image
                )
                new_log.save()

            if courier_name != 'pickup' and category == 'kostochka':
                #  записываем "движение средств" за зарплату курьера
                zp_courier = request.POST.get('zp_courier')
                if not Expense.objects.filter(description=u'Курьер (%s) - оплата за доставки %s.%s.%s' % (courier_name, date.day, date.month, date.year)):
                    new_expense = Expense(
                        type=0,
                        type_of_currency=0,
                        value=-int(zp_courier),
                        description=u'Курьер (%s) - оплата за доставки %s.%s.%s' % (
                        courier_name, date.day, date.month, date.year),
                        expensetype_id=2
                    )
                    new_expense.save()

            if category == 'kostochka' or courier_name == 'pickup':
                check_sum_cash = 0
                if request.POST.get('check_sum_cash'):
                    check_sum_cash = request.POST.get('check_sum_cash')
                new_encashment = Encashment(
                    money=check_sum_cash,
                    type=70,
                    comment=u'Приемка %s за %s.%s.%s' % (courier_name, date.day, date.month, date.year),
                    duty=cur_warehouse_duty
                )
                new_encashment.save()

            if courier_name != 'pickup' and category == 'kostochka':
                new_encashment = Encashment(
                    money=-int(zp_courier),
                    type=2,
                    comment=u'Оплата %s за %s.%s.%s' % (courier_name, date.day, date.month, date.year),
                    duty=cur_warehouse_duty
                )
                new_encashment.save()

            response = render(request, 'calculate_courier_finish.html', locals())
            response['Cache-Control'] = 'no-cache, must-revalidate'
            return response
        return HttpResponseRedirect("/s/")
    return HttpResponseRedirect("/")


def manage_collect_pdf(request):
    if request.user.is_authenticated and request.user.is_staff:
        if request.GET['ids']:
            ids = request.GET['ids'].split(',')
            onlyclient = request.GET.get('onlyclient')
            path = settings.BASE_DIR
            zakazs = []
            if len(ids) > 0:
                for id in ids:
                    pre_result = {}

                    pre_result['zakaz'] = Zakaz.objects.get(id=id)
                    pre_result['result'], pre_result['summ_s_dostavkoy'], pre_result['summ_so_skidkoi'], pre_result[
                        'skidka'], pre_result['sale'], pre_result['procent'], pre_result[
                        'skidka_na_meloch'] = get_zakaz_parametr_static(request, pre_result['zakaz'])

                    pre_result['zakaz'].for_check_sum = int(ceil(float(pre_result['zakaz'].k_oplate()) / 1000) * 1000)
                    pre_result['zakaz'].change = int(ceil(float(pre_result['zakaz'].k_oplate()) / 1000) * 1000) - \
                                                 pre_result['zakaz'].k_oplate()

                    pre_result['zakaz'].all_summ = pre_result['summ_so_skidkoi']
                    pre_result['zakaz'].paytype = PAY_TYPE_DICT[pre_result['zakaz'].paytype]
                    pre_result['zakaz'].dostavkatype = DOSTAVKA_TYPE_DICT[pre_result['zakaz'].dostavkatype]

                    pre_result['dostavka'] = pre_result['zakaz'].dostavka

                    if pre_result['zakaz'].district:
                        pre_result['zakaz'].district_name = pre_result['zakaz'].get_district_display()
                    zakazs.append(pre_result)

                if 'signature' in request.GET:
                    signature = True
                data = locals()

                response = HttpResponse(content_type='application/pdf')
                response['Content-Desposition'] = 'attachment; filename=super_file.pdf'

                template = get_template('collect_for_pdf.html')
                html = template.render(data)

                pisaFileObject.getNamedFile = lambda self: self.uri
                pdf = pisa.CreatePDF(html, response, encoding='utf-8')
                if pdf.err:
                    return HttpResponse('We had some errors <pre>' + html + '</pre>')
                return response
    return HttpResponseRedirect("/")


def change_nominal(current_nominal):
    new_nominal = 1
    if current_nominal == 1000:
        new_nominal = 500
    elif current_nominal == 500:
        new_nominal = 100
    elif current_nominal == 100:
        new_nominal = 50
    elif current_nominal == 50:
        new_nominal = 10
    elif current_nominal == 10:
        new_nominal = 5
    elif current_nominal == 5:
        new_nominal = 2
    elif current_nominal == 2:
        new_nominal = 1
    return new_nominal


def manage_collect_change(request):
    if request.user.is_authenticated and request.user.is_staff:
        changes_dict = {
            # 1000: 0,
            500: 0,
            100: 0,
            50: 0,
            10: 0,
            5: 0,
            2: 0,
            1: 0,
        }
        ids = request.GET['ids'].split(',')

        zakazs = []
        changes = 0
        try:
            first_order_courier = Zakaz.objects.get(id=ids[0]).courier
            courier_name = '%s %s' % (first_order_courier.first_name, first_order_courier.last_name)
        except:
            courier_name = u'?'

        for zakaz_id in ids:
            if zakaz_id:
                this_zakaz = Zakaz.objects.get(id=zakaz_id)
                this_zakaz.for_check_sum = 0

                if (this_zakaz.paytype == 0 or this_zakaz.paytype == 2) and not this_zakaz.paid_client:
                    this_zakaz.for_check_sum = int(ceil(float(this_zakaz.k_oplate()) / 1000) * 1000)
                    this_zakaz.change = int(ceil(float(this_zakaz.k_oplate()) / 1000) * 1000) - this_zakaz.k_oplate()
                    changes += this_zakaz.change

                    check_summ = 0
                    temporal_check_summ = 0
                    nominal = 500

                    while int(this_zakaz.change) != check_summ:
                        temporal_check_summ += nominal

                        if int(this_zakaz.change) >= temporal_check_summ:
                            changes_dict[nominal] += 1
                            check_summ = temporal_check_summ
                        else:
                            nominal = change_nominal(nominal)
                            temporal_check_summ = check_summ

                zakazs.append(this_zakaz)

        data = {
            'zakazs': zakazs,
        }
        now = datetime.datetime.now()
        response = render(request, 'admin_module/collect_change.html', locals())
        response['Cache-Control'] = 'no-cache, must-revalidate'
        return response

    return HttpResponseRedirect("/")


def manage_check_orders(request):
    if request.user.is_authenticated and request.user.is_staff:
        ids = request.GET['ids'].split(',')
        zakazs = []
        changes = 0
        for zakaz_id in ids:
            this_zakaz = Zakaz.objects.get(id=zakaz_id)
            this_zakaz.goods = ZakazGoods.objects.filter(zakaz=this_zakaz.id).select_related('item', 'item__deckitem',
                                                                                             'item__deckitem__producer')
            zakazs.append(this_zakaz)

        data = {
            'zakazs': zakazs,
        }
        now = datetime.datetime.now()
        response = render(request, 'admin_module/check_orders.html', locals())
        response['Cache-Control'] = 'no-cache, must-revalidate'
        return response

    return HttpResponseRedirect("/")


def manage_print_orders(request):
    default_courier_name = 'admin'
    if 'user' in request.GET:
        courier_name = request.GET['user']
    else:
        courier_name = default_courier_name
    courier_id = Account.objects.get(username=courier_name).id
    zakazs = Zakaz.objects.filter(courier_id=courier_id, status=3).exclude(owner__ur_lico=True).values_list('id',
                                                                                                            flat=True).order_by(
        'id')
    zakazs_id = ''
    for i in zakazs:
        zakazs_id += '%s,' % i
    zakazs_id = zakazs_id[0:-1]
    return redirect('/manage/collect_pdf/?onlyclient=1&ids=%s' % zakazs_id)


def manage_print_cash(request):
    default_courier_name = 'admin'
    if 'user' in request.GET:
        courier_name = request.GET['user']
    else:
        courier_name = default_courier_name
    courier_id = Account.objects.get(username=courier_name).id
    zakazs = Zakaz.objects.filter(courier_id=courier_id, status=3).values_list('id', flat=True).order_by('id')
    zakazs_id = ''
    for i in zakazs:
        zakazs_id += '%s,' % i
    zakazs_id = zakazs_id[0:-1]
    return redirect('/manage/collect_change/?1&ids=%s' % zakazs_id)


def manage_collect_orders(request):
    if request.user.is_authenticated and request.user.is_staff:

        warehouse = request.session.get('warehouse', -1)
        cur_warehouse_duty = Duty.get_current_duty_warehouse(warehouse)

        if cur_warehouse_duty:
            default_courier_name = 'admin'
            if 'user' in request.GET:
                courier_name = request.GET['user']
            else:
                courier_name = default_courier_name

            date = False
            if 'date' in request.GET:
                date = request.GET['date']
                date_no_parse = date

            if not date:
                date = datetime.datetime.now()
                redirect_to = '/manage/collect_orders/?user=%s&date=%s-%s-%s' % (
                    courier_name, date.year, date.month, date.day)
                return HttpResponseRedirect(redirect_to)

            date = dateutil.parser.parse(date)

            if courier_name == 'pickup':
                courier_id = 0
                collect_zalaz = Zakaz.objects.filter(
                    Q(courier_id__isnull=True, real_desired_time=date, status__in=[3, 31, 2],
                      dostavkatype=1, )).order_by('pickup_warehouse')
            else:
                courier_id = Account.objects.get(username=courier_name).id

                zakazs_notcomplete = []
                zakazs_complete = []
                changes = 0
                collect_zalaz = Zakaz.objects.filter(
                    Q(courier_id=courier_id, real_desired_time=date, status__in=[3, 31, 2]) | Q(courier_id=courier_id,
                                                                                                morning_delivery=True,
                                                                                                status__in=[2]))

            zakazs_notcomplete = []
            zakazs_complete = []
            changes = 0

            for this_zakaz in collect_zalaz:
                # zakaz_id = zakaz_id.id
                # this_zakaz = Zakaz.objects.get(id=zakaz_id)
                this_zakaz.goods = ZakazGoods.objects.filter(zakaz=this_zakaz.id).select_related('item',
                                                                                                 'item__deckitem',
                                                                                                 'item__deckitem__producer')
                this_zakaz.basket_of_good = any(map(lambda g: g.basket_of_good, this_zakaz.goods))

                this_zakaz.completed = 2
                full_empty = True
                for i in this_zakaz.goods:
                    quantity_in_reserve = i.item.quantity_in_reserve_by_warehouse(1)
                    if (quantity_in_reserve - i.item__vreserve_count()) < i.quantity:
                        this_zakaz.completed = 1
                    if (quantity_in_reserve - i.item__vreserve_count()) > 0:
                        full_empty = False
                if full_empty:
                    this_zakaz.completed = 0

                if ZakazGoods.objects.filter(zakaz=this_zakaz.id, sale__gt=5):
                    this_zakaz.sale = True

                if ZakazGoods.objects.filter(zakaz=this_zakaz.id, item__heavy=True, item__deckitem__producer_id=306):
                    this_zakaz.sklad2 = True
                elif ZakazGoods.objects.filter(zakaz=this_zakaz.id,
                                               item__deckitem__producer_id__in=[176, 27, 359, 341, 412]):
                    this_zakaz.sklad2 = True

                if this_zakaz.status in [3, 31]:
                    zakazs_complete.append(this_zakaz)
                else:
                    zakazs_notcomplete.append(this_zakaz)

            if courier_name != 'pickup':
                movement_complete = MovementOfGoods.objects.filter(courier_id=courier_id, delivery_date=date,
                                                                   status__in=[3, 31])
                movement_notcomplete = MovementOfGoods.objects.filter(courier_id=courier_id, delivery_date=date,
                                                                      status__in=[0])

            # zakazs_notcomplete = []
            # zakazs_complete = []

            now = datetime.datetime.now()
            response = render(request, 'admin_module/collect_orders.html', locals())
            response['Cache-Control'] = 'no-cache, must-revalidate'
            return response

        return HttpResponseRedirect("/s/")

    return HttpResponseRedirect("/")


def bober(zakaz):
    bober = False
    goods = ZakazGoods.objects.filter(zakaz=zakaz)
    for good in goods:
        if (good.basket_of_good):
            bober = True
            break

    return bober


def collect_inside_orders(request, segment_id):
    if request.user.is_authenticated and request.user.is_staff:
        ids = request.GET['ids'].split(',')
        ids_ordered_items = []

        new_inside_zakaz = InsideZakaz(
            cost=0,
            extra=u'Автосборка: %s' % ids,
            segment_new_id=segment_id,
            details=''
        )
        new_inside_zakaz.save()

        if not int(segment_id) in [1, 2, 3, 9, 12, 18, 102]:
            """
            Иногородние заказы
            """

            last_inside_order = InsideZakaz.objects.filter(segment_new_id=segment_id, status=6).order_by(
                '-date').first()
            ids = Zakaz.objects.filter(date_end__gt=last_inside_order.date).values_list('id', flat=True)

            for zakaz_id in ids:
                this_zakaz = Zakaz.objects.get(id=zakaz_id)

                if this_zakaz.owner_id == 577 or this_zakaz.status in [6, 7, 10] or not this_zakaz.warehouse_id == 1:
                    continue

                this_zakaz.goods = ZakazGoods.objects.filter(item__deckitem__segment_new__id=segment_id,
                                                             zakaz=this_zakaz.id).select_related('item',
                                                                                                 'item__deckitem',
                                                                                                 'item__deckitem__producer')

                for i in this_zakaz.goods:

                    need_order = i.buy_count_3_month_for_auto_suplier_order_round() - i.check_total_for_auto_inside_order()
                    if need_order > 0 and not i.item_id in ids_ordered_items:
                        ids_ordered_items.append(i.item_id)

                        new_inside_zakaz_line = InsideZakazGoods(
                            zakaz=new_inside_zakaz,
                            item=i.item,
                            quantity=need_order,
                            action=i.action
                        )
                        new_inside_zakaz.details += "%s b3m_faso=%s - ctotal_faio=%s \r\n" % (
                            i.item.id,
                            i.buy_count_3_month_for_auto_suplier_order_round(),
                            i.check_total_for_auto_inside_order()
                        )

                        new_inside_zakaz_line.save()
            new_inside_zakaz.save()

        else:
            """
            Местные поставщики (Иркутск)
            """
            for zakaz_id in ids:
                this_zakaz = Zakaz.objects.get(id=zakaz_id)

                if this_zakaz.owner_id == 577 or this_zakaz.status in [6, 7, 10]:
                    continue

                this_zakaz.goods = ZakazGoods.objects.filter(item__deckitem__segment_new__id=segment_id,
                                                             zakaz=this_zakaz.id).select_related('item',
                                                                                                 'item__deckitem',
                                                                                                 'item__deckitem__producer')
                for i in this_zakaz.goods:

                    # need_order = i.buy_count_3_month_for_auto_suplier_order() - i.check_total_for_auto_inside_order()
                    need_order = 0 - i.check_total_for_auto_inside_order()
                    if need_order > 0 and not i.item_id in ids_ordered_items:
                        ids_ordered_items.append(i.item_id)

                        new_inside_zakaz_line = InsideZakazGoods(
                            zakaz=new_inside_zakaz,
                            item=i.item,
                            quantity=need_order,
                            action=i.action
                        )
                        new_inside_zakaz.details += "%s b3m_faso=%s - ctotal_faio=%s \r\n" % (
                            i.item.id,
                            i.buy_count_3_month_for_auto_suplier_order(),
                            i.check_total_for_auto_inside_order()
                        )
                        new_inside_zakaz_line.save()
            new_inside_zakaz.save()

        return HttpResponseRedirect('/DgJrfdJg/catalog/insidezakaz/%s/' % new_inside_zakaz.id)
    return HttpResponseRedirect("/")


def collect_movement(request):
    if request.user.is_authenticated and request.user.is_staff:
        ids = request.GET['ids'].split(',')

        # new_inside_zakaz = InsideZakaz(
        #     cost=0,
        #     extra=u'Автосборка: %s' % ids,
        #     segment_new_id=segment_id,
        #
        # )
        # new_inside_zakaz.save()

        today = datetime.date.today()

        for movenent_id in ids:
            movement = MovementOfGoods.objects.get(id=movenent_id)

            if movement.ordered:
                continue

            movements_goods = GoodsInMovement.objects.filter(movement=movement)

            for good in movements_goods:

                ordered_count = 0
                if InsideZakazGoods.objects.filter(zakaz__status=0, zakaz__date_pickup=today,
                                                   zakaz__segment_new=good.item.deckitem.segment_new,
                                                   item=good.item).exists():
                    ordered_count = InsideZakazGoods.objects.filter(zakaz__status=0, zakaz__date_pickup=today,
                                                                    zakaz__segment_new=good.item.deckitem.segment_new,
                                                                    item=good.item).first().quantity

                """
                надо добавить = (кол-во в перемещении) - (уже заказано) + (то что уже в резерве) - (то что на складе) + (среднее для склада)
                  28 (20)            =      16                -  0             +  8                     - 24 (3)

                  24 - 16 - 8 = 0
                """
                need_for_order_count = good.quantity - ordered_count + good.item.vreserve_count_for_automovements() - good.item.quantity_in_reserve_by_warehouse(
                    good.movement.warehouse_donor_id) + good.item.buy_count_3_month_by_warehouse_round(
                    good.movement.warehouse_donor_id)

                if need_for_order_count > 0:
                    if InsideZakaz.objects.filter(status=0, date_pickup=today,
                                                  segment_new=good.item.deckitem.segment_new).exists():
                        inside_zakaz = InsideZakaz.objects.filter(status=0, date_pickup=today,
                                                                  segment_new=good.item.deckitem.segment_new).first()
                        inside_zakaz.extra += u"\r Перемещение: %s" % movenent_id
                        inside_zakaz.save()
                    else:
                        inside_zakaz = InsideZakaz(
                            cost=0,
                            date_pickup=datetime.datetime.now(),
                            extra=u"\r Перемещение: %s" % movenent_id,
                            segment_new=good.item.deckitem.segment_new,
                        )
                        inside_zakaz.save()

                    new_inside_zakaz_line = InsideZakazGoods(
                        zakaz=inside_zakaz,
                        item=good.item,
                        quantity=need_for_order_count
                    )
                    new_inside_zakaz_line.save()

            movement.ordered = True
            movement.save(request)

        return HttpResponseRedirect('/DgJrfdJg/catalog/insidezakaz/')
    return HttpResponseRedirect("/")


def fetch_resources(uri, rel):
    path = os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ""))
    return path


def manage_order_view_pdf(request, zakaz_id):
    if request.user.is_authenticated and request.user.is_staff:
        zakaz = Zakaz.objects.get(id=zakaz_id)
        result, summ_s_dostavkoy, summ_so_skidkoi, skidka, sale, procent, skidka_na_meloch = get_zakaz_parametr(request,
                                                                                                                zakaz)

        zakaz.all_summ = summ_so_skidkoi
        if zakaz.owner.free_buyer:
            zakaz.all_summ = zakaz.summ
        zakaz.paytype = PAY_TYPE_DICT[zakaz.paytype]
        zakaz.dostavkatype = DOSTAVKA_TYPE_DICT[zakaz.dostavkatype]

        zakaz.for_check_sum = int(ceil(float(zakaz.k_oplate()) / 1000) * 1000)
        zakaz.change = int(ceil(float(zakaz.k_oplate()) / 1000) * 1000) - zakaz.k_oplate()

        path = settings.BASE_DIR
        if zakaz.district:
            zakaz.district_name = zakaz.get_district_display()

        if 'signature' in request.GET:
            signature = True
        data = locals()

        response = HttpResponse(content_type='application/pdf')
        response['Content-Desposition'] = 'attachment; filename=super_file.pdf'

        template = get_template('for_pdf.html')
        html = template.render(data)

        pisaFileObject.getNamedFile = lambda self: self.uri
        pdf = pisa.CreatePDF(html, response, encoding='utf-8')
        if pdf.err:
            return HttpResponse('We had some errors <pre>' + html + '</pre>')
        return response


def manage_order_view_invoice(request, zakaz_id):
    if request.user.is_authenticated and request.user.is_staff:
        edo = False
        if request.GET.get('edo'):
            edo = True
        zakaz = Zakaz.objects.get(id=zakaz_id)
        result, summ_s_dostavkoy, summ_so_skidkoi, skidka, sale, procent, skidka_na_meloch = get_zakaz_parametr_static(
            request, zakaz)

        zakaz.all_summ = int(summ_so_skidkoi)
        if zakaz.owner.free_buyer:
            zakaz.all_summ = zakaz.summ
        zakaz.paytype = PAY_TYPE_DICT[zakaz.paytype]
        zakaz.dostavkatype = DOSTAVKA_TYPE_DICT[zakaz.dostavkatype]

        zakaz.for_check_sum = int(ceil(float(zakaz.k_oplate()) / 1000) * 1000)
        zakaz.change = int(ceil(float(zakaz.k_oplate()) / 1000) * 1000) - zakaz.k_oplate()

        path = settings.BASE_DIR
        if zakaz.district:
            zakaz.district_name = zakaz.get_district_display()

        full_sum = summ_so_skidkoi + skidka_na_meloch
        skidka_na_meloch_100 = int(round(skidka_na_meloch, 2) * 100)
        data = locals()
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Desposition'] = 'attachment; filename=invoice_%s.pdf' % zakaz.id

        template = get_template('invoice.html')
        html = template.render(data)

        pisaFileObject.getNamedFile = lambda self: self.uri
        pdf = pisa.CreatePDF(html, response, encoding='utf-8')
        if pdf.err:
            return HttpResponse('We had some errors <pre>' + html + '</pre>')
        return response


def manage_order_view_torg12(request, zakaz_id):
    if request.user.is_authenticated and request.user.is_staff:
        zakaz = Zakaz.objects.get(id=zakaz_id)
        sum_quantity = ZakazGoods.objects.filter(zakaz=zakaz.id).aggregate(sum=Sum('quantity'))['sum']
        result, summ_s_dostavkoy, summ_so_skidkoi, skidka, sale, procent, skidka_na_meloch = get_zakaz_parametr_static(
            request, zakaz)

        zakaz.all_summ = int(summ_so_skidkoi)
        if zakaz.owner.free_buyer:
            zakaz.all_summ = zakaz.summ
        zakaz.paytype = PAY_TYPE_DICT[zakaz.paytype]
        zakaz.dostavkatype = DOSTAVKA_TYPE_DICT[zakaz.dostavkatype]

        zakaz.for_check_sum = int(ceil(float(zakaz.k_oplate()) / 1000) * 1000)
        zakaz.change = int(ceil(float(zakaz.k_oplate()) / 1000) * 1000) - zakaz.k_oplate()

        path = settings.BASE_DIR
        if zakaz.district:
            zakaz.district_name = zakaz.get_district_display()

        full_sum = summ_so_skidkoi + skidka_na_meloch
        skidka_na_meloch_100 = int(round(skidka_na_meloch, 2) * 100)
        data = locals()

        response = render(request, 'torg12.html', data)
        response['Cache-Control'] = 'no-cache, must-revalidate'
        return response


def manage_order_view_inside_pdf_inside(request, zakaz_id):
    if request.user.is_authenticated and request.user.is_staff:
        zakaz = InsideZakaz.objects.get(id=zakaz_id)
        result = []
        data_zakaz = InsideZakazGoods.objects.filter(zakaz=zakaz.id).select_related('segment_new').order_by(
            'item__deckitem__producer').values()
        for j in data_zakaz:
            goods = Item.objects.get(id=j['item_id'])
            if goods.deckitem.cover():
                j['image_url'] = goods.deckitem.cover()[0].thumbnail_inner.url
            j['title'] = goods.deckitem.title
            j['title_en'] = goods.deckitem.title_en
            j['producer'] = goods.deckitem.producer.title
            j['article'] = goods.article
            j['code'] = goods.code
            j['real_price'] = goods.real_price
            j['weight'] = goods.weight

            if j['sale']:
                sale = True
                j['summ'] = (j['real_price'] * j['quantity']) * (1 - (j['sale'] / 100))
            else:
                j['summ'] = (j['real_price'] * j['quantity']) * zakaz.sale_koef

            result.append(j)

        path = settings.BASE_DIR
        data = {
            'zakaz': zakaz,
            'result': result,
            'path': path,
        }

        response = HttpResponse(content_type='application/pdf')
        response["Cache-Control"] = "no-cache"
        response["Accept-Ranges"] = "none"
        response['Content-Desposition'] = 'attachment; filename=super_file.pdf'
        if 'html' in request.GET:
            response = render(request, 'for_inside_pdf_inside_html.html', locals())
            response['Cache-Control'] = 'no-cache, must-revalidate'
            return response

        template = get_template('for_inside_pdf_inside.html')
        html = template.render(data)

        pisaFileObject.getNamedFile = lambda self: self.uri
        pdf = pisa.CreatePDF(html, response, encoding='utf-8')
        if pdf.err:
            return HttpResponse('We had some errors <pre>' + html + '</pre>')
        return response
    return HttpResponseRedirect("/")


def manage_day(request):
    if request.user.is_authenticated and request.user.is_staff:
        zakazs = Zakaz.objects.filter(status__in=[2]).values()
        id_list = []
        for i in zakazs:
            id_list.append(i['id'])
        all_zakaz_goods = ZakazGoods.objects.filter(zakaz__in=id_list).order_by('item').values()
        result = []
        n = 1
        summ = 0
        for j in all_zakaz_goods:
            if int(j['quantity']) == 0:
                continue

            for k in all_zakaz_goods:
                if k['id'] == j['id']:
                    continue
                else:
                    if k['item_id'] == j['item_id']:
                        j['quantity'] = int(j['quantity']) + int(k['quantity'])
                        k['quantity'] = 0

            goods = Item.objects.get(id=j['item_id'])
            j['item'] = goods
            j['number'] = n
            j['real_price'] = j['quantity'] * goods.real_price
            j['producer'] = goods.deckitem.producer
            summ += j['real_price']
            result.append(j)
            n += 1
            result.sort(key=lambda j: j['producer'])

        path = settings.PATH_TO_FONTS
        data = {'result': result, 'path': path, 'summ': summ, 'date_now': datetime.datetime.now()}

        response = HttpResponse(content_type='application/pdf')
        response['Content-Desposition'] = 'attachment; filename=super_file.pdf'

        template = get_template('manage_day_pdf.html')
        html = template.render(data)

        pisaFileObject.getNamedFile = lambda self: self.uri
        pdf = pisa.CreatePDF(html, response, encoding='utf-8')
        if pdf.err:
            return HttpResponse('We had some errors <pre>' + html + '</pre>')
        return response
    return HttpResponseRedirect("/error/")


def manage_month(request):
    if request.user.is_authenticated and request.user.is_staff:
        users = False
        if request.method == 'POST':
            users = Account.objects.all().order_by('username').values()
            month = int(request.POST['month'])
            year = int(request.POST['year'])
            for i in users:
                zakazs = Zakaz.objects.filter(status=6, date__month=month, date__year=year, owner=i['id']).values()
                all_summ = 0
                for j in zakazs:
                    all_summ += j['summ']
                i['all_summ'] = all_summ
                if int(all_summ) > 20000:
                    i['status'] = 'ok'
                else:
                    i['status'] = ''

        response = render(request, 'manage_month.html', {
            'users': users,
        })
        response['Cache-Control'] = 'no-cache, must-revalidate'
        return response

    return HttpResponseRedirect("/")


def order_view(request, zakaz_id):
    dostavka = settings.DOSTAVKA
    autorized = False
    order_need_pay = False
    zakaz = ''
    result = ''
    procent = ''
    skidka = ''
    sale = ''
    summ_so_skidkoi = ''
    repeat_order_modal = True
    if request.user.is_authenticated:
        autorized = True
        if Zakaz.objects.filter(id=zakaz_id, owner=request.user.id):
            zakaz = Zakaz.objects.get(id=zakaz_id)
            result, summ_s_dostavkoy, summ_so_skidkoi, skidka, sale, procent, skidka_na_meloch = get_zakaz_parametr_static(
                request, zakaz)
            if zakaz.paytype == 4 and zakaz.status == 82 and not zakaz.cash_go_to_kassa and not zakaz.paid_client:
                order_need_pay = True
            zakaz.paytype = PAY_TYPE_DICT[zakaz.paytype]
            zakaz.dostavkatype = DOSTAVKA_TYPE_DICT[zakaz.dostavkatype]

            zakaz.status_text = ORDER_STATUS_CLIENT_DICT[zakaz.status]
            dostavka = zakaz.dostavka

            # Если доставка отрицательная, то она считается как скидка
            if dostavka < 0:
                skidka += abs(dostavka)
    if not zakaz:
        return HttpResponseRedirect('/account/orders/')

    response = render(request, 'cart_order_view.html', locals())
    response['Cache-Control'] = 'no-cache, must-revalidate'
    return response


def autoorder_view(request, autozakaz_id):
    autorized = False
    zakaz = ''
    result = []

    if request.user.is_authenticated:
        autorized = True
        if AutoZakaz.objects.filter(id=autozakaz_id, owner=request.user.id):
            zakaz = AutoZakaz.objects.get(id=autozakaz_id)

            now_date = datetime.datetime.now()

            if zakaz.last_order:
                order_date = zakaz.last_order + datetime.timedelta(days=zakaz.repeat_period)
            else:
                order_date = zakaz.create_date + datetime.timedelta(days=zakaz.repeat_period)

            days = (order_date - now_date).days

            data = AutoZakazGoods.objects.filter(zakaz=zakaz.id).values()
            n = 1
            for j in data:
                goods = Item.objects.get(id=j['item_id'])
                j['goods'] = goods
                j['number'] = n
                j['price'] = goods.current_price()

                result.append(j)
                n += 1

            response = render(request, 'cart_autoorder_view.html', locals())
            response['Cache-Control'] = 'no-cache, must-revalidate'
            return response
    return HttpResponseRedirect('/account/orders/')


def orders(request, page=1):
    autorized = False
    zakazs = ''

    element_to_page = 6
    if 'page' in request.GET:
        page = int(request.GET['page'])

    start_query = int(page) * int(element_to_page) - int(element_to_page)
    stop_query = int(page) * int(element_to_page)

    iteration_count = 0

    page_var = {'pages': []}

    if request.user.is_authenticated:
        autorized = True
        autozakazs = AutoZakaz.objects.filter(owner=request.user.id, active=1).order_by('-create_date').values()
        now_date = datetime.datetime.now()

        for i in autozakazs:
            if i['last_order']:
                order_date = i['last_order'] + datetime.timedelta(days=i['repeat_period'])
            else:
                order_date = i['create_date'] + datetime.timedelta(days=i['repeat_period'])
            i['days'] = (order_date - now_date).days

        zakazs = Zakaz.objects.filter(owner=request.user.id).order_by('-date')
        result_count = zakazs.count()
        query = zakazs.values()

        if result_count > 20:
            results = query[start_query:stop_query]
            if result_count % element_to_page:
                iteration_count = math.trunc(result_count / element_to_page) + 1
            else:
                iteration_count = math.trunc(result_count / element_to_page)
            page_var['page_count'] = iteration_count

            if page == 1:  # первая страница
                page_var['next_page'] = page + 1
                page_var['first_page'] = True
                if iteration_count > 3:
                    page_var['page_count'] = 3
                else:
                    page_var['page_count'] = iteration_count

                for i in range(int(page_var['page_count'])):
                    page_var['pages'].append(i + 1)

            elif page == iteration_count:  # последняя страница
                page_var['prev_page'] = page - 1
                page_var['not_next_page'] = True
                page_var['last_page'] = True
                if iteration_count > 3:
                    page_var['page_count'] = 3
                    for i in range(int(page_var['page_count'])):
                        page_var['pages'].append(page - 2 + i)
                elif iteration_count == 3:
                    page_var['page_count'] = iteration_count
                    for i in range(int(page_var['page_count'])):
                        page_var['pages'].append(page - 2 + i)
                else:
                    page_var['page_count'] = iteration_count
                    for i in range(int(page_var['page_count'])):
                        page_var['pages'].append(page - 1 + i)

            else:  # промежуточная страница
                page_var['next_page'] = page + 1
                page_var['prev_page'] = page - 1
                page_var['page_count'] = 5
                for i in range(int(page_var['page_count'])):
                    this_page = page - 2 + i
                    if this_page > 0 and this_page <= iteration_count:
                        page_var['pages'].append(page - 2 + i)

        else:
            results = query.order_by('-date')
            stop_query = result_count

        for i in results:
            i['status_text'] = ORDER_STATUS_CLIENT_DICT[i['status']]
            zakaz = Zakaz.objects.get(id=i['id'])
            result, summ_s_dostavkoy, summ_so_skidkoi, skidka, sale, procent, skidka_na_meloch = get_zakaz_parametr_static(
                request, zakaz)
            i['summ'] = summ_so_skidkoi

        if stop_query > result_count:
            stop_query = result_count

    pages = range(iteration_count)

    start_item = start_query
    end_item = stop_query

    response = render(request, 'cart_orders.html', locals())
    response['Cache-Control'] = 'no-cache, must-revalidate'
    return response


def calculate_buy_rate(request):
    deckitems = Deckitem.objects.filter(active=True).values()

    for deckitem in deckitems:
        this_deckitem = Deckitem.objects.get(id=deckitem['id'])
        max_item = Item.objects.filter(deckitem=deckitem['id']).aggregate(Max('number_of_purchases'))
        this_deckitem.number_of_purchases = max_item['number_of_purchases__max']
        this_deckitem.save()

    response = render(request, 'result__calculate_buy_rate.html', {})
    response['Cache-Control'] = 'no-cache, must-revalidate'
    return response


def update_zakaz(request, zakaz_id):
    zakaz = Zakaz.objects.get(id=zakaz_id)
    data = ZakazGoods.objects.filter(zakaz=zakaz.id).values()
    summ_k_oplate = 0
    summ_cost = 0
    for j in data:
        line = ZakazGoods.objects.get(id=j['id'])
        item = line.item

        if line.zakaz.owner.optovik:
            line.summ = round(item.current_price_opt() * line.quantity, 2)
        elif line.zakaz.owner.zavodchik:
            line.summ = round(item.current_price_zavodchik() * line.quantity, 2)
        else:
            line.summ = round(item.current_price() * line.quantity, 2)
        line.save()

        summ_k_oplate += line.summ
        summ_cost += j['cost']

    zakaz.summ = summ_k_oplate
    zakaz.cost = summ_cost
    zakaz.revenue = (zakaz.summ * zakaz.sale_koef) - summ_cost
    zakaz.save()
    return HttpResponseRedirect('/DgJrfdJg/catalog/zakaz/%s/' % zakaz_id)


def update_insidezakaz(request, zakaz_id):
    zakaz = InsideZakaz.objects.get(id=zakaz_id)
    data = InsideZakazGoods.objects.filter(zakaz=zakaz.id).values()
    summ_cost = 0
    for j in data:
        line = InsideZakazGoods.objects.get(id=j['id'])
        line.cost = float(line.quantity * line.item.real_price) * line.zakaz.sale_koef
        line.save()
        summ_cost += line.cost

    zakaz.cost = summ_cost
    zakaz.save()
    return HttpResponseRedirect('/DgJrfdJg/catalog/insidezakaz/%s/' % zakaz_id)


def get_zakaz_parametr(request, zakaz):
    result = []
    n = 1
    summ_so_skidkoi = 0
    sale = False
    data = ZakazGoods.objects.filter(zakaz=zakaz.id)
    procent = 0

    for j in data.values():
        goods = Item.objects.get(id=j['item_id'])
        line = ZakazGoods.objects.get(id=j['id'])
        j['goods'] = goods
        j['number'] = n
        if line.zakaz.owner.optovik:
            j['real_sum'] = goods.current_price_opt() * j['quantity']
            j['price'] = goods.current_price_opt()
        elif line.zakaz.owner.zavodchik:
            j['real_sum'] = goods.current_price_zavodchik() * j['quantity']
            j['price'] = goods.current_price_zavodchik()
        else:
            j['real_sum'] = goods.current_price() * j['quantity']
            j['price'] = goods.current_price()

        if j['sale'] or j['sale'] == 0:
            sale = True
            j['price_sale'] = round(j['price'] * (float(100 - j['sale']) / 100), 2)
            j['summ_sale'] = round(j['price_sale'] * j['quantity'], 2)
        else:
            j['price_sale'] = round(j['price'] * zakaz.sale_koef, 2)
            j['summ_sale'] = round(j['price_sale'] * j['quantity'], 2)

        summ_so_skidkoi += j['summ_sale']
        result.append(j)
        n += 1

    summ_s_dostavkoy = zakaz.summ + zakaz.dostavka
    summ_so_skidkoi = round(summ_so_skidkoi + zakaz.dostavka, 2)

    skidka = summ_s_dostavkoy - summ_so_skidkoi

    skidka_na_meloch = False

    if zakaz.paytype != 4:
        skidka_na_meloch = summ_so_skidkoi - int(summ_so_skidkoi)
        if skidka_na_meloch < summ_so_skidkoi:
            summ_so_skidkoi = int(summ_so_skidkoi)

    if int(zakaz.sale_koef) != 1:
        sale = True
        procent = zakaz.sale_koef
    return result, summ_s_dostavkoy, summ_so_skidkoi, skidka, sale, procent, skidka_na_meloch


def get_zakaz_parametr_static(request, zakaz):
    result = []
    n = 1
    summ_so_skidkoi = 0
    sale = False
    data = ZakazGoods.objects.filter(zakaz=zakaz.id)
    procent = 0

    for j in data.values():
        goods = Item.objects.get(id=j['item_id'])
        line = ZakazGoods.objects.get(id=j['id'])
        j['number'] = n
        j['goods'] = goods
        # if line.zakaz.owner.optovik:
        # elif line.zakaz.owner.zavodchik:
        # else:
        if j['quantity'] and j['quantity'] != 0:
            j['price'] = j['summ'] / j['quantity']
        else:
            j['price'] = 0

        if j['sale'] or j['sale'] == 0:
            sale = True
            j['price_sale'] = round(j['price'] * (float(100 - j['sale']) / 100), 2)
        elif zakaz.sale_koef and zakaz.sale_koef != 1:
            sale = True
            procent = round((1 - zakaz.sale_koef) * 100, 1)
            if procent - int(procent) == 0:
                procent = int(procent)
            j['price_sale'] = round(j['price'] * zakaz.sale_koef, 2)
        else:
            j['price_sale'] = round(j['price'], 2)
        j['summ_sale'] = round(j['price_sale'] * j['quantity'], 2)

        summ_so_skidkoi += j['summ_sale']
        result.append(j)
        n += 1

    if zakaz.dostavka >= 0:
        summ_s_dostavkoy = zakaz.summ + zakaz.dostavka
    else:
        summ_s_dostavkoy = zakaz.summ
    summ_so_skidkoi = round(summ_so_skidkoi + zakaz.dostavka, 2)

    skidka = summ_s_dostavkoy - summ_so_skidkoi

    skidka_na_meloch = False

    if zakaz.paytype != 4:
        skidka_na_meloch = summ_so_skidkoi - int(summ_so_skidkoi)
        if skidka_na_meloch < summ_so_skidkoi:
            summ_so_skidkoi = int(summ_so_skidkoi)

    return result, summ_s_dostavkoy, summ_so_skidkoi, skidka, sale, procent, skidka_na_meloch


def captcha_refresh(request):
    """ Return json with new captcha for ajax refresh request """
    if not request.is_ajax():
        raise Http404
    challenge, response = conf.settings.get_challenge()()
    store = CaptchaStore.objects.create(challenge=challenge, response=response)
    new_key = store.hashkey

    image = reverse('captcha-image', kwargs=dict(key=new_key))
    to_json_response = {
        'key': new_key,
        'image_url': image,
    }
    return HttpResponse(json.dumps(to_json_response), content_type='application/json')


@csrf_exempt
def komtet_success(request):
    data = json.loads(request.body)
    id = data.get('id', None)
    external_id = data.get('external_id', None)
    fiscal_data = data.get('fiscal_data', None)
    if external_id:
        if Zakaz.objects.filter(id=external_id).exists():
            order = Zakaz.objects.get(id=external_id)
            order.f_state = 2
            order.f_response = fiscal_data
            order.save()
    return HttpResponse(status=200)


@csrf_exempt
def komtet_fail(request):
    data = json.loads(request.body)
    id = data.get('id', None)
    external_id = data.get('external_id', None)
    error_description = data.get('error_description', None)
    if external_id:
        if Zakaz.objects.filter(id=external_id).exists():
            order = Zakaz.objects.get(id=external_id)
            order.f_state = 3
            order.f_response = error_description
            order.save()
    return HttpResponse(status=200)


@csrf_exempt
def get_item_availability_table(request):
    try:
        warehouses = WareHouse.objects.all()
        is_grouped = request.GET.get('is-grouped')
        if is_grouped is not None:
            deckitem_id = request.GET.get('deckitem-id')
            deckitem = Deckitem.objects.get(id=deckitem_id)
            html_content = render_to_string('item_availability.html', {'deckitem': deckitem, 'warehouses': warehouses})
        else:
            item_id = request.GET.get('item-id')
            item = Item.objects.get(id=item_id)
            html_content = render_to_string('item_availability_no_group.html', {'item': item, 'warehouses': warehouses})
    except:
        html_content = 'Не удалось загрузить таблицу наличия товара в результате ошибки на стороне сервера'
    return HttpResponse(html_content)
