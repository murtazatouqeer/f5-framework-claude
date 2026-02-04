---
name: function-naming
description: Best practices for function and method naming
category: code-quality/naming
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Function Naming

## Overview

Function names should clearly communicate what the function does. A well-named function acts as documentation and makes code self-explanatory.

## Core Principles

### 1. Use Verbs for Actions

```typescript
// ❌ Bad - Nouns or unclear
function user(id: string) {}
function data() {}
function order() {}
function validation(input: string) {}

// ✅ Good - Verbs describe actions
function getUser(id: string): User {}
function fetchData(): Data {}
function createOrder(items: Item[]): Order {}
function validateInput(input: string): ValidationResult {}
```

### 2. Be Specific About What It Does

```typescript
// ❌ Bad - Vague
function handleData(data: any) {}
function processUser(user: User) {}
function doSomething() {}
function execute() {}

// ✅ Good - Specific
function parseJsonResponse(data: string): ResponseData {}
function sendWelcomeEmail(user: User): Promise<void> {}
function calculateOrderTotal(order: Order): number {}
function validateCreditCard(card: CreditCard): boolean {}
```

### 3. Name by Intent, Not Implementation

```typescript
// ❌ Bad - Implementation details
function loopThroughUsers(users: User[]) {}
function sqlQueryGetUser(id: string) {}
function regexValidateEmail(email: string) {}

// ✅ Good - What it achieves
function processAllUsers(users: User[]): void {}
function findUserById(id: string): User | null {}
function isValidEmail(email: string): boolean {}
```

## Common Verb Patterns

### Data Retrieval

```typescript
// get* - Synchronous retrieval, always returns a value
function getUser(id: string): User {}
function getUserName(user: User): string {}
function getCurrentTimestamp(): number {}

// fetch* - Async HTTP request
async function fetchUser(id: string): Promise<User> {}
async function fetchOrders(): Promise<Order[]> {}
async function fetchUserProfile(): Promise<UserProfile> {}

// find* - Search that might return null/undefined
function findUserById(id: string): User | null {}
function findOrdersByStatus(status: Status): Order[] {}
function findFirstMatch(items: Item[], predicate: Predicate): Item | undefined {}

// load* - Async with side effects (caching, state)
async function loadConfiguration(): Promise<Config> {}
async function loadUserPreferences(): Promise<Preferences> {}

// query* - Database or complex search
async function queryActiveUsers(): Promise<User[]> {}
function queryOrderHistory(filters: Filters): Promise<Order[]> {}
```

### Data Modification

```typescript
// create* - Make new entity
function createUser(data: CreateUserDTO): User {}
async function createOrder(items: Item[]): Promise<Order> {}
function createPaymentIntent(amount: Money): PaymentIntent {}

// update* - Modify existing entity
function updateUser(id: string, data: UpdateUserDTO): User {}
async function updateOrderStatus(orderId: string, status: Status): Promise<void> {}

// delete* / remove* - Remove entity
function deleteUser(id: string): void {}
async function removeItemFromCart(cartId: string, itemId: string): Promise<Cart> {}

// set* - Direct assignment
function setUserName(user: User, name: string): void {}
function setConfiguration(config: Config): void {}

// add* - Add to collection
function addItemToCart(cart: Cart, item: Item): Cart {}
function addUser(users: User[], user: User): User[] {}

// save* - Persist to storage
async function saveUser(user: User): Promise<void> {}
async function saveChanges(): Promise<void> {}
```

### Validation and Checks

```typescript
// is* - Returns boolean, checks state
function isActive(user: User): boolean {}
function isValidEmail(email: string): boolean {}
function isEmpty(array: any[]): boolean {}

// has* - Returns boolean, checks possession
function hasPermission(user: User, permission: Permission): boolean {}
function hasItems(cart: Cart): boolean {}

// can* - Returns boolean, checks capability
function canEdit(user: User, document: Document): boolean {}
function canProceedToCheckout(cart: Cart): boolean {}

// should* - Returns boolean, checks policy
function shouldRetry(error: Error, attempts: number): boolean {}
function shouldShowWarning(status: Status): boolean {}

// validate* - Throws or returns result
function validateOrder(order: Order): ValidationResult {}
function validateInput(input: string): void {} // throws if invalid

// check* - Verify and possibly throw
function checkPermission(user: User, action: Action): void {}
function checkAvailability(product: Product): boolean {}

// ensure* / assert* - Guarantee or throw
function ensureAuthenticated(request: Request): User {}
function assertNotNull<T>(value: T | null): T {}
```

### Transformation

```typescript
// format* - Convert to display format
function formatCurrency(amount: number): string {}
function formatDate(date: Date): string {}
function formatPhoneNumber(phone: string): string {}

// parse* - Convert from string/external format
function parseJson<T>(json: string): T {}
function parseDate(dateString: string): Date {}
function parseQueryString(query: string): Record<string, string> {}

// convert* - Transform between types
function convertToDTO(user: User): UserDTO {}
function convertCurrency(amount: Money, toCurrency: Currency): Money {}

// transform* - Apply transformation
function transformResponse(response: Response): TransformedData {}
function transformUserData(data: RawData): User {}

// map* - Transform collection elements
function mapToUserDTO(users: User[]): UserDTO[] {}
function mapOrdersToSummary(orders: Order[]): OrderSummary[] {}

// to* - Convert to specific type
function toString(value: unknown): string {}
function toNumber(value: string): number {}
function toJson(object: unknown): string {}
```

