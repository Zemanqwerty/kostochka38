# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import AbstractUser
from django.db.models import Q
from django.db import models
from django.conf import settings
from catalog.models import WareHouse

if settings.TYPE_CHECKING:
    from typing import Optional


class Duty(models.Model):
    class Meta:
        verbose_name = u"смена"
        verbose_name_plural = u"Смены"

    manager = models.ForeignKey('core.Account', limit_choices_to={'groups__id': '3'}, verbose_name="Кладовщик", related_name='sklad_dury_manager', on_delete=models.CASCADE)
    warehouse = models.ForeignKey('catalog.WareHouse', default=1, verbose_name="Склад", related_name='sklad_durt_warehouse', on_delete=models.SET_DEFAULT)
    open_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата открытия")
    close_date = models.DateTimeField(blank=True, null=True, verbose_name="Дата закрытия")
    cash = models.FloatField(default=0, verbose_name="Денег в кассе при закрытии")

    @classmethod
    def get_current_duty(cls, user, warehouse):
        # type: (AbstractUser, WareHouse) -> Optional[Duty]
        return Duty.objects.filter(Q(warehouse=warehouse) & Q(manager=user) & Q(close_date__isnull=True)).first()

    @classmethod
    def get_current_duty_warehouse(cls, warehouse):
        # type: (WareHouse) -> Optional[Duty]
        return Duty.objects.filter(Q(warehouse=warehouse) & Q(close_date__isnull=True)).first()

    @classmethod
    def get_last_duty(cls, warehouse):
        # type: (WareHouse) -> Optional[Duty]
        return Duty.objects.filter(Q(warehouse=warehouse)).exclude(Q(close_date__isnull=True)).order_by('-id').first()


EncashmentType = (
    (1, u'- изъятие'),
    (2, u'- оплата курьеру'),
    (3, u'- сдача курьеру'),
    (4, u'- въезд на территорию'),
    (5, u'- оплата доставок'),
    (70, u'+ Приемка заказов'),
    (80, u'+ Внесение в кассу'),
    (90, u'+- Прочее')
)

class Encashment(models.Model):
    class Meta:
        verbose_name = u"Инкассация/Поступление"
        verbose_name_plural = u"Инкассации/Поступления"
        ordering = ['-date']

    money = models.IntegerField(verbose_name="Кол-во денег")
    comment = models.TextField(verbose_name="Комментарий")
    date = models.DateTimeField(auto_now_add=True, verbose_name="Дата и время")

    type = models.IntegerField(verbose_name=u'Тип', default=1, choices=EncashmentType)

    duty = models.ForeignKey(Duty, on_delete=models.CASCADE, verbose_name="Смена")

    def duty_manager(self):
        return self.duty.manager

    duty_manager.admin_order_field = 'duty__manager'
    duty_manager.short_description = 'Кассир'

    def duty_warehouse(self):
        return self.duty.warehouse

    duty_warehouse.admin_order_field = 'duty__warehouse'
    duty_warehouse.short_description = 'Склад'
