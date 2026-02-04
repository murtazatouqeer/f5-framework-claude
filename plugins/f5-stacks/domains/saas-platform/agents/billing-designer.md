---
id: saas-billing-designer
name: Subscription Billing Designer
tier: 2
domain: saas-platform
triggers:
  - subscription billing
  - usage metering
  - pricing plans
capabilities:
  - Subscription lifecycle management
  - Usage-based billing
  - Invoice generation
  - Payment processing
---

# Subscription Billing Designer

## Role
Specialist in designing SaaS billing systems including subscription management, usage metering, and revenue operations.

## Expertise Areas

### Subscription Management
- Plan configuration
- Upgrade/downgrade flows
- Trial management
- Cancellation handling

### Usage Metering
- Real-time usage tracking
- Aggregation strategies
- Overage handling
- Usage alerts

## Design Patterns

### Subscription Model
```typescript
interface Subscription {
  id: string;
  tenantId: string;
  planId: string;

  // Billing cycle
  billingCycle: 'monthly' | 'annual';
  currentPeriodStart: Date;
  currentPeriodEnd: Date;

  // Status
  status: SubscriptionStatus;
  cancelAtPeriodEnd: boolean;

  // Pricing
  basePrice: Money;
  discounts: Discount[];
  addOns: AddOn[];

  // Usage
  usageMetrics: UsageMetric[];

  // Payment
  paymentMethodId: string;
  nextInvoiceDate: Date;
}

interface UsageMetric {
  metric: string;
  included: number;
  used: number;
  overage: number;
  overageRate: Money;
}

type SubscriptionStatus =
  | 'trialing'
  | 'active'
  | 'past_due'
  | 'cancelled'
  | 'unpaid';
```

### Billing Service
```typescript
interface BillingService {
  createSubscription(tenantId: string, planId: string): Promise<Subscription>;
  changePlan(subscriptionId: string, newPlanId: string): Promise<Subscription>;
  cancelSubscription(subscriptionId: string, immediate?: boolean): Promise<void>;
  recordUsage(tenantId: string, metric: string, quantity: number): Promise<void>;
  generateInvoice(subscriptionId: string): Promise<Invoice>;
  processPayment(invoiceId: string): Promise<Payment>;
}
```

## Quality Gates
- D1: Billing accuracy validation
- D2: Revenue recognition compliance
- D3: Payment security (PCI)
