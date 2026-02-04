---
name: observer-pattern
description: Observer pattern for event-driven communication
category: architecture/design-patterns/behavioral
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Observer Pattern

## Overview

The Observer pattern defines a one-to-many dependency between objects so
that when one object changes state, all its dependents are notified and
updated automatically.

## Basic Implementation

```typescript
// Observer interface
interface Observer<T> {
  update(event: T): void;
}

// Subject (Observable) interface
interface Subject<T> {
  subscribe(observer: Observer<T>): void;
  unsubscribe(observer: Observer<T>): void;
  notify(event: T): void;
}

// Concrete Subject
class EventEmitter<T> implements Subject<T> {
  private observers: Set<Observer<T>> = new Set();

  subscribe(observer: Observer<T>): void {
    this.observers.add(observer);
  }

  unsubscribe(observer: Observer<T>): void {
    this.observers.delete(observer);
  }

  notify(event: T): void {
    this.observers.forEach(observer => observer.update(event));
  }
}

// Usage
interface StockPrice {
  symbol: string;
  price: number;
  change: number;
}

class StockTicker extends EventEmitter<StockPrice> {
  updatePrice(symbol: string, price: number, change: number): void {
    this.notify({ symbol, price, change });
  }
}

class StockDisplay implements Observer<StockPrice> {
  update(event: StockPrice): void {
    console.log(`${event.symbol}: $${event.price} (${event.change > 0 ? '+' : ''}${event.change}%)`);
  }
}

class StockAlert implements Observer<StockPrice> {
  constructor(private threshold: number) {}

  update(event: StockPrice): void {
    if (Math.abs(event.change) > this.threshold) {
      console.log(`ALERT: ${event.symbol} moved ${event.change}%!`);
    }
  }
}

const ticker = new StockTicker();
ticker.subscribe(new StockDisplay());
ticker.subscribe(new StockAlert(5));

ticker.updatePrice('AAPL', 150.25, 2.5);
ticker.updatePrice('GOOGL', 2750.00, -6.2); // Triggers alert
```

## Typed Event System

```typescript
// Event types
type EventMap = {
  'user:created': { userId: string; email: string };
  'user:updated': { userId: string; changes: Partial<User> };
  'user:deleted': { userId: string };
  'order:placed': { orderId: string; userId: string; total: number };
  'order:shipped': { orderId: string; trackingNumber: string };
};

// Type-safe event emitter
class TypedEventEmitter {
  private listeners = new Map<string, Set<Function>>();

  on<K extends keyof EventMap>(event: K, handler: (data: EventMap[K]) => void): () => void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(handler);

    // Return unsubscribe function
    return () => this.off(event, handler);
  }

  off<K extends keyof EventMap>(event: K, handler: (data: EventMap[K]) => void): void {
    this.listeners.get(event)?.delete(handler);
  }

  emit<K extends keyof EventMap>(event: K, data: EventMap[K]): void {
    this.listeners.get(event)?.forEach(handler => handler(data));
  }

  once<K extends keyof EventMap>(event: K, handler: (data: EventMap[K]) => void): void {
    const wrapper = (data: EventMap[K]) => {
      handler(data);
      this.off(event, wrapper);
    };
    this.on(event, wrapper);
  }
}

// Usage
const events = new TypedEventEmitter();

// Type-safe subscription
events.on('user:created', (data) => {
  console.log(`User ${data.userId} created with email ${data.email}`);
});

events.on('order:placed', (data) => {
  console.log(`Order ${data.orderId} placed for $${data.total}`);
});

// Type-safe emission
events.emit('user:created', { userId: '123', email: 'test@example.com' });
events.emit('order:placed', { orderId: 'ORD-001', userId: '123', total: 99.99 });
```

## Async Observer Pattern

