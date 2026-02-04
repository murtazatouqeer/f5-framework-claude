# Layered Architecture Pattern

Traditional layered architecture for Spring Boot applications with Controller → Service → Repository pattern.

## Overview

```
┌─────────────────────────────────────────────────┐
│              Presentation Layer                  │
│         (Controllers, DTOs, Mappers)            │
├─────────────────────────────────────────────────┤
│               Business Layer                     │
│           (Services, Domain Logic)              │
├─────────────────────────────────────────────────┤
│              Persistence Layer                   │
│         (Repositories, Entities)                │
├─────────────────────────────────────────────────┤
│               Database Layer                     │
│            (PostgreSQL, MySQL)                  │
└─────────────────────────────────────────────────┘
```

## Layer Responsibilities

### Presentation Layer (Web)

```java
package com.example.app.web.controller;

import com.example.app.service.ProductService;
import com.example.app.web.dto.ProductRequest;
import com.example.app.web.dto.ProductResponse;
import com.example.app.web.mapper.ProductMapper;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

/**
 * REST controller - Presentation layer.
 *
 * Responsibilities:
 * - HTTP request/response handling
 * - Input validation (via @Valid)
 * - DTO transformation
 * - No business logic
 */
@RestController
@RequestMapping("/api/v1/products")
@RequiredArgsConstructor
public class ProductController {

    private final ProductService productService;
    private final ProductMapper productMapper;

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public ResponseEntity<ProductResponse> create(
            @Valid @RequestBody ProductRequest request) {
        // Transform DTO to entity
        var product = productMapper.toEntity(request);

        // Delegate to service
        var created = productService.create(product);

        // Transform entity to response DTO
        return ResponseEntity
            .status(HttpStatus.CREATED)
            .body(productMapper.toResponse(created));
    }

    @GetMapping("/{id}")
    public ResponseEntity<ProductResponse> getById(@PathVariable UUID id) {
        return productService.findById(id)
            .map(productMapper::toResponse)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }
}
```

### Business Layer (Service)

```java
package com.example.app.service.impl;

import com.example.app.domain.entity.Product;
import com.example.app.exception.ProductNotFoundException;
import com.example.app.repository.ProductRepository;
import com.example.app.service.ProductService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * Service implementation - Business layer.
 *
 * Responsibilities:
 * - Business logic and rules
 * - Transaction management
 * - Cross-cutting concerns (logging, caching)
 * - Orchestration of multiple repositories
 */
@Slf4j
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class ProductServiceImpl implements ProductService {

    private final ProductRepository productRepository;
    private final CategoryRepository categoryRepository;
    private final InventoryService inventoryService;

    @Override
    @Transactional
    public Product create(Product product) {
        log.info("Creating product: {}", product.getName());

        // Business validation
        validateProduct(product);

        // Business rule: set default status
        if (product.getStatus() == null) {
            product.setStatus(ProductStatus.DRAFT);
        }

        // Persist
        Product saved = productRepository.save(product);

        // Trigger side effects
        inventoryService.initializeInventory(saved.getId());

        return saved;
    }

    @Override
    public Optional<Product> findById(UUID id) {
        return productRepository.findById(id);
    }

    @Override
    @Transactional
    public Product update(Product product) {
        // Verify exists
        if (!productRepository.existsById(product.getId())) {
            throw new ProductNotFoundException(product.getId());
        }

        validateProduct(product);
        return productRepository.save(product);
    }

    private void validateProduct(Product product) {
        // Business validation rules
        if (product.getPrice().signum() < 0) {
            throw new IllegalArgumentException("Price cannot be negative");
        }

        if (product.getCategoryId() != null) {
            if (!categoryRepository.existsById(product.getCategoryId())) {
                throw new CategoryNotFoundException(product.getCategoryId());
            }
        }
    }
}
```

### Persistence Layer (Repository)

```java
package com.example.app.repository;

import com.example.app.domain.entity.Product;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

/**
 * Repository - Persistence layer.
 *
 * Responsibilities:
 * - Data access operations
 * - Query methods
 * - No business logic
 */
@Repository
public interface ProductRepository extends JpaRepository<Product, UUID> {

    List<Product> findByStatus(ProductStatus status);

    @Query("SELECT p FROM Product p WHERE p.category.id = :categoryId")
    List<Product> findByCategoryId(@Param("categoryId") UUID categoryId);

    boolean existsBySkuIgnoreCase(String sku);
}
```

