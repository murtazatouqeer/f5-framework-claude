---
name: integration-testing
description: WebApplicationFactory integration testing for ASP.NET Core
applies_to: dotnet
type: skill
---

# Integration Testing

## Overview

Integration tests verify that multiple components work together correctly. ASP.NET Core provides WebApplicationFactory for testing APIs with a real HTTP pipeline.

## Setup

### Installation

```bash
dotnet add package Microsoft.AspNetCore.Mvc.Testing
dotnet add package Microsoft.EntityFrameworkCore.InMemory
```

### Base Test Class

```csharp
// Tests/Integration/IntegrationTestBase.cs
public abstract class IntegrationTestBase
    : IClassFixture<CustomWebApplicationFactory>
{
    protected readonly HttpClient Client;
    protected readonly CustomWebApplicationFactory Factory;

    protected IntegrationTestBase(CustomWebApplicationFactory factory)
    {
        Factory = factory;
        Client = factory.CreateClient(new WebApplicationFactoryClientOptions
        {
            AllowAutoRedirect = false
        });
    }

    protected async Task<T?> GetAsync<T>(string url)
    {
        var response = await Client.GetAsync(url);
        response.EnsureSuccessStatusCode();
        return await response.Content.ReadFromJsonAsync<T>();
    }

    protected async Task<HttpResponseMessage> PostAsync<T>(string url, T data)
    {
        return await Client.PostAsJsonAsync(url, data);
    }

    protected async Task AuthenticateAsync(string email = "test@test.com")
    {
        var token = await GetTestTokenAsync(email);
        Client.DefaultRequestHeaders.Authorization =
            new AuthenticationHeaderValue("Bearer", token);
    }

    private async Task<string> GetTestTokenAsync(string email)
    {
        // Generate test JWT token
        using var scope = Factory.Services.CreateScope();
        var tokenService = scope.ServiceProvider
            .GetRequiredService<ITokenService>();

        var user = new ApplicationUser { Email = email, Id = Guid.NewGuid() };
        return tokenService.GenerateAccessToken(user);
    }
}
```

### Custom WebApplicationFactory

```csharp
// Tests/Integration/CustomWebApplicationFactory.cs
public class CustomWebApplicationFactory
    : WebApplicationFactory<Program>
{
    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        builder.ConfigureTestServices(services =>
        {
            // Remove real database
            var descriptor = services.SingleOrDefault(
                d => d.ServiceType == typeof(DbContextOptions<AppDbContext>));

            if (descriptor != null)
                services.Remove(descriptor);

            // Add in-memory database
            services.AddDbContext<AppDbContext>(options =>
            {
                options.UseInMemoryDatabase("TestDb");
            });

            // Replace external services with fakes
            services.AddScoped<IEmailService, FakeEmailService>();

            // Build service provider
            var sp = services.BuildServiceProvider();

            // Seed test data
            using var scope = sp.CreateScope();
            var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
            db.Database.EnsureCreated();
            SeedTestData(db);
        });

        builder.UseEnvironment("Testing");
    }

    private static void SeedTestData(AppDbContext context)
    {
        var category = new Category { Id = Guid.NewGuid(), Name = "Test Category" };
        context.Categories.Add(category);

        var product = Product.Create("Test Product", "Description", 99.99m);
        context.Products.Add(product);

        context.SaveChanges();
    }
}
```

## Controller Integration Tests

### CRUD Tests

