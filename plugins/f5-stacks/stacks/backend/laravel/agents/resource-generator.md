---
name: laravel-resource-generator
description: Agent for generating Laravel API Resources for JSON transformation
applies_to: laravel
category: agent
---

# Laravel Resource Generator Agent

## Purpose

Generate production-ready Laravel API Resources for consistent JSON API responses with proper data transformation.

## Input Requirements

```yaml
required:
  - entity_name: string          # e.g., "Product"

optional:
  - fields: array                # Fields to include
  - relationships: array         # Related resources to include
  - conditional_fields: array    # Fields shown conditionally
  - collection: boolean          # Generate collection resource (default: false)
  - with_meta: boolean           # Include meta information (default: true)
```

## Generation Process

### Step 1: Analyze Model

```php
// Get model structure
$model = app("App\\Models\\{$entityName}");
$fillable = $model->getFillable();
$casts = $model->getCasts();
$appends = $model->getAppends();
$relationships = getModelRelationships($model);
```

### Step 2: Generate Resource

```php
<?php
// app/Http/Resources/{{Entity}}Resource.php
namespace App\Http\Resources;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

class {{Entity}}Resource extends JsonResource
{
    /**
     * The "data" wrapper that should be applied.
     *
     * @var string|null
     */
    public static $wrap = 'data';

    /**
     * Transform the resource into an array.
     *
     * @param Request $request
     * @return array<string, mixed>
     */
    public function toArray(Request $request): array
    {
        return [
            // Primary Key
            'id' => $this->id,

            // Basic Fields
            'name' => $this->name,
            'slug' => $this->slug,
            'description' => $this->description,

            // Numeric Fields
            'price' => $this->price,
            'compare_price' => $this->compare_price,

            // Computed Fields (from accessors)
            'is_on_sale' => $this->is_on_sale,
            'discount_percentage' => $this->discount_percentage,

            // Status
            'status' => $this->status?->value,
            'status_label' => $this->status?->label(),

            // Boolean Fields
            'is_featured' => $this->is_featured,

            // Relationships (whenLoaded)
            'category' => CategoryResource::make($this->whenLoaded('category')),
            'tags' => TagResource::collection($this->whenLoaded('tags')),
            'images' => {{Entity}}ImageResource::collection($this->whenLoaded('images')),
            'user' => UserResource::make($this->whenLoaded('user')),

            // Conditional Fields (based on user permission)
            'metadata' => $this->when(
                $request->user()?->can('viewMetadata', $this->resource),
                $this->metadata
            ),

            // Admin-only fields
            'internal_notes' => $this->when(
                $request->user()?->isAdmin(),
                $this->internal_notes
            ),

            // Counts (when loaded)
            'orders_count' => $this->when(
                $this->orders_count !== null,
                $this->orders_count
            ),
            'reviews_count' => $this->when(
                $this->reviews_count !== null,
                $this->reviews_count
            ),

            // Aggregates (when loaded)
            'average_rating' => $this->when(
                $this->average_rating !== null,
                fn () => round($this->average_rating, 1)
            ),

            // Pivot data (for many-to-many)
            'pivot' => $this->whenPivotLoaded('{{entity}}_tag', function () {
                return [
                    'sort_order' => $this->pivot->sort_order,
                ];
            }),

            // Timestamps
            'published_at' => $this->published_at?->toISOString(),
            'created_at' => $this->created_at->toISOString(),
            'updated_at' => $this->updated_at->toISOString(),
        ];
    }

    /**
     * Get additional data that should be returned with the resource array.
     *
     * @param Request $request
     * @return array<string, mixed>
     */
    public function with(Request $request): array
    {
        return [
            'meta' => [
                'api_version' => 'v1',
            ],
        ];
    }

    /**
     * Customize the outgoing response for the resource.
     *
     * @param Request $request
     * @param \Illuminate\Http\JsonResponse $response
     * @return void
     */
    public function withResponse(Request $request, $response): void
    {
        $response->header('X-Resource-Type', '{{Entity}}');
    }
}
```

