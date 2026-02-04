---
name: strategy-pattern
description: Strategy pattern for interchangeable algorithms
category: architecture/design-patterns/behavioral
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Strategy Pattern

## Overview

The Strategy pattern defines a family of algorithms, encapsulates each one,
and makes them interchangeable. It lets the algorithm vary independently
from clients that use it.

## Problem

```typescript
// ❌ Monolithic class with switch statements
class PaymentProcessor {
  process(order: Order, paymentType: string): PaymentResult {
    if (paymentType === 'credit_card') {
      // 50 lines of credit card logic
      // Validation, API calls, error handling...
    } else if (paymentType === 'paypal') {
      // 50 lines of PayPal logic
      // OAuth, redirects, webhooks...
    } else if (paymentType === 'bank_transfer') {
      // 50 lines of bank transfer logic
      // Account validation, SWIFT codes...
    } else if (paymentType === 'crypto') {
      // 50 lines of crypto logic
      // Wallet addresses, blockchain verification...
    }
    // Adding new payment type requires modifying this class
  }
}
```

## Solution: Strategy Pattern

```typescript
// ✅ Strategy interface
interface PaymentStrategy {
  process(order: Order): Promise<PaymentResult>;
  getName(): string;
  validate(order: Order): ValidationResult;
}

// Concrete strategies
class CreditCardStrategy implements PaymentStrategy {
  constructor(private gateway: CreditCardGateway) {}

  async process(order: Order): Promise<PaymentResult> {
    const result = await this.gateway.charge({
      amount: order.total,
      cardNumber: order.paymentDetails.cardNumber,
      expiry: order.paymentDetails.expiry,
      cvv: order.paymentDetails.cvv,
    });

    return {
      success: result.status === 'approved',
      transactionId: result.transactionId,
      message: result.message,
    };
  }

  getName(): string {
    return 'Credit Card';
  }

  validate(order: Order): ValidationResult {
    const errors: string[] = [];
    if (!order.paymentDetails.cardNumber) {
      errors.push('Card number is required');
    }
    if (!order.paymentDetails.cvv) {
      errors.push('CVV is required');
    }
    return { valid: errors.length === 0, errors };
  }
}

class PayPalStrategy implements PaymentStrategy {
  constructor(private paypal: PayPalClient) {}

  async process(order: Order): Promise<PaymentResult> {
    const payment = await this.paypal.createPayment({
      amount: order.total,
      currency: order.currency,
      returnUrl: order.returnUrl,
      cancelUrl: order.cancelUrl,
    });

    return {
      success: true,
      transactionId: payment.id,
      redirectUrl: payment.approvalUrl,
    };
  }

  getName(): string {
    return 'PayPal';
  }

  validate(order: Order): ValidationResult {
    return { valid: true, errors: [] };
  }
}

class CryptoStrategy implements PaymentStrategy {
  constructor(private cryptoGateway: CryptoGateway) {}

  async process(order: Order): Promise<PaymentResult> {
    const invoice = await this.cryptoGateway.createInvoice({
      amount: order.total,
      currency: 'USD',
      cryptoCurrency: order.paymentDetails.cryptoCurrency || 'BTC',
    });

    return {
      success: true,
      transactionId: invoice.id,
      walletAddress: invoice.address,
      amount: invoice.cryptoAmount,
    };
  }

  getName(): string {
    return 'Cryptocurrency';
  }

  validate(order: Order): ValidationResult {
    return { valid: true, errors: [] };
  }
}

// Context class
class PaymentProcessor {
  constructor(private strategy: PaymentStrategy) {}

  setStrategy(strategy: PaymentStrategy): void {
    this.strategy = strategy;
  }

  async processPayment(order: Order): Promise<PaymentResult> {
    // Validate
    const validation = this.strategy.validate(order);
    if (!validation.valid) {
      return { success: false, errors: validation.errors };
    }

    // Process
    return this.strategy.process(order);
  }
}

// Usage
const processor = new PaymentProcessor(new CreditCardStrategy(creditCardGateway));
const result = await processor.processPayment(order);

// Switch strategy at runtime
processor.setStrategy(new PayPalStrategy(paypalClient));
const result2 = await processor.processPayment(anotherOrder);
```

## Strategy Factory

