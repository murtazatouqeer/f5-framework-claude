---
name: laravel-test-generator
description: Agent for generating Laravel Feature and Unit tests
applies_to: laravel
category: agent
---

# Laravel Test Generator Agent

## Purpose

Generate comprehensive Laravel tests including Feature tests for API endpoints and Unit tests for business logic.

## Input Requirements

```yaml
required:
  - entity_name: string          # e.g., "Product"
  - test_type: string            # "feature" or "unit"

optional:
  - endpoints: array             # Endpoints to test (feature tests)
  - methods: array               # Methods to test (unit tests)
  - use_factories: boolean       # Use model factories (default: true)
  - use_sanctum: boolean         # Use Sanctum authentication (default: true)
  - database: string             # "refresh" or "transaction" (default: "refresh")
```

## Generation Process

### Step 1: Analyze Controller/Service

```php
// Get methods to test
$controller = app("App\\Http\\Controllers\\Api\\V1\\{$entityName}Controller");
$service = app("App\\Services\\{$entityName}Service");
$methods = get_class_methods($controller);
```

### Step 2: Generate Feature Test

```php
<?php
// tests/Feature/{{Entity}}Test.php
namespace Tests\Feature;

use App\Models\Category;
use App\Models\{{Entity}};
use App\Models\User;
use App\Enums\{{Entity}}Status;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Foundation\Testing\WithFaker;
use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\Storage;
use Laravel\Sanctum\Sanctum;
use Tests\TestCase;

class {{Entity}}Test extends TestCase
{
    use RefreshDatabase, WithFaker;

    protected User $user;
    protected User $admin;
    protected Category $category;

    protected function setUp(): void
    {
        parent::setUp();

        $this->user = User::factory()->create();
        $this->admin = User::factory()->admin()->create();
        $this->category = Category::factory()->create();
    }

    /*
    |--------------------------------------------------------------------------
    | Index Tests
    |--------------------------------------------------------------------------
    */

    public function test_can_list_{{entities}}(): void
    {
        {{Entity}}::factory()->count(5)->create();

        Sanctum::actingAs($this->user);

        $response = $this->getJson('/api/v1/{{entities}}');

        $response
            ->assertOk()
            ->assertJsonCount(5, 'data')
            ->assertJsonStructure([
                'data' => [
                    '*' => [
                        'id',
                        'name',
                        'slug',
                        'price',
                        'status',
                        'created_at',
                        'updated_at',
                    ],
                ],
                'meta' => [
                    'total',
                    'per_page',
                    'current_page',
                    'last_page',
                ],
                'links',
            ]);
    }

    public function test_can_filter_{{entities}}_by_status(): void
    {
        {{Entity}}::factory()->count(3)->create(['status' => {{Entity}}Status::Active]);
        {{Entity}}::factory()->count(2)->create(['status' => {{Entity}}Status::Draft]);

        Sanctum::actingAs($this->user);

        $response = $this->getJson('/api/v1/{{entities}}?status=active');

        $response
            ->assertOk()
            ->assertJsonCount(3, 'data');
    }

    public function test_can_search_{{entities}}(): void
    {
        {{Entity}}::factory()->create(['name' => 'Apple Product']);
        {{Entity}}::factory()->create(['name' => 'Orange Product']);

        Sanctum::actingAs($this->user);

        $response = $this->getJson('/api/v1/{{entities}}?search=Apple');

        $response
            ->assertOk()
            ->assertJsonCount(1, 'data')
            ->assertJsonPath('data.0.name', 'Apple Product');
    }

    public function test_can_paginate_{{entities}}(): void
    {
        {{Entity}}::factory()->count(25)->create();

        Sanctum::actingAs($this->user);

        $response = $this->getJson('/api/v1/{{entities}}?per_page=10&page=2');

        $response
            ->assertOk()
            ->assertJsonCount(10, 'data')
            ->assertJsonPath('meta.current_page', 2)
            ->assertJsonPath('meta.per_page', 10);
    }

    /*
    |--------------------------------------------------------------------------
    | Show Tests
    |--------------------------------------------------------------------------
    */

    public function test_can_show_{{entity}}(): void
    {
        ${{entity}} = {{Entity}}::factory()->create();

        Sanctum::actingAs($this->user);

        $response = $this->getJson("/api/v1/{{entities}}/{${{entity}}->id}");

        $response
            ->assertOk()
            ->assertJsonPath('data.id', ${{entity}}->id)
            ->assertJsonPath('data.name', ${{entity}}->name);
    }

    public function test_show_{{entity}}_not_found(): void
    {
        Sanctum::actingAs($this->user);

        $response = $this->getJson('/api/v1/{{entities}}/non-existent-id');

        $response->assertNotFound();
    }

    public function test_show_{{entity}}_includes_relationships(): void
    {
        ${{entity}} = {{Entity}}::factory()
            ->for($this->category)
            ->create();

        Sanctum::actingAs($this->user);

        $response = $this->getJson("/api/v1/{{entities}}/{${{entity}}->id}?include=category");

        $response
            ->assertOk()
            ->assertJsonPath('data.category.id', $this->category->id);
    }

    /*
    |--------------------------------------------------------------------------
    | Store Tests
    |--------------------------------------------------------------------------
    */

    public function test_can_create_{{entity}}(): void
    {
        Sanctum::actingAs($this->admin);

        $data = [
            'name' => 'Test {{Entity}}',
            'description' => 'Test description',
            'price' => 99.99,
            'category_id' => $this->category->id,
        ];

        $response = $this->postJson('/api/v1/{{entities}}', $data);

        $response
            ->assertCreated()
            ->assertJsonPath('data.name', 'Test {{Entity}}')
            ->assertJsonPath('data.price', '99.99');

        $this->assertDatabaseHas('{{entities}}', [
            'name' => 'Test {{Entity}}',
            'price' => 99.99,
        ]);
    }

    public function test_create_{{entity}}_validation_fails(): void
    {
        Sanctum::actingAs($this->admin);

        $response = $this->postJson('/api/v1/{{entities}}', []);

        $response
            ->assertUnprocessable()
            ->assertJsonValidationErrors(['name', 'price', 'category_id']);
    }

    public function test_create_{{entity}}_name_must_be_unique(): void
    {
        {{Entity}}::factory()->create(['name' => 'Existing Name']);

        Sanctum::actingAs($this->admin);

        $response = $this->postJson('/api/v1/{{entities}}', [
            'name' => 'Existing Name',
            'price' => 10.00,
            'category_id' => $this->category->id,
        ]);

        $response
            ->assertUnprocessable()
            ->assertJsonValidationErrors(['name']);
    }

    public function test_create_{{entity}}_requires_authorization(): void
    {
        Sanctum::actingAs($this->user); // Regular user, not admin

        $response = $this->postJson('/api/v1/{{entities}}', [
            'name' => 'Test',
            'price' => 10.00,
            'category_id' => $this->category->id,
        ]);

        $response->assertForbidden();
    }

    /*
    |--------------------------------------------------------------------------
    | Update Tests
    |--------------------------------------------------------------------------
    */

    public function test_can_update_{{entity}}(): void
    {
        ${{entity}} = {{Entity}}::factory()->create(['user_id' => $this->admin->id]);

        Sanctum::actingAs($this->admin);

        $response = $this->putJson("/api/v1/{{entities}}/{${{entity}}->id}", [
            'name' => 'Updated Name',
            'price' => 149.99,
        ]);

        $response
            ->assertOk()
            ->assertJsonPath('data.name', 'Updated Name')
            ->assertJsonPath('data.price', '149.99');

        $this->assertDatabaseHas('{{entities}}', [
            'id' => ${{entity}}->id,
            'name' => 'Updated Name',
        ]);
    }

    public function test_update_{{entity}}_partial(): void
    {
        ${{entity}} = {{Entity}}::factory()->create([
            'user_id' => $this->admin->id,
            'name' => 'Original Name',
            'price' => 100.00,
        ]);

        Sanctum::actingAs($this->admin);

        $response = $this->patchJson("/api/v1/{{entities}}/{${{entity}}->id}", [
            'price' => 199.99,
        ]);

        $response
            ->assertOk()
            ->assertJsonPath('data.name', 'Original Name')
            ->assertJsonPath('data.price', '199.99');
    }

    /*
    |--------------------------------------------------------------------------
    | Delete Tests
    |--------------------------------------------------------------------------
    */

    public function test_can_delete_{{entity}}(): void
    {
        ${{entity}} = {{Entity}}::factory()->create(['user_id' => $this->admin->id]);

        Sanctum::actingAs($this->admin);

        $response = $this->deleteJson("/api/v1/{{entities}}/{${{entity}}->id}");

        $response->assertNoContent();

        $this->assertSoftDeleted('{{entities}}', [
            'id' => ${{entity}}->id,
        ]);
    }

    public function test_delete_{{entity}}_not_found(): void
    {
        Sanctum::actingAs($this->admin);

        $response = $this->deleteJson('/api/v1/{{entities}}/non-existent-id');

        $response->assertNotFound();
    }

    /*
    |--------------------------------------------------------------------------
    | Authentication Tests
    |--------------------------------------------------------------------------
    */

    public function test_unauthenticated_user_cannot_access(): void
    {
        $response = $this->getJson('/api/v1/{{entities}}');

        $response->assertUnauthorized();
    }

    /*
    |--------------------------------------------------------------------------
    | Custom Action Tests
    |--------------------------------------------------------------------------
    */

    public function test_can_activate_{{entity}}(): void
    {
        ${{entity}} = {{Entity}}::factory()->create([
            'user_id' => $this->admin->id,
            'status' => {{Entity}}Status::Draft,
        ]);

        Sanctum::actingAs($this->admin);

        $response = $this->postJson("/api/v1/{{entities}}/{${{entity}}->id}/activate");

        $response
            ->assertOk()
            ->assertJsonPath('data.status', 'active');

        $this->assertDatabaseHas('{{entities}}', [
            'id' => ${{entity}}->id,
            'status' => {{Entity}}Status::Active,
        ]);
    }
}
```

