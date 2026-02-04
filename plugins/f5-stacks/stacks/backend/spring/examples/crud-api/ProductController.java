package com.example.app.web.controller;

import com.example.app.domain.entity.ProductStatus;
import com.example.app.service.ProductService;
import com.example.app.web.dto.*;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.data.web.PageableDefault;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/products")
@RequiredArgsConstructor
@Tag(name = "Products", description = "Product management APIs")
@SecurityRequirement(name = "bearerAuth")
public class ProductController {

    private final ProductService productService;

    @GetMapping
    @Operation(summary = "List products", description = "Returns paginated list of products with optional filtering")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "Successfully retrieved products"),
        @ApiResponse(responseCode = "401", description = "Unauthorized")
    })
    public ResponseEntity<Page<ProductResponse>> list(
            @Parameter(description = "Search text")
            @RequestParam(required = false) String search,

            @Parameter(description = "Category ID")
            @RequestParam(required = false) UUID categoryId,

            @Parameter(description = "Status filter")
            @RequestParam(required = false) ProductStatusDto status,

            @Parameter(description = "Minimum price")
            @RequestParam(required = false) BigDecimal minPrice,

            @Parameter(description = "Maximum price")
            @RequestParam(required = false) BigDecimal maxPrice,

            @Parameter(description = "Featured only")
            @RequestParam(required = false) Boolean featured,

            @PageableDefault(size = 20, sort = "createdAt", direction = Sort.Direction.DESC)
            Pageable pageable) {

        ProductFilter filter = new ProductFilter(
            search, categoryId, status, minPrice, maxPrice, null, null, null
        );

        return ResponseEntity.ok(productService.findAll(filter, pageable));
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get product", description = "Returns a single product by ID")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "Successfully retrieved product"),
        @ApiResponse(responseCode = "404", description = "Product not found",
            content = @Content(schema = @Schema(implementation = ErrorResponse.class)))
    })
    public ResponseEntity<ProductResponse> getById(
            @Parameter(description = "Product ID", required = true)
            @PathVariable UUID id) {
        return ResponseEntity.ok(productService.findById(id));
    }

    @GetMapping("/sku/{sku}")
    @Operation(summary = "Get product by SKU", description = "Returns a single product by SKU")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "Successfully retrieved product"),
        @ApiResponse(responseCode = "404", description = "Product not found")
    })
    public ResponseEntity<ProductResponse> getBySku(
            @Parameter(description = "Product SKU", required = true)
            @PathVariable String sku) {
        return ResponseEntity.ok(productService.findBySku(sku));
    }

    @GetMapping("/featured")
    @Operation(summary = "Get featured products", description = "Returns list of featured products")
    public ResponseEntity<List<ProductResponse>> getFeatured() {
        return ResponseEntity.ok(productService.getFeaturedProducts());
    }

    @PostMapping
    @Operation(summary = "Create product", description = "Creates a new product")
    @ApiResponses({
        @ApiResponse(responseCode = "201", description = "Product created successfully"),
        @ApiResponse(responseCode = "400", description = "Invalid input"),
        @ApiResponse(responseCode = "409", description = "Product already exists")
    })
    @PreAuthorize("hasAnyRole('ADMIN', 'MANAGER')")
    public ResponseEntity<ProductResponse> create(
            @Parameter(description = "Product data", required = true)
            @Valid @RequestBody ProductRequest request) {
        ProductResponse created = productService.create(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(created);
    }

    @PutMapping("/{id}")
    @Operation(summary = "Update product", description = "Updates an existing product")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "Product updated successfully"),
        @ApiResponse(responseCode = "400", description = "Invalid input"),
        @ApiResponse(responseCode = "404", description = "Product not found")
    })
    @PreAuthorize("hasAnyRole('ADMIN', 'MANAGER')")
    public ResponseEntity<ProductResponse> update(
            @PathVariable UUID id,
            @Valid @RequestBody ProductRequest request) {
        return ResponseEntity.ok(productService.update(id, request));
    }

    @PatchMapping("/{id}")
    @Operation(summary = "Partial update", description = "Partially updates an existing product")
    @PreAuthorize("hasAnyRole('ADMIN', 'MANAGER')")
    public ResponseEntity<ProductResponse> partialUpdate(
            @PathVariable UUID id,
            @RequestBody ProductPatchRequest request) {
        return ResponseEntity.ok(productService.partialUpdate(id, request));
    }

    @PatchMapping("/{id}/status")
    @Operation(summary = "Update status", description = "Updates product status")
    @PreAuthorize("hasAnyRole('ADMIN', 'MANAGER')")
    public ResponseEntity<ProductResponse> updateStatus(
            @PathVariable UUID id,
            @RequestParam ProductStatus status) {
        return ResponseEntity.ok(productService.updateStatus(id, status));
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "Delete product", description = "Soft deletes a product")
    @ApiResponses({
        @ApiResponse(responseCode = "204", description = "Product deleted successfully"),
        @ApiResponse(responseCode = "404", description = "Product not found")
    })
    @PreAuthorize("hasRole('ADMIN')")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void delete(@PathVariable UUID id) {
        productService.delete(id);
    }
}
