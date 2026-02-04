# Domain-Driven Design in Go

Implementing DDD tactical patterns in Go for complex business domains.

## Project Structure for DDD

```
internal/
├── domain/
│   ├── user/                     # User Aggregate
│   │   ├── aggregate.go          # Aggregate root
│   │   ├── entity.go             # Child entities
│   │   ├── value_object.go       # Value objects
│   │   ├── repository.go         # Repository interface
│   │   ├── service.go            # Domain service
│   │   ├── events.go             # Domain events
│   │   └── errors.go             # Domain errors
│   │
│   ├── order/                    # Order Aggregate
│   │   ├── aggregate.go
│   │   ├── order_item.go         # Child entity
│   │   ├── money.go              # Value object
│   │   └── ...
│   │
│   └── shared/                   # Shared kernel
│       ├── entity.go             # Base entity
│       └── aggregate.go          # Base aggregate
│
├── application/                  # Application services
│   ├── user/
│   │   └── service.go
│   └── order/
│       └── service.go
│
└── infrastructure/
    ├── persistence/
    └── messaging/
```

## Base Types

```go
// internal/domain/shared/entity.go
package shared

import (
    "time"
    "github.com/google/uuid"
)

type EntityID uuid.UUID

func NewEntityID() EntityID {
    return EntityID(uuid.New())
}

func (id EntityID) String() string {
    return uuid.UUID(id).String()
}

type BaseEntity struct {
    id        EntityID
    createdAt time.Time
    updatedAt time.Time
}

func (e *BaseEntity) ID() EntityID {
    return e.id
}

func (e *BaseEntity) CreatedAt() time.Time {
    return e.createdAt
}

func (e *BaseEntity) UpdatedAt() time.Time {
    return e.updatedAt
}

func (e *BaseEntity) touch() {
    e.updatedAt = time.Now()
}
```

## Aggregate Root

