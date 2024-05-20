# -*- coding: utf-8 -*-
import csv
from django_tables2.config import RequestConfig
import os

import requests
import jwt

import hashlib
import json
import urllib
import ssl
from django.shortcuts import redirect

if False:
    from typing import List

from core.mail import htmlmail_sender
from core.tables import ZakazTable, InsideZakazTable, ZakazTableToday, ZakazTableTodayAdmin, ZakazTableAdmin, InsideZakazTableTodayAdmin, InsideZakazTableToday, InsideZakazTableAdmin
from django.contrib.admin.views.main import ChangeList
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db.models import Q
from django.contrib import messages
from django.core.paginator import Paginator

from django.template import RequestContext, loader, Context
from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.models import User
from core.models import *
from catalog.models import *
from news.models import *
from django.contrib import auth
from django.conf import settings
from django.apps import apps
from django import forms
from captcha.fields import CaptchaField
from django.core.mail import send_mail
import django.utils
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from operator import itemgetter
from django.contrib.admin.views.decorators import staff_member_required
import datetime

from .oauth.decorators import oauth_state_handler, oauth_error_handler
from .oauth.utils import create_account
from .search import sphinx_search


class RegistrationForm(forms.Form):
    captcha = CaptchaField()


class CaptchaForm(forms.Form):
    captcha = CaptchaField()


def is_valid_email(email):
    try:
        validate_email( email )
        return True
    except ValidationError:
        return False


def my_custom_404_view(request, exception):
    response = render(request, "404.html")
    response.status_code = 404
    return response


def my_custom_500_view(request):
    response = render(request, "500.html")
    response.status_code = 500
    return response


def start(request):
    main_menu = Menu.objects.filter(menu_type=0).order_by('position')
    flatpage = get_object_or_404(Static, link='home_main')
    current_link = ''
    last_news = New.objects.filter(action=False, status=2).order_by('-date')[0:2]

    bottom_1 = get_object_or_404(Static, link='home_bottom_1')
    bottom_2 = get_object_or_404(Static, link='home_bottom_2')
    bottom_3 = get_object_or_404(Static, link='home_bottom_3')

    last_review = SocialReview.objects.all()[0:3]

    producer_main = Producer.objects.filter(active=True, on_main=True).order_by('sort_main')

    items_royal = Item.objects.filter(active=True, deckitem__active=True, availability__in=[3, 10], on_main=True, deckitem__producer=16).order_by('?')[0:2]
    items_1 = Item.objects.filter(active=True, deckitem__active=True, availability__in=[3, 10], on_main=True).exclude(deckitem__producer=16).order_by('?')[0:1]

    city = 'город не определён'
    try:
        city = request.session['curCity']
    except Exception:
        pass
    
    items_new = Item.objects\
        .filter(
            Q(new=True) &
            Q(active=True) &
            Q(temporarily_unavailable=False)
        )\
        .exclude(availability=0)\
        .order_by('-date_created')\
        .order_by('?')[:6]

    itemsales = ItemSale.objects\
        .filter(date_end__gte=datetime.datetime.now(), show=True)\
        .order_by('?')\
        .select_related('item')\
        .values_list('item__id', flat=True)
    sort_itemsales = ItemSale.objects\
        .filter(date_end__gte=datetime.datetime.now(), show=True)\
        .order_by('?')\
        .select_related('item')\
        .values_list('id', flat=True)
    items_sale = list(Item.objects.filter(id__in=itemsales, active=True).distinct()[:6])
    items_sale.sort(key=lambda i: i.itemsale_set.filter(id__in=sort_itemsales).distinct().first().sale)

    response = render(request, 'new_index.html', locals())
    # response['Cache-Control'] = 'no-cache, must-revalidate'
    return response

def setCity(request):
    if request.method == 'POST':
        city = request.POST['city']
        request.session['curCity'] = city
        return redirect(request.META.get('HTTP_REFERER'))


def change_cookie_status(request):
    cookie_status = False
    request.session["cookie_status"] = cookie_status
    return HttpResponse()


def change_basket_of_goods_status(request):
    if request.user.is_authenticated:
        request.user.basket_of_goods = True
        request.user.save()
    else:
        request.session['basket_of_goods'] = True
    return HttpResponse()


def royal_canin(request, template=False):
    response = render(request, 'royalcanin/royal_canin.html', locals())
    response['Cache-Control'] = 'no-cache, must-revalidate'
    return response


def royal_dogs(request, template=False):
    if template:
        response = render(request, 'royal_dogs_%s.html' % template, locals())
    else:
        response = render(request, 'royal_dogs.html', locals())
    response['Cache-Control'] = 'no-cache, must-revalidate'
    return response


def static(request, link):
    flatpage = get_object_or_404(Static, link=link)
    current_link = link
    response = render(request, 'static.html', locals())
    response['Cache-Control'] = 'no-cache, must-revalidate'
    return response


def review(request, page=1):
    element_to_page = 6

    if 'page' in request.GET:
        page = int(request.GET['page'])

    start_query = int(page)*int(element_to_page) - int(element_to_page)
    stop_query = int(page)*int(element_to_page)

    iteration_count = 0

    reviews_count = SocialReview.objects.all().count()
    result_count = reviews_count

    news_items = SocialReview.objects.all()
    query = news_items

    page_var = {'pages': []}

    if result_count > 6:
        result = query[start_query:stop_query]
        if result_count % element_to_page:
            iteration_count = result_count / element_to_page + 1
        else:
            iteration_count = result_count / element_to_page
        page_var['page_count'] = iteration_count

        if page == 1:  # первая страница
            page_var['next_page'] = page+1
            page_var['first_page'] = True
            if iteration_count > 3:
                page_var['page_count'] = 3
            else:
                page_var['page_count'] = iteration_count

            for i in range(int(page_var['page_count'])):
                page_var['pages'].append(i+1)

        elif page == iteration_count:  # последняя страница
            page_var['prev_page'] = page-1
            page_var['not_next_page'] = True
            page_var['last_page'] = True
            if iteration_count > 3:
                page_var['page_count'] = 3
                for i in range(int(page_var['page_count'])):
                    page_var['pages'].append(page-2+i)
            elif iteration_count == 3:
                page_var['page_count'] = iteration_count
                for i in range(int(page_var['page_count'])):
                    page_var['pages'].append(page-2+i)
            else:
                page_var['page_count'] = iteration_count
                for i in range(int(page_var['page_count'])):
                    page_var['pages'].append(page-1+i)

        else:  # промежуточная страница
            page_var['next_page'] = page+1
            page_var['prev_page'] = page-1
            page_var['page_count'] = 5
            for i in range(int(page_var['page_count'])):
                this_page = page-2+i
                if this_page > 0 and this_page <= iteration_count:
                    page_var['pages'].append(page-2+i)

    else:
        result = query.order_by('-date')
        stop_query = result_count

    if stop_query > result_count:
        stop_query = result_count

    reviews = result
    pages = range(iteration_count)

    start_item = start_query
    end_item = stop_query

    last_review = reviews
    current_link = 'reviews'
    response = render(request, 'review.html', locals())
    response['Cache-Control'] = 'no-cache, must-revalidate'
    return response


