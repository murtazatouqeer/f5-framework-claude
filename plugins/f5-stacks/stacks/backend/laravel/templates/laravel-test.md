---
name: laravel-test
description: Template for Laravel Feature and Unit Tests
applies_to: laravel
type: template
---

# Laravel Test Template

## Feature Test

```php
<?php
// tests/Feature/Api/{{EntityName}}Test.php
namespace Tests\Feature\Api;

use App\Models\{{EntityName}};
use App\Models\Category;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Foundation\Testing\WithFaker;
use Laravel\Sanctum\Sanctum;
use Tests\TestCase;

class {{EntityName}}Test extends TestCase
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

    // ==========================================
    // INDEX TESTS
    // ==========================================

    public function test_can_list_{{entityNames}}(): void
    {
        Sanctum::actingAs($this->user);

        {{EntityName}}::factory()->count(5)->create();

        $response = $this->getJson('/api/{{entityNames}}');

        $response
            ->assertOk()
            ->assertJsonStructure([
                'success',
                'message',
                'data' => [
                    '*' => ['id', 'name', 'status'],
                ],
                'meta' => ['current_page', 'last_page', 'per_page', 'total'],
            ])
            ->assertJsonCount(5, 'data');
    }

    public function test_can_filter_{{entityNames}}_by_status(): void
    {
        Sanctum::actingAs($this->user);

        {{EntityName}}::factory()->active()->count(3)->create();
        {{EntityName}}::factory()->inactive()->count(2)->create();

        $response = $this->getJson('/api/{{entityNames}}?status=active');

        $response
            ->assertOk()
            ->assertJsonCount(3, 'data');
    }

    public function test_can_search_{{entityNames}}(): void
    {
        Sanctum::actingAs($this->user);

        {{EntityName}}::factory()->create(['name' => 'Specific Name']);
        {{EntityName}}::factory()->create(['name' => 'Other Name']);

        $response = $this->getJson('/api/{{entityNames}}?search=Specific');

        $response
            ->assertOk()
            ->assertJsonCount(1, 'data')
            ->assertJsonPath('data.0.name', 'Specific Name');
    }

    // ==========================================
    // SHOW TESTS
    // ==========================================

    public function test_can_show_{{entityName}}(): void
    {
        Sanctum::actingAs($this->user);

        ${{entityName}} = {{EntityName}}::factory()->create();

        $response = $this->getJson("/api/{{entityNames}}/{${{entityName}}->id}");

        $response
            ->assertOk()
            ->assertJsonPath('data.id', ${{entityName}}->id)
            ->assertJsonPath('data.name', ${{entityName}}->name);
    }

    public function test_show_nonexistent_{{entityName}}_returns_404(): void
    {
        Sanctum::actingAs($this->user);

        $response = $this->getJson('/api/{{entityNames}}/nonexistent-uuid');

        $response->assertNotFound();
    }

    // ==========================================
    // STORE TESTS
    // ==========================================

    public function test_can_create_{{entityName}}(): void
    {
        Sanctum::actingAs($this->admin);

        $category = Category::factory()->create();
        $data = [
            'name' => 'New {{EntityName}}',
            'description' => 'Description here',
            'price' => 99.99,
            'category_id' => $category->id,
        ];

        $response = $this->postJson('/api/{{entityNames}}', $data);

        $response
            ->assertCreated()
            ->assertJsonPath('data.name', 'New {{EntityName}}');

        $this->assertDatabaseHas('{{table_name}}', [
            'name' => 'New {{EntityName}}',
            'category_id' => $category->id,
        ]);
    }

    public function test_create_{{entityName}}_validates_required_fields(): void
    {
        Sanctum::actingAs($this->admin);

        $response = $this->postJson('/api/{{entityNames}}', []);

        $response
            ->assertUnprocessable()
            ->assertJsonValidationErrors(['name', 'price', 'category_id']);
    }

    public function test_create_{{entityName}}_validates_unique_name(): void
    {
        Sanctum::actingAs($this->admin);

        {{EntityName}}::factory()->create(['name' => 'Existing Name']);
        $category = Category::factory()->create();

        $response = $this->postJson('/api/{{entityNames}}', [
            'name' => 'Existing Name',
            'price' => 50.00,
            'category_id' => $category->id,
        ]);

        $response
            ->assertUnprocessable()
            ->assertJsonValidationErrors(['name']);
    }

    public function test_regular_user_cannot_create_{{entityName}}(): void
    {
        Sanctum::actingAs($this->user);

        $response = $this->postJson('/api/{{entityNames}}', [
            'name' => 'New {{EntityName}}',
            'price' => 99.99,
        ]);

        $response->assertForbidden();
    }

    // ==========================================
    // UPDATE TESTS
    // ==========================================

    public function test_can_update_{{entityName}}(): void
    {
        Sanctum::actingAs($this->admin);

        ${{entityName}} = {{EntityName}}::factory()->create();

        $response = $this->putJson("/api/{{entityNames}}/{${{entityName}}->id}", [
            'name' => 'Updated Name',
        ]);

        $response
            ->assertOk()
            ->assertJsonPath('data.name', 'Updated Name');

        $this->assertDatabaseHas('{{table_name}}', [
            'id' => ${{entityName}}->id,
            'name' => 'Updated Name',
        ]);
    }

    public function test_owner_can_update_own_{{entityName}}(): void
    {
        ${{entityName}} = {{EntityName}}::factory()->create(['user_id' => $this->user->id]);

        Sanctum::actingAs($this->user);

        $response = $this->putJson("/api/{{entityNames}}/{${{entityName}}->id}", [
            'name' => 'Updated by Owner',
        ]);

        $response->assertOk();
    }

    public function test_user_cannot_update_others_{{entityName}}(): void
    {
        $other = User::factory()->create();
        ${{entityName}} = {{EntityName}}::factory()->create(['user_id' => $other->id]);

        Sanctum::actingAs($this->user);

        $response = $this->putJson("/api/{{entityNames}}/{${{entityName}}->id}", [
            'name' => 'Updated',
        ]);

        $response->assertForbidden();
    }

    // ==========================================
    // DELETE TESTS
    // ==========================================

    public function test_can_delete_{{entityName}}(): void
    {
        Sanctum::actingAs($this->admin);

        ${{entityName}} = {{EntityName}}::factory()->create();

        $response = $this->deleteJson("/api/{{entityNames}}/{${{entityName}}->id}");

        $response->assertNoContent();

        $this->assertSoftDeleted('{{table_name}}', ['id' => ${{entityName}}->id]);
    }

    public function test_regular_user_cannot_delete_{{entityName}}(): void
    {
        $other = User::factory()->create();
        ${{entityName}} = {{EntityName}}::factory()->create(['user_id' => $other->id]);

        Sanctum::actingAs($this->user);

        $response = $this->deleteJson("/api/{{entityNames}}/{${{entityName}}->id}");

        $response->assertForbidden();
    }

    // ==========================================
    // AUTHENTICATION TESTS
    // ==========================================

    public function test_unauthenticated_user_cannot_access_{{entityNames}}(): void
    {
        $response = $this->getJson('/api/{{entityNames}}');

        $response->assertUnauthorized();
    }
}
```

