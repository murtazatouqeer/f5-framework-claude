# Hexagonal Architecture (Ports and Adapters)

Clean architecture pattern isolating domain logic from external concerns with explicit ports and adapters.

## Overview

```
                    ┌─────────────────────────────────────────┐
                    │            Input Adapters               │
                    │  (REST Controllers, CLI, Message Queue) │
                    └─────────────────────┬───────────────────┘
                                          │
                    ┌─────────────────────▼───────────────────┐
                    │             Input Ports                  │
                    │         (Use Case Interfaces)           │
                    └─────────────────────┬───────────────────┘
                                          │
                    ┌─────────────────────▼───────────────────┐
                    │               Domain                     │
                    │   (Entities, Value Objects, Services)   │
                    └─────────────────────┬───────────────────┘
                                          │
                    ┌─────────────────────▼───────────────────┐
                    │            Output Ports                  │
                    │      (Repository Interfaces)            │
                    └─────────────────────┬───────────────────┘
                                          │
                    ┌─────────────────────▼───────────────────┐
                    │           Output Adapters                │
                    │   (JPA Repository, External APIs)       │
                    └─────────────────────────────────────────┘
```

## Package Structure

```
com.example.app/
├── domain/                      # Core domain (no Spring dependencies)
│   ├── model/
│   │   ├── Product.java
│   │   ├── ProductId.java      # Value object
│   │   └── Money.java          # Value object
│   ├── service/
│   │   └── ProductDomainService.java
│   └── exception/
│       └── DomainException.java
├── application/                 # Application layer
│   ├── port/
│   │   ├── in/                 # Input ports (use cases)
│   │   │   ├── CreateProductUseCase.java
│   │   │   └── GetProductUseCase.java
│   │   └── out/                # Output ports (repositories)
│   │       ├── ProductRepository.java
│   │       └── NotificationService.java
│   └── service/                # Use case implementations
│       └── ProductApplicationService.java
└── infrastructure/              # Adapters
    ├── adapter/
    │   ├── in/
    │   │   ├── web/
    │   │   │   ├── ProductController.java
    │   │   │   └── dto/
    │   │   └── messaging/
    │   │       └── ProductMessageListener.java
    │   └── out/
    │       ├── persistence/
    │       │   ├── ProductJpaRepository.java
    │       │   ├── ProductJpaEntity.java
    │       │   └── ProductRepositoryAdapter.java
    │       └── notification/
    │           └── EmailNotificationAdapter.java
    └── config/
        └── BeanConfig.java
```

## Implementation

### Domain Layer (Core)

```java
package com.example.app.domain.model;

import lombok.Getter;
import java.util.UUID;

/**
 * Product aggregate root.
 * Pure domain object - no framework annotations.
 */
@Getter
public class Product {

    private final ProductId id;
    private String name;
    private String description;
    private Money price;
    private int stock;
    private ProductStatus status;

    // Private constructor - use factory methods
    private Product(ProductId id, String name, Money price) {
        this.id = id;
        this.name = name;
        this.price = price;
        this.stock = 0;
        this.status = ProductStatus.DRAFT;
    }

    // Factory method
    public static Product create(String name, Money price) {
        validateName(name);
        validatePrice(price);
        return new Product(ProductId.generate(), name, price);
    }

    // Reconstitution from persistence
    public static Product reconstitute(
            ProductId id, String name, String description,
            Money price, int stock, ProductStatus status) {
        Product product = new Product(id, name, price);
        product.description = description;
        product.stock = stock;
        product.status = status;
        return product;
    }

    // Domain behavior
    public void activate() {
        if (this.stock <= 0) {
            throw new DomainException("Cannot activate product with no stock");
        }
        this.status = ProductStatus.ACTIVE;
    }

    public void deactivate() {
        this.status = ProductStatus.INACTIVE;
    }

    public void updatePrice(Money newPrice) {
        validatePrice(newPrice);
        this.price = newPrice;
    }

    public void addStock(int quantity) {
        if (quantity <= 0) {
            throw new DomainException("Quantity must be positive");
        }
        this.stock += quantity;
    }

    public void removeStock(int quantity) {
        if (quantity > this.stock) {
            throw new InsufficientStockException(this.id, quantity, this.stock);
        }
        this.stock -= quantity;
    }

    public boolean isAvailable() {
        return status == ProductStatus.ACTIVE && stock > 0;
    }

    // Validation
    private static void validateName(String name) {
        if (name == null || name.isBlank()) {
            throw new DomainException("Product name is required");
        }
        if (name.length() > 100) {
            throw new DomainException("Product name too long");
        }
    }

    private static void validatePrice(Money price) {
        if (price == null || price.isNegative()) {
            throw new DomainException("Price must be positive");
        }
    }
}
```

### Value Objects