def help_aliya(request):
    return HttpResponsePermanentRedirect('/')


def faq(request):
    form = CaptchaForm(request.POST or None)
    errors = {}
    data = {}

    sovety = Vopros_otvet.objects.all().order_by('-date').values()
    number_action = 'false'
    if request.method == 'GET':
        try:
            number_action = request.GET['otvet']
        except:
            number_action = 'false'

    if request.method == 'POST':
        if request.POST['name'].strip():
            data['name'] = request.POST['name'].strip()
        else:
            errors['name'] = 'true'

        if request.POST['text'].strip():
            data['text'] = request.POST['text'].strip()
        else:
            errors['text'] = 'true'

        if request.POST['email'].strip():
            data['email'] = request.POST['email'].strip()
        else:
            errors['email'] = 'true'

        if not errors and form.is_valid():
            ## отправка письма
            subject = _("BOnPOc")
            message_template = loader.get_template('messages/send_email.txt')
            message_context = Context({
                'data': data,
            })
            message = message_template.render(message_context)
            send_mail(subject, message, settings.SENDER_EMAIL, [settings.REVIEW_EMAIL])
            return HttpResponseRedirect("/sendfaqtrue/")
        else:
            errors['captcha'] = 'true'

    response = render(request, 'faq.html', {
        'menu_active': 'faq',
        "errors": errors,
        "form": form,
        'data': data,
        'sovety': sovety,
        'number_action': number_action,
    })
    response['Cache-Control'] = 'no-cache, must-revalidate'
    return response


def contacts(request):
    form = CaptchaForm(request.POST or None)
    errors = {}
    data = {}

    static = Static.objects.get(link='contacts')
    if request.method == 'POST':
        if request.POST['name'].strip():
            data['name'] = request.POST['name'].strip()
        else:
            errors['name'] = 'true'

        if request.POST['text'].strip():
            data['text'] = request.POST['text'].strip()
        else:
            errors['text'] = 'true'

        if request.POST['email'].strip():
            data['email'] = request.POST['email'].strip()
        else:
            errors['email'] = 'true'
        if not form.is_valid():
            errors['captcha'] = 'true'
        if not errors:
            ## отправка письма
            subject = _("HoBoe nucbMo [kostochka.ru]")
            message_template = loader.get_template('messages/send_email2.txt')
            message_context = Context({
                'data': data,
            })
            message = message_template.render(message_context)
            send_mail(subject, message, settings.SENDER_EMAIL, [settings.ORDER_EMAIL])
            return HttpResponseRedirect("/sendcontacttrue/")

    response = render(request, 'contacts.html', {
        'current_link': 'contacts',
        "errors": errors,
        "static": static,
        "form": form,
        'data': data
    })
    response['Cache-Control'] = 'no-cache, must-revalidate'
    return response


@csrf_exempt
def search_ajax(request):
    q = request.POST.get('q')
    if q is not None:
        search_split = q.split(' ')
        deckitems = Deckitem.objects.filter(active=True)
        for x in search_split:
            match_name = x
            if match_name:
                deckitems = deckitems.filter(
                    Q(title__icontains=match_name) |
                    Q(title_en__icontains=match_name) | 
                    Q(description__icontains=match_name) |
                    Q(composition_title__icontains=match_name) | 
                    Q(tag__title__icontains=match_name) | 
                    Q(producer__title__icontains=match_name)
                ).distinct()
        
        # deckitems = sphinx_search(
        #     model_class=Deckitem,
        #     query=q,
        #     limits=(0, 5),
        #     weights={
        #         'title': 10,
        #         'title_en': 7,
        #         'description': 4,
        #         'composition_title': 4,
        #         'tag_title': 4,
        #         'producer_title': 4
        #     }
        # )
        # getting wildcard deckitems results
        if deckitems.count() == 0:
            deckitems = Deckitem.objects.filter(active=True)
        deckitems = deckitems.order_by('-availability', 'order', 'title')[:5]

        search_split = q.split(' ')
        tags = Tag.objects.all()
        for x in search_split:
            match_name = x
            if match_name:
                tags = tags.filter(
                    Q(title__icontains=match_name) |
                    Q(title_search__icontains=match_name)
                ).distinct()
        # getting wildcard tags results
        # if tags.count() == 0:
        #     tags = Tag.objects.all()
        tags = tags.order_by('sort', 'title')[:3]
    else:
        deckitems = Deckitem.objects.filter(active=True)
        deckitems = deckitems.order_by('-availability', 'order', 'title')[:5]
        tags = Tag.objects.all().order_by('sort', 'title')[:3]
    result = {
        'deckitems': [],
        'tags': []
    }
    for item in deckitems.values()[:5]:
        this_item = Deckitem.objects.get(id=item['id'])
        if this_item.search_thumb():
            photo = this_item.search_thumb()
        else:
            photo = '<img src="/static/kostochka38/images/noimage.png" height="60px">'
        title = item['title']
        if len(item['title']) > 99:
            title = item['title'][0:99] + '...'
        t_result = {
            'id': item['id'],
            'title': title,
            'title_en': item['title_en'],
            'producer': item['producer_id'],
            'link': this_item.get_absolute_url(),
            'image': photo,
            'category_link': this_item.tag.link,
            'category_title': this_item.tag.title_search or this_item.tag.title
        }
        result['deckitems'].append(t_result)
    for item in tags.values():
        result['tags'].append({
            'link': item['link'],
            'title': item.get('title_search') or item['title']
        })
    result['result_code'] = 1
    return HttpResponse(json.dumps(result), content_type='application/javascript')


