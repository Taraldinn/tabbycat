import logging
import os

import dj_database_url
from .core import TABBYCAT_VERSION

# ==============================================================================
# Render per https://render.com/docs/deploy-django
# ==============================================================================

if os.environ.get('TAB_DIRECTOR_EMAIL', ''):
    TAB_DIRECTOR_EMAIL = os.environ.get('TAB_DIRECTOR_EMAIL')

if os.environ.get('DJANGO_SECRET_KEY', ''):
    SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')

# https://docs.djangoproject.com/en/3.0/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ['*']

# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# NOTE: Do NOT set SECURE_SSL_REDIRECT=True with Daphne/ASGI on Render.
# Render's reverse proxy already enforces HTTPS. Setting it in Django causes
# AssertionError in SecurityMiddleware's ASGI scope handling.
# We still set the cookie flags since Render is always HTTPS.
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# ==============================================================================
# Multi-tenancy
# ==============================================================================

MULTI_TENANT_MODE = os.environ.get('MULTI_TENANT_MODE', 'true').lower() in ('true', '1', 'yes')
TABBYCAT_BASE_DOMAIN = os.environ.get('TABBYCAT_BASE_DOMAIN', 'tabbycatbd.com')
TENANT_BASE_DOMAIN = os.environ.get('TENANT_BASE_DOMAIN', TABBYCAT_BASE_DOMAIN)

CSRF_TRUSTED_ORIGINS = []
if RENDER_EXTERNAL_HOSTNAME:
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_EXTERNAL_HOSTNAME}")
if TABBYCAT_BASE_DOMAIN:
    CSRF_TRUSTED_ORIGINS.extend([
        f"https://{TABBYCAT_BASE_DOMAIN}",
        f"https://*.{TABBYCAT_BASE_DOMAIN}",
    ])
if TENANT_BASE_DOMAIN and TENANT_BASE_DOMAIN != TABBYCAT_BASE_DOMAIN:
    CSRF_TRUSTED_ORIGINS.extend([
        f"https://{TENANT_BASE_DOMAIN}",
        f"https://*.{TENANT_BASE_DOMAIN}",
    ])
if os.environ.get('CSRF_TRUSTED_ORIGINS'):
    CSRF_TRUSTED_ORIGINS.extend(
        origin.strip() for origin in os.environ['CSRF_TRUSTED_ORIGINS'].split(',') if origin.strip()
    )

# ==============================================================================
# Postgres
# ==============================================================================

DATABASES = {
    'default': dj_database_url.config(
        default='postgresql://postgres:postgres@localhost:5432/tabbycat',
        conn_max_age=600,
    )
}

# ==============================================================================
# Redis
# ==============================================================================

REDIS_URL = os.environ.get('REDIS_URL')

if REDIS_URL:
    USE_REDIS = True
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "SOCKET_CONNECT_TIMEOUT": 5,
                "SOCKET_TIMEOUT": 60,
                "IGNORE_EXCEPTIONS": True,  # Don't crash on ConnectionError at limit
            },
        },
    }

    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [REDIS_URL],
                # Remove channels from groups after 3 hours
                "group_expiry": 10800,
            },
        },
    }

# ==============================================================================
# Email
# ==============================================================================

if os.environ.get('EMAIL_HOST', ''):
    SERVER_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@tabbycatbd.com')
    DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@tabbycatbd.com')
    EMAIL_HOST = os.environ['EMAIL_HOST']
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
    EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'true').lower() == 'true'

elif os.environ.get('SENDGRID_API_KEY', ''):
    SERVER_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@tabbycatbd.com')
    DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@tabbycatbd.com')
    EMAIL_HOST = 'smtp.sendgrid.net'
    EMAIL_HOST_USER = 'apikey'
    EMAIL_HOST_PASSWORD = os.environ['SENDGRID_API_KEY']
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True

# ==============================================================================
# Sentry
# ==============================================================================

_sentry_dsn = os.environ.get('SENTRY_DSN', '')
if not os.environ.get('DISABLE_SENTRY') and _sentry_dsn:
    import sentry_sdk
    from sentry_sdk.integrations.logging import LoggingIntegration
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.redis import RedisIntegration

    DISABLE_SENTRY = False
    sentry_sdk.init(
        dsn=_sentry_dsn,
        integrations=[
            DjangoIntegration(),
            LoggingIntegration(event_level=logging.WARNING),
            RedisIntegration(),
        ],
        send_default_pii=True,
        release=TABBYCAT_VERSION,
    )

