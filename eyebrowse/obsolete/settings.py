import os
import django.contrib.auth

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Zamiang', 'brennanmoore@gmail.com'),
    )
MANAGERS = ADMINS

DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = 'ghaad.sqlite'
DATABASE_USER = ''
DATABASE_PASSWORD = '' 
DATABASE_HOST = ''
DATABASE_PORT = ''

TIME_ZONE = 'America/New_York'
LANGUAGE_CODE = 'en-us'
SITE_ID = 1
USE_I18N = True

#MEDIA_ROOT = '/Users/brennanmoore/ghaad/lib/'
UPLOAD_DIR = '/Users/brennanmoore/ghaad/uploads/'
#UPLOAD_DIR = '/uploads/'

#MEDIA_URL = 'http://localhost:8000/lib/'
#ADMIN_MEDIA_PREFIX = '/lib/'

SECRET_KEY = '*nqvav0sb*8xp=ysext=8m+j9%%htn2jn8&5sva#amahnzurqh'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
#    'django.middleware.cache.CacheMiddleware',
)

ROOT_URLCONF = 'ghaad.urls'

TEMPLATE_DIRS = (
    os.path.join(os.path.dirname(__file__), 'templates'),    
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'ghaad',
)

django.contrib.auth.LOGIN_URL = '/login/'

# EMAIL
SITE_HOST = '127.0.0.1:8000'
DEFAULT_FROM_EMAIL = 'Django Bookmarks <foo@example.com>'
EMAIL_HOST = 'mail.yourisp.com'
EMAIL_PORT = ''
EMAIL_HOST_USER = 'username+mail.yourisp.com'
EMAIL_HOST_PASSWORD = ''
