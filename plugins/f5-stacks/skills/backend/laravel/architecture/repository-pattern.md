---
name: laravel-repository-pattern
description: Repository pattern for data access abstraction in Laravel
applies_to: laravel
category: architecture
---

# Laravel Repository Pattern

## Overview

The repository pattern abstracts data access logic, providing a clean API for data operations and improving testability.

## When to Use

- Complex query logic that shouldn't live in models
- Need to swap data sources (e.g., database to API)
- Testing requires data access mocking
- Multiple models need similar query patterns
- Complex filtering and sorting requirements

## Structure

```
app/
├── Repositories/
│   ├── Contracts/
│   │   ├── RepositoryInterface.php        # Base interface
│   │   └── ProductRepositoryInterface.php
│   ├── BaseRepository.php                 # Base implementation
│   └── ProductRepository.php
```

## Base Repository Interface

```php
<?php
// app/Repositories/Contracts/RepositoryInterface.php
namespace App\Repositories\Contracts;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Pagination\LengthAwarePaginator;
use Illuminate\Support\Collection;

interface RepositoryInterface
{
    /**
     * Get all records.
     */
    public function all(array $filters = []): Collection;

    /**
     * Get paginated records.
     */
    public function paginate(int $perPage = 15, array $filters = []): LengthAwarePaginator;

    /**
     * Find record by ID.
     */
    public function findById(string $id): ?Model;

    /**
     * Find record by attribute.
     */
    public function findBy(string $attribute, mixed $value): ?Model;

    /**
     * Create a new record.
     */
    public function create(array $data): Model;

    /**
     * Update an existing record.
     */
    public function update(Model $model, array $data): Model;

    /**
     * Delete a record.
     */
    public function delete(Model $model): bool;

    /**
     * Count records matching filters.
     */
    public function count(array $filters = []): int;

    /**
     * Check if record exists.
     */
    public function exists(string $id): bool;
}
```

## Base Repository Implementation

```php
<?php
// app/Repositories/BaseRepository.php
namespace App\Repositories;

use App\Repositories\Contracts\RepositoryInterface;
use Illuminate\Database\Eloquent\Builder;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Pagination\LengthAwarePaginator;
use Illuminate\Support\Collection;

abstract class BaseRepository implements RepositoryInterface
{
    public function __construct(
        protected Model $model
    ) {}

    /**
     * Get all records.
     */
    public function all(array $filters = []): Collection
    {
        return $this->applyFilters($this->model->query(), $filters)->get();
    }

    /**
     * Get paginated records.
     */
    public function paginate(int $perPage = 15, array $filters = []): LengthAwarePaginator
    {
        $query = $this->applyFilters($this->model->query(), $filters);
        $query = $this->applySorting($query, $filters);

        return $query->paginate($perPage);
    }

    /**
     * Find record by ID.
     */
    public function findById(string $id): ?Model
    {
        return $this->model->find($id);
    }

    /**
     * Find record by attribute.
     */
    public function findBy(string $attribute, mixed $value): ?Model
    {
        return $this->model->where($attribute, $value)->first();
    }

    /**
     * Create a new record.
     */
    public function create(array $data): Model
    {
        return $this->model->create($data);
    }

    /**
     * Update an existing record.
     */
    public function update(Model $model, array $data): Model
    {
        $model->update($data);
        return $model->fresh();
    }

    /**
     * Delete a record.
     */
    public function delete(Model $model): bool
    {
        return $model->delete();
    }

    /**
     * Count records matching filters.
     */
    public function count(array $filters = []): int
    {
        return $this->applyFilters($this->model->query(), $filters)->count();
    }

    /**
     * Check if record exists.
     */
    public function exists(string $id): bool
    {
        return $this->model->where('id', $id)->exists();
    }

    /**
     * Apply filters to query.
     */
    protected function applyFilters(Builder $query, array $filters): Builder
    {
        // Override in child classes
        return $query;
    }

    /**
     * Apply sorting to query.
     */
    protected function applySorting(Builder $query, array $filters): Builder
    {
        $sortBy = $filters['sort_by'] ?? 'created_at';
        $sortOrder = $filters['sort_order'] ?? 'desc';

        return $query->orderBy($sortBy, $sortOrder);
    }
}
```

## Concrete Repository Interface

