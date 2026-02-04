# Unit Testing

JUnit 5 and Mockito patterns for Spring Boot unit testing.

## Dependencies

```groovy
dependencies {
    testImplementation 'org.springframework.boot:spring-boot-starter-test'
    testImplementation 'org.mockito:mockito-junit-jupiter'
}
```

## Service Layer Testing

### Basic Service Test

```java
package com.example.app.service;

import com.example.app.domain.entity.Product;
import com.example.app.exception.ResourceNotFoundException;
import com.example.app.repository.ProductRepository;
import com.example.app.web.dto.ProductRequest;
import com.example.app.web.dto.ProductResponse;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Captor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.math.BigDecimal;
import java.util.Optional;
import java.util.UUID;

import static org.assertj.core.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@DisplayName("ProductService")
class ProductServiceTest {

    @Mock
    private ProductRepository productRepository;

    @Mock
    private ProductMapper productMapper;

    @InjectMocks
    private ProductService productService;

    @Captor
    private ArgumentCaptor<Product> productCaptor;

    private Product testProduct;
    private ProductRequest testRequest;
    private UUID productId;

    @BeforeEach
    void setUp() {
        productId = UUID.randomUUID();
        testProduct = Product.builder()
            .id(productId)
            .name("Test Product")
            .sku("TST-0001")
            .price(new BigDecimal("29.99"))
            .stock(100)
            .build();

        testRequest = new ProductRequest(
            "Test Product",
            "Description",
            "TST-0001",
            new BigDecimal("29.99"),
            100,
            null
        );
    }

    @Nested
    @DisplayName("findById")
    class FindById {

        @Test
        @DisplayName("should return product when found")
        void shouldReturnProductWhenFound() {
            // Given
            when(productRepository.findById(productId)).thenReturn(Optional.of(testProduct));
            when(productMapper.toResponse(testProduct))
                .thenReturn(new ProductResponse(productId, "Test Product", "TST-0001",
                    new BigDecimal("29.99"), 100));

            // When
            ProductResponse result = productService.findById(productId);

            // Then
            assertThat(result).isNotNull();
            assertThat(result.id()).isEqualTo(productId);
            assertThat(result.name()).isEqualTo("Test Product");
            verify(productRepository).findById(productId);
        }

        @Test
        @DisplayName("should throw exception when not found")
        void shouldThrowExceptionWhenNotFound() {
            // Given
            when(productRepository.findById(productId)).thenReturn(Optional.empty());

            // When/Then
            assertThatThrownBy(() -> productService.findById(productId))
                .isInstanceOf(ResourceNotFoundException.class)
                .hasMessageContaining("Product")
                .hasMessageContaining(productId.toString());

            verify(productRepository).findById(productId);
            verifyNoMoreInteractions(productMapper);
        }
    }

    @Nested
    @DisplayName("create")
    class Create {

        @Test
        @DisplayName("should create product successfully")
        void shouldCreateProductSuccessfully() {
            // Given
            when(productRepository.existsBySku(testRequest.sku())).thenReturn(false);
            when(productMapper.toEntity(testRequest)).thenReturn(testProduct);
            when(productRepository.save(any(Product.class))).thenReturn(testProduct);
            when(productMapper.toResponse(testProduct))
                .thenReturn(new ProductResponse(productId, "Test Product", "TST-0001",
                    new BigDecimal("29.99"), 100));

            // When
            ProductResponse result = productService.create(testRequest);

            // Then
            assertThat(result).isNotNull();
            assertThat(result.sku()).isEqualTo("TST-0001");

            verify(productRepository).existsBySku(testRequest.sku());
            verify(productRepository).save(productCaptor.capture());

            Product savedProduct = productCaptor.getValue();
            assertThat(savedProduct.getName()).isEqualTo("Test Product");
        }

        @Test
        @DisplayName("should throw exception when SKU already exists")
        void shouldThrowExceptionWhenSkuExists() {
            // Given
            when(productRepository.existsBySku(testRequest.sku())).thenReturn(true);

            // When/Then
            assertThatThrownBy(() -> productService.create(testRequest))
                .isInstanceOf(BusinessException.class)
                .hasMessageContaining("SKU already exists");

            verify(productRepository).existsBySku(testRequest.sku());
            verify(productRepository, never()).save(any());
        }
    }

    @Nested
    @DisplayName("update")
    class Update {

        @Test
        @DisplayName("should update product successfully")
        void shouldUpdateProductSuccessfully() {
            // Given
            when(productRepository.findById(productId)).thenReturn(Optional.of(testProduct));
            when(productRepository.save(any(Product.class))).thenReturn(testProduct);
            when(productMapper.toResponse(testProduct))
                .thenReturn(new ProductResponse(productId, "Updated Name", "TST-0001",
                    new BigDecimal("39.99"), 100));

            ProductRequest updateRequest = new ProductRequest(
                "Updated Name", "Updated Description", "TST-0001",
                new BigDecimal("39.99"), 100, null
            );

            // When
            ProductResponse result = productService.update(productId, updateRequest);

            // Then
            assertThat(result.name()).isEqualTo("Updated Name");
            verify(productRepository).save(productCaptor.capture());

            Product updatedProduct = productCaptor.getValue();
            assertThat(updatedProduct.getName()).isEqualTo("Updated Name");
        }
    }

    @Nested
    @DisplayName("delete")
    class Delete {

        @Test
        @DisplayName("should delete product when exists")
        void shouldDeleteProductWhenExists() {
            // Given
            when(productRepository.existsById(productId)).thenReturn(true);

            // When
            productService.delete(productId);

            // Then
            verify(productRepository).deleteById(productId);
        }

        @Test
        @DisplayName("should throw exception when product not found")
        void shouldThrowExceptionWhenNotFound() {
            // Given
            when(productRepository.existsById(productId)).thenReturn(false);

            // When/Then
            assertThatThrownBy(() -> productService.delete(productId))
                .isInstanceOf(ResourceNotFoundException.class);

            verify(productRepository, never()).deleteById(any());
        }
    }
}
```

