---
name: clean-code-principles
description: Clean code principles and practices
category: code-quality/practices
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Clean Code Principles

## Overview

Clean code is code that is easy to read, understand, and maintain. It's code that clearly expresses intent and can be modified without fear.

## Core Principles

### 1. Meaningful Names

Names should reveal intent and be searchable.

```typescript
// ❌ Bad
const d = new Date();
const u = getUser();
function calc(a: number, b: number) {}

// ✅ Good
const currentDate = new Date();
const authenticatedUser = getUser();
function calculateOrderTotal(subtotal: number, taxRate: number): number {}
```

### 2. Functions Should Do One Thing

Each function should have a single responsibility.

```typescript
// ❌ Bad - Multiple responsibilities
async function handleUserRegistration(data: RegistrationData) {
  // Validate data (10 lines)
  // Hash password (5 lines)
  // Save to database (10 lines)
  // Send email (10 lines)
  // Log activity (5 lines)
  return user;
}

// ✅ Good - Single responsibility
async function registerUser(data: RegistrationData): Promise<User> {
  validateRegistrationData(data);
  const user = await createUser(data);
  await sendWelcomeEmail(user);
  await logUserRegistration(user);
  return user;
}

function validateRegistrationData(data: RegistrationData): void {
  if (!data.email || !data.password) {
    throw new ValidationError('Email and password required');
  }
}

async function createUser(data: RegistrationData): Promise<User> {
  const hashedPassword = await hashPassword(data.password);
  return db.users.create({
    email: data.email,
    password: hashedPassword,
  });
}
```

### 3. Small Functions

Functions should be small, typically under 20 lines.

```typescript
// ❌ Bad - Too long
function processOrder(order: Order) {
  // 100+ lines of validation, calculation, payment, notification...
}

// ✅ Good - Small, focused functions
function processOrder(order: Order): OrderResult {
  validateOrder(order);
  const total = calculateTotal(order);
  const payment = processPayment(order, total);
  sendConfirmation(order, payment);
  return createOrderResult(order, payment);
}
```

### 4. Avoid Side Effects

Functions should be predictable without hidden state changes.

```typescript
// ❌ Bad - Hidden side effect
let taxRate = 0.1;

function calculateTotal(price: number): number {
  taxRate = 0.15; // Side effect!
  return price * (1 + taxRate);
}

// ✅ Good - Pure function
function calculateTotal(price: number, taxRate: number): number {
  return price * (1 + taxRate);
}
```

### 5. Don't Repeat Yourself (DRY)

Abstract common functionality.

```typescript
// ❌ Repeated logic
function formatUserName(user: User): string {
  return `${user.firstName} ${user.lastName}`.trim();
}

function formatAdminName(admin: Admin): string {
  return `${admin.firstName} ${admin.lastName}`.trim();
}

// ✅ Extract common logic
interface Named {
  firstName: string;
  lastName: string;
}

function formatFullName(entity: Named): string {
  return `${entity.firstName} ${entity.lastName}`.trim();
}
```

### 6. Prefer Composition Over Inheritance

Build complex behavior from simple pieces.

```typescript
// ❌ Deep inheritance hierarchy
class Animal {}
class Mammal extends Animal {}
class Dog extends Mammal {}
class FlyingMammal extends Mammal {}
class Bat extends FlyingMammal {}

// ✅ Composition
interface CanWalk {
  walk(): void;
}

interface CanFly {
  fly(): void;
}

interface CanSwim {
  swim(): void;
}

class Duck implements CanWalk, CanFly, CanSwim {
  constructor(
    private walker: Walker,
    private flyer: Flyer,
    private swimmer: Swimmer
  ) {}

  walk() { this.walker.walk(); }
  fly() { this.flyer.fly(); }
  swim() { this.swimmer.swim(); }
}
```

### 7. Fail Fast

Validate early and report errors immediately.

```typescript
// ❌ Bad - Late validation
function processPayment(amount: number, card: CreditCard) {
  // ... 50 lines of processing
  if (amount <= 0) {
    throw new Error('Invalid amount'); // Too late!
  }
  // ... more processing
}

// ✅ Good - Early validation
function processPayment(amount: number, card: CreditCard) {
  if (amount <= 0) {
    throw new InvalidAmountError('Amount must be positive');
  }
  if (!card.isValid()) {
    throw new InvalidCardError('Card is invalid or expired');
  }
  // ... processing with validated inputs
}
```

