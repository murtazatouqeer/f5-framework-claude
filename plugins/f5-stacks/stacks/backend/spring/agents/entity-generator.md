# Entity Generator Agent

Spring Boot JPA entity generator with relationships, auditing, and soft delete support.

## Capabilities

- Generate JPA entities with proper mappings
- Implement entity relationships (OneToMany, ManyToOne, ManyToMany)
- Add auditing fields (createdAt, updatedAt, createdBy)
- Implement soft delete pattern
- Generate base entity classes
- Handle optimistic locking

## Input Requirements

```yaml
entity_name: "Product"
table_name: "products"
fields:
  - name: name
    type: String
    constraints: [NotBlank, Size(max=100)]
  - name: price
    type: BigDecimal
    constraints: [NotNull, Positive]
  - name: category
    type: Category
    relationship: ManyToOne
features:
  - auditing
  - soft_delete
  - versioning
```

## Generated Code Pattern

### Base Entity

```java
package com.example.app.domain.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;
import org.springframework.data.annotation.CreatedBy;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedBy;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.io.Serializable;
import java.time.Instant;
import java.util.UUID;

/**
 * Base entity with common fields.
 */
@Getter
@Setter
@MappedSuperclass
@EntityListeners(AuditingEntityListener.class)
public abstract class BaseEntity implements Serializable {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @Column(name = "id", updatable = false, nullable = false)
    private UUID id;

    @Version
    @Column(name = "version")
    private Long version;

    @CreatedDate
    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;

    @LastModifiedDate
    @Column(name = "updated_at")
    private Instant updatedAt;

    @CreatedBy
    @Column(name = "created_by", updatable = false)
    private String createdBy;

    @LastModifiedBy
    @Column(name = "updated_by")
    private String updatedBy;

    @Column(name = "deleted", nullable = false)
    private boolean deleted = false;

    @Column(name = "deleted_at")
    private Instant deletedAt;

    /**
     * Soft delete this entity.
     */
    public void softDelete() {
        this.deleted = true;
        this.deletedAt = Instant.now();
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof BaseEntity that)) return false;
        return id != null && id.equals(that.id);
    }

    @Override
    public int hashCode() {
        return getClass().hashCode();
    }
}
```

### Product Entity

```java
package com.example.app.domain.entity;

import jakarta.persistence.*;
import jakarta.validation.constraints.*;
import lombok.*;
import org.hibernate.annotations.SQLDelete;
import org.hibernate.annotations.SQLRestriction;

import java.math.BigDecimal;
import java.util.HashSet;
import java.util.Set;

/**
 * Product entity.
 *
 * REQ-001: Product Management
 */
@Entity
@Table(name = "products", indexes = {
    @Index(name = "idx_product_sku", columnList = "sku", unique = true),
    @Index(name = "idx_product_category", columnList = "category_id"),
    @Index(name = "idx_product_name", columnList = "name")
})
@SQLDelete(sql = "UPDATE products SET deleted = true, deleted_at = NOW() WHERE id = ? AND version = ?")
@SQLRestriction("deleted = false")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Product extends BaseEntity {

    @NotBlank(message = "Name is required")
    @Size(max = 100, message = "Name must not exceed 100 characters")
    @Column(name = "name", nullable = false, length = 100)
    private String name;

    @Size(max = 2000, message = "Description must not exceed 2000 characters")
    @Column(name = "description", length = 2000)
    private String description;

    @NotBlank(message = "SKU is required")
    @Size(max = 50, message = "SKU must not exceed 50 characters")
    @Column(name = "sku", nullable = false, unique = true, length = 50)
    private String sku;

    @NotNull(message = "Price is required")
    @Positive(message = "Price must be positive")
    @Column(name = "price", nullable = false, precision = 19, scale = 4)
    private BigDecimal price;

    @PositiveOrZero(message = "Stock cannot be negative")
    @Column(name = "stock", nullable = false)
    @Builder.Default
    private Integer stock = 0;

    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false, length = 20)
    @Builder.Default
    private ProductStatus status = ProductStatus.DRAFT;

    @Column(name = "image_url")
    private String imageUrl;

    // ========== Relationships ==========

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "category_id")
    private Category category;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "brand_id")
    private Brand brand;

    @OneToMany(mappedBy = "product", cascade = CascadeType.ALL, orphanRemoval = true)
    @Builder.Default
    private Set<ProductImage> images = new HashSet<>();

    @ManyToMany
    @JoinTable(
        name = "product_tags",
        joinColumns = @JoinColumn(name = "product_id"),
        inverseJoinColumns = @JoinColumn(name = "tag_id")
    )
    @Builder.Default
    private Set<Tag> tags = new HashSet<>();

    // ========== Helper Methods ==========

    public void addImage(ProductImage image) {
        images.add(image);
        image.setProduct(this);
    }

    public void removeImage(ProductImage image) {
        images.remove(image);
        image.setProduct(null);
    }

    public void addTag(Tag tag) {
        tags.add(tag);
        tag.getProducts().add(this);
    }

    public void removeTag(Tag tag) {
        tags.remove(tag);
        tag.getProducts().remove(this);
    }

    /**
     * Check if product is available for purchase.
     */
    public boolean isAvailable() {
        return status == ProductStatus.ACTIVE && stock > 0 && !isDeleted();
    }

    /**
     * Decrease stock by quantity.
     *
     * @param quantity Quantity to decrease
     * @throws IllegalStateException if insufficient stock
     */
    public void decreaseStock(int quantity) {
        if (stock < quantity) {
            throw new IllegalStateException(
                "Insufficient stock. Available: " + stock + ", Requested: " + quantity);
        }
        this.stock -= quantity;
    }

    /**
     * Increase stock by quantity.
     *
     * @param quantity Quantity to increase
     */
    public void increaseStock(int quantity) {
        if (quantity < 0) {
            throw new IllegalArgumentException("Quantity must be positive");
        }
        this.stock += quantity;
    }
}
```

