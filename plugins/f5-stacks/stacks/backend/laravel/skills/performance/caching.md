---
name: laravel-caching
description: Caching strategies and patterns in Laravel
applies_to: laravel
category: performance
---

# Laravel Caching

## Overview

Laravel provides a unified API for various caching backends including Redis, Memcached, file, and database.

## Basic Cache Operations

```php
<?php
use Illuminate\Support\Facades\Cache;

// Store value
Cache::put('key', 'value', now()->addMinutes(10));

// Store forever
Cache::forever('key', 'value');

// Retrieve value
$value = Cache::get('key');
$value = Cache::get('key', 'default');

// Check existence
if (Cache::has('key')) {
    // Key exists
}

// Retrieve and delete
$value = Cache::pull('key');

// Delete
Cache::forget('key');

// Clear all
Cache::flush();
```

## Remember Pattern

```php
<?php
// Remember for duration
$users = Cache::remember('users', now()->addHours(1), function () {
    return User::all();
});

// Remember forever
$settings = Cache::rememberForever('settings', function () {
    return Setting::all()->pluck('value', 'key');
});

// Remember with tags
$products = Cache::tags(['products', 'catalog'])->remember(
    'featured-products',
    now()->addHours(1),
    fn () => Product::featured()->get()
);
```

## Cache Keys Strategy

```php
<?php
// app/Services/CacheKeyService.php
namespace App\Services;

class CacheKeyService
{
    public static function user(int|string $id): string
    {
        return "user:{$id}";
    }

    public static function userProducts(int|string $userId): string
    {
        return "user:{$userId}:products";
    }

    public static function product(int|string $id): string
    {
        return "product:{$id}";
    }

    public static function productsByCategory(int|string $categoryId): string
    {
        return "category:{$categoryId}:products";
    }

    public static function searchResults(string $query, array $filters = []): string
    {
        $filterHash = md5(serialize($filters));
        return "search:" . md5($query) . ":{$filterHash}";
    }
}

// Usage
$cacheKey = CacheKeyService::product($product->id);
```

## Service Layer Caching

```php
<?php
// app/Services/ProductService.php
namespace App\Services;

use App\Models\Product;
use Illuminate\Support\Facades\Cache;
use Illuminate\Database\Eloquent\Collection;

class ProductService
{
    private const CACHE_TTL = 3600; // 1 hour

    public function find(string $id): ?Product
    {
        return Cache::remember(
            "product:{$id}",
            self::CACHE_TTL,
            fn () => Product::with(['category', 'tags'])->find($id)
        );
    }

    public function getFeatured(): Collection
    {
        return Cache::tags(['products', 'featured'])->remember(
            'products:featured',
            self::CACHE_TTL,
            fn () => Product::featured()->with('category')->limit(10)->get()
        );
    }

    public function getByCategory(string $categoryId): Collection
    {
        return Cache::tags(['products', "category:{$categoryId}"])->remember(
            "category:{$categoryId}:products",
            self::CACHE_TTL,
            fn () => Product::where('category_id', $categoryId)->get()
        );
    }

    public function clearProductCache(Product $product): void
    {
        Cache::forget("product:{$product->id}");
        Cache::tags(['products'])->flush();
        Cache::tags(["category:{$product->category_id}"])->flush();
    }

    public function update(Product $product, array $data): Product
    {
        $product->update($data);

        // Clear related caches
        $this->clearProductCache($product);

        return $product->fresh();
    }
}
```

## Model Caching with Events

```php
<?php
// app/Models/Product.php
namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Support\Facades\Cache;

class Product extends Model
{
    protected static function booted(): void
    {
        static::saved(function (Product $product) {
            Cache::forget("product:{$product->id}");
            Cache::tags(['products'])->flush();
        });

        static::deleted(function (Product $product) {
            Cache::forget("product:{$product->id}");
            Cache::tags(['products'])->flush();
        });
    }

    public static function findCached(string $id): ?static
    {
        return Cache::remember(
            "product:{$id}",
            3600,
            fn () => static::find($id)
        );
    }
}
```

## Cache Observer Pattern

```php
<?php
// app/Observers/ProductObserver.php
namespace App\Observers;

use App\Models\Product;
use Illuminate\Support\Facades\Cache;

class ProductObserver
{
    public function saved(Product $product): void
    {
        $this->clearCache($product);
    }

    public function deleted(Product $product): void
    {
        $this->clearCache($product);
    }

    protected function clearCache(Product $product): void
    {
        Cache::forget("product:{$product->id}");
        Cache::forget("category:{$product->category_id}:products");

        if ($product->is_featured) {
            Cache::tags(['featured'])->flush();
        }

        // Clear list caches
        Cache::tags(['products'])->flush();
    }
}

// Register in AppServiceProvider
Product::observe(ProductObserver::class);
```

## Query Result Caching

```php
<?php
// app/Repositories/ProductRepository.php
namespace App\Repositories;

use App\Models\Product;
use Illuminate\Contracts\Pagination\LengthAwarePaginator;
use Illuminate\Support\Facades\Cache;

class ProductRepository
{
    public function paginate(array $filters = [], int $perPage = 15): LengthAwarePaginator
    {
        $cacheKey = $this->buildCacheKey('products:list', $filters, $perPage);

        return Cache::remember($cacheKey, 600, function () use ($filters, $perPage) {
            $query = Product::query();

            if (!empty($filters['category_id'])) {
                $query->where('category_id', $filters['category_id']);
            }

            if (!empty($filters['search'])) {
                $query->where('name', 'like', "%{$filters['search']}%");
            }

            return $query->paginate($perPage);
        });
    }

    protected function buildCacheKey(string $prefix, array $filters, int $perPage): string
    {
        $page = request()->get('page', 1);
        $filterHash = md5(serialize($filters));

        return "{$prefix}:{$filterHash}:page:{$page}:per:{$perPage}";
    }
}
```

