---
name: database-testing
description: Database integration testing strategies
category: testing/integration-testing
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Database Integration Testing

## Overview

Test actual database interactions to verify queries, transactions,
and data integrity work correctly.

## Setup Strategies

### 1. Test Containers (Recommended)

```typescript
// test/setup/database.ts
import { PostgreSqlContainer, StartedPostgreSqlContainer } from '@testcontainers/postgresql';
import { PrismaClient } from '@prisma/client';
import { execSync } from 'child_process';

let container: StartedPostgreSqlContainer;
let prisma: PrismaClient;

export async function setupTestDatabase(): Promise<PrismaClient> {
  // Start PostgreSQL container
  container = await new PostgreSqlContainer()
    .withDatabase('testdb')
    .withUsername('test')
    .withPassword('test')
    .start();

  // Set DATABASE_URL for Prisma
  process.env.DATABASE_URL = container.getConnectionUri();

  // Initialize Prisma
  prisma = new PrismaClient();

  // Run migrations
  execSync('npx prisma migrate deploy', {
    env: { ...process.env, DATABASE_URL: container.getConnectionUri() },
  });

  return prisma;
}

export async function teardownTestDatabase(): Promise<void> {
  await prisma.$disconnect();
  await container.stop();
}

export function getTestPrisma(): PrismaClient {
  return prisma;
}
```

### 2. Jest Setup File

```typescript
// jest.integration.setup.ts
import { setupTestDatabase, teardownTestDatabase, getTestPrisma } from './setup/database';
import { cleanDatabase } from './helpers/database';

beforeAll(async () => {
  await setupTestDatabase();
}, 60000); // 60s timeout for container startup

beforeEach(async () => {
  await cleanDatabase(getTestPrisma());
});

afterAll(async () => {
  await teardownTestDatabase();
});
```

### 3. Test Isolation

```typescript
// test/helpers/database.helper.ts
import { PrismaClient } from '@prisma/client';

export async function cleanDatabase(prisma: PrismaClient): Promise<void> {
  // Delete in correct order (respect foreign keys)
  await prisma.$transaction([
    prisma.orderItem.deleteMany(),
    prisma.order.deleteMany(),
    prisma.product.deleteMany(),
    prisma.user.deleteMany(),
  ]);
}

export async function resetSequences(prisma: PrismaClient): Promise<void> {
  await prisma.$executeRaw`ALTER SEQUENCE users_id_seq RESTART WITH 1`;
  await prisma.$executeRaw`ALTER SEQUENCE orders_id_seq RESTART WITH 1`;
}
```

## Integration Test Examples

### Repository Tests

```typescript
// user.repository.integration.test.ts
import { PrismaClient } from '@prisma/client';
import { PrismaUserRepository } from '@/infrastructure/persistence/user.repository';
import { User } from '@/domain/entities/user';
import { cleanDatabase, getTestPrisma } from '@test/helpers/database.helper';
import { createTestUser } from '@test/factories/user.factory';

describe('PrismaUserRepository Integration', () => {
  let prisma: PrismaClient;
  let repository: PrismaUserRepository;

  beforeAll(() => {
    prisma = getTestPrisma();
    repository = new PrismaUserRepository(prisma);
  });

  beforeEach(async () => {
    await cleanDatabase(prisma);
  });

  describe('save', () => {
    it('should persist new user to database', async () => {
      // Arrange
      const user = createTestUser();

      // Act
      await repository.save(user);

      // Assert - verify in database
      const dbUser = await prisma.user.findUnique({
        where: { id: user.id },
      });

      expect(dbUser).not.toBeNull();
      expect(dbUser?.name).toBe(user.name);
      expect(dbUser?.email).toBe(user.email);
    });

    it('should update existing user', async () => {
      // Arrange
      const user = createTestUser();
      await repository.save(user);

      // Act
      user.updateName('Updated Name');
      await repository.save(user);

      // Assert
      const dbUser = await prisma.user.findUnique({
        where: { id: user.id },
      });

      expect(dbUser?.name).toBe('Updated Name');
    });
  });

  describe('findById', () => {
    it('should return user when exists', async () => {
      // Arrange
      const user = createTestUser();
      await prisma.user.create({
        data: {
          id: user.id,
          name: user.name,
          email: user.email,
          createdAt: user.createdAt,
        },
      });

      // Act
      const result = await repository.findById(user.id);

      // Assert
      expect(result).not.toBeNull();
      expect(result?.id).toBe(user.id);
    });

    it('should return null when not exists', async () => {
      const result = await repository.findById('non-existent-id');
      expect(result).toBeNull();
    });
  });

  describe('findByEmail', () => {
    it('should find user by email case-insensitive', async () => {
      // Arrange
      await prisma.user.create({
        data: {
          id: '1',
          name: 'Test',
          email: 'Test@Example.com',
          createdAt: new Date(),
        },
      });

      // Act
      const result = await repository.findByEmail('test@example.com');

      // Assert
      expect(result).not.toBeNull();
    });
  });
});
```

