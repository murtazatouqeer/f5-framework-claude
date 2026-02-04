# Custom Validators

Creating custom validation annotations and validators for Spring Boot applications.

## Basic Custom Validator

### Annotation Definition

```java
package com.example.app.validation;

import jakarta.validation.Constraint;
import jakarta.validation.Payload;
import java.lang.annotation.*;

@Documented
@Constraint(validatedBy = UniqueEmailValidator.class)
@Target({ElementType.FIELD, ElementType.PARAMETER})
@Retention(RetentionPolicy.RUNTIME)
public @interface UniqueEmail {
    String message() default "Email already exists";
    Class<?>[] groups() default {};
    Class<? extends Payload>[] payload() default {};
}
```

### Validator Implementation

```java
package com.example.app.validation;

import com.example.app.repository.UserRepository;
import jakarta.validation.ConstraintValidator;
import jakarta.validation.ConstraintValidatorContext;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
public class UniqueEmailValidator implements ConstraintValidator<UniqueEmail, String> {

    private final UserRepository userRepository;

    @Override
    public void initialize(UniqueEmail constraintAnnotation) {
        // Initialization if needed
    }

    @Override
    public boolean isValid(String email, ConstraintValidatorContext context) {
        if (email == null || email.isBlank()) {
            return true; // Let @NotBlank handle null/empty
        }
        return !userRepository.existsByEmailIgnoreCase(email);
    }
}
```

### Usage

```java
public record RegistrationRequest(
    @NotBlank
    @Email
    @UniqueEmail
    String email,

    @NotBlank
    @Size(min = 8)
    String password
) {}
```

## Update-Aware Unique Validator

```java
// Annotation
@Documented
@Constraint(validatedBy = UniqueEmailExceptCurrentValidator.class)
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
public @interface UniqueEmailExceptCurrent {
    String message() default "Email already exists";
    Class<?>[] groups() default {};
    Class<? extends Payload>[] payload() default {};
    String idField() default "id";
    String emailField() default "email";
}

// Validator
@Component
@RequiredArgsConstructor
public class UniqueEmailExceptCurrentValidator
        implements ConstraintValidator<UniqueEmailExceptCurrent, Object> {

    private final UserRepository userRepository;
    private String idField;
    private String emailField;

    @Override
    public void initialize(UniqueEmailExceptCurrent annotation) {
        this.idField = annotation.idField();
        this.emailField = annotation.emailField();
    }

    @Override
    public boolean isValid(Object value, ConstraintValidatorContext context) {
        try {
            UUID id = (UUID) getFieldValue(value, idField);
            String email = (String) getFieldValue(value, emailField);

            if (email == null || email.isBlank()) {
                return true;
            }

            Optional<User> existing = userRepository.findByEmailIgnoreCase(email);
            if (existing.isEmpty()) {
                return true;
            }

            // Allow if updating same user
            return existing.get().getId().equals(id);

        } catch (Exception e) {
            return false;
        }
    }

    private Object getFieldValue(Object object, String fieldName) throws Exception {
        var field = object.getClass().getDeclaredField(fieldName);
        field.setAccessible(true);
        return field.get(object);
    }
}

// Usage
@UniqueEmailExceptCurrent
public record UserUpdateRequest(
    UUID id,
    String email,
    String name
) {}
```

## Cross-Field Validation

### Date Range Validation

```java
// Annotation
@Documented
@Constraint(validatedBy = ValidDateRangeValidator.class)
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
public @interface ValidDateRange {
    String message() default "End date must be after start date";
    Class<?>[] groups() default {};
    Class<? extends Payload>[] payload() default {};
    String startDate();
    String endDate();
}

// Validator
public class ValidDateRangeValidator
        implements ConstraintValidator<ValidDateRange, Object> {

    private String startDateField;
    private String endDateField;

    @Override
    public void initialize(ValidDateRange annotation) {
        this.startDateField = annotation.startDate();
        this.endDateField = annotation.endDate();
    }

    @Override
    public boolean isValid(Object value, ConstraintValidatorContext context) {
        try {
            LocalDate startDate = (LocalDate) getFieldValue(value, startDateField);
            LocalDate endDate = (LocalDate) getFieldValue(value, endDateField);

            if (startDate == null || endDate == null) {
                return true; // Let @NotNull handle nulls
            }

            boolean valid = !endDate.isBefore(startDate);

            if (!valid) {
                context.disableDefaultConstraintViolation();
                context.buildConstraintViolationWithTemplate(context.getDefaultConstraintMessageTemplate())
                    .addPropertyNode(endDateField)
                    .addConstraintViolation();
            }

            return valid;

        } catch (Exception e) {
            return false;
        }
    }

    private Object getFieldValue(Object object, String fieldName) throws Exception {
        var field = object.getClass().getDeclaredField(fieldName);
        field.setAccessible(true);
        return field.get(object);
    }
}

// Usage
@ValidDateRange(startDate = "startDate", endDate = "endDate")
public record EventRequest(
    @NotBlank String name,
    @NotNull LocalDate startDate,
    @NotNull LocalDate endDate
) {}
```

