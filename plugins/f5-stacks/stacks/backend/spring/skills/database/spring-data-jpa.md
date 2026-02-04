# Spring Data JPA Patterns

Spring Data JPA repository patterns, query methods, and best practices.

## Repository Basics

### Base Repository

```java
package com.example.app.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.data.repository.NoRepositoryBean;

import java.util.UUID;

@NoRepositoryBean
public interface BaseRepository<T> extends
        JpaRepository<T, UUID>,
        JpaSpecificationExecutor<T> {
}
```

### Entity Repository

```java
@Repository
public interface ProductRepository extends BaseRepository<Product> {

    // Derived query methods
    List<Product> findByStatus(ProductStatus status);

    Optional<Product> findBySkuIgnoreCase(String sku);

    boolean existsBySkuIgnoreCase(String sku);

    List<Product> findByNameContainingIgnoreCase(String name);

    List<Product> findByCategoryId(UUID categoryId);

    Page<Product> findByCategoryIdAndStatus(
        UUID categoryId,
        ProductStatus status,
        Pageable pageable
    );

    long countByStatus(ProductStatus status);

    List<Product> findByPriceBetween(BigDecimal min, BigDecimal max);

    List<Product> findByStockLessThanOrderByStockAsc(int threshold);

    List<Product> findFirst10ByStatusOrderByCreatedAtDesc(ProductStatus status);

    @Modifying
    @Query("DELETE FROM Product p WHERE p.status = :status")
    int deleteByStatus(@Param("status") ProductStatus status);
}
```

## Query Methods

### Derived Query Keywords

```java
// Equality
List<Product> findByName(String name);
List<Product> findByNameIs(String name);
List<Product> findByNameEquals(String name);

// Comparison
List<Product> findByPriceGreaterThan(BigDecimal price);
List<Product> findByPriceLessThanEqual(BigDecimal price);
List<Product> findByPriceBetween(BigDecimal min, BigDecimal max);

// String matching
List<Product> findByNameLike(String pattern);              // Requires %
List<Product> findByNameContaining(String name);           // Auto %name%
List<Product> findByNameStartingWith(String prefix);       // Auto prefix%
List<Product> findByNameEndingWith(String suffix);         // Auto %suffix
List<Product> findByNameIgnoreCase(String name);

// Boolean
List<Product> findByActiveTrue();
List<Product> findByDeletedFalse();

// Null checks
List<Product> findByDescriptionIsNull();
List<Product> findByDescriptionIsNotNull();

// Collection
List<Product> findByStatusIn(List<ProductStatus> statuses);
List<Product> findByStatusNotIn(List<ProductStatus> statuses);

// Date
List<Product> findByCreatedAtAfter(Instant date);
List<Product> findByCreatedAtBefore(Instant date);

// Ordering
List<Product> findByStatusOrderByNameAsc(ProductStatus status);
List<Product> findByStatusOrderByPriceDescNameAsc(ProductStatus status);

// Limiting
Product findFirstByStatusOrderByCreatedAtDesc(ProductStatus status);
List<Product> findTop10ByStatusOrderByCreatedAtDesc(ProductStatus status);

// Distinct
List<Product> findDistinctByCategory(Category category);

// Nested properties
List<Product> findByCategoryName(String categoryName);
List<Product> findByCategoryIdAndBrandId(UUID categoryId, UUID brandId);
```

### JPQL Queries

```java
@Query("SELECT p FROM Product p WHERE p.status = :status AND p.stock > 0")
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
    WHERE (:name IS NULL OR LOWER(p.name) LIKE LOWER(CONCAT('%', :name, '%')))
    AND (:categoryId IS NULL OR p.category.id = :categoryId)
    AND (:minPrice IS NULL OR p.price >= :minPrice)
    AND (:maxPrice IS NULL OR p.price <= :maxPrice)
    AND p.deleted = false
    """)
Page<Product> search(
    @Param("name") String name,
    @Param("categoryId") UUID categoryId,
    @Param("minPrice") BigDecimal minPrice,
    @Param("maxPrice") BigDecimal maxPrice,
    Pageable pageable
);

@Query("SELECT AVG(p.price) FROM Product p WHERE p.category.id = :categoryId")
BigDecimal findAveragePriceByCategory(@Param("categoryId") UUID categoryId);

@Query("""
    SELECT p.category.name, COUNT(p), AVG(p.price)
    FROM Product p
    WHERE p.deleted = false
    GROUP BY p.category.name
    ORDER BY COUNT(p) DESC
    """)
List<Object[]> getStatsByCategory();
```

