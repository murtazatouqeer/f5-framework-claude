---
name: laravel-service-pattern
description: Service layer pattern in Laravel for business logic organization
applies_to: laravel
category: architecture
---

# Laravel Service Pattern

## Overview

The service layer contains business logic, keeping controllers thin and models focused on data representation.

## When to Use

- Complex business logic spanning multiple models
- Operations requiring transactions
- Event dispatching and side effects
- Logic that needs to be reused across controllers
- Logic that requires unit testing in isolation

## Structure

```
app/
├── Services/
│   ├── Contracts/
│   │   ├── UserServiceInterface.php
│   │   └── ProductServiceInterface.php
│   ├── UserService.php
│   └── ProductService.php
```

## Service Interface

```php
<?php
// app/Services/Contracts/ProductServiceInterface.php
namespace App\Services\Contracts;

use App\Models\Product;
use Illuminate\Pagination\LengthAwarePaginator;

interface ProductServiceInterface
{
    /**
     * Create a new product.
     */
    public function create(array $data): Product;

    /**
     * Update an existing product.
     */
    public function update(Product $product, array $data): Product;

    /**
     * Delete a product.
     */
    public function delete(Product $product): bool;

    /**
     * Find product by ID.
     */
    public function findById(string $id): ?Product;

    /**
     * Get paginated products.
     */
    public function paginate(int $perPage = 15, array $filters = []): LengthAwarePaginator;

    /**
     * Activate a product.
     */
    public function activate(Product $product): Product;

    /**
     * Deactivate a product.
     */
    public function deactivate(Product $product): Product;
}
```

## Service Implementation

```php
<?php
// app/Services/ProductService.php
namespace App\Services;

use App\Enums\ProductStatus;
use App\Events\ProductActivated;
use App\Events\ProductCreated;
use App\Events\ProductDeleted;
use App\Models\Product;
use App\Repositories\Contracts\ProductRepositoryInterface;
use App\Services\Contracts\ProductServiceInterface;
use Illuminate\Pagination\LengthAwarePaginator;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Str;

class ProductService implements ProductServiceInterface
{
    public function __construct(
        protected ProductRepositoryInterface $repository
    ) {}

    /**
     * Create a new product.
     */
    public function create(array $data): Product
    {
        return DB::transaction(function () use ($data) {
            // Generate slug if not provided
            if (empty($data['slug'])) {
                $data['slug'] = Str::slug($data['name']);
            }

            // Set default status
            if (empty($data['status'])) {
                $data['status'] = ProductStatus::Draft;
            }

            // Create the product
            $product = $this->repository->create($data);

            // Handle tags if provided
            if (!empty($data['tags'])) {
                $product->tags()->sync($data['tags']);
            }

            // Dispatch event
            event(new ProductCreated($product));

            return $product->load(['category', 'tags']);
        });
    }

    /**
     * Update an existing product.
     */
    public function update(Product $product, array $data): Product
    {
        return DB::transaction(function () use ($product, $data) {
            // Update slug if name changed
            if (isset($data['name']) && $data['name'] !== $product->name) {
                $data['slug'] = Str::slug($data['name']);
            }

            // Update the product
            $product = $this->repository->update($product, $data);

            // Sync tags if provided
            if (array_key_exists('tags', $data)) {
                $product->tags()->sync($data['tags'] ?? []);
            }

            return $product->fresh(['category', 'tags']);
        });
    }

    /**
     * Delete a product.
     */
    public function delete(Product $product): bool
    {
        return DB::transaction(function () use ($product) {
            // Detach relationships
            $product->tags()->detach();

            // Delete the product (soft delete)
            $result = $this->repository->delete($product);

            // Dispatch event
            event(new ProductDeleted($product));

            return $result;
        });
    }

    /**
     * Find product by ID.
     */
    public function findById(string $id): ?Product
    {
        return $this->repository->findById($id);
    }

    /**
     * Get paginated products.
     */
    public function paginate(int $perPage = 15, array $filters = []): LengthAwarePaginator
    {
        return $this->repository->paginate($perPage, $filters);
    }

    /**
     * Activate a product.
     *
     * @throws \DomainException
     */
    public function activate(Product $product): Product
    {
        // Business rule: only draft products can be activated
        if ($product->status !== ProductStatus::Draft) {
            throw new \DomainException('Only draft products can be activated.');
        }

        // Business rule: product must have a price
        if ($product->price <= 0) {
            throw new \DomainException('Product must have a valid price to be activated.');
        }

        return DB::transaction(function () use ($product) {
            $product = $this->repository->update($product, [
                'status' => ProductStatus::Active,
                'published_at' => now(),
            ]);

            event(new ProductActivated($product));

            return $product;
        });
    }

    /**
     * Deactivate a product.
     */
    public function deactivate(Product $product): Product
    {
        return $this->repository->update($product, [
            'status' => ProductStatus::Archived,
        ]);
    }

    /**
     * Bulk create products.
     */
    public function bulkCreate(array $items): array
    {
        return DB::transaction(function () use ($items) {
            $products = [];

            foreach ($items as $data) {
                $products[] = $this->create($data);
            }

            return $products;
        });
    }

    /**
     * Bulk delete products.
     */
    public function bulkDelete(array $ids): int
    {
        return DB::transaction(function () use ($ids) {
            $count = 0;

            foreach ($ids as $id) {
                $product = $this->repository->findById($id);
                if ($product && $this->delete($product)) {
                    $count++;
                }
            }

            return $count;
        });
    }

    /**
     * Export products to CSV.
     */
    public function exportToCsv(array $filters = []): \Symfony\Component\HttpFoundation\StreamedResponse
    {
        $products = $this->repository->all($filters);

        $headers = [
            'Content-Type' => 'text/csv',
            'Content-Disposition' => 'attachment; filename="products.csv"',
        ];

        return response()->stream(function () use ($products) {
            $handle = fopen('php://output', 'w');

            // Header row
            fputcsv($handle, ['ID', 'Name', 'Price', 'Status', 'Created At']);

            // Data rows
            foreach ($products as $product) {
                fputcsv($handle, [
                    $product->id,
                    $product->name,
                    $product->price,
                    $product->status->value,
                    $product->created_at->toISOString(),
                ]);
            }

            fclose($handle);
        }, 200, $headers);
    }
}
```

