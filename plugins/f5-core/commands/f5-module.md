---
description: Create or manage modules
argument-hint: <create|list|analyze> [name]
---

# /f5-module - Module Management

View and activate tech stack and domain modules for context-aware assistance.

## ARGUMENTS
The user's request is: $ARGUMENTS

## PURPOSE

Modules provide domain-specific knowledge:
- **Tech Modules**: Framework patterns, best practices, anti-patterns
- **Domain Modules**: Business logic, regulations, industry standards

## MODULE TYPES

### Tech Stack Modules

| Category | Modules |
|----------|---------|
| Backend | `nestjs`, `go`, `spring`, `fastapi`, `express`, `django`, `rails` |
| Frontend | `react`, `vue`, `angular`, `nextjs`, `nuxt`, `svelte` |
| Mobile | `flutter`, `react-native`, `swift`, `kotlin` |
| Database | `postgresql`, `mysql`, `mongodb`, `redis`, `elasticsearch` |
| Infrastructure | `kubernetes`, `docker`, `terraform`, `aws`, `gcp`, `azure` |
| Gateway | `nginx`, `kong`, `traefik`, `envoy` |

### Domain Modules

| Domain | Sub-domains |
|--------|-------------|
| `fintech` | stock-trading, p2p-lending, payment, banking, crypto |
| `e-commerce` | b2c-retail, b2b-wholesale, marketplace, subscription |
| `healthcare` | ehr, telemedicine, pharmacy, clinical-trials |
| `logistics` | warehouse, fleet, last-mile, supply-chain |
| `education` | lms, assessment, certification, e-learning |
| `entertainment` | streaming, gaming, esports, horse-racing |
| `saas` | multi-tenant, billing, analytics, crm |

## ACTIONS

### List Active Modules

```
/f5-module

Output:
📦 Active Modules

Tech Stack:
  ✓ nestjs     - Backend framework
  ✓ react      - Frontend framework
  ✓ postgresql - Primary database
  ✓ redis      - Cache layer

Domain:
  ✓ fintech/stock-trading - Retail variant

Source: .f5/config.json
```

### List Available Modules

```
/f5-module list

Output:
📋 Available Modules

TECH STACK:
┌─────────────┬─────────────────────────────────────────────┐
│ Category    │ Modules                                     │
├─────────────┼─────────────────────────────────────────────┤
│ Backend     │ nestjs, go, spring, fastapi, express        │
│ Frontend    │ react, vue, angular, nextjs, nuxt           │
│ Mobile      │ flutter, react-native, swift, kotlin        │
│ Database    │ postgresql, mysql, mongodb, redis           │
│ Infra       │ kubernetes, docker, terraform, aws          │
└─────────────┴─────────────────────────────────────────────┘

DOMAINS:
┌─────────────┬─────────────────────────────────────────────┐
│ Domain      │ Sub-domains                                 │
├─────────────┼─────────────────────────────────────────────┤
│ fintech     │ stock-trading, p2p-lending, payment         │
│ e-commerce  │ b2c-retail, marketplace, subscription       │
│ healthcare  │ ehr, telemedicine, pharmacy                 │
│ logistics   │ warehouse, fleet, last-mile                 │
│ education   │ lms, assessment, certification              │
│ saas        │ multi-tenant, billing, analytics            │
└─────────────┴─────────────────────────────────────────────┘
```

### Show Module Details

```
/f5-module show nestjs

Output:
📦 Module: nestjs

Type: Backend Framework
Category: TypeScript/Node.js

Provides:
• Module/Controller/Service patterns
• Dependency injection best practices
• Guard/Interceptor/Pipe patterns
• TypeORM/Prisma integration
• Testing patterns (jest)
• OpenAPI/Swagger documentation

Best Practices:
• Use DTOs for validation
• Implement custom exceptions
• Use ConfigService for env vars
• Apply guards at controller level

Anti-patterns to Avoid:
• Business logic in controllers
• Circular dependencies
• Missing validation pipes
• Hardcoded configurations

Related Modules:
• postgresql, mongodb (database)
• redis (caching)
• kubernetes (deployment)
```

### Show Domain Module

