---
name: variable-naming
description: Best practices for variable naming
category: code-quality/naming
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Variable Naming

## Overview

Good variable names are crucial for code readability. A well-named variable tells you what it contains and how it should be used.

## Core Principles

### 1. Be Descriptive

```typescript
// ❌ Bad - Cryptic
const d = new Date();
const n = users.length;
const t = price * quantity;
const arr = getItems();

// ✅ Good - Descriptive
const currentDate = new Date();
const userCount = users.length;
const totalPrice = price * quantity;
const orderItems = getItems();
```

### 2. Reveal Intent

```typescript
// ❌ Bad - What does this do?
const d = Date.now() - user.d;
if (d > 86400000) { ... }

// ✅ Good - Intent is clear
const timeSinceLastLogin = Date.now() - user.lastLoginAt;
const ONE_DAY_MS = 24 * 60 * 60 * 1000;
if (timeSinceLastLogin > ONE_DAY_MS) { ... }
```

### 3. Be Pronounceable

```typescript
// ❌ Bad - Unpronounceable
const genymdhms = generateTimestamp();
const modymdhms = user.modifiedAt;

// ✅ Good - Pronounceable
const generationTimestamp = generateTimestamp();
const modificationDate = user.modifiedAt;
```

### 4. Be Searchable

```typescript
// ❌ Bad - Can't search for "5"
setTimeout(callback, 86400000);
if (status === 5) { ... }

// ✅ Good - Searchable constants
const ONE_DAY_MS = 86400000;
const STATUS_ACTIVE = 5;

setTimeout(callback, ONE_DAY_MS);
if (status === STATUS_ACTIVE) { ... }
```

## Naming by Type

### Booleans

Always use predicates (is, has, should, can, will, did).

```typescript
// ❌ Bad - Unclear if boolean
const active = true;
const login = false;
const permission = true;
const visible = true;

// ✅ Good - Clear boolean intent
const isActive = true;
const hasLoggedIn = false;
const canEdit = true;
const shouldDisplay = true;
const willRetry = true;
const didComplete = false;

// ✅ Good - In conditions
if (isActive) { ... }
if (!hasPermission) { ... }
if (user.isVerified && order.isPaid) { ... }
```

### Numbers

Include units or context.

```typescript
// ❌ Bad - What unit?
const duration = 5;
const size = 1024;
const delay = 1000;
const price = 99;

// ✅ Good - Clear units
const durationInSeconds = 5;
const fileSizeInBytes = 1024;
const delayMs = 1000;
const priceInCents = 9900;

// ✅ Or use typed wrappers
interface Duration {
  value: number;
  unit: 'ms' | 's' | 'm' | 'h';
}
const timeout: Duration = { value: 5, unit: 's' };
```

### Arrays and Collections

Use plural nouns.

```typescript
// ❌ Bad - Unclear if array
const user = getUsers();
const item = fetchItems();
const orderList = getOrders();

// ✅ Good - Plural indicates array
const users = getUsers();
const items = fetchItems();
const orders = getOrders();

// ✅ For specific items from array
const firstUser = users[0];
const selectedItems = items.filter(item => item.isSelected);
const activeOrders = orders.filter(order => order.isActive);
```

### Maps and Records

Describe the key-value relationship.

```typescript
// ❌ Bad - What's the structure?
const data = new Map();
const lookup = {};

// ✅ Good - Clear structure
const userById = new Map<string, User>();
const ordersByCustomerId = new Map<string, Order[]>();
const priceByProductId: Record<string, number> = {};
const configByEnvironment: Record<string, Config> = {};
```

### Functions Returning Values

Name by what they return.

```typescript
// ❌ Bad - Unclear what's returned
const process = (order) => { ... };
const check = (user) => { ... };

// ✅ Good - Clear return type
const calculateTotal = (order: Order): number => { ... };
const isUserActive = (user: User): boolean => { ... };
const findUserById = (id: string): User | null => { ... };
const getUserOrders = (userId: string): Order[] => { ... };
```

## Context-Aware Naming

### Loop Variables

