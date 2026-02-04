---
name: laravel-api-responses
description: Consistent API response patterns in Laravel
applies_to: laravel
category: error-handling
---

# Laravel API Responses

## Response Trait

```php
<?php
// app/Traits/ApiResponse.php
namespace App\Traits;

use Illuminate\Http\JsonResponse;
use Illuminate\Http\Resources\Json\JsonResource;
use Illuminate\Http\Resources\Json\ResourceCollection;
use Illuminate\Pagination\LengthAwarePaginator;

trait ApiResponse
{
    /**
     * Success response.
     */
    protected function success(
        mixed $data = null,
        string $message = 'Success',
        int $code = 200
    ): JsonResponse {
        $response = [
            'success' => true,
            'message' => $message,
        ];

        if ($data !== null) {
            $response['data'] = $data;
        }

        return response()->json($response, $code);
    }

    /**
     * Created response.
     */
    protected function created(
        mixed $data = null,
        string $message = 'Resource created successfully'
    ): JsonResponse {
        return $this->success($data, $message, 201);
    }

    /**
     * No content response.
     */
    protected function noContent(): JsonResponse
    {
        return response()->json(null, 204);
    }

    /**
     * Error response.
     */
    protected function error(
        string $message = 'An error occurred',
        int $code = 400,
        array $errors = []
    ): JsonResponse {
        $response = [
            'success' => false,
            'message' => $message,
        ];

        if (!empty($errors)) {
            $response['errors'] = $errors;
        }

        return response()->json($response, $code);
    }

    /**
     * Validation error response.
     */
    protected function validationError(array $errors): JsonResponse
    {
        return $this->error('Validation failed', 422, $errors);
    }

    /**
     * Not found response.
     */
    protected function notFound(string $message = 'Resource not found'): JsonResponse
    {
        return $this->error($message, 404);
    }

    /**
     * Unauthorized response.
     */
    protected function unauthorized(string $message = 'Unauthorized'): JsonResponse
    {
        return $this->error($message, 401);
    }

    /**
     * Forbidden response.
     */
    protected function forbidden(string $message = 'Forbidden'): JsonResponse
    {
        return $this->error($message, 403);
    }

    /**
     * Paginated response.
     */
    protected function paginated(
        LengthAwarePaginator|ResourceCollection $data,
        string $message = 'Success'
    ): JsonResponse {
        $pagination = $data instanceof ResourceCollection
            ? $data->resource
            : $data;

        return response()->json([
            'success' => true,
            'message' => $message,
            'data' => $data instanceof ResourceCollection ? $data : $data->items(),
            'meta' => [
                'current_page' => $pagination->currentPage(),
                'last_page' => $pagination->lastPage(),
                'per_page' => $pagination->perPage(),
                'total' => $pagination->total(),
                'from' => $pagination->firstItem(),
                'to' => $pagination->lastItem(),
            ],
            'links' => [
                'first' => $pagination->url(1),
                'last' => $pagination->url($pagination->lastPage()),
                'prev' => $pagination->previousPageUrl(),
                'next' => $pagination->nextPageUrl(),
            ],
        ]);
    }
}
```

## Response Class

```php
<?php
// app/Http/Responses/ApiResponse.php
namespace App\Http\Responses;

use Illuminate\Contracts\Support\Responsable;
use Illuminate\Http\JsonResponse;

class ApiResponse implements Responsable
{
    protected bool $success;
    protected string $message;
    protected mixed $data;
    protected int $statusCode;
    protected array $headers;
    protected array $meta;

    public function __construct(
        bool $success = true,
        string $message = 'Success',
        mixed $data = null,
        int $statusCode = 200,
        array $headers = [],
        array $meta = []
    ) {
        $this->success = $success;
        $this->message = $message;
        $this->data = $data;
        $this->statusCode = $statusCode;
        $this->headers = $headers;
        $this->meta = $meta;
    }

    /**
     * Create successful response.
     */
    public static function success(
        mixed $data = null,
        string $message = 'Success',
        int $statusCode = 200
    ): static {
        return new static(true, $message, $data, $statusCode);
    }

    /**
     * Create error response.
     */
    public static function error(
        string $message = 'An error occurred',
        int $statusCode = 400,
        mixed $data = null
    ): static {
        return new static(false, $message, $data, $statusCode);
    }

    /**
     * Add meta information.
     */
    public function withMeta(array $meta): static
    {
        $this->meta = array_merge($this->meta, $meta);
        return $this;
    }

    /**
     * Add headers.
     */
    public function withHeaders(array $headers): static
    {
        $this->headers = array_merge($this->headers, $headers);
        return $this;
    }

    /**
     * Create an HTTP response.
     */
    public function toResponse($request): JsonResponse
    {
        $response = [
            'success' => $this->success,
            'message' => $this->message,
        ];

        if ($this->data !== null) {
            $response['data'] = $this->data;
        }

        if (!empty($this->meta)) {
            $response['meta'] = $this->meta;
        }

        return response()
            ->json($response, $this->statusCode)
            ->withHeaders($this->headers);
    }
}
```

## Controller Usage

