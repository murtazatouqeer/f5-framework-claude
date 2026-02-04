---
name: nestjs-test
description: NestJS test file templates
applies_to: nestjs
category: template
---

# NestJS Test Template

## Service Test

```typescript
// modules/{{module}}/__tests__/{{entity}}.service.spec.ts
import { Test, TestingModule } from '@nestjs/testing';
import { getRepositoryToken } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { NotFoundException } from '@nestjs/common';
import { {{Entity}}Service } from '../{{entity}}.service';
import { {{Entity}} } from '../entities/{{entity}}.entity';
import { Create{{Entity}}Dto } from '../dto/create-{{entity}}.dto';
import { Update{{Entity}}Dto } from '../dto/update-{{entity}}.dto';

describe('{{Entity}}Service', () => {
  let service: {{Entity}}Service;
  let repository: jest.Mocked<Repository<{{Entity}}>>;

  const mock{{Entity}}: {{Entity}} = {
    id: '{{uuid}}',
    {{field}}: '{{value}}',
    createdAt: new Date(),
    updatedAt: new Date(),
  } as {{Entity}};

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        {{Entity}}Service,
        {
          provide: getRepositoryToken({{Entity}}),
          useValue: {
            findOne: jest.fn(),
            find: jest.fn(),
            findAndCount: jest.fn(),
            create: jest.fn(),
            save: jest.fn(),
            update: jest.fn(),
            delete: jest.fn(),
            softDelete: jest.fn(),
          },
        },
      ],
    }).compile();

    service = module.get<{{Entity}}Service>({{Entity}}Service);
    repository = module.get(getRepositoryToken({{Entity}}));
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('findById', () => {
    it('should return {{entity}} when found', async () => {
      repository.findOne.mockResolvedValue(mock{{Entity}});

      const result = await service.findById('{{uuid}}');

      expect(result).toEqual(mock{{Entity}});
      expect(repository.findOne).toHaveBeenCalledWith({
        where: { id: '{{uuid}}' },
      });
    });

    it('should throw NotFoundException when {{entity}} not found', async () => {
      repository.findOne.mockResolvedValue(null);

      await expect(service.findById('nonexistent')).rejects.toThrow(
        NotFoundException,
      );
    });
  });

  describe('create', () => {
    const createDto: Create{{Entity}}Dto = {
      {{field}}: '{{value}}',
    };

    it('should create {{entity}} successfully', async () => {
      repository.create.mockReturnValue(mock{{Entity}});
      repository.save.mockResolvedValue(mock{{Entity}});

      const result = await service.create(createDto);

      expect(result).toEqual(mock{{Entity}});
      expect(repository.create).toHaveBeenCalledWith(createDto);
      expect(repository.save).toHaveBeenCalled();
    });
  });

  describe('update', () => {
    const updateDto: Update{{Entity}}Dto = {
      {{field}}: 'updated value',
    };

    it('should update {{entity}} successfully', async () => {
      repository.findOne.mockResolvedValue(mock{{Entity}});
      repository.save.mockResolvedValue({ ...mock{{Entity}}, ...updateDto });

      const result = await service.update('{{uuid}}', updateDto);

      expect(result.{{field}}).toBe('updated value');
    });

    it('should throw NotFoundException for nonexistent {{entity}}', async () => {
      repository.findOne.mockResolvedValue(null);

      await expect(service.update('nonexistent', updateDto)).rejects.toThrow(
        NotFoundException,
      );
    });
  });

  describe('delete', () => {
    it('should delete {{entity}} successfully', async () => {
      repository.findOne.mockResolvedValue(mock{{Entity}});
      repository.softDelete.mockResolvedValue({ affected: 1 } as any);

      await service.delete('{{uuid}}');

      expect(repository.softDelete).toHaveBeenCalledWith('{{uuid}}');
    });
  });
});
```

## Controller Test