### Transaction Tests

```typescript
describe('OrderService Transaction Tests', () => {
  let prisma: PrismaClient;
  let orderService: OrderService;

  beforeAll(() => {
    prisma = getTestPrisma();
    orderService = new OrderService(prisma);
  });

  beforeEach(async () => {
    await cleanDatabase(prisma);

    // Seed test data
    await prisma.product.createMany({
      data: [
        { id: 'p1', name: 'Product 1', price: 100, stock: 10 },
        { id: 'p2', name: 'Product 2', price: 200, stock: 5 },
      ],
    });

    await prisma.user.create({
      data: { id: 'u1', name: 'Test User', email: 'test@test.com' },
    });
  });

  it('should create order and update stock atomically', async () => {
    // Act
    const order = await orderService.createOrder({
      userId: 'u1',
      items: [
        { productId: 'p1', quantity: 2 },
        { productId: 'p2', quantity: 1 },
      ],
    });

    // Assert - order created
    const dbOrder = await prisma.order.findUnique({
      where: { id: order.id },
      include: { items: true },
    });
    expect(dbOrder).not.toBeNull();
    expect(dbOrder?.items).toHaveLength(2);

    // Assert - stock updated
    const product1 = await prisma.product.findUnique({ where: { id: 'p1' } });
    const product2 = await prisma.product.findUnique({ where: { id: 'p2' } });
    expect(product1?.stock).toBe(8); // 10 - 2
    expect(product2?.stock).toBe(4); // 5 - 1
  });

  it('should rollback on insufficient stock', async () => {
    // Act & Assert
    await expect(
      orderService.createOrder({
        userId: 'u1',
        items: [
          { productId: 'p1', quantity: 5 },
          { productId: 'p2', quantity: 10 }, // Only 5 in stock!
        ],
      })
    ).rejects.toThrow('Insufficient stock');

    // Verify rollback - no order created
    const orders = await prisma.order.findMany();
    expect(orders).toHaveLength(0);

    // Verify rollback - stock unchanged
    const product1 = await prisma.product.findUnique({ where: { id: 'p1' } });
    expect(product1?.stock).toBe(10); // Unchanged
  });

  it('should handle concurrent orders correctly', async () => {
    // Act - concurrent orders
    const results = await Promise.allSettled([
      orderService.createOrder({
        userId: 'u1',
        items: [{ productId: 'p2', quantity: 3 }],
      }),
      orderService.createOrder({
        userId: 'u1',
        items: [{ productId: 'p2', quantity: 3 }],
      }),
    ]);

    // Assert - one should succeed, one should fail
    const succeeded = results.filter(r => r.status === 'fulfilled');
    const failed = results.filter(r => r.status === 'rejected');

    expect(succeeded).toHaveLength(1);
    expect(failed).toHaveLength(1);

    // Assert - total stock reduction correct
    const product = await prisma.product.findUnique({ where: { id: 'p2' } });
    expect(product?.stock).toBe(2); // 5 - 3
  });
});
```

