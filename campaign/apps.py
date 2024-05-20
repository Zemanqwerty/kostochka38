from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class CampaignConfig(AppConfig):
    name = 'campaign'
    verbose_name = _("campaign management")
