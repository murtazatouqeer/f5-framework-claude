---
name: session-management
description: Secure session management patterns
category: security/authentication
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Session Management

## Overview

Sessions maintain user state across HTTP requests. Secure session
management is critical for preventing unauthorized access.

## Session Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Session Flow                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Client                     Server                          │
│    │                          │                             │
│    │ 1. Login Request         │                             │
│    │ ────────────────────────>│                             │
│    │                          │                             │
│    │ 2. Set-Cookie: sessionId │                             │
│    │ <────────────────────────│                             │
│    │                          │                             │
│    │ 3. Request + Cookie      │                             │
│    │ ────────────────────────>│                             │
│    │                          │                             │
│    │ 4. Lookup session        │ ────> Session Store         │
│    │                          │ <────                       │
│    │                          │                             │
│    │ 5. Response              │                             │
│    │ <────────────────────────│                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Implementation

### Session Service

```typescript
// services/session.service.ts
import crypto from 'crypto';
import { Redis } from 'ioredis';

interface Session {
  id: string;
  userId: string;
  data: Record<string, any>;
  createdAt: number;
  lastAccessedAt: number;
  expiresAt: number;
  userAgent: string;
  ipAddress: string;
}

export class SessionService {
  private readonly SESSION_PREFIX = 'session:';
  private readonly USER_SESSIONS_PREFIX = 'user_sessions:';
  private readonly DEFAULT_TTL = 24 * 60 * 60; // 24 hours
  private readonly MAX_SESSIONS_PER_USER = 5;

  constructor(private redis: Redis) {}

  async create(
    userId: string,
    data: Record<string, any>,
    options: { userAgent: string; ipAddress: string }
  ): Promise<Session> {
    // Generate secure session ID
    const sessionId = this.generateSessionId();
    const now = Date.now();

    const session: Session = {
      id: sessionId,
      userId,
      data,
      createdAt: now,
      lastAccessedAt: now,
      expiresAt: now + this.DEFAULT_TTL * 1000,
      userAgent: options.userAgent,
      ipAddress: options.ipAddress,
    };

    // Store session
    await this.redis.setex(
      `${this.SESSION_PREFIX}${sessionId}`,
      this.DEFAULT_TTL,
      JSON.stringify(session)
    );

    // Track user sessions
    await this.redis.sadd(`${this.USER_SESSIONS_PREFIX}${userId}`, sessionId);

    // Enforce max sessions
    await this.enforceMaxSessions(userId);

    return session;
  }

  async get(sessionId: string): Promise<Session | null> {
    const data = await this.redis.get(`${this.SESSION_PREFIX}${sessionId}`);
    if (!data) return null;

    const session = JSON.parse(data) as Session;

    // Check expiration
    if (session.expiresAt < Date.now()) {
      await this.destroy(sessionId);
      return null;
    }

    // Update last accessed (sliding expiration)
    session.lastAccessedAt = Date.now();
    session.expiresAt = Date.now() + this.DEFAULT_TTL * 1000;

    await this.redis.setex(
      `${this.SESSION_PREFIX}${sessionId}`,
      this.DEFAULT_TTL,
      JSON.stringify(session)
    );

    return session;
  }

  async destroy(sessionId: string): Promise<void> {
    const session = await this.get(sessionId);
    if (session) {
      await this.redis.del(`${this.SESSION_PREFIX}${sessionId}`);
      await this.redis.srem(`${this.USER_SESSIONS_PREFIX}${session.userId}`, sessionId);
    }
  }

  async destroyAllUserSessions(userId: string): Promise<number> {
    const sessionIds = await this.redis.smembers(`${this.USER_SESSIONS_PREFIX}${userId}`);

    if (sessionIds.length === 0) return 0;

    // Delete all sessions
    const sessionKeys = sessionIds.map(id => `${this.SESSION_PREFIX}${id}`);
    await this.redis.del(...sessionKeys);

    // Clear user sessions set
    await this.redis.del(`${this.USER_SESSIONS_PREFIX}${userId}`);

    return sessionIds.length;
  }

  async getUserSessions(userId: string): Promise<Session[]> {
    const sessionIds = await this.redis.smembers(`${this.USER_SESSIONS_PREFIX}${userId}`);
    const sessions: Session[] = [];

    for (const id of sessionIds) {
      const session = await this.get(id);
      if (session) {
        sessions.push(session);
      }
    }

    return sessions.sort((a, b) => b.lastAccessedAt - a.lastAccessedAt);
  }

  private generateSessionId(): string {
    return crypto.randomBytes(32).toString('hex');
  }

  private async enforceMaxSessions(userId: string): Promise<void> {
    const sessions = await this.getUserSessions(userId);

    if (sessions.length > this.MAX_SESSIONS_PER_USER) {
      // Remove oldest sessions
      const toRemove = sessions.slice(this.MAX_SESSIONS_PER_USER);
      for (const session of toRemove) {
        await this.destroy(session.id);
      }
    }
  }
}
```

### Session Middleware

