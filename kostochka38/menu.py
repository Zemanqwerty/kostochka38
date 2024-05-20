# -*- coding: utf-8 -*-
"""
This file was generated with the custommenu management command, it contains
the classes for the admin menu, you can customize this class as you want.

To activate your custom menu add the following to your settings.py::
    ADMIN_TOOLS_MENU = '104_kostochka38.menu.CustomMenu'
"""

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from admin_tools.menu import items, Menu
from core.models import Account


class CustomMenu(Menu):
    """
    Custom Menu for 104_kostochka38 admin site.
    """
    def __init__(self, **kwargs):
        couriers = Account.objects.filter(groups__id=1).order_by('-id')
        couriers_menu = []
        for i in couriers:
            couriers_menu.append(items.MenuItem('%s %s' % (i.last_name, i.first_name), '/manage/calculate_courier/?user=%s' % i.username))

        couriers_menu_collect_order = []
        for i in couriers:
            couriers_menu_collect_order.append(items.MenuItem('%s %s' % (i.last_name, i.first_name), '/manage/collect_orders/?user=%s' % i.username))

        Menu.__init__(self, **kwargs)
        self.children += [
            items.MenuItem(_('Dashboard'), reverse('admin:index')),
            items.Bookmarks(),
            items.AppList(
                _('Applications'),
                exclude=('django.contrib.*',)
            ),
            items.AppList(
                _('Administration'),
                models=('django.contrib.*',)
            ),
            items.MenuItem(u'Данные',
                children=[
                    items.MenuItem(u'Статистика (графики)', '/DgJrfdJg/statistics/'),
                    items.MenuItem(u'Сводный баланс', '/DgJrfdJg/balans/'),
                    items.MenuItem(u'Экспорт, прайс с остатками ОПТ', '/DgJrfdJg/export_to_xls/opt/'),
                    items.MenuItem(u'Экспорт, прайс с остатками ЗАВОДЧИК', '/DgJrfdJg/export_to_xls/zavodchik/'),
                    items.MenuItem(u'Собрать потерянных покупателей', '/DgJrfdJg/get-lost-users/'),
                ]
            ),
            items.MenuItem(u'Приемка курьера',
                children=couriers_menu
            )
        ]

    def init_with_context(self, context):
        """
        Use this method if you need to access the request context.
        """
        return super(CustomMenu, self).init_with_context(context)
