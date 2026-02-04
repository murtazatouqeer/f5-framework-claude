---
description: Database operations and migrations
argument-hint: <migrate|seed|schema> [action]
---

# /f5-db - Database Management Assistant

Hỗ trợ quản lý database theo stack đã chọn trong project.

## ARGUMENTS
The user's request is: $ARGUMENTS

## DETECT DATABASE STACK

```bash
# Auto-detect from .f5/config.json
DB=$(jq -r '.stack.database // "postgresql"' .f5/config.json 2>/dev/null)
BACKEND=$(jq -r '.stack.backend // "nestjs"' .f5/config.json 2>/dev/null)
```

## COMMANDS

| Command | Description |
|---------|-------------|
| `schema` | View current database schema |
| `migrate` | Run pending migrations |
| `migrate create <name>` | Create new migration |
| `migrate rollback` | Rollback last migration |
| `seed` | Run database seeders |
| `seed create <name>` | Create new seeder |
| `reset` | Reset database (migrate + seed) |
| `model <name>` | Generate model/entity |
| `diagram` | Generate ER diagram |

## DATABASE + ORM COMBINATIONS

| Backend | Database | ORM/Client |
|---------|----------|------------|
| NestJS | PostgreSQL | Prisma |
| NestJS | MySQL | TypeORM |
| FastAPI | PostgreSQL | SQLAlchemy |
| Django | PostgreSQL | Django ORM |
| Spring | PostgreSQL | JPA/Hibernate |
| Go | PostgreSQL | GORM |
| Laravel | MySQL | Eloquent |
| Rails | PostgreSQL | ActiveRecord |
| .NET | SQL Server | Entity Framework |
| Rust | PostgreSQL | Diesel |

## EXECUTION

### Schema Operations

```bash
# View schema
/f5-db schema

# Generate schema diagram
/f5-db diagram
```

Output:
```markdown
## Database Schema: {{DB_NAME}}

### Tables:
{{table list with columns}}

### Relationships:
{{ER diagram in mermaid}}
```

### Migration Operations

```bash
# Create migration
/f5-db migrate create add_users_table

# Run migrations
/f5-db migrate

# Rollback
/f5-db migrate rollback
```

### Model Generation

```bash
# Generate model from table
/f5-db model User

# Generate with relations
/f5-db model Order --relations
```

## ORM-SPECIFIC COMMANDS

### Prisma (NestJS)

```bash
/f5-db prisma generate     # Generate client
/f5-db prisma studio       # Open Prisma Studio
/f5-db prisma format       # Format schema
```

### SQLAlchemy (FastAPI)

```bash
/f5-db alembic revision    # Create revision
/f5-db alembic upgrade     # Apply migrations
/f5-db alembic downgrade   # Rollback
```

### Django ORM

```bash
/f5-db makemigrations      # Create migrations
/f5-db migrate             # Apply migrations
/f5-db shell               # Database shell
```

### TypeORM (NestJS)

```bash
/f5-db typeorm migration:create
/f5-db typeorm migration:run
/f5-db typeorm migration:revert
```

### Eloquent (Laravel)

```bash
/f5-db artisan migrate
/f5-db artisan migrate:rollback
/f5-db artisan db:seed
```

## EXAMPLES

```bash
# Schema operations
/f5-db schema
/f5-db diagram

# Migrations
/f5-db migrate create create_orders_table
/f5-db migrate
/f5-db migrate rollback

# Models
/f5-db model User
/f5-db model Product --relations

# Seeding
/f5-db seed create UserSeeder
/f5-db seed

# Reset for development
/f5-db reset
```

## NOSQL SUPPORT

### MongoDB

```bash
/f5-db mongo schema        # View collections
/f5-db mongo index <col>   # Create indexes
/f5-db mongo model <name>  # Generate Mongoose model
```

### Redis

```bash
/f5-db redis keys          # List keys
/f5-db redis flush         # Flush database
/f5-db redis info          # Show info
```

## BEST PRACTICES

Claude automatically applies:

1. **Naming Conventions**
   - Tables: snake_case, plural (users, order_items)
   - Columns: snake_case (created_at, user_id)
   - Indexes: idx_table_column

2. **Common Patterns**
   - Soft deletes (deleted_at)
   - Timestamps (created_at, updated_at)
   - UUID primary keys (optional)
   - Foreign key constraints

3. **Performance**
   - Index suggestions
   - Query optimization hints
   - Connection pooling setup

4. **Security**
   - Parameterized queries
   - Role-based access
   - Encryption for sensitive data

## RELATED COMMANDS

- /f5-backend entity  - Generate backend entity
- /f5-design db       - Database design documentation
- /f5-test-it database - Database integration tests
