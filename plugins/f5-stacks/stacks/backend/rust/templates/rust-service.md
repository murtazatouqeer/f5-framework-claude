---
name: rust-service
description: Application service template
applies_to: rust
variables:
  - name: entity_name
    description: Entity name (e.g., User, Product)
  - name: operations
    description: List of service operations
---

# Rust Service Template

## Application Service

```rust
// src/application/{{entity_name | snake_case}}/service.rs

use std::sync::Arc;
use uuid::Uuid;

use crate::application::{{entity_name | snake_case}}::{
    Create{{entity_name}}Dto,
    Update{{entity_name}}Dto,
    {{entity_name}}ListQuery,
};
use crate::domain::{{entity_name | snake_case}}::{
    entity::{{entity_name}},
    repository::{{entity_name}}Repository,
};
use crate::error::{AppError, Result};

/// Application service for {{entity_name}} operations
pub struct {{entity_name}}Service {
    repository: Arc<dyn {{entity_name}}Repository>,
    // Add other dependencies
    // event_publisher: Arc<dyn EventPublisher>,
    // cache: Arc<dyn Cache>,
}

impl {{entity_name}}Service {
    pub fn new(repository: Arc<dyn {{entity_name}}Repository>) -> Self {
        Self { repository }
    }

    /// Get {{entity_name}} by ID
    #[tracing::instrument(name = "{{entity_name}}Service::get_by_id", skip(self))]
    pub async fn get_by_id(&self, id: Uuid) -> Result<{{entity_name}}> {
        self.repository
            .find_by_id(id)
            .await?
            .ok_or(AppError::NotFound(format!("{{entity_name}} with id {} not found", id)))
    }

    /// List {{entity_name}}s with pagination
    #[tracing::instrument(name = "{{entity_name}}Service::list", skip(self))]
    pub async fn list(&self, query: {{entity_name}}ListQuery) -> Result<(Vec<{{entity_name}}>, i64)> {
        let page = query.page.unwrap_or(1);
        let per_page = query.per_page.unwrap_or(20).min(100);
        let offset = ((page - 1) * per_page) as i64;
        let limit = per_page as i64;

        let items = self.repository.find_all(offset, limit).await?;
        let total = self.repository.count().await?;

        Ok((items, total))
    }

    /// Create new {{entity_name}}
    #[tracing::instrument(name = "{{entity_name}}Service::create", skip(self, dto))]
    pub async fn create(&self, dto: Create{{entity_name}}Dto) -> Result<{{entity_name}}> {
        // Validate DTO
        dto.validate()?;

        // Business logic validation
        // e.g., check for duplicates, validate references, etc.

        // Create domain entity
        let entity = {{entity_name}}::new(
            dto.name,
            // ... other fields
        ).map_err(|errors| {
            AppError::Validation(
                errors.into_iter().map(|e| e.to_string()).collect::<Vec<_>>().join(", ")
            )
        })?;

        // Persist
        self.repository.save(&entity).await?;

        // Publish domain events
        // self.event_publisher.publish({{entity_name}}Created::new(&entity)).await?;

        tracing::info!(
            {{entity_name | snake_case}}_id = %entity.id(),
            "Created new {{entity_name}}"
        );

        Ok(entity)
    }

    /// Update existing {{entity_name}}
    #[tracing::instrument(name = "{{entity_name}}Service::update", skip(self, dto))]
    pub async fn update(&self, id: Uuid, dto: Update{{entity_name}}Dto) -> Result<{{entity_name}}> {
        // Validate DTO
        dto.validate()?;

        // Fetch existing entity
        let mut entity = self.get_by_id(id).await?;

        // Apply updates
        if let Some(name) = dto.name {
            entity.set_name(name)?;
        }
        // ... other fields

        // Persist
        self.repository.update(&entity).await?;

        // Publish domain events
        // self.event_publisher.publish({{entity_name}}Updated::new(&entity)).await?;

        tracing::info!(
            {{entity_name | snake_case}}_id = %entity.id(),
            "Updated {{entity_name}}"
        );

        Ok(entity)
    }

    /// Delete {{entity_name}}
    #[tracing::instrument(name = "{{entity_name}}Service::delete", skip(self))]
    pub async fn delete(&self, id: Uuid) -> Result<()> {
        // Verify exists
        let entity = self.get_by_id(id).await?;

        // Business logic validation
        // e.g., check if can be deleted, no dependencies, etc.

        // Delete
        self.repository.delete(id).await?;

        // Publish domain events
        // self.event_publisher.publish({{entity_name}}Deleted::new(&entity)).await?;

        tracing::info!(
            {{entity_name | snake_case}}_id = %id,
            "Deleted {{entity_name}}"
        );

        Ok(())
    }

    // Add domain-specific operations here
    // pub async fn activate(&self, id: Uuid) -> Result<{{entity_name}}> { ... }
    // pub async fn deactivate(&self, id: Uuid) -> Result<{{entity_name}}> { ... }
}

#[cfg(test)]
mod tests {
    use super::*;
    use mockall::predicate::*;

    #[tokio::test]
    async fn test_get_by_id_success() {
        let mut mock_repo = MockRepository::new();
        mock_repo
            .expect_find_by_id()
            .with(eq(test_id()))
            .times(1)
            .returning(|_| Ok(Some(create_test_entity())));

        let service = {{entity_name}}Service::new(Arc::new(mock_repo));
        let result = service.get_by_id(test_id()).await;

        assert!(result.is_ok());
    }

    #[tokio::test]
    async fn test_get_by_id_not_found() {
        let mut mock_repo = MockRepository::new();
        mock_repo
            .expect_find_by_id()
            .with(eq(test_id()))
            .times(1)
            .returning(|_| Ok(None));

        let service = {{entity_name}}Service::new(Arc::new(mock_repo));
        let result = service.get_by_id(test_id()).await;

        assert!(matches!(result, Err(AppError::NotFound(_))));
    }

    #[tokio::test]
    async fn test_create_success() {
        let mut mock_repo = MockRepository::new();
        mock_repo
            .expect_save()
            .times(1)
            .returning(|_| Ok(()));

        let service = {{entity_name}}Service::new(Arc::new(mock_repo));
        let dto = Create{{entity_name}}Dto {
            name: "Test".to_string(),
            // ...
        };

        let result = service.create(dto).await;
        assert!(result.is_ok());
    }

    #[tokio::test]
    async fn test_delete_not_found() {
        let mut mock_repo = MockRepository::new();
        mock_repo
            .expect_find_by_id()
            .times(1)
            .returning(|_| Ok(None));

        let service = {{entity_name}}Service::new(Arc::new(mock_repo));
        let result = service.delete(test_id()).await;

        assert!(matches!(result, Err(AppError::NotFound(_))));
    }
}
```

