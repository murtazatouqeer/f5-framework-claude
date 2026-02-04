---
name: rust-handler
description: Axum/Actix-web handler template
applies_to: rust
variables:
  - name: handler_name
    description: Name of the handler (e.g., get_user, create_product)
  - name: entity_name
    description: Entity name (e.g., User, Product)
  - name: http_method
    description: HTTP method (get, post, put, patch, delete)
  - name: path
    description: Route path (e.g., /users, /users/:id)
---

# Rust Handler Template

## Axum Handler

```rust
// src/api/handlers/{{entity_name | snake_case}}_handler.rs

use axum::{
    extract::{Path, Query, State},
    http::StatusCode,
    response::IntoResponse,
    Json,
};
use uuid::Uuid;

use crate::{
    application::{{entity_name | snake_case}}::{
        Create{{entity_name}}Dto,
        Update{{entity_name}}Dto,
        {{entity_name}}Response,
        {{entity_name}}ListQuery,
    },
    error::{AppError, Result},
    extractors::CurrentUser,
    startup::AppState,
};

/// {{handler_name | title_case}}
///
/// {{http_method | upper}} {{path}}
#[tracing::instrument(
    name = "{{handler_name}}",
    skip(state),
    fields(
        request_id = %Uuid::new_v4(),
    )
)]
pub async fn {{handler_name}}(
    State(state): State<AppState>,
    // Include if authentication required:
    // current_user: CurrentUser,
    {% if http_method == "get" and path contains ":id" %}
    Path(id): Path<Uuid>,
    {% endif %}
    {% if http_method == "get" and path not contains ":id" %}
    Query(query): Query<{{entity_name}}ListQuery>,
    {% endif %}
    {% if http_method in ["post", "put", "patch"] %}
    Json(payload): Json<{% if http_method == "post" %}Create{% else %}Update{% endif %}{{entity_name}}Dto>,
    {% endif %}
) -> Result<impl IntoResponse> {
    {% if http_method == "get" and path contains ":id" %}
    // Get single resource
    let {{entity_name | snake_case}} = state
        .{{entity_name | snake_case}}_service
        .get_by_id(id)
        .await?;

    Ok(Json({{entity_name}}Response::from({{entity_name | snake_case}})))
    {% endif %}

    {% if http_method == "get" and path not contains ":id" %}
    // List resources with pagination
    let (items, total) = state
        .{{entity_name | snake_case}}_service
        .list(query)
        .await?;

    Ok(Json({{entity_name}}ListResponse {
        items: items.into_iter().map({{entity_name}}Response::from).collect(),
        total,
        page: query.page.unwrap_or(1),
        per_page: query.per_page.unwrap_or(20),
    }))
    {% endif %}

    {% if http_method == "post" %}
    // Create resource
    payload.validate()?;

    let {{entity_name | snake_case}} = state
        .{{entity_name | snake_case}}_service
        .create(payload)
        .await?;

    Ok((
        StatusCode::CREATED,
        Json({{entity_name}}Response::from({{entity_name | snake_case}})),
    ))
    {% endif %}

    {% if http_method == "put" or http_method == "patch" %}
    // Update resource
    payload.validate()?;

    let {{entity_name | snake_case}} = state
        .{{entity_name | snake_case}}_service
        .update(id, payload)
        .await?;

    Ok(Json({{entity_name}}Response::from({{entity_name | snake_case}})))
    {% endif %}

    {% if http_method == "delete" %}
    // Delete resource
    state
        .{{entity_name | snake_case}}_service
        .delete(id)
        .await?;

    Ok(StatusCode::NO_CONTENT)
    {% endif %}
}

#[cfg(test)]
mod tests {
    use super::*;
    use axum::{
        body::Body,
        http::{Request, StatusCode},
    };
    use tower::ServiceExt;

    #[tokio::test]
    async fn test_{{handler_name}}_success() {
        let app = spawn_test_app().await;

        {% if http_method == "get" %}
        let response = app
            .oneshot(
                Request::builder()
                    .uri("{{path}}")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::OK);
        {% endif %}

        {% if http_method == "post" %}
        let payload = serde_json::json!({
            // Add required fields
        });

        let response = app
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("{{path}}")
                    .header("Content-Type", "application/json")
                    .body(Body::from(serde_json::to_string(&payload).unwrap()))
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::CREATED);
        {% endif %}
    }
}
```

