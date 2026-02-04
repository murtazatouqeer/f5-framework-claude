# Clean Code Practices Reference

## Core Principles

### Meaningful Names

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

### Functions Should Do One Thing

```typescript
// ❌ Bad - Multiple responsibilities
async function handleUserRegistration(data: RegistrationData) {
  // Validate + Hash password + Save + Send email + Log = 50+ lines
}

// ✅ Good - Single responsibility
async function registerUser(data: RegistrationData): Promise<User> {
  validateRegistrationData(data);
  const user = await createUser(data);
  await sendWelcomeEmail(user);
  await logUserRegistration(user);
  return user;
}
```

### Small Functions

```typescript
// ✅ Good - Small, focused functions (< 20 lines each)
function processOrder(order: Order): OrderResult {
  validateOrder(order);
  const total = calculateTotal(order);
  const payment = processPayment(order, total);
  sendConfirmation(order, payment);
  return createOrderResult(order, payment);
}
```

### Avoid Side Effects

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

### DRY (Don't Repeat Yourself)

```typescript
// ❌ Repeated logic
function formatUserName(user: User): string {
  return `${user.firstName} ${user.lastName}`.trim();
}
function formatAdminName(admin: Admin): string {
  return `${admin.firstName} ${admin.lastName}`.trim();
}

// ✅ Extract common logic
interface Named { firstName: string; lastName: string; }
function formatFullName(entity: Named): string {
  return `${entity.firstName} ${entity.lastName}`.trim();
}
```

### Fail Fast

```typescript
// ❌ Bad - Late validation
function processPayment(amount: number, card: CreditCard) {
  // ... 50 lines of processing
  if (amount <= 0) throw new Error('Invalid amount'); // Too late!
}

// ✅ Good - Early validation
function processPayment(amount: number, card: CreditCard) {
  if (amount <= 0) throw new InvalidAmountError('Amount must be positive');
  if (!card.isValid()) throw new InvalidCardError('Card is invalid');
  // ... processing with validated inputs
}
```

### Meaningful Error Handling

```typescript
// ❌ Bad
if (b === 0) throw new Error('Error');

// ✅ Good
class DivisionByZeroError extends Error {
  constructor(dividend: number) {
    super(`Cannot divide ${dividend} by zero`);
    this.name = 'DivisionByZeroError';
  }
}

if (b === 0) throw new DivisionByZeroError(a);
```

### KISS (Keep It Simple)

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

### YAGNI (You Aren't Gonna Need It)

```typescript
// ❌ Premature abstraction
interface PaymentProcessor {
  process(payment: Payment): Promise<Result>;
  refund(payment: Payment): Promise<Result>;
  void(payment: Payment): Promise<Result>;
  recurring(payment: Payment): Promise<Result>;
  batch(payments: Payment[]): Promise<Result[]>;
  // 10 more methods not needed yet
}

// ✅ Build what you need now
interface PaymentProcessor {
  process(payment: Payment): Promise<Result>;
}
// Add methods when requirements demand them
```

### Command Query Separation

```typescript
// ❌ Bad - Does both
function getAndIncrementCounter(): number {
  const value = counter;
  counter++;
  return value;
}

// ✅ Good - Separated
function getCounter(): number { return counter; }
function incrementCounter(): void { counter++; }
```

## Code Review Checklist

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

### For Error Handling
- [ ] Specific error types
- [ ] Meaningful error messages
- [ ] Proper error propagation
- [ ] No swallowed exceptions

### For Tests
- [ ] Tests exist for new code
- [ ] Tests are meaningful (not just coverage)
- [ ] Edge cases covered
- [ ] Clear test names

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
| Shotgun Surgery | One change, many files | Encapsulate related changes |
| Comments Explaining Bad Code | Unclear code | Rewrite to be self-documenting |

## Single Level of Abstraction

```typescript
// ❌ Mixed abstraction levels
function processOrder(order: Order) {
  validateOrder(order); // High level

  // Low level - wrong abstraction
  let total = 0;
  for (const item of order.items) {
    total += item.price * item.quantity;
  }

  await chargeCustomer(order.customer, total); // High level
}

// ✅ Consistent abstraction
function processOrder(order: Order) {
  validateOrder(order);
  const total = calculateTotal(order);
  await chargeCustomer(order.customer, total);
}

function calculateTotal(order: Order): number {
  return order.items.reduce((sum, item) => sum + item.price * item.quantity, 0);
}
```

## Documentation Guidelines

### When to Comment
- Complex algorithms that can't be simplified
- Non-obvious business rules
- API documentation (JSDoc/TSDoc)
- Why (not what) decisions were made

### When NOT to Comment
- Obvious code that explains itself
- What the code does (should be clear from names)
- Commented-out code (delete it)
- Noise comments ("increment i")

```typescript
// ❌ Bad - Comment explains confusing code
// Check if user can access based on role and subscription
if ((user.role === 'admin' || user.subscription === 'premium') &&
    (resource.isPublic || resource.ownerId === user.id)) {}

// ✅ Good - Self-documenting code
const hasRequiredAccess = user.isAdmin || user.hasPremiumSubscription;
const canAccessResource = resource.isPublic || resource.isOwnedBy(user);
if (hasRequiredAccess && canAccessResource) {}
```
