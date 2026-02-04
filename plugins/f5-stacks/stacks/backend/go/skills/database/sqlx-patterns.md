# SQLX Patterns

Best practices for using sqlx with PostgreSQL in Go applications.

## Connection Setup

```go
// pkg/database/postgres.go
package database

import (
    "fmt"
    "time"

    _ "github.com/jackc/pgx/v5/stdlib"
    "github.com/jmoiron/sqlx"
)

type Config struct {
    URL             string
    MaxOpenConns    int
    MaxIdleConns    int
    ConnMaxLifetime time.Duration
    ConnMaxIdleTime time.Duration
}

func NewPostgres(cfg Config) (*sqlx.DB, error) {
    db, err := sqlx.Connect("pgx", cfg.URL)
    if err != nil {
        return nil, fmt.Errorf("connecting to database: %w", err)
    }

    // Connection pool settings
    db.SetMaxOpenConns(cfg.MaxOpenConns)
    db.SetMaxIdleConns(cfg.MaxIdleConns)
    db.SetConnMaxLifetime(cfg.ConnMaxLifetime)
    db.SetConnMaxIdleTime(cfg.ConnMaxIdleTime)

    // Verify connection
    if err := db.Ping(); err != nil {
        return nil, fmt.Errorf("pinging database: %w", err)
    }

    return db, nil
}

func DefaultConfig(url string) Config {
    return Config{
        URL:             url,
        MaxOpenConns:    25,
        MaxIdleConns:    5,
        ConnMaxLifetime: 5 * time.Minute,
        ConnMaxIdleTime: 1 * time.Minute,
    }
}
```

## Model Definition

```go
// internal/repository/postgres/models.go
package postgres

import (
    "database/sql"
    "time"

    "github.com/google/uuid"
)

// Use struct tags for column mapping
type UserRow struct {
    ID        uuid.UUID      `db:"id"`
    Email     string         `db:"email"`
    Name      string         `db:"name"`
    Password  string         `db:"password"`
    Status    string         `db:"status"`
    Role      string         `db:"role"`
    CreatedAt time.Time      `db:"created_at"`
    UpdatedAt time.Time      `db:"updated_at"`
    DeletedAt sql.NullTime   `db:"deleted_at"`
}

// For nullable strings
type ProfileRow struct {
    ID        uuid.UUID      `db:"id"`
    UserID    uuid.UUID      `db:"user_id"`
    Bio       sql.NullString `db:"bio"`
    AvatarURL sql.NullString `db:"avatar_url"`
}
```

## Basic CRUD Operations

```go
// internal/repository/postgres/user_repository.go
package postgres

import (
    "context"
    "database/sql"
    "errors"
    "fmt"

    "github.com/google/uuid"
    "github.com/jmoiron/sqlx"

    "myproject/internal/domain/user"
)

type UserRepository struct {
    db *sqlx.DB
}

func NewUserRepository(db *sqlx.DB) *UserRepository {
    return &UserRepository{db: db}
}

// Create with NamedExec
func (r *UserRepository) Create(ctx context.Context, u *user.User) error {
    query := `
        INSERT INTO users (id, email, name, password, status, created_at, updated_at)
        VALUES (:id, :email, :name, :password, :status, :created_at, :updated_at)
    `

    row := toRow(u)
    _, err := r.db.NamedExecContext(ctx, query, row)
    if err != nil {
        return fmt.Errorf("inserting user: %w", err)
    }
    return nil
}

// GetByID with Get (single row)
func (r *UserRepository) GetByID(ctx context.Context, id uuid.UUID) (*user.User, error) {
    var row UserRow
    query := `SELECT * FROM users WHERE id = $1 AND deleted_at IS NULL`

    err := r.db.GetContext(ctx, &row, query, id)
    if err != nil {
        if errors.Is(err, sql.ErrNoRows) {
            return nil, user.ErrNotFound
        }
        return nil, fmt.Errorf("getting user: %w", err)
    }

    return toDomain(&row), nil
}

// List with Select (multiple rows)
func (r *UserRepository) List(ctx context.Context, filter user.Filter) ([]*user.User, int64, error) {
    var rows []UserRow
    var total int64

    // Count query
    countQuery := `SELECT COUNT(*) FROM users WHERE deleted_at IS NULL`
    if err := r.db.GetContext(ctx, &total, countQuery); err != nil {
        return nil, 0, fmt.Errorf("counting users: %w", err)
    }

    // Select query
    query := `
        SELECT * FROM users
        WHERE deleted_at IS NULL
        ORDER BY created_at DESC
        LIMIT $1 OFFSET $2
    `

    if err := r.db.SelectContext(ctx, &rows, query, filter.Limit, filter.Offset); err != nil {
        return nil, 0, fmt.Errorf("listing users: %w", err)
    }

    users := make([]*user.User, len(rows))
    for i, row := range rows {
        users[i] = toDomain(&row)
    }

    return users, total, nil
}

// Update with NamedExec
func (r *UserRepository) Update(ctx context.Context, u *user.User) error {
    query := `
        UPDATE users
        SET name = :name, status = :status, updated_at = :updated_at
        WHERE id = :id AND deleted_at IS NULL
    `

    row := toRow(u)
    result, err := r.db.NamedExecContext(ctx, query, row)
    if err != nil {
        return fmt.Errorf("updating user: %w", err)
    }

    affected, _ := result.RowsAffected()
    if affected == 0 {
        return user.ErrNotFound
    }

    return nil
}

// Delete (soft delete)
func (r *UserRepository) Delete(ctx context.Context, id uuid.UUID) error {
    query := `UPDATE users SET deleted_at = NOW() WHERE id = $1 AND deleted_at IS NULL`

    result, err := r.db.ExecContext(ctx, query, id)
    if err != nil {
        return fmt.Errorf("deleting user: %w", err)
    }

    affected, _ := result.RowsAffected()
    if affected == 0 {
        return user.ErrNotFound
    }

    return nil
}

// Mapping functions
func toRow(u *user.User) *UserRow {
    return &UserRow{
        ID:        u.ID,
        Email:     string(u.Email),
        Name:      u.Name,
        Password:  string(u.Password),
        Status:    string(u.Status),
        CreatedAt: u.CreatedAt,
        UpdatedAt: u.UpdatedAt,
    }
}

func toDomain(row *UserRow) *user.User {
    return &user.User{
        ID:        row.ID,
        Email:     user.Email(row.Email),
        Name:      row.Name,
        Password:  user.HashedPassword(row.Password),
        Status:    user.Status(row.Status),
        CreatedAt: row.CreatedAt,
        UpdatedAt: row.UpdatedAt,
    }
}
```

