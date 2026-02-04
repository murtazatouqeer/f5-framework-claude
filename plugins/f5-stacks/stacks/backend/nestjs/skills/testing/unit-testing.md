---
name: nestjs-unit-testing
description: Unit testing patterns in NestJS
applies_to: nestjs
category: testing
---

# NestJS Unit Testing

## Setup

Jest is configured by default in NestJS projects.

```json
// package.json
{
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch",
    "test:cov": "jest --coverage",
    "test:debug": "node --inspect-brk -r tsconfig-paths/register -r ts-node/register node_modules/.bin/jest --runInBand"
  }
}
```

## Testing Services

```typescript
// modules/users/__tests__/users.service.spec.ts
import { Test, TestingModule } from '@nestjs/testing';
import { getRepositoryToken } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { UsersService } from '../users.service';
import { User } from '../entities/user.entity';
import { NotFoundException } from '@nestjs/common';

describe('UsersService', () => {
  let service: UsersService;
  let repository: jest.Mocked<Repository<User>>;

  const mockUser: User = {
    id: 'user-1',
    email: 'test@example.com',
    name: 'Test User',
    isActive: true,
    createdAt: new Date(),
    updatedAt: new Date(),
  } as User;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        UsersService,
        {
          provide: getRepositoryToken(User),
          useValue: {
            findOne: jest.fn(),
            find: jest.fn(),
            findAndCount: jest.fn(),
            create: jest.fn(),
            save: jest.fn(),
            update: jest.fn(),
            softDelete: jest.fn(),
          },
        },
      ],
    }).compile();

    service = module.get<UsersService>(UsersService);
    repository = module.get(getRepositoryToken(User));
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('findById', () => {
    it('should return user when found', async () => {
      repository.findOne.mockResolvedValue(mockUser);

      const result = await service.findById('user-1');

      expect(result).toEqual(mockUser);
      expect(repository.findOne).toHaveBeenCalledWith({
        where: { id: 'user-1' },
      });
    });

    it('should throw NotFoundException when user not found', async () => {
      repository.findOne.mockResolvedValue(null);

      await expect(service.findById('nonexistent')).rejects.toThrow(
        NotFoundException,
      );
    });
  });

  describe('create', () => {
    const createDto = {
      email: 'new@example.com',
      name: 'New User',
      password: 'password123',
    };

    it('should create user successfully', async () => {
      repository.findOne.mockResolvedValue(null); // No existing user
      repository.create.mockReturnValue(mockUser);
      repository.save.mockResolvedValue(mockUser);

      const result = await service.create(createDto);

      expect(result).toEqual(mockUser);
      expect(repository.create).toHaveBeenCalled();
      expect(repository.save).toHaveBeenCalled();
    });

    it('should throw error when email exists', async () => {
      repository.findOne.mockResolvedValue(mockUser);

      await expect(service.create(createDto)).rejects.toThrow();
    });
  });

  describe('update', () => {
    const updateDto = { name: 'Updated Name' };

    it('should update user successfully', async () => {
      repository.findOne.mockResolvedValue(mockUser);
      repository.save.mockResolvedValue({ ...mockUser, ...updateDto });

      const result = await service.update('user-1', updateDto);

      expect(result.name).toBe('Updated Name');
    });

    it('should throw NotFoundException for nonexistent user', async () => {
      repository.findOne.mockResolvedValue(null);

      await expect(service.update('nonexistent', updateDto)).rejects.toThrow(
        NotFoundException,
      );
    });
  });
});
```

## Testing Controllers

```typescript
// modules/users/__tests__/users.controller.spec.ts
import { Test, TestingModule } from '@nestjs/testing';
import { UsersController } from '../users.controller';
import { UsersService } from '../users.service';
import { CreateUserDto } from '../dto/create-user.dto';

describe('UsersController', () => {
  let controller: UsersController;
  let service: jest.Mocked<UsersService>;

  const mockUser = {
    id: 'user-1',
    email: 'test@example.com',
    name: 'Test User',
  };

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      controllers: [UsersController],
      providers: [
        {
          provide: UsersService,
          useValue: {
            findAll: jest.fn(),
            findById: jest.fn(),
            create: jest.fn(),
            update: jest.fn(),
            remove: jest.fn(),
          },
        },
      ],
    }).compile();

    controller = module.get<UsersController>(UsersController);
    service = module.get(UsersService);
  });

  describe('findAll', () => {
    it('should return paginated users', async () => {
      const result = {
        items: [mockUser],
        total: 1,
        page: 1,
        limit: 10,
      };
      service.findAll.mockResolvedValue(result);

      expect(await controller.findAll({ page: 1, limit: 10 })).toEqual(result);
    });
  });

  describe('findOne', () => {
    it('should return user by id', async () => {
      service.findById.mockResolvedValue(mockUser as any);

      expect(await controller.findOne('user-1')).toEqual(mockUser);
      expect(service.findById).toHaveBeenCalledWith('user-1');
    });
  });

  describe('create', () => {
    const createDto: CreateUserDto = {
      email: 'new@example.com',
      name: 'New User',
      password: 'password123',
    };

    it('should create and return user', async () => {
      service.create.mockResolvedValue(mockUser as any);

      expect(await controller.create(createDto)).toEqual(mockUser);
      expect(service.create).toHaveBeenCalledWith(createDto);
    });
  });
});
```

