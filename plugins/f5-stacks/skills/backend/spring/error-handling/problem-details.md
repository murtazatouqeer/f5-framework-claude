# Problem Details (RFC 7807)

Standard problem details format for HTTP APIs based on RFC 7807 / RFC 9457.

## Dependencies

```groovy
// Spring Boot 3.x has built-in support
dependencies {
    implementation 'org.springframework.boot:spring-boot-starter-web'
}
```

## Enable Problem Details

### Application Properties

```yaml
# application.yml
spring:
  mvc:
    problemdetails:
      enabled: true
```

### Configuration

```java
@Configuration
public class ProblemDetailsConfig {

    @Bean
    public ProblemDetailsExceptionHandler problemDetailsExceptionHandler() {
        return new ProblemDetailsExceptionHandler();
    }
}
```

## Custom Problem Detail Types

### Base Problem Detail

```java
package com.example.app.exception;

import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.web.ErrorResponseException;

import java.net.URI;
import java.time.Instant;
import java.util.Map;

public class ApiException extends ErrorResponseException {

    public ApiException(HttpStatus status, String type, String title, String detail) {
        super(status, asProblemDetail(status, type, title, detail, null), null);
    }

    public ApiException(HttpStatus status, String type, String title,
                        String detail, Map<String, Object> properties) {
        super(status, asProblemDetail(status, type, title, detail, properties), null);
    }

    private static ProblemDetail asProblemDetail(
            HttpStatus status,
            String type,
            String title,
            String detail,
            Map<String, Object> properties) {

        ProblemDetail problem = ProblemDetail.forStatusAndDetail(status, detail);
        problem.setType(URI.create("https://api.example.com/errors/" + type));
        problem.setTitle(title);
        problem.setProperty("timestamp", Instant.now());

        if (properties != null) {
            properties.forEach(problem::setProperty);
        }

        return problem;
    }
}
```

### Specific Exception Types

```java
// Resource Not Found
public class ResourceNotFoundProblem extends ApiException {

    public ResourceNotFoundProblem(String resourceType, Object id) {
        super(
            HttpStatus.NOT_FOUND,
            "resource-not-found",
            "Resource Not Found",
            String.format("%s with id '%s' was not found", resourceType, id),
            Map.of(
                "resourceType", resourceType,
                "resourceId", String.valueOf(id)
            )
        );
    }

    public static ResourceNotFoundProblem product(UUID id) {
        return new ResourceNotFoundProblem("Product", id);
    }

    public static ResourceNotFoundProblem user(UUID id) {
        return new ResourceNotFoundProblem("User", id);
    }
}

// Validation Problem
public class ValidationProblem extends ApiException {

    public ValidationProblem(Map<String, List<String>> fieldErrors) {
        super(
            HttpStatus.BAD_REQUEST,
            "validation-error",
            "Validation Failed",
            "One or more fields have validation errors",
            Map.of("errors", fieldErrors)
        );
    }

    public ValidationProblem(String field, String message) {
        this(Map.of(field, List.of(message)));
    }
}

// Business Rule Violation
public class BusinessRuleProblem extends ApiException {

    public BusinessRuleProblem(String ruleCode, String detail) {
        super(
            HttpStatus.UNPROCESSABLE_ENTITY,
            "business-rule-violation",
            "Business Rule Violation",
            detail,
            Map.of("ruleCode", ruleCode)
        );
    }

    public static BusinessRuleProblem insufficientStock(
            String productName, int available, int requested) {
        return new BusinessRuleProblem(
            "INSUFFICIENT_STOCK",
            String.format("Insufficient stock for '%s'. Available: %d, Requested: %d",
                productName, available, requested)
        );
    }
}

// Conflict Problem
public class ConflictProblem extends ApiException {

    public ConflictProblem(String detail) {
        super(
            HttpStatus.CONFLICT,
            "conflict",
            "Conflict",
            detail
        );
    }

    public static ConflictProblem duplicateResource(String field, Object value) {
        return new ConflictProblem(
            String.format("A resource with %s '%s' already exists", field, value)
        );
    }

    public static ConflictProblem optimisticLock() {
        return new ConflictProblem(
            "The resource was modified by another user. Please refresh and try again."
        );
    }
}

// Authentication Problem
public class AuthenticationProblem extends ApiException {

    public AuthenticationProblem(String detail) {
        super(
            HttpStatus.UNAUTHORIZED,
            "authentication-required",
            "Authentication Required",
            detail
        );
    }

    public static AuthenticationProblem invalidCredentials() {
        return new AuthenticationProblem("Invalid email or password");
    }

    public static AuthenticationProblem tokenExpired() {
        return new AuthenticationProblem("Authentication token has expired");
    }
}

// Authorization Problem
public class AuthorizationProblem extends ApiException {

    public AuthorizationProblem(String detail) {
        super(
            HttpStatus.FORBIDDEN,
            "access-denied",
            "Access Denied",
            detail
        );
    }

    public static AuthorizationProblem insufficientPermissions() {
        return new AuthorizationProblem(
            "You do not have permission to perform this action"
        );
    }
}

// Rate Limit Problem
public class RateLimitProblem extends ApiException {

    public RateLimitProblem(int retryAfterSeconds) {
        super(
            HttpStatus.TOO_MANY_REQUESTS,
            "rate-limit-exceeded",
            "Rate Limit Exceeded",
            "Too many requests. Please try again later.",
            Map.of("retryAfter", retryAfterSeconds)
        );
    }
}
```

