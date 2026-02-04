---
name: logging-best-practices
description: Best practices for application logging
category: devops/logging
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Logging Best Practices

## Overview

Effective logging is crucial for debugging, monitoring, and understanding
application behavior. Good logs help identify issues quickly and provide
context for troubleshooting.

## Log Levels

```
┌─────────────────────────────────────────────────────────────────┐
│                        Log Levels                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Level      │ When to Use                                       │
│  ──────────────────────────────────────────────────────────     │
│  FATAL      │ Application cannot continue, immediate shutdown   │
│  ERROR      │ Error occurred, feature/operation failed          │
│  WARN       │ Unexpected situation, not an error                │
│  INFO       │ Normal operation, significant events              │
│  DEBUG      │ Detailed information for debugging                │
│  TRACE      │ Very detailed, step-by-step execution             │
│                                                                  │
│  Production: INFO and above                                      │
│  Development: DEBUG and above                                    │
│  Troubleshooting: TRACE (temporary)                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## What to Log

### DO Log

```typescript
// ✅ Application lifecycle events
logger.info('Application started', { port: 3000, environment: 'production' });
logger.info('Application shutting down');

// ✅ Request/Response (without sensitive data)
logger.info('Request received', {
  method: 'POST',
  path: '/api/orders',
  requestId: '123-456',
  userId: 'user-789',
});

logger.info('Response sent', {
  method: 'POST',
  path: '/api/orders',
  statusCode: 201,
  duration: 145,
  requestId: '123-456',
});

// ✅ Business events
logger.info('Order created', {
  orderId: 'order-123',
  userId: 'user-789',
  total: 99.99,
  itemCount: 3,
});

// ✅ Errors with context
logger.error('Failed to process payment', {
  orderId: 'order-123',
  error: error.message,
  stack: error.stack,
  paymentMethod: 'credit_card',
});

// ✅ External service calls
logger.info('External API call', {
  service: 'payment-gateway',
  operation: 'charge',
  duration: 234,
  success: true,
});

// ✅ Security events
logger.warn('Failed login attempt', {
  username: 'john@example.com',
  ip: '192.168.1.100',
  userAgent: 'Mozilla/5.0...',
  reason: 'invalid_password',
});
```

### DON'T Log

```typescript
// ❌ Sensitive data
logger.info('User login', {
  password: 'secret123', // NEVER log passwords
  creditCard: '4111-1111-1111-1111', // NEVER log credit cards
  ssn: '123-45-6789', // NEVER log SSN
  apiKey: 'sk_live_xxx', // NEVER log API keys
});

// ❌ Personal Identifiable Information (PII) in production
logger.info('User details', {
  email: 'john@example.com', // Avoid or mask
  phone: '+1234567890', // Avoid or mask
  address: '123 Main St', // Avoid or mask
});

// ❌ Excessive logging in hot paths
for (let i = 0; i < 1000000; i++) {
  logger.debug('Processing item', { index: i }); // Too verbose
}

// ❌ Binary or large data
logger.info('File uploaded', {
  content: buffer.toString('base64'), // Don't log file contents
});
```

## Log Message Guidelines

```typescript
// ✅ Good: Clear, actionable messages
logger.error('Database connection failed after 3 retries', {
  host: 'db.example.com',
  port: 5432,
  error: 'Connection refused',
});

// ❌ Bad: Vague messages
logger.error('Error');
logger.error('Something went wrong');
logger.error('Failed');

// ✅ Good: Consistent format
logger.info('User registered', { userId: '123', plan: 'premium' });
logger.info('Order created', { orderId: '456', userId: '123' });

// ❌ Bad: Inconsistent format
logger.info('New user: 123');
logger.info(`Order 456 was created for user 123`);

// ✅ Good: Use present tense for actions
logger.info('Processing payment');
logger.info('Payment processed');

// ❌ Bad: Mixed tenses
logger.info('We are going to process payment');
logger.info('Payment was being processed');
```

## Context and Correlation

```typescript
// Correlation ID for request tracing
import { v4 as uuid } from 'uuid';

function requestLogger(req, res, next) {
  const correlationId = req.headers['x-correlation-id'] || uuid();
  req.correlationId = correlationId;
  res.setHeader('x-correlation-id', correlationId);

  // Add to logger context
  req.logger = logger.child({ correlationId });

  next();
}

// Use throughout request lifecycle
app.post('/api/orders', async (req, res) => {
  req.logger.info('Creating order');

  // Pass to service layer
  const order = await orderService.create(req.body, req.logger);

  req.logger.info('Order created', { orderId: order.id });
  res.json(order);
});

// Service layer
class OrderService {
  async create(data: OrderData, logger: Logger) {
    logger.info('Validating order data');

    logger.info('Calculating totals');
    const totals = this.calculateTotals(data);

    logger.info('Saving to database');
    const order = await this.repository.save({ ...data, ...totals });

    logger.info('Order saved', { orderId: order.id });
    return order;
  }
}
```

## Performance Considerations

```typescript
// ✅ Lazy evaluation for expensive operations
logger.debug(() => `Complex calculation result: ${expensiveOperation()}`);

