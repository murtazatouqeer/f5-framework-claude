---
name: laravel-relationships
description: Eloquent relationship patterns and best practices
applies_to: laravel
category: database
---

# Laravel Eloquent Relationships

## One-to-One

```php
<?php
// User has one Profile
class User extends Model
{
    public function profile(): HasOne
    {
        return $this->hasOne(Profile::class);
    }
}

class Profile extends Model
{
    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }
}

// Usage
$user->profile; // Get profile
$user->profile()->create(['bio' => 'Hello']); // Create profile
```

## One-to-Many

```php
<?php
// Category has many Products
class Category extends Model
{
    public function products(): HasMany
    {
        return $this->hasMany(Product::class);
    }
}

class Product extends Model
{
    public function category(): BelongsTo
    {
        return $this->belongsTo(Category::class);
    }
}

// Usage
$category->products; // Get all products
$category->products()->create(['name' => 'New Product']); // Create product
$product->category; // Get category
$product->category()->associate($category); // Change category
```

## Many-to-Many

```php
<?php
// Product has many Tags, Tag has many Products
class Product extends Model
{
    public function tags(): BelongsToMany
    {
        return $this->belongsToMany(Tag::class)
            ->withTimestamps()
            ->withPivot(['sort_order', 'is_primary']);
    }
}

class Tag extends Model
{
    public function products(): BelongsToMany
    {
        return $this->belongsToMany(Product::class)
            ->withTimestamps();
    }
}

// Usage
$product->tags; // Get all tags
$product->tags()->attach($tagId); // Add tag
$product->tags()->detach($tagId); // Remove tag
$product->tags()->sync([1, 2, 3]); // Replace all
$product->tags()->syncWithoutDetaching([4, 5]); // Add without removing
$product->tags()->attach($tagId, ['is_primary' => true]); // With pivot data
```

## Has Many Through

```php
<?php
// Country -> Users -> Posts (Country has many posts through users)
class Country extends Model
{
    public function posts(): HasManyThrough
    {
        return $this->hasManyThrough(
            Post::class,     // Final model
            User::class,     // Intermediate model
            'country_id',    // Foreign key on users table
            'user_id',       // Foreign key on posts table
            'id',            // Local key on countries table
            'id'             // Local key on users table
        );
    }
}

// Usage
$country->posts; // All posts from users in this country
```

## Has One Through

```php
<?php
// Supplier -> User -> History
class Supplier extends Model
{
    public function userHistory(): HasOneThrough
    {
        return $this->hasOneThrough(
            History::class,
            User::class,
            'supplier_id', // Foreign key on users table
            'user_id',     // Foreign key on history table
            'id',          // Local key on suppliers table
            'id'           // Local key on users table
        );
    }
}
```

## Polymorphic Relationships

### One-to-Many Polymorphic

```php
<?php
// Comments can belong to Posts, Videos, or Products
class Comment extends Model
{
    public function commentable(): MorphTo
    {
        return $this->morphTo();
    }
}

class Post extends Model
{
    public function comments(): MorphMany
    {
        return $this->morphMany(Comment::class, 'commentable');
    }
}

class Video extends Model
{
    public function comments(): MorphMany
    {
        return $this->morphMany(Comment::class, 'commentable');
    }
}

// Migration
Schema::create('comments', function (Blueprint $table) {
    $table->id();
    $table->text('body');
    $table->uuidMorphs('commentable'); // commentable_type, commentable_id
    $table->timestamps();
});

// Usage
$post->comments; // Get comments
$comment->commentable; // Get parent (Post or Video)
```

### Many-to-Many Polymorphic

```php
<?php
// Tags can be applied to Posts, Videos, Products
class Tag extends Model
{
    public function posts(): MorphToMany
    {
        return $this->morphedByMany(Post::class, 'taggable');
    }

    public function videos(): MorphToMany
    {
        return $this->morphedByMany(Video::class, 'taggable');
    }
}

class Post extends Model
{
    public function tags(): MorphToMany
    {
        return $this->morphToMany(Tag::class, 'taggable');
    }
}

// Migration (pivot table: taggables)
Schema::create('taggables', function (Blueprint $table) {
    $table->foreignId('tag_id');
    $table->uuidMorphs('taggable');
    $table->timestamps();
});
```

