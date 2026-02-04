---
name: laravel-query-scopes
description: Eloquent query scopes for reusable query constraints
applies_to: laravel
category: database
---

# Laravel Query Scopes

## Local Scopes

Local scopes allow you to define reusable query constraints.

```php
<?php
namespace App\Models;

use App\Enums\ProductStatus;
use Illuminate\Database\Eloquent\Builder;
use Illuminate\Database\Eloquent\Model;

class Product extends Model
{
    /**
     * Scope to only include active products.
     */
    public function scopeActive(Builder $query): Builder
    {
        return $query->where('status', ProductStatus::Active);
    }

    /**
     * Scope to only include draft products.
     */
    public function scopeDraft(Builder $query): Builder
    {
        return $query->where('status', ProductStatus::Draft);
    }

    /**
     * Scope to only include featured products.
     */
    public function scopeFeatured(Builder $query): Builder
    {
        return $query->where('is_featured', true);
    }

    /**
     * Scope to only include published products.
     */
    public function scopePublished(Builder $query): Builder
    {
        return $query
            ->where('status', ProductStatus::Active)
            ->whereNotNull('published_at')
            ->where('published_at', '<=', now());
    }

    /**
     * Scope to filter by price range.
     */
    public function scopeInPriceRange(Builder $query, ?float $min, ?float $max): Builder
    {
        return $query
            ->when($min !== null, fn ($q) => $q->where('price', '>=', $min))
            ->when($max !== null, fn ($q) => $q->where('price', '<=', $max));
    }

    /**
     * Scope to search by name or description.
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
     * Scope to filter by category.
     */
    public function scopeInCategory(Builder $query, string|array|null $categoryIds): Builder
    {
        return $query->when($categoryIds, function ($q) use ($categoryIds) {
            $q->whereIn('category_id', (array) $categoryIds);
        });
    }

    /**
     * Scope to filter by date range.
     */
    public function scopeCreatedBetween(Builder $query, ?string $from, ?string $to): Builder
    {
        return $query
            ->when($from, fn ($q) => $q->whereDate('created_at', '>=', $from))
            ->when($to, fn ($q) => $q->whereDate('created_at', '<=', $to));
    }

    /**
     * Scope to order by popularity (based on order count).
     */
    public function scopePopular(Builder $query): Builder
    {
        return $query
            ->withCount('orders')
            ->orderByDesc('orders_count');
    }

    /**
     * Scope to get products on sale.
     */
    public function scopeOnSale(Builder $query): Builder
    {
        return $query
            ->whereNotNull('compare_price')
            ->whereColumn('compare_price', '>', 'price');
    }

    /**
     * Scope to filter by minimum discount percentage.
     */
    public function scopeWithMinDiscount(Builder $query, int $percentage): Builder
    {
        return $query
            ->whereNotNull('compare_price')
            ->whereRaw('(compare_price - price) / compare_price * 100 >= ?', [$percentage]);
    }
}
```

## Using Local Scopes

```php
<?php
// Chain multiple scopes
$products = Product::active()
    ->featured()
    ->inPriceRange(10, 100)
    ->search('laptop')
    ->get();

// With pagination
$products = Product::active()
    ->published()
    ->inCategory($categoryId)
    ->paginate(15);

// With eager loading
$products = Product::with(['category', 'tags'])
    ->active()
    ->popular()
    ->limit(10)
    ->get();

// Conditional scope usage
$products = Product::query()
    ->when($request->has('featured'), fn ($q) => $q->featured())
    ->when($request->search, fn ($q, $search) => $q->search($search))
    ->get();
```

## Dynamic Scopes

Scopes that accept parameters:

```php
<?php
class Product extends Model
{
    /**
     * Scope to filter by status.
     */
    public function scopeWithStatus(Builder $query, string|ProductStatus $status): Builder
    {
        $status = $status instanceof ProductStatus ? $status : ProductStatus::tryFrom($status);

        return $query->where('status', $status);
    }

    /**
     * Scope to filter by user.
     */
    public function scopeByUser(Builder $query, User|string $user): Builder
    {
        $userId = $user instanceof User ? $user->id : $user;

        return $query->where('user_id', $userId);
    }

    /**
     * Scope to filter by tags.
     */
    public function scopeWithTags(Builder $query, array $tagIds): Builder
    {
        return $query->whereHas('tags', function ($q) use ($tagIds) {
            $q->whereIn('tags.id', $tagIds);
        });
    }

    /**
     * Scope to filter by minimum rating.
     */
    public function scopeWithMinRating(Builder $query, float $rating): Builder
    {
        return $query
            ->withAvg('reviews', 'rating')
            ->having('reviews_avg_rating', '>=', $rating);
    }

    /**
     * Scope to sort by column and direction.
     */
    public function scopeSortBy(Builder $query, string $column, string $direction = 'asc'): Builder
    {
        $allowedColumns = ['name', 'price', 'created_at', 'updated_at'];
        $column = in_array($column, $allowedColumns) ? $column : 'created_at';
        $direction = in_array(strtolower($direction), ['asc', 'desc']) ? $direction : 'asc';

        return $query->orderBy($column, $direction);
    }
}
```

## Global Scopes

Global scopes apply automatically to all queries.

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

