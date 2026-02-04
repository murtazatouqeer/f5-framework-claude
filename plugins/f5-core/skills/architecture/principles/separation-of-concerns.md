---
name: separation-of-concerns
description: Organizing code by distinct responsibilities
category: architecture/principles
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Separation of Concerns (SoC)

## Overview

Separation of Concerns is the principle of dividing a program into
distinct sections, each addressing a separate concern. A concern is
a set of information that affects the code.

## Core Concept

```
┌─────────────────────────────────────────────────────────────┐
│                      Application                             │
├─────────────────┬─────────────────┬─────────────────────────┤
│   Presentation  │    Business     │     Data Access          │
│   (UI/API)      │    Logic        │     (Persistence)        │
├─────────────────┼─────────────────┼─────────────────────────┤
│ • Controllers   │ • Services      │ • Repositories           │
│ • Views         │ • Domain Models │ • Database Clients       │
│ • DTOs          │ • Validators    │ • ORMs                   │
│ • Serializers   │ • Business Rules│ • Cache                  │
└─────────────────┴─────────────────┴─────────────────────────┘
```

## Bad Example - Mixed Concerns

```typescript
// ❌ Controller doing everything
class UserController {
  async createUser(req: Request, res: Response) {
    // Validation (should be separate)
    if (!req.body.email || !req.body.email.includes('@')) {
      return res.status(400).json({ error: 'Invalid email' });
    }
    if (!req.body.password || req.body.password.length < 8) {
      return res.status(400).json({ error: 'Password too short' });
    }

    // Business logic (should be in service)
    const hashedPassword = await bcrypt.hash(req.body.password, 10);

    // Direct database access (should be in repository)
    const existingUser = await db.query(
      'SELECT * FROM users WHERE email = $1',
      [req.body.email]
    );

    if (existingUser.rows.length > 0) {
      return res.status(409).json({ error: 'Email already exists' });
    }

    const result = await db.query(
      'INSERT INTO users (email, password, created_at) VALUES ($1, $2, NOW()) RETURNING *',
      [req.body.email, hashedPassword]
    );

    // Email sending (should be separate service)
    await sendgrid.send({
      to: req.body.email,
      subject: 'Welcome!',
      html: `<h1>Welcome ${result.rows[0].email}</h1>`,
    });

    // Logging mixed in (should be middleware/decorator)
    console.log(`User created: ${result.rows[0].id}`);

    // Response formatting mixed with logic
    res.status(201).json({
      id: result.rows[0].id,
      email: result.rows[0].email,
      createdAt: result.rows[0].created_at,
    });
  }
}
```

## Good Example - Separated Concerns

```typescript
// ✅ Presentation Layer - Controller
// controllers/user.controller.ts
@Controller('users')
export class UserController {
  constructor(private readonly userService: UserService) {}

  @Post()
  @HttpCode(201)
  async create(@Body() dto: CreateUserDTO): Promise<UserResponseDTO> {
    const user = await this.userService.create(dto);
    return UserMapper.toResponse(user);
  }
}

// ✅ Presentation Layer - DTO & Validation
// dtos/create-user.dto.ts
export class CreateUserDTO {
  @IsEmail()
  @IsNotEmpty()
  email: string;

  @MinLength(8)
  @IsNotEmpty()
  password: string;
}

// ✅ Presentation Layer - Mapper
// mappers/user.mapper.ts
export class UserMapper {
  static toResponse(user: User): UserResponseDTO {
    return {
      id: user.id,
      email: user.email,
      createdAt: user.createdAt.toISOString(),
    };
  }
}

// ✅ Business Layer - Service
// services/user.service.ts
export class UserService {
  constructor(
    private readonly userRepository: UserRepository,
    private readonly passwordHasher: PasswordHasher,
    private readonly eventPublisher: EventPublisher
  ) {}

  async create(dto: CreateUserDTO): Promise<User> {
    // Business validation
    const exists = await this.userRepository.existsByEmail(dto.email);
    if (exists) {
      throw new EmailAlreadyExistsError(dto.email);
    }

    // Business logic
    const hashedPassword = await this.passwordHasher.hash(dto.password);
    const user = User.create(dto.email, hashedPassword);

    // Persistence
    await this.userRepository.save(user);

    // Side effects via events
    await this.eventPublisher.publish(new UserCreatedEvent(user));

    return user;
  }
}

// ✅ Data Access Layer - Repository
// repositories/user.repository.ts
export class UserRepository {
  constructor(private readonly db: Database) {}

  async save(user: User): Promise<void> {
    await this.db.query(
      'INSERT INTO users (id, email, password, created_at) VALUES ($1, $2, $3, $4)',
      [user.id, user.email, user.password, user.createdAt]
    );
  }

  async existsByEmail(email: string): Promise<boolean> {
    const result = await this.db.query(
      'SELECT 1 FROM users WHERE email = $1',
      [email]
    );
    return result.rowCount > 0;
  }
}

// ✅ Infrastructure - Event Handler (separate concern)
// handlers/user-created.handler.ts
export class UserCreatedHandler {
  constructor(private readonly emailService: EmailService) {}

  @OnEvent('user.created')
  async handle(event: UserCreatedEvent): Promise<void> {
    await this.emailService.sendWelcome(event.user.email);
  }
}
```

## Horizontal vs Vertical Separation

### Horizontal (Layer-based)

```
┌─────────────────────────────────────────┐
│           Presentation Layer            │  ← HTTP, GraphQL, CLI
├─────────────────────────────────────────┤
│           Application Layer             │  ← Use Cases, Services
├─────────────────────────────────────────┤
│             Domain Layer                │  ← Business Logic
├─────────────────────────────────────────┤
│          Infrastructure Layer           │  ← DB, External APIs
└─────────────────────────────────────────┘
```

