---
name: api-testing
description: API integration testing strategies and patterns
category: testing/integration-testing
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# API Integration Testing

## Overview

API integration tests verify that HTTP endpoints work correctly,
including request handling, response formatting, authentication,
and database interactions.

## Setup with Supertest

```typescript
// test/setup/api.ts
import { INestApplication } from '@nestjs/common';
import { Test } from '@nestjs/testing';
import { AppModule } from '@/app.module';
import request from 'supertest';

let app: INestApplication;

export async function setupTestApp(): Promise<INestApplication> {
  const moduleRef = await Test.createTestingModule({
    imports: [AppModule],
  }).compile();

  app = moduleRef.createNestApplication();
  await app.init();

  return app;
}

export function getApp(): INestApplication {
  return app;
}

export async function teardownTestApp(): Promise<void> {
  await app?.close();
}
```

## Basic API Tests

### GET Requests

```typescript
describe('GET /api/users', () => {
  it('should return list of users', async () => {
    // Arrange
    await seedUsers([
      { name: 'Alice', email: 'alice@test.com' },
      { name: 'Bob', email: 'bob@test.com' },
    ]);

    // Act
    const response = await request(app.getHttpServer())
      .get('/api/users')
      .expect(200);

    // Assert
    expect(response.body).toHaveLength(2);
    expect(response.body[0]).toHaveProperty('id');
    expect(response.body[0]).toHaveProperty('name');
    expect(response.body[0]).toHaveProperty('email');
  });

  it('should paginate results', async () => {
    await seedUsers(Array(25).fill({ name: 'Test', email: 'test@test.com' }));

    const response = await request(app.getHttpServer())
      .get('/api/users')
      .query({ page: 1, limit: 10 })
      .expect(200);

    expect(response.body.data).toHaveLength(10);
    expect(response.body.meta).toEqual({
      page: 1,
      limit: 10,
      total: 25,
      totalPages: 3,
    });
  });

  it('should filter by query params', async () => {
    await seedUsers([
      { name: 'Alice', role: 'admin' },
      { name: 'Bob', role: 'user' },
      { name: 'Charlie', role: 'admin' },
    ]);

    const response = await request(app.getHttpServer())
      .get('/api/users')
      .query({ role: 'admin' })
      .expect(200);

    expect(response.body).toHaveLength(2);
    response.body.forEach(user => {
      expect(user.role).toBe('admin');
    });
  });
});

describe('GET /api/users/:id', () => {
  it('should return user by ID', async () => {
    const user = await seedUser({ name: 'John' });

    const response = await request(app.getHttpServer())
      .get(`/api/users/${user.id}`)
      .expect(200);

    expect(response.body).toMatchObject({
      id: user.id,
      name: 'John',
    });
  });

  it('should return 404 for non-existent user', async () => {
    const response = await request(app.getHttpServer())
      .get('/api/users/non-existent-id')
      .expect(404);

    expect(response.body).toMatchObject({
      statusCode: 404,
      message: expect.stringContaining('not found'),
    });
  });
});
```

### POST Requests

```typescript
describe('POST /api/users', () => {
  it('should create user with valid data', async () => {
    const userData = {
      name: 'John Doe',
      email: 'john@example.com',
      password: 'SecurePass123!',
    };

    const response = await request(app.getHttpServer())
      .post('/api/users')
      .send(userData)
      .expect(201);

    // Assert response
    expect(response.body).toMatchObject({
      id: expect.any(String),
      name: 'John Doe',
      email: 'john@example.com',
    });
    expect(response.body).not.toHaveProperty('password');

    // Assert database
    const dbUser = await findUserById(response.body.id);
    expect(dbUser).not.toBeNull();
  });

  it('should return 400 for invalid email', async () => {
    const response = await request(app.getHttpServer())
      .post('/api/users')
      .send({
        name: 'John',
        email: 'invalid-email',
        password: 'SecurePass123!',
      })
      .expect(400);

    expect(response.body).toMatchObject({
      statusCode: 400,
      message: expect.arrayContaining([
        expect.stringContaining('email'),
      ]),
    });
  });

  it('should return 409 for duplicate email', async () => {
    await seedUser({ email: 'existing@test.com' });

    const response = await request(app.getHttpServer())
      .post('/api/users')
      .send({
        name: 'New User',
        email: 'existing@test.com',
        password: 'SecurePass123!',
      })
      .expect(409);

    expect(response.body.message).toContain('already exists');
  });
});
```