## Package Structure

```
com.example.app/
├── config/                 # Configuration classes
│   ├── SecurityConfig.java
│   ├── JpaConfig.java
│   └── WebConfig.java
├── domain/                 # Domain model
│   └── entity/
│       ├── BaseEntity.java
│       └── Product.java
├── repository/             # Persistence layer
│   └── ProductRepository.java
├── service/                # Business layer
│   ├── ProductService.java
│   └── impl/
│       └── ProductServiceImpl.java
├── web/                    # Presentation layer
│   ├── controller/
│   │   └── ProductController.java
│   ├── dto/
│   │   ├── ProductRequest.java
│   │   └── ProductResponse.java
│   └── mapper/
│       └── ProductMapper.java
└── exception/              # Exception handling
    ├── ProductNotFoundException.java
    └── GlobalExceptionHandler.java
```

## DTOs and Mappers

### Request DTO

```java
package com.example.app.web.dto;

import jakarta.validation.constraints.*;
import lombok.Data;

@Data
public class ProductRequest {

    @NotBlank(message = "Name is required")
    @Size(max = 100)
    private String name;

    @NotBlank(message = "SKU is required")
    private String sku;

    @NotNull(message = "Price is required")
    @Positive
    private BigDecimal price;

    private UUID categoryId;
}
```

### Response DTO

```java
package com.example.app.web.dto;

import lombok.Data;
import java.math.BigDecimal;
import java.time.Instant;
import java.util.UUID;

@Data
public class ProductResponse {
    private UUID id;
    private String name;
    private String sku;
    private BigDecimal price;
    private String categoryName;
    private Instant createdAt;
    private Instant updatedAt;
}
```

### MapStruct Mapper

```java
package com.example.app.web.mapper;

import com.example.app.domain.entity.Product;
import com.example.app.web.dto.ProductRequest;
import com.example.app.web.dto.ProductResponse;
import org.mapstruct.*;

@Mapper(componentModel = "spring", unmappedTargetPolicy = ReportingPolicy.IGNORE)
public interface ProductMapper {

    Product toEntity(ProductRequest request);

    @Mapping(target = "categoryName", source = "category.name")
    ProductResponse toResponse(Product product);

    @BeanMapping(nullValuePropertyMappingStrategy = NullValuePropertyMappingStrategy.IGNORE)
    void updateEntity(ProductRequest request, @MappingTarget Product product);
}
```

## Layer Communication Rules

1. **Controller → Service**
   - Controller calls service methods
   - Never bypass service to access repository directly
   - Pass domain objects or simple types

2. **Service → Repository**
   - Service calls repository for data access
   - Can call multiple repositories
   - Manages transactions

3. **Service → Service**
   - Services can call other services
   - Avoid circular dependencies
   - Consider domain events for loose coupling

## Benefits

- **Separation of Concerns**: Each layer has clear responsibility
- **Testability**: Easy to mock dependencies
- **Maintainability**: Changes isolated to specific layers
- **Familiarity**: Well-known pattern, easy onboarding

## Anti-Patterns to Avoid

```java
// ❌ Bad: Business logic in controller
@PostMapping
public Product create(@RequestBody ProductRequest request) {
    if (request.getPrice().signum() < 0) {
        throw new IllegalArgumentException("...");  // Should be in service
    }
    return productRepository.save(product);  // Should call service
}

// ❌ Bad: Controller calling repository directly
@GetMapping
public List<Product> list() {
    return productRepository.findAll();  // Should call service
}

// ❌ Bad: Entity exposed in API
@GetMapping("/{id}")
public Product getById(@PathVariable UUID id) {
    return productRepository.findById(id).orElseThrow();  // Should return DTO
}
```

## Best Practices

1. **Keep controllers thin** - Only HTTP handling
2. **Services contain business logic** - Validation, rules, orchestration
3. **Use DTOs** - Never expose entities in API
4. **Transaction at service level** - @Transactional on service methods
5. **Validate at both layers** - Bean validation + business validation
