---
name: solid-principles
description: SOLID principles for object-oriented design
category: architecture/principles
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# SOLID Principles

## Overview

SOLID is an acronym for five design principles that make software
more understandable, flexible, and maintainable.

## S - Single Responsibility Principle

> A class should have only one reason to change.

### Bad Example
```typescript
// ❌ Class has multiple responsibilities
class User {
  constructor(
    public name: string,
    public email: string
  ) {}

  // User data management
  save(): void {
    // Save to database
  }

  // Email functionality
  sendWelcomeEmail(): void {
    // Send email
  }

  // Report generation
  generateReport(): string {
    // Generate user report
  }
}
```

### Good Example
```typescript
// ✅ Each class has single responsibility
class User {
  constructor(
    public readonly id: string,
    public name: string,
    public email: string
  ) {}
}

class UserRepository {
  async save(user: User): Promise<void> {
    // Database operations only
  }

  async findById(id: string): Promise<User | null> {
    // Query operations
  }
}

class UserEmailService {
  async sendWelcomeEmail(user: User): Promise<void> {
    // Email operations only
  }
}

class UserReportGenerator {
  generate(user: User): string {
    // Report generation only
  }
}
```

## O - Open/Closed Principle

> Software entities should be open for extension but closed for modification.

### Bad Example
```typescript
// ❌ Must modify class to add new payment types
class PaymentProcessor {
  process(type: string, amount: number): void {
    if (type === 'credit_card') {
      // Process credit card
    } else if (type === 'paypal') {
      // Process PayPal
    } else if (type === 'stripe') {
      // Process Stripe - had to modify class!
    }
  }
}
```

### Good Example
```typescript
// ✅ Open for extension via new implementations
interface PaymentMethod {
  process(amount: number): Promise<PaymentResult>;
}

class CreditCardPayment implements PaymentMethod {
  async process(amount: number): Promise<PaymentResult> {
    // Credit card logic
  }
}

class PayPalPayment implements PaymentMethod {
  async process(amount: number): Promise<PaymentResult> {
    // PayPal logic
  }
}

// Adding new payment type doesn't modify existing code
class StripePayment implements PaymentMethod {
  async process(amount: number): Promise<PaymentResult> {
    // Stripe logic
  }
}

class PaymentProcessor {
  constructor(private paymentMethod: PaymentMethod) {}

  async process(amount: number): Promise<PaymentResult> {
    return this.paymentMethod.process(amount);
  }
}
```

## L - Liskov Substitution Principle

> Objects of a superclass should be replaceable with objects of subclasses
> without breaking the application.

### Bad Example
```typescript
// ❌ Square violates LSP - can't substitute for Rectangle
class Rectangle {
  constructor(
    protected width: number,
    protected height: number
  ) {}

  setWidth(width: number): void {
    this.width = width;
  }

  setHeight(height: number): void {
    this.height = height;
  }

  getArea(): number {
    return this.width * this.height;
  }
}

class Square extends Rectangle {
  setWidth(width: number): void {
    this.width = width;
    this.height = width; // Violates expected behavior!
  }

  setHeight(height: number): void {
    this.width = height;
    this.height = height; // Violates expected behavior!
  }
}

// This breaks with Square
function resizeRectangle(rect: Rectangle): void {
  rect.setWidth(10);
  rect.setHeight(5);
  console.log(rect.getArea()); // Expected: 50, Square gives: 25
}
```

### Good Example
```typescript
// ✅ Use composition/interfaces instead
interface Shape {
  getArea(): number;
}

class Rectangle implements Shape {
  constructor(
    private width: number,
    private height: number
  ) {}

  getArea(): number {
    return this.width * this.height;
  }
}

class Square implements Shape {
  constructor(private side: number) {}

  getArea(): number {
    return this.side * this.side;
  }
}
```

## I - Interface Segregation Principle

> Clients should not be forced to depend on interfaces they don't use.

### Bad Example
```typescript
// ❌ Fat interface forces unnecessary implementations
interface Worker {
  work(): void;
  eat(): void;
  sleep(): void;
  attendMeeting(): void;
  writeCode(): void;
}

class Robot implements Worker {
  work(): void { /* OK */ }
  eat(): void { throw new Error('Robots dont eat'); } // Forced!
  sleep(): void { throw new Error('Robots dont sleep'); } // Forced!
  attendMeeting(): void { /* OK */ }
  writeCode(): void { /* OK */ }
}
```

### Good Example
```typescript
// ✅ Segregated interfaces
interface Workable {
  work(): void;
}

interface Eatable {
  eat(): void;
}

interface Sleepable {
  sleep(): void;
}

interface Programmable {
  writeCode(): void;
}

class Human implements Workable, Eatable, Sleepable, Programmable {
  work(): void { /* ... */ }
  eat(): void { /* ... */ }
  sleep(): void { /* ... */ }
  writeCode(): void { /* ... */ }
}

class Robot implements Workable, Programmable {
  work(): void { /* ... */ }
  writeCode(): void { /* ... */ }
  // No need for eat() or sleep()
}
```

## D - Dependency Inversion Principle

> High-level modules should not depend on low-level modules.
> Both should depend on abstractions.

### Bad Example
```typescript
// ❌ High-level depends on low-level
class MySQLDatabase {
  save(data: any): void {
    // MySQL specific
  }
}

class UserService {
  private database = new MySQLDatabase(); // Tight coupling!

  createUser(data: UserData): void {
    this.database.save(data);
  }
}
```

### Good Example
```typescript
// ✅ Both depend on abstraction
interface Database {
  save(data: any): Promise<void>;
  find(query: any): Promise<any>;
}

class MySQLDatabase implements Database {
  async save(data: any): Promise<void> { /* ... */ }
  async find(query: any): Promise<any> { /* ... */ }
}

class PostgreSQLDatabase implements Database {
  async save(data: any): Promise<void> { /* ... */ }
  async find(query: any): Promise<any> { /* ... */ }
}

class UserService {
  constructor(private database: Database) {} // Injected!

  async createUser(data: UserData): Promise<void> {
    await this.database.save(data);
  }
}

// Easy to switch implementations
const userService = new UserService(new PostgreSQLDatabase());
```

## Summary Table

| Principle | Focus | Benefit |
|-----------|-------|---------|
| SRP | One responsibility per class | Easier maintenance |
| OCP | Extend without modifying | Reduced regression risk |
| LSP | Substitutable subtypes | Reliable polymorphism |
| ISP | Focused interfaces | Cleaner dependencies |
| DIP | Depend on abstractions | Flexible, testable code |

## Application Guidelines

### When to Apply
- New class/module design
- Refactoring legacy code
- Code review checklist
- Architecture decisions

### Common Violations
- God classes (SRP)
- Switch statements on types (OCP)
- Throwing NotImplementedException (LSP, ISP)
- Direct instantiation of dependencies (DIP)

### Testing Benefits
- SRP: Focused unit tests
- OCP: Test extensions independently
- LSP: Polymorphic test cases work
- ISP: Mock only what's needed
- DIP: Easy dependency mocking
