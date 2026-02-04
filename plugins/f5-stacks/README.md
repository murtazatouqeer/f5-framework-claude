# F5 Stacks Plugin

Technology stacks, domain knowledge, and stack-specific development skills for the F5 Framework.

## Installation

```bash
# Via Claude Code plugin system (requires f5-core)
/plugin marketplace add fujigo/f5-framework

# This plugin is automatically included with the main f5-framework marketplace
```

## Contents

### Technology Stacks

Comprehensive stack definitions for:

**Backend**
- NestJS, Spring Boot, Laravel, Django, FastAPI, Express
- Database integrations (PostgreSQL, MySQL, MongoDB, Redis)

**Frontend**
- React, Angular, Vue.js, Next.js, Nuxt.js
- State management (Redux, Zustand, Pinia)

**Mobile**
- Flutter, React Native
- iOS (Swift), Android (Kotlin)

**Infrastructure**
- Docker, Kubernetes
- Terraform, AWS CDK, Pulumi
- CI/CD pipelines

**Gateway**
- API Gateway patterns
- GraphQL Federation

### Domain Knowledge (14 domains)

Industry-specific knowledge and patterns:
- Agriculture
- E-commerce
- Education
- Entertainment
- Fintech
- Healthcare
- HR Management
- Insurance
- Logistics
- Manufacturing
- Media & Entertainment
- Real Estate
- SaaS Platform
- Travel & Hospitality

### Stack-Specific Skills

Advanced skills for each technology stack:
- Best practices and patterns
- Performance optimization
- Security considerations
- Testing strategies
- Deployment configurations

### Workflow Templates

Generic workflow templates for:
- POC (Proof of Concept)
- MVP development
- Enterprise projects
- Legacy migration
- Greenfield development
- Performance optimization
- Reverse engineering

## Usage

Stack skills are automatically available when using F5 Framework commands:

```bash
# Analyze with stack context
/f5-analyze --stack nestjs

# Implement with domain knowledge
/f5-implement --domain fintech --stack react
```

## Dependencies

This plugin requires **f5-core** plugin to be installed.

## License

MIT

---
*Part of the [F5 Framework](https://github.com/fujigo/f5-framework)*
