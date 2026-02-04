---
name: repository-pattern
description: Repository pattern for data access abstraction
category: architecture/design-patterns/structural
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Repository Pattern

## Overview

The Repository pattern mediates between the domain and data mapping layers,
acting like an in-memory collection of domain objects. It provides a clean
separation between data access logic and business logic.

## Basic Repository Interface

```typescript
// Generic repository interface
interface Repository<T, ID> {
  findById(id: ID): Promise<T | null>;
  findAll(): Promise<T[]>;
  save(entity: T): Promise<T>;
  delete(id: ID): Promise<void>;
  exists(id: ID): Promise<boolean>;
}

// Domain-specific repository
interface UserRepository extends Repository<User, string> {
  findByEmail(email: string): Promise<User | null>;
  findByRole(role: UserRole): Promise<User[]>;
  findActive(): Promise<User[]>;
}

interface OrderRepository extends Repository<Order, string> {
  findByCustomerId(customerId: string): Promise<Order[]>;
  findByStatus(status: OrderStatus): Promise<Order[]>;
  findByDateRange(start: Date, end: Date): Promise<Order[]>;
}
```

## Implementation

### In-Memory Repository (Testing)

```typescript
class InMemoryUserRepository implements UserRepository {
  private users: Map<string, User> = new Map();

  async findById(id: string): Promise<User | null> {
    return this.users.get(id) || null;
  }

  async findAll(): Promise<User[]> {
    return Array.from(this.users.values());
  }

  async save(user: User): Promise<User> {
    this.users.set(user.id, user);
    return user;
  }

  async delete(id: string): Promise<void> {
    this.users.delete(id);
  }

  async exists(id: string): Promise<boolean> {
    return this.users.has(id);
  }

  async findByEmail(email: string): Promise<User | null> {
    return Array.from(this.users.values()).find(u => u.email === email) || null;
  }

  async findByRole(role: UserRole): Promise<User[]> {
    return Array.from(this.users.values()).filter(u => u.role === role);
  }

  async findActive(): Promise<User[]> {
    return Array.from(this.users.values()).filter(u => u.isActive);
  }

  // Test helpers
  clear(): void {
    this.users.clear();
  }

  seed(users: User[]): void {
    users.forEach(u => this.users.set(u.id, u));
  }
}
```

### SQL Repository

```typescript
class PostgresUserRepository implements UserRepository {
  constructor(private readonly db: Database) {}

  async findById(id: string): Promise<User | null> {
    const row = await this.db.queryOne<UserRow>(
      'SELECT * FROM users WHERE id = $1',
      [id]
    );
    return row ? this.toDomain(row) : null;
  }

  async findAll(): Promise<User[]> {
    const rows = await this.db.query<UserRow>(
      'SELECT * FROM users ORDER BY created_at DESC'
    );
    return rows.map(this.toDomain);
  }

  async save(user: User): Promise<User> {
    const row = this.toRow(user);

    await this.db.query(
      `INSERT INTO users (id, email, name, role, is_active, created_at, updated_at)
       VALUES ($1, $2, $3, $4, $5, $6, $7)
       ON CONFLICT (id) DO UPDATE SET
         email = $2, name = $3, role = $4, is_active = $5, updated_at = $7`,
      [row.id, row.email, row.name, row.role, row.is_active, row.created_at, new Date()]
    );

    return user;
  }

  async delete(id: string): Promise<void> {
    await this.db.query('DELETE FROM users WHERE id = $1', [id]);
  }

  async exists(id: string): Promise<boolean> {
    const result = await this.db.queryOne<{ exists: boolean }>(
      'SELECT EXISTS(SELECT 1 FROM users WHERE id = $1)',
      [id]
    );
    return result?.exists ?? false;
  }

  async findByEmail(email: string): Promise<User | null> {
    const row = await this.db.queryOne<UserRow>(
      'SELECT * FROM users WHERE email = $1',
      [email]
    );
    return row ? this.toDomain(row) : null;
  }

  async findByRole(role: UserRole): Promise<User[]> {
    const rows = await this.db.query<UserRow>(
      'SELECT * FROM users WHERE role = $1',
      [role]
    );
    return rows.map(this.toDomain);
  }

  async findActive(): Promise<User[]> {
    const rows = await this.db.query<UserRow>(
      'SELECT * FROM users WHERE is_active = true'
    );
    return rows.map(this.toDomain);
  }

  private toDomain(row: UserRow): User {
    return new User(
      row.id,
      row.email,
      row.name,
      row.role as UserRole,
      row.is_active,
      row.created_at,
      row.updated_at
    );
  }

  private toRow(user: User): UserRow {
    return {
      id: user.id,
      email: user.email,
      name: user.name,
      role: user.role,
      is_active: user.isActive,
      created_at: user.createdAt,
      updated_at: user.updatedAt,
    };
  }
}
```