## Custom Pivot Models

```php
<?php
// app/Models/OrderItem.php
namespace App\Models;

use Illuminate\Database\Eloquent\Relations\Pivot;

class OrderItem extends Pivot
{
    protected $table = 'order_items';

    protected $casts = [
        'price' => 'decimal:2',
        'quantity' => 'integer',
    ];

    public function getSubtotalAttribute(): float
    {
        return $this->price * $this->quantity;
    }
}

// In Order model
class Order extends Model
{
    public function products(): BelongsToMany
    {
        return $this->belongsToMany(Product::class, 'order_items')
            ->using(OrderItem::class)
            ->withPivot(['quantity', 'price'])
            ->withTimestamps();
    }
}

// Usage
$order->products->each(function ($product) {
    echo $product->pivot->subtotal;
});
```

## Eager Loading

```php
<?php
// Prevent N+1 queries
$products = Product::with(['category', 'tags', 'user'])->get();

// Nested eager loading
$products = Product::with([
    'category.parent',
    'tags',
    'user.profile',
])->get();

// Constrained eager loading
$products = Product::with([
    'comments' => function ($query) {
        $query->where('approved', true)
              ->orderBy('created_at', 'desc')
              ->limit(10);
    }
])->get();

// Count relations
$products = Product::withCount('comments')->get();
$products->first()->comments_count;

// Conditional count
$products = Product::withCount([
    'comments',
    'comments as approved_comments_count' => function ($query) {
        $query->where('approved', true);
    }
])->get();

// Aggregates
$products = Product::withAvg('reviews', 'rating')
    ->withSum('orders', 'quantity')
    ->get();
```

## Default Models

```php
<?php
class Post extends Model
{
    public function author(): BelongsTo
    {
        return $this->belongsTo(User::class, 'user_id')
            ->withDefault([
                'name' => 'Anonymous',
            ]);
    }
}

// No null checks needed
$post->author->name; // Returns 'Anonymous' if no author
```

## Relationship Existence Queries

```php
<?php
// Products that have at least one comment
Product::has('comments')->get();

// Products with at least 5 comments
Product::has('comments', '>=', 5)->get();

// Products with approved comments
Product::whereHas('comments', function ($query) {
    $query->where('approved', true);
})->get();

// Products without comments
Product::doesntHave('comments')->get();

// Products where category name is 'Electronics'
Product::whereRelation('category', 'name', 'Electronics')->get();
```

## Relationship Ordering

```php
<?php
class User extends Model
{
    // Latest post first
    public function posts(): HasMany
    {
        return $this->hasMany(Post::class)->latest();
    }

    // Order by custom column
    public function orderedImages(): HasMany
    {
        return $this->hasMany(Image::class)->orderBy('sort_order');
    }
}
```

## Self-Referential Relationships

```php
<?php
class Category extends Model
{
    public function parent(): BelongsTo
    {
        return $this->belongsTo(Category::class, 'parent_id');
    }

    public function children(): HasMany
    {
        return $this->hasMany(Category::class, 'parent_id');
    }

    // Recursive children (all descendants)
    public function descendants(): HasMany
    {
        return $this->children()->with('descendants');
    }

    // Recursive parents (all ancestors)
    public function ancestors(): BelongsTo
    {
        return $this->parent()->with('ancestors');
    }
}
```

## Best Practices

1. **Define Inverse Relationships**: Always define both sides
2. **Use Eager Loading**: Prevent N+1 queries with `with()`
3. **Constrain Queries**: Filter early with `whereHas()`
4. **Custom Pivots**: For pivot tables with extra logic
5. **Default Models**: Avoid null checks with `withDefault()`
6. **Use Relationship Methods**: `$post->comments()` for queries, `$post->comments` for results
