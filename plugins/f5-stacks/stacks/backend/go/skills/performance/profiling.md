# Profiling and Benchmarking

Performance analysis and optimization in Go applications.

## Benchmark Tests

```go
// internal/service/user_service_benchmark_test.go
package service

import (
    "context"
    "testing"
)

func BenchmarkUserService_GetByID(b *testing.B) {
    // Setup
    repo := setupTestRepo()
    svc := NewUserService(repo)
    ctx := context.Background()
    userID := "123e4567-e89b-12d3-a456-426614174000"

    // Reset timer after setup
    b.ResetTimer()

    for i := 0; i < b.N; i++ {
        _, _ = svc.GetByID(ctx, userID)
    }
}

func BenchmarkUserService_GetByID_Parallel(b *testing.B) {
    repo := setupTestRepo()
    svc := NewUserService(repo)
    ctx := context.Background()
    userID := "123e4567-e89b-12d3-a456-426614174000"

    b.ResetTimer()
    b.RunParallel(func(pb *testing.PB) {
        for pb.Next() {
            _, _ = svc.GetByID(ctx, userID)
        }
    })
}

func BenchmarkSlugify(b *testing.B) {
    inputs := []string{
        "Hello World",
        "Test with UPPERCASE",
        "Special!@#Characters",
        "Very Long String That Goes On And On And On",
    }

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        Slugify(inputs[i%len(inputs)])
    }
}

// Benchmark with memory allocation tracking
func BenchmarkUserDTO_Marshal(b *testing.B) {
    user := &UserDTO{
        ID:    "123e4567-e89b-12d3-a456-426614174000",
        Email: "test@example.com",
        Name:  "Test User",
    }

    b.ReportAllocs()
    b.ResetTimer()

    for i := 0; i < b.N; i++ {
        _, _ = json.Marshal(user)
    }
}

// Sub-benchmarks for comparison
func BenchmarkHashPassword(b *testing.B) {
    password := "SecureP@ssw0rd123"

    costs := []int{10, 12, 14}
    for _, cost := range costs {
        b.Run(fmt.Sprintf("cost=%d", cost), func(b *testing.B) {
            for i := 0; i < b.N; i++ {
                _, _ = bcrypt.GenerateFromPassword([]byte(password), cost)
            }
        })
    }
}
```

## Running Benchmarks

```bash
# Run all benchmarks
go test -bench=. ./...

# Run specific benchmark
go test -bench=BenchmarkUserService_GetByID ./internal/service/

# With memory allocation stats
go test -bench=. -benchmem ./...

# Run benchmarks multiple times
go test -bench=. -count=5 ./...

# Compare benchmarks
go test -bench=. -count=10 ./... > old.txt
# Make changes
go test -bench=. -count=10 ./... > new.txt
benchstat old.txt new.txt

# CPU profile
go test -bench=BenchmarkUserService_GetByID -cpuprofile=cpu.prof ./internal/service/
go tool pprof cpu.prof

# Memory profile
go test -bench=BenchmarkUserService_GetByID -memprofile=mem.prof ./internal/service/
go tool pprof mem.prof
```

## pprof HTTP Endpoint

```go
// cmd/server/main.go
package main

import (
    "net/http"
    _ "net/http/pprof"

    "github.com/gin-gonic/gin"
)

func main() {
    // Start pprof server on separate port (not exposed publicly)
    go func() {
        http.ListenAndServe("localhost:6060", nil)
    }()

    // Main application server
    router := gin.Default()
    // ... setup routes
    router.Run(":8080")
}

// Access profiles:
// http://localhost:6060/debug/pprof/
// http://localhost:6060/debug/pprof/heap
// http://localhost:6060/debug/pprof/goroutine
// http://localhost:6060/debug/pprof/profile?seconds=30
```

## Custom Profiling Middleware

```go
// internal/middleware/profiling.go
package middleware

import (
    "time"

    "github.com/gin-gonic/gin"
    "go.uber.org/zap"
)

func Profiling(logger *zap.Logger) gin.HandlerFunc {
    return func(c *gin.Context) {
        start := time.Now()

        c.Next()

        duration := time.Since(start)

        // Log slow requests
        if duration > 500*time.Millisecond {
            logger.Warn("Slow request",
                zap.String("path", c.Request.URL.Path),
                zap.String("method", c.Request.Method),
                zap.Duration("duration", duration),
                zap.Int("status", c.Writer.Status()),
            )
        }
    }
}

// Detailed timing middleware
func DetailedTiming() gin.HandlerFunc {
    return func(c *gin.Context) {
        timings := make(map[string]time.Duration)
        c.Set("timings", timings)

        start := time.Now()
        c.Next()
        timings["total"] = time.Since(start)

        // Add to response header for debugging
        for name, duration := range timings {
            c.Header("X-Timing-"+name, duration.String())
        }
    }
}

// Usage in handler
func (h *Handler) Get(c *gin.Context) {
    timings := c.MustGet("timings").(map[string]time.Duration)

    dbStart := time.Now()
    data, err := h.repo.Get(ctx, id)
    timings["database"] = time.Since(dbStart)

    if err != nil {
        // handle error
    }

    serializeStart := time.Now()
    response.Success(c, 200, data)
    timings["serialize"] = time.Since(serializeStart)
}
```

