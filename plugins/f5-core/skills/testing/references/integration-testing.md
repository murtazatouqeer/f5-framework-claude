# Integration Testing Patterns

Comprehensive guide for integration testing APIs, databases, and external services.

## Table of Contents

1. [Overview](#overview)
2. [Database Integration Tests](#database-integration-tests)
3. [API Integration Tests](#api-integration-tests)
4. [External Service Testing](#external-service-testing)
5. [Test Containers](#test-containers)

---

## Overview

Integration tests verify that multiple components work together correctly. They test the interaction between units rather than units in isolation.

### When to Use Integration Tests

| Scenario | Integration Test? |
|----------|------------------|
| Database queries | ✅ Yes |
| API endpoints | ✅ Yes |
| External service calls | ✅ Yes (mocked) |
| Business logic only | ❌ No (unit test) |
| Pure functions | ❌ No (unit test) |

### Integration Test Characteristics

- Slower than unit tests (seconds, not milliseconds)
- Test real interactions between components
- May use real databases (in-memory or containers)
- External services typically mocked
- Higher confidence than unit tests

---

## Database Integration Tests

### In-Memory Database (SQLite)

```typescript
// test/setup/test-database.ts
import { DataSource } from 'typeorm';
import { User } from '../../src/entities/user.entity';

export const testDataSource = new DataSource({
  type: 'sqlite',
  database: ':memory:',
  entities: [User],
  synchronize: true,
  dropSchema: true,
});

export async function setupTestDatabase(): Promise<DataSource> {
  if (!testDataSource.isInitialized) {
    await testDataSource.initialize();
  }
  return testDataSource;
}

export async function teardownTestDatabase(): Promise<void> {
  if (testDataSource.isInitialized) {
    await testDataSource.destroy();
  }
}
```

### NestJS Integration Test Setup

```typescript
// user.integration.spec.ts
import { Test, TestingModule } from '@nestjs/testing';
import { TypeOrmModule } from '@nestjs/typeorm';
import { UserService } from '../user.service';
import { User } from '../entities/user.entity';
import { DataSource } from 'typeorm';

describe('UserService Integration', () => {
  let service: UserService;
  let dataSource: DataSource;

  beforeAll(async () => {
    const module: TestingModule = await Test.createTestingModule({
      imports: [
        TypeOrmModule.forRoot({
          type: 'sqlite',
          database: ':memory:',
          entities: [User],
          synchronize: true,
        }),
        TypeOrmModule.forFeature([User]),
      ],
      providers: [UserService],
    }).compile();

    service = module.get<UserService>(UserService);
    dataSource = module.get<DataSource>(DataSource);
  });

  afterAll(async () => {
    await dataSource.destroy();
  });

  beforeEach(async () => {
    // Clean database before each test
    await dataSource.synchronize(true);
  });

  it('should create and retrieve user', async () => {
    const user = await service.create({
      email: 'test@example.com',
      password: 'password123',
      name: 'Test User',
    });

    const found = await service.findById(user.id);

    expect(found.email).toBe('test@example.com');
  });

  it('should update user', async () => {
    const user = await service.create({
      email: 'test@example.com',
      password: 'password123',
      name: 'Test User',
    });

    await service.update(user.id, { name: 'Updated Name' });
    const updated = await service.findById(user.id);

    expect(updated.name).toBe('Updated Name');
  });

  it('should delete user', async () => {
    const user = await service.create({
      email: 'test@example.com',
      password: 'password123',
      name: 'Test User',
    });

    await service.remove(user.id);

    await expect(service.findById(user.id)).rejects.toThrow();
  });
});
```

### Transaction Testing

```typescript
describe('OrderService with Transactions', () => {
  it('should rollback on failure', async () => {
    const initialBalance = await walletService.getBalance(userId);

    // This should fail and rollback
    await expect(
      orderService.createOrder({
        userId,
        items: [{ productId: 'invalid', quantity: 1 }],
      })
    ).rejects.toThrow();

    // Balance should be unchanged
    const finalBalance = await walletService.getBalance(userId);
    expect(finalBalance).toBe(initialBalance);
  });

  it('should commit on success', async () => {
    const order = await orderService.createOrder({
      userId,
      items: [{ productId: validProductId, quantity: 2 }],
    });

    const savedOrder = await orderService.findById(order.id);
    expect(savedOrder).toBeDefined();
    expect(savedOrder.items).toHaveLength(2);
  });
});
```

### Query Testing

```typescript
describe('UserRepository Queries', () => {
  beforeEach(async () => {
    // Seed test data
    await userRepository.save([
      { name: 'Alice', email: 'alice@test.com', status: 'active' },
      { name: 'Bob', email: 'bob@test.com', status: 'active' },
      { name: 'Charlie', email: 'charlie@test.com', status: 'inactive' },
    ]);
  });

  it('should find active users', async () => {
    const activeUsers = await userRepository.findByStatus('active');

    expect(activeUsers).toHaveLength(2);
    expect(activeUsers.map(u => u.name)).toContain('Alice');
    expect(activeUsers.map(u => u.name)).toContain('Bob');
  });

  it('should paginate results', async () => {
    const page1 = await userRepository.findPaginated({ page: 1, limit: 2 });

    expect(page1.data).toHaveLength(2);
    expect(page1.total).toBe(3);
    expect(page1.hasMore).toBe(true);
  });

  it('should search by name', async () => {
    const results = await userRepository.searchByName('Ali');

    expect(results).toHaveLength(1);
    expect(results[0].name).toBe('Alice');
  });
});
```

---

## API Integration Tests

### Basic API Testing with Supertest

```typescript
// app.e2e-spec.ts
import { Test, TestingModule } from '@nestjs/testing';
import { INestApplication, ValidationPipe } from '@nestjs/common';
import * as request from 'supertest';
import { AppModule } from '../src/app.module';

describe('App (e2e)', () => {
  let app: INestApplication;

  beforeAll(async () => {
    const moduleFixture: TestingModule = await Test.createTestingModule({
      imports: [AppModule],
    }).compile();

    app = moduleFixture.createNestApplication();

    // Apply same configuration as production
    app.useGlobalPipes(new ValidationPipe({
      whitelist: true,
      forbidNonWhitelisted: true,
      transform: true,
    }));

    await app.init();
  });

  afterAll(async () => {
    await app.close();
  });

  describe('/health (GET)', () => {
    it('should return health status', () => {
      return request(app.getHttpServer())
        .get('/health')
        .expect(200)
        .expect({ status: 'ok' });
    });
  });
});
```

### CRUD API Tests

```typescript
describe('Users API', () => {
  let app: INestApplication;
  let accessToken: string;
  let userId: string;

  beforeAll(async () => {
    // ... setup

    // Get auth token
    const loginRes = await request(app.getHttpServer())
      .post('/auth/login')
      .send({ email: 'admin@test.com', password: 'admin123' });
    accessToken = loginRes.body.access_token;
  });

  describe('POST /users', () => {
    it('should create user with valid data', async () => {
      const response = await request(app.getHttpServer())
        .post('/users')
        .set('Authorization', `Bearer ${accessToken}`)
        .send({
          email: 'new@example.com',
          password: 'Password123!',
          name: 'New User',
        })
        .expect(201);

      userId = response.body.id;
      expect(response.body.email).toBe('new@example.com');
      expect(response.body).not.toHaveProperty('password');
    });

    it('should reject invalid email', () => {
      return request(app.getHttpServer())
        .post('/users')
        .set('Authorization', `Bearer ${accessToken}`)
        .send({
          email: 'invalid-email',
          password: 'Password123!',
          name: 'Test',
        })
        .expect(400);
    });

    it('should reject without auth', () => {
      return request(app.getHttpServer())
        .post('/users')
        .send({
          email: 'test@test.com',
          password: 'Password123!',
          name: 'Test',
        })
        .expect(401);
    });
  });

  describe('GET /users', () => {
    it('should return paginated users', async () => {
      const response = await request(app.getHttpServer())
        .get('/users')
        .set('Authorization', `Bearer ${accessToken}`)
        .query({ page: 1, limit: 10 })
        .expect(200);

      expect(response.body).toHaveProperty('data');
      expect(response.body).toHaveProperty('total');
      expect(Array.isArray(response.body.data)).toBe(true);
    });

    it('should filter by status', async () => {
      const response = await request(app.getHttpServer())
        .get('/users')
        .set('Authorization', `Bearer ${accessToken}`)
        .query({ status: 'active' })
        .expect(200);

      response.body.data.forEach((user: any) => {
        expect(user.status).toBe('active');
      });
    });
  });

  describe('GET /users/:id', () => {
    it('should return single user', async () => {
      const response = await request(app.getHttpServer())
        .get(`/users/${userId}`)
        .set('Authorization', `Bearer ${accessToken}`)
        .expect(200);

      expect(response.body.id).toBe(userId);
    });

    it('should return 404 for non-existent user', () => {
      return request(app.getHttpServer())
        .get('/users/non-existent-id')
        .set('Authorization', `Bearer ${accessToken}`)
        .expect(404);
    });
  });

  describe('PATCH /users/:id', () => {
    it('should update user', async () => {
      const response = await request(app.getHttpServer())
        .patch(`/users/${userId}`)
        .set('Authorization', `Bearer ${accessToken}`)
        .send({ name: 'Updated Name' })
        .expect(200);

      expect(response.body.name).toBe('Updated Name');
    });
  });

  describe('DELETE /users/:id', () => {
    it('should delete user', () => {
      return request(app.getHttpServer())
        .delete(`/users/${userId}`)
        .set('Authorization', `Bearer ${accessToken}`)
        .expect(200);
    });
  });
});
```

### Authentication Flow Tests

```typescript
describe('Auth Flow', () => {
  describe('Registration', () => {
    it('should register new user', async () => {
      const response = await request(app.getHttpServer())
        .post('/auth/register')
        .send({
          email: 'new@test.com',
          password: 'Password123!',
          name: 'New User',
        })
        .expect(201);

      expect(response.body).toHaveProperty('id');
      expect(response.body.email).toBe('new@test.com');
    });

    it('should reject duplicate email', async () => {
      // First registration
      await request(app.getHttpServer())
        .post('/auth/register')
        .send({
          email: 'duplicate@test.com',
          password: 'Password123!',
          name: 'User 1',
        });

      // Second registration with same email
      return request(app.getHttpServer())
        .post('/auth/register')
        .send({
          email: 'duplicate@test.com',
          password: 'Password123!',
          name: 'User 2',
        })
        .expect(409);
    });
  });

  describe('Login', () => {
    beforeEach(async () => {
      await request(app.getHttpServer())
        .post('/auth/register')
        .send({
          email: 'login@test.com',
          password: 'Password123!',
          name: 'Login User',
        });
    });

    it('should return tokens on valid login', async () => {
      const response = await request(app.getHttpServer())
        .post('/auth/login')
        .send({
          email: 'login@test.com',
          password: 'Password123!',
        })
        .expect(200);

      expect(response.body).toHaveProperty('access_token');
      expect(response.body).toHaveProperty('refresh_token');
    });

    it('should reject invalid password', () => {
      return request(app.getHttpServer())
        .post('/auth/login')
        .send({
          email: 'login@test.com',
          password: 'WrongPassword',
        })
        .expect(401);
    });
  });

  describe('Token Refresh', () => {
    it('should refresh access token', async () => {
      // Login first
      const loginRes = await request(app.getHttpServer())
        .post('/auth/login')
        .send({
          email: 'test@test.com',
          password: 'Password123!',
        });

      const refreshToken = loginRes.body.refresh_token;

      // Refresh token
      const response = await request(app.getHttpServer())
        .post('/auth/refresh')
        .send({ refresh_token: refreshToken })
        .expect(200);

      expect(response.body).toHaveProperty('access_token');
    });
  });
});
```

---

## External Service Testing

### Mocking External APIs

```typescript
// test/mocks/payment.service.mock.ts
import { PaymentService } from '../../src/services/payment.service';

export const createMockPaymentService = (): jest.Mocked<PaymentService> => ({
  processPayment: jest.fn(),
  refund: jest.fn(),
  getPaymentStatus: jest.fn(),
});

// In test
describe('OrderService with Payment', () => {
  let orderService: OrderService;
  let mockPaymentService: jest.Mocked<PaymentService>;

  beforeEach(async () => {
    mockPaymentService = createMockPaymentService();

    const module = await Test.createTestingModule({
      providers: [
        OrderService,
        {
          provide: PaymentService,
          useValue: mockPaymentService,
        },
      ],
    }).compile();

    orderService = module.get(OrderService);
  });

  it('should process payment on order creation', async () => {
    mockPaymentService.processPayment.mockResolvedValue({
      transactionId: 'txn_123',
      status: 'success',
    });

    const order = await orderService.createOrder({
      userId: 'user_1',
      items: [{ productId: 'prod_1', quantity: 1 }],
      paymentMethod: 'card',
    });

    expect(mockPaymentService.processPayment).toHaveBeenCalledWith(
      expect.objectContaining({
        amount: expect.any(Number),
        currency: 'USD',
      })
    );
    expect(order.paymentStatus).toBe('paid');
  });

  it('should handle payment failure', async () => {
    mockPaymentService.processPayment.mockRejectedValue(
      new Error('Payment declined')
    );

    await expect(
      orderService.createOrder({
        userId: 'user_1',
        items: [{ productId: 'prod_1', quantity: 1 }],
        paymentMethod: 'card',
      })
    ).rejects.toThrow('Payment declined');
  });
});
```

### Using nock for HTTP Mocking

```typescript
import * as nock from 'nock';

describe('ExternalApiClient', () => {
  afterEach(() => {
    nock.cleanAll();
  });

  it('should fetch data from external API', async () => {
    // Mock external API
    nock('https://api.external.com')
      .get('/users/123')
      .reply(200, {
        id: '123',
        name: 'External User',
      });

    const client = new ExternalApiClient();
    const user = await client.getUser('123');

    expect(user.name).toBe('External User');
  });

  it('should handle API errors', async () => {
    nock('https://api.external.com')
      .get('/users/invalid')
      .reply(404, { error: 'Not found' });

    const client = new ExternalApiClient();

    await expect(client.getUser('invalid'))
      .rejects
      .toThrow('Not found');
  });

  it('should retry on transient failures', async () => {
    nock('https://api.external.com')
      .get('/users/123')
      .reply(500) // First call fails
      .get('/users/123')
      .reply(200, { id: '123', name: 'User' }); // Second call succeeds

    const client = new ExternalApiClient({ retries: 1 });
    const user = await client.getUser('123');

    expect(user.name).toBe('User');
  });
});
```

---

## Test Containers

### Using Testcontainers for Real Database Testing

```typescript
import { GenericContainer, StartedTestContainer } from 'testcontainers';
import { DataSource } from 'typeorm';

describe('User Repository with PostgreSQL', () => {
  let container: StartedTestContainer;
  let dataSource: DataSource;

  beforeAll(async () => {
    // Start PostgreSQL container
    container = await new GenericContainer('postgres:15')
      .withExposedPorts(5432)
      .withEnvironment({
        POSTGRES_USER: 'test',
        POSTGRES_PASSWORD: 'test',
        POSTGRES_DB: 'testdb',
      })
      .start();

    const port = container.getMappedPort(5432);
    const host = container.getHost();

    // Connect to container
    dataSource = new DataSource({
      type: 'postgres',
      host,
      port,
      username: 'test',
      password: 'test',
      database: 'testdb',
      entities: [User],
      synchronize: true,
    });

    await dataSource.initialize();
  }, 60000); // 60s timeout for container startup

  afterAll(async () => {
    await dataSource.destroy();
    await container.stop();
  });

  it('should use PostgreSQL-specific features', async () => {
    const repo = dataSource.getRepository(User);

    // Test PostgreSQL-specific query
    const result = await repo
      .createQueryBuilder('user')
      .where("user.metadata->>'role' = :role", { role: 'admin' })
      .getMany();

    expect(result).toBeDefined();
  });
});
```

### Redis Container

```typescript
import { GenericContainer, StartedTestContainer } from 'testcontainers';
import { createClient, RedisClientType } from 'redis';

describe('CacheService with Redis', () => {
  let container: StartedTestContainer;
  let redisClient: RedisClientType;

  beforeAll(async () => {
    container = await new GenericContainer('redis:7')
      .withExposedPorts(6379)
      .start();

    const port = container.getMappedPort(6379);
    const host = container.getHost();

    redisClient = createClient({
      url: `redis://${host}:${port}`,
    });

    await redisClient.connect();
  }, 30000);

  afterAll(async () => {
    await redisClient.quit();
    await container.stop();
  });

  beforeEach(async () => {
    await redisClient.flushAll();
  });

  it('should cache and retrieve values', async () => {
    const cacheService = new CacheService(redisClient);

    await cacheService.set('key', { data: 'value' }, 60);
    const result = await cacheService.get('key');

    expect(result).toEqual({ data: 'value' });
  });

  it('should expire cached values', async () => {
    const cacheService = new CacheService(redisClient);

    await cacheService.set('key', 'value', 1); // 1 second TTL

    // Wait for expiration
    await new Promise(resolve => setTimeout(resolve, 1500));

    const result = await cacheService.get('key');
    expect(result).toBeNull();
  });
});
```

---

## Best Practices

### Test Data Management

```typescript
// test/fixtures/users.fixture.ts
export const testUsers = {
  admin: {
    email: 'admin@test.com',
    password: 'Admin123!',
    role: 'admin',
  },
  user: {
    email: 'user@test.com',
    password: 'User123!',
    role: 'user',
  },
};

