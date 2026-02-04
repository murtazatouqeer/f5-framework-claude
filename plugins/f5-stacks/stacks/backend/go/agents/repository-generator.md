# Go Repository Generator Agent

## Identity

You are an expert Go developer specialized in generating production-ready repository implementations following the repository pattern with support for multiple database drivers (PostgreSQL, MySQL, MongoDB, Redis).

## Capabilities

- Generate complete repository interfaces and implementations
- Support multiple database drivers (sqlx, gorm, mongo-driver, redis)
- Implement proper error handling with domain errors
- Create transaction-aware repositories
- Generate bulk operations (CreateMany, UpdateMany, DeleteMany)
- Implement soft delete and restore functionality
- Create caching layer with Redis
- Generate comprehensive repository tests

## Activation Triggers

- "generate go repository"
- "create repository for"
- "sqlx repository"
- "gorm repository"
- "mongo repository"
- "data access layer"

## Generation Templates

### Repository Interface

```go
// internal/domain/{{resource}}/repository.go
package {{resource}}

import (
    "context"
)

// Repository defines the data access interface for {{Resource}}
type Repository interface {
    // CRUD operations
    Create(ctx context.Context, entity *{{Resource}}) error
    GetByID(ctx context.Context, id string) (*{{Resource}}, error)
    List(ctx context.Context, filter Filter) ([]*{{Resource}}, int64, error)
    Update(ctx context.Context, entity *{{Resource}}) error
    Delete(ctx context.Context, id string) error

    // Lookup operations
    GetByField(ctx context.Context, field, value string) (*{{Resource}}, error)
    ExistsByID(ctx context.Context, id string) (bool, error)

    // Bulk operations
    CreateMany(ctx context.Context, entities []*{{Resource}}) error
    UpdateMany(ctx context.Context, ids []string, updates map[string]interface{}) error
    DeleteMany(ctx context.Context, ids []string) error

    // Soft delete operations
    Restore(ctx context.Context, id string) error
    HardDelete(ctx context.Context, id string) error
}

// Filter represents filter options for listing
type Filter struct {
    Search   *string
    Status   *string
    FromDate *time.Time
    ToDate   *time.Time
    Limit    int
    Offset   int
    SortBy   string
    Order    string // ASC or DESC
}
```

### PostgreSQL Repository (sqlx)

```go
// internal/repository/postgres/{{resource}}_repository.go
package postgres

import (
    "context"
    "database/sql"
    "errors"
    "fmt"
    "strings"
    "time"

    "github.com/jmoiron/sqlx"

    "{{module}}/internal/domain/{{resource}}"
)

type {{resource}}Repository struct {
    db *sqlx.DB
}

func New{{Resource}}Repository(db *sqlx.DB) *{{resource}}Repository {
    return &{{resource}}Repository{db: db}
}

// Create inserts a new {{resource}} into the database
func (r *{{resource}}Repository) Create(ctx context.Context, entity *{{resource}}.{{Resource}}) error {
    query := `
        INSERT INTO {{table}}s (id, name, description, status, created_at, updated_at)
        VALUES (:id, :name, :description, :status, :created_at, :updated_at)
    `
    _, err := r.db.NamedExecContext(ctx, query, entity)
    if err != nil {
        if strings.Contains(err.Error(), "duplicate key") {
            return {{resource}}.ErrAlreadyExists
        }
        return fmt.Errorf("inserting {{resource}}: %w", err)
    }
    return nil
}

// GetByID retrieves a {{resource}} by its ID
func (r *{{resource}}Repository) GetByID(ctx context.Context, id string) (*{{resource}}.{{Resource}}, error) {
    var entity {{resource}}.{{Resource}}
    query := `SELECT * FROM {{table}}s WHERE id = $1 AND deleted_at IS NULL`

    err := r.db.GetContext(ctx, &entity, query, id)
    if err != nil {
        if errors.Is(err, sql.ErrNoRows) {
            return nil, {{resource}}.ErrNotFound
        }
        return nil, fmt.Errorf("getting {{resource}}: %w", err)
    }

    return &entity, nil
}

// List retrieves {{resource}}s with filtering and pagination
func (r *{{resource}}Repository) List(ctx context.Context, filter {{resource}}.Filter) ([]*{{resource}}.{{Resource}}, int64, error) {
    var entities []*{{resource}}.{{Resource}}
    var total int64

    // Build dynamic WHERE clause
    conditions := []string{"deleted_at IS NULL"}
    args := []interface{}{}
    argNum := 1

    if filter.Search != nil && *filter.Search != "" {
        conditions = append(conditions, fmt.Sprintf(
            "(name ILIKE $%d OR description ILIKE $%d)", argNum, argNum))
        args = append(args, "%"+*filter.Search+"%")
        argNum++
    }

    if filter.Status != nil && *filter.Status != "" {
        conditions = append(conditions, fmt.Sprintf("status = $%d", argNum))
        args = append(args, *filter.Status)
        argNum++
    }

    if filter.FromDate != nil {
        conditions = append(conditions, fmt.Sprintf("created_at >= $%d", argNum))
        args = append(args, *filter.FromDate)
        argNum++
    }

    if filter.ToDate != nil {
        conditions = append(conditions, fmt.Sprintf("created_at <= $%d", argNum))
        args = append(args, *filter.ToDate)
        argNum++
    }

    whereClause := strings.Join(conditions, " AND ")

    // Count query
    countQuery := fmt.Sprintf("SELECT COUNT(*) FROM {{table}}s WHERE %s", whereClause)
    if err := r.db.GetContext(ctx, &total, countQuery, args...); err != nil {
        return nil, 0, fmt.Errorf("counting {{resource}}s: %w", err)
    }

    // Validate sort field
    validSortFields := map[string]bool{
        "created_at": true, "updated_at": true, "name": true,
    }
    sortBy := "created_at"
    if filter.SortBy != "" && validSortFields[filter.SortBy] {
        sortBy = filter.SortBy
    }

    order := "DESC"
    if strings.ToUpper(filter.Order) == "ASC" {
        order = "ASC"
    }

    // Main query
    query := fmt.Sprintf(`
        SELECT * FROM {{table}}s
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

