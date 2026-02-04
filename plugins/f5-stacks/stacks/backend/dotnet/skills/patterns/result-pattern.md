# Result Pattern - ASP.NET Core

## Overview

The Result pattern provides a consistent way to handle operation outcomes without throwing exceptions for expected failures. It encapsulates success/failure state, data, and error information.

## Basic Result Implementation

```csharp
// Application/Common/Result.cs
public class Result
{
    protected Result(bool isSuccess, Error error)
    {
        if (isSuccess && error != Error.None ||
            !isSuccess && error == Error.None)
        {
            throw new ArgumentException("Invalid error", nameof(error));
        }

        IsSuccess = isSuccess;
        Error = error;
    }

    public bool IsSuccess { get; }
    public bool IsFailure => !IsSuccess;
    public Error Error { get; }

    public static Result Success() => new(true, Error.None);
    public static Result Failure(Error error) => new(false, error);

    public static Result<TValue> Success<TValue>(TValue value) =>
        new(value, true, Error.None);

    public static Result<TValue> Failure<TValue>(Error error) =>
        new(default, false, error);
}

public class Result<TValue> : Result
{
    private readonly TValue? _value;

    protected internal Result(TValue? value, bool isSuccess, Error error)
        : base(isSuccess, error)
    {
        _value = value;
    }

    public TValue Value => IsSuccess
        ? _value!
        : throw new InvalidOperationException("Cannot access value of failed result");

    public static implicit operator Result<TValue>(TValue value) =>
        new(value, true, Error.None);
}
```

## Error Type

```csharp
// Application/Common/Error.cs
public sealed record Error(string Code, string Description)
{
    public static readonly Error None = new(string.Empty, string.Empty);
    public static readonly Error NullValue = new("Error.NullValue", "Value cannot be null");

    // Factory methods for common errors
    public static Error NotFound(string entity, object id) =>
        new($"{entity}.NotFound", $"{entity} with id '{id}' was not found.");

    public static Error Validation(string propertyName, string message) =>
        new($"Validation.{propertyName}", message);

    public static Error Conflict(string entity, string reason) =>
        new($"{entity}.Conflict", reason);

    public static Error Unauthorized() =>
        new("Auth.Unauthorized", "User is not authorized.");

    public static Error Forbidden() =>
        new("Auth.Forbidden", "User does not have permission.");
}
```

## Rich Result Implementation

```csharp
// Application/Common/Result/Result.cs
public class Result<T>
{
    public T? Value { get; }
    public bool IsSuccess { get; }
    public bool IsFailure => !IsSuccess;
    public ResultStatus Status { get; }
    public List<string> Errors { get; } = new();
    public List<ValidationError> ValidationErrors { get; } = new();

    private Result(T? value, ResultStatus status)
    {
        Value = value;
        Status = status;
        IsSuccess = status == ResultStatus.Ok || status == ResultStatus.Created;
    }

    // Success factories
    public static Result<T> Success(T value) =>
        new(value, ResultStatus.Ok);

    public static Result<T> Created(T value) =>
        new(value, ResultStatus.Created);

    // Failure factories
    public static Result<T> NotFound(string message = "Resource not found")
    {
        var result = new Result<T>(default, ResultStatus.NotFound);
        result.Errors.Add(message);
        return result;
    }

    public static Result<T> Invalid(string message)
    {
        var result = new Result<T>(default, ResultStatus.Invalid);
        result.Errors.Add(message);
        return result;
    }

    public static Result<T> Invalid(List<ValidationError> validationErrors)
    {
        var result = new Result<T>(default, ResultStatus.Invalid);
        result.ValidationErrors.AddRange(validationErrors);
        return result;
    }

    public static Result<T> Error(string message)
    {
        var result = new Result<T>(default, ResultStatus.Error);
        result.Errors.Add(message);
        return result;
    }

    public static Result<T> Unauthorized(string message = "Unauthorized")
    {
        var result = new Result<T>(default, ResultStatus.Unauthorized);
        result.Errors.Add(message);
        return result;
    }

    public static Result<T> Forbidden(string message = "Forbidden")
    {
        var result = new Result<T>(default, ResultStatus.Forbidden);
        result.Errors.Add(message);
        return result;
    }

    public static Result<T> Conflict(string message)
    {
        var result = new Result<T>(default, ResultStatus.Conflict);
        result.Errors.Add(message);
        return result;
    }
}

public enum ResultStatus
{
    Ok,
    Created,
    NotFound,
    Invalid,
    Error,
    Unauthorized,
    Forbidden,
    Conflict
}

public record ValidationError(string PropertyName, string ErrorMessage);
```