### Step 3: Generate Unit Test

```php
<?php
// tests/Unit/{{Entity}}ServiceTest.php
namespace Tests\Unit;

use App\Models\{{Entity}};
use App\Models\User;
use App\Models\Category;
use App\Enums\{{Entity}}Status;
use App\Repositories\{{Entity}}Repository;
use App\Services\{{Entity}}Service;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Mockery;
use Mockery\MockInterface;
use Tests\TestCase;

class {{Entity}}ServiceTest extends TestCase
{
    use RefreshDatabase;

    protected {{Entity}}Service $service;
    protected MockInterface $repository;
    protected User $user;
    protected Category $category;

    protected function setUp(): void
    {
        parent::setUp();

        $this->repository = Mockery::mock({{Entity}}Repository::class);
        $this->service = new {{Entity}}Service($this->repository);
        $this->user = User::factory()->create();
        $this->category = Category::factory()->create();
    }

    protected function tearDown(): void
    {
        Mockery::close();
        parent::tearDown();
    }

    /*
    |--------------------------------------------------------------------------
    | Create Tests
    |--------------------------------------------------------------------------
    */

    public function test_create_{{entity}}(): void
    {
        $data = [
            'name' => 'Test {{Entity}}',
            'price' => 99.99,
            'category_id' => $this->category->id,
        ];

        ${{entity}} = {{Entity}}::factory()->make($data);

        $this->repository
            ->shouldReceive('create')
            ->once()
            ->with($data)
            ->andReturn(${{entity}});

        $result = $this->service->create($data);

        $this->assertEquals('Test {{Entity}}', $result->name);
        $this->assertEquals(99.99, $result->price);
    }

    public function test_create_{{entity}}_sets_default_status(): void
    {
        $data = [
            'name' => 'Test {{Entity}}',
            'price' => 99.99,
            'category_id' => $this->category->id,
        ];

        $this->repository
            ->shouldReceive('create')
            ->once()
            ->andReturnUsing(function ($data) {
                return {{Entity}}::factory()->make($data);
            });

        $result = $this->service->create($data);

        $this->assertEquals({{Entity}}Status::Draft, $result->status);
    }

    /*
    |--------------------------------------------------------------------------
    | Update Tests
    |--------------------------------------------------------------------------
    */

    public function test_update_{{entity}}(): void
    {
        ${{entity}} = {{Entity}}::factory()->make(['id' => 'test-id']);
        $updateData = ['name' => 'Updated Name'];

        $updated{{Entity}} = {{Entity}}::factory()->make([
            'id' => 'test-id',
            'name' => 'Updated Name',
        ]);

        $this->repository
            ->shouldReceive('update')
            ->once()
            ->with(${{entity}}, $updateData)
            ->andReturn($updated{{Entity}});

        $result = $this->service->update(${{entity}}, $updateData);

        $this->assertEquals('Updated Name', $result->name);
    }

    /*
    |--------------------------------------------------------------------------
    | Delete Tests
    |--------------------------------------------------------------------------
    */

    public function test_delete_{{entity}}(): void
    {
        ${{entity}} = {{Entity}}::factory()->make(['id' => 'test-id']);

        $this->repository
            ->shouldReceive('delete')
            ->once()
            ->with(${{entity}})
            ->andReturn(true);

        $result = $this->service->delete(${{entity}});

        $this->assertTrue($result);
    }

    /*
    |--------------------------------------------------------------------------
    | Status Transition Tests
    |--------------------------------------------------------------------------
    */

    public function test_activate_{{entity}}_from_draft(): void
    {
        ${{entity}} = {{Entity}}::factory()->make([
            'status' => {{Entity}}Status::Draft,
        ]);

        $activated{{Entity}} = {{Entity}}::factory()->make([
            'status' => {{Entity}}Status::Active,
        ]);

        $this->repository
            ->shouldReceive('update')
            ->once()
            ->andReturn($activated{{Entity}});

        $result = $this->service->activate(${{entity}});

        $this->assertEquals({{Entity}}Status::Active, $result->status);
    }

    public function test_activate_{{entity}}_throws_exception_for_non_draft(): void
    {
        ${{entity}} = {{Entity}}::factory()->make([
            'status' => {{Entity}}Status::Active,
        ]);

        $this->expectException(\DomainException::class);
        $this->expectExceptionMessage('Only draft {{entities}} can be activated');

        $this->service->activate(${{entity}});
    }

    public function test_deactivate_{{entity}}(): void
    {
        ${{entity}} = {{Entity}}::factory()->make([
            'status' => {{Entity}}Status::Active,
        ]);

        $archived{{Entity}} = {{Entity}}::factory()->make([
            'status' => {{Entity}}Status::Archived,
        ]);

        $this->repository
            ->shouldReceive('update')
            ->once()
            ->andReturn($archived{{Entity}});

        $result = $this->service->deactivate(${{entity}});

        $this->assertEquals({{Entity}}Status::Archived, $result->status);
    }

    /*
    |--------------------------------------------------------------------------
    | Business Logic Tests
    |--------------------------------------------------------------------------
    */

    public function test_is_purchasable_returns_true_for_active_with_price(): void
    {
        ${{entity}} = {{Entity}}::factory()->make([
            'status' => {{Entity}}Status::Active,
            'price' => 99.99,
        ]);

        $this->assertTrue(${{entity}}->isPurchasable());
    }

    public function test_is_purchasable_returns_false_for_draft(): void
    {
        ${{entity}} = {{Entity}}::factory()->make([
            'status' => {{Entity}}Status::Draft,
            'price' => 99.99,
        ]);

        $this->assertFalse(${{entity}}->isPurchasable());
    }

    public function test_is_purchasable_returns_false_for_zero_price(): void
    {
        ${{entity}} = {{Entity}}::factory()->make([
            'status' => {{Entity}}Status::Active,
            'price' => 0,
        ]);

        $this->assertFalse(${{entity}}->isPurchasable());
    }

    /*
    |--------------------------------------------------------------------------
    | Computed Property Tests
    |--------------------------------------------------------------------------
    */

    public function test_is_on_sale_when_compare_price_higher(): void
    {
        ${{entity}} = {{Entity}}::factory()->make([
            'price' => 80.00,
            'compare_price' => 100.00,
        ]);

        $this->assertTrue(${{entity}}->is_on_sale);
    }

    public function test_discount_percentage_calculation(): void
    {
        ${{entity}} = {{Entity}}::factory()->make([
            'price' => 80.00,
            'compare_price' => 100.00,
        ]);

        $this->assertEquals(20, ${{entity}}->discount_percentage);
    }
}
```

