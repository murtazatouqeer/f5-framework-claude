---
name: extract-method
description: Extract Method refactoring technique in detail
category: code-quality/refactoring
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Extract Method

## Overview

Extract Method is the most common refactoring technique. It involves taking a code fragment and turning it into a method with a name that explains its purpose.

## When to Extract

### Signs You Need Extract Method

1. **Long methods** (>20 lines)
2. **Comments explaining what code does**
3. **Repeated code blocks**
4. **Deeply nested conditionals**
5. **Code at different abstraction levels**

## How to Extract

### Basic Steps

1. Create new method with intention-revealing name
2. Copy extracted code to new method
3. Replace original code with method call
4. Handle variables (parameters and return values)
5. Run tests

### Example: Basic Extraction

```typescript
// Before
function printInvoice(invoice: Invoice): void {
  console.log('========================');
  console.log('====== INVOICE =========');
  console.log('========================');

  let total = 0;
  for (const item of invoice.items) {
    console.log(`${item.name}: $${item.price}`);
    total += item.price;
  }

  console.log('------------------------');
  console.log(`Total: $${total}`);
  console.log('========================');
}

// After
function printInvoice(invoice: Invoice): void {
  printHeader();
  const total = printLineItems(invoice.items);
  printFooter(total);
}

function printHeader(): void {
  console.log('========================');
  console.log('====== INVOICE =========');
  console.log('========================');
}

function printLineItems(items: InvoiceItem[]): number {
  let total = 0;
  for (const item of items) {
    console.log(`${item.name}: $${item.price}`);
    total += item.price;
  }
  return total;
}

function printFooter(total: number): void {
  console.log('------------------------');
  console.log(`Total: $${total}`);
  console.log('========================');
}
```

## Handling Variables

### No Variables

Simplest case - just move the code.

```typescript
// Before
function process() {
  // Step 1
  console.log('Starting...');
  console.log('Processing...');
  console.log('Done!');
  // Step 2...
}

// After
function process() {
  logProgress();
  // Step 2...
}

function logProgress(): void {
  console.log('Starting...');
  console.log('Processing...');
  console.log('Done!');
}
```

### Local Variables (Read Only)

Pass as parameters.

```typescript
// Before
function calculateTotal(order: Order) {
  const items = order.items;
  const customer = order.customer;
  
  // Calculate base total
  let baseTotal = 0;
  for (const item of items) {
    baseTotal += item.price * item.quantity;
  }
  
  // Apply customer discount
  const discount = customer.discount;
  return baseTotal * (1 - discount);
}

// After
function calculateTotal(order: Order): number {
  const baseTotal = calculateBaseTotal(order.items);
  return applyDiscount(baseTotal, order.customer.discount);
}

function calculateBaseTotal(items: OrderItem[]): number {
  return items.reduce((sum, item) => sum + item.price * item.quantity, 0);
}

function applyDiscount(amount: number, discountRate: number): number {
  return amount * (1 - discountRate);
}
```

### Local Variables (Modified)

Return modified values.

```typescript
// Before
function processOrder(order: Order) {
  let total = 0;
  let itemCount = 0;
  
  for (const item of order.items) {
    total += item.price;
    itemCount++;
  }
  
  console.log(`Items: ${itemCount}, Total: ${total}`);
}

// After - Single modified variable
function processOrder(order: Order) {
  const { total, count } = calculateOrderMetrics(order.items);
  console.log(`Items: ${count}, Total: ${total}`);
}

function calculateOrderMetrics(items: OrderItem[]): { total: number; count: number } {
  let total = 0;
  let count = 0;
  
  for (const item of items) {
    total += item.price;
    count++;
  }
  
  return { total, count };
}

// Or using reduce
function calculateOrderMetrics(items: OrderItem[]): { total: number; count: number } {
  return items.reduce(
    (acc, item) => ({
      total: acc.total + item.price,
      count: acc.count + 1,
    }),
    { total: 0, count: 0 }
  );
}
```

### Multiple Modified Variables

Consider extracting a class instead.

