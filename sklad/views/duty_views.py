from django.contrib.auth import logout
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse

from catalog.models import WareHouse, Expense
from sklad.models import Encashment, Duty

import logging

logger = logging.getLogger(__name__)


def open_duty(request):
    warehouse = request.session.get('warehouse', -1)
    if warehouse == -1:
        return redirect(reverse('sklad_index'))

    warehouse = WareHouse.objects.filter(id=int(warehouse)).first()
    if not warehouse:
        request.session['warehouse'] = -1
        return redirect(reverse('sklad_index'))

    current_duty = Duty.get_current_duty(request.user, warehouse)
    if current_duty:
        return redirect(reverse('sklad_index'))

    last_duty = Duty.get_last_duty(warehouse)
    money = 0
    if last_duty:
        money = last_duty.cash
    duty = Duty()
    duty.warehouse = warehouse
    duty.manager = request.user
    duty.cash = money
    duty.save()
    return redirect(reverse('sklad_index'))


def change_warehouse(request, warehouse_id):
    request.session['warehouse'] = warehouse_id
    return redirect(reverse('sklad_index'))


def close_duty(request):
    warehouse = request.session.get('warehouse', -1)
    if warehouse == -1:
        return redirect(reverse('sklad_index'))
    warehouse = WareHouse.objects.filter(id=int(warehouse))
    current_duty = Duty.get_current_duty(request.user, warehouse)
    encashments = Encashment.objects.filter(duty=current_duty)

    encashments_sum = encashments.aggregate(Sum('money')).get('money__sum')
    if not encashments_sum:
        encashments_sum = 0
    current_duty.cash += encashments_sum
    current_duty.close_date = timezone.now()
    current_duty.save()

    for i in encashments:
        if i.type in [4, 5, 90] and i.money < 0:
            expensetype = 12
            if i.type == 4:
                expensetype = 11
            elif i.type == 5:
                expensetype = 1
            elif i.type == 90:
                expensetype = 12
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

    return redirect(reverse('sklad_logout'))


def logout_user(request):
    logout(request)
    return redirect(reverse('sklad_index'))


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


# @csrf_exempt
# def delete_encashment(request):
#     enc_id = request.POST.get("id")
#     enc = Encashment.objects.filter(id=int(enc_id)).first()
#     enc.delete()
#     return JsonResponse({})
