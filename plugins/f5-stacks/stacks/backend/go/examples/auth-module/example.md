# Authentication Module Example

Complete example of JWT-based authentication in Go using Gin.

## Project Structure

```
auth-module/
├── cmd/
│   └── server/
│       └── main.go
├── internal/
│   ├── config/
│   │   └── config.go
│   ├── domain/
│   │   └── user/
│   │       ├── user.go
│   │       ├── repository.go
│   │       └── errors.go
│   ├── dto/
│   │   └── auth_dto.go
│   ├── handler/
│   │   └── auth_handler.go
│   ├── repository/
│   │   └── postgres/
│   │       └── user_repository.go
│   ├── service/
│   │   └── auth_service.go
│   └── middleware/
│       └── auth_middleware.go
├── pkg/
│   ├── auth/
│   │   ├── jwt.go
│   │   └── password.go
│   └── response/
│       └── response.go
├── migrations/
│   ├── 001_create_users.up.sql
│   └── 001_create_users.down.sql
└── go.mod
```

## Domain Layer

```go
// internal/domain/user/user.go
package user

import (
    "time"

    "github.com/google/uuid"
    "golang.org/x/crypto/bcrypt"
)

type Status string

const (
    StatusActive   Status = "active"
    StatusInactive Status = "inactive"
    StatusBanned   Status = "banned"
)

type Role string

const (
    RoleAdmin Role = "admin"
    RoleUser  Role = "user"
)

type Email string

func (e Email) String() string {
    return string(e)
}

type Password string

func NewPassword(plain string) (Password, error) {
    hashed, err := bcrypt.GenerateFromPassword([]byte(plain), bcrypt.DefaultCost)
    if err != nil {
        return "", err
    }
    return Password(hashed), nil
}

func (p Password) Compare(plain string) bool {
    return bcrypt.CompareHashAndPassword([]byte(p), []byte(plain)) == nil
}

type User struct {
    ID            uuid.UUID  `json:"id"`
    Email         Email      `json:"email"`
    Name          string     `json:"name"`
    Password      Password   `json:"-"`
    Status        Status     `json:"status"`
    Role          Role       `json:"role"`
    EmailVerified bool       `json:"email_verified"`
    LastLoginAt   *time.Time `json:"last_login_at,omitempty"`
    CreatedAt     time.Time  `json:"created_at"`
    UpdatedAt     time.Time  `json:"updated_at"`
    DeletedAt     *time.Time `json:"deleted_at,omitempty"`
}

func New(email, name, password string) (*User, error) {
    hashedPassword, err := NewPassword(password)
    if err != nil {
        return nil, err
    }

    now := time.Now()

    u := &User{
        ID:            uuid.New(),
        Email:         Email(email),
        Name:          name,
        Password:      hashedPassword,
        Status:        StatusActive,
        Role:          RoleUser,
        EmailVerified: false,
        CreatedAt:     now,
        UpdatedAt:     now,
    }

    if err := u.Validate(); err != nil {
        return nil, err
    }

    return u, nil
}

func (u *User) Validate() error {
    if u.Email == "" {
        return ErrInvalidEmail
    }
    if u.Name == "" {
        return ErrInvalidName
    }
    return nil
}

func (u *User) IsActive() bool {
    return u.Status == StatusActive
}

func (u *User) IsAdmin() bool {
    return u.Role == RoleAdmin
}

func (u *User) UpdateLastLogin() {
    now := time.Now()
    u.LastLoginAt = &now
}

func (u *User) ChangePassword(newPassword string) error {
    hashedPassword, err := NewPassword(newPassword)
    if err != nil {
        return err
    }
    u.Password = hashedPassword
    u.UpdatedAt = time.Now()
    return nil
}

// internal/domain/user/errors.go
package user

import "errors"

var (
    ErrNotFound           = errors.New("user not found")
    ErrEmailExists        = errors.New("email already registered")
    ErrInvalidEmail       = errors.New("invalid email")
    ErrInvalidName        = errors.New("invalid name")
    ErrInvalidCredentials = errors.New("invalid email or password")
    ErrAccountInactive    = errors.New("account is not active")
    ErrAccountBanned      = errors.New("account has been banned")
)

// internal/domain/user/repository.go
package user

import (
    "context"

    "github.com/google/uuid"
)

type Repository interface {
    Create(ctx context.Context, user *User) error
    GetByID(ctx context.Context, id uuid.UUID) (*User, error)
    GetByEmail(ctx context.Context, email Email) (*User, error)
    Update(ctx context.Context, user *User) error
    ExistsByEmail(ctx context.Context, email Email) (bool, error)
}
```

