---
name: singleton-pattern
description: Singleton pattern and its alternatives
category: architecture/design-patterns/creational
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Singleton Pattern

## Overview

The Singleton pattern ensures a class has only one instance and provides
a global point of access to it. **Use sparingly** - often considered an
anti-pattern in modern development.

## Classic Singleton

```typescript
// Basic Singleton (Not Recommended)
class Logger {
  private static instance: Logger;

  private constructor() {
    // Private constructor prevents direct instantiation
  }

  static getInstance(): Logger {
    if (!Logger.instance) {
      Logger.instance = new Logger();
    }
    return Logger.instance;
  }

  log(message: string): void {
    console.log(`[${new Date().toISOString()}] ${message}`);
  }
}

// Usage
Logger.getInstance().log('Application started');
```

## Problems with Singleton

```typescript
// ❌ Global state - hard to test
class UserService {
  getUser(id: string): User {
    // Direct dependency on singleton - can't mock in tests
    Logger.getInstance().log(`Fetching user ${id}`);
    // ...
  }
}

// ❌ Hidden dependencies
class OrderService {
  processOrder(order: Order): void {
    // What dependencies does this class have?
    // Can't tell from constructor or interface
    Logger.getInstance().log('Processing order');
    DatabaseConnection.getInstance().save(order);
    EmailService.getInstance().send('Order processed');
  }
}

// ❌ Thread safety issues in multi-threaded environments
// ❌ Difficult to reset state for testing
// ❌ Violates Single Responsibility Principle
```

## Better Alternative: Dependency Injection

```typescript
// ✅ Logger as injectable dependency
interface ILogger {
  log(message: string): void;
  error(message: string, error?: Error): void;
}

class ConsoleLogger implements ILogger {
  log(message: string): void {
    console.log(`[${new Date().toISOString()}] ${message}`);
  }

  error(message: string, error?: Error): void {
    console.error(`[${new Date().toISOString()}] ERROR: ${message}`, error);
  }
}

// Service receives logger through constructor
class UserService {
  constructor(private readonly logger: ILogger) {}

  getUser(id: string): User {
    this.logger.log(`Fetching user ${id}`);
    // ...
  }
}

// Easy to test
const mockLogger: ILogger = {
  log: jest.fn(),
  error: jest.fn(),
};
const service = new UserService(mockLogger);

// Single instance managed by DI container
container.bind<ILogger>('Logger').to(ConsoleLogger).inSingletonScope();
```

## When Singleton Is Acceptable

### 1. Configuration Management

```typescript
// Application configuration - read-only after initialization
class Config {
  private static instance: Config;
  private settings: Record<string, any>;

  private constructor() {
    this.settings = this.loadFromEnvironment();
    Object.freeze(this.settings); // Make immutable
  }

  static getInstance(): Config {
    if (!Config.instance) {
      Config.instance = new Config();
    }
    return Config.instance;
  }

  get<T>(key: string): T {
    return this.settings[key] as T;
  }

  private loadFromEnvironment(): Record<string, any> {
    return {
      databaseUrl: process.env.DATABASE_URL,
      apiKey: process.env.API_KEY,
      environment: process.env.NODE_ENV || 'development',
    };
  }
}
```

### 2. Connection Pools

```typescript
// Database connection pool - expensive to create
class DatabasePool {
  private static instance: DatabasePool;
  private pool: Pool;

  private constructor() {
    this.pool = new Pool({
      connectionString: process.env.DATABASE_URL,
      max: 20,
      idleTimeoutMillis: 30000,
    });
  }

  static getInstance(): DatabasePool {
    if (!DatabasePool.instance) {
      DatabasePool.instance = new DatabasePool();
    }
    return DatabasePool.instance;
  }

  async query<T>(sql: string, params?: any[]): Promise<T[]> {
    const client = await this.pool.connect();
    try {
      const result = await client.query(sql, params);
      return result.rows;
    } finally {
      client.release();
    }
  }

  async shutdown(): Promise<void> {
    await this.pool.end();
  }
}
```

