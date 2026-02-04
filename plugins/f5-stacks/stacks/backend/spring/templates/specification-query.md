# Specification Query Template

Spring Data JPA Specification template for dynamic queries with type-safe criteria building.

## Template

```java
package {{package}}.repository.specification;

import {{package}}.domain.entity.{{Entity}};
import {{package}}.domain.entity.{{Entity}}Status;
import {{package}}.web.dto.{{Entity}}Filter;
import jakarta.persistence.criteria.*;
import org.springframework.data.jpa.domain.Specification;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

public class {{Entity}}Specification {

    private {{Entity}}Specification() {
        // Utility class
    }

    // ==================== Builder Pattern ====================

    public static Builder builder() {
        return new Builder();
    }

    public static class Builder {
        private String search;
        private UUID categoryId;
        private {{Entity}}Status status;
        private BigDecimal minPrice;
        private BigDecimal maxPrice;
        private Instant createdAfter;
        private Instant createdBefore;
        private List<String> tags;
        private Boolean includeDeleted = false;

        public Builder search(String search) {
            this.search = search;
            return this;
        }

        public Builder categoryId(UUID categoryId) {
            this.categoryId = categoryId;
            return this;
        }

        public Builder status({{Entity}}Status status) {
            this.status = status;
            return this;
        }

        public Builder priceRange(BigDecimal min, BigDecimal max) {
            this.minPrice = min;
            this.maxPrice = max;
            return this;
        }

        public Builder createdBetween(Instant after, Instant before) {
            this.createdAfter = after;
            this.createdBefore = before;
            return this;
        }

        public Builder tags(List<String> tags) {
            this.tags = tags;
            return this;
        }

        public Builder includeDeleted(boolean include) {
            this.includeDeleted = include;
            return this;
        }

        public Specification<{{Entity}}> build() {
            return (root, query, cb) -> {
                List<Predicate> predicates = new ArrayList<>();

                // Search across multiple fields
                if (search != null && !search.isBlank()) {
                    String pattern = "%" + search.toLowerCase() + "%";
                    predicates.add(cb.or(
                        cb.like(cb.lower(root.get("name")), pattern),
                        cb.like(cb.lower(root.get("description")), pattern)
                    ));
                }

                // Category filter
                if (categoryId != null) {
                    predicates.add(cb.equal(root.get("category").get("id"), categoryId));
                }

                // Status filter
                if (status != null) {
                    predicates.add(cb.equal(root.get("status"), status));
                }

                // Price range
                if (minPrice != null) {
                    predicates.add(cb.greaterThanOrEqualTo(root.get("price"), minPrice));
                }
                if (maxPrice != null) {
                    predicates.add(cb.lessThanOrEqualTo(root.get("price"), maxPrice));
                }

                // Date range
                if (createdAfter != null) {
                    predicates.add(cb.greaterThanOrEqualTo(root.get("createdAt"), createdAfter));
                }
                if (createdBefore != null) {
                    predicates.add(cb.lessThanOrEqualTo(root.get("createdAt"), createdBefore));
                }

                // Soft delete filter (if not using @SQLRestriction)
                if (!includeDeleted) {
                    predicates.add(cb.isFalse(root.get("deleted")));
                }

                return cb.and(predicates.toArray(new Predicate[0]));
            };
        }
    }

    // ==================== Static Specification Methods ====================

    public static Specification<{{Entity}}> hasName(String name) {
        return (root, query, cb) ->
            name == null ? null : cb.equal(root.get("name"), name);
    }

    public static Specification<{{Entity}}> nameContains(String search) {
        return (root, query, cb) -> {
            if (search == null || search.isBlank()) return null;
            return cb.like(cb.lower(root.get("name")), "%" + search.toLowerCase() + "%");
        };
    }

    public static Specification<{{Entity}}> hasStatus({{Entity}}Status status) {
        return (root, query, cb) ->
            status == null ? null : cb.equal(root.get("status"), status);
    }

    public static Specification<{{Entity}}> hasCategoryId(UUID categoryId) {
        return (root, query, cb) ->
            categoryId == null ? null : cb.equal(root.get("category").get("id"), categoryId);
    }

    public static Specification<{{Entity}}> priceGreaterThan(BigDecimal price) {
        return (root, query, cb) ->
            price == null ? null : cb.greaterThan(root.get("price"), price);
    }

    public static Specification<{{Entity}}> priceLessThan(BigDecimal price) {
        return (root, query, cb) ->
            price == null ? null : cb.lessThan(root.get("price"), price);
    }

    public static Specification<{{Entity}}> priceBetween(BigDecimal min, BigDecimal max) {
        return (root, query, cb) -> {
            if (min == null && max == null) return null;
            if (min == null) return cb.lessThanOrEqualTo(root.get("price"), max);
            if (max == null) return cb.greaterThanOrEqualTo(root.get("price"), min);
            return cb.between(root.get("price"), min, max);
        };
    }

    public static Specification<{{Entity}}> createdAfter(Instant date) {
        return (root, query, cb) ->
            date == null ? null : cb.greaterThanOrEqualTo(root.get("createdAt"), date);
    }

    public static Specification<{{Entity}}> createdBefore(Instant date) {
        return (root, query, cb) ->
            date == null ? null : cb.lessThanOrEqualTo(root.get("createdAt"), date);
    }

    public static Specification<{{Entity}}> isNotDeleted() {
        return (root, query, cb) -> cb.isFalse(root.get("deleted"));
    }

    public static Specification<{{Entity}}> createdBy(String username) {
        return (root, query, cb) ->
            username == null ? null : cb.equal(root.get("createdBy"), username);
    }

    // ==================== From Filter DTO ====================

    public static Specification<{{Entity}}> fromFilter({{Entity}}Filter filter) {
        if (filter == null) {
            return Specification.where(isNotDeleted());
        }

        return Specification
            .where(nameContains(filter.search()))
            .and(hasCategoryId(filter.categoryId()))
            .and(hasStatus(filter.status() != null ?
                {{Entity}}Status.valueOf(filter.status().name()) : null))
            .and(priceBetween(filter.minPrice(), filter.maxPrice()))
            .and(createdAfter(filter.createdAfter()))
            .and(createdBefore(filter.createdBefore()))
            .and(isNotDeleted());
    }
}
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{package}}` | Base package name | `com.example.app` |
| `{{Entity}}` | Entity name (PascalCase) | `Product` |
| `{{entity}}` | Entity name (camelCase) | `product` |