### Password Confirmation

```java
// Annotation
@Documented
@Constraint(validatedBy = PasswordMatchValidator.class)
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
public @interface PasswordMatch {
    String message() default "Passwords do not match";
    Class<?>[] groups() default {};
    Class<? extends Payload>[] payload() default {};
    String password();
    String confirmPassword();
}

// Validator
public class PasswordMatchValidator
        implements ConstraintValidator<PasswordMatch, Object> {

    private String passwordField;
    private String confirmField;

    @Override
    public void initialize(PasswordMatch annotation) {
        this.passwordField = annotation.password();
        this.confirmField = annotation.confirmPassword();
    }

    @Override
    public boolean isValid(Object value, ConstraintValidatorContext context) {
        try {
            String password = (String) getFieldValue(value, passwordField);
            String confirm = (String) getFieldValue(value, confirmField);

            if (password == null && confirm == null) {
                return true;
            }

            boolean valid = password != null && password.equals(confirm);

            if (!valid) {
                context.disableDefaultConstraintViolation();
                context.buildConstraintViolationWithTemplate(context.getDefaultConstraintMessageTemplate())
                    .addPropertyNode(confirmField)
                    .addConstraintViolation();
            }

            return valid;

        } catch (Exception e) {
            return false;
        }
    }
}

// Usage
@PasswordMatch(password = "password", confirmPassword = "confirmPassword")
public record RegistrationRequest(
    @NotBlank @Email String email,
    @NotBlank @Size(min = 8) String password,
    @NotBlank String confirmPassword
) {}
```

## Complex Business Rule Validation

### Order Total Validation

```java
// Annotation
@Documented
@Constraint(validatedBy = ValidOrderTotalValidator.class)
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
public @interface ValidOrderTotal {
    String message() default "Order total does not match sum of items";
    Class<?>[] groups() default {};
    Class<? extends Payload>[] payload() default {};
    String tolerance() default "0.01";
}

// Validator
public class ValidOrderTotalValidator
        implements ConstraintValidator<ValidOrderTotal, Object> {

    private BigDecimal tolerance;

    @Override
    public void initialize(ValidOrderTotal annotation) {
        this.tolerance = new BigDecimal(annotation.tolerance());
    }

    @Override
    public boolean isValid(Object value, ConstraintValidatorContext context) {
        try {
            if (!(value instanceof OrderRequest order)) {
                return true;
            }

            if (order.items() == null || order.items().isEmpty()) {
                return true;
            }

            BigDecimal calculatedTotal = order.items().stream()
                .map(item -> item.unitPrice().multiply(BigDecimal.valueOf(item.quantity())))
                .reduce(BigDecimal.ZERO, BigDecimal::add);

            BigDecimal providedTotal = order.total();
            if (providedTotal == null) {
                return true;
            }

            BigDecimal difference = calculatedTotal.subtract(providedTotal).abs();
            return difference.compareTo(tolerance) <= 0;

        } catch (Exception e) {
            return false;
        }
    }
}
```

### Inventory Availability Validation

