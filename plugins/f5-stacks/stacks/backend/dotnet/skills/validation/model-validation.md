---
name: model-validation
description: Data annotations and model validation in ASP.NET Core
applies_to: dotnet
type: skill
---

# Model Validation

## Overview

ASP.NET Core provides built-in model validation using data annotations. While FluentValidation is recommended for complex scenarios, data annotations work well for simple validations.

## Built-in Attributes

### Common Validation Attributes

```csharp
// DTOs/CreateProductDto.cs
public class CreateProductDto
{
    [Required(ErrorMessage = "Name is required")]
    [StringLength(200, MinimumLength = 2,
        ErrorMessage = "Name must be between 2 and 200 characters")]
    public string Name { get; set; } = string.Empty;

    [StringLength(1000)]
    public string? Description { get; set; }

    [Required]
    [Range(0.01, double.MaxValue,
        ErrorMessage = "Price must be greater than 0")]
    public decimal Price { get; set; }

    [Required]
    public Guid CategoryId { get; set; }

    [RegularExpression(@"^[A-Z]{3}-\d{4}$",
        ErrorMessage = "SKU must be in format XXX-0000")]
    public string? Sku { get; set; }

    [EmailAddress]
    public string? ContactEmail { get; set; }

    [Phone]
    public string? ContactPhone { get; set; }

    [Url]
    public string? Website { get; set; }

    [CreditCard]
    public string? PaymentCard { get; set; }

    [Compare(nameof(ConfirmEmail),
        ErrorMessage = "Emails must match")]
    public string? Email { get; set; }

    public string? ConfirmEmail { get; set; }
}
```

### Validation Attributes Reference

```csharp
// String validation
[Required]                              // Not null or empty
[StringLength(100)]                     // Max length
[StringLength(100, MinimumLength = 5)]  // Min and max length
[MinLength(5)]                          // Minimum length
[MaxLength(100)]                        // Maximum length
[EmailAddress]                          // Email format
[Phone]                                 // Phone format
[Url]                                   // URL format
[RegularExpression(@"pattern")]         // Regex match

// Numeric validation
[Range(1, 100)]                         // Inclusive range
[Range(typeof(decimal), "0.01", "999999.99")]

// Comparison
[Compare("OtherProperty")]              // Must equal
[CreditCard]                            // Credit card format

// Data type
[DataType(DataType.Password)]
[DataType(DataType.Date)]
[DataType(DataType.Currency)]

// Custom error messages
[Required(ErrorMessage = "Please enter {0}")]
```

## Custom Validation Attribute

### Simple Custom Attribute

```csharp
// Validation/FutureDateAttribute.cs
public class FutureDateAttribute : ValidationAttribute
{
    public FutureDateAttribute()
    {
        ErrorMessage = "{0} must be a date in the future";
    }

    public override bool IsValid(object? value)
    {
        if (value is null)
            return true; // Let [Required] handle null

        if (value is DateTime dateTime)
            return dateTime > DateTime.Today;

        return false;
    }
}

// Usage
[FutureDate]
public DateTime DeliveryDate { get; set; }
```

### Attribute with Parameters

```csharp
public class MinimumAgeAttribute : ValidationAttribute
{
    private readonly int _minimumAge;

    public MinimumAgeAttribute(int minimumAge)
    {
        _minimumAge = minimumAge;
        ErrorMessage = $"Must be at least {minimumAge} years old";
    }

    protected override ValidationResult? IsValid(
        object? value,
        ValidationContext validationContext)
    {
        if (value is null)
            return ValidationResult.Success;

        if (value is DateTime dateOfBirth)
        {
            var age = DateTime.Today.Year - dateOfBirth.Year;
            if (dateOfBirth.Date > DateTime.Today.AddYears(-age))
                age--;

            if (age >= _minimumAge)
                return ValidationResult.Success;

            return new ValidationResult(
                ErrorMessage,
                new[] { validationContext.MemberName! });
        }

        return new ValidationResult("Invalid date format");
    }
}

// Usage
[MinimumAge(18)]
public DateTime DateOfBirth { get; set; }
```

### Cross-Property Validation

