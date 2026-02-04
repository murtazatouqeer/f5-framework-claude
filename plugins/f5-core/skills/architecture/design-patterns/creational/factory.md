---
name: factory-pattern
description: Factory patterns for object creation
category: architecture/design-patterns/creational
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Factory Pattern

## Overview

Factory patterns encapsulate object creation logic, providing flexibility
in instantiation without exposing creation logic to the client.

## Factory Method Pattern

### Problem
```typescript
// ❌ Client directly creates objects
class OrderService {
  createNotification(type: string): Notification {
    if (type === 'email') {
      return new EmailNotification(
        this.smtpHost,
        this.smtpPort,
        this.smtpUser,
        this.smtpPass
      );
    } else if (type === 'sms') {
      return new SMSNotification(
        this.twilioSid,
        this.twilioToken,
        this.twilioNumber
      );
    } else if (type === 'push') {
      return new PushNotification(
        this.firebaseKey
      );
    }
    throw new Error(`Unknown notification type: ${type}`);
  }
}
```

### Solution
```typescript
// ✅ Factory Method Pattern
interface Notification {
  send(message: string, recipient: string): Promise<void>;
}

abstract class NotificationFactory {
  abstract createNotification(): Notification;

  async notify(message: string, recipient: string): Promise<void> {
    const notification = this.createNotification();
    await notification.send(message, recipient);
  }
}

class EmailNotificationFactory extends NotificationFactory {
  constructor(private readonly config: EmailConfig) {
    super();
  }

  createNotification(): Notification {
    return new EmailNotification(this.config);
  }
}

class SMSNotificationFactory extends NotificationFactory {
  constructor(private readonly config: SMSConfig) {
    super();
  }

  createNotification(): Notification {
    return new SMSNotification(this.config);
  }
}

// Usage
const factory = new EmailNotificationFactory(emailConfig);
await factory.notify('Order confirmed', 'user@example.com');
```

## Simple Factory

```typescript
// Simple Factory - Not a GoF pattern but commonly used
class NotificationFactory {
  constructor(
    private readonly emailConfig: EmailConfig,
    private readonly smsConfig: SMSConfig,
    private readonly pushConfig: PushConfig
  ) {}

  create(type: NotificationType): Notification {
    switch (type) {
      case NotificationType.EMAIL:
        return new EmailNotification(this.emailConfig);
      case NotificationType.SMS:
        return new SMSNotification(this.smsConfig);
      case NotificationType.PUSH:
        return new PushNotification(this.pushConfig);
      default:
        throw new Error(`Unknown notification type: ${type}`);
    }
  }
}

// Usage
const factory = new NotificationFactory(emailConfig, smsConfig, pushConfig);
const notification = factory.create(NotificationType.EMAIL);
await notification.send('Hello', 'user@example.com');
```

## Abstract Factory Pattern

### When You Need Families of Related Objects

```typescript
// Abstract Factory for UI Components
interface Button {
  render(): string;
  onClick(handler: () => void): void;
}

interface Input {
  render(): string;
  getValue(): string;
}

interface Modal {
  render(): string;
  open(): void;
  close(): void;
}

// Abstract Factory Interface
interface UIComponentFactory {
  createButton(label: string): Button;
  createInput(placeholder: string): Input;
  createModal(title: string): Modal;
}

// Material Design Implementation
class MaterialButton implements Button {
  constructor(private label: string) {}
  render(): string {
    return `<button class="mdc-button">${this.label}</button>`;
  }
  onClick(handler: () => void): void { /* ... */ }
}

class MaterialInput implements Input {
  constructor(private placeholder: string) {}
  render(): string {
    return `<input class="mdc-text-field" placeholder="${this.placeholder}">`;
  }
  getValue(): string { return ''; }
}

class MaterialUIFactory implements UIComponentFactory {
  createButton(label: string): Button {
    return new MaterialButton(label);
  }
  createInput(placeholder: string): Input {
    return new MaterialInput(placeholder);
  }
  createModal(title: string): Modal {
    return new MaterialModal(title);
  }
}

// Bootstrap Implementation
class BootstrapButton implements Button {
  constructor(private label: string) {}
  render(): string {
    return `<button class="btn btn-primary">${this.label}</button>`;
  }
  onClick(handler: () => void): void { /* ... */ }
}

class BootstrapUIFactory implements UIComponentFactory {
  createButton(label: string): Button {
    return new BootstrapButton(label);
  }
  createInput(placeholder: string): Input {
    return new BootstrapInput(placeholder);
  }
  createModal(title: string): Modal {
    return new BootstrapModal(title);
  }
}

// Usage - Application doesn't know which UI framework is used
class LoginForm {
  constructor(private readonly uiFactory: UIComponentFactory) {}

  render(): string {
    const emailInput = this.uiFactory.createInput('Email');
    const passwordInput = this.uiFactory.createInput('Password');
    const submitButton = this.uiFactory.createButton('Login');

    return `
      <form>
        ${emailInput.render()}
        ${passwordInput.render()}
        ${submitButton.render()}
      </form>
    `;
  }
}

// Switch UI framework by changing factory
const materialForm = new LoginForm(new MaterialUIFactory());
const bootstrapForm = new LoginForm(new BootstrapUIFactory());
```

