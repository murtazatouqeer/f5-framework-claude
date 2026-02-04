# Service Class Template

Spring Boot service layer template with business logic, validation, and transaction management.

## Template

```java
package {{package}}.service;

import {{package}}.domain.entity.{{Entity}};
import {{package}}.exception.BusinessException;
import {{package}}.exception.ResourceNotFoundException;
import {{package}}.mapper.{{Entity}}Mapper;
import {{package}}.repository.{{Entity}}Repository;
import {{package}}.web.dto.{{Entity}}Request;
import {{package}}.web.dto.{{Entity}}Response;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class {{Entity}}Service {

    private final {{Entity}}Repository {{entity}}Repository;
    private final {{Entity}}Mapper {{entity}}Mapper;

    /**
     * Find all {{entities}} with optional search and pagination.
     */
    public Page<{{Entity}}Response> findAll(String search, Pageable pageable) {
        log.debug("Finding all {{entities}} with search: {}", search);

        Page<{{Entity}}> page;
        if (search != null && !search.isBlank()) {
            page = {{entity}}Repository.findByNameContainingIgnoreCase(search, pageable);
        } else {
            page = {{entity}}Repository.findAll(pageable);
        }

        return page.map({{entity}}Mapper::toResponse);
    }

    /**
     * Find {{entity}} by ID.
     */
    @Cacheable(value = "{{entities}}", key = "#id")
    public {{Entity}}Response findById(UUID id) {
        log.debug("Finding {{entity}} by id: {}", id);

        return {{entity}}Repository.findById(id)
            .map({{entity}}Mapper::toResponse)
            .orElseThrow(() -> new ResourceNotFoundException("{{Entity}}", id));
    }

    /**
     * Create new {{entity}}.
     */
    @Transactional
    public {{Entity}}Response create({{Entity}}Request request) {
        log.info("Creating {{entity}}: {}", request);

        validateCreate(request);

        {{Entity}} {{entity}} = {{entity}}Mapper.toEntity(request);
        {{Entity}} saved = {{entity}}Repository.save({{entity}});

        log.info("Created {{entity}} with id: {}", saved.getId());
        return {{entity}}Mapper.toResponse(saved);
    }

    /**
     * Update existing {{entity}}.
     */
    @Transactional
    @CacheEvict(value = "{{entities}}", key = "#id")
    public {{Entity}}Response update(UUID id, {{Entity}}Request request) {
        log.info("Updating {{entity}} {}: {}", id, request);

        {{Entity}} {{entity}} = {{entity}}Repository.findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("{{Entity}}", id));

        validateUpdate({{entity}}, request);

        {{entity}}Mapper.updateEntity({{entity}}, request);
        {{Entity}} updated = {{entity}}Repository.save({{entity}});

        log.info("Updated {{entity}}: {}", id);
        return {{entity}}Mapper.toResponse(updated);
    }

    /**
     * Partially update {{entity}}.
     */
    @Transactional
    @CacheEvict(value = "{{entities}}", key = "#id")
    public {{Entity}}Response partialUpdate(UUID id, {{Entity}}PatchRequest request) {
        log.info("Partial update {{entity}} {}: {}", id, request);

        {{Entity}} {{entity}} = {{entity}}Repository.findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("{{Entity}}", id));

        {{entity}}Mapper.patchEntity({{entity}}, request);
        {{Entity}} updated = {{entity}}Repository.save({{entity}});

        return {{entity}}Mapper.toResponse(updated);
    }

    /**
     * Delete {{entity}} by ID.
     */
    @Transactional
    @CacheEvict(value = "{{entities}}", key = "#id")
    public void delete(UUID id) {
        log.info("Deleting {{entity}}: {}", id);

        if (!{{entity}}Repository.existsById(id)) {
            throw new ResourceNotFoundException("{{Entity}}", id);
        }

        {{entity}}Repository.deleteById(id);
        log.info("Deleted {{entity}}: {}", id);
    }

    // ==================== Validation Methods ====================

    private void validateCreate({{Entity}}Request request) {
        // Add business validation rules
        // Example: Check for duplicates
        // if ({{entity}}Repository.existsByName(request.name())) {
        //     throw new BusinessException("DUPLICATE_NAME", "{{Entity}} with this name already exists");
        // }
    }

    private void validateUpdate({{Entity}} existing, {{Entity}}Request request) {
        // Add update-specific validation
        // Example: Check if can be modified
        // if (existing.getStatus() == {{Entity}}Status.LOCKED) {
        //     throw new BusinessException("LOCKED", "Cannot modify locked {{entity}}");
        // }
    }
}
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{package}}` | Base package name | `com.example.app` |
| `{{Entity}}` | Entity name (PascalCase) | `Product` |
| `{{entity}}` | Entity name (camelCase) | `product` |
| `{{entities}}` | Entity name plural (lowercase) | `products` |

