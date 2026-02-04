---
name: command-pattern
description: Command pattern for encapsulating requests as objects
category: architecture/design-patterns/behavioral
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Command Pattern

## Overview

The Command pattern encapsulates a request as an object, letting you
parameterize clients with different requests, queue or log requests,
and support undoable operations.

## Basic Implementation

```typescript
// Command interface
interface Command {
  execute(): Promise<void>;
  undo?(): Promise<void>;
  getName(): string;
}

// Concrete Commands
class CreateUserCommand implements Command {
  private createdUserId?: string;

  constructor(
    private userService: UserService,
    private userData: CreateUserData
  ) {}

  async execute(): Promise<void> {
    const user = await this.userService.create(this.userData);
    this.createdUserId = user.id;
  }

  async undo(): Promise<void> {
    if (this.createdUserId) {
      await this.userService.delete(this.createdUserId);
    }
  }

  getName(): string {
    return `CreateUser: ${this.userData.email}`;
  }
}

class UpdateUserCommand implements Command {
  private previousData?: UserData;

  constructor(
    private userService: UserService,
    private userId: string,
    private updates: Partial<UserData>
  ) {}

  async execute(): Promise<void> {
    // Store previous state for undo
    const user = await this.userService.findById(this.userId);
    this.previousData = { ...user };

    await this.userService.update(this.userId, this.updates);
  }

  async undo(): Promise<void> {
    if (this.previousData) {
      await this.userService.update(this.userId, this.previousData);
    }
  }

  getName(): string {
    return `UpdateUser: ${this.userId}`;
  }
}

class DeleteUserCommand implements Command {
  private deletedUser?: UserData;

  constructor(
    private userService: UserService,
    private userId: string
  ) {}

  async execute(): Promise<void> {
    this.deletedUser = await this.userService.findById(this.userId);
    await this.userService.delete(this.userId);
  }

  async undo(): Promise<void> {
    if (this.deletedUser) {
      await this.userService.create(this.deletedUser);
    }
  }

  getName(): string {
    return `DeleteUser: ${this.userId}`;
  }
}

// Invoker
class CommandInvoker {
  private history: Command[] = [];
  private undoneCommands: Command[] = [];

  async execute(command: Command): Promise<void> {
    await command.execute();
    this.history.push(command);
    this.undoneCommands = []; // Clear redo stack
  }

  async undo(): Promise<void> {
    const command = this.history.pop();
    if (command?.undo) {
      await command.undo();
      this.undoneCommands.push(command);
    }
  }

  async redo(): Promise<void> {
    const command = this.undoneCommands.pop();
    if (command) {
      await command.execute();
      this.history.push(command);
    }
  }

  getHistory(): string[] {
    return this.history.map(cmd => cmd.getName());
  }
}

// Usage
const invoker = new CommandInvoker();

await invoker.execute(new CreateUserCommand(userService, { email: 'john@example.com' }));
await invoker.execute(new UpdateUserCommand(userService, 'user-1', { name: 'John Doe' }));

console.log(invoker.getHistory());
// ['CreateUser: john@example.com', 'UpdateUser: user-1']

await invoker.undo(); // Reverts UpdateUser
await invoker.undo(); // Reverts CreateUser (deletes user)
await invoker.redo(); // Re-creates user
```

## Command Queue

