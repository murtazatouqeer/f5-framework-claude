---
name: state-machine-pattern
description: State Machine pattern for managing object states and transitions
category: architecture/design-patterns/behavioral
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# State Machine Pattern

## Overview

The State Machine pattern allows an object to alter its behavior when its
internal state changes. The object will appear to change its class.

## Basic Implementation

```typescript
// State interface
interface OrderState {
  getName(): string;
  confirm(order: Order): void;
  ship(order: Order, trackingNumber: string): void;
  deliver(order: Order): void;
  cancel(order: Order, reason: string): void;
}

// Concrete States
class PendingState implements OrderState {
  getName(): string {
    return 'pending';
  }

  confirm(order: Order): void {
    order.setState(new ConfirmedState());
    order.addEvent({ type: 'confirmed', timestamp: new Date() });
  }

  ship(order: Order, trackingNumber: string): void {
    throw new InvalidStateTransitionError('Cannot ship pending order');
  }

  deliver(order: Order): void {
    throw new InvalidStateTransitionError('Cannot deliver pending order');
  }

  cancel(order: Order, reason: string): void {
    order.setState(new CancelledState(reason));
    order.addEvent({ type: 'cancelled', reason, timestamp: new Date() });
  }
}

class ConfirmedState implements OrderState {
  getName(): string {
    return 'confirmed';
  }

  confirm(order: Order): void {
    throw new InvalidStateTransitionError('Order already confirmed');
  }

  ship(order: Order, trackingNumber: string): void {
    order.setTrackingNumber(trackingNumber);
    order.setState(new ShippedState());
    order.addEvent({ type: 'shipped', trackingNumber, timestamp: new Date() });
  }

  deliver(order: Order): void {
    throw new InvalidStateTransitionError('Cannot deliver before shipping');
  }

  cancel(order: Order, reason: string): void {
    order.setState(new CancelledState(reason));
    order.addEvent({ type: 'cancelled', reason, timestamp: new Date() });
  }
}

class ShippedState implements OrderState {
  getName(): string {
    return 'shipped';
  }

  confirm(order: Order): void {
    throw new InvalidStateTransitionError('Order already shipped');
  }

  ship(order: Order, trackingNumber: string): void {
    throw new InvalidStateTransitionError('Order already shipped');
  }

  deliver(order: Order): void {
    order.setState(new DeliveredState());
    order.addEvent({ type: 'delivered', timestamp: new Date() });
  }

  cancel(order: Order, reason: string): void {
    throw new InvalidStateTransitionError('Cannot cancel shipped order');
  }
}

class DeliveredState implements OrderState {
  getName(): string {
    return 'delivered';
  }

  confirm(order: Order): void {
    throw new InvalidStateTransitionError('Order already delivered');
  }

  ship(order: Order, trackingNumber: string): void {
    throw new InvalidStateTransitionError('Order already delivered');
  }

  deliver(order: Order): void {
    throw new InvalidStateTransitionError('Order already delivered');
  }

  cancel(order: Order, reason: string): void {
    throw new InvalidStateTransitionError('Cannot cancel delivered order');
  }
}

class CancelledState implements OrderState {
  constructor(private reason: string) {}

  getName(): string {
    return 'cancelled';
  }

  confirm(order: Order): void {
    throw new InvalidStateTransitionError('Cannot modify cancelled order');
  }

  ship(order: Order, trackingNumber: string): void {
    throw new InvalidStateTransitionError('Cannot modify cancelled order');
  }

  deliver(order: Order): void {
    throw new InvalidStateTransitionError('Cannot modify cancelled order');
  }

  cancel(order: Order, reason: string): void {
    throw new InvalidStateTransitionError('Order already cancelled');
  }
}

// Context
class Order {
  private state: OrderState = new PendingState();
  private events: OrderEvent[] = [];
  private trackingNumber?: string;

  constructor(
    public readonly id: string,
    public readonly customerId: string,
    public readonly items: OrderItem[]
  ) {}

  setState(state: OrderState): void {
    this.state = state;
  }

  getState(): string {
    return this.state.getName();
  }

  setTrackingNumber(number: string): void {
    this.trackingNumber = number;
  }

  addEvent(event: OrderEvent): void {
    this.events.push(event);
  }

  // Delegate to state
  confirm(): void {
    this.state.confirm(this);
  }

  ship(trackingNumber: string): void {
    this.state.ship(this, trackingNumber);
  }

  deliver(): void {
    this.state.deliver(this);
  }

  cancel(reason: string): void {
    this.state.cancel(this, reason);
  }
}

// Usage
const order = new Order('ORD-001', 'CUST-001', items);
console.log(order.getState()); // 'pending'

order.confirm();
console.log(order.getState()); // 'confirmed'

order.ship('TRK-12345');
console.log(order.getState()); // 'shipped'

order.deliver();
console.log(order.getState()); // 'delivered'

// This throws error
// order.cancel('Changed mind'); // InvalidStateTransitionError
```

## Declarative State Machine

