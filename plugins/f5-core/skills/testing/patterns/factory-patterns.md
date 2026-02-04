---
name: factory-patterns
description: Test data factory patterns for maintainable tests
category: testing/patterns
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Factory Patterns for Testing

## Overview

Factory patterns help create test data in a consistent, maintainable way.
They reduce duplication and make tests more readable.

## Basic Factory Function

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
const inactive = createUser({ status: 'inactive' });
```

## Builder Pattern

```typescript
// factories/order.builder.ts
import { Order, OrderItem, OrderStatus } from '@/types';

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

  withId(id: string): this {
    this.order.id = id;
    return this;
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

  addItems(count: number, itemTemplate: Partial<OrderItem> = {}): this {
    for (let i = 0; i < count; i++) {
      this.addItem(itemTemplate);
    }
    return this;
  }

  withShipping(address: Address): this {
    this.order.shippingAddress = address;
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

  asDelivered(): this {
    this.order.status = 'delivered';
    this.order.deliveredAt = new Date();
    return this;
  }

  asCancelled(): this {
    this.order.status = 'cancelled';
    this.order.cancelledAt = new Date();
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
  .addItems(3, { price: 19.99 })
  .asPaid()
  .asShipped()
  .asDelivered()
  .build();

const cancelledOrder = builder
  .forUser('user-789')
  .addItem({ productId: 'prod-2', quantity: 2 })
  .asCancelled()
  .build();
```

## Factory with Traits

```typescript
// factories/user.factory.ts
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
    emailVerified: false,
    subscription: 'free',
    permissions: ['read'],
    features: [],
    loginCount: 1,
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
const inactiveAdmin = createUser({}, ['admin', 'inactive']);
```

## Factory with Sequences

```typescript
// factories/sequences.ts
type SequenceGenerator<T> = () => T;

const sequences: Map<string, SequenceGenerator<any>> = new Map();
const sequenceCounters: Map<string, number> = new Map();

export function defineSequence<T>(name: string, generator: (n: number) => T): void {
  sequences.set(name, () => {
    const count = (sequenceCounters.get(name) || 0) + 1;
    sequenceCounters.set(name, count);
    return generator(count);
  });
}

export function generate<T>(name: string): T {
  const generator = sequences.get(name);
  if (!generator) throw new Error(`Sequence ${name} not defined`);
  return generator();
}

export function resetSequences(): void {
  sequenceCounters.clear();
}

// Define sequences
defineSequence('userId', n => `user-${n}`);
defineSequence('email', n => `user${n}@example.com`);
defineSequence('orderId', n => `ORD-${String(n).padStart(6, '0')}`);

// Factory using sequences
export function createUser(overrides: Partial<User> = {}): User {
  return {
    id: generate('userId'),
    email: generate('email'),
    name: 'Test User',
    role: 'user',
    status: 'active',
    createdAt: new Date(),
    ...overrides,
  };
}

// Usage
const user1 = createUser(); // { id: 'user-1', email: 'user1@example.com', ... }
const user2 = createUser(); // { id: 'user-2', email: 'user2@example.com', ... }

// Reset in beforeEach
beforeEach(() => {
  resetSequences();
});
```

## Factory with Relationships

```typescript
// factories/index.ts
import { User, Order, OrderItem, Product } from '@/types';

// Product factory
export function createProduct(overrides: Partial<Product> = {}): Product {
  return {
    id: `product-${Date.now()}`,
    name: 'Test Product',
    price: 29.99,
    stock: 100,
    category: 'general',
    ...overrides,
  };
}

// User factory
export function createUser(overrides: Partial<User> = {}): User {
  return {
    id: `user-${Date.now()}`,
    name: 'Test User',
    email: 'test@example.com',
    role: 'user',
    status: 'active',
    createdAt: new Date(),
    ...overrides,
  };
}

// Order factory with relationships
interface OrderFactoryOptions {
  user?: User;
  products?: Product[];
  itemCount?: number;
  overrides?: Partial<Order>;
}

export function createOrder(options: OrderFactoryOptions = {}): {
  order: Order;
  user: User;
  products: Product[];
} {
  // Create or use provided user
  const user = options.user ?? createUser();

  // Create or use provided products
  const products = options.products ?? [createProduct()];

  // Create order items
  const items: OrderItem[] = [];
  const itemCount = options.itemCount ?? products.length;

  for (let i = 0; i < itemCount; i++) {
    const product = products[i % products.length];
    items.push({
      id: `item-${i + 1}`,
      productId: product.id,
      productName: product.name,
      quantity: 1,
      price: product.price,
    });
  }

  // Calculate total
  const total = items.reduce((sum, item) => sum + item.price * item.quantity, 0);

  // Create order
  const order: Order = {
    id: `order-${Date.now()}`,
    userId: user.id,
    items,
    total,
    status: 'pending',
    createdAt: new Date(),
    ...options.overrides,
  };

  return { order, user, products };
}

// Usage
const { order, user, products } = createOrder();

const customOrder = createOrder({
  user: createUser({ name: 'Custom User' }),
  products: [
    createProduct({ name: 'Product A', price: 10 }),
    createProduct({ name: 'Product B', price: 20 }),
  ],
  itemCount: 5,
  overrides: { status: 'paid' },
});
```

## Async Factory (Database)

```typescript
// factories/database-factories.ts
import { PrismaClient, User, Order } from '@prisma/client';

const prisma = new PrismaClient();

export async function createDbUser(overrides: Partial<User> = {}): Promise<User> {
  return prisma.user.create({
    data: {
      email: `test-${Date.now()}@example.com`,
      name: 'Test User',
      role: 'user',
      status: 'active',
      ...overrides,
    },
  });
}

export async function createDbOrder(
  userId: string,
  items: Array<{ productId: string; quantity: number }>
): Promise<Order> {
  // Get product prices
  const productIds = items.map(i => i.productId);
  const products = await prisma.product.findMany({
    where: { id: { in: productIds } },
  });

  const productPrices = new Map(products.map(p => [p.id, p.price]));

  // Create order with items
  return prisma.order.create({
    data: {
      userId,
      status: 'pending',
      items: {
        create: items.map(item => ({
          productId: item.productId,
          quantity: item.quantity,
          price: productPrices.get(item.productId) || 0,
        })),
      },
    },
    include: { items: true },
  });
}

// Test helpers
export async function seedTestUsers(count: number): Promise<User[]> {
  return Promise.all(
    Array.from({ length: count }, (_, i) =>
      createDbUser({ name: `User ${i + 1}` })
    )
  );
}

// Usage
describe('Order Service', () => {
  let user: User;
  let products: Product[];

  beforeEach(async () => {
    user = await createDbUser();
    products = await seedProducts(3);
  });

  it('should create order', async () => {
    const order = await createDbOrder(user.id, [
      { productId: products[0].id, quantity: 2 },
    ]);

    expect(order.userId).toBe(user.id);
    expect(order.items).toHaveLength(1);
  });
});
```

## Factory Registry

```typescript
// factories/registry.ts
type FactoryFn<T> = (overrides?: Partial<T>) => T;

class FactoryRegistry {
  private factories: Map<string, FactoryFn<any>> = new Map();

  register<T>(name: string, factory: FactoryFn<T>): void {
    this.factories.set(name, factory);
  }

  create<T>(name: string, overrides?: Partial<T>): T {
    const factory = this.factories.get(name);
    if (!factory) {
      throw new Error(`Factory '${name}' not registered`);
    }
    return factory(overrides);
  }

  createMany<T>(name: string, count: number, overrides?: Partial<T>): T[] {
    return Array.from({ length: count }, () => this.create<T>(name, overrides));
  }
}

export const factory = new FactoryRegistry();

// Register factories
factory.register<User>('user', (o = {}) => ({
  id: `user-${Date.now()}`,
  name: 'Test User',
  email: 'test@example.com',
  ...o,
}));

factory.register<Product>('product', (o = {}) => ({
  id: `prod-${Date.now()}`,
  name: 'Test Product',
  price: 9.99,
  ...o,
}));

// Usage
const user = factory.create<User>('user', { name: 'Custom' });
const products = factory.createMany<Product>('product', 5);
```

## Best Practices

| Do | Don't |
|----|-------|
| Use meaningful defaults | Require all fields |
| Allow easy overrides | Make customization hard |
| Keep factories simple | Add too much logic |
| Create related data together | Orphan relationships |
| Use sequences for uniqueness | Hard-code IDs |
| Reset state between tests | Share mutable state |

## Related Topics

- [Test Fixtures](./test-fixtures.md)
- [Test Doubles](../unit-testing/test-doubles.md)
- [Database Testing](../integration-testing/database-testing.md)
