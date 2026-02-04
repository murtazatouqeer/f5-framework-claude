# Repository Pattern

Implementing the repository pattern for clean data access in Go.

## Interface Definition

```go
// internal/domain/user/repository.go
package user

import (
    "context"
    "github.com/google/uuid"
)

// Repository defines the contract for user data access
type Repository interface {
    // Basic CRUD
    Create(ctx context.Context, user *User) error
    GetByID(ctx context.Context, id uuid.UUID) (*User, error)
    Update(ctx context.Context, user *User) error
    Delete(ctx context.Context, id uuid.UUID) error

    // Queries
    GetByEmail(ctx context.Context, email Email) (*User, error)
    List(ctx context.Context, filter Filter) ([]*User, int64, error)
    ExistsByEmail(ctx context.Context, email Email) (bool, error)

    // Bulk operations
    CreateMany(ctx context.Context, users []*User) error
    DeleteMany(ctx context.Context, ids []uuid.UUID) error
}

// Filter for list queries
type Filter struct {
    Search   *string
    Status   *Status
    Role     *string
    FromDate *time.Time
    ToDate   *time.Time
    Limit    int
    Offset   int
    SortBy   string
    Order    string
}
```

## Generic Repository

```go
// internal/repository/base.go
package repository

import (
    "context"
)

// GenericRepository defines common repository operations
type GenericRepository[T any, ID comparable] interface {
    Create(ctx context.Context, entity *T) error
    GetByID(ctx context.Context, id ID) (*T, error)
    Update(ctx context.Context, entity *T) error
    Delete(ctx context.Context, id ID) error
    List(ctx context.Context, filter Filter) ([]*T, int64, error)
}

// Filter for generic queries
type Filter struct {
    Conditions map[string]interface{}
    Limit      int
    Offset     int
    SortBy     string
    Order      string
}
```

## Concrete Implementation

