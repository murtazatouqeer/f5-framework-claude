---
name: rust-tower-middleware
description: Tower middleware patterns for Rust web frameworks
applies_to: rust
---

# Tower Middleware Patterns

## Overview

Tower is a library of modular, reusable components for building robust networking clients and servers.
Axum is built on Tower, making middleware composition powerful and flexible.

## Basic Middleware Structure

```rust
// src/middleware/logging.rs
use axum::{
    body::Body,
    http::Request,
    middleware::Next,
    response::Response,
};
use std::time::Instant;

/// Simple logging middleware
pub async fn logging_middleware(
    request: Request<Body>,
    next: Next,
) -> Response {
    let start = Instant::now();
    let method = request.method().clone();
    let uri = request.uri().clone();

    let response = next.run(request).await;

    let duration = start.elapsed();
    let status = response.status();

    tracing::info!(
        method = %method,
        uri = %uri,
        status = %status,
        duration_ms = %duration.as_millis(),
        "Request completed"
    );

    response
}
```

## Middleware with State

```rust
// src/middleware/auth.rs
use axum::{
    body::Body,
    extract::State,
    http::{Request, StatusCode},
    middleware::Next,
    response::{IntoResponse, Response},
};
use axum_extra::{
    headers::{authorization::Bearer, Authorization},
    TypedHeader,
};

use crate::startup::AppState;

/// Authentication middleware
pub async fn auth_middleware(
    State(state): State<AppState>,
    TypedHeader(auth): TypedHeader<Authorization<Bearer>>,
    request: Request<Body>,
    next: Next,
) -> Result<Response, StatusCode> {
    // Verify JWT token
    let claims = jsonwebtoken::decode::<Claims>(
        auth.token(),
        &jsonwebtoken::DecodingKey::from_secret(state.config.jwt.secret.as_bytes()),
        &jsonwebtoken::Validation::default(),
    )
    .map_err(|_| StatusCode::UNAUTHORIZED)?;

    // Check expiration
    let now = chrono::Utc::now().timestamp();
    if claims.claims.exp < now {
        return Err(StatusCode::UNAUTHORIZED);
    }

    // Continue to next handler
    Ok(next.run(request).await)
}

// Usage in router:
// .layer(axum::middleware::from_fn_with_state(state, auth_middleware))
```

## Request ID Middleware

```rust
// src/middleware/request_id.rs
use axum::{
    body::Body,
    http::{header::HeaderName, Request},
    middleware::Next,
    response::Response,
};
use uuid::Uuid;

static X_REQUEST_ID: HeaderName = HeaderName::from_static("x-request-id");

/// Adds a unique request ID to each request
pub async fn request_id_middleware(
    mut request: Request<Body>,
    next: Next,
) -> Response {
    // Get existing request ID or generate new one
    let request_id = request
        .headers()
        .get(&X_REQUEST_ID)
        .and_then(|v| v.to_str().ok())
        .map(String::from)
        .unwrap_or_else(|| Uuid::new_v4().to_string());

    // Add to request extensions for use in handlers
    request.extensions_mut().insert(RequestId(request_id.clone()));

    let mut response = next.run(request).await;

    // Add to response headers
    response.headers_mut().insert(
        &X_REQUEST_ID,
        request_id.parse().unwrap(),
    );

    response
}

#[derive(Clone, Debug)]
pub struct RequestId(pub String);
```

## Rate Limiting Middleware

```rust
// src/middleware/rate_limit.rs
use axum::{
    body::Body,
    extract::ConnectInfo,
    http::{Request, StatusCode},
    middleware::Next,
    response::{IntoResponse, Response},
};
use std::{
    collections::HashMap,
    net::SocketAddr,
    sync::Arc,
    time::{Duration, Instant},
};
use tokio::sync::RwLock;

#[derive(Clone)]
pub struct RateLimiter {
    requests: Arc<RwLock<HashMap<String, Vec<Instant>>>>,
    max_requests: usize,
    window: Duration,
}

impl RateLimiter {
    pub fn new(max_requests: usize, window: Duration) -> Self {
        Self {
            requests: Arc::new(RwLock::new(HashMap::new())),
            max_requests,
            window,
        }
    }

    async fn is_allowed(&self, key: &str) -> bool {
        let now = Instant::now();
        let mut requests = self.requests.write().await;

        let timestamps = requests.entry(key.to_string()).or_insert_with(Vec::new);

        // Remove old timestamps
        timestamps.retain(|t| now.duration_since(*t) < self.window);

        if timestamps.len() < self.max_requests {
            timestamps.push(now);
            true
        } else {
            false
        }
    }
}

pub async fn rate_limit_middleware(
    ConnectInfo(addr): ConnectInfo<SocketAddr>,
    axum::extract::State(limiter): axum::extract::State<RateLimiter>,
    request: Request<Body>,
    next: Next,
) -> Response {
    let key = addr.ip().to_string();

    if !limiter.is_allowed(&key).await {
        return (
            StatusCode::TOO_MANY_REQUESTS,
            "Rate limit exceeded",
        ).into_response();
    }

    next.run(request).await
}
```

