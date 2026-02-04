---
name: dependency-inversion
description: Decoupling high-level and low-level modules through abstractions
category: architecture/principles
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Dependency Inversion Principle (DIP)

## Overview

The Dependency Inversion Principle states:
1. High-level modules should not depend on low-level modules. Both should depend on abstractions.
2. Abstractions should not depend on details. Details should depend on abstractions.

## The Problem

```
Traditional Dependency Flow (Problematic):
┌──────────────────┐
│   Controller     │ ─────────────────────────┐
└────────┬─────────┘                          │
         │ depends on                         │
         ▼                                    │
┌──────────────────┐                          │ All dependencies
│    Service       │ ─────────────────────────┤ flow downward
└────────┬─────────┘                          │
         │ depends on                         │
         ▼                                    │
┌──────────────────┐                          │
│   Repository     │ ─────────────────────────┤
└────────┬─────────┘                          │
         │ depends on                         │
         ▼                                    │
┌──────────────────┐                          │
│   MySQL Driver   │ ─────────────────────────┘
└──────────────────┘
```

## The Solution

```
Inverted Dependency Flow (DIP Applied):
┌──────────────────┐
│   Controller     │
└────────┬─────────┘
         │ depends on interface
         ▼
┌──────────────────┐
│   «interface»    │ ◄──────────┐
│   IUserService   │            │
└────────┬─────────┘            │
         △                      │
         │ implements           │
┌────────┴─────────┐            │
│   UserService    │────────────┤ High-level defines
└────────┬─────────┘            │ the interfaces
         │ depends on interface │
         ▼                      │
┌──────────────────┐            │
│   «interface»    │ ◄──────────┘
│  IUserRepository │
└────────┬─────────┘
         △
         │ implements
┌────────┴─────────┐
│ MySQLUserRepo    │  ← Low-level implements
└──────────────────┘
```

## Implementation Patterns

### Pattern 1: Constructor Injection

```typescript
// ❌ Without DIP - Tightly coupled
class UserService {
  private userRepository = new MySQLUserRepository();  // Direct dependency
  private emailService = new SendGridEmailService();   // Direct dependency

  async createUser(data: CreateUserDTO): Promise<User> {
    const user = await this.userRepository.save(data);
    await this.emailService.sendWelcome(user.email);
    return user;
  }
}

// ✅ With DIP - Loosely coupled
// Define abstractions in domain layer
interface UserRepository {
  save(data: CreateUserDTO): Promise<User>;
  findById(id: string): Promise<User | null>;
  findByEmail(email: string): Promise<User | null>;
}

interface EmailService {
  sendWelcome(email: string): Promise<void>;
}

// Service depends on abstractions
class UserService {
  constructor(
    private readonly userRepository: UserRepository,
    private readonly emailService: EmailService
  ) {}

  async createUser(data: CreateUserDTO): Promise<User> {
    const user = await this.userRepository.save(data);
    await this.emailService.sendWelcome(user.email);
    return user;
  }
}

// Infrastructure implements abstractions
class MySQLUserRepository implements UserRepository {
  async save(data: CreateUserDTO): Promise<User> { /* MySQL implementation */ }
  async findById(id: string): Promise<User | null> { /* ... */ }
  async findByEmail(email: string): Promise<User | null> { /* ... */ }
}

class SendGridEmailService implements EmailService {
  async sendWelcome(email: string): Promise<void> { /* SendGrid implementation */ }
}

// Composition at startup
const userRepository = new MySQLUserRepository();
const emailService = new SendGridEmailService();
const userService = new UserService(userRepository, emailService);
```

### Pattern 2: DI Container

