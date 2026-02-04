---
name: rust-test
description: Test file template for unit and integration tests
applies_to: rust
variables:
  - name: module_name
    description: Module being tested (e.g., user, product)
  - name: test_type
    description: Type of test (unit, integration, e2e)
---

# Rust Test Template

## Unit Test Module

```rust
// src/domain/{{module_name}}/entity.rs

// ... entity implementation ...

#[cfg(test)]
mod tests {
    use super::*;
    use rust_decimal_macros::dec;

    // Test fixtures
    fn create_valid_{{module_name}}() -> {{module_name | pascal_case}} {
        {{module_name | pascal_case}}::new(
            "Test Name".to_string(),
            // ... other valid params
        ).expect("Failed to create test entity")
    }

    mod creation {
        use super::*;

        #[test]
        fn test_create_with_valid_params() {
            let result = {{module_name | pascal_case}}::new(
                "Valid Name".to_string(),
                // ... params
            );

            assert!(result.is_ok());
            let entity = result.unwrap();
            assert_eq!(entity.name(), "Valid Name");
        }

        #[test]
        fn test_create_with_empty_name_fails() {
            let result = {{module_name | pascal_case}}::new(
                "".to_string(),
                // ... params
            );

            assert!(result.is_err());
            let errors = result.unwrap_err();
            assert!(errors.iter().any(|e| matches!(e, ValidationError::MissingField(_))));
        }

        #[test]
        fn test_create_with_name_too_long_fails() {
            let long_name = "a".repeat(201);
            let result = {{module_name | pascal_case}}::new(
                long_name,
                // ... params
            );

            assert!(result.is_err());
        }
    }

    mod mutations {
        use super::*;

        #[test]
        fn test_update_name_success() {
            let mut entity = create_valid_{{module_name}}();
            let original_updated_at = entity.updated_at();

            std::thread::sleep(std::time::Duration::from_millis(10));

            let result = entity.set_name("New Name".to_string());

            assert!(result.is_ok());
            assert_eq!(entity.name(), "New Name");
            assert!(entity.updated_at() > original_updated_at);
        }

        #[test]
        fn test_update_with_invalid_value_fails() {
            let mut entity = create_valid_{{module_name}}();

            let result = entity.set_name("".to_string());

            assert!(result.is_err());
        }
    }

    mod business_rules {
        use super::*;

        #[test]
        fn test_business_rule_validation() {
            let entity = create_valid_{{module_name}}();

            // Test domain-specific business rules
            // assert!(entity.can_perform_action());
        }
    }
}
```

## Service Unit Test

