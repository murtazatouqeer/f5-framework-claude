---
name: dotnet-test-generator
description: Generates xUnit tests for controllers, services, and handlers
triggers:
  - create test
  - generate test
  - add test
  - xunit
  - unit test
---

# .NET Test Generator

## Purpose

Generate comprehensive unit and integration tests using xUnit, Moq, and FluentAssertions.

## Required Context

Before generating, gather:
1. **Test Type**: Unit test or Integration test
2. **Target**: Controller, Service, Handler, or Repository
3. **Entity Name**: Entity being tested
4. **Scenarios**: Test cases to cover

## Unit Test Template

### Service Unit Tests

```csharp
// {{SolutionName}}.Tests/Unit/Services/{{EntityName}}ServiceTests.cs
using AutoMapper;
using FluentAssertions;
using Microsoft.Extensions.Logging;
using Moq;
using {{SolutionName}}.Application.DTOs;
using {{SolutionName}}.Application.Services;
using {{SolutionName}}.Domain.Entities;
using {{SolutionName}}.Domain.Interfaces;
using Xunit;

namespace {{SolutionName}}.Tests.Unit.Services;

public class {{EntityName}}ServiceTests
{
    private readonly Mock<I{{EntityName}}Repository> _repositoryMock;
    private readonly Mock<IUnitOfWork> _unitOfWorkMock;
    private readonly Mock<IMapper> _mapperMock;
    private readonly Mock<ILogger<{{EntityName}}Service>> _loggerMock;
    private readonly {{EntityName}}Service _sut;

    public {{EntityName}}ServiceTests()
    {
        _repositoryMock = new Mock<I{{EntityName}}Repository>();
        _unitOfWorkMock = new Mock<IUnitOfWork>();
        _mapperMock = new Mock<IMapper>();
        _loggerMock = new Mock<ILogger<{{EntityName}}Service>>();

        _sut = new {{EntityName}}Service(
            _repositoryMock.Object,
            _unitOfWorkMock.Object,
            _mapperMock.Object,
            _loggerMock.Object);
    }

    [Fact]
    public async Task GetByIdAsync_WhenExists_ReturnsDto()
    {
        // Arrange
        var id = Guid.NewGuid();
        var entity = {{EntityName}}.Create("Test", null, 100, Guid.NewGuid());
        var expectedDto = new {{EntityName}}Dto { Id = id, Name = "Test" };

        _repositoryMock
            .Setup(x => x.GetByIdAsync(id, It.IsAny<CancellationToken>()))
            .ReturnsAsync(entity);

        _mapperMock
            .Setup(x => x.Map<{{EntityName}}Dto>(entity))
            .Returns(expectedDto);

        // Act
        var result = await _sut.GetByIdAsync(id);

        // Assert
        result.Should().NotBeNull();
        result.Should().BeEquivalentTo(expectedDto);
    }

    [Fact]
    public async Task GetByIdAsync_WhenNotExists_ReturnsNull()
    {
        // Arrange
        var id = Guid.NewGuid();
        _repositoryMock
            .Setup(x => x.GetByIdAsync(id, It.IsAny<CancellationToken>()))
            .ReturnsAsync(({{EntityName}}?)null);

        // Act
        var result = await _sut.GetByIdAsync(id);

        // Assert
        result.Should().BeNull();
    }

    [Fact]
    public async Task CreateAsync_ValidDto_ReturnsCreatedDto()
    {
        // Arrange
        var createDto = new Create{{EntityName}}Dto
        {
            Name = "New {{EntityName}}",
            Price = 50.00m,
            CategoryId = Guid.NewGuid()
        };

        var expectedDto = new {{EntityName}}Dto
        {
            Id = Guid.NewGuid(),
            Name = createDto.Name
        };

        _mapperMock
            .Setup(x => x.Map<{{EntityName}}>(createDto))
            .Returns({{EntityName}}.Create(
                createDto.Name,
                null,
                createDto.Price,
                createDto.CategoryId));

        _mapperMock
            .Setup(x => x.Map<{{EntityName}}Dto>(It.IsAny<{{EntityName}}>()))
            .Returns(expectedDto);

        // Act
        var result = await _sut.CreateAsync(createDto);

        // Assert
        result.Should().NotBeNull();
        result.Name.Should().Be(createDto.Name);

        _repositoryMock.Verify(
            x => x.AddAsync(It.IsAny<{{EntityName}}>(), It.IsAny<CancellationToken>()),
            Times.Once);

        _unitOfWorkMock.Verify(
            x => x.SaveChangesAsync(It.IsAny<CancellationToken>()),
            Times.Once);
    }

    [Fact]
    public async Task DeleteAsync_WhenExists_ReturnsTrue()
    {
        // Arrange
        var id = Guid.NewGuid();
        var entity = {{EntityName}}.Create("Test", null, 100, Guid.NewGuid());

        _repositoryMock
            .Setup(x => x.GetByIdAsync(id, It.IsAny<CancellationToken>()))
            .ReturnsAsync(entity);

        // Act
        var result = await _sut.DeleteAsync(id);

        // Assert
        result.Should().BeTrue();

        _repositoryMock.Verify(x => x.Delete(entity), Times.Once);
        _unitOfWorkMock.Verify(
            x => x.SaveChangesAsync(It.IsAny<CancellationToken>()),
            Times.Once);
    }

    [Fact]
    public async Task DeleteAsync_WhenNotExists_ReturnsFalse()
    {
        // Arrange
        var id = Guid.NewGuid();
        _repositoryMock
            .Setup(x => x.GetByIdAsync(id, It.IsAny<CancellationToken>()))
            .ReturnsAsync(({{EntityName}}?)null);

        // Act
        var result = await _sut.DeleteAsync(id);

        // Assert
        result.Should().BeFalse();
        _repositoryMock.Verify(x => x.Delete(It.IsAny<{{EntityName}}>()), Times.Never);
    }
}
```

