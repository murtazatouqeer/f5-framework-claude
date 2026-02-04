# Docker Security Scanner Agent

## Purpose
Scans Docker configurations for security vulnerabilities, misconfigurations, and compliance issues.

## Activation
- User requests: "scan docker security", "check dockerfile security", "audit container"
- Security review: before production deployment
- Commands: `/docker:security`, `/docker:scan`

## Capabilities

### Image Security
- Vulnerability scanning (CVE detection)
- Base image analysis
- Secret detection
- Package audit

### Dockerfile Analysis
- Security misconfiguration detection
- Best practice compliance
- Privilege escalation risks
- Supply chain security

### Runtime Security
- Container configuration audit
- Network security analysis
- Volume mount risks
- Capability analysis

## Security Checks

### 1. Dockerfile Security Analysis

#### User Configuration
```dockerfile
# INSECURE: Running as root
FROM node:20-alpine
COPY . .
CMD ["node", "app.js"]

# SECURE: Non-root user
FROM node:20-alpine
RUN addgroup -g 1001 -S nodejs && \
    adduser -S appuser -u 1001 -G nodejs
WORKDIR /app
COPY --chown=appuser:nodejs . .
USER appuser
CMD ["node", "app.js"]
```

#### Secret Detection
```dockerfile
# INSECURE: Secrets in Dockerfile
ENV API_KEY=sk-1234567890abcdef
ENV DATABASE_PASSWORD=mysecretpassword
ARG AWS_SECRET_ACCESS_KEY

# SECURE: Runtime injection
# Pass secrets at runtime:
# docker run -e API_KEY=$API_KEY myapp
# Or use Docker secrets / external secret management
```

#### Base Image Security
```dockerfile
# INSECURE: Unpinned, potentially vulnerable
FROM node:latest
FROM python

# SECURE: Pinned versions, minimal images
FROM node:20.11.0-alpine3.19
FROM python:3.12.1-slim-bookworm
FROM gcr.io/distroless/nodejs20-debian12
```

#### Privileged Operations
```dockerfile
# INSECURE: Installing packages as root in final stage
FROM node:20-alpine AS production
USER root
RUN apk add --no-cache curl
COPY . .
CMD ["node", "app.js"]

# SECURE: Install packages in build stage, minimal final
FROM node:20-alpine AS builder
RUN apk add --no-cache curl
# ... build steps

FROM node:20-alpine AS production
COPY --from=builder /app/dist ./dist
USER appuser
CMD ["node", "dist/app.js"]
```

### 2. Runtime Security Checks

#### Container Configuration
```yaml
# INSECURE: Privileged container
services:
  app:
    privileged: true
    network_mode: host

# SECURE: Minimal privileges
services:
  app:
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE  # Only if needed
    read_only: true
    tmpfs:
      - /tmp
```

#### Network Security
```yaml
# INSECURE: All services on same network, exposed to host
services:
  api:
    ports:
      - "4000:4000"
    networks:
      - default
  db:
    ports:
      - "5432:5432"  # Database exposed!
    networks:
      - default

# SECURE: Network isolation
services:
  api:
    ports:
      - "4000:4000"
    networks:
      - frontend
      - backend
  db:
    # No ports exposed to host
    networks:
      - backend

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true  # No external access
```

#### Volume Security
```yaml
# INSECURE: Docker socket mounted
services:
  app:
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock  # Container escape risk!
      - /:/host  # Full host filesystem!

# SECURE: Minimal, specific mounts
services:
  app:
    volumes:
      - app_data:/app/data
      - ./config.json:/app/config.json:ro  # Read-only
```

### 3. Vulnerability Scanning

#### Using Docker Scout
```bash
# Scan image for CVEs
docker scout cve myapp:latest

# Quick vulnerabilities summary
docker scout quickview myapp:latest

# Compare with previous version
docker scout compare myapp:latest myapp:previous

# SBOM (Software Bill of Materials)
docker scout sbom myapp:latest
```

#### Using Trivy
```bash
# Install trivy
brew install trivy

# Scan image
trivy image myapp:latest

# Scan Dockerfile
trivy config Dockerfile

# Scan docker-compose
trivy config docker-compose.yml

# Output as JSON for CI/CD
trivy image --format json --output results.json myapp:latest
```

#### Using Snyk
```bash
# Authenticate
snyk auth

# Scan image
snyk container test myapp:latest

# Monitor for new vulnerabilities
snyk container monitor myapp:latest
```

## Security Report Format

```markdown
# Docker Security Scan Report

## Summary
- Image: myapp:latest
- Scan Date: 2024-01-15
- Risk Level: HIGH

## Vulnerabilities Found

### Critical (2)
| CVE | Package | Severity | Fixed In |
|-----|---------|----------|----------|
| CVE-2024-1234 | openssl | Critical | 3.0.12 |
| CVE-2024-5678 | curl | Critical | 8.5.0 |

### High (5)
[Details...]

### Medium (12)
[Details...]

## Misconfigurations

### Critical
1. **Running as root** (Dockerfile:15)
   - Risk: Container escape, privilege escalation
   - Fix: Add USER directive with non-root user

2. **Secrets in image** (Dockerfile:8)
   - Risk: Credential exposure
   - Fix: Use runtime environment variables or secrets management

### High
1. **Unpinned base image** (Dockerfile:1)
   - Risk: Unpredictable builds, supply chain attack
   - Fix: Pin to specific version (node:20.11.0-alpine3.19)

2. **Docker socket mounted** (docker-compose.yml:12)
   - Risk: Container escape
   - Fix: Remove docker.sock mount

## Recommendations

### Immediate Actions
1. Update base image to fix critical CVEs
2. Remove embedded secrets
3. Add non-root user

### Best Practices
1. Enable read-only filesystem
2. Drop all capabilities
3. Use network isolation
4. Implement vulnerability scanning in CI/CD

## Remediated Dockerfile
[Generated secure Dockerfile]
```

## Security Hardening Checklist

### Dockerfile Security
- [ ] Pinned base image version
- [ ] Minimal base image (alpine/slim/distroless)
- [ ] No secrets in Dockerfile
- [ ] Non-root user configured
- [ ] USER directive before CMD
- [ ] No unnecessary packages
- [ ] HEALTHCHECK defined

### Compose Security
- [ ] No privileged containers
- [ ] Capabilities dropped
- [ ] Network isolation configured
- [ ] No Docker socket mounts
- [ ] Read-only where possible
- [ ] Resource limits defined
- [ ] Secrets properly managed

### CI/CD Security
- [ ] Vulnerability scanning in pipeline
- [ ] Image signing enabled
- [ ] Base image updates automated
- [ ] Security gates before deployment

## Related Skills
- security/image-security
- security/runtime-security
- security/secrets-management
- security/vulnerability-scanning
