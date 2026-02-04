# Async Processing

Spring Boot asynchronous processing patterns with @Async, CompletableFuture, and event-driven architecture.

## Configuration

### Enable Async Processing

```java
package com.example.app.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;

import java.util.concurrent.Executor;
import java.util.concurrent.ThreadPoolExecutor;

@Configuration
@EnableAsync
public class AsyncConfig {

    @Bean(name = "asyncExecutor")
    public Executor asyncExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(5);
        executor.setMaxPoolSize(10);
        executor.setQueueCapacity(100);
        executor.setThreadNamePrefix("Async-");
        executor.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
        executor.setWaitForTasksToCompleteOnShutdown(true);
        executor.setAwaitTerminationSeconds(60);
        executor.initialize();
        return executor;
    }

    @Bean(name = "emailExecutor")
    public Executor emailExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(2);
        executor.setMaxPoolSize(5);
        executor.setQueueCapacity(50);
        executor.setThreadNamePrefix("Email-");
        executor.initialize();
        return executor;
    }

    @Bean(name = "reportExecutor")
    public Executor reportExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(1);
        executor.setMaxPoolSize(3);
        executor.setQueueCapacity(20);
        executor.setThreadNamePrefix("Report-");
        executor.initialize();
        return executor;
    }
}
```

### Application Properties

```yaml
# application.yml
spring:
  task:
    execution:
      pool:
        core-size: 5
        max-size: 10
        queue-capacity: 100
      thread-name-prefix: "task-"
    scheduling:
      pool:
        size: 5
      thread-name-prefix: "scheduling-"
```

## Basic @Async Usage

### Fire and Forget

```java
@Service
@RequiredArgsConstructor
@Slf4j
public class NotificationService {

    private final EmailSender emailSender;
    private final PushNotificationSender pushSender;

    @Async("emailExecutor")
    public void sendWelcomeEmail(User user) {
        log.info("Sending welcome email to {} on thread {}",
            user.getEmail(), Thread.currentThread().getName());

        emailSender.send(
            user.getEmail(),
            "Welcome!",
            "Thank you for joining..."
        );
    }

    @Async
    public void sendOrderConfirmation(Order order, User user) {
        log.info("Sending order confirmation on thread {}",
            Thread.currentThread().getName());

        emailSender.send(
            user.getEmail(),
            "Order Confirmed",
            buildOrderEmail(order)
        );

        pushSender.send(
            user.getDeviceToken(),
            "Order #" + order.getId() + " confirmed!"
        );
    }

    @Async
    public void sendBulkNotifications(List<User> users, String message) {
        log.info("Sending bulk notifications to {} users", users.size());

        for (User user : users) {
            try {
                emailSender.send(user.getEmail(), "Notification", message);
            } catch (Exception e) {
                log.error("Failed to send to {}: {}", user.getEmail(), e.getMessage());
            }
        }
    }
}
```

### Return CompletableFuture

```java
@Service
@RequiredArgsConstructor
@Slf4j
public class ReportService {

    private final ReportGenerator reportGenerator;
    private final StorageService storageService;

    @Async("reportExecutor")
    public CompletableFuture<ReportResult> generateReport(ReportRequest request) {
        log.info("Generating report: {}", request.getType());

        try {
            byte[] reportData = reportGenerator.generate(request);
            String url = storageService.upload(reportData, request.getFilename());

            return CompletableFuture.completedFuture(
                new ReportResult(request.getId(), url, ReportStatus.COMPLETED)
            );
        } catch (Exception e) {
            log.error("Report generation failed: {}", e.getMessage());
            return CompletableFuture.completedFuture(
                new ReportResult(request.getId(), null, ReportStatus.FAILED)
            );
        }
    }

    @Async
    public CompletableFuture<DataExport> exportData(ExportRequest request) {
        log.info("Exporting data for user: {}", request.getUserId());

        List<Object> data = fetchData(request);
        byte[] exportFile = formatExport(data, request.getFormat());
        String downloadUrl = storageService.upload(exportFile, generateFilename(request));

        return CompletableFuture.completedFuture(
            new DataExport(downloadUrl, data.size())
        );
    }
}
```

## Combining CompletableFutures

### Parallel Execution

