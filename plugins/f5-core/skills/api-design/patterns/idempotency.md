---
name: idempotency
description: API idempotency patterns for safe retries
category: api-design/patterns
applies_to: [all]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Idempotency Patterns

## Overview

Idempotency ensures that multiple identical requests have the same effect as a
single request. This is crucial for handling network failures and retries
safely, especially for financial transactions and other critical operations.

## Idempotency Concepts

```
┌─────────────────────────────────────────────────────────────────┐
│                  Idempotency by HTTP Method                      │
├────────────────┬────────────────────────────────────────────────┤
│ Method         │ Idempotent │ Safe   │ Notes                    │
├────────────────┼────────────┼────────┼──────────────────────────┤
│ GET            │ Yes        │ Yes    │ No side effects          │
│ HEAD           │ Yes        │ Yes    │ Same as GET, no body     │
│ OPTIONS        │ Yes        │ Yes    │ No side effects          │
│ PUT            │ Yes        │ No     │ Full replacement         │
│ DELETE         │ Yes        │ No     │ Delete once = delete N   │
│ POST           │ No         │ No     │ Creates new resource     │
│ PATCH          │ No*        │ No     │ Depends on implementation│
└────────────────┴────────────┴────────┴──────────────────────────┘

* PATCH can be made idempotent with proper design
```

## Idempotency Key Pattern

### Implementation

```typescript
interface IdempotencyRecord {
  key: string;
  request_hash: string;
  response_status: number;
  response_body: string;
  created_at: Date;
  expires_at: Date;
}

class IdempotencyService {
  private redis: Redis;
  private db: Database;
  private lockTTL = 10; // 10 seconds lock
  private recordTTL = 24 * 60 * 60; // 24 hours

  /**
   * Process request with idempotency
   */
  async processRequest(
    key: string,
    requestBody: any,
    handler: () => Promise<{ status: number; body: any }>
  ): Promise<{ status: number; body: any; cached: boolean }> {
    // Validate key format
    if (!this.isValidKey(key)) {
      throw new ValidationError([
        {
          field: 'Idempotency-Key',
          code: 'INVALID_FORMAT',
          message: 'Idempotency key must be a valid UUID',
        },
      ]);
    }

    // Calculate request hash to detect different payloads with same key
    const requestHash = this.hashRequest(requestBody);

    // Try to get existing record
    const existing = await this.getRecord(key);

    if (existing) {
      // Check if request matches
      if (existing.request_hash !== requestHash) {
        throw new ConflictError(
          'Idempotency key already used with different request body'
        );
      }

      // Return cached response
      return {
        status: existing.response_status,
        body: JSON.parse(existing.response_body),
        cached: true,
      };
    }

    // Acquire lock to prevent concurrent requests with same key
    const lockKey = `idempotency:lock:${key}`;
    const lockAcquired = await this.redis.set(lockKey, '1', 'NX', 'EX', this.lockTTL);

    if (!lockAcquired) {
      throw new ConflictError(
        'Request with this idempotency key is already being processed'
      );
    }

    try {
      // Double-check after acquiring lock
      const recheckRecord = await this.getRecord(key);
      if (recheckRecord) {
        return {
          status: recheckRecord.response_status,
          body: JSON.parse(recheckRecord.response_body),
          cached: true,
        };
      }

      // Execute the actual request
      const result = await handler();

      // Store the response
      await this.saveRecord({
        key,
        request_hash: requestHash,
        response_status: result.status,
        response_body: JSON.stringify(result.body),
        created_at: new Date(),
        expires_at: new Date(Date.now() + this.recordTTL * 1000),
      });

      return {
        ...result,
        cached: false,
      };
    } finally {
      // Release lock
      await this.redis.del(lockKey);
    }
  }

  private isValidKey(key: string): boolean {
    // Accept UUIDs or custom formats
    const uuidRegex =
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    const customRegex = /^[a-zA-Z0-9_-]{16,64}$/;
    return uuidRegex.test(key) || customRegex.test(key);
  }

  private hashRequest(body: any): string {
    const normalized = JSON.stringify(body, Object.keys(body).sort());
    return crypto.createHash('sha256').update(normalized).digest('hex');
  }

  private async getRecord(key: string): Promise<IdempotencyRecord | null> {
    // Try cache first
    const cached = await this.redis.get(`idempotency:${key}`);
    if (cached) {
      return JSON.parse(cached);
    }

    // Fall back to database
    const record = await this.db.idempotencyRecords.findByKey(key);
    if (record && record.expires_at > new Date()) {
      // Cache for future requests
      await this.redis.set(
        `idempotency:${key}`,
        JSON.stringify(record),
        'EX',
        Math.floor((record.expires_at.getTime() - Date.now()) / 1000)
      );
      return record;
    }

    return null;
  }

  private async saveRecord(record: IdempotencyRecord): Promise<void> {
    // Save to database
    await this.db.idempotencyRecords.create(record);

    // Cache
    await this.redis.set(
      `idempotency:${record.key}`,
      JSON.stringify(record),
      'EX',
      this.recordTTL
    );
  }
}
```

