---
name: laravel-sanctum-auth
description: Laravel Sanctum authentication for API tokens and SPA
applies_to: laravel
category: security
---

# Laravel Sanctum Authentication

## Overview

Laravel Sanctum provides a simple authentication system for SPAs, mobile applications, and simple token-based APIs.

## Installation

```bash
composer require laravel/sanctum
php artisan vendor:publish --provider="Laravel\Sanctum\SanctumServiceProvider"
php artisan migrate
```

## Configuration

```php
<?php
// config/sanctum.php
return [
    'stateful' => explode(',', env('SANCTUM_STATEFUL_DOMAINS', sprintf(
        '%s%s',
        'localhost,localhost:3000,127.0.0.1,127.0.0.1:8000,::1',
        Sanctum::currentApplicationUrlWithPort()
    ))),

    'guard' => ['web'],

    'expiration' => null, // Minutes until tokens expire (null = never)

    'token_prefix' => env('SANCTUM_TOKEN_PREFIX', ''),

    'middleware' => [
        'authenticate_session' => Laravel\Sanctum\Http\Middleware\AuthenticateSession::class,
        'encrypt_cookies' => App\Http\Middleware\EncryptCookies::class,
        'verify_csrf_token' => App\Http\Middleware\VerifyCsrfToken::class,
    ],
];
```

## User Model Setup

```php
<?php
// app/Models/User.php
namespace App\Models;

use Illuminate\Foundation\Auth\User as Authenticatable;
use Illuminate\Notifications\Notifiable;
use Laravel\Sanctum\HasApiTokens;

class User extends Authenticatable
{
    use HasApiTokens, Notifiable;

    protected $fillable = [
        'name',
        'email',
        'password',
    ];

    protected $hidden = [
        'password',
        'remember_token',
    ];

    protected $casts = [
        'email_verified_at' => 'datetime',
        'password' => 'hashed',
    ];
}
```

## API Authentication Controller

```php
<?php
// app/Http/Controllers/Api/AuthController.php
namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Http\Requests\Auth\LoginRequest;
use App\Http\Requests\Auth\RegisterRequest;
use App\Http\Resources\UserResource;
use App\Models\User;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Hash;
use Illuminate\Validation\ValidationException;

class AuthController extends Controller
{
    /**
     * Register a new user.
     */
    public function register(RegisterRequest $request): JsonResponse
    {
        $user = User::create([
            'name' => $request->name,
            'email' => $request->email,
            'password' => Hash::make($request->password),
        ]);

        $token = $user->createToken('auth-token')->plainTextToken;

        return response()->json([
            'user' => UserResource::make($user),
            'token' => $token,
            'token_type' => 'Bearer',
        ], 201);
    }

    /**
     * Login and issue token.
     */
    public function login(LoginRequest $request): JsonResponse
    {
        $user = User::where('email', $request->email)->first();

        if (!$user || !Hash::check($request->password, $user->password)) {
            throw ValidationException::withMessages([
                'email' => ['The provided credentials are incorrect.'],
            ]);
        }

        // Revoke existing tokens if needed
        // $user->tokens()->delete();

        $token = $user->createToken(
            name: $request->device_name ?? 'auth-token',
            abilities: $this->getTokenAbilities($user)
        )->plainTextToken;

        return response()->json([
            'user' => UserResource::make($user),
            'token' => $token,
            'token_type' => 'Bearer',
        ]);
    }

    /**
     * Get the authenticated user.
     */
    public function user(Request $request): UserResource
    {
        return UserResource::make($request->user()->load('profile'));
    }

    /**
     * Logout and revoke token.
     */
    public function logout(Request $request): JsonResponse
    {
        // Revoke current token
        $request->user()->currentAccessToken()->delete();

        return response()->json([
            'message' => 'Successfully logged out',
        ]);
    }

    /**
     * Logout from all devices.
     */
    public function logoutAll(Request $request): JsonResponse
    {
        // Revoke all tokens
        $request->user()->tokens()->delete();

        return response()->json([
            'message' => 'Successfully logged out from all devices',
        ]);
    }

    /**
     * Refresh token.
     */
    public function refresh(Request $request): JsonResponse
    {
        $user = $request->user();

        // Delete current token
        $user->currentAccessToken()->delete();

        // Create new token
        $token = $user->createToken(
            name: 'auth-token',
            abilities: $this->getTokenAbilities($user)
        )->plainTextToken;

        return response()->json([
            'token' => $token,
            'token_type' => 'Bearer',
        ]);
    }

    /**
     * Get token abilities based on user role.
     */
    protected function getTokenAbilities(User $user): array
    {
        if ($user->isAdmin()) {
            return ['*']; // Full access
        }

        return [
            'read',
            'create',
            'update',
            'delete:own', // Can only delete own resources
        ];
    }
}
```

## Routes Setup

```php
<?php
// routes/api.php
use App\Http\Controllers\Api\AuthController;
use Illuminate\Support\Facades\Route;

// Public routes
Route::prefix('auth')->group(function () {
    Route::post('register', [AuthController::class, 'register']);
    Route::post('login', [AuthController::class, 'login']);
});

// Protected routes
Route::middleware('auth:sanctum')->group(function () {
    Route::prefix('auth')->group(function () {
        Route::get('user', [AuthController::class, 'user']);
        Route::post('logout', [AuthController::class, 'logout']);
        Route::post('logout-all', [AuthController::class, 'logoutAll']);
        Route::post('refresh', [AuthController::class, 'refresh']);
    });

    // API resources
    Route::apiResource('products', ProductController::class);
});
```

