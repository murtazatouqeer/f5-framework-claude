---
name: exception-handling
description: Global exception handling middleware for ASP.NET Core
applies_to: dotnet
type: skill
---

# Exception Handling

## Overview

Centralized exception handling ensures consistent error responses and prevents sensitive information leakage. This guide covers implementing global exception handling middleware.

## Exception Middleware

```csharp
// Middleware/ExceptionHandlingMiddleware.cs
public class ExceptionHandlingMiddleware
{
    private readonly RequestDelegate _next;
    private readonly ILogger<ExceptionHandlingMiddleware> _logger;
    private readonly IHostEnvironment _environment;

    public ExceptionHandlingMiddleware(
        RequestDelegate next,
        ILogger<ExceptionHandlingMiddleware> logger,
        IHostEnvironment environment)
    {
        _next = next;
        _logger = logger;
        _environment = environment;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        try
        {
            await _next(context);
        }
        catch (Exception exception)
        {
            await HandleExceptionAsync(context, exception);
        }
    }

    private async Task HandleExceptionAsync(
        HttpContext context,
        Exception exception)
    {
        _logger.LogError(exception, "An unhandled exception occurred");

        var (statusCode, problemDetails) = exception switch
        {
            ValidationException ve => (
                StatusCodes.Status422UnprocessableEntity,
                CreateValidationProblemDetails(ve)),

            NotFoundException nfe => (
                StatusCodes.Status404NotFound,
                CreateProblemDetails(
                    StatusCodes.Status404NotFound,
                    "Not Found",
                    nfe.Message)),

            ConflictException ce => (
                StatusCodes.Status409Conflict,
                CreateProblemDetails(
                    StatusCodes.Status409Conflict,
                    "Conflict",
                    ce.Message)),

            UnauthorizedException => (
                StatusCodes.Status401Unauthorized,
                CreateProblemDetails(
                    StatusCodes.Status401Unauthorized,
                    "Unauthorized",
                    "Authentication is required")),

            ForbiddenException fe => (
                StatusCodes.Status403Forbidden,
                CreateProblemDetails(
                    StatusCodes.Status403Forbidden,
                    "Forbidden",
                    fe.Message)),

            BadRequestException bre => (
                StatusCodes.Status400BadRequest,
                CreateProblemDetails(
                    StatusCodes.Status400BadRequest,
                    "Bad Request",
                    bre.Message)),

            _ => (
                StatusCodes.Status500InternalServerError,
                CreateProblemDetails(
                    StatusCodes.Status500InternalServerError,
                    "Internal Server Error",
                    _environment.IsDevelopment()
                        ? exception.Message
                        : "An unexpected error occurred"))
        };

        // Add trace ID for correlation
        problemDetails.Extensions["traceId"] = context.TraceIdentifier;

        // Add stack trace in development
        if (_environment.IsDevelopment() && statusCode == 500)
        {
            problemDetails.Extensions["stackTrace"] = exception.StackTrace;
        }

        context.Response.StatusCode = statusCode;
        context.Response.ContentType = "application/problem+json";

        await context.Response.WriteAsJsonAsync(problemDetails);
    }

    private static ProblemDetails CreateProblemDetails(
        int status,
        string title,
        string detail)
    {
        return new ProblemDetails
        {
            Status = status,
            Title = title,
            Detail = detail,
            Type = $"https://httpstatuses.com/{status}"
        };
    }

    private static ValidationProblemDetails CreateValidationProblemDetails(
        ValidationException exception)
    {
        var errors = exception.Errors
            .GroupBy(e => e.PropertyName)
            .ToDictionary(
                g => g.Key,
                g => g.Select(e => e.ErrorMessage).ToArray());

        return new ValidationProblemDetails(errors)
        {
            Status = StatusCodes.Status422UnprocessableEntity,
            Title = "Validation Failed",
            Detail = "One or more validation errors occurred",
            Type = "https://httpstatuses.com/422"
        };
    }
}

// Extension method
public static class ExceptionHandlingMiddlewareExtensions
{
    public static IApplicationBuilder UseExceptionHandling(
        this IApplicationBuilder app)
    {
        return app.UseMiddleware<ExceptionHandlingMiddleware>();
    }
}

// Program.cs
app.UseExceptionHandling();
```

## Custom Exceptions

