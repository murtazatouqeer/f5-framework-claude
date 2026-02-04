# Bean Validation

Standard Jakarta Bean Validation patterns for Spring Boot REST APIs.

## Dependencies

```groovy
dependencies {
    implementation 'org.springframework.boot:spring-boot-starter-validation'
}
```

## Basic Validation Annotations

### Common Constraints

```java
package com.example.app.web.dto;

import jakarta.validation.constraints.*;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;
import java.util.UUID;

public record ProductRequest(
    @NotBlank(message = "Name is required")
    @Size(min = 2, max = 100, message = "Name must be between 2 and 100 characters")
    String name,

    @Size(max = 2000, message = "Description cannot exceed 2000 characters")
    String description,

    @NotBlank(message = "SKU is required")
    @Pattern(regexp = "^[A-Z]{2,4}-\\d{4,8}$", message = "SKU must match format XX-0000")
    String sku,

    @NotNull(message = "Price is required")
    @DecimalMin(value = "0.01", message = "Price must be at least 0.01")
    @DecimalMax(value = "999999.99", message = "Price cannot exceed 999999.99")
    @Digits(integer = 6, fraction = 2, message = "Price must have max 6 integer and 2 fraction digits")
    BigDecimal price,

    @NotNull(message = "Quantity is required")
    @Min(value = 0, message = "Quantity cannot be negative")
    @Max(value = 10000, message = "Quantity cannot exceed 10000")
    Integer quantity,

    @NotNull(message = "Category ID is required")
    UUID categoryId,

    @Email(message = "Invalid email format")
    String contactEmail,

    @Past(message = "Manufacturing date must be in the past")
    LocalDate manufacturingDate,

    @Future(message = "Expiry date must be in the future")
    LocalDate expiryDate,

    @NotEmpty(message = "At least one tag is required")
    @Size(max = 10, message = "Maximum 10 tags allowed")
    List<@NotBlank(message = "Tag cannot be blank") String> tags
) {}
```

### Nested Object Validation

```java
public record OrderRequest(
    @NotNull(message = "Customer info is required")
    @Valid
    CustomerInfo customer,

    @NotEmpty(message = "At least one item is required")
    @Size(max = 50, message = "Maximum 50 items per order")
    List<@Valid OrderItem> items,

    @Valid
    ShippingAddress shippingAddress
) {}

public record CustomerInfo(
    @NotBlank(message = "Customer name is required")
    @Size(max = 100)
    String name,

    @NotBlank(message = "Email is required")
    @Email(message = "Invalid email format")
    String email,

    @Pattern(regexp = "^\\+?[1-9]\\d{1,14}$", message = "Invalid phone number")
    String phone
) {}

public record OrderItem(
    @NotNull(message = "Product ID is required")
    UUID productId,

    @NotNull(message = "Quantity is required")
    @Min(value = 1, message = "Quantity must be at least 1")
    @Max(value = 100, message = "Quantity cannot exceed 100")
    Integer quantity,

    @DecimalMin(value = "0.00")
    BigDecimal unitPrice
) {}

public record ShippingAddress(
    @NotBlank(message = "Street address is required")
    @Size(max = 200)
    String street,

    @NotBlank(message = "City is required")
    @Size(max = 100)
    String city,

    @NotBlank(message = "Postal code is required")
    @Pattern(regexp = "^\\d{5}(-\\d{4})?$", message = "Invalid postal code")
    String postalCode,

    @NotBlank(message = "Country is required")
    @Size(min = 2, max = 2, message = "Country must be ISO 2-letter code")
    String country
) {}
```

## Controller Integration

### Request Body Validation

```java
@RestController
@RequestMapping("/api/v1/products")
@RequiredArgsConstructor
public class ProductController {

    private final ProductService productService;

    @PostMapping
    public ResponseEntity<ProductResponse> create(
            @Valid @RequestBody ProductRequest request) {
        ProductResponse response = productService.create(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    @PutMapping("/{id}")
    public ResponseEntity<ProductResponse> update(
            @PathVariable UUID id,
            @Valid @RequestBody ProductRequest request) {
        ProductResponse response = productService.update(id, request);
        return ResponseEntity.ok(response);
    }

    @PatchMapping("/{id}")
    public ResponseEntity<ProductResponse> partialUpdate(
            @PathVariable UUID id,
            @Valid @RequestBody ProductPatchRequest request) {
        ProductResponse response = productService.partialUpdate(id, request);
        return ResponseEntity.ok(response);
    }
}
```