```java
@Service
@RequiredArgsConstructor
public class DashboardService {

    private final OrderService orderService;
    private final InventoryService inventoryService;
    private final AnalyticsService analyticsService;

    public DashboardData getDashboard(UUID userId) {
        // Start all async operations in parallel
        CompletableFuture<OrderStats> orderStatsFuture =
            orderService.getOrderStats(userId);

        CompletableFuture<InventorySummary> inventoryFuture =
            inventoryService.getSummary(userId);

        CompletableFuture<AnalyticsReport> analyticsFuture =
            analyticsService.getReport(userId);

        // Wait for all to complete
        CompletableFuture.allOf(
            orderStatsFuture,
            inventoryFuture,
            analyticsFuture
        ).join();

        // Combine results
        return new DashboardData(
            orderStatsFuture.join(),
            inventoryFuture.join(),
            analyticsFuture.join()
        );
    }

    public CompletableFuture<DashboardData> getDashboardAsync(UUID userId) {
        CompletableFuture<OrderStats> orderStatsFuture =
            orderService.getOrderStats(userId);

        CompletableFuture<InventorySummary> inventoryFuture =
            inventoryService.getSummary(userId);

        CompletableFuture<AnalyticsReport> analyticsFuture =
            analyticsService.getReport(userId);

        return CompletableFuture.allOf(
            orderStatsFuture,
            inventoryFuture,
            analyticsFuture
        ).thenApply(v -> new DashboardData(
            orderStatsFuture.join(),
            inventoryFuture.join(),
            analyticsFuture.join()
        ));
    }
}
```

### Chaining Operations

```java
@Service
@RequiredArgsConstructor
public class OrderProcessingService {

    private final InventoryService inventoryService;
    private final PaymentService paymentService;
    private final ShippingService shippingService;
    private final NotificationService notificationService;

    @Async
    public CompletableFuture<OrderResult> processOrder(Order order) {
        return inventoryService.reserveStock(order)
            .thenCompose(reservation ->
                paymentService.processPayment(order, reservation))
            .thenCompose(payment ->
                shippingService.createShipment(order, payment))
            .thenApply(shipment -> {
                notificationService.sendOrderConfirmation(order, shipment);
                return new OrderResult(order.getId(), OrderStatus.COMPLETED, shipment);
            })
            .exceptionally(ex -> {
                log.error("Order processing failed: {}", ex.getMessage());
                rollbackOrder(order);
                return new OrderResult(order.getId(), OrderStatus.FAILED, null);
            });
    }

    @Async
    public CompletableFuture<List<ProductData>> enrichProducts(List<UUID> productIds) {
        List<CompletableFuture<ProductData>> futures = productIds.stream()
            .map(this::fetchProductData)
            .toList();

        return CompletableFuture.allOf(futures.toArray(new CompletableFuture[0]))
            .thenApply(v -> futures.stream()
                .map(CompletableFuture::join)
                .filter(Objects::nonNull)
                .toList());
    }

    private CompletableFuture<ProductData> fetchProductData(UUID productId) {
        return CompletableFuture.supplyAsync(() -> {
            // Fetch from external API
            return externalApiClient.getProductData(productId);
        }).exceptionally(ex -> {
            log.warn("Failed to fetch product data for {}: {}", productId, ex.getMessage());
            return null;
        });
    }
}
```

### First Successful Result

```java
@Service
public class PriceService {

    private final List<PriceProvider> providers;

    @Async
    public CompletableFuture<BigDecimal> getBestPrice(String sku) {
        List<CompletableFuture<BigDecimal>> futures = providers.stream()
            .map(provider -> fetchPrice(provider, sku))
            .toList();

        // Get first successful result
        return CompletableFuture.anyOf(futures.toArray(new CompletableFuture[0]))
            .thenApply(result -> (BigDecimal) result);
    }

    private CompletableFuture<BigDecimal> fetchPrice(PriceProvider provider, String sku) {
        return CompletableFuture.supplyAsync(() -> provider.getPrice(sku))
            .orTimeout(5, TimeUnit.SECONDS)
            .exceptionally(ex -> null);
    }
}
```

## Event-Driven Async

### Application Events

