---
name: repository-pattern
description: Repository and Unit of Work patterns for data access
applies_to: dotnet
type: skill
---

# Repository Pattern

## Overview

The Repository pattern abstracts data access, providing a collection-like interface for domain objects. Combined with Unit of Work, it enables transaction management and testing flexibility.

## Generic Repository Interface

```csharp
// Domain/Interfaces/IRepository.cs
public interface IRepository<T> where T : BaseEntity
{
    Task<T?> GetByIdAsync(Guid id, CancellationToken ct = default);
    Task<IEnumerable<T>> GetAllAsync(CancellationToken ct = default);
    Task<IEnumerable<T>> FindAsync(
        Expression<Func<T, bool>> predicate,
        CancellationToken ct = default);
    Task AddAsync(T entity, CancellationToken ct = default);
    void Update(T entity);
    void Delete(T entity);
    IQueryable<T> Query();
}
```

## Generic Repository Implementation

```csharp
// Infrastructure/Persistence/Repositories/Repository.cs
public class Repository<T> : IRepository<T> where T : BaseEntity
{
    protected readonly AppDbContext _context;
    protected readonly DbSet<T> _dbSet;

    public Repository(AppDbContext context)
    {
        _context = context;
        _dbSet = context.Set<T>();
    }

    public virtual async Task<T?> GetByIdAsync(
        Guid id,
        CancellationToken ct = default)
    {
        return await _dbSet.FindAsync(new object[] { id }, ct);
    }

    public virtual async Task<IEnumerable<T>> GetAllAsync(
        CancellationToken ct = default)
    {
        return await _dbSet.ToListAsync(ct);
    }

    public virtual async Task<IEnumerable<T>> FindAsync(
        Expression<Func<T, bool>> predicate,
        CancellationToken ct = default)
    {
        return await _dbSet.Where(predicate).ToListAsync(ct);
    }

    public virtual async Task AddAsync(
        T entity,
        CancellationToken ct = default)
    {
        await _dbSet.AddAsync(entity, ct);
    }

    public virtual void Update(T entity)
    {
        _dbSet.Update(entity);
    }

    public virtual void Delete(T entity)
    {
        _dbSet.Remove(entity);
    }

    public IQueryable<T> Query()
    {
        return _dbSet.AsQueryable();
    }
}
```

## Specific Repository

```csharp
// Domain/Interfaces/IProductRepository.cs
public interface IProductRepository : IRepository<Product>
{
    Task<Product?> GetBySkuAsync(string sku, CancellationToken ct = default);
    Task<IEnumerable<Product>> GetByCategoryAsync(
        Guid categoryId,
        CancellationToken ct = default);
    Task<IEnumerable<Product>> GetActiveProductsAsync(
        CancellationToken ct = default);
    Task<bool> SkuExistsAsync(string sku, CancellationToken ct = default);
}

// Infrastructure/Persistence/Repositories/ProductRepository.cs
public class ProductRepository : Repository<Product>, IProductRepository
{
    public ProductRepository(AppDbContext context) : base(context)
    {
    }

    public override async Task<Product?> GetByIdAsync(
        Guid id,
        CancellationToken ct = default)
    {
        return await _dbSet
            .Include(p => p.Category)
            .Include(p => p.Tags)
            .FirstOrDefaultAsync(p => p.Id == id, ct);
    }

    public async Task<Product?> GetBySkuAsync(
        string sku,
        CancellationToken ct = default)
    {
        return await _dbSet
            .Include(p => p.Category)
            .FirstOrDefaultAsync(p => p.Sku == sku, ct);
    }

    public async Task<IEnumerable<Product>> GetByCategoryAsync(
        Guid categoryId,
        CancellationToken ct = default)
    {
        return await _dbSet
            .Where(p => p.CategoryId == categoryId)
            .OrderBy(p => p.Name)
            .ToListAsync(ct);
    }

    public async Task<IEnumerable<Product>> GetActiveProductsAsync(
        CancellationToken ct = default)
    {
        return await _dbSet
            .Where(p => p.IsActive)
            .Include(p => p.Category)
            .OrderBy(p => p.Name)
            .ToListAsync(ct);
    }

    public async Task<bool> SkuExistsAsync(
        string sku,
        CancellationToken ct = default)
    {
        return await _dbSet.AnyAsync(p => p.Sku == sku, ct);
    }
}
```

## Unit of Work

