---
name: nestjs-test-generator
description: Agent for generating NestJS test files
applies_to: nestjs
category: agent
---

# NestJS Test Generator Agent

## Purpose

Generate comprehensive test files for NestJS services, controllers, guards, pipes, and interceptors.

## Input Requirements

```yaml
required:
  - target_type: string        # service, controller, guard, pipe, interceptor
  - entity_name: string        # e.g., "user"
  - module_name: string        # e.g., "users"

optional:
  - coverage_level: string     # basic, standard, comprehensive (default: standard)
  - e2e: boolean               # Generate E2E tests (default: false)
  - mock_external: boolean     # Mock external services (default: true)
  - include_edge_cases: boolean # Add edge case tests (default: true)
```

## Generation Process

### Step 1: Analyze Target

```typescript
// Analyze the target file
const targetFile = await readFile(`${moduleName}/${targetType}.ts`);
const methods = extractPublicMethods(targetFile);
const dependencies = extractDependencies(targetFile);
const returnTypes = extractReturnTypes(targetFile);
```

### Step 2: Generate Service Test

```typescript
// modules/{{module}}/__tests__/{{entity}}.service.spec.ts
import { Test, TestingModule } from '@nestjs/testing';
import { getRepositoryToken } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { NotFoundException, ConflictException, BadRequestException } from '@nestjs/common';
import { {{Entity}}Service } from '../{{entity}}.service';
import { {{Entity}} } from '../entities/{{entity}}.entity';
import { Create{{Entity}}Dto } from '../dto/create-{{entity}}.dto';
import { Update{{Entity}}Dto } from '../dto/update-{{entity}}.dto';
import { Query{{Entity}}Dto } from '../dto/query-{{entity}}.dto';

describe('{{Entity}}Service', () => {
  let service: {{Entity}}Service;
  let repository: jest.Mocked<Repository<{{Entity}}>>;

  // Test fixtures
  const mock{{Entity}}: {{Entity}} = {
    id: 'test-uuid-1234',
    {{#each fields}}
    {{name}}: {{mockValue}},
    {{/each}}
    createdAt: new Date('2024-01-01'),
    updatedAt: new Date('2024-01-01'),
  };

  const mock{{Entity}}List: {{Entity}}[] = [
    mock{{Entity}},
    { ...mock{{Entity}}, id: 'test-uuid-5678' },
  ];

  // Mock repository factory
  const createMockRepository = () => ({
    findOne: jest.fn(),
    find: jest.fn(),
    findAndCount: jest.fn(),
    create: jest.fn(),
    save: jest.fn(),
    update: jest.fn(),
    delete: jest.fn(),
    softDelete: jest.fn(),
    count: jest.fn(),
    createQueryBuilder: jest.fn(() => ({
      where: jest.fn().mockReturnThis(),
      andWhere: jest.fn().mockReturnThis(),
      leftJoinAndSelect: jest.fn().mockReturnThis(),
      orderBy: jest.fn().mockReturnThis(),
      skip: jest.fn().mockReturnThis(),
      take: jest.fn().mockReturnThis(),
      getMany: jest.fn(),
      getManyAndCount: jest.fn(),
      getOne: jest.fn(),
    })),
  });

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        {{Entity}}Service,
        {
          provide: getRepositoryToken({{Entity}}),
          useValue: createMockRepository(),
        },
      ],
    }).compile();

    service = module.get<{{Entity}}Service>({{Entity}}Service);
    repository = module.get(getRepositoryToken({{Entity}}));
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('create', () => {
    const createDto: Create{{Entity}}Dto = {
      {{#each createFields}}
      {{name}}: {{value}},
      {{/each}}
    };

    it('should create {{entity}} successfully', async () => {
      repository.findOne.mockResolvedValue(null); // No existing
      repository.create.mockReturnValue(mock{{Entity}});
      repository.save.mockResolvedValue(mock{{Entity}});

      const result = await service.create(createDto);

      expect(result).toEqual(mock{{Entity}});
      expect(repository.create).toHaveBeenCalledWith(createDto);
      expect(repository.save).toHaveBeenCalled();
    });

    it('should throw ConflictException when {{entity}} already exists', async () => {
      repository.findOne.mockResolvedValue(mock{{Entity}});

      await expect(service.create(createDto)).rejects.toThrow(ConflictException);
    });

    it('should handle database errors', async () => {
      repository.findOne.mockResolvedValue(null);
      repository.save.mockRejectedValue(new Error('Database error'));

      await expect(service.create(createDto)).rejects.toThrow('Database error');
    });
  });

  describe('findAll', () => {
    const queryDto: Query{{Entity}}Dto = {
      page: 1,
      limit: 10,
    };

    it('should return paginated {{entities}}', async () => {
      repository.findAndCount.mockResolvedValue([mock{{Entity}}List, 2]);

      const result = await service.findAll(queryDto);

      expect(result.items).toEqual(mock{{Entity}}List);
      expect(result.total).toBe(2);
      expect(result.page).toBe(1);
      expect(result.limit).toBe(10);
    });

    it('should apply search filter', async () => {
      const searchQuery = { ...queryDto, search: 'test' };
      repository.findAndCount.mockResolvedValue([mock{{Entity}}List, 2]);

      await service.findAll(searchQuery);

      expect(repository.findAndCount).toHaveBeenCalled();
    });

    it('should return empty list when no results', async () => {
      repository.findAndCount.mockResolvedValue([[], 0]);

      const result = await service.findAll(queryDto);

      expect(result.items).toEqual([]);
      expect(result.total).toBe(0);
    });
  });

  describe('findById', () => {
    it('should return {{entity}} when found', async () => {
      repository.findOne.mockResolvedValue(mock{{Entity}});

      const result = await service.findById('test-uuid-1234');

      expect(result).toEqual(mock{{Entity}});
      expect(repository.findOne).toHaveBeenCalledWith({
        where: { id: 'test-uuid-1234' },
      });
    });

    it('should throw NotFoundException when {{entity}} not found', async () => {
      repository.findOne.mockResolvedValue(null);

      await expect(service.findById('nonexistent')).rejects.toThrow(
        NotFoundException,
      );
    });

    it('should handle invalid UUID format', async () => {
      await expect(service.findById('invalid-uuid')).rejects.toThrow();
    });
  });

  describe('update', () => {
    const updateDto: Update{{Entity}}Dto = {
      {{#each updateFields}}
      {{name}}: {{value}},
      {{/each}}
    };

    it('should update {{entity}} successfully', async () => {
      repository.findOne.mockResolvedValue(mock{{Entity}});
      repository.save.mockResolvedValue({ ...mock{{Entity}}, ...updateDto });

      const result = await service.update('test-uuid-1234', updateDto);

      expect(result).toMatchObject(updateDto);
    });

    it('should throw NotFoundException when {{entity}} not found', async () => {
      repository.findOne.mockResolvedValue(null);

      await expect(service.update('nonexistent', updateDto)).rejects.toThrow(
        NotFoundException,
      );
    });

    it('should handle partial updates', async () => {
      const partialUpdate = { {{partialField}}: {{partialValue}} };
      repository.findOne.mockResolvedValue(mock{{Entity}});
      repository.save.mockResolvedValue({ ...mock{{Entity}}, ...partialUpdate });

      const result = await service.update('test-uuid-1234', partialUpdate);

      expect(result.{{partialField}}).toBe({{partialValue}});
    });
  });

  describe('delete', () => {
    it('should delete {{entity}} successfully', async () => {
      repository.findOne.mockResolvedValue(mock{{Entity}});
      repository.softDelete.mockResolvedValue({ affected: 1 });

      await service.delete('test-uuid-1234');

      expect(repository.softDelete).toHaveBeenCalledWith('test-uuid-1234');
    });

    it('should throw NotFoundException when {{entity}} not found', async () => {
      repository.findOne.mockResolvedValue(null);

      await expect(service.delete('nonexistent')).rejects.toThrow(
        NotFoundException,
      );
    });
  });

  // Edge cases
  describe('edge cases', () => {
    it('should handle concurrent updates', async () => {
      repository.findOne.mockResolvedValue(mock{{Entity}});
      repository.save.mockRejectedValueOnce(new Error('Optimistic lock'));

      await expect(
        service.update('test-uuid-1234', { {{field}}: {{value}} }),
      ).rejects.toThrow();
    });

    it('should handle empty update payload', async () => {
      repository.findOne.mockResolvedValue(mock{{Entity}});
      repository.save.mockResolvedValue(mock{{Entity}});

      const result = await service.update('test-uuid-1234', {});

      expect(result).toEqual(mock{{Entity}});
    });

    it('should handle special characters in search', async () => {
      const specialQuery = { page: 1, limit: 10, search: "test'--" };
      repository.findAndCount.mockResolvedValue([[], 0]);

      // Should not throw SQL injection error
      await expect(service.findAll(specialQuery)).resolves.toBeDefined();
    });
  });
});
```