## JWT Service

```go
// pkg/auth/jwt.go
package auth

import (
    "errors"
    "fmt"
    "time"

    "github.com/golang-jwt/jwt/v5"
    "github.com/google/uuid"
)

var (
    ErrInvalidToken = errors.New("invalid token")
    ErrExpiredToken = errors.New("token has expired")
)

type Claims struct {
    UserID string `json:"user_id"`
    Email  string `json:"email"`
    Role   string `json:"role"`
    jwt.RegisteredClaims
}

type JWTService struct {
    secretKey     []byte
    accessExpiry  time.Duration
    refreshExpiry time.Duration
    issuer        string
}

type Config struct {
    SecretKey     string
    AccessExpiry  time.Duration
    RefreshExpiry time.Duration
    Issuer        string
}

func NewJWTService(cfg Config) *JWTService {
    return &JWTService{
        secretKey:     []byte(cfg.SecretKey),
        accessExpiry:  cfg.AccessExpiry,
        refreshExpiry: cfg.RefreshExpiry,
        issuer:        cfg.Issuer,
    }
}

type TokenPair struct {
    AccessToken  string    `json:"access_token"`
    RefreshToken string    `json:"refresh_token"`
    ExpiresAt    time.Time `json:"expires_at"`
    TokenType    string    `json:"token_type"`
}

func (s *JWTService) GenerateTokenPair(userID, email, role string) (*TokenPair, error) {
    accessToken, expiresAt, err := s.generateToken(userID, email, role, s.accessExpiry)
    if err != nil {
        return nil, fmt.Errorf("generating access token: %w", err)
    }

    refreshToken, _, err := s.generateToken(userID, email, role, s.refreshExpiry)
    if err != nil {
        return nil, fmt.Errorf("generating refresh token: %w", err)
    }

    return &TokenPair{
        AccessToken:  accessToken,
        RefreshToken: refreshToken,
        ExpiresAt:    expiresAt,
        TokenType:    "Bearer",
    }, nil
}

func (s *JWTService) generateToken(userID, email, role string, expiry time.Duration) (string, time.Time, error) {
    now := time.Now()
    expiresAt := now.Add(expiry)

    claims := &Claims{
        UserID: userID,
        Email:  email,
        Role:   role,
        RegisteredClaims: jwt.RegisteredClaims{
            ID:        uuid.New().String(),
            Subject:   userID,
            Issuer:    s.issuer,
            IssuedAt:  jwt.NewNumericDate(now),
            ExpiresAt: jwt.NewNumericDate(expiresAt),
            NotBefore: jwt.NewNumericDate(now),
        },
    }

    token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
    signedToken, err := token.SignedString(s.secretKey)
    if err != nil {
        return "", time.Time{}, err
    }

    return signedToken, expiresAt, nil
}

func (s *JWTService) ValidateToken(tokenString string) (*Claims, error) {
    token, err := jwt.ParseWithClaims(tokenString, &Claims{}, func(token *jwt.Token) (interface{}, error) {
        if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
            return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
        }
        return s.secretKey, nil
    })

    if err != nil {
        if errors.Is(err, jwt.ErrTokenExpired) {
            return nil, ErrExpiredToken
        }
        return nil, ErrInvalidToken
    }

    claims, ok := token.Claims.(*Claims)
    if !ok || !token.Valid {
        return nil, ErrInvalidToken
    }

    return claims, nil
}

func (s *JWTService) RefreshToken(refreshToken string) (*TokenPair, error) {
    claims, err := s.ValidateToken(refreshToken)
    if err != nil {
        return nil, err
    }

    return s.GenerateTokenPair(claims.UserID, claims.Email, claims.Role)
}
```

