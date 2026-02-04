---
name: authorization-policies
description: Policy-based authorization for ASP.NET Core
applies_to: dotnet
type: skill
---

# Authorization Policies

## Overview

Policy-based authorization provides flexible, reusable authorization rules that can combine multiple requirements.

## Basic Setup

```csharp
// Program.cs
builder.Services.AddAuthorization(options =>
{
    // Simple role-based policy
    options.AddPolicy("AdminOnly", policy =>
        policy.RequireRole("Admin"));

    // Multiple roles (any of)
    options.AddPolicy("ManagerOrAdmin", policy =>
        policy.RequireRole("Manager", "Admin"));

    // Claim-based policy
    options.AddPolicy("VerifiedUser", policy =>
        policy.RequireClaim("email_verified", "true"));

    // Custom requirement
    options.AddPolicy("MinimumAge", policy =>
        policy.Requirements.Add(new MinimumAgeRequirement(18)));

    // Combined requirements
    options.AddPolicy("SeniorEditor", policy =>
        policy
            .RequireRole("Editor")
            .RequireClaim("experience_years")
            .Requirements.Add(new MinimumExperienceRequirement(5)));
});
```

## Custom Requirements

### Requirement Class

```csharp
// Requirements/MinimumAgeRequirement.cs
public class MinimumAgeRequirement : IAuthorizationRequirement
{
    public int MinimumAge { get; }

    public MinimumAgeRequirement(int minimumAge)
    {
        MinimumAge = minimumAge;
    }
}

// Requirements/MinimumAgeHandler.cs
public class MinimumAgeHandler
    : AuthorizationHandler<MinimumAgeRequirement>
{
    protected override Task HandleRequirementAsync(
        AuthorizationHandlerContext context,
        MinimumAgeRequirement requirement)
    {
        var dobClaim = context.User.FindFirst(c =>
            c.Type == "date_of_birth");

        if (dobClaim is null)
            return Task.CompletedTask;

        if (DateTime.TryParse(dobClaim.Value, out var dob))
        {
            var age = DateTime.Today.Year - dob.Year;
            if (dob.Date > DateTime.Today.AddYears(-age))
                age--;

            if (age >= requirement.MinimumAge)
            {
                context.Succeed(requirement);
            }
        }

        return Task.CompletedTask;
    }
}

// Registration
builder.Services.AddSingleton<IAuthorizationHandler, MinimumAgeHandler>();
```

### Resource-Based Authorization

```csharp
// Requirements/SameAuthorRequirement.cs
public class SameAuthorRequirement : IAuthorizationRequirement { }

public class DocumentAuthorizationHandler
    : AuthorizationHandler<SameAuthorRequirement, Document>
{
    protected override Task HandleRequirementAsync(
        AuthorizationHandlerContext context,
        SameAuthorRequirement requirement,
        Document resource)
    {
        var userId = context.User.FindFirst(ClaimTypes.NameIdentifier)?.Value;

        if (userId is not null && resource.AuthorId.ToString() == userId)
        {
            context.Succeed(requirement);
        }

        return Task.CompletedTask;
    }
}

// Usage in controller
[Authorize]
public class DocumentsController : ControllerBase
{
    private readonly IAuthorizationService _authorizationService;
    private readonly IDocumentService _documentService;

    [HttpPut("{id:guid}")]
    public async Task<IActionResult> Update(
        Guid id,
        UpdateDocumentDto dto,
        CancellationToken ct)
    {
        var document = await _documentService.GetByIdAsync(id, ct);

        if (document is null)
            return NotFound();

        var authResult = await _authorizationService.AuthorizeAsync(
            User,
            document,
            new SameAuthorRequirement());

        if (!authResult.Succeeded)
            return Forbid();

        // Update logic...
        return Ok();
    }
}
```

### Operation-Based Authorization