```typescript
// Factory to create strategies based on configuration
class PaymentStrategyFactory {
  private strategies = new Map<string, () => PaymentStrategy>();

  constructor(
    private creditCardGateway: CreditCardGateway,
    private paypalClient: PayPalClient,
    private cryptoGateway: CryptoGateway
  ) {
    this.registerStrategies();
  }

  private registerStrategies(): void {
    this.strategies.set('credit_card', () =>
      new CreditCardStrategy(this.creditCardGateway)
    );
    this.strategies.set('paypal', () =>
      new PayPalStrategy(this.paypalClient)
    );
    this.strategies.set('crypto', () =>
      new CryptoStrategy(this.cryptoGateway)
    );
  }

  create(type: string): PaymentStrategy {
    const factory = this.strategies.get(type);
    if (!factory) {
      throw new Error(`Unknown payment type: ${type}`);
    }
    return factory();
  }

  getAvailableTypes(): string[] {
    return Array.from(this.strategies.keys());
  }
}

// Usage
const factory = new PaymentStrategyFactory(creditCard, paypal, crypto);
const strategy = factory.create(order.paymentType);
const processor = new PaymentProcessor(strategy);
```

## Real-World Examples

### Compression Strategy

```typescript
interface CompressionStrategy {
  compress(data: Buffer): Promise<Buffer>;
  decompress(data: Buffer): Promise<Buffer>;
  getExtension(): string;
}

class GzipStrategy implements CompressionStrategy {
  async compress(data: Buffer): Promise<Buffer> {
    return zlib.gzipSync(data);
  }

  async decompress(data: Buffer): Promise<Buffer> {
    return zlib.gunzipSync(data);
  }

  getExtension(): string {
    return '.gz';
  }
}

class Bzip2Strategy implements CompressionStrategy {
  async compress(data: Buffer): Promise<Buffer> {
    return bzip2.compressSync(data);
  }

  async decompress(data: Buffer): Promise<Buffer> {
    return bzip2.decompressSync(data);
  }

  getExtension(): string {
    return '.bz2';
  }
}

class NoCompressionStrategy implements CompressionStrategy {
  async compress(data: Buffer): Promise<Buffer> {
    return data;
  }

  async decompress(data: Buffer): Promise<Buffer> {
    return data;
  }

  getExtension(): string {
    return '';
  }
}

class FileArchiver {
  constructor(private compressionStrategy: CompressionStrategy) {}

  async archive(files: File[], outputPath: string): Promise<void> {
    // Combine files
    const combined = await this.combineFiles(files);

    // Compress using strategy
    const compressed = await this.compressionStrategy.compress(combined);

    // Write to output with appropriate extension
    const finalPath = outputPath + this.compressionStrategy.getExtension();
    await fs.promises.writeFile(finalPath, compressed);
  }

  private async combineFiles(files: File[]): Promise<Buffer> {
    // Combine files into single buffer
    return Buffer.concat(await Promise.all(files.map(f => f.read())));
  }
}
```

### Sorting Strategy

```typescript
interface SortStrategy<T> {
  sort(items: T[]): T[];
  getName(): string;
}

class QuickSortStrategy<T> implements SortStrategy<T> {
  constructor(private compareFn: (a: T, b: T) => number) {}

  sort(items: T[]): T[] {
    if (items.length <= 1) return items;

    const pivot = items[Math.floor(items.length / 2)];
    const left = items.filter(item => this.compareFn(item, pivot) < 0);
    const middle = items.filter(item => this.compareFn(item, pivot) === 0);
    const right = items.filter(item => this.compareFn(item, pivot) > 0);

    return [...this.sort(left), ...middle, ...this.sort(right)];
  }

  getName(): string {
    return 'Quick Sort';
  }
}

class MergeSortStrategy<T> implements SortStrategy<T> {
  constructor(private compareFn: (a: T, b: T) => number) {}

  sort(items: T[]): T[] {
    if (items.length <= 1) return items;

    const mid = Math.floor(items.length / 2);
    const left = this.sort(items.slice(0, mid));
    const right = this.sort(items.slice(mid));

    return this.merge(left, right);
  }

  private merge(left: T[], right: T[]): T[] {
    const result: T[] = [];
    let i = 0, j = 0;

    while (i < left.length && j < right.length) {
      if (this.compareFn(left[i], right[j]) <= 0) {
        result.push(left[i++]);
      } else {
        result.push(right[j++]);
      }
    }

    return [...result, ...left.slice(i), ...right.slice(j)];
  }

  getName(): string {
    return 'Merge Sort';
  }
}

// Adaptive strategy selection
class AdaptiveSortStrategy<T> implements SortStrategy<T> {
  constructor(
    private compareFn: (a: T, b: T) => number,
    private threshold: number = 1000
  ) {}

  sort(items: T[]): T[] {
    // Use QuickSort for small arrays, MergeSort for large
    const strategy = items.length < this.threshold
      ? new QuickSortStrategy<T>(this.compareFn)
      : new MergeSortStrategy<T>(this.compareFn);

    return strategy.sort(items);
  }

  getName(): string {
    return 'Adaptive Sort';
  }
}
```

