---
name: rust-middleware
description: Middleware template for Axum/Tower
applies_to: rust
variables:
  - name: middleware_name
    description: Middleware name (e.g., auth, logging, rate_limit)
  - name: purpose
    description: Brief description of middleware purpose
---

# Rust Middleware Template

## Basic Tower Middleware

```rust
// src/api/middleware/{{middleware_name}}.rs

use axum::{
    body::Body,
    http::{Request, Response, StatusCode},
    response::IntoResponse,
};
use futures::future::BoxFuture;
use std::task::{Context, Poll};
use tower::{Layer, Service};

/// {{middleware_name | title_case}} Middleware Layer
#[derive(Clone)]
pub struct {{middleware_name | pascal_case}}Layer {
    // Configuration fields
    // e.g., config: Config,
}

impl {{middleware_name | pascal_case}}Layer {
    pub fn new() -> Self {
        Self {
            // Initialize configuration
        }
    }
}

impl<S> Layer<S> for {{middleware_name | pascal_case}}Layer {
    type Service = {{middleware_name | pascal_case}}Middleware<S>;

    fn layer(&self, inner: S) -> Self::Service {
        {{middleware_name | pascal_case}}Middleware {
            inner,
            // Pass configuration
        }
    }
}

/// {{middleware_name | title_case}} Middleware Service
#[derive(Clone)]
pub struct {{middleware_name | pascal_case}}Middleware<S> {
    inner: S,
    // Configuration fields
}

impl<S, ReqBody, ResBody> Service<Request<ReqBody>> for {{middleware_name | pascal_case}}Middleware<S>
where
    S: Service<Request<ReqBody>, Response = Response<ResBody>> + Clone + Send + 'static,
    S::Future: Send + 'static,
    ReqBody: Send + 'static,
    ResBody: Default + Send + 'static,
{
    type Response = S::Response;
    type Error = S::Error;
    type Future = BoxFuture<'static, Result<Self::Response, Self::Error>>;

    fn poll_ready(&mut self, cx: &mut Context<'_>) -> Poll<Result<(), Self::Error>> {
        self.inner.poll_ready(cx)
    }

    fn call(&mut self, request: Request<ReqBody>) -> Self::Future {
        let mut inner = self.inner.clone();

        Box::pin(async move {
            // Pre-processing logic
            // e.g., extract headers, validate tokens, etc.

            // Call the inner service
            let response = inner.call(request).await?;

            // Post-processing logic
            // e.g., add headers, log response, etc.

            Ok(response)
        })
    }
}
```

## Authentication Middleware

```rust
// src/api/middleware/auth.rs

use axum::{
    body::Body,
    extract::State,
    http::{header, Request, StatusCode},
    middleware::Next,
    response::{IntoResponse, Response},
    Json,
};

use crate::{
    error::{AppError, ErrorResponse},
    services::jwt::JwtService,
    startup::AppState,
};

/// Authentication middleware using axum::middleware::from_fn
pub async fn auth_middleware(
    State(state): State<AppState>,
    mut request: Request<Body>,
    next: Next,
) -> Result<Response, AppError> {
    // Extract token from Authorization header
    let auth_header = request
        .headers()
        .get(header::AUTHORIZATION)
        .and_then(|value| value.to_str().ok())
        .ok_or(AppError::Unauthorized("Missing authorization header".to_string()))?;

    let token = auth_header
        .strip_prefix("Bearer ")
        .ok_or(AppError::Unauthorized("Invalid authorization header format".to_string()))?;

    // Verify token
    let claims = state
        .jwt_service
        .verify_access_token(token)
        .map_err(|e| AppError::Unauthorized(e.to_string()))?;

    // Insert claims into request extensions
    request.extensions_mut().insert(claims);

    // Continue to the next handler
    Ok(next.run(request).await)
}

/// Optional authentication (doesn't fail if no token)
pub async fn optional_auth_middleware(
    State(state): State<AppState>,
    mut request: Request<Body>,
    next: Next,
) -> Response {
    if let Some(auth_header) = request
        .headers()
        .get(header::AUTHORIZATION)
        .and_then(|value| value.to_str().ok())
    {
        if let Some(token) = auth_header.strip_prefix("Bearer ") {
            if let Ok(claims) = state.jwt_service.verify_access_token(token) {
                request.extensions_mut().insert(claims);
            }
        }
    }

    next.run(request).await
}

/// Role-based authorization middleware
pub fn require_role(
    required_role: &'static str,
) -> impl Fn(Request<Body>, Next) -> BoxFuture<'static, Result<Response, AppError>> + Clone {
    move |request: Request<Body>, next: Next| {
        Box::pin(async move {
            let claims = request
                .extensions()
                .get::<Claims>()
                .ok_or(AppError::Unauthorized("No authentication".to_string()))?;

            if claims.role != required_role && claims.role != "admin" {
                return Err(AppError::Forbidden(format!(
                    "Role '{}' required",
                    required_role
                )));
            }

            Ok(next.run(request).await)
        })
    }
}
```