## Integration Test Template

### Controller Integration Tests

```csharp
// {{SolutionName}}.Tests/Integration/Controllers/{{EntityName}}sControllerTests.cs
using System.Net;
using System.Net.Http.Json;
using FluentAssertions;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.Extensions.DependencyInjection;
using {{SolutionName}}.Application.DTOs;
using {{SolutionName}}.Infrastructure.Persistence;
using Xunit;

namespace {{SolutionName}}.Tests.Integration.Controllers;

public class {{EntityName}}sControllerTests
    : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly HttpClient _client;
    private readonly WebApplicationFactory<Program> _factory;

    public {{EntityName}}sControllerTests(WebApplicationFactory<Program> factory)
    {
        _factory = factory.WithWebHostBuilder(builder =>
        {
            builder.ConfigureServices(services =>
            {
                // Replace with test database
                var descriptor = services.SingleOrDefault(
                    d => d.ServiceType == typeof(DbContextOptions<AppDbContext>));

                if (descriptor != null)
                    services.Remove(descriptor);

                services.AddDbContext<AppDbContext>(options =>
                    options.UseInMemoryDatabase("TestDb"));
            });
        });

        _client = _factory.CreateClient();
    }

    [Fact]
    public async Task GetAll_ReturnsOkWithList()
    {
        // Act
        var response = await _client.GetAsync("/api/{{entityName}}s");

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.OK);

        var content = await response.Content
            .ReadFromJsonAsync<IEnumerable<{{EntityName}}Dto>>();

        content.Should().NotBeNull();
    }

    [Fact]
    public async Task GetById_WhenExists_ReturnsOk()
    {
        // Arrange - Seed data
        using var scope = _factory.Services.CreateScope();
        var context = scope.ServiceProvider.GetRequiredService<AppDbContext>();

        var entity = {{EntityName}}.Create("Test", null, 100, Guid.NewGuid());
        context.{{EntityName}}s.Add(entity);
        await context.SaveChangesAsync();

        // Act
        var response = await _client.GetAsync($"/api/{{entityName}}s/{entity.Id}");

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.OK);
    }

    [Fact]
    public async Task GetById_WhenNotExists_ReturnsNotFound()
    {
        // Act
        var response = await _client.GetAsync($"/api/{{entityName}}s/{Guid.NewGuid()}");

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.NotFound);
    }

    [Fact]
    public async Task Create_ValidData_ReturnsCreated()
    {
        // Arrange
        var createDto = new Create{{EntityName}}Dto
        {
            Name = "New Item",
            Price = 99.99m,
            CategoryId = Guid.NewGuid()
        };

        // Act
        var response = await _client.PostAsJsonAsync("/api/{{entityName}}s", createDto);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.Created);
        response.Headers.Location.Should().NotBeNull();
    }

    [Fact]
    public async Task Create_InvalidData_ReturnsBadRequest()
    {
        // Arrange - Empty name
        var createDto = new Create{{EntityName}}Dto
        {
            Name = "",
            Price = 99.99m
        };

        // Act
        var response = await _client.PostAsJsonAsync("/api/{{entityName}}s", createDto);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.BadRequest);
    }
}
```

## Generation Checklist

- [ ] Arrange-Act-Assert pattern
- [ ] Mock dependencies properly
- [ ] Test happy path and edge cases
- [ ] Use FluentAssertions
- [ ] Verify mock interactions
- [ ] Integration tests use WebApplicationFactory
- [ ] Test database isolation
- [ ] CancellationToken in async tests

## Related Templates

- `templates/dotnet-test.md` - Full test template