```typescript
// Async observer
interface AsyncObserver<T> {
  handle(event: T): Promise<void>;
}

class AsyncEventEmitter<T> {
  private observers: Set<AsyncObserver<T>> = new Set();

  subscribe(observer: AsyncObserver<T>): () => void {
    this.observers.add(observer);
    return () => this.observers.delete(observer);
  }

  // Parallel notification
  async notifyAll(event: T): Promise<void> {
    const promises = Array.from(this.observers).map(observer =>
      observer.handle(event).catch(error => {
        console.error('Observer error:', error);
      })
    );
    await Promise.all(promises);
  }

  // Sequential notification
  async notifySequential(event: T): Promise<void> {
    for (const observer of this.observers) {
      try {
        await observer.handle(event);
      } catch (error) {
        console.error('Observer error:', error);
      }
    }
  }

  // With timeout
  async notifyWithTimeout(event: T, timeoutMs: number): Promise<void> {
    const promises = Array.from(this.observers).map(observer =>
      Promise.race([
        observer.handle(event),
        new Promise((_, reject) =>
          setTimeout(() => reject(new Error('Observer timeout')), timeoutMs)
        ),
      ]).catch(error => {
        console.error('Observer error:', error);
      })
    );
    await Promise.all(promises);
  }
}

// Example: Order processing with async observers
class OrderEventEmitter extends AsyncEventEmitter<OrderEvent> {}

class InventoryObserver implements AsyncObserver<OrderEvent> {
  async handle(event: OrderEvent): Promise<void> {
    if (event.type === 'order:placed') {
      await this.inventoryService.reserve(event.orderId, event.items);
    }
  }
}

class EmailObserver implements AsyncObserver<OrderEvent> {
  async handle(event: OrderEvent): Promise<void> {
    if (event.type === 'order:placed') {
      await this.emailService.sendOrderConfirmation(event.userId, event.orderId);
    }
  }
}

class AnalyticsObserver implements AsyncObserver<OrderEvent> {
  async handle(event: OrderEvent): Promise<void> {
    await this.analyticsService.track(event.type, event);
  }
}
```

## Pub/Sub Pattern

```typescript
// More decoupled version using channels
class PubSub {
  private channels = new Map<string, Set<(message: any) => void>>();

  subscribe<T>(channel: string, handler: (message: T) => void): () => void {
    if (!this.channels.has(channel)) {
      this.channels.set(channel, new Set());
    }
    this.channels.get(channel)!.add(handler);

    return () => this.channels.get(channel)?.delete(handler);
  }

  publish<T>(channel: string, message: T): void {
    this.channels.get(channel)?.forEach(handler => {
      try {
        handler(message);
      } catch (error) {
        console.error(`Error in ${channel} handler:`, error);
      }
    });
  }

  // Pattern matching
  subscribePattern(pattern: RegExp, handler: (channel: string, message: any) => void): () => void {
    const wrapper = { pattern, handler };
    this.patternHandlers.add(wrapper);
    return () => this.patternHandlers.delete(wrapper);
  }

  private patternHandlers = new Set<{ pattern: RegExp; handler: Function }>();

  private notifyPatternHandlers(channel: string, message: any): void {
    this.patternHandlers.forEach(({ pattern, handler }) => {
      if (pattern.test(channel)) {
        handler(channel, message);
      }
    });
  }
}

// Usage
const pubsub = new PubSub();

// Subscribe to specific channel
pubsub.subscribe('orders:placed', (order) => {
  console.log('New order:', order);
});

// Subscribe to pattern
pubsub.subscribePattern(/^orders:/, (channel, message) => {
  console.log(`Order event on ${channel}:`, message);
});

// Publish
pubsub.publish('orders:placed', { orderId: '123', total: 99.99 });
pubsub.publish('orders:shipped', { orderId: '123', tracking: 'TRK-456' });
```

## React-Style Observable State

