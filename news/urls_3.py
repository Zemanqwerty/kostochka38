from django.conf.urls import *
from django.urls import re_path
from news import views

urlpatterns = [
    re_path(r'^$', views.article, name='article'),
    re_path(r'^comment-add-complete/$', views.static_information_2),
    re_path(r'^(?P<link>.+)/$', views.article_inner)
]

