# E-Commerce Patterns

## Overview
Common patterns and best practices for e-commerce development.

## Key Patterns

### Pattern 1: Cart Persistence Strategy
**When to use:** When needing to maintain cart state across sessions
**Description:** Use combination of local storage and server-side storage
**Example:**
```typescript
// Guest: localStorage + sessionId
// Authenticated: Server-side with merge on login
const cartStrategy = {
  guest: {
    primary: 'localStorage',
    sync: 'sessionId',
    expiry: '30 days'
  },
  authenticated: {
    primary: 'database',
    merge: 'onLogin'
  }
};
```

### Pattern 2: Inventory Reservation
**When to use:** During checkout to prevent overselling
**Description:** Reserve inventory when adding to cart or during checkout
**Example:**
```typescript
// Soft reservation at checkout
await inventoryService.reserve({
  sku: 'ABC123',
  quantity: 2,
  reservationId: checkoutId,
  expiresAt: addMinutes(now(), 15)
});
```

### Pattern 3: Price Calculation Pipeline
**When to use:** When calculating final price with multiple modifiers
**Description:** Chain of responsibility for price calculation
**Example:**
```typescript
const pricePipeline = [
  new BasePriceCalculator(),
  new SalePriceCalculator(),
  new VolumeDiscountCalculator(),
  new CouponCalculator(),
  new TaxCalculator(),
  new ShippingCalculator()
];
```

### Pattern 4: Order State Machine
**When to use:** Managing order lifecycle
**Description:** Finite state machine cho order states
**Example:**
```typescript
const orderStateMachine = {
  pending: ['paid', 'cancelled'],
  paid: ['processing', 'refunded'],
  processing: ['shipped', 'cancelled'],
  shipped: ['delivered', 'returned'],
  delivered: ['completed', 'returned']
};
```

## Best Practices
- Use optimistic UI updates for cart operations
- Implement idempotency for payment processing
- Cache product data aggressively with proper invalidation
- Use webhooks for payment and shipping updates
- Implement rate limiting for cart and checkout APIs

## Anti-Patterns to Avoid
- Storing card data directly (use tokenization)
- Calculating prices client-side only
- Not handling race conditions in inventory
- Tight coupling between cart and order services
