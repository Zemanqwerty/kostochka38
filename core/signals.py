# -*- coding: utf-8 -*-

from django.db.models.signals import pre_save
from django.dispatch import receiver

from core.models import Announcement


@receiver(pre_save, sender=Announcement, dispatch_uid='on_announcement_pre_save')
def on_announcement_pre_save(sender, instance, **kwargs):
    instance.hash = str(hash(instance.text))[:30]