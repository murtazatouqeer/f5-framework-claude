---
name: dry-kiss-yagni
description: Foundational software design principles
category: architecture/principles
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# DRY, KISS, YAGNI Principles

## Overview

Three complementary principles that guide software design toward
simplicity, maintainability, and pragmatism.

## DRY - Don't Repeat Yourself

> Every piece of knowledge must have a single, unambiguous,
> authoritative representation within a system.

### Bad Example
```typescript
// ❌ Duplicated validation logic
class UserController {
  createUser(data: any) {
    // Validation duplicated here
    if (!data.email || !data.email.includes('@')) {
      throw new Error('Invalid email');
    }
    if (!data.password || data.password.length < 8) {
      throw new Error('Password too short');
    }
    // ... create user
  }

  updateUser(id: string, data: any) {
    // Same validation duplicated!
    if (!data.email || !data.email.includes('@')) {
      throw new Error('Invalid email');
    }
    if (!data.password || data.password.length < 8) {
      throw new Error('Password too short');
    }
    // ... update user
  }
}
```

### Good Example
```typescript
// ✅ Single source of truth for validation
class EmailValidator {
  static validate(email: string): void {
    if (!email || !email.includes('@')) {
      throw new ValidationError('Invalid email format');
    }
  }
}

class PasswordValidator {
  static validate(password: string): void {
    if (!password || password.length < 8) {
      throw new ValidationError('Password must be at least 8 characters');
    }
  }
}

class UserValidator {
  static validate(data: UserInput): void {
    EmailValidator.validate(data.email);
    PasswordValidator.validate(data.password);
  }
}

class UserController {
  createUser(data: UserInput) {
    UserValidator.validate(data);
    // ... create user
  }

  updateUser(id: string, data: UserInput) {
    UserValidator.validate(data);
    // ... update user
  }
}
```

### DRY Applied to Different Levels

```typescript
// Configuration - Single source
// config/database.ts
export const DATABASE_CONFIG = {
  host: process.env.DB_HOST,
  port: parseInt(process.env.DB_PORT || '5432'),
  database: process.env.DB_NAME,
} as const;

// Constants - Centralized
// constants/status.ts
export const ORDER_STATUS = {
  PENDING: 'pending',
  CONFIRMED: 'confirmed',
  SHIPPED: 'shipped',
  DELIVERED: 'delivered',
  CANCELLED: 'cancelled',
} as const;

// Types derived from constants
export type OrderStatus = typeof ORDER_STATUS[keyof typeof ORDER_STATUS];

// Business rules - Single location
// domain/rules/pricing-rules.ts
export class PricingRules {
  static readonly TAX_RATE = 0.1;
  static readonly FREE_SHIPPING_THRESHOLD = 100;
  static readonly VIP_DISCOUNT = 0.15;

  static calculateTax(amount: number): number {
    return amount * this.TAX_RATE;
  }

  static qualifiesForFreeShipping(amount: number): boolean {
    return amount >= this.FREE_SHIPPING_THRESHOLD;
  }
}
```

### When DRY Goes Wrong (WET - Write Everything Twice)

```typescript
// ❌ Over-DRY: Forced abstraction for unrelated code
class StringManipulator {
  // Bad: These operations are unrelated, forced together
  static process(str: string, type: 'email' | 'phone' | 'name'): string {
    switch (type) {
      case 'email': return str.toLowerCase().trim();
      case 'phone': return str.replace(/\D/g, '');
      case 'name': return str.trim().split(' ').map(s =>
        s.charAt(0).toUpperCase() + s.slice(1).toLowerCase()
      ).join(' ');
    }
  }
}

// ✅ Better: Let them be separate - they'll evolve differently
const normalizeEmail = (email: string) => email.toLowerCase().trim();
const normalizePhone = (phone: string) => phone.replace(/\D/g, '');
const normalizeName = (name: string) => name.trim().split(' ')
  .map(s => s.charAt(0).toUpperCase() + s.slice(1).toLowerCase())
  .join(' ');
```

## KISS - Keep It Simple, Stupid

