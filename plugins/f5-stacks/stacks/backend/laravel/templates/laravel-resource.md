---
name: laravel-resource
description: Template for Laravel API Resources
applies_to: laravel
type: template
---

# Laravel Resource Template

## API Resource

```php
<?php
// app/Http/Resources/{{EntityName}}Resource.php
namespace App\Http\Resources;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

class {{EntityName}}Resource extends JsonResource
{
    /**
     * Transform the resource into an array.
     *
     * @return array<string, mixed>
     */
    public function toArray(Request $request): array
    {
        return [
            'id' => $this->id,
            'type' => '{{entity_name}}',

            // Basic attributes
            'name' => $this->name,
            'slug' => $this->slug,
            'description' => $this->description,
            'status' => $this->status->value,
            'status_label' => $this->status->label(),

            // Formatted attributes
            'price' => $this->price,
            'formatted_price' => $this->formatted_price,

            // Conditional attributes
            'secret_field' => $this->when($request->user()?->isAdmin(), $this->secret_field),

            // Relationships (only when loaded)
            'category' => new CategoryResource($this->whenLoaded('category')),
            'user' => new UserResource($this->whenLoaded('user')),
            'tags' => TagResource::collection($this->whenLoaded('tags')),
            'items' => {{EntityName}}ItemResource::collection($this->whenLoaded('items')),

            // Counts (only when loaded)
            'items_count' => $this->whenCounted('items'),
            'comments_count' => $this->whenCounted('comments'),

            // Computed/Aggregate values
            'total_value' => $this->whenHas('total_value'),

            // Timestamps
            'published_at' => $this->published_at?->toISOString(),
            'created_at' => $this->created_at->toISOString(),
            'updated_at' => $this->updated_at->toISOString(),

            // Links
            'links' => [
                'self' => route('api.{{entityNames}}.show', $this->id),
            ],
        ];
    }

    /**
     * Get additional data that should be returned with the resource array.
     *
     * @return array<string, mixed>
     */
    public function with(Request $request): array
    {
        return [
            'meta' => [
                'version' => '1.0',
            ],
        ];
    }
}
```

## Collection Resource

```php
<?php
// app/Http/Resources/{{EntityName}}Collection.php
namespace App\Http\Resources;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\ResourceCollection;

class {{EntityName}}Collection extends ResourceCollection
{
    /**
     * The resource that this resource collects.
     */
    public $collects = {{EntityName}}Resource::class;

    /**
     * Transform the resource collection into an array.
     *
     * @return array<int|string, mixed>
     */
    public function toArray(Request $request): array
    {
        return [
            'data' => $this->collection,
            'meta' => [
                'total' => $this->total(),
                'count' => $this->count(),
            ],
        ];
    }
}
```

## Lightweight Resource (for lists)

```php
<?php
// app/Http/Resources/{{EntityName}}ListResource.php
namespace App\Http\Resources;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

class {{EntityName}}ListResource extends JsonResource
{
    /**
     * Transform the resource into an array.
     * Lightweight version for lists/dropdowns.
     *
     * @return array<string, mixed>
     */
    public function toArray(Request $request): array
    {
        return [
            'id' => $this->id,
            'name' => $this->name,
            'slug' => $this->slug,
            'status' => $this->status->value,
        ];
    }
}
```

## Detail Resource (for single view)

```php
<?php
// app/Http/Resources/{{EntityName}}DetailResource.php
namespace App\Http\Resources;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

class {{EntityName}}DetailResource extends JsonResource
{
    /**
     * Transform the resource into an array.
     * Full detail version with all relationships.
     *
     * @return array<string, mixed>
     */
    public function toArray(Request $request): array
    {
        return [
            'id' => $this->id,
            'type' => '{{entity_name}}',

            // All attributes
            'name' => $this->name,
            'slug' => $this->slug,
            'description' => $this->description,
            'content' => $this->content,
            'status' => $this->status->value,
            'status_label' => $this->status->label(),

            // Full relationships
            'category' => new CategoryResource($this->category),
            'user' => new UserResource($this->user),
            'tags' => TagResource::collection($this->tags),

            // Related items with details
            'items' => {{EntityName}}ItemResource::collection($this->items),

            // Activity/History
            'activities' => ActivityResource::collection($this->whenLoaded('activities')),

            // Metadata
            'metadata' => $this->metadata,

            // Timestamps
            'published_at' => $this->published_at?->toISOString(),
            'created_at' => $this->created_at->toISOString(),
            'updated_at' => $this->updated_at->toISOString(),

            // Links
            'links' => [
                'self' => route('api.{{entityNames}}.show', $this->id),
                'edit' => route('api.{{entityNames}}.update', $this->id),
                'delete' => route('api.{{entityNames}}.destroy', $this->id),
            ],
        ];
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
