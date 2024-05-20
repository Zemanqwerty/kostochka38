# coding=utf-8
from django.conf import settings
from django.views.generic import ListView
from django.db.models import Q, Sum

from django.shortcuts import redirect, render
from django.http import HttpResponseRedirect
from catalog.models import Zakaz, WareHouse, InsideZakaz, MovementOfGoods
from sklad.models import Duty, Encashment
from core.models import Account

import logging
import datetime

if settings.TYPE_CHECKING:
    from typing import Tuple, Iterable


logger = logging.getLogger(__name__)


class OrderListView(ListView):
    model = Zakaz
    template_name = 'sklad/order_list.html'
    context_object_name = 'orders'
    current_duty = None  # type: Optional[Duty]

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        context = self.get_context_data()
        if not request.user.is_superuser and (not request.user.is_staff or not request.user.groups.filter(id=4).exists()):
            return HttpResponseRedirect('/')
        else:
            return render(self.request, self.template_name, context=context)

    def get_queryset(self):
        current_duty = Duty.get_current_duty(self.request.user, self.request.session.get('warehouse', -1))
        if not current_duty:
            return []
        return []

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)  # type: dict
        warehouse = self.request.session.get('warehouse', -1)
        cur_warehouse_duty = Duty.get_current_duty_warehouse(warehouse)
        if cur_warehouse_duty:
            if cur_warehouse_duty.manager != self.request.user:
                context["status"] = 1
                context["cur_user"] = cur_warehouse_duty.manager
                warehouse = -1
                self.request.session['warehouse'] = warehouse
        self.current_duty = Duty.get_current_duty(self.request.user, warehouse)
        context['user'] = self.request.user
        context['last_duty'] = Duty.get_last_duty(warehouse)
        context["duty"] = self.current_duty

        if self.current_duty:
            current_cash = self.current_duty.cash
            encashments = Encashment.objects.filter(duty=self.current_duty)
            encashments_sum = encashments.aggregate(Sum('money')).get('money__sum')
            if not encashments_sum:
                encashments_sum = 0
            context['current_cash'] = current_cash + encashments_sum

        context["warehouses"] = WareHouse.objects.filter(type=0)
        context["warehouse"] = warehouse
        context["encashments"] = Encashment.objects.filter(duty=self.current_duty)

        couriers = Account.objects.filter(groups__id=1).order_by('-id')

        for i in couriers:
            i.zakaz_print = Zakaz.objects.filter(courier_id=i.id, status=3).count()

        context["couriers"] = couriers

        context["pickup_orders"] = Zakaz.objects.filter(dostavkatype=1, real_desired_time=datetime.datetime.now(), status__in=[0, 11, 2, 3]).order_by('pickup_warehouse')
        context["insidezakazs_today"] = InsideZakaz.objects.filter(date_pickup=datetime.datetime.now()).select_related('segment_new')
        context["movements_to_sklad"] = MovementOfGoods.objects.filter(delivery_date=datetime.datetime.now(), warehouse_recieving=warehouse)


        # for i in couriers:
        #     couriers_menu.append(items.MenuItem('%s %s' % (i.last_name, i.first_name),
        #                                         '/manage/calculate_courier/?user=%s' % i.username))
        #
        # couriers_menu_collect_order = []
        # for i in couriers:
        #     couriers_menu_collect_order.append(
        #         items.MenuItem('%s %s' % (i.last_name, i.first_name), '/manage/collect_orders/?user=%s' % i.username))
        #
        if self.current_duty:
            pass
        return context


