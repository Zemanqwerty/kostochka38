from django import template


register = template.Library()


@register.filter
def escape_unicode(string):
    return string.encode('utf-8').decode('unicode-escape')