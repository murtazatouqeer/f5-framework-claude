# Django Project Structure Skill

## Overview

Best practices for organizing Django projects for scalability and maintainability.

## Recommended Project Structure

```
project_name/
├── config/                    # Project configuration
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py           # Shared settings
│   │   ├── development.py    # Dev-specific
│   │   ├── production.py     # Production-specific
│   │   └── testing.py        # Test-specific
│   ├── urls.py               # Root URL configuration
│   ├── wsgi.py
│   ├── asgi.py
│   └── celery.py             # Celery configuration
│
├── apps/                      # Django applications
│   ├── __init__.py
│   ├── core/                 # Shared utilities
│   │   ├── models.py         # Base models
│   │   ├── permissions.py    # Shared permissions
│   │   ├── pagination.py     # Pagination classes
│   │   └── exceptions.py     # Custom exceptions
│   │
│   ├── users/                # User management
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── ...
│   │
│   └── {{domain}}/           # Domain-specific apps
│       ├── models/
│       ├── serializers/
│       ├── views/
│       └── ...
│
├── services/                  # Business logic layer
│   ├── __init__.py
│   └── {{domain}}_service.py
│
├── integrations/              # External integrations
│   ├── __init__.py
│   ├── payment/
│   └── email/
│
├── utils/                     # Utility functions
│   ├── __init__.py
│   ├── validators.py
│   └── helpers.py
│
├── tests/                     # Test configuration
│   ├── conftest.py
│   └── factories/
│
├── static/                    # Static files
├── media/                     # User uploads
├── locale/                    # Translations
│
├── manage.py
├── pyproject.toml
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   ├── production.txt
│   └── testing.txt
│
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
│
└── scripts/                   # Management scripts
    ├── entrypoint.sh
    └── wait_for_db.py
```

## Settings Organization

### base.py

```python
"""
Base settings shared across all environments.
"""
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY')

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'django_filters',
    'drf_spectacular',
    'corsheaders',
]

LOCAL_APPS = [
    'apps.core',
    'apps.users',
    # Add domain apps here
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# DRF Settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'apps.core.pagination.StandardPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'EXCEPTION_HANDLER': 'apps.core.exceptions.custom_exception_handler',
}

# OpenAPI Settings
SPECTACULAR_SETTINGS = {
    'TITLE': 'API Documentation',
    'DESCRIPTION': 'API description',
    'VERSION': '1.0.0',
}
```

### development.py

```python
"""
Development-specific settings.
"""
from .base import *

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'dev_db'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'postgres'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# Debug Toolbar
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
INTERNAL_IPS = ['127.0.0.1']

# Email
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# CORS
CORS_ALLOW_ALL_ORIGINS = True
```

### production.py

```python
"""
Production-specific settings.
"""
from .base import *

DEBUG = False
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# Security
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ['DB_NAME'],
        'USER': os.environ['DB_USER'],
        'PASSWORD': os.environ['DB_PASSWORD'],
        'HOST': os.environ['DB_HOST'],
        'PORT': os.environ.get('DB_PORT', '5432'),
        'CONN_MAX_AGE': 60,
    }
}

# Cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ['REDIS_URL'],
    }
}

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
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
}
```

## URL Organization

### config/urls.py

```python
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),

    # API versions
    path('api/v1/', include('apps.api.v1.urls')),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='docs'),
]
```

### apps/api/v1/urls.py

```python
from django.urls import path, include

urlpatterns = [
    path('auth/', include('apps.users.urls')),
    path('{{domain}}/', include('apps.{{domain}}.urls')),
]
```

## Best Practices

1. **Separate settings by environment** - Never mix dev/prod configurations
2. **Use apps/ directory** - Keep all apps in one location
3. **Core app for shared code** - Base models, utilities, mixins
4. **Services layer** - Extract complex business logic
5. **Version your API** - /api/v1/, /api/v2/
6. **Environment variables** - Never hardcode secrets
