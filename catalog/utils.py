# -*- coding: utf-8 -*-
from django.conf import settings


def shipping(user, summ):
    if user.is_authenticated:
        if user.free_shipping:
            return 0
    dostavka = settings.DOSTAVKA
    if summ >= settings.MIN_SUMM_FREE_SHIPING:
        dostavka = 0
    return dostavka


def is_digit(char):
    try:
        float(char)
        return True
    except:
        return False
