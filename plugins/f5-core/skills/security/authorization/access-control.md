---
name: access-control
description: Access control patterns and implementations
category: security/authorization
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Access Control Patterns

## Overview

Access control determines who can access what resources and
what actions they can perform. Multiple patterns exist for
different security requirements.

## Access Control Models

```
┌─────────────────────────────────────────────────────────────┐
│               Access Control Models                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  DAC (Discretionary)                                        │
│  └── Resource owner controls access                         │
│                                                             │
│  MAC (Mandatory)                                            │
│  └── System enforces access based on labels                 │
│                                                             │
│  RBAC (Role-Based)                                          │
│  └── Access based on user roles                             │
│                                                             │
│  ABAC (Attribute-Based)                                     │
│  └── Access based on attributes of subject/resource         │
│                                                             │
│  ReBAC (Relationship-Based)                                 │
│  └── Access based on relationships between entities         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Discretionary Access Control (DAC)

### Implementation

```typescript
// models/resource.model.ts
interface Resource {
  id: string;
  ownerId: string;
  type: string;
  permissions: ResourcePermission[];
}

interface ResourcePermission {
  granteeId: string;      // User or group ID
  granteeType: 'user' | 'group';
  permissions: string[];  // ['read', 'write', 'delete']
  grantedAt: Date;
  grantedBy: string;
}

// services/dac.service.ts
export class DACService {
  async grantAccess(
    resourceId: string,
    granterId: string,
    granteeId: string,
    permissions: string[]
  ): Promise<void> {
    const resource = await this.resourceRepository.findById(resourceId);

    // Only owner can grant access
    if (resource.ownerId !== granterId) {
      throw new ForbiddenError('Only owner can grant access');
    }

    await this.resourceRepository.addPermission(resourceId, {
      granteeId,
      granteeType: 'user',
      permissions,
      grantedAt: new Date(),
      grantedBy: granterId,
    });
  }

  async checkAccess(
    resourceId: string,
    userId: string,
    action: string
  ): Promise<boolean> {
    const resource = await this.resourceRepository.findById(resourceId);

    // Owner has full access
    if (resource.ownerId === userId) {
      return true;
    }

    // Check explicit permissions
    const permission = resource.permissions.find(
      p => p.granteeId === userId && p.granteeType === 'user'
    );

    if (permission?.permissions.includes(action)) {
      return true;
    }

    // Check group permissions
    const userGroups = await this.groupService.getUserGroups(userId);
    for (const groupId of userGroups) {
      const groupPermission = resource.permissions.find(
        p => p.granteeId === groupId && p.granteeType === 'group'
      );
      if (groupPermission?.permissions.includes(action)) {
        return true;
      }
    }

    return false;
  }
}
```

## Relationship-Based Access Control (ReBAC)

### Google Zanzibar-Style Implementation

```typescript
// types/rebac.types.ts
interface RelationTuple {
  object: ObjectRef;     // e.g., doc:readme
  relation: string;      // e.g., viewer, editor, owner
  subject: SubjectRef;   // e.g., user:alice or group:engineering#member
}

interface ObjectRef {
  type: string;
  id: string;
}

interface SubjectRef {
  type: string;
  id: string;
  relation?: string;  // For userset rewrite
}

// Namespace definition (schema)
interface Namespace {
  name: string;
  relations: {
    [key: string]: RelationDefinition;
  };
}

interface RelationDefinition {
  union?: string[];      // Combine multiple relations
  intersection?: string[];
  exclusion?: { base: string; exclude: string };
  computed?: {
    relation: string;
    object: string;
  };
}

// Example: Document namespace
const documentNamespace: Namespace = {
  name: 'document',
  relations: {
    owner: {},
    editor: {
      union: ['owner'],  // owners are also editors
    },
    viewer: {
      union: ['editor'], // editors are also viewers
    },
    parent: {},
    // Inherit from parent folder
    inherited_viewer: {
      computed: {
        relation: 'viewer',
        object: 'parent',
      },
    },
  },
};