```java
package com.example.app.domain.model;

import java.util.UUID;

/**
 * Product ID value object.
 */
public record ProductId(UUID value) {

    public ProductId {
        if (value == null) {
            throw new IllegalArgumentException("Product ID cannot be null");
        }
    }

    public static ProductId generate() {
        return new ProductId(UUID.randomUUID());
    }

    public static ProductId of(UUID value) {
        return new ProductId(value);
    }

    public static ProductId of(String value) {
        return new ProductId(UUID.fromString(value));
    }

    @Override
    public String toString() {
        return value.toString();
    }
}

/**
 * Money value object.
 */
public record Money(BigDecimal amount, Currency currency) {

    public static final Currency DEFAULT_CURRENCY = Currency.getInstance("USD");

    public Money {
        if (amount == null) {
            throw new IllegalArgumentException("Amount cannot be null");
        }
        if (currency == null) {
            currency = DEFAULT_CURRENCY;
        }
        amount = amount.setScale(2, RoundingMode.HALF_UP);
    }

    public static Money of(BigDecimal amount) {
        return new Money(amount, DEFAULT_CURRENCY);
    }

    public static Money of(double amount) {
        return new Money(BigDecimal.valueOf(amount), DEFAULT_CURRENCY);
    }

    public boolean isNegative() {
        return amount.signum() < 0;
    }

    public boolean isZero() {
        return amount.signum() == 0;
    }

    public Money add(Money other) {
        validateSameCurrency(other);
        return new Money(this.amount.add(other.amount), this.currency);
    }

    public Money multiply(int quantity) {
        return new Money(this.amount.multiply(BigDecimal.valueOf(quantity)), this.currency);
    }

    private void validateSameCurrency(Money other) {
        if (!this.currency.equals(other.currency)) {
            throw new IllegalArgumentException("Currency mismatch");
        }
    }
}
```

### Input Ports (Use Cases)

```java
package com.example.app.application.port.in;

/**
 * Input port for creating products.
 */
public interface CreateProductUseCase {

    ProductId execute(CreateProductCommand command);

    record CreateProductCommand(
        String name,
        String description,
        BigDecimal price,
        String currencyCode
    ) {
        public CreateProductCommand {
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException("Name is required");
            }
            if (price == null) {
                throw new IllegalArgumentException("Price is required");
            }
        }
    }
}

/**
 * Input port for getting products.
 */
public interface GetProductUseCase {

    Optional<ProductView> getById(ProductId id);

    Page<ProductView> search(SearchProductQuery query);

    record SearchProductQuery(
        String name,
        String category,
        BigDecimal minPrice,
        BigDecimal maxPrice,
        int page,
        int size
    ) {}

    record ProductView(
        ProductId id,
        String name,
        String description,
        Money price,
        int stock,
        String status
    ) {}
}
```

### Output Ports (Repository Interfaces)

```java
package com.example.app.application.port.out;

import com.example.app.domain.model.Product;
import com.example.app.domain.model.ProductId;

/**
 * Output port for product persistence.
 * Defined in application layer, implemented in infrastructure.
 */
public interface ProductRepository {

    Product save(Product product);

    Optional<Product> findById(ProductId id);

    Page<Product> findAll(Pageable pageable);

    boolean existsById(ProductId id);

    void deleteById(ProductId id);
}

/**
 * Output port for notifications.
 */
public interface NotificationService {

    void notifyProductCreated(ProductId productId, String productName);
}
```

### Application Service (Use Case Implementation)

```java
package com.example.app.application.service;

import com.example.app.application.port.in.CreateProductUseCase;
import com.example.app.application.port.in.GetProductUseCase;
import com.example.app.application.port.out.NotificationService;
import com.example.app.application.port.out.ProductRepository;
import com.example.app.domain.model.*;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * Application service implementing use cases.
 * Orchestrates domain objects and ports.
 */
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class ProductApplicationService implements CreateProductUseCase, GetProductUseCase {

    private final ProductRepository productRepository;
    private final NotificationService notificationService;

    @Override
    @Transactional
    public ProductId execute(CreateProductCommand command) {
        // Create domain object using factory
        Money price = new Money(
            command.price(),
            Currency.getInstance(command.currencyCode())
        );

        Product product = Product.create(command.name(), price);

        if (command.description() != null) {
            product.setDescription(command.description());
        }

        // Persist through output port
        Product saved = productRepository.save(product);

        // Notify through output port
        notificationService.notifyProductCreated(
            saved.getId(),
            saved.getName()
        );

        return saved.getId();
    }

    @Override
    public Optional<ProductView> getById(ProductId id) {
        return productRepository.findById(id)
            .map(this::toProductView);
    }

    @Override
    public Page<ProductView> search(SearchProductQuery query) {
        // Implementation with specifications
        return productRepository.findAll(
            PageRequest.of(query.page(), query.size())
        ).map(this::toProductView);
    }

    private ProductView toProductView(Product product) {
        return new ProductView(
            product.getId(),
            product.getName(),
            product.getDescription(),
            product.getPrice(),
            product.getStock(),
            product.getStatus().name()
        );
    }
}
```

