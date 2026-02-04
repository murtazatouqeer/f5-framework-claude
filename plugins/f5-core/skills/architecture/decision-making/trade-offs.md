---
name: trade-offs
description: Framework for analyzing and communicating architectural trade-offs
category: architecture/decision-making
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Architectural Trade-offs

## Overview

Every architectural decision involves trade-offs. Understanding and
communicating these trade-offs is essential for making informed decisions
and setting appropriate expectations with stakeholders.

## The CAP Theorem

```
┌─────────────────────────────────────────────────────────────┐
│                    CAP THEOREM                               │
│                                                             │
│                    Consistency                              │
│                        ▲                                    │
│                       / \                                   │
│                      /   \                                  │
│                     /     \                                 │
│                    /  CA   \                                │
│                   /         \                               │
│                  /           \                              │
│ Availability ◄──────────────────► Partition Tolerance       │
│                  \           /                              │
│                   \   AP   /                                │
│                    \       /                                │
│                     \ CP  /                                 │
│                      \   /                                  │
│                       \ /                                   │
│                                                             │
│  In distributed systems, pick two:                          │
│  CA: Single-node systems (PostgreSQL, traditional RDBMS)    │
│  CP: Consistent but may be unavailable (HBase, MongoDB)     │
│  AP: Available but eventually consistent (Cassandra, DynamoDB)│
└─────────────────────────────────────────────────────────────┘
```

## Common Trade-off Dimensions

### Performance vs Maintainability

```typescript
// Trade-off: Inline everything for performance vs modular code

// High Performance (harder to maintain)
function processOrderOptimized(order: RawOrder): ProcessedOrder {
  // Everything inlined for minimal function calls
  const items = order.items;
  let total = 0;
  let tax = 0;
  let discount = 0;

  for (let i = 0; i < items.length; i++) {
    const item = items[i];
    const itemTotal = item.price * item.quantity;
    total += itemTotal;

    // Inline tax calculation
    if (item.taxable) {
      tax += itemTotal * 0.08;
    }

    // Inline discount calculation
    if (order.couponCode && item.discountable) {
      discount += itemTotal * 0.1;
    }
  }

  return { total, tax, discount, grandTotal: total + tax - discount };
}

// Maintainable (slightly slower due to function calls)
function processOrderMaintainable(order: RawOrder): ProcessedOrder {
  const itemTotals = calculateItemTotals(order.items);
  const tax = calculateTax(order.items, itemTotals);
  const discount = calculateDiscount(order, itemTotals);
  const total = sumTotals(itemTotals);

  return {
    total,
    tax,
    discount,
    grandTotal: total + tax - discount,
  };
}

// Decision factors:
// - How often is this code modified? (maintainability wins)
// - Is this in a hot path? (performance may win)
// - What's the actual performance difference? (measure!)
```

### Consistency vs Availability

```typescript
// Trade-off: Strong consistency vs high availability

// Strong Consistency (lower availability)
class StrongConsistencyOrderService {
  async placeOrder(order: Order): Promise<OrderResult> {
    // Synchronous, distributed transaction
    const txn = await this.coordinator.beginTransaction();

    try {
      // All must succeed or all fail
      await this.inventoryService.reserve(order.items, txn);
      await this.paymentService.charge(order.total, txn);
      await this.orderRepository.save(order, txn);

      await txn.commit();
      return { success: true, orderId: order.id };
    } catch (error) {
      await txn.rollback();
      throw error; // Order fails if any service is down
    }
  }
}

// High Availability (eventual consistency)
class HighAvailabilityOrderService {
  async placeOrder(order: Order): Promise<OrderResult> {
    // Save order locally first (always available)
    order.status = 'pending';
    await this.orderRepository.save(order);

    // Publish events for async processing
    await this.eventBus.publish(new OrderPlacedEvent(order));

    // Order accepted, will be processed eventually
    return { success: true, orderId: order.id, status: 'pending' };
  }

  // Separate handler processes order asynchronously
  async handleOrderPlaced(event: OrderPlacedEvent): Promise<void> {
    try {
      await this.inventoryService.reserve(event.items);
      await this.paymentService.charge(event.total);
      await this.orderRepository.updateStatus(event.orderId, 'confirmed');
    } catch (error) {
      await this.orderRepository.updateStatus(event.orderId, 'failed');
      await this.compensate(event);
    }
  }
}
```

### Simplicity vs Flexibility

