# -*- coding: utf-8 -*-
from django.conf.urls import *
from django.urls import re_path
from django.views.static import serve
from core import views as core_views
from sberbank import views as sberbank_views
from catalog.views import views as catalog_views
from kassa import views as kassa_views
from django.conf import settings
from django.contrib import admin
from core import service as service_views
from core import temporal as temporal_views
from django.conf.urls.static import static
from core import get_price

admin.autodiscover()

handler404 = 'core.views.my_custom_404_view'
handler500 = 'core.views.my_custom_500_view'

urlpatterns = [
    re_path(r'^admins/', admin.site.urls),
    re_path(r'^admin_tools/', include('admin_tools.urls')),
    re_path(r'^captcha/refresh/$', catalog_views.captcha_refresh),
    re_path(r'^captcha/', include('captcha.urls')),
    re_path(r'^ckeditor/', include('ckeditor_uploader.urls')),
    re_path(r'^campaign/', include('campaign.urls')),

    re_path(r'^news/', include('news.urls')),
    re_path(r'^promo/', include('news.urls_2')),
    re_path(r'^article/', include('news.urls_3')),
    re_path(r'^unsubscribe/$', core_views.unsubscribe),
    re_path(r'^unsubscribe/success/$', core_views.unsubscribe_success),

    #  discount
    re_path(r'^discount/', core_views.discount, name='discount'),

    #  new
    re_path(r'^new/', core_views.new_items, name='new'),

    re_path(r'^setCity', core_views.setCity, name='setCity'),

    re_path(r'^irr/', include('irr.urls')),
    re_path(r'^export/', include('rambler.urls')),


    re_path(r'^$', core_views.start, name='main'),
    re_path(r'^change_cookie_status/$', core_views.change_cookie_status, name='change_cookie_status'),
    re_path(r'^change_basket_of_goods_status/$', core_views.change_basket_of_goods_status, name='change_cookie_status'),
    re_path(r'^faq/$', catalog_views.view_redirect, {'path': '/', 'end_path': ''}),
    re_path(r'^search_ajax/$', core_views.search_ajax),
    re_path(r'^search/$', core_views.search),

    # royal brand-zone
    re_path(r'^royal-canin/$', core_views.royal_canin, name='royal_cats'),

    # ---

    # Текстовые разделы
    re_path(r'^contacts/$', core_views.contacts, name='contacts'),
    re_path(r'^about/$', core_views.static, {'link': 'about'}, name='about'),
    re_path(r'^reviews/$', core_views.review, name='reviews'),
    re_path(r'^delivery/$', core_views.static, {'link': 'delivery'}, name='delivery'),
    # ---

    # Каталог
    re_path(r'^catalog/(?P<end_path>.*)/$', catalog_views.view_redirect, {'path': '/c/'}),
    re_path(r'^catalog/$', catalog_views.view_redirect, {'path': '/c/', 'end_path': ''}),
    re_path(r'^c/', include('catalog.urls')),
    # ---

    # Корзина клиента
    re_path(r'^cart/add/$', catalog_views.cart_add),
    re_path(r'^edit_cart_line/$', catalog_views.edit_cart_line),
    re_path(r'^cart/$', catalog_views.cart_view, name='cart'),
    re_path(r'^cart/registration/$', catalog_views.cart_registration),
    re_path(r'^cart/complete/(?P<zakaz_id>.*)/$', catalog_views.cart_complete),
    re_path(r'^cart/repeat/(?P<order_id>.*)/$', catalog_views.repeat),
    re_path(r'^cart/autorepeat/(?P<order_id>.*)/(?P<days>.*)/$', catalog_views.autorepeat),
    # ---PyYAML==5.3.1


    # Работа с заказами клиентов
    re_path(r'^manage/(?P<zakaz_id>.*)/pdf/$', catalog_views.manage_order_view_pdf),
    re_path(r'^manage/(?P<zakaz_id>.*)/invoice/$', catalog_views.manage_order_view_invoice),
    re_path(r'^manage/(?P<zakaz_id>.*)/torg-12/$', catalog_views.manage_order_view_torg12),
    re_path(r'^manage/collect_pdf/$', catalog_views.manage_collect_pdf),
    re_path(r'^manage/collect_change/$', catalog_views.manage_collect_change),
    re_path(r'^manage/check_orders/$', catalog_views.manage_check_orders),

    re_path(r'^manage/collect_movement/$', catalog_views.collect_movement),
    re_path(r'^manage/collect_inside_orders/(?P<segment_id>\d*)/$', catalog_views.collect_inside_orders),
    re_path(r'^manage/(?P<zakaz_id>.*)/inside_pdf_inside/$', catalog_views.manage_order_view_inside_pdf_inside),
    # ---

    re_path(r'^manage/print/$', core_views.print_view, name='print_view'),
    re_path(r'^manage/print_price_tag_view/$', core_views.print_price_tag_view, name='print_price_tag_view'),

    # Работа с кассой
    re_path(r'^manage/komtet/success/$', catalog_views.komtet_success),
    re_path(r'^manage/komtet/fail/(?P<status_id>.*)/$', catalog_views.komtet_fail),
    # ---

    # Приемка курьера
    re_path(r'^manage/collect_orders/$', catalog_views.manage_collect_orders),
    re_path(r'^manage/print_orders/$', catalog_views.manage_print_orders),
    re_path(r'^manage/print_cash/$', catalog_views.manage_print_cash),
    re_path(r'^manage/calculate_courier/$', catalog_views.calculate_courier),
    re_path(r'^manage/calculate_courier/(?P<date>.*)/finish$', catalog_views.calculate_courier_finish),
    re_path(r'^manage/calculate_courier/(?P<date>.*)/$', catalog_views.calculate_courier),
    # ---

    # Обновление заказов
    re_path(r'^DgJrfdJg/catalog/zakaz/(?P<zakaz_id>.*)/update_zakaz/$', catalog_views.update_zakaz),
    re_path(r'^DgJrfdJg/catalog/insidezakaz/(?P<zakaz_id>.*)/update_zakaz/$', catalog_views.update_insidezakaz),
    # ---

    # Автозаказы клиентов
    re_path(r'^DgJrfdJg/createzakaz/(?P<autozakaz_id>.*)/(?P<call_type>.*)/$', catalog_views.create_zakaz),
    re_path(r'^DgJrfdJg/createautozakaz/(?P<zakaz_id>.*)/(?P<call_type>.*)/$', catalog_views.create_autozakaz),
    re_path(r'^DgJrfdJg/deleteautozakaz/(?P<autozakaz_id>.*)/$', catalog_views.delete_autozakaz),
    re_path(r'^DgJrfdJg/collect_autozakaz/$', catalog_views.collect_autozakaz),
    # ---

    # service_views
    # статистика и баланс
    re_path(r'^DgJrfdJg/statistics/$', service_views.statistics),
    re_path(r'^DgJrfdJg/balans/$', service_views.balans),
    re_path(r'^put_statistics/$', service_views.put_statistics),

    # супер отчет
    re_path(r'^DgJrfdJg/calculate_revenue/$', service_views.calculate_revenue),
    re_path(r'^DgJrfdJg/sr/$', service_views.sr),
    re_path(r'^DgJrfdJg/sr/(?P<month_count>\d*)/$', service_views.sr),
    re_path(r'^DgJrfdJg/export_to_xls/$', service_views.export_to_xls),
    re_path(r'^DgJrfdJg/export_to_xls/zavodchik/$', service_views.export_to_xls, {'type': 'zavodchik'}),
    re_path(r'^DgJrfdJg/export_to_xls/opt/$', service_views.export_to_xls, {'type': 'opt'}),
    re_path(r'^DgJrfdJg/get-lost-users/$', service_views.get_lost_users),
    re_path(r'^autozakaz/(?P<segment>.*)/$', service_views.autozakaz),
    re_path(r'^check_zakaz_state/$', service_views.check_zakaz_state),
    re_path(r'^DgJrfdJg/inventory/$', service_views.inventory),
    re_path(r'^DgJrfdJg/royal_report/$', service_views.royal_report),
    # ---

    # autorun
    re_path(r'^get_price/$', get_price.get_price, name='get_price'),
    re_path(r'^get_price_barcode/(?P<segment>.*)/$', get_price.get_price_barcode, name='get_price_barcode'),

    # Need Add to cron
    re_path(r'^calculate_price/$', service_views.calculate_price),
    re_path(r'^deckitems_availability/$', service_views.deckitems_availability),
    re_path(r'^deactivate_deckitems/$', service_views.deactivate_deckitems),
    re_path(r'^calculate_buy_rate/$', catalog_views.calculate_buy_rate),
    re_path(r'^check_availibility_status_date/$', service_views.check_availibility_status_date),
    re_path(r'^check_availibility_status_date_fix/$', service_views.check_availibility_status_date_fix),
    # ---

    # re_path(r'^deckitems_activate/$', service_views.deckitems_activate),

    # Личный кабинет
    re_path(r'^account/orders/$', catalog_views.orders),
    re_path(r'^account/order/(?P<zakaz_id>.*)/$', catalog_views.order_view),
    re_path(r'^account/autoorder/(?P<autozakaz_id>.*)/$', catalog_views.autoorder_view),
    re_path(r'^account/$', catalog_views.account, name='account'),
    re_path(r'^entry/$', core_views.entry),
    re_path(r'^accounts/login/$', core_views.login),
    re_path(r'^registration/$', core_views.registration),
    re_path(r'^account/logout/$', core_views.logout),
    re_path(r'^account/newuser/$', core_views.newuser),
    re_path(r'^account/newuser/vk/$', core_views.newuser_vk),
    re_path(r'^account/newuser/ok/$', core_views.newuser_ok),
    re_path(r'^account/newuser/fb/$', core_views.newuser_fb),
    re_path(r'^account/newuser/google/$', core_views.newuser_google),
    re_path(r'^account/edit/$', core_views.account_edit),
    re_path(r'^account/password/restore/(?P<user_id>.*)/(?P<hash_code>.*)/$', core_views.password_restore),
    re_path(r'^account/password/forget/$', core_views.password_forget),
    re_path(r'^account/password/change/$', core_views.password_change),
    re_path(r'^account/notifications/$', core_views.notifications),
    # ---

    # Панель курьера
    re_path(r'^mz/$', core_views.courier_orders),
    re_path(r'^order/sort/$', core_views.order_sort),
    re_path(r'^manage/(?P<zakaz_id>.*)/change_status/(?P<store_type>.*)/(?P<status_id>.*)/$',
        catalog_views.manage_change_status),

    re_path(r'^manage/(?P<zakaz_id>.*)/change_status/(?P<status_id>.*)/$',
        catalog_views.manage_change_status_from_collect_order),

    re_path(r'^manage/(?P<zakaz_id>.*)/change_status_movement/(?P<status_id>.*)/$',
        catalog_views.manage_change_status_movement_from_collect_order),

    re_path(r'^manage/(?P<zakaz_id>.*)/change_status_inside/(?P<status_id>.*)/$',
        catalog_views.manage_change_status_inside),
    # ---

    # re_path(r'^royal_availability/$', temporal_views.royal_availability),
    re_path(r'^DgJrfdJg/', admin.site.urls, name='admin'),
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),

    #  Sberbank\Yookassa
    re_path(r'^payment/(?P<zakaz_id>.*)/redirect/$', sberbank_views.payment_redirect, name='payment_redirect'),
    # re_path(r'^payment/(?P<zakaz_id>.*)/$', sberbank_views.payment_page, name='payment_page'),
    re_path(r'^payment-success/(?P<payment_uuid>.*)/$', sberbank_views.payment_success, name='payment_success'),
    re_path(r'^payment-webhook/$', sberbank_views.yookassa_webhook),
    re_path(r'^payment-fail/(?P<payment_uuid>.*)/$', sberbank_views.payment_fail, name='payment_fail'),

    #  items feed for facebook
    re_path(r'^facebook/feed.xml', service_views.facebook_xml, name='facebook_xml_feed'),

    re_path(r'^k/', include('kassa.urls')),
    re_path(r'^s/', include('sklad.urls')),

]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# #  redirected
# urlpatterns += [
#     re_path(r'^help-aliya/$', core_views.help_aliya),
# ]

urlpatterns += [
    re_path(r'^(?P<link>.*)/$', core_views.static),
]
