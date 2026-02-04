# Error Handling Patterns

Implementing robust error handling in Go applications.

## Error Wrapping

```go
// pkg/errors/wrap.go
package errors

import (
    "errors"
    "fmt"
)

// Wrap adds context to an error
func Wrap(err error, message string) error {
    if err == nil {
        return nil
    }
    return fmt.Errorf("%s: %w", message, err)
}

// Wrapf adds formatted context to an error
func Wrapf(err error, format string, args ...interface{}) error {
    if err == nil {
        return nil
    }
    return fmt.Errorf("%s: %w", fmt.Sprintf(format, args...), err)
}

// Unwrap extracts the underlying error
func Unwrap(err error) error {
    return errors.Unwrap(err)
}

// Is checks if error matches target
func Is(err, target error) bool {
    return errors.Is(err, target)
}

// As extracts error of specific type
func As(err error, target interface{}) bool {
    return errors.As(err, target)
}
```

## Service Layer Error Handling

```go
// internal/service/user_service.go
package service

import (
    "context"
    "fmt"

    "myproject/internal/domain/user"
    "myproject/pkg/errors"
)

func (s *UserService) GetByID(ctx context.Context, id string) (*user.User, error) {
    // Validate input
    if id == "" {
        return nil, errors.ErrInvalidInput.WithMessage("user ID is required")
    }

    // Parse UUID
    uid, err := uuid.Parse(id)
    if err != nil {
        return nil, errors.ErrInvalidInput.WithMessagef("invalid user ID format: %s", id)
    }

    // Get from repository
    u, err := s.repo.GetByID(ctx, uid)
    if err != nil {
        if errors.Is(err, user.ErrNotFound) {
            return nil, errors.ErrNotFound.WithMessagef("user not found: %s", id)
        }
        return nil, errors.Wrap(err, "getting user from repository")
    }

    return u, nil
}

func (s *UserService) Create(ctx context.Context, input CreateUserInput) (*user.User, error) {
    // Check email uniqueness
    exists, err := s.repo.ExistsByEmail(ctx, input.Email)
    if err != nil {
        return nil, errors.Wrap(err, "checking email existence")
    }
    if exists {
        return nil, errors.ErrConflict.WithMessage("email already registered")
    }

    // Create domain entity
    u, err := user.New(input.Email, input.Name, input.Password)
    if err != nil {
        return nil, errors.Wrap(err, "creating user entity")
    }

    // Persist
    if err := s.repo.Create(ctx, u); err != nil {
        return nil, errors.Wrap(err, "saving user to database")
    }

    return u, nil
}
```

## Repository Layer Error Handling

