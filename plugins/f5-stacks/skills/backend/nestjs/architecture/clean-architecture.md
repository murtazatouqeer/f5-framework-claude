---
name: nestjs-clean-architecture
description: Implementing Clean Architecture in NestJS
applies_to: nestjs
category: architecture
---

# Clean Architecture in NestJS

## Overview

Clean Architecture separates concerns into layers, with dependencies pointing inward.
The domain layer is at the center, independent of frameworks and infrastructure.

## When to Use

- Complex business logic
- Long-term maintainability is priority
- Team experienced with DDD concepts
- Need to swap infrastructure easily
- Enterprise applications

## Layer Structure

```
src/
├── domain/                    # Enterprise Business Rules
│   ├── entities/
│   ├── value-objects/
│   ├── repositories/         # Interfaces only
│   ├── services/             # Domain services
│   └── exceptions/
│
├── application/              # Application Business Rules
│   ├── use-cases/
│   ├── dto/
│   ├── ports/               # Interfaces for infra
│   ├── services/            # Application services
│   └── mappers/
│
├── infrastructure/          # Frameworks & Drivers
│   ├── database/
│   │   ├── typeorm/
│   │   └── repositories/    # Implementations
│   ├── external-services/
│   ├── config/
│   └── persistence/
│
└── presentation/            # Interface Adapters
    ├── http/
    │   ├── controllers/
    │   └── dto/
    ├── graphql/
    └── websocket/
```

## Implementation

### Domain Layer (Core)

The innermost layer - pure business logic with no external dependencies.

```typescript
// domain/entities/user.entity.ts
import { Email } from '../value-objects/email.vo';
import { UserId } from '../value-objects/user-id.vo';
import { DomainException } from '../exceptions/domain.exception';

export enum UserStatus {
  PENDING = 'pending',
  ACTIVE = 'active',
  SUSPENDED = 'suspended',
}

export interface CreateUserProps {
  email: string;
  name: string;
  password: string;
}

export interface ReconstitueUserProps {
  id: string;
  email: string;
  name: string;
  passwordHash: string;
  status: UserStatus;
  createdAt: Date;
}

export class User {
  private constructor(
    public readonly id: UserId,
    public readonly email: Email,
    private _name: string,
    private _passwordHash: string,
    private _status: UserStatus,
    public readonly createdAt: Date,
  ) {}

  // Factory method for creating new users
  static create(props: CreateUserProps): User {
    const id = UserId.generate();
    const email = Email.create(props.email);

    if (props.name.length < 2) {
      throw new DomainException('Name must be at least 2 characters');
    }

    // In real app, hash password
    const passwordHash = props.password; // Should be hashed

    return new User(
      id,
      email,
      props.name,
      passwordHash,
      UserStatus.PENDING,
      new Date(),
    );
  }

  // Factory method for reconstituting from persistence
  static reconstitute(props: ReconstitueUserProps): User {
    return new User(
      UserId.from(props.id),
      Email.create(props.email),
      props.name,
      props.passwordHash,
      props.status,
      props.createdAt,
    );
  }

  // Business logic methods
  activate(): void {
    if (this._status !== UserStatus.PENDING) {
      throw new DomainException('Only pending users can be activated');
    }
    this._status = UserStatus.ACTIVE;
  }

  suspend(): void {
    if (this._status === UserStatus.SUSPENDED) {
      throw new DomainException('User is already suspended');
    }
    this._status = UserStatus.SUSPENDED;
  }

  updateName(newName: string): void {
    if (newName.length < 2) {
      throw new DomainException('Name must be at least 2 characters');
    }
    this._name = newName;
  }

  verifyPassword(password: string): boolean {
    // In real app, compare hashed passwords
    return this._passwordHash === password;
  }

  // Getters
  get name(): string {
    return this._name;
  }

  get status(): UserStatus {
    return this._status;
  }

  get passwordHash(): string {
    return this._passwordHash;
  }

  isActive(): boolean {
    return this._status === UserStatus.ACTIVE;
  }
}

// domain/value-objects/email.vo.ts
import { DomainException } from '../exceptions/domain.exception';

export class Email {
  private constructor(public readonly value: string) {}

  static create(email: string): Email {
    if (!this.isValid(email)) {
      throw new DomainException('Invalid email format');
    }
    return new Email(email.toLowerCase().trim());
  }

  private static isValid(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  equals(other: Email): boolean {
    return this.value === other.value;
  }
}

// domain/value-objects/user-id.vo.ts
import { v4 as uuidv4, validate as uuidValidate } from 'uuid';
import { DomainException } from '../exceptions/domain.exception';

export class UserId {
  private constructor(public readonly value: string) {}

  static generate(): UserId {
    return new UserId(uuidv4());
  }

  static from(id: string): UserId {
    if (!uuidValidate(id)) {
      throw new DomainException('Invalid user ID format');
    }
    return new UserId(id);
  }

  equals(other: UserId): boolean {
    return this.value === other.value;
  }
}

// domain/repositories/user.repository.interface.ts
import { User } from '../entities/user.entity';
import { Email } from '../value-objects/email.vo';
import { UserId } from '../value-objects/user-id.vo';

export interface IUserRepository {
  findById(id: UserId): Promise<User | null>;
  findByEmail(email: Email): Promise<User | null>;
  save(user: User): Promise<void>;
  delete(id: UserId): Promise<void>;
  exists(email: Email): Promise<boolean>;
}

export const USER_REPOSITORY = Symbol('IUserRepository');

// domain/exceptions/domain.exception.ts
export class DomainException extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'DomainException';
  }
}
```

