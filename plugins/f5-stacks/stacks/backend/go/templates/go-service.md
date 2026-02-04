# Go Service Template

Production-ready service layer template for Go applications following clean architecture.

## Service Interface Definition

```go
// internal/domain/{{resource}}.go
package domain

import (
    "context"
    "time"
)

// {{Resource}} represents the {{resource}} domain entity
type {{Resource}} struct {
    ID          string     `json:"id" db:"id"`
    // Add domain fields
    CreatedAt   time.Time  `json:"created_at" db:"created_at"`
    UpdatedAt   time.Time  `json:"updated_at" db:"updated_at"`
    DeletedAt   *time.Time `json:"deleted_at,omitempty" db:"deleted_at"`
}

// Create{{Resource}}Input represents the input for creating a {{resource}}
type Create{{Resource}}Input struct {
    // Add required fields with validation tags
    Name string `json:"name" validate:"required,min=2,max=255"`
}

// Update{{Resource}}Input represents the input for updating a {{resource}}
type Update{{Resource}}Input struct {
    Name *string `json:"name,omitempty" validate:"omitempty,min=2,max=255"`
}

// {{Resource}}Filter represents filter options for listing
type {{Resource}}Filter struct {
    Search *string
    Status *string
    Limit  int
    Offset int
    SortBy string
    Order  string
}

// {{Resource}}Service defines the business logic interface
type {{Resource}}Service interface {
    Create(ctx context.Context, input Create{{Resource}}Input) (*{{Resource}}, error)
    GetByID(ctx context.Context, id string) (*{{Resource}}, error)
    List(ctx context.Context, filter {{Resource}}Filter) ([]*{{Resource}}, int64, error)
    Update(ctx context.Context, id string, input Update{{Resource}}Input) (*{{Resource}}, error)
    Delete(ctx context.Context, id string) error
}

// {{Resource}}Repository defines the data access interface
type {{Resource}}Repository interface {
    Create(ctx context.Context, entity *{{Resource}}) error
    GetByID(ctx context.Context, id string) (*{{Resource}}, error)
    GetByUniqueField(ctx context.Context, field string) (*{{Resource}}, error)
    List(ctx context.Context, filter {{Resource}}Filter) ([]*{{Resource}}, int64, error)
    Update(ctx context.Context, entity *{{Resource}}) error
    Delete(ctx context.Context, id string) error
}
```

## Service Implementation

