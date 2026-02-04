---
name: rust-repository-generator
description: Generates repository trait and implementations
applies_to: rust
inputs:
  - name: entity_name
    description: Entity name (e.g., User, Product)
    required: true
  - name: table_name
    description: Database table name
    required: true
  - name: orm
    description: ORM to use (sqlx, diesel, sea-orm)
    required: false
    default: sqlx
  - name: custom_queries
    description: List of custom query methods to generate
    required: false
---

# Rust Repository Generator Agent

## Purpose

Generate repository pattern implementations with:
- Domain repository trait
- ORM-specific implementations
- Transaction support
- Custom query methods
- Unit tests with mocks

## Generation Process

### 1. Analyze Entity Structure

```yaml
analysis:
  - Parse entity fields and types
  - Identify indexed fields for query methods
  - Detect relationships for joins
  - Check for soft delete requirements
```

### 2. Generate Repository Trait

```rust
// src/domain/{{entity_name | snake_case}}/repository.rs

use async_trait::async_trait;
use uuid::Uuid;

use super::entity::{{entity_name}};
use crate::domain::common::{RepositoryError, RepositoryResult};

/// Repository trait for {{entity_name}} aggregate
#[async_trait]
pub trait {{entity_name}}Repository: Send + Sync {
    // Standard CRUD operations
    async fn find_by_id(&self, id: Uuid) -> RepositoryResult<Option<{{entity_name}}>>;
    async fn find_all(&self, offset: i64, limit: i64) -> RepositoryResult<Vec<{{entity_name}}>>;
    async fn count(&self) -> RepositoryResult<i64>;
    async fn save(&self, entity: &{{entity_name}}) -> RepositoryResult<()>;
    async fn update(&self, entity: &{{entity_name}}) -> RepositoryResult<()>;
    async fn delete(&self, id: Uuid) -> RepositoryResult<()>;
    async fn exists(&self, id: Uuid) -> RepositoryResult<bool>;

    {% for query in custom_queries %}
    /// {{query.description}}
    async fn {{query.name}}(&self, {{query.params}}) -> RepositoryResult<{{query.return_type}}>;
    {% endfor %}
}

// Re-export for convenience
pub use crate::infrastructure::persistence::repositories::{{entity_name | snake_case}}_repository::*;
```

### 3. Generate SQLx Implementation

```rust
// src/infrastructure/persistence/repositories/{{entity_name | snake_case}}_repository.rs

use async_trait::async_trait;
use sqlx::PgPool;
use uuid::Uuid;

use crate::domain::{{entity_name | snake_case}}::{
    entity::{{entity_name}},
    repository::{{entity_name}}Repository,
};
use crate::domain::common::{RepositoryError, RepositoryResult};
use crate::infrastructure::persistence::models::{{entity_name | snake_case}}::{{entity_name}}Model;

pub struct Sqlx{{entity_name}}Repository {
    pool: PgPool,
}

impl Sqlx{{entity_name}}Repository {
    pub fn new(pool: PgPool) -> Self {
        Self { pool }
    }
}

#[async_trait]
impl {{entity_name}}Repository for Sqlx{{entity_name}}Repository {
    #[tracing::instrument(name = "{{entity_name}}Repository::find_by_id", skip(self))]
    async fn find_by_id(&self, id: Uuid) -> RepositoryResult<Option<{{entity_name}}>> {
        let result = sqlx::query_as!(
            {{entity_name}}Model,
            r#"
            SELECT *
            FROM {{table_name}}
            WHERE id = $1
            {% if soft_delete %}AND deleted_at IS NULL{% endif %}
            "#,
            id
        )
        .fetch_optional(&self.pool)
        .await
        .map_err(|e| RepositoryError::Database(e.to_string()))?;

        Ok(result.map({{entity_name}}::from))
    }

    #[tracing::instrument(name = "{{entity_name}}Repository::find_all", skip(self))]
    async fn find_all(&self, offset: i64, limit: i64) -> RepositoryResult<Vec<{{entity_name}}>> {
        let results = sqlx::query_as!(
            {{entity_name}}Model,
            r#"
            SELECT *
            FROM {{table_name}}
            {% if soft_delete %}WHERE deleted_at IS NULL{% endif %}
            ORDER BY created_at DESC
            LIMIT $1 OFFSET $2
            "#,
            limit,
            offset
        )
        .fetch_all(&self.pool)
        .await
        .map_err(|e| RepositoryError::Database(e.to_string()))?;

        Ok(results.into_iter().map({{entity_name}}::from).collect())
    }

    #[tracing::instrument(name = "{{entity_name}}Repository::count", skip(self))]
    async fn count(&self) -> RepositoryResult<i64> {
        let result = sqlx::query_scalar!(
            r#"
            SELECT COUNT(*) as "count!"
            FROM {{table_name}}
            {% if soft_delete %}WHERE deleted_at IS NULL{% endif %}
            "#
        )
        .fetch_one(&self.pool)
        .await
        .map_err(|e| RepositoryError::Database(e.to_string()))?;

        Ok(result)
    }

    #[tracing::instrument(name = "{{entity_name}}Repository::save", skip(self, entity))]
    async fn save(&self, entity: &{{entity_name}}) -> RepositoryResult<()> {
        sqlx::query!(
            r#"
            INSERT INTO {{table_name}} (id, {% for field in fields %}{{field.name}}, {% endfor %}created_at, updated_at)
            VALUES ($1, {% for field in fields %}${{loop.index + 1}}, {% endfor %}${{fields.len + 2}}, ${{fields.len + 3}})
            "#,
            entity.id().as_uuid(),
            {% for field in fields %}
            entity.{{field.name}}(),
            {% endfor %}
            entity.created_at(),
            entity.updated_at(),
        )
        .execute(&self.pool)
        .await
        .map_err(|e| {
            if let sqlx::Error::Database(ref db_err) = e {
                if db_err.is_unique_violation() {
                    return RepositoryError::Conflict("{{entity_name}} already exists".to_string());
                }
            }
            RepositoryError::Database(e.to_string())
        })?;

        Ok(())
    }

    #[tracing::instrument(name = "{{entity_name}}Repository::update", skip(self, entity))]
    async fn update(&self, entity: &{{entity_name}}) -> RepositoryResult<()> {
        let result = sqlx::query!(
            r#"
            UPDATE {{table_name}}
            SET {% for field in fields %}{{field.name}} = ${{loop.index + 1}}, {% endfor %}updated_at = ${{fields.len + 2}}
            WHERE id = ${{fields.len + 3}}
            {% if soft_delete %}AND deleted_at IS NULL{% endif %}
            "#,
            {% for field in fields %}
            entity.{{field.name}}(),
            {% endfor %}
            entity.updated_at(),
            entity.id().as_uuid(),
        )
        .execute(&self.pool)
        .await
        .map_err(|e| RepositoryError::Database(e.to_string()))?;

        if result.rows_affected() == 0 {
            return Err(RepositoryError::NotFound);
        }

        Ok(())
    }

    #[tracing::instrument(name = "{{entity_name}}Repository::delete", skip(self))]
    async fn delete(&self, id: Uuid) -> RepositoryResult<()> {
        {% if soft_delete %}
        let result = sqlx::query!(
            r#"
            UPDATE {{table_name}}
            SET deleted_at = NOW()
            WHERE id = $1 AND deleted_at IS NULL
            "#,
            id
        )
        {% else %}
        let result = sqlx::query!(
            r#"DELETE FROM {{table_name}} WHERE id = $1"#,
            id
        )
        {% endif %}
        .execute(&self.pool)
        .await
        .map_err(|e| RepositoryError::Database(e.to_string()))?;

        if result.rows_affected() == 0 {
            return Err(RepositoryError::NotFound);
        }

        Ok(())
    }

    #[tracing::instrument(name = "{{entity_name}}Repository::exists", skip(self))]
    async fn exists(&self, id: Uuid) -> RepositoryResult<bool> {
        let result = sqlx::query_scalar!(
            r#"
            SELECT EXISTS(
                SELECT 1 FROM {{table_name}}
                WHERE id = $1
                {% if soft_delete %}AND deleted_at IS NULL{% endif %}
            ) as "exists!"
            "#,
            id
        )
        .fetch_one(&self.pool)
        .await
        .map_err(|e| RepositoryError::Database(e.to_string()))?;

        Ok(result)
    }

    {% for query in custom_queries %}
    #[tracing::instrument(name = "{{entity_name}}Repository::{{query.name}}", skip(self))]
    async fn {{query.name}}(&self, {{query.params}}) -> RepositoryResult<{{query.return_type}}> {
        {{query.implementation}}
    }
    {% endfor %}
}
```