```typescript
// State machine configuration
interface StateMachineConfig<S extends string, E extends string> {
  initial: S;
  states: {
    [key in S]: {
      on?: {
        [event in E]?: {
          target: S;
          guard?: (context: any) => boolean;
          action?: (context: any) => void;
        };
      };
      onEntry?: (context: any) => void;
      onExit?: (context: any) => void;
    };
  };
}

class StateMachine<S extends string, E extends string, C = any> {
  private currentState: S;
  private context: C;

  constructor(
    private config: StateMachineConfig<S, E>,
    initialContext: C
  ) {
    this.currentState = config.initial;
    this.context = initialContext;
    this.executeEntry(this.currentState);
  }

  getState(): S {
    return this.currentState;
  }

  getContext(): C {
    return this.context;
  }

  send(event: E): boolean {
    const stateConfig = this.config.states[this.currentState];
    const transition = stateConfig.on?.[event];

    if (!transition) {
      return false; // Event not valid in current state
    }

    // Check guard
    if (transition.guard && !transition.guard(this.context)) {
      return false;
    }

    // Execute exit action
    this.executeExit(this.currentState);

    // Execute transition action
    if (transition.action) {
      transition.action(this.context);
    }

    // Change state
    this.currentState = transition.target;

    // Execute entry action
    this.executeEntry(this.currentState);

    return true;
  }

  private executeEntry(state: S): void {
    const stateConfig = this.config.states[state];
    if (stateConfig.onEntry) {
      stateConfig.onEntry(this.context);
    }
  }

  private executeExit(state: S): void {
    const stateConfig = this.config.states[state];
    if (stateConfig.onExit) {
      stateConfig.onExit(this.context);
    }
  }
}

// Define order state machine
type OrderStates = 'pending' | 'confirmed' | 'shipped' | 'delivered' | 'cancelled';
type OrderEvents = 'CONFIRM' | 'SHIP' | 'DELIVER' | 'CANCEL';

interface OrderContext {
  orderId: string;
  trackingNumber?: string;
  cancelReason?: string;
}

const orderMachine: StateMachineConfig<OrderStates, OrderEvents> = {
  initial: 'pending',
  states: {
    pending: {
      on: {
        CONFIRM: { target: 'confirmed' },
        CANCEL: {
          target: 'cancelled',
          action: (ctx) => { ctx.cancelReason = 'Cancelled while pending'; },
        },
      },
      onEntry: (ctx) => console.log(`Order ${ctx.orderId} is pending`),
    },
    confirmed: {
      on: {
        SHIP: {
          target: 'shipped',
          action: (ctx) => { ctx.trackingNumber = `TRK-${Date.now()}`; },
        },
        CANCEL: { target: 'cancelled' },
      },
      onEntry: (ctx) => console.log(`Order ${ctx.orderId} confirmed`),
    },
    shipped: {
      on: {
        DELIVER: { target: 'delivered' },
      },
      onEntry: (ctx) => console.log(`Order ${ctx.orderId} shipped: ${ctx.trackingNumber}`),
    },
    delivered: {
      onEntry: (ctx) => console.log(`Order ${ctx.orderId} delivered!`),
    },
    cancelled: {
      onEntry: (ctx) => console.log(`Order ${ctx.orderId} cancelled`),
    },
  },
};

// Usage
const machine = new StateMachine(orderMachine, { orderId: 'ORD-001' });

machine.send('CONFIRM');  // pending → confirmed
machine.send('SHIP');     // confirmed → shipped
machine.send('DELIVER');  // shipped → delivered
machine.send('CANCEL');   // Returns false - not valid in delivered state
```

## XState-Style Machine

```typescript
// More advanced state machine with hierarchical states
interface MachineDefinition<C, E extends { type: string }> {
  id: string;
  initial: string;
  context: C;
  states: Record<string, StateNode<C, E>>;
}

interface StateNode<C, E extends { type: string }> {
  initial?: string;
  states?: Record<string, StateNode<C, E>>;
  on?: Record<string, Transition<C, E>>;
  entry?: Action<C, E>[];
  exit?: Action<C, E>[];
}

type Transition<C, E> = {
  target: string;
  guard?: (context: C, event: E) => boolean;
  actions?: Action<C, E>[];
};

type Action<C, E> = (context: C, event: E) => void;

// Order machine with nested states
const orderMachineDef: MachineDefinition<OrderContext, OrderEvent> = {
  id: 'order',
  initial: 'pending',
  context: { orderId: '', items: [] },
  states: {
    pending: {
      on: {
        CONFIRM: {
          target: 'processing',
          guard: (ctx) => ctx.items.length > 0,
          actions: [(ctx) => { ctx.confirmedAt = new Date(); }],
        },
        CANCEL: { target: 'cancelled' },
      },
    },
    processing: {
      initial: 'payment',
      states: {
        payment: {
          on: {
            PAYMENT_SUCCESS: { target: 'fulfillment' },
            PAYMENT_FAILED: { target: '#order.cancelled' },
          },
        },
        fulfillment: {
          on: {
            SHIPPED: { target: '#order.shipped' },
          },
        },
      },
    },
    shipped: {
      on: {
        DELIVERED: { target: 'delivered' },
        RETURNED: { target: 'returned' },
      },
    },
    delivered: {
      type: 'final',
    },
    cancelled: {
      type: 'final',
    },
    returned: {
      type: 'final',
    },
  },
};
```

