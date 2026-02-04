# JPA Entity Patterns

JPA entity mapping patterns, relationships, and best practices for Spring Boot.

## Entity Basics

### Base Entity with Auditing

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

### Enable JPA Auditing

```java
@Configuration
@EnableJpaAuditing(auditorAwareRef = "auditorProvider")
public class JpaConfig {

    @Bean
    public AuditorAware<String> auditorProvider() {
        return () -> Optional.ofNullable(SecurityContextHolder.getContext())
            .map(SecurityContext::getAuthentication)
            .filter(Authentication::isAuthenticated)
            .map(Authentication::getName);
    }
}
```

## Relationship Mappings

### One-to-Many (Bidirectional)

```java
// Parent entity
@Entity
@Table(name = "categories")
public class Category extends BaseEntity {

    @Column(nullable = false)
    private String name;

    @OneToMany(
        mappedBy = "category",
        cascade = CascadeType.ALL,
        orphanRemoval = true
    )
    @Builder.Default
    private Set<Product> products = new HashSet<>();

    // Helper methods for bidirectional sync
    public void addProduct(Product product) {
        products.add(product);
        product.setCategory(this);
    }

    public void removeProduct(Product product) {
        products.remove(product);
        product.setCategory(null);
    }
}

// Child entity
@Entity
@Table(name = "products")
public class Product extends BaseEntity {

    @Column(nullable = false)
    private String name;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "category_id")
    private Category category;
}
```

### Many-to-Many

```java
@Entity
@Table(name = "products")
public class Product extends BaseEntity {

    @ManyToMany
    @JoinTable(
        name = "product_tags",
        joinColumns = @JoinColumn(name = "product_id"),
        inverseJoinColumns = @JoinColumn(name = "tag_id")
    )
    @Builder.Default
    private Set<Tag> tags = new HashSet<>();

    public void addTag(Tag tag) {
        this.tags.add(tag);
        tag.getProducts().add(this);
    }

    public void removeTag(Tag tag) {
        this.tags.remove(tag);
        tag.getProducts().remove(this);
    }
}

@Entity
@Table(name = "tags")
public class Tag extends BaseEntity {

    @Column(nullable = false, unique = true)
    private String name;

    @ManyToMany(mappedBy = "tags")
    @Builder.Default
    private Set<Product> products = new HashSet<>();
}
```

### Many-to-Many with Extra Columns

```java
// Join entity
@Entity
@Table(name = "order_items")
public class OrderItem {

    @EmbeddedId
    private OrderItemId id;

    @ManyToOne(fetch = FetchType.LAZY)
    @MapsId("orderId")
    private Order order;

    @ManyToOne(fetch = FetchType.LAZY)
    @MapsId("productId")
    private Product product;

    // Extra columns
    @Column(nullable = false)
    private Integer quantity;

    @Column(nullable = false)
    private BigDecimal unitPrice;

    @Column(nullable = false)
    private BigDecimal subtotal;
}

@Embeddable
public class OrderItemId implements Serializable {

    @Column(name = "order_id")
    private UUID orderId;

    @Column(name = "product_id")
    private UUID productId;

    // equals and hashCode
}
```

### One-to-One

```java
@Entity
@Table(name = "users")
public class User extends BaseEntity {

    @Column(nullable = false)
    private String email;

    @OneToOne(
        mappedBy = "user",
        cascade = CascadeType.ALL,
        orphanRemoval = true,
        fetch = FetchType.LAZY
    )
    private UserProfile profile;

    public void setProfile(UserProfile profile) {
        if (profile == null) {
            if (this.profile != null) {
                this.profile.setUser(null);
            }
        } else {
            profile.setUser(this);
        }
        this.profile = profile;
    }
}

@Entity
@Table(name = "user_profiles")
public class UserProfile extends BaseEntity {

    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id")
    private User user;

    private String firstName;
    private String lastName;
    private String phone;
}
```

## Embedded Objects

### Embeddable Value Object

```java
@Embeddable
public class Address {

    @Column(name = "street", length = 200)
    private String street;

    @Column(name = "city", length = 100)
    private String city;

    @Column(name = "state", length = 100)
    private String state;

    @Column(name = "postal_code", length = 20)
    private String postalCode;

    @Column(name = "country", length = 2)
    private String country;
}

@Entity
@Table(name = "customers")
public class Customer extends BaseEntity {

    @Embedded
    @AttributeOverrides({
        @AttributeOverride(name = "street", column = @Column(name = "billing_street")),
        @AttributeOverride(name = "city", column = @Column(name = "billing_city")),
        @AttributeOverride(name = "state", column = @Column(name = "billing_state")),
        @AttributeOverride(name = "postalCode", column = @Column(name = "billing_postal_code")),
        @AttributeOverride(name = "country", column = @Column(name = "billing_country"))
    })
    private Address billingAddress;

    @Embedded
    @AttributeOverrides({
        @AttributeOverride(name = "street", column = @Column(name = "shipping_street")),
        @AttributeOverride(name = "city", column = @Column(name = "shipping_city")),
        @AttributeOverride(name = "state", column = @Column(name = "shipping_state")),
        @AttributeOverride(name = "postalCode", column = @Column(name = "shipping_postal_code")),
        @AttributeOverride(name = "country", column = @Column(name = "shipping_country"))
    })
    private Address shippingAddress;
}
```

### Collection of Embeddables

