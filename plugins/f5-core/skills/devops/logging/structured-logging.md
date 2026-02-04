---
name: structured-logging
description: Structured logging patterns and implementation
category: devops/logging
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Structured Logging

## Overview

Structured logging outputs log messages in a machine-readable format (typically JSON),
making logs easier to search, filter, and analyze.

## Structured vs Unstructured

```
┌─────────────────────────────────────────────────────────────────┐
│               Structured vs Unstructured Logging                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Unstructured (Plain Text):                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 2024-01-15 10:30:45 INFO User john@example.com logged   │   │
│  │ in from 192.168.1.100                                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│  • Difficult to parse                                           │
│  • Hard to search specific fields                               │
│  • Inconsistent format                                          │
│                                                                  │
│  Structured (JSON):                                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ {                                                        │   │
│  │   "timestamp": "2024-01-15T10:30:45.123Z",              │   │
│  │   "level": "info",                                       │   │
│  │   "message": "User logged in",                           │   │
│  │   "email": "john@example.com",                           │   │
│  │   "ip": "192.168.1.100"                                  │   │
│  │ }                                                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│  • Easy to parse                                                │
│  • Searchable by any field                                      │
│  • Consistent structure                                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Pino (Node.js)

### Basic Setup

```typescript
// logger.ts
import pino from 'pino';

export const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  formatters: {
    level: (label) => ({ level: label }),
    bindings: (bindings) => ({
      pid: bindings.pid,
      host: bindings.hostname,
    }),
  },
  timestamp: () => `,"timestamp":"${new Date().toISOString()}"`,
  base: {
    service: 'api-service',
    version: process.env.npm_package_version,
    environment: process.env.NODE_ENV,
  },
});

// Usage
logger.info('Server started', { port: 3000 });
// Output: {"level":"info","timestamp":"2024-01-15T10:30:45.123Z","service":"api-service","message":"Server started","port":3000}
```

### Child Loggers

```typescript
// Create child logger with additional context
const requestLogger = logger.child({
  correlationId: '123-456',
  userId: 'user-789',
});

requestLogger.info('Processing request');
// Output includes correlationId and userId

// For Express middleware
function loggingMiddleware(req, res, next) {
  req.log = logger.child({
    correlationId: req.headers['x-correlation-id'] || uuid(),
    method: req.method,
    path: req.path,
  });

  const start = Date.now();

  res.on('finish', () => {
    req.log.info('Request completed', {
      statusCode: res.statusCode,
      duration: Date.now() - start,
    });
  });

  next();
}
```

### Pino with Express

```typescript
// app.ts
import express from 'express';
import pino from 'pino';
import pinoHttp from 'pino-http';

const logger = pino({
  level: 'info',
});

const app = express();

app.use(
  pinoHttp({
    logger,
    customLogLevel: (req, res, err) => {
      if (res.statusCode >= 500 || err) return 'error';
      if (res.statusCode >= 400) return 'warn';
      return 'info';
    },
    customSuccessMessage: (req, res) => {
      return `${req.method} ${req.url} completed`;
    },
    customErrorMessage: (req, res, err) => {
      return `${req.method} ${req.url} failed: ${err.message}`;
    },
    customAttributeKeys: {
      req: 'request',
      res: 'response',
      err: 'error',
      responseTime: 'duration',
    },
    redact: {
      paths: ['request.headers.authorization', 'request.body.password'],
      remove: true,
    },
  })
);

app.get('/api/users', (req, res) => {
  req.log.info('Fetching users');
  res.json([]);
});
```

### Pino Pretty (Development)

```typescript
// development config
import pino from 'pino';

const logger = pino({
  transport: {
    target: 'pino-pretty',
    options: {
      colorize: true,
      translateTime: 'SYS:standard',
      ignore: 'pid,hostname',
      messageFormat: '{levelLabel} - {msg}',
    },
  },
});