## Request ID Middleware

```rust
// src/api/middleware/request_id.rs

use axum::{
    body::Body,
    http::{header::HeaderName, HeaderValue, Request},
    middleware::Next,
    response::Response,
};
use uuid::Uuid;

pub static X_REQUEST_ID: HeaderName = HeaderName::from_static("x-request-id");

/// Adds a unique request ID to each request
pub async fn request_id_middleware(
    mut request: Request<Body>,
    next: Next,
) -> Response {
    // Check for existing request ID or generate new one
    let request_id = request
        .headers()
        .get(&X_REQUEST_ID)
        .and_then(|v| v.to_str().ok())
        .map(String::from)
        .unwrap_or_else(|| Uuid::new_v4().to_string());

    // Insert into extensions for handlers to access
    request.extensions_mut().insert(RequestId(request_id.clone()));

    // Run the request
    let mut response = next.run(request).await;

    // Add request ID to response headers
    response.headers_mut().insert(
        X_REQUEST_ID.clone(),
        HeaderValue::from_str(&request_id).unwrap(),
    );

    response
}

#[derive(Debug, Clone)]
pub struct RequestId(pub String);
```

## Logging Middleware

```rust
// src/api/middleware/logging.rs

use axum::{
    body::Body,
    http::Request,
    middleware::Next,
    response::Response,
};
use std::time::Instant;
use tracing::{info, warn, Span};

/// Request/response logging middleware
pub async fn logging_middleware(
    request: Request<Body>,
    next: Next,
) -> Response {
    let method = request.method().clone();
    let uri = request.uri().clone();
    let version = request.version();

    // Extract request ID if available
    let request_id = request
        .extensions()
        .get::<RequestId>()
        .map(|id| id.0.clone())
        .unwrap_or_else(|| "unknown".to_string());

    let span = tracing::info_span!(
        "http_request",
        method = %method,
        uri = %uri,
        version = ?version,
        request_id = %request_id,
    );

    let start = Instant::now();

    let response = next.run(request).await;

    let latency = start.elapsed();
    let status = response.status();

    if status.is_server_error() {
        warn!(
            parent: &span,
            status = %status.as_u16(),
            latency_ms = %latency.as_millis(),
            "Request completed with server error"
        );
    } else if status.is_client_error() {
        info!(
            parent: &span,
            status = %status.as_u16(),
            latency_ms = %latency.as_millis(),
            "Request completed with client error"
        );
    } else {
        info!(
            parent: &span,
            status = %status.as_u16(),
            latency_ms = %latency.as_millis(),
            "Request completed"
        );
    }

    response
}
```

## Rate Limiting Middleware

