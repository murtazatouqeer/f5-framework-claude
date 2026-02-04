---
name: when-to-refactor
description: Decision framework for when to refactor code
category: code-quality/refactoring
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# When to Refactor

## Overview

Refactoring should be a deliberate decision, not an impulse. This guide helps you decide when refactoring adds value and when it doesn't.

## The Rule of Three

> "The first time you do something, just do it. The second time you do something similar, wince at the duplication but do it anyway. The third time you do something similar, refactor."

```typescript
// First time - just write it
function processUserOrder(order: Order) {
  // validation inline
}

// Second time - note the duplication
function processGuestOrder(order: Order) {
  // similar validation inline (wince)
}

// Third time - refactor!
function validateOrder(order: Order): ValidationResult {
  // extracted common validation
}
```

## Refactoring Triggers

### Preparatory Refactoring

Refactor **before** adding new features to make the change easier.

```typescript
// Before adding a new payment method:
// Current code handles payments in a switch statement

// ❌ Adding another case makes it worse
switch (paymentType) {
  case 'card': // existing
  case 'bank': // existing
  case 'crypto': // new - now switch is even longer
}

// ✅ Refactor first, then add
interface PaymentProcessor {
  process(payment: Payment): Promise<PaymentResult>;
}

// Now adding crypto is trivial
class CryptoPaymentProcessor implements PaymentProcessor {
  async process(payment: Payment): Promise<PaymentResult> {
    // implementation
  }
}
```

### Comprehension Refactoring

Refactor **while** trying to understand confusing code.

```typescript
// You're reading this and don't understand it
function calc(d: any[], f: number) {
  return d.reduce((a, x) => a + (x.p * x.q * (1 - f)), 0);
}

// Refactor for clarity
function calculateDiscountedTotal(items: OrderItem[], discountRate: number): number {
  return items.reduce((total, item) => {
    const itemTotal = item.price * item.quantity;
    const discountedAmount = itemTotal * (1 - discountRate);
    return total + discountedAmount;
  }, 0);
}
```

### Litter-Pickup Refactoring

Small improvements while working on other tasks (Boy Scout Rule).

```typescript
// While fixing a bug, you notice:
function processData(data) { // No types!
  var result = []; // var instead of const
  for (var i = 0; i < data.length; i++) { // Could use for-of
    result.push(data[i].value)
  }
  return result
}

// Quick cleanup
function processData(data: DataItem[]): string[] {
  return data.map(item => item.value);
}
```

### Code Review Refactoring

Refactor based on review feedback.

```typescript
// Reviewer comment: "This function does too much"
function handleUserAction(action: Action) {
  // 50 lines of validation
  // 30 lines of processing
  // 20 lines of notification
}

// Refactored based on feedback
function handleUserAction(action: Action) {
  const validatedAction = validateAction(action);
  const result = processAction(validatedAction);
  await notifyCompletion(result);
}
```

## When NOT to Refactor

### Deadline Pressure

```typescript
// ❌ Don't refactor during crunch time
// Ship first, create technical debt ticket, refactor later

// Create a ticket:
// TECH-123: Refactor payment processing
// - Extract payment strategy pattern
// - Estimated: 4 hours
// - Priority: After release
```

### Code That Works and Rarely Changes

```typescript
// ❌ Don't refactor stable, working code
// This authentication code hasn't changed in 2 years
// It's ugly but tested and works
// Leave it alone unless you need to modify it
```

### Code Scheduled for Replacement

```typescript
// ❌ Don't polish code being deleted
// We're migrating to a new system next quarter
// Don't refactor the legacy code
```

### When You Don't Understand the Domain

```typescript
// ❌ Don't refactor financial calculations you don't understand
function calculateCompoundInterest(p: number, r: number, n: number, t: number) {
  return p * Math.pow(1 + r / n, n * t);
}
// This looks simple but may have domain-specific reasons
// Understand the business rules before changing
```

## Refactoring Decision Matrix

| Situation | Refactor? | Why |
|-----------|-----------|-----|
| Adding feature to messy code | ✅ Yes | Makes change easier |
| Code review feedback | ✅ Yes | Team alignment |
| Third duplication | ✅ Yes | Rule of three |
| Can't understand code | ✅ Yes | Comprehension |
| Small cleanup while passing | ✅ Yes | Boy Scout Rule |
| Deadline in 2 days | ❌ No | Ship first |
| Legacy code being replaced | ❌ No | Waste of effort |
| Unfamiliar domain logic | ❌ No | Risk of breaking |
| Working, stable code | ❌ No | If it ain't broke... |

## Safe Refactoring Checklist

Before refactoring:

- [ ] Tests exist and pass
- [ ] You understand what the code does
- [ ] You have time to complete the refactoring
- [ ] Changes can be reviewed before merge
- [ ] Rollback plan exists (git)

During refactoring:

- [ ] Make small, incremental changes
- [ ] Run tests after each change
- [ ] Commit frequently
- [ ] Don't mix refactoring with feature changes

After refactoring:

- [ ] All tests still pass
- [ ] Behavior hasn't changed
- [ ] Code is clearer
- [ ] Get code review

## Refactoring Scope Guidelines

### Micro Refactoring (Minutes)

- Rename variable
- Extract variable
- Inline variable
- Change function signature

```typescript
// 2 minutes
const t = price * qty; // → const totalPrice = price * quantity;
```

### Small Refactoring (< 1 Hour)

- Extract method
- Move method
- Replace conditional with guard clause

```typescript
// 30 minutes
// Extract validation into separate functions
```

### Medium Refactoring (Hours)

- Extract class
- Replace type code with polymorphism
- Introduce parameter object

```typescript
// 2-4 hours
// Convert switch statement to strategy pattern
```

### Large Refactoring (Days)

- Introduce design pattern
- Restructure module boundaries
- Replace algorithm

```typescript
// 2-5 days
// Migrate from monolith service to domain modules
// Do this incrementally!
```

## Incremental Large Refactoring

### Branch by Abstraction

```typescript
// Step 1: Create abstraction
interface NotificationService {
  send(notification: Notification): Promise<void>;
}

// Step 2: Implement old way
class LegacyNotificationService implements NotificationService {
  async send(notification: Notification): Promise<void> {
    // existing implementation
  }
}

// Step 3: Use abstraction everywhere
const notificationService: NotificationService = new LegacyNotificationService();

// Step 4: Create new implementation
class ModernNotificationService implements NotificationService {
  async send(notification: Notification): Promise<void> {
    // new implementation
  }
}

// Step 5: Switch to new (can be gradual with feature flags)
const notificationService: NotificationService = new ModernNotificationService();

// Step 6: Remove old implementation
```

## Measuring Refactoring Success

| Metric | Before | After | Improved? |
|--------|--------|-------|-----------|
| Cyclomatic complexity | 25 | 8 | ✅ |
| Function length | 150 lines | 20 lines | ✅ |
| Test coverage | 45% | 85% | ✅ |
| Time to add feature | 3 days | 1 day | ✅ |
| Bug rate in area | 5/month | 1/month | ✅ |
