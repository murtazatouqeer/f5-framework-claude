---
name: laravel-unit-tests
description: Unit testing patterns for Laravel applications
applies_to: laravel
category: testing
---

# Laravel Unit Tests

## Overview

Unit tests focus on testing individual components in isolation, mocking external dependencies.

## Basic Unit Test Structure

```php
<?php
// tests/Unit/Services/ProductServiceTest.php
namespace Tests\Unit\Services;

use App\Models\Product;
use App\Models\Category;
use App\Repositories\ProductRepository;
use App\Services\ProductService;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Mockery;
use Mockery\MockInterface;
use Tests\TestCase;

class ProductServiceTest extends TestCase
{
    use RefreshDatabase;

    protected ProductService $service;
    protected MockInterface $repository;

    protected function setUp(): void
    {
        parent::setUp();

        $this->repository = Mockery::mock(ProductRepository::class);
        $this->service = new ProductService($this->repository);
    }

    protected function tearDown(): void
    {
        Mockery::close();
        parent::tearDown();
    }
}
```

## Testing Services

### Service with Repository

```php
<?php
public function test_create_product(): void
{
    $data = [
        'name' => 'New Product',
        'price' => 99.99,
        'category_id' => 'uuid-here',
    ];

    $product = new Product($data);
    $product->id = 'product-uuid';

    $this->repository
        ->shouldReceive('create')
        ->once()
        ->with($data)
        ->andReturn($product);

    $result = $this->service->create($data);

    $this->assertInstanceOf(Product::class, $result);
    $this->assertEquals('New Product', $result->name);
}

public function test_update_product(): void
{
    $product = new Product(['id' => 'uuid', 'name' => 'Old Name']);
    $data = ['name' => 'New Name'];

    $this->repository
        ->shouldReceive('update')
        ->once()
        ->with($product, $data)
        ->andReturnUsing(function ($p, $d) {
            $p->fill($d);
            return $p;
        });

    $result = $this->service->update($product, $data);

    $this->assertEquals('New Name', $result->name);
}

public function test_delete_product(): void
{
    $product = new Product(['id' => 'uuid']);

    $this->repository
        ->shouldReceive('delete')
        ->once()
        ->with($product)
        ->andReturn(true);

    $result = $this->service->delete($product);

    $this->assertTrue($result);
}
```

### Service with Business Logic

```php
<?php
// tests/Unit/Services/OrderServiceTest.php
namespace Tests\Unit\Services;

use App\Exceptions\InsufficientBalanceException;
use App\Exceptions\InsufficientStockException;
use App\Models\Order;
use App\Models\Product;
use App\Models\User;
use App\Services\OrderService;
use App\Services\PaymentService;
use App\Services\InventoryService;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Mockery;
use Tests\TestCase;

class OrderServiceTest extends TestCase
{
    use RefreshDatabase;

    protected OrderService $service;
    protected $paymentService;
    protected $inventoryService;

    protected function setUp(): void
    {
        parent::setUp();

        $this->paymentService = Mockery::mock(PaymentService::class);
        $this->inventoryService = Mockery::mock(InventoryService::class);

        $this->service = new OrderService(
            $this->paymentService,
            $this->inventoryService
        );
    }

    public function test_create_order_success(): void
    {
        $user = User::factory()->create(['balance' => 200]);
        $product = Product::factory()->create(['price' => 50, 'stock' => 10]);

        $items = [
            ['product_id' => $product->id, 'quantity' => 2],
        ];

        $this->inventoryService
            ->shouldReceive('checkAvailability')
            ->once()
            ->andReturn(true);

        $this->inventoryService
            ->shouldReceive('reserve')
            ->once()
            ->andReturn(true);

        $this->paymentService
            ->shouldReceive('charge')
            ->once()
            ->with($user, 100.00)
            ->andReturn(true);

        $order = $this->service->create($user, $items);

        $this->assertInstanceOf(Order::class, $order);
        $this->assertEquals(100.00, $order->total);
    }

    public function test_create_order_insufficient_stock(): void
    {
        $user = User::factory()->create(['balance' => 200]);
        $product = Product::factory()->create(['stock' => 1]);

        $items = [
            ['product_id' => $product->id, 'quantity' => 5],
        ];

        $this->inventoryService
            ->shouldReceive('checkAvailability')
            ->once()
            ->andReturn(false);

        $this->expectException(InsufficientStockException::class);

        $this->service->create($user, $items);
    }

    public function test_create_order_insufficient_balance(): void
    {
        $user = User::factory()->create(['balance' => 10]);
        $product = Product::factory()->create(['price' => 100, 'stock' => 10]);

        $items = [
            ['product_id' => $product->id, 'quantity' => 1],
        ];

        $this->inventoryService
            ->shouldReceive('checkAvailability')
            ->once()
            ->andReturn(true);

        $this->paymentService
            ->shouldReceive('charge')
            ->once()
            ->andThrow(new InsufficientBalanceException(100, 10));

        $this->expectException(InsufficientBalanceException::class);

        $this->service->create($user, $items);
    }
}
```

