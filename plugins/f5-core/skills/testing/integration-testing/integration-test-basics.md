---
name: integration-test-basics
description: Integration testing fundamentals and strategies
category: testing/integration-testing
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Integration Testing Basics

## Overview

Integration tests verify that multiple components work together correctly.
They test the boundaries and interactions between units.

## What Integration Tests Cover

```
┌─────────────────────────────────────────────────────────────────┐
│                    Integration Test Scope                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────┐      ┌─────────┐      ┌─────────┐                │
│   │ Service │ ───▶ │  Repo   │ ───▶ │Database │                │
│   └─────────┘      └─────────┘      └─────────┘                │
│        │                                                         │
│        ▼                                                         │
│   ┌─────────┐      ┌─────────┐                                  │
│   │  API    │ ◀─── │External │                                  │
│   │ Client  │      │ Service │                                  │
│   └─────────┘      └─────────┘                                  │
│                                                                  │
│   Integration tests verify these connections work correctly     │
└─────────────────────────────────────────────────────────────────┘
```

## Types of Integration Tests

| Type | Description | Speed | Isolation |
|------|-------------|-------|-----------|
| **Narrow** | Few components, mocked external | Fast | High |
| **Broad** | Many components, real services | Slow | Low |
| **Contract** | API boundaries | Medium | Medium |

## Narrow Integration Tests

Test a few components together with external dependencies mocked.

```typescript
// narrow-integration.test.ts
describe('UserService + UserRepository Integration', () => {
  let userService: UserService;
  let userRepository: UserRepository;
  let mockEmailService: jest.Mocked<EmailService>;

  beforeEach(async () => {
    // Real repository with test database
    userRepository = new UserRepository(testDb);

    // Mock external service
    mockEmailService = {
      sendWelcomeEmail: jest.fn().mockResolvedValue(undefined),
    };

    // Real service with mixed dependencies
    userService = new UserService(userRepository, mockEmailService);

    // Clean database
    await testDb.clean();
  });

  it('should create user and persist to database', async () => {
    // Act
    const user = await userService.createUser({
      name: 'John',
      email: 'john@test.com',
    });

    // Assert - verify database state
    const dbUser = await userRepository.findById(user.id);
    expect(dbUser).not.toBeNull();
    expect(dbUser?.name).toBe('John');

    // Assert - verify external service called
    expect(mockEmailService.sendWelcomeEmail).toHaveBeenCalledWith('john@test.com');
  });
});
```

## Broad Integration Tests

Test the full stack with minimal mocking.

```typescript
// broad-integration.test.ts
describe('Order Processing Flow', () => {
  let app: Application;

  beforeAll(async () => {
    // Start full application
    app = await createTestApplication({
      database: testDatabase,
      messageQueue: testMessageQueue,
      cache: testRedis,
    });
  });

  afterAll(async () => {
    await app.close();
  });

  beforeEach(async () => {
    await testDatabase.clean();
    await testRedis.flushAll();
    await testMessageQueue.purge();
  });

  it('should process order end-to-end', async () => {
    // Arrange - seed data
    const user = await seedUser({ balance: 1000 });
    const product = await seedProduct({ price: 100, stock: 10 });

    // Act - create order
    const response = await request(app)
      .post('/api/orders')
      .set('Authorization', `Bearer ${user.token}`)
      .send({
        items: [{ productId: product.id, quantity: 2 }],
      });

    // Assert - API response
    expect(response.status).toBe(201);
    expect(response.body.total).toBe(200);

    // Assert - database state
    const order = await findOrder(response.body.id);
    expect(order.status).toBe('confirmed');

    // Assert - user balance updated
    const updatedUser = await findUser(user.id);
    expect(updatedUser.balance).toBe(800);

    // Assert - stock reduced
    const updatedProduct = await findProduct(product.id);
    expect(updatedProduct.stock).toBe(8);

    // Assert - message published
    const messages = await testMessageQueue.getMessages('order.created');
    expect(messages).toHaveLength(1);
  });
});
```

## Setting Up Test Environment

### Test Container Setup

```typescript
// test/setup/test-containers.ts
import { PostgreSqlContainer } from '@testcontainers/postgresql';
import { RedisContainer } from '@testcontainers/redis';

let postgresContainer: StartedPostgreSqlContainer;
let redisContainer: StartedRedisContainer;

export async function setupContainers() {
  // Start containers in parallel
  [postgresContainer, redisContainer] = await Promise.all([
    new PostgreSqlContainer()
      .withDatabase('testdb')
      .withUsername('test')
      .withPassword('test')
      .start(),
    new RedisContainer().start(),
  ]);

  // Set environment variables
  process.env.DATABASE_URL = postgresContainer.getConnectionUri();
  process.env.REDIS_URL = redisContainer.getConnectionUri();

  // Run migrations
  await runMigrations();
}

export async function teardownContainers() {
  await Promise.all([
    postgresContainer?.stop(),
    redisContainer?.stop(),
  ]);
}
```

