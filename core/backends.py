# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model

from django.contrib.auth.models import User
from core.models import Token


class AuthenticationTokenBackend(object):

    def authenticate(self, token):
        UserModel = get_user_model()
        try:
            token = Token.objects.get(token=token)
            user = UserModel._default_manager.get(username=token.user.username)
            return user
        except Token.DoesNotExist:
            return None
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        UserModel = get_user_model()
        try:
            return UserModel._default_manager.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None