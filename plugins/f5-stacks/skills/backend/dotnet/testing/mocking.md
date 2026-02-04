# Mocking with Moq - ASP.NET Core Testing

## Overview

Moq is the most popular mocking framework for .NET, providing a simple API for creating mock objects and verifying interactions in unit tests.

## Basic Mocking Setup

```csharp
// ProductServiceTests.cs
using Moq;
using FluentAssertions;

public class ProductServiceTests
{
    private readonly Mock<IProductRepository> _mockRepository;
    private readonly Mock<IUnitOfWork> _mockUnitOfWork;
    private readonly Mock<ILogger<ProductService>> _mockLogger;
    private readonly ProductService _sut;

    public ProductServiceTests()
    {
        _mockRepository = new Mock<IProductRepository>();
        _mockUnitOfWork = new Mock<IUnitOfWork>();
        _mockLogger = new Mock<ILogger<ProductService>>();

        _sut = new ProductService(
            _mockRepository.Object,
            _mockUnitOfWork.Object,
            _mockLogger.Object);
    }
}
```

## Setup Return Values

```csharp
// Setup method return values
[Fact]
public async Task GetProductById_ShouldReturnProduct_WhenExists()
{
    // Arrange
    var productId = Guid.NewGuid();
    var expectedProduct = new Product
    {
        Id = productId,
        Name = "Test Product",
        Price = 99.99m
    };

    _mockRepository
        .Setup(r => r.GetByIdAsync(productId, It.IsAny<CancellationToken>()))
        .ReturnsAsync(expectedProduct);

    // Act
    var result = await _sut.GetByIdAsync(productId);

    // Assert
    result.Should().NotBeNull();
    result.Id.Should().Be(productId);
}

// Setup with argument matching
[Fact]
public async Task SearchProducts_ShouldFilterByCategory()
{
    var products = new List<Product>
    {
        new Product { Name = "Product 1", CategoryId = 1 },
        new Product { Name = "Product 2", CategoryId = 2 }
    };

    _mockRepository
        .Setup(r => r.FindAsync(
            It.Is<Expression<Func<Product, bool>>>(e => true),
            It.IsAny<CancellationToken>()))
        .ReturnsAsync(products);

    // Act & Assert...
}
```

## Argument Matchers

```csharp
// It.IsAny<T>() - matches any value
_mockRepository
    .Setup(r => r.GetByIdAsync(It.IsAny<Guid>(), It.IsAny<CancellationToken>()))
    .ReturnsAsync(new Product());

// It.Is<T>(predicate) - matches specific condition
_mockRepository
    .Setup(r => r.GetByIdAsync(
        It.Is<Guid>(id => id != Guid.Empty),
        It.IsAny<CancellationToken>()))
    .ReturnsAsync(new Product());

// It.IsIn<T>() - matches any value in collection
_mockRepository
    .Setup(r => r.GetByIdAsync(
        It.IsIn(validIds),
        It.IsAny<CancellationToken>()))
    .ReturnsAsync(new Product());

// It.IsNotIn<T>() - matches any value not in collection
_mockRepository
    .Setup(r => r.GetByIdAsync(
        It.IsNotIn(invalidIds),
        It.IsAny<CancellationToken>()))
    .ReturnsAsync(new Product());

// It.IsRegex() - matches string pattern
_mockService
    .Setup(s => s.SendEmail(It.IsRegex(@"^[^@]+@[^@]+\.[^@]+$")))
    .Returns(true);
```

## Verifying Method Calls

