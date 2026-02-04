---
name: rust-actix-patterns
description: Actix-web framework patterns and best practices
applies_to: rust
---

# Actix-web Framework Patterns

## Overview

Actix-web is a powerful, actor-based web framework for Rust.
It provides excellent performance and a rich ecosystem.

## Application Setup

```rust
// src/main.rs
use actix_web::{web, App, HttpServer, middleware};
use sqlx::postgres::PgPoolOptions;
use std::sync::Arc;

use myapp::{
    api::{health, user_handler, product_handler},
    config::Config,
    middleware::auth::AuthMiddleware,
    startup::AppState,
};

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    // Initialize logging
    env_logger::init_from_env(env_logger::Env::default().default_filter_or("info"));

    // Load configuration
    let config = Config::load().expect("Failed to load config");

    // Database pool
    let pool = PgPoolOptions::new()
        .max_connections(config.database.max_connections)
        .connect(&config.database.url)
        .await
        .expect("Failed to create pool");

    // Run migrations
    sqlx::migrate!("./migrations")
        .run(&pool)
        .await
        .expect("Failed to run migrations");

    // Application state
    let state = web::Data::new(AppState::new(config.clone(), pool));

    log::info!("Starting server at http://{}:{}", config.server.host, config.server.port);

    HttpServer::new(move || {
        App::new()
            .app_data(state.clone())
            // Middleware
            .wrap(middleware::Logger::default())
            .wrap(middleware::Compress::default())
            .wrap(
                middleware::DefaultHeaders::new()
                    .add(("X-Content-Type-Options", "nosniff"))
                    .add(("X-Frame-Options", "DENY")),
            )
            // Routes
            .configure(configure_routes)
    })
    .bind((config.server.host.as_str(), config.server.port))?
    .run()
    .await
}

fn configure_routes(cfg: &mut web::ServiceConfig) {
    cfg
        // Health endpoints
        .service(
            web::scope("/health")
                .route("", web::get().to(health::health_check))
                .route("/ready", web::get().to(health::readiness)),
        )
        // API v1
        .service(
            web::scope("/api/v1")
                // Public routes
                .service(
                    web::scope("/auth")
                        .route("/login", web::post().to(user_handler::login))
                        .route("/register", web::post().to(user_handler::register))
                        .route("/refresh", web::post().to(user_handler::refresh_token)),
                )
                // Protected routes
                .service(
                    web::scope("")
                        .wrap(AuthMiddleware)
                        .service(
                            web::scope("/users")
                                .route("", web::get().to(user_handler::list))
                                .route("", web::post().to(user_handler::create))
                                .route("/me", web::get().to(user_handler::me))
                                .route("/{id}", web::get().to(user_handler::get_by_id))
                                .route("/{id}", web::put().to(user_handler::update))
                                .route("/{id}", web::delete().to(user_handler::delete)),
                        )
                        .service(
                            web::scope("/products")
                                .route("", web::get().to(product_handler::list))
                                .route("", web::post().to(product_handler::create))
                                .route("/{id}", web::get().to(product_handler::get_by_id))
                                .route("/{id}", web::put().to(product_handler::update))
                                .route("/{id}", web::delete().to(product_handler::delete)),
                        ),
                ),
        );
}
```

## Handler Patterns

```rust
// src/api/handlers/user_handler.rs
use actix_web::{web, HttpResponse, Result};
use uuid::Uuid;
use validator::Validate;

use crate::{
    api::extractors::CurrentUser,
    application::user::{CreateUserDto, UpdateUserDto, UserService},
    error::AppError,
    startup::AppState,
};

/// List users with pagination
pub async fn list(
    state: web::Data<AppState>,
    query: web::Query<ListQuery>,
) -> Result<HttpResponse, AppError> {
    let (users, total) = state.user_service
        .list(&query.into_inner())
        .await?;

    Ok(HttpResponse::Ok().json(PaginatedResponse {
        items: users,
        total,
        page: query.page,
        page_size: query.page_size,
    }))
}

/// Get user by ID
pub async fn get_by_id(
    state: web::Data<AppState>,
    path: web::Path<Uuid>,
) -> Result<HttpResponse, AppError> {
    let id = path.into_inner();

    let user = state.user_service
        .get_by_id(id)
        .await?
        .ok_or_else(|| AppError::NotFound("User not found".into()))?;

    Ok(HttpResponse::Ok().json(user))
}

/// Create new user
pub async fn create(
    state: web::Data<AppState>,
    payload: web::Json<CreateUserDto>,
) -> Result<HttpResponse, AppError> {
    let dto = payload.into_inner();

    // Validate
    dto.validate()
        .map_err(|e| AppError::Validation(e.to_string()))?;

    let user = state.user_service.create(dto).await?;

    Ok(HttpResponse::Created().json(user))
}

/// Update user
pub async fn update(
    state: web::Data<AppState>,
    path: web::Path<Uuid>,
    current_user: CurrentUser,
    payload: web::Json<UpdateUserDto>,
) -> Result<HttpResponse, AppError> {
    let id = path.into_inner();
    let dto = payload.into_inner();

    // Authorization check
    if current_user.id != id && !current_user.is_admin {
        return Err(AppError::Forbidden("Not authorized".into()));
    }

    // Validate
    dto.validate()
        .map_err(|e| AppError::Validation(e.to_string()))?;

    let user = state.user_service
        .update(id, dto)
        .await?
        .ok_or_else(|| AppError::NotFound("User not found".into()))?;

    Ok(HttpResponse::Ok().json(user))
}

/// Delete user
pub async fn delete(
    state: web::Data<AppState>,
    path: web::Path<Uuid>,
    current_user: CurrentUser,
) -> Result<HttpResponse, AppError> {
    let id = path.into_inner();

    // Authorization check
    if current_user.id != id && !current_user.is_admin {
        return Err(AppError::Forbidden("Not authorized".into()));
    }

    state.user_service.delete(id).await?;

    Ok(HttpResponse::NoContent().finish())
}

/// Get current user
pub async fn me(current_user: CurrentUser) -> Result<HttpResponse, AppError> {
    Ok(HttpResponse::Ok().json(current_user))
}
```

