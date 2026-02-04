# Test Patterns & Best Practices

Reusable testing patterns including AAA, fixtures, factories, and Page Object Model.

## Table of Contents

1. [AAA Pattern](#aaa-pattern)
2. [Test Fixtures](#test-fixtures)
3. [Factory Patterns](#factory-patterns)
4. [Page Object Model](#page-object-model)
5. [Test Data Management](#test-data-management)

---

## AAA Pattern

### Overview

The Arrange-Act-Assert pattern provides clear structure for organizing tests into three phases.

```
┌──────────────────────────────────────────────────┐
│  ARRANGE                                          │
│  - Set up test data                              │
│  - Configure mocks                               │
│  - Create dependencies                           │
└──────────────────────────────────────────────────┘
                      ↓
┌──────────────────────────────────────────────────┐
│  ACT                                              │
│  - Execute the code under test                   │
│  - Usually ONE action                            │
└──────────────────────────────────────────────────┘
                      ↓
┌──────────────────────────────────────────────────┐
│  ASSERT                                           │
│  - Verify expected outcomes                      │
│  - Check state changes                           │
│  - Validate interactions                         │
└──────────────────────────────────────────────────┘
```

### Basic Example

```typescript
describe('Calculator', () => {
  it('should add two numbers', () => {
    // Arrange
    const calculator = new Calculator();
    const a = 5;
    const b = 3;

    // Act
    const result = calculator.add(a, b);

    // Assert
    expect(result).toBe(8);
  });
});
```

### Service Testing Example

```typescript
describe('UserService', () => {
  describe('createUser', () => {
    it('should create user with hashed password', async () => {
      // Arrange
      const mockUserRepository = {
        save: jest.fn().mockResolvedValue({ id: '123', name: 'John' }),
        findByEmail: jest.fn().mockResolvedValue(null),
      };
      const mockHashService = {
        hash: jest.fn().mockResolvedValue('hashed_password'),
      };
      const userService = new UserService(mockUserRepository, mockHashService);
      const userData = {
        name: 'John',
        email: 'john@test.com',
        password: 'plaintext_password',
      };

      // Act
      const result = await userService.createUser(userData);

      // Assert
      expect(result).toEqual({ id: '123', name: 'John' });
      expect(mockHashService.hash).toHaveBeenCalledWith('plaintext_password');
      expect(mockUserRepository.save).toHaveBeenCalledWith(
        expect.objectContaining({
          name: 'John',
          email: 'john@test.com',
          password: 'hashed_password',
        })
      );
    });
  });
});
```

### Best Practices

#### Arrange Phase

```typescript
// ✅ Good: Use factories for test data
const user = createTestUser({ name: 'John', role: 'admin' });

// ❌ Bad: Inline object creation with many fields
const user = {
  id: '123',
  name: 'John',
  email: 'john@test.com',
  role: 'admin',
  createdAt: new Date(),
  // ... many more fields
};
```

#### Act Phase

```typescript
// ✅ Good: Single action, store result
const result = await paymentService.process(payment);
expect(result.success).toBe(true);

// ❌ Bad: Multiple actions
await paymentService.process(payment);
await notificationService.send(payment.userId);
await auditService.log('payment_processed');
```

#### Assert Phase

```typescript
// ✅ Good: Specific assertions
expect(result.status).toBe('success');
expect(result.data.id).toBe('123');

// ❌ Bad: Vague assertions
expect(result).toBeTruthy();
expect(result.data).toBeDefined();
```

---

## Test Fixtures

### Types of Fixtures

| Type | Purpose | Example |
|------|---------|---------|
| **Data Fixtures** | Pre-defined test data | User objects, orders |
| **State Fixtures** | System state setup | Database state, config |
| **Environment Fixtures** | External dependencies | Mock servers, containers |

### Static Fixtures (JSON)

```json
// fixtures/users.json
{
  "validUser": {
    "id": "user-001",
    "name": "John Doe",
    "email": "john@example.com",
    "role": "user",
    "status": "active"
  },
  "adminUser": {
    "id": "admin-001",
    "name": "Admin User",
    "email": "admin@example.com",
    "role": "admin",
    "status": "active"
  }
}
```

### TypeScript Fixtures

```typescript
// fixtures/users.ts
import { User } from '@/types';

export const validUser: User = {
  id: 'user-001',
  name: 'John Doe',
  email: 'john@example.com',
  role: 'user',
  status: 'active',
  createdAt: new Date('2024-01-01'),
};

export const adminUser: User = {
  id: 'admin-001',
  name: 'Admin User',
  email: 'admin@example.com',
  role: 'admin',
  status: 'active',
  createdAt: new Date('2024-01-01'),
};
```

### Playwright Fixtures

```typescript
// fixtures/pages.fixture.ts
import { test as base, Page } from '@playwright/test';
import { LoginPage } from '../pages/login.page';
import { DashboardPage } from '../pages/dashboard.page';

interface PageObjects {
  loginPage: LoginPage;
  dashboardPage: DashboardPage;
  authenticatedPage: Page;
}

export const test = base.extend<PageObjects>({
  loginPage: async ({ page }, use) => {
    await use(new LoginPage(page));
  },

  dashboardPage: async ({ page }, use) => {
    await use(new DashboardPage(page));
  },

  authenticatedPage: async ({ page }, use) => {
    // Login before test
    await page.goto('/login');
    await page.fill('[data-testid="email"]', 'test@example.com');
    await page.fill('[data-testid="password"]', 'password123');
    await page.click('[data-testid="submit"]');
    await page.waitForURL('/dashboard');

    await use(page);

    // Cleanup after test
    await page.goto('/logout');
  },
});

export { expect } from '@playwright/test';
```

---

## Factory Patterns

### Basic Factory Function

```typescript
// factories/user.factory.ts
import { User } from '@/types';

let idCounter = 0;

export function createUser(overrides: Partial<User> = {}): User {
  idCounter++;
  return {
    id: `user-${idCounter}`,
    name: 'Test User',
    email: `test${idCounter}@example.com`,
    role: 'user',
    status: 'active',
    createdAt: new Date(),
    ...overrides,
  };
}

// Usage
const user = createUser();
const admin = createUser({ role: 'admin', name: 'Admin User' });
```

### Builder Pattern

```typescript
// factories/order.builder.ts
export class OrderBuilder {
  private order: Partial<Order> = {};
  private items: OrderItem[] = [];

  constructor() {
    this.reset();
  }

  private reset(): void {
    this.order = {
      id: `order-${Date.now()}`,
      userId: 'user-1',
      status: 'pending',
      createdAt: new Date(),
    };
    this.items = [];
  }

  forUser(userId: string): this {
    this.order.userId = userId;
    return this;
  }

  withStatus(status: OrderStatus): this {
    this.order.status = status;
    return this;
  }

  addItem(item: Partial<OrderItem>): this {
    this.items.push({
      id: `item-${this.items.length + 1}`,
      productId: 'product-1',
      quantity: 1,
      price: 9.99,
      ...item,
    });
    return this;
  }

  asPaid(): this {
    this.order.status = 'paid';
    this.order.paidAt = new Date();
    return this;
  }

  asShipped(): this {
    this.order.status = 'shipped';
    this.order.shippedAt = new Date();
    return this;
  }

  build(): Order {
    const order: Order = {
      ...(this.order as Order),
      items: this.items,
      total: this.items.reduce((sum, item) => sum + item.price * item.quantity, 0),
    };
    this.reset();
    return order;
  }
}

// Usage
const builder = new OrderBuilder();

const simpleOrder = builder
  .forUser('user-123')
  .addItem({ productId: 'prod-1', price: 29.99 })
  .build();

const completedOrder = builder
  .forUser('user-456')
  .addItem({ price: 19.99 })
  .addItem({ price: 29.99 })
  .asPaid()
  .asShipped()
  .build();
```

### Factory with Traits

```typescript
type UserTrait = 'admin' | 'premium' | 'inactive' | 'verified' | 'new';

const userTraits: Record<UserTrait, Partial<User>> = {
  admin: { role: 'admin', permissions: ['read', 'write', 'delete', 'admin'] },
  premium: { subscription: 'premium', features: ['priority-support', 'analytics'] },
  inactive: { status: 'inactive', deactivatedAt: new Date() },
  verified: { emailVerified: true, verifiedAt: new Date() },
  new: { createdAt: new Date(), loginCount: 0 },
};

export function createUser(
  overrides: Partial<User> = {},
  traits: UserTrait[] = []
): User {
  const baseUser: User = {
    id: `user-${Date.now()}`,
    name: 'Test User',
    email: 'test@example.com',
    role: 'user',
    status: 'active',
    createdAt: new Date(),
  };

  // Apply traits
  const traitOverrides = traits.reduce(
    (acc, trait) => ({ ...acc, ...userTraits[trait] }),
    {}
  );

  return {
    ...baseUser,
    ...traitOverrides,
    ...overrides,
  };
}

// Usage
const regularUser = createUser();
const adminUser = createUser({}, ['admin', 'verified']);
const premiumNewUser = createUser({ name: 'Premium User' }, ['premium', 'new']);
```

### Faker Integration

```typescript
import { faker } from '@faker-js/faker';

export function createRandomUser(overrides: Partial<User> = {}): User {
  return {
    id: faker.string.uuid(),
    name: faker.person.fullName(),
    email: faker.internet.email(),
    role: faker.helpers.arrayElement(['user', 'admin']),
    status: faker.helpers.arrayElement(['active', 'inactive']),
    createdAt: faker.date.past(),
    avatar: faker.image.avatar(),
    bio: faker.lorem.paragraph(),
    ...overrides,
  };
}

export function createManyUsers(count: number): User[] {
  return Array.from({ length: count }, () => createRandomUser());
}

// Seeded random for reproducibility
export function createSeededUser(seed: number): User {
  faker.seed(seed);
  return createRandomUser();
}
```

---

## Page Object Model

### Overview

Page Object Model creates an abstraction layer over UI pages, separating page structure from test logic.

| Benefit | Description |
|---------|-------------|
| Maintainability | Change selectors in one place |
| Readability | Tests read like user actions |
| Reusability | Share page logic across tests |
| Abstraction | Hide implementation details |

### Basic Page Object

```typescript
// pages/login.page.ts
import { Page, Locator } from '@playwright/test';

export class LoginPage {
  readonly page: Page;
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly loginButton: Locator;
  readonly errorMessage: Locator;

  constructor(page: Page) {
    this.page = page;
    this.emailInput = page.locator('[data-testid="email-input"]');
    this.passwordInput = page.locator('[data-testid="password-input"]');
    this.loginButton = page.locator('[data-testid="login-button"]');
    this.errorMessage = page.locator('[data-testid="error-message"]');
  }

  async goto(): Promise<void> {
    await this.page.goto('/login');
  }

  async login(email: string, password: string): Promise<void> {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.loginButton.click();
  }

  async getErrorMessage(): Promise<string> {
    return this.errorMessage.textContent() ?? '';
  }
}
```

### Using Page Objects in Tests

```typescript
import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/login.page';
import { DashboardPage } from '../pages/dashboard.page';

test.describe('Authentication', () => {
  let loginPage: LoginPage;
  let dashboardPage: DashboardPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    dashboardPage = new DashboardPage(page);
    await loginPage.goto();
  });

  test('should login with valid credentials', async () => {
    await loginPage.login('user@example.com', 'password123');

    await expect(dashboardPage.welcomeMessage).toBeVisible();
    await expect(dashboardPage.welcomeMessage).toContainText('Welcome');
  });

  test('should show error for invalid credentials', async () => {
    await loginPage.login('wrong@example.com', 'wrongpassword');

    const error = await loginPage.getErrorMessage();
    expect(error).toContain('Invalid credentials');
  });
});
```

### Component Page Objects

```typescript
// components/header.component.ts
export class HeaderComponent {
  readonly container: Locator;
  readonly logo: Locator;
  readonly searchInput: Locator;
  readonly cartButton: Locator;
  readonly userMenu: Locator;

  constructor(page: Page) {
    this.container = page.locator('header');
    this.logo = this.container.locator('[data-testid="logo"]');
    this.searchInput = this.container.locator('[data-testid="search-input"]');
    this.cartButton = this.container.locator('[data-testid="cart-button"]');
    this.userMenu = this.container.locator('[data-testid="user-menu"]');
  }

  async search(query: string): Promise<void> {
    await this.searchInput.fill(query);
    await this.searchInput.press('Enter');
  }

  async openCart(): Promise<void> {
    await this.cartButton.click();
  }

  async logout(): Promise<void> {
    await this.userMenu.click();
    await this.container.locator('button:has-text("Logout")').click();
  }
}
```

### Page with Components

```typescript
// pages/product-list.page.ts
export class ProductListPage {
  readonly page: Page;
  readonly header: HeaderComponent;
  readonly productGrid: Locator;

  constructor(page: Page) {
    this.page = page;
    this.header = new HeaderComponent(page);
    this.productGrid = page.locator('[data-testid="product-grid"]');
  }

  async goto(category?: string): Promise<void> {
    const url = category ? `/products?category=${category}` : '/products';
    await this.page.goto(url);
  }

  async searchProducts(query: string): Promise<void> {
    await this.header.search(query);
    await this.page.waitForLoadState('networkidle');
  }
}
```

### Locator Best Practices

```typescript
// ✅ Good: Use data-testid
readonly submitButton = page.locator('[data-testid="submit-button"]');

// ✅ Good: Use accessible roles
readonly submitButton = page.getByRole('button', { name: 'Submit' });

// ❌ Bad: Use CSS classes
readonly submitButton = page.locator('.btn.btn-primary.submit');

// ❌ Bad: Use XPath
readonly submitButton = page.locator('//button[@class="submit"]');
```

---

## Test Data Management

### Organization Structure

```
test/
├── fixtures/
│   ├── data/
│   │   ├── users.json
│   │   ├── orders.json
│   │   └── products.json
│   ├── factories/
│   │   ├── user.factory.ts
│   │   ├── order.factory.ts
│   │   └── product.factory.ts
│   ├── builders/
│   │   ├── user.builder.ts
│   │   └── order.builder.ts
│   └── mocks/
│       ├── api.handlers.ts
│       └── services.ts
```

### Database Seeding

```typescript
// fixtures/database.ts
import { PrismaClient } from '@prisma/client';
import { createUser } from '../factories/user.factory';
import { createOrder } from '../factories/order.factory';

const prisma = new PrismaClient();

export async function seedTestData() {
  const users = await Promise.all([
    prisma.user.create({ data: createUser({ role: 'admin' }) }),
    prisma.user.create({ data: createUser() }),
  ]);

  const orders = await Promise.all(
    users.flatMap(user =>
      Array.from({ length: 3 }, () =>
        prisma.order.create({
          data: createOrder({ userId: user.id }),
        })
      )
    )
  );

  return { users, orders };
}

export async function cleanTestData() {
  await prisma.$transaction([
    prisma.orderItem.deleteMany(),
    prisma.order.deleteMany(),
    prisma.user.deleteMany(),
  ]);
}
```

### Best Practices Summary

| Do | Don't |
|----|-------|
| Use factories for dynamic data | Hard-code test data |
| Reset fixtures between tests | Share mutable state |
| Keep fixtures close to tests | Put fixtures far from usage |
| Use meaningful fixture names | Use generic names |
| Document fixture purpose | Leave fixtures unexplained |
| Use data-testid selectors | Use fragile CSS selectors |
| Keep page objects focused | Create god page objects |
| Return data, assert in tests | Assert inside page objects |