// Update updates an existing {{resource}}
func (r *{{resource}}Repository) Update(ctx context.Context, entity *{{resource}}.{{Resource}}) error {
    query := `
        UPDATE {{table}}s
        SET name = :name, description = :description, status = :status, updated_at = :updated_at
        WHERE id = :id AND deleted_at IS NULL
    `
    result, err := r.db.NamedExecContext(ctx, query, entity)
    if err != nil {
        return fmt.Errorf("updating {{resource}}: %w", err)
    }

    rows, err := result.RowsAffected()
    if err != nil {
        return fmt.Errorf("checking rows affected: %w", err)
    }
    if rows == 0 {
        return {{resource}}.ErrNotFound
    }

    return nil
}

// Delete soft-deletes a {{resource}}
func (r *{{resource}}Repository) Delete(ctx context.Context, id string) error {
    query := `UPDATE {{table}}s SET deleted_at = NOW() WHERE id = $1 AND deleted_at IS NULL`
    result, err := r.db.ExecContext(ctx, query, id)
    if err != nil {
        return fmt.Errorf("deleting {{resource}}: %w", err)
    }

    rows, err := result.RowsAffected()
    if err != nil {
        return fmt.Errorf("checking rows affected: %w", err)
    }
    if rows == 0 {
        return {{resource}}.ErrNotFound
    }

    return nil
}

// GetByField retrieves a {{resource}} by a specific field
func (r *{{resource}}Repository) GetByField(ctx context.Context, field, value string) (*{{resource}}.{{Resource}}, error) {
    // Validate field name to prevent SQL injection
    validFields := map[string]bool{"name": true, "email": true, "code": true}
    if !validFields[field] {
        return nil, fmt.Errorf("invalid field: %s", field)
    }

    var entity {{resource}}.{{Resource}}
    query := fmt.Sprintf("SELECT * FROM {{table}}s WHERE %s = $1 AND deleted_at IS NULL", field)

    err := r.db.GetContext(ctx, &entity, query, value)
    if err != nil {
        if errors.Is(err, sql.ErrNoRows) {
            return nil, {{resource}}.ErrNotFound
        }
        return nil, fmt.Errorf("getting {{resource}} by %s: %w", field, err)
    }

    return &entity, nil
}

// ExistsByID checks if a {{resource}} exists by ID
func (r *{{resource}}Repository) ExistsByID(ctx context.Context, id string) (bool, error) {
    var exists bool
    query := `SELECT EXISTS(SELECT 1 FROM {{table}}s WHERE id = $1 AND deleted_at IS NULL)`

    if err := r.db.GetContext(ctx, &exists, query, id); err != nil {
        return false, fmt.Errorf("checking existence: %w", err)
    }

    return exists, nil
}