### Path Variable & Request Parameter Validation

```java
@RestController
@RequestMapping("/api/v1/products")
@Validated  // Required for method parameter validation
public class ProductController {

    @GetMapping("/{id}")
    public ResponseEntity<ProductResponse> getById(
            @PathVariable @NotNull UUID id) {
        return ResponseEntity.ok(productService.findById(id));
    }

    @GetMapping
    public ResponseEntity<Page<ProductResponse>> list(
            @RequestParam(defaultValue = "0")
            @Min(0) int page,

            @RequestParam(defaultValue = "20")
            @Min(1) @Max(100) int size,

            @RequestParam(required = false)
            @Size(max = 100) String search,

            @RequestParam(required = false)
            @Pattern(regexp = "^(ACTIVE|INACTIVE|DRAFT)$") String status) {

        Pageable pageable = PageRequest.of(page, size);
        return ResponseEntity.ok(productService.findAll(search, status, pageable));
    }

    @GetMapping("/by-sku/{sku}")
    public ResponseEntity<ProductResponse> getBySku(
            @PathVariable
            @NotBlank
            @Pattern(regexp = "^[A-Z]{2,4}-\\d{4,8}$") String sku) {
        return ResponseEntity.ok(productService.findBySku(sku));
    }
}
```

## Validation Groups

### Group Definitions

```java
public interface ValidationGroups {

    interface Create {}

    interface Update {}

    interface PartialUpdate {}

    interface Admin {}
}
```

### Using Groups

```java
public record UserRequest(
    @Null(groups = ValidationGroups.Create.class, message = "ID must be null on create")
    @NotNull(groups = ValidationGroups.Update.class, message = "ID is required on update")
    UUID id,

    @NotBlank(groups = {ValidationGroups.Create.class, ValidationGroups.Update.class})
    @Size(min = 2, max = 50)
    String firstName,

    @NotBlank(groups = {ValidationGroups.Create.class, ValidationGroups.Update.class})
    @Size(min = 2, max = 50)
    String lastName,

    @NotBlank(groups = ValidationGroups.Create.class, message = "Email required on create")
    @Email
    String email,

    @NotBlank(groups = ValidationGroups.Create.class, message = "Password required on create")
    @Size(min = 8, max = 100, groups = {ValidationGroups.Create.class, ValidationGroups.Update.class})
    String password,

    // Admin-only field
    @Null(groups = {ValidationGroups.Create.class, ValidationGroups.Update.class})
    @NotNull(groups = ValidationGroups.Admin.class)
    String role
) {}
```

### Controller with Groups

```java
@RestController
@RequestMapping("/api/v1/users")
public class UserController {

    @PostMapping
    public ResponseEntity<UserResponse> create(
            @Validated(ValidationGroups.Create.class)
            @RequestBody UserRequest request) {
        return ResponseEntity.status(HttpStatus.CREATED)
            .body(userService.create(request));
    }

    @PutMapping("/{id}")
    public ResponseEntity<UserResponse> update(
            @PathVariable UUID id,
            @Validated(ValidationGroups.Update.class)
            @RequestBody UserRequest request) {
        return ResponseEntity.ok(userService.update(id, request));
    }

    @PutMapping("/{id}/role")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<UserResponse> updateRole(
            @PathVariable UUID id,
            @Validated(ValidationGroups.Admin.class)
            @RequestBody UserRequest request) {
        return ResponseEntity.ok(userService.updateRole(id, request));
    }
}
```

## Group Sequences