## Global Exception Handler with Problem Details

```java
package com.example.app.exception;

import io.micrometer.tracing.Tracer;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.ConstraintViolationException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.dao.OptimisticLockingFailureException;
import org.springframework.http.*;
import org.springframework.lang.Nullable;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.context.request.WebRequest;
import org.springframework.web.servlet.mvc.method.annotation.ResponseEntityExceptionHandler;

import java.net.URI;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Slf4j
@RestControllerAdvice
@RequiredArgsConstructor
public class ProblemDetailsExceptionHandler extends ResponseEntityExceptionHandler {

    private static final String BASE_TYPE = "https://api.example.com/errors/";

    private final Tracer tracer;

    // ==================== Override Spring Handlers ====================

    @Override
    protected ResponseEntity<Object> handleMethodArgumentNotValid(
            MethodArgumentNotValidException ex,
            HttpHeaders headers,
            HttpStatusCode status,
            WebRequest request) {

        Map<String, List<String>> fieldErrors = ex.getBindingResult()
            .getFieldErrors()
            .stream()
            .collect(Collectors.groupingBy(
                FieldError::getField,
                Collectors.mapping(
                    FieldError::getDefaultMessage,
                    Collectors.toList()
                )
            ));

        ProblemDetail problem = createProblemDetail(
            HttpStatus.BAD_REQUEST,
            "validation-error",
            "Validation Failed",
            "One or more fields have validation errors"
        );
        problem.setProperty("errors", fieldErrors);

        return ResponseEntity.badRequest()
            .contentType(MediaType.APPLICATION_PROBLEM_JSON)
            .body(problem);
    }

    @Override
    protected ResponseEntity<Object> handleExceptionInternal(
            Exception ex,
            @Nullable Object body,
            HttpHeaders headers,
            HttpStatusCode statusCode,
            WebRequest request) {

        if (body instanceof ProblemDetail problem) {
            enrichProblemDetail(problem);
            return ResponseEntity.status(statusCode)
                .contentType(MediaType.APPLICATION_PROBLEM_JSON)
                .body(problem);
        }

        HttpStatus status = HttpStatus.valueOf(statusCode.value());
        ProblemDetail problem = createProblemDetail(
            status,
            "internal-error",
            status.getReasonPhrase(),
            ex.getMessage()
        );

        return ResponseEntity.status(statusCode)
            .contentType(MediaType.APPLICATION_PROBLEM_JSON)
            .body(problem);
    }

    // ==================== Custom Exception Handlers ====================

    @ExceptionHandler(ConstraintViolationException.class)
    public ResponseEntity<ProblemDetail> handleConstraintViolation(
            ConstraintViolationException ex) {

        Map<String, List<String>> errors = ex.getConstraintViolations()
            .stream()
            .collect(Collectors.groupingBy(
                cv -> extractPropertyName(cv.getPropertyPath().toString()),
                Collectors.mapping(
                    cv -> cv.getMessage(),
                    Collectors.toList()
                )
            ));

        ProblemDetail problem = createProblemDetail(
            HttpStatus.BAD_REQUEST,
            "constraint-violation",
            "Constraint Violation",
            "One or more constraints were violated"
        );
        problem.setProperty("errors", errors);

        return ResponseEntity.badRequest()
            .contentType(MediaType.APPLICATION_PROBLEM_JSON)
            .body(problem);
    }

    @ExceptionHandler(BadCredentialsException.class)
    public ResponseEntity<ProblemDetail> handleBadCredentials(BadCredentialsException ex) {
        log.warn("Authentication failed: bad credentials");

        ProblemDetail problem = createProblemDetail(
            HttpStatus.UNAUTHORIZED,
            "invalid-credentials",
            "Authentication Failed",
            "Invalid email or password"
        );

        return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
            .contentType(MediaType.APPLICATION_PROBLEM_JSON)
            .body(problem);
    }

    @ExceptionHandler(AccessDeniedException.class)
    public ResponseEntity<ProblemDetail> handleAccessDenied(AccessDeniedException ex) {
        log.warn("Access denied: {}", ex.getMessage());

        ProblemDetail problem = createProblemDetail(
            HttpStatus.FORBIDDEN,
            "access-denied",
            "Access Denied",
            "You do not have permission to perform this action"
        );

        return ResponseEntity.status(HttpStatus.FORBIDDEN)
            .contentType(MediaType.APPLICATION_PROBLEM_JSON)
            .body(problem);
    }

    @ExceptionHandler(DataIntegrityViolationException.class)
    public ResponseEntity<ProblemDetail> handleDataIntegrity(
            DataIntegrityViolationException ex) {
        log.error("Data integrity violation", ex);

        String detail = "Data integrity violation occurred";
        String type = "data-integrity-error";

        String exMessage = ex.getMostSpecificCause().getMessage();
        if (exMessage != null) {
            if (exMessage.contains("unique constraint") ||
                exMessage.contains("duplicate key")) {
                detail = "A record with this value already exists";
                type = "duplicate-entry";
            } else if (exMessage.contains("foreign key constraint")) {
                detail = "Cannot delete - record is referenced by other records";
                type = "foreign-key-violation";
            }
        }

        ProblemDetail problem = createProblemDetail(
            HttpStatus.CONFLICT,
            type,
            "Data Conflict",
            detail
        );

        return ResponseEntity.status(HttpStatus.CONFLICT)
            .contentType(MediaType.APPLICATION_PROBLEM_JSON)
            .body(problem);
    }

    @ExceptionHandler(OptimisticLockingFailureException.class)
    public ResponseEntity<ProblemDetail> handleOptimisticLock(
            OptimisticLockingFailureException ex) {
        log.warn("Optimistic locking failure");

        ProblemDetail problem = createProblemDetail(
            HttpStatus.CONFLICT,
            "optimistic-lock-failure",
            "Concurrent Modification",
            "The resource was modified by another user. Please refresh and try again."
        );

        return ResponseEntity.status(HttpStatus.CONFLICT)
            .contentType(MediaType.APPLICATION_PROBLEM_JSON)
            .body(problem);
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ProblemDetail> handleGenericException(Exception ex) {
        log.error("Unexpected error occurred", ex);

        ProblemDetail problem = createProblemDetail(
            HttpStatus.INTERNAL_SERVER_ERROR,
            "internal-error",
            "Internal Server Error",
            "An unexpected error occurred. Please try again later."
        );

        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
            .contentType(MediaType.APPLICATION_PROBLEM_JSON)
            .body(problem);
    }

    // ==================== Helper Methods ====================

    private ProblemDetail createProblemDetail(
            HttpStatus status,
            String type,
            String title,
            String detail) {

        ProblemDetail problem = ProblemDetail.forStatusAndDetail(status, detail);
        problem.setType(URI.create(BASE_TYPE + type));
        problem.setTitle(title);
        enrichProblemDetail(problem);

        return problem;
    }

    private void enrichProblemDetail(ProblemDetail problem) {
        problem.setProperty("timestamp", Instant.now());

        if (tracer != null && tracer.currentSpan() != null) {
            problem.setProperty("traceId", tracer.currentSpan().context().traceId());
        }
    }

    private String extractPropertyName(String path) {
        int lastDot = path.lastIndexOf('.');
        return lastDot > 0 ? path.substring(lastDot + 1) : path;
    }
}
```

