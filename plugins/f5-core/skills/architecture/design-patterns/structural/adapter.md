---
name: adapter-pattern
description: Adapter pattern for interface compatibility
category: architecture/design-patterns/structural
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Adapter Pattern

## Overview

The Adapter pattern converts the interface of a class into another
interface that clients expect. It allows classes with incompatible
interfaces to work together.

## Problem

```typescript
// Existing interface your code expects
interface PaymentGateway {
  charge(amount: number, currency: string): Promise<PaymentResult>;
  refund(transactionId: string): Promise<RefundResult>;
}

// Third-party library with different interface
class StripeSDK {
  createPaymentIntent(params: {
    amount: number;
    currency: string;
    payment_method_types: string[];
  }): Promise<StripePaymentIntent> { /* ... */ }

  createRefund(params: {
    payment_intent: string;
    amount?: number;
  }): Promise<StripeRefund> { /* ... */ }
}

// Problem: StripeSDK doesn't implement PaymentGateway interface
// const gateway: PaymentGateway = new StripeSDK(); // ❌ Type error!
```

## Solution: Adapter

```typescript
// ✅ Adapter wraps Stripe SDK and implements PaymentGateway interface
class StripeAdapter implements PaymentGateway {
  constructor(private readonly stripe: StripeSDK) {}

  async charge(amount: number, currency: string): Promise<PaymentResult> {
    const intent = await this.stripe.createPaymentIntent({
      amount: Math.round(amount * 100), // Convert to cents
      currency: currency.toLowerCase(),
      payment_method_types: ['card'],
    });

    return {
      success: intent.status === 'succeeded',
      transactionId: intent.id,
      amount: intent.amount / 100,
      currency: intent.currency.toUpperCase(),
    };
  }

  async refund(transactionId: string): Promise<RefundResult> {
    const refund = await this.stripe.createRefund({
      payment_intent: transactionId,
    });

    return {
      success: refund.status === 'succeeded',
      refundId: refund.id,
      amount: refund.amount / 100,
    };
  }
}

// Now can use as PaymentGateway
const gateway: PaymentGateway = new StripeAdapter(new StripeSDK());
await gateway.charge(99.99, 'USD');
```

## Object Adapter vs Class Adapter

### Object Adapter (Composition) - Preferred

```typescript
// Uses composition - adapter HAS-A adaptee
class PayPalAdapter implements PaymentGateway {
  constructor(private readonly paypal: PayPalSDK) {}

  async charge(amount: number, currency: string): Promise<PaymentResult> {
    const order = await this.paypal.orders.create({
      intent: 'CAPTURE',
      purchase_units: [{
        amount: { value: amount.toFixed(2), currency_code: currency }
      }]
    });
    return this.toPaymentResult(order);
  }

  // ... other methods
}
```

### Class Adapter (Inheritance) - Less Flexible

```typescript
// Uses inheritance - adapter IS-A adaptee (multiple inheritance issues)
class PayPalAdapter extends PayPalSDK implements PaymentGateway {
  async charge(amount: number, currency: string): Promise<PaymentResult> {
    const order = await this.orders.create({ /* ... */ });
    return this.toPaymentResult(order);
  }
}
```

## Real-World Examples

### Database Adapter

```typescript
// Common interface for database operations
interface Database {
  connect(): Promise<void>;
  query<T>(sql: string, params?: any[]): Promise<T[]>;
  execute(sql: string, params?: any[]): Promise<void>;
  disconnect(): Promise<void>;
}

// PostgreSQL Adapter
class PostgreSQLAdapter implements Database {
  private client: pg.Client;

  constructor(connectionString: string) {
    this.client = new pg.Client({ connectionString });
  }

  async connect(): Promise<void> {
    await this.client.connect();
  }

  async query<T>(sql: string, params?: any[]): Promise<T[]> {
    const result = await this.client.query(sql, params);
    return result.rows as T[];
  }

  async execute(sql: string, params?: any[]): Promise<void> {
    await this.client.query(sql, params);
  }

  async disconnect(): Promise<void> {
    await this.client.end();
  }
}

// MySQL Adapter
class MySQLAdapter implements Database {
  private pool: mysql.Pool;

  constructor(config: mysql.PoolOptions) {
    this.pool = mysql.createPool(config);
  }

  async connect(): Promise<void> {
    // MySQL pool connects automatically
  }

  async query<T>(sql: string, params?: any[]): Promise<T[]> {
    const [rows] = await this.pool.execute(sql, params);
    return rows as T[];
  }

  async execute(sql: string, params?: any[]): Promise<void> {
    await this.pool.execute(sql, params);
  }

  async disconnect(): Promise<void> {
    await this.pool.end();
  }
}

// Application code works with any database
class UserRepository {
  constructor(private readonly db: Database) {}

  async findById(id: string): Promise<User | null> {
    const [user] = await this.db.query<User>(
      'SELECT * FROM users WHERE id = $1',
      [id]
    );
    return user || null;
  }
}
```

### Logger Adapter

