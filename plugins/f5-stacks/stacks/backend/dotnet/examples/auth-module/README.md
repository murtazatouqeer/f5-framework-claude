# Authentication Module Example

Complete JWT Authentication implementation with ASP.NET Core Identity.

## Project Structure

```
AuthModule/
├── src/
│   ├── AuthModule.Domain/
│   │   ├── Entities/
│   │   │   └── ApplicationUser.cs
│   │   └── Interfaces/
│   │       └── ITokenService.cs
│   │
│   ├── AuthModule.Application/
│   │   ├── DTOs/
│   │   │   ├── AuthResponseDto.cs
│   │   │   ├── LoginDto.cs
│   │   │   ├── RegisterDto.cs
│   │   │   └── RefreshTokenDto.cs
│   │   ├── Auth/
│   │   │   ├── Commands/
│   │   │   │   ├── Login/
│   │   │   │   ├── Register/
│   │   │   │   └── RefreshToken/
│   │   │   └── Queries/
│   │   │       └── GetCurrentUser/
│   │   └── Services/
│   │       └── ICurrentUserService.cs
│   │
│   ├── AuthModule.Infrastructure/
│   │   ├── Identity/
│   │   │   ├── IdentityDbContext.cs
│   │   │   └── TokenService.cs
│   │   └── Services/
│   │       └── CurrentUserService.cs
│   │
│   └── AuthModule.API/
│       ├── Controllers/
│       │   └── AuthController.cs
│       └── Program.cs
│
└── tests/
    └── AuthModule.Tests.Unit/
        └── TokenServiceTests.cs
```

## Implementation

### 1. Domain Layer

```csharp
// Domain/Entities/ApplicationUser.cs
using Microsoft.AspNetCore.Identity;

namespace AuthModule.Domain.Entities;

public class ApplicationUser : IdentityUser<Guid>
{
    public string FirstName { get; set; } = string.Empty;
    public string LastName { get; set; } = string.Empty;
    public string? RefreshToken { get; set; }
    public DateTime? RefreshTokenExpiryTime { get; set; }
    public bool IsActive { get; set; } = true;
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime? LastLoginAt { get; set; }

    public string FullName => $"{FirstName} {LastName}";
}

// Domain/Interfaces/ITokenService.cs
namespace AuthModule.Domain.Interfaces;

public interface ITokenService
{
    Task<(string AccessToken, string RefreshToken)> GenerateTokensAsync(
        ApplicationUser user);

    Task<ClaimsPrincipal?> ValidateAccessTokenAsync(string token);

    string GenerateRefreshToken();
}
```

### 2. Application Layer