## Custom Problem Detail Extensions

### Extended Problem Detail

```java
public class ExtendedProblemDetail {

    public static ProblemDetail validation(Map<String, List<String>> errors) {
        ProblemDetail problem = ProblemDetail.forStatus(HttpStatus.BAD_REQUEST);
        problem.setType(URI.create("https://api.example.com/errors/validation-error"));
        problem.setTitle("Validation Failed");
        problem.setDetail("One or more fields have validation errors");
        problem.setProperty("errors", errors);
        problem.setProperty("timestamp", Instant.now());
        return problem;
    }

    public static ProblemDetail notFound(String resourceType, Object id) {
        ProblemDetail problem = ProblemDetail.forStatus(HttpStatus.NOT_FOUND);
        problem.setType(URI.create("https://api.example.com/errors/resource-not-found"));
        problem.setTitle("Resource Not Found");
        problem.setDetail(String.format("%s with id '%s' was not found", resourceType, id));
        problem.setProperty("resourceType", resourceType);
        problem.setProperty("resourceId", String.valueOf(id));
        problem.setProperty("timestamp", Instant.now());
        return problem;
    }

    public static ProblemDetail conflict(String detail, String conflictType) {
        ProblemDetail problem = ProblemDetail.forStatus(HttpStatus.CONFLICT);
        problem.setType(URI.create("https://api.example.com/errors/" + conflictType));
        problem.setTitle("Conflict");
        problem.setDetail(detail);
        problem.setProperty("timestamp", Instant.now());
        return problem;
    }

    public static ProblemDetail businessRule(String ruleCode, String detail) {
        ProblemDetail problem = ProblemDetail.forStatus(HttpStatus.UNPROCESSABLE_ENTITY);
        problem.setType(URI.create("https://api.example.com/errors/business-rule-violation"));
        problem.setTitle("Business Rule Violation");
        problem.setDetail(detail);
        problem.setProperty("ruleCode", ruleCode);
        problem.setProperty("timestamp", Instant.now());
        return problem;
    }

    public static ProblemDetail rateLimit(int retryAfterSeconds) {
        ProblemDetail problem = ProblemDetail.forStatus(HttpStatus.TOO_MANY_REQUESTS);
        problem.setType(URI.create("https://api.example.com/errors/rate-limit-exceeded"));
        problem.setTitle("Rate Limit Exceeded");
        problem.setDetail("Too many requests. Please try again later.");
        problem.setProperty("retryAfter", retryAfterSeconds);
        problem.setProperty("timestamp", Instant.now());
        return problem;
    }
}
```