## Auth Service

```go
// internal/service/auth_service.go
package service

import (
    "context"
    "fmt"
    "time"

    "github.com/google/uuid"

    "myproject/internal/domain/user"
    "myproject/internal/dto"
    "myproject/pkg/auth"
    "myproject/pkg/cache"
    "myproject/pkg/errors"
)

type AuthService struct {
    userRepo   user.Repository
    jwtService *auth.JWTService
    cache      *cache.RedisCache
}

func NewAuthService(
    userRepo user.Repository,
    jwtService *auth.JWTService,
    cache *cache.RedisCache,
) *AuthService {
    return &AuthService{
        userRepo:   userRepo,
        jwtService: jwtService,
        cache:      cache,
    }
}

func (s *AuthService) Register(ctx context.Context, req dto.RegisterRequest) (*dto.UserResponse, error) {
    // Check if email exists
    exists, err := s.userRepo.ExistsByEmail(ctx, user.Email(req.Email))
    if err != nil {
        return nil, errors.Wrap(err, "checking email existence")
    }
    if exists {
        return nil, errors.ErrConflict.WithMessage("email already registered")
    }

    // Create user
    u, err := user.New(req.Email, req.Name, req.Password)
    if err != nil {
        return nil, errors.Wrap(err, "creating user")
    }

    if err := s.userRepo.Create(ctx, u); err != nil {
        return nil, errors.Wrap(err, "saving user")
    }

    return dto.NewUserResponse(u), nil
}

func (s *AuthService) Login(ctx context.Context, req dto.LoginRequest) (*dto.AuthResponse, error) {
    // Find user
    u, err := s.userRepo.GetByEmail(ctx, user.Email(req.Email))
    if err != nil {
        if errors.Is(err, user.ErrNotFound) {
            return nil, errors.ErrUnauthorized.WithMessage("invalid email or password")
        }
        return nil, errors.Wrap(err, "finding user")
    }

    // Check password
    if !u.Password.Compare(req.Password) {
        return nil, errors.ErrUnauthorized.WithMessage("invalid email or password")
    }

    // Check status
    if !u.IsActive() {
        if u.Status == user.StatusBanned {
            return nil, errors.ErrForbidden.WithMessage("account has been banned")
        }
        return nil, errors.ErrForbidden.WithMessage("account is not active")
    }

    // Update last login
    u.UpdateLastLogin()
    if err := s.userRepo.Update(ctx, u); err != nil {
        // Log but don't fail login
    }

    // Generate tokens
    tokens, err := s.jwtService.GenerateTokenPair(u.ID.String(), string(u.Email), string(u.Role))
    if err != nil {
        return nil, errors.Wrap(err, "generating tokens")
    }

    return &dto.AuthResponse{
        User:   dto.NewUserResponse(u),
        Tokens: tokens,
    }, nil
}

func (s *AuthService) RefreshToken(ctx context.Context, refreshToken string) (*auth.TokenPair, error) {
    // Check if token is blacklisted
    blacklisted, _ := s.isTokenBlacklisted(ctx, refreshToken)
    if blacklisted {
        return nil, errors.ErrUnauthorized.WithMessage("token has been revoked")
    }

    return s.jwtService.RefreshToken(refreshToken)
}

func (s *AuthService) Logout(ctx context.Context, tokenID string, expiry time.Duration) error {
    key := fmt.Sprintf("blacklist:%s", tokenID)
    return s.cache.Set(ctx, key, "1", expiry)
}

func (s *AuthService) GetCurrentUser(ctx context.Context, userID string) (*dto.UserResponse, error) {
    id, err := uuid.Parse(userID)
    if err != nil {
        return nil, errors.ErrInvalidInput.WithMessage("invalid user ID")
    }

    u, err := s.userRepo.GetByID(ctx, id)
    if err != nil {
        if errors.Is(err, user.ErrNotFound) {
            return nil, errors.ErrNotFound.WithMessage("user not found")
        }
        return nil, errors.Wrap(err, "getting user")
    }

    return dto.NewUserResponse(u), nil
}

func (s *AuthService) ChangePassword(ctx context.Context, userID string, req dto.ChangePasswordRequest) error {
    id, err := uuid.Parse(userID)
    if err != nil {
        return errors.ErrInvalidInput.WithMessage("invalid user ID")
    }

    u, err := s.userRepo.GetByID(ctx, id)
    if err != nil {
        return errors.Wrap(err, "getting user")
    }

    if !u.Password.Compare(req.CurrentPassword) {
        return errors.ErrUnauthorized.WithMessage("current password is incorrect")
    }

    if err := u.ChangePassword(req.NewPassword); err != nil {
        return errors.Wrap(err, "changing password")
    }

    return s.userRepo.Update(ctx, u)
}

func (s *AuthService) isTokenBlacklisted(ctx context.Context, tokenID string) (bool, error) {
    key := fmt.Sprintf("blacklist:%s", tokenID)
    _, err := s.cache.Get(ctx, key)
    if err != nil {
        if errors.Is(err, cache.ErrCacheMiss) {
            return false, nil
        }
        return false, err
    }
    return true, nil
}

func (s *AuthService) IsTokenBlacklisted(ctx context.Context, tokenID string) (bool, error) {
    return s.isTokenBlacklisted(ctx, tokenID)
}
```

