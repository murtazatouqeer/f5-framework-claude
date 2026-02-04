---
name: xss-prevention
description: Cross-Site Scripting prevention techniques
category: security/owasp
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# XSS Prevention

## Types of XSS

| Type | Description | Example |
|------|-------------|---------|
| **Stored** | Malicious script stored in database | Forum post with `<script>` |
| **Reflected** | Script in URL reflected back | Search query `?q=<script>` |
| **DOM-based** | Script manipulates client-side DOM | `location.hash` injection |

## Output Encoding

### HTML Context

```typescript
// ❌ Vulnerable
function renderComment(comment: string) {
  return `<div class="comment">${comment}</div>`;
}
// Attacker: <script>alert('xss')</script>

// ✅ Safe - encode HTML entities
import { encode } from 'html-entities';

function renderComment(comment: string) {
  return `<div class="comment">${encode(comment)}</div>`;
}
// Output: &lt;script&gt;alert('xss')&lt;/script&gt;

// ✅ Using template engines (auto-escape)
// EJS: <%= comment %> (escapes by default)
// Handlebars: {{comment}} (escapes by default)
// Pug: #{comment} (escapes by default)
// React: {comment} (escapes by default)

// Manual HTML encoding
function escapeHtml(unsafe: string): string {
  return unsafe
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
```

### JavaScript Context

```typescript
// ❌ Vulnerable
function setUsername(name: string) {
  return `<script>var username = "${name}";</script>`;
}
// Attacker: "; alert('xss'); "

// ✅ Safe - JSON encode for JS context
function setUsername(name: string) {
  const safeName = JSON.stringify(name);
  return `<script>var username = ${safeName};</script>`;
}

// ✅ Better - use data attributes
function setUsername(name: string) {
  return `<div id="user" data-name="${escapeHtml(name)}"></div>
          <script>var username = document.getElementById('user').dataset.name;</script>`;
}
```

### URL Context

```typescript
// ❌ Vulnerable
function createLink(url: string) {
  return `<a href="${url}">Click</a>`;
}
// Attacker: javascript:alert('xss')

// ✅ Safe - validate URL scheme
function createLink(url: string) {
  try {
    const parsed = new URL(url);
    if (!['http:', 'https:'].includes(parsed.protocol)) {
      throw new Error('Invalid URL scheme');
    }
    return `<a href="${encodeURI(url)}">Click</a>`;
  } catch {
    return `<span>Invalid URL</span>`;
  }
}

// ✅ Safe URL in query parameter
function createSearchLink(query: string) {
  const safeQuery = encodeURIComponent(query);
  return `<a href="/search?q=${safeQuery}">Search</a>`;
}
```

### CSS Context

```typescript
// ❌ Vulnerable
function setColor(color: string) {
  return `<div style="color: ${color}">Text</div>`;
}
// Attacker: red; background: url('javascript:...')

// ✅ Safe - whitelist allowed values
const allowedColors = ['red', 'blue', 'green', 'black', 'white'];

function setColor(color: string) {
  if (!allowedColors.includes(color)) {
    color = 'black';
  }
  return `<div style="color: ${color}">Text</div>`;
}

// ✅ Safe - use CSS custom properties
function setThemeColor(color: string) {
  // Validate hex color
  if (!/^#[0-9a-fA-F]{6}$/.test(color)) {
    color = '#000000';
  }
  return `<div style="--theme-color: ${color}">Text</div>`;
}
```

## Content Security Policy (CSP)

### Implementation

