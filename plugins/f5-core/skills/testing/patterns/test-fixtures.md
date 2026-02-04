---
name: test-fixtures
description: Test fixture patterns for consistent test data
category: testing/patterns
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Test Fixtures

## Overview

Test fixtures are pre-defined states or data used to establish a consistent
testing environment. They help create reproducible, maintainable tests.

## Types of Fixtures

| Type | Purpose | Example |
|------|---------|---------|
| **Data Fixtures** | Pre-defined test data | User objects, orders |
| **State Fixtures** | System state setup | Database state, config |
| **Environment Fixtures** | External dependencies | Mock servers, containers |

## Data Fixtures

### Static Fixtures (JSON/YAML)

```json
// fixtures/users.json
{
  "validUser": {
    "id": "user-001",
    "name": "John Doe",
    "email": "john@example.com",
    "role": "user",
    "status": "active"
  },
  "adminUser": {
    "id": "admin-001",
    "name": "Admin User",
    "email": "admin@example.com",
    "role": "admin",
    "status": "active"
  },
  "inactiveUser": {
    "id": "user-002",
    "name": "Jane Inactive",
    "email": "jane@example.com",
    "role": "user",
    "status": "inactive"
  }
}
```

```typescript
// Using fixtures
import users from './fixtures/users.json';

describe('UserService', () => {
  it('should activate inactive user', async () => {
    const user = { ...users.inactiveUser };
    await repository.save(user);

    await userService.activate(user.id);

    const updated = await repository.findById(user.id);
    expect(updated.status).toBe('active');
  });
});
```

### TypeScript Fixtures

```typescript
// fixtures/users.ts
import { User } from '@/types';

export const validUser: User = {
  id: 'user-001',
  name: 'John Doe',
  email: 'john@example.com',
  role: 'user',
  status: 'active',
  createdAt: new Date('2024-01-01'),
};

export const adminUser: User = {
  id: 'admin-001',
  name: 'Admin User',
  email: 'admin@example.com',
  role: 'admin',
  status: 'active',
  createdAt: new Date('2024-01-01'),
};

export const testUsers: User[] = [
  validUser,
  adminUser,
  {
    id: 'user-002',
    name: 'Jane Doe',
    email: 'jane@example.com',
    role: 'user',
    status: 'active',
    createdAt: new Date('2024-01-02'),
  },
];
```

## Fixture Factories

### Basic Factory

```typescript
// factories/user.factory.ts
import { User } from '@/types';
import { randomUUID } from 'crypto';

interface UserFactoryOptions {
  id?: string;
  name?: string;
  email?: string;
  role?: 'user' | 'admin';
  status?: 'active' | 'inactive';
}

export function createUser(options: UserFactoryOptions = {}): User {
  const id = options.id ?? randomUUID();
  return {
    id,
    name: options.name ?? 'Test User',
    email: options.email ?? `test-${id}@example.com`,
    role: options.role ?? 'user',
    status: options.status ?? 'active',
    createdAt: new Date(),
  };
}

// Usage
const user = createUser({ role: 'admin' });
const customUser = createUser({ name: 'Custom Name', email: 'custom@test.com' });
```

### Builder Pattern Factory

```typescript
// factories/user.builder.ts
import { User } from '@/types';

export class UserBuilder {
  private user: Partial<User> = {};

  constructor() {
    this.reset();
  }

  private reset(): this {
    this.user = {
      id: `user-${Date.now()}`,
      name: 'Test User',
      email: 'test@example.com',
      role: 'user',
      status: 'active',
      createdAt: new Date(),
    };
    return this;
  }

  withId(id: string): this {
    this.user.id = id;
    return this;
  }

  withName(name: string): this {
    this.user.name = name;
    return this;
  }

  withEmail(email: string): this {
    this.user.email = email;
    return this;
  }

  asAdmin(): this {
    this.user.role = 'admin';
    return this;
  }

  asInactive(): this {
    this.user.status = 'inactive';
    return this;
  }

  build(): User {
    const result = this.user as User;
    this.reset();
    return result;
  }
}

// Usage
const userBuilder = new UserBuilder();

const admin = userBuilder.asAdmin().withName('Admin').build();
const inactiveUser = userBuilder.withEmail('inactive@test.com').asInactive().build();
```

### Faker Integration

```typescript
// factories/user.factory.ts
import { faker } from '@faker-js/faker';
import { User } from '@/types';

export function createRandomUser(overrides: Partial<User> = {}): User {
  return {
    id: faker.string.uuid(),
    name: faker.person.fullName(),
    email: faker.internet.email(),
    role: faker.helpers.arrayElement(['user', 'admin']),
    status: faker.helpers.arrayElement(['active', 'inactive']),
    createdAt: faker.date.past(),
    avatar: faker.image.avatar(),
    bio: faker.lorem.paragraph(),
    ...overrides,
  };
}

export function createManyUsers(count: number): User[] {
  return Array.from({ length: count }, () => createRandomUser());
}

// Seeded random for reproducibility
export function createSeededUser(seed: number): User {
  faker.seed(seed);
  return createRandomUser();
}
```

## Database Fixtures

### Seeding Functions