```java
// Annotation
@Documented
@Constraint(validatedBy = SufficientInventoryValidator.class)
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
public @interface SufficientInventory {
    String message() default "Insufficient inventory for one or more items";
    Class<?>[] groups() default {};
    Class<? extends Payload>[] payload() default {};
}

// Validator
@Component
@RequiredArgsConstructor
public class SufficientInventoryValidator
        implements ConstraintValidator<SufficientInventory, OrderRequest> {

    private final ProductRepository productRepository;

    @Override
    public boolean isValid(OrderRequest order, ConstraintValidatorContext context) {
        if (order == null || order.items() == null) {
            return true;
        }

        List<String> insufficientItems = new ArrayList<>();

        for (OrderItemRequest item : order.items()) {
            Product product = productRepository.findById(item.productId()).orElse(null);
            if (product == null) {
                insufficientItems.add("Product " + item.productId() + " not found");
                continue;
            }

            if (product.getStock() < item.quantity()) {
                insufficientItems.add(
                    "Product " + product.getName() +
                    " has only " + product.getStock() +
                    " items (requested: " + item.quantity() + ")"
                );
            }
        }

        if (!insufficientItems.isEmpty()) {
            context.disableDefaultConstraintViolation();
            for (String message : insufficientItems) {
                context.buildConstraintViolationWithTemplate(message)
                    .addPropertyNode("items")
                    .addConstraintViolation();
            }
            return false;
        }

        return true;
    }
}
```

## Conditional Validation

### Validate If Field Present

```java
// Annotation
@Documented
@Constraint(validatedBy = RequiredIfValidator.class)
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
@Repeatable(RequiredIf.List.class)
public @interface RequiredIf {
    String message() default "{field} is required when {condition}";
    Class<?>[] groups() default {};
    Class<? extends Payload>[] payload() default {};

    String field();
    String conditionField();
    String conditionValue();

    @Target(ElementType.TYPE)
    @Retention(RetentionPolicy.RUNTIME)
    @Documented
    @interface List {
        RequiredIf[] value();
    }
}

// Validator
public class RequiredIfValidator
        implements ConstraintValidator<RequiredIf, Object> {

    private String field;
    private String conditionField;
    private String conditionValue;

    @Override
    public void initialize(RequiredIf annotation) {
        this.field = annotation.field();
        this.conditionField = annotation.conditionField();
        this.conditionValue = annotation.conditionValue();
    }

    @Override
    public boolean isValid(Object value, ConstraintValidatorContext context) {
        try {
            Object conditionFieldValue = getFieldValue(value, conditionField);
            Object fieldValue = getFieldValue(value, field);

            // Check if condition is met
            boolean conditionMet = conditionValue.equals(String.valueOf(conditionFieldValue));

            if (conditionMet) {
                boolean valid = fieldValue != null &&
                    (!(fieldValue instanceof String) || !((String) fieldValue).isBlank());

                if (!valid) {
                    context.disableDefaultConstraintViolation();
                    context.buildConstraintViolationWithTemplate(
                            field + " is required when " + conditionField + " is " + conditionValue)
                        .addPropertyNode(field)
                        .addConstraintViolation();
                }
                return valid;
            }

            return true;

        } catch (Exception e) {
            return false;
        }
    }
}

// Usage
@RequiredIf(field = "companyName", conditionField = "accountType", conditionValue = "BUSINESS")
@RequiredIf(field = "taxId", conditionField = "accountType", conditionValue = "BUSINESS")
public record AccountRequest(
    @NotBlank String email,
    @NotNull AccountType accountType,
    String companyName,  // Required for BUSINESS
    String taxId         // Required for BUSINESS
) {}
```

## Enum Validation

```java
// Annotation
@Documented
@Constraint(validatedBy = ValidEnumValidator.class)
@Target({ElementType.FIELD, ElementType.PARAMETER})
@Retention(RetentionPolicy.RUNTIME)
public @interface ValidEnum {
    String message() default "Invalid value. Must be one of: {values}";
    Class<?>[] groups() default {};
    Class<? extends Payload>[] payload() default {};
    Class<? extends Enum<?>> enumClass();
    boolean ignoreCase() default true;
}

// Validator
public class ValidEnumValidator implements ConstraintValidator<ValidEnum, String> {

    private Set<String> validValues;
    private boolean ignoreCase;

    @Override
    public void initialize(ValidEnum annotation) {
        this.ignoreCase = annotation.ignoreCase();
        this.validValues = Arrays.stream(annotation.enumClass().getEnumConstants())
            .map(e -> ignoreCase ? e.name().toUpperCase() : e.name())
            .collect(Collectors.toSet());
    }

    @Override
    public boolean isValid(String value, ConstraintValidatorContext context) {
        if (value == null) {
            return true;
        }

        String checkValue = ignoreCase ? value.toUpperCase() : value;
        boolean valid = validValues.contains(checkValue);

        if (!valid) {
            context.disableDefaultConstraintViolation();
            context.buildConstraintViolationWithTemplate(
                    "Invalid value '" + value + "'. Must be one of: " + String.join(", ", validValues))
                .addConstraintViolation();
        }

        return valid;
    }
}

// Usage
public record ProductRequest(
    @NotBlank String name,

    @ValidEnum(enumClass = ProductStatus.class)
    String status,

    @ValidEnum(enumClass = ProductCategory.class, ignoreCase = false)
    String category
) {}
```