## Usage Examples

### Basic Usage

```java
// Using builder
Specification<{{Entity}}> spec = {{Entity}}Specification.builder()
    .search("laptop")
    .status({{Entity}}Status.ACTIVE)
    .priceRange(BigDecimal.valueOf(100), BigDecimal.valueOf(1000))
    .build();

Page<{{Entity}}> results = {{entity}}Repository.findAll(spec, pageable);

// Using static methods with composition
Specification<{{Entity}}> spec = Specification
    .where({{Entity}}Specification.nameContains("laptop"))
    .and({{Entity}}Specification.hasStatus({{Entity}}Status.ACTIVE))
    .and({{Entity}}Specification.priceBetween(BigDecimal.valueOf(100), BigDecimal.valueOf(1000)));

// Using filter DTO
Page<{{Entity}}> results = {{entity}}Repository.findAll(
    {{Entity}}Specification.fromFilter(filter),
    pageable
);
```

## Customization Options

### With Join Fetch

```java
public static Specification<{{Entity}}> withCategory() {
    return (root, query, cb) -> {
        // Avoid duplicate fetching for count queries
        if (query.getResultType() != Long.class && query.getResultType() != long.class) {
            root.fetch("category", JoinType.LEFT);
        }
        return null;
    };
}

public static Specification<{{Entity}}> withItems() {
    return (root, query, cb) -> {
        if (query.getResultType() != Long.class && query.getResultType() != long.class) {
            root.fetch("items", JoinType.LEFT);
            query.distinct(true);
        }
        return null;
    };
}

// Usage
Specification<{{Entity}}> spec = Specification
    .where({{Entity}}Specification.withCategory())
    .and({{Entity}}Specification.withItems())
    .and({{Entity}}Specification.hasStatus({{Entity}}Status.ACTIVE));
```

