---
name: dotnet-repository
description: Template for repository interface and implementation
applies_to: dotnet
type: template
---

# Repository Template

## Repository Interface

```csharp
// {{SolutionName}}.Domain/Interfaces/I{{EntityName}}Repository.cs
using {{SolutionName}}.Domain.Entities;

namespace {{SolutionName}}.Domain.Interfaces;

public interface I{{EntityName}}Repository : IRepository<{{EntityName}}>
{
    Task<{{EntityName}}?> GetByIdWithIncludesAsync(
        Guid id,
        CancellationToken cancellationToken = default);

    Task<IEnumerable<{{EntityName}}>> GetByCategoryAsync(
        Guid categoryId,
        CancellationToken cancellationToken = default);

    Task<IEnumerable<{{EntityName}}>> GetActiveAsync(
        CancellationToken cancellationToken = default);

    Task<bool> NameExistsAsync(
        string name,
        Guid? excludeId = null,
        CancellationToken cancellationToken = default);

    Task<IEnumerable<{{EntityName}}>> SearchAsync(
        string searchTerm,
        CancellationToken cancellationToken = default);
}
```

## Repository Implementation

```csharp
// {{SolutionName}}.Infrastructure/Persistence/Repositories/{{EntityName}}Repository.cs
using Microsoft.EntityFrameworkCore;
using {{SolutionName}}.Domain.Entities;
using {{SolutionName}}.Domain.Interfaces;
using {{SolutionName}}.Infrastructure.Persistence;

namespace {{SolutionName}}.Infrastructure.Persistence.Repositories;

public class {{EntityName}}Repository : Repository<{{EntityName}}>, I{{EntityName}}Repository
{
    public {{EntityName}}Repository(AppDbContext context) : base(context)
    {
    }

    public async Task<{{EntityName}}?> GetByIdWithIncludesAsync(
        Guid id,
        CancellationToken cancellationToken = default)
    {
        return await _dbSet
            .Include(e => e.Category)
            .Include(e => e.Tags)
                .ThenInclude(t => t.Tag)
            .FirstOrDefaultAsync(e => e.Id == id, cancellationToken);
    }

    public async Task<IEnumerable<{{EntityName}}>> GetByCategoryAsync(
        Guid categoryId,
        CancellationToken cancellationToken = default)
    {
        return await _dbSet
            .Where(e => e.CategoryId == categoryId)
            .Include(e => e.Category)
            .OrderBy(e => e.Name)
            .ToListAsync(cancellationToken);
    }

    public async Task<IEnumerable<{{EntityName}}>> GetActiveAsync(
        CancellationToken cancellationToken = default)
    {
        return await _dbSet
            .Where(e => e.IsActive)
            .Include(e => e.Category)
            .OrderBy(e => e.Name)
            .ToListAsync(cancellationToken);
    }

    public async Task<bool> NameExistsAsync(
        string name,
        Guid? excludeId = null,
        CancellationToken cancellationToken = default)
    {
        var query = _dbSet.Where(e =>
            e.Name.ToLower() == name.ToLower());

        if (excludeId.HasValue)
        {
            query = query.Where(e => e.Id != excludeId.Value);
        }

        return await query.AnyAsync(cancellationToken);
    }

    public async Task<IEnumerable<{{EntityName}}>> SearchAsync(
        string searchTerm,
        CancellationToken cancellationToken = default)
    {
        return await _dbSet
            .Where(e =>
                e.Name.Contains(searchTerm) ||
                (e.Description != null && e.Description.Contains(searchTerm)))
            .Include(e => e.Category)
            .OrderBy(e => e.Name)
            .Take(50)
            .ToListAsync(cancellationToken);
    }
}
```

## Generic Repository Base

```csharp
// {{SolutionName}}.Infrastructure/Persistence/Repositories/Repository.cs
using System.Linq.Expressions;
using Microsoft.EntityFrameworkCore;
using {{SolutionName}}.Domain.Common;
using {{SolutionName}}.Domain.Interfaces;

namespace {{SolutionName}}.Infrastructure.Persistence.Repositories;

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
        CancellationToken cancellationToken = default)
    {
        return await _dbSet.FindAsync(
            new object[] { id },
            cancellationToken);
    }

    public virtual async Task<IEnumerable<T>> GetAllAsync(
        CancellationToken cancellationToken = default)
    {
        return await _dbSet.ToListAsync(cancellationToken);
    }

    public virtual async Task<IEnumerable<T>> FindAsync(
        Expression<Func<T, bool>> predicate,
        CancellationToken cancellationToken = default)
    {
        return await _dbSet
            .Where(predicate)
            .ToListAsync(cancellationToken);
    }

    public virtual async Task<T?> FirstOrDefaultAsync(
        Expression<Func<T, bool>> predicate,
        CancellationToken cancellationToken = default)
    {
        return await _dbSet
            .FirstOrDefaultAsync(predicate, cancellationToken);
    }

    public virtual async Task<bool> ExistsAsync(
        Guid id,
        CancellationToken cancellationToken = default)
    {
        return await _dbSet
            .AnyAsync(e => e.Id == id, cancellationToken);
    }

    public virtual async Task<bool> AnyAsync(
        Expression<Func<T, bool>> predicate,
        CancellationToken cancellationToken = default)
    {
        return await _dbSet
            .AnyAsync(predicate, cancellationToken);
    }

    public virtual async Task<int> CountAsync(
        CancellationToken cancellationToken = default)
    {
        return await _dbSet.CountAsync(cancellationToken);
    }

    public virtual async Task<int> CountAsync(
        Expression<Func<T, bool>> predicate,
        CancellationToken cancellationToken = default)
    {
        return await _dbSet.CountAsync(predicate, cancellationToken);
    }

    public virtual async Task AddAsync(
        T entity,
        CancellationToken cancellationToken = default)
    {
        await _dbSet.AddAsync(entity, cancellationToken);
    }

    public virtual async Task AddRangeAsync(
        IEnumerable<T> entities,
        CancellationToken cancellationToken = default)
    {
        await _dbSet.AddRangeAsync(entities, cancellationToken);
    }

    public virtual void Update(T entity)
    {
        _dbSet.Update(entity);
    }

    public virtual void Delete(T entity)
    {
        _dbSet.Remove(entity);
    }

    public virtual void DeleteRange(IEnumerable<T> entities)
    {
        _dbSet.RemoveRange(entities);
    }

    public IQueryable<T> Query()
    {
        return _dbSet.AsQueryable();
    }
}
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{SolutionName}}` | Solution/project name | `MyApp` |
| `{{EntityName}}` | PascalCase entity name | `Product` |
