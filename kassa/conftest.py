import pytest

from django.conf import settings

import os


@pytest.fixture(scope='session')
def django_db_setup():
    DB_USER = os.getenv('DB_USER')
    DB_PASS = os.getenv('DB_PASS')
    DB_HOST = os.getenv('DB_HOST')
    DB_NAME = os.getenv('DB_NAME')
    DB_PORT = os.getenv('DB_PORT')
    DB_PORT = 3306

    settings.DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'db',
            'USER': 'root',
            'PASSWORD': 'root',
            'HOST': 'db',
            'PORT': '3306',
            'OPTIONS': {
                'init_command': 'SET default_storage_engine=INNODB, foreign_key_checks = 0',
                'charset': 'utf8',
            },
            'TEST': {
                'NAME': 'db',
            }
        }
    }

    # settings.DATABASES = {
    # 'default': {
    #     'ENGINE': 'django.db.backends.postgresql_psycopg2',
    #     'NAME': 'db',
    #     'USER': 'root',
    #     'PASSWORD': 'root',
    #     'HOST': 'dbpg',
    #     'PORT': '5432',
    # }
    # }