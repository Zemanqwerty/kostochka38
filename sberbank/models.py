# -*- coding: utf-8 -*-
import uuid
from enum import IntEnum

from django.db import models
from django.conf import settings
import jsonfield
from .signals import payment_success
from django.utils.html import format_html
# from .signals import payment_fail
# from .signals import payment_process


class Choisable(IntEnum):
    @classmethod
    def choices(cls):
        return [(x.value, x.name) for x in cls]


class Status(Choisable):
    CREATED = 0
    PENDING = 1
    SUCCEEDED = 2
    FAILED = 3

    def __str__(self):
        return str(self.value)


class Payment(models.Model):
    """
    details JSON fields:
        username
        currency
        success_url
        fail_url
        session_timeout
        page_view
        redirect_url
    """
    # id = models.IntegerField(primary_key=True, default=0)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    bank_id = models.UUIDField(null=True)
    amount = models.DecimalField(max_digits=65, decimal_places=2)
    error_code = models.PositiveIntegerField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    status = models.PositiveSmallIntegerField(choices=Status.choices(), default=Status.CREATED)
    details = jsonfield.JSONField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    payservice = models.ForeignKey('catalog.Zakaz', verbose_name=u'Заказ', related_name='catalog_zakaz',
                              blank=True, null=True, on_delete=models.CASCADE)

    def get_service(self):
        if self.payservice:
            return format_html(u'<a href="/DgJrfdJg/catalog/zakaz/{0}/change/" target="_blank">{1} &rarr;</a>', self.payservice.id, self.payservice.id)
    get_service.allow_tags = True
    get_service.short_description = u'Заказ'

    def send_signals(self):
        status = self.status
        if status == Status.SUCCEEDED:
            payment_success.send(sender=self)
        # if status == self.STATUS.SUCCESS:
        #     payment_completed.send(sender=self)
        # if status == self.STATUS.FAIL:
        #     payment_fail.send(sender=self)


class LogType(Choisable):
    CREATE = 0
    CALLBACK = 1
    CHECK_STATUS = 2

    def __str__(self):
        return str(self.value)


class BankLog(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment_id = models.UUIDField(null=True)
    bank_id = models.UUIDField(null=True)
    request_type = models.CharField(max_length=1, choices=LogType.choices())
    response_json = jsonfield.JSONField(blank=True, null=True)
    response_text = models.TextField(null=True)
    created = models.DateTimeField(auto_now_add=True)
