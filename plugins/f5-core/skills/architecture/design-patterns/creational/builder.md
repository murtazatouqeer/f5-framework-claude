---
name: builder-pattern
description: Builder pattern for complex object construction
category: architecture/design-patterns/creational
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Builder Pattern

## Overview

The Builder pattern separates the construction of a complex object from
its representation, allowing the same construction process to create
different representations.

## Problem

```typescript
// ❌ Constructor with many parameters
class Email {
  constructor(
    to: string,
    from: string,
    subject: string,
    body: string,
    cc?: string[],
    bcc?: string[],
    replyTo?: string,
    attachments?: Attachment[],
    priority?: 'high' | 'normal' | 'low',
    readReceipt?: boolean,
    headers?: Record<string, string>
  ) {
    // Hard to read, easy to mix up parameters
  }
}

// Usage - confusing parameter order
const email = new Email(
  'user@example.com',
  'noreply@company.com',
  'Welcome!',
  'Hello...',
  undefined,  // cc
  undefined,  // bcc
  undefined,  // replyTo
  undefined,  // attachments
  'high',     // priority
  true,       // readReceipt
  undefined   // headers
);
```

## Solution: Fluent Builder

```typescript
// ✅ Builder Pattern
class EmailBuilder {
  private email: Partial<EmailData> = {};

  to(address: string): this {
    this.email.to = address;
    return this;
  }

  from(address: string): this {
    this.email.from = address;
    return this;
  }

  subject(subject: string): this {
    this.email.subject = subject;
    return this;
  }

  body(content: string): this {
    this.email.body = content;
    return this;
  }

  cc(...addresses: string[]): this {
    this.email.cc = addresses;
    return this;
  }

  bcc(...addresses: string[]): this {
    this.email.bcc = addresses;
    return this;
  }

  replyTo(address: string): this {
    this.email.replyTo = address;
    return this;
  }

  attach(attachment: Attachment): this {
    this.email.attachments = this.email.attachments || [];
    this.email.attachments.push(attachment);
    return this;
  }

  priority(level: 'high' | 'normal' | 'low'): this {
    this.email.priority = level;
    return this;
  }

  requestReadReceipt(): this {
    this.email.readReceipt = true;
    return this;
  }

  header(name: string, value: string): this {
    this.email.headers = this.email.headers || {};
    this.email.headers[name] = value;
    return this;
  }

  build(): Email {
    // Validate required fields
    if (!this.email.to) throw new Error('To address is required');
    if (!this.email.from) throw new Error('From address is required');
    if (!this.email.subject) throw new Error('Subject is required');
    if (!this.email.body) throw new Error('Body is required');

    return new Email(this.email as EmailData);
  }
}

// Usage - clear and readable
const email = new EmailBuilder()
  .to('user@example.com')
  .from('noreply@company.com')
  .subject('Welcome!')
  .body('Hello, welcome to our platform!')
  .priority('high')
  .requestReadReceipt()
  .attach({ filename: 'guide.pdf', content: pdfBuffer })
  .build();
```

## Builder with Director

```typescript
// Director encapsulates common construction sequences
class EmailDirector {
  constructor(private builder: EmailBuilder) {}

  buildWelcomeEmail(user: User): Email {
    return this.builder
      .to(user.email)
      .from('welcome@company.com')
      .subject('Welcome to Our Platform!')
      .body(this.getWelcomeTemplate(user))
      .priority('normal')
      .build();
  }

  buildPasswordResetEmail(user: User, resetToken: string): Email {
    return this.builder
      .to(user.email)
      .from('security@company.com')
      .subject('Password Reset Request')
      .body(this.getPasswordResetTemplate(user, resetToken))
      .priority('high')
      .header('X-Priority', '1')
      .build();
  }

  buildOrderConfirmationEmail(user: User, order: Order): Email {
    return this.builder
      .to(user.email)
      .from('orders@company.com')
      .subject(`Order Confirmation #${order.id}`)
      .body(this.getOrderTemplate(order))
      .attach(this.generateInvoicePdf(order))
      .build();
  }

  private getWelcomeTemplate(user: User): string {
    return `Hello ${user.name}, welcome to our platform!`;
  }

  private getPasswordResetTemplate(user: User, token: string): string {
    return `Click here to reset: ${RESET_URL}?token=${token}`;
  }

  private getOrderTemplate(order: Order): string {
    return `Thank you for your order #${order.id}`;
  }

  private generateInvoicePdf(order: Order): Attachment {
    // Generate PDF
    return { filename: `invoice-${order.id}.pdf`, content: Buffer.from('') };
  }
}