### Complex Query Tests

```typescript
describe('Order Query Tests', () => {
  beforeEach(async () => {
    await cleanDatabase(prisma);
    await seedTestOrders(prisma);
  });

  it('should filter orders by date range', async () => {
    const orders = await repository.findByDateRange(
      new Date('2024-01-01'),
      new Date('2024-01-31')
    );

    expect(orders).toHaveLength(5);
    orders.forEach(order => {
      expect(order.createdAt.getMonth()).toBe(0); // January
    });
  });

  it('should calculate total revenue by product', async () => {
    const revenue = await repository.getRevenueByProduct();

    expect(revenue).toEqual([
      { productId: 'p1', productName: 'Product 1', totalRevenue: 1000 },
      { productId: 'p2', productName: 'Product 2', totalRevenue: 800 },
    ]);
  });

  it('should paginate results correctly', async () => {
    const page1 = await repository.findAll({ page: 1, limit: 10 });
    const page2 = await repository.findAll({ page: 2, limit: 10 });

    expect(page1.items).toHaveLength(10);
    expect(page2.items).toHaveLength(5); // 15 total
    expect(page1.items[0].id).not.toBe(page2.items[0].id);
  });

  it('should search by text', async () => {
    const results = await repository.search('Product 1');

    expect(results.length).toBeGreaterThan(0);
    results.forEach(order => {
      expect(order.items.some(i => i.productName.includes('Product 1'))).toBe(true);
    });
  });
});

// Helper to seed complex test data
async function seedTestOrders(prisma: PrismaClient): Promise<void> {
  const user = await prisma.user.create({
    data: { id: 'u1', name: 'Test', email: 'test@test.com' },
  });

  await prisma.product.createMany({
    data: [
      { id: 'p1', name: 'Product 1', price: 100, stock: 100 },
      { id: 'p2', name: 'Product 2', price: 200, stock: 100 },
    ],
  });

  // Create orders across different dates
  for (let i = 0; i < 15; i++) {
    await prisma.order.create({
      data: {
        userId: user.id,
        createdAt: new Date(2024, 0, (i % 28) + 1), // January dates
        items: {
          create: [
            { productId: 'p1', quantity: 1, price: 100 },
            { productId: 'p2', quantity: 1, price: 200 },
          ],
        },
      },
    });
  }
}
```

## Testing Database Constraints

```typescript
describe('Database Constraints', () => {
  it('should enforce unique email constraint', async () => {
    await prisma.user.create({
      data: { email: 'test@test.com', name: 'First' },
    });

    await expect(
      prisma.user.create({
        data: { email: 'test@test.com', name: 'Second' },
      })
    ).rejects.toThrow(/unique constraint/i);
  });

  it('should enforce foreign key constraint', async () => {
    await expect(
      prisma.order.create({
        data: { userId: 'non-existent' },
      })
    ).rejects.toThrow(/foreign key/i);
  });

  it('should enforce check constraint', async () => {
    await expect(
      prisma.product.create({
        data: { name: 'Test', price: -10 }, // Invalid negative price
      })
    ).rejects.toThrow(/check constraint/i);
  });
});
```

## Best Practices

| Practice | Description |
|----------|-------------|
| Use containers | Real database, isolated environment |
| Clean between tests | Prevent test pollution |
| Test transactions | Verify atomicity |
| Test edge cases | NULL, duplicates, constraints |
| Seed realistic data | Use factories |
| Parallel safe | Don't rely on IDs or order |

## Related Topics

- [Integration Test Basics](./integration-test-basics.md)
- [API Testing](./api-testing.md)
- [Test Fixtures](../patterns/test-fixtures.md)
