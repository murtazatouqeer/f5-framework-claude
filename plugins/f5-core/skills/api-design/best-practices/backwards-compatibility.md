---
name: backwards-compatibility
description: Maintaining backwards compatibility in APIs
category: api-design/best-practices
applies_to: [all]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Backwards Compatibility

## Overview

Backwards compatibility ensures existing clients continue to work when APIs
evolve. This guide covers strategies for making non-breaking changes, handling
deprecations, and maintaining stable contracts.

## Breaking vs Non-Breaking Changes

```
┌─────────────────────────────────────────────────────────────────┐
│                    Change Classification                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ✅ Non-Breaking (Safe)                                         │
│  ├── Adding new endpoints                                       │
│  ├── Adding optional request fields                             │
│  ├── Adding response fields                                     │
│  ├── Adding new enum values (if client ignores unknown)         │
│  ├── Adding optional query parameters                           │
│  └── Adding new HTTP methods to existing resources              │
│                                                                  │
│  ❌ Breaking (Dangerous)                                        │
│  ├── Removing endpoints                                         │
│  ├── Removing request/response fields                           │
│  ├── Renaming fields                                            │
│  ├── Changing field types                                       │
│  ├── Making optional fields required                            │
│  ├── Changing URL structure                                     │
│  ├── Changing authentication mechanism                          │
│  ├── Changing error codes/formats                               │
│  └── Changing HTTP methods                                      │
│                                                                  │
│  ⚠️ Potentially Breaking                                        │
│  ├── Changing default values                                    │
│  ├── Adding required response fields                            │
│  ├── Changing validation rules (stricter)                       │
│  ├── Changing rate limits                                       │
│  └── Changing pagination defaults                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Additive Changes

### Adding Fields

```typescript
// Original response (v1)
interface UserResponseV1 {
  id: string;
  name: string;
  email: string;
}

// Extended response (v1 compatible)
interface UserResponseV1Extended {
  id: string;
  name: string;
  email: string;
  // New fields - existing clients ignore these
  avatar_url?: string;
  created_at?: string;
  metadata?: Record<string, string>;
}

// Client handling (tolerant reader pattern)
function parseUser(data: any): User {
  return {
    id: data.id,
    name: data.name,
    email: data.email,
    // Safely access new fields
    avatarUrl: data.avatar_url ?? null,
    createdAt: data.created_at ? new Date(data.created_at) : null,
  };
}
```

### Adding Endpoints

```typescript
// Original endpoints
app.get('/users', listUsers);
app.get('/users/:id', getUser);
app.post('/users', createUser);

// New endpoints (non-breaking additions)
app.get('/users/:id/activity', getUserActivity);
app.post('/users/:id/verify', verifyUser);
app.get('/users/search', searchUsers);

// New resource (non-breaking)
app.get('/teams', listTeams);
app.get('/teams/:id', getTeam);
app.post('/teams', createTeam);
```

### Adding Optional Parameters

```typescript
// Original endpoint
// GET /users?page_size=20&cursor=xxx

// Extended with optional filters (non-breaking)
// GET /users?page_size=20&cursor=xxx&status=active&role=admin&sort=-created_at

interface ListUsersParams {
  page_size?: number; // Existing
  cursor?: string; // Existing
  // New optional parameters
  status?: 'active' | 'inactive' | 'all';
  role?: string;
  sort?: string;
  created_after?: string;
  created_before?: string;
}

function listUsers(params: ListUsersParams) {
  const {
    page_size = 20,
    cursor,
    status = 'all',
    role,
    sort = '-created_at',
    created_after,
    created_before,
  } = params;

  // Build query with defaults for backwards compatibility
  let query = db.users.query();

  if (status !== 'all') {
    query = query.where('status', status);
  }
  if (role) {
    query = query.where('role', role);
  }
  // ... rest of implementation
}
```

## Deprecation Strategy

### Marking Deprecation

```typescript
// Response headers for deprecation
function deprecationMiddleware(options: DeprecationOptions) {
  return (req: Request, res: Response, next: NextFunction) => {
    if (options.deprecated) {
      // Standard deprecation headers
      res.set('Deprecation', options.deprecationDate);
      res.set('Sunset', options.sunsetDate);
      res.set(
        'Link',
        `<${options.replacementUrl}>; rel="successor-version"`
      );

      // Custom header with more info
      res.set('X-Deprecation-Notice', options.message);
    }
    next();
  };
}

// Usage
app.get(
  '/v1/users',
  deprecationMiddleware({
    deprecated: true,
    deprecationDate: '2024-01-01',
    sunsetDate: '2024-07-01',
    replacementUrl: '/v2/users',
    message: 'This endpoint is deprecated. Please migrate to /v2/users',
  }),
  listUsersV1
);

