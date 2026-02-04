# Mocking with Testify

Implementing mocks for unit testing in Go applications.

## Mock Generation with mockery

```bash
# Install mockery
go install github.com/vektra/mockery/v2@latest

# Generate mocks for all interfaces
mockery --all --output=mocks

# Generate mock for specific interface
mockery --name=UserRepository --dir=internal/domain/user --output=internal/domain/user/mocks
```

## Basic Mock Usage

```go
// internal/domain/user/repository.go
package user

import (
    "context"
    "github.com/google/uuid"
)

type Repository interface {
    GetByID(ctx context.Context, id uuid.UUID) (*User, error)
    GetByEmail(ctx context.Context, email Email) (*User, error)
    Create(ctx context.Context, user *User) error
    Update(ctx context.Context, user *User) error
    Delete(ctx context.Context, id uuid.UUID) error
}

// internal/domain/user/mocks/repository.go (generated or manual)
package mocks

import (
    "context"

    "github.com/google/uuid"
    "github.com/stretchr/testify/mock"

    "myproject/internal/domain/user"
)

type MockUserRepository struct {
    mock.Mock
}

func (m *MockUserRepository) GetByID(ctx context.Context, id uuid.UUID) (*user.User, error) {
    args := m.Called(ctx, id)
    if args.Get(0) == nil {
        return nil, args.Error(1)
    }
    return args.Get(0).(*user.User), args.Error(1)
}

func (m *MockUserRepository) GetByEmail(ctx context.Context, email user.Email) (*user.User, error) {
    args := m.Called(ctx, email)
    if args.Get(0) == nil {
        return nil, args.Error(1)
    }
    return args.Get(0).(*user.User), args.Error(1)
}

func (m *MockUserRepository) Create(ctx context.Context, u *user.User) error {
    args := m.Called(ctx, u)
    return args.Error(0)
}

func (m *MockUserRepository) Update(ctx context.Context, u *user.User) error {
    args := m.Called(ctx, u)
    return args.Error(0)
}

func (m *MockUserRepository) Delete(ctx context.Context, id uuid.UUID) error {
    args := m.Called(ctx, id)
    return args.Error(0)
}
```

## Using Mocks in Tests

```go
// internal/service/user_service_test.go
package service

import (
    "context"
    "testing"

    "github.com/google/uuid"
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/mock"
    "github.com/stretchr/testify/require"

    "myproject/internal/domain/user"
    "myproject/internal/domain/user/mocks"
)

func TestUserService_Create(t *testing.T) {
    t.Run("successful creation", func(t *testing.T) {
        // Setup
        mockRepo := new(mocks.MockUserRepository)
        mockRepo.On("ExistsByEmail", mock.Anything, user.Email("test@example.com")).Return(false, nil)
        mockRepo.On("Create", mock.Anything, mock.AnythingOfType("*user.User")).Return(nil)

        svc := NewUserService(mockRepo)

        // Execute
        result, err := svc.Create(context.Background(), CreateUserInput{
            Email:    "test@example.com",
            Name:     "Test User",
            Password: "SecureP@ss123",
        })

        // Assert
        require.NoError(t, err)
        assert.NotNil(t, result)
        assert.Equal(t, user.Email("test@example.com"), result.Email)
        mockRepo.AssertExpectations(t)
    })

    t.Run("email already exists", func(t *testing.T) {
        // Setup
        mockRepo := new(mocks.MockUserRepository)
        mockRepo.On("ExistsByEmail", mock.Anything, user.Email("existing@example.com")).Return(true, nil)

        svc := NewUserService(mockRepo)

        // Execute
        result, err := svc.Create(context.Background(), CreateUserInput{
            Email:    "existing@example.com",
            Name:     "Test User",
            Password: "SecureP@ss123",
        })

        // Assert
        require.Error(t, err)
        assert.Nil(t, result)
        assert.True(t, errors.Is(err, user.ErrEmailExists))
        mockRepo.AssertExpectations(t)
    })
}
```

## Mock Matchers

```go
// Using different matchers
func TestUserService_Update(t *testing.T) {
    mockRepo := new(mocks.MockUserRepository)

    // Exact value matching
    mockRepo.On("GetByID", mock.Anything, uuid.MustParse("123e4567-e89b-12d3-a456-426614174000")).
        Return(&user.User{ID: uuid.MustParse("123e4567-e89b-12d3-a456-426614174000")}, nil)

    // Type matching
    mockRepo.On("Update", mock.Anything, mock.AnythingOfType("*user.User")).Return(nil)

    // Custom matching function
    mockRepo.On("Create", mock.Anything, mock.MatchedBy(func(u *user.User) bool {
        return u.Email == "test@example.com" && u.Status == user.StatusActive
    })).Return(nil)

    // Any value
    mockRepo.On("Delete", mock.Anything, mock.Anything).Return(nil)
}
```

## Mock Return Values

```go
func TestUserService_GetByID(t *testing.T) {
    mockRepo := new(mocks.MockUserRepository)

    // Return specific value
    mockRepo.On("GetByID", mock.Anything, testUserID).Return(testUser, nil)

    // Return nil with error
    mockRepo.On("GetByID", mock.Anything, nonExistentID).Return(nil, user.ErrNotFound)

    // Return value based on input (using Run)
    mockRepo.On("Update", mock.Anything, mock.AnythingOfType("*user.User")).
        Run(func(args mock.Arguments) {
            u := args.Get(1).(*user.User)
            u.UpdatedAt = time.Now()
        }).Return(nil)

    // Return different values on sequential calls
    mockRepo.On("GetByID", mock.Anything, fluctuatingID).
        Return(testUser, nil).Once()
    mockRepo.On("GetByID", mock.Anything, fluctuatingID).
        Return(nil, user.ErrNotFound).Once()
}
```

