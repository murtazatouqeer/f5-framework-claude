---
name: layered-architecture
description: Traditional N-tier layered architecture pattern
category: architecture/patterns
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Layered Architecture (N-Tier)

## Overview

Layered Architecture organizes code into horizontal layers, where each
layer has a specific role and only depends on the layer directly below it.

## Traditional 3-Tier Architecture

```
┌─────────────────────────────────────┐
│       Presentation Layer            │  ← UI, API Controllers
│   (User Interface / API Layer)      │
├─────────────────────────────────────┤
│          │                          │
│          ▼                          │
├─────────────────────────────────────┤
│        Business Layer               │  ← Business Logic, Services
│     (Business Logic Layer)          │
├─────────────────────────────────────┤
│          │                          │
│          ▼                          │
├─────────────────────────────────────┤
│         Data Layer                  │  ← Data Access, ORM
│     (Data Access Layer)             │
└─────────────────────────────────────┘
              │
              ▼
        ┌───────────┐
        │ Database  │
        └───────────┘
```

## 4-Tier Architecture (with Domain)

```
┌─────────────────────────────────────┐
│       Presentation Layer            │
├─────────────────────────────────────┤
│        Application Layer            │  ← Use Cases, Orchestration
├─────────────────────────────────────┤
│          Domain Layer               │  ← Business Rules, Entities
├─────────────────────────────────────┤
│      Infrastructure Layer           │  ← Data Access, External APIs
└─────────────────────────────────────┘
```

## Directory Structure

```
src/
├── presentation/              # Layer 1: UI/API
│   ├── controllers/
│   │   ├── user.controller.ts
│   │   └── order.controller.ts
│   ├── middlewares/
│   │   ├── auth.middleware.ts
│   │   └── error.middleware.ts
│   ├── validators/
│   │   └── user.validator.ts
│   └── dtos/
│       ├── requests/
│       └── responses/
│
├── business/                  # Layer 2: Business Logic
│   ├── services/
│   │   ├── user.service.ts
│   │   └── order.service.ts
│   ├── validators/
│   │   └── business-rules.ts
│   └── interfaces/
│       └── service.interfaces.ts
│
├── data/                      # Layer 3: Data Access
│   ├── repositories/
│   │   ├── user.repository.ts
│   │   └── order.repository.ts
│   ├── entities/
│   │   ├── user.entity.ts
│   │   └── order.entity.ts
│   └── migrations/
│
└── shared/                    # Cross-cutting concerns
    ├── utils/
    ├── constants/
    └── types/
```

## Implementation

### Presentation Layer

```typescript
// presentation/controllers/user.controller.ts
import { Controller, Get, Post, Body, Param, UseGuards } from '@nestjs/common';
import { UserService } from '@/business/services/user.service';
import { CreateUserDTO, UserResponseDTO } from '../dtos';
import { AuthGuard } from '../middlewares/auth.middleware';

@Controller('users')
export class UserController {
  constructor(private readonly userService: UserService) {}

  @Post()
  async create(@Body() dto: CreateUserDTO): Promise<UserResponseDTO> {
    const user = await this.userService.create(dto);
    return this.toResponse(user);
  }

  @Get(':id')
  @UseGuards(AuthGuard)
  async findOne(@Param('id') id: string): Promise<UserResponseDTO> {
    const user = await this.userService.findById(id);
    if (!user) {
      throw new NotFoundException('User not found');
    }
    return this.toResponse(user);
  }

  @Get()
  @UseGuards(AuthGuard)
  async findAll(): Promise<UserResponseDTO[]> {
    const users = await this.userService.findAll();
    return users.map(this.toResponse);
  }

  private toResponse(user: User): UserResponseDTO {
    return {
      id: user.id,
      email: user.email,
      name: user.name,
      createdAt: user.createdAt.toISOString(),
    };
  }
}

// presentation/dtos/create-user.dto.ts
import { IsEmail, IsString, MinLength } from 'class-validator';

export class CreateUserDTO {
  @IsEmail()
  email: string;

  @IsString()
  @MinLength(2)
  name: string;

  @IsString()
  @MinLength(8)
  password: string;
}
```

### Business Layer

```typescript
// business/services/user.service.ts
import { Injectable } from '@nestjs/common';
import { UserRepository } from '@/data/repositories/user.repository';
import { User } from '@/data/entities/user.entity';
import { CreateUserDTO } from '@/presentation/dtos/create-user.dto';
import * as bcrypt from 'bcrypt';

@Injectable()
export class UserService {
  constructor(private readonly userRepository: UserRepository) {}

  async create(dto: CreateUserDTO): Promise<User> {
    // Business validation
    const existingUser = await this.userRepository.findByEmail(dto.email);
    if (existingUser) {
      throw new ConflictException('Email already exists');
    }

    // Business logic
    const hashedPassword = await bcrypt.hash(dto.password, 10);

    const user = new User();
    user.email = dto.email;
    user.name = dto.name;
    user.password = hashedPassword;
    user.createdAt = new Date();

    return this.userRepository.save(user);
  }

  async findById(id: string): Promise<User | null> {
    return this.userRepository.findById(id);
  }

  async findAll(): Promise<User[]> {
    return this.userRepository.findAll();
  }

  async updatePassword(userId: string, newPassword: string): Promise<void> {
    const user = await this.userRepository.findById(userId);
    if (!user) {
      throw new NotFoundException('User not found');
    }

    // Business rule: password must be different from current
    const isSamePassword = await bcrypt.compare(newPassword, user.password);
    if (isSamePassword) {
      throw new BadRequestException('New password must be different');
    }

    user.password = await bcrypt.hash(newPassword, 10);
    await this.userRepository.save(user);
  }
}

// business/services/order.service.ts
@Injectable()
export class OrderService {
  constructor(
    private readonly orderRepository: OrderRepository,
    private readonly productRepository: ProductRepository,
    private readonly userService: UserService  // Services can use other services
  ) {}

  async createOrder(userId: string, items: OrderItemDTO[]): Promise<Order> {
    // Verify user exists
    const user = await this.userService.findById(userId);
    if (!user) {
      throw new NotFoundException('User not found');
    }

    // Calculate total and validate stock
    let total = 0;
    for (const item of items) {
      const product = await this.productRepository.findById(item.productId);
      if (!product) {
        throw new NotFoundException(`Product ${item.productId} not found`);
      }
      if (product.stock < item.quantity) {
        throw new BadRequestException(`Insufficient stock for ${product.name}`);
      }
      total += product.price * item.quantity;
    }

    // Create order
    const order = new Order();
    order.userId = userId;
    order.items = items;
    order.total = total;
    order.status = 'pending';
    order.createdAt = new Date();

    return this.orderRepository.save(order);
  }
}
```