## Auth Middleware

```go
// internal/middleware/auth_middleware.go
package middleware

import (
    "net/http"
    "strings"

    "github.com/gin-gonic/gin"

    "myproject/internal/service"
    "myproject/pkg/auth"
    "myproject/pkg/response"
)

type AuthMiddleware struct {
    jwtService  *auth.JWTService
    authService *service.AuthService
}

func NewAuthMiddleware(jwtService *auth.JWTService, authService *service.AuthService) *AuthMiddleware {
    return &AuthMiddleware{
        jwtService:  jwtService,
        authService: authService,
    }
}

func (m *AuthMiddleware) Authenticate() gin.HandlerFunc {
    return func(c *gin.Context) {
        authHeader := c.GetHeader("Authorization")
        if authHeader == "" {
            response.Error(c, http.StatusUnauthorized, "AUTH_REQUIRED", "Authorization header required")
            c.Abort()
            return
        }

        parts := strings.Split(authHeader, " ")
        if len(parts) != 2 || strings.ToLower(parts[0]) != "bearer" {
            response.Error(c, http.StatusUnauthorized, "INVALID_AUTH_FORMAT", "Invalid authorization format")
            c.Abort()
            return
        }

        claims, err := m.jwtService.ValidateToken(parts[1])
        if err != nil {
            if err == auth.ErrExpiredToken {
                response.Error(c, http.StatusUnauthorized, "TOKEN_EXPIRED", "Token has expired")
            } else {
                response.Error(c, http.StatusUnauthorized, "INVALID_TOKEN", "Invalid token")
            }
            c.Abort()
            return
        }

        // Check blacklist
        blacklisted, _ := m.authService.IsTokenBlacklisted(c.Request.Context(), claims.ID)
        if blacklisted {
            response.Error(c, http.StatusUnauthorized, "TOKEN_REVOKED", "Token has been revoked")
            c.Abort()
            return
        }

        c.Set("user_id", claims.UserID)
        c.Set("email", claims.Email)
        c.Set("role", claims.Role)
        c.Set("token_id", claims.ID)

        c.Next()
    }
}

func (m *AuthMiddleware) RequireRole(roles ...string) gin.HandlerFunc {
    return func(c *gin.Context) {
        userRole := c.GetString("role")

        for _, role := range roles {
            if userRole == role {
                c.Next()
                return
            }
        }

        response.Error(c, http.StatusForbidden, "FORBIDDEN", "Insufficient permissions")
        c.Abort()
    }
}
```

## Auth Handler