### Application Layer

Use cases that orchestrate domain logic.

```typescript
// application/use-cases/create-user/create-user.use-case.ts
import { Inject, Injectable } from '@nestjs/common';
import { User } from '../../../domain/entities/user.entity';
import { Email } from '../../../domain/value-objects/email.vo';
import {
  IUserRepository,
  USER_REPOSITORY,
} from '../../../domain/repositories/user.repository.interface';
import { CreateUserInput, CreateUserOutput } from './create-user.dto';
import { UserAlreadyExistsException } from '../../exceptions/user-already-exists.exception';

@Injectable()
export class CreateUserUseCase {
  constructor(
    @Inject(USER_REPOSITORY)
    private readonly userRepository: IUserRepository,
  ) {}

  async execute(input: CreateUserInput): Promise<CreateUserOutput> {
    // Check if user exists
    const email = Email.create(input.email);
    const exists = await this.userRepository.exists(email);

    if (exists) {
      throw new UserAlreadyExistsException(input.email);
    }

    // Create domain entity
    const user = User.create({
      email: input.email,
      name: input.name,
      password: input.password,
    });

    // Persist
    await this.userRepository.save(user);

    // Return output DTO
    return {
      id: user.id.value,
      email: user.email.value,
      name: user.name,
      status: user.status,
      createdAt: user.createdAt,
    };
  }
}

// application/use-cases/create-user/create-user.dto.ts
import { UserStatus } from '../../../domain/entities/user.entity';

export interface CreateUserInput {
  email: string;
  name: string;
  password: string;
}

export interface CreateUserOutput {
  id: string;
  email: string;
  name: string;
  status: UserStatus;
  createdAt: Date;
}

// application/use-cases/activate-user/activate-user.use-case.ts
import { Inject, Injectable } from '@nestjs/common';
import { UserId } from '../../../domain/value-objects/user-id.vo';
import {
  IUserRepository,
  USER_REPOSITORY,
} from '../../../domain/repositories/user.repository.interface';
import { UserNotFoundException } from '../../exceptions/user-not-found.exception';

@Injectable()
export class ActivateUserUseCase {
  constructor(
    @Inject(USER_REPOSITORY)
    private readonly userRepository: IUserRepository,
  ) {}

  async execute(userId: string): Promise<void> {
    const id = UserId.from(userId);
    const user = await this.userRepository.findById(id);

    if (!user) {
      throw new UserNotFoundException(userId);
    }

    // Domain logic
    user.activate();

    // Persist
    await this.userRepository.save(user);
  }
}

// application/exceptions/user-already-exists.exception.ts
export class UserAlreadyExistsException extends Error {
  constructor(email: string) {
    super(`User with email ${email} already exists`);
    this.name = 'UserAlreadyExistsException';
  }
}

// application/exceptions/user-not-found.exception.ts
export class UserNotFoundException extends Error {
  constructor(id: string) {
    super(`User with ID ${id} not found`);
    this.name = 'UserNotFoundException';
  }
}
```

### Infrastructure Layer

Implementation of interfaces and external integrations.

