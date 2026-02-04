---
name: rust-test-generator
description: Generates comprehensive test suites for Rust code
applies_to: rust
inputs:
  - name: target
    description: Target to test (entity, service, handler, repository)
    required: true
  - name: target_name
    description: Name of the target (e.g., User, Product)
    required: true
  - name: test_types
    description: Types of tests to generate
    required: false
    default: [unit, integration]
  - name: with_property_tests
    description: Include property-based tests
    required: false
    default: false
  - name: with_fixtures
    description: Generate test fixtures
    required: false
    default: true
---

# Rust Test Generator Agent

## Purpose

Generate comprehensive test suites with:
- Unit tests with mocks
- Integration tests
- Property-based tests
- Test fixtures and helpers
- Test coverage optimization

## Generation Process

### 1. Analyze Test Requirements

```yaml
analysis:
  - Identify target type and structure
  - Determine testable behaviors
  - Check for dependencies to mock
  - Review edge cases and error conditions
```

### 2. Generate Unit Tests

```rust
// src/domain/{{target_name | snake_case}}/entity.rs

#[cfg(test)]
mod tests {
    use super::*;
    use proptest::prelude::*;

    // ============================================
    // Test Fixtures
    // ============================================

    fn valid_{{target_name | snake_case}}_params() -> {{target_name}}Params {
        {{target_name}}Params {
            name: "Valid Name".to_string(),
            // ... other valid parameters
        }
    }

    fn create_valid_{{target_name | snake_case}}() -> {{target_name}} {
        {{target_name}}::new(valid_{{target_name | snake_case}}_params())
            .expect("Failed to create test entity")
    }

    // ============================================
    // Creation Tests
    // ============================================

    mod creation {
        use super::*;

        #[test]
        fn test_create_with_valid_params_succeeds() {
            let params = valid_{{target_name | snake_case}}_params();

            let result = {{target_name}}::new(params);

            assert!(result.is_ok());
            let entity = result.unwrap();
            assert!(!entity.id().as_uuid().is_nil());
        }

        #[test]
        fn test_create_with_empty_name_fails() {
            let mut params = valid_{{target_name | snake_case}}_params();
            params.name = String::new();

            let result = {{target_name}}::new(params);

            assert!(result.is_err());
            let errors = result.unwrap_err();
            assert!(errors.iter().any(|e| {
                matches!(e, ValidationError::EmptyField(field) if field == "name")
            }));
        }

        #[test]
        fn test_create_with_name_too_long_fails() {
            let mut params = valid_{{target_name | snake_case}}_params();
            params.name = "a".repeat(201);

            let result = {{target_name}}::new(params);

            assert!(result.is_err());
        }

        #[test]
        fn test_id_is_unique_for_each_creation() {
            let entity1 = create_valid_{{target_name | snake_case}}();
            let entity2 = create_valid_{{target_name | snake_case}}();

            assert_ne!(entity1.id(), entity2.id());
        }

        #[test]
        fn test_timestamps_are_set_on_creation() {
            let before = chrono::Utc::now();
            let entity = create_valid_{{target_name | snake_case}}();
            let after = chrono::Utc::now();

            assert!(entity.created_at() >= before);
            assert!(entity.created_at() <= after);
            assert_eq!(entity.created_at(), entity.updated_at());
        }
    }

    // ============================================
    // Mutation Tests
    // ============================================

    mod mutations {
        use super::*;

        #[test]
        fn test_update_name_with_valid_value_succeeds() {
            let mut entity = create_valid_{{target_name | snake_case}}();
            let original_updated_at = entity.updated_at();
            std::thread::sleep(std::time::Duration::from_millis(10));

            let result = entity.set_name("New Name".to_string());

            assert!(result.is_ok());
            assert_eq!(entity.name(), "New Name");
            assert!(entity.updated_at() > original_updated_at);
        }

        #[test]
        fn test_update_name_with_invalid_value_fails() {
            let mut entity = create_valid_{{target_name | snake_case}}();
            let original_name = entity.name().to_string();
            let original_updated_at = entity.updated_at();

            let result = entity.set_name(String::new());

            assert!(result.is_err());
            assert_eq!(entity.name(), original_name);
            assert_eq!(entity.updated_at(), original_updated_at);
        }
    }

    // ============================================
    // Persistence Tests
    // ============================================

    mod persistence {
        use super::*;

        #[test]
        fn test_from_persistence_creates_valid_entity() {
            let id = Uuid::new_v4();
            let name = "Persisted Name".to_string();
            let created_at = chrono::Utc::now() - chrono::Duration::hours(1);
            let updated_at = chrono::Utc::now();

            let entity = {{target_name}}::from_persistence(
                id,
                name.clone(),
                created_at,
                updated_at,
            );

            assert_eq!(*entity.id().as_uuid(), id);
            assert_eq!(entity.name(), &name);
            assert_eq!(entity.created_at(), created_at);
            assert_eq!(entity.updated_at(), updated_at);
        }
    }

    // ============================================
    // Business Rule Tests
    // ============================================

    mod business_rules {
        use super::*;

        #[test]
        fn test_business_rule_validation() {
            let entity = create_valid_{{target_name | snake_case}}();

            // Add domain-specific business rule tests
            // assert!(entity.can_perform_action());
        }
    }

    {% if with_property_tests %}
    // ============================================
    // Property-Based Tests
    // ============================================

    mod property_tests {
        use super::*;
        use proptest::prelude::*;

        proptest! {
            #[test]
            fn test_valid_names_always_accepted(
                name in "[a-zA-Z0-9 ]{2,200}"
            ) {
                let mut params = valid_{{target_name | snake_case}}_params();
                params.name = name;

                let result = {{target_name}}::new(params);

                prop_assert!(result.is_ok());
            }

            #[test]
            fn test_empty_names_always_rejected(
                name in prop::string::string_regex("^$").unwrap()
            ) {
                let mut params = valid_{{target_name | snake_case}}_params();
                params.name = name;

                let result = {{target_name}}::new(params);

                prop_assert!(result.is_err());
            }

            #[test]
            fn test_names_over_200_chars_rejected(
                name in ".{201,500}"
            ) {
                let mut params = valid_{{target_name | snake_case}}_params();
                params.name = name;

                let result = {{target_name}}::new(params);

                prop_assert!(result.is_err());
            }

            #[test]
            fn test_id_never_nil(
                _ in 0..1000u32
            ) {
                let entity = create_valid_{{target_name | snake_case}}();

                prop_assert!(!entity.id().as_uuid().is_nil());
            }

            #[test]
            fn test_updated_at_never_before_created_at(
                _ in 0..100u32
            ) {
                let entity = create_valid_{{target_name | snake_case}}();

                prop_assert!(entity.updated_at() >= entity.created_at());
            }
        }
    }
    {% endif %}
}
```