### PUT/PATCH Requests

```typescript
describe('PUT /api/users/:id', () => {
  it('should update user', async () => {
    const user = await seedUser({ name: 'Original Name' });

    const response = await request(app.getHttpServer())
      .put(`/api/users/${user.id}`)
      .set('Authorization', `Bearer ${user.token}`)
      .send({ name: 'Updated Name' })
      .expect(200);

    expect(response.body.name).toBe('Updated Name');

    // Verify in database
    const dbUser = await findUserById(user.id);
    expect(dbUser?.name).toBe('Updated Name');
  });
});

describe('PATCH /api/users/:id', () => {
  it('should partially update user', async () => {
    const user = await seedUser({
      name: 'John',
      email: 'john@test.com',
      bio: 'Original bio',
    });

    const response = await request(app.getHttpServer())
      .patch(`/api/users/${user.id}`)
      .set('Authorization', `Bearer ${user.token}`)
      .send({ bio: 'Updated bio' })
      .expect(200);

    // Bio updated
    expect(response.body.bio).toBe('Updated bio');
    // Other fields unchanged
    expect(response.body.name).toBe('John');
  });
});
```

### DELETE Requests

```typescript
describe('DELETE /api/users/:id', () => {
  it('should delete user', async () => {
    const user = await seedUser();

    await request(app.getHttpServer())
      .delete(`/api/users/${user.id}`)
      .set('Authorization', `Bearer ${adminToken}`)
      .expect(204);

    // Verify deleted
    const dbUser = await findUserById(user.id);
    expect(dbUser).toBeNull();
  });

  it('should return 403 for non-admin', async () => {
    const user = await seedUser();
    const regularUser = await seedUser({ role: 'user' });

    await request(app.getHttpServer())
      .delete(`/api/users/${user.id}`)
      .set('Authorization', `Bearer ${regularUser.token}`)
      .expect(403);
  });
});
```

## Authentication Testing

```typescript
describe('Authentication', () => {
  describe('POST /api/auth/login', () => {
    it('should return token for valid credentials', async () => {
      await seedUser({
        email: 'test@test.com',
        password: 'password123',
      });

      const response = await request(app.getHttpServer())
        .post('/api/auth/login')
        .send({
          email: 'test@test.com',
          password: 'password123',
        })
        .expect(200);

      expect(response.body).toMatchObject({
        accessToken: expect.any(String),
        refreshToken: expect.any(String),
        expiresIn: expect.any(Number),
      });
    });

    it('should return 401 for invalid credentials', async () => {
      await request(app.getHttpServer())
        .post('/api/auth/login')
        .send({
          email: 'wrong@test.com',
          password: 'wrongpassword',
        })
        .expect(401);
    });
  });

  describe('Protected routes', () => {
    it('should return 401 without token', async () => {
      await request(app.getHttpServer())
        .get('/api/users/me')
        .expect(401);
    });

    it('should return 401 with invalid token', async () => {
      await request(app.getHttpServer())
        .get('/api/users/me')
        .set('Authorization', 'Bearer invalid-token')
        .expect(401);
    });

    it('should return 401 with expired token', async () => {
      const expiredToken = generateToken({ userId: '1' }, { expiresIn: '-1h' });

      await request(app.getHttpServer())
        .get('/api/users/me')
        .set('Authorization', `Bearer ${expiredToken}`)
        .expect(401);
    });

    it('should succeed with valid token', async () => {
      const user = await seedUser();

      const response = await request(app.getHttpServer())
        .get('/api/users/me')
        .set('Authorization', `Bearer ${user.token}`)
        .expect(200);

      expect(response.body.id).toBe(user.id);
    });
  });
});
```