> The simplest solution is usually the best solution.

### Bad Example
```typescript
// ❌ Over-engineered solution
class UserStatusManager {
  private statusStateMachine: StateMachine;
  private statusHistory: StatusHistoryTracker;
  private statusNotifier: StatusChangeNotifier;
  private statusValidator: StatusTransitionValidator;

  constructor(
    private eventBus: EventBus,
    private cacheManager: CacheManager,
    private auditLogger: AuditLogger
  ) {
    this.statusStateMachine = new StateMachine(USER_STATUS_TRANSITIONS);
    this.statusHistory = new StatusHistoryTracker(this.cacheManager);
    this.statusNotifier = new StatusChangeNotifier(this.eventBus);
    this.statusValidator = new StatusTransitionValidator();
  }

  async setStatus(userId: string, newStatus: UserStatus): Promise<void> {
    const user = await this.userRepository.findById(userId);
    const currentStatus = user.status;

    await this.statusValidator.validateTransition(currentStatus, newStatus);
    this.statusStateMachine.transition(currentStatus, newStatus);
    await this.statusHistory.record(userId, currentStatus, newStatus);

    user.status = newStatus;
    await this.userRepository.save(user);

    await this.statusNotifier.notify(userId, newStatus);
    await this.auditLogger.log('status_change', { userId, from: currentStatus, to: newStatus });
    await this.cacheManager.invalidate(`user:${userId}`);
  }
}
```

### Good Example
```typescript
// ✅ Simple solution that meets requirements
class UserService {
  constructor(private userRepository: UserRepository) {}

  async updateStatus(userId: string, newStatus: UserStatus): Promise<void> {
    const user = await this.userRepository.findById(userId);

    if (!this.canTransition(user.status, newStatus)) {
      throw new InvalidStatusTransitionError(user.status, newStatus);
    }

    user.status = newStatus;
    await this.userRepository.save(user);
  }

  private canTransition(from: UserStatus, to: UserStatus): boolean {
    const allowed: Record<UserStatus, UserStatus[]> = {
      'pending': ['active', 'cancelled'],
      'active': ['suspended', 'cancelled'],
      'suspended': ['active', 'cancelled'],
      'cancelled': [],
    };
    return allowed[from]?.includes(to) ?? false;
  }
}
```

### KISS Guidelines

```typescript
// ✅ Prefer built-in over custom
// Bad: Custom array utilities
class ArrayUtils {
  static filter<T>(arr: T[], predicate: (item: T) => boolean): T[] { /* ... */ }
  static map<T, U>(arr: T[], transform: (item: T) => U): U[] { /* ... */ }
}
// Good: Use native methods
const filtered = items.filter(item => item.active);
const mapped = items.map(item => item.name);

// ✅ Prefer flat over nested
// Bad: Deep nesting
if (user) {
  if (user.isActive) {
    if (user.hasPermission('admin')) {
      if (user.emailVerified) {
        // do something
      }
    }
  }
}
// Good: Early returns
if (!user) return;
if (!user.isActive) return;
if (!user.hasPermission('admin')) return;
if (!user.emailVerified) return;
// do something

// ✅ Prefer explicit over clever
// Bad: Clever one-liner
const result = data?.items?.filter(Boolean).reduce((a, b) => ({...a, [b.id]: b}), {}) ?? {};
// Good: Clear steps
const items = data?.items ?? [];
const validItems = items.filter(item => item != null);
const result = Object.fromEntries(validItems.map(item => [item.id, item]));
```

## YAGNI - You Aren't Gonna Need It

> Don't implement functionality until it's actually needed.

