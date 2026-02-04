---
name: migrations
description: Entity Framework Core migration management
applies_to: dotnet
type: skill
---

# EF Core Migrations

## Overview

Code-first migrations allow you to evolve your database schema alongside your code, maintaining version control and reproducibility.

## Basic Commands

### CLI Commands

```bash
# Add a new migration
dotnet ef migrations add InitialCreate --project src/MyApp.Infrastructure --startup-project src/MyApp.API

# Update database
dotnet ef database update --project src/MyApp.Infrastructure --startup-project src/MyApp.API

# Remove last migration (if not applied)
dotnet ef migrations remove --project src/MyApp.Infrastructure --startup-project src/MyApp.API

# Generate SQL script
dotnet ef migrations script --idempotent --output migrations.sql --project src/MyApp.Infrastructure --startup-project src/MyApp.API

# List migrations
dotnet ef migrations list --project src/MyApp.Infrastructure --startup-project src/MyApp.API

# Rollback to specific migration
dotnet ef database update PreviousMigrationName --project src/MyApp.Infrastructure --startup-project src/MyApp.API
```

### Package Manager Console

```powershell
# Add migration
Add-Migration InitialCreate -Project MyApp.Infrastructure -StartupProject MyApp.API

# Update database
Update-Database -Project MyApp.Infrastructure -StartupProject MyApp.API

# Generate script
Script-Migration -Idempotent -Output migrations.sql

# Remove last migration
Remove-Migration -Project MyApp.Infrastructure
```

## Migration Structure

### Generated Migration

```csharp
// Migrations/20240115120000_AddProductsTable.cs
public partial class AddProductsTable : Migration
{
    protected override void Up(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.CreateTable(
            name: "Products",
            columns: table => new
            {
                Id = table.Column<Guid>(type: "uniqueidentifier", nullable: false),
                Name = table.Column<string>(type: "nvarchar(200)", maxLength: 200, nullable: false),
                Description = table.Column<string>(type: "nvarchar(1000)", maxLength: 1000, nullable: true),
                Price = table.Column<decimal>(type: "decimal(18,2)", precision: 18, scale: 2, nullable: false),
                CategoryId = table.Column<Guid>(type: "uniqueidentifier", nullable: false),
                CreatedAt = table.Column<DateTime>(type: "datetime2", nullable: false),
                UpdatedAt = table.Column<DateTime>(type: "datetime2", nullable: true)
            },
            constraints: table =>
            {
                table.PrimaryKey("PK_Products", x => x.Id);
                table.ForeignKey(
                    name: "FK_Products_Categories_CategoryId",
                    column: x => x.CategoryId,
                    principalTable: "Categories",
                    principalColumn: "Id",
                    onDelete: ReferentialAction.Restrict);
            });

        migrationBuilder.CreateIndex(
            name: "IX_Products_CategoryId",
            table: "Products",
            column: "CategoryId");

        migrationBuilder.CreateIndex(
            name: "IX_Products_Name",
            table: "Products",
            column: "Name");
    }

    protected override void Down(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.DropTable(
            name: "Products");
    }
}
```

## Custom Migrations

### Data Migration

```csharp
public partial class AddDefaultCategories : Migration
{
    protected override void Up(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.InsertData(
            table: "Categories",
            columns: new[] { "Id", "Name", "CreatedAt" },
            values: new object[,]
            {
                { Guid.NewGuid(), "Electronics", DateTime.UtcNow },
                { Guid.NewGuid(), "Clothing", DateTime.UtcNow },
                { Guid.NewGuid(), "Books", DateTime.UtcNow }
            });
    }

    protected override void Down(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.Sql("DELETE FROM Categories WHERE Name IN ('Electronics', 'Clothing', 'Books')");
    }
}
```

### Raw SQL Migration

```csharp
public partial class AddFullTextIndex : Migration
{
    protected override void Up(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.Sql(@"
            CREATE FULLTEXT CATALOG ProductsCatalog AS DEFAULT;

            CREATE FULLTEXT INDEX ON Products(Name, Description)
            KEY INDEX PK_Products ON ProductsCatalog;
        ");
    }

    protected override void Down(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.Sql(@"
            DROP FULLTEXT INDEX ON Products;
            DROP FULLTEXT CATALOG ProductsCatalog;
        ");
    }
}
```

### Stored Procedure Migration