```go
// internal/repository/postgres/user_repository.go
package postgres

import (
    "context"
    "database/sql"
    "fmt"
    "strings"

    "myproject/internal/domain/user"
    "myproject/pkg/errors"
)

func (r *userRepository) GetByID(ctx context.Context, id uuid.UUID) (*user.User, error) {
    var row userRow
    query := `SELECT * FROM users WHERE id = $1 AND deleted_at IS NULL`

    if err := r.db.GetContext(ctx, &row, query, id); err != nil {
        if err == sql.ErrNoRows {
            return nil, user.ErrNotFound
        }
        return nil, errors.Wrap(err, "executing query")
    }

    return row.toDomain(), nil
}

func (r *userRepository) Create(ctx context.Context, u *user.User) error {
    query := `
        INSERT INTO users (id, email, name, password, status, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    `

    _, err := r.db.ExecContext(ctx, query,
        u.ID, u.Email, u.Name, u.Password, u.Status, u.CreatedAt, u.UpdatedAt,
    )
    if err != nil {
        // Check for unique constraint violation
        if strings.Contains(err.Error(), "duplicate key") {
            if strings.Contains(err.Error(), "email") {
                return user.ErrEmailExists
            }
            return errors.ErrConflict.WithMessage("duplicate entry")
        }
        return errors.Wrap(err, "executing insert")
    }

    return nil
}
```

## Handler Layer Error Handling

```go
// internal/handler/user_handler.go
package handler

import (
    "net/http"

    "github.com/gin-gonic/gin"

    "myproject/pkg/errors"
    "myproject/pkg/response"
)

func (h *UserHandler) Get(c *gin.Context) {
    id := c.Param("id")

    user, err := h.service.GetByID(c.Request.Context(), id)
    if err != nil {
        handleError(c, err)
        return
    }

    response.Success(c, http.StatusOK, user)
}

func handleError(c *gin.Context, err error) {
    var appErr *errors.AppError
    if errors.As(err, &appErr) {
        response.Error(c, appErr.HTTPStatus(), appErr.Code, appErr.Message)
        return
    }

    // Fallback for unexpected errors
    response.Error(c, http.StatusInternalServerError, "INTERNAL_ERROR", "An unexpected error occurred")
}
```

## Error Response Format

```go
// pkg/response/error.go
package response

import (
    "github.com/gin-gonic/gin"

    "myproject/pkg/errors"
    "myproject/pkg/validator"
)

type ErrorResponse struct {
    Error ErrorDetail `json:"error"`
}

type ErrorDetail struct {
    Code    string                      `json:"code"`
    Message string                      `json:"message"`
    Details []validator.ValidationError `json:"details,omitempty"`
}

func Error(c *gin.Context, status int, code, message string) {
    c.JSON(status, ErrorResponse{
        Error: ErrorDetail{
            Code:    code,
            Message: message,
        },
    })
}

func ValidationError(c *gin.Context, errs validator.ValidationErrors) {
    c.JSON(400, ErrorResponse{
        Error: ErrorDetail{
            Code:    "VALIDATION_ERROR",
            Message: "Invalid input",
            Details: errs,
        },
    })
}

func HandleError(c *gin.Context, err error) {
    var appErr *errors.AppError
    if errors.As(err, &appErr) {
        Error(c, appErr.HTTPStatus(), appErr.Code, appErr.Message)
        return
    }

    Error(c, 500, "INTERNAL_ERROR", "An unexpected error occurred")
}
```

## Panic Recovery

```go
// internal/middleware/recovery.go
package middleware

import (
    "net/http"
    "runtime/debug"

    "github.com/gin-gonic/gin"
    "go.uber.org/zap"

    "myproject/pkg/response"
)

func Recovery(logger *zap.Logger) gin.HandlerFunc {
    return func(c *gin.Context) {
        defer func() {
            if r := recover(); r != nil {
                // Log the panic with stack trace
                logger.Error("Panic recovered",
                    zap.Any("panic", r),
                    zap.String("stack", string(debug.Stack())),
                    zap.String("path", c.Request.URL.Path),
                    zap.String("method", c.Request.Method),
                )

                response.Error(c, http.StatusInternalServerError,
                    "INTERNAL_ERROR", "An unexpected error occurred")
                c.Abort()
            }
        }()
        c.Next()
    }
}
```

## Error Logging

```go
// internal/middleware/error_logger.go
package middleware

import (
    "github.com/gin-gonic/gin"
    "go.uber.org/zap"

    "myproject/pkg/errors"
)

func ErrorLogger(logger *zap.Logger) gin.HandlerFunc {
    return func(c *gin.Context) {
        c.Next()

        // Log any errors that occurred
        for _, ginErr := range c.Errors {
            var appErr *errors.AppError
            if errors.As(ginErr.Err, &appErr) {
                if appErr.IsServerError() {
                    logger.Error("Server error",
                        zap.Error(ginErr.Err),
                        zap.String("path", c.Request.URL.Path),
                        zap.String("method", c.Request.Method),
                        zap.String("request_id", c.GetString("request_id")),
                    )
                } else {
                    logger.Warn("Client error",
                        zap.Error(ginErr.Err),
                        zap.String("path", c.Request.URL.Path),
                    )
                }
            } else {
                logger.Error("Unhandled error",
                    zap.Error(ginErr.Err),
                    zap.String("path", c.Request.URL.Path),
                )
            }
        }
    }
}
```

## Error Handling Chain

```go
// Example: Complete error handling flow
// 1. Repository detects DB error
// 2. Service wraps with context
// 3. Handler converts to HTTP response
// 4. Middleware logs appropriately

// Repository
func (r *repo) GetByID(ctx context.Context, id uuid.UUID) (*Entity, error) {
    err := r.db.GetContext(ctx, &row, query, id)
    if err == sql.ErrNoRows {
        return nil, domain.ErrNotFound  // Domain error
    }
    return nil, errors.Wrap(err, "database query failed")
}

// Service
func (s *service) Get(ctx context.Context, id string) (*Entity, error) {
    entity, err := s.repo.GetByID(ctx, parsedID)
    if err != nil {
        if errors.Is(err, domain.ErrNotFound) {
            return nil, errors.ErrNotFound.WithMessagef("entity %s not found", id)
        }
        return nil, errors.Wrap(err, "fetching entity")
    }
    return entity, nil
}

// Handler
func (h *handler) Get(c *gin.Context) {
    entity, err := h.service.Get(ctx, id)
    if err != nil {
        response.HandleError(c, err)  // Converts to HTTP response
        return
    }
    response.Success(c, 200, entity)
}
```

## Best Practices

1. **Wrap Errors**: Add context at each layer
2. **Domain Errors**: Define errors in domain layer
3. **Error Types**: Use typed errors for different categories
4. **Log Once**: Log at the boundary, not at every layer
5. **User Messages**: Separate internal and user-facing messages
6. **Stack Traces**: Include stack traces for server errors
