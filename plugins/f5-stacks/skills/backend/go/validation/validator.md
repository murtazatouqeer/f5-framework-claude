# Input Validation

Implementing input validation in Go applications using go-playground/validator.

## Setup

```bash
go get github.com/go-playground/validator/v10
```

## Basic Validation

```go
// pkg/validator/validator.go
package validator

import (
    "reflect"
    "strings"
    "sync"

    "github.com/go-playground/validator/v10"
)

var (
    validate *validator.Validate
    once     sync.Once
)

func Get() *validator.Validate {
    once.Do(func() {
        validate = validator.New()

        // Use JSON tag names in errors
        validate.RegisterTagNameFunc(func(fld reflect.StructField) string {
            name := strings.SplitN(fld.Tag.Get("json"), ",", 2)[0]
            if name == "-" {
                return ""
            }
            return name
        })
    })
    return validate
}

func Struct(s interface{}) error {
    return Get().Struct(s)
}

func Var(field interface{}, tag string) error {
    return Get().Var(field, tag)
}
```

## Validation Tags

```go
// internal/dto/user_dto.go
package dto

type CreateUserRequest struct {
    Email     string `json:"email" validate:"required,email,max=255"`
    Password  string `json:"password" validate:"required,min=8,max=72"`
    Name      string `json:"name" validate:"required,min=2,max=100"`
    Age       int    `json:"age" validate:"omitempty,gte=18,lte=150"`
    Phone     string `json:"phone" validate:"omitempty,e164"`
    Role      string `json:"role" validate:"omitempty,oneof=admin user guest"`
}

type UpdateUserRequest struct {
    Name  *string `json:"name" validate:"omitempty,min=2,max=100"`
    Email *string `json:"email" validate:"omitempty,email,max=255"`
    Age   *int    `json:"age" validate:"omitempty,gte=18,lte=150"`
}

type LoginRequest struct {
    Email    string `json:"email" validate:"required,email"`
    Password string `json:"password" validate:"required"`
}

type PaginationRequest struct {
    Page    int    `json:"page" validate:"gte=1"`
    PerPage int    `json:"per_page" validate:"gte=1,lte=100"`
    SortBy  string `json:"sort_by" validate:"omitempty,oneof=created_at updated_at name"`
    Order   string `json:"order" validate:"omitempty,oneof=asc desc"`
}
```

## Common Validation Tags

| Tag | Description | Example |
|-----|-------------|---------|
| `required` | Field must be present | `validate:"required"` |
| `email` | Must be valid email | `validate:"email"` |
| `min` | Minimum length/value | `validate:"min=8"` |
| `max` | Maximum length/value | `validate:"max=100"` |
| `len` | Exact length | `validate:"len=10"` |
| `gte` | Greater than or equal | `validate:"gte=18"` |
| `lte` | Less than or equal | `validate:"lte=100"` |
| `oneof` | Must be one of values | `validate:"oneof=a b c"` |
| `e164` | E.164 phone format | `validate:"e164"` |
| `url` | Must be valid URL | `validate:"url"` |
| `uuid` | Must be valid UUID | `validate:"uuid"` |
| `alpha` | Alphabetic only | `validate:"alpha"` |
| `alphanum` | Alphanumeric only | `validate:"alphanum"` |

## Error Handling