### Testing with Argument Matchers

```java
@ExtendWith(MockitoExtension.class)
class OrderServiceTest {

    @Mock
    private OrderRepository orderRepository;

    @Mock
    private ProductRepository productRepository;

    @Mock
    private NotificationService notificationService;

    @InjectMocks
    private OrderService orderService;

    @Test
    void shouldCreateOrderWithMultipleItems() {
        // Given
        Product product1 = createProduct(UUID.randomUUID(), "Product 1", 100);
        Product product2 = createProduct(UUID.randomUUID(), "Product 2", 50);

        when(productRepository.findById(product1.getId())).thenReturn(Optional.of(product1));
        when(productRepository.findById(product2.getId())).thenReturn(Optional.of(product2));
        when(orderRepository.save(any(Order.class))).thenAnswer(invocation -> {
            Order order = invocation.getArgument(0);
            order.setId(UUID.randomUUID());
            return order;
        });

        CreateOrderRequest request = new CreateOrderRequest(
            List.of(
                new OrderItemRequest(product1.getId(), 2),
                new OrderItemRequest(product2.getId(), 3)
            )
        );

        // When
        OrderResponse result = orderService.createOrder(request);

        // Then
        assertThat(result).isNotNull();
        verify(orderRepository).save(argThat(order ->
            order.getItems().size() == 2 &&
            order.getStatus() == OrderStatus.PENDING
        ));
        verify(notificationService).sendOrderConfirmation(any());
    }

    @Test
    void shouldNotSendNotificationOnFailure() {
        // Given
        when(productRepository.findById(any())).thenReturn(Optional.empty());

        CreateOrderRequest request = new CreateOrderRequest(
            List.of(new OrderItemRequest(UUID.randomUUID(), 1))
        );

        // When/Then
        assertThatThrownBy(() -> orderService.createOrder(request))
            .isInstanceOf(ResourceNotFoundException.class);

        verify(notificationService, never()).sendOrderConfirmation(any());
    }
}
```

## Controller Testing with MockMvc

### Basic Controller Test

