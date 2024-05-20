# import logging
# from recommends.storages.djangoorm.storage import DjangoOrmStorage
# from recommends.settings import RECOMMENDS_LOGGER_NAME
# from recommends.storages.djangoorm.models import Recommendation


# logger = logging.getLogger(RECOMMENDS_LOGGER_NAME)


# class DjangoStorage(DjangoOrmStorage):
#     def get_recommendations_for_user(self, user, limit=10, raw_id=False, object_site_id=None):
#         if object_site_id is None:
#             object_site_id = self.settings.SITE_ID
#         qs = Recommendation.objects.filter(
#             user=user.id,
#             object_site=object_site_id,
#             recommendations__active=True,
#         ).order_by('-score')
#         if raw_id:
#             qs = qs.extra(
#                 select={'contect_type_id': 'object_ctype_id'}).values(
#                     'object_id', 'contect_type_id'
#                 )
#         return qs[:limit]
