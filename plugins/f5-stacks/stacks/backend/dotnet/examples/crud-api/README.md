# CRUD API Example

Complete CRUD API implementation using Clean Architecture with ASP.NET Core.

## Project Structure

```
CrudApi/
├── src/
│   ├── CrudApi.Domain/
│   │   ├── Common/
│   │   │   ├── BaseEntity.cs
│   │   │   └── AuditableEntity.cs
│   │   ├── Entities/
│   │   │   ├── Product.cs
│   │   │   └── Category.cs
│   │   └── Interfaces/
│   │       ├── IRepository.cs
│   │       ├── IProductRepository.cs
│   │       └── IUnitOfWork.cs
│   │
│   ├── CrudApi.Application/
│   │   ├── Common/
│   │   │   ├── Behaviors/
│   │   │   │   ├── ValidationBehavior.cs
│   │   │   │   └── LoggingBehavior.cs
│   │   │   └── Mappings/
│   │   │       └── MappingProfile.cs
│   │   ├── DTOs/
│   │   │   ├── ProductDto.cs
│   │   │   ├── CreateProductDto.cs
│   │   │   └── UpdateProductDto.cs
│   │   ├── Products/
│   │   │   ├── Commands/
│   │   │   │   ├── CreateProduct/
│   │   │   │   ├── UpdateProduct/
│   │   │   │   └── DeleteProduct/
│   │   │   └── Queries/
│   │   │       ├── GetProductById/
│   │   │       └── GetProducts/
│   │   └── DependencyInjection.cs
│   │
│   ├── CrudApi.Infrastructure/
│   │   ├── Persistence/
│   │   │   ├── AppDbContext.cs
│   │   │   ├── Configurations/
│   │   │   │   ├── ProductConfiguration.cs
│   │   │   │   └── CategoryConfiguration.cs
│   │   │   └── Repositories/
│   │   │       ├── Repository.cs
│   │   │       └── ProductRepository.cs
│   │   └── DependencyInjection.cs
│   │
│   └── CrudApi.API/
│       ├── Controllers/
│       │   └── ProductsController.cs
│       ├── Middleware/
│       │   └── ExceptionHandlingMiddleware.cs
│       └── Program.cs
│
└── tests/
    ├── CrudApi.Tests.Unit/
    │   └── Products/
    │       └── CreateProductCommandTests.cs
    └── CrudApi.Tests.Integration/
        └── Controllers/
            └── ProductsControllerTests.cs
```

## Implementation

### 1. Domain Layer

```csharp
// Domain/Common/BaseEntity.cs
namespace CrudApi.Domain.Common;

public abstract class BaseEntity
{
    public Guid Id { get; protected set; } = Guid.NewGuid();
}

// Domain/Common/AuditableEntity.cs
public abstract class AuditableEntity : BaseEntity
{
    public DateTime CreatedAt { get; set; }
    public string? CreatedBy { get; set; }
    public DateTime? UpdatedAt { get; set; }
    public string? UpdatedBy { get; set; }
}

// Domain/Entities/Product.cs
namespace CrudApi.Domain.Entities;

public class Product : AuditableEntity
{
    public string Name { get; private set; } = string.Empty;
    public string? Description { get; private set; }
    public decimal Price { get; private set; }
    public int Stock { get; private set; }
    public bool IsActive { get; private set; } = true;

    public Guid CategoryId { get; private set; }
    public Category Category { get; private set; } = null!;

    private Product() { } // EF Core

    public static Product Create(
        string name,
        string? description,
        decimal price,
        Guid categoryId)
    {
        if (string.IsNullOrWhiteSpace(name))
            throw new ArgumentException("Name is required", nameof(name));

        if (price < 0)
            throw new ArgumentException("Price cannot be negative", nameof(price));

        return new Product
        {
            Name = name,
            Description = description,
            Price = price,
            CategoryId = categoryId
        };
    }

    public void Update(string? name, string? description, decimal? price)
    {
        if (name is not null) Name = name;
        if (description is not null) Description = description;
        if (price.HasValue) Price = price.Value;
    }

    public void UpdateStock(int quantity)
    {
        if (Stock + quantity < 0)
            throw new InvalidOperationException("Insufficient stock");

        Stock += quantity;
    }

    public void Activate() => IsActive = true;
    public void Deactivate() => IsActive = false;
}
```

