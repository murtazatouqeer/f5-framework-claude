---
name: boy-scout-rule
description: The Boy Scout Rule - Leave code better than you found it
category: code-quality/practices
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Boy Scout Rule

## Overview

> "Leave the campground cleaner than you found it."
> — The Boy Scout Rule, adapted for software

The Boy Scout Rule in software development means making small, incremental improvements to code quality whenever you work on a file. These small improvements compound over time, gradually improving the entire codebase.

## Core Principle

**Every time you touch code, leave it better than you found it.**

This doesn't mean rewriting everything. It means making small, safe improvements:
- Fix a typo
- Improve a variable name
- Add a missing type
- Extract a small function
- Remove dead code
- Add a clarifying comment

## Practical Examples

### Improve Variable Names

```typescript
// While fixing a bug, you see:
function calc(d) {
  const t = d.reduce((a, x) => a + x.p * x.q, 0);
  return t * 1.1;
}

// Leave it better:
function calculateOrderTotal(items: OrderItem[]): number {
  const subtotal = items.reduce(
    (sum, item) => sum + item.price * item.quantity,
    0
  );
  const TAX_RATE = 0.1;
  return subtotal * (1 + TAX_RATE);
}
```

### Add Missing Types

```typescript
// While adding a feature, you see:
function processUser(user) {
  if (user.active) {
    sendNotification(user);
  }
}

// Leave it better:
function processUser(user: User): void {
  if (user.active) {
    sendNotification(user);
  }
}
```

### Remove Dead Code

```typescript
// While reviewing, you see:
function getUserData(id: string) {
  // const oldMethod = fetchFromLegacy(id);
  // if (oldMethod) return oldMethod;
  
  const user = database.findUser(id);
  // TODO: Remove this after migration (2022-01-15)
  // const backup = backupStore.get(id);
  return user;
}

// Leave it better:
function getUserData(id: string): User | null {
  return database.findUser(id);
}
```

### Extract Magic Numbers

```typescript
// While debugging, you see:
if (retries > 3) {
  throw new Error('Max retries');
}
await sleep(1000);

// Leave it better:
const MAX_RETRY_ATTEMPTS = 3;
const RETRY_DELAY_MS = 1000;

if (retries > MAX_RETRY_ATTEMPTS) {
  throw new MaxRetriesExceededError();
}
await sleep(RETRY_DELAY_MS);
```

### Simplify Conditionals

```typescript
// While adding a condition, you see:
if (user !== null && user !== undefined) {
  if (user.status === 'active') {
    if (user.permissions && user.permissions.length > 0) {
      doSomething(user);
    }
  }
}

// Leave it better:
const isActiveUser = user?.status === 'active';
const hasPermissions = user?.permissions?.length > 0;

if (isActiveUser && hasPermissions) {
  doSomething(user);
}
```

### Add Error Handling

```typescript
// While adding a feature, you see:
async function fetchData(url) {
  const response = await fetch(url);
  return response.json();
}

// Leave it better:
async function fetchData<T>(url: string): Promise<T> {
  const response = await fetch(url);
  
  if (!response.ok) {
    throw new FetchError(`HTTP ${response.status}: ${response.statusText}`);
  }
  
  return response.json();
}
```

### Improve Function Structure

```typescript
// While fixing a bug, you see:
function processOrder(order) {
  if (order.items.length > 0) {
    let total = 0;
    for (let i = 0; i < order.items.length; i++) {
      total = total + order.items[i].price;
    }
    if (total > 100) {
      total = total * 0.9;
    }
    return total;
  }
  return 0;
}

// Leave it better:
function processOrder(order: Order): number {
  if (order.items.length === 0) {
    return 0;
  }

  const subtotal = calculateSubtotal(order.items);
  return applyBulkDiscount(subtotal);
}

function calculateSubtotal(items: OrderItem[]): number {
  return items.reduce((sum, item) => sum + item.price, 0);
}

function applyBulkDiscount(amount: number): number {
  const BULK_THRESHOLD = 100;
  const BULK_DISCOUNT = 0.1;
  
  return amount > BULK_THRESHOLD 
    ? amount * (1 - BULK_DISCOUNT)
    : amount;
}
```

## What to Clean Up

### Always Safe

