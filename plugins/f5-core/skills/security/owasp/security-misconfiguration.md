---
name: security-misconfiguration
description: Preventing security misconfiguration vulnerabilities
category: security/owasp
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Security Misconfiguration

## Overview

Security misconfiguration is one of the most common vulnerabilities,
often resulting from insecure default settings, incomplete
configurations, or exposed error messages.

## Common Misconfigurations

| Category | Risk | Impact |
|----------|------|--------|
| Default credentials | Critical | Full system compromise |
| Verbose errors | High | Information disclosure |
| Debug mode in production | High | Code/data exposure |
| Unnecessary features | Medium | Increased attack surface |
| Missing security headers | Medium | Various attacks |
| Outdated software | High | Known vulnerabilities |

## Secure Configuration Practices

### Environment Configuration

```typescript
// config/environment.ts
import { z } from 'zod';

const envSchema = z.object({
  NODE_ENV: z.enum(['development', 'test', 'staging', 'production']),
  PORT: z.string().transform(Number),

  // Database
  DATABASE_URL: z.string().url(),

  // Security
  JWT_SECRET: z.string().min(64),
  SESSION_SECRET: z.string().min(32),

  // Feature flags
  DEBUG_MODE: z.string().transform(val => val === 'true').default('false'),
  ENABLE_SWAGGER: z.string().transform(val => val === 'true').default('false'),
});

// Validate environment variables at startup
function validateEnv() {
  const result = envSchema.safeParse(process.env);

  if (!result.success) {
    console.error('Invalid environment variables:', result.error.format());
    process.exit(1);
  }

  // Enforce production settings
  if (result.data.NODE_ENV === 'production') {
    if (result.data.DEBUG_MODE) {
      console.error('DEBUG_MODE must be false in production');
      process.exit(1);
    }
    if (result.data.ENABLE_SWAGGER) {
      console.warn('Warning: Swagger enabled in production');
    }
  }

  return result.data;
}

export const env = validateEnv();
```

### Production Checklist

```typescript
// startup/production-checks.ts
export async function runProductionChecks() {
  const checks: Check[] = [
    {
      name: 'NODE_ENV is production',
      check: () => process.env.NODE_ENV === 'production',
      critical: true,
    },
    {
      name: 'Debug mode disabled',
      check: () => !process.env.DEBUG_MODE,
      critical: true,
    },
    {
      name: 'HTTPS enforced',
      check: () => !!process.env.FORCE_HTTPS,
      critical: true,
    },
    {
      name: 'Strong secrets configured',
      check: () => {
        const jwtSecret = process.env.JWT_SECRET || '';
        return jwtSecret.length >= 64;
      },
      critical: true,
    },
    {
      name: 'Default admin password changed',
      check: async () => {
        const admin = await userRepo.findByEmail('admin@example.com');
        if (!admin) return true;
        // Check if using default password
        return !await bcrypt.compare('admin', admin.passwordHash);
      },
      critical: true,
    },
    {
      name: 'Database credentials not default',
      check: () => {
        const dbUrl = process.env.DATABASE_URL || '';
        return !dbUrl.includes('postgres:postgres');
      },
      critical: true,
    },
    {
      name: 'Rate limiting enabled',
      check: () => !!process.env.RATE_LIMIT_ENABLED,
      critical: false,
    },
    {
      name: 'Security headers middleware active',
      check: () => !!global.helmetEnabled,
      critical: false,
    },
  ];

  const results = await Promise.all(
    checks.map(async c => ({
      name: c.name,
      passed: await c.check(),
      critical: c.critical,
    }))
  );

  const failed = results.filter(r => !r.passed);
  const criticalFailed = failed.filter(r => r.critical);

  if (criticalFailed.length > 0) {
    console.error('Critical security checks failed:');
    criticalFailed.forEach(r => console.error(`  ❌ ${r.name}`));
    process.exit(1);
  }

  if (failed.length > 0) {
    console.warn('Security warnings:');
    failed.forEach(r => console.warn(`  ⚠️ ${r.name}`));
  }

  console.log('✅ All critical security checks passed');
}
```

### Error Handling

