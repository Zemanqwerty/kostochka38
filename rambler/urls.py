# -*- coding: utf-8 -*-
from django.conf.urls import *
from django.urls import re_path
from core.views import static
from kostochka38 import settings
from rambler import views

urlpatterns = [
    re_path(r'^create/$', views.create_yml)
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)