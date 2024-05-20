# -*- coding: utf-8 -*-
from django.contrib.auth import logout
from django.db.models import Sum, Q
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from catalog.models import GoodsInMovement, WareHouse, MovementOfGoods, Zakaz, Expense, LeftItem
from kassa.models import Encashment, Duty

import logging

logger = logging.getLogger(__name__)


def open_duty(request):
    warehouse = request.session.get('warehouse', -1)
    if warehouse == -1:
        return redirect('/k/')

    warehouse = WareHouse.objects.filter(id=int(warehouse)).first()
    if not warehouse:
        request.session['warehouse'] = -1
        return redirect('/k/')

    current_duty = Duty.get_current_duty(request.user, warehouse)
    if current_duty:
        return redirect('/k/')

    last_duty = Duty.get_last_duty(warehouse)
    money = 0
    if last_duty:
        money = last_duty.cash
    duty = Duty()
    duty.warehouse = warehouse
    duty.manager = request.user
    duty.cash_earned = 0
    duty.cash = money
    duty.save()
    return redirect('/k/')


def change_warehouse(request, warehouse_id):
    request.session['warehouse'] = warehouse_id
    return redirect('/k/')


def close_duty(request):
    warehouse = request.session.get('warehouse', -1)
    if warehouse == -1:
        return redirect('/k/')
    warehouse = WareHouse.objects.filter(id=int(warehouse))
    current_duty = Duty.get_current_duty(request.user, warehouse)
    encashments = Encashment.objects.filter(duty=current_duty)
    orders = Zakaz.objects.filter(Q(cashier=request.user) & Q(date__gt=current_duty.open_date) | (
            Q(pickup_warehouse=warehouse) & Q(status=5))).exclude(status__in=[3, 10])

    movement = MovementOfGoods()
    movement.warehouse_donor = WareHouse.objects.filter(id=1).first()
    movement.warehouse_recieving = current_duty.warehouse
    movement.ordered = False
    movement.details = ''
    movement.save(request)
    for order in orders:
        order.status = 6
        if int(order.paytype) != 3 and order.paid_client is False:
            current_duty.cash += float(order.cash)
        order.paid_client = True
        order.cash_go_to_kassa = True
        order.create_expenses()

        order.save()

        for order_item in order.zakazgoods_set.all().exclude(sale__gte=25):
            print (order_item)
            if order_item.zakaz.warehouse.type == 0:
                continue
            if order_item.item.id == 23330 or order_item.item.id == 23329:
                continue
            if order_item.zakaz.dostavkatype == 1:
                continue

            need_for_order_count = order_item.item.buy_count_3_month_by_warehouse_ceil(warehouse) - order_item.item.quantity_in_reserve_by_warehouse(warehouse)
            print ('order_item.item.buy_count_3_month_by_warehouse_ceil(warehouse): ')
            print (order_item.item.buy_count_3_month_by_warehouse_ceil(warehouse))
            print ('order_item.item.quantity_in_reserve_by_warehouse(warehouse): ')
            print(order_item.item.quantity_in_reserve_by_warehouse(warehouse))

            left = order_item.item.quantity_in_reserve_by_warehouse(1) - order_item.item__vreserve_count()
            print ('left: ')
            print (left)
            if need_for_order_count > left:
                need_for_order_count = left

            if need_for_order_count <= 0:
                continue

            movement_item = GoodsInMovement.objects.filter(movement=movement, item=order_item.item).first()
            if movement_item:
                movement_item.quantity = need_for_order_count
                movement_item.save()

                movement.details += "update %s b_3_m=%s - ins=%s \r\n" % (
                                                order_item.item.id,
                                                order_item.item.buy_count_3_month_by_warehouse_ceil(warehouse),
                                                order_item.item.quantity_in_reserve_by_warehouse(warehouse))
                movement.save(request)
            else:
                new_movement_item = GoodsInMovement()
                new_movement_item.quantity = need_for_order_count
                new_movement_item.movement = movement
                new_movement_item.item = order_item.item
                new_movement_item.save()

                movement.details += "%s b_count_3_m=%s - inst=%s \r\n" % (
                                                order_item.item.id,
                                                order_item.item.buy_count_3_month_by_warehouse_ceil(warehouse),
                                                order_item.item.quantity_in_reserve_by_warehouse(warehouse))
                movement.save(request)

    if not movement.goodsinmovement_set.all().count():
        movement.delete()
    encashments_sum = encashments.aggregate(Sum('money')).get('money__sum')
    if not encashments_sum:
        encashments_sum = 0
    current_duty.cash += encashments_sum
    current_duty.close_date = timezone.now()
    current_duty.save()

    for i in encashments:
        if i.type in [2, 3, 9] and i.money < 0:
            expensetype = 21
            if i.type == 2:
                expensetype = 7
            elif i.type == 3:
                expensetype = 1
            elif i.type == 9:
                expensetype = 21
            new_expense = Expense(
                type=0,
                type_of_currency=0,
                value=i.money,
                source=0,
                description=i.comment,
                expensetype_id=expensetype
            )
            new_expense.save()
        else:
            pass
    return redirect('/k/logout/')


def logout_user(request):
    logout(request)
    return redirect('/k/')


@csrf_exempt
def add_encashment(request):
    warehouse = request.session.get("warehouse")
    money = request.POST.get("money")
    comment = request.POST.get("comment")
    type = request.POST.get("type")
    duty = Duty.get_current_duty(request.user, warehouse)
    encashment = Encashment()
    encashment.duty = duty
    encashment.money = int(money)
    encashment.comment = comment
    encashment.type = type
    encashment.save()
    return JsonResponse({})

#
# @csrf_exempt
# def delete_encashment(request):
#     enc_id = request.POST.get("id")
#     enc = Encashment.objects.filter(id=int(enc_id)).first()
#     enc.delete()
#     return JsonResponse({})


def accept_movement(request, movement_id):
    movement = MovementOfGoods.objects.filter(id=int(movement_id)).first()
    movement.status = 6
    movement.save(request)
    return redirect(reverse('kassa_index'))
