---
name: shared-security-patterns
description: Common security patterns used across F5 Framework
category: shared
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Shared Security Patterns

## Input Validation

```typescript
// Always validate and sanitize input
const schema = z.object({
  email: z.string().email(),
  password: z.string().min(8).max(128),
});

const validated = schema.parse(input);
```

## Authentication Patterns

### JWT Token Structure
```typescript
interface JwtPayload {
  sub: string;      // User ID
  iat: number;      // Issued at
  exp: number;      // Expiration
  roles: string[];  // User roles
}
```

### Password Hashing
```typescript
// Use bcrypt with appropriate cost
const hash = await bcrypt.hash(password, 12);
const isValid = await bcrypt.compare(input, hash);
```

## Authorization Patterns

### Role-Based Access Control (RBAC)
```typescript
@Roles('admin', 'manager')
@UseGuards(JwtAuthGuard, RolesGuard)
async deleteUser(@Param('id') id: string) {
  // Only admin/manager can access
}
```

### Ownership Check
```typescript
if (resource.ownerId !== currentUser.id) {
  throw new ForbiddenException('Not owner');
}
```

## OWASP Top 10 Checklist

- [ ] A01: Broken Access Control
- [ ] A02: Cryptographic Failures
- [ ] A03: Injection
- [ ] A04: Insecure Design
- [ ] A05: Security Misconfiguration
- [ ] A06: Vulnerable Components
- [ ] A07: Authentication Failures
- [ ] A08: Integrity Failures
- [ ] A09: Logging Failures
- [ ] A10: SSRF

## Security Headers

```typescript
// Required headers
{
  'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
  'X-Content-Type-Options': 'nosniff',
  'X-Frame-Options': 'DENY',
  'X-XSS-Protection': '1; mode=block',
  'Content-Security-Policy': "default-src 'self'",
}
```

## Sensitive Data Handling

- Never log passwords/tokens
- Use parameterized queries
- Encrypt at rest and in transit
- Implement proper key rotation
- Use secrets manager for credentials
