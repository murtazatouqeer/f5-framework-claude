---
name: dotnet-entity
description: Template for Entity Framework Core entities
applies_to: dotnet
type: template
---

# Entity Framework Core Entity Template

## Domain Entity

```csharp
// {{SolutionName}}.Domain/Entities/{{EntityName}}.cs
using {{SolutionName}}.Domain.Common;

namespace {{SolutionName}}.Domain.Entities;

public class {{EntityName}} : BaseEntity, IAuditableEntity
{
    // Properties
    public string Name { get; private set; } = string.Empty;
    public string? Description { get; private set; }
    public decimal Price { get; private set; }
    public int Stock { get; private set; }
    public bool IsActive { get; private set; } = true;

    // Foreign Keys
    public Guid CategoryId { get; private set; }

    // Navigation Properties
    public virtual Category Category { get; private set; } = null!;
    public virtual ICollection<{{EntityName}}Tag> Tags { get; private set; } = new List<{{EntityName}}Tag>();

    // Audit Fields
    public DateTime CreatedAt { get; set; }
    public string? CreatedBy { get; set; }
    public DateTime? UpdatedAt { get; set; }
    public string? UpdatedBy { get; set; }

    // Private constructor for EF Core
    private {{EntityName}}() { }

    // Factory method for creation
    public static {{EntityName}} Create(
        string name,
        string? description,
        decimal price,
        Guid categoryId)
    {
        if (string.IsNullOrWhiteSpace(name))
            throw new ArgumentException("Name is required", nameof(name));

        if (price < 0)
            throw new ArgumentException("Price cannot be negative", nameof(price));

        return new {{EntityName}}
        {
            Id = Guid.NewGuid(),
            Name = name,
            Description = description,
            Price = price,
            CategoryId = categoryId,
            IsActive = true,
            Stock = 0
        };
    }

    // Domain methods
    public void UpdateDetails(string name, string? description, decimal price)
    {
        if (string.IsNullOrWhiteSpace(name))
            throw new ArgumentException("Name is required", nameof(name));

        if (price < 0)
            throw new ArgumentException("Price cannot be negative", nameof(price));

        Name = name;
        Description = description;
        Price = price;
    }

    public void UpdateStock(int quantity)
    {
        var newStock = Stock + quantity;
        if (newStock < 0)
            throw new InvalidOperationException("Stock cannot be negative");

        Stock = newStock;
    }

    public void ChangeCategory(Guid categoryId)
    {
        if (categoryId == Guid.Empty)
            throw new ArgumentException("Category ID is required", nameof(categoryId));

        CategoryId = categoryId;
    }

    public void Activate() => IsActive = true;

    public void Deactivate() => IsActive = false;
}
```

## Base Classes

```csharp
// {{SolutionName}}.Domain/Common/BaseEntity.cs
namespace {{SolutionName}}.Domain.Common;

public abstract class BaseEntity
{
    public Guid Id { get; protected set; }

    private readonly List<IDomainEvent> _domainEvents = new();
    public IReadOnlyCollection<IDomainEvent> DomainEvents => _domainEvents.AsReadOnly();

    protected void AddDomainEvent(IDomainEvent domainEvent)
    {
        _domainEvents.Add(domainEvent);
    }

    public void ClearDomainEvents()
    {
        _domainEvents.Clear();
    }
}

public interface IAuditableEntity
{
    DateTime CreatedAt { get; set; }
    string? CreatedBy { get; set; }
    DateTime? UpdatedAt { get; set; }
    string? UpdatedBy { get; set; }
}

public interface ISoftDeletable
{
    bool IsDeleted { get; set; }
    DateTime? DeletedAt { get; set; }
    string? DeletedBy { get; set; }
}
```

## Entity Configuration

```csharp
// {{SolutionName}}.Infrastructure/Persistence/Configurations/{{EntityName}}Configuration.cs
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using {{SolutionName}}.Domain.Entities;

namespace {{SolutionName}}.Infrastructure.Persistence.Configurations;

public class {{EntityName}}Configuration : IEntityTypeConfiguration<{{EntityName}}>
{
    public void Configure(EntityTypeBuilder<{{EntityName}}> builder)
    {
        builder.ToTable("{{EntityName}}s");

        builder.HasKey(e => e.Id);

        builder.Property(e => e.Name)
            .HasMaxLength(200)
            .IsRequired();

        builder.Property(e => e.Description)
            .HasMaxLength(1000);

        builder.Property(e => e.Price)
            .HasPrecision(18, 2);

        builder.Property(e => e.Stock)
            .IsRequired();

        builder.Property(e => e.IsActive)
            .HasDefaultValue(true);

        // Foreign Key
        builder.HasOne(e => e.Category)
            .WithMany(c => c.{{EntityName}}s)
            .HasForeignKey(e => e.CategoryId)
            .OnDelete(DeleteBehavior.Restrict);

        // Indexes
        builder.HasIndex(e => e.Name);
        builder.HasIndex(e => e.CategoryId);
        builder.HasIndex(e => e.IsActive);

        // Ignore domain events in persistence
        builder.Ignore(e => e.DomainEvents);
    }
}
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{SolutionName}}` | Solution/project name | `MyApp` |
| `{{EntityName}}` | PascalCase entity name | `Product` |
