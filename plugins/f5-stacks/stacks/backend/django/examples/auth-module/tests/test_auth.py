# tests/users/test_auth.py
"""
Authentication API tests.

REQ-002: User Authentication
"""
import pytest
from django.urls import reverse
from rest_framework import status
from unittest.mock import patch

from tests.factories import UserFactory


@pytest.mark.django_db
class TestRegistration:
    """Tests for user registration."""

    @pytest.fixture
    def url(self):
        return reverse('auth:register')

    @pytest.fixture
    def valid_data(self):
        return {
            'email': 'newuser@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': 'Test',
            'last_name': 'User',
        }

    def test_register_success(self, api_client, url, valid_data):
        """Test successful registration."""
        with patch('apps.users.services.AuthService.send_verification_email'):
            response = api_client.post(url, valid_data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert 'user' in response.data
        assert 'tokens' in response.data
        assert response.data['user']['email'] == 'newuser@example.com'

    def test_register_duplicate_email(self, api_client, url, valid_data):
        """Test registration with existing email."""
        UserFactory(email='newuser@example.com')

        response = api_client.post(url, valid_data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in str(response.data).lower()

    def test_register_password_mismatch(self, api_client, url, valid_data):
        """Test registration with mismatched passwords."""
        valid_data['password_confirm'] = 'DifferentPass123!'

        response = api_client.post(url, valid_data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_weak_password(self, api_client, url, valid_data):
        """Test registration with weak password."""
        valid_data['password'] = '123'
        valid_data['password_confirm'] = '123'

        response = api_client.post(url, valid_data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestLogin:
    """Tests for user login."""

    @pytest.fixture
    def url(self):
        return reverse('auth:login')

    @pytest.fixture
    def user(self, db):
        user = UserFactory()
        user.set_password('TestPass123!')
        user.save()
        return user

    def test_login_success(self, api_client, url, user):
        """Test successful login."""
        response = api_client.post(url, {
            'email': user.email,
            'password': 'TestPass123!',
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data
        assert 'user' in response.data

    def test_login_wrong_password(self, api_client, url, user):
        """Test login with wrong password."""
        response = api_client.post(url, {
            'email': user.email,
            'password': 'WrongPass123!',
        }, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_nonexistent_user(self, api_client, url):
        """Test login with non-existent email."""
        response = api_client.post(url, {
            'email': 'nonexistent@example.com',
            'password': 'TestPass123!',
        }, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_inactive_user(self, api_client, url):
        """Test login with inactive user."""
        user = UserFactory(is_active=False)
        user.set_password('TestPass123!')
        user.save()

        response = api_client.post(url, {
            'email': user.email,
            'password': 'TestPass123!',
        }, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestTokenRefresh:
    """Tests for token refresh."""

    @pytest.fixture
    def url(self):
        return reverse('auth:token_refresh')

    def test_refresh_success(self, api_client, url, user):
        """Test successful token refresh."""
        # First login to get tokens
        login_response = api_client.post(reverse('auth:login'), {
            'email': user.email,
            'password': 'testpass123',
        }, format='json')

        refresh_token = login_response.data['refresh']

        # Refresh the token
        response = api_client.post(url, {
            'refresh': refresh_token,
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data

    def test_refresh_invalid_token(self, api_client, url):
        """Test refresh with invalid token."""
        response = api_client.post(url, {
            'refresh': 'invalid-token',
        }, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestMe:
    """Tests for current user endpoint."""

    @pytest.fixture
    def url(self):
        return reverse('auth:me')

    def test_me_authenticated(self, authenticated_client, url, user):
        """Test get current user."""
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == user.email

    def test_me_unauthenticated(self, api_client, url):
        """Test get current user without auth."""
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_me_update(self, authenticated_client, url):
        """Test update current user."""
        response = authenticated_client.patch(url, {
            'first_name': 'Updated',
            'last_name': 'Name',
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['first_name'] == 'Updated'


@pytest.mark.django_db
class TestPasswordChange:
    """Tests for password change."""

    @pytest.fixture
    def url(self):
        return reverse('auth:password_change')

    def test_change_password_success(self, authenticated_client, url, user):
        """Test successful password change."""
        user.set_password('CurrentPass123!')
        user.save()

        response = authenticated_client.post(url, {
            'current_password': 'CurrentPass123!',
            'new_password': 'NewSecurePass123!',
            'new_password_confirm': 'NewSecurePass123!',
        }, format='json')

        assert response.status_code == status.HTTP_200_OK

    def test_change_password_wrong_current(self, authenticated_client, url):
        """Test password change with wrong current password."""
        response = authenticated_client.post(url, {
            'current_password': 'WrongPass123!',
            'new_password': 'NewSecurePass123!',
            'new_password_confirm': 'NewSecurePass123!',
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestPasswordReset:
    """Tests for password reset flow."""

    @pytest.fixture
    def request_url(self):
        return reverse('auth:password_reset')

    @pytest.fixture
    def confirm_url(self):
        return reverse('auth:password_reset_confirm')

    def test_request_reset_success(self, api_client, request_url, user):
        """Test request password reset."""
        with patch('apps.users.services.AuthService.send_password_reset_email'):
            response = api_client.post(request_url, {
                'email': user.email,
            }, format='json')

        assert response.status_code == status.HTTP_200_OK

    def test_request_reset_nonexistent_email(self, api_client, request_url):
        """Test request reset for non-existent email (no error revealed)."""
        response = api_client.post(request_url, {
            'email': 'nonexistent@example.com',
        }, format='json')

        # Should still return 200 to prevent email enumeration
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestLogout:
    """Tests for logout."""

    @pytest.fixture
    def url(self):
        return reverse('auth:logout')

    def test_logout_success(self, authenticated_client, url):
        """Test successful logout."""
        # Get refresh token first
        login_response = authenticated_client.post(reverse('auth:login'), {
            'email': 'test@example.com',
            'password': 'testpass123',
        }, format='json')

        response = authenticated_client.post(url, {
            'refresh': login_response.data.get('refresh', ''),
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
