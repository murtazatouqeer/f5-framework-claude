---
name: clean-architecture
description: Clean Architecture layer separation and dependency rules for ASP.NET Core
applies_to: dotnet
type: skill
---

# Clean Architecture for ASP.NET Core

## Overview

Clean Architecture separates concerns into concentric layers with the Domain at the center. Dependencies point inward, and the outer layers depend on the inner layers, never the reverse.

## Layer Structure

```
┌─────────────────────────────────────────────────┐
│                  Presentation                    │
│            (API, Controllers, Views)            │
├─────────────────────────────────────────────────┤
│                 Infrastructure                   │
│      (EF Core, External Services, Identity)     │
├─────────────────────────────────────────────────┤
│                  Application                     │
│        (Use Cases, DTOs, Interfaces)            │
├─────────────────────────────────────────────────┤
│                    Domain                        │
│     (Entities, Value Objects, Domain Events)    │
└─────────────────────────────────────────────────┘
```

## Project Organization

```
Solution/
├── src/
│   ├── MyApp.Domain/                    # Core business logic
│   │   ├── Common/
│   │   │   ├── BaseEntity.cs
│   │   │   ├── AuditableEntity.cs
│   │   │   └── DomainEvent.cs
│   │   ├── Entities/
│   │   │   ├── Product.cs
│   │   │   └── Category.cs
│   │   ├── ValueObjects/
│   │   │   ├── Money.cs
│   │   │   └── Address.cs
│   │   ├── Interfaces/
│   │   │   └── IProductRepository.cs
│   │   └── Events/
│   │       └── ProductCreatedEvent.cs
│   │
│   ├── MyApp.Application/               # Use cases
│   │   ├── Common/
│   │   │   ├── Behaviors/
│   │   │   │   ├── ValidationBehavior.cs
│   │   │   │   └── LoggingBehavior.cs
│   │   │   ├── Interfaces/
│   │   │   │   └── IApplicationDbContext.cs
│   │   │   └── Mappings/
│   │   │       └── MappingProfile.cs
│   │   ├── Products/
│   │   │   ├── Commands/
│   │   │   │   └── CreateProduct/
│   │   │   │       ├── CreateProductCommand.cs
│   │   │   │       ├── CreateProductCommandHandler.cs
│   │   │   │       └── CreateProductCommandValidator.cs
│   │   │   └── Queries/
│   │   │       └── GetProducts/
│   │   │           ├── GetProductsQuery.cs
│   │   │           └── GetProductsQueryHandler.cs
│   │   ├── DTOs/
│   │   │   └── ProductDto.cs
│   │   └── DependencyInjection.cs
│   │
│   ├── MyApp.Infrastructure/            # External concerns
│   │   ├── Persistence/
│   │   │   ├── AppDbContext.cs
│   │   │   ├── Configurations/
│   │   │   │   └── ProductConfiguration.cs
│   │   │   └── Repositories/
│   │   │       └── ProductRepository.cs
│   │   ├── Services/
│   │   │   └── EmailService.cs
│   │   ├── Identity/
│   │   │   └── IdentityService.cs
│   │   └── DependencyInjection.cs
│   │
│   └── MyApp.API/                       # Presentation
│       ├── Controllers/
│       │   └── ProductsController.cs
│       ├── Middleware/
│       │   └── ExceptionHandlingMiddleware.cs
│       ├── Filters/
│       │   └── ApiExceptionFilterAttribute.cs
│       └── Program.cs
│
└── tests/
    ├── MyApp.Domain.Tests/
    ├── MyApp.Application.Tests/
    └── MyApp.API.Tests/
```

## Dependency Rules

### ❌ NEVER DO

```csharp
// Domain layer referencing Infrastructure
using Microsoft.EntityFrameworkCore; // ❌ Wrong!

public class Product
{
    public DbSet<Product> Products { get; } // ❌ EF in Domain!
}
```

### ✅ ALWAYS DO

```csharp
// Domain defines interfaces, Infrastructure implements
// Domain/Interfaces/IProductRepository.cs
public interface IProductRepository
{
    Task<Product?> GetByIdAsync(Guid id, CancellationToken ct);
    Task AddAsync(Product product, CancellationToken ct);
}

// Infrastructure/Repositories/ProductRepository.cs
public class ProductRepository : IProductRepository
{
    private readonly AppDbContext _context;
    // Implementation with EF Core
}
```