```php
<?php
// app/Repositories/Contracts/ProductRepositoryInterface.php
namespace App\Repositories\Contracts;

use App\Models\Product;
use Illuminate\Support\Collection;

interface ProductRepositoryInterface extends RepositoryInterface
{
    /**
     * Find product by slug.
     */
    public function findBySlug(string $slug): ?Product;

    /**
     * Get featured products.
     */
    public function getFeatured(int $limit = 10): Collection;

    /**
     * Get products in category.
     */
    public function getByCategory(string $categoryId, int $limit = 20): Collection;

    /**
     * Get products on sale.
     */
    public function getOnSale(int $limit = 20): Collection;

    /**
     * Search products.
     */
    public function search(string $term, int $limit = 20): Collection;
}
```

## Concrete Repository Implementation

```php
<?php
// app/Repositories/ProductRepository.php
namespace App\Repositories;

use App\Enums\ProductStatus;
use App\Models\Product;
use App\Repositories\Contracts\ProductRepositoryInterface;
use Illuminate\Database\Eloquent\Builder;
use Illuminate\Support\Collection;

class ProductRepository extends BaseRepository implements ProductRepositoryInterface
{
    public function __construct(Product $model)
    {
        parent::__construct($model);
    }

    /**
     * Find product by slug.
     */
    public function findBySlug(string $slug): ?Product
    {
        return $this->model
            ->with(['category', 'tags', 'images'])
            ->where('slug', $slug)
            ->first();
    }

    /**
     * Get featured products.
     */
    public function getFeatured(int $limit = 10): Collection
    {
        return $this->model
            ->with(['category'])
            ->active()
            ->featured()
            ->limit($limit)
            ->get();
    }

    /**
     * Get products in category.
     */
    public function getByCategory(string $categoryId, int $limit = 20): Collection
    {
        return $this->model
            ->with(['tags'])
            ->active()
            ->where('category_id', $categoryId)
            ->limit($limit)
            ->get();
    }

    /**
     * Get products on sale.
     */
    public function getOnSale(int $limit = 20): Collection
    {
        return $this->model
            ->with(['category'])
            ->active()
            ->whereNotNull('compare_price')
            ->whereColumn('compare_price', '>', 'price')
            ->orderByRaw('(compare_price - price) / compare_price DESC')
            ->limit($limit)
            ->get();
    }

    /**
     * Search products.
     */
    public function search(string $term, int $limit = 20): Collection
    {
        return $this->model
            ->with(['category'])
            ->active()
            ->search($term)
            ->limit($limit)
            ->get();
    }

    /**
     * Apply filters to query.
     */
    protected function applyFilters(Builder $query, array $filters): Builder
    {
        return $query
            // Search filter
            ->when(isset($filters['search']) && $filters['search'], function ($q) use ($filters) {
                $q->where(function ($q) use ($filters) {
                    $q->where('name', 'like', "%{$filters['search']}%")
                      ->orWhere('description', 'like', "%{$filters['search']}%");
                });
            })
            // Status filter
            ->when(isset($filters['status']), function ($q) use ($filters) {
                $q->where('status', $filters['status']);
            })
            // Category filter
            ->when(isset($filters['category_id']), function ($q) use ($filters) {
                $q->where('category_id', $filters['category_id']);
            })
            // Price range filter
            ->when(isset($filters['min_price']), function ($q) use ($filters) {
                $q->where('price', '>=', $filters['min_price']);
            })
            ->when(isset($filters['max_price']), function ($q) use ($filters) {
                $q->where('price', '<=', $filters['max_price']);
            })
            // Featured filter
            ->when(isset($filters['is_featured']), function ($q) use ($filters) {
                $q->where('is_featured', $filters['is_featured']);
            })
            // Date range filter
            ->when(isset($filters['created_from']), function ($q) use ($filters) {
                $q->whereDate('created_at', '>=', $filters['created_from']);
            })
            ->when(isset($filters['created_to']), function ($q) use ($filters) {
                $q->whereDate('created_at', '<=', $filters['created_to']);
            })
            // Include soft deleted
            ->when(isset($filters['with_trashed']) && $filters['with_trashed'], function ($q) {
                $q->withTrashed();
            })
            // Eager load relationships
            ->when(isset($filters['include']), function ($q) use ($filters) {
                $includes = explode(',', $filters['include']);
                $allowed = ['category', 'tags', 'images', 'user'];
                $validated = array_intersect($includes, $allowed);
                $q->with($validated);
            });
    }

    /**
     * Apply sorting to query.
     */
    protected function applySorting(Builder $query, array $filters): Builder
    {
        $sortBy = $filters['sort_by'] ?? 'created_at';
        $sortOrder = $filters['sort_order'] ?? 'desc';

        $allowedSorts = ['name', 'price', 'created_at', 'updated_at'];

        if (in_array($sortBy, $allowedSorts)) {
            return $query->orderBy($sortBy, $sortOrder);
        }

        return $query->latest();
    }
}
```

