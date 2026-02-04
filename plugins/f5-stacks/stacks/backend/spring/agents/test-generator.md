# Test Generator Agent

Spring Boot test generator with unit tests, integration tests, and Testcontainers support.

## Capabilities

- Generate unit tests with JUnit 5 and Mockito
- Create integration tests with @SpringBootTest
- Implement controller tests with MockMvc
- Generate repository tests with Testcontainers
- Create test fixtures and factories
- Implement parameterized tests

## Input Requirements

```yaml
class_name: "ProductService"
class_type: "service"
methods:
  - create
  - findById
  - update
  - delete
features:
  - unit_tests
  - integration_tests
  - mocking
  - testcontainers
```

## Generated Code Pattern

### Unit Test (Service)

```java
package com.example.app.service;

import com.example.app.domain.entity.Product;
import com.example.app.domain.entity.ProductStatus;
import com.example.app.exception.ProductNotFoundException;
import com.example.app.exception.DuplicateProductException;
import com.example.app.repository.ProductRepository;
import com.example.app.service.impl.ProductServiceImpl;
import org.junit.jupiter.api.*;
import org.junit.jupiter.api.extension.ExtendWith;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.*;
import org.mockito.*;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;

import java.math.BigDecimal;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

import static org.assertj.core.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.BDDMockito.*;

/**
 * Unit tests for ProductService.
 *
 * REQ-001: Product Management
 */
@ExtendWith(MockitoExtension.class)
@DisplayName("ProductService Unit Tests")
class ProductServiceTest {

    @Mock
    private ProductRepository productRepository;

    @Mock
    private ApplicationEventPublisher eventPublisher;

    @InjectMocks
    private ProductServiceImpl productService;

    @Captor
    private ArgumentCaptor<Product> productCaptor;

    private Product testProduct;
    private UUID productId;

    @BeforeEach
    void setUp() {
        productId = UUID.randomUUID();
        testProduct = Product.builder()
            .id(productId)
            .name("Test Product")
            .sku("TEST-001")
            .price(new BigDecimal("99.99"))
            .stock(100)
            .status(ProductStatus.ACTIVE)
            .build();
    }

    // ========== Create Tests ==========

    @Nested
    @DisplayName("create()")
    class CreateTests {

        @Test
        @DisplayName("should create product successfully")
        void shouldCreateProductSuccessfully() {
            // Given
            given(productRepository.existsBySkuIgnoreCase(anyString())).willReturn(false);
            given(productRepository.save(any(Product.class))).willReturn(testProduct);

            // When
            Product result = productService.create(testProduct);

            // Then
            assertThat(result).isNotNull();
            assertThat(result.getId()).isEqualTo(productId);
            assertThat(result.getName()).isEqualTo("Test Product");

            then(productRepository).should().existsBySkuIgnoreCase("TEST-001");
            then(productRepository).should().save(productCaptor.capture());
            then(eventPublisher).should().publishEvent(any());

            Product captured = productCaptor.getValue();
            assertThat(captured.getSku()).isEqualTo("TEST-001");
        }

        @Test
        @DisplayName("should throw exception when SKU already exists")
        void shouldThrowExceptionWhenSkuExists() {
            // Given
            given(productRepository.existsBySkuIgnoreCase("TEST-001")).willReturn(true);

            // When & Then
            assertThatThrownBy(() -> productService.create(testProduct))
                .isInstanceOf(DuplicateProductException.class)
                .hasMessageContaining("TEST-001");

            then(productRepository).should(never()).save(any());
        }

        @ParameterizedTest
        @DisplayName("should reject invalid prices")
        @ValueSource(strings = {"-1", "-100", "-0.01"})
        void shouldRejectNegativePrices(String price) {
            // Given
            testProduct.setPrice(new BigDecimal(price));

            // When & Then
            assertThatThrownBy(() -> productService.create(testProduct))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("Price cannot be negative");
        }

        @ParameterizedTest
        @DisplayName("should accept valid prices")
        @ValueSource(strings = {"0", "0.01", "100", "9999.99"})
        void shouldAcceptValidPrices(String price) {
            // Given
            testProduct.setPrice(new BigDecimal(price));
            given(productRepository.existsBySkuIgnoreCase(anyString())).willReturn(false);
            given(productRepository.save(any())).willReturn(testProduct);

            // When
            Product result = productService.create(testProduct);

            // Then
            assertThat(result).isNotNull();
        }
    }

    // ========== Find Tests ==========

    @Nested
    @DisplayName("findById()")
    class FindByIdTests {

        @Test
        @DisplayName("should find product by ID")
        void shouldFindProductById() {
            // Given
            given(productRepository.findById(productId)).willReturn(Optional.of(testProduct));

            // When
            Optional<Product> result = productService.findById(productId);

            // Then
            assertThat(result).isPresent();
            assertThat(result.get().getId()).isEqualTo(productId);
        }

        @Test
        @DisplayName("should return empty when product not found")
        void shouldReturnEmptyWhenNotFound() {
            // Given
            given(productRepository.findById(any())).willReturn(Optional.empty());

            // When
            Optional<Product> result = productService.findById(UUID.randomUUID());

            // Then
            assertThat(result).isEmpty();
        }
    }

    // ========== Update Tests ==========

    @Nested
    @DisplayName("update()")
    class UpdateTests {

        @Test
        @DisplayName("should update product successfully")
        void shouldUpdateProductSuccessfully() {
            // Given
            testProduct.setVersion(1L);
            given(productRepository.existsById(productId)).willReturn(true);
            given(productRepository.save(any())).willReturn(testProduct);

            // When
            Product result = productService.update(testProduct);

            // Then
            assertThat(result).isNotNull();
            then(productRepository).should().save(testProduct);
            then(eventPublisher).should().publishEvent(any());
        }

        @Test
        @DisplayName("should throw exception when product not found")
        void shouldThrowExceptionWhenProductNotFound() {
            // Given
            testProduct.setVersion(1L);
            given(productRepository.existsById(productId)).willReturn(false);

            // When & Then
            assertThatThrownBy(() -> productService.update(testProduct))
                .isInstanceOf(ProductNotFoundException.class);

            then(productRepository).should(never()).save(any());
        }
    }

    // ========== Delete Tests ==========

    @Nested
    @DisplayName("deleteById()")
    class DeleteTests {

        @Test
        @DisplayName("should soft delete product")
        void shouldSoftDeleteProduct() {
            // Given
            given(productRepository.findById(productId)).willReturn(Optional.of(testProduct));
            given(productRepository.save(any())).willReturn(testProduct);

            // When
            productService.deleteById(productId);

            // Then
            then(productRepository).should().save(productCaptor.capture());
            assertThat(productCaptor.getValue().isDeleted()).isTrue();
            then(eventPublisher).should().publishEvent(any());
        }

        @Test
        @DisplayName("should throw exception when product not found")
        void shouldThrowExceptionWhenProductNotFound() {
            // Given
            given(productRepository.findById(any())).willReturn(Optional.empty());

            // When & Then
            assertThatThrownBy(() -> productService.deleteById(UUID.randomUUID()))
                .isInstanceOf(ProductNotFoundException.class);
        }
    }

    // ========== Pagination Tests ==========

    @Nested
    @DisplayName("findAll()")
    class FindAllTests {

        @Test
        @DisplayName("should return paginated results")
        void shouldReturnPaginatedResults() {
            // Given
            Pageable pageable = PageRequest.of(0, 10);
            List<Product> products = List.of(testProduct);
            Page<Product> page = new PageImpl<>(products, pageable, 1);
            given(productRepository.findAll(pageable)).willReturn(page);

            // When
            Page<Product> result = productService.findAll(pageable);

            // Then
            assertThat(result.getContent()).hasSize(1);
            assertThat(result.getTotalElements()).isEqualTo(1);
        }
    }
}
```

