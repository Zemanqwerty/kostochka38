# coding=utf-8
from itertools import zip_longest

from catalog.models import Item

from django.conf import settings

BASE_URL = "https://kostochka38.ru"
if settings.LOCAL:
    BASE_URL = "http://127.0.0.1:8000"


def get_item_cell(item):
    #  type: (Item) -> unicode
    return u"""
    <table style="font-size: 14px">
    <tr>
        <td style="text-align: left;">
            <span style="border: 2px solid #619af8; background: #619af8;vertical-align:top; border-radius:10px;color: #fff; padding: 3px 8px 3px;margin: 3px 5px 5px; top:0; left:0;">{}</span>
        </td>
    </tr>    
    <tr>
        <td style="text-align: center;">
            <a href="{}">{}</a>
        </td>
    </tr>
    <tr>
        <td style="text-align: center; font-size: 24px; font-weight: 700; color: #222;">
        <b>{} <span style="font-size: 80%; font-weight: 500;">руб</span></b>
        </td>
    </tr>
    <tr>
        <td style="text-align: center; line-height: 1.5;">
        <a style="color: #444; text-decoration: none;" href="{}">{}, {}, {}</a> 
        </td>
    </tr>
    </table>
    """.format(item.weight, u"{}{}".format(BASE_URL, item.get_absolute_url()), item.deckitem.photo_big_thumb_absolute_url(), item.get_current_price_with_intspace(), u"{}{}".format(BASE_URL, item.get_absolute_url()), item.deckitem.producer.title, item.deckitem.title, item.weight)


def group_by_two(items):
    args = [iter(items)] * 2
    return zip_longest(fillvalue=None, *args)