```typescript
// infrastructure/database/typeorm/entities/user.orm-entity.ts
import {
  Entity,
  PrimaryColumn,
  Column,
  CreateDateColumn,
  Index,
} from 'typeorm';
import { UserStatus } from '../../../../domain/entities/user.entity';

@Entity('users')
export class UserOrmEntity {
  @PrimaryColumn('uuid')
  id: string;

  @Column({ unique: true })
  @Index()
  email: string;

  @Column()
  name: string;

  @Column({ name: 'password_hash' })
  passwordHash: string;

  @Column({ type: 'enum', enum: UserStatus, default: UserStatus.PENDING })
  status: UserStatus;

  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;
}

// infrastructure/database/repositories/user.repository.impl.ts
import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { User } from '../../../domain/entities/user.entity';
import { Email } from '../../../domain/value-objects/email.vo';
import { UserId } from '../../../domain/value-objects/user-id.vo';
import { IUserRepository } from '../../../domain/repositories/user.repository.interface';
import { UserOrmEntity } from '../typeorm/entities/user.orm-entity';

@Injectable()
export class UserRepositoryImpl implements IUserRepository {
  constructor(
    @InjectRepository(UserOrmEntity)
    private readonly ormRepo: Repository<UserOrmEntity>,
  ) {}

  async findById(id: UserId): Promise<User | null> {
    const entity = await this.ormRepo.findOne({
      where: { id: id.value },
    });
    return entity ? this.toDomain(entity) : null;
  }

  async findByEmail(email: Email): Promise<User | null> {
    const entity = await this.ormRepo.findOne({
      where: { email: email.value },
    });
    return entity ? this.toDomain(entity) : null;
  }

  async save(user: User): Promise<void> {
    const entity = this.toOrmEntity(user);
    await this.ormRepo.save(entity);
  }

  async delete(id: UserId): Promise<void> {
    await this.ormRepo.delete(id.value);
  }

  async exists(email: Email): Promise<boolean> {
    const count = await this.ormRepo.count({
      where: { email: email.value },
    });
    return count > 0;
  }

  // Mappers
  private toDomain(entity: UserOrmEntity): User {
    return User.reconstitute({
      id: entity.id,
      email: entity.email,
      name: entity.name,
      passwordHash: entity.passwordHash,
      status: entity.status,
      createdAt: entity.createdAt,
    });
  }

  private toOrmEntity(user: User): UserOrmEntity {
    const entity = new UserOrmEntity();
    entity.id = user.id.value;
    entity.email = user.email.value;
    entity.name = user.name;
    entity.passwordHash = user.passwordHash;
    entity.status = user.status;
    entity.createdAt = user.createdAt;
    return entity;
  }
}
```

### Presentation Layer

Controllers and HTTP-specific DTOs.

```typescript
// presentation/http/controllers/users.controller.ts
import {
  Controller,
  Post,
  Get,
  Patch,
  Param,
  Body,
  HttpCode,
  HttpStatus,
} from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse } from '@nestjs/swagger';
import { CreateUserUseCase } from '../../../application/use-cases/create-user/create-user.use-case';
import { ActivateUserUseCase } from '../../../application/use-cases/activate-user/activate-user.use-case';
import { GetUserUseCase } from '../../../application/use-cases/get-user/get-user.use-case';
import { CreateUserRequestDto } from '../dto/create-user-request.dto';
import { UserResponseDto } from '../dto/user-response.dto';

@ApiTags('Users')
@Controller('users')
export class UsersController {
  constructor(
    private readonly createUserUseCase: CreateUserUseCase,
    private readonly activateUserUseCase: ActivateUserUseCase,
    private readonly getUserUseCase: GetUserUseCase,
  ) {}

  @Post()
  @ApiOperation({ summary: 'Create a new user' })
  @ApiResponse({ status: 201, type: UserResponseDto })
  async create(@Body() dto: CreateUserRequestDto): Promise<UserResponseDto> {
    const result = await this.createUserUseCase.execute({
      email: dto.email,
      name: dto.name,
      password: dto.password,
    });

    return new UserResponseDto(result);
  }

  @Get(':id')
  @ApiOperation({ summary: 'Get user by ID' })
  @ApiResponse({ status: 200, type: UserResponseDto })
  async findOne(@Param('id') id: string): Promise<UserResponseDto> {
    const result = await this.getUserUseCase.execute(id);
    return new UserResponseDto(result);
  }

  @Patch(':id/activate')
  @HttpCode(HttpStatus.NO_CONTENT)
  @ApiOperation({ summary: 'Activate a user' })
  async activate(@Param('id') id: string): Promise<void> {
    await this.activateUserUseCase.execute(id);
  }
}

// presentation/http/dto/create-user-request.dto.ts
import { ApiProperty } from '@nestjs/swagger';
import { IsEmail, IsString, MinLength } from 'class-validator';

export class CreateUserRequestDto {
  @ApiProperty({ example: 'user@example.com' })
  @IsEmail()
  email: string;

  @ApiProperty({ example: 'John Doe' })
  @IsString()
  @MinLength(2)
  name: string;

  @ApiProperty({ example: 'password123' })
  @IsString()
  @MinLength(8)
  password: string;
}

// presentation/http/dto/user-response.dto.ts
import { ApiProperty } from '@nestjs/swagger';
import { UserStatus } from '../../../domain/entities/user.entity';

export class UserResponseDto {
  @ApiProperty()
  id: string;

  @ApiProperty()
  email: string;

  @ApiProperty()
  name: string;

  @ApiProperty({ enum: UserStatus })
  status: UserStatus;

  @ApiProperty()
  createdAt: Date;

  constructor(data: {
    id: string;
    email: string;
    name: string;
    status: UserStatus;
    createdAt: Date;
  }) {
    this.id = data.id;
    this.email = data.email;
    this.name = data.name;
    this.status = data.status;
    this.createdAt = data.createdAt;
  }
}
```

