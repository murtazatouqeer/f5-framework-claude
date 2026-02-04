# Caching Patterns

Implementing caching strategies in Go applications.

## In-Memory Cache with sync.Map

```go
// pkg/cache/memory.go
package cache

import (
    "sync"
    "time"
)

type item struct {
    value     interface{}
    expiresAt time.Time
}

type MemoryCache struct {
    items sync.Map
    ttl   time.Duration
}

func NewMemoryCache(ttl time.Duration) *MemoryCache {
    cache := &MemoryCache{ttl: ttl}
    go cache.cleanup()
    return cache
}

func (c *MemoryCache) Get(key string) (interface{}, bool) {
    val, ok := c.items.Load(key)
    if !ok {
        return nil, false
    }

    item := val.(*item)
    if time.Now().After(item.expiresAt) {
        c.items.Delete(key)
        return nil, false
    }

    return item.value, true
}

func (c *MemoryCache) Set(key string, value interface{}) {
    c.SetWithTTL(key, value, c.ttl)
}

func (c *MemoryCache) SetWithTTL(key string, value interface{}, ttl time.Duration) {
    c.items.Store(key, &item{
        value:     value,
        expiresAt: time.Now().Add(ttl),
    })
}

func (c *MemoryCache) Delete(key string) {
    c.items.Delete(key)
}

func (c *MemoryCache) cleanup() {
    ticker := time.NewTicker(time.Minute)
    defer ticker.Stop()

    for range ticker.C {
        now := time.Now()
        c.items.Range(func(key, val interface{}) bool {
            item := val.(*item)
            if now.After(item.expiresAt) {
                c.items.Delete(key)
            }
            return true
        })
    }
}
```

## Redis Cache Implementation

```go
// pkg/cache/redis.go
package cache

import (
    "context"
    "encoding/json"
    "errors"
    "time"

    "github.com/redis/go-redis/v9"
)

var ErrCacheMiss = errors.New("cache miss")

type RedisCache struct {
    client *redis.Client
    prefix string
}

func NewRedisCache(client *redis.Client, prefix string) *RedisCache {
    return &RedisCache{
        client: client,
        prefix: prefix,
    }
}

func (c *RedisCache) key(k string) string {
    return c.prefix + ":" + k
}

func (c *RedisCache) Get(ctx context.Context, key string) (string, error) {
    val, err := c.client.Get(ctx, c.key(key)).Result()
    if err != nil {
        if errors.Is(err, redis.Nil) {
            return "", ErrCacheMiss
        }
        return "", err
    }
    return val, nil
}

func (c *RedisCache) GetJSON(ctx context.Context, key string, dest interface{}) error {
    val, err := c.Get(ctx, key)
    if err != nil {
        return err
    }
    return json.Unmarshal([]byte(val), dest)
}

func (c *RedisCache) Set(ctx context.Context, key, value string, ttl time.Duration) error {
    return c.client.Set(ctx, c.key(key), value, ttl).Err()
}

func (c *RedisCache) SetJSON(ctx context.Context, key string, value interface{}, ttl time.Duration) error {
    data, err := json.Marshal(value)
    if err != nil {
        return err
    }
    return c.Set(ctx, key, string(data), ttl)
}

func (c *RedisCache) Delete(ctx context.Context, key string) error {
    return c.client.Del(ctx, c.key(key)).Err()
}

func (c *RedisCache) DeletePattern(ctx context.Context, pattern string) error {
    iter := c.client.Scan(ctx, 0, c.key(pattern), 100).Iterator()
    var keys []string
    for iter.Next(ctx) {
        keys = append(keys, iter.Val())
    }
    if err := iter.Err(); err != nil {
        return err
    }
    if len(keys) > 0 {
        return c.client.Del(ctx, keys...).Err()
    }
    return nil
}

func (c *RedisCache) Exists(ctx context.Context, key string) (bool, error) {
    n, err := c.client.Exists(ctx, c.key(key)).Result()
    return n > 0, err
}
```

## Cache-Aside Pattern

```go
// internal/service/user_service.go
package service

import (
    "context"
    "fmt"
    "time"

    "myproject/internal/domain/user"
    "myproject/pkg/cache"
)

type UserService struct {
    repo  user.Repository
    cache *cache.RedisCache
    ttl   time.Duration
}

func NewUserService(repo user.Repository, cache *cache.RedisCache) *UserService {
    return &UserService{
        repo:  repo,
        cache: cache,
        ttl:   15 * time.Minute,
    }
}

func (s *UserService) GetByID(ctx context.Context, id string) (*user.User, error) {
    cacheKey := fmt.Sprintf("user:%s", id)

    // Try cache first
    var u user.User
    err := s.cache.GetJSON(ctx, cacheKey, &u)
    if err == nil {
        return &u, nil
    }

    // Cache miss - get from database
    userEntity, err := s.repo.GetByID(ctx, uuid.MustParse(id))
    if err != nil {
        return nil, err
    }

    // Store in cache
    go func() {
        ctx, cancel := context.WithTimeout(context.Background(), time.Second)
        defer cancel()
        s.cache.SetJSON(ctx, cacheKey, userEntity, s.ttl)
    }()

    return userEntity, nil
}

func (s *UserService) Update(ctx context.Context, id string, input UpdateUserInput) (*user.User, error) {
    // Update in database
    u, err := s.repo.Update(ctx, uuid.MustParse(id), input)
    if err != nil {
        return nil, err
    }

    // Invalidate cache
    cacheKey := fmt.Sprintf("user:%s", id)
    s.cache.Delete(ctx, cacheKey)

    return u, nil
}
```

