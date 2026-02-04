---
name: dotnet-validator
description: Template for FluentValidation validators
applies_to: dotnet
type: template
---

# FluentValidation Template

## Create Validator

```csharp
// {{SolutionName}}.Application/{{EntityName}}s/Commands/Create{{EntityName}}/Create{{EntityName}}CommandValidator.cs
using FluentValidation;
using {{SolutionName}}.Domain.Interfaces;

namespace {{SolutionName}}.Application.{{EntityName}}s.Commands.Create{{EntityName}};

public class Create{{EntityName}}CommandValidator
    : AbstractValidator<Create{{EntityName}}Command>
{
    private readonly I{{EntityName}}Repository _{{entityName}}Repository;
    private readonly ICategoryRepository _categoryRepository;

    public Create{{EntityName}}CommandValidator(
        I{{EntityName}}Repository {{entityName}}Repository,
        ICategoryRepository categoryRepository)
    {
        _{{entityName}}Repository = {{entityName}}Repository;
        _categoryRepository = categoryRepository;

        // Name validation
        RuleFor(x => x.Name)
            .NotEmpty()
                .WithMessage("Name is required")
            .MaximumLength(200)
                .WithMessage("Name cannot exceed 200 characters")
            .MustAsync(BeUniqueName)
                .WithMessage("A {{entityName}} with this name already exists");

        // Description validation
        RuleFor(x => x.Description)
            .MaximumLength(1000)
                .WithMessage("Description cannot exceed 1000 characters");

        // Price validation
        RuleFor(x => x.Price)
            .GreaterThan(0)
                .WithMessage("Price must be greater than 0")
            .PrecisionScale(18, 2, true)
                .WithMessage("Price can have at most 2 decimal places");

        // Category validation
        RuleFor(x => x.CategoryId)
            .NotEmpty()
                .WithMessage("Category is required")
            .MustAsync(CategoryExists)
                .WithMessage("Category does not exist");

        // Conditional validation
        When(x => x.Stock.HasValue, () =>
        {
            RuleFor(x => x.Stock!.Value)
                .GreaterThanOrEqualTo(0)
                    .WithMessage("Stock cannot be negative");
        });

        // Collection validation
        When(x => x.TagIds is not null && x.TagIds.Any(), () =>
        {
            RuleForEach(x => x.TagIds)
                .NotEmpty()
                    .WithMessage("Tag ID cannot be empty");
        });
    }

    private async Task<bool> BeUniqueName(
        string name,
        CancellationToken cancellationToken)
    {
        return !await _{{entityName}}Repository.NameExistsAsync(
            name,
            null,
            cancellationToken);
    }

    private async Task<bool> CategoryExists(
        Guid categoryId,
        CancellationToken cancellationToken)
    {
        return await _categoryRepository.ExistsAsync(
            categoryId,
            cancellationToken);
    }
}
```

## Update Validator

