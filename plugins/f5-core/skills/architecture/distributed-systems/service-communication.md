---
name: service-communication
description: Patterns for inter-service communication in distributed systems
category: architecture/distributed-systems
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Service Communication Patterns

## Overview

Service communication defines how services interact in distributed systems.
Choosing the right communication pattern impacts reliability, performance,
and system complexity.

## Communication Styles

### Synchronous vs Asynchronous

```
┌─────────────────────────────────────────────────────────────┐
│                    SYNCHRONOUS                               │
│  ┌────────┐    Request    ┌────────┐                        │
│  │Service │ ────────────► │Service │                        │
│  │   A    │ ◄──────────── │   B    │                        │
│  └────────┘    Response   └────────┘                        │
│         Caller blocks until response                        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   ASYNCHRONOUS                               │
│  ┌────────┐    Message    ┌────────┐    Message  ┌────────┐ │
│  │Service │ ────────────► │ Queue  │ ──────────► │Service │ │
│  │   A    │               │        │             │   B    │ │
│  └────────┘               └────────┘             └────────┘ │
│         Caller continues immediately                        │
└─────────────────────────────────────────────────────────────┘
```

## REST API Communication

```typescript
// REST Client with retry and circuit breaker
interface HttpClientConfig {
  baseUrl: string;
  timeout: number;
  retries: number;
  circuitBreaker: CircuitBreakerConfig;
}

class ServiceClient {
  private circuitBreaker: CircuitBreaker;

  constructor(
    private config: HttpClientConfig,
    private httpClient: HttpClient
  ) {
    this.circuitBreaker = new CircuitBreaker(config.circuitBreaker);
  }

  async get<T>(path: string): Promise<T> {
    return this.circuitBreaker.execute(async () => {
      return this.withRetry(async () => {
        const response = await this.httpClient.get(`${this.config.baseUrl}${path}`, {
          timeout: this.config.timeout,
        });
        return response.data;
      });
    });
  }

  async post<T, R>(path: string, data: T): Promise<R> {
    return this.circuitBreaker.execute(async () => {
      return this.withRetry(async () => {
        const response = await this.httpClient.post(
          `${this.config.baseUrl}${path}`,
          data,
          { timeout: this.config.timeout }
        );
        return response.data;
      });
    });
  }

  private async withRetry<T>(fn: () => Promise<T>): Promise<T> {
    let lastError: Error;

    for (let attempt = 0; attempt < this.config.retries; attempt++) {
      try {
        return await fn();
      } catch (error) {
        lastError = error;
        if (!this.isRetryable(error)) throw error;
        await this.delay(this.getBackoff(attempt));
      }
    }

    throw lastError!;
  }

  private isRetryable(error: any): boolean {
    const retryableCodes = [408, 429, 500, 502, 503, 504];
    return retryableCodes.includes(error.response?.status);
  }

  private getBackoff(attempt: number): number {
    return Math.min(1000 * Math.pow(2, attempt), 30000);
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Usage
const userService = new ServiceClient({
  baseUrl: 'http://user-service:3000',
  timeout: 5000,
  retries: 3,
  circuitBreaker: { threshold: 5, timeout: 30000 },
}, httpClient);

const user = await userService.get<User>(`/users/${userId}`);
```

## gRPC Communication

