---
name: laravel-policy
description: Template for Laravel Authorization Policies
applies_to: laravel
type: template
---

# Laravel Policy Template

## Policy Class

```php
<?php
// app/Policies/{{EntityName}}Policy.php
namespace App\Policies;

use App\Models\{{EntityName}};
use App\Models\User;
use Illuminate\Auth\Access\HandlesAuthorization;
use Illuminate\Auth\Access\Response;

class {{EntityName}}Policy
{
    use HandlesAuthorization;

    /**
     * Perform pre-authorization checks.
     */
    public function before(User $user, string $ability): ?bool
    {
        // Super admins can do anything
        if ($user->isSuperAdmin()) {
            return true;
        }

        // Suspended users can't do anything
        if ($user->isSuspended()) {
            return false;
        }

        return null;
    }

    /**
     * Determine whether the user can view any models.
     */
    public function viewAny(User $user): Response|bool
    {
        return $user->hasPermission('{{entity_name}}.view')
            ? Response::allow()
            : Response::deny('You do not have permission to view {{entityNames}}.');
    }

    /**
     * Determine whether the user can view the model.
     */
    public function view(User $user, {{EntityName}} ${{entityName}}): Response|bool
    {
        // Public {{entityNames}} can be viewed by anyone
        if (${{entityName}}->is_public) {
            return true;
        }

        // Owner can always view
        if ($user->id === ${{entityName}}->user_id) {
            return true;
        }

        // Check permission
        return $user->hasPermission('{{entity_name}}.view');
    }

    /**
     * Determine whether the user can create models.
     */
    public function create(User $user): Response|bool
    {
        return $user->hasPermission('{{entity_name}}.create')
            ? Response::allow()
            : Response::deny('You do not have permission to create {{entityNames}}.');
    }

    /**
     * Determine whether the user can update the model.
     */
    public function update(User $user, {{EntityName}} ${{entityName}}): Response|bool
    {
        // Owner can update
        if ($user->id === ${{entityName}}->user_id) {
            return Response::allow();
        }

        // Admins can update
        if ($user->hasPermission('{{entity_name}}.update')) {
            return Response::allow();
        }

        return Response::deny('You do not have permission to update this {{entityName}}.');
    }

    /**
     * Determine whether the user can delete the model.
     */
    public function delete(User $user, {{EntityName}} ${{entityName}}): Response|bool
    {
        // Cannot delete archived {{entityNames}}
        if (${{entityName}}->isArchived()) {
            return Response::deny('Archived {{entityNames}} cannot be deleted.');
        }

        // Owner can delete their own
        if ($user->id === ${{entityName}}->user_id) {
            return Response::allow();
        }

        // Admins can delete
        if ($user->hasPermission('{{entity_name}}.delete')) {
            return Response::allow();
        }

        return Response::deny('You do not have permission to delete this {{entityName}}.');
    }

    /**
     * Determine whether the user can restore the model.
     */
    public function restore(User $user, {{EntityName}} ${{entityName}}): Response|bool
    {
        return $user->hasPermission('{{entity_name}}.restore')
            ? Response::allow()
            : Response::deny('You do not have permission to restore {{entityNames}}.');
    }

    /**
     * Determine whether the user can permanently delete the model.
     */
    public function forceDelete(User $user, {{EntityName}} ${{entityName}}): Response|bool
    {
        return $user->hasPermission('{{entity_name}}.force-delete')
            ? Response::allow()
            : Response::deny('You do not have permission to permanently delete {{entityNames}}.');
    }

    /**
     * Determine whether the user can publish the model.
     */
    public function publish(User $user, {{EntityName}} ${{entityName}}): Response|bool
    {
        // Must be the owner or have permission
        if ($user->id !== ${{entityName}}->user_id && !$user->hasPermission('{{entity_name}}.publish')) {
            return Response::deny('You do not have permission to publish this {{entityName}}.');
        }

        // Check if {{entityName}} is publishable
        if (!${{entityName}}->canBePublished()) {
            return Response::deny('This {{entityName}} cannot be published in its current state.');
        }

        return Response::allow();
    }

    /**
     * Determine whether the user can archive the model.
     */
    public function archive(User $user, {{EntityName}} ${{entityName}}): Response|bool
    {
        // Owner can archive their own
        if ($user->id === ${{entityName}}->user_id) {
            return Response::allow();
        }

        return $user->hasPermission('{{entity_name}}.archive')
            ? Response::allow()
            : Response::deny('You do not have permission to archive this {{entityName}}.');
    }

    /**
     * Determine whether the user can manage {{entityName}} tags.
     */
    public function manageTags(User $user, {{EntityName}} ${{entityName}}): Response|bool
    {
        // Owner or editor permission
        if ($user->id === ${{entityName}}->user_id || $user->hasPermission('{{entity_name}}.edit')) {
            return Response::allow();
        }

        return Response::deny('You do not have permission to manage tags for this {{entityName}}.');
    }
}
```

## Register Policy

```php
<?php
// app/Providers/AuthServiceProvider.php
namespace App\Providers;

use App\Models\{{EntityName}};
use App\Policies\{{EntityName}}Policy;
use Illuminate\Foundation\Support\Providers\AuthServiceProvider as ServiceProvider;

class AuthServiceProvider extends ServiceProvider
{
    /**
     * The model to policy mappings for the application.
     *
     * @var array<class-string, class-string>
     */
    protected $policies = [
        {{EntityName}}::class => {{EntityName}}Policy::class,
    ];

    public function boot(): void
    {
        //
    }
}
```

## Usage in Controller

```php
<?php
// Authorization in controller
public function update(Update{{EntityName}}Request $request, {{EntityName}} ${{entityName}})
{
    $this->authorize('update', ${{entityName}});

    // or in form request
    // public function authorize(): bool
    // {
    //     return $this->user()->can('update', $this->route('{{entityName}}'));
    // }
}
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{EntityName}}` | PascalCase entity name | `Product` |
| `{{entityName}}` | camelCase entity name | `product` |
| `{{entityNames}}` | camelCase plural | `products` |
| `{{entity_name}}` | snake_case entity name | `product` |
