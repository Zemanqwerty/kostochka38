# -*- coding: utf-8 -*-
from django.conf.urls import *
from django.urls import re_path
from rambler import views

urlpatterns = [
    re_path(r'^create/$', views.create_yml)
]