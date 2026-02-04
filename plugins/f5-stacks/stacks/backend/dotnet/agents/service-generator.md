---
name: dotnet-service-generator
description: Generates service interfaces and implementations following Clean Architecture
triggers:
  - create service
  - generate service
  - add service
  - dotnet service
---

# ASP.NET Core Service Generator

## Purpose

Generate service layer with interface and implementation following Clean Architecture, with proper validation, mapping, and error handling.

## Required Context

Before generating, gather:
1. **Entity Name**: PascalCase name (e.g., `Product`)
2. **Operations**: Required service methods
3. **Repository**: Repository interface to use
4. **Validation**: Validation requirements

## Generation Template

### Service Interface

```csharp
// {{SolutionName}}.Application/Interfaces/I{{EntityName}}Service.cs
using {{SolutionName}}.Application.DTOs;

namespace {{SolutionName}}.Application.Interfaces;

public interface I{{EntityName}}Service
{
    Task<IEnumerable<{{EntityName}}Dto>> GetAllAsync(
        {{EntityName}}FilterDto filter,
        CancellationToken cancellationToken = default);

    Task<{{EntityName}}Dto?> GetByIdAsync(
        Guid id,
        CancellationToken cancellationToken = default);

    Task<{{EntityName}}Dto> CreateAsync(
        Create{{EntityName}}Dto dto,
        CancellationToken cancellationToken = default);

    Task<{{EntityName}}Dto?> UpdateAsync(
        Guid id,
        Update{{EntityName}}Dto dto,
        CancellationToken cancellationToken = default);

    Task<bool> DeleteAsync(
        Guid id,
        CancellationToken cancellationToken = default);
}
```

### Service Implementation

```csharp
// {{SolutionName}}.Application/Services/{{EntityName}}Service.cs
using AutoMapper;
using Microsoft.Extensions.Logging;
using {{SolutionName}}.Application.DTOs;
using {{SolutionName}}.Application.Interfaces;
using {{SolutionName}}.Domain.Entities;
using {{SolutionName}}.Domain.Interfaces;

namespace {{SolutionName}}.Application.Services;

public class {{EntityName}}Service : I{{EntityName}}Service
{
    private readonly I{{EntityName}}Repository _repository;
    private readonly IUnitOfWork _unitOfWork;
    private readonly IMapper _mapper;
    private readonly ILogger<{{EntityName}}Service> _logger;

    public {{EntityName}}Service(
        I{{EntityName}}Repository repository,
        IUnitOfWork unitOfWork,
        IMapper mapper,
        ILogger<{{EntityName}}Service> logger)
    {
        _repository = repository;
        _unitOfWork = unitOfWork;
        _mapper = mapper;
        _logger = logger;
    }

    public async Task<IEnumerable<{{EntityName}}Dto>> GetAllAsync(
        {{EntityName}}FilterDto filter,
        CancellationToken cancellationToken = default)
    {
        var entities = await _repository.GetAllAsync(filter, cancellationToken);
        return _mapper.Map<IEnumerable<{{EntityName}}Dto>>(entities);
    }

    public async Task<{{EntityName}}Dto?> GetByIdAsync(
        Guid id,
        CancellationToken cancellationToken = default)
    {
        var entity = await _repository.GetByIdAsync(id, cancellationToken);
        return entity is null ? null : _mapper.Map<{{EntityName}}Dto>(entity);
    }

    public async Task<{{EntityName}}Dto> CreateAsync(
        Create{{EntityName}}Dto dto,
        CancellationToken cancellationToken = default)
    {
        var entity = _mapper.Map<{{EntityName}}>(dto);

        await _repository.AddAsync(entity, cancellationToken);
        await _unitOfWork.SaveChangesAsync(cancellationToken);

        _logger.LogInformation("{{EntityName}} created with ID {Id}", entity.Id);

        return _mapper.Map<{{EntityName}}Dto>(entity);
    }

    public async Task<{{EntityName}}Dto?> UpdateAsync(
        Guid id,
        Update{{EntityName}}Dto dto,
        CancellationToken cancellationToken = default)
    {
        var entity = await _repository.GetByIdAsync(id, cancellationToken);

        if (entity is null)
            return null;

        _mapper.Map(dto, entity);

        _repository.Update(entity);
        await _unitOfWork.SaveChangesAsync(cancellationToken);

        _logger.LogInformation("{{EntityName}} updated with ID {Id}", id);

        return _mapper.Map<{{EntityName}}Dto>(entity);
    }

    public async Task<bool> DeleteAsync(
        Guid id,
        CancellationToken cancellationToken = default)
    {
        var entity = await _repository.GetByIdAsync(id, cancellationToken);

        if (entity is null)
            return false;

        _repository.Delete(entity);
        await _unitOfWork.SaveChangesAsync(cancellationToken);

        _logger.LogInformation("{{EntityName}} deleted with ID {Id}", id);

        return true;
    }
}
```

## DI Registration

```csharp
// In Program.cs or ServiceCollectionExtensions.cs
services.AddScoped<I{{EntityName}}Service, {{EntityName}}Service>();
```

## Generation Checklist

- [ ] Interface in Application layer
- [ ] Implementation in Application layer
- [ ] Repository dependency injection
- [ ] UnitOfWork for transactions
- [ ] AutoMapper for DTO mapping
- [ ] Logging for operations
- [ ] CancellationToken support
- [ ] Null checks and error handling

## Related Templates

- `templates/dotnet-service.md` - Full service template
- `templates/dotnet-repository.md` - Repository pattern