```csharp
public partial class AddGetProductsByCategory : Migration
{
    protected override void Up(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.Sql(@"
            CREATE PROCEDURE [dbo].[GetProductsByCategory]
                @CategoryId UNIQUEIDENTIFIER
            AS
            BEGIN
                SELECT Id, Name, Price
                FROM Products
                WHERE CategoryId = @CategoryId
                AND IsDeleted = 0
                ORDER BY Name;
            END
        ");
    }

    protected override void Down(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.Sql("DROP PROCEDURE [dbo].[GetProductsByCategory]");
    }
}
```

## Automatic Migration at Startup

### Development Only

```csharp
// Program.cs
if (app.Environment.IsDevelopment())
{
    using var scope = app.Services.CreateScope();
    var context = scope.ServiceProvider.GetRequiredService<AppDbContext>();
    await context.Database.MigrateAsync();
}
```

### With Health Check

```csharp
// Infrastructure/HealthChecks/DatabaseMigrationHealthCheck.cs
public class DatabaseMigrationHealthCheck : IHealthCheck
{
    private readonly AppDbContext _context;

    public DatabaseMigrationHealthCheck(AppDbContext context)
    {
        _context = context;
    }

    public async Task<HealthCheckResult> CheckHealthAsync(
        HealthCheckContext context,
        CancellationToken cancellationToken = default)
    {
        var pending = await _context.Database
            .GetPendingMigrationsAsync(cancellationToken);

        if (pending.Any())
        {
            return HealthCheckResult.Unhealthy(
                $"Pending migrations: {string.Join(", ", pending)}");
        }

        return HealthCheckResult.Healthy("All migrations applied");
    }
}
```

## Database Seeding

### Using HasData

```csharp
// In Configuration class
public void Configure(EntityTypeBuilder<Category> builder)
{
    builder.HasData(
        new Category { Id = Guid.Parse("..."), Name = "Electronics" },
        new Category { Id = Guid.Parse("..."), Name = "Clothing" }
    );
}
```

### Using DbContext Extension

```csharp
// Infrastructure/Persistence/AppDbContextSeed.cs
public static class AppDbContextSeed
{
    public static async Task SeedAsync(
        AppDbContext context,
        ILogger logger)
    {
        if (!await context.Categories.AnyAsync())
        {
            var categories = new List<Category>
            {
                Category.Create("Electronics"),
                Category.Create("Clothing"),
                Category.Create("Books")
            };

            await context.Categories.AddRangeAsync(categories);
            await context.SaveChangesAsync();

            logger.LogInformation("Seeded {Count} categories", categories.Count);
        }
    }
}

// Program.cs
using var scope = app.Services.CreateScope();
var context = scope.ServiceProvider.GetRequiredService<AppDbContext>();
var logger = scope.ServiceProvider.GetRequiredService<ILogger<Program>>();
await AppDbContextSeed.SeedAsync(context, logger);
```

## Best Practices

### 1. Use Descriptive Names

```bash
# ✅ Good
dotnet ef migrations add AddOrderStatusColumn
dotnet ef migrations add RenameProductSkuToCode
dotnet ef migrations add AddIndexOnProductName

# ❌ Bad
dotnet ef migrations add Update1
dotnet ef migrations add Fix
dotnet ef migrations add Changes
```

### 2. Keep Migrations Small

```bash
# ✅ Good - One logical change per migration
dotnet ef migrations add AddProductsTable
dotnet ef migrations add AddCategoriesTable
dotnet ef migrations add AddProductCategoryRelation

# ❌ Bad - Too many changes in one migration
dotnet ef migrations add AddAllEntities
```

### 3. Always Provide Down Method

```csharp
// ✅ Good - Reversible
protected override void Down(MigrationBuilder migrationBuilder)
{
    migrationBuilder.DropColumn(
        name: "NewColumn",
        table: "Products");
}

// ❌ Bad - Non-reversible
protected override void Down(MigrationBuilder migrationBuilder)
{
    // Nothing here or throws
}
```

### 4. Use Idempotent Scripts for Production

```bash
# Generate idempotent script
dotnet ef migrations script --idempotent --output deploy.sql
```

### 5. Version Control Best Practices

- Never edit applied migrations
- Don't delete applied migrations
- Merge migration conflicts carefully
- Use consistent naming

## Related Skills

- `skills/database/ef-core-patterns.md`
- `skills/database/repository-pattern.md`
