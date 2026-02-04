# Testcontainers

Docker-based integration testing with real databases and services.

## Dependencies

```groovy
dependencies {
    testImplementation 'org.springframework.boot:spring-boot-testcontainers'
    testImplementation 'org.testcontainers:junit-jupiter'
    testImplementation 'org.testcontainers:postgresql'
    testImplementation 'org.testcontainers:kafka'
    testImplementation 'org.testcontainers:localstack'
}
```

## PostgreSQL Container

### Basic Setup

```java
package com.example.app;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.testcontainers.service.connection.ServiceConnection;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

@SpringBootTest
@Testcontainers
class ProductRepositoryContainerTest {

    @Container
    @ServiceConnection
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:15-alpine");

    @Autowired
    private ProductRepository productRepository;

    @Test
    void shouldSaveAndRetrieveProduct() {
        Product product = Product.builder()
            .name("Test Product")
            .sku("TST-0001")
            .price(new BigDecimal("29.99"))
            .stock(100)
            .build();

        Product saved = productRepository.save(product);

        assertThat(saved.getId()).isNotNull();
        assertThat(productRepository.findById(saved.getId())).isPresent();
    }
}
```

### Shared Container Across Tests

```java
package com.example.app.test;

import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.PostgreSQLContainer;

public abstract class AbstractContainerTest {

    static final PostgreSQLContainer<?> postgres;

    static {
        postgres = new PostgreSQLContainer<>("postgres:15-alpine")
            .withDatabaseName("testdb")
            .withUsername("test")
            .withPassword("test")
            .withReuse(true);
        postgres.start();
    }

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
    }
}

// Usage
@SpringBootTest
class ProductServiceTest extends AbstractContainerTest {

    @Autowired
    private ProductService productService;

    @Test
    void shouldCreateProduct() {
        // Test with real PostgreSQL
    }
}
```

### Custom PostgreSQL Configuration

```java
@Container
@ServiceConnection
static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:15-alpine")
    .withDatabaseName("myapp")
    .withUsername("myuser")
    .withPassword("mypassword")
    .withInitScript("db/init.sql")
    .withCommand("postgres -c max_connections=200")
    .withEnv("POSTGRES_INITDB_ARGS", "--encoding=UTF-8");
```

## Redis Container

```java
@SpringBootTest
@Testcontainers
class CacheServiceContainerTest {

    @Container
    @ServiceConnection
    static GenericContainer<?> redis = new GenericContainer<>("redis:7-alpine")
        .withExposedPorts(6379);

    @Autowired
    private CacheService cacheService;

    @Test
    void shouldCacheAndRetrieve() {
        String key = "test-key";
        String value = "test-value";

        cacheService.put(key, value);

        assertThat(cacheService.get(key)).isEqualTo(value);
    }
}
```

## Kafka Container

```java
@SpringBootTest
@Testcontainers
class OrderEventPublisherTest {

    @Container
    static KafkaContainer kafka = new KafkaContainer(
        DockerImageName.parse("confluentinc/cp-kafka:7.4.0")
    );

    @DynamicPropertySource
    static void kafkaProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.kafka.bootstrap-servers", kafka::getBootstrapServers);
    }

    @Autowired
    private OrderEventPublisher eventPublisher;

    @Autowired
    private KafkaTemplate<String, OrderEvent> kafkaTemplate;

    @Test
    void shouldPublishOrderCreatedEvent() throws Exception {
        // Given
        OrderCreatedEvent event = new OrderCreatedEvent(
            UUID.randomUUID(),
            new BigDecimal("100.00"),
            Instant.now()
        );

        // When
        eventPublisher.publish(event);

        // Then - verify with consumer
        Consumer<String, OrderEvent> consumer = createConsumer();
        ConsumerRecords<String, OrderEvent> records = consumer.poll(Duration.ofSeconds(5));

        assertThat(records).hasSize(1);
        assertThat(records.iterator().next().value().getOrderId()).isEqualTo(event.getOrderId());
    }

    private Consumer<String, OrderEvent> createConsumer() {
        Map<String, Object> props = new HashMap<>();
        props.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, kafka.getBootstrapServers());
        props.put(ConsumerConfig.GROUP_ID_CONFIG, "test-consumer");
        props.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "earliest");
        props.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class);
        props.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, JsonDeserializer.class);

        Consumer<String, OrderEvent> consumer = new KafkaConsumer<>(props);
        consumer.subscribe(List.of("order-events"));
        return consumer;
    }
}
```

