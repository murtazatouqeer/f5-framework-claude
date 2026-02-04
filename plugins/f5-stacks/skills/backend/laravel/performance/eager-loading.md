---
name: laravel-eager-loading
description: Preventing N+1 queries with eager loading in Laravel
applies_to: laravel
category: performance
---

# Laravel Eager Loading

## Overview

Eager loading prevents the N+1 query problem by loading related models in a single query instead of separate queries for each parent model.

## The N+1 Problem

```php
<?php
// ❌ N+1 Problem: 1 query for books + N queries for authors
$books = Book::all();

foreach ($books as $book) {
    echo $book->author->name; // Executes a query for each book
}

// ✅ Eager Loading: 2 queries total
$books = Book::with('author')->get();

foreach ($books as $book) {
    echo $book->author->name; // No additional queries
}
```

## Basic Eager Loading

```php
<?php
// Single relationship
$posts = Post::with('author')->get();

// Multiple relationships
$posts = Post::with(['author', 'category', 'tags'])->get();

// Nested relationships
$posts = Post::with('author.profile')->get();

// Deep nesting
$posts = Post::with('author.profile.avatar')->get();

// Multiple nested
$posts = Post::with([
    'author.profile',
    'comments.user',
    'category',
])->get();
```

## Constraining Eager Loads

```php
<?php
// Filter related records
$posts = Post::with(['comments' => function ($query) {
    $query->where('approved', true)
          ->orderBy('created_at', 'desc');
}])->get();

// Select specific columns
$posts = Post::with(['author' => function ($query) {
    $query->select('id', 'name', 'email');
}])->get();

// Limit related records
$posts = Post::with(['comments' => function ($query) {
    $query->latest()->limit(5);
}])->get();

// Combined constraints
$posts = Post::with([
    'author:id,name',
    'comments' => function ($query) {
        $query->where('approved', true)
              ->with('user:id,name')
              ->latest()
              ->limit(10);
    },
    'category:id,name,slug',
])->get();
```

## Lazy Eager Loading

```php
<?php
// Load relationships after initial query
$posts = Post::all();

if ($someCondition) {
    $posts->load('comments');
}

// Load with constraints
$posts->load(['comments' => function ($query) {
    $query->where('approved', true);
}]);

// Load missing only (won't reload if already loaded)
$posts->loadMissing('author');
$posts->loadMissing(['author', 'category']);
```

## Eager Loading Counts

```php
<?php
// Load relationship count
$posts = Post::withCount('comments')->get();

foreach ($posts as $post) {
    echo $post->comments_count; // No additional query
}

// Multiple counts
$posts = Post::withCount(['comments', 'likes'])->get();

// Conditional count
$posts = Post::withCount([
    'comments',
    'comments as approved_comments_count' => function ($query) {
        $query->where('approved', true);
    },
])->get();

// Count with constraints
$users = User::withCount([
    'posts',
    'posts as published_posts_count' => fn ($q) => $q->published(),
    'posts as draft_posts_count' => fn ($q) => $q->draft(),
])->get();
```

## Eager Loading Aggregates

```php
<?php
// Sum
$posts = Post::withSum('comments', 'votes')->get();
echo $post->comments_sum_votes;

// Average
$categories = Category::withAvg('products', 'price')->get();
echo $category->products_avg_price;

// Min/Max
$authors = Author::withMin('books', 'published_at')
                 ->withMax('books', 'published_at')
                 ->get();

// Multiple aggregates
$users = User::query()
    ->withSum('orders', 'total')
    ->withAvg('orders', 'total')
    ->withCount('orders')
    ->get();
```

## Default Eager Loading

```php
<?php
// app/Models/Post.php
namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Post extends Model
{
    /**
     * Relationships to always eager load.
     */
    protected $with = ['author', 'category'];

    public function author()
    {
        return $this->belongsTo(User::class);
    }

    public function category()
    {
        return $this->belongsTo(Category::class);
    }
}

// Disable default eager loading
$posts = Post::without('author')->get();

// Override with different relationships
$posts = Post::without('category')->with('tags')->get();
```

## Preventing Lazy Loading (Development)

```php
<?php
// app/Providers/AppServiceProvider.php
use Illuminate\Database\Eloquent\Model;

public function boot(): void
{
    // Throw exception on lazy loading (development only)
    Model::preventLazyLoading(!app()->isProduction());

    // Or log instead of throwing
    Model::handleLazyLoadingViolationUsing(function ($model, $relation) {
        Log::warning("Lazy loading {$relation} on {$model}");
    });
}
```

## MorphTo Eager Loading

```php
<?php
// Polymorphic relationship eager loading
$activities = Activity::with('subject')->get();

// Constrain morphed types
$activities = Activity::with([
    'subject' => function (MorphTo $morphTo) {
        $morphTo->morphWith([
            Post::class => ['author'],
            Comment::class => ['post', 'user'],
        ]);
    },
])->get();

// Load specific morph types only
$activities = Activity::with([
    'subject' => function (MorphTo $morphTo) {
        $morphTo->constrain([
            Post::class => fn ($q) => $q->where('published', true),
            Comment::class => fn ($q) => $q->where('approved', true),
        ]);
    },
])->get();
```

## Query Optimization Patterns

### Repository Pattern with Eager Loading

