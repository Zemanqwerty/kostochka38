# -*- coding: utf-8 -*-
from django.conf.urls import *
from django.urls import re_path
from catalog.views import views
from core.views import static
from kostochka38 import settings

urlpatterns = [
    re_path(r'^$', views.catalog_view, name='catalog'),

    # for redirect old ulrs
    re_path(r'^produktsiya-dlya-schenkov/$', views.view_redirect, {'end_path': False, 'path': '/c/korm-dlya-sobak/?f-age=schenok'}),
    re_path(r'^vzroslyie-sobaki-1-7-let/$', views.view_redirect, {'end_path': False, 'path': '/c/korm-dlya-sobak/?f-age=vzroslaya-sobaka'}),
    re_path(r'^pozhilyie-sobaki-starshe-7-let/$', views.view_redirect, {'end_path': False, 'path': '/c/korm-dlya-sobak/?f-age=pozhilaya-sobaka'}),
    re_path(r'^sobaki-s-osobyimi-potrebnostyami/$', views.view_redirect, {'end_path': False, 'path': '/c/korm-dlya-sobak/?f-other=osobyie-potrebnosti'}),
    re_path(r'^sobaki-opredelennyih-porod/$', views.view_redirect, {'end_path': False, 'path': '/c/korm-dlya-sobak/?f-other=opredelennaiy-poroda'}),
    re_path(r'^sobaki-razlichnyih-razmerov/$', views.view_redirect, {'end_path': False, 'path': '/c/korm-dlya-sobak/'}),
    re_path(r'^pischevyie-dobavki/$', views.view_redirect, {'end_path': False, 'path': '/c/pischevyie-dobavki-dlya-sobak/'}),
    re_path(r'^vlazhnyij-korm-dlya-sobak/$', views.view_redirect, {'end_path': False, 'path': '/c/korm-dlya-sobak/?f-type=vlazhnyij'}),

    re_path(r'^vlazhnyij-korm//$', views.view_redirect, {'end_path': False, 'path': '/c/korm-dlya-koshek/?f-type=vlazhnyij'}),
    re_path(r'^produktsiya-dlya-kotyat/$', views.view_redirect, {'end_path': False, 'path': '/c/korm-dlya-koshek/?f-age=kotenok'}),
    re_path(r'^vzroslyie-koshki-1-7-let/$', views.view_redirect, {'end_path': False, 'path': '/c/korm-dlya-koshek/?f-age=vzroslaya-koshka'}),
    re_path(r'^pozhilyie-koshki-starshe-7-let/$', views.view_redirect, {'end_path': False, 'path': '/c/korm-dlya-koshek/?f-age=pozhilaya-koshka'}),
    re_path(r'^koshki-s-osobyimi-potrebnostyami/$', views.view_redirect, {'end_path': False, 'path': '/c/korm-dlya-koshek/?f-other=osobennosti-dlya-koshek'}),
    re_path(r'^koshki-opredelennyih-porod/$', views.view_redirect, {'end_path': False, 'path': '/c/korm-dlya-koshek/?f-other=poroda'}),
    re_path(r'^napolnitel-dlya-tualeta/$', views.view_redirect, {'end_path': False, 'path': '/c/napolniteli-dlya-tualetov-dlya-koshek/'}),

    re_path(r'^uhod-za-sobakoi/$', views.view_redirect, {'end_path': False, 'path': '/c/uhod-za-sobakoj/'}),
    re_path(r'^salfetki-podguzniki-podstilki-pelenki-dlya-sobak/$', views.view_redirect, {'end_path': False, 'path': '/c/uhod-za-sobakoj/'}),
    re_path(r'^ammunitsiya-dlya-sobak/$', views.view_redirect, {'end_path': False, 'path': '/c/aksessuaryi-dlya-sobak/'}),
    re_path(r'^miski-dlya-sobak/$', views.view_redirect, {'end_path': False, 'path': '/c/aksessuaryi-dlya-sobak/?f-type-accessories-dog=miski'}),
    re_path(r'^ruletki-dlya-sobak/$', views.view_redirect, {'end_path': False, 'path': '/c/aksessuaryi-dlya-sobak/?f-type-accessories-dog=ruletki'}),
    re_path(r'^tualetyi-dlya-sobak/$', views.view_redirect, {'end_path': False, 'path': '/c/aksessuaryi-dlya-sobak/?f-type-accessories-dog=tualetyi'}),
    re_path(r'^sumki-perenoski/$', views.view_redirect, {'end_path': False, 'path': '/c/aksessuaryi-dlya-sobak/?f-type-accessories-dog=sumki-perenoski'}),

    re_path(r'^ammunitsiya-dlya-koshek/$', views.view_redirect, {'end_path': False, 'path': '/c/aksessuaryi-dlya-koshek/'}),
    re_path(r'^sredstva-uhoda/$', views.view_redirect, {'end_path': False, 'path': '/c/uhod-za-koshkoj/'}),
    re_path(r'^miski-dlya-koshek/$', views.view_redirect, {'end_path': False, 'path': '/c/aksessuaryi-dlya-koshek/?f-type-accessories-cat=miska'}),
    re_path(r'^tualetyi-dlya-koshek/$', views.view_redirect, {'end_path': False, 'path': '/c/aksessuaryi-dlya-koshek/?f-type-accessories-cat=tualet'}),
    re_path(r'^mebel-dlya-koshek/$', views.view_redirect, {'end_path': False, 'path': '/c/aksessuaryi-dlya-koshek/?f-type-accessories-cat=domik'}),
    re_path(r'^sumki-perenoski-dlya-koshek/$', views.view_redirect, {'end_path': False, 'path': '/c/aksessuaryi-dlya-koshek/?f-type-accessories-cat=sumka-perenoska'}),
    re_path(r'^lezhaki-dlya-koshek/$', views.view_redirect, {'end_path': False, 'path': '/c/aksessuaryi-dlya-koshek/?page=1&f-type-accessories-cat=mebel'}),

    re_path(r'^grunt-dlya-rybok/$', views.view_redirect, {'end_path': False, 'path': '/c/akvariumistika-dlya-rybok/?f-type-akvariumistika=grunt'}),



    re_path(r'^producer/(?P<end_path>.*)/$', views.view_redirect, {'path': '/c/p/'}),
    re_path(r'^p/(?P<producer_link>.*)/$', views.view_producer),

    re_path(r'^slug/(?P<slug>.*)/', views.view_category),

    re_path(r'^(?P<category_link>.*)/gf/(?P<group_filter>.*)/(?P<filter_value>.*)/$', views.view_category),

    re_path(r'^(?P<category_link>.*)/(?P<item_link>\d*)/review_add_complete/$', views.view_item_review_add_complete_redirect),
    re_path(r'^(?P<category_link>.*)/(?P<item_link>\d*)/$', views.view_item_redirect),

    re_path(r'^i/(?P<item_link>.*)/review_add_complete/$', views.view_item_review_add_complete),
    re_path(r'^i/(?P<item_link>.*)/$', views.view_item),

    re_path(r'^get_item_availability_table/$', views.get_item_availability_table),

    re_path(r'^(?P<category_link>.*)/$', views.view_category),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

