# JPA Entity Template

Spring Boot JPA entity template with auditing, soft delete, and optimistic locking.

## Template

```java
package {{package}}.domain.entity;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.SQLDelete;
import org.hibernate.annotations.SQLRestriction;
import org.springframework.data.annotation.CreatedBy;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedBy;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "{{table_name}}")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
@EntityListeners(AuditingEntityListener.class)
@SQLDelete(sql = "UPDATE {{table_name}} SET deleted = true, deleted_at = NOW() WHERE id = ? AND version = ?")
@SQLRestriction("deleted = false")
public class {{Entity}} {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @Column(name = "id", updatable = false, nullable = false)
    private UUID id;

    @Column(name = "name", nullable = false, length = 100)
    private String name;

    @Column(name = "description", length = 2000)
    private String description;

    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false, length = 20)
    @Builder.Default
    private {{Entity}}Status status = {{Entity}}Status.DRAFT;

    // Relationships
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "category_id")
    private Category category;

    @OneToMany(mappedBy = "{{entity}}", cascade = CascadeType.ALL, orphanRemoval = true)
    @Builder.Default
    private Set<{{Entity}}Item> items = new HashSet<>();

    // Auditing fields
    @CreatedDate
    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;

    @LastModifiedDate
    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    @CreatedBy
    @Column(name = "created_by", length = 255)
    private String createdBy;

    @LastModifiedBy
    @Column(name = "updated_by", length = 255)
    private String updatedBy;

    // Soft delete
    @Column(name = "deleted", nullable = false)
    @Builder.Default
    private boolean deleted = false;

    @Column(name = "deleted_at")
    private Instant deletedAt;

    // Optimistic locking
    @Version
    @Column(name = "version", nullable = false)
    @Builder.Default
    private Long version = 0L;

    // ==================== Helper Methods ====================

    public void addItem({{Entity}}Item item) {
        items.add(item);
        item.set{{Entity}}(this);
    }

    public void removeItem({{Entity}}Item item) {
        items.remove(item);
        item.set{{Entity}}(null);
    }

    // ==================== Lifecycle Callbacks ====================

    @PrePersist
    protected void onCreate() {
        // Pre-persist logic
    }

    @PreUpdate
    protected void onUpdate() {
        // Pre-update logic
    }
}
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{package}}` | Base package name | `com.example.app` |
| `{{Entity}}` | Entity name (PascalCase) | `Product` |
| `{{entity}}` | Entity name (camelCase) | `product` |
| `{{table_name}}` | Database table name | `products` |

## Enum Template

```java
package {{package}}.domain.entity;

public enum {{Entity}}Status {
    DRAFT,
    ACTIVE,
    INACTIVE,
    ARCHIVED;

    public boolean isEditable() {
        return this == DRAFT || this == ACTIVE;
    }

    public boolean isDeletable() {
        return this != ACTIVE;
    }
}
```

## Customization Options

### With Embedded Value Objects

```java
@Entity
@Table(name = "{{table_name}}")
public class {{Entity}} {

    @Embedded
    private Money price;

    @Embedded
    @AttributeOverrides({
        @AttributeOverride(name = "street", column = @Column(name = "billing_street")),
        @AttributeOverride(name = "city", column = @Column(name = "billing_city")),
        @AttributeOverride(name = "country", column = @Column(name = "billing_country"))
    })
    private Address billingAddress;
}

@Embeddable
@Getter
@NoArgsConstructor
@AllArgsConstructor
public class Money {
    @Column(precision = 19, scale = 4)
    private BigDecimal amount;

    @Column(length = 3)
    private String currency;
}

@Embeddable
@Getter
@NoArgsConstructor
@AllArgsConstructor
public class Address {
    private String street;
    private String city;
    private String postalCode;
    private String country;
}
```

### With JSON Column

