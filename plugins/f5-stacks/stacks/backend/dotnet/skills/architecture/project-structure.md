---
name: project-structure
description: Solution and project organization for ASP.NET Core applications
applies_to: dotnet
type: skill
---

# .NET Project Structure

## Overview

Proper solution organization is crucial for maintainability, testability, and team collaboration. This guide covers standard patterns for ASP.NET Core applications.

## Solution Templates

### Simple API (Single Project)

```
MyApp/
├── MyApp.sln
├── src/
│   └── MyApp.API/
│       ├── MyApp.API.csproj
│       ├── Program.cs
│       ├── appsettings.json
│       ├── appsettings.Development.json
│       ├── Controllers/
│       ├── Models/
│       ├── Services/
│       └── Data/
├── tests/
│   └── MyApp.API.Tests/
│       └── MyApp.API.Tests.csproj
├── .gitignore
├── README.md
└── docker-compose.yml
```

### Clean Architecture (Multi-Project)

```
MyApp/
├── MyApp.sln
├── src/
│   ├── MyApp.Domain/
│   │   ├── MyApp.Domain.csproj
│   │   ├── Common/
│   │   ├── Entities/
│   │   ├── ValueObjects/
│   │   ├── Interfaces/
│   │   └── Events/
│   ├── MyApp.Application/
│   │   ├── MyApp.Application.csproj
│   │   ├── Common/
│   │   ├── Features/
│   │   ├── DTOs/
│   │   └── DependencyInjection.cs
│   ├── MyApp.Infrastructure/
│   │   ├── MyApp.Infrastructure.csproj
│   │   ├── Persistence/
│   │   ├── Services/
│   │   ├── Identity/
│   │   └── DependencyInjection.cs
│   └── MyApp.API/
│       ├── MyApp.API.csproj
│       ├── Program.cs
│       ├── Controllers/
│       ├── Middleware/
│       └── Filters/
├── tests/
│   ├── MyApp.Domain.Tests/
│   ├── MyApp.Application.Tests/
│   ├── MyApp.Infrastructure.Tests/
│   └── MyApp.API.Tests/
├── docs/
├── scripts/
├── .github/
│   └── workflows/
├── .gitignore
├── README.md
├── docker-compose.yml
└── Makefile
```

### Microservices Solution

```
MyPlatform/
├── MyPlatform.sln
├── src/
│   ├── Services/
│   │   ├── Catalog/
│   │   │   ├── Catalog.API/
│   │   │   ├── Catalog.Domain/
│   │   │   └── Catalog.Infrastructure/
│   │   ├── Orders/
│   │   │   ├── Orders.API/
│   │   │   ├── Orders.Domain/
│   │   │   └── Orders.Infrastructure/
│   │   └── Identity/
│   │       └── Identity.API/
│   ├── BuildingBlocks/
│   │   ├── EventBus/
│   │   ├── Common/
│   │   └── Infrastructure.Common/
│   └── ApiGateway/
│       └── Gateway.API/
├── tests/
│   ├── Catalog.Tests/
│   └── Orders.Tests/
├── deploy/
│   ├── k8s/
│   └── docker/
└── docker-compose.yml
```

## Project File Configuration

### Domain Project

```xml
<!-- MyApp.Domain.csproj -->
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
  </PropertyGroup>

  <!-- No external dependencies! Pure .NET -->
</Project>
```

### Application Project

```xml
<!-- MyApp.Application.csproj -->
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
  </PropertyGroup>

  <ItemGroup>
    <ProjectReference Include="..\MyApp.Domain\MyApp.Domain.csproj" />
  </ItemGroup>

  <ItemGroup>
    <PackageReference Include="AutoMapper.Extensions.Microsoft.DependencyInjection" Version="12.0.1" />
    <PackageReference Include="FluentValidation.DependencyInjectionExtensions" Version="11.9.0" />
    <PackageReference Include="MediatR" Version="12.2.0" />
  </ItemGroup>
</Project>
```

### Infrastructure Project

```xml
<!-- MyApp.Infrastructure.csproj -->
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
  </PropertyGroup>

  <ItemGroup>
    <ProjectReference Include="..\MyApp.Application\MyApp.Application.csproj" />
  </ItemGroup>

  <ItemGroup>
    <PackageReference Include="Microsoft.EntityFrameworkCore" Version="8.0.2" />
    <PackageReference Include="Microsoft.EntityFrameworkCore.SqlServer" Version="8.0.2" />
    <PackageReference Include="Microsoft.AspNetCore.Identity.EntityFrameworkCore" Version="8.0.2" />
    <PackageReference Include="Serilog.AspNetCore" Version="8.0.1" />
  </ItemGroup>
</Project>
```

### API Project

```xml
<!-- MyApp.API.csproj -->
<Project Sdk="Microsoft.NET.Sdk.Web">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
  </PropertyGroup>

  <ItemGroup>
    <ProjectReference Include="..\MyApp.Application\MyApp.Application.csproj" />
    <ProjectReference Include="..\MyApp.Infrastructure\MyApp.Infrastructure.csproj" />
  </ItemGroup>

  <ItemGroup>
    <PackageReference Include="Swashbuckle.AspNetCore" Version="6.5.0" />
  </ItemGroup>
</Project>
```

## Common Folders

### Controllers/

```
Controllers/
├── V1/
│   ├── ProductsController.cs
│   └── CategoriesController.cs
└── V2/
    └── ProductsController.cs
```

### Middleware/

```
Middleware/
├── ExceptionHandlingMiddleware.cs
├── RequestLoggingMiddleware.cs
└── AuthenticationMiddleware.cs
```

### Persistence/

```
Persistence/
├── AppDbContext.cs
├── Configurations/
│   ├── ProductConfiguration.cs
│   └── CategoryConfiguration.cs
├── Repositories/
│   └── ProductRepository.cs
├── Migrations/
└── Seed/
    └── SeedData.cs
```

## Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Solution | PascalCase | `MyCompany.MyApp` |
| Project | PascalCase | `MyApp.Domain` |
| Folder | PascalCase | `Controllers` |
| File | PascalCase | `ProductsController.cs` |
| Namespace | PascalCase | `MyApp.Domain.Entities` |

## Configuration Files

### appsettings.json

```json
{
  "Logging": {
    "LogLevel": {
      "Default": "Information",
      "Microsoft.AspNetCore": "Warning"
    }
  },
  "ConnectionStrings": {
    "DefaultConnection": "Server=.;Database=MyApp;Trusted_Connection=True;"
  },
  "Jwt": {
    "Secret": "",
    "Issuer": "MyApp",
    "Audience": "MyApp",
    "ExpirationMinutes": 60
  }
}
```

### Directory.Build.props

```xml
<!-- At solution root - applies to all projects -->
<Project>
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
    <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
  </PropertyGroup>

  <PropertyGroup>
    <Company>MyCompany</Company>
    <Product>MyApp</Product>
  </PropertyGroup>
</Project>
```

## Global Usings

```csharp
// GlobalUsings.cs
global using Microsoft.EntityFrameworkCore;
global using MediatR;
global using AutoMapper;
global using FluentValidation;
global using MyApp.Domain.Entities;
global using MyApp.Application.DTOs;
```

## Best Practices

1. **Layer Separation**: Keep project references flowing inward
2. **Consistent Naming**: Follow .NET naming conventions
3. **Configuration Per Environment**: Use appsettings.{Environment}.json
4. **Central Build Props**: Use Directory.Build.props for common settings
5. **Feature Folders**: Group related files by feature, not type

## Related Skills

- `skills/architecture/clean-architecture.md`
- `skills/architecture/vertical-slices.md`
