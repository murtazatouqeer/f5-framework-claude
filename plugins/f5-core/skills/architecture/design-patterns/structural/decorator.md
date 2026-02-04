---
name: decorator-pattern
description: Decorator pattern for adding behavior dynamically
category: architecture/design-patterns/structural
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Decorator Pattern

## Overview

The Decorator pattern attaches additional responsibilities to an object
dynamically. Decorators provide a flexible alternative to subclassing
for extending functionality.

## Problem

```typescript
// ❌ Inheritance explosion for combinations
class Coffee { cost(): number { return 5; } }
class CoffeeWithMilk extends Coffee { cost(): number { return 6; } }
class CoffeeWithSugar extends Coffee { cost(): number { return 5.5; } }
class CoffeeWithMilkAndSugar extends Coffee { cost(): number { return 6.5; } }
class CoffeeWithMilkAndWhip extends Coffee { cost(): number { return 7; } }
// ... more combinations

// What about Milk + Sugar + Whip + Chocolate + ...?
// Leads to class explosion!
```

## Solution: Decorator

```typescript
// ✅ Base interface
interface Beverage {
  getDescription(): string;
  cost(): number;
}

// Concrete component
class Espresso implements Beverage {
  getDescription(): string {
    return 'Espresso';
  }

  cost(): number {
    return 2.00;
  }
}

class HouseBlend implements Beverage {
  getDescription(): string {
    return 'House Blend Coffee';
  }

  cost(): number {
    return 1.50;
  }
}

// Base decorator
abstract class CondimentDecorator implements Beverage {
  constructor(protected beverage: Beverage) {}

  abstract getDescription(): string;
  abstract cost(): number;
}

// Concrete decorators
class Milk extends CondimentDecorator {
  getDescription(): string {
    return `${this.beverage.getDescription()}, Milk`;
  }

  cost(): number {
    return this.beverage.cost() + 0.50;
  }
}

class Mocha extends CondimentDecorator {
  getDescription(): string {
    return `${this.beverage.getDescription()}, Mocha`;
  }

  cost(): number {
    return this.beverage.cost() + 0.75;
  }
}

class Whip extends CondimentDecorator {
  getDescription(): string {
    return `${this.beverage.getDescription()}, Whip`;
  }

  cost(): number {
    return this.beverage.cost() + 0.30;
  }
}

// Usage - compose any combination
let beverage: Beverage = new Espresso();
beverage = new Milk(beverage);
beverage = new Mocha(beverage);
beverage = new Whip(beverage);

console.log(beverage.getDescription()); // "Espresso, Milk, Mocha, Whip"
console.log(beverage.cost());           // 3.55
```

## Real-World Examples

### HTTP Client with Decorators

