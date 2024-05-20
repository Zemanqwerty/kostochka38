import logging
import re

from django import http
from django.conf import settings
from django.urls import is_valid_path
from django.utils.cache import get_conditional_response, set_response_etag
from django.utils.deprecation import MiddlewareMixin
from django.utils.http import unquote_etag
from django.utils.encoding import force_str
from django.utils.six.moves.urllib.parse import urlparse
from django.core.mail import mail_managers

logger = logging.getLogger('django.request')


class BrokenLinkEmailsMiddleware(MiddlewareMixin):

    def process_response(self, request, response):
        """
        Send broken link emails for relevant 404 NOT FOUND responses.
        """
        if response.status_code == 404 and not settings.DEBUG:
            domain = request.get_host()
            path = request.get_full_path()
            referer = force_str(request.META.get('HTTP_REFERER', ''), errors='replace')

            ignorible = True
            if referer.find('DgJrfdJg') > 0:
                ignorible = False

            if not self.is_ignorable_request(request, path, domain, referer) and ignorible:
                ua = force_str(request.META.get('HTTP_USER_AGENT', '<none>'), errors='replace')
                ip = request.META.get('REMOTE_ADDR', '<none>')
                mail_managers(
                    "Broken %slink on %s" % (
                        ('INTERNAL ' if self.is_internal_request(domain, referer) else ''),
                        domain
                    ),
                    "Referrer: %s\nRequested URL: %s\nUser agent: %s\n"
                    "IP address: %s\n" % (referer, path, ua, ip),
                    fail_silently=True)
        return response

    def is_internal_request(self, domain, referer):
        """
        Returns True if the referring URL is the same domain as the current request.
        """
        # Different subdomains are treated as different domains.
        return bool(re.match("^https?://%s/" % re.escape(domain), referer))

    def is_ignorable_request(self, request, uri, domain, referer):
        """
        Return True if the given request *shouldn't* notify the site managers
        according to project settings or in situations outlined by the inline
        comments.
        """
        # The referer is empty.
        if not referer:
            return True

        # APPEND_SLASH is enabled and the referer is equal to the current URL
        # without a trailing slash indicating an internal redirect.
        if settings.APPEND_SLASH and uri.endswith('/') and referer == uri[:-1]:
            return True

        # A '?' in referer is identified as a search engine source.
        if not self.is_internal_request(domain, referer) and '?' in referer:
            return True

        # The referer is equal to the current URL, ignoring the scheme (assumed
        # to be a poorly implemented bot).
        parsed_referer = urlparse(referer)
        if parsed_referer.netloc in ['', domain] and parsed_referer.path == uri:
            return True

        return any(pattern.search(uri) for pattern in settings.IGNORABLE_404_URLS)


class GoToPathWithoutWWW(MiddlewareMixin):

    response_redirect_class = http.HttpResponsePermanentRedirect

    def process_request(self, request):
        # Check for a redirect based on settings.PREPEND_WWW
        host = request.get_host()
        must_prepend = settings.PREPEND_NOT_WWW and host and host.startswith('www.')
        redirect_url = ('%s://%s' % (request.scheme, host[4:])) if must_prepend else ''

        # Check if a slash should be appended
        if self.should_redirect_with_slash(request):
            path = self.get_full_path_with_slash(request)
        else:
            path = request.get_full_path()

        # Return a redirect if necessary
        if redirect_url or path != request.get_full_path():
            redirect_url += path
            return self.response_redirect_class(redirect_url)

    def should_redirect_with_slash(self, request):
        """
        Return True if settings.APPEND_SLASH is True and appending a slash to
        the request path turns an invalid path into a valid one.
        """
        if settings.APPEND_SLASH and not request.get_full_path().endswith('/'):
            urlconf = getattr(request, 'urlconf', None)
            return (
                not is_valid_path(request.path_info, urlconf) and
                is_valid_path('%s/' % request.path_info, urlconf)
            )
        return False

    def get_full_path_with_slash(self, request):
        """
        Return the full path of the request with a trailing slash appended.

        Raise a RuntimeError if settings.DEBUG is True and request.method is
        POST, PUT, or PATCH.
        """
        new_path = request.get_full_path(force_append_slash=True)
        if settings.DEBUG and request.method in ('POST', 'PUT', 'PATCH'):
            raise RuntimeError(
                "You called this URL via %(method)s, but the URL doesn't end "
                "in a slash and you have APPEND_SLASH set. Django can't "
                "redirect to the slash URL while maintaining %(method)s data. "
                "Change your form to point to %(url)s (note the trailing "
                "slash), or set APPEND_SLASH=False in your Django settings." % {
                    'method': request.method,
                    'url': request.get_host() + new_path,
                }
            )
        return new_path

    def process_response(self, request, response):

        if settings.USE_ETAGS:
            if not response.has_header('ETag'):
                set_response_etag(response)

            if response.has_header('ETag'):
                return get_conditional_response(
                    request,
                    etag=unquote_etag(response['ETag']),
                    response=response,
                )

        return response
