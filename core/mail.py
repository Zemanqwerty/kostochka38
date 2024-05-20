# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.mail import EmailMessage, EmailMultiAlternatives
from core.models import Mail, Token
from mailer import send_html_mail
from django.template import engines
from sendgrid import SendGridAPIClient


def htmlmail_sender(link, data, to, user=None):
    if to is not None:
        mail = Mail.objects.get(link=link)
        if user is not None and mail.notificationsettings_set.filter(user_id=user.id, send=False).exists():
            return
        subject_template = engines['django'].from_string(mail.subject)
        subject_context = data
        subject = subject_template.render(subject_context).encode('utf-8')

        if user is not None:
            token = Token.generate_token(user)
            data.update({
                'token': token.token,
            })
        message_template = engines['django'].from_string(mail.body)
        message_context = data
        message = message_template.render(message_context).encode('utf-8')

        if not settings.LOCAL:
            # try:
            # htmlmail = EmailMessage(subject, message, settings.SENDER_EMAIL, [to])

            send_html_mail(subject, subject, message, settings.SENDER_EMAIL, [to])

            # htmlmail.content_subtype = "html"
            # htmlmail.send()
            # except:
            #     pass