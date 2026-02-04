---
name: jwt-authentication
description: JWT token-based authentication for ASP.NET Core
applies_to: dotnet
type: skill
---

# JWT Authentication

## Overview

JSON Web Tokens (JWT) provide stateless, secure authentication for APIs. This guide covers implementing JWT authentication in ASP.NET Core.

## Setup

### Installation

```bash
dotnet add package Microsoft.AspNetCore.Authentication.JwtBearer
dotnet add package System.IdentityModel.Tokens.Jwt
```

### Configuration

```csharp
// Program.cs
builder.Services.AddAuthentication(options =>
{
    options.DefaultAuthenticateScheme = JwtBearerDefaults.AuthenticationScheme;
    options.DefaultChallengeScheme = JwtBearerDefaults.AuthenticationScheme;
})
.AddJwtBearer(options =>
{
    options.TokenValidationParameters = new TokenValidationParameters
    {
        ValidateIssuer = true,
        ValidateAudience = true,
        ValidateLifetime = true,
        ValidateIssuerSigningKey = true,
        ValidIssuer = builder.Configuration["Jwt:Issuer"],
        ValidAudience = builder.Configuration["Jwt:Audience"],
        IssuerSigningKey = new SymmetricSecurityKey(
            Encoding.UTF8.GetBytes(builder.Configuration["Jwt:Secret"]!)),
        ClockSkew = TimeSpan.Zero // No tolerance for token expiration
    };

    options.Events = new JwtBearerEvents
    {
        OnAuthenticationFailed = context =>
        {
            if (context.Exception is SecurityTokenExpiredException)
            {
                context.Response.Headers.Add("Token-Expired", "true");
            }
            return Task.CompletedTask;
        },
        OnTokenValidated = context =>
        {
            // Additional validation logic
            return Task.CompletedTask;
        }
    };
});

builder.Services.AddAuthorization();

// Middleware
app.UseAuthentication();
app.UseAuthorization();
```

### App Settings

```json
{
  "Jwt": {
    "Secret": "YourSuperSecretKeyThatIsAtLeast32CharactersLong!",
    "Issuer": "MyApp",
    "Audience": "MyAppUsers",
    "ExpirationMinutes": 60,
    "RefreshExpirationDays": 7
  }
}
```

## Token Service

```csharp
// Application/Interfaces/ITokenService.cs
public interface ITokenService
{
    string GenerateAccessToken(User user);
    string GenerateRefreshToken();
    ClaimsPrincipal? ValidateToken(string token);
}

// Infrastructure/Services/TokenService.cs
public class TokenService : ITokenService
{
    private readonly JwtSettings _settings;

    public TokenService(IOptions<JwtSettings> settings)
    {
        _settings = settings.Value;
    }

    public string GenerateAccessToken(User user)
    {
        var claims = new List<Claim>
        {
            new(JwtRegisteredClaimNames.Sub, user.Id.ToString()),
            new(JwtRegisteredClaimNames.Email, user.Email),
            new(JwtRegisteredClaimNames.Jti, Guid.NewGuid().ToString()),
            new(ClaimTypes.Name, user.UserName),
            new(ClaimTypes.NameIdentifier, user.Id.ToString())
        };

        // Add role claims
        foreach (var role in user.Roles)
        {
            claims.Add(new Claim(ClaimTypes.Role, role.Name));
        }

        // Add custom claims
        claims.Add(new Claim("tenant_id", user.TenantId.ToString()));

        var key = new SymmetricSecurityKey(
            Encoding.UTF8.GetBytes(_settings.Secret));

        var credentials = new SigningCredentials(
            key,
            SecurityAlgorithms.HmacSha256);

        var token = new JwtSecurityToken(
            issuer: _settings.Issuer,
            audience: _settings.Audience,
            claims: claims,
            expires: DateTime.UtcNow.AddMinutes(_settings.ExpirationMinutes),
            signingCredentials: credentials);

        return new JwtSecurityTokenHandler().WriteToken(token);
    }

    public string GenerateRefreshToken()
    {
        var randomBytes = new byte[64];
        using var rng = RandomNumberGenerator.Create();
        rng.GetBytes(randomBytes);
        return Convert.ToBase64String(randomBytes);
    }

    public ClaimsPrincipal? ValidateToken(string token)
    {
        var tokenHandler = new JwtSecurityTokenHandler();
        var key = Encoding.UTF8.GetBytes(_settings.Secret);

        try
        {
            var principal = tokenHandler.ValidateToken(token,
                new TokenValidationParameters
                {
                    ValidateIssuerSigningKey = true,
                    IssuerSigningKey = new SymmetricSecurityKey(key),
                    ValidateIssuer = true,
                    ValidIssuer = _settings.Issuer,
                    ValidateAudience = true,
                    ValidAudience = _settings.Audience,
                    ValidateLifetime = false // Allow expired tokens for refresh
                },
                out var validatedToken);

            return principal;
        }
        catch
        {
            return null;
        }
    }
}
```

## Auth Controller