### 2. Application Layer

```csharp
// Application/Products/Commands/CreateProduct/CreateProductCommand.cs
using MediatR;

namespace CrudApi.Application.Products.Commands.CreateProduct;

public record CreateProductCommand(
    string Name,
    string? Description,
    decimal Price,
    Guid CategoryId
) : IRequest<ProductDto>;

// CreateProductCommandHandler.cs
public class CreateProductCommandHandler
    : IRequestHandler<CreateProductCommand, ProductDto>
{
    private readonly IProductRepository _repository;
    private readonly IUnitOfWork _unitOfWork;
    private readonly IMapper _mapper;

    public CreateProductCommandHandler(
        IProductRepository repository,
        IUnitOfWork unitOfWork,
        IMapper mapper)
    {
        _repository = repository;
        _unitOfWork = unitOfWork;
        _mapper = mapper;
    }

    public async Task<ProductDto> Handle(
        CreateProductCommand request,
        CancellationToken cancellationToken)
    {
        var product = Product.Create(
            request.Name,
            request.Description,
            request.Price,
            request.CategoryId);

        await _repository.AddAsync(product, cancellationToken);
        await _unitOfWork.SaveChangesAsync(cancellationToken);

        return _mapper.Map<ProductDto>(product);
    }
}

// CreateProductCommandValidator.cs
using FluentValidation;

public class CreateProductCommandValidator
    : AbstractValidator<CreateProductCommand>
{
    public CreateProductCommandValidator()
    {
        RuleFor(x => x.Name)
            .NotEmpty()
            .MaximumLength(200);

        RuleFor(x => x.Description)
            .MaximumLength(1000);

        RuleFor(x => x.Price)
            .GreaterThan(0);

        RuleFor(x => x.CategoryId)
            .NotEmpty();
    }
}
```

### 3. Infrastructure Layer

```csharp
// Infrastructure/Persistence/AppDbContext.cs
using Microsoft.EntityFrameworkCore;

namespace CrudApi.Infrastructure.Persistence;

public class AppDbContext : DbContext
{
    public AppDbContext(DbContextOptions<AppDbContext> options)
        : base(options) { }

    public DbSet<Product> Products => Set<Product>();
    public DbSet<Category> Categories => Set<Category>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.ApplyConfigurationsFromAssembly(
            typeof(AppDbContext).Assembly);
    }

    public override async Task<int> SaveChangesAsync(
        CancellationToken cancellationToken = default)
    {
        foreach (var entry in ChangeTracker.Entries<AuditableEntity>())
        {
            switch (entry.State)
            {
                case EntityState.Added:
                    entry.Entity.CreatedAt = DateTime.UtcNow;
                    break;
                case EntityState.Modified:
                    entry.Entity.UpdatedAt = DateTime.UtcNow;
                    break;
            }
        }

        return await base.SaveChangesAsync(cancellationToken);
    }
}

// Infrastructure/Persistence/Repositories/ProductRepository.cs
public class ProductRepository : Repository<Product>, IProductRepository
{
    public ProductRepository(AppDbContext context) : base(context) { }

    public async Task<Product?> GetByIdWithCategoryAsync(
        Guid id,
        CancellationToken cancellationToken = default)
    {
        return await _dbSet
            .Include(p => p.Category)
            .FirstOrDefaultAsync(p => p.Id == id, cancellationToken);
    }

    public async Task<IEnumerable<Product>> GetByCategoryAsync(
        Guid categoryId,
        CancellationToken cancellationToken = default)
    {
        return await _dbSet
            .Where(p => p.CategoryId == categoryId)
            .Include(p => p.Category)
            .ToListAsync(cancellationToken);
    }
}
```

### 4. API Layer