```java
// Event
public record OrderCreatedEvent(
    UUID orderId,
    UUID userId,
    BigDecimal totalAmount,
    Instant createdAt
) implements ApplicationEvent {

    public OrderCreatedEvent(Order order) {
        this(order.getId(), order.getUserId(),
             order.getTotalAmount(), Instant.now());
    }
}

// Publisher
@Service
@RequiredArgsConstructor
public class OrderService {

    private final OrderRepository orderRepository;
    private final ApplicationEventPublisher eventPublisher;

    @Transactional
    public Order createOrder(CreateOrderRequest request) {
        Order order = new Order(request);
        order = orderRepository.save(order);

        // Publish event after commit
        eventPublisher.publishEvent(new OrderCreatedEvent(order));

        return order;
    }
}

// Async Listener
@Component
@RequiredArgsConstructor
@Slf4j
public class OrderEventListener {

    private final NotificationService notificationService;
    private final AnalyticsService analyticsService;
    private final InventoryService inventoryService;

    @Async
    @EventListener
    public void handleOrderCreated(OrderCreatedEvent event) {
        log.info("Processing order created event: {}", event.orderId());
        notificationService.sendOrderConfirmation(event);
    }

    @Async
    @EventListener
    public void trackOrderAnalytics(OrderCreatedEvent event) {
        log.info("Tracking analytics for order: {}", event.orderId());
        analyticsService.trackOrder(event);
    }

    @Async
    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void updateInventory(OrderCreatedEvent event) {
        log.info("Updating inventory for order: {}", event.orderId());
        inventoryService.decrementStock(event.orderId());
    }
}
```

### Transactional Event Listener

```java
@Component
@RequiredArgsConstructor
@Slf4j
public class TransactionalEventHandler {

    @Async
    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void afterCommit(OrderCreatedEvent event) {
        // Only runs after transaction commits
        log.info("Order {} committed, sending notifications", event.orderId());
    }

    @Async
    @TransactionalEventListener(phase = TransactionPhase.AFTER_ROLLBACK)
    public void afterRollback(OrderCreatedEvent event) {
        // Cleanup on rollback
        log.warn("Order {} rolled back", event.orderId());
    }

    @Async
    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMPLETION)
    public void afterCompletion(OrderCreatedEvent event) {
        // Runs regardless of commit/rollback
        log.info("Order {} transaction completed", event.orderId());
    }
}
```

## Scheduled Tasks

```java
@Component
@RequiredArgsConstructor
@Slf4j
public class ScheduledTasks {

    private final ReportService reportService;
    private final CleanupService cleanupService;

    // Run every hour
    @Scheduled(cron = "0 0 * * * *")
    public void generateHourlyReport() {
        log.info("Starting hourly report generation");
        reportService.generateHourlyReport();
    }

    // Run at midnight daily
    @Scheduled(cron = "0 0 0 * * *")
    public void dailyCleanup() {
        log.info("Starting daily cleanup");
        cleanupService.cleanupExpiredSessions();
        cleanupService.archiveOldRecords();
    }

    // Run every 5 minutes
    @Scheduled(fixedRate = 300000)
    public void healthCheck() {
        log.debug("Performing health check");
    }

    // Run 10 seconds after previous completion
    @Scheduled(fixedDelay = 10000)
    public void processQueue() {
        queueService.processNextBatch();
    }

    // Async scheduled task
    @Async
    @Scheduled(fixedRate = 60000)
    public CompletableFuture<Void> syncExternalData() {
        return externalService.sync()
            .thenAccept(result -> log.info("Sync completed: {}", result));
    }
}
```

## Error Handling

### Custom Async Exception Handler

```java
@Configuration
public class AsyncExceptionConfig implements AsyncConfigurer {

    @Override
    public AsyncUncaughtExceptionHandler getAsyncUncaughtExceptionHandler() {
        return new CustomAsyncExceptionHandler();
    }
}

@Slf4j
public class CustomAsyncExceptionHandler implements AsyncUncaughtExceptionHandler {

    @Override
    public void handleUncaughtException(Throwable ex, Method method, Object... params) {
        log.error("Async method {} failed with parameters {}: {}",
            method.getName(),
            Arrays.toString(params),
            ex.getMessage(),
            ex);

        // Send alert, record metric, etc.
        if (ex instanceof BusinessException) {
            // Handle recoverable errors
        } else {
            // Handle unexpected errors
        }
    }
}
```

