---
name: controller-patterns
description: ASP.NET Core controller best practices and patterns
applies_to: dotnet
type: skill
---

# Controller Patterns

## Overview

ASP.NET Core controllers handle HTTP requests and orchestrate the response. This guide covers best practices for building maintainable, testable API controllers.

## Basic Controller Structure

```csharp
// Controllers/ProductsController.cs
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace MyApp.API.Controllers;

[ApiController]
[Route("api/[controller]")]
[Produces("application/json")]
public class ProductsController : ControllerBase
{
    private readonly IMediator _mediator;
    private readonly ILogger<ProductsController> _logger;

    public ProductsController(
        IMediator mediator,
        ILogger<ProductsController> logger)
    {
        _mediator = mediator;
        _logger = logger;
    }

    /// <summary>
    /// Get all products with optional filtering and pagination
    /// </summary>
    /// <param name="query">Filter and pagination parameters</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>Paginated list of products</returns>
    [HttpGet]
    [ProducesResponseType(typeof(PaginatedList<ProductDto>), StatusCodes.Status200OK)]
    public async Task<ActionResult<PaginatedList<ProductDto>>> GetAll(
        [FromQuery] GetProductsQuery query,
        CancellationToken cancellationToken)
    {
        var result = await _mediator.Send(query, cancellationToken);
        return Ok(result);
    }

    /// <summary>
    /// Get a product by ID
    /// </summary>
    /// <param name="id">Product ID</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>Product details</returns>
    [HttpGet("{id:guid}")]
    [ProducesResponseType(typeof(ProductDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<ProductDto>> GetById(
        Guid id,
        CancellationToken cancellationToken)
    {
        var query = new GetProductByIdQuery(id);
        var result = await _mediator.Send(query, cancellationToken);

        if (result is null)
            return NotFound();

        return Ok(result);
    }

    /// <summary>
    /// Create a new product
    /// </summary>
    /// <param name="command">Product creation data</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>Created product</returns>
    [HttpPost]
    [Authorize(Policy = "ProductWrite")]
    [ProducesResponseType(typeof(ProductDto), StatusCodes.Status201Created)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    public async Task<ActionResult<ProductDto>> Create(
        [FromBody] CreateProductCommand command,
        CancellationToken cancellationToken)
    {
        var result = await _mediator.Send(command, cancellationToken);

        return CreatedAtAction(
            nameof(GetById),
            new { id = result.Id },
            result);
    }

    /// <summary>
    /// Update an existing product
    /// </summary>
    [HttpPut("{id:guid}")]
    [Authorize(Policy = "ProductWrite")]
    [ProducesResponseType(typeof(ProductDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<ActionResult<ProductDto>> Update(
        Guid id,
        [FromBody] UpdateProductCommand command,
        CancellationToken cancellationToken)
    {
        if (id != command.Id)
            return BadRequest("ID mismatch");

        var result = await _mediator.Send(command, cancellationToken);

        if (result is null)
            return NotFound();

        return Ok(result);
    }

    /// <summary>
    /// Delete a product
    /// </summary>
    [HttpDelete("{id:guid}")]
    [Authorize(Policy = "ProductDelete")]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> Delete(
        Guid id,
        CancellationToken cancellationToken)
    {
        var command = new DeleteProductCommand(id);
        var success = await _mediator.Send(command, cancellationToken);

        if (!success)
            return NotFound();

        return NoContent();
    }
}
```

## Route Patterns

### Resource Routes

```csharp
// Standard CRUD routes
[HttpGet]                           // GET /api/products
[HttpGet("{id:guid}")]              // GET /api/products/{id}
[HttpPost]                          // POST /api/products
[HttpPut("{id:guid}")]              // PUT /api/products/{id}
[HttpPatch("{id:guid}")]            // PATCH /api/products/{id}
[HttpDelete("{id:guid}")]           // DELETE /api/products/{id}

// Nested resources
[Route("api/categories/{categoryId}/products")]
public class CategoryProductsController : ControllerBase
{
    [HttpGet]                       // GET /api/categories/{categoryId}/products
    public async Task<ActionResult<IEnumerable<ProductDto>>> GetByCategoryId(
        Guid categoryId) { }
}

// Actions on resources
[HttpPost("{id:guid}/activate")]    // POST /api/products/{id}/activate
[HttpPost("{id:guid}/deactivate")]  // POST /api/products/{id}/deactivate
```

### Query Parameters

```csharp
// Simple parameters
[HttpGet]
public async Task<ActionResult> GetAll(
    [FromQuery] string? search,
    [FromQuery] int page = 1,
    [FromQuery] int pageSize = 10)

// Complex query object
public record GetProductsQuery(
    string? Search,
    Guid? CategoryId,
    decimal? MinPrice,
    decimal? MaxPrice,
    bool? IsActive,
    int Page = 1,
    int PageSize = 10
);

[HttpGet]
public async Task<ActionResult> GetAll([FromQuery] GetProductsQuery query)
```

## Response Patterns

### Returning Results

```csharp
// 200 OK with data
return Ok(result);

// 201 Created with location header
return CreatedAtAction(nameof(GetById), new { id = result.Id }, result);

// 204 No Content
return NoContent();

// 400 Bad Request
return BadRequest(new { error = "Invalid request" });

// 404 Not Found
return NotFound();

// 409 Conflict
return Conflict(new { error = "Resource already exists" });

// 422 Unprocessable Entity (validation errors)
return UnprocessableEntity(ModelState);
```