### 3. Hardware Resource Access

```typescript
// Printer spooler - only one can manage the printer
class PrinterSpooler {
  private static instance: PrinterSpooler;
  private queue: PrintJob[] = [];
  private isProcessing = false;

  private constructor() {}

  static getInstance(): PrinterSpooler {
    if (!PrinterSpooler.instance) {
      PrinterSpooler.instance = new PrinterSpooler();
    }
    return PrinterSpooler.instance;
  }

  addJob(job: PrintJob): void {
    this.queue.push(job);
    this.processQueue();
  }

  private async processQueue(): Promise<void> {
    if (this.isProcessing || this.queue.length === 0) return;

    this.isProcessing = true;
    while (this.queue.length > 0) {
      const job = this.queue.shift()!;
      await this.print(job);
    }
    this.isProcessing = false;
  }

  private async print(job: PrintJob): Promise<void> {
    // Send to printer
  }
}
```

## Lazy Initialization with Module Pattern

```typescript
// Node.js module pattern - natural singleton
// logger.ts
class Logger {
  private level: LogLevel = 'info';

  setLevel(level: LogLevel): void {
    this.level = level;
  }

  log(message: string): void {
    if (this.shouldLog('info')) {
      console.log(`[INFO] ${message}`);
    }
  }

  error(message: string, error?: Error): void {
    if (this.shouldLog('error')) {
      console.error(`[ERROR] ${message}`, error);
    }
  }

  private shouldLog(level: LogLevel): boolean {
    const levels: LogLevel[] = ['debug', 'info', 'warn', 'error'];
    return levels.indexOf(level) >= levels.indexOf(this.level);
  }
}

// Module exports a single instance
export const logger = new Logger();

// Usage - same instance everywhere
import { logger } from './logger';
logger.log('Application started');
```

## Resettable Singleton for Testing

```typescript
class CacheManager {
  private static instance: CacheManager | null = null;
  private cache = new Map<string, any>();

  private constructor() {}

  static getInstance(): CacheManager {
    if (!CacheManager.instance) {
      CacheManager.instance = new CacheManager();
    }
    return CacheManager.instance;
  }

  // Allow resetting for tests
  static resetInstance(): void {
    CacheManager.instance = null;
  }

  get<T>(key: string): T | undefined {
    return this.cache.get(key);
  }

  set<T>(key: string, value: T, ttl?: number): void {
    this.cache.set(key, value);
    if (ttl) {
      setTimeout(() => this.cache.delete(key), ttl);
    }
  }

  clear(): void {
    this.cache.clear();
  }
}

// In tests
beforeEach(() => {
  CacheManager.resetInstance();
});
```

## Singleton with DI Container

```typescript
// Let DI container manage singleton lifecycle
import { Container, injectable } from 'inversify';

@injectable()
class EmailService {
  constructor(
    private readonly smtpClient: SmtpClient,
    private readonly templateEngine: TemplateEngine
  ) {}

  async send(to: string, template: string, data: any): Promise<void> {
    const html = this.templateEngine.render(template, data);
    await this.smtpClient.send({ to, html });
  }
}

// Container configuration
const container = new Container();
container.bind(EmailService).toSelf().inSingletonScope();
container.bind(SmtpClient).toSelf().inSingletonScope();
container.bind(TemplateEngine).toSelf().inSingletonScope();

// Single instance, but injectable and testable
const emailService = container.get(EmailService);
```

## Summary

| Approach | When to Use |
|----------|------------|
| Avoid Singleton | Default choice - use DI instead |
| Singleton | Truly global state (config, hardware access) |
| Module Pattern | Simple Node.js services |
| DI Singleton Scope | Need single instance with testability |

### Singleton Checklist

Before using Singleton, ask:
- [ ] Is there truly only one instance needed system-wide?
- [ ] Would DI achieve the same result with better testability?
- [ ] Is the singleton stateless or immutable?
- [ ] Can I easily reset it for testing?
- [ ] Am I hiding dependencies?