```java
@WebMvcTest(ProductController.class)
class ProductControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @MockBean
    private ProductService productService;

    private UUID productId;
    private ProductResponse productResponse;

    @BeforeEach
    void setUp() {
        productId = UUID.randomUUID();
        productResponse = new ProductResponse(
            productId, "Test Product", "TST-0001",
            new BigDecimal("29.99"), 100
        );
    }

    @Nested
    @DisplayName("GET /api/v1/products/{id}")
    class GetById {

        @Test
        @DisplayName("should return 200 with product")
        void shouldReturn200WithProduct() throws Exception {
            when(productService.findById(productId)).thenReturn(productResponse);

            mockMvc.perform(get("/api/v1/products/{id}", productId)
                    .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.id").value(productId.toString()))
                .andExpect(jsonPath("$.name").value("Test Product"))
                .andExpect(jsonPath("$.price").value(29.99));
        }

        @Test
        @DisplayName("should return 404 when not found")
        void shouldReturn404WhenNotFound() throws Exception {
            when(productService.findById(productId))
                .thenThrow(new ResourceNotFoundException("Product", productId));

            mockMvc.perform(get("/api/v1/products/{id}", productId))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.code").value("RESOURCE_NOT_FOUND"));
        }
    }

    @Nested
    @DisplayName("POST /api/v1/products")
    class Create {

        @Test
        @DisplayName("should return 201 when created")
        void shouldReturn201WhenCreated() throws Exception {
            ProductRequest request = new ProductRequest(
                "New Product", "Description", "NEW-0001",
                new BigDecimal("49.99"), 50, null
            );

            when(productService.create(any(ProductRequest.class))).thenReturn(productResponse);

            mockMvc.perform(post("/api/v1/products")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.id").exists());
        }

        @Test
        @DisplayName("should return 400 for invalid request")
        void shouldReturn400ForInvalidRequest() throws Exception {
            ProductRequest invalidRequest = new ProductRequest(
                "", null, "INVALID", // Empty name, null description
                new BigDecimal("-1"), // Negative price
                -10, // Negative stock
                null
            );

            mockMvc.perform(post("/api/v1/products")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(objectMapper.writeValueAsString(invalidRequest)))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.code").value("VALIDATION_ERROR"))
                .andExpect(jsonPath("$.fieldErrors.name").exists())
                .andExpect(jsonPath("$.fieldErrors.price").exists());
        }
    }

    @Nested
    @DisplayName("GET /api/v1/products")
    class List {

        @Test
        @DisplayName("should return paginated results")
        void shouldReturnPaginatedResults() throws Exception {
            Page<ProductResponse> page = new PageImpl<>(
                List.of(productResponse),
                PageRequest.of(0, 20),
                1
            );

            when(productService.findAll(any(Pageable.class))).thenReturn(page);

            mockMvc.perform(get("/api/v1/products")
                    .param("page", "0")
                    .param("size", "20"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content").isArray())
                .andExpect(jsonPath("$.content[0].id").value(productId.toString()))
                .andExpect(jsonPath("$.totalElements").value(1))
                .andExpect(jsonPath("$.totalPages").value(1));
        }
    }
}
```

### Controller Test with Security

```java
@WebMvcTest(ProductController.class)
@Import(SecurityConfig.class)
class ProductControllerSecurityTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private ProductService productService;

    @MockBean
    private JwtService jwtService;

    @MockBean
    private UserDetailsService userDetailsService;

    @Test
    @WithMockUser(roles = "USER")
    void shouldAllowReadForAuthenticatedUser() throws Exception {
        mockMvc.perform(get("/api/v1/products"))
            .andExpect(status().isOk());
    }

    @Test
    void shouldReturn401ForUnauthenticatedRequest() throws Exception {
        mockMvc.perform(get("/api/v1/products"))
            .andExpect(status().isUnauthorized());
    }

    @Test
    @WithMockUser(roles = "USER")
    void shouldReturn403ForUnauthorizedAction() throws Exception {
        mockMvc.perform(delete("/api/v1/products/{id}", UUID.randomUUID()))
            .andExpect(status().isForbidden());
    }

    @Test
    @WithMockUser(roles = "ADMIN")
    void shouldAllowDeleteForAdmin() throws Exception {
        UUID productId = UUID.randomUUID();
        doNothing().when(productService).delete(productId);

        mockMvc.perform(delete("/api/v1/products/{id}", productId))
            .andExpect(status().isNoContent());
    }
}
```