// OpenAPI deprecation
/*
paths:
  /v1/users:
    get:
      deprecated: true
      x-sunset-date: "2024-07-01"
      description: |
        **Deprecated**: This endpoint will be removed on 2024-07-01.
        Please use /v2/users instead.
*/
```

### Field Deprecation

```typescript
// Deprecate fields in response
interface UserResponse {
  id: string;
  name: string;
  email: string;

  // Deprecated - use full_name instead
  /** @deprecated Use full_name instead */
  displayName?: string;
  full_name: string;

  // Deprecated - use metadata instead
  /** @deprecated Use metadata.avatar_url instead */
  avatar?: string;
  metadata: {
    avatar_url?: string;
  };
}

// Transform function maintaining backwards compatibility
function transformUser(user: DbUser): UserResponse {
  return {
    id: user.id,
    name: user.name,
    email: user.email,
    // Include deprecated field for old clients
    displayName: user.fullName,
    // New field
    full_name: user.fullName,
    // Deprecated field
    avatar: user.avatarUrl,
    // New structure
    metadata: {
      avatar_url: user.avatarUrl,
    },
  };
}

// Document deprecation in response
function addDeprecationWarnings(response: any, deprecations: string[]) {
  return {
    ...response,
    _warnings: deprecations.map((field) => ({
      type: 'deprecated_field',
      field,
      message: `The field '${field}' is deprecated and will be removed in a future version`,
    })),
  };
}
```

### Endpoint Migration

```typescript
// Phased endpoint migration
class MigrationMiddleware {
  // Phase 1: Both endpoints work, old returns warning
  static phase1(oldPath: string, newPath: string) {
    return (req: Request, res: Response, next: NextFunction) => {
      if (req.path === oldPath) {
        res.set('Warning', `299 - "Deprecated: Use ${newPath} instead"`);
      }
      next();
    };
  }

  // Phase 2: Old endpoint redirects to new
  static phase2(oldPath: string, newPath: string) {
    return (req: Request, res: Response, next: NextFunction) => {
      if (req.path === oldPath) {
        // Permanent redirect
        return res.redirect(301, newPath + (req.search || ''));
      }
      next();
    };
  }

  // Phase 3: Old endpoint returns gone
  static phase3(oldPath: string, newPath: string) {
    return (req: Request, res: Response, next: NextFunction) => {
      if (req.path === oldPath) {
        return res.status(410).json({
          error: {
            code: 'ENDPOINT_REMOVED',
            message: `This endpoint has been removed. Please use ${newPath}`,
          },
        });
      }
      next();
    };
  }
}

// Timeline
// Month 1-3: phase1 - warnings
// Month 4-6: phase2 - redirects
// Month 7+: phase3 - 410 Gone
```

## Versioning Strategies

### URL Versioning

```typescript
// Version in URL path
app.use('/v1', v1Router);
app.use('/v2', v2Router);

// Version routing
const v1Router = express.Router();
v1Router.get('/users', listUsersV1);
v1Router.get('/users/:id', getUserV1);

const v2Router = express.Router();
v2Router.get('/users', listUsersV2);
v2Router.get('/users/:id', getUserV2);

// Version-specific controllers
async function listUsersV1(req: Request, res: Response) {
  const users = await userService.list(req.query);
  res.json({
    data: users.map(transformUserV1),
  });
}

async function listUsersV2(req: Request, res: Response) {
  const users = await userService.list(req.query);
  res.json({
    object: 'list',
    data: users.map(transformUserV2),
    pagination: { ... },
  });
}
```

### Header Versioning

```typescript
// Version in Accept header
// Accept: application/vnd.myapi.v2+json

function versionFromHeader(req: Request): number {
  const accept = req.headers.accept || '';
  const match = accept.match(/application\/vnd\.myapi\.v(\d+)\+json/);
  return match ? parseInt(match[1], 10) : 1; // Default to v1
}

function versionMiddleware(req: Request, res: Response, next: NextFunction) {
  req.apiVersion = versionFromHeader(req);
  res.set('X-API-Version', req.apiVersion.toString());
  next();
}

// Version-aware controller
async function getUser(req: Request, res: Response) {
  const user = await userService.findById(req.params.id);

  const transformer =
    req.apiVersion >= 2 ? transformUserV2 : transformUserV1;

  res.json({ data: transformer(user) });
}
```

### Query Parameter Versioning

```typescript
// Version in query parameter
// GET /users?version=2

function versionFromQuery(req: Request): number {
  const version = req.query.version;
  return version ? parseInt(version as string, 10) : 1;
}

// Not recommended but sometimes necessary for JSONP or restricted clients
```

## Tolerant Reader Pattern

### Client Implementation

```typescript
// Robust client that handles API evolution
class TolerantApiClient {
  async getUser(id: string): Promise<User> {
    const response = await this.fetch(`/users/${id}`);
    return this.parseUser(response.data);
  }

