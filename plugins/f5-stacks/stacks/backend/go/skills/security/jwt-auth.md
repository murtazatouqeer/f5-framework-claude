# JWT Authentication

Implementing JWT-based authentication in Go applications.

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
}

func (s *JWTService) GenerateTokenPair(userID, email, role string) (*TokenPair, error) {
    // Access token
    accessToken, expiresAt, err := s.generateToken(userID, email, role, s.accessExpiry)
    if err != nil {
        return nil, fmt.Errorf("generating access token: %w", err)
    }

    // Refresh token
    refreshToken, _, err := s.generateToken(userID, email, role, s.refreshExpiry)
    if err != nil {
        return nil, fmt.Errorf("generating refresh token: %w", err)
    }

    return &TokenPair{
        AccessToken:  accessToken,
        RefreshToken: refreshToken,
        ExpiresAt:    expiresAt,
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

## Auth Handler

```go
// internal/handler/auth_handler.go
package handler

import (
    "net/http"

    "github.com/gin-gonic/gin"

    "myproject/internal/service"
    "myproject/pkg/response"
)

type AuthHandler struct {
    authService *service.AuthService
}

func NewAuthHandler(authService *service.AuthService) *AuthHandler {
    return &AuthHandler{authService: authService}
}

type LoginRequest struct {
    Email    string `json:"email" binding:"required,email"`
    Password string `json:"password" binding:"required,min=8"`
}

type RegisterRequest struct {
    Email    string `json:"email" binding:"required,email"`
    Name     string `json:"name" binding:"required,min=2,max=100"`
    Password string `json:"password" binding:"required,min=8"`
}

type RefreshRequest struct {
    RefreshToken string `json:"refresh_token" binding:"required"`
}

func (h *AuthHandler) Register(c *gin.Context) {
    var req RegisterRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        response.ValidationError(c, err)
        return
    }

    user, err := h.authService.Register(c.Request.Context(), service.RegisterInput{
        Email:    req.Email,
        Name:     req.Name,
        Password: req.Password,
    })
    if err != nil {
        response.HandleError(c, err)
        return
    }

    response.Success(c, http.StatusCreated, user)
}

func (h *AuthHandler) Login(c *gin.Context) {
    var req LoginRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        response.ValidationError(c, err)
        return
    }

    tokens, err := h.authService.Login(c.Request.Context(), service.LoginInput{
        Email:    req.Email,
        Password: req.Password,
    })
    if err != nil {
        response.HandleError(c, err)
        return
    }

    response.Success(c, http.StatusOK, tokens)
}

func (h *AuthHandler) Refresh(c *gin.Context) {
    var req RefreshRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        response.ValidationError(c, err)
        return
    }

    tokens, err := h.authService.RefreshTokens(c.Request.Context(), req.RefreshToken)
    if err != nil {
        response.HandleError(c, err)
        return
    }

    response.Success(c, http.StatusOK, tokens)
}

func (h *AuthHandler) Logout(c *gin.Context) {
    // Get token from context (set by auth middleware)
    tokenID := c.GetString("token_id")

    if err := h.authService.Logout(c.Request.Context(), tokenID); err != nil {
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
```

## Auth Service

```go
// internal/service/auth_service.go
package service

import (
    "context"
    "fmt"

    "myproject/internal/domain/user"
    "myproject/pkg/auth"
)

type AuthService struct {
    userRepo   user.Repository
    jwtService *auth.JWTService
    cache      CacheService // For token blacklist
}

func NewAuthService(
    userRepo user.Repository,
    jwtService *auth.JWTService,
    cache CacheService,
) *AuthService {
    return &AuthService{
        userRepo:   userRepo,
        jwtService: jwtService,
        cache:      cache,
    }
}

type RegisterInput struct {
    Email    string
    Name     string
    Password string
}

type LoginInput struct {
    Email    string
    Password string
}

func (s *AuthService) Register(ctx context.Context, input RegisterInput) (*user.User, error) {
    // Check if email exists
    exists, err := s.userRepo.ExistsByEmail(ctx, user.Email(input.Email))
    if err != nil {
        return nil, fmt.Errorf("checking email: %w", err)
    }
    if exists {
        return nil, user.ErrEmailExists
    }

    // Create user
    u, err := user.NewUser(input.Email, input.Name, input.Password)
    if err != nil {
        return nil, err
    }

    if err := s.userRepo.Create(ctx, u); err != nil {
        return nil, fmt.Errorf("creating user: %w", err)
    }

    return u, nil
}

func (s *AuthService) Login(ctx context.Context, input LoginInput) (*auth.TokenPair, error) {
    // Find user
    u, err := s.userRepo.GetByEmail(ctx, user.Email(input.Email))
    if err != nil {
        if err == user.ErrNotFound {
            return nil, user.ErrInvalidCredentials
        }
        return nil, err
    }

    // Verify password
    if !u.Password.Compare(input.Password) {
        return nil, user.ErrInvalidCredentials
    }

    // Check status
    if u.Status != user.StatusActive {
        return nil, user.ErrAccountInactive
    }

    // Generate tokens
    tokens, err := s.jwtService.GenerateTokenPair(u.ID.String(), string(u.Email), string(u.Role))
    if err != nil {
        return nil, fmt.Errorf("generating tokens: %w", err)
    }

    return tokens, nil
}

func (s *AuthService) RefreshTokens(ctx context.Context, refreshToken string) (*auth.TokenPair, error) {
    return s.jwtService.RefreshToken(refreshToken)
}

func (s *AuthService) Logout(ctx context.Context, tokenID string) error {
    // Add token to blacklist
    return s.cache.SetBlacklist(ctx, tokenID, time.Hour*24)
}

func (s *AuthService) GetCurrentUser(ctx context.Context, userID string) (*user.User, error) {
    id, err := uuid.Parse(userID)
    if err != nil {
        return nil, user.ErrInvalidID
    }
    return s.userRepo.GetByID(ctx, id)
}
```

## Password Hashing

```go
// pkg/auth/password.go
package auth

import (
    "golang.org/x/crypto/bcrypt"
)

const (
    DefaultCost = bcrypt.DefaultCost
    MinCost     = bcrypt.MinCost
    MaxCost     = bcrypt.MaxCost
)

func HashPassword(password string) (string, error) {
    bytes, err := bcrypt.GenerateFromPassword([]byte(password), DefaultCost)
    return string(bytes), err
}

func CheckPassword(password, hash string) bool {
    err := bcrypt.CompareHashAndPassword([]byte(hash), []byte(password))
    return err == nil
}
```

## Best Practices

1. **Short Access Tokens**: 15-30 minutes expiry
2. **Longer Refresh Tokens**: 7-30 days expiry
3. **Token Blacklist**: Invalidate tokens on logout
4. **Secure Storage**: Store refresh tokens securely
5. **HTTPS Only**: Always use HTTPS in production
6. **Rate Limiting**: Protect login endpoints
