# Go Test Template

Template for creating test files in Go applications.

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{package_name}}` | Package being tested | service |
| `{{struct_name}}` | Struct/Type being tested | UserService |
| `{{method_name}}` | Method being tested | GetByID |
| `{{module_path}}` | Go module path | myproject |

## Unit Test Template

```go
// internal/{{package_name}}/{{struct_name_lower}}_test.go
package {{package_name}}

import (
    "context"
    "testing"

    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/mock"
    "github.com/stretchr/testify/require"

    "{{module_path}}/internal/domain/{{domain_name}}"
    "{{module_path}}/internal/domain/{{domain_name}}/mocks"
)

func Test{{struct_name}}_{{method_name}}(t *testing.T) {
    tests := []struct {
        name          string
        {{#input_fields}}
        {{field_name}} {{field_type}}
        {{/input_fields}}
        mockSetup     func(*mocks.Mock{{dependency_name}})
        expected      {{expected_type}}
        expectedError error
    }{
        {
            name: "success case",
            {{#input_values}}
            {{field_name}}: {{field_value}},
            {{/input_values}}
            mockSetup: func(m *mocks.Mock{{dependency_name}}) {
                m.On("{{mock_method}}", mock.Anything{{#mock_args}}, {{arg}}{{/mock_args}}).
                    Return({{mock_return}})
            },
            expected:      {{expected_value}},
            expectedError: nil,
        },
        {
            name: "error case",
            {{#error_input_values}}
            {{field_name}}: {{field_value}},
            {{/error_input_values}}
            mockSetup: func(m *mocks.Mock{{dependency_name}}) {
                m.On("{{mock_method}}", mock.Anything{{#mock_args}}, mock.Anything{{/mock_args}}).
                    Return({{error_mock_return}})
            },
            expected:      {{zero_value}},
            expectedError: {{expected_error}},
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            // Setup
            mock{{dependency_name}} := new(mocks.Mock{{dependency_name}})
            tt.mockSetup(mock{{dependency_name}})

            svc := New{{struct_name}}(mock{{dependency_name}})

            // Execute
            result, err := svc.{{method_name}}(context.Background(){{#method_args}}, tt.{{arg_name}}{{/method_args}})

            // Assert
            if tt.expectedError != nil {
                require.Error(t, err)
                assert.ErrorIs(t, err, tt.expectedError)
            } else {
                require.NoError(t, err)
                assert.Equal(t, tt.expected, result)
            }

            mock{{dependency_name}}.AssertExpectations(t)
        })
    }
}
```

## Example: User Service Test

```go
// internal/service/user_service_test.go
package service

import (
    "context"
    "testing"
    "time"

    "github.com/google/uuid"
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/mock"
    "github.com/stretchr/testify/require"

    "myproject/internal/domain/user"
    "myproject/internal/domain/user/mocks"
    "myproject/pkg/errors"
)

// Test fixtures
var (
    testUserID    = uuid.MustParse("123e4567-e89b-12d3-a456-426614174000")
    testUserEmail = user.Email("test@example.com")
    testTime      = time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC)
)

func newTestUser() *user.User {
    return &user.User{
        ID:        testUserID,
        Email:     testUserEmail,
        Name:      "Test User",
        Status:    user.StatusActive,
        Role:      user.RoleUser,
        CreatedAt: testTime,
        UpdatedAt: testTime,
    }
}

func TestUserService_GetByID(t *testing.T) {
    tests := []struct {
        name          string
        userID        string
        mockSetup     func(*mocks.MockUserRepository)
        expectedUser  *user.User
        expectedError error
    }{
        {
            name:   "valid user",
            userID: testUserID.String(),
            mockSetup: func(m *mocks.MockUserRepository) {
                m.On("GetByID", mock.Anything, testUserID).Return(newTestUser(), nil)
            },
            expectedUser:  newTestUser(),
            expectedError: nil,
        },
        {
            name:   "user not found",
            userID: uuid.New().String(),
            mockSetup: func(m *mocks.MockUserRepository) {
                m.On("GetByID", mock.Anything, mock.Anything).Return(nil, user.ErrNotFound)
            },
            expectedUser:  nil,
            expectedError: errors.ErrNotFound,
        },
        {
            name:          "invalid UUID",
            userID:        "invalid-uuid",
            mockSetup:     func(m *mocks.MockUserRepository) {},
            expectedUser:  nil,
            expectedError: errors.ErrInvalidInput,
        },
        {
            name:          "empty ID",
            userID:        "",
            mockSetup:     func(m *mocks.MockUserRepository) {},
            expectedUser:  nil,
            expectedError: errors.ErrInvalidInput,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            mockRepo := new(mocks.MockUserRepository)
            tt.mockSetup(mockRepo)

            svc := NewUserService(mockRepo, nil, nil)

            result, err := svc.GetByID(context.Background(), tt.userID)

            if tt.expectedError != nil {
                require.Error(t, err)
                assert.True(t, errors.Is(err, tt.expectedError))
                assert.Nil(t, result)
            } else {
                require.NoError(t, err)
                require.NotNil(t, result)
                assert.Equal(t, tt.expectedUser.ID, result.ID)
                assert.Equal(t, tt.expectedUser.Email, result.Email)
            }

            mockRepo.AssertExpectations(t)
        })
    }
}

func TestUserService_Create(t *testing.T) {
    tests := []struct {
        name          string
        input         CreateUserInput
        mockSetup     func(*mocks.MockUserRepository)
        expectedError error
    }{
        {
            name: "successful creation",
            input: CreateUserInput{
                Email:    "new@example.com",
                Name:     "New User",
                Password: "SecureP@ss123",
            },
            mockSetup: func(m *mocks.MockUserRepository) {
                m.On("ExistsByEmail", mock.Anything, user.Email("new@example.com")).Return(false, nil)
                m.On("Create", mock.Anything, mock.AnythingOfType("*user.User")).Return(nil)
            },
            expectedError: nil,
        },
        {
            name: "email already exists",
            input: CreateUserInput{
                Email:    "existing@example.com",
                Name:     "Existing User",
                Password: "SecureP@ss123",
            },
            mockSetup: func(m *mocks.MockUserRepository) {
                m.On("ExistsByEmail", mock.Anything, user.Email("existing@example.com")).Return(true, nil)
            },
            expectedError: user.ErrEmailExists,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            mockRepo := new(mocks.MockUserRepository)
            tt.mockSetup(mockRepo)

            svc := NewUserService(mockRepo, nil, nil)

            result, err := svc.Create(context.Background(), tt.input)

            if tt.expectedError != nil {
                require.Error(t, err)
                assert.True(t, errors.Is(err, tt.expectedError))
            } else {
                require.NoError(t, err)
                require.NotNil(t, result)
                assert.Equal(t, user.Email(tt.input.Email), result.Email)
                assert.Equal(t, tt.input.Name, result.Name)
            }

            mockRepo.AssertExpectations(t)
        })
    }
}
```

## Handler Test Template

```go
// internal/handler/{{handler_name_lower}}_handler_test.go
package handler

import (
    "bytes"
    "encoding/json"
    "net/http"
    "net/http/httptest"
    "testing"

    "github.com/gin-gonic/gin"
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/mock"
    "github.com/stretchr/testify/require"
)

func setupTestRouter(h *{{handler_name}}Handler) *gin.Engine {
    gin.SetMode(gin.TestMode)
    r := gin.New()
    {{#routes}}
    r.{{http_method}}("{{route_path}}", h.{{handler_method}})
    {{/routes}}
    return r
}

func Test{{handler_name}}Handler_{{method_name}}(t *testing.T) {
    tests := []struct {
        name           string
        requestBody    interface{}
        mockSetup      func(*Mock{{service_name}})
        expectedStatus int
        expectedBody   map[string]interface{}
    }{
        // Test cases
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            mockService := new(Mock{{service_name}})
            tt.mockSetup(mockService)

            handler := New{{handler_name}}Handler(mockService)
            router := setupTestRouter(handler)

            body, _ := json.Marshal(tt.requestBody)
            req := httptest.NewRequest(http.Method{{http_method}}, "{{route_path}}", bytes.NewBuffer(body))
            req.Header.Set("Content-Type", "application/json")
            rec := httptest.NewRecorder()

            router.ServeHTTP(rec, req)

            assert.Equal(t, tt.expectedStatus, rec.Code)

            var response map[string]interface{}
            json.Unmarshal(rec.Body.Bytes(), &response)

            for key, expected := range tt.expectedBody {
                assert.Contains(t, response, key)
            }

            mockService.AssertExpectations(t)
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

func MakeJSONRequest(t *testing.T, method, url string, body interface{}) *http.Request {
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

func ParseJSONResponse(t *testing.T, rec *httptest.ResponseRecorder, target interface{}) {
    t.Helper()
    err := json.Unmarshal(rec.Body.Bytes(), target)
    require.NoError(t, err)
}

func AssertStatus(t *testing.T, rec *httptest.ResponseRecorder, expected int) {
    t.Helper()
    if rec.Code != expected {
        t.Errorf("expected status %d, got %d. Body: %s", expected, rec.Code, rec.Body.String())
    }
}
```

## Usage

```bash
# Generate test for service
f5 generate test UserService --methods "GetByID,Create,Update,Delete"

# Generate test for handler
f5 generate test UserHandler --type handler --methods "Get,Create,Update"
```