## Unit Test

```php
<?php
// tests/Unit/Services/{{EntityName}}ServiceTest.php
namespace Tests\Unit\Services;

use App\Models\{{EntityName}};
use App\Models\Category;
use App\Repositories\{{EntityName}}Repository;
use App\Services\{{EntityName}}Service;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Mockery;
use Mockery\MockInterface;
use Tests\TestCase;

class {{EntityName}}ServiceTest extends TestCase
{
    use RefreshDatabase;

    protected {{EntityName}}Service $service;
    protected MockInterface $repository;

    protected function setUp(): void
    {
        parent::setUp();

        $this->repository = Mockery::mock({{EntityName}}Repository::class);
        $this->service = new {{EntityName}}Service($this->repository);
    }

    protected function tearDown(): void
    {
        Mockery::close();
        parent::tearDown();
    }

    public function test_creates_{{entityName}}(): void
    {
        $category = Category::factory()->create();
        $data = [
            'name' => 'Test {{EntityName}}',
            'category_id' => $category->id,
        ];

        ${{entityName}} = new {{EntityName}}($data);
        ${{entityName}}->id = 'test-uuid';

        $this->repository
            ->shouldReceive('create')
            ->once()
            ->andReturn(${{entityName}});

        $result = $this->service->create($data);

        $this->assertInstanceOf({{EntityName}}::class, $result);
        $this->assertEquals('Test {{EntityName}}', $result->name);
    }

    public function test_updates_{{entityName}}(): void
    {
        ${{entityName}} = {{EntityName}}::factory()->make(['id' => 'test-uuid']);
        $data = ['name' => 'Updated Name'];

        $this->repository
            ->shouldReceive('update')
            ->once()
            ->with(${{entityName}}, Mockery::on(fn ($d) => $d['name'] === 'Updated Name'))
            ->andReturnUsing(function ($p, $d) {
                $p->fill($d);
                return $p;
            });

        $result = $this->service->update(${{entityName}}, $data);

        $this->assertEquals('Updated Name', $result->name);
    }

    public function test_deletes_{{entityName}}(): void
    {
        ${{entityName}} = {{EntityName}}::factory()->make(['id' => 'test-uuid']);

        $this->repository
            ->shouldReceive('delete')
            ->once()
            ->with(${{entityName}})
            ->andReturn(true);

        $result = $this->service->delete(${{entityName}});

        $this->assertTrue($result);
    }
}
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{EntityName}}` | PascalCase entity name | `Product` |
| `{{entityName}}` | camelCase entity name | `product` |
| `{{entityNames}}` | camelCase plural | `products` |
| `{{table_name}}` | snake_case plural table name | `products` |