```java
@GroupSequence({BasicChecks.class, AdvancedChecks.class, Default.class})
public interface OrderedChecks {}

public interface BasicChecks {}
public interface AdvancedChecks {}

public record RegistrationRequest(
    // Basic checks run first
    @NotBlank(groups = BasicChecks.class)
    @Size(min = 3, max = 50, groups = BasicChecks.class)
    String username,

    @NotBlank(groups = BasicChecks.class)
    @Email(groups = BasicChecks.class)
    String email,

    // Advanced checks run only if basic pass
    @UniqueUsername(groups = AdvancedChecks.class)
    String usernameForUniqueness,

    @UniqueEmail(groups = AdvancedChecks.class)
    String emailForUniqueness
) {
    public RegistrationRequest {
        usernameForUniqueness = username;
        emailForUniqueness = email;
    }
}

// Usage
@PostMapping("/register")
public ResponseEntity<UserResponse> register(
        @Validated(OrderedChecks.class)
        @RequestBody RegistrationRequest request) {
    return ResponseEntity.ok(userService.register(request));
}
```

## Service Layer Validation

```java
@Service
@Validated
@RequiredArgsConstructor
public class ProductService {

    private final ProductRepository productRepository;

    @Transactional
    public ProductResponse create(@Valid ProductRequest request) {
        // Validation runs automatically
        Product product = mapToEntity(request);
        return mapToResponse(productRepository.save(product));
    }

    @Transactional
    public void updatePrices(
            @NotEmpty List<@Valid PriceUpdate> updates) {
        updates.forEach(this::applyPriceUpdate);
    }

    public List<ProductResponse> findByIds(
            @NotEmpty @Size(max = 100)
            List<@NotNull UUID> ids) {
        return productRepository.findAllById(ids).stream()
            .map(this::mapToResponse)
            .toList();
    }
}
```

## Entity Validation

```java
@Entity
@Table(name = "products")
public class Product {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @NotBlank
    @Size(max = 100)
    @Column(nullable = false, length = 100)
    private String name;

    @NotBlank
    @Pattern(regexp = "^[A-Z]{2,4}-\\d{4,8}$")
    @Column(nullable = false, unique = true, length = 20)
    private String sku;

    @NotNull
    @DecimalMin("0.01")
    @Digits(integer = 6, fraction = 2)
    @Column(nullable = false, precision = 8, scale = 2)
    private BigDecimal price;

    @NotNull
    @Min(0)
    @Column(nullable = false)
    private Integer stock;

    @NotNull
    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private ProductStatus status;

    // Validation triggered on persist/update
    @PrePersist
    @PreUpdate
    private void validate() {
        if (status == ProductStatus.ACTIVE && stock == 0) {
            throw new IllegalStateException("Active products must have stock");
        }
    }
}
```

## Collection Validation

```java
public record BatchRequest(
    @NotEmpty(message = "Items list cannot be empty")
    @Size(max = 100, message = "Maximum 100 items per batch")
    List<@Valid ItemRequest> items,

    @Size(max = 10)
    Set<@NotBlank @Size(max = 50) String> tags,

    Map<@NotBlank String, @NotNull @Valid ConfigValue> config
) {}

public record ItemRequest(
    @NotNull UUID id,
    @NotBlank @Size(max = 100) String name,
    @NotNull @Min(1) Integer quantity
) {}

public record ConfigValue(
    @NotBlank String key,
    @NotNull Object value,
    @Pattern(regexp = "^(STRING|NUMBER|BOOLEAN)$") String type
) {}
```

## Programmatic Validation

```java
@Service
@RequiredArgsConstructor
public class ValidationService {

    private final Validator validator;

    public <T> void validate(T object) {
        Set<ConstraintViolation<T>> violations = validator.validate(object);
        if (!violations.isEmpty()) {
            throw new ConstraintViolationException(violations);
        }
    }

    public <T> void validate(T object, Class<?>... groups) {
        Set<ConstraintViolation<T>> violations = validator.validate(object, groups);
        if (!violations.isEmpty()) {
            throw new ConstraintViolationException(violations);
        }
    }

    public <T> ValidationResult<T> validateWithResult(T object) {
        Set<ConstraintViolation<T>> violations = validator.validate(object);
        if (violations.isEmpty()) {
            return ValidationResult.valid(object);
        }
        return ValidationResult.invalid(object, mapViolations(violations));
    }

    private <T> Map<String, List<String>> mapViolations(
            Set<ConstraintViolation<T>> violations) {
        return violations.stream()
            .collect(Collectors.groupingBy(
                v -> v.getPropertyPath().toString(),
                Collectors.mapping(
                    ConstraintViolation::getMessage,
                    Collectors.toList()
                )
            ));
    }
}

public record ValidationResult<T>(
    T object,
    boolean valid,
    Map<String, List<String>> errors
) {
    public static <T> ValidationResult<T> valid(T object) {
        return new ValidationResult<>(object, true, Map.of());
    }

    public static <T> ValidationResult<T> invalid(
            T object, Map<String, List<String>> errors) {
        return new ValidationResult<>(object, false, errors);
    }
}
```

