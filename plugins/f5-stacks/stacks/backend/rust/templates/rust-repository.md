---
name: rust-repository
description: Repository pattern template with SQLx/Diesel/SeaORM
applies_to: rust
variables:
  - name: entity_name
    description: Entity name (e.g., User, Product)
  - name: table_name
    description: Database table name
  - name: orm
    description: ORM to use (sqlx, diesel, sea-orm)
---

# Rust Repository Template

## Repository Trait (Domain Layer)

```rust
// src/domain/{{entity_name | snake_case}}/repository.rs

use async_trait::async_trait;
use uuid::Uuid;

use super::entity::{{entity_name}};
use crate::domain::common::{RepositoryError, RepositoryResult};

/// Repository trait for {{entity_name}} aggregate
#[async_trait]
pub trait {{entity_name}}Repository: Send + Sync {
    /// Find {{entity_name}} by ID
    async fn find_by_id(&self, id: Uuid) -> RepositoryResult<Option<{{entity_name}}>>;

    /// Find all {{entity_name}}s with pagination
    async fn find_all(
        &self,
        offset: i64,
        limit: i64,
    ) -> RepositoryResult<Vec<{{entity_name}}>>;

    /// Count total {{entity_name}}s
    async fn count(&self) -> RepositoryResult<i64>;

    /// Save a new {{entity_name}}
    async fn save(&self, entity: &{{entity_name}}) -> RepositoryResult<()>;

    /// Update an existing {{entity_name}}
    async fn update(&self, entity: &{{entity_name}}) -> RepositoryResult<()>;

    /// Delete {{entity_name}} by ID
    async fn delete(&self, id: Uuid) -> RepositoryResult<()>;

    /// Check if {{entity_name}} exists by ID
    async fn exists(&self, id: Uuid) -> RepositoryResult<bool>;

    // Add domain-specific query methods here
    // async fn find_by_email(&self, email: &str) -> RepositoryResult<Option<{{entity_name}}>>;
}
```

## SQLx Implementation

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
            SELECT id, name, created_at, updated_at
            FROM {{table_name}}
            WHERE id = $1
            "#,
            id
        )
        .fetch_optional(&self.pool)
        .await
        .map_err(|e| RepositoryError::Database(e.to_string()))?;

        Ok(result.map({{entity_name}}::from))
    }

    #[tracing::instrument(name = "{{entity_name}}Repository::find_all", skip(self))]
    async fn find_all(
        &self,
        offset: i64,
        limit: i64,
    ) -> RepositoryResult<Vec<{{entity_name}}>> {
        let results = sqlx::query_as!(
            {{entity_name}}Model,
            r#"
            SELECT id, name, created_at, updated_at
            FROM {{table_name}}
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
            r#"SELECT COUNT(*) as "count!" FROM {{table_name}}"#
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
            INSERT INTO {{table_name}} (id, name, created_at, updated_at)
            VALUES ($1, $2, $3, $4)
            "#,
            entity.id().as_uuid(),
            entity.name(),
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
            SET name = $2, updated_at = $3
            WHERE id = $1
            "#,
            entity.id().as_uuid(),
            entity.name(),
            entity.updated_at(),
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
        let result = sqlx::query!(
            r#"DELETE FROM {{table_name}} WHERE id = $1"#,
            id
        )
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
            r#"SELECT EXISTS(SELECT 1 FROM {{table_name}} WHERE id = $1) as "exists!""#,
            id
        )
        .fetch_one(&self.pool)
        .await
        .map_err(|e| RepositoryError::Database(e.to_string()))?;

        Ok(result)
    }
}
```

## Diesel Implementation

```rust
// src/infrastructure/persistence/repositories/{{entity_name | snake_case}}_repository.rs

use async_trait::async_trait;
use diesel::prelude::*;
use diesel_async::{AsyncPgConnection, RunQueryDsl};
use uuid::Uuid;

use crate::domain::{{entity_name | snake_case}}::{
    entity::{{entity_name}},
    repository::{{entity_name}}Repository,
};
use crate::domain::common::{RepositoryError, RepositoryResult};
use crate::infrastructure::persistence::models::{{entity_name | snake_case}}::{
    {{entity_name}}Model, New{{entity_name}}, {{entity_name}}Changeset,
};
use crate::schema::{{table_name}};

