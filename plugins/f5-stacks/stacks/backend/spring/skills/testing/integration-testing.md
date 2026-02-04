# Integration Testing

Spring Boot integration testing patterns with database, web layer, and full stack tests.

## Dependencies

```groovy
dependencies {
    testImplementation 'org.springframework.boot:spring-boot-starter-test'
    testImplementation 'org.springframework.security:spring-security-test'
    testImplementation 'io.rest-assured:rest-assured'
}
```

## Repository Integration Tests

### Basic Repository Test

```java
package com.example.app.repository;

import com.example.app.domain.entity.Product;
import com.example.app.domain.entity.ProductStatus;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.boot.test.autoconfigure.orm.jpa.TestEntityManager;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;

import java.math.BigDecimal;
import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.*;

@DataJpaTest
@DisplayName("ProductRepository")
class ProductRepositoryTest {

    @Autowired
    private ProductRepository productRepository;

    @Autowired
    private TestEntityManager entityManager;

    private Product savedProduct;

    @BeforeEach
    void setUp() {
        savedProduct = entityManager.persistAndFlush(
            Product.builder()
                .name("Test Product")
                .sku("TST-0001")
                .price(new BigDecimal("29.99"))
                .stock(100)
                .status(ProductStatus.ACTIVE)
                .build()
        );
        entityManager.clear();
    }

    @Nested
    @DisplayName("findBySku")
    class FindBySku {

        @Test
        @DisplayName("should find product by SKU")
        void shouldFindProductBySku() {
            Optional<Product> result = productRepository.findBySku("TST-0001");

            assertThat(result).isPresent();
            assertThat(result.get().getName()).isEqualTo("Test Product");
        }

        @Test
        @DisplayName("should return empty for non-existent SKU")
        void shouldReturnEmptyForNonExistentSku() {
            Optional<Product> result = productRepository.findBySku("INVALID-SKU");

            assertThat(result).isEmpty();
        }
    }

    @Nested
    @DisplayName("findByStatus")
    class FindByStatus {

        @BeforeEach
        void setUpMore() {
            entityManager.persistAndFlush(
                Product.builder()
                    .name("Inactive Product")
                    .sku("TST-0002")
                    .price(new BigDecimal("19.99"))
                    .stock(50)
                    .status(ProductStatus.INACTIVE)
                    .build()
            );
        }

        @Test
        @DisplayName("should find active products")
        void shouldFindActiveProducts() {
            List<Product> result = productRepository.findByStatus(ProductStatus.ACTIVE);

            assertThat(result).hasSize(1);
            assertThat(result.get(0).getName()).isEqualTo("Test Product");
        }

        @Test
        @DisplayName("should find inactive products")
        void shouldFindInactiveProducts() {
            List<Product> result = productRepository.findByStatus(ProductStatus.INACTIVE);

            assertThat(result).hasSize(1);
            assertThat(result.get(0).getName()).isEqualTo("Inactive Product");
        }
    }

    @Nested
    @DisplayName("Custom Queries")
    class CustomQueries {

        @BeforeEach
        void setUpProducts() {
            entityManager.persistAndFlush(Product.builder()
                .name("Cheap Product")
                .sku("TST-0002")
                .price(new BigDecimal("9.99"))
                .stock(200)
                .status(ProductStatus.ACTIVE)
                .build());

            entityManager.persistAndFlush(Product.builder()
                .name("Expensive Product")
                .sku("TST-0003")
                .price(new BigDecimal("99.99"))
                .stock(10)
                .status(ProductStatus.ACTIVE)
                .build());
        }

        @Test
        @DisplayName("should find products by price range")
        void shouldFindByPriceRange() {
            List<Product> result = productRepository.findByPriceBetween(
                new BigDecimal("10.00"),
                new BigDecimal("50.00")
            );

            assertThat(result).hasSize(1);
            assertThat(result.get(0).getName()).isEqualTo("Test Product");
        }

        @Test
        @DisplayName("should find products with low stock")
        void shouldFindLowStockProducts() {
            List<Product> result = productRepository.findByStockLessThan(50);

            assertThat(result).hasSize(1);
            assertThat(result.get(0).getName()).isEqualTo("Expensive Product");
        }

        @Test
        @DisplayName("should search products by name")
        void shouldSearchByName() {
            Page<Product> result = productRepository.findByNameContainingIgnoreCase(
                "product",
                PageRequest.of(0, 10, Sort.by("name"))
            );

            assertThat(result.getTotalElements()).isEqualTo(3);
        }
    }

    @Nested
    @DisplayName("Pagination")
    class Pagination {

        @BeforeEach
        void setUpManyProducts() {
            for (int i = 0; i < 25; i++) {
                entityManager.persist(Product.builder()
                    .name("Product " + i)
                    .sku("PROD-" + String.format("%04d", i))
                    .price(new BigDecimal("10.00"))
                    .stock(100)
                    .status(ProductStatus.ACTIVE)
                    .build());
            }
            entityManager.flush();
        }

        @Test
        @DisplayName("should return first page")
        void shouldReturnFirstPage() {
            Page<Product> page = productRepository.findAll(
                PageRequest.of(0, 10, Sort.by("name"))
            );

            assertThat(page.getNumber()).isZero();
            assertThat(page.getSize()).isEqualTo(10);
            assertThat(page.getTotalElements()).isEqualTo(26); // 25 + 1 from setUp
            assertThat(page.getTotalPages()).isEqualTo(3);
        }

        @Test
        @DisplayName("should return sorted results")
        void shouldReturnSortedResults() {
            Page<Product> page = productRepository.findAll(
                PageRequest.of(0, 5, Sort.by(Sort.Direction.DESC, "price"))
            );

            List<Product> products = page.getContent();
            assertThat(products.get(0).getPrice())
                .isGreaterThanOrEqualTo(products.get(1).getPrice());
        }
    }
}
```

