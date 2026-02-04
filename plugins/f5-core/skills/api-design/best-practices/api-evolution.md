---
name: api-evolution
description: API versioning and evolution strategies
category: api-design/best-practices
applies_to: [all]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# API Evolution

## Overview

APIs must evolve to meet changing requirements while maintaining stability for
existing clients. This guide covers versioning strategies, release management,
and long-term API lifecycle planning.

## Versioning Strategies

```
┌─────────────────────────────────────────────────────────────────┐
│                   Versioning Approaches                          │
├────────────────┬────────────────────────────────────────────────┤
│ Strategy       │ Example                                        │
├────────────────┼────────────────────────────────────────────────┤
│ URL Path       │ /v1/users, /v2/users                           │
│ Header         │ Accept: application/vnd.api.v2+json            │
│ Query Param    │ /users?version=2                               │
│ Subdomain      │ v2.api.example.com                             │
│ Date-based     │ Accept-Version: 2024-01-15                     │
├────────────────┴────────────────────────────────────────────────┤
│                                                                  │
│  Recommended: URL Path (most visible, easiest to implement)     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### URL Path Versioning

```typescript
// Most common and recommended approach
import express from 'express';

const app = express();

// Version routers
import v1Router from './routes/v1';
import v2Router from './routes/v2';
import v3Router from './routes/v3';

// Mount versioned routes
app.use('/v1', v1Router);
app.use('/v2', v2Router);
app.use('/v3', v3Router);

// Latest alias (optional)
app.use('/latest', v3Router);

// Default version redirect
app.get('/users', (req, res) => {
  res.redirect(301, '/v3/users');
});

// Version-specific implementations
// routes/v1/users.ts
export const v1Router = express.Router();
v1Router.get('/users', async (req, res) => {
  const users = await userService.list();
  res.json(users.map(toV1Format));
});

// routes/v2/users.ts
export const v2Router = express.Router();
v2Router.get('/users', async (req, res) => {
  const users = await userService.list();
  res.json({
    data: users.map(toV2Format),
    meta: { total: users.length },
  });
});

// routes/v3/users.ts
export const v3Router = express.Router();
v3Router.get('/users', async (req, res) => {
  const result = await userService.listPaginated(req.query);
  res.json({
    object: 'list',
    data: result.users.map(toV3Format),
    pagination: result.pagination,
  });
});
```

### Header Versioning

```typescript
// Accept header versioning
// Accept: application/vnd.myapi.v2+json

function getVersion(req: Request): number {
  const accept = req.headers.accept || '';

  // Parse version from media type
  const match = accept.match(/application\/vnd\.myapi\.v(\d+)\+json/);
  if (match) {
    return parseInt(match[1], 10);
  }

  // Check custom header
  const customVersion = req.headers['x-api-version'];
  if (customVersion) {
    return parseInt(customVersion as string, 10);
  }

  // Default version
  return 1;
}

// Middleware to set version
function versionMiddleware(req: Request, res: Response, next: NextFunction) {
  req.apiVersion = getVersion(req);

  // Set response content type with version
  res.set('Content-Type', `application/vnd.myapi.v${req.apiVersion}+json`);
  res.set('X-API-Version', req.apiVersion.toString());

  next();
}

// Version-aware controller
async function listUsers(req: Request, res: Response) {
  const users = await userService.list();

  switch (req.apiVersion) {
    case 3:
      return res.json(formatV3(users));
    case 2:
      return res.json(formatV2(users));
    default:
      return res.json(formatV1(users));
  }
}
```

### Date-Based Versioning (Stripe Style)

```typescript
// Version by release date
// Accept-Version: 2024-01-15

interface ApiVersion {
  date: string;
  changes: Change[];
}

const API_VERSIONS: ApiVersion[] = [
  {
    date: '2024-03-01',
    changes: [
      { type: 'added', field: 'users.metadata' },
      { type: 'deprecated', field: 'users.old_field' },
    ],
  },
  {
    date: '2024-01-15',
    changes: [
      { type: 'added', field: 'users.created_at' },
      { type: 'changed', field: 'users.status', from: 'string', to: 'enum' },
    ],
  },
  {
    date: '2023-10-01',
    changes: [{ type: 'initial' }],
  },
];

function getVersionDate(req: Request): string {
  const header = req.headers['accept-version'] || req.headers['stripe-version'];
  if (header && isValidDate(header as string)) {
    return header as string;
  }
  // Return latest version
  return API_VERSIONS[0].date;
}

