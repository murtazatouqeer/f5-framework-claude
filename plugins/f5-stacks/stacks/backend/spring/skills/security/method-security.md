# Method-Level Security

Spring Security method-level authorization with @PreAuthorize, @PostAuthorize, and custom security expressions.

## Enable Method Security

```java
@Configuration
@EnableMethodSecurity(
    prePostEnabled = true,      // @PreAuthorize, @PostAuthorize
    securedEnabled = true,      // @Secured
    jsr250Enabled = true        // @RolesAllowed
)
public class MethodSecurityConfig {
}
```

## Basic Annotations

### @PreAuthorize

```java
@Service
public class ProductService {

    // Role-based access
    @PreAuthorize("hasRole('ADMIN')")
    public void deleteProduct(UUID id) {
        productRepository.deleteById(id);
    }

    // Multiple roles
    @PreAuthorize("hasAnyRole('ADMIN', 'MANAGER')")
    public Product updatePrice(UUID id, BigDecimal price) {
        // ...
    }

    // Authority-based (includes ROLE_ prefix handling)
    @PreAuthorize("hasAuthority('ROLE_ADMIN')")
    public void adminOnly() {
        // ...
    }

    // Permission-based
    @PreAuthorize("hasAuthority('product:write')")
    public Product create(Product product) {
        // ...
    }

    // Complex expressions
    @PreAuthorize("hasRole('ADMIN') or hasRole('MANAGER')")
    public void adminOrManager() {
        // ...
    }

    // AND condition
    @PreAuthorize("hasRole('USER') and hasAuthority('premium:access')")
    public void premiumUserOnly() {
        // ...
    }

    // Authenticated check
    @PreAuthorize("isAuthenticated()")
    public UserProfile getProfile() {
        // ...
    }

    // Anonymous check
    @PreAuthorize("isAnonymous()")
    public void publicOnly() {
        // ...
    }
}
```

### @PostAuthorize

```java
@Service
public class DocumentService {

    // Check returned object
    @PostAuthorize("returnObject.owner == authentication.name")
    public Document findById(UUID id) {
        return documentRepository.findById(id).orElseThrow();
    }

    // Check returned object with null safety
    @PostAuthorize("returnObject == null or returnObject.owner == authentication.name")
    public Document findByIdOptional(UUID id) {
        return documentRepository.findById(id).orElse(null);
    }

    // Check against custom principal
    @PostAuthorize("returnObject.tenantId == authentication.principal.tenantId")
    public Document findByIdTenantAware(UUID id) {
        return documentRepository.findById(id).orElseThrow();
    }
}
```

### @PreFilter and @PostFilter

```java
@Service
public class ProductService {

    // Filter input collection
    @PreFilter("filterObject.category.id == authentication.principal.allowedCategoryId")
    public List<Product> createBatch(List<Product> products) {
        return productRepository.saveAll(products);
    }

    // Filter output collection
    @PostFilter("filterObject.owner == authentication.name")
    public List<Document> findAllDocuments() {
        return documentRepository.findAll();
    }

    // Combined filtering
    @PreFilter("filterObject.price > 0")
    @PostFilter("filterObject.status == 'ACTIVE'")
    public List<Product> processProducts(List<Product> products) {
        return productRepository.saveAll(products);
    }
}
```

## Parameter Access

### Using Method Parameters

```java
@Service
public class OrderService {

    // Access parameter by name
    @PreAuthorize("#customerId == authentication.principal.id")
    public List<Order> getCustomerOrders(UUID customerId) {
        return orderRepository.findByCustomerId(customerId);
    }

    // Access object property
    @PreAuthorize("#order.customerId == authentication.principal.id")
    public Order createOrder(Order order) {
        return orderRepository.save(order);
    }

    // Access multiple parameters
    @PreAuthorize("#customerId == authentication.principal.id or hasRole('ADMIN')")
    public Order getOrder(UUID customerId, UUID orderId) {
        return orderRepository.findByIdAndCustomerId(orderId, customerId)
            .orElseThrow();
    }

    // Access path variable from request
    @PreAuthorize("@securityService.canAccessResource(#id, authentication)")
    public Resource getResource(@PathVariable UUID id) {
        return resourceRepository.findById(id).orElseThrow();
    }
}
```

### Using Authentication Object

```java
@Service
public class UserService {

    // Access principal
    @PreAuthorize("authentication.principal.id == #userId")
    public UserProfile updateProfile(UUID userId, ProfileUpdateRequest request) {
        // ...
    }

    // Access principal properties
    @PreAuthorize("authentication.principal.tenantId == #tenantId")
    public List<User> getUsersByTenant(String tenantId) {
        return userRepository.findByTenantId(tenantId);
    }

    // Check authentication details
    @PreAuthorize("authentication.details.remoteAddress == '127.0.0.1'")
    public void localOnly() {
        // ...
    }
}
```

