---
name: csrf-prevention
description: Cross-Site Request Forgery prevention
category: security/owasp
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# CSRF Prevention

## Overview

Cross-Site Request Forgery (CSRF) tricks users into performing
unintended actions on websites where they're authenticated.

## Attack Scenario

```
┌────────────────────────────────────────────────────────────┐
│                    CSRF Attack Flow                        │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  1. User logs into bank.com (session cookie set)           │
│                                                            │
│  2. User visits evil.com (while still logged in)           │
│                                                            │
│  3. evil.com contains:                                     │
│     <img src="bank.com/transfer?to=attacker&amount=1000">  │
│                                                            │
│  4. Browser sends request WITH user's bank.com cookies     │
│                                                            │
│  5. Bank processes the malicious transfer                  │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

## CSRF Token Implementation

### Token Generation and Validation

```typescript
// services/csrf.service.ts
import crypto from 'crypto';

export class CSRFService {
  private readonly TOKEN_LENGTH = 32;
  private readonly TOKEN_EXPIRY = 60 * 60 * 1000; // 1 hour

  constructor(private redis: Redis) {}

  async generateToken(sessionId: string): Promise<string> {
    const token = crypto.randomBytes(this.TOKEN_LENGTH).toString('hex');

    await this.redis.setex(
      `csrf:${sessionId}:${token}`,
      this.TOKEN_EXPIRY / 1000,
      'valid'
    );

    return token;
  }

  async validateToken(sessionId: string, token: string): Promise<boolean> {
    if (!token || !sessionId) {
      return false;
    }

    const key = `csrf:${sessionId}:${token}`;
    const exists = await this.redis.get(key);

    if (!exists) {
      return false;
    }

    // Optional: Single-use tokens (delete after use)
    // await this.redis.del(key);

    return true;
  }

  async rotateToken(sessionId: string, oldToken: string): Promise<string> {
    // Invalidate old token
    await this.redis.del(`csrf:${sessionId}:${oldToken}`);

    // Generate new token
    return this.generateToken(sessionId);
  }
}
```

### Middleware Implementation

```typescript
// middleware/csrf.middleware.ts
export function csrfMiddleware(csrfService: CSRFService) {
  return async (req: Request, res: Response, next: NextFunction) => {
    // Skip for safe methods
    if (['GET', 'HEAD', 'OPTIONS'].includes(req.method)) {
      return next();
    }

    const sessionId = req.session?.id;
    if (!sessionId) {
      return res.status(403).json({ error: 'Session required' });
    }

    // Get token from header or body
    const token =
      req.headers['x-csrf-token'] ||
      req.body?._csrf ||
      req.query?._csrf;

    const isValid = await csrfService.validateToken(sessionId, token);

    if (!isValid) {
      return res.status(403).json({ error: 'Invalid CSRF token' });
    }

    next();
  };
}

// Middleware to inject new token
export function csrfTokenMiddleware(csrfService: CSRFService) {
  return async (req: Request, res: Response, next: NextFunction) => {
    if (req.session?.id) {
      const token = await csrfService.generateToken(req.session.id);
      res.locals.csrfToken = token;

      // Also set as cookie for SPA
      res.cookie('XSRF-TOKEN', token, {
        httpOnly: false, // Must be readable by JS
        secure: true,
        sameSite: 'strict',
      });
    }
    next();
  };
}
```

### Usage with Express

```typescript
import csurf from 'csurf';

// Using csurf package (simpler)
const csrfProtection = csurf({
  cookie: {
    httpOnly: true,
    secure: true,
    sameSite: 'strict',
  },
});

app.use(csrfProtection);

// Error handler for CSRF
app.use((err, req, res, next) => {
  if (err.code === 'EBADCSRFTOKEN') {
    return res.status(403).json({ error: 'Invalid CSRF token' });
  }
  next(err);
});

// Inject token into templates
app.use((req, res, next) => {
  res.locals.csrfToken = req.csrfToken();
  next();
});
```

### Form Implementation

```html
<!-- Server-rendered form -->
<form method="POST" action="/transfer">
  <input type="hidden" name="_csrf" value="<%= csrfToken %>">
  <input type="text" name="amount">
  <input type="text" name="recipient">
  <button type="submit">Transfer</button>
</form>
```

### Frontend (SPA) Implementation

```typescript
// React/Vue/Angular - read from cookie, send in header

// Axios interceptor
import axios from 'axios';

axios.interceptors.request.use(config => {
  // Read token from cookie
  const token = document.cookie
    .split('; ')
    .find(row => row.startsWith('XSRF-TOKEN='))
    ?.split('=')[1];

  if (token) {
    config.headers['X-CSRF-Token'] = token;
  }

  return config;
});

// Fetch wrapper
async function secureFetch(url: string, options: RequestInit = {}) {
  const token = getCookie('XSRF-TOKEN');

  return fetch(url, {
    ...options,
    credentials: 'include',
    headers: {
      ...options.headers,
      'X-CSRF-Token': token || '',
    },
  });
}

function getCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
  return match ? match[2] : null;
}
```

## SameSite Cookies

```typescript
// SameSite cookie configuration
res.cookie('sessionId', session.id, {
  httpOnly: true,
  secure: true,
  sameSite: 'strict', // or 'lax'
  maxAge: 24 * 60 * 60 * 1000,
});