## Testing Models

### Model Attributes

```php
<?php
// tests/Unit/Models/ProductTest.php
namespace Tests\Unit\Models;

use App\Models\Product;
use App\Models\Category;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class ProductTest extends TestCase
{
    use RefreshDatabase;

    public function test_fillable_attributes(): void
    {
        $product = new Product([
            'name' => 'Test Product',
            'price' => 99.99,
            'secret_field' => 'should-not-be-set',
        ]);

        $this->assertEquals('Test Product', $product->name);
        $this->assertEquals(99.99, $product->price);
        $this->assertNull($product->secret_field);
    }

    public function test_casts(): void
    {
        $product = Product::factory()->create([
            'price' => '99.99',
            'is_active' => '1',
            'metadata' => ['key' => 'value'],
        ]);

        $this->assertIsFloat($product->price);
        $this->assertIsBool($product->is_active);
        $this->assertIsArray($product->metadata);
    }

    public function test_hidden_attributes(): void
    {
        $product = Product::factory()->create();
        $array = $product->toArray();

        $this->assertArrayNotHasKey('cost_price', $array);
        $this->assertArrayNotHasKey('internal_notes', $array);
    }
}
```

### Model Accessors and Mutators

```php
<?php
public function test_formatted_price_accessor(): void
{
    $product = Product::factory()->create(['price' => 1234.56]);

    $this->assertEquals('$1,234.56', $product->formatted_price);
}

public function test_slug_mutator(): void
{
    $product = new Product();
    $product->name = 'My Awesome Product';

    $this->assertEquals('my-awesome-product', $product->slug);
}

public function test_full_name_accessor(): void
{
    $user = User::factory()->create([
        'first_name' => 'John',
        'last_name' => 'Doe',
    ]);

    $this->assertEquals('John Doe', $user->full_name);
}
```

### Model Relationships

```php
<?php
public function test_belongs_to_category(): void
{
    $category = Category::factory()->create();
    $product = Product::factory()->create(['category_id' => $category->id]);

    $this->assertInstanceOf(Category::class, $product->category);
    $this->assertEquals($category->id, $product->category->id);
}

public function test_has_many_reviews(): void
{
    $product = Product::factory()
        ->hasReviews(3)
        ->create();

    $this->assertCount(3, $product->reviews);
}

public function test_belongs_to_many_tags(): void
{
    $product = Product::factory()
        ->hasTags(5)
        ->create();

    $this->assertCount(5, $product->tags);
}
```

### Model Scopes

