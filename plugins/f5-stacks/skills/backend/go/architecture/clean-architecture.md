# Clean Architecture in Go

Domain-centric architecture with clear separation of concerns and dependency inversion.

## Layer Structure

```
internal/
├── domain/                        # Enterprise Business Rules
│   └── user/
│       ├── entity.go             # Domain entity
│       ├── value_objects.go      # Value objects
│       ├── repository.go         # Repository interface
│       ├── service.go            # Service interface
│       └── errors.go             # Domain errors
│
├── usecase/                       # Application Business Rules
│   └── user/
│       ├── create.go             # Create use case
│       ├── find.go               # Find use case
│       ├── update.go             # Update use case
│       ├── delete.go             # Delete use case
│       └── dto.go                # Input/Output DTOs
│
├── adapter/                       # Interface Adapters
│   ├── handler/                  # HTTP handlers
│   │   └── user_handler.go
│   ├── repository/               # Repository implementations
│   │   └── postgres/
│   │       └── user_repository.go
│   └── presenter/
│       └── user_presenter.go
│
└── infrastructure/               # Frameworks & Drivers
    ├── database/
    │   └── postgres.go
    ├── server/
    │   └── gin.go
    └── config/
        └── config.go
```

## Domain Layer

```go
// internal/domain/user/entity.go
package user

import (
    "time"
    "github.com/google/uuid"
)

type Status string

const (
    StatusActive   Status = "active"
    StatusInactive Status = "inactive"
    StatusPending  Status = "pending"
)

type User struct {
    ID        uuid.UUID
    Email     Email           // Value object
    Name      string
    Password  HashedPassword  // Value object
    Status    Status
    CreatedAt time.Time
    UpdatedAt time.Time
}

// Factory method with validation
func NewUser(email, name, password string) (*User, error) {
    e, err := NewEmail(email)
    if err != nil {
        return nil, err
    }

    hp, err := NewHashedPassword(password)
    if err != nil {
        return nil, err
    }

    return &User{
        ID:        uuid.New(),
        Email:     e,
        Name:      name,
        Password:  hp,
        Status:    StatusPending,
        CreatedAt: time.Now(),
        UpdatedAt: time.Now(),
    }, nil
}

// Domain behavior
func (u *User) Activate() error {
    if u.Status == StatusActive {
        return ErrAlreadyActive
    }
    u.Status = StatusActive
    u.UpdatedAt = time.Now()
    return nil
}

func (u *User) Deactivate() {
    u.Status = StatusInactive
    u.UpdatedAt = time.Now()
}

func (u *User) UpdateName(name string) error {
    if name == "" {
        return ErrInvalidName
    }
    u.Name = name
    u.UpdatedAt = time.Now()
    return nil
}
```

## Value Objects

```go
// internal/domain/user/value_objects.go
package user

import (
    "regexp"
    "golang.org/x/crypto/bcrypt"
)

// Email value object
type Email string

func NewEmail(value string) (Email, error) {
    if !isValidEmail(value) {
        return "", ErrInvalidEmail
    }
    return Email(value), nil
}

func (e Email) String() string {
    return string(e)
}

func isValidEmail(email string) bool {
    pattern := `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`
    matched, _ := regexp.MatchString(pattern, email)
    return matched
}

// HashedPassword value object
type HashedPassword string

func NewHashedPassword(plain string) (HashedPassword, error) {
    if len(plain) < 8 {
        return "", ErrPasswordTooShort
    }
    hashed, err := bcrypt.GenerateFromPassword([]byte(plain), bcrypt.DefaultCost)
    if err != nil {
        return "", err
    }
    return HashedPassword(hashed), nil
}

func (hp HashedPassword) Compare(plain string) bool {
    return bcrypt.CompareHashAndPassword([]byte(hp), []byte(plain)) == nil
}
```

## Repository Interface (Domain)

```go
// internal/domain/user/repository.go
package user

import (
    "context"
    "github.com/google/uuid"
)

type Repository interface {
    FindByID(ctx context.Context, id uuid.UUID) (*User, error)
    FindByEmail(ctx context.Context, email Email) (*User, error)
    FindAll(ctx context.Context, opts FindOptions) ([]*User, int64, error)
    Save(ctx context.Context, user *User) error
    Delete(ctx context.Context, id uuid.UUID) error
}

type FindOptions struct {
    Offset int
    Limit  int
    Search string
    Status *Status
}
```

## Use Case Layer