def search(request):
    q = request.GET.get('q')
    if q is not None:
        search_split = q.split(' ')
        queryset = Deckitem.objects.filter(active=True)
        for x in search_split:
            match_name = x
            if match_name:
                queryset = queryset.filter(
                    Q(title__icontains=match_name) |
                    Q(title_en__icontains=match_name) | 
                    Q(description__icontains=match_name) |
                    Q(composition_title__icontains=match_name) | 
                    Q(tag__title__icontains=match_name) | 
                    Q(producer__title__icontains=match_name)
                ).distinct()
        
        # queryset = sphinx_search(
        #     model_class=Deckitem,
        #     query=q,
        #     limits=(0, 30),
        #     weights={
        #         'title': 10,
        #         'title_en': 7,
        #         'description': 4,
        #         'composition_title': 4,
        #         'tag_title': 4,
        #         'producer_title': 4
        #     }
        # )
        # getting wildcard deckitems results
        if queryset.count() == 0:
            queryset = Deckitem.objects.filter(active=True)
        queryset = queryset.order_by('-availability', 'order', 'title')[:30]
    else:
        queryset = Deckitem.objects.filter(active=True)
        queryset = queryset.order_by('-availability', 'order', 'title')[:30]

    response = render(request, 'search.html', {
        "items": queryset,
        'q': q
    })
    response['Cache-Control'] = 'no-cache, must-revalidate'
    return response


def upload_image(request):
    date = datetime.datetime.now()
    user_name = request.user.username
    hashstring = str(date) + str(user_name)
    alloved_files = ('.jpg', '.jpeg', '.png', '.gif', '.JPG', '.JPEG', '.PNG', '.GIF')
    path = settings.MEDIA_ROOT

    for image_file in request.FILES:
        filename = request.FILES[image_file].name
        name, ext = os.path.splitext(filename)
        image_name = 'img-' + hashlib.sha224(hashstring).hexdigest() + ext
        if ext not in alloved_files:
            continue
        if filename == '':
            continue
        content = request.FILES[image_file].read()
        filename = image_name
        f = open(path + '/' + filename, 'wb')
        try:
            f.write(content)
        finally:
            f.close()
        source = '/images/'
        link_for_images = source + filename
        return render("done.html", {
            "link_for_images": link_for_images
        })


def error_404(request):
    response = render(request, '404.html', {})
    return response


@csrf_exempt
def entry(request):
    if request.method == 'POST':
        username = request.POST['login']
        password = request.POST['pass']
        user = auth.authenticate(username=username, password=password)

        if user is not None and user.is_active:
            auth.login(request, user)
            result = user.id

            ##перевод существующий заказа на залогиненного пользователя
            user_a_id = ''
            if "user_a_id" in request.session:
                user_a_id = request.session["user_a_id"]

            if TempZakaz.objects.filter(hash=user_a_id):
                if TempZakaz.objects.filter(owner=request.user.id):
                    zakaz = TempZakaz.objects.get(owner=request.user.id)
                    TempZakazGoods.objects.filter(zakaz=zakaz.id).delete()
                    zakaz.delete()
                zakaz = TempZakaz.objects.get(hash=user_a_id)
                zakaz.owner_id = request.user.id
                zakaz.save()
                ## конец перевода заказа
        else:
            result = '0'

        return HttpResponse(json.dumps(result), content_type='application/javascript')
    else:
        return HttpResponseRedirect('/account/login/')