## Testing Utilities

### Test Data Builder

```java
public class TestDataBuilder {

    public static ProductBuilder aProduct() {
        return new ProductBuilder();
    }

    public static OrderBuilder anOrder() {
        return new OrderBuilder();
    }

    public static class ProductBuilder {
        private UUID id = UUID.randomUUID();
        private String name = "Test Product";
        private String sku = "TST-" + RandomString.make(4).toUpperCase();
        private BigDecimal price = new BigDecimal("29.99");
        private int stock = 100;
        private ProductStatus status = ProductStatus.ACTIVE;

        public ProductBuilder withId(UUID id) {
            this.id = id;
            return this;
        }

        public ProductBuilder withName(String name) {
            this.name = name;
            return this;
        }

        public ProductBuilder withSku(String sku) {
            this.sku = sku;
            return this;
        }

        public ProductBuilder withPrice(BigDecimal price) {
            this.price = price;
            return this;
        }

        public ProductBuilder withStock(int stock) {
            this.stock = stock;
            return this;
        }

        public ProductBuilder withStatus(ProductStatus status) {
            this.status = status;
            return this;
        }

        public Product build() {
            return Product.builder()
                .id(id)
                .name(name)
                .sku(sku)
                .price(price)
                .stock(stock)
                .status(status)
                .build();
        }
    }

    public static class OrderBuilder {
        private UUID id = UUID.randomUUID();
        private List<OrderItem> items = new ArrayList<>();
        private OrderStatus status = OrderStatus.PENDING;

        public OrderBuilder withId(UUID id) {
            this.id = id;
            return this;
        }

        public OrderBuilder withItem(Product product, int quantity) {
            items.add(OrderItem.builder()
                .product(product)
                .quantity(quantity)
                .unitPrice(product.getPrice())
                .build());
            return this;
        }

        public OrderBuilder withStatus(OrderStatus status) {
            this.status = status;
            return this;
        }

        public Order build() {
            return Order.builder()
                .id(id)
                .items(items)
                .status(status)
                .build();
        }
    }
}
```

### Custom Assertions

```java
public class ProductAssert extends AbstractAssert<ProductAssert, Product> {

    public ProductAssert(Product actual) {
        super(actual, ProductAssert.class);
    }

    public static ProductAssert assertThat(Product actual) {
        return new ProductAssert(actual);
    }

    public ProductAssert hasName(String name) {
        isNotNull();
        if (!Objects.equals(actual.getName(), name)) {
            failWithMessage("Expected name to be <%s> but was <%s>",
                name, actual.getName());
        }
        return this;
    }

    public ProductAssert hasSku(String sku) {
        isNotNull();
        if (!Objects.equals(actual.getSku(), sku)) {
            failWithMessage("Expected SKU to be <%s> but was <%s>",
                sku, actual.getSku());
        }
        return this;
    }

    public ProductAssert hasStock(int stock) {
        isNotNull();
        if (actual.getStock() != stock) {
            failWithMessage("Expected stock to be <%d> but was <%d>",
                stock, actual.getStock());
        }
        return this;
    }

    public ProductAssert hasStockGreaterThan(int minimum) {
        isNotNull();
        if (actual.getStock() <= minimum) {
            failWithMessage("Expected stock to be greater than <%d> but was <%d>",
                minimum, actual.getStock());
        }
        return this;
    }

    public ProductAssert isActive() {
        isNotNull();
        if (actual.getStatus() != ProductStatus.ACTIVE) {
            failWithMessage("Expected product to be ACTIVE but was <%s>",
                actual.getStatus());
        }
        return this;
    }
}
```

## Parameterized Tests

