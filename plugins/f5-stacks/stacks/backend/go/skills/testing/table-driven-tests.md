# Table-Driven Tests

Implementing table-driven tests in Go for comprehensive test coverage.

## Basic Table-Driven Test

```go
// internal/service/calculator_test.go
package service

import (
    "testing"

    "github.com/stretchr/testify/assert"
)

func TestAdd(t *testing.T) {
    tests := []struct {
        name     string
        a, b     int
        expected int
    }{
        {"positive numbers", 2, 3, 5},
        {"negative numbers", -2, -3, -5},
        {"mixed numbers", -2, 3, 1},
        {"zeros", 0, 0, 0},
        {"large numbers", 1000000, 2000000, 3000000},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            result := Add(tt.a, tt.b)
            assert.Equal(t, tt.expected, result)
        })
    }
}
```

## Test with Error Cases

```go
// internal/service/user_service_test.go
package service

import (
    "context"
    "testing"

    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"

    "myproject/internal/domain/user"
    "myproject/pkg/errors"
)

func TestUserService_GetByID(t *testing.T) {
    tests := []struct {
        name          string
        userID        string
        mockSetup     func(*MockUserRepository)
        expectedUser  *user.User
        expectedError error
    }{
        {
            name:   "valid user",
            userID: "123e4567-e89b-12d3-a456-426614174000",
            mockSetup: func(m *MockUserRepository) {
                m.On("GetByID", mock.Anything, mock.Anything).Return(&user.User{
                    ID:    uuid.MustParse("123e4567-e89b-12d3-a456-426614174000"),
                    Email: "test@example.com",
                    Name:  "Test User",
                }, nil)
            },
            expectedUser: &user.User{
                ID:    uuid.MustParse("123e4567-e89b-12d3-a456-426614174000"),
                Email: "test@example.com",
                Name:  "Test User",
            },
            expectedError: nil,
        },
        {
            name:   "user not found",
            userID: "123e4567-e89b-12d3-a456-426614174001",
            mockSetup: func(m *MockUserRepository) {
                m.On("GetByID", mock.Anything, mock.Anything).Return(nil, user.ErrNotFound)
            },
            expectedUser:  nil,
            expectedError: errors.ErrNotFound,
        },
        {
            name:          "invalid ID format",
            userID:        "invalid-uuid",
            mockSetup:     func(m *MockUserRepository) {},
            expectedUser:  nil,
            expectedError: errors.ErrInvalidInput,
        },
        {
            name:          "empty ID",
            userID:        "",
            mockSetup:     func(m *MockUserRepository) {},
            expectedUser:  nil,
            expectedError: errors.ErrInvalidInput,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            // Setup
            mockRepo := new(MockUserRepository)
            tt.mockSetup(mockRepo)
            svc := NewUserService(mockRepo)

            // Execute
            result, err := svc.GetByID(context.Background(), tt.userID)

            // Assert
            if tt.expectedError != nil {
                require.Error(t, err)
                assert.True(t, errors.Is(err, tt.expectedError))
                assert.Nil(t, result)
            } else {
                require.NoError(t, err)
                assert.Equal(t, tt.expectedUser.ID, result.ID)
                assert.Equal(t, tt.expectedUser.Email, result.Email)
            }

            mockRepo.AssertExpectations(t)
        })
    }
}
```

## Test with Subtests and Setup

