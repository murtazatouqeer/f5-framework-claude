---
name: versioning
description: REST API versioning strategies
category: api-design/rest
applies_to: [all]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# API Versioning

## Overview

API versioning allows you to introduce breaking changes without disrupting
existing clients. Choose a strategy based on your needs and stick with it.

## Versioning Strategies

```
┌─────────────────────────────────────────────────────────────────┐
│                   Versioning Strategy Comparison                 │
├────────────────────┬────────────────────────────────────────────┤
│ Strategy           │ Format                                      │
├────────────────────┼────────────────────────────────────────────┤
│ URL Path           │ /api/v1/users                               │
│ Query Parameter    │ /api/users?version=1                        │
│ Header             │ X-API-Version: 1                            │
│ Accept Header      │ Accept: application/vnd.api.v1+json        │
│ Content-Type       │ Content-Type: application/vnd.api.v1+json  │
└────────────────────┴────────────────────────────────────────────┘
```

## URL Path Versioning

The most common and visible approach.

```http
# Version in URL path
GET /api/v1/users HTTP/1.1
GET /api/v2/users HTTP/1.1

# With resource version
GET /v1/users HTTP/1.1
GET /v2/users HTTP/1.1
```

### Pros and Cons

```
✅ Pros:
  - Easy to understand and implement
  - Visible in browser/logs
  - Easy caching
  - Simple routing

❌ Cons:
  - Not truly RESTful (URI should identify resource)
  - URL pollution
  - Harder to deprecate gracefully
```

### Implementation

```typescript
// Express.js routing
import express from 'express';
import v1Router from './routes/v1';
import v2Router from './routes/v2';

const app = express();

// Mount versioned routers
app.use('/api/v1', v1Router);
app.use('/api/v2', v2Router);

// routes/v1/users.ts
const router = express.Router();

router.get('/users', async (req, res) => {
  // V1 response format
  const users = await userService.list();
  res.json(users);  // Array directly
});

// routes/v2/users.ts
const router = express.Router();

router.get('/users', async (req, res) => {
  // V2 response format with envelope
  const users = await userService.list();
  res.json({
    data: users,
    meta: { version: 'v2' }
  });
});
```

## Query Parameter Versioning

```http
GET /api/users?version=1 HTTP/1.1
GET /api/users?api-version=2024-01-01 HTTP/1.1
```

### Pros and Cons

```
✅ Pros:
  - Optional versioning
  - Easy to implement
  - Can have default version

❌ Cons:
  - Easy to forget
  - Complicates caching
  - Not part of resource identifier
```

### Implementation

```typescript
// Middleware for query parameter versioning
function versionMiddleware(req: Request, res: Response, next: NextFunction) {
  const version = req.query.version || req.query['api-version'] || 'v1';
  req.apiVersion = version;
  next();
}

app.use(versionMiddleware);

app.get('/api/users', async (req, res) => {
  const users = await userService.list();

  if (req.apiVersion === 'v1') {
    res.json(users);
  } else if (req.apiVersion === 'v2') {
    res.json({ data: users, meta: {} });
  } else {
    res.status(400).json({ error: 'Unknown API version' });
  }
});
```

## Header Versioning

```http
# Custom header
GET /api/users HTTP/1.1
X-API-Version: 2

# Accept header (content negotiation)
GET /api/users HTTP/1.1
Accept: application/vnd.myapi.v2+json

# Accept header with version parameter
GET /api/users HTTP/1.1
Accept: application/json; version=2
```

### Pros and Cons

```
✅ Pros:
  - Clean URLs
  - More RESTful
  - Flexible version formats

❌ Cons:
  - Harder to test in browser
  - Less visible
  - Requires documentation
```

### Implementation