```typescript
// fixtures/database.ts
import { PrismaClient } from '@prisma/client';
import { createUser } from '../factories/user.factory';
import { createOrder } from '../factories/order.factory';

const prisma = new PrismaClient();

export async function seedTestData() {
  // Create users
  const users = await Promise.all([
    prisma.user.create({ data: createUser({ role: 'admin' }) }),
    prisma.user.create({ data: createUser() }),
    prisma.user.create({ data: createUser() }),
  ]);

  // Create orders for users
  const orders = await Promise.all(
    users.flatMap(user =>
      Array.from({ length: 3 }, () =>
        prisma.order.create({
          data: createOrder({ userId: user.id }),
        })
      )
    )
  );

  return { users, orders };
}

export async function cleanTestData() {
  await prisma.$transaction([
    prisma.orderItem.deleteMany(),
    prisma.order.deleteMany(),
    prisma.user.deleteMany(),
  ]);
}
```

### Snapshot/Restore

```typescript
// fixtures/snapshot.ts
import { execSync } from 'child_process';

export async function createDatabaseSnapshot(name: string) {
  execSync(`pg_dump -Fc testdb > snapshots/${name}.dump`);
}

export async function restoreDatabaseSnapshot(name: string) {
  execSync(`pg_restore -d testdb --clean snapshots/${name}.dump`);
}

// Usage in tests
describe('Complex Integration', () => {
  beforeAll(async () => {
    await seedTestData();
    await createDatabaseSnapshot('baseline');
  });

  beforeEach(async () => {
    await restoreDatabaseSnapshot('baseline');
  });

  it('should modify data safely', async () => {
    // Test can modify data, will be restored before next test
  });
});
```

## Environment Fixtures

### Test Containers

```typescript
// fixtures/containers.ts
import { PostgreSqlContainer, StartedPostgreSqlContainer } from '@testcontainers/postgresql';
import { RedisContainer, StartedRedisContainer } from '@testcontainers/redis';

interface TestContainers {
  postgres: StartedPostgreSqlContainer;
  redis: StartedRedisContainer;
}

let containers: TestContainers;

export async function startContainers(): Promise<TestContainers> {
  const [postgres, redis] = await Promise.all([
    new PostgreSqlContainer().start(),
    new RedisContainer().start(),
  ]);

  containers = { postgres, redis };

  process.env.DATABASE_URL = postgres.getConnectionUri();
  process.env.REDIS_URL = redis.getConnectionUrl();

  return containers;
}

export async function stopContainers(): Promise<void> {
  await Promise.all([
    containers.postgres?.stop(),
    containers.redis?.stop(),
  ]);
}

export function getContainers(): TestContainers {
  return containers;
}
```

### Mock Server Fixtures

```typescript
// fixtures/mock-server.ts
import { setupServer } from 'msw/node';
import { rest } from 'msw';

// Default handlers
const handlers = [
  rest.get('/api/users/:id', (req, res, ctx) => {
    return res(
      ctx.json({
        id: req.params.id,
        name: 'Mock User',
        email: 'mock@example.com',
      })
    );
  }),

  rest.post('/api/orders', (req, res, ctx) => {
    return res(
      ctx.status(201),
      ctx.json({
        id: 'order-123',
        status: 'created',
      })
    );
  }),
];

export const mockServer = setupServer(...handlers);

// Helper to add custom handlers per test
export function mockEndpoint(
  method: 'get' | 'post' | 'put' | 'delete',
  path: string,
  response: any,
  status = 200
) {
  mockServer.use(
    rest[method](path, (req, res, ctx) => {
      return res(ctx.status(status), ctx.json(response));
    })
  );
}
```

## Playwright Fixtures

```typescript
// fixtures/playwright.fixture.ts
import { test as base, Page } from '@playwright/test';
import { LoginPage } from '../pages/login.page';
import { DashboardPage } from '../pages/dashboard.page';

interface TestFixtures {
  loginPage: LoginPage;
  dashboardPage: DashboardPage;
  authenticatedPage: Page;
}

export const test = base.extend<TestFixtures>({
  loginPage: async ({ page }, use) => {
    const loginPage = new LoginPage(page);
    await use(loginPage);
  },

  dashboardPage: async ({ page }, use) => {
    const dashboardPage = new DashboardPage(page);
    await use(dashboardPage);
  },

  authenticatedPage: async ({ page }, use) => {
    // Login before test
    await page.goto('/login');
    await page.fill('[data-testid="email"]', 'test@example.com');
    await page.fill('[data-testid="password"]', 'password123');
    await page.click('[data-testid="submit"]');
    await page.waitForURL('/dashboard');

    await use(page);

    // Cleanup after test
    await page.goto('/logout');
  },
});

// Usage
test('should show dashboard', async ({ authenticatedPage }) => {
  await expect(authenticatedPage.locator('h1')).toHaveText('Dashboard');
});
```

## Fixture Organization

```
test/
├── fixtures/
│   ├── data/
│   │   ├── users.json
│   │   ├── orders.json
│   │   └── products.json
│   ├── factories/
│   │   ├── user.factory.ts
│   │   ├── order.factory.ts
│   │   └── product.factory.ts
│   ├── builders/
│   │   ├── user.builder.ts
│   │   └── order.builder.ts
│   ├── database/
│   │   ├── seed.ts
│   │   ├── clean.ts
│   │   └── snapshots/
│   └── mocks/
│       ├── api.handlers.ts
│       └── services.ts
```

## Best Practices

| Do | Don't |
|----|-------|
| Use factories for dynamic data | Hard-code test data |
| Reset fixtures between tests | Share mutable state |
| Keep fixtures close to tests | Put fixtures far from usage |
| Use meaningful fixture names | Use generic names |
| Version control fixtures | Ignore fixture files |
| Document fixture purpose | Leave fixtures unexplained |

## Related Topics

- [Factory Patterns](./factory-patterns.md)
- [Arrange-Act-Assert](./arrange-act-assert.md)
- [Database Testing](../integration-testing/database-testing.md)