## LocalStack (AWS Services)

```java
@SpringBootTest
@Testcontainers
class S3ServiceContainerTest {

    @Container
    static LocalStackContainer localstack = new LocalStackContainer(
            DockerImageName.parse("localstack/localstack:2.2")
        )
        .withServices(LocalStackContainer.Service.S3);

    @DynamicPropertySource
    static void awsProperties(DynamicPropertyRegistry registry) {
        registry.add("cloud.aws.s3.endpoint",
            () -> localstack.getEndpointOverride(LocalStackContainer.Service.S3).toString());
        registry.add("cloud.aws.credentials.access-key", localstack::getAccessKey);
        registry.add("cloud.aws.credentials.secret-key", localstack::getSecretKey);
        registry.add("cloud.aws.region.static", localstack::getRegion);
    }

    @Autowired
    private S3Service s3Service;

    @BeforeEach
    void setUp() {
        // Create bucket before tests
        try {
            localstack.execInContainer(
                "awslocal", "s3", "mb", "s3://test-bucket"
            );
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    @Test
    void shouldUploadAndDownloadFile() {
        // Given
        byte[] content = "test content".getBytes();
        String key = "test-file.txt";

        // When
        s3Service.upload("test-bucket", key, content);
        byte[] downloaded = s3Service.download("test-bucket", key);

        // Then
        assertThat(downloaded).isEqualTo(content);
    }
}
```

## Elasticsearch Container

```java
@SpringBootTest
@Testcontainers
class ProductSearchContainerTest {

    @Container
    static ElasticsearchContainer elasticsearch = new ElasticsearchContainer(
        "docker.elastic.co/elasticsearch/elasticsearch:8.9.0"
    )
    .withEnv("xpack.security.enabled", "false");

    @DynamicPropertySource
    static void elasticsearchProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.elasticsearch.uris", elasticsearch::getHttpHostAddress);
    }

    @Autowired
    private ProductSearchService searchService;

    @Test
    void shouldIndexAndSearchProduct() {
        // Given
        Product product = Product.builder()
            .id(UUID.randomUUID())
            .name("Wireless Headphones")
            .description("High quality wireless headphones")
            .build();

        // When
        searchService.index(product);

        // Wait for indexing
        await().atMost(5, TimeUnit.SECONDS).until(() ->
            !searchService.search("wireless").isEmpty()
        );

        // Then
        List<Product> results = searchService.search("wireless");
        assertThat(results).hasSize(1);
        assertThat(results.get(0).getName()).isEqualTo("Wireless Headphones");
    }
}
```

## Multiple Containers

```java
@SpringBootTest
@Testcontainers
class FullStackContainerTest {

    @Container
    @ServiceConnection
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:15-alpine");

    @Container
    static GenericContainer<?> redis = new GenericContainer<>("redis:7-alpine")
        .withExposedPorts(6379);

    @Container
    static KafkaContainer kafka = new KafkaContainer(
        DockerImageName.parse("confluentinc/cp-kafka:7.4.0")
    );

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.data.redis.host", redis::getHost);
        registry.add("spring.data.redis.port", redis::getFirstMappedPort);
        registry.add("spring.kafka.bootstrap-servers", kafka::getBootstrapServers);
    }

    @Autowired
    private OrderService orderService;

    @Test
    void shouldCreateOrderWithCacheAndEvents() {
        // Full integration test with all services
    }
}
```

## Docker Compose Integration

```java
@SpringBootTest
@Testcontainers
class DockerComposeTest {

    @Container
    static DockerComposeContainer<?> environment =
        new DockerComposeContainer<>(new File("src/test/resources/docker-compose-test.yml"))
            .withExposedService("postgres", 5432)
            .withExposedService("redis", 6379)
            .withExposedService("kafka", 9092)
            .waitingFor("postgres", Wait.forListeningPort())
            .waitingFor("redis", Wait.forListeningPort());

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", () ->
            String.format("jdbc:postgresql://%s:%d/testdb",
                environment.getServiceHost("postgres", 5432),
                environment.getServicePort("postgres", 5432)));
        registry.add("spring.datasource.username", () -> "test");
        registry.add("spring.datasource.password", () -> "test");
    }
}
```