pub struct Diesel{{entity_name}}Repository {
    pool: deadpool_diesel::Pool<AsyncPgConnection>,
}

impl Diesel{{entity_name}}Repository {
    pub fn new(pool: deadpool_diesel::Pool<AsyncPgConnection>) -> Self {
        Self { pool }
    }

    async fn get_conn(&self) -> Result<deadpool_diesel::Connection<AsyncPgConnection>, RepositoryError> {
        self.pool
            .get()
            .await
            .map_err(|e| RepositoryError::Database(e.to_string()))
    }
}

#[async_trait]
impl {{entity_name}}Repository for Diesel{{entity_name}}Repository {
    async fn find_by_id(&self, id: Uuid) -> RepositoryResult<Option<{{entity_name}}>> {
        let mut conn = self.get_conn().await?;

        let result = {{table_name}}::table
            .find(id)
            .first::<{{entity_name}}Model>(&mut conn)
            .await
            .optional()
            .map_err(|e| RepositoryError::Database(e.to_string()))?;

        Ok(result.map({{entity_name}}::from))
    }

    async fn find_all(&self, offset: i64, limit: i64) -> RepositoryResult<Vec<{{entity_name}}>> {
        let mut conn = self.get_conn().await?;

        let results = {{table_name}}::table
            .order({{table_name}}::created_at.desc())
            .offset(offset)
            .limit(limit)
            .load::<{{entity_name}}Model>(&mut conn)
            .await
            .map_err(|e| RepositoryError::Database(e.to_string()))?;

        Ok(results.into_iter().map({{entity_name}}::from).collect())
    }

    async fn count(&self) -> RepositoryResult<i64> {
        let mut conn = self.get_conn().await?;

        let count = {{table_name}}::table
            .count()
            .get_result::<i64>(&mut conn)
            .await
            .map_err(|e| RepositoryError::Database(e.to_string()))?;

        Ok(count)
    }

    async fn save(&self, entity: &{{entity_name}}) -> RepositoryResult<()> {
        let mut conn = self.get_conn().await?;

        let new_entity = New{{entity_name}}::from(entity);

        diesel::insert_into({{table_name}}::table)
            .values(&new_entity)
            .execute(&mut conn)
            .await
            .map_err(|e| RepositoryError::Database(e.to_string()))?;

        Ok(())
    }

    async fn update(&self, entity: &{{entity_name}}) -> RepositoryResult<()> {
        let mut conn = self.get_conn().await?;

        let changeset = {{entity_name}}Changeset::from(entity);

        let rows = diesel::update({{table_name}}::table.find(*entity.id().as_uuid()))
            .set(&changeset)
            .execute(&mut conn)
            .await
            .map_err(|e| RepositoryError::Database(e.to_string()))?;

        if rows == 0 {
            return Err(RepositoryError::NotFound);
        }

        Ok(())
    }

    async fn delete(&self, id: Uuid) -> RepositoryResult<()> {
        let mut conn = self.get_conn().await?;

        let rows = diesel::delete({{table_name}}::table.find(id))
            .execute(&mut conn)
            .await
            .map_err(|e| RepositoryError::Database(e.to_string()))?;

        if rows == 0 {
            return Err(RepositoryError::NotFound);
        }

        Ok(())
    }

    async fn exists(&self, id: Uuid) -> RepositoryResult<bool> {
        let mut conn = self.get_conn().await?;

        let exists = diesel::select(diesel::dsl::exists(
            {{table_name}}::table.find(id)
        ))
        .get_result::<bool>(&mut conn)
        .await
        .map_err(|e| RepositoryError::Database(e.to_string()))?;

        Ok(exists)
    }
}
```

## SeaORM Implementation

```rust
// src/infrastructure/persistence/repositories/{{entity_name | snake_case}}_repository.rs

use async_trait::async_trait;
use sea_orm::{
    ActiveModelTrait, ColumnTrait, DatabaseConnection, EntityTrait,
    PaginatorTrait, QueryFilter, QueryOrder, Set,
};
use uuid::Uuid;