```typescript
// Application logging interface
interface Logger {
  debug(message: string, context?: Record<string, any>): void;
  info(message: string, context?: Record<string, any>): void;
  warn(message: string, context?: Record<string, any>): void;
  error(message: string, error?: Error, context?: Record<string, any>): void;
}

// Winston Adapter
class WinstonAdapter implements Logger {
  private winston: Winston.Logger;

  constructor(config: WinstonConfig) {
    this.winston = createLogger(config);
  }

  debug(message: string, context?: Record<string, any>): void {
    this.winston.debug(message, { ...context });
  }

  info(message: string, context?: Record<string, any>): void {
    this.winston.info(message, { ...context });
  }

  warn(message: string, context?: Record<string, any>): void {
    this.winston.warn(message, { ...context });
  }

  error(message: string, error?: Error, context?: Record<string, any>): void {
    this.winston.error(message, { error: error?.stack, ...context });
  }
}

// Pino Adapter
class PinoAdapter implements Logger {
  private pino: Pino.Logger;

  constructor(config: PinoConfig) {
    this.pino = pino(config);
  }

  debug(message: string, context?: Record<string, any>): void {
    this.pino.debug(context || {}, message);
  }

  info(message: string, context?: Record<string, any>): void {
    this.pino.info(context || {}, message);
  }

  warn(message: string, context?: Record<string, any>): void {
    this.pino.warn(context || {}, message);
  }

  error(message: string, error?: Error, context?: Record<string, any>): void {
    this.pino.error({ error: error?.stack, ...context }, message);
  }
}
```

### External API Adapter

```typescript
// Internal weather interface
interface WeatherService {
  getCurrentWeather(city: string): Promise<Weather>;
  getForecast(city: string, days: number): Promise<Forecast[]>;
}

interface Weather {
  temperature: number;  // Celsius
  humidity: number;     // Percentage
  description: string;
  windSpeed: number;    // km/h
}

// OpenWeatherMap Adapter
class OpenWeatherMapAdapter implements WeatherService {
  constructor(
    private readonly apiKey: string,
    private readonly httpClient: HttpClient
  ) {}

  async getCurrentWeather(city: string): Promise<Weather> {
    const response = await this.httpClient.get(
      `https://api.openweathermap.org/data/2.5/weather`,
      { params: { q: city, appid: this.apiKey, units: 'metric' } }
    );

    // Transform external format to internal format
    return {
      temperature: response.data.main.temp,
      humidity: response.data.main.humidity,
      description: response.data.weather[0].description,
      windSpeed: response.data.wind.speed * 3.6, // m/s to km/h
    };
  }

  async getForecast(city: string, days: number): Promise<Forecast[]> {
    const response = await this.httpClient.get(
      `https://api.openweathermap.org/data/2.5/forecast`,
      { params: { q: city, appid: this.apiKey, units: 'metric', cnt: days * 8 } }
    );

    return this.transformForecast(response.data.list);
  }

  private transformForecast(data: any[]): Forecast[] {
    // Transform API-specific format to internal format
    return data.map(item => ({
      date: new Date(item.dt * 1000),
      temperature: item.main.temp,
      description: item.weather[0].description,
    }));
  }
}

// WeatherAPI.com Adapter (different API, same interface)
class WeatherAPIAdapter implements WeatherService {
  constructor(
    private readonly apiKey: string,
    private readonly httpClient: HttpClient
  ) {}

  async getCurrentWeather(city: string): Promise<Weather> {
    const response = await this.httpClient.get(
      `https://api.weatherapi.com/v1/current.json`,
      { params: { key: this.apiKey, q: city } }
    );

    return {
      temperature: response.data.current.temp_c,
      humidity: response.data.current.humidity,
      description: response.data.current.condition.text,
      windSpeed: response.data.current.wind_kph,
    };
  }

  async getForecast(city: string, days: number): Promise<Forecast[]> {
    // Implementation for WeatherAPI.com
  }
}
```

## Anti-Corruption Layer

```typescript
// In DDD, adapters form the Anti-Corruption Layer between bounded contexts
class InventoryAntiCorruptionLayer {
  constructor(private readonly legacyInventorySystem: LegacyInventoryAPI) {}

  async checkStock(productId: string): Promise<StockStatus> {
    // Call legacy system
    const legacyResponse = await this.legacyInventorySystem.getItemAvailability(
      this.toLegacyProductCode(productId)
    );

    // Translate to our domain model
    return {
      productId,
      available: legacyResponse.qty_available > 0,
      quantity: legacyResponse.qty_available,
      warehouseLocation: this.mapWarehouse(legacyResponse.whse_id),
    };
  }

  private toLegacyProductCode(productId: string): string {
    // Convert our product ID format to legacy system format
    return `PROD-${productId.toUpperCase()}`;
  }

  private mapWarehouse(legacyWarehouseId: string): string {
    const warehouseMap: Record<string, string> = {
      'WH001': 'warehouse-east',
      'WH002': 'warehouse-west',
      'WH003': 'warehouse-central',
    };
    return warehouseMap[legacyWarehouseId] || 'unknown';
  }
}
```

## Benefits

| Benefit | Description |
|---------|-------------|
| Compatibility | Makes incompatible interfaces work together |
| Reusability | Reuse existing code without modification |
| Single Responsibility | Conversion logic isolated in adapter |
| Flexibility | Easy to switch implementations |

## When to Use

- Integrating third-party libraries
- Working with legacy systems
- Creating unified interfaces for multiple services
- Building anti-corruption layers in DDD
