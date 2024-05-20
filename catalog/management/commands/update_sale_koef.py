from django.core.management import BaseCommand
from django.utils import timezone

from catalog.models import InsideZakaz, SaleTable


class Command(BaseCommand):
    def handle(self, *args, **options):
        for zakaz in InsideZakaz.objects.all():
            zakaz.sale_koef = 100 - (zakaz.sale_koef * 100)
            zakaz.save()
        for table in SaleTable.objects.all():
            table.value = 100 - (table.value * 100)
            table.save()