// services/rebac.service.ts
export class ReBACService {
  constructor(private tupleStore: TupleStore) {}

  // Write relation tuple
  async write(tuple: RelationTuple): Promise<void> {
    await this.tupleStore.write(tuple);
  }

  // Delete relation tuple
  async delete(tuple: RelationTuple): Promise<void> {
    await this.tupleStore.delete(tuple);
  }

  // Check if subject has relation to object
  async check(
    object: ObjectRef,
    relation: string,
    subject: SubjectRef
  ): Promise<boolean> {
    // Direct check
    const direct = await this.tupleStore.exists({
      object,
      relation,
      subject,
    });

    if (direct) return true;

    // Get namespace definition
    const namespace = await this.getNamespace(object.type);
    const relationDef = namespace.relations[relation];

    // Check union relations
    if (relationDef.union) {
      for (const rel of relationDef.union) {
        if (await this.check(object, rel, subject)) {
          return true;
        }
      }
    }

    // Check computed relations (inheritance)
    if (relationDef.computed) {
      const parentTuples = await this.tupleStore.find({
        object,
        relation: relationDef.computed.object,
      });

      for (const tuple of parentTuples) {
        const parentRef: ObjectRef = {
          type: tuple.subject.type,
          id: tuple.subject.id,
        };
        if (await this.check(parentRef, relationDef.computed.relation, subject)) {
          return true;
        }
      }
    }

    // Check group membership (userset rewrite)
    if (subject.type === 'group' && subject.relation) {
      const members = await this.tupleStore.find({
        object: { type: 'group', id: subject.id },
        relation: subject.relation,
      });

      for (const member of members) {
        if (await this.check(object, relation, member.subject)) {
          return true;
        }
      }
    }

    return false;
  }

  // List all subjects with relation to object
  async listSubjects(object: ObjectRef, relation: string): Promise<SubjectRef[]> {
    return this.tupleStore.findSubjects({ object, relation });
  }

  // List all objects subject has relation to
  async listObjects(
    subject: SubjectRef,
    relation: string,
    objectType: string
  ): Promise<ObjectRef[]> {
    return this.tupleStore.findObjects({ subject, relation, objectType });
  }
}
```

### Usage Example

```typescript
// Create document and set permissions
await rebac.write({
  object: { type: 'document', id: 'doc-123' },
  relation: 'owner',
  subject: { type: 'user', id: 'alice' },
});

// Share with team
await rebac.write({
  object: { type: 'document', id: 'doc-123' },
  relation: 'viewer',
  subject: { type: 'group', id: 'engineering', relation: 'member' },
});

// Check access
const canView = await rebac.check(
  { type: 'document', id: 'doc-123' },
  'viewer',
  { type: 'user', id: 'bob' }
);
```

## Access Control Lists (ACL)

```typescript
// types/acl.types.ts
interface ACLEntry {
  principal: string;        // user:alice, group:admins, role:editor
  principalType: 'user' | 'group' | 'role';
  permissions: Permission[];
  inherited: boolean;
  inheritedFrom?: string;
}

interface ACL {
  resourceId: string;
  entries: ACLEntry[];
  inheritFromParent: boolean;
}

// services/acl.service.ts
export class ACLService {
  async getEffectiveACL(resourceId: string): Promise<ACL> {
    const resource = await this.resourceRepository.findById(resourceId);
    let acl = await this.aclRepository.findByResourceId(resourceId);

    // Merge with inherited ACL
    if (acl.inheritFromParent && resource.parentId) {
      const parentACL = await this.getEffectiveACL(resource.parentId);
      const inheritedEntries = parentACL.entries.map(entry => ({
        ...entry,
        inherited: true,
        inheritedFrom: resource.parentId,
      }));

      // Merge: explicit entries override inherited
      acl = {
        ...acl,
        entries: [...inheritedEntries, ...acl.entries],
      };
    }

    return acl;
  }

