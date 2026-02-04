---
name: batch-operations
description: API batch operations and bulk processing
category: performance/api
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Batch Operations

## Overview

Batch operations allow multiple actions to be performed in a single API request,
reducing network overhead and improving performance.

## Benefits of Batching

| Metric | Individual Requests | Batched |
|--------|---------------------|---------|
| Network round trips | N | 1 |
| HTTP overhead | N × headers | 1 × headers |
| Connection setup | N × latency | 1 × latency |
| Database transactions | N | 1 |

## Batch API Design

### Simple Batch Endpoint

```typescript
// POST /api/batch
interface BatchRequest {
  operations: BatchOperation[];
}

interface BatchOperation {
  method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  path: string;
  body?: any;
  headers?: Record<string, string>;
}

interface BatchResponse {
  results: BatchResult[];
}

interface BatchResult {
  status: number;
  body: any;
  headers?: Record<string, string>;
}

app.post('/api/batch', async (req, res) => {
  const { operations } = req.body as BatchRequest;

  // Limit batch size
  if (operations.length > 100) {
    return res.status(400).json({
      error: 'Batch size exceeds maximum of 100 operations',
    });
  }

  const results: BatchResult[] = [];

  for (const op of operations) {
    try {
      const result = await executeOperation(op, req);
      results.push(result);
    } catch (error) {
      results.push({
        status: 500,
        body: { error: error.message },
      });
    }
  }

  res.json({ results });
});

async function executeOperation(
  op: BatchOperation,
  parentReq: Request
): Promise<BatchResult> {
  // Create mock request/response
  const mockReq = createMockRequest(op, parentReq);
  const mockRes = createMockResponse();

  // Route to appropriate handler
  await routeRequest(mockReq, mockRes);

  return {
    status: mockRes.statusCode,
    body: mockRes.body,
    headers: mockRes.headers,
  };
}
```

### Bulk Create/Update

```typescript
// POST /api/users/bulk
interface BulkCreateRequest {
  users: CreateUserDTO[];
}

app.post('/api/users/bulk', async (req, res) => {
  const { users } = req.body as BulkCreateRequest;

  // Validate all first
  const validationErrors: { index: number; errors: string[] }[] = [];
  for (let i = 0; i < users.length; i++) {
    const errors = validateUser(users[i]);
    if (errors.length > 0) {
      validationErrors.push({ index: i, errors });
    }
  }

  if (validationErrors.length > 0) {
    return res.status(400).json({ errors: validationErrors });
  }

  // Bulk insert with transaction
  const result = await prisma.$transaction(async (tx) => {
    return tx.user.createMany({
      data: users,
      skipDuplicates: true,
    });
  });

  res.json({
    created: result.count,
    message: `Successfully created ${result.count} users`,
  });
});

// PATCH /api/users/bulk
interface BulkUpdateRequest {
  updates: { id: string; data: Partial<UpdateUserDTO> }[];
}

app.patch('/api/users/bulk', async (req, res) => {
  const { updates } = req.body as BulkUpdateRequest;

  const results = await prisma.$transaction(
    updates.map(({ id, data }) =>
      prisma.user.update({
        where: { id },
        data,
      })
    )
  );

  res.json({
    updated: results.length,
    users: results,
  });
});
```

### Bulk Delete

```typescript
// DELETE /api/users/bulk
interface BulkDeleteRequest {
  ids: string[];
}

app.delete('/api/users/bulk', async (req, res) => {
  const { ids } = req.body as BulkDeleteRequest;

  // Soft delete
  const result = await prisma.user.updateMany({
    where: { id: { in: ids } },
    data: { deletedAt: new Date() },
  });

  // Or hard delete
  // const result = await prisma.user.deleteMany({
  //   where: { id: { in: ids } },
  // });

  res.json({
    deleted: result.count,
  });
});
```

## GraphQL Batching

### Query Batching

```typescript
// Apollo Server with batching
import { ApolloServer } from '@apollo/server';
import { expressMiddleware } from '@apollo/server/express4';

const server = new ApolloServer({
  typeDefs,
  resolvers,
  // Enable query batching
  allowBatchedHttpRequests: true,
});

// Client sends array of queries
// POST /graphql
// [
//   { "query": "{ user(id: \"1\") { name } }" },
//   { "query": "{ user(id: \"2\") { name } }" }
// ]
```

### DataLoader for N+1 Prevention

```typescript
import DataLoader from 'dataloader';

// Create loaders per request
function createLoaders() {
  return {
    users: new DataLoader<string, User>(async (ids) => {
      const users = await prisma.user.findMany({
        where: { id: { in: ids as string[] } },
      });
      const userMap = new Map(users.map(u => [u.id, u]));
      return ids.map(id => userMap.get(id) || null);
    }),

    ordersByUser: new DataLoader<string, Order[]>(async (userIds) => {
      const orders = await prisma.order.findMany({
        where: { userId: { in: userIds as string[] } },
      });
      const ordersByUser = new Map<string, Order[]>();
      for (const order of orders) {
        if (!ordersByUser.has(order.userId)) {
          ordersByUser.set(order.userId, []);
        }
        ordersByUser.get(order.userId)!.push(order);
      }
      return userIds.map(id => ordersByUser.get(id) || []);
    }),
  };
}

// Use in resolvers
const resolvers = {
  Query: {
    users: async (_, { ids }, { loaders }) => {
      return loaders.users.loadMany(ids);
    },
  },
  User: {
    orders: async (parent, _, { loaders }) => {
      return loaders.ordersByUser.load(parent.id);
    },
  },
};
```

