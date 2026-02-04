# Go Middleware Template

Template for creating HTTP middleware in Go applications.

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{middleware_name}}` | Middleware name | Auth |
| `{{middleware_name_lower}}` | Middleware name (lowercase) | auth |
| `{{package_name}}` | Package name | middleware |

## Basic Middleware Template

```go
// internal/middleware/{{middleware_name_lower}}.go
package middleware

import (
    "github.com/gin-gonic/gin"
)

func {{middleware_name}}() gin.HandlerFunc {
    return func(c *gin.Context) {
        // Before request processing
        {{#before_logic}}
        {{before_code}}
        {{/before_logic}}

        c.Next()

        // After request processing
        {{#after_logic}}
        {{after_code}}
        {{/after_logic}}
    }
}
```

## Middleware with Dependencies Template

```go
// internal/middleware/{{middleware_name_lower}}.go
package middleware

import (
    "net/http"

    "github.com/gin-gonic/gin"

    "{{module_path}}/pkg/response"
)

type {{middleware_name}}Middleware struct {
    {{#dependencies}}
    {{dep_name}} {{dep_type}}
    {{/dependencies}}
}

func New{{middleware_name}}Middleware({{constructor_params}}) *{{middleware_name}}Middleware {
    return &{{middleware_name}}Middleware{
        {{#dependencies}}
        {{dep_name}}: {{dep_param}},
        {{/dependencies}}
    }
}

func (m *{{middleware_name}}Middleware) Handle() gin.HandlerFunc {
    return func(c *gin.Context) {
        {{#middleware_logic}}
        {{logic_code}}
        {{/middleware_logic}}

        c.Next()
    }
}
```

## Example: Request Logger Middleware

```go
// internal/middleware/logger.go
package middleware

import (
    "time"

    "github.com/gin-gonic/gin"
    "go.uber.org/zap"
)

type LoggerMiddleware struct {
    logger *zap.Logger
}

func NewLoggerMiddleware(logger *zap.Logger) *LoggerMiddleware {
    return &LoggerMiddleware{logger: logger}
}

func (m *LoggerMiddleware) Handle() gin.HandlerFunc {
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
            m.logger.Error("Server error", fields...)
        } else if status >= 400 {
            m.logger.Warn("Client error", fields...)
        } else {
            m.logger.Info("Request completed", fields...)
        }
    }
}
```

## Example: Rate Limiter Middleware

```go
// internal/middleware/rate_limiter.go
package middleware

import (
    "net/http"
    "sync"
    "time"

    "github.com/gin-gonic/gin"
    "golang.org/x/time/rate"

    "myproject/pkg/response"
)

type RateLimiterMiddleware struct {
    visitors map[string]*visitor
    mu       sync.RWMutex
    rate     rate.Limit
    burst    int
}

type visitor struct {
    limiter  *rate.Limiter
    lastSeen time.Time
}

func NewRateLimiterMiddleware(r rate.Limit, burst int) *RateLimiterMiddleware {
    rl := &RateLimiterMiddleware{
        visitors: make(map[string]*visitor),
        rate:     r,
        burst:    burst,
    }
    go rl.cleanupVisitors()
    return rl
}

func (m *RateLimiterMiddleware) getVisitor(ip string) *rate.Limiter {
    m.mu.Lock()
    defer m.mu.Unlock()

    v, exists := m.visitors[ip]
    if !exists {
        limiter := rate.NewLimiter(m.rate, m.burst)
        m.visitors[ip] = &visitor{limiter: limiter, lastSeen: time.Now()}
        return limiter
    }

    v.lastSeen = time.Now()
    return v.limiter
}

func (m *RateLimiterMiddleware) cleanupVisitors() {
    for {
        time.Sleep(time.Minute)
        m.mu.Lock()
        for ip, v := range m.visitors {
            if time.Since(v.lastSeen) > 3*time.Minute {
                delete(m.visitors, ip)
            }
        }
        m.mu.Unlock()
    }
}

func (m *RateLimiterMiddleware) Handle() gin.HandlerFunc {
    return func(c *gin.Context) {
        ip := c.ClientIP()
        limiter := m.getVisitor(ip)

        if !limiter.Allow() {
            response.Error(c, http.StatusTooManyRequests, "RATE_LIMIT_EXCEEDED", "Too many requests")
            c.Abort()
            return
        }

        c.Next()
    }
}
```

## Example: CORS Middleware

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

        // Determine allowed origin
        allowedOrigin := ""
        if len(cfg.AllowedOrigins) > 0 {
            if cfg.AllowedOrigins[0] == "*" {
                allowedOrigin = "*"
            } else {
                for _, allowed := range cfg.AllowedOrigins {
                    if allowed == origin {
                        allowedOrigin = origin
                        break
                    }
                }
            }
        }

        if allowedOrigin != "" {
            c.Header("Access-Control-Allow-Origin", allowedOrigin)
            c.Header("Access-Control-Allow-Methods", strings.Join(cfg.AllowedMethods, ", "))
            c.Header("Access-Control-Allow-Headers", strings.Join(cfg.AllowedHeaders, ", "))
            c.Header("Access-Control-Expose-Headers", strings.Join(cfg.ExposedHeaders, ", "))

            if cfg.AllowCredentials && allowedOrigin != "*" {
                c.Header("Access-Control-Allow-Credentials", "true")
            }

            if cfg.MaxAge > 0 {
                c.Header("Access-Control-Max-Age", fmt.Sprintf("%d", cfg.MaxAge))
            }
        }

        if c.Request.Method == http.MethodOptions {
            c.AbortWithStatus(http.StatusNoContent)
            return
        }

        c.Next()
    }
}
```

## Middleware Chain Setup

```go
// internal/middleware/chain.go
package middleware

import (
    "github.com/gin-gonic/gin"
    "go.uber.org/zap"
)

type Middlewares struct {
    Logger      *LoggerMiddleware
    Auth        *AuthMiddleware
    RateLimiter *RateLimiterMiddleware
    Recovery    gin.HandlerFunc
    RequestID   gin.HandlerFunc
    CORS        gin.HandlerFunc
}

func NewMiddlewares(
    logger *zap.Logger,
    authService AuthService,
    cache CacheService,
) *Middlewares {
    return &Middlewares{
        Logger:      NewLoggerMiddleware(logger),
        Auth:        NewAuthMiddleware(authService, cache),
        RateLimiter: NewRateLimiterMiddleware(100, 10),
        Recovery:    Recovery(logger),
        RequestID:   RequestID(),
        CORS:        CORS(DefaultCORSConfig()),
    }
}

func (m *Middlewares) Global() []gin.HandlerFunc {
    return []gin.HandlerFunc{
        m.Recovery,
        m.RequestID,
        m.CORS,
        m.Logger.Handle(),
        m.RateLimiter.Handle(),
    }
}
```

## Usage

```bash
# Generate auth middleware
f5 generate middleware Auth --deps "authService:AuthService,cache:CacheService"

# Generate rate limiter middleware
f5 generate middleware RateLimiter --deps "rate:rate.Limit,burst:int"
```
