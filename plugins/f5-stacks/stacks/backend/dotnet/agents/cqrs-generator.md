---
name: dotnet-cqrs-generator
description: Generates CQRS Commands, Queries, and Handlers using MediatR
triggers:
  - create command
  - create query
  - generate handler
  - cqrs
  - mediatr
---

# CQRS/MediatR Generator

## Purpose

Generate Commands, Queries, and Handlers following CQRS pattern with MediatR for clean separation of read and write operations.

## Required Context

Before generating, gather:
1. **Operation Type**: Command (write) or Query (read)
2. **Entity Name**: Target entity
3. **Action**: Specific operation (Create, Update, Delete, Get, List)
4. **Parameters**: Required input data

## Command Generation Template

### Create Command

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

### Command Handler

```csharp
// {{SolutionName}}.Application/{{EntityName}}s/Commands/Create{{EntityName}}/Create{{EntityName}}CommandHandler.cs
using AutoMapper;
using MediatR;
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

    public Create{{EntityName}}CommandHandler(
        I{{EntityName}}Repository repository,
        IUnitOfWork unitOfWork,
        IMapper mapper)
    {
        _repository = repository;
        _unitOfWork = unitOfWork;
        _mapper = mapper;
    }

    public async Task<{{EntityName}}Dto> Handle(
        Create{{EntityName}}Command request,
        CancellationToken cancellationToken)
    {
        var entity = {{EntityName}}.Create(
            request.Name,
            request.Description,
            request.Price,
            request.CategoryId);

        await _repository.AddAsync(entity, cancellationToken);
        await _unitOfWork.SaveChangesAsync(cancellationToken);

        return _mapper.Map<{{EntityName}}Dto>(entity);
    }
}
```

### Command Validator

```csharp
// {{SolutionName}}.Application/{{EntityName}}s/Commands/Create{{EntityName}}/Create{{EntityName}}CommandValidator.cs
using FluentValidation;

namespace {{SolutionName}}.Application.{{EntityName}}s.Commands.Create{{EntityName}};

public class Create{{EntityName}}CommandValidator
    : AbstractValidator<Create{{EntityName}}Command>
{
    public Create{{EntityName}}CommandValidator()
    {
        RuleFor(x => x.Name)
            .NotEmpty()
            .MaximumLength(200);

        RuleFor(x => x.Description)
            .MaximumLength(1000);

        RuleFor(x => x.Price)
            .GreaterThanOrEqualTo(0);

        RuleFor(x => x.CategoryId)
            .NotEmpty();
    }
}
```

## Query Generation Template

### Get Query

```csharp
// {{SolutionName}}.Application/{{EntityName}}s/Queries/Get{{EntityName}}ById/Get{{EntityName}}ByIdQuery.cs
using MediatR;
using {{SolutionName}}.Application.DTOs;

namespace {{SolutionName}}.Application.{{EntityName}}s.Queries.Get{{EntityName}}ById;

public record Get{{EntityName}}ByIdQuery(Guid Id) : IRequest<{{EntityName}}Dto?>;
```

### Query Handler

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
        var entity = await _repository.GetByIdAsync(
            request.Id,
            cancellationToken);

        return entity is null
            ? null
            : _mapper.Map<{{EntityName}}Dto>(entity);
    }
}
```

## List Query with Pagination

```csharp
// Get{{EntityName}}sQuery.cs
public record Get{{EntityName}}sQuery(
    string? SearchTerm,
    int PageNumber = 1,
    int PageSize = 10
) : IRequest<PaginatedList<{{EntityName}}Dto>>;

// Get{{EntityName}}sQueryHandler.cs
public class Get{{EntityName}}sQueryHandler
    : IRequestHandler<Get{{EntityName}}sQuery, PaginatedList<{{EntityName}}Dto>>
{
    public async Task<PaginatedList<{{EntityName}}Dto>> Handle(
        Get{{EntityName}}sQuery request,
        CancellationToken cancellationToken)
    {
        var query = _repository.Query();

        if (!string.IsNullOrEmpty(request.SearchTerm))
        {
            query = query.Where(x =>
                x.Name.Contains(request.SearchTerm));
        }

        return await query
            .ProjectTo<{{EntityName}}Dto>(_mapper.ConfigurationProvider)
            .ToPaginatedListAsync(
                request.PageNumber,
                request.PageSize,
                cancellationToken);
    }
}
```

## Pipeline Behaviors

### Validation Behavior

```csharp
// {{SolutionName}}.Application/Common/Behaviors/ValidationBehavior.cs
using FluentValidation;
using MediatR;

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
        if (_validators.Any())
        {
            var context = new ValidationContext<TRequest>(request);

            var results = await Task.WhenAll(
                _validators.Select(v => v.ValidateAsync(context, cancellationToken)));

            var failures = results
                .SelectMany(r => r.Errors)
                .Where(f => f != null)
                .ToList();

            if (failures.Count > 0)
                throw new ValidationException(failures);
        }

        return await next();
    }
}
```

## Generation Checklist

- [ ] Command/Query as record type
- [ ] Handler implements IRequestHandler
- [ ] Validator using FluentValidation
- [ ] Proper folder structure per feature
- [ ] CancellationToken passed through
- [ ] AutoMapper for projections
- [ ] Pipeline behaviors registered

## Related Templates

- `templates/dotnet-handler.md` - Handler template
- `templates/dotnet-validator.md` - Validator template