```csharp
// Operations
public static class Operations
{
    public static OperationAuthorizationRequirement Create =
        new() { Name = nameof(Create) };
    public static OperationAuthorizationRequirement Read =
        new() { Name = nameof(Read) };
    public static OperationAuthorizationRequirement Update =
        new() { Name = nameof(Update) };
    public static OperationAuthorizationRequirement Delete =
        new() { Name = nameof(Delete) };
}

// Handler
public class ProductAuthorizationHandler
    : AuthorizationHandler<OperationAuthorizationRequirement, Product>
{
    protected override Task HandleRequirementAsync(
        AuthorizationHandlerContext context,
        OperationAuthorizationRequirement requirement,
        Product resource)
    {
        var userId = context.User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
        var isAdmin = context.User.IsInRole("Admin");

        switch (requirement.Name)
        {
            case nameof(Operations.Read):
                // Everyone can read published products
                if (resource.IsPublished || isAdmin)
                    context.Succeed(requirement);
                break;

            case nameof(Operations.Create):
                // Sellers and admins can create
                if (context.User.IsInRole("Seller") || isAdmin)
                    context.Succeed(requirement);
                break;

            case nameof(Operations.Update):
                // Owner or admin can update
                if (resource.SellerId.ToString() == userId || isAdmin)
                    context.Succeed(requirement);
                break;

            case nameof(Operations.Delete):
                // Only admin can delete
                if (isAdmin)
                    context.Succeed(requirement);
                break;
        }

        return Task.CompletedTask;
    }
}

// Usage
var authResult = await _authorizationService.AuthorizeAsync(
    User,
    product,
    Operations.Update);
```

## Policy Provider

```csharp
// Dynamic policy generation
public class PermissionPolicyProvider : IAuthorizationPolicyProvider
{
    private readonly DefaultAuthorizationPolicyProvider _fallback;

    public PermissionPolicyProvider(IOptions<AuthorizationOptions> options)
    {
        _fallback = new DefaultAuthorizationPolicyProvider(options);
    }

    public Task<AuthorizationPolicy> GetDefaultPolicyAsync() =>
        _fallback.GetDefaultPolicyAsync();

    public Task<AuthorizationPolicy?> GetFallbackPolicyAsync() =>
        _fallback.GetFallbackPolicyAsync();

    public Task<AuthorizationPolicy?> GetPolicyAsync(string policyName)
    {
        if (policyName.StartsWith("Permission:"))
        {
            var permission = policyName.Substring("Permission:".Length);
            var policy = new AuthorizationPolicyBuilder()
                .AddRequirements(new PermissionRequirement(permission))
                .Build();

            return Task.FromResult<AuthorizationPolicy?>(policy);
        }

        return _fallback.GetPolicyAsync(policyName);
    }
}

// Requirement
public class PermissionRequirement : IAuthorizationRequirement
{
    public string Permission { get; }

    public PermissionRequirement(string permission)
    {
        Permission = permission;
    }
}

// Handler
public class PermissionHandler : AuthorizationHandler<PermissionRequirement>
{
    private readonly IPermissionService _permissionService;

    public PermissionHandler(IPermissionService permissionService)
    {
        _permissionService = permissionService;
    }

    protected override async Task HandleRequirementAsync(
        AuthorizationHandlerContext context,
        PermissionRequirement requirement)
    {
        var userId = context.User.FindFirst(ClaimTypes.NameIdentifier)?.Value;

        if (userId is null)
            return;

        var hasPermission = await _permissionService.UserHasPermissionAsync(
            Guid.Parse(userId),
            requirement.Permission);

        if (hasPermission)
            context.Succeed(requirement);
    }
}

// Usage with attribute
[Authorize(Policy = "Permission:products.edit")]
public IActionResult EditProduct() { }
```

## Custom Authorize Attribute

```csharp
// Attribute
[AttributeUsage(AttributeTargets.Class | AttributeTargets.Method)]
public class HasPermissionAttribute : AuthorizeAttribute
{
    public HasPermissionAttribute(string permission)
        : base($"Permission:{permission}")
    {
    }
}

// Usage
[HasPermission("products.create")]
public IActionResult CreateProduct() { }

[HasPermission("products.delete")]
public IActionResult DeleteProduct() { }
```

## Best Practices

| Practice | Recommendation |
|----------|----------------|
| Policy naming | Use descriptive names: `CanEditProducts` |
| Requirement reuse | Create reusable requirements |
| Handler scope | Use scoped for DB-dependent |
| Failure reasons | Use `context.Fail()` with reason |
| Testing | Unit test handlers with mocked context |

## Related Skills

- `skills/security/jwt-authentication.md`
- `skills/security/identity-setup.md`