## CORS Configuration

```rust
// src/middleware/cors.rs
use axum::http::{HeaderValue, Method};
use tower_http::cors::{Any, CorsLayer};

/// Create CORS layer for development
pub fn cors_layer_dev() -> CorsLayer {
    CorsLayer::new()
        .allow_origin(Any)
        .allow_methods(Any)
        .allow_headers(Any)
        .expose_headers(Any)
}

/// Create CORS layer for production
pub fn cors_layer_prod(allowed_origins: &[&str]) -> CorsLayer {
    let origins: Vec<HeaderValue> = allowed_origins
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
            Method::OPTIONS,
        ])
        .allow_headers([
            axum::http::header::AUTHORIZATION,
            axum::http::header::CONTENT_TYPE,
            axum::http::header::ACCEPT,
        ])
        .expose_headers([
            axum::http::header::CONTENT_LENGTH,
            HeaderName::from_static("x-request-id"),
        ])
        .max_age(Duration::from_secs(3600))
}
```

## Compression Middleware

```rust
// src/middleware/compression.rs
use tower_http::compression::{
    CompressionLayer,
    predicate::{NotForContentType, SizeAbove},
    Predicate,
};

/// Create compression layer with sensible defaults
pub fn compression_layer() -> CompressionLayer {
    CompressionLayer::new()
        .quality(tower_http::CompressionLevel::Default)
}

/// Create compression layer with custom predicates
pub fn compression_layer_custom() -> CompressionLayer {
    // Don't compress small responses or already compressed content
    let predicate = SizeAbove::new(1024)
        .and(NotForContentType::GRPC)
        .and(NotForContentType::IMAGES)
        .and(NotForContentType::SSE);

    CompressionLayer::new()
        .compress_when(predicate)
}
```

## Request Body Limit

```rust
// src/middleware/body_limit.rs
use tower_http::limit::RequestBodyLimitLayer;

/// Limit request body size to 10MB
pub fn body_limit_layer() -> RequestBodyLimitLayer {
    RequestBodyLimitLayer::new(10 * 1024 * 1024)
}

/// Limit request body size to custom value
pub fn body_limit_layer_custom(max_bytes: usize) -> RequestBodyLimitLayer {
    RequestBodyLimitLayer::new(max_bytes)
}
```

## Timeout Middleware

```rust
// src/middleware/timeout.rs
use std::time::Duration;
use tower_http::timeout::TimeoutLayer;

/// Default 30 second timeout
pub fn timeout_layer() -> TimeoutLayer {
    TimeoutLayer::new(Duration::from_secs(30))
}

/// Custom timeout
pub fn timeout_layer_custom(seconds: u64) -> TimeoutLayer {
    TimeoutLayer::new(Duration::from_secs(seconds))
}
```

## Security Headers

```rust
// src/middleware/security.rs
use axum::{
    body::Body,
    http::{header, Request},
    middleware::Next,
    response::Response,
};

/// Add security headers to all responses
pub async fn security_headers_middleware(
    request: Request<Body>,
    next: Next,
) -> Response {
    let mut response = next.run(request).await;
    let headers = response.headers_mut();

    // Prevent MIME type sniffing
    headers.insert(
        header::X_CONTENT_TYPE_OPTIONS,
        "nosniff".parse().unwrap(),
    );

    // Prevent clickjacking
    headers.insert(
        header::X_FRAME_OPTIONS,
        "DENY".parse().unwrap(),
    );

    // Enable XSS protection
    headers.insert(
        "X-XSS-Protection",
        "1; mode=block".parse().unwrap(),
    );

    // Strict Transport Security (HTTPS only)
    headers.insert(
        header::STRICT_TRANSPORT_SECURITY,
        "max-age=31536000; includeSubDomains".parse().unwrap(),
    );

    // Content Security Policy
    headers.insert(
        header::CONTENT_SECURITY_POLICY,
        "default-src 'self'".parse().unwrap(),
    );

    // Referrer Policy
    headers.insert(
        header::REFERRER_POLICY,
        "strict-origin-when-cross-origin".parse().unwrap(),
    );

    response
}
```

