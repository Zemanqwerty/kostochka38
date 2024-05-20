# -*- coding: utf-8 -*-
"""
This file was generated with the customdashboard management command, it
contains the two classes for the main dashboard and app index dashboard.
You can customize these classes as you want.

To activate your index dashboard add the following to your settings.py::
    ADMIN_TOOLS_INDEX_DASHBOARD = '104_kostochka38.dashboard.CustomIndexDashboard'

And to activate the app index dashboard::
    ADMIN_TOOLS_APP_INDEX_DASHBOARD = '104_kostochka38.dashboard.CustomAppIndexDashboard'
"""

from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse

from admin_tools.dashboard import modules, Dashboard, AppIndexDashboard
from admin_tools.utils import get_admin_site_name
from catalog.models import *
from django.db.models import Sum

#  количество повторных заказов по месяцам
#  SELECT count(id) as count, owner_id, date, summ from `catalog_zakaz` where status=6 group by `owner_id`, MONTH(date_end) having count>1

class CustomIndexDashboard(Dashboard):
    """
    Custom index dashboard for 104_kostochka38.
    """
    columns = 2

    def init_with_context(self, context):
        site_name = get_admin_site_name(context)
        # append a link list module for "quick links"
        self.children.append(modules.LinkList(
            _('Quick links'),
            layout='inline',
            draggable=False,
            deletable=False,
            collapsible=False,
            children=[
                [_('Return to site'), '/'],
                [_('Change password'),
                 reverse('%s:password_change' % site_name)],
                [_('Log out'), reverse('%s:logout' % site_name)],
            ]
        ))


        #InnerZakazSumMonth(title=u"ПрокСервис", supplier=0),
        #InnerZakazSumMonth(title=u"РоялКанин", supplier=1),
        #InnerZakazSumMonth(title=u"Аврора", supplier=2),

        self.children.append(modules.Group(
            title=u"Модули",
            display="tabs",
            children=[
                modules.AppList(
                    title=u'Каталог',
                    models=('catalog.models.*',)
                ),
                modules.AppList(
                    title=u'Рассылки',
                    models=('mailer.models.*', 'campaign.models.*')
                ),
                modules.AppList(
                    title=u'Ядро',
                    models=('core.models.*',)
                ),
                modules.AppList(
                    title=u'Новости и Акции',
                    models=('news.models.*',)
                ),
                modules.AppList(
                    _('Administration'),
                    models=('django.contrib.*',),
                )
            ]
        ))


class CustomAppIndexDashboard(AppIndexDashboard):
    """
    Custom app index dashboard for 104_kostochka38.
    """

    # we disable title because its redundant with the model list module
    title = ''

    def __init__(self, *args, **kwargs):
        AppIndexDashboard.__init__(self, *args, **kwargs)

        # append a model list module and a recent actions module
        self.children += [
            modules.ModelList(self.app_title, self.models),
            modules.RecentActions(
                _('Recent Actions'),
                include_list=self.get_app_content_types(),
                limit=5
            )
        ]

    def init_with_context(self, context):
        """
        Use this method if you need to access the request context.
        """
        return super(CustomAppIndexDashboard, self).init_with_context(context)
