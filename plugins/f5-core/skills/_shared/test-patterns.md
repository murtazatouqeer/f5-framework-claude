---
name: shared-test-patterns
description: Common testing patterns used across F5 Framework
category: shared
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Shared Test Patterns

## AAA Pattern (Arrange-Act-Assert)

```typescript
describe('UserService', () => {
  it('should return user when found', async () => {
    // Arrange
    const expectedUser = { id: '1', name: 'John' };
    mockRepo.findById.mockResolvedValue(expectedUser);

    // Act
    const result = await userService.getUser('1');

    // Assert
    expect(result).toEqual(expectedUser);
    expect(mockRepo.findById).toHaveBeenCalledWith('1');
  });
});
```

## Test Naming Convention

Pattern: `should_ExpectedBehavior_When_StateUnderTest`

```typescript
it('should return sum when adding two positive numbers', () => {});
it('should throw error when dividing by zero', () => {});
it('should return empty array when no items found', () => {});
```

## Mock Patterns

### Mock Repository
```typescript
const mockRepo = {
  findById: jest.fn(),
  save: jest.fn(),
  delete: jest.fn(),
};
```

### Mock External Service
```typescript
jest.mock('../external-service', () => ({
  fetchData: jest.fn().mockResolvedValue({ data: 'test' }),
}));
```

## Test Data Factories

```typescript
const createTestUser = (overrides = {}) => ({
  id: '123',
  name: 'Test User',
  email: 'test@test.com',
  ...overrides,
});
```

## Edge Case Checklist

- [ ] Empty input
- [ ] Null/undefined input
- [ ] Boundary values
- [ ] Invalid format
- [ ] Large input
- [ ] Concurrent access
- [ ] Network failure
- [ ] Timeout

## Coverage Targets

| Type | Target |
|------|--------|
| Statements | ≥80% |
| Branches | ≥75% |
| Functions | ≥80% |
| Lines | ≥80% |
