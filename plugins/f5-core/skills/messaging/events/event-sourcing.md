---
name: event-sourcing
description: Persisting state as a sequence of events
category: messaging/events
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Event Sourcing

## Overview

Event Sourcing is a pattern where application state is stored as a sequence of events rather than current state. The current state is derived by replaying all events from the beginning.

## Core Concepts

| Concept | Description |
|---------|-------------|
| **Event** | Immutable fact that happened |
| **Event Store** | Append-only log of all events |
| **Aggregate** | Domain object reconstructed from events |
| **Projection** | Read model built from events |
| **Snapshot** | Cached state at point in time |

## Traditional vs Event Sourced

```
Traditional:
┌────────────┐
│ Current    │  ← Only latest state
│ State: $80 │
└────────────┘

Event Sourced:
┌──────────────────────────────────────────────────┐
│ Created($100) → Debited($30) → Credited($10) │  ← Full history
└──────────────────────────────────────────────────┘
                  Current State: $80 (computed)
```

## Event Store Implementation

```typescript
interface StoredEvent {
  eventId: string;
  streamId: string;
  streamType: string;
  eventType: string;
  eventData: string;
  metadata: string;
  version: number;
  timestamp: Date;
}

class EventStore {
  constructor(private readonly db: Database) {}

  async append(
    streamId: string,
    streamType: string,
    events: DomainEvent[],
    expectedVersion: number
  ): Promise<void> {
    // Optimistic concurrency check
    const currentVersion = await this.getCurrentVersion(streamId);

    if (currentVersion !== expectedVersion) {
      throw new ConcurrencyError(
        `Expected version ${expectedVersion}, but found ${currentVersion}`
      );
    }

    // Append events atomically
    await this.db.transaction(async (tx) => {
      for (let i = 0; i < events.length; i++) {
        const event = events[i];
        const version = expectedVersion + i + 1;

        await tx.query(`
          INSERT INTO events (
            event_id, stream_id, stream_type, event_type,
            event_data, metadata, version, timestamp
          ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        `, [
          event.eventId,
          streamId,
          streamType,
          event.eventType,
          JSON.stringify(event),
          JSON.stringify(event.metadata),
          version,
          event.occurredOn,
        ]);
      }
    });
  }

  async getStream(streamId: string): Promise<StoredEvent[]> {
    return this.db.query(`
      SELECT * FROM events
      WHERE stream_id = $1
      ORDER BY version ASC
    `, [streamId]);
  }

  async getStreamFrom(
    streamId: string,
    fromVersion: number
  ): Promise<StoredEvent[]> {
    return this.db.query(`
      SELECT * FROM events
      WHERE stream_id = $1 AND version > $2
      ORDER BY version ASC
    `, [streamId, fromVersion]);
  }

  async getAllStreams(
    fromPosition: number,
    limit: number = 100
  ): Promise<{ events: StoredEvent[]; nextPosition: number }> {
    const events = await this.db.query(`
      SELECT * FROM events
      WHERE id > $1
      ORDER BY id ASC
      LIMIT $2
    `, [fromPosition, limit]);

    const nextPosition = events.length > 0
      ? events[events.length - 1].id
      : fromPosition;

    return { events, nextPosition };
  }

  private async getCurrentVersion(streamId: string): Promise<number> {
    const result = await this.db.query(`
      SELECT MAX(version) as version FROM events WHERE stream_id = $1
    `, [streamId]);

    return result[0]?.version || 0;
  }
}

class ConcurrencyError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ConcurrencyError';
  }
}
```

## Aggregate Implementation

```typescript
abstract class EventSourcedAggregate {
  private _uncommittedEvents: DomainEvent[] = [];
  protected _version: number = 0;

  get version(): number {
    return this._version;
  }

  get uncommittedEvents(): DomainEvent[] {
    return [...this._uncommittedEvents];
  }

  clearUncommittedEvents(): void {
    this._uncommittedEvents = [];
  }

  protected raise(event: DomainEvent): void {
    this._uncommittedEvents.push(event);
    this.apply(event);
    this._version++;
  }

  protected abstract apply(event: DomainEvent): void;

  loadFromHistory(events: DomainEvent[]): void {
    for (const event of events) {
      this.apply(event);
      this._version++;
    }
  }
}

// Concrete aggregate
class BankAccount extends EventSourcedAggregate {
  private _id!: string;
  private _balance: number = 0;
  private _status: 'active' | 'closed' = 'active';

  get id(): string { return this._id; }
  get balance(): number { return this._balance; }

  static create(accountId: string, initialBalance: number): BankAccount {
    const account = new BankAccount();

    account.raise(new AccountCreatedEvent(
      crypto.randomUUID(),
      accountId,
      initialBalance,
      { correlationId: crypto.randomUUID(), timestamp: new Date() }
    ));

    return account;
  }

  deposit(amount: number): void {
    if (this._status === 'closed') {
      throw new Error('Cannot deposit to closed account');
    }

    if (amount <= 0) {
      throw new Error('Amount must be positive');
    }

    this.raise(new MoneyDepositedEvent(
      crypto.randomUUID(),
      this._id,
      amount,
      { correlationId: crypto.randomUUID(), timestamp: new Date() }
    ));
  }

  withdraw(amount: number): void {
    if (this._status === 'closed') {
      throw new Error('Cannot withdraw from closed account');
    }

    if (amount <= 0) {
      throw new Error('Amount must be positive');
    }

    if (this._balance < amount) {
      throw new Error('Insufficient funds');
    }

    this.raise(new MoneyWithdrawnEvent(
      crypto.randomUUID(),
      this._id,
      amount,
      { correlationId: crypto.randomUUID(), timestamp: new Date() }
    ));
  }

  close(): void {
    if (this._balance !== 0) {
      throw new Error('Balance must be zero to close account');
    }

    this.raise(new AccountClosedEvent(
      crypto.randomUUID(),
      this._id,
      { correlationId: crypto.randomUUID(), timestamp: new Date() }
    ));
  }

  protected apply(event: DomainEvent): void {
    switch (event.eventType) {
      case 'account.created':
        this._id = event.aggregateId;
        this._balance = (event as AccountCreatedEvent).initialBalance;
        this._status = 'active';
        break;

      case 'money.deposited':
        this._balance += (event as MoneyDepositedEvent).amount;
        break;

      case 'money.withdrawn':
        this._balance -= (event as MoneyWithdrawnEvent).amount;
        break;

      case 'account.closed':
        this._status = 'closed';
        break;
    }
  }
}
```

## Repository Pattern

```typescript
class EventSourcedRepository<T extends EventSourcedAggregate> {
  constructor(
    private readonly eventStore: EventStore,
    private readonly streamType: string,
    private readonly factory: () => T
  ) {}

  async save(aggregate: T, streamId: string): Promise<void> {
    const events = aggregate.uncommittedEvents;

    if (events.length === 0) return;

    const expectedVersion = aggregate.version - events.length;

    await this.eventStore.append(
      streamId,
      this.streamType,
      events,
      expectedVersion
    );

    aggregate.clearUncommittedEvents();
  }

  async getById(streamId: string): Promise<T | null> {
    const storedEvents = await this.eventStore.getStream(streamId);

    if (storedEvents.length === 0) {
      return null;
    }

    const aggregate = this.factory();
    const events = storedEvents.map(e => JSON.parse(e.eventData) as DomainEvent);
    aggregate.loadFromHistory(events);

    return aggregate;
  }
}

// Usage
const accountRepository = new EventSourcedRepository<BankAccount>(
  eventStore,
  'BankAccount',
  () => new BankAccount()
);

// Create account
const account = BankAccount.create('acc-123', 1000);
await accountRepository.save(account, 'acc-123');

// Load and modify
const loaded = await accountRepository.getById('acc-123');
loaded?.deposit(500);
loaded?.withdraw(200);
await accountRepository.save(loaded!, 'acc-123');
```

## Snapshots

```typescript
interface Snapshot {
  streamId: string;
  version: number;
  state: string;
  createdAt: Date;
}

class SnapshotStore {
  constructor(private readonly db: Database) {}

  async save(streamId: string, version: number, state: object): Promise<void> {
    await this.db.query(`
      INSERT INTO snapshots (stream_id, version, state, created_at)
      VALUES ($1, $2, $3, $4)
      ON CONFLICT (stream_id) DO UPDATE
      SET version = $2, state = $3, created_at = $4
    `, [streamId, version, JSON.stringify(state), new Date()]);
  }

  async get(streamId: string): Promise<Snapshot | null> {
    const rows = await this.db.query(`
      SELECT * FROM snapshots WHERE stream_id = $1
    `, [streamId]);

    return rows[0] || null;
  }
}

class SnapshotRepository<T extends EventSourcedAggregate> {
  private readonly snapshotInterval = 100; // Snapshot every 100 events

  constructor(
    private readonly eventStore: EventStore,
    private readonly snapshotStore: SnapshotStore,
    private readonly streamType: string,
    private readonly factory: () => T,
    private readonly serialize: (aggregate: T) => object,
    private readonly deserialize: (state: object, aggregate: T) => void
  ) {}

  async getById(streamId: string): Promise<T | null> {
    const aggregate = this.factory();

    // Try to load from snapshot
    const snapshot = await this.snapshotStore.get(streamId);

    if (snapshot) {
      this.deserialize(JSON.parse(snapshot.state), aggregate);

      // Load events after snapshot
      const newEvents = await this.eventStore.getStreamFrom(
        streamId,
        snapshot.version
      );

      const events = newEvents.map(e => JSON.parse(e.eventData) as DomainEvent);
      aggregate.loadFromHistory(events);
    } else {
      // Load all events
      const storedEvents = await this.eventStore.getStream(streamId);

      if (storedEvents.length === 0) {
        return null;
      }

      const events = storedEvents.map(e => JSON.parse(e.eventData) as DomainEvent);
      aggregate.loadFromHistory(events);
    }

    return aggregate;
  }

  async save(aggregate: T, streamId: string): Promise<void> {
    const events = aggregate.uncommittedEvents;
    if (events.length === 0) return;

    const expectedVersion = aggregate.version - events.length;

    await this.eventStore.append(
      streamId,
      this.streamType,
      events,
      expectedVersion
    );

    aggregate.clearUncommittedEvents();

    // Create snapshot if needed
    if (aggregate.version % this.snapshotInterval === 0) {
      await this.snapshotStore.save(
        streamId,
        aggregate.version,
        this.serialize(aggregate)
      );
    }
  }
}
```

## Projections

```typescript
// Read model
interface AccountView {
  id: string;
  balance: number;
  status: string;
  lastTransaction: Date;
  transactionCount: number;
}

class AccountProjection {
  constructor(private readonly db: Database) {}

  async handle(event: DomainEvent): Promise<void> {
    switch (event.eventType) {
      case 'account.created':
        await this.handleAccountCreated(event as AccountCreatedEvent);
        break;
      case 'money.deposited':
        await this.handleMoneyDeposited(event as MoneyDepositedEvent);
        break;
      case 'money.withdrawn':
        await this.handleMoneyWithdrawn(event as MoneyWithdrawnEvent);
        break;
      case 'account.closed':
        await this.handleAccountClosed(event as AccountClosedEvent);
        break;
    }
  }

  private async handleAccountCreated(event: AccountCreatedEvent): Promise<void> {
    await this.db.query(`
      INSERT INTO account_views (id, balance, status, transaction_count, last_transaction)
      VALUES ($1, $2, 'active', 1, $3)
    `, [event.aggregateId, event.initialBalance, event.occurredOn]);
  }

  private async handleMoneyDeposited(event: MoneyDepositedEvent): Promise<void> {
    await this.db.query(`
      UPDATE account_views
      SET balance = balance + $1,
          transaction_count = transaction_count + 1,
          last_transaction = $2
      WHERE id = $3
    `, [event.amount, event.occurredOn, event.aggregateId]);
  }

  private async handleMoneyWithdrawn(event: MoneyWithdrawnEvent): Promise<void> {
    await this.db.query(`
      UPDATE account_views
      SET balance = balance - $1,
          transaction_count = transaction_count + 1,
          last_transaction = $2
      WHERE id = $3
    `, [event.amount, event.occurredOn, event.aggregateId]);
  }

  private async handleAccountClosed(event: AccountClosedEvent): Promise<void> {
    await this.db.query(`
      UPDATE account_views SET status = 'closed' WHERE id = $1
    `, [event.aggregateId]);
  }

  // Query methods
  async getAccount(id: string): Promise<AccountView | null> {
    const rows = await this.db.query(`
      SELECT * FROM account_views WHERE id = $1
    `, [id]);

    return rows[0] || null;
  }

  async getActiveAccounts(): Promise<AccountView[]> {
    return this.db.query(`
      SELECT * FROM account_views WHERE status = 'active'
    `);
  }
}
```

## Projection Rebuilding

```typescript
class ProjectionRebuilder {
  constructor(
    private readonly eventStore: EventStore,
    private readonly projections: Map<string, Projection>
  ) {}

  async rebuild(projectionName: string): Promise<void> {
    const projection = this.projections.get(projectionName);
    if (!projection) throw new Error(`Unknown projection: ${projectionName}`);

    // Clear existing projection data
    await projection.reset();

    // Replay all events
    let position = 0;
    const batchSize = 1000;

    while (true) {
      const { events, nextPosition } = await this.eventStore.getAllStreams(
        position,
        batchSize
      );

      if (events.length === 0) break;

      for (const storedEvent of events) {
        const event = JSON.parse(storedEvent.eventData) as DomainEvent;
        await projection.handle(event);
      }

      position = nextPosition;

      console.log(`Processed ${position} events`);
    }

    console.log('Projection rebuild complete');
  }
}
```

## Benefits and Trade-offs

| Benefit | Trade-off |
|---------|-----------|
| Complete audit trail | Storage growth |
| Temporal queries | Query complexity |
| Debug with replay | Learning curve |
| Event-driven ready | Eventual consistency |
| Schema evolution | Event versioning |

## When to Use

### Good Fit
- Audit requirements (finance, healthcare)
- Complex domain logic
- Temporal queries needed
- Event-driven architecture
- High write scalability

### Poor Fit
- Simple CRUD operations
- Ad-hoc queries needed
- Strong consistency required
- Small, simple domains

## Best Practices

| Practice | Implementation |
|----------|----------------|
| **Immutable events** | Never modify stored events |
| **Event versioning** | Support schema evolution |
| **Use snapshots** | For aggregates with many events |
| **Idempotent projections** | Handle replay safely |
| **Separate read/write** | CQRS for queries |
