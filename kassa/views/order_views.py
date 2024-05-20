# coding=utf-8

from komtet_kassa_sdk.v1 import Check, Client, Intent, TaxSystem, VatRate, PaymentMethod

from django.conf import settings
from django.db.models import Q, Sum
from django.db import transaction
from django.http import HttpRequest
from django.shortcuts import redirect, render
from django.http import HttpResponseRedirect
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, DetailView

from catalog.models import Zakaz, WareHouse, Item, ZakazGoods, MovementOfGoods, LeftItem, GoodsInMovement
from core.models import Account
from kassa.models import Duty, Encashment

import logging

if settings.TYPE_CHECKING:
    from typing import Tuple, Iterable, Optional


logger = logging.getLogger(__name__)


class OrderListView(ListView):
    model = Zakaz
    template_name = 'kassa/order_list.html'
    context_object_name = 'orders'
    current_duty = None  # type: Optional[Duty]

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        context = self.get_context_data()
        if not request.user.is_superuser and (not request.user.is_staff or not request.user.groups.filter(id=3).exists()):
            return HttpResponseRedirect('/')
        else:
            return render(self.request, self.template_name, context=context)

    def get_queryset(self):
        current_duty = Duty.get_current_duty(self.request.user, self.request.session.get('warehouse', -1))
        if not current_duty:
            return []
        return self.model.objects.filter(
            (Q(cashier=self.request.user) & Q(date__gt=current_duty.open_date)) | (
            Q(pickup_warehouse=current_duty.warehouse) & Q(status=5) & Q(is_refund=False))
        ).exclude(status=3)

    def get_sums(self):
        #  type: () -> Tuple[float, float, float, Iterable[Encashment]]
        """
        Получение сумм заказов и поступлений/инкассаций
        """
        encashments = Encashment.objects.filter(duty=self.current_duty)

        orders = self.model.objects.filter((Q(cashier=self.request.user) & Q(date__gt=self.current_duty.open_date)) | (
            Q(pickup_warehouse=self.current_duty.warehouse) & Q(status=5))
                                           ).exclude(status=10).exclude(status=3)

        non_cash = orders.exclude(paytype__in=[3, 4, 5]).aggregate(Sum('non_cash')).get('non_cash__sum')
        cash = orders.exclude(paytype__in=[3, 4, 5]).aggregate(Sum('cash')).get('cash__sum')
        encashments_sum = encashments.aggregate(Sum('money')).get('money__sum')
        if not encashments_sum:
            encashments_sum = 0
        if not non_cash:
            non_cash = 0
        if not cash:
            cash = 0
        return encashments_sum, non_cash, cash, encashments

    def get_pickup_orders(self):
        """
        Получение заказов на самовывоз
        """
        return self.model.objects.filter(pickup_warehouse=self.current_duty.warehouse, status=3)

    def get_movement_of_goods(self):
        """
        Получение перемещений
        """
        return MovementOfGoods.objects.filter(warehouse_recieving=self.current_duty.warehouse, status=5).order_by('-id')

    def get_current_duty_data(self):
        """
        Получение данных, которые доступны только для текущей смены
        Инкассации/Поступления сумма налички, безнала, общая сумма
        Перемещения, заказы самовывозы
        """
        context = {}
        encashments_sum, non_cash, cash, encashments = self.get_sums()
        context["encashments"] = encashments
        context["cash_sum"] = cash
        context["non_cash"] = non_cash
        context["orders_sum"] = cash + non_cash
        cash += encashments_sum
        context["duty_cash"] = self.current_duty.cash + cash
        context["movements"] = self.get_movement_of_goods()
        context["pickup_orders"] = self.get_pickup_orders()
        return context

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
        context["warehouses"] = WareHouse.objects.filter(type=1)
        context["warehouse"] = warehouse
        if self.current_duty:
            context.update(self.get_current_duty_data())
        return context


class OrderView(DetailView):
    model = Zakaz
    template_name = 'kassa/order.html'

    def get(self, request, *args, **kwargs):
        if not request.user.is_superuser and (not request.user.is_staff or not request.user.groups.filter(id=3).exists()):
            return HttpResponseRedirect('/')
        else:
            self.object = self.get_object()
            context = self.get_context_data(object=self.object)
            return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        if "change_paytype" in request.POST:
            zakaz = self.get_object()
            if zakaz.paytype in [0, 1]:
                zakaz.paytype = 0 if zakaz.paytype == 1 else 1
                cash = zakaz.cash
                zakaz.cash = zakaz.non_cash
                zakaz.non_cash = cash
                zakaz.save()
                return redirect("kassa_index")
        return super(OrderView, self).post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(OrderView, self).get_context_data(**kwargs)
        sale_cents = sum([i.get_summ() for i in self.object.zakazgoods_set.all()])
        context["sale_cents"] = '0.{}'.format(str(sale_cents).split('.')[1])
        context["sale"] = self.object.get_full_summ() - sale_cents
        return context


