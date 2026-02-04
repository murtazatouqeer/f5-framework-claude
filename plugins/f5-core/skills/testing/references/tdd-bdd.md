# TDD & BDD Patterns

Test-Driven Development and Behavior-Driven Development workflows for quality-first software development.

## Table of Contents

1. [TDD Overview](#tdd-overview)
2. [Red-Green-Refactor Cycle](#red-green-refactor-cycle)
3. [BDD Overview](#bdd-overview)
4. [Given-When-Then Pattern](#given-when-then-pattern)
5. [Gherkin Syntax](#gherkin-syntax)
6. [F5 Framework Integration](#f5-framework-integration)

---

## TDD Overview

### Core Principles

| Principle | Description |
|-----------|-------------|
| Test First | Write tests before implementation |
| Minimal Code | Write only enough code to pass tests |
| Continuous Refactoring | Improve code while keeping tests green |
| Fast Feedback | Run tests frequently during development |

### When to Use TDD

- Business logic with clear requirements
- Algorithm implementation
- Data validation and transformation
- API endpoint behavior
- Bug fixes (write failing test first)

---

## Red-Green-Refactor Cycle

### Phase 1: Red (Write Failing Test)

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

### Phase 2: Green (Minimal Implementation)

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

### Phase 3: Refactor (Improve Code Quality)

**Goal**: Improve code while keeping tests green

- Extract common patterns
- Improve naming and readability
- Remove duplication
- Optimize performance
- Add documentation

```typescript
// After refactoring
@Injectable()
export class AuthService {
  async authenticate(dto: LoginDto): Promise<AuthResult> {
    const user = await this.findAndValidateUser(dto);
    return this.createAuthResult(user);
  }

  private async findAndValidateUser(dto: LoginDto): Promise<User> {
    const user = await this.userRepository.findByEmail(dto.email);

    if (!user) {
      throw new UnauthorizedException('Invalid credentials');
    }

    const isValidPassword = await this.verifyPassword(dto.password, user.passwordHash);
    if (!isValidPassword) {
      throw new UnauthorizedException('Invalid credentials');
    }

    return user;
  }

  private createAuthResult(user: User): AuthResult {
    return {
      accessToken: this.jwtService.sign({ sub: user.id }),
      user: user,
    };
  }
}
```

---

## BDD Overview

### Core Concepts

| Concept | Description |
|---------|-------------|
| Behavior Focus | Describe system behavior in business terms |
| Ubiquitous Language | Use domain language shared by all stakeholders |
| Living Documentation | Tests serve as executable specifications |
| Collaboration | Bridge gap between technical and business teams |

### BDD vs TDD

| Aspect | TDD | BDD |
|--------|-----|-----|
| Focus | Implementation correctness | Business behavior |
| Language | Technical | Business domain |
| Audience | Developers | Developers + Stakeholders |
| Naming | `should [result] when [condition]` | `Given-When-Then` |
| Scope | Unit level | Feature/acceptance level |

---

## Given-When-Then Pattern

### Pattern Structure

```
GIVEN [preconditions/initial state]
WHEN [action/event occurs]
THEN [expected outcome/behavior]
```

### Basic Example

```typescript
describe('UserRegistration', () => {
  it('should allow registration with valid email', () => {
    // Given a new user with valid details
    const registrationService = new RegistrationService();
    const validUserData = {
      email: 'newuser@example.com',
      password: 'SecurePass123!',
    };

    // When they register
    const result = registrationService.register(validUserData);

    // Then they should be successfully registered
    expect(result.success).toBe(true);
    expect(result.user.email).toBe('newuser@example.com');
  });
});
```

### With Multiple Conditions

```typescript
describe('ShoppingCart', () => {
  it('should apply discount for premium customer with large order', () => {
    // Given a premium customer
    const customer = createCustomer({ type: 'premium' });

    // And a cart with items totaling over $100
    const cart = new ShoppingCart(customer);
    cart.addItem({ price: 50, quantity: 3 }); // $150

    // When the discount is calculated
    const discount = cart.calculateDiscount();

    // Then a 15% discount should be applied
    expect(discount).toBe(22.5);
  });
});
```

### Nested Givens (Jest)

```typescript
describe('Premium User Features', () => {
  describe('Given a premium user', () => {
    let user: User;

    beforeEach(async () => {
      user = await createPremiumUser();
    });

    describe('And they have active subscription', () => {
      beforeEach(async () => {
        await activateSubscription(user.id, { plan: 'premium' });
      });

      describe('When they access exclusive content', () => {
        it('Then they should see full content', async () => {
          const content = await contentService.getExclusive(user.id, 'article-1');

          expect(content.isRestricted).toBe(false);
          expect(content.fullText).toBeDefined();
        });
      });
    });

    describe('And subscription has expired', () => {
      beforeEach(async () => {
        await expireSubscription(user.id);
      });

      describe('When they access exclusive content', () => {
        it('Then they should see preview only', async () => {
          const content = await contentService.getExclusive(user.id, 'article-1');

          expect(content.isRestricted).toBe(true);
          expect(content.fullText).toBeUndefined();
          expect(content.preview).toBeDefined();
        });
      });
    });
  });
});
```

---

## Gherkin Syntax

### Feature File Structure

```gherkin
Feature: User Authentication
  As a registered user
  I want to log into my account
  So that I can access my personal data

  Background:
    Given the authentication service is available

  Scenario: Successful login
    Given a user exists with email "user@test.com" and password "password123"
    When the user logs in with email "user@test.com" and password "password123"
    Then the login should be successful
    And a valid session token should be returned

  Scenario: Failed login with wrong password
    Given a user exists with email "user@test.com" and password "password123"
    When the user logs in with email "user@test.com" and password "wrongpassword"
    Then the login should fail
    And the error message should be "Invalid credentials"

  Scenario Outline: Password validation
    Given a user is registering
    When they enter password "<password>"
    Then the validation result should be <valid>
    And the message should be "<message>"

    Examples:
      | password      | valid | message                     |
      | weak          | false | Password too short          |
      | NoSpecial123  | false | Must include special char   |
      | ValidPass1!   | true  | Password accepted           |
```

### Step Definitions (Cucumber.js)

```typescript
import { Given, When, Then } from '@cucumber/cucumber';
import { expect } from 'chai';

let authService: AuthService;
let loginResult: LoginResult;
let existingUser: User;

Given('the authentication service is available', function () {
  authService = new AuthService();
});

Given('a user exists with email {string} and password {string}',
  async function (email: string, password: string) {
    existingUser = await authService.createUser({ email, password });
  }
);

When('the user logs in with email {string} and password {string}',
  async function (email: string, password: string) {
    loginResult = await authService.login({ email, password });
  }
);

Then('the login should be successful', function () {
  expect(loginResult.success).to.be.true;
});

Then('the login should fail', function () {
  expect(loginResult.success).to.be.false;
});

Then('a valid session token should be returned', function () {
  expect(loginResult.token).to.be.a('string');
  expect(loginResult.token.length).to.be.greaterThan(0);
});

Then('the error message should be {string}', function (message: string) {
  expect(loginResult.error).to.equal(message);
});
```

### And/But Keywords

```gherkin
Scenario: Apply coupon to order
  Given a customer has items in their cart
  And the cart total is $100
  And a valid coupon "SAVE20" exists for 20% off
  When the customer applies coupon "SAVE20"
  Then the discount should be $20
  And the new total should be $80
  But the original price should still show $100

Scenario: Cannot apply expired coupon
  Given a customer has items in their cart
  And a coupon "OLDCODE" that expired yesterday
  When the customer applies coupon "OLDCODE"
  Then the coupon should be rejected
  And an error message "Coupon has expired" should show
  But the cart total should remain unchanged
```

---

## F5 Framework Integration

### Quality Gates Mapping

| Gate | TDD Requirement | Implementation |
|------|-----------------|----------------|
| G2 | Tests written before implementation | Red phase completed |
| G2.5 | All tests passing | Green phase completed |
| G3 | 80% coverage achieved | Comprehensive test suite |
| G4 | Integration tests passing | E2E verification |

### TDD Commands

```bash
/f5-tdd start feature-name    # Start TDD session
/f5-tdd red                   # Write failing test
/f5-tdd green                 # Implement to pass
/f5-tdd refactor              # Improve code quality
/f5-tdd end                   # End TDD session
```

### Test Naming Convention

```typescript
// Pattern: should [expected behavior] when [condition]
it('should return null when user not found', () => {});
it('should throw error when password is invalid', () => {});
it('should create user when all fields are valid', () => {});
```

### Coverage Requirements

| Level | Requirement | Gate |
|-------|-------------|------|
| Unit tests | 80% minimum | G3 |
| Integration tests | Critical paths covered | G3 |
| E2E tests | Main user journeys | G4 |

---

## Best Practices

### TDD Best Practices

| Do | Don't |
|----|-------|
| Write test first | Write code first, then tests |
| One assertion per test | Multiple unrelated assertions |
| Test behavior, not implementation | Test private methods |
| Keep tests fast | Rely on external services |
| Refactor in green phase | Refactor in red phase |

### BDD Best Practices

| Do | Don't |
|----|-------|
| Use business language | Use technical jargon |
| Keep scenarios focused | Test multiple behaviors |
| Abstract technical details | Expose implementation |
| Collaborate with stakeholders | Write in isolation |

### Decision Guide

| Use TDD When | Use BDD When |
|--------------|--------------|
| Unit-level testing | Acceptance testing |
| Developer-only audience | Stakeholder communication |
| Technical requirements | Business requirements |
| Algorithm implementation | User journey validation |
| Quick iteration | Living documentation needed |