### 8. Use Meaningful Error Handling

Provide context with errors.

```typescript
// ❌ Bad - Generic error
function divide(a: number, b: number): number {
  if (b === 0) {
    throw new Error('Error');
  }
  return a / b;
}

// ✅ Good - Specific errors with context
class DivisionByZeroError extends Error {
  constructor(dividend: number) {
    super(`Cannot divide ${dividend} by zero`);
    this.name = 'DivisionByZeroError';
  }
}

function divide(a: number, b: number): number {
  if (b === 0) {
    throw new DivisionByZeroError(a);
  }
  return a / b;
}
```

### 9. Keep It Simple (KISS)

Choose simplicity over cleverness.

```typescript
// ❌ Over-engineered
class UserNameFormatterFactory {
  createFormatter(strategy: FormattingStrategy): Formatter {
    return new FormatterImpl(strategy);
  }
}

// ✅ Simple solution
function formatUserName(user: User): string {
  return `${user.firstName} ${user.lastName}`;
}
```

### 10. You Aren't Gonna Need It (YAGNI)

Don't build features before they're needed.

```typescript
// ❌ Premature abstraction
interface PaymentProcessor {
  process(payment: Payment): Promise<Result>;
  refund(payment: Payment): Promise<Result>;
  void(payment: Payment): Promise<Result>;
  recurring(payment: Payment): Promise<Result>;
  batch(payments: Payment[]): Promise<Result[]>;
  // 10 more methods that aren't needed yet
}

// ✅ Build what you need now
interface PaymentProcessor {
  process(payment: Payment): Promise<Result>;
}
// Add methods when requirements demand them
```

## Code Organization

### Single Level of Abstraction

Each function should operate at one level of abstraction.

```typescript
// ❌ Mixed abstraction levels
function processOrder(order: Order) {
  // High level
  validateOrder(order);
  
  // Low level - wrong abstraction
  let total = 0;
  for (const item of order.items) {
    total += item.price * item.quantity;
  }
  
  // High level again
  await chargeCustomer(order.customer, total);
}

// ✅ Consistent abstraction
function processOrder(order: Order) {
  validateOrder(order);
  const total = calculateTotal(order);
  await chargeCustomer(order.customer, total);
}

function calculateTotal(order: Order): number {
  return order.items.reduce(
    (sum, item) => sum + item.price * item.quantity,
    0
  );
}
```

### Command Query Separation

Functions should either do something OR return something, not both.

```typescript
// ❌ Bad - Does both
function getAndIncrementCounter(): number {
  const value = counter;
  counter++;
  return value;
}

// ✅ Good - Separated
function getCounter(): number {
  return counter;
}

function incrementCounter(): void {
  counter++;
}
```

## Clean Code Checklist

### For Functions
- [ ] Does one thing
- [ ] Less than 20 lines
- [ ] Clear, intention-revealing name
- [ ] Few parameters (ideally ≤ 3)
- [ ] No side effects
- [ ] Single level of abstraction

### For Classes
- [ ] Single responsibility
- [ ] Cohesive (methods use most fields)
- [ ] Small public interface
- [ ] Encapsulated implementation

### For Files
- [ ] Less than 300 lines
- [ ] Related code grouped together
- [ ] Clear, descriptive filename
- [ ] Proper organization (imports, exports)

### For Names
- [ ] Reveals intent
- [ ] Searchable
- [ ] Pronounceable
- [ ] Follows conventions

## Anti-Patterns to Avoid

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| God Class | Too many responsibilities | Split into smaller classes |
| Long Method | Hard to understand | Extract methods |
| Long Parameter List | Hard to call | Use parameter objects |
| Feature Envy | Uses others' data | Move method to data |
| Primitive Obsession | Lost semantics | Create value objects |
| Duplicate Code | Maintenance burden | Extract and reuse |
| Dead Code | Confusion | Delete it |
| Magic Numbers | No context | Use named constants |
