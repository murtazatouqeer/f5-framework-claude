---
name: minimal-apis
description: Minimal API endpoints in ASP.NET Core
applies_to: dotnet
type: skill
---

# Minimal APIs

## Overview

Minimal APIs provide a lightweight way to build HTTP APIs with minimal dependencies. Introduced in .NET 6, they offer a simpler alternative to controllers for smaller APIs or microservices.

## Basic Setup

```csharp
// Program.cs
var builder = WebApplication.CreateBuilder(args);

// Add services
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

var app = builder.Build();

// Configure pipeline
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();
app.UseAuthorization();

// Map endpoints
app.MapGet("/", () => "Hello World!");

app.Run();
```

## Endpoint Patterns

### Basic CRUD

```csharp
// Simple endpoints
app.MapGet("/api/products", GetProducts);
app.MapGet("/api/products/{id:guid}", GetProductById);
app.MapPost("/api/products", CreateProduct);
app.MapPut("/api/products/{id:guid}", UpdateProduct);
app.MapDelete("/api/products/{id:guid}", DeleteProduct);

// Handler methods
static async Task<IResult> GetProducts(
    IProductService service,
    CancellationToken ct)
{
    var products = await service.GetAllAsync(ct);
    return Results.Ok(products);
}

static async Task<IResult> GetProductById(
    Guid id,
    IProductService service,
    CancellationToken ct)
{
    var product = await service.GetByIdAsync(id, ct);
    return product is null
        ? Results.NotFound()
        : Results.Ok(product);
}

static async Task<IResult> CreateProduct(
    CreateProductDto dto,
    IProductService service,
    CancellationToken ct)
{
    var product = await service.CreateAsync(dto, ct);
    return Results.Created($"/api/products/{product.Id}", product);
}

static async Task<IResult> UpdateProduct(
    Guid id,
    UpdateProductDto dto,
    IProductService service,
    CancellationToken ct)
{
    var product = await service.UpdateAsync(id, dto, ct);
    return product is null
        ? Results.NotFound()
        : Results.Ok(product);
}

static async Task<IResult> DeleteProduct(
    Guid id,
    IProductService service,
    CancellationToken ct)
{
    var success = await service.DeleteAsync(id, ct);
    return success
        ? Results.NoContent()
        : Results.NotFound();
}
```

### Route Groups

```csharp
// Organize endpoints in groups
var products = app.MapGroup("/api/products")
    .WithTags("Products")
    .RequireAuthorization();

products.MapGet("/", GetProducts);
products.MapGet("/{id:guid}", GetProductById);
products.MapPost("/", CreateProduct);
products.MapPut("/{id:guid}", UpdateProduct);
products.MapDelete("/{id:guid}", DeleteProduct);

// Nested groups
var categories = app.MapGroup("/api/categories")
    .WithTags("Categories");

var categoryProducts = categories.MapGroup("/{categoryId:guid}/products");
categoryProducts.MapGet("/", GetProductsByCategory);
```

## Parameter Binding

### Automatic Binding

```csharp
// Route parameters
app.MapGet("/api/products/{id:guid}", (Guid id) => $"Product {id}");

// Query parameters
app.MapGet("/api/products", (string? search, int page = 1, int size = 10) =>
    $"Search: {search}, Page: {page}, Size: {size}");

// Body binding
app.MapPost("/api/products", (CreateProductDto dto) => Results.Ok(dto));

// Header binding
app.MapGet("/api/test", ([FromHeader(Name = "X-Request-Id")] string? requestId) =>
    $"Request ID: {requestId}");
```

### Complex Binding

```csharp
// Bind from multiple sources
app.MapPut("/api/products/{id:guid}",
    async (
        [FromRoute] Guid id,
        [FromBody] UpdateProductDto dto,
        [FromQuery] bool notify,
        [FromServices] IProductService service,
        CancellationToken ct) =>
{
    if (id != dto.Id)
        return Results.BadRequest("ID mismatch");

    var result = await service.UpdateAsync(id, dto, ct);
    return result is null ? Results.NotFound() : Results.Ok(result);
});
```

### Validation with Filters

```csharp
// Validation filter
public class ValidationFilter<T> : IEndpointFilter
{
    public async ValueTask<object?> InvokeAsync(
        EndpointFilterInvocationContext context,
        EndpointFilterDelegate next)
    {
        var validator = context.HttpContext.RequestServices
            .GetService<IValidator<T>>();

        if (validator is null)
            return await next(context);

        var argument = context.Arguments
            .OfType<T>()
            .FirstOrDefault();

        if (argument is null)
            return await next(context);

        var result = await validator.ValidateAsync(argument);

        if (!result.IsValid)
            return Results.ValidationProblem(result.ToDictionary());

        return await next(context);
    }
}

// Apply filter
app.MapPost("/api/products", CreateProduct)
    .AddEndpointFilter<ValidationFilter<CreateProductDto>>();
```