```
/f5-module show fintech/stock-trading

Output:
📦 Domain: fintech/stock-trading

Variant: retail (default)

Provides:
• Trading system patterns
• Order management flows
• Real-time price handling
• Portfolio calculation logic
• Risk management rules

Regulatory Knowledge:
• Securities regulations
• KYC/AML requirements
• Audit trail requirements
• Data retention policies

Integration Patterns:
• Market data feeds
• Order execution APIs
• Settlement systems
• Compliance reporting

Business Rules:
• Order validation
• Position limits
• Trading hours
• Price validation
```

### Activate Module

```
/f5-module activate go

Output:
✓ Module Activated: go

Added knowledge:
• Go project structure (cmd/, pkg/, internal/)
• Error handling patterns
• Concurrency best practices
• Testing with testify
• Go modules dependency management

Updated .f5/config.json

💡 Use /f5-sync to update CLAUDE.md
```

### Deactivate Module

```
/f5-module deactivate spring

Output:
✓ Module Deactivated: spring

Removed from active modules.
Updated .f5/config.json

💡 Use /f5-sync to update CLAUDE.md
```

### Auto-detect Modules

```
/f5-module detect

Output:
🔍 Auto-detecting modules...

Detected from project files:
  package.json → nestjs, react, typescript
  docker-compose.yml → postgresql, redis
  .f5/config.json → fintech/stock-trading

Suggested additions:
  ○ kubernetes (found k8s/ directory)
  ○ nginx (found nginx.conf)

Apply detected? [Y/n]
```

## MODULE KNOWLEDGE

### What Modules Provide

**Tech Modules:**
```yaml
patterns:
  - Project structure conventions
  - Code organization patterns
  - Common implementations

best_practices:
  - Security guidelines
  - Performance optimization
  - Error handling

anti_patterns:
  - Common mistakes to avoid
  - Security vulnerabilities
  - Performance pitfalls

integration:
  - How to combine with other modules
  - Configuration patterns
  - Migration guides
```

**Domain Modules:**
```yaml
business_rules:
  - Industry-specific logic
  - Validation requirements
  - Calculation formulas

regulations:
  - Compliance requirements
  - Data handling rules
  - Audit requirements

terminology:
  - Domain vocabulary
  - Standard abbreviations
  - Common concepts

workflows:
  - Business processes
  - State machines
  - Integration flows
```

## CONFIGURATION

Modules in `.f5/config.json`:

```json
{
  "stack": {
    "backend": ["nestjs"],
    "frontend": "react",
    "database": ["postgresql"],
    "cache": "redis",
    "queue": "kafka"
  },
  "domain": {
    "name": "fintech",
    "subDomain": "stock-trading",
    "variant": "retail"
  },
  "modules": {
    "active": ["nestjs", "react", "postgresql", "redis", "fintech"],
    "customPaths": {
      "internal-auth": "./modules/auth-module.yaml"
    }
  }
}
```

## CUSTOM MODULES

Create custom modules in `.claude/modules/`:

```yaml
# .claude/modules/internal-api.yaml
name: internal-api
type: custom
version: 1.0.0

provides:
  patterns:
    - "Internal API authentication flow"
    - "Rate limiting configuration"
    - "Error response format"

  endpoints:
    - name: /api/v1/users
      method: GET
      auth: required
    - name: /api/v1/orders
      method: POST
      auth: required

  rules:
    - "All responses use camelCase"
    - "Errors include correlation ID"
    - "Pagination uses cursor-based approach"
```

## EXAMPLES

```bash
# View active modules
/f5-module

# List all available modules
/f5-module list

# Show module details
/f5-module show nestjs
/f5-module show fintech/stock-trading

# Activate a module
/f5-module activate go
/f5-module activate e-commerce/marketplace

# Deactivate a module
/f5-module deactivate spring

# Auto-detect from project
/f5-module detect

# Search modules
/f5-module search payment
```

## INTEGRATION

### With Mode

```
Mode: development + Module: nestjs
→ Suggests NestJS patterns
→ Validates against NestJS best practices
→ Uses NestJS testing patterns

Mode: design + Module: fintech
→ Considers regulatory requirements
→ Applies security standards
→ Includes audit requirements
```

### With Strict Mode

```
Module: fintech/stock-trading
SIP Session Active

→ Requirements include domain-specific validations
→ Traceability includes business rule references
→ Tests cover regulatory requirements
```

---

**Tip:** Keep modules aligned with your actual tech stack. Run `/f5-module detect` when adding new technologies!