```typescript
// middleware/error.middleware.ts
export function errorMiddleware() {
  return (err: Error, req: Request, res: Response, next: NextFunction) => {
    // Log full error internally
    console.error('Error:', {
      message: err.message,
      stack: err.stack,
      url: req.url,
      method: req.method,
      userId: req.user?.id,
    });

    // Determine error response
    const isProduction = process.env.NODE_ENV === 'production';

    if (err instanceof ValidationError) {
      return res.status(400).json({
        error: 'Validation Error',
        details: err.details, // Safe to expose
      });
    }

    if (err instanceof UnauthorizedError) {
      return res.status(401).json({
        error: 'Unauthorized',
      });
    }

    if (err instanceof ForbiddenError) {
      return res.status(403).json({
        error: 'Forbidden',
      });
    }

    if (err instanceof NotFoundError) {
      return res.status(404).json({
        error: 'Not Found',
      });
    }

    // Generic error - hide details in production
    return res.status(500).json({
      error: 'Internal Server Error',
      ...(isProduction
        ? {} // No details in production
        : {
            message: err.message,
            stack: err.stack,
          }),
      requestId: req.requestId, // For support reference
    });
  };
}
```

### Secure Headers

```typescript
// middleware/security-headers.middleware.ts
import helmet from 'helmet';

export function securityHeaders() {
  return helmet({
    // Content Security Policy
    contentSecurityPolicy: {
      directives: {
        defaultSrc: ["'self'"],
        scriptSrc: ["'self'"],
        styleSrc: ["'self'", "'unsafe-inline'"],
        imgSrc: ["'self'", "data:", "https:"],
        connectSrc: ["'self'"],
        fontSrc: ["'self'"],
        objectSrc: ["'none'"],
        mediaSrc: ["'self'"],
        frameSrc: ["'none'"],
      },
    },

    // Strict Transport Security
    hsts: {
      maxAge: 31536000,
      includeSubDomains: true,
      preload: true,
    },

    // Prevent clickjacking
    frameguard: { action: 'deny' },

    // Hide server info
    hidePoweredBy: true,

    // Prevent MIME sniffing
    noSniff: true,

    // XSS filter
    xssFilter: true,

    // Referrer policy
    referrerPolicy: { policy: 'strict-origin-when-cross-origin' },

    // Permissions Policy
    permittedCrossDomainPolicies: { permittedPolicies: 'none' },
  });
}

// Additional custom headers
export function additionalSecurityHeaders() {
  return (req: Request, res: Response, next: NextFunction) => {
    // Permissions Policy
    res.setHeader(
      'Permissions-Policy',
      'accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()'
    );

    // Cross-Origin headers
    res.setHeader('Cross-Origin-Opener-Policy', 'same-origin');
    res.setHeader('Cross-Origin-Embedder-Policy', 'require-corp');
    res.setHeader('Cross-Origin-Resource-Policy', 'same-origin');

    // Remove fingerprinting headers
    res.removeHeader('X-Powered-By');
    res.removeHeader('Server');

    next();
  };
}
```

### Feature Flags

```typescript
// config/features.ts
const featureFlags = {
  development: {
    swagger: true,
    debugEndpoints: true,
    verboseErrors: true,
    mockAuth: true,
    seedData: true,
  },
  test: {
    swagger: true,
    debugEndpoints: true,
    verboseErrors: true,
    mockAuth: true,
    seedData: true,
  },
  staging: {
    swagger: true,
    debugEndpoints: false,
    verboseErrors: false,
    mockAuth: false,
    seedData: false,
  },
  production: {
    swagger: false,
    debugEndpoints: false,
    verboseErrors: false,
    mockAuth: false,
    seedData: false,
  },
};

export function getFeatureFlags() {
  const env = process.env.NODE_ENV || 'development';
  return featureFlags[env] || featureFlags.production;
}

// Usage
const features = getFeatureFlags();

if (features.swagger) {
  app.use('/api-docs', swaggerUI.serve, swaggerUI.setup(swaggerSpec));
}

if (features.debugEndpoints) {
  app.use('/debug', debugRouter);
}
```

### Disable Unnecessary Features

