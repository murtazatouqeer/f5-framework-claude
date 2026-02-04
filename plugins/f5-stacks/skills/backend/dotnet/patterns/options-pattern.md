# Options Pattern - ASP.NET Core Configuration

## Overview

The Options pattern provides strongly-typed access to groups of related settings. It separates configuration concerns and supports validation, change notifications, and named options.

## Basic Options Class

```csharp
// Application/Common/Options/JwtOptions.cs
public class JwtOptions
{
    public const string SectionName = "Jwt";

    public string Secret { get; set; } = string.Empty;
    public string Issuer { get; set; } = string.Empty;
    public string Audience { get; set; } = string.Empty;
    public int ExpirationMinutes { get; set; } = 60;
    public int RefreshTokenExpirationDays { get; set; } = 7;
}

// Application/Common/Options/DatabaseOptions.cs
public class DatabaseOptions
{
    public const string SectionName = "Database";

    public string ConnectionString { get; set; } = string.Empty;
    public int MaxRetryCount { get; set; } = 3;
    public int CommandTimeout { get; set; } = 30;
    public bool EnableSensitiveDataLogging { get; set; } = false;
}

// Application/Common/Options/EmailOptions.cs
public class EmailOptions
{
    public const string SectionName = "Email";

    public string SmtpHost { get; set; } = string.Empty;
    public int SmtpPort { get; set; } = 587;
    public string Username { get; set; } = string.Empty;
    public string Password { get; set; } = string.Empty;
    public string FromAddress { get; set; } = string.Empty;
    public string FromName { get; set; } = string.Empty;
    public bool UseSsl { get; set; } = true;
}
```

## Configuration in appsettings.json

```json
{
  "Jwt": {
    "Secret": "your-super-secret-key-at-least-32-characters",
    "Issuer": "MyApp",
    "Audience": "MyApp.Users",
    "ExpirationMinutes": 60,
    "RefreshTokenExpirationDays": 7
  },
  "Database": {
    "ConnectionString": "Server=localhost;Database=MyApp;User Id=sa;Password=...;",
    "MaxRetryCount": 3,
    "CommandTimeout": 30,
    "EnableSensitiveDataLogging": false
  },
  "Email": {
    "SmtpHost": "smtp.example.com",
    "SmtpPort": 587,
    "Username": "noreply@example.com",
    "Password": "...",
    "FromAddress": "noreply@example.com",
    "FromName": "MyApp",
    "UseSsl": true
  }
}
```

## Registration Methods

```csharp
// Program.cs or DependencyInjection.cs

// Method 1: Basic binding
builder.Services.Configure<JwtOptions>(
    builder.Configuration.GetSection(JwtOptions.SectionName));

// Method 2: With validation
builder.Services.AddOptions<JwtOptions>()
    .Bind(builder.Configuration.GetSection(JwtOptions.SectionName))
    .ValidateDataAnnotations()
    .ValidateOnStart();

// Method 3: With custom validation
builder.Services.AddOptions<DatabaseOptions>()
    .Bind(builder.Configuration.GetSection(DatabaseOptions.SectionName))
    .Validate(options =>
    {
        return !string.IsNullOrEmpty(options.ConnectionString);
    }, "Connection string is required")
    .ValidateOnStart();

// Method 4: Using extension method
public static class OptionsExtensions
{
    public static IServiceCollection AddAppOptions(
        this IServiceCollection services,
        IConfiguration configuration)
    {
        services.AddOptions<JwtOptions>()
            .Bind(configuration.GetSection(JwtOptions.SectionName))
            .ValidateDataAnnotations()
            .ValidateOnStart();

        services.AddOptions<DatabaseOptions>()
            .Bind(configuration.GetSection(DatabaseOptions.SectionName))
            .ValidateDataAnnotations()
            .ValidateOnStart();

        services.AddOptions<EmailOptions>()
            .Bind(configuration.GetSection(EmailOptions.SectionName))
            .ValidateDataAnnotations()
            .ValidateOnStart();

        return services;
    }
}
```

