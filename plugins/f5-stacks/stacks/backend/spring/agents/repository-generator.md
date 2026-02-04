# Repository Generator Agent

Spring Data JPA repository generator with query methods, specifications, and projections.

## Capabilities

- Generate Spring Data JPA repositories
- Create derived query methods
- Implement custom JPQL/native queries
- Generate JPA Specifications for dynamic queries
- Create projections for optimized queries
- Implement custom repository fragments

## Input Requirements

```yaml
entity_name: "Product"
queries:
  - findByCategory
  - findByPriceRange
  - search
features:
  - specifications
  - projections
  - pagination
  - custom_queries
```

## Generated Code Pattern

### Basic Repository

```java
package com.example.app.repository;

import com.example.app.domain.entity.Product;
import com.example.app.domain.entity.ProductStatus;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

/**
 * Repository for Product entity.
 *
 * REQ-001: Product Management
 */
@Repository
public interface ProductRepository extends
        JpaRepository<Product, UUID>,
        JpaSpecificationExecutor<Product>,
        ProductRepositoryCustom {

    // ========== Derived Query Methods ==========

    Optional<Product> findBySkuIgnoreCase(String sku);

    boolean existsBySkuIgnoreCase(String sku);

    List<Product> findByStatus(ProductStatus status);

    List<Product> findByCategoryId(UUID categoryId);

    Page<Product> findByCategoryIdAndStatus(
        UUID categoryId,
        ProductStatus status,
        Pageable pageable
    );

    List<Product> findByNameContainingIgnoreCase(String name);

    List<Product> findByPriceBetween(BigDecimal minPrice, BigDecimal maxPrice);

    List<Product> findByStockLessThan(Integer threshold);

    long countByStatus(ProductStatus status);

    long countByCategoryId(UUID categoryId);

    // ========== JPQL Queries ==========

    @Query("""
        SELECT p FROM Product p
        WHERE p.status = :status
        AND p.stock > 0
        ORDER BY p.createdAt DESC
        """)
    List<Product> findAvailableProducts(@Param("status") ProductStatus status);

    @Query("""
        SELECT p FROM Product p
        LEFT JOIN FETCH p.category
        LEFT JOIN FETCH p.brand
        WHERE p.id = :id
        """)
    Optional<Product> findByIdWithRelations(@Param("id") UUID id);

    @Query("""
        SELECT p FROM Product p
        LEFT JOIN FETCH p.images
        WHERE p.id = :id
        """)
    Optional<Product> findByIdWithImages(@Param("id") UUID id);

    @Query("""
        SELECT DISTINCT p FROM Product p
        JOIN p.tags t
        WHERE t.name IN :tagNames
        """)
    List<Product> findByTagNames(@Param("tagNames") List<String> tagNames);

    // ========== Search Query ==========

    @Query("""
        SELECT p FROM Product p
        WHERE (:name IS NULL OR LOWER(p.name) LIKE LOWER(CONCAT('%', :name, '%')))
        AND (:category IS NULL OR p.category.name = :category)
        AND (:minPrice IS NULL OR p.price >= :minPrice)
        AND (:maxPrice IS NULL OR p.price <= :maxPrice)
        AND p.status = 'ACTIVE'
        """)
    Page<Product> search(
        @Param("name") String name,
        @Param("category") String category,
        @Param("minPrice") BigDecimal minPrice,
        @Param("maxPrice") BigDecimal maxPrice,
        Pageable pageable
    );

    // ========== Native Queries ==========

    @Query(value = """
        SELECT * FROM products p
        WHERE p.deleted = false
        AND p.status = 'ACTIVE'
        AND to_tsvector('english', p.name || ' ' || COALESCE(p.description, ''))
            @@ plainto_tsquery('english', :query)
        ORDER BY ts_rank(
            to_tsvector('english', p.name || ' ' || COALESCE(p.description, '')),
            plainto_tsquery('english', :query)
        ) DESC
        """, nativeQuery = true)
    Page<Product> fullTextSearch(@Param("query") String query, Pageable pageable);

    // ========== Modifying Queries ==========

    @Modifying
    @Query("UPDATE Product p SET p.status = :status WHERE p.id = :id")
    int updateStatus(@Param("id") UUID id, @Param("status") ProductStatus status);

    @Modifying
    @Query("UPDATE Product p SET p.stock = p.stock - :quantity WHERE p.id = :id AND p.stock >= :quantity")
    int decreaseStock(@Param("id") UUID id, @Param("quantity") int quantity);

    @Modifying
    @Query("UPDATE Product p SET p.stock = p.stock + :quantity WHERE p.id = :id")
    int increaseStock(@Param("id") UUID id, @Param("quantity") int quantity);

    @Modifying
    @Query("UPDATE Product p SET p.deleted = true, p.deletedAt = :now WHERE p.id IN :ids")
    int softDeleteByIds(@Param("ids") List<UUID> ids, @Param("now") Instant now);

    // ========== Aggregation Queries ==========

    @Query("SELECT AVG(p.price) FROM Product p WHERE p.category.id = :categoryId")
    BigDecimal findAveragePriceByCategory(@Param("categoryId") UUID categoryId);

    @Query("""
        SELECT p.category.name, COUNT(p), AVG(p.price)
        FROM Product p
        GROUP BY p.category.name
        """)
    List<Object[]> getStatsByCategory();
}
```