## Controller Usage

```java
@RestController
@RequestMapping("/api/v1/products")
@RequiredArgsConstructor
public class ProductController {

    private final ProductService productService;

    @GetMapping("/{id}")
    public ResponseEntity<ProductResponse> getById(@PathVariable UUID id) {
        return productService.findById(id)
            .map(ResponseEntity::ok)
            .orElseThrow(() -> new ResourceNotFoundProblem("Product", id));
    }

    @PostMapping
    public ResponseEntity<ProductResponse> create(
            @Valid @RequestBody ProductRequest request) {
        try {
            ProductResponse response = productService.create(request);
            return ResponseEntity.status(HttpStatus.CREATED).body(response);
        } catch (DuplicateSkuException e) {
            throw ConflictProblem.duplicateResource("sku", request.sku());
        }
    }

    @PutMapping("/{id}")
    public ResponseEntity<ProductResponse> update(
            @PathVariable UUID id,
            @Valid @RequestBody ProductRequest request) {
        try {
            return ResponseEntity.ok(productService.update(id, request));
        } catch (OptimisticLockingFailureException e) {
            throw ConflictProblem.optimisticLock();
        }
    }
}
```

## Response Examples

### Validation Error Response

```json
{
    "type": "https://api.example.com/errors/validation-error",
    "title": "Validation Failed",
    "status": 400,
    "detail": "One or more fields have validation errors",
    "instance": "/api/v1/products",
    "timestamp": "2024-01-15T10:30:00Z",
    "traceId": "abc123def456",
    "errors": {
        "name": ["Name is required", "Name must be between 2 and 100 characters"],
        "price": ["Price must be positive"]
    }
}
```