```go
// internal/repository/postgres/user_repository.go
package postgres

import (
    "context"
    "database/sql"
    "errors"
    "fmt"
    "strings"

    "github.com/google/uuid"
    "github.com/jmoiron/sqlx"

    "myproject/internal/domain/user"
)

type userRepository struct {
    db *sqlx.DB
}

func NewUserRepository(db *sqlx.DB) user.Repository {
    return &userRepository{db: db}
}

func (r *userRepository) Create(ctx context.Context, u *user.User) error {
    query := `
        INSERT INTO users (id, email, name, password, status, role, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    `
    _, err := r.db.ExecContext(ctx, query,
        u.ID, u.Email, u.Name, u.Password, u.Status, u.Role, u.CreatedAt, u.UpdatedAt,
    )
    if err != nil {
        if strings.Contains(err.Error(), "duplicate key") {
            return user.ErrAlreadyExists
        }
        return fmt.Errorf("creating user: %w", err)
    }
    return nil
}

func (r *userRepository) GetByID(ctx context.Context, id uuid.UUID) (*user.User, error) {
    var row userRow
    query := `SELECT * FROM users WHERE id = $1 AND deleted_at IS NULL`

    if err := r.db.GetContext(ctx, &row, query, id); err != nil {
        if errors.Is(err, sql.ErrNoRows) {
            return nil, user.ErrNotFound
        }
        return nil, fmt.Errorf("getting user: %w", err)
    }

    return row.toDomain(), nil
}

func (r *userRepository) GetByEmail(ctx context.Context, email user.Email) (*user.User, error) {
    var row userRow
    query := `SELECT * FROM users WHERE email = $1 AND deleted_at IS NULL`

    if err := r.db.GetContext(ctx, &row, query, string(email)); err != nil {
        if errors.Is(err, sql.ErrNoRows) {
            return nil, user.ErrNotFound
        }
        return nil, fmt.Errorf("getting user by email: %w", err)
    }

    return row.toDomain(), nil
}

func (r *userRepository) List(ctx context.Context, filter user.Filter) ([]*user.User, int64, error) {
    qb := newQueryBuilder("users")

    // Build conditions
    qb.Where("deleted_at IS NULL")

    if filter.Search != nil && *filter.Search != "" {
        qb.Where("(name ILIKE ? OR email ILIKE ?)", "%"+*filter.Search+"%", "%"+*filter.Search+"%")
    }

    if filter.Status != nil {
        qb.Where("status = ?", *filter.Status)
    }

    if filter.Role != nil {
        qb.Where("role = ?", *filter.Role)
    }

    if filter.FromDate != nil {
        qb.Where("created_at >= ?", *filter.FromDate)
    }

    if filter.ToDate != nil {
        qb.Where("created_at <= ?", *filter.ToDate)
    }

    // Count total
    total, err := qb.Count(ctx, r.db)
    if err != nil {
        return nil, 0, fmt.Errorf("counting users: %w", err)
    }

    // Set pagination and sorting
    qb.OrderBy(filter.SortBy, filter.Order)
    qb.Limit(filter.Limit)
    qb.Offset(filter.Offset)

    // Execute query
    var rows []userRow
    if err := qb.Select(ctx, r.db, &rows); err != nil {
        return nil, 0, fmt.Errorf("listing users: %w", err)
    }

    users := make([]*user.User, len(rows))
    for i, row := range rows {
        users[i] = row.toDomain()
    }

    return users, total, nil
}

func (r *userRepository) Update(ctx context.Context, u *user.User) error {
    query := `
        UPDATE users
        SET name = $1, status = $2, role = $3, updated_at = $4
        WHERE id = $5 AND deleted_at IS NULL
    `
    result, err := r.db.ExecContext(ctx, query, u.Name, u.Status, u.Role, u.UpdatedAt, u.ID)
    if err != nil {
        return fmt.Errorf("updating user: %w", err)
    }

    rows, _ := result.RowsAffected()
    if rows == 0 {
        return user.ErrNotFound
    }

    return nil
}

func (r *userRepository) Delete(ctx context.Context, id uuid.UUID) error {
    query := `UPDATE users SET deleted_at = NOW() WHERE id = $1 AND deleted_at IS NULL`
    result, err := r.db.ExecContext(ctx, query, id)
    if err != nil {
        return fmt.Errorf("deleting user: %w", err)
    }

    rows, _ := result.RowsAffected()
    if rows == 0 {
        return user.ErrNotFound
    }

    return nil
}

func (r *userRepository) ExistsByEmail(ctx context.Context, email user.Email) (bool, error) {
    var exists bool
    query := `SELECT EXISTS(SELECT 1 FROM users WHERE email = $1 AND deleted_at IS NULL)`

    if err := r.db.GetContext(ctx, &exists, query, string(email)); err != nil {
        return false, fmt.Errorf("checking email exists: %w", err)
    }

    return exists, nil
}

func (r *userRepository) CreateMany(ctx context.Context, users []*user.User) error {
    if len(users) == 0 {
        return nil
    }

    tx, err := r.db.BeginTxx(ctx, nil)
    if err != nil {
        return fmt.Errorf("beginning transaction: %w", err)
    }
    defer tx.Rollback()

    query := `
        INSERT INTO users (id, email, name, password, status, role, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    `

    for _, u := range users {
        if _, err := tx.ExecContext(ctx, query,
            u.ID, u.Email, u.Name, u.Password, u.Status, u.Role, u.CreatedAt, u.UpdatedAt,
        ); err != nil {
            return fmt.Errorf("inserting user: %w", err)
        }
    }

    return tx.Commit()
}

func (r *userRepository) DeleteMany(ctx context.Context, ids []uuid.UUID) error {
    if len(ids) == 0 {
        return nil
    }

    query, args, err := sqlx.In(
        `UPDATE users SET deleted_at = NOW() WHERE id IN (?) AND deleted_at IS NULL`,
        ids,
    )
    if err != nil {
        return fmt.Errorf("building query: %w", err)
    }

    query = r.db.Rebind(query)
    _, err = r.db.ExecContext(ctx, query, args...)
    return err
}
```

## Query Builder Helper

```go
// internal/repository/postgres/query_builder.go
package postgres

import (
    "context"
    "fmt"
    "strings"

    "github.com/jmoiron/sqlx"
)

type queryBuilder struct {
    table      string
    conditions []string
    args       []interface{}
    orderBy    string
    limit      int
    offset     int
}

func newQueryBuilder(table string) *queryBuilder {
    return &queryBuilder{table: table}
}

func (qb *queryBuilder) Where(condition string, args ...interface{}) *queryBuilder {
    qb.conditions = append(qb.conditions, condition)
    qb.args = append(qb.args, args...)
    return qb
}

func (qb *queryBuilder) OrderBy(field, order string) *queryBuilder {
    if field == "" {
        field = "created_at"
    }
    if order != "ASC" {
        order = "DESC"
    }
    qb.orderBy = fmt.Sprintf("%s %s", field, order)
    return qb
}

func (qb *queryBuilder) Limit(n int) *queryBuilder {
    qb.limit = n
    return qb
}

func (qb *queryBuilder) Offset(n int) *queryBuilder {
    qb.offset = n
    return qb
}

func (qb *queryBuilder) buildWhere() string {
    if len(qb.conditions) == 0 {
        return ""
    }
    return "WHERE " + strings.Join(qb.conditions, " AND ")
}

func (qb *queryBuilder) Count(ctx context.Context, db *sqlx.DB) (int64, error) {
    var count int64
    query := fmt.Sprintf("SELECT COUNT(*) FROM %s %s", qb.table, qb.buildWhere())
    query = rebindArgs(query)

    if err := db.GetContext(ctx, &count, query, qb.args...); err != nil {
        return 0, err
    }
    return count, nil
}

func (qb *queryBuilder) Select(ctx context.Context, db *sqlx.DB, dest interface{}) error {
    query := fmt.Sprintf("SELECT * FROM %s %s", qb.table, qb.buildWhere())

    if qb.orderBy != "" {
        query += " ORDER BY " + qb.orderBy
    }

    args := append([]interface{}{}, qb.args...)
    argNum := len(args) + 1

    if qb.limit > 0 {
        query += fmt.Sprintf(" LIMIT $%d", argNum)
        args = append(args, qb.limit)
        argNum++
    }

    if qb.offset > 0 {
        query += fmt.Sprintf(" OFFSET $%d", argNum)
        args = append(args, qb.offset)
    }

    query = rebindArgs(query)
    return db.SelectContext(ctx, dest, query, args...)
}

func rebindArgs(query string) string {
    // Convert ? to $1, $2, etc.
    i := 1
    for strings.Contains(query, "?") {
        query = strings.Replace(query, "?", fmt.Sprintf("$%d", i), 1)
        i++
    }
    return query
}
```

## Unit of Work Pattern

```go
// internal/repository/unit_of_work.go
package repository

import (
    "context"

    "myproject/internal/domain/user"
    "myproject/internal/domain/order"
)

type UnitOfWork interface {
    Users() user.Repository
    Orders() order.Repository
    Commit() error
    Rollback() error
}

// Usage in service
func (s *OrderService) CreateOrder(ctx context.Context, input CreateOrderInput) error {
    uow := s.uowFactory.Begin(ctx)
    defer uow.Rollback()

    // Check user exists
    user, err := uow.Users().GetByID(ctx, input.UserID)
    if err != nil {
        return err
    }

    // Create order
    order := domain.NewOrder(user.ID, input.Items)
    if err := uow.Orders().Create(ctx, order); err != nil {
        return err
    }

    return uow.Commit()
}
```

## Best Practices

1. **Interface in Domain**: Define repository interfaces where they're used
2. **Implementation in Infrastructure**: Keep database details separate
3. **Single Responsibility**: One repository per aggregate root
4. **Unit of Work**: For cross-aggregate transactions
5. **Query Builder**: For complex dynamic queries
6. **Mapping Functions**: Convert between domain and DB models