### Native Queries

```java
@Query(
    value = """
        SELECT * FROM products p
        WHERE p.deleted = false
        AND to_tsvector('english', p.name || ' ' || COALESCE(p.description, ''))
            @@ plainto_tsquery('english', :query)
        ORDER BY ts_rank(
            to_tsvector('english', p.name || ' ' || COALESCE(p.description, '')),
            plainto_tsquery('english', :query)
        ) DESC
        """,
    nativeQuery = true
)
Page<Product> fullTextSearch(@Param("query") String query, Pageable pageable);

@Query(
    value = "SELECT * FROM products WHERE status = :status LIMIT :limit",
    nativeQuery = true
)
List<Product> findByStatusWithLimit(
    @Param("status") String status,
    @Param("limit") int limit
);
```

### Modifying Queries

```java
@Modifying
@Query("UPDATE Product p SET p.status = :status WHERE p.id = :id")
int updateStatus(@Param("id") UUID id, @Param("status") ProductStatus status);

@Modifying
@Query("UPDATE Product p SET p.stock = p.stock - :quantity WHERE p.id = :id AND p.stock >= :quantity")
int decreaseStock(@Param("id") UUID id, @Param("quantity") int quantity);

@Modifying
@Query("UPDATE Product p SET p.deleted = true, p.deletedAt = :now WHERE p.id IN :ids")
int softDeleteByIds(@Param("ids") List<UUID> ids, @Param("now") Instant now);

@Modifying(clearAutomatically = true)  // Clear persistence context after
@Query("UPDATE Product p SET p.price = p.price * (1 + :percentage / 100) WHERE p.category.id = :categoryId")
int increasePricesByCategory(@Param("categoryId") UUID categoryId, @Param("percentage") BigDecimal percentage);
```

## Projections

### Interface Projection

```java
public interface ProductSummary {
    UUID getId();
    String getName();
    String getSku();
    BigDecimal getPrice();

    @Value("#{target.category.name}")
    String getCategoryName();
}

// Repository method
List<ProductSummary> findByStatus(ProductStatus status);
```

### Class Projection (DTO)

```java
public record ProductDTO(
    UUID id,
    String name,
    BigDecimal price,
    String categoryName
) {}

@Query("""
    SELECT new com.example.app.dto.ProductDTO(
        p.id, p.name, p.price, p.category.name
    )
    FROM Product p
    WHERE p.status = 'ACTIVE'
    """)
List<ProductDTO> findActiveProductDTOs();
```

### Dynamic Projections

```java
<T> List<T> findByStatus(ProductStatus status, Class<T> type);

// Usage
List<ProductSummary> summaries = repository.findByStatus(ACTIVE, ProductSummary.class);
List<ProductDTO> dtos = repository.findByStatus(ACTIVE, ProductDTO.class);
List<Product> entities = repository.findByStatus(ACTIVE, Product.class);
```

## Specifications (Dynamic Queries)

```java
public class ProductSpecifications {

    public static Specification<Product> hasName(String name) {
        return (root, query, cb) -> {
            if (name == null || name.isBlank()) {
                return cb.conjunction();
            }
            return cb.like(cb.lower(root.get("name")), "%" + name.toLowerCase() + "%");
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

    public static Specification<Product> hasPriceBetween(BigDecimal min, BigDecimal max) {
        return (root, query, cb) -> {
            List<Predicate> predicates = new ArrayList<>();
            if (min != null) {
                predicates.add(cb.greaterThanOrEqualTo(root.get("price"), min));
            }
            if (max != null) {
                predicates.add(cb.lessThanOrEqualTo(root.get("price"), max));
            }
            return cb.and(predicates.toArray(new Predicate[0]));
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

    public static Specification<Product> isNotDeleted() {
        return (root, query, cb) -> cb.isFalse(root.get("deleted"));
    }
}

// Service usage
public Page<Product> search(ProductSearchCriteria criteria, Pageable pageable) {
    Specification<Product> spec = Specification
        .where(ProductSpecifications.hasName(criteria.getName()))
        .and(ProductSpecifications.hasCategory(criteria.getCategoryId()))
        .and(ProductSpecifications.hasPriceBetween(criteria.getMinPrice(), criteria.getMaxPrice()))
        .and(ProductSpecifications.hasStatus(criteria.getStatus()))
        .and(ProductSpecifications.isNotDeleted());

    return productRepository.findAll(spec, pageable);
}
```

