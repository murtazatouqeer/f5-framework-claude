# Multi-Tenancy Patterns

## Overview
Design patterns cho multi-tenant SaaS applications.

## Key Patterns

### Pattern 1: Database Per Tenant
**When to use:** High isolation requirements, enterprise customers
```typescript
class TenantDatabaseRouter {
  async getConnection(tenantId: string): Promise<DatabaseConnection> {
    const tenant = await this.getTenant(tenantId);
    const connectionString = tenant.databaseUrl;
    return this.connectionPool.get(connectionString);
  }
}
```

### Pattern 2: Schema Per Tenant
**When to use:** Moderate isolation, cost-effective
```typescript
const setTenantSchema = async (tenantId: string) => {
  await db.raw(`SET search_path TO tenant_${tenantId}`);
};
```

### Pattern 3: Row-Level Security
**When to use:** Cost optimization, shared infrastructure
```typescript
// Prisma middleware for automatic tenant filtering
const tenantMiddleware = async (params, next) => {
  if (params.action === 'findMany') {
    params.args.where = { ...params.args.where, tenantId };
  }
  return next(params);
};
```

### Pattern 4: Tenant Context Propagation
**When to use:** Maintaining tenant context across services
```typescript
class TenantContext {
  private static asyncLocalStorage = new AsyncLocalStorage<TenantContextData>();

  static run<T>(context: TenantContextData, fn: () => T): T {
    return this.asyncLocalStorage.run(context, fn);
  }

  static get(): TenantContextData | undefined {
    return this.asyncLocalStorage.getStore();
  }
}
```

## Best Practices
- Always validate tenant context
- Use connection pooling for database-per-tenant
- Implement tenant-aware caching
- Monitor per-tenant resource usage