```typescript
// Using InversifyJS or similar
import { Container, injectable, inject } from 'inversify';

// Symbols for dependency identification
const TYPES = {
  UserRepository: Symbol.for('UserRepository'),
  EmailService: Symbol.for('EmailService'),
  UserService: Symbol.for('UserService'),
};

// Mark implementations as injectable
@injectable()
class MySQLUserRepository implements UserRepository {
  async save(data: CreateUserDTO): Promise<User> { /* ... */ }
  async findById(id: string): Promise<User | null> { /* ... */ }
  async findByEmail(email: string): Promise<User | null> { /* ... */ }
}

@injectable()
class SendGridEmailService implements EmailService {
  async sendWelcome(email: string): Promise<void> { /* ... */ }
}

@injectable()
class UserService {
  constructor(
    @inject(TYPES.UserRepository) private userRepository: UserRepository,
    @inject(TYPES.EmailService) private emailService: EmailService
  ) {}
}

// Configure container
const container = new Container();
container.bind<UserRepository>(TYPES.UserRepository).to(MySQLUserRepository);
container.bind<EmailService>(TYPES.EmailService).to(SendGridEmailService);
container.bind<UserService>(TYPES.UserService).to(UserService);

// Resolve dependencies
const userService = container.get<UserService>(TYPES.UserService);
```

### Pattern 3: Factory Pattern with DIP

```typescript
// When you need runtime decisions
interface PaymentGateway {
  charge(amount: number): Promise<ChargeResult>;
  refund(chargeId: string): Promise<RefundResult>;
}

interface PaymentGatewayFactory {
  create(type: PaymentType): PaymentGateway;
}

class DefaultPaymentGatewayFactory implements PaymentGatewayFactory {
  constructor(
    private stripeGateway: StripeGateway,
    private paypalGateway: PayPalGateway
  ) {}

  create(type: PaymentType): PaymentGateway {
    switch (type) {
      case 'stripe': return this.stripeGateway;
      case 'paypal': return this.paypalGateway;
      default: throw new Error(`Unknown payment type: ${type}`);
    }
  }
}

// Service uses factory abstraction
class PaymentService {
  constructor(private gatewayFactory: PaymentGatewayFactory) {}

  async processPayment(order: Order, paymentType: PaymentType): Promise<Payment> {
    const gateway = this.gatewayFactory.create(paymentType);
    const result = await gateway.charge(order.total);
    return Payment.create(order.id, result);
  }
}
```

## Layer Organization with DIP

```
src/
├── domain/                      # Core business logic (no external deps)
│   ├── entities/
│   │   └── user.ts
│   ├── repositories/            # Interface definitions
│   │   └── user.repository.ts   # interface UserRepository
│   ├── services/               # Interface definitions
│   │   └── email.service.ts    # interface EmailService
│   └── errors/
│
├── application/                 # Use cases (depends on domain interfaces)
│   ├── use-cases/
│   │   └── create-user.ts      # Uses UserRepository interface
│   └── dtos/
│
├── infrastructure/             # Implementations (depends on domain interfaces)
│   ├── persistence/
│   │   ├── mysql/
│   │   │   └── mysql-user.repository.ts  # implements UserRepository
│   │   └── postgres/
│   │       └── postgres-user.repository.ts
│   ├── email/
│   │   ├── sendgrid.service.ts  # implements EmailService
│   │   └── ses.service.ts
│   └── di/
│       └── container.ts         # Wire everything together
│
└── presentation/               # HTTP/GraphQL/CLI (depends on application)
    └── http/
        └── controllers/
```

## Dependency Direction Rules

```typescript
// ✅ CORRECT: High-level defines interface, low-level implements

// domain/repositories/user.repository.ts (HIGH-LEVEL)
export interface UserRepository {
  save(user: User): Promise<void>;
  findById(id: string): Promise<User | null>;
}

// infrastructure/persistence/mysql-user.repository.ts (LOW-LEVEL)
import { UserRepository } from '@/domain/repositories/user.repository';

export class MySQLUserRepository implements UserRepository {
  // Implements the high-level interface
}


// ❌ WRONG: Low-level defines interface

// infrastructure/mysql/mysql-repository.ts (LOW-LEVEL defining interface)
export interface MySQLRepository<T> {  // Infrastructure-specific
  query(sql: string): Promise<T[]>;
  execute(sql: string): Promise<void>;
}

// domain/services/user.service.ts (HIGH-LEVEL depending on low-level)
import { MySQLRepository } from '@/infrastructure/mysql';  // Wrong direction!

export class UserService {
  constructor(private repo: MySQLRepository<User>) {}  // Coupled to MySQL!
}
```

