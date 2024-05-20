# -*- coding: utf-8 -*-
from pprint import pformat
import re

from django import forms
from django.contrib import admin
from django.contrib.admin.options import StackedInline, TabularInline
from django.contrib.admin import SimpleListFilter
from django.http import HttpResponseRedirect
from django.db import models
from django.db.models.fields.related import ManyToManyField
from django.db.models import Q, F
from django.db.models.expressions import RawSQL
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.safestring import mark_safe
from django.utils.html import format_html

from reversion import revisions as reversion
from reversion.admin import VersionAdmin

from adminsortable2.admin import SortableInlineAdminMixin

from catalog.widgets import CheckboxSelectMultiple
from django_admin_inline_paginator.admin import TabularInlinePaginated

from catalog.tuples import ORDER_STATUS, INSIDE_ORDER_STATUS
from catalog.enums import MOVEMENTOFGOODSCHOICES
from .models import ProducerCategory, Producer, Item, Deckitem, Tag, Zakaz, ZakazGoods, ZakazStatusLog, InsideZakaz, \
    InsideZakazGoods, \
    TempZakaz, TempZakazGoods, Commentitem, GroupFilter, Filter, ReserveLog, InsideZakazStatusLog, VendorAccount, \
    Expense, ExpenseType, Courier, SaleTable, ParserLog, ZakazBonus, OutsideZakaz, ItemPhoto, LogingCourierFinish, \
    AutoZakazGoods, AutoZakazStatusLog, AutoZakaz, OutsideZakazStatusLog, ItemSale, FilterDescription, PriceParser, \
    ItemAvailabilityLog, Segment, LeftItem, WareHouse, MovementOfGoods, MovementStatusLog, GoodsInMovement, ItemPriceChange, BasketOfGoodItem, \
    ZakazGoodsBaskedOfGoodsProxy
from math import ceil
from sberbank.models import Payment
from django.conf import settings
from catalog.widgets import InlineItemPhotoForeignKeyRawIdWidget
from catalog.tuples import AVAILABILTY_DICT

if False:
    from typing import Callable

import datetime
import logging



logger = logging.getLogger(__name__)


class ProducerCategoryAdmin(VersionAdmin):
    pass


def print_items(warehouse):
    # type: (WareHouse) -> Callable
    def print_for_warehouse(modeladmin, request, queryset):
        items_ids = []
        # filter_arg это может быть Producer или Segment
        lookup_ends = {
            "Producer": "deckitem__producer",
            "Segment": "deckitem__segment_new",
            "New": "newitems__new",
        }
        for filter_arg in queryset:
            class_name = filter_arg.__class__.__name__
            lookup = "item__{}".format(lookup_ends.get(class_name))
            leftitems = warehouse.get_items_to_print().filter(
                Q(**{lookup: filter_arg}),
            )
            for leftitem in leftitems:
                leftitem  # type: LeftItem
                items_ids.append(str(leftitem.id))
        url = reverse('print_view')
        ids = ",".join(items_ids)
        url = u"{}?ids={}".format(url, ids)
        return redirect(url)

    print_for_warehouse.short_description = u"Распечатать ценники для склада {0}".format(warehouse.name)
    print_for_warehouse.__name__ = 'print_for_warehouse_{0}'.format(warehouse.id)

    return print_for_warehouse


class SegmentAdmin(VersionAdmin):
    list_display = ['title', 'order', 'in_statistics', 'in_balans']
    list_editable = ['order']
    list_filter = ['in_statistics', 'in_balans']

    def get_actions(self, request):
        actions = super(VersionAdmin, self).get_actions(request)
        warehouses = WareHouse.objects.all()
        for warehouse in warehouses:
            action = print_items(warehouse)
            actions[action.__name__] = (
                action,
                action.__name__,
                action.short_description
            )
        return actions


class ProducerAdmin(VersionAdmin):
    list_display = ['title', 'id', 'link', 'active', 'margin', 'margin_heavy', 'margin_zavodchiki', 'margin_opt', 'on_main', 'sort']
    list_filter = ['producercategory', 'active', 'on_main']
    list_editable = ['active', 'margin', 'margin_heavy']
    filter_vertical = ['producercategory']
    fieldsets = (
        (u'', {'fields': (
            'title', 'link', 'active', 'producercategory', 'original_image', ('margin', 'margin_heavy'), ('margin_zavodchiki', 'margin_opt'), 'sort', 'on_main', 'sort_main', 'slider_link')}),
        (u'SEO', {'fields': ('html_title', 'header', 'meta_description', 'meta_keywords', 'seo_text')}),
    )

    def get_actions(self, request):
        actions = super(VersionAdmin, self).get_actions(request)
        warehouses = WareHouse.objects.all()
        for warehouse in warehouses:
            action = print_items(warehouse)
            actions[action.__name__] = (
                action,
                action.__name__,
                action.short_description
            )
        return actions


class InlineItemAdmin(StackedInline):
    model = Item
    show_change_link = True
    ordering = ['real_price']
    readonly_fields = ['quantity_in_reserve', ]
    fieldsets = (
        (u'', {'fields': (
            ('weight', 'real_price', 'price'),
            ('article', 'code'), 'barcode',
            ('availability', 'quantity_in_reserve', 'quantity_in_stock'),
            'temporarily_unavailable',
            ('active', 'heavy', 'new', 'order'),
        )}),
        (u'автозаказ',
         {'classes': ('collapse', 'close'), 'fields': (('minimum_need', 'count_for_zakaz', 'amount_in_block'),)}),
    )

    extra = 0


class InlineCommentitemAdmin(TabularInline):
    model = Commentitem
    readonly_fields = ['date', ]
    fields = ['name', 'text', 'date', 'status']
    ordering = ['-date', ]
    extra = 0


class TagAdmin(VersionAdmin):
    list_display = ['title', 'id', 'section', 'sort']
    list_editable = ['sort']
    fieldsets = (
        (u'', {'classes': ('wide',), 'fields': ('section', 'title', 'title_search', 'link', 'sort')}),
        (u'SEO',
         {'classes': ('wide',), 'fields': ('header', 'html_title', 'meta_description', 'meta_keywords', 'seo_text')}),
    )
    ordering = ['section', 'sort', 'title']
    list_filter = ['section']


class InlineFilter(StackedInline):
    model = Filter
    ordering = ['tag', 'sort', 'title']
    fields = ('title', 'link', 'sort', 'tag', 'hide')
    extra = 0


class ItemPhotoAdmin(admin.ModelAdmin):
    readonly_fields = ['photo_inline']
    fields = ['title', 'cover', 'original_image', 'photo_inline', 'deckitem']
    ordering = ['deckitem', 'order']


# class InlineItemPhoto(SortableInlineAdminMixin, TabularInline):
class InlineItemPhoto(TabularInline):
    model = ItemPhoto
    readonly_fields = ['photo_inline']
    fields = ['photo_inline', 'original_image', 'title', 'deckitem', 'item', 'cover']
    extra = 0

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'item':
            db = kwargs.get('using')
            deckitem_id_matches = re.findall('([0-9]+)', request.path)
            if len(deckitem_id_matches) > 0:
                deckitem_id = deckitem_id_matches[0]
            else:
                deckitem_id = None
            kwargs['widget'] = InlineItemPhotoForeignKeyRawIdWidget(db_field.remote_field, self.admin_site, deckitem_id, using=db)
        return super(InlineItemPhoto, self).formfield_for_foreignkey(db_field, request, **kwargs)


class FilterDeckitemInline(admin.TabularInline):
    model = Filter.deckitems.through
    raw_id_fields = ['deckitem']


class FilterAdmin(VersionAdmin):
    filter_vertical = ['deckitems', ]
    list_display = ['title', 'id', 'tag', 'seo_title', 'link', 'sort', 'parent', 'hide', 'view']
    readonly_fields = ['view']
    fieldsets = (
        (u'', {'classes': ('wide',), 'fields': ('title', 'link', 'tag')}),
        (u'', {'fields': ('hint', 'sort', 'hide', 'view', 'seo_title')}),
    )
    ordering = ['tag', 'sort', 'title']
    inlines = [FilterDeckitemInline, ]
    list_filter = ['tag', 'hide']
    search_fields = ['title', 'link']
    list_editable = ['sort', 'tag', 'seo_title']


class GroupFilterAdmin(admin.ModelAdmin):
    filter_vertical = ['filter', ]
    list_display = ['title', 'sort', 'id', 'link', 'tag', 'is_tag']
    ordering = ['tag', 'sort', 'title']
    list_editable = ['sort', ]
    list_filter = ['tag']
    fieldsets = (
        (u'', {'classes': ('wide',), 'fields': ('tag', 'title', 'link', 'is_tag')}),
        (u'', {'classes': (), 'fields': ('sort', 'filter')})
    )