### Module Wiring

```typescript
// users.module.ts
import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';

// Presentation
import { UsersController } from './presentation/http/controllers/users.controller';

// Application - Use Cases
import { CreateUserUseCase } from './application/use-cases/create-user/create-user.use-case';
import { ActivateUserUseCase } from './application/use-cases/activate-user/activate-user.use-case';
import { GetUserUseCase } from './application/use-cases/get-user/get-user.use-case';

// Infrastructure
import { UserOrmEntity } from './infrastructure/database/typeorm/entities/user.orm-entity';
import { UserRepositoryImpl } from './infrastructure/database/repositories/user.repository.impl';

// Domain
import { USER_REPOSITORY } from './domain/repositories/user.repository.interface';

@Module({
  imports: [TypeOrmModule.forFeature([UserOrmEntity])],
  controllers: [UsersController],
  providers: [
    // Use Cases
    CreateUserUseCase,
    ActivateUserUseCase,
    GetUserUseCase,

    // Repository binding
    {
      provide: USER_REPOSITORY,
      useClass: UserRepositoryImpl,
    },
  ],
  exports: [USER_REPOSITORY],
})
export class UsersModule {}
```

## Benefits

- **Testability**: Domain logic testable without infrastructure
- **Flexibility**: Swap databases, frameworks easily
- **Maintainability**: Clear boundaries, single responsibility
- **Scalability**: Can extract to microservices
- **Framework Independence**: Domain doesn't know about NestJS

## Testing in Clean Architecture

```typescript
// Unit test for domain entity
describe('User', () => {
  it('should create user with valid data', () => {
    const user = User.create({
      email: 'test@example.com',
      name: 'Test User',
      password: 'password123',
    });

    expect(user.email.value).toBe('test@example.com');
    expect(user.status).toBe(UserStatus.PENDING);
  });

  it('should activate pending user', () => {
    const user = User.create({
      email: 'test@example.com',
      name: 'Test User',
      password: 'password123',
    });

    user.activate();

    expect(user.status).toBe(UserStatus.ACTIVE);
  });
});

// Unit test for use case (mocking repository)
describe('CreateUserUseCase', () => {
  let useCase: CreateUserUseCase;
  let userRepository: jest.Mocked<IUserRepository>;

  beforeEach(() => {
    userRepository = {
      findById: jest.fn(),
      findByEmail: jest.fn(),
      save: jest.fn(),
      delete: jest.fn(),
      exists: jest.fn(),
    };

    useCase = new CreateUserUseCase(userRepository);
  });

  it('should create user when email is unique', async () => {
    userRepository.exists.mockResolvedValue(false);
    userRepository.save.mockResolvedValue();

    const result = await useCase.execute({
      email: 'new@example.com',
      name: 'New User',
      password: 'password123',
    });

    expect(result.email).toBe('new@example.com');
    expect(userRepository.save).toHaveBeenCalled();
  });
});
```

## Checklist

- [ ] Domain entities have no framework dependencies
- [ ] Use cases orchestrate domain logic
- [ ] Infrastructure implements domain interfaces
- [ ] Dependencies point inward only
- [ ] Value objects for domain concepts
- [ ] Domain exceptions for business rules violations
- [ ] Mappers between layers