### 3. Generate Service Unit Tests

```rust
// src/application/{{target_name | snake_case}}/service.rs

#[cfg(test)]
mod tests {
    use super::*;
    use mockall::predicate::*;
    use std::sync::Arc;

    // ============================================
    // Mock Setup
    // ============================================

    mock! {
        pub {{target_name}}Repository {}

        #[async_trait]
        impl {{target_name}}Repository for {{target_name}}Repository {
            async fn find_by_id(&self, id: Uuid) -> RepositoryResult<Option<{{target_name}}>>;
            async fn find_all(&self, offset: i64, limit: i64) -> RepositoryResult<Vec<{{target_name}}>>;
            async fn count(&self) -> RepositoryResult<i64>;
            async fn save(&self, entity: &{{target_name}}) -> RepositoryResult<()>;
            async fn update(&self, entity: &{{target_name}}) -> RepositoryResult<()>;
            async fn delete(&self, id: Uuid) -> RepositoryResult<()>;
            async fn exists(&self, id: Uuid) -> RepositoryResult<bool>;
        }
    }

    // ============================================
    // Test Helpers
    // ============================================

    fn test_id() -> Uuid {
        Uuid::parse_str("550e8400-e29b-41d4-a716-446655440000").unwrap()
    }

    fn create_test_{{target_name | snake_case}}() -> {{target_name}} {
        {{target_name}}::from_persistence(
            test_id(),
            "Test Entity".to_string(),
            chrono::Utc::now(),
            chrono::Utc::now(),
        )
    }

    fn create_service(repo: Mock{{target_name}}Repository) -> {{target_name}}Service {
        {{target_name}}Service::new(Arc::new(repo))
    }

    // ============================================
    // Get By ID Tests
    // ============================================

    mod get_by_id {
        use super::*;

        #[tokio::test]
        async fn test_returns_entity_when_found() {
            let mut mock_repo = Mock{{target_name}}Repository::new();
            mock_repo
                .expect_find_by_id()
                .with(eq(test_id()))
                .times(1)
                .returning(|_| Ok(Some(create_test_{{target_name | snake_case}}())));

            let service = create_service(mock_repo);

            let result = service.get_by_id(test_id()).await;

            assert!(result.is_ok());
            let entity = result.unwrap();
            assert_eq!(*entity.id().as_uuid(), test_id());
        }

        #[tokio::test]
        async fn test_returns_not_found_error_when_missing() {
            let mut mock_repo = Mock{{target_name}}Repository::new();
            mock_repo
                .expect_find_by_id()
                .with(eq(test_id()))
                .times(1)
                .returning(|_| Ok(None));

            let service = create_service(mock_repo);

            let result = service.get_by_id(test_id()).await;

            assert!(matches!(result, Err(AppError::NotFound(_))));
        }

        #[tokio::test]
        async fn test_propagates_repository_error() {
            let mut mock_repo = Mock{{target_name}}Repository::new();
            mock_repo
                .expect_find_by_id()
                .times(1)
                .returning(|_| Err(RepositoryError::Database("Connection failed".to_string())));

            let service = create_service(mock_repo);

            let result = service.get_by_id(test_id()).await;

            assert!(result.is_err());
        }
    }

    // ============================================
    // List Tests
    // ============================================

    mod list {
        use super::*;

        #[tokio::test]
        async fn test_returns_paginated_results() {
            let mut mock_repo = Mock{{target_name}}Repository::new();
            mock_repo
                .expect_find_all()
                .with(eq(0i64), eq(20i64))
                .times(1)
                .returning(|_, _| Ok(vec![create_test_{{target_name | snake_case}}()]));
            mock_repo
                .expect_count()
                .times(1)
                .returning(|| Ok(1));

            let service = create_service(mock_repo);
            let query = {{target_name}}ListQuery::default();

            let result = service.list(query).await;

            assert!(result.is_ok());
            let (items, total) = result.unwrap();
            assert_eq!(items.len(), 1);
            assert_eq!(total, 1);
        }

        #[tokio::test]
        async fn test_respects_pagination_parameters() {
            let mut mock_repo = Mock{{target_name}}Repository::new();
            mock_repo
                .expect_find_all()
                .with(eq(20i64), eq(10i64))
                .times(1)
                .returning(|_, _| Ok(vec![]));
            mock_repo
                .expect_count()
                .times(1)
                .returning(|| Ok(50));

            let service = create_service(mock_repo);
            let query = {{target_name}}ListQuery {
                page: Some(3),
                per_page: Some(10),
                ..Default::default()
            };

            let result = service.list(query).await;

            assert!(result.is_ok());
        }

        #[tokio::test]
        async fn test_limits_per_page_to_maximum() {
            let mut mock_repo = Mock{{target_name}}Repository::new();
            mock_repo
                .expect_find_all()
                .with(eq(0i64), eq(100i64)) // Max is 100
                .times(1)
                .returning(|_, _| Ok(vec![]));
            mock_repo
                .expect_count()
                .times(1)
                .returning(|| Ok(0));

            let service = create_service(mock_repo);
            let query = {{target_name}}ListQuery {
                page: Some(1),
                per_page: Some(500), // Exceeds max
                ..Default::default()
            };

            let _ = service.list(query).await;
        }
    }

    // ============================================
    // Create Tests
    // ============================================

    mod create {
        use super::*;

        #[tokio::test]
        async fn test_creates_entity_successfully() {
            let mut mock_repo = Mock{{target_name}}Repository::new();
            mock_repo
                .expect_save()
                .times(1)
                .returning(|_| Ok(()));

            let service = create_service(mock_repo);
            let dto = Create{{target_name}}Dto {
                name: "New Entity".to_string(),
            };

            let result = service.create(dto).await;

            assert!(result.is_ok());
            let entity = result.unwrap();
            assert_eq!(entity.name(), "New Entity");
        }

        #[tokio::test]
        async fn test_returns_validation_error_for_invalid_dto() {
            let mock_repo = Mock{{target_name}}Repository::new();
            let service = create_service(mock_repo);
            let dto = Create{{target_name}}Dto {
                name: "".to_string(), // Invalid
            };

            let result = service.create(dto).await;

            assert!(matches!(result, Err(AppError::Validation(_))));
        }

        #[tokio::test]
        async fn test_propagates_save_error() {
            let mut mock_repo = Mock{{target_name}}Repository::new();
            mock_repo
                .expect_save()
                .times(1)
                .returning(|_| Err(RepositoryError::Conflict("Already exists".to_string())));

            let service = create_service(mock_repo);
            let dto = Create{{target_name}}Dto {
                name: "Valid Name".to_string(),
            };

            let result = service.create(dto).await;

            assert!(result.is_err());
        }
    }

    // ============================================
    // Update Tests
    // ============================================

    mod update {
        use super::*;

        #[tokio::test]
        async fn test_updates_entity_successfully() {
            let mut mock_repo = Mock{{target_name}}Repository::new();
            mock_repo
                .expect_find_by_id()
                .times(1)
                .returning(|_| Ok(Some(create_test_{{target_name | snake_case}}())));
            mock_repo
                .expect_update()
                .times(1)
                .returning(|_| Ok(()));

            let service = create_service(mock_repo);
            let dto = Update{{target_name}}Dto {
                name: Some("Updated Name".to_string()),
            };

            let result = service.update(test_id(), dto).await;

            assert!(result.is_ok());
            assert_eq!(result.unwrap().name(), "Updated Name");
        }

        #[tokio::test]
        async fn test_returns_not_found_for_missing_entity() {
            let mut mock_repo = Mock{{target_name}}Repository::new();
            mock_repo
                .expect_find_by_id()
                .times(1)
                .returning(|_| Ok(None));

            let service = create_service(mock_repo);
            let dto = Update{{target_name}}Dto {
                name: Some("Updated Name".to_string()),
            };

            let result = service.update(test_id(), dto).await;

            assert!(matches!(result, Err(AppError::NotFound(_))));
        }
    }

    // ============================================
    // Delete Tests
    // ============================================

    mod delete {
        use super::*;

        #[tokio::test]
        async fn test_deletes_existing_entity() {
            let mut mock_repo = Mock{{target_name}}Repository::new();
            mock_repo
                .expect_find_by_id()
                .times(1)
                .returning(|_| Ok(Some(create_test_{{target_name | snake_case}}())));
            mock_repo
                .expect_delete()
                .times(1)
                .returning(|_| Ok(()));

            let service = create_service(mock_repo);

            let result = service.delete(test_id()).await;

            assert!(result.is_ok());
        }

        #[tokio::test]
        async fn test_returns_not_found_for_missing_entity() {
            let mut mock_repo = Mock{{target_name}}Repository::new();
            mock_repo
                .expect_find_by_id()
                .times(1)
                .returning(|_| Ok(None));

            let service = create_service(mock_repo);

            let result = service.delete(test_id()).await;

            assert!(matches!(result, Err(AppError::NotFound(_))));
        }
    }
}
```