## Write-Through Cache

```go
// pkg/cache/writethrough.go
package cache

import (
    "context"
    "time"
)

type WriteThroughCache[T any] struct {
    cache  *RedisCache
    loader func(ctx context.Context, key string) (T, error)
    saver  func(ctx context.Context, key string, value T) error
    ttl    time.Duration
}

func NewWriteThroughCache[T any](
    cache *RedisCache,
    loader func(ctx context.Context, key string) (T, error),
    saver func(ctx context.Context, key string, value T) error,
    ttl time.Duration,
) *WriteThroughCache[T] {
    return &WriteThroughCache[T]{
        cache:  cache,
        loader: loader,
        saver:  saver,
        ttl:    ttl,
    }
}

func (c *WriteThroughCache[T]) Get(ctx context.Context, key string) (T, error) {
    var value T

    // Try cache
    if err := c.cache.GetJSON(ctx, key, &value); err == nil {
        return value, nil
    }

    // Load from source
    value, err := c.loader(ctx, key)
    if err != nil {
        return value, err
    }

    // Update cache
    c.cache.SetJSON(ctx, key, value, c.ttl)

    return value, nil
}

func (c *WriteThroughCache[T]) Set(ctx context.Context, key string, value T) error {
    // Write to source first
    if err := c.saver(ctx, key, value); err != nil {
        return err
    }

    // Update cache
    return c.cache.SetJSON(ctx, key, value, c.ttl)
}
```

## Cache with Stampede Protection

```go
// pkg/cache/singleflight.go
package cache

import (
    "context"
    "time"

    "golang.org/x/sync/singleflight"
)

type SingleFlightCache[T any] struct {
    cache  *RedisCache
    loader func(ctx context.Context, key string) (T, error)
    group  singleflight.Group
    ttl    time.Duration
}

func NewSingleFlightCache[T any](
    cache *RedisCache,
    loader func(ctx context.Context, key string) (T, error),
    ttl time.Duration,
) *SingleFlightCache[T] {
    return &SingleFlightCache[T]{
        cache:  cache,
        loader: loader,
        ttl:    ttl,
    }
}

func (c *SingleFlightCache[T]) Get(ctx context.Context, key string) (T, error) {
    var value T

    // Try cache first
    if err := c.cache.GetJSON(ctx, key, &value); err == nil {
        return value, nil
    }

    // Use singleflight to prevent stampede
    result, err, _ := c.group.Do(key, func() (interface{}, error) {
        // Double-check cache (another goroutine might have populated it)
        if err := c.cache.GetJSON(ctx, key, &value); err == nil {
            return value, nil
        }

        // Load from source
        loaded, err := c.loader(ctx, key)
        if err != nil {
            return nil, err
        }

        // Update cache
        c.cache.SetJSON(ctx, key, loaded, c.ttl)

        return loaded, nil
    })

    if err != nil {
        return value, err
    }

    return result.(T), nil
}
```

## LRU Cache

```go
// pkg/cache/lru.go
package cache

import (
    "container/list"
    "sync"
)

type LRUCache struct {
    capacity int
    cache    map[string]*list.Element
    list     *list.List
    mu       sync.RWMutex
}

type entry struct {
    key   string
    value interface{}
}

func NewLRUCache(capacity int) *LRUCache {
    return &LRUCache{
        capacity: capacity,
        cache:    make(map[string]*list.Element),
        list:     list.New(),
    }
}

func (c *LRUCache) Get(key string) (interface{}, bool) {
    c.mu.Lock()
    defer c.mu.Unlock()

    if elem, ok := c.cache[key]; ok {
        c.list.MoveToFront(elem)
        return elem.Value.(*entry).value, true
    }
    return nil, false
}

func (c *LRUCache) Set(key string, value interface{}) {
    c.mu.Lock()
    defer c.mu.Unlock()

    if elem, ok := c.cache[key]; ok {
        c.list.MoveToFront(elem)
        elem.Value.(*entry).value = value
        return
    }

    // Add new entry
    elem := c.list.PushFront(&entry{key: key, value: value})
    c.cache[key] = elem

    // Evict if over capacity
    if c.list.Len() > c.capacity {
        oldest := c.list.Back()
        if oldest != nil {
            c.list.Remove(oldest)
            delete(c.cache, oldest.Value.(*entry).key)
        }
    }
}

func (c *LRUCache) Delete(key string) {
    c.mu.Lock()
    defer c.mu.Unlock()

    if elem, ok := c.cache[key]; ok {
        c.list.Remove(elem)
        delete(c.cache, key)
    }
}
```

## Best Practices

1. **TTL Strategy**: Set appropriate TTLs based on data volatility
2. **Cache Invalidation**: Invalidate on writes, not just expire
3. **Stampede Protection**: Use singleflight for expensive operations
4. **Graceful Degradation**: Handle cache failures gracefully
5. **Monitoring**: Track hit rates and miss rates
6. **Serialization**: Use efficient serialization (JSON, msgpack)
