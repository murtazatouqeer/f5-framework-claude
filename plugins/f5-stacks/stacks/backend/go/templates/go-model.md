# Go Model Template

Template for creating domain models in Go applications.

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{entity_name}}` | Entity name (PascalCase) | User |
| `{{entity_name_lower}}` | Entity name (lowercase) | user |
| `{{package_name}}` | Package name | user |
| `{{fields}}` | Entity fields | ID, Email, Name |
| `{{module_path}}` | Go module path | myproject |

## Domain Entity Template

```go
// internal/domain/{{entity_name_lower}}/{{entity_name_lower}}.go
package {{package_name}}

import (
    "time"

    "github.com/google/uuid"
)

type {{entity_name}} struct {
    ID        uuid.UUID `json:"id"`
    {{#fields}}
    {{field_name}} {{field_type}} `json:"{{field_json}}"`
    {{/fields}}
    CreatedAt time.Time  `json:"created_at"`
    UpdatedAt time.Time  `json:"updated_at"`
    DeletedAt *time.Time `json:"deleted_at,omitempty"`
}

// New{{entity_name}} creates a new {{entity_name}} instance
func New{{entity_name}}({{constructor_params}}) (*{{entity_name}}, error) {
    now := time.Now()

    e := &{{entity_name}}{
        ID:        uuid.New(),
        {{#fields}}
        {{field_name}}: {{field_param}},
        {{/fields}}
        CreatedAt: now,
        UpdatedAt: now,
    }

    if err := e.Validate(); err != nil {
        return nil, err
    }

    return e, nil
}

// Validate validates the entity
func (e *{{entity_name}}) Validate() error {
    {{#validations}}
    if {{validation_condition}} {
        return Err{{validation_error}}
    }
    {{/validations}}
    return nil
}

// IsDeleted checks if entity is soft deleted
func (e *{{entity_name}}) IsDeleted() bool {
    return e.DeletedAt != nil
}
```

## Example: User Entity

```go
// internal/domain/user/user.go
package user

import (
    "time"

    "github.com/google/uuid"
    "golang.org/x/crypto/bcrypt"
)

type Status string

const (
    StatusActive   Status = "active"
    StatusInactive Status = "inactive"
    StatusBanned   Status = "banned"
)

type Role string

const (
    RoleAdmin Role = "admin"
    RoleUser  Role = "user"
    RoleGuest Role = "guest"
)

type Email string

func (e Email) String() string {
    return string(e)
}

type Password string

func (p Password) Compare(plain string) bool {
    return bcrypt.CompareHashAndPassword([]byte(p), []byte(plain)) == nil
}

type User struct {
    ID        uuid.UUID  `json:"id"`
    Email     Email      `json:"email"`
    Name      string     `json:"name"`
    Password  Password   `json:"-"`
    Status    Status     `json:"status"`
    Role      Role       `json:"role"`
    CreatedAt time.Time  `json:"created_at"`
    UpdatedAt time.Time  `json:"updated_at"`
    DeletedAt *time.Time `json:"deleted_at,omitempty"`
}

func NewUser(email, name, password string) (*User, error) {
    now := time.Now()

    hashedPassword, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
    if err != nil {
        return nil, err
    }

    u := &User{
        ID:        uuid.New(),
        Email:     Email(email),
        Name:      name,
        Password:  Password(hashedPassword),
        Status:    StatusActive,
        Role:      RoleUser,
        CreatedAt: now,
        UpdatedAt: now,
    }

    if err := u.Validate(); err != nil {
        return nil, err
    }

    return u, nil
}

func (u *User) Validate() error {
    if u.Email == "" {
        return ErrInvalidEmail
    }
    if u.Name == "" {
        return ErrInvalidName
    }
    return nil
}

func (u *User) IsActive() bool {
    return u.Status == StatusActive
}

func (u *User) IsAdmin() bool {
    return u.Role == RoleAdmin
}

func (u *User) Deactivate() {
    u.Status = StatusInactive
    u.UpdatedAt = time.Now()
}

func (u *User) Activate() {
    u.Status = StatusActive
    u.UpdatedAt = time.Now()
}
```

## Errors Template

```go
// internal/domain/{{entity_name_lower}}/errors.go
package {{package_name}}

import "errors"

var (
    ErrNotFound     = errors.New("{{entity_name_lower}} not found")
    ErrAlreadyExists = errors.New("{{entity_name_lower}} already exists")
    {{#error_definitions}}
    Err{{error_name}} = errors.New("{{error_message}}")
    {{/error_definitions}}
)
```

## Repository Interface Template

```go
// internal/domain/{{entity_name_lower}}/repository.go
package {{package_name}}

import (
    "context"

    "github.com/google/uuid"
)

type Repository interface {
    Create(ctx context.Context, entity *{{entity_name}}) error
    GetByID(ctx context.Context, id uuid.UUID) (*{{entity_name}}, error)
    Update(ctx context.Context, entity *{{entity_name}}) error
    Delete(ctx context.Context, id uuid.UUID) error
    List(ctx context.Context, filter Filter) ([]*{{entity_name}}, int64, error)
    {{#custom_methods}}
    {{method_signature}}
    {{/custom_methods}}
}

type Filter struct {
    {{#filter_fields}}
    {{field_name}} {{field_type}}
    {{/filter_fields}}
    Limit  int
    Offset int
    SortBy string
    Order  string
}
```

## Usage

```bash
# Generate user model
f5 generate model User --fields "email:string,name:string,status:enum"

# Generate order model with custom methods
f5 generate model Order --fields "user_id:uuid,total:decimal,status:enum" \
  --methods "GetByUserID,GetPending"
```