## Testing Guards

```typescript
// common/guards/__tests__/roles.guard.spec.ts
import { ExecutionContext } from '@nestjs/common';
import { Reflector } from '@nestjs/core';
import { RolesGuard } from '../roles.guard';
import { Role } from '../../enums/role.enum';

describe('RolesGuard', () => {
  let guard: RolesGuard;
  let reflector: jest.Mocked<Reflector>;

  beforeEach(() => {
    reflector = {
      getAllAndOverride: jest.fn(),
    } as any;

    guard = new RolesGuard(reflector);
  });

  const createMockContext = (user: any = {}): ExecutionContext =>
    ({
      switchToHttp: () => ({
        getRequest: () => ({ user }),
      }),
      getHandler: () => ({}),
      getClass: () => ({}),
    } as ExecutionContext);

  it('should allow when no roles required', () => {
    reflector.getAllAndOverride.mockReturnValue(null);

    const context = createMockContext({ roles: [Role.USER] });
    expect(guard.canActivate(context)).toBe(true);
  });

  it('should allow user with required role', () => {
    reflector.getAllAndOverride.mockReturnValue([Role.ADMIN]);

    const context = createMockContext({ roles: [Role.ADMIN] });
    expect(guard.canActivate(context)).toBe(true);
  });

  it('should deny user without required role', () => {
    reflector.getAllAndOverride.mockReturnValue([Role.ADMIN]);

    const context = createMockContext({ roles: [Role.USER] });
    expect(guard.canActivate(context)).toBe(false);
  });

  it('should deny when no user', () => {
    reflector.getAllAndOverride.mockReturnValue([Role.ADMIN]);

    const context = createMockContext(null);
    expect(guard.canActivate(context)).toBe(false);
  });
});
```

## Testing Pipes

```typescript
// common/pipes/__tests__/parse-uuid.pipe.spec.ts
import { BadRequestException } from '@nestjs/common';
import { ParseUUIDPipe } from '../parse-uuid.pipe';

describe('ParseUUIDPipe', () => {
  let pipe: ParseUUIDPipe;

  beforeEach(() => {
    pipe = new ParseUUIDPipe();
  });

  it('should pass valid UUID', () => {
    const validUUID = '123e4567-e89b-12d3-a456-426614174000';
    expect(pipe.transform(validUUID, { type: 'param' })).toBe(validUUID);
  });

  it('should throw for invalid UUID', () => {
    expect(() => pipe.transform('invalid', { type: 'param' })).toThrow(
      BadRequestException,
    );
  });

  it('should throw for empty value', () => {
    expect(() => pipe.transform('', { type: 'param' })).toThrow(
      BadRequestException,
    );
  });
});
```

## Test Utilities

```typescript
// test/utils/test.utils.ts
import { Test, TestingModule } from '@nestjs/testing';

export const createMockRepository = () => ({
  find: jest.fn(),
  findOne: jest.fn(),
  findAndCount: jest.fn(),
  create: jest.fn(),
  save: jest.fn(),
  update: jest.fn(),
  delete: jest.fn(),
  softDelete: jest.fn(),
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

export const createMockUser = (overrides = {}) => ({
  id: 'user-1',
  email: 'test@example.com',
  name: 'Test User',
  isActive: true,
  roles: ['user'],
  createdAt: new Date(),
  updatedAt: new Date(),
  ...overrides,
});

export const createMockRequest = (overrides = {}) => ({
  user: createMockUser(),
  params: {},
  query: {},
  body: {},
  headers: {},
  ...overrides,
});
```

## Coverage Configuration

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
    '**/*.(t|j)s',
    '!**/*.module.ts',
    '!**/index.ts',
    '!main.ts',
  ],
  coverageDirectory: '../coverage',
  testEnvironment: 'node',
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
};
```

## Best Practices

1. **Isolate units**: Mock all dependencies
2. **Test behavior**: Not implementation details
3. **Descriptive names**: Clear test descriptions
4. **Arrange-Act-Assert**: Consistent test structure
5. **Cover edge cases**: Errors, null values, boundaries
6. **Keep tests fast**: Unit tests should be quick

## Checklist

- [ ] Service methods tested
- [ ] Controller endpoints tested
- [ ] Guards tested
- [ ] Pipes tested
- [ ] Custom validators tested
- [ ] Edge cases covered
- [ ] Coverage thresholds met
