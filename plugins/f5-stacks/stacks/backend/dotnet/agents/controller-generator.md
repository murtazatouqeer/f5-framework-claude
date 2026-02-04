---
name: dotnet-controller-generator
description: Generates ASP.NET Core API controllers following Clean Architecture patterns
triggers:
  - create controller
  - generate controller
  - add controller
  - dotnet controller
  - aspnet controller
---

# ASP.NET Core Controller Generator

## Purpose

Generate API controllers following Clean Architecture principles with proper dependency injection, validation, and error handling.

## Required Context

Before generating, gather:
1. **Entity Name**: PascalCase name (e.g., `Product`)
2. **CRUD Operations**: Which operations to include (Create, Read, Update, Delete)
3. **Authorization**: Required roles/policies
4. **Service Interface**: Service to inject

## Generation Template

```csharp
// {{SolutionName}}.API/Controllers/{{EntityName}}sController.cs
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using {{SolutionName}}.Application.DTOs;
using {{SolutionName}}.Application.Interfaces;

namespace {{SolutionName}}.API.Controllers;

[ApiController]
[Route("api/[controller]")]
[Produces("application/json")]
public class {{EntityName}}sController : ControllerBase
{
    private readonly I{{EntityName}}Service _service;
    private readonly ILogger<{{EntityName}}sController> _logger;

    public {{EntityName}}sController(
        I{{EntityName}}Service service,
        ILogger<{{EntityName}}sController> logger)
    {
        _service = service;
        _logger = logger;
    }

    /// <summary>
    /// Get all {{entityName}}s with optional filtering
    /// </summary>
    [HttpGet]
    [ProducesResponseType(typeof(IEnumerable<{{EntityName}}Dto>), StatusCodes.Status200OK)]
    public async Task<ActionResult<IEnumerable<{{EntityName}}Dto>>> GetAll(
        [FromQuery] {{EntityName}}FilterDto filter,
        CancellationToken cancellationToken)
    {
        var result = await _service.GetAllAsync(filter, cancellationToken);
        return Ok(result);
    }

    /// <summary>
    /// Get a {{entityName}} by ID
    /// </summary>
    [HttpGet("{id:guid}")]
    [ProducesResponseType(typeof({{EntityName}}Dto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<{{EntityName}}Dto>> GetById(
        Guid id,
        CancellationToken cancellationToken)
    {
        var result = await _service.GetByIdAsync(id, cancellationToken);

        if (result is null)
            return NotFound();

        return Ok(result);
    }

    /// <summary>
    /// Create a new {{entityName}}
    /// </summary>
    [HttpPost]
    [Authorize(Policy = "{{EntityName}}Write")]
    [ProducesResponseType(typeof({{EntityName}}Dto), StatusCodes.Status201Created)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<ActionResult<{{EntityName}}Dto>> Create(
        [FromBody] Create{{EntityName}}Dto dto,
        CancellationToken cancellationToken)
    {
        var result = await _service.CreateAsync(dto, cancellationToken);

        return CreatedAtAction(
            nameof(GetById),
            new { id = result.Id },
            result);
    }

    /// <summary>
    /// Update an existing {{entityName}}
    /// </summary>
    [HttpPut("{id:guid}")]
    [Authorize(Policy = "{{EntityName}}Write")]
    [ProducesResponseType(typeof({{EntityName}}Dto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<ActionResult<{{EntityName}}Dto>> Update(
        Guid id,
        [FromBody] Update{{EntityName}}Dto dto,
        CancellationToken cancellationToken)
    {
        var result = await _service.UpdateAsync(id, dto, cancellationToken);

        if (result is null)
            return NotFound();

        return Ok(result);
    }

    /// <summary>
    /// Delete a {{entityName}}
    /// </summary>
    [HttpDelete("{id:guid}")]
    [Authorize(Policy = "{{EntityName}}Delete")]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> Delete(
        Guid id,
        CancellationToken cancellationToken)
    {
        var success = await _service.DeleteAsync(id, cancellationToken);

        if (!success)
            return NotFound();

        return NoContent();
    }
}
```

## Generation Checklist

- [ ] Controller inherits from ControllerBase
- [ ] Route attribute uses [controller] placeholder
- [ ] ApiController attribute present
- [ ] Proper HTTP method attributes
- [ ] ProducesResponseType for Swagger
- [ ] CancellationToken in all async methods
- [ ] Authorization policies applied
- [ ] XML documentation comments
- [ ] Dependency injection via constructor

## Related Templates

- `templates/dotnet-controller.md` - Full controller template
- `templates/dotnet-dto.md` - DTO generation
- `templates/dotnet-service.md` - Service interface
