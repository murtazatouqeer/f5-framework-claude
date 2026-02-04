# Refactoring Reference

## Code Smells

### Long Method

```typescript
// ❌ Bad - Too long, does too much
async function processOrder(order: Order) {
  // Validate (10 lines) + Calculate (15 lines) + Payment (15 lines) + Notify (10 lines)
  // ... 50+ lines total
}

// ✅ Good - Extract methods
async function processOrder(order: Order): Promise<OrderResult> {
  validateOrder(order);
  const totals = calculateTotals(order);
  const finalAmount = applyDiscounts(totals, order.customer);
  const payment = await processPayment(order, finalAmount);
  await sendOrderConfirmation(order, payment);
  return { orderId: order.id, payment };
}
```

### Long Parameter List

```typescript
// ❌ Bad
function createUser(name, email, password, phone, address, city, country, role) {}

// ✅ Good - Use object parameter
interface CreateUserDTO {
  name: string;
  email: string;
  password: string;
  phone?: string;
  address?: Address;
  role?: UserRole;
}

function createUser(data: CreateUserDTO): User {}
```

### Primitive Obsession

```typescript
// ❌ Bad - Using primitives for domain concepts
function processPayment(amount: number, currency: string, cardNumber: string) {}

// ✅ Good - Use value objects
class Money {
  constructor(public readonly amount: number, public readonly currency: Currency) {
    if (amount < 0) throw new Error('Amount cannot be negative');
  }

  add(other: Money): Money {
    if (this.currency !== other.currency) throw new CurrencyMismatchError();
    return new Money(this.amount + other.amount, this.currency);
  }
}

function processPayment(amount: Money, card: CreditCard): PaymentResult {}
```

### Feature Envy

```typescript
// ❌ Bad - Method uses another object's data extensively
class OrderProcessor {
  calculateShipping(order: Order): number {
    const weight = order.items.reduce((sum, item) => sum + item.weight, 0);
    const address = order.customer.address;
    return weight * this.getRate(address.country);
  }
}

// ✅ Good - Move method to where data lives
class Order {
  calculateShipping(): Money {
    const zone = ShippingZone.forCountry(this.customer.address.country);
    return new Money(this.totalWeight * zone.rate, this.currency);
  }

  get totalWeight(): number {
    return this.items.reduce((sum, item) => sum + item.weight, 0);
  }
}
```

### God Class

```typescript
// ❌ Bad - Class does everything
class UserManager {
  createUser() {}
  sendEmail() {}
  generateReport() {}
  exportToCsv() {}
  // ... 50+ methods
}

// ✅ Good - Single responsibility
class UserService {
  async create(data: CreateUserDTO): Promise<User> {}
}

class UserEmailService {
  async sendWelcome(user: User): Promise<void> {}
}

class UserReportService {
  generateActivityReport(userId: string): Report {}
}
```

### Magic Numbers

```typescript
// ❌ Bad
if (user.age >= 18) {}
if (order.total > 100) {}
setTimeout(callback, 86400000);

// ✅ Good - Named constants
const MINIMUM_AGE = 18;
const FREE_SHIPPING_THRESHOLD = 100;
const ONE_DAY_MS = 24 * 60 * 60 * 1000;

enum UserStatus { Active = 'active', Inactive = 'inactive' }

if (user.age >= MINIMUM_AGE) {}
if (order.total > FREE_SHIPPING_THRESHOLD) {}
setTimeout(callback, ONE_DAY_MS);
```

## Refactoring Techniques

### Extract Method

```typescript
// Before
function printOwing(invoice: Invoice) {
  let outstanding = 0;
  console.log('**** Customer Owes ****');
  for (const order of invoice.orders) {
    outstanding += order.amount;
  }
  console.log(`amount: ${outstanding}`);
}

// After
function printOwing(invoice: Invoice) {
  printBanner();
  const outstanding = calculateOutstanding(invoice);
  printDetails(invoice, outstanding);
}

function printBanner(): void { console.log('**** Customer Owes ****'); }
function calculateOutstanding(invoice: Invoice): number {
  return invoice.orders.reduce((sum, order) => sum + order.amount, 0);
}
```

### Replace Nested Conditionals with Guard Clauses

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

### Decompose Conditional

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
  return isSummer(date) ? summerCharge(quantity) : winterCharge(quantity);
}

function isSummer(date: Date): boolean {
  return date.getMonth() >= 6 && date.getMonth() <= 8;
}
```

### Replace Conditional with Polymorphism

```typescript
// Before
function getSpeed(bird: Bird): number {
  switch (bird.type) {
    case 'European': return 35;
    case 'African': return 40 - 2 * bird.numberOfCoconuts;
    default: throw new Error('Unknown type');
  }
}

// After
abstract class Bird {
  abstract getSpeed(): number;
}

class EuropeanSwallow extends Bird {
  getSpeed(): number { return 35; }
}

class AfricanSwallow extends Bird {
  constructor(private numberOfCoconuts: number) { super(); }
  getSpeed(): number { return 40 - 2 * this.numberOfCoconuts; }
}
```

### Introduce Parameter Object

```typescript
// Before
function amountInvoiced(start: Date, end: Date): number {}
function amountReceived(start: Date, end: Date): number {}
function amountOverdue(start: Date, end: Date): number {}

// After
class DateRange {
  constructor(public readonly start: Date, public readonly end: Date) {}
  includes(date: Date): boolean { return date >= this.start && date <= this.end; }
}

function amountInvoiced(range: DateRange): number {}
function amountReceived(range: DateRange): number {}
function amountOverdue(range: DateRange): number {}
```

### Move Method

```typescript
// Before
class Account {
  type: AccountType;
  daysOverdrawn: number;

  overdraftCharge(): number {
    if (this.type.isPremium) {
      return this.daysOverdrawn <= 7 ? 10 : 10 + (this.daysOverdrawn - 7) * 0.85;
    }
    return this.daysOverdrawn * 1.75;
  }
}

// After
class AccountType {
  overdraftCharge(daysOverdrawn: number): number {
    if (this.isPremium) {
      return daysOverdrawn <= 7 ? 10 : 10 + (daysOverdrawn - 7) * 0.85;
    }
    return daysOverdrawn * 1.75;
  }
}

class Account {
  overdraftCharge(): number {
    return this.type.overdraftCharge(this.daysOverdrawn);
  }
}
```

### Encapsulate Field

```typescript
// Before
class Person { name: string; }

// After
class Person {
  private _name: string;

  get name(): string { return this._name; }

  set name(value: string) {
    if (!value.trim()) throw new Error('Name cannot be empty');
    this._name = value.trim();
  }
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
| Guard Clauses | Nested conditionals |
| Parameter Object | Data clumps in parameters |
| Replace Conditional | Switch on type |
| Encapsulate Field | Direct field access |
