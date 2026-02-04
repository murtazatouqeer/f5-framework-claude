# Domain-Driven Design Patterns

DDD building blocks and tactical patterns for Spring Boot applications.

## Building Blocks Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Bounded Context                         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   Aggregate                          │   │
│  │  ┌─────────────────┐  ┌────────────────────────┐   │   │
│  │  │ Aggregate Root  │  │    Entity              │   │   │
│  │  │   (Product)     │──│   (ProductVariant)     │   │   │
│  │  └────────┬────────┘  └────────────────────────┘   │   │
│  │           │                                         │   │
│  │  ┌────────▼────────┐  ┌────────────────────────┐   │   │
│  │  │  Value Object   │  │    Value Object        │   │   │
│  │  │    (Money)      │  │     (SKU)              │   │   │
│  │  └─────────────────┘  └────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │   Repository    │  │ Domain Service  │                  │
│  └─────────────────┘  └─────────────────┘                  │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │  Domain Event   │  │    Factory      │                  │
│  └─────────────────┘  └─────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

## Aggregate Root

```java
package com.example.app.domain.order;

import lombok.Getter;
import java.util.*;

/**
 * Order aggregate root.
 *
 * - Controls access to aggregate members
 * - Enforces invariants
 * - Only entity accessible from outside aggregate
 */
@Getter
public class Order {

    private final OrderId id;
    private final CustomerId customerId;
    private OrderStatus status;
    private Money totalAmount;
    private final List<OrderLine> lines;
    private final List<DomainEvent> domainEvents;
    private final Instant createdAt;
    private Instant updatedAt;

    // Private constructor - use factory
    private Order(OrderId id, CustomerId customerId) {
        this.id = id;
        this.customerId = customerId;
        this.status = OrderStatus.DRAFT;
        this.totalAmount = Money.ZERO;
        this.lines = new ArrayList<>();
        this.domainEvents = new ArrayList<>();
        this.createdAt = Instant.now();
        this.updatedAt = Instant.now();
    }

    // Factory method
    public static Order create(CustomerId customerId) {
        Order order = new Order(OrderId.generate(), customerId);
        order.registerEvent(new OrderCreatedEvent(order.getId(), customerId));
        return order;
    }

    // ========== Aggregate Behavior ==========

    /**
     * Add item to order.
     * Enforces invariants and maintains consistency.
     */
    public void addItem(ProductId productId, String productName,
                       Money unitPrice, int quantity) {
        validateDraftStatus();
        validateQuantity(quantity);

        // Check if product already in order
        Optional<OrderLine> existingLine = findLineByProduct(productId);

        if (existingLine.isPresent()) {
            existingLine.get().increaseQuantity(quantity);
        } else {
            OrderLine line = new OrderLine(
                OrderLineId.generate(),
                productId,
                productName,
                unitPrice,
                quantity
            );
            this.lines.add(line);
        }

        recalculateTotal();
        this.updatedAt = Instant.now();

        registerEvent(new OrderItemAddedEvent(this.id, productId, quantity));
    }

    /**
     * Remove item from order.
     */
    public void removeItem(ProductId productId) {
        validateDraftStatus();

        OrderLine line = findLineByProduct(productId)
            .orElseThrow(() -> new DomainException("Product not in order"));

        this.lines.remove(line);
        recalculateTotal();
        this.updatedAt = Instant.now();
    }

    /**
     * Place the order.
     */
    public void place() {
        validateDraftStatus();

        if (lines.isEmpty()) {
            throw new DomainException("Cannot place empty order");
        }

        this.status = OrderStatus.PLACED;
        this.updatedAt = Instant.now();

        registerEvent(new OrderPlacedEvent(this.id, this.customerId, this.totalAmount));
    }

    /**
     * Confirm the order.
     */
    public void confirm() {
        if (status != OrderStatus.PLACED) {
            throw new DomainException("Only placed orders can be confirmed");
        }

        this.status = OrderStatus.CONFIRMED;
        this.updatedAt = Instant.now();

        registerEvent(new OrderConfirmedEvent(this.id));
    }

    /**
     * Cancel the order.
     */
    public void cancel(String reason) {
        if (status == OrderStatus.SHIPPED || status == OrderStatus.DELIVERED) {
            throw new DomainException("Cannot cancel shipped/delivered order");
        }

        this.status = OrderStatus.CANCELLED;
        this.updatedAt = Instant.now();

        registerEvent(new OrderCancelledEvent(this.id, reason));
    }

    // ========== Invariant Enforcement ==========

    private void validateDraftStatus() {
        if (status != OrderStatus.DRAFT) {
            throw new DomainException("Order is no longer modifiable");
        }
    }

    private void validateQuantity(int quantity) {
        if (quantity <= 0) {
            throw new DomainException("Quantity must be positive");
        }
    }

    private void recalculateTotal() {
        this.totalAmount = lines.stream()
            .map(OrderLine::getSubtotal)
            .reduce(Money.ZERO, Money::add);
    }

    private Optional<OrderLine> findLineByProduct(ProductId productId) {
        return lines.stream()
            .filter(line -> line.getProductId().equals(productId))
            .findFirst();
    }

    // ========== Domain Events ==========

    private void registerEvent(DomainEvent event) {
        this.domainEvents.add(event);
    }

    public List<DomainEvent> pullDomainEvents() {
        List<DomainEvent> events = new ArrayList<>(domainEvents);
        domainEvents.clear();
        return events;
    }

    // ========== Read-only access to lines ==========

    public List<OrderLine> getLines() {
        return Collections.unmodifiableList(lines);
    }
}
```

