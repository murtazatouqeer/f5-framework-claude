# Go Project Layout

Standard Go project layout and organization patterns for production applications.

## Standard Layout

```
project/
├── cmd/                           # Main applications
│   └── api/
│       └── main.go               # Entry point
│
├── internal/                      # Private application code
│   ├── config/
│   │   └── config.go             # Configuration management
│   │
│   ├── domain/                   # Business domain
│   │   ├── user/
│   │   │   ├── entity.go        # Domain entity
│   │   │   ├── repository.go    # Repository interface
│   │   │   ├── service.go       # Service interface
│   │   │   └── errors.go        # Domain errors
│   │   └── product/
│   │       └── ...
│   │
│   ├── handler/                  # HTTP handlers
│   │   ├── user_handler.go
│   │   ├── product_handler.go
│   │   └── router.go
│   │
│   ├── service/                  # Business logic
│   │   ├── user_service.go
│   │   └── product_service.go
│   │
│   ├── repository/               # Data access
│   │   └── postgres/
│   │       ├── user_repository.go
│   │       └── product_repository.go
│   │
│   └── middleware/
│       ├── auth.go
│       ├── logging.go
│       └── recovery.go
│
├── pkg/                          # Public libraries
│   ├── errors/
│   │   └── errors.go
│   ├── response/
│   │   └── response.go
│   └── validator/
│       └── validator.go
│
├── migrations/
│   ├── 001_create_users.up.sql
│   └── 001_create_users.down.sql
│
├── docs/
│   └── swagger.yaml
│
├── scripts/
│   └── setup.sh
│
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yaml
│
├── go.mod
├── go.sum
├── Makefile
└── .env.example
```

## Main Entry Point

```go
// cmd/api/main.go
package main

import (
    "context"
    "log"
    "net/http"
    "os"
    "os/signal"
    "syscall"
    "time"

    "github.com/gin-gonic/gin"

    "myproject/internal/config"
    "myproject/internal/handler"
    "myproject/internal/middleware"
    "myproject/internal/repository/postgres"
    "myproject/internal/service"
    "myproject/pkg/database"
)

func main() {
    // Load configuration
    cfg, err := config.Load()
    if err != nil {
        log.Fatalf("Failed to load config: %v", err)
    }

    // Initialize database
    db, err := database.NewPostgres(cfg.DatabaseURL)
    if err != nil {
        log.Fatalf("Failed to connect to database: %v", err)
    }
    defer db.Close()

    // Initialize layers (dependency injection)
    userRepo := postgres.NewUserRepository(db)
    userService := service.NewUserService(userRepo)
    userHandler := handler.NewUserHandler(userService)

    // Setup router
    if cfg.Environment == "production" {
        gin.SetMode(gin.ReleaseMode)
    }

    router := gin.New()
    router.Use(middleware.Logger())
    router.Use(middleware.Recovery())
    router.Use(middleware.CORS())

    // Health check
    router.GET("/health", func(c *gin.Context) {
        c.JSON(http.StatusOK, gin.H{"status": "healthy"})
    })

    // API routes
    api := router.Group("/api/v1")
    {
        users := api.Group("/users")
        users.Use(middleware.Auth(cfg.JWTSecret))
        {
            users.GET("", userHandler.List)
            users.POST("", userHandler.Create)
            users.GET("/:id", userHandler.Get)
            users.PUT("/:id", userHandler.Update)
            users.DELETE("/:id", userHandler.Delete)
        }
    }

    // Server with graceful shutdown
    srv := &http.Server{
        Addr:         ":" + cfg.Port,
        Handler:      router,
        ReadTimeout:  10 * time.Second,
        WriteTimeout: 10 * time.Second,
        IdleTimeout:  60 * time.Second,
    }

    // Start server in goroutine
    go func() {
        log.Printf("Server starting on port %s", cfg.Port)
        if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
            log.Fatalf("Server failed: %v", err)
        }
    }()

    // Wait for interrupt signal
    quit := make(chan os.Signal, 1)
    signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
    <-quit
    log.Println("Shutting down server...")

    // Graceful shutdown with timeout
    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
    defer cancel()

    if err := srv.Shutdown(ctx); err != nil {
        log.Fatalf("Server forced to shutdown: %v", err)
    }

    log.Println("Server exited")
}
```

## Configuration

```go
// internal/config/config.go
package config

import (
    "fmt"

    "github.com/caarlos0/env/v10"
    "github.com/joho/godotenv"
)

type Config struct {
    Port        string `env:"PORT" envDefault:"8080"`
    Environment string `env:"ENVIRONMENT" envDefault:"development"`

    // Database
    DatabaseURL string `env:"DATABASE_URL,required"`

    // JWT
    JWTSecret string `env:"JWT_SECRET,required"`
    JWTExpiry int    `env:"JWT_EXPIRY" envDefault:"3600"`

    // Redis
    RedisURL string `env:"REDIS_URL" envDefault:"redis://localhost:6379"`

    // Logging
    LogLevel  string `env:"LOG_LEVEL" envDefault:"info"`
    LogFormat string `env:"LOG_FORMAT" envDefault:"json"`
}

func Load() (*Config, error) {
    // Load .env file (ignore if not exists)
    _ = godotenv.Load()

    cfg := &Config{}
    if err := env.Parse(cfg); err != nil {
        return nil, fmt.Errorf("parsing config: %w", err)
    }

    return cfg, nil
}
```

## Directory Guidelines

### `/cmd`
- One directory per binary
- Minimal code - just wiring
- Configuration loading
- Dependency injection

### `/internal`
- Private application code
- Cannot be imported by external packages
- Contains business logic, handlers, repositories

### `/pkg`
- Public reusable libraries
- Can be imported by external projects
- Utility functions, helpers

### `/migrations`
- Database migrations
- Use golang-migrate or goose format
- Both up and down migrations

### `/docs`
- API documentation (Swagger/OpenAPI)
- Architecture diagrams
- Development guides

## Best Practices

1. **Keep cmd/ minimal**: Only initialization and wiring
2. **Use internal/**: Prevents accidental imports
3. **Define interfaces in domain**: Dependency inversion
4. **Dependency injection in main**: Wire dependencies explicitly
5. **Graceful shutdown**: Handle signals properly
6. **Configuration from environment**: 12-factor app compliance
