---
name: laravel-model-generator
description: Agent for generating Laravel Eloquent models with relationships and traits
applies_to: laravel
category: agent
---

# Laravel Model Generator Agent

## Purpose

Generate production-ready Laravel Eloquent models with relationships, scopes, accessors, and traits.

## Input Requirements

```yaml
required:
  - entity_name: string          # e.g., "Product"
  - table_name: string           # e.g., "products"

optional:
  - fillable: array              # Mass assignable fields
  - casts: object                # Attribute casting
  - relationships: array         # Model relationships
  - scopes: array                # Query scopes
  - traits: array                # Model traits to use
  - soft_deletes: boolean        # Use soft deletes (default: true)
  - uuid: boolean                # Use UUID primary key (default: true)
  - timestamps: boolean          # Use timestamps (default: true)
```

## Generation Process

### Step 1: Analyze Schema

```php
// Get table columns from migration or database
$columns = Schema::getColumnListing($tableName);
$columnTypes = collect($columns)->mapWithKeys(fn($col) => [
    $col => Schema::getColumnType($tableName, $col)
]);
```

### Step 2: Generate Model

```php
<?php
// app/Models/{{Entity}}.php
namespace App\Models;

use App\Models\Concerns\HasUuid;
use App\Enums\{{Entity}}Status;
use Illuminate\Database\Eloquent\Casts\Attribute;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\BelongsToMany;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Database\Eloquent\SoftDeletes;
use Illuminate\Database\Eloquent\Builder;

class {{Entity}} extends Model
{
    use HasFactory, HasUuid, SoftDeletes;

    /**
     * The table associated with the model.
     *
     * @var string
     */
    protected $table = '{{table_name}}';

    /**
     * The primary key type.
     *
     * @var string
     */
    protected $keyType = 'string';

    /**
     * Indicates if the IDs are auto-incrementing.
     *
     * @var bool
     */
    public $incrementing = false;

    /**
     * The attributes that are mass assignable.
     *
     * @var array<int, string>
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
    ];

    /**
     * The attributes that should be cast.
     *
     * @var array<string, string>
     */
    protected $casts = [
        'price' => 'decimal:2',
        'compare_price' => 'decimal:2',
        'status' => {{Entity}}Status::class,
        'metadata' => 'array',
        'is_featured' => 'boolean',
        'published_at' => 'datetime',
    ];

    /**
     * The model's default values for attributes.
     *
     * @var array
     */
    protected $attributes = [
        'status' => 'draft',
        'is_featured' => false,
    ];

    /**
     * The relationships that should always be loaded.
     *
     * @var array
     */
    protected $with = [];

    /**
     * The accessors to append to the model's array form.
     *
     * @var array
     */
    protected $appends = [
        'is_on_sale',
        'discount_percentage',
    ];

    /*
    |--------------------------------------------------------------------------
    | Relationships
    |--------------------------------------------------------------------------
    */

    /**
     * Get the category that owns the {{entity}}.
     */
    public function category(): BelongsTo
    {
        return $this->belongsTo(Category::class);
    }

    /**
     * Get the user that owns the {{entity}}.
     */
    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }

    /**
     * The tags that belong to the {{entity}}.
     */
    public function tags(): BelongsToMany
    {
        return $this->belongsToMany(Tag::class)
            ->withTimestamps();
    }

    /**
     * Get the images for the {{entity}}.
     */
    public function images(): HasMany
    {
        return $this->hasMany({{Entity}}Image::class)
            ->orderBy('sort_order');
    }

    /*
    |--------------------------------------------------------------------------
    | Scopes
    |--------------------------------------------------------------------------
    */

    /**
     * Scope a query to only include active {{entities}}.
     */
    public function scopeActive(Builder $query): Builder
    {
        return $query->where('status', {{Entity}}Status::Active);
    }

    /**
     * Scope a query to only include featured {{entities}}.
     */
    public function scopeFeatured(Builder $query): Builder
    {
        return $query->where('is_featured', true);
    }

    /**
     * Scope a query to filter by price range.
     */
    public function scopeInPriceRange(Builder $query, ?float $min, ?float $max): Builder
    {
        return $query
            ->when($min, fn ($q) => $q->where('price', '>=', $min))
            ->when($max, fn ($q) => $q->where('price', '<=', $max));
    }

    /**
     * Scope a query to search by name or description.
     */
    public function scopeSearch(Builder $query, ?string $term): Builder
    {
        return $query->when($term, function ($q) use ($term) {
            $q->where(function ($q) use ($term) {
                $q->where('name', 'like', "%{$term}%")
                  ->orWhere('description', 'like', "%{$term}%");
            });
        });
    }

    /**
     * Scope a query to filter by category.
     */
    public function scopeInCategory(Builder $query, string|array $categoryIds): Builder
    {
        return $query->whereIn('category_id', (array) $categoryIds);
    }

    /*
    |--------------------------------------------------------------------------
    | Accessors & Mutators
    |--------------------------------------------------------------------------
    */

    /**
     * Determine if the {{entity}} is on sale.
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
     * Get/set the slug attribute.
     */
    protected function slug(): Attribute
    {
        return Attribute::make(
            get: fn ($value) => $value,
            set: fn ($value) => \Str::slug($value)
        );
    }

    /*
    |--------------------------------------------------------------------------
    | Business Logic
    |--------------------------------------------------------------------------
    */

    /**
     * Publish the {{entity}}.
     *
     * @throws \DomainException
     */
    public function publish(): void
    {
        if ($this->status !== {{Entity}}Status::Draft) {
            throw new \DomainException('Only draft {{entities}} can be published');
        }

        $this->update([
            'status' => {{Entity}}Status::Active,
            'published_at' => now(),
        ]);
    }

    /**
     * Archive the {{entity}}.
     */
    public function archive(): void
    {
        $this->update(['status' => {{Entity}}Status::Archived]);
    }

    /**
     * Check if {{entity}} is purchasable.
     */
    public function isPurchasable(): bool
    {
        return $this->status === {{Entity}}Status::Active
            && $this->price > 0;
    }

    /*
    |--------------------------------------------------------------------------
    | Model Events
    |--------------------------------------------------------------------------
    */

    /**
     * Bootstrap the model and its traits.
     */
    protected static function booted(): void
    {
        static::creating(function ({{Entity}} ${{entity}}) {
            if (empty(${{entity}}->slug)) {
                ${{entity}}->slug = \Str::slug(${{entity}}->name);
            }
        });

        static::deleting(function ({{Entity}} ${{entity}}) {
            ${{entity}}->tags()->detach();
        });
    }
}
```

