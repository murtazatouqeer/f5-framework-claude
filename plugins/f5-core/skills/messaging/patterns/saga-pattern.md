---
name: saga-pattern
description: Managing distributed transactions across services
category: messaging/patterns
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Saga Pattern

## Overview

The Saga pattern manages distributed transactions across multiple services without using distributed locks. It breaks a transaction into a sequence of local transactions, each with a compensating action for rollback.

## Core Concepts

| Concept | Description |
|---------|-------------|
| **Saga** | Sequence of local transactions |
| **Step** | Single local transaction |
| **Compensation** | Undo action for a step |
| **Orchestrator** | Central coordinator (orchestration) |
| **Choreography** | Event-driven coordination |

## Saga Types

| Type | Coordination | Complexity | Use Case |
|------|--------------|------------|----------|
| **Orchestration** | Central coordinator | Lower | Complex workflows |
| **Choreography** | Event-driven | Higher | Simple workflows |

## Orchestration Saga

```typescript
// Saga step definition
interface SagaStep<TInput, TOutput> {
  name: string;
  execute: (input: TInput, context: SagaContext) => Promise<TOutput>;
  compensate: (input: TInput, context: SagaContext) => Promise<void>;
}

interface SagaContext {
  sagaId: string;
  data: Record<string, any>;
  completedSteps: string[];
}

class SagaOrchestrator<TInput> {
  private steps: SagaStep<any, any>[] = [];

  addStep<TStepInput, TStepOutput>(
    step: SagaStep<TStepInput, TStepOutput>
  ): this {
    this.steps.push(step);
    return this;
  }

  async execute(input: TInput): Promise<SagaContext> {
    const context: SagaContext = {
      sagaId: crypto.randomUUID(),
      data: { input },
      completedSteps: [],
    };

    try {
      for (const step of this.steps) {
        console.log(`Executing step: ${step.name}`);

        const stepInput = this.getStepInput(step.name, context);
        const result = await step.execute(stepInput, context);

        context.data[step.name] = result;
        context.completedSteps.push(step.name);
      }

      return context;
    } catch (error) {
      console.error(`Saga failed at step, starting compensation`, error);
      await this.compensate(context);
      throw error;
    }
  }

  private async compensate(context: SagaContext): Promise<void> {
    // Compensate in reverse order
    const stepsToCompensate = [...context.completedSteps].reverse();

    for (const stepName of stepsToCompensate) {
      const step = this.steps.find(s => s.name === stepName);

      if (step) {
        try {
          console.log(`Compensating step: ${stepName}`);
          const stepInput = this.getStepInput(stepName, context);
          await step.compensate(stepInput, context);
        } catch (error) {
          console.error(`Compensation failed for ${stepName}:`, error);
          // Log for manual intervention
        }
      }
    }
  }

  private getStepInput(stepName: string, context: SagaContext): any {
    // Custom logic to derive step input from context
    return context.data;
  }
}
```

### Order Saga Example

```typescript
// Create Order Saga
interface CreateOrderInput {
  customerId: string;
  items: Array<{ productId: string; quantity: number; price: number }>;
  paymentMethod: string;
}

const createOrderSaga = new SagaOrchestrator<CreateOrderInput>()
  // Step 1: Create order
  .addStep({
    name: 'createOrder',
    execute: async (input, context) => {
      const order = await orderService.create({
        customerId: input.input.customerId,
        items: input.input.items,
        status: 'pending',
      });
      return { orderId: order.id };
    },
    compensate: async (input, context) => {
      const { orderId } = context.data.createOrder;
      await orderService.cancel(orderId);
    },
  })

  // Step 2: Reserve inventory
  .addStep({
    name: 'reserveInventory',
    execute: async (input, context) => {
      const { orderId } = context.data.createOrder;
      const reservations = await inventoryService.reserve(
        orderId,
        input.input.items
      );
      return { reservations };
    },
    compensate: async (input, context) => {
      const { orderId } = context.data.createOrder;
      await inventoryService.releaseReservation(orderId);
    },
  })

  // Step 3: Process payment
  .addStep({
    name: 'processPayment',
    execute: async (input, context) => {
      const { orderId } = context.data.createOrder;
      const total = input.input.items.reduce(
        (sum, item) => sum + item.price * item.quantity,
        0
      );

      const payment = await paymentService.charge({
        orderId,
        customerId: input.input.customerId,
        amount: total,
        method: input.input.paymentMethod,
      });

      return { paymentId: payment.id };
    },
    compensate: async (input, context) => {
      const { paymentId } = context.data.processPayment;
      await paymentService.refund(paymentId);
    },
  })

  // Step 4: Confirm order
  .addStep({
    name: 'confirmOrder',
    execute: async (input, context) => {
      const { orderId } = context.data.createOrder;
      await orderService.confirm(orderId);
      return { confirmed: true };
    },
    compensate: async (input, context) => {
      // Order cancellation already handled in step 1 compensation
    },
  });

// Usage
try {
  const result = await createOrderSaga.execute({
    customerId: 'cust-123',
    items: [{ productId: 'prod-1', quantity: 2, price: 49.99 }],
    paymentMethod: 'credit_card',
  });

  console.log('Order created:', result.data.createOrder.orderId);
} catch (error) {
  console.error('Order creation failed:', error);
}
```

