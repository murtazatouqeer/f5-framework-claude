---
name: tdd
description: tdd skill
category: testing
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: true
context: inject
---# Test-Driven Development (TDD) Skill

## Auto-Activation
Triggered when:
- `/f5-tdd` command is used
- `--tdd` flag is passed to `/f5-implement`
- TDD mode is enabled in session

## TDD Workflow Phases

### 1. Red Phase - Write Failing Test
**Goal**: Define expected behavior before implementation

```typescript
// REQ-001: User authentication
describe('AuthService', () => {
  it('should authenticate valid user credentials', async () => {
    const result = await authService.authenticate({
      email: 'user@example.com',
      password: 'validPassword123',
    });

    expect(result).toBeDefined();
    expect(result.accessToken).toBeDefined();
    expect(result.user.email).toBe('user@example.com');
  });

  it('should reject invalid credentials', async () => {
    await expect(
      authService.authenticate({
        email: 'user@example.com',
        password: 'wrongPassword',
      }),
    ).rejects.toThrow(UnauthorizedException);
  });
});
```

### 2. Green Phase - Minimal Implementation
**Goal**: Write minimum code to pass the test

```typescript
// REQ-001: User authentication
@Injectable()
export class AuthService {
  async authenticate(dto: LoginDto): Promise<AuthResult> {
    const user = await this.userRepository.findByEmail(dto.email);

    if (!user || !await this.verifyPassword(dto.password, user.passwordHash)) {
      throw new UnauthorizedException('Invalid credentials');
    }

    return {
      accessToken: this.jwtService.sign({ sub: user.id }),
      user: user,
    };
  }
}
```

### 3. Refactor Phase - Improve Code Quality
**Goal**: Improve code while keeping tests green

- Extract common patterns
- Improve naming
- Remove duplication
- Optimize performance
- Add documentation

## TDD Best Practices

### Test Structure (AAA Pattern)
```typescript
it('should do something', () => {
  // Arrange - Set up test data and conditions
  const input = createTestInput();

  // Act - Execute the code under test
  const result = service.doSomething(input);

  // Assert - Verify the expected outcome
  expect(result).toEqual(expectedOutput);
});
```

### Test Naming Convention
- `should [expected behavior] when [condition]`
- `should return [value] for [input]`
- `should throw [error] when [invalid condition]`

### Coverage Requirements
- Unit tests: 80% minimum (G3 gate)
- Integration tests: Critical paths covered
- E2E tests: Main user journeys

## Integration with F5 Framework

### With Quality Gates
- G2: Tests written before implementation
- G2.5: Integration tests passing
- G3: 80% coverage achieved

### With Agents
- f5-architect: Defines testable architecture
- f5-reviewer: Reviews test quality
- f5-tester: Executes TDD workflow

### Commands
```bash
/f5-tdd start feature-name    # Start TDD session
/f5-tdd red                   # Write failing test
/f5-tdd green                 # Implement to pass
/f5-tdd refactor              # Improve code quality
/f5-tdd end                   # End TDD session
```

## Test Doubles

### Mocks
```typescript
const mockUserRepository = {
  findByEmail: jest.fn().mockResolvedValue(mockUser),
  save: jest.fn().mockResolvedValue(mockUser),
};
```

### Stubs
```typescript
const stubConfigService = {
  get: (key: string) => configValues[key],
};
```

### Spies
```typescript
const spy = jest.spyOn(service, 'method');
// ... execute code
expect(spy).toHaveBeenCalledWith(expectedArgs);
```

## Output Artifacts
- Test specifications
- Implementation code with traceability
- Coverage reports
- Refactoring notes