## Token Abilities (Permissions)

```php
<?php
// Create token with specific abilities
$token = $user->createToken('api-token', ['read', 'create'])->plainTextToken;

// Check ability in controller
public function store(Request $request)
{
    if (!$request->user()->tokenCan('create')) {
        abort(403, 'Token does not have create permission');
    }

    // Create resource...
}

// Check ability in middleware
Route::middleware(['auth:sanctum', 'ability:create'])->group(function () {
    Route::post('products', [ProductController::class, 'store']);
});

// Check multiple abilities
Route::middleware(['auth:sanctum', 'abilities:read,create'])->group(function () {
    // Routes...
});
```

## Custom Token Model

```php
<?php
// app/Models/PersonalAccessToken.php
namespace App\Models;

use Laravel\Sanctum\PersonalAccessToken as SanctumPersonalAccessToken;

class PersonalAccessToken extends SanctumPersonalAccessToken
{
    /**
     * The attributes that should be cast.
     */
    protected $casts = [
        'abilities' => 'json',
        'last_used_at' => 'datetime',
        'expires_at' => 'datetime',
    ];

    /**
     * Check if token has expired.
     */
    public function hasExpired(): bool
    {
        return $this->expires_at && $this->expires_at->isPast();
    }
}

// Register in AppServiceProvider
use Laravel\Sanctum\Sanctum;

public function boot(): void
{
    Sanctum::usePersonalAccessTokenModel(PersonalAccessToken::class);
}
```

## SPA Authentication (Cookie-based)

```php
<?php
// config/cors.php
return [
    'paths' => ['api/*', 'sanctum/csrf-cookie'],
    'allowed_methods' => ['*'],
    'allowed_origins' => [env('FRONTEND_URL', 'http://localhost:3000')],
    'allowed_origins_patterns' => [],
    'allowed_headers' => ['*'],
    'exposed_headers' => [],
    'max_age' => 0,
    'supports_credentials' => true, // Important for cookies
];

// .env
SANCTUM_STATEFUL_DOMAINS=localhost:3000,your-frontend.com
SESSION_DOMAIN=.your-domain.com
```

```javascript
// Frontend (JavaScript)
// First, get CSRF cookie
await fetch('/sanctum/csrf-cookie', {
  credentials: 'include',
});

// Then login
const response = await fetch('/api/auth/login', {
  method: 'POST',
  credentials: 'include',
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'X-XSRF-TOKEN': getCookie('XSRF-TOKEN'),
  },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'password',
  }),
});

// Subsequent requests
const products = await fetch('/api/products', {
  credentials: 'include',
  headers: {
    'Accept': 'application/json',
    'X-XSRF-TOKEN': getCookie('XSRF-TOKEN'),
  },
});
```

## Token Expiration

```php
<?php
// config/sanctum.php
'expiration' => 60 * 24, // 24 hours in minutes

// Or set per-token expiration
$token = $user->createToken('auth-token');
$token->accessToken->expires_at = now()->addHours(24);
$token->accessToken->save();

return $token->plainTextToken;

// Prune expired tokens (add to scheduler)
// app/Console/Kernel.php
$schedule->command('sanctum:prune-expired --hours=24')->daily();
```

## Rate Limiting

```php
<?php
// app/Providers/RouteServiceProvider.php
use Illuminate\Cache\RateLimiting\Limit;
use Illuminate\Support\Facades\RateLimiter;

public function boot(): void
{
    RateLimiter::for('api', function (Request $request) {
        return Limit::perMinute(60)->by($request->user()?->id ?: $request->ip());
    });

    RateLimiter::for('auth', function (Request $request) {
        return Limit::perMinute(5)->by($request->ip());
    });
}

// routes/api.php
Route::middleware('throttle:auth')->group(function () {
    Route::post('auth/login', [AuthController::class, 'login']);
});
```

## Testing Sanctum

```php
<?php
// tests/Feature/AuthTest.php
use App\Models\User;
use Laravel\Sanctum\Sanctum;

class AuthTest extends TestCase
{
    public function test_user_can_login(): void
    {
        $user = User::factory()->create([
            'password' => Hash::make('password'),
        ]);

        $response = $this->postJson('/api/auth/login', [
            'email' => $user->email,
            'password' => 'password',
        ]);

        $response
            ->assertOk()
            ->assertJsonStructure([
                'user' => ['id', 'name', 'email'],
                'token',
                'token_type',
            ]);
    }

    public function test_authenticated_user_can_access_protected_route(): void
    {
        $user = User::factory()->create();

        Sanctum::actingAs($user, ['read']);

        $response = $this->getJson('/api/products');

        $response->assertOk();
    }

    public function test_token_ability_is_checked(): void
    {
        $user = User::factory()->create();

        Sanctum::actingAs($user, ['read']); // No 'create' ability

        $response = $this->postJson('/api/products', [
            'name' => 'Test Product',
        ]);

        $response->assertForbidden();
    }
}
```

## Best Practices

1. **Use HTTPS**: Always in production
2. **Token Expiration**: Set appropriate expiration times
3. **Rate Limiting**: Protect auth endpoints
4. **Ability Scoping**: Use token abilities for fine-grained control
5. **Prune Tokens**: Regularly clean up expired tokens
6. **Secure Storage**: Store tokens securely on client