// Usage
const director = new EmailDirector(new EmailBuilder());
const welcomeEmail = director.buildWelcomeEmail(user);
const resetEmail = director.buildPasswordResetEmail(user, token);
```

## Builder for Complex Objects

```typescript
// Query Builder
class QueryBuilder {
  private query: QueryParts = {
    select: ['*'],
    from: '',
    where: [],
    joins: [],
    orderBy: [],
    limit: undefined,
    offset: undefined,
  };

  select(...columns: string[]): this {
    this.query.select = columns;
    return this;
  }

  from(table: string): this {
    this.query.from = table;
    return this;
  }

  where(condition: string, ...params: any[]): this {
    this.query.where.push({ condition, params });
    return this;
  }

  andWhere(condition: string, ...params: any[]): this {
    return this.where(condition, ...params);
  }

  orWhere(condition: string, ...params: any[]): this {
    this.query.where.push({ condition, params, or: true });
    return this;
  }

  join(table: string, condition: string): this {
    this.query.joins.push({ type: 'INNER', table, condition });
    return this;
  }

  leftJoin(table: string, condition: string): this {
    this.query.joins.push({ type: 'LEFT', table, condition });
    return this;
  }

  orderBy(column: string, direction: 'ASC' | 'DESC' = 'ASC'): this {
    this.query.orderBy.push({ column, direction });
    return this;
  }

  limit(count: number): this {
    this.query.limit = count;
    return this;
  }

  offset(count: number): this {
    this.query.offset = count;
    return this;
  }

  toSQL(): { sql: string; params: any[] } {
    const params: any[] = [];
    let paramIndex = 1;

    let sql = `SELECT ${this.query.select.join(', ')}`;
    sql += ` FROM ${this.query.from}`;

    for (const join of this.query.joins) {
      sql += ` ${join.type} JOIN ${join.table} ON ${join.condition}`;
    }

    if (this.query.where.length > 0) {
      const conditions = this.query.where.map((w, i) => {
        const prefix = i === 0 ? 'WHERE' : (w.or ? 'OR' : 'AND');
        const condition = w.condition.replace(/\?/g, () => `$${paramIndex++}`);
        params.push(...w.params);
        return `${prefix} ${condition}`;
      });
      sql += ` ${conditions.join(' ')}`;
    }

    if (this.query.orderBy.length > 0) {
      sql += ` ORDER BY ${this.query.orderBy
        .map(o => `${o.column} ${o.direction}`)
        .join(', ')}`;
    }

    if (this.query.limit !== undefined) {
      sql += ` LIMIT ${this.query.limit}`;
    }

    if (this.query.offset !== undefined) {
      sql += ` OFFSET ${this.query.offset}`;
    }

    return { sql, params };
  }

  async execute<T>(db: Database): Promise<T[]> {
    const { sql, params } = this.toSQL();
    return db.query<T>(sql, params);
  }
}

// Usage
const { sql, params } = new QueryBuilder()
  .select('users.id', 'users.name', 'orders.total')
  .from('users')
  .leftJoin('orders', 'orders.user_id = users.id')
  .where('users.active = ?', true)
  .andWhere('users.created_at > ?', new Date('2024-01-01'))
  .orderBy('users.name', 'ASC')
  .limit(10)
  .offset(20)
  .toSQL();
```

## Builder for HTTP Requests

```typescript
class HttpRequestBuilder {
  private config: RequestConfig = {
    method: 'GET',
    headers: {},
    timeout: 30000,
  };

  url(url: string): this {
    this.config.url = url;
    return this;
  }