### Step 3: Generate Collection Resource

```php
<?php
// app/Http/Resources/{{Entity}}Collection.php
namespace App\Http\Resources;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\ResourceCollection;

class {{Entity}}Collection extends ResourceCollection
{
    /**
     * The resource that this resource collects.
     *
     * @var string
     */
    public $collects = {{Entity}}Resource::class;

    /**
     * Transform the resource collection into an array.
     *
     * @param Request $request
     * @return array<string, mixed>
     */
    public function toArray(Request $request): array
    {
        return [
            'data' => $this->collection,
        ];
    }

    /**
     * Get additional data that should be returned with the resource array.
     *
     * @param Request $request
     * @return array<string, mixed>
     */
    public function with(Request $request): array
    {
        return [
            'meta' => [
                'total' => $this->total(),
                'per_page' => $this->perPage(),
                'current_page' => $this->currentPage(),
                'last_page' => $this->lastPage(),
                'from' => $this->firstItem(),
                'to' => $this->lastItem(),
            ],
            'links' => [
                'first' => $this->url(1),
                'last' => $this->url($this->lastPage()),
                'prev' => $this->previousPageUrl(),
                'next' => $this->nextPageUrl(),
            ],
        ];
    }
}
```

### Step 4: Generate Summary Resource (Lightweight)

```php
<?php
// app/Http/Resources/{{Entity}}SummaryResource.php
namespace App\Http\Resources;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

/**
 * Lightweight resource for list views and relationships.
 */
class {{Entity}}SummaryResource extends JsonResource
{
    /**
     * Transform the resource into an array.
     *
     * @param Request $request
     * @return array<string, mixed>
     */
    public function toArray(Request $request): array
    {
        return [
            'id' => $this->id,
            'name' => $this->name,
            'slug' => $this->slug,
            'price' => $this->price,
            'status' => $this->status?->value,
            'thumbnail' => $this->whenLoaded('images', function () {
                return $this->images->first()?->thumbnail_url;
            }),
        ];
    }
}
```

## Resource Patterns

### Conditional Relationship Loading

```php
// In Resource
'related_items' => $this->when(
    $request->has('include') && in_array('related', explode(',', $request->include)),
    fn () => {{Entity}}Resource::collection($this->relatedItems)
),
```

### Dynamic Field Selection

```php
// In Resource
public function toArray(Request $request): array
{
    $fields = $request->has('fields')
        ? explode(',', $request->fields)
        : $this->defaultFields();

    $data = [];
    foreach ($fields as $field) {
        if (method_exists($this, $method = 'get' . Str::studly($field) . 'Field')) {
            $data[$field] = $this->{$method}();
        } elseif (isset($this->resource->{$field})) {
            $data[$field] = $this->resource->{$field};
        }
    }

    return $data;
}
```

### Nested Resource with Depth Control

```php
// In Resource
public function toArray(Request $request): array
{
    $depth = (int) $request->get('depth', 1);

    return [
        'id' => $this->id,
        'name' => $this->name,
        'children' => $this->when(
            $depth > 0 && $this->relationLoaded('children'),
            fn () => {{Entity}}Resource::collection($this->children)
                ->additional(['depth' => $depth - 1])
        ),
    ];
}
```

## Output Files

```
app/Http/Resources/
├── {{Entity}}Resource.php         # Full resource
├── {{Entity}}Collection.php       # Collection resource
└── {{Entity}}SummaryResource.php  # Summary resource
```

## Usage Example

```bash
# Generate resource via agent
@laravel:resource-generator {
  "entity_name": "Product",
  "fields": ["id", "name", "slug", "price", "status"],
  "relationships": ["category", "tags", "images"],
  "conditional_fields": ["metadata", "internal_notes"],
  "collection": true,
  "with_meta": true
}
```

## Validation Checklist

- [ ] All fields exist on model
- [ ] Relationships are properly loaded
- [ ] Conditional fields check permissions
- [ ] Timestamps are ISO 8601 formatted
- [ ] Collection includes pagination meta
- [ ] No N+1 queries (use whenLoaded)