```go
// pkg/validator/errors.go
package validator

import (
    "fmt"

    "github.com/go-playground/validator/v10"
)

type ValidationError struct {
    Field   string `json:"field"`
    Tag     string `json:"tag"`
    Value   string `json:"value,omitempty"`
    Message string `json:"message"`
}

type ValidationErrors []ValidationError

func (v ValidationErrors) Error() string {
    if len(v) == 0 {
        return "validation failed"
    }
    return fmt.Sprintf("validation failed: %s", v[0].Message)
}

func FormatErrors(err error) ValidationErrors {
    var errors ValidationErrors

    validationErrs, ok := err.(validator.ValidationErrors)
    if !ok {
        return ValidationErrors{{Message: err.Error()}}
    }

    for _, e := range validationErrs {
        errors = append(errors, ValidationError{
            Field:   e.Field(),
            Tag:     e.Tag(),
            Value:   fmt.Sprintf("%v", e.Value()),
            Message: formatMessage(e),
        })
    }

    return errors
}

func formatMessage(e validator.FieldError) string {
    switch e.Tag() {
    case "required":
        return fmt.Sprintf("%s is required", e.Field())
    case "email":
        return fmt.Sprintf("%s must be a valid email", e.Field())
    case "min":
        return fmt.Sprintf("%s must be at least %s characters", e.Field(), e.Param())
    case "max":
        return fmt.Sprintf("%s must be at most %s characters", e.Field(), e.Param())
    case "gte":
        return fmt.Sprintf("%s must be greater than or equal to %s", e.Field(), e.Param())
    case "lte":
        return fmt.Sprintf("%s must be less than or equal to %s", e.Field(), e.Param())
    case "oneof":
        return fmt.Sprintf("%s must be one of: %s", e.Field(), e.Param())
    case "uuid":
        return fmt.Sprintf("%s must be a valid UUID", e.Field())
    default:
        return fmt.Sprintf("%s failed on %s validation", e.Field(), e.Tag())
    }
}
```

## Handler Integration

```go
// internal/handler/user_handler.go
package handler

import (
    "net/http"

    "github.com/gin-gonic/gin"

    "myproject/internal/dto"
    "myproject/pkg/response"
    "myproject/pkg/validator"
)

func (h *UserHandler) Create(c *gin.Context) {
    var req dto.CreateUserRequest

    if err := c.ShouldBindJSON(&req); err != nil {
        response.Error(c, http.StatusBadRequest, "INVALID_JSON", err.Error())
        return
    }

    if err := validator.Struct(&req); err != nil {
        errors := validator.FormatErrors(err)
        response.ValidationError(c, errors)
        return
    }

    // Proceed with creation
    user, err := h.service.Create(c.Request.Context(), req)
    if err != nil {
        response.HandleError(c, err)
        return
    }

    response.Success(c, http.StatusCreated, user)
}
```

## Gin Binding with Validation

```go
// pkg/binding/binding.go
package binding

import (
    "net/http"

    "github.com/gin-gonic/gin"

    "myproject/pkg/response"
    "myproject/pkg/validator"
)

// BindAndValidate binds request and validates
func BindAndValidate(c *gin.Context, obj interface{}) bool {
    if err := c.ShouldBindJSON(obj); err != nil {
        response.Error(c, http.StatusBadRequest, "INVALID_JSON", "Invalid request body")
        return false
    }

    if err := validator.Struct(obj); err != nil {
        errors := validator.FormatErrors(err)
        response.ValidationError(c, errors)
        return false
    }

    return true
}

// BindQuery binds query parameters and validates
func BindQuery(c *gin.Context, obj interface{}) bool {
    if err := c.ShouldBindQuery(obj); err != nil {
        response.Error(c, http.StatusBadRequest, "INVALID_QUERY", "Invalid query parameters")
        return false
    }

    if err := validator.Struct(obj); err != nil {
        errors := validator.FormatErrors(err)
        response.ValidationError(c, errors)
        return false
    }

    return true
}

// Usage in handler
func (h *UserHandler) Create(c *gin.Context) {
    var req dto.CreateUserRequest
    if !binding.BindAndValidate(c, &req) {
        return
    }
    // Proceed with validated request
}
```

## Best Practices

1. **Use JSON Tags**: Register tag name func to use JSON field names
2. **Centralize Validator**: Single instance with sync.Once
3. **Custom Messages**: Provide user-friendly error messages
4. **DTO Validation**: Validate DTOs before business logic
5. **Optional Fields**: Use `omitempty` for optional fields
6. **Pointer Fields**: Use pointers for partial updates
