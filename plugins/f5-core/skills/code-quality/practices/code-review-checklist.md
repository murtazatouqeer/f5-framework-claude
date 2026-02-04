---
name: code-review-checklist
description: Comprehensive code review checklist and guidelines
category: code-quality/practices
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Code Review Checklist

## Overview

Code reviews improve code quality, share knowledge, and catch bugs early. This checklist helps reviewers be thorough and consistent.

## Quick Review Checklist

### ✅ Functionality
- [ ] Code does what it's supposed to do
- [ ] Edge cases are handled
- [ ] Error scenarios are covered
- [ ] No obvious bugs

### ✅ Design
- [ ] Code follows project patterns
- [ ] No unnecessary complexity
- [ ] Single responsibility principle
- [ ] Appropriate abstraction level

### ✅ Quality
- [ ] Readable and self-documenting
- [ ] No code smells
- [ ] Tests included and passing
- [ ] No hardcoded values

### ✅ Security
- [ ] No exposed secrets
- [ ] Input validation present
- [ ] No injection vulnerabilities
- [ ] Proper authentication/authorization

## Detailed Review Areas

### 1. Logic and Correctness

```typescript
// ❌ Bug: Off-by-one error
for (let i = 0; i <= items.length; i++) {
  process(items[i]); // items[items.length] is undefined!
}

// ✅ Correct
for (let i = 0; i < items.length; i++) {
  process(items[i]);
}

// ✅ Better - use for-of
for (const item of items) {
  process(item);
}
```

**Check for:**
- Off-by-one errors
- Null/undefined handling
- Async/await correctness
- Race conditions
- Boundary conditions

### 2. Error Handling

```typescript
// ❌ Bad - Swallowing errors
try {
  await saveData(data);
} catch (error) {
  // Silent failure!
}

// ❌ Bad - Generic error message
try {
  await saveData(data);
} catch (error) {
  throw new Error('Something went wrong');
}

// ✅ Good - Proper error handling
try {
  await saveData(data);
} catch (error) {
  logger.error('Failed to save data', { error, data });
  throw new DataPersistenceError('Could not save user data', { cause: error });
}
```

**Check for:**
- Empty catch blocks
- Proper error logging
- Error propagation
- User-friendly error messages
- Error recovery

### 3. Security

```typescript
// ❌ SQL Injection vulnerability
const query = `SELECT * FROM users WHERE id = '${userId}'`;

// ✅ Parameterized query
const query = 'SELECT * FROM users WHERE id = $1';
const result = await db.query(query, [userId]);

// ❌ XSS vulnerability
element.innerHTML = userInput;

// ✅ Safe
element.textContent = userInput;
// Or sanitize if HTML is needed
element.innerHTML = DOMPurify.sanitize(userInput);

// ❌ Exposed secrets
const apiKey = 'sk-1234567890';

// ✅ From environment
const apiKey = process.env.API_KEY;
```

**Check for:**
- SQL/NoSQL injection
- XSS vulnerabilities
- CSRF protection
- Hardcoded credentials
- Sensitive data in logs
- Authentication bypass

### 4. Performance

```typescript
// ❌ N+1 query problem
const users = await db.users.findAll();
for (const user of users) {
  const orders = await db.orders.findByUser(user.id); // N queries!
}

// ✅ Eager loading
const users = await db.users.findAll({
  include: [{ model: db.orders }],
});

// ❌ Unnecessary re-renders (React)
function UserList({ users }) {
  const sortedUsers = users.sort((a, b) => a.name.localeCompare(b.name));
  return <ul>{sortedUsers.map(u => <li key={u.id}>{u.name}</li>)}</ul>;
}

// ✅ Memoized
function UserList({ users }) {
  const sortedUsers = useMemo(
    () => [...users].sort((a, b) => a.name.localeCompare(b.name)),
    [users]
  );
  return <ul>{sortedUsers.map(u => <li key={u.id}>{u.name}</li>)}</ul>;
}
```

**Check for:**
- N+1 queries
- Unnecessary iterations
- Memory leaks
- Missing indexes
- Unoptimized algorithms
- React re-render issues

### 5. Code Style and Readability

```typescript
// ❌ Hard to read
if(x>0&&y<10||z===null){doSomething();doSomethingElse();}

// ✅ Readable
const isInRange = x > 0 && y < 10;
const isUnset = z === null;

if (isInRange || isUnset) {
  doSomething();
  doSomethingElse();
}
```

**Check for:**
- Consistent formatting
- Clear naming
- Appropriate comments
- Logical organization
- No dead code

### 6. Testing

```typescript
// ❌ Bad test - no clear assertion
it('should work', () => {
  const result = process(data);
  expect(result).toBeDefined();
});

// ✅ Good test - specific assertion
it('should calculate total with tax', () => {
  const order = createOrder({ subtotal: 100, taxRate: 0.1 });
  const result = calculateTotal(order);
  expect(result).toBe(110);
});

// ✅ Good test - edge case
it('should handle empty order', () => {
  const order = createOrder({ items: [] });
  const result = calculateTotal(order);
  expect(result).toBe(0);
});
```

**Check for:**
- Test coverage
- Edge cases tested
- Clear test names
- No flaky tests
- Proper mocking

## Review Process

### Before You Start

1. Understand the context (PR description, linked issues)
2. Run the code locally if needed
3. Check CI/CD status

### During Review

1. **First pass**: High-level design and architecture
2. **Second pass**: Logic and correctness
3. **Third pass**: Code quality and style

### Providing Feedback

#### Good Comment Examples

```markdown
# Suggestion
Consider using `Array.includes()` here for better readability:
`if (validStatuses.includes(status))`

# Question
What happens if `userId` is undefined here? Should we add a check?

# Praise
Nice refactoring! This is much cleaner than the previous implementation.

# Concern
This query could be slow with large datasets. 
Could we add an index or pagination?
```

#### Comment Categories

| Prefix | Meaning | Action |
|--------|---------|--------|
| `[blocking]` | Must fix before merge | Required |
| `[suggestion]` | Nice to have | Optional |
| `[question]` | Need clarification | Discussion |
| `[nit]` | Minor style issue | Optional |
| `[praise]` | Good work | None |

### Review Response Etiquette

**For Authors:**
- Respond to all comments
- Don't take feedback personally
- Explain your reasoning
- Be open to alternatives

**For Reviewers:**
- Be kind and constructive
- Explain the "why"
- Offer solutions, not just problems
- Acknowledge good work

## Review Metrics

### Healthy Review Process

| Metric | Target |
|--------|--------|
| Time to first review | < 24 hours |
| Review iterations | 1-3 rounds |
| Comments per review | 5-15 substantive |
| PR size | < 400 lines |

### Red Flags

- PRs sitting for days
- Review wars (many rounds)
- No comments (rubber stamp)
- Consistently large PRs

## Automated Checks

Let automation handle what it can:

```yaml
# .github/workflows/pr-checks.yml
name: PR Checks
on: [pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Lint
        run: npm run lint
      - name: Type check
        run: npm run type-check
      - name: Tests
        run: npm run test
      - name: Security audit
        run: npm audit
```

This frees reviewers to focus on:
- Business logic
- Design decisions
- Edge cases
- Knowledge sharing
