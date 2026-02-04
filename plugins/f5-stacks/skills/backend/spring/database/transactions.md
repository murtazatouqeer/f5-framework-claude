# Transaction Management

Spring transaction management patterns and best practices.

## Basic Transaction Configuration

### Enable Transaction Management

```java
@Configuration
@EnableTransactionManagement
public class TransactionConfig {

    @Bean
    public PlatformTransactionManager transactionManager(EntityManagerFactory emf) {
        return new JpaTransactionManager(emf);
    }
}
```

### @Transactional Basics

```java
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)  // Default for class - read-only
public class ProductServiceImpl implements ProductService {

    private final ProductRepository productRepository;

    // Inherits class-level @Transactional(readOnly = true)
    @Override
    public Optional<Product> findById(UUID id) {
        return productRepository.findById(id);
    }

    // Override with write transaction
    @Override
    @Transactional
    public Product create(Product product) {
        return productRepository.save(product);
    }

    @Override
    @Transactional
    public Product update(Product product) {
        return productRepository.save(product);
    }

    @Override
    @Transactional
    public void delete(UUID id) {
        productRepository.deleteById(id);
    }
}
```

## Transaction Attributes

### Propagation

```java
// REQUIRED (default) - Use existing or create new
@Transactional(propagation = Propagation.REQUIRED)
public void method1() {
    // Uses existing transaction or creates new one
}

// REQUIRES_NEW - Always create new, suspend existing
@Transactional(propagation = Propagation.REQUIRES_NEW)
public void logAudit(String action) {
    // Always runs in new transaction
    // Commits even if outer transaction rolls back
}

// MANDATORY - Must have existing transaction
@Transactional(propagation = Propagation.MANDATORY)
public void mustHaveTransaction() {
    // Throws exception if no active transaction
}

// SUPPORTS - Use existing if available
@Transactional(propagation = Propagation.SUPPORTS)
public List<Product> findAll() {
    // Runs in transaction if one exists, otherwise non-transactional
}

// NOT_SUPPORTED - Suspend existing, run non-transactional
@Transactional(propagation = Propagation.NOT_SUPPORTED)
public void runWithoutTransaction() {
    // Suspends any existing transaction
}

// NEVER - Must not have transaction
@Transactional(propagation = Propagation.NEVER)
public void mustNotHaveTransaction() {
    // Throws exception if transaction exists
}

// NESTED - Nested transaction (savepoint)
@Transactional(propagation = Propagation.NESTED)
public void nestedOperation() {
    // Creates savepoint, can rollback independently
}
```

### Isolation Levels

```java
// READ_UNCOMMITTED - Lowest isolation
@Transactional(isolation = Isolation.READ_UNCOMMITTED)
public void dirtyReadsAllowed() {
    // Can read uncommitted changes from other transactions
}

// READ_COMMITTED - Prevents dirty reads (default for PostgreSQL)
@Transactional(isolation = Isolation.READ_COMMITTED)
public void preventDirtyReads() {
    // Only reads committed data
}

// REPEATABLE_READ - Prevents non-repeatable reads
@Transactional(isolation = Isolation.REPEATABLE_READ)
public void consistentReads() {
    // Same query returns same results within transaction
}

// SERIALIZABLE - Highest isolation
@Transactional(isolation = Isolation.SERIALIZABLE)
public void fullIsolation() {
    // Complete isolation, may cause serialization failures
}
```

### Timeout and Read-Only

```java
// Timeout in seconds
@Transactional(timeout = 30)
public void longRunningOperation() {
    // Rolls back if exceeds 30 seconds
}

// Read-only optimization
@Transactional(readOnly = true)
public List<Product> findAll() {
    // Hibernate skips dirty checking
    // Can use read replicas
}
```

### Rollback Rules

