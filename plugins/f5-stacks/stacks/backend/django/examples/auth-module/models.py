# apps/users/models.py
"""
Custom User model with email authentication.

REQ-002: User Authentication
"""
import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.base_user import BaseUserManager
from django.utils import timezone


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a user with email and password."""
        if not email:
            raise ValueError('Email is required')

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create regular user."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        """Create superuser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('email_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model with email authentication.

    Attributes:
        email: Primary identifier and login credential
        first_name: User's first name
        last_name: User's last name
        is_active: Can the user log in
        is_staff: Can access admin site
        email_verified: Has verified email address
        created_at: Account creation timestamp
        updated_at: Last profile update timestamp
        last_login_ip: IP of last successful login
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # Authentication
    email = models.EmailField(
        'email address',
        unique=True,
        db_index=True
    )

    # Profile
    first_name = models.CharField(
        'first name',
        max_length=150,
        blank=True
    )
    last_name = models.CharField(
        'last name',
        max_length=150,
        blank=True
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True
    )

    # Status
    is_active = models.BooleanField(
        'active',
        default=True,
        help_text='Designates whether this user can log in.'
    )
    is_staff = models.BooleanField(
        'staff status',
        default=False,
        help_text='Designates whether the user can log into admin site.'
    )
    email_verified = models.BooleanField(
        'email verified',
        default=False,
        help_text='Designates whether the user has verified their email.'
    )

    # Metadata
    created_at = models.DateTimeField(
        'date joined',
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )
    last_login_ip = models.GenericIPAddressField(
        null=True,
        blank=True
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'users'
        verbose_name = 'user'
        verbose_name_plural = 'users'
        ordering = ['-created_at']

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        """Return full name."""
        return f'{self.first_name} {self.last_name}'.strip() or self.email

    def get_short_name(self):
        """Return first name or email prefix."""
        return self.first_name or self.email.split('@')[0]


class PasswordResetToken(models.Model):
    """Token for password reset requests."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='password_reset_tokens'
    )
    token = models.CharField(
        max_length=255,
        unique=True,
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'password_reset_tokens'

    def is_valid(self):
        """Check if token is valid and not expired."""
        return (
            self.used_at is None and
            self.expires_at > timezone.now()
        )


class EmailVerificationToken(models.Model):
    """Token for email verification."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='email_verification_tokens'
    )
    token = models.CharField(
        max_length=255,
        unique=True,
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'email_verification_tokens'

    def is_valid(self):
        """Check if token is valid and not expired."""
        return (
            self.used_at is None and
            self.expires_at > timezone.now()
        )