```csharp
// Controllers/AuthController.cs
[ApiController]
[Route("api/auth")]
public class AuthController : ControllerBase
{
    private readonly IAuthService _authService;
    private readonly ITokenService _tokenService;

    [HttpPost("login")]
    [AllowAnonymous]
    public async Task<ActionResult<AuthResponse>> Login(
        [FromBody] LoginRequest request,
        CancellationToken ct)
    {
        var user = await _authService.ValidateUserAsync(
            request.Email,
            request.Password,
            ct);

        if (user is null)
            return Unauthorized(new { message = "Invalid credentials" });

        var accessToken = _tokenService.GenerateAccessToken(user);
        var refreshToken = _tokenService.GenerateRefreshToken();

        // Store refresh token
        await _authService.SaveRefreshTokenAsync(
            user.Id,
            refreshToken,
            DateTime.UtcNow.AddDays(7),
            ct);

        return Ok(new AuthResponse
        {
            AccessToken = accessToken,
            RefreshToken = refreshToken,
            ExpiresAt = DateTime.UtcNow.AddMinutes(60)
        });
    }

    [HttpPost("refresh")]
    [AllowAnonymous]
    public async Task<ActionResult<AuthResponse>> Refresh(
        [FromBody] RefreshTokenRequest request,
        CancellationToken ct)
    {
        var principal = _tokenService.ValidateToken(request.AccessToken);
        if (principal is null)
            return Unauthorized();

        var userId = principal.FindFirst(ClaimTypes.NameIdentifier)?.Value;
        if (userId is null)
            return Unauthorized();

        var storedToken = await _authService.GetRefreshTokenAsync(
            Guid.Parse(userId),
            request.RefreshToken,
            ct);

        if (storedToken is null || storedToken.ExpiresAt < DateTime.UtcNow)
            return Unauthorized(new { message = "Invalid refresh token" });

        // Revoke old token
        await _authService.RevokeRefreshTokenAsync(storedToken.Id, ct);

        // Get user and generate new tokens
        var user = await _authService.GetUserByIdAsync(Guid.Parse(userId), ct);
        var newAccessToken = _tokenService.GenerateAccessToken(user!);
        var newRefreshToken = _tokenService.GenerateRefreshToken();

        await _authService.SaveRefreshTokenAsync(
            user!.Id,
            newRefreshToken,
            DateTime.UtcNow.AddDays(7),
            ct);

        return Ok(new AuthResponse
        {
            AccessToken = newAccessToken,
            RefreshToken = newRefreshToken,
            ExpiresAt = DateTime.UtcNow.AddMinutes(60)
        });
    }

    [HttpPost("logout")]
    [Authorize]
    public async Task<IActionResult> Logout(CancellationToken ct)
    {
        var userId = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
        if (userId is not null)
        {
            await _authService.RevokeAllRefreshTokensAsync(
                Guid.Parse(userId),
                ct);
        }

        return NoContent();
    }
}
```

## Accessing Claims

```csharp
// Current user service
public interface ICurrentUserService
{
    Guid? UserId { get; }
    string? Email { get; }
    IEnumerable<string> Roles { get; }
    bool IsAuthenticated { get; }
}

public class CurrentUserService : ICurrentUserService
{
    private readonly IHttpContextAccessor _httpContextAccessor;

    public CurrentUserService(IHttpContextAccessor httpContextAccessor)
    {
        _httpContextAccessor = httpContextAccessor;
    }

    private ClaimsPrincipal? User =>
        _httpContextAccessor.HttpContext?.User;

    public Guid? UserId
    {
        get
        {
            var id = User?.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            return id is not null ? Guid.Parse(id) : null;
        }
    }

    public string? Email =>
        User?.FindFirst(JwtRegisteredClaimNames.Email)?.Value ??
        User?.FindFirst(ClaimTypes.Email)?.Value;

    public IEnumerable<string> Roles =>
        User?.FindAll(ClaimTypes.Role).Select(c => c.Value) ??
        Enumerable.Empty<string>();

    public bool IsAuthenticated =>
        User?.Identity?.IsAuthenticated ?? false;
}

// Registration
builder.Services.AddHttpContextAccessor();
builder.Services.AddScoped<ICurrentUserService, CurrentUserService>();
```

## Secure Endpoints

```csharp
// Require authentication
[Authorize]
public class ProductsController : ControllerBase { }

// Require specific role
[Authorize(Roles = "Admin")]
public class AdminController : ControllerBase { }

// Require any of multiple roles
[Authorize(Roles = "Admin,Manager")]
public IActionResult ManageProducts() { }

// Policy-based
[Authorize(Policy = "CanEditProducts")]
public IActionResult EditProduct() { }
```

## Security Best Practices

| Practice | Implementation |
|----------|----------------|
| Secret length | Minimum 256 bits (32 chars) |
| Algorithm | HS256 or RS256 |
| Token expiry | Short-lived (15-60 mins) |
| Refresh tokens | Rotate on use |
| HTTPS only | Always use TLS |
| Claim minimization | Only essential claims |

## Related Skills

- `skills/security/authorization-policies.md`
- `skills/security/identity-setup.md`
