package com.example.app.web.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.*;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

// ==================== Request DTOs ====================

@Schema(description = "Product creation/update request")
public record ProductRequest(

    @Schema(description = "Product name", example = "Laptop Pro 15")
    @NotBlank(message = "Name is required")
    @Size(min = 2, max = 100, message = "Name must be between 2 and 100 characters")
    String name,

    @Schema(description = "Product description")
    @Size(max = 2000, message = "Description must not exceed 2000 characters")
    String description,

    @Schema(description = "Stock Keeping Unit", example = "LAP-PRO-15")
    @Size(max = 50)
    @Pattern(regexp = "^[A-Z0-9-]+$", message = "SKU must contain only uppercase letters, numbers, and hyphens")
    String sku,

    @Schema(description = "Product price", example = "1299.99")
    @NotNull(message = "Price is required")
    @DecimalMin(value = "0.00", message = "Price must be non-negative")
    @Digits(integer = 15, fraction = 4, message = "Price format invalid")
    BigDecimal price,

    @Schema(description = "Category ID")
    UUID categoryId,

    @Schema(description = "Product status")
    ProductStatusDto status,

    @Schema(description = "Product tags")
    List<@NotBlank String> tags,

    @Schema(description = "Initial stock quantity")
    @Min(value = 0, message = "Stock quantity cannot be negative")
    Integer stockQuantity,

    @Schema(description = "Is featured product")
    Boolean featured

) {
    public ProductRequest {
        name = name != null ? name.trim() : null;
        description = description != null ? description.trim() : null;
        sku = sku != null ? sku.trim().toUpperCase() : null;
        tags = tags != null ? List.copyOf(tags) : List.of();
        stockQuantity = stockQuantity != null ? stockQuantity : 0;
        featured = featured != null ? featured : false;
    }
}

@Schema(description = "Product partial update request")
public record ProductPatchRequest(

    @Size(min = 2, max = 100)
    Optional<String> name,

    @Size(max = 2000)
    Optional<String> description,

    @DecimalMin("0.00")
    Optional<BigDecimal> price,

    Optional<ProductStatusDto> status,

    Optional<List<String>> tags,

    @Min(0)
    Optional<Integer> stockQuantity,

    Optional<Boolean> featured

) {}

@Schema(description = "Product filter parameters")
public record ProductFilter(

    @Size(max = 100)
    String search,

    UUID categoryId,

    ProductStatusDto status,

    @DecimalMin("0.00")
    BigDecimal minPrice,

    @DecimalMin("0.00")
    BigDecimal maxPrice,

    Instant createdAfter,

    Instant createdBefore,

    List<String> tags

) {
    public ProductFilter {
        search = search != null ? search.trim() : null;
        tags = tags != null ? List.copyOf(tags) : List.of();
    }

    public boolean hasSearch() {
        return search != null && !search.isBlank();
    }

    public boolean hasPriceRange() {
        return minPrice != null || maxPrice != null;
    }
}

// ==================== Response DTOs ====================

@Schema(description = "Product response")
@JsonInclude(JsonInclude.Include.NON_NULL)
public record ProductResponse(

    @Schema(description = "Product ID")
    UUID id,

    @Schema(description = "Product name")
    String name,

    @Schema(description = "Product description")
    String description,

    @Schema(description = "Stock Keeping Unit")
    String sku,

    @Schema(description = "Product price")
    BigDecimal price,

    @Schema(description = "Product status")
    ProductStatusDto status,

    @Schema(description = "Category")
    CategorySummary category,

    @Schema(description = "Product tags")
    List<String> tags,

    @Schema(description = "Stock quantity")
    Integer stockQuantity,

    @Schema(description = "Is available for purchase")
    boolean available,

    @Schema(description = "Is featured")
    boolean featured,

    @Schema(description = "Created timestamp")
    Instant createdAt,

    @Schema(description = "Updated timestamp")
    Instant updatedAt,

    @Schema(description = "Created by")
    String createdBy

) {
    public record CategorySummary(UUID id, String name) {}
}

@Schema(description = "Product list item (summary)")
public record ProductListItem(

    UUID id,
    String name,
    String sku,
    BigDecimal price,
    ProductStatusDto status,
    String categoryName,
    Integer stockQuantity,
    boolean available,
    Instant createdAt

) {}

// ==================== Status Enum ====================

@Schema(description = "Product status", enumAsRef = true)
public enum ProductStatusDto {

    @Schema(description = "Draft - not yet published")
    DRAFT,

    @Schema(description = "Active - available for sale")
    ACTIVE,

    @Schema(description = "Inactive - temporarily unavailable")
    INACTIVE,

    @Schema(description = "Archived - permanently removed from sale")
    ARCHIVED
}