## Service Integration Tests

```java
@SpringBootTest
@Transactional
@DisplayName("ProductService Integration")
class ProductServiceIntegrationTest {

    @Autowired
    private ProductService productService;

    @Autowired
    private ProductRepository productRepository;

    @Autowired
    private CategoryRepository categoryRepository;

    private Category testCategory;

    @BeforeEach
    void setUp() {
        testCategory = categoryRepository.save(
            Category.builder()
                .name("Electronics")
                .build()
        );
    }

    @Test
    @DisplayName("should create product with category")
    void shouldCreateProductWithCategory() {
        // Given
        ProductRequest request = new ProductRequest(
            "New Laptop",
            "High-performance laptop",
            "LAP-0001",
            new BigDecimal("999.99"),
            50,
            testCategory.getId()
        );

        // When
        ProductResponse response = productService.create(request);

        // Then
        assertThat(response.id()).isNotNull();
        assertThat(response.name()).isEqualTo("New Laptop");

        Product savedProduct = productRepository.findById(response.id()).orElseThrow();
        assertThat(savedProduct.getCategory().getId()).isEqualTo(testCategory.getId());
    }

    @Test
    @DisplayName("should update product stock")
    void shouldUpdateProductStock() {
        // Given
        Product product = productRepository.save(
            Product.builder()
                .name("Test Product")
                .sku("TST-0001")
                .price(new BigDecimal("50.00"))
                .stock(100)
                .status(ProductStatus.ACTIVE)
                .build()
        );

        // When
        productService.updateStock(product.getId(), 75);

        // Then
        Product updated = productRepository.findById(product.getId()).orElseThrow();
        assertThat(updated.getStock()).isEqualTo(75);
    }

    @Test
    @DisplayName("should throw exception for insufficient stock")
    void shouldThrowExceptionForInsufficientStock() {
        // Given
        Product product = productRepository.save(
            Product.builder()
                .name("Limited Product")
                .sku("LIM-0001")
                .price(new BigDecimal("25.00"))
                .stock(5)
                .status(ProductStatus.ACTIVE)
                .build()
        );

        // When/Then
        assertThatThrownBy(() -> productService.decrementStock(product.getId(), 10))
            .isInstanceOf(BusinessException.class)
            .hasMessageContaining("Insufficient stock");
    }
}
```

## Web Layer Integration Tests

### Full MVC Test

