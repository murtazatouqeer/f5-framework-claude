# Custom Errors

Implementing custom error types for Go applications.

## Application Error Type

```go
// pkg/errors/app_error.go
package errors

import (
    "fmt"
    "net/http"
)

// ErrorCode represents application error codes
type ErrorCode string

const (
    CodeInvalidInput     ErrorCode = "INVALID_INPUT"
    CodeNotFound         ErrorCode = "NOT_FOUND"
    CodeConflict         ErrorCode = "CONFLICT"
    CodeUnauthorized     ErrorCode = "UNAUTHORIZED"
    CodeForbidden        ErrorCode = "FORBIDDEN"
    CodeInternal         ErrorCode = "INTERNAL_ERROR"
    CodeServiceUnavailable ErrorCode = "SERVICE_UNAVAILABLE"
    CodeTimeout          ErrorCode = "TIMEOUT"
    CodeRateLimited      ErrorCode = "RATE_LIMITED"
)

// AppError represents an application-level error
type AppError struct {
    Code       ErrorCode `json:"code"`
    Message    string    `json:"message"`
    Details    any       `json:"details,omitempty"`
    Err        error     `json:"-"`
    StatusCode int       `json:"-"`
}

func (e *AppError) Error() string {
    if e.Err != nil {
        return fmt.Sprintf("%s: %s: %v", e.Code, e.Message, e.Err)
    }
    return fmt.Sprintf("%s: %s", e.Code, e.Message)
}

func (e *AppError) Unwrap() error {
    return e.Err
}

func (e *AppError) HTTPStatus() int {
    if e.StatusCode != 0 {
        return e.StatusCode
    }
    return codeToStatus(e.Code)
}

func (e *AppError) IsServerError() bool {
    return e.HTTPStatus() >= 500
}

func (e *AppError) WithMessage(msg string) *AppError {
    return &AppError{
        Code:       e.Code,
        Message:    msg,
        StatusCode: e.StatusCode,
        Err:        e.Err,
    }
}

func (e *AppError) WithMessagef(format string, args ...interface{}) *AppError {
    return e.WithMessage(fmt.Sprintf(format, args...))
}

func (e *AppError) WithDetails(details any) *AppError {
    return &AppError{
        Code:       e.Code,
        Message:    e.Message,
        Details:    details,
        StatusCode: e.StatusCode,
        Err:        e.Err,
    }
}

func (e *AppError) WithError(err error) *AppError {
    return &AppError{
        Code:       e.Code,
        Message:    e.Message,
        Details:    e.Details,
        StatusCode: e.StatusCode,
        Err:        err,
    }
}

func codeToStatus(code ErrorCode) int {
    switch code {
    case CodeInvalidInput:
        return http.StatusBadRequest
    case CodeNotFound:
        return http.StatusNotFound
    case CodeConflict:
        return http.StatusConflict
    case CodeUnauthorized:
        return http.StatusUnauthorized
    case CodeForbidden:
        return http.StatusForbidden
    case CodeRateLimited:
        return http.StatusTooManyRequests
    case CodeTimeout:
        return http.StatusGatewayTimeout
    case CodeServiceUnavailable:
        return http.StatusServiceUnavailable
    default:
        return http.StatusInternalServerError
    }
}
```

## Predefined Errors

```go
// pkg/errors/errors.go
package errors

// Predefined application errors
var (
    ErrInvalidInput = &AppError{
        Code:       CodeInvalidInput,
        Message:    "Invalid input provided",
        StatusCode: 400,
    }

    ErrNotFound = &AppError{
        Code:       CodeNotFound,
        Message:    "Resource not found",
        StatusCode: 404,
    }

    ErrConflict = &AppError{
        Code:       CodeConflict,
        Message:    "Resource already exists",
        StatusCode: 409,
    }

    ErrUnauthorized = &AppError{
        Code:       CodeUnauthorized,
        Message:    "Authentication required",
        StatusCode: 401,
    }

    ErrForbidden = &AppError{
        Code:       CodeForbidden,
        Message:    "Access denied",
        StatusCode: 403,
    }

    ErrInternal = &AppError{
        Code:       CodeInternal,
        Message:    "Internal server error",
        StatusCode: 500,
    }

    ErrServiceUnavailable = &AppError{
        Code:       CodeServiceUnavailable,
        Message:    "Service temporarily unavailable",
        StatusCode: 503,
    }

    ErrTimeout = &AppError{
        Code:       CodeTimeout,
        Message:    "Request timeout",
        StatusCode: 504,
    }

    ErrRateLimited = &AppError{
        Code:       CodeRateLimited,
        Message:    "Too many requests",
        StatusCode: 429,
    }
)
```