## Parallel vs Sequential Processing

### Parallel Processing

```typescript
// Process batches in parallel (independent operations)
async function processBatchParallel<T, R>(
  items: T[],
  processor: (item: T) => Promise<R>,
  concurrency: number = 10
): Promise<R[]> {
  const results: R[] = [];
  const chunks = chunkArray(items, concurrency);

  for (const chunk of chunks) {
    const chunkResults = await Promise.all(
      chunk.map(item => processor(item))
    );
    results.push(...chunkResults);
  }

  return results;
}

function chunkArray<T>(array: T[], size: number): T[][] {
  const chunks: T[][] = [];
  for (let i = 0; i < array.length; i += size) {
    chunks.push(array.slice(i, i + size));
  }
  return chunks;
}

// Usage
const results = await processBatchParallel(
  userIds,
  (id) => fetchUserData(id),
  10 // 10 concurrent requests
);
```

### Sequential Processing

```typescript
// Process sequentially (dependent operations or rate limits)
async function processBatchSequential<T, R>(
  items: T[],
  processor: (item: T, index: number) => Promise<R>,
  onProgress?: (completed: number, total: number) => void
): Promise<R[]> {
  const results: R[] = [];

  for (let i = 0; i < items.length; i++) {
    const result = await processor(items[i], i);
    results.push(result);
    onProgress?.(i + 1, items.length);
  }

  return results;
}
```

### Adaptive Batching

```typescript
// Adjust batch size based on response time
class AdaptiveBatcher<T, R> {
  private batchSize: number;
  private minBatchSize = 1;
  private maxBatchSize = 100;
  private targetLatency = 1000; // 1 second

  constructor(private processor: (items: T[]) => Promise<R[]>) {
    this.batchSize = 10; // Start with moderate size
  }

  async process(items: T[]): Promise<R[]> {
    const results: R[] = [];
    let i = 0;

    while (i < items.length) {
      const batch = items.slice(i, i + this.batchSize);
      const start = Date.now();

      const batchResults = await this.processor(batch);
      results.push(...batchResults);

      const latency = Date.now() - start;
      this.adjustBatchSize(latency);

      i += this.batchSize;
    }

    return results;
  }

  private adjustBatchSize(latency: number): void {
    if (latency < this.targetLatency * 0.5) {
      // Too fast, increase batch size
      this.batchSize = Math.min(this.batchSize * 1.5, this.maxBatchSize);
    } else if (latency > this.targetLatency * 1.5) {
      // Too slow, decrease batch size
      this.batchSize = Math.max(this.batchSize * 0.75, this.minBatchSize);
    }
    this.batchSize = Math.round(this.batchSize);
  }
}
```

## Error Handling in Batches

### Partial Success

```typescript
interface BatchItemResult<T> {
  success: boolean;
  data?: T;
  error?: string;
  index: number;
}

async function processBatchWithErrors<T, R>(
  items: T[],
  processor: (item: T) => Promise<R>
): Promise<{
  results: BatchItemResult<R>[];
  successCount: number;
  errorCount: number;
}> {
  const results: BatchItemResult<R>[] = [];
  let successCount = 0;
  let errorCount = 0;

  for (let i = 0; i < items.length; i++) {
    try {
      const data = await processor(items[i]);
      results.push({ success: true, data, index: i });
      successCount++;
    } catch (error) {
      results.push({
        success: false,
        error: error.message,
        index: i,
      });
      errorCount++;
    }
  }

  return { results, successCount, errorCount };
}

// API response
app.post('/api/users/bulk', async (req, res) => {
  const { users } = req.body;

  const { results, successCount, errorCount } = await processBatchWithErrors(
    users,
    (user) => prisma.user.create({ data: user })
  );

  const status = errorCount === 0 ? 200 : errorCount === users.length ? 400 : 207;

  res.status(status).json({
    results,
    summary: {
      total: users.length,
      succeeded: successCount,
      failed: errorCount,
    },
  });
});
```

### Transaction Rollback

```typescript
// All-or-nothing batch
app.post('/api/orders/bulk', async (req, res) => {
  const { orders } = req.body;

  try {
    const results = await prisma.$transaction(async (tx) => {
      const created: Order[] = [];

      for (const order of orders) {
        // Validate inventory
        const product = await tx.product.findUnique({
          where: { id: order.productId },
        });

        if (!product || product.stock < order.quantity) {
          throw new Error(`Insufficient stock for product ${order.productId}`);
        }

        // Create order
        const newOrder = await tx.order.create({ data: order });
        created.push(newOrder);

        // Decrement stock
        await tx.product.update({
          where: { id: order.productId },
          data: { stock: { decrement: order.quantity } },
        });
      }

      return created;
    });

    res.json({ orders: results });
  } catch (error) {
    // All operations rolled back
    res.status(400).json({ error: error.message });
  }
});
```

## Best Practices

1. **Set batch size limits** - Prevent resource exhaustion
2. **Use transactions** - Ensure data consistency
3. **Handle partial failures** - Report which items succeeded/failed
4. **Implement rate limiting** - Prevent abuse
5. **Validate all items first** - Fail fast before processing
6. **Use appropriate concurrency** - Balance speed vs resource usage
7. **Provide progress feedback** - For long-running batches
8. **Consider async processing** - For very large batches
