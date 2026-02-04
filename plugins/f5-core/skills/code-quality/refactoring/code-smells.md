---
name: code-smells
description: Identifying and fixing code smells
category: code-quality/refactoring
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Code Smells

## Overview

Code smells are symptoms in code that may indicate deeper problems. They're not bugs, but weaknesses that slow development and increase maintenance costs.

## Common Code Smells

### 1. Long Method

```typescript
// ❌ Bad - Too long, does too much
async function processOrder(order: Order) {
  // Validate order (10 lines)
  if (!order.items || order.items.length === 0) {
    throw new Error('Order must have items');
  }
  if (!order.customerId) {
    throw new Error('Customer ID required');
  }
  // ... more validation

  // Calculate totals (15 lines)
  let subtotal = 0;
  for (const item of order.items) {
    subtotal += item.price * item.quantity;
  }
  const tax = subtotal * 0.1;
  const total = subtotal + tax;
  // ... more calculations

  // Apply discounts (20 lines)
  // Check inventory (10 lines)
  // Process payment (15 lines)
  // Update inventory (10 lines)
  // Send notifications (10 lines)
  // ... 90+ lines total
}

// ✅ Good - Extract methods
async function processOrder(order: Order): Promise<OrderResult> {
  validateOrder(order);
  const totals = calculateTotals(order);
  const finalAmount = applyDiscounts(totals, order.customer);
  await checkInventory(order.items);
  const payment = await processPayment(order, finalAmount);
  await updateInventory(order.items);
  await sendOrderConfirmation(order, payment);
  return { orderId: order.id, payment };
}
```

### 2. Long Parameter List

```typescript
// ❌ Bad - Too many parameters
function createUser(
  name: string,
  email: string,
  password: string,
  phone: string,
  address: string,
  city: string,
  country: string,
  role: string,
  department: string,
  manager: string
) {}

// ✅ Good - Use object parameter
interface CreateUserDTO {
  name: string;
  email: string;
  password: string;
  phone?: string;
  address?: Address;
  role?: UserRole;
  department?: string;
  managerId?: string;
}

function createUser(data: CreateUserDTO): User {
  // Implementation
}
```

### 3. Duplicate Code

```typescript
// ❌ Bad - Repeated validation
// file: userService.ts
function validateEmail(email: string): boolean {
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return regex.test(email);
}

// file: contactService.ts (same logic!)
function isValidEmail(email: string): boolean {
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return regex.test(email);
}

// ✅ Good - Single source of truth
// file: utils/validators.ts
export const validators = {
  email: (value: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value),
  phone: (value: string) => /^\+?[\d\s-]{10,}$/.test(value),
  url: (value: string) => {
    try {
      new URL(value);
      return true;
    } catch {
      return false;
    }
  },
};
```

### 4. Primitive Obsession

```typescript
// ❌ Bad - Using primitives for domain concepts
function processPayment(
  amount: number,
  currency: string,
  cardNumber: string,
  expiry: string,
  cvv: string
): boolean {
  // How do we know amount is positive?
  // How do we validate currency?
  // What's the card number format?
}

// ✅ Good - Use value objects
class Money {
  constructor(
    public readonly amount: number,
    public readonly currency: Currency
  ) {
    if (amount < 0) throw new Error('Amount cannot be negative');
  }

  add(other: Money): Money {
    if (this.currency !== other.currency) {
      throw new CurrencyMismatchError();
    }
    return new Money(this.amount + other.amount, this.currency);
  }

  format(): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: this.currency,
    }).format(this.amount);
  }
}

class CreditCard {
  constructor(
    private readonly number: string,
    private readonly expiry: Date,
    private readonly cvv: string
  ) {
    this.validate();
  }

  private validate(): void {
    if (!this.isValidNumber()) throw new InvalidCardNumberError();
    if (this.isExpired()) throw new ExpiredCardError();
  }
}

function processPayment(amount: Money, card: CreditCard): PaymentResult {
  // Type-safe, validated inputs
}
```

### 5. Feature Envy

```typescript
// ❌ Bad - Method uses another object's data extensively
class OrderProcessor {
  calculateShipping(order: Order): number {
    const weight = order.items.reduce((sum, item) => sum + item.weight, 0);
    const address = order.customer.address;
    const zone = this.getShippingZone(address.country);
    const baseRate = order.customer.isPremium ? 5 : 10;
    const distance = this.calculateDistance(address.postalCode);
    return weight * zone.rate + baseRate + distance * 0.01;
  }
}

// ✅ Good - Move method to where the data lives
class Order {
  calculateShipping(): Money {
    const zone = ShippingZone.forCountry(this.customer.address.country);
    const baseRate = this.customer.shippingRate;
    return new Money(
      this.totalWeight * zone.rate + baseRate,
      this.currency
    );
  }

  get totalWeight(): number {
    return this.items.reduce((sum, item) => sum + item.weight, 0);
  }
}

class Customer {
  get shippingRate(): number {
    return this.isPremium ? 5 : 10;
  }
}
```

### 6. Shotgun Surgery

