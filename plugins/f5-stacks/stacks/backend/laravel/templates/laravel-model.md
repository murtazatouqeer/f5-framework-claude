---
name: laravel-model
description: Template for Laravel Eloquent Models
applies_to: laravel
type: template
---

# Laravel Model Template

## Eloquent Model

```php
<?php
// app/Models/{{EntityName}}.php
namespace App\Models;

use App\Enums\{{EntityName}}Status;
use App\Models\Concerns\HasUuid;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Database\Eloquent\Relations\BelongsToMany;
use Illuminate\Database\Eloquent\SoftDeletes;
use Illuminate\Database\Eloquent\Builder;

class {{EntityName}} extends Model
{
    use HasFactory, HasUuid, SoftDeletes;

    /**
     * The table associated with the model.
     */
    protected $table = '{{table_name}}';

    /**
     * The primary key type.
     */
    protected $keyType = 'string';

    /**
     * Indicates if the IDs are auto-incrementing.
     */
    public $incrementing = false;

    /**
     * The attributes that are mass assignable.
     */
    protected $fillable = [
        'name',
        'slug',
        'description',
        'status',
        'metadata',
        // Add fillable fields
    ];

    /**
     * The attributes that should be hidden for serialization.
     */
    protected $hidden = [
        // Add hidden fields
    ];

    /**
     * The attributes that should be cast.
     */
    protected function casts(): array
    {
        return [
            'status' => {{EntityName}}Status::class,
            'metadata' => 'array',
            'is_active' => 'boolean',
            'published_at' => 'datetime',
            'amount' => 'decimal:2',
        ];
    }

    /**
     * The model's default values for attributes.
     */
    protected $attributes = [
        'status' => 'draft',
        'metadata' => '{}',
    ];

    // ==========================================
    // RELATIONSHIPS
    // ==========================================

    /**
     * Get the user that owns the {{entityName}}.
     */
    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }

    /**
     * Get the category that the {{entityName}} belongs to.
     */
    public function category(): BelongsTo
    {
        return $this->belongsTo(Category::class);
    }

    /**
     * Get the items for the {{entityName}}.
     */
    public function items(): HasMany
    {
        return $this->hasMany({{EntityName}}Item::class);
    }

    /**
     * The tags that belong to the {{entityName}}.
     */
    public function tags(): BelongsToMany
    {
        return $this->belongsToMany(Tag::class)
            ->withTimestamps()
            ->withPivot('order');
    }

    // ==========================================
    // SCOPES
    // ==========================================

    /**
     * Scope a query to only include active records.
     */
    public function scopeActive(Builder $query): Builder
    {
        return $query->where('status', {{EntityName}}Status::ACTIVE);
    }

    /**
     * Scope a query to only include published records.
     */
    public function scopePublished(Builder $query): Builder
    {
        return $query->whereNotNull('published_at')
            ->where('published_at', '<=', now());
    }

    /**
     * Scope a query to search by name.
     */
    public function scopeSearch(Builder $query, ?string $search): Builder
    {
        if (empty($search)) {
            return $query;
        }

        return $query->where(function ($q) use ($search) {
            $q->where('name', 'like', "%{$search}%")
              ->orWhere('description', 'like', "%{$search}%");
        });
    }

    /**
     * Scope a query to filter by status.
     */
    public function scopeStatus(Builder $query, string|{{EntityName}}Status $status): Builder
    {
        return $query->where('status', $status);
    }

    // ==========================================
    // ACCESSORS & MUTATORS
    // ==========================================

    /**
     * Get the formatted price.
     */
    protected function formattedPrice(): Attribute
    {
        return Attribute::make(
            get: fn () => '$' . number_format($this->price, 2),
        );
    }

    /**
     * Determine if the {{entityName}} is published.
     */
    protected function isPublished(): Attribute
    {
        return Attribute::make(
            get: fn () => $this->published_at !== null && $this->published_at <= now(),
        );
    }

    // ==========================================
    // METHODS
    // ==========================================

    /**
     * Publish the {{entityName}}.
     */
    public function publish(): bool
    {
        return $this->update([
            'status' => {{EntityName}}Status::ACTIVE,
            'published_at' => now(),
        ]);
    }

    /**
     * Archive the {{entityName}}.
     */
    public function archive(): bool
    {
        return $this->update([
            'status' => {{EntityName}}Status::ARCHIVED,
        ]);
    }

    /**
     * Determine if the {{entityName}} can be edited.
     */
    public function canBeEdited(): bool
    {
        return $this->status !== {{EntityName}}Status::ARCHIVED;
    }
}
```

## HasUuid Trait

```php
<?php
// app/Models/Concerns/HasUuid.php
namespace App\Models\Concerns;

use Illuminate\Support\Str;

trait HasUuid
{
    protected static function bootHasUuid(): void
    {
        static::creating(function ($model) {
            if (empty($model->{$model->getKeyName()})) {
                $model->{$model->getKeyName()} = (string) Str::uuid();
            }
        });
    }
}
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{EntityName}}` | PascalCase entity name | `Product` |
| `{{entityName}}` | camelCase entity name | `product` |
| `{{table_name}}` | snake_case plural table name | `products` |
