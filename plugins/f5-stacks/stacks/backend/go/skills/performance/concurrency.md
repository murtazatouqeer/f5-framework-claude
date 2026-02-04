# Concurrency Patterns

Implementing concurrency patterns in Go applications.

## Worker Pool Pattern

```go
// pkg/worker/pool.go
package worker

import (
    "context"
    "sync"
)

type Job func(ctx context.Context) error

type Pool struct {
    workers    int
    jobs       chan Job
    results    chan error
    wg         sync.WaitGroup
}

func NewPool(workers int, queueSize int) *Pool {
    return &Pool{
        workers: workers,
        jobs:    make(chan Job, queueSize),
        results: make(chan error, queueSize),
    }
}

func (p *Pool) Start(ctx context.Context) {
    for i := 0; i < p.workers; i++ {
        p.wg.Add(1)
        go p.worker(ctx)
    }
}

func (p *Pool) worker(ctx context.Context) {
    defer p.wg.Done()

    for {
        select {
        case <-ctx.Done():
            return
        case job, ok := <-p.jobs:
            if !ok {
                return
            }
            err := job(ctx)
            p.results <- err
        }
    }
}

func (p *Pool) Submit(job Job) {
    p.jobs <- job
}

func (p *Pool) Stop() {
    close(p.jobs)
    p.wg.Wait()
    close(p.results)
}

func (p *Pool) Results() <-chan error {
    return p.results
}

// Usage
func ProcessImages(ctx context.Context, images []Image) error {
    pool := worker.NewPool(5, len(images))
    pool.Start(ctx)

    for _, img := range images {
        img := img // capture
        pool.Submit(func(ctx context.Context) error {
            return processImage(ctx, img)
        })
    }

    go func() {
        pool.Stop()
    }()

    for err := range pool.Results() {
        if err != nil {
            return err
        }
    }
    return nil
}
```

## Fan-Out/Fan-In Pattern

```go
// pkg/concurrent/fanout.go
package concurrent

import (
    "context"
    "sync"
)

// FanOut distributes work across multiple workers
func FanOut[T any, R any](
    ctx context.Context,
    items []T,
    workers int,
    processor func(context.Context, T) (R, error),
) ([]R, error) {
    itemCh := make(chan T, len(items))
    resultCh := make(chan result[R], len(items))

    // Start workers
    var wg sync.WaitGroup
    for i := 0; i < workers; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            for item := range itemCh {
                select {
                case <-ctx.Done():
                    return
                default:
                    r, err := processor(ctx, item)
                    resultCh <- result[R]{value: r, err: err}
                }
            }
        }()
    }

    // Send items
    go func() {
        for _, item := range items {
            itemCh <- item
        }
        close(itemCh)
    }()

    // Wait and close results
    go func() {
        wg.Wait()
        close(resultCh)
    }()

    // Collect results
    var results []R
    for r := range resultCh {
        if r.err != nil {
            return nil, r.err
        }
        results = append(results, r.value)
    }

    return results, nil
}

type result[R any] struct {
    value R
    err   error
}

// Usage
func FetchAllUsers(ctx context.Context, userIDs []string) ([]*User, error) {
    return concurrent.FanOut(ctx, userIDs, 10, func(ctx context.Context, id string) (*User, error) {
        return userRepo.GetByID(ctx, id)
    })
}
```

## Semaphore Pattern

```go
// pkg/concurrent/semaphore.go
package concurrent

import (
    "context"
)

type Semaphore struct {
    sem chan struct{}
}

func NewSemaphore(limit int) *Semaphore {
    return &Semaphore{
        sem: make(chan struct{}, limit),
    }
}

func (s *Semaphore) Acquire(ctx context.Context) error {
    select {
    case s.sem <- struct{}{}:
        return nil
    case <-ctx.Done():
        return ctx.Err()
    }
}

func (s *Semaphore) Release() {
    <-s.sem
}

func (s *Semaphore) TryAcquire() bool {
    select {
    case s.sem <- struct{}{}:
        return true
    default:
        return false
    }
}

// Usage: Rate limit API calls
func (c *APIClient) FetchMany(ctx context.Context, ids []string) ([]*Resource, error) {
    sem := concurrent.NewSemaphore(10) // Max 10 concurrent requests
    var results []*Resource
    var mu sync.Mutex
    var wg sync.WaitGroup
    errCh := make(chan error, 1)

    for _, id := range ids {
        wg.Add(1)
        go func(id string) {
            defer wg.Done()

            if err := sem.Acquire(ctx); err != nil {
                select {
                case errCh <- err:
                default:
                }
                return
            }
            defer sem.Release()

            resource, err := c.Fetch(ctx, id)
            if err != nil {
                select {
                case errCh <- err:
                default:
                }
                return
            }

            mu.Lock()
            results = append(results, resource)
            mu.Unlock()
        }(id)
    }

    wg.Wait()

    select {
    case err := <-errCh:
        return nil, err
    default:
        return results, nil
    }
}
```