## Domain-Specific Errors

```go
// internal/domain/user/errors.go
package user

import "myproject/pkg/errors"

var (
    ErrNotFound = errors.ErrNotFound.WithMessage("User not found")

    ErrEmailExists = errors.ErrConflict.WithMessage("Email already registered")

    ErrInvalidCredentials = errors.ErrUnauthorized.WithMessage("Invalid email or password")

    ErrAccountInactive = errors.ErrForbidden.WithMessage("Account is not active")

    ErrInvalidID = errors.ErrInvalidInput.WithMessage("Invalid user ID format")

    ErrWeakPassword = errors.ErrInvalidInput.WithMessage("Password does not meet security requirements")

    ErrEmailNotVerified = errors.ErrForbidden.WithMessage("Email address not verified")
)

// internal/domain/order/errors.go
package order

import "myproject/pkg/errors"

var (
    ErrNotFound = errors.ErrNotFound.WithMessage("Order not found")

    ErrInvalidStatus = errors.ErrInvalidInput.WithMessage("Invalid order status")

    ErrCannotCancel = errors.ErrConflict.WithMessage("Order cannot be cancelled in current status")

    ErrInsufficientStock = errors.ErrConflict.WithMessage("Insufficient stock for order")

    ErrPaymentFailed = &errors.AppError{
        Code:       "PAYMENT_FAILED",
        Message:    "Payment processing failed",
        StatusCode: 402,
    }

    ErrShippingUnavailable = errors.ErrServiceUnavailable.WithMessage("Shipping service unavailable")
)
```

## Error Builder Pattern

```go
// pkg/errors/builder.go
package errors

type ErrorBuilder struct {
    err *AppError
}

func New(code ErrorCode) *ErrorBuilder {
    return &ErrorBuilder{
        err: &AppError{
            Code:       code,
            StatusCode: codeToStatus(code),
        },
    }
}

func (b *ErrorBuilder) Message(msg string) *ErrorBuilder {
    b.err.Message = msg
    return b
}

func (b *ErrorBuilder) Messagef(format string, args ...interface{}) *ErrorBuilder {
    b.err.Message = fmt.Sprintf(format, args...)
    return b
}

func (b *ErrorBuilder) Status(code int) *ErrorBuilder {
    b.err.StatusCode = code
    return b
}

func (b *ErrorBuilder) Details(details any) *ErrorBuilder {
    b.err.Details = details
    return b
}

func (b *ErrorBuilder) Wrap(err error) *ErrorBuilder {
    b.err.Err = err
    return b
}

func (b *ErrorBuilder) Build() *AppError {
    return b.err
}

// Usage
err := errors.New(errors.CodeNotFound).
    Messagef("User %s not found", userID).
    Details(map[string]string{"user_id": userID}).
    Build()
```

## Sentinel Errors with Context

```go
// pkg/errors/sentinel.go
package errors

import "errors"

// Sentinel errors for error checking
var (
    ErrValidation     = errors.New("validation error")
    ErrDatabase       = errors.New("database error")
    ErrExternalAPI    = errors.New("external API error")
    ErrAuthentication = errors.New("authentication error")
    ErrAuthorization  = errors.New("authorization error")
)

// WithContext wraps a sentinel error with context
func WithContext(sentinel error, msg string) error {
    return fmt.Errorf("%s: %w", msg, sentinel)
}

// Usage
func (r *repo) GetByID(ctx context.Context, id uuid.UUID) (*Entity, error) {
    err := r.db.GetContext(ctx, &row, query, id)
    if err != nil {
        return nil, errors.WithContext(errors.ErrDatabase, fmt.Sprintf("fetching entity %s", id))
    }
    return row.toDomain(), nil
}

// Checking
if errors.Is(err, errors.ErrDatabase) {
    // Handle database error
}
```

## Multi-Error Collection