```go
// internal/usecase/user/create.go
package user

import (
    "context"
    "myproject/internal/domain/user"
)

type CreateUserInput struct {
    Email    string `validate:"required,email"`
    Name     string `validate:"required,min=2,max=100"`
    Password string `validate:"required,min=8"`
}

type CreateUserOutput struct {
    ID    string `json:"id"`
    Email string `json:"email"`
    Name  string `json:"name"`
}

type CreateUserUseCase struct {
    repo user.Repository
}

func NewCreateUserUseCase(repo user.Repository) *CreateUserUseCase {
    return &CreateUserUseCase{repo: repo}
}

func (uc *CreateUserUseCase) Execute(ctx context.Context, input CreateUserInput) (*CreateUserOutput, error) {
    // Check existing
    email, err := user.NewEmail(input.Email)
    if err != nil {
        return nil, err
    }

    existing, err := uc.repo.FindByEmail(ctx, email)
    if err != nil && err != user.ErrNotFound {
        return nil, err
    }
    if existing != nil {
        return nil, user.ErrEmailExists
    }

    // Create domain entity
    u, err := user.NewUser(input.Email, input.Name, input.Password)
    if err != nil {
        return nil, err
    }

    // Persist
    if err := uc.repo.Save(ctx, u); err != nil {
        return nil, err
    }

    return &CreateUserOutput{
        ID:    u.ID.String(),
        Email: u.Email.String(),
        Name:  u.Name,
    }, nil
}
```

## Adapter Layer - Handler

```go
// internal/adapter/handler/user_handler.go
package handler

import (
    "net/http"
    "github.com/gin-gonic/gin"
    usecase "myproject/internal/usecase/user"
    "myproject/pkg/response"
)

type UserHandler struct {
    createUser *usecase.CreateUserUseCase
    findUser   *usecase.FindUserUseCase
}

func NewUserHandler(
    createUser *usecase.CreateUserUseCase,
    findUser *usecase.FindUserUseCase,
) *UserHandler {
    return &UserHandler{
        createUser: createUser,
        findUser:   findUser,
    }
}

type CreateUserRequest struct {
    Email    string `json:"email" binding:"required,email"`
    Name     string `json:"name" binding:"required,min=2,max=100"`
    Password string `json:"password" binding:"required,min=8"`
}

func (h *UserHandler) Create(c *gin.Context) {
    var req CreateUserRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        response.ValidationError(c, err)
        return
    }

    output, err := h.createUser.Execute(c.Request.Context(), usecase.CreateUserInput{
        Email:    req.Email,
        Name:     req.Name,
        Password: req.Password,
    })
    if err != nil {
        response.HandleError(c, err)
        return
    }

    response.Success(c, http.StatusCreated, output)
}
```

## Adapter Layer - Repository

```go
// internal/adapter/repository/postgres/user_repository.go
package postgres

import (
    "context"
    "database/sql"
    "time"

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

// Database model (different from domain entity)
type userRow struct {
    ID        uuid.UUID  `db:"id"`
    Email     string     `db:"email"`
    Name      string     `db:"name"`
    Password  string     `db:"password"`
    Status    string     `db:"status"`
    CreatedAt time.Time  `db:"created_at"`
    UpdatedAt time.Time  `db:"updated_at"`
    DeletedAt *time.Time `db:"deleted_at"`
}

func (r *UserRepository) FindByID(ctx context.Context, id uuid.UUID) (*user.User, error) {
    var row userRow
    query := `SELECT * FROM users WHERE id = $1 AND deleted_at IS NULL`

    if err := r.db.GetContext(ctx, &row, query, id); err != nil {
        if err == sql.ErrNoRows {
            return nil, user.ErrNotFound
        }
        return nil, err
    }

    return r.toDomain(&row), nil
}

func (r *UserRepository) Save(ctx context.Context, u *user.User) error {
    query := `
        INSERT INTO users (id, email, name, password, status, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        ON CONFLICT (id) DO UPDATE SET
            name = EXCLUDED.name,
            password = EXCLUDED.password,
            status = EXCLUDED.status,
            updated_at = EXCLUDED.updated_at
    `

    _, err := r.db.ExecContext(ctx, query,
        u.ID, u.Email, u.Name, u.Password, u.Status, u.CreatedAt, u.UpdatedAt,
    )
    return err
}

// Convert database model to domain entity
func (r *UserRepository) toDomain(row *userRow) *user.User {
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

## Dependency Flow

```
Domain (innermost)
   ↑ depends on nothing

Use Cases
   ↑ depends on Domain only

Adapters
   ↑ depends on Use Cases and Domain

Infrastructure (outermost)
   ↑ depends on everything
```

## Best Practices

1. **Domain is pure**: No external dependencies
2. **Use Cases orchestrate**: Business logic coordination
3. **Adapters translate**: Between external and internal formats
4. **Infrastructure wires**: Dependency injection at startup
5. **Interfaces at boundaries**: Define in the package that uses them
6. **Value objects for validation**: Encapsulate validation logic