### ORM Repository (TypeORM)

```typescript
class TypeORMUserRepository implements UserRepository {
  constructor(
    private readonly repository: TypeORMRepository<UserEntity>
  ) {}

  async findById(id: string): Promise<User | null> {
    const entity = await this.repository.findOne({ where: { id } });
    return entity ? this.toDomain(entity) : null;
  }

  async findAll(): Promise<User[]> {
    const entities = await this.repository.find({
      order: { createdAt: 'DESC' }
    });
    return entities.map(this.toDomain);
  }

  async save(user: User): Promise<User> {
    const entity = this.toEntity(user);
    const saved = await this.repository.save(entity);
    return this.toDomain(saved);
  }

  async delete(id: string): Promise<void> {
    await this.repository.delete(id);
  }

  async exists(id: string): Promise<boolean> {
    const count = await this.repository.count({ where: { id } });
    return count > 0;
  }

  async findByEmail(email: string): Promise<User | null> {
    const entity = await this.repository.findOne({ where: { email } });
    return entity ? this.toDomain(entity) : null;
  }

  async findByRole(role: UserRole): Promise<User[]> {
    const entities = await this.repository.find({ where: { role } });
    return entities.map(this.toDomain);
  }

  async findActive(): Promise<User[]> {
    const entities = await this.repository.find({ where: { isActive: true } });
    return entities.map(this.toDomain);
  }

  private toDomain(entity: UserEntity): User {
    return new User(
      entity.id,
      entity.email,
      entity.name,
      entity.role,
      entity.isActive,
      entity.createdAt,
      entity.updatedAt
    );
  }

  private toEntity(user: User): UserEntity {
    const entity = new UserEntity();
    entity.id = user.id;
    entity.email = user.email;
    entity.name = user.name;
    entity.role = user.role;
    entity.isActive = user.isActive;
    entity.createdAt = user.createdAt;
    entity.updatedAt = user.updatedAt;
    return entity;
  }
}
```

## Specification Pattern

```typescript
// Specification interface
interface Specification<T> {
  isSatisfiedBy(entity: T): boolean;
  toSQL(): { sql: string; params: any[] };
}

// Specifications
class UserIsActiveSpec implements Specification<User> {
  isSatisfiedBy(user: User): boolean {
    return user.isActive;
  }

  toSQL(): { sql: string; params: any[] } {
    return { sql: 'is_active = true', params: [] };
  }
}

class UserHasRoleSpec implements Specification<User> {
  constructor(private role: UserRole) {}

  isSatisfiedBy(user: User): boolean {
    return user.role === this.role;
  }

  toSQL(): { sql: string; params: any[] } {
    return { sql: 'role = $1', params: [this.role] };
  }
}

class UserCreatedAfterSpec implements Specification<User> {
  constructor(private date: Date) {}

  isSatisfiedBy(user: User): boolean {
    return user.createdAt > this.date;
  }

  toSQL(): { sql: string; params: any[] } {
    return { sql: 'created_at > $1', params: [this.date] };
  }
}

// Composite specifications
class AndSpecification<T> implements Specification<T> {
  constructor(private specs: Specification<T>[]) {}

  isSatisfiedBy(entity: T): boolean {
    return this.specs.every(spec => spec.isSatisfiedBy(entity));
  }

  toSQL(): { sql: string; params: any[] } {
    const parts = this.specs.map((spec, i) => {
      const { sql, params } = spec.toSQL();
      return { sql: this.renumberParams(sql, i), params };
    });

    return {
      sql: parts.map(p => `(${p.sql})`).join(' AND '),
      params: parts.flatMap(p => p.params),
    };
  }

  private renumberParams(sql: string, offset: number): string {
    // Renumber $1, $2 etc. based on offset
    return sql.replace(/\$(\d+)/g, (_, num) => `$${parseInt(num) + offset}`);
  }
}

// Repository with specification support
interface SpecificationRepository<T, ID> extends Repository<T, ID> {
  findBySpec(spec: Specification<T>): Promise<T[]>;
  countBySpec(spec: Specification<T>): Promise<number>;
}

class PostgresUserRepository implements SpecificationRepository<User, string> {
  // ... basic methods ...

  async findBySpec(spec: Specification<User>): Promise<User[]> {
    const { sql, params } = spec.toSQL();
    const rows = await this.db.query<UserRow>(
      `SELECT * FROM users WHERE ${sql}`,
      params
    );
    return rows.map(this.toDomain);
  }

  async countBySpec(spec: Specification<User>): Promise<number> {
    const { sql, params } = spec.toSQL();
    const result = await this.db.queryOne<{ count: number }>(
      `SELECT COUNT(*) as count FROM users WHERE ${sql}`,
      params
    );
    return result?.count ?? 0;
  }
}

// Usage
const activeAdmins = await userRepository.findBySpec(
  new AndSpecification([
    new UserIsActiveSpec(),
    new UserHasRoleSpec('admin'),
    new UserCreatedAfterSpec(new Date('2024-01-01')),
  ])
);
```

