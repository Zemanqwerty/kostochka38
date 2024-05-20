from django import template


register = template.Library()


@register.simple_tag
def modify_pagination_path(full_path, key, value):
    get_params = None
    if full_path.find('?') > -1:
        get_params = full_path[full_path.find('?')+1:]
    if full_path.find('#') > -1:
        get_params = full_path[:full_path.find('#')]
    if get_params is not None:
        params = dict(map(lambda p: tuple(p.split('=')), get_params.split('&')))
        params[key] = value
        return '&'.join(map(lambda k: '%s=%s' % (k, params[k]), params))
    return '%s=%s' % (key, value)