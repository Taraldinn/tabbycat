import logging
from os import environ

from .digitalocean import *  # Import base DigitalOcean settings

# ==============================================================================
# Basic Plan Optimizations ($10/mo - 1GB RAM, 1 vCPU)
# ==============================================================================

# Memory optimization for 1GB RAM
# Reduce the number of database connections
DATABASES['default']['OPTIONS'].update({
    'MAX_CONNS': 5,  # Limit database connections
    'OPTIONS': {
        'sslmode': 'require',
        'connect_timeout': 10,
        'application_name': 'tabbycat_basic',
    }
})

# Cache optimization for limited memory
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'tabbycat-cache',
        'OPTIONS': {
            'MAX_ENTRIES': 1000,  # Reduced for memory efficiency
            'CULL_FREQUENCY': 3,
        },
        'TIMEOUT': 300,
    }
}

# Session configuration optimized for basic plan
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 3600  # 1 hour (shorter for memory efficiency)

# Disable channels/WebSocket for basic plan to save memory
CHANNEL_LAYERS = {}
ASGI_APPLICATION = None

# Use WSGI instead of ASGI for better resource efficiency
WSGI_APPLICATION = 'wsgi.application'

# Logging optimization - reduce verbosity
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',  # Only warnings and errors
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

# Cache timeout optimization for basic plan
PUBLIC_FAST_CACHE_TIMEOUT = int(environ.get('PUBLIC_FAST_CACHE_TIMEOUT', 300))   # 5 minutes
PUBLIC_SLOW_CACHE_TIMEOUT = int(environ.get('PUBLIC_SLOW_CACHE_TIMEOUT', 900))   # 15 minutes
TAB_PAGES_CACHE_TIMEOUT = int(environ.get('TAB_PAGES_CACHE_TIMEOUT', 1800))      # 30 minutes

# File upload limits for basic plan
FILE_UPLOAD_MAX_MEMORY_SIZE = 2621440  # 2.5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 2621440  # 2.5MB

# Template optimization - templates are already cached in the base settings

# Static files optimization
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
WHITENOISE_USE_FINDERS = False  # Disable for production
WHITENOISE_AUTOREFRESH = False

# Email backend optimization (use console for basic plan to save resources)
if not environ.get('EMAIL_HOST'):
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Security optimizations
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# Disable debug toolbar
DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda request: False,
}

# ==============================================================================
# Basic Plan Specific Settings
# ==============================================================================

# Reduce middleware for better performance
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'utils.middleware.DebateMiddleware',
]

# Gunicorn settings optimized for 1GB RAM / 1 vCPU
GUNICORN_WORKERS = 1
GUNICORN_WORKER_CLASS = 'sync'
GUNICORN_MAX_REQUESTS = int(environ.get('GUNICORN_MAX_REQUESTS', 1000))
GUNICORN_MAX_REQUESTS_JITTER = int(environ.get('GUNICORN_MAX_REQUESTS_JITTER', 100))
GUNICORN_TIMEOUT = 30
GUNICORN_KEEPALIVE = 2

# Database connection optimization
CONN_MAX_AGE = 300  # 5 minutes
CONN_HEALTH_CHECKS = True
