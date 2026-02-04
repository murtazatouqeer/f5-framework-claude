---
name: laravel-controller-generator
description: Agent for generating Laravel API controllers with CRUD operations
applies_to: laravel
category: agent
---

# Laravel Controller Generator Agent

## Purpose

Generate production-ready Laravel API controllers with proper validation, authorization, and API Resource responses.

## Input Requirements

```yaml
required:
  - entity_name: string        # e.g., "Product"
  - entity_plural: string      # e.g., "products"

optional:
  - api_version: string        # API version (default: "v1")
  - authentication: boolean    # Add Sanctum auth (default: true)
  - authorization: boolean     # Add Policy checks (default: true)
  - pagination: boolean        # Add paginated list endpoint (default: true)
  - soft_delete: boolean       # Support soft deletes (default: true)
  - custom_endpoints: array    # Additional custom endpoints
  - use_service: boolean       # Use service layer (default: true)
```

## Generation Process

### Step 1: Analyze Module Structure

```php
// Check existing files
$serviceExists = file_exists("app/Services/{$entityName}Service.php");
$requestsExist = file_exists("app/Http/Requests/{$entityName}/Create{$entityName}Request.php");
$resourceExists = file_exists("app/Http/Resources/{$entityName}Resource.php");
$policyExists = file_exists("app/Policies/{$entityName}Policy.php");
```

### Step 2: Generate Controller

```php
<?php
// app/Http/Controllers/Api/V1/{{Entity}}Controller.php
namespace App\Http\Controllers\Api\V1;

use App\Http\Controllers\Controller;
use App\Http\Requests\{{Entity}}\Create{{Entity}}Request;
use App\Http\Requests\{{Entity}}\Update{{Entity}}Request;
use App\Http\Resources\{{Entity}}Resource;
use App\Models\{{Entity}};
use App\Services\{{Entity}}Service;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\AnonymousResourceCollection;

class {{Entity}}Controller extends Controller
{
    public function __construct(
        protected {{Entity}}Service ${{entity}}Service
    ) {}

    /**
     * Display a listing of the resource.
     *
     * @param Request $request
     * @return AnonymousResourceCollection
     */
    public function index(Request $request): AnonymousResourceCollection
    {
        $this->authorize('viewAny', {{Entity}}::class);

        ${{entities}} = $this->{{entity}}Service->paginate(
            perPage: $request->integer('per_page', 15),
            filters: $request->only(['search', 'status', 'category_id'])
        );

        return {{Entity}}Resource::collection(${{entities}});
    }

    /**
     * Store a newly created resource in storage.
     *
     * @param Create{{Entity}}Request $request
     * @return JsonResponse
     */
    public function store(Create{{Entity}}Request $request): JsonResponse
    {
        ${{entity}} = $this->{{entity}}Service->create($request->validated());

        return {{Entity}}Resource::make(${{entity}})
            ->response()
            ->setStatusCode(201);
    }

    /**
     * Display the specified resource.
     *
     * @param {{Entity}} ${{entity}}
     * @return {{Entity}}Resource
     */
    public function show({{Entity}} ${{entity}}): {{Entity}}Resource
    {
        $this->authorize('view', ${{entity}});

        return {{Entity}}Resource::make(
            ${{entity}}->load(['category', 'tags'])
        );
    }

    /**
     * Update the specified resource in storage.
     *
     * @param Update{{Entity}}Request $request
     * @param {{Entity}} ${{entity}}
     * @return {{Entity}}Resource
     */
    public function update(Update{{Entity}}Request $request, {{Entity}} ${{entity}}): {{Entity}}Resource
    {
        ${{entity}} = $this->{{entity}}Service->update(${{entity}}, $request->validated());

        return {{Entity}}Resource::make(${{entity}});
    }

    /**
     * Remove the specified resource from storage.
     *
     * @param {{Entity}} ${{entity}}
     * @return JsonResponse
     */
    public function destroy({{Entity}} ${{entity}}): JsonResponse
    {
        $this->authorize('delete', ${{entity}});

        $this->{{entity}}Service->delete(${{entity}});

        return response()->json(null, 204);
    }
}
```

### Step 3: Generate Optional Endpoints

#### Activate/Deactivate Actions

```php
/**
 * Activate the specified resource.
 *
 * @param {{Entity}} ${{entity}}
 * @return {{Entity}}Resource
 */
public function activate({{Entity}} ${{entity}}): {{Entity}}Resource
{
    $this->authorize('update', ${{entity}});

    ${{entity}} = $this->{{entity}}Service->activate(${{entity}});

    return {{Entity}}Resource::make(${{entity}});
}

/**
 * Deactivate the specified resource.
 *
 * @param {{Entity}} ${{entity}}
 * @return {{Entity}}Resource
 */
public function deactivate({{Entity}} ${{entity}}): {{Entity}}Resource
{
    $this->authorize('update', ${{entity}});

    ${{entity}} = $this->{{entity}}Service->deactivate(${{entity}});

    return {{Entity}}Resource::make(${{entity}});
}
```

#### Bulk Operations

```php
/**
 * Bulk create resources.
 *
 * @param Request $request
 * @return AnonymousResourceCollection
 */
public function bulkStore(Request $request): AnonymousResourceCollection
{
    $this->authorize('create', {{Entity}}::class);

    ${{entities}} = $this->{{entity}}Service->bulkCreate($request->input('items', []));

    return {{Entity}}Resource::collection(${{entities}});
}

/**
 * Bulk delete resources.
 *
 * @param Request $request
 * @return JsonResponse
 */
public function bulkDestroy(Request $request): JsonResponse
{
    $this->authorize('deleteAny', {{Entity}}::class);

    $this->{{entity}}Service->bulkDelete($request->input('ids', []));

    return response()->json(null, 204);
}
```

#### Export Endpoint

```php
/**
 * Export resources to CSV.
 *
 * @param Request $request
 * @return \Symfony\Component\HttpFoundation\StreamedResponse
 */
public function export(Request $request)
{
    $this->authorize('viewAny', {{Entity}}::class);

    return $this->{{entity}}Service->exportToCsv(
        $request->only(['search', 'status'])
    );
}
```

### Step 4: Register Routes

```php
// routes/api.php
use App\Http\Controllers\Api\V1\{{Entity}}Controller;

Route::prefix('v1')->middleware(['auth:sanctum'])->group(function () {
    Route::apiResource('{{entities}}', {{Entity}}Controller::class);

    Route::prefix('{{entities}}')->group(function () {
        Route::post('{{{entity}}}/activate', [{{Entity}}Controller::class, 'activate']);
        Route::post('{{{entity}}}/deactivate', [{{Entity}}Controller::class, 'deactivate']);
        Route::post('bulk', [{{Entity}}Controller::class, 'bulkStore']);
        Route::delete('bulk', [{{Entity}}Controller::class, 'bulkDestroy']);
        Route::get('export', [{{Entity}}Controller::class, 'export']);
    });
});
```

## Output Files

```
app/Http/Controllers/Api/V1/
└── {{Entity}}Controller.php    # Generated controller

routes/
└── api.php                     # Updated routes
```

## Usage Example

```bash
# Generate controller via agent
@laravel:controller-generator {
  "entity_name": "Product",
  "entity_plural": "products",
  "api_version": "v1",
  "authentication": true,
  "authorization": true,
  "use_service": true
}
```

## Validation Checklist

- [ ] Service exists and is injectable
- [ ] Form Requests are defined and validated
- [ ] API Resource is defined
- [ ] Policy exists for authorization
- [ ] Routes are registered
- [ ] Model binding works correctly
- [ ] Error responses are consistent
