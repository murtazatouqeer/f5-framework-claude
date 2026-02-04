# NestJS Testing Patterns

Comprehensive testing strategies for NestJS applications with Jest.

## Table of Contents

1. [Unit Testing](#unit-testing)
2. [Integration Testing](#integration-testing)
3. [E2E Testing](#e2e-testing)
4. [Mocking Patterns](#mocking-patterns)
5. [Coverage Configuration](#coverage-configuration)

---

## Unit Testing

### Test Structure

```
src/modules/user/
├── __tests__/
│   ├── user.service.spec.ts      # Service unit tests
│   ├── user.controller.spec.ts   # Controller unit tests
│   └── user.guard.spec.ts        # Guard unit tests
└── ...
```

### Service Testing

```typescript
// user.service.spec.ts
import { Test, TestingModule } from '@nestjs/testing';
import { getRepositoryToken } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { UserService } from '../user.service';
import { User } from '../entities/user.entity';
import { CreateUserDto } from '../dto/create-user.dto';
import { ConflictException, NotFoundException } from '@nestjs/common';

describe('UserService', () => {
  let service: UserService;
  let repository: jest.Mocked<Repository<User>>;

  const mockRepository = {
    create: jest.fn(),
    save: jest.fn(),
    findOne: jest.fn(),
    find: jest.fn(),
    update: jest.fn(),
    delete: jest.fn(),
    createQueryBuilder: jest.fn(),
  };

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        UserService,
        {
          provide: getRepositoryToken(User),
          useValue: mockRepository,
        },
      ],
    }).compile();

    service = module.get<UserService>(UserService);
    repository = module.get(getRepositoryToken(User));
    jest.clearAllMocks();
  });

  describe('create', () => {
    const createDto: CreateUserDto = {
      email: 'test@example.com',
      password: 'password123',
      name: 'Test User',
    };

    it('should create a new user', async () => {
      const expectedUser = { id: '1', ...createDto };
      mockRepository.findOne.mockResolvedValue(null);
      mockRepository.create.mockReturnValue(expectedUser);
      mockRepository.save.mockResolvedValue(expectedUser);

      const result = await service.create(createDto);

      expect(mockRepository.findOne).toHaveBeenCalledWith({
        where: { email: createDto.email },
      });
      expect(mockRepository.create).toHaveBeenCalledWith(createDto);
      expect(result).toEqual(expectedUser);
    });

    it('should throw ConflictException if email exists', async () => {
      mockRepository.findOne.mockResolvedValue({ id: '1', email: createDto.email });

      await expect(service.create(createDto)).rejects.toThrow(ConflictException);
    });
  });

  describe('findById', () => {
    it('should return user if found', async () => {
      const user = { id: '1', email: 'test@example.com' };
      mockRepository.findOne.mockResolvedValue(user);

      const result = await service.findById('1');

      expect(result).toEqual(user);
    });

    it('should throw NotFoundException if not found', async () => {
      mockRepository.findOne.mockResolvedValue(null);

      await expect(service.findById('1')).rejects.toThrow(NotFoundException);
    });
  });

  describe('findAll with pagination', () => {
    it('should return paginated results', async () => {
      const users = [{ id: '1' }, { id: '2' }];
      const queryBuilder = {
        skip: jest.fn().mockReturnThis(),
        take: jest.fn().mockReturnThis(),
        orderBy: jest.fn().mockReturnThis(),
        getManyAndCount: jest.fn().mockResolvedValue([users, 10]),
      };
      mockRepository.createQueryBuilder.mockReturnValue(queryBuilder);

      const result = await service.findAll({ page: 1, limit: 10 });

      expect(result.data).toEqual(users);
      expect(result.total).toBe(10);
    });
  });
});
```

### Controller Testing

```typescript
// user.controller.spec.ts
import { Test, TestingModule } from '@nestjs/testing';
import { UserController } from '../user.controller';
import { UserService } from '../user.service';
import { CreateUserDto } from '../dto/create-user.dto';
import { User } from '../entities/user.entity';

describe('UserController', () => {
  let controller: UserController;
  let service: jest.Mocked<UserService>;

  const mockUserService = {
    create: jest.fn(),
    findById: jest.fn(),
    findAll: jest.fn(),
    update: jest.fn(),
    remove: jest.fn(),
  };

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      controllers: [UserController],
      providers: [
        {
          provide: UserService,
          useValue: mockUserService,
        },
      ],
    }).compile();

    controller = module.get<UserController>(UserController);
    service = module.get(UserService);
    jest.clearAllMocks();
  });

  describe('create', () => {
    it('should create user and return response', async () => {
      const dto: CreateUserDto = {
        email: 'test@example.com',
        password: 'password123',
        name: 'Test',
      };
      const expected: User = { id: '1', ...dto } as User;
      mockUserService.create.mockResolvedValue(expected);

      const result = await controller.create(dto);

      expect(service.create).toHaveBeenCalledWith(dto);
      expect(result).toEqual(expected);
    });
  });

  describe('findOne', () => {
    it('should return user by id', async () => {
      const user = { id: '1', email: 'test@example.com' };
      mockUserService.findById.mockResolvedValue(user);

      const result = await controller.findOne('1');

      expect(result).toEqual(user);
    });
  });

  describe('findAll', () => {
    it('should return paginated users', async () => {
      const paginatedResult = {
        data: [{ id: '1' }],
        total: 1,
        page: 1,
        limit: 10,
      };
      mockUserService.findAll.mockResolvedValue(paginatedResult);

      const result = await controller.findAll({ page: 1, limit: 10 });

      expect(result).toEqual(paginatedResult);
    });
  });
});
```

### Guard Testing

```typescript
// roles.guard.spec.ts
import { Test, TestingModule } from '@nestjs/testing';
import { Reflector } from '@nestjs/core';
import { ExecutionContext } from '@nestjs/common';
import { RolesGuard } from '../guards/roles.guard';
import { Role } from '../enums/role.enum';

describe('RolesGuard', () => {
  let guard: RolesGuard;
  let reflector: Reflector;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        RolesGuard,
        {
          provide: Reflector,
          useValue: {
            getAllAndOverride: jest.fn(),
          },
        },
      ],
    }).compile();

    guard = module.get<RolesGuard>(RolesGuard);
    reflector = module.get<Reflector>(Reflector);
  });

  const mockExecutionContext = (user: any): ExecutionContext => ({
    switchToHttp: () => ({
      getRequest: () => ({ user }),
    }),
    getHandler: () => jest.fn(),
    getClass: () => jest.fn(),
  } as unknown as ExecutionContext);

  it('should allow access when no roles required', () => {
    jest.spyOn(reflector, 'getAllAndOverride').mockReturnValue(undefined);

    const result = guard.canActivate(mockExecutionContext({ roles: [] }));

    expect(result).toBe(true);
  });

  it('should allow access when user has required role', () => {
    jest.spyOn(reflector, 'getAllAndOverride').mockReturnValue([Role.ADMIN]);

    const result = guard.canActivate(
      mockExecutionContext({ roles: [Role.ADMIN] })
    );

    expect(result).toBe(true);
  });

  it('should deny access when user lacks required role', () => {
    jest.spyOn(reflector, 'getAllAndOverride').mockReturnValue([Role.ADMIN]);

    const result = guard.canActivate(
      mockExecutionContext({ roles: [Role.USER] })
    );

    expect(result).toBe(false);
  });
});
```

### Pipe Testing

```typescript
// validation.pipe.spec.ts
import { ValidationPipe, BadRequestException } from '@nestjs/common';
import { IsString, IsEmail, MinLength } from 'class-validator';

class TestDto {
  @IsEmail()
  email: string;

  @IsString()
  @MinLength(8)
  password: string;
}

describe('ValidationPipe', () => {
  let pipe: ValidationPipe;

  beforeEach(() => {
    pipe = new ValidationPipe({
      whitelist: true,
      forbidNonWhitelisted: true,
      transform: true,
    });
  });

  it('should pass valid data', async () => {
    const dto = { email: 'test@example.com', password: 'password123' };

    const result = await pipe.transform(dto, {
      type: 'body',
      metatype: TestDto,
    });

    expect(result).toEqual(dto);
  });

  it('should reject invalid email', async () => {
    const dto = { email: 'invalid', password: 'password123' };

    await expect(
      pipe.transform(dto, { type: 'body', metatype: TestDto })
    ).rejects.toThrow(BadRequestException);
  });

  it('should reject short password', async () => {
    const dto = { email: 'test@example.com', password: 'short' };

    await expect(
      pipe.transform(dto, { type: 'body', metatype: TestDto })
    ).rejects.toThrow(BadRequestException);
  });

  it('should strip unknown properties with whitelist', async () => {
    const dto = {
      email: 'test@example.com',
      password: 'password123',
      unknown: 'field',
    };

    const result = await pipe.transform(dto, {
      type: 'body',
      metatype: TestDto,
    });

    expect(result).not.toHaveProperty('unknown');
  });
});
```

### Interceptor Testing

```typescript
// transform.interceptor.spec.ts
import { TransformInterceptor } from '../interceptors/transform.interceptor';
import { of } from 'rxjs';
import { ExecutionContext, CallHandler } from '@nestjs/common';

describe('TransformInterceptor', () => {
  let interceptor: TransformInterceptor<any>;

  beforeEach(() => {
    interceptor = new TransformInterceptor();
  });

  it('should wrap response in data property', (done) => {
    const mockData = { id: 1, name: 'Test' };
    const mockContext = {} as ExecutionContext;
    const mockCallHandler: CallHandler = {
      handle: () => of(mockData),
    };

    interceptor.intercept(mockContext, mockCallHandler).subscribe({
      next: (value) => {
        expect(value).toEqual({ data: mockData });
        done();
      },
    });
  });

  it('should handle null response', (done) => {
    const mockContext = {} as ExecutionContext;
    const mockCallHandler: CallHandler = {
      handle: () => of(null),
    };

    interceptor.intercept(mockContext, mockCallHandler).subscribe({
      next: (value) => {
        expect(value).toEqual({ data: null });
        done();
      },
    });
  });
});
```

---

## Integration Testing

### Database Integration Tests

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

### Module Integration Tests

```typescript
// auth.integration.spec.ts
import { Test, TestingModule } from '@nestjs/testing';
import { JwtModule } from '@nestjs/jwt';
import { PassportModule } from '@nestjs/passport';
import { AuthService } from '../auth.service';
import { UserService } from '../../user/user.service';
import { JwtStrategy } from '../strategies/jwt.strategy';
import { LocalStrategy } from '../strategies/local.strategy';

describe('AuthModule Integration', () => {
  let authService: AuthService;
  let userService: jest.Mocked<UserService>;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      imports: [
        PassportModule.register({ defaultStrategy: 'jwt' }),
        JwtModule.register({
          secret: 'test-secret',
          signOptions: { expiresIn: '1h' },
        }),
      ],
      providers: [
        AuthService,
        JwtStrategy,
        LocalStrategy,
        {
          provide: UserService,
          useValue: {
            findByEmail: jest.fn(),
            validatePassword: jest.fn(),
          },
        },
      ],
    }).compile();

    authService = module.get<AuthService>(AuthService);
    userService = module.get(UserService);
  });

  it('should validate user and return JWT', async () => {
    const user = {
      id: '1',
      email: 'test@example.com',
      roles: ['user'],
    };
    userService.findByEmail.mockResolvedValue(user);
    userService.validatePassword.mockResolvedValue(true);

    const result = await authService.login(user);

    expect(result).toHaveProperty('access_token');
    expect(typeof result.access_token).toBe('string');
  });
});
```

### Test Database Configuration

```typescript
// test/test-database.config.ts
import { TypeOrmModuleOptions } from '@nestjs/typeorm';

export const testDatabaseConfig: TypeOrmModuleOptions = {
  type: 'sqlite',
  database: ':memory:',
  entities: ['src/**/*.entity.ts'],
  synchronize: true,
  dropSchema: true,
};

// Alternative: PostgreSQL test container
export const testPostgresConfig: TypeOrmModuleOptions = {
  type: 'postgres',
  host: process.env.TEST_DB_HOST || 'localhost',
  port: parseInt(process.env.TEST_DB_PORT, 10) || 5433,
  username: process.env.TEST_DB_USER || 'test',
  password: process.env.TEST_DB_PASSWORD || 'test',
  database: process.env.TEST_DB_NAME || 'test_db',
  entities: ['src/**/*.entity.ts'],
  synchronize: true,
};
```

---

## E2E Testing

### Setup

```typescript
// test/app.e2e-spec.ts
import { Test, TestingModule } from '@nestjs/testing';
import { INestApplication, ValidationPipe } from '@nestjs/common';
import * as request from 'supertest';
import { AppModule } from '../src/app.module';
import { DataSource } from 'typeorm';

describe('AppController (e2e)', () => {
  let app: INestApplication;
  let dataSource: DataSource;

  beforeAll(async () => {
    const moduleFixture: TestingModule = await Test.createTestingModule({
      imports: [AppModule],
    }).compile();

    app = moduleFixture.createNestApplication();

    // Apply same pipes as production
    app.useGlobalPipes(new ValidationPipe({
      whitelist: true,
      forbidNonWhitelisted: true,
      transform: true,
    }));

    await app.init();

    dataSource = moduleFixture.get<DataSource>(DataSource);
  });

  afterAll(async () => {
    await dataSource.destroy();
    await app.close();
  });

  beforeEach(async () => {
    // Clean database
    await dataSource.synchronize(true);
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

### Authentication E2E Tests

```typescript
// test/auth.e2e-spec.ts
import { Test, TestingModule } from '@nestjs/testing';
import { INestApplication, ValidationPipe } from '@nestjs/common';
import * as request from 'supertest';
import { AppModule } from '../src/app.module';
import { DataSource } from 'typeorm';

describe('Auth (e2e)', () => {
  let app: INestApplication;
  let dataSource: DataSource;
  let accessToken: string;

  beforeAll(async () => {
    const moduleFixture: TestingModule = await Test.createTestingModule({
      imports: [AppModule],
    }).compile();

    app = moduleFixture.createNestApplication();
    app.useGlobalPipes(new ValidationPipe({
      whitelist: true,
      transform: true,
    }));
    await app.init();

    dataSource = moduleFixture.get<DataSource>(DataSource);
  });

  afterAll(async () => {
    await dataSource.destroy();
    await app.close();
  });

  beforeEach(async () => {
    await dataSource.synchronize(true);
  });

  describe('/auth/register (POST)', () => {
    it('should register new user', () => {
      return request(app.getHttpServer())
        .post('/auth/register')
        .send({
          email: 'test@example.com',
          password: 'Password123!',
          name: 'Test User',
        })
        .expect(201)
        .expect((res) => {
          expect(res.body).toHaveProperty('id');
          expect(res.body.email).toBe('test@example.com');
        });
    });

    it('should reject duplicate email', async () => {
      // First registration
      await request(app.getHttpServer())
        .post('/auth/register')
        .send({
          email: 'test@example.com',
          password: 'Password123!',
          name: 'Test User',
        });

      // Duplicate attempt
      return request(app.getHttpServer())
        .post('/auth/register')
        .send({
          email: 'test@example.com',
          password: 'Password123!',
          name: 'Test User 2',
        })
        .expect(409);
    });

    it('should validate password strength', () => {
      return request(app.getHttpServer())
        .post('/auth/register')
        .send({
          email: 'test@example.com',
          password: 'weak',
          name: 'Test User',
        })
        .expect(400);
    });
  });

  describe('/auth/login (POST)', () => {
    beforeEach(async () => {
      // Create user for login tests
      await request(app.getHttpServer())
        .post('/auth/register')
        .send({
          email: 'login@example.com',
          password: 'Password123!',
          name: 'Login User',
        });
    });

    it('should return access token', async () => {
      const response = await request(app.getHttpServer())
        .post('/auth/login')
        .send({
          email: 'login@example.com',
          password: 'Password123!',
        })
        .expect(200);

      expect(response.body).toHaveProperty('access_token');
      accessToken = response.body.access_token;
    });

    it('should reject invalid credentials', () => {
      return request(app.getHttpServer())
        .post('/auth/login')
        .send({
          email: 'login@example.com',
          password: 'wrongpassword',
        })
        .expect(401);
    });
  });

  describe('/auth/profile (GET)', () => {
    beforeEach(async () => {
      // Create and login user
      await request(app.getHttpServer())
        .post('/auth/register')
        .send({
          email: 'profile@example.com',
          password: 'Password123!',
          name: 'Profile User',
        });

      const loginRes = await request(app.getHttpServer())
        .post('/auth/login')
        .send({
          email: 'profile@example.com',
          password: 'Password123!',
        });

      accessToken = loginRes.body.access_token;
    });

    it('should return user profile with valid token', () => {
      return request(app.getHttpServer())
        .get('/auth/profile')
        .set('Authorization', `Bearer ${accessToken}`)
        .expect(200)
        .expect((res) => {
          expect(res.body.email).toBe('profile@example.com');
        });
    });

    it('should reject without token', () => {
      return request(app.getHttpServer())
        .get('/auth/profile')
        .expect(401);
    });

    it('should reject invalid token', () => {
      return request(app.getHttpServer())
        .get('/auth/profile')
        .set('Authorization', 'Bearer invalid-token')
        .expect(401);
    });
  });
});
```

### CRUD E2E Tests

```typescript
// test/users.e2e-spec.ts
import { Test, TestingModule } from '@nestjs/testing';
import { INestApplication, ValidationPipe } from '@nestjs/common';
import * as request from 'supertest';
import { AppModule } from '../src/app.module';

describe('Users CRUD (e2e)', () => {
  let app: INestApplication;
  let adminToken: string;
  let userId: string;

  beforeAll(async () => {
    const moduleFixture = await Test.createTestingModule({
      imports: [AppModule],
    }).compile();

    app = moduleFixture.createNestApplication();
    app.useGlobalPipes(new ValidationPipe({ transform: true }));
    await app.init();

    // Login as admin
    const loginRes = await request(app.getHttpServer())
      .post('/auth/login')
      .send({ email: 'admin@example.com', password: 'admin123' });
    adminToken = loginRes.body.access_token;
  });

  afterAll(async () => {
    await app.close();
  });

  describe('POST /users', () => {
    it('should create user (admin only)', async () => {
      const response = await request(app.getHttpServer())
        .post('/users')
        .set('Authorization', `Bearer ${adminToken}`)
        .send({
          email: 'new@example.com',
          password: 'Password123!',
          name: 'New User',
        })
        .expect(201);

      userId = response.body.id;
      expect(response.body.email).toBe('new@example.com');
    });
  });

  describe('GET /users', () => {
    it('should return paginated users', async () => {
      const response = await request(app.getHttpServer())
        .get('/users')
        .set('Authorization', `Bearer ${adminToken}`)
        .query({ page: 1, limit: 10 })
        .expect(200);

      expect(response.body).toHaveProperty('data');
      expect(response.body).toHaveProperty('total');
      expect(Array.isArray(response.body.data)).toBe(true);
    });
  });

  describe('GET /users/:id', () => {
    it('should return single user', async () => {
      const response = await request(app.getHttpServer())
        .get(`/users/${userId}`)
        .set('Authorization', `Bearer ${adminToken}`)
        .expect(200);

      expect(response.body.id).toBe(userId);
    });

    it('should return 404 for non-existent user', () => {
      return request(app.getHttpServer())
        .get('/users/non-existent-id')
        .set('Authorization', `Bearer ${adminToken}`)
        .expect(404);
    });
  });

  describe('PATCH /users/:id', () => {
    it('should update user', async () => {
      const response = await request(app.getHttpServer())
        .patch(`/users/${userId}`)
        .set('Authorization', `Bearer ${adminToken}`)
        .send({ name: 'Updated Name' })
        .expect(200);

      expect(response.body.name).toBe('Updated Name');
    });
  });

  describe('DELETE /users/:id', () => {
    it('should delete user', () => {
      return request(app.getHttpServer())
        .delete(`/users/${userId}`)
        .set('Authorization', `Bearer ${adminToken}`)
        .expect(200);
    });
  });
});
```

### E2E Test Configuration

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
  "moduleNameMapper": {
    "^@/(.*)$": "<rootDir>/../src/$1"
  },
  "setupFilesAfterEnv": ["<rootDir>/setup.ts"],
  "testTimeout": 30000
}
```

```typescript
// test/setup.ts
import { DataSource } from 'typeorm';

// Global test setup
beforeAll(async () => {
  // Any global setup
});

afterAll(async () => {
  // Any global cleanup
});
```

---

## Mocking Patterns

### Repository Mock Factory

```typescript
// test/utils/mock-repository.ts
import { Repository } from 'typeorm';

export type MockRepository<T = any> = Partial<Record<keyof Repository<T>, jest.Mock>>;

export const createMockRepository = <T = any>(): MockRepository<T> => ({
  find: jest.fn(),
  findOne: jest.fn(),
  findOneBy: jest.fn(),
  save: jest.fn(),
  create: jest.fn(),
  update: jest.fn(),
  delete: jest.fn(),
  remove: jest.fn(),
  count: jest.fn(),
  createQueryBuilder: jest.fn(() => ({
    where: jest.fn().mockReturnThis(),
    andWhere: jest.fn().mockReturnThis(),
    orderBy: jest.fn().mockReturnThis(),
    skip: jest.fn().mockReturnThis(),
    take: jest.fn().mockReturnThis(),
    getMany: jest.fn(),
    getManyAndCount: jest.fn(),
    getOne: jest.fn(),
  })),
});
```

### Service Mock Factory

```typescript
// test/utils/mock-services.ts
export const createMockUserService = () => ({
  create: jest.fn(),
  findById: jest.fn(),
  findByEmail: jest.fn(),
  findAll: jest.fn(),
  update: jest.fn(),
  remove: jest.fn(),
  validatePassword: jest.fn(),
});

export const createMockAuthService = () => ({
  validateUser: jest.fn(),
  login: jest.fn(),
  register: jest.fn(),
  refreshToken: jest.fn(),
});

export const createMockCacheManager = () => ({
  get: jest.fn(),
  set: jest.fn(),
  del: jest.fn(),
  reset: jest.fn(),
});
```

### External Service Mocks

```typescript
// test/utils/mock-external.ts
export const createMockHttpService = () => ({
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  delete: jest.fn(),
  request: jest.fn(),
});

export const createMockMailService = () => ({
  send: jest.fn().mockResolvedValue({ messageId: 'test-message-id' }),
  sendTemplate: jest.fn().mockResolvedValue({ messageId: 'test-message-id' }),
});

export const createMockStorageService = () => ({
  upload: jest.fn().mockResolvedValue({ url: 'https://storage.example.com/file.jpg' }),
  delete: jest.fn().mockResolvedValue(true),
  getSignedUrl: jest.fn().mockResolvedValue('https://signed-url.example.com'),
});
```

### Testing Module Builder

```typescript
// test/utils/test-module-builder.ts
import { Test, TestingModule } from '@nestjs/testing';
import { getRepositoryToken } from '@nestjs/typeorm';
import { createMockRepository } from './mock-repository';

interface TestModuleConfig {
  providers: any[];
  entities?: any[];
  services?: Record<string, any>;
}

export async function createTestModule(config: TestModuleConfig): Promise<TestingModule> {
  const providers = [...config.providers];

  // Add entity repositories
  if (config.entities) {
    for (const entity of config.entities) {
      providers.push({
        provide: getRepositoryToken(entity),
        useValue: createMockRepository(),
      });
    }
  }

  // Add service mocks
  if (config.services) {
    for (const [token, mock] of Object.entries(config.services)) {
      providers.push({
        provide: token,
        useValue: mock,
      });
    }
  }

  return Test.createTestingModule({
    providers,
  }).compile();
}
```

### Request Mock Helper

```typescript
// test/utils/mock-request.ts
import { ExecutionContext } from '@nestjs/common';

export function createMockExecutionContext(overrides: {
  user?: any;
  body?: any;
  params?: any;
  query?: any;
  headers?: any;
}): ExecutionContext {
  const request = {
    user: overrides.user || { id: '1', roles: ['user'] },
    body: overrides.body || {},
    params: overrides.params || {},
    query: overrides.query || {},
    headers: overrides.headers || {},
  };

  return {
    switchToHttp: () => ({
      getRequest: () => request,
      getResponse: () => ({
        status: jest.fn().mockReturnThis(),
        json: jest.fn().mockReturnThis(),
      }),
    }),
    getHandler: () => jest.fn(),
    getClass: () => jest.fn(),
    getType: () => 'http',
    getArgs: () => [request],
    getArgByIndex: (index: number) => [request][index],
  } as unknown as ExecutionContext;
}
```

---

## Coverage Configuration

### Jest Coverage Setup

```javascript
// jest.config.js
module.exports = {
  moduleFileExtensions: ['js', 'json', 'ts'],
  rootDir: 'src',
  testRegex: '.*\\.spec\\.ts$',
  transform: {
    '^.+\\.(t|j)s$': 'ts-jest',
  },
  collectCoverageFrom: [
    '**/*.ts',
    '!**/node_modules/**',
    '!**/*.module.ts',
    '!**/main.ts',
    '!**/*.dto.ts',
    '!**/*.entity.ts',
    '!**/*.interface.ts',
    '!**/__tests__/**',
  ],
  coverageDirectory: '../coverage',
  testEnvironment: 'node',
  coverageReporters: ['text', 'lcov', 'html', 'json-summary'],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
    // Higher thresholds for critical modules
    './src/modules/auth/**/*.ts': {
      branches: 90,
      functions: 90,
      lines: 90,
      statements: 90,
    },
    './src/modules/payment/**/*.ts': {
      branches: 90,
      functions: 90,
      lines: 90,
      statements: 90,
    },
  },
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
    '^@common/(.*)$': '<rootDir>/common/$1',
    '^@modules/(.*)$': '<rootDir>/modules/$1',
  },
};
```

### Coverage Scripts

```json
// package.json
{
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch",
    "test:cov": "jest --coverage",
    "test:debug": "node --inspect-brk -r tsconfig-paths/register -r ts-node/register node_modules/.bin/jest --runInBand",
    "test:e2e": "jest --config ./test/jest-e2e.json",
    "test:e2e:cov": "jest --config ./test/jest-e2e.json --coverage",
    "test:ci": "jest --coverage --ci --reporters=default --reporters=jest-junit"
  }
}
```

### Coverage Report Analysis

```typescript
// scripts/check-coverage.ts
import * as fs from 'fs';

interface CoverageSummary {
  total: {
    lines: { pct: number };
    statements: { pct: number };
    functions: { pct: number };
    branches: { pct: number };
  };
}

const THRESHOLD = 80;
const CRITICAL_THRESHOLD = 90;

function checkCoverage(): void {
  const summaryPath = './coverage/coverage-summary.json';

  if (!fs.existsSync(summaryPath)) {
    console.error('Coverage report not found. Run tests first.');
    process.exit(1);
  }

  const summary: CoverageSummary = JSON.parse(
    fs.readFileSync(summaryPath, 'utf-8')
  );

  const { lines, statements, functions, branches } = summary.total;

  console.log('\n📊 Coverage Report');
  console.log('==================');
  console.log(`Lines:      ${lines.pct}%`);
  console.log(`Statements: ${statements.pct}%`);
  console.log(`Functions:  ${functions.pct}%`);
  console.log(`Branches:   ${branches.pct}%`);

  const allPass =
    lines.pct >= THRESHOLD &&
    statements.pct >= THRESHOLD &&
    functions.pct >= THRESHOLD &&
    branches.pct >= THRESHOLD;

  if (!allPass) {
    console.error(`\n❌ Coverage below ${THRESHOLD}% threshold`);
    process.exit(1);
  }

  console.log(`\n✅ All coverage metrics above ${THRESHOLD}%`);
}

checkCoverage();
```

---

## F5 Quality Gates Mapping

| Gate | Testing Requirement | Implementation |
|------|-------------------|----------------|
| G2.5 | Code Review | Unit tests exist for services, guards, pipes |
| G3 | Testing Gate | 80% coverage, E2E tests for critical paths |
| G4 | Integration Gate | Integration tests with real database |
| G5 | Production Ready | Performance tests, security tests |

## Quick Reference

### Test Commands

```bash
# Unit tests
npm run test                    # Run all unit tests
npm run test:watch             # Watch mode
npm run test:cov               # With coverage
npm run test -- --testPathPattern=user  # Specific module

# E2E tests
npm run test:e2e               # Run all E2E tests
npm run test:e2e:cov           # E2E with coverage

# Debug
npm run test:debug             # Debug mode

# CI/CD
npm run test:ci                # CI mode with reports
```

### Test File Naming

| Type | Pattern | Example |
|------|---------|---------|
| Unit Test | `*.spec.ts` | `user.service.spec.ts` |
| Integration | `*.integration.spec.ts` | `user.integration.spec.ts` |
| E2E | `*.e2e-spec.ts` | `auth.e2e-spec.ts` |

### Best Practices Checklist

- [ ] Test one thing per test case
- [ ] Use descriptive test names
- [ ] Follow AAA pattern (Arrange, Act, Assert)
- [ ] Mock external dependencies
- [ ] Clean up after tests
- [ ] Use factories for test data
- [ ] Test edge cases and error paths
- [ ] Keep tests independent
- [ ] Maintain 80%+ coverage
- [ ] Run tests in CI/CD pipeline