### Input Adapter (REST Controller)

```java
package com.example.app.infrastructure.adapter.in.web;

import com.example.app.application.port.in.CreateProductUseCase;
import com.example.app.application.port.in.CreateProductUseCase.CreateProductCommand;
import com.example.app.application.port.in.GetProductUseCase;
import com.example.app.domain.model.ProductId;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

/**
 * REST adapter - drives the application.
 */
@RestController
@RequestMapping("/api/v1/products")
@RequiredArgsConstructor
public class ProductController {

    private final CreateProductUseCase createProductUseCase;
    private final GetProductUseCase getProductUseCase;

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public CreateProductResponse create(@Valid @RequestBody CreateProductRequest request) {
        CreateProductCommand command = new CreateProductCommand(
            request.name(),
            request.description(),
            request.price(),
            request.currencyCode() != null ? request.currencyCode() : "USD"
        );

        ProductId productId = createProductUseCase.execute(command);

        return new CreateProductResponse(productId.toString());
    }

    @GetMapping("/{id}")
    public ResponseEntity<ProductResponse> getById(@PathVariable UUID id) {
        return getProductUseCase.getById(ProductId.of(id))
            .map(view -> new ProductResponse(
                view.id().toString(),
                view.name(),
                view.description(),
                view.price().amount(),
                view.stock(),
                view.status()
            ))
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }
}

record CreateProductRequest(
    @NotBlank String name,
    String description,
    @NotNull @Positive BigDecimal price,
    String currencyCode
) {}

record CreateProductResponse(String id) {}

record ProductResponse(
    String id,
    String name,
    String description,
    BigDecimal price,
    int stock,
    String status
) {}
```

### Output Adapter (Repository Implementation)

```java
package com.example.app.infrastructure.adapter.out.persistence;

import com.example.app.application.port.out.ProductRepository;
import com.example.app.domain.model.*;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

/**
 * JPA adapter implementing ProductRepository port.
 */
@Component
@RequiredArgsConstructor
public class ProductRepositoryAdapter implements ProductRepository {

    private final ProductJpaRepository jpaRepository;

    @Override
    public Product save(Product product) {
        ProductJpaEntity entity = toJpaEntity(product);
        ProductJpaEntity saved = jpaRepository.save(entity);
        return toDomainModel(saved);
    }

    @Override
    public Optional<Product> findById(ProductId id) {
        return jpaRepository.findById(id.value())
            .map(this::toDomainModel);
    }

    @Override
    public Page<Product> findAll(Pageable pageable) {
        return jpaRepository.findAll(pageable)
            .map(this::toDomainModel);
    }

    @Override
    public boolean existsById(ProductId id) {
        return jpaRepository.existsById(id.value());
    }

    @Override
    public void deleteById(ProductId id) {
        jpaRepository.deleteById(id.value());
    }

    // Mapping methods
    private ProductJpaEntity toJpaEntity(Product product) {
        return ProductJpaEntity.builder()
            .id(product.getId().value())
            .name(product.getName())
            .description(product.getDescription())
            .priceAmount(product.getPrice().amount())
            .priceCurrency(product.getPrice().currency().getCurrencyCode())
            .stock(product.getStock())
            .status(product.getStatus().name())
            .build();
    }

    private Product toDomainModel(ProductJpaEntity entity) {
        return Product.reconstitute(
            ProductId.of(entity.getId()),
            entity.getName(),
            entity.getDescription(),
            new Money(entity.getPriceAmount(),
                     Currency.getInstance(entity.getPriceCurrency())),
            entity.getStock(),
            ProductStatus.valueOf(entity.getStatus())
        );
    }
}

/**
 * JPA entity - infrastructure concern.
 */
@Entity
@Table(name = "products")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
class ProductJpaEntity {

    @Id
    private UUID id;

    @Column(nullable = false)
    private String name;

    private String description;

    @Column(name = "price_amount", nullable = false)
    private BigDecimal priceAmount;

    @Column(name = "price_currency", nullable = false)
    private String priceCurrency;

    @Column(nullable = false)
    private int stock;

    @Column(nullable = false)
    private String status;
}

/**
 * Spring Data JPA repository.
 */
interface ProductJpaRepository extends JpaRepository<ProductJpaEntity, UUID> {
}
```

## Benefits

1. **Domain Isolation**: Domain logic has no framework dependencies
2. **Testability**: Easy to test domain and use cases in isolation
3. **Flexibility**: Easy to swap adapters (different DB, different API)
4. **Clear Dependencies**: Direction of dependencies is always inward

## When to Use

- Complex domain logic
- Long-term maintainability priority
- Multiple entry points (REST, messaging, CLI)
- Team familiar with clean architecture
