# MediatR and CQRS Pattern - ASP.NET Core

## Overview

CQRS (Command Query Responsibility Segregation) separates read and write operations. MediatR provides an in-process mediator implementation for .NET, enabling loose coupling between components.

## Installation

```bash
dotnet add package MediatR
```

## Project Structure

```
Application/
├── Features/
│   └── Products/
│       ├── Commands/
│       │   ├── CreateProduct/
│       │   │   ├── CreateProductCommand.cs
│       │   │   ├── CreateProductCommandHandler.cs
│       │   │   └── CreateProductCommandValidator.cs
│       │   ├── UpdateProduct/
│       │   └── DeleteProduct/
│       └── Queries/
│           ├── GetProductById/
│           │   ├── GetProductByIdQuery.cs
│           │   ├── GetProductByIdQueryHandler.cs
│           │   └── ProductDto.cs
│           └── GetProducts/
├── Common/
│   ├── Behaviors/
│   │   ├── ValidationBehavior.cs
│   │   ├── LoggingBehavior.cs
│   │   └── PerformanceBehavior.cs
│   └── Interfaces/
│       └── ICommand.cs
```

## Command Definition

```csharp
// Application/Features/Products/Commands/CreateProduct/CreateProductCommand.cs
public record CreateProductCommand(
    string Name,
    string Description,
    decimal Price,
    int CategoryId
) : IRequest<Result<ProductDto>>;

// With validation
public record UpdateProductCommand : IRequest<Result<ProductDto>>
{
    public Guid Id { get; init; }
    public string Name { get; init; } = string.Empty;
    public string Description { get; init; } = string.Empty;
    public decimal Price { get; init; }

    // Factory method for cleaner API
    public static UpdateProductCommand Create(Guid id, UpdateProductRequest request) =>
        new()
        {
            Id = id,
            Name = request.Name,
            Description = request.Description,
            Price = request.Price
        };
}
```

## Command Handler

```csharp
// Application/Features/Products/Commands/CreateProduct/CreateProductCommandHandler.cs
public class CreateProductCommandHandler
    : IRequestHandler<CreateProductCommand, Result<ProductDto>>
{
    private readonly IApplicationDbContext _context;
    private readonly IMapper _mapper;
    private readonly ILogger<CreateProductCommandHandler> _logger;

    public CreateProductCommandHandler(
        IApplicationDbContext context,
        IMapper mapper,
        ILogger<CreateProductCommandHandler> logger)
    {
        _context = context;
        _mapper = mapper;
        _logger = logger;
    }

    public async Task<Result<ProductDto>> Handle(
        CreateProductCommand request,
        CancellationToken cancellationToken)
    {
        // Check if category exists
        var categoryExists = await _context.Categories
            .AnyAsync(c => c.Id == request.CategoryId, cancellationToken);

        if (!categoryExists)
        {
            return Result<ProductDto>.NotFound($"Category {request.CategoryId} not found");
        }

        // Check for duplicate name
        var nameExists = await _context.Products
            .AnyAsync(p => p.Name == request.Name, cancellationToken);

        if (nameExists)
        {
            return Result<ProductDto>.Invalid("Product with this name already exists");
        }

        // Create entity
        var product = new Product
        {
            Name = request.Name,
            Description = request.Description,
            Price = request.Price,
            CategoryId = request.CategoryId,
            Status = ProductStatus.Active
        };

        _context.Products.Add(product);
        await _context.SaveChangesAsync(cancellationToken);

        _logger.LogInformation("Created product {ProductId}: {ProductName}",
            product.Id, product.Name);

        return Result<ProductDto>.Success(_mapper.Map<ProductDto>(product));
    }
}
```

## Query Definition

```csharp
// Application/Features/Products/Queries/GetProductById/GetProductByIdQuery.cs
public record GetProductByIdQuery(Guid Id) : IRequest<Result<ProductDto>>;

// Query with parameters
public record GetProductsQuery : IRequest<Result<PaginatedList<ProductDto>>>
{
    public string? SearchTerm { get; init; }
    public int? CategoryId { get; init; }
    public ProductStatus? Status { get; init; }
    public int PageNumber { get; init; } = 1;
    public int PageSize { get; init; } = 10;
    public string? SortBy { get; init; }
    public bool SortDescending { get; init; }
}
```

## Query Handler