```java
@Entity
@Table(name = "{{table_name}}")
public class {{Entity}} {

    @Type(JsonType.class)
    @Column(name = "metadata", columnDefinition = "jsonb")
    private Map<String, Object> metadata;

    @Type(JsonType.class)
    @Column(name = "tags", columnDefinition = "jsonb")
    private List<String> tags;

    @Type(JsonType.class)
    @Column(name = "config", columnDefinition = "jsonb")
    private {{Entity}}Config config;
}
```

### With Inheritance (Single Table)

```java
@Entity
@Table(name = "payments")
@Inheritance(strategy = InheritanceType.SINGLE_TABLE)
@DiscriminatorColumn(name = "payment_type", discriminatorType = DiscriminatorType.STRING)
public abstract class Payment {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    private BigDecimal amount;
    private Instant paidAt;
}

@Entity
@DiscriminatorValue("CREDIT_CARD")
public class CreditCardPayment extends Payment {
    private String cardLastFour;
    private String cardBrand;
}

@Entity
@DiscriminatorValue("BANK_TRANSFER")
public class BankTransferPayment extends Payment {
    private String bankName;
    private String accountNumber;
}
```

### With Inheritance (Joined)

```java
@Entity
@Table(name = "products")
@Inheritance(strategy = InheritanceType.JOINED)
public abstract class Product {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;
    private String name;
    private BigDecimal price;
}

@Entity
@Table(name = "physical_products")
public class PhysicalProduct extends Product {
    private Double weight;
    private String dimensions;
}

@Entity
@Table(name = "digital_products")
public class DigitalProduct extends Product {
    private String downloadUrl;
    private Long fileSize;
}
```

### With Composite Primary Key

```java
@Entity
@Table(name = "order_items")
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

    private Integer quantity;
    private BigDecimal unitPrice;
}

@Embeddable
@Getter
@NoArgsConstructor
@AllArgsConstructor
@EqualsAndHashCode
public class OrderItemId implements Serializable {
    private UUID orderId;
    private UUID productId;
}
```

### With Element Collection

```java
@Entity
@Table(name = "{{table_name}}")
public class {{Entity}} {

    @ElementCollection
    @CollectionTable(
        name = "{{entity}}_tags",
        joinColumns = @JoinColumn(name = "{{entity}}_id")
    )
    @Column(name = "tag")
    private Set<String> tags = new HashSet<>();

    @ElementCollection
    @CollectionTable(
        name = "{{entity}}_attributes",
        joinColumns = @JoinColumn(name = "{{entity}}_id")
    )
    @MapKeyColumn(name = "attribute_key")
    @Column(name = "attribute_value")
    private Map<String, String> attributes = new HashMap<>();
}
```

### With Natural ID

```java
@Entity
@Table(name = "{{table_name}}")
@NaturalIdCache
@Cache(usage = CacheConcurrencyStrategy.READ_WRITE)
public class {{Entity}} {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @NaturalId
    @Column(name = "sku", nullable = false, unique = true, length = 50)
    private String sku;

    // Repository method
    // Optional<{{Entity}}> findBySimpleNaturalId(String sku);
}
```

## Migration Template

```sql
-- V1__create_{{table_name}}_table.sql
CREATE TABLE {{table_name}} (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description VARCHAR(2000),
    status VARCHAR(20) NOT NULL DEFAULT 'DRAFT',
    category_id UUID REFERENCES categories(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by VARCHAR(255),
    updated_by VARCHAR(255),
    deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    version BIGINT NOT NULL DEFAULT 0,

    CONSTRAINT chk_{{table_name}}_status CHECK (status IN ('DRAFT', 'ACTIVE', 'INACTIVE', 'ARCHIVED'))
);

CREATE INDEX idx_{{table_name}}_name ON {{table_name}}(name);
CREATE INDEX idx_{{table_name}}_status ON {{table_name}}(status) WHERE deleted = FALSE;
CREATE INDEX idx_{{table_name}}_category ON {{table_name}}(category_id);
CREATE INDEX idx_{{table_name}}_created_at ON {{table_name}}(created_at);

COMMENT ON TABLE {{table_name}} IS '{{Entity}} table';
```
