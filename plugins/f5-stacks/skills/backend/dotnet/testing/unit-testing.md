---
name: unit-testing
description: xUnit testing patterns for ASP.NET Core
applies_to: dotnet
type: skill
---

# Unit Testing with xUnit

## Overview

Unit tests verify individual components in isolation. xUnit is the recommended testing framework for .NET, providing a clean, extensible testing experience.

## Setup

### Installation

```bash
dotnet add package xunit
dotnet add package xunit.runner.visualstudio
dotnet add package Moq
dotnet add package FluentAssertions
dotnet add package Microsoft.NET.Test.Sdk
```

### Project Structure

```
tests/
├── MyApp.Domain.Tests/
│   └── Entities/
│       └── ProductTests.cs
├── MyApp.Application.Tests/
│   ├── Services/
│   │   └── ProductServiceTests.cs
│   └── Handlers/
│       └── CreateProductHandlerTests.cs
└── MyApp.API.Tests/
    └── Controllers/
        └── ProductsControllerTests.cs
```

## Basic Test Structure

### Arrange-Act-Assert Pattern

```csharp
// Tests/Unit/Services/ProductServiceTests.cs
public class ProductServiceTests
{
    [Fact]
    public async Task GetByIdAsync_WhenProductExists_ReturnsProduct()
    {
        // Arrange
        var productId = Guid.NewGuid();
        var product = Product.Create("Test Product", "Description", 99.99m);

        var repositoryMock = new Mock<IProductRepository>();
        repositoryMock
            .Setup(x => x.GetByIdAsync(productId, It.IsAny<CancellationToken>()))
            .ReturnsAsync(product);

        var service = new ProductService(repositoryMock.Object);

        // Act
        var result = await service.GetByIdAsync(productId);

        // Assert
        result.Should().NotBeNull();
        result!.Name.Should().Be("Test Product");
    }

    [Fact]
    public async Task GetByIdAsync_WhenProductNotFound_ReturnsNull()
    {
        // Arrange
        var repositoryMock = new Mock<IProductRepository>();
        repositoryMock
            .Setup(x => x.GetByIdAsync(It.IsAny<Guid>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync((Product?)null);

        var service = new ProductService(repositoryMock.Object);

        // Act
        var result = await service.GetByIdAsync(Guid.NewGuid());

        // Assert
        result.Should().BeNull();
    }
}
```

## Test Fixtures

### Class Fixture (Shared Setup)

```csharp
// Shared setup across all tests in a class
public class DatabaseFixture : IDisposable
{
    public AppDbContext Context { get; }

    public DatabaseFixture()
    {
        var options = new DbContextOptionsBuilder<AppDbContext>()
            .UseInMemoryDatabase(Guid.NewGuid().ToString())
            .Options;

        Context = new AppDbContext(options);
        SeedData();
    }

    private void SeedData()
    {
        Context.Products.Add(Product.Create("Test", null, 10));
        Context.SaveChanges();
    }

    public void Dispose()
    {
        Context.Dispose();
    }
}

public class ProductRepositoryTests : IClassFixture<DatabaseFixture>
{
    private readonly DatabaseFixture _fixture;

    public ProductRepositoryTests(DatabaseFixture fixture)
    {
        _fixture = fixture;
    }

    [Fact]
    public async Task GetAllAsync_ReturnsProducts()
    {
        var repository = new ProductRepository(_fixture.Context);
        var products = await repository.GetAllAsync();

        products.Should().NotBeEmpty();
    }
}
```

### Collection Fixture (Shared Across Classes)

```csharp
[CollectionDefinition("Database")]
public class DatabaseCollection : ICollectionFixture<DatabaseFixture> { }

[Collection("Database")]
public class ProductServiceTests
{
    private readonly DatabaseFixture _fixture;

    public ProductServiceTests(DatabaseFixture fixture)
    {
        _fixture = fixture;
    }
}

[Collection("Database")]
public class OrderServiceTests
{
    private readonly DatabaseFixture _fixture;

    public OrderServiceTests(DatabaseFixture fixture)
    {
        _fixture = fixture;
    }
}
```

## Parameterized Tests

### Theory with InlineData

```csharp
public class PriceCalculatorTests
{
    [Theory]
    [InlineData(100, 0.10, 90)]    // 10% discount
    [InlineData(100, 0.25, 75)]    // 25% discount
    [InlineData(50, 0.50, 25)]     // 50% discount
    public void ApplyDiscount_ReturnsCorrectPrice(
        decimal price,
        decimal discountRate,
        decimal expected)
    {
        var calculator = new PriceCalculator();

        var result = calculator.ApplyDiscount(price, discountRate);

        result.Should().Be(expected);
    }
}
```

### Theory with MemberData

```csharp
public class ValidationTests
{
    public static IEnumerable<object[]> InvalidEmailData =>
        new List<object[]>
        {
            new object[] { null!, "Email is required" },
            new object[] { "", "Email is required" },
            new object[] { "invalid", "Email format is invalid" },
            new object[] { "test@", "Email format is invalid" }
        };

    [Theory]
    [MemberData(nameof(InvalidEmailData))]
    public void ValidateEmail_WithInvalidInput_ReturnsError(
        string email,
        string expectedError)
    {
        var validator = new EmailValidator();

        var result = validator.Validate(email);

        result.IsValid.Should().BeFalse();
        result.Error.Should().Be(expectedError);
    }
}
```