## OpenAPI/Swagger

### Endpoint Metadata

```csharp
app.MapGet("/api/products/{id:guid}", GetProductById)
    .WithName("GetProductById")
    .WithTags("Products")
    .WithDescription("Get a product by its ID")
    .WithOpenApi(operation =>
    {
        operation.Summary = "Get Product";
        operation.Parameters[0].Description = "The product ID";
        return operation;
    })
    .Produces<ProductDto>(StatusCodes.Status200OK)
    .Produces(StatusCodes.Status404NotFound);

app.MapPost("/api/products", CreateProduct)
    .WithName("CreateProduct")
    .WithTags("Products")
    .Accepts<CreateProductDto>("application/json")
    .Produces<ProductDto>(StatusCodes.Status201Created)
    .ProducesValidationProblem()
    .RequireAuthorization("ProductWrite");
```

## Modular Organization

### Extension Methods

```csharp
// Features/Products/ProductEndpoints.cs
public static class ProductEndpoints
{
    public static void MapProductEndpoints(this IEndpointRouteBuilder app)
    {
        var group = app.MapGroup("/api/products")
            .WithTags("Products");

        group.MapGet("/", GetProducts)
            .WithName("GetProducts")
            .Produces<IEnumerable<ProductDto>>();

        group.MapGet("/{id:guid}", GetProductById)
            .WithName("GetProductById")
            .Produces<ProductDto>()
            .Produces(StatusCodes.Status404NotFound);

        group.MapPost("/", CreateProduct)
            .WithName("CreateProduct")
            .Produces<ProductDto>(StatusCodes.Status201Created)
            .ProducesValidationProblem()
            .RequireAuthorization();

        group.MapPut("/{id:guid}", UpdateProduct)
            .WithName("UpdateProduct")
            .Produces<ProductDto>()
            .Produces(StatusCodes.Status404NotFound)
            .RequireAuthorization();

        group.MapDelete("/{id:guid}", DeleteProduct)
            .WithName("DeleteProduct")
            .Produces(StatusCodes.Status204NoContent)
            .Produces(StatusCodes.Status404NotFound)
            .RequireAuthorization();
    }

    private static async Task<IResult> GetProducts(
        [AsParameters] GetProductsQuery query,
        IMediator mediator,
        CancellationToken ct)
    {
        var result = await mediator.Send(query, ct);
        return Results.Ok(result);
    }

    // ... other handlers
}

// Program.cs
app.MapProductEndpoints();
app.MapCategoryEndpoints();
app.MapOrderEndpoints();
```

### Carter Integration

```csharp
// Using Carter for structured minimal APIs
// Install-Package Carter

public class ProductsModule : ICarterModule
{
    public void AddRoutes(IEndpointRouteBuilder app)
    {
        app.MapGet("/api/products", async (
            IProductService service,
            CancellationToken ct) =>
        {
            var products = await service.GetAllAsync(ct);
            return Results.Ok(products);
        })
        .WithName("GetProducts")
        .WithTags("Products");
    }
}

// Program.cs
builder.Services.AddCarter();
// ...
app.MapCarter();
```

## With MediatR

```csharp
// Endpoint with MediatR
app.MapPost("/api/products", async (
    CreateProductCommand command,
    IMediator mediator,
    CancellationToken ct) =>
{
    var result = await mediator.Send(command, ct);
    return Results.Created($"/api/products/{result.Id}", result);
})
.WithName("CreateProduct")
.WithTags("Products")
.Produces<ProductDto>(StatusCodes.Status201Created)
.ProducesValidationProblem();
```

## Error Handling

```csharp
// Global error handler
app.UseExceptionHandler(exceptionApp =>
{
    exceptionApp.Run(async context =>
    {
        var exception = context.Features.Get<IExceptionHandlerFeature>()?.Error;

        var problem = exception switch
        {
            NotFoundException => new ProblemDetails
            {
                Status = StatusCodes.Status404NotFound,
                Title = "Not Found",
                Detail = exception.Message
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
                Title = "Internal Server Error"
            }
        };

        context.Response.StatusCode = problem.Status ?? 500;
        await context.Response.WriteAsJsonAsync(problem);
    });
});
```

## When to Use

| Scenario | Recommendation |
|----------|----------------|
| Small APIs | ✅ Minimal APIs |
| Microservices | ✅ Minimal APIs |
| Simple CRUD | ✅ Minimal APIs |
| Complex validation | ⚠️ Controllers may be cleaner |
| Large applications | ⚠️ Controllers with MediatR |
| Team familiarity | Consider experience |

## Related Skills

- `skills/api/controller-patterns.md`
- `skills/architecture/vertical-slices.md`
