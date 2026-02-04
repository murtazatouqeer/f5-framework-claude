---
name: identity-setup
description: ASP.NET Core Identity configuration for user management
applies_to: dotnet
type: skill
---

# ASP.NET Core Identity Setup

## Overview

ASP.NET Core Identity provides a complete user management system including authentication, authorization, password management, and role-based access control.

## Installation

```bash
dotnet add package Microsoft.AspNetCore.Identity.EntityFrameworkCore
dotnet add package Microsoft.EntityFrameworkCore.SqlServer
```

## Custom User and Role

```csharp
// Domain/Entities/ApplicationUser.cs
public class ApplicationUser : IdentityUser<Guid>
{
    public string FirstName { get; set; } = string.Empty;
    public string LastName { get; set; } = string.Empty;
    public string? ProfilePictureUrl { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime? LastLoginAt { get; set; }
    public bool IsActive { get; set; } = true;

    // Navigation properties
    public virtual ICollection<ApplicationUserRole> UserRoles { get; set; } =
        new List<ApplicationUserRole>();
    public virtual ICollection<RefreshToken> RefreshTokens { get; set; } =
        new List<RefreshToken>();
}

// Domain/Entities/ApplicationRole.cs
public class ApplicationRole : IdentityRole<Guid>
{
    public string? Description { get; set; }
    public DateTime CreatedAt { get; set; }

    public virtual ICollection<ApplicationUserRole> UserRoles { get; set; } =
        new List<ApplicationUserRole>();
    public virtual ICollection<RolePermission> Permissions { get; set; } =
        new List<RolePermission>();
}

// Join table for additional properties
public class ApplicationUserRole : IdentityUserRole<Guid>
{
    public virtual ApplicationUser User { get; set; } = null!;
    public virtual ApplicationRole Role { get; set; } = null!;
    public DateTime AssignedAt { get; set; }
    public Guid? AssignedBy { get; set; }
}
```

## DbContext Configuration

```csharp
// Infrastructure/Persistence/AppDbContext.cs
public class AppDbContext : IdentityDbContext<
    ApplicationUser,
    ApplicationRole,
    Guid,
    IdentityUserClaim<Guid>,
    ApplicationUserRole,
    IdentityUserLogin<Guid>,
    IdentityRoleClaim<Guid>,
    IdentityUserToken<Guid>>
{
    public AppDbContext(DbContextOptions<AppDbContext> options)
        : base(options) { }

    public DbSet<RefreshToken> RefreshTokens => Set<RefreshToken>();
    public DbSet<RolePermission> RolePermissions => Set<RolePermission>();

    protected override void OnModelCreating(ModelBuilder builder)
    {
        base.OnModelCreating(builder);

        // Rename Identity tables
        builder.Entity<ApplicationUser>().ToTable("Users");
        builder.Entity<ApplicationRole>().ToTable("Roles");
        builder.Entity<ApplicationUserRole>().ToTable("UserRoles");
        builder.Entity<IdentityUserClaim<Guid>>().ToTable("UserClaims");
        builder.Entity<IdentityUserLogin<Guid>>().ToTable("UserLogins");
        builder.Entity<IdentityUserToken<Guid>>().ToTable("UserTokens");
        builder.Entity<IdentityRoleClaim<Guid>>().ToTable("RoleClaims");

        // Configure ApplicationUser
        builder.Entity<ApplicationUser>(entity =>
        {
            entity.Property(u => u.FirstName).HasMaxLength(100);
            entity.Property(u => u.LastName).HasMaxLength(100);

            entity.HasMany(u => u.UserRoles)
                .WithOne(ur => ur.User)
                .HasForeignKey(ur => ur.UserId)
                .IsRequired();
        });

        // Configure ApplicationRole
        builder.Entity<ApplicationRole>(entity =>
        {
            entity.Property(r => r.Description).HasMaxLength(500);

            entity.HasMany(r => r.UserRoles)
                .WithOne(ur => ur.Role)
                .HasForeignKey(ur => ur.RoleId)
                .IsRequired();
        });

        // Configure join table
        builder.Entity<ApplicationUserRole>(entity =>
        {
            entity.HasKey(ur => new { ur.UserId, ur.RoleId });
        });
    }
}
```