```csharp
public class DateRangeAttribute : ValidationAttribute
{
    private readonly string _startDatePropertyName;

    public DateRangeAttribute(string startDatePropertyName)
    {
        _startDatePropertyName = startDatePropertyName;
        ErrorMessage = "End date must be after start date";
    }

    protected override ValidationResult? IsValid(
        object? value,
        ValidationContext validationContext)
    {
        if (value is null)
            return ValidationResult.Success;

        var startDateProperty = validationContext.ObjectType
            .GetProperty(_startDatePropertyName);

        if (startDateProperty is null)
            throw new ArgumentException($"Property {_startDatePropertyName} not found");

        var startDate = (DateTime?)startDateProperty
            .GetValue(validationContext.ObjectInstance);

        if (startDate is null)
            return ValidationResult.Success;

        if (value is DateTime endDate && endDate > startDate)
            return ValidationResult.Success;

        return new ValidationResult(
            ErrorMessage,
            new[] { validationContext.MemberName! });
    }
}

// Usage
public class EventDto
{
    public DateTime StartDate { get; set; }

    [DateRange(nameof(StartDate))]
    public DateTime EndDate { get; set; }
}
```

## IValidatableObject

```csharp
// Complex cross-property validation
public class OrderDto : IValidatableObject
{
    public decimal SubTotal { get; set; }
    public decimal Tax { get; set; }
    public decimal Total { get; set; }
    public List<OrderItemDto> Items { get; set; } = new();

    public IEnumerable<ValidationResult> Validate(
        ValidationContext validationContext)
    {
        // Validate total calculation
        var calculatedTotal = SubTotal + Tax;
        if (Math.Abs(Total - calculatedTotal) > 0.01m)
        {
            yield return new ValidationResult(
                "Total must equal SubTotal + Tax",
                new[] { nameof(Total) });
        }

        // Validate items match subtotal
        var itemsTotal = Items.Sum(i => i.Price * i.Quantity);
        if (Math.Abs(SubTotal - itemsTotal) > 0.01m)
        {
            yield return new ValidationResult(
                "SubTotal must match sum of items",
                new[] { nameof(SubTotal) });
        }

        // Conditional validation
        if (Items.Any(i => i.IsGift) && Tax > 0)
        {
            yield return new ValidationResult(
                "Gift items should not have tax",
                new[] { nameof(Tax) });
        }
    }
}
```

## Controller Integration

### Automatic Validation

```csharp
// [ApiController] enables automatic validation
[ApiController]
[Route("api/[controller]")]
public class ProductsController : ControllerBase
{
    // ModelState is automatically validated
    // Returns 400 if invalid
    [HttpPost]
    public IActionResult Create([FromBody] CreateProductDto dto)
    {
        // If we reach here, model is valid
        return Ok();
    }
}
```

### Manual Validation

```csharp
// Without [ApiController]
[Route("api/[controller]")]
public class ProductsController : ControllerBase
{
    [HttpPost]
    public IActionResult Create([FromBody] CreateProductDto dto)
    {
        if (!ModelState.IsValid)
        {
            return BadRequest(ModelState);
        }

        // Process valid request
        return Ok();
    }
}
```

### Custom Validation Response

```csharp
// Program.cs
builder.Services.AddControllers()
    .ConfigureApiBehaviorOptions(options =>
    {
        options.InvalidModelStateResponseFactory = context =>
        {
            var errors = context.ModelState
                .Where(e => e.Value?.Errors.Count > 0)
                .ToDictionary(
                    e => e.Key,
                    e => e.Value!.Errors.Select(er => er.ErrorMessage).ToArray());

            var response = new
            {
                Success = false,
                Message = "Validation failed",
                Errors = errors
            };

            return new BadRequestObjectResult(response);
        };
    });
```

## When to Use What

| Scenario | Recommendation |
|----------|----------------|
| Simple DTOs | Data annotations |
| Complex validation | FluentValidation |
| Async validation | FluentValidation |
| Cross-property | IValidatableObject or FluentValidation |
| Reusable rules | FluentValidation extensions |
| Clean Architecture | FluentValidation (separated concerns) |

## Related Skills

- `skills/validation/fluent-validation.md`
- `skills/error-handling/problem-details.md`
