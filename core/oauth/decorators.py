# -*- coding: utf-8 -*-

from functools import wraps

from django.middleware import csrf
from django.contrib import messages
from django.shortcuts import render


def oauth_state_handler(view_func):
    @wraps(view_func)
    def decorator(request, *args, **kwargs):
        # state = request.GET.get('state')
        # if state != csrf.get_token(request):
        #     messages.error(
        #         request=request,
        #         message=u'Неверный CSRF-токен',
        #         extra_tags='danger'
        #     )
        #     return render(request, 'newuser.html')
        return view_func(request, *args, **kwargs)
    return decorator


def oauth_error_handler(view_func):
    @wraps(view_func)
    def decorator(request, *args, **kwargs):
        error = request.GET.get('error')
        error_message = request.GET.get('error_message') # Для facebook
        if error or error_message:
            messages.error(
                request=request,
                message=u'Ошибка авторизации',
                extra_tags='danger'
            )
            return render(request, 'newuser.html')
        return view_func(request, *args, **kwargs)
    return decorator