```csharp
// Application/Features/Products/Queries/GetProductById/GetProductByIdQueryHandler.cs
public class GetProductByIdQueryHandler
    : IRequestHandler<GetProductByIdQuery, Result<ProductDto>>
{
    private readonly IApplicationDbContext _context;
    private readonly IMapper _mapper;

    public GetProductByIdQueryHandler(
        IApplicationDbContext context,
        IMapper mapper)
    {
        _context = context;
        _mapper = mapper;
    }

    public async Task<Result<ProductDto>> Handle(
        GetProductByIdQuery request,
        CancellationToken cancellationToken)
    {
        var product = await _context.Products
            .AsNoTracking()
            .Include(p => p.Category)
            .FirstOrDefaultAsync(p => p.Id == request.Id, cancellationToken);

        if (product is null)
        {
            return Result<ProductDto>.NotFound($"Product {request.Id} not found");
        }

        return Result<ProductDto>.Success(_mapper.Map<ProductDto>(product));
    }
}

// Paginated query handler
public class GetProductsQueryHandler
    : IRequestHandler<GetProductsQuery, Result<PaginatedList<ProductDto>>>
{
    private readonly IApplicationDbContext _context;
    private readonly IMapper _mapper;

    public GetProductsQueryHandler(IApplicationDbContext context, IMapper mapper)
    {
        _context = context;
        _mapper = mapper;
    }

    public async Task<Result<PaginatedList<ProductDto>>> Handle(
        GetProductsQuery request,
        CancellationToken cancellationToken)
    {
        var query = _context.Products
            .AsNoTracking()
            .Include(p => p.Category)
            .AsQueryable();

        // Apply filters
        if (!string.IsNullOrWhiteSpace(request.SearchTerm))
        {
            query = query.Where(p =>
                p.Name.Contains(request.SearchTerm) ||
                p.Description.Contains(request.SearchTerm));
        }

        if (request.CategoryId.HasValue)
        {
            query = query.Where(p => p.CategoryId == request.CategoryId.Value);
        }

        if (request.Status.HasValue)
        {
            query = query.Where(p => p.Status == request.Status.Value);
        }

        // Apply sorting
        query = request.SortBy?.ToLower() switch
        {
            "name" => request.SortDescending
                ? query.OrderByDescending(p => p.Name)
                : query.OrderBy(p => p.Name),
            "price" => request.SortDescending
                ? query.OrderByDescending(p => p.Price)
                : query.OrderBy(p => p.Price),
            "created" => request.SortDescending
                ? query.OrderByDescending(p => p.CreatedAt)
                : query.OrderBy(p => p.CreatedAt),
            _ => query.OrderByDescending(p => p.CreatedAt)
        };

        var result = await PaginatedList<ProductDto>.CreateAsync(
            query.ProjectTo<ProductDto>(_mapper.ConfigurationProvider),
            request.PageNumber,
            request.PageSize,
            cancellationToken);

        return Result<PaginatedList<ProductDto>>.Success(result);
    }
}
```

## Pipeline Behaviors

