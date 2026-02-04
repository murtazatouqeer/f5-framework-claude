---
name: laravel-feature-tests
description: Feature testing patterns for Laravel APIs
applies_to: laravel
category: testing
---

# Laravel Feature Tests

## Overview

Feature tests validate complete user journeys and API workflows, testing multiple components working together.

## Test Setup

```php
<?php
// tests/Feature/Api/ProductTest.php
namespace Tests\Feature\Api;

use App\Models\Product;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Foundation\Testing\WithFaker;
use Laravel\Sanctum\Sanctum;
use Tests\TestCase;

class ProductTest extends TestCase
{
    use RefreshDatabase, WithFaker;

    protected User $user;
    protected User $admin;

    protected function setUp(): void
    {
        parent::setUp();

        $this->user = User::factory()->create();
        $this->admin = User::factory()->admin()->create();
    }

    /**
     * Helper to authenticate as user.
     */
    protected function actingAsUser(): static
    {
        Sanctum::actingAs($this->user);
        return $this;
    }

    /**
     * Helper to authenticate as admin.
     */
    protected function actingAsAdmin(): static
    {
        Sanctum::actingAs($this->admin);
        return $this;
    }
}
```

## CRUD Test Patterns

### Index/List Tests

```php
<?php
public function test_can_list_products(): void
{
    $this->actingAsUser();

    Product::factory()->count(15)->create();

    $response = $this->getJson('/api/products');

    $response
        ->assertOk()
        ->assertJsonStructure([
            'success',
            'message',
            'data' => [
                '*' => ['id', 'name', 'price', 'status'],
            ],
            'meta' => ['current_page', 'last_page', 'per_page', 'total'],
        ])
        ->assertJsonCount(15, 'data');
}

public function test_can_filter_products(): void
{
    $this->actingAsUser();

    Product::factory()->active()->count(5)->create();
    Product::factory()->inactive()->count(3)->create();

    $response = $this->getJson('/api/products?status=active');

    $response
        ->assertOk()
        ->assertJsonCount(5, 'data');
}

public function test_can_search_products(): void
{
    $this->actingAsUser();

    Product::factory()->create(['name' => 'iPhone Pro']);
    Product::factory()->create(['name' => 'Samsung Galaxy']);

    $response = $this->getJson('/api/products?search=iPhone');

    $response
        ->assertOk()
        ->assertJsonCount(1, 'data')
        ->assertJsonPath('data.0.name', 'iPhone Pro');
}

public function test_can_paginate_products(): void
{
    $this->actingAsUser();

    Product::factory()->count(25)->create();

    $response = $this->getJson('/api/products?per_page=10&page=2');

    $response
        ->assertOk()
        ->assertJsonCount(10, 'data')
        ->assertJsonPath('meta.current_page', 2)
        ->assertJsonPath('meta.per_page', 10);
}
```

### Show Tests

```php
<?php
public function test_can_show_product(): void
{
    $this->actingAsUser();

    $product = Product::factory()->create();

    $response = $this->getJson("/api/products/{$product->id}");

    $response
        ->assertOk()
        ->assertJsonPath('data.id', $product->id)
        ->assertJsonPath('data.name', $product->name);
}

public function test_show_nonexistent_product_returns_404(): void
{
    $this->actingAsUser();

    $response = $this->getJson('/api/products/nonexistent-uuid');

    $response->assertNotFound();
}

public function test_show_product_includes_relationships(): void
{
    $this->actingAsUser();

    $product = Product::factory()
        ->hasCategory()
        ->hasTags(3)
        ->create();

    $response = $this->getJson("/api/products/{$product->id}");

    $response
        ->assertOk()
        ->assertJsonStructure([
            'data' => [
                'id',
                'name',
                'category' => ['id', 'name'],
                'tags' => [
                    '*' => ['id', 'name'],
                ],
            ],
        ]);
}
```

### Create Tests

```php
<?php
public function test_can_create_product(): void
{
    $this->actingAsAdmin();

    $category = Category::factory()->create();
    $data = [
        'name' => 'New Product',
        'description' => 'Product description',
        'price' => 99.99,
        'category_id' => $category->id,
    ];

    $response = $this->postJson('/api/products', $data);

    $response
        ->assertCreated()
        ->assertJsonPath('data.name', 'New Product')
        ->assertJsonPath('data.price', '99.99');

    $this->assertDatabaseHas('products', [
        'name' => 'New Product',
        'category_id' => $category->id,
    ]);
}

public function test_create_product_validation(): void
{
    $this->actingAsAdmin();

    $response = $this->postJson('/api/products', []);

    $response
        ->assertUnprocessable()
        ->assertJsonValidationErrors(['name', 'price', 'category_id']);
}

public function test_create_product_unique_name(): void
{
    $this->actingAsAdmin();

    Product::factory()->create(['name' => 'Existing Product']);
    $category = Category::factory()->create();

    $response = $this->postJson('/api/products', [
        'name' => 'Existing Product',
        'price' => 50.00,
        'category_id' => $category->id,
    ]);

    $response
        ->assertUnprocessable()
        ->assertJsonValidationErrors(['name']);
}

public function test_regular_user_cannot_create_product(): void
{
    $this->actingAsUser();

    $response = $this->postJson('/api/products', [
        'name' => 'New Product',
        'price' => 99.99,
    ]);

    $response->assertForbidden();
}
```

