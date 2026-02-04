# Go Repository Template

Production-ready repository layer templates for Go applications with PostgreSQL, MongoDB, and Redis.

## PostgreSQL Repository

```go
// internal/repository/postgres/{{resource}}.go
package postgres

import (
    "context"
    "database/sql"
    "errors"
    "fmt"
    "strings"

    "github.com/jmoiron/sqlx"

    "{{module}}/internal/domain"
)

type {{resource}}Repository struct {
    db *sqlx.DB
}

func New{{Resource}}Repository(db *sqlx.DB) *{{resource}}Repository {
    return &{{resource}}Repository{db: db}
}

func (r *{{resource}}Repository) Create(ctx context.Context, entity *domain.{{Resource}}) error {
    query := `
        INSERT INTO {{table}} (id, name, status, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5)
    `
    _, err := r.db.ExecContext(ctx, query,
        entity.ID,
        entity.Name,
        entity.Status,
        entity.CreatedAt,
        entity.UpdatedAt,
    )
    if err != nil {
        if strings.Contains(err.Error(), "duplicate key") {
            return domain.ErrAlreadyExists
        }
        return fmt.Errorf("inserting {{resource}}: %w", err)
    }
    return nil
}

func (r *{{resource}}Repository) GetByID(ctx context.Context, id string) (*domain.{{Resource}}, error) {
    var entity domain.{{Resource}}
    query := `SELECT * FROM {{table}} WHERE id = $1 AND deleted_at IS NULL`

    err := r.db.GetContext(ctx, &entity, query, id)
    if err != nil {
        if errors.Is(err, sql.ErrNoRows) {
            return nil, domain.ErrNotFound
        }
        return nil, fmt.Errorf("getting {{resource}}: %w", err)
    }

    return &entity, nil
}

func (r *{{resource}}Repository) GetByUniqueField(ctx context.Context, value string) (*domain.{{Resource}}, error) {
    var entity domain.{{Resource}}
    query := `SELECT * FROM {{table}} WHERE name = $1 AND deleted_at IS NULL`

    err := r.db.GetContext(ctx, &entity, query, value)
    if err != nil {
        if errors.Is(err, sql.ErrNoRows) {
            return nil, domain.ErrNotFound
        }
        return nil, fmt.Errorf("getting {{resource}} by unique field: %w", err)
    }

    return &entity, nil
}

func (r *{{resource}}Repository) List(ctx context.Context, filter domain.{{Resource}}Filter) ([]*domain.{{Resource}}, int64, error) {
    var entities []*domain.{{Resource}}
    var total int64

    // Build WHERE clause
    where := []string{"deleted_at IS NULL"}
    args := []interface{}{}
    argNum := 1

    if filter.Search != nil && *filter.Search != "" {
        where = append(where, fmt.Sprintf("(name ILIKE $%d OR description ILIKE $%d)", argNum, argNum))
        args = append(args, "%"+*filter.Search+"%")
        argNum++
    }

    if filter.Status != nil && *filter.Status != "" {
        where = append(where, fmt.Sprintf("status = $%d", argNum))
        args = append(args, *filter.Status)
        argNum++
    }

    whereClause := strings.Join(where, " AND ")

    // Count query
    countQuery := fmt.Sprintf("SELECT COUNT(*) FROM {{table}} WHERE %s", whereClause)
    if err := r.db.GetContext(ctx, &total, countQuery, args...); err != nil {
        return nil, 0, fmt.Errorf("counting {{resource}}s: %w", err)
    }

    // Validate sort field to prevent SQL injection
    validSortFields := map[string]bool{
        "created_at": true,
        "updated_at": true,
        "name":       true,
    }
    sortBy := "created_at"
    if filter.SortBy != "" && validSortFields[filter.SortBy] {
        sortBy = filter.SortBy
    }

    order := "DESC"
    if filter.Order == "ASC" {
        order = "ASC"
    }

    // Main query with pagination
    query := fmt.Sprintf(`
        SELECT * FROM {{table}}
        WHERE %s
        ORDER BY %s %s
        LIMIT $%d OFFSET $%d
    `, whereClause, sortBy, order, argNum, argNum+1)

    args = append(args, filter.Limit, filter.Offset)

    if err := r.db.SelectContext(ctx, &entities, query, args...); err != nil {
        return nil, 0, fmt.Errorf("listing {{resource}}s: %w", err)
    }

    return entities, total, nil
}

func (r *{{resource}}Repository) Update(ctx context.Context, entity *domain.{{Resource}}) error {
    query := `
        UPDATE {{table}}
        SET name = $1, status = $2, updated_at = $3
        WHERE id = $4 AND deleted_at IS NULL
    `
    result, err := r.db.ExecContext(ctx, query,
        entity.Name,
        entity.Status,
        entity.UpdatedAt,
        entity.ID,
    )
    if err != nil {
        return fmt.Errorf("updating {{resource}}: %w", err)
    }

    rows, err := result.RowsAffected()
    if err != nil {
        return fmt.Errorf("checking rows affected: %w", err)
    }
    if rows == 0 {
        return domain.ErrNotFound
    }

    return nil
}

func (r *{{resource}}Repository) Delete(ctx context.Context, id string) error {
    // Soft delete
    query := `UPDATE {{table}} SET deleted_at = NOW() WHERE id = $1 AND deleted_at IS NULL`
    result, err := r.db.ExecContext(ctx, query, id)
    if err != nil {
        return fmt.Errorf("deleting {{resource}}: %w", err)
    }

    rows, err := result.RowsAffected()
    if err != nil {
        return fmt.Errorf("checking rows affected: %w", err)
    }
    if rows == 0 {
        return domain.ErrNotFound
    }

    return nil
}

// HardDelete permanently removes the entity
func (r *{{resource}}Repository) HardDelete(ctx context.Context, id string) error {
    query := `DELETE FROM {{table}} WHERE id = $1`
    result, err := r.db.ExecContext(ctx, query, id)
    if err != nil {
        return fmt.Errorf("hard deleting {{resource}}: %w", err)
    }

    rows, err := result.RowsAffected()
    if err != nil {
        return fmt.Errorf("checking rows affected: %w", err)
    }
    if rows == 0 {
        return domain.ErrNotFound
    }

    return nil
}

// Restore restores a soft-deleted entity
func (r *{{resource}}Repository) Restore(ctx context.Context, id string) error {
    query := `UPDATE {{table}} SET deleted_at = NULL, updated_at = NOW() WHERE id = $1 AND deleted_at IS NOT NULL`
    result, err := r.db.ExecContext(ctx, query, id)
    if err != nil {
        return fmt.Errorf("restoring {{resource}}: %w", err)
    }

    rows, err := result.RowsAffected()
    if err != nil {
        return fmt.Errorf("checking rows affected: %w", err)
    }
    if rows == 0 {
        return domain.ErrNotFound
    }

    return nil
}
```

