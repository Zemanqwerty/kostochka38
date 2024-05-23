from django.urls import re_path
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView

from core.views import static
from kassa.views.cart_views import autocomplete, autocomplete_customers, add_item_to_cart, clear_cart, update_cart, remove_from_cart
from kassa.views.duty_views import open_duty, change_warehouse, close_duty, logout_user, add_encashment, accept_movement#, delete_encashment
from kassa.views.order_views import OrderListView, OrderCreateView, OrderView, disband, refund, PickupOrderView
from kostochka38 import settings

urlpatterns = [
    re_path(r'^login/$', LoginView.as_view(template_name='admin/login.html'), name='kassa_login'),
    re_path(r'^$', login_required(OrderListView.as_view(), login_url='/k/login/', redirect_field_name='next'), name='kassa_index'),
    re_path(r'^order/$', login_required(OrderCreateView.as_view(), login_url='/k/login/', redirect_field_name='next'), name='kassa_order_create'),
    re_path(r'^order/(?P<reserve>[\w-]+)/$', login_required(OrderCreateView.as_view(), login_url='/k/login/', redirect_field_name='next'), name='kassa_order_create'),
    re_path(r'^order_view/(?P<pk>[0-9]+)/$', login_required(OrderView.as_view(), login_url='/k/login/'), name='kassa_order_view'),
    re_path(r'^pickup_order_view/(?P<pk>[0-9]+)/$', login_required(PickupOrderView.as_view(), login_url="/k/login/"), name="kassa_pickup_order_view"),
    re_path(r'^disband_view/(?P<order_id>[0-9]+)/$', login_required(disband), name="kassa_disband"),
    re_path(r'^autocomplete/$', autocomplete, name='kassa_autocomplete_items'),
    re_path(r'^autocomplete_customers/$', autocomplete_customers, name='kassa_autocomplete_custromers'),
    re_path(r'^add_to_cart/$', add_item_to_cart, name='kassa_add_to_cart'),
    re_path(r'^clear_cart/$', clear_cart, name='kassa_clear_cart'),
    re_path(r'^update_cart/$', update_cart, name='kassa_update_cart'),
    re_path(r'^remove_from_cart/$', remove_from_cart, name='kassa_remove_from_cart'),
    re_path(r'^open_duty/$', open_duty, name='kassa_open_duty'),
    re_path(r'^change_warehouse/(?P<warehouse_id>[0-9]+)/$', change_warehouse, name='kassa_change_warehouse'),
    re_path(r'^close_duty/$', close_duty, name='kassa_close_duty'),
    re_path(r'^refund/(?P<order_id>[0-9]+)/$', refund, name='kassa_refund'),
    re_path(r'^logout/$', logout_user, name='kassa_logout'),
    re_path(r'^add_encashment/$', add_encashment, name='kassa_add_encashment'),
    #re_path(r'^del_encashment/$', delete_encashment, name='kassa_del_encashment'),
    re_path(r'^accept_movement/(?P<movement_id>[0-9]+)$', accept_movement, name='accept_movement')
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
