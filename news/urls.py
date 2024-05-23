from django.conf.urls import *
from django.urls import re_path
from news import views

urlpatterns = [
    re_path(r'^$', views.news, name='news'),
    re_path(r'^comment-add-complete/$', views.static_information),
    re_path(r'^(?P<link>.+)/$', views.news_inner, name='news_inner')
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)