```java
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@AutoConfigureMockMvc
@DisplayName("ProductController Integration")
class ProductControllerIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private ProductRepository productRepository;

    @BeforeEach
    void setUp() {
        productRepository.deleteAll();
    }

    @Test
    @DisplayName("should create and retrieve product")
    @WithMockUser(roles = "ADMIN")
    void shouldCreateAndRetrieveProduct() throws Exception {
        // Create
        ProductRequest request = new ProductRequest(
            "Integration Test Product",
            "Description",
            "INT-0001",
            new BigDecimal("49.99"),
            100,
            null
        );

        String createResponse = mockMvc.perform(post("/api/v1/products")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.id").exists())
            .andReturn()
            .getResponse()
            .getContentAsString();

        String productId = objectMapper.readTree(createResponse).get("id").asText();

        // Retrieve
        mockMvc.perform(get("/api/v1/products/{id}", productId))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.name").value("Integration Test Product"))
            .andExpect(jsonPath("$.sku").value("INT-0001"));

        // Verify in database
        Product savedProduct = productRepository.findById(UUID.fromString(productId))
            .orElseThrow();
        assertThat(savedProduct.getName()).isEqualTo("Integration Test Product");
    }

    @Test
    @DisplayName("should list products with pagination")
    @WithMockUser
    void shouldListProductsWithPagination() throws Exception {
        // Given
        for (int i = 0; i < 15; i++) {
            productRepository.save(Product.builder()
                .name("Product " + i)
                .sku("PROD-" + String.format("%04d", i))
                .price(new BigDecimal("10.00"))
                .stock(100)
                .status(ProductStatus.ACTIVE)
                .build());
        }

        // When/Then
        mockMvc.perform(get("/api/v1/products")
                .param("page", "0")
                .param("size", "10"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.content").isArray())
            .andExpect(jsonPath("$.content.length()").value(10))
            .andExpect(jsonPath("$.totalElements").value(15))
            .andExpect(jsonPath("$.totalPages").value(2));
    }
}
```

### RestAssured Tests

```java
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@DisplayName("Product API E2E Tests")
class ProductApiE2ETest {

    @LocalServerPort
    private int port;

    @Autowired
    private ProductRepository productRepository;

    @BeforeEach
    void setUp() {
        RestAssured.port = port;
        RestAssured.basePath = "/api/v1";
        productRepository.deleteAll();
    }

    @Test
    @DisplayName("should perform full CRUD operations")
    void shouldPerformFullCrudOperations() {
        // Create
        ProductRequest createRequest = new ProductRequest(
            "E2E Product", "Description", "E2E-0001",
            new BigDecimal("75.00"), 50, null
        );

        String productId =
            given()
                .contentType(ContentType.JSON)
                .body(createRequest)
                .header("Authorization", "Bearer " + getAuthToken())
            .when()
                .post("/products")
            .then()
                .statusCode(201)
                .body("name", equalTo("E2E Product"))
                .extract()
                .path("id");

        // Read
        given()
            .header("Authorization", "Bearer " + getAuthToken())
        .when()
            .get("/products/{id}", productId)
        .then()
            .statusCode(200)
            .body("id", equalTo(productId))
            .body("sku", equalTo("E2E-0001"));

        // Update
        ProductRequest updateRequest = new ProductRequest(
            "Updated E2E Product", "Updated Description", "E2E-0001",
            new BigDecimal("85.00"), 40, null
        );

        given()
            .contentType(ContentType.JSON)
            .body(updateRequest)
            .header("Authorization", "Bearer " + getAuthToken())
        .when()
            .put("/products/{id}", productId)
        .then()
            .statusCode(200)
            .body("name", equalTo("Updated E2E Product"))
            .body("price", equalTo(85.00f));

        // Delete
        given()
            .header("Authorization", "Bearer " + getAdminToken())
        .when()
            .delete("/products/{id}", productId)
        .then()
            .statusCode(204);

        // Verify deleted
        given()
            .header("Authorization", "Bearer " + getAuthToken())
        .when()
            .get("/products/{id}", productId)
        .then()
            .statusCode(404);
    }

    @Test
    @DisplayName("should filter products")
    void shouldFilterProducts() {
        // Given
        productRepository.saveAll(List.of(
            Product.builder()
                .name("Active Product")
                .sku("ACT-0001")
                .price(new BigDecimal("50.00"))
                .stock(100)
                .status(ProductStatus.ACTIVE)
                .build(),
            Product.builder()
                .name("Inactive Product")
                .sku("INA-0001")
                .price(new BigDecimal("30.00"))
                .stock(0)
                .status(ProductStatus.INACTIVE)
                .build()
        ));

        // When/Then
        given()
            .header("Authorization", "Bearer " + getAuthToken())
            .queryParam("status", "ACTIVE")
        .when()
            .get("/products")
        .then()
            .statusCode(200)
            .body("content.size()", equalTo(1))
            .body("content[0].name", equalTo("Active Product"));
    }

    private String getAuthToken() {
        // Implement token retrieval for tests
        return "test-user-token";
    }

    private String getAdminToken() {
        return "test-admin-token";
    }
}
```

