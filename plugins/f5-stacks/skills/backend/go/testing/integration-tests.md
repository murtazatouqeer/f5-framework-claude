# Integration Tests

Implementing integration tests with testcontainers in Go applications.

## Setup Testcontainers

```bash
go get github.com/testcontainers/testcontainers-go
go get github.com/testcontainers/testcontainers-go/modules/postgres
go get github.com/testcontainers/testcontainers-go/modules/redis
```

## PostgreSQL Integration Test

```go
// internal/repository/postgres/user_repository_integration_test.go
//go:build integration

package postgres

import (
    "context"
    "testing"
    "time"

    "github.com/google/uuid"
    "github.com/jmoiron/sqlx"
    _ "github.com/lib/pq"
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"
    "github.com/stretchr/testify/suite"
    "github.com/testcontainers/testcontainers-go"
    "github.com/testcontainers/testcontainers-go/modules/postgres"
    "github.com/testcontainers/testcontainers-go/wait"

    "myproject/internal/domain/user"
)

type UserRepositorySuite struct {
    suite.Suite
    container testcontainers.Container
    db        *sqlx.DB
    repo      user.Repository
}

func (s *UserRepositorySuite) SetupSuite() {
    ctx := context.Background()

    // Start PostgreSQL container
    pgContainer, err := postgres.RunContainer(ctx,
        testcontainers.WithImage("postgres:16-alpine"),
        postgres.WithDatabase("testdb"),
        postgres.WithUsername("test"),
        postgres.WithPassword("test"),
        testcontainers.WithWaitStrategy(
            wait.ForLog("database system is ready to accept connections").
                WithOccurrence(2).
                WithStartupTimeout(30*time.Second),
        ),
    )
    require.NoError(s.T(), err)
    s.container = pgContainer

    // Get connection string
    connStr, err := pgContainer.ConnectionString(ctx, "sslmode=disable")
    require.NoError(s.T(), err)

    // Connect to database
    s.db, err = sqlx.Connect("postgres", connStr)
    require.NoError(s.T(), err)

    // Run migrations
    s.runMigrations()

    // Create repository
    s.repo = NewUserRepository(s.db)
}

func (s *UserRepositorySuite) TearDownSuite() {
    if s.db != nil {
        s.db.Close()
    }
    if s.container != nil {
        s.container.Terminate(context.Background())
    }
}

func (s *UserRepositorySuite) SetupTest() {
    // Clean up before each test
    s.db.Exec("TRUNCATE users CASCADE")
}

func (s *UserRepositorySuite) runMigrations() {
    schema := `
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            email VARCHAR(255) NOT NULL UNIQUE,
            name VARCHAR(100) NOT NULL,
            password VARCHAR(255) NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'active',
            role VARCHAR(20) NOT NULL DEFAULT 'user',
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
            deleted_at TIMESTAMP
        );
    `
    _, err := s.db.Exec(schema)
    require.NoError(s.T(), err)
}

func (s *UserRepositorySuite) TestCreate() {
    ctx := context.Background()
    u := &user.User{
        ID:       uuid.New(),
        Email:    "test@example.com",
        Name:     "Test User",
        Password: "hashedpassword",
        Status:   user.StatusActive,
        Role:     user.RoleUser,
    }

    err := s.repo.Create(ctx, u)
    require.NoError(s.T(), err)

    // Verify user was created
    found, err := s.repo.GetByID(ctx, u.ID)
    require.NoError(s.T(), err)
    assert.Equal(s.T(), u.Email, found.Email)
    assert.Equal(s.T(), u.Name, found.Name)
}

func (s *UserRepositorySuite) TestGetByEmail() {
    ctx := context.Background()

    // Create test user
    u := &user.User{
        ID:       uuid.New(),
        Email:    "findme@example.com",
        Name:     "Find Me",
        Password: "hashedpassword",
        Status:   user.StatusActive,
    }
    err := s.repo.Create(ctx, u)
    require.NoError(s.T(), err)

    // Find by email
    found, err := s.repo.GetByEmail(ctx, user.Email("findme@example.com"))
    require.NoError(s.T(), err)
    assert.Equal(s.T(), u.ID, found.ID)

    // Not found case
    _, err = s.repo.GetByEmail(ctx, user.Email("notfound@example.com"))
    assert.ErrorIs(s.T(), err, user.ErrNotFound)
}

func (s *UserRepositorySuite) TestUpdate() {
    ctx := context.Background()

    // Create test user
    u := &user.User{
        ID:       uuid.New(),
        Email:    "update@example.com",
        Name:     "Original Name",
        Password: "hashedpassword",
        Status:   user.StatusActive,
    }
    err := s.repo.Create(ctx, u)
    require.NoError(s.T(), err)

    // Update user
    u.Name = "Updated Name"
    u.Status = user.StatusInactive
    err = s.repo.Update(ctx, u)
    require.NoError(s.T(), err)

    // Verify update
    found, err := s.repo.GetByID(ctx, u.ID)
    require.NoError(s.T(), err)
    assert.Equal(s.T(), "Updated Name", found.Name)
    assert.Equal(s.T(), user.StatusInactive, found.Status)
}

func (s *UserRepositorySuite) TestDelete() {
    ctx := context.Background()

    // Create test user
    u := &user.User{
        ID:       uuid.New(),
        Email:    "delete@example.com",
        Name:     "Delete Me",
        Password: "hashedpassword",
        Status:   user.StatusActive,
    }
    err := s.repo.Create(ctx, u)
    require.NoError(s.T(), err)

    // Delete user
    err = s.repo.Delete(ctx, u.ID)
    require.NoError(s.T(), err)

    // Verify soft delete
    _, err = s.repo.GetByID(ctx, u.ID)
    assert.ErrorIs(s.T(), err, user.ErrNotFound)
}

func TestUserRepositorySuite(t *testing.T) {
    if testing.Short() {
        t.Skip("Skipping integration test")
    }
    suite.Run(t, new(UserRepositorySuite))
}
```

