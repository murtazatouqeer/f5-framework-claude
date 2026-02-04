---
name: documentation
description: Best practices for documenting software architecture
category: architecture/decision-making
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Architecture Documentation

## Overview

Good architecture documentation helps teams understand, maintain, and evolve
systems. It should be accurate, accessible, and maintainable—avoiding both
over-documentation and under-documentation.

## Documentation Levels

```
┌─────────────────────────────────────────────────────────────┐
│                 DOCUMENTATION PYRAMID                        │
│                                                             │
│                      ┌─────────┐                            │
│                      │  Code   │  ← Self-documenting code   │
│                      └────┬────┘                            │
│                     ┌─────┴─────┐                           │
│                     │ API Docs  │  ← OpenAPI, JSDoc         │
│                     └─────┬─────┘                           │
│                   ┌───────┴───────┐                         │
│                   │ Architecture  │  ← C4, ADRs, diagrams   │
│                   └───────┬───────┘                         │
│                 ┌─────────┴─────────┐                       │
│                 │    Runbooks      │  ← Operations guides    │
│                 └─────────┬─────────┘                       │
│               ┌───────────┴───────────┐                     │
│               │    Onboarding        │  ← Getting started    │
│               └───────────────────────┘                     │
│                                                             │
│  More specific ▲                         ▼ More general     │
└─────────────────────────────────────────────────────────────┘
```

## C4 Model

### Level 1: System Context

```typescript
// Documents the system and its relationships with users and other systems

interface SystemContext {
  system: {
    name: string;
    description: string;
    technology?: string;
  };
  people: Person[];
  externalSystems: ExternalSystem[];
  relationships: Relationship[];
}

// Example: E-commerce Platform Context
const ecommerceContext: SystemContext = {
  system: {
    name: 'E-Commerce Platform',
    description: 'Allows customers to browse products and place orders',
  },
  people: [
    { name: 'Customer', description: 'Browses and purchases products' },
    { name: 'Admin', description: 'Manages products and orders' },
  ],
  externalSystems: [
    { name: 'Payment Gateway', description: 'Processes credit card payments' },
    { name: 'Shipping Provider', description: 'Handles order fulfillment' },
    { name: 'Email Service', description: 'Sends transactional emails' },
  ],
  relationships: [
    { from: 'Customer', to: 'E-Commerce Platform', description: 'Uses' },
    { from: 'E-Commerce Platform', to: 'Payment Gateway', description: 'Processes payments via' },
  ],
};
```

```
┌─────────────────────────────────────────────────────────────┐
│                    SYSTEM CONTEXT                            │
│                                                             │
│    ┌──────────┐                      ┌──────────────┐       │
│    │ Customer │──────Uses───────────►│  E-Commerce  │       │
│    └──────────┘                      │   Platform   │       │
│                                      └──────┬───────┘       │
│    ┌──────────┐                             │               │
│    │  Admin   │──────Manages────────────────┤               │
│    └──────────┘                             │               │
│                                             │               │
│            ┌────────────────────────────────┼───────┐       │
│            │                                │       │       │
│            ▼                                ▼       ▼       │
│    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│    │   Payment    │  │   Shipping   │  │    Email     │    │
│    │   Gateway    │  │   Provider   │  │   Service    │    │
│    └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Level 2: Container Diagram

```typescript
// Shows the high-level technical building blocks

interface ContainerDiagram {
  containers: Container[];
  relationships: ContainerRelationship[];
}

interface Container {
  name: string;
  type: 'web-app' | 'mobile-app' | 'api' | 'database' | 'queue' | 'file-store';
  technology: string;
  description: string;
}

// Example
const ecommerceContainers: ContainerDiagram = {
  containers: [
    {
      name: 'Web Application',
      type: 'web-app',
      technology: 'React, TypeScript',
      description: 'Customer-facing storefront',
    },
    {
      name: 'API Gateway',
      type: 'api',
      technology: 'Kong',
      description: 'Routes and rate-limits API requests',
    },
    {
      name: 'Order Service',
      type: 'api',
      technology: 'Node.js, NestJS',
      description: 'Handles order processing',
    },
    {
      name: 'Order Database',
      type: 'database',
      technology: 'PostgreSQL',
      description: 'Stores order data',
    },
    {
      name: 'Message Queue',
      type: 'queue',
      technology: 'RabbitMQ',
      description: 'Async communication between services',
    },
  ],
  relationships: [
    { from: 'Web Application', to: 'API Gateway', protocol: 'HTTPS', description: 'API calls' },
    { from: 'API Gateway', to: 'Order Service', protocol: 'HTTP', description: 'Routes requests' },
    { from: 'Order Service', to: 'Order Database', protocol: 'TCP', description: 'Reads/writes data' },
    { from: 'Order Service', to: 'Message Queue', protocol: 'AMQP', description: 'Publishes events' },
  ],
};
```

### Level 3: Component Diagram

```typescript
// Shows the internal structure of a container