```csharp
// Application/DTOs/AuthResponseDto.cs
namespace AuthModule.Application.DTOs;

public record AuthResponseDto
{
    public Guid UserId { get; init; }
    public string Email { get; init; } = string.Empty;
    public string FullName { get; init; } = string.Empty;
    public string AccessToken { get; init; } = string.Empty;
    public string RefreshToken { get; init; } = string.Empty;
    public DateTime ExpiresAt { get; init; }
    public IEnumerable<string> Roles { get; init; } = Enumerable.Empty<string>();
}

public record LoginDto
{
    public string Email { get; init; } = string.Empty;
    public string Password { get; init; } = string.Empty;
    public bool RememberMe { get; init; }
}

public record RegisterDto
{
    public string Email { get; init; } = string.Empty;
    public string Password { get; init; } = string.Empty;
    public string ConfirmPassword { get; init; } = string.Empty;
    public string FirstName { get; init; } = string.Empty;
    public string LastName { get; init; } = string.Empty;
}

// Application/Auth/Commands/Login/LoginCommand.cs
using MediatR;

namespace AuthModule.Application.Auth.Commands.Login;

public record LoginCommand(
    string Email,
    string Password,
    bool RememberMe = false
) : IRequest<Result<AuthResponseDto>>;

// LoginCommandHandler.cs
public class LoginCommandHandler
    : IRequestHandler<LoginCommand, Result<AuthResponseDto>>
{
    private readonly UserManager<ApplicationUser> _userManager;
    private readonly ITokenService _tokenService;
    private readonly ILogger<LoginCommandHandler> _logger;

    public LoginCommandHandler(
        UserManager<ApplicationUser> userManager,
        ITokenService tokenService,
        ILogger<LoginCommandHandler> logger)
    {
        _userManager = userManager;
        _tokenService = tokenService;
        _logger = logger;
    }

    public async Task<Result<AuthResponseDto>> Handle(
        LoginCommand request,
        CancellationToken cancellationToken)
    {
        var user = await _userManager.FindByEmailAsync(request.Email);

        if (user is null || !user.IsActive)
        {
            _logger.LogWarning("Login failed for {Email}", request.Email);
            return Result<AuthResponseDto>.Failure("Invalid credentials");
        }

        var passwordValid = await _userManager.CheckPasswordAsync(
            user,
            request.Password);

        if (!passwordValid)
        {
            await _userManager.AccessFailedAsync(user);
            return Result<AuthResponseDto>.Failure("Invalid credentials");
        }

        // Reset access failed count on successful login
        await _userManager.ResetAccessFailedCountAsync(user);

        // Generate tokens
        var (accessToken, refreshToken) = await _tokenService.GenerateTokensAsync(user);

        // Store refresh token
        user.RefreshToken = refreshToken;
        user.RefreshTokenExpiryTime = DateTime.UtcNow.AddDays(
            request.RememberMe ? 30 : 7);
        user.LastLoginAt = DateTime.UtcNow;

        await _userManager.UpdateAsync(user);

        var roles = await _userManager.GetRolesAsync(user);

        _logger.LogInformation("User {Email} logged in successfully", request.Email);

        return Result<AuthResponseDto>.Success(new AuthResponseDto
        {
            UserId = user.Id,
            Email = user.Email!,
            FullName = user.FullName,
            AccessToken = accessToken,
            RefreshToken = refreshToken,
            ExpiresAt = DateTime.UtcNow.AddHours(1),
            Roles = roles
        });
    }
}

// LoginCommandValidator.cs
using FluentValidation;

public class LoginCommandValidator : AbstractValidator<LoginCommand>
{
    public LoginCommandValidator()
    {
        RuleFor(x => x.Email)
            .NotEmpty()
            .EmailAddress();

        RuleFor(x => x.Password)
            .NotEmpty()
            .MinimumLength(6);
    }
}

// Application/Auth/Commands/Register/RegisterCommand.cs
public record RegisterCommand(
    string Email,
    string Password,
    string ConfirmPassword,
    string FirstName,
    string LastName
) : IRequest<Result<AuthResponseDto>>;

// RegisterCommandHandler.cs
public class RegisterCommandHandler
    : IRequestHandler<RegisterCommand, Result<AuthResponseDto>>
{
    private readonly UserManager<ApplicationUser> _userManager;
    private readonly ITokenService _tokenService;

    public async Task<Result<AuthResponseDto>> Handle(
        RegisterCommand request,
        CancellationToken cancellationToken)
    {
        var existingUser = await _userManager.FindByEmailAsync(request.Email);
        if (existingUser is not null)
        {
            return Result<AuthResponseDto>.Failure("Email already registered");
        }

        var user = new ApplicationUser
        {
            Email = request.Email,
            UserName = request.Email,
            FirstName = request.FirstName,
            LastName = request.LastName,
            EmailConfirmed = true // Set to false for email verification
        };

        var result = await _userManager.CreateAsync(user, request.Password);

        if (!result.Succeeded)
        {
            var errors = string.Join(", ", result.Errors.Select(e => e.Description));
            return Result<AuthResponseDto>.Failure(errors);
        }

        // Assign default role
        await _userManager.AddToRoleAsync(user, "User");

        // Generate tokens
        var (accessToken, refreshToken) = await _tokenService.GenerateTokensAsync(user);

        user.RefreshToken = refreshToken;
        user.RefreshTokenExpiryTime = DateTime.UtcNow.AddDays(7);
        await _userManager.UpdateAsync(user);

        return Result<AuthResponseDto>.Success(new AuthResponseDto
        {
            UserId = user.Id,
            Email = user.Email,
            FullName = user.FullName,
            AccessToken = accessToken,
            RefreshToken = refreshToken,
            ExpiresAt = DateTime.UtcNow.AddHours(1),
            Roles = new[] { "User" }
        });
    }
}

// Application/Auth/Commands/RefreshToken/RefreshTokenCommand.cs
public record RefreshTokenCommand(
    string AccessToken,
    string RefreshToken
) : IRequest<Result<AuthResponseDto>>;

// RefreshTokenCommandHandler.cs
public class RefreshTokenCommandHandler
    : IRequestHandler<RefreshTokenCommand, Result<AuthResponseDto>>
{
    private readonly UserManager<ApplicationUser> _userManager;
    private readonly ITokenService _tokenService;

    public async Task<Result<AuthResponseDto>> Handle(
        RefreshTokenCommand request,
        CancellationToken cancellationToken)
    {
        var principal = await _tokenService.ValidateAccessTokenAsync(
            request.AccessToken);

        if (principal is null)
        {
            return Result<AuthResponseDto>.Failure("Invalid access token");
        }

        var userId = principal.FindFirst(ClaimTypes.NameIdentifier)?.Value;
        if (userId is null)
        {
            return Result<AuthResponseDto>.Failure("Invalid token claims");
        }

        var user = await _userManager.FindByIdAsync(userId);

        if (user is null ||
            user.RefreshToken != request.RefreshToken ||
            user.RefreshTokenExpiryTime <= DateTime.UtcNow)
        {
            return Result<AuthResponseDto>.Failure("Invalid refresh token");
        }

        // Generate new tokens
        var (accessToken, refreshToken) = await _tokenService.GenerateTokensAsync(user);

        user.RefreshToken = refreshToken;
        user.RefreshTokenExpiryTime = DateTime.UtcNow.AddDays(7);
        await _userManager.UpdateAsync(user);

        var roles = await _userManager.GetRolesAsync(user);

        return Result<AuthResponseDto>.Success(new AuthResponseDto
        {
            UserId = user.Id,
            Email = user.Email!,
            FullName = user.FullName,
            AccessToken = accessToken,
            RefreshToken = refreshToken,
            ExpiresAt = DateTime.UtcNow.AddHours(1),
            Roles = roles
        });
    }
}
```