## Workflow Engine

```typescript
// Simple workflow engine using state machines
interface WorkflowStep {
  id: string;
  name: string;
  handler: (context: WorkflowContext) => Promise<WorkflowResult>;
  next: string | null;
  onError?: string;
}

interface WorkflowDefinition {
  id: string;
  name: string;
  initialStep: string;
  steps: Record<string, WorkflowStep>;
}

interface WorkflowContext {
  workflowId: string;
  data: Record<string, any>;
  currentStep: string;
  history: WorkflowHistoryEntry[];
}

interface WorkflowResult {
  success: boolean;
  data?: Record<string, any>;
  nextStep?: string;
}

class WorkflowEngine {
  constructor(private definition: WorkflowDefinition) {}

  async start(initialData: Record<string, any>): Promise<WorkflowContext> {
    const context: WorkflowContext = {
      workflowId: crypto.randomUUID(),
      data: initialData,
      currentStep: this.definition.initialStep,
      history: [],
    };

    return this.executeWorkflow(context);
  }

  private async executeWorkflow(context: WorkflowContext): Promise<WorkflowContext> {
    while (context.currentStep) {
      const step = this.definition.steps[context.currentStep];
      if (!step) {
        throw new Error(`Unknown step: ${context.currentStep}`);
      }

      context.history.push({
        step: step.id,
        startedAt: new Date(),
        status: 'running',
      });

      try {
        const result = await step.handler(context);

        context.data = { ...context.data, ...result.data };
        context.history[context.history.length - 1].status = 'completed';
        context.history[context.history.length - 1].completedAt = new Date();

        // Determine next step
        context.currentStep = result.nextStep ?? step.next ?? '';

      } catch (error) {
        context.history[context.history.length - 1].status = 'failed';
        context.history[context.history.length - 1].error = error.message;

        if (step.onError) {
          context.currentStep = step.onError;
        } else {
          throw error;
        }
      }
    }

    return context;
  }
}

// Define order fulfillment workflow
const orderWorkflow: WorkflowDefinition = {
  id: 'order-fulfillment',
  name: 'Order Fulfillment Workflow',
  initialStep: 'validate',
  steps: {
    validate: {
      id: 'validate',
      name: 'Validate Order',
      handler: async (ctx) => {
        // Validate order data
        if (!ctx.data.items?.length) {
          throw new Error('Order has no items');
        }
        return { success: true };
      },
      next: 'reserve-inventory',
      onError: 'handle-error',
    },
    'reserve-inventory': {
      id: 'reserve-inventory',
      name: 'Reserve Inventory',
      handler: async (ctx) => {
        // Reserve inventory
        const reservationId = await inventoryService.reserve(ctx.data.items);
        return { success: true, data: { reservationId } };
      },
      next: 'process-payment',
      onError: 'handle-error',
    },
    'process-payment': {
      id: 'process-payment',
      name: 'Process Payment',
      handler: async (ctx) => {
        const paymentResult = await paymentService.process(ctx.data.paymentInfo);
        return {
          success: paymentResult.success,
          data: { paymentId: paymentResult.id },
        };
      },
      next: 'create-shipment',
      onError: 'rollback-inventory',
    },
    'create-shipment': {
      id: 'create-shipment',
      name: 'Create Shipment',
      handler: async (ctx) => {
        const shipment = await shippingService.createShipment(ctx.data);
        return {
          success: true,
          data: { trackingNumber: shipment.trackingNumber },
        };
      },
      next: 'send-confirmation',
    },
    'send-confirmation': {
      id: 'send-confirmation',
      name: 'Send Confirmation',
      handler: async (ctx) => {
        await emailService.sendOrderConfirmation(ctx.data);
        return { success: true };
      },
      next: null, // End of workflow
    },
    'rollback-inventory': {
      id: 'rollback-inventory',
      name: 'Rollback Inventory',
      handler: async (ctx) => {
        await inventoryService.release(ctx.data.reservationId);
        return { success: true };
      },
      next: 'handle-error',
    },
    'handle-error': {
      id: 'handle-error',
      name: 'Handle Error',
      handler: async (ctx) => {
        await notificationService.notifyAdmin(ctx);
        return { success: true };
      },
      next: null,
    },
  },
};

// Usage
const engine = new WorkflowEngine(orderWorkflow);
const result = await engine.start({
  orderId: 'ORD-001',
  items: [{ productId: 'PROD-1', quantity: 2 }],
  paymentInfo: { method: 'credit_card', token: 'tok_xxx' },
});
```

## Benefits

| Benefit | Description |
|---------|-------------|
| Explicit States | All possible states are clearly defined |
| Controlled Transitions | Invalid state changes are prevented |
| Self-Documenting | State diagram documents behavior |
| Testable | Easy to test each state and transition |
| Maintainable | State logic is organized and isolated |

## When to Use

- Objects with distinct behavioral states
- Complex workflows with defined steps
- Game development (AI, game states)
- UI component states
- Order/transaction processing
- Protocol implementations