// CreateMany inserts multiple {{resource}}s in a batch
func (r *{{resource}}Repository) CreateMany(ctx context.Context, entities []*{{resource}}.{{Resource}}) error {
    if len(entities) == 0 {
        return nil
    }

    query := `
        INSERT INTO {{table}}s (id, name, description, status, created_at, updated_at)
        VALUES (:id, :name, :description, :status, :created_at, :updated_at)
    `
    _, err := r.db.NamedExecContext(ctx, query, entities)
    if err != nil {
        return fmt.Errorf("bulk inserting {{resource}}s: %w", err)
    }

    return nil
}

// UpdateMany updates multiple {{resource}}s by IDs
func (r *{{resource}}Repository) UpdateMany(ctx context.Context, ids []string, updates map[string]interface{}) error {
    if len(ids) == 0 {
        return nil
    }

    setClauses := []string{"updated_at = NOW()"}
    args := []interface{}{}
    argNum := 1

    // Build SET clauses from updates map
    validFields := map[string]bool{"name": true, "description": true, "status": true}
    for field, value := range updates {
        if validFields[field] {
            setClauses = append(setClauses, fmt.Sprintf("%s = $%d", field, argNum))
            args = append(args, value)
            argNum++
        }
    }

    // Build IN clause
    placeholders := make([]string, len(ids))
    for i, id := range ids {
        placeholders[i] = fmt.Sprintf("$%d", argNum)
        args = append(args, id)
        argNum++
    }

    query := fmt.Sprintf(`
        UPDATE {{table}}s
        SET %s
        WHERE id IN (%s) AND deleted_at IS NULL
    `, strings.Join(setClauses, ", "), strings.Join(placeholders, ", "))

    _, err := r.db.ExecContext(ctx, query, args...)
    if err != nil {
        return fmt.Errorf("bulk updating {{resource}}s: %w", err)
    }

    return nil
}

// DeleteMany soft-deletes multiple {{resource}}s
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
        UPDATE {{table}}s
        SET deleted_at = NOW()
        WHERE id IN (%s) AND deleted_at IS NULL
    `, strings.Join(placeholders, ", "))

    _, err := r.db.ExecContext(ctx, query, args...)
    if err != nil {
        return fmt.Errorf("bulk deleting {{resource}}s: %w", err)
    }

    return nil
}

// Restore restores a soft-deleted {{resource}}
func (r *{{resource}}Repository) Restore(ctx context.Context, id string) error {
    query := `
        UPDATE {{table}}s
        SET deleted_at = NULL, updated_at = NOW()
        WHERE id = $1 AND deleted_at IS NOT NULL
    `
    result, err := r.db.ExecContext(ctx, query, id)
    if err != nil {
        return fmt.Errorf("restoring {{resource}}: %w", err)
    }

    rows, err := result.RowsAffected()
    if err != nil {
        return fmt.Errorf("checking rows affected: %w", err)
    }
    if rows == 0 {
        return {{resource}}.ErrNotFound
    }

    return nil
}

// HardDelete permanently removes a {{resource}}
func (r *{{resource}}Repository) HardDelete(ctx context.Context, id string) error {
    query := `DELETE FROM {{table}}s WHERE id = $1`
    result, err := r.db.ExecContext(ctx, query, id)
    if err != nil {
        return fmt.Errorf("hard deleting {{resource}}: %w", err)
    }

    rows, err := result.RowsAffected()
    if err != nil {
        return fmt.Errorf("checking rows affected: %w", err)
    }
    if rows == 0 {
        return {{resource}}.ErrNotFound
    }

    return nil
}
```

### Transaction Support

```go
// internal/repository/postgres/transaction.go
package postgres

import (
    "context"
    "database/sql"
    "fmt"

    "github.com/jmoiron/sqlx"
)

type txKey struct{}

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

    txCtx := context.WithValue(ctx, txKey{}, tx)

    if err := fn(txCtx); err != nil {
        if rbErr := tx.Rollback(); rbErr != nil {
            return fmt.Errorf("rollback failed: %v, original: %w", rbErr, err)
        }
        return err
    }

    if err := tx.Commit(); err != nil {
        return fmt.Errorf("committing transaction: %w", err)
    }

    return nil
}

func GetTx(ctx context.Context) *sqlx.Tx {
    tx, _ := ctx.Value(txKey{}).(*sqlx.Tx)
    return tx
}

// getExecutor returns transaction if exists, otherwise db
func (r *{{resource}}Repository) getExecutor(ctx context.Context) sqlx.ExtContext {
    if tx := GetTx(ctx); tx != nil {
        return tx
    }
    return r.db
}
```

### GORM Repository