### Middleware

```typescript
function idempotencyMiddleware(options?: {
  headerName?: string;
  required?: boolean;
  methods?: string[];
}) {
  const {
    headerName = 'Idempotency-Key',
    required = false,
    methods = ['POST', 'PATCH'],
  } = options || {};

  const idempotencyService = new IdempotencyService(redis, db);

  return async (req: Request, res: Response, next: NextFunction) => {
    // Skip if method doesn't need idempotency
    if (!methods.includes(req.method)) {
      return next();
    }

    const idempotencyKey = req.headers[headerName.toLowerCase()] as string;

    // Check if key is required
    if (!idempotencyKey) {
      if (required) {
        return res.status(400).json({
          error: {
            code: 'MISSING_IDEMPOTENCY_KEY',
            message: `${headerName} header is required`,
          },
        });
      }
      return next();
    }

    try {
      // Store original send function
      const originalSend = res.send.bind(res);
      let responseBody: any;
      let responseCaptured = false;

      // Override send to capture response
      res.send = function (body: any) {
        if (!responseCaptured) {
          responseBody = body;
          responseCaptured = true;
        }
        return originalSend(body);
      };

      // Process with idempotency
      const result = await idempotencyService.processRequest(
        idempotencyKey,
        req.body,
        async () => {
          // Continue to next middleware/handler
          await new Promise<void>((resolve, reject) => {
            res.on('finish', resolve);
            res.on('error', reject);
            next();
          });

          return {
            status: res.statusCode,
            body: responseBody,
          };
        }
      );

      if (result.cached) {
        // Return cached response
        res.set('Idempotency-Replayed', 'true');
        return res.status(result.status).json(result.body);
      }
    } catch (error) {
      if (error instanceof ConflictError) {
        return res.status(409).json({
          error: {
            code: 'IDEMPOTENCY_CONFLICT',
            message: error.message,
          },
        });
      }
      next(error);
    }
  };
}

// Usage
app.post(
  '/api/payments',
  idempotencyMiddleware({ required: true }),
  processPayment
);

app.post(
  '/api/orders',
  idempotencyMiddleware({ required: false }),
  createOrder
);
```

## Client Implementation

```typescript
class ApiClient {
  private baseUrl: string;
  private apiKey: string;

  /**
   * Make idempotent request with automatic retries
   */
  async idempotentRequest<T>(
    method: 'POST' | 'PATCH',
    path: string,
    body: any,
    options?: {
      idempotencyKey?: string;
      maxRetries?: number;
      retryDelay?: number;
    }
  ): Promise<T> {
    const {
      idempotencyKey = crypto.randomUUID(),
      maxRetries = 3,
      retryDelay = 1000,
    } = options || {};

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        const response = await fetch(`${this.baseUrl}${path}`, {
          method,
          headers: {
            Authorization: `Bearer ${this.apiKey}`,
            'Content-Type': 'application/json',
            'Idempotency-Key': idempotencyKey,
          },
          body: JSON.stringify(body),
        });

        // Check for idempotency conflict
        if (response.status === 409) {
          const error = await response.json();
          if (error.error?.code === 'IDEMPOTENCY_CONFLICT') {
            // Request body mismatch - this is a programming error
            throw new Error('Idempotency key used with different request body');
          }
        }

        // Success - check if replayed
        if (response.ok) {
          const isReplayed = response.headers.get('Idempotency-Replayed') === 'true';
          if (isReplayed) {
            console.log(`Response replayed for idempotency key: ${idempotencyKey}`);
          }
          return response.json();
        }

        // Non-retryable errors
        if (response.status >= 400 && response.status < 500) {
          throw new ApiError(await response.json());
        }

        // Server error - retry
        if (attempt < maxRetries) {
          await this.sleep(retryDelay * Math.pow(2, attempt - 1));
          continue;
        }

        throw new ApiError(await response.json());
      } catch (error) {
        // Network error - retry with same idempotency key
        if (error instanceof TypeError && attempt < maxRetries) {
          await this.sleep(retryDelay * Math.pow(2, attempt - 1));
          continue;
        }
        throw error;
      }
    }

    throw new Error('Max retries exceeded');
  }

  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}

// Usage
const client = new ApiClient();

// Safe to retry - same idempotency key ensures single execution
const payment = await client.idempotentRequest('POST', '/payments', {
  amount: 9999,
  currency: 'USD',
  customer_id: 'cus_123',
});
```

