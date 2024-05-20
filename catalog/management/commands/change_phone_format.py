from django.core.management import BaseCommand
from catalog.models import Account
from catalog.utils import is_digit

import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):
        users = Account.objects.all()
        wrong_phone = list()
        for user in users:
            if not user.phone:
                continue
            if len(str(user.phone)) < 12:
                wrong_phone.append(user)
                continue
            new_phone = ""
            for char in user.phone:
                if is_digit(char):
                    new_phone += char
            user.phone = new_phone
            user.save()
        logger.warning(wrong_phone)