## Unit of Work Pattern

```typescript
interface UnitOfWork {
  userRepository: UserRepository;
  orderRepository: OrderRepository;
  commit(): Promise<void>;
  rollback(): Promise<void>;
}

class PostgresUnitOfWork implements UnitOfWork {
  private connection: Connection;
  private _userRepository: UserRepository;
  private _orderRepository: OrderRepository;

  constructor(private pool: Pool) {}

  async begin(): Promise<void> {
    this.connection = await this.pool.connect();
    await this.connection.query('BEGIN');
  }

  get userRepository(): UserRepository {
    if (!this._userRepository) {
      this._userRepository = new PostgresUserRepository(this.connection);
    }
    return this._userRepository;
  }

  get orderRepository(): OrderRepository {
    if (!this._orderRepository) {
      this._orderRepository = new PostgresOrderRepository(this.connection);
    }
    return this._orderRepository;
  }

  async commit(): Promise<void> {
    try {
      await this.connection.query('COMMIT');
    } finally {
      this.connection.release();
    }
  }

  async rollback(): Promise<void> {
    try {
      await this.connection.query('ROLLBACK');
    } finally {
      this.connection.release();
    }
  }
}

// Usage
async function transferOrder(userId: string, orderId: string): Promise<void> {
  const uow = new PostgresUnitOfWork(pool);
  await uow.begin();

  try {
    const user = await uow.userRepository.findById(userId);
    const order = await uow.orderRepository.findById(orderId);

    if (!user || !order) {
      throw new Error('Not found');
    }

    order.assignTo(user);

    await uow.orderRepository.save(order);
    await uow.commit();
  } catch (error) {
    await uow.rollback();
    throw error;
  }
}
```

## Caching Repository Decorator

```typescript
class CachedUserRepository implements UserRepository {
  constructor(
    private readonly repository: UserRepository,
    private readonly cache: Cache,
    private readonly ttl: number = 300
  ) {}

  async findById(id: string): Promise<User | null> {
    const cacheKey = `user:${id}`;
    const cached = await this.cache.get<User>(cacheKey);

    if (cached) return cached;

    const user = await this.repository.findById(id);
    if (user) {
      await this.cache.set(cacheKey, user, this.ttl);
    }
    return user;
  }

  async save(user: User): Promise<User> {
    const saved = await this.repository.save(user);
    await this.cache.delete(`user:${user.id}`);
    await this.cache.delete(`user:email:${user.email}`);
    return saved;
  }

  async findByEmail(email: string): Promise<User | null> {
    const cacheKey = `user:email:${email}`;
    const cached = await this.cache.get<User>(cacheKey);

    if (cached) return cached;

    const user = await this.repository.findByEmail(email);
    if (user) {
      await this.cache.set(cacheKey, user, this.ttl);
    }
    return user;
  }

  // ... delegate other methods ...
}
```

## Benefits

| Benefit | Description |
|---------|-------------|
| Testability | Easy to mock for unit tests |
| Separation | Data access isolated from business logic |
| Flexibility | Swap storage implementations |
| Domain Focus | Domain objects stay pure |
| Query Reuse | Common queries defined once |

## When to Use

- Complex domain models
- Multiple data sources
- Need for unit testing
- ORM abstraction needed
- CQRS/Clean Architecture
