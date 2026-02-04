---
name: sonarqube
description: SonarQube code quality and security analysis
category: code-quality/static-analysis
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# SonarQube Analysis

## Overview

SonarQube is a comprehensive code quality platform that detects bugs, vulnerabilities, code smells, and provides metrics on technical debt.

## Setup

### sonar-project.properties

```properties
# Project identification
sonar.projectKey=my-project
sonar.projectName=My Project
sonar.projectVersion=1.0.0

# Source configuration
sonar.sources=src
sonar.tests=src
sonar.test.inclusions=**/*.test.ts,**/*.spec.ts

# TypeScript configuration
sonar.typescript.lcov.reportPaths=coverage/lcov.info
sonar.typescript.tsconfigPath=tsconfig.json

# Exclusions
sonar.exclusions=**/node_modules/**,**/dist/**,**/*.test.ts,**/*.spec.ts
sonar.coverage.exclusions=**/*.test.ts,**/*.spec.ts,**/mocks/**

# Encoding
sonar.sourceEncoding=UTF-8

# Quality Gate
sonar.qualitygate.wait=true
```

### Docker Compose (Local Development)

```yaml
# docker-compose.yml
version: '3.8'

services:
  sonarqube:
    image: sonarqube:lts-community
    container_name: sonarqube
    ports:
      - '9000:9000'
    environment:
      - SONAR_ES_BOOTSTRAP_CHECKS_DISABLE=true
    volumes:
      - sonarqube_data:/opt/sonarqube/data
      - sonarqube_logs:/opt/sonarqube/logs
      - sonarqube_extensions:/opt/sonarqube/extensions

volumes:
  sonarqube_data:
  sonarqube_logs:
  sonarqube_extensions:
```

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/sonar.yml
name: SonarQube Analysis

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  sonarqube:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run tests with coverage
        run: npm run test:coverage

      - name: SonarQube Scan
        uses: SonarSource/sonarqube-scan-action@master
        env:
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
          SONAR_HOST_URL: ${{ secrets.SONAR_HOST_URL }}

      - name: Quality Gate
        uses: SonarSource/sonarqube-quality-gate-action@master
        timeout-minutes: 5
        env:
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
```

### GitLab CI

```yaml
# .gitlab-ci.yml
sonarqube-check:
  stage: test
  image:
    name: sonarsource/sonar-scanner-cli:latest
  variables:
    SONAR_USER_HOME: '${CI_PROJECT_DIR}/.sonar'
    GIT_DEPTH: '0'
  cache:
    key: '${CI_JOB_NAME}'
    paths:
      - .sonar/cache
  script:
    - sonar-scanner
  only:
    - merge_requests
    - main
    - develop
```

## Quality Gates

### Default Quality Gate Conditions

```yaml
quality_gate:
  conditions:
    # Coverage
    - metric: new_coverage
      operator: LT
      value: 80
      
    # Duplication
    - metric: new_duplicated_lines_density
      operator: GT
      value: 3
      
    # Maintainability
    - metric: new_maintainability_rating
      operator: GT
      value: 1  # A rating
      
    # Reliability
    - metric: new_reliability_rating
      operator: GT
      value: 1  # A rating
      
    # Security
    - metric: new_security_rating
      operator: GT
      value: 1  # A rating
      
    # Security Hotspots
    - metric: new_security_hotspots_reviewed
      operator: LT
      value: 100
```

### Custom Quality Gate (API)

```bash
# Create quality gate
curl -X POST \
  -u admin:admin \
  "http://localhost:9000/api/qualitygates/create?name=MyGate"

# Add condition
curl -X POST \
  -u admin:admin \
  "http://localhost:9000/api/qualitygates/create_condition?gateId=1&metric=coverage&op=LT&error=80"
```

## Code Smell Categories

### Maintainability Issues

| Smell | Description | Fix |
|-------|-------------|-----|
| Cognitive Complexity | Function too complex | Extract methods |
| Duplicated Blocks | Copy-paste code | Extract common code |
| Too Many Parameters | >4 parameters | Use object parameter |
| Long Method | >20 lines | Extract methods |

### Reliability Issues

| Bug Type | Description | Severity |
|----------|-------------|----------|
| Null Pointer | Potential null dereference | Major |
| Resource Leak | Unclosed resources | Major |
| Infinite Loop | Loop never terminates | Critical |
| Out of Bounds | Array index issues | Critical |

### Security Vulnerabilities

| Vulnerability | Risk | OWASP |
|---------------|------|-------|
| SQL Injection | Data breach | A03:2021 |
| XSS | Script injection | A03:2021 |
| Hardcoded Credentials | Access breach | A07:2021 |
| Weak Crypto | Data exposure | A02:2021 |

## SonarLint IDE Integration

### VS Code

```json
// .vscode/settings.json
{
  "sonarlint.connectedMode.project": {
    "connectionId": "my-sonar",
    "projectKey": "my-project"
  },
  "sonarlint.pathToNodeExecutable": "/usr/local/bin/node"
}
```

### IntelliJ IDEA

1. Install SonarLint plugin
2. Configure connection: Settings → Tools → SonarLint
3. Bind to SonarQube project

## Package.json Scripts

```json
{
  "scripts": {
    "sonar": "sonar-scanner",
    "sonar:local": "sonar-scanner -Dsonar.host.url=http://localhost:9000",
    "test:coverage": "jest --coverage"
  }
}
```

## Suppressing False Positives

### In Code

```typescript
// NOSONAR - Suppress all issues on this line
const password = 'hardcoded'; // NOSONAR

// Suppress specific rule
// @sonar-ignore-next-line typescript:S1186
function emptyCallback() {}
```

### In sonar-project.properties

```properties
# Exclude specific rules
sonar.issue.ignore.multicriteria=e1,e2

# Exclude rule S1186 in test files
sonar.issue.ignore.multicriteria.e1.ruleKey=typescript:S1186
sonar.issue.ignore.multicriteria.e1.resourceKey=**/*test*.ts

# Exclude rule S1135 (TODO comments) everywhere
sonar.issue.ignore.multicriteria.e2.ruleKey=typescript:S1135
sonar.issue.ignore.multicriteria.e2.resourceKey=**/*.ts
```

## Metrics Reference

| Metric | Description | Target |
|--------|-------------|--------|
| Coverage | % of code covered by tests | > 80% |
| Duplications | % of duplicated lines | < 3% |
| Complexity | Cyclomatic complexity | < 10/function |
| Technical Debt | Time to fix all issues | < 5% of dev time |
| Bugs | Reliability issues | 0 (new code) |
| Vulnerabilities | Security issues | 0 |
| Code Smells | Maintainability issues | A rating |
