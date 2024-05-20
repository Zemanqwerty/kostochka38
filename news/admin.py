# -*- coding: utf-8 -*-
from django.contrib import admin

from catalog.admin import print_items
from catalog.models import WareHouse
from .models import New, Comment, Vopros_otvet, NewItems
from reversion import revisions as reversion
from adminsortable2.admin import SortableAdminMixin, SortableInlineAdminMixin


# class InlineNewItems(SortableInlineAdminMixin, admin.TabularInline):
class InlineNewItems(admin.TabularInline):
    model = NewItems
    raw_id_fields = ('item', )
    readonly_fields = ['get_thumbnail', 'item__code']
    fields = ['item', 'item__code', 'get_thumbnail']
    extra = 1
reversion.register(NewItems)


class NewAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ['title', 'status', 'photo', 'date', 'short', 'action', 'complete', 'discount_size']
    readonly_fields = ['photo', ]
    list_filter = ['action', 'complete']
    list_per_page = 15
    save_on_top = True
    save_as = True
    fieldsets = (
        (u'', {'classes': ('wide', ), 'fields': ('title', 'original_image', 'photo', 'short', 'body', 'social_short', 'status', 'action_target', ('action', 'complete'), 'discount_size', 'exp_date')}),
        (u'СЕО', {'classes': ('collapse',), 'fields': ('html_title', 'meta_description', 'meta_keywords', 'seo_text')})
    )
    inlines = [InlineNewItems]

    class Media:
        css = {
            "all": ('css/admin-chosen.css', )
        }

    def get_actions(self, request):
        actions = super(SortableAdminMixin, self).get_actions(request)
        warehouses = WareHouse.objects.all()
        for warehouse in warehouses:
            action = print_items(warehouse)
            actions[action.__name__] = (
                action,
                action.__name__,
                action.short_description
            )
        return actions
admin.site.register(New, NewAdmin)


class CommentAdmin(admin.ModelAdmin):
    list_display = ['new', 'date', 'owner']
admin.site.register(Comment, CommentAdmin)


class Vopros_otvetAdmin(admin.ModelAdmin):
    list_display = ['date', 'vopros', 'otvet']
    class Media:
        js = (
            '/tiny_mce/tiny_mce.js',
            '/tiny_mce/tiny_mce_config.js'
        )
admin.site.register(Vopros_otvet, Vopros_otvetAdmin)




