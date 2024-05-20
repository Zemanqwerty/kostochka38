# from recommends.providers import recommendation_registry
# from recommends.settings import RECOMMENDS_CACHE_TEMPLATETAGS_TIMEOUT
# from catalog.models import ZakazGoods
# from django import template
# from django.core.cache import cache
# from django.conf import settings
# from django.db import models
# register = template.Library()


# pass
# @register.filter
# def similarities_bought(obj, limit=4):
#     """
#     Returns a list of Similarity objects, representing how much an object is similar to the given one.

#     Usage:

#     ::

#         {% for similarity in myobj|similarities_bought:5 %}
#             {{ similarity.related_object }}
#         {% endfor %}
#     """
#     if isinstance(obj, models.Model):
#         cache_key = 'recommends:similarities:%s:%s.%s:%s:%s' % (settings.ALSO_BUY_SITE_ID, obj._meta.app_label, obj._meta.object_name.lower(), obj.id, limit)
#         similarities = cache.get(cache_key)
#         if similarities is None:
#             provider = recommendation_registry.get_provider_for_vote(ZakazGoods)
#             similarities = provider.storage.get_similarities_for_object(obj, int(limit))
#             cache.set(cache_key, similarities, RECOMMENDS_CACHE_TEMPLATETAGS_TIMEOUT)
#         return similarities