```typescript
// app.ts
import express from 'express';

const app = express();

// Disable x-powered-by header
app.disable('x-powered-by');

// Disable detailed error pages
app.set('env', 'production');

// Enable trust proxy if behind reverse proxy
if (process.env.TRUST_PROXY) {
  app.set('trust proxy', 1);
}

// Disable etag if not needed
app.disable('etag');

// Remove unused middleware
// Don't add: app.use(express.urlencoded({ extended: true }))
// unless you need form parsing
```

### Database Security

```typescript
// config/database.ts
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient({
  log: process.env.NODE_ENV === 'production'
    ? ['error', 'warn']
    : ['query', 'error', 'warn'],

  // Don't expose query errors in production
  errorFormat: process.env.NODE_ENV === 'production'
    ? 'minimal'
    : 'pretty',
});

// Database connection string validation
function validateDatabaseUrl(url: string): void {
  // Check for default credentials
  const patterns = [
    /postgres:postgres/,
    /root:root/,
    /admin:admin/,
    /password/i,
  ];

  for (const pattern of patterns) {
    if (pattern.test(url)) {
      throw new Error('Database URL contains default/weak credentials');
    }
  }

  // Check for SSL requirement in production
  if (process.env.NODE_ENV === 'production') {
    if (!url.includes('sslmode=require') && !url.includes('ssl=true')) {
      console.warn('Warning: Database connection should use SSL in production');
    }
  }
}
```

### Secrets Management

```typescript
// config/secrets.ts
import { SecretManagerServiceClient } from '@google-cloud/secret-manager';

// Use secret manager in production
async function getSecret(name: string): Promise<string> {
  if (process.env.NODE_ENV !== 'production') {
    // Use .env in development
    return process.env[name] || '';
  }

  const client = new SecretManagerServiceClient();
  const projectId = process.env.GCP_PROJECT_ID;

  const [version] = await client.accessSecretVersion({
    name: `projects/${projectId}/secrets/${name}/versions/latest`,
  });

  return version.payload?.data?.toString() || '';
}

// Validate secrets are not hardcoded
function validateSecrets(): void {
  const suspiciousPatterns = [
    /password/i,
    /secret/i,
    /api.?key/i,
    /token/i,
  ];

  // Check for hardcoded secrets in environment
  for (const [key, value] of Object.entries(process.env)) {
    if (suspiciousPatterns.some(p => p.test(key))) {
      // Check if value looks like a default
      if (value && (value.length < 16 || /^(test|dev|local)/i.test(value))) {
        console.warn(`Warning: ${key} may contain a weak or default value`);
      }
    }
  }
}
```

## Configuration Audit

```typescript
// scripts/security-audit.ts
async function auditConfiguration() {
  const findings: Finding[] = [];

  // Check environment
  if (process.env.NODE_ENV !== 'production') {
    findings.push({
      severity: 'high',
      category: 'Environment',
      message: 'NODE_ENV is not set to production',
    });
  }

  // Check for debug mode
  if (process.env.DEBUG || process.env.DEBUG_MODE) {
    findings.push({
      severity: 'high',
      category: 'Debug',
      message: 'Debug mode is enabled',
    });
  }

  // Check security headers
  const response = await fetch('http://localhost:3000/');
  const headers = response.headers;

  const requiredHeaders = [
    'strict-transport-security',
    'x-content-type-options',
    'x-frame-options',
    'content-security-policy',
  ];

  for (const header of requiredHeaders) {
    if (!headers.has(header)) {
      findings.push({
        severity: 'medium',
        category: 'Headers',
        message: `Missing security header: ${header}`,
      });
    }
  }

  // Report findings
  console.log('Security Audit Results:');
  console.log('='.repeat(50));

  if (findings.length === 0) {
    console.log('✅ No security issues found');
  } else {
    findings.forEach(f => {
      const icon = f.severity === 'high' ? '🔴' : f.severity === 'medium' ? '🟡' : '🟢';
      console.log(`${icon} [${f.severity.toUpperCase()}] ${f.category}: ${f.message}`);
    });
  }
}
```

## Best Practices

| Practice | Description |
|----------|-------------|
| Validate config | Validate all environment variables at startup |
| Disable debug | Never enable debug mode in production |
| Remove defaults | Change all default passwords/settings |
| Minimize features | Disable unnecessary features and endpoints |
| Security headers | Enable all security headers |
| Error handling | Never expose stack traces in production |
