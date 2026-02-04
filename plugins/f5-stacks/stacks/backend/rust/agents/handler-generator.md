---
name: rust-handler-generator
description: Generates Axum/Actix-web handlers from specifications
applies_to: rust
inputs:
  - name: entity_name
    description: Entity name (e.g., User, Product)
    required: true
  - name: operations
    description: List of CRUD operations to generate
    required: false
    default: [list, get, create, update, delete]
  - name: framework
    description: Web framework (axum, actix-web)
    required: false
    default: axum
  - name: auth_required
    description: Whether authentication is required
    required: false
    default: true
---

# Rust Handler Generator Agent

## Purpose

Generate production-ready HTTP handlers for Rust web APIs with proper:
- Request/response handling
- Input validation
- Error handling
- Authentication/authorization
- Tracing and logging
- Tests

## Generation Process

### 1. Analyze Requirements

```yaml
analysis_steps:
  - Identify entity and operations needed
  - Determine authentication requirements
  - Check for custom validation rules
  - Identify related entities for nested routes
  - Review existing patterns in codebase
```

### 2. Generate Handler File

For each operation, generate appropriate handler:

#### List Handler
```rust
/// List {{entity_name}}s with pagination
#[tracing::instrument(name = "list_{{entity_name | snake_case}}s", skip(state))]
pub async fn list_{{entity_name | snake_case}}s(
    State(state): State<AppState>,
    {% if auth_required %}current_user: CurrentUser,{% endif %}
    Query(query): Query<{{entity_name}}ListQuery>,
) -> Result<Json<{{entity_name}}ListResponse>> {
    let (items, total) = state
        .{{entity_name | snake_case}}_service
        .list(query)
        .await?;

    Ok(Json({{entity_name}}ListResponse::new(items, total, query.page, query.per_page)))
}
```

#### Get Handler
```rust
/// Get {{entity_name}} by ID
#[tracing::instrument(name = "get_{{entity_name | snake_case}}", skip(state))]
pub async fn get_{{entity_name | snake_case}}(
    State(state): State<AppState>,
    {% if auth_required %}current_user: CurrentUser,{% endif %}
    Path(id): Path<Uuid>,
) -> Result<Json<{{entity_name}}Response>> {
    let entity = state
        .{{entity_name | snake_case}}_service
        .get_by_id(id)
        .await?;

    Ok(Json({{entity_name}}Response::from(entity)))
}
```

#### Create Handler
```rust
/// Create new {{entity_name}}
#[tracing::instrument(name = "create_{{entity_name | snake_case}}", skip(state, payload))]
pub async fn create_{{entity_name | snake_case}}(
    State(state): State<AppState>,
    current_user: CurrentUser,
    Json(payload): Json<Create{{entity_name}}Dto>,
) -> Result<(StatusCode, Json<{{entity_name}}Response>)> {
    payload.validate()?;

    let entity = state
        .{{entity_name | snake_case}}_service
        .create(payload, current_user.id)
        .await?;

    Ok((StatusCode::CREATED, Json({{entity_name}}Response::from(entity))))
}
```

#### Update Handler
```rust
/// Update existing {{entity_name}}
#[tracing::instrument(name = "update_{{entity_name | snake_case}}", skip(state, payload))]
pub async fn update_{{entity_name | snake_case}}(
    State(state): State<AppState>,
    current_user: CurrentUser,
    Path(id): Path<Uuid>,
    Json(payload): Json<Update{{entity_name}}Dto>,
) -> Result<Json<{{entity_name}}Response>> {
    payload.validate()?;

    let entity = state
        .{{entity_name | snake_case}}_service
        .update(id, payload, current_user.id)
        .await?;

    Ok(Json({{entity_name}}Response::from(entity)))
}
```

#### Delete Handler
```rust
/// Delete {{entity_name}}
#[tracing::instrument(name = "delete_{{entity_name | snake_case}}", skip(state))]
pub async fn delete_{{entity_name | snake_case}}(
    State(state): State<AppState>,
    current_user: CurrentUser,
    Path(id): Path<Uuid>,
) -> Result<StatusCode> {
    state
        .{{entity_name | snake_case}}_service
        .delete(id, current_user.id)
        .await?;

    Ok(StatusCode::NO_CONTENT)
}
```

### 3. Generate Router Configuration

```rust
use axum::{
    routing::{get, post, put, delete},
    Router,
};

pub fn {{entity_name | snake_case}}_routes() -> Router<AppState> {
    Router::new()
        .route(
            "/{{entity_name | snake_case}}s",
            get(list_{{entity_name | snake_case}}s)
                .post(create_{{entity_name | snake_case}}),
        )
        .route(
            "/{{entity_name | snake_case}}s/:id",
            get(get_{{entity_name | snake_case}})
                .put(update_{{entity_name | snake_case}})
                .delete(delete_{{entity_name | snake_case}}),
        )
}
```

### 4. Generate Tests

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use axum::{body::Body, http::{Request, StatusCode}};
    use tower::ServiceExt;

    #[tokio::test]
    async fn test_list_{{entity_name | snake_case}}s() {
        let app = spawn_test_app().await;

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/api/v1/{{entity_name | snake_case}}s")
                    .header("Authorization", format!("Bearer {}", test_token()))
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::OK);
    }

    #[tokio::test]
    async fn test_create_{{entity_name | snake_case}}_success() {
        let app = spawn_test_app().await;

        let response = app
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/api/v1/{{entity_name | snake_case}}s")
                    .header("Content-Type", "application/json")
                    .header("Authorization", format!("Bearer {}", test_token()))
                    .body(Body::from(r#"{"name": "Test"}"#))
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::CREATED);
    }
}
```

## Usage

```bash
# Generate handlers for Product entity
f5 generate handler Product --framework axum --auth-required

# Generate with specific operations
f5 generate handler Order --operations list,get,create --framework axum

# Generate without authentication
f5 generate handler PublicContent --auth-required false
```

## Output Files

```
src/api/handlers/
├── mod.rs (updated)
└── {{entity_name | snake_case}}_handler.rs

src/api/routes/
├── mod.rs (updated)
└── {{entity_name | snake_case}}_routes.rs

tests/api/
└── {{entity_name | snake_case}}_test.rs
```

## Customization

The generator supports customization through:
- Custom extractors for specific requirements
- Additional middleware per route
- Custom response types
- Nested routes for related entities