### Jest Configuration

```typescript
// jest.integration.config.ts
export default {
  preset: 'ts-jest',
  testEnvironment: 'node',
  testMatch: ['**/*.integration.test.ts'],
  setupFilesAfterEnv: ['./test/setup/integration.setup.ts'],
  globalSetup: './test/setup/global-setup.ts',
  globalTeardown: './test/setup/global-teardown.ts',
  testTimeout: 30000, // Longer timeout for integration tests
};

// test/setup/integration.setup.ts
beforeEach(async () => {
  await cleanDatabase();
  jest.clearAllMocks();
});
```

## Test Data Management

### Seeding Test Data

```typescript
// test/helpers/seed.ts
export async function seedUser(overrides = {}): Promise<TestUser> {
  const user = await prisma.user.create({
    data: {
      id: randomUUID(),
      email: `test-${Date.now()}@example.com`,
      name: 'Test User',
      ...overrides,
    },
  });

  const token = generateToken(user);
  return { ...user, token };
}

export async function seedProduct(overrides = {}): Promise<Product> {
  return prisma.product.create({
    data: {
      id: randomUUID(),
      name: 'Test Product',
      price: 99.99,
      stock: 100,
      ...overrides,
    },
  });
}

export async function seedOrder(user: User, items: OrderItem[]): Promise<Order> {
  return prisma.order.create({
    data: {
      userId: user.id,
      items: { create: items },
      status: 'pending',
    },
    include: { items: true },
  });
}
```

### Database Cleaning

```typescript
// test/helpers/database.ts
export async function cleanDatabase(): Promise<void> {
  // Delete in correct order (respect foreign keys)
  await prisma.$transaction([
    prisma.orderItem.deleteMany(),
    prisma.order.deleteMany(),
    prisma.product.deleteMany(),
    prisma.user.deleteMany(),
  ]);
}

// Alternative: Truncate tables (faster)
export async function truncateTables(): Promise<void> {
  const tables = ['order_items', 'orders', 'products', 'users'];

  await prisma.$executeRaw`SET CONSTRAINTS ALL DEFERRED`;

  for (const table of tables) {
    await prisma.$executeRawUnsafe(`TRUNCATE TABLE "${table}" CASCADE`);
  }

  await prisma.$executeRaw`SET CONSTRAINTS ALL IMMEDIATE`;
}
```

## Testing Patterns

### Test HTTP Endpoints

```typescript
import request from 'supertest';

describe('User API Integration', () => {
  it('should create user via API', async () => {
    const response = await request(app)
      .post('/api/users')
      .send({ name: 'John', email: 'john@test.com' })
      .expect(201);

    expect(response.body).toMatchObject({
      id: expect.any(String),
      name: 'John',
      email: 'john@test.com',
    });

    // Verify in database
    const dbUser = await prisma.user.findUnique({
      where: { id: response.body.id },
    });
    expect(dbUser).not.toBeNull();
  });

  it('should return 400 for invalid input', async () => {
    const response = await request(app)
      .post('/api/users')
      .send({ name: '' }) // Invalid
      .expect(400);

    expect(response.body.error).toContain('name');
  });

  it('should return 401 for unauthorized access', async () => {
    await request(app)
      .get('/api/users/me')
      // No auth header
      .expect(401);
  });
});
```

### Test Database Transactions

```typescript
describe('Transaction Tests', () => {
  it('should rollback on failure', async () => {
    // Arrange
    const user = await seedUser({ balance: 100 });
    const initialBalance = user.balance;

    // Act - attempt operation that should fail
    try {
      await transferFunds({
        fromUserId: user.id,
        toUserId: 'non-existent',
        amount: 50,
      });
    } catch (error) {
      // Expected to fail
    }

    // Assert - balance unchanged (rollback worked)
    const updatedUser = await findUser(user.id);
    expect(updatedUser.balance).toBe(initialBalance);
  });
});
```

## Best Practices

### Do

| Practice | Description |
|----------|-------------|
| Use test containers | Real databases, isolated environment |
| Clean between tests | Prevent test pollution |
| Test realistic scenarios | Verify actual workflows |
| Check side effects | Database state, messages, events |
| Use meaningful seed data | Realistic test scenarios |

### Don't

| Anti-Pattern | Why |
|--------------|-----|
| Share test data | Creates dependencies |
| Hard-code IDs | Tests become brittle |
| Skip cleanup | Tests pollute each other |
| Mock everything | Defeats integration purpose |
| Ignore timeouts | Hides performance issues |

## Related Topics

- [Database Testing](./database-testing.md)
- [API Testing](./api-testing.md)
- [External Service Testing](./external-service-testing.md)
- [Testing Pyramid](../fundamentals/testing-pyramid.md)