```typescript
// Before - Complex state manipulation
function processTransaction(transaction: Transaction) {
  let balance = transaction.account.balance;
  let pendingAmount = 0;
  let completedCount = 0;
  let failedCount = 0;
  
  for (const item of transaction.items) {
    if (item.status === 'pending') {
      pendingAmount += item.amount;
    } else if (item.status === 'completed') {
      balance -= item.amount;
      completedCount++;
    } else {
      failedCount++;
    }
  }
  
  return { balance, pendingAmount, completedCount, failedCount };
}

// After - Extract class
class TransactionProcessor {
  private balance: number;
  private pendingAmount = 0;
  private completedCount = 0;
  private failedCount = 0;

  constructor(initialBalance: number) {
    this.balance = initialBalance;
  }

  process(items: TransactionItem[]): TransactionResult {
    for (const item of items) {
      this.processItem(item);
    }
    return this.getResult();
  }

  private processItem(item: TransactionItem): void {
    switch (item.status) {
      case 'pending':
        this.pendingAmount += item.amount;
        break;
      case 'completed':
        this.balance -= item.amount;
        this.completedCount++;
        break;
      default:
        this.failedCount++;
    }
  }

  private getResult(): TransactionResult {
    return {
      balance: this.balance,
      pendingAmount: this.pendingAmount,
      completedCount: this.completedCount,
      failedCount: this.failedCount,
    };
  }
}
```

## Naming Extracted Methods

### Good Names

- **Describe intent**, not implementation
- **Use verbs** for actions
- **Be specific** but concise

```typescript
// ❌ Bad names
function doStuff() {}
function handleData() {}
function process() {}
function calc() {}

// ✅ Good names
function validateUserCredentials() {}
function calculateOrderDiscount() {}
function sendPasswordResetEmail() {}
function formatCurrencyForDisplay() {}
```

### Name by Abstraction Level

```typescript
// High level (what)
function processOrder(order: Order): OrderResult {
  validateOrder(order);
  const total = calculateTotal(order);
  const payment = chargeCustomer(order.customer, total);
  return createOrderResult(order, payment);
}

// Medium level (how - one level down)
function calculateTotal(order: Order): Money {
  const subtotal = sumLineItems(order.items);
  const tax = calculateTax(subtotal, order.taxRate);
  const shipping = calculateShipping(order);
  return subtotal.add(tax).add(shipping);
}

// Low level (implementation details)
function sumLineItems(items: OrderItem[]): Money {
  return items.reduce(
    (sum, item) => sum.add(item.price.multiply(item.quantity)),
    Money.zero()
  );
}
```

## Common Patterns

### Extract Validation

```typescript
// Before
function createUser(data: UserInput): User {
  if (!data.email) throw new Error('Email required');
  if (!data.email.includes('@')) throw new Error('Invalid email');
  if (!data.password) throw new Error('Password required');
  if (data.password.length < 8) throw new Error('Password too short');
  // ... create user
}

// After
function createUser(data: UserInput): User {
  validateUserInput(data);
  // ... create user
}

function validateUserInput(data: UserInput): void {
  validateEmail(data.email);
  validatePassword(data.password);
}

function validateEmail(email: string | undefined): void {
  if (!email) throw new ValidationError('Email required');
  if (!email.includes('@')) throw new ValidationError('Invalid email format');
}

function validatePassword(password: string | undefined): void {
  if (!password) throw new ValidationError('Password required');
  if (password.length < 8) throw new ValidationError('Password must be at least 8 characters');
}
```

### Extract Transformation

```typescript
// Before
function displayUsers(users: User[]): string {
  let result = '<ul>';
  for (const user of users) {
    result += `<li>${user.firstName} ${user.lastName} (${user.email})</li>`;
  }
  result += '</ul>';
  return result;
}

// After
function displayUsers(users: User[]): string {
  const items = users.map(formatUserListItem).join('');
  return wrapInList(items);
}

function formatUserListItem(user: User): string {
  return `<li>${formatUserName(user)} (${user.email})</li>`;
}

function formatUserName(user: User): string {
  return `${user.firstName} ${user.lastName}`;
}

function wrapInList(content: string): string {
  return `<ul>${content}</ul>`;
}
```

## Anti-Patterns to Avoid

```typescript
// ❌ Don't extract single-line methods (usually)
function add(a: number, b: number): number {
  return a + b;
}

// ❌ Don't create "util" dumping grounds
class StringUtils {
  static trim(s: string) {}
  static pad(s: string) {}
  static format(s: string) {}
  // 50 more unrelated methods
}

// ❌ Don't pass too many parameters
function extracted(a: string, b: number, c: Date, d: boolean, e: User): void {}
// → Consider a parameter object or keeping code inline

// ❌ Don't extract if it makes code less clear
// Sometimes inline is clearer than indirection
```
