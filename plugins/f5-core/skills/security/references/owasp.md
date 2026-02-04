# OWASP Top 10 Prevention

XSS, SQL Injection, CSRF, and other OWASP vulnerability prevention patterns.

## Table of Contents

1. [Injection Prevention](#injection-prevention)
2. [XSS Prevention](#xss-prevention)
3. [CSRF Protection](#csrf-protection)
4. [Security Misconfiguration](#security-misconfiguration)
5. [Broken Authentication](#broken-authentication)
6. [Sensitive Data Exposure](#sensitive-data-exposure)

---

## Injection Prevention

### SQL Injection

```typescript
// VULNERABLE - Never do this
const query = `SELECT * FROM users WHERE id = '${userId}'`;

// SAFE - Parameterized queries
const query = 'SELECT * FROM users WHERE id = $1';
const result = await db.query(query, [userId]);

// SAFE - ORMs handle parameterization
const user = await prisma.user.findUnique({
  where: { id: userId }
});

// SAFE - Query builders
const user = await knex('users')
  .where('id', userId)
  .first();
```

### NoSQL Injection

```typescript
// VULNERABLE - Object injection
const user = await User.findOne({ email: req.body.email });

// If req.body.email = { $gt: "" }, returns first user!

// SAFE - Type validation
import { z } from 'zod';

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
});

const validated = loginSchema.parse(req.body);
const user = await User.findOne({ email: validated.email });

// SAFE - Explicit string conversion
const email = String(req.body.email);
const user = await User.findOne({ email });
```

### Command Injection

```typescript
// VULNERABLE - Shell execution with user input
const { exec } = require('child_process');
exec(`ls ${userInput}`, callback);

// If userInput = "; rm -rf /", disaster!

// SAFE - Use spawn with arguments array
import { spawn } from 'child_process';

const ls = spawn('ls', ['-la', sanitizedPath]);
ls.stdout.on('data', (data) => console.log(data));

// SAFE - Allowlist approach
const allowedCommands = ['list', 'status', 'info'];
if (!allowedCommands.includes(command)) {
  throw new Error('Invalid command');
}
```

### Path Traversal

```typescript
import path from 'path';

// VULNERABLE
const filePath = `/uploads/${req.params.filename}`;

// If filename = "../../../etc/passwd", exposes system files!

// SAFE - Validate and normalize path
function getSecurePath(filename: string, baseDir: string): string {
  const normalizedPath = path.normalize(filename);

  // Prevent path traversal
  if (normalizedPath.includes('..')) {
    throw new Error('Invalid path');
  }

  const fullPath = path.join(baseDir, normalizedPath);

  // Ensure path is within base directory
  if (!fullPath.startsWith(path.resolve(baseDir))) {
    throw new Error('Path traversal detected');
  }

  return fullPath;
}
```

---

## XSS Prevention

### Output Encoding

```typescript
// React - Auto-escapes by default
function Comment({ text }: { text: string }) {
  return <div>{text}</div>; // Safe - auto-escaped
}

// DANGEROUS - Bypass React's protection
function UnsafeComment({ html }: { html: string }) {
  return <div dangerouslySetInnerHTML={{ __html: html }} />; // XSS risk!
}

// SAFE - Sanitize if HTML is needed
import DOMPurify from 'dompurify';

function SafeHtmlComment({ html }: { html: string }) {
  const sanitized = DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p'],
    ALLOWED_ATTR: ['href', 'title'],
  });
  return <div dangerouslySetInnerHTML={{ __html: sanitized }} />;
}
```

### Content Security Policy

```typescript
import helmet from 'helmet';
import crypto from 'crypto';

// Generate nonce per request
app.use((req, res, next) => {
  res.locals.nonce = crypto.randomBytes(16).toString('base64');
  next();
});

app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: [
        "'self'",
        (req, res) => `'nonce-${res.locals.nonce}'`,
      ],
      styleSrc: ["'self'", "'unsafe-inline'"],
      imgSrc: ["'self'", "data:", "https:"],
      connectSrc: ["'self'", "https://api.example.com"],
      fontSrc: ["'self'", "https://fonts.gstatic.com"],
      objectSrc: ["'none'"],
      frameAncestors: ["'none'"],
      upgradeInsecureRequests: [],
    },
  },
}));

// In HTML templates
app.get('/', (req, res) => {
  res.render('index', { nonce: res.locals.nonce });
});
```

```html
<!-- Use nonce in script tags -->
<script nonce="<%= nonce %>">
  // Inline script allowed by CSP
</script>
```

### DOM-based XSS Prevention

```typescript
// VULNERABLE - Direct DOM manipulation
document.getElementById('output').innerHTML = userInput;

// SAFE - Use textContent for text
document.getElementById('output').textContent = userInput;

// SAFE - Create elements properly
const link = document.createElement('a');
link.href = sanitizeUrl(userUrl);
link.textContent = userText;
container.appendChild(link);

// URL sanitization
function sanitizeUrl(url: string): string {
  const parsed = new URL(url, window.location.origin);
  if (!['http:', 'https:'].includes(parsed.protocol)) {
    return '#'; // Block javascript:, data:, etc.
  }
  return parsed.href;
}
```

### Template Injection Prevention

```typescript
// Server-side template injection prevention
// VULNERABLE - User input in template
const template = `Hello ${req.query.name}!`;

// SAFE - Use template engine with auto-escaping
// EJS with auto-escaping
app.set('view engine', 'ejs');
res.render('greeting', { name: req.query.name });

// In greeting.ejs - auto-escaped
// <%= name %> - escaped
// <%- name %> - raw (avoid with user input)
```

---

## CSRF Protection

### Token-based Protection

```typescript
import csrf from 'csurf';
import cookieParser from 'cookie-parser';

app.use(cookieParser());
app.use(csrf({ cookie: true }));

// Generate token for forms
app.get('/form', (req, res) => {
  res.render('form', { csrfToken: req.csrfToken() });
});

// In HTML form
// <input type="hidden" name="_csrf" value="<%= csrfToken %>">

// Validate on POST
app.post('/submit', (req, res) => {
  // csrf middleware automatically validates
  // Throws 403 if invalid
});

// For SPAs - send token in header
app.get('/api/csrf-token', (req, res) => {
  res.json({ csrfToken: req.csrfToken() });
});

// Client-side
fetch('/api/submit', {
  method: 'POST',
  headers: {
    'CSRF-Token': csrfToken,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(data),
});
```

### SameSite Cookies

```typescript
// Session cookie with SameSite protection
app.use(session({
  cookie: {
    httpOnly: true,
    secure: true,
    sameSite: 'strict', // or 'lax' for navigation
    maxAge: 24 * 60 * 60 * 1000,
  },
}));

// Cookie options explained
const cookieOptions = {
  httpOnly: true,   // Not accessible via JavaScript
  secure: true,     // HTTPS only
  sameSite: 'strict', // Not sent with cross-site requests
  path: '/',
  domain: '.example.com',
};
```

### Double Submit Cookie

```typescript
// Alternative CSRF protection without server state
import crypto from 'crypto';

// Set CSRF cookie
app.use((req, res, next) => {
  if (!req.cookies.csrfToken) {
    const token = crypto.randomBytes(32).toString('hex');
    res.cookie('csrfToken', token, {
      httpOnly: false, // Accessible to JS
      secure: true,
      sameSite: 'strict',
    });
  }
  next();
});

// Validate token in header matches cookie
app.post('/api/*', (req, res, next) => {
  const cookieToken = req.cookies.csrfToken;
  const headerToken = req.headers['x-csrf-token'];

  if (!cookieToken || cookieToken !== headerToken) {
    return res.status(403).json({ error: 'Invalid CSRF token' });
  }
  next();
});
```

---

## Security Misconfiguration

### Error Handling

```typescript
// VULNERABLE - Exposes stack trace
app.use((err, req, res, next) => {
  res.status(500).json({ error: err.stack }); // Information disclosure!
});

// SAFE - Generic error in production
app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
  const errorId = crypto.randomUUID();

  // Log full error for debugging
  logger.error({
    errorId,
    message: err.message,
    stack: err.stack,
    url: req.url,
    method: req.method,
    userId: req.user?.id,
  });

  // Return generic message to client
  const isProduction = process.env.NODE_ENV === 'production';
  res.status(500).json({
    error: isProduction ? 'Internal server error' : err.message,
    errorId, // For support reference
  });
});
```

### Secure Headers

```typescript
import helmet from 'helmet';

app.use(helmet({
  // Prevent MIME sniffing
  noSniff: true,

  // Prevent clickjacking
  frameguard: { action: 'deny' },

  // XSS filter
  xssFilter: true,

  // Hide X-Powered-By
  hidePoweredBy: true,

  // HSTS
  hsts: {
    maxAge: 31536000,
    includeSubDomains: true,
    preload: true,
  },

  // Referrer policy
  referrerPolicy: { policy: 'strict-origin-when-cross-origin' },

  // Permissions policy
  permittedCrossDomainPolicies: { permittedPolicies: 'none' },
}));

// Additional headers
app.use((req, res, next) => {
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('X-Frame-Options', 'DENY');
  res.setHeader('Permissions-Policy', 'geolocation=(), microphone=()');
  next();
});
```

### Directory Listing Prevention

```typescript
import express from 'express';

// VULNERABLE - Shows directory contents
app.use(express.static('public'));

// SAFE - Disable directory listing
app.use(express.static('public', {
  index: false,
  dotfiles: 'deny',
}));

// Or use explicit routes only
app.get('/assets/:file', (req, res) => {
  const allowedFiles = ['style.css', 'app.js'];
  if (!allowedFiles.includes(req.params.file)) {
    return res.status(404).send('Not found');
  }
  res.sendFile(path.join(__dirname, 'public', req.params.file));
});
```

---

## Broken Authentication

### Secure Password Storage

```typescript
import bcrypt from 'bcrypt';

const SALT_ROUNDS = 12;

async function hashPassword(password: string): Promise<string> {
  return bcrypt.hash(password, SALT_ROUNDS);
}

async function verifyPassword(password: string, hash: string): Promise<boolean> {
  return bcrypt.compare(password, hash);
}

// Alternative: Argon2 (memory-hard)
import argon2 from 'argon2';

async function hashPasswordArgon2(password: string): Promise<string> {
  return argon2.hash(password, {
    type: argon2.argon2id,
    memoryCost: 65536, // 64 MB
    timeCost: 3,
    parallelism: 4,
  });
}
```

### Account Lockout

```typescript
interface LoginAttempt {
  count: number;
  lockedUntil: Date | null;
}

const loginAttempts = new Map<string, LoginAttempt>();
const MAX_ATTEMPTS = 5;
const LOCKOUT_DURATION = 15 * 60 * 1000; // 15 minutes

async function checkLoginAttempts(email: string): Promise<void> {
  const attempt = loginAttempts.get(email);

  if (attempt?.lockedUntil && attempt.lockedUntil > new Date()) {
    const remainingTime = Math.ceil(
      (attempt.lockedUntil.getTime() - Date.now()) / 1000 / 60
    );
    throw new Error(`Account locked. Try again in ${remainingTime} minutes`);
  }
}

async function recordFailedLogin(email: string): Promise<void> {
  const attempt = loginAttempts.get(email) || { count: 0, lockedUntil: null };
  attempt.count++;

  if (attempt.count >= MAX_ATTEMPTS) {
    attempt.lockedUntil = new Date(Date.now() + LOCKOUT_DURATION);
  }

  loginAttempts.set(email, attempt);
}

function clearLoginAttempts(email: string): void {
  loginAttempts.delete(email);
}
```

### Timing Attack Prevention

```typescript
import crypto from 'crypto';

// VULNERABLE - Early return reveals information
async function verifyApiKey(provided: string, stored: string): Promise<boolean> {
  return provided === stored; // Timing attack possible
}

// SAFE - Constant-time comparison
function secureCompare(a: string, b: string): boolean {
  const bufA = Buffer.from(a);
  const bufB = Buffer.from(b);

  if (bufA.length !== bufB.length) {
    // Compare against itself to maintain constant time
    crypto.timingSafeEqual(bufA, bufA);
    return false;
  }

  return crypto.timingSafeEqual(bufA, bufB);
}

// SAFE - Always verify password even if user not found
async function authenticate(email: string, password: string): Promise<User | null> {
  const user = await userRepository.findByEmail(email);

  // Always perform password check to prevent timing attacks
  const dummyHash = '$2b$12$dummy.hash.for.timing.attack.prevention';
  const hashToCheck = user?.passwordHash || dummyHash;

  const isValid = await bcrypt.compare(password, hashToCheck);

  if (!user || !isValid) {
    return null;
  }

  return user;
}
```

---

## Sensitive Data Exposure

### Data Masking

```typescript
// Mask sensitive data in logs and responses
function maskEmail(email: string): string {
  const [local, domain] = email.split('@');
  const masked = local.charAt(0) + '***' + local.charAt(local.length - 1);
  return `${masked}@${domain}`;
}

function maskCreditCard(number: string): string {
  return number.slice(-4).padStart(number.length, '*');
}

function maskPhone(phone: string): string {
  return phone.slice(-4).padStart(phone.length, '*');
}

// Logger that auto-masks sensitive fields
const sensitiveFields = ['password', 'ssn', 'creditCard', 'token'];

function sanitizeForLogging(obj: any): any {
  if (typeof obj !== 'object' || obj === null) return obj;

  const sanitized = { ...obj };
  for (const key of Object.keys(sanitized)) {
    if (sensitiveFields.some(f => key.toLowerCase().includes(f))) {
      sanitized[key] = '[REDACTED]';
    } else if (typeof sanitized[key] === 'object') {
      sanitized[key] = sanitizeForLogging(sanitized[key]);
    }
  }
  return sanitized;
}
```

### Secure Data Transmission

```typescript
// Force HTTPS
app.use((req, res, next) => {
  if (req.header('x-forwarded-proto') !== 'https') {
    return res.redirect(301, `https://${req.hostname}${req.url}`);
  }
  next();
});

// HSTS header
app.use(helmet.hsts({
  maxAge: 31536000, // 1 year
  includeSubDomains: true,
  preload: true,
}));

// Secure cookie transmission
app.use(session({
  cookie: {
    secure: true, // Only over HTTPS
    httpOnly: true,
    sameSite: 'strict',
  },
}));
```

### Response Sanitization

```typescript
// Remove sensitive fields from API responses
function sanitizeUserResponse(user: User): PublicUser {
  const { password, ssn, internalNotes, ...publicFields } = user;
  return publicFields;
}

// Class-transformer approach
import { Exclude, Expose } from 'class-transformer';

class UserResponse {
  @Expose()
  id: string;

  @Expose()
  email: string;

  @Expose()
  name: string;

  @Exclude()
  password: string;

  @Exclude()
  ssn: string;
}

// GraphQL field-level security
const resolvers = {
  User: {
    ssn: (parent, args, context) => {
      if (!context.user.isAdmin) {
        return null; // Hide from non-admins
      }
      return parent.ssn;
    },
  },
};
```

---

## Quick Reference

| Vulnerability | Primary Defense | Secondary Defense |
|---------------|-----------------|-------------------|
| SQL Injection | Parameterized queries | ORM/Query builders |
| NoSQL Injection | Schema validation | Type checking |
| XSS | Output encoding | CSP headers |
| CSRF | CSRF tokens | SameSite cookies |
| Command Injection | Avoid shell, use spawn | Input allowlisting |
| Path Traversal | Path normalization | Chroot/sandboxing |
| Broken Auth | Strong hashing | Account lockout |
| Data Exposure | Encryption | Data masking |

## Security Testing Checklist

```markdown
- [ ] SQL injection in all database queries
- [ ] NoSQL injection in document queries
- [ ] XSS in all user output points
- [ ] CSRF tokens on state-changing requests
- [ ] Path traversal in file operations
- [ ] Command injection in system calls
- [ ] Authentication bypass attempts
- [ ] Authorization checks on all endpoints
- [ ] Sensitive data in logs/errors
- [ ] Security headers configured
```
