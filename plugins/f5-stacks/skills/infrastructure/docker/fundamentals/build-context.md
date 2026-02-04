---
name: build-context
description: Understanding Docker build context and .dockerignore
applies_to: docker
---

# Docker Build Context

## What is Build Context?

The build context is the set of files and directories that Docker can access during the build process. When you run `docker build`, the entire context is sent to the Docker daemon.

```bash
# Current directory as context
docker build -t myapp .

# Specific directory as context
docker build -t myapp ./app

# URL as context
docker build -t myapp https://github.com/user/repo.git
```

## Build Context Flow

```
┌─────────────────────────────────────────────────────────┐
│                    Build Context                         │
│  (Files and directories you specify)                    │
│                                                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │
│  │    src/     │ │ package.json│ │ Dockerfile  │       │
│  └─────────────┘ └─────────────┘ └─────────────┘       │
│                                                         │
└─────────────────────────────────────────────────────────┘
                            │
                            │ Sent to Docker daemon
                            │ (excluding .dockerignore)
                            ▼
┌─────────────────────────────────────────────────────────┐
│                    Docker Daemon                         │
│                                                         │
│  1. Receives context                                    │
│  2. Parses Dockerfile                                   │
│  3. Executes instructions                               │
│  4. Builds image                                        │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Context Size Matters

Large contexts slow down builds:

```bash
# See what's being sent
docker build -t myapp . 2>&1 | head -5
# "Sending build context to Docker daemon  156.7MB"

# If this is large, you need .dockerignore!
```

## .dockerignore

The `.dockerignore` file specifies what to exclude from the build context.

### Basic Syntax

```dockerignore
# Comment

# Ignore file
README.md

# Ignore directory
node_modules/

# Wildcard (matches any character except /)
*.log
*.md

# Double wildcard (matches any path)
**/*.test.js
**/temp/*

# Negation (include previously excluded)
*.md
!README.md
```

### Complete .dockerignore Example

```dockerignore
# =============================================================================
# .dockerignore - Exclude files from Docker build context
# =============================================================================

# Version Control
.git
.gitignore
.gitattributes

# Dependencies (rebuilt in container)
node_modules
vendor
__pycache__
*.pyc
.pnp
.pnp.js

# Build outputs (rebuilt in container)
dist
build
out
target
*.egg-info

# IDE and Editor
.idea
.vscode
*.swp
*.swo
*~
.project
.classpath
.settings

# Environment and secrets
.env
.env.*
!.env.example
*.pem
*.key
secrets/

# Docker files (not needed in image)
Dockerfile*
docker-compose*
.docker
.dockerignore

# Documentation
README.md
CHANGELOG.md
CONTRIBUTING.md
docs/
*.md
!LICENSE.md

# Testing
test/
tests/
__tests__
*.test.js
*.test.ts
*.spec.js
*.spec.ts
coverage/
.coverage
.nyc_output
.pytest_cache

# Logs and temporary files
*.log
logs/
tmp/
temp/
.tmp

# OS files
.DS_Store
.DS_Store?
._*
Thumbs.db
ehthumbs.db

# CI/CD
.github
.gitlab-ci.yml
.travis.yml
Jenkinsfile
azure-pipelines.yml
.circleci

# Misc
*.bak
*.backup
npm-debug.log*
yarn-debug.log*
yarn-error.log*
```

### Language-Specific Patterns

#### Node.js
```dockerignore
node_modules
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.npm
.yarn
coverage
.nyc_output
```

#### Python
```dockerignore
__pycache__
*.py[cod]
*$py.class
*.so
.Python
venv/
.venv/
ENV/
.eggs/
*.egg-info/
.coverage
htmlcov/
.pytest_cache/
.mypy_cache/
```

#### Go
```dockerignore
*.exe
*.exe~
*.dll
*.so
*.dylib
*.test
*.out
vendor/
```

#### Java
```dockerignore
target/
*.class
*.jar
*.war
*.ear
.gradle/
build/
```

## Build Context Strategies

### Strategy 1: Minimal Context

Only include what's needed:

```bash
# Create a build directory with only needed files
mkdir -p .build
cp package*.json .build/
cp -r src .build/
cp Dockerfile .build/

# Build from minimal context
docker build -t myapp .build/
```

### Strategy 2: Multiple Dockerfiles

Different contexts for different images:

```
project/
├── frontend/
│   ├── Dockerfile
│   ├── .dockerignore
│   └── src/
├── backend/
│   ├── Dockerfile
│   ├── .dockerignore
│   └── src/
└── docker-compose.yml
```

```yaml
# docker-compose.yml
services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
```

### Strategy 3: Custom Dockerfile Location

```bash
# Dockerfile outside context
docker build -f ../Dockerfile -t myapp .

# Dockerfile in subdirectory
docker build -f docker/Dockerfile.prod -t myapp:prod .
```

### Strategy 4: Git URL as Context

```bash
# Build from Git repository
docker build -t myapp https://github.com/user/repo.git

# Specific branch
docker build -t myapp https://github.com/user/repo.git#branch

# Specific directory in repo
docker build -t myapp https://github.com/user/repo.git#:subdir
```

## Debugging Context Issues

### Check Context Size

```bash
# Create tarball to see what would be sent
tar -cvf context.tar --exclude-from=.dockerignore .
ls -lh context.tar

# More accurate (uses Docker's ignore logic)
docker build -t test . 2>&1 | grep "Sending build context"
```

### Verify .dockerignore

```bash
# Test what files would be included
# (No standard tool, but you can use rsync to simulate)
rsync -av --exclude-from=.dockerignore --dry-run . /tmp/test/
```

### Common Issues

#### Issue: node_modules in context
```bash
# Symptom: Very large context
# Solution: Add to .dockerignore
node_modules
```

#### Issue: COPY fails
```bash
# Symptom: "file not found" during COPY
# Cause: File in .dockerignore or not in context
# Solution: Check .dockerignore, verify file exists
```

#### Issue: .git in context
```bash
# Symptom: Large context, slow builds
# Solution: Add .git to .dockerignore
.git
```

## Best Practices

1. **Always use .dockerignore** - Even for small projects
2. **Keep context minimal** - Only include what's needed
3. **Mirror .gitignore** - Start with similar patterns
4. **Exclude build outputs** - They're rebuilt anyway
5. **Exclude secrets** - Never include .env files with secrets
6. **Exclude tests** - Unless building test image
7. **Exclude documentation** - Not needed in image

## Related Skills
- fundamentals/dockerfile-syntax
- dockerfile/best-practices
- optimization/build-performance