### Step 4: Generate Factory

```php
<?php
// database/factories/{{Entity}}Factory.php
namespace Database\Factories;

use App\Enums\{{Entity}}Status;
use App\Models\Category;
use App\Models\{{Entity}};
use App\Models\User;
use Illuminate\Database\Eloquent\Factories\Factory;
use Illuminate\Support\Str;

/**
 * @extends Factory<{{Entity}}>
 */
class {{Entity}}Factory extends Factory
{
    protected $model = {{Entity}}::class;

    /**
     * Define the model's default state.
     */
    public function definition(): array
    {
        $name = $this->faker->unique()->words(3, true);

        return [
            'id' => Str::uuid(),
            'name' => $name,
            'slug' => Str::slug($name),
            'description' => $this->faker->paragraph(),
            'price' => $this->faker->randomFloat(2, 10, 1000),
            'compare_price' => null,
            'status' => {{Entity}}Status::Draft,
            'is_featured' => false,
            'category_id' => Category::factory(),
            'user_id' => User::factory(),
            'metadata' => null,
            'published_at' => null,
        ];
    }

    /**
     * Indicate that the {{entity}} is active.
     */
    public function active(): static
    {
        return $this->state(fn (array $attributes) => [
            'status' => {{Entity}}Status::Active,
            'published_at' => now(),
        ]);
    }

    /**
     * Indicate that the {{entity}} is on sale.
     */
    public function onSale(): static
    {
        return $this->state(function (array $attributes) {
            $price = $attributes['price'] ?? $this->faker->randomFloat(2, 10, 500);
            return [
                'price' => $price,
                'compare_price' => $price * 1.25, // 20% off
            ];
        });
    }

    /**
     * Indicate that the {{entity}} is featured.
     */
    public function featured(): static
    {
        return $this->state(fn (array $attributes) => [
            'is_featured' => true,
        ]);
    }

    /**
     * Indicate that the {{entity}} is archived.
     */
    public function archived(): static
    {
        return $this->state(fn (array $attributes) => [
            'status' => {{Entity}}Status::Archived,
        ]);
    }
}
```

## Output Files

```
tests/
├── Feature/
│   └── {{Entity}}Test.php           # Feature tests
└── Unit/
    └── {{Entity}}ServiceTest.php    # Unit tests

database/factories/
└── {{Entity}}Factory.php            # Model factory
```

## Usage Example

```bash
# Generate tests via agent
@laravel:test-generator {
  "entity_name": "Product",
  "test_type": "feature",
  "endpoints": ["index", "show", "store", "update", "destroy"],
  "use_factories": true,
  "use_sanctum": true
}
```

## Validation Checklist

- [ ] All CRUD endpoints are tested
- [ ] Validation errors are tested
- [ ] Authorization is tested
- [ ] Edge cases are covered
- [ ] Factory generates valid data
- [ ] Relationships are tested
- [ ] Business logic is unit tested