### Projections

```java
package com.example.app.repository.projection;

import java.math.BigDecimal;
import java.util.UUID;

/**
 * Projection for product summary view.
 */
public interface ProductSummary {
    UUID getId();
    String getName();
    String getSku();
    BigDecimal getPrice();
    Integer getStock();
    String getCategoryName();
}

/**
 * Projection for product with category.
 */
public interface ProductWithCategory {
    UUID getId();
    String getName();
    BigDecimal getPrice();
    CategoryInfo getCategory();

    interface CategoryInfo {
        UUID getId();
        String getName();
    }
}

/**
 * DTO Projection using constructor expression.
 */
public record ProductDTO(
    UUID id,
    String name,
    BigDecimal price,
    String categoryName
) {}
```

### Repository with Projections

```java
// In ProductRepository

@Query("SELECT p FROM Product p WHERE p.status = :status")
List<ProductSummary> findSummariesByStatus(@Param("status") ProductStatus status);

<T> List<T> findByStatus(ProductStatus status, Class<T> type);

@Query("""
    SELECT new com.example.app.repository.projection.ProductDTO(
        p.id, p.name, p.price, p.category.name
    )
    FROM Product p
    WHERE p.status = 'ACTIVE'
    """)
List<ProductDTO> findActiveProductDTOs();
```

### JPA Specifications

```java
package com.example.app.repository.specification;

import com.example.app.domain.entity.Product;
import com.example.app.domain.entity.ProductStatus;
import jakarta.persistence.criteria.JoinType;
import org.springframework.data.jpa.domain.Specification;

import java.math.BigDecimal;
import java.util.UUID;

/**
 * JPA Specifications for Product queries.
 */
public final class ProductSpecifications {

    private ProductSpecifications() {}

    public static Specification<Product> hasName(String name) {
        return (root, query, cb) -> {
            if (name == null || name.isBlank()) {
                return cb.conjunction();
            }
            return cb.like(
                cb.lower(root.get("name")),
                "%" + name.toLowerCase() + "%"
            );
        };
    }

    public static Specification<Product> hasCategory(UUID categoryId) {
        return (root, query, cb) -> {
            if (categoryId == null) {
                return cb.conjunction();
            }
            return cb.equal(root.get("category").get("id"), categoryId);
        };
    }

    public static Specification<Product> hasCategoryName(String categoryName) {
        return (root, query, cb) -> {
            if (categoryName == null || categoryName.isBlank()) {
                return cb.conjunction();
            }
            root.fetch("category", JoinType.LEFT);
            return cb.equal(root.get("category").get("name"), categoryName);
        };
    }

    public static Specification<Product> hasStatus(ProductStatus status) {
        return (root, query, cb) -> {
            if (status == null) {
                return cb.conjunction();
            }
            return cb.equal(root.get("status"), status);
        };
    }

    public static Specification<Product> hasPriceBetween(
            BigDecimal minPrice, BigDecimal maxPrice) {
        return (root, query, cb) -> {
            if (minPrice == null && maxPrice == null) {
                return cb.conjunction();
            }
            if (minPrice != null && maxPrice != null) {
                return cb.between(root.get("price"), minPrice, maxPrice);
            }
            if (minPrice != null) {
                return cb.greaterThanOrEqualTo(root.get("price"), minPrice);
            }
            return cb.lessThanOrEqualTo(root.get("price"), maxPrice);
        };
    }

    public static Specification<Product> hasStockGreaterThan(Integer minStock) {
        return (root, query, cb) -> {
            if (minStock == null) {
                return cb.conjunction();
            }
            return cb.greaterThan(root.get("stock"), minStock);
        };
    }

    public static Specification<Product> isAvailable() {
        return (root, query, cb) -> cb.and(
            cb.equal(root.get("status"), ProductStatus.ACTIVE),
            cb.greaterThan(root.get("stock"), 0),
            cb.isFalse(root.get("deleted"))
        );
    }

    public static Specification<Product> isNotDeleted() {
        return (root, query, cb) -> cb.isFalse(root.get("deleted"));
    }
}
```

