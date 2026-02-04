# SaaS Billing Patterns

## Overview
Design patterns cho subscription billing systems.

## Key Patterns

### Pattern 1: Usage Metering
**When to use:** Usage-based pricing models
```typescript
class UsageMeter {
  async record(tenantId: string, metric: string, quantity: number) {
    await this.redis.hincrby(`usage:${tenantId}:${this.currentPeriod()}`, metric, quantity);
  }

  async getUsage(tenantId: string, metric: string): Promise<number> {
    return parseInt(await this.redis.hget(`usage:${tenantId}:${this.currentPeriod()}`, metric)) || 0;
  }

  async aggregateForBilling(tenantId: string): Promise<UsageSummary> {
    const usage = await this.redis.hgetall(`usage:${tenantId}:${this.currentPeriod()}`);
    return this.calculateOverages(tenantId, usage);
  }
}
```

### Pattern 2: Plan Change Proration
**When to use:** Mid-cycle plan changes
```typescript
const calculateProration = (oldPlan: Plan, newPlan: Plan, daysRemaining: number, totalDays: number) => {
  const unusedCredit = (oldPlan.price * daysRemaining) / totalDays;
  const newCharge = (newPlan.price * daysRemaining) / totalDays;
  return newCharge - unusedCredit;
};
```

### Pattern 3: Dunning Management
**When to use:** Handling failed payments
```typescript
interface DunningSchedule {
  attempts: DunningAttempt[];
  gracePeriodDays: number;
  actions: DunningAction[];
}

const dunningSchedule: DunningSchedule = {
  gracePeriodDays: 7,
  attempts: [
    { day: 1, action: 'retry_payment' },
    { day: 3, action: 'retry_payment', notify: 'email' },
    { day: 5, action: 'retry_payment', notify: 'email' },
    { day: 7, action: 'suspend_access' }
  ]
};
```

### Pattern 4: Revenue Recognition
**When to use:** Deferred revenue tracking
```typescript
interface RevenueSchedule {
  invoiceId: string;
  totalAmount: Money;
  recognitionPeriod: { start: Date; end: Date };
  recognized: Money;
  deferred: Money;
  entries: RevenueEntry[];
}
```

## Best Practices
- Idempotent billing operations
- Audit trail for all changes
- Grace periods for failed payments
- Clear upgrade/downgrade UX