## Pagination and Sorting

```java
// Controller
@GetMapping
public Page<ProductResponse> list(
        @RequestParam(defaultValue = "0") int page,
        @RequestParam(defaultValue = "20") int size,
        @RequestParam(defaultValue = "createdAt,desc") String[] sort) {

    Pageable pageable = PageRequest.of(page, size, parseSort(sort));
    return productService.findAll(pageable);
}

private Sort parseSort(String[] sort) {
    List<Sort.Order> orders = new ArrayList<>();
    for (String s : sort) {
        String[] parts = s.split(",");
        String property = parts[0];
        Sort.Direction direction = parts.length > 1 && parts[1].equalsIgnoreCase("desc")
            ? Sort.Direction.DESC
            : Sort.Direction.ASC;
        orders.add(new Sort.Order(direction, property));
    }
    return Sort.by(orders);
}

// Using @PageableDefault
@GetMapping
public Page<ProductResponse> list(
        @PageableDefault(size = 20, sort = "createdAt", direction = Sort.Direction.DESC)
        Pageable pageable) {
    return productService.findAll(pageable);
}
```

## Custom Repository Implementation

```java
public interface ProductRepositoryCustom {
    Page<Product> searchWithFilters(ProductSearchCriteria criteria, Pageable pageable);
    void updatePricesByCategory(UUID categoryId, BigDecimal percentage);
}

public class ProductRepositoryImpl implements ProductRepositoryCustom {

    @PersistenceContext
    private EntityManager em;

    @Override
    public Page<Product> searchWithFilters(ProductSearchCriteria criteria, Pageable pageable) {
        CriteriaBuilder cb = em.getCriteriaBuilder();
        CriteriaQuery<Product> query = cb.createQuery(Product.class);
        Root<Product> root = query.from(Product.class);

        List<Predicate> predicates = buildPredicates(criteria, cb, root);
        query.where(predicates.toArray(new Predicate[0]));

        // Sorting
        if (pageable.getSort().isSorted()) {
            List<Order> orders = pageable.getSort().stream()
                .map(order -> order.isAscending()
                    ? cb.asc(root.get(order.getProperty()))
                    : cb.desc(root.get(order.getProperty())))
                .collect(Collectors.toList());
            query.orderBy(orders);
        }

        TypedQuery<Product> typedQuery = em.createQuery(query);
        typedQuery.setFirstResult((int) pageable.getOffset());
        typedQuery.setMaxResults(pageable.getPageSize());

        List<Product> results = typedQuery.getResultList();
        long total = getTotalCount(criteria);

        return new PageImpl<>(results, pageable, total);
    }

    private List<Predicate> buildPredicates(
            ProductSearchCriteria criteria,
            CriteriaBuilder cb,
            Root<Product> root) {
        List<Predicate> predicates = new ArrayList<>();
        predicates.add(cb.isFalse(root.get("deleted")));

        if (criteria.getName() != null) {
            predicates.add(cb.like(
                cb.lower(root.get("name")),
                "%" + criteria.getName().toLowerCase() + "%"
            ));
        }
        // Add more predicates...

        return predicates;
    }
}

// Main repository extends custom
public interface ProductRepository extends
        BaseRepository<Product>,
        ProductRepositoryCustom {
    // Derived methods...
}
```

## Best Practices

1. **Use Projections** for read-only queries
2. **Use Specifications** for dynamic queries
3. **Use @EntityGraph** to avoid N+1
4. **Prefer JPQL** over native queries
5. **Use @Modifying** for update/delete
6. **Implement custom repository** for complex queries
7. **Use Page/Slice** for large datasets
8. **Index frequently queried columns**