### Event Handling

```typescript
// handle* - Process an event
function handleClick(event: MouseEvent): void {}
function handleSubmit(event: FormEvent): void {}
function handleError(error: Error): void {}

// on* - Event callback (used in props/options)
interface ButtonProps {
  onClick: (event: MouseEvent) => void;
  onSubmit: (data: FormData) => void;
  onError: (error: Error) => void;
}

// trigger* - Cause an event
function triggerRefresh(): void {}
function triggerValidation(): void {}

// emit* - Publish an event
function emitUserCreated(user: User): void {}
function emitOrderCompleted(order: Order): void {}

// dispatch* - Send action (Redux pattern)
function dispatchAddItem(item: Item): void {}
function dispatchUpdateCart(cart: Cart): void {}
```

### Async Operations

```typescript
// Prefer clear async naming
async function fetchUserAsync(id: string): Promise<User> {} // Explicit async suffix
async function loadDataAsync(): Promise<Data> {}

// Or rely on return type for clarity
async function fetchUser(id: string): Promise<User> {} // Promise indicates async

// For operations with callbacks
function fetchUserWithCallback(id: string, callback: (user: User) => void): void {}

// For operations that might be sync or async
function getOrFetchUser(id: string): User | Promise<User> {}
```

## Function Naming in Context

### Class Methods

```typescript
class UserService {
  // CRUD operations
  create(data: CreateUserDTO): User {}
  findById(id: string): User | null {}
  update(id: string, data: UpdateUserDTO): User {}
  delete(id: string): void {}

  // Business operations - use domain language
  activate(userId: string): void {}
  deactivate(userId: string): void {}
  resetPassword(userId: string): string {}
  verifyEmail(userId: string, token: string): boolean {}

  // Private helpers - can be more technical
  private hashPassword(password: string): string {}
  private generateToken(): string {}
  private sendNotification(user: User, type: NotificationType): void {}
}
```

### React Components

```tsx
function UserProfile({ userId }: Props) {
  // State handlers
  const [isEditing, setIsEditing] = useState(false);

  // Event handlers - handle prefix
  const handleEditClick = () => setIsEditing(true);
  const handleSaveClick = () => { /* save logic */ };
  const handleCancelClick = () => setIsEditing(false);

  // Data fetching - often in hooks
  const { user, isLoading } = useUser(userId);

  // Computed values - get prefix or descriptive
  const displayName = getDisplayName(user);
  const canEdit = hasEditPermission(user);

  // Render helpers - render prefix
  const renderHeader = () => <Header user={user} />;
  const renderEditForm = () => <EditForm user={user} />;
}
```

### Utility Functions

```typescript
// utils/string.ts
export function capitalize(str: string): string {}
export function truncate(str: string, maxLength: number): string {}
export function slugify(str: string): string {}

// utils/array.ts
export function unique<T>(array: T[]): T[] {}
export function groupBy<T>(array: T[], key: keyof T): Record<string, T[]> {}
export function chunk<T>(array: T[], size: number): T[][] {}

// utils/date.ts
export function addDays(date: Date, days: number): Date {}
export function isWeekend(date: Date): boolean {}
export function formatRelative(date: Date): string {}
```

## Anti-Patterns to Avoid

```typescript
// ❌ Avoid generic names
function handle() {}
function process() {}
function do() {}
function execute() {}
function run() {}
function manage() {}

// ❌ Avoid misleading names
function getUserById(email: string) {} // Parameter doesn't match name
function isEmpty(array: any[]): number {} // Returns number, not boolean

// ❌ Avoid implementation in name
function getUserFromMongoDB(id: string) {} // What if we change DBs?

// ❌ Avoid redundant context
class User {
  getUserName() {} // "User" is redundant
}

// ✅ Better
class User {
  getName() {}
}

// ❌ Avoid side effects with getter name
function getUser(id: string) {
  logAccess(id); // Side effect!
  return users[id];
}

// ✅ Better - name reveals side effect
function fetchAndLogUser(id: string) {
  logAccess(id);
  return users[id];
}
```

## Summary Table

| Pattern | Usage | Example |
|---------|-------|---------|
| `get*` | Sync retrieval | `getName()` |
| `fetch*` | Async HTTP | `fetchUser()` |
| `find*` | Search, may be null | `findById()` |
| `create*` | Make new | `createOrder()` |
| `update*` | Modify existing | `updateStatus()` |
| `delete*` | Remove | `deleteUser()` |
| `is*` | Boolean state | `isActive()` |
| `has*` | Boolean possession | `hasPermission()` |
| `can*` | Boolean capability | `canEdit()` |
| `validate*` | Check validity | `validateEmail()` |
| `format*` | To display format | `formatDate()` |
| `parse*` | From string | `parseJson()` |
| `handle*` | Process event | `handleClick()` |
