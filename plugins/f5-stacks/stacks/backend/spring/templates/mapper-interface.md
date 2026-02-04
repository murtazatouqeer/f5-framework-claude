# Mapper Interface Template

MapStruct mapper template for Spring Boot with entity-DTO conversion.

## Template

```java
package {{package}}.mapper;

import {{package}}.domain.entity.{{Entity}};
import {{package}}.domain.entity.{{Entity}}Status;
import {{package}}.web.dto.{{Entity}}Request;
import {{package}}.web.dto.{{Entity}}Response;
import {{package}}.web.dto.{{Entity}}PatchRequest;
import {{package}}.web.dto.{{Entity}}StatusDto;
import {{package}}.web.dto.{{Entity}}ListItem;
import org.mapstruct.*;

import java.util.List;

@Mapper(
    componentModel = "spring",
    unmappedTargetPolicy = ReportingPolicy.IGNORE,
    nullValuePropertyMappingStrategy = NullValuePropertyMappingStrategy.IGNORE,
    injectionStrategy = InjectionStrategy.CONSTRUCTOR
)
public interface {{Entity}}Mapper {

    // ==================== Entity to Response ====================

    @Mapping(target = "category", source = "category")
    @Mapping(target = "status", source = "status", qualifiedByName = "statusToDto")
    {{Entity}}Response toResponse({{Entity}} entity);

    List<{{Entity}}Response> toResponseList(List<{{Entity}}> entities);

    // ==================== Request to Entity ====================

    @Mapping(target = "id", ignore = true)
    @Mapping(target = "category", ignore = true) // Set separately
    @Mapping(target = "items", ignore = true)    // Set separately
    @Mapping(target = "status", source = "status", qualifiedByName = "dtoToStatus")
    @Mapping(target = "createdAt", ignore = true)
    @Mapping(target = "updatedAt", ignore = true)
    @Mapping(target = "createdBy", ignore = true)
    @Mapping(target = "updatedBy", ignore = true)
    @Mapping(target = "deleted", ignore = true)
    @Mapping(target = "deletedAt", ignore = true)
    @Mapping(target = "version", ignore = true)
    {{Entity}} toEntity({{Entity}}Request request);

    // ==================== Update Entity ====================

    @Mapping(target = "id", ignore = true)
    @Mapping(target = "category", ignore = true)
    @Mapping(target = "items", ignore = true)
    @Mapping(target = "status", source = "status", qualifiedByName = "dtoToStatus")
    @Mapping(target = "createdAt", ignore = true)
    @Mapping(target = "updatedAt", ignore = true)
    @Mapping(target = "createdBy", ignore = true)
    @Mapping(target = "updatedBy", ignore = true)
    @Mapping(target = "deleted", ignore = true)
    @Mapping(target = "deletedAt", ignore = true)
    @Mapping(target = "version", ignore = true)
    void updateEntity(@MappingTarget {{Entity}} entity, {{Entity}}Request request);

    // ==================== Patch Entity ====================

    @BeanMapping(nullValuePropertyMappingStrategy = NullValuePropertyMappingStrategy.IGNORE)
    @Mapping(target = "id", ignore = true)
    @Mapping(target = "createdAt", ignore = true)
    @Mapping(target = "updatedAt", ignore = true)
    @Mapping(target = "createdBy", ignore = true)
    @Mapping(target = "updatedBy", ignore = true)
    @Mapping(target = "deleted", ignore = true)
    @Mapping(target = "deletedAt", ignore = true)
    @Mapping(target = "version", ignore = true)
    void patchEntity(@MappingTarget {{Entity}} entity, {{Entity}}PatchRequest request);

    // ==================== Summary/List ====================

    @Mapping(target = "categoryName", source = "category.name")
    @Mapping(target = "itemCount", expression = "java(entity.getItems().size())")
    @Mapping(target = "totalValue", expression = "java(calculateTotalValue(entity))")
    @Mapping(target = "status", source = "status", qualifiedByName = "statusToDto")
    {{Entity}}ListItem toListItem({{Entity}} entity);

    List<{{Entity}}ListItem> toListItems(List<{{Entity}}> entities);

    // ==================== Status Conversion ====================

    @Named("statusToDto")
    default {{Entity}}StatusDto statusToDto({{Entity}}Status status) {
        if (status == null) return null;
        return switch (status) {
            case DRAFT -> {{Entity}}StatusDto.DRAFT;
            case ACTIVE -> {{Entity}}StatusDto.ACTIVE;
            case INACTIVE -> {{Entity}}StatusDto.INACTIVE;
            case ARCHIVED -> {{Entity}}StatusDto.ARCHIVED;
        };
    }

    @Named("dtoToStatus")
    default {{Entity}}Status dtoToStatus({{Entity}}StatusDto dto) {
        if (dto == null) return null;
        return switch (dto) {
            case DRAFT -> {{Entity}}Status.DRAFT;
            case ACTIVE -> {{Entity}}Status.ACTIVE;
            case INACTIVE -> {{Entity}}Status.INACTIVE;
            case ARCHIVED -> {{Entity}}Status.ARCHIVED;
        };
    }

    // ==================== Helper Methods ====================

    default java.math.BigDecimal calculateTotalValue({{Entity}} entity) {
        // Implement calculation logic
        return java.math.BigDecimal.ZERO;
    }
}
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{package}}` | Base package name | `com.example.app` |
| `{{Entity}}` | Entity name (PascalCase) | `Product` |
| `{{entity}}` | Entity name (camelCase) | `product` |