  method(method: HttpMethod): this {
    this.config.method = method;
    return this;
  }

  get(url: string): this {
    return this.method('GET').url(url);
  }

  post(url: string): this {
    return this.method('POST').url(url);
  }

  put(url: string): this {
    return this.method('PUT').url(url);
  }

  delete(url: string): this {
    return this.method('DELETE').url(url);
  }

  header(name: string, value: string): this {
    this.config.headers[name] = value;
    return this;
  }

  bearerToken(token: string): this {
    return this.header('Authorization', `Bearer ${token}`);
  }

  contentType(type: string): this {
    return this.header('Content-Type', type);
  }

  json(data: any): this {
    this.config.body = JSON.stringify(data);
    return this.contentType('application/json');
  }

  formData(data: Record<string, any>): this {
    const formData = new FormData();
    for (const [key, value] of Object.entries(data)) {
      formData.append(key, value);
    }
    this.config.body = formData;
    return this;
  }

  timeout(ms: number): this {
    this.config.timeout = ms;
    return this;
  }

  retry(count: number, delay: number = 1000): this {
    this.config.retryCount = count;
    this.config.retryDelay = delay;
    return this;
  }

  async send<T>(): Promise<Response<T>> {
    if (!this.config.url) {
      throw new Error('URL is required');
    }
    return httpClient.request<T>(this.config);
  }
}

// Usage
const response = await new HttpRequestBuilder()
  .post('https://api.example.com/users')
  .bearerToken(token)
  .json({ name: 'John', email: 'john@example.com' })
  .timeout(5000)
  .retry(3)
  .send<User>();
```

## Step Builder (Type-Safe)

```typescript
// Enforce required fields at compile time
interface EmailBuilderWithTo {
  from(address: string): EmailBuilderWithFrom;
}

interface EmailBuilderWithFrom {
  subject(subject: string): EmailBuilderWithSubject;
}

interface EmailBuilderWithSubject {
  body(content: string): EmailBuilderComplete;
}

interface EmailBuilderComplete {
  cc(...addresses: string[]): EmailBuilderComplete;
  bcc(...addresses: string[]): EmailBuilderComplete;
  priority(level: 'high' | 'normal' | 'low'): EmailBuilderComplete;
  build(): Email;
}

class StepEmailBuilder implements
  EmailBuilderWithTo,
  EmailBuilderWithFrom,
  EmailBuilderWithSubject,
  EmailBuilderComplete
{
  private data: Partial<EmailData> = {};

  private constructor() {}

  static create(): { to(address: string): EmailBuilderWithTo } {
    const builder = new StepEmailBuilder();
    return {
      to: (address: string) => builder.to(address),
    };
  }

  to(address: string): EmailBuilderWithFrom {
    this.data.to = address;
    return this;
  }

  from(address: string): EmailBuilderWithSubject {
    this.data.from = address;
    return this;
  }

  subject(subject: string): EmailBuilderComplete {
    this.data.subject = subject;
    return this;
  }

  body(content: string): EmailBuilderComplete {
    this.data.body = content;
    return this;
  }

  cc(...addresses: string[]): EmailBuilderComplete {
    this.data.cc = addresses;
    return this;
  }

  bcc(...addresses: string[]): EmailBuilderComplete {
    this.data.bcc = addresses;
    return this;
  }

  priority(level: 'high' | 'normal' | 'low'): EmailBuilderComplete {
    this.data.priority = level;
    return this;
  }

  build(): Email {
    return new Email(this.data as EmailData);
  }
}

// Usage - compile-time enforcement of required fields
const email = StepEmailBuilder.create()
  .to('user@example.com')    // Must call to() first
  .from('noreply@co.com')    // Then from()
  .subject('Hello')          // Then subject()
  .body('Content')           // Then body()
  .priority('high')          // Optional
  .build();
```

## Benefits

| Benefit | Description |
|---------|-------------|
| Readability | Clear, fluent API |
| Flexibility | Optional parameters without constructor overloads |
| Validation | Centralized validation in build() |
| Immutability | Can create immutable objects |
| Testability | Easy to create test fixtures |