### Update Tests

```php
<?php
public function test_can_update_product(): void
{
    $this->actingAsAdmin();

    $product = Product::factory()->create();

    $response = $this->putJson("/api/products/{$product->id}", [
        'name' => 'Updated Name',
        'price' => 149.99,
    ]);

    $response
        ->assertOk()
        ->assertJsonPath('data.name', 'Updated Name')
        ->assertJsonPath('data.price', '149.99');

    $this->assertDatabaseHas('products', [
        'id' => $product->id,
        'name' => 'Updated Name',
    ]);
}

public function test_can_partial_update_product(): void
{
    $this->actingAsAdmin();

    $product = Product::factory()->create(['name' => 'Original', 'price' => 100]);

    $response = $this->patchJson("/api/products/{$product->id}", [
        'price' => 150,
    ]);

    $response->assertOk();

    $this->assertDatabaseHas('products', [
        'id' => $product->id,
        'name' => 'Original', // Unchanged
        'price' => 150,       // Updated
    ]);
}

public function test_update_nonexistent_product_returns_404(): void
{
    $this->actingAsAdmin();

    $response = $this->putJson('/api/products/nonexistent-uuid', [
        'name' => 'Updated',
    ]);

    $response->assertNotFound();
}
```

### Delete Tests

```php
<?php
public function test_can_delete_product(): void
{
    $this->actingAsAdmin();

    $product = Product::factory()->create();

    $response = $this->deleteJson("/api/products/{$product->id}");

    $response->assertNoContent();

    $this->assertSoftDeleted('products', ['id' => $product->id]);
}

public function test_delete_nonexistent_product_returns_404(): void
{
    $this->actingAsAdmin();

    $response = $this->deleteJson('/api/products/nonexistent-uuid');

    $response->assertNotFound();
}

public function test_regular_user_cannot_delete_product(): void
{
    $this->actingAsUser();

    $product = Product::factory()->create();

    $response = $this->deleteJson("/api/products/{$product->id}");

    $response->assertForbidden();
}
```

## Authentication Tests

```php
<?php
// tests/Feature/Api/AuthTest.php
namespace Tests\Feature\Api;

use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Hash;
use Tests\TestCase;

class AuthTest extends TestCase
{
    use RefreshDatabase;

    public function test_user_can_register(): void
    {
        $response = $this->postJson('/api/auth/register', [
            'name' => 'John Doe',
            'email' => 'john@example.com',
            'password' => 'password123',
            'password_confirmation' => 'password123',
        ]);

        $response
            ->assertCreated()
            ->assertJsonStructure([
                'data' => ['user', 'token'],
            ]);

        $this->assertDatabaseHas('users', ['email' => 'john@example.com']);
    }

    public function test_user_can_login(): void
    {
        $user = User::factory()->create([
            'password' => Hash::make('password123'),
        ]);

        $response = $this->postJson('/api/auth/login', [
            'email' => $user->email,
            'password' => 'password123',
        ]);

        $response
            ->assertOk()
            ->assertJsonStructure([
                'data' => ['user', 'token'],
            ]);
    }

    public function test_login_with_invalid_credentials(): void
    {
        $user = User::factory()->create();

        $response = $this->postJson('/api/auth/login', [
            'email' => $user->email,
            'password' => 'wrong-password',
        ]);

        $response
            ->assertUnauthorized()
            ->assertJson(['message' => 'Invalid credentials']);
    }

    public function test_user_can_logout(): void
    {
        $user = User::factory()->create();
        Sanctum::actingAs($user);

        $response = $this->postJson('/api/auth/logout');

        $response->assertNoContent();
    }

    public function test_unauthenticated_access_returns_401(): void
    {
        $response = $this->getJson('/api/user');

        $response->assertUnauthorized();
    }
}
```

## File Upload Tests

```php
<?php
use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\Storage;

public function test_can_upload_product_image(): void
{
    Storage::fake('public');
    $this->actingAsAdmin();

    $product = Product::factory()->create();
    $file = UploadedFile::fake()->image('product.jpg', 800, 600);

    $response = $this->postJson("/api/products/{$product->id}/image", [
        'image' => $file,
    ]);

    $response->assertOk();

    Storage::disk('public')->assertExists("products/{$product->id}/{$file->hashName()}");
}

public function test_upload_validates_file_type(): void
{
    Storage::fake('public');
    $this->actingAsAdmin();

    $product = Product::factory()->create();
    $file = UploadedFile::fake()->create('document.pdf', 1024);

    $response = $this->postJson("/api/products/{$product->id}/image", [
        'image' => $file,
    ]);

    $response
        ->assertUnprocessable()
        ->assertJsonValidationErrors(['image']);
}

public function test_upload_validates_file_size(): void
{
    Storage::fake('public');
    $this->actingAsAdmin();

    $product = Product::factory()->create();
    $file = UploadedFile::fake()->image('large.jpg')->size(10240); // 10MB

    $response = $this->postJson("/api/products/{$product->id}/image", [
        'image' => $file,
    ]);

    $response
        ->assertUnprocessable()
        ->assertJsonValidationErrors(['image']);
}
```

