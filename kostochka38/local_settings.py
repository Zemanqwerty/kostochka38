DEBUG = True
COMPRESS_ENABLED = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'db',
        'USER': 'root',
        # 'PASSWORD': 'root',
        'HOST': '127.0.0.1',
        'OPTIONS': {
            'init_command': 'SET default_storage_engine=INNODB, foreign_key_checks = 0',
            'charset': 'utf8',
        },
    }
}
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql_psycopg2',
#         'NAME': 'db',
#         'USER': 'root',
#         'PASSWORD': 'root',
#         'HOST': 'dbpg',
#         'PORT': '5432',
#     }
# }
