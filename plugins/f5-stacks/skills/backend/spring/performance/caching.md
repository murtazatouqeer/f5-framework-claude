# Caching

Spring Boot caching patterns with Redis and local caching.

## Dependencies

```groovy
dependencies {
    implementation 'org.springframework.boot:spring-boot-starter-cache'
    implementation 'org.springframework.boot:spring-boot-starter-data-redis'
    implementation 'com.github.ben-manes.caffeine:caffeine'
}
```

## Configuration

### Redis Cache Configuration

```yaml
# application.yml
spring:
  data:
    redis:
      host: ${REDIS_HOST:localhost}
      port: ${REDIS_PORT:6379}
      password: ${REDIS_PASSWORD:}
      timeout: 2000ms

  cache:
    type: redis
    redis:
      time-to-live: 3600000  # 1 hour
      cache-null-values: false
      key-prefix: "myapp:"
      use-key-prefix: true
```

### Redis Cache Config Class

```java
package com.example.app.config;

import com.fasterxml.jackson.annotation.JsonTypeInfo;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.jsontype.impl.LaissezFaireSubTypeValidator;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import org.springframework.cache.CacheManager;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.cache.RedisCacheConfiguration;
import org.springframework.data.redis.cache.RedisCacheManager;
import org.springframework.data.redis.connection.RedisConnectionFactory;
import org.springframework.data.redis.serializer.GenericJackson2JsonRedisSerializer;
import org.springframework.data.redis.serializer.RedisSerializationContext;
import org.springframework.data.redis.serializer.StringRedisSerializer;

import java.time.Duration;
import java.util.HashMap;
import java.util.Map;

@Configuration
@EnableCaching
public class RedisCacheConfig {

    @Bean
    public CacheManager cacheManager(RedisConnectionFactory connectionFactory) {
        RedisCacheConfiguration defaultConfig = RedisCacheConfiguration.defaultCacheConfig()
            .entryTtl(Duration.ofHours(1))
            .serializeKeysWith(RedisSerializationContext.SerializationPair
                .fromSerializer(new StringRedisSerializer()))
            .serializeValuesWith(RedisSerializationContext.SerializationPair
                .fromSerializer(createJsonSerializer()))
            .disableCachingNullValues();

        Map<String, RedisCacheConfiguration> cacheConfigs = new HashMap<>();
        cacheConfigs.put("products", defaultConfig.entryTtl(Duration.ofMinutes(30)));
        cacheConfigs.put("users", defaultConfig.entryTtl(Duration.ofMinutes(15)));
        cacheConfigs.put("categories", defaultConfig.entryTtl(Duration.ofHours(24)));
        cacheConfigs.put("short-lived", defaultConfig.entryTtl(Duration.ofMinutes(5)));

        return RedisCacheManager.builder(connectionFactory)
            .cacheDefaults(defaultConfig)
            .withInitialCacheConfigurations(cacheConfigs)
            .transactionAware()
            .build();
    }

    private GenericJackson2JsonRedisSerializer createJsonSerializer() {
        ObjectMapper objectMapper = new ObjectMapper()
            .registerModule(new JavaTimeModule())
            .activateDefaultTyping(
                LaissezFaireSubTypeValidator.instance,
                ObjectMapper.DefaultTyping.NON_FINAL,
                JsonTypeInfo.As.PROPERTY
            );
        return new GenericJackson2JsonRedisSerializer(objectMapper);
    }
}
```

### Caffeine Local Cache

```java
@Configuration
@EnableCaching
public class CaffeineCacheConfig {

    @Bean
    public CacheManager cacheManager() {
        CaffeineCacheManager cacheManager = new CaffeineCacheManager();
        cacheManager.setCaffeine(caffeineCacheBuilder());
        return cacheManager;
    }

    private Caffeine<Object, Object> caffeineCacheBuilder() {
        return Caffeine.newBuilder()
            .initialCapacity(100)
            .maximumSize(500)
            .expireAfterWrite(Duration.ofMinutes(10))
            .expireAfterAccess(Duration.ofMinutes(5))
            .recordStats();
    }

    @Bean
    public CacheManager multiCacheManager() {
        SimpleCacheManager cacheManager = new SimpleCacheManager();
        cacheManager.setCaches(List.of(
            buildCache("products", 500, Duration.ofMinutes(30)),
            buildCache("users", 200, Duration.ofMinutes(15)),
            buildCache("categories", 100, Duration.ofHours(24))
        ));
        return cacheManager;
    }

    private CaffeineCache buildCache(String name, int maxSize, Duration ttl) {
        return new CaffeineCache(name,
            Caffeine.newBuilder()
                .maximumSize(maxSize)
                .expireAfterWrite(ttl)
                .recordStats()
                .build());
    }
}
```