```rust
// src/api/middleware/rate_limit.rs

use axum::{
    body::Body,
    http::{Request, StatusCode},
    middleware::Next,
    response::{IntoResponse, Response},
};
use std::sync::Arc;
use tokio::sync::Mutex;
use std::collections::HashMap;
use std::time::{Duration, Instant};

pub struct RateLimiter {
    requests: Mutex<HashMap<String, Vec<Instant>>>,
    max_requests: usize,
    window: Duration,
}

impl RateLimiter {
    pub fn new(max_requests: usize, window: Duration) -> Self {
        Self {
            requests: Mutex::new(HashMap::new()),
            max_requests,
            window,
        }
    }

    pub async fn check(&self, key: &str) -> bool {
        let mut requests = self.requests.lock().await;
        let now = Instant::now();
        let window_start = now - self.window;

        let entry = requests.entry(key.to_string()).or_insert_with(Vec::new);

        // Remove old requests
        entry.retain(|&time| time > window_start);

        if entry.len() >= self.max_requests {
            false
        } else {
            entry.push(now);
            true
        }
    }
}

/// Rate limiting middleware
pub async fn rate_limit_middleware(
    State(limiter): State<Arc<RateLimiter>>,
    request: Request<Body>,
    next: Next,
) -> Response {
    // Extract client identifier (IP address, API key, user ID, etc.)
    let client_id = request
        .headers()
        .get("X-Forwarded-For")
        .and_then(|v| v.to_str().ok())
        .unwrap_or("unknown")
        .to_string();

    if !limiter.check(&client_id).await {
        return (
            StatusCode::TOO_MANY_REQUESTS,
            "Rate limit exceeded",
        ).into_response();
    }

    next.run(request).await
}
```

## CORS Middleware

```rust
// src/api/middleware/cors.rs

use axum::http::{header, Method};
use tower_http::cors::{Any, CorsLayer};

/// Configure CORS for the application
pub fn cors_layer() -> CorsLayer {
    CorsLayer::new()
        .allow_origin(Any)
        .allow_methods([
            Method::GET,
            Method::POST,
            Method::PUT,
            Method::PATCH,
            Method::DELETE,
            Method::OPTIONS,
        ])
        .allow_headers([
            header::AUTHORIZATION,
            header::CONTENT_TYPE,
            header::ACCEPT,
        ])
        .max_age(std::time::Duration::from_secs(3600))
}

/// Restrictive CORS for production
pub fn production_cors_layer(allowed_origins: Vec<String>) -> CorsLayer {
    let origins: Vec<_> = allowed_origins
        .iter()
        .filter_map(|o| o.parse().ok())
        .collect();

    CorsLayer::new()
        .allow_origin(origins)
        .allow_methods([
            Method::GET,
            Method::POST,
            Method::PUT,
            Method::PATCH,
            Method::DELETE,
        ])
        .allow_headers([
            header::AUTHORIZATION,
            header::CONTENT_TYPE,
        ])
        .allow_credentials(true)
        .max_age(std::time::Duration::from_secs(3600))
}
```

## Combining Middleware

```rust
// src/api/middleware/mod.rs

use axum::{middleware, Router};
use tower::ServiceBuilder;
use tower_http::{
    compression::CompressionLayer,
    timeout::TimeoutLayer,
    trace::TraceLayer,
};
use std::time::Duration;

pub mod auth;
pub mod cors;
pub mod logging;
pub mod rate_limit;
pub mod request_id;

use auth::auth_middleware;
use cors::cors_layer;
use logging::logging_middleware;
use rate_limit::{rate_limit_middleware, RateLimiter};
use request_id::request_id_middleware;

/// Apply all middleware to router
pub fn apply_middleware(router: Router<AppState>, state: AppState) -> Router<AppState> {
    let rate_limiter = Arc::new(RateLimiter::new(100, Duration::from_secs(60)));

    router
        .layer(
            ServiceBuilder::new()
                // Outermost: Timeout
                .layer(TimeoutLayer::new(Duration::from_secs(30)))
                // Compression
                .layer(CompressionLayer::new())
                // CORS
                .layer(cors_layer())
                // Tracing
                .layer(TraceLayer::new_for_http())
        )
        // Request ID (using from_fn)
        .layer(middleware::from_fn(request_id_middleware))
        // Logging
        .layer(middleware::from_fn(logging_middleware))
        // Rate limiting
        .layer(middleware::from_fn_with_state(
            rate_limiter,
            rate_limit_middleware,
        ))
}

/// Protected routes with authentication
pub fn protected_routes(router: Router<AppState>, state: AppState) -> Router<AppState> {
    router.layer(middleware::from_fn_with_state(state, auth_middleware))
}
```
