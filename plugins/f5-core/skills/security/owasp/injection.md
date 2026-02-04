---
name: injection-prevention
description: Preventing SQL injection and other injection attacks
category: security/owasp
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Injection Prevention

## Overview

Injection attacks occur when untrusted data is sent to an interpreter
as part of a command or query. SQL injection is most common.

## Injection Types

| Type | Target | Example |
|------|--------|---------|
| SQL Injection | Database | `' OR '1'='1` |
| NoSQL Injection | MongoDB, etc. | `{"$gt": ""}` |
| Command Injection | OS shell | `; rm -rf /` |
| LDAP Injection | Directory services | `*)(uid=*))(|(uid=*` |
| XPath Injection | XML queries | `' or '1'='1` |
| Template Injection | Template engines | `{{constructor.constructor('return process')()}}` |

## SQL Injection Prevention

### Vulnerable Code

```typescript
// ❌ NEVER do this!
async function getUser(userId: string) {
  const query = `SELECT * FROM users WHERE id = '${userId}'`;
  return db.query(query);
}

// Attacker input: "1' OR '1'='1"
// Resulting query: SELECT * FROM users WHERE id = '1' OR '1'='1'
// Returns ALL users!

// Attacker input: "1'; DROP TABLE users;--"
// Resulting query: SELECT * FROM users WHERE id = '1'; DROP TABLE users;--'
// Deletes the table!
```

### Parameterized Queries

```typescript
// ✅ PostgreSQL with pg
async function getUser(userId: string) {
  const query = 'SELECT * FROM users WHERE id = $1';
  return db.query(query, [userId]);
}

// ✅ MySQL with mysql2
async function getUser(userId: string) {
  const query = 'SELECT * FROM users WHERE id = ?';
  return db.execute(query, [userId]);
}

// ✅ Prisma ORM (safe by default)
async function getUser(userId: string) {
  return prisma.user.findUnique({
    where: { id: userId }
  });
}

// ✅ TypeORM (use query builder)
async function getUser(userId: string) {
  return userRepository
    .createQueryBuilder('user')
    .where('user.id = :id', { id: userId })
    .getOne();
}

// ✅ Knex.js
async function getUser(userId: string) {
  return knex('users')
    .where('id', userId)
    .first();
}
```

### Safe Dynamic Queries

```typescript
// Building queries with dynamic conditions
interface UserFilter {
  name?: string;
  email?: string;
  status?: string;
  role?: string;
}

function buildUserQuery(filter: UserFilter) {
  const conditions: string[] = [];
  const params: any[] = [];
  let paramIndex = 1;

  if (filter.name) {
    conditions.push(`name ILIKE $${paramIndex++}`);
    params.push(`%${filter.name}%`);
  }

  if (filter.email) {
    conditions.push(`email = $${paramIndex++}`);
    params.push(filter.email);
  }

  if (filter.status) {
    // Whitelist allowed values
    const allowedStatuses = ['active', 'inactive', 'pending'];
    if (!allowedStatuses.includes(filter.status)) {
      throw new Error('Invalid status');
    }
    conditions.push(`status = $${paramIndex++}`);
    params.push(filter.status);
  }

  if (filter.role) {
    // Whitelist allowed values
    const allowedRoles = ['admin', 'user', 'manager'];
    if (!allowedRoles.includes(filter.role)) {
      throw new Error('Invalid role');
    }
    conditions.push(`role = $${paramIndex++}`);
    params.push(filter.role);
  }

  const whereClause = conditions.length > 0
    ? `WHERE ${conditions.join(' AND ')}`
    : '';

  return {
    query: `SELECT * FROM users ${whereClause}`,
    params,
  };
}

// Safe ORDER BY with whitelist
function buildOrderBy(field: string, direction: string): string {
  const allowedFields = ['name', 'email', 'created_at', 'updated_at'];
  const allowedDirections = ['ASC', 'DESC'];

  if (!allowedFields.includes(field)) {
    field = 'created_at'; // Default
  }

  if (!allowedDirections.includes(direction.toUpperCase())) {
    direction = 'DESC'; // Default
  }

  return `ORDER BY ${field} ${direction}`;
}
```

## NoSQL Injection Prevention

### MongoDB

```typescript
// ❌ Vulnerable
async function findUser(query: any) {
  return User.find(query); // Attacker can inject operators!
}

// Attacker sends: { "$gt": "" }
// Matches all documents!

// ✅ Safe - validate and sanitize
import mongoSanitize from 'express-mongo-sanitize';

// Middleware to strip $ and . from req.body/query/params
app.use(mongoSanitize());

async function findUser(email: string) {
  // Explicitly specify field
  return User.findOne({ email: email });
}

// ✅ Safe - use schema validation
const userSchema = new Schema({
  email: {
    type: String,
    validate: {
      validator: (v: string) => /^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$/.test(v),
      message: 'Invalid email format'
    }
  }
});

// ✅ Safe - sanitize input manually
function sanitizeInput(input: any): any {
  if (typeof input === 'object' && input !== null) {
    for (const key of Object.keys(input)) {
      if (key.startsWith('$') || key.includes('.')) {
        delete input[key];
      } else {
        input[key] = sanitizeInput(input[key]);
      }
    }
  }
  return input;
}
```

