---
name: rust-service-generator
description: Generates application services with business logic
applies_to: rust
inputs:
  - name: entity_name
    description: Entity name (e.g., User, Product)
    required: true
  - name: operations
    description: List of service operations
    required: false
    default: [get, list, create, update, delete]
  - name: with_caching
    description: Include caching layer
    required: false
    default: false
  - name: with_events
    description: Include domain event publishing
    required: false
    default: false
---

# Rust Service Generator Agent

## Purpose

Generate application layer services with:
- Business logic orchestration
- Transaction management
- Caching integration
- Event publishing
- Comprehensive tests

## Generation Process

### 1. Analyze Service Requirements

```yaml
analysis:
  - Identify required dependencies (repositories, other services)
  - Determine caching strategy
  - Check for event publishing needs
  - Review authorization requirements
```

### 2. Generate Service Implementation

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
{% if with_events %}
use crate::domain::events::{DomainEvent, EventPublisher};
{% endif %}
{% if with_caching %}
use crate::infrastructure::cache::Cache;
{% endif %}

/// Application service for {{entity_name}} operations
pub struct {{entity_name}}Service {
    repository: Arc<dyn {{entity_name}}Repository>,
    {% if with_events %}
    event_publisher: Arc<dyn EventPublisher>,
    {% endif %}
    {% if with_caching %}
    cache: Arc<dyn Cache>,
    {% endif %}
}

impl {{entity_name}}Service {
    pub fn new(
        repository: Arc<dyn {{entity_name}}Repository>,
        {% if with_events %}
        event_publisher: Arc<dyn EventPublisher>,
        {% endif %}
        {% if with_caching %}
        cache: Arc<dyn Cache>,
        {% endif %}
    ) -> Self {
        Self {
            repository,
            {% if with_events %}
            event_publisher,
            {% endif %}
            {% if with_caching %}
            cache,
            {% endif %}
        }
    }

    /// Get {{entity_name}} by ID
    #[tracing::instrument(name = "{{entity_name}}Service::get_by_id", skip(self))]
    pub async fn get_by_id(&self, id: Uuid) -> Result<{{entity_name}}> {
        {% if with_caching %}
        // Check cache first
        let cache_key = format!("{{entity_name | snake_case}}:{}", id);
        if let Some(cached) = self.cache.get::<{{entity_name}}>(&cache_key).await? {
            tracing::debug!(id = %id, "Cache hit for {{entity_name}}");
            return Ok(cached);
        }
        {% endif %}

        let entity = self.repository
            .find_by_id(id)
            .await?
            .ok_or_else(|| AppError::NotFound(format!("{{entity_name}} with id {} not found", id)))?;

        {% if with_caching %}
        // Store in cache
        self.cache.set(&cache_key, &entity, std::time::Duration::from_secs(300)).await?;
        {% endif %}

        Ok(entity)
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

        // Additional business validation
        self.validate_create(&dto).await?;

        // Create domain entity
        let entity = {{entity_name}}::new(
            dto.name,
            // ... other fields from dto
        ).map_err(|errors| {
            AppError::Validation(
                errors.into_iter().map(|e| e.to_string()).collect::<Vec<_>>().join(", ")
            )
        })?;

        // Persist
        self.repository.save(&entity).await?;

        {% if with_events %}
        // Publish domain event
        self.event_publisher
            .publish(DomainEvent::{{entity_name}}Created {
                id: *entity.id().as_uuid(),
                timestamp: chrono::Utc::now(),
            })
            .await?;
        {% endif %}

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

        // Track changes for events
        {% if with_events %}
        let mut changes = Vec::new();
        {% endif %}

        // Apply updates
        if let Some(name) = dto.name {
            {% if with_events %}
            if entity.name() != &name {
                changes.push("name".to_string());
            }
            {% endif %}
            entity.set_name(name)?;
        }
        // ... other fields

        // Persist
        self.repository.update(&entity).await?;

        {% if with_caching %}
        // Invalidate cache
        let cache_key = format!("{{entity_name | snake_case}}:{}", id);
        self.cache.delete(&cache_key).await?;
        {% endif %}

        {% if with_events %}
        // Publish domain event
        if !changes.is_empty() {
            self.event_publisher
                .publish(DomainEvent::{{entity_name}}Updated {
                    id: *entity.id().as_uuid(),
                    changes,
                    timestamp: chrono::Utc::now(),
                })
                .await?;
        }
        {% endif %}

        tracing::info!(
            {{entity_name | snake_case}}_id = %entity.id(),
            "Updated {{entity_name}}"
        );

        Ok(entity)
    }

