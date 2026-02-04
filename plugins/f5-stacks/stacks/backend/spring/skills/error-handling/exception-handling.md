# Exception Handling

Centralized exception handling patterns for Spring Boot REST APIs.

## Global Exception Handler

### Basic Setup

```java
package com.example.app.exception;

import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(ResourceNotFoundException.class)
    public ResponseEntity<ErrorResponse> handleResourceNotFound(ResourceNotFoundException ex) {
        log.warn("Resource not found: {}", ex.getMessage());

        ErrorResponse error = ErrorResponse.builder()
            .code("RESOURCE_NOT_FOUND")
            .message(ex.getMessage())
            .build();

        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(error);
    }

    @ExceptionHandler(BusinessException.class)
    public ResponseEntity<ErrorResponse> handleBusinessException(BusinessException ex) {
        log.warn("Business rule violation: {}", ex.getMessage());

        ErrorResponse error = ErrorResponse.builder()
            .code(ex.getErrorCode())
            .message(ex.getMessage())
            .build();

        return ResponseEntity.status(HttpStatus.UNPROCESSABLE_ENTITY).body(error);
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleGenericException(Exception ex) {
        log.error("Unexpected error occurred", ex);

        ErrorResponse error = ErrorResponse.builder()
            .code("INTERNAL_ERROR")
            .message("An unexpected error occurred")
            .build();

        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
    }
}
```

### Error Response Model

```java
package com.example.app.exception;

import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.Builder;
import lombok.Data;

import java.time.Instant;
import java.util.List;
import java.util.Map;

@Data
@Builder
@JsonInclude(JsonInclude.Include.NON_NULL)
public class ErrorResponse {
    private final String code;
    private final String message;
    private final String path;
    @Builder.Default
    private final Instant timestamp = Instant.now();
    private final Map<String, List<String>> fieldErrors;
    private final List<String> details;
    private final String traceId;
}
```

## Custom Exceptions

### Base Exception

```java
package com.example.app.exception;

import lombok.Getter;

@Getter
public abstract class BaseException extends RuntimeException {
    private final String errorCode;
    private final Object[] args;

    protected BaseException(String errorCode, String message, Object... args) {
        super(message);
        this.errorCode = errorCode;
        this.args = args;
    }

    protected BaseException(String errorCode, String message, Throwable cause) {
        super(message, cause);
        this.errorCode = errorCode;
        this.args = new Object[0];
    }
}
```

### Specific Exceptions

```java
// Resource not found
public class ResourceNotFoundException extends BaseException {
    public ResourceNotFoundException(String resourceType, Object id) {
        super("RESOURCE_NOT_FOUND",
              String.format("%s not found with id: %s", resourceType, id),
              resourceType, id);
    }

    public static ResourceNotFoundException product(UUID id) {
        return new ResourceNotFoundException("Product", id);
    }

    public static ResourceNotFoundException user(UUID id) {
        return new ResourceNotFoundException("User", id);
    }

    public static ResourceNotFoundException order(UUID id) {
        return new ResourceNotFoundException("Order", id);
    }
}

// Business rule violation
@Getter
public class BusinessException extends BaseException {
    public BusinessException(String errorCode, String message) {
        super(errorCode, message);
    }

    public static BusinessException insufficientStock(String productName, int available, int requested) {
        return new BusinessException("INSUFFICIENT_STOCK",
            String.format("Insufficient stock for %s. Available: %d, Requested: %d",
                productName, available, requested));
    }

    public static BusinessException orderAlreadyShipped(UUID orderId) {
        return new BusinessException("ORDER_ALREADY_SHIPPED",
            "Cannot modify order " + orderId + " - already shipped");
    }

    public static BusinessException duplicateEmail(String email) {
        return new BusinessException("DUPLICATE_EMAIL",
            "Email " + email + " is already registered");
    }
}

// Authentication/Authorization
public class UnauthorizedException extends BaseException {
    public UnauthorizedException(String message) {
        super("UNAUTHORIZED", message);
    }

    public static UnauthorizedException invalidCredentials() {
        return new UnauthorizedException("Invalid email or password");
    }

    public static UnauthorizedException tokenExpired() {
        return new UnauthorizedException("Authentication token has expired");
    }
}

public class ForbiddenException extends BaseException {
    public ForbiddenException(String message) {
        super("FORBIDDEN", message);
    }

    public static ForbiddenException accessDenied() {
        return new ForbiddenException("Access denied");
    }

    public static ForbiddenException resourceOwnerOnly() {
        return new ForbiddenException("Only the resource owner can perform this action");
    }
}

// Conflict
public class ConflictException extends BaseException {
    public ConflictException(String message) {
        super("CONFLICT", message);
    }

    public static ConflictException optimisticLock(String resourceType) {
        return new ConflictException(
            resourceType + " was modified by another user. Please refresh and try again.");
    }

    public static ConflictException duplicateResource(String resourceType, String field, Object value) {
        return new ConflictException(
            String.format("%s with %s '%s' already exists", resourceType, field, value));
    }
}

// Validation
@Getter
public class ValidationException extends BaseException {
    private final Map<String, List<String>> fieldErrors;

    public ValidationException(String message, Map<String, List<String>> fieldErrors) {
        super("VALIDATION_ERROR", message);
        this.fieldErrors = fieldErrors;
    }

    public ValidationException(String field, String message) {
        super("VALIDATION_ERROR", message);
        this.fieldErrors = Map.of(field, List.of(message));
    }
}
```