### Resource Not Found Response

```json
{
    "type": "https://api.example.com/errors/resource-not-found",
    "title": "Resource Not Found",
    "status": 404,
    "detail": "Product with id '550e8400-e29b-41d4-a716-446655440000' was not found",
    "instance": "/api/v1/products/550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2024-01-15T10:30:00Z",
    "traceId": "abc123def456",
    "resourceType": "Product",
    "resourceId": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Business Rule Violation Response

```json
{
    "type": "https://api.example.com/errors/business-rule-violation",
    "title": "Business Rule Violation",
    "status": 422,
    "detail": "Insufficient stock for 'Widget'. Available: 5, Requested: 10",
    "instance": "/api/v1/orders",
    "timestamp": "2024-01-15T10:30:00Z",
    "traceId": "abc123def456",
    "ruleCode": "INSUFFICIENT_STOCK"
}
```

## Testing Problem Details

```java
@WebMvcTest(ProductController.class)
class ProductControllerProblemDetailsTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private ProductService productService;

    @Test
    void shouldReturnProblemDetailForNotFound() throws Exception {
        UUID productId = UUID.randomUUID();
        when(productService.findById(productId)).thenReturn(Optional.empty());

        mockMvc.perform(get("/api/v1/products/{id}", productId))
            .andExpect(status().isNotFound())
            .andExpect(content().contentType(MediaType.APPLICATION_PROBLEM_JSON))
            .andExpect(jsonPath("$.type").value("https://api.example.com/errors/resource-not-found"))
            .andExpect(jsonPath("$.title").value("Resource Not Found"))
            .andExpect(jsonPath("$.status").value(404))
            .andExpect(jsonPath("$.resourceType").value("Product"))
            .andExpect(jsonPath("$.resourceId").value(productId.toString()))
            .andExpect(jsonPath("$.timestamp").exists());
    }

    @Test
    void shouldReturnProblemDetailForValidationErrors() throws Exception {
        mockMvc.perform(post("/api/v1/products")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"name\":\"\",\"price\":-1}"))
            .andExpect(status().isBadRequest())
            .andExpect(content().contentType(MediaType.APPLICATION_PROBLEM_JSON))
            .andExpect(jsonPath("$.type").value("https://api.example.com/errors/validation-error"))
            .andExpect(jsonPath("$.title").value("Validation Failed"))
            .andExpect(jsonPath("$.errors.name").exists())
            .andExpect(jsonPath("$.errors.price").exists());
    }
}
```

## Best Practices

1. **Use standard type URIs** - Document all error types at your API docs URL
2. **Include trace ID** - For correlation in distributed systems
3. **Consistent structure** - Same fields across all error responses
4. **Proper content type** - `application/problem+json`
5. **Meaningful titles** - Human-readable error category
6. **Detailed descriptions** - Actionable detail messages
7. **Extension properties** - Add context-specific fields
8. **Document error types** - API docs should list all possible error types
