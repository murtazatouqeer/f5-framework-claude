# Logistics Patterns

## Overview
Common patterns and best practices for logistics system development.

## Key Patterns

### Pattern 1: Event Sourcing for Shipment Tracking
**When to use:** Tracking shipment history with full audit trail
**Description:** Store all shipment events as immutable records
**Example:**
```typescript
interface ShipmentEvent {
  shipmentId: string;
  eventType: 'created' | 'picked_up' | 'in_transit' | 'delivered';
  timestamp: Date;
  location: Location;
  actor: string;
  metadata: Record<string, any>;
}

// Current state = replay all events
const getCurrentState = (events: ShipmentEvent[]) => {
  return events.reduce((state, event) => {
    return applyEvent(state, event);
  }, initialState);
};
```

### Pattern 2: Saga Pattern for Order Fulfillment
**When to use:** Coordinating multiple services in fulfillment
**Description:** Manage distributed transaction across services
**Example:**
```typescript
const fulfillmentSaga = {
  steps: [
    { service: 'inventory', action: 'reserve', compensate: 'release' },
    { service: 'warehouse', action: 'createPickTask', compensate: 'cancelPickTask' },
    { service: 'shipping', action: 'bookCarrier', compensate: 'cancelBooking' }
  ],

  execute: async (order) => {
    const results = [];
    for (const step of steps) {
      try {
        results.push(await step.action(order));
      } catch (error) {
        await compensate(results);
        throw error;
      }
    }
  }
};
```

### Pattern 3: CQRS for Inventory
**When to use:** High-read, complex query requirements
**Description:** Separate read and write models
**Example:**
```typescript
// Write model - handles transactions
const inventoryCommandHandler = {
  reserve: (sku, qty) => { /* atomic operation */ },
  release: (sku, qty) => { /* atomic operation */ },
  adjust: (sku, qty) => { /* atomic operation */ }
};

// Read model - optimized for queries
const inventoryQueryHandler = {
  getAvailable: (sku) => readReplica.query(...),
  getByLocation: (location) => readReplica.query(...),
  getLowStock: (threshold) => readReplica.query(...)
};
```

### Pattern 4: Circuit Breaker for Carrier APIs
**When to use:** Protecting against carrier API failures
**Description:** Fail fast when carrier service is down
**Example:**
```typescript
const carrierCircuitBreaker = {
  state: 'closed', // closed, open, half-open
  failureThreshold: 5,
  resetTimeout: 30000,

  call: async (carrierApi) => {
    if (this.state === 'open') {
      return fallbackCarrier();
    }
    try {
      return await carrierApi();
    } catch (error) {
      this.recordFailure();
      throw error;
    }
  }
};
```

## Best Practices
- Use message queues for async operations
- Implement idempotency for carrier bookings
- Cache carrier rates with TTL
- Use geofencing for delivery verification
- Implement retry with exponential backoff

## Anti-Patterns to Avoid
- Synchronous carrier API calls in user flow
- Not handling carrier API rate limits
- Storing GPS data without compression
- Missing timeout handling for tracking