## Customization Options

### With Events

```java
@Service
@RequiredArgsConstructor
public class {{Entity}}Service {

    private final {{Entity}}Repository {{entity}}Repository;
    private final ApplicationEventPublisher eventPublisher;

    @Transactional
    public {{Entity}}Response create({{Entity}}Request request) {
        {{Entity}} {{entity}} = {{entity}}Mapper.toEntity(request);
        {{Entity}} saved = {{entity}}Repository.save({{entity}});

        eventPublisher.publishEvent(new {{Entity}}CreatedEvent(saved));

        return {{entity}}Mapper.toResponse(saved);
    }

    @Transactional
    public void delete(UUID id) {
        {{Entity}} {{entity}} = {{entity}}Repository.findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("{{Entity}}", id));

        {{entity}}Repository.delete({{entity}});

        eventPublisher.publishEvent(new {{Entity}}DeletedEvent(id));
    }
}
```

### With Specification Queries

```java
public Page<{{Entity}}Response> findAll({{Entity}}Filter filter, Pageable pageable) {
    Specification<{{Entity}}> spec = {{Entity}}Specification.builder()
        .search(filter.getSearch())
        .status(filter.getStatus())
        .categoryId(filter.getCategoryId())
        .priceRange(filter.getMinPrice(), filter.getMaxPrice())
        .build();

    return {{entity}}Repository.findAll(spec, pageable)
        .map({{entity}}Mapper::toResponse);
}
```

### With Bulk Operations

```java
@Transactional
public List<{{Entity}}Response> createBulk(List<{{Entity}}Request> requests) {
    List<{{Entity}}> entities = requests.stream()
        .map({{entity}}Mapper::toEntity)
        .toList();

    List<{{Entity}}> saved = {{entity}}Repository.saveAll(entities);
    return saved.stream()
        .map({{entity}}Mapper::toResponse)
        .toList();
}

@Transactional
@CacheEvict(value = "{{entities}}", allEntries = true)
public void deleteBulk(List<UUID> ids) {
    {{entity}}Repository.deleteAllById(ids);
}
```

### With Soft Delete

```java
@Transactional
@CacheEvict(value = "{{entities}}", key = "#id")
public void delete(UUID id) {
    {{Entity}} {{entity}} = {{entity}}Repository.findById(id)
        .orElseThrow(() -> new ResourceNotFoundException("{{Entity}}", id));

    {{entity}}.setDeleted(true);
    {{entity}}.setDeletedAt(Instant.now());
    {{entity}}Repository.save({{entity}});
}

public Page<{{Entity}}Response> findAll(String search, Pageable pageable) {
    return {{entity}}Repository.findByDeletedFalse(pageable)
        .map({{entity}}Mapper::toResponse);
}
```

### With Async Operations

```java
@Async
public CompletableFuture<{{Entity}}Response> processAsync(UUID id) {
    {{Entity}} {{entity}} = {{entity}}Repository.findById(id)
        .orElseThrow(() -> new ResourceNotFoundException("{{Entity}}", id));

    // Long-running operation
    {{entity}}.setProcessed(true);
    {{Entity}} saved = {{entity}}Repository.save({{entity}});

    return CompletableFuture.completedFuture({{entity}}Mapper.toResponse(saved));
}
```

### With External Service Integration

```java
@Service
@RequiredArgsConstructor
public class {{Entity}}Service {

    private final {{Entity}}Repository {{entity}}Repository;
    private final ExternalApiClient externalApiClient;
    private final CacheManager cacheManager;

    @Transactional
    public {{Entity}}Response createWithEnrichment({{Entity}}Request request) {
        {{Entity}} {{entity}} = {{entity}}Mapper.toEntity(request);

        // Enrich with external data
        ExternalData enrichment = externalApiClient.fetchData(request.getExternalId());
        {{entity}}.setEnrichedField(enrichment.getValue());

        {{Entity}} saved = {{entity}}Repository.save({{entity}});
        return {{entity}}Mapper.toResponse(saved);
    }
}
```
