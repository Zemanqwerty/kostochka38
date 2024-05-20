# -*- coding: utf-8 -*-
__author__ = 'Vanger'
from catalog.models import Deckitem, Tag, Producer, FilterDescription, FilterSitemapLink
from core.models import Page
from news.models import New
from django.contrib.sitemaps import GenericSitemap
from django.contrib import sitemaps
from django.core.urlresolvers import reverse
import datetime


deckitem_dict = {
    'queryset': Deckitem.objects.filter(active=True),
    'date_field': 'last_edit',
}
news_dict = {
    'queryset': New.objects.filter(status=2, action=False),
    'date_field': 'date',
}
article_dict = {
    'queryset': Page.objects.filter(date__lte=datetime.datetime.now()),
    'date_field': 'date',
}
action_dict = {
    'queryset': New.objects.filter(status=2, action=True),
    'date_field': 'date',
}
category_dict = {
    'queryset': Tag.objects.all(),
}
filter_category_dict = {
    'queryset': FilterDescription.objects.all(),
}
producer_dict = {
    'queryset': Producer.objects.all(),
}


class StaticViewSitemap(sitemaps.Sitemap):
    priority = 0.9
    changefreq = 'weekly'
    protocol = 'https'

    def items(self):
        return ['main', 'contacts', 'about', 'delivery', 'promo', 'catalog', 'news', 'article']

    def location(self, item):
        return reverse(item)


class CatalogCategorySitemap(sitemaps.Sitemap):
    priority = 0.5
    changefreq = 'weekly'
    protocol = 'https'

    def items(self):
        return Tag.objects.all()

    def location(self, item):
        return item.get_absolute_url()


class CatalogViewSitemap(sitemaps.Sitemap):
    priority = 0.5
    changefreq = 'weekly'
    protocol = 'https'
    limit = 50000 * 500

    def items(self):
        return FilterSitemapLink.objects.all()

    def location(self, item):
        return item.get_absolute_url()


sitemaps = {
    'static': StaticViewSitemap,
    'items': GenericSitemap(deckitem_dict, priority=0.4, changefreq='daily'),
    'news': GenericSitemap(news_dict, priority=0.3, changefreq='monthly'),
    'article': GenericSitemap(article_dict, priority=0.4, changefreq='monthly'),
    'action': GenericSitemap(action_dict, priority=0.3, changefreq='monthly'),
    'category': GenericSitemap(category_dict, priority=0.8, changefreq='daily'),
    'filter_category': GenericSitemap(filter_category_dict, priority=0.8, changefreq='daily'),
    'producer': GenericSitemap(producer_dict, priority=0.8, changefreq='weekly'),
    'catalog': CatalogViewSitemap
}

