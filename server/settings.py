"""
Django settings for server project.

Generated by 'django-admin startproject' using Django 4.1.3.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""

import logging
import mimetypes
import tomli

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

with open(BASE_DIR / "server/.env", "rb") as config_p:
    config = tomli.load(config_p)

DJANGO_MODE = config["mode"]

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-v$rywutoth&6+v8&_#t@_7l*d=k-u^lnx@1)f(o9rs(2pu=i=n"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config[DJANGO_MODE]["Debug"]

if DJANGO_MODE == "dev":
    DATA_HOME = BASE_DIR / "datadir/releases/current/"
else:
    DATA_HOME = "/data/arpah/releases/current/"

ALLOWED_HOSTS = ["middleware", "127.0.0.1", "localhost"]

APPEND_SLASH = False

AUTH_USER_MODEL = "users.User"

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://smart-feast",
    "https://feast.mgpc.biochemistry.gwu.edu",
]

# CORS_ORIGIN_ALLOW_ALL = True

CORS_EXPOSE_HEADERS = ["Content-Type", "X-CSRFToken"]
CORS_ALLOW_HEADERS = [
    "X-CSRFToken",
    "Content-Type",
    "Cache-Control",
    "Authorization",
    "Iss-Oauth",
]
CORS_ALLOW_CREDENTIALS = True

CSRF_COOKIE_SAMESITE = "Strict"
SESSION_COOKIE_SAMESITE = "Strict"
# Production values
# CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_HTTPONLY = True
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "https://feast.mgpc.biochemistry.gwu.edu",
]

# LOGIN_URL = "https://feast.mgpc.biochemistry.gwu.edu/gw-feast/callback/"
# LOGIN_URL = "https://feast.mgpc.biochemistry.gwu.edu/dsviewer/login/"
LOGIN_URL = "http://localhost:3000/gw-feast/callback/"

if DEBUG:
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
            },
        },
        "root": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
    }

# Handle MIMEtypes
mimetypes.add_type("text/css", ".css", True)
mimetypes.add_type("application/javascript", ".js", True)

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "oauth2_provider",
    "corsheaders",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "ui.apps.UiConfig",
    "users.apps.UsersConfig",
    "data_api.apps.DataApiConfig",
]

logger = logging.getLogger()


def get_rsa_key():
    with open("oidc.key", "r") as key_p:
        return "".join(key_p.readlines())


# This is questionable:
# c.f. https://django-oauth-toolkit.readthedocs.io/en/latest/changelog.html#warning
# & https://stackoverflow.com/a/72186730
OAUTH2_PROVIDER = {
    "PKCE_REQUIRED": True,
    "OAUTH2_BACKEND_CLASS": "oauth2_provider.oauth2_backends.JSONOAuthLibCore",
    "OIDC_ENABLED": True,
    "OIDC_ISS_ENDPOINT": "https://feast.mgpc.biochemistry.gwu.edu/testing-ui/oauth",
    "OIDC_RSA_PRIVATE_KEY": get_rsa_key(),
    "ACCESS_TOKEN_EXPIRE_SECONDS": 3600 * 10000,  # 10000 hours should suffice
    "ID_TOKEN_EXPIRE_SECONDS": 3600 * 10000,  # Ditto
    "SCOPES": {
        "openid": "OpenID Connect scope",
        "read": "Read scope",
        "write": "Write scope",
        "groups": "Access to your groups",
        "patient/*": "Access to in-group patient records",
    },
}

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "oauth2_provider.middleware.OAuth2TokenMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# NB: Include the backends! See e.g.
# https://stackoverflow.com/q/28178767
# ...or, as typical, RTM (to completion...):
# https://django-oauth-toolkit.readthedocs.io/en/latest/tutorial/tutorial_03.html#setup-a-provider
AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "oauth2_provider.backends.OAuth2Backend",
)

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "oauth2_provider.contrib.rest_framework.OAuth2Authentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        # "rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly",
        # "rest_framework.authentication.BasicAuthentication",
        # "rest_framework.authentication.SessionAuthentication",
    ],
}

ROOT_URLCONF = "server.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "server.wsgi.application"

# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / STATIC_URL
# STATICFILES_DIRS = [
#     BASE_DIR / "static",
#     BASE_DIR / "static/assets",
# ]
MEDIA_ROOT = "static/assets/"
# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