## Identity Configuration

```csharp
// Program.cs
builder.Services.AddIdentity<ApplicationUser, ApplicationRole>(options =>
{
    // Password settings
    options.Password.RequiredLength = 8;
    options.Password.RequireDigit = true;
    options.Password.RequireLowercase = true;
    options.Password.RequireUppercase = true;
    options.Password.RequireNonAlphanumeric = true;
    options.Password.RequiredUniqueChars = 3;

    // Lockout settings
    options.Lockout.DefaultLockoutTimeSpan = TimeSpan.FromMinutes(15);
    options.Lockout.MaxFailedAccessAttempts = 5;
    options.Lockout.AllowedForNewUsers = true;

    // User settings
    options.User.RequireUniqueEmail = true;
    options.User.AllowedUserNameCharacters =
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._@+";

    // Sign-in settings
    options.SignIn.RequireConfirmedEmail = true;
    options.SignIn.RequireConfirmedAccount = true;
})
.AddEntityFrameworkStores<AppDbContext>()
.AddDefaultTokenProviders()
.AddTokenProvider<DataProtectorTokenProvider<ApplicationUser>>("Email");

// Configure token lifespan
builder.Services.Configure<DataProtectionTokenProviderOptions>(options =>
{
    options.TokenLifespan = TimeSpan.FromHours(2);
});
```

## Identity Service

```csharp
// Application/Interfaces/IIdentityService.cs
public interface IIdentityService
{
    Task<(bool Success, string[] Errors)> CreateUserAsync(
        CreateUserDto dto,
        CancellationToken ct = default);
    Task<ApplicationUser?> GetUserByEmailAsync(string email);
    Task<bool> ValidateCredentialsAsync(string email, string password);
    Task<IEnumerable<string>> GetUserRolesAsync(Guid userId);
    Task<bool> AddToRoleAsync(Guid userId, string role);
    Task<bool> RemoveFromRoleAsync(Guid userId, string role);
    Task<string> GenerateEmailConfirmationTokenAsync(ApplicationUser user);
    Task<bool> ConfirmEmailAsync(Guid userId, string token);
    Task<string> GeneratePasswordResetTokenAsync(ApplicationUser user);
    Task<(bool Success, string[] Errors)> ResetPasswordAsync(
        Guid userId, string token, string newPassword);
}

// Infrastructure/Identity/IdentityService.cs
public class IdentityService : IIdentityService
{
    private readonly UserManager<ApplicationUser> _userManager;
    private readonly RoleManager<ApplicationRole> _roleManager;
    private readonly ILogger<IdentityService> _logger;

    public IdentityService(
        UserManager<ApplicationUser> userManager,
        RoleManager<ApplicationRole> roleManager,
        ILogger<IdentityService> logger)
    {
        _userManager = userManager;
        _roleManager = roleManager;
        _logger = logger;
    }

    public async Task<(bool Success, string[] Errors)> CreateUserAsync(
        CreateUserDto dto,
        CancellationToken ct = default)
    {
        var user = new ApplicationUser
        {
            UserName = dto.Email,
            Email = dto.Email,
            FirstName = dto.FirstName,
            LastName = dto.LastName,
            CreatedAt = DateTime.UtcNow
        };

        var result = await _userManager.CreateAsync(user, dto.Password);

        if (result.Succeeded)
        {
            _logger.LogInformation("User {Email} created successfully", dto.Email);

            // Add default role
            await _userManager.AddToRoleAsync(user, "User");

            return (true, Array.Empty<string>());
        }

        return (false, result.Errors.Select(e => e.Description).ToArray());
    }

    public async Task<ApplicationUser?> GetUserByEmailAsync(string email)
    {
        return await _userManager.FindByEmailAsync(email);
    }

    public async Task<bool> ValidateCredentialsAsync(string email, string password)
    {
        var user = await _userManager.FindByEmailAsync(email);

        if (user is null || !user.IsActive)
            return false;

        if (await _userManager.IsLockedOutAsync(user))
            return false;

        var result = await _userManager.CheckPasswordAsync(user, password);

        if (!result)
        {
            await _userManager.AccessFailedAsync(user);
            return false;
        }

        await _userManager.ResetAccessFailedCountAsync(user);
        user.LastLoginAt = DateTime.UtcNow;
        await _userManager.UpdateAsync(user);

        return true;
    }

    public async Task<IEnumerable<string>> GetUserRolesAsync(Guid userId)
    {
        var user = await _userManager.FindByIdAsync(userId.ToString());
        if (user is null)
            return Enumerable.Empty<string>();

        return await _userManager.GetRolesAsync(user);
    }

    public async Task<bool> AddToRoleAsync(Guid userId, string role)
    {
        var user = await _userManager.FindByIdAsync(userId.ToString());
        if (user is null)
            return false;

        if (!await _roleManager.RoleExistsAsync(role))
            return false;

        var result = await _userManager.AddToRoleAsync(user, role);
        return result.Succeeded;
    }

    // ... other implementations
}
```