```csharp
// Domain/Exceptions/DomainException.cs
public abstract class DomainException : Exception
{
    protected DomainException(string message) : base(message) { }
    protected DomainException(string message, Exception inner)
        : base(message, inner) { }
}

// Not Found
public class NotFoundException : DomainException
{
    public NotFoundException(string message) : base(message) { }

    public NotFoundException(string entityName, object key)
        : base($"{entityName} with key '{key}' was not found") { }
}

// Conflict
public class ConflictException : DomainException
{
    public ConflictException(string message) : base(message) { }
}

// Unauthorized
public class UnauthorizedException : DomainException
{
    public UnauthorizedException() : base("Unauthorized") { }
    public UnauthorizedException(string message) : base(message) { }
}

// Forbidden
public class ForbiddenException : DomainException
{
    public ForbiddenException() : base("Access denied") { }
    public ForbiddenException(string message) : base(message) { }
}

// Bad Request
public class BadRequestException : DomainException
{
    public BadRequestException(string message) : base(message) { }
}

// Validation Exception (extends FluentValidation)
public class ValidationException : DomainException
{
    public IEnumerable<ValidationFailure> Errors { get; }

    public ValidationException(IEnumerable<ValidationFailure> errors)
        : base("One or more validation errors occurred")
    {
        Errors = errors;
    }
}
```

## Using Exceptions in Services

```csharp
// Application/Services/ProductService.cs
public class ProductService : IProductService
{
    private readonly IProductRepository _repository;

    public async Task<ProductDto> GetByIdAsync(
        Guid id,
        CancellationToken ct)
    {
        var product = await _repository.GetByIdAsync(id, ct);

        if (product is null)
            throw new NotFoundException(nameof(Product), id);

        return _mapper.Map<ProductDto>(product);
    }

    public async Task<ProductDto> UpdateAsync(
        Guid id,
        UpdateProductDto dto,
        CancellationToken ct)
    {
        var product = await _repository.GetByIdAsync(id, ct);

        if (product is null)
            throw new NotFoundException(nameof(Product), id);

        // Check for duplicate SKU
        if (!string.IsNullOrEmpty(dto.Sku))
        {
            var existing = await _repository.GetBySkuAsync(dto.Sku, ct);
            if (existing is not null && existing.Id != id)
                throw new ConflictException($"SKU '{dto.Sku}' already exists");
        }

        // Update and return
        _mapper.Map(dto, product);
        await _unitOfWork.SaveChangesAsync(ct);

        return _mapper.Map<ProductDto>(product);
    }
}
```

## Exception Filter (Alternative)

```csharp
// Filters/ApiExceptionFilterAttribute.cs
public class ApiExceptionFilterAttribute : ExceptionFilterAttribute
{
    private readonly ILogger<ApiExceptionFilterAttribute> _logger;
    private readonly IHostEnvironment _env;

    public ApiExceptionFilterAttribute(
        ILogger<ApiExceptionFilterAttribute> logger,
        IHostEnvironment env)
    {
        _logger = logger;
        _env = env;
    }

    public override void OnException(ExceptionContext context)
    {
        _logger.LogError(context.Exception, "Unhandled exception");

        var problemDetails = context.Exception switch
        {
            NotFoundException nfe => new ProblemDetails
            {
                Status = 404,
                Title = "Not Found",
                Detail = nfe.Message
            },
            // ... other exception types
            _ => new ProblemDetails
            {
                Status = 500,
                Title = "Internal Server Error",
                Detail = _env.IsDevelopment()
                    ? context.Exception.Message
                    : "An unexpected error occurred"
            }
        };

        context.Result = new ObjectResult(problemDetails)
        {
            StatusCode = problemDetails.Status
        };

        context.ExceptionHandled = true;
    }
}

// Registration
builder.Services.AddControllers(options =>
{
    options.Filters.Add<ApiExceptionFilterAttribute>();
});
```

## Best Practices

| Practice | Recommendation |
|----------|----------------|
| Logging | Log all exceptions with context |
| Information hiding | Hide details in production |
| Trace ID | Include for correlation |
| Consistent format | Use Problem Details |
| Custom exceptions | Create domain-specific types |
| HTTP semantics | Map to correct status codes |

## Related Skills

- `skills/error-handling/problem-details.md`
- `skills/validation/fluent-validation.md`