## Bulk Operations

```go
// internal/repository/postgres/{{resource}}_bulk.go
package postgres

import (
    "context"
    "fmt"
    "strings"

    "{{module}}/internal/domain"
)

func (r *{{resource}}Repository) CreateMany(ctx context.Context, entities []*domain.{{Resource}}) error {
    if len(entities) == 0 {
        return nil
    }

    valueStrings := make([]string, 0, len(entities))
    valueArgs := make([]interface{}, 0, len(entities)*5)

    for i, entity := range entities {
        offset := i * 5
        valueStrings = append(valueStrings, fmt.Sprintf("($%d, $%d, $%d, $%d, $%d)",
            offset+1, offset+2, offset+3, offset+4, offset+5))
        valueArgs = append(valueArgs,
            entity.ID,
            entity.Name,
            entity.Status,
            entity.CreatedAt,
            entity.UpdatedAt,
        )
    }

    query := fmt.Sprintf(`
        INSERT INTO {{table}} (id, name, status, created_at, updated_at)
        VALUES %s
    `, strings.Join(valueStrings, ","))

    _, err := r.db.ExecContext(ctx, query, valueArgs...)
    if err != nil {
        return fmt.Errorf("bulk inserting {{resource}}s: %w", err)
    }

    return nil
}

func (r *{{resource}}Repository) UpdateMany(ctx context.Context, ids []string, updates map[string]interface{}) error {
    if len(ids) == 0 {
        return nil
    }

    setClauses := []string{}
    args := []interface{}{}
    argNum := 1

    for field, value := range updates {
        setClauses = append(setClauses, fmt.Sprintf("%s = $%d", field, argNum))
        args = append(args, value)
        argNum++
    }

    // Add updated_at
    setClauses = append(setClauses, fmt.Sprintf("updated_at = NOW()"))

    // Build IN clause for IDs
    idPlaceholders := make([]string, len(ids))
    for i, id := range ids {
        idPlaceholders[i] = fmt.Sprintf("$%d", argNum)
        args = append(args, id)
        argNum++
    }

    query := fmt.Sprintf(`
        UPDATE {{table}}
        SET %s
        WHERE id IN (%s) AND deleted_at IS NULL
    `, strings.Join(setClauses, ", "), strings.Join(idPlaceholders, ", "))

    _, err := r.db.ExecContext(ctx, query, args...)
    if err != nil {
        return fmt.Errorf("bulk updating {{resource}}s: %w", err)
    }

    return nil
}

func (r *{{resource}}Repository) DeleteMany(ctx context.Context, ids []string) error {
    if len(ids) == 0 {
        return nil
    }

    placeholders := make([]string, len(ids))
    args := make([]interface{}, len(ids))
    for i, id := range ids {
        placeholders[i] = fmt.Sprintf("$%d", i+1)
        args[i] = id
    }

    query := fmt.Sprintf(`
        UPDATE {{table}}
        SET deleted_at = NOW()
        WHERE id IN (%s) AND deleted_at IS NULL
    `, strings.Join(placeholders, ", "))

    _, err := r.db.ExecContext(ctx, query, args...)
    if err != nil {
        return fmt.Errorf("bulk deleting {{resource}}s: %w", err)
    }

    return nil
}
```