## Data Annotations Validation

```csharp
// Application/Common/Options/JwtOptions.cs
using System.ComponentModel.DataAnnotations;

public class JwtOptions
{
    public const string SectionName = "Jwt";

    [Required]
    [MinLength(32, ErrorMessage = "Secret must be at least 32 characters")]
    public string Secret { get; set; } = string.Empty;

    [Required]
    public string Issuer { get; set; } = string.Empty;

    [Required]
    public string Audience { get; set; } = string.Empty;

    [Range(1, 1440, ErrorMessage = "Expiration must be between 1 and 1440 minutes")]
    public int ExpirationMinutes { get; set; } = 60;

    [Range(1, 365, ErrorMessage = "Refresh token expiration must be between 1 and 365 days")]
    public int RefreshTokenExpirationDays { get; set; } = 7;
}
```

## FluentValidation for Options

```csharp
// Application/Common/Options/Validators/JwtOptionsValidator.cs
public class JwtOptionsValidator : AbstractValidator<JwtOptions>
{
    public JwtOptionsValidator()
    {
        RuleFor(x => x.Secret)
            .NotEmpty()
            .MinimumLength(32)
            .WithMessage("JWT Secret must be at least 32 characters");

        RuleFor(x => x.Issuer)
            .NotEmpty();

        RuleFor(x => x.Audience)
            .NotEmpty();

        RuleFor(x => x.ExpirationMinutes)
            .InclusiveBetween(1, 1440);
    }
}

// Registration with FluentValidation
public static class OptionsValidationExtensions
{
    public static OptionsBuilder<TOptions> ValidateFluentValidation<TOptions>(
        this OptionsBuilder<TOptions> builder) where TOptions : class
    {
        builder.Services.AddSingleton<IValidateOptions<TOptions>>(sp =>
        {
            var validator = sp.GetService<IValidator<TOptions>>();
            return new FluentValidationOptions<TOptions>(
                builder.Name,
                validator!);
        });

        return builder;
    }
}

public class FluentValidationOptions<TOptions>
    : IValidateOptions<TOptions> where TOptions : class
{
    private readonly string? _name;
    private readonly IValidator<TOptions> _validator;

    public FluentValidationOptions(string? name, IValidator<TOptions> validator)
    {
        _name = name;
        _validator = validator;
    }

    public ValidateOptionsResult Validate(string? name, TOptions options)
    {
        if (_name != null && _name != name)
        {
            return ValidateOptionsResult.Skip;
        }

        var result = _validator.Validate(options);

        if (result.IsValid)
        {
            return ValidateOptionsResult.Success;
        }

        var errors = result.Errors.Select(e => e.ErrorMessage);
        return ValidateOptionsResult.Fail(errors);
    }
}
```

## Injection Methods

```csharp
// Method 1: IOptions<T> - Singleton, read at startup
public class TokenService
{
    private readonly JwtOptions _options;

    public TokenService(IOptions<JwtOptions> options)
    {
        _options = options.Value;
    }
}

// Method 2: IOptionsSnapshot<T> - Scoped, re-reads per request
public class EmailService
{
    private readonly EmailOptions _options;

    public EmailService(IOptionsSnapshot<EmailOptions> options)
    {
        _options = options.Value;
    }
}

// Method 3: IOptionsMonitor<T> - Singleton, supports change notifications
public class CacheService
{
    private CacheOptions _options;

    public CacheService(IOptionsMonitor<CacheOptions> optionsMonitor)
    {
        _options = optionsMonitor.CurrentValue;

        optionsMonitor.OnChange(newOptions =>
        {
            _options = newOptions;
            // Handle configuration change
        });
    }
}
```

## Named Options

