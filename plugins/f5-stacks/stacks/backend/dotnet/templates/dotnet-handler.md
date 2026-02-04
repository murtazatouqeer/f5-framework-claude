---
name: dotnet-handler
description: Template for MediatR command and query handlers
applies_to: dotnet
type: template
---

# CQRS Handler Template

## Command

```csharp
// {{SolutionName}}.Application/{{EntityName}}s/Commands/Create{{EntityName}}/Create{{EntityName}}Command.cs
using MediatR;
using {{SolutionName}}.Application.DTOs;

namespace {{SolutionName}}.Application.{{EntityName}}s.Commands.Create{{EntityName}};

public record Create{{EntityName}}Command(
    string Name,
    string? Description,
    decimal Price,
    Guid CategoryId
) : IRequest<{{EntityName}}Dto>;
```

## Command Handler

```csharp
// {{SolutionName}}.Application/{{EntityName}}s/Commands/Create{{EntityName}}/Create{{EntityName}}CommandHandler.cs
using AutoMapper;
using MediatR;
using Microsoft.Extensions.Logging;
using {{SolutionName}}.Application.DTOs;
using {{SolutionName}}.Domain.Entities;
using {{SolutionName}}.Domain.Interfaces;

namespace {{SolutionName}}.Application.{{EntityName}}s.Commands.Create{{EntityName}};

public class Create{{EntityName}}CommandHandler
    : IRequestHandler<Create{{EntityName}}Command, {{EntityName}}Dto>
{
    private readonly I{{EntityName}}Repository _repository;
    private readonly IUnitOfWork _unitOfWork;
    private readonly IMapper _mapper;
    private readonly ILogger<Create{{EntityName}}CommandHandler> _logger;

    public Create{{EntityName}}CommandHandler(
        I{{EntityName}}Repository repository,
        IUnitOfWork unitOfWork,
        IMapper mapper,
        ILogger<Create{{EntityName}}CommandHandler> logger)
    {
        _repository = repository;
        _unitOfWork = unitOfWork;
        _mapper = mapper;
        _logger = logger;
    }

    public async Task<{{EntityName}}Dto> Handle(
        Create{{EntityName}}Command request,
        CancellationToken cancellationToken)
    {
        // Create domain entity
        var entity = {{EntityName}}.Create(
            request.Name,
            request.Description,
            request.Price,
            request.CategoryId);

        // Persist
        await _repository.AddAsync(entity, cancellationToken);
        await _unitOfWork.SaveChangesAsync(cancellationToken);

        _logger.LogInformation(
            "{{EntityName}} created with ID {Id}",
            entity.Id);

        return _mapper.Map<{{EntityName}}Dto>(entity);
    }
}
```

## Command Validator

```csharp
// {{SolutionName}}.Application/{{EntityName}}s/Commands/Create{{EntityName}}/Create{{EntityName}}CommandValidator.cs
using FluentValidation;
using {{SolutionName}}.Domain.Interfaces;

namespace {{SolutionName}}.Application.{{EntityName}}s.Commands.Create{{EntityName}};

public class Create{{EntityName}}CommandValidator
    : AbstractValidator<Create{{EntityName}}Command>
{
    private readonly I{{EntityName}}Repository _repository;

    public Create{{EntityName}}CommandValidator(I{{EntityName}}Repository repository)
    {
        _repository = repository;

        RuleFor(x => x.Name)
            .NotEmpty().WithMessage("Name is required")
            .MaximumLength(200).WithMessage("Name cannot exceed 200 characters")
            .MustAsync(BeUniqueName).WithMessage("Name already exists");

        RuleFor(x => x.Description)
            .MaximumLength(1000).WithMessage("Description cannot exceed 1000 characters");

        RuleFor(x => x.Price)
            .GreaterThan(0).WithMessage("Price must be greater than 0");

        RuleFor(x => x.CategoryId)
            .NotEmpty().WithMessage("Category is required");
    }

    private async Task<bool> BeUniqueName(
        string name,
        CancellationToken cancellationToken)
    {
        return !await _repository.NameExistsAsync(name, null, cancellationToken);
    }
}
```