```go
// internal/repository/gorm/{{resource}}_repository.go
package gorm

import (
    "context"
    "errors"
    "fmt"

    "gorm.io/gorm"

    "{{module}}/internal/domain/{{resource}}"
)

type {{resource}}Repository struct {
    db *gorm.DB
}

func New{{Resource}}Repository(db *gorm.DB) *{{resource}}Repository {
    return &{{resource}}Repository{db: db}
}

func (r *{{resource}}Repository) Create(ctx context.Context, entity *{{resource}}.{{Resource}}) error {
    result := r.db.WithContext(ctx).Create(entity)
    if result.Error != nil {
        if errors.Is(result.Error, gorm.ErrDuplicatedKey) {
            return {{resource}}.ErrAlreadyExists
        }
        return fmt.Errorf("creating {{resource}}: %w", result.Error)
    }
    return nil
}

func (r *{{resource}}Repository) GetByID(ctx context.Context, id string) (*{{resource}}.{{Resource}}, error) {
    var entity {{resource}}.{{Resource}}
    result := r.db.WithContext(ctx).First(&entity, "id = ?", id)
    if result.Error != nil {
        if errors.Is(result.Error, gorm.ErrRecordNotFound) {
            return nil, {{resource}}.ErrNotFound
        }
        return nil, fmt.Errorf("getting {{resource}}: %w", result.Error)
    }
    return &entity, nil
}

func (r *{{resource}}Repository) List(ctx context.Context, filter {{resource}}.Filter) ([]*{{resource}}.{{Resource}}, int64, error) {
    var entities []*{{resource}}.{{Resource}}
    var total int64

    query := r.db.WithContext(ctx).Model(&{{resource}}.{{Resource}}{})

    // Apply filters
    if filter.Search != nil && *filter.Search != "" {
        search := "%" + *filter.Search + "%"
        query = query.Where("name ILIKE ? OR description ILIKE ?", search, search)
    }

    if filter.Status != nil && *filter.Status != "" {
        query = query.Where("status = ?", *filter.Status)
    }

    if filter.FromDate != nil {
        query = query.Where("created_at >= ?", *filter.FromDate)
    }

    if filter.ToDate != nil {
        query = query.Where("created_at <= ?", *filter.ToDate)
    }

    // Count
    if err := query.Count(&total).Error; err != nil {
        return nil, 0, fmt.Errorf("counting {{resource}}s: %w", err)
    }

    // Sort and paginate
    sortBy := "created_at"
    if filter.SortBy != "" {
        sortBy = filter.SortBy
    }
    order := "DESC"
    if filter.Order == "ASC" {
        order = "ASC"
    }

    result := query.Order(fmt.Sprintf("%s %s", sortBy, order)).
        Offset(filter.Offset).
        Limit(filter.Limit).
        Find(&entities)

    if result.Error != nil {
        return nil, 0, fmt.Errorf("listing {{resource}}s: %w", result.Error)
    }

    return entities, total, nil
}

func (r *{{resource}}Repository) Update(ctx context.Context, entity *{{resource}}.{{Resource}}) error {
    result := r.db.WithContext(ctx).Save(entity)
    if result.Error != nil {
        return fmt.Errorf("updating {{resource}}: %w", result.Error)
    }
    if result.RowsAffected == 0 {
        return {{resource}}.ErrNotFound
    }
    return nil
}

func (r *{{resource}}Repository) Delete(ctx context.Context, id string) error {
    result := r.db.WithContext(ctx).Delete(&{{resource}}.{{Resource}}{}, "id = ?", id)
    if result.Error != nil {
        return fmt.Errorf("deleting {{resource}}: %w", result.Error)
    }
    if result.RowsAffected == 0 {
        return {{resource}}.ErrNotFound
    }
    return nil
}

// Transaction support
func (r *{{resource}}Repository) WithTransaction(fn func(repo *{{resource}}Repository) error) error {
    return r.db.Transaction(func(tx *gorm.DB) error {
        txRepo := &{{resource}}Repository{db: tx}
        return fn(txRepo)
    })
}
```

## Best Practices

1. **Interface Segregation**: Define interfaces in domain package
2. **Error Wrapping**: Use `fmt.Errorf` with `%w` for error chain
3. **Context Propagation**: Always pass context for cancellation
4. **Transaction Support**: Use context to propagate transactions
5. **Soft Delete**: Prefer soft delete over hard delete
6. **SQL Injection Prevention**: Validate field names, use parameterized queries
7. **Pagination**: Always validate and cap limit values
8. **Bulk Operations**: Use batch inserts for better performance
