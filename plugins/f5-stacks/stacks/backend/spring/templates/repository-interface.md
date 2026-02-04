# Repository Interface Template

Spring Data JPA repository template with custom queries, specifications, and projections.

## Template

```java
package {{package}}.repository;

import {{package}}.domain.entity.{{Entity}};
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface {{Entity}}Repository extends
        JpaRepository<{{Entity}}, UUID>,
        JpaSpecificationExecutor<{{Entity}}> {

    // ==================== Query Methods ====================

    Optional<{{Entity}}> findByName(String name);

    List<{{Entity}}> findByStatus({{Entity}}Status status);

    Page<{{Entity}}> findByNameContainingIgnoreCase(String name, Pageable pageable);

    boolean existsByName(String name);

    long countByStatus({{Entity}}Status status);

    // ==================== JPQL Queries ====================

    @Query("SELECT e FROM {{Entity}} e WHERE e.status = :status AND e.deleted = false")
    List<{{Entity}}> findActiveByStatus(@Param("status") {{Entity}}Status status);

    @Query("SELECT e FROM {{Entity}} e WHERE e.category.id = :categoryId")
    Page<{{Entity}}> findByCategoryId(@Param("categoryId") UUID categoryId, Pageable pageable);

    @Query("""
        SELECT e FROM {{Entity}} e
        WHERE e.createdAt BETWEEN :startDate AND :endDate
        ORDER BY e.createdAt DESC
        """)
    List<{{Entity}}> findByDateRange(
        @Param("startDate") Instant startDate,
        @Param("endDate") Instant endDate
    );

    // ==================== Native Queries ====================

    @Query(value = """
        SELECT * FROM {{table_name}}
        WHERE deleted = false
        AND status = :status
        ORDER BY created_at DESC
        LIMIT :limit
        """, nativeQuery = true)
    List<{{Entity}}> findTopByStatus(
        @Param("status") String status,
        @Param("limit") int limit
    );

    // ==================== Modifying Queries ====================

    @Modifying
    @Query("UPDATE {{Entity}} e SET e.status = :status WHERE e.id = :id")
    int updateStatus(@Param("id") UUID id, @Param("status") {{Entity}}Status status);

    @Modifying
    @Query("UPDATE {{Entity}} e SET e.deleted = true, e.deletedAt = :deletedAt WHERE e.id IN :ids")
    int softDeleteByIds(@Param("ids") List<UUID> ids, @Param("deletedAt") Instant deletedAt);

    @Modifying
    @Query("DELETE FROM {{Entity}} e WHERE e.deleted = true AND e.deletedAt < :cutoffDate")
    int purgeDeletedBefore(@Param("cutoffDate") Instant cutoffDate);
}
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{package}}` | Base package name | `com.example.app` |
| `{{Entity}}` | Entity name (PascalCase) | `Product` |
| `{{entity}}` | Entity name (camelCase) | `product` |
| `{{table_name}}` | Database table name | `products` |

## Customization Options

### With Projections

```java
public interface {{Entity}}Repository extends JpaRepository<{{Entity}}, UUID> {

    // Interface-based projection
    List<{{Entity}}Summary> findByStatus({{Entity}}Status status);

    // Class-based projection
    @Query("SELECT new {{package}}.dto.{{Entity}}Summary(e.id, e.name, e.status) FROM {{Entity}} e")
    List<{{Entity}}Summary> findAllSummaries();

    // Dynamic projection
    <T> List<T> findByStatus({{Entity}}Status status, Class<T> type);
}

// Projection interface
public interface {{Entity}}Summary {
    UUID getId();
    String getName();
    {{Entity}}Status getStatus();

    // Nested projection
    CategorySummary getCategory();

    interface CategorySummary {
        UUID getId();
        String getName();
    }
}

// DTO projection
public record {{Entity}}SummaryDto(UUID id, String name, {{Entity}}Status status) {}
```

### With Entity Graph

