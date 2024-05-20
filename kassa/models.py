# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import AbstractUser
from django.db.models import Q, Sum, F
from django.db import models
from django.conf import settings

# Create your models here.

from catalog.models import WareHouse, Zakaz

if settings.TYPE_CHECKING:
    from typing import Optional


class Duty(models.Model):
    class Meta:
        verbose_name = u"смена"
        verbose_name_plural = u"Смены"

    manager = models.ForeignKey('core.Account', limit_choices_to={'groups__id': '3'}, verbose_name="Кассир", on_delete=models.CASCADE)
    warehouse = models.ForeignKey('catalog.WareHouse', default=1, verbose_name="Склад", on_delete=models.SET_DEFAULT)
    open_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата открытия")
    close_date = models.DateTimeField(blank=True, null=True, verbose_name="Дата закрытия")
    cash = models.FloatField(default=0, verbose_name="Денег в кассе")
    non_cash = models.FloatField(default=0, verbose_name="Продано за безнал")
    cash_earned = models.FloatField(default=0, verbose_name="Продано за наличку")

    def total_earned(self):
        return self.non_cash + self.cash_earned

    total_earned.short_description = u"Итого за смену"

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
    (1, u'- Изъятие'),
    (2, u'- ЗП'),
    (3, u'- Возврат клиенту'),
    (4, u'+ Внесение сдачи'),
    (9, u'+- Прочее')
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
