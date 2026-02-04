# GORM Patterns

Best practices for using GORM ORM in Go applications.

## Connection Setup

```go
// pkg/database/gorm.go
package database

import (
    "fmt"
    "time"

    "gorm.io/driver/postgres"
    "gorm.io/gorm"
    "gorm.io/gorm/logger"
)

type GormConfig struct {
    DSN             string
    MaxOpenConns    int
    MaxIdleConns    int
    ConnMaxLifetime time.Duration
    LogLevel        logger.LogLevel
}

func NewGorm(cfg GormConfig) (*gorm.DB, error) {
    db, err := gorm.Open(postgres.Open(cfg.DSN), &gorm.Config{
        Logger: logger.Default.LogMode(cfg.LogLevel),
        NowFunc: func() time.Time {
            return time.Now().UTC()
        },
        PrepareStmt: true, // Cache prepared statements
    })
    if err != nil {
        return nil, fmt.Errorf("opening database: %w", err)
    }

    sqlDB, err := db.DB()
    if err != nil {
        return nil, fmt.Errorf("getting sql.DB: %w", err)
    }

    sqlDB.SetMaxOpenConns(cfg.MaxOpenConns)
    sqlDB.SetMaxIdleConns(cfg.MaxIdleConns)
    sqlDB.SetConnMaxLifetime(cfg.ConnMaxLifetime)

    return db, nil
}
```

## Model Definition

```go
// internal/repository/gorm/models.go
package gorm

import (
    "time"

    "github.com/google/uuid"
    "gorm.io/gorm"
)

// Base model with common fields
type BaseModel struct {
    ID        uuid.UUID      `gorm:"type:uuid;primary_key;default:gen_random_uuid()"`
    CreatedAt time.Time      `gorm:"autoCreateTime"`
    UpdatedAt time.Time      `gorm:"autoUpdateTime"`
    DeletedAt gorm.DeletedAt `gorm:"index"`
}

type User struct {
    BaseModel
    Email    string `gorm:"uniqueIndex;not null;size:255"`
    Name     string `gorm:"not null;size:100"`
    Password string `gorm:"not null"`
    Status   string `gorm:"not null;default:'active';size:20"`
    Role     string `gorm:"not null;default:'user';size:20"`

    // Relations
    Profile  *Profile  `gorm:"foreignKey:UserID"`
    Posts    []Post    `gorm:"foreignKey:AuthorID"`
    Comments []Comment `gorm:"foreignKey:UserID"`
}

func (User) TableName() string {
    return "users"
}

type Profile struct {
    BaseModel
    UserID    uuid.UUID `gorm:"type:uuid;uniqueIndex"`
    Bio       *string   `gorm:"type:text"`
    AvatarURL *string   `gorm:"size:500"`
    User      *User     `gorm:"foreignKey:UserID"`
}

type Post struct {
    BaseModel
    Title    string    `gorm:"not null;size:255"`
    Content  string    `gorm:"type:text"`
    Status   string    `gorm:"not null;default:'draft';size:20"`
    AuthorID uuid.UUID `gorm:"type:uuid;index"`
    Author   *User     `gorm:"foreignKey:AuthorID"`
    Tags     []Tag     `gorm:"many2many:post_tags;"`
}

type Tag struct {
    BaseModel
    Name  string `gorm:"uniqueIndex;not null;size:50"`
    Posts []Post `gorm:"many2many:post_tags;"`
}
```

## Repository Implementation

