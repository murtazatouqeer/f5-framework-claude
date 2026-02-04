---
name: laravel-gates
description: Laravel authorization gates for ability-based access control
applies_to: laravel
category: security
---

# Laravel Authorization Gates

## Overview

Gates are closures that determine if a user is authorized to perform a given action. Use gates for actions not related to any specific model.

## Defining Gates

```php
<?php
// app/Providers/AuthServiceProvider.php
namespace App\Providers;

use App\Models\User;
use Illuminate\Foundation\Support\Providers\AuthServiceProvider as ServiceProvider;
use Illuminate\Support\Facades\Gate;

class AuthServiceProvider extends ServiceProvider
{
    public function boot(): void
    {
        // Simple ability check
        Gate::define('access-admin', function (User $user) {
            return $user->isAdmin();
        });

        // Role-based gate
        Gate::define('manage-users', function (User $user) {
            return $user->hasRole('admin') || $user->hasRole('manager');
        });

        // Permission-based gate
        Gate::define('create-products', function (User $user) {
            return $user->hasPermission('products.create');
        });

        // Feature flag gate
        Gate::define('use-beta-features', function (User $user) {
            return $user->is_beta_tester || config('features.beta_enabled');
        });

        // Subscription-based gate
        Gate::define('access-premium', function (User $user) {
            return $user->subscription?->isActive() && $user->subscription->plan === 'premium';
        });

        // Gate with additional parameter
        Gate::define('update-post', function (User $user, Post $post) {
            return $user->id === $post->user_id;
        });

        // Gate with optional parameter
        Gate::define('view-reports', function (User $user, ?string $type = null) {
            if ($type === 'financial') {
                return $user->hasRole('finance');
            }
            return $user->hasRole(['admin', 'manager', 'analyst']);
        });
    }
}
```

## Using Gates

```php
<?php
use Illuminate\Support\Facades\Gate;

// In Controllers
class AdminController extends Controller
{
    public function dashboard()
    {
        if (Gate::denies('access-admin')) {
            abort(403);
        }

        return view('admin.dashboard');
    }

    public function users()
    {
        Gate::authorize('manage-users');

        return view('admin.users');
    }
}

// Using allows/denies
if (Gate::allows('create-products')) {
    // User can create products
}

if (Gate::denies('access-premium')) {
    return redirect()->route('subscription.upgrade');
}

// Using check (returns boolean)
$canManage = Gate::check('manage-users');

// With additional parameters
if (Gate::allows('update-post', $post)) {
    // Can update
}

// Using forUser (check for different user)
if (Gate::forUser($anotherUser)->allows('access-admin')) {
    // Another user can access admin
}
```

## Gate Responses

```php
<?php
use Illuminate\Auth\Access\Response;

Gate::define('access-admin', function (User $user) {
    if (!$user->isAdmin()) {
        return Response::deny('You must be an administrator.');
    }

    if (!$user->hasVerifiedEmail()) {
        return Response::deny('Please verify your email first.');
    }

    if ($user->is_suspended) {
        return Response::denyWithStatus(423, 'Your account is suspended.');
    }

    return Response::allow();
});

// Inspect response
$response = Gate::inspect('access-admin');

if ($response->allowed()) {
    // Access granted
}

if ($response->denied()) {
    $message = $response->message(); // Get denial message
    $code = $response->code(); // Get status code if set
}
```

## Gate Before/After Hooks

```php
<?php
// AuthServiceProvider.php
public function boot(): void
{
    // Before hook - runs before all gates
    Gate::before(function (User $user, string $ability) {
        // Super admins bypass all gates
        if ($user->isSuperAdmin()) {
            return true;
        }

        // Check if user is banned
        if ($user->is_banned) {
            return false;
        }

        // Return null to continue to gate
        return null;
    });

    // After hook - runs after gate (if gate didn't return null)
    Gate::after(function (User $user, string $ability, bool $result, $arguments) {
        // Log authorization attempts
        logger()->info('Gate check', [
            'user' => $user->id,
            'ability' => $ability,
            'result' => $result,
        ]);
    });

    // Define gates...
}
```

## Gate Middleware

```php
<?php
// routes/web.php
Route::middleware('can:access-admin')->group(function () {
    Route::get('/admin', [AdminController::class, 'index']);
    Route::get('/admin/users', [AdminController::class, 'users']);
});

// With parameters
Route::put('/posts/{post}', [PostController::class, 'update'])
    ->middleware('can:update-post,post');

// Multiple gates (any of them)
Route::middleware('can:access-admin|manage-users')->group(function () {
    // Routes...
});
```