```go
// pkg/errors/multi.go
package errors

import (
    "strings"
)

// MultiError collects multiple errors
type MultiError struct {
    Errors []error
}

func (m *MultiError) Add(err error) {
    if err != nil {
        m.Errors = append(m.Errors, err)
    }
}

func (m *MultiError) HasErrors() bool {
    return len(m.Errors) > 0
}

func (m *MultiError) Error() string {
    if len(m.Errors) == 0 {
        return ""
    }

    msgs := make([]string, len(m.Errors))
    for i, err := range m.Errors {
        msgs[i] = err.Error()
    }
    return strings.Join(msgs, "; ")
}

func (m *MultiError) ToError() error {
    if !m.HasErrors() {
        return nil
    }
    return m
}

// Usage: Validate multiple fields
func ValidateOrder(order *Order) error {
    errs := &errors.MultiError{}

    if order.CustomerID == "" {
        errs.Add(errors.ErrInvalidInput.WithMessage("customer ID is required"))
    }

    if len(order.Items) == 0 {
        errs.Add(errors.ErrInvalidInput.WithMessage("at least one item is required"))
    }

    if order.Total <= 0 {
        errs.Add(errors.ErrInvalidInput.WithMessage("total must be positive"))
    }

    return errs.ToError()
}
```

## Error Mapping for External APIs

```go
// pkg/errors/external.go
package errors

import (
    "net/http"
)

// MapHTTPError maps external HTTP status codes to app errors
func MapHTTPError(statusCode int, message string) *AppError {
    switch statusCode {
    case http.StatusBadRequest:
        return ErrInvalidInput.WithMessage(message)
    case http.StatusUnauthorized:
        return ErrUnauthorized.WithMessage(message)
    case http.StatusForbidden:
        return ErrForbidden.WithMessage(message)
    case http.StatusNotFound:
        return ErrNotFound.WithMessage(message)
    case http.StatusConflict:
        return ErrConflict.WithMessage(message)
    case http.StatusTooManyRequests:
        return ErrRateLimited.WithMessage(message)
    case http.StatusServiceUnavailable:
        return ErrServiceUnavailable.WithMessage(message)
    case http.StatusGatewayTimeout:
        return ErrTimeout.WithMessage(message)
    default:
        if statusCode >= 500 {
            return ErrInternal.WithMessage(message)
        }
        return ErrInvalidInput.WithMessage(message)
    }
}

// Usage: Calling external API
func (c *PaymentClient) Charge(ctx context.Context, req ChargeRequest) error {
    resp, err := c.httpClient.Post(url, body)
    if err != nil {
        return errors.ErrServiceUnavailable.
            WithMessage("Payment service unavailable").
            WithError(err)
    }

    if resp.StatusCode != http.StatusOK {
        body, _ := io.ReadAll(resp.Body)
        return errors.MapHTTPError(resp.StatusCode, string(body))
    }

    return nil
}
```

## Error Testing Helpers

```go
// pkg/errors/testing.go
package errors

import (
    "testing"

    "github.com/stretchr/testify/assert"
)

// AssertAppError checks if error is AppError with expected code
func AssertAppError(t *testing.T, err error, expectedCode ErrorCode) {
    t.Helper()

    var appErr *AppError
    if !As(err, &appErr) {
        t.Fatalf("expected AppError, got %T", err)
    }

    assert.Equal(t, expectedCode, appErr.Code)
}

// AssertHTTPStatus checks if error has expected HTTP status
func AssertHTTPStatus(t *testing.T, err error, expectedStatus int) {
    t.Helper()

    var appErr *AppError
    if !As(err, &appErr) {
        t.Fatalf("expected AppError, got %T", err)
    }

    assert.Equal(t, expectedStatus, appErr.HTTPStatus())
}

// Usage in tests
func TestUserService_GetByID_NotFound(t *testing.T) {
    // ... setup
    _, err := service.GetByID(ctx, "non-existent-id")

    errors.AssertAppError(t, err, errors.CodeNotFound)
    errors.AssertHTTPStatus(t, err, 404)
}
```

## Best Practices

1. **Define at Domain Level**: Domain errors belong in domain package
2. **Use Builders**: Error builders for flexible construction
3. **Consistent Codes**: Use consistent error codes across application
4. **HTTP Mapping**: Map errors to appropriate HTTP status codes
5. **Context Preservation**: Include context in error messages
6. **Type Safety**: Use typed errors for compile-time safety