### With Subqueries

```java
public static Specification<{{Entity}}> hasItemsWithProduct(UUID productId) {
    return (root, query, cb) -> {
        if (productId == null) return null;

        Subquery<Long> subquery = query.subquery(Long.class);
        Root<{{Entity}}Item> itemRoot = subquery.from({{Entity}}Item.class);
        subquery.select(cb.literal(1L))
            .where(cb.and(
                cb.equal(itemRoot.get("{{entity}}"), root),
                cb.equal(itemRoot.get("product").get("id"), productId)
            ));

        return cb.exists(subquery);
    };
}

public static Specification<{{Entity}}> hasMinimumItemCount(int minCount) {
    return (root, query, cb) -> {
        Subquery<Long> subquery = query.subquery(Long.class);
        Root<{{Entity}}Item> itemRoot = subquery.from({{Entity}}Item.class);
        subquery.select(cb.count(itemRoot))
            .where(cb.equal(itemRoot.get("{{entity}}"), root));

        return cb.greaterThanOrEqualTo(subquery, (long) minCount);
    };
}

public static Specification<{{Entity}}> totalValueGreaterThan(BigDecimal value) {
    return (root, query, cb) -> {
        if (value == null) return null;

        Subquery<BigDecimal> subquery = query.subquery(BigDecimal.class);
        Root<{{Entity}}Item> itemRoot = subquery.from({{Entity}}Item.class);
        subquery.select(cb.sum(
            cb.prod(itemRoot.get("quantity"), itemRoot.get("unitPrice"))
        ))
        .where(cb.equal(itemRoot.get("{{entity}}"), root));

        return cb.greaterThan(subquery, value);
    };
}
```

### With Collection Filters

```java
public static Specification<{{Entity}}> hasTag(String tag) {
    return (root, query, cb) -> {
        if (tag == null) return null;
        return cb.isMember(tag, root.get("tags"));
    };
}

public static Specification<{{Entity}}> hasAnyTag(List<String> tags) {
    return (root, query, cb) -> {
        if (tags == null || tags.isEmpty()) return null;
        return tags.stream()
            .map(tag -> cb.isMember(tag, root.<List<String>>get("tags")))
            .reduce(cb::or)
            .orElse(null);
    };
}

public static Specification<{{Entity}}> hasAllTags(List<String> tags) {
    return (root, query, cb) -> {
        if (tags == null || tags.isEmpty()) return null;
        return tags.stream()
            .map(tag -> cb.isMember(tag, root.<List<String>>get("tags")))
            .reduce(cb::and)
            .orElse(null);
    };
}
```

### With JSON Column Queries (PostgreSQL)

```java
public static Specification<{{Entity}}> hasMetadataKey(String key) {
    return (root, query, cb) -> {
        if (key == null) return null;
        // PostgreSQL jsonb operator
        return cb.isTrue(
            cb.function("jsonb_exists", Boolean.class, root.get("metadata"), cb.literal(key))
        );
    };
}

public static Specification<{{Entity}}> metadataEquals(String key, String value) {
    return (root, query, cb) -> {
        if (key == null || value == null) return null;
        // PostgreSQL ->> operator
        return cb.equal(
            cb.function("jsonb_extract_path_text", String.class,
                root.get("metadata"), cb.literal(key)),
            value
        );
    };
}
```

### With Full-Text Search (PostgreSQL)

```java
public static Specification<{{Entity}}> fullTextSearch(String searchText) {
    return (root, query, cb) -> {
        if (searchText == null || searchText.isBlank()) return null;

        // PostgreSQL full-text search
        Expression<Boolean> tsQuery = cb.function(
            "to_tsquery",
            Boolean.class,
            cb.literal("english"),
            cb.literal(searchText.replace(" ", " & "))
        );

        Expression<Object> tsVector = cb.function(
            "to_tsvector",
            Object.class,
            cb.literal("english"),
            cb.concat(
                cb.concat(root.get("name"), cb.literal(" ")),
                root.get("description")
            )
        );

        return cb.isTrue(
            cb.function("@@", Boolean.class, tsVector, tsQuery)
        );
    };
}
```