## Custom Security Expressions

### Permission Evaluator

```java
@Component
public class CustomPermissionEvaluator implements PermissionEvaluator {

    private final ProductRepository productRepository;
    private final DocumentRepository documentRepository;

    @Override
    public boolean hasPermission(
            Authentication authentication,
            Object targetDomainObject,
            Object permission) {

        if (authentication == null || targetDomainObject == null) {
            return false;
        }

        CustomUserDetails user = (CustomUserDetails) authentication.getPrincipal();
        String permissionStr = (String) permission;

        if (targetDomainObject instanceof Product product) {
            return hasProductPermission(user, product, permissionStr);
        }

        if (targetDomainObject instanceof Document document) {
            return hasDocumentPermission(user, document, permissionStr);
        }

        return false;
    }

    @Override
    public boolean hasPermission(
            Authentication authentication,
            Serializable targetId,
            String targetType,
            Object permission) {

        if (authentication == null) {
            return false;
        }

        CustomUserDetails user = (CustomUserDetails) authentication.getPrincipal();
        UUID id = (UUID) targetId;
        String permissionStr = (String) permission;

        return switch (targetType) {
            case "Product" -> hasProductPermission(user, id, permissionStr);
            case "Document" -> hasDocumentPermission(user, id, permissionStr);
            default -> false;
        };
    }

    private boolean hasProductPermission(CustomUserDetails user, Product product, String permission) {
        return switch (permission) {
            case "read" -> true;  // Anyone can read
            case "write" -> product.getCreatedBy().equals(user.getId()) ||
                           user.hasRole("ADMIN");
            case "delete" -> user.hasRole("ADMIN");
            default -> false;
        };
    }

    private boolean hasProductPermission(CustomUserDetails user, UUID productId, String permission) {
        return productRepository.findById(productId)
            .map(product -> hasProductPermission(user, product, permission))
            .orElse(false);
    }

    // Similar methods for documents...
}

// Configuration
@Configuration
public class MethodSecurityConfig {

    @Bean
    public MethodSecurityExpressionHandler methodSecurityExpressionHandler(
            CustomPermissionEvaluator permissionEvaluator) {
        DefaultMethodSecurityExpressionHandler handler =
            new DefaultMethodSecurityExpressionHandler();
        handler.setPermissionEvaluator(permissionEvaluator);
        return handler;
    }
}

// Usage
@Service
public class ProductService {

    @PreAuthorize("hasPermission(#product, 'write')")
    public Product update(Product product) {
        return productRepository.save(product);
    }

    @PreAuthorize("hasPermission(#id, 'Product', 'delete')")
    public void delete(UUID id) {
        productRepository.deleteById(id);
    }
}
```

### Custom Security Service

```java
@Service("securityService")
@RequiredArgsConstructor
public class SecurityService {

    private final ProductRepository productRepository;
    private final TeamMemberRepository teamMemberRepository;

    public boolean isOwner(UUID resourceId, Authentication authentication) {
        CustomUserDetails user = (CustomUserDetails) authentication.getPrincipal();
        return productRepository.findById(resourceId)
            .map(product -> product.getCreatedBy().equals(user.getId()))
            .orElse(false);
    }

    public boolean isTeamMember(UUID teamId, Authentication authentication) {
        CustomUserDetails user = (CustomUserDetails) authentication.getPrincipal();
        return teamMemberRepository.existsByTeamIdAndUserId(teamId, user.getId());
    }

    public boolean canAccessResource(UUID resourceId, Authentication authentication) {
        if (isOwner(resourceId, authentication)) {
            return true;
        }

        // Check if user has admin role
        return authentication.getAuthorities().stream()
            .anyMatch(auth -> auth.getAuthority().equals("ROLE_ADMIN"));
    }

    public boolean isSameOrganization(UUID orgId, Authentication authentication) {
        CustomUserDetails user = (CustomUserDetails) authentication.getPrincipal();
        return user.getOrganizationId().equals(orgId);
    }
}

// Usage in service
@Service
public class ResourceService {

    @PreAuthorize("@securityService.isOwner(#id, authentication)")
    public void deleteResource(UUID id) {
        resourceRepository.deleteById(id);
    }

    @PreAuthorize("@securityService.isTeamMember(#teamId, authentication)")
    public List<Task> getTeamTasks(UUID teamId) {
        return taskRepository.findByTeamId(teamId);
    }

    @PreAuthorize("@securityService.canAccessResource(#id, authentication) or hasRole('ADMIN')")
    public Resource getResource(UUID id) {
        return resourceRepository.findById(id).orElseThrow();
    }
}
```