### Step 3: Generate UUID Trait

```php
<?php
// app/Models/Concerns/HasUuid.php
namespace App\Models\Concerns;

use Illuminate\Support\Str;

trait HasUuid
{
    /**
     * Initialize the trait.
     */
    protected function initializeHasUuid(): void
    {
        $this->usesUniqueIds = true;
    }

    /**
     * Get the columns that should receive a unique identifier.
     */
    public function uniqueIds(): array
    {
        return [$this->getKeyName()];
    }

    /**
     * Generate a new UUID for the model.
     */
    public function newUniqueId(): string
    {
        return (string) Str::uuid();
    }
}
```

### Step 4: Generate Enum

```php
<?php
// app/Enums/{{Entity}}Status.php
namespace App\Enums;

enum {{Entity}}Status: string
{
    case Draft = 'draft';
    case Active = 'active';
    case Archived = 'archived';

    public function label(): string
    {
        return match($this) {
            self::Draft => 'Draft',
            self::Active => 'Active',
            self::Archived => 'Archived',
        };
    }

    public function color(): string
    {
        return match($this) {
            self::Draft => 'gray',
            self::Active => 'green',
            self::Archived => 'red',
        };
    }
}
```

## Output Files

```
app/
├── Models/
│   ├── {{Entity}}.php           # Generated model
│   └── Concerns/
│       └── HasUuid.php          # UUID trait
├── Enums/
│   └── {{Entity}}Status.php     # Status enum
```

## Usage Example

```bash
# Generate model via agent
@laravel:model-generator {
  "entity_name": "Product",
  "table_name": "products",
  "fillable": ["name", "slug", "price", "status"],
  "relationships": ["category:belongsTo", "tags:belongsToMany"],
  "soft_deletes": true,
  "uuid": true
}
```

## Validation Checklist

- [ ] Table exists or migration is defined
- [ ] All relationships reference existing models
- [ ] Casts match column types
- [ ] Scopes are properly typed
- [ ] Enum values match database constraints
- [ ] Factory is generated