### Step 3: Generate Controller Test

```typescript
// modules/{{module}}/__tests__/{{entity}}.controller.spec.ts
import { Test, TestingModule } from '@nestjs/testing';
import { {{Entity}}Controller } from '../{{entity}}.controller';
import { {{Entity}}Service } from '../{{entity}}.service';
import { Create{{Entity}}Dto } from '../dto/create-{{entity}}.dto';
import { Update{{Entity}}Dto } from '../dto/update-{{entity}}.dto';
import { Query{{Entity}}Dto } from '../dto/query-{{entity}}.dto';
import { NotFoundException } from '@nestjs/common';

describe('{{Entity}}Controller', () => {
  let controller: {{Entity}}Controller;
  let service: jest.Mocked<{{Entity}}Service>;

  const mock{{Entity}} = {
    id: 'test-uuid-1234',
    {{#each fields}}
    {{name}}: {{mockValue}},
    {{/each}}
    createdAt: new Date(),
    updatedAt: new Date(),
  };

  const mockUser = {
    id: 'user-uuid-1234',
    email: 'test@example.com',
    roles: ['admin'],
  };

  const createMockService = () => ({
    create: jest.fn(),
    findAll: jest.fn(),
    findById: jest.fn(),
    update: jest.fn(),
    delete: jest.fn(),
  });

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      controllers: [{{Entity}}Controller],
      providers: [
        {
          provide: {{Entity}}Service,
          useValue: createMockService(),
        },
      ],
    }).compile();

    controller = module.get<{{Entity}}Controller>({{Entity}}Controller);
    service = module.get({{Entity}}Service);
  });

  describe('create', () => {
    const createDto: Create{{Entity}}Dto = {
      {{#each createFields}}
      {{name}}: {{value}},
      {{/each}}
    };

    it('should create {{entity}}', async () => {
      service.create.mockResolvedValue(mock{{Entity}} as any);

      const result = await controller.create(createDto, mockUser);

      expect(result).toEqual(mock{{Entity}});
      expect(service.create).toHaveBeenCalledWith(createDto, mockUser.id);
    });
  });

  describe('findAll', () => {
    const queryDto: Query{{Entity}}Dto = { page: 1, limit: 10 };

    it('should return paginated {{entities}}', async () => {
      const paginatedResult = {
        items: [mock{{Entity}}],
        total: 1,
        page: 1,
        limit: 10,
      };
      service.findAll.mockResolvedValue(paginatedResult);

      const result = await controller.findAll(queryDto);

      expect(result).toEqual(paginatedResult);
    });
  });

  describe('findOne', () => {
    it('should return {{entity}} by id', async () => {
      service.findById.mockResolvedValue(mock{{Entity}} as any);

      const result = await controller.findOne('test-uuid-1234');

      expect(result).toEqual(mock{{Entity}});
    });

    it('should propagate NotFoundException', async () => {
      service.findById.mockRejectedValue(
        new NotFoundException('{{Entity}} not found'),
      );

      await expect(controller.findOne('nonexistent')).rejects.toThrow(
        NotFoundException,
      );
    });
  });

  describe('update', () => {
    const updateDto: Update{{Entity}}Dto = {
      {{#each updateFields}}
      {{name}}: {{value}},
      {{/each}}
    };

    it('should update {{entity}}', async () => {
      service.update.mockResolvedValue({ ...mock{{Entity}}, ...updateDto } as any);

      const result = await controller.update('test-uuid-1234', updateDto);

      expect(service.update).toHaveBeenCalledWith('test-uuid-1234', updateDto);
    });
  });

  describe('remove', () => {
    it('should delete {{entity}}', async () => {
      service.delete.mockResolvedValue(undefined);

      await controller.remove('test-uuid-1234');

      expect(service.delete).toHaveBeenCalledWith('test-uuid-1234');
    });
  });
});
```