```go
// internal/domain/order/aggregate.go
package order

import (
    "errors"
    "time"

    "myproject/internal/domain/shared"
)

type Status string

const (
    StatusPending    Status = "pending"
    StatusConfirmed  Status = "confirmed"
    StatusShipped    Status = "shipped"
    StatusDelivered  Status = "delivered"
    StatusCancelled  Status = "cancelled"
)

// Order is the aggregate root
type Order struct {
    shared.BaseEntity

    customerID shared.EntityID
    items      []OrderItem      // Child entities
    status     Status
    total      Money            // Value object
    shippingAddress Address     // Value object

    // Domain events
    events []DomainEvent
}

// Factory function - ensures valid state
func NewOrder(customerID shared.EntityID, shippingAddress Address) (*Order, error) {
    if customerID == (shared.EntityID{}) {
        return nil, ErrInvalidCustomer
    }

    order := &Order{
        BaseEntity: shared.BaseEntity{
            id:        shared.NewEntityID(),
            createdAt: time.Now(),
            updatedAt: time.Now(),
        },
        customerID:      customerID,
        items:           make([]OrderItem, 0),
        status:          StatusPending,
        total:           NewMoney(0, "USD"),
        shippingAddress: shippingAddress,
        events:          make([]DomainEvent, 0),
    }

    order.addEvent(OrderCreated{
        OrderID:    order.ID(),
        CustomerID: customerID,
        CreatedAt:  order.CreatedAt(),
    })

    return order, nil
}

// Business operations - maintain invariants
func (o *Order) AddItem(productID shared.EntityID, name string, quantity int, unitPrice Money) error {
    if o.status != StatusPending {
        return ErrOrderNotModifiable
    }
    if quantity <= 0 {
        return ErrInvalidQuantity
    }

    // Check if item already exists
    for i, item := range o.items {
        if item.ProductID() == productID {
            o.items[i].increaseQuantity(quantity)
            o.recalculateTotal()
            o.touch()
            return nil
        }
    }

    // Add new item
    item, err := NewOrderItem(productID, name, quantity, unitPrice)
    if err != nil {
        return err
    }

    o.items = append(o.items, *item)
    o.recalculateTotal()
    o.touch()

    o.addEvent(ItemAddedToOrder{
        OrderID:   o.ID(),
        ProductID: productID,
        Quantity:  quantity,
    })

    return nil
}

func (o *Order) RemoveItem(productID shared.EntityID) error {
    if o.status != StatusPending {
        return ErrOrderNotModifiable
    }

    for i, item := range o.items {
        if item.ProductID() == productID {
            o.items = append(o.items[:i], o.items[i+1:]...)
            o.recalculateTotal()
            o.touch()
            return nil
        }
    }

    return ErrItemNotFound
}

func (o *Order) Confirm() error {
    if o.status != StatusPending {
        return ErrInvalidStatusTransition
    }
    if len(o.items) == 0 {
        return ErrEmptyOrder
    }

    o.status = StatusConfirmed
    o.touch()

    o.addEvent(OrderConfirmed{
        OrderID:     o.ID(),
        Total:       o.total,
        ConfirmedAt: time.Now(),
    })

    return nil
}

func (o *Order) Ship(trackingNumber string) error {
    if o.status != StatusConfirmed {
        return ErrInvalidStatusTransition
    }

    o.status = StatusShipped
    o.touch()

    o.addEvent(OrderShipped{
        OrderID:        o.ID(),
        TrackingNumber: trackingNumber,
        ShippedAt:      time.Now(),
    })

    return nil
}

func (o *Order) Cancel(reason string) error {
    if o.status == StatusDelivered || o.status == StatusCancelled {
        return ErrInvalidStatusTransition
    }

    o.status = StatusCancelled
    o.touch()

    o.addEvent(OrderCancelled{
        OrderID:     o.ID(),
        Reason:      reason,
        CancelledAt: time.Now(),
    })

    return nil
}

// Internal helper
func (o *Order) recalculateTotal() {
    total := NewMoney(0, o.total.Currency())
    for _, item := range o.items {
        total = total.Add(item.Subtotal())
    }
    o.total = total
}

// Getters - expose read-only access
func (o *Order) CustomerID() shared.EntityID { return o.customerID }
func (o *Order) Status() Status              { return o.status }
func (o *Order) Total() Money                { return o.total }
func (o *Order) Items() []OrderItem          { return append([]OrderItem{}, o.items...) }

// Event management
func (o *Order) addEvent(event DomainEvent) {
    o.events = append(o.events, event)
}

func (o *Order) PullEvents() []DomainEvent {
    events := o.events
    o.events = make([]DomainEvent, 0)
    return events
}
```

## Child Entity

```go
// internal/domain/order/order_item.go
package order

import (
    "myproject/internal/domain/shared"
)

// OrderItem is a child entity (identity within aggregate)
type OrderItem struct {
    id        shared.EntityID
    productID shared.EntityID
    name      string
    quantity  int
    unitPrice Money
}

func NewOrderItem(productID shared.EntityID, name string, quantity int, unitPrice Money) (*OrderItem, error) {
    if quantity <= 0 {
        return nil, ErrInvalidQuantity
    }

    return &OrderItem{
        id:        shared.NewEntityID(),
        productID: productID,
        name:      name,
        quantity:  quantity,
        unitPrice: unitPrice,
    }, nil
}

func (i *OrderItem) ID() shared.EntityID        { return i.id }
func (i *OrderItem) ProductID() shared.EntityID { return i.productID }
func (i *OrderItem) Name() string               { return i.name }
func (i *OrderItem) Quantity() int              { return i.quantity }
func (i *OrderItem) UnitPrice() Money           { return i.unitPrice }

func (i *OrderItem) Subtotal() Money {
    return i.unitPrice.Multiply(i.quantity)
}

func (i *OrderItem) increaseQuantity(amount int) {
    i.quantity += amount
}
```

## Value Object