```typescript
interface QueuedCommand extends Command {
  id: string;
  priority: number;
  scheduledAt?: Date;
  maxRetries: number;
  retryCount: number;
}

class CommandQueue {
  private queue: QueuedCommand[] = [];
  private processing = false;

  async enqueue(command: Command, options: QueueOptions = {}): Promise<string> {
    const queuedCommand: QueuedCommand = {
      ...command,
      id: crypto.randomUUID(),
      priority: options.priority ?? 0,
      scheduledAt: options.scheduledAt,
      maxRetries: options.maxRetries ?? 3,
      retryCount: 0,
      execute: command.execute.bind(command),
      getName: command.getName.bind(command),
    };

    this.queue.push(queuedCommand);
    this.queue.sort((a, b) => b.priority - a.priority);

    if (!this.processing) {
      this.processQueue();
    }

    return queuedCommand.id;
  }

  private async processQueue(): Promise<void> {
    this.processing = true;

    while (this.queue.length > 0) {
      const command = this.queue.shift()!;

      // Check if scheduled for later
      if (command.scheduledAt && command.scheduledAt > new Date()) {
        this.queue.push(command);
        await this.sleep(1000);
        continue;
      }

      try {
        await command.execute();
        console.log(`Executed: ${command.getName()}`);
      } catch (error) {
        command.retryCount++;

        if (command.retryCount < command.maxRetries) {
          console.log(`Retry ${command.retryCount}/${command.maxRetries}: ${command.getName()}`);
          this.queue.push(command);
        } else {
          console.error(`Failed after ${command.maxRetries} retries: ${command.getName()}`);
        }
      }
    }

    this.processing = false;
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Usage
const queue = new CommandQueue();

await queue.enqueue(new SendEmailCommand(emailService, emailData), { priority: 10 });
await queue.enqueue(new ProcessPaymentCommand(paymentService, paymentData), { priority: 20 });
await queue.enqueue(new GenerateReportCommand(reportService), {
  priority: 5,
  scheduledAt: new Date(Date.now() + 60000), // 1 minute later
});
```

## Macro Commands (Composite)

```typescript
class MacroCommand implements Command {
  constructor(
    private commands: Command[],
    private name: string
  ) {}

  async execute(): Promise<void> {
    for (const command of this.commands) {
      await command.execute();
    }
  }

  async undo(): Promise<void> {
    // Undo in reverse order
    for (const command of [...this.commands].reverse()) {
      if (command.undo) {
        await command.undo();
      }
    }
  }

  getName(): string {
    return this.name;
  }
}

// Usage: Create order workflow
const createOrderWorkflow = new MacroCommand([
  new ValidateInventoryCommand(inventoryService, orderItems),
  new ReserveInventoryCommand(inventoryService, orderItems),
  new ProcessPaymentCommand(paymentService, paymentData),
  new CreateOrderRecordCommand(orderService, orderData),
  new SendConfirmationEmailCommand(emailService, customerEmail),
], 'CreateOrder');

const invoker = new CommandInvoker();
await invoker.execute(createOrderWorkflow);

// Undo entire workflow
await invoker.undo();
```

## Command with Result

```typescript
interface CommandWithResult<T> {
  execute(): Promise<T>;
  getName(): string;
}

class CreateOrderCommand implements CommandWithResult<Order> {
  constructor(
    private orderService: OrderService,
    private orderData: CreateOrderData
  ) {}

  async execute(): Promise<Order> {
    return this.orderService.create(this.orderData);
  }

  getName(): string {
    return `CreateOrder: ${this.orderData.customerId}`;
  }
}

class CommandHandler {
  async handle<T>(command: CommandWithResult<T>): Promise<T> {
    console.log(`Executing: ${command.getName()}`);
    const startTime = Date.now();

    try {
      const result = await command.execute();
      console.log(`Completed: ${command.getName()} (${Date.now() - startTime}ms)`);
      return result;
    } catch (error) {
      console.error(`Failed: ${command.getName()}`, error);
      throw error;
    }
  }
}

// Usage
const handler = new CommandHandler();
const order = await handler.handle(new CreateOrderCommand(orderService, orderData));
```

## CQRS Commands