```csharp
// Domain/Interfaces/IUnitOfWork.cs
public interface IUnitOfWork : IDisposable
{
    IProductRepository Products { get; }
    ICategoryRepository Categories { get; }
    IOrderRepository Orders { get; }

    Task<int> SaveChangesAsync(CancellationToken ct = default);
    Task BeginTransactionAsync(CancellationToken ct = default);
    Task CommitTransactionAsync(CancellationToken ct = default);
    Task RollbackTransactionAsync(CancellationToken ct = default);
}

// Infrastructure/Persistence/UnitOfWork.cs
public class UnitOfWork : IUnitOfWork
{
    private readonly AppDbContext _context;
    private IDbContextTransaction? _transaction;

    private IProductRepository? _products;
    private ICategoryRepository? _categories;
    private IOrderRepository? _orders;

    public UnitOfWork(AppDbContext context)
    {
        _context = context;
    }

    public IProductRepository Products =>
        _products ??= new ProductRepository(_context);

    public ICategoryRepository Categories =>
        _categories ??= new CategoryRepository(_context);

    public IOrderRepository Orders =>
        _orders ??= new OrderRepository(_context);

    public async Task<int> SaveChangesAsync(CancellationToken ct = default)
    {
        return await _context.SaveChangesAsync(ct);
    }

    public async Task BeginTransactionAsync(CancellationToken ct = default)
    {
        _transaction = await _context.Database
            .BeginTransactionAsync(ct);
    }

    public async Task CommitTransactionAsync(CancellationToken ct = default)
    {
        try
        {
            await _context.SaveChangesAsync(ct);
            await _transaction!.CommitAsync(ct);
        }
        catch
        {
            await RollbackTransactionAsync(ct);
            throw;
        }
        finally
        {
            _transaction?.Dispose();
            _transaction = null;
        }
    }

    public async Task RollbackTransactionAsync(CancellationToken ct = default)
    {
        if (_transaction != null)
        {
            await _transaction.RollbackAsync(ct);
            _transaction.Dispose();
            _transaction = null;
        }
    }

    public void Dispose()
    {
        _transaction?.Dispose();
        _context.Dispose();
    }
}
```

## Usage in Service

```csharp
// Application/Services/OrderService.cs
public class OrderService : IOrderService
{
    private readonly IUnitOfWork _unitOfWork;

    public OrderService(IUnitOfWork unitOfWork)
    {
        _unitOfWork = unitOfWork;
    }

    public async Task<OrderDto> CreateOrderAsync(
        CreateOrderDto dto,
        CancellationToken ct = default)
    {
        await _unitOfWork.BeginTransactionAsync(ct);

        try
        {
            // Get product
            var product = await _unitOfWork.Products
                .GetByIdAsync(dto.ProductId, ct);

            if (product is null)
                throw new NotFoundException("Product not found");

            // Create order
            var order = Order.Create(product, dto.Quantity);
            await _unitOfWork.Orders.AddAsync(order, ct);

            // Update stock
            product.DecrementStock(dto.Quantity);
            _unitOfWork.Products.Update(product);

            await _unitOfWork.CommitTransactionAsync(ct);

            return _mapper.Map<OrderDto>(order);
        }
        catch
        {
            await _unitOfWork.RollbackTransactionAsync(ct);
            throw;
        }
    }
}
```

## Specification Pattern

```csharp
// Domain/Specifications/Specification.cs
public abstract class Specification<T>
{
    public abstract Expression<Func<T, bool>> ToExpression();

    public bool IsSatisfiedBy(T entity)
    {
        var predicate = ToExpression().Compile();
        return predicate(entity);
    }

    public Specification<T> And(Specification<T> specification)
    {
        return new AndSpecification<T>(this, specification);
    }

    public Specification<T> Or(Specification<T> specification)
    {
        return new OrSpecification<T>(this, specification);
    }
}

// Domain/Specifications/ActiveProductSpecification.cs
public class ActiveProductSpecification : Specification<Product>
{
    public override Expression<Func<Product, bool>> ToExpression()
    {
        return product => product.IsActive && !product.IsDeleted;
    }
}

// Domain/Specifications/ProductInCategorySpecification.cs
public class ProductInCategorySpecification : Specification<Product>
{
    private readonly Guid _categoryId;

    public ProductInCategorySpecification(Guid categoryId)
    {
        _categoryId = categoryId;
    }

    public override Expression<Func<Product, bool>> ToExpression()
    {
        return product => product.CategoryId == _categoryId;
    }
}

// Usage
var spec = new ActiveProductSpecification()
    .And(new ProductInCategorySpecification(categoryId));

var products = await _repository.FindAsync(spec.ToExpression());
```

## DI Registration

```csharp
// Infrastructure/DependencyInjection.cs
public static IServiceCollection AddInfrastructure(
    this IServiceCollection services,
    IConfiguration configuration)
{
    services.AddDbContext<AppDbContext>(options =>
        options.UseSqlServer(
            configuration.GetConnectionString("DefaultConnection")));

    // Repositories
    services.AddScoped(typeof(IRepository<>), typeof(Repository<>));
    services.AddScoped<IProductRepository, ProductRepository>();
    services.AddScoped<ICategoryRepository, CategoryRepository>();
    services.AddScoped<IOrderRepository, OrderRepository>();

    // Unit of Work
    services.AddScoped<IUnitOfWork, UnitOfWork>();

    return services;
}
```

## Best Practices

| Practice | Recommendation |
|----------|----------------|
| Interface Location | Domain layer |
| Implementation | Infrastructure layer |
| Generic vs Specific | Use specific for custom queries |
| Unit of Work | Use for multi-entity transactions |
| Lazy Loading | Avoid, use explicit Include |
| Query Methods | Return IQueryable for flexibility |

## Related Skills

- `skills/database/ef-core-patterns.md`
- `skills/architecture/clean-architecture.md`