// ✅ Check log level before expensive formatting
if (logger.isDebugEnabled()) {
  const debugInfo = gatherDebugInfo(); // Only called if DEBUG is enabled
  logger.debug('Debug info', debugInfo);
}

// ✅ Use sampling for high-volume logs
const SAMPLE_RATE = 0.01; // 1%
if (Math.random() < SAMPLE_RATE) {
  logger.debug('Sampled request', { path: req.path });
}

// ✅ Async logging to avoid blocking
const logger = pino({
  transport: {
    target: 'pino/file',
    options: { destination: '/var/log/app.log' },
  },
});

// ✅ Buffer logs and batch writes
const logger = pino({
  transport: {
    target: 'pino-pretty',
  },
  sync: false, // Async logging
});
```

## Error Logging

```typescript
// ✅ Include full error details
try {
  await processOrder(order);
} catch (error) {
  logger.error('Order processing failed', {
    orderId: order.id,
    error: {
      name: error.name,
      message: error.message,
      stack: error.stack,
      code: error.code,
    },
    context: {
      userId: order.userId,
      items: order.items.length,
    },
  });
  throw error;
}

// ✅ Categorize errors
class AppError extends Error {
  constructor(
    message: string,
    public code: string,
    public isOperational: boolean = true
  ) {
    super(message);
    this.name = this.constructor.name;
  }
}

// Operational errors (expected)
throw new AppError('Insufficient funds', 'INSUFFICIENT_FUNDS', true);

// Programming errors (unexpected)
throw new AppError('Invalid state', 'INVALID_STATE', false);

// Log differently based on error type
function logError(error: Error, context: object) {
  const errorInfo = {
    ...context,
    error: {
      name: error.name,
      message: error.message,
      stack: error.stack,
    },
  };

  if (error instanceof AppError && error.isOperational) {
    logger.warn('Operational error', errorInfo);
  } else {
    logger.error('Unexpected error', errorInfo);
  }
}
```

## Environment-Specific Configuration

```typescript
// config/logging.ts
import pino from 'pino';

const logConfig = {
  development: {
    level: 'debug',
    transport: {
      target: 'pino-pretty',
      options: {
        colorize: true,
        translateTime: 'SYS:standard',
      },
    },
  },
  staging: {
    level: 'debug',
    transport: {
      target: 'pino/file',
      options: { destination: '/var/log/app.log' },
    },
  },
  production: {
    level: 'info',
    // JSON output for log aggregation
    formatters: {
      level: (label) => ({ level: label }),
    },
  },
};

export const logger = pino(logConfig[process.env.NODE_ENV || 'development']);
```

## Log Retention and Rotation

```yaml
# logrotate configuration
/var/log/app/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0644 app app
    sharedscripts
    postrotate
        [ -f /var/run/app.pid ] && kill -USR1 `cat /var/run/app.pid`
    endscript
}
```

```typescript
// Using pino with file rotation
import pino from 'pino';
import { createStream } from 'rotating-file-stream';

const stream = createStream('app.log', {
  size: '10M', // Rotate every 10MB
  interval: '1d', // Rotate daily
  compress: 'gzip',
  path: '/var/log/app',
  maxFiles: 14,
});

export const logger = pino(stream);
```

## Security Logging

```typescript
// Security event logger
const securityLogger = logger.child({ type: 'security' });

// Authentication events
securityLogger.info('User authenticated', {
  event: 'auth.login.success',
  userId: user.id,
  ip: req.ip,
  userAgent: req.headers['user-agent'],
});

securityLogger.warn('Authentication failed', {
  event: 'auth.login.failure',
  username: req.body.username,
  ip: req.ip,
  reason: 'invalid_credentials',
  attemptCount: failedAttempts,
});

// Authorization events
securityLogger.warn('Unauthorized access attempt', {
  event: 'authz.denied',
  userId: user.id,
  resource: req.path,
  action: req.method,
  reason: 'insufficient_permissions',
});

// Suspicious activity
securityLogger.error('Potential attack detected', {
  event: 'security.threat',
  type: 'sql_injection_attempt',
  ip: req.ip,
  payload: sanitize(req.body),
});
```

## Best Practices Checklist

```
┌─────────────────────────────────────────────────────────────────┐
│                 Logging Best Practices Checklist                 │
├─────────────────────────────────────────────────────────────────┤
│ ☐ Use structured logging (JSON format)                          │
│ ☐ Include correlation IDs for request tracing                   │
│ ☐ Use appropriate log levels                                    │
│ ☐ Never log sensitive data (passwords, keys, PII)              │
│ ☐ Include contextual information                                │
│ ☐ Log at service boundaries (requests, external calls)          │
│ ☐ Use consistent message formats                                │
│ ☐ Configure environment-specific log levels                     │
│ ☐ Implement log rotation and retention                          │
│ ☐ Include timestamps in UTC                                     │
│ ☐ Log security-relevant events                                  │
│ ☐ Monitor log volume and storage costs                          │
└─────────────────────────────────────────────────────────────────┘
```
