# coding=utf-8
from __future__ import unicode_literals

import logging

from django import template, http
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.contrib.sites.models import Site
from django.core.exceptions import ImproperlyConfigured

from campaign.models import Campaign, BlacklistEntry, MailTemplate
from campaign.forms import SubscribeForm, UnsubscribeForm
from campaign.utils import group_by_two, get_item_cell


logger = logging.getLogger(__name__)


def preview_template(request, object_id):
    """
    Превью шаблона
    """
    campaign = Campaign.objects.filter(id=int(object_id)).first()  # type: Campaign
    items = campaign.template.itemmail_set.all()
    not_rendered_content = campaign.template.html
    items_tag = "{{ items }}"
    if items_tag in not_rendered_content:
        new_string = u"""
        <table align="center" border="0" cellpadding="0" cellspacing="0"><tr><td style="padding: 5px 10px;"><table cellspacing="20">
        """
        for left_item, right_item in group_by_two(items):
            new_string += u"""
            <tr>
            <td style="width: 50%; border: 1px #e5e5e5 solid; border-radius: 5px; vertical-align:top; padding: 20px 10px;">{}</td>
            <td style="width: 50%; border: 1px #e5e5e5 solid; border-radius: 5px; vertical-align:top; padding: 20px 10px;">{}</td>
            </tr>
            """.format(get_item_cell(left_item.item), get_item_cell(right_item.item) if right_item is not None else '')
            pass
        new_string += "</table></td></tr></table>"
        not_rendered_content = not_rendered_content.replace(items_tag, new_string)
    _template = template.Template(not_rendered_content)
    context = template.Context({"items": items})
    content = _template.render(context)
    return HttpResponse(content)


def view_online(request, object_id):
    campaign = get_object_or_404(Campaign, pk=object_id, online=True)

    if campaign.template.html is not None and \
        campaign.template.html != "" and \
        not request.GET.get('txt', False):
        tpl = template.Template(campaign.template.html)
        content_type = 'text/html; charset=utf-8'
    else:
        tpl = template.Template(campaign.template.plain)
        content_type = 'text/plain; charset=utf-8'
    context = template.Context({})
    if campaign.online:
        context.update({'view_online_url': reverse("campaign_view_online", kwargs={
                        'object_id': campaign.pk}),
                        'viewed_online': True,
                        'site_url': Site.objects.get_current().domain})
    return http.HttpResponse(tpl.render(context),
                            content_type=content_type)


def subscribe(request, template_name='campaign/subscribe.html',
              form_class=SubscribeForm, extra_context=None):
    context = extra_context or {}
    if request.method == 'POST':
        form = form_class(request.POST)
        if form.is_valid():
            callback = _get_callback('CAMPAIGN_SUBSCRIBE_CALLBACK')
            if callback:
                success = callback(form.cleaned_data['email'])
                context.update({'success': success, 'action': 'subscribe'})
            else:
                raise ImproperlyConfigured("CAMPAIGN_SUBSCRIBE_CALLBACK must be configured to use the subscribe view")
    else:
        form = form_class()
    context.update({'form': form})
    return render(request, template_name, context)


def unsubscribe(request, template_name='campaign/unsubscribe.html',
                form_class=UnsubscribeForm, extra_context=None):
    context = extra_context or {}
    if request.method == 'POST':
        form = form_class(request.POST)
        if form.is_valid():
            callback = _get_callback('CAMPAIGN_UNSUBSCRIBE_CALLBACK')
            if callback:
                success = callback(form.cleaned_data['email'])
                context.update({'success': success, 'action': 'unsubscribe'})
            else:
                raise ImproperlyConfigured("CAMPAIGN_UNSUBSCRIBE_CALLBACK must be configured to use the unsubscribe view")
    else:
        initial = {}
        if request.GET.get('email'):
            initial['email'] = request.GET.get('email')
        form = form_class(initial=initial)
    context.update({'form': form})
    return render(request, template_name, context)


def _get_callback(setting):
    callback = getattr(settings, setting, None)
    if callback is None:
        return None
    if callable(callback):
        return callback
    else:
        mod, name = callback.rsplit('.', 1)
        module = __import__(mod, {}, {}, [''])
        return getattr(module, name)