## Extension Methods for Controllers

```csharp
// Api/Extensions/ResultExtensions.cs
public static class ResultExtensions
{
    public static IActionResult ToActionResult<T>(this Result<T> result)
    {
        return result.Status switch
        {
            ResultStatus.Ok => new OkObjectResult(result.Value),
            ResultStatus.Created => new ObjectResult(result.Value)
            {
                StatusCode = StatusCodes.Status201Created
            },
            ResultStatus.NotFound => new NotFoundObjectResult(new ProblemDetails
            {
                Status = StatusCodes.Status404NotFound,
                Title = "Not Found",
                Detail = result.Errors.FirstOrDefault()
            }),
            ResultStatus.Invalid => new BadRequestObjectResult(new ValidationProblemDetails
            {
                Status = StatusCodes.Status400BadRequest,
                Title = "Validation Error",
                Errors = result.ValidationErrors
                    .GroupBy(e => e.PropertyName)
                    .ToDictionary(
                        g => g.Key,
                        g => g.Select(e => e.ErrorMessage).ToArray())
            }),
            ResultStatus.Unauthorized => new UnauthorizedObjectResult(new ProblemDetails
            {
                Status = StatusCodes.Status401Unauthorized,
                Title = "Unauthorized",
                Detail = result.Errors.FirstOrDefault()
            }),
            ResultStatus.Forbidden => new ObjectResult(new ProblemDetails
            {
                Status = StatusCodes.Status403Forbidden,
                Title = "Forbidden",
                Detail = result.Errors.FirstOrDefault()
            })
            {
                StatusCode = StatusCodes.Status403Forbidden
            },
            ResultStatus.Conflict => new ConflictObjectResult(new ProblemDetails
            {
                Status = StatusCodes.Status409Conflict,
                Title = "Conflict",
                Detail = result.Errors.FirstOrDefault()
            }),
            ResultStatus.Error => new ObjectResult(new ProblemDetails
            {
                Status = StatusCodes.Status500InternalServerError,
                Title = "Server Error",
                Detail = result.Errors.FirstOrDefault()
            })
            {
                StatusCode = StatusCodes.Status500InternalServerError
            },
            _ => new ObjectResult(new ProblemDetails
            {
                Status = StatusCodes.Status500InternalServerError,
                Title = "Unknown Error"
            })
            {
                StatusCode = StatusCodes.Status500InternalServerError
            }
        };
    }

    public static IActionResult ToCreatedActionResult<T>(
        this Result<T> result,
        string actionName,
        object? routeValues = null)
    {
        if (result.Status != ResultStatus.Created && result.Status != ResultStatus.Ok)
        {
            return result.ToActionResult();
        }

        return new CreatedAtActionResult(actionName, null, routeValues, result.Value);
    }
}
```

## Usage in Handlers

```csharp
// Application/Features/Products/Commands/CreateProductCommandHandler.cs
public class CreateProductCommandHandler
    : IRequestHandler<CreateProductCommand, Result<ProductDto>>
{
    private readonly IApplicationDbContext _context;
    private readonly IMapper _mapper;

    public CreateProductCommandHandler(
        IApplicationDbContext context,
        IMapper mapper)
    {
        _context = context;
        _mapper = mapper;
    }

    public async Task<Result<ProductDto>> Handle(
        CreateProductCommand request,
        CancellationToken cancellationToken)
    {
        // Validation
        var existingProduct = await _context.Products
            .FirstOrDefaultAsync(p => p.Sku == request.Sku, cancellationToken);

        if (existingProduct is not null)
        {
            return Result<ProductDto>.Conflict($"Product with SKU '{request.Sku}' already exists");
        }

        var category = await _context.Categories
            .FindAsync(new object[] { request.CategoryId }, cancellationToken);

        if (category is null)
        {
            return Result<ProductDto>.NotFound($"Category {request.CategoryId} not found");
        }

        // Create
        var product = new Product
        {
            Name = request.Name,
            Sku = request.Sku,
            Price = request.Price,
            CategoryId = request.CategoryId
        };

        _context.Products.Add(product);
        await _context.SaveChangesAsync(cancellationToken);

        return Result<ProductDto>.Created(_mapper.Map<ProductDto>(product));
    }
}
```