// SameSite values:
// - 'strict': Cookie never sent cross-site
// - 'lax': Cookie sent for top-level navigation (default in modern browsers)
// - 'none': Cookie sent cross-site (requires Secure)
```

### SameSite Considerations

| Value | Behavior | Use Case |
|-------|----------|----------|
| `strict` | Never sent cross-site | Maximum security |
| `lax` | Sent on top-level navigation | Balance security/usability |
| `none` | Always sent (with Secure) | Cross-site use cases |

## Double Submit Cookie

```typescript
// Alternative pattern: Double Submit Cookie
// No server-side token storage needed

export class DoubleSubmitCSRF {
  async generateToken(): Promise<string> {
    return crypto.randomBytes(32).toString('hex');
  }

  validateDoubleSubmit(
    cookieToken: string,
    headerToken: string
  ): boolean {
    if (!cookieToken || !headerToken) {
      return false;
    }

    // Timing-safe comparison
    return crypto.timingSafeEqual(
      Buffer.from(cookieToken),
      Buffer.from(headerToken)
    );
  }
}

// Middleware
app.use((req, res, next) => {
  // Skip safe methods
  if (['GET', 'HEAD', 'OPTIONS'].includes(req.method)) {
    return next();
  }

  const cookieToken = req.cookies['csrf-token'];
  const headerToken = req.headers['x-csrf-token'];

  if (!doubleSubmitCSRF.validateDoubleSubmit(cookieToken, headerToken)) {
    return res.status(403).json({ error: 'CSRF validation failed' });
  }

  next();
});
```

## Origin/Referer Validation

```typescript
// Additional layer of CSRF protection
export function originValidation(allowedOrigins: string[]) {
  return (req: Request, res: Response, next: NextFunction) => {
    // Skip safe methods
    if (['GET', 'HEAD', 'OPTIONS'].includes(req.method)) {
      return next();
    }

    const origin = req.headers.origin;
    const referer = req.headers.referer;

    // Check Origin header first (most reliable)
    if (origin) {
      if (!allowedOrigins.includes(origin)) {
        return res.status(403).json({ error: 'Invalid origin' });
      }
      return next();
    }

    // Fall back to Referer header
    if (referer) {
      try {
        const refererUrl = new URL(referer);
        if (!allowedOrigins.includes(refererUrl.origin)) {
          return res.status(403).json({ error: 'Invalid referer' });
        }
        return next();
      } catch {
        return res.status(403).json({ error: 'Invalid referer' });
      }
    }

    // No origin or referer - might be direct access
    // Decide based on security requirements
    // Option 1: Block (more secure)
    return res.status(403).json({ error: 'Origin validation failed' });

    // Option 2: Allow (more permissive)
    // return next();
  };
}

// Usage
app.use(originValidation([
  'https://myapp.com',
  'https://www.myapp.com',
  process.env.NODE_ENV === 'development' ? 'http://localhost:3000' : '',
].filter(Boolean)));
```

## Custom Header Validation

```typescript
// APIs can use custom header requirement
// Browsers don't send custom headers cross-origin without CORS preflight

export function customHeaderValidation(headerName: string) {
  return (req: Request, res: Response, next: NextFunction) => {
    // Skip safe methods
    if (['GET', 'HEAD', 'OPTIONS'].includes(req.method)) {
      return next();
    }

    // Require custom header
    if (!req.headers[headerName.toLowerCase()]) {
      return res.status(403).json({
        error: `Missing required header: ${headerName}`,
      });
    }

    next();
  };
}

// Usage
app.use('/api', customHeaderValidation('X-Requested-With'));

// Client must send:
// fetch('/api/action', {
//   method: 'POST',
//   headers: {
//     'X-Requested-With': 'XMLHttpRequest',
//   },
// });
```

## Framework-Specific Solutions

### NestJS

```typescript
// Using csurf with NestJS
import * as csurf from 'csurf';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  app.use(csurf({
    cookie: {
      httpOnly: true,
      secure: true,
      sameSite: 'strict',
    },
  }));

  await app.listen(3000);
}

// Guard
@Injectable()
export class CsrfGuard implements CanActivate {
  canActivate(context: ExecutionContext): boolean {
    const request = context.switchToHttp().getRequest();

    // csurf validates automatically, this just ensures it ran
    return !!request.csrfToken;
  }
}
```

### Next.js

```typescript
// pages/api/transfer.ts
import { NextApiRequest, NextApiResponse } from 'next';
import Csrf from 'csrf';

const csrf = new Csrf();

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'POST') {
    return res.status(405).end();
  }

  const secret = req.cookies['csrf-secret'];
  const token = req.headers['x-csrf-token'] as string;

  if (!csrf.verify(secret, token)) {
    return res.status(403).json({ error: 'Invalid CSRF token' });
  }

  // Process request
}
```

## Best Practices

| Practice | Description |
|----------|-------------|
| SameSite cookies | Use Strict or Lax for session cookies |
| CSRF tokens | Synchronizer tokens for forms |
| Origin validation | Check Origin/Referer headers |
| Custom headers | Require for API requests |
| Secure cookies | Always use Secure flag |
| Token rotation | Rotate tokens periodically |