### docker-compose-test.yml

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: testdb
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
    ports:
      - "5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379"

  kafka:
    image: confluentinc/cp-kafka:7.4.0
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092
    ports:
      - "9092"
    depends_on:
      - zookeeper

  zookeeper:
    image: confluentinc/cp-zookeeper:7.4.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
```

## Network Configuration

```java
@Testcontainers
class NetworkContainerTest {

    static Network network = Network.newNetwork();

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:15-alpine")
        .withNetwork(network)
        .withNetworkAliases("postgres");

    @Container
    static GenericContainer<?> app = new GenericContainer<>("myapp:latest")
        .withNetwork(network)
        .withEnv("DB_HOST", "postgres")
        .withEnv("DB_PORT", "5432")
        .dependsOn(postgres);
}
```

## Wait Strategies

```java
@Container
static GenericContainer<?> customService = new GenericContainer<>("myservice:latest")
    .withExposedPorts(8080)
    // Wait for HTTP endpoint
    .waitingFor(Wait.forHttp("/health")
        .forPort(8080)
        .forStatusCode(200)
        .withStartupTimeout(Duration.ofMinutes(2)))
    // Or wait for log message
    .waitingFor(Wait.forLogMessage(".*Application started.*", 1));

@Container
static GenericContainer<?> dbContainer = new GenericContainer<>("postgres:15-alpine")
    .withExposedPorts(5432)
    // Wait for specific log message
    .waitingFor(Wait.forLogMessage(".*database system is ready to accept connections.*", 1))
    // With health check
    .waitingFor(Wait.forHealthcheck());
```

## Container Lifecycle Callbacks

```java
@SpringBootTest
@Testcontainers
class ContainerLifecycleTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:15-alpine") {
        @Override
        public void start() {
            super.start();
            System.out.println("PostgreSQL started at: " + getJdbcUrl());
        }

        @Override
        public void stop() {
            System.out.println("Stopping PostgreSQL...");
            super.stop();
        }
    };

    @BeforeAll
    static void beforeAll() {
        // Container is already started at this point
        execSqlScript(postgres, "classpath:db/schema.sql");
    }

    @AfterAll
    static void afterAll() {
        // Container will be stopped after this
    }

    private static void execSqlScript(PostgreSQLContainer<?> container, String script) {
        // Execute SQL script against container
    }
}
```

## Reusable Containers

```java
// Enable in ~/.testcontainers.properties:
// testcontainers.reuse.enable=true

@Container
static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:15-alpine")
    .withReuse(true)  // Reuse container across test runs
    .withLabel("reuse.UUID", "my-postgres-container");
```

## Test Configuration Class

```java
@TestConfiguration
public class TestContainersConfig {

    @Bean
    @ServiceConnection
    PostgreSQLContainer<?> postgresContainer() {
        return new PostgreSQLContainer<>("postgres:15-alpine")
            .withDatabaseName("testdb");
    }

    @Bean
    @ServiceConnection(name = "redis")
    GenericContainer<?> redisContainer() {
        return new GenericContainer<>("redis:7-alpine")
            .withExposedPorts(6379);
    }
}

// Usage
@SpringBootTest
@Import(TestContainersConfig.class)
class ServiceTest {
    // Tests with auto-configured containers
}
```

## CI/CD Configuration

```yaml
# GitHub Actions
name: Tests with Testcontainers

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up JDK 17
        uses: actions/setup-java@v4
        with:
          java-version: '17'
          distribution: 'temurin'

      - name: Run tests
        run: ./gradlew test
        env:
          TESTCONTAINERS_RYUK_DISABLED: true
```

## Best Practices

1. **Use @ServiceConnection** - Automatic property configuration
2. **Share containers** - Static containers for faster tests
3. **Enable reuse** - Faster local development
4. **Use appropriate wait strategies** - Avoid flaky tests
5. **Clean data between tests** - @Transactional or explicit cleanup
6. **Pin image versions** - Reproducible builds
7. **Use Alpine images** - Smaller, faster to pull
8. **Configure timeouts** - Handle slow CI environments
9. **Use networks** - For container-to-container communication
10. **Monitor resources** - Containers consume memory/CPU