```typescript
// ❌ Bad - One change requires many file edits
// Changing user status requires editing:
// - UserService.ts (status logic)
// - UserController.ts (status endpoint)
// - UserRepository.ts (status query)
// - UserValidator.ts (status validation)
// - userRoutes.ts (status route)

// ✅ Good - Encapsulate related changes
class User {
  private _status: UserStatus;

  activate(): void {
    if (this._status === UserStatus.Suspended) {
      throw new Error('Cannot activate suspended user');
    }
    this._status = UserStatus.Active;
    this.addDomainEvent(new UserActivatedEvent(this.id));
  }

  deactivate(reason: string): void {
    this._status = UserStatus.Inactive;
    this.deactivationReason = reason;
    this.addDomainEvent(new UserDeactivatedEvent(this.id, reason));
  }

  suspend(reason: string): void {
    this._status = UserStatus.Suspended;
    this.suspensionReason = reason;
    this.addDomainEvent(new UserSuspendedEvent(this.id, reason));
  }
}
```

### 7. God Class

```typescript
// ❌ Bad - Class does everything
class UserManager {
  createUser() {}
  updateUser() {}
  deleteUser() {}
  sendEmail() {}
  generateReport() {}
  validateInput() {}
  formatOutput() {}
  logActivity() {}
  exportToCsv() {}
  importFromCsv() {}
  calculateStats() {}
  // ... 50+ methods
}

// ✅ Good - Single responsibility
class UserService {
  constructor(
    private repository: UserRepository,
    private validator: UserValidator,
    private eventBus: EventBus
  ) {}

  async create(data: CreateUserDTO): Promise<User> {
    this.validator.validate(data);
    const user = User.create(data);
    await this.repository.save(user);
    this.eventBus.publish(new UserCreatedEvent(user));
    return user;
  }
}

class UserEmailService {
  async sendWelcome(user: User): Promise<void> {}
  async sendPasswordReset(user: User, token: string): Promise<void> {}
}

class UserReportService {
  generateActivityReport(userId: string): Report {}
  exportUsers(format: ExportFormat): Buffer {}
}
```

### 8. Magic Numbers/Strings

```typescript
// ❌ Bad - Magic values
if (user.age >= 18) {}
if (order.total > 100) {}
if (status === 'active') {}
if (retryCount < 3) {}
setTimeout(callback, 86400000);

// ✅ Good - Named constants
const MINIMUM_AGE = 18;
const FREE_SHIPPING_THRESHOLD = 100;
const MAX_RETRY_ATTEMPTS = 3;
const ONE_DAY_MS = 24 * 60 * 60 * 1000;

enum UserStatus {
  Active = 'active',
  Inactive = 'inactive',
  Suspended = 'suspended',
}

if (user.age >= MINIMUM_AGE) {}
if (order.total > FREE_SHIPPING_THRESHOLD) {}
if (status === UserStatus.Active) {}
if (retryCount < MAX_RETRY_ATTEMPTS) {}
setTimeout(callback, ONE_DAY_MS);
```

### 9. Data Clumps

```typescript
// ❌ Bad - Same data groups appear together
function createEvent(
  startDate: Date,
  startTime: string,
  endDate: Date,
  endTime: string,
  title: string
) {}

function updateEvent(
  eventId: string,
  startDate: Date,
  startTime: string,
  endDate: Date,
  endTime: string
) {}

// ✅ Good - Group into object
interface DateTimeRange {
  start: Date;
  end: Date;
}

function createEvent(title: string, when: DateTimeRange): Event {}
function updateEvent(eventId: string, when: DateTimeRange): Event {}
```

### 10. Comments Explaining Bad Code

```typescript
// ❌ Bad - Comment explains confusing code
// Check if user can access the resource based on their role and subscription
// and whether the resource is public or the user owns it
if (
  (user.role === 'admin' || user.subscription === 'premium') &&
  (resource.isPublic || resource.ownerId === user.id)
) {}

// ✅ Good - Self-documenting code
const hasRequiredAccess = user.isAdmin || user.hasPremiumSubscription;
const canAccessResource = resource.isPublic || resource.isOwnedBy(user);

if (hasRequiredAccess && canAccessResource) {}

// Even better - extract to method
function canUserAccessResource(user: User, resource: Resource): boolean {
  const hasRequiredAccess = user.isAdmin || user.hasPremiumSubscription;
  const canAccessResource = resource.isPublic || resource.isOwnedBy(user);
  return hasRequiredAccess && canAccessResource;
}
```

## Code Smell Detection Tools

| Tool | Detects |
|------|---------|
| ESLint | Complexity, unused code, style issues |
| SonarQube | All smell types, technical debt |
| TypeScript | Type issues, null safety |
| Code Climate | Duplication, complexity, churn |
| CodeScene | Hotspots, coupling, team patterns |

## Quick Reference

| Smell | Indicator | Fix |
|-------|-----------|-----|
| Long Method | >20 lines | Extract Method |
| Long Parameters | >4 params | Parameter Object |
| Duplicate Code | Similar blocks | Extract Function |
| Primitive Obsession | Raw types | Value Objects |
| Feature Envy | External data access | Move Method |
| God Class | Many responsibilities | Extract Class |
| Magic Numbers | Hardcoded values | Named Constants |
| Data Clumps | Repeated groups | Create Class |
