---
name: nestjs-e2e-testing
description: End-to-end testing patterns in NestJS
applies_to: nestjs
category: testing
---

# NestJS E2E Testing

## Setup

```typescript
// test/app.e2e-spec.ts
import { Test, TestingModule } from '@nestjs/testing';
import { INestApplication, ValidationPipe } from '@nestjs/common';
import * as request from 'supertest';
import { AppModule } from '../src/app.module';

describe('AppController (e2e)', () => {
  let app: INestApplication;

  beforeAll(async () => {
    const moduleFixture: TestingModule = await Test.createTestingModule({
      imports: [AppModule],
    }).compile();

    app = moduleFixture.createNestApplication();

    // Apply same pipes as main.ts
    app.useGlobalPipes(
      new ValidationPipe({
        whitelist: true,
        forbidNonWhitelisted: true,
        transform: true,
      }),
    );

    await app.init();
  });

  afterAll(async () => {
    await app.close();
  });

  it('/ (GET)', () => {
    return request(app.getHttpServer())
      .get('/')
      .expect(200)
      .expect('Hello World!');
  });
});
```

## Test Database Setup

```typescript
// test/setup.ts
import { Test, TestingModule } from '@nestjs/testing';
import { INestApplication } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { ConfigModule, ConfigService } from '@nestjs/config';

export async function createTestingApp(
  imports: any[] = [],
): Promise<INestApplication> {
  const moduleFixture: TestingModule = await Test.createTestingModule({
    imports: [
      ConfigModule.forRoot({
        envFilePath: '.env.test',
      }),
      TypeOrmModule.forRootAsync({
        imports: [ConfigModule],
        useFactory: (config: ConfigService) => ({
          type: 'postgres',
          host: config.get('TEST_DB_HOST', 'localhost'),
          port: config.get('TEST_DB_PORT', 5433),
          username: config.get('TEST_DB_USER', 'test'),
          password: config.get('TEST_DB_PASSWORD', 'test'),
          database: config.get('TEST_DB_NAME', 'test_db'),
          autoLoadEntities: true,
          synchronize: true, // Only for testing!
          dropSchema: true,  // Clean slate each run
        }),
        inject: [ConfigService],
      }),
      ...imports,
    ],
  }).compile();

  const app = moduleFixture.createNestApplication();
  await app.init();
  return app;
}
```

## Testing CRUD Endpoints