class PickupOrderView(OrderView):
    template_name = "kassa/pickup_order.html"


class OrderCreateView(View):
    template_name = "kassa/order_create.html"
    warehouse = None  # type: Optional[WareHouse]
    order = None  # type: Optional[Zakaz]
    request = None  # type: Optional[HttpRequest]
    cart = None  # type: Optional[list]
    pay_type = None  # type: Optional[str]
    cash = None  # type: Optional[str]
    non_cash = None  # type: Optional[str]

    def dispatch(self, request, *args, **kwargs):
        self.request = request
        warehouse = request.session.get('warehouse', -1)
        if warehouse == -1:
            return redirect('/k/')
        self.warehouse = WareHouse.objects.filter(id=int(warehouse)).first()
        return super(OrderCreateView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        if not request.user.is_superuser and (not request.user.is_staff or not request.user.groups.filter(id=3).exists()):
            return HttpResponseRedirect('/')
        else:
            context = {"user": self.request.user, "warehouse": self.warehouse, "is_refund": self.request.GET.get("is_refund")}
            cart = self.request.session.get('cart', list())
            self.request.session['cart'] = cart
            return render(self.request, self.template_name, context=context)

    def create_order(self):
        # type: () -> Zakaz
        customer_id = self.request.POST.get('customer-id')
        customer = Account.objects.filter(id=int(customer_id)).first()
        sale_koef = 0
        if customer.sale:
            sale_koef = customer.sale
        order = Zakaz()
        order.cash = float(self.cash)
        order.non_cash = float(self.non_cash)
        order.cashier = self.request.user
        order.phone = customer.phone
        order.status = 0
        order.f_print = self.f_print
        order.real_desired_time = timezone.now()
        order.paytype = int(self.pay_type)
        order.owner = customer
        order.warehouse = self.warehouse
        order.sale_koef = sale_koef
        order.save()
        return order

    def create_order_items(self, reserve):
        _sum = 0
        _sum_without_sale = 0
        for item_dict in self.cart:
            percent = 0
            amount = int(item_dict.get('amount'))
            item = Item.objects.filter(id=int(item_dict.get('id'))).first()  # type: Item
            sale = 0
            if item.get_sale_retail():
                sale = item.get_sale_retail()
            if sale:
                percent = sale
            elif self.order.owner.sale:
                percent = int(100 - float(self.order.owner.sale) * 100)
            order_item = ZakazGoods()
            order_item.zakaz = self.order
            item_sum = round(item.current_price() * amount, 2)
            _sum_without_sale += item_sum
            if item.current_sale_retail_price():
                item_sum = round(item.current_sale_retail_price() * amount, 2)
            _sum += item_sum
            if item.id != 23330 and item.id != 23329:
                order_item.sale = percent
            else:
                order_item.sale = 0
            order_item.item = item
            order_item.quantity = amount
            order_item.save()
        if len(str(_sum).split('.')) > 1:
            _sum -= float("0.{}".format(str(_sum).split('.')[1]))
        self.order.summ = _sum_without_sale
        if not reserve:
            self.order.status = 5
        self.order.save()

    def create_refund_order(self):
        # type: () -> Zakaz
        customer_id = self.request.POST.get('customer-id')
        customer = Account.objects.filter(id=int(customer_id)).first()
        sale_koef = 0
        if customer.sale:
            sale_koef = customer.sale
        order = Zakaz()
        order.cash = float(self.cash)
        order.non_cash = float(self.non_cash)
        order.cashier = self.request.user
        order.phone = customer.phone
        order.status = 0
        order.f_print = self.f_print
        order.real_desired_time = timezone.now()
        order.paytype = int(self.pay_type)
        order.owner = customer
        order.warehouse = self.warehouse
        order.sale_koef = sale_koef
        order.is_refund = True
        order.status = 5
        order.save()
        return order

    def create_refund_order_items(self):
        _sum = 0
        _sum_without_sale = 0
        for item_dict in self.cart:
            percent = 0
            amount = int(item_dict.get('amount'))
            item = Item.objects.filter(id=int(item_dict.get('id'))).first()  # type: Item
            cost = int(item_dict.get('cost', item.current_price()))
            item.price = cost
            sale = 0
            if item.get_sale_retail():
                sale = item.get_sale_retail()
            if sale:
                percent = sale
            elif self.order.owner.sale:
                percent = int(100 - float(self.order.owner.sale) * 100)
            order_item = ZakazGoods()
            order_item.zakaz = self.order
            item_sum = round(item.current_price() * amount, 2)
            _sum_without_sale += item_sum
            if item.current_sale_retail_price():
                item_sum = round(item.current_sale_retail_price() * amount, 2)
            _sum += item_sum
            if item.id != 23330 and item.id != 23329:
                order_item.sale = percent
            else:
                order_item.sale = 0
            order_item.item = item
            order_item.quantity = -amount
            order_item.save()

        _sum -= float("0.{}".format(str(_sum).split('.')[1]))
        self.order.save()

    def update_order(self):
        self.order.paytype = int(self.pay_type)
        self.order.cashier = self.request.user
        self.order.cash = float(self.cash)
        self.order.non_cash = float(self.non_cash)

        self.order.status = 5
        if self.order.warehouse != self.warehouse:
            movement = MovementOfGoods()
            movement.warehouse_donor = self.order.warehouse
            movement.warehouse_recieving = self.warehouse
            movement.extra = u"Автоматическое перемещение из расформирования самовывозы №{}".format(self.order.id)
            movement.delivery_date = timezone.now()
            movement.save(self.request)
            for item in ZakazGoods.objects.filter(zakaz=self.order):
                goodsinmovement = GoodsInMovement()
                goodsinmovement.item = item.item
                goodsinmovement.quantity = item.quantity
                goodsinmovement.movement = movement
                goodsinmovement.save()
            movement.status = 6
            movement.save(self.request)

            self.order.warehouse = self.warehouse
        self.order.save()

    def reserve_order(self):
        self.order.pickup_warehouse = self.warehouse
        self.order.warehouse = self.warehouse
        self.order.status = 3
        self.order.save()

    def post(self, request, *args, **kwargs):
        self.pay_type = self.request.POST.get('pay_type', 0)
        self.cash = self.request.POST.get('cash')
        self.non_cash = self.request.POST.get('non_cash')
        self.cart = self.request.session.get('cart', list())
        self.f_print = True if self.request.POST.get('f_print') else False
        order_id = self.request.POST.get('order_id', '')
        reserve = kwargs.get('reserve', False)
        if order_id == '':
            if len(self.cart) == 0:
                return redirect('/k/order/')
            is_refund = self.request.POST.get('is_refund')
            if is_refund == 'true':
                self.order = self.create_refund_order()
                self.create_refund_order_items()
            else:
                self.order = self.create_order()
                self.create_order_items(reserve)
                if reserve:
                    self.cash = "0"
                    self.non_cash = "0"
                    self.reserve_order()
        else:
            self.order = Zakaz.objects.filter(id=int(order_id)).first()
            self.update_order()
        if not reserve:
            duty = Duty.get_current_duty(self.request.user, self.warehouse)

            if int(self.pay_type) == 0 or int(self.pay_type) == 1 or int(self.pay_type) == 6:
                duty.cash_earned += self.order.cash
                duty.non_cash += self.order.non_cash

            duty.save()
        return redirect('/k/clear_cart/')


def disband(request, order_id):
    warehouse = request.session.get('warehouse')
    warehouse = WareHouse.objects.filter(id=int(warehouse)).first()
    order = Zakaz.objects.filter(id=int(order_id)).first()  # type: Zakaz
    """
    создадим перемещение только в том случае если склад формирования заказа не совпадает со складом нахождения заказа
    """
    if order.warehouse != warehouse:
        movement = MovementOfGoods()
        movement.warehouse_recieving = warehouse
        movement.warehouse_donor = order.warehouse
        movement.delivery_date = timezone.now()
        movement.status = 0
        movement.save(request)
        for zakazgoods in order.zakazgoods_set.all():
            movement_item = GoodsInMovement()
            movement_item.item = zakazgoods.item
            movement_item.quantity = zakazgoods.quantity
            movement_item.movement = movement
            movement_item.save()
        movement.status = 6
        movement.save(request)

    order.status = 10
    order.warehouse = warehouse
    order.cashier = request.user
    order.save()
    return redirect('/k/')


def refund(request, order_id):
    """
    Отмена заказа
    """
    with transaction.atomic():
        order = Zakaz.objects.filter(id=int(order_id)).first()  # type: Zakaz
        order.status = 10
        order.save()
        duty = Duty.get_current_duty(request.user, request.session.get('warehouse'))
        duty.cash_earned -= order.cash
        duty.non_cash -= order.non_cash
        duty.save()
        return redirect('/k/')
