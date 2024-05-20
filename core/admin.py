# -*- coding: utf-8 -*-
from reversion.admin import VersionAdmin
from django.contrib import admin
from django.contrib.admin.filters import SimpleListFilter
from django.contrib.admin.options import TabularInline
from catalog.models import *
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User, Group
from core.models import AccountChangeForm, AccountCreationForm, SubscriberListSettings, Token, Mail, Account, Static, \
    Slide, SocialReview, Photo, Menu, Page, UserSource, LostUser, Announcement

from django_admin_inline_paginator.admin import TabularInlinePaginated


class LostUserAdmin(VersionAdmin):
    list_display = ['user', 'status', 'need_again', 'create_date', 'average', 'mediana', 'last_order', 'order_count', 'go_to_user']
    list_filter = ['status', 'create_date']
    fields = (
        ('user'),
        ('create_date', 'go_to_user'),
        ('status', 'need_again'),
        'average', 'mediana', 'last_order', 'order_count',
        'description',
    )
    readonly_fields = ['create_date', 'mediana', 'last_order', 'average', 'go_to_user']


class StaticAdmin(VersionAdmin):
    list_display = ['title', 'link', 'menu', 'active']
    #list_per_page = 15
    save_on_top = True
    save_as = True
    #fields = ('title', 'body', 'menu', 'active', 'number', 'meta_descroption', 'meta_keywords')
    fieldsets = (
        (None, {'fields': ('title', 'body', 'menu', 'active', 'number')}),
        ((u'Мета информация для оптимизации'), {'fields': ('link', 'meta_title', 'meta_descroption', 'meta_keywords')}),
    )
    ordering = ('id',)


class SocialReviewAdmin(admin.ModelAdmin):
    list_display = ['title', 'date', 'photo', 'short', 'link']


class InlineAutoZakazAdmin(TabularInlinePaginated):
    model = AutoZakaz
    readonly_fields = ['link', 'last_order', 'repeat_period', 'zakaz', 'repear_count', 'active', 'create_date']
    ordering = ['-create_date']
    fieldsets = (
        (u'', {'fields': ('link', 'last_order', 'repeat_period', 'zakaz', 'repear_count', 'active', 'create_date')}),
    )
    extra = 0
    max_num = 0
    fk_name = 'owner'
    per_page = 20


class InlineZakazAdmin(TabularInlinePaginated):
    model = Zakaz
    readonly_fields = ['date', 'date_end', 'status', 'summ', 'cost', 'revenue', 'dostavka', 'sale_koef', 'link']
    ordering = ['-date']
    fieldsets = (
        (u'', {'fields': (
            ('link', 'date', 'date_end'),
            'status',
            ('summ', 'cost', 'revenue'),
            ('dostavka', 'sale_koef',)
        )}),
    )
    extra = 0
    max_num = 1
    fk_name = 'owner'
    per_page = 20


class GroupListFilter(SimpleListFilter):
    title = u'Группа'
    parameter_name = 'group'

    def lookups(self, request, model_admin):
        groups = Group.objects.all()
        items = ()
        for group in groups:
            items += ((group.id, group.name,),)
        return items

    def queryset(self, request, queryset):
        group_id = request.GET.get(self.parameter_name, None)
        if group_id:
            return queryset.filter(groups=group_id)
        return queryset


class UserSourceAdmin(admin.ModelAdmin):
    list_display = ['title', 'get_user_count']


class AccountAdmin(UserAdmin):
    list_display = ('username', 'id', 'email', 'first_name', 'last_name', 'phone', 'usersource',
                    'sale', 'get_summ_zakaz')
    list_filter = ('sale', 'ur_lico', 'zavodchik', 'optovik', 'usersource', GroupListFilter, 'free_shipping')
    ordering = ('id', 'username')
    search_fields = ('phone', 'first_name', 'last_name', 'email', 'username')
    form = AccountChangeForm
    add_form = AccountCreationForm
    readonly_fields = ['get_summ_zakaz', ]
    inlines = [InlineAutoZakazAdmin, InlineZakazAdmin]
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (('Персональная информация'), {'fields': (('first_name', 'last_name'), ('email', 'unsubscribed', 'basket_of_goods'), 'phone')}),
        (('Юридическое лицо'), {'fields': (
            'ur_lico',
            'zavodchik',
            'optovik',
            'name_pol', ('inn_pol', 'kpp_pol'), 'address_pol', 'okpo_pol',
            'name_plat', ('inn_plat', 'kpp_plat'), 'address_plat', 'okpo_plat'
        )}),

        ('Кассир', {
            'fields': (
                'is_employed',
                'name_cashier',
                'inn_cashier'
            )
        }),

        (('Характеристики'), {'fields': ('usersource', ('sale', 'get_summ_zakaz'),
                                       'description')}),
        (('Доступы'), {'classes': ('collapse', 'close'), 'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (('Даты'), {'classes': ('collapse', 'close'), 'fields': ('last_login', 'date_joined')}),
    )

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super(AccountAdmin, self).get_readonly_fields(request)
        if request.user.is_superuser:
            pass
        else:
            readonly_fields = ['get_summ_zakaz', 'free_shipping', 'free_buyer', 'customer', 'repeat_customer',
                               'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions', 'last_login',
                               'date_joined', 'sale']
        return readonly_fields


class MailAdmin(VersionAdmin):
    list_display = ('title', 'link', 'type', 'type')
    list_filter = ('type', )
    fieldsets = (
        (None, {'fields': ('link', 'title', 'type')}),
        (u'Письмо', {'fields': ('subject', 'body')})
    )


class TokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'used')


class SubscriberListSettingsAdmin(admin.ModelAdmin):
    list_display = ('name', 'subscriberlist', 'visible')


class PhotoAdmin(admin.ModelAdmin):
    list_display = ['photo', 'link', 'title', 'date']
    readonly_fields = ['photo', 'date', 'link']
    fields = ['photo', 'original_image', 'title', 'date', 'link']


class MenuAdmin(VersionAdmin):
    list_display = ['id', 'photo', 'subtitle', 'title', 'link', 'extra_class', 'position', 'show_on_top']
    readonly_fields = ['photo', ]
    list_filter = ['menu_type']
    list_editable = ['position', 'show_on_top']


class PageAdmin(VersionAdmin):
    list_display = ['title', 'date', 'photo', 'link', 'extra_class', 'position', 'section']
    list_filter = ['section', ]
    readonly_fields = ['photo', ]
    list_editable = ['position']


class SlideAdmin(VersionAdmin):
    list_display = ['title', 'admin_slide', 'startdate', 'expdate', 'position']
    readonly_fields = ['admin_slide', ]
    list_editable = ['position']


class AnnouncementAdmin(VersionAdmin):
    list_display = ['text', 'is_active', 'hash']
    list_editable = ['is_active']
    list_filter = ['is_active']
    search_fields = ['text']
    readonly_fields = ['hash']


# admin.site.register(SubscriberListSettings, SubscriberListSettingsAdmin)
# admin.site.register(Token, TokenAdmin)
admin.site.register(Mail, MailAdmin)
admin.site.register(UserSource, UserSourceAdmin)
admin.site.register(Account, AccountAdmin)
# admin.site.register(LostUser, LostUserAdmin)
admin.site.register(Static, StaticAdmin)
admin.site.register(SocialReview, SocialReviewAdmin)
admin.site.register(Photo, PhotoAdmin)
admin.site.register(Menu, MenuAdmin)
admin.site.register(Page, PageAdmin)
admin.site.register(Slide, SlideAdmin)
admin.site.register(Announcement, AnnouncementAdmin)