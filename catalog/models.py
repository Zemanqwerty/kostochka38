# -*- coding: utf-8 -*-
import re
import datetime
import pytils
import uuid
import os
import json
import logging
from math import ceil
import calendar

from django.db.models import Sum, Q
from django.db import models, transaction
from django.conf import settings
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.db.models.signals import post_delete, pre_delete
from django.dispatch.dispatcher import receiver
from django.template.loader import render_to_string
from imagekit.models import ProcessedImageField, ImageSpecField
from imagekit.processors import ResizeToFit
from ckeditor_uploader.fields import RichTextUploadingField
from ckeditor.fields import RichTextField

from catalog.tuples import *
from catalog.enums import MOVEMENTOFGOODSCHOICES

from campaign.models import MailTemplate

from core.mail import htmlmail_sender
from core.models import Account

from news.models import New, NewItems
# from recommends.providers import RecommendationProvider, recommendation_registry

from requests.exceptions import HTTPError
from komtet_kassa_sdk.v1 import Check, Client, Intent, TaxSystem, VatRate, PaymentMethod
from sberbank.signals import payment_success

from reversion import revisions as reversion


if settings.TYPE_CHECKING:
    from typing import Optional

logger = logging.getLogger(__name__)


def get_file_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = "%s.%s" % (uuid.uuid4(), ext)
    return os.path.join(instance.directory_string_var, filename)


DEFAULT_PHOTO_WIDTH = 1024
DEFAULT_PHOTO_HEIGHT = 1024


class Segment(models.Model):
    title = models.CharField(max_length=512, verbose_name=u'Название')
    link = models.CharField(max_length=512, blank=True, null=True)
    order = models.PositiveIntegerField(verbose_name=u'Сортировка', default=99)
    in_statistics = models.BooleanField(default=False, verbose_name=u'В статистике')
    in_balans = models.BooleanField(default=False, verbose_name=u'В балансе')

    num_title = models.IntegerField(verbose_name=u'#title', blank=True, null=True)
    num_price = models.IntegerField(verbose_name=u'#price', blank=True, null=True)
    num_code = models.IntegerField(verbose_name=u'#code', blank=True, null=True)
    num_article = models.IntegerField(verbose_name=u'#article', blank=True, null=True)
    num_quantity = models.IntegerField(verbose_name=u'#quantity', blank=True, null=True)

    num_check_empty = models.IntegerField(verbose_name=u'#empty', blank=True, null=True)
    num_start = models.IntegerField(verbose_name=u'#start', blank=True, null=True)

    need_quantity = models.BooleanField(verbose_name=u'Учитывать количество?', default=False)
    need_special_article = models.BooleanField(verbose_name=u'Невидимые артикулы?', default=False)
    word_to_quantity = models.CharField(verbose_name=u'Слово для Количества много', max_length=128, blank=True, null=True)
    word_to_quantity_small = models.CharField(verbose_name=u'Слово для Количества мало', max_length=128, blank=True, null=True)
    what_status = models.IntegerField(verbose_name=u'Какой статус?', choices=AVAILABILTY, default=3)

    def get_balans(self):
        result = 0
        if VendorAccount.objects.filter(segment_new=self).order_by('-id').exists():
            result = VendorAccount.objects.filter(segment_new=self).order_by('-id')[0:1][0].balans
        return result

    def get_item_count(self, warehouse=None):
        item_count = Item.objects.filter(quantity_in_reserve__gt=0, deckitem__segment_new=self)
        if warehouse is not None:
            item_count = item_count.filter(leftitem__left__gt=0, leftitem__warehouse=warehouse)
            result = 0
            for i in item_count:
                result += i.get_quantity_in_reserve_by_warehouse(warehouse)
            return result
        item_count = item_count.aggregate(sum=Sum('quantity_in_reserve'))['sum']
        result = 0
        if item_count:
            result = item_count
        return result

    def get_items_sum(self, warehouse=None):
        items = Item.objects.filter(quantity_in_reserve__gt=0, deckitem__segment_new=self)
        if warehouse is not None:
            items = items.filter(leftitem__warehouse=warehouse)
            items_sum = 0
            for i in items:
                items_sum += i.get_quantity_in_reserve_by_warehouse(warehouse) * i.real_price
            return items_sum

        items_sum = 0
        for i in items:
            items_sum += i.quantity_in_reserve * i.real_price
        return items_sum

    class Meta:
        verbose_name = u"поставщик"
        verbose_name_plural = u"Поставщики"
        ordering = ['order', 'title']

    def __str__(self):
        return self.title


class ProducerCategory(models.Model):
    title = models.CharField(max_length=512, verbose_name=u'Название')

    class Meta:
        verbose_name = u"Категория производителей"
        verbose_name_plural = u"Категории производителей"
        ordering = ['title']

    def __str__(self):
        return self.title


class Producer(models.Model):
    title = models.CharField(max_length=512, verbose_name=u'Название')
    link = models.CharField(max_length=1024, blank=True, null=True)
    product = models.IntegerField(verbose_name=u'Продукт', choices=PRODUCT, default=0)
    sort = models.IntegerField()
    original_image = ProcessedImageField(upload_to=get_file_path,
                                         options={'qaulity': 80},
                                         processors=[ResizeToFit(DEFAULT_PHOTO_WIDTH, DEFAULT_PHOTO_HEIGHT), ],
                                         verbose_name=u'фото', null=True, blank=True)
    catalog_image = ImageSpecField(source='original_image', processors=[ResizeToFit(165, 165), ],
                                   options={'quality': 80})
    menu_image = ImageSpecField(source='original_image', processors=[ResizeToFit(22, 18), ],
                                options={'quality': 80})

    active = models.BooleanField(verbose_name=u'Активный', default=False)
    # META данные
    html_title = models.CharField(u"HTML Title", max_length=128, default=u"", blank=True, null=True)
    header = models.CharField(verbose_name=u'<h1>', max_length=256, blank=True, null=True)
    meta_description = models.CharField(verbose_name="description", max_length=255, blank=True, null=True)
    meta_keywords = models.CharField(verbose_name="keywords", max_length=255, blank=True, null=True)

    margin = models.FloatField(verbose_name=u"Наценка", default='1.3')
    margin_heavy = models.FloatField(verbose_name=u"Наценка тяжелых", default='1.3')

    margin_zavodchiki = models.FloatField(verbose_name=u"Наценка для питомников", blank=True, null=True)
    margin_opt = models.FloatField(verbose_name=u"Наценка для магазинов", blank=True, null=True)

    seo_text = RichTextField(u"SEO текст", blank=True, null=True)
    directory_string_var = 'photos'
    producercategory = models.ManyToManyField(ProducerCategory, verbose_name=u'Категории')

    on_main = models.BooleanField(verbose_name=u'На главную', default=False)
    sort_main = models.PositiveIntegerField(verbose_name=u'Сортировка для главной', default=90)
    slider_link = models.CharField(u"Специальная ссылка в слайдере", max_length=512, blank=True, null=True)

    class Meta:
        verbose_name = u"Производитель"
        verbose_name_plural = u"Производители"
        ordering = ['sort', 'title']

    def __str__(self):
        return self.title

    def get_title(self):
        if self.html_title:
            return self.html_title
        else:
            return self.title

    def get_absolute_url(self):
        return '/c/p/%s/' % self.link

    def save(self):
        if not self.link:
            trans_title = pytils.translit.slugify(self.title)
            date = datetime.datetime.now()
            self.link = trans_title
        super(Producer, self).save()


class Tag(models.Model):
    section = models.CharField(max_length=128, choices=SECTION, verbose_name=u'Раздел')
    title = models.CharField(max_length=512, verbose_name=u'Название')
    title_search = models.CharField(max_length=512, verbose_name=u'Название (для поиска)', null=True, blank=True)
    link = models.CharField(max_length=1024, blank=True, null=True)
    sort = models.IntegerField()

    html_title = models.CharField(u"HTML Title", max_length=128, default=u"", blank=True)

    # META данные
    meta_description = models.CharField(u"meta description", max_length=255, blank=True)
    meta_keywords = models.CharField(u"meta keywords", max_length=255, blank=True)
    header = models.CharField(verbose_name=u'<h1>', max_length=256, blank=True, null=True)

    seo_text = RichTextField(u"SEO текст", blank=True)
    deckitems = models.ManyToManyField('Deckitem', verbose_name=u'Продукт', through='DeckitemTag', blank=True,
                                       related_name='all_deckitems')

    class Meta:
        verbose_name = u"Категория"
        verbose_name_plural = u"Категории"
        ordering = ['section', 'sort', 'title']

    def __str__(self):
        if self.section:
            return '%s (%s)' % (self.title, SECTION_DICT[self.section])
        else:
            return self.title

    def get_absolute_url(self):
        return '/c/%s/' % self.link

    def get_title(self):
        if self.html_title:
            return self.html_title
        else:
            return self.title

    def get_filter_link(self):
        return FilterDescription.objects.filter(filter__tag=self.id).values()

    def save(self):
        if not self.link:
            trans_title = pytils.translit.slugify(self.title)
            self.link = u'%s-%s' % (trans_title, self.section)
        super(Tag, self).save()


class Filter(models.Model):
    u""" Фильтры. """

    parent = models.ForeignKey('Filter', verbose_name=u'Родитель', blank=True, null=True, on_delete=models.CASCADE)
    title = models.CharField(max_length=512, verbose_name=u'Название')
    link = models.CharField(max_length=1024, blank=True, null=True)
    sort = models.IntegerField(default=99, verbose_name=u'Порядок')
    hint = models.CharField(verbose_name=u'Подсказка', blank=True, null=True, max_length=256)
    tag = models.ForeignKey(Tag, verbose_name=u'Категория', on_delete=models.CASCADE)
    deckitems = models.ManyToManyField('Deckitem', verbose_name=u'Продукт', through='FilterDeckitem', blank=True)
    hide = models.BooleanField(verbose_name=u'Спрятать в каталоге', default=False)
    view = models.PositiveIntegerField(verbose_name=u'Клики', default=0)
    seo_title = models.CharField(verbose_name=u'CEO название', max_length=128, null=True, blank=True)

    class Meta:
        verbose_name = u"Фильтр"
        verbose_name_plural = u"Фильтры"
        ordering = ['sort', 'title']

    def __str__(self):
        if self.parent:
            return '(%s) [%s] %s' % (str(self.parent.tag), self.parent.title, self.title)
        else:
            return '(%s) %s' % (str(self.tag), self.title)

    def save(self):
        if not self.link:
            trans_title = pytils.translit.slugify(self.title)
            self.link = trans_title
        super(Filter, self).save()


class GroupFilter(models.Model):
    tag = models.ForeignKey(Tag, verbose_name=u'Категория', on_delete=models.CASCADE)
    title = models.CharField(max_length=512, verbose_name=u'Название')
    link = models.CharField(max_length=1024, blank=True, null=True)
    sort = models.IntegerField(default=99, verbose_name=u'Порядок')

    is_tag = models.BooleanField(verbose_name=u'Эта группа теги', default=False)

    filter = models.ManyToManyField(Filter, verbose_name=u'Фильтры')

    class Meta:
        verbose_name = u"Группа фильтров"
        verbose_name_plural = u"Группы фильтров"
        ordering = ['tag', 'sort', 'title']

    def __str__(self):
        return self.title


class FilterDescription(models.Model):
    filter = models.ForeignKey(Filter, verbose_name=u'Фильтр', unique=True, default=1, on_delete=models.CASCADE)
    section = models.CharField(max_length=128, choices=SECTION, verbose_name=u'Раздел')

    title = models.CharField(max_length=512, verbose_name=u'Заголовок h1', blank=True, null=True)
    head_title = models.CharField(max_length=512, verbose_name=u'<title>', blank=True, null=True)
    meta_descroption = models.CharField(max_length=1024, verbose_name=u'<descroption>', blank=True, null=True)
    meta_keywords = models.CharField(max_length=1024, verbose_name=u'<keywords>', blank=True, null=True)

    link_title = models.CharField(max_length=128, verbose_name=u'Название ссылки')
    link_url = models.CharField(max_length=128, verbose_name=u'ссылка')

    footer_view = models.BooleanField(verbose_name=u'Выводить в подвале', default=False)

    def get_absolute_url(self):
        return self.link_url

    class Meta:
        verbose_name = u"Уникальная страница для фильтрв"
        verbose_name_plural = u"Уникальные страницы для фильтров"

    def __str__(self):
        return '%s %s' % (self.filter.tag.title, self.filter.title)


