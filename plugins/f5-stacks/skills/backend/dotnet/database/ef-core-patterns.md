---
name: ef-core-patterns
description: Entity Framework Core best practices and patterns
applies_to: dotnet
type: skill
---

# Entity Framework Core Patterns

## Overview

Entity Framework Core is the recommended ORM for .NET applications. This guide covers best practices for performance, maintainability, and proper configuration.

## DbContext Configuration

### Basic Setup

```csharp
// Infrastructure/Persistence/AppDbContext.cs
public class AppDbContext : DbContext, IApplicationDbContext, IUnitOfWork
{
    private readonly ICurrentUserService _currentUser;
    private readonly IDateTimeService _dateTime;

    public AppDbContext(
        DbContextOptions<AppDbContext> options,
        ICurrentUserService currentUser,
        IDateTimeService dateTime)
        : base(options)
    {
        _currentUser = currentUser;
        _dateTime = dateTime;
    }

    public DbSet<Product> Products => Set<Product>();
    public DbSet<Category> Categories => Set<Category>();
    public DbSet<Order> Orders => Set<Order>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        // Apply all configurations from assembly
        modelBuilder.ApplyConfigurationsFromAssembly(
            typeof(AppDbContext).Assembly);

        base.OnModelCreating(modelBuilder);
    }

    public override async Task<int> SaveChangesAsync(
        CancellationToken cancellationToken = default)
    {
        // Auto-set audit fields
        foreach (var entry in ChangeTracker.Entries<IAuditableEntity>())
        {
            switch (entry.State)
            {
                case EntityState.Added:
                    entry.Entity.CreatedBy = _currentUser.UserId;
                    entry.Entity.CreatedAt = _dateTime.Now;
                    break;
                case EntityState.Modified:
                    entry.Entity.UpdatedBy = _currentUser.UserId;
                    entry.Entity.UpdatedAt = _dateTime.Now;
                    break;
            }
        }

        return await base.SaveChangesAsync(cancellationToken);
    }
}
```

### Fluent Configuration

```csharp
// Infrastructure/Persistence/Configurations/ProductConfiguration.cs
public class ProductConfiguration : IEntityTypeConfiguration<Product>
{
    public void Configure(EntityTypeBuilder<Product> builder)
    {
        // Table
        builder.ToTable("Products");

        // Primary Key
        builder.HasKey(p => p.Id);

        // Properties
        builder.Property(p => p.Name)
            .HasMaxLength(200)
            .IsRequired();

        builder.Property(p => p.Description)
            .HasMaxLength(1000);

        builder.Property(p => p.Price)
            .HasPrecision(18, 2);

        builder.Property(p => p.Sku)
            .HasMaxLength(50);

        // Relationships
        builder.HasOne(p => p.Category)
            .WithMany(c => c.Products)
            .HasForeignKey(p => p.CategoryId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasMany(p => p.Tags)
            .WithMany(t => t.Products)
            .UsingEntity<ProductTag>(
                j => j.HasOne(pt => pt.Tag)
                    .WithMany()
                    .HasForeignKey(pt => pt.TagId),
                j => j.HasOne(pt => pt.Product)
                    .WithMany()
                    .HasForeignKey(pt => pt.ProductId),
                j => j.HasKey(pt => new { pt.ProductId, pt.TagId }));

        // Indexes
        builder.HasIndex(p => p.Sku)
            .IsUnique();

        builder.HasIndex(p => p.Name);

        builder.HasIndex(p => new { p.CategoryId, p.IsActive });

        // Query Filter (Soft Delete)
        builder.HasQueryFilter(p => !p.IsDeleted);
    }
}
```

## Query Patterns

### Eager Loading

```csharp
// ✅ Good - Explicit includes
var products = await _context.Products
    .Include(p => p.Category)
    .Include(p => p.Tags)
        .ThenInclude(t => t.Tag)
    .Where(p => p.IsActive)
    .ToListAsync();

// ✅ Good - Split query for large relationships
var products = await _context.Products
    .Include(p => p.OrderItems)
    .AsSplitQuery()
    .ToListAsync();
```

### Projection

```csharp
// ✅ Best - Select only needed fields
var products = await _context.Products
    .Where(p => p.IsActive)
    .Select(p => new ProductDto
    {
        Id = p.Id,
        Name = p.Name,
        Price = p.Price,
        CategoryName = p.Category.Name
    })
    .ToListAsync();

// ✅ With AutoMapper
var products = await _context.Products
    .Where(p => p.IsActive)
    .ProjectTo<ProductDto>(_mapper.ConfigurationProvider)
    .ToListAsync();
```

### No Tracking

```csharp
// ✅ For read-only queries
var products = await _context.Products
    .AsNoTracking()
    .Where(p => p.IsActive)
    .ToListAsync();

// Set globally for read-only context
services.AddDbContext<ReadOnlyDbContext>(options =>
    options.UseSqlServer(connectionString)
           .UseQueryTrackingBehavior(QueryTrackingBehavior.NoTracking));
```

