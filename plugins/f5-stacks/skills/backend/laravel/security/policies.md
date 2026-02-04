---
name: laravel-policies
description: Laravel authorization policies for resource access control
applies_to: laravel
category: security
---

# Laravel Authorization Policies

## Overview

Policies are classes that organize authorization logic around a particular model or resource.

## Creating a Policy

```bash
# Create policy
php artisan make:policy ProductPolicy --model=Product
```

## Policy Structure

```php
<?php
// app/Policies/ProductPolicy.php
namespace App\Policies;

use App\Models\Product;
use App\Models\User;
use Illuminate\Auth\Access\HandlesAuthorization;
use Illuminate\Auth\Access\Response;

class ProductPolicy
{
    use HandlesAuthorization;

    /**
     * Perform pre-authorization checks.
     */
    public function before(User $user, string $ability): ?bool
    {
        // Admins can do anything
        if ($user->isAdmin()) {
            return true;
        }

        // Return null to fall through to specific policy method
        return null;
    }

    /**
     * Determine whether the user can view any products.
     */
    public function viewAny(User $user): bool
    {
        return true; // Everyone can view product list
    }

    /**
     * Determine whether the user can view the product.
     */
    public function view(User $user, Product $product): bool
    {
        // Public products can be viewed by anyone
        if ($product->status === 'active') {
            return true;
        }

        // Draft products can only be viewed by owner
        return $user->id === $product->user_id;
    }

    /**
     * Determine whether the user can create products.
     */
    public function create(User $user): bool
    {
        return $user->hasVerifiedEmail() && $user->can_create_products;
    }

    /**
     * Determine whether the user can update the product.
     */
    public function update(User $user, Product $product): bool
    {
        return $user->id === $product->user_id;
    }

    /**
     * Determine whether the user can delete the product.
     */
    public function delete(User $user, Product $product): bool
    {
        // Can only delete own products
        if ($user->id !== $product->user_id) {
            return false;
        }

        // Can't delete products with orders
        if ($product->orders()->exists()) {
            return false;
        }

        return true;
    }

    /**
     * Determine whether the user can restore the product.
     */
    public function restore(User $user, Product $product): bool
    {
        return $user->id === $product->user_id;
    }

    /**
     * Determine whether the user can permanently delete the product.
     */
    public function forceDelete(User $user, Product $product): bool
    {
        return $user->isAdmin();
    }

    /**
     * Determine whether the user can publish the product.
     */
    public function publish(User $user, Product $product): bool
    {
        return $user->id === $product->user_id
            && $product->status === 'draft'
            && $product->isComplete();
    }

    /**
     * Determine whether the user can archive the product.
     */
    public function archive(User $user, Product $product): bool
    {
        return $user->id === $product->user_id
            && $product->status === 'active';
    }
}
```

## Registering Policies

```php
<?php
// app/Providers/AuthServiceProvider.php
namespace App\Providers;

use App\Models\Product;
use App\Policies\ProductPolicy;
use Illuminate\Foundation\Support\Providers\AuthServiceProvider as ServiceProvider;

class AuthServiceProvider extends ServiceProvider
{
    /**
     * The policy mappings for the application.
     */
    protected $policies = [
        Product::class => ProductPolicy::class,
    ];

    public function boot(): void
    {
        // Laravel auto-discovers policies following naming convention:
        // App\Models\Product -> App\Policies\ProductPolicy
    }
}
```

## Using Policies in Controllers

```php
<?php
// app/Http/Controllers/Api/ProductController.php
namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Product;
use Illuminate\Http\Request;

class ProductController extends Controller
{
    /**
     * Using authorize() method.
     */
    public function show(Product $product)
    {
        $this->authorize('view', $product);

        return ProductResource::make($product);
    }

    /**
     * Using authorize() for model-less actions.
     */
    public function index()
    {
        $this->authorize('viewAny', Product::class);

        return ProductResource::collection(Product::paginate());
    }

    /**
     * Using authorize() before store.
     */
    public function store(CreateProductRequest $request)
    {
        $this->authorize('create', Product::class);

        $product = Product::create($request->validated());

        return ProductResource::make($product);
    }

    /**
     * Using authorize() before update.
     */
    public function update(UpdateProductRequest $request, Product $product)
    {
        $this->authorize('update', $product);

        $product->update($request->validated());

        return ProductResource::make($product);
    }

    /**
     * Using authorize() before delete.
     */
    public function destroy(Product $product)
    {
        $this->authorize('delete', $product);

        $product->delete();

        return response()->noContent();
    }

    /**
     * Custom action.
     */
    public function publish(Product $product)
    {
        $this->authorize('publish', $product);

        $product->publish();

        return ProductResource::make($product);
    }
}
```