## MongoDB Repository

```go
// internal/repository/mongo/{{resource}}.go
package mongo

import (
    "context"
    "errors"
    "fmt"
    "time"

    "go.mongodb.org/mongo-driver/bson"
    "go.mongodb.org/mongo-driver/bson/primitive"
    "go.mongodb.org/mongo-driver/mongo"
    "go.mongodb.org/mongo-driver/mongo/options"

    "{{module}}/internal/domain"
)

type {{resource}}Repository struct {
    collection *mongo.Collection
}

func New{{Resource}}Repository(db *mongo.Database) *{{resource}}Repository {
    return &{{resource}}Repository{
        collection: db.Collection("{{table}}"),
    }
}

func (r *{{resource}}Repository) Create(ctx context.Context, entity *domain.{{Resource}}) error {
    _, err := r.collection.InsertOne(ctx, entity)
    if err != nil {
        if mongo.IsDuplicateKeyError(err) {
            return domain.ErrAlreadyExists
        }
        return fmt.Errorf("inserting {{resource}}: %w", err)
    }
    return nil
}

func (r *{{resource}}Repository) GetByID(ctx context.Context, id string) (*domain.{{Resource}}, error) {
    filter := bson.M{
        "_id":        id,
        "deleted_at": bson.M{"$exists": false},
    }

    var entity domain.{{Resource}}
    err := r.collection.FindOne(ctx, filter).Decode(&entity)
    if err != nil {
        if errors.Is(err, mongo.ErrNoDocuments) {
            return nil, domain.ErrNotFound
        }
        return nil, fmt.Errorf("getting {{resource}}: %w", err)
    }

    return &entity, nil
}

func (r *{{resource}}Repository) List(ctx context.Context, filter domain.{{Resource}}Filter) ([]*domain.{{Resource}}, int64, error) {
    query := bson.M{"deleted_at": bson.M{"$exists": false}}

    if filter.Search != nil && *filter.Search != "" {
        query["$or"] = []bson.M{
            {"name": bson.M{"$regex": *filter.Search, "$options": "i"}},
            {"description": bson.M{"$regex": *filter.Search, "$options": "i"}},
        }
    }

    if filter.Status != nil && *filter.Status != "" {
        query["status"] = *filter.Status
    }

    // Count total
    total, err := r.collection.CountDocuments(ctx, query)
    if err != nil {
        return nil, 0, fmt.Errorf("counting {{resource}}s: %w", err)
    }

    // Sort options
    sortField := "created_at"
    if filter.SortBy != "" {
        sortField = filter.SortBy
    }
    sortOrder := -1 // DESC
    if filter.Order == "ASC" {
        sortOrder = 1
    }

    opts := options.Find().
        SetSort(bson.D{{sortField, sortOrder}}).
        SetSkip(int64(filter.Offset)).
        SetLimit(int64(filter.Limit))

    cursor, err := r.collection.Find(ctx, query, opts)
    if err != nil {
        return nil, 0, fmt.Errorf("finding {{resource}}s: %w", err)
    }
    defer cursor.Close(ctx)

    var entities []*domain.{{Resource}}
    if err := cursor.All(ctx, &entities); err != nil {
        return nil, 0, fmt.Errorf("decoding {{resource}}s: %w", err)
    }

    return entities, total, nil
}

func (r *{{resource}}Repository) Update(ctx context.Context, entity *domain.{{Resource}}) error {
    filter := bson.M{
        "_id":        entity.ID,
        "deleted_at": bson.M{"$exists": false},
    }
    update := bson.M{
        "$set": bson.M{
            "name":       entity.Name,
            "status":     entity.Status,
            "updated_at": entity.UpdatedAt,
        },
    }

    result, err := r.collection.UpdateOne(ctx, filter, update)
    if err != nil {
        return fmt.Errorf("updating {{resource}}: %w", err)
    }
    if result.MatchedCount == 0 {
        return domain.ErrNotFound
    }

    return nil
}

func (r *{{resource}}Repository) Delete(ctx context.Context, id string) error {
    filter := bson.M{
        "_id":        id,
        "deleted_at": bson.M{"$exists": false},
    }
    update := bson.M{
        "$set": bson.M{
            "deleted_at": time.Now(),
        },
    }

    result, err := r.collection.UpdateOne(ctx, filter, update)
    if err != nil {
        return fmt.Errorf("deleting {{resource}}: %w", err)
    }
    if result.MatchedCount == 0 {
        return domain.ErrNotFound
    }

    return nil
}

// CreateIndexes creates necessary indexes
func (r *{{resource}}Repository) CreateIndexes(ctx context.Context) error {
    indexes := []mongo.IndexModel{
        {
            Keys:    bson.D{{"name", 1}},
            Options: options.Index().SetUnique(true).SetPartialFilterExpression(bson.M{"deleted_at": bson.M{"$exists": false}}),
        },
        {
            Keys: bson.D{{"status", 1}},
        },
        {
            Keys: bson.D{{"created_at", -1}},
        },
    }

    _, err := r.collection.Indexes().CreateMany(ctx, indexes)
    return err
}
```

