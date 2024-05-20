# -*- coding: utf-8 -*-
import logging

from campaign.models import Campaign
from django.conf import settings
from mailer import send_html_mail
from campaign.backends.base import BaseBackend
from django import template
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from campaign.context import MailContext
from campaign.utils import group_by_two, get_item_cell

logger = logging.getLogger(__name__)


class DjangoMailerBackend(BaseBackend):
    """simple backend using django-mailer to queue and send the mails"""

    def send_campaign(self, campaign, fail_silently=False):
        #  type: (Campaign, bool) -> None
        """
        Does the actual work
        """
        from campaign.models import BlacklistEntry

        subject = campaign.template.subject
        text_template = template.Template(campaign.template.plain)
        if campaign.template.html is not None and campaign.template.html != u"":
            items = campaign.template.itemmail_set.all()
            not_rendered_content = campaign.template.html
            items_tag = u"{{ items }}"
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
                            """.format(get_item_cell(left_item.item),
                                       get_item_cell(right_item.item) if right_item is not None else '')
                    pass
                new_string += u"</table></td></tr></table>"
                not_rendered_content = not_rendered_content.replace(items_tag, new_string)
            html_template = template.Template(not_rendered_content)

        sent = 0
        used_addresses = []
        for recipient_list in campaign.recipients.all():
            for recipient in recipient_list.object_list():
                # never send mail to blacklisted email addresses
                recipient_email = getattr(recipient, recipient_list.email_field_name)
                if not recipient.unsubscribed and recipient_email and not recipient_email in used_addresses:
                    msg = EmailMultiAlternatives(subject, to=[recipient_email, ])
                    context = MailContext(recipient)
                    # if campaign.online:
                    context.update({'view_online_url': reverse("campaign_view_online", kwargs={'object_id': campaign.pk}),
                                    'site_url': Site.objects.get_current().domain,
                                    'recipient_email': recipient_email, 'recipient_id': recipient.id,
                                    'name': recipient.first_name, 'cid': campaign.id})
                    msg.body = text_template.render(context)
                    html_content = ''
                    if campaign.template.html is not None and campaign.template.html != u"":
                        html_content = html_template.render(context)
                        msg.attach_alternative(html_content, 'text/html')

                    sent += send_html_mail(subject, msg.body, html_content,
                                           settings.DEFAULT_FROM_EMAIL, msg.to, fail_silently=fail_silently)
                    used_addresses.append(recipient_email)
        return sent

    def send_mail(self, email, fail_silently=False):
        subject = email.subject
        body = email.body

        send_html_mail(
            subject, body, email.alternatives[0], settings.DEFAULT_FROM_EMAIL, email.recipients(),
            fail_silently=fail_silently
        )
        return 1


backend = DjangoMailerBackend()