## Event Tests

```php
<?php
use Illuminate\Support\Facades\Event;
use App\Events\ProductCreated;
use App\Events\ProductUpdated;

public function test_product_created_event_dispatched(): void
{
    Event::fake([ProductCreated::class]);
    $this->actingAsAdmin();

    $this->postJson('/api/products', [
        'name' => 'New Product',
        'price' => 99.99,
        'category_id' => Category::factory()->create()->id,
    ]);

    Event::assertDispatched(ProductCreated::class, function ($event) {
        return $event->product->name === 'New Product';
    });
}

public function test_product_updated_event_dispatched(): void
{
    Event::fake([ProductUpdated::class]);
    $this->actingAsAdmin();

    $product = Product::factory()->create();

    $this->putJson("/api/products/{$product->id}", [
        'name' => 'Updated Name',
    ]);

    Event::assertDispatched(ProductUpdated::class);
}
```

## Notification Tests

```php
<?php
use Illuminate\Support\Facades\Notification;
use App\Notifications\OrderConfirmation;

public function test_order_confirmation_notification_sent(): void
{
    Notification::fake();
    $this->actingAsUser();

    $this->postJson('/api/orders', [
        'items' => [
            ['product_id' => Product::factory()->create()->id, 'quantity' => 2],
        ],
    ]);

    Notification::assertSentTo(
        $this->user,
        OrderConfirmation::class,
        function ($notification, $channels) {
            return in_array('mail', $channels);
        }
    );
}
```

## Queue Tests

```php
<?php
use Illuminate\Support\Facades\Queue;
use App\Jobs\ProcessOrder;

public function test_order_processing_job_dispatched(): void
{
    Queue::fake();
    $this->actingAsUser();

    $this->postJson('/api/orders', [
        'items' => [
            ['product_id' => Product::factory()->create()->id, 'quantity' => 2],
        ],
    ]);

    Queue::assertPushed(ProcessOrder::class);
}

public function test_job_dispatched_with_correct_data(): void
{
    Queue::fake();
    $this->actingAsUser();

    $product = Product::factory()->create();

    $this->postJson('/api/orders', [
        'items' => [
            ['product_id' => $product->id, 'quantity' => 2],
        ],
    ]);

    Queue::assertPushed(ProcessOrder::class, function ($job) use ($product) {
        return $job->order->items->first()->product_id === $product->id;
    });
}
```

## Database Transaction Tests

```php
<?php
public function test_order_creation_is_atomic(): void
{
    $this->actingAsUser();

    $product = Product::factory()->create(['stock' => 5]);

    // Attempt to order more than available stock
    $response = $this->postJson('/api/orders', [
        'items' => [
            ['product_id' => $product->id, 'quantity' => 10],
        ],
    ]);

    $response->assertUnprocessable();

    // Ensure no partial data was saved
    $this->assertDatabaseCount('orders', 0);
    $this->assertDatabaseCount('order_items', 0);
    $this->assertDatabaseHas('products', ['id' => $product->id, 'stock' => 5]);
}
```

## Test Traits

```php
<?php
// tests/Traits/ApiTestHelpers.php
namespace Tests\Traits;

trait ApiTestHelpers
{
    protected function assertApiSuccess($response, int $status = 200): void
    {
        $response
            ->assertStatus($status)
            ->assertJsonStructure(['success', 'message', 'data'])
            ->assertJson(['success' => true]);
    }

    protected function assertApiError($response, int $status = 400): void
    {
        $response
            ->assertStatus($status)
            ->assertJson(['success' => false]);
    }

    protected function assertApiPaginated($response, int $expectedCount): void
    {
        $response
            ->assertOk()
            ->assertJsonStructure([
                'data',
                'meta' => ['current_page', 'last_page', 'per_page', 'total'],
                'links',
            ])
            ->assertJsonCount($expectedCount, 'data');
    }
}
```

## Best Practices

1. **Use RefreshDatabase**: Ensures clean state for each test
2. **Use Factories**: Create test data consistently
3. **Test Authorization**: Verify access control at all levels
4. **Test Validation**: Cover all validation rules
5. **Test Edge Cases**: Empty data, boundaries, invalid states
6. **Use Assertions**: assertDatabaseHas, assertSoftDeleted, assertJsonPath
7. **Organize Tests**: Group by resource/feature