```typescript
// modules/{{module}}/__tests__/{{entity}}.controller.spec.ts
import { Test, TestingModule } from '@nestjs/testing';
import { {{Entity}}Controller } from '../{{entity}}.controller';
import { {{Entity}}Service } from '../{{entity}}.service';
import { Create{{Entity}}Dto } from '../dto/create-{{entity}}.dto';
import { Update{{Entity}}Dto } from '../dto/update-{{entity}}.dto';

describe('{{Entity}}Controller', () => {
  let controller: {{Entity}}Controller;
  let service: jest.Mocked<{{Entity}}Service>;

  const mock{{Entity}} = {
    id: '{{uuid}}',
    {{field}}: '{{value}}',
    createdAt: new Date(),
    updatedAt: new Date(),
  };

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      controllers: [{{Entity}}Controller],
      providers: [
        {
          provide: {{Entity}}Service,
          useValue: {
            findAll: jest.fn(),
            findById: jest.fn(),
            create: jest.fn(),
            update: jest.fn(),
            delete: jest.fn(),
          },
        },
      ],
    }).compile();

    controller = module.get<{{Entity}}Controller>({{Entity}}Controller);
    service = module.get({{Entity}}Service);
  });

  describe('findAll', () => {
    it('should return paginated {{entities}}', async () => {
      const result = {
        items: [mock{{Entity}}],
        total: 1,
        page: 1,
        limit: 10,
      };
      service.findAll.mockResolvedValue(result);

      expect(await controller.findAll({ page: 1, limit: 10 })).toEqual(result);
    });
  });

  describe('findOne', () => {
    it('should return {{entity}} by id', async () => {
      service.findById.mockResolvedValue(mock{{Entity}} as any);

      expect(await controller.findOne('{{uuid}}')).toEqual(mock{{Entity}});
      expect(service.findById).toHaveBeenCalledWith('{{uuid}}');
    });
  });

  describe('create', () => {
    it('should create and return {{entity}}', async () => {
      const createDto: Create{{Entity}}Dto = {
        {{field}}: '{{value}}',
      };
      service.create.mockResolvedValue(mock{{Entity}} as any);

      expect(await controller.create(createDto)).toEqual(mock{{Entity}});
      expect(service.create).toHaveBeenCalledWith(createDto);
    });
  });

  describe('update', () => {
    it('should update and return {{entity}}', async () => {
      const updateDto: Update{{Entity}}Dto = {
        {{field}}: 'updated',
      };
      service.update.mockResolvedValue({ ...mock{{Entity}}, ...updateDto } as any);

      const result = await controller.update('{{uuid}}', updateDto);

      expect(result.{{field}}).toBe('updated');
      expect(service.update).toHaveBeenCalledWith('{{uuid}}', updateDto);
    });
  });

  describe('delete', () => {
    it('should delete {{entity}}', async () => {
      service.delete.mockResolvedValue(undefined);

      await controller.delete('{{uuid}}');

      expect(service.delete).toHaveBeenCalledWith('{{uuid}}');
    });
  });
});
```

## Guard Test

```typescript
// common/guards/__tests__/{{guard}}.guard.spec.ts
import { ExecutionContext } from '@nestjs/common';
import { Reflector } from '@nestjs/core';
import { {{Guard}}Guard } from '../{{guard}}.guard';

describe('{{Guard}}Guard', () => {
  let guard: {{Guard}}Guard;
  let reflector: jest.Mocked<Reflector>;

  beforeEach(() => {
    reflector = {
      getAllAndOverride: jest.fn(),
    } as any;

    guard = new {{Guard}}Guard(reflector);
  });

  const createMockContext = (user: any = {}): ExecutionContext =>
    ({
      switchToHttp: () => ({
        getRequest: () => ({ user }),
      }),
      getHandler: () => ({}),
      getClass: () => ({}),
    } as ExecutionContext);

  it('should allow when no restrictions', () => {
    reflector.getAllAndOverride.mockReturnValue(null);

    const context = createMockContext({});
    expect(guard.canActivate(context)).toBe(true);
  });

  it('should allow authorized user', () => {
    reflector.getAllAndOverride.mockReturnValue(['{{permission}}']);

    const context = createMockContext({
      permissions: ['{{permission}}'],
    });
    expect(guard.canActivate(context)).toBe(true);
  });

  it('should deny unauthorized user', () => {
    reflector.getAllAndOverride.mockReturnValue(['{{permission}}']);

    const context = createMockContext({
      permissions: [],
    });
    expect(guard.canActivate(context)).toBe(false);
  });
});
```

