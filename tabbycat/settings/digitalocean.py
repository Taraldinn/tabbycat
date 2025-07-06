import logging
from os import environ
import dj_database_url
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.redis import RedisIntegration

from .core import TABBYCAT_VERSION

# ==============================================================================
# DigitalOcean App Platform Configuration
# ==============================================================================

# Store Tab Director Emails for reporting purposes
if environ.get('TAB_DIRECTOR_EMAIL', ''):
    TAB_DIRECTOR_EMAIL = environ.get('TAB_DIRECTOR_EMAIL')

if environ.get('DJANGO_SECRET_KEY', ''):
    SECRET_KEY = environ.get('DJANGO_SECRET_KEY')

# Allow all host headers (DigitalOcean handles SSL termination)
ALLOWED_HOSTS = ['*']

# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Require HTTPS in production
if 'DJANGO_SECRET_KEY' in environ and environ.get('DISABLE_HTTPS_REDIRECTS', '') != 'disable':
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# ==============================================================================
# Database Configuration (External PostgreSQL)
# ==============================================================================

# Parse database configuration from $DATABASE_URL
DATABASES = {
    'default': dj_database_url.config(
        default='postgres://localhost',
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Ensure SSL is used for database connections
if 'sslmode' not in DATABASES['default']['OPTIONS']:
    DATABASES['default']['OPTIONS'] = {
        'sslmode': 'require',
    }

# ==============================================================================
# Redis Configuration
# ==============================================================================

# Redis configuration for caching and channels
REDIS_URL = environ.get('REDIS_URL', 'redis://localhost:6379')

# Parse Redis URL for different components
import urllib.parse
redis_url = urllib.parse.urlparse(REDIS_URL)

# Cache configuration using Redis
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 20,
                'retry_on_timeout': True,
            },
        },
        'KEY_PREFIX': 'tabbycat',
        'TIMEOUT': 300,
    }
}

# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# ==============================================================================
# Channels (WebSocket) Configuration
# ==============================================================================

# Channels configuration for WebSocket support
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [REDIS_URL],
            'capacity': 1500,
            'expiry': 10,
        },
    },
}

# ASGI application
ASGI_APPLICATION = 'asgi.application'

# ==============================================================================
# Logging Configuration
# ==============================================================================

# Enhanced logging for production
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': environ.get('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Add logging for all Tabbycat apps
from .core import TABBYCAT_APPS
for app in TABBYCAT_APPS:
    LOGGING['loggers'][app] = {
        'handlers': ['console'],
        'level': environ.get('DJANGO_LOG_LEVEL', 'INFO'),
        'propagate': False,
    }

# ==============================================================================
# Email Configuration (Optional)
# ==============================================================================

# Email configuration for notifications (configure as needed)
if environ.get('EMAIL_HOST'):
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = environ.get('EMAIL_HOST')
    EMAIL_PORT = int(environ.get('EMAIL_PORT', 587))
    EMAIL_USE_TLS = environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
    EMAIL_HOST_USER = environ.get('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = environ.get('EMAIL_HOST_PASSWORD', '')
    DEFAULT_FROM_EMAIL = environ.get('DEFAULT_FROM_EMAIL', TAB_DIRECTOR_EMAIL if 'TAB_DIRECTOR_EMAIL' in locals() else 'tabbycat@example.com')
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ==============================================================================
# Sentry Error Tracking (Optional)
# ==============================================================================

# Configure Sentry for error tracking
DISABLE_SENTRY = environ.get('DISABLE_SENTRY', '').lower() in ('true', '1', 'yes')

if not DISABLE_SENTRY and environ.get('SENTRY_DSN'):
    sentry_logging = LoggingIntegration(
        level=logging.INFO,        # Capture info and above as breadcrumbs
        event_level=logging.ERROR  # Send errors as events
    )
    
    sentry_sdk.init(
        dsn=environ.get('SENTRY_DSN'),
        integrations=[
            sentry_logging,
            DjangoIntegration(),
            RedisIntegration(),
        ],
        traces_sample_rate=0.1,
        send_default_pii=False,
        release=TABBYCAT_VERSION,
        environment='digitalocean-production',
    )

# ==============================================================================
# Performance Optimizations
# ==============================================================================

# Database connection pooling
DATABASES['default']['CONN_MAX_AGE'] = 600
DATABASES['default']['CONN_HEALTH_CHECKS'] = True

# Cache timeout settings
PUBLIC_FAST_CACHE_TIMEOUT = int(environ.get('PUBLIC_FAST_CACHE_TIMEOUT', 60 * 5))
PUBLIC_SLOW_CACHE_TIMEOUT = int(environ.get('PUBLIC_SLOW_CACHE_TIMEOUT', 60 * 15))
TAB_PAGES_CACHE_TIMEOUT = int(environ.get('TAB_PAGES_CACHE_TIMEOUT', 60 * 60))

# ==============================================================================
# Security Headers
# ==============================================================================

# Additional security headers
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

# ==============================================================================
# CORS Configuration
# ==============================================================================

# CORS settings for API access
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    # Add your frontend domains here if needed
]

# Allow credentials in CORS requests
CORS_ALLOW_CREDENTIALS = True

# ==============================================================================
# Static Files Configuration
# ==============================================================================

# WhiteNoise settings for static file serving
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = False
WHITENOISE_STATIC_PREFIX = '/static/'

# ==============================================================================
# Debug Configuration
# ==============================================================================

# Debug should be False in production
DEBUG = False
ENABLE_DEBUG_TOOLBAR = False

# ==============================================================================
# Other Production Settings
# ==============================================================================

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB

# Session settings
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_SAVE_EVERY_REQUEST = False
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# CSRF settings
CSRF_COOKIE_AGE = 86400  # 24 hours
CSRF_COOKIE_HTTPONLY = True

# Time zone
USE_TZ = True
TIME_ZONE = environ.get('TIME_ZONE', 'UTC')

# Language settings
USE_I18N = True
LANGUAGE_CODE = environ.get('LANGUAGE_CODE', 'en')