```php
<?php
public function test_active_scope(): void
{
    Product::factory()->active()->count(3)->create();
    Product::factory()->inactive()->count(2)->create();

    $activeProducts = Product::active()->get();

    $this->assertCount(3, $activeProducts);
}

public function test_price_range_scope(): void
{
    Product::factory()->create(['price' => 50]);
    Product::factory()->create(['price' => 100]);
    Product::factory()->create(['price' => 150]);

    $products = Product::priceRange(75, 125)->get();

    $this->assertCount(1, $products);
    $this->assertEquals(100, $products->first()->price);
}

public function test_search_scope(): void
{
    Product::factory()->create(['name' => 'iPhone 15 Pro']);
    Product::factory()->create(['name' => 'Samsung Galaxy']);

    $results = Product::search('iPhone')->get();

    $this->assertCount(1, $results);
}
```

## Testing Value Objects

```php
<?php
// tests/Unit/ValueObjects/MoneyTest.php
namespace Tests\Unit\ValueObjects;

use App\ValueObjects\Money;
use InvalidArgumentException;
use Tests\TestCase;

class MoneyTest extends TestCase
{
    public function test_create_from_cents(): void
    {
        $money = Money::fromCents(1234);

        $this->assertEquals(1234, $money->cents());
        $this->assertEquals(12.34, $money->dollars());
    }

    public function test_create_from_dollars(): void
    {
        $money = Money::fromDollars(12.34);

        $this->assertEquals(1234, $money->cents());
    }

    public function test_addition(): void
    {
        $a = Money::fromDollars(10.00);
        $b = Money::fromDollars(5.50);

        $result = $a->add($b);

        $this->assertEquals(15.50, $result->dollars());
    }

    public function test_subtraction(): void
    {
        $a = Money::fromDollars(10.00);
        $b = Money::fromDollars(3.50);

        $result = $a->subtract($b);

        $this->assertEquals(6.50, $result->dollars());
    }

    public function test_cannot_be_negative(): void
    {
        $this->expectException(InvalidArgumentException::class);

        Money::fromCents(-100);
    }

    public function test_formatting(): void
    {
        $money = Money::fromDollars(1234.56);

        $this->assertEquals('$1,234.56', $money->format());
    }

    public function test_equality(): void
    {
        $a = Money::fromDollars(10.00);
        $b = Money::fromCents(1000);

        $this->assertTrue($a->equals($b));
    }
}
```

## Testing Actions/Commands

```php
<?php
// tests/Unit/Actions/CreateProductActionTest.php
namespace Tests\Unit\Actions;

use App\Actions\CreateProductAction;
use App\DTOs\ProductData;
use App\Models\Product;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class CreateProductActionTest extends TestCase
{
    use RefreshDatabase;

    public function test_creates_product_with_valid_data(): void
    {
        $action = new CreateProductAction();

        $data = new ProductData(
            name: 'Test Product',
            price: 99.99,
            description: 'A test product',
        );

        $product = $action->execute($data);

        $this->assertInstanceOf(Product::class, $product);
        $this->assertEquals('Test Product', $product->name);
        $this->assertDatabaseHas('products', ['name' => 'Test Product']);
    }

    public function test_generates_unique_slug(): void
    {
        Product::factory()->create(['slug' => 'test-product']);

        $action = new CreateProductAction();

        $data = new ProductData(
            name: 'Test Product',
            price: 99.99,
        );

        $product = $action->execute($data);

        $this->assertEquals('test-product-1', $product->slug);
    }
}
```

## Testing Validators