### With Sorting in Specification

```java
public static Specification<{{Entity}}> withSorting(String sortBy, boolean ascending) {
    return (root, query, cb) -> {
        if (sortBy != null && query.getResultType() != Long.class) {
            Path<?> sortPath = root.get(sortBy);
            query.orderBy(ascending ? cb.asc(sortPath) : cb.desc(sortPath));
        }
        return null;
    };
}

public static Specification<{{Entity}}> sortByRelevance(String search) {
    return (root, query, cb) -> {
        if (search == null || query.getResultType() == Long.class) return null;

        // Sort by relevance (exact match first, then contains)
        Expression<Integer> exactMatch = cb.selectCase()
            .when(cb.equal(cb.lower(root.get("name")), search.toLowerCase()), 1)
            .otherwise(0);

        Expression<Integer> startsWithMatch = cb.selectCase()
            .when(cb.like(cb.lower(root.get("name")), search.toLowerCase() + "%"), 2)
            .otherwise(0);

        query.orderBy(
            cb.desc(exactMatch),
            cb.desc(startsWithMatch),
            cb.asc(root.get("name"))
        );

        return null;
    };
}
```

### With Distinct and Grouping

```java
public static Specification<{{Entity}}> distinctByCategory() {
    return (root, query, cb) -> {
        if (query.getResultType() != Long.class) {
            query.distinct(true);
            query.groupBy(root.get("category").get("id"));
        }
        return null;
    };
}
```

### Complex AND/OR Logic

```java
public static Specification<{{Entity}}> complexFilter(
        String search,
        List<{{Entity}}Status> statuses,
        List<UUID> categoryIds,
        boolean matchAny) {

    return (root, query, cb) -> {
        List<Predicate> predicates = new ArrayList<>();

        // Search predicate
        if (search != null && !search.isBlank()) {
            String pattern = "%" + search.toLowerCase() + "%";
            predicates.add(cb.or(
                cb.like(cb.lower(root.get("name")), pattern),
                cb.like(cb.lower(root.get("description")), pattern)
            ));
        }

        // Status predicates
        List<Predicate> statusPredicates = new ArrayList<>();
        if (statuses != null && !statuses.isEmpty()) {
            statusPredicates.add(root.get("status").in(statuses));
        }

        // Category predicates
        List<Predicate> categoryPredicates = new ArrayList<>();
        if (categoryIds != null && !categoryIds.isEmpty()) {
            categoryPredicates.add(root.get("category").get("id").in(categoryIds));
        }

        // Combine status and category with AND or OR
        List<Predicate> filterPredicates = new ArrayList<>();
        filterPredicates.addAll(statusPredicates);
        filterPredicates.addAll(categoryPredicates);

        if (!filterPredicates.isEmpty()) {
            if (matchAny) {
                predicates.add(cb.or(filterPredicates.toArray(new Predicate[0])));
            } else {
                predicates.add(cb.and(filterPredicates.toArray(new Predicate[0])));
            }
        }

        return predicates.isEmpty() ? null : cb.and(predicates.toArray(new Predicate[0]));
    };
}
```

## Service Integration

```java
@Service
@RequiredArgsConstructor
public class {{Entity}}Service {

    private final {{Entity}}Repository {{entity}}Repository;

    public Page<{{Entity}}Response> search({{Entity}}Filter filter, Pageable pageable) {
        Specification<{{Entity}}> spec = {{Entity}}Specification.builder()
            .search(filter.search())
            .categoryId(filter.categoryId())
            .status(filter.status() != null ?
                {{Entity}}Status.valueOf(filter.status().name()) : null)
            .priceRange(filter.minPrice(), filter.maxPrice())
            .createdBetween(filter.createdAfter(), filter.createdBefore())
            .build();

        return {{entity}}Repository.findAll(spec, pageable)
            .map({{entity}}Mapper::toResponse);
    }
}
```
