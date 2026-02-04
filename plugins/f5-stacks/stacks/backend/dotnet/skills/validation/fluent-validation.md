---
name: fluent-validation
description: FluentValidation rules and patterns for ASP.NET Core
applies_to: dotnet
type: skill
---

# FluentValidation

## Overview

FluentValidation is a popular .NET library for building strongly-typed validation rules. It provides a fluent interface for defining validation logic separate from your models.

## Setup

### Installation

```bash
dotnet add package FluentValidation
dotnet add package FluentValidation.DependencyInjectionExtensions
```

### Registration

```csharp
// Program.cs
builder.Services.AddValidatorsFromAssemblyContaining<CreateProductValidator>();

// Or from multiple assemblies
builder.Services.AddValidatorsFromAssemblies(new[]
{
    typeof(Application.DependencyInjection).Assembly,
    typeof(API.DependencyInjection).Assembly
});
```

## Basic Validators

### Simple Validator

```csharp
// Application/Products/Commands/CreateProduct/CreateProductValidator.cs
public class CreateProductValidator : AbstractValidator<CreateProductCommand>
{
    public CreateProductValidator()
    {
        RuleFor(x => x.Name)
            .NotEmpty().WithMessage("Name is required")
            .MaximumLength(200).WithMessage("Name cannot exceed 200 characters");

        RuleFor(x => x.Description)
            .MaximumLength(1000);

        RuleFor(x => x.Price)
            .GreaterThan(0).WithMessage("Price must be greater than zero")
            .PrecisionScale(18, 2, true).WithMessage("Price can have at most 2 decimal places");

        RuleFor(x => x.CategoryId)
            .NotEmpty().WithMessage("Category is required");

        RuleFor(x => x.Sku)
            .NotEmpty()
            .Matches(@"^[A-Z]{3}-\d{4}$")
            .WithMessage("SKU must be in format XXX-0000");
    }
}
```

### Conditional Rules

```csharp
public class UpdateProductValidator : AbstractValidator<UpdateProductCommand>
{
    public UpdateProductValidator()
    {
        RuleFor(x => x.Id)
            .NotEmpty();

        // Only validate if provided
        When(x => !string.IsNullOrEmpty(x.Name), () =>
        {
            RuleFor(x => x.Name)
                .MaximumLength(200);
        });

        // Conditional based on another property
        RuleFor(x => x.SalePrice)
            .LessThan(x => x.Price)
            .When(x => x.IsOnSale)
            .WithMessage("Sale price must be less than regular price");

        // Unless (opposite of When)
        RuleFor(x => x.Stock)
            .GreaterThan(0)
            .Unless(x => x.IsDiscontinued);
    }
}
```

## Built-in Validators

### Common Validators

```csharp
public class UserValidator : AbstractValidator<CreateUserDto>
{
    public UserValidator()
    {
        // String validators
        RuleFor(x => x.Name).NotEmpty();
        RuleFor(x => x.Name).NotNull();
        RuleFor(x => x.Name).Length(2, 100);
        RuleFor(x => x.Name).MinimumLength(2);
        RuleFor(x => x.Name).MaximumLength(100);

        // Email
        RuleFor(x => x.Email).EmailAddress();

        // Comparison
        RuleFor(x => x.Age).GreaterThan(0);
        RuleFor(x => x.Age).GreaterThanOrEqualTo(18);
        RuleFor(x => x.Age).LessThan(120);
        RuleFor(x => x.Age).LessThanOrEqualTo(65);
        RuleFor(x => x.Count).InclusiveBetween(1, 100);
        RuleFor(x => x.Count).ExclusiveBetween(0, 101);

        // Equality
        RuleFor(x => x.Password).Equal(x => x.ConfirmPassword);
        RuleFor(x => x.Status).NotEqual("deleted");

        // Regex
        RuleFor(x => x.Phone).Matches(@"^\+?[\d\s-]+$");

        // Null checks
        RuleFor(x => x.OptionalField).Null();

        // Collection
        RuleFor(x => x.Tags).NotEmpty();

        // Enum
        RuleFor(x => x.Status).IsInEnum();

        // Credit card
        RuleFor(x => x.CardNumber).CreditCard();

        // Precision
        RuleFor(x => x.Price).PrecisionScale(10, 2, true);
    }
}
```

## Custom Validators

### Inline Custom Rule

