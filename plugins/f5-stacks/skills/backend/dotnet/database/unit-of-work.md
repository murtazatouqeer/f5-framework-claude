# Unit of Work Pattern - ASP.NET Core

## Overview

The Unit of Work pattern maintains a list of objects affected by a business transaction and coordinates the writing out of changes. Combined with the Repository pattern, it provides a clean abstraction over data access.

## Unit of Work Interface

```csharp
// Application/Interfaces/IUnitOfWork.cs
public interface IUnitOfWork : IDisposable
{
    IProductRepository Products { get; }
    ICategoryRepository Categories { get; }
    IOrderRepository Orders { get; }

    Task<int> SaveChangesAsync(CancellationToken cancellationToken = default);
    Task BeginTransactionAsync(CancellationToken cancellationToken = default);
    Task CommitTransactionAsync(CancellationToken cancellationToken = default);
    Task RollbackTransactionAsync(CancellationToken cancellationToken = default);
}
```

## Unit of Work Implementation

```csharp
// Infrastructure/Persistence/UnitOfWork.cs
public class UnitOfWork : IUnitOfWork
{
    private readonly ApplicationDbContext _context;
    private IDbContextTransaction? _transaction;

    private IProductRepository? _products;
    private ICategoryRepository? _categories;
    private IOrderRepository? _orders;

    public UnitOfWork(ApplicationDbContext context)
    {
        _context = context;
    }

    public IProductRepository Products =>
        _products ??= new ProductRepository(_context);

    public ICategoryRepository Categories =>
        _categories ??= new CategoryRepository(_context);

    public IOrderRepository Orders =>
        _orders ??= new OrderRepository(_context);

    public async Task<int> SaveChangesAsync(CancellationToken cancellationToken = default)
    {
        return await _context.SaveChangesAsync(cancellationToken);
    }

    public async Task BeginTransactionAsync(CancellationToken cancellationToken = default)
    {
        _transaction = await _context.Database.BeginTransactionAsync(cancellationToken);
    }

    public async Task CommitTransactionAsync(CancellationToken cancellationToken = default)
    {
        try
        {
            await _context.SaveChangesAsync(cancellationToken);
            await _transaction?.CommitAsync(cancellationToken)!;
        }
        catch
        {
            await RollbackTransactionAsync(cancellationToken);
            throw;
        }
        finally
        {
            _transaction?.Dispose();
            _transaction = null;
        }
    }

    public async Task RollbackTransactionAsync(CancellationToken cancellationToken = default)
    {
        if (_transaction is not null)
        {
            await _transaction.RollbackAsync(cancellationToken);
            _transaction.Dispose();
            _transaction = null;
        }
    }

    public void Dispose()
    {
        _transaction?.Dispose();
        _context.Dispose();
        GC.SuppressFinalize(this);
    }
}
```

## Generic Unit of Work

```csharp
// Application/Interfaces/IGenericUnitOfWork.cs
public interface IGenericUnitOfWork : IDisposable
{
    IGenericRepository<TEntity> Repository<TEntity>() where TEntity : BaseEntity;
    Task<int> SaveChangesAsync(CancellationToken cancellationToken = default);
    Task<bool> SaveEntitiesAsync(CancellationToken cancellationToken = default);
}

// Infrastructure/Persistence/GenericUnitOfWork.cs
public class GenericUnitOfWork : IGenericUnitOfWork
{
    private readonly ApplicationDbContext _context;
    private readonly Dictionary<Type, object> _repositories = new();
    private bool _disposed;

    public GenericUnitOfWork(ApplicationDbContext context)
    {
        _context = context;
    }

    public IGenericRepository<TEntity> Repository<TEntity>() where TEntity : BaseEntity
    {
        var type = typeof(TEntity);

        if (!_repositories.ContainsKey(type))
        {
            var repositoryInstance = new GenericRepository<TEntity>(_context);
            _repositories.Add(type, repositoryInstance);
        }

        return (IGenericRepository<TEntity>)_repositories[type];
    }

    public async Task<int> SaveChangesAsync(CancellationToken cancellationToken = default)
    {
        return await _context.SaveChangesAsync(cancellationToken);
    }

    public async Task<bool> SaveEntitiesAsync(CancellationToken cancellationToken = default)
    {
        // Dispatch domain events before saving
        var domainEntities = _context.ChangeTracker
            .Entries<BaseEntity>()
            .Where(x => x.Entity.DomainEvents.Any())
            .ToList();

        var domainEvents = domainEntities
            .SelectMany(x => x.Entity.DomainEvents)
            .ToList();

        domainEntities.ForEach(entity => entity.Entity.ClearDomainEvents());

        // Save changes
        var result = await _context.SaveChangesAsync(cancellationToken) > 0;

        // Publish domain events after save
        // ... dispatch events

        return result;
    }

    protected virtual void Dispose(bool disposing)
    {
        if (!_disposed && disposing)
        {
            _context.Dispose();
        }
        _disposed = true;
    }

    public void Dispose()
    {
        Dispose(true);
        GC.SuppressFinalize(this);
    }
}
```

