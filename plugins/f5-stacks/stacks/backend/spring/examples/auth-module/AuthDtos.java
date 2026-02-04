package com.example.app.web.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.*;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

// ==================== Request DTOs ====================

@Schema(description = "User registration request")
public record RegisterRequest(

    @Schema(description = "User email", example = "user@example.com")
    @NotBlank(message = "Email is required")
    @Email(message = "Invalid email format")
    @Size(max = 255, message = "Email must not exceed 255 characters")
    String email,

    @Schema(description = "User password", example = "SecureP@ss123")
    @NotBlank(message = "Password is required")
    @Size(min = 8, max = 100, message = "Password must be between 8 and 100 characters")
    @Pattern(
        regexp = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d)(?=.*[@$!%*?&])[A-Za-z\\d@$!%*?&]+$",
        message = "Password must contain at least one uppercase, lowercase, digit, and special character"
    )
    String password,

    @Schema(description = "User's full name", example = "John Doe")
    @NotBlank(message = "Name is required")
    @Size(min = 2, max = 100, message = "Name must be between 2 and 100 characters")
    String name

) {}

@Schema(description = "User login request")
public record LoginRequest(

    @Schema(description = "User email", example = "user@example.com")
    @NotBlank(message = "Email is required")
    @Email(message = "Invalid email format")
    String email,

    @Schema(description = "User password")
    @NotBlank(message = "Password is required")
    String password

) {}

@Schema(description = "Refresh token request")
public record RefreshTokenRequest(

    @Schema(description = "Refresh token")
    @NotBlank(message = "Refresh token is required")
    String refreshToken

) {}

@Schema(description = "Change password request")
public record ChangePasswordRequest(

    @Schema(description = "Current password")
    @NotBlank(message = "Current password is required")
    String currentPassword,

    @Schema(description = "New password")
    @NotBlank(message = "New password is required")
    @Size(min = 8, max = 100, message = "Password must be between 8 and 100 characters")
    @Pattern(
        regexp = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d)(?=.*[@$!%*?&])[A-Za-z\\d@$!%*?&]+$",
        message = "Password must contain at least one uppercase, lowercase, digit, and special character"
    )
    String newPassword

) {}

// ==================== Response DTOs ====================

@Schema(description = "Authentication response")
@JsonInclude(JsonInclude.Include.NON_NULL)
public record AuthResponse(

    @Schema(description = "JWT access token")
    String accessToken,

    @Schema(description = "JWT refresh token")
    String refreshToken,

    @Schema(description = "Token expiration time in milliseconds")
    long expiresIn,

    @Schema(description = "User profile")
    UserResponse user

) {}

@Schema(description = "User profile response")
@JsonInclude(JsonInclude.Include.NON_NULL)
public record UserResponse(

    @Schema(description = "User ID")
    UUID id,

    @Schema(description = "User email")
    String email,

    @Schema(description = "User's full name")
    String name,

    @Schema(description = "Avatar URL")
    String avatarUrl,

    @Schema(description = "User roles")
    List<String> roles,

    @Schema(description = "Email verified status")
    boolean emailVerified,

    @Schema(description = "Last login timestamp")
    Instant lastLoginAt,

    @Schema(description = "Account creation timestamp")
    Instant createdAt

) {}

// ==================== Error Response ====================

@Schema(description = "Error response")
public record ErrorResponse(

    @Schema(description = "Error type URI")
    String type,

    @Schema(description = "Error title")
    String title,

    @Schema(description = "HTTP status code")
    int status,

    @Schema(description = "Error detail")
    String detail,

    @Schema(description = "Timestamp")
    Instant timestamp

) {
    public static ErrorResponse of(String title, int status, String detail) {
        return new ErrorResponse(
            "about:blank",
            title,
            status,
            detail,
            Instant.now()
        );
    }
}