## Command Injection Prevention

```typescript
// ❌ NEVER execute user input as command
import { exec } from 'child_process';

function dangerous(userInput: string) {
  exec(`ls ${userInput}`); // Command injection!
}
// Attacker: "; rm -rf /"

// ✅ Use execFile with arguments array
import { execFile } from 'child_process';

function safe(filename: string) {
  // Validate filename first
  if (!/^[\w\-\.]+$/.test(filename)) {
    throw new Error('Invalid filename');
  }

  execFile('ls', ['-la', filename], (error, stdout) => {
    // Handle output
  });
}

// ✅ Even better - avoid shell entirely
import { readdir, stat } from 'fs/promises';
import path from 'path';

async function listFiles(directory: string) {
  // Validate path (prevent path traversal)
  const basePath = '/allowed/base/path';
  const safePath = path.resolve(basePath, directory);

  if (!safePath.startsWith(basePath)) {
    throw new Error('Path traversal attempt');
  }

  return readdir(safePath);
}

// ✅ If shell is needed, use allowlist
function runAllowedCommand(command: string, args: string[]) {
  const allowedCommands = ['ls', 'pwd', 'whoami'];

  if (!allowedCommands.includes(command)) {
    throw new Error('Command not allowed');
  }

  // Validate args
  for (const arg of args) {
    if (!/^[\w\-\.\/]+$/.test(arg)) {
      throw new Error('Invalid argument');
    }
  }

  execFile(command, args);
}
```

## LDAP Injection Prevention

```typescript
// ❌ Vulnerable
function findUser(username: string) {
  const filter = `(uid=${username})`;
  return ldap.search(filter);
}
// Attacker: "*)(uid=*))(|(uid=*"

// ✅ Safe - escape special characters
function escapeLdap(input: string): string {
  return input
    .replace(/\\/g, '\\5c')
    .replace(/\*/g, '\\2a')
    .replace(/\(/g, '\\28')
    .replace(/\)/g, '\\29')
    .replace(/\x00/g, '\\00')
    .replace(/\//g, '\\2f');
}

function findUser(username: string) {
  const safeUsername = escapeLdap(username);
  const filter = `(uid=${safeUsername})`;
  return ldap.search(filter);
}
```

## Template Injection Prevention

```typescript
// ❌ Vulnerable - user input in template
function renderTemplate(userInput: string) {
  return nunjucks.renderString(userInput, data);
}
// Attacker: {{constructor.constructor('return process')()}}

// ✅ Safe - use templates from files only
function renderTemplate(templateName: string, data: object) {
  // Whitelist templates
  const allowedTemplates = ['welcome', 'invoice', 'notification'];
  if (!allowedTemplates.includes(templateName)) {
    throw new Error('Invalid template');
  }

  return nunjucks.render(`${templateName}.html`, data);
}

// ✅ Safe - sanitize user data passed to templates
function renderWithUserData(templateName: string, userData: any) {
  const sanitizedData = {
    name: escapeHtml(userData.name),
    email: escapeHtml(userData.email),
    // Only pass expected fields
  };

  return nunjucks.render(`${templateName}.html`, sanitizedData);
}
```

## Input Validation Layer

```typescript
// validation/user.validation.ts
import { z } from 'zod';

export const createUserSchema = z.object({
  name: z.string()
    .min(1)
    .max(100)
    .regex(/^[a-zA-Z\s\-']+$/, 'Invalid characters in name'),

  email: z.string()
    .email()
    .max(255)
    .toLowerCase(),

  password: z.string()
    .min(8)
    .max(128)
    .regex(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/, 'Weak password'),

  role: z.enum(['user', 'admin', 'moderator']),

  age: z.number()
    .int()
    .min(0)
    .max(150)
    .optional(),
});

// Use in controller
async function createUser(req: Request, res: Response) {
  const validatedData = createUserSchema.parse(req.body);
  // Now safe to use
  const user = await userService.create(validatedData);
  return res.json(user);
}
```

## Defense in Depth

```
┌─────────────────────────────────────────────────────┐
│                    WAF (Web Application Firewall)    │
├─────────────────────────────────────────────────────┤
│                    Input Validation                  │
├─────────────────────────────────────────────────────┤
│                    Parameterized Queries             │
├─────────────────────────────────────────────────────┤
│                    Least Privilege DB User           │
├─────────────────────────────────────────────────────┤
│                    Monitoring & Alerting             │
└─────────────────────────────────────────────────────┘
```

## Best Practices

| Practice | Description |
|----------|-------------|
| Use parameterized queries | Always use prepared statements |
| Validate input | Whitelist allowed characters/values |
| Escape output | Context-appropriate escaping |
| Least privilege | Minimal database permissions |
| Error handling | Don't expose SQL errors to users |
| Monitoring | Log and alert on suspicious queries |