## Exception Handling

```java
@RestControllerAdvice
public class ValidationExceptionHandler {

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> handleValidationErrors(
            MethodArgumentNotValidException ex) {

        Map<String, List<String>> errors = ex.getBindingResult()
            .getFieldErrors()
            .stream()
            .collect(Collectors.groupingBy(
                FieldError::getField,
                Collectors.mapping(
                    FieldError::getDefaultMessage,
                    Collectors.toList()
                )
            ));

        ErrorResponse response = new ErrorResponse(
            "VALIDATION_ERROR",
            "Validation failed",
            errors
        );

        return ResponseEntity.badRequest().body(response);
    }

    @ExceptionHandler(ConstraintViolationException.class)
    public ResponseEntity<ErrorResponse> handleConstraintViolation(
            ConstraintViolationException ex) {

        Map<String, List<String>> errors = ex.getConstraintViolations()
            .stream()
            .collect(Collectors.groupingBy(
                v -> extractPropertyName(v.getPropertyPath()),
                Collectors.mapping(
                    ConstraintViolation::getMessage,
                    Collectors.toList()
                )
            ));

        ErrorResponse response = new ErrorResponse(
            "CONSTRAINT_VIOLATION",
            "Constraint violation",
            errors
        );

        return ResponseEntity.badRequest().body(response);
    }

    @ExceptionHandler(HttpMessageNotReadableException.class)
    public ResponseEntity<ErrorResponse> handleMalformedJson(
            HttpMessageNotReadableException ex) {

        ErrorResponse response = new ErrorResponse(
            "MALFORMED_REQUEST",
            "Malformed JSON request body",
            Map.of()
        );

        return ResponseEntity.badRequest().body(response);
    }

    private String extractPropertyName(Path path) {
        String fullPath = path.toString();
        int lastDot = fullPath.lastIndexOf('.');
        return lastDot > 0 ? fullPath.substring(lastDot + 1) : fullPath;
    }
}

public record ErrorResponse(
    String code,
    String message,
    Map<String, List<String>> errors
) {}
```

## Configuration

```java
@Configuration
public class ValidationConfig {

    @Bean
    public LocalValidatorFactoryBean validator() {
        LocalValidatorFactoryBean bean = new LocalValidatorFactoryBean();
        bean.setValidationMessageSource(messageSource());
        return bean;
    }

    @Bean
    public MessageSource messageSource() {
        ReloadableResourceBundleMessageSource messageSource =
            new ReloadableResourceBundleMessageSource();
        messageSource.setBasename("classpath:messages/validation");
        messageSource.setDefaultEncoding("UTF-8");
        return messageSource;
    }

    @Bean
    public MethodValidationPostProcessor methodValidationPostProcessor() {
        return new MethodValidationPostProcessor();
    }
}
```

### Custom Messages (messages/validation.properties)

```properties
# Default messages
NotBlank.default=This field is required
NotNull.default=This field cannot be null
Size.default=Size must be between {min} and {max}
Email.default=Invalid email format
Pattern.default=Invalid format

# Field-specific messages
NotBlank.productRequest.name=Product name is required
Size.productRequest.name=Product name must be between {min} and {max} characters
DecimalMin.productRequest.price=Price must be at least {value}
Pattern.productRequest.sku=SKU must match format XX-0000

# Custom constraint messages
UniqueEmail=This email is already registered
UniqueUsername=This username is already taken
ValidDateRange=End date must be after start date
```

## Best Practices

1. **Use records for DTOs** - Immutable and cleaner syntax
2. **Validate at boundaries** - Controllers and service entry points
3. **Use @Valid for nested objects** - Ensures deep validation
4. **Custom messages** - User-friendly error messages
5. **Validation groups** - Different rules for different operations
6. **Group sequences** - Order validation checks efficiently
7. **Programmatic validation** - For complex business rules
8. **Consistent error format** - Standard error response structure