## Using can() Method

```php
<?php
// In controller
if ($request->user()->can('update', $product)) {
    // User can update
}

if ($request->user()->cannot('delete', $product)) {
    abort(403);
}

// In Blade templates
@can('update', $product)
    <a href="{{ route('products.edit', $product) }}">Edit</a>
@endcan

@canany(['update', 'delete'], $product)
    <div class="actions">
        @can('update', $product)
            <button>Edit</button>
        @endcan
        @can('delete', $product)
            <button>Delete</button>
        @endcan
    </div>
@endcanany

// Check for model-less actions
@can('create', App\Models\Product::class)
    <a href="{{ route('products.create') }}">Create Product</a>
@endcan
```

## Policy Responses with Messages

```php
<?php
use Illuminate\Auth\Access\Response;

public function delete(User $user, Product $product): Response
{
    if ($user->id !== $product->user_id) {
        return Response::deny('You do not own this product.');
    }

    if ($product->orders()->exists()) {
        return Response::deny('Cannot delete a product with orders.');
    }

    return Response::allow();
}

// In controller - get response message
$response = Gate::inspect('delete', $product);

if ($response->denied()) {
    return response()->json([
        'message' => $response->message(),
    ], 403);
}
```

## Resource Controller with Policy

```php
<?php
class ProductController extends Controller
{
    public function __construct()
    {
        // Authorize all resource actions
        $this->authorizeResource(Product::class, 'product');
    }

    // Policy methods are automatically mapped:
    // index -> viewAny
    // show -> view
    // create, store -> create
    // edit, update -> update
    // destroy -> delete
}
```

## Policy with Additional Arguments

```php
<?php
// Policy method
public function transfer(User $user, Product $product, User $recipient): bool
{
    return $user->id === $product->user_id
        && $user->id !== $recipient->id
        && $recipient->can_receive_products;
}

// Authorization
$this->authorize('transfer', [$product, $recipient]);
```

## Middleware Authorization

```php
<?php
// routes/api.php

// Authorize based on route model binding
Route::put('products/{product}', [ProductController::class, 'update'])
    ->middleware('can:update,product');

// Multiple models
Route::post('products/{product}/transfer/{user}', [ProductController::class, 'transfer'])
    ->middleware('can:transfer,product,user');

// Model-less authorization
Route::post('products', [ProductController::class, 'store'])
    ->middleware('can:create,App\Models\Product');
```

## Testing Policies

```php
<?php
// tests/Unit/ProductPolicyTest.php
namespace Tests\Unit;

use App\Models\Product;
use App\Models\User;
use App\Policies\ProductPolicy;
use Tests\TestCase;

class ProductPolicyTest extends TestCase
{
    public function test_owner_can_update_product(): void
    {
        $user = User::factory()->create();
        $product = Product::factory()->create(['user_id' => $user->id]);

        $policy = new ProductPolicy();

        $this->assertTrue($policy->update($user, $product));
    }

    public function test_non_owner_cannot_update_product(): void
    {
        $user = User::factory()->create();
        $otherUser = User::factory()->create();
        $product = Product::factory()->create(['user_id' => $otherUser->id]);

        $policy = new ProductPolicy();

        $this->assertFalse($policy->update($user, $product));
    }

    public function test_admin_can_do_anything(): void
    {
        $admin = User::factory()->admin()->create();
        $product = Product::factory()->create();

        $policy = new ProductPolicy();

        $this->assertTrue($policy->before($admin, 'delete'));
    }

    public function test_cannot_delete_product_with_orders(): void
    {
        $user = User::factory()->create();
        $product = Product::factory()
            ->hasOrders(1)
            ->create(['user_id' => $user->id]);

        $policy = new ProductPolicy();

        $this->assertFalse($policy->delete($user, $product));
    }
}
```

## Best Practices

1. **Use before() for Admin**: Grant admins full access
2. **Return bool or Response**: Be explicit about authorization
3. **Keep Policies Focused**: One policy per model
4. **Test Policies**: Unit test authorization logic
5. **Use authorize()**: In controllers for cleaner code
6. **Custom Actions**: Add methods for non-CRUD operations