## Redis Cache Repository

```go
// internal/repository/redis/{{resource}}_cache.go
package redis

import (
    "context"
    "encoding/json"
    "fmt"
    "time"

    "github.com/redis/go-redis/v9"

    "{{module}}/internal/domain"
)

type {{resource}}CacheRepository struct {
    client *redis.Client
    ttl    time.Duration
    prefix string
}

func New{{Resource}}CacheRepository(client *redis.Client, ttl time.Duration) *{{resource}}CacheRepository {
    return &{{resource}}CacheRepository{
        client: client,
        ttl:    ttl,
        prefix: "{{resource}}:",
    }
}

func (r *{{resource}}CacheRepository) key(id string) string {
    return r.prefix + id
}

func (r *{{resource}}CacheRepository) listKey(filter domain.{{Resource}}Filter) string {
    return fmt.Sprintf("%slist:%d:%d:%s", r.prefix, filter.Limit, filter.Offset, *filter.Search)
}

func (r *{{resource}}CacheRepository) Get(ctx context.Context, id string) (*domain.{{Resource}}, error) {
    data, err := r.client.Get(ctx, r.key(id)).Bytes()
    if err != nil {
        if err == redis.Nil {
            return nil, nil // Cache miss
        }
        return nil, fmt.Errorf("getting from cache: %w", err)
    }

    var entity domain.{{Resource}}
    if err := json.Unmarshal(data, &entity); err != nil {
        return nil, fmt.Errorf("unmarshaling cached {{resource}}: %w", err)
    }

    return &entity, nil
}

func (r *{{resource}}CacheRepository) Set(ctx context.Context, entity *domain.{{Resource}}) error {
    data, err := json.Marshal(entity)
    if err != nil {
        return fmt.Errorf("marshaling {{resource}}: %w", err)
    }

    if err := r.client.Set(ctx, r.key(entity.ID), data, r.ttl).Err(); err != nil {
        return fmt.Errorf("setting cache: %w", err)
    }

    return nil
}

func (r *{{resource}}CacheRepository) Delete(ctx context.Context, id string) error {
    if err := r.client.Del(ctx, r.key(id)).Err(); err != nil {
        return fmt.Errorf("deleting from cache: %w", err)
    }
    return nil
}

func (r *{{resource}}CacheRepository) InvalidateList(ctx context.Context) error {
    pattern := r.prefix + "list:*"
    var cursor uint64
    for {
        keys, nextCursor, err := r.client.Scan(ctx, cursor, pattern, 100).Result()
        if err != nil {
            return fmt.Errorf("scanning keys: %w", err)
        }
        if len(keys) > 0 {
            if err := r.client.Del(ctx, keys...).Err(); err != nil {
                return fmt.Errorf("deleting list cache: %w", err)
            }
        }
        cursor = nextCursor
        if cursor == 0 {
            break
        }
    }
    return nil
}

func (r *{{resource}}CacheRepository) SetMany(ctx context.Context, entities []*domain.{{Resource}}) error {
    pipe := r.client.Pipeline()
    for _, entity := range entities {
        data, err := json.Marshal(entity)
        if err != nil {
            return fmt.Errorf("marshaling {{resource}}: %w", err)
        }
        pipe.Set(ctx, r.key(entity.ID), data, r.ttl)
    }
    _, err := pipe.Exec(ctx)
    return err
}
```