## Factory with Registry

```typescript
// Dynamic registration of factories
class PaymentGatewayRegistry {
  private factories = new Map<string, () => PaymentGateway>();

  register(type: string, factory: () => PaymentGateway): void {
    this.factories.set(type, factory);
  }

  create(type: string): PaymentGateway {
    const factory = this.factories.get(type);
    if (!factory) {
      throw new Error(`Unknown payment gateway: ${type}`);
    }
    return factory();
  }

  getAvailableTypes(): string[] {
    return Array.from(this.factories.keys());
  }
}

// Registration at application startup
const registry = new PaymentGatewayRegistry();

registry.register('stripe', () => new StripeGateway(stripeConfig));
registry.register('paypal', () => new PayPalGateway(paypalConfig));
registry.register('braintree', () => new BraintreeGateway(braintreeConfig));

// Plugin-style registration
if (process.env.ENABLE_CRYPTO_PAYMENTS) {
  registry.register('bitcoin', () => new BitcoinGateway(bitcoinConfig));
}

// Usage
const gateway = registry.create('stripe');
await gateway.charge(amount);
```

## Factory in Domain-Driven Design

```typescript
// Order Factory - encapsulates complex creation logic
export class OrderFactory {
  constructor(
    private readonly idGenerator: IdGenerator,
    private readonly pricingService: PricingService,
    private readonly inventoryService: InventoryService
  ) {}

  async create(params: CreateOrderParams): Promise<Order> {
    // Validate items are available
    for (const item of params.items) {
      const available = await this.inventoryService.checkAvailability(
        item.productId,
        item.quantity
      );
      if (!available) {
        throw new ProductNotAvailableError(item.productId);
      }
    }

    // Calculate prices
    const orderItems = await Promise.all(
      params.items.map(async item => {
        const price = await this.pricingService.getPrice(
          item.productId,
          params.customerId
        );
        return OrderItem.create(
          item.productId,
          item.quantity,
          price
        );
      })
    );

    // Create order with generated ID
    return Order.create(
      this.idGenerator.generate(),
      params.customerId,
      orderItems,
      params.shippingAddress
    );
  }

  // Reconstitute from persistence (no validation needed)
  reconstitute(data: OrderData): Order {
    return Order.reconstitute(
      data.id,
      data.customerId,
      data.items.map(item => OrderItem.reconstitute(
        item.productId,
        item.quantity,
        Money.create(item.price, item.currency)
      )),
      data.status,
      data.createdAt
    );
  }
}
```

## Static Factory Methods

```typescript
// Factory methods on the class itself
export class Money {
  private constructor(
    private readonly amount: number,
    private readonly currency: string
  ) {}

  // Static factory methods
  static zero(currency: string = 'USD'): Money {
    return new Money(0, currency);
  }

  static fromCents(cents: number, currency: string = 'USD'): Money {
    return new Money(cents / 100, currency);
  }

  static usd(amount: number): Money {
    return new Money(amount, 'USD');
  }

  static eur(amount: number): Money {
    return new Money(amount, 'EUR');
  }

  static parse(value: string): Money {
    const match = value.match(/^([A-Z]{3})\s*(\d+(?:\.\d{2})?)$/);
    if (!match) {
      throw new Error(`Invalid money format: ${value}`);
    }
    return new Money(parseFloat(match[2]), match[1]);
  }
}

// Usage - clear intent
const price = Money.usd(99.99);
const zero = Money.zero('EUR');
const fromDb = Money.fromCents(9999, 'USD');
const parsed = Money.parse('USD 49.99');
```

## When to Use

| Pattern | Use Case |
|---------|----------|
| Simple Factory | Single type hierarchy, central creation |
| Factory Method | Subclass decides which class to create |
| Abstract Factory | Families of related objects |
| Registry | Plugin architecture, runtime registration |

## Benefits

- Decouples creation from usage
- Centralizes complex creation logic
- Enables testing with mock factories
- Supports Open/Closed principle
