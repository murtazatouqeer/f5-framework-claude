---
name: laravel-repository
description: Template for Laravel Repository Classes
applies_to: laravel
type: template
---

# Laravel Repository Template

## Repository Interface

```php
<?php
// app/Repositories/Contracts/{{EntityName}}RepositoryInterface.php
namespace App\Repositories\Contracts;

use App\Models\{{EntityName}};
use Illuminate\Contracts\Pagination\LengthAwarePaginator;
use Illuminate\Database\Eloquent\Collection;

interface {{EntityName}}RepositoryInterface
{
    public function paginate(int $perPage = 15, array $filters = []): LengthAwarePaginator;

    public function all(array $filters = []): Collection;

    public function find(string $id): ?{{EntityName}};

    public function findOrFail(string $id): {{EntityName}};

    public function create(array $data): {{EntityName}};

    public function update({{EntityName}} ${{entityName}}, array $data): {{EntityName}};

    public function delete({{EntityName}} ${{entityName}}): bool;
}
```

## Repository Implementation

```php
<?php
// app/Repositories/{{EntityName}}Repository.php
namespace App\Repositories;

use App\Models\{{EntityName}};
use App\Repositories\Contracts\{{EntityName}}RepositoryInterface;
use Illuminate\Contracts\Pagination\LengthAwarePaginator;
use Illuminate\Database\Eloquent\Builder;
use Illuminate\Database\Eloquent\Collection;

class {{EntityName}}Repository implements {{EntityName}}RepositoryInterface
{
    public function __construct(
        protected {{EntityName}} $model
    ) {}

    /**
     * Get paginated list of {{entityNames}}.
     *
     * @param int $perPage
     * @param array $filters
     * @return LengthAwarePaginator
     */
    public function paginate(int $perPage = 15, array $filters = []): LengthAwarePaginator
    {
        return $this->applyFilters($this->baseQuery(), $filters)
            ->latest()
            ->paginate($perPage);
    }

    /**
     * Get all {{entityNames}}.
     *
     * @param array $filters
     * @return Collection
     */
    public function all(array $filters = []): Collection
    {
        return $this->applyFilters($this->baseQuery(), $filters)
            ->latest()
            ->get();
    }

    /**
     * Find a {{entityName}} by ID.
     *
     * @param string $id
     * @return {{EntityName}}|null
     */
    public function find(string $id): ?{{EntityName}}
    {
        return $this->baseQuery()->find($id);
    }

    /**
     * Find a {{entityName}} by ID or fail.
     *
     * @param string $id
     * @return {{EntityName}}
     */
    public function findOrFail(string $id): {{EntityName}}
    {
        return $this->baseQuery()->findOrFail($id);
    }

    /**
     * Find a {{entityName}} by slug.
     *
     * @param string $slug
     * @return {{EntityName}}|null
     */
    public function findBySlug(string $slug): ?{{EntityName}}
    {
        return $this->baseQuery()->where('slug', $slug)->first();
    }

    /**
     * Create a new {{entityName}}.
     *
     * @param array $data
     * @return {{EntityName}}
     */
    public function create(array $data): {{EntityName}}
    {
        return $this->model->create($data);
    }

    /**
     * Update a {{entityName}}.
     *
     * @param {{EntityName}} ${{entityName}}
     * @param array $data
     * @return {{EntityName}}
     */
    public function update({{EntityName}} ${{entityName}}, array $data): {{EntityName}}
    {
        ${{entityName}}->update($data);
        return ${{entityName}};
    }

    /**
     * Delete a {{entityName}}.
     *
     * @param {{EntityName}} ${{entityName}}
     * @return bool
     */
    public function delete({{EntityName}} ${{entityName}}): bool
    {
        return ${{entityName}}->delete();
    }

    /**
     * Get the base query with common eager loads.
     *
     * @return Builder
     */
    protected function baseQuery(): Builder
    {
        return $this->model
            ->newQuery()
            ->with(['category'])
            ->withCount(['items']);
    }

    /**
     * Apply filters to the query.
     *
     * @param Builder $query
     * @param array $filters
     * @return Builder
     */
    protected function applyFilters(Builder $query, array $filters): Builder
    {
        // Search filter
        if (!empty($filters['search'])) {
            $query->search($filters['search']);
        }

        // Status filter
        if (!empty($filters['status'])) {
            $query->where('status', $filters['status']);
        }

        // Category filter
        if (!empty($filters['category_id'])) {
            $query->where('category_id', $filters['category_id']);
        }

        // Date range filter
        if (!empty($filters['from_date'])) {
            $query->whereDate('created_at', '>=', $filters['from_date']);
        }

        if (!empty($filters['to_date'])) {
            $query->whereDate('created_at', '<=', $filters['to_date']);
        }

        // Active only
        if (!empty($filters['active_only'])) {
            $query->active();
        }

        // Sorting
        if (!empty($filters['sort_by'])) {
            $direction = $filters['sort_direction'] ?? 'asc';
            $query->orderBy($filters['sort_by'], $direction);
        }

        return $query;
    }

    /**
     * Get featured {{entityNames}}.
     *
     * @param int $limit
     * @return Collection
     */
    public function getFeatured(int $limit = 10): Collection
    {
        return $this->baseQuery()
            ->active()
            ->where('is_featured', true)
            ->latest()
            ->limit($limit)
            ->get();
    }

    /**
     * Get {{entityNames}} by category.
     *
     * @param string $categoryId
     * @param int $perPage
     * @return LengthAwarePaginator
     */
    public function getByCategory(string $categoryId, int $perPage = 15): LengthAwarePaginator
    {
        return $this->baseQuery()
            ->where('category_id', $categoryId)
            ->active()
            ->latest()
            ->paginate($perPage);
    }

    /**
     * Get related {{entityNames}}.
     *
     * @param {{EntityName}} ${{entityName}}
     * @param int $limit
     * @return Collection
     */
    public function getRelated({{EntityName}} ${{entityName}}, int $limit = 5): Collection
    {
        return $this->baseQuery()
            ->where('id', '!=', ${{entityName}}->id)
            ->where('category_id', ${{entityName}}->category_id)
            ->active()
            ->inRandomOrder()
            ->limit($limit)
            ->get();
    }
}
```

## Service Provider Registration

```php
<?php
// app/Providers/RepositoryServiceProvider.php
namespace App\Providers;

use Illuminate\Support\ServiceProvider;
use App\Repositories\{{EntityName}}Repository;
use App\Repositories\Contracts\{{EntityName}}RepositoryInterface;

class RepositoryServiceProvider extends ServiceProvider
{
    public function register(): void
    {
        $this->app->bind(
            {{EntityName}}RepositoryInterface::class,
            {{EntityName}}Repository::class
        );
    }
}
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{EntityName}}` | PascalCase entity name | `Product` |
| `{{entityName}}` | camelCase entity name | `product` |
| `{{entityNames}}` | camelCase plural | `products` |