## Database-Level Idempotency

```typescript
/**
 * Using database constraints for idempotency
 */
class OrderService {
  async createOrder(
    customerId: string,
    items: OrderItem[],
    idempotencyKey: string
  ): Promise<Order> {
    // Use idempotency key as part of unique constraint
    try {
      const order = await this.db.orders.create({
        data: {
          id: generateOrderId(),
          customer_id: customerId,
          items: {
            create: items,
          },
          idempotency_key: idempotencyKey,
          status: 'pending',
        },
      });

      return order;
    } catch (error) {
      // Handle unique constraint violation
      if (error.code === 'P2002' && error.meta?.target?.includes('idempotency_key')) {
        // Return existing order
        const existing = await this.db.orders.findUnique({
          where: { idempotency_key: idempotencyKey },
        });

        if (existing) {
          return existing;
        }
      }
      throw error;
    }
  }
}

// Database schema
/*
CREATE TABLE orders (
  id VARCHAR(26) PRIMARY KEY,
  customer_id VARCHAR(26) NOT NULL,
  idempotency_key VARCHAR(64) UNIQUE,
  status VARCHAR(20) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  -- Idempotency key can be null for orders created without one
  -- But if provided, it must be unique
  CONSTRAINT unique_idempotency_key UNIQUE (idempotency_key)
);

CREATE INDEX idx_orders_idempotency_key ON orders(idempotency_key);
*/
```

## Transactional Idempotency

```typescript
/**
 * Idempotency with transactional outbox pattern
 */
class PaymentService {
  async processPayment(
    paymentData: PaymentData,
    idempotencyKey: string
  ): Promise<Payment> {
    return this.db.$transaction(async (tx) => {
      // Check for existing idempotent request
      const existing = await tx.idempotencyRecords.findUnique({
        where: { key: idempotencyKey },
      });

      if (existing) {
        // Return cached result
        return JSON.parse(existing.response) as Payment;
      }

      // Process payment
      const payment = await tx.payments.create({
        data: {
          id: generatePaymentId(),
          amount: paymentData.amount,
          currency: paymentData.currency,
          customer_id: paymentData.customerId,
          status: 'processing',
        },
      });

      // Call external payment processor
      const processorResult = await this.paymentProcessor.charge({
        amount: paymentData.amount,
        currency: paymentData.currency,
        source: paymentData.paymentMethodId,
      });

      // Update payment with result
      const updatedPayment = await tx.payments.update({
        where: { id: payment.id },
        data: {
          status: processorResult.success ? 'succeeded' : 'failed',
          processor_id: processorResult.id,
          failure_reason: processorResult.error,
        },
      });

      // Store idempotency record
      await tx.idempotencyRecords.create({
        data: {
          key: idempotencyKey,
          request_hash: this.hashRequest(paymentData),
          response: JSON.stringify(updatedPayment),
          expires_at: new Date(Date.now() + 24 * 60 * 60 * 1000),
        },
      });

      // Add to outbox for event publishing
      await tx.outbox.create({
        data: {
          event_type: 'payment.processed',
          payload: JSON.stringify({
            payment_id: updatedPayment.id,
            status: updatedPayment.status,
          }),
        },
      });

      return updatedPayment;
    });
  }
}
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│                Idempotency Best Practices                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Require Idempotency Keys for Critical Operations            │
│     └── Payments, orders, transfers                             │
│                                                                  │
│  2. Validate Key Format                                         │
│     └── UUID or structured format                               │
│                                                                  │
│  3. Hash Request Body                                           │
│     └── Detect mismatched requests with same key                │
│                                                                  │
│  4. Set Appropriate TTL                                         │
│     └── 24 hours is common, balance storage vs safety           │
│                                                                  │
│  5. Handle Concurrent Requests                                  │
│     └── Use locks to prevent race conditions                    │
│                                                                  │
│  6. Return Cached Response Exactly                              │
│     └── Same status code and body                               │
│                                                                  │
│  7. Indicate Replayed Responses                                 │
│     └── Idempotency-Replayed header                             │
│                                                                  │
│  8. Use Database Constraints                                    │
│     └── Secondary protection with unique constraints            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```
