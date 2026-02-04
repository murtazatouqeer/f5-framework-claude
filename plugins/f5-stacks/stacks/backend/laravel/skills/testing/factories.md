---
name: laravel-factories
description: Model factory patterns for Laravel testing
applies_to: laravel
category: testing
---

# Laravel Model Factories

## Overview

Factories provide a convenient way to create model instances for testing with realistic, customizable data.

## Basic Factory Structure

```php
<?php
// database/factories/ProductFactory.php
namespace Database\Factories;

use App\Enums\ProductStatus;
use App\Models\Category;
use App\Models\Product;
use Illuminate\Database\Eloquent\Factories\Factory;
use Illuminate\Support\Str;

class ProductFactory extends Factory
{
    protected $model = Product::class;

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
            'sku' => strtoupper($this->faker->unique()->bothify('SKU-####-????')),
            'stock' => $this->faker->numberBetween(0, 100),
            'status' => ProductStatus::ACTIVE,
            'is_featured' => false,
            'category_id' => Category::factory(),
            'metadata' => [],
            'published_at' => now(),
        ];
    }
}
```

## Factory States

```php
<?php
// States for different product configurations
class ProductFactory extends Factory
{
    // ... definition() ...

    /**
     * Active product.
     */
    public function active(): static
    {
        return $this->state(fn (array $attributes) => [
            'status' => ProductStatus::ACTIVE,
            'published_at' => now(),
        ]);
    }

    /**
     * Inactive/Draft product.
     */
    public function inactive(): static
    {
        return $this->state(fn (array $attributes) => [
            'status' => ProductStatus::DRAFT,
            'published_at' => null,
        ]);
    }

    /**
     * Archived product.
     */
    public function archived(): static
    {
        return $this->state(fn (array $attributes) => [
            'status' => ProductStatus::ARCHIVED,
        ]);
    }

    /**
     * Featured product.
     */
    public function featured(): static
    {
        return $this->state(fn (array $attributes) => [
            'is_featured' => true,
        ]);
    }

    /**
     * On sale product.
     */
    public function onSale(): static
    {
        return $this->state(function (array $attributes) {
            $price = $attributes['price'];
            return [
                'compare_price' => $price * 1.5,
            ];
        });
    }

    /**
     * Out of stock product.
     */
    public function outOfStock(): static
    {
        return $this->state(fn (array $attributes) => [
            'stock' => 0,
        ]);
    }

    /**
     * Low stock product.
     */
    public function lowStock(): static
    {
        return $this->state(fn (array $attributes) => [
            'stock' => $this->faker->numberBetween(1, 5),
        ]);
    }

    /**
     * Expensive product.
     */
    public function expensive(): static
    {
        return $this->state(fn (array $attributes) => [
            'price' => $this->faker->randomFloat(2, 500, 2000),
        ]);
    }

    /**
     * Budget product.
     */
    public function budget(): static
    {
        return $this->state(fn (array $attributes) => [
            'price' => $this->faker->randomFloat(2, 1, 50),
        ]);
    }

    /**
     * With specific price.
     */
    public function withPrice(float $price): static
    {
        return $this->state(fn (array $attributes) => [
            'price' => $price,
        ]);
    }

    /**
     * Published at specific time.
     */
    public function publishedAt(\DateTimeInterface $date): static
    {
        return $this->state(fn (array $attributes) => [
            'published_at' => $date,
            'status' => ProductStatus::ACTIVE,
        ]);
    }
}
```

## Factory Relationships

```php
<?php
class ProductFactory extends Factory
{
    // ... definition() and states ...

    /**
     * Product with category.
     */
    public function hasCategory(): static
    {
        return $this->state(fn (array $attributes) => [
            'category_id' => Category::factory(),
        ]);
    }

    /**
     * Product with specific category.
     */
    public function forCategory(Category $category): static
    {
        return $this->state(fn (array $attributes) => [
            'category_id' => $category->id,
        ]);
    }

    /**
     * Configure relationships after creation.
     */
    public function configure(): static
    {
        return $this->afterCreating(function (Product $product) {
            // Default configuration after creation
        });
    }
}
```

## Using Factories in Tests

### Basic Usage

```php
<?php
// Create single instance
$product = Product::factory()->create();

// Create without persisting
$product = Product::factory()->make();

// Create multiple
$products = Product::factory()->count(5)->create();

// Create with specific attributes
$product = Product::factory()->create([
    'name' => 'Custom Name',
    'price' => 99.99,
]);
```

### Using States

```php
<?php
// Single state
$product = Product::factory()->active()->create();

// Multiple states
$product = Product::factory()
    ->active()
    ->featured()
    ->onSale()
    ->create();

// State with parameter
$product = Product::factory()
    ->withPrice(149.99)
    ->create();
```

### Creating with Relationships