### Resilient Async Operations

```java
@Service
@RequiredArgsConstructor
@Slf4j
public class ResilientAsyncService {

    private final ExternalApiClient apiClient;

    @Async
    @Retryable(
        value = {TransientException.class},
        maxAttempts = 3,
        backoff = @Backoff(delay = 1000, multiplier = 2)
    )
    public CompletableFuture<ApiResponse> callExternalApi(ApiRequest request) {
        log.info("Calling external API");
        return CompletableFuture.supplyAsync(() -> apiClient.call(request));
    }

    @Async
    public CompletableFuture<Result> withTimeout(Request request) {
        return CompletableFuture.supplyAsync(() -> process(request))
            .orTimeout(30, TimeUnit.SECONDS)
            .exceptionally(ex -> {
                if (ex instanceof TimeoutException) {
                    log.error("Operation timed out");
                    return Result.timeout();
                }
                log.error("Operation failed: {}", ex.getMessage());
                return Result.error(ex.getMessage());
            });
    }

    @Async
    public CompletableFuture<Result> withFallback(Request request) {
        return CompletableFuture.supplyAsync(() -> process(request))
            .exceptionally(ex -> {
                log.warn("Primary processing failed, using fallback");
                return fallbackProcess(request);
            });
    }
}
```

## Context Propagation

```java
@Configuration
public class AsyncContextConfig {

    @Bean
    public TaskDecorator contextDecorator() {
        return runnable -> {
            // Capture context from calling thread
            RequestAttributes context = RequestContextHolder.getRequestAttributes();
            SecurityContext securityContext = SecurityContextHolder.getContext();
            MDC.getCopyOfContextMap();

            return () -> {
                try {
                    // Restore context in async thread
                    RequestContextHolder.setRequestAttributes(context);
                    SecurityContextHolder.setContext(securityContext);
                    MDC.setContextMap(mdcContext != null ? mdcContext : Map.of());
                    runnable.run();
                } finally {
                    // Clean up
                    RequestContextHolder.resetRequestAttributes();
                    SecurityContextHolder.clearContext();
                    MDC.clear();
                }
            };
        };
    }

    @Bean
    public Executor asyncExecutor(TaskDecorator contextDecorator) {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(5);
        executor.setMaxPoolSize(10);
        executor.setTaskDecorator(contextDecorator);
        executor.initialize();
        return executor;
    }
}
```

## Monitoring Async Tasks

```java
@Component
@RequiredArgsConstructor
@Slf4j
public class AsyncTaskMonitor {

    private final MeterRegistry meterRegistry;

    @Around("@annotation(org.springframework.scheduling.annotation.Async)")
    public Object monitorAsyncTask(ProceedingJoinPoint joinPoint) throws Throwable {
        String methodName = joinPoint.getSignature().getName();
        Timer.Sample sample = Timer.start(meterRegistry);

        try {
            Object result = joinPoint.proceed();

            if (result instanceof CompletableFuture<?> future) {
                return future.whenComplete((res, ex) -> {
                    sample.stop(Timer.builder("async.task")
                        .tag("method", methodName)
                        .tag("status", ex == null ? "success" : "failure")
                        .register(meterRegistry));
                });
            }

            sample.stop(Timer.builder("async.task")
                .tag("method", methodName)
                .tag("status", "success")
                .register(meterRegistry));

            return result;
        } catch (Exception e) {
            sample.stop(Timer.builder("async.task")
                .tag("method", methodName)
                .tag("status", "failure")
                .register(meterRegistry));
            throw e;
        }
    }
}
```

## Best Practices

1. **Use dedicated executors** - Different pools for different workloads
2. **Set appropriate pool sizes** - Based on workload characteristics
3. **Handle exceptions** - Always provide exception handlers
4. **Propagate context** - Security, MDC, request attributes
5. **Use timeouts** - Prevent indefinite waits
6. **Monitor metrics** - Track queue sizes, completion times
7. **Test async code** - Use `@Async` with synchronous executor in tests
8. **Avoid @Async on private methods** - Spring proxy limitations
9. **Use @TransactionalEventListener** - For post-commit processing
10. **Consider backpressure** - Queue capacity and rejection policies