## Choreography Saga

```typescript
// Event-driven saga using events
interface SagaEvent {
  sagaId: string;
  eventType: string;
  data: any;
  timestamp: Date;
}

class OrderSagaChoreography {
  constructor(
    private readonly eventBus: EventBus,
    private readonly orderService: OrderService,
    private readonly inventoryService: InventoryService,
    private readonly paymentService: PaymentService
  ) {
    this.setupEventHandlers();
  }

  private setupEventHandlers(): void {
    // Order Service handlers
    this.eventBus.subscribe('order.created', async (event: SagaEvent) => {
      // Trigger inventory reservation
      await this.eventBus.publish({
        sagaId: event.sagaId,
        eventType: 'inventory.reserve.requested',
        data: event.data,
        timestamp: new Date(),
      });
    });

    // Inventory Service handlers
    this.eventBus.subscribe('inventory.reserve.requested', async (event: SagaEvent) => {
      try {
        await this.inventoryService.reserve(event.data.orderId, event.data.items);

        await this.eventBus.publish({
          sagaId: event.sagaId,
          eventType: 'inventory.reserved',
          data: event.data,
          timestamp: new Date(),
        });
      } catch (error) {
        await this.eventBus.publish({
          sagaId: event.sagaId,
          eventType: 'inventory.reserve.failed',
          data: { ...event.data, error: error.message },
          timestamp: new Date(),
        });
      }
    });

    this.eventBus.subscribe('inventory.reserved', async (event: SagaEvent) => {
      // Trigger payment processing
      await this.eventBus.publish({
        sagaId: event.sagaId,
        eventType: 'payment.process.requested',
        data: event.data,
        timestamp: new Date(),
      });
    });

    // Payment Service handlers
    this.eventBus.subscribe('payment.process.requested', async (event: SagaEvent) => {
      try {
        const payment = await this.paymentService.charge(event.data);

        await this.eventBus.publish({
          sagaId: event.sagaId,
          eventType: 'payment.processed',
          data: { ...event.data, paymentId: payment.id },
          timestamp: new Date(),
        });
      } catch (error) {
        await this.eventBus.publish({
          sagaId: event.sagaId,
          eventType: 'payment.failed',
          data: { ...event.data, error: error.message },
          timestamp: new Date(),
        });
      }
    });

    // Compensation handlers
    this.eventBus.subscribe('payment.failed', async (event: SagaEvent) => {
      // Release inventory
      await this.inventoryService.releaseReservation(event.data.orderId);

      await this.eventBus.publish({
        sagaId: event.sagaId,
        eventType: 'inventory.released',
        data: event.data,
        timestamp: new Date(),
      });
    });

    this.eventBus.subscribe('inventory.released', async (event: SagaEvent) => {
      // Cancel order
      await this.orderService.cancel(event.data.orderId);

      await this.eventBus.publish({
        sagaId: event.sagaId,
        eventType: 'order.cancelled',
        data: event.data,
        timestamp: new Date(),
      });
    });

    // Success handler
    this.eventBus.subscribe('payment.processed', async (event: SagaEvent) => {
      await this.orderService.confirm(event.data.orderId);

      await this.eventBus.publish({
        sagaId: event.sagaId,
        eventType: 'order.confirmed',
        data: event.data,
        timestamp: new Date(),
      });
    });
  }

  // Start saga
  async createOrder(input: CreateOrderInput): Promise<string> {
    const sagaId = crypto.randomUUID();

    const order = await this.orderService.create({
      ...input,
      status: 'pending',
    });

    await this.eventBus.publish({
      sagaId,
      eventType: 'order.created',
      data: { orderId: order.id, ...input },
      timestamp: new Date(),
    });

    return sagaId;
  }
}
```

## Saga State Machine