## Layer Responsibilities

### Domain Layer

- **Entities**: Business objects with identity
- **Value Objects**: Immutable objects without identity
- **Domain Events**: Events raised by domain objects
- **Repository Interfaces**: Contracts for data access
- **Domain Services**: Business logic spanning multiple entities

```csharp
// Domain/Entities/Product.cs
public class Product : BaseEntity
{
    public string Name { get; private set; }
    public Money Price { get; private set; }

    private Product() { } // EF Core

    public static Product Create(string name, Money price)
    {
        var product = new Product
        {
            Id = Guid.NewGuid(),
            Name = name,
            Price = price
        };

        product.AddDomainEvent(new ProductCreatedEvent(product.Id));
        return product;
    }

    public void UpdatePrice(Money newPrice)
    {
        if (newPrice.Amount <= 0)
            throw new DomainException("Price must be positive");

        Price = newPrice;
        AddDomainEvent(new ProductPriceUpdatedEvent(Id, newPrice));
    }
}
```

### Application Layer

- **Commands/Queries**: CQRS operations
- **Handlers**: Use case implementations
- **DTOs**: Data transfer objects
- **Validators**: Input validation
- **Interfaces**: Contracts for external services

```csharp
// Application/Products/Commands/CreateProduct/CreateProductCommand.cs
public record CreateProductCommand(
    string Name,
    decimal Price,
    string Currency
) : IRequest<ProductDto>;

// Application/Products/Commands/CreateProduct/CreateProductCommandHandler.cs
public class CreateProductCommandHandler
    : IRequestHandler<CreateProductCommand, ProductDto>
{
    private readonly IProductRepository _repository;
    private readonly IUnitOfWork _unitOfWork;
    private readonly IMapper _mapper;

    public async Task<ProductDto> Handle(
        CreateProductCommand request,
        CancellationToken cancellationToken)
    {
        var price = new Money(request.Price, request.Currency);
        var product = Product.Create(request.Name, price);

        await _repository.AddAsync(product, cancellationToken);
        await _unitOfWork.SaveChangesAsync(cancellationToken);

        return _mapper.Map<ProductDto>(product);
    }
}
```

### Infrastructure Layer

- **DbContext**: EF Core database context
- **Repositories**: Data access implementations
- **External Services**: Email, storage, etc.
- **Identity**: Authentication/authorization

```csharp
// Infrastructure/Persistence/AppDbContext.cs
public class AppDbContext : DbContext, IApplicationDbContext
{
    public DbSet<Product> Products => Set<Product>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.ApplyConfigurationsFromAssembly(
            typeof(AppDbContext).Assembly);
    }
}
```

### Presentation Layer

- **Controllers**: API endpoints
- **Middleware**: Cross-cutting concerns
- **Filters**: Exception handling
- **View Models**: API response models

```csharp
// API/Controllers/ProductsController.cs
[ApiController]
[Route("api/[controller]")]
public class ProductsController : ControllerBase
{
    private readonly IMediator _mediator;

    [HttpPost]
    public async Task<ActionResult<ProductDto>> Create(
        [FromBody] CreateProductCommand command)
    {
        var result = await _mediator.Send(command);
        return CreatedAtAction(
            nameof(GetById),
            new { id = result.Id },
            result);
    }
}
```

## Best Practices

### 1. Keep Domain Pure

```csharp
// ✅ No framework dependencies
public class Product
{
    // Pure C# only
}
```

### 2. Use Dependency Injection

```csharp
// Infrastructure/DependencyInjection.cs
public static class DependencyInjection
{
    public static IServiceCollection AddInfrastructure(
        this IServiceCollection services,
        IConfiguration configuration)
    {
        services.AddDbContext<AppDbContext>(options =>
            options.UseSqlServer(
                configuration.GetConnectionString("Default")));

        services.AddScoped<IProductRepository, ProductRepository>();
        services.AddScoped<IUnitOfWork>(sp =>
            sp.GetRequiredService<AppDbContext>());

        return services;
    }
}
```

### 3. Register in Correct Order

```csharp
// Program.cs
builder.Services.AddApplication();
builder.Services.AddInfrastructure(builder.Configuration);
```

## Related Skills

- `skills/architecture/vertical-slices.md`
- `skills/database/repository-pattern.md`