## Collection Element Validation

```java
// Annotation
@Documented
@Constraint(validatedBy = UniqueElementsValidator.class)
@Target({ElementType.FIELD, ElementType.PARAMETER})
@Retention(RetentionPolicy.RUNTIME)
public @interface UniqueElements {
    String message() default "Collection contains duplicate elements";
    Class<?>[] groups() default {};
    Class<? extends Payload>[] payload() default {};
    String property() default "";  // Property to check for uniqueness
}

// Validator
public class UniqueElementsValidator
        implements ConstraintValidator<UniqueElements, Collection<?>> {

    private String property;

    @Override
    public void initialize(UniqueElements annotation) {
        this.property = annotation.property();
    }

    @Override
    public boolean isValid(Collection<?> collection, ConstraintValidatorContext context) {
        if (collection == null || collection.isEmpty()) {
            return true;
        }

        Set<Object> seen = new HashSet<>();
        List<Integer> duplicateIndices = new ArrayList<>();

        int index = 0;
        for (Object element : collection) {
            Object valueToCheck = property.isEmpty() ?
                element : getPropertyValue(element, property);

            if (valueToCheck != null && !seen.add(valueToCheck)) {
                duplicateIndices.add(index);
            }
            index++;
        }

        if (!duplicateIndices.isEmpty()) {
            context.disableDefaultConstraintViolation();
            for (Integer duplicateIndex : duplicateIndices) {
                context.buildConstraintViolationWithTemplate(
                        "Duplicate element at index " + duplicateIndex)
                    .addBeanNode()
                    .inIterable()
                    .atIndex(duplicateIndex)
                    .addConstraintViolation();
            }
            return false;
        }

        return true;
    }

    private Object getPropertyValue(Object object, String propertyName) {
        try {
            var field = object.getClass().getDeclaredField(propertyName);
            field.setAccessible(true);
            return field.get(object);
        } catch (Exception e) {
            return null;
        }
    }
}

// Usage
public record BatchCreateRequest(
    @NotEmpty
    @UniqueElements(property = "sku")
    List<@Valid ProductRequest> products,

    @UniqueElements  // Simple collection
    Set<String> tags
) {}
```

## File Validation