### Bad Example
```typescript
// ❌ Over-engineering for hypothetical future needs
class UserService {
  constructor(
    private userRepository: UserRepository,
    private cacheService: CacheService,  // "We might need caching"
    private analyticsService: AnalyticsService,  // "We might want analytics"
    private featureFlagService: FeatureFlagService,  // "We might need feature flags"
    private auditService: AuditService,  // "We might need auditing"
    private notificationService: NotificationService,  // "We might notify users"
  ) {}

  async createUser(data: CreateUserDTO): Promise<User> {
    // Check feature flags for "future" variations
    const useNewFlow = await this.featureFlagService.isEnabled('new_user_flow');

    // Create user with "flexible" schema for future fields
    const user = await this.userRepository.create({
      ...data,
      metadata: {},  // "For future extensibility"
      tags: [],  // "We might need tags later"
      preferences: {},  // "Users might have preferences"
      customFields: {},  // "For custom integrations"
    });

    // Cache invalidation "we might need"
    await this.cacheService.invalidatePattern('users:*');

    // Track analytics "we might want"
    await this.analyticsService.track('user_created', { userId: user.id });

    // Audit logging "we might need for compliance"
    await this.auditService.log('CREATE_USER', user);

    return user;
  }
}
```

### Good Example
```typescript
// ✅ Implement what's needed now
class UserService {
  constructor(private userRepository: UserRepository) {}

  async createUser(data: CreateUserDTO): Promise<User> {
    return this.userRepository.create({
      email: data.email,
      name: data.name,
      password: await this.hashPassword(data.password),
    });
  }

  private async hashPassword(password: string): Promise<string> {
    return bcrypt.hash(password, 10);
  }
}

// Add features when actually needed:
// - Caching: When performance becomes an issue
// - Analytics: When product needs data
// - Audit logging: When compliance requires it
```

### YAGNI Checklist

| Question | If YES | If NO |
|----------|--------|-------|
| Is there a current requirement? | Build it | Don't build it |
| Will it be used this sprint? | Consider it | Defer it |
| Is the cost of adding later high? | Consider carefully | Defer it |
| Does the team have bandwidth? | Maybe | Definitely no |

### YAGNI vs Future-Proofing

```typescript
// ✅ Good future-proofing: Interfaces allow change
interface PaymentGateway {
  charge(amount: number): Promise<ChargeResult>;
}

class StripeGateway implements PaymentGateway {
  async charge(amount: number): Promise<ChargeResult> {
    // Stripe implementation
  }
}

// ❌ Bad future-proofing: Building unused implementations
class PaymentGatewayFactory {
  static create(type: 'stripe' | 'paypal' | 'square' | 'braintree'): PaymentGateway {
    // Building 4 implementations when only Stripe is needed
  }
}
```

## Balancing the Principles

### Decision Matrix

| Scenario | DRY | KISS | YAGNI |
|----------|-----|------|-------|
| Duplicated code | Apply | - | - |
| Complex abstraction | - | Question | - |
| Future feature | - | - | Don't build |
| Third duplicate | Apply carefully | Keep simple | Build minimal |

### Practical Example

```typescript
// Scenario: Building an e-commerce checkout

// ❌ Violates all three principles
class UniversalCheckoutProcessor {
  async process(cart: Cart, options: CheckoutOptions): Promise<Order> {
    // Supports 15 payment gateways (YAGNI - only use 2)
    // Complex routing logic (KISS violation)
    // Duplicates validation in multiple places (DRY violation)
  }
}

// ✅ Follows all three principles
class CheckoutService {
  constructor(
    private paymentGateway: PaymentGateway,  // Interface (future-proof but simple)
    private orderRepository: OrderRepository,
    private inventoryService: InventoryService
  ) {}

  async checkout(cart: Cart): Promise<Order> {
    // Single validation point (DRY)
    this.validateCart(cart);

    // Simple, linear flow (KISS)
    await this.inventoryService.reserve(cart.items);
    const payment = await this.paymentGateway.charge(cart.total);
    const order = await this.orderRepository.create(cart, payment);

    return order;
  }

  private validateCart(cart: Cart): void {
    if (cart.items.length === 0) {
      throw new EmptyCartError();
    }
  }
}
```

## Summary

| Principle | Focus | Question to Ask |
|-----------|-------|-----------------|
| DRY | Eliminate duplication | "Is this knowledge repeated?" |
| KISS | Reduce complexity | "Is this the simplest solution?" |
| YAGNI | Avoid speculation | "Do I need this right now?" |