interface ComponentDiagram {
  container: string;
  components: Component[];
  relationships: ComponentRelationship[];
}

interface Component {
  name: string;
  responsibility: string;
  technology?: string;
}

// Example: Order Service Components
const orderServiceComponents: ComponentDiagram = {
  container: 'Order Service',
  components: [
    { name: 'OrderController', responsibility: 'Handles HTTP requests', technology: 'NestJS Controller' },
    { name: 'OrderService', responsibility: 'Business logic orchestration', technology: 'NestJS Service' },
    { name: 'OrderRepository', responsibility: 'Data access abstraction', technology: 'TypeORM Repository' },
    { name: 'PaymentClient', responsibility: 'Payment gateway integration', technology: 'HTTP Client' },
    { name: 'EventPublisher', responsibility: 'Publishes domain events', technology: 'RabbitMQ Client' },
  ],
  relationships: [
    { from: 'OrderController', to: 'OrderService', description: 'Uses' },
    { from: 'OrderService', to: 'OrderRepository', description: 'Persists via' },
    { from: 'OrderService', to: 'PaymentClient', description: 'Processes payments via' },
    { from: 'OrderService', to: 'EventPublisher', description: 'Publishes events via' },
  ],
};
```

### Level 4: Code

```typescript
// Use code comments and self-documenting code at this level

/**
 * OrderService handles order lifecycle operations.
 *
 * Responsibilities:
 * - Validate order data
 * - Process payments via PaymentClient
 * - Persist orders via OrderRepository
 * - Publish events for downstream systems
 *
 * @example
 * const order = await orderService.placeOrder({
 *   customerId: 'cust-123',
 *   items: [{ productId: 'prod-1', quantity: 2 }],
 * });
 */
@Injectable()
export class OrderService {
  constructor(
    private readonly orderRepository: OrderRepository,
    private readonly paymentClient: PaymentClient,
    private readonly eventPublisher: EventPublisher,
  ) {}

  /**
   * Places a new order.
   *
   * Flow:
   * 1. Validate order data
   * 2. Calculate totals
   * 3. Process payment
   * 4. Save order
   * 5. Publish OrderPlaced event
   *
   * @throws ValidationError if order data is invalid
   * @throws PaymentError if payment processing fails
   */
  async placeOrder(data: CreateOrderDto): Promise<Order> {
    // Implementation
  }
}
```

## API Documentation

### OpenAPI/Swagger

```yaml
openapi: 3.0.3
info:
  title: Order Service API
  version: 1.0.0
  description: |
    API for managing orders in the e-commerce platform.

    ## Authentication
    All endpoints require Bearer token authentication.

    ## Rate Limiting
    - 100 requests per minute for standard users
    - 1000 requests per minute for premium users

paths:
  /orders:
    post:
      summary: Create a new order
      operationId: createOrder
      tags:
        - Orders
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateOrderRequest'
            example:
              customerId: "cust-123"
              items:
                - productId: "prod-456"
                  quantity: 2
              shippingAddress:
                street: "123 Main St"
                city: "Tokyo"
                postalCode: "100-0001"
      responses:
        '201':
          description: Order created successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Order'
        '400':
          description: Invalid request data
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '402':
          description: Payment failed
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaymentError'

components:
  schemas:
    CreateOrderRequest:
      type: object
      required:
        - customerId
        - items
      properties:
        customerId:
          type: string
          description: Customer identifier
        items:
          type: array
          items:
            $ref: '#/components/schemas/OrderItem'
          minItems: 1
        shippingAddress:
          $ref: '#/components/schemas/Address'

    Order:
      type: object
      properties:
        id:
          type: string
          format: uuid
        status:
          type: string
          enum: [pending, confirmed, shipped, delivered, cancelled]
        total:
          type: number
          format: decimal
        createdAt:
          type: string
          format: date-time
```

## Runbooks

### Template

```markdown
# Runbook: {Service/Process Name}

## Overview
Brief description of the service and its role in the system.

## Quick Reference

| Item | Value |
|------|-------|
| Service URL | https://order-service.internal |
| Health Check | GET /health |
| Logs | Datadog: `service:order-service` |
| Dashboards | [Grafana](link) |
| On-Call | #platform-oncall |

## Common Operations

### Restart Service
```bash
kubectl rollout restart deployment/order-service -n production
```

### Scale Up
```bash
kubectl scale deployment/order-service --replicas=10 -n production
```

### Check Logs
```bash
kubectl logs -l app=order-service -n production --tail=100
```

## Alerts

### High Error Rate
**Trigger**: Error rate > 1% for 5 minutes
**Impact**: Customer orders may be failing
**Steps**:
1. Check recent deployments: `kubectl rollout history deployment/order-service`
2. Check downstream services: Payment, Inventory
3. Check database connectivity
4. If recent deploy, rollback: `kubectl rollout undo deployment/order-service`