### Theory with ClassData

```csharp
public class ProductTestData : IEnumerable<object[]>
{
    public IEnumerator<object[]> GetEnumerator()
    {
        yield return new object[]
        {
            new CreateProductDto { Name = "Product 1", Price = 10 },
            true
        };
        yield return new object[]
        {
            new CreateProductDto { Name = "", Price = 10 },
            false
        };
        yield return new object[]
        {
            new CreateProductDto { Name = "Product", Price = -1 },
            false
        };
    }

    IEnumerator IEnumerable.GetEnumerator() => GetEnumerator();
}

[Theory]
[ClassData(typeof(ProductTestData))]
public void Validate_ReturnsExpectedResult(
    CreateProductDto dto,
    bool expectedValid)
{
    var validator = new CreateProductValidator();

    var result = validator.Validate(dto);

    result.IsValid.Should().Be(expectedValid);
}
```

## Mocking with Moq

### Basic Mocking

```csharp
public class ProductServiceTests
{
    private readonly Mock<IProductRepository> _repositoryMock;
    private readonly Mock<IUnitOfWork> _unitOfWorkMock;
    private readonly Mock<IMapper> _mapperMock;
    private readonly ProductService _sut;

    public ProductServiceTests()
    {
        _repositoryMock = new Mock<IProductRepository>();
        _unitOfWorkMock = new Mock<IUnitOfWork>();
        _mapperMock = new Mock<IMapper>();

        _sut = new ProductService(
            _repositoryMock.Object,
            _unitOfWorkMock.Object,
            _mapperMock.Object);
    }

    [Fact]
    public async Task CreateAsync_CallsRepositoryAndSaves()
    {
        // Arrange
        var dto = new CreateProductDto { Name = "Test", Price = 10 };
        var product = Product.Create("Test", null, 10);

        _mapperMock
            .Setup(x => x.Map<Product>(dto))
            .Returns(product);

        _mapperMock
            .Setup(x => x.Map<ProductDto>(product))
            .Returns(new ProductDto { Name = "Test" });

        // Act
        await _sut.CreateAsync(dto);

        // Assert
        _repositoryMock.Verify(
            x => x.AddAsync(It.IsAny<Product>(), It.IsAny<CancellationToken>()),
            Times.Once);

        _unitOfWorkMock.Verify(
            x => x.SaveChangesAsync(It.IsAny<CancellationToken>()),
            Times.Once);
    }
}
```

### Advanced Mocking

```csharp
// Callback for capturing arguments
_repositoryMock
    .Setup(x => x.AddAsync(It.IsAny<Product>(), It.IsAny<CancellationToken>()))
    .Callback<Product, CancellationToken>((p, ct) =>
    {
        capturedProduct = p;
    });

// Sequential returns
_repositoryMock
    .SetupSequence(x => x.GetByIdAsync(It.IsAny<Guid>(), It.IsAny<CancellationToken>()))
    .ReturnsAsync(product1)
    .ReturnsAsync(product2)
    .ReturnsAsync((Product?)null);

// Throwing exceptions
_repositoryMock
    .Setup(x => x.GetByIdAsync(It.IsAny<Guid>(), It.IsAny<CancellationToken>()))
    .ThrowsAsync(new InvalidOperationException("Database error"));

// Verify with specific arguments
_repositoryMock.Verify(
    x => x.AddAsync(
        It.Is<Product>(p => p.Name == "Expected Name"),
        It.IsAny<CancellationToken>()),
    Times.Once);
```

## FluentAssertions

```csharp
public class AssertionExamples
{
    [Fact]
    public void FluentAssertions_Examples()
    {
        // Basic assertions
        var result = 5;
        result.Should().Be(5);
        result.Should().BePositive();
        result.Should().BeInRange(1, 10);

        // String assertions
        var name = "John Doe";
        name.Should().StartWith("John");
        name.Should().Contain("Doe");
        name.Should().NotBeNullOrEmpty();

        // Collection assertions
        var list = new[] { 1, 2, 3 };
        list.Should().HaveCount(3);
        list.Should().Contain(2);
        list.Should().BeInAscendingOrder();

        // Object assertions
        var product = new ProductDto { Name = "Test", Price = 100 };
        product.Should().NotBeNull();
        product.Should().BeEquivalentTo(new { Name = "Test", Price = 100 });

        // Exception assertions
        Action act = () => throw new InvalidOperationException("Error");
        act.Should().Throw<InvalidOperationException>()
            .WithMessage("Error");

        // Async exception
        Func<Task> asyncAct = () => throw new InvalidOperationException();
        asyncAct.Should().ThrowAsync<InvalidOperationException>();
    }
}
```

## Best Practices

| Practice | Recommendation |
|----------|----------------|
| Naming | `MethodName_Scenario_ExpectedResult` |
| Isolation | Each test independent |
| Single assertion | One logical assertion per test |
| AAA pattern | Arrange, Act, Assert |
| Mock only dependencies | Don't mock the SUT |
| Use fixtures | Share expensive setup |

## Related Skills

- `skills/testing/integration-testing.md`
- `templates/dotnet-test.md`
