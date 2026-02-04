# apps/users/views.py
"""
Authentication views.

REQ-002: User Authentication
"""
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.throttling import AnonRateThrottle
from django.contrib.auth import get_user_model

from apps.users.serializers import (
    UserSerializer,
    UserRegistrationSerializer,
    UserUpdateSerializer,
    CustomTokenObtainPairSerializer,
    PasswordChangeSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    EmailVerificationSerializer,
)
from apps.users.services import AuthService

User = get_user_model()


class RegistrationThrottle(AnonRateThrottle):
    """Rate limit for registration."""
    rate = '5/hour'


class PasswordResetThrottle(AnonRateThrottle):
    """Rate limit for password reset."""
    rate = '3/hour'


class RegisterView(generics.CreateAPIView):
    """
    Register a new user account.

    POST /api/auth/register/
    """

    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    throttle_classes = [RegistrationThrottle]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Send verification email
        AuthService.send_verification_email(user)

        # Generate tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            },
            'message': 'Registration successful. Please verify your email.',
        }, status=status.HTTP_201_CREATED)


class LoginView(TokenObtainPairView):
    """
    Obtain JWT token pair.

    POST /api/auth/login/
    """

    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        # Update last login IP
        if response.status_code == 200:
            email = request.data.get('email', '').lower()
            ip = self.get_client_ip(request)
            User.objects.filter(email=email).update(last_login_ip=ip)

        return response

    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')


class RefreshTokenView(TokenRefreshView):
    """
    Refresh access token.

    POST /api/auth/refresh/
    """
    pass


class VerifyTokenView(TokenVerifyView):
    """
    Verify token validity.

    POST /api/auth/verify/
    """
    pass


class LogoutView(APIView):
    """
    Logout by blacklisting refresh token.

    POST /api/auth/logout/
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()

            return Response(
                {'message': 'Logged out successfully.'},
                status=status.HTTP_200_OK
            )
        except Exception:
            return Response(
                {'error': 'Invalid token.'},
                status=status.HTTP_400_BAD_REQUEST
            )


class MeView(generics.RetrieveUpdateAPIView):
    """
    Get or update current user profile.

    GET /api/auth/me/
    PATCH /api/auth/me/
    """

    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return UserSerializer
        return UserUpdateSerializer


class PasswordChangeView(APIView):
    """
    Change current user's password.

    POST /api/auth/password/change/
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {'message': 'Password changed successfully.'},
            status=status.HTTP_200_OK
        )


class PasswordResetRequestView(APIView):
    """
    Request password reset email.

    POST /api/auth/password/reset/
    """

    permission_classes = [AllowAny]
    throttle_classes = [PasswordResetThrottle]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        AuthService.send_password_reset_email(email)

        # Always return success to prevent email enumeration
        return Response(
            {'message': 'If an account exists, a password reset email has been sent.'},
            status=status.HTTP_200_OK
        )


class PasswordResetConfirmView(APIView):
    """
    Confirm password reset with token.

    POST /api/auth/password/reset/confirm/
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        success = AuthService.reset_password(
            token=serializer.validated_data['token'],
            new_password=serializer.validated_data['new_password']
        )

        if success:
            return Response(
                {'message': 'Password reset successfully.'},
                status=status.HTTP_200_OK
            )

        return Response(
            {'error': 'Invalid or expired token.'},
            status=status.HTTP_400_BAD_REQUEST
        )


class EmailVerificationView(APIView):
    """
    Verify email with token.

    POST /api/auth/email/verify/
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        success = AuthService.verify_email(serializer.validated_data['token'])

        if success:
            return Response(
                {'message': 'Email verified successfully.'},
                status=status.HTTP_200_OK
            )

        return Response(
            {'error': 'Invalid or expired token.'},
            status=status.HTTP_400_BAD_REQUEST
        )


class ResendVerificationView(APIView):
    """
    Resend email verification.

    POST /api/auth/email/resend/
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        if user.email_verified:
            return Response(
                {'message': 'Email already verified.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        AuthService.send_verification_email(user)

        return Response(
            {'message': 'Verification email sent.'},
            status=status.HTTP_200_OK
        )
