---
name: rust-axum-patterns
description: Axum framework patterns and best practices
applies_to: rust
---

# Axum Framework Patterns

## Overview

Axum is a modern, ergonomic web framework built on Tokio and Tower.
It provides excellent async support and composable middleware.

## Router Setup

```rust
// src/api/router.rs
use axum::{
    routing::{get, post, put, delete},
    Router,
};
use tower_http::{
    cors::{Any, CorsLayer},
    trace::TraceLayer,
    compression::CompressionLayer,
    timeout::TimeoutLayer,
};
use std::time::Duration;

use crate::{
    api::handlers::{health, user_handler, product_handler},
    middleware::auth::auth_middleware,
    startup::AppState,
};

pub fn create_router(state: AppState) -> Router {
    // Public routes
    let public_routes = Router::new()
        .route("/health", get(health::health_check))
        .route("/ready", get(health::readiness_check))
        .route("/auth/login", post(user_handler::login))
        .route("/auth/register", post(user_handler::register))
        .route("/auth/refresh", post(user_handler::refresh_token));

    // Protected routes
    let protected_routes = Router::new()
        .route("/users", get(user_handler::list))
        .route("/users/:id", get(user_handler::get_by_id))
        .route("/users/:id", put(user_handler::update))
        .route("/users/:id", delete(user_handler::delete))
        .route("/users/me", get(user_handler::me))
        .route("/products", get(product_handler::list))
        .route("/products", post(product_handler::create))
        .route("/products/:id", get(product_handler::get_by_id))
        .route("/products/:id", put(product_handler::update))
        .route("/products/:id", delete(product_handler::delete))
        .layer(axum::middleware::from_fn_with_state(
            state.clone(),
            auth_middleware,
        ));

    // Combine routes with middleware
    Router::new()
        .nest("/api/v1", public_routes.merge(protected_routes))
        .layer(CompressionLayer::new())
        .layer(TimeoutLayer::new(Duration::from_secs(30)))
        .layer(
            CorsLayer::new()
                .allow_origin(Any)
                .allow_methods(Any)
                .allow_headers(Any),
        )
        .layer(TraceLayer::new_for_http())
        .with_state(state)
}
```

## Handler Patterns

### Basic CRUD Handler

```rust
// src/api/handlers/user_handler.rs
use axum::{
    extract::{Path, Query, State},
    http::StatusCode,
    Json,
};
use uuid::Uuid;
use validator::Validate;

use crate::{
    api::extractors::CurrentUser,
    application::user::{CreateUserDto, UpdateUserDto, UserResponse, ListQuery},
    error::{AppError, Result},
    startup::AppState,
};

/// List users with pagination
#[axum::debug_handler]
pub async fn list(
    State(state): State<AppState>,
    Query(query): Query<ListQuery>,
) -> Result<Json<PaginatedResponse<UserResponse>>> {
    let (users, total) = state.user_service
        .list(&query)
        .await?;

    Ok(Json(PaginatedResponse {
        items: users,
        total,
        page: query.page,
        page_size: query.page_size,
    }))
}

/// Get user by ID
#[axum::debug_handler]
pub async fn get_by_id(
    State(state): State<AppState>,
    Path(id): Path<Uuid>,
) -> Result<Json<UserResponse>> {
    let user = state.user_service
        .get_by_id(id)
        .await?
        .ok_or_else(|| AppError::NotFound("User not found".into()))?;

    Ok(Json(user))
}

/// Create new user
#[axum::debug_handler]
pub async fn create(
    State(state): State<AppState>,
    Json(payload): Json<CreateUserDto>,
) -> Result<(StatusCode, Json<UserResponse>)> {
    // Validate input
    payload.validate()
        .map_err(|e| AppError::Validation(e.to_string()))?;

    let user = state.user_service.create(payload).await?;

    Ok((StatusCode::CREATED, Json(user)))
}

/// Update user
#[axum::debug_handler]
pub async fn update(
    State(state): State<AppState>,
    Path(id): Path<Uuid>,
    current_user: CurrentUser,
    Json(payload): Json<UpdateUserDto>,
) -> Result<Json<UserResponse>> {
    // Check ownership
    if current_user.id != id && !current_user.is_admin {
        return Err(AppError::Forbidden("Not authorized".into()));
    }

    // Validate input
    payload.validate()
        .map_err(|e| AppError::Validation(e.to_string()))?;

    let user = state.user_service
        .update(id, payload)
        .await?
        .ok_or_else(|| AppError::NotFound("User not found".into()))?;

    Ok(Json(user))
}

/// Delete user
#[axum::debug_handler]
pub async fn delete(
    State(state): State<AppState>,
    Path(id): Path<Uuid>,
    current_user: CurrentUser,
) -> Result<StatusCode> {
    // Check ownership
    if current_user.id != id && !current_user.is_admin {
        return Err(AppError::Forbidden("Not authorized".into()));
    }

    state.user_service.delete(id).await?;

    Ok(StatusCode::NO_CONTENT)
}
```