// Output (colorized):
// INFO - Server started
// INFO - Processing request
// ERROR - Database connection failed
```

## Winston (Node.js)

### Basic Setup

```typescript
// logger.ts
import winston from 'winston';

export const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  defaultMeta: {
    service: 'api-service',
    version: process.env.npm_package_version,
  },
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: 'error.log', level: 'error' }),
    new winston.transports.File({ filename: 'combined.log' }),
  ],
});

// Development format
if (process.env.NODE_ENV !== 'production') {
  logger.add(
    new winston.transports.Console({
      format: winston.format.combine(winston.format.colorize(), winston.format.simple()),
    })
  );
}
```

### Winston with Metadata

```typescript
// Using child loggers with metadata
const childLogger = logger.child({ requestId: '123-456' });
childLogger.info('Processing');

// Adding metadata to log calls
logger.info('User action', {
  userId: 'user-123',
  action: 'login',
  ip: '192.168.1.100',
});

// Custom format for structured output
const customFormat = winston.format.printf(({ level, message, timestamp, ...meta }) => {
  return JSON.stringify({
    timestamp,
    level,
    message,
    ...meta,
  });
});
```

## NestJS Logging

```typescript
// logger.service.ts
import { Injectable, LoggerService } from '@nestjs/common';
import pino from 'pino';

@Injectable()
export class PinoLoggerService implements LoggerService {
  private logger = pino({
    level: process.env.LOG_LEVEL || 'info',
  });

  log(message: string, context?: string) {
    this.logger.info({ context }, message);
  }

  error(message: string, trace?: string, context?: string) {
    this.logger.error({ context, trace }, message);
  }

  warn(message: string, context?: string) {
    this.logger.warn({ context }, message);
  }

  debug(message: string, context?: string) {
    this.logger.debug({ context }, message);
  }

  verbose(message: string, context?: string) {
    this.logger.trace({ context }, message);
  }
}

// main.ts
async function bootstrap() {
  const app = await NestFactory.create(AppModule, {
    logger: new PinoLoggerService(),
  });
}

// Using nestjs-pino package
import { LoggerModule } from 'nestjs-pino';

@Module({
  imports: [
    LoggerModule.forRoot({
      pinoHttp: {
        level: process.env.LOG_LEVEL || 'info',
        redact: ['req.headers.authorization'],
        transport:
          process.env.NODE_ENV !== 'production'
            ? {
                target: 'pino-pretty',
                options: { colorize: true },
              }
            : undefined,
      },
    }),
  ],
})
export class AppModule {}
```

## Python Structured Logging

```python
# logger.py
import structlog
import logging

# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Usage
logger.info("user_logged_in", user_id="123", ip="192.168.1.100")
# Output: {"event": "user_logged_in", "user_id": "123", "ip": "192.168.1.100", "timestamp": "2024-01-15T10:30:45.123456Z", "level": "info"}

# With context binding
log = logger.bind(request_id="req-123")
log.info("processing_started")
log.info("processing_completed", duration_ms=150)
```

```python
# FastAPI integration
from fastapi import FastAPI, Request
import structlog
import uuid

app = FastAPI()

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))

    log = structlog.get_logger().bind(
        request_id=request_id,
        method=request.method,
        path=request.url.path
    )

    request.state.log = log
    log.info("request_started")

    response = await call_next(request)

    log.info("request_completed", status_code=response.status_code)
    response.headers["x-request-id"] = request_id

    return response

@app.get("/users/{user_id}")
async def get_user(user_id: str, request: Request):
    request.state.log.info("fetching_user", user_id=user_id)
    return {"user_id": user_id}
```

## Standard Log Schema

```typescript
// Consistent log schema
interface LogEntry {
  // Required fields
  timestamp: string; // ISO 8601 format
  level: 'trace' | 'debug' | 'info' | 'warn' | 'error' | 'fatal';
  message: string;

  // Service identification
  service: string;
  version: string;
  environment: string;
  host: string;