```csharp
[Fact]
public async Task CreateProduct_ShouldCallRepositoryAdd()
{
    // Arrange
    var createDto = new CreateProductDto { Name = "New Product", Price = 50.00m };

    _mockRepository
        .Setup(r => r.AddAsync(It.IsAny<Product>(), It.IsAny<CancellationToken>()))
        .Returns(Task.CompletedTask);

    _mockUnitOfWork
        .Setup(u => u.SaveChangesAsync(It.IsAny<CancellationToken>()))
        .ReturnsAsync(1);

    // Act
    await _sut.CreateAsync(createDto);

    // Assert - Verify method was called
    _mockRepository.Verify(
        r => r.AddAsync(It.IsAny<Product>(), It.IsAny<CancellationToken>()),
        Times.Once);

    _mockUnitOfWork.Verify(
        u => u.SaveChangesAsync(It.IsAny<CancellationToken>()),
        Times.Once);
}

// Verify with specific arguments
_mockRepository.Verify(
    r => r.AddAsync(
        It.Is<Product>(p => p.Name == "New Product"),
        It.IsAny<CancellationToken>()),
    Times.Once);

// Verify never called
_mockRepository.Verify(
    r => r.DeleteAsync(It.IsAny<Product>(), It.IsAny<CancellationToken>()),
    Times.Never);

// Verify call count
_mockRepository.Verify(
    r => r.GetByIdAsync(It.IsAny<Guid>(), It.IsAny<CancellationToken>()),
    Times.Exactly(2));
```

## Mocking Exceptions

```csharp
[Fact]
public async Task GetProduct_ShouldThrow_WhenRepositoryFails()
{
    // Arrange
    _mockRepository
        .Setup(r => r.GetByIdAsync(It.IsAny<Guid>(), It.IsAny<CancellationToken>()))
        .ThrowsAsync(new DatabaseException("Connection failed"));

    // Act & Assert
    await _sut.Invoking(s => s.GetByIdAsync(Guid.NewGuid()))
        .Should()
        .ThrowAsync<DatabaseException>()
        .WithMessage("Connection failed");
}

// Throw on specific call
_mockRepository
    .SetupSequence(r => r.GetByIdAsync(It.IsAny<Guid>(), It.IsAny<CancellationToken>()))
    .ReturnsAsync(new Product())
    .ThrowsAsync(new DatabaseException());
```

## Sequential Returns

```csharp
[Fact]
public async Task RetryOperation_ShouldSucceedOnSecondAttempt()
{
    _mockRepository
        .SetupSequence(r => r.GetByIdAsync(It.IsAny<Guid>(), It.IsAny<CancellationToken>()))
        .ThrowsAsync(new TimeoutException())  // First call throws
        .ReturnsAsync(new Product { Name = "Success" });  // Second call succeeds

    // Act with retry logic
    var result = await _sut.GetWithRetryAsync(Guid.NewGuid());

    // Assert
    result.Name.Should().Be("Success");
}
```

## Callback Actions

```csharp
[Fact]
public async Task CreateProduct_ShouldSetCreatedDate()
{
    Product? capturedProduct = null;

    _mockRepository
        .Setup(r => r.AddAsync(It.IsAny<Product>(), It.IsAny<CancellationToken>()))
        .Callback<Product, CancellationToken>((product, ct) =>
        {
            capturedProduct = product;
            product.Id = Guid.NewGuid(); // Simulate DB generating ID
        })
        .Returns(Task.CompletedTask);

    _mockUnitOfWork
        .Setup(u => u.SaveChangesAsync(It.IsAny<CancellationToken>()))
        .ReturnsAsync(1);

    // Act
    var result = await _sut.CreateAsync(new CreateProductDto { Name = "Test" });

    // Assert
    capturedProduct.Should().NotBeNull();
    capturedProduct!.CreatedAt.Should().BeCloseTo(DateTime.UtcNow, TimeSpan.FromSeconds(1));
}
```

## Mocking HttpClient