## Pipe Test

```typescript
// common/pipes/__tests__/{{pipe}}.pipe.spec.ts
import { BadRequestException } from '@nestjs/common';
import { {{Pipe}}Pipe } from '../{{pipe}}.pipe';

describe('{{Pipe}}Pipe', () => {
  let pipe: {{Pipe}}Pipe;

  beforeEach(() => {
    pipe = new {{Pipe}}Pipe();
  });

  it('should transform valid input', () => {
    const result = pipe.transform('{{validInput}}', { type: 'param' });
    expect(result).toBe('{{expectedOutput}}');
  });

  it('should throw BadRequestException for invalid input', () => {
    expect(() =>
      pipe.transform('{{invalidInput}}', { type: 'param' }),
    ).toThrow(BadRequestException);
  });

  it('should handle empty value', () => {
    expect(() => pipe.transform('', { type: 'param' })).toThrow(
      BadRequestException,
    );
  });
});
```

## Interceptor Test

```typescript
// common/interceptors/__tests__/{{interceptor}}.interceptor.spec.ts
import { ExecutionContext, CallHandler } from '@nestjs/common';
import { of } from 'rxjs';
import { {{Interceptor}}Interceptor } from '../{{interceptor}}.interceptor';

describe('{{Interceptor}}Interceptor', () => {
  let interceptor: {{Interceptor}}Interceptor;

  beforeEach(() => {
    interceptor = new {{Interceptor}}Interceptor();
  });

  const createMockContext = (): ExecutionContext =>
    ({
      switchToHttp: () => ({
        getRequest: () => ({
          url: '/test',
          method: 'GET',
        }),
        getResponse: () => ({
          statusCode: 200,
        }),
      }),
    } as ExecutionContext);

  const createMockHandler = (data: any): CallHandler => ({
    handle: () => of(data),
  });

  it('should transform response', (done) => {
    const context = createMockContext();
    const handler = createMockHandler({ id: '1', name: 'Test' });

    interceptor.intercept(context, handler).subscribe((result) => {
      expect(result).toHaveProperty('success', true);
      expect(result).toHaveProperty('data');
      expect(result).toHaveProperty('timestamp');
      done();
    });
  });
});
```

## E2E Test

