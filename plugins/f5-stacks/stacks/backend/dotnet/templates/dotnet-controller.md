---
name: dotnet-controller
description: Template for ASP.NET Core API Controllers
applies_to: dotnet
type: template
---

# ASP.NET Core Controller Template

```csharp
// {{SolutionName}}.API/Controllers/{{EntityName}}sController.cs
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using MediatR;
using {{SolutionName}}.Application.{{EntityName}}s.Commands;
using {{SolutionName}}.Application.{{EntityName}}s.Queries;
using {{SolutionName}}.Application.DTOs;

namespace {{SolutionName}}.API.Controllers;

/// <summary>
/// Manages {{entityName}} resources
/// </summary>
[ApiController]
[Route("api/[controller]")]
[Produces("application/json")]
public class {{EntityName}}sController : ControllerBase
{
    private readonly IMediator _mediator;
    private readonly ILogger<{{EntityName}}sController> _logger;

    public {{EntityName}}sController(
        IMediator mediator,
        ILogger<{{EntityName}}sController> logger)
    {
        _mediator = mediator;
        _logger = logger;
    }

    /// <summary>
    /// Get all {{entityName}}s with pagination and filtering
    /// </summary>
    /// <param name="query">Filter and pagination parameters</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>Paginated list of {{entityName}}s</returns>
    [HttpGet]
    [ProducesResponseType(typeof(PaginatedList<{{EntityName}}Dto>), StatusCodes.Status200OK)]
    public async Task<ActionResult<PaginatedList<{{EntityName}}Dto>>> GetAll(
        [FromQuery] Get{{EntityName}}sQuery query,
        CancellationToken cancellationToken)
    {
        var result = await _mediator.Send(query, cancellationToken);
        return Ok(result);
    }

    /// <summary>
    /// Get a {{entityName}} by ID
    /// </summary>
    /// <param name="id">{{EntityName}} ID</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>{{EntityName}} details</returns>
    [HttpGet("{id:guid}")]
    [ProducesResponseType(typeof({{EntityName}}Dto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<{{EntityName}}Dto>> GetById(
        Guid id,
        CancellationToken cancellationToken)
    {
        var query = new Get{{EntityName}}ByIdQuery(id);
        var result = await _mediator.Send(query, cancellationToken);

        if (result is null)
            return NotFound();

        return Ok(result);
    }

    /// <summary>
    /// Create a new {{entityName}}
    /// </summary>
    /// <param name="command">{{EntityName}} creation data</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>Created {{entityName}}</returns>
    [HttpPost]
    [Authorize(Policy = "{{EntityName}}Write")]
    [ProducesResponseType(typeof({{EntityName}}Dto), StatusCodes.Status201Created)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(StatusCodes.Status422UnprocessableEntity)]
    public async Task<ActionResult<{{EntityName}}Dto>> Create(
        [FromBody] Create{{EntityName}}Command command,
        CancellationToken cancellationToken)
    {
        var result = await _mediator.Send(command, cancellationToken);

        _logger.LogInformation("{{EntityName}} created with ID {Id}", result.Id);

        return CreatedAtAction(
            nameof(GetById),
            new { id = result.Id },
            result);
    }

    /// <summary>
    /// Update an existing {{entityName}}
    /// </summary>
    /// <param name="id">{{EntityName}} ID</param>
    /// <param name="command">Update data</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>Updated {{entityName}}</returns>
    [HttpPut("{id:guid}")]
    [Authorize(Policy = "{{EntityName}}Write")]
    [ProducesResponseType(typeof({{EntityName}}Dto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<ActionResult<{{EntityName}}Dto>> Update(
        Guid id,
        [FromBody] Update{{EntityName}}Command command,
        CancellationToken cancellationToken)
    {
        if (id != command.Id)
            return BadRequest("ID mismatch");

        var result = await _mediator.Send(command, cancellationToken);

        if (result is null)
            return NotFound();

        _logger.LogInformation("{{EntityName}} updated with ID {Id}", id);

        return Ok(result);
    }

    /// <summary>
    /// Delete a {{entityName}}
    /// </summary>
    /// <param name="id">{{EntityName}} ID</param>
    /// <param name="cancellationToken">Cancellation token</param>
    [HttpDelete("{id:guid}")]
    [Authorize(Policy = "{{EntityName}}Delete")]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> Delete(
        Guid id,
        CancellationToken cancellationToken)
    {
        var command = new Delete{{EntityName}}Command(id);
        var success = await _mediator.Send(command, cancellationToken);

        if (!success)
            return NotFound();

        _logger.LogInformation("{{EntityName}} deleted with ID {Id}", id);

        return NoContent();
    }
}
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{SolutionName}}` | Solution/project name | `MyApp` |
| `{{EntityName}}` | PascalCase entity name | `Product` |
| `{{entityName}}` | camelCase entity name | `product` |