```csharp
// For multiple configurations of the same type
public class StorageOptions
{
    public string ConnectionString { get; set; } = string.Empty;
    public string ContainerName { get; set; } = string.Empty;
}

// Registration
builder.Services.Configure<StorageOptions>("Images",
    builder.Configuration.GetSection("Storage:Images"));
builder.Services.Configure<StorageOptions>("Documents",
    builder.Configuration.GetSection("Storage:Documents"));

// Usage
public class StorageService
{
    private readonly StorageOptions _imageOptions;
    private readonly StorageOptions _documentOptions;

    public StorageService(IOptionsSnapshot<StorageOptions> optionsSnapshot)
    {
        _imageOptions = optionsSnapshot.Get("Images");
        _documentOptions = optionsSnapshot.Get("Documents");
    }
}
```

## Options Setup

```csharp
// Post-configuration (runs after binding)
builder.Services.PostConfigure<JwtOptions>(options =>
{
    if (builder.Environment.IsDevelopment())
    {
        options.ExpirationMinutes = 480; // Longer expiration in dev
    }
});

// Configure with dependencies
builder.Services.AddOptions<DatabaseOptions>()
    .Bind(builder.Configuration.GetSection(DatabaseOptions.SectionName))
    .Configure<IHostEnvironment>((options, env) =>
    {
        options.EnableSensitiveDataLogging = env.IsDevelopment();
    });
```

## Options Factory Pattern

```csharp
// For complex options that need services
public class ExternalApiOptionsFactory : IConfigureOptions<ExternalApiOptions>
{
    private readonly IConfiguration _configuration;
    private readonly ISecretManager _secretManager;

    public ExternalApiOptionsFactory(
        IConfiguration configuration,
        ISecretManager secretManager)
    {
        _configuration = configuration;
        _secretManager = secretManager;
    }

    public void Configure(ExternalApiOptions options)
    {
        _configuration.GetSection(ExternalApiOptions.SectionName).Bind(options);

        // Fetch secrets from secret manager
        options.ApiKey = _secretManager.GetSecret("ExternalApi:ApiKey");
    }
}

// Registration
builder.Services.AddSingleton<IConfigureOptions<ExternalApiOptions>, ExternalApiOptionsFactory>();
```

## Reloading Configuration

```csharp
// appsettings.json changes reload automatically with IOptionsSnapshot/IOptionsMonitor
builder.Configuration
    .AddJsonFile("appsettings.json", optional: false, reloadOnChange: true)
    .AddJsonFile($"appsettings.{builder.Environment.EnvironmentName}.json",
        optional: true,
        reloadOnChange: true);

// Manual reload trigger
public class ConfigurationReloadService
{
    private readonly IOptionsMonitor<AppOptions> _optionsMonitor;
    private readonly ILogger<ConfigurationReloadService> _logger;

    public ConfigurationReloadService(
        IOptionsMonitor<AppOptions> optionsMonitor,
        ILogger<ConfigurationReloadService> logger)
    {
        _optionsMonitor = optionsMonitor;
        _logger = logger;

        _optionsMonitor.OnChange(OnConfigurationChanged);
    }

    private void OnConfigurationChanged(AppOptions options, string? name)
    {
        _logger.LogInformation(
            "Configuration reloaded at {Time}. New setting: {Setting}",
            DateTime.UtcNow,
            options.SomeSetting);

        // Perform any necessary updates
    }
}
```

## Best Practices

1. **Use const SectionName**: Makes binding less error-prone
2. **Validate on Start**: Catch configuration errors early
3. **Choose Right Interface**: IOptions (static), IOptionsSnapshot (per-request), IOptionsMonitor (live updates)
4. **Secure Secrets**: Use Secret Manager or Azure Key Vault for sensitive data
5. **Environment-Specific**: Use appsettings.{Environment}.json for overrides
6. **Strong Typing**: Avoid magic strings in configuration access
7. **Default Values**: Provide sensible defaults in options classes
