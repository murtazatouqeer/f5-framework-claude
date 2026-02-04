---
name: vertical-slices
description: Feature-based code organization for ASP.NET Core
applies_to: dotnet
type: skill
---

# Vertical Slice Architecture

## Overview

Vertical Slice Architecture organizes code by feature rather than by layer. Each feature contains all the code needed to fulfill a use case, from API to database.

## Structure Comparison

### Horizontal Layers (Traditional)

```
Controllers/
    ProductsController.cs
    OrdersController.cs
Services/
    ProductService.cs
    OrderService.cs
Repositories/
    ProductRepository.cs
    OrderRepository.cs
```

### Vertical Slices (Feature-Based)

```
Features/
    Products/
        CreateProduct/
            CreateProductCommand.cs
            CreateProductHandler.cs
            CreateProductValidator.cs
            CreateProductEndpoint.cs
        GetProducts/
            GetProductsQuery.cs
            GetProductsHandler.cs
            GetProductsEndpoint.cs
    Orders/
        CreateOrder/
            ...
```

## Implementation Pattern

### Feature Folder Structure

```
src/
└── MyApp.API/
    └── Features/
        └── Products/
            ├── CreateProduct/
            │   ├── CreateProductCommand.cs
            │   ├── CreateProductHandler.cs
            │   ├── CreateProductValidator.cs
            │   └── CreateProductEndpoint.cs
            ├── GetProductById/
            │   ├── GetProductByIdQuery.cs
            │   ├── GetProductByIdHandler.cs
            │   └── GetProductByIdEndpoint.cs
            ├── UpdateProduct/
            │   └── ...
            ├── DeleteProduct/
            │   └── ...
            └── Shared/
                ├── ProductDto.cs
                └── ProductMappingProfile.cs
```

### Command Example

```csharp
// Features/Products/CreateProduct/CreateProductCommand.cs
namespace MyApp.API.Features.Products.CreateProduct;

public record CreateProductCommand(
    string Name,
    string Description,
    decimal Price,
    Guid CategoryId
);

// Features/Products/CreateProduct/CreateProductHandler.cs
public class CreateProductHandler
{
    private readonly AppDbContext _context;
    private readonly IMapper _mapper;

    public CreateProductHandler(AppDbContext context, IMapper mapper)
    {
        _context = context;
        _mapper = mapper;
    }

    public async Task<ProductDto> Handle(
        CreateProductCommand command,
        CancellationToken cancellationToken)
    {
        var product = new Product
        {
            Id = Guid.NewGuid(),
            Name = command.Name,
            Description = command.Description,
            Price = command.Price,
            CategoryId = command.CategoryId
        };

        _context.Products.Add(product);
        await _context.SaveChangesAsync(cancellationToken);

        return _mapper.Map<ProductDto>(product);
    }
}

// Features/Products/CreateProduct/CreateProductValidator.cs
public class CreateProductValidator
    : AbstractValidator<CreateProductCommand>
{
    public CreateProductValidator()
    {
        RuleFor(x => x.Name)
            .NotEmpty()
            .MaximumLength(200);

        RuleFor(x => x.Price)
            .GreaterThan(0);

        RuleFor(x => x.CategoryId)
            .NotEmpty();
    }
}
```

### Endpoint with Carter

```csharp
// Using Carter for endpoint registration
// Features/Products/CreateProduct/CreateProductEndpoint.cs
public class CreateProductEndpoint : ICarterModule
{
    public void AddRoutes(IEndpointRouteBuilder app)
    {
        app.MapPost("/api/products", async (
            CreateProductCommand command,
            CreateProductHandler handler,
            CancellationToken ct) =>
        {
            var result = await handler.Handle(command, ct);
            return Results.Created($"/api/products/{result.Id}", result);
        })
        .WithName("CreateProduct")
        .WithTags("Products")
        .Produces<ProductDto>(StatusCodes.Status201Created)
        .ProducesValidationProblem();
    }
}
```

### Endpoint with Minimal APIs

```csharp
// Features/Products/CreateProduct/CreateProductEndpoint.cs
public static class CreateProductEndpoint
{
    public static void MapCreateProduct(this IEndpointRouteBuilder app)
    {
        app.MapPost("/api/products", Handle)
            .WithName("CreateProduct")
            .WithTags("Products")
            .Produces<ProductDto>(StatusCodes.Status201Created)
            .ProducesValidationProblem();
    }

    private static async Task<IResult> Handle(
        CreateProductCommand command,
        CreateProductHandler handler,
        IValidator<CreateProductCommand> validator,
        CancellationToken ct)
    {
        var validation = await validator.ValidateAsync(command, ct);
        if (!validation.IsValid)
            return Results.ValidationProblem(validation.ToDictionary());

        var result = await handler.Handle(command, ct);
        return Results.Created($"/api/products/{result.Id}", result);
    }
}
```

## With MediatR

### Handler as MediatR Request

```csharp
// Features/Products/CreateProduct/CreateProductCommand.cs
public record CreateProductCommand(
    string Name,
    decimal Price
) : IRequest<ProductDto>;

public class CreateProductHandler
    : IRequestHandler<CreateProductCommand, ProductDto>
{
    private readonly AppDbContext _context;

    public async Task<ProductDto> Handle(
        CreateProductCommand request,
        CancellationToken cancellationToken)
    {
        // Implementation
    }
}

// Features/Products/CreateProduct/CreateProductEndpoint.cs
public static class CreateProductEndpoint
{
    public static void MapCreateProduct(this IEndpointRouteBuilder app)
    {
        app.MapPost("/api/products", async (
            CreateProductCommand command,
            IMediator mediator,
            CancellationToken ct) =>
        {
            var result = await mediator.Send(command, ct);
            return Results.Created($"/api/products/{result.Id}", result);
        });
    }
}
```

## Auto-Registration

### Using Reflection

```csharp
// Program.cs
var assembly = typeof(Program).Assembly;

// Register all handlers
builder.Services.Scan(scan => scan
    .FromAssemblies(assembly)
    .AddClasses(classes => classes.Where(t => t.Name.EndsWith("Handler")))
    .AsSelf()
    .WithScopedLifetime());

// Register all validators
builder.Services.AddValidatorsFromAssembly(assembly);

// Register all endpoints
app.MapEndpoints(assembly);

// Extension method
public static class EndpointExtensions
{
    public static void MapEndpoints(
        this IEndpointRouteBuilder app,
        Assembly assembly)
    {
        var endpointTypes = assembly.GetTypes()
            .Where(t => t.GetMethods()
                .Any(m => m.Name.StartsWith("Map") && m.IsStatic));

        foreach (var type in endpointTypes)
        {
            var method = type.GetMethods()
                .First(m => m.Name.StartsWith("Map") && m.IsStatic);
            method.Invoke(null, new object[] { app });
        }
    }
}
```

## Benefits

1. **High Cohesion**: All feature code in one place
2. **Easy Navigation**: Find everything for a feature in one folder
3. **Independent Changes**: Modify features without affecting others
4. **Simpler Testing**: Test complete features in isolation
5. **Reduced Coupling**: Features don't depend on each other

## When to Use

| Scenario | Recommendation |
|----------|----------------|
| Small to medium APIs | ✅ Excellent fit |
| CRUD-heavy applications | ✅ Excellent fit |
| Microservices | ✅ Natural fit |
| Complex domain logic | ⚠️ Consider Clean Architecture |
| Shared business rules | ⚠️ Need careful abstraction |

## Related Skills

- `skills/api/minimal-apis.md`
- `skills/architecture/clean-architecture.md`