```rust
// src/application/{{module_name}}/service.rs

#[cfg(test)]
mod tests {
    use super::*;
    use mockall::predicate::*;
    use std::sync::Arc;

    // Mock repository
    mock! {
        pub {{module_name | pascal_case}}Repository {}

        #[async_trait]
        impl {{module_name | pascal_case}}Repository for {{module_name | pascal_case}}Repository {
            async fn find_by_id(&self, id: Uuid) -> RepositoryResult<Option<{{module_name | pascal_case}}>>;
            async fn find_all(&self, offset: i64, limit: i64) -> RepositoryResult<Vec<{{module_name | pascal_case}}>>;
            async fn count(&self) -> RepositoryResult<i64>;
            async fn save(&self, entity: &{{module_name | pascal_case}}) -> RepositoryResult<()>;
            async fn update(&self, entity: &{{module_name | pascal_case}}) -> RepositoryResult<()>;
            async fn delete(&self, id: Uuid) -> RepositoryResult<()>;
            async fn exists(&self, id: Uuid) -> RepositoryResult<bool>;
        }
    }

    // Test helpers
    fn test_id() -> Uuid {
        Uuid::parse_str("550e8400-e29b-41d4-a716-446655440000").unwrap()
    }

    fn create_test_entity() -> {{module_name | pascal_case}} {
        {{module_name | pascal_case}}::from_persistence(
            test_id(),
            "Test Entity".to_string(),
            // ... other fields
            chrono::Utc::now(),
            chrono::Utc::now(),
        )
    }

    fn create_service(repo: Mock{{module_name | pascal_case}}Repository) -> {{module_name | pascal_case}}Service {
        {{module_name | pascal_case}}Service::new(Arc::new(repo))
    }

    mod get_by_id {
        use super::*;

        #[tokio::test]
        async fn test_returns_entity_when_found() {
            let mut mock_repo = Mock{{module_name | pascal_case}}Repository::new();
            mock_repo
                .expect_find_by_id()
                .with(eq(test_id()))
                .times(1)
                .returning(|_| Ok(Some(create_test_entity())));

            let service = create_service(mock_repo);

            let result = service.get_by_id(test_id()).await;

            assert!(result.is_ok());
            assert_eq!(*result.unwrap().id().as_uuid(), test_id());
        }

        #[tokio::test]
        async fn test_returns_not_found_when_missing() {
            let mut mock_repo = Mock{{module_name | pascal_case}}Repository::new();
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
            let mut mock_repo = Mock{{module_name | pascal_case}}Repository::new();
            mock_repo
                .expect_find_by_id()
                .times(1)
                .returning(|_| Err(RepositoryError::Database("Connection failed".to_string())));

            let service = create_service(mock_repo);

            let result = service.get_by_id(test_id()).await;

            assert!(result.is_err());
        }
    }

    mod create {
        use super::*;

        #[tokio::test]
        async fn test_creates_entity_successfully() {
            let mut mock_repo = Mock{{module_name | pascal_case}}Repository::new();
            mock_repo
                .expect_save()
                .times(1)
                .returning(|_| Ok(()));

            let service = create_service(mock_repo);
            let dto = Create{{module_name | pascal_case}}Dto {
                name: "New Entity".to_string(),
                // ... other fields
            };

            let result = service.create(dto).await;

            assert!(result.is_ok());
        }

        #[tokio::test]
        async fn test_returns_validation_error_for_invalid_dto() {
            let mock_repo = Mock{{module_name | pascal_case}}Repository::new();
            let service = create_service(mock_repo);
            let dto = Create{{module_name | pascal_case}}Dto {
                name: "".to_string(), // Invalid
                // ... other fields
            };

            let result = service.create(dto).await;

            assert!(matches!(result, Err(AppError::Validation(_))));
        }
    }

    mod delete {
        use super::*;

        #[tokio::test]
        async fn test_deletes_existing_entity() {
            let mut mock_repo = Mock{{module_name | pascal_case}}Repository::new();
            mock_repo
                .expect_find_by_id()
                .times(1)
                .returning(|_| Ok(Some(create_test_entity())));
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
            let mut mock_repo = Mock{{module_name | pascal_case}}Repository::new();
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

## Integration Test File

```rust
// tests/api/{{module_name}}_test.rs

use crate::common::{spawn_app, TestApp};
use serde_json::json;
use uuid::Uuid;

mod common;

#[tokio::test]
async fn test_list_{{module_name}}s() {
    let app = spawn_app().await;

    let response = app.get("/api/v1/{{module_name}}s").await;

    assert_eq!(response.status(), 200);

    let body: serde_json::Value = response.json().await.unwrap();
    assert!(body["items"].is_array());
    assert!(body["total"].is_number());
}

#[tokio::test]
async fn test_create_{{module_name}}() {
    let app = spawn_app().await;

    let payload = json!({
        "name": "Test {{module_name | pascal_case}}",
        // ... other fields
    });

    let response = app.post_auth("/api/v1/{{module_name}}s", &payload).await;

    assert_eq!(response.status(), 201);

    let body: serde_json::Value = response.json().await.unwrap();
    assert_eq!(body["name"], "Test {{module_name | pascal_case}}");
    assert!(body["id"].is_string());
}

#[tokio::test]
async fn test_create_{{module_name}}_validation_error() {
    let app = spawn_app().await;

    let payload = json!({
        "name": "", // Invalid: empty name
    });

    let response = app.post_auth("/api/v1/{{module_name}}s", &payload).await;

    assert_eq!(response.status(), 422);
}

#[tokio::test]
async fn test_create_{{module_name}}_unauthorized() {
    let app = spawn_app().await;

    let payload = json!({
        "name": "Test {{module_name | pascal_case}}",
    });

    let response = app.post("/api/v1/{{module_name}}s", &payload).await;

    assert_eq!(response.status(), 401);
}

#[tokio::test]
async fn test_get_{{module_name}}() {
    let app = spawn_app().await;
    let {{module_name}}_id = create_test_{{module_name}}(&app).await;

    let response = app.get(&format!("/api/v1/{{module_name}}s/{}", {{module_name}}_id)).await;

    assert_eq!(response.status(), 200);

    let body: serde_json::Value = response.json().await.unwrap();
    assert_eq!(body["id"], {{module_name}}_id.to_string());
}

#[tokio::test]
async fn test_get_{{module_name}}_not_found() {
    let app = spawn_app().await;
    let random_id = Uuid::new_v4();

    let response = app.get(&format!("/api/v1/{{module_name}}s/{}", random_id)).await;

    assert_eq!(response.status(), 404);
}