```typescript
// ❌ OK for short loops, but can be clearer
for (let i = 0; i < users.length; i++) {
  const u = users[i];
}

// ✅ Better - Descriptive
for (let userIndex = 0; userIndex < users.length; userIndex++) {
  const currentUser = users[userIndex];
}

// ✅ Best - Use for-of when possible
for (const user of users) {
  processUser(user);
}

// ✅ With index when needed
users.forEach((user, index) => {
  console.log(`User ${index + 1}: ${user.name}`);
});
```

### Nested Loops

```typescript
// ❌ Bad - Confusing
for (let i = 0; i < rows.length; i++) {
  for (let j = 0; j < rows[i].cells.length; j++) {
    const c = rows[i].cells[j];
  }
}

// ✅ Good - Clear context
for (const row of rows) {
  for (const cell of row.cells) {
    processCell(cell);
  }
}

// ✅ When indices needed
for (let rowIndex = 0; rowIndex < rows.length; rowIndex++) {
  const row = rows[rowIndex];
  for (let colIndex = 0; colIndex < row.cells.length; colIndex++) {
    const cell = row.cells[colIndex];
  }
}
```

### Callback Parameters

```typescript
// ❌ Bad - Unclear
users.map(x => x.name);
items.filter(i => i.active);
orders.reduce((a, b) => a + b.total, 0);

// ✅ Good - Descriptive
users.map(user => user.name);
items.filter(item => item.isActive);
orders.reduce((totalAmount, order) => totalAmount + order.total, 0);
```

### Destructuring

```typescript
// ❌ Bad - Overuse of short names
const { n, e, a } = user;

// ✅ Good - Keep meaningful names
const { name, email, address } = user;

// ✅ Rename when context is clear
const { name: userName, email: userEmail } = user;
const { name: productName, price: productPrice } = product;
```

## Avoiding Common Mistakes

### Avoid Generic Names

```typescript
// ❌ Bad
const data = fetchData();
const info = getUserInfo();
const result = processOrder();
const temp = calculateValue();
const obj = createObject();

// ✅ Good - Specific
const userProfile = fetchUserProfile();
const orderSummary = getOrderSummary();
const paymentResult = processPayment();
const discountedPrice = calculateDiscountedPrice();
const shippingAddress = createShippingAddress();
```

### Avoid Abbreviations

```typescript
// ❌ Bad - Unclear abbreviations
const usrCnt = getUserCount();
const prodCat = product.category;
const btnClk = handleClick;
const addr = user.address;
const msg = 'Hello';

// ✅ Good - Full words
const userCount = getUserCount();
const productCategory = product.category;
const handleButtonClick = handleClick;
const address = user.address;
const message = 'Hello';

// ✅ Acceptable abbreviations (well-known)
const id = user.id;           // identifier
const url = config.apiUrl;    // URL
const html = render();        // HTML
const api = createApi();      // API
const config = loadConfig();  // configuration
```

### Avoid Noise Words

```typescript
// ❌ Bad - Redundant words
const userData = getUser();
const userInfo = fetchUser();
const userObject = createUser();
const theUser = findUser();
const aUser = selectUser();

// ✅ Good - Just the noun
const user = getUser();
const userProfile = getUserProfile();
const selectedUser = selectUser();
```

### Consistent Vocabulary

```typescript
// ❌ Bad - Inconsistent terms
function fetchUser() {}
function getOrder() {}
function retrieveProduct() {}
function loadCustomer() {}

// ✅ Good - Consistent
function getUser() {}
function getOrder() {}
function getProduct() {}
function getCustomer() {}

// Or consistent with specific meanings:
// fetch* = HTTP request
// get* = synchronous retrieval
// load* = async with caching
// find* = search with possible null
```

## Variable Scope and Length

### Short Scope = Short Name

```typescript
// ✅ OK - Very short scope
users.map(u => u.name);
items.find(i => i.id === targetId);

// ✅ Better - Longer scope needs longer name
function processOrder(order: Order) {
  const orderItems = order.items;
  const totalAmount = orderItems.reduce(
    (sum, item) => sum + item.price * item.quantity,
    0
  );
  return { orderId: order.id, totalAmount };
}
```

### Long Scope = Descriptive Name

```typescript
// Module-level variables need very clear names
const defaultUserPreferences: UserPreferences = {
  theme: 'light',
  notifications: true,
};

const MAX_AUTHENTICATION_ATTEMPTS = 3;
const SESSION_TIMEOUT_MINUTES = 30;
```