```go
// internal/service/{{resource}}.go
package service

import (
    "context"
    "errors"
    "fmt"
    "time"

    "github.com/google/uuid"
    "go.uber.org/zap"

    "{{module}}/internal/domain"
)

type {{resource}}Service struct {
    repo   domain.{{Resource}}Repository
    logger *zap.Logger
}

// New{{Resource}}Service creates a new {{resource}} service
func New{{Resource}}Service(repo domain.{{Resource}}Repository, logger *zap.Logger) *{{resource}}Service {
    return &{{resource}}Service{
        repo:   repo,
        logger: logger.Named("{{resource}}_service"),
    }
}

// Create creates a new {{resource}}
func (s *{{resource}}Service) Create(ctx context.Context, input domain.Create{{Resource}}Input) (*domain.{{Resource}}, error) {
    s.logger.Info("creating {{resource}}", zap.String("name", input.Name))

    // Check for duplicates
    existing, err := s.repo.GetByUniqueField(ctx, input.Name)
    if err != nil && !errors.Is(err, domain.ErrNotFound) {
        return nil, fmt.Errorf("checking existing {{resource}}: %w", err)
    }
    if existing != nil {
        return nil, domain.ErrAlreadyExists
    }

    now := time.Now()
    entity := &domain.{{Resource}}{
        ID:        uuid.New().String(),
        Name:      input.Name,
        CreatedAt: now,
        UpdatedAt: now,
    }

    if err := s.repo.Create(ctx, entity); err != nil {
        s.logger.Error("failed to create {{resource}}", zap.Error(err))
        return nil, fmt.Errorf("creating {{resource}}: %w", err)
    }

    s.logger.Info("{{resource}} created", zap.String("id", entity.ID))
    return entity, nil
}

// GetByID retrieves a {{resource}} by ID
func (s *{{resource}}Service) GetByID(ctx context.Context, id string) (*domain.{{Resource}}, error) {
    s.logger.Debug("getting {{resource}}", zap.String("id", id))

    entity, err := s.repo.GetByID(ctx, id)
    if err != nil {
        if errors.Is(err, domain.ErrNotFound) {
            return nil, err
        }
        return nil, fmt.Errorf("getting {{resource}}: %w", err)
    }

    return entity, nil
}

// List retrieves {{resource}}s with filtering and pagination
func (s *{{resource}}Service) List(ctx context.Context, filter domain.{{Resource}}Filter) ([]*domain.{{Resource}}, int64, error) {
    s.logger.Debug("listing {{resource}}s",
        zap.Int("limit", filter.Limit),
        zap.Int("offset", filter.Offset),
    )

    // Validate and set defaults
    if filter.Limit <= 0 || filter.Limit > 100 {
        filter.Limit = 10
    }
    if filter.Offset < 0 {
        filter.Offset = 0
    }
    if filter.SortBy == "" {
        filter.SortBy = "created_at"
    }
    if filter.Order == "" {
        filter.Order = "DESC"
    }

    entities, total, err := s.repo.List(ctx, filter)
    if err != nil {
        return nil, 0, fmt.Errorf("listing {{resource}}s: %w", err)
    }

    return entities, total, nil
}

// Update updates an existing {{resource}}
func (s *{{resource}}Service) Update(ctx context.Context, id string, input domain.Update{{Resource}}Input) (*domain.{{Resource}}, error) {
    s.logger.Info("updating {{resource}}", zap.String("id", id))

    entity, err := s.repo.GetByID(ctx, id)
    if err != nil {
        return nil, fmt.Errorf("getting {{resource}}: %w", err)
    }

    // Apply updates
    if input.Name != nil {
        entity.Name = *input.Name
    }
    entity.UpdatedAt = time.Now()

    if err := s.repo.Update(ctx, entity); err != nil {
        s.logger.Error("failed to update {{resource}}", zap.Error(err))
        return nil, fmt.Errorf("updating {{resource}}: %w", err)
    }

    s.logger.Info("{{resource}} updated", zap.String("id", id))
    return entity, nil
}

// Delete soft-deletes a {{resource}}
func (s *{{resource}}Service) Delete(ctx context.Context, id string) error {
    s.logger.Info("deleting {{resource}}", zap.String("id", id))

    // Verify existence
    _, err := s.repo.GetByID(ctx, id)
    if err != nil {
        return fmt.Errorf("getting {{resource}}: %w", err)
    }

    if err := s.repo.Delete(ctx, id); err != nil {
        s.logger.Error("failed to delete {{resource}}", zap.Error(err))
        return fmt.Errorf("deleting {{resource}}: %w", err)
    }

    s.logger.Info("{{resource}} deleted", zap.String("id", id))
    return nil
}
```

## Service with Transaction Support

```go
// internal/service/{{resource}}_transactional.go
package service

import (
    "context"
    "database/sql"
    "fmt"
)

type Transactor interface {
    WithTransaction(ctx context.Context, fn func(ctx context.Context) error) error
}

type transactionalService struct {
    *{{resource}}Service
    tx Transactor
}

func New{{Resource}}TransactionalService(
    repo domain.{{Resource}}Repository,
    tx Transactor,
    logger *zap.Logger,
) *transactionalService {
    return &transactionalService{
        {{resource}}Service: New{{Resource}}Service(repo, logger),
        tx:                  tx,
    }
}

func (s *transactionalService) CreateWithRelations(
    ctx context.Context,
    input domain.Create{{Resource}}Input,
    relatedInput domain.CreateRelatedInput,
) (*domain.{{Resource}}, error) {
    var result *domain.{{Resource}}

    err := s.tx.WithTransaction(ctx, func(txCtx context.Context) error {
        var err error
        result, err = s.Create(txCtx, input)
        if err != nil {
            return fmt.Errorf("creating {{resource}}: %w", err)
        }

        // Create related entities within same transaction
        // relatedService.Create(txCtx, relatedInput)

        return nil
    })

    if err != nil {
        return nil, err
    }

    return result, nil
}
```