```typescript
// test/users.e2e-spec.ts
import { INestApplication } from '@nestjs/common';
import * as request from 'supertest';
import { createTestingApp } from './setup';
import { UsersModule } from '../src/modules/users/users.module';

describe('UsersController (e2e)', () => {
  let app: INestApplication;
  let authToken: string;
  let createdUserId: string;

  beforeAll(async () => {
    app = await createTestingApp([UsersModule]);

    // Get auth token for protected routes
    const loginResponse = await request(app.getHttpServer())
      .post('/auth/login')
      .send({ email: 'admin@test.com', password: 'password' });

    authToken = loginResponse.body.accessToken;
  });

  afterAll(async () => {
    await app.close();
  });

  describe('POST /users', () => {
    it('should create a user', async () => {
      const createUserDto = {
        email: 'new@example.com',
        name: 'New User',
        password: 'Password123!',
      };

      const response = await request(app.getHttpServer())
        .post('/users')
        .set('Authorization', `Bearer ${authToken}`)
        .send(createUserDto)
        .expect(201);

      expect(response.body).toMatchObject({
        email: createUserDto.email,
        name: createUserDto.name,
      });
      expect(response.body.id).toBeDefined();
      expect(response.body.password).toBeUndefined(); // Password should not be returned

      createdUserId = response.body.id;
    });

    it('should return 400 for invalid data', async () => {
      const invalidDto = {
        email: 'invalid-email',
        name: '',
      };

      const response = await request(app.getHttpServer())
        .post('/users')
        .set('Authorization', `Bearer ${authToken}`)
        .send(invalidDto)
        .expect(400);

      expect(response.body.message).toContain('email');
    });

    it('should return 409 for duplicate email', async () => {
      const duplicateDto = {
        email: 'new@example.com', // Already created
        name: 'Another User',
        password: 'Password123!',
      };

      await request(app.getHttpServer())
        .post('/users')
        .set('Authorization', `Bearer ${authToken}`)
        .send(duplicateDto)
        .expect(409);
    });
  });

  describe('GET /users', () => {
    it('should return paginated users', async () => {
      const response = await request(app.getHttpServer())
        .get('/users')
        .set('Authorization', `Bearer ${authToken}`)
        .query({ page: 1, limit: 10 })
        .expect(200);

      expect(response.body).toMatchObject({
        items: expect.any(Array),
        total: expect.any(Number),
        page: 1,
        limit: 10,
      });
    });

    it('should filter users by search', async () => {
      const response = await request(app.getHttpServer())
        .get('/users')
        .set('Authorization', `Bearer ${authToken}`)
        .query({ search: 'new@example' })
        .expect(200);

      expect(response.body.items).toHaveLength(1);
      expect(response.body.items[0].email).toBe('new@example.com');
    });
  });

  describe('GET /users/:id', () => {
    it('should return user by id', async () => {
      const response = await request(app.getHttpServer())
        .get(`/users/${createdUserId}`)
        .set('Authorization', `Bearer ${authToken}`)
        .expect(200);

      expect(response.body.id).toBe(createdUserId);
    });

    it('should return 404 for non-existent user', async () => {
      await request(app.getHttpServer())
        .get('/users/00000000-0000-0000-0000-000000000000')
        .set('Authorization', `Bearer ${authToken}`)
        .expect(404);
    });
  });

  describe('PATCH /users/:id', () => {
    it('should update user', async () => {
      const updateDto = { name: 'Updated Name' };

      const response = await request(app.getHttpServer())
        .patch(`/users/${createdUserId}`)
        .set('Authorization', `Bearer ${authToken}`)
        .send(updateDto)
        .expect(200);

      expect(response.body.name).toBe('Updated Name');
    });
  });

  describe('DELETE /users/:id', () => {
    it('should delete user', async () => {
      await request(app.getHttpServer())
        .delete(`/users/${createdUserId}`)
        .set('Authorization', `Bearer ${authToken}`)
        .expect(200);

      // Verify deletion
      await request(app.getHttpServer())
        .get(`/users/${createdUserId}`)
        .set('Authorization', `Bearer ${authToken}`)
        .expect(404);
    });
  });
});
```

## Authentication Testing

```typescript
// test/auth.e2e-spec.ts
import { INestApplication } from '@nestjs/common';
import * as request from 'supertest';
import { createTestingApp } from './setup';
import { AuthModule } from '../src/modules/auth/auth.module';

describe('AuthController (e2e)', () => {
  let app: INestApplication;

  beforeAll(async () => {
    app = await createTestingApp([AuthModule]);
  });

  afterAll(async () => {
    await app.close();
  });

  describe('POST /auth/register', () => {
    it('should register new user', async () => {
      const registerDto = {
        email: 'test@example.com',
        name: 'Test User',
        password: 'Password123!',
      };

      const response = await request(app.getHttpServer())
        .post('/auth/register')
        .send(registerDto)
        .expect(201);

      expect(response.body).toMatchObject({
        user: {
          email: registerDto.email,
          name: registerDto.name,
        },
        accessToken: expect.any(String),
        refreshToken: expect.any(String),
      });
    });
  });

  describe('POST /auth/login', () => {
    it('should login with valid credentials', async () => {
      const loginDto = {
        email: 'test@example.com',
        password: 'Password123!',
      };

      const response = await request(app.getHttpServer())
        .post('/auth/login')
        .send(loginDto)
        .expect(200);

      expect(response.body.accessToken).toBeDefined();
      expect(response.body.refreshToken).toBeDefined();
    });

    it('should return 401 for invalid credentials', async () => {
      const loginDto = {
        email: 'test@example.com',
        password: 'wrong-password',
      };

      await request(app.getHttpServer())
        .post('/auth/login')
        .send(loginDto)
        .expect(401);
    });
  });

  describe('POST /auth/refresh', () => {
    it('should refresh tokens', async () => {
      // First login to get refresh token
      const loginResponse = await request(app.getHttpServer())
        .post('/auth/login')
        .send({ email: 'test@example.com', password: 'Password123!' });

      const { refreshToken } = loginResponse.body;

      const response = await request(app.getHttpServer())
        .post('/auth/refresh')
        .send({ refreshToken })
        .expect(200);

      expect(response.body.accessToken).toBeDefined();
      expect(response.body.refreshToken).toBeDefined();
    });
  });

  describe('Protected Routes', () => {
    it('should deny access without token', async () => {
      await request(app.getHttpServer())
        .get('/users/profile')
        .expect(401);
    });

    it('should deny access with invalid token', async () => {
      await request(app.getHttpServer())
        .get('/users/profile')
        .set('Authorization', 'Bearer invalid-token')
        .expect(401);
    });

    it('should allow access with valid token', async () => {
      const loginResponse = await request(app.getHttpServer())
        .post('/auth/login')
        .send({ email: 'test@example.com', password: 'Password123!' });

      const { accessToken } = loginResponse.body;

      await request(app.getHttpServer())
        .get('/users/profile')
        .set('Authorization', `Bearer ${accessToken}`)
        .expect(200);
    });
  });
});
```

