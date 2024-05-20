from django.contrib import admin
from reversion.admin import VersionAdmin

from sklad.models import Duty, Encashment


class EncashmentInline(admin.TabularInline):
    model = Encashment
    extra = 0


@admin.register(Duty)
class DutyAdmin(VersionAdmin):
    list_filter = ['manager', 'open_date', 'close_date']
    list_display = ['manager', 'open_date', 'close_date', 'cash']
    date_hierarchy = 'open_date'
    inlines = [EncashmentInline]


@admin.register(Encashment)
class EncashmentAdmin(VersionAdmin):
    date_hierarchy = 'date'
    list_filter = ['duty__warehouse', 'type', 'duty__manager']
    list_display = ['money', 'duty_manager', 'duty_warehouse', 'type', 'comment', 'date']