```java
// Rollback on specific exceptions
@Transactional(rollbackFor = BusinessException.class)
public void businessOperation() throws BusinessException {
    // Rolls back on BusinessException (checked)
}

// Rollback on multiple exceptions
@Transactional(rollbackFor = {BusinessException.class, ValidationException.class})
public void multipleExceptions() {
    // Rolls back on either exception
}

// Don't rollback on specific exception
@Transactional(noRollbackFor = WarningException.class)
public void warningsOk() {
    // Commits even if WarningException thrown
}

// Rollback for class hierarchy
@Transactional(rollbackFor = Exception.class)  // All exceptions
public void rollbackAll() throws Exception {
    // Note: By default only RuntimeException triggers rollback
}
```

## Transaction Patterns

### Service Layer Transactions

```java
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class OrderService {

    private final OrderRepository orderRepository;
    private final ProductService productService;
    private final PaymentService paymentService;
    private final NotificationService notificationService;

    @Transactional
    public Order placeOrder(CreateOrderRequest request) {
        // All operations in single transaction
        Order order = createOrder(request);

        // Update inventory
        for (OrderLine line : order.getLines()) {
            productService.decreaseStock(line.getProductId(), line.getQuantity());
        }

        // Process payment
        paymentService.processPayment(order);

        // Save order
        Order saved = orderRepository.save(order);

        // Notification in separate transaction (won't rollback order)
        notificationService.sendOrderConfirmation(saved);

        return saved;
    }
}

@Service
public class NotificationService {

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void sendOrderConfirmation(Order order) {
        // Runs in separate transaction
        // If this fails, order is still saved
    }
}
```

### Audit Logging Pattern

```java
@Service
@RequiredArgsConstructor
public class AuditService {

    private final AuditLogRepository auditLogRepository;

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void logAction(String action, String entity, UUID entityId, String details) {
        AuditLog log = AuditLog.builder()
            .action(action)
            .entityType(entity)
            .entityId(entityId)
            .details(details)
            .timestamp(Instant.now())
            .userId(getCurrentUserId())
            .build();

        auditLogRepository.save(log);
        // Commits independently of calling transaction
    }
}

@Service
public class ProductService {

    private final AuditService auditService;

    @Transactional
    public void deleteProduct(UUID id) {
        // Even if delete fails, audit log is saved
        auditService.logAction("DELETE_ATTEMPT", "Product", id, "Deletion requested");

        try {
            productRepository.deleteById(id);
            auditService.logAction("DELETE_SUCCESS", "Product", id, "Deleted successfully");
        } catch (Exception e) {
            auditService.logAction("DELETE_FAILED", "Product", id, e.getMessage());
            throw e;  // Transaction rolls back, but audit logs are preserved
        }
    }
}
```

### Retry Pattern

```java
@Service
public class PaymentService {

    @Transactional
    @Retryable(
        value = {OptimisticLockingFailureException.class},
        maxAttempts = 3,
        backoff = @Backoff(delay = 100)
    )
    public Payment processPayment(Order order) {
        // Retry on optimistic locking conflicts
        Account account = accountRepository.findById(order.getAccountId())
            .orElseThrow();

        account.debit(order.getTotalAmount());
        accountRepository.save(account);  // May throw OptimisticLockingFailureException

        return createPayment(order);
    }

    @Recover
    public Payment recoverPayment(OptimisticLockingFailureException e, Order order) {
        throw new PaymentFailedException("Could not process payment after retries", e);
    }
}
```

### Programmatic Transactions

```java
@Service
@RequiredArgsConstructor
public class BatchService {

    private final TransactionTemplate transactionTemplate;
    private final PlatformTransactionManager transactionManager;

    // Using TransactionTemplate
    public void processBatch(List<Item> items) {
        for (Item item : items) {
            transactionTemplate.executeWithoutResult(status -> {
                try {
                    processItem(item);
                } catch (Exception e) {
                    status.setRollbackOnly();
                    log.error("Failed to process item: {}", item.getId(), e);
                }
            });
        }
    }

    // Using TransactionTemplate with result
    public Result processWithResult(Item item) {
        return transactionTemplate.execute(status -> {
            // Process and return result
            return doProcess(item);
        });
    }

    // Manual transaction management
    public void manualTransaction() {
        TransactionDefinition def = new DefaultTransactionDefinition();
        TransactionStatus status = transactionManager.getTransaction(def);

        try {
            // Perform operations
            doWork();
            transactionManager.commit(status);
        } catch (Exception e) {
            transactionManager.rollback(status);
            throw e;
        }
    }
}

// Configure TransactionTemplate
@Configuration
public class TransactionConfig {

    @Bean
    public TransactionTemplate transactionTemplate(PlatformTransactionManager transactionManager) {
        TransactionTemplate template = new TransactionTemplate(transactionManager);
        template.setIsolationLevel(TransactionDefinition.ISOLATION_READ_COMMITTED);
        template.setTimeout(30);
        return template;
    }
}
```