### Controller Test

```java
package com.example.app.web.controller;

import com.example.app.domain.entity.Product;
import com.example.app.domain.entity.ProductStatus;
import com.example.app.service.ProductService;
import com.example.app.web.dto.ProductRequest;
import com.example.app.web.dto.ProductResponse;
import com.example.app.web.mapper.ProductMapper;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.Pageable;
import org.springframework.http.MediaType;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.web.servlet.MockMvc;

import java.math.BigDecimal;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

import static org.mockito.ArgumentMatchers.*;
import static org.mockito.BDDMockito.*;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * Controller tests for ProductController.
 */
@WebMvcTest(ProductController.class)
@DisplayName("ProductController Tests")
class ProductControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @MockBean
    private ProductService productService;

    @MockBean
    private ProductMapper productMapper;

    private Product testProduct;
    private ProductRequest testRequest;
    private ProductResponse testResponse;
    private UUID productId;

    @BeforeEach
    void setUp() {
        productId = UUID.randomUUID();

        testProduct = Product.builder()
            .id(productId)
            .name("Test Product")
            .sku("TEST-001")
            .price(new BigDecimal("99.99"))
            .stock(100)
            .status(ProductStatus.ACTIVE)
            .build();

        testRequest = new ProductRequest();
        testRequest.setName("Test Product");
        testRequest.setSku("TEST-001");
        testRequest.setPrice(new BigDecimal("99.99"));

        testResponse = new ProductResponse();
        testResponse.setId(productId);
        testResponse.setName("Test Product");
        testResponse.setSku("TEST-001");
        testResponse.setPrice(new BigDecimal("99.99"));
    }

    // ========== Create Tests ==========

    @Nested
    @DisplayName("POST /api/v1/products")
    class CreateTests {

        @Test
        @DisplayName("should create product and return 201")
        @WithMockUser(roles = "ADMIN")
        void shouldCreateProduct() throws Exception {
            // Given
            given(productMapper.toEntity(any())).willReturn(testProduct);
            given(productService.create(any())).willReturn(testProduct);
            given(productMapper.toResponse(any())).willReturn(testResponse);

            // When & Then
            mockMvc.perform(post("/api/v1/products")
                    .with(csrf())
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(objectMapper.writeValueAsString(testRequest)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.id").value(productId.toString()))
                .andExpect(jsonPath("$.name").value("Test Product"));
        }

        @Test
        @DisplayName("should return 400 for invalid request")
        @WithMockUser(roles = "ADMIN")
        void shouldReturn400ForInvalidRequest() throws Exception {
            // Given
            testRequest.setName(null);

            // When & Then
            mockMvc.perform(post("/api/v1/products")
                    .with(csrf())
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(objectMapper.writeValueAsString(testRequest)))
                .andExpect(status().isBadRequest());
        }

        @Test
        @DisplayName("should return 401 for unauthenticated")
        void shouldReturn401ForUnauthenticated() throws Exception {
            mockMvc.perform(post("/api/v1/products")
                    .with(csrf())
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(objectMapper.writeValueAsString(testRequest)))
                .andExpect(status().isUnauthorized());
        }
    }

    // ========== Read Tests ==========

    @Nested
    @DisplayName("GET /api/v1/products/{id}")
    class GetByIdTests {

        @Test
        @DisplayName("should return product")
        @WithMockUser
        void shouldReturnProduct() throws Exception {
            // Given
            given(productService.findById(productId)).willReturn(Optional.of(testProduct));
            given(productMapper.toResponse(any())).willReturn(testResponse);

            // When & Then
            mockMvc.perform(get("/api/v1/products/{id}", productId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value(productId.toString()))
                .andExpect(jsonPath("$.name").value("Test Product"));
        }

        @Test
        @DisplayName("should return 404 when not found")
        @WithMockUser
        void shouldReturn404WhenNotFound() throws Exception {
            // Given
            given(productService.findById(any())).willReturn(Optional.empty());

            // When & Then
            mockMvc.perform(get("/api/v1/products/{id}", UUID.randomUUID()))
                .andExpect(status().isNotFound());
        }
    }

    // ========== List Tests ==========

    @Nested
    @DisplayName("GET /api/v1/products")
    class ListTests {

        @Test
        @DisplayName("should return paginated products")
        @WithMockUser
        void shouldReturnPaginatedProducts() throws Exception {
            // Given
            given(productService.findAll(any(Pageable.class)))
                .willReturn(new PageImpl<>(List.of(testProduct)));
            given(productMapper.toResponse(any())).willReturn(testResponse);

            // When & Then
            mockMvc.perform(get("/api/v1/products")
                    .param("page", "0")
                    .param("size", "10"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content").isArray())
                .andExpect(jsonPath("$.content[0].name").value("Test Product"));
        }
    }

    // ========== Delete Tests ==========

    @Nested
    @DisplayName("DELETE /api/v1/products/{id}")
    class DeleteTests {

        @Test
        @DisplayName("should delete product and return 204")
        @WithMockUser(roles = "ADMIN")
        void shouldDeleteProduct() throws Exception {
            // Given
            given(productService.existsById(productId)).willReturn(true);
            willDoNothing().given(productService).deleteById(productId);

            // When & Then
            mockMvc.perform(delete("/api/v1/products/{id}", productId)
                    .with(csrf()))
                .andExpect(status().isNoContent());
        }

        @Test
        @DisplayName("should return 404 when product not found")
        @WithMockUser(roles = "ADMIN")
        void shouldReturn404WhenNotFound() throws Exception {
            // Given
            given(productService.existsById(any())).willReturn(false);

            // When & Then
            mockMvc.perform(delete("/api/v1/products/{id}", UUID.randomUUID())
                    .with(csrf()))
                .andExpect(status().isNotFound());
        }
    }
}
```