```typescript
// Custom header versioning
function headerVersionMiddleware(req: Request, res: Response, next: NextFunction) {
  const version = req.headers['x-api-version'] ||
                  req.headers['api-version'] ||
                  '1';
  req.apiVersion = `v${version}`;
  next();
}

// Accept header versioning
function acceptVersionMiddleware(req: Request, res: Response, next: NextFunction) {
  const accept = req.headers['accept'] || 'application/json';

  // Parse: application/vnd.myapi.v2+json
  const versionMatch = accept.match(/application\/vnd\.myapi\.v(\d+)\+json/);
  if (versionMatch) {
    req.apiVersion = `v${versionMatch[1]}`;
  } else {
    // Parse: application/json; version=2
    const paramMatch = accept.match(/version=(\d+)/);
    req.apiVersion = paramMatch ? `v${paramMatch[1]}` : 'v1';
  }

  next();
}
```

## Date-Based Versioning

Used by Stripe, Twilio, and others.

```http
GET /api/users HTTP/1.1
Stripe-Version: 2024-01-01
```

### Pros and Cons

```
✅ Pros:
  - Clear release timeline
  - Gradual rollout possible
  - Easy to understand freshness

❌ Cons:
  - Many potential versions
  - Complex compatibility matrix
  - Harder to maintain
```

### Implementation

```typescript
// Date-based versioning
const API_VERSIONS = [
  '2024-01-01',
  '2023-07-01',
  '2023-01-01',
] as const;

type ApiVersion = typeof API_VERSIONS[number];

function getEffectiveVersion(requested: string): ApiVersion {
  // Find the closest version at or before requested date
  const requestedDate = new Date(requested);

  for (const version of API_VERSIONS) {
    if (new Date(version) <= requestedDate) {
      return version;
    }
  }

  return API_VERSIONS[API_VERSIONS.length - 1]; // Oldest
}

function dateVersionMiddleware(req: Request, res: Response, next: NextFunction) {
  const requestedVersion = req.headers['api-version'] || API_VERSIONS[0];
  req.apiVersion = getEffectiveVersion(requestedVersion);

  // Always return actual version used
  res.setHeader('X-API-Version', req.apiVersion);
  next();
}
```

## Version Transformation

Transform responses based on version.

```typescript
interface UserV1 {
  id: string;
  name: string;
  email: string;
}

interface UserV2 {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  created_at: string;
}

// Internal representation
interface User {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  createdAt: Date;
}

// Transformers
const transformers = {
  v1: {
    user: (user: User): UserV1 => ({
      id: user.id,
      name: `${user.firstName} ${user.lastName}`,
      email: user.email,
    }),
  },
  v2: {
    user: (user: User): UserV2 => ({
      id: user.id,
      first_name: user.firstName,
      last_name: user.lastName,
      email: user.email,
      created_at: user.createdAt.toISOString(),
    }),
  },
};

// Response helper
function sendVersioned(res: Response, resource: string, data: any) {
  const version = res.req.apiVersion as keyof typeof transformers;
  const transformer = transformers[version]?.[resource];

  if (Array.isArray(data)) {
    res.json({ data: data.map(transformer) });
  } else {
    res.json({ data: transformer(data) });
  }
}

// Usage
app.get('/api/users/:id', async (req, res) => {
  const user = await userService.findById(req.params.id);
  sendVersioned(res, 'user', user);
});
```

## Deprecation Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                   API Deprecation Timeline                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Phase 1: Announce (6+ months before)                           │
│  ├── Add deprecation notices to docs                            │
│  ├── Send email to API users                                    │
│  ├── Add Deprecation header to responses                        │
│  └── Provide migration guide                                    │
│                                                                  │
│  Phase 2: Soft Deprecation (3-6 months)                         │
│  ├── Return warning headers                                     │
│  ├── Log deprecated endpoint usage                              │
│  └── Contact heavy users directly                               │
│                                                                  │
│  Phase 3: Hard Deprecation (1-3 months)                         │
│  ├── Return 410 Gone with migration info                        │
│  ├── Or redirect to new version                                 │
│  └── Keep monitoring for stragglers                             │
│                                                                  │
│  Phase 4: Sunset                                                 │
│  ├── Remove old version code                                    │
│  └── Archive documentation                                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Deprecation Headers