### 4. Generate Integration Tests

```rust
// tests/api/{{target_name | snake_case}}_test.rs

use crate::common::{spawn_app, TestApp};
use serde_json::json;
use uuid::Uuid;

mod common;

// ============================================
// List Endpoint Tests
// ============================================

#[tokio::test]
async fn test_list_{{target_name | snake_case}}s_returns_empty_list() {
    let app = spawn_app().await;

    let response = app.get("/api/v1/{{target_name | snake_case}}s").await;

    assert_eq!(response.status(), 200);
    let body: serde_json::Value = response.json().await.unwrap();
    assert!(body["items"].as_array().unwrap().is_empty());
    assert_eq!(body["total"], 0);
}

#[tokio::test]
async fn test_list_{{target_name | snake_case}}s_returns_created_items() {
    let app = spawn_app().await;
    let _ = create_test_{{target_name | snake_case}}(&app).await;
    let _ = create_test_{{target_name | snake_case}}(&app).await;

    let response = app.get("/api/v1/{{target_name | snake_case}}s").await;

    assert_eq!(response.status(), 200);
    let body: serde_json::Value = response.json().await.unwrap();
    assert_eq!(body["items"].as_array().unwrap().len(), 2);
    assert_eq!(body["total"], 2);
}

#[tokio::test]
async fn test_list_{{target_name | snake_case}}s_respects_pagination() {
    let app = spawn_app().await;
    for _ in 0..15 {
        create_test_{{target_name | snake_case}}(&app).await;
    }

    let response = app.get("/api/v1/{{target_name | snake_case}}s?page=2&per_page=5").await;

    assert_eq!(response.status(), 200);
    let body: serde_json::Value = response.json().await.unwrap();
    assert_eq!(body["items"].as_array().unwrap().len(), 5);
    assert_eq!(body["total"], 15);
    assert_eq!(body["page"], 2);
}

// ============================================
// Create Endpoint Tests
// ============================================

#[tokio::test]
async fn test_create_{{target_name | snake_case}}_success() {
    let app = spawn_app().await;

    let payload = json!({
        "name": "Test {{target_name}}",
    });

    let response = app.post_auth("/api/v1/{{target_name | snake_case}}s", &payload).await;

    assert_eq!(response.status(), 201);
    let body: serde_json::Value = response.json().await.unwrap();
    assert_eq!(body["name"], "Test {{target_name}}");
    assert!(body["id"].is_string());
    assert!(body["created_at"].is_string());
}

#[tokio::test]
async fn test_create_{{target_name | snake_case}}_validation_error() {
    let app = spawn_app().await;

    let payload = json!({
        "name": "", // Invalid: empty name
    });

    let response = app.post_auth("/api/v1/{{target_name | snake_case}}s", &payload).await;

    assert_eq!(response.status(), 422);
    let body: serde_json::Value = response.json().await.unwrap();
    assert!(body["errors"].is_array());
}

#[tokio::test]
async fn test_create_{{target_name | snake_case}}_requires_authentication() {
    let app = spawn_app().await;

    let payload = json!({
        "name": "Test {{target_name}}",
    });

    let response = app.post("/api/v1/{{target_name | snake_case}}s", &payload).await;

    assert_eq!(response.status(), 401);
}

// ============================================
// Get Endpoint Tests
// ============================================

#[tokio::test]
async fn test_get_{{target_name | snake_case}}_success() {
    let app = spawn_app().await;
    let id = create_test_{{target_name | snake_case}}(&app).await;

    let response = app.get(&format!("/api/v1/{{target_name | snake_case}}s/{}", id)).await;

    assert_eq!(response.status(), 200);
    let body: serde_json::Value = response.json().await.unwrap();
    assert_eq!(body["id"], id.to_string());
}

#[tokio::test]
async fn test_get_{{target_name | snake_case}}_not_found() {
    let app = spawn_app().await;
    let random_id = Uuid::new_v4();

    let response = app.get(&format!("/api/v1/{{target_name | snake_case}}s/{}", random_id)).await;

    assert_eq!(response.status(), 404);
}

#[tokio::test]
async fn test_get_{{target_name | snake_case}}_invalid_id() {
    let app = spawn_app().await;

    let response = app.get("/api/v1/{{target_name | snake_case}}s/not-a-uuid").await;

    assert_eq!(response.status(), 400);
}

// ============================================
// Update Endpoint Tests
// ============================================

#[tokio::test]
async fn test_update_{{target_name | snake_case}}_success() {
    let app = spawn_app().await;
    let id = create_test_{{target_name | snake_case}}(&app).await;

    let payload = json!({
        "name": "Updated Name",
    });

    let response = app
        .put_auth(&format!("/api/v1/{{target_name | snake_case}}s/{}", id), &payload)
        .await;

    assert_eq!(response.status(), 200);
    let body: serde_json::Value = response.json().await.unwrap();
    assert_eq!(body["name"], "Updated Name");
}

#[tokio::test]
async fn test_update_{{target_name | snake_case}}_not_found() {
    let app = spawn_app().await;
    let random_id = Uuid::new_v4();

    let payload = json!({
        "name": "Updated Name",
    });

    let response = app
        .put_auth(&format!("/api/v1/{{target_name | snake_case}}s/{}", random_id), &payload)
        .await;

    assert_eq!(response.status(), 404);
}

#[tokio::test]
async fn test_update_{{target_name | snake_case}}_requires_authentication() {
    let app = spawn_app().await;
    let id = create_test_{{target_name | snake_case}}(&app).await;

    let payload = json!({
        "name": "Updated Name",
    });

    let response = app
        .put(&format!("/api/v1/{{target_name | snake_case}}s/{}", id), &payload)
        .await;

    assert_eq!(response.status(), 401);
}

// ============================================
// Delete Endpoint Tests
// ============================================

#[tokio::test]
async fn test_delete_{{target_name | snake_case}}_success() {
    let app = spawn_app().await;
    let id = create_test_{{target_name | snake_case}}(&app).await;

    let response = app
        .delete_auth(&format!("/api/v1/{{target_name | snake_case}}s/{}", id))
        .await;

    assert_eq!(response.status(), 204);

    // Verify deletion
    let get_response = app.get(&format!("/api/v1/{{target_name | snake_case}}s/{}", id)).await;
    assert_eq!(get_response.status(), 404);
}

#[tokio::test]
async fn test_delete_{{target_name | snake_case}}_not_found() {
    let app = spawn_app().await;
    let random_id = Uuid::new_v4();

    let response = app
        .delete_auth(&format!("/api/v1/{{target_name | snake_case}}s/{}", random_id))
        .await;

    assert_eq!(response.status(), 404);
}

#[tokio::test]
async fn test_delete_{{target_name | snake_case}}_requires_authentication() {
    let app = spawn_app().await;
    let id = create_test_{{target_name | snake_case}}(&app).await;

    let response = app
        .delete(&format!("/api/v1/{{target_name | snake_case}}s/{}", id))
        .await;

    assert_eq!(response.status(), 401);
}

#[tokio::test]
async fn test_delete_{{target_name | snake_case}}_idempotent() {
    let app = spawn_app().await;
    let id = create_test_{{target_name | snake_case}}(&app).await;

    // First delete
    let response1 = app
        .delete_auth(&format!("/api/v1/{{target_name | snake_case}}s/{}", id))
        .await;
    assert_eq!(response1.status(), 204);

    // Second delete should return 404
    let response2 = app
        .delete_auth(&format!("/api/v1/{{target_name | snake_case}}s/{}", id))
        .await;
    assert_eq!(response2.status(), 404);
}

// ============================================
// Helper Functions
// ============================================

async fn create_test_{{target_name | snake_case}}(app: &TestApp) -> Uuid {
    let payload = json!({
        "name": format!("Test {{target_name}} {}", Uuid::new_v4()),
    });

    let response = app.post_auth("/api/v1/{{target_name | snake_case}}s", &payload).await;
    let body: serde_json::Value = response.json().await.unwrap();

    Uuid::parse_str(body["id"].as_str().unwrap()).unwrap()
}
```

