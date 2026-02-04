---
name: refactoring-techniques
description: Systematic refactoring techniques and patterns
category: code-quality/refactoring
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Refactoring Techniques

## Overview

Refactoring is the process of restructuring existing code without changing its external behavior. These techniques help improve code quality systematically.

## Composing Methods

### Extract Method

Transform code fragments into well-named methods.

```typescript
// Before
function printOwing(invoice: Invoice) {
  let outstanding = 0;

  console.log('***********************');
  console.log('**** Customer Owes ****');
  console.log('***********************');

  for (const order of invoice.orders) {
    outstanding += order.amount;
  }

  console.log(`name: ${invoice.customer}`);
  console.log(`amount: ${outstanding}`);
}

// After
function printOwing(invoice: Invoice) {
  printBanner();
  const outstanding = calculateOutstanding(invoice);
  printDetails(invoice, outstanding);
}

function printBanner(): void {
  console.log('***********************');
  console.log('**** Customer Owes ****');
  console.log('***********************');
}

function calculateOutstanding(invoice: Invoice): number {
  return invoice.orders.reduce((sum, order) => sum + order.amount, 0);
}

function printDetails(invoice: Invoice, outstanding: number): void {
  console.log(`name: ${invoice.customer}`);
  console.log(`amount: ${outstanding}`);
}
```

### Inline Method

Replace method call with method body when it's clearer.

```typescript
// Before
function getRating(driver: Driver): number {
  return moreThanFiveLateDeliveries(driver) ? 2 : 1;
}

function moreThanFiveLateDeliveries(driver: Driver): boolean {
  return driver.numberOfLateDeliveries > 5;
}

// After
function getRating(driver: Driver): number {
  return driver.numberOfLateDeliveries > 5 ? 2 : 1;
}
```

### Replace Temp with Query

Replace temporary variable with method call.

```typescript
// Before
function calculateTotal(order: Order): number {
  const basePrice = order.quantity * order.itemPrice;
  if (basePrice > 1000) {
    return basePrice * 0.95;
  }
  return basePrice * 0.98;
}

// After
function calculateTotal(order: Order): number {
  if (basePrice(order) > 1000) {
    return basePrice(order) * 0.95;
  }
  return basePrice(order) * 0.98;
}

function basePrice(order: Order): number {
  return order.quantity * order.itemPrice;
}
```

## Moving Features

### Move Method

Move method to class that uses it most.

```typescript
// Before
class Account {
  type: AccountType;
  daysOverdrawn: number;

  overdraftCharge(): number {
    if (this.type.isPremium) {
      const baseCharge = 10;
      if (this.daysOverdrawn <= 7) return baseCharge;
      return baseCharge + (this.daysOverdrawn - 7) * 0.85;
    }
    return this.daysOverdrawn * 1.75;
  }
}

// After
class AccountType {
  isPremium: boolean;

  overdraftCharge(daysOverdrawn: number): number {
    if (this.isPremium) {
      const baseCharge = 10;
      if (daysOverdrawn <= 7) return baseCharge;
      return baseCharge + (daysOverdrawn - 7) * 0.85;
    }
    return daysOverdrawn * 1.75;
  }
}

class Account {
  type: AccountType;
  daysOverdrawn: number;

  overdraftCharge(): number {
    return this.type.overdraftCharge(this.daysOverdrawn);
  }
}
```

### Move Field

Move field to class that uses it more.

```typescript
// Before
class Customer {
  name: string;
  discountRate: number;
  contract: CustomerContract;
}

class CustomerContract {
  startDate: Date;
}

// After (discount rate used more in contract calculations)
class Customer {
  name: string;
  contract: CustomerContract;

  get discountRate(): number {
    return this.contract.discountRate;
  }
}

class CustomerContract {
  startDate: Date;
  discountRate: number;
}
```

## Organizing Data

### Replace Data Value with Object

Replace primitive with rich object.

```typescript
// Before
class Order {
  customer: string; // Just a name
}

// After
class Order {
  customer: Customer;
}

class Customer {
  constructor(
    public readonly id: string,
    public readonly name: string,
    public readonly email: string
  ) {}

  get displayName(): string {
    return this.name || this.email;
  }
}
```

### Replace Array with Object

Replace array with object for mixed data.

```typescript
// Before
const row = ['Liverpool', 15, 8]; // [team, wins, losses]

// After
interface TeamRecord {
  team: string;
  wins: number;
  losses: number;
}

const record: TeamRecord = {
  team: 'Liverpool',
  wins: 15,
  losses: 8,
};
```

### Encapsulate Field

Make field private and provide accessors.