@csrf_exempt
def login(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('/')
    return render(request, 'account/login.html', locals())


@csrf_exempt
def registration(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('/')
    return render(request, 'account/registration.html', locals())


def logout(request):
    auth.logout(request)
    return HttpResponseRedirect("/account/logout/complete/")


@oauth_state_handler
@oauth_error_handler
def newuser_vk(request):
    code = request.GET.get('code')
    endpoint = 'https://oauth.vk.com/access_token'
    payload = {
        'client_id': '7927466',
        'client_secret': '7fvhYU0c10mXNWcCkyFh',
        'code': code,
        'redirect_uri': 'https://kostochka38.ru/account/newuser/vk/'
    }
    response = requests.post(endpoint, params=payload)
    response_json = response.json()
    username = response_json.get('email')
    create_account(username, request)
    return render(request, 'newuser.html')


@oauth_state_handler
@oauth_error_handler
def newuser_ok(request):
    # Получение токена доступа
    code = request.GET.get('code')
    endpoint = 'https://api.ok.ru/oauth/token.do'
    payload = {
        'code': code,
        'client_id': '512001028834',
        'client_secret': '8D1E503EB28826DCF14ED2F5',
        'redirect_uri': 'https://kostochka38.ru/account/newuser/ok/',
        'grant_type': 'authorization_code'
    }
    response = requests.post(endpoint, params=payload)
    response_json = response.json()
    access_token = response_json['access_token']
    # Получение адреса электронной почты
    endpoint = 'https://api.ok.ru/fb.do'
    payload = {
        'method': 'users.getCurrentUser',
        'application_id': '512001028834',
        'application_key': 'CDODLEKGDIHBABABA',
        'application_secret_key': '8D1E503EB28826DCF14ED2F5',
        'fields': 'EMAIL'
    }
    payload['sig'] = hashlib.md5(
        ''.join(map(lambda k: '%s=%s' % (k, payload[k]), sorted(payload))) +\
        hashlib.md5(access_token + '8D1E503EB28826DCF14ED2F5').hexdigest()
    ).hexdigest()
    payload['access_token'] = access_token
    response = requests.get(endpoint, params=payload)
    response_json = response.json()
    username = response_json['email']
    create_account(username, request)
    return render(request, 'newuser.html')


@oauth_state_handler
@oauth_error_handler
def newuser_fb(request):
    # Получение токена доступа
    code = request.GET.get('code')
    endpoint = 'https://graph.facebook.com/v11.0/oauth/access_token'
    payload = {
        'client_id': '533851551368467',
        'redirect_uri': 'https://kostochka38.ru/account/newuser/fb/',
        'client_secret': '4dc48bea32475c7fc6966d3b5a2dd154',
        'code': code
    }
    response = requests.post(endpoint, params=payload)
    response_json = response.json()
    access_token = response_json['access_token']
    # Получение адреса электронной почты
    endpoint = 'https://graph.facebook.com/v11.0/me'
    payload = {
        'access_token': access_token,
        'fields': 'email'
    }
    response = requests.get(endpoint, params=payload)
    response_json = response.json()
    username = response_json['email']
    create_account(username, request)
    return render(request, 'newuser.html')


@oauth_state_handler
@oauth_error_handler
def newuser_google(request):
    # Получение токена доступа
    code = request.GET.get('code')
    endpoint = 'https://oauth2.googleapis.com/token'
    payload = {
        'client_id': '381129474137-gaje4iq8s7ccqh2ij4rk5o0ep64m1m0f.apps.googleusercontent.com',
        'client_secret': 'UkPh61aDrlBTLlQlVrSch0_9',
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': 'https://kostochka38.ru/account/newuser/google/'
    }
    response = requests.post(endpoint, params=payload)
    response_json = response.json()
    id_token = response_json['id_token']
    # Получение адреса электронной почты
    id_token_decoded = jwt.decode(id_token, verify=False, options={'verify_signature': False})
    username = id_token_decoded['email']
    create_account(username, request)
    return render(request, 'newuser.html')


@csrf_exempt
def newuser(request):
        # form = RegistrationForm(request.POST or None)
        errors = {}
        result = {}

        if request.method == 'POST':

            # test password
            if not request.POST['pass'].strip() and len(request.POST['pass'].strip()) < 3:
                errors['pass'] = "true"
                errors['text'] = u"Слишком короткий пароль, минимум 4 символа"
            else:
                password_1 = request.POST['pass'].strip()
                password_2 = request.POST['pass2'].strip()
                if not password_1 == password_2:
                    errors['pass2'] = "true"
                    errors['text'] = u"Введенные пароли не совпадают"

            # if not form.is_valid():
            #     errors['captcha'] = 'true'
            #     errors['text'] = u"Введите правильно символы с картинки."

            # test username
            if not request.POST['login'].strip() or len(request.POST['login'].strip()) < 4:
                errors['login'] = "true"
                errors['text'] = u"Введите корректный e-mail."
            else:
                if Account.objects.filter(username=request.POST['login']):
                    errors['login'] = "true"
                    errors[
                        'text'] = u"Е-mail уже используется. <a class='recovery-link' href='/account/password/forget/'>Восстановить пароль</a>"

            if not is_valid_email(request.POST['login'].strip()):
                errors['login'] = "true"
                errors['text'] = u"Введите корректный e-mail."

            username = request.POST['login'].strip()

            if request.POST.get('subscribe') == 'true':
                unsubscribed = False
            else:
                unsubscribed = True

            if not errors:
                # form = form.cleaned_data
                print('try to create new user')
                new_user = Account(
                    username=username,
                    email=username,
                    unsubscribed=unsubscribed,
                    # first_name=request.POST.get('first_name', '').strip(),
                )
                print('new user created')
                new_user.set_password(password_2)
                new_user.save()
                print('new user saved')

                user = auth.authenticate(username=username, password=password_2)
                auth.login(request, user)

                user_a_id = ''
                if "user_a_id" in request.session:
                    user_a_id = request.session["user_a_id"]

                if TempZakaz.objects.filter(hash=user_a_id):
                    zakaz = TempZakaz.objects.get(hash=user_a_id)
                    zakaz.owner_id = new_user.id
                    zakaz.save()

                data = {
                    'username': username,
                    'password': password_2,
                    'user': request.user
                }
                htmlmail_sender('registration', data, username, request.user)
                result['response'] = '1'
            else:
                result['error'] = errors
                result['response'] = '0'
        return HttpResponse(json.dumps(result), content_type='application/javascript')


@csrf_exempt
def password_change(request):
    error_old_password = ''
    error_new_password = ''
    if request.user.is_authenticated:
        if request.method == 'POST':
            user = request.user
            username = user.username
            old_password = request.POST['old_password']
            new_password = request.POST['new_password']
            new_password2 = request.POST['new_password2']
            check = user.check_password(old_password)
            if not check:
                error_old_password = 'true'
            if not (new_password == new_password2) or not new_password:
                error_new_password = 'true'

            if not error_old_password and not error_new_password:
                user.set_password(new_password)
                user.save()
                return HttpResponseRedirect("/account/password/change/complete/")

        return render(request, 'account/password_change.html', {
            "error_old_password": error_old_password,
            "error_new_password": error_new_password,
            "user": request.user})
    else:
        return HttpResponseRedirect("/error/")


@csrf_exempt
def password_forget(request):
    result = '0'
    if not request.user.is_authenticated:
        if request.method == 'POST':
            email = request.POST['login']

            check = Account.objects.filter(username=email)
            if check:
                user = Account.objects.get(username=email)
                user_email = user.email
                username = user.username

                date = datetime.datetime.now()
                hashstring = str(date) + str(username)
                hash_code = hashlib.sha224(hashstring).hexdigest()

                p = Restore(
                    user=user,
                    rdate=date,
                    hash=hash_code
                )
                p.save()

                htmlmail_password_forget_data = {
                    'data': p
                }
                htmlmail_sender('password_forget', htmlmail_password_forget_data,
                                user_email, user)  # высылаем письмо с инструкцией

                result = 'true'

    return HttpResponse(json.dumps(result), content_type='application/javascript')


@csrf_exempt
def password_restore(request, user_id, hash_code):
    key = ''
    error_new_password = ''
    check = Restore.objects.filter(user_id=user_id, hash=hash_code, used=False)

    if check:
        check = Restore.objects.get(user_id=user_id, hash=hash_code, used=False)
        if request.method == 'POST':
            new_password = request.POST['new_password']
            new_password2 = request.POST['new_password2']

            if not (new_password == new_password2) or not new_password:
                error_new_password = 'true'

            if not error_new_password:
                user = Account.objects.get(id=user_id)
                user.set_password(new_password)
                user.save()
                key = 'true'
                check.used = 1
                check.save()
        return render(request, 'account/password_restore.html', {
            "key": key,
            "error_new_password": error_new_password,
        })
    else:
        return HttpResponseRedirect('/')


@csrf_exempt
def notifications(request):
    n_settings = {}

    autorized = False
    if request.user.is_authenticated:
        autorized = True
    saved = False
    if request.method == 'POST':
        for link in CLIENT_MAIL_LIST:
            if not Mail.objects.filter(link=link).exists():
                continue
            mail = Mail.objects.get(link=link)
            notifications, result = NotificationSettings.objects.get_or_create(
                user_id=request.user.id,
                mail_id=mail.id
            )
            notifications.send = link in request.POST
            notifications.save()

        if 'subscriberlist' in request.POST:
            request.user.unsubscribed = False
        else:
            request.user.unsubscribed = True
        request.user.save()

        saved = True

    for link in CLIENT_MAIL_LIST:
        if not Mail.objects.filter(link=link).exists():
            continue
        mail = Mail.objects.get(link=link)
        if mail.notificationsettings_set.filter(user_id=request.user.id, send=False).exists():
            n_settings[link] = False
        else:
            n_settings[link] = True
    return render(request, 'account/notifications.html', {
        'user': request.user,
        'saved': saved,
        'settings': n_settings,
        'autorized': autorized,
        'subscriberlist_settings': SubscriberListSettings.objects.filter(visible=True).all(),
    })


@csrf_exempt
def account_edit(request):
    autorized = False
    if request.user.is_authenticated:
        autorized = True

    tmp = {'autorized': autorized}

    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', '').strip()
        request.user.phone = request.POST.get('phone', '').strip()

        try:
            request.user.full_clean()
            request.user.save()
            return HttpResponseRedirect("/account/")
        except ValidationError as e:
            for key, value in e.message_dict.iteritems():
                tmp.update({'error_' + key: value[0]})
        return render(request, 'account/profile_edit.html', tmp)
    else:
        return render(request, 'account/profile_edit.html', tmp)


def unsubscribe(request):
    if 'success' in request.GET:
        try:
            account_obj = Account.objects.get(email=request.GET.get('email'), id=request.GET.get('id'))
            account_obj.unsubscribed = True
            account_obj.save()
            return HttpResponseRedirect('/unsubscribe/success/?email=%s' % request.GET.get('email'))
        except Account.DoesNotExist:
            return HttpResponseRedirect('/')

    email = request.GET.get('email')
    id = request.GET.get('id')
    return render(request, 'newsletter/unsubscribe.html', locals())

def unsubscribe_success(request):
    email = request.GET.get('email')
    return render(request, 'newsletter/unsubscribe_success.html', locals())

def get_order_from_order_id(order_id):
    order = 999
    order_sort = OrderSort.objects.filter(order_id=order_id, date=datetime.datetime.now())

    if order_sort.count() > 1:
        order_sort.delete()
    elif order_sort.count() == 1:
        order = order_sort.values()[0]['order']

    return order


@staff_member_required
def courier_orders(request):

    show_courier = False
    user = request.user
    data = {'today': [], 'finished': [], 'another': [], 'long': []}
    data_kostochka38 = {}
    data_movement = {}
    data_bbox = {}
    data_outside = {}
    count = {}

    if request.user.is_staff and 'user' in request.GET:
        user = Account.objects.get(username=request.GET['user'])

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    # try:
    json_string = urllib.request.urlopen('https://beautybox38.ru/admin/index.php?route=api/couriers_orders&key=beauty4kostochka&courier_id=' + str(user.id), context=ctx).read()
    data_bbox = json.loads(json_string)
    # except:
    #     data_bbox = False

    data_kostochka38['today'] = Zakaz.objects.filter(courier=user, real_desired_time=datetime.datetime.today()).exclude(status__in=[5, 6, 10, 11, 1, 8]).all().values()
    data_kostochka38['finished'] = Zakaz.objects.filter(courier=user, status=5).values()
    data_kostochka38['another'] = Zakaz.objects.filter(courier=user, real_desired_time__gt=datetime.datetime.now()).exclude(status__in=[5, 6, 10, 11, 1, 8]).exclude(real_desired_time=datetime.datetime.today()).values()

    data_movement['today'] = MovementOfGoods.objects.filter(courier=user, delivery_date=datetime.datetime.today()).exclude(status__in=[5, 6, 10, 11, 1, 8]).all().select_related('warehouse_donor', 'warehouse_recieving').values()
    data_movement['finished'] = MovementOfGoods.objects.filter(courier=user, status=5).values()
    data_movement['another'] = MovementOfGoods.objects.filter(courier=user, delivery_date__gt=datetime.datetime.now()).exclude(status__in=[5, 6, 10, 11, 1, 8]).exclude(delivery_date=datetime.datetime.today()).values()

    data_outside['today'] = OutsideZakaz.objects.filter(courier=user, real_desired_time=datetime.datetime.today()).exclude(status__in=[5, 6, 10, 11, 1, 8]).all().values()
    data_outside['finished'] = OutsideZakaz.objects.filter(courier=user, status=5).values()
    data_outside['another'] = OutsideZakaz.objects.filter(courier=user, real_desired_time__gt=datetime.datetime.now()).exclude(status__in=[5, 6, 10, 11, 1, 8]).exclude(real_desired_time=datetime.datetime.today()).all().values()

    # LONG ORDER
    if 'long' in data_bbox:
        for i in data_bbox['long']:
            i['order'] = get_order_from_order_id(i['order_number'])

            i['type'] = 'bbox38'
            i['id'] = i['order_number']
            i['desired_time'] = i['time_delivery']
            i['k_oplate'] = i['total']

            try:
                i['first_hour'] = int(i['desired_time'].split('-')[0].split(':')[0])
                if i['first_hour'] < 18:
                    i['marker_type'] = 1
                else:
                    i['marker_type'] = 2
            except:
                i['first_hour'] = 10
                i['marker_type'] = 1

            try:
                date_django = i['date_delivery'].replace('-', ',').replace(' ', ',').replace(':', ',')
                date_django = date_django.split(',')
                i['real_desired_time'] = datetime.date(int(date_django[0]), int(date_django[1]), int(date_django[2]))
            except:
                pass

            # 8 = передан курьеру, 13 = собран, 17 = ожидает отправки
            # make change_status link
            if int(i['status_id']) == 2 or int(i['status_id']) == 8 or int(i['status_id']) == 13 or int(i['status_id']) == 20 or int(i['status_id']) == 17:
                i['status_link'] = u'https://beautybox38.ru/admin/index.php?route=api/couriers_orders/courier_left&key=beauty4kostochka&order_id=%s' % i['order_id']
                i['status_link_text'] = u'Выезжаешь на заказ #%s?' % i['id']
                if int(i['status_id']) == 2 or int(i['status_id']) == 20:
                    i['status'] = 2
                elif int(i['status_id']) == 8:
                    i['status'] = 31
                else:
                    i['status'] = 3

            elif int(i['status_id']) == 3:
                i['status_link'] = u'https://beautybox38.ru/admin/index.php?route=api/couriers_orders/delivered&key=beauty4kostochka&order_id=%s' % i['order_id']
                i['status_link_text'] = u'Заказ #%s доставлен?' % i['id']
                i['status'] = 4

            data['long'].append(i)

    # TODAY ORDER
    for i in data_kostochka38['today']:
        i['order'] = get_order_from_order_id(i['id'])
        i['k_oplate'] = Zakaz.objects.get(id=i['id']).k_oplate()
        i['type'] = 'kostochka38'
        i['address'] = i['city'] + ', ' + i['street'] + ' ' + i['dom'] + ' - ' + i['appart']

        i['status_label'] = ORDER_STATUS_DICT[i['status']]
        if i['district']:
            i['district'] = DISTRICT_DICT[i['district']]
        i['edit_link'] = '/DgJrfdJg/catalog/zakaz/%s/' % i['id']

        i['status_link'] = u'/manage/%s/change_status/kostochka/4/' % i['id']
        if int(i['status']) == 4:
            i['status_link'] = u'/manage/%s/change_status/kostochka/5/' % i['id']

        try:
            i['first_hour'] = int(i['desired_time'].split('-')[0].split(':')[0])
            if i['first_hour'] < 18:
                i['marker_type'] = 1
            else:
                i['marker_type'] = 2
        except:
            i['first_hour'] = 10
            i['marker_type'] = 1

        if i['paytype'] == 4 and not i['paid_client']:
            i['paytype'] = 9

        if i['paid_client']:  # если заказ оплачен
            i['paytype'] = 4
        i['pdf_link'] = '/manage/%s/pdf/' % i['id']
        data['today'].append(i)

    for i in data_movement['today']:
        i['order'] = get_order_from_order_id(i['id'])
        i['k_oplate'] = 0
        i['desired_time'] = u'12:00 - 15:00'
        i['type'] = 'kostochka38_movement'
        donor = WareHouse.objects.get(id=i['warehouse_donor_id'])
        recieving = WareHouse.objects.get(id=i['warehouse_recieving_id'])
        i['address'] = "%s &rarr; %s" % (donor.name, recieving.name)

        i['status_label'] = ORDER_STATUS_DICT[i['status']]
        # if i['district']:
        #     i['district'] = DISTRICT_DICT[i['district']]
        i['edit_link'] = '/DgJrfdJg/catalog/movementofgoods/%s/' % i['id']

        i['status_link'] = u'/manage/%s/change_status/movement/4/' % i['id']
        if int(i['status']) == 4:
            i['status_link'] = u'/manage/%s/change_status/movement/5/' % i['id']

        i['marker_type'] = 1
        data['today'].append(i)

    for i in data_outside['today']:
        i['order'] = get_order_from_order_id(i['zakaz_id'])
        i['type'] = 'outside'
        i['address'] = i['city'] + ', ' + i['street'] + ' ' + i['dom'] + ' - ' + i['appart']

        i['status_label'] = ORDER_STATUS_DICT[i['status']]
        if i['district']:
            i['district'] = DISTRICT_DICT[i['district']]
        i['edit_link'] = '/DgJrfdJg/catalog/outsidezakaz/%s/' % i['id']

        i['status_link'] = u'/manage/%s/change_status/outside/4/' % i['id']
        if int(i['status']) == 4:
            i['status_link'] = u'/manage/%s/change_status/outside/5/' % i['id']

        i['id'] = i['zakaz_id']

        try:
            i['first_hour'] = int(i['desired_time'].split('-')[0].split(':')[0])
            if i['first_hour'] < 18:
                i['marker_type'] = 1
            else:
                i['marker_type'] = 2
        except:
            i['first_hour'] = 10
            i['marker_type'] = 1

        if i['paid_client']:  # если заказ оплачен
            i['paytype'] = 4
        data['today'].append(i)

    for i in data_bbox['current']:
        i['order'] = get_order_from_order_id(i['order_number'])

        i['type'] = 'bbox38'
        i['id'] = i['order_number']
        i['desired_time'] = i['time_delivery']
        i['k_oplate'] = i['total']

        try:
            i['first_hour'] = int(i['desired_time'].split('-')[0].split(':')[0])
            if i['first_hour'] < 18:
                i['marker_type'] = 1
            else:
                i['marker_type'] = 2
        except:
            i['first_hour'] = 10
            i['marker_type'] = 1

        # 8 = передан курьеру, 13 = собран, 17 = ожидает отправки
        # make change_status link
        if int(i['status_id']) == 2 or int(i['status_id']) == 8 or int(i['status_id']) == 13 or int(i['status_id']) == 20 or int(i['status_id']) == 17:
            i['status_link'] = u'https://beautybox38.ru/admin/index.php?route=api/couriers_orders/courier_left&key=beauty4kostochka&order_id=%s' % i['order_id']
            i['status_link_text'] = u'Выезжаешь на заказ #%s?' % i['id']
            if int(i['status_id']) == 2 or int(i['status_id']) == 20:
                i['status'] = 2
            elif int(i['status_id']) == 8:
                i['status'] = 31
            else:
                i['status'] = 3

        elif int(i['status_id']) == 3:
            i['status_link'] = u'https://beautybox38.ru/admin/index.php?route=api/couriers_orders/delivered&key=beauty4kostochka&order_id=%s' % i['order_id']
            i['status_link_text'] = u'Заказ #%s доставлен?' % i['id']
            i['status'] = 4

        data['today'].append(i)

    data['today'] = sorted(data['today'], key=itemgetter('desired_time'))

    count['all_today'] = len(data['today'])
    count['kostochka38_today'] = data_kostochka38['today'].count()
    count['bbox38_today'] = len(data_bbox['current'])
    count['outside_today'] = data_outside['today'].count()

    # FINISHED ORDER
    for i in data_kostochka38['finished']:
        i['address'] = i['city'] + ', ' + i['street'] + ' ' + i['dom'] + ' - ' + i['appart']
        i['type'] = 'kostochka38'

        i['last_edit'] = '%s:%s' % (99, 99)
        this_zakaz = Zakaz.objects.get(id=i['id'])
        if this_zakaz.last_edit():
            order_hours = this_zakaz.last_edit().time().hour
            order_minutes = this_zakaz.last_edit().time().minute
            if order_minutes < 10:
                order_minutes = '0' + str(order_minutes)
            i['last_edit'] = '%s:%s' % (order_hours, order_minutes)

        i['status'] = 5
        if i['district']:
            i['district'] = DISTRICT_DICT[i['district']]
        i['edit_link'] = '/DgJrfdJg/catalog/zakaz/%s/' % i['id']

        i['pdf_link'] = '/manage/%s/pdf/' % i['id']

        if i['paytype'] == 4 and not i['paid_client']:
            i['paytype'] = 9

        if i['paid_client']:  # если заказ оплачен
            i['paytype'] = 4

        data['finished'].append(i)

    for i in data_movement['finished']:
        donor = WareHouse.objects.get(id=i['warehouse_donor_id'])
        recieving = WareHouse.objects.get(id=i['warehouse_recieving_id'])
        i['address'] = "%s &rarr; %s" % (donor.name, recieving.name)
        i['type'] = 'kostochka38_movement'
        i['desired_time'] = u'12:00 - 15:00'
        i['real_desired_time'] = i['delivery_date']
        i['last_edit'] = '%s:%s' % (99, 99)
        this_zakaz = MovementOfGoods.objects.get(id=i['id'])
        if this_zakaz.last_edit():
            order_hours = this_zakaz.last_edit().time().hour
            order_minutes = this_zakaz.last_edit().time().minute
            if order_minutes < 10:
                order_minutes = '0' + str(order_minutes)
            i['last_edit'] = '%s:%s' % (order_hours, order_minutes)

        i['status'] = 5
        i['edit_link'] = '/DgJrfdJg/catalog/movementofgoods/%s/' % i['id']

        data['finished'].append(i)

    for i in data_outside['finished']:
        i['address'] = i['city'] + ', ' + i['street'] + ' ' + i['dom'] + ' - ' + i['appart']
        i['type'] = 'outside'
        i['status'] = 5

        i['last_edit'] = '%s:%s' % (99, 99)
        this_zakaz = OutsideZakaz.objects.get(id=i['id'])
        if this_zakaz.last_edit():
            order_hours = this_zakaz.last_edit().time().hour
            order_minutes = this_zakaz.last_edit().time().minute
            if order_minutes < 10:
                order_minutes = '0' + str(order_minutes)
            i['last_edit'] = '%s:%s' % (order_hours, order_minutes)

        if i['district']:
            i['district'] = DISTRICT_DICT[i['district']]
        i['edit_link'] = '/DgJrfdJg/catalog/outsidezakaz/%s/' % i['id']

        i['id'] = i['zakaz_id']

        if i['paid_client']:  # если заказ оплачен
            i['paytype'] = 4

        data['finished'].append(i)

    for i in data_bbox['delivered']:
        i['type'] = 'bbox38'
        i['status'] = 5
        i['id'] = i['order_number']
        i['desired_time'] = i['time_delivery']
        try:
            date_django = i['date_delivery'].replace('-', ',').replace(' ', ',').replace(':', ',')
            date_django = date_django.split(',')
            i['real_desired_time'] = datetime.datetime(int(date_django[0]), int(date_django[1]),int(date_django[2]))
        except:
            pass
        data['finished'].append(i)

    count['all_finished'] = len(data['finished'])
    count['kostochka38_finished'] = data_kostochka38['finished'].count()
    count['bbox38_finished'] = len(data_bbox['delivered'])
    count['outside_finished'] = data_outside['finished'].count()

    #  FUTURE ORDER
    for i in data_kostochka38['another']:
        i['type'] = 'kostochka38'
        i['edit_link'] = '/DgJrfdJg/catalog/zakaz/%s/' % i['id']
        i['address'] = i['city'] + ', ' + i['street'] + ' ' + i['dom'] + ' - ' + i['appart']
        i['status_label'] = ORDER_STATUS_DICT[i['status']]
        if i['district']:
            i['district'] = DISTRICT_DICT[i['district']]
        i['pdf_link'] = '/manage/%s/pdf/' % i['id']

        if i['paytype'] == 4 and not i['paid_client']:
            i['paytype'] = 9

        if i['paid_client']:  # если заказ оплачен
            i['paytype'] = 4

        data['another'].append(i)

    for i in data_movement['another']:
        i['type'] = 'kostochka38_movement'
        i['edit_link'] = '/DgJrfdJg/catalog/movementofgoods/%s/' % i['id']
        donor = WareHouse.objects.get(id=i['warehouse_donor_id'])
        recieving = WareHouse.objects.get(id=i['warehouse_recieving_id'])
        i['address'] = "%s &rarr; %s" % (donor.name, recieving.name)
        i['status_label'] = ORDER_STATUS_DICT[i['status']]
        i['desired_time'] = u'12:00 - 15:00'
        i['real_desired_time'] = i['delivery_date']
        data['another'].append(i)

    for i in data_outside['another']:
        i['type'] = 'outside'
        i['edit_link'] = '/DgJrfdJg/catalog/outsidezakaz/%s/' % i['id']
        i['address'] = i['city'] + ', ' + i['street'] + ' ' + i['dom'] + ' - ' + i['appart']
        i['status_label'] = ORDER_STATUS_DICT[i['status']]
        if i['district']:
            i['district'] = DISTRICT_DICT[i['district']]
        i['id'] = i['zakaz_id']
        if i['paid_client']:  # если заказ оплачен
            i['paytype'] = 4
        data['another'].append(i)

    for i in data_bbox['future']:
        i['type'] = 'bbox38'

        if int(i['status_id']) == 13 or int(i['status_id']) == 8:
            i['status_label'] = u'Заказ собран'
            i['status'] = 3
        else:
            i['status_label'] = u'Доставка согласована'
            i['status'] = 2
        i['id'] = i['order_number']
        i['desired_time'] = i['time_delivery']
        try:
            date_django = i['date_delivery'].replace('-', ',').replace(' ', ',').replace(':', ',')
            date_django = date_django.split(',')
            i['real_desired_time'] = datetime.date(int(date_django[0]),int(date_django[1]),int(date_django[2]))
        except:
            pass
        data['another'].append(i)

    data['another'] = sorted(data['another'], key=itemgetter('real_desired_time'))

    count['all_another'] = len(data['another'])
    count['kostochka38_another'] = data_kostochka38['another'].count()
    count['bbox38_another'] = len(data_bbox['future'])
    count['outside_another'] = data_outside['another'].count()

    data['inside_today'] = InsideZakaz.objects.filter(courier=user, date_pickup=datetime.datetime.today()).exclude(status__in=[6, 4]).select_related('segment_new').all()
    data['inside_finished'] = InsideZakaz.objects.filter(courier=user, status=4).select_related('segment_new').all()
    data['inside_another'] = InsideZakaz.objects.filter(courier=user).exclude(status__in=[4, 6]).exclude(date_pickup=datetime.datetime.today()).select_related('segment_new').all()

    if request.user.is_staff and 'user' in request.GET:
        admin = True

        try:
            courier_buttons = []

            for this_user in Account.objects.filter(groups__id=1).order_by('-id'):
                if user.id == 5316:
                    continue
                temp_result = {'count_bbox': '?'}
                if this_user.id == 5316:
                    continue

                temp_result['user'] = this_user
                try:
                    json_string = urllib.request.urlopen(
                        'http://beautybox38.ru/admin/index.php?route=api/couriers_orders&key=beauty4kostochka&courier_id=' + str(
                            this_user.id), context=ctx).read()
                    data_bbox = json.loads(json_string)

                    temp_result['count_bbox'] = len(data_bbox['current']) + len(data_bbox['future'])
                except:
                    data_bbox = False

                count_today = Zakaz.objects.filter(courier=this_user,real_desired_time=datetime.datetime.today()).exclude(status__in=[5, 6, 10, 11, 1, 8]).all().count()
                count_another = Zakaz.objects.filter(courier=this_user,real_desired_time__gt=datetime.datetime.now()).exclude(status__in=[5, 6, 10, 11, 1, 8]).exclude(real_desired_time=datetime.datetime.today()).count()
                temp_result['count'] = count_today + count_another

                count_outside_today = OutsideZakaz.objects.filter(courier=this_user,real_desired_time=datetime.datetime.today()).exclude(status__in=[5, 6, 10, 11, 1, 8]).all().count()
                count_outside_another = OutsideZakaz.objects.filter(courier=this_user,real_desired_time__gt=datetime.datetime.now()).exclude(status__in=[5, 6, 10, 11, 1, 8]).exclude(real_desired_time=datetime.datetime.today()).all().count()
                temp_result['count_outside'] = count_outside_today + count_outside_another

                courier_buttons.append(temp_result)
        except :
            pass

    else:
        courier = True

    edit = request.user.is_staff and 'edit' in request.GET
    map = request.user.is_staff and 'map' in request.GET

    today = datetime.datetime.now()

    return render(request, 'courier/order_list_admin.html', locals())


@csrf_exempt
def order_sort(request):
    order_data = request.POST['order_date'].split(',')[:-1]
    result = False
    for i in order_data:
        result = True
        order_prop = i.split(':')
        order_sort = OrderSort.objects.filter(order_id=order_prop[0], date=datetime.datetime.now())

        if order_sort.count() == 1:
            order_sort.update(order=order_prop[1])
        else:
            new_order_sort = OrderSort(
                order_id=order_prop[0],
                order=order_prop[1]
            )
            new_order_sort.save()

    return HttpResponse(json.dumps(result), content_type='application/javascript')


@staff_member_required
def courier_orders_fulfilled(request):
    date_range = (datetime.datetime.today() - datetime.timedelta(days=1), datetime.datetime.today() + datetime.timedelta(days=1))
    zakaz_table = ZakazTable(Zakaz.objects.filter(
        courier=request.user,
        status__in=[6, 10],
        date_end__range=date_range,
    ).all(), request=request)
    inside_zakaz_table = InsideZakazTable(InsideZakaz.objects.filter(
        courier=request.user,
        status=6,
        date_end__range=date_range
    ).all(), request=request)
    return render(request, 'courier/order_list.html', {
        'zakaz_table': zakaz_table,
        'inside_zakaz_table': inside_zakaz_table,
        'fulfilled': True,
        'zakaz_table_today': False,
        'inside_zakaz_table_today': False,
        'zakaz_table_finished': False,
    })


@staff_member_required
def print_view(request):
    """
    model_name это либо MovementOfGoods, либо InsideZakaz
    Эти модели реализуют метод get_items_to_print
    """
    ids = request.GET.get("ids", "")  # type: str
    if ids == "":
        model_name = request.GET.get("model_name")
        Model = apps.get_model("catalog", model_name)
        _id = request.GET.get("id")
        instance = Model.objects.filter(id=int(_id)).first()
        context = {"object": instance}
    else:
        _ids = ids.split(",")  # type: List
        if '' in _ids:
            _ids.remove('')
        items = LeftItem.objects.filter(id__in=_ids)
        context = {
            "object": {
                "get_items_to_print": items
            }
        }
    return render(request, 'print.html', context=context)


@staff_member_required
def print_price_tag_view(request):
    item_ids = request.GET.get('item_ids').split(',')
    items = Item.objects.filter(id__in=item_ids)
    return render(request, 'print_price_tags.html', context={'items': items})


def discount(request):
    flatpage = get_object_or_404(Static, link='discount')
    itemsales = ItemSale.objects\
        .filter(date_end__gte=datetime.datetime.now(), show=True)\
        .order_by('-sale')\
        .select_related('item', 'item__deckitem')\
        .values_list('item__deckitem__id', flat=True)

    items = Deckitem.objects.filter(id__in=itemsales, active=True).distinct()

    items = dict([(obj.id, obj) for obj in items])
    sorted_items = []
    idlist = []
    for id in itemsales:
        if not id in idlist and id in items:
            sorted_items.append(items[id])
            idlist.append(id)
    items = sorted_items
    response = render(request, 'discount.html', locals())
    response['Cache-Control'] = 'no-cache, must-revalidate'
    return response


def new_items(request):
    items = Item.objects\
        .filter(
            Q(new=True) &
            Q(active=True) &
            Q(temporarily_unavailable=False)
        )\
        .exclude(availability=0)\
        .order_by('-date_created')

    response = render(request, 'new_items.html', locals())
    response['Cache-Control'] = 'no-cache, must-revalidate'

    return response
