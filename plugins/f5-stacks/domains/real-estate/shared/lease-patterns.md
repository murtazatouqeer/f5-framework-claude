# Lease Management Patterns

## Overview
Patterns and best practices for lease management systems in real estate.

## Key Patterns

### Pattern 1: State Machine for Lease Lifecycle
**When to use:** Managing complex lease state transitions
**Description:** Formal state machine for lease status management
**Example:**
```typescript
type LeaseState =
  | 'draft'
  | 'pending_signature'
  | 'signed'
  | 'active'
  | 'renewal_offered'
  | 'notice_given'
  | 'move_out_scheduled'
  | 'ended';

type LeaseEvent =
  | 'submit_for_signature'
  | 'tenant_signed'
  | 'landlord_signed'
  | 'move_in'
  | 'offer_renewal'
  | 'accept_renewal'
  | 'decline_renewal'
  | 'give_notice'
  | 'schedule_move_out'
  | 'complete_move_out'
  | 'cancel';

const leaseStateMachine = {
  draft: {
    submit_for_signature: 'pending_signature',
    cancel: 'cancelled'
  },
  pending_signature: {
    tenant_signed: 'pending_landlord_signature',
    cancel: 'cancelled'
  },
  pending_landlord_signature: {
    landlord_signed: 'signed',
    cancel: 'cancelled'
  },
  signed: {
    move_in: 'active'
  },
  active: {
    offer_renewal: 'renewal_offered',
    give_notice: 'notice_given'
  },
  renewal_offered: {
    accept_renewal: 'active',
    decline_renewal: 'notice_given'
  },
  notice_given: {
    schedule_move_out: 'move_out_scheduled'
  },
  move_out_scheduled: {
    complete_move_out: 'ended'
  }
};

class LeaseStateMachine {
  transition(lease: Lease, event: LeaseEvent): LeaseState {
    const currentState = lease.status;
    const nextState = leaseStateMachine[currentState]?.[event];

    if (!nextState) {
      throw new Error(`Invalid transition: ${currentState} -> ${event}`);
    }

    return nextState;
  }

  canTransition(lease: Lease, event: LeaseEvent): boolean {
    return !!leaseStateMachine[lease.status]?.[event];
  }

  getAvailableActions(lease: Lease): LeaseEvent[] {
    return Object.keys(leaseStateMachine[lease.status] || {}) as LeaseEvent[];
  }
}
```

### Pattern 2: Rent Ledger with Double-Entry
**When to use:** Accurate financial tracking for rent
**Description:** Double-entry bookkeeping for rent transactions
**Example:**
```typescript
interface LedgerEntry {
  id: string;
  leaseId: string;
  date: Date;
  type: 'charge' | 'payment' | 'credit' | 'adjustment';
  description: string;
  debit: Money;  // What tenant owes
  credit: Money; // What was paid/credited
  balance: Money;
  referenceId?: string;
  referenceType?: 'invoice' | 'payment' | 'late_fee' | 'deposit';
}

class RentLedgerService {
  async recordCharge(
    leaseId: string,
    charge: {
      amount: Money;
      description: string;
      dueDate: Date;
      type: 'rent' | 'late_fee' | 'utility' | 'other';
    }
  ): Promise<LedgerEntry> {
    const currentBalance = await this.getBalance(leaseId);

    return this.repository.create({
      leaseId,
      date: new Date(),
      type: 'charge',
      description: charge.description,
      debit: charge.amount,
      credit: { amount: 0, currency: charge.amount.currency },
      balance: {
        amount: currentBalance.amount + charge.amount.amount,
        currency: charge.amount.currency
      }
    });
  }

  async recordPayment(
    leaseId: string,
    payment: {
      amount: Money;
      method: PaymentMethod;
      transactionId: string;
    }
  ): Promise<LedgerEntry> {
    const currentBalance = await this.getBalance(leaseId);

    const entry = await this.repository.create({
      leaseId,
      date: new Date(),
      type: 'payment',
      description: `Payment via ${payment.method}`,
      debit: { amount: 0, currency: payment.amount.currency },
      credit: payment.amount,
      balance: {
        amount: currentBalance.amount - payment.amount.amount,
        currency: payment.amount.currency
      },
      referenceId: payment.transactionId,
      referenceType: 'payment'
    });

    // Apply payment to oldest charges first (FIFO)
    await this.applyPaymentToCharges(leaseId, payment.amount);

    return entry;
  }

  async getStatement(
    leaseId: string,
    period: { start: Date; end: Date }
  ): Promise<{
    entries: LedgerEntry[];
    openingBalance: Money;
    closingBalance: Money;
    totalCharges: Money;
    totalPayments: Money;
  }> {
    const entries = await this.repository.findByLease(leaseId, period);
    const openingBalance = await this.getBalanceAsOf(leaseId, period.start);

    return {
      entries,
      openingBalance,
      closingBalance: entries[entries.length - 1]?.balance || openingBalance,
      totalCharges: this.sumDebits(entries),
      totalPayments: this.sumCredits(entries)
    };
  }
}
```