```typescript
// Observable state container
class ObservableState<T> {
  private state: T;
  private listeners = new Set<(state: T) => void>();

  constructor(initialState: T) {
    this.state = initialState;
  }

  getState(): T {
    return this.state;
  }

  setState(update: Partial<T> | ((prev: T) => Partial<T>)): void {
    const updates = typeof update === 'function' ? update(this.state) : update;
    this.state = { ...this.state, ...updates };
    this.notify();
  }

  subscribe(listener: (state: T) => void): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private notify(): void {
    this.listeners.forEach(listener => listener(this.state));
  }
}

// Selector-based subscriptions (like Redux)
class Store<T> {
  private state: T;
  private listeners = new Map<(state: T) => any, Set<(value: any) => void>>();

  constructor(initialState: T) {
    this.state = initialState;
  }

  getState(): T {
    return this.state;
  }

  dispatch(reducer: (state: T) => T): void {
    this.state = reducer(this.state);
    this.notifyAll();
  }

  subscribe<S>(selector: (state: T) => S, listener: (value: S) => void): () => void {
    if (!this.listeners.has(selector)) {
      this.listeners.set(selector, new Set());
    }
    this.listeners.get(selector)!.add(listener);

    // Immediately call with current value
    listener(selector(this.state));

    return () => this.listeners.get(selector)?.delete(listener);
  }

  private notifyAll(): void {
    this.listeners.forEach((listeners, selector) => {
      const value = selector(this.state);
      listeners.forEach(listener => listener(value));
    });
  }
}

// Usage
interface AppState {
  user: User | null;
  cart: CartItem[];
  notifications: Notification[];
}

const store = new Store<AppState>({
  user: null,
  cart: [],
  notifications: [],
});

// Subscribe to specific parts of state
store.subscribe(
  state => state.cart.length,
  count => console.log(`Cart has ${count} items`)
);

store.subscribe(
  state => state.user,
  user => console.log(`User changed:`, user)
);

// Update state
store.dispatch(state => ({
  ...state,
  cart: [...state.cart, { productId: '123', quantity: 1 }],
}));
```

## Domain Events

```typescript
// Domain event base
abstract class DomainEvent {
  readonly occurredOn: Date = new Date();
  abstract readonly eventType: string;
}

// Concrete events
class OrderPlacedEvent extends DomainEvent {
  readonly eventType = 'OrderPlaced';

  constructor(
    public readonly orderId: string,
    public readonly customerId: string,
    public readonly total: number
  ) {
    super();
  }
}

class OrderShippedEvent extends DomainEvent {
  readonly eventType = 'OrderShipped';

  constructor(
    public readonly orderId: string,
    public readonly trackingNumber: string
  ) {
    super();
  }
}

// Domain event dispatcher
class DomainEventDispatcher {
  private handlers = new Map<string, Set<(event: DomainEvent) => Promise<void>>>();

  register<T extends DomainEvent>(
    eventType: string,
    handler: (event: T) => Promise<void>
  ): void {
    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, new Set());
    }
    this.handlers.get(eventType)!.add(handler as any);
  }

  async dispatch(event: DomainEvent): Promise<void> {
    const handlers = this.handlers.get(event.eventType);
    if (!handlers) return;

    await Promise.all(
      Array.from(handlers).map(handler => handler(event))
    );
  }

  async dispatchAll(events: DomainEvent[]): Promise<void> {
    for (const event of events) {
      await this.dispatch(event);
    }
  }
}

// Usage with aggregates
class Order {
  private events: DomainEvent[] = [];

  place(): void {
    this.status = 'placed';
    this.events.push(new OrderPlacedEvent(this.id, this.customerId, this.total));
  }

  ship(trackingNumber: string): void {
    this.status = 'shipped';
    this.trackingNumber = trackingNumber;
    this.events.push(new OrderShippedEvent(this.id, trackingNumber));
  }

  pullEvents(): DomainEvent[] {
    const events = [...this.events];
    this.events = [];
    return events;
  }
}

// Register handlers
const dispatcher = new DomainEventDispatcher();

dispatcher.register('OrderPlaced', async (event: OrderPlacedEvent) => {
  await emailService.sendOrderConfirmation(event.customerId, event.orderId);
});

dispatcher.register('OrderPlaced', async (event: OrderPlacedEvent) => {
  await analyticsService.trackOrder(event);
});

dispatcher.register('OrderShipped', async (event: OrderShippedEvent) => {
  await emailService.sendShippingNotification(event.orderId, event.trackingNumber);
});

// In repository
class OrderRepository {
  async save(order: Order): Promise<void> {
    await this.db.save(order);
    await this.dispatcher.dispatchAll(order.pullEvents());
  }
}
```

## Benefits

| Benefit | Description |
|---------|-------------|
| Loose Coupling | Subjects and observers don't know each other directly |
| Open/Closed | Add observers without modifying subject |
| Broadcast | One notification reaches all interested parties |
| Dynamic | Add/remove observers at runtime |

## When to Use

- State changes should trigger multiple actions
- Decoupled event-driven systems
- UI updates from model changes
- Cross-cutting concerns (logging, analytics)
- Implementing message queues
