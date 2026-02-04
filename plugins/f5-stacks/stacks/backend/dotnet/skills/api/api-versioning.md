---
name: api-versioning
description: API versioning strategies for ASP.NET Core
applies_to: dotnet
type: skill
---

# API Versioning

## Overview

API versioning allows you to evolve your API while maintaining backward compatibility for existing clients. ASP.NET Core provides built-in support for multiple versioning strategies.

## Setup

### Installation

```bash
dotnet add package Asp.Versioning.Mvc
dotnet add package Asp.Versioning.Mvc.ApiExplorer
```

### Configuration

```csharp
// Program.cs
builder.Services.AddApiVersioning(options =>
{
    options.DefaultApiVersion = new ApiVersion(1, 0);
    options.AssumeDefaultVersionWhenUnspecified = true;
    options.ReportApiVersions = true;
    options.ApiVersionReader = ApiVersionReader.Combine(
        new UrlSegmentApiVersionReader(),
        new HeaderApiVersionReader("X-Api-Version"),
        new QueryStringApiVersionReader("api-version"));
})
.AddMvc()
.AddApiExplorer(options =>
{
    options.GroupNameFormat = "'v'VVV";
    options.SubstituteApiVersionInUrl = true;
});
```

## Versioning Strategies

### URL Path Versioning

```csharp
// Most explicit and RESTful approach
// /api/v1/products
// /api/v2/products

[ApiController]
[Route("api/v{version:apiVersion}/products")]
[ApiVersion("1.0")]
public class ProductsController : ControllerBase
{
    [HttpGet]
    public IActionResult Get() => Ok("Version 1");
}

[ApiController]
[Route("api/v{version:apiVersion}/products")]
[ApiVersion("2.0")]
public class ProductsV2Controller : ControllerBase
{
    [HttpGet]
    public IActionResult Get() => Ok("Version 2");
}
```

### Query String Versioning

```csharp
// /api/products?api-version=1.0

builder.Services.AddApiVersioning(options =>
{
    options.ApiVersionReader = new QueryStringApiVersionReader("api-version");
});
```

### Header Versioning

```csharp
// X-Api-Version: 1.0

builder.Services.AddApiVersioning(options =>
{
    options.ApiVersionReader = new HeaderApiVersionReader("X-Api-Version");
});
```

### Media Type Versioning

```csharp
// Accept: application/json;v=1.0

builder.Services.AddApiVersioning(options =>
{
    options.ApiVersionReader = new MediaTypeApiVersionReader("v");
});
```

## Version Attributes

### Controller Level

```csharp
[ApiController]
[Route("api/v{version:apiVersion}/[controller]")]
[ApiVersion("1.0")]
[ApiVersion("2.0")] // Supports multiple versions
public class ProductsController : ControllerBase
{
    [HttpGet]
    public IActionResult GetV1() => Ok("V1");

    [HttpGet]
    [MapToApiVersion("2.0")]
    public IActionResult GetV2() => Ok("V2");
}
```

### Action Level

```csharp
[ApiController]
[Route("api/v{version:apiVersion}/products")]
[ApiVersion("1.0")]
[ApiVersion("2.0")]
public class ProductsController : ControllerBase
{
    // Available in both versions
    [HttpGet]
    public IActionResult GetAll() => Ok("All products");

    // Only in v1
    [HttpGet("legacy")]
    [MapToApiVersion("1.0")]
    public IActionResult GetLegacy() => Ok("Legacy endpoint");

    // Only in v2
    [HttpGet("enhanced")]
    [MapToApiVersion("2.0")]
    public IActionResult GetEnhanced() => Ok("Enhanced endpoint");
}
```

### Deprecation

```csharp
[ApiController]
[Route("api/v{version:apiVersion}/products")]
[ApiVersion("1.0", Deprecated = true)] // Mark as deprecated
[ApiVersion("2.0")]
public class ProductsController : ControllerBase
{
    // Deprecated version will return:
    // api-deprecated-versions: 1.0
    // api-supported-versions: 2.0
}
```

## Swagger/OpenAPI Integration

### Configure for Multiple Versions