```csharp
public class OrderValidator : AbstractValidator<CreateOrderDto>
{
    public OrderValidator()
    {
        RuleFor(x => x.Items)
            .Must(items => items != null && items.Count > 0)
            .WithMessage("Order must have at least one item");

        RuleFor(x => x.DeliveryDate)
            .Must(BeAFutureDate)
            .WithMessage("Delivery date must be in the future");

        RuleFor(x => x)
            .Must(HaveValidTotalAmount)
            .WithMessage("Total amount doesn't match items");
    }

    private bool BeAFutureDate(DateTime date)
    {
        return date > DateTime.Today;
    }

    private bool HaveValidTotalAmount(CreateOrderDto order)
    {
        var calculatedTotal = order.Items.Sum(i => i.Price * i.Quantity);
        return Math.Abs(calculatedTotal - order.TotalAmount) < 0.01m;
    }
}
```

### Reusable Custom Validator

```csharp
// Custom validator class
public class FutureDateValidator<T> : PropertyValidator<T, DateTime>
{
    public override string Name => "FutureDateValidator";

    public override bool IsValid(ValidationContext<T> context, DateTime value)
    {
        return value > DateTime.Today;
    }

    protected override string GetDefaultMessageTemplate(string errorCode)
        => "{PropertyName} must be a date in the future";
}

// Extension method
public static class ValidatorExtensions
{
    public static IRuleBuilderOptions<T, DateTime> MustBeFutureDate<T>(
        this IRuleBuilder<T, DateTime> ruleBuilder)
    {
        return ruleBuilder.SetValidator(new FutureDateValidator<T>());
    }

    public static IRuleBuilderOptions<T, string> MustBeValidPhoneNumber<T>(
        this IRuleBuilder<T, string> ruleBuilder)
    {
        return ruleBuilder
            .Matches(@"^\+?[\d\s-]{10,15}$")
            .WithMessage("{PropertyName} is not a valid phone number");
    }
}

// Usage
RuleFor(x => x.DeliveryDate).MustBeFutureDate();
RuleFor(x => x.Phone).MustBeValidPhoneNumber();
```

## Async Validation

```csharp
public class CreateProductValidator : AbstractValidator<CreateProductCommand>
{
    private readonly IProductRepository _repository;

    public CreateProductValidator(IProductRepository repository)
    {
        _repository = repository;

        RuleFor(x => x.Sku)
            .NotEmpty()
            .MustAsync(BeUniqueSku)
            .WithMessage("SKU already exists");

        RuleFor(x => x.CategoryId)
            .MustAsync(CategoryMustExist)
            .WithMessage("Category does not exist");
    }

    private async Task<bool> BeUniqueSku(
        string sku,
        CancellationToken cancellationToken)
    {
        return !await _repository.SkuExistsAsync(sku, cancellationToken);
    }

    private async Task<bool> CategoryMustExist(
        Guid categoryId,
        CancellationToken cancellationToken)
    {
        return await _repository.CategoryExistsAsync(categoryId, cancellationToken);
    }
}
```

## Collection Validation

```csharp
public class OrderValidator : AbstractValidator<CreateOrderDto>
{
    public OrderValidator()
    {
        RuleFor(x => x.Items)
            .NotEmpty()
            .WithMessage("Order must have items");

        RuleForEach(x => x.Items)
            .SetValidator(new OrderItemValidator());

        // Or inline
        RuleForEach(x => x.Items).ChildRules(item =>
        {
            item.RuleFor(x => x.ProductId).NotEmpty();
            item.RuleFor(x => x.Quantity).GreaterThan(0);
        });
    }
}

public class OrderItemValidator : AbstractValidator<OrderItemDto>
{
    public OrderItemValidator()
    {
        RuleFor(x => x.ProductId)
            .NotEmpty();

        RuleFor(x => x.Quantity)
            .GreaterThan(0)
            .LessThanOrEqualTo(100);

        RuleFor(x => x.Price)
            .GreaterThan(0);
    }
}
```

## MediatR Pipeline Integration

```csharp
// Validation pipeline behavior
public class ValidationBehavior<TRequest, TResponse>
    : IPipelineBehavior<TRequest, TResponse>
    where TRequest : notnull
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
        if (!_validators.Any())
            return await next();

        var context = new ValidationContext<TRequest>(request);

        var results = await Task.WhenAll(
            _validators.Select(v => v.ValidateAsync(context, cancellationToken)));

        var failures = results
            .SelectMany(r => r.Errors)
            .Where(f => f != null)
            .ToList();

        if (failures.Count > 0)
            throw new ValidationException(failures);

        return await next();
    }
}

// Registration
builder.Services.AddTransient(
    typeof(IPipelineBehavior<,>),
    typeof(ValidationBehavior<,>));
```

## Best Practices

| Practice | Recommendation |
|----------|----------------|
| Location | Place validators near commands/queries |
| Naming | Use `{Command}Validator` naming |
| Async | Use async for DB validations |
| Reuse | Create extension methods for common rules |
| Messages | Provide clear, actionable error messages |
| Testing | Unit test validators thoroughly |

## Related Skills

- `skills/validation/model-validation.md`
- `skills/error-handling/problem-details.md`
