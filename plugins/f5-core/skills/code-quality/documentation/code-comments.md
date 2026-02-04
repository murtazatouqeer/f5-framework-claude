---
name: code-comments
description: Guidelines for writing effective code comments
category: code-quality/documentation
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Code Comments

## Overview

Comments should explain *why*, not *what*. Good code should be self-documenting through clear naming and structure. Comments fill the gaps where code can't express intent.

## When to Comment

### Comment the Why, Not the What

```typescript
// ❌ Bad - Explains what (obvious from code)
// Loop through users
for (const user of users) {
  // Check if user is active
  if (user.isActive) {
    // Add user to result
    result.push(user);
  }
}

// ✅ Good - Explains why
// Filter out inactive users to prevent sending emails to deactivated accounts
// as per GDPR compliance requirements
const activeUsers = users.filter(user => user.isActive);
```

### Document Business Rules

```typescript
// ❌ Bad - Just code
if (order.total > 100 && user.tier === 'gold') {
  order.discount = 0.15;
}

// ✅ Good - Business context
// Gold tier members get 15% discount on orders over $100
// Per marketing campaign Q4-2024 (JIRA: PROMO-1234)
if (order.total > 100 && user.tier === 'gold') {
  order.discount = 0.15;
}
```

### Explain Complex Algorithms

```typescript
// ❌ Bad - No context for complex code
function calculateHash(data: string): number {
  let hash = 5381;
  for (let i = 0; i < data.length; i++) {
    hash = ((hash << 5) + hash) ^ data.charCodeAt(i);
  }
  return hash >>> 0;
}

// ✅ Good - Explain the algorithm
/**
 * DJB2 hash function - fast, simple string hashing
 * 
 * Why DJB2: Good distribution, fast computation, minimal collisions
 * for our use case (cache keys for user sessions).
 * 
 * The magic number 5381 is a prime that works well empirically.
 * Left shift by 5 is equivalent to multiplying by 32.
 * 
 * @see http://www.cse.yorku.ca/~oz/hash.html
 */
function calculateHash(data: string): number {
  let hash = 5381;
  for (let i = 0; i < data.length; i++) {
    hash = ((hash << 5) + hash) ^ data.charCodeAt(i);
  }
  return hash >>> 0; // Convert to unsigned 32-bit integer
}
```

### Document Workarounds and Hacks

```typescript
// ❌ Bad - Unexplained hack
setTimeout(() => {
  element.focus();
}, 0);

// ✅ Good - Explains the workaround
// HACK: setTimeout(0) pushes focus to next event loop tick.
// This is needed because React's synthetic event system
// prevents focus during the current event handler.
// TODO: Remove when upgrading to React 18+ (fixes this issue)
setTimeout(() => {
  element.focus();
}, 0);
```

### Warn About Non-Obvious Behavior

```typescript
// ❌ Bad - Surprise behavior
function deleteUser(id: string) {
  // ... deletion logic
  cache.clear();
}

// ✅ Good - Warning about side effect
function deleteUser(id: string) {
  // ... deletion logic
  
  // WARNING: Clears entire cache to ensure no stale user data remains.
  // This affects all cached entities, not just the deleted user.
  // Consider targeted cache invalidation for better performance.
  cache.clear();
}
```

## When NOT to Comment

### Don't Explain Obvious Code

```typescript
// ❌ Bad - Obvious from code
// Declare a variable to store the user's name
const userName = user.name;

// Increment the counter by 1
counter++;

// Return true if the array is empty
return array.length === 0;

// ✅ Good - No comment needed, code is clear
const userName = user.name;
counter++;
return array.length === 0;
```

### Don't Use Comments as Excuses for Bad Code

```typescript
// ❌ Bad - Comment masks poor naming
// This function calculates the total price including tax and discounts
function calc(a, b, c) {
  return a * (1 + b) * (1 - c);
}

// ✅ Good - Self-documenting code
function calculateTotalPrice(subtotal: number, taxRate: number, discountRate: number): number {
  const afterTax = subtotal * (1 + taxRate);
  const afterDiscount = afterTax * (1 - discountRate);
  return afterDiscount;
}
```

### Don't Leave Commented-Out Code

