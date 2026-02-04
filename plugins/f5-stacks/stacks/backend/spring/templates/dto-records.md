# DTO Records Template

Java record-based DTOs for Spring Boot with validation, documentation, and mapping support.

## Request DTO Template

```java
package {{package}}.web.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.List;
import java.util.UUID;

@Schema(description = "{{Entity}} creation/update request")
public record {{Entity}}Request(

    @Schema(description = "Name of the {{entity}}", example = "Sample Name")
    @NotBlank(message = "Name is required")
    @Size(min = 2, max = 100, message = "Name must be between 2 and 100 characters")
    String name,

    @Schema(description = "Description of the {{entity}}", example = "Sample description")
    @Size(max = 2000, message = "Description must not exceed 2000 characters")
    String description,

    @Schema(description = "Category ID", example = "123e4567-e89b-12d3-a456-426614174000")
    UUID categoryId,

    @Schema(description = "Price", example = "99.99")
    @NotNull(message = "Price is required")
    @DecimalMin(value = "0.00", message = "Price must be non-negative")
    @Digits(integer = 10, fraction = 2, message = "Price format invalid")
    BigDecimal price,

    @Schema(description = "Status")
    {{Entity}}StatusDto status,

    @Schema(description = "Tags")
    List<@NotBlank String> tags,

    @Schema(description = "Items")
    @Valid
    List<{{Entity}}ItemRequest> items

) {
    // Compact constructor for validation/normalization
    public {{Entity}}Request {
        name = name != null ? name.trim() : null;
        description = description != null ? description.trim() : null;
        tags = tags != null ? List.copyOf(tags) : List.of();
        items = items != null ? List.copyOf(items) : List.of();
    }
}
```

## Response DTO Template

```java
package {{package}}.web.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import io.swagger.v3.oas.annotations.media.Schema;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.List;
import java.util.UUID;

@Schema(description = "{{Entity}} response")
@JsonInclude(JsonInclude.Include.NON_NULL)
public record {{Entity}}Response(

    @Schema(description = "Unique identifier")
    UUID id,

    @Schema(description = "Name")
    String name,

    @Schema(description = "Description")
    String description,

    @Schema(description = "Category")
    CategorySummary category,

    @Schema(description = "Price")
    BigDecimal price,

    @Schema(description = "Status")
    {{Entity}}StatusDto status,

    @Schema(description = "Tags")
    List<String> tags,

    @Schema(description = "Items")
    List<{{Entity}}ItemResponse> items,

    @Schema(description = "Creation timestamp")
    Instant createdAt,

    @Schema(description = "Last update timestamp")
    Instant updatedAt,

    @Schema(description = "Created by user")
    String createdBy

) {
    // Nested record for related entity summary
    public record CategorySummary(
        UUID id,
        String name
    ) {}
}
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{package}}` | Base package name | `com.example.app` |
| `{{Entity}}` | Entity name (PascalCase) | `Product` |
| `{{entity}}` | Entity name (camelCase) | `product` |

## Customization Options

### Patch Request (Partial Update)

```java
@Schema(description = "{{Entity}} partial update request")
public record {{Entity}}PatchRequest(

    @Schema(description = "Name of the {{entity}}")
    @Size(min = 2, max = 100, message = "Name must be between 2 and 100 characters")
    Optional<String> name,

    @Schema(description = "Description")
    @Size(max = 2000, message = "Description must not exceed 2000 characters")
    Optional<String> description,

    @Schema(description = "Status")
    Optional<{{Entity}}StatusDto> status,

    @Schema(description = "Price")
    @DecimalMin(value = "0.00", message = "Price must be non-negative")
    Optional<BigDecimal> price

) {
    public {{Entity}}PatchRequest {
        name = name != null ? name.map(String::trim) : Optional.empty();
        description = description != null ? description.map(String::trim) : Optional.empty();
    }
}
```

### Filter/Search Request