    /// Delete {{entity_name}}
    #[tracing::instrument(name = "{{entity_name}}Service::delete", skip(self))]
    pub async fn delete(&self, id: Uuid) -> Result<()> {
        // Verify exists and can be deleted
        let entity = self.get_by_id(id).await?;

        // Business rule validation
        self.validate_delete(&entity).await?;

        // Delete
        self.repository.delete(id).await?;

        {% if with_caching %}
        // Invalidate cache
        let cache_key = format!("{{entity_name | snake_case}}:{}", id);
        self.cache.delete(&cache_key).await?;
        {% endif %}

        {% if with_events %}
        // Publish domain event
        self.event_publisher
            .publish(DomainEvent::{{entity_name}}Deleted {
                id,
                timestamp: chrono::Utc::now(),
            })
            .await?;
        {% endif %}

        tracing::info!(
            {{entity_name | snake_case}}_id = %id,
            "Deleted {{entity_name}}"
        );

        Ok(())
    }

    // Private validation methods
    async fn validate_create(&self, dto: &Create{{entity_name}}Dto) -> Result<()> {
        // Add business rule validations here
        // Example: check for duplicates, validate references, etc.
        Ok(())
    }

    async fn validate_delete(&self, entity: &{{entity_name}}) -> Result<()> {
        // Add business rule validations here
        // Example: check for dependencies, status restrictions, etc.
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use mockall::predicate::*;

    fn test_id() -> Uuid {
        Uuid::parse_str("550e8400-e29b-41d4-a716-446655440000").unwrap()
    }

    fn create_test_entity() -> {{entity_name}} {
        {{entity_name}}::from_persistence(
            test_id(),
            "Test".to_string(),
            chrono::Utc::now(),
            chrono::Utc::now(),
        )
    }

    #[tokio::test]
    async fn test_get_by_id_success() {
        let mut mock_repo = Mock{{entity_name}}Repository::new();
        mock_repo
            .expect_find_by_id()
            .with(eq(test_id()))
            .times(1)
            .returning(|_| Ok(Some(create_test_entity())));

        let service = {{entity_name}}Service::new(
            Arc::new(mock_repo),
            {% if with_events %}Arc::new(MockEventPublisher::new()),{% endif %}
            {% if with_caching %}Arc::new(MockCache::new()),{% endif %}
        );

        let result = service.get_by_id(test_id()).await;
        assert!(result.is_ok());
    }

    #[tokio::test]
    async fn test_get_by_id_not_found() {
        let mut mock_repo = Mock{{entity_name}}Repository::new();
        mock_repo
            .expect_find_by_id()
            .times(1)
            .returning(|_| Ok(None));

        let service = {{entity_name}}Service::new(
            Arc::new(mock_repo),
            {% if with_events %}Arc::new(MockEventPublisher::new()),{% endif %}
            {% if with_caching %}Arc::new(MockCache::new()),{% endif %}
        );

        let result = service.get_by_id(test_id()).await;
        assert!(matches!(result, Err(AppError::NotFound(_))));
    }

    #[tokio::test]
    async fn test_create_success() {
        let mut mock_repo = Mock{{entity_name}}Repository::new();
        mock_repo.expect_save().times(1).returning(|_| Ok(()));

        {% if with_events %}
        let mut mock_events = MockEventPublisher::new();
        mock_events.expect_publish().times(1).returning(|_| Ok(()));
        {% endif %}

        let service = {{entity_name}}Service::new(
            Arc::new(mock_repo),
            {% if with_events %}Arc::new(mock_events),{% endif %}
            {% if with_caching %}Arc::new(MockCache::new()),{% endif %}
        );

        let dto = Create{{entity_name}}Dto {
            name: "New Entity".to_string(),
        };

        let result = service.create(dto).await;
        assert!(result.is_ok());
    }
}
```

### 3. Generate DTOs

```rust
// src/application/{{entity_name | snake_case}}/dto.rs

use serde::{Deserialize, Serialize};
use validator::Validate;

#[derive(Debug, Clone, Deserialize, Validate)]
pub struct Create{{entity_name}}Dto {
    #[validate(length(min = 2, max = 200))]
    pub name: String,
    // ... other fields
}

#[derive(Debug, Clone, Deserialize, Validate)]
pub struct Update{{entity_name}}Dto {
    #[validate(length(min = 2, max = 200))]
    pub name: Option<String>,
    // ... other fields
}

#[derive(Debug, Clone, Deserialize, Default)]
pub struct {{entity_name}}ListQuery {
    pub page: Option<u32>,
    pub per_page: Option<u32>,
    pub search: Option<String>,
}
```

## Usage

```bash
# Generate basic service
f5 generate service User

# Generate with caching
f5 generate service Product --with-caching

# Generate with events
f5 generate service Order --with-events

# Generate with both
f5 generate service Customer --with-caching --with-events
```

## Output Files

```
src/application/{{entity_name | snake_case}}/
├── mod.rs
├── service.rs
└── dto.rs
```
