# -*- coding: utf-8 -*-
from core.models import *
from catalog.models import *
from news.models import *
import datetime, hashlib, random
from django.db.models import Sum
from django.conf import settings


def test_permitions(request):
    user = False
    zakaz_count = 0
    all_summ = 0
    sale = ''
    sale_koef = 1

    if request.user.is_authenticated:
        user = request.user
        # SALE
        if user.sale:
            sale = 'true'
            sale_koef = user.sale
            ## END SALE

        if TempZakaz.objects.filter(owner=request.user.id).count() == 1:
            zakaz = TempZakaz.objects.get(owner=request.user.id)

            all_summ = zakaz.summ
            zakaz_count = TempZakazGoods.objects.filter(zakaz=zakaz.id).aggregate(quantity=Sum('quantity'))['quantity']
        elif TempZakaz.objects.filter(owner=request.user.id).count() > 1:
            first = TempZakaz.objects.filter(owner=request.user.id).first()
            if first:
                TempZakaz.objects.filter(owner=request.user.id).exclude(id=first.id).delete()

                if TempZakaz.objects.filter(owner=request.user.id).count() == 1:
                    zakaz = TempZakaz.objects.get(owner=request.user.id)
                    all_summ = zakaz.summ
                    zakaz_count = TempZakazGoods.objects.filter(zakaz=zakaz.id).aggregate(quantity=Sum('quantity'))['quantity']

        user_a_id = request.user.id
    else:
        if "user_a_id" in request.session:
            user_a_id = request.session["user_a_id"]
        else:
            date = datetime.datetime.now()
            hashstring = str(date) + str(random.randint(1, 100000))
            hashcode = hashlib.sha224(hashstring.encode('utf-8')).hexdigest()
            request.session["user_a_id"] = hashcode
            user_a_id = hashcode

        if TempZakaz.objects.filter(hash=user_a_id):
            zakaz = TempZakaz.objects.get(hash=user_a_id)

            all_summ = zakaz.summ
            zakaz_count = TempZakazGoods.objects.filter(zakaz=zakaz.id).aggregate(quantity=Sum('quantity'))['quantity']

    return {
        'sale': sale,
        'sale_koef': sale_koef,
        'zakaz_count': zakaz_count,
        'all_summ': all_summ,
        'user_a_id': user_a_id,
        'user': user
    }