### Pricing Strategy

```typescript
interface PricingStrategy {
  calculatePrice(basePrice: number, customer: Customer): number;
  getDescription(): string;
}

class RegularPricingStrategy implements PricingStrategy {
  calculatePrice(basePrice: number, customer: Customer): number {
    return basePrice;
  }

  getDescription(): string {
    return 'Regular pricing';
  }
}

class VIPPricingStrategy implements PricingStrategy {
  constructor(private discountPercent: number = 20) {}

  calculatePrice(basePrice: number, customer: Customer): number {
    return basePrice * (1 - this.discountPercent / 100);
  }

  getDescription(): string {
    return `VIP pricing (${this.discountPercent}% discount)`;
  }
}

class SeasonalPricingStrategy implements PricingStrategy {
  constructor(
    private seasonMultiplier: number,
    private seasonName: string
  ) {}

  calculatePrice(basePrice: number, customer: Customer): number {
    return basePrice * this.seasonMultiplier;
  }

  getDescription(): string {
    return `${this.seasonName} pricing (${this.seasonMultiplier}x)`;
  }
}

class BulkPricingStrategy implements PricingStrategy {
  constructor(private tiers: { minQuantity: number; discount: number }[]) {}

  calculatePrice(basePrice: number, customer: Customer): number {
    const quantity = customer.currentOrderQuantity;
    const tier = this.tiers
      .sort((a, b) => b.minQuantity - a.minQuantity)
      .find(t => quantity >= t.minQuantity);

    const discount = tier?.discount || 0;
    return basePrice * (1 - discount / 100);
  }

  getDescription(): string {
    return 'Bulk pricing';
  }
}

// Context with strategy selection
class PricingEngine {
  private strategies: Map<string, PricingStrategy> = new Map();
  private defaultStrategy: PricingStrategy;

  constructor() {
    this.defaultStrategy = new RegularPricingStrategy();
    this.registerStrategies();
  }

  private registerStrategies(): void {
    this.strategies.set('regular', new RegularPricingStrategy());
    this.strategies.set('vip', new VIPPricingStrategy(20));
    this.strategies.set('holiday', new SeasonalPricingStrategy(1.25, 'Holiday'));
    this.strategies.set('bulk', new BulkPricingStrategy([
      { minQuantity: 100, discount: 15 },
      { minQuantity: 50, discount: 10 },
      { minQuantity: 20, discount: 5 },
    ]));
  }

  calculatePrice(basePrice: number, customer: Customer): PriceResult {
    const strategyKey = this.selectStrategy(customer);
    const strategy = this.strategies.get(strategyKey) || this.defaultStrategy;
    const finalPrice = strategy.calculatePrice(basePrice, customer);

    return {
      basePrice,
      finalPrice,
      strategy: strategyKey,
      description: strategy.getDescription(),
      savings: basePrice - finalPrice,
    };
  }

  private selectStrategy(customer: Customer): string {
    if (customer.isVIP) return 'vip';
    if (customer.currentOrderQuantity >= 20) return 'bulk';
    if (this.isHolidaySeason()) return 'holiday';
    return 'regular';
  }

  private isHolidaySeason(): boolean {
    const month = new Date().getMonth();
    return month === 11 || month === 0; // Dec or Jan
  }
}
```

## Benefits

| Benefit | Description |
|---------|-------------|
| Open/Closed | Add new strategies without modifying context |
| Single Responsibility | Each strategy handles one algorithm |
| Runtime Flexibility | Switch algorithms at runtime |
| Testability | Strategies can be tested independently |
| Eliminates Conditionals | No switch/if-else for algorithm selection |

## When to Use

- Multiple algorithms for a task
- Need to switch algorithms at runtime
- Class has multiple conditional behaviors
- Algorithm implementations should be independent