class ShowDeckItemsActive(SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = u'Наличие активных Вес/Тип с ценой'

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'in_reserve'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return (
            ('1', u'Есть'),
            ('0', u'Нету'),
        )

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # Compare the requested value (either '80s' or 'other')
        # to decide how to filter the queryset.
        if self.value() == '1':
            return queryset.filter(item__active=True, active=False)
        if self.value() == '0':
            return queryset.filter(item__active=False, active=False)


class DeckitemAdmin(VersionAdmin):
    list_display = ['title', 'id', 'get_last_buy_date', 'get_active_item_count', 'photo_thumb', 'order', 'title_en', 'views', 'number_of_purchases']
    list_filter = [ShowDeckItemsActive, 'active', 'producer', 'segment_new', 'tag', 'on_main', 'type']
    search_fields = ['title', 'title_en', 'id']
    readonly_fields = ['get_active_item_count', 'get_last_buy_date']
    save_on_top = True
    ordering = ['id']

    filter_vertical = ['all_tags']
    fieldsets = (
        (u'', {'classes': ('wide',), 'fields': ('producer', 'segment_new', 'title', 'title_en', 'tag')}),
        (u'', {'classes': (), 'fields': ('all_tags', 'active')}),
        (u'Фильтры', {'classes': ('wide',), 'fields': ('filters',)}),
        (u'Описание', {'classes': ('wide',), 'fields': ('description',
                                                        'composition_title', 'composition',
                                                        'ration_title', 'ration')}),
        (u'Видимость', {'classes': ('collapse', 'close'), 'fields': (('on_main', 'views', 'order'),)}),
        (u'SEO', {'classes': ('wide', 'collapse', 'close'), 'fields': (
            'link', 'last_edit', 'super_description', 'header', 'html_title', 'meta_description', 'meta_keywords',
            'seo_text')}),
    )
    inlines = [InlineItemAdmin, InlineItemPhoto, InlineCommentitemAdmin]

    # formfield_overrides = {
    #     ManyToManyField: {'widget': CheckboxSelectMultiple},
    # }

    class Media:
        css = {
            "all": ("kostochka38/css/filter.css", 'kostochka38/css/admin-chosen.css')
        }
        js = ['admin/list_filter_collapse.js']

    def get_form(self, request, obj=None, **kwargs):
        u""" Форма. """
        setattr(request, 'obj', obj)
        return super(DeckitemAdmin, self).get_form(request, obj, **kwargs)

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        u""" Формирует поля для ManyToMany. """
        if db_field.name == 'filters':
            if hasattr(request, 'obj') and request.obj:
                groups = GroupFilter.objects.filter(tag__in=request.obj.all_tags.all())
            else:
                groups = GroupFilter.objects.filter(tag__id__in=[0])
            qs = Filter.objects.filter(groupfilter__in=groups)
            # parents = list(qs.filter(parent__isnull=False).values_list('parent_id', flat=True))
            # ids = parents + list(qs.values_list('id', flat=True))
            ids = list(qs.values_list('id', flat=True))
            # kwargs['queryset'] = Filter.objects.filter(
            #     Q(id__in=ids) | Q(parent__in=ids)
            # )
            kwargs['queryset'] = Filter.objects.filter(Q(id__in=ids))

        return super(DeckitemAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        """
        Given a model instance save it to the database.
        """
        obj.save()

        # Сохранение прикреплённых изображений (deckitem_images в шаблоне submit_line.html)
        for image in request.FILES.getlist('deckitem_images'):
            ItemPhoto.objects.create(
                deckitem=obj,
                original_image=image,
            )


admin.site.register(Deckitem, DeckitemAdmin)


class CommentitemAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'date']


admin.site.register(Commentitem, CommentitemAdmin)


class InlineReserveLog(TabularInlinePaginated):
    model = ReserveLog
    can_delete = False
    readonly_fields = ['date', 'zakaz_link', 'inside_zakaz_link', 'movement_link', 'count_move', 'residue', 'get_warehouse']
    fields = ['date', 'zakaz_link', 'inside_zakaz_link', 'movement_link', 'count_move', 'residue', 'get_warehouse']
    extra = 0
    max_num = 0
    per_page = 20

    def get_warehouse(self, obj):
        if obj.zakaz:
            return obj.zakaz.warehouse
        if obj.inside_zakaz:
            return obj.inside_zakaz.warehouse
        if obj.movement:
            if obj.count_move < 0:
                return obj.movement.warehouse_donor
            else:
                return obj.movement.warehouse_recieving
        return ''
    get_warehouse.short_description = u"Склад"


class ShowItemsInReserve(SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = u'Наличие на складе'

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'in_reserve'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return (
            ('1', u'Есть'),
            ('0', u'Нету'),
        )

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # Compare the requested value (either '80s' or 'other')
        # to decide how to filter the queryset.
        if self.value() == '1':
            return queryset.filter(quantity_in_reserve__gt=0)
        if self.value() == '0':
            return queryset.filter(quantity_in_reserve__lte=0)


class ProducerListFilter(SimpleListFilter):
    title = u'Производитель'

    parameter_name = 'producer_id'

    def lookups(self, request, model_admin):
        segment_id = request.GET.get('deckitem__segment_new__id__exact')
        if segment_id:
            segment_new_ids = Deckitem.objects.filter(
                segment_new__id=segment_id
            ).values_list('producer__id', flat=True)
            return Producer.objects.filter(
                id__in=segment_new_ids
            ).distinct().values_list('id', 'title')
        else:
            return Producer.objects.values_list('id', 'title')

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(deckitem__producer__id=self.value())


class ShowItemsInReserveBasketOfGoods(SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = u'Наличие на складе'

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'in_reserve'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return (
            ('1', u'Есть'),
            ('0', u'Нету'),
        )

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # Compare the requested value (either '80s' or 'other')
        # to decide how to filter the queryset.
        if self.value() == '1':
            return queryset.filter(item__quantity_in_reserve__gt=0)
        if self.value() == '0':
            return queryset.filter(item__quantity_in_reserve__lte=0)


class ItemSaleForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ItemSaleForm, self).__init__(*args, **kwargs)
        self.fields['item'].queryset = Item.objects.all() \
            .select_related('deckitem')

    class Meta:
        model = ZakazGoods
        fields = []


class ItemSaleAdmin(VersionAdmin):
    list_display = ['item', 'date_end', 'sale', 'sale_target', 'show']
    list_editable = ['sale', 'sale_target', 'show']
    raw_id_fields = ['item', ]
    pass


class InlineItemSale(TabularInline):
    model = ItemSale
    extra = 1


class InlineItemAvailabilityLog(TabularInlinePaginated):
    model = ItemAvailabilityLog
    readonly_fields = ['availability', 'date']
    ordering = ['-date']
    extra = 0
    per_page = 20


class InlineItemLeftAdmin(TabularInline):
    model = LeftItem
    extra = 0
    readonly_fields = ['item', 'warehouse', 'left']


class ItemAdmin(VersionAdmin):
    # list_editable = ['']
    # list_editable = ['article', 'code']
    search_fields = ['deckitem__title', 'deckitem__title_en', 'id', 'deckitem__id', 'article', 'code']
    formfield_overrides = {
        models.TextField: {'widget': forms.Textarea(attrs={'rows': 2, 'cols': 15})}
    }
    list_filter = (
        ShowItemsInReserve, 'temporarily_unavailable', 'active', 
        'availability', 'deckitem__segment_new', ProducerListFilter, 
        'deckitem__tag', 'new', 'heavy', 'on_main')
    readonly_fields = ['get_suplier', 'get_photo_thumbnail', 'vreserve', 'quantity_in_reserve', 'go_to_deckitem',
                       'last_order_date', 'number_of_purchases', 'count_of_purchases', 'current_price',
                       'buy_count_3_month', 'date_created']
    list_display = ['title', 'id', 'get_photo_thumbnail', 'barcode', 'weight', 'current_price', 'get_suplier', 'availability',
                    'temporarily_unavailable', 'new', 'vreserve', 'last_order_date',
                    'quantity_in_reserve', 'quantity_in_stock', 'number_of_purchases', 'count_of_purchases',
                    'buy_count_3_month']
    list_editable = ['barcode']
    list_per_page = 30
    raw_id_fields = ['deckitem']
    fieldsets = (
        (
            u'', {
                'fields': (
                    'deckitem', 'get_photo_thumbnail',
                    ('weight', 'real_price', 'price'),
                    'current_price', ('article', 'code',),
                    'get_suplier', 'barcode'
                )
            }
        ),
        (
            u'Видимость', {
                'fields': (('active', 'new', 'date_created', 'order'), 'heavy', 'on_main')
            }
        ),
        (
            u'Наличие', {
                'fields': (
                    ('availability', 'temporarily_unavailable'),
                    ('quantity_in_reserve', 'quantity_in_stock'),
                    'vreserve'
                )
            }
        ),
        (u'Статистика', {'fields': ('last_order_date', ('number_of_purchases', 'count_of_purchases'),)}),
        (u'Автозаказ',
         {'classes': ('collapse', 'open'), 'fields': (('minimum_need', 'count_for_zakaz', 'amount_in_block'),)}),
    )

    inlines = [InlineItemSale, InlineItemLeftAdmin, InlineReserveLog, InlineItemAvailabilityLog]

    def get_queryset(self, request):
        queryset = super(ItemAdmin, self).get_queryset(request)
        stop_date = datetime.datetime.now()
        start_date = stop_date - datetime.timedelta(days=90)
        queryset = queryset.annotate(
            _buy_count_3_month=RawSQL('SELECT COALESCE(SUM(catalog_zakazgoods.quantity), 0) FROM catalog_zakazgoods INNER JOIN catalog_zakaz ON catalog_zakaz.id=catalog_zakazgoods.zakaz_id WHERE catalog_zakazgoods.item_id=catalog_item.id AND catalog_zakaz.owner_id<>577 AND COALESCE(catalog_zakazgoods.sale, 0)<25 AND catalog_zakaz.status=6 AND catalog_zakaz.date>=%s AND catalog_zakaz.date<%s', (start_date.strftime('%Y-%m-%d'), stop_date.strftime('%Y-%m-%d')))
        )
        return queryset

    def get_readonly_fields(self, request, obj=None):
        fields = set(super(ItemAdmin, self).get_readonly_fields(request, obj))
        if request.user.groups.filter(id=3).first():
            fields.add("deckitem")
            for field in Item._meta.get_fields():
                field_name = field.__dict__.get('attname')
                if not field_name:
                    continue
                if field_name != "barcode":
                    fields.add(field_name)
        return fields

    class Media:
        css = {
            "all": ("kostochka38/css/filter.css", 'kostochka38/css/admin-chosen.css')
        }
        js = ['admin/list_filter_collapse.js']


class BasketOfGoodItemAdmin(VersionAdmin):
    search_fields = [
        'item__deckitem__title',
        'item__deckitem__title_en',
        'item__id',
        'item__deckitem__id',
        'item__article',
        'item__code'
    ]

    list_display = [
        'item__title',
        'item__get_photo_thumbnail',
        'date_started',
        'date_ended',
        'item__get_suplier',
        'item__availability',
        'item__temporarily_unavailable',
        'item__vreserve',
        'item__quantity_in_reserve',
        'item__quantity_in_stock'
    ]

    raw_id_fields = ['item']

    list_filter = [
        ShowItemsInReserveBasketOfGoods,
        'item__temporarily_unavailable',
        'item__active',
        'item__availability',
        'item__deckitem__segment_new',
        'item__deckitem__producer',
        'item__deckitem__tag',
        'item__new',
        'item__heavy',
        'item__on_main'
    ]

    def item__get_photo_thumbnail(self, obj):
        return obj.item.get_photo_thumbnail()
    item__get_photo_thumbnail.short_description = u'Фото'

    def item__title(self, obj):
        return mark_safe(obj.item.title())
    item__title.short_description = u'Название'

    def item__get_suplier(self, obj):
        return obj.item.get_suplier()
    item__get_suplier.short_description = u'Поставщик'

    def item__availability(self, obj):
        return AVAILABILTY_DICT[obj.item.availability]
    item__availability.short_description = u'Наличие товара'

    def item__temporarily_unavailable(self, obj):
        return 'Да' if obj.item.temporarily_unavailable is True else 'Нет'
    item__temporarily_unavailable.short_description = u'Временно недоступен'

    def item__vreserve(self, obj):
        return obj.item.vreserve()
    item__vreserve.short_description = u'Резерв'

    def item__quantity_in_reserve(self, obj):
        return obj.item.quantity_in_reserve
    item__quantity_in_reserve.short_description = u'На складе'

    def item__quantity_in_stock(self, obj):
        return obj.item.quantity_in_stock
    item__quantity_in_stock.short_description = u'У поставщика'

    class Media:
        css = {
            "all": ("kostochka38/css/filter.css", 'kostochka38/css/admin-chosen.css')
        }
        js = ['admin/list_filter_collapse.js']


class InlineTempZakazGoodsAdmin(TabularInline):
    model = TempZakazGoods
    readonly_fields = ['summ', 'get_thumbnail']
    fields = ['item', 'get_thumbnail', 'quantity', 'summ']
    extra = 0
    ordering = ['item__deckitem__producer', ]


class TempZakazAdmin(admin.ModelAdmin):
    list_display = ['owner', 'date', 'summ', 'hash']
    list_filter = ['owner', 'date']
    save_on_top = True
    inlines = [InlineTempZakazGoodsAdmin]


class ZakazGoodsForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ZakazGoodsForm, self).__init__(*args, **kwargs)
        self.fields['item'].queryset = Item.objects.all() \
            .select_related('deckitem')

    class Meta:
        model = ZakazGoods
        fields = []


class AutoZakazGoodsForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(AutoZakazGoodsForm, self).__init__(*args, **kwargs)
        self.fields['item'].queryset = Item.objects.all() \
            .select_related('deckitem')

    class Meta:
        model = ZakazGoods
        fields = []

# class ZakazGoodsAdmin(admin.TabularInline):
#     model = ZakazGoods
#     # form = ZakazGoodsForm
#     raw_id_fields = ('item',)
#     readonly_fields = ['get_item_id', 'get_thumbnail', 'item__vreserve', 'item__quantity_in_reserve',
#                        'item__quantity_in_stock', 'item__code', 'link', 'get_segment', 'buy_count_3_month', 'get_presale']
#     fields = ['get_item_id', 'get_presale', 'item', 'get_segment', 'item__code', 'get_thumbnail', 'buy_count_3_month', 'presale', 'quantity',
#               'sale', 'summ', 'item__vreserve', 'item__quantity_in_reserve', 'item__quantity_in_stock']
#     extra = 0
#     ordering = ['item__deckitem__producer', 'id']
#
#     class Media:
#         css = {
#             "all": ('kostochka38/css/admin-chosen.css',)
#         }

# ЗАКАЗЫ
class InlineZakazGoodsAdmin(TabularInline):
    model = ZakazGoods
    # form = ZakazGoodsForm
    raw_id_fields = ('item',)
    readonly_fields = ['get_item_id', 'get_thumbnail', 'item__vreserve', 'item__quantity_in_reserve',
                       'item__quantity_in_stock', 'item__code', 'link', 'get_segment', 'buy_count_3_month', 'get_presale', 'render_action']
    fields = ['get_item_id', 'get_presale', 'render_action', 'item', 'get_segment', 'item__code', 'get_thumbnail', 'buy_count_3_month', 'presale', 'quantity',
              'sale', 'summ', 'item__vreserve', 'item__quantity_in_reserve', 'item__quantity_in_stock']
    extra = 0
    ordering = ['item__deckitem__producer', 'id']

    class Media:
        css = {
            "all": ('kostochka38/css/admin-chosen.css',)
        }

    def render_action(self, obj):
        if obj.basket_of_good:
            return mark_safe(
                '<img src="/static/kostochka38/images/bober.png" title="Корзина добра" height="50px">'
            )
        elif obj.action is not None:
            action_change_url = reverse('admin:news_new_change', args=[obj.action.id])
            return mark_safe((
                '<div style="background-color: red; padding: 5px 10px;">'
                '<a href="%s" style="color: white;">%s</a>'
                '</div>'
            ) % (action_change_url, obj.action))
        return u'-'
    render_action.short_description = u'Акция'



    def get_readonly_fields(self, request, obj=None):
        if obj:
            if request.user.id not in SUPER_ADMIN_IDS and request.user.id not in SQUAD_IDS:  # если не Админы!

                if obj.status in [3, 31, 4, 5, 6, 7]:
                    """
                    (3, u'Заказ собран'),
                    (31, u'Заказ у курьера'),
                    (4, u'Курьер выехал'),
                    (5, u'Заказ доставлен'),
                    (6, u'Завершен'),
                    (7, u'Отказ от заказа'),
                    (10, u'Отменен'),
                    """
                    return ['get_item_id', 'get_thumbnail', 'item__vreserve', 'item__quantity_in_reserve',
                            'item__quantity_in_stock', 'item__code', 'link', 'get_segment', 'buy_count_3_month', 'item',
                            'get_segment', 'item__code', 'get_thumbnail', 'buy_count_3_month', 'quantity', 'sale',
                            'summ', 'item__vreserve', 'item__quantity_in_reserve', 'item__quantity_in_stock', 'get_presale', 'presale', 'render_action']
        # return self.readonly_fields
        return super(InlineZakazGoodsAdmin, self).get_readonly_fields(request, obj)

    def has_delete_permission(self, request, obj=None):
        if request.user.id not in SUPER_ADMIN_IDS and request.user.id not in SQUAD_IDS:  # если не Админы!
            if obj:
                if obj.status in [3, 31, 4, 5, 6, 7]:
                    return False
            return True
        else:
            return True



reversion.register(ZakazGoods)


class InlineAutoZakazGoodsAdmin(admin.TabularInline):
    model = AutoZakazGoods
    form = AutoZakazGoodsForm
    raw_id_fields = ('item',)
    readonly_fields = ['get_thumbnail', 'item__vreserve', 'item__quantity_in_reserve', 'item__quantity_in_stock',
                       'item__code', 'link']
    fields = ['item', 'link', 'item__code', 'get_thumbnail', 'quantity', 'item__vreserve', 'item__quantity_in_reserve',
              'item__quantity_in_stock']
    extra = 0
    ordering = ['item__deckitem__producer', 'id']


reversion.register(AutoZakazGoods)


class InlineInsideZakazGoodsAdmin(TabularInline):
    model = InsideZakazGoods
    # form = ZakazGoodsForm
    raw_id_fields = ('item',)
    readonly_fields = ['get_thumbnail', 'item__quantity_in_reserve', 'item__quantity_in_stock', 'item__code', 'link',
                       'buy_count_3_month', 'item__vreserve', 'render_action']
    fields = ['item', 'render_action', 'link', 'item__code', 'get_thumbnail', 'buy_count_3_month', 'quantity', 'sale', 'cost',
              'item__vreserve', 'item__quantity_in_reserve', 'item__quantity_in_stock']
    extra = 1
    ordering = ['item__deckitem__producer', 'id']

    def render_action(self, obj):
        if obj.action is not None:
            action_change_url = reverse('admin:news_new_change', args=[obj.action.id])
            return mark_safe((
                '<div style="background-color: red; padding: 5px 10px;">'
                '<a href="%s" style="color: white;">%s</a>'
                '</div>'
            ) % (action_change_url, obj.action))
        return u'-'
    render_action.short_description = u'Акция'

    def has_delete_permission(self, request, obj=None):
        if request.user.id not in SUPER_ADMIN_IDS and request.user.id not in SQUAD_IDS:  # если не Админы!
            if obj:
                if obj.status in [0, 1, 2]:
                    return True
            return False
        else:
            return True

    def get_readonly_fields(self, request, obj=None):
        if obj:
            if request.user.id not in SUPER_ADMIN_IDS and request.user.id not in SQUAD_IDS:  # если не Админы!
                if obj.status in [4, 6]:  #
                    return ['item', 'link', 'item__code', 'get_thumbnail', 'buy_count_3_month', 'quantity', 'sale', 'cost',
                                'item__vreserve', 'item__quantity_in_reserve', 'item__quantity_in_stock', 'render_action']
        return super(InlineInsideZakazGoodsAdmin, self).get_readonly_fields(request, obj)

reversion.register(InsideZakazGoods)


class InlineZakazStatusLog(TabularInline):
    model = ZakazStatusLog
    extra = 0
    can_delete = False
    readonly_fields = ['status', 'user', 'date']
    fields = ['date', 'status', 'user']
    max_num = 0


class InlineOutsideZakazStatusLog(TabularInline):
    model = OutsideZakazStatusLog
    extra = 0
    can_delete = False
    readonly_fields = ['status', 'user', 'date']
    fields = ['date', 'status', 'user']
    max_num = 0


class InlineAutoZakazStatusLog(TabularInline):
    model = AutoZakazStatusLog
    extra = 0
    can_delete = False
    readonly_fields = ['zakaz']
    fields = ['zakaz']
    max_num = 0


class InlineInsideZakazStatusLog(TabularInline):
    model = InsideZakazStatusLog
    extra = 0
    can_delete = False
    readonly_fields = ['status', 'user', 'date']
    fields = ['date', 'status', 'user']
    max_num = 0


def do_paid_client(modeladmin, request, queryset):
    queryset.update(paid_client=True)


do_paid_client.short_description = u"Клиенты оплатили"


def change_status_2(modeladmin, request, queryset):
    """
    Каждый раз при смене статуса заказа
    создаем "лог изменения статуса заказа"
    """
    for i in queryset:
        this_zakaz = Zakaz.objects.get(id=i.id)
        this_zakaz.status = 2
        this_zakaz.save()

        new_zakazstatuslog = ZakazStatusLog(
            zakaz_id=i.id,
            status=2,
            user=request.user
        )
        new_zakazstatuslog.save()


change_status_2.short_description = u"Доставка согласована?"


def change_status_3(modeladmin, request, queryset):
    """
    Каждый раз при смене статуса заказа
    создаем "лог изменения статуса заказа"
    """
    for i in queryset:
        this_zakaz = Zakaz.objects.get(id=i.id)
        this_zakaz.status = 3
        this_zakaz.save()

        new_zakazstatuslog = ZakazStatusLog(
            zakaz_id=i.id,
            status=3,
            user=request.user
        )
        new_zakazstatuslog.save()


change_status_3.short_description = u"Заказ собран?"


def change_status_4(modeladmin, request, queryset):
    for i in queryset:
        this_zakaz = Zakaz.objects.get(id=i.id)
        this_zakaz.status = 4
        this_zakaz.save()

        new_zakazstatuslog = ZakazStatusLog(
            zakaz_id=i.id,
            status=4,
            user=request.user
        )
        new_zakazstatuslog.save()


change_status_4.short_description = u"Курьер выехал?"


def paid_courier(modeladmin, request, queryset):
    queryset.update(paid_courier=True)


paid_courier.short_description = u"Оплачено куреьру"


def paid_supplier(modeladmin, request, queryset):
    queryset.update(paid_supplier=True)


paid_supplier.short_description = u"Оплачено поставщику"


def export_selected_objects(modeladmin, request, queryset):
    selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
    return HttpResponseRedirect("/manage/collect_pdf/?ids=%s" % ",".join(selected))


export_selected_objects.short_description = u'Распечатать заказы'


def export_onlyclient_selected_objects(modeladmin, request, queryset):
    selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
    return HttpResponseRedirect("/manage/collect_pdf/?onlyclient=1&ids=%s" % ",".join(selected))


export_onlyclient_selected_objects.short_description = u'Распечатать заказы (без складских!)'


def collect_change(modeladmin, request, queryset):
    selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
    return HttpResponseRedirect("/manage/collect_change/?ids=%s" % ",".join(selected))


collect_change.short_description = u'Посчитать сдачу'


def check_orders(modeladmin, request, queryset):
    selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
    return HttpResponseRedirect("/manage/check_orders/?ids=%s" % ",".join(selected))


check_orders.short_description = u'Проверить заказы'


def collect_orders(modeladmin, request, queryset):
    selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
    return HttpResponseRedirect("/manage/collect_orders/?ids=%s" % ",".join(selected))


collect_orders.short_description = u'СБОРКА заказов'


def collect_order_royal(modeladmin, request, queryset):
    selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
    return HttpResponseRedirect("/manage/collect_inside_orders/1/?ids=%s" % ",".join(selected))


collect_order_royal.short_description = u'Собрать Роял'


def collect_order_avrora(modeladmin, request, queryset):
    selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
    return HttpResponseRedirect("/manage/collect_inside_orders/2/?ids=%s" % ",".join(selected))


collect_order_avrora.short_description = u'Собрать Аврору'


def collect_order_zooirkutsk(modeladmin, request, queryset):
    selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
    return HttpResponseRedirect("/manage/collect_inside_orders/3/?ids=%s" % ",".join(selected))


collect_order_zooirkutsk.short_description = u'Собрать Зооиркутск'


def collect_order_purina(modeladmin, request, queryset):
    selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
    return HttpResponseRedirect("/manage/collect_inside_orders/100/?ids=%s" % ",".join(selected))


collect_order_purina.short_description = u'Собрать ИЛС Пурину'


def collect_order_valta(modeladmin, request, queryset):
    selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
    return HttpResponseRedirect("/manage/collect_inside_orders/9/?ids=%s" % ",".join(selected))


collect_order_valta.short_description = u'Собрать Валту'


def collect_order_petcontinent(modeladmin, request, queryset):
    selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
    return HttpResponseRedirect("/manage/collect_inside_orders/12/?ids=%s" % ",".join(selected))


collect_order_petcontinent.short_description = u'Собрать ПетКонтинент'


def collect_order_perfoodtraid(modeladmin, request, queryset):
    selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
    return HttpResponseRedirect("/manage/collect_inside_orders/18/?ids=%s" % ",".join(selected))
collect_order_perfoodtraid.short_description = u'Собрать Петфудтрейд'


def collect_order_zoograd(modeladmin, request, queryset):
    selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
    return HttpResponseRedirect("/manage/collect_inside_orders/102/?ids=%s" % ",".join(selected))
collect_order_zoograd.short_description = u'Собрать Зооград'


def collect_order_ivanko(modeladmin, request, queryset):
    selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
    return HttpResponseRedirect("/manage/collect_inside_orders/11/?ids=%s" % ",".join(selected))
collect_order_ivanko.short_description = u'-- Собрать ИВАНКО'


def collect_order_zebra(modeladmin, request, queryset):
    selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
    return HttpResponseRedirect("/manage/collect_inside_orders/13/?ids=%s" % ",".join(selected))
collect_order_zebra.short_description = u'-- Собрать Животный мир'


def collect_order_zebra(modeladmin, request, queryset):
    selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
    return HttpResponseRedirect("/manage/collect_inside_orders/16/?ids=%s" % ",".join(selected))
collect_order_zebra.short_description = u'-- Собрать Вэлкорм'


def collect_order_zebra(modeladmin, request, queryset):
    selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
    return HttpResponseRedirect("/manage/collect_inside_orders/107/?ids=%s" % ",".join(selected))
collect_order_zebra.short_description = u'-- Собрать Добрый дом'


def collect_order_zebra(modeladmin, request, queryset):
    selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
    return HttpResponseRedirect("/manage/collect_inside_orders/4/?ids=%s" % ",".join(selected))
collect_order_zebra.short_description = u'-- Собрать Владивосток 2000'


class ShowDateDelivered(SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = u'Дата доставки'

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'delivered_date'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return (
            ('today', u'Сегодня'),
            ('tomorrow', u'Завтра'),
            ('yesterday', u'Вчера'),
        )

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # Compare the requested value (either '80s' or 'other')
        # to decide how to filter the queryset.
        now = timezone.now()
        # When time zone support is enabled, convert "now" to the user's time
        # zone so Django's definition of "Today" matches what the user expects.
        if timezone.is_aware(now):
            now = timezone.localtime(now)

        today = now.date()
        today_minus_1 = today - datetime.timedelta(days=1)
        tomorrow = today + datetime.timedelta(days=1)
        tomorrow_plus_1 = today + datetime.timedelta(days=2)

        if self.value() == 'today':
            return queryset.filter(real_desired_time__gte=today, real_desired_time__lt=tomorrow)
        if self.value() == 'tomorrow':
            return queryset.filter(real_desired_time__gte=tomorrow, real_desired_time__lt=tomorrow_plus_1)
        if self.value() == 'yesterday':
            return queryset.filter(real_desired_time__gte=today_minus_1, real_desired_time__lt=today)


STATUS_FROM_31 = (
    (3, u'Заказ собран'),
    (31, u'Заказ у курьера'),
    (4, u'Курьер выехал'),
    (5, u'Заказ доставлен'),
    (7, u'Отказ от заказа'),
)

STATUS_FROM_4 = (
    (31, u'Заказ у курьера'),
    (4, u'Курьер выехал'),
    (5, u'Заказ доставлен'),
    (7, u'Отказ от заказа'),
)
STATUS_FROM_5 = (
    (5, u'Заказ доставлен'),
)
STATUS_FROM_6 = (
    (6, u'Завершен'),
)
STATUS_FROM_7 = (
    (7, u'Отказ от заказа'),
)
STATUS_FROM_10 = (
    (10, u'Отменен'),
)

STATUS_FROM_OTHER = (
    (0, u'Новый'),
    (11, u'Обрабатывается'),
    (1, u'Не удалось дозвониться'),
    (8, u'Требуется перезвонить'),
    (81, u'Ждем звонка от клиента'),
    (82, u'Ждем оплаты'),
    (2, u'Доставка согласована'),
    (10, u'Отменен'),
)

"""
(0, u'Новый'),
(1, u'Под заказ'),
(2, u'Доставка согласована'),
(4, u'Заказ получен'),
(6, u'Завершен')
"""
INSIDE_STATUS_FROM_OTHER = (
    (0, u'Новый'),
    (1, u'Под заказ'),
    (2, u'Доставка согласована'),
    (4, u'Заказ получен'),
)

MOVEMENT_STATUS_FROM_OTHER = (
    (0, u'Новое'),
    (3, u'Перемещение собрано'),

    (31, u'Перемещение у курьера'),
    (4, u'Курьер выехал'),
    (5, u'Перемещение доставлено'),
)

SUPER_ADMIN_IDS = [1, 142, 3958, 3959]
SQUAD_IDS = [5305, ]


class StatusForm31(forms.ModelForm):
    class Meta:
        model = Zakaz
        fields = ['status']

    def __init__(self, *args, **kwargs):
        super(StatusForm31, self).__init__(*args, **kwargs)
        if self.fields.get('status'):
            self.fields['status'].widget = forms.Select(choices=STATUS_FROM_31)


class StatusForm4(forms.ModelForm):
    class Meta:
        model = Zakaz
        fields = ['status']

    def __init__(self, *args, **kwargs):
        super(StatusForm4, self).__init__(*args, **kwargs)
        if self.fields.get('status'):
            self.fields['status'].widget = forms.Select(choices=STATUS_FROM_4)


class StatusForm5(forms.ModelForm):
    class Meta:
        model = Zakaz
        fields = ['status']

    def __init__(self, *args, **kwargs):
        super(StatusForm5, self).__init__(*args, **kwargs)
        if self.fields.get('status'):
            self.fields['status'].widget = forms.Select(choices=STATUS_FROM_5)


class StatusForm6(forms.ModelForm):
    class Meta:
        model = Zakaz
        fields = ['status']

    def __init__(self, *args, **kwargs):
        super(StatusForm6, self).__init__(*args, **kwargs)
        if self.fields.get('status'):
            self.fields['status'].widget = forms.Select(choices=STATUS_FROM_6)


class StatusForm7(forms.ModelForm):
    class Meta:
        model = Zakaz
        fields = ['status']

    def __init__(self, *args, **kwargs):
        super(StatusForm7, self).__init__(*args, **kwargs)
        if self.fields.get('status'):
            self.fields['status'].widget = forms.Select(choices=STATUS_FROM_7)


class StatusForm10(forms.ModelForm):
    class Meta:
        model = Zakaz
        fields = ['status']

    def __init__(self, *args, **kwargs):
        super(StatusForm10, self).__init__(*args, **kwargs)
        if self.fields.get('status'):
            self.fields['status'].widget = forms.Select(choices=STATUS_FROM_10)


class StatusFormOther(forms.ModelForm):
    class Meta:
        model = Zakaz
        fields = ['status']

    def __init__(self, *args, **kwargs):
        super(StatusFormOther, self).__init__(*args, **kwargs)
        if self.fields.get('status'):
            self.fields['status'].widget = forms.Select(choices=STATUS_FROM_OTHER)


class StatusFormAdmin(forms.ModelForm):
    class Meta:
        model = Zakaz
        fields = ['status']

    def __init__(self, *args, **kwargs):
        super(StatusFormAdmin, self).__init__(*args, **kwargs)
        if self.fields.get('status'):
            self.fields['status'].widget = forms.Select(choices=ORDER_STATUS)


class InsideStatusFormOther(forms.ModelForm):
    class Meta:
        model = InsideZakaz
        fields = ['status']

    def __init__(self, *args, **kwargs):
        super(InsideStatusFormOther, self).__init__(*args, **kwargs)
        if self.fields.get('status'):
            self.fields['status'].widget = forms.Select(choices=INSIDE_STATUS_FROM_OTHER)


class InsideStatusFormAdmin(forms.ModelForm):
    class Meta:
        model = InsideZakaz
        fields = ['status']

    def __init__(self, *args, **kwargs):
        super(InsideStatusFormAdmin, self).__init__(*args, **kwargs)
        if self.fields.get('status'):
            self.fields['status'].widget = forms.Select(choices=INSIDE_ORDER_STATUS)


class MovementOfGoodsFormOther(forms.ModelForm):
    class Meta:
        model = MovementOfGoods
        fields = ['status']

    def __init__(self, *args, **kwargs):
        super(MovementOfGoodsFormOther, self).__init__(*args, **kwargs)
        if self.fields.get('status'):
            self.fields['status'].widget = forms.Select(choices=MOVEMENT_STATUS_FROM_OTHER)


class MovementOfGoodsFormAdmin(forms.ModelForm):
    class Meta:
        model = MovementOfGoods
        fields = ['status']

    def __init__(self, *args, **kwargs):
        super(MovementOfGoodsFormAdmin, self).__init__(*args, **kwargs)
        if self.fields.get('status'):
            self.fields['status'].widget = forms.Select(choices=MOVEMENTOFGOODSCHOICES)


class ShowZakazWithoutEnd(SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = u'Без завершенных'

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'without_end'

    def lookups(self, request, model_admin):
        return (
            (None, u'Без завершенных'),
            ('all', u'Все'),
        )

    def choices(self, cl):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == lookup,
                'query_string': cl.get_query_string({
                    self.parameter_name: lookup,
                }, []),
                'display': title,
            }

    def queryset(self, request, queryset):
        if self.value() == None:
            return queryset.exclude(status__in=[6, 7, 10])


class PaymentInline(TabularInline):
    model = Payment
    max_num = 0
    fields = ['uid', 'amount', 'status', 'created', 'updated', 'error_code', 'error_message']
    readonly_fields = ['uid', 'amount', 'status', 'created', 'updated', 'error_code', 'error_message']
    can_delete = False


class ZakazAdmin(VersionAdmin):
    list_display = ['id', 'get_presale_count', 'get_short_date', 'status', 'get_f_status', 'owner_name',
                    'get_short_date_delivery', 'get_short_courier', 'get_short_paytype', 'k_oplate',
                    'paid_client', 'cash_go_to_kassa']
    list_filter = [ShowDateDelivered, 'courier', ShowZakazWithoutEnd, 'status', 'manager', 'cashier', 'warehouse', 'date', 'paid_client', 'cash_go_to_kassa',
                   'paid_courier', 'paytype', 'is_refund', 'f_taxtype']
    search_fields = ['owner__username', 'owner__first_name', 'owner__last_name', 'id', 'phone', 'fio', 'street']
    readonly_fields = ['date', 'date_end', 'cost', 'revenue', 'k_oplate', 'autocreate', 'get_order_count_inner',
                       'user_description', 'get_presale_count_inner', 'cash', 'non_cash', 'warehouse', 'cashier']

    list_per_page = 250
    date_hierarchy = 'date_end'
    raw_id_fields = ['owner']
    fieldsets = (
        (u'', {'fields': ('owner', ('get_order_count_inner', 'user_description'),
                          'get_presale_count_inner',
                          ('status', 'paid_client', 'cash_go_to_kassa', 'paid_courier'),
                          ('summ', 'sale_koef', 'k_oplate'), 'manager', 'extra', 'cashier', 'warehouse')}),
        (u'Даты и прочее', {'classes': ('collapse',), 'fields': (('date', 'date_end'), 'autocreate', 'target_sended')}),
        (u'Контакты', {'fields': (('phone', 'fio'), ('city', 'street'), ('dom', 'appart'), 'district', 'description')}),
        (u'Оплата/Доставка', {'fields': (
            ('desired_time', 'real_desired_time'),
            'courier',
            ('need_call', 'inbox', 'morning_delivery'),
            ('paytype', 'dostavkatype', 'dostavka'),
            'pickup_warehouse',
            ('cash', 'non_cash')
        )}),
        (u'Данные фискализации',
         {'classes': ('collapse',), 'fields': ('f_check', 'f_state', 'f_response', 'f_id', 'f_fiscal_data', 'f_print')})
    )
    save_on_top = True

    inlines = [InlineZakazGoodsAdmin, InlineZakazStatusLog, PaymentInline]
    # actions = [collect_change, export_selected_objects, check_orders, paid_courier, do_paid_client, change_status_2, change_status_3, change_status_4]
    actions = [collect_change, export_onlyclient_selected_objects, export_selected_objects, check_orders, collect_orders, change_status_3, collect_order_royal,
               collect_order_avrora, collect_order_zooirkutsk, collect_order_purina, collect_order_valta,
               collect_order_petcontinent, collect_order_perfoodtraid, collect_order_zoograd, collect_order_ivanko, collect_order_zebra]

    class Media:
        css = {
            "all": ("kostochka38/css/filter.css", 'kostochka38/css/admin-chosen.css')
        }
        js = ("kostochka38/js/core-admin-order.js", 'kostochka38/js/reloader.js')

    def get_form(self, request, obj=None, **kwargs):
        if request.user.id not in SUPER_ADMIN_IDS and request.user.id not in SQUAD_IDS:  # если не Админы!
            if obj:
                """
                (0, u'Новый'),
                (11, u'Обрабатывается'),
                (1, u'Не удалось дозвониться'),
                (8, u'Требуется перезвонить'),

                (81, u'Ждем звонка от клиента'),
                (82, u'Ждем оплаты'),

                (2, u'Доставка согласована'),
                (3, u'Заказ собран'),

                (31, u'Заказ у курьера'),

                (4, u'Курьер выехал'),
                (5, u'Заказ доставлен'),
                (6, u'Завершен'),
                (7, u'Отказ от заказа'),
                (10, u'Отменен'),
                """
                if obj.status == 31 or obj.status == 3:  # Заказ собран , Заказ у курьера
                    self.form = StatusForm31
                    """
                    (3, u'Заказ собран'),
                    (31, u'Заказ у курьера'),
                    (4, u'Курьер выехал'),
                    (5, u'Заказ доставлен'),
                    (7, u'Отказ от заказа'),
                    """
                elif obj.status == 4:  # Курьер выехал
                    self.form = StatusForm4
                    """
                    (31, u'Заказ у курьера'),
                    (4, u'Курьер выехал'),
                    (5, u'Заказ доставлен'),
                    (7, u'Отказ от заказа'),
                    """
                else:
                    self.form = StatusFormOther
                    """
                    (0, u'Новый'),
                    (11, u'Обрабатывается'),
                    (1, u'Не удалось дозвониться'),
                    (8, u'Требуется перезвонить'),
                    (81, u'Ждем звонка от клиента'),
                    (82, u'Ждем оплаты'),
                    (2, u'Доставка согласована'),
                    (10, u'Отменен'),
                    """
            else:
                self.form = StatusFormOther
        else:
            self.form = StatusFormAdmin
        return super(ZakazAdmin, self).get_form(request, obj, **kwargs)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            if request.user.id not in SUPER_ADMIN_IDS: # and request.user.id not in SQUAD_IDS:  # если не Админы!
                # old_obj = Zakaz.objects.get(id=obj.id)
                if obj.status in [3, 31, 4]:
                    """
                    (0, u'Новый'),
                    (11, u'Обрабатывается'),
                    (1, u'Не удалось дозвониться'),
                    (8, u'Требуется перезвонить'),
                    (81, u'Ждем звонка от клиента'),
                    (82, u'Ждем оплаты'),
                    (2, u'Доставка согласована'),
                    """
                    return ['date', 'date_end', 'cost', 'revenue', 'k_oplate', 'autocreate', 'get_order_count_inner',
                            'user_description', 'get_presale_count_inner', 'cash', 'non_cash', 'warehouse', 'cashier',
                            'paid_client', 'cash_go_to_kassa', 'paid_courier', 'cash', 'non_cash', 'warehouse',
                            'cashier', 'pickup_warehouse'
                            ]

                if obj.status in [3, 31, 4]:  #
                    """
                    (3, u'Заказ собран'),
                    (31, u'Заказ у курьера'),
                    (4, u'Курьер выехал'),
                    (5, u'Заказ доставлен'),
                    (6, u'Завершен'),
                    (7, u'Отказ от заказа'),
                    (10, u'Отменен'),
                    """
                    return ['date', 'date_end', 'cost', 'revenue', 'k_oplate', 'autocreate', 'get_order_count_inner',
                            'user_description', 'owner', 'summ', 'paid_client', 'cash_go_to_kassa', 'paid_courier',
                            'description', 'paytype', 'sale_koef', 'courier', 'manager', 'dostavkatype', 'dostavka',
                            'get_presale_count_inner', 'cash', 'non_cash', 'warehouse', 'cashier', 'pickup_warehouse']

                if obj.status in [5, 6, 7, 10]:
                    return ['date', 'date_end', 'status', 'cost', 'revenue', 'k_oplate', 'autocreate', 'get_order_count_inner',
                            'user_description', 'owner', 'summ', 'paid_client', 'cash_go_to_kassa',
                            'paid_courier', 'description', 'paytype', 'sale_koef', 'courier',
                            'manager', 'dostavkatype', 'dostavka', 'desired_time', 'real_desired_time',
                            'extra', 'phone', 'fio', 'city', 'street', 'dom', 'appart', 'district', 'need_call',
                            'get_presale_count_inner', 'f_state', 'f_id', 'f_fiscal_data', 'f_print', 'f_check',
                            'inbox', 'cash', 'non_cash', 'warehouse', 'cashier', 'pickup_warehouse', 'f_response']
        return super(ZakazAdmin, self).get_readonly_fields(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj:
            if request.user.id in SUPER_ADMIN_IDS:  # Если Админы
                return True
        return False

    def save_model(self, request, obj, form, change):
        if obj.id:
            old_order = Zakaz.objects.get(id=obj.id)

            if (old_order.cash_go_to_kassa != obj.cash_go_to_kassa) and obj.cash_go_to_kassa:
                """
                если поставили галку "бабло в кассу",
                то создадим движние средств за оплату
                этого заказа
                """
                if not Expense.objects.filter(description=u'заказ №' + str(obj.id)) and not Expense.objects.filter(description=u'заказ № %s, %s' % (str(obj.id), obj.owner.name_plat)):
                    summ_so_skidkoi = obj.k_oplate()
                    paytype = 0
                    summ = 0
                    description = ''
                    if obj.paytype == 1:
                        """
                        оплата картой через терминал
                        """
                        summ = ceil(summ_so_skidkoi * settings.BANK_COMMISSION)
                        description = u'заказ №%s' % obj.id
                        paytype = 1

                    elif obj.paytype == 5:
                        """
                        оплата на расчетынй счет
                        """
                        summ = summ_so_skidkoi
                        description = u'заказ №%s, %s' % (obj.id, obj.owner.name_plat)
                        paytype = 1

                    elif obj.paytype == 4:
                        """
                        онлайн оплата
                        """
                        summ = summ_so_skidkoi * settings.BANK_COMMISSION_ONLINE
                        description = u'заказ №%s' % obj.id
                        paytype = 1

                    elif obj.paytype == 3 or obj.paytype == 0:
                        """
                        оплата наличными или переводом на карту
                        """
                        summ = int(summ_so_skidkoi)
                        description = u'заказ №%s' % str(obj.id)
                        paytype = 0

                    new_expense = Expense(
                        type=1,
                        type_of_currency=paytype,
                        value=summ,
                        description=description,
                        expensetype_id=1
                    )
                    new_expense.save()

            if old_order.status != obj.status:
                """
                Каждый раз при смене статуса заказа
                создаем "лог изменения статуса заказа"
                """
                new_zakazstatuslog = ZakazStatusLog(
                    zakaz=old_order,
                    status=obj.status,
                    user=request.user
                )
                new_zakazstatuslog.save()

            if not obj.summ:
                obj.summ = old_order.summ
        obj.save()


class AutoZakazAdmin(VersionAdmin):
    list_display = ['id', 'repear_count', 'last_order', 'owner_name']
    list_filter = ['last_order']
    search_fields = ['owner__username', 'owner__first_name', 'owner__last_name', 'id']
    readonly_fields = ['create_date', 'zakaz', 'repear_count', 'last_order']
    list_per_page = 100
    date_hierarchy = 'create_date'
    raw_id_fields = ['owner',]
    fieldsets = (
        (u'', {'fields': ('owner', 'zakaz', 'extra')}),
        (u'Даты', {'fields': (('create_date', 'last_order'), 'repeat_period', 'repear_count')})
    )
    save_on_top = True
    inlines = [InlineAutoZakazGoodsAdmin, InlineAutoZakazStatusLog]

    class Media:
        css = {
            "all": ("kostochka38/css/filter.css", 'kostochka38/css/admin-chosen.css')
        }
        js = ("kostochka38/js/core-admin-order.js", 'kostochka38/js/reloader.js')


class OutsideZakazAdmin(VersionAdmin):
    list_display = ['zakaz_id', 'date', 'status', 'desired_time', 'real_desired_time', 'district', 'courier_name',
                    'paid_courier', 'paytype', 'paid_client']
    list_filter = ['store', 'status', 'courier', 'real_desired_time', 'date', 'paid_client', 'paid_courier']
    readonly_fields = ['date', 'date_end']
    list_per_page = 25
    date_hierarchy = 'date_end'
    fieldsets = (
        (u'', {'fields': (('store', 'zakaz_id'), ('status', 'paid_client'), 'paid_courier', ('summ'), 'extra')}),
        (u'Даты', {'classes': ('collapse',), 'fields': (('date', 'date_end'),)}),
        (u'Контакты', {'fields': (('phone', 'fio'), ('city', 'street'), ('dom', 'appart'), 'district')}),
        (u'Оплата/Доставка',
         {'fields': (('desired_time', 'real_desired_time'), 'courier', 'need_call', ('paytype'), ('dostavka'))})
    )
    save_on_top = True
    save_as = True
    inlines = [InlineOutsideZakazStatusLog]

    class Media:
        css = {
            "all": ("kostochka38/css/filter.css", 'kostochka38/css/admin-chosen.css')
        }
        js = ("kostochka38/js/core-admin-order.js",)

    def save_model(self, request, obj, form, change):
        if obj.id:
            old_order = OutsideZakaz.objects.get(id=obj.id)
            if old_order.status != obj.status:
                new_zakazstatuslog = OutsideZakazStatusLog(
                    zakaz=old_order,
                    status=obj.status,
                    user=request.user
                )
                new_zakazstatuslog.save()
        obj.save()


class InsideZakazAdmin(VersionAdmin):
    list_display = ['id', 'status', 'segment_new', 'paid_supplier', 'date_pickup', 'pickup', 'cost', 'getpdflinkinside',
                    'courier', 'paid_courier', ]
    list_filter = ['segment_new', 'courier', 'status', 'manager', 'date', 'paid_supplier', 'paid_courier', 'pickup', 'warehouse']
    readonly_fields = ['date', 'date_end']
    list_per_page = 50
    date_hierarchy = 'date_end'
    fieldsets = (
        (u'', {'fields': ('status', 'manager', 'warehouse', ('segment_new', 'paid_supplier'), 'cost', ('date', 'date_end'), 'extra')}),
        (u'Лог создания', {'classes': ('collapse', 'close'), 'fields': ('details',)}),
        (u'Параметры', {'fields': ('sale_koef', ('pickup', 'date_pickup'), ('courier', 'paid_courier'))})
    )
    actions = [paid_courier, paid_supplier]
    save_on_top = True
    inlines = [InlineInsideZakazGoodsAdmin, InlineInsideZakazStatusLog]
    ordering = ['status', '-date_pickup', '-id']

    def get_readonly_fields(self, request, obj=None):
        if obj:
            if request.user.id not in SUPER_ADMIN_IDS and request.user.id not in SQUAD_IDS:  # если не Админы!
                if obj.status in [4, 6]:  #
                    return ['status', 'manager', 'warehouse', 'segment_new', 'paid_supplier', 'cost', 'date',
                            'date_end', 'extra', 'sale_koef', 'pickup', 'date_pickup', 'courier', 'paid_courier']
        return super(InsideZakazAdmin, self).get_readonly_fields(request, obj)

    def has_delete_permission(self, request, obj=None):
        if request.user.id not in SUPER_ADMIN_IDS and request.user.id not in SQUAD_IDS:  # если не Админы!
            if obj:
                if obj.status in [0, 1, 2]:
                    return True
            return False
        else:
            return True

    def get_form(self, request, obj=None, **kwargs):
        if request.user.id not in SUPER_ADMIN_IDS and request.user.id not in SQUAD_IDS:  # если не Админы!
            self.form = InsideStatusFormOther
        else:
            self.form = InsideStatusFormAdmin
        return super(InsideZakazAdmin, self).get_form(request, obj, **kwargs)

    def get_actions(self, request):
        if request.user.id not in SUPER_ADMIN_IDS:  # если не Админы!
            return []
        else:
            return super(VersionAdmin, self).get_actions(request)

    class Media:
        css = {
            "all": ("kostochka38/css/filter.css", 'kostochka38/css/admin-chosen.css')
        }
        js = ("kostochka38/js/core-admin-order.js", 'kostochka38/js/inside_reloader.js')

    def save_model(self, request, obj, form, change):
        if obj.id:
            old_order = InsideZakaz.objects.get(id=obj.id)
            if old_order.status != obj.status:
                new_zakazstatuslog = InsideZakazStatusLog(
                    zakaz=old_order,
                    status=obj.status,
                    user=request.user
                )
                new_zakazstatuslog.save()
        obj.save()


# конец ЗАКАЗЫ


class ParserLogAdmin(admin.ModelAdmin):
    list_display = ['date', 'filename', 'segment_new']
    list_filter = ['segment_new', 'date']


class CourierAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'create_date']
    ordering = ['name', ]


class ExpenseAdmin(VersionAdmin):
    list_display = ['type', 'type_of_currency', 'date', 'value', 'source', 'expensetype', 'description']
    list_filter = ['type', 'expensetype', 'source', 'type_of_currency', 'date']
    search_fields = ['description']
    date_hierarchy = 'date'

    class Media:
        css = {
            "all": ('kostochka38/css/admin-chosen.css',)
        }

    def get_readonly_fields(self, request, obj=None):
        if obj:
            if obj.expensetype.id != 6 and request.user.id != 1 and request.user.id != 142:  # если не "временное" движение средств
                return self.readonly_fields + (
                    'type', 'type_of_currency', 'expensetype', 'value', 'date', 'source', 'description')
        return self.readonly_fields

    def has_delete_permission(self, request, obj=None):
        if obj:
            if obj.expensetype.id == 6 or request.user.id == 1 or request.user.id != 142:  # если "временное" движение средств
                return True
        return False


class VendorAccountAdmin(VersionAdmin):
    list_display = ['type', 'type_of_currency', 'date', 'value', 'segment_new', 'description', 'balans']
    list_filter = ['type', 'segment_new', 'type_of_currency', 'date']
    date_hierarchy = 'date'

    class Media:
        css = {
            "all": ('kostochka38/css/admin-chosen.css',)
        }


class SaleTableAdmin(VersionAdmin):
    list_display = ['segment_new', 'value', 'date', 'value_for_revenue']
    list_filter = ['segment_new']


class ExpenseTypeAdmin(VersionAdmin):
    list_display = ['title', 'id', 'type']


class ZakazBonusAdmin(VersionAdmin):
    list_display = ['title', 'active', 'exp_date']
    list_filter = ['active']
    ordering = ['-id']


class LogingCourierFinishAdmin(admin.ModelAdmin):
    list_display = ['date', 'get_thumbnail', 'courier']
    list_filter = ['courier', 'date']
    date_hierarchy = 'date'
    ordering = ['-date']
    readonly_fields = ['textlog', 'image', 'get_thumbnail']


class FilterDescriptionAdmin(admin.ModelAdmin):
    list_display = ['id', 'link_title', 'head_title', 'section', 'title', 'footer_view']
    list_filter = ['section']
    list_editable = ['link_title', 'head_title', 'title', 'footer_view']

    fieldsets = (
        (u'', {'classes': ('wide',), 'fields': ('filter', 'section')}),
        (u'', {'classes': (),
               'fields': ('title', 'head_title', 'meta_descroption', 'link_title', 'link_url', 'footer_view')}),
    )


class PriceParserAdmin(admin.ModelAdmin):
    list_display = ['id', 'segment_new', 'date', 'status', 'price_file']
    list_filter = ['segment_new', 'status']
    fieldsets = (
        (u'', {'fields': ('segment_new', 'price_file', 'extra', 'status')}),
        (u'Ошибки', {'classes': ('collapse', 'open'), 'fields': ('get_result_error',)}),
        (u'Нашелся, цена изменилась', {'classes': ('collapse', 'open'), 'fields': ('get_result_1',)}),
        (u'Новинки', {'classes': ('collapse', 'open'), 'fields': ('get_result_2',)}),
        (u'Потерянный (есть в базе, нет в прайсе)', {'classes': ('collapse', 'close'), 'fields': ('get_result_3',)}),
        (u'Нашелся, НО НЕ АКТИВНЫЙ', {'classes': ('collapse', 'close'), 'fields': ('get_result_4',)}),
        (u'Нашелся, цена не изменилась', {'classes': ('collapse', 'close'), 'fields': ('get_result_5',)})
    )

    readonly_fields = ['status', 'get_result_error', 'get_result_1', 'get_result_2', 'get_result_3', 'get_result_4',
                       'get_result_5']


class InlineGoodsInMovement(TabularInline):
    model = GoodsInMovement
    raw_id_fields = ['item']
    readonly_fields = ['get_thumbnail', 'item__quantity_in_reserve', 'item__quantity_in_stock',
                       'buy_count_3_month', 'item__vreserve', 'get_segment']
    fields = ['item', 'get_segment', 'get_thumbnail', 'buy_count_3_month', 'quantity',
              'item__vreserve', 'item__quantity_in_reserve', 'item__quantity_in_stock']
    extra = 0

    def get_readonly_fields(self, request, obj=None):
        if obj:
            if request.user.id not in SUPER_ADMIN_IDS and request.user.id not in SQUAD_IDS:  # если не Админы!
                if obj.status in [4, 5, 6, 10]:
                    """
                    (0, u'Новое'),
                    (3, u'Перемещение собрано'),

                    (31, u'Перемещение у курьера'),
                    (4, u'Курьер выехал'),
                    (5, u'Перемещение доставлено'),
                    (6, u'Завершено'),
                    (10, u'Отменено'),
                    """
                    return ['item', 'get_segment', 'get_thumbnail', 'buy_count_3_month', 'quantity',
                                    'item__vreserve', 'item__quantity_in_reserve', 'item__quantity_in_stock']
        # return self.readonly_fields
        return super(InlineGoodsInMovement, self).get_readonly_fields(request, obj)

    def has_delete_permission(self, request, obj=None):
        if request.user.id not in SUPER_ADMIN_IDS and request.user.id not in SQUAD_IDS:  # если не Админы!
            if obj:
                if obj.status in [4, 5, 6, 10]:
                    return False
            return True
        else:
            return True

class InlineMovementStatusLog(TabularInline):
    model = MovementStatusLog
    readonly_fields = ['status', 'user', 'date']
    extra = 0
    can_delete = False
    fields = ['date', 'status', 'user']
    max_num = 0


class WareHouseAdmin(VersionAdmin):
    raw_id_fields = ["default_customer"]

    fieldsets = (
        (None, {
            'fields': ('name', 'full_name', 'address', 'phone', 'type', 'default_customer')
        }),
        ('Понедельник', {
            'fields': ('mon_start', 'mon_end')
        }),
        ('Вторник', {
            'fields': ('tue_start', 'tue_end')
        }),
        ('Среда', {
            'fields': ('wed_start', 'wed_end')
        }),
        ('Четверг', {
            'fields': ('thu_start', 'thu_end')
        }),
        ('Пятница', {
            'fields': ('fri_start', 'fri_end')
        }),
        ('Суббота', {
            'fields': ('sat_start', 'sat_end')
        }),
        ('Воскоресенье', {
            'fields': ('sun_start', 'sun_end')
        })
    )


def collect_movement(modeladmin, request, queryset):
    selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
    return HttpResponseRedirect("/manage/collect_movement/?ids=%s" % ",".join(selected))
collect_movement.short_description = u'Заказать товар из перемещений'


class MovementOfGoodsAdmin(VersionAdmin):
    date_hierarchy = 'date_end'
    save_on_top = True
    readonly_fields = ['creation_date', 'date_end']
    inlines = [InlineGoodsInMovement, InlineMovementStatusLog]
    list_display = ['id', 'status', 'warehouse_donor', 'warehouse_recieving', 'delivery_date', 'courier', 'courier_paid', 'ordered']
    list_filter = ['status', 'warehouse_donor', 'warehouse_recieving', 'delivery_date', 'courier', 'ordered']
    fieldsets = (
        (u'', {'fields': ('courier_paid', 'delivery_date', 'date_end', 'creation_date', 'status', 'courier',
                          'warehouse_donor', 'warehouse_recieving', 'extra', 'ordered')}),
        (u'Лог создания', {'classes': ('collapse', 'close'), 'fields': ('details',)})
    )

    actions = [collect_movement]

    class Media:
        css = {
            "all": ("kostochka38/css/filter.css", 'kostochka38/css/admin-chosen.css')
        }
        js = ('kostochka38/js/movement_reloader.js', )

    def get_form(self, request, obj=None, **kwargs):
        if request.user.id not in SUPER_ADMIN_IDS and request.user.id not in SQUAD_IDS:  # если не Админы!
            self.form = MovementOfGoodsFormOther
        else:
            self.form = MovementOfGoodsFormAdmin
        return super(MovementOfGoodsAdmin, self).get_form(request, obj, **kwargs)

    def has_delete_permission(self, request, obj=None):
        if request.user.id not in SUPER_ADMIN_IDS and request.user.id not in SQUAD_IDS:  # если не Админы!
            if obj:
                if obj.status in [0, 1, 2]:
                    return True
            return False
        else:
            return True

    def get_readonly_fields(self, request, obj=None):
        if not obj:
            return super(VersionAdmin, self).get_readonly_fields(request, obj)

        if request.user.id not in SUPER_ADMIN_IDS and request.user.id not in SQUAD_IDS:
            if obj.status in [31, 3, 4, 5]:
                return ['courier_paid', 'delivery_date', 'creation_date', 'courier', 'warehouse_donor',
                        'warehouse_recieving', 'date_end']
            if obj.status in [31, 3, 4, 5, 6, 10]:
                return ['courier_paid', 'delivery_date', 'status', 'creation_date', 'courier', 'warehouse_donor',
                        'warehouse_recieving', 'date_end', 'extra', 'ordered']
        return super(VersionAdmin, self).get_readonly_fields(request, obj)

    def save_model(self, request, obj, form, change):
        obj.save(request)


def PrintPriceTagAction(warehouse):

    def print_price_tags_for_warehouse(modeladmin, request, queryset):
        queryset = queryset.filter(warehouse=warehouse)
        item_ids = ','.join([str(item_id) for item_id in queryset.values_list('item__id', flat=True)])
        url = '{}?item_ids={}'.format(reverse('print_price_tag_view'), item_ids)
        queryset.update(is_processed=True)
        return redirect(url)

    print_price_tags_for_warehouse.short_description = (
        u'Распечатать ценники для магазина "{0}"'.format(warehouse.name)
    )
    print_price_tags_for_warehouse.__name__ = (
        'print_price_tags_for_warehouse_{0}'.format(warehouse.id)
    )

    return print_price_tags_for_warehouse


class IsProcessedFilter(SimpleListFilter):
    
    title = u'Обработано'
    parameter_name = 'is_processed__exact'

    def lookups(self, request, model_admin):
        return (
            ('all', u'Все'),
            ('true', u'Да')
        )

    def choices(self, changelist):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == force_str(lookup),
                'query_string': changelist.get_query_string({self.parameter_name: lookup}, []),
                'display': title,
            }
        yield {
            'selected': self.value() is None,
            'query_string': changelist.get_query_string({}, [self.parameter_name]),
            'display': 'Нет',
        }

    def queryset(self, request, queryset):
        value = self.value()
        if value == 'all':
            return queryset
        elif value == 'true':
            return queryset.filter(is_processed__exact=True)
        return queryset.filter(is_processed__exact=False)


class ItemPriceChangeAdmin(VersionAdmin):

    raw_id_fields = ('item',)
    
    list_display = ('item', 'warehouse', 'date', 'is_processed')

    list_filter = (IsProcessedFilter, 'warehouse', 'date')

    readonly_fields = ('is_processed',)

    def get_actions(self, request):
        actions = super(VersionAdmin, self).get_actions(request)
        for warehouse in WareHouse.objects.all():
            action = PrintPriceTagAction(warehouse)
            actions[action.__name__] = (
                action,
                action.__name__,
                action.short_description
            )
        return actions


def flip_is_shipped_state(modeladmin, request, queryset):
    queryset.update(is_shipped=Q(is_shipped=False))
flip_is_shipped_state.short_description = u'Отгрузить/вернуть обратно'


class ZakazGoodsBaskedOfGoodsProxyAdmin(VersionAdmin):

    search_fields = [
        'item__deckitem__title',
        'item__deckitem__title_en',
        'item__id',
        'item__deckitem__id',
        'item__article',
        'item__code'
    ]

    list_filter = [
        'is_shipped',
        # ShowItemsInReserve,
        'item__temporarily_unavailable',
        'item__active',
        'item__deckitem__tag',
        'item__heavy'
    ]

    list_display = [
        'item__title',
        'order_link',
        'item__get_photo_thumbnail',
        'item__quantity_in_reserve',
        'item__quantity_in_stock',
        'is_shipped'
    ]

    actions = [flip_is_shipped_state]

    class Media:
        css = {
            "all": ("kostochka38/css/filter.css", 'kostochka38/css/admin-chosen.css')
        }
        js = ['admin/list_filter_collapse.js']

    def get_queryset(self, request):
        queryset = super(ZakazGoodsBaskedOfGoodsProxyAdmin, self).get_queryset(request)
        queryset = queryset.filter(basket_of_good=True)
        return queryset

    def item__title(self, obj):
        return mark_safe(obj.item.title())
    item__title.short_description = u'Название'

    def item__get_photo_thumbnail(self, obj):
        return obj.item.get_photo_thumbnail()
    item__get_photo_thumbnail.short_description = u'Фото'

    def item__quantity_in_reserve(self, obj):
        return obj.item.quantity_in_reserve
    item__quantity_in_reserve.short_description = u'На складе'

    def item__quantity_in_stock(self, obj):
        return obj.item.quantity_in_stock
    item__quantity_in_stock.short_description = u'У поставщика'

    def order_link(self, obj):
        zakaz_url = reverse('admin:catalog_zakaz_change', args=(obj.zakaz.id,))
        return format_html('<a href="{}" target="_blank">{}</a>', zakaz_url, obj.zakaz.id)
    order_link.short_description = u'Заказ'


admin.site.register(Segment, SegmentAdmin)
admin.site.register(ProducerCategory, ProducerCategoryAdmin)
admin.site.register(Producer, ProducerAdmin)
admin.site.register(ItemSale, ItemSaleAdmin)
admin.site.register(Item, ItemAdmin)
admin.site.register(BasketOfGoodItem, BasketOfGoodItemAdmin)
# admin.site.register(ItemPhoto, ItemPhotoAdmin)
admin.site.register(VendorAccount, VendorAccountAdmin)
admin.site.register(Expense, ExpenseAdmin)
# admin.site.register(ExpenseType, ExpenseTypeAdmin)
# admin.site.register(Courier, CourierAdmin)
# admin.site.register(ParserLog, ParserLogAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Filter, FilterAdmin)
admin.site.register(GroupFilter, GroupFilterAdmin)
# admin.site.register(TempZakaz, TempZakazAdmin)
admin.site.register(Zakaz, ZakazAdmin)
admin.site.register(AutoZakaz, AutoZakazAdmin)
admin.site.register(InsideZakaz, InsideZakazAdmin)
admin.site.register(SaleTable, SaleTableAdmin)
# admin.site.register(ZakazBonus, ZakazBonusAdmin)
admin.site.register(OutsideZakaz, OutsideZakazAdmin)
admin.site.register(LogingCourierFinish, LogingCourierFinishAdmin)
admin.site.register(FilterDescription, FilterDescriptionAdmin)
admin.site.register(PriceParser, PriceParserAdmin)
admin.site.register(MovementOfGoods, MovementOfGoodsAdmin)
admin.site.register(WareHouse, WareHouseAdmin)
admin.site.register(ItemPriceChange, ItemPriceChangeAdmin)
admin.site.register(ZakazGoodsBaskedOfGoodsProxy, ZakazGoodsBaskedOfGoodsProxyAdmin)