## Comprehensive Exception Handler

```java
package com.example.app.exception;

import io.micrometer.tracing.Tracer;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.ConstraintViolationException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.dao.OptimisticLockingFailureException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.core.AuthenticationException;
import org.springframework.web.HttpMediaTypeNotSupportedException;
import org.springframework.web.HttpRequestMethodNotSupportedException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.MissingServletRequestParameterException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;
import org.springframework.web.multipart.MaxUploadSizeExceededException;
import org.springframework.web.servlet.NoHandlerFoundException;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Slf4j
@RestControllerAdvice
@RequiredArgsConstructor
public class GlobalExceptionHandler {

    private final Tracer tracer;

    // ==================== Custom Exceptions ====================

    @ExceptionHandler(ResourceNotFoundException.class)
    public ResponseEntity<ErrorResponse> handleResourceNotFound(
            ResourceNotFoundException ex, HttpServletRequest request) {
        log.warn("Resource not found: {}", ex.getMessage());

        return buildResponse(HttpStatus.NOT_FOUND, ex.getErrorCode(),
            ex.getMessage(), request, null);
    }

    @ExceptionHandler(BusinessException.class)
    public ResponseEntity<ErrorResponse> handleBusinessException(
            BusinessException ex, HttpServletRequest request) {
        log.warn("Business rule violation: {}", ex.getMessage());

        return buildResponse(HttpStatus.UNPROCESSABLE_ENTITY, ex.getErrorCode(),
            ex.getMessage(), request, null);
    }

    @ExceptionHandler(ValidationException.class)
    public ResponseEntity<ErrorResponse> handleValidationException(
            ValidationException ex, HttpServletRequest request) {
        log.warn("Validation error: {}", ex.getMessage());

        return buildResponse(HttpStatus.BAD_REQUEST, ex.getErrorCode(),
            ex.getMessage(), request, ex.getFieldErrors());
    }

    @ExceptionHandler(ConflictException.class)
    public ResponseEntity<ErrorResponse> handleConflictException(
            ConflictException ex, HttpServletRequest request) {
        log.warn("Conflict: {}", ex.getMessage());

        return buildResponse(HttpStatus.CONFLICT, ex.getErrorCode(),
            ex.getMessage(), request, null);
    }

    @ExceptionHandler(UnauthorizedException.class)
    public ResponseEntity<ErrorResponse> handleUnauthorizedException(
            UnauthorizedException ex, HttpServletRequest request) {
        log.warn("Unauthorized: {}", ex.getMessage());

        return buildResponse(HttpStatus.UNAUTHORIZED, ex.getErrorCode(),
            ex.getMessage(), request, null);
    }

    @ExceptionHandler(ForbiddenException.class)
    public ResponseEntity<ErrorResponse> handleForbiddenException(
            ForbiddenException ex, HttpServletRequest request) {
        log.warn("Forbidden: {}", ex.getMessage());

        return buildResponse(HttpStatus.FORBIDDEN, ex.getErrorCode(),
            ex.getMessage(), request, null);
    }

    // ==================== Spring Validation ====================

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> handleMethodArgumentNotValid(
            MethodArgumentNotValidException ex, HttpServletRequest request) {

        Map<String, List<String>> fieldErrors = ex.getBindingResult()
            .getFieldErrors()
            .stream()
            .collect(Collectors.groupingBy(
                fe -> fe.getField(),
                Collectors.mapping(
                    fe -> fe.getDefaultMessage(),
                    Collectors.toList()
                )
            ));

        log.warn("Validation failed: {}", fieldErrors);

        return buildResponse(HttpStatus.BAD_REQUEST, "VALIDATION_ERROR",
            "Validation failed", request, fieldErrors);
    }

    @ExceptionHandler(ConstraintViolationException.class)
    public ResponseEntity<ErrorResponse> handleConstraintViolation(
            ConstraintViolationException ex, HttpServletRequest request) {

        Map<String, List<String>> fieldErrors = ex.getConstraintViolations()
            .stream()
            .collect(Collectors.groupingBy(
                cv -> getPropertyName(cv.getPropertyPath().toString()),
                Collectors.mapping(
                    cv -> cv.getMessage(),
                    Collectors.toList()
                )
            ));

        log.warn("Constraint violation: {}", fieldErrors);

        return buildResponse(HttpStatus.BAD_REQUEST, "CONSTRAINT_VIOLATION",
            "Constraint violation", request, fieldErrors);
    }

    // ==================== Security Exceptions ====================

    @ExceptionHandler(AuthenticationException.class)
    public ResponseEntity<ErrorResponse> handleAuthenticationException(
            AuthenticationException ex, HttpServletRequest request) {
        log.warn("Authentication failed: {}", ex.getMessage());

        return buildResponse(HttpStatus.UNAUTHORIZED, "AUTHENTICATION_FAILED",
            "Authentication failed", request, null);
    }

    @ExceptionHandler(BadCredentialsException.class)
    public ResponseEntity<ErrorResponse> handleBadCredentials(
            BadCredentialsException ex, HttpServletRequest request) {
        log.warn("Bad credentials");

        return buildResponse(HttpStatus.UNAUTHORIZED, "INVALID_CREDENTIALS",
            "Invalid email or password", request, null);
    }

    @ExceptionHandler(AccessDeniedException.class)
    public ResponseEntity<ErrorResponse> handleAccessDenied(
            AccessDeniedException ex, HttpServletRequest request) {
        log.warn("Access denied: {}", ex.getMessage());

        return buildResponse(HttpStatus.FORBIDDEN, "ACCESS_DENIED",
            "Access denied", request, null);
    }

    // ==================== Data Exceptions ====================

    @ExceptionHandler(DataIntegrityViolationException.class)
    public ResponseEntity<ErrorResponse> handleDataIntegrityViolation(
            DataIntegrityViolationException ex, HttpServletRequest request) {
        log.error("Data integrity violation", ex);

        String message = "Data integrity violation";
        String code = "DATA_INTEGRITY_ERROR";

        // Parse specific constraint violations
        String exMessage = ex.getMostSpecificCause().getMessage();
        if (exMessage != null) {
            if (exMessage.contains("unique constraint") || exMessage.contains("duplicate key")) {
                message = "A record with this value already exists";
                code = "DUPLICATE_ENTRY";
            } else if (exMessage.contains("foreign key constraint")) {
                message = "Cannot delete record - it is referenced by other records";
                code = "FOREIGN_KEY_VIOLATION";
            }
        }

        return buildResponse(HttpStatus.CONFLICT, code, message, request, null);
    }

    @ExceptionHandler(OptimisticLockingFailureException.class)
    public ResponseEntity<ErrorResponse> handleOptimisticLocking(
            OptimisticLockingFailureException ex, HttpServletRequest request) {
        log.warn("Optimistic locking failure", ex);

        return buildResponse(HttpStatus.CONFLICT, "OPTIMISTIC_LOCK_ERROR",
            "Record was modified by another user. Please refresh and try again.",
            request, null);
    }

    // ==================== Request Exceptions ====================

    @ExceptionHandler(HttpMessageNotReadableException.class)
    public ResponseEntity<ErrorResponse> handleHttpMessageNotReadable(
            HttpMessageNotReadableException ex, HttpServletRequest request) {
        log.warn("Malformed request body: {}", ex.getMessage());

        return buildResponse(HttpStatus.BAD_REQUEST, "MALFORMED_REQUEST",
            "Malformed JSON request body", request, null);
    }

    @ExceptionHandler(MissingServletRequestParameterException.class)
    public ResponseEntity<ErrorResponse> handleMissingParameter(
            MissingServletRequestParameterException ex, HttpServletRequest request) {

        String message = String.format("Required parameter '%s' is missing",
            ex.getParameterName());

        return buildResponse(HttpStatus.BAD_REQUEST, "MISSING_PARAMETER",
            message, request, null);
    }

    @ExceptionHandler(MethodArgumentTypeMismatchException.class)
    public ResponseEntity<ErrorResponse> handleTypeMismatch(
            MethodArgumentTypeMismatchException ex, HttpServletRequest request) {

        String message = String.format("Parameter '%s' must be of type %s",
            ex.getName(), ex.getRequiredType().getSimpleName());

        return buildResponse(HttpStatus.BAD_REQUEST, "TYPE_MISMATCH",
            message, request, null);
    }

    @ExceptionHandler(HttpRequestMethodNotSupportedException.class)
    public ResponseEntity<ErrorResponse> handleMethodNotSupported(
            HttpRequestMethodNotSupportedException ex, HttpServletRequest request) {

        String message = String.format("Method '%s' is not supported for this endpoint",
            ex.getMethod());

        return buildResponse(HttpStatus.METHOD_NOT_ALLOWED, "METHOD_NOT_ALLOWED",
            message, request, null);
    }

    @ExceptionHandler(HttpMediaTypeNotSupportedException.class)
    public ResponseEntity<ErrorResponse> handleMediaTypeNotSupported(
            HttpMediaTypeNotSupportedException ex, HttpServletRequest request) {

        return buildResponse(HttpStatus.UNSUPPORTED_MEDIA_TYPE, "UNSUPPORTED_MEDIA_TYPE",
            "Unsupported media type: " + ex.getContentType(), request, null);
    }

    @ExceptionHandler(NoHandlerFoundException.class)
    public ResponseEntity<ErrorResponse> handleNoHandlerFound(
            NoHandlerFoundException ex, HttpServletRequest request) {

        return buildResponse(HttpStatus.NOT_FOUND, "ENDPOINT_NOT_FOUND",
            "Endpoint not found: " + ex.getRequestURL(), request, null);
    }

    @ExceptionHandler(MaxUploadSizeExceededException.class)
    public ResponseEntity<ErrorResponse> handleMaxUploadSize(
            MaxUploadSizeExceededException ex, HttpServletRequest request) {

        return buildResponse(HttpStatus.PAYLOAD_TOO_LARGE, "FILE_TOO_LARGE",
            "File size exceeds maximum allowed size", request, null);
    }

    // ==================== Generic Exception ====================

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleGenericException(
            Exception ex, HttpServletRequest request) {
        log.error("Unexpected error occurred", ex);

        return buildResponse(HttpStatus.INTERNAL_SERVER_ERROR, "INTERNAL_ERROR",
            "An unexpected error occurred", request, null);
    }

    // ==================== Helper Methods ====================

    private ResponseEntity<ErrorResponse> buildResponse(
            HttpStatus status,
            String code,
            String message,
            HttpServletRequest request,
            Map<String, List<String>> fieldErrors) {

        ErrorResponse error = ErrorResponse.builder()
            .code(code)
            .message(message)
            .path(request.getRequestURI())
            .fieldErrors(fieldErrors)
            .traceId(getTraceId())
            .build();

        return ResponseEntity.status(status).body(error);
    }

    private String getTraceId() {
        if (tracer != null && tracer.currentSpan() != null) {
            return tracer.currentSpan().context().traceId();
        }
        return null;
    }

    private String getPropertyName(String path) {
        int lastDot = path.lastIndexOf('.');
        return lastDot > 0 ? path.substring(lastDot + 1) : path;
    }
}
```

