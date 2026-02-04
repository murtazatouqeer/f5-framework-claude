# REST Controller Template

Spring Boot REST controller template with CRUD operations, pagination, and OpenAPI documentation.

## Template

```java
package {{package}}.web.controller;

import {{package}}.service.{{Entity}}Service;
import {{package}}.web.dto.{{Entity}}Request;
import {{package}}.web.dto.{{Entity}}Response;
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

import java.util.UUID;

@RestController
@RequestMapping("/api/v1/{{entities}}")
@RequiredArgsConstructor
@Tag(name = "{{Entity}}", description = "{{Entity}} management APIs")
@SecurityRequirement(name = "bearerAuth")
public class {{Entity}}Controller {

    private final {{Entity}}Service {{entity}}Service;

    @GetMapping
    @Operation(summary = "List all {{entities}}", description = "Returns paginated list of {{entities}}")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "Successfully retrieved list"),
        @ApiResponse(responseCode = "401", description = "Unauthorized")
    })
    public ResponseEntity<Page<{{Entity}}Response>> list(
            @Parameter(description = "Search query")
            @RequestParam(required = false) String search,
            @PageableDefault(size = 20, sort = "createdAt", direction = Sort.Direction.DESC)
            Pageable pageable) {
        return ResponseEntity.ok({{entity}}Service.findAll(search, pageable));
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get {{entity}} by ID", description = "Returns a single {{entity}}")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "Successfully retrieved {{entity}}"),
        @ApiResponse(responseCode = "404", description = "{{Entity}} not found")
    })
    public ResponseEntity<{{Entity}}Response> getById(
            @Parameter(description = "{{Entity}} ID", required = true)
            @PathVariable UUID id) {
        return ResponseEntity.ok({{entity}}Service.findById(id));
    }

    @PostMapping
    @Operation(summary = "Create {{entity}}", description = "Creates a new {{entity}}")
    @ApiResponses({
        @ApiResponse(responseCode = "201", description = "{{Entity}} created successfully"),
        @ApiResponse(responseCode = "400", description = "Invalid input"),
        @ApiResponse(responseCode = "409", description = "{{Entity}} already exists")
    })
    @PreAuthorize("hasAnyRole('ADMIN', 'MANAGER')")
    public ResponseEntity<{{Entity}}Response> create(
            @Parameter(description = "{{Entity}} data", required = true)
            @Valid @RequestBody {{Entity}}Request request) {
        {{Entity}}Response created = {{entity}}Service.create(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(created);
    }

    @PutMapping("/{id}")
    @Operation(summary = "Update {{entity}}", description = "Updates an existing {{entity}}")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "{{Entity}} updated successfully"),
        @ApiResponse(responseCode = "400", description = "Invalid input"),
        @ApiResponse(responseCode = "404", description = "{{Entity}} not found")
    })
    @PreAuthorize("hasAnyRole('ADMIN', 'MANAGER')")
    public ResponseEntity<{{Entity}}Response> update(
            @PathVariable UUID id,
            @Valid @RequestBody {{Entity}}Request request) {
        return ResponseEntity.ok({{entity}}Service.update(id, request));
    }

    @PatchMapping("/{id}")
    @Operation(summary = "Partial update {{entity}}", description = "Partially updates an existing {{entity}}")
    @PreAuthorize("hasAnyRole('ADMIN', 'MANAGER')")
    public ResponseEntity<{{Entity}}Response> partialUpdate(
            @PathVariable UUID id,
            @RequestBody {{Entity}}PatchRequest request) {
        return ResponseEntity.ok({{entity}}Service.partialUpdate(id, request));
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "Delete {{entity}}", description = "Deletes a {{entity}}")
    @ApiResponses({
        @ApiResponse(responseCode = "204", description = "{{Entity}} deleted successfully"),
        @ApiResponse(responseCode = "404", description = "{{Entity}} not found")
    })
    @PreAuthorize("hasRole('ADMIN')")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void delete(@PathVariable UUID id) {
        {{entity}}Service.delete(id);
    }
}
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{package}}` | Base package name | `com.example.app` |
| `{{Entity}}` | Entity name (PascalCase) | `Product` |
| `{{entity}}` | Entity name (camelCase) | `product` |
| `{{entities}}` | Entity name plural (kebab-case) | `products` |

## Usage Example

For a `Product` entity:

```java
package com.example.app.web.controller;

import com.example.app.service.ProductService;
import com.example.app.web.dto.ProductRequest;
import com.example.app.web.dto.ProductResponse;
// ... other imports

@RestController
@RequestMapping("/api/v1/products")
@RequiredArgsConstructor
@Tag(name = "Product", description = "Product management APIs")
public class ProductController {

    private final ProductService productService;

    @GetMapping
    public ResponseEntity<Page<ProductResponse>> list(
            @RequestParam(required = false) String search,
            @PageableDefault(size = 20) Pageable pageable) {
        return ResponseEntity.ok(productService.findAll(search, pageable));
    }

    // ... other methods
}
```

## Customization Options

### With Filtering

```java
@GetMapping
public ResponseEntity<Page<{{Entity}}Response>> list(
        @RequestParam(required = false) String search,
        @RequestParam(required = false) UUID categoryId,
        @RequestParam(required = false) {{Entity}}Status status,
        @RequestParam(required = false) BigDecimal minPrice,
        @RequestParam(required = false) BigDecimal maxPrice,
        @PageableDefault(size = 20) Pageable pageable) {

    {{Entity}}Filter filter = {{Entity}}Filter.builder()
        .search(search)
        .categoryId(categoryId)
        .status(status)
        .minPrice(minPrice)
        .maxPrice(maxPrice)
        .build();

    return ResponseEntity.ok({{entity}}Service.findAll(filter, pageable));
}
```

### With Bulk Operations

```java
@PostMapping("/bulk")
@PreAuthorize("hasRole('ADMIN')")
public ResponseEntity<List<{{Entity}}Response>> createBulk(
        @Valid @RequestBody List<{{Entity}}Request> requests) {
    return ResponseEntity.status(HttpStatus.CREATED)
        .body({{entity}}Service.createBulk(requests));
}

@DeleteMapping("/bulk")
@PreAuthorize("hasRole('ADMIN')")
@ResponseStatus(HttpStatus.NO_CONTENT)
public void deleteBulk(@RequestBody List<UUID> ids) {
    {{entity}}Service.deleteBulk(ids);
}
```

### With File Upload

```java
@PostMapping("/{id}/image")
public ResponseEntity<{{Entity}}Response> uploadImage(
        @PathVariable UUID id,
        @RequestParam("file") MultipartFile file) {
    return ResponseEntity.ok({{entity}}Service.uploadImage(id, file));
}
```

### With Export

```java
@GetMapping("/export")
@PreAuthorize("hasRole('ADMIN')")
public ResponseEntity<Resource> export(
        @RequestParam(defaultValue = "csv") String format) {
    Resource resource = {{entity}}Service.export(format);
    return ResponseEntity.ok()
        .contentType(MediaType.APPLICATION_OCTET_STREAM)
        .header(HttpHeaders.CONTENT_DISPOSITION,
            "attachment; filename=\"{{entities}}." + format + "\"")
        .body(resource);
}
```