// Apply version-specific transformations
function transformResponse(data: any, versionDate: string): any {
  const applicableChanges = API_VERSIONS.filter((v) => v.date > versionDate)
    .flatMap((v) => v.changes);

  let result = { ...data };

  for (const change of applicableChanges) {
    if (change.type === 'added') {
      // Remove fields added after client's version
      result = omitField(result, change.field);
    }
    if (change.type === 'changed') {
      // Revert field to old format
      result = revertField(result, change);
    }
  }

  return result;
}
```

## Semantic Versioning

```
┌─────────────────────────────────────────────────────────────────┐
│                    Semantic Versioning                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│                      MAJOR.MINOR.PATCH                          │
│                        2   . 1  .  3                            │
│                        │     │     │                            │
│                        │     │     └── Backwards-compatible     │
│                        │     │         bug fixes                │
│                        │     │                                  │
│                        │     └── Backwards-compatible           │
│                        │         new features                   │
│                        │                                        │
│                        └── Breaking changes                     │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  For APIs, typically only MAJOR version is exposed:             │
│  • /v1 = 1.x.x (all compatible versions)                        │
│  • /v2 = 2.x.x (breaking changes from v1)                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Version Policy

```typescript
interface VersionPolicy {
  // Major version increment triggers
  majorChanges: [
    'Removing endpoints',
    'Removing required fields',
    'Changing field types',
    'Changing authentication',
    'Changing error formats',
  ];

  // Minor version changes (non-breaking)
  minorChanges: [
    'Adding new endpoints',
    'Adding optional fields',
    'Adding new enum values',
    'Performance improvements',
  ];

  // Patch changes
  patchChanges: ['Bug fixes', 'Documentation updates', 'Security patches'];
}

// Expose versions appropriately
const versionConfig = {
  // URL shows major version only
  urlVersion: 'v2',

  // Headers can show full version
  fullVersion: '2.3.1',

  // Date of this release
  releaseDate: '2024-01-15',

  // Minimum supported version
  minimumVersion: 'v1',

  // Sunset date for old versions
  v1Sunset: '2024-12-31',
};
```

## Release Management

### Release Pipeline

```typescript
// API release stages
enum ReleaseStage {
  ALPHA = 'alpha', // Internal testing only
  BETA = 'beta', // Limited external testing
  RC = 'rc', // Release candidate
  GA = 'ga', // General availability
  DEPRECATED = 'deprecated', // Phasing out
  SUNSET = 'sunset', // End of life
}

interface ApiRelease {
  version: string;
  stage: ReleaseStage;
  releaseDate: Date;
  sunsetDate?: Date;
  changelog: ChangelogEntry[];
  breakingChanges: BreakingChange[];
  migrationGuide?: string;
}

// Release lifecycle
class ReleaseManager {
  private releases: Map<string, ApiRelease> = new Map();

  async promoteToGA(version: string): Promise<void> {
    const release = this.releases.get(version);
    if (!release) throw new Error('Release not found');

    // Validate release criteria
    await this.validateGACriteria(release);

    // Update stage
    release.stage = ReleaseStage.GA;

    // Notify subscribers
    await this.notifySubscribers('release', release);

    // Update documentation
    await this.updateDocs(release);
  }

  async deprecate(version: string, sunsetDate: Date): Promise<void> {
    const release = this.releases.get(version);
    if (!release) throw new Error('Release not found');

    release.stage = ReleaseStage.DEPRECATED;
    release.sunsetDate = sunsetDate;

    // Start deprecation notifications
    await this.notifySubscribers('deprecation', release);

    // Enable deprecation headers
    await this.enableDeprecationHeaders(version);
  }

  private async validateGACriteria(release: ApiRelease): Promise<void> {
    // Check documentation complete
    // Check contract tests passing
    // Check performance benchmarks
    // Check security review
  }
}
```

### Feature Flags

```typescript
// Feature flags for gradual rollout
interface FeatureFlag {
  name: string;
  enabled: boolean;
  rolloutPercentage: number;
  allowlist: string[]; // User IDs or API keys
  blocklist: string[];
}

class FeatureFlagService {
  private flags: Map<string, FeatureFlag> = new Map();

  isEnabled(flagName: string, context: RequestContext): boolean {
    const flag = this.flags.get(flagName);
    if (!flag) return false;
    if (!flag.enabled) return false;

    // Check blocklist
    if (flag.blocklist.includes(context.userId)) {
      return false;
    }

    // Check allowlist
    if (flag.allowlist.includes(context.userId)) {
      return true;
    }

    // Percentage rollout
    const hash = this.hashUserId(context.userId);
    return hash < flag.rolloutPercentage;
  }

  private hashUserId(userId: string): number {
    // Consistent hash to percentage (0-100)
    let hash = 0;
    for (const char of userId) {
      hash = ((hash << 5) - hash + char.charCodeAt(0)) | 0;
    }
    return Math.abs(hash) % 100;
  }
}

// Usage in controller
async function listUsers(req: Request, res: Response) {
  const users = await userService.list();

  // New feature behind flag
  if (featureFlags.isEnabled('enhanced_user_response', req.context)) {
    return res.json(formatEnhanced(users));
  }

  return res.json(formatStandard(users));
}
```

