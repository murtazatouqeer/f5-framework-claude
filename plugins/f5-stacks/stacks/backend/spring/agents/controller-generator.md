# Controller Generator Agent

Spring Boot REST controller generator with CRUD operations, pagination, and OpenAPI documentation.

## Capabilities

- Generate REST controllers with standard CRUD endpoints
- Implement pagination and sorting
- Add filtering and search capabilities
- Generate OpenAPI/Swagger documentation
- Handle request validation
- Implement proper HTTP status codes

## Input Requirements

```yaml
entity_name: "Product"
base_path: "/api/v1/products"
operations:
  - create
  - read
  - update
  - delete
  - list
features:
  - pagination
  - sorting
  - filtering
  - openapi
```

## Generated Code Pattern

### Standard REST Controller

```java
package com.example.app.web.controller;

import com.example.app.domain.entity.Product;
import com.example.app.service.ProductService;
import com.example.app.web.dto.ProductRequest;
import com.example.app.web.dto.ProductResponse;
import com.example.app.web.mapper.ProductMapper;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.web.PageableDefault;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

/**
 * REST controller for Product operations.
 *
 * REQ-001: Product Management API
 */
@RestController
@RequestMapping("/api/v1/products")
@RequiredArgsConstructor
@Tag(name = "Products", description = "Product management endpoints")
public class ProductController {

    private final ProductService productService;
    private final ProductMapper productMapper;

    /**
     * Create a new product.
     *
     * @param request Product creation request
     * @return Created product
     */
    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    @Operation(summary = "Create product", description = "Create a new product")
    @ApiResponses({
        @ApiResponse(responseCode = "201", description = "Product created successfully",
            content = @Content(schema = @Schema(implementation = ProductResponse.class))),
        @ApiResponse(responseCode = "400", description = "Invalid request"),
        @ApiResponse(responseCode = "409", description = "Product already exists")
    })
    public ResponseEntity<ProductResponse> create(
            @Valid @RequestBody ProductRequest request) {
        Product product = productMapper.toEntity(request);
        Product created = productService.create(product);
        return ResponseEntity
            .status(HttpStatus.CREATED)
            .body(productMapper.toResponse(created));
    }

    /**
     * Get product by ID.
     *
     * @param id Product ID
     * @return Product details
     */
    @GetMapping("/{id}")
    @Operation(summary = "Get product", description = "Get product by ID")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "Product found",
            content = @Content(schema = @Schema(implementation = ProductResponse.class))),
        @ApiResponse(responseCode = "404", description = "Product not found")
    })
    public ResponseEntity<ProductResponse> getById(
            @Parameter(description = "Product ID")
            @PathVariable UUID id) {
        return productService.findById(id)
            .map(productMapper::toResponse)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }

    /**
     * List all products with pagination.
     *
     * @param pageable Pagination parameters
     * @return Page of products
     */
    @GetMapping
    @Operation(summary = "List products", description = "Get paginated list of products")
    @ApiResponse(responseCode = "200", description = "Products retrieved successfully")
    public ResponseEntity<Page<ProductResponse>> list(
            @PageableDefault(size = 20, sort = "createdAt") Pageable pageable) {
        Page<Product> products = productService.findAll(pageable);
        Page<ProductResponse> response = products.map(productMapper::toResponse);
        return ResponseEntity.ok(response);
    }

    /**
     * Search products with filters.
     *
     * @param name Name filter (partial match)
     * @param category Category filter
     * @param minPrice Minimum price
     * @param maxPrice Maximum price
     * @param pageable Pagination parameters
     * @return Filtered page of products
     */
    @GetMapping("/search")
    @Operation(summary = "Search products", description = "Search products with filters")
    public ResponseEntity<Page<ProductResponse>> search(
            @RequestParam(required = false) String name,
            @RequestParam(required = false) String category,
            @RequestParam(required = false) Double minPrice,
            @RequestParam(required = false) Double maxPrice,
            @PageableDefault(size = 20) Pageable pageable) {
        Page<Product> products = productService.search(
            name, category, minPrice, maxPrice, pageable);
        return ResponseEntity.ok(products.map(productMapper::toResponse));
    }

    /**
     * Update existing product.
     *
     * @param id Product ID
     * @param request Update request
     * @return Updated product
     */
    @PutMapping("/{id}")
    @Operation(summary = "Update product", description = "Update existing product")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "Product updated successfully"),
        @ApiResponse(responseCode = "404", description = "Product not found"),
        @ApiResponse(responseCode = "400", description = "Invalid request")
    })
    public ResponseEntity<ProductResponse> update(
            @PathVariable UUID id,
            @Valid @RequestBody ProductRequest request) {
        return productService.findById(id)
            .map(existing -> {
                productMapper.updateEntity(request, existing);
                Product updated = productService.update(existing);
                return ResponseEntity.ok(productMapper.toResponse(updated));
            })
            .orElse(ResponseEntity.notFound().build());
    }

    /**
     * Partially update product.
     *
     * @param id Product ID
     * @param request Partial update request
     * @return Updated product
     */
    @PatchMapping("/{id}")
    @Operation(summary = "Patch product", description = "Partially update product")
    public ResponseEntity<ProductResponse> patch(
            @PathVariable UUID id,
            @RequestBody ProductRequest request) {
        return productService.findById(id)
            .map(existing -> {
                productMapper.patchEntity(request, existing);
                Product updated = productService.update(existing);
                return ResponseEntity.ok(productMapper.toResponse(updated));
            })
            .orElse(ResponseEntity.notFound().build());
    }

    /**
     * Delete product.
     *
     * @param id Product ID
     * @return No content
     */
    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    @Operation(summary = "Delete product", description = "Delete product by ID")
    @ApiResponses({
        @ApiResponse(responseCode = "204", description = "Product deleted"),
        @ApiResponse(responseCode = "404", description = "Product not found")
    })
    public ResponseEntity<Void> delete(@PathVariable UUID id) {
        if (!productService.existsById(id)) {
            return ResponseEntity.notFound().build();
        }
        productService.deleteById(id);
        return ResponseEntity.noContent().build();
    }

    /**
     * Check if product exists.
     *
     * @param id Product ID
     * @return Head response
     */
    @RequestMapping(value = "/{id}", method = RequestMethod.HEAD)
    @Operation(summary = "Check product exists", description = "Check if product exists")
    public ResponseEntity<Void> exists(@PathVariable UUID id) {
        return productService.existsById(id)
            ? ResponseEntity.ok().build()
            : ResponseEntity.notFound().build();
    }

    /**
     * Get product count.
     *
     * @return Count response
     */
    @GetMapping("/count")
    @Operation(summary = "Count products", description = "Get total product count")
    public ResponseEntity<Long> count() {
        return ResponseEntity.ok(productService.count());
    }
}
```

