import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = os.environ.get('DEBUG', '1') == '1'

SECRET_KEY = os.environ.get('SECRET_KEY', '')
if not SECRET_KEY:
    # Fail loudly rather than serve production traffic on a key that is in git.
    if not DEBUG:
        raise ImproperlyConfigured('SECRET_KEY must be set when DEBUG is off')
    SECRET_KEY = 'dev-only-insecure-key'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Browser origins allowed to call the API. The Nuxt dev server by default; a Capacitor
# build (capacitor://localhost) and the production origin get added here via the env var.
CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', 'http://localhost:3000').split(',')

# The Google Cloud web client the sign-in button is configured with. Empty is a supported
# state — the dev-token path still signs you in, and the login screen renders no Google
# button without it. core/google_auth.py refuses to verify anything while it is unset.
# One id today; the Capacitor build signs in with its own Android/iOS client id, and this
# becomes the list of audiences we accept.
GOOGLE_OAUTH_CLIENT_ID = os.environ.get('GOOGLE_OAUTH_CLIENT_ID', '')

# The Dramatiq broker the worker and scheduler share with the api. Compose's own service
# name is the default, so a dev machine needs nothing in .env; feedme/broker.py reads it.
REDIS_URL = os.environ.get('REDIS_URL', 'redis://redis:6379/0')

INSTALLED_APPS = [
    'core',
    'corsheaders',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    # Must stay first: middleware runs top-down, and anything that returns a
    # response before this one runs sends it back without the CORS headers.
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'feedme.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'feedme.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB', 'feedme'),
        'USER': os.environ.get('POSTGRES_USER', 'feedme'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'feedme'),
        'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
    }
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_TZ = True

STATIC_URL = 'static/'

AUTH_USER_MODEL = 'core.User'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