## Service with Caching

```go
// internal/service/{{resource}}_cached.go
package service

import (
    "context"
    "encoding/json"
    "fmt"
    "time"

    "github.com/redis/go-redis/v9"
)

type cachedService struct {
    *{{resource}}Service
    cache    *redis.Client
    cacheTTL time.Duration
}

func New{{Resource}}CachedService(
    repo domain.{{Resource}}Repository,
    cache *redis.Client,
    logger *zap.Logger,
) *cachedService {
    return &cachedService{
        {{resource}}Service: New{{Resource}}Service(repo, logger),
        cache:               cache,
        cacheTTL:            5 * time.Minute,
    }
}

func (s *cachedService) cacheKey(id string) string {
    return fmt.Sprintf("{{resource}}:%s", id)
}

func (s *cachedService) GetByID(ctx context.Context, id string) (*domain.{{Resource}}, error) {
    // Try cache first
    key := s.cacheKey(id)
    cached, err := s.cache.Get(ctx, key).Result()
    if err == nil {
        var entity domain.{{Resource}}
        if json.Unmarshal([]byte(cached), &entity) == nil {
            return &entity, nil
        }
    }

    // Fetch from database
    entity, err := s.{{resource}}Service.GetByID(ctx, id)
    if err != nil {
        return nil, err
    }

    // Store in cache
    if data, err := json.Marshal(entity); err == nil {
        s.cache.Set(ctx, key, data, s.cacheTTL)
    }

    return entity, nil
}

func (s *cachedService) Update(ctx context.Context, id string, input domain.Update{{Resource}}Input) (*domain.{{Resource}}, error) {
    entity, err := s.{{resource}}Service.Update(ctx, id, input)
    if err != nil {
        return nil, err
    }

    // Invalidate cache
    s.cache.Del(ctx, s.cacheKey(id))

    return entity, nil
}

func (s *cachedService) Delete(ctx context.Context, id string) error {
    if err := s.{{resource}}Service.Delete(ctx, id); err != nil {
        return err
    }

    // Invalidate cache
    s.cache.Del(ctx, s.cacheKey(id))

    return nil
}
```

## Event-Driven Service