### 3. Infrastructure Layer

```csharp
// Infrastructure/Identity/TokenService.cs
using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Security.Cryptography;
using System.Text;
using Microsoft.Extensions.Options;
using Microsoft.IdentityModel.Tokens;

namespace AuthModule.Infrastructure.Identity;

public class JwtSettings
{
    public string Secret { get; set; } = string.Empty;
    public string Issuer { get; set; } = string.Empty;
    public string Audience { get; set; } = string.Empty;
    public int ExpiryMinutes { get; set; } = 60;
}

public class TokenService : ITokenService
{
    private readonly UserManager<ApplicationUser> _userManager;
    private readonly JwtSettings _jwtSettings;

    public TokenService(
        UserManager<ApplicationUser> userManager,
        IOptions<JwtSettings> jwtSettings)
    {
        _userManager = userManager;
        _jwtSettings = jwtSettings.Value;
    }

    public async Task<(string AccessToken, string RefreshToken)> GenerateTokensAsync(
        ApplicationUser user)
    {
        var accessToken = await GenerateAccessTokenAsync(user);
        var refreshToken = GenerateRefreshToken();

        return (accessToken, refreshToken);
    }

    private async Task<string> GenerateAccessTokenAsync(ApplicationUser user)
    {
        var roles = await _userManager.GetRolesAsync(user);
        var claims = await _userManager.GetClaimsAsync(user);

        var tokenClaims = new List<Claim>
        {
            new(JwtRegisteredClaimNames.Sub, user.Id.ToString()),
            new(JwtRegisteredClaimNames.Email, user.Email!),
            new(JwtRegisteredClaimNames.Jti, Guid.NewGuid().ToString()),
            new(ClaimTypes.Name, user.FullName),
        };

        // Add roles as claims
        tokenClaims.AddRange(roles.Select(role =>
            new Claim(ClaimTypes.Role, role)));

        // Add user claims
        tokenClaims.AddRange(claims);

        var key = new SymmetricSecurityKey(
            Encoding.UTF8.GetBytes(_jwtSettings.Secret));
        var credentials = new SigningCredentials(
            key,
            SecurityAlgorithms.HmacSha256);

        var token = new JwtSecurityToken(
            issuer: _jwtSettings.Issuer,
            audience: _jwtSettings.Audience,
            claims: tokenClaims,
            expires: DateTime.UtcNow.AddMinutes(_jwtSettings.ExpiryMinutes),
            signingCredentials: credentials);

        return new JwtSecurityTokenHandler().WriteToken(token);
    }

    public string GenerateRefreshToken()
    {
        var randomNumber = new byte[64];
        using var rng = RandomNumberGenerator.Create();
        rng.GetBytes(randomNumber);
        return Convert.ToBase64String(randomNumber);
    }

    public Task<ClaimsPrincipal?> ValidateAccessTokenAsync(string token)
    {
        var tokenHandler = new JwtSecurityTokenHandler();
        var key = Encoding.UTF8.GetBytes(_jwtSettings.Secret);

        try
        {
            var principal = tokenHandler.ValidateToken(token, new TokenValidationParameters
            {
                ValidateIssuerSigningKey = true,
                IssuerSigningKey = new SymmetricSecurityKey(key),
                ValidateIssuer = true,
                ValidIssuer = _jwtSettings.Issuer,
                ValidateAudience = true,
                ValidAudience = _jwtSettings.Audience,
                ValidateLifetime = false, // Allow expired tokens for refresh
                ClockSkew = TimeSpan.Zero
            }, out _);

            return Task.FromResult<ClaimsPrincipal?>(principal);
        }
        catch
        {
            return Task.FromResult<ClaimsPrincipal?>(null);
        }
    }
}

// Infrastructure/Identity/IdentityDbContext.cs
using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.Identity.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore;

namespace AuthModule.Infrastructure.Identity;

public class IdentityDbContext
    : IdentityDbContext<ApplicationUser, IdentityRole<Guid>, Guid>
{
    public IdentityDbContext(DbContextOptions<IdentityDbContext> options)
        : base(options) { }

    protected override void OnModelCreating(ModelBuilder builder)
    {
        base.OnModelCreating(builder);

        // Customize Identity table names
        builder.Entity<ApplicationUser>().ToTable("Users");
        builder.Entity<IdentityRole<Guid>>().ToTable("Roles");
        builder.Entity<IdentityUserRole<Guid>>().ToTable("UserRoles");
        builder.Entity<IdentityUserClaim<Guid>>().ToTable("UserClaims");
        builder.Entity<IdentityUserLogin<Guid>>().ToTable("UserLogins");
        builder.Entity<IdentityRoleClaim<Guid>>().ToTable("RoleClaims");
        builder.Entity<IdentityUserToken<Guid>>().ToTable("UserTokens");

        // Configure ApplicationUser
        builder.Entity<ApplicationUser>(entity =>
        {
            entity.Property(e => e.FirstName).HasMaxLength(100).IsRequired();
            entity.Property(e => e.LastName).HasMaxLength(100).IsRequired();
            entity.Property(e => e.RefreshToken).HasMaxLength(256);
        });

        // Seed default roles
        builder.Entity<IdentityRole<Guid>>().HasData(
            new IdentityRole<Guid>
            {
                Id = Guid.Parse("8D04DCE2-969A-435D-BBA4-DF3F325983DC"),
                Name = "Admin",
                NormalizedName = "ADMIN"
            },
            new IdentityRole<Guid>
            {
                Id = Guid.Parse("7D04DCE2-969A-435D-BBA4-DF3F325983DC"),
                Name = "User",
                NormalizedName = "USER"
            }
        );
    }
}

// Infrastructure/DependencyInjection.cs
namespace AuthModule.Infrastructure;

public static class DependencyInjection
{
    public static IServiceCollection AddInfrastructure(
        this IServiceCollection services,
        IConfiguration configuration)
    {
        // Configure JWT settings
        services.Configure<JwtSettings>(
            configuration.GetSection("JwtSettings"));

        // Add DbContext
        services.AddDbContext<IdentityDbContext>(options =>
            options.UseSqlServer(
                configuration.GetConnectionString("DefaultConnection")));

        // Add Identity
        services.AddIdentity<ApplicationUser, IdentityRole<Guid>>(options =>
        {
            options.Password.RequireDigit = true;
            options.Password.RequireLowercase = true;
            options.Password.RequireUppercase = true;
            options.Password.RequireNonAlphanumeric = true;
            options.Password.RequiredLength = 8;

            options.Lockout.DefaultLockoutTimeSpan = TimeSpan.FromMinutes(5);
            options.Lockout.MaxFailedAccessAttempts = 5;

            options.User.RequireUniqueEmail = true;
        })
        .AddEntityFrameworkStores<IdentityDbContext>()
        .AddDefaultTokenProviders();

        // Add JWT Authentication
        var jwtSettings = configuration.GetSection("JwtSettings").Get<JwtSettings>()!;

        services.AddAuthentication(options =>
        {
            options.DefaultAuthenticateScheme = JwtBearerDefaults.AuthenticationScheme;
            options.DefaultChallengeScheme = JwtBearerDefaults.AuthenticationScheme;
        })
        .AddJwtBearer(options =>
        {
            options.TokenValidationParameters = new TokenValidationParameters
            {
                ValidateIssuer = true,
                ValidIssuer = jwtSettings.Issuer,
                ValidateAudience = true,
                ValidAudience = jwtSettings.Audience,
                ValidateIssuerSigningKey = true,
                IssuerSigningKey = new SymmetricSecurityKey(
                    Encoding.UTF8.GetBytes(jwtSettings.Secret)),
                ValidateLifetime = true,
                ClockSkew = TimeSpan.Zero
            };
        });

        // Register services
        services.AddScoped<ITokenService, TokenService>();

        return services;
    }
}
```