```typescript
// middleware/session.middleware.ts
export function sessionMiddleware(sessionService: SessionService) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const sessionId = req.cookies.sessionId;

    if (!sessionId) {
      return next();
    }

    try {
      const session = await sessionService.get(sessionId);

      if (session) {
        req.session = session;
        req.user = { id: session.userId, ...session.data };
      }

      next();
    } catch (error) {
      next(error);
    }
  };
}

// Require authentication middleware
export function requireAuth(req: Request, res: Response, next: NextFunction) {
  if (!req.session) {
    return res.status(401).json({ error: 'Authentication required' });
  }
  next();
}
```

### Cookie Configuration

```typescript
// config/cookie.config.ts
export const cookieConfig = {
  httpOnly: true,        // Not accessible via JavaScript
  secure: true,          // HTTPS only in production
  sameSite: 'lax' as const, // CSRF protection
  maxAge: 24 * 60 * 60 * 1000, // 24 hours
  path: '/',
  domain: process.env.COOKIE_DOMAIN,
};

// Set session cookie
res.cookie('sessionId', session.id, cookieConfig);

// Clear session cookie
res.clearCookie('sessionId', {
  httpOnly: true,
  secure: true,
  sameSite: 'lax',
  path: '/',
});
```

## Session Security

### Session Fixation Prevention

```typescript
// Regenerate session after authentication
async function login(req: Request, res: Response) {
  const user = await authenticate(req.body);

  // Destroy old session if exists
  if (req.session) {
    await sessionService.destroy(req.session.id);
  }

  // Create new session
  const newSession = await sessionService.create(user.id, {
    roles: user.roles,
  }, {
    userAgent: req.headers['user-agent'] || '',
    ipAddress: req.ip,
  });

  res.cookie('sessionId', newSession.id, cookieConfig);
  res.json({ user });
}
```

### Session Hijacking Prevention

```typescript
// Bind session to client characteristics
interface SessionBinding {
  userAgent: string;
  ipAddress: string;
  fingerprint?: string;
}

async function validateSessionBinding(
  session: Session,
  current: SessionBinding
): Promise<boolean> {
  // Strict validation (may cause issues with mobile networks)
  if (session.ipAddress !== current.ipAddress) {
    console.warn('IP address mismatch', {
      sessionId: session.id,
      expected: session.ipAddress,
      actual: current.ipAddress,
    });
    // Depending on security requirements:
    // return false; // Strict
    // Or just log warning
  }

  if (session.userAgent !== current.userAgent) {
    console.warn('User agent mismatch', { sessionId: session.id });
    return false; // Usually indicates hijacking
  }

  return true;
}
```

### Absolute vs Sliding Expiration

```typescript
// Sliding expiration (extends on activity)
async function touchSession(session: Session): Promise<void> {
  session.lastAccessedAt = Date.now();
  session.expiresAt = Date.now() + SLIDING_TTL;
  await saveSession(session);
}

// Absolute expiration (fixed lifetime)
const ABSOLUTE_TTL = 8 * 60 * 60 * 1000; // 8 hours max

function isSessionValid(session: Session): boolean {
  const now = Date.now();

  // Check absolute expiration
  if (now - session.createdAt > ABSOLUTE_TTL) {
    return false;
  }

  // Check sliding expiration
  if (now > session.expiresAt) {
    return false;
  }

  return true;
}
```

## Active Session Management

### List User Sessions

```typescript
// routes/session.routes.ts
router.get('/sessions', requireAuth, async (req, res) => {
  const sessions = await sessionService.getUserSessions(req.user.id);

  // Mask current session, highlight active
  const formattedSessions = sessions.map(s => ({
    id: s.id,
    isCurrent: s.id === req.session.id,
    userAgent: s.userAgent,
    ipAddress: s.ipAddress.substring(0, s.ipAddress.lastIndexOf('.') + 1) + 'xxx',
    createdAt: s.createdAt,
    lastAccessedAt: s.lastAccessedAt,
  }));

  res.json({ sessions: formattedSessions });
});

// Revoke specific session
router.delete('/sessions/:sessionId', requireAuth, async (req, res) => {
  const { sessionId } = req.params;

  // Prevent revoking current session via this endpoint
  if (sessionId === req.session.id) {
    return res.status(400).json({ error: 'Use logout to end current session' });
  }

  // Verify session belongs to user
  const session = await sessionService.get(sessionId);
  if (!session || session.userId !== req.user.id) {
    return res.status(404).json({ error: 'Session not found' });
  }

  await sessionService.destroy(sessionId);
  res.status(204).end();
});

// Revoke all other sessions
router.delete('/sessions', requireAuth, async (req, res) => {
  const sessions = await sessionService.getUserSessions(req.user.id);

  for (const session of sessions) {
    if (session.id !== req.session.id) {
      await sessionService.destroy(session.id);
    }
  }

  res.json({ message: 'All other sessions revoked' });
});
```

## Best Practices

| Practice | Description |
|----------|-------------|
| Secure ID generation | Use crypto.randomBytes(32) minimum |
| HttpOnly cookies | Prevent XSS from stealing sessions |
| Secure flag | Cookies only sent over HTTPS |
| SameSite attribute | Protect against CSRF |
| Session timeout | Both idle and absolute timeouts |
| Regenerate on auth | Prevent session fixation |
| Limit sessions | Max sessions per user |
| Audit logging | Log session creation/destruction |
