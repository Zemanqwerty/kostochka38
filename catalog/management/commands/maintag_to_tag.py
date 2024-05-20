# -*- coding: utf-8 -*-
from catalog.models import Deckitem
from django.core.management.base import BaseCommand
from django.db.models.expressions import F


class Command(BaseCommand):

    def handle(self, *args, **options):
        print('List of deckitem id:')
        for item in Deckitem.objects.exclude(tags__id=F('maintag')).distinct().values('id'):
            print(item['id'])