## Test Utilities

```typescript
// test/utils/test-helpers.ts
import { INestApplication } from '@nestjs/common';
import * as request from 'supertest';

export class TestHelpers {
  constructor(private app: INestApplication) {}

  async createUser(data: {
    email: string;
    name: string;
    password: string;
  }): Promise<{ user: any; token: string }> {
    const response = await request(this.app.getHttpServer())
      .post('/auth/register')
      .send(data);

    return {
      user: response.body.user,
      token: response.body.accessToken,
    };
  }

  async loginAs(email: string, password: string): Promise<string> {
    const response = await request(this.app.getHttpServer())
      .post('/auth/login')
      .send({ email, password });

    return response.body.accessToken;
  }

  authenticatedRequest(token: string) {
    return {
      get: (url: string) =>
        request(this.app.getHttpServer())
          .get(url)
          .set('Authorization', `Bearer ${token}`),
      post: (url: string) =>
        request(this.app.getHttpServer())
          .post(url)
          .set('Authorization', `Bearer ${token}`),
      patch: (url: string) =>
        request(this.app.getHttpServer())
          .patch(url)
          .set('Authorization', `Bearer ${token}`),
      delete: (url: string) =>
        request(this.app.getHttpServer())
          .delete(url)
          .set('Authorization', `Bearer ${token}`),
    };
  }
}

// test/utils/database-helpers.ts
import { DataSource } from 'typeorm';

export async function cleanDatabase(dataSource: DataSource): Promise<void> {
  const entities = dataSource.entityMetadatas;

  for (const entity of entities) {
    const repository = dataSource.getRepository(entity.name);
    await repository.query(`TRUNCATE "${entity.tableName}" CASCADE`);
  }
}

export async function seedDatabase(dataSource: DataSource): Promise<void> {
  // Seed test data
  const userRepository = dataSource.getRepository('User');

  await userRepository.save([
    {
      email: 'admin@test.com',
      name: 'Admin User',
      password: 'hashed-password',
      roles: ['admin'],
    },
    {
      email: 'user@test.com',
      name: 'Regular User',
      password: 'hashed-password',
      roles: ['user'],
    },
  ]);
}
```

## Testing File Uploads

```typescript
// test/files.e2e-spec.ts
import { INestApplication } from '@nestjs/common';
import * as request from 'supertest';
import * as path from 'path';

describe('FileController (e2e)', () => {
  let app: INestApplication;
  let authToken: string;

  describe('POST /files/upload', () => {
    it('should upload a file', async () => {
      const response = await request(app.getHttpServer())
        .post('/files/upload')
        .set('Authorization', `Bearer ${authToken}`)
        .attach('file', path.join(__dirname, 'fixtures', 'test-image.jpg'))
        .expect(201);

      expect(response.body).toMatchObject({
        filename: expect.any(String),
        url: expect.any(String),
        size: expect.any(Number),
      });
    });

    it('should reject invalid file types', async () => {
      await request(app.getHttpServer())
        .post('/files/upload')
        .set('Authorization', `Bearer ${authToken}`)
        .attach('file', path.join(__dirname, 'fixtures', 'test.exe'))
        .expect(400);
    });

    it('should reject files exceeding size limit', async () => {
      await request(app.getHttpServer())
        .post('/files/upload')
        .set('Authorization', `Bearer ${authToken}`)
        .attach('file', path.join(__dirname, 'fixtures', 'large-file.jpg'))
        .expect(413);
    });
  });
});
```