```go
// internal/handler/user_handler_test.go
package handler

import (
    "bytes"
    "encoding/json"
    "net/http"
    "net/http/httptest"
    "testing"

    "github.com/gin-gonic/gin"
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"
)

func TestUserHandler_Create(t *testing.T) {
    gin.SetMode(gin.TestMode)

    tests := []struct {
        name           string
        requestBody    interface{}
        mockSetup      func(*MockUserService)
        expectedStatus int
        expectedBody   map[string]interface{}
    }{
        {
            name: "successful creation",
            requestBody: map[string]string{
                "email":    "test@example.com",
                "name":     "Test User",
                "password": "SecureP@ss123",
            },
            mockSetup: func(m *MockUserService) {
                m.On("Create", mock.Anything, mock.Anything).Return(&user.User{
                    ID:    uuid.New(),
                    Email: "test@example.com",
                    Name:  "Test User",
                }, nil)
            },
            expectedStatus: http.StatusCreated,
            expectedBody: map[string]interface{}{
                "email": "test@example.com",
                "name":  "Test User",
            },
        },
        {
            name: "validation error - missing email",
            requestBody: map[string]string{
                "name":     "Test User",
                "password": "SecureP@ss123",
            },
            mockSetup:      func(m *MockUserService) {},
            expectedStatus: http.StatusBadRequest,
            expectedBody: map[string]interface{}{
                "error": map[string]interface{}{
                    "code": "VALIDATION_ERROR",
                },
            },
        },
        {
            name: "validation error - invalid email",
            requestBody: map[string]string{
                "email":    "invalid-email",
                "name":     "Test User",
                "password": "SecureP@ss123",
            },
            mockSetup:      func(m *MockUserService) {},
            expectedStatus: http.StatusBadRequest,
            expectedBody: map[string]interface{}{
                "error": map[string]interface{}{
                    "code": "VALIDATION_ERROR",
                },
            },
        },
        {
            name: "conflict - email exists",
            requestBody: map[string]string{
                "email":    "existing@example.com",
                "name":     "Test User",
                "password": "SecureP@ss123",
            },
            mockSetup: func(m *MockUserService) {
                m.On("Create", mock.Anything, mock.Anything).Return(nil, user.ErrEmailExists)
            },
            expectedStatus: http.StatusConflict,
            expectedBody: map[string]interface{}{
                "error": map[string]interface{}{
                    "code": "CONFLICT",
                },
            },
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            // Setup
            mockService := new(MockUserService)
            tt.mockSetup(mockService)
            handler := NewUserHandler(mockService)

            router := gin.New()
            router.POST("/users", handler.Create)

            // Create request
            body, _ := json.Marshal(tt.requestBody)
            req := httptest.NewRequest(http.MethodPost, "/users", bytes.NewBuffer(body))
            req.Header.Set("Content-Type", "application/json")
            rec := httptest.NewRecorder()

            // Execute
            router.ServeHTTP(rec, req)

            // Assert status
            assert.Equal(t, tt.expectedStatus, rec.Code)

            // Assert body
            var response map[string]interface{}
            err := json.Unmarshal(rec.Body.Bytes(), &response)
            require.NoError(t, err)

            for key, expected := range tt.expectedBody {
                assert.Contains(t, response, key)
                if expectedMap, ok := expected.(map[string]interface{}); ok {
                    for subKey := range expectedMap {
                        assert.Contains(t, response[key], subKey)
                    }
                }
            }

            mockService.AssertExpectations(t)
        })
    }
}
```

## Test with Parallel Execution

```go
// internal/util/string_test.go
package util

import (
    "testing"

    "github.com/stretchr/testify/assert"
)

func TestSlugify(t *testing.T) {
    tests := []struct {
        name     string
        input    string
        expected string
    }{
        {"simple string", "Hello World", "hello-world"},
        {"with numbers", "Test 123", "test-123"},
        {"special chars", "Hello! @World#", "hello-world"},
        {"multiple spaces", "Hello    World", "hello-world"},
        {"unicode", "Café Münster", "cafe-munster"},
        {"empty string", "", ""},
        {"only special chars", "!@#$%", ""},
    }

    for _, tt := range tests {
        tt := tt // capture range variable for parallel execution
        t.Run(tt.name, func(t *testing.T) {
            t.Parallel() // Run subtests in parallel

            result := Slugify(tt.input)
            assert.Equal(t, tt.expected, result)
        })
    }
}
```

## Test with Test Fixtures