## Exception Logging

```java
@Aspect
@Component
@Slf4j
public class ExceptionLoggingAspect {

    @AfterThrowing(
        pointcut = "within(com.example.app.service..*) || within(com.example.app.web..*)",
        throwing = "ex")
    public void logException(JoinPoint joinPoint, Exception ex) {
        String className = joinPoint.getTarget().getClass().getSimpleName();
        String methodName = joinPoint.getSignature().getName();

        if (ex instanceof BaseException) {
            // Business exceptions - log at warn level
            log.warn("Business exception in {}.{}: {} - {}",
                className, methodName,
                ((BaseException) ex).getErrorCode(),
                ex.getMessage());
        } else {
            // Unexpected exceptions - log at error level with stack trace
            log.error("Unexpected exception in {}.{}: {}",
                className, methodName, ex.getMessage(), ex);
        }
    }
}
```

## Service Layer Exception Usage

```java
@Service
@RequiredArgsConstructor
@Transactional
public class OrderService {

    private final OrderRepository orderRepository;
    private final ProductRepository productRepository;
    private final UserRepository userRepository;

    public OrderResponse createOrder(UUID userId, CreateOrderRequest request) {
        // Validate user exists
        User user = userRepository.findById(userId)
            .orElseThrow(() -> ResourceNotFoundException.user(userId));

        // Validate products and check stock
        List<OrderItem> items = new ArrayList<>();
        for (OrderItemRequest itemRequest : request.items()) {
            Product product = productRepository.findById(itemRequest.productId())
                .orElseThrow(() -> ResourceNotFoundException.product(itemRequest.productId()));

            if (product.getStock() < itemRequest.quantity()) {
                throw BusinessException.insufficientStock(
                    product.getName(),
                    product.getStock(),
                    itemRequest.quantity()
                );
            }

            items.add(createOrderItem(product, itemRequest.quantity()));
        }

        // Create order
        Order order = Order.builder()
            .user(user)
            .items(items)
            .status(OrderStatus.PENDING)
            .build();

        return mapToResponse(orderRepository.save(order));
    }

    public OrderResponse updateOrderStatus(UUID orderId, OrderStatus newStatus) {
        Order order = orderRepository.findById(orderId)
            .orElseThrow(() -> ResourceNotFoundException.order(orderId));

        // Business rule validation
        if (order.getStatus() == OrderStatus.SHIPPED) {
            throw BusinessException.orderAlreadyShipped(orderId);
        }

        if (!isValidStatusTransition(order.getStatus(), newStatus)) {
            throw new BusinessException("INVALID_STATUS_TRANSITION",
                String.format("Cannot transition from %s to %s",
                    order.getStatus(), newStatus));
        }

        order.setStatus(newStatus);
        return mapToResponse(orderRepository.save(order));
    }

    public void cancelOrder(UUID orderId, UUID userId) {
        Order order = orderRepository.findById(orderId)
            .orElseThrow(() -> ResourceNotFoundException.order(orderId));

        // Authorization check
        if (!order.getUser().getId().equals(userId)) {
            throw ForbiddenException.resourceOwnerOnly();
        }

        // Business rule
        if (order.getStatus() == OrderStatus.SHIPPED) {
            throw BusinessException.orderAlreadyShipped(orderId);
        }

        order.setStatus(OrderStatus.CANCELLED);
        orderRepository.save(order);
    }
}
```