## Customization Options

### With Nested Mappers

```java
@Mapper(
    componentModel = "spring",
    uses = {CategoryMapper.class, {{Entity}}ItemMapper.class},
    injectionStrategy = InjectionStrategy.CONSTRUCTOR
)
public interface {{Entity}}Mapper {

    @Mapping(target = "category", source = "category")
    @Mapping(target = "items", source = "items")
    {{Entity}}Response toResponse({{Entity}} entity);
}

// Nested mapper
@Mapper(componentModel = "spring")
public interface {{Entity}}ItemMapper {

    @Mapping(target = "productName", source = "product.name")
    @Mapping(target = "totalPrice", expression = "java(item.getQuantity().multiply(item.getUnitPrice()))")
    {{Entity}}ItemResponse toResponse({{Entity}}Item item);

    List<{{Entity}}ItemResponse> toResponseList(List<{{Entity}}Item> items);

    @Mapping(target = "id", ignore = true)
    @Mapping(target = "{{entity}}", ignore = true)
    @Mapping(target = "product", ignore = true)
    {{Entity}}Item toEntity({{Entity}}ItemRequest request);
}
```

### With Custom Qualifiers

```java
@Mapper(componentModel = "spring")
public interface {{Entity}}Mapper {

    @Mapping(target = "formattedPrice", source = "price", qualifiedByName = "formatCurrency")
    @Mapping(target = "createdAt", source = "createdAt", qualifiedByName = "formatDateTime")
    {{Entity}}Response toResponse({{Entity}} entity);

    @Named("formatCurrency")
    default String formatCurrency(java.math.BigDecimal amount) {
        if (amount == null) return null;
        return java.text.NumberFormat.getCurrencyInstance(java.util.Locale.US)
            .format(amount);
    }

    @Named("formatDateTime")
    default String formatDateTime(java.time.Instant instant) {
        if (instant == null) return null;
        return java.time.format.DateTimeFormatter.ISO_INSTANT.format(instant);
    }
}
```

### With Conditional Mapping

