# Tenant Architecture Template

## Multi-Tenancy Models

### Shared Database (Row-Level)
```
┌─────────────────────────────────────┐
│           Single Database           │
├─────────────────────────────────────┤
│  tenant_id | data | ...             │
│  A         | ...  | ...             │
│  B         | ...  | ...             │
│  C         | ...  | ...             │
└─────────────────────────────────────┘
```

### Schema Per Tenant
```
┌─────────────────────────────────────┐
│           Single Database           │
├──────────┬──────────┬──────────────┤
│ tenant_a │ tenant_b │ tenant_c     │
│ schema   │ schema   │ schema       │
└──────────┴──────────┴──────────────┘
```

### Database Per Tenant
```
┌──────────┐ ┌──────────┐ ┌──────────┐
│ tenant_a │ │ tenant_b │ │ tenant_c │
│ database │ │ database │ │ database │
└──────────┘ └──────────┘ └──────────┘
```

## Tenant Data Model

```typescript
interface Tenant {
  id: string;
  slug: string;
  name: string;

  // Domain
  subdomain: string;
  customDomains: string[];

  // Configuration
  settings: {
    branding: BrandingSettings;
    features: FeatureSettings;
    integrations: IntegrationSettings;
    security: SecuritySettings;
  };

  // Plan & Limits
  plan: {
    id: string;
    name: string;
    limits: ResourceLimits;
  };

  // Status
  status: TenantStatus;
  createdAt: Date;
  activatedAt?: Date;
}

interface ResourceLimits {
  users: number;
  storage: number; // bytes
  apiCalls: number; // per month
  customFields: number;
  integrations: number;
}
```

## Tenant Resolution

```typescript
// Resolution strategies
type ResolutionStrategy =
  | 'subdomain'    // tenant.app.com
  | 'path'         // app.com/tenant
  | 'header'       // X-Tenant-ID header
  | 'query'        // ?tenant=xxx
  | 'jwt';         // From auth token

class TenantResolver {
  resolve(req: Request): string | null {
    // 1. Custom domain lookup
    const customDomain = this.resolveByCustomDomain(req.hostname);
    if (customDomain) return customDomain;

    // 2. Subdomain
    const subdomain = this.extractSubdomain(req.hostname);
    if (subdomain) return subdomain;

    // 3. Header
    const header = req.headers['x-tenant-id'];
    if (header) return header;

    // 4. JWT claim
    const token = req.user?.tenantId;
    if (token) return token;

    return null;
  }
}
```

## Isolation Patterns

```typescript
// Row-level security with middleware
const tenantIsolationMiddleware = (req, res, next) => {
  const tenantId = req.tenantContext.tenantId;

  // Inject tenant filter into all queries
  req.db = req.db.extend({
    query: {
      $allModels: {
        async $allOperations({ operation, args, query }) {
          if (['findMany', 'findFirst', 'count', 'aggregate'].includes(operation)) {
            args.where = { ...args.where, tenantId };
          }
          if (['create', 'createMany'].includes(operation)) {
            args.data = { ...args.data, tenantId };
          }
          return query(args);
        }
      }
    }
  });

  next();
};
```
