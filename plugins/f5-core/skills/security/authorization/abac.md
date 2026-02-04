---
name: abac
description: Attribute-Based Access Control implementation
category: security/authorization
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Attribute-Based Access Control (ABAC)

## Overview

ABAC makes access decisions based on attributes of subjects, resources,
actions, and environment. More flexible than RBAC for complex scenarios.

## ABAC Model

```
┌─────────────────────────────────────────────────────────────┐
│                      ABAC Model                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Subject    │  │   Resource   │  │    Action    │      │
│  │  Attributes  │  │  Attributes  │  │  Attributes  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                 │                 │               │
│         └─────────────────┼─────────────────┘               │
│                           │                                 │
│                           v                                 │
│                  ┌──────────────┐                          │
│                  │    Policy    │                          │
│                  │    Engine    │                          │
│                  └──────────────┘                          │
│                           │                                 │
│                           v                                 │
│                  ┌──────────────┐                          │
│                  │   Decision   │                          │
│                  │ (Allow/Deny) │                          │
│                  └──────────────┘                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Attribute Types

| Type | Examples |
|------|----------|
| **Subject** | user.role, user.department, user.clearance_level |
| **Resource** | document.classification, order.status, data.owner |
| **Action** | read, write, delete, approve |
| **Environment** | time, location, device_type, ip_address |

## Policy Language

### Policy Definition

```typescript
// types/policy.types.ts
interface Policy {
  id: string;
  name: string;
  description: string;
  effect: 'allow' | 'deny';
  priority: number;
  conditions: Condition[];
  target?: Target;
}

interface Target {
  subjects?: SubjectMatch[];
  resources?: ResourceMatch[];
  actions?: string[];
}

interface Condition {
  attribute: string;
  operator: Operator;
  value: any;
}

type Operator =
  | 'equals'
  | 'not_equals'
  | 'in'
  | 'not_in'
  | 'greater_than'
  | 'less_than'
  | 'contains'
  | 'starts_with'
  | 'matches'; // regex

// Example policies
const policies: Policy[] = [
  {
    id: 'policy-1',
    name: 'Allow managers to approve orders',
    description: 'Managers can approve orders in their department',
    effect: 'allow',
    priority: 1,
    target: {
      actions: ['approve'],
      resources: [{ type: 'order' }],
    },
    conditions: [
      { attribute: 'subject.role', operator: 'equals', value: 'manager' },
      { attribute: 'subject.department', operator: 'equals', value: 'resource.department' },
    ],
  },
  {
    id: 'policy-2',
    name: 'Deny access outside business hours',
    description: 'Block access to sensitive resources outside 9-5',
    effect: 'deny',
    priority: 100, // High priority deny
    target: {
      resources: [{ classification: 'sensitive' }],
    },
    conditions: [
      { attribute: 'environment.hour', operator: 'not_in', value: [9, 10, 11, 12, 13, 14, 15, 16, 17] },
    ],
  },
  {
    id: 'policy-3',
    name: 'Allow document owner full access',
    description: 'Document owners can perform any action on their documents',
    effect: 'allow',
    priority: 1,
    target: {
      resources: [{ type: 'document' }],
    },
    conditions: [
      { attribute: 'subject.id', operator: 'equals', value: 'resource.ownerId' },
    ],
  },
];
```

### Policy Engine

```typescript
// services/abac.service.ts
export class ABACService {
  constructor(
    private policyRepository: PolicyRepository,
    private attributeResolver: AttributeResolver
  ) {}

  async evaluate(
    subject: Subject,
    resource: Resource,
    action: string,
    environment?: Environment
  ): Promise<Decision> {
    // Resolve all attributes
    const context: EvaluationContext = {
      subject: await this.attributeResolver.resolveSubject(subject),
      resource: await this.attributeResolver.resolveResource(resource),
      action,
      environment: environment || this.getEnvironmentContext(),
    };

    // Get applicable policies
    const policies = await this.policyRepository.findApplicable(context);

    // Sort by priority (lower = higher priority)
    policies.sort((a, b) => a.priority - b.priority);

    // Evaluate policies (deny-overrides algorithm)
    let finalDecision: Decision = { allowed: false, reason: 'No applicable policy' };

    for (const policy of policies) {
      const matches = this.evaluatePolicy(policy, context);

      if (matches) {
        if (policy.effect === 'deny') {
          return {
            allowed: false,
            reason: `Denied by policy: ${policy.name}`,
            policyId: policy.id,
          };
        }
        finalDecision = {
          allowed: true,
          reason: `Allowed by policy: ${policy.name}`,
          policyId: policy.id,
        };
      }
    }

    return finalDecision;
  }

  private evaluatePolicy(policy: Policy, context: EvaluationContext): boolean {
    // Check target (if specified)
    if (policy.target) {
      if (!this.matchesTarget(policy.target, context)) {
        return false;
      }
    }

    // Evaluate all conditions
    return policy.conditions.every(condition =>
      this.evaluateCondition(condition, context)
    );
  }

  private matchesTarget(target: Target, context: EvaluationContext): boolean {
    // Check action match
    if (target.actions && !target.actions.includes(context.action)) {
      return false;
    }

    // Check resource match
    if (target.resources) {
      const matchesResource = target.resources.some(resourceMatch =>
        Object.entries(resourceMatch).every(([key, value]) =>
          context.resource[key] === value
        )
      );
      if (!matchesResource) return false;
    }

    // Check subject match
    if (target.subjects) {
      const matchesSubject = target.subjects.some(subjectMatch =>
        Object.entries(subjectMatch).every(([key, value]) =>
          context.subject[key] === value
        )
      );
      if (!matchesSubject) return false;
    }

    return true;
  }