## Entity

```java
package com.example.app.domain.order;

import lombok.Getter;

/**
 * Order line entity (part of Order aggregate).
 *
 * - Has identity within aggregate
 * - Lifecycle tied to aggregate root
 */
@Getter
public class OrderLine {

    private final OrderLineId id;
    private final ProductId productId;
    private final String productName;
    private final Money unitPrice;
    private int quantity;

    OrderLine(OrderLineId id, ProductId productId, String productName,
              Money unitPrice, int quantity) {
        this.id = id;
        this.productId = productId;
        this.productName = productName;
        this.unitPrice = unitPrice;
        this.quantity = quantity;
    }

    void increaseQuantity(int amount) {
        if (amount <= 0) {
            throw new DomainException("Amount must be positive");
        }
        this.quantity += amount;
    }

    void decreaseQuantity(int amount) {
        if (amount <= 0) {
            throw new DomainException("Amount must be positive");
        }
        if (this.quantity - amount < 1) {
            throw new DomainException("Quantity cannot be less than 1");
        }
        this.quantity -= amount;
    }

    public Money getSubtotal() {
        return unitPrice.multiply(quantity);
    }
}
```

## Value Objects

```java
package com.example.app.domain.common;

/**
 * Money value object.
 *
 * - Immutable
 * - Equality by value
 * - Self-validating
 */
public record Money(BigDecimal amount, Currency currency) {

    public static final Money ZERO = new Money(BigDecimal.ZERO, Currency.getInstance("USD"));

    public Money {
        Objects.requireNonNull(amount, "Amount cannot be null");
        Objects.requireNonNull(currency, "Currency cannot be null");
        amount = amount.setScale(2, RoundingMode.HALF_UP);
    }

    public static Money of(BigDecimal amount, String currencyCode) {
        return new Money(amount, Currency.getInstance(currencyCode));
    }

    public static Money usd(BigDecimal amount) {
        return new Money(amount, Currency.getInstance("USD"));
    }

    public boolean isNegative() {
        return amount.signum() < 0;
    }

    public boolean isPositive() {
        return amount.signum() > 0;
    }

    public Money add(Money other) {
        assertSameCurrency(other);
        return new Money(this.amount.add(other.amount), this.currency);
    }

    public Money subtract(Money other) {
        assertSameCurrency(other);
        return new Money(this.amount.subtract(other.amount), this.currency);
    }

    public Money multiply(int multiplier) {
        return new Money(this.amount.multiply(BigDecimal.valueOf(multiplier)), this.currency);
    }

    public Money multiply(BigDecimal multiplier) {
        return new Money(this.amount.multiply(multiplier), this.currency);
    }

    private void assertSameCurrency(Money other) {
        if (!this.currency.equals(other.currency)) {
            throw new IllegalArgumentException(
                "Cannot operate on different currencies: " +
                this.currency + " and " + other.currency);
        }
    }
}

/**
 * Address value object.
 */
public record Address(
    String street,
    String city,
    String state,
    String postalCode,
    String country
) {
    public Address {
        Objects.requireNonNull(street, "Street is required");
        Objects.requireNonNull(city, "City is required");
        Objects.requireNonNull(postalCode, "Postal code is required");
        Objects.requireNonNull(country, "Country is required");
    }

    public String getFullAddress() {
        StringBuilder sb = new StringBuilder();
        sb.append(street).append(", ");
        sb.append(city);
        if (state != null && !state.isBlank()) {
            sb.append(", ").append(state);
        }
        sb.append(" ").append(postalCode);
        sb.append(", ").append(country);
        return sb.toString();
    }
}

/**
 * Typed ID value object.
 */
public record OrderId(UUID value) {

    public OrderId {
        Objects.requireNonNull(value, "Order ID cannot be null");
    }

    public static OrderId generate() {
        return new OrderId(UUID.randomUUID());
    }

    public static OrderId of(UUID value) {
        return new OrderId(value);
    }

    public static OrderId of(String value) {
        return new OrderId(UUID.fromString(value));
    }

    @Override
    public String toString() {
        return value.toString();
    }
}
```