```typescript
// Proto definition
/*
syntax = "proto3";

service UserService {
  rpc GetUser(GetUserRequest) returns (User);
  rpc CreateUser(CreateUserRequest) returns (User);
  rpc ListUsers(ListUsersRequest) returns (stream User);
  rpc UpdateUsers(stream UpdateUserRequest) returns (UpdateResult);
}

message User {
  string id = 1;
  string email = 2;
  string name = 3;
}
*/

// gRPC Server
import { Server, ServerCredentials } from '@grpc/grpc-js';
import { UserServiceService } from './generated/user_grpc_pb';

class UserServiceImpl implements UserServiceHandlers {
  async getUser(
    call: ServerUnaryCall<GetUserRequest, User>,
    callback: sendUnaryData<User>
  ): Promise<void> {
    try {
      const userId = call.request.getId();
      const user = await this.userRepository.findById(userId);

      if (!user) {
        callback({
          code: grpc.status.NOT_FOUND,
          message: `User ${userId} not found`,
        });
        return;
      }

      const response = new User();
      response.setId(user.id);
      response.setEmail(user.email);
      response.setName(user.name);

      callback(null, response);
    } catch (error) {
      callback({
        code: grpc.status.INTERNAL,
        message: error.message,
      });
    }
  }

  // Streaming response
  listUsers(call: ServerWritableStream<ListUsersRequest, User>): void {
    const criteria = call.request.getCriteria();

    this.userRepository.findByCriteria(criteria, (user) => {
      const response = new User();
      response.setId(user.id);
      response.setEmail(user.email);
      call.write(response);
    }).then(() => {
      call.end();
    });
  }
}

const server = new Server();
server.addService(UserServiceService, new UserServiceImpl());
server.bindAsync('0.0.0.0:50051', ServerCredentials.createInsecure(), () => {
  server.start();
});

// gRPC Client
import { credentials } from '@grpc/grpc-js';
import { UserServiceClient } from './generated/user_grpc_pb';

class GrpcUserClient {
  private client: UserServiceClient;

  constructor(address: string) {
    this.client = new UserServiceClient(address, credentials.createInsecure());
  }

  async getUser(userId: string): Promise<User> {
    return new Promise((resolve, reject) => {
      const request = new GetUserRequest();
      request.setId(userId);

      this.client.getUser(request, (error, response) => {
        if (error) reject(error);
        else resolve(response);
      });
    });
  }

  // Stream handling
  async *listUsers(criteria: string): AsyncGenerator<User> {
    const request = new ListUsersRequest();
    request.setCriteria(criteria);

    const stream = this.client.listUsers(request);

    for await (const user of stream) {
      yield user;
    }
  }
}
```

## Message Queue Communication

```typescript
// Message broker abstraction
interface MessageBroker {
  publish(topic: string, message: Message): Promise<void>;
  subscribe(topic: string, handler: MessageHandler): Promise<void>;
  unsubscribe(topic: string): Promise<void>;
}

interface Message {
  id: string;
  type: string;
  payload: any;
  metadata: MessageMetadata;
}

interface MessageMetadata {
  correlationId: string;
  timestamp: Date;
  source: string;
  version: string;
}

// RabbitMQ implementation
class RabbitMQBroker implements MessageBroker {
  private connection: Connection;
  private channel: Channel;

  async connect(): Promise<void> {
    this.connection = await amqp.connect(this.config.url);
    this.channel = await this.connection.createChannel();
  }

  async publish(topic: string, message: Message): Promise<void> {
    await this.channel.assertExchange(topic, 'topic', { durable: true });

    this.channel.publish(
      topic,
      message.type,
      Buffer.from(JSON.stringify(message)),
      {
        persistent: true,
        messageId: message.id,
        correlationId: message.metadata.correlationId,
        timestamp: message.metadata.timestamp.getTime(),
        headers: {
          source: message.metadata.source,
          version: message.metadata.version,
        },
      }
    );
  }

  async subscribe(topic: string, handler: MessageHandler): Promise<void> {
    await this.channel.assertExchange(topic, 'topic', { durable: true });

    const queue = await this.channel.assertQueue('', { exclusive: true });
    await this.channel.bindQueue(queue.queue, topic, '#');

    this.channel.consume(queue.queue, async (msg) => {
      if (!msg) return;

      try {
        const message = JSON.parse(msg.content.toString()) as Message;
        await handler(message);
        this.channel.ack(msg);
      } catch (error) {
        // Dead letter queue for failed messages
        this.channel.nack(msg, false, false);
      }
    });
  }
}

// Kafka implementation
class KafkaBroker implements MessageBroker {
  private producer: Producer;
  private consumer: Consumer;

  async publish(topic: string, message: Message): Promise<void> {
    await this.producer.send({
      topic,
      messages: [{
        key: message.metadata.correlationId,
        value: JSON.stringify(message),
        headers: {
          'message-type': message.type,
          'source': message.metadata.source,
          'version': message.metadata.version,
        },
      }],
    });
  }

  async subscribe(topic: string, handler: MessageHandler): Promise<void> {
    await this.consumer.subscribe({ topic, fromBeginning: false });

    await this.consumer.run({
      eachMessage: async ({ message }) => {
        const parsed = JSON.parse(message.value!.toString()) as Message;
        await handler(parsed);
      },
    });
  }
}

// Usage
const broker = new RabbitMQBroker(config);
await broker.connect();

// Publisher
await broker.publish('orders', {
  id: crypto.randomUUID(),
  type: 'order.created',
  payload: { orderId: '123', customerId: '456', total: 99.99 },
  metadata: {
    correlationId: crypto.randomUUID(),
    timestamp: new Date(),
    source: 'order-service',
    version: '1.0',
  },
});

// Subscriber
await broker.subscribe('orders', async (message) => {
  if (message.type === 'order.created') {
    await inventoryService.reserveItems(message.payload);
  }
});
```