## Event-Driven Integration Tests

```java
@SpringBootTest
@Transactional
@DisplayName("Order Event Integration")
class OrderEventIntegrationTest {

    @Autowired
    private OrderService orderService;

    @Autowired
    private ProductRepository productRepository;

    @SpyBean
    private ApplicationEventPublisher eventPublisher;

    @Captor
    private ArgumentCaptor<OrderCreatedEvent> eventCaptor;

    @Test
    @DisplayName("should publish event when order created")
    void shouldPublishEventWhenOrderCreated() {
        // Given
        Product product = productRepository.save(
            Product.builder()
                .name("Event Test Product")
                .sku("EVT-0001")
                .price(new BigDecimal("100.00"))
                .stock(50)
                .status(ProductStatus.ACTIVE)
                .build()
        );

        CreateOrderRequest request = new CreateOrderRequest(
            List.of(new OrderItemRequest(product.getId(), 2))
        );

        // When
        OrderResponse order = orderService.create(request);

        // Then
        verify(eventPublisher).publishEvent(eventCaptor.capture());

        OrderCreatedEvent event = eventCaptor.getValue();
        assertThat(event.getOrderId()).isEqualTo(order.id());
        assertThat(event.getTotalAmount()).isEqualByComparingTo(new BigDecimal("200.00"));
    }
}
```

## Profile-Specific Tests

```java
@SpringBootTest
@ActiveProfiles("test")
@TestPropertySource(properties = {
    "app.feature.notifications.enabled=false",
    "app.cache.ttl=60"
})
@DisplayName("Profile-Specific Integration Tests")
class ProfileSpecificIntegrationTest {

    @Value("${app.feature.notifications.enabled}")
    private boolean notificationsEnabled;

    @Autowired
    private FeatureFlags featureFlags;

    @Test
    @DisplayName("should use test profile configuration")
    void shouldUseTestProfileConfiguration() {
        assertThat(notificationsEnabled).isFalse();
    }

    @Test
    @DisplayName("should disable notifications in test")
    void shouldDisableNotificationsInTest() {
        assertThat(featureFlags.isNotificationsEnabled()).isFalse();
    }
}
```

## Database Cleanup Strategies

```java
@SpringBootTest
@Transactional  // Rollback after each test
class TransactionalCleanupTest {
    // All changes rolled back automatically
}

@SpringBootTest
@Sql(executionPhase = Sql.ExecutionPhase.BEFORE_TEST_METHOD,
     scripts = "classpath:sql/cleanup.sql")
@Sql(executionPhase = Sql.ExecutionPhase.BEFORE_TEST_METHOD,
     scripts = "classpath:sql/test-data.sql")
class SqlScriptCleanupTest {
    // Uses SQL scripts for setup/cleanup
}

@SpringBootTest
@DirtiesContext(classMode = DirtiesContext.ClassMode.AFTER_EACH_TEST_METHOD)
class ContextRefreshTest {
    // Refreshes entire context (slow, use sparingly)
}
```

## Custom Test Configuration

```java
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Transactional
public @interface IntegrationTest {
}

// Usage
@IntegrationTest
@DisplayName("Order Service")
class OrderServiceIntegrationTest {
    // Test methods
}
```

## Test Slices Reference

| Annotation | Purpose | Loaded Components |
|------------|---------|-------------------|
| `@DataJpaTest` | JPA repositories | JPA, EntityManager |
| `@WebMvcTest` | Controllers | MVC, MockMvc |
| `@WebFluxTest` | WebFlux controllers | WebFlux |
| `@DataMongoTest` | MongoDB repositories | MongoDB |
| `@DataRedisTest` | Redis operations | Redis |
| `@JsonTest` | JSON serialization | Jackson |

## Best Practices

1. **Use @Transactional** - Automatic rollback after tests
2. **Prefer test slices** - Load only needed components
3. **Use realistic data** - Representative test scenarios
4. **Test boundaries** - Focus on integration points
5. **Clean database state** - Predictable test environment
6. **Use @ActiveProfiles** - Separate test configuration
7. **Mock external services** - WireMock for HTTP APIs
8. **Verify database state** - Check actual persisted data
9. **Test security** - Include authentication scenarios
10. **Performance considerations** - Keep tests fast