## Migration Strategies

### Parallel Running

```typescript
// Run old and new versions in parallel during migration
class ParallelMigration {
  async migrate(
    oldVersion: () => Promise<any>,
    newVersion: () => Promise<any>,
    options: MigrationOptions
  ): Promise<any> {
    // Run both versions
    const [oldResult, newResult] = await Promise.all([
      this.safeExecute(oldVersion),
      this.safeExecute(newVersion),
    ]);

    // Compare results
    if (options.compareResults) {
      const comparison = this.compareResults(oldResult, newResult);
      if (!comparison.match) {
        await this.reportDifference(comparison);
      }
    }

    // Return based on migration stage
    switch (options.stage) {
      case 'shadow':
        // Return old, log new
        return oldResult.data;
      case 'canary':
        // Return new for some users
        if (options.useNew(options.context)) {
          return newResult.data;
        }
        return oldResult.data;
      case 'full':
        // Return new
        return newResult.data;
    }
  }

  private async safeExecute(fn: () => Promise<any>): Promise<ExecutionResult> {
    const start = Date.now();
    try {
      const data = await fn();
      return {
        success: true,
        data,
        duration: Date.now() - start,
      };
    } catch (error) {
      return {
        success: false,
        error,
        duration: Date.now() - start,
      };
    }
  }
}
```

### Incremental Migration

```typescript
// Migrate endpoints incrementally
interface MigrationPlan {
  phases: MigrationPhase[];
  currentPhase: number;
  startDate: Date;
  targetDate: Date;
}

interface MigrationPhase {
  name: string;
  endpoints: string[];
  startDate: Date;
  completedDate?: Date;
  status: 'pending' | 'in_progress' | 'completed';
}

const migrationPlan: MigrationPlan = {
  phases: [
    {
      name: 'Phase 1: Read endpoints',
      endpoints: ['GET /users', 'GET /users/:id', 'GET /products'],
      startDate: new Date('2024-01-01'),
      status: 'completed',
    },
    {
      name: 'Phase 2: Write endpoints',
      endpoints: ['POST /users', 'PUT /users/:id', 'DELETE /users/:id'],
      startDate: new Date('2024-02-01'),
      status: 'in_progress',
    },
    {
      name: 'Phase 3: Complex operations',
      endpoints: ['POST /orders', 'POST /payments'],
      startDate: new Date('2024-03-01'),
      status: 'pending',
    },
  ],
  currentPhase: 1,
  startDate: new Date('2024-01-01'),
  targetDate: new Date('2024-04-01'),
};
```

## Changelog Management

### Changelog Format

```markdown
# API Changelog

## [v3.2.0] - 2024-03-15

### Added

- `GET /users/{id}/activity` - Retrieve user activity history
- `metadata` field on User resource for custom key-value pairs
- Webhook support for user events

### Changed

- Improved pagination performance for large result sets
- Default page_size increased from 20 to 50

### Deprecated

- `displayName` field on User - use `full_name` instead
- `GET /users/search` - use `GET /users?q=query` instead

### Security

- Fixed potential information disclosure in error messages

## [v3.1.0] - 2024-02-01

### Added

- Support for filtering users by creation date
- `sort` parameter for list endpoints

### Fixed

- Rate limiting now correctly resets at window boundaries
- Pagination cursor encoding issue with special characters
```

### Automated Changelog

```typescript
// Generate changelog from commits/PRs
interface ChangelogEntry {
  type: 'added' | 'changed' | 'deprecated' | 'removed' | 'fixed' | 'security';
  description: string;
  pr?: number;
  breaking?: boolean;
}

class ChangelogGenerator {
  async generateFromGit(fromTag: string, toTag: string): Promise<ChangelogEntry[]> {
    const commits = await this.getCommitsBetween(fromTag, toTag);
    return commits
      .map(this.parseCommit)
      .filter((entry) => entry !== null) as ChangelogEntry[];
  }

  private parseCommit(commit: GitCommit): ChangelogEntry | null {
    // Parse conventional commits
    const match = commit.message.match(
      /^(feat|fix|docs|style|refactor|perf|test|chore)(\(.+\))?(!)?:\s*(.+)$/
    );

    if (!match) return null;

    const [, type, scope, breaking, description] = match;

    const typeMap: Record<string, ChangelogEntry['type']> = {
      feat: 'added',
      fix: 'fixed',
      perf: 'changed',
      refactor: 'changed',
    };

    const entryType = typeMap[type];
    if (!entryType) return null;

    return {
      type: entryType,
      description,
      breaking: !!breaking,
    };
  }
}
```