```java
@ExtendWith(MockitoExtension.class)
class PriceCalculatorTest {

    @InjectMocks
    private PriceCalculator priceCalculator;

    @ParameterizedTest
    @DisplayName("should calculate discount correctly")
    @CsvSource({
        "100.00, 10, 90.00",
        "50.00, 20, 40.00",
        "200.00, 50, 100.00",
        "75.00, 0, 75.00"
    })
    void shouldCalculateDiscountCorrectly(
            BigDecimal originalPrice,
            int discountPercent,
            BigDecimal expectedPrice) {

        BigDecimal result = priceCalculator.applyDiscount(originalPrice, discountPercent);

        assertThat(result).isEqualByComparingTo(expectedPrice);
    }

    @ParameterizedTest
    @DisplayName("should throw exception for invalid discount")
    @ValueSource(ints = {-1, -10, 101, 150})
    void shouldThrowExceptionForInvalidDiscount(int invalidDiscount) {
        BigDecimal price = new BigDecimal("100.00");

        assertThatThrownBy(() -> priceCalculator.applyDiscount(price, invalidDiscount))
            .isInstanceOf(IllegalArgumentException.class)
            .hasMessageContaining("Discount must be between 0 and 100");
    }

    @ParameterizedTest
    @DisplayName("should apply tax correctly for different regions")
    @MethodSource("provideRegionTaxRates")
    void shouldApplyTaxCorrectly(String region, BigDecimal price, BigDecimal expectedTotal) {
        BigDecimal result = priceCalculator.calculateWithTax(price, region);

        assertThat(result).isEqualByComparingTo(expectedTotal);
    }

    private static Stream<Arguments> provideRegionTaxRates() {
        return Stream.of(
            Arguments.of("US-CA", new BigDecimal("100.00"), new BigDecimal("107.25")),
            Arguments.of("US-TX", new BigDecimal("100.00"), new BigDecimal("106.25")),
            Arguments.of("EU-DE", new BigDecimal("100.00"), new BigDecimal("119.00")),
            Arguments.of("EU-FR", new BigDecimal("100.00"), new BigDecimal("120.00"))
        );
    }
}
```

## Async Testing

```java
@ExtendWith(MockitoExtension.class)
class NotificationServiceTest {

    @Mock
    private EmailSender emailSender;

    @Mock
    private PushNotificationSender pushSender;

    @InjectMocks
    private NotificationService notificationService;

    @Test
    void shouldSendNotificationAsync() throws Exception {
        // Given
        CompletableFuture<Void> emailFuture = CompletableFuture.completedFuture(null);
        CompletableFuture<Void> pushFuture = CompletableFuture.completedFuture(null);

        when(emailSender.sendAsync(any())).thenReturn(emailFuture);
        when(pushSender.sendAsync(any())).thenReturn(pushFuture);

        Notification notification = new Notification("user@example.com", "Test", "Message");

        // When
        CompletableFuture<Void> result = notificationService.sendAsync(notification);

        // Then
        result.get(5, TimeUnit.SECONDS); // Wait for completion

        verify(emailSender).sendAsync(any());
        verify(pushSender).sendAsync(any());
    }

    @Test
    void shouldHandleAsyncFailure() {
        // Given
        CompletableFuture<Void> failedFuture = new CompletableFuture<>();
        failedFuture.completeExceptionally(new RuntimeException("Send failed"));

        when(emailSender.sendAsync(any())).thenReturn(failedFuture);

        Notification notification = new Notification("user@example.com", "Test", "Message");

        // When
        CompletableFuture<Void> result = notificationService.sendAsync(notification);

        // Then
        assertThatThrownBy(() -> result.get(5, TimeUnit.SECONDS))
            .hasCauseInstanceOf(RuntimeException.class);
    }
}
```

## Best Practices

1. **Use @DisplayName** - Clear test descriptions
2. **Group with @Nested** - Organize tests by method/scenario
3. **Follow AAA pattern** - Arrange, Act, Assert
4. **Test one thing** - Single assertion focus per test
5. **Use builders** - Consistent test data creation
6. **Mock only external deps** - Don't mock the system under test
7. **Verify interactions** - Check method calls and arguments
8. **Test edge cases** - Null, empty, boundary values
9. **Use parameterized tests** - For multiple input scenarios
10. **Keep tests independent** - No shared mutable state
