# -*- coding: utf-8 -*-
from django import forms
from django.contrib import admin
from reversion.admin import VersionAdmin

from catalog.widgets import CheckboxSelectMultiple

from catalog.tuples import ORDER_STATUS
from .models import Payment, BankLog
from math import ceil
from django.conf import settings

import datetime


class PaymentAdmin(admin.ModelAdmin):
    list_display = ['uid', 'amount', 'status', 'get_service']
    # list_filter = ['in_statistics', 'in_balans']

admin.site.register(Payment, PaymentAdmin)