```java
@Entity
@Table(name = "products")
public class Product extends BaseEntity {

    @ElementCollection
    @CollectionTable(
        name = "product_attributes",
        joinColumns = @JoinColumn(name = "product_id")
    )
    @Builder.Default
    private Set<ProductAttribute> attributes = new HashSet<>();
}

@Embeddable
public class ProductAttribute {

    @Column(name = "attribute_name", nullable = false)
    private String name;

    @Column(name = "attribute_value", nullable = false)
    private String value;
}
```

## Soft Delete Pattern

```java
@Entity
@Table(name = "products")
@SQLDelete(sql = "UPDATE products SET deleted = true, deleted_at = NOW() WHERE id = ? AND version = ?")
@SQLRestriction("deleted = false")
public class Product extends BaseEntity {

    @Column(name = "deleted", nullable = false)
    @Builder.Default
    private boolean deleted = false;

    @Column(name = "deleted_at")
    private Instant deletedAt;

    public void softDelete() {
        this.deleted = true;
        this.deletedAt = Instant.now();
    }
}
```

## Inheritance Strategies

### Single Table Inheritance

```java
@Entity
@Table(name = "payments")
@Inheritance(strategy = InheritanceType.SINGLE_TABLE)
@DiscriminatorColumn(name = "payment_type", discriminatorType = DiscriminatorType.STRING)
public abstract class Payment extends BaseEntity {

    @Column(nullable = false)
    private BigDecimal amount;

    @Enumerated(EnumType.STRING)
    private PaymentStatus status;
}

@Entity
@DiscriminatorValue("CREDIT_CARD")
public class CreditCardPayment extends Payment {

    @Column(name = "card_last_four")
    private String cardLastFour;

    @Column(name = "card_brand")
    private String cardBrand;
}

@Entity
@DiscriminatorValue("BANK_TRANSFER")
public class BankTransferPayment extends Payment {

    @Column(name = "bank_name")
    private String bankName;

    @Column(name = "account_number")
    private String accountNumber;
}
```

### Joined Table Inheritance

```java
@Entity
@Table(name = "vehicles")
@Inheritance(strategy = InheritanceType.JOINED)
public abstract class Vehicle extends BaseEntity {

    @Column(nullable = false)
    private String manufacturer;

    @Column(nullable = false)
    private String model;
}

@Entity
@Table(name = "cars")
@PrimaryKeyJoinColumn(name = "vehicle_id")
public class Car extends Vehicle {

    @Column(name = "num_doors")
    private int numberOfDoors;

    @Column(name = "trunk_capacity")
    private int trunkCapacity;
}

@Entity
@Table(name = "motorcycles")
@PrimaryKeyJoinColumn(name = "vehicle_id")
public class Motorcycle extends Vehicle {

    @Column(name = "engine_displacement")
    private int engineDisplacement;

    private boolean hasSidecar;
}
```

## Enum Mapping

```java
// String enum (recommended)
@Enumerated(EnumType.STRING)
@Column(name = "status", length = 20)
private OrderStatus status;

// Ordinal enum (not recommended - order dependent)
@Enumerated(EnumType.ORDINAL)
private Priority priority;

// Custom converter for complex enums
@Converter(autoApply = true)
public class OrderStatusConverter implements AttributeConverter<OrderStatus, String> {

    @Override
    public String convertToDatabaseColumn(OrderStatus status) {
        return status != null ? status.getCode() : null;
    }

    @Override
    public OrderStatus convertToEntityAttribute(String code) {
        return code != null ? OrderStatus.fromCode(code) : null;
    }
}
```

## JSON Column

```java
@Entity
@Table(name = "products")
public class Product extends BaseEntity {

    @Type(JsonType.class)
    @Column(name = "metadata", columnDefinition = "jsonb")
    private Map<String, Object> metadata = new HashMap<>();

    @Type(JsonType.class)
    @Column(name = "specifications", columnDefinition = "jsonb")
    private ProductSpecifications specifications;
}

// DTO for JSON column
public record ProductSpecifications(
    String dimensions,
    double weight,
    String color,
    List<String> materials
) {}
```

## Performance Patterns

### Fetch Optimization

```java
// Entity graph for eager loading
@Entity
@NamedEntityGraph(
    name = "Product.withCategoryAndTags",
    attributeNodes = {
        @NamedAttributeNode("category"),
        @NamedAttributeNode("tags")
    }
)
public class Product extends BaseEntity {
    // ...
}

// Repository usage
@EntityGraph(value = "Product.withCategoryAndTags")
Optional<Product> findById(UUID id);

// Or inline
@EntityGraph(attributePaths = {"category", "brand", "images"})
List<Product> findByStatus(ProductStatus status);
```

### Batch Size for Collections

```java
@OneToMany(mappedBy = "product")
@BatchSize(size = 20)  // Fetch 20 collections at a time
private Set<ProductImage> images = new HashSet<>();
```

## Best Practices

1. **Use Lazy Loading** - Default for associations
2. **Avoid Bidirectional if Not Needed** - Simpler, fewer bugs
3. **Use Set for Collections** - Better performance for many-to-many
4. **Implement equals/hashCode** - Based on ID or business key
5. **Use @Version** - Optimistic locking
6. **Prefer @Enumerated(STRING)** - Safer than ORDINAL
7. **Index Foreign Keys** - Better query performance
8. **Use @BatchSize** - Avoid N+1 problems