#[tokio::test]
async fn test_update_{{module_name}}() {
    let app = spawn_app().await;
    let {{module_name}}_id = create_test_{{module_name}}(&app).await;

    let payload = json!({
        "name": "Updated Name",
    });

    let response = app
        .put_auth(&format!("/api/v1/{{module_name}}s/{}", {{module_name}}_id), &payload)
        .await;

    assert_eq!(response.status(), 200);

    let body: serde_json::Value = response.json().await.unwrap();
    assert_eq!(body["name"], "Updated Name");
}

#[tokio::test]
async fn test_delete_{{module_name}}() {
    let app = spawn_app().await;
    let {{module_name}}_id = create_test_{{module_name}}(&app).await;

    let response = app
        .delete_auth(&format!("/api/v1/{{module_name}}s/{}", {{module_name}}_id))
        .await;

    assert_eq!(response.status(), 204);

    // Verify deletion
    let get_response = app.get(&format!("/api/v1/{{module_name}}s/{}", {{module_name}}_id)).await;
    assert_eq!(get_response.status(), 404);
}

// Helper functions
async fn create_test_{{module_name}}(app: &TestApp) -> Uuid {
    let payload = json!({
        "name": "Test {{module_name | pascal_case}}",
        // ... other required fields
    });

    let response = app.post_auth("/api/v1/{{module_name}}s", &payload).await;
    let body: serde_json::Value = response.json().await.unwrap();

    Uuid::parse_str(body["id"].as_str().unwrap()).unwrap()
}
```

## Property-Based Test

```rust
// tests/property/{{module_name}}_test.rs

use proptest::prelude::*;

proptest! {
    #[test]
    fn test_name_never_empty_after_validation(
        name in "[a-zA-Z0-9 ]{2,100}"
    ) {
        let result = {{module_name | pascal_case}}::new(name.clone());
        prop_assert!(result.is_ok());
        prop_assert!(!result.unwrap().name().is_empty());
    }

    #[test]
    fn test_invalid_names_rejected(
        name in prop::string::string_regex("^.{0,1}$|^.{201,}$").unwrap()
    ) {
        let result = {{module_name | pascal_case}}::new(name);
        prop_assert!(result.is_err());
    }

    #[test]
    fn test_id_always_unique(
        _ in 0..1000u32
    ) {
        let entity1 = create_test_{{module_name}}();
        let entity2 = create_test_{{module_name}}();
        prop_assert_ne!(entity1.id(), entity2.id());
    }
}
```

## Test Utilities

```rust
// tests/common/mod.rs

use once_cell::sync::Lazy;
use sqlx::PgPool;
use uuid::Uuid;

pub struct TestApp {
    pub address: String,
    pub pool: PgPool,
    pub client: reqwest::Client,
    pub auth_token: String,
}

impl TestApp {
    pub async fn get(&self, path: &str) -> reqwest::Response {
        self.client
            .get(format!("{}{}", self.address, path))
            .send()
            .await
            .expect("Failed to execute request")
    }

    pub async fn get_auth(&self, path: &str) -> reqwest::Response {
        self.client
            .get(format!("{}{}", self.address, path))
            .header("Authorization", format!("Bearer {}", self.auth_token))
            .send()
            .await
            .expect("Failed to execute request")
    }

    pub async fn post<T: serde::Serialize>(&self, path: &str, body: &T) -> reqwest::Response {
        self.client
            .post(format!("{}{}", self.address, path))
            .json(body)
            .send()
            .await
            .expect("Failed to execute request")
    }

    pub async fn post_auth<T: serde::Serialize>(&self, path: &str, body: &T) -> reqwest::Response {
        self.client
            .post(format!("{}{}", self.address, path))
            .header("Authorization", format!("Bearer {}", self.auth_token))
            .json(body)
            .send()
            .await
            .expect("Failed to execute request")
    }

    pub async fn put_auth<T: serde::Serialize>(&self, path: &str, body: &T) -> reqwest::Response {
        self.client
            .put(format!("{}{}", self.address, path))
            .header("Authorization", format!("Bearer {}", self.auth_token))
            .json(body)
            .send()
            .await
            .expect("Failed to execute request")
    }

    pub async fn delete_auth(&self, path: &str) -> reqwest::Response {
        self.client
            .delete(format!("{}{}", self.address, path))
            .header("Authorization", format!("Bearer {}", self.auth_token))
            .send()
            .await
            .expect("Failed to execute request")
    }
}

pub async fn spawn_app() -> TestApp {
    // Implementation from integration tests skill
    todo!()
}
```