```typescript
// Base interface
interface HttpClient {
  request<T>(config: RequestConfig): Promise<Response<T>>;
}

// Simple implementation
class BaseHttpClient implements HttpClient {
  async request<T>(config: RequestConfig): Promise<Response<T>> {
    const response = await fetch(config.url, {
      method: config.method,
      headers: config.headers,
      body: config.body ? JSON.stringify(config.body) : undefined,
    });
    return { data: await response.json(), status: response.status };
  }
}

// Logging decorator
class LoggingHttpClient implements HttpClient {
  constructor(
    private readonly client: HttpClient,
    private readonly logger: Logger
  ) {}

  async request<T>(config: RequestConfig): Promise<Response<T>> {
    this.logger.info(`HTTP ${config.method} ${config.url}`);
    const start = Date.now();

    try {
      const response = await this.client.request<T>(config);
      this.logger.info(`HTTP ${config.method} ${config.url} - ${response.status} (${Date.now() - start}ms)`);
      return response;
    } catch (error) {
      this.logger.error(`HTTP ${config.method} ${config.url} failed`, error);
      throw error;
    }
  }
}

// Retry decorator
class RetryHttpClient implements HttpClient {
  constructor(
    private readonly client: HttpClient,
    private readonly maxRetries: number = 3,
    private readonly delay: number = 1000
  ) {}

  async request<T>(config: RequestConfig): Promise<Response<T>> {
    let lastError: Error;

    for (let attempt = 1; attempt <= this.maxRetries; attempt++) {
      try {
        return await this.client.request<T>(config);
      } catch (error) {
        lastError = error as Error;
        if (attempt < this.maxRetries) {
          await this.sleep(this.delay * attempt);
        }
      }
    }

    throw lastError!;
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Auth decorator
class AuthHttpClient implements HttpClient {
  constructor(
    private readonly client: HttpClient,
    private readonly tokenProvider: () => Promise<string>
  ) {}

  async request<T>(config: RequestConfig): Promise<Response<T>> {
    const token = await this.tokenProvider();
    const authConfig = {
      ...config,
      headers: {
        ...config.headers,
        Authorization: `Bearer ${token}`,
      },
    };
    return this.client.request<T>(authConfig);
  }
}

// Caching decorator
class CachingHttpClient implements HttpClient {
  private cache = new Map<string, { data: any; expires: number }>();

  constructor(
    private readonly client: HttpClient,
    private readonly ttl: number = 60000
  ) {}

  async request<T>(config: RequestConfig): Promise<Response<T>> {
    // Only cache GET requests
    if (config.method !== 'GET') {
      return this.client.request<T>(config);
    }

    const cacheKey = `${config.method}:${config.url}`;
    const cached = this.cache.get(cacheKey);

    if (cached && cached.expires > Date.now()) {
      return { data: cached.data, status: 200, cached: true };
    }

    const response = await this.client.request<T>(config);
    this.cache.set(cacheKey, { data: response.data, expires: Date.now() + this.ttl });
    return response;
  }
}

// Usage - compose decorators
let client: HttpClient = new BaseHttpClient();
client = new CachingHttpClient(client, 30000);
client = new RetryHttpClient(client, 3);
client = new AuthHttpClient(client, () => getAccessToken());
client = new LoggingHttpClient(client, logger);

// All requests now have: logging, auth, retry, and caching
const response = await client.request({ method: 'GET', url: '/api/users' });
```

### Stream Processing Decorators

```typescript
// Base interface
interface DataStream {
  read(): Promise<string>;
  write(data: string): Promise<void>;
}

// File stream
class FileStream implements DataStream {
  constructor(private readonly path: string) {}

  async read(): Promise<string> {
    return fs.promises.readFile(this.path, 'utf-8');
  }

  async write(data: string): Promise<void> {
    await fs.promises.writeFile(this.path, data, 'utf-8');
  }
}

// Compression decorator
class GzipStream implements DataStream {
  constructor(private readonly stream: DataStream) {}

  async read(): Promise<string> {
    const compressed = await this.stream.read();
    return zlib.gunzipSync(Buffer.from(compressed, 'base64')).toString();
  }

  async write(data: string): Promise<void> {
    const compressed = zlib.gzipSync(data).toString('base64');
    await this.stream.write(compressed);
  }
}

// Encryption decorator
class EncryptedStream implements DataStream {
  constructor(
    private readonly stream: DataStream,
    private readonly key: string
  ) {}

  async read(): Promise<string> {
    const encrypted = await this.stream.read();
    return this.decrypt(encrypted);
  }

  async write(data: string): Promise<void> {
    const encrypted = this.encrypt(data);
    await this.stream.write(encrypted);
  }

  private encrypt(data: string): string {
    // AES encryption
    const cipher = crypto.createCipher('aes-256-cbc', this.key);
    return cipher.update(data, 'utf8', 'hex') + cipher.final('hex');
  }

  private decrypt(data: string): string {
    const decipher = crypto.createDecipher('aes-256-cbc', this.key);
    return decipher.update(data, 'hex', 'utf8') + decipher.final('utf8');
  }
}

// Usage
let stream: DataStream = new FileStream('/data/sensitive.txt');
stream = new GzipStream(stream);      // Compress before encrypting
stream = new EncryptedStream(stream, secretKey);  // Encrypt

await stream.write('Sensitive data');  // Compressed, then encrypted
const data = await stream.read();      // Decrypted, then decompressed
```