```java
@Mapper(componentModel = "spring")
public interface {{Entity}}Mapper {

    @Mapping(target = "sensitiveData", conditionExpression = "java(shouldIncludeSensitiveData())")
    @Mapping(target = "adminNotes", conditionQualifiedByName = "isAdmin")
    {{Entity}}Response toResponse({{Entity}} entity);

    @Condition
    @Named("isAdmin")
    default boolean isAdmin() {
        // Check security context
        var auth = org.springframework.security.core.context.SecurityContextHolder
            .getContext().getAuthentication();
        return auth != null && auth.getAuthorities().stream()
            .anyMatch(a -> a.getAuthority().equals("ROLE_ADMIN"));
    }

    default boolean shouldIncludeSensitiveData() {
        // Custom logic
        return isAdmin();
    }
}
```

### With Before/After Mapping

```java
@Mapper(componentModel = "spring")
public abstract class {{Entity}}Mapper {

    @Autowired
    protected SecurityService securityService;

    @Autowired
    protected {{Entity}}ItemMapper itemMapper;

    @Mapping(target = "category", source = "category")
    @Mapping(target = "items", ignore = true) // Handle in @AfterMapping
    public abstract {{Entity}}Response toResponse({{Entity}} entity);

    @AfterMapping
    protected void afterToResponse({{Entity}} entity, @MappingTarget {{Entity}}Response.Builder response) {
        // Add computed fields
        if (entity.getItems() != null) {
            response.items(itemMapper.toResponseList(entity.getItems()));
        }

        // Add user-specific data
        if (securityService.isAdmin()) {
            response.adminNotes(entity.getAdminNotes());
        }
    }

    @BeforeMapping
    protected void beforeToEntity({{Entity}}Request request) {
        // Validate or transform request before mapping
        if (request.name() != null) {
            // Sanitize input
        }
    }
}
```

### With Expression Mapping

```java
@Mapper(
    componentModel = "spring",
    imports = {java.time.Instant.class, java.util.UUID.class}
)
public interface {{Entity}}Mapper {

    @Mapping(target = "id", expression = "java(UUID.randomUUID())")
    @Mapping(target = "createdAt", expression = "java(Instant.now())")
    @Mapping(target = "updatedAt", expression = "java(Instant.now())")
    @Mapping(target = "fullName", expression = "java(request.firstName() + \" \" + request.lastName())")
    @Mapping(target = "slug", expression = "java(generateSlug(request.name()))")
    {{Entity}} toEntity({{Entity}}Request request);

    default String generateSlug(String name) {
        if (name == null) return null;
        return name.toLowerCase()
            .replaceAll("[^a-z0-9\\s-]", "")
            .replaceAll("\\s+", "-")
            .replaceAll("-+", "-")
            .trim();
    }
}
```

### With Context Parameters

```java
@Mapper(componentModel = "spring")
public interface {{Entity}}Mapper {

    @Mapping(target = "locale", ignore = true)
    {{Entity}}Response toResponse({{Entity}} entity, @Context java.util.Locale locale);

    @AfterMapping
    default void setLocaleSpecificFields(
            {{Entity}} entity,
            @MappingTarget {{Entity}}Response.Builder response,
            @Context java.util.Locale locale) {
        // Set locale-specific formatted fields
        if (locale != null) {
            response.formattedPrice(formatPrice(entity.getPrice(), locale));
        }
    }

    default String formatPrice(java.math.BigDecimal price, java.util.Locale locale) {
        if (price == null) return null;
        return java.text.NumberFormat.getCurrencyInstance(locale).format(price);
    }
}
```

### With Decorator Pattern