## Actix-web Handler

```rust
// src/api/handlers/{{entity_name | snake_case}}_handler.rs

use actix_web::{web, HttpResponse, Result};
use uuid::Uuid;

use crate::{
    application::{{entity_name | snake_case}}::{
        Create{{entity_name}}Dto,
        Update{{entity_name}}Dto,
        {{entity_name}}Response,
        {{entity_name}}ListQuery,
    },
    error::AppError,
    extractors::CurrentUser,
    startup::AppState,
};

/// {{handler_name | title_case}}
///
/// {{http_method | upper}} {{path}}
#[tracing::instrument(
    name = "{{handler_name}}",
    skip(state),
)]
pub async fn {{handler_name}}(
    state: web::Data<AppState>,
    // Include if authentication required:
    // current_user: CurrentUser,
    {% if http_method == "get" and path contains ":id" %}
    path: web::Path<Uuid>,
    {% endif %}
    {% if http_method == "get" and path not contains ":id" %}
    query: web::Query<{{entity_name}}ListQuery>,
    {% endif %}
    {% if http_method in ["post", "put", "patch"] %}
    payload: web::Json<{% if http_method == "post" %}Create{% else %}Update{% endif %}{{entity_name}}Dto>,
    {% endif %}
) -> Result<HttpResponse, AppError> {
    {% if http_method == "get" and path contains ":id" %}
    let id = path.into_inner();
    let {{entity_name | snake_case}} = state
        .{{entity_name | snake_case}}_service
        .get_by_id(id)
        .await?;

    Ok(HttpResponse::Ok().json({{entity_name}}Response::from({{entity_name | snake_case}})))
    {% endif %}

    {% if http_method == "get" and path not contains ":id" %}
    let query = query.into_inner();
    let (items, total) = state
        .{{entity_name | snake_case}}_service
        .list(query)
        .await?;

    Ok(HttpResponse::Ok().json({{entity_name}}ListResponse {
        items: items.into_iter().map({{entity_name}}Response::from).collect(),
        total,
    }))
    {% endif %}

    {% if http_method == "post" %}
    let payload = payload.into_inner();
    payload.validate()?;

    let {{entity_name | snake_case}} = state
        .{{entity_name | snake_case}}_service
        .create(payload)
        .await?;

    Ok(HttpResponse::Created().json({{entity_name}}Response::from({{entity_name | snake_case}})))
    {% endif %}

    {% if http_method == "put" or http_method == "patch" %}
    let id = path.into_inner();
    let payload = payload.into_inner();
    payload.validate()?;

    let {{entity_name | snake_case}} = state
        .{{entity_name | snake_case}}_service
        .update(id, payload)
        .await?;

    Ok(HttpResponse::Ok().json({{entity_name}}Response::from({{entity_name | snake_case}})))
    {% endif %}

    {% if http_method == "delete" %}
    let id = path.into_inner();
    state
        .{{entity_name | snake_case}}_service
        .delete(id)
        .await?;

    Ok(HttpResponse::NoContent().finish())
    {% endif %}
}
```

## Router Configuration

```rust
// Axum Router
use axum::{routing::{get, post, put, delete}, Router};

pub fn {{entity_name | snake_case}}_routes() -> Router<AppState> {
    Router::new()
        .route("/{{entity_name | snake_case}}s", get(list_{{entity_name | snake_case}}s).post(create_{{entity_name | snake_case}}))
        .route(
            "/{{entity_name | snake_case}}s/:id",
            get(get_{{entity_name | snake_case}})
                .put(update_{{entity_name | snake_case}})
                .delete(delete_{{entity_name | snake_case}}),
        )
}

// Actix-web Config
pub fn configure_{{entity_name | snake_case}}_routes(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/{{entity_name | snake_case}}s")
            .route("", web::get().to(list_{{entity_name | snake_case}}s))
            .route("", web::post().to(create_{{entity_name | snake_case}}))
            .route("/{id}", web::get().to(get_{{entity_name | snake_case}}))
            .route("/{id}", web::put().to(update_{{entity_name | snake_case}}))
            .route("/{id}", web::delete().to(delete_{{entity_name | snake_case}})),
    );
}
```