```java
@Schema(description = "{{Entity}} search filters")
public record {{Entity}}Filter(

    @Schema(description = "Search text")
    @Size(max = 100)
    String search,

    @Schema(description = "Category ID filter")
    UUID categoryId,

    @Schema(description = "Status filter")
    {{Entity}}StatusDto status,

    @Schema(description = "Minimum price")
    @DecimalMin("0.00")
    BigDecimal minPrice,

    @Schema(description = "Maximum price")
    @DecimalMin("0.00")
    BigDecimal maxPrice,

    @Schema(description = "Created after")
    Instant createdAfter,

    @Schema(description = "Created before")
    Instant createdBefore,

    @Schema(description = "Tags to filter by")
    List<String> tags

) {
    public {{Entity}}Filter {
        search = search != null ? search.trim() : null;
        tags = tags != null ? List.copyOf(tags) : List.of();
    }

    public boolean hasSearch() {
        return search != null && !search.isBlank();
    }

    public boolean hasPriceRange() {
        return minPrice != null || maxPrice != null;
    }

    public boolean hasDateRange() {
        return createdAfter != null || createdBefore != null;
    }
}
```

### Bulk Operations Request

```java
@Schema(description = "Bulk {{entity}} creation request")
public record {{Entity}}BulkRequest(

    @Schema(description = "Items to create")
    @NotNull
    @Size(min = 1, max = 100, message = "Must have between 1 and 100 items")
    @Valid
    List<{{Entity}}Request> items

) {
    public {{Entity}}BulkRequest {
        items = items != null ? List.copyOf(items) : List.of();
    }
}

@Schema(description = "Bulk {{entity}} operation response")
public record {{Entity}}BulkResponse(

    @Schema(description = "Successfully processed items")
    List<{{Entity}}Response> successful,

    @Schema(description = "Failed items with errors")
    List<FailedItem> failed,

    @Schema(description = "Total processed")
    int totalProcessed,

    @Schema(description = "Success count")
    int successCount,

    @Schema(description = "Failure count")
    int failureCount

) {
    public record FailedItem(
        int index,
        {{Entity}}Request request,
        String errorMessage
    ) {}

    public static {{Entity}}BulkResponse of(
            List<{{Entity}}Response> successful,
            List<FailedItem> failed) {
        return new {{Entity}}BulkResponse(
            successful,
            failed,
            successful.size() + failed.size(),
            successful.size(),
            failed.size()
        );
    }
}
```

### Status DTO Enum

```java
package {{package}}.web.dto;

import com.fasterxml.jackson.annotation.JsonValue;
import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "{{Entity}} status", enumAsRef = true)
public enum {{Entity}}StatusDto {

    @Schema(description = "Draft state")
    DRAFT("draft"),

    @Schema(description = "Active state")
    ACTIVE("active"),

    @Schema(description = "Inactive state")
    INACTIVE("inactive"),

    @Schema(description = "Archived state")
    ARCHIVED("archived");

    private final String value;

    {{Entity}}StatusDto(String value) {
        this.value = value;
    }

    @JsonValue
    public String getValue() {
        return value;
    }

    public static {{Entity}}StatusDto fromValue(String value) {
        for ({{Entity}}StatusDto status : values()) {
            if (status.value.equalsIgnoreCase(value)) {
                return status;
            }
        }
        throw new IllegalArgumentException("Unknown status: " + value);
    }
}
```

### Paginated Response Wrapper

```java
@Schema(description = "Paginated response")
public record PageResponse<T>(

    @Schema(description = "Content items")
    List<T> content,

    @Schema(description = "Page metadata")
    PageMetadata page

) {
    public record PageMetadata(
        @Schema(description = "Current page number (0-based)")
        int number,

        @Schema(description = "Page size")
        int size,

        @Schema(description = "Total elements")
        long totalElements,

        @Schema(description = "Total pages")
        int totalPages,

        @Schema(description = "Is first page")
        boolean first,

        @Schema(description = "Is last page")
        boolean last
    ) {}

    public static <T> PageResponse<T> from(Page<T> page) {
        return new PageResponse<>(
            page.getContent(),
            new PageMetadata(
                page.getNumber(),
                page.getSize(),
                page.getTotalElements(),
                page.getTotalPages(),
                page.isFirst(),
                page.isLast()
            )
        );
    }
}
```

### Nested Item DTOs