## Repository with Transaction Support

```go
// internal/repository/postgres/transaction.go
package postgres

import (
    "context"
    "database/sql"
    "fmt"

    "github.com/jmoiron/sqlx"
)

type TxKey struct{}

type TransactionManager struct {
    db *sqlx.DB
}

func NewTransactionManager(db *sqlx.DB) *TransactionManager {
    return &TransactionManager{db: db}
}

func (m *TransactionManager) WithTransaction(ctx context.Context, fn func(ctx context.Context) error) error {
    tx, err := m.db.BeginTxx(ctx, &sql.TxOptions{})
    if err != nil {
        return fmt.Errorf("beginning transaction: %w", err)
    }

    txCtx := context.WithValue(ctx, TxKey{}, tx)

    if err := fn(txCtx); err != nil {
        if rbErr := tx.Rollback(); rbErr != nil {
            return fmt.Errorf("rollback failed: %v, original error: %w", rbErr, err)
        }
        return err
    }

    if err := tx.Commit(); err != nil {
        return fmt.Errorf("committing transaction: %w", err)
    }

    return nil
}

func GetTx(ctx context.Context) *sqlx.Tx {
    tx, ok := ctx.Value(TxKey{}).(*sqlx.Tx)
    if !ok {
        return nil
    }
    return tx
}

// GetExecutor returns the transaction if present, otherwise the db connection
func (r *{{resource}}Repository) getExecutor(ctx context.Context) sqlx.ExtContext {
    if tx := GetTx(ctx); tx != nil {
        return tx
    }
    return r.db
}
```

## Repository Testing