```go
// internal/service/{{resource}}_events.go
package service

import (
    "context"
    "encoding/json"
    "time"
)

type EventPublisher interface {
    Publish(ctx context.Context, topic string, event interface{}) error
}

type {{Resource}}Event struct {
    Type      string          `json:"type"`
    ID        string          `json:"id"`
    Timestamp time.Time       `json:"timestamp"`
    Data      json.RawMessage `json:"data,omitempty"`
}

type eventDrivenService struct {
    *{{resource}}Service
    publisher EventPublisher
}

func New{{Resource}}EventDrivenService(
    repo domain.{{Resource}}Repository,
    publisher EventPublisher,
    logger *zap.Logger,
) *eventDrivenService {
    return &eventDrivenService{
        {{resource}}Service: New{{Resource}}Service(repo, logger),
        publisher:           publisher,
    }
}

func (s *eventDrivenService) Create(ctx context.Context, input domain.Create{{Resource}}Input) (*domain.{{Resource}}, error) {
    entity, err := s.{{resource}}Service.Create(ctx, input)
    if err != nil {
        return nil, err
    }

    // Publish event
    data, _ := json.Marshal(entity)
    event := {{Resource}}Event{
        Type:      "{{resource}}.created",
        ID:        entity.ID,
        Timestamp: time.Now(),
        Data:      data,
    }
    s.publisher.Publish(ctx, "{{resource}}.events", event)

    return entity, nil
}

func (s *eventDrivenService) Update(ctx context.Context, id string, input domain.Update{{Resource}}Input) (*domain.{{Resource}}, error) {
    entity, err := s.{{resource}}Service.Update(ctx, id, input)
    if err != nil {
        return nil, err
    }

    // Publish event
    data, _ := json.Marshal(entity)
    event := {{Resource}}Event{
        Type:      "{{resource}}.updated",
        ID:        entity.ID,
        Timestamp: time.Now(),
        Data:      data,
    }
    s.publisher.Publish(ctx, "{{resource}}.events", event)

    return entity, nil
}

func (s *eventDrivenService) Delete(ctx context.Context, id string) error {
    if err := s.{{resource}}Service.Delete(ctx, id); err != nil {
        return err
    }

    // Publish event
    event := {{Resource}}Event{
        Type:      "{{resource}}.deleted",
        ID:        id,
        Timestamp: time.Now(),
    }
    s.publisher.Publish(ctx, "{{resource}}.events", event)

    return nil
}
```

## Service Testing