## Basic Cache Annotations

### @Cacheable

```java
@Service
@RequiredArgsConstructor
public class ProductService {

    private final ProductRepository productRepository;
    private final ProductMapper productMapper;

    @Cacheable(value = "products", key = "#id")
    public ProductResponse findById(UUID id) {
        return productRepository.findById(id)
            .map(productMapper::toResponse)
            .orElseThrow(() -> new ResourceNotFoundException("Product", id));
    }

    @Cacheable(value = "products", key = "#sku")
    public ProductResponse findBySku(String sku) {
        return productRepository.findBySku(sku)
            .map(productMapper::toResponse)
            .orElseThrow(() -> new ResourceNotFoundException("Product", sku));
    }

    // Conditional caching
    @Cacheable(value = "products", key = "#id", condition = "#result != null")
    public ProductResponse findByIdOptional(UUID id) {
        return productRepository.findById(id)
            .map(productMapper::toResponse)
            .orElse(null);
    }

    // Unless - don't cache if condition is true
    @Cacheable(value = "products", key = "#id", unless = "#result.stock == 0")
    public ProductResponse findByIdUnlessOutOfStock(UUID id) {
        return productRepository.findById(id)
            .map(productMapper::toResponse)
            .orElseThrow();
    }

    // Cache with SpEL key
    @Cacheable(value = "products",
               key = "'category:' + #categoryId + ':page:' + #pageable.pageNumber")
    public Page<ProductResponse> findByCategory(UUID categoryId, Pageable pageable) {
        return productRepository.findByCategoryId(categoryId, pageable)
            .map(productMapper::toResponse);
    }
}
```

### @CachePut

```java
@Service
public class ProductService {

    @CachePut(value = "products", key = "#result.id")
    public ProductResponse create(ProductRequest request) {
        Product product = productMapper.toEntity(request);
        Product saved = productRepository.save(product);
        return productMapper.toResponse(saved);
    }

    @CachePut(value = "products", key = "#id")
    public ProductResponse update(UUID id, ProductRequest request) {
        Product product = productRepository.findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("Product", id));

        productMapper.updateEntity(product, request);
        Product updated = productRepository.save(product);
        return productMapper.toResponse(updated);
    }
}
```

### @CacheEvict

```java
@Service
public class ProductService {

    @CacheEvict(value = "products", key = "#id")
    public void delete(UUID id) {
        productRepository.deleteById(id);
    }

    @CacheEvict(value = "products", allEntries = true)
    public void clearProductCache() {
        // Clears all entries in 'products' cache
    }

    // Evict before method execution
    @CacheEvict(value = "products", key = "#id", beforeInvocation = true)
    public void deleteAndCleanup(UUID id) {
        // Cache evicted before this runs
        productRepository.deleteById(id);
        // Additional cleanup
    }

    // Evict multiple caches
    @Caching(evict = {
        @CacheEvict(value = "products", key = "#id"),
        @CacheEvict(value = "products", key = "'category:' + #categoryId + ':*'")
    })
    public void deleteWithCategoryEviction(UUID id, UUID categoryId) {
        productRepository.deleteById(id);
    }
}
```

### @Caching - Combined Operations

```java
@Service
public class ProductService {

    @Caching(
        cacheable = {
            @Cacheable(value = "products", key = "#id")
        },
        put = {
            @CachePut(value = "products-by-sku", key = "#result.sku")
        }
    )
    public ProductResponse findAndCacheMultiple(UUID id) {
        return productRepository.findById(id)
            .map(productMapper::toResponse)
            .orElseThrow();
    }

    @Caching(evict = {
        @CacheEvict(value = "products", key = "#id"),
        @CacheEvict(value = "products-by-sku", key = "#sku"),
        @CacheEvict(value = "products-by-category", key = "#categoryId", condition = "#categoryId != null")
    })
    public void evictAll(UUID id, String sku, UUID categoryId) {
        // Evicts from multiple caches
    }
}
```

## Custom Key Generator