## Usage in Services

```csharp
// Application/Services/OrderService.cs
public class OrderService : IOrderService
{
    private readonly IUnitOfWork _unitOfWork;
    private readonly ILogger<OrderService> _logger;

    public OrderService(IUnitOfWork unitOfWork, ILogger<OrderService> logger)
    {
        _unitOfWork = unitOfWork;
        _logger = logger;
    }

    public async Task<Result<OrderDto>> CreateOrderAsync(
        CreateOrderRequest request,
        CancellationToken cancellationToken = default)
    {
        try
        {
            await _unitOfWork.BeginTransactionAsync(cancellationToken);

            // Validate product availability
            var product = await _unitOfWork.Products
                .GetByIdAsync(request.ProductId, cancellationToken);

            if (product is null)
                return Result<OrderDto>.NotFound("Product not found");

            if (product.StockQuantity < request.Quantity)
                return Result<OrderDto>.Invalid("Insufficient stock");

            // Create order
            var order = new Order
            {
                UserId = request.UserId,
                Status = OrderStatus.Pending,
                Items = new List<OrderItem>
                {
                    new OrderItem
                    {
                        ProductId = product.Id,
                        Quantity = request.Quantity,
                        UnitPrice = product.Price
                    }
                }
            };

            await _unitOfWork.Orders.AddAsync(order, cancellationToken);

            // Update stock
            product.StockQuantity -= request.Quantity;
            _unitOfWork.Products.Update(product);

            // Commit transaction
            await _unitOfWork.CommitTransactionAsync(cancellationToken);

            _logger.LogInformation("Order {OrderId} created successfully", order.Id);

            return Result<OrderDto>.Success(order.ToDto());
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error creating order");
            await _unitOfWork.RollbackTransactionAsync(cancellationToken);
            return Result<OrderDto>.Error("Failed to create order");
        }
    }
}
```

## Usage with MediatR Handler

```csharp
// Application/Features/Orders/Commands/CreateOrderCommandHandler.cs
public class CreateOrderCommandHandler : IRequestHandler<CreateOrderCommand, Result<OrderDto>>
{
    private readonly IUnitOfWork _unitOfWork;

    public CreateOrderCommandHandler(IUnitOfWork unitOfWork)
    {
        _unitOfWork = unitOfWork;
    }

    public async Task<Result<OrderDto>> Handle(
        CreateOrderCommand request,
        CancellationToken cancellationToken)
    {
        await _unitOfWork.BeginTransactionAsync(cancellationToken);

        try
        {
            // Business logic here...

            var order = Order.Create(request.UserId, request.Items);
            await _unitOfWork.Orders.AddAsync(order, cancellationToken);
            await _unitOfWork.CommitTransactionAsync(cancellationToken);

            return Result<OrderDto>.Success(order.ToDto());
        }
        catch
        {
            await _unitOfWork.RollbackTransactionAsync(cancellationToken);
            throw;
        }
    }
}
```

## Dependency Injection Registration

```csharp
// Api/Extensions/ServiceCollectionExtensions.cs
public static class ServiceCollectionExtensions
{
    public static IServiceCollection AddPersistence(
        this IServiceCollection services,
        IConfiguration configuration)
    {
        services.AddDbContext<ApplicationDbContext>(options =>
            options.UseSqlServer(
                configuration.GetConnectionString("DefaultConnection")));

        // Register Unit of Work
        services.AddScoped<IUnitOfWork, UnitOfWork>();
        services.AddScoped<IGenericUnitOfWork, GenericUnitOfWork>();

        // Register repositories
        services.AddScoped<IProductRepository, ProductRepository>();
        services.AddScoped<ICategoryRepository, CategoryRepository>();
        services.AddScoped<IOrderRepository, OrderRepository>();

        return services;
    }
}
```

## Best Practices

1. **Scoped Lifetime**: Register as Scoped to match DbContext lifetime
2. **Transaction Management**: Always use transactions for multi-entity operations
3. **Lazy Initialization**: Create repositories lazily for performance
4. **Domain Events**: Dispatch domain events within SaveChangesAsync
5. **Exception Handling**: Always rollback on exceptions
6. **Async Operations**: Use async methods for database operations