### 4. API Layer

```csharp
// API/Controllers/AuthController.cs
using MediatR;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace AuthModule.API.Controllers;

[ApiController]
[Route("api/[controller]")]
[Produces("application/json")]
public class AuthController : ControllerBase
{
    private readonly IMediator _mediator;

    public AuthController(IMediator mediator)
    {
        _mediator = mediator;
    }

    /// <summary>
    /// Register a new user
    /// </summary>
    [HttpPost("register")]
    [ProducesResponseType(typeof(AuthResponseDto), 200)]
    [ProducesResponseType(typeof(ProblemDetails), 400)]
    public async Task<ActionResult<AuthResponseDto>> Register(
        RegisterDto dto,
        CancellationToken cancellationToken)
    {
        var command = new RegisterCommand(
            dto.Email,
            dto.Password,
            dto.ConfirmPassword,
            dto.FirstName,
            dto.LastName);

        var result = await _mediator.Send(command, cancellationToken);

        return result.IsSuccess
            ? Ok(result.Value)
            : BadRequest(new ProblemDetails
            {
                Title = "Registration failed",
                Detail = result.Error
            });
    }

    /// <summary>
    /// Login with email and password
    /// </summary>
    [HttpPost("login")]
    [ProducesResponseType(typeof(AuthResponseDto), 200)]
    [ProducesResponseType(typeof(ProblemDetails), 401)]
    public async Task<ActionResult<AuthResponseDto>> Login(
        LoginDto dto,
        CancellationToken cancellationToken)
    {
        var command = new LoginCommand(
            dto.Email,
            dto.Password,
            dto.RememberMe);

        var result = await _mediator.Send(command, cancellationToken);

        return result.IsSuccess
            ? Ok(result.Value)
            : Unauthorized(new ProblemDetails
            {
                Title = "Authentication failed",
                Detail = result.Error
            });
    }

    /// <summary>
    /// Refresh access token
    /// </summary>
    [HttpPost("refresh")]
    [ProducesResponseType(typeof(AuthResponseDto), 200)]
    [ProducesResponseType(typeof(ProblemDetails), 401)]
    public async Task<ActionResult<AuthResponseDto>> Refresh(
        RefreshTokenDto dto,
        CancellationToken cancellationToken)
    {
        var command = new RefreshTokenCommand(
            dto.AccessToken,
            dto.RefreshToken);

        var result = await _mediator.Send(command, cancellationToken);

        return result.IsSuccess
            ? Ok(result.Value)
            : Unauthorized(new ProblemDetails
            {
                Title = "Token refresh failed",
                Detail = result.Error
            });
    }

    /// <summary>
    /// Get current user info
    /// </summary>
    [HttpGet("me")]
    [Authorize]
    [ProducesResponseType(typeof(UserDto), 200)]
    [ProducesResponseType(401)]
    public async Task<ActionResult<UserDto>> GetCurrentUser(
        CancellationToken cancellationToken)
    {
        var result = await _mediator.Send(
            new GetCurrentUserQuery(),
            cancellationToken);

        return result is null ? NotFound() : Ok(result);
    }

    /// <summary>
    /// Logout (revoke refresh token)
    /// </summary>
    [HttpPost("logout")]
    [Authorize]
    [ProducesResponseType(204)]
    public async Task<IActionResult> Logout(CancellationToken cancellationToken)
    {
        await _mediator.Send(new LogoutCommand(), cancellationToken);
        return NoContent();
    }
}
```