```php
<?php
// app/Http/Controllers/Api/ProductController.php
namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Http\Requests\Product\CreateProductRequest;
use App\Http\Requests\Product\UpdateProductRequest;
use App\Http\Resources\ProductResource;
use App\Http\Responses\ApiResponse;
use App\Models\Product;
use App\Services\ProductService;
use App\Traits\ApiResponse as ApiResponseTrait;

class ProductController extends Controller
{
    use ApiResponseTrait;

    public function __construct(
        protected ProductService $productService
    ) {}

    /**
     * List products with pagination.
     */
    public function index(): JsonResponse
    {
        $this->authorize('viewAny', Product::class);

        $products = $this->productService->paginate(
            perPage: request()->integer('per_page', 15),
            filters: request()->only(['search', 'status', 'category_id'])
        );

        return $this->paginated(
            ProductResource::collection($products),
            'Products retrieved successfully'
        );
    }

    /**
     * Get single product.
     */
    public function show(Product $product): JsonResponse
    {
        $this->authorize('view', $product);

        return $this->success(
            ProductResource::make($product->load(['category', 'tags'])),
            'Product retrieved successfully'
        );
    }

    /**
     * Create product.
     */
    public function store(CreateProductRequest $request): JsonResponse
    {
        $product = $this->productService->create($request->validated());

        return $this->created(
            ProductResource::make($product),
            'Product created successfully'
        );
    }

    /**
     * Update product.
     */
    public function update(UpdateProductRequest $request, Product $product): JsonResponse
    {
        $product = $this->productService->update($product, $request->validated());

        return $this->success(
            ProductResource::make($product),
            'Product updated successfully'
        );
    }

    /**
     * Delete product.
     */
    public function destroy(Product $product): JsonResponse
    {
        $this->authorize('delete', $product);

        $this->productService->delete($product);

        return $this->noContent();
    }

    /**
     * Using ApiResponse class.
     */
    public function activate(Product $product)
    {
        $this->authorize('update', $product);

        try {
            $product = $this->productService->activate($product);

            return ApiResponse::success(
                ProductResource::make($product),
                'Product activated successfully'
            )->withMeta(['activated_at' => now()->toISOString()]);

        } catch (\DomainException $e) {
            return ApiResponse::error($e->getMessage(), 422);
        }
    }
}
```

## Response Macros

```php
<?php
// app/Providers/AppServiceProvider.php
use Illuminate\Support\Facades\Response;

public function boot(): void
{
    Response::macro('success', function ($data = null, $message = 'Success', $code = 200) {
        return response()->json([
            'success' => true,
            'message' => $message,
            'data' => $data,
        ], $code);
    });

    Response::macro('error', function ($message = 'Error', $code = 400, $errors = []) {
        $response = [
            'success' => false,
            'message' => $message,
        ];

        if (!empty($errors)) {
            $response['errors'] = $errors;
        }

        return response()->json($response, $code);
    });

    Response::macro('created', function ($data = null, $message = 'Created') {
        return Response::success($data, $message, 201);
    });
}

// Usage in controller
return response()->success($product, 'Product created');
return response()->error('Not found', 404);
```

## Standard Response Formats

```json
// Success Response
{
  "success": true,
  "message": "Products retrieved successfully",
  "data": {
    "id": "uuid",
    "name": "Product Name",
    "price": "99.99"
  }
}

// Paginated Response
{
  "success": true,
  "message": "Products retrieved successfully",
  "data": [
    { "id": "uuid-1", "name": "Product 1" },
    { "id": "uuid-2", "name": "Product 2" }
  ],
  "meta": {
    "current_page": 1,
    "last_page": 10,
    "per_page": 15,
    "total": 150,
    "from": 1,
    "to": 15
  },
  "links": {
    "first": "http://api.example.com/products?page=1",
    "last": "http://api.example.com/products?page=10",
    "prev": null,
    "next": "http://api.example.com/products?page=2"
  }
}

// Error Response
{
  "success": false,
  "message": "Validation failed",
  "errors": {
    "name": ["The name field is required."],
    "price": ["The price must be a number."]
  }
}

// Not Found Response
{
  "success": false,
  "message": "Product not found"
}
```

## Testing API Responses

```php
<?php
class ProductApiTest extends TestCase
{
    public function test_success_response_structure(): void
    {
        $user = User::factory()->create();
        $product = Product::factory()->create();

        Sanctum::actingAs($user);

        $response = $this->getJson("/api/products/{$product->id}");

        $response
            ->assertOk()
            ->assertJsonStructure([
                'success',
                'message',
                'data' => ['id', 'name', 'price'],
            ])
            ->assertJson(['success' => true]);
    }

    public function test_paginated_response_structure(): void
    {
        $user = User::factory()->create();
        Product::factory()->count(20)->create();

        Sanctum::actingAs($user);

        $response = $this->getJson('/api/products?per_page=10');

        $response
            ->assertOk()
            ->assertJsonStructure([
                'success',
                'message',
                'data',
                'meta' => ['current_page', 'last_page', 'per_page', 'total'],
                'links' => ['first', 'last', 'prev', 'next'],
            ]);
    }

    public function test_error_response_structure(): void
    {
        Sanctum::actingAs(User::factory()->create());

        $response = $this->postJson('/api/products', []);

        $response
            ->assertUnprocessable()
            ->assertJsonStructure([
                'success',
                'message',
                'errors',
            ])
            ->assertJson(['success' => false]);
    }
}
```

## Best Practices

1. **Consistency**: Use same structure across all endpoints
2. **Clear Messages**: Provide meaningful messages
3. **Proper Status Codes**: Use correct HTTP status codes
4. **Include Meta**: Add pagination meta for lists
5. **Error Details**: Include validation errors in response
6. **Test Responses**: Verify response structure in tests