## Domain Service

```java
package com.example.app.domain.order;

import lombok.RequiredArgsConstructor;

/**
 * Domain service for pricing calculation.
 *
 * Use when:
 * - Logic doesn't naturally belong to any entity
 * - Operation involves multiple aggregates
 * - Stateless operation
 */
@RequiredArgsConstructor
public class PricingService {

    private final DiscountPolicy discountPolicy;
    private final TaxCalculator taxCalculator;

    /**
     * Calculate final price for order.
     */
    public Money calculateFinalPrice(Order order, Customer customer) {
        Money baseAmount = order.getTotalAmount();

        // Apply discount based on customer tier
        Money discountedAmount = discountPolicy.applyDiscount(baseAmount, customer.getTier());

        // Calculate tax
        Money tax = taxCalculator.calculate(discountedAmount, customer.getAddress());

        return discountedAmount.add(tax);
    }
}

/**
 * Domain service for order placement validation.
 */
@RequiredArgsConstructor
public class OrderPlacementService {

    private final InventoryChecker inventoryChecker;
    private final CreditChecker creditChecker;

    /**
     * Validate if order can be placed.
     */
    public void validatePlacement(Order order, Customer customer) {
        // Check inventory for all items
        for (OrderLine line : order.getLines()) {
            if (!inventoryChecker.isAvailable(line.getProductId(), line.getQuantity())) {
                throw new InsufficientInventoryException(line.getProductId());
            }
        }

        // Check customer credit
        if (!creditChecker.hasCredit(customer.getId(), order.getTotalAmount())) {
            throw new InsufficientCreditException(customer.getId());
        }
    }
}
```

## Repository

```java
package com.example.app.domain.order;

import java.util.Optional;

/**
 * Repository interface (domain layer).
 *
 * - One per aggregate
 * - Returns and accepts domain objects
 * - Implementation in infrastructure layer
 */
public interface OrderRepository {

    Order save(Order order);

    Optional<Order> findById(OrderId id);

    List<Order> findByCustomerId(CustomerId customerId);

    boolean existsById(OrderId id);

    void delete(Order order);
}
```