```typescript
// Trade-off: Simple, opinionated vs flexible, complex

// Simple, opinionated (less flexible)
interface SimpleConfig {
  databaseUrl: string;
  port: number;
  logLevel: 'debug' | 'info' | 'warn' | 'error';
}

class SimpleApp {
  constructor(config: SimpleConfig) {
    // Fixed architecture decisions
    this.db = new PostgresDatabase(config.databaseUrl);
    this.server = new ExpressServer(config.port);
    this.logger = new ConsoleLogger(config.logLevel);
  }
}

// Flexible, complex (more options, more complexity)
interface FlexibleConfig {
  database: {
    type: 'postgres' | 'mysql' | 'mongodb' | 'dynamodb';
    connection: Record<string, any>;
    poolSize?: number;
    ssl?: SslConfig;
    replication?: ReplicationConfig;
  };
  server: {
    type: 'express' | 'fastify' | 'koa' | 'hapi';
    port: number;
    middleware?: MiddlewareConfig[];
    cors?: CorsConfig;
    rateLimit?: RateLimitConfig;
  };
  logging: {
    type: 'console' | 'file' | 'cloudwatch' | 'datadog';
    level: string;
    format: 'json' | 'text';
    destination?: string;
  };
}

class FlexibleApp {
  constructor(config: FlexibleConfig) {
    this.db = DatabaseFactory.create(config.database);
    this.server = ServerFactory.create(config.server);
    this.logger = LoggerFactory.create(config.logging);
  }
}

// Decision factors:
// - How many use cases need to be supported?
// - Who will configure this? (developers vs operators)
// - What's the cost of wrong defaults?
```

## Trade-off Analysis Framework

```typescript
interface TradeoffAnalysis {
  decision: string;
  options: Option[];
  criteria: Criterion[];
  evaluation: EvaluationMatrix;
  recommendation: Recommendation;
}

interface Option {
  name: string;
  description: string;
}

interface Criterion {
  name: string;
  weight: number;  // 1-10 importance
  description: string;
}

interface EvaluationMatrix {
  scores: Map<string, Map<string, number>>;  // option -> criterion -> score
}

interface Recommendation {
  chosenOption: string;
  rationale: string;
  risks: string[];
  mitigations: string[];
}

// Example: Database Selection

const analysis: TradeoffAnalysis = {
  decision: 'Select primary database for e-commerce platform',

  options: [
    { name: 'PostgreSQL', description: 'Open-source relational database' },
    { name: 'MongoDB', description: 'Document-oriented NoSQL database' },
    { name: 'DynamoDB', description: 'AWS managed NoSQL database' },
  ],

  criteria: [
    { name: 'Consistency', weight: 9, description: 'ACID compliance for transactions' },
    { name: 'Scalability', weight: 7, description: 'Ability to handle growth' },
    { name: 'Query Flexibility', weight: 8, description: 'Complex query support' },
    { name: 'Operational Cost', weight: 6, description: 'Total cost of ownership' },
    { name: 'Team Expertise', weight: 7, description: 'Existing team knowledge' },
    { name: 'Ecosystem', weight: 5, description: 'Tools, libraries, community' },
  ],

  evaluation: {
    scores: new Map([
      ['PostgreSQL', new Map([
        ['Consistency', 10],
        ['Scalability', 6],
        ['Query Flexibility', 9],
        ['Operational Cost', 7],
        ['Team Expertise', 9],
        ['Ecosystem', 9],
      ])],
      ['MongoDB', new Map([
        ['Consistency', 6],
        ['Scalability', 8],
        ['Query Flexibility', 7],
        ['Operational Cost', 6],
        ['Team Expertise', 4],
        ['Ecosystem', 8],
      ])],
      ['DynamoDB', new Map([
        ['Consistency', 7],
        ['Scalability', 10],
        ['Query Flexibility', 4],
        ['Operational Cost', 8],
        ['Team Expertise', 3],
        ['Ecosystem', 6],
      ])],
    ]),
  },

  recommendation: {
    chosenOption: 'PostgreSQL',
    rationale: `
      PostgreSQL scores highest on weighted criteria (342 vs MongoDB 275 vs DynamoDB 263).
      Key factors: strong consistency for financial transactions, team expertise,
      and query flexibility for complex product searches.
    `,
    risks: [
      'Write scaling limited to single node initially',
      'Need read replicas for high traffic',
    ],
    mitigations: [
      'Plan for read replica setup at 10K concurrent users',
      'Evaluate Citus or partitioning if write scaling needed',
    ],
  },
};
```

## Visualizing Trade-offs

### Radar Chart Comparison

```
                    Consistency
                         10
                          │
                          │
       Ecosystem  8 ──────┼────── 8  Scalability
                    \     │     /
                     \    │    /
                      \   │   /
                       \  │  /
            Team  6 ────\ │ /──── 6  Cost
           Expertise     \│/
                          │
                          │
                    Query Flex

        ── PostgreSQL    -- MongoDB    ·· DynamoDB
```

### Decision Matrix Table

