---
name: laravel-controller
description: Template for Laravel API Controllers
applies_to: laravel
type: template
---

# Laravel Controller Template

## API Resource Controller

```php
<?php
// app/Http/Controllers/Api/{{EntityName}}Controller.php
namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Http\Requests\{{EntityName}}\Create{{EntityName}}Request;
use App\Http\Requests\{{EntityName}}\Update{{EntityName}}Request;
use App\Http\Resources\{{EntityName}}Resource;
use App\Models\{{EntityName}};
use App\Services\{{EntityName}}Service;
use App\Traits\ApiResponse;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\AnonymousResourceCollection;

class {{EntityName}}Controller extends Controller
{
    use ApiResponse;

    public function __construct(
        protected {{EntityName}}Service ${{entityName}}Service
    ) {}

    /**
     * Display a listing of the resource.
     *
     * @param Request $request
     * @return JsonResponse
     */
    public function index(Request $request): JsonResponse
    {
        $this->authorize('viewAny', {{EntityName}}::class);

        ${{entityNames}} = $this->{{entityName}}Service->paginate(
            perPage: $request->integer('per_page', 15),
            filters: $request->only([
                'search',
                'status',
                // Add filter fields
            ])
        );

        return $this->paginated(
            {{EntityName}}Resource::collection(${{entityNames}}),
            '{{EntityName}}s retrieved successfully'
        );
    }

    /**
     * Store a newly created resource in storage.
     *
     * @param Create{{EntityName}}Request $request
     * @return JsonResponse
     */
    public function store(Create{{EntityName}}Request $request): JsonResponse
    {
        ${{entityName}} = $this->{{entityName}}Service->create($request->validated());

        return $this->created(
            {{EntityName}}Resource::make(${{entityName}}),
            '{{EntityName}} created successfully'
        );
    }

    /**
     * Display the specified resource.
     *
     * @param {{EntityName}} ${{entityName}}
     * @return JsonResponse
     */
    public function show({{EntityName}} ${{entityName}}): JsonResponse
    {
        $this->authorize('view', ${{entityName}});

        return $this->success(
            {{EntityName}}Resource::make(${{entityName}}->load([/* relationships */])),
            '{{EntityName}} retrieved successfully'
        );
    }

    /**
     * Update the specified resource in storage.
     *
     * @param Update{{EntityName}}Request $request
     * @param {{EntityName}} ${{entityName}}
     * @return JsonResponse
     */
    public function update(Update{{EntityName}}Request $request, {{EntityName}} ${{entityName}}): JsonResponse
    {
        ${{entityName}} = $this->{{entityName}}Service->update(${{entityName}}, $request->validated());

        return $this->success(
            {{EntityName}}Resource::make(${{entityName}}),
            '{{EntityName}} updated successfully'
        );
    }

    /**
     * Remove the specified resource from storage.
     *
     * @param {{EntityName}} ${{entityName}}
     * @return JsonResponse
     */
    public function destroy({{EntityName}} ${{entityName}}): JsonResponse
    {
        $this->authorize('delete', ${{entityName}});

        $this->{{entityName}}Service->delete(${{entityName}});

        return $this->noContent();
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

## Usage

```bash
# Generate controller
php artisan make:controller Api/ProductController --api --model=Product

# Then customize using this template
```