## Redis Integration Test

```go
// internal/cache/redis_cache_integration_test.go
//go:build integration

package cache

import (
    "context"
    "testing"
    "time"

    "github.com/redis/go-redis/v9"
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"
    "github.com/stretchr/testify/suite"
    "github.com/testcontainers/testcontainers-go"
    "github.com/testcontainers/testcontainers-go/modules/redis"
)

type RedisCacheSuite struct {
    suite.Suite
    container testcontainers.Container
    client    *redis.Client
    cache     *RedisCache
}

func (s *RedisCacheSuite) SetupSuite() {
    ctx := context.Background()

    // Start Redis container
    redisContainer, err := redis.RunContainer(ctx,
        testcontainers.WithImage("redis:7-alpine"),
    )
    require.NoError(s.T(), err)
    s.container = redisContainer

    // Get connection string
    endpoint, err := redisContainer.Endpoint(ctx, "")
    require.NoError(s.T(), err)

    // Create Redis client
    s.client = redis.NewClient(&redis.Options{
        Addr: endpoint,
    })

    // Create cache
    s.cache = NewRedisCache(s.client)
}

func (s *RedisCacheSuite) TearDownSuite() {
    if s.client != nil {
        s.client.Close()
    }
    if s.container != nil {
        s.container.Terminate(context.Background())
    }
}

func (s *RedisCacheSuite) SetupTest() {
    s.client.FlushAll(context.Background())
}

func (s *RedisCacheSuite) TestSetAndGet() {
    ctx := context.Background()

    err := s.cache.Set(ctx, "test-key", "test-value", time.Minute)
    require.NoError(s.T(), err)

    value, err := s.cache.Get(ctx, "test-key")
    require.NoError(s.T(), err)
    assert.Equal(s.T(), "test-value", value)
}

func (s *RedisCacheSuite) TestExpiration() {
    ctx := context.Background()

    err := s.cache.Set(ctx, "expiring-key", "value", 100*time.Millisecond)
    require.NoError(s.T(), err)

    // Should exist initially
    _, err = s.cache.Get(ctx, "expiring-key")
    require.NoError(s.T(), err)

    // Wait for expiration
    time.Sleep(150 * time.Millisecond)

    // Should be gone
    _, err = s.cache.Get(ctx, "expiring-key")
    assert.ErrorIs(s.T(), err, ErrCacheMiss)
}

func TestRedisCacheSuite(t *testing.T) {
    if testing.Short() {
        t.Skip("Skipping integration test")
    }
    suite.Run(t, new(RedisCacheSuite))
}
```

## API Integration Test

