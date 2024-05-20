from django.conf import settings
from django.urls import re_path
from campaign.views import view_online, subscribe, unsubscribe, preview_template

urlpatterns = [
    re_path(r'^view/(?P<object_id>[\d]+)/$', view_online, {}, name="campaign_view_online"),
    re_path(r'^preview_template/(?P<object_id>[\d]+)/$', preview_template, name="campaign_preview_template"),
]

if getattr(settings, 'CAMPAIGN_SUBSCRIBE_CALLBACK', None):
    urlpatterns += [
        re_path(r'^subscribe/$', subscribe, {}, name="campaign_subscribe"),
    ]

if getattr(settings, 'CAMPAIGN_UNSUBSCRIBE_CALLBACK', None):
    urlpatterns += [
        re_path(r'^unsubscribe/$', unsubscribe, {}, name="campaign_unsubscribe"),
    ]