## API Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                     API Lifecycle Stages                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. DESIGN                                                      │
│     ├── Requirements gathering                                  │
│     ├── API design review                                       │
│     └── OpenAPI specification                                   │
│                                                                  │
│  2. DEVELOPMENT                                                 │
│     ├── Implementation                                          │
│     ├── Unit testing                                            │
│     └── Contract testing                                        │
│                                                                  │
│  3. ALPHA                                                       │
│     ├── Internal testing                                        │
│     ├── Security review                                         │
│     └── Performance testing                                     │
│                                                                  │
│  4. BETA                                                        │
│     ├── Limited external access                                 │
│     ├── Feedback collection                                     │
│     └── Documentation refinement                                │
│                                                                  │
│  5. GENERAL AVAILABILITY                                        │
│     ├── Public release                                          │
│     ├── SLA commitment                                          │
│     └── Support channels active                                 │
│                                                                  │
│  6. MAINTENANCE                                                 │
│     ├── Bug fixes                                               │
│     ├── Security patches                                        │
│     └── Minor improvements                                      │
│                                                                  │
│  7. DEPRECATION                                                 │
│     ├── Announcement (6+ months notice)                         │
│     ├── Migration support                                       │
│     └── Usage monitoring                                        │
│                                                                  │
│  8. SUNSET                                                      │
│     ├── Final shutdown                                          │
│     ├── 410 Gone responses                                      │
│     └── Archive documentation                                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Lifecycle Management

```typescript
class ApiLifecycle {
  private versions: Map<string, VersionState> = new Map();

  async transitionTo(version: string, stage: LifecycleStage): Promise<void> {
    const current = this.versions.get(version);
    if (!current) throw new Error('Version not found');

    // Validate transition
    if (!this.isValidTransition(current.stage, stage)) {
      throw new Error(`Invalid transition from ${current.stage} to ${stage}`);
    }

    // Execute transition actions
    await this.executeTransitionActions(version, current.stage, stage);

    // Update state
    current.stage = stage;
    current.stageChangedAt = new Date();

    // Notify stakeholders
    await this.notifyStakeholders(version, stage);
  }

  private isValidTransition(from: LifecycleStage, to: LifecycleStage): boolean {
    const validTransitions: Record<LifecycleStage, LifecycleStage[]> = {
      design: ['development'],
      development: ['alpha'],
      alpha: ['beta', 'development'], // Can go back
      beta: ['ga', 'alpha'], // Can go back
      ga: ['deprecated'],
      deprecated: ['sunset'],
      sunset: [], // Terminal
    };

    return validTransitions[from]?.includes(to) ?? false;
  }

  private async executeTransitionActions(
    version: string,
    from: LifecycleStage,
    to: LifecycleStage
  ): Promise<void> {
    if (to === 'ga') {
      await this.publishDocumentation(version);
      await this.enableProduction(version);
      await this.activateSLA(version);
    }

    if (to === 'deprecated') {
      await this.enableDeprecationHeaders(version);
      await this.scheduleReminders(version);
    }

    if (to === 'sunset') {
      await this.disableEndpoints(version);
      await this.archiveDocumentation(version);
    }
  }
}
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│                API Evolution Best Practices                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Plan for Evolution                                          │
│     └── Design APIs with change in mind from day one            │
│                                                                  │
│  2. Version Strategically                                       │
│     └── Major versions for breaking changes only                │
│                                                                  │
│  3. Communicate Changes                                         │
│     └── Changelogs, emails, deprecation notices                 │
│                                                                  │
│  4. Provide Migration Paths                                     │
│     └── Clear guides, tools, and support                        │
│                                                                  │
│  5. Maintain Multiple Versions                                  │
│     └── Support at least N-1 versions                           │
│                                                                  │
│  6. Use Feature Flags                                           │
│     └── Gradual rollout of new features                         │
│                                                                  │
│  7. Monitor Usage                                               │
│     └── Track version and endpoint usage                        │
│                                                                  │
│  8. Set Clear SLAs                                              │
│     └── Define support periods and deprecation policies         │
│                                                                  │
│  9. Automate Testing                                            │
│     └── Contract tests, compatibility tests                     │
│                                                                  │
│  10. Document Everything                                        │
│      └── API specs, changelogs, migration guides                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```