```php
<?php
// app/Repositories/PostRepository.php
namespace App\Repositories;

use App\Models\Post;
use Illuminate\Database\Eloquent\Builder;
use Illuminate\Database\Eloquent\Collection;

class PostRepository
{
    /**
     * Base query with common eager loads.
     */
    protected function baseQuery(): Builder
    {
        return Post::query()
            ->with(['author:id,name', 'category:id,name,slug'])
            ->withCount('comments');
    }

    /**
     * Get published posts with full eager loading.
     */
    public function getPublished(): Collection
    {
        return $this->baseQuery()
            ->with(['tags', 'featuredImage'])
            ->published()
            ->latest()
            ->get();
    }

    /**
     * Get post with all details.
     */
    public function findWithDetails(string $id): ?Post
    {
        return Post::with([
            'author.profile',
            'category',
            'tags',
            'comments' => fn ($q) => $q->approved()->with('user:id,name')->latest(),
            'relatedPosts' => fn ($q) => $q->limit(5),
        ])
        ->withCount(['comments', 'likes'])
        ->find($id);
    }

    /**
     * Get posts for listing (minimal eager loading).
     */
    public function getForListing(int $perPage = 15)
    {
        return $this->baseQuery()
            ->published()
            ->latest()
            ->paginate($perPage);
    }
}
```

### Controller Usage

```php
<?php
// app/Http/Controllers/PostController.php
namespace App\Http\Controllers;

use App\Repositories\PostRepository;
use App\Http\Resources\PostResource;
use App\Http\Resources\PostDetailResource;

class PostController extends Controller
{
    public function __construct(
        protected PostRepository $posts
    ) {}

    public function index()
    {
        $posts = $this->posts->getForListing();

        return PostResource::collection($posts);
    }

    public function show(string $id)
    {
        $post = $this->posts->findWithDetails($id);

        if (!$post) {
            abort(404);
        }

        return new PostDetailResource($post);
    }
}
```

### Dynamic Eager Loading

```php
<?php
// app/Http/Controllers/Api/PostController.php
namespace App\Http\Controllers\Api;

use App\Models\Post;
use Illuminate\Http\Request;

class PostController extends Controller
{
    protected array $allowedIncludes = [
        'author',
        'category',
        'tags',
        'comments',
        'comments.user',
    ];

    public function index(Request $request)
    {
        $query = Post::query();

        // Parse ?include=author,tags,comments.user
        if ($request->has('include')) {
            $includes = explode(',', $request->input('include'));
            $includes = array_intersect($includes, $this->allowedIncludes);
            $query->with($includes);
        }

        return PostResource::collection($query->paginate());
    }
}
```

## Chunking with Eager Loading

```php
<?php
// Process large datasets efficiently
Post::with('author')->chunk(100, function ($posts) {
    foreach ($posts as $post) {
        // Process post
    }
});

// Cursor for memory efficiency
Post::with('author')->cursor()->each(function ($post) {
    // Process one at a time
});

// Lazy collection
Post::with('author')->lazy()->each(function ($post) {
    // Memory efficient iteration
});
```

## Testing Eager Loading

```php
<?php
use Illuminate\Database\Eloquent\Model;

class PostTest extends TestCase
{
    public function test_prevents_n_plus_one_queries(): void
    {
        // Create test data
        $posts = Post::factory()
            ->count(10)
            ->has(Comment::factory()->count(5))
            ->create();

        // Enable query logging
        DB::enableQueryLog();

        // Load with eager loading
        $loadedPosts = Post::with('comments')->get();

        foreach ($loadedPosts as $post) {
            $post->comments->count();
        }

        // Assert only 2 queries (posts + comments)
        $this->assertCount(2, DB::getQueryLog());
    }

    public function test_eager_loading_relationships_loaded(): void
    {
        $post = Post::factory()
            ->has(Comment::factory()->count(3))
            ->create();

        $loadedPost = Post::with('comments')->find($post->id);

        $this->assertTrue($loadedPost->relationLoaded('comments'));
        $this->assertCount(3, $loadedPost->comments);
    }

    public function test_prevents_lazy_loading_in_tests(): void
    {
        Model::preventLazyLoading();

        $post = Post::factory()->create();

        $this->expectException(LazyLoadingViolationException::class);

        $post->comments; // Should throw
    }
}
```

## Query Debugging

```php
<?php
// Log all queries
DB::listen(function ($query) {
    Log::info('Query', [
        'sql' => $query->sql,
        'bindings' => $query->bindings,
        'time' => $query->time,
    ]);
});

// Using Laravel Debugbar
// composer require barryvdh/laravel-debugbar --dev

// Using Telescope
// composer require laravel/telescope --dev

// Manual query count
$queryCount = 0;
DB::listen(function () use (&$queryCount) {
    $queryCount++;
});

$posts = Post::with('comments')->get();
foreach ($posts as $post) {
    $post->comments->count();
}

Log::info("Query count: {$queryCount}"); // Should be 2
```

## Best Practices

1. **Always Eager Load**: When iterating over related models
2. **Use withCount**: For counts without loading full relationships
3. **Constrain Eager Loads**: Only load needed columns and records
4. **Prevent Lazy Loading**: Enable in development to catch N+1
5. **Default Wisely**: Use `$with` for always-needed relationships
6. **Profile Queries**: Use Debugbar/Telescope to monitor
7. **Chunk Large Sets**: Use chunking for large data processing
8. **Document Relationships**: Clear docs for expected eager loads