## Controller Usage

```php
<?php
// app/Http/Controllers/Api/V1/ProductController.php
namespace App\Http\Controllers\Api\V1;

use App\Http\Controllers\Controller;
use App\Http\Requests\Product\CreateProductRequest;
use App\Http\Requests\Product\UpdateProductRequest;
use App\Http\Resources\ProductResource;
use App\Models\Product;
use App\Services\Contracts\ProductServiceInterface;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\AnonymousResourceCollection;

class ProductController extends Controller
{
    public function __construct(
        protected ProductServiceInterface $productService
    ) {}

    public function index(Request $request): AnonymousResourceCollection
    {
        $this->authorize('viewAny', Product::class);

        $products = $this->productService->paginate(
            perPage: $request->integer('per_page', 15),
            filters: $request->only(['search', 'status', 'category_id'])
        );

        return ProductResource::collection($products);
    }

    public function store(CreateProductRequest $request): JsonResponse
    {
        $product = $this->productService->create($request->validated());

        return ProductResource::make($product)
            ->response()
            ->setStatusCode(201);
    }

    public function show(Product $product): ProductResource
    {
        $this->authorize('view', $product);

        return ProductResource::make($product->load(['category', 'tags']));
    }

    public function update(UpdateProductRequest $request, Product $product): ProductResource
    {
        $product = $this->productService->update($product, $request->validated());

        return ProductResource::make($product);
    }

    public function destroy(Product $product): JsonResponse
    {
        $this->authorize('delete', $product);

        $this->productService->delete($product);

        return response()->json(null, 204);
    }

    public function activate(Product $product): ProductResource
    {
        $this->authorize('update', $product);

        $product = $this->productService->activate($product);

        return ProductResource::make($product);
    }
}
```

## Service Provider Registration

```php
<?php
// app/Providers/AppServiceProvider.php
namespace App\Providers;

use App\Repositories\Contracts\ProductRepositoryInterface;
use App\Repositories\ProductRepository;
use App\Services\Contracts\ProductServiceInterface;
use App\Services\ProductService;
use Illuminate\Support\ServiceProvider;

class AppServiceProvider extends ServiceProvider
{
    /**
     * All of the container bindings that should be registered.
     *
     * @var array
     */
    public $bindings = [
        ProductServiceInterface::class => ProductService::class,
        ProductRepositoryInterface::class => ProductRepository::class,
    ];

    public function register(): void
    {
        // Alternative: individual bindings
        // $this->app->bind(ProductServiceInterface::class, ProductService::class);
    }
}
```

## Testing Services

```php
<?php
// tests/Unit/ProductServiceTest.php
namespace Tests\Unit;

use App\Enums\ProductStatus;
use App\Models\Product;
use App\Repositories\Contracts\ProductRepositoryInterface;
use App\Services\ProductService;
use Mockery;
use Tests\TestCase;

class ProductServiceTest extends TestCase
{
    protected ProductService $service;
    protected $mockRepository;

    protected function setUp(): void
    {
        parent::setUp();

        $this->mockRepository = Mockery::mock(ProductRepositoryInterface::class);
        $this->service = new ProductService($this->mockRepository);
    }

    public function test_activate_throws_exception_for_non_draft_product(): void
    {
        $product = Product::factory()->make([
            'status' => ProductStatus::Active,
        ]);

        $this->expectException(\DomainException::class);
        $this->expectExceptionMessage('Only draft products can be activated.');

        $this->service->activate($product);
    }

    public function test_activate_throws_exception_for_zero_price(): void
    {
        $product = Product::factory()->make([
            'status' => ProductStatus::Draft,
            'price' => 0,
        ]);

        $this->expectException(\DomainException::class);
        $this->expectExceptionMessage('Product must have a valid price');

        $this->service->activate($product);
    }
}
```

## Best Practices

1. **Single Responsibility**: One service per domain concept
2. **Interface-Driven**: Define contracts for flexibility
3. **Transaction Boundaries**: Wrap multi-step operations in transactions
4. **Event Dispatching**: Services are the right place for events
5. **Domain Exceptions**: Throw domain-specific exceptions for business rule violations
6. **Dependency Injection**: Inject repositories and other services via constructor