### Custom Repository Fragment

```java
package com.example.app.repository;

import com.example.app.domain.entity.Product;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;

import java.math.BigDecimal;

/**
 * Custom repository interface for complex queries.
 */
public interface ProductRepositoryCustom {

    Page<Product> search(
        String name,
        String category,
        Double minPrice,
        Double maxPrice,
        Pageable pageable
    );

    void updatePricesByCategory(UUID categoryId, BigDecimal percentage);
}

/**
 * Custom repository implementation.
 */
package com.example.app.repository.impl;

import com.example.app.domain.entity.Product;
import com.example.app.repository.ProductRepositoryCustom;
import jakarta.persistence.EntityManager;
import jakarta.persistence.PersistenceContext;
import jakarta.persistence.TypedQuery;
import jakarta.persistence.criteria.*;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.Pageable;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

public class ProductRepositoryCustomImpl implements ProductRepositoryCustom {

    @PersistenceContext
    private EntityManager entityManager;

    @Override
    public Page<Product> search(
            String name,
            String category,
            Double minPrice,
            Double maxPrice,
            Pageable pageable) {

        CriteriaBuilder cb = entityManager.getCriteriaBuilder();
        CriteriaQuery<Product> query = cb.createQuery(Product.class);
        Root<Product> root = query.from(Product.class);

        List<Predicate> predicates = new ArrayList<>();
        predicates.add(cb.isFalse(root.get("deleted")));

        if (name != null && !name.isBlank()) {
            predicates.add(cb.like(
                cb.lower(root.get("name")),
                "%" + name.toLowerCase() + "%"
            ));
        }

        if (category != null && !category.isBlank()) {
            root.fetch("category", JoinType.LEFT);
            predicates.add(cb.equal(root.get("category").get("name"), category));
        }

        if (minPrice != null) {
            predicates.add(cb.greaterThanOrEqualTo(
                root.get("price"), BigDecimal.valueOf(minPrice)));
        }

        if (maxPrice != null) {
            predicates.add(cb.lessThanOrEqualTo(
                root.get("price"), BigDecimal.valueOf(maxPrice)));
        }

        query.where(predicates.toArray(new Predicate[0]));

        // Apply sorting
        if (pageable.getSort().isSorted()) {
            List<Order> orders = new ArrayList<>();
            pageable.getSort().forEach(order -> {
                if (order.isAscending()) {
                    orders.add(cb.asc(root.get(order.getProperty())));
                } else {
                    orders.add(cb.desc(root.get(order.getProperty())));
                }
            });
            query.orderBy(orders);
        }

        TypedQuery<Product> typedQuery = entityManager.createQuery(query);
        typedQuery.setFirstResult((int) pageable.getOffset());
        typedQuery.setMaxResults(pageable.getPageSize());

        List<Product> results = typedQuery.getResultList();

        // Count query
        CriteriaQuery<Long> countQuery = cb.createQuery(Long.class);
        Root<Product> countRoot = countQuery.from(Product.class);
        countQuery.select(cb.count(countRoot));
        countQuery.where(predicates.toArray(new Predicate[0]));
        Long total = entityManager.createQuery(countQuery).getSingleResult();

        return new PageImpl<>(results, pageable, total);
    }

    @Override
    public void updatePricesByCategory(UUID categoryId, BigDecimal percentage) {
        entityManager.createQuery("""
            UPDATE Product p
            SET p.price = p.price * (1 + :percentage / 100)
            WHERE p.category.id = :categoryId
            """)
            .setParameter("categoryId", categoryId)
            .setParameter("percentage", percentage)
            .executeUpdate();
    }
}
```

## Generation Rules

1. **Query Methods**
   - Use derived queries for simple cases
   - Use @Query for complex queries
   - Prefer JPQL over native queries
   - Use named parameters with @Param

2. **Specifications**
   - Use for dynamic queries
   - Implement as static factory methods
   - Handle null parameters gracefully
   - Combine with and()/or()

3. **Projections**
   - Use interface projections for read-only views
   - Use DTO projections for specific fields
   - Avoid fetching unnecessary data

4. **Pagination**
   - Return Page for paginated results
   - Include count queries
   - Support sorting

5. **Modifying Queries**
   - Always use @Modifying
   - Clear persistence context when needed
   - Return affected row count

## Best Practices

- Extend JpaRepository and JpaSpecificationExecutor
- Use Optional for single results
- Implement custom repository for complex queries
- Use fetch joins to avoid N+1 problems
- Document query methods
- Test repository methods
- Use projections for read-only queries