### High Latency
**Trigger**: P99 latency > 2s for 5 minutes
**Impact**: Poor customer experience
**Steps**:
1. Check database slow queries
2. Check external service latency
3. Consider scaling up pods

## Disaster Recovery

### Database Restore
```bash
# List available backups
aws s3 ls s3://backups/order-db/

# Restore from backup
pg_restore -h $DB_HOST -d orders backup.dump
```

## Contacts
- Service Owner: @order-team
- Database: @platform-db
- Escalation: @engineering-manager
```

## README Templates

### Repository README

```markdown
# Order Service

Microservice responsible for order management in the e-commerce platform.

## Quick Start

```bash
# Prerequisites
- Node.js 20+
- Docker
- PostgreSQL 15+

# Setup
npm install
cp .env.example .env
npm run db:migrate

# Run
npm run dev

# Test
npm test
```

## Architecture

```
src/
├── controllers/     # HTTP handlers
├── services/        # Business logic
├── repositories/    # Data access
├── domain/          # Domain models
├── events/          # Event definitions
└── infrastructure/  # External integrations
```

## API Documentation

- [OpenAPI Spec](./docs/openapi.yaml)
- [Swagger UI](http://localhost:3000/docs) (when running locally)

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | - |
| `RABBITMQ_URL` | RabbitMQ connection string | - |
| `PAYMENT_SERVICE_URL` | Payment service endpoint | - |

## Development

### Running Tests
```bash
npm test              # Unit tests
npm run test:e2e      # End-to-end tests
npm run test:coverage # With coverage
```

### Database Migrations
```bash
npm run db:migrate     # Run migrations
npm run db:migrate:new # Create new migration
npm run db:rollback    # Rollback last migration
```

## Deployment

Deployed via GitHub Actions to Kubernetes.
- `main` → Production
- `develop` → Staging

## Related

- [Architecture Decision Records](./docs/adr/)
- [Runbook](./docs/runbook.md)
- [API Documentation](./docs/api.md)
```

## Documentation Best Practices

### Keep Documentation Close to Code

```
project/
├── src/
│   ├── orders/
│   │   ├── README.md           # Module-specific docs
│   │   ├── order.service.ts
│   │   └── order.controller.ts
├── docs/
│   ├── architecture/
│   │   ├── c4-diagrams/
│   │   └── adr/
│   ├── api/
│   │   └── openapi.yaml
│   └── runbooks/
├── README.md                    # Project overview
└── CONTRIBUTING.md              # How to contribute
```

### Documentation as Code

```typescript
// Use tools that generate docs from code

// TypeDoc for TypeScript
/**
 * Calculates the total price of an order.
 *
 * @param items - Array of order items
 * @param discount - Optional discount percentage (0-100)
 * @returns The calculated total price
 *
 * @example
 * ```ts
 * const total = calculateTotal([
 *   { price: 10, quantity: 2 },
 *   { price: 5, quantity: 1 }
 * ], 10);
 * // Returns 22.50 (10% discount applied)
 * ```
 */
function calculateTotal(items: OrderItem[], discount?: number): number {
  const subtotal = items.reduce((sum, item) => sum + item.price * item.quantity, 0);
  return discount ? subtotal * (1 - discount / 100) : subtotal;
}
```

### Living Documentation

```typescript
// Generate documentation from tests (BDD style)

describe('Order Service', () => {
  describe('placeOrder', () => {
    it('should create order with valid items', async () => {
      // Given
      const items = [{ productId: 'prod-1', quantity: 2 }];

      // When
      const order = await orderService.placeOrder({ customerId: 'cust-1', items });

      // Then
      expect(order.status).toBe('pending');
      expect(order.items).toHaveLength(1);
    });

    it('should reject order with empty items', async () => {
      // Given
      const items: OrderItem[] = [];

      // When/Then
      await expect(
        orderService.placeOrder({ customerId: 'cust-1', items })
      ).rejects.toThrow('Order must have at least one item');
    });

    it('should process payment before confirming order', async () => {
      // Given
      const order = await createPendingOrder();

      // When
      await orderService.confirmOrder(order.id);

      // Then
      expect(paymentClient.charge).toHaveBeenCalledWith(order.total);
      expect(order.status).toBe('confirmed');
    });
  });
});
```

## Benefits

| Benefit | Description |
|---------|-------------|
| Onboarding | New team members ramp up faster |
| Maintenance | Understand system before changing it |
| Communication | Stakeholders understand architecture |
| Decision Support | Context for future decisions |
| Compliance | Audit requirements met |

## When to Document

- New systems or significant changes
- Decisions with long-term impact
- Non-obvious design choices
- Integration points
- Operational procedures
- Security considerations