use crate::domain::{{entity_name | snake_case}}::{
    entity::{{entity_name}},
    repository::{{entity_name}}Repository,
};
use crate::domain::common::{RepositoryError, RepositoryResult};
use crate::infrastructure::persistence::entities::{{entity_name | snake_case}}::{
    self, ActiveModel, Entity, Model,
};

pub struct SeaOrm{{entity_name}}Repository {
    db: DatabaseConnection,
}

impl SeaOrm{{entity_name}}Repository {
    pub fn new(db: DatabaseConnection) -> Self {
        Self { db }
    }
}

#[async_trait]
impl {{entity_name}}Repository for SeaOrm{{entity_name}}Repository {
    async fn find_by_id(&self, id: Uuid) -> RepositoryResult<Option<{{entity_name}}>> {
        let result = Entity::find_by_id(id)
            .one(&self.db)
            .await
            .map_err(|e| RepositoryError::Database(e.to_string()))?;

        Ok(result.map({{entity_name}}::from))
    }

    async fn find_all(&self, offset: i64, limit: i64) -> RepositoryResult<Vec<{{entity_name}}>> {
        let results = Entity::find()
            .order_by_desc({{entity_name | snake_case}}::Column::CreatedAt)
            .offset(offset as u64)
            .limit(limit as u64)
            .all(&self.db)
            .await
            .map_err(|e| RepositoryError::Database(e.to_string()))?;

        Ok(results.into_iter().map({{entity_name}}::from).collect())
    }

    async fn count(&self) -> RepositoryResult<i64> {
        let count = Entity::find()
            .count(&self.db)
            .await
            .map_err(|e| RepositoryError::Database(e.to_string()))?;

        Ok(count as i64)
    }

    async fn save(&self, entity: &{{entity_name}}) -> RepositoryResult<()> {
        let active_model = ActiveModel::from(entity);

        active_model
            .insert(&self.db)
            .await
            .map_err(|e| RepositoryError::Database(e.to_string()))?;

        Ok(())
    }

    async fn update(&self, entity: &{{entity_name}}) -> RepositoryResult<()> {
        let active_model = ActiveModel::from(entity);

        active_model
            .update(&self.db)
            .await
            .map_err(|e| RepositoryError::Database(e.to_string()))?;

        Ok(())
    }

    async fn delete(&self, id: Uuid) -> RepositoryResult<()> {
        let result = Entity::delete_by_id(id)
            .exec(&self.db)
            .await
            .map_err(|e| RepositoryError::Database(e.to_string()))?;

        if result.rows_affected == 0 {
            return Err(RepositoryError::NotFound);
        }

        Ok(())
    }

    async fn exists(&self, id: Uuid) -> RepositoryResult<bool> {
        let count = Entity::find_by_id(id)
            .count(&self.db)
            .await
            .map_err(|e| RepositoryError::Database(e.to_string()))?;

        Ok(count > 0)
    }
}
```

## Unit of Work Pattern

```rust
// src/infrastructure/persistence/unit_of_work.rs

use async_trait::async_trait;
use sqlx::{PgPool, Transaction, Postgres};

#[async_trait]
pub trait UnitOfWork {
    type Tx;

    async fn begin(&self) -> Result<Self::Tx, RepositoryError>;
    async fn commit(tx: Self::Tx) -> Result<(), RepositoryError>;
    async fn rollback(tx: Self::Tx) -> Result<(), RepositoryError>;
}

pub struct SqlxUnitOfWork {
    pool: PgPool,
}

#[async_trait]
impl UnitOfWork for SqlxUnitOfWork {
    type Tx = Transaction<'static, Postgres>;

    async fn begin(&self) -> Result<Self::Tx, RepositoryError> {
        self.pool
            .begin()
            .await
            .map_err(|e| RepositoryError::Database(e.to_string()))
    }

    async fn commit(tx: Self::Tx) -> Result<(), RepositoryError> {
        tx.commit()
            .await
            .map_err(|e| RepositoryError::Database(e.to_string()))
    }

    async fn rollback(tx: Self::Tx) -> Result<(), RepositoryError> {
        tx.rollback()
            .await
            .map_err(|e| RepositoryError::Database(e.to_string()))
    }
}
```