### Enum Types

```java
package com.example.app.domain.entity;

/**
 * Product status enumeration.
 */
public enum ProductStatus {
    DRAFT,
    ACTIVE,
    INACTIVE,
    DISCONTINUED
}
```

### Embedded Value Objects

```java
package com.example.app.domain.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Embeddable;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import lombok.*;

/**
 * Address value object.
 */
@Embeddable
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Address {

    @NotBlank
    @Column(name = "street", length = 200)
    private String street;

    @NotBlank
    @Column(name = "city", length = 100)
    private String city;

    @Column(name = "state", length = 100)
    private String state;

    @NotBlank
    @Pattern(regexp = "^[0-9]{5}(-[0-9]{4})?$")
    @Column(name = "postal_code", length = 20)
    private String postalCode;

    @NotBlank
    @Column(name = "country", length = 2)
    private String country;
}
```

### Entity with Composite Key

```java
package com.example.app.domain.entity;

import jakarta.persistence.*;
import lombok.*;

import java.io.Serializable;
import java.util.UUID;

/**
 * Order item with composite key.
 */
@Entity
@Table(name = "order_items")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class OrderItem {

    @EmbeddedId
    private OrderItemId id;

    @ManyToOne(fetch = FetchType.LAZY)
    @MapsId("orderId")
    @JoinColumn(name = "order_id")
    private Order order;

    @ManyToOne(fetch = FetchType.LAZY)
    @MapsId("productId")
    @JoinColumn(name = "product_id")
    private Product product;

    @Column(name = "quantity", nullable = false)
    private Integer quantity;

    @Column(name = "unit_price", nullable = false)
    private BigDecimal unitPrice;
}

@Embeddable
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@EqualsAndHashCode
public class OrderItemId implements Serializable {

    @Column(name = "order_id")
    private UUID orderId;

    @Column(name = "product_id")
    private UUID productId;
}
```

## Generation Rules

1. **Primary Key**
   - Use UUID for IDs
   - GenerationType.UUID strategy
   - Never expose sequential IDs

2. **Relationships**
   - Use FetchType.LAZY by default
   - Cascade wisely (avoid CascadeType.ALL unless needed)
   - Use orphanRemoval for owned collections
   - Implement helper methods for bidirectional relationships

3. **Indexes**
   - Index foreign keys
   - Index frequently queried fields
   - Add unique constraints via indexes

4. **Soft Delete**
   - Use @SQLDelete for soft delete
   - Use @SQLRestriction to filter deleted
   - Include deletedAt timestamp

5. **Auditing**
   - Always include audit fields
   - Use @EntityListeners
   - Track createdBy/updatedBy

6. **Validation**
   - Use Jakarta validation constraints
   - Validate at entity level
   - Include meaningful messages

## Best Practices

- Extend BaseEntity for common fields
- Use Lombok for boilerplate reduction
- Implement equals/hashCode based on ID
- Use builder pattern for complex entities
- Document business rules in entity
- Keep domain logic in entity when appropriate
- Use value objects for composite values
- Never expose internal collections directly