### Pattern 3: Prorated Rent Calculation
**When to use:** Partial month rent calculations
**Description:** Various proration methods for rent
**Example:**
```typescript
type ProrationMethod =
  | 'calendar_days'      // Actual days in month
  | 'banking_days'       // 30-day month
  | 'actual_365'         // 365 days per year
  | 'actual_360';        // 360 days per year

class RentProrationService {
  calculate(
    monthlyRent: Money,
    startDate: Date,
    method: ProrationMethod = 'calendar_days'
  ): Money {
    const daysInMonth = this.getDaysInMonth(startDate);
    const daysRemaining = daysInMonth - startDate.getDate() + 1;

    let dailyRate: number;

    switch (method) {
      case 'calendar_days':
        dailyRate = monthlyRent.amount / daysInMonth;
        break;
      case 'banking_days':
        dailyRate = monthlyRent.amount / 30;
        break;
      case 'actual_365':
        dailyRate = (monthlyRent.amount * 12) / 365;
        break;
      case 'actual_360':
        dailyRate = (monthlyRent.amount * 12) / 360;
        break;
    }

    return {
      amount: Math.round(dailyRate * daysRemaining * 100) / 100,
      currency: monthlyRent.currency
    };
  }

  calculateMoveOutProration(
    monthlyRent: Money,
    moveOutDate: Date,
    method: ProrationMethod = 'calendar_days'
  ): Money {
    const daysOccupied = moveOutDate.getDate();
    const daysInMonth = this.getDaysInMonth(moveOutDate);

    let dailyRate: number;

    switch (method) {
      case 'calendar_days':
        dailyRate = monthlyRent.amount / daysInMonth;
        break;
      // ... other methods
    }

    return {
      amount: Math.round(dailyRate * daysOccupied * 100) / 100,
      currency: monthlyRent.currency
    };
  }

  private getDaysInMonth(date: Date): number {
    return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
  }
}
```

### Pattern 4: Security Deposit Reconciliation
**When to use:** Move-out deposit processing
**Description:** Systematic deposit deduction and refund calculation
**Example:**
```typescript
interface DepositReconciliation {
  leaseId: string;
  originalDeposit: Money;
  deductions: DepositDeduction[];
  refundAmount: Money;
  refundMethod: 'check' | 'ach';
  itemizedStatement: Document;
  dueDate: Date; // State-specific deadline
}

interface DepositDeduction {
  category: 'cleaning' | 'repairs' | 'unpaid_rent' | 'damages' | 'other';
  description: string;
  amount: Money;
  evidence?: {
    photos: string[];
    invoices: Document[];
    moveInCondition: string;
    moveOutCondition: string;
  };
}

class DepositReconciliationService {
  async reconcile(
    leaseId: string,
    inspection: MoveOutInspection
  ): Promise<DepositReconciliation> {
    const lease = await this.leaseService.findById(leaseId);
    const moveInInspection = await this.inspectionService.getMoveIn(leaseId);

    const deductions: DepositDeduction[] = [];

    // Compare move-in vs move-out condition
    for (const item of inspection.items) {
      const moveInItem = moveInInspection.items.find(i => i.area === item.area);

      if (item.condition !== moveInItem?.condition) {
        const damage = this.assessDamage(moveInItem, item);
        if (damage) {
          deductions.push(damage);
        }
      }
    }

    // Check for unpaid rent
    const balance = await this.ledgerService.getBalance(leaseId);
    if (balance.amount > 0) {
      deductions.push({
        category: 'unpaid_rent',
        description: 'Outstanding rent balance',
        amount: balance
      });
    }

    // Calculate refund
    const totalDeductions = deductions.reduce(
      (sum, d) => sum + d.amount.amount,
      0
    );
    const refundAmount = {
      amount: Math.max(0, lease.securityDeposit.amount - totalDeductions),
      currency: lease.securityDeposit.currency
    };

    // Generate itemized statement
    const statement = await this.generateStatement(lease, deductions, refundAmount);

    return {
      leaseId,
      originalDeposit: lease.securityDeposit,
      deductions,
      refundAmount,
      refundMethod: 'check',
      itemizedStatement: statement,
      dueDate: this.calculateDeadline(lease.state, inspection.date)
    };
  }

  private calculateDeadline(state: string, moveOutDate: Date): Date {
    // State-specific deadlines (days after move-out)
    const deadlines: Record<string, number> = {
      'CA': 21,
      'NY': 14,
      'TX': 30,
      'FL': 15,
      // ... other states
    };

    const days = deadlines[state] || 30;
    return addDays(moveOutDate, days);
  }
}
```

## Best Practices
- Use state machines for lifecycle management
- Implement double-entry bookkeeping for financials
- Track all condition changes with photos
- Know state-specific regulations
- Automate compliance deadlines

## Anti-Patterns to Avoid
- Manual balance calculations without ledger
- Ignoring state-specific deposit laws
- Not documenting move-in condition
- Applying payments without FIFO order