// test/helpers/database.helper.ts
export async function seedDatabase(dataSource: DataSource): Promise<void> {
  const userRepo = dataSource.getRepository(User);

  await userRepo.save(
    Object.values(testUsers).map(u => userRepo.create(u))
  );
}

export async function clearDatabase(dataSource: DataSource): Promise<void> {
  const entities = dataSource.entityMetadatas;

  for (const entity of entities) {
    const repository = dataSource.getRepository(entity.name);
    await repository.clear();
  }
}
```

### Test Isolation

```typescript
describe('Isolated Integration Tests', () => {
  beforeEach(async () => {
    // Clean slate for each test
    await clearDatabase(dataSource);
    await seedDatabase(dataSource);
  });

  // Tests are now independent
});
```

### Performance Considerations

```typescript
// Run database setup once, use transactions for isolation
describe('Fast Integration Tests', () => {
  let queryRunner: QueryRunner;

  beforeAll(async () => {
    await seedDatabase(dataSource); // Once
  });

  beforeEach(async () => {
    queryRunner = dataSource.createQueryRunner();
    await queryRunner.startTransaction();
  });

  afterEach(async () => {
    await queryRunner.rollbackTransaction();
    await queryRunner.release();
  });

  // Tests use transactions - no cleanup needed
});
```