class FilterSitemapLink(models.Model):

    id = models.PositiveIntegerField(primary_key=True, unique=True)
    title = models.CharField(max_length=512)
    keywords = models.CharField(max_length=512)
    slug = models.CharField(max_length=512, null=True)
    filters = models.ManyToManyField(to=Filter)
    producer = models.ForeignKey(to=Producer, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return '/c/slug/%s/' % self.slug

    def get_tag(self):
        if self.filters.count() > 0:
            return self.filters.first().tag
        return self.producer.deckitem_set.first().tag


class Deckitem(models.Model):
    tag = models.ForeignKey(Tag, verbose_name=u'Главная категория', related_name='maintag', on_delete=models.CASCADE)
    all_tags = models.ManyToManyField('Tag', verbose_name=u'Все категории', through='DeckitemTag')
    filters = models.ManyToManyField('Filter', verbose_name=u'Фильтры', through='FilterDeckitem', blank=True)
    segment_new = models.ForeignKey(Segment, verbose_name=u'Сегмент', on_delete=models.CASCADE)

    producer = models.ForeignKey(Producer, verbose_name=u'Производитель', on_delete=models.CASCADE)

    title = models.CharField(max_length=1024, verbose_name=u'Заголовок RU')
    title_en = models.CharField(max_length=1024, verbose_name=u'Заголовок EN', blank=True, null=True)

    description = RichTextUploadingField(blank=True, null=True, verbose_name=u'Описание')

    composition_title = models.CharField(max_length=128, blank=True, null=True, verbose_name=u'Название блока',
                                         default=u'Состав')
    composition = RichTextUploadingField(blank=True, null=True, verbose_name=u'Второй блок')

    ration_title = models.CharField(max_length=128, blank=True, null=True, verbose_name=u'Название блока',
                                    default=u'Суточный рацион')
    ration = RichTextUploadingField(blank=True, null=True, verbose_name=u'Третий блок')

    super_description = models.TextField(verbose_name=u'Супер описание', blank=True, null=True)

    date = models.DateTimeField(auto_now_add=True, verbose_name=u'Дата')
    link = models.CharField(max_length=1024, blank=True, null=True)
    sale = models.FloatField(blank=True, null=True, verbose_name=u'Скидка')
    price = models.IntegerField(blank=True, null=True, verbose_name=u'Цена')
    type = models.CharField(max_length=16, verbose_name=u'Тип', choices=ITEM_TYPE, null=True, blank=True)
    on_main = models.BooleanField(verbose_name=u'На главную?', default=False)
    active = models.BooleanField(verbose_name=u'Активный?', default=True)

    # META данные
    html_title = models.CharField(u"Head <title>", max_length=255, default=u"", blank=True)
    meta_description = models.CharField(u"<meta> description", max_length=255, blank=True)
    meta_keywords = models.CharField(u"<meta> keywords", max_length=255, blank=True)
    seo_text = RichTextField(u"SEO текст", blank=True)
    header = models.CharField(verbose_name=u'<h1>', max_length=256, blank=True, null=True)

    views = models.IntegerField(verbose_name=u'Просмотров', default=0)

    order = models.IntegerField(verbose_name=u'Порядковый номер', default=999)
    number_of_purchases = models.IntegerField(verbose_name=u'Рейтинг', default=0)

    last_edit = models.DateTimeField(verbose_name=u'Дата изменения', null=True, blank=True)
    availability = models.IntegerField(verbose_name=u'Наличие товара', default=3, choices=AVAILABILTY)

    def __str__(self):
        return '[%s] %s' % (self.producer.title, self.title)

    def get_absolute_url(self):
        return '/c/i/%s/' % self.link

    def item_sort_key(self, item):
        return AVAILABILTY_SORT_DICT[int(item.availability)]

    def items(self):
        items_not_sorted = Item.objects.filter(deckitem=self.id, active=1)
        result = sorted(items_not_sorted, key=self.item_sort_key)
        return result
    
    def first_available_item(self):
        query = self.item_set.filter(active=1).order_by('real_price')
        if query.filter(availability__gt=0).exists():
            return query.filter(availability__gt=0).first()
        return query.first()

    def sale_items(self):
        items = Item.objects.filter(deckitem=self.id, active=1).order_by('real_price', 'id')
        items_result = []
        for i in items.values():
            if ItemSale.objects.filter(date_end__gte=datetime.datetime.now(), item=i['id']).count() > 0:
                this_item = Item.objects.get(id=i['id'])
                items_result.append(this_item)
        return items_result

    def photo_thumb(self):
        if ItemPhoto.objects.filter(deckitem=self.id).exists():
            try:
                return format_html(u'<img src="{0}">', ItemPhoto.objects.filter(deckitem=self.id).order_by('order', 'id')[0].cart_thumbnail.url)
            except:
                return False
        return '-'

    def search_thumb(self):
        if ItemPhoto.objects.filter(deckitem=self.id).exists():
            try:
                return format_html(u'<img src="{0}" height="60px">', ItemPhoto.objects.filter(deckitem=self.id).order_by('order', 'id')[0].search_thumbnail.url)
            except:
                return False
        return '-'

    photo_thumb.allow_tags = True
    photo_thumb.short_description = u'Фото'

    def photo_big_thumb_absolute_url(self):
        if ItemPhoto.objects.filter(deckitem=self.id).exists():
            try:
                return format_html(u'<img src="https://kostochka38.ru{0}">', ItemPhoto.objects.filter(deckitem=self.id).order_by('order', 'id')[0].thumbnail_new.url)
            except:
                return False
        return '-'

    def photo_big_thumb(self):
        if ItemPhoto.objects.filter(deckitem=self.id).exists():
            try:
                return format_html(u'<img src="{0}">', ItemPhoto.objects.filter(deckitem=self.id).order_by('order', 'id')[0].thumbnail_new.url)
            except:
                return False
        return '-'

    photo_big_thumb.allow_tags = True
    photo_big_thumb.short_description = u'Фото'

    def photos(self):
        return ItemPhoto.objects.filter(deckitem=self.id).order_by('order', 'id')

    def get_active_item_count(self):
        return Item.objects.filter(deckitem=self.id, active=True).count()

    get_active_item_count.allow_tags = True
    get_active_item_count.short_description = u'Активных элементов'

    def cover(self):
        photos = ItemPhoto.objects.filter(deckitem=self.id).order_by('order','id')
        if photos.filter(cover=True).count() > 0:
            return photos.filter(cover=True)[0:1]
        elif photos.count() > 0:
            return photos[0:1]
        else:
            return False

    def get_last_buy_date(self):
        items = Item.objects.filter(deckitem=self.id).values_list('id')
        logs = ReserveLog.objects.filter(item__id__in=items).order_by('-date')
        last_date = ' - '
        internal = '-'
        if logs:
            last_date = logs[0].date
            internal = datetime.datetime.now() - last_date
        return '%s (%s)' % (last_date, internal)

    get_last_buy_date.short_description = u'Дата продажи'

    def min_price(self):
        if Item.objects.filter(deckitem=self.id, active=1).order_by('real_price'):
            return int(Item.objects.filter(deckitem=self.id, active=1).order_by('real_price')[0]['real_price'])
        return 0

    class Meta:
        ordering = ["-id"]
        verbose_name = u"Элемент каталога"
        verbose_name_plural = u"Элементы каталога"

    def save(self):

        if self.id:
            old_deckitem = Deckitem.objects.get(id=self.id)
            if old_deckitem.active != self.active and not self.active:
                items = Item.objects.filter(deckitem=self.id).update(active=False)

        super(Deckitem, self).save()
        trans_title = pytils.translit.slugify(self.title)
        if not self.link:
            self.link = trans_title + '_' + str(self.id)
        self.last_edit = datetime.datetime.now()
        super(Deckitem, self).save()


class ItemPhoto(models.Model):
    order = models.PositiveSmallIntegerField(verbose_name=u'Порядок', default=99)
    deckitem = models.ForeignKey(Deckitem, verbose_name=u'Товар', on_delete=models.CASCADE)
    item = models.OneToOneField(to='Item',
                                on_delete=models.SET_NULL,
                                null=True,
                                blank=True,
                                verbose_name=u'вес/тип с ценой')
    title = models.CharField(verbose_name=u'Название', max_length=128, null=True, blank=True)
    cover = models.BooleanField(verbose_name=u'Обложка', default=False)
    original_image = ProcessedImageField(upload_to=get_file_path,
                                         options={'qaulity': 80},
                                         processors=[ResizeToFit(DEFAULT_PHOTO_WIDTH, DEFAULT_PHOTO_HEIGHT), ],
                                         verbose_name=u'фото')
    thumbnail = ImageSpecField(source='original_image', processors=[ResizeToFit(180, 130), ],
                               options={'quality': 80})
    thumbnail_new = ImageSpecField(source='original_image', processors=[ResizeToFit(170, 160), ],
                                   options={'quality': 80})
    thumbnail_new_lazy = ImageSpecField(source='original_image', processors=[ResizeToFit(170, 160), ],
                                        options={'quality': 1})
    cart_thumbnail = ImageSpecField(source='original_image', processors=[ResizeToFit(100, 45), ],
                                    options={'quality': 80})
    thumbnail_inner = ImageSpecField(source='original_image', processors=[ResizeToFit(160, 160), ],
                                     options={'quality': 80})
    thumbnail_item = ImageSpecField(source='original_image', processors=[ResizeToFit(58, 58), ],
                                    options={'quality': 80})
    fullimage = ImageSpecField(source='original_image', processors=[ResizeToFit(800, 800), ],
                               options={'quality': 80})
    search_thumbnail = ImageSpecField(source='original_image', processors=[ResizeToFit(100, 100), ],
                               options={'quality': 80})
    directory_string_var = 'goods_photo'

    def __str__(self):
        return u'[' + self.deckitem.title + u'] '

    def photo(self):
        return '<img src="%s">' % self.cart_thumbnail.url

    photo.allow_tags = True
    photo.short_description = u'Фото'

    def photo_inline(self):
        return format_html('<img src="{0}" style="margin: 0 5px;">', self.thumbnail_new.url)

    photo_inline.allow_tags = True
    photo_inline.short_description = u'Превью'

    class Meta:
        verbose_name = u"Фото товара"
        verbose_name_plural = u"Фото товара"
        ordering = ['order']


class DeckitemTag(models.Model):
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    deckitem = models.ForeignKey(Deckitem, on_delete=models.CASCADE)

    class Meta:
        db_table = 'catalog_deckitem_all_tags'
        auto_created = Tag


class FilterDeckitem(models.Model):
    filter = models.ForeignKey(Filter, on_delete=models.CASCADE)
    deckitem = models.ForeignKey(Deckitem, on_delete=models.CASCADE)

    class Meta:
        db_table = 'catalog_filter_deckitem'
        auto_created = Filter


class Commentitem(models.Model):
    deckitem = models.ForeignKey(Deckitem, on_delete=models.CASCADE)
    name = models.CharField(max_length=128, verbose_name=u'Имя', default=False)
    text = models.TextField(verbose_name=u'Отзыв')
    date = models.DateTimeField(auto_now_add=True, verbose_name=u'Дата публикации')
    status = models.CharField(max_length=1, choices=STATUS, verbose_name=u'Статус', default='1')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = u"Отзыв о товаре"
        verbose_name_plural = u"Отзывы о товаре"

class WareHouse(models.Model):
    class Meta:
        verbose_name = u"Склад"
        verbose_name_plural = u"Склады"

    name = models.CharField(max_length=250, verbose_name=u"Название склада")
    full_name = models.TextField(blank=True, null=True, verbose_name=u'Полное название')
    address = models.CharField(blank=True, null=True, max_length=250, verbose_name=u"Адрес")
    phone = models.CharField(blank=True, null=True, max_length=250, verbose_name=u"Номер телефона")
    type = models.IntegerField(default=0, choices=TYPE_OF_WAREHOUSE, verbose_name=u"Тип склада")
    default_customer = models.ForeignKey(Account, blank=True, null=True, verbose_name="Покупатель по-умолчанию", on_delete=models.SET_NULL)
    # Понедельник
    mon_start = models.TimeField(verbose_name=u'Начало рабочего дня', null=True, blank=True)
    mon_end = models.TimeField(verbose_name=u'Окончание рабочего дня', null=True, blank=True)
    # Вторник
    tue_start = models.TimeField(verbose_name=u'Начало рабочего дня', null=True, blank=True)
    tue_end = models.TimeField(verbose_name=u'Окончание рабочего дня', null=True, blank=True)
    # Среда
    wed_start = models.TimeField(verbose_name=u'Начало рабочего дня', null=True, blank=True)
    wed_end = models.TimeField(verbose_name=u'Окончание рабочего дня', null=True, blank=True)
    # Четверг
    thu_start = models.TimeField(verbose_name=u'Начало рабочего дня', null=True, blank=True)
    thu_end = models.TimeField(verbose_name=u'Окончание рабочего дня', null=True, blank=True)
    # Пятница
    fri_start = models.TimeField(verbose_name=u'Начало рабочего дня', null=True, blank=True)
    fri_end = models.TimeField(verbose_name=u'Окончание рабочего дня', null=True, blank=True)
    # Суббота
    sat_start = models.TimeField(verbose_name=u'Начало рабочего дня', null=True, blank=True)
    sat_end = models.TimeField(verbose_name=u'Окончание рабочего дня', null=True, blank=True)
    # Воскресенье
    sun_start = models.TimeField(verbose_name=u'Начало рабочего дня', null=True, blank=True)
    sun_end = models.TimeField(verbose_name=u'Окончание рабочего дня', null=True, blank=True)

    def __str__(self):
        return u'{}'.format(self.name)

    def get_left_items(self):
        return self.leftitem_set.all()

    def get_items_to_print(self):
        return self.get_left_items()

    def prepare_balance(self):
        self.set_segments_for_balance()
        return ""

    def set_segments_for_balance(self):
        self.segments = Segment.objects.filter(deckitem__item__leftitem__warehouse=self, in_balans=True).distinct()
        count_all = 0
        sum_all = 0
        for i in self.segments:
            i.count = i.get_item_count(self)
            count_all += i.count
            i.sum = i.get_items_sum(self)
            sum_all += i.sum
        self.count_all = count_all
        self.sum_all = sum_all

    def is_opened(self):
        now = timezone.now()
        time_now = now.time()
        day_abbr = calendar.day_abbr[now.weekday()].lower()
        time_start = getattr(self, '%s_start' % day_abbr)
        time_end = getattr(self, '%s_end' % day_abbr)
        if time_start is None or time_end is None: # Выходной
            return '<span class="label label-danger" style="color: white !important;">Закрыто<span/>'
        if time_start <= time_now and time_end >= time_now:
            return '<span class="label label-success" style="color: white !important;">Открыто<span/>'
        return '<span class="label label-danger" style="color: white !important;">Закрыто<span/>'



class Item(models.Model):
    deckitem = models.ForeignKey(Deckitem, verbose_name=u'Товар', on_delete=models.CASCADE)

    # warehouse = models.ForeignKey(WareHouse, verbose_name=u'К складу', on_delete=models.CASCADE, default=None, null=True)
    warehouse = models.ManyToManyField(WareHouse)
    date_created = models.DateTimeField(auto_now_add=True, verbose_name=u'Дата добавления')

    real_price = models.FloatField(verbose_name=u'Цена закупки')
    price = models.IntegerField(verbose_name=u'Цена', null=True, blank=True)

    sort_price = models.IntegerField(verbose_name=u'Цена для сортировки', null=True, blank=True)

    weight = models.CharField(max_length=1024, verbose_name=u'Вес/Размер')

    article = models.CharField(max_length=64, verbose_name=u'Артикул')
    code = models.CharField(max_length=64, verbose_name=u'Код')
    barcode = models.TextField(verbose_name=u'Штрихкод', default='')

    active = models.BooleanField(verbose_name=u'Активный', default=True)
    new = models.BooleanField(verbose_name=u'Новинка', default=True)

    availability = models.IntegerField(verbose_name=u'Наличие товара', default=3, choices=AVAILABILTY)
    quantity_in_stock = models.IntegerField(verbose_name=u'У поставщика', default=0)
    quantity_in_reserve = models.IntegerField(verbose_name=u'На складе', default=0)
    temporarily_unavailable = models.BooleanField(verbose_name=u'Временно недоступен', default=False)

    minimum_need = models.IntegerField(verbose_name=u'Необходимый минимум', default=0)
    count_for_zakaz = models.IntegerField(verbose_name=u'Кол-во дозаказа', default=0)

    number_of_purchases = models.IntegerField(verbose_name=u'Куплено раз', default=0, help_text=u'количество покупок')
    count_of_purchases = models.IntegerField(verbose_name=u'Куплено к-во', default=0,
                                             help_text=u'количество купленного товара')

    order = models.PositiveIntegerField(verbose_name=u'Порядковый номер', default=999)

    amount_in_block = models.IntegerField(verbose_name=u'Кол-во в упаковке', default=0)

    heavy = models.BooleanField(verbose_name=u'Тяжелый', default=False)

    last_order_date = models.DateField(verbose_name=u'Последняя продажа', null=True, blank=True)
    on_main = models.BooleanField(verbose_name=u'На главной', default=False)

    def get_photo(self):
        photos = self.deckitem.itemphoto_set.all().order_by('order','id')
        return photos.filter(item=self).first() or photos.filter(cover=True).first() or photos.first()

    def get_photo_thumbnail(self):
        photo = self.get_photo()
        if photo is not None:
            return format_html('<img height="100px" src="{0}">', photo.thumbnail.url)
        return '-'
    get_photo_thumbnail.allow_tags = True
    get_photo_thumbnail.short_description = u'Фото'

    def get_photo_thumbnail_small(self):
        photo = self.get_photo()
        if photo is not None:
            return format_html('<img height="40px" src="{0}">', photo.thumbnail.url)
        return '-'
    get_photo_thumbnail.allow_tags = True
    get_photo_thumbnail.short_description = u'Фото'

    def get_current_price_with_intspace(self):
        from django.utils.encoding import force_str

        def intspace(value):
            orig = force_str(value)
            new = re.sub("^(-?\d+)(\d{3})", '\g<1> \g<2>', orig)
            if orig == new:
                return new
            else:
                return intspace(new)
        if self.get_sale_online():
            value = intspace(str("%.2f" % self.current_sale_online_price()).replace(".", ","))
        else:
            value = intspace(str(self.current_price()).split(".")[0])
        return value

    def current_price(self):
        if self.price:
            price = self.price
        else:
            if not self.heavy:
                price = ceil(self.real_price * self.deckitem.producer.margin)
            else:
                price = ceil(self.real_price * self.deckitem.producer.margin_heavy)
        return price

    def current_price_opt(self):
        if self.deckitem.producer.margin_opt:
            price = round(self.real_price * self.deckitem.producer.margin_opt, 2)
            return price
        else:
            return self.current_price()

    def current_price_zavodchik(self):
        if self.deckitem.producer.margin_zavodchiki:
            price = round(self.real_price * self.deckitem.producer.margin_zavodchiki, 2)
            return price
        else:
            return self.current_price()

    current_price.short_description = u'Цена продажи'
    current_price.admin_order_field = 'sort_price'

    def get_action_online(self):
        itemactions = self.newitems_set.filter(
            Q(new__exp_date__gte=datetime.datetime.now()) &
            Q(new__status='2') &
            Q(new__complete=False) &
            Q(new__action_target__in=[0, 1])
        )
        if itemactions.count() == 1:
            return itemactions.first().new
        return None

    def get_sale_online(self):
        itemsales = self.itemsale_set.filter(
            Q(date_end__gte=datetime.datetime.now()) &
            Q(sale_target__in=[0, 1])
        )
        if itemsales.count() > 1:
            return max(itemsales, key=lambda itemsale: itemsale.sale).sale
        elif itemsales.count() == 1:
            return itemsales.first().sale
        else:
            action = self.get_action_online()
            if action:
                return action.discount_size
        return None

    def get_sale_online_description(self):
        itemsales = self.itemsale_set.filter(
            Q(date_end__gte=datetime.datetime.now()) &
            Q(sale_target__in=[0, 1])
        )
        if itemsales.count() > 1:
            return max(itemsales, key=lambda itemsale: itemsale.sale).description
        elif itemsales.count() == 1:
            return itemsales.first().description
        else:
            action = self.get_action_online()
            if action:
                return action.title
        return None

    def current_sale_online_price(self):
        sale = self.get_sale_online()
        if sale:
            return round(self.current_price() * (float(100 - sale) / 100), 2)
        return None

    def get_action_retail(self):
        itemactions = self.newitems_set.filter(
            Q(new__exp_date__gte=datetime.datetime.now()) &
            Q(new__status='2') &
            Q(new__complete=False) &
            Q(new__action_target__in=[0, 2])
        )
        if itemactions.count() == 1:
            return itemactions.first().new
        return None

    def get_sale_retail(self):
        itemsales = self.itemsale_set.filter(
            Q(date_end__gte=datetime.datetime.now()) &
            Q(sale_target__in=[0, 2])
        )
        if itemsales.count() > 1:
            return max(itemsales, key=lambda itemsale: itemsale.sale).sale
        elif itemsales.count() == 1:
            return itemsales.first().sale
        else:
            action = self.get_action_retail()
            if action:
                return action.discount_size
        return None

    def current_sale_retail_price(self):
        sale = self.get_sale_retail()
        if sale:
            return round(self.current_price() * (float(100 - sale) / 100), 2)
        return None

    def get_thumbnail(self):
        return self.deckitem.photo_thumb()

    get_thumbnail.allow_tags = True
    get_thumbnail.short_description = u'Фото'

    def buy_count_3_month(self):
        stop_date = datetime.datetime.now()
        start_date = stop_date - datetime.timedelta(days=90)
        counts = ZakazGoods.objects.filter(zakaz__date__gte=start_date, zakaz__date__lt=stop_date, item=self,
                                           zakaz__status=6).exclude(sale__gte=25, zakaz__owner__id=577).aggregate(sum=Sum('quantity'))['sum']
        if counts is None:
            counts = format_html(u"<span style='color:#b26'>==&nbsp;{0}</span>", 0)
        else:
            counts = format_html(u"<span style='color:#2b6'>==&nbsp;<b>{0}</b></span>",
                                 ("%.2f" % (float(counts) / 6)).replace('.', ','))
            warehoeses = WareHouse.objects.all()
            for i in warehoeses:
                count = ZakazGoods.objects.filter(zakaz__date__gte=start_date, zakaz__date__lt=stop_date, item=self,
                                                  zakaz__status=6, zakaz__warehouse=i).exclude(sale__gte=25,
                                                                                               zakaz__owner__id=577).aggregate(
                    sum=Sum('quantity'))['sum']
                if count is None:
                    count = 0
                counts_str = u'%s %s ' % (i.name[0:2], ("%.2f" % (float(count) / 6)).replace('.', ','))
                counts += format_html(u'<br>{0} ', counts_str)

        return counts
    buy_count_3_month.allow_tags = True
    buy_count_3_month.short_description = u'Куп. за 3 мес.'
    buy_count_3_month.admin_order_field = '_buy_count_3_month'

    def buy_count_3_month_by_warehouse_round(self, warehouse_id):
        stop_date = datetime.datetime.now()
        start_date = stop_date - datetime.timedelta(days=90)
        counts = ZakazGoods.objects.filter(zakaz__date__gte=start_date, zakaz__date__lt=stop_date, item=self,
                                           zakaz__status=6, zakaz__warehouse__id=warehouse_id).exclude(sale__gte=25, zakaz__owner__id=577).aggregate(sum=Sum('quantity'))['sum']
        if counts is None:
            counts = 0
        else:
            counts = round(float(counts) / 6)

        return counts


    def buy_count_3_month_by_warehouse_ceil(self, warehouse_id):
        stop_date = datetime.datetime.now()
        start_date = stop_date - datetime.timedelta(days=90)
        counts = ZakazGoods.objects.filter(zakaz__date__gte=start_date, zakaz__date__lt=stop_date, item=self,
                                           zakaz__status=6, zakaz__warehouse__id=warehouse_id).exclude(sale__gte=25, zakaz__owner__id=577).aggregate(sum=Sum('quantity'))['sum']
        if counts is None:
            counts = 0
        else:
            counts = ceil(float(counts) / 6)

        return counts

    def go_to_deckitem(self):
        return format_html(u"<a href='/DgJrfdJg/catalog/deckitem/{0}/'>Перейти к элементу каталога &rarr;</a>",
                           self.deckitem.id)

    go_to_deckitem.allow_tags = True
    go_to_deckitem.short_description = u'Товар'

    def item__quantity_in_reserve(self):
        quantity_in_reserve_str = format_html(u'== {0}', self.quantity_in_reserve)
        warehoeses = WareHouse.objects.all()
        for i in warehoeses:
            left = 0
            if LeftItem.objects.filter(warehouse=i, item=self).count() == 1:
                left = LeftItem.objects.get(warehouse=i, item=self).left
            warehouse_str = u'%s %s ' % (i.name[0:2], left)
            quantity_in_reserve_str += format_html(u'<br>{0} ', warehouse_str)
        return format_html(u"{0}", quantity_in_reserve_str)

    def quantity_in_reserve_by_warehouse(self, warehouse_id):
        quantity = 0
        if LeftItem.objects.filter(item=self, warehouse__id=warehouse_id).exists():
            quantity = LeftItem.objects.filter(item=self, warehouse__id=warehouse_id).first().left
        return quantity

    def vreserve(self):
        count = 0
        color = 'green'
        orders = format_html('')
        if ZakazGoods.objects.filter(item=self.id, zakaz__status__in=[2, 3, 4, 5, 31]).aggregate(sum=Sum('quantity'))[
            'sum']:
            count = \
                ZakazGoods.objects.filter(item=self.id, zakaz__status__in=[2, 3, 4, 5, 31]).aggregate(
                    sum=Sum('quantity'))[
                    'sum']
            for i in ZakazGoods.objects.filter(item=self.id, zakaz__status__in=[2, 3, 4, 5, 31]).values():
                orders += format_html('<br><a target="_blank" href="/DgJrfdJg/catalog/zakaz/{0}/">{1}&rarr;</a>',
                                      i['zakaz_id'], i['zakaz_id'])
            color = 'red'
        return format_html("<span style='color: {0};'>{1}</span>{2}", color, count, orders)

    vreserve.allow_tags = True
    vreserve.short_description = u'Резерв'

    def vreserve_count_for_automovements(self):
        count = 0
        if ZakazGoods.objects.filter(item=self.id, zakaz__status__in=[2, 3, 31, 4, 5]).exclude(zakaz__owner__id=577).aggregate(sum=Sum('quantity'))['sum']:
            count = ZakazGoods.objects.filter(item=self.id, zakaz__status__in=[2, 3, 31, 4, 5]).exclude(id=self.id).exclude(zakaz__owner__id=577).aggregate(sum=Sum('quantity'))['sum']
        return count

    def get_suplier(self):
        return self.deckitem.segment_new

    get_suplier.short_description = u'Поставщик'

    def get_absolute_url(self):
        return '/c/i/%s/' % self.deckitem.link

    def __str__(self):
        if self.deckitem.title_en:
            return u'[' + self.deckitem.producer.title + u'] ' + self.deckitem.title + u' - ' + self.deckitem.title_en + u' (' + self.weight + u')'
        else:
            return u'[' + self.deckitem.producer.title + u'] ' + self.deckitem.title + u' (' + self.weight + u')'

    def get_title_kassir(self):
        return u'[{}] {}'.format(self.deckitem.producer.title, self.deckitem.title)

    def title(self):
        if self.deckitem.title_en:
            return u'[' + self.deckitem.producer.title + u'] ' + self.deckitem.title + u' (' + self.weight + u')<br>' + self.deckitem.title_en
        else:
            return u'[' + self.deckitem.producer.title + u'] ' + self.deckitem.title + u' (' + self.weight + u')'

    title.allow_tags = True
    title.short_description = u'Название'

    def count_left(self):
        _sum = self.leftitem_set.all().aggregate(Sum('left')).get('left__sum', 0)
        if not _sum:
            _sum = 0
        return _sum

    def get_name_to_display(self):
        title = u'{}, {}'.format(self.producer, self.title)
        return title

    def get_quantity_in_reserve_by_warehouse(self, warehouse):
        count = 0
        if LeftItem.objects.filter(warehouse=warehouse, item=self).exists():
            count = LeftItem.objects.filter(warehouse=warehouse, item=self).first().left
        return count

    def get_warehouse_available_count(self):
        '''
        Возвращает количество складов, на которых товар доступен для
        приобретения (с учётом активных заказов).

        Если товар находится не в интернет магазине (тип склада "склад"),
        то дополнительно проверяется количество единиц товара у постовщика.
        '''

        warehouses = WareHouse.objects.all()
        count = 0
        for warehouse in warehouses:
            count_zakaz = self.zakazgoods_set.filter(zakaz__status__in=[2, 3, 4, 5, 31], zakaz__warehouse=warehouse).exclude(zakaz__owner__id=577).aggregate(sum=Sum('quantity'))['sum'] or 0
            left_item = 0
            if LeftItem.objects.filter(item=self, warehouse=warehouse).exists():
                left_item = LeftItem.objects.filter(item=self, warehouse=warehouse).first().left

            if warehouse.type == 0:
                if left_item + self.quantity_in_stock - count_zakaz > 0:
                    count += 1
            else:
                if left_item - count_zakaz > 0:
                    count += 1
        return count

    def save(self, *args, **kwargs):
        if self.id:
            old_item = Item.objects.get(id=self.id)
            if old_item.availability != self.availability:
                new_itemavailabilitylog = ItemAvailabilityLog(
                    item_id=self.id,
                    availability=self.availability
                )
                new_itemavailabilitylog.save()
        super(Item, self).save()

    class Meta:
        verbose_name = u"Вес/тип с ценой"
        verbose_name_plural = u"Вес/тип с ценой"
        ordering = ['deckitem__producer__title', 'deckitem__title', 'real_price']



class BasketOfGoodItem(models.Model):
    item = models.ForeignKey(Item, verbose_name=u'Товар', on_delete=models.CASCADE)
    date_started = models.DateTimeField(verbose_name=u'Дата запуска')
    date_ended = models.DateTimeField(verbose_name=u'Дата окончания')


    class Meta:
        verbose_name = u"Товар для корзины добра"
        verbose_name_plural = u"Товары для корзины добра"
        ordering = ['date_ended', 'date_started']


class ItemAvailabilityLog(models.Model):
    item = models.ForeignKey(Item, verbose_name=u'Вес/Тип с ценой', on_delete=models.CASCADE)
    availability = models.IntegerField(verbose_name=u'Статус наличия', choices=AVAILABILTY)
    date = models.DateTimeField(auto_now_add=True, verbose_name=u'Дата смены')

    class Meta:
        verbose_name = u"Лог статусов наличия"
        verbose_name_plural = u"Лог статусов наличия"
        ordering = ['-date']


SALE_TARGET = (
    (0, u'Везде'),
    (1, u'Онлайн'),
    (2, u'Розница')
)


class ItemSale(models.Model):
    item = models.ForeignKey(Item, verbose_name=u'товар', on_delete=models.CASCADE)
    sale = models.FloatField(verbose_name=u'Скидка %', blank=True, null=True)
    sale_target = models.PositiveSmallIntegerField(verbose_name=u'Область применения', choices=SALE_TARGET, default=0)
    show = models.BooleanField(verbose_name=u'Отображать в разделе акции', default=False)
    date_end = models.DateField(verbose_name=u'До', blank=True, null=True)
    description = models.CharField(verbose_name=u'Описание', max_length=512, blank=True, null=True)

    def __str__(self):
        return "%s (%s)" % (self.item.deckitem.title, self.item.weight)

    class Meta:
        ordering = ['date_end', ]
        verbose_name = u"Скидка на товар"
        verbose_name_plural = u"Скидки на товар"


class ItemMail(models.Model):

    class Meta:
        verbose_name = u"Товар для рассылки"
        verbose_name_plural = u"Товары для рассылок"

    item = models.ForeignKey(Item, verbose_name=u'Товар', on_delete=models.CASCADE)
    mail = models.ForeignKey(MailTemplate, verbose_name=u"Шаблон рассылки", on_delete=models.CASCADE)


class TempZakaz(models.Model):
    owner = models.ForeignKey(Account, verbose_name=u'Пользователь', null=True, blank=True, on_delete=models.CASCADE)
    summ = models.FloatField(verbose_name=u'Сумма')
    date = models.DateTimeField(verbose_name=u'Дата')
    hash = models.CharField(max_length=512, verbose_name=u'хэш-код', null=True, blank=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = u"Корзина"
        verbose_name_plural = u"Корзины"
        ordering = ['-date']


class TempZakazGoods(models.Model):
    action = models.ForeignKey(New, verbose_name='Акция', null=True, blank=True, on_delete=models.SET_NULL)
    zakaz = models.ForeignKey(TempZakaz, verbose_name=u'Заказ', on_delete=models.CASCADE)
    item = models.ForeignKey(Item, verbose_name=u'Товар', on_delete=models.CASCADE)
    quantity = models.IntegerField(verbose_name=u'Количество')
    sale = models.IntegerField(verbose_name=u'скидка %', blank=True, null=True)
    summ = models.FloatField(verbose_name=u'Сумма')
    presale = models.BooleanField(verbose_name=u'Предзаказ', default=False)
    summ_changed = models.BooleanField(
        default=False,
        verbose_name=u'Сумма изменилась',
        help_text=(
            u'Устонавливается в "True", если стоимость товара была изменена, '
            u'чтобы один раз уведомить пользователя об изменении суммы заказа'
        )
    )
    availability_changed = models.BooleanField(
        default=False,
        verbose_name=u'Наличие изменилось (поле на данный момент не используется)',
        help_text=(
            u'Устонавливается в "True", если наличие товара было изменено, '
            u'чтобы один раз уведомить пользователя об изменении наличия товара'
        )
    )
    basket_of_good = models.BooleanField(verbose_name=u'Корзина добра', default=False)

    def __str__(self):
        return str(self.zakaz)

    def get_thumbnail(self):
        return self.item.get_photo_thumbnail()

    get_thumbnail.allow_tags = True
    get_thumbnail.short_description = u'Фото'

    class Meta:
        verbose_name = u"Товар в корзине"
        verbose_name_plural = u"Товар в корзине"
        ordering = ['item__deckitem__producer', 'item__deckitem__title']

    def save(self):
        action = self.item.get_action_online()
        if action:
            self.action = action

        self.sale = self.item.get_sale_online()

        if self.item.availability != 0:
            if self.sale:
                self.summ = round(self.item.current_sale_online_price(), 2) * int(self.quantity)
            elif self.zakaz.owner and self.zakaz.owner.sale:
                self.summ = round(self.item.current_price() * float(self.zakaz.owner.sale), 2) * int(self.quantity)
            else:
                self.summ = round(self.item.current_price(), 2) * int(self.quantity)
        else:
            self.summ = 0

        super(TempZakazGoods, self).save()

        self.zakaz.summ = self.zakaz.tempzakazgoods_set.all().aggregate(summ=Sum('summ'))['summ'] or 0
        self.zakaz.save()

    def delete(self):
        super(TempZakazGoods, self).delete()
        if TempZakazGoods.objects.filter(zakaz=self.zakaz.id):
            self.zakaz.summ = TempZakazGoods.objects.filter(zakaz=self.zakaz.id).aggregate(summ=Sum('summ'))['summ']
            self.zakaz.save()
        else:
            self.zakaz.delete()


class Courier(models.Model):
    name = models.CharField(max_length=256, verbose_name=u'ФИО', default='Name')
    create_date = models.DateTimeField(auto_now_add=True, verbose_name=u'Дата создания')
    phone = models.CharField(max_length=16, verbose_name=u'Телефон', null=True, blank=True)
    dop_phone = models.CharField(max_length=16, verbose_name=u'Дополнительный телефон', null=True, blank=True)
    address = models.CharField(max_length=256, verbose_name=u'Адрес', null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = u"Курьер"
        verbose_name_plural = u"Курьеры"


F_STATE = (
    (1, u'Отправлено на ФР'),
    (2, u'ОК'),
    (3, u'Ошибка'),
)
MONTH_ARR = {1: u'Янв', 2: u'Фев', 3: u'Март', 4: u'Апр', 5: u'Май', 6: u'Июнь', 7: u'Июль', 8: u'Авг', 9: u'Сен', 10: u'Окт', 11: u'Ноя', 12: u'Дек'}


class Zakaz(models.Model):
    owner = models.ForeignKey(Account, verbose_name=u'Пользователь', on_delete=models.CASCADE)
    summ = models.FloatField(verbose_name=u'Сумма заказа', default=0)
    cost = models.FloatField(verbose_name=u'Стоимость', null=True, blank=True)
    revenue = models.FloatField(verbose_name=u'Доход', null=True, blank=True)
    real_sum = models.IntegerField(verbose_name=u'К оплате', default=0, null=True, blank=True)

    date = models.DateTimeField(verbose_name=u'Дата', auto_now_add=True)
    date_end = models.DateTimeField(verbose_name=u'Дата завершения', null=True, blank=True)
    status = models.IntegerField(choices=ORDER_STATUS, default=DEFAULT_ORDER_STATUS, verbose_name=u'Статус')
    paid_client = models.BooleanField(default=False, verbose_name=u'Клиент')
    cash_go_to_kassa = models.BooleanField(default=False, verbose_name=u'Касса')
    paid_courier = models.BooleanField(default=False, verbose_name=u'Курьер')

    extra = models.TextField(blank=True, null=True, verbose_name=u'Комментарий менеджера магазина')
    real_desired_time = models.DateField(blank=True, null=True, verbose_name=u'Дата доставки')

    fio = models.CharField(max_length=128, blank=True, null=True, verbose_name=u'Имя')
    phone = models.CharField(max_length=32, verbose_name=u'Телефон', default=0, null=True, blank=True)
    index = models.CharField(max_length=32, blank=True, null=True, verbose_name=u'Индекс')
    city = models.CharField(max_length=128, blank=True, null=True, verbose_name=u'Город')
    street = models.CharField(max_length=128, blank=True, null=True, verbose_name=u'Улица')
    dom = models.CharField(max_length=64, blank=True, null=True, verbose_name=u'Дом')
    appart = models.CharField(max_length=64, blank=True, null=True, verbose_name=u'Квартира')
    description = models.TextField(blank=True, null=True, verbose_name=u'Комментарий')
    district = models.IntegerField(blank=True, null=True, choices=DISTRICT, verbose_name=u'Район')

    cash = models.FloatField(blank=True, null=True, verbose_name=u"Оплачено наличными")
    non_cash = models.FloatField(blank=True, null=True, verbose_name=u"Оплачено безналом")

    paytype = models.IntegerField(verbose_name=u'Способ оплаты', default=0, choices=PAY_TYPE)
    dostavkatype = models.IntegerField(verbose_name=u'Способ доставки', default=0, choices=DOSTAVKA_TYPE)
    desired_time = models.CharField(max_length=128, blank=True, null=True, verbose_name=u'Время доставки')

    need_call = models.BooleanField(default=False, verbose_name=u'Позвонить?')

    dostavka = models.IntegerField(verbose_name=u'доставка/-скидка', default=0)
    sale_koef = models.FloatField(verbose_name=u'Скидка', choices=SALE_GROUP, default=1)

    autocreate = models.BooleanField(verbose_name=u'Автосоздание', default=False)

    courier = models.ForeignKey(Account, verbose_name=u'Курьер', blank=True, null=True,
                                related_name='courier_zakaz_set',
                                limit_choices_to={'groups__permissions__codename': 'courier'}, on_delete=models.SET_NULL)
    manager = models.ForeignKey(Account, verbose_name=u'Менеджер', blank=True, null=True,
                                related_name='manager_zakaz_set',
                                limit_choices_to={'groups__permissions__codename': 'manager', 'is_active': True}, on_delete=models.SET_NULL)
    cashier = models.ForeignKey(Account, verbose_name=u'Кассир', blank=True, null=True,
                                related_name='cashier_zakaz_set',
                                limit_choices_to={'groups__id': '3'}, on_delete=models.SET_NULL)
    warehouse = models.ForeignKey('WareHouse', related_name='warehouse', default=1, blank=True, null=True, verbose_name=u"Склад", on_delete=models.SET_NULL)

    pickup_warehouse = models.ForeignKey('WareHouse', related_name='pickup_warehouse', blank=True, null=True, verbose_name=u"Пункт выдачи(при самовывозе)", on_delete=models.SET_NULL)

    inbox = models.BooleanField(verbose_name=u'Упаковать для отправки', default=False)
    morning_delivery = models.BooleanField(verbose_name=u'Утренняя доставка', default=False, help_text=u'Галка ставится, если заказ необходимо загрузить сегодня, а доставить на следующий раб. день.')

    # данные фискализацзии
    f_state = models.IntegerField(verbose_name=u'Ф-Статус', blank=True, null=True, choices=F_STATE)
    f_id = models.CharField(verbose_name=u'Ф-ID задачи', blank=True, null=True, max_length=256)
    f_fiscal_data = models.TextField(verbose_name=u'Ф-data', blank=True, null=True)
    f_response = models.TextField(verbose_name=u'Ф-response', blank=True, null=True)
    f_print = models.BooleanField(verbose_name=u'Ф-Печать чека', default=False)
    f_check = models.BooleanField(verbose_name=u'Ф-Фискализировать', default=True)
    f_taxtype = models.CharField(verbose_name=u'Тип налога', blank=True, null=True, max_length=256)

    target_sended = models.BooleanField(verbose_name=u'Цели отправлены', default=False)

    is_refund = models.BooleanField(verbose_name=u'Возврат прихода', default=False)


    def __str__(self):
        return str(self.id)

    def get_pay_type_string(self):
        return dict(PAY_TYPE)[self.paytype]

    def get_status_string(self):
        return dict(ORDER_STATUS)[self.status]

    def last_edit(self):
        if ZakazStatusLog.objects.filter(zakaz=self.id):
            return ZakazStatusLog.objects.filter(zakaz=self.id).order_by('-date')[0:1].values()[0]['date']
        else:
            return False

    def courier_name(self):
        if self.courier:
            if self.courier.last_name:
                return format_html(u'{0} {1}<br> ({2})', self.courier.first_name, self.courier.last_name,
                                   self.courier.username)
            else:
                return format_html(u'{0}<br> ({1})', self.courier.first_name, self.courier.username)
        else:
            return ' - '

    courier_name.allow_tags = True
    courier_name.short_description = u'Курьер'

    def get_short_courier(self):
        courier = '-'
        color = 'black'
        if self.courier:
            if self.courier_id == 3642:
                color = '#FF96EC'
            if self.courier_id == 3095:
                color = '#33B027'
            if self.courier_id == 1827:
                color = 'gray'
            if self.courier_id == 1 or self.courier_id == 142:
                color = '#477EFF'
            courier = format_html(u'<span style="color:{0}"> {1}{2}</span>', color, self.courier.first_name[0:3], self.courier.last_name[0:1])
        return courier

    get_short_courier.allow_tags = True
    get_short_courier.short_description = u'Кур'

    def get_short_paytype(self):
        if self.paytype == 4 and not self.paid_client:
            return format_html(u"<img src = '/static/kostochka38/images/i_oplata_{0}.png' width = '16px'>", 9)
        return format_html(u"<img src = '/static/kostochka38/images/i_oplata_{0}.png' width = '16px'>", self.paytype)

    get_short_paytype.allow_tags = True
    get_short_paytype.short_description = u'Опл'

    def get_short_date(self):
        return format_html(u'{0} {1}, {2}:{3}', self.date.day, MONTH_ARR[self.date.month], self.date.hour, self.date.minute)

    get_short_date.allow_tags = True
    get_short_date.short_description = u'Д'

    def get_short_date_delivery(self):
        date_time = '-'
        if self.real_desired_time and self.desired_time:
            if self.district:
                date_time = format_html(u'{0} {1}, {2}<br>{3}', self.real_desired_time.day, MONTH_ARR[self.real_desired_time.month], self.desired_time, self.get_district_display())
            else:
                date_time = format_html(u'{0} {1}, {2}', self.real_desired_time.day, MONTH_ARR[self.real_desired_time.month], self.desired_time)
        elif self.real_desired_time:
            if self.district:
                date_time = format_html(u'{0} {1}<br>{2}', self.real_desired_time.day, MONTH_ARR[self.real_desired_time.month], self.get_district_display())
            else:
                date_time = format_html(u'{0} {1}', self.real_desired_time.day, MONTH_ARR[self.real_desired_time.month])
        elif self.desired_time:
            if self.district:
                date_time = format_html(u'{0}<br>{1}', self.desired_time, self.get_district_display())
            else:
                date_time = self.desired_time
        return date_time

    get_short_date_delivery.allow_tags = True
    get_short_date_delivery.short_description = u'Доставка'

    def owner_name(self):
        name = '-'
        if self.owner:
            if self.owner_id == 138:  # from phone
                name = format_html(u"<span style='color: #a33'>По телефону</span>")
            elif self.owner_id == 577:  # from sklad
                name = format_html(u"<img src='/static/kostochka38/images/discount.png' width='16'> <span style='color: #3aa'>Со склада</span>")
            elif self.owner_id == 3229:  # anonim
                name = format_html(u"<span style='color: #a33'>Аноним</span>")
            elif self.owner.last_name:
                name = format_html(u"<span style='color: #666'>{0} {1}<br> {2}</span>", self.owner.first_name, self.owner.last_name, self.owner.username)
            else:
                name = format_html(u"<span style='color: #666'>{0}<br> {1}</span>", self.owner.first_name, self.owner.username)
        return name

    owner_name.allow_tags = True
    owner_name.short_description = u'Клиент'

    def user_description(self):
        if self.owner.description:
            return '%s %s' % (format_html(u'<br>'), self.owner.description)
        else:
            return u'-'

    user_description.allow_tags = True
    user_description.short_description = u'О клиенте'

    def link(self):
        return format_html("<a target='_blank' href='/DgJrfdJg/catalog/zakaz/{0}/'>{1}&rarr;</a>", self.id, self.id)

    link.allow_tags = True
    link.short_description = u'Линк'

    def get_order_count(self):
        order_count = Zakaz.objects.filter(owner=self.owner, status__in=[5, 6], date__lt=self.date).count() + 1
        font_size = 80
        font_color = '#999'
        font_weight = 'normal'
        if order_count == 1 or order_count % 3 == 0:
            font_size = 130
            font_weight = 'bold'
            font_color = '#333'
        return format_html(
            "<span style='padding: 5px; border: 1px solid #f5f5f5; border-radius: 5px; background: #fff; display: block; text-align: center; font-size: {0}%; font-weight: {1}; color: {2}; '>{3}</span>",
            font_size, font_weight, font_color, order_count)

    get_order_count.allow_tags = True
    get_order_count.short_description = u'S'

    def get_order_count_inner(self):
        order_count = Zakaz.objects.filter(owner=self.owner, status__in=[5, 6], date__lt=self.date).count() + 1
        font_size = 80
        font_color = '#999'
        font_weight = 'normal'
        if order_count == 1 or order_count % 3 == 0:
            font_size = 130
            font_weight = 'bold'
            font_color = '#333'
        return format_html("<span style='font-size: {0}%; font-weight: {1}; color: {2}; '>{3}</span>", font_size,
                           font_weight, font_color, order_count)

    get_order_count_inner.allow_tags = True
    get_order_count_inner.short_description = u'Количество заказов'

    def get_presale_count(self):
        order_count = ZakazGoods.objects.filter(zakaz_id=self.id, presale=True).count()
        order_count_color = '-'
        if order_count > 0:
            order_count_color = format_html(
                "<span style='padding: 5px; border: 1px solid #666; border-radius: 5px; background: #faa; display: block; text-align: center; font-size: 100%; font-weight: bold; color: #444; '>{0}</span>",
                order_count)
        return order_count_color

    get_presale_count.allow_tags = True
    get_presale_count.short_description = u'P'

    def get_presale_count_inner(self):
        order_count = ZakazGoods.objects.filter(zakaz_id=self.id, presale=True).count()
        if order_count > 0:
            return format_html(
                "<span style='padding: 4px 35px; border: 1px solid #f5f5f5; border-radius: 5px; background: #faa; display: inline-block; text-align: center; font-size: 130%; font-weight: bold; color: #444; '>{0}</span>",
                order_count)
        return '0'

    get_presale_count_inner.allow_tags = True
    get_presale_count_inner.short_description = u'Количество товаров по предзаказу'

    def get_full_summ(self):
        return sum([i.summ for i in self.zakazgoods_set.all()])

    def get_summ_with_sale(self):
        summ_so_skidkoi = 0
        all_goods = self.zakazgoods_set.all()
        for line in all_goods:
            goods = Item.objects.get(id=line.item_id)
            if line.sale:
                line.summ_sale = line.summ * (float(100 - line.sale) / 100)
            else:
                line.summ_sale = line.summ * self.sale_koef
            summ_so_skidkoi += line.summ_sale
        return summ_so_skidkoi

    def create_expenses(self):
        non_cash = self.non_cash * settings.BANK_COMMISSION
        if self.paytype == 0:
            new_expense_cash = Expense(
                type=1,
                type_of_currency=self.paytype,
                value=self.cash,
                description=u'заказ №{}'.format(self.id),
                expensetype_id=1,
            )
            new_expense_cash.save()
        elif self.paytype == 1:
            new_expense_cash = Expense(
                type=1,
                type_of_currency=self.paytype,
                value=non_cash,
                description=u'заказ №{}'.format(self.id),
                expensetype_id=1,
            )
            new_expense_cash.save()
        elif self.paytype == 6:
            new_expense_cash = Expense(
                type=1,
                type_of_currency=0,
                value=self.cash,
                description=u'заказ №{}'.format(self.id),
                expensetype_id=1,
            )
            new_expense_cash.save()
            new_expense_non_cash = Expense(
                type=1,
                type_of_currency=1,
                value=non_cash,
                description=u'заказ №{}'.format(self.id),
                expensetype_id=1,
            )
            new_expense_non_cash.save()

    def k_oplate(self, without_velrokm=False, only_velrokm=False):
        summ_so_skidkoi = 0
        lines = ZakazGoods.objects.filter(zakaz=self.id).values()
        for j in lines:
            if without_velrokm:
                item = Item.objects.get(id=j['item_id'])
                if item.deckitem.segment_new.id == 16:
                    continue
            if only_velrokm:
                item = Item.objects.get(id=j['item_id'])
                if not item.deckitem.segment_new.id == 16:
                    continue
            if int(j['quantity']) == 0:
                continue
            j['price'] = j['summ'] / j['quantity']
            if j['sale'] or j['sale'] == 0:
                j['price_sale'] = round(j['price'] * (float(100 - j['sale']) / 100), 2)
                j['summ_sale'] = round(j['price_sale'] * j['quantity'], 2)
            else:
                j['price_sale'] = round(j['price'] * self.sale_koef, 2)
                j['summ_sale'] = round(j['price_sale'] * j['quantity'], 2)
            summ_so_skidkoi += j['summ_sale']

        # +/- доставка/скидка
        if self.dostavka:
            summ_so_skidkoi += self.dostavka

        # "скидка на мелочь" не считается для онлайн оплат
        if self.paytype != 4:
            return int(summ_so_skidkoi)
        return round(summ_so_skidkoi, 2)

    k_oplate.short_description = u'К оплате'

    def getpdflink(self):
        return format_html('<a href="/manage/{0}/pdf/"> PDF &rarr; </a>', str(self.id))

    getpdflink.allow_tags = True
    getpdflink.short_description = u'PDF'

    def get_f_status(self):
        if self.f_state == 1:
            return '<div style="background: #fff; padding: 5px; color: #000; text-align: center; border-radius: 50px;">N</div>'
        elif self.f_state == 2:
            return '<div style="background: #af9; padding: 5px; color: #000; text-align: center; border-radius: 50px;">O</div>'
        elif self.f_state == 3:
            return '<div style="background: #f66; padding: 5px; color: #fff; text-align: center; border-radius: 50px;">E</div>'
        else:
            return '-'

    get_f_status.allow_tags = True
    get_f_status.short_description = u'ФС'

    def getpdflinkinside(self):
        return format_html('<a href="/manage/{0}/pdf_inside/">PDF_inside &rarr;</a>', str(self.id))

    getpdflinkinside.allow_tags = True
    getpdflinkinside.short_description = u'PDF_inside'

    class Meta:
        verbose_name = u"Заказ клиента"
        verbose_name_plural = u"Заказы клиента"
        permissions = (
            ("courier", u"Курьер заказа"),
        )

    def save(self, *args, **kwargs):

        if self.paytype in [1, 4, 5]:
            self.cash = 0
            self.non_cash = self.k_oplate()
        elif self.paytype in [0, 3]:
            self.non_cash = 0
            self.cash = self.k_oplate()

        if not self.date_end and self.status == 6:  # завершенный заказ
            if Zakaz.objects.filter(owner=self.owner.id, status=6):
                all_summ = Zakaz.objects.filter(owner=self.owner.id, status=6).aggregate(summ=Sum('summ')).get('summ', 0)
                if not all_summ:
                    all_summ = 0
                all_summ += self.summ
            else:
                all_summ = self.summ

            self.owner.customer = True
            if Zakaz.objects.filter(owner=self.owner.id, status=6).count() > 0:
                self.owner.repeat_customer = True

            if not self.owner.ur_lico and not self.owner.is_staff and not self.owner.id in [3229, 138, 577, 4515]:
                if all_summ > 5000 and not self.owner.free_buyer and not self.owner.sale:
                    self.owner.sale = 0.99
                if all_summ > 10000 and not self.owner.free_buyer and not self.owner.sale < 0.98:
                    self.owner.sale = 0.98
                if all_summ > 15000 and not self.owner.free_buyer and not self.owner.sale < 0.97:
                    self.owner.sale = 0.97
                if all_summ > 30000 and not self.owner.free_buyer and not self.owner.sale < 0.96:
                    self.owner.sale = 0.96
                if all_summ > 50000 and not self.owner.free_buyer and not self.owner.sale < 0.95:
                    self.owner.sale = 0.95

            self.owner.order_sum = all_summ
            self.owner.save()

            self.date_end = datetime.datetime.now()
            items_in_order = ZakazGoods.objects.filter(zakaz=self.id).select_related('item').values_list(
                'item_id',
                flat=True
            )
            Item.objects.filter(id__in=items_in_order).update(last_order_date=datetime.datetime.now())

            self.real_sum = self.k_oplate()

            buy_reserve_items__update_item_rate(self.id)  # уменьшим количество товара в резерве, обновим рейтинг покупок товара

        if self.id and not self.is_refund:
            old_order = Zakaz.objects.get(id=self.id)

            # добавить расход за доставку
            if not old_order.paid_courier and self.paid_courier and not self.courier_id == 1 and not self.courier == 2:
                pass

            # выслать информера на почту клиенту об изменении статуса
            if old_order.status != self.status and self.warehouse.id == 1:
                # 0 - Новый
                status_1 = [11, 1, 8, 81, 82]  # Обрабатывается
                status_2 = [2, 3, 31]  # Доставка согласована
                # 4 - Курьер выехал
                status_4 = [5, 6]  # Заказ доставлен
                status_5 = [7, 10]  # Отменен
                if self.status == 82 and not self.paid_client and self.owner.email:
                    htmlmail_order_change_status_data = {
                        'zakaz': self,
                        'status_text': ORDER_STATUS_CLIENT_DICT[self.status]
                    }
                    htmlmail_sender(MAIL_ORDER_NEED_PAY, htmlmail_order_change_status_data,
                                    self.owner.email, self.owner)  # высылаем информера клиенту

                elif (old_order.status == 0) or \
                        (old_order.status == 4) or \
                        (old_order.status in status_1 and not self.status in status_1) or \
                        (old_order.status in status_2 and not self.status in status_2) or \
                        (old_order.status in status_4 and not self.status in status_4) or \
                        (old_order.status in status_5 and not self.status in status_5):
                    if self.owner.email:
                        htmlmail_order_change_status_data = {
                            'zakaz': self,
                            'status_text': ORDER_STATUS_CLIENT_DICT[self.status]
                        }
                        htmlmail_sender(MAIL_ORDER_CHANGE_STATUS, htmlmail_order_change_status_data,
                                        self.owner.email, self.owner)  # высылаем информера клиенту

        # при возврате делаем сумму положительной
        k_oplate = abs(self.k_oplate()) if self.is_refund else self.k_oplate()

        # фискализация
        if (((((self.status == 5 and not self.owner.id == 1) 
                    or (self.status == 11 and self.paytype == 4 and self.paid_client)) 
                and not self.f_state and self.warehouse.type == 1)  # продажа/обработка
                or (self.status == 10 and self.f_state)  # мгновенный возврат
                or (
                    self.status == 6 
                    and not self.owner.id == 1 
                    and not self.f_state 
                    and self.warehouse.type == 0))  # доставка/самовывоз
            and self.f_check 
            and not self.owner.ur_lico 
            and k_oplate > 0):

            client = Client(settings.F_SHOP_ID, settings.F_SECRET_KEY)

            tax_system = TaxSystem.PATENT

            # if (self.owner.id in [3229, 138, 577] and self.dostavkatype == 0) or (self.owner.id in [3229, 138, 577] and self.pickup_warehouse.id == 1):
            #     # (если с телефона, аноним, или со скдала и доставка!) или (если с телефона, анони или со склада и выдача со склада!) ТО УСН
            #     tax_system = TaxSystem.SIMPLIFIED_IN
            #
            # if (Zakaz.objects.filter(owner_id=self.owner_id).count() == 1 and self.dostavkatype == 0 and self.warehouse_id == 1):
            #     # (если первый заказ и доставка!) ТО УСН
            #     tax_system = TaxSystem.SIMPLIFIED_IN
            # if (Zakaz.objects.filter(owner_id=self.owner_id).count() == 1 and self.pickup_warehouse):
            #     if self.pickup_warehouse.id == 1:
            #         # или (если первый заказ и выдача со склада!) ТО УСН
            #         tax_system = TaxSystem.SIMPLIFIED_IN

            intent = Intent.RETURN if self.is_refund or self.status == 10 else Intent.SELL  # Направление платежа
            # Используйте Intent.RETURN для оформления возврата
            vat_rate = VatRate.RATE_NO

            method = PaymentMethod.CARD
            if self.paytype == 1:
                method = PaymentMethod.CARD
            elif self.paytype == 0:
                method = PaymentMethod.CASH
            elif self.paytype == 3:
                method = PaymentMethod.CASH
            elif self.paytype == 4:
                method = PaymentMethod.CARD
                tax_system = TaxSystem.SIMPLIFIED_IN

            if self.warehouse.id == 1:
                if self.owner.email:
                    email = self.owner.email
                else:
                    email = 'pochta@kostochka38.ru'
            else:
                email = 'pochta@kostochka38.ru'

            check = Check(self.id, email, intent, tax_system)

            positions = ZakazGoods.objects.filter(zakaz=self.id).order_by('summ')

            counter = 1
            sum = 0
            str_to_log = ''
            for i in positions:
                quantity = abs(i.quantity)
                # Добавление позиции
                if counter == positions.count():
                    total = k_oplate - sum
                    price = round(float(total) / quantity, 2)
                    total = price * quantity
                else:
                    if i.sale:
                        price = round(i.item.current_price() * (float(100 - i.sale) / 100), 2)
                        total = price * quantity
                    else:
                        price = round(i.item.current_price() * self.sale_koef, 2)
                        total = price * quantity

                # discount = (i.item.current_price() * i.quantity) - total
                title = u'%s, %s, %s \n' % (i.item.deckitem.producer.title, i.item.deckitem.title, i.item.weight)
                str_to_log += u'%s - %s - %s = %s; \n' % (title, price, int(i.quantity), round(total, 2))
                check.add_position(
                    title,
                    oid=i.item_id,  # Идентификатор позиции в магазине
                    price=price,  # Цена за единицу
                    quantity=quantity,
                    total=round(total, 2),  # Общая стоимость позиции (по умолчанию price * quantity)
                    vat=vat_rate,  # По умолчанию Без НДС (VatRate.RATE_NO),
                )

                sum += total
                counter += 1

            str_to_log += u'== %s (%s/%s)' % (sum, self.cash, self.non_cash)
            self.f_fiscal_data = str_to_log

            # Добавление суммы расчёта
            if self.paytype == 6:
                method = PaymentMethod.CASH
                check.add_payment(self.cash, method)
                method = PaymentMethod.CARD
                check.add_payment(self.non_cash, method)
            else:
                check.add_payment(sum, method)

            if self.f_print:
                check.set_print(True)

            # Если нужно задать данные по кассиру, по умолчанию возьмутся с ФН
            # check.add_cashier('Иваров И.П.', '1234567890123')
            if self.cashier and self.cashier.is_employed:
                check.add_cashier(self.cashier.name_cashier, self.cashier.inn_cashier)

            self.f_taxtype = tax_system

            # Отправка запроса
            try:
                if not settings.DEBUG:
                    task = client.create_task(check, 9756)
            except HTTPError as exc:
                self.f_state = 3
                self.f_response = exc.response.text
            except Exception as exc:
                self.f_state = 3
                self.f_response = exc
            else:
                self.f_state = 1
                self.f_response = check
                # Task(id=1, external_id=2, print_queue_id=3, state='new')
                # id - идентификатор задачи
                # external_id - идентификатор операции в магазине
                # print_queue_id - идентификатор очереди
                # state - состояние задачи
        super(Zakaz, self).save(*args, **kwargs)


class ZakazGoods(models.Model):
    action = models.ForeignKey(New, verbose_name='Акция', null=True, blank=True, on_delete=models.SET_NULL)
    zakaz = models.ForeignKey(Zakaz, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    sale = models.IntegerField(verbose_name=u'скидка %', blank=True, null=True)
    summ = models.FloatField(blank=True, null=True)
    cost = models.FloatField(null=True, blank=True)
    from_rezervation = models.BooleanField(default=True, verbose_name=u'Из резерва?')
    presale = models.BooleanField(verbose_name=u'Предзаказ', default=False)
    basket_of_good = models.BooleanField(verbose_name=u'Корзина добра', default=False)
    is_shipped = models.BooleanField(verbose_name=u'Отгружен', default=False)

    def __str__(self):
        return str(self.zakaz)

    def get_sale_price(self):
        price = self.summ / self.quantity
        if self.sale:
            return price - price / 100 * self.sale
        else:
            return price

    def get_sale_price_dot(self):
        price = self.summ / self.quantity
        if self.sale:
            return str(price - price / 100 * self.sale).replace(',', '.')
        else:
            return str(price).replace(',', '.')

    def get_thumbnail(self):
        return self.item.get_photo_thumbnail()

    get_thumbnail.allow_tags = True
    get_thumbnail.short_description = u'Фото'

    def get_cover(self):
        return self.item.deckitem.cover()

    def get_summ(self):
        if self.sale:
            return self.summ - self.summ / 100 * self.sale
        return self.summ

    def get_round_summ(self):
        return self.summ

    def get_round_sale_summ(self):
        return int(self.get_summ())

    get_cover.allow_tags = True
    get_cover.short_description = u'Обложка'

    def get_segment(self):
        return self.item.deckitem.segment_new

    get_segment.short_description = u'Пост.'

    def get_item_id(self):
        if self.item:
            return self.item.id
        else:
            return u'-'

    get_item_id.short_description = u'item id'

    class Meta:
        verbose_name = u"Товар в заказе"
        verbose_name_plural = u"Товар в заказе"
        ordering = ['item__deckitem__producer', 'id']

    def get_presale(self):
        if self.presale:
            return "<span style='padding: 10px 20px; border: 1px solid #f5f5f5; border-radius: 5px; background: #f88; display: inline-block; text-align: center; font-size: 150%; font-weight: bold; color: #444; '>!</span>"
        return ''

    get_presale.allow_tags = True
    get_presale.short_description = u'P'

    def check_total(self):
        total = int(self.item.quantity_in_reserve) + int(self.check_insideorder_sum()) - int(self.quantity) - int(
            self.item__vreserve_count())
        return total

    check_total.allow_tags = True
    check_total.short_description = u'='

    """
    +1 (0, u'Новый'),
    +1 (11, u'Обрабатывается'),
    +1 (1, u'Не удалось дозвониться'),
    +1 (8, u'Требуется перезвонить'),

    +1 (81, u'Ждем звонка от клиента'),
    (82, u'Ждем оплаты'),

    +1 (2, u'Доставка согласована'),
    +1 (3, u'Заказ собран'),

    +1 (31, u'Заказ у курьера'),

    +1 (4, u'Курьер выехал'),
    +1 (5, u'Заказ доставлен'),
    +2 (6, u'Завершен'),

    (7, u'Отказ от заказа'),
    (10, u'Отменен'),
    """

    def check_total_for_auto_inside_order(self):
        total = 0

        """
        item.quantity_in_reserve = на складе
        check_insideorder_sum() = уже заказано у поставщика
        quantity = кол-во в заказе
        item__vreserve_count() = в резерве, другими заказами
        (на складе + в магазине) + (уже заказано у поставщика) - (кол-во в заказе) - (в резерве, другими заказами)
        """
        # если заказ новый, или в обработке или согласованный
        item_quantity_in_reserve = 0
        if LeftItem.objects.filter(item=self.item, warehouse__id=1).count() == 1:
            item_quantity_in_reserve += LeftItem.objects.filter(item=self.item, warehouse__id=1).first().left
        if LeftItem.objects.filter(item=self.item, warehouse__id=2).count() == 1:
            item_quantity_in_reserve += LeftItem.objects.filter(item=self.item, warehouse__id=2).first().left
        if self.zakaz.status in [0, 11, 1, 8, 81, 82, 2, 3, 31, 4, 5]:
            # (на складе) + (уже заказано у поставщика) - (кол-во в заказе) - (в резерве, другими заказами)
            total = int(item_quantity_in_reserve) + int(self.check_insideorder_sum_forautoinsideorder()) - int(
                self.quantity) - int(self.item__vreserve_count_for_autoinsideorder_by_warehouse(1))

        # если заказ уже доставили

        elif self.zakaz.status in [6]:
            # (на складе) + (уже заказано у поставщика) - (в резерве, другими заказами)
            total = int(item_quantity_in_reserve) + int(self.check_insideorder_sum_forautoinsideorder()) - int(
                self.item__vreserve_count_for_autoinsideorder_by_warehouse(1))
        return total

    def check_insideorder_sum(self):
        sum = 0
        if InsideZakazGoods.objects.filter(item=self.item_id, zakaz__status__in=[0, 2, 4]).exists():
            sum = InsideZakazGoods.objects.filter(item=self.item_id, zakaz__status__in=[0, 2, 4]).aggregate(
                sum=Sum('quantity'))['sum']
        return sum

    check_insideorder_sum.allow_tags = True
    check_insideorder_sum.short_description = u'ПЗП'

    def check_insideorder_sum_forautoinsideorder(self):
        sum = 0
        if InsideZakazGoods.objects.filter(item=self.item_id, zakaz__status__in=[0, 2, 4], quantity__gte=0).exists():
            sum = InsideZakazGoods.objects.filter(item=self.item_id, zakaz__status__in=[0, 2, 4], quantity__gte=0).aggregate(sum=Sum('quantity'))['sum']
        return sum

    def check_insideorder(self):
        inside_order = False
        if InsideZakazGoods.objects.filter(item=self.item_id, zakaz__status__in=[0, 2, 4]).exists():
            inside_order_goods = InsideZakazGoods.objects.filter(item=self.item_id, zakaz__status__in=[0, 2, 4])[0:1].select_related('zakaz')
            inside_order = inside_order_goods[0].zakaz
        return inside_order

    check_insideorder.allow_tags = True
    check_insideorder.short_description = u'ПЗП'

    def item__vreserve(self):
        count = 0
        color = 'green'
        orders = format_html('')
        if ZakazGoods.objects.filter(item=self.item.id, zakaz__status__in=[2, 3, 31, 4, 5]).exclude(id=self.id).aggregate(
                sum=Sum('quantity'))['sum']:
            count = \
                ZakazGoods.objects.filter(item=self.item.id, zakaz__status__in=[2, 3, 31, 4, 5]).exclude(
                    id=self.id).aggregate(
                    sum=Sum('quantity'))['sum']
            for i in ZakazGoods.objects.filter(item=self.item.id, zakaz__status__in=[2, 3, 31, 4, 5]).exclude(
                    id=self.id).values():
                orders += format_html('<br><a target="_blank" href="/DgJrfdJg/catalog/zakaz/{0}/">{1}&rarr;</a>',
                                      i['zakaz_id'], i['zakaz_id'])
            color = 'red'
        return format_html("<span style='color: {0}'>{1}</span>{2}", color, count, orders)

    item__vreserve.allow_tags = True
    item__vreserve.short_description = u'В резерве'

    def item__vreserve_order(self):
        orders = format_html('')
        if ZakazGoods.objects.filter(item=self.item.id, zakaz__status__in=[2, 3, 31, 4, 5]).exclude(id=self.id).aggregate(
                sum=Sum('quantity'))['sum']:
            for i in ZakazGoods.objects.filter(item=self.item.id, zakaz__status__in=[2, 3, 31, 4, 5]).exclude(
                    id=self.id).values():
                orders += format_html("<a target='_blank' href='/DgJrfdJg/catalog/zakaz/{0}/'>{1}&rarr;</a><br>",
                                      i['zakaz_id'], i['zakaz_id'])
        return format_html("{0}", orders)

    item__vreserve_order.allow_tags = True
    item__vreserve_order.short_description = u'В резерве заказы'

    def item__vreserve_plain(self):
        count = 0
        color = 'green'
        if ZakazGoods.objects.filter(item=self.item.id, zakaz__status__in=[2, 3, 31, 4, 5]).exclude(id=self.id).aggregate(
                sum=Sum('quantity'))['sum']:
            count = \
                ZakazGoods.objects.filter(item=self.item.id, zakaz__status__in=[2, 3, 31, 4, 5]).exclude(
                    id=self.id).aggregate(
                    sum=Sum('quantity'))['sum']
            color = 'red'
        return format_html("<span style='color: {0}'>{1}</span>", color, count)

    item__vreserve_plain.allow_tags = True
    item__vreserve_plain.short_description = u'В резерве кол-во'

    def item__vreserve_count(self):
        count = 0
        if ZakazGoods.objects.filter(item=self.item.id, zakaz__status__in=[2, 3, 31, 4, 5]).exclude(id=self.id).aggregate(
                sum=Sum('quantity'))['sum']:
            count = \
                ZakazGoods.objects.filter(item=self.item.id, zakaz__status__in=[2, 3, 31, 4, 5]).exclude(
                    id=self.id).aggregate(
                    sum=Sum('quantity'))['sum']
        return count

    def item__vreserve_count_for_autoinsideorder(self):
        count = 0
        if ZakazGoods.objects.filter(item=self.item.id, zakaz__status__in=[2, 3, 31, 4, 5]).exclude(id=self.id).exclude(
                zakaz__owner__id=577).aggregate(
            sum=Sum('quantity'))['sum']:
            count = \
                ZakazGoods.objects.filter(item=self.item.id, zakaz__status__in=[2, 3, 31, 4, 5]).exclude(
                    id=self.id).exclude(zakaz__owner__id=577).aggregate(
                    sum=Sum('quantity'))['sum']
        return count

    item__vreserve_count.allow_tags = False
    item__vreserve_count.short_description = u'В резерве цифра'

    def item__vreserve_count_for_autoinsideorder_by_warehouse(self, warehouse_id):
        count = 0
        if ZakazGoods.objects.filter(item=self.item.id, zakaz__status__in=[2, 3, 31, 4, 5], zakaz__warehouse__id=warehouse_id).exclude(id=self.id).exclude(
                zakaz__owner__id=577).aggregate(
            sum=Sum('quantity'))['sum']:
            count = \
                ZakazGoods.objects.filter(item=self.item.id, zakaz__status__in=[2, 3, 31, 4, 5], zakaz__warehouse__id=warehouse_id).exclude(
                    id=self.id).exclude(zakaz__owner__id=577).aggregate(
                    sum=Sum('quantity'))['sum']
        return count

    def link(self):
        return format_html("<a target='_blank' href='/DgJrfdJg/catalog/item/{0}/'>{1}&rarr;</a>", self.item.id,
                           self.item.id)

    link.allow_tags = True
    link.short_description = u'Линк'

    def item__quantity_in_reserve(self):
        quantity_in_reserve_str = format_html(u'== {0}', self.item.quantity_in_reserve)
        warehoeses = WareHouse.objects.all()
        for i in warehoeses:
            left = 0
            if LeftItem.objects.filter(warehouse=i, item=self.item).count() == 1:
                left = LeftItem.objects.get(warehouse=i, item=self.item).left
            warehouse_str = u'%s %s ' % (i.name[0:2], left)
            quantity_in_reserve_str += format_html(u'<br>{0} ', warehouse_str)
        return format_html(u"{0}", quantity_in_reserve_str)

    item__quantity_in_reserve.allow_tags = True
    item__quantity_in_reserve.short_description = u'Остаток'

    def item__quantity_in_stock(self):
        return str(self.item.quantity_in_stock)

    item__quantity_in_stock.allow_tags = True
    item__quantity_in_stock.short_description = u'У поставщика'

    def item__code(self):
        if self.item.deckitem.segment_new.id == 2:
            return self.item.code
        else:
            return self.item.article

    item__code.short_description = u'Код'

    def buy_count_3_month(self):
        return self.item.buy_count_3_month()

    buy_count_3_month.allow_tags = True
    buy_count_3_month.short_description = u'Куплено за 3 месяца'

    def buy_count_3_month_round(self):
        stop_date = datetime.datetime.now()
        start_date = stop_date - datetime.timedelta(days=90)
        counts = ZakazGoods.objects.filter(zakaz__date__gte=start_date, zakaz__date__lt=stop_date, item=self.item,
                                           zakaz__status=6).exclude(sale__gte=25, zakaz__owner__id=577).aggregate(sum=Sum('quantity'))['sum']
        if counts is None:
            counts = 0
        else:
            counts = round(float(counts) / 3)
        return int(counts)

    def buy_count_3_month_int(self):
        stop_date = datetime.datetime.now()
        start_date = stop_date - datetime.timedelta(days=90)
        counts = ZakazGoods.objects.filter(zakaz__date__gte=start_date, zakaz__date__lt=stop_date, item=self.item,
                                           zakaz__status=6).exclude(sale__gte=25, zakaz__owner__id=577).aggregate(sum=Sum('quantity'))['sum']
        if counts is None:
            counts = 0
        else:
            counts = int(float(counts) / 3)
        return int(counts)

    def buy_count_3_month_for_auto_suplier_order(self):
        stop_date = datetime.datetime.now()
        start_date = stop_date - datetime.timedelta(days=90)
        counts = ZakazGoods.objects.filter(zakaz__warehouse__id=1, zakaz__date__gte=start_date, zakaz__date__lt=stop_date, item=self.item,
                                           zakaz__status=6).exclude(sale__gte=25, zakaz__owner__id=577).aggregate(
            sum=Sum('quantity'))['sum']
        counts_order = ZakazGoods.objects.filter(zakaz__warehouse__id=1, zakaz__date__gte=start_date, zakaz__date__lt=stop_date, item=self.item,
                                                 zakaz__status=6).exclude(sale__gte=25, zakaz__owner__id=577).count()

        if counts_order > 2:
            if counts is None:
                counts = 0
            else:
                counts = int(float(counts) / 3)
            return int(counts)
        else:
            return 0

    def buy_count_3_month_for_auto_suplier_order_round(self):
        stop_date = datetime.datetime.now()
        start_date = stop_date - datetime.timedelta(days=90)
        counts = ZakazGoods.objects.filter(zakaz__warehouse__id=1, zakaz__date__gte=start_date, zakaz__date__lt=stop_date, item=self.item,
                                           zakaz__status=6).exclude(sale__gte=25, zakaz__owner__id=577).aggregate(
            sum=Sum('quantity'))['sum']
        counts_order = ZakazGoods.objects.filter(zakaz__warehouse__id=1, zakaz__date__gte=start_date, zakaz__date__lt=stop_date, item=self.item,
                                                 zakaz__status=6).exclude(sale__gte=25, zakaz__owner__id=577).count()

        if counts_order > 2:
            if counts is None:
                counts = 0
            else:
                counts = int(round(float(counts) / 3))
            return int(round(counts))
        else:
            return 0

    def save(self):
        if self.zakaz.owner.optovik:
            self.summ = round(int(self.quantity) * self.item.current_price_opt(), 2)
        elif self.zakaz.owner.zavodchik:
            self.summ = round(int(self.quantity) * self.item.current_price_zavodchik(), 2)
        else:
            self.summ = int(self.quantity) * int(self.item.current_price())

        """
        поиск  последней цены закупки
        """
        if InsideZakazGoods.objects.filter(item=self.item, quantity__gt=0).order_by('-id').exists():
            inside_zakaz_good = InsideZakazGoods.objects.filter(item=self.item, quantity__gt=0).order_by('-id').first()
            real_item_price = inside_zakaz_good.cost / inside_zakaz_good.quantity
        else:
            real_item_price = self.item.real_price

        self.cost = float(self.quantity * real_item_price)
        super(ZakazGoods, self).save()

        data = ZakazGoods.objects.filter(zakaz=self.zakaz.id).values()
        summ_k_oplate = 0
        summ_cost = 0
        for j in data:
            summ_k_oplate += j['summ']
            summ_cost += j['cost']
        self.zakaz.summ = summ_k_oplate
        self.zakaz.cost = summ_cost
        self.zakaz.revenue = summ_k_oplate - summ_cost
        self.zakaz.save()

    def delete(self):
        super(ZakazGoods, self).delete()

        data = ZakazGoods.objects.filter(zakaz=self.zakaz.id).values()
        summ_k_oplate = 0
        summ_cost = 0
        for j in data:
            summ_k_oplate += j['summ']
            if not j['from_rezervation']:
                summ_cost += j['cost']
        self.zakaz.summ = summ_k_oplate
        self.zakaz.cost = summ_cost
        self.zakaz.revenue = (self.zakaz.summ * self.zakaz.sale_koef) - summ_cost
        self.zakaz.save()


class ZakazGoodsBaskedOfGoodsProxy(ZakazGoods):
    class Meta:
        proxy = True
        verbose_name = u'товар из корзины добра'
        verbose_name_plural = u'Товары из корзины добра'


class AutoZakaz(models.Model):
    owner = models.ForeignKey(Account, verbose_name=u'Пользователь', on_delete=models.CASCADE)

    create_date = models.DateTimeField(verbose_name=u'Дата создания', auto_now_add=True)
    repeat_period = models.PositiveIntegerField(verbose_name=u'Период повтора', help_text=u'в днях', default=30)

    last_order = models.DateTimeField(verbose_name=u'Дата последнего автоповтора', blank=True, null=True)

    extra = models.TextField(blank=True, null=True, verbose_name=u'Комментарий менеджера магазина')
    zakaz = models.ForeignKey(Zakaz, verbose_name=u'Родительский заказ', blank=True, null=True, on_delete=models.CASCADE)

    repear_count = models.PositiveIntegerField(default=0, verbose_name=u'Количество повторов')

    active = models.BooleanField(verbose_name=u'Активный', default=True)

    def __str__(self):
        return str(self.id)

    def owner_name(self):
        if self.owner:
            if self.owner.last_name:
                return format_html(u'{0} {1}<br> ({2})', self.owner.first_name, self.owner.last_name,
                                   self.owner.username)
            else:
                return format_html(u'{0}<br> ({1})', self.owner.first_name, self.owner.username)
        else:
            return ' - '

    owner_name.allow_tags = True
    owner_name.short_description = u'Клиент'

    def link(self):
        return format_html("<a target='_blank' href='/DgJrfdJg/catalog/autozakaz/{0}/'>{1}&rarr;</a>", self.id, self.id)

    link.allow_tags = True
    link.short_description = u'Линк'

    class Meta:
        verbose_name = u"Автозаказ"
        verbose_name_plural = u"Автозаказы"


class AutoZakazGoods(models.Model):
    zakaz = models.ForeignKey(AutoZakaz, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.IntegerField()

    def __str__(self):
        return str(self.zakaz)

    def get_thumbnail(self):
        return self.item.get_photo_thumbnail()

    get_thumbnail.allow_tags = True
    get_thumbnail.short_description = u'Фото'

    def item__vreserve(self):
        count = 0
        color = 'green'
        if ZakazGoods.objects.filter(item=self.item.id, zakaz__status__in=[2, 3, 4, 5]).exclude(id=self.id).aggregate(
                sum=Sum('quantity'))['sum']:
            count = \
                ZakazGoods.objects.filter(item=self.item.id, zakaz__status__in=[2, 3, 4, 5]).exclude(
                    id=self.id).aggregate(
                    sum=Sum('quantity'))['sum']
            color = 'red'
        return format_html("<span style='color: {0}'>{1}</span>", color, count)

    item__vreserve.allow_tags = True
    item__vreserve.short_description = u'В резерве'

    def link(self):
        return format_html("<a target='_blank' href='/DgJrfdJg/catalog/item/{0}/'>{1}&rarr;</a>", self.item.id,
                           self.item.id)

    link.allow_tags = True
    link.short_description = u'Линк'

    def item__quantity_in_reserve(self):
        quantity_in_reserve_str = format_html(u'== {0}', self.item.quantity_in_reserve)
        warehoeses = WareHouse.objects.all()
        for i in warehoeses:
            left = 0
            if LeftItem.objects.filter(warehouse=i, item=self.item).count() == 1:
                left = LeftItem.objects.get(warehouse=i, item=self.item).left
            warehouse_str = u'%s %s ' % (i.name[0:2], left)
            quantity_in_reserve_str += format_html(u'<br>{0} ', warehouse_str)
        return format_html(u"{0}", quantity_in_reserve_str)

    item__quantity_in_reserve.allow_tags = True
    item__quantity_in_reserve.short_description = u'Остаток'

    def item__quantity_in_stock(self):
        return str(self.item.quantity_in_stock)

    item__quantity_in_stock.allow_tags = True
    item__quantity_in_stock.short_description = u'У поставщика'

    def item__code(self):
        if self.item.deckitem.segment_new.id == 2:
            return self.item.code
        else:
            return self.item.article

    item__code.short_description = u'Код'

    class Meta:
        verbose_name = u"Товар в автозаказе"
        verbose_name_plural = u"Товары в автозаказе"
        ordering = ['item__deckitem__producer', 'id']


class InsideZakaz(models.Model):
    cost = models.FloatField(verbose_name=u'Стоимость', null=True, blank=True)
    date = models.DateTimeField(verbose_name=u'Дата', auto_now_add=True)
    date_end = models.DateTimeField(verbose_name=u'Дата завершения', null=True, blank=True)
    date_pickup = models.DateField(verbose_name=u'Дата самовывоза', null=True, blank=True)
    status = models.IntegerField(choices=INSIDE_ORDER_STATUS, default=0, verbose_name=u'Статус')
    paid_supplier = models.BooleanField(default=False, verbose_name=u'Оплачен поставщику')
    segment_new = models.ForeignKey(Segment, verbose_name=u'Поставщик', on_delete=models.CASCADE)
    pickup = models.BooleanField(default=False, verbose_name=u'Самовывоз')

    extra = models.TextField(blank=True, null=True, verbose_name=u'Комментарий менеджера магазина')

    sale_koef = models.FloatField(verbose_name=u'Скидка %', default=0)

    paid_courier = models.BooleanField(default=False, verbose_name=u'Оплачен Курьеру')
    courier = models.ForeignKey(Account, verbose_name=u'Курьер', blank=True, null=True,
                                limit_choices_to={'groups__permissions__codename': 'courier'}, on_delete=models.SET_NULL)
    manager = models.ForeignKey(Account, verbose_name=u'Менеджер', blank=True, null=True,
                                related_name='manager_insidezakaz_set',
                                limit_choices_to={'groups__permissions__codename': 'manager', 'is_active': True}, on_delete=models.SET_NULL)
    warehouse = models.ForeignKey('WareHouse', verbose_name=u'Склад', default=1, on_delete=models.SET_DEFAULT)

    details = models.TextField(u'Лог', blank=True, null=True)

    def __str__(self):
        return u'[' + str(self.id) + u'] '

    class Meta:
        verbose_name = u"Заказ поставщика"
        verbose_name_plural = u"Заказы поставщика"

    def getpdflinkinside(self):
        return format_html('<a href="/manage/{0}/inside_pdf_inside/">PDF_inside_zakaz &rarr;</a>', str(self.id))

    def get_items_to_print(self):
        return self.insidezakazgoods_set.all()

    def last_edit(self):
        if InsideZakazStatusLog.objects.filter(zakaz=self.id):
            return InsideZakazStatusLog.objects.filter(zakaz=self.id).order_by('-date')[0:1].values()[0]['date']
        else:
            return False

    getpdflinkinside.allow_tags = True
    getpdflinkinside.short_description = u'PDF_inside'

    def save(self):
        if not self.id:
            if SaleTable.objects.filter(segment_new=self.segment_new).order_by('-date').exists():
                sale_table = SaleTable.objects.filter(segment_new=self.segment_new).order_by('-date').values()[0:1]
                self.sale_koef = sale_table[0]['value']
            else:
                self.sale_koef = 0
        else:
            self.cost = float("%.2f" % self.cost)
        if not self.date_end and self.status == 6:  # завершенный заказ
            self.date_end = datetime.datetime.now()
            new_reserve_items(self.id)
            new_vendor = VendorAccount(
                type=0,
                type_of_currency=0,
                value="%.2f" % ((-1) * self.cost),
                segment_new=self.segment_new,
                description=u'заказ поставщика №' + str(self.id),
            )

            new_vendor.save()
            super(InsideZakaz, self).save()

        super(InsideZakaz, self).save()


class InsideZakazGoods(models.Model):
    action = models.ForeignKey(New, verbose_name='Акция', null=True, blank=True, on_delete=models.SET_NULL)
    zakaz = models.ForeignKey(InsideZakaz, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    sale = models.FloatField(verbose_name=u'скидка %', blank=True, null=True)
    quantity = models.IntegerField()
    cost = models.FloatField(null=True, blank=True)

    def __str__(self):
        return str(self.zakaz)

    def get_thumbnail(self):
        return self.item.get_photo_thumbnail()

    get_thumbnail.allow_tags = True
    get_thumbnail.short_description = u'Фото'

    def link(self):
        return format_html("<a target='_blank' href='/DgJrfdJg/catalog/item/{0}/'>{1} &rarr;</a>", self.item.id,
                           self.item.id)

    link.allow_tags = True
    link.short_description = u'Линк'

    class Meta:
        verbose_name = u"Товар в заказе"
        verbose_name_plural = u"Товар в заказе"
        ordering = ['item__deckitem__producer', 'id']

    def item__quantity_in_reserve(self):
        quantity_in_reserve_str = format_html(u'== {0}', self.item.quantity_in_reserve)
        warehoeses = WareHouse.objects.all()
        for i in warehoeses:
            left = 0
            if LeftItem.objects.filter(warehouse=i, item=self.item).count() == 1:
                left = LeftItem.objects.get(warehouse=i, item=self.item).left
            warehouse_str = u'%s %s ' % (i.name[0:2], left)
            quantity_in_reserve_str += format_html(u'<br>{0} ', warehouse_str)
        return format_html(u"{0}", quantity_in_reserve_str)

    item__quantity_in_reserve.allow_tags = True
    item__quantity_in_reserve.short_description = u'Остаток'

    def item__quantity_in_stock(self):
        return str(self.item.quantity_in_stock)

    item__quantity_in_stock.allow_tags = True
    item__quantity_in_stock.short_description = u'У поставщика'

    def buy_count_3_month(self):
        return self.item.buy_count_3_month()

    buy_count_3_month.allow_tags = True
    buy_count_3_month.short_description = u'Куплено за 3 месяца'

    def item__code(self):
        # if self.item.deckitem.segment == 'avrora':
        #    return self.item.code
        # else:
        #    return self.item.article
        return self.item.code

    item__code.short_description = u'Код'

    def item__vreserve(self):
        count = 0
        color = 'green'
        orders = format_html('')
        if ZakazGoods.objects.filter(item=self.item.id, zakaz__status__in=[2, 3, 4, 5]).exclude(id=self.id).aggregate(
                sum=Sum('quantity'))['sum']:
            count = \
                ZakazGoods.objects.filter(item=self.item.id, zakaz__status__in=[2, 3, 4, 5]).exclude(
                    id=self.id).aggregate(
                    sum=Sum('quantity'))['sum']
            for i in ZakazGoods.objects.filter(item=self.item.id, zakaz__status__in=[2, 3, 4, 5]).exclude(
                    id=self.id).values():
                orders += format_html('<br><a target="_blank" href="/DgJrfdJg/catalog/zakaz/{0}/">{1}&rarr;</a>',
                                      i['zakaz_id'], i['zakaz_id'])
            color = 'red'
        return format_html("<span style='color: {0}'>{1}</span>{2}", color, count, orders)

    item__vreserve.allow_tags = True
    item__vreserve.short_description = u'В резерве'

    def save(self):
        if self.sale:
            self.cost = float(self.quantity * self.item.real_price) * (1 - (self.sale / 100))
        else:
            self.cost = float(self.quantity * self.item.real_price) * (1 - (self.zakaz.sale_koef / 100))
        super(InsideZakazGoods, self).save()

        data = InsideZakazGoods.objects.filter(zakaz=self.zakaz.id).values()
        summ_cost = 0
        for j in data:
            summ_cost += j['cost']

        self.zakaz.cost = summ_cost
        self.zakaz.save()

    def delete(self):
        super(InsideZakazGoods, self).delete()

        data = InsideZakazGoods.objects.filter(zakaz=self.zakaz.id).values()
        summ_cost = 0
        for j in data:
            summ_cost += j['cost']

        self.zakaz.cost = summ_cost
        self.zakaz.save()


class OutsideZakaz(models.Model):
    summ = models.IntegerField(verbose_name=u'Сумма заказа')
    zakaz_id = models.CharField(max_length=32, verbose_name=u'Номер заказа')

    store = models.IntegerField(verbose_name=u'Магазин', choices=STORES)
    date = models.DateTimeField(verbose_name=u'Дата', auto_now_add=True)
    date_end = models.DateTimeField(verbose_name=u'Дата завершения', null=True, blank=True)
    status = models.IntegerField(choices=ORDER_STATUS, default=DEFAULT_ORDER_STATUS, verbose_name=u'Статус')
    paid_client = models.BooleanField(default=False, verbose_name=u'Клиент')
    paid_courier = models.BooleanField(default=False, verbose_name=u'Курьер')

    extra = models.TextField(blank=True, null=True, verbose_name=u'Комментарий менеджера магазина')
    real_desired_time = models.DateField(blank=True, null=True, verbose_name=u'Дата доставки')

    fio = models.CharField(max_length=128, blank=True, null=True, verbose_name=u'Имя')
    phone = models.CharField(max_length=32, verbose_name=u'Телефон')
    index = models.CharField(max_length=32, blank=True, null=True, verbose_name=u'Индекс')
    city = models.CharField(max_length=128, blank=True, null=True, verbose_name=u'Город')
    street = models.CharField(max_length=128, blank=True, null=True, verbose_name=u'Улица')
    dom = models.CharField(max_length=64, blank=True, null=True, verbose_name=u'Дом')
    appart = models.CharField(max_length=64, blank=True, null=True, verbose_name=u'Квартира')
    district = models.IntegerField(blank=True, null=True, choices=DISTRICT, verbose_name=u'Район')

    paytype = models.IntegerField(verbose_name=u'Способ оплаты', default=0, choices=PAY_TYPE)
    desired_time = models.CharField(max_length=128, blank=True, null=True, verbose_name=u'Время доставки')
    need_call = models.BooleanField(default=False, verbose_name=u'Позвонить?')

    dostavka = models.IntegerField(verbose_name=u'Доставка', default=0)

    courier = models.ForeignKey(Account, verbose_name=u'Курьер', blank=True, null=True,
                                related_name='courier_outsidezakaz_set',
                                limit_choices_to={'groups__permissions__codename': 'courier'}, on_delete=models.SET_NULL)

    def __str__(self):
        return str(self.id)

    def last_edit(self):
        if OutsideZakazStatusLog.objects.filter(zakaz=self.id):
            return OutsideZakazStatusLog.objects.filter(zakaz=self.id).order_by('-date')[0:1].values()[0]['date']
        else:
            return False

    def courier_name(self):
        if self.courier:
            if self.courier.last_name:
                return format_html(u'{0} {1}<br> ({2})', self.courier.first_name, self.courier.last_name,
                                   self.courier.username)
            else:
                return format_html(u'{0}<br> ({1})', self.courier.first_name, self.courier.username)
        else:
            return ' - '

    courier_name.allow_tags = True
    courier_name.short_description = u'Курьер'

    class Meta:
        verbose_name = u"Сторонние доставки"
        verbose_name_plural = u"Сторонние доставки"
        permissions = (
            ("courier", u"Курьер заказа"),
        )


class ParserLog(models.Model):
    date = models.DateTimeField(auto_now_add=True, verbose_name=u'Дата парсинга')
    filename = models.CharField(verbose_name=u'Имя файла', max_length=128)
    segment_new = models.ForeignKey(Segment, verbose_name=u'Сегмент', on_delete=models.CASCADE)

    def __str__(self):
        return str(self.date)

    class Meta:
        verbose_name = u"Лог парсинга"
        verbose_name_plural = u"Лог парсинга"
        ordering = ['-date', ]


class ReserveLog(models.Model):
    date = models.DateTimeField(auto_now_add=True, verbose_name=u'Дата движения')
    item = models.ForeignKey(Item, verbose_name=u'Товар', on_delete=models.CASCADE)
    zakaz = models.ForeignKey(Zakaz, blank=True, null=True, verbose_name=u'Заказ клиента', on_delete=models.SET_NULL)
    inside_zakaz = models.ForeignKey(InsideZakaz, blank=True, null=True, verbose_name=u'Заказ поставщика', on_delete=models.SET_NULL)
    movement = models.ForeignKey('MovementOfGoods', blank=True, null=True, verbose_name=u'Перемещение', on_delete=models.SET_NULL)
    count_move = models.IntegerField(verbose_name=u'Движение')
    residue = models.IntegerField(verbose_name=u'Остаток')

    def zakaz_link(self):
        return format_html("<a target='_blank' href='/DgJrfdJg/catalog/zakaz/{0}/change/'>{1} &rarr;</a>",
                           self.zakaz.id, self.zakaz.id)

    zakaz_link.allow_tags = True
    zakaz_link.short_description = u'Заказ клиента'

    def inside_zakaz_link(self):
        return format_html("<a target='_blank' href='/DgJrfdJg/catalog/insidezakaz/{0}/change/'>{1} &rarr;</a>",
                           self.inside_zakaz.id, self.inside_zakaz.id)

    inside_zakaz_link.allow_tags = True
    inside_zakaz_link.short_description = u'Заказ поставщика'

    def movement_link(self):
        return format_html("<a target='_blank' href='/DgJrfdJg/catalog/movementofgoods/{0}/change/'>{1} &rarr;</a>",
                           self.movement.id, self.movement.id)

    movement_link.allow_tags = True
    movement_link.short_description = u'Перемещение'

    def __str__(self):
        return str(self.date)

    class Meta:
        verbose_name = u"Лог движения товара"
        verbose_name_plural = u"Лог движения товара"
        ordering = ['-date', ]


class ZakazStatusLog(models.Model):
    zakaz = models.ForeignKey(Zakaz, verbose_name=u'Заказ', on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True, verbose_name=u'Дата')
    status = models.IntegerField(choices=ORDER_STATUS, default=DEFAULT_ORDER_STATUS, verbose_name=u'статус заказа')
    user = models.ForeignKey(Account, verbose_name=u'Кто изменил', blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return str('-')

    class Meta:
        verbose_name = u"Лог изменения статуса заказа"
        verbose_name_plural = u"Лог изменения статуса заказа"
        ordering = ['date', ]


class AutoZakazStatusLog(models.Model):
    zakaz = models.ForeignKey(Zakaz, verbose_name=u'Заказ', on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True, verbose_name=u'Дата')
    autozakaz = models.ForeignKey(AutoZakaz, verbose_name=u'Автозаказ', on_delete=models.CASCADE)

    def __str__(self):
        return str('-')

    class Meta:
        verbose_name = u"Лог генерации автозаказов"
        verbose_name_plural = u"Лог генерации автозаказов"
        ordering = ['date', ]


class InsideZakazStatusLog(models.Model):
    zakaz = models.ForeignKey(InsideZakaz, verbose_name=u'Заказ поставщика', on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True, verbose_name=u'Дата')
    status = models.IntegerField(choices=INSIDE_ORDER_STATUS, default=0, verbose_name=u'статус заказа')
    user = models.ForeignKey(Account, verbose_name=u'Кто изменил', blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return str('-')

    class Meta:
        verbose_name = u"Лог изменения статуса заказа поставщика"
        verbose_name_plural = u"Лог изменения статуса заказа поставщика"
        ordering = ['date', ]


class OutsideZakazStatusLog(models.Model):
    zakaz = models.ForeignKey(OutsideZakaz, verbose_name=u'Заказ поставщика', on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True, verbose_name=u'Дата')
    status = models.IntegerField(choices=INSIDE_ORDER_STATUS, default=0, verbose_name=u'статус заказа')
    user = models.ForeignKey(Account, verbose_name=u'Кто изменил', blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return str('-')

    class Meta:
        verbose_name = u"Лог изменения статуса стороннего заказа"
        verbose_name_plural = u"Лог изменения статуса стороннего заказа"
        ordering = ['date', ]


class ExpenseType(models.Model):
    title = models.CharField(verbose_name=u'Название статьи', max_length=256)
    type = models.IntegerField(verbose_name=u'Тип', choices=EXPENSE_TYPE, default=1)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = u"Статья расхода/дохода"
        verbose_name_plural = u"Статьи расхода/дохода"
        ordering = ['title', ]


class Expense(models.Model):
    type = models.IntegerField(verbose_name=u'Тип', choices=EXPENSE_TYPE, default=0)
    type_of_currency = models.IntegerField(verbose_name=u'Тип платежа', choices=CURRENCY_TYPE, default=0)
    value = models.FloatField(verbose_name=u'Сумма операции', default=0)
    source = models.IntegerField(verbose_name=u'Источник средств', default=0, choices=SOURCES)
    description = models.TextField(verbose_name=u'Описание', blank=True, null=True)
    date = models.DateTimeField(verbose_name=u'Дата', auto_now_add=True)
    expensetype = models.ForeignKey(ExpenseType, verbose_name=u'Статья', null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = u"Движение средств"
        verbose_name_plural = u"Движения средств"
        ordering = ['-date', ]


class VendorAccount(models.Model):
    type = models.IntegerField(verbose_name=u'Тип', choices=VENDOR_TYPE, default=1)
    type_of_currency = models.IntegerField(verbose_name=u'Тип платежа', choices=CURRENCY_TYPE, default=1)
    value = models.FloatField(verbose_name=u'Сумма операции', default=0)
    segment_new = models.ForeignKey(Segment, verbose_name=u'Поставщик', on_delete=models.CASCADE)
    description = models.TextField(verbose_name=u'Описание', blank=True, null=True)
    date = models.DateTimeField(verbose_name=u'Дата', auto_now_add=True)
    balans = models.FloatField(verbose_name=u'Баланс', default=0)

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = u"Счет у поставщика"
        verbose_name_plural = u"Счет у поставщика"
        ordering = ['-date', ]

    def save(self):
        if not self.id:
            if VendorAccount.objects.filter(segment_new=self.segment_new).order_by('-id').count() > 0:
                old_balans = VendorAccount.objects.filter(segment_new=self.segment_new).order_by('-id').values()
                balans = float("%.2f" % (old_balans[0]['balans'] + float(self.value)))
            else:
                balans = self.value
            self.balans = balans

            if self.type == 1:
                new_expense = Expense(
                    type=0,
                    type_of_currency=self.type_of_currency,
                    value="%.2f" % ((-1) * self.value),
                    description=u'%s оплата поставщику' % self.segment_new.title,
                    expensetype_id=4
                )
                new_expense.save()

        super(VendorAccount, self).save()


class ZakazBonus(models.Model):
    title = models.CharField(verbose_name=u'Название', max_length=512)
    zakaz_quantity = models.IntegerField(verbose_name=u'Количество заказов')
    repeater = models.BooleanField(verbose_name=u'Повторяющийся бонус', default=False)
    text = RichTextField(verbose_name=u'Поздравительный текст', blank=True, null=True)
    manager_text = models.TextField(verbose_name=u'Текст для менеджера заказов', blank=True, null=True)
    item = models.ForeignKey(Item, verbose_name=u'Подарок', blank=True, null=True, on_delete=models.SET_NULL)
    item_quantity = models.IntegerField(verbose_name=u'Количество подарков', blank=True, null=True)
    active = models.BooleanField(default=True, verbose_name=u'Активный')
    exp_date = models.DateField(verbose_name=u'Действует до', blank=True, null=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = u"Подарок за заказы"
        verbose_name_plural = u"Подароки за заказы"


def new_reserve_items(zakaz_id):  # при завершении заказа в статусе "в резерв" обновим остатки товара в резерве
    lines = InsideZakazGoods.objects.filter(zakaz=zakaz_id)
    for line in lines:
        item = Item.objects.get(id=line.item_id)
        left_item = item.leftitem_set.filter(warehouse=line.zakaz.warehouse).first()
        if not left_item:
            left_item = LeftItem()
            left_item.item = item
            left_item.warehouse = line.zakaz.warehouse
        left_item.left += line.quantity
        left_item.save()
        if line.quantity > 0:
            item.availability = 10
        else:
            if item.quantity_in_reserve < 1:
                item.availability = 3
                if item.deckitem.segment_new.id == 13 or item.deckitem.segment_new.id == 11:
                    item.availability = 20

                if item.quantity_in_stock < 1:
                    item.availability = 0

        new_reservelog = ReserveLog(
            item=item,
            inside_zakaz_id=zakaz_id,
            count_move=line.quantity,
            residue=item.quantity_in_reserve
        )
        new_reservelog.save()

        item.save()


def buy_reserve_items__update_item_rate(zakaz_id):
    order = Zakaz.objects.filter(id=int(zakaz_id)).first()
    lines = ZakazGoods.objects.filter(zakaz=zakaz_id).values()
    for line in lines:
        item = Item.objects.get(id=line['item_id'])
        item.number_of_purchases += 1  # увеличим количество покупок на 1
        item.count_of_purchases += line['quantity']  # увеличим количество купленного товара

        if line['from_rezervation']:
            left_item = item.leftitem_set.filter(warehouse=order.warehouse).first()
            if not left_item:
                left_item = LeftItem()
                left_item.warehouse = order.warehouse
                left_item.item = item
            left_item.left -= line['quantity']
            left_item.save()
            _sum = item.leftitem_set.all().aggregate(Sum('left'))['left__sum']
            if not _sum:
                _sum = 0
            item.quantity_in_reserve = _sum

            if item.quantity_in_reserve < 1:
                item.availability = 3
                if ItemSale.objects.filter(item_id=item.id).exists():
                    ItemSale.objects.filter(item_id=item.id).delete()
                if item.deckitem.segment_new.id == 13 or item.deckitem.segment_new.id == 11:
                    # НЕ АКТИВИРУЕМ ИНОГОРОДНИЕ ТОВАРЫ
                    item.availability = 0

                if item.quantity_in_stock < 1:
                    item.availability = 0

            if item.availability == 0 and item.quantity_in_reserve > 0:
                item.availability = 10

            new_reservelog = ReserveLog(
                item=item,
                zakaz_id=zakaz_id,
                count_move=-line['quantity'],
                residue=item.quantity_in_reserve
            )
            new_reservelog.save()

        item.save()


class SaleTable(models.Model):
    segment_new = models.ForeignKey(Segment, verbose_name=u'Поставщик', on_delete=models.CASCADE)
    value = models.FloatField(verbose_name=u'Размер скидки', default=0)
    value_for_revenue = models.FloatField(verbose_name=u'Коэффициент дохода', default=1)
    date = models.DateTimeField(verbose_name=u'Дата создания', auto_now_add=True)

    class Meta:
        verbose_name = u'Скидка поставщика'
        verbose_name_plural = u'Скидки поставщиков'


class OrderSort(models.Model):
    order_id = models.CharField(verbose_name=u'Номер заказа', max_length=128)
    order = models.PositiveIntegerField(verbose_name=u'Порядковый номер')
    date = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name = u"Сортировка заказов курьера"
        verbose_name_plural = u"Сортировка заказов курьера"


class LogingCourierFinish(models.Model):
    courier = models.ForeignKey(Account, verbose_name=u'Курьер', blank=True, null=True,
                                related_name='courier_logcourierfinish_set',
                                limit_choices_to={'groups__permissions__codename': 'courier'}, on_delete=models.SET_NULL)
    date = models.DateTimeField(verbose_name=u'Дата', auto_now_add=True)
    image = models.ImageField(verbose_name=u'Скрин', upload_to=get_file_path, blank=True, null=True)
    thumbnail_admin = ImageSpecField(source='image', processors=[ResizeToFit(150, 120), ],
                                     options={'quality': 80})
    fullimage = ImageSpecField(source='image', processors=[ResizeToFit(2520, 4080), ],
                               options={'quality': 80})

    textlog = models.TextField(verbose_name=u'Лог', )

    directory_string_var = 'screenshot_courier'

    def __str__(self):
        return str(self.id)

    def get_thumbnail(self):
        return_image = '-'
        if self.image:
            return_image = format_html('<a href="{0}" data-fancybox="gallery"><img src="{1}"></a>', self.fullimage.url, self.thumbnail_admin.url)
        return return_image

    get_thumbnail.allow_tags = True
    get_thumbnail.short_description = u'Скрин'

    def courier_name(self):
        if self.courier:
            if self.courier.last_name:
                return format_html(u'{0} {1}<br> ({2})', self.courier.first_name, self.courier.last_name,
                                   self.courier.username)
            else:
                return format_html(u'{0}<br> ({1})', self.courier.first_name, self.courier.username)
        else:
            return ' - '

    courier_name.allow_tags = True
    courier_name.short_description = u'Курьер'

    class Meta:
        verbose_name = u"Лог приемки курьера"
        verbose_name_plural = u"Лог приемки курьера"
        permissions = (
            ("courier", u"Курьер заказа"),
        )


@receiver(post_delete, sender=LogingCourierFinish)
def priceparser_delete(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete(False)


PRICE_STATUS = (
    (1, u'Новый'),
    (2, u'Выполнен'),
    (3, u'В процессе'),
    (4, u'Ошибка'),
)


class PriceParser(models.Model):
    date = models.DateTimeField(verbose_name=u'Дата загрузки', auto_now_add=True)
    segment_new = models.ForeignKey(Segment, verbose_name=u'Поставщик', on_delete=models.CASCADE)

    status = models.IntegerField(choices=PRICE_STATUS, default=1, verbose_name=u'Статус')
    price_file = models.FileField(verbose_name=u'Прайс', upload_to=get_file_path)
    extra = models.TextField(verbose_name=u'Комментарий', null=True, blank=True)

    error = models.TextField(verbose_name=u'Ошибки', null=True, blank=True)
    result_1 = models.TextField(verbose_name=u'Товар нашелся, цена изменилась', null=True, blank=True)
    result_2 = models.TextField(verbose_name=u'Новые элементы', null=True, blank=True)
    result_3 = models.TextField(verbose_name=u'Потерянный товар (есть в базе, нет в прайсе)', null=True, blank=True)
    result_4 = models.TextField(verbose_name=u'Товар нашелся, цена не изменилась (НО ТОВАР НЕ АКТИВНЫЙ)', null=True, blank=True)
    result_5 = models.TextField(verbose_name=u'Товар нашелся, цена не изменилась', null=True, blank=True)

    directory_string_var = 'price'

    def __str__(self):
        return str(self.id)

    def get_result_error(self):
        if self.id:
            return mark_safe(self.error)

    get_result_error.allow_tags = True
    get_result_error.short_description = u''

    def get_result_1(self):
        if self.id:
            return mark_safe(self.result_1)

    get_result_1.allow_tags = True
    get_result_1.short_description = u''

    def get_result_2(self):
        if self.id:
            return mark_safe(self.result_2)

    get_result_2.allow_tags = True
    get_result_2.short_description = u''

    def get_result_3(self):
        if self.id:
            return mark_safe(self.result_3)

    get_result_3.allow_tags = True
    get_result_3.short_description = u''

    def get_result_4(self):
        if self.id:
            return mark_safe(self.result_4)

    get_result_4.allow_tags = True
    get_result_4.short_description = u''

    def get_result_5(self):
        if self.id:
            return mark_safe(self.result_5)

    get_result_5.allow_tags = True
    get_result_5.short_description = u''

    class Meta:
        verbose_name = u"Прайс для парсинга"
        verbose_name_plural = u"прайсы для парсинга"


@receiver(post_delete, sender=PriceParser)
def priceparser_delete(sender, instance, **kwargs):
    if instance.price_file:
        instance.price_file.delete(False)


# class BoughtProductRecommendationProvider(RecommendationProvider):
#     def get_users(self):
#         return Account.objects.filter(is_active=True, zakaz__status=6).distinct()

#     def get_items(self):
#         return Deckitem.objects.filter(
#             item__zakazgoods__zakaz__status=6,
#             active=True,
#             item__availability__in=[3, 10],
#             item__active=True).distinct().all()

#     def get_ratings(self, obj):
#         return ZakazGoods.objects.filter(
#             item__deckitem=obj,
#             zakaz__status=6,
#             item__deckitem__active=True,
#             item__active=True,
#             item__availability__in=[3, 10]
#         ).distinct().select_related('zakaz__owner', 'item__deckitem').all()

#     def get_rating_score(self, zakazGoods):
#         return 1

#     def get_rating_user(self, zakazGoods):
#         return zakazGoods.zakaz.owner

#     def get_rating_item(self, zakazGoods):
#         return zakazGoods.item.deckitem

#     def get_rating_site(self, zakazGoods):
#         return 1


# recommendation_registry.register(ZakazGoods, [Deckitem], BoughtProductRecommendationProvider)


@receiver(pre_delete, sender=Zakaz)
def pre_delete(sender, instance, **kwargs):
    with transaction.atomic(), reversion.create_revision():
        zakaz = Zakaz.objects.get(id=instance.id)
        zakaz.revenue = 0
        zakaz.save()
        reversion.set_comment("Delete object")


@receiver(payment_success)
def my_callback(sender, **kwargs):
    with transaction.atomic(), reversion.create_revision():
        admin = Account.objects.get(id=1)
        sender.payservice.status = 11
        sender.payservice.paid_client = True
        sender.payservice.cash_go_to_kassa = True
        sender.payservice.save()
        reversion.set_user(admin)
        reversion.set_comment("Online payment success")

    new_zakazstatuslog = ZakazStatusLog(
        zakaz_id=sender.payservice.id,
        status=11,
        user=admin
    )
    new_zakazstatuslog.save()

    zakaz = Zakaz.objects.get(id=sender.payservice.id)
    summ_so_skidkoi = zakaz.k_oplate()

    summ = round(summ_so_skidkoi * settings.BANK_COMMISSION_ONLINE, 2)
    new_expense = Expense(
        type=1,
        type_of_currency=1,
        value=summ,
        description=u'заказ №%s' % sender.payservice,
        expensetype_id=1
    )
    new_expense.save()




class LeftItem(models.Model):
    class Meta:
        verbose_name = u"Остаток"
        verbose_name_plural = u"Остатки"

    item = models.ForeignKey(Item, verbose_name=u"Вес/Тип товара", on_delete=models.CASCADE)
    warehouse = models.ForeignKey(WareHouse, verbose_name=u"Склад", on_delete=models.CASCADE)
    left = models.IntegerField(default=0, verbose_name=u"Остаток")

    def __str__(self):
        return u'{}'.format(str(self.item))

    def save(self, *args, **kwargs):
        super(LeftItem, self).save(*args, **kwargs)
        self.item.quantity_in_reserve = self.item.count_left()
        self.item.save()

    def get_left_humanized(self):
        count_zakaz = self.item.zakazgoods_set.filter(zakaz__status__in=[2, 3, 4, 5, 31], zakaz__warehouse=self.warehouse).exclude(zakaz__owner__id=577).aggregate(sum=Sum('quantity'))['sum'] or 0

        if self.warehouse.type == 0:
            if self.item.availability == 20:
                return (u'Под заказ', 'text-success')
            else:
                if self.item.quantity_in_stock + self.left - count_zakaz < 1:
                    return (u'Нет в наличии', 'text-muted')
                elif self.item.quantity_in_stock + self.left - count_zakaz == 1:
                    return (u'Мало', 'text-danger')
                elif self.item.quantity_in_stock + self.left - count_zakaz > 1 and self.item.quantity_in_stock + self.left - count_zakaz < 5:
                    return (u'Достаточно', 'text-warning')
                else:
                    return (u'Много', 'text-success')
        if self.left - count_zakaz < 1:
            return (u'Нет в наличии', 'text-muted')
        elif self.left - count_zakaz == 1:
            return (u'Мало', 'text-danger')
        elif self.left - count_zakaz > 1 and self.left - count_zakaz < 5:
            return (u'Достаточно', 'text-warning')
        else:
            return (u'Много', 'text-success')


class MovementOfGoods(models.Model):
    class Meta:
        verbose_name = u"Перемещение"
        verbose_name_plural = u"Перемещения"

    courier_paid = models.BooleanField(default=False, verbose_name=u"Оплачено курьеру")
    delivery_date = models.DateField(blank=True, null=True, verbose_name=u"Дата доставки")
    date_end = models.DateTimeField(verbose_name=u'Дата завершения', null=True, blank=True)
    creation_date = models.DateField(auto_now_add=True, verbose_name=u'Дата создания')

    status = models.IntegerField(choices=MOVEMENTOFGOODSCHOICES, default=0, verbose_name=u'Статус')

    courier = models.ForeignKey(Account, blank=True, null=True, limit_choices_to={'groups__permissions__codename': 'courier'}, verbose_name=u'Курьер', on_delete=models.SET_NULL)
    warehouse_donor = models.ForeignKey(WareHouse, related_name='warehouse_giving', verbose_name=u'Склад-отправитель', on_delete=models.CASCADE)
    warehouse_recieving = models.ForeignKey(WareHouse, related_name='warehouse_recieving', verbose_name=u'Склад-получатель', on_delete=models.CASCADE)
    extra = models.TextField(u'Комментарий', blank=True, null=True)

    details = models.TextField(u'Лог', blank=True, null=True)

    ordered = models.BooleanField(verbose_name=u'Обработано в автосборке', default=True)

    def __str__(self):
        return u'{}->{}'.format(self.warehouse_donor, self.warehouse_recieving)

    def get_goods(self):
        return self.goodsinmovement_set.all()

    def get_items_to_print(self):
        """
        Метод используется в print.html для распечатки ценников
        """
        return self.get_goods()

    def last_edit(self):
        if MovementStatusLog.objects.filter(movement=self.id).exists():
            return MovementStatusLog.objects.filter(movement=self.id).order_by('-date')[0:1].values()[0]['date']
        else:
            return False

    def get_short_courier(self):
        courier = '-'
        color = 'black'
        if self.courier:
            if self.courier_id == 3642:
                color = '#FF96EC'
            if self.courier_id == 3095:
                color = '#33B027'
            if self.courier_id == 1827:
                color = 'gray'
            if self.courier_id == 1 or self.courier_id == 142:
                color = '#477EFF'
            courier = format_html(u'<span style="color:{0}"> {1}{2}</span>', color, self.courier.first_name[0:3], self.courier.last_name[0:1])
        return courier

    get_short_courier.allow_tags = True
    get_short_courier.short_description = u'Кур'

    def save(self, request, **kwargs):
        old_obj = None  # Optional[MovementOfGoods]
        if self.id:
            old_obj = MovementOfGoods.objects.filter(id=self.id).first()
            if self.status != old_obj.status:
                log = MovementStatusLog()
                log.movement = self
                log.user = request.user
                log.status = self.status
                log.save()
        if not self.date_end and self.status == 6:  # Перемещние завершено
            self.date_end = datetime.datetime.now()
            goods = self.get_goods()
            for product in goods:
                item_left_donor = product.item.leftitem_set.filter(warehouse=self.warehouse_donor).first()
                if not item_left_donor:
                    continue
                item_left_donor.left -= product.quantity
                item_left_donor.save()
                item_left_reciever = product.item.leftitem_set.filter(warehouse=self.warehouse_recieving).first()
                if not item_left_reciever:
                    item_left_reciever = LeftItem()
                    item_left_reciever.item = product.item
                    item_left_reciever.warehouse = self.warehouse_recieving
                item_left_reciever.left += product.quantity
                item_left_reciever.save()
                reserve_log_donor = ReserveLog()
                reserve_log_donor.item = product.item
                reserve_log_donor.movement = self
                reserve_log_donor.count_move = -product.quantity
                reserve_log_donor.residue = item_left_donor.left
                reserve_log_donor.save()
                reserve_log_reciever = ReserveLog()
                reserve_log_reciever.item = product.item
                reserve_log_reciever.movement = self
                reserve_log_reciever.count_move = product.quantity
                reserve_log_reciever.residue = item_left_reciever.left
                reserve_log_reciever.save()
        return super(MovementOfGoods, self).save(**kwargs)


class GoodsInMovement(models.Model):
    class Meta:
        verbose_name = u"Товар перемещения"
        verbose_name_plural = u"Товары перемещения"

    movement = models.ForeignKey(MovementOfGoods, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.IntegerField()

    def get_segment(self):
        return self.item.deckitem.segment_new

    get_segment.short_description = u'Пост.'

    def get_thumbnail(self):
        return self.item.get_photo_thumbnail()

    get_thumbnail.allow_tags = True
    get_thumbnail.short_description = u'Фото'

    def get_cover(self):
        return self.item.deckitem.cover()

    def item__quantity_in_reserve(self):
        quantity_in_reserve_str = format_html(u'== {0}', self.item.quantity_in_reserve)
        warehoeses = WareHouse.objects.all()
        for i in warehoeses:
            left = 0
            if LeftItem.objects.filter(warehouse=i, item=self.item).count() == 1:
                left = LeftItem.objects.get(warehouse=i, item=self.item).left
            warehouse_str = u'%s %s ' % (i.name[0:2], left)
            quantity_in_reserve_str += format_html(u'<br>{0} ', warehouse_str)
        return format_html(u"{0}", quantity_in_reserve_str)

    item__quantity_in_reserve.allow_tags = True
    item__quantity_in_reserve.short_description = u'Остатки'

    def item__quantity_in_stock(self):
        return str(self.item.quantity_in_stock)

    item__quantity_in_stock.allow_tags = True
    item__quantity_in_stock.short_description = u'У поставщика'

    def buy_count_3_month(self):
        return self.item.buy_count_3_month()

    buy_count_3_month.allow_tags = True
    buy_count_3_month.short_description = u'Куплено за 3 месяца'

    def item__vreserve(self):
        count = 0
        color = 'green'
        orders = format_html('')
        if ZakazGoods.objects.filter(item=self.item.id, zakaz__status__in=[2, 3, 4, 5]).exclude(id=self.id).aggregate(
                sum=Sum('quantity'))['sum']:
            count = \
                ZakazGoods.objects.filter(item=self.item.id, zakaz__status__in=[2, 3, 4, 5]).exclude(
                    id=self.id).aggregate(
                    sum=Sum('quantity'))['sum']
            for i in ZakazGoods.objects.filter(item=self.item.id, zakaz__status__in=[2, 3, 4, 5]).exclude(
                    id=self.id).values():
                orders += format_html('<br><a target="_blank" href="/DgJrfdJg/catalog/zakaz/{0}/">{1}&rarr;</a>',
                                      i['zakaz_id'], i['zakaz_id'])
            color = 'red'
        return format_html("<span style='color: {0}'>{1}</span>{2}", color, count, orders)

    item__vreserve.allow_tags = True
    item__vreserve.short_description = u'В резерве'

    def item__vreserve_order(self):
        orders = format_html('')
        if ZakazGoods.objects.filter(item=self.item.id, zakaz__status__in=[2, 3, 31, 4, 5]).exclude(id=self.id).aggregate(
                sum=Sum('quantity'))['sum']:
            for i in ZakazGoods.objects.filter(item=self.item.id, zakaz__status__in=[2, 3, 31, 4, 5]).exclude(
                    id=self.id).values():
                orders += format_html("<a target='_blank' href='/DgJrfdJg/catalog/zakaz/{0}/'>{1}&rarr;</a><br>",
                                      i['zakaz_id'], i['zakaz_id'])
        return format_html("{0}", orders)

    item__vreserve_order.allow_tags = True
    item__vreserve_order.short_description = u'В резерве заказы'

    def item__vreserve_plain(self):
        count = 0
        color = 'green'
        if ZakazGoods.objects.filter(item=self.item.id, zakaz__status__in=[2, 3, 31, 4, 5]).exclude(id=self.id).aggregate(
                sum=Sum('quantity'))['sum']:
            count = \
                ZakazGoods.objects.filter(item=self.item.id, zakaz__status__in=[2, 3, 31, 4, 5]).exclude(
                    id=self.id).aggregate(
                    sum=Sum('quantity'))['sum']
            color = 'red'
        return format_html("<span style='color: {0}'>{1}</span>", color, count)

    item__vreserve_plain.allow_tags = True
    item__vreserve_plain.short_description = u'В резерве кол-во'

    def item__vreserve_count(self):
        count = 0
        if ZakazGoods.objects.filter(item=self.item.id, zakaz__status__in=[2, 3, 31, 4, 5]).exclude(id=self.id).aggregate(
                sum=Sum('quantity'))['sum']:
            count = \
                ZakazGoods.objects.filter(item=self.item.id, zakaz__status__in=[2, 3, 31, 4, 5]).exclude(
                    id=self.id).aggregate(
                    sum=Sum('quantity'))['sum']
        return count

    def check_insideorder_sum(self):
        sum = 0
        if InsideZakazGoods.objects.filter(item=self.item_id, zakaz__status__in=[0, 2, 4]).exists():
            sum = InsideZakazGoods.objects.filter(item=self.item_id, zakaz__status__in=[0, 2, 4]).aggregate(
                sum=Sum('quantity'))['sum']
        return sum

    check_insideorder_sum.allow_tags = True
    check_insideorder_sum.short_description = u'ПЗП'

    def check_insideorder_sum_forautoinsideorder(self):
        sum = 0
        if InsideZakazGoods.objects.filter(item=self.item_id, zakaz__status__in=[0, 2, 4], quantity__gte=0).exists():
            sum = \
                InsideZakazGoods.objects.filter(item=self.item_id, zakaz__status__in=[0, 2, 4], quantity__gte=0).aggregate(
                    sum=Sum('quantity'))['sum']
        return sum

    def check_insideorder(self):
        inside_order = False
        if InsideZakazGoods.objects.filter(item=self.item_id, zakaz__status__in=[0, 2, 4]).exists():
            inside_order_goods = InsideZakazGoods.objects.filter(item=self.item_id, zakaz__status__in=[0, 2, 4])[
                                 0:1].select_related('zakaz')
            inside_order = inside_order_goods[0].zakaz
        return inside_order

    check_insideorder.allow_tags = True
    check_insideorder.short_description = u'ПЗП'


class MovementStatusLog(models.Model):
    class Meta:
        verbose_name = u"Лог статуса перемещения"
        verbose_name_plural = u"Логи статуса перемещения"

    status = models.IntegerField(choices=MOVEMENTOFGOODSCHOICES, default=0, verbose_name=u"Статус")
    date = models.DateTimeField(verbose_name=u"Когда изменил", auto_now_add=True)
    user = models.ForeignKey(Account, verbose_name=u"Кто изменил", null=True, blank=True, on_delete=models.SET_NULL)
    movement = models.ForeignKey(MovementOfGoods, on_delete=models.CASCADE)


class ItemPriceChange(models.Model):

    item = models.ForeignKey(
        to=Item,
        verbose_name=u'Товар (вес/тип с ценой)',
        on_delete=models.CASCADE
    )

    warehouse = models.ForeignKey(
        to=WareHouse,
        verbose_name=u'Магазин',
        on_delete=models.CASCADE
    )

    is_processed = models.BooleanField(
        verbose_name=u'Обработано',
        default=False
    )

    date = models.DateField(
        verbose_name=u'Дата создания',
        help_text=u'Соответствует дате, когда был запущен парсер цен, создавший данную запись в базе',
        auto_now_add=True
    )

    class Meta:
        verbose_name = u'изменение прайса'
        verbose_name_plural = u'Изменения прайсов'
        ordering = ['-date']

    def __str__(self):
        return '[%s] %s' % (str(self.warehouse), str(self.item))