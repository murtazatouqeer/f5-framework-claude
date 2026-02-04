# apps/users/services.py
"""
Authentication service layer.

REQ-002: User Authentication
"""
import secrets
from datetime import timedelta
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.users.models import PasswordResetToken, EmailVerificationToken

User = get_user_model()


class AuthService:
    """Service for authentication-related operations."""

    TOKEN_LENGTH = 64
    PASSWORD_RESET_EXPIRY_HOURS = 24
    EMAIL_VERIFICATION_EXPIRY_HOURS = 72

    @classmethod
    def generate_token(cls):
        """Generate secure random token."""
        return secrets.token_urlsafe(cls.TOKEN_LENGTH)

    @classmethod
    def send_verification_email(cls, user):
        """
        Send email verification link.

        Args:
            user: User instance to verify
        """
        # Invalidate previous tokens
        EmailVerificationToken.objects.filter(
            user=user,
            used_at__isnull=True
        ).update(used_at=timezone.now())

        # Create new token
        token = cls.generate_token()
        expires_at = timezone.now() + timedelta(hours=cls.EMAIL_VERIFICATION_EXPIRY_HOURS)

        EmailVerificationToken.objects.create(
            user=user,
            token=token,
            expires_at=expires_at
        )

        # Build verification URL
        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"

        # Send email
        context = {
            'user': user,
            'verification_url': verification_url,
            'expiry_hours': cls.EMAIL_VERIFICATION_EXPIRY_HOURS,
        }

        send_mail(
            subject='Verify your email address',
            message=render_to_string('emails/verify_email.txt', context),
            html_message=render_to_string('emails/verify_email.html', context),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

    @classmethod
    def verify_email(cls, token):
        """
        Verify email with token.

        Args:
            token: Verification token string

        Returns:
            bool: True if verification successful
        """
        try:
            verification = EmailVerificationToken.objects.select_related('user').get(
                token=token,
                used_at__isnull=True,
                expires_at__gt=timezone.now()
            )

            # Mark token as used
            verification.used_at = timezone.now()
            verification.save()

            # Mark user email as verified
            verification.user.email_verified = True
            verification.user.save(update_fields=['email_verified', 'updated_at'])

            return True

        except EmailVerificationToken.DoesNotExist:
            return False

    @classmethod
    def send_password_reset_email(cls, email):
        """
        Send password reset link.

        Args:
            email: Email address to send reset to
        """
        try:
            user = User.objects.get(email=email.lower(), is_active=True)
        except User.DoesNotExist:
            # Don't reveal if user exists
            return

        # Invalidate previous tokens
        PasswordResetToken.objects.filter(
            user=user,
            used_at__isnull=True
        ).update(used_at=timezone.now())

        # Create new token
        token = cls.generate_token()
        expires_at = timezone.now() + timedelta(hours=cls.PASSWORD_RESET_EXPIRY_HOURS)

        PasswordResetToken.objects.create(
            user=user,
            token=token,
            expires_at=expires_at
        )

        # Build reset URL
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"

        # Send email
        context = {
            'user': user,
            'reset_url': reset_url,
            'expiry_hours': cls.PASSWORD_RESET_EXPIRY_HOURS,
        }

        send_mail(
            subject='Reset your password',
            message=render_to_string('emails/password_reset.txt', context),
            html_message=render_to_string('emails/password_reset.html', context),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

    @classmethod
    def reset_password(cls, token, new_password):
        """
        Reset password with token.

        Args:
            token: Reset token string
            new_password: New password to set

        Returns:
            bool: True if reset successful
        """
        try:
            reset_token = PasswordResetToken.objects.select_related('user').get(
                token=token,
                used_at__isnull=True,
                expires_at__gt=timezone.now()
            )

            # Mark token as used
            reset_token.used_at = timezone.now()
            reset_token.save()

            # Update password
            user = reset_token.user
            user.set_password(new_password)
            user.save(update_fields=['password', 'updated_at'])

            return True

        except PasswordResetToken.DoesNotExist:
            return False

    @classmethod
    def cleanup_expired_tokens(cls):
        """Remove expired tokens from database."""
        now = timezone.now()

        # Delete expired password reset tokens
        PasswordResetToken.objects.filter(expires_at__lt=now).delete()

        # Delete expired email verification tokens
        EmailVerificationToken.objects.filter(expires_at__lt=now).delete()
