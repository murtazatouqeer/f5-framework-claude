---
name: https-tls
description: HTTPS and TLS configuration best practices
category: security/infrastructure
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# HTTPS & TLS Configuration

## Overview

HTTPS encrypts data in transit using TLS (Transport Layer Security),
protecting against eavesdropping and tampering.

## TLS Versions

| Version | Status | Recommendation |
|---------|--------|----------------|
| TLS 1.0 | Deprecated | Disable |
| TLS 1.1 | Deprecated | Disable |
| TLS 1.2 | Supported | Minimum |
| TLS 1.3 | Current | Preferred |

## Node.js HTTPS Server

```typescript
// server.ts
import https from 'https';
import fs from 'fs';
import express from 'express';

const app = express();

const httpsOptions: https.ServerOptions = {
  // Certificate files
  key: fs.readFileSync('/path/to/private.key'),
  cert: fs.readFileSync('/path/to/certificate.crt'),
  ca: fs.readFileSync('/path/to/ca-bundle.crt'),

  // TLS configuration
  minVersion: 'TLSv1.2',
  maxVersion: 'TLSv1.3',

  // Strong cipher suites
  ciphers: [
    // TLS 1.3 ciphers (automatically used when available)
    'TLS_AES_256_GCM_SHA384',
    'TLS_AES_128_GCM_SHA256',
    'TLS_CHACHA20_POLY1305_SHA256',
    // TLS 1.2 ciphers
    'ECDHE-ECDSA-AES256-GCM-SHA384',
    'ECDHE-RSA-AES256-GCM-SHA384',
    'ECDHE-ECDSA-AES128-GCM-SHA256',
    'ECDHE-RSA-AES128-GCM-SHA256',
    'ECDHE-ECDSA-CHACHA20-POLY1305',
    'ECDHE-RSA-CHACHA20-POLY1305',
  ].join(':'),

  // Prefer server cipher order
  honorCipherOrder: true,

  // ECDH curves
  ecdhCurve: ['P-521', 'P-384', 'P-256'].join(':'),

  // Session settings
  sessionTimeout: 300, // 5 minutes

  // Reject connections with invalid certificates
  rejectUnauthorized: true,
};

const server = https.createServer(httpsOptions, app);

server.listen(443, () => {
  console.log('HTTPS server running on port 443');
});

// HTTP redirect to HTTPS
import http from 'http';

http.createServer((req, res) => {
  res.writeHead(301, {
    Location: `https://${req.headers.host}${req.url}`,
  });
  res.end();
}).listen(80);
```

## Nginx TLS Configuration

```nginx
# /etc/nginx/conf.d/ssl.conf

# SSL/TLS settings
ssl_protocols TLSv1.2 TLSv1.3;

ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';

ssl_prefer_server_ciphers on;

# ECDH curve
ssl_ecdh_curve secp384r1;

# Session settings
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
ssl_session_tickets off;

# OCSP stapling
ssl_stapling on;
ssl_stapling_verify on;
resolver 8.8.8.8 8.8.4.4 valid=300s;
resolver_timeout 5s;

# DH parameters (generate with: openssl dhparam -out dhparam.pem 4096)
ssl_dhparam /etc/nginx/ssl/dhparam.pem;

# Server block
server {
    listen 443 ssl http2;
    server_name example.com;

    ssl_certificate /etc/nginx/ssl/certificate.crt;
    ssl_certificate_key /etc/nginx/ssl/private.key;
    ssl_trusted_certificate /etc/nginx/ssl/ca-bundle.crt;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # ... rest of configuration
}

# HTTP to HTTPS redirect
server {
    listen 80;
    server_name example.com;
    return 301 https://$host$request_uri;
}
```

## HSTS (HTTP Strict Transport Security)

```typescript
// middleware/hsts.middleware.ts
app.use((req, res, next) => {
  // Only set HSTS for HTTPS requests
  if (req.secure) {
    res.setHeader(
      'Strict-Transport-Security',
      'max-age=31536000; includeSubDomains; preload'
    );
  }
  next();
});

// Using helmet
import helmet from 'helmet';

app.use(helmet.hsts({
  maxAge: 31536000,        // 1 year in seconds
  includeSubDomains: true, // Apply to all subdomains
  preload: true,           // Submit to HSTS preload list
}));
```

## Certificate Management

### Let's Encrypt with Certbot

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d example.com -d www.example.com

# Auto-renewal (add to crontab)
0 12 * * * /usr/bin/certbot renew --quiet
```

### Certificate in Code