### Data Layer

```typescript
// data/entities/user.entity.ts
import { Entity, Column, PrimaryGeneratedColumn, CreateDateColumn } from 'typeorm';

@Entity('users')
export class User {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ unique: true })
  email: string;

  @Column()
  name: string;

  @Column()
  password: string;

  @CreateDateColumn()
  createdAt: Date;

  @Column({ nullable: true })
  updatedAt: Date;
}

// data/repositories/user.repository.ts
import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { User } from '../entities/user.entity';

@Injectable()
export class UserRepository {
  constructor(
    @InjectRepository(User)
    private readonly repository: Repository<User>
  ) {}

  async save(user: User): Promise<User> {
    return this.repository.save(user);
  }

  async findById(id: string): Promise<User | null> {
    return this.repository.findOne({ where: { id } });
  }

  async findByEmail(email: string): Promise<User | null> {
    return this.repository.findOne({ where: { email } });
  }

  async findAll(): Promise<User[]> {
    return this.repository.find({
      order: { createdAt: 'DESC' },
    });
  }

  async delete(id: string): Promise<void> {
    await this.repository.delete(id);
  }
}
```

## Layer Dependencies

```
✅ Allowed Dependencies:
Presentation → Business → Data

❌ Forbidden Dependencies:
Data → Business (data layer shouldn't know business rules)
Business → Presentation (service shouldn't know about HTTP)
Data → Presentation (repository shouldn't format responses)
```

## Strict vs Relaxed Layering

### Strict Layering
Each layer can only access the layer immediately below.

```typescript
// ❌ Presentation directly accessing Data layer
@Controller('users')
class UserController {
  constructor(private userRepository: UserRepository) {}  // WRONG!
}

// ✅ Presentation through Business layer
@Controller('users')
class UserController {
  constructor(private userService: UserService) {}  // CORRECT
}
```

### Relaxed Layering
Layers can access any layer below them.

```typescript
// Presentation can access both Business and Data
@Controller('reports')
class ReportController {
  constructor(
    private orderService: OrderService,     // Business layer
    private reportRepository: ReportRepository  // Data layer (for reads)
  ) {}
}
```

## Cross-Cutting Concerns

```
┌─────────────────────────────────────┐
│       Presentation Layer            │
├──────────────────────┬──────────────┤
│                      │              │
│    Business Layer    │  Logging     │
│                      │  Security    │
├──────────────────────┤  Caching     │
│                      │  Error       │
│      Data Layer      │  Handling    │
│                      │              │
└──────────────────────┴──────────────┘
```

### Implementation

```typescript
// shared/interceptors/logging.interceptor.ts
@Injectable()
export class LoggingInterceptor implements NestInterceptor {
  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    const request = context.switchToHttp().getRequest();
    const { method, url } = request;
    const now = Date.now();

    return next.handle().pipe(
      tap(() => {
        console.log(`${method} ${url} - ${Date.now() - now}ms`);
      }),
    );
  }
}

// shared/filters/http-exception.filter.ts
@Catch()
export class AllExceptionsFilter implements ExceptionFilter {
  catch(exception: unknown, host: ArgumentsHost): void {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();

    const status = exception instanceof HttpException
      ? exception.getStatus()
      : 500;

    const message = exception instanceof HttpException
      ? exception.message
      : 'Internal server error';

    response.status(status).json({
      statusCode: status,
      message,
      timestamp: new Date().toISOString(),
    });
  }
}
```

## Advantages and Disadvantages

### Advantages

| Advantage | Description |
|-----------|-------------|
| Simplicity | Easy to understand and implement |
| Separation | Clear separation of concerns |
| Testability | Layers can be tested independently |
| Familiar | Well-known pattern, easy onboarding |

### Disadvantages

| Disadvantage | Description |
|--------------|-------------|
| Coupling | Changes can cascade through layers |
| Overhead | May require passing data through layers |
| Rigidity | Strict rules can feel constraining |
| Database-Centric | Often becomes data-driven design |

## When to Use

### Good Fit
- CRUD-heavy applications
- Small to medium projects
- Teams familiar with traditional patterns
- Applications with clear layer boundaries

### Consider Alternatives When
- Complex domain logic (use DDD)
- Multiple delivery mechanisms (use Hexagonal)
- Microservices (use Clean Architecture)
- Event-driven systems (use CQRS)

## Migration Path

```
Layered Architecture
        ↓
Add interfaces at layer boundaries
        ↓
Introduce domain layer
        ↓
Clean Architecture / Hexagonal
```
