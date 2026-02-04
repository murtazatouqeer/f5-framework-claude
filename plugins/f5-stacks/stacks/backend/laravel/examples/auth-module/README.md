# Laravel Authentication Module Example

Complete example of a Laravel API authentication system using Sanctum.

## Structure

```
auth-module/
├── README.md
├── app/
│   ├── Http/
│   │   ├── Controllers/Api/Auth/
│   │   │   ├── LoginController.php
│   │   │   ├── LogoutController.php
│   │   │   ├── RegisterController.php
│   │   │   ├── PasswordResetController.php
│   │   │   └── ProfileController.php
│   │   ├── Requests/Auth/
│   │   │   ├── LoginRequest.php
│   │   │   ├── RegisterRequest.php
│   │   │   ├── ForgotPasswordRequest.php
│   │   │   ├── ResetPasswordRequest.php
│   │   │   └── UpdateProfileRequest.php
│   │   └── Resources/
│   │       └── UserResource.php
│   ├── Models/
│   │   └── User.php
│   ├── Notifications/
│   │   ├── PasswordResetNotification.php
│   │   └── WelcomeNotification.php
│   └── Services/
│       └── AuthService.php
├── database/
│   ├── factories/
│   │   └── UserFactory.php
│   └── migrations/
│       ├── create_users_table.php
│       └── create_password_reset_tokens_table.php
├── routes/
│   └── api.php
└── tests/
    └── Feature/Api/Auth/
        ├── LoginTest.php
        ├── RegisterTest.php
        ├── LogoutTest.php
        └── PasswordResetTest.php
```

## Features

### Registration
- Email validation
- Password strength rules
- Welcome email notification
- Automatic login after registration
- Token generation

### Login
- Email/password authentication
- Token generation with Sanctum
- Remember token support
- Failed attempt tracking

### Logout
- Current device logout
- All devices logout
- Token revocation

### Password Reset
- Forgot password email
- Token-based reset
- Password history validation (optional)
- Expirable reset tokens

### Profile Management
- View profile
- Update profile
- Change password
- Email verification

## API Endpoints

```
# Public routes
POST   /api/auth/register          - Register new user
POST   /api/auth/login             - Login user
POST   /api/auth/forgot-password   - Request password reset
POST   /api/auth/reset-password    - Reset password with token

# Protected routes (require authentication)
POST   /api/auth/logout            - Logout current device
POST   /api/auth/logout-all        - Logout all devices
GET    /api/auth/user              - Get current user
PUT    /api/auth/profile           - Update profile
PUT    /api/auth/password          - Change password
POST   /api/auth/verify-email      - Verify email address
POST   /api/auth/resend-verification - Resend verification email
```

## Key Patterns

### 1. Token-Based Authentication
```php
// Login and generate token
$token = $user->createToken('auth-token')->plainTextToken;

// Revoke tokens
$user->currentAccessToken()->delete(); // Current
$user->tokens()->delete(); // All
```

### 2. Password Hashing
```php
// Hash password
$user->password = Hash::make($request->password);

// Verify password
if (!Hash::check($request->password, $user->password)) {
    throw new AuthenticationException();
}
```

### 3. Email Verification
```php
// Mark as verified
$user->markEmailAsVerified();

// Send verification
$user->sendEmailVerificationNotification();
```

### 4. Rate Limiting
```php
// In RouteServiceProvider
RateLimiter::for('auth', function (Request $request) {
    return Limit::perMinute(5)->by($request->ip());
});
```

## Security Considerations

1. **Password Hashing**: Use Bcrypt/Argon2
2. **Token Expiration**: Configure token lifetimes
3. **Rate Limiting**: Prevent brute force attacks
4. **HTTPS Only**: Secure token transmission
5. **Token Abilities**: Scope token permissions
6. **Password Rules**: Enforce strong passwords

## Configuration

```php
// config/sanctum.php
'expiration' => 60 * 24 * 7, // 1 week

// config/auth.php
'guards' => [
    'api' => [
        'driver' => 'sanctum',
        'provider' => 'users',
    ],
],
```

## Related Skills

- `skills/security/sanctum-auth.md`
- `skills/validation/form-requests.md`
- `skills/validation/custom-rules.md`
- `skills/error-handling/exception-handling.md`
- `skills/testing/feature-tests.md`

## Related Templates

- `templates/laravel-controller.md`
- `templates/laravel-request.md`
- `templates/laravel-resource.md`
- `templates/laravel-service.md`
- `templates/laravel-test.md`

## Testing

Run authentication tests:

```bash
php artisan test --filter=Auth
```

Key test scenarios:
- Successful registration
- Login with valid credentials
- Login with invalid credentials
- Token-based authentication
- Logout functionality
- Password reset flow
- Rate limiting