```go
// internal/handler/auth_handler.go
package handler

import (
    "net/http"
    "time"

    "github.com/gin-gonic/gin"

    "myproject/internal/dto"
    "myproject/internal/middleware"
    "myproject/internal/service"
    "myproject/pkg/response"
    "myproject/pkg/validator"
)

type AuthHandler struct {
    authService    *service.AuthService
    authMiddleware *middleware.AuthMiddleware
}

func NewAuthHandler(authService *service.AuthService, authMiddleware *middleware.AuthMiddleware) *AuthHandler {
    return &AuthHandler{
        authService:    authService,
        authMiddleware: authMiddleware,
    }
}

func (h *AuthHandler) Register(c *gin.Context) {
    var req dto.RegisterRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        response.Error(c, http.StatusBadRequest, "INVALID_JSON", err.Error())
        return
    }

    if err := validator.Struct(&req); err != nil {
        response.ValidationError(c, validator.FormatErrors(err))
        return
    }

    user, err := h.authService.Register(c.Request.Context(), req)
    if err != nil {
        response.HandleError(c, err)
        return
    }

    response.Success(c, http.StatusCreated, user)
}

func (h *AuthHandler) Login(c *gin.Context) {
    var req dto.LoginRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        response.Error(c, http.StatusBadRequest, "INVALID_JSON", err.Error())
        return
    }

    if err := validator.Struct(&req); err != nil {
        response.ValidationError(c, validator.FormatErrors(err))
        return
    }

    result, err := h.authService.Login(c.Request.Context(), req)
    if err != nil {
        response.HandleError(c, err)
        return
    }

    response.Success(c, http.StatusOK, result)
}

func (h *AuthHandler) RefreshToken(c *gin.Context) {
    var req dto.RefreshTokenRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        response.Error(c, http.StatusBadRequest, "INVALID_JSON", err.Error())
        return
    }

    tokens, err := h.authService.RefreshToken(c.Request.Context(), req.RefreshToken)
    if err != nil {
        response.HandleError(c, err)
        return
    }

    response.Success(c, http.StatusOK, tokens)
}

func (h *AuthHandler) Logout(c *gin.Context) {
    tokenID := c.GetString("token_id")

    if err := h.authService.Logout(c.Request.Context(), tokenID, 24*time.Hour); err != nil {
        response.HandleError(c, err)
        return
    }

    response.Success(c, http.StatusOK, gin.H{"message": "logged out successfully"})
}

func (h *AuthHandler) Me(c *gin.Context) {
    userID := c.GetString("user_id")

    user, err := h.authService.GetCurrentUser(c.Request.Context(), userID)
    if err != nil {
        response.HandleError(c, err)
        return
    }

    response.Success(c, http.StatusOK, user)
}

func (h *AuthHandler) ChangePassword(c *gin.Context) {
    userID := c.GetString("user_id")

    var req dto.ChangePasswordRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        response.Error(c, http.StatusBadRequest, "INVALID_JSON", err.Error())
        return
    }

    if err := validator.Struct(&req); err != nil {
        response.ValidationError(c, validator.FormatErrors(err))
        return
    }

    if err := h.authService.ChangePassword(c.Request.Context(), userID, req); err != nil {
        response.HandleError(c, err)
        return
    }

    response.Success(c, http.StatusOK, gin.H{"message": "password changed successfully"})
}

func (h *AuthHandler) RegisterRoutes(r *gin.RouterGroup) {
    auth := r.Group("/auth")
    {
        auth.POST("/register", h.Register)
        auth.POST("/login", h.Login)
        auth.POST("/refresh", h.RefreshToken)

        // Protected routes
        protected := auth.Group("")
        protected.Use(h.authMiddleware.Authenticate())
        {
            protected.POST("/logout", h.Logout)
            protected.GET("/me", h.Me)
            protected.POST("/change-password", h.ChangePassword)
        }
    }
}
```

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | /api/v1/auth/register | No | Register new user |
| POST | /api/v1/auth/login | No | Login and get tokens |
| POST | /api/v1/auth/refresh | No | Refresh access token |
| POST | /api/v1/auth/logout | Yes | Logout (blacklist token) |
| GET | /api/v1/auth/me | Yes | Get current user |
| POST | /api/v1/auth/change-password | Yes | Change password |