```typescript
// middleware/csp.middleware.ts
import helmet from 'helmet';

app.use(helmet.contentSecurityPolicy({
  directives: {
    defaultSrc: ["'self'"],
    scriptSrc: [
      "'self'",
      "'strict-dynamic'",  // Allow trusted scripts to load others
      // Avoid 'unsafe-inline' if possible
      // Use nonce or hash for inline scripts
    ],
    scriptSrcAttr: ["'none'"],           // No inline event handlers
    styleSrc: ["'self'", "'unsafe-inline'"], // Often needed for CSS
    imgSrc: ["'self'", "data:", "https:"],
    fontSrc: ["'self'", "https://fonts.gstatic.com"],
    connectSrc: ["'self'", "https://api.example.com"],
    frameSrc: ["'none'"],                // No iframes
    objectSrc: ["'none'"],               // No plugins
    baseUri: ["'self'"],                 // Prevent base tag hijacking
    formAction: ["'self'"],              // Form submissions only to self
    frameAncestors: ["'none'"],          // Prevent framing (clickjacking)
    upgradeInsecureRequests: [],         // Upgrade HTTP to HTTPS
    blockAllMixedContent: [],            // Block mixed content
  },
  reportOnly: false,
  reportUri: '/csp-report',
}));

// CSP violation reporting endpoint
app.post('/csp-report', express.json({ type: 'application/csp-report' }), (req, res) => {
  console.log('CSP Violation:', req.body['csp-report']);
  // Log to monitoring system
  res.status(204).end();
});
```

### CSP with Nonces

```typescript
// Generate nonce per request
import crypto from 'crypto';

app.use((req, res, next) => {
  res.locals.nonce = crypto.randomBytes(16).toString('base64');
  next();
});

app.use(helmet.contentSecurityPolicy({
  directives: {
    scriptSrc: ["'self'", (req, res) => `'nonce-${res.locals.nonce}'`],
  },
}));

// In template
app.get('/', (req, res) => {
  res.render('index', { nonce: res.locals.nonce });
});

// index.ejs
// <script nonce="<%= nonce %>">
//   // Inline script allowed with matching nonce
// </script>
```

## React XSS Prevention

```tsx
// ✅ Safe by default - React escapes automatically
function Comment({ text }: { text: string }) {
  return <div>{text}</div>;
}

// ❌ Dangerous - bypasses escaping
function Comment({ html }: { html: string }) {
  return <div dangerouslySetInnerHTML={{ __html: html }} />;
}

// ✅ If HTML is needed, sanitize first
import DOMPurify from 'dompurify';

function SafeHtml({ html }: { html: string }) {
  const sanitized = DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'br', 'ul', 'ol', 'li'],
    ALLOWED_ATTR: ['href', 'target', 'rel'],
    ALLOW_DATA_ATTR: false,
  });
  return <div dangerouslySetInnerHTML={{ __html: sanitized }} />;
}

// ✅ Safe URL handling in React
function UserLink({ url }: { url: string }) {
  const isSafe = url.startsWith('https://') || url.startsWith('http://');
  if (!isSafe) return null;

  return (
    <a
      href={url}
      rel="noopener noreferrer"
      target="_blank"
    >
      {url}
    </a>
  );
}

// ✅ Safe dynamic styles
function UserAvatar({ color }: { color: string }) {
  // Validate color
  const safeColor = /^#[0-9a-fA-F]{6}$/.test(color) ? color : '#cccccc';

  return (
    <div
      style={{
        backgroundColor: safeColor,
        // React escapes style values automatically
      }}
    />
  );
}
```

## DOM-based XSS Prevention

```typescript
// ❌ Vulnerable DOM manipulation
document.getElementById('output').innerHTML = location.hash.substring(1);

// ✅ Safe - use textContent
document.getElementById('output').textContent = location.hash.substring(1);

// ✅ Safe - use DOM APIs
const element = document.createElement('div');
element.textContent = userInput;
container.appendChild(element);

// ❌ Vulnerable eval
eval(userInput);

// ❌ Vulnerable setTimeout/setInterval with string
setTimeout(userInput, 1000);

// ✅ Safe - use function
setTimeout(() => {
  // Safe code here
}, 1000);

// ❌ Vulnerable document.write
document.write(userInput);

// ✅ Safe - manipulate DOM
document.body.appendChild(document.createTextNode(userInput));

// ❌ Vulnerable jQuery
$('#output').html(userInput);

// ✅ Safe jQuery
$('#output').text(userInput);

// Safe URL handling
function safeRedirect(url: string) {
  try {
    const parsed = new URL(url, window.location.origin);
    // Only allow same-origin redirects
    if (parsed.origin === window.location.origin) {
      window.location.href = parsed.href;
    }
  } catch {
    console.error('Invalid URL');
  }
}
```