## Service with Transactions

```rust
// src/application/{{entity_name | snake_case}}/service.rs

use std::sync::Arc;
use sqlx::{PgPool, Transaction, Postgres};

pub struct {{entity_name}}Service {
    pool: PgPool,
    repository: Arc<dyn {{entity_name}}Repository>,
    related_repository: Arc<dyn RelatedRepository>,
}

impl {{entity_name}}Service {
    /// Create with related entities (transactional)
    pub async fn create_with_related(
        &self,
        dto: Create{{entity_name}}WithRelatedDto,
    ) -> Result<{{entity_name}}> {
        let mut tx = self.pool.begin().await?;

        // Create main entity
        let entity = {{entity_name}}::new(dto.name)?;
        self.repository.save_with_tx(&entity, &mut tx).await?;

        // Create related entities
        for related_dto in dto.related_items {
            let related = Related::new(entity.id(), related_dto)?;
            self.related_repository.save_with_tx(&related, &mut tx).await?;
        }

        // Commit transaction
        tx.commit().await?;

        Ok(entity)
    }

    /// Delete with cascade (transactional)
    pub async fn delete_cascade(&self, id: Uuid) -> Result<()> {
        let mut tx = self.pool.begin().await?;

        // Delete related first
        self.related_repository.delete_by_parent_with_tx(id, &mut tx).await?;

        // Delete main entity
        self.repository.delete_with_tx(id, &mut tx).await?;

        tx.commit().await?;

        Ok(())
    }
}
```

## Service with Caching

```rust
// src/application/{{entity_name | snake_case}}/service.rs

use std::sync::Arc;
use tokio::sync::RwLock;
use std::collections::HashMap;

pub struct {{entity_name}}Service {
    repository: Arc<dyn {{entity_name}}Repository>,
    cache: Arc<RwLock<HashMap<Uuid, {{entity_name}}>>>,
    cache_ttl: std::time::Duration,
}

impl {{entity_name}}Service {
    pub async fn get_by_id_cached(&self, id: Uuid) -> Result<{{entity_name}}> {
        // Check cache
        {
            let cache = self.cache.read().await;
            if let Some(entity) = cache.get(&id) {
                return Ok(entity.clone());
            }
        }

        // Fetch from database
        let entity = self.repository
            .find_by_id(id)
            .await?
            .ok_or(AppError::NotFound(format!("{{entity_name}} {} not found", id)))?;

        // Update cache
        {
            let mut cache = self.cache.write().await;
            cache.insert(id, entity.clone());
        }

        Ok(entity)
    }

    pub async fn invalidate_cache(&self, id: Uuid) {
        let mut cache = self.cache.write().await;
        cache.remove(&id);
    }

    pub async fn clear_cache(&self) {
        let mut cache = self.cache.write().await;
        cache.clear();
    }
}
```

## Service with Events

```rust
// src/application/{{entity_name | snake_case}}/service.rs

use crate::domain::events::{DomainEvent, EventPublisher};

pub struct {{entity_name}}Service {
    repository: Arc<dyn {{entity_name}}Repository>,
    event_publisher: Arc<dyn EventPublisher>,
}

impl {{entity_name}}Service {
    pub async fn create(&self, dto: Create{{entity_name}}Dto) -> Result<{{entity_name}}> {
        let entity = {{entity_name}}::new(dto.name)?;

        self.repository.save(&entity).await?;

        // Publish event
        self.event_publisher
            .publish(DomainEvent::{{entity_name}}Created {
                id: *entity.id().as_uuid(),
                name: entity.name().to_string(),
                timestamp: chrono::Utc::now(),
            })
            .await?;

        Ok(entity)
    }
}

// Event definitions
#[derive(Debug, Clone, serde::Serialize)]
pub enum DomainEvent {
    {{entity_name}}Created {
        id: Uuid,
        name: String,
        timestamp: chrono::DateTime<chrono::Utc>,
    },
    {{entity_name}}Updated {
        id: Uuid,
        changes: Vec<String>,
        timestamp: chrono::DateTime<chrono::Utc>,
    },
    {{entity_name}}Deleted {
        id: Uuid,
        timestamp: chrono::DateTime<chrono::Utc>,
    },
}
```
