---
name: dotnet-entity-generator
description: Generates Entity Framework Core entities with proper configuration
triggers:
  - create entity
  - generate entity
  - add entity
  - ef entity
  - dotnet entity
---

# Entity Framework Core Entity Generator

## Purpose

Generate domain entities with proper EF Core configuration, relationships, and value objects.

## Required Context

Before generating, gather:
1. **Entity Name**: PascalCase name (e.g., `Product`)
2. **Properties**: Fields with types and constraints
3. **Relationships**: Navigation properties and foreign keys
4. **Audit Fields**: CreatedAt, UpdatedAt, CreatedBy, etc.

## Generation Template

### Domain Entity

```csharp
// {{SolutionName}}.Domain/Entities/{{EntityName}}.cs
using {{SolutionName}}.Domain.Common;

namespace {{SolutionName}}.Domain.Entities;

public class {{EntityName}} : BaseEntity, IAuditableEntity
{
    public string Name { get; private set; } = string.Empty;
    public string? Description { get; private set; }
    public decimal Price { get; private set; }
    public int Stock { get; private set; }
    public bool IsActive { get; private set; } = true;

    // Foreign Key
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

    // Factory method
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
            IsActive = true
        };
    }

    // Domain methods
    public void UpdateDetails(string name, string? description, decimal price)
    {
        if (string.IsNullOrWhiteSpace(name))
            throw new ArgumentException("Name is required", nameof(name));

        Name = name;
        Description = description;
        Price = price;
    }

    public void UpdateStock(int quantity)
    {
        if (Stock + quantity < 0)
            throw new InvalidOperationException("Stock cannot be negative");

        Stock += quantity;
    }

    public void Activate() => IsActive = true;

    public void Deactivate() => IsActive = false;
}
```

### Base Entity

```csharp
// {{SolutionName}}.Domain/Common/BaseEntity.cs
namespace {{SolutionName}}.Domain.Common;

public abstract class BaseEntity
{
    public Guid Id { get; protected set; }
}

public interface IAuditableEntity
{
    DateTime CreatedAt { get; set; }
    string? CreatedBy { get; set; }
    DateTime? UpdatedAt { get; set; }
    string? UpdatedBy { get; set; }
}
```

### Entity Configuration

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

        builder.HasOne(e => e.Category)
            .WithMany(c => c.{{EntityName}}s)
            .HasForeignKey(e => e.CategoryId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasIndex(e => e.Name);
        builder.HasIndex(e => e.IsActive);
    }
}
```

## Generation Checklist

- [ ] Private setters for encapsulation
- [ ] Factory method for creation
- [ ] Domain validation in constructors
- [ ] Navigation properties properly configured
- [ ] IEntityTypeConfiguration for Fluent API
- [ ] Proper indexes defined
- [ ] Audit fields implemented
- [ ] Private parameterless constructor for EF

## Related Templates

- `templates/dotnet-entity.md` - Full entity template
- `templates/dotnet-repository.md` - Repository pattern
