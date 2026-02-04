# Security Middleware

Implementing security middleware for Go web applications.

## Authentication Middleware

```go
// internal/middleware/auth.go
package middleware

import (
    "net/http"
    "strings"

    "github.com/gin-gonic/gin"

    "myproject/pkg/auth"
    "myproject/pkg/response"
)

type AuthMiddleware struct {
    jwtService *auth.JWTService
    cache      CacheService
}

func NewAuthMiddleware(jwtService *auth.JWTService, cache CacheService) *AuthMiddleware {
    return &AuthMiddleware{
        jwtService: jwtService,
        cache:      cache,
    }
}

func (m *AuthMiddleware) Authenticate() gin.HandlerFunc {
    return func(c *gin.Context) {
        // Extract token from header
        authHeader := c.GetHeader("Authorization")
        if authHeader == "" {
            response.Error(c, http.StatusUnauthorized, "AUTH_REQUIRED", "Authorization header required")
            c.Abort()
            return
        }

        // Parse Bearer token
        parts := strings.Split(authHeader, " ")
        if len(parts) != 2 || strings.ToLower(parts[0]) != "bearer" {
            response.Error(c, http.StatusUnauthorized, "INVALID_AUTH_FORMAT", "Invalid authorization format")
            c.Abort()
            return
        }

        tokenString := parts[1]

        // Validate token
        claims, err := m.jwtService.ValidateToken(tokenString)
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
        if m.cache != nil {
            isBlacklisted, _ := m.cache.IsBlacklisted(c.Request.Context(), claims.ID)
            if isBlacklisted {
                response.Error(c, http.StatusUnauthorized, "TOKEN_REVOKED", "Token has been revoked")
                c.Abort()
                return
            }
        }

        // Set user info in context
        c.Set("user_id", claims.UserID)
        c.Set("email", claims.Email)
        c.Set("role", claims.Role)
        c.Set("token_id", claims.ID)

        c.Next()
    }
}

// OptionalAuth - doesn't fail if no token
func (m *AuthMiddleware) OptionalAuth() gin.HandlerFunc {
    return func(c *gin.Context) {
        authHeader := c.GetHeader("Authorization")
        if authHeader == "" {
            c.Next()
            return
        }

        parts := strings.Split(authHeader, " ")
        if len(parts) != 2 || strings.ToLower(parts[0]) != "bearer" {
            c.Next()
            return
        }

        claims, err := m.jwtService.ValidateToken(parts[1])
        if err == nil {
            c.Set("user_id", claims.UserID)
            c.Set("email", claims.Email)
            c.Set("role", claims.Role)
        }

        c.Next()
    }
}
```

## CORS Middleware

```go
// internal/middleware/cors.go
package middleware

import (
    "net/http"
    "strings"

    "github.com/gin-gonic/gin"
)

type CORSConfig struct {
    AllowedOrigins   []string
    AllowedMethods   []string
    AllowedHeaders   []string
    ExposedHeaders   []string
    AllowCredentials bool
    MaxAge           int
}

func DefaultCORSConfig() CORSConfig {
    return CORSConfig{
        AllowedOrigins:   []string{"*"},
        AllowedMethods:   []string{"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"},
        AllowedHeaders:   []string{"Origin", "Content-Type", "Accept", "Authorization", "X-Request-ID"},
        ExposedHeaders:   []string{"Content-Length", "X-Request-ID"},
        AllowCredentials: true,
        MaxAge:           86400,
    }
}

func CORS(cfg CORSConfig) gin.HandlerFunc {
    return func(c *gin.Context) {
        origin := c.Request.Header.Get("Origin")

        // Check allowed origins
        allowedOrigin := "*"
        if len(cfg.AllowedOrigins) > 0 && cfg.AllowedOrigins[0] != "*" {
            for _, allowed := range cfg.AllowedOrigins {
                if allowed == origin {
                    allowedOrigin = origin
                    break
                }
            }
            if allowedOrigin == "*" {
                allowedOrigin = ""
            }
        }

        if allowedOrigin != "" {
            c.Header("Access-Control-Allow-Origin", allowedOrigin)
        }

        c.Header("Access-Control-Allow-Methods", strings.Join(cfg.AllowedMethods, ", "))
        c.Header("Access-Control-Allow-Headers", strings.Join(cfg.AllowedHeaders, ", "))
        c.Header("Access-Control-Expose-Headers", strings.Join(cfg.ExposedHeaders, ", "))

        if cfg.AllowCredentials {
            c.Header("Access-Control-Allow-Credentials", "true")
        }

        if cfg.MaxAge > 0 {
            c.Header("Access-Control-Max-Age", fmt.Sprintf("%d", cfg.MaxAge))
        }

        // Handle preflight
        if c.Request.Method == http.MethodOptions {
            c.AbortWithStatus(http.StatusNoContent)
            return
        }

        c.Next()
    }
}
```

## Rate Limiting Middleware