## Testing Benefits

```typescript
// Easy to test with mock implementations
describe('UserService', () => {
  let userService: UserService;
  let mockUserRepository: jest.Mocked<UserRepository>;
  let mockEmailService: jest.Mocked<EmailService>;

  beforeEach(() => {
    // Create mocks that implement the interfaces
    mockUserRepository = {
      save: jest.fn(),
      findById: jest.fn(),
      findByEmail: jest.fn(),
    };

    mockEmailService = {
      sendWelcome: jest.fn(),
    };

    // Inject mocks
    userService = new UserService(mockUserRepository, mockEmailService);
  });

  it('should create user and send welcome email', async () => {
    const userData = { email: 'test@example.com', name: 'Test' };
    const savedUser = { id: '1', ...userData };

    mockUserRepository.save.mockResolvedValue(savedUser);
    mockEmailService.sendWelcome.mockResolvedValue();

    const result = await userService.createUser(userData);

    expect(mockUserRepository.save).toHaveBeenCalledWith(userData);
    expect(mockEmailService.sendWelcome).toHaveBeenCalledWith(userData.email);
    expect(result).toEqual(savedUser);
  });

  it('should not send email if save fails', async () => {
    mockUserRepository.save.mockRejectedValue(new Error('DB error'));

    await expect(userService.createUser({ email: 'test@example.com' }))
      .rejects.toThrow('DB error');

    expect(mockEmailService.sendWelcome).not.toHaveBeenCalled();
  });
});
```

## Common Violations

### 1. Concrete Class Dependencies

```typescript
// ❌ Depending on concrete class
class OrderService {
  private stripe = new Stripe(process.env.STRIPE_KEY);  // Concrete!
}

// ✅ Depending on abstraction
class OrderService {
  constructor(private paymentGateway: PaymentGateway) {}
}
```

### 2. Framework Dependencies in Domain

```typescript
// ❌ Domain coupled to framework
import { Entity, Column } from 'typeorm';  // Framework in domain!

@Entity()
export class User {
  @Column()
  email: string;
}

// ✅ Pure domain entity
export class User {
  constructor(
    public readonly id: string,
    public email: string,
    public name: string
  ) {}
}

// TypeORM schema separate in infrastructure
@Entity('users')
export class UserEntity {
  @PrimaryColumn()
  id: string;

  @Column()
  email: string;
}
```

### 3. Static Method Dependencies

```typescript
// ❌ Static methods can't be inverted
class UserService {
  async hashPassword(password: string) {
    return bcrypt.hash(password, 10);  // Static call, can't mock
  }
}

// ✅ Injectable service
interface PasswordHasher {
  hash(password: string): Promise<string>;
  verify(password: string, hash: string): Promise<boolean>;
}

class BcryptPasswordHasher implements PasswordHasher {
  async hash(password: string): Promise<string> {
    return bcrypt.hash(password, 10);
  }
  async verify(password: string, hash: string): Promise<boolean> {
    return bcrypt.compare(password, hash);
  }
}
```

## Summary

| Aspect | Without DIP | With DIP |
|--------|-------------|----------|
| Coupling | High-level → Low-level | Both → Abstractions |
| Testing | Hard (real dependencies) | Easy (mock interfaces) |
| Flexibility | Hard to change implementations | Swap implementations easily |
| Compile-time | Changes cascade | Isolated changes |
| Dependencies | Point downward | Point toward domain |