### Vertical (Feature-based)

```
┌─────────────┬─────────────┬─────────────┐
│    Users    │   Orders    │  Products   │
├─────────────┼─────────────┼─────────────┤
│ Controller  │ Controller  │ Controller  │
│ Service     │ Service     │ Service     │
│ Repository  │ Repository  │ Repository  │
│ Entity      │ Entity      │ Entity      │
└─────────────┴─────────────┴─────────────┘
```

### Combined Approach (Recommended)

```
src/
├── modules/                 # Vertical slices
│   ├── users/
│   │   ├── presentation/   # Horizontal layer
│   │   │   ├── user.controller.ts
│   │   │   └── dtos/
│   │   ├── application/    # Horizontal layer
│   │   │   └── user.service.ts
│   │   ├── domain/         # Horizontal layer
│   │   │   ├── user.entity.ts
│   │   │   └── user.repository.ts
│   │   └── infrastructure/ # Horizontal layer
│   │       └── prisma-user.repository.ts
│   ├── orders/
│   └── products/
└── shared/                  # Cross-cutting concerns
    ├── middleware/
    ├── guards/
    └── utils/
```

## Cross-Cutting Concerns

Some concerns span multiple layers and need special handling.

### Logging

```typescript
// ❌ Logging scattered everywhere
class OrderService {
  async create(dto: CreateOrderDTO) {
    console.log('Creating order', dto);
    try {
      const order = await this.doCreate(dto);
      console.log('Order created', order.id);
      return order;
    } catch (error) {
      console.error('Failed to create order', error);
      throw error;
    }
  }
}

// ✅ Logging as cross-cutting concern
@Injectable()
export class LoggingInterceptor implements NestInterceptor {
  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    const request = context.switchToHttp().getRequest();
    const method = request.method;
    const url = request.url;
    const now = Date.now();

    return next.handle().pipe(
      tap(() => {
        console.log(`${method} ${url} - ${Date.now() - now}ms`);
      }),
      catchError((error) => {
        console.error(`${method} ${url} failed:`, error.message);
        throw error;
      }),
    );
  }
}
```

### Authentication/Authorization

```typescript
// ❌ Auth logic mixed in controller
class OrderController {
  async create(req: Request) {
    // Auth check mixed with business logic
    const token = req.headers.authorization?.split(' ')[1];
    if (!token) throw new UnauthorizedError();

    const user = jwt.verify(token, SECRET);
    if (!user.permissions.includes('create:orders')) {
      throw new ForbiddenError();
    }

    // Business logic starts here...
  }
}

// ✅ Auth as separate concern
// guards/auth.guard.ts
@Injectable()
export class AuthGuard implements CanActivate {
  canActivate(context: ExecutionContext): boolean {
    const request = context.switchToHttp().getRequest();
    return this.validateToken(request.headers.authorization);
  }
}

// guards/permission.guard.ts
@Injectable()
export class PermissionGuard implements CanActivate {
  constructor(private reflector: Reflector) {}

  canActivate(context: ExecutionContext): boolean {
    const requiredPermissions = this.reflector.get<string[]>(
      'permissions',
      context.getHandler()
    );
    const user = context.switchToHttp().getRequest().user;
    return requiredPermissions.every(p => user.permissions.includes(p));
  }
}

// Usage - clean controller
@Controller('orders')
@UseGuards(AuthGuard, PermissionGuard)
export class OrderController {
  @Post()
  @Permissions('create:orders')
  async create(@Body() dto: CreateOrderDTO) {
    // Pure business logic
    return this.orderService.create(dto);
  }
}
```

### Error Handling

```typescript
// ❌ Error handling mixed everywhere
class ProductService {
  async findById(id: string) {
    try {
      const product = await this.repo.findById(id);
      if (!product) {
        throw { status: 404, message: 'Product not found' };
      }
      return product;
    } catch (error) {
      if (error.code === 'ECONNREFUSED') {
        throw { status: 503, message: 'Database unavailable' };
      }
      throw error;
    }
  }
}

// ✅ Centralized error handling
// Domain errors
export class ProductNotFoundError extends DomainError {
  constructor(id: string) {
    super(`Product ${id} not found`);
  }
}

// Service throws domain errors
class ProductService {
  async findById(id: string): Promise<Product> {
    const product = await this.repo.findById(id);
    if (!product) {
      throw new ProductNotFoundError(id);
    }
    return product;
  }
}

// Global error filter handles all errors
@Catch()
export class GlobalExceptionFilter implements ExceptionFilter {
  catch(exception: unknown, host: ArgumentsHost) {
    const response = host.switchToHttp().getResponse();

    if (exception instanceof ProductNotFoundError) {
      return response.status(404).json({
        error: 'NOT_FOUND',
        message: exception.message,
      });
    }

    if (exception instanceof ValidationError) {
      return response.status(400).json({
        error: 'VALIDATION_ERROR',
        details: exception.errors,
      });
    }

    // Default 500 error
    return response.status(500).json({
      error: 'INTERNAL_ERROR',
      message: 'An unexpected error occurred',
    });
  }
}
```

## Benefits

| Benefit | Description |
|---------|-------------|
| Maintainability | Changes in one area don't affect others |
| Testability | Units can be tested in isolation |
| Reusability | Components can be reused in different contexts |
| Understandability | Code is organized logically |
| Parallel Development | Teams can work on different concerns |

## Warning Signs of Mixed Concerns

- Controllers with database queries
- Services with HTTP response formatting
- Entities with validation decorators
- Business logic in middleware
- Database entities used as API responses
- Configuration values hardcoded in business logic
