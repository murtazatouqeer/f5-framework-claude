---
name: docker-secrets-management
description: Managing secrets and sensitive data in Docker
applies_to: docker
---

# Docker Secrets Management

## Security Principles

1. **Never in images** - Secrets must not be baked into images
2. **Never in environment** - Avoid sensitive data in plain env vars
3. **Encrypted at rest** - Use encrypted storage
4. **Minimal exposure** - Only where needed
5. **Rotation support** - Enable secret rotation

## Methods Comparison

| Method | Security | Complexity | Use Case |
|--------|----------|------------|----------|
| Docker Secrets (Swarm) | High | Medium | Production Swarm |
| BuildKit Secrets | High | Low | Build-time |
| Volume Mounts | Medium | Low | Development |
| External Managers | Highest | High | Enterprise |

## Docker Secrets (Swarm Mode)

### Create Secret

```bash
# From stdin
echo "my-secret-password" | docker secret create db_password -

# From file
docker secret create db_password ./password.txt

# With labels
docker secret create \
  --label env=production \
  --label app=myapp \
  db_password ./password.txt
```

### Use in Service

```bash
# Create service with secret
docker service create \
  --name api \
  --secret db_password \
  myapp

# Secret available at /run/secrets/db_password
```

### Docker Compose (Swarm)

```yaml
services:
  api:
    image: myapp
    secrets:
      - db_password
      - api_key
    environment:
      DB_PASSWORD_FILE: /run/secrets/db_password
      API_KEY_FILE: /run/secrets/api_key

secrets:
  db_password:
    file: ./secrets/db_password.txt
  api_key:
    external: true
```

### Access in Application

```javascript
// Node.js - Read from file
const fs = require('fs');

function getSecret(name) {
  const path = process.env[`${name}_FILE`] || `/run/secrets/${name}`;
  return fs.readFileSync(path, 'utf8').trim();
}

const dbPassword = getSecret('db_password');
```

```python
# Python
import os

def get_secret(name):
    file_path = os.environ.get(f'{name}_FILE', f'/run/secrets/{name}')
    with open(file_path) as f:
        return f.read().strip()

db_password = get_secret('db_password')
```

### Secret Options

```yaml
services:
  api:
    secrets:
      - source: db_password
        target: database_password  # Custom name
        uid: '1000'
        gid: '1000'
        mode: 0400  # Read-only by owner

secrets:
  db_password:
    file: ./secrets/db_password.txt
```

## BuildKit Secrets

### Dockerfile

```dockerfile
# syntax=docker/dockerfile:1

FROM node:20-alpine

WORKDIR /app
COPY package*.json ./

# Secret available only during this RUN, never stored in layer
RUN --mount=type=secret,id=npmrc,target=/app/.npmrc \
    npm ci

COPY . .
CMD ["node", "server.js"]
```

### Build Command

```bash
# Pass secret during build
docker build --secret id=npmrc,src=.npmrc .

# Multiple secrets
docker build \
  --secret id=npmrc,src=.npmrc \
  --secret id=ssh_key,src=~/.ssh/id_rsa \
  .
```

### SSH Keys

```dockerfile
# syntax=docker/dockerfile:1

FROM node:20-alpine

# Mount SSH agent for git clone
RUN --mount=type=ssh \
    git clone git@github.com:private/repo.git
```

```bash
# Build with SSH
docker build --ssh default .
```

## Volume-Based Secrets

### Development Pattern

```yaml
services:
  api:
    volumes:
      - ./secrets:/run/secrets:ro
    environment:
      DB_PASSWORD_FILE: /run/secrets/db_password
```

### File Structure

```
project/
├── secrets/           # .gitignore this directory
│   ├── db_password
│   ├── api_key
│   └── jwt_secret
├── docker-compose.yml
└── .gitignore
```

### .gitignore

```gitignore
# Never commit secrets
secrets/
*.pem
*.key
.env
.env.local
.env.*.local
```

## Environment Variables (Limited Use)

### Acceptable Uses

```yaml
services:
  api:
    environment:
      # OK - Reference to secret location
      - DB_PASSWORD_FILE=/run/secrets/db_password

      # OK - Non-sensitive configuration
      - NODE_ENV=production
      - LOG_LEVEL=info

      # AVOID - Actual secret value
      # - DB_PASSWORD=secret123
```

### Using .env File

```yaml
services:
  api:
    env_file:
      - .env  # For non-sensitive config only
```

```bash
# .env (committed) - defaults only
NODE_ENV=development
LOG_LEVEL=debug

# .env.local (not committed) - overrides
# DB_PASSWORD=mysecret  # Still not recommended
```

## External Secret Managers

### HashiCorp Vault