### Health Check Handlers

```rust
// src/api/handlers/health.rs
use axum::{
    extract::State,
    http::StatusCode,
    Json,
};
use serde::Serialize;

use crate::startup::AppState;

#[derive(Serialize)]
pub struct HealthResponse {
    status: String,
    version: String,
}

#[derive(Serialize)]
pub struct ReadinessResponse {
    status: String,
    database: String,
    cache: String,
}

pub async fn health_check() -> Json<HealthResponse> {
    Json(HealthResponse {
        status: "healthy".to_string(),
        version: env!("CARGO_PKG_VERSION").to_string(),
    })
}

pub async fn readiness_check(
    State(state): State<AppState>,
) -> Result<Json<ReadinessResponse>, StatusCode> {
    // Check database
    let db_status = sqlx::query("SELECT 1")
        .execute(&state.pool)
        .await
        .map(|_| "connected")
        .unwrap_or("disconnected");

    // Check cache (if applicable)
    let cache_status = "connected"; // Replace with actual check

    let all_healthy = db_status == "connected" && cache_status == "connected";

    let response = ReadinessResponse {
        status: if all_healthy { "ready" } else { "not_ready" }.to_string(),
        database: db_status.to_string(),
        cache: cache_status.to_string(),
    };

    if all_healthy {
        Ok(Json(response))
    } else {
        Err(StatusCode::SERVICE_UNAVAILABLE)
    }
}
```

## Custom Extractors

### Current User Extractor

```rust
// src/api/extractors.rs
use axum::{
    async_trait,
    extract::FromRequestParts,
    http::{request::Parts, StatusCode},
    RequestPartsExt,
};
use axum_extra::{
    headers::{authorization::Bearer, Authorization},
    TypedHeader,
};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

use crate::{error::AppError, startup::AppState};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Claims {
    pub sub: Uuid,
    pub email: String,
    pub is_admin: bool,
    pub exp: i64,
    pub iat: i64,
}

#[derive(Debug, Clone)]
pub struct CurrentUser {
    pub id: Uuid,
    pub email: String,
    pub is_admin: bool,
}

#[async_trait]
impl FromRequestParts<AppState> for CurrentUser {
    type Rejection = AppError;

    async fn from_request_parts(
        parts: &mut Parts,
        state: &AppState,
    ) -> Result<Self, Self::Rejection> {
        // Extract bearer token
        let TypedHeader(Authorization(bearer)) = parts
            .extract::<TypedHeader<Authorization<Bearer>>>()
            .await
            .map_err(|_| AppError::Unauthorized("Missing authorization header".into()))?;

        // Verify token
        let claims = jsonwebtoken::decode::<Claims>(
            bearer.token(),
            &jsonwebtoken::DecodingKey::from_secret(state.config.jwt.secret.as_bytes()),
            &jsonwebtoken::Validation::default(),
        )
        .map_err(|e| AppError::Unauthorized(format!("Invalid token: {}", e)))?
        .claims;

        // Check expiration
        let now = chrono::Utc::now().timestamp();
        if claims.exp < now {
            return Err(AppError::Unauthorized("Token expired".into()));
        }

        Ok(CurrentUser {
            id: claims.sub,
            email: claims.email,
            is_admin: claims.is_admin,
        })
    }
}

/// Optional authentication - returns None if no valid token
pub struct MaybeUser(pub Option<CurrentUser>);

#[async_trait]
impl FromRequestParts<AppState> for MaybeUser {
    type Rejection = AppError;

    async fn from_request_parts(
        parts: &mut Parts,
        state: &AppState,
    ) -> Result<Self, Self::Rejection> {
        match CurrentUser::from_request_parts(parts, state).await {
            Ok(user) => Ok(MaybeUser(Some(user))),
            Err(_) => Ok(MaybeUser(None)),
        }
    }
}
```

### Pagination Extractor

```rust
// src/api/extractors/pagination.rs
use axum::{
    async_trait,
    extract::{FromRequestParts, Query},
    http::request::Parts,
};
use serde::Deserialize;

#[derive(Debug, Deserialize)]
pub struct PaginationQuery {
    #[serde(default = "default_page")]
    pub page: i64,
    #[serde(default = "default_page_size")]
    pub page_size: i64,
}

fn default_page() -> i64 { 1 }
fn default_page_size() -> i64 { 20 }

#[derive(Debug)]
pub struct Pagination {
    pub offset: i64,
    pub limit: i64,
    pub page: i64,
    pub page_size: i64,
}

impl Pagination {
    const MAX_PAGE_SIZE: i64 = 100;
}

#[async_trait]
impl<S> FromRequestParts<S> for Pagination
where
    S: Send + Sync,
{
    type Rejection = std::convert::Infallible;

    async fn from_request_parts(
        parts: &mut Parts,
        state: &S,
    ) -> Result<Self, Self::Rejection> {
        let Query(query) = Query::<PaginationQuery>::from_request_parts(parts, state)
            .await
            .unwrap_or(Query(PaginationQuery {
                page: 1,
                page_size: 20,
            }));

        let page = query.page.max(1);
        let page_size = query.page_size.clamp(1, Pagination::MAX_PAGE_SIZE);
        let offset = (page - 1) * page_size;

        Ok(Pagination {
            offset,
            limit: page_size,
            page,
            page_size,
        })
    }
}
```