  // Request context (when applicable)
  correlationId?: string;
  requestId?: string;
  userId?: string;
  sessionId?: string;

  // HTTP context (when applicable)
  http?: {
    method: string;
    path: string;
    statusCode: number;
    duration: number;
    userAgent?: string;
    ip?: string;
  };

  // Error context (when applicable)
  error?: {
    name: string;
    message: string;
    stack: string;
    code?: string;
  };

  // Additional context
  [key: string]: unknown;
}

// Example output
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "info",
  "message": "Request completed",
  "service": "api-gateway",
  "version": "1.2.3",
  "environment": "production",
  "host": "api-gateway-abc123",
  "correlationId": "corr-123-456",
  "requestId": "req-789",
  "userId": "user-456",
  "http": {
    "method": "POST",
    "path": "/api/orders",
    "statusCode": 201,
    "duration": 145,
    "ip": "192.168.1.100"
  }
}
```

## Log Enrichment

```typescript
// Auto-enrichment with common fields
function createEnrichedLogger(baseLogger: pino.Logger) {
  return baseLogger.child({
    // Service info
    service: process.env.SERVICE_NAME,
    version: process.env.npm_package_version,
    environment: process.env.NODE_ENV,

    // Infrastructure info
    host: os.hostname(),
    pid: process.pid,

    // Kubernetes info (if available)
    k8s: {
      namespace: process.env.K8S_NAMESPACE,
      pod: process.env.K8S_POD_NAME,
      node: process.env.K8S_NODE_NAME,
    },
  });
}

// Request enrichment middleware
function enrichRequestLogger(req, res, next) {
  req.log = req.log.child({
    // Request identification
    requestId: req.headers['x-request-id'] || uuid(),
    correlationId: req.headers['x-correlation-id'] || uuid(),

    // User context
    userId: req.user?.id,
    tenantId: req.user?.tenantId,

    // Request details
    http: {
      method: req.method,
      path: req.path,
      query: req.query,
      userAgent: req.headers['user-agent'],
      ip: req.ip,
    },
  });

  next();
}
```

## Sensitive Data Handling

```typescript
// Redaction configuration
const logger = pino({
  redact: {
    paths: [
      'password',
      'req.headers.authorization',
      'req.body.password',
      'req.body.creditCard',
      'req.body.ssn',
      '*.apiKey',
      '*.secret',
    ],
    censor: '[REDACTED]',
  },
});

// Custom redaction function
function redactSensitive(obj: any): any {
  const sensitiveFields = ['password', 'creditCard', 'ssn', 'apiKey'];

  if (typeof obj !== 'object' || obj === null) {
    return obj;
  }

  const result = Array.isArray(obj) ? [] : {};

  for (const [key, value] of Object.entries(obj)) {
    if (sensitiveFields.includes(key)) {
      result[key] = '[REDACTED]';
    } else if (typeof value === 'object') {
      result[key] = redactSensitive(value);
    } else {
      result[key] = value;
    }
  }

  return result;
}

// Email masking
function maskEmail(email: string): string {
  const [local, domain] = email.split('@');
  const masked = local.substring(0, 2) + '***';
  return `${masked}@${domain}`;
}
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│              Structured Logging Best Practices                   │
├─────────────────────────────────────────────────────────────────┤
│ ☐ Use JSON format for all production logs                       │
│ ☐ Define a consistent schema across services                    │
│ ☐ Include timestamp in ISO 8601 format                          │
│ ☐ Use child loggers for context propagation                     │
│ ☐ Implement automatic field redaction                           │
│ ☐ Add service identification fields                             │
│ ☐ Include correlation IDs                                       │
│ ☐ Use appropriate log levels                                    │
│ ☐ Enable pretty printing in development only                    │
│ ☐ Configure log rotation and retention                          │
│ ☐ Validate log format in CI/CD                                  │
│ ☐ Document your logging schema                                  │
└─────────────────────────────────────────────────────────────────┘
```