## HTTP Response Caching

```php
<?php
// app/Http/Controllers/Api/ProductController.php
namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Http\Resources\ProductResource;
use App\Models\Product;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Cache;

class ProductController extends Controller
{
    public function index(Request $request)
    {
        $cacheKey = 'api:products:' . md5($request->fullUrl());

        $response = Cache::remember($cacheKey, 300, function () {
            $products = Product::paginate(15);
            return ProductResource::collection($products)->response()->getData(true);
        });

        return response()->json($response);
    }

    public function show(Product $product)
    {
        $etag = md5($product->updated_at->timestamp);

        return response()
            ->json(ProductResource::make($product))
            ->header('ETag', $etag)
            ->header('Cache-Control', 'private, max-age=300');
    }
}
```

## Cache Middleware

```php
<?php
// app/Http/Middleware/CacheResponse.php
namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Cache;
use Symfony\Component\HttpFoundation\Response;

class CacheResponse
{
    public function handle(Request $request, Closure $next, int $minutes = 5): Response
    {
        if ($request->method() !== 'GET') {
            return $next($request);
        }

        $cacheKey = 'response:' . md5($request->fullUrl());

        if (Cache::has($cacheKey)) {
            $cached = Cache::get($cacheKey);
            return response($cached['content'])
                ->withHeaders($cached['headers'])
                ->header('X-Cache', 'HIT');
        }

        $response = $next($request);

        if ($response->isSuccessful()) {
            Cache::put($cacheKey, [
                'content' => $response->getContent(),
                'headers' => $response->headers->all(),
            ], now()->addMinutes($minutes));
        }

        return $response->header('X-Cache', 'MISS');
    }
}

// routes/api.php
Route::middleware('cache.response:10')->group(function () {
    Route::get('/products', [ProductController::class, 'index']);
});
```

## Redis-Specific Features

```php
<?php
use Illuminate\Support\Facades\Redis;

// Atomic operations
Redis::incr('visits');
Redis::incrby('counter', 5);
Redis::decr('stock');

// Hash operations
Redis::hset('user:1', 'name', 'John');
Redis::hget('user:1', 'name');
Redis::hgetall('user:1');

// Sets
Redis::sadd('online_users', $userId);
Redis::srem('online_users', $userId);
Redis::smembers('online_users');

// Sorted sets (leaderboards)
Redis::zadd('leaderboard', $score, $userId);
Redis::zrevrange('leaderboard', 0, 9, 'WITHSCORES');

// Pub/Sub
Redis::publish('notifications', json_encode($data));

// Pipelines for batch operations
Redis::pipeline(function ($pipe) {
    for ($i = 0; $i < 1000; $i++) {
        $pipe->set("key:$i", $i);
    }
});
```

## Cache Locking

```php
<?php
use Illuminate\Support\Facades\Cache;

// Atomic lock
$lock = Cache::lock('processing:order:123', 10);

if ($lock->get()) {
    try {
        // Process exclusively
        $this->processOrder($order);
    } finally {
        $lock->release();
    }
}

// Block until lock available
$lock = Cache::lock('processing:order:123', 10);

$lock->block(5, function () use ($order) {
    // Got the lock, process order
    $this->processOrder($order);
});

// In jobs
public function handle(): void
{
    $lock = Cache::lock('import:products', 300);

    if (!$lock->get()) {
        $this->release(60); // Retry in 60 seconds
        return;
    }

    try {
        $this->importProducts();
    } finally {
        $lock->release();
    }
}
```

## Rate Limiting with Cache

```php
<?php
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\RateLimiter;

// Using RateLimiter (Laravel built-in)
$executed = RateLimiter::attempt(
    'api:' . $request->ip(),
    $perMinute = 60,
    function() {
        // Perform action
    }
);

if (!$executed) {
    return response()->json(['message' => 'Too many requests'], 429);
}

// Custom sliding window
public function checkRateLimit(string $key, int $maxAttempts, int $decaySeconds): bool
{
    $attempts = Cache::get($key, 0);

    if ($attempts >= $maxAttempts) {
        return false;
    }

    Cache::put($key, $attempts + 1, $decaySeconds);
    return true;
}
```

## Testing Cache

```php
<?php
use Illuminate\Support\Facades\Cache;

class ProductServiceTest extends TestCase
{
    public function test_caches_product(): void
    {
        Cache::shouldReceive('remember')
            ->once()
            ->with('product:123', Mockery::any(), Mockery::type('Closure'))
            ->andReturn(Product::factory()->make(['id' => '123']));

        $product = $this->service->find('123');

        $this->assertEquals('123', $product->id);
    }

    public function test_clears_cache_on_update(): void
    {
        Cache::shouldReceive('forget')
            ->once()
            ->with('product:123');

        Cache::shouldReceive('tags')
            ->andReturnSelf();

        Cache::shouldReceive('flush')->once();

        $this->service->update($product, ['name' => 'Updated']);
    }
}
```

## Best Practices

1. **Use Tags**: Group related cache entries for bulk invalidation
2. **Set TTL**: Always set expiration to prevent stale data
3. **Key Naming**: Use consistent, descriptive key patterns
4. **Invalidation Strategy**: Clear cache on model changes
5. **Lock Critical Sections**: Use cache locks for concurrency
6. **Monitor Cache**: Track hit/miss rates and memory usage
7. **Serialize Carefully**: Be mindful of what you cache (avoid closures)