```php
<?php
// Has many relationship
$product = Product::factory()
    ->hasReviews(5)
    ->create();

// Has many with attributes
$product = Product::factory()
    ->hasReviews(3, ['rating' => 5])
    ->create();

// Has many with factory states
$product = Product::factory()
    ->hasReviews(3, function (array $attributes, Product $product) {
        return ['title' => "Review for {$product->name}"];
    })
    ->create();

// Belongs to relationship
$category = Category::factory()->create();
$product = Product::factory()
    ->for($category)
    ->create();

// Many to many relationship
$product = Product::factory()
    ->hasTags(5)
    ->create();

// Attach existing models
$tags = Tag::factory()->count(3)->create();
$product = Product::factory()
    ->hasAttached($tags)
    ->create();

// With pivot data
$product = Product::factory()
    ->hasAttached(
        Tag::factory()->count(3),
        ['added_by' => 'admin']
    )
    ->create();
```

## User Factory

```php
<?php
// database/factories/UserFactory.php
namespace Database\Factories;

use App\Models\User;
use Illuminate\Database\Eloquent\Factories\Factory;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Str;

class UserFactory extends Factory
{
    protected $model = User::class;

    protected static ?string $password;

    public function definition(): array
    {
        return [
            'id' => Str::uuid(),
            'name' => fake()->name(),
            'email' => fake()->unique()->safeEmail(),
            'email_verified_at' => now(),
            'password' => static::$password ??= Hash::make('password'),
            'remember_token' => Str::random(10),
            'role' => 'user',
            'is_active' => true,
        ];
    }

    /**
     * Unverified email.
     */
    public function unverified(): static
    {
        return $this->state(fn (array $attributes) => [
            'email_verified_at' => null,
        ]);
    }

    /**
     * Admin user.
     */
    public function admin(): static
    {
        return $this->state(fn (array $attributes) => [
            'role' => 'admin',
        ]);
    }

    /**
     * Super admin user.
     */
    public function superAdmin(): static
    {
        return $this->state(fn (array $attributes) => [
            'role' => 'super_admin',
        ]);
    }

    /**
     * Manager user.
     */
    public function manager(): static
    {
        return $this->state(fn (array $attributes) => [
            'role' => 'manager',
        ]);
    }

    /**
     * Inactive user.
     */
    public function inactive(): static
    {
        return $this->state(fn (array $attributes) => [
            'is_active' => false,
        ]);
    }

    /**
     * Suspended user.
     */
    public function suspended(): static
    {
        return $this->state(fn (array $attributes) => [
            'suspended_at' => now(),
            'suspension_reason' => 'Policy violation',
        ]);
    }

    /**
     * With specific password.
     */
    public function withPassword(string $password): static
    {
        return $this->state(fn (array $attributes) => [
            'password' => Hash::make($password),
        ]);
    }

    /**
     * With subscription.
     */
    public function withSubscription(string $plan = 'premium'): static
    {
        return $this->afterCreating(function (User $user) use ($plan) {
            Subscription::factory()->for($user)->create([
                'plan' => $plan,
                'status' => 'active',
            ]);
        });
    }
}
```

## Order Factory

```php
<?php
// database/factories/OrderFactory.php
namespace Database\Factories;

use App\Enums\OrderStatus;
use App\Models\Order;
use App\Models\User;
use Illuminate\Database\Eloquent\Factories\Factory;
use Illuminate\Support\Str;

class OrderFactory extends Factory
{
    protected $model = Order::class;

    public function definition(): array
    {
        return [
            'id' => Str::uuid(),
            'order_number' => 'ORD-' . strtoupper(Str::random(8)),
            'user_id' => User::factory(),
            'status' => OrderStatus::PENDING,
            'subtotal' => 0,
            'tax' => 0,
            'shipping' => 0,
            'total' => 0,
            'notes' => null,
            'shipping_address' => [
                'name' => $this->faker->name(),
                'street' => $this->faker->streetAddress(),
                'city' => $this->faker->city(),
                'state' => $this->faker->state(),
                'zip' => $this->faker->postcode(),
                'country' => 'US',
            ],
        ];
    }

    /**
     * Pending order.
     */
    public function pending(): static
    {
        return $this->state(fn (array $attributes) => [
            'status' => OrderStatus::PENDING,
        ]);
    }

    /**
     * Processing order.
     */
    public function processing(): static
    {
        return $this->state(fn (array $attributes) => [
            'status' => OrderStatus::PROCESSING,
            'processed_at' => now(),
        ]);
    }

    /**
     * Shipped order.
     */
    public function shipped(): static
    {
        return $this->state(fn (array $attributes) => [
            'status' => OrderStatus::SHIPPED,
            'shipped_at' => now(),
            'tracking_number' => strtoupper(Str::random(12)),
        ]);
    }

    /**
     * Delivered order.
     */
    public function delivered(): static
    {
        return $this->state(fn (array $attributes) => [
            'status' => OrderStatus::DELIVERED,
            'delivered_at' => now(),
        ]);
    }

    /**
     * Cancelled order.
     */
    public function cancelled(): static
    {
        return $this->state(fn (array $attributes) => [
            'status' => OrderStatus::CANCELLED,
            'cancelled_at' => now(),
            'cancellation_reason' => 'Customer request',
        ]);
    }

    /**
     * With items and calculated totals.
     */
    public function withItems(int $count = 3): static
    {
        return $this->afterCreating(function (Order $order) use ($count) {
            $items = OrderItem::factory()
                ->count($count)
                ->for($order)
                ->create();

            $subtotal = $items->sum(fn ($item) => $item->price * $item->quantity);
            $tax = $subtotal * 0.1;
            $shipping = 9.99;

            $order->update([
                'subtotal' => $subtotal,
                'tax' => $tax,
                'shipping' => $shipping,
                'total' => $subtotal + $tax + $shipping,
            ]);
        });
    }
}
```