```yaml
services:
  api:
    environment:
      VAULT_ADDR: http://vault:8200
      VAULT_TOKEN_FILE: /run/secrets/vault_token
    secrets:
      - vault_token

secrets:
  vault_token:
    file: ./vault-token.txt
```

```javascript
// Fetch secrets from Vault
const vault = require('node-vault')({
  endpoint: process.env.VAULT_ADDR,
  token: fs.readFileSync('/run/secrets/vault_token', 'utf8').trim()
});

async function getDbPassword() {
  const result = await vault.read('secret/data/database');
  return result.data.data.password;
}
```

### AWS Secrets Manager

```yaml
services:
  api:
    environment:
      AWS_REGION: us-east-1
      # Use IAM roles, not access keys
    # Or mount AWS credentials securely
```

```javascript
const { SecretsManager } = require('@aws-sdk/client-secrets-manager');

async function getSecret(secretName) {
  const client = new SecretsManager({ region: process.env.AWS_REGION });
  const response = await client.getSecretValue({ SecretId: secretName });
  return JSON.parse(response.SecretString);
}
```

### Kubernetes Secrets (K8s)

```yaml
# k8s secret
apiVersion: v1
kind: Secret
metadata:
  name: db-credentials
type: Opaque
data:
  password: base64-encoded-password
```

```yaml
# Mount in pod
volumes:
  - name: db-creds
    secret:
      secretName: db-credentials
```

## Secret Rotation

### Pattern for Rotation

```yaml
services:
  api:
    secrets:
      - db_password
      - db_password_new  # New secret during rotation
    environment:
      DB_PASSWORD_FILE: /run/secrets/db_password
      DB_PASSWORD_NEW_FILE: /run/secrets/db_password_new
```

### Application Support

```javascript
// Support multiple passwords during rotation
async function connectDatabase() {
  const passwords = [
    getSecret('db_password'),
    getSecretOrNull('db_password_new')
  ].filter(Boolean);

  for (const password of passwords) {
    try {
      return await createConnection({ password });
    } catch (e) {
      continue;
    }
  }
  throw new Error('All database passwords failed');
}
```

## Database Initialization

### PostgreSQL

```yaml
services:
  db:
    image: postgres:16-alpine
    secrets:
      - postgres_password
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/postgres_password

secrets:
  postgres_password:
    file: ./secrets/postgres_password.txt
```

### MySQL

```yaml
services:
  db:
    image: mysql:8.0
    secrets:
      - mysql_root_password
    environment:
      MYSQL_ROOT_PASSWORD_FILE: /run/secrets/mysql_root_password
```

### MongoDB

```yaml
services:
  db:
    image: mongo:7
    secrets:
      - mongo_password
    environment:
      MONGO_INITDB_ROOT_PASSWORD_FILE: /run/secrets/mongo_password
```

## Complete Example

```yaml
services:
  api:
    build: ./api
    secrets:
      - db_password
      - jwt_secret
      - api_key
    environment:
      NODE_ENV: production
      DB_HOST: db
      DB_USER: app
      DB_PASSWORD_FILE: /run/secrets/db_password
      JWT_SECRET_FILE: /run/secrets/jwt_secret
      EXTERNAL_API_KEY_FILE: /run/secrets/api_key
    networks:
      - frontend
      - backend
    depends_on:
      - db

  db:
    image: postgres:16-alpine
    secrets:
      - postgres_password
    environment:
      POSTGRES_USER: app
      POSTGRES_PASSWORD_FILE: /run/secrets/postgres_password
      POSTGRES_DB: myapp
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - backend

secrets:
  # For development - file-based
  db_password:
    file: ./secrets/db_password.txt
  postgres_password:
    file: ./secrets/postgres_password.txt
  jwt_secret:
    file: ./secrets/jwt_secret.txt
  api_key:
    file: ./secrets/api_key.txt

  # For production - external (Swarm)
  # db_password:
  #   external: true
  # postgres_password:
  #   external: true

networks:
  frontend:
  backend:
    internal: true

volumes:
  postgres_data:
```

## Security Checklist

### Image Build

- [ ] Never COPY secrets into image
- [ ] Never use ENV for secrets
- [ ] Use BuildKit secret mounts
- [ ] Don't commit secrets to git

### Runtime

- [ ] Use Docker Secrets (Swarm) or volume mounts
- [ ] Read from files, not environment
- [ ] Set restrictive file permissions
- [ ] Use internal networks

### Operations

- [ ] Rotate secrets regularly
- [ ] Audit secret access
- [ ] Use external secret managers for production
- [ ] Encrypt secrets at rest

### Development

- [ ] Use .gitignore for secret files
- [ ] Provide .env.example templates
- [ ] Document required secrets
- [ ] Use different secrets per environment

## Related Skills
- security/image-security
- security/runtime-security
- compose/environment