## Testing File Uploads

```typescript
describe('POST /api/files/upload', () => {
  it('should upload image file', async () => {
    const user = await seedUser();
    const testImagePath = path.join(__dirname, 'fixtures', 'test-image.png');

    const response = await request(app.getHttpServer())
      .post('/api/files/upload')
      .set('Authorization', `Bearer ${user.token}`)
      .attach('file', testImagePath)
      .field('description', 'Test image')
      .expect(201);

    expect(response.body).toMatchObject({
      id: expect.any(String),
      filename: expect.stringContaining('.png'),
      mimeType: 'image/png',
      size: expect.any(Number),
      url: expect.stringContaining('http'),
    });
  });

  it('should reject invalid file type', async () => {
    const user = await seedUser();
    const executablePath = path.join(__dirname, 'fixtures', 'test.exe');

    await request(app.getHttpServer())
      .post('/api/files/upload')
      .set('Authorization', `Bearer ${user.token}`)
      .attach('file', executablePath)
      .expect(400);
  });

  it('should reject oversized file', async () => {
    const user = await seedUser();
    const largeFilePath = path.join(__dirname, 'fixtures', 'large-file.zip');

    await request(app.getHttpServer())
      .post('/api/files/upload')
      .set('Authorization', `Bearer ${user.token}`)
      .attach('file', largeFilePath)
      .expect(413);
  });
});
```

## Testing Error Handling

```typescript
describe('Error Handling', () => {
  it('should return proper error format for validation errors', async () => {
    const response = await request(app.getHttpServer())
      .post('/api/users')
      .send({}) // Missing required fields
      .expect(400);

    expect(response.body).toMatchObject({
      statusCode: 400,
      error: 'Bad Request',
      message: expect.any(Array),
    });
  });

  it('should return 500 for unhandled errors', async () => {
    // Trigger internal error (e.g., disconnect database temporarily)
    await prisma.$disconnect();

    const response = await request(app.getHttpServer())
      .get('/api/users')
      .expect(500);

    expect(response.body).toMatchObject({
      statusCode: 500,
      message: 'Internal server error',
    });

    // Reconnect for other tests
    await prisma.$connect();
  });
});
```

## Response Headers Testing

```typescript
describe('Response Headers', () => {
  it('should set correct content-type', async () => {
    const response = await request(app.getHttpServer())
      .get('/api/users')
      .expect(200);

    expect(response.headers['content-type']).toMatch(/application\/json/);
  });

  it('should set cache headers', async () => {
    const response = await request(app.getHttpServer())
      .get('/api/products')
      .expect(200);

    expect(response.headers['cache-control']).toBe('public, max-age=300');
  });

  it('should set CORS headers', async () => {
    const response = await request(app.getHttpServer())
      .options('/api/users')
      .set('Origin', 'http://localhost:3000')
      .expect(204);

    expect(response.headers['access-control-allow-origin']).toBe('http://localhost:3000');
    expect(response.headers['access-control-allow-methods']).toContain('GET');
  });
});
```

## Best Practices

| Practice | Description |
|----------|-------------|
| Test all HTTP methods | GET, POST, PUT, PATCH, DELETE |
| Test status codes | Success and error codes |
| Test response bodies | Structure and content |
| Test authentication | Protected routes, tokens |
| Test validation | Required fields, formats |
| Test edge cases | Empty data, large payloads |
| Clean database | Isolate test data |

## Related Topics

- [Integration Test Basics](./integration-test-basics.md)
- [Database Testing](./database-testing.md)
- [External Service Testing](./external-service-testing.md)