## Sequences and Complex Data

```php
<?php
use Illuminate\Database\Eloquent\Factories\Sequence;

// Sequential data
$products = Product::factory()
    ->count(4)
    ->state(new Sequence(
        ['status' => 'active'],
        ['status' => 'draft'],
        ['status' => 'archived'],
        ['status' => 'active'],
    ))
    ->create();

// Sequential with index
$products = Product::factory()
    ->count(5)
    ->state(new Sequence(
        fn (Sequence $sequence) => ['sort_order' => $sequence->index]
    ))
    ->create();

// Cycling through values
$products = Product::factory()
    ->count(10)
    ->sequence(
        ['category_id' => $category1->id],
        ['category_id' => $category2->id],
    )
    ->create();
```

## Factory Callbacks

```php
<?php
class ProductFactory extends Factory
{
    public function configure(): static
    {
        return $this
            ->afterMaking(function (Product $product) {
                // Called after make() but before create()
            })
            ->afterCreating(function (Product $product) {
                // Called after create()
                $product->searchable(); // Index in search
            });
    }
}

// In tests, use afterCreating for setup
Product::factory()
    ->afterCreating(function (Product $product) {
        // Attach images
        Image::factory()->count(3)->for($product)->create();
    })
    ->create();
```

## Faker Customization

```php
<?php
class ProductFactory extends Factory
{
    public function definition(): array
    {
        return [
            // Basic types
            'name' => $this->faker->words(3, true),
            'description' => $this->faker->paragraphs(3, true),
            'price' => $this->faker->randomFloat(2, 10, 1000),

            // Specific formats
            'email' => $this->faker->unique()->safeEmail(),
            'phone' => $this->faker->phoneNumber(),
            'url' => $this->faker->url(),

            // Dates
            'created_at' => $this->faker->dateTimeBetween('-1 year'),
            'published_at' => $this->faker->dateTimeBetween('-30 days', 'now'),

            // Images (placeholders)
            'image' => $this->faker->imageUrl(640, 480, 'products'),

            // Address components
            'address' => [
                'street' => $this->faker->streetAddress(),
                'city' => $this->faker->city(),
                'state' => $this->faker->stateAbbr(),
                'zip' => $this->faker->postcode(),
            ],

            // Random selection
            'status' => $this->faker->randomElement(['active', 'pending', 'inactive']),
            'category' => $this->faker->randomElement(Category::pluck('id')),

            // Boolean with weight
            'is_featured' => $this->faker->boolean(20), // 20% chance true

            // Conditionals
            'discount' => $this->faker->optional(0.3)->randomFloat(2, 5, 50),
        ];
    }
}
```

## Testing Data Builders (Alternative Pattern)

```php
<?php
// tests/Builders/ProductBuilder.php
namespace Tests\Builders;

use App\Models\Category;
use App\Models\Product;
use App\Models\Tag;

class ProductBuilder
{
    private array $attributes = [];
    private array $tags = [];
    private ?Category $category = null;

    public static function new(): self
    {
        return new self();
    }

    public function withName(string $name): self
    {
        $this->attributes['name'] = $name;
        return $this;
    }

    public function withPrice(float $price): self
    {
        $this->attributes['price'] = $price;
        return $this;
    }

    public function active(): self
    {
        $this->attributes['status'] = 'active';
        return $this;
    }

    public function featured(): self
    {
        $this->attributes['is_featured'] = true;
        return $this;
    }

    public function inCategory(Category $category): self
    {
        $this->category = $category;
        return $this;
    }

    public function withTags(array $tags): self
    {
        $this->tags = $tags;
        return $this;
    }

    public function create(): Product
    {
        if ($this->category) {
            $this->attributes['category_id'] = $this->category->id;
        }

        $product = Product::factory()->create($this->attributes);

        if (!empty($this->tags)) {
            $product->tags()->attach($this->tags);
        }

        return $product;
    }
}

// Usage in tests
$product = ProductBuilder::new()
    ->withName('Test Product')
    ->withPrice(99.99)
    ->active()
    ->featured()
    ->inCategory($electronics)
    ->withTags([$tagA->id, $tagB->id])
    ->create();
```

## Best Practices

1. **Minimal Defaults**: Factory definition should have minimal required data
2. **Use States**: Create states for common configurations
3. **Unique Constraints**: Use `unique()` for unique fields
4. **Related Models**: Use relationship methods instead of IDs
5. **Readable Tests**: States make test intent clear
6. **Avoid Overrides**: Prefer states over inline attribute overrides
7. **Realistic Data**: Use Faker for realistic test data
8. **Callback Cleanup**: Use configure() for post-creation setup