```csharp
// Program.cs
builder.Services.AddSwaggerGen(options =>
{
    var provider = builder.Services.BuildServiceProvider()
        .GetRequiredService<IApiVersionDescriptionProvider>();

    foreach (var description in provider.ApiVersionDescriptions)
    {
        options.SwaggerDoc(
            description.GroupName,
            new OpenApiInfo
            {
                Title = $"My API {description.ApiVersion}",
                Version = description.ApiVersion.ToString(),
                Description = description.IsDeprecated
                    ? "This API version has been deprecated."
                    : null
            });
    }
});

// Middleware
app.UseSwagger();
app.UseSwaggerUI(options =>
{
    var provider = app.Services.GetRequiredService<IApiVersionDescriptionProvider>();

    foreach (var description in provider.ApiVersionDescriptions.Reverse())
    {
        options.SwaggerEndpoint(
            $"/swagger/{description.GroupName}/swagger.json",
            description.GroupName.ToUpperInvariant());
    }
});
```

## Minimal APIs Versioning

```csharp
// Setup
var versionSet = app.NewApiVersionSet()
    .HasApiVersion(new ApiVersion(1, 0))
    .HasApiVersion(new ApiVersion(2, 0))
    .ReportApiVersions()
    .Build();

// V1 endpoints
var v1 = app.MapGroup("/api/v{version:apiVersion}/products")
    .WithApiVersionSet(versionSet)
    .MapToApiVersion(new ApiVersion(1, 0));

v1.MapGet("/", () => "V1 Products");

// V2 endpoints
var v2 = app.MapGroup("/api/v{version:apiVersion}/products")
    .WithApiVersionSet(versionSet)
    .MapToApiVersion(new ApiVersion(2, 0));

v2.MapGet("/", () => new { data = "V2 Products", enhanced = true });
```

## Version Neutral Endpoints

```csharp
// Endpoints that work with all versions
[ApiController]
[Route("api/health")]
[ApiVersionNeutral] // Works with any version
public class HealthController : ControllerBase
{
    [HttpGet]
    public IActionResult Get() => Ok(new { status = "healthy" });
}
```

## Best Practices

### Version DTOs

```csharp
// V1 DTO
namespace MyApp.API.V1.Models;

public record ProductDto(
    Guid Id,
    string Name,
    decimal Price);

// V2 DTO with breaking changes
namespace MyApp.API.V2.Models;

public record ProductDto(
    Guid Id,
    string Name,
    MoneyDto Price,    // Changed from decimal
    string[] Tags);    // New field

public record MoneyDto(
    decimal Amount,
    string Currency);
```

### Mapping Between Versions

```csharp
// AutoMapper profile
public class ProductMappingProfile : Profile
{
    public ProductMappingProfile()
    {
        // V1 mapping
        CreateMap<Product, V1.Models.ProductDto>();

        // V2 mapping
        CreateMap<Product, V2.Models.ProductDto>()
            .ForMember(d => d.Price, opt => opt.MapFrom(s =>
                new V2.Models.MoneyDto(s.Price, s.Currency)));
    }
}
```

### Version Negotiation

```csharp
// Controller that handles version negotiation
[ApiController]
[Route("api/v{version:apiVersion}/products")]
[ApiVersion("1.0")]
[ApiVersion("2.0")]
public class ProductsController : ControllerBase
{
    private readonly IMapper _mapper;

    [HttpGet("{id:guid}")]
    public async Task<IActionResult> GetById(
        Guid id,
        ApiVersion version,
        [FromServices] IProductService service)
    {
        var product = await service.GetByIdAsync(id);

        if (product is null)
            return NotFound();

        return version.MajorVersion switch
        {
            1 => Ok(_mapper.Map<V1.Models.ProductDto>(product)),
            2 => Ok(_mapper.Map<V2.Models.ProductDto>(product)),
            _ => BadRequest("Unsupported version")
        };
    }
}
```

## Guidelines

| Scenario | Recommendation |
|----------|----------------|
| Breaking changes | New major version |
| New fields (additive) | Same version, document |
| Removed fields | New major version |
| Changed behavior | New major version |
| Bug fixes | Same version |
| New endpoints | Same version, document |

## Related Skills

- `skills/api/controller-patterns.md`
- `skills/api/minimal-apis.md`