```http
HTTP/1.1 200 OK
Deprecation: true
Sunset: Sat, 01 Jun 2024 00:00:00 GMT
Link: <https://api.example.com/v2/users>; rel="successor-version"

{
  "data": [...],
  "meta": {
    "deprecation_notice": "This API version is deprecated. Please migrate to v2 by June 1, 2024.",
    "migration_guide": "https://docs.example.com/migration/v1-to-v2"
  }
}
```

### Deprecation Middleware

```typescript
interface DeprecationConfig {
  version: string;
  sunsetDate: Date;
  successorVersion: string;
  migrationGuide: string;
}

const deprecatedVersions: Record<string, DeprecationConfig> = {
  v1: {
    version: 'v1',
    sunsetDate: new Date('2024-06-01'),
    successorVersion: 'v2',
    migrationGuide: 'https://docs.example.com/migration/v1-to-v2',
  },
};

function deprecationMiddleware(req: Request, res: Response, next: NextFunction) {
  const config = deprecatedVersions[req.apiVersion];

  if (config) {
    const now = new Date();

    if (now > config.sunsetDate) {
      // Version is sunset - return 410 Gone
      return res.status(410).json({
        error: {
          code: 'VERSION_SUNSET',
          message: `API ${config.version} has been sunset`,
          migration_guide: config.migrationGuide,
          successor_version: config.successorVersion,
        },
      });
    }

    // Add deprecation headers
    res.setHeader('Deprecation', 'true');
    res.setHeader('Sunset', config.sunsetDate.toUTCString());
    res.setHeader(
      'Link',
      `<${req.baseUrl.replace(config.version, config.successorVersion)}>; rel="successor-version"`
    );

    // Log usage for monitoring
    logger.warn('Deprecated API version used', {
      version: config.version,
      endpoint: req.path,
      clientId: req.headers['x-client-id'],
    });
  }

  next();
}
```

## Breaking vs Non-Breaking Changes

```
┌─────────────────────────────────────────────────────────────────┐
│              Breaking vs Non-Breaking Changes                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Non-Breaking (No version bump needed):                         │
│  ├── Adding new optional fields                                 │
│  ├── Adding new endpoints                                       │
│  ├── Adding new optional parameters                             │
│  ├── Extending enums (if client handles unknown)                │
│  └── Performance improvements                                   │
│                                                                  │
│  Breaking (Version bump required):                              │
│  ├── Removing fields                                            │
│  ├── Renaming fields                                            │
│  ├── Changing field types                                       │
│  ├── Removing endpoints                                         │
│  ├── Changing required parameters                               │
│  ├── Changing error codes/formats                               │
│  └── Changing authentication                                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│                  Versioning Best Practices                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Start with Versioning from Day 1                            │
│     └── Easier than adding later                                │
│                                                                  │
│  2. Choose One Strategy and Stick With It                       │
│     └── Consistency is key                                      │
│                                                                  │
│  3. Support At Least 2 Versions                                 │
│     └── Give clients time to migrate                            │
│                                                                  │
│  4. Document Version Differences                                │
│     ├── Changelog per version                                   │
│     └── Migration guides                                        │
│                                                                  │
│  5. Use Semantic Versioning Principles                          │
│     ├── Major: Breaking changes                                 │
│     ├── Minor: New features                                     │
│     └── Patch: Bug fixes                                        │
│                                                                  │
│  6. Communicate Deprecation Early                               │
│     └── 6+ months notice minimum                                │
│                                                                  │
│  7. Monitor Version Usage                                       │
│     └── Know when it's safe to sunset                           │
│                                                                  │
│  8. Make Breaking Changes Worth It                              │
│     └── Bundle multiple breaking changes                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Version Strategy Comparison

| Strategy | Visibility | RESTful | Caching | Testing | Flexibility |
|----------|------------|---------|---------|---------|-------------|
| URL Path | High | Low | Easy | Easy | Low |
| Query Param | Medium | Low | Hard | Easy | Medium |
| Header | Low | High | Medium | Medium | High |
| Accept | Low | High | Medium | Hard | High |
| Date-based | Medium | Medium | Medium | Medium | High |