```php
<?php
// tests/Unit/Rules/ValidSlugTest.php
namespace Tests\Unit\Rules;

use App\Rules\ValidSlug;
use Tests\TestCase;

class ValidSlugTest extends TestCase
{
    protected ValidSlug $rule;

    protected function setUp(): void
    {
        parent::setUp();
        $this->rule = new ValidSlug();
    }

    /**
     * @dataProvider validSlugsProvider
     */
    public function test_valid_slugs(string $slug): void
    {
        $failed = false;

        $this->rule->validate('slug', $slug, function () use (&$failed) {
            $failed = true;
        });

        $this->assertFalse($failed, "Slug '{$slug}' should be valid");
    }

    /**
     * @dataProvider invalidSlugsProvider
     */
    public function test_invalid_slugs(string $slug): void
    {
        $failed = false;

        $this->rule->validate('slug', $slug, function () use (&$failed) {
            $failed = true;
        });

        $this->assertTrue($failed, "Slug '{$slug}' should be invalid");
    }

    public static function validSlugsProvider(): array
    {
        return [
            ['valid-slug'],
            ['another-valid-123'],
            ['simple'],
        ];
    }

    public static function invalidSlugsProvider(): array
    {
        return [
            ['Invalid-Slug'],
            ['has spaces'],
            ['special@chars'],
            ['admin'], // Reserved
        ];
    }
}
```

## Testing Events and Listeners

```php
<?php
// tests/Unit/Listeners/UpdateInventoryListenerTest.php
namespace Tests\Unit\Listeners;

use App\Events\OrderPlaced;
use App\Listeners\UpdateInventoryListener;
use App\Models\Order;
use App\Models\Product;
use App\Services\InventoryService;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Mockery;
use Tests\TestCase;

class UpdateInventoryListenerTest extends TestCase
{
    use RefreshDatabase;

    public function test_decrements_inventory_on_order(): void
    {
        $product = Product::factory()->create(['stock' => 10]);
        $order = Order::factory()
            ->hasItems(1, ['product_id' => $product->id, 'quantity' => 3])
            ->create();

        $inventoryService = Mockery::mock(InventoryService::class);
        $inventoryService
            ->shouldReceive('decrement')
            ->once()
            ->with($product->id, 3);

        $listener = new UpdateInventoryListener($inventoryService);
        $event = new OrderPlaced($order);

        $listener->handle($event);
    }
}
```

## Testing Jobs

```php
<?php
// tests/Unit/Jobs/ProcessOrderJobTest.php
namespace Tests\Unit\Jobs;

use App\Jobs\ProcessOrderJob;
use App\Models\Order;
use App\Services\OrderService;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Mockery;
use Tests\TestCase;

class ProcessOrderJobTest extends TestCase
{
    use RefreshDatabase;

    public function test_processes_order(): void
    {
        $order = Order::factory()->create(['status' => 'pending']);

        $orderService = Mockery::mock(OrderService::class);
        $orderService
            ->shouldReceive('process')
            ->once()
            ->with(Mockery::on(fn ($o) => $o->id === $order->id))
            ->andReturn(true);

        $this->app->instance(OrderService::class, $orderService);

        $job = new ProcessOrderJob($order);
        $job->handle($orderService);
    }

    public function test_retries_on_failure(): void
    {
        $job = new ProcessOrderJob(Order::factory()->create());

        $this->assertEquals(3, $job->tries);
        $this->assertEquals([10, 60, 300], $job->backoff());
    }
}
```

## Mocking Best Practices

```php
<?php
// Partial mocks
$service = Mockery::mock(ProductService::class)->makePartial();
$service->shouldReceive('externalApiCall')->andReturn(['data']);

// Spy (verify after the fact)
$spy = Mockery::spy(Logger::class);
$service = new ProductService($spy);
$service->create($data);
$spy->shouldHaveReceived('info')->once();

// Mock specific methods
$this->partialMock(ProductService::class, function ($mock) {
    $mock->shouldReceive('validateStock')->andReturn(true);
});

// Mock facades
Queue::fake();
Mail::fake();
Event::fake([ProductCreated::class]);
```

## Best Practices

1. **Test One Thing**: Each test should verify a single behavior
2. **Mock Dependencies**: Isolate the unit under test
3. **Use Data Providers**: For testing multiple inputs
4. **Name Clearly**: Test names should describe the expected behavior
5. **Arrange-Act-Assert**: Structure tests consistently
6. **Avoid Database**: Prefer mocking over database for true unit tests
7. **Test Edge Cases**: Null values, empty arrays, boundaries