## Event-Driven Communication

```typescript
// Domain events
abstract class DomainEvent {
  readonly eventId: string = crypto.randomUUID();
  readonly occurredOn: Date = new Date();
  abstract readonly eventType: string;
}

class OrderPlacedEvent extends DomainEvent {
  readonly eventType = 'order.placed';

  constructor(
    public readonly orderId: string,
    public readonly customerId: string,
    public readonly items: OrderItem[],
    public readonly total: number
  ) {
    super();
  }
}

// Event bus
interface EventBus {
  publish(event: DomainEvent): Promise<void>;
  subscribe<T extends DomainEvent>(
    eventType: string,
    handler: (event: T) => Promise<void>
  ): void;
}

class DistributedEventBus implements EventBus {
  constructor(private broker: MessageBroker) {}

  async publish(event: DomainEvent): Promise<void> {
    await this.broker.publish('domain-events', {
      id: event.eventId,
      type: event.eventType,
      payload: event,
      metadata: {
        correlationId: event.eventId,
        timestamp: event.occurredOn,
        source: process.env.SERVICE_NAME!,
        version: '1.0',
      },
    });
  }

  subscribe<T extends DomainEvent>(
    eventType: string,
    handler: (event: T) => Promise<void>
  ): void {
    this.broker.subscribe('domain-events', async (message) => {
      if (message.type === eventType) {
        await handler(message.payload as T);
      }
    });
  }
}

// Event handlers in different services
// Inventory Service
eventBus.subscribe<OrderPlacedEvent>('order.placed', async (event) => {
  await inventoryService.reserveItems(event.items);
});

// Notification Service
eventBus.subscribe<OrderPlacedEvent>('order.placed', async (event) => {
  await notificationService.sendOrderConfirmation(event.customerId, event.orderId);
});

// Analytics Service
eventBus.subscribe<OrderPlacedEvent>('order.placed', async (event) => {
  await analyticsService.trackOrder(event);
});
```

## Service Discovery

```typescript
// Service registry interface
interface ServiceRegistry {
  register(service: ServiceInstance): Promise<void>;
  deregister(serviceId: string): Promise<void>;
  discover(serviceName: string): Promise<ServiceInstance[]>;
  watch(serviceName: string, callback: (instances: ServiceInstance[]) => void): void;
}

interface ServiceInstance {
  id: string;
  name: string;
  host: string;
  port: number;
  metadata: Record<string, string>;
  healthCheckUrl: string;
}

// Consul implementation
class ConsulServiceRegistry implements ServiceRegistry {
  constructor(private consul: Consul) {}

  async register(service: ServiceInstance): Promise<void> {
    await this.consul.agent.service.register({
      id: service.id,
      name: service.name,
      address: service.host,
      port: service.port,
      meta: service.metadata,
      check: {
        http: service.healthCheckUrl,
        interval: '10s',
        timeout: '5s',
      },
    });
  }

  async discover(serviceName: string): Promise<ServiceInstance[]> {
    const services = await this.consul.health.service({
      service: serviceName,
      passing: true,
    });

    return services.map(entry => ({
      id: entry.Service.ID,
      name: entry.Service.Service,
      host: entry.Service.Address,
      port: entry.Service.Port,
      metadata: entry.Service.Meta,
      healthCheckUrl: `http://${entry.Service.Address}:${entry.Service.Port}/health`,
    }));
  }

  watch(serviceName: string, callback: (instances: ServiceInstance[]) => void): void {
    const watch = this.consul.watch({
      method: this.consul.health.service,
      options: { service: serviceName, passing: true },
    });

    watch.on('change', (data) => {
      const instances = data.map(this.mapToServiceInstance);
      callback(instances);
    });
  }
}

// Load balancer with service discovery
class LoadBalancedClient {
  private instances: ServiceInstance[] = [];
  private currentIndex = 0;

  constructor(
    private registry: ServiceRegistry,
    private serviceName: string
  ) {
    this.registry.watch(serviceName, (instances) => {
      this.instances = instances;
    });
  }

  async initialize(): Promise<void> {
    this.instances = await this.registry.discover(this.serviceName);
  }