```java
@Configuration
public class CacheKeyConfig {

    @Bean
    public KeyGenerator productKeyGenerator() {
        return (target, method, params) -> {
            StringBuilder sb = new StringBuilder();
            sb.append(target.getClass().getSimpleName());
            sb.append(":");
            sb.append(method.getName());
            for (Object param : params) {
                sb.append(":").append(param.toString());
            }
            return sb.toString();
        };
    }

    @Bean
    public KeyGenerator hashKeyGenerator() {
        return (target, method, params) -> {
            String key = target.getClass().getSimpleName() + ":" +
                        method.getName() + ":" +
                        Arrays.deepHashCode(params);
            return DigestUtils.md5DigestAsHex(key.getBytes());
        };
    }
}

// Usage
@Cacheable(value = "products", keyGenerator = "productKeyGenerator")
public ProductResponse findWithCustomKey(UUID id, String tenant) {
    // Key: ProductService:findWithCustomKey:uuid:tenant
    return productRepository.findByIdAndTenant(id, tenant)
        .map(productMapper::toResponse)
        .orElseThrow();
}
```

## Programmatic Caching

```java
@Service
@RequiredArgsConstructor
public class ProductCacheService {

    private final CacheManager cacheManager;
    private final ProductRepository productRepository;
    private final ProductMapper productMapper;

    public ProductResponse getProduct(UUID id) {
        Cache cache = cacheManager.getCache("products");
        if (cache == null) {
            return fetchFromDatabase(id);
        }

        ProductResponse cached = cache.get(id, ProductResponse.class);
        if (cached != null) {
            return cached;
        }

        ProductResponse product = fetchFromDatabase(id);
        cache.put(id, product);
        return product;
    }

    public void evictProduct(UUID id) {
        Cache cache = cacheManager.getCache("products");
        if (cache != null) {
            cache.evict(id);
        }
    }

    public void warmupCache() {
        Cache cache = cacheManager.getCache("products");
        if (cache == null) return;

        List<Product> activeProducts = productRepository
            .findByStatus(ProductStatus.ACTIVE);

        for (Product product : activeProducts) {
            ProductResponse response = productMapper.toResponse(product);
            cache.put(product.getId(), response);
        }
    }

    public CacheStats getCacheStats() {
        Cache cache = cacheManager.getCache("products");
        if (cache instanceof CaffeineCache caffeineCache) {
            com.github.benmanes.caffeine.cache.stats.CacheStats stats =
                caffeineCache.getNativeCache().stats();
            return new CacheStats(
                stats.hitCount(),
                stats.missCount(),
                stats.hitRate(),
                stats.evictionCount()
            );
        }
        return null;
    }

    private ProductResponse fetchFromDatabase(UUID id) {
        return productRepository.findById(id)
            .map(productMapper::toResponse)
            .orElseThrow(() -> new ResourceNotFoundException("Product", id));
    }
}

public record CacheStats(
    long hitCount,
    long missCount,
    double hitRate,
    long evictionCount
) {}
```

## Cache Aside Pattern

```java
@Service
@RequiredArgsConstructor
public class CacheAsideService {

    private final RedisTemplate<String, Object> redisTemplate;
    private final ProductRepository productRepository;
    private final ObjectMapper objectMapper;

    private static final String CACHE_PREFIX = "product:";
    private static final Duration TTL = Duration.ofHours(1);

    public ProductResponse getProduct(UUID id) {
        String cacheKey = CACHE_PREFIX + id;

        // Try to get from cache
        String cached = (String) redisTemplate.opsForValue().get(cacheKey);
        if (cached != null) {
            return deserialize(cached);
        }

        // Cache miss - load from database
        Product product = productRepository.findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("Product", id));

        ProductResponse response = toResponse(product);

        // Store in cache
        redisTemplate.opsForValue().set(
            cacheKey,
            serialize(response),
            TTL
        );

        return response;
    }

    public void updateProduct(UUID id, ProductRequest request) {
        String cacheKey = CACHE_PREFIX + id;

        // Update database
        Product product = productRepository.findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("Product", id));

        updateEntity(product, request);
        productRepository.save(product);

        // Invalidate cache
        redisTemplate.delete(cacheKey);
    }

    private String serialize(Object obj) {
        try {
            return objectMapper.writeValueAsString(obj);
        } catch (JsonProcessingException e) {
            throw new RuntimeException(e);
        }
    }

    private ProductResponse deserialize(String json) {
        try {
            return objectMapper.readValue(json, ProductResponse.class);
        } catch (JsonProcessingException e) {
            throw new RuntimeException(e);
        }
    }
}
```

## Write-Through Pattern