| Criterion | Weight | PostgreSQL | MongoDB | DynamoDB |
|-----------|--------|------------|---------|----------|
| Consistency | 9 | 10 (90) | 6 (54) | 7 (63) |
| Scalability | 7 | 6 (42) | 8 (56) | 10 (70) |
| Query Flexibility | 8 | 9 (72) | 7 (56) | 4 (32) |
| Operational Cost | 6 | 7 (42) | 6 (36) | 8 (48) |
| Team Expertise | 7 | 9 (63) | 4 (28) | 3 (21) |
| Ecosystem | 5 | 9 (45) | 8 (40) | 6 (30) |
| **Weighted Total** | | **354** | **270** | **264** |

## Common Trade-off Patterns

### Build vs Buy

```typescript
interface BuildVsBuyAnalysis {
  option: 'build' | 'buy';

  buildFactors: {
    customization: 'high' | 'medium' | 'low';
    competitiveAdvantage: boolean;
    teamCapability: boolean;
    timeToMarket: number;  // months
    maintenanceCost: number;  // per year
  };

  buyFactors: {
    fitToRequirements: 'perfect' | 'good' | 'poor';
    vendorStability: 'high' | 'medium' | 'low';
    licenseCost: number;  // per year
    integrationEffort: number;  // person-months
    lockInRisk: 'high' | 'medium' | 'low';
  };
}

// Decision heuristics:
// BUILD when:
// - Core differentiator for your business
// - No suitable solution exists
// - Team has expertise and capacity
// - Long-term cost of ownership is lower

// BUY when:
// - Commodity functionality (auth, payments, email)
// - Time to market is critical
// - Vendor solution is mature and well-supported
// - Internal expertise is lacking
```

### Synchronous vs Asynchronous

```typescript
// Decision framework for sync vs async
interface SyncAsyncDecision {
  operation: string;

  syncIndicators: {
    userWaitsForResult: boolean;
    operationIsFast: boolean;  // < 500ms
    strongConsistencyRequired: boolean;
    simpleErrorHandling: boolean;
  };

  asyncIndicators: {
    longRunningOperation: boolean;  // > 1s
    canBeProcessedLater: boolean;
    needsRetryLogic: boolean;
    crossServiceOrchestration: boolean;
    userCanBePollNotified: boolean;
  };
}

// Examples:
// SYNC: Login validation, add to cart, get product details
// ASYNC: Order processing, report generation, bulk imports
```

### Monolith vs Microservices

```typescript
interface ArchitectureStyleDecision {
  factors: {
    teamSize: number;
    deploymentFrequency: 'daily' | 'weekly' | 'monthly';
    scalingRequirements: 'uniform' | 'varied';
    domainComplexity: 'simple' | 'moderate' | 'complex';
    operationalMaturity: 'low' | 'medium' | 'high';
  };
}

// Monolith indicators:
// - Small team (< 10 developers)
// - Simple domain
// - Uniform scaling needs
// - Low operational maturity
// - Early stage product

// Microservices indicators:
// - Large team (> 20 developers)
// - Complex domain with clear boundaries
// - Different scaling needs per component
// - High operational maturity
// - Mature product with proven domain model
```

## Communicating Trade-offs

### To Technical Stakeholders

```markdown
## Trade-off Summary: Event Sourcing

### We're Trading:
- **Complexity** for **Auditability**
- **Immediate Consistency** for **Scalability**
- **Simple Queries** for **Temporal Queries**

### Quantified Impact:
| Metric | Before | After |
|--------|--------|-------|
| Write Latency | 5ms | 8ms (+60%) |
| Storage | 100GB | 300GB (+200%) |
| Query Complexity | Simple SQL | Projections required |
| Audit Coverage | 40% | 100% |
| Rebuild Time | N/A | 2 hours for full rebuild |

### Risk Mitigation:
- Snapshot strategy reduces rebuild time to 10 minutes
- Read projections optimize common queries
- Team training planned for Q2
```

### To Business Stakeholders

```markdown
## Trade-off Summary: Database Selection

### Business Impact

**Option A: PostgreSQL**
- ✅ Proven reliability for financial transactions
- ✅ No licensing costs
- ⚠️ May need infrastructure investment at scale
- 📊 Supports current + 3-year growth projection

**Option B: Cloud-Managed Database**
- ✅ Automatic scaling, less operational burden
- ❌ Higher monthly cost ($5K → $15K/month)
- ⚠️ Vendor lock-in limits future options

### Recommendation
PostgreSQL for Phase 1, with planned evaluation of managed options
at 100K daily users (projected: Month 18).
```

## Benefits

| Benefit | Description |
|---------|-------------|
| Informed Decisions | Understand full implications before committing |
| Stakeholder Alignment | Everyone understands what's being traded |
| Future Reference | Document why trade-offs were accepted |
| Risk Management | Identify and plan for negative consequences |

## When to Analyze Trade-offs

- Architectural decisions affecting multiple components
- Technology selections with long-term implications
- Performance optimizations with complexity cost
- Security measures affecting usability
- Scalability changes affecting consistency