```go
// internal/handler/integration_test.go
//go:build integration

package handler

import (
    "bytes"
    "context"
    "encoding/json"
    "net/http"
    "net/http/httptest"
    "testing"

    "github.com/gin-gonic/gin"
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"
    "github.com/stretchr/testify/suite"

    "myproject/internal/config"
    "myproject/internal/repository/postgres"
    "myproject/internal/service"
)

type APIIntegrationSuite struct {
    suite.Suite
    router *gin.Engine
    db     *sqlx.DB
}

func (s *APIIntegrationSuite) SetupSuite() {
    gin.SetMode(gin.TestMode)

    // Setup test database (using testcontainers)
    s.db = setupTestDB(s.T())

    // Create real dependencies
    userRepo := postgres.NewUserRepository(s.db)
    userService := service.NewUserService(userRepo)
    userHandler := NewUserHandler(userService)

    // Setup router
    s.router = gin.New()
    s.router.POST("/api/users", userHandler.Create)
    s.router.GET("/api/users/:id", userHandler.GetByID)
}

func (s *APIIntegrationSuite) TearDownSuite() {
    if s.db != nil {
        s.db.Close()
    }
}

func (s *APIIntegrationSuite) SetupTest() {
    s.db.Exec("TRUNCATE users CASCADE")
}

func (s *APIIntegrationSuite) TestCreateAndGetUser() {
    // Create user
    createBody := map[string]string{
        "email":    "integration@example.com",
        "name":     "Integration Test",
        "password": "SecureP@ss123",
    }
    bodyBytes, _ := json.Marshal(createBody)

    req := httptest.NewRequest(http.MethodPost, "/api/users", bytes.NewBuffer(bodyBytes))
    req.Header.Set("Content-Type", "application/json")
    rec := httptest.NewRecorder()

    s.router.ServeHTTP(rec, req)

    require.Equal(s.T(), http.StatusCreated, rec.Code)

    var createResponse map[string]interface{}
    json.Unmarshal(rec.Body.Bytes(), &createResponse)
    userID := createResponse["data"].(map[string]interface{})["id"].(string)

    // Get user
    req = httptest.NewRequest(http.MethodGet, "/api/users/"+userID, nil)
    rec = httptest.NewRecorder()

    s.router.ServeHTTP(rec, req)

    require.Equal(s.T(), http.StatusOK, rec.Code)

    var getResponse map[string]interface{}
    json.Unmarshal(rec.Body.Bytes(), &getResponse)
    assert.Equal(s.T(), "integration@example.com", getResponse["data"].(map[string]interface{})["email"])
}

func TestAPIIntegrationSuite(t *testing.T) {
    if testing.Short() {
        t.Skip("Skipping integration test")
    }
    suite.Run(t, new(APIIntegrationSuite))
}
```

## Test Helper Package

```go
// internal/testutil/containers.go
package testutil

import (
    "context"
    "testing"
    "time"

    "github.com/jmoiron/sqlx"
    "github.com/testcontainers/testcontainers-go"
    "github.com/testcontainers/testcontainers-go/modules/postgres"
    "github.com/testcontainers/testcontainers-go/wait"
)

type TestContainer struct {
    Container testcontainers.Container
    DB        *sqlx.DB
}

func SetupPostgres(t *testing.T) *TestContainer {
    t.Helper()
    ctx := context.Background()

    pgContainer, err := postgres.RunContainer(ctx,
        testcontainers.WithImage("postgres:16-alpine"),
        postgres.WithDatabase("testdb"),
        postgres.WithUsername("test"),
        postgres.WithPassword("test"),
        testcontainers.WithWaitStrategy(
            wait.ForLog("database system is ready to accept connections").
                WithOccurrence(2).
                WithStartupTimeout(30*time.Second),
        ),
    )
    if err != nil {
        t.Fatalf("Failed to start postgres container: %v", err)
    }

    connStr, err := pgContainer.ConnectionString(ctx, "sslmode=disable")
    if err != nil {
        pgContainer.Terminate(ctx)
        t.Fatalf("Failed to get connection string: %v", err)
    }

    db, err := sqlx.Connect("postgres", connStr)
    if err != nil {
        pgContainer.Terminate(ctx)
        t.Fatalf("Failed to connect to database: %v", err)
    }

    return &TestContainer{
        Container: pgContainer,
        DB:        db,
    }
}

func (tc *TestContainer) Cleanup() {
    if tc.DB != nil {
        tc.DB.Close()
    }
    if tc.Container != nil {
        tc.Container.Terminate(context.Background())
    }
}
```

## Makefile Commands

```makefile
# Makefile
.PHONY: test test-unit test-integration

test:
	go test ./...

test-unit:
	go test -short ./...

test-integration:
	go test -tags=integration ./...

test-coverage:
	go test -coverprofile=coverage.out ./...
	go tool cover -html=coverage.out -o coverage.html
```

## Best Practices

1. **Use Build Tags**: Separate integration tests with `//go:build integration`
2. **Test Suites**: Use testify suite for setup/teardown
3. **Cleanup**: Always clean containers in TearDownSuite
4. **Parallel Safety**: Don't run integration tests in parallel
5. **Short Flag**: Skip integration tests with `go test -short`
6. **Real Dependencies**: Use real databases for integration tests