## Testing Exception Handling

```java
@WebMvcTest(ProductController.class)
class ProductControllerExceptionTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private ProductService productService;

    @Test
    void shouldReturn404WhenProductNotFound() throws Exception {
        UUID productId = UUID.randomUUID();
        when(productService.findById(productId))
            .thenThrow(ResourceNotFoundException.product(productId));

        mockMvc.perform(get("/api/v1/products/{id}", productId))
            .andExpect(status().isNotFound())
            .andExpect(jsonPath("$.code").value("RESOURCE_NOT_FOUND"))
            .andExpect(jsonPath("$.message").value("Product not found with id: " + productId))
            .andExpect(jsonPath("$.timestamp").exists());
    }

    @Test
    void shouldReturn422WhenBusinessRuleViolated() throws Exception {
        when(productService.create(any()))
            .thenThrow(BusinessException.duplicateEmail("test@example.com"));

        mockMvc.perform(post("/api/v1/products")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"name\":\"Test\",\"sku\":\"TST-0001\",\"price\":10.00}"))
            .andExpect(status().isUnprocessableEntity())
            .andExpect(jsonPath("$.code").value("DUPLICATE_EMAIL"));
    }

    @Test
    void shouldReturn400ForValidationErrors() throws Exception {
        mockMvc.perform(post("/api/v1/products")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"name\":\"\",\"price\":-1}"))
            .andExpect(status().isBadRequest())
            .andExpect(jsonPath("$.code").value("VALIDATION_ERROR"))
            .andExpect(jsonPath("$.fieldErrors.name").exists())
            .andExpect(jsonPath("$.fieldErrors.price").exists());
    }
}
```

## Best Practices

1. **Use specific exceptions** - Create domain-specific exceptions
2. **Log appropriately** - Warn for business, error for unexpected
3. **Include trace ID** - For distributed tracing correlation
4. **Consistent response format** - Same structure across all errors
5. **Don't expose internals** - Generic message for 500 errors
6. **Validate early** - Fail fast with clear messages
7. **Use factory methods** - For common exception scenarios
8. **Test exception paths** - Verify error responses in tests
