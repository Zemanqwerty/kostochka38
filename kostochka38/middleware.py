# -*- coding: utf-8 -*-

from django.conf import settings
from django.shortcuts import render
from django.template.context import RequestContext

ALLOWED_BROWSERS = (
    ('Firefox', 3.6),
    ('Opera', 9),
    ('MSIE', 9),
    ('Safari', 85),
)


def check_browser(agent):
    for b in ALLOWED_BROWSERS:
        try:
            loc = agent.find(b[0])
            if loc != -1:
                start = loc + len(b[0]) + 1
                end = agent.find(' ', start)
                if end != -1:
                    version = agent[start:end]
                else:
                    version = agent[start:]
                if version == '':
                    version = '2.0'
                elif version[-1] == ';':
                    version = version[0:-1]
                version = version.split('.')
                version = "%s.%s" % (
                    version[0].split(')')[0], ''.join(version[1:]).split(',')[0].split('+')[0].split('u')[0].split('a')[0])
                if float(version.strip('"')) < float(b[1]):
                    valid = False
                else:
                    valid = True
                ec = {'browser_version': version, 'browser': b[0], 'valid': valid}
                return ec
        except:
            pass

    return {'browser': agent, 'browser_version': '', 'valid': True}


class ValidateBrowser(object):
    def process_response(self, request, response):
        if '_verify_browser' in request.COOKIES or request.META[
            'HTTP_USER_AGENT'] == 'Python-urllib/1.16' or request.GET.get('skipcheck', False) or request.META[
            'HTTP_USER_AGENT'].find('Googlebot') != -1:
            return response

        agent = request.META['HTTP_USER_AGENT']
        ec = check_browser(agent)
        if ec['valid']:
            response.set_cookie('_verify_browser', '1', max_age=60 * 60 * 24 * 30, domain=settings.SESSION_COOKIE_DOMAIN)
            return response

        response = render(request, 'browsers.html', {})
        return response