### 5. Generate Test Fixtures

```rust
// tests/fixtures/{{target_name | snake_case}}_fixtures.rs

use crate::common::TestApp;
use serde_json::json;
use uuid::Uuid;

/// Builder for creating test {{target_name}}s with customizable properties
pub struct {{target_name}}FixtureBuilder {
    name: String,
    // Add other fields as needed
}

impl Default for {{target_name}}FixtureBuilder {
    fn default() -> Self {
        Self {
            name: format!("Test {{target_name}} {}", Uuid::new_v4()),
        }
    }
}

impl {{target_name}}FixtureBuilder {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn with_name(mut self, name: impl Into<String>) -> Self {
        self.name = name.into();
        self
    }

    pub async fn create(self, app: &TestApp) -> {{target_name}}Fixture {
        let payload = json!({
            "name": self.name,
        });

        let response = app.post_auth("/api/v1/{{target_name | snake_case}}s", &payload).await;
        assert_eq!(response.status(), 201, "Failed to create fixture");

        let body: serde_json::Value = response.json().await.unwrap();

        {{target_name}}Fixture {
            id: Uuid::parse_str(body["id"].as_str().unwrap()).unwrap(),
            name: body["name"].as_str().unwrap().to_string(),
        }
    }
}

/// Represents a created {{target_name}} for use in tests
#[derive(Debug, Clone)]
pub struct {{target_name}}Fixture {
    pub id: Uuid,
    pub name: String,
}

impl {{target_name}}Fixture {
    pub fn builder() -> {{target_name}}FixtureBuilder {
        {{target_name}}FixtureBuilder::new()
    }

    pub async fn create(app: &TestApp) -> Self {
        Self::builder().create(app).await
    }

    pub async fn create_many(app: &TestApp, count: usize) -> Vec<Self> {
        let mut fixtures = Vec::with_capacity(count);
        for _ in 0..count {
            fixtures.push(Self::create(app).await);
        }
        fixtures
    }
}

// ============================================
// Assertion Helpers
// ============================================

pub mod assertions {
    use super::*;

    pub fn assert_{{target_name | snake_case}}_eq(actual: &serde_json::Value, expected: &{{target_name}}Fixture) {
        assert_eq!(
            actual["id"].as_str().unwrap(),
            expected.id.to_string(),
            "ID mismatch"
        );
        assert_eq!(
            actual["name"].as_str().unwrap(),
            expected.name,
            "Name mismatch"
        );
    }

    pub fn assert_{{target_name | snake_case}}_list_contains(
        list: &serde_json::Value,
        fixture: &{{target_name}}Fixture,
    ) {
        let items = list["items"].as_array().expect("Expected items array");
        let found = items.iter().any(|item| {
            item["id"].as_str().unwrap() == fixture.id.to_string()
        });
        assert!(found, "Expected list to contain {{target_name}} {}", fixture.id);
    }
}
```

## Usage

```bash
# Generate unit tests for entity
f5 generate tests User --target entity --test-types unit

# Generate integration tests for handler
f5 generate tests Product --target handler --test-types integration

# Generate comprehensive test suite
f5 generate tests Order --target service --test-types unit,integration --with-property-tests

# Generate with fixtures
f5 generate tests Customer --target handler --with-fixtures
```

## Output Files

```
# Entity unit tests
src/domain/{{target_name | snake_case}}/entity.rs (updated with #[cfg(test)])

# Service unit tests
src/application/{{target_name | snake_case}}/service.rs (updated with #[cfg(test)])

# Integration tests
tests/api/{{target_name | snake_case}}_test.rs

# Test fixtures
tests/fixtures/{{target_name | snake_case}}_fixtures.rs
tests/fixtures/mod.rs (updated)
```

## Test Categories Generated

| Category | Location | Purpose |
|----------|----------|---------|
| Unit (Entity) | `src/domain/*/entity.rs` | Domain logic validation |
| Unit (Service) | `src/application/*/service.rs` | Business logic with mocks |
| Integration | `tests/api/*_test.rs` | Full API endpoint testing |
| Property | Within unit tests | Invariant verification |
| Fixtures | `tests/fixtures/*` | Reusable test data builders |