### Step 4: Generate E2E Test (if requested)

```typescript
// test/{{module}}.e2e-spec.ts
import { Test, TestingModule } from '@nestjs/testing';
import { INestApplication, ValidationPipe } from '@nestjs/common';
import * as request from 'supertest';
import { AppModule } from '../src/app.module';
import { DataSource } from 'typeorm';

describe('{{Entity}}Controller (e2e)', () => {
  let app: INestApplication;
  let dataSource: DataSource;
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

    dataSource = moduleFixture.get(DataSource);
    await app.init();

    // Get auth token
    const loginResponse = await request(app.getHttpServer())
      .post('/auth/login')
      .send({ email: 'admin@test.com', password: 'password123' });
    authToken = loginResponse.body.accessToken;
  });

  afterAll(async () => {
    await dataSource.query('TRUNCATE TABLE {{tableName}} CASCADE');
    await app.close();
  });

  describe('POST /{{module}}', () => {
    const validPayload = {
      {{#each createFields}}
      {{name}}: {{value}},
      {{/each}}
    };

    it('should create {{entity}} with valid data', () => {
      return request(app.getHttpServer())
        .post('/{{module}}')
        .set('Authorization', `Bearer ${authToken}`)
        .send(validPayload)
        .expect(201)
        .expect((res) => {
          expect(res.body.id).toBeDefined();
          created{{Entity}}Id = res.body.id;
        });
    });

    it('should return 400 for invalid data', () => {
      return request(app.getHttpServer())
        .post('/{{module}}')
        .set('Authorization', `Bearer ${authToken}`)
        .send({})
        .expect(400);
    });

    it('should return 401 without auth', () => {
      return request(app.getHttpServer())
        .post('/{{module}}')
        .send(validPayload)
        .expect(401);
    });
  });

  describe('GET /{{module}}', () => {
    it('should return paginated list', () => {
      return request(app.getHttpServer())
        .get('/{{module}}')
        .set('Authorization', `Bearer ${authToken}`)
        .query({ page: 1, limit: 10 })
        .expect(200)
        .expect((res) => {
          expect(res.body.items).toBeInstanceOf(Array);
          expect(res.body.total).toBeGreaterThanOrEqual(1);
        });
    });
  });

  describe('GET /{{module}}/:id', () => {
    it('should return {{entity}} by id', () => {
      return request(app.getHttpServer())
        .get(`/{{module}}/${created{{Entity}}Id}`)
        .set('Authorization', `Bearer ${authToken}`)
        .expect(200)
        .expect((res) => {
          expect(res.body.id).toBe(created{{Entity}}Id);
        });
    });

    it('should return 404 for non-existent id', () => {
      return request(app.getHttpServer())
        .get('/{{module}}/00000000-0000-0000-0000-000000000000')
        .set('Authorization', `Bearer ${authToken}`)
        .expect(404);
    });
  });

  describe('PATCH /{{module}}/:id', () => {
    it('should update {{entity}}', () => {
      return request(app.getHttpServer())
        .patch(`/{{module}}/${created{{Entity}}Id}`)
        .set('Authorization', `Bearer ${authToken}`)
        .send({ {{updateField}}: {{updateValue}} })
        .expect(200)
        .expect((res) => {
          expect(res.body.{{updateField}}).toBe({{updateValue}});
        });
    });
  });

  describe('DELETE /{{module}}/:id', () => {
    it('should delete {{entity}}', () => {
      return request(app.getHttpServer())
        .delete(`/{{module}}/${created{{Entity}}Id}`)
        .set('Authorization', `Bearer ${authToken}`)
        .expect(204);
    });

    it('should return 404 after deletion', () => {
      return request(app.getHttpServer())
        .get(`/{{module}}/${created{{Entity}}Id}`)
        .set('Authorization', `Bearer ${authToken}`)
        .expect(404);
    });
  });
});
```

## Output Files

```
modules/{{module}}/
├── __tests__/
│   ├── {{entity}}.service.spec.ts
│   └── {{entity}}.controller.spec.ts
test/
└── {{module}}.e2e-spec.ts (if e2e=true)
```

## Usage Example

```bash
# Generate tests via agent
@nestjs:test-generator {
  "target_type": "service",
  "entity_name": "product",
  "module_name": "products",
  "coverage_level": "comprehensive",
  "e2e": true,
  "include_edge_cases": true
}
```

## Validation Checklist

- [ ] All public methods have tests
- [ ] Happy path scenarios covered
- [ ] Error scenarios covered
- [ ] Edge cases handled
- [ ] Mocks properly configured
- [ ] Async operations awaited
- [ ] Cleanup in afterEach/afterAll
- [ ] E2E tests isolated
- [ ] Coverage requirements met