```java
public interface {{Entity}}Repository extends JpaRepository<{{Entity}}, UUID> {

    @EntityGraph(attributePaths = {"category", "items"})
    Optional<{{Entity}}> findWithDetailsById(UUID id);

    @EntityGraph(attributePaths = {"category"})
    Page<{{Entity}}> findAllWithCategory(Pageable pageable);

    @EntityGraph(value = "{{Entity}}.fullDetails", type = EntityGraph.EntityGraphType.LOAD)
    List<{{Entity}}> findByStatus({{Entity}}Status status);
}

// Entity with named graph
@Entity
@NamedEntityGraph(
    name = "{{Entity}}.fullDetails",
    attributeNodes = {
        @NamedAttributeNode("category"),
        @NamedAttributeNode(value = "items", subgraph = "items-subgraph")
    },
    subgraphs = {
        @NamedSubgraph(
            name = "items-subgraph",
            attributeNodes = @NamedAttributeNode("product")
        )
    }
)
public class {{Entity}} {
    // ...
}
```

### With Query Hints

```java
public interface {{Entity}}Repository extends JpaRepository<{{Entity}}, UUID> {

    @QueryHints({
        @QueryHint(name = "org.hibernate.readOnly", value = "true"),
        @QueryHint(name = "org.hibernate.fetchSize", value = "50"),
        @QueryHint(name = "org.hibernate.cacheable", value = "true"),
        @QueryHint(name = "jakarta.persistence.cache.retrieveMode", value = "USE"),
        @QueryHint(name = "jakarta.persistence.cache.storeMode", value = "USE")
    })
    @Query("SELECT e FROM {{Entity}} e WHERE e.status = :status")
    List<{{Entity}}> findByStatusWithHints(@Param("status") {{Entity}}Status status);

    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @Query("SELECT e FROM {{Entity}} e WHERE e.id = :id")
    Optional<{{Entity}}> findByIdForUpdate(@Param("id") UUID id);

    @Lock(LockModeType.OPTIMISTIC_FORCE_INCREMENT)
    Optional<{{Entity}}> findWithLockById(UUID id);
}
```

### With Streaming

```java
public interface {{Entity}}Repository extends JpaRepository<{{Entity}}, UUID> {

    @Query("SELECT e FROM {{Entity}} e WHERE e.status = :status")
    Stream<{{Entity}}> streamByStatus(@Param("status") {{Entity}}Status status);

    @Query("SELECT e FROM {{Entity}} e")
    @QueryHints(@QueryHint(name = HINT_FETCH_SIZE, value = "100"))
    Stream<{{Entity}}> streamAll();
}

// Usage in service
@Transactional(readOnly = true)
public void processAll{{Entity}}s() {
    try (Stream<{{Entity}}> stream = {{entity}}Repository.streamAll()) {
        stream.forEach(this::process);
    }
}
```

### With Stored Procedures

```java
public interface {{Entity}}Repository extends JpaRepository<{{Entity}}, UUID> {

    @Procedure(name = "{{Entity}}.calculateStats")
    Map<String, Object> calculateStats(@Param("category_id") UUID categoryId);

    @Procedure(procedureName = "sp_archive_{{entities}}")
    int archiveOldRecords(@Param("cutoff_date") Instant cutoffDate);
}

// Entity with named stored procedure
@Entity
@NamedStoredProcedureQuery(
    name = "{{Entity}}.calculateStats",
    procedureName = "sp_calculate_{{entity}}_stats",
    parameters = {
        @StoredProcedureParameter(mode = ParameterMode.IN, name = "category_id", type = UUID.class),
        @StoredProcedureParameter(mode = ParameterMode.OUT, name = "total_count", type = Long.class),
        @StoredProcedureParameter(mode = ParameterMode.OUT, name = "total_value", type = BigDecimal.class)
    }
)
public class {{Entity}} {
    // ...
}
```

### With Auditing Queries

```java
public interface {{Entity}}Repository extends JpaRepository<{{Entity}}, UUID> {

    List<{{Entity}}> findByCreatedBy(String username);

    List<{{Entity}}> findByUpdatedAtAfter(Instant timestamp);

    @Query("""
        SELECT e FROM {{Entity}} e
        WHERE e.createdAt >= :since
        AND e.createdBy = :user
        ORDER BY e.createdAt DESC
        """)
    List<{{Entity}}> findRecentByUser(
        @Param("user") String user,
        @Param("since") Instant since
    );
}
```

