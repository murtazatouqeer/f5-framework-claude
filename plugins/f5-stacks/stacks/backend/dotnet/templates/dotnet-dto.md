---
name: dotnet-dto
description: Template for Data Transfer Objects (DTOs)
applies_to: dotnet
type: template
---

# DTO Template

## Response DTOs

```csharp
// {{SolutionName}}.Application/DTOs/{{EntityName}}Dto.cs
namespace {{SolutionName}}.Application.DTOs;

/// <summary>
/// {{EntityName}} data transfer object for responses
/// </summary>
public record {{EntityName}}Dto
{
    public Guid Id { get; init; }
    public string Name { get; init; } = string.Empty;
    public string? Description { get; init; }
    public decimal Price { get; init; }
    public int Stock { get; init; }
    public bool IsActive { get; init; }
    public Guid CategoryId { get; init; }
    public string? CategoryName { get; init; }
    public DateTime CreatedAt { get; init; }
    public DateTime? UpdatedAt { get; init; }
}

/// <summary>
/// Detailed {{EntityName}} DTO with related entities
/// </summary>
public record {{EntityName}}DetailDto : {{EntityName}}Dto
{
    public IEnumerable<TagDto> Tags { get; init; } = Enumerable.Empty<TagDto>();
    public CategoryDto? Category { get; init; }
    public string? CreatedBy { get; init; }
    public string? UpdatedBy { get; init; }
}

/// <summary>
/// Simplified {{EntityName}} DTO for list views
/// </summary>
public record {{EntityName}}ListItemDto
{
    public Guid Id { get; init; }
    public string Name { get; init; } = string.Empty;
    public decimal Price { get; init; }
    public bool IsActive { get; init; }
    public string? CategoryName { get; init; }
}
```

## Request DTOs

```csharp
// {{SolutionName}}.Application/DTOs/Create{{EntityName}}Dto.cs
using System.ComponentModel.DataAnnotations;

namespace {{SolutionName}}.Application.DTOs;

/// <summary>
/// DTO for creating a new {{EntityName}}
/// </summary>
public record Create{{EntityName}}Dto
{
    [Required]
    [StringLength(200, MinimumLength = 2)]
    public string Name { get; init; } = string.Empty;

    [StringLength(1000)]
    public string? Description { get; init; }

    [Required]
    [Range(0.01, double.MaxValue)]
    public decimal Price { get; init; }

    [Required]
    public Guid CategoryId { get; init; }

    public IEnumerable<Guid>? TagIds { get; init; }
}

// {{SolutionName}}.Application/DTOs/Update{{EntityName}}Dto.cs
/// <summary>
/// DTO for updating an existing {{EntityName}}
/// </summary>
public record Update{{EntityName}}Dto
{
    [StringLength(200, MinimumLength = 2)]
    public string? Name { get; init; }

    [StringLength(1000)]
    public string? Description { get; init; }

    [Range(0.01, double.MaxValue)]
    public decimal? Price { get; init; }

    public int? Stock { get; init; }

    public bool? IsActive { get; init; }

    public Guid? CategoryId { get; init; }

    public IEnumerable<Guid>? TagIds { get; init; }
}
```

## Filter DTOs

```csharp
// {{SolutionName}}.Application/DTOs/{{EntityName}}FilterDto.cs
namespace {{SolutionName}}.Application.DTOs;

/// <summary>
/// Filter parameters for {{EntityName}} queries
/// </summary>
public record {{EntityName}}FilterDto
{
    public string? Search { get; init; }
    public Guid? CategoryId { get; init; }
    public bool? IsActive { get; init; }
    public decimal? MinPrice { get; init; }
    public decimal? MaxPrice { get; init; }
    public DateTime? CreatedFrom { get; init; }
    public DateTime? CreatedTo { get; init; }
    public string? SortBy { get; init; } = "Name";
    public bool SortDescending { get; init; } = false;
}
```

## AutoMapper Profile

```csharp
// {{SolutionName}}.Application/Mappings/{{EntityName}}MappingProfile.cs
using AutoMapper;
using {{SolutionName}}.Application.DTOs;
using {{SolutionName}}.Domain.Entities;

namespace {{SolutionName}}.Application.Mappings;

public class {{EntityName}}MappingProfile : Profile
{
    public {{EntityName}}MappingProfile()
    {
        // Entity to DTO
        CreateMap<{{EntityName}}, {{EntityName}}Dto>()
            .ForMember(
                dest => dest.CategoryName,
                opt => opt.MapFrom(src => src.Category.Name));

        CreateMap<{{EntityName}}, {{EntityName}}DetailDto>()
            .ForMember(
                dest => dest.CategoryName,
                opt => opt.MapFrom(src => src.Category.Name))
            .ForMember(
                dest => dest.Tags,
                opt => opt.MapFrom(src => src.Tags.Select(t => t.Tag)));

        CreateMap<{{EntityName}}, {{EntityName}}ListItemDto>()
            .ForMember(
                dest => dest.CategoryName,
                opt => opt.MapFrom(src => src.Category.Name));

        // Create DTO to Entity
        CreateMap<Create{{EntityName}}Dto, {{EntityName}}>()
            .ForMember(dest => dest.Id, opt => opt.Ignore())
            .ForMember(dest => dest.Category, opt => opt.Ignore())
            .ForMember(dest => dest.Tags, opt => opt.Ignore())
            .ForMember(dest => dest.CreatedAt, opt => opt.Ignore())
            .ForMember(dest => dest.UpdatedAt, opt => opt.Ignore());

        // Update DTO to Entity (for partial updates)
        CreateMap<Update{{EntityName}}Dto, {{EntityName}}>()
            .ForAllMembers(opt => opt.Condition(
                (src, dest, srcMember) => srcMember != null));
    }
}
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{SolutionName}}` | Solution/project name | `MyApp` |
| `{{EntityName}}` | PascalCase entity name | `Product` |