## Role Seeding

```csharp
// Infrastructure/Identity/IdentitySeed.cs
public static class IdentitySeed
{
    public static async Task SeedRolesAsync(RoleManager<ApplicationRole> roleManager)
    {
        var roles = new[]
        {
            new ApplicationRole
            {
                Name = "Admin",
                Description = "Full system access"
            },
            new ApplicationRole
            {
                Name = "Manager",
                Description = "Department management access"
            },
            new ApplicationRole
            {
                Name = "User",
                Description = "Standard user access"
            }
        };

        foreach (var role in roles)
        {
            if (!await roleManager.RoleExistsAsync(role.Name!))
            {
                role.CreatedAt = DateTime.UtcNow;
                await roleManager.CreateAsync(role);
            }
        }
    }

    public static async Task SeedAdminAsync(
        UserManager<ApplicationUser> userManager,
        IConfiguration configuration)
    {
        var adminEmail = configuration["Admin:Email"] ?? "admin@example.com";
        var adminPassword = configuration["Admin:Password"] ?? "Admin@123";

        if (await userManager.FindByEmailAsync(adminEmail) is null)
        {
            var admin = new ApplicationUser
            {
                UserName = adminEmail,
                Email = adminEmail,
                FirstName = "System",
                LastName = "Administrator",
                EmailConfirmed = true,
                CreatedAt = DateTime.UtcNow
            };

            await userManager.CreateAsync(admin, adminPassword);
            await userManager.AddToRoleAsync(admin, "Admin");
        }
    }
}

// Program.cs
using (var scope = app.Services.CreateScope())
{
    var roleManager = scope.ServiceProvider
        .GetRequiredService<RoleManager<ApplicationRole>>();
    var userManager = scope.ServiceProvider
        .GetRequiredService<UserManager<ApplicationUser>>();
    var config = scope.ServiceProvider.GetRequiredService<IConfiguration>();

    await IdentitySeed.SeedRolesAsync(roleManager);
    await IdentitySeed.SeedAdminAsync(userManager, config);
}
```

## Best Practices

| Practice | Recommendation |
|----------|----------------|
| Password rules | Enforce strong passwords |
| Lockout | Enable after failed attempts |
| Email confirmation | Require for production |
| Two-factor auth | Implement for sensitive apps |
| Role hierarchy | Use permissions for granular control |

## Related Skills

- `skills/security/jwt-authentication.md`
- `skills/security/authorization-policies.md`