### Controller with File Upload

```java
@PostMapping(value = "/{id}/image", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
@Operation(summary = "Upload product image")
public ResponseEntity<ProductResponse> uploadImage(
        @PathVariable UUID id,
        @RequestParam("file") MultipartFile file) {
    Product product = productService.uploadImage(id, file);
    return ResponseEntity.ok(productMapper.toResponse(product));
}
```

### Controller with Batch Operations

```java
@PostMapping("/batch")
@Operation(summary = "Create multiple products")
public ResponseEntity<List<ProductResponse>> createBatch(
        @Valid @RequestBody List<ProductRequest> requests) {
    List<Product> products = requests.stream()
        .map(productMapper::toEntity)
        .toList();
    List<Product> created = productService.createAll(products);
    return ResponseEntity
        .status(HttpStatus.CREATED)
        .body(created.stream()
            .map(productMapper::toResponse)
            .toList());
}

@DeleteMapping("/batch")
@Operation(summary = "Delete multiple products")
public ResponseEntity<Void> deleteBatch(@RequestBody List<UUID> ids) {
    productService.deleteAllById(ids);
    return ResponseEntity.noContent().build();
}
```

## Generation Rules

1. **URL Patterns**
   - Collection: `/api/v1/{entities}` (plural, lowercase, kebab-case)
   - Resource: `/api/v1/{entities}/{id}`
   - Actions: `/api/v1/{entities}/{id}/{action}`

2. **HTTP Methods**
   - POST: Create resource
   - GET: Read resource(s)
   - PUT: Full update
   - PATCH: Partial update
   - DELETE: Remove resource
   - HEAD: Check existence

3. **Status Codes**
   - 200: Success (GET, PUT, PATCH)
   - 201: Created (POST)
   - 204: No Content (DELETE)
   - 400: Bad Request (validation errors)
   - 404: Not Found
   - 409: Conflict (duplicate)

4. **Pagination**
   - Default page size: 20
   - Max page size: 100
   - Sort by createdAt DESC default

5. **Documentation**
   - All public methods documented
   - OpenAPI annotations required
   - Include request/response examples

## Best Practices

- Use constructor injection via `@RequiredArgsConstructor`
- Keep controllers thin - delegate to services
- Use DTOs for request/response (never expose entities)
- Validate all input with `@Valid`
- Return proper HTTP status codes
- Document all endpoints with OpenAPI
- Use meaningful operation IDs
- Handle errors globally (not in controllers)