## Blade Directives

```blade
{{-- Simple gate check --}}
@can('access-admin')
    <a href="/admin">Admin Panel</a>
@endcan

{{-- With denial handling --}}
@can('create-products')
    <button>Create Product</button>
@else
    <p>You don't have permission to create products.</p>
@endcan

{{-- Cannot directive --}}
@cannot('access-premium')
    <a href="/upgrade">Upgrade to Premium</a>
@endcannot

{{-- Check multiple abilities --}}
@canany(['manage-users', 'access-admin'])
    <a href="/admin/users">Manage Users</a>
@endcanany

{{-- With model --}}
@can('update-post', $post)
    <a href="{{ route('posts.edit', $post) }}">Edit</a>
@endcan

{{-- Check for guest --}}
@guest
    <a href="/login">Login</a>
@else
    @can('access-admin')
        <a href="/admin">Admin</a>
    @endcan
@endguest
```

## User Model Helper Methods

```php
<?php
// On User model - these work with both gates and policies
$user->can('access-admin');
$user->cannot('access-admin');
$user->can('update-post', $post);

// In controllers with auth helper
auth()->user()->can('access-admin');

// With request
$request->user()->can('access-admin');
```

## Organizing Gates

For larger applications, organize gates in separate files:

```php
<?php
// app/Auth/Gates/AdminGates.php
namespace App\Auth\Gates;

use App\Models\User;
use Illuminate\Support\Facades\Gate;

class AdminGates
{
    public static function register(): void
    {
        Gate::define('access-admin', function (User $user) {
            return $user->isAdmin();
        });

        Gate::define('manage-users', function (User $user) {
            return $user->hasRole('admin');
        });

        Gate::define('manage-settings', function (User $user) {
            return $user->hasRole('super-admin');
        });
    }
}

// app/Auth/Gates/ContentGates.php
namespace App\Auth\Gates;

use App\Models\User;
use Illuminate\Support\Facades\Gate;

class ContentGates
{
    public static function register(): void
    {
        Gate::define('publish-content', function (User $user) {
            return $user->hasPermission('content.publish');
        });

        Gate::define('moderate-content', function (User $user) {
            return $user->hasRole(['admin', 'moderator']);
        });
    }
}

// AuthServiceProvider.php
public function boot(): void
{
    AdminGates::register();
    ContentGates::register();
}
```

## Testing Gates

```php
<?php
// tests/Unit/GatesTest.php
namespace Tests\Unit;

use App\Models\User;
use Illuminate\Support\Facades\Gate;
use Tests\TestCase;

class GatesTest extends TestCase
{
    public function test_admin_can_access_admin(): void
    {
        $admin = User::factory()->admin()->create();

        $this->actingAs($admin);

        $this->assertTrue(Gate::allows('access-admin'));
    }

    public function test_regular_user_cannot_access_admin(): void
    {
        $user = User::factory()->create();

        $this->actingAs($user);

        $this->assertTrue(Gate::denies('access-admin'));
    }

    public function test_premium_user_can_access_premium_features(): void
    {
        $user = User::factory()
            ->hasSubscription(['plan' => 'premium', 'status' => 'active'])
            ->create();

        $this->actingAs($user);

        $this->assertTrue(Gate::allows('access-premium'));
    }

    public function test_gate_response_message(): void
    {
        $user = User::factory()->create(['is_suspended' => true]);

        $this->actingAs($user);

        $response = Gate::inspect('access-admin');

        $this->assertTrue($response->denied());
        $this->assertStringContains('suspended', $response->message());
    }
}
```

## Gates vs Policies

| Aspect | Gates | Policies |
|--------|-------|----------|
| Use for | General abilities | Model-specific actions |
| Defined in | AuthServiceProvider | Policy classes |
| Complexity | Simple closures | Full classes |
| Parameters | Any | User + Model |
| Best for | Feature flags, roles | CRUD operations |

## Best Practices

1. **Use Gates for Global Abilities**: Feature access, roles
2. **Use Policies for Models**: CRUD operations on models
3. **Keep Gates Simple**: Complex logic in services
4. **Use Response Objects**: For custom error messages
5. **Organize Large Apps**: Separate gate classes
6. **Test Authorization**: Unit test gates thoroughly