```typescript
// Before
class Person {
  name: string;
}

// After
class Person {
  private _name: string;

  get name(): string {
    return this._name;
  }

  set name(value: string) {
    if (!value.trim()) {
      throw new Error('Name cannot be empty');
    }
    this._name = value.trim();
  }
}
```

## Simplifying Conditionals

### Decompose Conditional

Extract complex conditions into methods.

```typescript
// Before
function getCharge(date: Date, quantity: number): number {
  if (date.getMonth() >= 6 && date.getMonth() <= 8) {
    return quantity * summerRate + summerServiceCharge;
  }
  return quantity * winterRate + winterServiceCharge;
}

// After
function getCharge(date: Date, quantity: number): number {
  if (isSummer(date)) {
    return summerCharge(quantity);
  }
  return winterCharge(quantity);
}

function isSummer(date: Date): boolean {
  return date.getMonth() >= 6 && date.getMonth() <= 8;
}

function summerCharge(quantity: number): number {
  return quantity * summerRate + summerServiceCharge;
}

function winterCharge(quantity: number): number {
  return quantity * winterRate + winterServiceCharge;
}
```

### Replace Nested Conditionals with Guard Clauses

Use early returns instead of deep nesting.

```typescript
// Before
function getPayAmount(employee: Employee): number {
  let result: number;
  if (employee.isSeparated) {
    result = separatedAmount();
  } else {
    if (employee.isRetired) {
      result = retiredAmount();
    } else {
      result = normalPayAmount();
    }
  }
  return result;
}

// After
function getPayAmount(employee: Employee): number {
  if (employee.isSeparated) return separatedAmount();
  if (employee.isRetired) return retiredAmount();
  return normalPayAmount();
}
```

### Replace Conditional with Polymorphism

Replace switch/if with polymorphic behavior.

```typescript
// Before
function getSpeed(bird: Bird): number {
  switch (bird.type) {
    case 'European':
      return 35;
    case 'African':
      return 40 - 2 * bird.numberOfCoconuts;
    case 'Norwegian Blue':
      return bird.isNailed ? 0 : 10 + bird.voltage / 10;
    default:
      throw new Error('Unknown bird type');
  }
}

// After
abstract class Bird {
  abstract getSpeed(): number;
}

class EuropeanSwallow extends Bird {
  getSpeed(): number {
    return 35;
  }
}

class AfricanSwallow extends Bird {
  constructor(private numberOfCoconuts: number) {
    super();
  }

  getSpeed(): number {
    return 40 - 2 * this.numberOfCoconuts;
  }
}

class NorwegianBlueParrot extends Bird {
  constructor(
    private isNailed: boolean,
    private voltage: number
  ) {
    super();
  }

  getSpeed(): number {
    return this.isNailed ? 0 : 10 + this.voltage / 10;
  }
}
```

## Making Method Calls Simpler

### Rename Method

Give methods intention-revealing names.

```typescript
// Before
function calc(a: number, b: number): number {}

// After
function calculateOrderTotal(subtotal: number, taxRate: number): number {}
```

### Introduce Parameter Object

Group related parameters.

```typescript
// Before
function amountInvoiced(start: Date, end: Date): number {}
function amountReceived(start: Date, end: Date): number {}
function amountOverdue(start: Date, end: Date): number {}

// After
class DateRange {
  constructor(
    public readonly start: Date,
    public readonly end: Date
  ) {}

  includes(date: Date): boolean {
    return date >= this.start && date <= this.end;
  }
}

function amountInvoiced(range: DateRange): number {}
function amountReceived(range: DateRange): number {}
function amountOverdue(range: DateRange): number {}
```

### Replace Parameter with Method

Remove parameter by calling method internally.

```typescript
// Before
const basePrice = quantity * itemPrice;
const discount = getDiscount(basePrice);
const finalPrice = applyDiscount(basePrice, discount);

// After
const finalPrice = applyDiscount(quantity * itemPrice);

function applyDiscount(basePrice: number): number {
  const discount = getDiscount(basePrice);
  return basePrice - discount;
}
```

## Refactoring Workflow

1. **Ensure tests pass** before starting
2. **Make small changes** - one refactoring at a time
3. **Run tests** after each change
4. **Commit frequently** - easy to revert
5. **Review the result** - is it actually better?

## Quick Reference

| Technique | When to Use |
|-----------|-------------|
| Extract Method | Long method, code comments |
| Move Method | Feature envy |
| Replace Temp with Query | Temp used multiple times |
| Decompose Conditional | Complex condition |
| Guard Clauses | Nested conditionals |
| Parameter Object | Data clumps in parameters |
| Replace Conditional with Polymorphism | Switch on type |
| Encapsulate Field | Direct field access |