## Pipeline Pattern

```go
// pkg/pipeline/pipeline.go
package pipeline

import (
    "context"
)

type Stage[I, O any] func(ctx context.Context, in <-chan I) <-chan O

// Pipeline connects multiple stages
func Connect[T any](ctx context.Context, source <-chan T, stages ...Stage[T, T]) <-chan T {
    current := source
    for _, stage := range stages {
        current = stage(ctx, current)
    }
    return current
}

// Generator creates a source channel from items
func Generator[T any](ctx context.Context, items ...T) <-chan T {
    out := make(chan T)
    go func() {
        defer close(out)
        for _, item := range items {
            select {
            case <-ctx.Done():
                return
            case out <- item:
            }
        }
    }()
    return out
}

// Map transforms each item
func Map[I, O any](fn func(I) O) Stage[I, O] {
    return func(ctx context.Context, in <-chan I) <-chan O {
        out := make(chan O)
        go func() {
            defer close(out)
            for item := range in {
                select {
                case <-ctx.Done():
                    return
                case out <- fn(item):
                }
            }
        }()
        return out
    }
}

// Filter removes items that don't match predicate
func Filter[T any](predicate func(T) bool) Stage[T, T] {
    return func(ctx context.Context, in <-chan T) <-chan T {
        out := make(chan T)
        go func() {
            defer close(out)
            for item := range in {
                if predicate(item) {
                    select {
                    case <-ctx.Done():
                        return
                    case out <- item:
                    }
                }
            }
        }()
        return out
    }
}

// Usage
func ProcessOrders(ctx context.Context, orders []Order) <-chan ProcessedOrder {
    source := pipeline.Generator(ctx, orders...)

    validated := pipeline.Map(func(o Order) Order {
        o.Validated = true
        return o
    })(ctx, source)

    filtered := pipeline.Filter(func(o Order) bool {
        return o.Amount > 0
    })(ctx, validated)

    processed := pipeline.Map(func(o Order) ProcessedOrder {
        return ProcessedOrder{Order: o, ProcessedAt: time.Now()}
    })(ctx, filtered)

    return processed
}
```

## Context with Timeout

```go
// pkg/concurrent/timeout.go
package concurrent

import (
    "context"
    "time"
)

// WithTimeout runs function with timeout
func WithTimeout[T any](ctx context.Context, timeout time.Duration, fn func(context.Context) (T, error)) (T, error) {
    ctx, cancel := context.WithTimeout(ctx, timeout)
    defer cancel()

    resultCh := make(chan T, 1)
    errCh := make(chan error, 1)

    go func() {
        result, err := fn(ctx)
        if err != nil {
            errCh <- err
            return
        }
        resultCh <- result
    }()

    select {
    case <-ctx.Done():
        var zero T
        return zero, ctx.Err()
    case err := <-errCh:
        var zero T
        return zero, err
    case result := <-resultCh:
        return result, nil
    }
}

// Usage
func FetchWithTimeout(ctx context.Context, url string) (*Response, error) {
    return concurrent.WithTimeout(ctx, 5*time.Second, func(ctx context.Context) (*Response, error) {
        return httpClient.Get(ctx, url)
    })
}
```

## Graceful Shutdown

```go
// cmd/server/main.go
package main

import (
    "context"
    "net/http"
    "os"
    "os/signal"
    "syscall"
    "time"

    "go.uber.org/zap"
)

func main() {
    logger, _ := zap.NewProduction()
    defer logger.Sync()

    server := &http.Server{
        Addr:    ":8080",
        Handler: setupRouter(),
    }

    // Start server in goroutine
    go func() {
        logger.Info("Starting server", zap.String("addr", server.Addr))
        if err := server.ListenAndServe(); err != http.ErrServerClosed {
            logger.Fatal("Server error", zap.Error(err))
        }
    }()

    // Wait for interrupt signal
    quit := make(chan os.Signal, 1)
    signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
    <-quit

    logger.Info("Shutting down server...")

    // Graceful shutdown with timeout
    ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()

    if err := server.Shutdown(ctx); err != nil {
        logger.Error("Server forced to shutdown", zap.Error(err))
    }

    logger.Info("Server exited")
}
```

## Best Practices

1. **Use Contexts**: Pass context for cancellation
2. **Avoid Goroutine Leaks**: Always ensure goroutines can exit
3. **Buffer Channels**: Use buffered channels when appropriate
4. **Limit Concurrency**: Use semaphores or worker pools
5. **Handle Panics**: Recover panics in goroutines
6. **Graceful Shutdown**: Implement proper shutdown handling