### Envelope Pattern

```csharp
// Common response wrapper
public class ApiResponse<T>
{
    public bool Success { get; set; }
    public T? Data { get; set; }
    public string? Message { get; set; }
    public IEnumerable<string>? Errors { get; set; }
}

// Controller action
[HttpGet("{id:guid}")]
public async Task<ActionResult<ApiResponse<ProductDto>>> GetById(Guid id)
{
    var result = await _mediator.Send(new GetProductByIdQuery(id));

    if (result is null)
        return NotFound(new ApiResponse<ProductDto>
        {
            Success = false,
            Message = "Product not found"
        });

    return Ok(new ApiResponse<ProductDto>
    {
        Success = true,
        Data = result
    });
}
```

## Model Binding

### Source Attributes

```csharp
[HttpPut("{id:guid}")]
public async Task<ActionResult> Update(
    [FromRoute] Guid id,           // From URL route
    [FromBody] UpdateDto dto,       // From request body
    [FromQuery] bool notify = false,// From query string
    [FromHeader(Name = "X-Request-Id")] string? requestId) // From header
```

### File Upload

```csharp
[HttpPost("upload")]
[Consumes("multipart/form-data")]
public async Task<ActionResult> UploadImage(
    [FromForm] IFormFile file,
    [FromForm] string description)
{
    if (file.Length == 0)
        return BadRequest("No file provided");

    if (file.Length > 5 * 1024 * 1024)
        return BadRequest("File too large");

    var allowedTypes = new[] { "image/jpeg", "image/png" };
    if (!allowedTypes.Contains(file.ContentType))
        return BadRequest("Invalid file type");

    // Process file...
    return Ok(new { url = uploadedUrl });
}
```

## API Versioning

### Setup

```csharp
// Program.cs
builder.Services.AddApiVersioning(options =>
{
    options.DefaultApiVersion = new ApiVersion(1, 0);
    options.AssumeDefaultVersionWhenUnspecified = true;
    options.ReportApiVersions = true;
})
.AddApiExplorer(options =>
{
    options.GroupNameFormat = "'v'VVV";
    options.SubstituteApiVersionInUrl = true;
});
```

### Versioned Controllers

```csharp
// URL versioning
[ApiController]
[Route("api/v{version:apiVersion}/products")]
[ApiVersion("1.0")]
public class ProductsController : ControllerBase { }

[ApiController]
[Route("api/v{version:apiVersion}/products")]
[ApiVersion("2.0")]
public class ProductsV2Controller : ControllerBase { }

// Header versioning
[ApiVersion("1.0")]
public class ProductsController : ControllerBase
{
    // Access via: X-Api-Version: 1.0
}
```

## Filters

### Action Filters

```csharp
// Filters/ValidateModelAttribute.cs
public class ValidateModelAttribute : ActionFilterAttribute
{
    public override void OnActionExecuting(ActionExecutingContext context)
    {
        if (!context.ModelState.IsValid)
        {
            context.Result = new BadRequestObjectResult(context.ModelState);
        }
    }
}

// Usage
[ValidateModel]
[HttpPost]
public async Task<ActionResult> Create([FromBody] CreateDto dto)
```

### Exception Filter

```csharp
// Filters/ApiExceptionFilterAttribute.cs
public class ApiExceptionFilterAttribute : ExceptionFilterAttribute
{
    private readonly ILogger<ApiExceptionFilterAttribute> _logger;

    public ApiExceptionFilterAttribute(ILogger<ApiExceptionFilterAttribute> logger)
    {
        _logger = logger;
    }

    public override void OnException(ExceptionContext context)
    {
        _logger.LogError(context.Exception, "Unhandled exception occurred");

        var problemDetails = context.Exception switch
        {
            NotFoundException => new ProblemDetails
            {
                Status = StatusCodes.Status404NotFound,
                Title = "Resource not found",
                Detail = context.Exception.Message
            },
            ValidationException ve => new ValidationProblemDetails(
                ve.Errors.GroupBy(e => e.PropertyName)
                    .ToDictionary(g => g.Key, g => g.Select(e => e.ErrorMessage).ToArray()))
            {
                Status = StatusCodes.Status422UnprocessableEntity
            },
            _ => new ProblemDetails
            {
                Status = StatusCodes.Status500InternalServerError,
                Title = "An error occurred"
            }
        };

        context.Result = new ObjectResult(problemDetails)
        {
            StatusCode = problemDetails.Status
        };

        context.ExceptionHandled = true;
    }
}
```

## Best Practices

| Practice | Recommendation |
|----------|----------------|
| Keep controllers thin | Delegate to handlers/services |
| Use DTOs | Never expose domain entities |
| Async all the way | All I/O operations async |
| CancellationToken | Always accept and pass through |
| HTTP semantics | Use correct status codes |
| Validation | Use FluentValidation in pipeline |
| Documentation | XML comments for Swagger |

## Related Skills

- `skills/api/minimal-apis.md`
- `skills/api/api-versioning.md`
- `skills/error-handling/problem-details.md`
