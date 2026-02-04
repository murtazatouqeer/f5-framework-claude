---
name: security
description: Application security best practices and patterns
category: skill
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: true
context: inject
---

# Security Skills

## Overview

Security knowledge essential for building secure applications,
protecting user data, and preventing common vulnerabilities.

## Security Layers

```
┌─────────────────────────────────────────────┐
│              Application Security            │
│  ┌─────────────────────────────────────────┐│
│  │         Authentication & AuthZ          ││
│  │  ┌───────────────────────────────────┐  ││
│  │  │        Input Validation           │  ││
│  │  │  ┌─────────────────────────────┐  │  ││
│  │  │  │    Data Protection          │  │  ││
│  │  │  └─────────────────────────────┘  │  ││
│  │  └───────────────────────────────────┘  ││
│  └─────────────────────────────────────────┘│
│              Infrastructure Security         │
└─────────────────────────────────────────────┘
```

## Categories

### Authentication
- JWT tokens and refresh strategies
- OAuth 2.0 / OpenID Connect
- Session management
- Multi-factor authentication
- Passwordless authentication

### Authorization
- Role-Based Access Control (RBAC)
- Attribute-Based Access Control (ABAC)
- Permission systems
- Access control patterns

### OWASP Top 10
- Injection attacks
- Broken authentication
- Cross-Site Scripting (XSS)
- Cross-Site Request Forgery (CSRF)
- Security misconfiguration
- Sensitive data exposure

### API Security
- Rate limiting
- Input validation
- API key management
- CORS configuration

### Data Protection
- Encryption at rest/transit
- Password hashing
- Secrets management
- Data masking/anonymization

### Infrastructure
- HTTPS/TLS configuration
- Security headers
- Container security
- Network security

### Compliance
- GDPR requirements
- PCI-DSS standards
- Security auditing

## Security Mindset

> "Security is not a product, but a process." - Bruce Schneier

Always assume:
- All input is malicious
- External systems can be compromised
- Attackers will find vulnerabilities
- Defense in depth is essential

## Quick Reference

| Threat | Primary Defense | Secondary Defense |
|--------|-----------------|-------------------|
| SQL Injection | Parameterized queries | Input validation |
| XSS | Output encoding | CSP headers |
| CSRF | CSRF tokens | SameSite cookies |
| Auth bypass | Strong authentication | Session management |
| Data breach | Encryption | Access control |

## Related Skills

- [API Design](../api-design/) - Secure API patterns
- [Testing](../testing/) - Security testing
- [Architecture](../architecture/) - Security architecture
