---
name: laravel-project-structure
description: Laravel project structure and organization best practices
applies_to: laravel
category: architecture
---

# Laravel Project Structure

## Overview

A well-organized Laravel project structure improves maintainability, testability, and team collaboration.

## Recommended Structure

```
app/
├── Console/
│   └── Commands/                   # Artisan commands
├── Exceptions/
│   └── Handler.php                 # Exception handling
├── Http/
│   ├── Controllers/
│   │   ├── Controller.php          # Base controller
│   │   └── Api/
│   │       └── V1/                 # API version 1
│   │           ├── AuthController.php
│   │           ├── UserController.php
│   │           └── ProductController.php
│   ├── Middleware/
│   │   ├── Authenticate.php
│   │   └── TrustHosts.php
│   ├── Requests/                   # Form requests by entity
│   │   ├── Auth/
│   │   │   ├── LoginRequest.php
│   │   │   └── RegisterRequest.php
│   │   └── Product/
│   │       ├── CreateProductRequest.php
│   │       └── UpdateProductRequest.php
│   └── Resources/                  # API resources
│       ├── UserResource.php
│       └── ProductResource.php
├── Models/
│   ├── User.php
│   ├── Product.php
│   └── Concerns/                   # Model traits
│       ├── HasUuid.php
│       └── HasSlug.php
├── Policies/                       # Authorization policies
│   ├── UserPolicy.php
│   └── ProductPolicy.php
├── Providers/
│   ├── AppServiceProvider.php
│   ├── AuthServiceProvider.php
│   └── RouteServiceProvider.php
├── Repositories/                   # Data access layer
│   ├── Contracts/
│   │   └── ProductRepositoryInterface.php
│   └── ProductRepository.php
├── Services/                       # Business logic layer
│   ├── Contracts/
│   │   └── ProductServiceInterface.php
│   └── ProductService.php
├── Rules/                          # Custom validation rules
│   └── ValidSlug.php
├── Enums/                          # PHP 8.1+ Enums
│   ├── UserRole.php
│   └── ProductStatus.php
├── Events/                         # Event classes
│   ├── ProductCreated.php
│   └── ProductUpdated.php
├── Listeners/                      # Event listeners
│   └── SendProductNotification.php
├── Jobs/                           # Queue jobs
│   └── ProcessProductImage.php
├── Mail/                           # Mailable classes
│   └── OrderConfirmation.php
├── Notifications/                  # Notification classes
│   └── ProductApproved.php
└── Observers/                      # Model observers
    └── ProductObserver.php

bootstrap/
├── app.php
└── cache/

config/
├── app.php
├── auth.php
├── database.php
├── sanctum.php
└── ...

database/
├── factories/
│   ├── UserFactory.php
│   └── ProductFactory.php
├── migrations/
│   ├── 2024_01_01_000000_create_users_table.php
│   └── 2024_01_01_000001_create_products_table.php
└── seeders/
    ├── DatabaseSeeder.php
    └── ProductSeeder.php

routes/
├── api.php                         # API routes
├── web.php                         # Web routes
├── console.php                     # Console routes
└── channels.php                    # Broadcast channels

storage/
├── app/
│   └── public/
├── framework/
│   ├── cache/
│   ├── sessions/
│   └── views/
└── logs/

tests/
├── Feature/
│   ├── AuthTest.php
│   └── ProductTest.php
├── Unit/
│   ├── ProductServiceTest.php
│   └── ProductTest.php
├── CreatesApplication.php
└── TestCase.php
```

## Layer Separation

### Controllers Layer (Thin)

Controllers should only handle HTTP concerns:
- Receive request
- Call service
- Return response

```php
<?php
// app/Http/Controllers/Api/V1/ProductController.php
namespace App\Http\Controllers\Api\V1;

use App\Http\Controllers\Controller;
use App\Http\Requests\Product\CreateProductRequest;
use App\Http\Resources\ProductResource;
use App\Services\Contracts\ProductServiceInterface;

class ProductController extends Controller
{
    public function __construct(
        protected ProductServiceInterface $productService
    ) {}

    public function store(CreateProductRequest $request): ProductResource
    {
        $product = $this->productService->create($request->validated());

        return ProductResource::make($product);
    }
}
```

### Service Layer (Business Logic)

Services contain business logic and orchestration:

```php
<?php
// app/Services/ProductService.php
namespace App\Services;

use App\Events\ProductCreated;
use App\Models\Product;
use App\Repositories\Contracts\ProductRepositoryInterface;
use App\Services\Contracts\ProductServiceInterface;
use Illuminate\Support\Facades\DB;

class ProductService implements ProductServiceInterface
{
    public function __construct(
        protected ProductRepositoryInterface $repository
    ) {}

    public function create(array $data): Product
    {
        return DB::transaction(function () use ($data) {
            $product = $this->repository->create($data);

            event(new ProductCreated($product));

            return $product;
        });
    }
}
```

### Repository Layer (Data Access)

Repositories abstract data access:

```php
<?php
// app/Repositories/ProductRepository.php
namespace App\Repositories;

use App\Models\Product;
use App\Repositories\Contracts\ProductRepositoryInterface;
use Illuminate\Pagination\LengthAwarePaginator;

class ProductRepository implements ProductRepositoryInterface
{
    public function __construct(
        protected Product $model
    ) {}

    public function create(array $data): Product
    {
        return $this->model->create($data);
    }

    public function paginate(int $perPage, array $filters): LengthAwarePaginator
    {
        return $this->model
            ->query()
            ->when(isset($filters['search']), fn ($q) =>
                $q->search($filters['search'])
            )
            ->when(isset($filters['status']), fn ($q) =>
                $q->where('status', $filters['status'])
            )
            ->latest()
            ->paginate($perPage);
    }
}
```

## Namespace Conventions

| Directory | Namespace |
|-----------|-----------|
| `app/` | `App\` |
| `app/Http/Controllers/` | `App\Http\Controllers\` |
| `app/Models/` | `App\Models\` |
| `app/Services/` | `App\Services\` |
| `app/Repositories/` | `App\Repositories\` |
| `tests/Feature/` | `Tests\Feature\` |
| `tests/Unit/` | `Tests\Unit\` |

## File Naming

| Type | Convention | Example |
|------|------------|---------|
| Model | Singular, PascalCase | `Product.php` |
| Controller | Singular + Controller | `ProductController.php` |
| Request | Action + Entity + Request | `CreateProductRequest.php` |
| Resource | Singular + Resource | `ProductResource.php` |
| Policy | Singular + Policy | `ProductPolicy.php` |
| Service | Singular + Service | `ProductService.php` |
| Repository | Singular + Repository | `ProductRepository.php` |
| Test | Entity + Test | `ProductTest.php` |
| Factory | Entity + Factory | `ProductFactory.php` |
| Migration | Verb + Table | `create_products_table.php` |

## Best Practices

### DO

1. **Group by Feature**: Keep related files together
2. **Use Contracts**: Define interfaces for services and repositories
3. **Leverage Service Container**: Let Laravel resolve dependencies
4. **Version APIs**: Use `/api/v1/` prefix for API routes
5. **Namespace Requests**: Group form requests by entity

### DON'T

1. **Fat Controllers**: Business logic belongs in services
2. **Fat Models**: Use repositories for complex queries
3. **Skip Interfaces**: Makes testing and swapping difficult
4. **Mix Concerns**: Each layer has a specific responsibility
5. **Hardcode Paths**: Use config and environment variables