  private evaluateCondition(
    condition: Condition,
    context: EvaluationContext
  ): boolean {
    const actualValue = this.resolveAttribute(condition.attribute, context);
    let expectedValue = condition.value;

    // Resolve reference values (e.g., "resource.ownerId")
    if (typeof expectedValue === 'string' && expectedValue.includes('.')) {
      expectedValue = this.resolveAttribute(expectedValue, context);
    }

    return this.compare(actualValue, condition.operator, expectedValue);
  }

  private resolveAttribute(path: string, context: EvaluationContext): any {
    const parts = path.split('.');
    let value: any = context;

    for (const part of parts) {
      if (value === undefined || value === null) return undefined;
      value = value[part];
    }

    return value;
  }

  private compare(actual: any, operator: Operator, expected: any): boolean {
    switch (operator) {
      case 'equals':
        return actual === expected;
      case 'not_equals':
        return actual !== expected;
      case 'in':
        return Array.isArray(expected) && expected.includes(actual);
      case 'not_in':
        return Array.isArray(expected) && !expected.includes(actual);
      case 'greater_than':
        return actual > expected;
      case 'less_than':
        return actual < expected;
      case 'contains':
        return String(actual).includes(String(expected));
      case 'starts_with':
        return String(actual).startsWith(String(expected));
      case 'matches':
        return new RegExp(expected).test(String(actual));
      default:
        return false;
    }
  }

  private getEnvironmentContext(): Environment {
    const now = new Date();
    return {
      timestamp: now.toISOString(),
      hour: now.getHours(),
      dayOfWeek: now.getDay(),
      date: now.toISOString().split('T')[0],
    };
  }
}
```

### Middleware

```typescript
// middleware/abac.middleware.ts
export function abacAuthorize(resourceType: string, actionType: string) {
  return async (req: Request, res: Response, next: NextFunction) => {
    try {
      const subject: Subject = {
        id: req.user.id,
        type: 'user',
        ...req.user,
      };

      const resource: Resource = {
        type: resourceType,
        id: req.params.id,
        ...await loadResourceAttributes(resourceType, req.params.id),
      };

      const environment: Environment = {
        ipAddress: req.ip,
        userAgent: req.headers['user-agent'],
        ...abacService.getEnvironmentContext(),
      };

      const decision = await abacService.evaluate(
        subject,
        resource,
        actionType,
        environment
      );

      if (!decision.allowed) {
        return res.status(403).json({
          error: 'Access denied',
          reason: decision.reason,
        });
      }

      // Attach decision for audit logging
      req.authzDecision = decision;
      next();
    } catch (error) {
      next(error);
    }
  };
}

// Usage
router.post(
  '/orders/:id/approve',
  abacAuthorize('order', 'approve'),
  approveOrder
);
```

## Common ABAC Patterns

### Resource Ownership

```typescript
// Policy: Users can only access their own resources
{
  id: 'owner-access',
  name: 'Owner Access',
  effect: 'allow',
  conditions: [
    { attribute: 'subject.id', operator: 'equals', value: 'resource.ownerId' },
  ],
}
```

### Time-Based Access

```typescript
// Policy: Access only during business hours
{
  id: 'business-hours',
  name: 'Business Hours Only',
  effect: 'allow',
  conditions: [
    { attribute: 'environment.hour', operator: 'greater_than', value: 8 },
    { attribute: 'environment.hour', operator: 'less_than', value: 18 },
    { attribute: 'environment.dayOfWeek', operator: 'in', value: [1, 2, 3, 4, 5] },
  ],
}
```

### Location-Based Access

```typescript
// Policy: Sensitive data only from office IPs
{
  id: 'office-only',
  name: 'Office Network Only',
  effect: 'allow',
  target: {
    resources: [{ classification: 'sensitive' }],
  },
  conditions: [
    { attribute: 'environment.ipAddress', operator: 'starts_with', value: '192.168.' },
  ],
}
```

### Department Hierarchy

```typescript
// Policy: Managers can view reports from their department
{
  id: 'dept-reports',
  name: 'Department Reports Access',
  effect: 'allow',
  target: {
    actions: ['read'],
    resources: [{ type: 'report' }],
  },
  conditions: [
    { attribute: 'subject.role', operator: 'in', value: ['manager', 'director'] },
    { attribute: 'subject.department', operator: 'equals', value: 'resource.department' },
  ],
}
```

## RBAC vs ABAC Comparison

| Aspect | RBAC | ABAC |
|--------|------|------|
| Complexity | Simple | Complex |
| Flexibility | Limited | High |
| Maintenance | Easy | More effort |
| Performance | Fast | Slower |
| Use case | Static roles | Dynamic rules |
| Scalability | Role explosion | Attribute explosion |

## Hybrid Approach

```typescript
// Combine RBAC for coarse-grained, ABAC for fine-grained
async function authorize(subject, resource, action, environment) {
  // First check RBAC
  const rbacAllowed = await rbacService.hasPermission(
    subject.id,
    resource.type,
    action
  );

  if (!rbacAllowed) {
    return { allowed: false, reason: 'RBAC denied' };
  }

  // Then check ABAC for fine-grained control
  return abacService.evaluate(subject, resource, action, environment);
}
```

## Best Practices

| Practice | Description |
|----------|-------------|
| Start simple | Add complexity only when needed |
| Cache policies | Avoid loading policies on every request |
| Audit decisions | Log all authorization decisions |
| Test thoroughly | Unit test each policy |
| Version policies | Track policy changes over time |
| Default deny | Deny access unless explicitly allowed |
