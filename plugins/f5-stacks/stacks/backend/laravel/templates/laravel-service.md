---
name: laravel-service
description: Template for Laravel Service Classes
applies_to: laravel
type: template
---

# Laravel Service Template

## Service Class

```php
<?php
// app/Services/{{EntityName}}Service.php
namespace App\Services;

use App\Events\{{EntityName}}Created;
use App\Events\{{EntityName}}Deleted;
use App\Events\{{EntityName}}Updated;
use App\Exceptions\{{EntityName}}Exception;
use App\Models\{{EntityName}};
use App\Repositories\{{EntityName}}Repository;
use Illuminate\Contracts\Pagination\LengthAwarePaginator;
use Illuminate\Database\Eloquent\Collection;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Log;

class {{EntityName}}Service
{
    public function __construct(
        protected {{EntityName}}Repository $repository
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
        return $this->repository->paginate($perPage, $filters);
    }

    /**
     * Get all {{entityNames}}.
     *
     * @param array $filters
     * @return Collection
     */
    public function all(array $filters = []): Collection
    {
        return $this->repository->all($filters);
    }

    /**
     * Find a {{entityName}} by ID.
     *
     * @param string $id
     * @return {{EntityName}}|null
     */
    public function find(string $id): ?{{EntityName}}
    {
        return Cache::remember(
            "{{entity_name}}:{$id}",
            3600,
            fn () => $this->repository->find($id)
        );
    }

    /**
     * Find a {{entityName}} by ID or fail.
     *
     * @param string $id
     * @return {{EntityName}}
     * @throws \Illuminate\Database\Eloquent\ModelNotFoundException
     */
    public function findOrFail(string $id): {{EntityName}}
    {
        return $this->repository->findOrFail($id);
    }

    /**
     * Create a new {{entityName}}.
     *
     * @param array $data
     * @return {{EntityName}}
     * @throws {{EntityName}}Exception
     */
    public function create(array $data): {{EntityName}}
    {
        return DB::transaction(function () use ($data) {
            // Prepare data
            $data = $this->prepareData($data);

            // Create {{entityName}}
            ${{entityName}} = $this->repository->create($data);

            // Handle relationships
            if (isset($data['tags'])) {
                ${{entityName}}->tags()->sync($data['tags']);
            }

            // Dispatch event
            event(new {{EntityName}}Created(${{entityName}}));

            // Clear cache
            $this->clearCache();

            Log::info('{{EntityName}} created', ['id' => ${{entityName}}->id]);

            return ${{entityName}}->fresh(['tags', 'category']);
        });
    }

    /**
     * Update an existing {{entityName}}.
     *
     * @param {{EntityName}} ${{entityName}}
     * @param array $data
     * @return {{EntityName}}
     * @throws {{EntityName}}Exception
     */
    public function update({{EntityName}} ${{entityName}}, array $data): {{EntityName}}
    {
        return DB::transaction(function () use (${{entityName}}, $data) {
            // Prepare data
            $data = $this->prepareData($data);

            // Update {{entityName}}
            ${{entityName}} = $this->repository->update(${{entityName}}, $data);

            // Handle relationships
            if (isset($data['tags'])) {
                ${{entityName}}->tags()->sync($data['tags']);
            }

            // Dispatch event
            event(new {{EntityName}}Updated(${{entityName}}));

            // Clear cache
            $this->clearCache(${{entityName}});

            Log::info('{{EntityName}} updated', ['id' => ${{entityName}}->id]);

            return ${{entityName}}->fresh(['tags', 'category']);
        });
    }

    /**
     * Delete a {{entityName}}.
     *
     * @param {{EntityName}} ${{entityName}}
     * @return bool
     */
    public function delete({{EntityName}} ${{entityName}}): bool
    {
        return DB::transaction(function () use (${{entityName}}) {
            // Soft delete
            $deleted = $this->repository->delete(${{entityName}});

            if ($deleted) {
                // Dispatch event
                event(new {{EntityName}}Deleted(${{entityName}}));

                // Clear cache
                $this->clearCache(${{entityName}});

                Log::info('{{EntityName}} deleted', ['id' => ${{entityName}}->id]);
            }

            return $deleted;
        });
    }

    /**
     * Force delete a {{entityName}}.
     *
     * @param {{EntityName}} ${{entityName}}
     * @return bool
     */
    public function forceDelete({{EntityName}} ${{entityName}}): bool
    {
        return DB::transaction(function () use (${{entityName}}) {
            // Detach relationships
            ${{entityName}}->tags()->detach();

            // Force delete
            $deleted = ${{entityName}}->forceDelete();

            if ($deleted) {
                $this->clearCache(${{entityName}});
                Log::info('{{EntityName}} force deleted', ['id' => ${{entityName}}->id]);
            }

            return $deleted;
        });
    }

    /**
     * Restore a soft-deleted {{entityName}}.
     *
     * @param {{EntityName}} ${{entityName}}
     * @return bool
     */
    public function restore({{EntityName}} ${{entityName}}): bool
    {
        $restored = ${{entityName}}->restore();

        if ($restored) {
            $this->clearCache(${{entityName}});
            Log::info('{{EntityName}} restored', ['id' => ${{entityName}}->id]);
        }

        return $restored;
    }

    /**
     * Publish a {{entityName}}.
     *
     * @param {{EntityName}} ${{entityName}}
     * @return {{EntityName}}
     * @throws {{EntityName}}Exception
     */
    public function publish({{EntityName}} ${{entityName}}): {{EntityName}}
    {
        if (!${{entityName}}->canBePublished()) {
            throw new {{EntityName}}Exception('{{EntityName}} cannot be published');
        }

        return $this->update(${{entityName}}, [
            'status' => 'active',
            'published_at' => now(),
        ]);
    }

    /**
     * Archive a {{entityName}}.
     *
     * @param {{EntityName}} ${{entityName}}
     * @return {{EntityName}}
     */
    public function archive({{EntityName}} ${{entityName}}): {{EntityName}}
    {
        return $this->update(${{entityName}}, [
            'status' => 'archived',
        ]);
    }

    /**
     * Prepare data before saving.
     *
     * @param array $data
     * @return array
     */
    protected function prepareData(array $data): array
    {
        // Generate slug if not provided
        if (isset($data['name']) && empty($data['slug'])) {
            $data['slug'] = \Str::slug($data['name']);
        }

        return $data;
    }

    /**
     * Clear related caches.
     *
     * @param {{EntityName}}|null ${{entityName}}
     * @return void
     */
    protected function clearCache(?{{EntityName}} ${{entityName}} = null): void
    {
        if (${{entityName}}) {
            Cache::forget("{{entity_name}}:{${{entityName}}->id}");
        }

        Cache::tags(['{{entity_name}}s'])->flush();
    }
}
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{EntityName}}` | PascalCase entity name | `Product` |
| `{{entityName}}` | camelCase entity name | `product` |
| `{{entityNames}}` | camelCase plural | `products` |
| `{{entity_name}}` | snake_case entity name | `product` |