### Validation Decorators

```typescript
// Base validator interface
interface Validator<T> {
  validate(value: T): ValidationResult;
}

// Simple validators
class RequiredValidator<T> implements Validator<T> {
  validate(value: T): ValidationResult {
    if (value === null || value === undefined || value === '') {
      return { valid: false, errors: ['Value is required'] };
    }
    return { valid: true, errors: [] };
  }
}

// Decorator base
abstract class ValidatorDecorator<T> implements Validator<T> {
  constructor(protected validator: Validator<T>) {}

  validate(value: T): ValidationResult {
    const result = this.validator.validate(value);
    if (!result.valid) return result;
    return this.additionalValidation(value);
  }

  protected abstract additionalValidation(value: T): ValidationResult;
}

// String length decorator
class MinLengthValidator extends ValidatorDecorator<string> {
  constructor(validator: Validator<string>, private minLength: number) {
    super(validator);
  }

  protected additionalValidation(value: string): ValidationResult {
    if (value.length < this.minLength) {
      return { valid: false, errors: [`Minimum length is ${this.minLength}`] };
    }
    return { valid: true, errors: [] };
  }
}

class MaxLengthValidator extends ValidatorDecorator<string> {
  constructor(validator: Validator<string>, private maxLength: number) {
    super(validator);
  }

  protected additionalValidation(value: string): ValidationResult {
    if (value.length > this.maxLength) {
      return { valid: false, errors: [`Maximum length is ${this.maxLength}`] };
    }
    return { valid: true, errors: [] };
  }
}

class PatternValidator extends ValidatorDecorator<string> {
  constructor(validator: Validator<string>, private pattern: RegExp, private message: string) {
    super(validator);
  }

  protected additionalValidation(value: string): ValidationResult {
    if (!this.pattern.test(value)) {
      return { valid: false, errors: [this.message] };
    }
    return { valid: true, errors: [] };
  }
}

// Usage
let passwordValidator: Validator<string> = new RequiredValidator();
passwordValidator = new MinLengthValidator(passwordValidator, 8);
passwordValidator = new MaxLengthValidator(passwordValidator, 100);
passwordValidator = new PatternValidator(
  passwordValidator,
  /[A-Z]/,
  'Must contain uppercase letter'
);
passwordValidator = new PatternValidator(
  passwordValidator,
  /[0-9]/,
  'Must contain number'
);

const result = passwordValidator.validate('weak'); // Invalid - multiple errors
```

## TypeScript Decorators (Language Feature)

```typescript
// Method decorator for logging
function log(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
  const original = descriptor.value;

  descriptor.value = async function (...args: any[]) {
    console.log(`Calling ${propertyKey} with`, args);
    const result = await original.apply(this, args);
    console.log(`${propertyKey} returned`, result);
    return result;
  };

  return descriptor;
}

// Method decorator for caching
function cached(ttl: number = 60000) {
  const cache = new Map<string, { value: any; expires: number }>();

  return function (target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const original = descriptor.value;

    descriptor.value = async function (...args: any[]) {
      const key = JSON.stringify(args);
      const entry = cache.get(key);

      if (entry && entry.expires > Date.now()) {
        return entry.value;
      }

      const result = await original.apply(this, args);
      cache.set(key, { value: result, expires: Date.now() + ttl });
      return result;
    };

    return descriptor;
  };
}

// Usage
class UserService {
  @log
  @cached(30000)
  async getUser(id: string): Promise<User> {
    // Expensive operation
    return this.repository.findById(id);
  }
}
```

## Benefits

| Benefit | Description |
|---------|-------------|
| Flexibility | Add/remove behaviors at runtime |
| Composition | Combine behaviors in any order |
| Open/Closed | Extend without modifying existing code |
| Single Responsibility | Each decorator has one behavior |

## When to Use

- Adding responsibilities dynamically
- When inheritance causes class explosion
- Stream/filter processing pipelines
- Cross-cutting concerns (logging, caching, auth)