```go
// internal/service/{{resource}}_test.go
package service_test

import (
    "context"
    "testing"
    "time"

    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/mock"
    "github.com/stretchr/testify/require"
    "go.uber.org/zap"

    "{{module}}/internal/domain"
    "{{module}}/internal/service"
)

type Mock{{Resource}}Repository struct {
    mock.Mock
}

func (m *Mock{{Resource}}Repository) Create(ctx context.Context, entity *domain.{{Resource}}) error {
    args := m.Called(ctx, entity)
    return args.Error(0)
}

func (m *Mock{{Resource}}Repository) GetByID(ctx context.Context, id string) (*domain.{{Resource}}, error) {
    args := m.Called(ctx, id)
    if args.Get(0) == nil {
        return nil, args.Error(1)
    }
    return args.Get(0).(*domain.{{Resource}}), args.Error(1)
}

func (m *Mock{{Resource}}Repository) GetByUniqueField(ctx context.Context, field string) (*domain.{{Resource}}, error) {
    args := m.Called(ctx, field)
    if args.Get(0) == nil {
        return nil, args.Error(1)
    }
    return args.Get(0).(*domain.{{Resource}}), args.Error(1)
}

func (m *Mock{{Resource}}Repository) List(ctx context.Context, filter domain.{{Resource}}Filter) ([]*domain.{{Resource}}, int64, error) {
    args := m.Called(ctx, filter)
    return args.Get(0).([]*domain.{{Resource}}), args.Get(1).(int64), args.Error(2)
}

func (m *Mock{{Resource}}Repository) Update(ctx context.Context, entity *domain.{{Resource}}) error {
    args := m.Called(ctx, entity)
    return args.Error(0)
}

func (m *Mock{{Resource}}Repository) Delete(ctx context.Context, id string) error {
    args := m.Called(ctx, id)
    return args.Error(0)
}

func TestCreate{{Resource}}(t *testing.T) {
    logger := zap.NewNop()
    repo := new(Mock{{Resource}}Repository)
    svc := service.New{{Resource}}Service(repo, logger)

    ctx := context.Background()
    input := domain.Create{{Resource}}Input{Name: "test"}

    repo.On("GetByUniqueField", ctx, input.Name).Return(nil, domain.ErrNotFound)
    repo.On("Create", ctx, mock.AnythingOfType("*domain.{{Resource}}")).Return(nil)

    result, err := svc.Create(ctx, input)

    require.NoError(t, err)
    assert.NotEmpty(t, result.ID)
    assert.Equal(t, input.Name, result.Name)
    repo.AssertExpectations(t)
}

func TestCreate{{Resource}}_AlreadyExists(t *testing.T) {
    logger := zap.NewNop()
    repo := new(Mock{{Resource}}Repository)
    svc := service.New{{Resource}}Service(repo, logger)

    ctx := context.Background()
    input := domain.Create{{Resource}}Input{Name: "existing"}
    existing := &domain.{{Resource}}{ID: "123", Name: "existing"}

    repo.On("GetByUniqueField", ctx, input.Name).Return(existing, nil)

    result, err := svc.Create(ctx, input)

    assert.Error(t, err)
    assert.Nil(t, result)
    assert.ErrorIs(t, err, domain.ErrAlreadyExists)
}

func TestGetByID_Success(t *testing.T) {
    logger := zap.NewNop()
    repo := new(Mock{{Resource}}Repository)
    svc := service.New{{Resource}}Service(repo, logger)

    ctx := context.Background()
    id := "test-id"
    expected := &domain.{{Resource}}{
        ID:        id,
        Name:      "test",
        CreatedAt: time.Now(),
    }

    repo.On("GetByID", ctx, id).Return(expected, nil)

    result, err := svc.GetByID(ctx, id)

    require.NoError(t, err)
    assert.Equal(t, expected, result)
}

func TestGetByID_NotFound(t *testing.T) {
    logger := zap.NewNop()
    repo := new(Mock{{Resource}}Repository)
    svc := service.New{{Resource}}Service(repo, logger)

    ctx := context.Background()
    id := "nonexistent"

    repo.On("GetByID", ctx, id).Return(nil, domain.ErrNotFound)

    result, err := svc.GetByID(ctx, id)

    assert.Error(t, err)
    assert.Nil(t, result)
    assert.ErrorIs(t, err, domain.ErrNotFound)
}

func TestList{{Resource}}s(t *testing.T) {
    logger := zap.NewNop()
    repo := new(Mock{{Resource}}Repository)
    svc := service.New{{Resource}}Service(repo, logger)

    ctx := context.Background()
    filter := domain.{{Resource}}Filter{Limit: 10, Offset: 0}
    expected := []*domain.{{Resource}}{
        {ID: "1", Name: "first"},
        {ID: "2", Name: "second"},
    }

    repo.On("List", ctx, mock.AnythingOfType("domain.{{Resource}}Filter")).Return(expected, int64(2), nil)

    results, total, err := svc.List(ctx, filter)

    require.NoError(t, err)
    assert.Len(t, results, 2)
    assert.Equal(t, int64(2), total)
}

func TestUpdate{{Resource}}(t *testing.T) {
    logger := zap.NewNop()
    repo := new(Mock{{Resource}}Repository)
    svc := service.New{{Resource}}Service(repo, logger)

    ctx := context.Background()
    id := "test-id"
    newName := "updated"
    input := domain.Update{{Resource}}Input{Name: &newName}
    existing := &domain.{{Resource}}{ID: id, Name: "original", CreatedAt: time.Now()}

    repo.On("GetByID", ctx, id).Return(existing, nil)
    repo.On("Update", ctx, mock.AnythingOfType("*domain.{{Resource}}")).Return(nil)

    result, err := svc.Update(ctx, id, input)

    require.NoError(t, err)
    assert.Equal(t, newName, result.Name)
}

func TestDelete{{Resource}}(t *testing.T) {
    logger := zap.NewNop()
    repo := new(Mock{{Resource}}Repository)
    svc := service.New{{Resource}}Service(repo, logger)

    ctx := context.Background()
    id := "test-id"
    existing := &domain.{{Resource}}{ID: id, Name: "test"}

    repo.On("GetByID", ctx, id).Return(existing, nil)
    repo.On("Delete", ctx, id).Return(nil)

    err := svc.Delete(ctx, id)

    require.NoError(t, err)
    repo.AssertExpectations(t)
}
```