### Pagination

```csharp
// ✅ Efficient pagination
var products = await _context.Products
    .OrderBy(p => p.Name)
    .Skip((pageNumber - 1) * pageSize)
    .Take(pageSize)
    .ToListAsync();

var totalCount = await _context.Products.CountAsync();

// ✅ Extension method
public static class QueryableExtensions
{
    public static async Task<PaginatedList<T>> ToPaginatedListAsync<T>(
        this IQueryable<T> source,
        int pageNumber,
        int pageSize,
        CancellationToken ct = default)
    {
        var count = await source.CountAsync(ct);
        var items = await source
            .Skip((pageNumber - 1) * pageSize)
            .Take(pageSize)
            .ToListAsync(ct);

        return new PaginatedList<T>(items, count, pageNumber, pageSize);
    }
}
```

## Performance Tips

### 1. Use Compiled Queries for Hot Paths

```csharp
private static readonly Func<AppDbContext, Guid, Task<Product?>>
    GetProductById = EF.CompileAsyncQuery(
        (AppDbContext context, Guid id) =>
            context.Products
                .Include(p => p.Category)
                .FirstOrDefault(p => p.Id == id));

public async Task<Product?> GetByIdAsync(Guid id)
{
    return await GetProductById(_context, id);
}
```

### 2. Batch Operations

```csharp
// ✅ Batch update with ExecuteUpdateAsync (.NET 7+)
await _context.Products
    .Where(p => p.CategoryId == categoryId)
    .ExecuteUpdateAsync(setters => setters
        .SetProperty(p => p.IsActive, false)
        .SetProperty(p => p.UpdatedAt, DateTime.UtcNow));

// ✅ Batch delete
await _context.Products
    .Where(p => p.IsDeleted && p.DeletedAt < DateTime.UtcNow.AddDays(-30))
    .ExecuteDeleteAsync();
```

### 3. Avoid N+1 Queries

```csharp
// ❌ Bad - N+1 problem
var categories = await _context.Categories.ToListAsync();
foreach (var category in categories)
{
    var products = await _context.Products
        .Where(p => p.CategoryId == category.Id)
        .ToListAsync(); // N additional queries!
}

// ✅ Good - Single query with Include
var categories = await _context.Categories
    .Include(c => c.Products)
    .ToListAsync();
```

### 4. Use Raw SQL When Needed

```csharp
// ✅ For complex queries
var products = await _context.Products
    .FromSqlRaw(@"
        SELECT * FROM Products p
        WHERE p.Price > {0}
        AND EXISTS (SELECT 1 FROM Categories c
                    WHERE c.Id = p.CategoryId AND c.IsActive = 1)",
        minPrice)
    .ToListAsync();
```

## Value Converters

```csharp
// Domain enum
public enum OrderStatus
{
    Pending = 1,
    Processing = 2,
    Shipped = 3,
    Delivered = 4,
    Cancelled = 5
}

// Configuration
builder.Property(o => o.Status)
    .HasConversion<string>()
    .HasMaxLength(20);

// Custom converter
builder.Property(o => o.Status)
    .HasConversion(
        v => v.ToString(),
        v => (OrderStatus)Enum.Parse(typeof(OrderStatus), v));

// JSON column (.NET 7+)
builder.OwnsOne(o => o.ShippingAddress, sa =>
{
    sa.ToJson();
});
```

## Global Query Filters

```csharp
// Soft delete filter
protected override void OnModelCreating(ModelBuilder modelBuilder)
{
    // Apply to all entities implementing ISoftDeletable
    foreach (var entityType in modelBuilder.Model.GetEntityTypes())
    {
        if (typeof(ISoftDeletable).IsAssignableFrom(entityType.ClrType))
        {
            var parameter = Expression.Parameter(entityType.ClrType, "e");
            var property = Expression.Property(parameter, "IsDeleted");
            var condition = Expression.Equal(property, Expression.Constant(false));
            var lambda = Expression.Lambda(condition, parameter);

            modelBuilder.Entity(entityType.ClrType).HasQueryFilter(lambda);
        }
    }
}

// Disable filter when needed
var allProducts = await _context.Products
    .IgnoreQueryFilters()
    .ToListAsync();
```

## Best Practices Summary

| Practice | Recommendation |
|----------|----------------|
| Tracking | Use `AsNoTracking()` for read-only |
| Loading | Use projection or explicit Include |
| Pagination | Always paginate large result sets |
| Indexes | Index frequently queried columns |
| Batch Ops | Use ExecuteUpdateAsync/ExecuteDeleteAsync |
| Raw SQL | Use for complex queries |
| Filters | Apply global filters for multi-tenancy/soft delete |

## Related Skills

- `skills/database/migrations.md`
- `skills/database/repository-pattern.md`
