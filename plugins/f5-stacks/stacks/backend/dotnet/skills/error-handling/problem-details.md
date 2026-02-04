---
name: problem-details
description: RFC 7807 Problem Details responses for ASP.NET Core APIs
applies_to: dotnet
type: skill
---

# Problem Details

## Overview

RFC 7807 defines a standard format for describing errors in HTTP APIs. ASP.NET Core provides built-in support for Problem Details, ensuring consistent error responses.

## Standard Problem Details

### Structure

```json
{
  "type": "https://tools.ietf.org/html/rfc7807",
  "title": "One or more validation errors occurred",
  "status": 400,
  "detail": "See errors property for details",
  "instance": "/api/products",
  "traceId": "00-abc123...",
  "errors": {
    "Name": ["Name is required"],
    "Price": ["Price must be greater than 0"]
  }
}
```

### Built-in Types

```csharp
// ProblemDetails - basic error
public class ProblemDetails
{
    public string? Type { get; set; }
    public string? Title { get; set; }
    public int? Status { get; set; }
    public string? Detail { get; set; }
    public string? Instance { get; set; }
    public IDictionary<string, object?> Extensions { get; }
}

// ValidationProblemDetails - validation errors
public class ValidationProblemDetails : ProblemDetails
{
    public IDictionary<string, string[]> Errors { get; }
}
```

## Configuration

### Enable Problem Details

```csharp
// Program.cs
builder.Services.AddProblemDetails(options =>
{
    options.CustomizeProblemDetails = context =>
    {
        context.ProblemDetails.Instance =
            $"{context.HttpContext.Request.Method} {context.HttpContext.Request.Path}";

        context.ProblemDetails.Extensions["traceId"] =
            context.HttpContext.TraceIdentifier;

        context.ProblemDetails.Extensions["nodeId"] =
            Environment.MachineName;
    };
});

// Use exception handler with Problem Details
app.UseExceptionHandler();
app.UseStatusCodePages();
```

### Custom Error Types

```csharp
// Define custom problem types
public static class ProblemTypes
{
    private const string BaseUrl = "https://api.myapp.com/errors";

    public static string NotFound => $"{BaseUrl}/not-found";
    public static string Validation => $"{BaseUrl}/validation";
    public static string Conflict => $"{BaseUrl}/conflict";
    public static string Unauthorized => $"{BaseUrl}/unauthorized";
    public static string Forbidden => $"{BaseUrl}/forbidden";
    public static string InternalError => $"{BaseUrl}/internal-error";
    public static string RateLimited => $"{BaseUrl}/rate-limited";
}
```

## Creating Problem Details Responses

### In Controllers

```csharp
[ApiController]
[Route("api/[controller]")]
public class ProductsController : ControllerBase
{
    [HttpGet("{id:guid}")]
    public async Task<IActionResult> GetById(Guid id)
    {
        var product = await _service.GetByIdAsync(id);

        if (product is null)
        {
            return Problem(
                title: "Product not found",
                detail: $"Product with ID {id} does not exist",
                statusCode: StatusCodes.Status404NotFound,
                type: ProblemTypes.NotFound);
        }

        return Ok(product);
    }

    [HttpPost]
    public async Task<IActionResult> Create(CreateProductDto dto)
    {
        // Check for duplicate
        if (await _service.SkuExistsAsync(dto.Sku))
        {
            return Problem(
                title: "Duplicate SKU",
                detail: $"A product with SKU '{dto.Sku}' already exists",
                statusCode: StatusCodes.Status409Conflict,
                type: ProblemTypes.Conflict);
        }

        var product = await _service.CreateAsync(dto);
        return CreatedAtAction(nameof(GetById), new { id = product.Id }, product);
    }
}
```

### Validation Problem Details

```csharp
// Return validation errors
[HttpPost]
public IActionResult Create(CreateProductDto dto)
{
    if (dto.Price <= 0)
    {
        ModelState.AddModelError(nameof(dto.Price), "Price must be positive");
    }

    if (string.IsNullOrEmpty(dto.Name))
    {
        ModelState.AddModelError(nameof(dto.Name), "Name is required");
    }

    if (!ModelState.IsValid)
    {
        return ValidationProblem(ModelState);
    }

    // Create product...
    return Ok();
}

// Custom validation problem
[HttpPost]
public IActionResult Create(CreateProductDto dto)
{
    var errors = new Dictionary<string, string[]>
    {
        { "Name", new[] { "Name is required", "Name must be unique" } },
        { "Price", new[] { "Price must be greater than 0" } }
    };

    return ValidationProblem(
        new ValidationProblemDetails(errors)
        {
            Title = "Validation Failed",
            Detail = "Please correct the errors and try again",
            Type = ProblemTypes.Validation,
            Status = StatusCodes.Status422UnprocessableEntity
        });
}
```