## Dynamic Query Building

```go
// Dynamic WHERE clause construction
func (r *UserRepository) Search(ctx context.Context, filter user.Filter) ([]*user.User, int64, error) {
    // Build WHERE conditions dynamically
    conditions := []string{"deleted_at IS NULL"}
    args := []interface{}{}
    argNum := 1

    if filter.Search != nil && *filter.Search != "" {
        conditions = append(conditions, fmt.Sprintf(
            "(name ILIKE $%d OR email ILIKE $%d)", argNum, argNum))
        args = append(args, "%"+*filter.Search+"%")
        argNum++
    }

    if filter.Status != nil {
        conditions = append(conditions, fmt.Sprintf("status = $%d", argNum))
        args = append(args, *filter.Status)
        argNum++
    }

    if filter.Role != nil {
        conditions = append(conditions, fmt.Sprintf("role = $%d", argNum))
        args = append(args, *filter.Role)
        argNum++
    }

    whereClause := strings.Join(conditions, " AND ")

    // Count query
    var total int64
    countQuery := fmt.Sprintf("SELECT COUNT(*) FROM users WHERE %s", whereClause)
    if err := r.db.GetContext(ctx, &total, countQuery, args...); err != nil {
        return nil, 0, err
    }

    // Validate sort field
    sortField := "created_at"
    validSorts := map[string]bool{"created_at": true, "name": true, "email": true}
    if filter.SortBy != "" && validSorts[filter.SortBy] {
        sortField = filter.SortBy
    }

    order := "DESC"
    if strings.ToUpper(filter.Order) == "ASC" {
        order = "ASC"
    }

    // Main query
    query := fmt.Sprintf(`
        SELECT * FROM users
        WHERE %s
        ORDER BY %s %s
        LIMIT $%d OFFSET $%d
    `, whereClause, sortField, order, argNum, argNum+1)

    args = append(args, filter.Limit, filter.Offset)

    var rows []UserRow
    if err := r.db.SelectContext(ctx, &rows, query, args...); err != nil {
        return nil, 0, err
    }

    // Convert to domain
    users := make([]*user.User, len(rows))
    for i, row := range rows {
        users[i] = toDomain(&row)
    }

    return users, total, nil
}
```

## Transactions

```go
// Transaction wrapper
type TxKey struct{}

func (r *UserRepository) WithTransaction(ctx context.Context, fn func(context.Context) error) error {
    tx, err := r.db.BeginTxx(ctx, nil)
    if err != nil {
        return fmt.Errorf("beginning transaction: %w", err)
    }

    txCtx := context.WithValue(ctx, TxKey{}, tx)

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

func (r *UserRepository) getExecutor(ctx context.Context) sqlx.ExtContext {
    if tx, ok := ctx.Value(TxKey{}).(*sqlx.Tx); ok {
        return tx
    }
    return r.db
}
```

## Bulk Operations

```go
// Batch insert using NamedExec with slice
func (r *UserRepository) CreateMany(ctx context.Context, users []*user.User) error {
    if len(users) == 0 {
        return nil
    }

    query := `
        INSERT INTO users (id, email, name, password, status, created_at, updated_at)
        VALUES (:id, :email, :name, :password, :status, :created_at, :updated_at)
    `

    rows := make([]UserRow, len(users))
    for i, u := range users {
        rows[i] = *toRow(u)
    }

    _, err := r.db.NamedExecContext(ctx, query, rows)
    if err != nil {
        return fmt.Errorf("bulk inserting users: %w", err)
    }

    return nil
}

// Batch update using IN clause
func (r *UserRepository) UpdateStatusMany(ctx context.Context, ids []uuid.UUID, status string) error {
    if len(ids) == 0 {
        return nil
    }

    query, args, err := sqlx.In(`
        UPDATE users SET status = ?, updated_at = NOW()
        WHERE id IN (?) AND deleted_at IS NULL
    `, status, ids)
    if err != nil {
        return err
    }

    query = r.db.Rebind(query)
    _, err = r.db.ExecContext(ctx, query, args...)
    return err
}
```

## Best Practices

1. **Use Context**: Always pass context for cancellation
2. **Named Queries**: Use `:name` for better readability
3. **Validate Sort Fields**: Prevent SQL injection in ORDER BY
4. **Handle NULL**: Use sql.Null* types for nullable columns
5. **Connection Pooling**: Configure pool settings appropriately
6. **Transaction Scope**: Keep transactions as short as possible