## Response Types

```rust
// src/api/response.rs
use serde::Serialize;

#[derive(Debug, Serialize)]
pub struct PaginatedResponse<T> {
    pub items: Vec<T>,
    pub total: i64,
    pub page: i64,
    pub page_size: i64,
    pub total_pages: i64,
}

impl<T> PaginatedResponse<T> {
    pub fn new(items: Vec<T>, total: i64, page: i64, page_size: i64) -> Self {
        let total_pages = (total as f64 / page_size as f64).ceil() as i64;
        Self {
            items,
            total,
            page,
            page_size,
            total_pages,
        }
    }
}

#[derive(Debug, Serialize)]
pub struct CreatedResponse<T> {
    pub data: T,
    pub message: String,
}

#[derive(Debug, Serialize)]
pub struct DeletedResponse {
    pub message: String,
}
```

## State Management

```rust
// src/startup.rs
use std::sync::Arc;
use axum::extract::FromRef;
use sqlx::PgPool;

use crate::{
    application::{user::UserService, product::ProductService},
    config::Config,
};

/// Application state shared across handlers
#[derive(Clone)]
pub struct AppState {
    pub config: Config,
    pub pool: PgPool,
    pub user_service: Arc<UserService>,
    pub product_service: Arc<ProductService>,
}

// Allow extracting individual parts of state
impl FromRef<AppState> for Config {
    fn from_ref(state: &AppState) -> Self {
        state.config.clone()
    }
}

impl FromRef<AppState> for PgPool {
    fn from_ref(state: &AppState) -> Self {
        state.pool.clone()
    }
}
```

## Nested Routers

```rust
// src/api/router.rs
use axum::Router;

use crate::startup::AppState;

pub fn create_router(state: AppState) -> Router {
    Router::new()
        .nest("/api/v1", api_v1_router(state.clone()))
        .nest("/admin", admin_router(state))
}

fn api_v1_router(state: AppState) -> Router<AppState> {
    Router::new()
        .nest("/users", user_router())
        .nest("/products", product_router())
        .nest("/orders", order_router())
        .with_state(state)
}

fn user_router() -> Router<AppState> {
    Router::new()
        .route("/", get(list_users).post(create_user))
        .route("/:id", get(get_user).put(update_user).delete(delete_user))
}
```

## WebSocket Support

```rust
// src/api/handlers/ws.rs
use axum::{
    extract::{
        ws::{Message, WebSocket, WebSocketUpgrade},
        State,
    },
    response::IntoResponse,
};
use futures::{sink::SinkExt, stream::StreamExt};

use crate::startup::AppState;

pub async fn ws_handler(
    ws: WebSocketUpgrade,
    State(state): State<AppState>,
) -> impl IntoResponse {
    ws.on_upgrade(|socket| handle_socket(socket, state))
}

async fn handle_socket(socket: WebSocket, state: AppState) {
    let (mut sender, mut receiver) = socket.split();

    // Spawn task to handle incoming messages
    let mut recv_task = tokio::spawn(async move {
        while let Some(Ok(msg)) = receiver.next().await {
            match msg {
                Message::Text(text) => {
                    tracing::info!("Received: {}", text);
                }
                Message::Close(_) => break,
                _ => {}
            }
        }
    });

    // Spawn task to send messages
    let mut send_task = tokio::spawn(async move {
        loop {
            if sender
                .send(Message::Text("ping".to_string()))
                .await
                .is_err()
            {
                break;
            }
            tokio::time::sleep(tokio::time::Duration::from_secs(30)).await;
        }
    });

    // Wait for either task to finish
    tokio::select! {
        _ = &mut recv_task => send_task.abort(),
        _ = &mut send_task => recv_task.abort(),
    }
}
```

## Best Practices

1. **Use `#[axum::debug_handler]`**: Helps with better error messages during development
2. **Extract common logic**: Use custom extractors for repeated patterns
3. **State composition**: Use `FromRef` to extract parts of state
4. **Layer ordering**: Apply middleware in correct order (innermost first)
5. **Error handling**: Return proper HTTP status codes
6. **Validation**: Validate input DTOs before processing