```typescript
// services/certificate.service.ts
import { exec } from 'child_process';
import fs from 'fs';

export class CertificateService {
  private certPath: string;
  private keyPath: string;

  constructor(domain: string) {
    this.certPath = `/etc/letsencrypt/live/${domain}/fullchain.pem`;
    this.keyPath = `/etc/letsencrypt/live/${domain}/privkey.pem`;
  }

  getCertificate(): { cert: Buffer; key: Buffer } {
    return {
      cert: fs.readFileSync(this.certPath),
      key: fs.readFileSync(this.keyPath),
    };
  }

  // Check certificate expiration
  async checkExpiration(): Promise<{ daysUntilExpiry: number; isValid: boolean }> {
    return new Promise((resolve, reject) => {
      exec(
        `openssl x509 -enddate -noout -in ${this.certPath}`,
        (error, stdout) => {
          if (error) return reject(error);

          const dateMatch = stdout.match(/notAfter=(.+)/);
          if (!dateMatch) return reject(new Error('Cannot parse date'));

          const expiryDate = new Date(dateMatch[1]);
          const now = new Date();
          const daysUntilExpiry = Math.floor(
            (expiryDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24)
          );

          resolve({
            daysUntilExpiry,
            isValid: daysUntilExpiry > 0,
          });
        }
      );
    });
  }

  // Alert if certificate is expiring soon
  async monitorExpiration(thresholdDays: number = 30): Promise<void> {
    const { daysUntilExpiry, isValid } = await this.checkExpiration();

    if (!isValid) {
      throw new Error('Certificate has expired!');
    }

    if (daysUntilExpiry <= thresholdDays) {
      console.warn(`Certificate expires in ${daysUntilExpiry} days`);
      // Send alert
    }
  }
}
```

## Certificate Pinning (Mobile/Desktop Apps)

```typescript
// For HTTPS requests from Node.js to external services
import https from 'https';
import crypto from 'crypto';

const pinnedCerts = new Set([
  // SHA-256 fingerprint of certificate
  'sha256//YLh1dUR9y6Kja30RrAn7JKnbQG/uEtLMkBgFF2Fuihg=',
]);

const agent = new https.Agent({
  checkServerIdentity: (host, cert) => {
    // Calculate certificate fingerprint
    const fingerprint = `sha256//${crypto
      .createHash('sha256')
      .update(cert.raw)
      .digest('base64')}`;

    if (!pinnedCerts.has(fingerprint)) {
      throw new Error(`Certificate fingerprint mismatch for ${host}`);
    }
  },
});

// Use agent for requests
https.get('https://api.example.com', { agent }, (res) => {
  // Handle response
});
```

## mTLS (Mutual TLS)

```typescript
// Server requiring client certificates
const httpsOptions: https.ServerOptions = {
  key: fs.readFileSync('server-key.pem'),
  cert: fs.readFileSync('server-cert.pem'),
  ca: fs.readFileSync('client-ca.pem'), // CA that signed client certs

  // Require client certificate
  requestCert: true,
  rejectUnauthorized: true,
};

// Middleware to verify client cert
app.use((req, res, next) => {
  const cert = (req.socket as any).getPeerCertificate();

  if (!cert || !cert.subject) {
    return res.status(401).json({ error: 'Client certificate required' });
  }

  // Verify certificate attributes
  if (cert.subject.CN !== 'expected-client-name') {
    return res.status(403).json({ error: 'Invalid client certificate' });
  }

  // Attach client identity to request
  req.clientId = cert.subject.CN;

  next();
});

// Client with certificate
const clientOptions = {
  hostname: 'api.example.com',
  port: 443,
  path: '/data',
  method: 'GET',
  key: fs.readFileSync('client-key.pem'),
  cert: fs.readFileSync('client-cert.pem'),
  ca: fs.readFileSync('server-ca.pem'),
};

https.request(clientOptions, (res) => {
  // Handle response
}).end();
```

## TLS Testing

```bash
# Test TLS configuration
openssl s_client -connect example.com:443 -tls1_2
openssl s_client -connect example.com:443 -tls1_3

# Check certificate details
openssl s_client -connect example.com:443 </dev/null 2>/dev/null | openssl x509 -text

# Test specific cipher
openssl s_client -connect example.com:443 -cipher ECDHE-RSA-AES256-GCM-SHA384

# Use testssl.sh for comprehensive testing
./testssl.sh example.com
```

## Best Practices

| Practice | Description |
|----------|-------------|
| TLS 1.2+ only | Disable older versions |
| Strong ciphers | Use AEAD ciphers (GCM, ChaCha20) |
| ECDHE key exchange | Forward secrecy |
| HSTS | Force HTTPS with preload |
| Certificate monitoring | Alert before expiry |
| OCSP stapling | Improve performance |
