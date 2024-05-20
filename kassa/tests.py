# coding=utf-8
from django.test import Client
from django.urls import reverse
from django.conf import settings

from catalog.models import WareHouse
from core.models import Account

import pytest

import logging
import json


if settings.TYPE_CHECKING:
    from typing import Optional

logger = logging.getLogger(__name__)


# Create your tests here.

@pytest.fixture(name="client")
def client_with_warehouse():
    _client = Client()
    user = {'username': 'kassir1', 'password': 'retro123'}
    _client.post(reverse('kassa_login'), data=user)
    _client.get(reverse('kassa_change_warehouse', kwargs={'warehouse_id': '2'}))
    return _client


@pytest.fixture(name="client_ww")
def client_without_warehouse():
    _client = Client()
    user = {'username': 'kassir1', 'password': 'retro123'}
    _client.post(reverse('kassa_login'), data=user)
    return _client


@pytest.mark.django_db
def test_cashier_login():
    client = Client()
    response = client.get(reverse('kassa_index'))
    assert response.status_code == 302
    user = {'username': 'kassir1', 'password': 'retro123'}
    response = client.post(response.url, data=user)
    assert response.url == '/k/'


@pytest.mark.django_db
def test_redirects(client_ww):
    # type: (Client) -> None
    response = client_ww.get(reverse('kassa_open_duty'))
    assert response.status_code == 302
    response = client_ww.get(reverse('kassa_close_duty'))
    assert response.status_code == 302
    response = client_ww.get(reverse('kassa_logout'))
    assert response.status_code == 302
    response = client_ww.get(reverse('kassa_order_create'))
    assert response.status_code == 302


def clear_cart(client):
    # type: (Client) -> None
    client.get(reverse('kassa_clear_cart'))


def autocomplete_items(client, q):
    # type: (Client, unicode) -> list
    response = client.get(reverse('kassa_autocomplete_items'), data={"q": q})
    json_content = json.loads(response.content)
    return json_content


def autocomplete_customers(client, q):
    # type: (Client, unicode) -> list
    response = client.get(reverse('kassa_autocomplete_custromers'), data={"q": q})
    json_content = json.loads(response.content)
    return json_content


def add_item_to_cart(client, q):
    # type: (Client, unicode) -> list
    response = client.get(reverse('kassa_add_to_cart'), data={"id": q})
    json_content = json.loads(response.content)
    return json_content


def update_cart(client, customer_id=''):
    # type: (Client, Optional[unicode]) -> dict
    response = client.get(reverse('kassa_update_cart'), data={"user_id": customer_id})
    json_content = json.loads(response.content)
    return json_content


def delete_from_cart(client, q):
    response = client.get(reverse('kassa_remove_from_cart'), data={"id": q})
    json_content = json.loads(response.content)
    return json_content


@pytest.mark.django_db
def test_autocomplete_items(client):
    # type: (Client) -> None
    json_content = autocomplete_items(client, u"косточка")
    assert len(json_content) > 0
    json_content = autocomplete_items(client, u"09202")
    assert len(json_content) == 1


@pytest.mark.django_db
def test_autocomplete_customers(client):
    # type: (Client) -> None
    json_content = autocomplete_customers(client, u"софья")
    assert len(json_content) > 0
    json_content = autocomplete_customers(client, u"895014")
    assert len(json_content) > 0
    json_content = autocomplete_customers(client, u"mail.ru")
    assert len(json_content) > 0


@pytest.mark.django_db
def test_add_item_to_cart(client):
    # type: (Client) -> None
    json_content = update_cart(client)
    assert len(json_content.get('cart', [])) == 0
    json_content = add_item_to_cart(client, "13067")
    assert json_content == {}
    json_content = update_cart(client)
    assert len(json_content.get('cart', [])) == 1


@pytest.mark.django_db
def test_delete_from_cart(client):
    # type: (Client) -> None
    add_item_to_cart(client, "13067")
    json_content = delete_from_cart(client, "13067")
    assert json_content == {}


@pytest.mark.django_db
def test_update_cart_with_customer(client):
    # type: (Client) -> None
    json_content = autocomplete_customers(client, u'Софья')
    customer_id = json_content[0].get('id')
    logger.warning(customer_id)
    add_item_to_cart(client, u"13067")
    json_content = update_cart(client, customer_id)


@pytest.mark.django_db
def test_create_order_with_discount(client):
    # type: (Client) -> None
    json_content = autocomplete_items(client, u"Косточка")
    item = json_content[0]
    product_id = item.get('id')
    add_item_to_cart(client, product_id)
    json_content = update_cart(client)
    cart_item_id = json_content.get('cart', [])[0].get("id")
    assert cart_item_id == product_id
    assert json_content.get('cents') == 0
    assert json_content.get('cart_sum') == 207
    assert json_content.get('sale_cost') == 0
    json_content = add_item_to_cart(client, product_id)
    assert json_content == {}
    json_content = update_cart(client)
    cart_item_id = json_content.get('cart', [])[0].get("id")
    assert cart_item_id == product_id
    assert json_content.get('cents') == 0
    assert json_content.get('cart_sum') == 414
    assert json_content.get('sale_cost') == 0
    json_content = autocomplete_customers(client, u"Софья")
    customer_id = json_content[0].get('id')
