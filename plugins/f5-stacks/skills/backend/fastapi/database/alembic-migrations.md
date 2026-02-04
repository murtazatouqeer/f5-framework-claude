---
name: fastapi-alembic-migrations
description: Alembic database migrations for FastAPI
applies_to: fastapi
category: skill
---

# Alembic Migrations for FastAPI

## Setup

### Installation

```bash
pip install alembic asyncpg
```

### Initialize Alembic

```bash
alembic init alembic
```

### Configuration

```ini
# alembic.ini
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os

# Use async for migrations
sqlalchemy.url = driver://user:pass@localhost/dbname

[post_write_hooks]
hooks = black
black.type = console_scripts
black.entrypoint = black
black.options = -q

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

### Async Environment

```python
# alembic/env.py
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Import your models
from app.database import Base
from app.config import settings

# Import all models to register them
from app.models import user, product, order, category  # noqa

config = context.config

# Set database URL from settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

## Migration Commands

```bash
# Generate migration from model changes
alembic revision --autogenerate -m "Add products table"

# Create empty migration
alembic revision -m "Custom migration"

# Run all migrations
alembic upgrade head

# Run specific migration
alembic upgrade +1
alembic upgrade abc123

# Rollback
alembic downgrade -1
alembic downgrade base

# Show current revision
alembic current

# Show history
alembic history

# Show pending migrations
alembic history --indicate-current
```

## Migration Examples

### Create Table

```python
# alembic/versions/001_create_users_table.py
"""Create users table

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_verified', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )

    # Create indexes
    op.create_index('idx_users_email', 'users', ['email'], unique=True)
    op.create_index('idx_users_created_at', 'users', ['created_at'])


def downgrade() -> None:
    op.drop_index('idx_users_created_at', table_name='users')
    op.drop_index('idx_users_email', table_name='users')
    op.drop_table('users')
```

### Add Column

```python
# alembic/versions/002_add_user_avatar.py
"""Add user avatar column

Revision ID: 002
Revises: 001
Create Date: 2024-01-02 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision: str = '002'
down_revision: str = '001'


def upgrade() -> None:
    op.add_column('users', sa.Column('avatar_url', sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'avatar_url')
```

### Create Enum

```python
# alembic/versions/003_add_product_status.py
"""Add product status enum

Revision ID: 003
Revises: 002
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '003'
down_revision: str = '002'

# Define enum
product_status = postgresql.ENUM(
    'draft', 'active', 'inactive', 'archived',
    name='productstatus'
)


def upgrade() -> None:
    # Create enum type
    product_status.create(op.get_bind())

    # Add column using enum
    op.add_column(
        'products',
        sa.Column(
            'status',
            product_status,
            nullable=False,
            server_default='draft'
        )
    )


def downgrade() -> None:
    op.drop_column('products', 'status')
    product_status.drop(op.get_bind())
```

### Add Foreign Key

```python
# alembic/versions/004_add_category_to_product.py
"""Add category foreign key to products

Revision ID: 004
Revises: 003
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '004'
down_revision: str = '003'


def upgrade() -> None:
    # Add column
    op.add_column(
        'products',
        sa.Column('category_id', postgresql.UUID(as_uuid=True), nullable=True)
    )

    # Add foreign key constraint
    op.create_foreign_key(
        'fk_products_category',
        'products', 'categories',
        ['category_id'], ['id'],
        ondelete='SET NULL'
    )

    # Add index
    op.create_index('idx_products_category', 'products', ['category_id'])


def downgrade() -> None:
    op.drop_index('idx_products_category', table_name='products')
    op.drop_constraint('fk_products_category', 'products', type_='foreignkey')
    op.drop_column('products', 'category_id')
```

### Data Migration

```python
# alembic/versions/005_migrate_user_data.py
"""Migrate user data

Revision ID: 005
Revises: 004
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session

revision: str = '005'
down_revision: str = '004'


def upgrade() -> None:
    # Get connection
    bind = op.get_bind()
    session = Session(bind=bind)

    # Migrate data
    session.execute(
        sa.text("""
            UPDATE users
            SET name = CONCAT(first_name, ' ', last_name)
            WHERE name IS NULL OR name = ''
        """)
    )

    session.commit()


def downgrade() -> None:
    # Data migrations are often not reversible
    pass
```

### Create Many-to-Many Table

```python
# alembic/versions/006_create_product_tags.py
"""Create product_tags junction table

Revision ID: 006
Revises: 005
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '006'
down_revision: str = '005'


def upgrade() -> None:
    op.create_table(
        'product_tags',
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tag_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint('product_id', 'tag_id'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
    )

    op.create_index('idx_product_tags_product', 'product_tags', ['product_id'])
    op.create_index('idx_product_tags_tag', 'product_tags', ['tag_id'])


def downgrade() -> None:
    op.drop_index('idx_product_tags_tag', table_name='product_tags')
    op.drop_index('idx_product_tags_product', table_name='product_tags')
    op.drop_table('product_tags')
```

## Helper Scripts

```python
# scripts/db.py
import asyncio
import click
from alembic import command
from alembic.config import Config


@click.group()
def cli():
    """Database management commands."""
    pass


@cli.command()
def migrate():
    """Run database migrations."""
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    click.echo("Migrations completed!")


@cli.command()
@click.argument("message")
def revision(message: str):
    """Create new migration."""
    alembic_cfg = Config("alembic.ini")
    command.revision(alembic_cfg, autogenerate=True, message=message)
    click.echo(f"Created migration: {message}")


@cli.command()
@click.option("--steps", default=1, help="Number of revisions to rollback")
def rollback(steps: int):
    """Rollback migrations."""
    alembic_cfg = Config("alembic.ini")
    command.downgrade(alembic_cfg, f"-{steps}")
    click.echo(f"Rolled back {steps} migration(s)")


if __name__ == "__main__":
    cli()
```

## Best Practices

1. **Use autogenerate** but always review generated migrations
2. **Name migrations descriptively** - "add_user_avatar" not "update"
3. **Keep migrations small** - one logical change per migration
4. **Test rollbacks** - ensure downgrade() works
5. **Use data migrations carefully** - they can be slow on large tables
6. **Don't modify old migrations** - create new ones instead
7. **Use batch operations** for large data changes
8. **Add indexes** for foreign keys and commonly queried columns
