# Custom Validation

Implementing custom validation rules in Go applications.

## Custom Validation Functions

```go
// pkg/validator/custom.go
package validator

import (
    "regexp"
    "strings"
    "unicode"

    "github.com/go-playground/validator/v10"
)

func RegisterCustomValidations(v *validator.Validate) {
    // Password strength
    v.RegisterValidation("password", validatePassword)

    // Username format
    v.RegisterValidation("username", validateUsername)

    // Slug format
    v.RegisterValidation("slug", validateSlug)

    // Japanese phone
    v.RegisterValidation("jp_phone", validateJPPhone)

    // No whitespace
    v.RegisterValidation("notblank", validateNotBlank)

    // Safe string (no special chars)
    v.RegisterValidation("safestring", validateSafeString)
}

// Password requires: min 8 chars, 1 upper, 1 lower, 1 digit, 1 special
func validatePassword(fl validator.FieldLevel) bool {
    password := fl.Field().String()

    if len(password) < 8 {
        return false
    }

    var hasUpper, hasLower, hasDigit, hasSpecial bool

    for _, char := range password {
        switch {
        case unicode.IsUpper(char):
            hasUpper = true
        case unicode.IsLower(char):
            hasLower = true
        case unicode.IsDigit(char):
            hasDigit = true
        case unicode.IsPunct(char) || unicode.IsSymbol(char):
            hasSpecial = true
        }
    }

    return hasUpper && hasLower && hasDigit && hasSpecial
}

// Username: alphanumeric, underscore, 3-20 chars
func validateUsername(fl validator.FieldLevel) bool {
    username := fl.Field().String()
    match, _ := regexp.MatchString(`^[a-zA-Z0-9_]{3,20}$`, username)
    return match
}

// Slug: lowercase, alphanumeric, hyphens
func validateSlug(fl validator.FieldLevel) bool {
    slug := fl.Field().String()
    match, _ := regexp.MatchString(`^[a-z0-9]+(-[a-z0-9]+)*$`, slug)
    return match
}

// Japanese phone: 0X0-XXXX-XXXX format
func validateJPPhone(fl validator.FieldLevel) bool {
    phone := fl.Field().String()
    match, _ := regexp.MatchString(`^0\d{1,4}-\d{1,4}-\d{4}$`, phone)
    return match
}

// Not blank: not empty or only whitespace
func validateNotBlank(fl validator.FieldLevel) bool {
    return strings.TrimSpace(fl.Field().String()) != ""
}

// Safe string: no SQL injection chars
func validateSafeString(fl validator.FieldLevel) bool {
    s := fl.Field().String()
    dangerous := []string{"'", "\"", ";", "--", "/*", "*/", "xp_"}
    for _, d := range dangerous {
        if strings.Contains(strings.ToLower(s), d) {
            return false
        }
    }
    return true
}
```

## Cross-Field Validation

```go
// pkg/validator/cross_field.go
package validator

import (
    "reflect"

    "github.com/go-playground/validator/v10"
)

func RegisterCrossFieldValidations(v *validator.Validate) {
    // Password confirmation
    v.RegisterValidation("eqfield", validateEqField)

    // Date range
    v.RegisterStructValidation(validateDateRange, DateRangeRequest{})

    // Conditional required
    v.RegisterStructValidation(validateConditionalRequired, PaymentRequest{})
}

type DateRangeRequest struct {
    StartDate string `json:"start_date" validate:"required,datetime=2006-01-02"`
    EndDate   string `json:"end_date" validate:"required,datetime=2006-01-02"`
}

func validateDateRange(sl validator.StructLevel) {
    req := sl.Current().Interface().(DateRangeRequest)

    if req.StartDate >= req.EndDate {
        sl.ReportError(req.EndDate, "end_date", "EndDate", "gtfield", "start_date")
    }
}

type PaymentRequest struct {
    Method     string `json:"method" validate:"required,oneof=card bank crypto"`
    CardNumber string `json:"card_number"`
    BankCode   string `json:"bank_code"`
    WalletAddr string `json:"wallet_address"`
}

func validateConditionalRequired(sl validator.StructLevel) {
    req := sl.Current().Interface().(PaymentRequest)

    switch req.Method {
    case "card":
        if req.CardNumber == "" {
            sl.ReportError(req.CardNumber, "card_number", "CardNumber", "required_if", "method=card")
        }
    case "bank":
        if req.BankCode == "" {
            sl.ReportError(req.BankCode, "bank_code", "BankCode", "required_if", "method=bank")
        }
    case "crypto":
        if req.WalletAddr == "" {
            sl.ReportError(req.WalletAddr, "wallet_address", "WalletAddress", "required_if", "method=crypto")
        }
    }
}
```

## Validation with Database Lookup

