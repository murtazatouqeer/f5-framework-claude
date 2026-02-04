# Authentication Module Example

Complete JWT authentication module for Django REST Framework with SimpleJWT.

## Structure

```
auth-module/
├── README.md
├── models.py          # Custom User model
├── serializers.py     # Auth serializers
├── views.py           # Auth endpoints
├── urls.py            # URL configuration
├── permissions.py     # Custom permissions
├── backends.py        # Authentication backends
├── tokens.py          # Custom JWT tokens
├── services.py        # Auth business logic
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── factories.py
    └── test_auth.py
```

## Features Demonstrated

- ✅ Custom User model with email login
- ✅ JWT authentication with SimpleJWT
- ✅ Token refresh and verification
- ✅ User registration with email verification
- ✅ Password reset flow
- ✅ Custom token claims
- ✅ Permission classes
- ✅ Rate limiting
- ✅ Comprehensive tests

## Usage

1. Copy files to your Django app
2. Set `AUTH_USER_MODEL = 'users.User'` in settings
3. Configure SimpleJWT settings
4. Run migrations
5. Register URLs

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register/` | Register new user |
| POST | `/api/auth/login/` | Get JWT tokens |
| POST | `/api/auth/refresh/` | Refresh access token |
| POST | `/api/auth/verify/` | Verify token validity |
| POST | `/api/auth/logout/` | Blacklist refresh token |
| GET | `/api/auth/me/` | Get current user |
| PATCH | `/api/auth/me/` | Update current user |
| POST | `/api/auth/password/change/` | Change password |
| POST | `/api/auth/password/reset/` | Request reset |
| POST | `/api/auth/password/reset/confirm/` | Confirm reset |

## Settings Configuration

```python
# settings.py
AUTH_USER_MODEL = 'users.User'

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
}
```
