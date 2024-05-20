# coding=utf-8
import json
import traceback
from uuid import UUID

from django.conf import settings
from django.http import  HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from yookassa.domain.common import SecurityHelper
from yookassa.domain.notification import WebhookNotificationFactory, WebhookNotificationEventType

from sberbank.models import Payment, BankLog, Status, LogType
from catalog.models import Zakaz
from sberbank.exceptions import PaymentNotFoundException, ProcessingException
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from yookassa import Configuration
from yookassa import Payment as YooPayment


def callback(request):
    data = {
        'bank_id': request.GET.get('mdOrder'),
        'payment_id': str(UUID(request.GET.get('orderNumber'))),
        'checksum': request.GET.get('checksum'),
        'operation': request.GET.get('operation'),
        'status': request.GET.get('status'),
    }

    try:
        payment = Payment.objects.get(bank_id=data.get('bank_id'))
    except Payment.DoesNotExist:
        raise PaymentNotFoundException()

    log = BankLog(request_type=LogType.CALLBACK, bank_id=payment.bank_id, payment_id=payment.uid, response_json=data)
    log.save()

    if int(data.get('status')) == 1:
        payment.status = Status.SUCCEEDED
        payment.send_signals()
        payment.payservice.status = 11
        payment.payservice.paid_client = True
        payment.payservice.cash_go_to_kassa = True
        payment.payservice.save()

    elif int(data.get('status')) == 0:
        payment.status = Status.FAILED

    payment.save()

    return HttpResponse(status=200)


def payment_page(request, zakaz_id):
    if request.user.is_authenticated:
        zakaz_object = get_object_or_404(Zakaz, id=zakaz_id, owner=request.user)
        response = render(request, 'sberbank/zakaz_payment.html', locals())
        response['Cache-Control'] = 'no-cache, must-revalidate'
        return response
    return HttpResponseRedirect('/')


def create_payment_yookassa(amount, payment_uuid, name, email, phone, description):
    """Создаёт заказ в платёжном шлюзе Юкасса"""
    Configuration.account_id = settings.YOOKASSA_ACCOUNT_ID
    Configuration.secret_key = settings.YOOKASSA_SECRET_KEY

    return YooPayment.create({
        "amount": {
            "value": str(amount),
            "currency": "RUB"
        },
        # "receipt": {
        #     "customer": {
        #         "full_name": name,
        #         "email": email,
        #         "phone": phone,
        #     },
        # },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://kostochka38.ru" + reverse('payment_success', args=[payment_uuid])
        },
        "capture": True,
        # "description": description,
        "metadata": {
            "payment_uuid": payment_uuid
        },
    }, payment_uuid)


def payment_redirect(request, zakaz_id):
    # if request.user.is_authenticated:
    zakaz_object = get_object_or_404(Zakaz, id=zakaz_id, status=82, paytype=4)

    amount = zakaz_object.k_oplate()

    payment_obj = Payment(amount=zakaz_object.k_oplate(), payservice=zakaz_object)
    payment_obj.save()

    try:
        payment_yookassa = create_payment_yookassa(
            amount=amount,
            payment_uuid=payment_obj.uid.hex,
            name='',
            phone='',
            email='',
            description=''
        )
    except Exception as e:
        traceback.print_exc()
        payment_obj.status = Status.FAILED
        payment_obj.save()
        log = BankLog(request_type=LogType.CREATE, payment_id=payment_obj.uid, response_text=e.message)
        log.save()
        raise ProcessingException(payment_obj.uid)
    else:
        payment_obj.bank_id = payment_yookassa.id
        payment_obj.status = Status.PENDING
        payment_obj.save()
        log = BankLog(request_type=LogType.CREATE, payment_id=payment_obj.uid, bank_id=payment_yookassa.id,
                      response_json=payment_yookassa)
        log.save()
        return HttpResponseRedirect(payment_yookassa.confirmation.confirmation_url)


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@csrf_exempt
def yookassa_webhook(request):
    ip = get_client_ip(request)
    if not SecurityHelper().is_ip_trusted(ip):
        return HttpResponse(status=400)

    event_json = json.loads(request.body)

    try:
        notification_object = WebhookNotificationFactory().create(event_json)
        response_obj = notification_object.object

        payment_uuid = response_obj.metadata.get('payment_uuid')

        payment_obj = get_object_or_404(Payment, uid=payment_uuid)

        if payment_obj.status == Status.PENDING:
            if notification_object.event == WebhookNotificationEventType.PAYMENT_SUCCEEDED:
                payment_obj.status = Status.SUCCEEDED
                payment_obj.send_signals()
                payment_obj.save()
                payment_obj.payservice.status = 11
                payment_obj.payservice.paid_client = True
                payment_obj.payservice.cash_go_to_kassa = True
                payment_obj.payservice.save()

            elif notification_object.event == WebhookNotificationEventType.PAYMENT_CANCELED:
                payment_obj.status = Status.FAILED
                payment_obj.save()

            log = BankLog(request_type=LogType.CALLBACK, bank_id=payment_obj.bank_id, payment_id=payment_obj.uid,
                          response_json=event_json)
            log.save()

    except Exception as e:
        traceback.print_exc()
        log = BankLog(request_type=LogType.CALLBACK, response_json=event_json, response_text=e.message)
        log.save()
        return HttpResponse(status=400)

    return HttpResponse(status=200)


def payment_success(request, payment_uuid):
    current_payment = Payment.objects.get(uid=payment_uuid)

    if current_payment.status != Status.SUCCEEDED:
        return HttpResponseRedirect(reverse('payment_fail', args=[payment_uuid]))

    response = render(request, 'sberbank/zakaz_payment_success.html', locals())
    response['Cache-Control'] = 'no-cache, must-revalidate'
    return response


def payment_fail(request, payment_uuid):
    current_payment = Payment.objects.get(uid=payment_uuid)

    response = render(request, 'sberbank/zakaz_payment_fail.html', locals())
    response['Cache-Control'] = 'no-cache, must-revalidate'
    return response