## Testing WebSockets

```typescript
// test/chat.e2e-spec.ts
import { INestApplication } from '@nestjs/common';
import { io, Socket } from 'socket.io-client';
import { createTestingApp } from './setup';
import { ChatModule } from '../src/modules/chat/chat.module';

describe('ChatGateway (e2e)', () => {
  let app: INestApplication;
  let socket: Socket;
  let authToken: string;

  beforeAll(async () => {
    app = await createTestingApp([ChatModule]);
    await app.listen(3001);

    // Get auth token
    authToken = 'test-token';
  });

  afterAll(async () => {
    socket?.disconnect();
    await app.close();
  });

  beforeEach((done) => {
    socket = io('http://localhost:3001', {
      auth: { token: authToken },
      transports: ['websocket'],
    });
    socket.on('connect', done);
  });

  afterEach(() => {
    socket.disconnect();
  });

  it('should connect with valid token', (done) => {
    expect(socket.connected).toBe(true);
    done();
  });

  it('should join a room', (done) => {
    socket.emit('joinRoom', { roomId: 'room-1' });

    socket.on('joinedRoom', (data) => {
      expect(data.roomId).toBe('room-1');
      done();
    });
  });

  it('should send and receive messages', (done) => {
    const message = { roomId: 'room-1', content: 'Hello!' };

    socket.on('newMessage', (data) => {
      expect(data.content).toBe('Hello!');
      expect(data.userId).toBeDefined();
      done();
    });

    socket.emit('sendMessage', message);
  });

  it('should broadcast to room members', (done) => {
    const socket2 = io('http://localhost:3001', {
      auth: { token: authToken },
      transports: ['websocket'],
    });

    socket2.on('connect', () => {
      socket.emit('joinRoom', { roomId: 'room-2' });
      socket2.emit('joinRoom', { roomId: 'room-2' });

      socket2.on('newMessage', (data) => {
        expect(data.content).toBe('Broadcast test');
        socket2.disconnect();
        done();
      });

      setTimeout(() => {
        socket.emit('sendMessage', {
          roomId: 'room-2',
          content: 'Broadcast test',
        });
      }, 100);
    });
  });
});
```

## Jest E2E Configuration

```javascript
// test/jest-e2e.json
{
  "moduleFileExtensions": ["js", "json", "ts"],
  "rootDir": ".",
  "testEnvironment": "node",
  "testRegex": ".e2e-spec.ts$",
  "transform": {
    "^.+\\.(t|j)s$": "ts-jest"
  },
  "setupFilesAfterEnv": ["./jest.setup.ts"],
  "testTimeout": 30000,
  "maxWorkers": 1,
  "globalSetup": "./global-setup.ts",
  "globalTeardown": "./global-teardown.ts"
}

// test/jest.setup.ts
import { cleanDatabase } from './utils/database-helpers';

beforeEach(async () => {
  // Clean database before each test if needed
});

// test/global-setup.ts
import { execSync } from 'child_process';

export default async function globalSetup() {
  // Start test database container
  execSync('docker-compose -f docker-compose.test.yml up -d');

  // Wait for database to be ready
  await new Promise((resolve) => setTimeout(resolve, 5000));
}

// test/global-teardown.ts
import { execSync } from 'child_process';

export default async function globalTeardown() {
  // Stop test database container
  execSync('docker-compose -f docker-compose.test.yml down');
}
```

## Docker Compose for Testing

```yaml
# docker-compose.test.yml
version: '3.8'
services:
  test-db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
      POSTGRES_DB: test_db
    ports:
      - "5433:5432"
    tmpfs:
      - /var/lib/postgresql/data
```

## Best Practices

1. **Isolate tests**: Each test should be independent
2. **Clean state**: Reset database between test suites
3. **Use fixtures**: Organize test data in fixtures
4. **Test realistic scenarios**: Include edge cases
5. **Parallelize carefully**: Database conflicts in parallel runs
6. **Mock external services**: Don't depend on external APIs

## Checklist

- [ ] Test setup with database
- [ ] CRUD endpoint tests
- [ ] Authentication flow tests
- [ ] Authorization tests
- [ ] File upload tests
- [ ] WebSocket tests (if applicable)
- [ ] Error response tests
- [ ] Edge case coverage
- [ ] CI/CD integration