### With Soft Delete Support

```java
public interface {{Entity}}Repository extends JpaRepository<{{Entity}}, UUID> {

    // Automatically filtered by @SQLRestriction on entity
    List<{{Entity}}> findAll();

    // Include soft deleted
    @Query("SELECT e FROM {{Entity}} e WHERE e.id = :id")
    @Modifying
    Optional<{{Entity}}> findByIdIncludingDeleted(@Param("id") UUID id);

    // Only deleted
    @Query("SELECT e FROM {{Entity}} e WHERE e.deleted = true")
    List<{{Entity}}> findAllDeleted();

    // Restore soft deleted
    @Modifying
    @Query("UPDATE {{Entity}} e SET e.deleted = false, e.deletedAt = null WHERE e.id = :id")
    int restore(@Param("id") UUID id);
}
```

### Custom Repository Implementation

```java
// Custom repository interface
public interface {{Entity}}RepositoryCustom {
    List<{{Entity}}> findByComplexCriteria({{Entity}}SearchCriteria criteria);
    void batchUpdate(List<{{Entity}}> entities);
}

// Custom implementation
@RequiredArgsConstructor
public class {{Entity}}RepositoryImpl implements {{Entity}}RepositoryCustom {

    private final EntityManager entityManager;

    @Override
    public List<{{Entity}}> findByComplexCriteria({{Entity}}SearchCriteria criteria) {
        CriteriaBuilder cb = entityManager.getCriteriaBuilder();
        CriteriaQuery<{{Entity}}> query = cb.createQuery({{Entity}}.class);
        Root<{{Entity}}> root = query.from({{Entity}}.class);

        List<Predicate> predicates = new ArrayList<>();

        if (criteria.getName() != null) {
            predicates.add(cb.like(
                cb.lower(root.get("name")),
                "%" + criteria.getName().toLowerCase() + "%"
            ));
        }

        if (criteria.getStatus() != null) {
            predicates.add(cb.equal(root.get("status"), criteria.getStatus()));
        }

        query.where(predicates.toArray(new Predicate[0]));
        query.orderBy(cb.desc(root.get("createdAt")));

        return entityManager.createQuery(query).getResultList();
    }

    @Override
    public void batchUpdate(List<{{Entity}}> entities) {
        int batchSize = 50;
        for (int i = 0; i < entities.size(); i++) {
            entityManager.merge(entities.get(i));
            if (i > 0 && i % batchSize == 0) {
                entityManager.flush();
                entityManager.clear();
            }
        }
    }
}

// Main repository extends custom
public interface {{Entity}}Repository extends
        JpaRepository<{{Entity}}, UUID>,
        {{Entity}}RepositoryCustom {
    // ...
}
```

### With QueryDSL

```java
public interface {{Entity}}Repository extends
        JpaRepository<{{Entity}}, UUID>,
        QuerydslPredicateExecutor<{{Entity}}>,
        QuerydslBinderCustomizer<Q{{Entity}}> {

    @Override
    default void customize(QuerydslBindings bindings, Q{{Entity}} root) {
        bindings.bind(root.name).first((path, value) ->
            path.containsIgnoreCase(value));
        bindings.bind(root.createdAt).all((path, values) -> {
            List<? extends Instant> dates = new ArrayList<>(values);
            if (dates.size() == 2) {
                return Optional.of(path.between(dates.get(0), dates.get(1)));
            }
            return Optional.of(path.goe(dates.get(0)));
        });
    }
}

// Usage
Q{{Entity}} q{{entity}} = Q{{Entity}}.{{entity}};
BooleanBuilder builder = new BooleanBuilder();
builder.and(q{{entity}}.status.eq({{Entity}}Status.ACTIVE));
builder.and(q{{entity}}.name.containsIgnoreCase("search"));

Page<{{Entity}}> results = {{entity}}Repository.findAll(builder, pageable);
```