  private parseUser(data: any): User {
    // Handle missing fields gracefully
    return {
      id: data.id || '',
      name: data.name || data.displayName || 'Unknown',
      email: data.email || '',
      // Handle new fields
      avatarUrl: data.avatar_url || data.avatar || null,
      // Handle restructured fields
      role: data.role || data.user_role || 'user',
      // Handle type changes
      createdAt: this.parseDate(data.created_at),
      // Ignore unknown fields automatically
    };
  }

  private parseDate(value: any): Date | null {
    if (!value) return null;
    if (value instanceof Date) return value;
    if (typeof value === 'string') return new Date(value);
    if (typeof value === 'number') return new Date(value);
    return null;
  }

  // Handle unknown enum values
  private parseStatus(value: string): UserStatus {
    const known: UserStatus[] = ['active', 'inactive', 'suspended'];
    return known.includes(value as UserStatus)
      ? (value as UserStatus)
      : 'unknown';
  }
}
```

### Server Implementation

```typescript
// Accept unknown fields in requests
const CreateUserSchema = z
  .object({
    email: z.string().email(),
    name: z.string(),
    role: z.enum(['user', 'admin']).optional(),
  })
  .passthrough(); // Allow additional properties

// Ignore unknown fields in requests
const StrictCreateUserSchema = z
  .object({
    email: z.string().email(),
    name: z.string(),
    role: z.enum(['user', 'admin']).optional(),
  })
  .strict(); // Reject additional properties

// Recommended: strip unknown fields
const SafeCreateUserSchema = z
  .object({
    email: z.string().email(),
    name: z.string(),
    role: z.enum(['user', 'admin']).optional(),
  })
  .strip(); // Remove additional properties silently
```

## Contract Testing

```typescript
// Contract test to ensure backwards compatibility
import { Pact } from '@pact-foundation/pact';

describe('User API Contract', () => {
  const provider = new Pact({
    consumer: 'WebApp',
    provider: 'UserService',
  });

  beforeAll(() => provider.setup());
  afterAll(() => provider.finalize());

  describe('GET /users/:id', () => {
    it('returns user with required fields', async () => {
      // Define expected contract
      await provider.addInteraction({
        state: 'user exists',
        uponReceiving: 'a request for user',
        withRequest: {
          method: 'GET',
          path: '/users/usr_123',
        },
        willRespondWith: {
          status: 200,
          body: {
            data: {
              id: like('usr_123'),
              name: like('John Doe'),
              email: like('john@example.com'),
              // New fields are optional
              created_at: like('2024-01-15T00:00:00Z'),
            },
          },
        },
      });

      // Test the contract
      const response = await client.getUser('usr_123');
      expect(response.id).toBe('usr_123');
    });
  });
});
```

## Compatibility Checklist

```
┌─────────────────────────────────────────────────────────────────┐
│             Backwards Compatibility Checklist                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Before Making Changes                                          │
│  □ Review change classification (breaking/non-breaking)         │
│  □ Check existing client integrations                           │
│  □ Document migration path for breaking changes                 │
│  □ Plan deprecation timeline (minimum 6 months)                 │
│                                                                  │
│  For Non-Breaking Changes                                       │
│  □ New fields have default values                               │
│  □ New endpoints don't conflict with existing                   │
│  □ New parameters are optional                                  │
│  □ Contract tests pass                                          │
│                                                                  │
│  For Breaking Changes                                           │
│  □ Increment major version                                      │
│  □ Maintain old version during transition                       │
│  □ Add deprecation headers to old version                       │
│  □ Notify all API consumers                                     │
│  □ Update documentation                                         │
│  □ Provide migration guide                                      │
│                                                                  │
│  For Deprecations                                               │
│  □ Add Deprecation and Sunset headers                           │
│  □ Update OpenAPI spec with deprecated: true                    │
│  □ Log usage of deprecated features                             │
│  □ Communicate deprecation to users                             │
│  □ Set and honor sunset date                                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│          Backwards Compatibility Best Practices                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Design for Evolution                                        │
│     └── Plan for change from the beginning                      │
│                                                                  │
│  2. Be Additive                                                 │
│     └── Add new things, don't modify existing                   │
│                                                                  │
│  3. Use Optional Fields                                         │
│     └── New fields should always be optional                    │
│                                                                  │
│  4. Deprecate Gracefully                                        │
│     └── Long deprecation periods with clear communication       │
│                                                                  │
│  5. Version Thoughtfully                                        │
│     └── Only major version for breaking changes                 │
│                                                                  │
│  6. Test Contracts                                              │
│     └── Automated compatibility testing                         │
│                                                                  │
│  7. Monitor Usage                                               │
│     └── Track deprecated feature usage                          │
│                                                                  │
│  8. Communicate Clearly                                         │
│     └── Changelogs, migration guides, notifications             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```