## Query

```csharp
// {{SolutionName}}.Application/{{EntityName}}s/Queries/Get{{EntityName}}ById/Get{{EntityName}}ByIdQuery.cs
using MediatR;
using {{SolutionName}}.Application.DTOs;

namespace {{SolutionName}}.Application.{{EntityName}}s.Queries.Get{{EntityName}}ById;

public record Get{{EntityName}}ByIdQuery(Guid Id) : IRequest<{{EntityName}}Dto?>;
```

## Query Handler

```csharp
// {{SolutionName}}.Application/{{EntityName}}s/Queries/Get{{EntityName}}ById/Get{{EntityName}}ByIdQueryHandler.cs
using AutoMapper;
using MediatR;
using {{SolutionName}}.Application.DTOs;
using {{SolutionName}}.Domain.Interfaces;

namespace {{SolutionName}}.Application.{{EntityName}}s.Queries.Get{{EntityName}}ById;

public class Get{{EntityName}}ByIdQueryHandler
    : IRequestHandler<Get{{EntityName}}ByIdQuery, {{EntityName}}Dto?>
{
    private readonly I{{EntityName}}Repository _repository;
    private readonly IMapper _mapper;

    public Get{{EntityName}}ByIdQueryHandler(
        I{{EntityName}}Repository repository,
        IMapper mapper)
    {
        _repository = repository;
        _mapper = mapper;
    }

    public async Task<{{EntityName}}Dto?> Handle(
        Get{{EntityName}}ByIdQuery request,
        CancellationToken cancellationToken)
    {
        var entity = await _repository.GetByIdWithIncludesAsync(
            request.Id,
            cancellationToken);

        return entity is null
            ? null
            : _mapper.Map<{{EntityName}}Dto>(entity);
    }
}
```

## Paginated Query

```csharp
// Get{{EntityName}}sQuery.cs
public record Get{{EntityName}}sQuery(
    string? Search,
    Guid? CategoryId,
    bool? IsActive,
    int PageNumber = 1,
    int PageSize = 10
) : IRequest<PaginatedList<{{EntityName}}Dto>>;

// Get{{EntityName}}sQueryHandler.cs
public class Get{{EntityName}}sQueryHandler
    : IRequestHandler<Get{{EntityName}}sQuery, PaginatedList<{{EntityName}}Dto>>
{
    private readonly I{{EntityName}}Repository _repository;
    private readonly IMapper _mapper;

    public Get{{EntityName}}sQueryHandler(
        I{{EntityName}}Repository repository,
        IMapper mapper)
    {
        _repository = repository;
        _mapper = mapper;
    }

    public async Task<PaginatedList<{{EntityName}}Dto>> Handle(
        Get{{EntityName}}sQuery request,
        CancellationToken cancellationToken)
    {
        var query = _repository.Query();

        // Apply filters
        if (!string.IsNullOrEmpty(request.Search))
        {
            query = query.Where(x =>
                x.Name.Contains(request.Search) ||
                (x.Description != null && x.Description.Contains(request.Search)));
        }

        if (request.CategoryId.HasValue)
        {
            query = query.Where(x => x.CategoryId == request.CategoryId.Value);
        }

        if (request.IsActive.HasValue)
        {
            query = query.Where(x => x.IsActive == request.IsActive.Value);
        }

        // Order and paginate
        return await query
            .OrderBy(x => x.Name)
            .ProjectTo<{{EntityName}}Dto>(_mapper.ConfigurationProvider)
            .ToPaginatedListAsync(
                request.PageNumber,
                request.PageSize,
                cancellationToken);
    }
}
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{SolutionName}}` | Solution/project name | `MyApp` |
| `{{EntityName}}` | PascalCase entity name | `Product` |