## Query Builder Pattern

For complex queries, use a dedicated query builder:

```php
<?php
// app/Repositories/Builders/ProductQueryBuilder.php
namespace App\Repositories\Builders;

use App\Enums\ProductStatus;
use App\Models\Product;
use Illuminate\Database\Eloquent\Builder;

class ProductQueryBuilder
{
    protected Builder $query;

    public function __construct()
    {
        $this->query = Product::query();
    }

    public function active(): self
    {
        $this->query->where('status', ProductStatus::Active);
        return $this;
    }

    public function featured(): self
    {
        $this->query->where('is_featured', true);
        return $this;
    }

    public function inCategory(string $categoryId): self
    {
        $this->query->where('category_id', $categoryId);
        return $this;
    }

    public function priceRange(?float $min, ?float $max): self
    {
        if ($min !== null) {
            $this->query->where('price', '>=', $min);
        }
        if ($max !== null) {
            $this->query->where('price', '<=', $max);
        }
        return $this;
    }

    public function search(string $term): self
    {
        $this->query->where(function ($q) use ($term) {
            $q->where('name', 'like', "%{$term}%")
              ->orWhere('description', 'like', "%{$term}%");
        });
        return $this;
    }

    public function with(array $relations): self
    {
        $this->query->with($relations);
        return $this;
    }

    public function orderBy(string $column, string $direction = 'asc'): self
    {
        $this->query->orderBy($column, $direction);
        return $this;
    }

    public function getQuery(): Builder
    {
        return $this->query;
    }

    public function get()
    {
        return $this->query->get();
    }

    public function paginate(int $perPage = 15)
    {
        return $this->query->paginate($perPage);
    }
}

// Usage
$products = (new ProductQueryBuilder())
    ->active()
    ->featured()
    ->priceRange(10, 100)
    ->with(['category', 'tags'])
    ->orderBy('price', 'desc')
    ->paginate(20);
```

## Testing Repositories

```php
<?php
// tests/Unit/ProductRepositoryTest.php
namespace Tests\Unit;

use App\Enums\ProductStatus;
use App\Models\Product;
use App\Repositories\ProductRepository;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class ProductRepositoryTest extends TestCase
{
    use RefreshDatabase;

    protected ProductRepository $repository;

    protected function setUp(): void
    {
        parent::setUp();
        $this->repository = app(ProductRepository::class);
    }

    public function test_can_get_featured_products(): void
    {
        Product::factory()->count(3)->create(['is_featured' => true, 'status' => ProductStatus::Active]);
        Product::factory()->count(2)->create(['is_featured' => false, 'status' => ProductStatus::Active]);

        $featured = $this->repository->getFeatured(10);

        $this->assertCount(3, $featured);
        $this->assertTrue($featured->every(fn ($p) => $p->is_featured));
    }

    public function test_can_filter_by_price_range(): void
    {
        Product::factory()->create(['price' => 50, 'status' => ProductStatus::Active]);
        Product::factory()->create(['price' => 100, 'status' => ProductStatus::Active]);
        Product::factory()->create(['price' => 150, 'status' => ProductStatus::Active]);

        $products = $this->repository->paginate(15, [
            'min_price' => 60,
            'max_price' => 120,
        ]);

        $this->assertCount(1, $products);
        $this->assertEquals(100, $products->first()->price);
    }
}
```

## Best Practices

1. **Interface-First**: Always define contracts before implementations
2. **Single Responsibility**: One repository per entity/aggregate
3. **Encapsulate Queries**: Complex queries belong in repository methods
4. **Use Query Scopes**: Leverage Eloquent scopes for reusable conditions
5. **Eager Loading**: Handle relationship loading in repository
6. **No Business Logic**: Repositories only handle data access