```go
// internal/repository/gorm/user_repository.go
package gorm

import (
    "context"
    "errors"

    "github.com/google/uuid"
    "gorm.io/gorm"

    "myproject/internal/domain/user"
)

type UserRepository struct {
    db *gorm.DB
}

func NewUserRepository(db *gorm.DB) *UserRepository {
    return &UserRepository{db: db}
}

// Create
func (r *UserRepository) Create(ctx context.Context, u *user.User) error {
    model := toModel(u)
    result := r.db.WithContext(ctx).Create(model)
    if result.Error != nil {
        if errors.Is(result.Error, gorm.ErrDuplicatedKey) {
            return user.ErrAlreadyExists
        }
        return result.Error
    }
    return nil
}

// GetByID
func (r *UserRepository) GetByID(ctx context.Context, id uuid.UUID) (*user.User, error) {
    var model User
    result := r.db.WithContext(ctx).First(&model, "id = ?", id)
    if result.Error != nil {
        if errors.Is(result.Error, gorm.ErrRecordNotFound) {
            return nil, user.ErrNotFound
        }
        return nil, result.Error
    }
    return toDomain(&model), nil
}

// GetByEmail
func (r *UserRepository) GetByEmail(ctx context.Context, email string) (*user.User, error) {
    var model User
    result := r.db.WithContext(ctx).Where("email = ?", email).First(&model)
    if result.Error != nil {
        if errors.Is(result.Error, gorm.ErrRecordNotFound) {
            return nil, user.ErrNotFound
        }
        return nil, result.Error
    }
    return toDomain(&model), nil
}

// List with filters
func (r *UserRepository) List(ctx context.Context, filter user.Filter) ([]*user.User, int64, error) {
    var models []User
    var total int64

    query := r.db.WithContext(ctx).Model(&User{})

    // Apply filters
    if filter.Search != nil && *filter.Search != "" {
        search := "%" + *filter.Search + "%"
        query = query.Where("name ILIKE ? OR email ILIKE ?", search, search)
    }

    if filter.Status != nil {
        query = query.Where("status = ?", *filter.Status)
    }

    if filter.Role != nil {
        query = query.Where("role = ?", *filter.Role)
    }

    // Count total
    if err := query.Count(&total).Error; err != nil {
        return nil, 0, err
    }

    // Apply sorting
    sortBy := "created_at"
    if filter.SortBy != "" {
        sortBy = filter.SortBy
    }
    order := "DESC"
    if filter.Order == "ASC" {
        order = "ASC"
    }

    // Fetch with pagination
    result := query.
        Order(sortBy + " " + order).
        Offset(filter.Offset).
        Limit(filter.Limit).
        Find(&models)

    if result.Error != nil {
        return nil, 0, result.Error
    }

    users := make([]*user.User, len(models))
    for i, model := range models {
        users[i] = toDomain(&model)
    }

    return users, total, nil
}

// Update
func (r *UserRepository) Update(ctx context.Context, u *user.User) error {
    result := r.db.WithContext(ctx).
        Model(&User{}).
        Where("id = ?", u.ID).
        Updates(map[string]interface{}{
            "name":   u.Name,
            "status": u.Status,
        })

    if result.Error != nil {
        return result.Error
    }
    if result.RowsAffected == 0 {
        return user.ErrNotFound
    }
    return nil
}

// Delete (soft delete)
func (r *UserRepository) Delete(ctx context.Context, id uuid.UUID) error {
    result := r.db.WithContext(ctx).Delete(&User{}, "id = ?", id)
    if result.Error != nil {
        return result.Error
    }
    if result.RowsAffected == 0 {
        return user.ErrNotFound
    }
    return nil
}

// Mapping functions
func toModel(u *user.User) *User {
    return &User{
        BaseModel: BaseModel{ID: u.ID},
        Email:     string(u.Email),
        Name:      u.Name,
        Password:  string(u.Password),
        Status:    string(u.Status),
    }
}

func toDomain(m *User) *user.User {
    return &user.User{
        ID:        m.ID,
        Email:     user.Email(m.Email),
        Name:      m.Name,
        Password:  user.HashedPassword(m.Password),
        Status:    user.Status(m.Status),
        CreatedAt: m.CreatedAt,
        UpdatedAt: m.UpdatedAt,
    }
}
```

## Preloading Relations