### Custom SpEL Functions

```java
@Component
public class SecurityExpressions {

    public static boolean hasMinRole(Authentication auth, String minRole) {
        Map<String, Integer> roleHierarchy = Map.of(
            "USER", 1,
            "MODERATOR", 2,
            "ADMIN", 3,
            "SUPER_ADMIN", 4
        );

        int minRoleLevel = roleHierarchy.getOrDefault(minRole, 0);

        return auth.getAuthorities().stream()
            .map(GrantedAuthority::getAuthority)
            .map(a -> a.replace("ROLE_", ""))
            .map(roleHierarchy::get)
            .filter(Objects::nonNull)
            .anyMatch(level -> level >= minRoleLevel);
    }
}

// Register in expression handler
@Configuration
public class MethodSecurityConfig {

    @Bean
    public MethodSecurityExpressionHandler methodSecurityExpressionHandler() {
        DefaultMethodSecurityExpressionHandler handler =
            new DefaultMethodSecurityExpressionHandler();

        // Register custom root object with methods
        handler.setDefaultRootObject(new SecurityExpressions());

        return handler;
    }
}

// Usage
@PreAuthorize("hasMinRole(authentication, 'MODERATOR')")
public void moderatorOrHigher() {
    // ...
}
```

## Controller-Level Security

```java
@RestController
@RequestMapping("/api/v1/products")
public class ProductController {

    @GetMapping
    @PreAuthorize("hasAuthority('product:read')")
    public List<ProductResponse> list() {
        return productService.findAll();
    }

    @GetMapping("/{id}")
    @PreAuthorize("hasAuthority('product:read')")
    public ProductResponse getById(@PathVariable UUID id) {
        return productService.findById(id);
    }

    @PostMapping
    @PreAuthorize("hasAuthority('product:write')")
    public ProductResponse create(@Valid @RequestBody ProductRequest request) {
        return productService.create(request);
    }

    @PutMapping("/{id}")
    @PreAuthorize("hasAuthority('product:write') and @securityService.isOwner(#id, authentication)")
    public ProductResponse update(
            @PathVariable UUID id,
            @Valid @RequestBody ProductRequest request) {
        return productService.update(id, request);
    }

    @DeleteMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN') or @securityService.isOwner(#id, authentication)")
    public void delete(@PathVariable UUID id) {
        productService.delete(id);
    }
}
```

## Class-Level Security

```java
@RestController
@RequestMapping("/api/v1/admin")
@PreAuthorize("hasRole('ADMIN')")  // Applies to all methods
public class AdminController {

    @GetMapping("/users")
    public List<UserResponse> listUsers() {
        return userService.findAll();
    }

    @PostMapping("/users/{id}/roles")
    public void assignRole(@PathVariable UUID id, @RequestBody RoleRequest request) {
        userService.assignRole(id, request.getRole());
    }

    // Override class-level
    @GetMapping("/public-stats")
    @PreAuthorize("permitAll()")
    public StatsResponse getPublicStats() {
        return statsService.getPublicStats();
    }
}
```

## Testing Method Security

```java
@SpringBootTest
class ProductServiceSecurityTest {

    @Autowired
    private ProductService productService;

    @Test
    @WithMockUser(roles = "ADMIN")
    void deleteProduct_asAdmin_succeeds() {
        assertDoesNotThrow(() -> productService.delete(testProductId));
    }

    @Test
    @WithMockUser(roles = "USER")
    void deleteProduct_asUser_denied() {
        assertThrows(AccessDeniedException.class,
            () -> productService.delete(testProductId));
    }

    @Test
    @WithMockUser(username = "owner@test.com")
    void updateProduct_asOwner_succeeds() {
        // Setup: product owned by owner@test.com
        Product product = createProductOwnedBy("owner@test.com");

        assertDoesNotThrow(() -> productService.update(product));
    }

    @Test
    @WithUserDetails("test@example.com")
    void getProfile_withUserDetails_succeeds() {
        UserProfile profile = userService.getProfile();
        assertThat(profile.getEmail()).isEqualTo("test@example.com");
    }
}
```

## Best Practices

1. **Prefer @PreAuthorize** over @Secured or @RolesAllowed for flexibility
2. **Use service beans** for complex authorization logic
3. **Keep expressions readable** - extract complex logic to services
4. **Test security rules** explicitly
5. **Document authorization requirements**
6. **Use hierarchical roles** when appropriate
7. **Combine with URL security** - defense in depth
8. **Audit authorization failures**