## Custom Extractors

```rust
// src/api/extractors.rs
use actix_web::{dev::Payload, web, FromRequest, HttpRequest};
use futures::future::{ok, Ready};
use std::future::Future;
use std::pin::Pin;

use crate::{error::AppError, startup::AppState};

#[derive(Debug, Clone)]
pub struct CurrentUser {
    pub id: uuid::Uuid,
    pub email: String,
    pub is_admin: bool,
}

impl FromRequest for CurrentUser {
    type Error = AppError;
    type Future = Pin<Box<dyn Future<Output = Result<Self, Self::Error>>>>;

    fn from_request(req: &HttpRequest, _payload: &mut Payload) -> Self::Future {
        let req = req.clone();

        Box::pin(async move {
            // Get state
            let state = req.app_data::<web::Data<AppState>>()
                .ok_or_else(|| AppError::Internal(anyhow::anyhow!("State not found")))?;

            // Get authorization header
            let auth_header = req.headers()
                .get("Authorization")
                .and_then(|h| h.to_str().ok())
                .ok_or_else(|| AppError::Unauthorized("Missing authorization header".into()))?;

            // Extract bearer token
            let token = auth_header
                .strip_prefix("Bearer ")
                .ok_or_else(|| AppError::Unauthorized("Invalid authorization format".into()))?;

            // Verify token
            let claims = jsonwebtoken::decode::<Claims>(
                token,
                &jsonwebtoken::DecodingKey::from_secret(state.config.jwt.secret.as_bytes()),
                &jsonwebtoken::Validation::default(),
            )
            .map_err(|e| AppError::Unauthorized(format!("Invalid token: {}", e)))?
            .claims;

            Ok(CurrentUser {
                id: claims.sub,
                email: claims.email,
                is_admin: claims.is_admin,
            })
        })
    }
}

/// Optional user extractor
pub struct MaybeUser(pub Option<CurrentUser>);

impl FromRequest for MaybeUser {
    type Error = AppError;
    type Future = Pin<Box<dyn Future<Output = Result<Self, Self::Error>>>>;

    fn from_request(req: &HttpRequest, payload: &mut Payload) -> Self::Future {
        let user_fut = CurrentUser::from_request(req, payload);

        Box::pin(async move {
            match user_fut.await {
                Ok(user) => Ok(MaybeUser(Some(user))),
                Err(_) => Ok(MaybeUser(None)),
            }
        })
    }
}
```

## Middleware

```rust
// src/middleware/auth.rs
use actix_web::{
    dev::{forward_ready, Service, ServiceRequest, ServiceResponse, Transform},
    Error, HttpMessage,
};
use futures::future::{ok, LocalBoxFuture, Ready};
use std::rc::Rc;

use crate::error::AppError;

pub struct AuthMiddleware;

impl<S, B> Transform<S, ServiceRequest> for AuthMiddleware
where
    S: Service<ServiceRequest, Response = ServiceResponse<B>, Error = Error> + 'static,
    S::Future: 'static,
    B: 'static,
{
    type Response = ServiceResponse<B>;
    type Error = Error;
    type Transform = AuthMiddlewareService<S>;
    type InitError = ();
    type Future = Ready<Result<Self::Transform, Self::InitError>>;

    fn new_transform(&self, service: S) -> Self::Future {
        ok(AuthMiddlewareService {
            service: Rc::new(service),
        })
    }
}

pub struct AuthMiddlewareService<S> {
    service: Rc<S>,
}

impl<S, B> Service<ServiceRequest> for AuthMiddlewareService<S>
where
    S: Service<ServiceRequest, Response = ServiceResponse<B>, Error = Error> + 'static,
    S::Future: 'static,
    B: 'static,
{
    type Response = ServiceResponse<B>;
    type Error = Error;
    type Future = LocalBoxFuture<'static, Result<Self::Response, Self::Error>>;

    forward_ready!(service);

    fn call(&self, req: ServiceRequest) -> Self::Future {
        let service = Rc::clone(&self.service);

        Box::pin(async move {
            // Extract and validate token
            let auth_header = req.headers()
                .get("Authorization")
                .and_then(|h| h.to_str().ok());

            match auth_header {
                Some(header) if header.starts_with("Bearer ") => {
                    // Token exists, let the handler validate it
                    service.call(req).await
                }
                _ => {
                    Err(AppError::Unauthorized("Missing or invalid authorization".into()).into())
                }
            }
        })
    }
}
```