## Usage in Controllers

```csharp
// Api/Controllers/ProductsController.cs
[ApiController]
[Route("api/[controller]")]
public class ProductsController : ControllerBase
{
    private readonly IMediator _mediator;

    public ProductsController(IMediator mediator)
    {
        _mediator = mediator;
    }

    [HttpGet("{id:guid}")]
    [ProducesResponseType(typeof(ProductDto), StatusCodes.Status200OK)]
    [ProducesResponseType(typeof(ProblemDetails), StatusCodes.Status404NotFound)]
    public async Task<IActionResult> GetProduct(Guid id)
    {
        var result = await _mediator.Send(new GetProductByIdQuery(id));
        return result.ToActionResult();
    }

    [HttpPost]
    [ProducesResponseType(typeof(ProductDto), StatusCodes.Status201Created)]
    [ProducesResponseType(typeof(ValidationProblemDetails), StatusCodes.Status400BadRequest)]
    [ProducesResponseType(typeof(ProblemDetails), StatusCodes.Status409Conflict)]
    public async Task<IActionResult> CreateProduct([FromBody] CreateProductCommand command)
    {
        var result = await _mediator.Send(command);
        return result.ToCreatedActionResult(nameof(GetProduct), new { id = result.Value?.Id });
    }
}
```

## Functional Extensions

```csharp
// Application/Common/ResultExtensions.cs
public static class ResultFunctionalExtensions
{
    // Map success value
    public static Result<TOut> Map<TIn, TOut>(
        this Result<TIn> result,
        Func<TIn, TOut> mapper)
    {
        return result.IsSuccess
            ? Result<TOut>.Success(mapper(result.Value!))
            : Result<TOut>.Error(result.Errors.FirstOrDefault() ?? "Unknown error");
    }

    // Bind (flatMap) for chaining
    public static async Task<Result<TOut>> Bind<TIn, TOut>(
        this Result<TIn> result,
        Func<TIn, Task<Result<TOut>>> func)
    {
        return result.IsSuccess
            ? await func(result.Value!)
            : Result<TOut>.Error(result.Errors.FirstOrDefault() ?? "Unknown error");
    }

    // Match for handling both cases
    public static TOut Match<TIn, TOut>(
        this Result<TIn> result,
        Func<TIn, TOut> onSuccess,
        Func<List<string>, TOut> onFailure)
    {
        return result.IsSuccess
            ? onSuccess(result.Value!)
            : onFailure(result.Errors);
    }

    // Tap for side effects
    public static Result<T> Tap<T>(
        this Result<T> result,
        Action<T> action)
    {
        if (result.IsSuccess)
        {
            action(result.Value!);
        }
        return result;
    }

    // Ensure for validation
    public static Result<T> Ensure<T>(
        this Result<T> result,
        Func<T, bool> predicate,
        string errorMessage)
    {
        if (result.IsFailure)
            return result;

        return predicate(result.Value!)
            ? result
            : Result<T>.Invalid(errorMessage);
    }
}
```

## Using Ardalis.Result Package

```csharp
// Alternative: Using Ardalis.Result NuGet package
using Ardalis.Result;

public class ProductService
{
    public async Task<Result<ProductDto>> GetByIdAsync(Guid id)
    {
        var product = await _repository.GetByIdAsync(id);

        if (product is null)
        {
            return Result<ProductDto>.NotFound();
        }

        return Result<ProductDto>.Success(_mapper.Map<ProductDto>(product));
    }

    public async Task<Result<ProductDto>> CreateAsync(CreateProductRequest request)
    {
        var validationResult = await _validator.ValidateAsync(request);

        if (!validationResult.IsValid)
        {
            return Result<ProductDto>.Invalid(
                validationResult.Errors.Select(e =>
                    new ValidationError(e.PropertyName, e.ErrorMessage)));
        }

        // Create product...

        return Result<ProductDto>.Success(dto);
    }
}
```

## Best Practices

1. **Never Throw for Expected Failures**: Use Result for business logic errors
2. **Consistent API Responses**: Map Result status to HTTP status codes
3. **Rich Error Information**: Include detailed error messages and validation errors
4. **Functional Chaining**: Use Map/Bind for complex workflows
5. **Type Safety**: Result<T> forces handling of both success and failure cases
6. **Controller Simplicity**: Use extension methods for clean controller code
