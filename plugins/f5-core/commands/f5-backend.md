---
description: Backend development commands
argument-hint: <generate|scaffold> <type> [name]
---

# /f5-backend - Backend Development Assistant

Hỗ trợ phát triển backend theo stack đã chọn trong project.

## ARGUMENTS
The user's request is: $ARGUMENTS

## DETECT BACKEND STACK

```bash
# Auto-detect from .f5/config.json
STACK=$(jq -r '.stack.backend // "nestjs"' .f5/config.json 2>/dev/null)
```

## STACK-SPECIFIC COMMANDS

### NestJS (Default)

| Command | Description |
|---------|-------------|
| `module <name>` | Generate NestJS module with CRUD |
| `service <name>` | Generate service with repository pattern |
| `controller <name>` | Generate REST controller |
| `guard <name>` | Generate auth guard |
| `dto <name>` | Generate DTO with validation |
| `entity <name>` | Generate Prisma/TypeORM entity |

### FastAPI (Python)

| Command | Description |
|---------|-------------|
| `router <name>` | Generate FastAPI router |
| `service <name>` | Generate service class |
| `model <name>` | Generate Pydantic model |
| `schema <name>` | Generate SQLAlchemy schema |

### Spring Boot (Java)

| Command | Description |
|---------|-------------|
| `controller <name>` | Generate REST controller |
| `service <name>` | Generate service with interface |
| `repository <name>` | Generate JPA repository |
| `entity <name>` | Generate JPA entity |
| `dto <name>` | Generate DTO with MapStruct |

### Go (Gin)

| Command | Description |
|---------|-------------|
| `handler <name>` | Generate Gin handler |
| `service <name>` | Generate service layer |
| `repository <name>` | Generate GORM repository |
| `model <name>` | Generate Go struct |

### Django (Python)

| Command | Description |
|---------|-------------|
| `app <name>` | Create Django app |
| `model <name>` | Generate Django model |
| `view <name>` | Generate DRF viewset |
| `serializer <name>` | Generate DRF serializer |

### Laravel (PHP)

| Command | Description |
|---------|-------------|
| `controller <name>` | Generate controller |
| `model <name>` | Generate Eloquent model |
| `migration <name>` | Generate migration |
| `resource <name>` | Generate API resource |

### Rails (Ruby)

| Command | Description |
|---------|-------------|
| `scaffold <name>` | Generate full scaffold |
| `model <name>` | Generate ActiveRecord model |
| `controller <name>` | Generate controller |
| `serializer <name>` | Generate serializer |

### .NET Core (C#)

| Command | Description |
|---------|-------------|
| `controller <name>` | Generate API controller |
| `service <name>` | Generate service with DI |
| `entity <name>` | Generate EF Core entity |
| `dto <name>` | Generate DTO with AutoMapper |

### Rust (Actix)

| Command | Description |
|---------|-------------|
| `handler <name>` | Generate Actix handler |
| `service <name>` | Generate service |
| `model <name>` | Generate Diesel model |

## EXECUTION

Based on detected stack and user request:

```markdown
## Backend: {{STACK}}

### Generated Files:
{{list of generated files}}

### Next Steps:
{{stack-specific recommendations}}

### Related Commands:
- /f5-db migrate    - Run database migrations
- /f5-test-unit     - Run unit tests
- /f5-test-it api   - Run API integration tests
```

## EXAMPLES

```bash
# NestJS
/f5-backend module users
/f5-backend service auth
/f5-backend guard jwt

# FastAPI
/f5-backend router users
/f5-backend model User

# Spring
/f5-backend controller UserController
/f5-backend entity User

# Go
/f5-backend handler user
/f5-backend service user
```

## BEST PRACTICES

Claude sẽ tự động áp dụng best practices theo stack:

| Stack | Patterns Applied |
|-------|-----------------|
| NestJS | Repository pattern, DTOs, Guards |
| FastAPI | Dependency injection, Pydantic validation |
| Spring | Layered architecture, JPA best practices |
| Go | Clean architecture, interface-based |
| Django | Fat models, thin views |
| Laravel | Service layer, Repository pattern |
| Rails | Convention over configuration |
| .NET | CQRS, Mediator pattern |
| Rust | Actor model, async patterns |