```go
// internal/repository/user_repository_test.go
package repository

import (
    "testing"
    "time"

    "github.com/google/uuid"

    "myproject/internal/domain/user"
)

// Test fixtures
var (
    testUserID    = uuid.MustParse("123e4567-e89b-12d3-a456-426614174000")
    testUserEmail = user.Email("test@example.com")
    testUserName  = "Test User"
    testTime      = time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC)
)

func newTestUser() *user.User {
    return &user.User{
        ID:        testUserID,
        Email:     testUserEmail,
        Name:      testUserName,
        Status:    user.StatusActive,
        CreatedAt: testTime,
        UpdatedAt: testTime,
    }
}

func TestUserRepository_GetByID(t *testing.T) {
    tests := []struct {
        name          string
        userID        uuid.UUID
        setupDB       func(*testing.T, *sqlx.DB)
        expectedUser  *user.User
        expectedError error
    }{
        {
            name:   "user exists",
            userID: testUserID,
            setupDB: func(t *testing.T, db *sqlx.DB) {
                testUser := newTestUser()
                _, err := db.Exec(`
                    INSERT INTO users (id, email, name, status, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6)
                `, testUser.ID, testUser.Email, testUser.Name, testUser.Status,
                    testUser.CreatedAt, testUser.UpdatedAt)
                require.NoError(t, err)
            },
            expectedUser:  newTestUser(),
            expectedError: nil,
        },
        {
            name:          "user not found",
            userID:        uuid.MustParse("123e4567-e89b-12d3-a456-426614174001"),
            setupDB:       func(t *testing.T, db *sqlx.DB) {},
            expectedUser:  nil,
            expectedError: user.ErrNotFound,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            // Setup test database
            db := setupTestDB(t)
            defer cleanupTestDB(t, db)
            tt.setupDB(t, db)

            repo := NewUserRepository(db)

            // Execute
            result, err := repo.GetByID(context.Background(), tt.userID)

            // Assert
            if tt.expectedError != nil {
                require.Error(t, err)
                assert.True(t, errors.Is(err, tt.expectedError))
            } else {
                require.NoError(t, err)
                assert.Equal(t, tt.expectedUser.ID, result.ID)
                assert.Equal(t, tt.expectedUser.Email, result.Email)
            }
        })
    }
}
```

## Test Helper Functions

```go
// internal/testutil/helpers.go
package testutil

import (
    "encoding/json"
    "io"
    "net/http"
    "net/http/httptest"
    "strings"
    "testing"

    "github.com/stretchr/testify/require"
)

// MakeRequest creates a test HTTP request
func MakeRequest(t *testing.T, method, url string, body interface{}) *http.Request {
    t.Helper()

    var reader io.Reader
    if body != nil {
        jsonBytes, err := json.Marshal(body)
        require.NoError(t, err)
        reader = strings.NewReader(string(jsonBytes))
    }

    req := httptest.NewRequest(method, url, reader)
    req.Header.Set("Content-Type", "application/json")
    return req
}

// ParseResponse parses response body to target
func ParseResponse(t *testing.T, rec *httptest.ResponseRecorder, target interface{}) {
    t.Helper()
    err := json.Unmarshal(rec.Body.Bytes(), target)
    require.NoError(t, err)
}

// AssertStatus asserts response status code
func AssertStatus(t *testing.T, rec *httptest.ResponseRecorder, expected int) {
    t.Helper()
    if rec.Code != expected {
        t.Errorf("expected status %d, got %d. Body: %s", expected, rec.Code, rec.Body.String())
    }
}
```

## Best Practices

1. **Descriptive Names**: Use clear, descriptive test case names
2. **Parallel Tests**: Use `t.Parallel()` for independent tests
3. **Capture Variables**: Capture range variables in parallel tests
4. **Test Fixtures**: Create reusable test data factories
5. **Helper Functions**: Use `t.Helper()` in test helpers
6. **Subtests**: Use `t.Run()` for organized test output