```go
// internal/domain/order/money.go
package order

import (
    "fmt"
)

// Money is an immutable value object
type Money struct {
    amount   int64  // Store as cents to avoid floating point issues
    currency string
}

func NewMoney(amount int64, currency string) Money {
    return Money{
        amount:   amount,
        currency: currency,
    }
}

func (m Money) Amount() int64    { return m.amount }
func (m Money) Currency() string { return m.currency }

func (m Money) Add(other Money) Money {
    if m.currency != other.currency {
        panic("cannot add money with different currencies")
    }
    return Money{
        amount:   m.amount + other.amount,
        currency: m.currency,
    }
}

func (m Money) Subtract(other Money) Money {
    if m.currency != other.currency {
        panic("cannot subtract money with different currencies")
    }
    return Money{
        amount:   m.amount - other.amount,
        currency: m.currency,
    }
}

func (m Money) Multiply(factor int) Money {
    return Money{
        amount:   m.amount * int64(factor),
        currency: m.currency,
    }
}

func (m Money) Equals(other Money) bool {
    return m.amount == other.amount && m.currency == other.currency
}

func (m Money) String() string {
    return fmt.Sprintf("%.2f %s", float64(m.amount)/100, m.currency)
}
```

## Domain Events

```go
// internal/domain/order/events.go
package order

import (
    "time"
    "myproject/internal/domain/shared"
)

type DomainEvent interface {
    EventName() string
    OccurredAt() time.Time
}

type OrderCreated struct {
    OrderID    shared.EntityID
    CustomerID shared.EntityID
    CreatedAt  time.Time
}

func (e OrderCreated) EventName() string   { return "order.created" }
func (e OrderCreated) OccurredAt() time.Time { return e.CreatedAt }

type ItemAddedToOrder struct {
    OrderID   shared.EntityID
    ProductID shared.EntityID
    Quantity  int
    AddedAt   time.Time
}

func (e ItemAddedToOrder) EventName() string   { return "order.item_added" }
func (e ItemAddedToOrder) OccurredAt() time.Time { return e.AddedAt }

type OrderConfirmed struct {
    OrderID     shared.EntityID
    Total       Money
    ConfirmedAt time.Time
}

func (e OrderConfirmed) EventName() string   { return "order.confirmed" }
func (e OrderConfirmed) OccurredAt() time.Time { return e.ConfirmedAt }

type OrderShipped struct {
    OrderID        shared.EntityID
    TrackingNumber string
    ShippedAt      time.Time
}

func (e OrderShipped) EventName() string   { return "order.shipped" }
func (e OrderShipped) OccurredAt() time.Time { return e.ShippedAt }

type OrderCancelled struct {
    OrderID     shared.EntityID
    Reason      string
    CancelledAt time.Time
}

func (e OrderCancelled) EventName() string   { return "order.cancelled" }
func (e OrderCancelled) OccurredAt() time.Time { return e.CancelledAt }
```

## Repository Interface

```go
// internal/domain/order/repository.go
package order

import (
    "context"
    "myproject/internal/domain/shared"
)

type Repository interface {
    // Persistence
    Save(ctx context.Context, order *Order) error
    FindByID(ctx context.Context, id shared.EntityID) (*Order, error)

    // Queries
    FindByCustomer(ctx context.Context, customerID shared.EntityID) ([]*Order, error)
    FindByStatus(ctx context.Context, status Status) ([]*Order, error)

    // For reporting (consider using separate read models)
    CountByStatus(ctx context.Context) (map[Status]int64, error)
}
```

## Domain Service

```go
// internal/domain/order/service.go
package order

import (
    "context"
    "myproject/internal/domain/shared"
)

// Domain service for operations spanning multiple aggregates
type PricingService interface {
    CalculateDiscount(ctx context.Context, order *Order) (Money, error)
}

type InventoryService interface {
    CheckAvailability(ctx context.Context, productID shared.EntityID, quantity int) (bool, error)
    Reserve(ctx context.Context, productID shared.EntityID, quantity int) error
}
```

## DDD Principles

1. **Ubiquitous Language**: Use domain terms consistently
2. **Bounded Contexts**: Clear boundaries between domains
3. **Aggregates**: Consistency boundaries with single root
4. **Value Objects**: Immutable, compared by value
5. **Domain Events**: Capture important domain occurrences
6. **Repositories**: Collection-like interface for aggregates
