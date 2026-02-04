# Subscription Flow Template

## Subscription Lifecycle

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    Trial    │────▶│   Active    │────▶│  Past Due   │────▶│  Cancelled  │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
      │                   │                   │
      ▼                   ▼                   ▼
  Free features      Full access        Grace period
  Time-limited       Billing active     Payment retry
  Convert prompt     Upgrades           Reactivation
```

## Subscription States

```typescript
type SubscriptionStatus =
  | 'trialing'
  | 'active'
  | 'past_due'
  | 'unpaid'
  | 'cancelled'
  | 'paused';
```

## Subscription Model

```typescript
interface Subscription {
  id: string;
  tenantId: string;
  status: SubscriptionStatus;

  // Plan
  plan: {
    id: string;
    name: string;
    price: Money;
    interval: 'month' | 'year';
    features: string[];
  };

  // Billing
  billing: {
    currentPeriodStart: Date;
    currentPeriodEnd: Date;
    cancelAtPeriodEnd: boolean;
    paymentMethodId: string;
  };

  // Usage
  usage: {
    [metric: string]: {
      included: number;
      used: number;
      overage: number;
    };
  };

  // Trial
  trial?: {
    start: Date;
    end: Date;
    extended: boolean;
  };
}
```

## Billing Events

```typescript
interface BillingEvent {
  type: BillingEventType;
  subscriptionId: string;
  timestamp: Date;
  data: Record<string, any>;
}

type BillingEventType =
  | 'subscription.created'
  | 'subscription.updated'
  | 'subscription.cancelled'
  | 'invoice.created'
  | 'invoice.paid'
  | 'invoice.failed'
  | 'payment.succeeded'
  | 'payment.failed'
  | 'trial.ending'
  | 'trial.ended';
```

## Invoice Generation

```typescript
interface Invoice {
  id: string;
  subscriptionId: string;
  tenantId: string;
  status: 'draft' | 'open' | 'paid' | 'void' | 'uncollectible';

  // Line items
  lineItems: {
    description: string;
    quantity: number;
    unitPrice: Money;
    amount: Money;
  }[];

  // Totals
  subtotal: Money;
  tax: Money;
  total: Money;
  amountPaid: Money;
  amountDue: Money;

  // Dates
  periodStart: Date;
  periodEnd: Date;
  dueDate: Date;
  paidAt?: Date;
}
```