```go
// internal/middleware/rate_limit.go
package middleware

import (
    "net/http"
    "sync"
    "time"

    "github.com/gin-gonic/gin"
    "golang.org/x/time/rate"

    "myproject/pkg/response"
)

type RateLimiter struct {
    visitors map[string]*visitor
    mu       sync.RWMutex
    rate     rate.Limit
    burst    int
}

type visitor struct {
    limiter  *rate.Limiter
    lastSeen time.Time
}

func NewRateLimiter(r rate.Limit, burst int) *RateLimiter {
    rl := &RateLimiter{
        visitors: make(map[string]*visitor),
        rate:     r,
        burst:    burst,
    }

    // Cleanup old visitors
    go rl.cleanupVisitors()

    return rl
}

func (rl *RateLimiter) getVisitor(ip string) *rate.Limiter {
    rl.mu.Lock()
    defer rl.mu.Unlock()

    v, exists := rl.visitors[ip]
    if !exists {
        limiter := rate.NewLimiter(rl.rate, rl.burst)
        rl.visitors[ip] = &visitor{limiter: limiter, lastSeen: time.Now()}
        return limiter
    }

    v.lastSeen = time.Now()
    return v.limiter
}

func (rl *RateLimiter) cleanupVisitors() {
    for {
        time.Sleep(time.Minute)

        rl.mu.Lock()
        for ip, v := range rl.visitors {
            if time.Since(v.lastSeen) > 3*time.Minute {
                delete(rl.visitors, ip)
            }
        }
        rl.mu.Unlock()
    }
}

func (rl *RateLimiter) Limit() gin.HandlerFunc {
    return func(c *gin.Context) {
        ip := c.ClientIP()
        limiter := rl.getVisitor(ip)

        if !limiter.Allow() {
            response.Error(c, http.StatusTooManyRequests, "RATE_LIMIT_EXCEEDED", "Too many requests")
            c.Abort()
            return
        }

        c.Next()
    }
}

// Redis-based rate limiting
type RedisRateLimiter struct {
    redis  *redis.Client
    limit  int
    window time.Duration
}

func (rl *RedisRateLimiter) Limit() gin.HandlerFunc {
    return func(c *gin.Context) {
        key := fmt.Sprintf("rate_limit:%s", c.ClientIP())

        count, err := rl.redis.Incr(c.Request.Context(), key).Result()
        if err != nil {
            c.Next()
            return
        }

        if count == 1 {
            rl.redis.Expire(c.Request.Context(), key, rl.window)
        }

        if count > int64(rl.limit) {
            c.Header("X-RateLimit-Limit", fmt.Sprintf("%d", rl.limit))
            c.Header("X-RateLimit-Remaining", "0")
            response.Error(c, http.StatusTooManyRequests, "RATE_LIMIT_EXCEEDED", "Too many requests")
            c.Abort()
            return
        }

        c.Header("X-RateLimit-Limit", fmt.Sprintf("%d", rl.limit))
        c.Header("X-RateLimit-Remaining", fmt.Sprintf("%d", rl.limit-int(count)))

        c.Next()
    }
}
```

## Security Headers Middleware

```go
// internal/middleware/security.go
package middleware

import (
    "github.com/gin-gonic/gin"
)

func SecurityHeaders() gin.HandlerFunc {
    return func(c *gin.Context) {
        // Prevent MIME sniffing
        c.Header("X-Content-Type-Options", "nosniff")

        // XSS protection
        c.Header("X-XSS-Protection", "1; mode=block")

        // Clickjacking protection
        c.Header("X-Frame-Options", "DENY")

        // Content Security Policy
        c.Header("Content-Security-Policy", "default-src 'self'")

        // Referrer Policy
        c.Header("Referrer-Policy", "strict-origin-when-cross-origin")

        // HSTS (only in production with HTTPS)
        // c.Header("Strict-Transport-Security", "max-age=31536000; includeSubDomains")

        c.Next()
    }
}
```

## Request ID Middleware

```go
// internal/middleware/request_id.go
package middleware

import (
    "github.com/gin-gonic/gin"
    "github.com/google/uuid"
)

const RequestIDHeader = "X-Request-ID"

func RequestID() gin.HandlerFunc {
    return func(c *gin.Context) {
        requestID := c.GetHeader(RequestIDHeader)
        if requestID == "" {
            requestID = uuid.New().String()
        }

        c.Set("request_id", requestID)
        c.Header(RequestIDHeader, requestID)

        c.Next()
    }
}
```

## Logging Middleware

```go
// internal/middleware/logging.go
package middleware

import (
    "time"

    "github.com/gin-gonic/gin"
    "go.uber.org/zap"
)

func Logger(logger *zap.Logger) gin.HandlerFunc {
    return func(c *gin.Context) {
        start := time.Now()
        path := c.Request.URL.Path
        query := c.Request.URL.RawQuery

        c.Next()

        latency := time.Since(start)
        status := c.Writer.Status()

        fields := []zap.Field{
            zap.String("request_id", c.GetString("request_id")),
            zap.String("method", c.Request.Method),
            zap.String("path", path),
            zap.String("query", query),
            zap.Int("status", status),
            zap.Duration("latency", latency),
            zap.String("client_ip", c.ClientIP()),
            zap.String("user_agent", c.Request.UserAgent()),
        }

        if userID := c.GetString("user_id"); userID != "" {
            fields = append(fields, zap.String("user_id", userID))
        }

        if status >= 500 {
            logger.Error("Server error", fields...)
        } else if status >= 400 {
            logger.Warn("Client error", fields...)
        } else {
            logger.Info("Request completed", fields...)
        }
    }
}
```

## Best Practices

1. **Order Matters**: Apply middleware in correct order
2. **Early Exit**: Abort early on auth failures
3. **Context Values**: Use gin.Context for request-scoped data
4. **Error Handling**: Return consistent error responses
5. **Logging**: Log security-relevant events
6. **Rate Limiting**: Protect against abuse
