# -*- coding: utf-8 -*-

import hashlib

from django.contrib import auth, messages
from django.conf import settings
from django.db.models import Q

from ..models import Account
from ..mail import htmlmail_sender


def create_account(username, request):
    if Account.objects.filter(Q(username=username) & Q(Q(is_staff=True) | Q(is_superuser=True))).exists():
        return
    user, created = Account.objects.get_or_create(username=username)
    user.email = username
    user.save()
    if created:
        password = hashlib.sha256(username + settings.SECRET_KEY).hexdigest()[:8]
        user.set_password(password)
        user.save()
        messages.success(
            request=request,
            message=(
                u'Регистрация прошла успешно. Пароль отправлен на почту, '
                u'привязанную к Вашей странице'
            )
        )
        data = {
            'username': username,
            'password': password,
            'user': user
        }
        htmlmail_sender('registration', data, username, user)
    else:
        messages.success(
            request=request,
            message=u'Вход успешно выполнен'
        )
    auth.login(request, user)