```java
// Annotation
@Documented
@Constraint(validatedBy = ValidFileValidator.class)
@Target({ElementType.FIELD, ElementType.PARAMETER})
@Retention(RetentionPolicy.RUNTIME)
public @interface ValidFile {
    String message() default "Invalid file";
    Class<?>[] groups() default {};
    Class<? extends Payload>[] payload() default {};
    String[] allowedExtensions() default {};
    String[] allowedMimeTypes() default {};
    long maxSizeBytes() default 10 * 1024 * 1024; // 10MB default
}

// Validator
public class ValidFileValidator
        implements ConstraintValidator<ValidFile, MultipartFile> {

    private Set<String> allowedExtensions;
    private Set<String> allowedMimeTypes;
    private long maxSizeBytes;

    @Override
    public void initialize(ValidFile annotation) {
        this.allowedExtensions = Set.of(annotation.allowedExtensions());
        this.allowedMimeTypes = Set.of(annotation.allowedMimeTypes());
        this.maxSizeBytes = annotation.maxSizeBytes();
    }

    @Override
    public boolean isValid(MultipartFile file, ConstraintValidatorContext context) {
        if (file == null || file.isEmpty()) {
            return true;
        }

        List<String> errors = new ArrayList<>();

        // Check size
        if (file.getSize() > maxSizeBytes) {
            errors.add("File size exceeds maximum of " + (maxSizeBytes / 1024 / 1024) + "MB");
        }

        // Check extension
        String originalFilename = file.getOriginalFilename();
        if (originalFilename != null && !allowedExtensions.isEmpty()) {
            String extension = getExtension(originalFilename);
            if (!allowedExtensions.contains(extension.toLowerCase())) {
                errors.add("File extension '" + extension + "' not allowed. " +
                          "Allowed: " + String.join(", ", allowedExtensions));
            }
        }

        // Check MIME type
        if (!allowedMimeTypes.isEmpty() && file.getContentType() != null) {
            if (!allowedMimeTypes.contains(file.getContentType())) {
                errors.add("File type '" + file.getContentType() + "' not allowed");
            }
        }

        if (!errors.isEmpty()) {
            context.disableDefaultConstraintViolation();
            for (String error : errors) {
                context.buildConstraintViolationWithTemplate(error)
                    .addConstraintViolation();
            }
            return false;
        }

        return true;
    }

    private String getExtension(String filename) {
        int lastDot = filename.lastIndexOf('.');
        return lastDot > 0 ? filename.substring(lastDot + 1) : "";
    }
}

// Usage
@PostMapping("/upload")
public ResponseEntity<FileResponse> uploadFile(
        @RequestParam("file")
        @ValidFile(
            allowedExtensions = {"jpg", "jpeg", "png", "pdf"},
            allowedMimeTypes = {"image/jpeg", "image/png", "application/pdf"},
            maxSizeBytes = 5 * 1024 * 1024
        )
        MultipartFile file) {
    return ResponseEntity.ok(fileService.upload(file));
}
```

## Composing Validators

```java
// Composed annotation combining multiple constraints
@NotBlank
@Size(min = 3, max = 50)
@Pattern(regexp = "^[a-zA-Z0-9_]+$")
@Target({ElementType.FIELD, ElementType.PARAMETER})
@Retention(RetentionPolicy.RUNTIME)
@Constraint(validatedBy = {})  // No dedicated validator
@Documented
public @interface ValidUsername {
    String message() default "Invalid username";
    Class<?>[] groups() default {};
    Class<? extends Payload>[] payload() default {};
}

// Usage
public record UserRequest(
    @ValidUsername
    String username,

    @Email
    @NotBlank
    String email
) {}
```

## Testing Custom Validators

```java
@ExtendWith(MockitoExtension.class)
class UniqueEmailValidatorTest {

    @Mock
    private UserRepository userRepository;

    @InjectMocks
    private UniqueEmailValidator validator;

    private ConstraintValidatorContext context;

    @BeforeEach
    void setUp() {
        context = mock(ConstraintValidatorContext.class);
        ConstraintValidatorContext.ConstraintViolationBuilder builder =
            mock(ConstraintValidatorContext.ConstraintViolationBuilder.class);
        when(context.buildConstraintViolationWithTemplate(anyString())).thenReturn(builder);
    }

    @Test
    void shouldReturnTrueForUniqueEmail() {
        when(userRepository.existsByEmailIgnoreCase("new@example.com")).thenReturn(false);

        boolean result = validator.isValid("new@example.com", context);

        assertThat(result).isTrue();
    }

    @Test
    void shouldReturnFalseForExistingEmail() {
        when(userRepository.existsByEmailIgnoreCase("existing@example.com")).thenReturn(true);

        boolean result = validator.isValid("existing@example.com", context);

        assertThat(result).isFalse();
    }

    @Test
    void shouldReturnTrueForNullEmail() {
        boolean result = validator.isValid(null, context);

        assertThat(result).isTrue();
        verifyNoInteractions(userRepository);
    }

    @Test
    void shouldReturnTrueForBlankEmail() {
        boolean result = validator.isValid("", context);

        assertThat(result).isTrue();
        verifyNoInteractions(userRepository);
    }
}
```

## Best Practices

1. **Handle null properly** - Return true for null, let @NotNull handle it
2. **Use clear error messages** - Include field names and allowed values
3. **Add property nodes** - For cross-field validation error location
4. **Inject dependencies** - Use @Component for database access
5. **Compose constraints** - Create meta-annotations for common patterns
6. **Test thoroughly** - Cover all validation scenarios
7. **Document constraints** - Explain validation rules in annotation docs
8. **Keep validators focused** - One validation rule per validator