```java
// Mapper interface
@Mapper(componentModel = "spring")
@DecoratedWith({{Entity}}MapperDecorator.class)
public interface {{Entity}}Mapper {

    {{Entity}}Response toResponse({{Entity}} entity);

    {{Entity}} toEntity({{Entity}}Request request);
}

// Decorator implementation
public abstract class {{Entity}}MapperDecorator implements {{Entity}}Mapper {

    @Autowired
    @Qualifier("delegate")
    private {{Entity}}Mapper delegate;

    @Autowired
    private CategoryRepository categoryRepository;

    @Override
    public {{Entity}}Response toResponse({{Entity}} entity) {
        {{Entity}}Response response = delegate.toResponse(entity);
        // Add additional logic
        return response;
    }

    @Override
    public {{Entity}} toEntity({{Entity}}Request request) {
        {{Entity}} entity = delegate.toEntity(request);
        // Resolve relationships
        if (request.categoryId() != null) {
            entity.setCategory(categoryRepository.findById(request.categoryId())
                .orElseThrow(() -> new ResourceNotFoundException("Category", request.categoryId())));
        }
        return entity;
    }
}
```

### With Multiple Source Objects

```java
@Mapper(componentModel = "spring")
public interface {{Entity}}Mapper {

    @Mapping(target = "id", source = "entity.id")
    @Mapping(target = "name", source = "entity.name")
    @Mapping(target = "categoryName", source = "category.name")
    @Mapping(target = "createdByName", source = "user.displayName")
    @Mapping(target = "permissions", source = "permissions")
    {{Entity}}DetailResponse toDetailResponse(
        {{Entity}} entity,
        Category category,
        User user,
        List<String> permissions
    );
}
```

### With Inverse Mapping

```java
@Mapper(componentModel = "spring")
public interface {{Entity}}Mapper {

    @Mapping(target = "status", source = "status", qualifiedByName = "statusToDto")
    {{Entity}}Response toResponse({{Entity}} entity);

    @InheritInverseConfiguration
    @Mapping(target = "id", ignore = true)
    @Mapping(target = "createdAt", ignore = true)
    @Mapping(target = "updatedAt", ignore = true)
    {{Entity}} toEntity({{Entity}}Response response);

    @InheritConfiguration(name = "toResponse")
    @Mapping(target = "additionalField", source = "extraData")
    {{Entity}}DetailResponse toDetailResponse({{Entity}} entity, String extraData);
}
```

### Configuration Class

```java
// Central mapper configuration
@MapperConfig(
    componentModel = "spring",
    unmappedTargetPolicy = ReportingPolicy.ERROR,
    unmappedSourcePolicy = ReportingPolicy.WARN,
    nullValuePropertyMappingStrategy = NullValuePropertyMappingStrategy.IGNORE,
    nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS,
    injectionStrategy = InjectionStrategy.CONSTRUCTOR,
    collectionMappingStrategy = CollectionMappingStrategy.ADDER_PREFERRED
)
public interface MapperConfiguration {
}

// Use configuration
@Mapper(config = MapperConfiguration.class)
public interface {{Entity}}Mapper {
    // Inherits all configuration settings
}
```

## Maven Dependencies

```xml
<properties>
    <mapstruct.version>1.5.5.Final</mapstruct.version>
</properties>

<dependencies>
    <dependency>
        <groupId>org.mapstruct</groupId>
        <artifactId>mapstruct</artifactId>
        <version>${mapstruct.version}</version>
    </dependency>
</dependencies>

<build>
    <plugins>
        <plugin>
            <groupId>org.apache.maven.plugins</groupId>
            <artifactId>maven-compiler-plugin</artifactId>
            <configuration>
                <annotationProcessorPaths>
                    <path>
                        <groupId>org.mapstruct</groupId>
                        <artifactId>mapstruct-processor</artifactId>
                        <version>${mapstruct.version}</version>
                    </path>
                    <path>
                        <groupId>org.projectlombok</groupId>
                        <artifactId>lombok</artifactId>
                        <version>${lombok.version}</version>
                    </path>
                    <path>
                        <groupId>org.projectlombok</groupId>
                        <artifactId>lombok-mapstruct-binding</artifactId>
                        <version>0.2.0</version>
                    </path>
                </annotationProcessorPaths>
            </configuration>
        </plugin>
    </plugins>
</build>
```