```csharp
// Tests/Integration/Controllers/ProductsControllerTests.cs
public class ProductsControllerTests : IntegrationTestBase
{
    public ProductsControllerTests(CustomWebApplicationFactory factory)
        : base(factory) { }

    [Fact]
    public async Task GetAll_ReturnsSuccessAndProducts()
    {
        // Act
        var response = await Client.GetAsync("/api/products");

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.OK);

        var products = await response.Content
            .ReadFromJsonAsync<IEnumerable<ProductDto>>();

        products.Should().NotBeEmpty();
    }

    [Fact]
    public async Task GetById_WhenExists_ReturnsProduct()
    {
        // Arrange
        var productId = await CreateTestProductAsync();

        // Act
        var response = await Client.GetAsync($"/api/products/{productId}");

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.OK);

        var product = await response.Content.ReadFromJsonAsync<ProductDto>();
        product.Should().NotBeNull();
        product!.Id.Should().Be(productId);
    }

    [Fact]
    public async Task GetById_WhenNotExists_ReturnsNotFound()
    {
        // Act
        var response = await Client.GetAsync($"/api/products/{Guid.NewGuid()}");

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.NotFound);
    }

    [Fact]
    public async Task Create_WithValidData_ReturnsCreated()
    {
        // Arrange
        await AuthenticateAsync();
        var createDto = new CreateProductDto
        {
            Name = "New Product",
            Price = 49.99m,
            CategoryId = await GetTestCategoryIdAsync()
        };

        // Act
        var response = await Client.PostAsJsonAsync("/api/products", createDto);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.Created);
        response.Headers.Location.Should().NotBeNull();

        var created = await response.Content.ReadFromJsonAsync<ProductDto>();
        created!.Name.Should().Be("New Product");
    }

    [Fact]
    public async Task Create_WithInvalidData_ReturnsBadRequest()
    {
        // Arrange
        await AuthenticateAsync();
        var createDto = new CreateProductDto
        {
            Name = "", // Invalid - empty
            Price = -10 // Invalid - negative
        };

        // Act
        var response = await Client.PostAsJsonAsync("/api/products", createDto);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.BadRequest);

        var problem = await response.Content
            .ReadFromJsonAsync<ValidationProblemDetails>();

        problem!.Errors.Should().ContainKey("Name");
        problem.Errors.Should().ContainKey("Price");
    }

    [Fact]
    public async Task Create_WithoutAuth_ReturnsUnauthorized()
    {
        // Arrange - No authentication
        var createDto = new CreateProductDto { Name = "Test", Price = 10 };

        // Act
        var response = await Client.PostAsJsonAsync("/api/products", createDto);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.Unauthorized);
    }

    [Fact]
    public async Task Update_WhenExists_ReturnsUpdatedProduct()
    {
        // Arrange
        await AuthenticateAsync();
        var productId = await CreateTestProductAsync();
        var updateDto = new UpdateProductDto
        {
            Name = "Updated Name",
            Price = 199.99m
        };

        // Act
        var response = await Client.PutAsJsonAsync(
            $"/api/products/{productId}",
            updateDto);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.OK);

        var updated = await response.Content.ReadFromJsonAsync<ProductDto>();
        updated!.Name.Should().Be("Updated Name");
    }

    [Fact]
    public async Task Delete_WhenExists_ReturnsNoContent()
    {
        // Arrange
        await AuthenticateAsync();
        var productId = await CreateTestProductAsync();

        // Act
        var response = await Client.DeleteAsync($"/api/products/{productId}");

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.NoContent);

        // Verify deletion
        var getResponse = await Client.GetAsync($"/api/products/{productId}");
        getResponse.StatusCode.Should().Be(HttpStatusCode.NotFound);
    }

    private async Task<Guid> CreateTestProductAsync()
    {
        await AuthenticateAsync();
        var createDto = new CreateProductDto
        {
            Name = "Test Product",
            Price = 99.99m,
            CategoryId = await GetTestCategoryIdAsync()
        };

        var response = await Client.PostAsJsonAsync("/api/products", createDto);
        var product = await response.Content.ReadFromJsonAsync<ProductDto>();
        return product!.Id;
    }

    private async Task<Guid> GetTestCategoryIdAsync()
    {
        using var scope = Factory.Services.CreateScope();
        var context = scope.ServiceProvider.GetRequiredService<AppDbContext>();
        var category = await context.Categories.FirstAsync();
        return category.Id;
    }
}
```

## Test Database Strategies

### Per-Test Isolation

```csharp
public class IsolatedDatabaseFactory : WebApplicationFactory<Program>
{
    private readonly string _databaseName = Guid.NewGuid().ToString();

    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        builder.ConfigureTestServices(services =>
        {
            services.AddDbContext<AppDbContext>(options =>
                options.UseInMemoryDatabase(_databaseName));
        });
    }
}

public class IsolatedTests : IDisposable
{
    private readonly IsolatedDatabaseFactory _factory;
    private readonly HttpClient _client;

    public IsolatedTests()
    {
        _factory = new IsolatedDatabaseFactory();
        _client = _factory.CreateClient();
    }

    public void Dispose()
    {
        _factory.Dispose();
    }
}
```

### Transaction Rollback

```csharp
public class TransactionalTests : IntegrationTestBase
{
    public TransactionalTests(CustomWebApplicationFactory factory)
        : base(factory) { }

    [Fact]
    public async Task Test_WithTransaction_RollsBack()
    {
        using var scope = Factory.Services.CreateScope();
        var context = scope.ServiceProvider.GetRequiredService<AppDbContext>();

        using var transaction = await context.Database.BeginTransactionAsync();
        try
        {
            // Test operations...

            // Verify results...
        }
        finally
        {
            await transaction.RollbackAsync();
        }
    }
}
```

## Authentication Testing

```csharp
public class AuthTests : IntegrationTestBase
{
    public AuthTests(CustomWebApplicationFactory factory)
        : base(factory) { }

    [Fact]
    public async Task ProtectedEndpoint_WithValidToken_ReturnsSuccess()
    {
        // Arrange
        await AuthenticateAsync();

        // Act
        var response = await Client.GetAsync("/api/protected");

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.OK);
    }

    [Fact]
    public async Task ProtectedEndpoint_WithExpiredToken_ReturnsUnauthorized()
    {
        // Arrange
        Client.DefaultRequestHeaders.Authorization =
            new AuthenticationHeaderValue("Bearer", "expired.token.here");

        // Act
        var response = await Client.GetAsync("/api/protected");

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.Unauthorized);
    }

    [Fact]
    public async Task AdminEndpoint_WithUserRole_ReturnsForbidden()
    {
        // Arrange
        await AuthenticateAsAsync("user", new[] { "User" });

        // Act
        var response = await Client.GetAsync("/api/admin");

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.Forbidden);
    }
}
```

## Best Practices

| Practice | Recommendation |
|----------|----------------|
| Database isolation | Use in-memory or transaction rollback |
| External services | Replace with fakes/stubs |
| Authentication | Use test tokens or mock auth |
| Seed data | Create minimal required data |
| Cleanup | Dispose resources properly |
| Parallel tests | Ensure isolation between tests |

## Related Skills

- `skills/testing/unit-testing.md`
- `templates/dotnet-test.md`