```typescript
// test/{{module}}.e2e-spec.ts
import { Test, TestingModule } from '@nestjs/testing';
import { INestApplication, ValidationPipe } from '@nestjs/common';
import * as request from 'supertest';
import { AppModule } from '../src/app.module';

describe('{{Entity}}Controller (e2e)', () => {
  let app: INestApplication;
  let authToken: string;
  let created{{Entity}}Id: string;

  beforeAll(async () => {
    const moduleFixture: TestingModule = await Test.createTestingModule({
      imports: [AppModule],
    }).compile();

    app = moduleFixture.createNestApplication();
    app.useGlobalPipes(
      new ValidationPipe({
        whitelist: true,
        forbidNonWhitelisted: true,
        transform: true,
      }),
    );

    await app.init();

    // Get auth token
    const loginResponse = await request(app.getHttpServer())
      .post('/auth/login')
      .send({ email: 'test@example.com', password: 'password' });
    authToken = loginResponse.body.accessToken;
  });

  afterAll(async () => {
    await app.close();
  });

  describe('POST /{{module}}', () => {
    it('should create {{entity}}', async () => {
      const response = await request(app.getHttpServer())
        .post('/{{module}}')
        .set('Authorization', `Bearer ${authToken}`)
        .send({
          {{field}}: '{{value}}',
        })
        .expect(201);

      expect(response.body.id).toBeDefined();
      expect(response.body.{{field}}).toBe('{{value}}');
      created{{Entity}}Id = response.body.id;
    });

    it('should return 400 for invalid data', async () => {
      await request(app.getHttpServer())
        .post('/{{module}}')
        .set('Authorization', `Bearer ${authToken}`)
        .send({})
        .expect(400);
    });
  });

  describe('GET /{{module}}', () => {
    it('should return paginated {{entities}}', async () => {
      const response = await request(app.getHttpServer())
        .get('/{{module}}')
        .set('Authorization', `Bearer ${authToken}`)
        .query({ page: 1, limit: 10 })
        .expect(200);

      expect(response.body.items).toBeInstanceOf(Array);
      expect(response.body.total).toBeGreaterThanOrEqual(1);
    });
  });

  describe('GET /{{module}}/:id', () => {
    it('should return {{entity}} by id', async () => {
      const response = await request(app.getHttpServer())
        .get(`/{{module}}/${created{{Entity}}Id}`)
        .set('Authorization', `Bearer ${authToken}`)
        .expect(200);

      expect(response.body.id).toBe(created{{Entity}}Id);
    });

    it('should return 404 for non-existent id', async () => {
      await request(app.getHttpServer())
        .get('/{{module}}/00000000-0000-0000-0000-000000000000')
        .set('Authorization', `Bearer ${authToken}`)
        .expect(404);
    });
  });

  describe('PATCH /{{module}}/:id', () => {
    it('should update {{entity}}', async () => {
      const response = await request(app.getHttpServer())
        .patch(`/{{module}}/${created{{Entity}}Id}`)
        .set('Authorization', `Bearer ${authToken}`)
        .send({ {{field}}: 'updated' })
        .expect(200);

      expect(response.body.{{field}}).toBe('updated');
    });
  });

  describe('DELETE /{{module}}/:id', () => {
    it('should delete {{entity}}', async () => {
      await request(app.getHttpServer())
        .delete(`/{{module}}/${created{{Entity}}Id}`)
        .set('Authorization', `Bearer ${authToken}`)
        .expect(200);

      // Verify deletion
      await request(app.getHttpServer())
        .get(`/{{module}}/${created{{Entity}}Id}`)
        .set('Authorization', `Bearer ${authToken}`)
        .expect(404);
    });
  });
});
```

## Test Utilities

```typescript
// test/utils/test.utils.ts
import { INestApplication } from '@nestjs/common';
import * as request from 'supertest';

export const createMock{{Entity}} = (overrides = {}) => ({
  id: '{{uuid}}',
  {{field}}: '{{value}}',
  createdAt: new Date(),
  updatedAt: new Date(),
  ...overrides,
});

export const createMockRepository = () => ({
  find: jest.fn(),
  findOne: jest.fn(),
  findAndCount: jest.fn(),
  create: jest.fn(),
  save: jest.fn(),
  update: jest.fn(),
  delete: jest.fn(),
  softDelete: jest.fn(),
});

export const authenticatedRequest = (
  app: INestApplication,
  token: string,
) => ({
  get: (url: string) =>
    request(app.getHttpServer())
      .get(url)
      .set('Authorization', `Bearer ${token}`),
  post: (url: string) =>
    request(app.getHttpServer())
      .post(url)
      .set('Authorization', `Bearer ${token}`),
  patch: (url: string) =>
    request(app.getHttpServer())
      .patch(url)
      .set('Authorization', `Bearer ${token}`),
  delete: (url: string) =>
    request(app.getHttpServer())
      .delete(url)
      .set('Authorization', `Bearer ${token}`),
});
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{module}}` | Module name (lowercase) | users |
| `{{entity}}` | Entity name (lowercase) | user |
| `{{entities}}` | Entity name (plural) | users |
| `{{Entity}}` | Entity name (PascalCase) | User |
| `{{field}}` | Field name | name |
| `{{value}}` | Field value | John Doe |
| `{{uuid}}` | UUID example | 123e4567-e89b-12d3-a456-426614174000 |
| `{{guard}}` | Guard name (lowercase) | roles |
| `{{Guard}}` | Guard name (PascalCase) | Roles |
| `{{pipe}}` | Pipe name (lowercase) | parse-uuid |
| `{{Pipe}}` | Pipe name (PascalCase) | ParseUUID |
| `{{interceptor}}` | Interceptor name | transform |
| `{{Interceptor}}` | Interceptor name (PascalCase) | Transform |
| `{{permission}}` | Permission name | users:read |
