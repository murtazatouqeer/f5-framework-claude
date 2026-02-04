---
name: laravel-eloquent-patterns
description: Eloquent ORM patterns and best practices
applies_to: laravel
category: database
---

# Laravel Eloquent Patterns

## Model Definition

```php
<?php
// app/Models/Product.php
namespace App\Models;

use App\Enums\ProductStatus;
use App\Models\Concerns\HasUuid;
use Illuminate\Database\Eloquent\Casts\Attribute;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\BelongsToMany;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Database\Eloquent\SoftDeletes;
use Illuminate\Database\Eloquent\Builder;

class Product extends Model
{
    use HasFactory, HasUuid, SoftDeletes;

    /**
     * The table associated with the model.
     */
    protected $table = 'products';

    /**
     * The primary key type.
     */
    protected $keyType = 'string';

    /**
     * Indicates if the IDs are auto-incrementing.
     */
    public $incrementing = false;

    /**
     * The attributes that are mass assignable.
     */
    protected $fillable = [
        'name',
        'slug',
        'description',
        'price',
        'compare_price',
        'status',
        'category_id',
        'user_id',
        'metadata',
        'is_featured',
        'published_at',
    ];

    /**
     * The attributes that should be cast.
     */
    protected $casts = [
        'price' => 'decimal:2',
        'compare_price' => 'decimal:2',
        'status' => ProductStatus::class,
        'metadata' => 'array',
        'is_featured' => 'boolean',
        'published_at' => 'datetime',
    ];

    /**
     * The model's default values for attributes.
     */
    protected $attributes = [
        'status' => 'draft',
        'is_featured' => false,
    ];

    /**
     * The accessors to append to the model's array form.
     */
    protected $appends = [];

    /**
     * The relationships that should be touched on save.
     */
    protected $touches = ['category'];
}
```

## Accessors & Mutators (Laravel 11+)

```php
<?php
use Illuminate\Database\Eloquent\Casts\Attribute;
use Illuminate\Support\Str;

class Product extends Model
{
    /**
     * Get the product's formatted price.
     */
    protected function formattedPrice(): Attribute
    {
        return Attribute::get(
            fn () => number_format($this->price, 2) . ' USD'
        );
    }

    /**
     * Determine if the product is on sale.
     */
    protected function isOnSale(): Attribute
    {
        return Attribute::get(
            fn () => $this->compare_price && $this->compare_price > $this->price
        );
    }

    /**
     * Get the discount percentage.
     */
    protected function discountPercentage(): Attribute
    {
        return Attribute::get(function () {
            if (!$this->is_on_sale) {
                return 0;
            }
            return round((1 - $this->price / $this->compare_price) * 100);
        });
    }

    /**
     * Get/set the name (with transformation).
     */
    protected function name(): Attribute
    {
        return Attribute::make(
            get: fn (string $value) => ucfirst($value),
            set: fn (string $value) => strtolower(trim($value))
        );
    }

    /**
     * Auto-generate slug from name.
     */
    protected function slug(): Attribute
    {
        return Attribute::make(
            get: fn ($value) => $value,
            set: fn ($value) => Str::slug($value ?: $this->name)
        );
    }
}
```

## Custom Casts

```php
<?php
// app/Casts/MoneyCast.php
namespace App\Casts;

use Illuminate\Contracts\Database\Eloquent\CastsAttributes;
use Illuminate\Database\Eloquent\Model;

class MoneyCast implements CastsAttributes
{
    public function __construct(
        protected string $currency = 'USD'
    ) {}

    /**
     * Cast the given value.
     */
    public function get(Model $model, string $key, mixed $value, array $attributes): ?Money
    {
        if ($value === null) {
            return null;
        }

        return new Money($value, $this->currency);
    }

    /**
     * Prepare the given value for storage.
     */
    public function set(Model $model, string $key, mixed $value, array $attributes): ?int
    {
        if ($value === null) {
            return null;
        }

        return $value instanceof Money ? $value->cents : $value;
    }
}

// Usage in Model
protected $casts = [
    'price' => MoneyCast::class . ':USD',
    'discount' => MoneyCast::class . ':USD',
];
```

## Value Objects with Casts

