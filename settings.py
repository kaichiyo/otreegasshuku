from os import environ

SESSION_CONFIGS = [
    dict(
       name = 'TD',
       display_name = "旅人のジレンマゲーム",
       num_demo_participants = 4,
       app_sequence = ['travelers_dilemma']
   )  
]

# if you set a property in SESSION_CONFIG_DEFAULTS, it will be inherited by all configs
# in SESSION_CONFIGS, except those that explicitly override it.
# the session config can be accessed from methods in your apps as self.session.config,
# e.g. self.session.config['participation_fee']

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1.00, participation_fee=0.00, doc=""
)

PARTICIPANT_FIELDS = []
SESSION_FIELDS = []

# ISO-639 code
# for example: de, fr, ja, ko, zh-hans
LANGUAGE_CODE = 'ja'

# e.g. EUR, GBP, CNY, JPY
REAL_WORLD_CURRENCY_CODE = 'JPY'
USE_POINTS = True

import os
DATABASE_URL = os.environ.get('DATABASE_URL')
db_engine = 'postgresql' if DATABASE_URL else 'sqlite3'
DATABASES = {
    'default': {
        'ENGINE': f'django.db.backends.{db_engine}',
        'NAME': 'db.sqlite3',
        'OPTIONS': {
            'url': DATABASE_URL,
            'conn_max_age': 500,
        }
    }
}

ADMIN_USERNAME = 'admin'
# for security, best to set admin password in an environment variable
ADMIN_PASSWORD = os.environ.get('OTREE_ADMIN_PASSWORD')
OTREE_AUTH_LEVEL = os.environ.get('OTREE_AUTH_LEVEL')

DEMO_PAGE_INTRO_HTML = """ """

SECRET_KEY = '3382438676643'
