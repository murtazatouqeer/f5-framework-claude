---
name: dotnet-service
description: Template for service layer interface and implementation
applies_to: dotnet
type: template
---

# ASP.NET Core Service Template

## Service Interface

```csharp
// {{SolutionName}}.Application/Interfaces/I{{EntityName}}Service.cs
using {{SolutionName}}.Application.DTOs;

namespace {{SolutionName}}.Application.Interfaces;

public interface I{{EntityName}}Service
{
    Task<IEnumerable<{{EntityName}}Dto>> GetAllAsync(
        {{EntityName}}FilterDto? filter = null,
        CancellationToken cancellationToken = default);

    Task<PaginatedList<{{EntityName}}Dto>> GetPagedAsync(
        int pageNumber,
        int pageSize,
        {{EntityName}}FilterDto? filter = null,
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

    Task<bool> ExistsAsync(
        Guid id,
        CancellationToken cancellationToken = default);
}
```

## Service Implementation

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
        {{EntityName}}FilterDto? filter = null,
        CancellationToken cancellationToken = default)
    {
        var entities = await _repository.GetAllAsync(filter, cancellationToken);
        return _mapper.Map<IEnumerable<{{EntityName}}Dto>>(entities);
    }

    public async Task<PaginatedList<{{EntityName}}Dto>> GetPagedAsync(
        int pageNumber,
        int pageSize,
        {{EntityName}}FilterDto? filter = null,
        CancellationToken cancellationToken = default)
    {
        var query = _repository.Query();

        // Apply filters
        if (filter is not null)
        {
            if (!string.IsNullOrEmpty(filter.Search))
            {
                query = query.Where(x =>
                    x.Name.Contains(filter.Search));
            }

            if (filter.IsActive.HasValue)
            {
                query = query.Where(x => x.IsActive == filter.IsActive.Value);
            }
        }

        return await query
            .OrderBy(x => x.Name)
            .ProjectTo<{{EntityName}}Dto>(_mapper.ConfigurationProvider)
            .ToPaginatedListAsync(pageNumber, pageSize, cancellationToken);
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

    public async Task<bool> ExistsAsync(
        Guid id,
        CancellationToken cancellationToken = default)
    {
        return await _repository.ExistsAsync(id, cancellationToken);
    }
}
```

## DI Registration

```csharp
// Program.cs or DependencyInjection.cs
services.AddScoped<I{{EntityName}}Service, {{EntityName}}Service>();
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{SolutionName}}` | Solution/project name | `MyApp` |
| `{{EntityName}}` | PascalCase entity name | `Product` |