  async checkPermission(
    resourceId: string,
    principalId: string,
    permission: string
  ): Promise<boolean> {
    const acl = await this.getEffectiveACL(resourceId);
    const principals = await this.expandPrincipals(principalId);

    for (const entry of acl.entries) {
      if (principals.includes(entry.principal)) {
        if (entry.permissions.some(p => p.name === permission && p.allowed)) {
          return true;
        }
      }
    }

    return false;
  }

  // Expand user to include groups and roles
  private async expandPrincipals(userId: string): Promise<string[]> {
    const principals = [`user:${userId}`];

    const groups = await this.groupService.getUserGroups(userId);
    principals.push(...groups.map(g => `group:${g}`));

    const roles = await this.roleService.getUserRoles(userId);
    principals.push(...roles.map(r => `role:${r}`));

    return principals;
  }
}
```

## Row-Level Security

```typescript
// Row-level security using database policies
// PostgreSQL RLS Example

/*
-- Enable RLS on table
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- Policy: Users can see their own documents
CREATE POLICY documents_owner_policy ON documents
  FOR ALL
  USING (owner_id = current_user_id());

-- Policy: Users can see documents shared with them
CREATE POLICY documents_shared_policy ON documents
  FOR SELECT
  USING (
    id IN (
      SELECT document_id FROM document_shares
      WHERE user_id = current_user_id()
    )
  );

-- Policy: Admins can see all documents
CREATE POLICY documents_admin_policy ON documents
  FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM user_roles
      WHERE user_id = current_user_id()
      AND role = 'admin'
    )
  );
*/

// Application-level RLS
export class QueryBuilder {
  constructor(
    private user: User,
    private permissionService: PermissionService
  ) {}

  async buildQuery(baseQuery: Query): Promise<Query> {
    const filters: QueryFilter[] = [];

    // Check if user has full access
    if (await this.permissionService.hasPermission(this.user.id, 'documents:read:all')) {
      return baseQuery;
    }

    // Add ownership filter
    if (await this.permissionService.hasPermission(this.user.id, 'documents:read:own')) {
      filters.push({ field: 'ownerId', operator: 'eq', value: this.user.id });
    }

    // Add department filter
    if (await this.permissionService.hasPermission(this.user.id, 'documents:read:department')) {
      filters.push({ field: 'departmentId', operator: 'eq', value: this.user.departmentId });
    }

    // Add shared with filter
    filters.push({
      field: 'id',
      operator: 'in',
      subquery: `SELECT document_id FROM shares WHERE user_id = '${this.user.id}'`,
    });

    // Combine with OR
    return baseQuery.where({ or: filters });
  }
}
```

## Multi-Tenancy Access Control

```typescript
// Tenant isolation
export class TenantAccessControl {
  async validateTenantAccess(userId: string, resourceId: string): Promise<void> {
    const user = await this.userRepository.findById(userId);
    const resource = await this.resourceRepository.findById(resourceId);

    if (user.tenantId !== resource.tenantId) {
      throw new ForbiddenError('Cross-tenant access denied');
    }
  }

  // Middleware for tenant isolation
  tenantMiddleware() {
    return async (req: Request, res: Response, next: NextFunction) => {
      const tenantId = req.user?.tenantId;
      if (!tenantId) {
        return res.status(403).json({ error: 'Tenant context required' });
      }

      // Add tenant filter to all queries
      req.tenantScope = { tenantId };
      next();
    };
  }
}
```

## Best Practices

| Practice | Description |
|----------|-------------|
| Defense in depth | Combine multiple access control layers |
| Fail secure | Deny access by default |
| Least privilege | Grant minimum necessary access |
| Separation of duties | Critical actions require multiple authorizations |
| Audit everything | Log all access decisions |
| Regular review | Periodically audit permissions |