def menu(request):
    menu = {'food': []}
    if request.user.is_authenticated:
        if request.user.zavodchik:
            menu['food'].append({
                'title': u'Для собак',
                'class': 'dlya-sobak',
                'items': Tag.objects.filter(section='dlya-sobak', deckitem__producer__margin_zavodchiki__gt=0).distinct().order_by('sort'),
                'id': 'dog',
            })

            menu['food'].append({
                'title': u'Для кошек',
                'class': 'dlya-koshek',
                'items': Tag.objects.filter(section='dlya-koshek', deckitem__producer__margin_zavodchiki__gt=0).distinct().order_by('sort'),
                'id': 'cat'
            })

            menu['food'].append({
                'title': u'Для грызунов',
                'class': 'dlya-gryzunov-i-harkov',
                'items': Tag.objects.filter(section='dlya-gryzunov-i-harkov', deckitem__producer__margin_zavodchiki__gt=0).distinct().order_by('sort'),
                'id': 'rat'
            })

            menu['food'].append({
                'title': u'Для птиц',
                'class': 'dlya-ptiz',
                'items': Tag.objects.filter(section='dlya-ptiz', deckitem__producer__margin_zavodchiki__gt=0).distinct().order_by('sort'),
                'id': 'bird'
            })

            menu['food'].append({
                'title': u'Для рыбок',
                'class': 'dlya-rybok',
                'items': Tag.objects.filter(section='dlya-rybok', deckitem__producer__margin_zavodchiki__gt=0).distinct().order_by('sort'),
                'id': 'fish'
            })

            menu['food'].append({
                'title': u'Для рептилий',
                'class': 'dlya-reptiliy',
                'items': Tag.objects.filter(section='dlya-reptiliy', deckitem__producer__margin_zavodchiki__gt=0).distinct().order_by('sort'),
                'id': 'snake'
            })
            menu['producers'] = Producer.objects.filter(active=True).order_by('sort', 'title')

        elif request.user.optovik:
            menu['food'].append({
                'title': u'Для собак',
                'class': 'dlya-sobak',
                'items': Tag.objects.filter(section='dlya-sobak', deckitem__producer__margin_opt__gt=0).distinct().order_by('sort'),
                'id': 'dog',
            })

            menu['food'].append({
                'title': u'Для кошек',
                'class': 'dlya-koshek',
                'items': Tag.objects.filter(section='dlya-koshek', deckitem__producer__margin_opt__gt=0).distinct().order_by('sort'),
                'id': 'cat'
            })

            menu['food'].append({
                'title': u'Для грызунов',
                'class': 'dlya-gryzunov-i-harkov',
                'items': Tag.objects.filter(section='dlya-gryzunov-i-harkov', deckitem__producer__margin_opt__gt=0).distinct().order_by('sort'),
                'id': 'rat'
            })

            menu['food'].append({
                'title': u'Для птиц',
                'class': 'dlya-ptiz',
                'items': Tag.objects.filter(section='dlya-ptiz', deckitem__producer__margin_opt__gt=0).distinct().order_by('sort'),
                'id': 'bird'
            })

            menu['food'].append({
                'title': u'Для рыбок',
                'class': 'dlya-rybok',
                'items': Tag.objects.filter(section='dlya-rybok', deckitem__producer__margin_opt__gt=0).distinct().order_by('sort'),
                'id': 'fish'
            })

            menu['food'].append({
                'title': u'Для рептилий',
                'class': 'dlya-reptiliy',
                'items': Tag.objects.filter(section='dlya-reptiliy').order_by('sort'),
                'id': 'snake'
            })
            menu['producers'] = Producer.objects.filter(active=True, margin_opt__gt=0).order_by('sort', 'title')
        else:
            menu['food'].append({
                'title': u'Для собак',
                'class': 'dlya-sobak',
                'items': Tag.objects.filter(section='dlya-sobak').order_by('sort'),
                'id': 'dog',
            })

            menu['food'].append({
                'title': u'Для кошек',
                'class': 'dlya-koshek',
                'items': Tag.objects.filter(section='dlya-koshek').order_by('sort'),
                'id': 'cat'
            })

            menu['food'].append({
                'title': u'Для грызунов',
                'class': 'dlya-gryzunov-i-harkov',
                'items': Tag.objects.filter(section='dlya-gryzunov-i-harkov').order_by('sort'),
                'id': 'rat'
            })

            menu['food'].append({
                'title': u'Для птиц',
                'class': 'dlya-ptiz',
                'items': Tag.objects.filter(section='dlya-ptiz').order_by('sort'),
                'id': 'bird'
            })

            menu['food'].append({
                'title': u'Для рыбок',
                'class': 'dlya-rybok',
                'items': Tag.objects.filter(section='dlya-rybok').order_by('sort'),
                'id': 'fish'
            })

            menu['food'].append({
                'title': u'Для рептилий',
                'class': 'dlya-reptiliy',
                'items': Tag.objects.filter(section='dlya-reptiliy').order_by('sort'),
                'id': 'snake'
            })

            menu['producers'] = Producer.objects.filter(active=True).order_by('sort', 'title')
    else:
        menu['food'].append({
            'title': u'Для собак',
            'class': 'dlya-sobak',
            'items': Tag.objects.filter(section='dlya-sobak').order_by('sort'),
            'id': 'dog',
        })

        menu['food'].append({
            'title': u'Для кошек',
            'class': 'dlya-koshek',
            'items': Tag.objects.filter(section='dlya-koshek').order_by('sort'),
            'id': 'cat'
        })

        menu['food'].append({
            'title': u'Для грызунов',
            'class': 'dlya-gryzunov-i-harkov',
            'items': Tag.objects.filter(section='dlya-gryzunov-i-harkov').order_by('sort'),
            'id': 'rat'
        })

        menu['food'].append({
            'title': u'Для птиц',
            'class': 'dlya-ptiz',
            'items': Tag.objects.filter(section='dlya-ptiz').order_by('sort'),
            'id': 'bird'
        })

        menu['food'].append({
            'title': u'Для рыбок',
            'class': 'dlya-rybok',
            'items': Tag.objects.filter(section='dlya-rybok').order_by('sort'),
            'id': 'fish'
        })

        menu['food'].append({
            'title': u'Для рептилий',
            'class': 'dlya-reptiliy',
            'items': Tag.objects.filter(section='dlya-reptiliy').order_by('sort'),
            'id': 'snake'
        })

        menu['producers'] = Producer.objects.filter(active=True).order_by('sort', 'title')
    menu['sovety'] = Vopros_otvet.objects.all().order_by('-date').values()[0:3]
    menu['news'] = New.objects.filter(status=2).order_by('-date').values()[0:5]
    debug = settings.DEBUG

    menu['left'] = Menu.objects.filter(menu_type=1).order_by('position')
    menu['top'] = Menu.objects.filter(menu_type=1, show_on_top=True).order_by('position')
    menu['footer_text'] = Static.objects.get(link='footer_text')

    menu['footer_links'] = {
        'dog': FilterDescription.objects.filter(footer_view=True, section='dlya-sobak'),
        'cat': FilterDescription.objects.filter(footer_view=True, section='dlya-koshek'),
        'other': FilterDescription.objects.filter(footer_view=True, section__in=['dlya-gryzunov-i-harkov', 'dlya-ptiz', 'dlya-rybok', 'dlya-reptiliy']),
    }

    today = datetime.datetime.today()
    banners = Slide.objects.filter(startdate__lte=today, expdate__gte=today).order_by('position')

    last_page = Page.objects.filter(date__lte=datetime.datetime.now()).order_by('-date')[0:1]

    return {
        'menu': menu,
        'now_date': datetime.datetime.now(),
        'now_year': datetime.datetime.now().year,
        'debug': debug,
        'vers': 94,
        'banners': banners,
        'last_page': last_page,
    }  


def announcement(request):
    return {
        'announcement': Announcement.objects.filter(is_active=True).first()
    }