```csharp
// {{SolutionName}}.Application/{{EntityName}}s/Commands/Update{{EntityName}}/Update{{EntityName}}CommandValidator.cs
using FluentValidation;
using {{SolutionName}}.Domain.Interfaces;

namespace {{SolutionName}}.Application.{{EntityName}}s.Commands.Update{{EntityName}};

public class Update{{EntityName}}CommandValidator
    : AbstractValidator<Update{{EntityName}}Command>
{
    private readonly I{{EntityName}}Repository _repository;

    public Update{{EntityName}}CommandValidator(
        I{{EntityName}}Repository repository)
    {
        _repository = repository;

        RuleFor(x => x.Id)
            .NotEmpty()
                .WithMessage("ID is required")
            .MustAsync({{EntityName}}Exists)
                .WithMessage("{{EntityName}} not found");

        // Only validate if provided (partial update)
        When(x => !string.IsNullOrEmpty(x.Name), () =>
        {
            RuleFor(x => x.Name)
                .MaximumLength(200)
                    .WithMessage("Name cannot exceed 200 characters")
                .MustAsync(BeUniqueNameForUpdate)
                    .WithMessage("A {{entityName}} with this name already exists");
        });

        When(x => x.Description is not null, () =>
        {
            RuleFor(x => x.Description)
                .MaximumLength(1000)
                    .WithMessage("Description cannot exceed 1000 characters");
        });

        When(x => x.Price.HasValue, () =>
        {
            RuleFor(x => x.Price!.Value)
                .GreaterThan(0)
                    .WithMessage("Price must be greater than 0");
        });

        When(x => x.Stock.HasValue, () =>
        {
            RuleFor(x => x.Stock!.Value)
                .GreaterThanOrEqualTo(0)
                    .WithMessage("Stock cannot be negative");
        });
    }

    private async Task<bool> {{EntityName}}Exists(
        Guid id,
        CancellationToken cancellationToken)
    {
        return await _repository.ExistsAsync(id, cancellationToken);
    }

    private async Task<bool> BeUniqueNameForUpdate(
        Update{{EntityName}}Command command,
        string? name,
        CancellationToken cancellationToken)
    {
        if (string.IsNullOrEmpty(name))
            return true;

        return !await _repository.NameExistsAsync(
            name,
            command.Id,
            cancellationToken);
    }
}
```

## DTO Validator

```csharp
// {{SolutionName}}.Application/DTOs/Validators/Create{{EntityName}}DtoValidator.cs
using FluentValidation;

namespace {{SolutionName}}.Application.DTOs.Validators;

public class Create{{EntityName}}DtoValidator
    : AbstractValidator<Create{{EntityName}}Dto>
{
    public Create{{EntityName}}DtoValidator()
    {
        RuleFor(x => x.Name)
            .NotEmpty()
            .MaximumLength(200);

        RuleFor(x => x.Description)
            .MaximumLength(1000);

        RuleFor(x => x.Price)
            .GreaterThan(0)
            .PrecisionScale(18, 2, true);

        RuleFor(x => x.CategoryId)
            .NotEmpty();
    }
}
```

## Custom Validation Extensions

```csharp
// {{SolutionName}}.Application/Common/Validation/ValidationExtensions.cs
using FluentValidation;

namespace {{SolutionName}}.Application.Common.Validation;

public static class ValidationExtensions
{
    public static IRuleBuilderOptions<T, string> MustBeValidSlug<T>(
        this IRuleBuilder<T, string> ruleBuilder)
    {
        return ruleBuilder
            .Matches(@"^[a-z0-9]+(?:-[a-z0-9]+)*$")
            .WithMessage("{PropertyName} must be a valid slug (lowercase letters, numbers, and hyphens)");
    }

    public static IRuleBuilderOptions<T, string?> MustBeValidPhoneNumber<T>(
        this IRuleBuilder<T, string?> ruleBuilder)
    {
        return ruleBuilder
            .Matches(@"^\+?[\d\s-]{10,15}$")
            .When(x => !string.IsNullOrEmpty(x as string))
            .WithMessage("{PropertyName} is not a valid phone number");
    }

    public static IRuleBuilderOptions<T, decimal> MustBeCurrency<T>(
        this IRuleBuilder<T, decimal> ruleBuilder)
    {
        return ruleBuilder
            .GreaterThanOrEqualTo(0)
            .PrecisionScale(18, 2, true)
            .WithMessage("{PropertyName} must be a valid currency value");
    }

    public static IRuleBuilderOptions<T, Guid> MustBeNonEmptyGuid<T>(
        this IRuleBuilder<T, Guid> ruleBuilder)
    {
        return ruleBuilder
            .NotEqual(Guid.Empty)
            .WithMessage("{PropertyName} must be a valid ID");
    }
}
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{SolutionName}}` | Solution/project name | `MyApp` |
| `{{EntityName}}` | PascalCase entity name | `Product` |
| `{{entityName}}` | camelCase entity name | `product` |
