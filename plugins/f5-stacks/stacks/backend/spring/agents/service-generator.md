# Service Generator Agent

Spring Boot service layer generator with business logic, transactions, and validation.

## Capabilities

- Generate service interfaces and implementations
- Implement transaction management
- Add business validation logic
- Generate event publishing
- Implement caching strategies
- Handle complex business workflows

## Input Requirements

```yaml
entity_name: "Product"
operations:
  - create
  - read
  - update
  - delete
  - search
features:
  - transactions
  - validation
  - events
  - caching
```

## Generated Code Pattern

### Service Interface

```java
package com.example.app.service;

import com.example.app.domain.entity.Product;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

/**
 * Service interface for Product operations.
 *
 * REQ-001: Product Management
 */
public interface ProductService {

    /**
     * Create a new product.
     *
     * @param product Product to create
     * @return Created product with ID
     */
    Product create(Product product);

    /**
     * Find product by ID.
     *
     * @param id Product ID
     * @return Optional containing product if found
     */
    Optional<Product> findById(UUID id);

    /**
     * Find all products with pagination.
     *
     * @param pageable Pagination parameters
     * @return Page of products
     */
    Page<Product> findAll(Pageable pageable);

    /**
     * Search products with filters.
     *
     * @param name Name filter
     * @param category Category filter
     * @param minPrice Minimum price
     * @param maxPrice Maximum price
     * @param pageable Pagination parameters
     * @return Page of matching products
     */
    Page<Product> search(String name, String category,
                        Double minPrice, Double maxPrice,
                        Pageable pageable);

    /**
     * Update existing product.
     *
     * @param product Product to update
     * @return Updated product
     */
    Product update(Product product);

    /**
     * Delete product by ID.
     *
     * @param id Product ID
     */
    void deleteById(UUID id);

    /**
     * Check if product exists.
     *
     * @param id Product ID
     * @return true if exists
     */
    boolean existsById(UUID id);

    /**
     * Count all products.
     *
     * @return Total count
     */
    long count();

    /**
     * Create multiple products.
     *
     * @param products Products to create
     * @return Created products
     */
    List<Product> createAll(List<Product> products);

    /**
     * Delete multiple products.
     *
     * @param ids Product IDs
     */
    void deleteAllById(List<UUID> ids);
}
```

### Service Implementation

```java
package com.example.app.service.impl;

import com.example.app.domain.entity.Product;
import com.example.app.event.ProductCreatedEvent;
import com.example.app.event.ProductDeletedEvent;
import com.example.app.event.ProductUpdatedEvent;
import com.example.app.exception.ProductNotFoundException;
import com.example.app.exception.DuplicateProductException;
import com.example.app.repository.ProductRepository;
import com.example.app.service.ProductService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.CachePut;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

/**
 * Implementation of ProductService.
 *
 * REQ-001: Product Management
 */
@Slf4j
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class ProductServiceImpl implements ProductService {

    private final ProductRepository productRepository;
    private final ApplicationEventPublisher eventPublisher;

    @Override
    @Transactional
    public Product create(Product product) {
        log.info("Creating product: {}", product.getName());

        // Business validation
        validateNewProduct(product);

        // Check for duplicates
        if (productRepository.existsBySkuIgnoreCase(product.getSku())) {
            throw new DuplicateProductException(
                "Product with SKU already exists: " + product.getSku());
        }

        // Save entity
        Product saved = productRepository.save(product);

        // Publish event
        eventPublisher.publishEvent(new ProductCreatedEvent(this, saved));

        log.info("Product created with ID: {}", saved.getId());
        return saved;
    }

    @Override
    @Cacheable(value = "products", key = "#id")
    public Optional<Product> findById(UUID id) {
        log.debug("Finding product by ID: {}", id);
        return productRepository.findById(id);
    }

    @Override
    public Page<Product> findAll(Pageable pageable) {
        log.debug("Finding all products, page: {}", pageable.getPageNumber());
        return productRepository.findAll(pageable);
    }

    @Override
    public Page<Product> search(String name, String category,
                                Double minPrice, Double maxPrice,
                                Pageable pageable) {
        log.debug("Searching products with filters");
        return productRepository.search(name, category, minPrice, maxPrice, pageable);
    }

    @Override
    @Transactional
    @CachePut(value = "products", key = "#product.id")
    public Product update(Product product) {
        log.info("Updating product: {}", product.getId());

        // Verify exists
        if (!productRepository.existsById(product.getId())) {
            throw new ProductNotFoundException(product.getId());
        }

        // Business validation
        validateProductUpdate(product);

        // Update entity
        Product updated = productRepository.save(product);

        // Publish event
        eventPublisher.publishEvent(new ProductUpdatedEvent(this, updated));

        log.info("Product updated: {}", updated.getId());
        return updated;
    }

    @Override
    @Transactional
    @CacheEvict(value = "products", key = "#id")
    public void deleteById(UUID id) {
        log.info("Deleting product: {}", id);

        Product product = productRepository.findById(id)
            .orElseThrow(() -> new ProductNotFoundException(id));

        // Soft delete
        product.setDeleted(true);
        productRepository.save(product);

        // Publish event
        eventPublisher.publishEvent(new ProductDeletedEvent(this, id));

        log.info("Product deleted: {}", id);
    }

    @Override
    public boolean existsById(UUID id) {
        return productRepository.existsById(id);
    }

    @Override
    public long count() {
        return productRepository.count();
    }

    @Override
    @Transactional
    public List<Product> createAll(List<Product> products) {
        log.info("Creating {} products in batch", products.size());

        products.forEach(this::validateNewProduct);

        List<Product> saved = productRepository.saveAll(products);

        saved.forEach(product ->
            eventPublisher.publishEvent(new ProductCreatedEvent(this, product)));

        return saved;
    }

    @Override
    @Transactional
    @CacheEvict(value = "products", allEntries = true)
    public void deleteAllById(List<UUID> ids) {
        log.info("Deleting {} products in batch", ids.size());

        ids.forEach(id -> {
            productRepository.findById(id).ifPresent(product -> {
                product.setDeleted(true);
                productRepository.save(product);
                eventPublisher.publishEvent(new ProductDeletedEvent(this, id));
            });
        });
    }

    // ========== Business Validation ==========

    private void validateNewProduct(Product product) {
        if (product.getPrice() != null && product.getPrice().signum() < 0) {
            throw new IllegalArgumentException("Price cannot be negative");
        }

        if (product.getStock() != null && product.getStock() < 0) {
            throw new IllegalArgumentException("Stock cannot be negative");
        }
    }

    private void validateProductUpdate(Product product) {
        validateNewProduct(product);

        // Additional update-specific validations
        if (product.getVersion() == null) {
            throw new IllegalArgumentException("Version is required for updates");
        }
    }
}
```