```go
// internal/repository/postgres/{{resource}}_test.go
package postgres_test

import (
    "context"
    "testing"
    "time"

    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"
    "github.com/testcontainers/testcontainers-go"
    "github.com/testcontainers/testcontainers-go/wait"

    "{{module}}/internal/domain"
    "{{module}}/internal/repository/postgres"
)

func setupTestDB(t *testing.T) (*sqlx.DB, func()) {
    ctx := context.Background()

    req := testcontainers.ContainerRequest{
        Image:        "postgres:15-alpine",
        ExposedPorts: []string{"5432/tcp"},
        Env: map[string]string{
            "POSTGRES_USER":     "test",
            "POSTGRES_PASSWORD": "test",
            "POSTGRES_DB":       "test",
        },
        WaitingFor: wait.ForLog("database system is ready to accept connections"),
    }

    container, err := testcontainers.GenericContainer(ctx, testcontainers.GenericContainerRequest{
        ContainerRequest: req,
        Started:          true,
    })
    require.NoError(t, err)

    host, _ := container.Host(ctx)
    port, _ := container.MappedPort(ctx, "5432")

    dsn := fmt.Sprintf("postgres://test:test@%s:%s/test?sslmode=disable", host, port.Port())
    db, err := sqlx.Connect("postgres", dsn)
    require.NoError(t, err)

    // Run migrations
    db.MustExec(`
        CREATE TABLE IF NOT EXISTS {{table}} (
            id VARCHAR(36) PRIMARY KEY,
            name VARCHAR(255) NOT NULL UNIQUE,
            status VARCHAR(50) NOT NULL DEFAULT 'active',
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
            deleted_at TIMESTAMP
        )
    `)

    cleanup := func() {
        db.Close()
        container.Terminate(ctx)
    }

    return db, cleanup
}

func TestCreate(t *testing.T) {
    db, cleanup := setupTestDB(t)
    defer cleanup()

    repo := postgres.New{{Resource}}Repository(db)
    ctx := context.Background()

    entity := &domain.{{Resource}}{
        ID:        "test-id",
        Name:      "test",
        Status:    "active",
        CreatedAt: time.Now(),
        UpdatedAt: time.Now(),
    }

    err := repo.Create(ctx, entity)
    require.NoError(t, err)

    // Verify
    found, err := repo.GetByID(ctx, entity.ID)
    require.NoError(t, err)
    assert.Equal(t, entity.Name, found.Name)
}

func TestCreate_Duplicate(t *testing.T) {
    db, cleanup := setupTestDB(t)
    defer cleanup()

    repo := postgres.New{{Resource}}Repository(db)
    ctx := context.Background()

    entity := &domain.{{Resource}}{
        ID:        "test-id",
        Name:      "duplicate",
        Status:    "active",
        CreatedAt: time.Now(),
        UpdatedAt: time.Now(),
    }

    err := repo.Create(ctx, entity)
    require.NoError(t, err)

    // Try to create duplicate
    entity.ID = "test-id-2"
    err = repo.Create(ctx, entity)
    assert.ErrorIs(t, err, domain.ErrAlreadyExists)
}

func TestList_WithFilters(t *testing.T) {
    db, cleanup := setupTestDB(t)
    defer cleanup()

    repo := postgres.New{{Resource}}Repository(db)
    ctx := context.Background()

    // Create test data
    for i := 0; i < 15; i++ {
        entity := &domain.{{Resource}}{
            ID:        fmt.Sprintf("id-%d", i),
            Name:      fmt.Sprintf("test-%d", i),
            Status:    "active",
            CreatedAt: time.Now(),
            UpdatedAt: time.Now(),
        }
        require.NoError(t, repo.Create(ctx, entity))
    }

    // Test pagination
    filter := domain.{{Resource}}Filter{
        Limit:  10,
        Offset: 0,
    }

    results, total, err := repo.List(ctx, filter)
    require.NoError(t, err)
    assert.Len(t, results, 10)
    assert.Equal(t, int64(15), total)

    // Test search
    search := "test-1"
    filter.Search = &search
    results, total, err = repo.List(ctx, filter)
    require.NoError(t, err)
    assert.Greater(t, len(results), 0)
}
```