## HTTP Client Mocking

```go
// pkg/httpclient/client_test.go
package httpclient

import (
    "net/http"
    "net/http/httptest"
    "testing"

    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"
)

func TestPaymentClient_Charge(t *testing.T) {
    tests := []struct {
        name           string
        serverResponse func(w http.ResponseWriter, r *http.Request)
        expectedError  bool
    }{
        {
            name: "successful charge",
            serverResponse: func(w http.ResponseWriter, r *http.Request) {
                w.WriteHeader(http.StatusOK)
                w.Write([]byte(`{"status":"success","transaction_id":"txn_123"}`))
            },
            expectedError: false,
        },
        {
            name: "payment declined",
            serverResponse: func(w http.ResponseWriter, r *http.Request) {
                w.WriteHeader(http.StatusPaymentRequired)
                w.Write([]byte(`{"error":"card_declined"}`))
            },
            expectedError: true,
        },
        {
            name: "server error",
            serverResponse: func(w http.ResponseWriter, r *http.Request) {
                w.WriteHeader(http.StatusInternalServerError)
            },
            expectedError: true,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            // Create test server
            server := httptest.NewServer(http.HandlerFunc(tt.serverResponse))
            defer server.Close()

            // Create client with test server URL
            client := NewPaymentClient(server.URL)

            // Execute
            err := client.Charge(context.Background(), ChargeRequest{
                Amount:   1000,
                Currency: "USD",
                CardToken: "tok_123",
            })

            // Assert
            if tt.expectedError {
                require.Error(t, err)
            } else {
                require.NoError(t, err)
            }
        })
    }
}
```

## Service Mock with Multiple Dependencies

```go
// internal/service/order_service_test.go
package service

import (
    "context"
    "testing"

    "github.com/stretchr/testify/mock"
    "github.com/stretchr/testify/require"

    ordermocks "myproject/internal/domain/order/mocks"
    usermocks "myproject/internal/domain/user/mocks"
    productmocks "myproject/internal/domain/product/mocks"
)

type orderServiceMocks struct {
    orderRepo   *ordermocks.MockOrderRepository
    userRepo    *usermocks.MockUserRepository
    productRepo *productmocks.MockProductRepository
    paymentSvc  *MockPaymentService
}

func newOrderServiceMocks() *orderServiceMocks {
    return &orderServiceMocks{
        orderRepo:   new(ordermocks.MockOrderRepository),
        userRepo:    new(usermocks.MockUserRepository),
        productRepo: new(productmocks.MockProductRepository),
        paymentSvc:  new(MockPaymentService),
    }
}

func (m *orderServiceMocks) assertExpectations(t *testing.T) {
    m.orderRepo.AssertExpectations(t)
    m.userRepo.AssertExpectations(t)
    m.productRepo.AssertExpectations(t)
    m.paymentSvc.AssertExpectations(t)
}

func TestOrderService_CreateOrder(t *testing.T) {
    t.Run("successful order creation", func(t *testing.T) {
        mocks := newOrderServiceMocks()

        // Setup expectations
        mocks.userRepo.On("GetByID", mock.Anything, testUserID).Return(testUser, nil)
        mocks.productRepo.On("GetByID", mock.Anything, testProductID).Return(testProduct, nil)
        mocks.productRepo.On("DecrementStock", mock.Anything, testProductID, 1).Return(nil)
        mocks.orderRepo.On("Create", mock.Anything, mock.AnythingOfType("*order.Order")).Return(nil)
        mocks.paymentSvc.On("Charge", mock.Anything, mock.Anything).Return(nil)

        svc := NewOrderService(
            mocks.orderRepo,
            mocks.userRepo,
            mocks.productRepo,
            mocks.paymentSvc,
        )

        // Execute
        order, err := svc.CreateOrder(context.Background(), CreateOrderInput{
            UserID: testUserID.String(),
            Items: []OrderItemInput{
                {ProductID: testProductID.String(), Quantity: 1},
            },
        })

        // Assert
        require.NoError(t, err)
        require.NotNil(t, order)
        mocks.assertExpectations(t)
    })
}
```

## Mock Interface Pattern

```go
// internal/service/interfaces.go
package service

// Define interfaces for external dependencies
type PaymentGateway interface {
    Charge(ctx context.Context, amount int, currency string) error
    Refund(ctx context.Context, transactionID string) error
}

type EmailSender interface {
    Send(ctx context.Context, to, subject, body string) error
}

type CacheStore interface {
    Get(ctx context.Context, key string) (string, error)
    Set(ctx context.Context, key, value string, ttl time.Duration) error
    Delete(ctx context.Context, key string) error
}

// Service uses interfaces (easy to mock)
type OrderService struct {
    orderRepo      order.Repository
    paymentGateway PaymentGateway
    emailSender    EmailSender
    cache          CacheStore
}
```

## Best Practices

1. **Interface First**: Define interfaces for dependencies
2. **Generate Mocks**: Use mockery for consistent mock generation
3. **Assert Expectations**: Always call `AssertExpectations(t)`
4. **Isolate Tests**: Each test should have its own mock instance
5. **Clear Setup**: Make mock setup explicit and readable
6. **Use Matchers**: Use appropriate matchers for flexibility