| Improvement | Risk | Time |
|------------|------|------|
| Fix typos | None | 1 min |
| Add types | Very low | 2 min |
| Rename variables | Low | 2 min |
| Remove dead code | Low | 2 min |
| Add constants for magic numbers | Low | 3 min |
| Format code | None | 1 min |

### Usually Safe

| Improvement | Risk | Time |
|------------|------|------|
| Extract small functions | Low | 5 min |
| Simplify conditionals | Low | 5 min |
| Add null checks | Low | 3 min |
| Convert var to const/let | Low | 2 min |
| Add JSDoc comments | None | 5 min |

### Proceed with Caution

| Improvement | Risk | Time |
|------------|------|------|
| Refactor algorithm | Medium | 30+ min |
| Change function signatures | Medium | 15+ min |
| Restructure classes | Medium | 30+ min |
| Change data structures | High | 30+ min |

## When NOT to Apply

### Time Constraints

```typescript
// Critical production bug at 3 AM?
// Fix the bug, ship it, create a ticket for cleanup later.

// ❌ Don't do this during incident response:
// "While I'm here, let me refactor the entire auth module..."

// ✅ Do this:
// Fix the immediate issue
// Create ticket: "Clean up auth module - see incident #123"
```

### Unrelated Code

```typescript
// Working on user authentication?
// Don't clean up the payment module "while you're here"

// ❌ PR: "Add login feature + refactor payments + fix email templates"
// ✅ PR: "Add login feature (improved auth utils while here)"
```

### No Test Coverage

```typescript
// If code has no tests and you're not sure what it does:
// Don't refactor it just to make it "cleaner"

// ❌ Risky without tests:
function mysteriousLegacyFunction(data) {
  // 200 lines of untested code
  // "I'll just clean this up..."
}

// ✅ Better approach:
// 1. Add tests first
// 2. Then improve
```

## Team Guidelines

### Commit Strategy

```bash
# Option 1: Separate commits
git commit -m "fix: resolve login timeout bug"
git commit -m "refactor: improve auth utils naming"

# Option 2: Combined with clear message
git commit -m "fix: resolve login timeout bug

Also improved variable naming and extracted constants
in auth utilities touched during fix."
```

### PR Guidelines

```markdown
## PR Description

### Changes
- Fixed login timeout bug (#123)

### Boy Scout Improvements (while here)
- Renamed `usr` → `currentUser` in auth.ts
- Extracted `AUTH_TIMEOUT_MS` constant
- Added missing TypeScript types
- Removed commented-out code from 2019

These improvements are in files touched by the main fix.
```

### Code Review Notes

```markdown
# For Reviewers

When reviewing Boy Scout changes:
- ✅ Accept: Small, safe improvements in touched files
- ⚠️ Question: Large refactors unrelated to main change
- ❌ Reject: Changes to untouched files "while we're at it"
```

## Measuring Impact

### Before/After Metrics

```
File: auth/login.ts
Before Boy Scout fixes (6 months ago):
- Lines: 450
- Complexity: 28
- Types: 40% coverage
- Lint warnings: 15

After consistent Boy Scout approach:
- Lines: 320 (-30%)
- Complexity: 12 (-57%)
- Types: 100% coverage
- Lint warnings: 0
```

### Team Dashboard

```
┌─────────────────────────────────────────────┐
│         Boy Scout Metrics (Monthly)         │
├─────────────────────────────────────────────┤
│                                             │
│  PRs with Boy Scout improvements: 45/60     │
│  ████████████████████░░░░░ 75%              │
│                                             │
│  Average improvements per PR: 2.3           │
│                                             │
│  Code quality trend: ↗ Improving            │
│  - Lint warnings: -15%                      │
│  - Type coverage: +8%                       │
│  - Complexity: -12%                         │
│                                             │
└─────────────────────────────────────────────┘
```

## Summary

| Do | Don't |
|----|-------|
| Small improvements | Big refactors |
| Same files you're touching | Files you're not touching |
| Safe, tested changes | Risky changes without tests |
| Clear commit messages | Hiding cleanup in features |
| Incremental progress | Perfect all at once |

**Remember**: Small improvements compound. A few minutes of cleanup each day leads to significantly better code over weeks and months.
