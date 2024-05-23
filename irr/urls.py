# -*- coding: utf-8 -*-
from django.conf.urls import *
from django.urls import re_path
from core.views import static
from irr import views
from kostochka38 import settings

urlpatterns = [
    re_path(r'^create/$', views.create_xml)
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)