```typescript
// ❌ Bad - Dead code
function processOrder(order: Order) {
  // const oldLogic = order.items.map(i => i.price);
  // const total = oldLogic.reduce((a, b) => a + b, 0);
  
  const total = calculateTotal(order);
  // console.log('Debug:', total);
  return total;
}

// ✅ Good - Clean code, use version control for history
function processOrder(order: Order) {
  return calculateTotal(order);
}
```

## Comment Types

### Single-Line Comments

```typescript
// Use for brief explanations on same line or line above

const timeout = 5000; // milliseconds

// Check for premium features before accessing
if (user.subscription.isPremium) {
  enablePremiumFeatures();
}
```

### Multi-Line Comments

```typescript
/*
 * Use for longer explanations that span multiple lines.
 * Keep each line under 80 characters for readability.
 * 
 * Good for:
 * - Complex algorithm explanations
 * - Important context or history
 * - Temporary notes during development
 */
```

### Documentation Comments

```typescript
/**
 * Use JSDoc/TSDoc for public APIs.
 * These generate documentation and provide IDE support.
 * 
 * @param userId - The unique identifier of the user
 * @returns The user object or null if not found
 */
function findUser(userId: string): User | null {
  // implementation
}
```

### TODO/FIXME Comments

```typescript
// TODO: Implement caching to improve performance
// Consider using Redis for distributed caching

// FIXME: This breaks when user.name contains special characters
// Need to escape HTML entities before rendering

// HACK: Temporary workaround for API rate limiting
// Remove after backend implements proper throttling

// NOTE: This relies on the external service being available
// See fallback handling in error handler

// DEPRECATED: Use newFunction() instead
// Will be removed in v3.0.0
```

## Comment Formatting

### Keep Comments Updated

```typescript
// ❌ Bad - Outdated comment
// Returns user's full name
function getUserDisplayName(user: User): string {
  return user.nickname || user.email; // Actually returns nickname or email!
}

// ✅ Good - Accurate comment
// Returns user's display name (nickname if set, otherwise email)
function getUserDisplayName(user: User): string {
  return user.nickname || user.email;
}
```

### Use Consistent Style

```typescript
// ✅ Consistent capitalization and punctuation
// Calculate the total including all applicable taxes.
// This uses the regional tax rates from the configuration.

// ❌ Inconsistent style
// calculate total
// This Uses regional tax rates from configuration
```

### Group Related Comments

```typescript
// ✅ Good - Grouped explanation
/*
 * Authentication Flow:
 * 1. Validate credentials against the database
 * 2. Generate JWT token with user claims
 * 3. Store refresh token in secure cookie
 * 4. Return access token to client
 */

// ❌ Bad - Scattered comments
// Validate credentials
const isValid = validateCredentials(email, password);
// Generate token
const token = generateToken(user);
// Store refresh token
storeRefreshToken(refreshToken);
// Return to client
return { accessToken: token };
```

## Special Comment Patterns

### Region Comments (Use Sparingly)

```typescript
// #region User Management
function createUser() {}
function updateUser() {}
function deleteUser() {}
// #endregion

// Note: Regions often indicate the file should be split
```

### License Headers

```typescript
/**
 * Copyright (c) 2024 Company Name
 * 
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
```

### API Version Comments

```typescript
/**
 * @since 2.0.0
 * @deprecated Use newMethod() instead. Will be removed in 3.0.0.
 */
function oldMethod() {}
```

## Comment Anti-Patterns

| Anti-Pattern | Example | Problem |
|--------------|---------|---------|
| Obvious comments | `i++; // increment i` | Adds noise |
| Commented code | `// const old = ...` | Use version control |
| Journal comments | `// Added by John 2024` | Use git blame |
| Misleading | Comment says X, code does Y | Dangerous |
| Too many | Every line commented | Code smell |
| Closing brace | `} // end if` | Use better structure |

## Self-Documenting Code Checklist

Before adding a comment, try these first:

- [ ] Can I rename the variable/function to be clearer?
- [ ] Can I extract a well-named function?
- [ ] Can I introduce an explaining variable?
- [ ] Can I use a more descriptive type?
- [ ] Can I remove code complexity?

If you still need a comment after these steps, write it!