```go
// pkg/validator/db_validator.go
package validator

import (
    "context"

    "github.com/go-playground/validator/v10"
)

type DBValidator struct {
    userRepo UserRepository
    tagRepo  TagRepository
}

type UserRepository interface {
    ExistsByEmail(ctx context.Context, email string) (bool, error)
    ExistsByUsername(ctx context.Context, username string) (bool, error)
}

type TagRepository interface {
    ExistsByIDs(ctx context.Context, ids []string) (bool, error)
}

func NewDBValidator(userRepo UserRepository, tagRepo TagRepository) *DBValidator {
    return &DBValidator{
        userRepo: userRepo,
        tagRepo:  tagRepo,
    }
}

func (d *DBValidator) Register(v *validator.Validate) {
    v.RegisterValidationCtx("unique_email", d.validateUniqueEmail)
    v.RegisterValidationCtx("unique_username", d.validateUniqueUsername)
    v.RegisterValidationCtx("valid_tags", d.validateTags)
}

func (d *DBValidator) validateUniqueEmail(ctx context.Context, fl validator.FieldLevel) bool {
    email := fl.Field().String()
    exists, err := d.userRepo.ExistsByEmail(ctx, email)
    if err != nil {
        return false
    }
    return !exists
}

func (d *DBValidator) validateUniqueUsername(ctx context.Context, fl validator.FieldLevel) bool {
    username := fl.Field().String()
    exists, err := d.userRepo.ExistsByUsername(ctx, username)
    if err != nil {
        return false
    }
    return !exists
}

func (d *DBValidator) validateTags(ctx context.Context, fl validator.FieldLevel) bool {
    tags := fl.Field().Interface().([]string)
    if len(tags) == 0 {
        return true
    }

    exists, err := d.tagRepo.ExistsByIDs(ctx, tags)
    if err != nil {
        return false
    }
    return exists
}

// Usage
type CreatePostRequest struct {
    Title  string   `json:"title" validate:"required,min=5,max=200"`
    Body   string   `json:"body" validate:"required,min=10"`
    Tags   []string `json:"tags" validate:"omitempty,max=5,dive,uuid,valid_tags"`
    Author string   `json:"author" validate:"required,uuid"`
}
```

## Reusable Validation Rules

```go
// pkg/validator/rules.go
package validator

import (
    "regexp"
    "time"

    "github.com/go-playground/validator/v10"
)

// Common regex patterns
var (
    usernameRegex = regexp.MustCompile(`^[a-zA-Z0-9_]{3,20}$`)
    slugRegex     = regexp.MustCompile(`^[a-z0-9]+(-[a-z0-9]+)*$`)
    hexColorRegex = regexp.MustCompile(`^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$`)
    urlRegex      = regexp.MustCompile(`^https?://[^\s]+$`)
)

// RegisterAllValidations registers all custom validations
func RegisterAllValidations(v *validator.Validate) error {
    validations := map[string]validator.Func{
        "username":  validateUsernameRule,
        "slug":      validateSlugRule,
        "hexcolor":  validateHexColor,
        "http_url":  validateHTTPURL,
        "future":    validateFutureDate,
        "past":      validatePastDate,
        "age":       validateAge,
        "file_ext":  validateFileExtension,
    }

    for name, fn := range validations {
        if err := v.RegisterValidation(name, fn); err != nil {
            return err
        }
    }

    return nil
}

func validateUsernameRule(fl validator.FieldLevel) bool {
    return usernameRegex.MatchString(fl.Field().String())
}

func validateSlugRule(fl validator.FieldLevel) bool {
    return slugRegex.MatchString(fl.Field().String())
}

func validateHexColor(fl validator.FieldLevel) bool {
    return hexColorRegex.MatchString(fl.Field().String())
}

func validateHTTPURL(fl validator.FieldLevel) bool {
    return urlRegex.MatchString(fl.Field().String())
}

func validateFutureDate(fl validator.FieldLevel) bool {
    t, ok := fl.Field().Interface().(time.Time)
    if !ok {
        return false
    }
    return t.After(time.Now())
}

func validatePastDate(fl validator.FieldLevel) bool {
    t, ok := fl.Field().Interface().(time.Time)
    if !ok {
        return false
    }
    return t.Before(time.Now())
}

func validateAge(fl validator.FieldLevel) bool {
    birthDate, ok := fl.Field().Interface().(time.Time)
    if !ok {
        return false
    }

    age := time.Now().Year() - birthDate.Year()
    if time.Now().YearDay() < birthDate.YearDay() {
        age--
    }

    param := fl.Param()
    var minAge int
    if param != "" {
        minAge = 18 // Default
    }

    return age >= minAge
}

func validateFileExtension(fl validator.FieldLevel) bool {
    filename := fl.Field().String()
    allowedExts := map[string]bool{
        ".jpg": true, ".jpeg": true, ".png": true, ".gif": true,
        ".pdf": true, ".doc": true, ".docx": true,
    }

    for ext := range allowedExts {
        if len(filename) > len(ext) && filename[len(filename)-len(ext):] == ext {
            return true
        }
    }
    return false
}
```

## Validation Middleware

```go
// internal/middleware/validation.go
package middleware

import (
    "net/http"
    "reflect"

    "github.com/gin-gonic/gin"

    "myproject/pkg/response"
    "myproject/pkg/validator"
)

// ValidateRequest validates request body against a type
func ValidateRequest[T any]() gin.HandlerFunc {
    return func(c *gin.Context) {
        var req T

        if err := c.ShouldBindJSON(&req); err != nil {
            response.Error(c, http.StatusBadRequest, "INVALID_JSON", "Invalid request body")
            c.Abort()
            return
        }

        if err := validator.Struct(&req); err != nil {
            errors := validator.FormatErrors(err)
            response.ValidationError(c, errors)
            c.Abort()
            return
        }

        // Store validated request in context
        c.Set("validated_request", req)
        c.Next()
    }
}

// GetValidatedRequest retrieves validated request from context
func GetValidatedRequest[T any](c *gin.Context) T {
    req, _ := c.Get("validated_request")
    return req.(T)
}

// Usage
router.POST("/users",
    middleware.ValidateRequest[dto.CreateUserRequest](),
    userHandler.Create,
)

func (h *UserHandler) Create(c *gin.Context) {
    req := middleware.GetValidatedRequest[dto.CreateUserRequest](c)
    // Request is already validated
}
```

## Best Practices

1. **Register Early**: Register custom validations at startup
2. **Meaningful Names**: Use descriptive validation tag names
3. **Compile Regex Once**: Use package-level compiled regex
4. **Context Validation**: Use context for async/DB validations
5. **Clear Messages**: Provide user-friendly error messages
6. **Separate Concerns**: Keep validation logic in dedicated package