## Error Handling

```rust
// src/error.rs
use actix_web::{http::StatusCode, HttpResponse, ResponseError};
use serde::Serialize;
use std::fmt;

#[derive(Debug)]
pub enum AppError {
    NotFound(String),
    BadRequest(String),
    Unauthorized(String),
    Forbidden(String),
    Conflict(String),
    Validation(String),
    Internal(anyhow::Error),
}

#[derive(Serialize)]
struct ErrorResponse {
    error: ErrorBody,
}

#[derive(Serialize)]
struct ErrorBody {
    code: u16,
    message: String,
}

impl fmt::Display for AppError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            AppError::NotFound(msg) => write!(f, "Not found: {}", msg),
            AppError::BadRequest(msg) => write!(f, "Bad request: {}", msg),
            AppError::Unauthorized(msg) => write!(f, "Unauthorized: {}", msg),
            AppError::Forbidden(msg) => write!(f, "Forbidden: {}", msg),
            AppError::Conflict(msg) => write!(f, "Conflict: {}", msg),
            AppError::Validation(msg) => write!(f, "Validation error: {}", msg),
            AppError::Internal(e) => write!(f, "Internal error: {}", e),
        }
    }
}

impl ResponseError for AppError {
    fn status_code(&self) -> StatusCode {
        match self {
            AppError::NotFound(_) => StatusCode::NOT_FOUND,
            AppError::BadRequest(_) => StatusCode::BAD_REQUEST,
            AppError::Unauthorized(_) => StatusCode::UNAUTHORIZED,
            AppError::Forbidden(_) => StatusCode::FORBIDDEN,
            AppError::Conflict(_) => StatusCode::CONFLICT,
            AppError::Validation(_) => StatusCode::UNPROCESSABLE_ENTITY,
            AppError::Internal(_) => StatusCode::INTERNAL_SERVER_ERROR,
        }
    }

    fn error_response(&self) -> HttpResponse {
        let status = self.status_code();
        let message = match self {
            AppError::Internal(e) => {
                log::error!("Internal error: {:?}", e);
                "Internal server error".to_string()
            }
            _ => self.to_string(),
        };

        HttpResponse::build(status).json(ErrorResponse {
            error: ErrorBody {
                code: status.as_u16(),
                message,
            },
        })
    }
}
```

## Testing

```rust
// tests/api/user_tests.rs
use actix_web::{test, web, App};
use serde_json::json;

use myapp::{
    api::handlers::user_handler,
    startup::AppState,
};

#[actix_web::test]
async fn test_create_user() {
    let state = web::Data::new(create_test_state().await);

    let app = test::init_service(
        App::new()
            .app_data(state.clone())
            .route("/users", web::post().to(user_handler::create)),
    )
    .await;

    let payload = json!({
        "email": "test@example.com",
        "password": "password123",
        "name": "Test User"
    });

    let req = test::TestRequest::post()
        .uri("/users")
        .set_json(&payload)
        .to_request();

    let resp = test::call_service(&app, req).await;
    assert!(resp.status().is_success());
}

#[actix_web::test]
async fn test_get_user_not_found() {
    let state = web::Data::new(create_test_state().await);

    let app = test::init_service(
        App::new()
            .app_data(state.clone())
            .route("/users/{id}", web::get().to(user_handler::get_by_id)),
    )
    .await;

    let req = test::TestRequest::get()
        .uri("/users/00000000-0000-0000-0000-000000000000")
        .to_request();

    let resp = test::call_service(&app, req).await;
    assert_eq!(resp.status(), 404);
}
```

## Best Practices

1. **Use `web::Data` for shared state**: Wraps state in `Arc` automatically
2. **Configure routes modularly**: Use `ServiceConfig` for route organization
3. **Layer middleware properly**: Order matters for request/response flow
4. **Error handling**: Implement `ResponseError` for custom error types
5. **Extractors**: Use extractors for DRY request parsing
6. **Testing**: Use `actix_web::test` utilities for integration tests