```java
@Schema(description = "{{Entity}} item request")
public record {{Entity}}ItemRequest(

    @Schema(description = "Product ID")
    @NotNull
    UUID productId,

    @Schema(description = "Quantity")
    @NotNull
    @Min(1)
    @Max(10000)
    Integer quantity,

    @Schema(description = "Unit price override")
    @DecimalMin("0.00")
    BigDecimal unitPrice,

    @Schema(description = "Notes")
    @Size(max = 500)
    String notes

) {}

@Schema(description = "{{Entity}} item response")
public record {{Entity}}ItemResponse(

    UUID id,
    UUID productId,
    String productName,
    Integer quantity,
    BigDecimal unitPrice,
    BigDecimal totalPrice,
    String notes

) {}
```

### Summary/List DTO

```java
@Schema(description = "{{Entity}} list item (summary)")
public record {{Entity}}ListItem(

    @Schema(description = "ID")
    UUID id,

    @Schema(description = "Name")
    String name,

    @Schema(description = "Status")
    {{Entity}}StatusDto status,

    @Schema(description = "Category name")
    String categoryName,

    @Schema(description = "Item count")
    int itemCount,

    @Schema(description = "Total value")
    BigDecimal totalValue,

    @Schema(description = "Created at")
    Instant createdAt

) {}
```

### Validation Groups

```java
// Validation groups interface
public interface ValidationGroups {
    interface Create {}
    interface Update {}
    interface Patch {}
}

// Request with group-specific validation
@Schema(description = "{{Entity}} request with validation groups")
public record {{Entity}}GroupedRequest(

    @Schema(description = "ID (required for update)")
    @NotNull(groups = ValidationGroups.Update.class)
    @Null(groups = ValidationGroups.Create.class)
    UUID id,

    @Schema(description = "Name")
    @NotBlank(groups = {ValidationGroups.Create.class, ValidationGroups.Update.class})
    String name,

    @Schema(description = "Status")
    @NotNull(groups = ValidationGroups.Create.class)
    {{Entity}}StatusDto status

) {}

// Controller usage
@PostMapping
public ResponseEntity<{{Entity}}Response> create(
        @Validated(ValidationGroups.Create.class) @RequestBody {{Entity}}GroupedRequest request) {
    // ...
}

@PutMapping("/{id}")
public ResponseEntity<{{Entity}}Response> update(
        @PathVariable UUID id,
        @Validated(ValidationGroups.Update.class) @RequestBody {{Entity}}GroupedRequest request) {
    // ...
}
```

### Builder Pattern for Complex DTOs

```java
// Using Lombok with records (requires additional setup)
// Alternative: static factory methods
public record {{Entity}}Response(
    UUID id,
    String name,
    String description,
    {{Entity}}StatusDto status,
    Instant createdAt
) {
    public static Builder builder() {
        return new Builder();
    }

    public static class Builder {
        private UUID id;
        private String name;
        private String description;
        private {{Entity}}StatusDto status;
        private Instant createdAt;

        public Builder id(UUID id) {
            this.id = id;
            return this;
        }

        public Builder name(String name) {
            this.name = name;
            return this;
        }

        public Builder description(String description) {
            this.description = description;
            return this;
        }

        public Builder status({{Entity}}StatusDto status) {
            this.status = status;
            return this;
        }

        public Builder createdAt(Instant createdAt) {
            this.createdAt = createdAt;
            return this;
        }

        public {{Entity}}Response build() {
            return new {{Entity}}Response(id, name, description, status, createdAt);
        }
    }
}
```

### API Error Response

```java
@Schema(description = "API error response")
public record ErrorResponse(

    @Schema(description = "Error type URI")
    String type,

    @Schema(description = "Error title")
    String title,

    @Schema(description = "HTTP status code")
    int status,

    @Schema(description = "Error detail message")
    String detail,

    @Schema(description = "Request instance")
    String instance,

    @Schema(description = "Timestamp")
    Instant timestamp,

    @Schema(description = "Trace ID for debugging")
    String traceId,

    @Schema(description = "Field validation errors")
    List<FieldError> errors

) {
    public record FieldError(
        String field,
        String message,
        Object rejectedValue
    ) {}

    public static ErrorResponse of(String title, int status, String detail, String instance) {
        return new ErrorResponse(
            "about:blank",
            title,
            status,
            detail,
            instance,
            Instant.now(),
            MDC.get("traceId"),
            List.of()
        );
    }
}
```