### 5. appsettings.json

```json
{
  "ConnectionStrings": {
    "DefaultConnection": "Server=localhost;Database=AuthModuleDb;Trusted_Connection=True;TrustServerCertificate=True"
  },
  "JwtSettings": {
    "Secret": "YourSuperSecretKeyThatIsAtLeast32CharactersLong!",
    "Issuer": "AuthModule",
    "Audience": "AuthModuleClient",
    "ExpiryMinutes": 60
  },
  "Logging": {
    "LogLevel": {
      "Default": "Information"
    }
  }
}
```

## Running the Example

```bash
# Create solution
dotnet new sln -n AuthModule

# Create projects
dotnet new classlib -n AuthModule.Domain -o src/AuthModule.Domain
dotnet new classlib -n AuthModule.Application -o src/AuthModule.Application
dotnet new classlib -n AuthModule.Infrastructure -o src/AuthModule.Infrastructure
dotnet new webapi -n AuthModule.API -o src/AuthModule.API

# Add packages
dotnet add src/AuthModule.Infrastructure package Microsoft.AspNetCore.Identity.EntityFrameworkCore
dotnet add src/AuthModule.Infrastructure package Microsoft.AspNetCore.Authentication.JwtBearer
dotnet add src/AuthModule.API package Swashbuckle.AspNetCore

# Run migrations
cd src/AuthModule.API
dotnet ef migrations add InitialCreate -o ../AuthModule.Infrastructure/Migrations
dotnet ef database update

# Run the API
dotnet run
```

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/register` | No | Register new user |
| POST | `/api/auth/login` | No | Login |
| POST | `/api/auth/refresh` | No | Refresh token |
| GET | `/api/auth/me` | Yes | Get current user |
| POST | `/api/auth/logout` | Yes | Logout |

## Security Considerations

1. **Secret Management**: Store JWT secret in environment variables or Azure Key Vault
2. **HTTPS Only**: Always use HTTPS in production
3. **Token Expiry**: Short-lived access tokens (1 hour), longer refresh tokens (7-30 days)
4. **Password Policy**: Enforce strong passwords
5. **Rate Limiting**: Implement rate limiting on auth endpoints
6. **Account Lockout**: Lock account after failed attempts

## Related Skills

- `jwt-authentication` - JWT token patterns
- `identity-setup` - ASP.NET Core Identity setup
- `authorization-policies` - Role and policy-based authorization
- `fluent-validation` - Input validation