### 4. Generate Transaction Support

```rust
// With transaction support
impl Sqlx{{entity_name}}Repository {
    pub async fn save_with_tx(
        &self,
        entity: &{{entity_name}},
        tx: &mut sqlx::Transaction<'_, sqlx::Postgres>,
    ) -> RepositoryResult<()> {
        sqlx::query!(
            r#"
            INSERT INTO {{table_name}} (id, name, created_at, updated_at)
            VALUES ($1, $2, $3, $4)
            "#,
            entity.id().as_uuid(),
            entity.name(),
            entity.created_at(),
            entity.updated_at(),
        )
        .execute(&mut **tx)
        .await
        .map_err(|e| RepositoryError::Database(e.to_string()))?;

        Ok(())
    }
}
```

### 5. Generate Mock for Testing

```rust
// For use with mockall in tests
use mockall::mock;

mock! {
    pub {{entity_name}}Repository {}

    #[async_trait]
    impl {{entity_name}}Repository for {{entity_name}}Repository {
        async fn find_by_id(&self, id: Uuid) -> RepositoryResult<Option<{{entity_name}}>>;
        async fn find_all(&self, offset: i64, limit: i64) -> RepositoryResult<Vec<{{entity_name}}>>;
        async fn count(&self) -> RepositoryResult<i64>;
        async fn save(&self, entity: &{{entity_name}}) -> RepositoryResult<()>;
        async fn update(&self, entity: &{{entity_name}}) -> RepositoryResult<()>;
        async fn delete(&self, id: Uuid) -> RepositoryResult<()>;
        async fn exists(&self, id: Uuid) -> RepositoryResult<bool>;
        {% for query in custom_queries %}
        async fn {{query.name}}(&self, {{query.params}}) -> RepositoryResult<{{query.return_type}}>;
        {% endfor %}
    }
}
```

## Usage

```bash
# Generate repository with default settings
f5 generate repository User --table users

# Generate with custom queries
f5 generate repository User --table users \
  --custom-queries "find_by_email:email:String:Option<User>,find_active:Vec<User>"

# Generate with soft delete
f5 generate repository Product --table products --soft-delete

# Generate for Diesel
f5 generate repository Order --table orders --orm diesel
```

## Output Files

```
src/domain/{{entity_name | snake_case}}/
├── mod.rs (updated)
└── repository.rs

src/infrastructure/persistence/repositories/
├── mod.rs (updated)
└── {{entity_name | snake_case}}_repository.rs
```