```csharp
// API/Controllers/ProductsController.cs
using MediatR;
using Microsoft.AspNetCore.Mvc;

namespace CrudApi.API.Controllers;

[ApiController]
[Route("api/[controller]")]
[Produces("application/json")]
public class ProductsController : ControllerBase
{
    private readonly IMediator _mediator;

    public ProductsController(IMediator mediator)
    {
        _mediator = mediator;
    }

    /// <summary>
    /// Get all products with optional filtering
    /// </summary>
    [HttpGet]
    [ProducesResponseType(typeof(PaginatedList<ProductDto>), 200)]
    public async Task<ActionResult<PaginatedList<ProductDto>>> GetAll(
        [FromQuery] GetProductsQuery query,
        CancellationToken cancellationToken)
    {
        return Ok(await _mediator.Send(query, cancellationToken));
    }

    /// <summary>
    /// Get a product by ID
    /// </summary>
    [HttpGet("{id:guid}")]
    [ProducesResponseType(typeof(ProductDto), 200)]
    [ProducesResponseType(404)]
    public async Task<ActionResult<ProductDto>> GetById(
        Guid id,
        CancellationToken cancellationToken)
    {
        var result = await _mediator.Send(
            new GetProductByIdQuery(id),
            cancellationToken);

        return result is null ? NotFound() : Ok(result);
    }

    /// <summary>
    /// Create a new product
    /// </summary>
    [HttpPost]
    [ProducesResponseType(typeof(ProductDto), 201)]
    [ProducesResponseType(typeof(ValidationProblemDetails), 400)]
    public async Task<ActionResult<ProductDto>> Create(
        CreateProductCommand command,
        CancellationToken cancellationToken)
    {
        var result = await _mediator.Send(command, cancellationToken);
        return CreatedAtAction(nameof(GetById), new { id = result.Id }, result);
    }

    /// <summary>
    /// Update an existing product
    /// </summary>
    [HttpPut("{id:guid}")]
    [ProducesResponseType(typeof(ProductDto), 200)]
    [ProducesResponseType(404)]
    public async Task<ActionResult<ProductDto>> Update(
        Guid id,
        UpdateProductCommand command,
        CancellationToken cancellationToken)
    {
        if (id != command.Id)
            return BadRequest();

        var result = await _mediator.Send(command, cancellationToken);
        return result is null ? NotFound() : Ok(result);
    }

    /// <summary>
    /// Delete a product
    /// </summary>
    [HttpDelete("{id:guid}")]
    [ProducesResponseType(204)]
    [ProducesResponseType(404)]
    public async Task<IActionResult> Delete(
        Guid id,
        CancellationToken cancellationToken)
    {
        var result = await _mediator.Send(
            new DeleteProductCommand(id),
            cancellationToken);

        return result ? NoContent() : NotFound();
    }
}
```

### 5. Program.cs Setup

```csharp
using CrudApi.Application;
using CrudApi.Infrastructure;

var builder = WebApplication.CreateBuilder(args);

// Add services
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// Add Clean Architecture layers
builder.Services.AddApplication();
builder.Services.AddInfrastructure(builder.Configuration);

var app = builder.Build();

// Configure middleware
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();
app.UseAuthorization();
app.MapControllers();

app.Run();
```

## Running the Example

```bash
# Create solution
dotnet new sln -n CrudApi

# Create projects
dotnet new classlib -n CrudApi.Domain -o src/CrudApi.Domain
dotnet new classlib -n CrudApi.Application -o src/CrudApi.Application
dotnet new classlib -n CrudApi.Infrastructure -o src/CrudApi.Infrastructure
dotnet new webapi -n CrudApi.API -o src/CrudApi.API

# Add projects to solution
dotnet sln add src/CrudApi.Domain
dotnet sln add src/CrudApi.Application
dotnet sln add src/CrudApi.Infrastructure
dotnet sln add src/CrudApi.API

# Add project references
dotnet add src/CrudApi.Application reference src/CrudApi.Domain
dotnet add src/CrudApi.Infrastructure reference src/CrudApi.Application
dotnet add src/CrudApi.API reference src/CrudApi.Infrastructure

# Add required packages
dotnet add src/CrudApi.Application package MediatR
dotnet add src/CrudApi.Application package AutoMapper
dotnet add src/CrudApi.Application package FluentValidation
dotnet add src/CrudApi.Infrastructure package Microsoft.EntityFrameworkCore.SqlServer

# Run the API
cd src/CrudApi.API
dotnet run
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/products` | Get all products |
| GET | `/api/products/{id}` | Get product by ID |
| POST | `/api/products` | Create new product |
| PUT | `/api/products/{id}` | Update product |
| DELETE | `/api/products/{id}` | Delete product |

## Related Skills

- `clean-architecture` - Architecture patterns
- `ef-core-patterns` - Database patterns
- `controller-patterns` - API controller patterns
- `fluent-validation` - Validation patterns