  getNextInstance(): ServiceInstance {
    if (this.instances.length === 0) {
      throw new Error(`No instances available for ${this.serviceName}`);
    }

    // Round-robin
    const instance = this.instances[this.currentIndex];
    this.currentIndex = (this.currentIndex + 1) % this.instances.length;
    return instance;
  }

  async call<T>(path: string): Promise<T> {
    const instance = this.getNextInstance();
    const url = `http://${instance.host}:${instance.port}${path}`;
    return httpClient.get(url);
  }
}
```

## API Gateway Pattern

```typescript
// API Gateway
class ApiGateway {
  private routes: Map<string, RouteConfig> = new Map();
  private rateLimiter: RateLimiter;
  private authService: AuthService;

  constructor(
    private serviceRegistry: ServiceRegistry,
    private circuitBreakers: Map<string, CircuitBreaker>
  ) {
    this.rateLimiter = new RateLimiter();
    this.authService = new AuthService();
  }

  registerRoute(config: RouteConfig): void {
    this.routes.set(config.path, config);
  }

  async handleRequest(req: Request): Promise<Response> {
    // Rate limiting
    if (!this.rateLimiter.allow(req.ip)) {
      return new Response(429, { error: 'Too many requests' });
    }

    const route = this.findRoute(req.path);
    if (!route) {
      return new Response(404, { error: 'Not found' });
    }

    // Authentication
    if (route.requiresAuth) {
      const authResult = await this.authService.validate(req.headers.authorization);
      if (!authResult.valid) {
        return new Response(401, { error: 'Unauthorized' });
      }
      req.user = authResult.user;
    }

    // Route to service
    try {
      const circuitBreaker = this.circuitBreakers.get(route.service);
      const instances = await this.serviceRegistry.discover(route.service);

      return await circuitBreaker!.execute(async () => {
        const instance = this.selectInstance(instances);
        return this.forwardRequest(instance, req, route);
      });
    } catch (error) {
      if (error instanceof CircuitOpenError) {
        return new Response(503, { error: 'Service temporarily unavailable' });
      }
      return new Response(500, { error: 'Internal server error' });
    }
  }

  private async forwardRequest(
    instance: ServiceInstance,
    req: Request,
    route: RouteConfig
  ): Promise<Response> {
    const targetUrl = `http://${instance.host}:${instance.port}${route.targetPath}`;

    const response = await httpClient.request({
      method: req.method,
      url: targetUrl,
      headers: this.transformHeaders(req.headers, req.user),
      data: req.body,
      timeout: route.timeout,
    });

    return new Response(response.status, response.data);
  }

  private transformHeaders(
    headers: Record<string, string>,
    user?: User
  ): Record<string, string> {
    const transformed = { ...headers };

    // Add internal headers
    transformed['X-Request-ID'] = crypto.randomUUID();
    transformed['X-Forwarded-For'] = headers['x-real-ip'] || '';

    if (user) {
      transformed['X-User-ID'] = user.id;
      transformed['X-User-Roles'] = user.roles.join(',');
    }

    // Remove sensitive headers
    delete transformed['authorization'];

    return transformed;
  }
}

// Route configuration
interface RouteConfig {
  path: string;
  service: string;
  targetPath: string;
  methods: string[];
  requiresAuth: boolean;
  timeout: number;
  rateLimit?: RateLimitConfig;
}

// Usage
const gateway = new ApiGateway(serviceRegistry, circuitBreakers);

gateway.registerRoute({
  path: '/api/users/*',
  service: 'user-service',
  targetPath: '/users/*',
  methods: ['GET', 'POST', 'PUT', 'DELETE'],
  requiresAuth: true,
  timeout: 5000,
});

gateway.registerRoute({
  path: '/api/orders/*',
  service: 'order-service',
  targetPath: '/orders/*',
  methods: ['GET', 'POST'],
  requiresAuth: true,
  timeout: 10000,
});
```

## Communication Pattern Comparison

| Pattern | Latency | Coupling | Reliability | Complexity |
|---------|---------|----------|-------------|------------|
| REST | Low | High | Medium | Low |
| gRPC | Very Low | High | Medium | Medium |
| Message Queue | Medium | Low | High | Medium |
| Event-Driven | Medium | Very Low | High | High |

## When to Use

| Pattern | Use Case |
|---------|----------|
| REST | Public APIs, CRUD operations |
| gRPC | Internal services, streaming |
| Message Queue | Task processing, decoupling |
| Event-Driven | Complex workflows, eventual consistency |
