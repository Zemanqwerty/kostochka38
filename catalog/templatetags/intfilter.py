from django import template
import re
from django.utils.encoding import force_str

register = template.Library()

@register.filter('intspace')
def intspace(value):
    """
    Converts an integer to a string containing spaces every three digits.
    For example, 3000 becomes '3 000' and 45000 becomes '45 000'.
    See django.contrib.humanize app
    """
    orig = force_str(value)
    new = re.sub("^(-?\d+)(\d{3})", '\g<1> \g<2>', orig)
    if orig == new:
        return new
    else:
        return intspace(new)


@register.filter(name='format_numbers')
def format_numbers(phone_number):
    numbers = list(filter(str.isdigit, str(phone_number)))[1:]
    return "+7({}{}{}){}{}{}-{}{}-{}{}".format(*numbers)