```typescript
type SagaStatus = 'pending' | 'running' | 'completed' | 'compensating' | 'failed';

interface SagaState {
  sagaId: string;
  status: SagaStatus;
  currentStep: number;
  steps: Array<{
    name: string;
    status: 'pending' | 'completed' | 'compensated' | 'failed';
    result?: any;
    error?: string;
  }>;
  createdAt: Date;
  updatedAt: Date;
}

class SagaStateMachine {
  constructor(private readonly store: SagaStore) {}

  async create(sagaId: string, stepNames: string[]): Promise<SagaState> {
    const state: SagaState = {
      sagaId,
      status: 'pending',
      currentStep: 0,
      steps: stepNames.map(name => ({
        name,
        status: 'pending',
      })),
      createdAt: new Date(),
      updatedAt: new Date(),
    };

    await this.store.save(state);
    return state;
  }

  async markStepCompleted(sagaId: string, stepIndex: number, result: any): Promise<SagaState> {
    const state = await this.store.get(sagaId);

    state.steps[stepIndex].status = 'completed';
    state.steps[stepIndex].result = result;
    state.currentStep = stepIndex + 1;
    state.updatedAt = new Date();

    if (state.currentStep >= state.steps.length) {
      state.status = 'completed';
    } else {
      state.status = 'running';
    }

    await this.store.save(state);
    return state;
  }

  async markStepFailed(sagaId: string, stepIndex: number, error: string): Promise<SagaState> {
    const state = await this.store.get(sagaId);

    state.steps[stepIndex].status = 'failed';
    state.steps[stepIndex].error = error;
    state.status = 'compensating';
    state.updatedAt = new Date();

    await this.store.save(state);
    return state;
  }

  async markStepCompensated(sagaId: string, stepIndex: number): Promise<SagaState> {
    const state = await this.store.get(sagaId);

    state.steps[stepIndex].status = 'compensated';
    state.currentStep = stepIndex - 1;
    state.updatedAt = new Date();

    if (state.currentStep < 0) {
      state.status = 'failed';
    }

    await this.store.save(state);
    return state;
  }

  async getState(sagaId: string): Promise<SagaState> {
    return this.store.get(sagaId);
  }
}
```

## Saga with Timeouts

```typescript
interface SagaStepConfig {
  timeout: number;
  retries: number;
  retryDelay: number;
}

class TimeoutSagaOrchestrator {
  private steps: Array<{
    step: SagaStep<any, any>;
    config: SagaStepConfig;
  }> = [];

  addStep(
    step: SagaStep<any, any>,
    config: Partial<SagaStepConfig> = {}
  ): this {
    this.steps.push({
      step,
      config: {
        timeout: config.timeout || 30000,
        retries: config.retries || 3,
        retryDelay: config.retryDelay || 1000,
      },
    });
    return this;
  }

  async executeWithTimeout<T>(
    fn: () => Promise<T>,
    timeout: number
  ): Promise<T> {
    return Promise.race([
      fn(),
      new Promise<never>((_, reject) =>
        setTimeout(() => reject(new Error('Step timeout')), timeout)
      ),
    ]);
  }

  async executeWithRetry<T>(
    fn: () => Promise<T>,
    config: SagaStepConfig
  ): Promise<T> {
    let lastError: Error | undefined;

    for (let attempt = 0; attempt <= config.retries; attempt++) {
      try {
        return await this.executeWithTimeout(fn, config.timeout);
      } catch (error) {
        lastError = error as Error;

        if (attempt < config.retries) {
          await new Promise(r => setTimeout(r, config.retryDelay * (attempt + 1)));
        }
      }
    }

    throw lastError;
  }

  async execute(input: any): Promise<SagaContext> {
    const context: SagaContext = {
      sagaId: crypto.randomUUID(),
      data: { input },
      completedSteps: [],
    };

    try {
      for (const { step, config } of this.steps) {
        const stepInput = context.data;

        const result = await this.executeWithRetry(
          () => step.execute(stepInput, context),
          config
        );

        context.data[step.name] = result;
        context.completedSteps.push(step.name);
      }

      return context;
    } catch (error) {
      await this.compensate(context);
      throw error;
    }
  }

  private async compensate(context: SagaContext): Promise<void> {
    const stepsToCompensate = [...context.completedSteps].reverse();

    for (const stepName of stepsToCompensate) {
      const { step, config } = this.steps.find(s => s.step.name === stepName)!;

      try {
        await this.executeWithRetry(
          () => step.compensate(context.data, context),
          config
        );
      } catch (error) {
        console.error(`Compensation failed for ${stepName}:`, error);
      }
    }
  }
}
```

## Comparison

| Aspect | Orchestration | Choreography |
|--------|--------------|--------------|
| Coordination | Central | Decentralized |
| Coupling | Services to orchestrator | Services to events |
| Complexity | Lower | Higher |
| Debugging | Easier | Harder |
| Single point of failure | Orchestrator | None |
| Flexibility | Lower | Higher |

## Best Practices

| Practice | Implementation |
|----------|----------------|
| **Idempotent operations** | Handle retries safely |
| **Persist saga state** | Enable recovery after failures |
| **Set timeouts** | Prevent stuck sagas |
| **Log all steps** | Enable debugging and audit |
| **Handle partial failures** | Compensations may also fail |
| **Design reversible operations** | Not all actions can be undone |