## HTML Sanitization

```typescript
// services/sanitizer.service.ts
import DOMPurify from 'dompurify';
import { JSDOM } from 'jsdom';

// Server-side DOMPurify
const window = new JSDOM('').window;
const purify = DOMPurify(window);

// Preset configurations
const sanitizeConfigs = {
  // Allow only basic formatting
  basic: {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'br'],
    ALLOWED_ATTR: [],
  },

  // Allow formatting and links
  withLinks: {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'br', 'p'],
    ALLOWED_ATTR: ['href', 'target', 'rel'],
    ADD_ATTR: ['target', 'rel'],
    FORCE_BODY: true,
  },

  // Rich text (blog posts, etc.)
  richText: {
    ALLOWED_TAGS: [
      'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
      'p', 'br', 'hr',
      'b', 'i', 'em', 'strong', 'u', 's',
      'a', 'img',
      'ul', 'ol', 'li',
      'blockquote', 'pre', 'code',
      'table', 'thead', 'tbody', 'tr', 'th', 'td',
    ],
    ALLOWED_ATTR: ['href', 'src', 'alt', 'title', 'class'],
    FORBID_TAGS: ['style', 'script', 'iframe', 'form', 'input'],
    FORBID_ATTR: ['onerror', 'onload', 'onclick', 'onmouseover'],
  },
};

export function sanitizeHtml(
  html: string,
  preset: keyof typeof sanitizeConfigs = 'basic'
): string {
  const config = sanitizeConfigs[preset];

  return purify.sanitize(html, {
    ...config,
    RETURN_DOM: false,
    RETURN_DOM_FRAGMENT: false,
  });
}

// Hook to transform elements
purify.addHook('afterSanitizeAttributes', (node) => {
  // Add rel="noopener noreferrer" to links
  if (node.tagName === 'A') {
    node.setAttribute('rel', 'noopener noreferrer');
    node.setAttribute('target', '_blank');
  }

  // Prefix image sources with CDN
  if (node.tagName === 'IMG') {
    const src = node.getAttribute('src');
    if (src && !src.startsWith('https://cdn.example.com')) {
      node.setAttribute('src', `https://cdn.example.com/proxy?url=${encodeURIComponent(src)}`);
    }
  }
});
```

## HTTP Security Headers

```typescript
// All security headers with helmet
import helmet from 'helmet';

app.use(helmet({
  contentSecurityPolicy: { /* CSP config */ },
  xssFilter: true,                        // X-XSS-Protection (legacy)
  noSniff: true,                          // X-Content-Type-Options: nosniff
  frameguard: { action: 'deny' },         // X-Frame-Options: DENY
  hsts: {                                 // Strict-Transport-Security
    maxAge: 31536000,
    includeSubDomains: true,
    preload: true,
  },
  referrerPolicy: { policy: 'strict-origin-when-cross-origin' },
}));

// Additional headers
app.use((req, res, next) => {
  // Permissions Policy (formerly Feature-Policy)
  res.setHeader('Permissions-Policy', 'geolocation=(), microphone=(), camera=()');

  // Cross-Origin headers
  res.setHeader('Cross-Origin-Opener-Policy', 'same-origin');
  res.setHeader('Cross-Origin-Embedder-Policy', 'require-corp');
  res.setHeader('Cross-Origin-Resource-Policy', 'same-origin');

  next();
});
```

## Best Practices

| Practice | Description |
|----------|-------------|
| Output encoding | Context-appropriate encoding |
| Input validation | Whitelist allowed input |
| CSP | Implement strict Content Security Policy |
| Sanitization | Sanitize HTML when needed |
| HttpOnly cookies | Prevent cookie theft via XSS |
| Framework features | Use auto-escaping features |