## Factory Pattern

### Problem Details Factory

```csharp
// Infrastructure/Services/ProblemDetailsFactory.cs
public interface IAppProblemDetailsFactory
{
    ProblemDetails CreateNotFound(string entityName, object key);
    ProblemDetails CreateConflict(string message);
    ProblemDetails CreateForbidden(string? message = null);
    ProblemDetails CreateBadRequest(string message);
    ValidationProblemDetails CreateValidation(
        IDictionary<string, string[]> errors);
}

public class AppProblemDetailsFactory : IAppProblemDetailsFactory
{
    private readonly IHttpContextAccessor _httpContextAccessor;

    public AppProblemDetailsFactory(IHttpContextAccessor httpContextAccessor)
    {
        _httpContextAccessor = httpContextAccessor;
    }

    public ProblemDetails CreateNotFound(string entityName, object key)
    {
        return new ProblemDetails
        {
            Type = ProblemTypes.NotFound,
            Title = "Resource Not Found",
            Detail = $"{entityName} with key '{key}' was not found",
            Status = StatusCodes.Status404NotFound,
            Instance = GetInstance(),
            Extensions =
            {
                ["traceId"] = GetTraceId()
            }
        };
    }

    public ProblemDetails CreateConflict(string message)
    {
        return new ProblemDetails
        {
            Type = ProblemTypes.Conflict,
            Title = "Resource Conflict",
            Detail = message,
            Status = StatusCodes.Status409Conflict,
            Instance = GetInstance(),
            Extensions =
            {
                ["traceId"] = GetTraceId()
            }
        };
    }

    public ProblemDetails CreateForbidden(string? message = null)
    {
        return new ProblemDetails
        {
            Type = ProblemTypes.Forbidden,
            Title = "Access Denied",
            Detail = message ?? "You do not have permission to access this resource",
            Status = StatusCodes.Status403Forbidden,
            Instance = GetInstance(),
            Extensions =
            {
                ["traceId"] = GetTraceId()
            }
        };
    }

    public ProblemDetails CreateBadRequest(string message)
    {
        return new ProblemDetails
        {
            Type = "https://tools.ietf.org/html/rfc7231#section-6.5.1",
            Title = "Bad Request",
            Detail = message,
            Status = StatusCodes.Status400BadRequest,
            Instance = GetInstance(),
            Extensions =
            {
                ["traceId"] = GetTraceId()
            }
        };
    }

    public ValidationProblemDetails CreateValidation(
        IDictionary<string, string[]> errors)
    {
        return new ValidationProblemDetails(errors)
        {
            Type = ProblemTypes.Validation,
            Title = "Validation Failed",
            Detail = "One or more validation errors occurred",
            Status = StatusCodes.Status422UnprocessableEntity,
            Instance = GetInstance(),
            Extensions =
            {
                ["traceId"] = GetTraceId()
            }
        };
    }

    private string GetInstance()
    {
        var context = _httpContextAccessor.HttpContext;
        return context is not null
            ? $"{context.Request.Method} {context.Request.Path}"
            : "";
    }

    private string GetTraceId()
    {
        return _httpContextAccessor.HttpContext?.TraceIdentifier ?? "";
    }
}
```

## Extended Problem Details

```csharp
// Extended with additional properties
public class ExtendedProblemDetails : ProblemDetails
{
    public string? ErrorCode { get; set; }
    public string? HelpUrl { get; set; }
    public DateTimeOffset Timestamp { get; set; } = DateTimeOffset.UtcNow;
}

// Usage
return new ExtendedProblemDetails
{
    Type = ProblemTypes.Validation,
    Title = "Validation Error",
    Status = 422,
    ErrorCode = "PRODUCT_001",
    HelpUrl = "https://docs.myapp.com/errors/PRODUCT_001"
};
```

## Best Practices

| Practice | Recommendation |
|----------|----------------|
| Type URI | Use consistent, documented type URIs |
| Title | Human-readable, non-changing summary |
| Detail | Specific explanation for this occurrence |
| Instance | URI reference for the specific problem |
| Extensions | Add traceId for correlation |
| Status | Match HTTP response status code |

## Related Skills

- `skills/error-handling/exception-handling.md`
- `skills/api/controller-patterns.md`