### Optimistic Locking

```java
@Entity
public class Product {

    @Version
    private Long version;

    // Other fields...
}

@Service
public class ProductService {

    @Transactional
    public Product update(UUID id, ProductUpdateRequest request) {
        Product product = productRepository.findById(id)
            .orElseThrow(() -> new ProductNotFoundException(id));

        // Update fields
        product.setName(request.getName());
        product.setPrice(request.getPrice());

        try {
            return productRepository.save(product);
        } catch (OptimisticLockingFailureException e) {
            throw new ConcurrentModificationException(
                "Product was modified by another user. Please refresh and try again.");
        }
    }
}
```

### Pessimistic Locking

```java
public interface ProductRepository extends JpaRepository<Product, UUID> {

    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @Query("SELECT p FROM Product p WHERE p.id = :id")
    Optional<Product> findByIdWithLock(@Param("id") UUID id);

    @Lock(LockModeType.PESSIMISTIC_READ)
    @Query("SELECT p FROM Product p WHERE p.id = :id")
    Optional<Product> findByIdWithReadLock(@Param("id") UUID id);
}

@Service
public class InventoryService {

    @Transactional
    public void decreaseStock(UUID productId, int quantity) {
        // Lock row for update
        Product product = productRepository.findByIdWithLock(productId)
            .orElseThrow(() -> new ProductNotFoundException(productId));

        if (product.getStock() < quantity) {
            throw new InsufficientStockException(productId);
        }

        product.setStock(product.getStock() - quantity);
        productRepository.save(product);
    }
}
```

## Common Pitfalls

### Self-Invocation Problem

```java
@Service
public class ProductService {

    // ❌ WRONG: Self-invocation bypasses proxy
    @Transactional
    public void processAll() {
        for (Product p : findAll()) {
            process(p);  // @Transactional ignored!
        }
    }

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void process(Product product) {
        // Not in new transaction when called internally
    }

    // ✅ Solution 1: Inject self
    @Autowired
    private ProductService self;

    @Transactional
    public void processAllFixed() {
        for (Product p : findAll()) {
            self.process(p);  // Uses proxy
        }
    }

    // ✅ Solution 2: Separate into different service
    @Autowired
    private ProductProcessor processor;

    @Transactional
    public void processAllWithSeparateService() {
        for (Product p : findAll()) {
            processor.process(p);  // Different bean, proxy works
        }
    }
}
```

### Checked Exception Rollback

```java
// ❌ WRONG: Checked exceptions don't trigger rollback by default
@Transactional
public void process() throws BusinessException {
    doWork();
    throw new BusinessException();  // Transaction commits!
}

// ✅ RIGHT: Explicitly specify rollback
@Transactional(rollbackFor = BusinessException.class)
public void processFixed() throws BusinessException {
    doWork();
    throw new BusinessException();  // Transaction rolls back
}
```

## Best Practices

1. **Use class-level @Transactional(readOnly = true)** - Default to read-only
2. **Override with @Transactional** for write operations
3. **Keep transactions short** - Don't include external calls
4. **Use REQUIRES_NEW for audit logs** - Preserve regardless of outcome
5. **Handle optimistic locking** - Expect and handle conflicts
6. **Avoid self-invocation** - Use separate beans or self-injection
7. **Specify rollbackFor** for checked exceptions
8. **Use appropriate isolation level** - Default is usually fine