```java
@Service
@RequiredArgsConstructor
public class WriteThroughCacheService {

    private final ProductRepository productRepository;
    private final ProductMapper productMapper;

    @CachePut(value = "products", key = "#result.id")
    @Transactional
    public ProductResponse createOrUpdate(ProductRequest request) {
        Product product;

        if (request.id() != null) {
            product = productRepository.findById(request.id())
                .orElseThrow(() -> new ResourceNotFoundException("Product", request.id()));
            productMapper.updateEntity(product, request);
        } else {
            product = productMapper.toEntity(request);
        }

        Product saved = productRepository.save(product);
        return productMapper.toResponse(saved);
    }
}
```

## Multi-Level Cache

```java
@Configuration
@EnableCaching
public class MultiLevelCacheConfig {

    @Bean
    @Primary
    public CacheManager compositeCacheManager(
            @Qualifier("localCacheManager") CacheManager localCache,
            @Qualifier("redisCacheManager") CacheManager redisCache) {

        return new CompositeCacheManager(localCache, redisCache);
    }

    @Bean
    public CacheManager localCacheManager() {
        CaffeineCacheManager manager = new CaffeineCacheManager();
        manager.setCaffeine(Caffeine.newBuilder()
            .maximumSize(1000)
            .expireAfterWrite(Duration.ofMinutes(5)));
        return manager;
    }

    @Bean
    public CacheManager redisCacheManager(RedisConnectionFactory connectionFactory) {
        return RedisCacheManager.builder(connectionFactory)
            .cacheDefaults(RedisCacheConfiguration.defaultCacheConfig()
                .entryTtl(Duration.ofHours(1)))
            .build();
    }
}

// Custom composite implementation
public class CompositeCacheManager implements CacheManager {

    private final List<CacheManager> cacheManagers;

    public CompositeCacheManager(CacheManager... managers) {
        this.cacheManagers = List.of(managers);
    }

    @Override
    public Cache getCache(String name) {
        List<Cache> caches = cacheManagers.stream()
            .map(cm -> cm.getCache(name))
            .filter(Objects::nonNull)
            .toList();

        return caches.isEmpty() ? null : new CompositeCache(name, caches);
    }

    @Override
    public Collection<String> getCacheNames() {
        return cacheManagers.stream()
            .flatMap(cm -> cm.getCacheNames().stream())
            .distinct()
            .toList();
    }
}
```

## Cache Warming

```java
@Component
@RequiredArgsConstructor
@Slf4j
public class CacheWarmer implements ApplicationRunner {

    private final ProductService productService;
    private final CategoryService categoryService;

    @Override
    public void run(ApplicationArguments args) {
        log.info("Warming up caches...");

        warmupCategories();
        warmupPopularProducts();

        log.info("Cache warmup complete");
    }

    private void warmupCategories() {
        categoryService.findAll(); // Triggers caching
    }

    private void warmupPopularProducts() {
        List<UUID> popularIds = getPopularProductIds();
        for (UUID id : popularIds) {
            try {
                productService.findById(id);
            } catch (Exception e) {
                log.warn("Failed to cache product {}: {}", id, e.getMessage());
            }
        }
    }

    @Scheduled(cron = "0 0 */4 * * *") // Every 4 hours
    public void refreshCache() {
        log.info("Refreshing cache...");
        // Re-warm caches
    }
}
```

## Cache Metrics

```java
@Configuration
public class CacheMetricsConfig {

    @Bean
    public MeterBinder caffeineCacheMetrics(CacheManager cacheManager) {
        return registry -> {
            if (cacheManager instanceof CaffeineCacheManager caffeineManager) {
                caffeineManager.getCacheNames().forEach(name -> {
                    Cache cache = caffeineManager.getCache(name);
                    if (cache instanceof CaffeineCache caffeineCache) {
                        CaffeineCacheMetrics.monitor(
                            registry,
                            caffeineCache.getNativeCache(),
                            name
                        );
                    }
                });
            }
        };
    }
}
```

## Best Practices

1. **Choose appropriate TTL** - Balance freshness vs performance
2. **Use cache prefixes** - Namespace for multi-tenant
3. **Handle cache failures gracefully** - Fallback to database
4. **Monitor cache metrics** - Hit rate, evictions, memory
5. **Avoid caching mutable objects** - Cache immutable DTOs
6. **Consider cache warming** - For frequently accessed data
7. **Use conditional caching** - Don't cache nulls unnecessarily
8. **Implement cache invalidation** - Update/evict on writes
9. **Set maximum size limits** - Prevent memory issues
10. **Test cache behavior** - Verify caching works correctly