### Event Classes

```java
package com.example.app.event;

import com.example.app.domain.entity.Product;
import lombok.Getter;
import org.springframework.context.ApplicationEvent;

@Getter
public class ProductCreatedEvent extends ApplicationEvent {
    private final Product product;

    public ProductCreatedEvent(Object source, Product product) {
        super(source);
        this.product = product;
    }
}

@Getter
public class ProductUpdatedEvent extends ApplicationEvent {
    private final Product product;

    public ProductUpdatedEvent(Object source, Product product) {
        super(source);
        this.product = product;
    }
}

@Getter
public class ProductDeletedEvent extends ApplicationEvent {
    private final UUID productId;

    public ProductDeletedEvent(Object source, UUID productId) {
        super(source);
        this.productId = productId;
    }
}
```

### Event Listener

```java
package com.example.app.event;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.event.EventListener;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Component;

@Slf4j
@Component
@RequiredArgsConstructor
public class ProductEventListener {

    private final NotificationService notificationService;
    private final SearchIndexService searchIndexService;

    @Async
    @EventListener
    public void handleProductCreated(ProductCreatedEvent event) {
        log.info("Handling product created event: {}", event.getProduct().getId());

        // Index for search
        searchIndexService.index(event.getProduct());

        // Send notifications
        notificationService.notifyProductCreated(event.getProduct());
    }

    @Async
    @EventListener
    public void handleProductUpdated(ProductUpdatedEvent event) {
        log.info("Handling product updated event: {}", event.getProduct().getId());

        // Update search index
        searchIndexService.update(event.getProduct());
    }

    @Async
    @EventListener
    public void handleProductDeleted(ProductDeletedEvent event) {
        log.info("Handling product deleted event: {}", event.getProductId());

        // Remove from search index
        searchIndexService.delete(event.getProductId());
    }
}
```

## Generation Rules

1. **Transaction Management**
   - Read operations: `@Transactional(readOnly = true)`
   - Write operations: `@Transactional`
   - Class-level default: read-only

2. **Logging**
   - Log at INFO level for state changes
   - Log at DEBUG level for queries
   - Include relevant identifiers

3. **Caching**
   - Cache frequently read entities
   - Evict on updates/deletes
   - Use meaningful cache names

4. **Events**
   - Publish after successful operations
   - Include relevant entity/ID
   - Handle asynchronously

5. **Validation**
   - Business rules in service layer
   - Input validation in DTOs
   - Throw meaningful exceptions

## Best Practices

- Interface + Implementation pattern
- Keep services focused (Single Responsibility)
- Use dependency injection
- Implement proper logging
- Handle exceptions appropriately
- Use events for loose coupling
- Cache expensive operations
- Document public methods
