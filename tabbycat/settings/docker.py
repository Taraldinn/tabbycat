# ==============================================================================
# Docker
# ==============================================================================

import os
import dj_database_url

ALLOWED_HOSTS = ["*"]

# Honor the 'X-Forwarded-Proto' header for request.is_secure() behind Traefik / Nginx
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

if os.environ.get('DJANGO_SECRET_KEY'):
    SECRET_KEY = os.environ['DJANGO_SECRET_KEY']

# Database configuration
if os.environ.get('DATABASE_URL'):
    DATABASES = {
        'default': dj_database_url.config(
            default=os.environ['DATABASE_URL'],
            conn_max_age=600,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_DATABASE', os.environ.get('DB_NAME', 'tabbycat')),
            'USER': os.environ.get('DB_USERNAME', os.environ.get('DB_USER', 'tabbycat')),
            'PASSWORD': os.environ.get('DB_PASSWORD', 'tabbycat'),
            'HOST': os.environ.get('DB_HOST', 'db'),
            'PORT': int(os.environ.get('DB_PORT', 5432)),
        }
    }

# Multi-tenancy & CSRF
MULTI_TENANT_MODE = os.environ.get('MULTI_TENANT_MODE', 'true').lower() in ('true', '1', 'yes')
TABBYCAT_BASE_DOMAIN = os.environ.get('TABBYCAT_BASE_DOMAIN', 'dash.tab.work.gd')
TENANT_BASE_DOMAIN = os.environ.get('TENANT_BASE_DOMAIN', TABBYCAT_BASE_DOMAIN)

CSRF_TRUSTED_ORIGINS = [
    f"https://{TABBYCAT_BASE_DOMAIN}",
    f"https://*.{TABBYCAT_BASE_DOMAIN}",
]
if os.environ.get('CSRF_TRUSTED_ORIGINS'):
    CSRF_TRUSTED_ORIGINS.extend(
        origin.strip() for origin in os.environ['CSRF_TRUSTED_ORIGINS'].split(',') if origin.strip()
    )

# Sessions: Use cached_db so sessions are stored in Postgres and cached in Redis
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

# Redis / Caching
REDIS_URL = os.environ.get('REDIS_URL')
if not REDIS_URL and os.environ.get('REDIS_HOST'):
    REDIS_URL = f"redis://{os.environ['REDIS_HOST']}:{os.environ.get('REDIS_PORT', 6379)}/1"

if REDIS_URL:
    USE_REDIS = True
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "SOCKET_CONNECT_TIMEOUT": 3,
                "SOCKET_TIMEOUT": 5,
                "IGNORE_EXCEPTIONS": True,
            },
        },
    }
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [REDIS_URL],
                "group_expiry": 10800,
            },
        },
    }
elif bool(int(os.environ.get('DOCKER_REDIS', 0))):
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": "redis://redis:6379/1",
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "SOCKET_CONNECT_TIMEOUT": 3,
                "SOCKET_TIMEOUT": 5,
                "IGNORE_EXCEPTIONS": True,
            },
        },
    }
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [("redis", 6379)],
                "group_expiry": 10800,
            },
        },
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        }
    }