## Combining Middleware

```rust
// src/api/router.rs
use axum::{
    middleware,
    Router,
};
use tower::ServiceBuilder;
use tower_http::{
    compression::CompressionLayer,
    cors::CorsLayer,
    timeout::TimeoutLayer,
    trace::TraceLayer,
};
use std::time::Duration;

use crate::{
    middleware::{
        auth::auth_middleware,
        logging::logging_middleware,
        request_id::request_id_middleware,
        security::security_headers_middleware,
    },
    startup::AppState,
};

pub fn create_router(state: AppState) -> Router {
    // Public routes
    let public_routes = Router::new()
        .route("/health", get(health_check))
        .route("/auth/login", post(login));

    // Protected routes
    let protected_routes = Router::new()
        .route("/users", get(list_users))
        .route("/users/:id", get(get_user))
        .layer(middleware::from_fn_with_state(state.clone(), auth_middleware));

    // Combine with middleware stack
    Router::new()
        .nest("/api/v1", public_routes.merge(protected_routes))
        .layer(
            ServiceBuilder::new()
                // Applied bottom-to-top (last added = first executed)
                .layer(middleware::from_fn(security_headers_middleware))
                .layer(middleware::from_fn(request_id_middleware))
                .layer(middleware::from_fn(logging_middleware))
                .layer(CompressionLayer::new())
                .layer(TimeoutLayer::new(Duration::from_secs(30)))
                .layer(CorsLayer::permissive())
                .layer(TraceLayer::new_for_http()),
        )
        .with_state(state)
}
```

## Custom Tower Service

```rust
// src/middleware/custom_service.rs
use axum::{
    body::Body,
    http::{Request, Response},
};
use std::{
    future::Future,
    pin::Pin,
    task::{Context, Poll},
};
use tower::{Layer, Service};

#[derive(Clone)]
pub struct MyLayer;

impl<S> Layer<S> for MyLayer {
    type Service = MyService<S>;

    fn layer(&self, inner: S) -> Self::Service {
        MyService { inner }
    }
}

#[derive(Clone)]
pub struct MyService<S> {
    inner: S,
}

impl<S> Service<Request<Body>> for MyService<S>
where
    S: Service<Request<Body>, Response = Response<Body>> + Clone + Send + 'static,
    S::Future: Send,
{
    type Response = S::Response;
    type Error = S::Error;
    type Future = Pin<Box<dyn Future<Output = Result<Self::Response, Self::Error>> + Send>>;

    fn poll_ready(&mut self, cx: &mut Context<'_>) -> Poll<Result<(), Self::Error>> {
        self.inner.poll_ready(cx)
    }

    fn call(&mut self, request: Request<Body>) -> Self::Future {
        let clone = self.inner.clone();
        let mut inner = std::mem::replace(&mut self.inner, clone);

        Box::pin(async move {
            // Pre-processing
            tracing::debug!("Before request");

            let response = inner.call(request).await?;

            // Post-processing
            tracing::debug!("After request");

            Ok(response)
        })
    }
}
```

## Middleware Order Guidelines

```
Request flow (top to bottom):
┌─────────────────────────────┐
│  TraceLayer (outermost)     │ ← First to receive request
├─────────────────────────────┤
│  CorsLayer                  │
├─────────────────────────────┤
│  TimeoutLayer               │
├─────────────────────────────┤
│  CompressionLayer           │
├─────────────────────────────┤
│  RequestIdMiddleware        │
├─────────────────────────────┤
│  SecurityHeadersMiddleware  │
├─────────────────────────────┤
│  AuthMiddleware             │
├─────────────────────────────┤
│  Handler (innermost)        │ ← Actual request handling
└─────────────────────────────┘

Response flow (bottom to top)
```

## Best Practices

1. **Order matters**: Layer middleware carefully - outer layers wrap inner ones
2. **Use ServiceBuilder**: Compose multiple layers cleanly
3. **State in middleware**: Use `from_fn_with_state` for stateful middleware
4. **Error handling**: Convert errors to appropriate HTTP responses
5. **Performance**: Put expensive operations (auth, rate limit) after cheap ones
6. **Tracing**: Always use TraceLayer for observability
7. **Timeout**: Set reasonable timeouts to prevent resource exhaustion
