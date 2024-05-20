# -*- coding: utf-8 -*-
from django.utils import dateformat

import django_tables2 as tables
from catalog.models import Zakaz, InsideZakaz


class ZakazTableTodayAdmin(tables.Table):
    zakaz_url = tables.TemplateColumn(u'{% load admin_urls %} <a href="/DgJrfdJg/catalog/zakaz/{{ record.id|admin_urlquote }}/" '
                                    u'class="pdf_link" target="_blank">Открыть заказ &rarr;</a>',
                                    verbose_name=u'Заказ')
    paidtype = tables.TemplateColumn(u'<img src="/static/kostochka38/images/i_oplata_{{ record.paytype }}.png" width="16px">',
                                     verbose_name=u'Опл')

    class Meta:
        model = Zakaz
        fields = ('id', 'status_label', 'desired_time', 'phone', 'need_call', 'district',
                  'address', 'paidtype',
                  'zakaz_url')
        attrs = {"class": "paleblue  "}
        ordering = ['desired_time']


class ZakazTableToday(tables.Table):
    pdf_url = tables.TemplateColumn(u'{% load admin_urls %} <a href="{{ record.pdf_link }}" '
                                    u'class="pdf_link" target="_blank">{{ record.pdf_link_text|safe }}</a>',
                                    verbose_name=u'PDF')
    complete_url = tables.TemplateColumn(u'{% load admin_urls %} '
                                         u'<a href="{{ record.status_link }}" class="pdf_link" onclick="return confirm(\'{{ record.status_link_text }}\')"><img src="{{ record.status_link_image }}"></a>',
                                         verbose_name=u'-')
    paidtype = tables.TemplateColumn(u'<img src="/static/kostochka38/images/i_oplata_{{ record.paytype }}.png" width="32px">',
                                     verbose_name=u'Опл')

    phone_number = tables.TemplateColumn(u'<a href="tel:{{ record.phone }}">{{ record.phone }}</a>',
                                     verbose_name=u'Тел')

    class Meta:
        model = Zakaz
        fields = ('id', 'complete_url', 'desired_time', 'phone_number', 'need_call', 'district',
                  'address', 'paidtype',
                  'pdf_url')
        attrs = {"class": "paleblue  "}
        ordering = ['desired_time']


class ZakazTableAdmin(tables.Table):
    zakaz_url = tables.TemplateColumn(u'{% load admin_urls %} <a href="/DgJrfdJg/catalog/zakaz/{{ record.id|admin_urlquote }}/" '
                                    u'class="pdf_link" target="_blank">Открыть заказ &rarr;</a>',
                                    verbose_name=u'Заказ')
    paidtype = tables.TemplateColumn(u'<img src="/static/kostochka38/images/i_oplata_{{ record.paytype }}.png" width="16px">',
                                     verbose_name=u'Опл')

    def render_real_desired_time(self, value):
        if value:
            return dateformat.format(value, 'j N')
        else:
            return u''

    class Meta:
        model = Zakaz
        fields = ('id', 'status_label', 'real_desired_time', 'desired_time', 'phone', 'district',
                  'address', 'paidtype', 'zakaz_url')
        attrs = {"class": "paleblue  "}
        ordering = ['desired_time']

class ZakazTable(tables.Table):
    pdf_url = tables.TemplateColumn(u'{% load admin_urls %} <a href="{{ record.pdf_link }}" '
                                    u'class="pdf_link" target="_blank">{{ record.pdf_link_text|safe }}</a>',
                                    verbose_name=u'PDF')
    paidtype = tables.TemplateColumn(u'<img src="/static/kostochka38/images/i_oplata_{{ record.paytype }}.png" width="32px">',
                                     verbose_name=u'Опл')

    def render_real_desired_time(self, value):
        if value:
            return dateformat.format(value, 'j N')
        else:
            return u''

    class Meta:
        model = Zakaz
        fields = ('id', 'status_label', 'real_desired_time', 'desired_time', 'phone', 'district', 'paidtype',
                  'address')
        attrs = {"class": "paleblue  "}
        ordering = ['desired_time']


class InsideZakazTableAdmin(tables.Table):
    zakaz_url = tables.TemplateColumn(u'{% load admin_urls %} <a href="/DgJrfdJg/catalog/insidezakaz/{{ record.id|admin_urlquote }}/" '
                                    u'class="pdf_link" target="_blank">Открыть заказ &rarr;</a>',
                                    verbose_name=u'Заказ')

    def render_date_pickup(self, value):
        if value:
            return dateformat.format(value, 'j N')
        else:
            return u''

    class Meta:
        model = InsideZakaz
        fields = ('id', 'status', 'supplier', 'paid_supplier', 'date_pickup', 'cost',  'zakaz_url', )
        attrs = {"class": "paleblue  "}

class InsideZakazTable(tables.Table):
    pdf_url = tables.TemplateColumn(u"<a href='/manage/{{ record.pk }}/inside_pdf_inside/'>PDF внутренняя &rarr;</a>",
                                    verbose_name=u'PDF')

    def render_date_pickup(self, value):
        if value:
            return dateformat.format(value, 'j N')
        else:
            return u''

    class Meta:
        model = InsideZakaz
        fields = ('id', 'status', 'supplier', 'paid_supplier', 'date_pickup', 'cost',  'pdf_url', )
        attrs = {"class": "paleblue  "}


class InsideZakazTableTodayAdmin(tables.Table):
    zakaz_url = tables.TemplateColumn(u'{% load admin_urls %} <a href="/DgJrfdJg/catalog/insidezakaz/{{ record.id|admin_urlquote }}/" '
                                    u'class="pdf_link" target="_blank">Открыть заказ &rarr;</a>',
                                    verbose_name=u'Заказ')

    def render_date_pickup(self, value):
        if value:
            return dateformat.format(value, 'j N')
        else:
            return u''

    class Meta:
        model = InsideZakaz
        fields = ('id', 'status', 'supplier', 'paid_supplier', 'cost',  'zakaz_url', )
        attrs = {"class": "paleblue  "}


class InsideZakazTableToday(tables.Table):
    pdf_url = tables.TemplateColumn(u"<a href='/manage/{{ record.pk }}/inside_pdf_inside/'>PDF внутренняя &rarr;</a>",
                                    verbose_name=u'PDF')

    complete_url = tables.TemplateColumn(u'{% load admin_urls %} '
                                         u'<a href="/manage/{{ record.id|admin_urlquote }}/change_status_inside/4/" class="pdf_link" onclick="return confirm(\'Заказ поставщика #{{ record.id }} получен?\')"><img src="/staticfiles/images/complete-icon.png"></a>',
                                         verbose_name=u'-')

    def render_date_pickup(self, value):
        if value:
            return dateformat.format(value, 'j N')
        else:
            return u''

    class Meta:
        model = InsideZakaz
        fields = ('id', 'status', 'complete_url', 'supplier', 'paid_supplier', 'cost',  'pdf_url', )
        attrs = {"class": "paleblue  "}