// app/Models/Scopes/TenantScope.php (Multi-tenancy)
class TenantScope implements Scope
{
    public function apply(Builder $builder, Model $model): void
    {
        if (auth()->check() && auth()->user()->tenant_id) {
            $builder->where($model->getTable() . '.tenant_id', auth()->user()->tenant_id);
        }
    }
}
```

### Applying Global Scopes

```php
<?php
class Product extends Model
{
    /**
     * The "booted" method of the model.
     */
    protected static function booted(): void
    {
        // Using class
        static::addGlobalScope(new ActiveScope);
        static::addGlobalScope(new TenantScope);

        // Using closure
        static::addGlobalScope('active', function (Builder $builder) {
            $builder->where('status', 'active');
        });
    }
}
```

### Removing Global Scopes

```php
<?php
// Remove specific scope
Product::withoutGlobalScope(ActiveScope::class)->get();
Product::withoutGlobalScope('active')->get();

// Remove multiple scopes
Product::withoutGlobalScopes([
    ActiveScope::class,
    TenantScope::class,
])->get();

// Remove all global scopes
Product::withoutGlobalScopes()->get();
```

## Scope Trait Pattern

For reusable scopes across models:

```php
<?php
// app/Models/Concerns/HasActiveScope.php
namespace App\Models\Concerns;

use Illuminate\Database\Eloquent\Builder;

trait HasActiveScope
{
    /**
     * Scope to only include active records.
     */
    public function scopeActive(Builder $query): Builder
    {
        return $query->where('status', 'active');
    }

    /**
     * Scope to only include inactive records.
     */
    public function scopeInactive(Builder $query): Builder
    {
        return $query->where('status', '!=', 'active');
    }
}

// app/Models/Concerns/HasSearchScope.php
trait HasSearchScope
{
    /**
     * Searchable columns. Override in model if needed.
     */
    protected function searchableColumns(): array
    {
        return ['name', 'description'];
    }

    /**
     * Scope to search by term.
     */
    public function scopeSearch(Builder $query, ?string $term): Builder
    {
        if (!$term) {
            return $query;
        }

        return $query->where(function ($q) use ($term) {
            foreach ($this->searchableColumns() as $column) {
                $q->orWhere($column, 'like', "%{$term}%");
            }
        });
    }
}

// app/Models/Concerns/HasDateFilters.php
trait HasDateFilters
{
    public function scopeCreatedAfter(Builder $query, string $date): Builder
    {
        return $query->where('created_at', '>=', $date);
    }

    public function scopeCreatedBefore(Builder $query, string $date): Builder
    {
        return $query->where('created_at', '<=', $date);
    }

    public function scopeCreatedToday(Builder $query): Builder
    {
        return $query->whereDate('created_at', today());
    }

    public function scopeCreatedThisWeek(Builder $query): Builder
    {
        return $query->whereBetween('created_at', [
            now()->startOfWeek(),
            now()->endOfWeek(),
        ]);
    }

    public function scopeCreatedThisMonth(Builder $query): Builder
    {
        return $query->whereMonth('created_at', now()->month)
            ->whereYear('created_at', now()->year);
    }
}

// Usage in model
class Product extends Model
{
    use HasActiveScope, HasSearchScope, HasDateFilters;

    protected function searchableColumns(): array
    {
        return ['name', 'description', 'sku'];
    }
}
```

## Advanced Scope Patterns

### Conditional Scopes

```php
<?php
class Product extends Model
{
    /**
     * Apply filters from request.
     */
    public function scopeFilter(Builder $query, array $filters): Builder
    {
        return $query
            ->when($filters['status'] ?? null, fn ($q, $status) => $q->where('status', $status))
            ->when($filters['category_id'] ?? null, fn ($q, $id) => $q->where('category_id', $id))
            ->when($filters['min_price'] ?? null, fn ($q, $min) => $q->where('price', '>=', $min))
            ->when($filters['max_price'] ?? null, fn ($q, $max) => $q->where('price', '<=', $max))
            ->when($filters['search'] ?? null, fn ($q, $term) => $q->search($term))
            ->when($filters['sort'] ?? null, fn ($q, $sort) => $q->sortBy($sort, $filters['order'] ?? 'asc'));
    }
}

// Usage
$products = Product::filter($request->validated())->paginate();
```

### Subquery Scopes

```php
<?php
class Product extends Model
{
    /**
     * Scope to add latest order date.
     */
    public function scopeWithLatestOrderDate(Builder $query): Builder
    {
        return $query->addSelect([
            'latest_order_at' => Order::select('created_at')
                ->whereColumn('product_id', 'products.id')
                ->latest()
                ->limit(1)
        ]);
    }

    /**
     * Scope to add total sales.
     */
    public function scopeWithTotalSales(Builder $query): Builder
    {
        return $query->addSelect([
            'total_sales' => OrderItem::selectRaw('COALESCE(SUM(quantity * price), 0)')
                ->whereColumn('product_id', 'products.id')
        ]);
    }
}
```

## Best Practices

1. **Name Clearly**: Use descriptive names like `active()`, `featured()`, `inPriceRange()`
2. **Return Builder**: Always return `Builder` for chaining
3. **Use `when()`**: For conditional scope logic
4. **Handle Null**: Check for null/empty parameters
5. **Validate Input**: Sanitize parameters in scopes
6. **Use Traits**: Share common scopes across models
7. **Document**: Add PHPDoc for complex scopes