```go
// Get user with profile
func (r *UserRepository) GetWithProfile(ctx context.Context, id uuid.UUID) (*user.User, error) {
    var model User
    result := r.db.WithContext(ctx).
        Preload("Profile").
        First(&model, "id = ?", id)

    if result.Error != nil {
        if errors.Is(result.Error, gorm.ErrRecordNotFound) {
            return nil, user.ErrNotFound
        }
        return nil, result.Error
    }

    return toDomainWithProfile(&model), nil
}

// Get posts with author and tags
func (r *PostRepository) GetWithRelations(ctx context.Context, id uuid.UUID) (*Post, error) {
    var model Post
    result := r.db.WithContext(ctx).
        Preload("Author").
        Preload("Tags").
        First(&model, "id = ?", id)

    return &model, result.Error
}

// Nested preloading
func (r *PostRepository) GetFullPost(ctx context.Context, id uuid.UUID) (*Post, error) {
    var model Post
    result := r.db.WithContext(ctx).
        Preload("Author.Profile").  // Nested
        Preload("Tags").
        Preload("Comments", func(db *gorm.DB) *gorm.DB {
            return db.Order("created_at DESC").Limit(10)  // Conditional
        }).
        First(&model, "id = ?", id)

    return &model, result.Error
}
```

## Transactions

```go
// Transaction wrapper
func (r *UserRepository) WithTransaction(fn func(tx *gorm.DB) error) error {
    return r.db.Transaction(fn)
}

// Using transaction
func (r *UserRepository) CreateWithProfile(ctx context.Context, u *user.User, p *Profile) error {
    return r.db.WithContext(ctx).Transaction(func(tx *gorm.DB) error {
        // Create user
        userModel := toModel(u)
        if err := tx.Create(userModel).Error; err != nil {
            return err
        }

        // Create profile
        p.UserID = userModel.ID
        if err := tx.Create(p).Error; err != nil {
            return err
        }

        return nil
    })
}
```

## Scopes (Reusable Queries)

```go
// Define scopes
func Active(db *gorm.DB) *gorm.DB {
    return db.Where("status = ?", "active")
}

func ByRole(role string) func(db *gorm.DB) *gorm.DB {
    return func(db *gorm.DB) *gorm.DB {
        return db.Where("role = ?", role)
    }
}

func Paginate(page, pageSize int) func(db *gorm.DB) *gorm.DB {
    return func(db *gorm.DB) *gorm.DB {
        offset := (page - 1) * pageSize
        return db.Offset(offset).Limit(pageSize)
    }
}

func OrderByLatest(db *gorm.DB) *gorm.DB {
    return db.Order("created_at DESC")
}

// Using scopes
func (r *UserRepository) ListActiveAdmins(ctx context.Context, page, pageSize int) ([]User, error) {
    var users []User
    result := r.db.WithContext(ctx).
        Scopes(Active, ByRole("admin"), Paginate(page, pageSize), OrderByLatest).
        Find(&users)
    return users, result.Error
}
```

## Hooks

```go
// BeforeCreate hook
func (u *User) BeforeCreate(tx *gorm.DB) error {
    if u.ID == uuid.Nil {
        u.ID = uuid.New()
    }
    return nil
}

// AfterCreate hook
func (u *User) AfterCreate(tx *gorm.DB) error {
    // Send welcome email, etc.
    return nil
}

// BeforeUpdate hook
func (u *User) BeforeUpdate(tx *gorm.DB) error {
    // Validate before update
    return nil
}
```

## Best Practices

1. **Use Contexts**: Always pass context for cancellation
2. **Avoid SELECT ***: Use Select() for specific columns
3. **Batch Operations**: Use CreateInBatches for bulk inserts
4. **Index Queries**: Ensure indexes on filtered columns
5. **Preload Wisely**: Only preload needed relations
6. **Use Scopes**: Create reusable query components