### Integration Test with Testcontainers

```java
package com.example.app.integration;

import com.example.app.domain.entity.Product;
import com.example.app.domain.entity.ProductStatus;
import com.example.app.repository.ProductRepository;
import org.junit.jupiter.api.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.boot.testcontainers.service.connection.ServiceConnection;
import org.springframework.http.*;
import org.springframework.test.context.ActiveProfiles;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

import java.math.BigDecimal;

import static org.assertj.core.api.Assertions.*;

/**
 * Integration tests with real database.
 */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@Testcontainers
@ActiveProfiles("test")
@DisplayName("Product Integration Tests")
class ProductIntegrationTest {

    @Container
    @ServiceConnection
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:15-alpine");

    @Autowired
    private TestRestTemplate restTemplate;

    @Autowired
    private ProductRepository productRepository;

    @BeforeEach
    void setUp() {
        productRepository.deleteAll();
    }

    @Test
    @DisplayName("should create and retrieve product")
    void shouldCreateAndRetrieveProduct() {
        // Create product
        var request = new ProductRequest("Test Product", "TEST-001", new BigDecimal("99.99"));

        ResponseEntity<ProductResponse> createResponse = restTemplate.postForEntity(
            "/api/v1/products",
            request,
            ProductResponse.class
        );

        assertThat(createResponse.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        assertThat(createResponse.getBody()).isNotNull();
        assertThat(createResponse.getBody().getName()).isEqualTo("Test Product");

        // Retrieve product
        UUID productId = createResponse.getBody().getId();
        ResponseEntity<ProductResponse> getResponse = restTemplate.getForEntity(
            "/api/v1/products/{id}",
            ProductResponse.class,
            productId
        );

        assertThat(getResponse.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(getResponse.getBody().getId()).isEqualTo(productId);
    }

    @Test
    @DisplayName("should return 404 for non-existent product")
    void shouldReturn404ForNonExistent() {
        ResponseEntity<String> response = restTemplate.getForEntity(
            "/api/v1/products/{id}",
            String.class,
            UUID.randomUUID()
        );

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.NOT_FOUND);
    }
}
```

## Generation Rules

1. **Test Structure**
   - Use @Nested for logical grouping
   - Use @DisplayName for readable names
   - Follow AAA pattern (Arrange-Act-Assert)
   - Use BDD style (given-when-then)

2. **Mocking**
   - Use @Mock for dependencies
   - Use @InjectMocks for SUT
   - Use BDDMockito for readability
   - Capture arguments when needed

3. **Assertions**
   - Use AssertJ for fluent assertions
   - Assert one concept per test
   - Include meaningful messages

4. **Testcontainers**
   - Use @ServiceConnection
   - Define containers as static
   - Use appropriate database version

5. **Controller Tests**
   - Use @WebMvcTest for slicing
   - Mock service layer
   - Test all HTTP status codes
   - Include security tests

## Best Practices

- Test public behavior, not implementation
- One assertion concept per test
- Use descriptive test names
- Clean up test data
- Use test fixtures/factories
- Cover edge cases
- Test error conditions
- Use parameterized tests for variations
