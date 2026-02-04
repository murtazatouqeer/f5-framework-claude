# apps/users/urls.py
"""
Authentication URL configuration.

REQ-002: User Authentication
"""
from django.urls import path

from apps.users.views import (
    RegisterView,
    LoginView,
    RefreshTokenView,
    VerifyTokenView,
    LogoutView,
    MeView,
    PasswordChangeView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    EmailVerificationView,
    ResendVerificationView,
)

app_name = 'auth'

urlpatterns = [
    # Registration
    path('register/', RegisterView.as_view(), name='register'),

    # JWT Token endpoints
    path('login/', LoginView.as_view(), name='login'),
    path('refresh/', RefreshTokenView.as_view(), name='token_refresh'),
    path('verify/', VerifyTokenView.as_view(), name='token_verify'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # User profile
    path('me/', MeView.as_view(), name='me'),

    # Password management
    path('password/change/', PasswordChangeView.as_view(), name='password_change'),
    path('password/reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('password/reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),

    # Email verification
    path('email/verify/', EmailVerificationView.as_view(), name='email_verify'),
    path('email/resend/', ResendVerificationView.as_view(), name='email_resend'),
]

# URL Patterns Summary:
# ---------------------------------------------------------
# POST   /api/auth/register/               - Register new user
# POST   /api/auth/login/                  - Get JWT tokens
# POST   /api/auth/refresh/                - Refresh access token
# POST   /api/auth/verify/                 - Verify token validity
# POST   /api/auth/logout/                 - Blacklist refresh token
# GET    /api/auth/me/                     - Get current user
# PATCH  /api/auth/me/                     - Update current user
# POST   /api/auth/password/change/        - Change password
# POST   /api/auth/password/reset/         - Request reset email
# POST   /api/auth/password/reset/confirm/ - Confirm reset with token
# POST   /api/auth/email/verify/           - Verify email
# POST   /api/auth/email/resend/           - Resend verification
# ---------------------------------------------------------
