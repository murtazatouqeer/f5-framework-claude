---
name: headers-security
description: HTTP security headers configuration
category: security/infrastructure
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# HTTP Security Headers

## Overview

Security headers instruct browsers to enable security features
and protect against common web vulnerabilities.

## Essential Headers

| Header | Purpose | Priority |
|--------|---------|----------|
| Content-Security-Policy | XSS protection | Critical |
| Strict-Transport-Security | Force HTTPS | Critical |
| X-Content-Type-Options | MIME sniffing | High |
| X-Frame-Options | Clickjacking | High |
| Referrer-Policy | Privacy | Medium |
| Permissions-Policy | Feature control | Medium |

## Implementation with Helmet

```typescript
// middleware/security-headers.ts
import helmet from 'helmet';

// Full helmet configuration
app.use(helmet({
  // Content Security Policy
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'", "'strict-dynamic'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      imgSrc: ["'self'", "data:", "https:"],
      fontSrc: ["'self'", "https://fonts.gstatic.com"],
      connectSrc: ["'self'", "https://api.example.com"],
      frameSrc: ["'none'"],
      objectSrc: ["'none'"],
      baseUri: ["'self'"],
      formAction: ["'self'"],
      frameAncestors: ["'none'"],
      upgradeInsecureRequests: [],
    },
    reportOnly: false,
  },

  // Cross-Origin Embedder Policy
  crossOriginEmbedderPolicy: { policy: "require-corp" },

  // Cross-Origin Opener Policy
  crossOriginOpenerPolicy: { policy: "same-origin" },

  // Cross-Origin Resource Policy
  crossOriginResourcePolicy: { policy: "same-origin" },

  // DNS Prefetch Control
  dnsPrefetchControl: { allow: false },

  // Frameguard (X-Frame-Options)
  frameguard: { action: "deny" },

  // Hide X-Powered-By
  hidePoweredBy: true,

  // HSTS
  hsts: {
    maxAge: 31536000,
    includeSubDomains: true,
    preload: true,
  },

  // IE No Open
  ieNoOpen: true,

  // No Sniff (X-Content-Type-Options)
  noSniff: true,

  // Origin Agent Cluster
  originAgentCluster: true,

  // Permitted Cross-Domain Policies
  permittedCrossDomainPolicies: { permittedPolicies: "none" },

  // Referrer Policy
  referrerPolicy: { policy: "strict-origin-when-cross-origin" },

  // X-XSS-Protection (legacy, but still useful)
  xssFilter: true,
}));
```

## Content Security Policy (CSP)

### Basic CSP

```typescript
// Strict CSP for simple apps
app.use(helmet.contentSecurityPolicy({
  directives: {
    defaultSrc: ["'self'"],
    scriptSrc: ["'self'"],
    styleSrc: ["'self'"],
    imgSrc: ["'self'"],
    fontSrc: ["'self'"],
    objectSrc: ["'none'"],
    frameAncestors: ["'none'"],
  },
}));
```

### CSP with Nonces

```typescript
// Generate nonce per request
import crypto from 'crypto';

app.use((req, res, next) => {
  res.locals.nonce = crypto.randomBytes(16).toString('base64');
  next();
});

// CSP with nonce
app.use((req, res, next) => {
  const nonce = res.locals.nonce;

  res.setHeader('Content-Security-Policy', [
    `default-src 'self'`,
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'`,
    `style-src 'self' 'nonce-${nonce}'`,
    `img-src 'self' data: https:`,
    `font-src 'self'`,
    `object-src 'none'`,
    `base-uri 'self'`,
    `form-action 'self'`,
    `frame-ancestors 'none'`,
    `upgrade-insecure-requests`,
  ].join('; '));

  next();
});

// In template (EJS example)
// <script nonce="<%= nonce %>">
//   // Your inline script
// </script>
```

### CSP Reporting

```typescript
// Enable CSP reporting
app.use(helmet.contentSecurityPolicy({
  directives: {
    // ... other directives
    reportUri: '/csp-report',
  },
}));

// Report endpoint
app.post('/csp-report',
  express.json({ type: 'application/csp-report' }),
  (req, res) => {
    console.log('CSP Violation:', req.body['csp-report']);

    // Log to monitoring service
    // logService.log('csp_violation', req.body);

    res.status(204).end();
  }
);