## Domain Events

```java
package com.example.app.domain.event;

import java.time.Instant;
import java.util.UUID;

/**
 * Base domain event.
 */
public abstract class DomainEvent {

    private final UUID eventId;
    private final Instant occurredOn;

    protected DomainEvent() {
        this.eventId = UUID.randomUUID();
        this.occurredOn = Instant.now();
    }

    public UUID getEventId() {
        return eventId;
    }

    public Instant getOccurredOn() {
        return occurredOn;
    }
}

/**
 * Order placed event.
 */
public class OrderPlacedEvent extends DomainEvent {

    private final OrderId orderId;
    private final CustomerId customerId;
    private final Money totalAmount;

    public OrderPlacedEvent(OrderId orderId, CustomerId customerId, Money totalAmount) {
        super();
        this.orderId = orderId;
        this.customerId = customerId;
        this.totalAmount = totalAmount;
    }

    // Getters...
}
```

## Factory

```java
package com.example.app.domain.order;

import lombok.RequiredArgsConstructor;

/**
 * Factory for complex aggregate creation.
 */
@RequiredArgsConstructor
public class OrderFactory {

    private final ProductCatalog productCatalog;

    /**
     * Create order from cart.
     */
    public Order createFromCart(Cart cart, CustomerId customerId) {
        Order order = Order.create(customerId);

        for (CartItem item : cart.getItems()) {
            Product product = productCatalog.getById(item.getProductId())
                .orElseThrow(() -> new ProductNotFoundException(item.getProductId()));

            order.addItem(
                product.getId(),
                product.getName(),
                product.getPrice(),
                item.getQuantity()
            );
        }

        return order;
    }

    /**
     * Reconstitute order from persistence.
     */
    public Order reconstitute(OrderSnapshot snapshot) {
        // Rebuild aggregate from stored data
        return Order.reconstitute(
            snapshot.getId(),
            snapshot.getCustomerId(),
            snapshot.getStatus(),
            snapshot.getLines(),
            snapshot.getTotalAmount(),
            snapshot.getCreatedAt(),
            snapshot.getUpdatedAt()
        );
    }
}
```

## Specification Pattern

```java
package com.example.app.domain.order;

/**
 * Specification pattern for business rules.
 */
public interface Specification<T> {
    boolean isSatisfiedBy(T candidate);

    default Specification<T> and(Specification<T> other) {
        return candidate -> this.isSatisfiedBy(candidate) && other.isSatisfiedBy(candidate);
    }

    default Specification<T> or(Specification<T> other) {
        return candidate -> this.isSatisfiedBy(candidate) || other.isSatisfiedBy(candidate);
    }

    default Specification<T> not() {
        return candidate -> !this.isSatisfiedBy(candidate);
    }
}

/**
 * High value order specification.
 */
public class HighValueOrderSpecification implements Specification<Order> {

    private final Money threshold;

    public HighValueOrderSpecification(Money threshold) {
        this.threshold = threshold;
    }

    @Override
    public boolean isSatisfiedBy(Order order) {
        return order.getTotalAmount().compareTo(threshold) > 0;
    }
}

// Usage
Specification<Order> highValue = new HighValueOrderSpecification(Money.usd(1000));
Specification<Order> confirmed = order -> order.getStatus() == OrderStatus.CONFIRMED;
Specification<Order> highValueConfirmed = highValue.and(confirmed);

if (highValueConfirmed.isSatisfiedBy(order)) {
    // Apply special handling
}
```

## Best Practices

1. **Aggregate Design**
   - Keep aggregates small
   - Reference other aggregates by ID
   - One transaction = one aggregate

2. **Value Objects**
   - Prefer value objects over primitives
   - Make them immutable
   - Self-validating

3. **Domain Events**
   - Capture state changes
   - Enable loose coupling
   - Support eventual consistency

4. **Repository**
   - One per aggregate
   - Domain interface, infrastructure implementation
   - Never expose persistence details
