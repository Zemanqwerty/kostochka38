from django.urls import re_path
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView

from sklad.views.duty_views import open_duty, change_warehouse, close_duty, logout_user, add_encashment
from sklad.views.order_views import OrderListView

urlpatterns = [
    re_path(r'^login/$', LoginView.as_view(template_name='admin/login.html'), name='sklad_login'),
    re_path(r'^$', login_required(OrderListView.as_view(), login_url='/s/login/', redirect_field_name='next'), name='sklad_index'),

    re_path(r'^open_duty/$', open_duty, name='sklad_open_duty'),
    re_path(r'^change_warehouse/(?P<warehouse_id>[0-9]+)/$', change_warehouse, name='sklad_change_warehouse'),
    re_path(r'^close_duty/$', close_duty, name='sklad_close_duty'),

    re_path(r'^logout/$', logout_user, name='sklad_logout'),
    re_path(r'^add_encashment/$', add_encashment, name='sklad_add_encashment'),
    # re_path(r'^del_encashment/$', delete_encashment, name='sklad_del_encashment'),

]
