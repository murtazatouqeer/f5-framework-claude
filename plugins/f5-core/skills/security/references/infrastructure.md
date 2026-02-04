# Infrastructure Security

HTTPS/TLS configuration, security headers, network security, and container hardening.

## Table of Contents

1. [HTTPS/TLS Configuration](#httpstls-configuration)
2. [Security Headers](#security-headers)
3. [Network Security](#network-security)
4. [Container Security](#container-security)
5. [Logging & Monitoring](#logging--monitoring)

---

## HTTPS/TLS Configuration

### Node.js HTTPS Server

```typescript
import https from 'https';
import fs from 'fs';
import express from 'express';

const app = express();

const httpsOptions = {
  key: fs.readFileSync('/etc/ssl/private/server.key'),
  cert: fs.readFileSync('/etc/ssl/certs/server.crt'),
  ca: fs.readFileSync('/etc/ssl/certs/ca-bundle.crt'),

  // TLS configuration
  minVersion: 'TLSv1.2',
  ciphers: [
    'ECDHE-ECDSA-AES128-GCM-SHA256',
    'ECDHE-RSA-AES128-GCM-SHA256',
    'ECDHE-ECDSA-AES256-GCM-SHA384',
    'ECDHE-RSA-AES256-GCM-SHA384',
  ].join(':'),

  // Honor server cipher order
  honorCipherOrder: true,

  // Session resumption
  sessionTimeout: 300,
};

const server = https.createServer(httpsOptions, app);

server.listen(443, () => {
  console.log('HTTPS server running on port 443');
});

// Redirect HTTP to HTTPS
import http from 'http';

http.createServer((req, res) => {
  res.writeHead(301, {
    Location: `https://${req.headers.host}${req.url}`,
  });
  res.end();
}).listen(80);
```

### Nginx TLS Configuration

```nginx
# /etc/nginx/conf.d/ssl.conf

server {
    listen 443 ssl http2;
    server_name example.com;

    # Certificates
    ssl_certificate /etc/nginx/ssl/server.crt;
    ssl_certificate_key /etc/nginx/ssl/server.key;
    ssl_trusted_certificate /etc/nginx/ssl/ca-bundle.crt;

    # TLS configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers on;

    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    resolver 8.8.8.8 8.8.4.4 valid=300s;

    # Session caching
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    ssl_session_tickets off;

    # Diffie-Hellman
    ssl_dhparam /etc/nginx/ssl/dhparam.pem;

    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name example.com;
    return 301 https://$server_name$request_uri;
}
```

### Certificate Management with Let's Encrypt

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d example.com -d www.example.com

# Auto-renewal (cron job)
0 0 * * * /usr/bin/certbot renew --quiet --post-hook "systemctl reload nginx"
```

```typescript
// Certificate monitoring
import tls from 'tls';

async function checkCertificateExpiry(hostname: string, port: number = 443): Promise<{
  valid: boolean;
  daysRemaining: number;
  expiresAt: Date;
}> {
  return new Promise((resolve, reject) => {
    const socket = tls.connect(port, hostname, { servername: hostname }, () => {
      const cert = socket.getPeerCertificate();
      socket.end();

      const expiresAt = new Date(cert.valid_to);
      const daysRemaining = Math.floor(
        (expiresAt.getTime() - Date.now()) / (1000 * 60 * 60 * 24)
      );

      resolve({
        valid: daysRemaining > 0,
        daysRemaining,
        expiresAt,
      });
    });

    socket.on('error', reject);
  });
}

// Alert if certificate expires within 30 days
async function monitorCertificates() {
  const domains = ['api.example.com', 'app.example.com'];

  for (const domain of domains) {
    const result = await checkCertificateExpiry(domain);
    if (result.daysRemaining < 30) {
      await alertService.send({
        level: result.daysRemaining < 7 ? 'critical' : 'warning',
        message: `Certificate for ${domain} expires in ${result.daysRemaining} days`,
      });
    }
  }
}
```

---

## Security Headers

### Helmet Configuration

```typescript
import helmet from 'helmet';
import crypto from 'crypto';

// Generate nonce per request
app.use((req, res, next) => {
  res.locals.nonce = crypto.randomBytes(16).toString('base64');
  next();
});

app.use(helmet({
  // Content Security Policy
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
      mediaSrc: ["'self'"],
      frameSrc: ["'none'"],
      frameAncestors: ["'none'"],
      formAction: ["'self'"],
      baseUri: ["'self'"],
      upgradeInsecureRequests: [],
    },
  },

  // X-Frame-Options
  frameguard: { action: 'deny' },

  // X-Content-Type-Options
  noSniff: true,

  // X-XSS-Protection (legacy, but still useful)
  xssFilter: true,

  // Referrer-Policy
  referrerPolicy: { policy: 'strict-origin-when-cross-origin' },

  // HSTS
  hsts: {
    maxAge: 31536000,
    includeSubDomains: true,
    preload: true,
  },

  // Hide X-Powered-By
  hidePoweredBy: true,

  // DNS Prefetch Control
  dnsPrefetchControl: { allow: false },

  // IE No Open
  ieNoOpen: true,

  // Permitted Cross-Domain Policies
  permittedCrossDomainPolicies: { permittedPolicies: 'none' },
}));

// Additional headers
app.use((req, res, next) => {
  // Permissions Policy
  res.setHeader('Permissions-Policy',
    'geolocation=(), microphone=(), camera=(), payment=(), usb=()'
  );

  // Cross-Origin policies
  res.setHeader('Cross-Origin-Opener-Policy', 'same-origin');
  res.setHeader('Cross-Origin-Resource-Policy', 'same-origin');
  res.setHeader('Cross-Origin-Embedder-Policy', 'require-corp');

  next();
});
```

### CSP Violation Reporting

```typescript
// CSP report endpoint
app.post('/csp-report', express.json({ type: 'application/csp-report' }), (req, res) => {
  const report = req.body['csp-report'];

  logger.warn({
    type: 'csp_violation',
    blockedUri: report['blocked-uri'],
    violatedDirective: report['violated-directive'],
    documentUri: report['document-uri'],
    sourceFile: report['source-file'],
    lineNumber: report['line-number'],
  });

  res.status(204).send();
});

// Update CSP to include reporting
app.use(helmet.contentSecurityPolicy({
  directives: {
    // ... other directives
    reportUri: '/csp-report',
  },
}));

// Report-Only mode for testing
app.use((req, res, next) => {
  res.setHeader('Content-Security-Policy-Report-Only',
    "default-src 'self'; report-uri /csp-report"
  );
  next();
});
```

### Cookie Security

```typescript
import session from 'express-session';

app.use(session({
  name: '__Host-session', // Secure cookie prefix
  secret: process.env.SESSION_SECRET!,
  resave: false,
  saveUninitialized: false,
  cookie: {
    httpOnly: true,      // Not accessible via JavaScript
    secure: true,        // HTTPS only
    sameSite: 'strict',  // CSRF protection
    maxAge: 24 * 60 * 60 * 1000, // 24 hours
    path: '/',
    domain: undefined,   // Current domain only
  },
}));

// Set secure cookies manually
res.cookie('preference', value, {
  httpOnly: true,
  secure: process.env.NODE_ENV === 'production',
  sameSite: 'strict',
  maxAge: 30 * 24 * 60 * 60 * 1000, // 30 days
  signed: true, // Requires cookie-parser with secret
});
```

---

## Network Security

### Firewall Rules (iptables)

```bash
#!/bin/bash
# Basic firewall setup

# Flush existing rules
iptables -F
iptables -X

# Default policies
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# Allow loopback
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# Allow established connections
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Allow SSH (limit rate)
iptables -A INPUT -p tcp --dport 22 -m state --state NEW -m recent --set
iptables -A INPUT -p tcp --dport 22 -m state --state NEW -m recent --update --seconds 60 --hitcount 4 -j DROP
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Allow HTTP/HTTPS
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Allow ping (optional)
iptables -A INPUT -p icmp --icmp-type echo-request -j ACCEPT

# Log dropped packets
iptables -A INPUT -j LOG --log-prefix "DROPPED: "

# Save rules
iptables-save > /etc/iptables/rules.v4
```

### Rate Limiting at Network Level

```nginx
# Nginx rate limiting
http {
    # Define rate limit zones
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;
    limit_conn_zone $binary_remote_addr zone=conn:10m;

    server {
        # Apply rate limits
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            limit_conn conn 10;

            proxy_pass http://backend;
        }

        location /auth/login {
            limit_req zone=login burst=5;

            proxy_pass http://backend;
        }

        # Custom error pages
        error_page 429 /429.html;
    }
}
```

### VPC and Security Groups (AWS)

```typescript
// AWS CDK security group configuration
import * as ec2 from 'aws-cdk-lib/aws-ec2';

const vpc = new ec2.Vpc(this, 'AppVPC', {
  maxAzs: 3,
  natGateways: 1,
  subnetConfiguration: [
    {
      name: 'Public',
      subnetType: ec2.SubnetType.PUBLIC,
      cidrMask: 24,
    },
    {
      name: 'Private',
      subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
      cidrMask: 24,
    },
    {
      name: 'Isolated',
      subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
      cidrMask: 24,
    },
  ],
});

// Web tier security group
const webSG = new ec2.SecurityGroup(this, 'WebSG', {
  vpc,
  description: 'Web tier security group',
  allowAllOutbound: false,
});

webSG.addIngressRule(
  ec2.Peer.anyIpv4(),
  ec2.Port.tcp(443),
  'Allow HTTPS'
);

// App tier security group
const appSG = new ec2.SecurityGroup(this, 'AppSG', {
  vpc,
  description: 'App tier security group',
});

appSG.addIngressRule(
  webSG,
  ec2.Port.tcp(3000),
  'Allow from web tier'
);

// Database security group
const dbSG = new ec2.SecurityGroup(this, 'DbSG', {
  vpc,
  description: 'Database security group',
});

dbSG.addIngressRule(
  appSG,
  ec2.Port.tcp(5432),
  'Allow PostgreSQL from app tier'
);
```

---

## Container Security

### Dockerfile Security Best Practices

```dockerfile
# Use specific version, not latest
FROM node:20.10-alpine AS builder

# Create non-root user
RUN addgroup -g 1001 -S appgroup && \
    adduser -u 1001 -S appuser -G appgroup

WORKDIR /app

# Copy package files first (layer caching)
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production && \
    npm cache clean --force

# Copy application code
COPY --chown=appuser:appgroup . .

# Build application
RUN npm run build

# Production image
FROM node:20.10-alpine AS production

# Security updates
RUN apk update && apk upgrade && \
    rm -rf /var/cache/apk/*

# Create non-root user
RUN addgroup -g 1001 -S appgroup && \
    adduser -u 1001 -S appuser -G appgroup

WORKDIR /app

# Copy only production artifacts
COPY --from=builder --chown=appuser:appgroup /app/dist ./dist
COPY --from=builder --chown=appuser:appgroup /app/node_modules ./node_modules
COPY --from=builder --chown=appuser:appgroup /app/package.json ./

# Switch to non-root user
USER appuser

# Read-only root filesystem
# (Enable via docker run --read-only)

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

EXPOSE 3000

CMD ["node", "dist/index.js"]
```

### Docker Compose Security

```yaml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    image: myapp:latest
    user: "1001:1001"
    read_only: true
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    tmpfs:
      - /tmp:noexec,nosuid,size=100m
    networks:
      - internal
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
    secrets:
      - db_password
      - jwt_secret
    healthcheck:
      test: ["CMD", "wget", "--spider", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 128M

  db:
    image: postgres:15-alpine
    user: postgres
    read_only: true
    security_opt:
      - no-new-privileges:true
    volumes:
      - db_data:/var/lib/postgresql/data
      - type: tmpfs
        target: /var/run/postgresql
    networks:
      - internal
    environment:
      - POSTGRES_DB=app
      - POSTGRES_USER=app
    secrets:
      - source: db_password
        target: /run/secrets/db_password

networks:
  internal:
    driver: bridge
    internal: true

volumes:
  db_data:
    driver: local

secrets:
  db_password:
    external: true
  jwt_secret:
    external: true
```

### Kubernetes Security

```yaml
# Pod Security Policy
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1001
    runAsGroup: 1001
    fsGroup: 1001
    seccompProfile:
      type: RuntimeDefault

  containers:
    - name: app
      image: myapp:latest
      securityContext:
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        capabilities:
          drop:
            - ALL

      resources:
        limits:
          memory: "512Mi"
          cpu: "1000m"
        requests:
          memory: "128Mi"
          cpu: "100m"

      volumeMounts:
        - name: tmp
          mountPath: /tmp
        - name: secrets
          mountPath: /etc/secrets
          readOnly: true

      livenessProbe:
        httpGet:
          path: /health
          port: 3000
        initialDelaySeconds: 10
        periodSeconds: 10

      readinessProbe:
        httpGet:
          path: /ready
          port: 3000
        initialDelaySeconds: 5
        periodSeconds: 5

  volumes:
    - name: tmp
      emptyDir: {}
    - name: secrets
      secret:
        secretName: app-secrets

---
# Network Policy
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: app-network-policy
spec:
  podSelector:
    matchLabels:
      app: myapp
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: nginx
      ports:
        - protocol: TCP
          port: 3000
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: postgres
      ports:
        - protocol: TCP
          port: 5432
```

---

## Logging & Monitoring

### Security Logging

```typescript
import pino from 'pino';

const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  redact: {
    paths: ['password', 'token', 'secret', 'authorization', '*.password'],
    remove: true,
  },
});

// Security event logging
interface SecurityEvent {
  type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  userId?: string;
  ip: string;
  userAgent?: string;
  details: Record<string, any>;
}

function logSecurityEvent(event: SecurityEvent): void {
  logger.warn({
    category: 'security',
    ...event,
    timestamp: new Date().toISOString(),
  });
}

// Log authentication events
logSecurityEvent({
  type: 'login_success',
  severity: 'low',
  userId: user.id,
  ip: req.ip,
  userAgent: req.get('User-Agent'),
  details: { method: 'password' },
});

logSecurityEvent({
  type: 'login_failure',
  severity: 'medium',
  ip: req.ip,
  userAgent: req.get('User-Agent'),
  details: { reason: 'invalid_password', email },
});

logSecurityEvent({
  type: 'privilege_escalation_attempt',
  severity: 'critical',
  userId: user.id,
  ip: req.ip,
  details: { attemptedAction: 'admin_access' },
});
```

### Audit Trail

```typescript
interface AuditLog {
  id: string;
  timestamp: Date;
  userId: string;
  action: string;
  resource: string;
  resourceId: string;
  changes?: {
    before: Record<string, any>;
    after: Record<string, any>;
  };
  ip: string;
  userAgent: string;
}

class AuditService {
  async log(entry: Omit<AuditLog, 'id' | 'timestamp'>): Promise<void> {
    await this.repository.create({
      id: crypto.randomUUID(),
      timestamp: new Date(),
      ...entry,
    });
  }

  async getHistory(resourceType: string, resourceId: string): Promise<AuditLog[]> {
    return this.repository.find({
      resource: resourceType,
      resourceId,
      orderBy: { timestamp: 'desc' },
    });
  }
}

// Usage in service
async function updateUser(userId: string, data: UpdateUserDto, actor: User): Promise<User> {
  const before = await userRepository.findById(userId);
  const after = await userRepository.update(userId, data);

  await auditService.log({
    userId: actor.id,
    action: 'update',
    resource: 'user',
    resourceId: userId,
    changes: { before, after },
    ip: actor.ip,
    userAgent: actor.userAgent,
  });

  return after;
}
```

### Alerting

```typescript
interface Alert {
  severity: 'info' | 'warning' | 'error' | 'critical';
  title: string;
  message: string;
  metadata?: Record<string, any>;
}

class AlertService {
  private thresholds = {
    failedLogins: { count: 5, window: 300 }, // 5 in 5 minutes
    errorRate: { rate: 0.05, window: 60 },   // 5% in 1 minute
    responseTime: { p99: 5000 },              // 5 second p99
  };

  async checkAndAlert(metric: string, value: number): Promise<void> {
    const threshold = this.thresholds[metric as keyof typeof this.thresholds];

    if (this.exceedsThreshold(metric, value, threshold)) {
      await this.send({
        severity: 'warning',
        title: `${metric} threshold exceeded`,
        message: `Current value: ${value}`,
        metadata: { metric, value, threshold },
      });
    }
  }

  async send(alert: Alert): Promise<void> {
    // Send to multiple channels based on severity
    if (alert.severity === 'critical') {
      await Promise.all([
        this.pagerDuty(alert),
        this.slack(alert),
        this.email(alert),
      ]);
    } else if (alert.severity === 'error') {
      await this.slack(alert);
    } else {
      // Log only
      logger.warn(alert);
    }
  }
}
```

---

## Best Practices Summary

| Category | Requirement |
|----------|-------------|
| TLS | TLS 1.2+ only, strong ciphers, HSTS |
| Headers | CSP, X-Frame-Options, X-Content-Type-Options |
| Cookies | HttpOnly, Secure, SameSite |
| Network | Firewall, rate limiting, VPC isolation |
| Containers | Non-root, read-only, minimal base image |
| Logging | Redact secrets, audit trail, alerting |
| Monitoring | Certificate expiry, error rates, intrusion detection |