```typescript
// Command base
abstract class BaseCommand {
  readonly commandId: string = crypto.randomUUID();
  readonly timestamp: Date = new Date();
  abstract readonly commandType: string;
}

// Specific commands
class PlaceOrderCommand extends BaseCommand {
  readonly commandType = 'PlaceOrder';

  constructor(
    public readonly customerId: string,
    public readonly items: OrderItem[],
    public readonly shippingAddress: Address
  ) {
    super();
  }
}

class CancelOrderCommand extends BaseCommand {
  readonly commandType = 'CancelOrder';

  constructor(
    public readonly orderId: string,
    public readonly reason: string
  ) {
    super();
  }
}

// Command handler interface
interface CommandHandler<T extends BaseCommand> {
  handle(command: T): Promise<void>;
}

// Concrete handlers
class PlaceOrderHandler implements CommandHandler<PlaceOrderCommand> {
  constructor(
    private orderRepository: OrderRepository,
    private inventoryService: InventoryService,
    private paymentService: PaymentService
  ) {}

  async handle(command: PlaceOrderCommand): Promise<void> {
    // Validate inventory
    await this.inventoryService.validateAvailability(command.items);

    // Create order
    const order = Order.create(
      command.customerId,
      command.items,
      command.shippingAddress
    );

    // Process payment
    await this.paymentService.processPayment(order);

    // Save order
    await this.orderRepository.save(order);
  }
}

class CancelOrderHandler implements CommandHandler<CancelOrderCommand> {
  constructor(
    private orderRepository: OrderRepository,
    private paymentService: PaymentService
  ) {}

  async handle(command: CancelOrderCommand): Promise<void> {
    const order = await this.orderRepository.findById(command.orderId);
    if (!order) {
      throw new OrderNotFoundError(command.orderId);
    }

    order.cancel(command.reason);

    await this.paymentService.refund(order.paymentId);
    await this.orderRepository.save(order);
  }
}

// Command bus
class CommandBus {
  private handlers = new Map<string, CommandHandler<any>>();

  register<T extends BaseCommand>(
    commandType: string,
    handler: CommandHandler<T>
  ): void {
    this.handlers.set(commandType, handler);
  }

  async dispatch<T extends BaseCommand>(command: T): Promise<void> {
    const handler = this.handlers.get(command.commandType);
    if (!handler) {
      throw new Error(`No handler for command: ${command.commandType}`);
    }
    await handler.handle(command);
  }
}

// Setup
const commandBus = new CommandBus();
commandBus.register('PlaceOrder', new PlaceOrderHandler(orderRepo, inventoryService, paymentService));
commandBus.register('CancelOrder', new CancelOrderHandler(orderRepo, paymentService));

// Usage
await commandBus.dispatch(new PlaceOrderCommand(customerId, items, address));
await commandBus.dispatch(new CancelOrderCommand(orderId, 'Customer requested'));
```

## Text Editor Example (Undo/Redo)

```typescript
interface TextCommand extends Command {
  execute(): void;
  undo(): void;
}

class InsertTextCommand implements TextCommand {
  constructor(
    private editor: TextEditor,
    private text: string,
    private position: number
  ) {}

  execute(): void {
    this.editor.insertAt(this.position, this.text);
  }

  undo(): void {
    this.editor.deleteRange(this.position, this.position + this.text.length);
  }

  getName(): string {
    return `Insert "${this.text.substring(0, 20)}..."`;
  }
}

class DeleteTextCommand implements TextCommand {
  private deletedText: string = '';

  constructor(
    private editor: TextEditor,
    private start: number,
    private end: number
  ) {}

  execute(): void {
    this.deletedText = this.editor.getRange(this.start, this.end);
    this.editor.deleteRange(this.start, this.end);
  }

  undo(): void {
    this.editor.insertAt(this.start, this.deletedText);
  }

  getName(): string {
    return `Delete "${this.deletedText.substring(0, 20)}..."`;
  }
}

class ReplaceTextCommand implements TextCommand {
  private originalText: string = '';

  constructor(
    private editor: TextEditor,
    private start: number,
    private end: number,
    private newText: string
  ) {}

  execute(): void {
    this.originalText = this.editor.getRange(this.start, this.end);
    this.editor.deleteRange(this.start, this.end);
    this.editor.insertAt(this.start, this.newText);
  }

  undo(): void {
    this.editor.deleteRange(this.start, this.start + this.newText.length);
    this.editor.insertAt(this.start, this.originalText);
  }

  getName(): string {
    return `Replace "${this.originalText.substring(0, 10)}..." with "${this.newText.substring(0, 10)}..."`;
  }
}
```

## Benefits

| Benefit | Description |
|---------|-------------|
| Decoupling | Sender and receiver are decoupled |
| Undo/Redo | Natural support for reversible operations |
| Queuing | Commands can be queued for later execution |
| Logging | Easy to log all commands |
| Transactions | Combine commands into macro operations |

## When to Use

- Need undo/redo functionality
- Queue operations for later
- Log operations for audit
- Parameterize objects with operations
- Implement transactional behavior