// Report-Only mode for testing
app.use(helmet.contentSecurityPolicy({
  directives: {
    // ... directives
  },
  reportOnly: true, // Don't block, just report
}));
```

## Permissions Policy

```typescript
// Control browser features
app.use((req, res, next) => {
  res.setHeader('Permissions-Policy', [
    'accelerometer=()',
    'ambient-light-sensor=()',
    'autoplay=(self)',
    'battery=()',
    'camera=()',
    'display-capture=()',
    'document-domain=()',
    'encrypted-media=(self)',
    'fullscreen=(self)',
    'geolocation=()',
    'gyroscope=()',
    'layout-animations=(self)',
    'legacy-image-formats=(self)',
    'magnetometer=()',
    'microphone=()',
    'midi=()',
    'navigation-override=()',
    'oversized-images=(self)',
    'payment=()',
    'picture-in-picture=(self)',
    'publickey-credentials-get=(self)',
    'speaker-selection=()',
    'sync-xhr=()',
    'unoptimized-images=()',
    'unsized-media=(self)',
    'usb=()',
    'web-share=(self)',
    'xr-spatial-tracking=()',
  ].join(', '));

  next();
});
```

## Cross-Origin Headers

```typescript
// Cross-Origin headers for enhanced security
app.use((req, res, next) => {
  // Cross-Origin-Opener-Policy
  // Prevents other windows from accessing your window
  res.setHeader('Cross-Origin-Opener-Policy', 'same-origin');

  // Cross-Origin-Embedder-Policy
  // Requires resources to explicitly allow embedding
  res.setHeader('Cross-Origin-Embedder-Policy', 'require-corp');

  // Cross-Origin-Resource-Policy
  // Controls who can load your resources
  res.setHeader('Cross-Origin-Resource-Policy', 'same-origin');

  next();
});

// For resources that need to be embedded cross-origin
app.get('/public-resource', (req, res) => {
  res.setHeader('Cross-Origin-Resource-Policy', 'cross-origin');
  // ... serve resource
});
```

## Cache Control Headers

```typescript
// Prevent caching of sensitive responses
app.use('/api', (req, res, next) => {
  res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate, proxy-revalidate');
  res.setHeader('Pragma', 'no-cache');
  res.setHeader('Expires', '0');
  res.setHeader('Surrogate-Control', 'no-store');
  next();
});

// Allow caching for static assets
app.use('/static', express.static('public', {
  setHeaders: (res, path) => {
    if (path.endsWith('.js') || path.endsWith('.css')) {
      res.setHeader('Cache-Control', 'public, max-age=31536000, immutable');
    }
  },
}));
```

## Nginx Security Headers

```nginx
# /etc/nginx/conf.d/security-headers.conf

# Add headers to all responses
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "DENY" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;

# HSTS (only on HTTPS)
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

# CSP
add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'self'; form-action 'self';" always;

# Remove server info
server_tokens off;
more_clear_headers Server;
```

## Header Validation

```typescript
// Test security headers
import fetch from 'node-fetch';

async function validateSecurityHeaders(url: string) {
  const response = await fetch(url);
  const headers = response.headers;

  const required = {
    'strict-transport-security': /max-age=\d+/,
    'x-content-type-options': 'nosniff',
    'x-frame-options': /(DENY|SAMEORIGIN)/,
    'content-security-policy': /.+/,
    'referrer-policy': /.+/,
  };

  const results: { header: string; status: string; value?: string }[] = [];

  for (const [header, pattern] of Object.entries(required)) {
    const value = headers.get(header);

    if (!value) {
      results.push({ header, status: 'MISSING' });
    } else if (pattern instanceof RegExp ? !pattern.test(value) : value !== pattern) {
      results.push({ header, status: 'INVALID', value });
    } else {
      results.push({ header, status: 'OK', value });
    }
  }

  return results;
}
```

## Best Practices

| Practice | Description |
|----------|-------------|
| Start strict | Begin with restrictive policies |
| Use Report-Only | Test CSP before enforcing |
| Avoid unsafe | Minimize 'unsafe-inline' and 'unsafe-eval' |
| Use nonces | For inline scripts/styles |
| Monitor reports | Track CSP violations |
| Regular audits | Test headers periodically |