## Memory Optimization

```go
// pkg/pool/buffer.go
package pool

import (
    "bytes"
    "sync"
)

// Buffer pool to reduce allocations
var bufferPool = sync.Pool{
    New: func() interface{} {
        return new(bytes.Buffer)
    },
}

func GetBuffer() *bytes.Buffer {
    return bufferPool.Get().(*bytes.Buffer)
}

func PutBuffer(buf *bytes.Buffer) {
    buf.Reset()
    bufferPool.Put(buf)
}

// Usage
func SerializeUser(user *User) ([]byte, error) {
    buf := pool.GetBuffer()
    defer pool.PutBuffer(buf)

    encoder := json.NewEncoder(buf)
    if err := encoder.Encode(user); err != nil {
        return nil, err
    }

    // Make a copy since we're returning the buffer to the pool
    result := make([]byte, buf.Len())
    copy(result, buf.Bytes())

    return result, nil
}
```

## Query Performance

```go
// internal/repository/postgres/query_analyzer.go
package postgres

import (
    "context"
    "time"

    "github.com/jmoiron/sqlx"
    "go.uber.org/zap"
)

type QueryAnalyzer struct {
    db     *sqlx.DB
    logger *zap.Logger
}

func (a *QueryAnalyzer) Analyze(ctx context.Context, query string) {
    // EXPLAIN ANALYZE
    rows, err := a.db.QueryContext(ctx, "EXPLAIN ANALYZE "+query)
    if err != nil {
        a.logger.Error("Failed to analyze query", zap.Error(err))
        return
    }
    defer rows.Close()

    var plan []string
    for rows.Next() {
        var line string
        rows.Scan(&line)
        plan = append(plan, line)
    }

    a.logger.Info("Query plan",
        zap.String("query", query),
        zap.Strings("plan", plan),
    )
}

// Wrapper for timing queries
func (r *userRepository) GetByIDWithTiming(ctx context.Context, id uuid.UUID) (*user.User, time.Duration, error) {
    start := time.Now()
    u, err := r.GetByID(ctx, id)
    duration := time.Since(start)

    if duration > 100*time.Millisecond {
        r.logger.Warn("Slow query",
            zap.String("query", "GetByID"),
            zap.Duration("duration", duration),
        )
    }

    return u, duration, err
}
```

## Trace Integration

```go
// pkg/tracing/tracer.go
package tracing

import (
    "context"

    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/trace"
)

var tracer = otel.Tracer("myproject")

func StartSpan(ctx context.Context, name string) (context.Context, trace.Span) {
    return tracer.Start(ctx, name)
}

// Usage in service
func (s *UserService) GetByID(ctx context.Context, id string) (*user.User, error) {
    ctx, span := tracing.StartSpan(ctx, "UserService.GetByID")
    defer span.End()

    span.SetAttributes(attribute.String("user.id", id))

    u, err := s.repo.GetByID(ctx, uuid.MustParse(id))
    if err != nil {
        span.RecordError(err)
        return nil, err
    }

    return u, nil
}
```

## Makefile Commands

```makefile
# Makefile
.PHONY: bench profile

bench:
	go test -bench=. -benchmem ./...

bench-compare:
	go test -bench=. -count=10 ./... > bench-old.txt
	@echo "Make your changes, then run: make bench-compare-new"

bench-compare-new:
	go test -bench=. -count=10 ./... > bench-new.txt
	benchstat bench-old.txt bench-new.txt

profile-cpu:
	go test -bench=. -cpuprofile=cpu.prof ./...
	go tool pprof -http=:8080 cpu.prof

profile-mem:
	go test -bench=. -memprofile=mem.prof ./...
	go tool pprof -http=:8080 mem.prof

profile-trace:
	go test -bench=. -trace=trace.out ./...
	go tool trace trace.out
```

## Best Practices

1. **Benchmark Representative Cases**: Test realistic scenarios
2. **Reset Timer**: Use `b.ResetTimer()` after setup
3. **Report Allocations**: Use `b.ReportAllocs()` for memory tracking
4. **Run Multiple Times**: Use `-count` flag for statistical significance
5. **Profile in Production**: Use pprof endpoints carefully
6. **Object Pools**: Use sync.Pool for frequent allocations