```php
<?php
// app/ValueObjects/Address.php
namespace App\ValueObjects;

use Illuminate\Contracts\Database\Eloquent\Castable;
use Illuminate\Contracts\Support\Arrayable;

class Address implements Castable, Arrayable
{
    public function __construct(
        public readonly string $street,
        public readonly string $city,
        public readonly string $state,
        public readonly string $zipCode,
        public readonly string $country = 'US'
    ) {}

    public static function castUsing(array $arguments): string
    {
        return AddressCast::class;
    }

    public function toArray(): array
    {
        return [
            'street' => $this->street,
            'city' => $this->city,
            'state' => $this->state,
            'zip_code' => $this->zipCode,
            'country' => $this->country,
        ];
    }
}

// app/Casts/AddressCast.php
namespace App\Casts;

use App\ValueObjects\Address;
use Illuminate\Contracts\Database\Eloquent\CastsAttributes;
use Illuminate\Database\Eloquent\Model;

class AddressCast implements CastsAttributes
{
    public function get(Model $model, string $key, mixed $value, array $attributes): ?Address
    {
        if ($value === null) {
            return null;
        }

        $data = json_decode($value, true);

        return new Address(
            street: $data['street'],
            city: $data['city'],
            state: $data['state'],
            zipCode: $data['zip_code'],
            country: $data['country'] ?? 'US'
        );
    }

    public function set(Model $model, string $key, mixed $value, array $attributes): ?string
    {
        if ($value === null) {
            return null;
        }

        return json_encode($value->toArray());
    }
}

// Usage
protected $casts = [
    'billing_address' => Address::class,
    'shipping_address' => Address::class,
];
```

## Model Events

```php
<?php
class Product extends Model
{
    /**
     * The "booted" method of the model.
     */
    protected static function booted(): void
    {
        // Before creating
        static::creating(function (Product $product) {
            if (empty($product->slug)) {
                $product->slug = Str::slug($product->name);
            }
        });

        // After creating
        static::created(function (Product $product) {
            // Clear cache, send notifications, etc.
            Cache::tags(['products'])->flush();
        });

        // Before updating
        static::updating(function (Product $product) {
            if ($product->isDirty('name')) {
                $product->slug = Str::slug($product->name);
            }
        });

        // Before deleting
        static::deleting(function (Product $product) {
            // Clean up related data
            $product->tags()->detach();
            $product->images()->delete();
        });

        // After soft deleting
        static::softDeleted(function (Product $product) {
            // Additional cleanup after soft delete
        });
    }
}
```

## Model Observers

```php
<?php
// app/Observers/ProductObserver.php
namespace App\Observers;

use App\Models\Product;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Str;

class ProductObserver
{
    /**
     * Handle the Product "creating" event.
     */
    public function creating(Product $product): void
    {
        if (empty($product->slug)) {
            $product->slug = Str::slug($product->name);
        }
    }

    /**
     * Handle the Product "created" event.
     */
    public function created(Product $product): void
    {
        Cache::tags(['products', 'category_' . $product->category_id])->flush();
    }

    /**
     * Handle the Product "updated" event.
     */
    public function updated(Product $product): void
    {
        Cache::tags(['products', 'product_' . $product->id])->flush();
    }

    /**
     * Handle the Product "deleted" event.
     */
    public function deleted(Product $product): void
    {
        // Clean up related resources
        $product->tags()->detach();

        Cache::tags(['products'])->flush();
    }

    /**
     * Handle the Product "forceDeleted" event.
     */
    public function forceDeleted(Product $product): void
    {
        // Clean up files, etc.
        Storage::delete($product->images->pluck('path')->toArray());
    }
}

// Register in AppServiceProvider
public function boot(): void
{
    Product::observe(ProductObserver::class);
}
```

## Global Scopes

```php
<?php
// app/Models/Scopes/ActiveScope.php
namespace App\Models\Scopes;

use Illuminate\Database\Eloquent\Builder;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Scope;

class ActiveScope implements Scope
{
    /**
     * Apply the scope to a given Eloquent query builder.
     */
    public function apply(Builder $builder, Model $model): void
    {
        $builder->where($model->getTable() . '.status', 'active');
    }
}

// Apply in model
protected static function booted(): void
{
    static::addGlobalScope(new ActiveScope);
}

// Remove when needed
Product::withoutGlobalScope(ActiveScope::class)->get();
Product::withoutGlobalScopes()->get(); // Remove all
```

## Prunable Models

```php
<?php
use Illuminate\Database\Eloquent\Prunable;

class AuditLog extends Model
{
    use Prunable;

    /**
     * Get the prunable model query.
     */
    public function prunable(): Builder
    {
        return static::where('created_at', '<=', now()->subMonths(6));
    }

    /**
     * Prepare the model for pruning.
     */
    protected function pruning(): void
    {
        // Clean up related files, etc.
    }
}

// Run via scheduler
$schedule->command('model:prune')->daily();
```

## Best Practices

### DO

1. **Use Casts**: For type conversion and value objects
2. **Use Accessors**: For computed/derived attributes
3. **Use Observers**: For complex event handling
4. **Use Global Scopes**: For default query constraints
5. **Define Relationships**: Explicitly in model

### DON'T

1. **Fat Models**: Business logic belongs in services
2. **Complex Queries in Models**: Use repositories
3. **Skip Validation**: Models should have validation rules
4. **Ignore Mass Assignment**: Always define fillable/guarded
5. **Query in Accessors**: Leads to N+1 problems