```csharp
public class ExternalApiServiceTests
{
    private readonly Mock<HttpMessageHandler> _mockHttpHandler;
    private readonly HttpClient _httpClient;
    private readonly ExternalApiService _sut;

    public ExternalApiServiceTests()
    {
        _mockHttpHandler = new Mock<HttpMessageHandler>();
        _httpClient = new HttpClient(_mockHttpHandler.Object)
        {
            BaseAddress = new Uri("https://api.example.com")
        };
        _sut = new ExternalApiService(_httpClient);
    }

    [Fact]
    public async Task GetData_ShouldReturnDeserializedResponse()
    {
        // Arrange
        var responseContent = JsonSerializer.Serialize(new { Data = "test" });
        var response = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(responseContent, Encoding.UTF8, "application/json")
        };

        _mockHttpHandler
            .Protected()
            .Setup<Task<HttpResponseMessage>>(
                "SendAsync",
                ItExpr.IsAny<HttpRequestMessage>(),
                ItExpr.IsAny<CancellationToken>())
            .ReturnsAsync(response);

        // Act
        var result = await _sut.GetDataAsync();

        // Assert
        result.Data.Should().Be("test");
    }
}
```

## Mocking DbContext

```csharp
public class ProductRepositoryTests
{
    private readonly Mock<DbSet<Product>> _mockDbSet;
    private readonly Mock<ApplicationDbContext> _mockContext;
    private readonly ProductRepository _sut;

    public ProductRepositoryTests()
    {
        var products = new List<Product>
        {
            new Product { Id = Guid.NewGuid(), Name = "Product 1" },
            new Product { Id = Guid.NewGuid(), Name = "Product 2" }
        }.AsQueryable();

        _mockDbSet = new Mock<DbSet<Product>>();
        _mockDbSet.As<IAsyncEnumerable<Product>>()
            .Setup(m => m.GetAsyncEnumerator(It.IsAny<CancellationToken>()))
            .Returns(new TestAsyncEnumerator<Product>(products.GetEnumerator()));
        _mockDbSet.As<IQueryable<Product>>()
            .Setup(m => m.Provider)
            .Returns(new TestAsyncQueryProvider<Product>(products.Provider));
        _mockDbSet.As<IQueryable<Product>>()
            .Setup(m => m.Expression).Returns(products.Expression);
        _mockDbSet.As<IQueryable<Product>>()
            .Setup(m => m.ElementType).Returns(products.ElementType);

        _mockContext = new Mock<ApplicationDbContext>();
        _mockContext.Setup(c => c.Products).Returns(_mockDbSet.Object);

        _sut = new ProductRepository(_mockContext.Object);
    }
}
```

## AutoMocker for Automatic Dependency Injection

```csharp
// Using Moq.AutoMock
using Moq.AutoMock;

public class ProductServiceAutoMockTests
{
    private readonly AutoMocker _mocker;
    private readonly ProductService _sut;

    public ProductServiceAutoMockTests()
    {
        _mocker = new AutoMocker();
        _sut = _mocker.CreateInstance<ProductService>();
    }

    [Fact]
    public async Task GetProduct_ShouldCallRepository()
    {
        // Arrange
        var productId = Guid.NewGuid();
        var product = new Product { Id = productId, Name = "Test" };

        _mocker.GetMock<IProductRepository>()
            .Setup(r => r.GetByIdAsync(productId, It.IsAny<CancellationToken>()))
            .ReturnsAsync(product);

        // Act
        var result = await _sut.GetByIdAsync(productId);

        // Assert
        result.Should().NotBeNull();
        _mocker.GetMock<IProductRepository>()
            .Verify(r => r.GetByIdAsync(productId, It.IsAny<CancellationToken>()), Times.Once);
    }
}
```

## Best Practices

1. **Mock Only What You Own**: Don't mock third-party types directly
2. **Use Strict Mode Sparingly**: MockBehavior.Strict requires all setups
3. **Verify Important Interactions**: Don't over-verify
4. **Keep Mocks Simple**: Complex setups indicate design issues
5. **Use AutoMocker**: Reduces boilerplate for services with many dependencies
6. **Reset Between Tests**: Use fresh mocks for each test