```csharp
// Application/Common/Behaviors/ValidationBehavior.cs
public class ValidationBehavior<TRequest, TResponse>
    : IPipelineBehavior<TRequest, TResponse>
    where TRequest : IRequest<TResponse>
{
    private readonly IEnumerable<IValidator<TRequest>> _validators;

    public ValidationBehavior(IEnumerable<IValidator<TRequest>> validators)
    {
        _validators = validators;
    }

    public async Task<TResponse> Handle(
        TRequest request,
        RequestHandlerDelegate<TResponse> next,
        CancellationToken cancellationToken)
    {
        if (!_validators.Any())
        {
            return await next();
        }

        var context = new ValidationContext<TRequest>(request);

        var validationResults = await Task.WhenAll(
            _validators.Select(v => v.ValidateAsync(context, cancellationToken)));

        var failures = validationResults
            .SelectMany(r => r.Errors)
            .Where(f => f != null)
            .ToList();

        if (failures.Any())
        {
            throw new ValidationException(failures);
        }

        return await next();
    }
}

// Application/Common/Behaviors/LoggingBehavior.cs
public class LoggingBehavior<TRequest, TResponse>
    : IPipelineBehavior<TRequest, TResponse>
    where TRequest : IRequest<TResponse>
{
    private readonly ILogger<LoggingBehavior<TRequest, TResponse>> _logger;
    private readonly ICurrentUserService _currentUserService;

    public LoggingBehavior(
        ILogger<LoggingBehavior<TRequest, TResponse>> logger,
        ICurrentUserService currentUserService)
    {
        _logger = logger;
        _currentUserService = currentUserService;
    }

    public async Task<TResponse> Handle(
        TRequest request,
        RequestHandlerDelegate<TResponse> next,
        CancellationToken cancellationToken)
    {
        var requestName = typeof(TRequest).Name;
        var userId = _currentUserService.UserId ?? "Anonymous";

        _logger.LogInformation(
            "Handling {RequestName} for user {UserId}",
            requestName, userId);

        var response = await next();

        _logger.LogInformation(
            "Handled {RequestName} for user {UserId}",
            requestName, userId);

        return response;
    }
}

// Application/Common/Behaviors/PerformanceBehavior.cs
public class PerformanceBehavior<TRequest, TResponse>
    : IPipelineBehavior<TRequest, TResponse>
    where TRequest : IRequest<TResponse>
{
    private readonly Stopwatch _timer;
    private readonly ILogger<TRequest> _logger;

    public PerformanceBehavior(ILogger<TRequest> logger)
    {
        _timer = new Stopwatch();
        _logger = logger;
    }

    public async Task<TResponse> Handle(
        TRequest request,
        RequestHandlerDelegate<TResponse> next,
        CancellationToken cancellationToken)
    {
        _timer.Start();

        var response = await next();

        _timer.Stop();

        var elapsedMilliseconds = _timer.ElapsedMilliseconds;

        if (elapsedMilliseconds > 500) // Log slow requests
        {
            var requestName = typeof(TRequest).Name;

            _logger.LogWarning(
                "Long running request: {RequestName} ({ElapsedMilliseconds}ms) {@Request}",
                requestName, elapsedMilliseconds, request);
        }

        return response;
    }
}
```

## Registration

```csharp
// Application/DependencyInjection.cs
public static class DependencyInjection
{
    public static IServiceCollection AddApplicationServices(this IServiceCollection services)
    {
        services.AddMediatR(cfg =>
        {
            cfg.RegisterServicesFromAssembly(Assembly.GetExecutingAssembly());

            // Add pipeline behaviors (order matters!)
            cfg.AddBehavior(typeof(IPipelineBehavior<,>), typeof(LoggingBehavior<,>));
            cfg.AddBehavior(typeof(IPipelineBehavior<,>), typeof(ValidationBehavior<,>));
            cfg.AddBehavior(typeof(IPipelineBehavior<,>), typeof(PerformanceBehavior<,>));
        });

        services.AddValidatorsFromAssembly(Assembly.GetExecutingAssembly());
        services.AddAutoMapper(Assembly.GetExecutingAssembly());

        return services;
    }
}
```

## Controller Usage

```csharp
// Api/Controllers/ProductsController.cs
[ApiController]
[Route("api/[controller]")]
public class ProductsController : ControllerBase
{
    private readonly IMediator _mediator;

    public ProductsController(IMediator mediator)
    {
        _mediator = mediator;
    }

    [HttpGet]
    public async Task<IActionResult> GetProducts([FromQuery] GetProductsQuery query)
    {
        var result = await _mediator.Send(query);
        return result.ToActionResult();
    }

    [HttpGet("{id:guid}")]
    public async Task<IActionResult> GetProduct(Guid id)
    {
        var result = await _mediator.Send(new GetProductByIdQuery(id));
        return result.ToActionResult();
    }

    [HttpPost]
    public async Task<IActionResult> CreateProduct([FromBody] CreateProductCommand command)
    {
        var result = await _mediator.Send(command);
        return result.ToCreatedActionResult(nameof(GetProduct), new { id = result.Value?.Id });
    }

    [HttpPut("{id:guid}")]
    public async Task<IActionResult> UpdateProduct(Guid id, [FromBody] UpdateProductRequest request)
    {
        var command = UpdateProductCommand.Create(id, request);
        var result = await _mediator.Send(command);
        return result.ToActionResult();
    }

    [HttpDelete("{id:guid}")]
    public async Task<IActionResult> DeleteProduct(Guid id)
    {
        var result = await _mediator.Send(new DeleteProductCommand(id));
        return result.ToActionResult();
    }
}
```

## Best Practices

1. **Single Responsibility**: One handler per command/query
2. **Immutable Commands**: Use records for commands and queries
3. **Validation Separation**: Use FluentValidation with pipeline behavior
4. **Cross-Cutting Concerns**: Use pipeline behaviors for logging, caching, transactions
5. **Thin Controllers**: Controllers only dispatch to MediatR
6. **Return Result Types**: Use Result pattern for consistent error handling
