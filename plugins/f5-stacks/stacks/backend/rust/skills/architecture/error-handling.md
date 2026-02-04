---
name: rust-error-handling
description: Comprehensive error handling patterns in Rust
applies_to: rust
---

# Error Handling in Rust

## Overview

Rust's error handling is explicit and type-safe. Use `Result<T, E>` for recoverable errors
and proper error types for each layer of the application.

## Error Type Hierarchy

```
AppError (HTTP Response)
    ├── DomainError (Business Logic)
    ├── ServiceError (Application Layer)
    ├── RepositoryError (Infrastructure)
    └── ValidationError (Input Validation)
```

## Domain Errors

Define specific errors for each domain entity.

```rust
// src/domain/order/error.rs
use thiserror::Error;

#[derive(Debug, Error)]
pub enum OrderError {
    #[error("Order cannot be empty")]
    EmptyOrder,

    #[error("Quantity must be greater than zero")]
    InvalidQuantity,

    #[error("Price must be positive")]
    InvalidPrice,

    #[error("Invalid state transition from {from:?} to {to:?}")]
    InvalidStateTransition {
        from: OrderStatus,
        to: OrderStatus,
    },

    #[error("Cannot cancel shipped order")]
    CannotCancelShippedOrder,

    #[error("Order is already completed")]
    AlreadyCompleted,
}
```

## Repository Errors

Generic errors for data access layer.

```rust
// src/domain/common/repository_error.rs
use thiserror::Error;

#[derive(Debug, Error)]
pub enum RepositoryError {
    #[error("Entity not found: {entity_type} with id {id}")]
    NotFound {
        entity_type: &'static str,
        id: String,
    },

    #[error("Duplicate entity: {entity_type}")]
    Duplicate {
        entity_type: &'static str,
    },

    #[error("Constraint violation: {0}")]
    ConstraintViolation(String),

    #[error("Connection error: {0}")]
    Connection(String),

    #[error("Query error: {0}")]
    Query(String),

    #[error("Transaction error: {0}")]
    Transaction(String),
}

impl From<sqlx::Error> for RepositoryError {
    fn from(err: sqlx::Error) -> Self {
        match err {
            sqlx::Error::RowNotFound => RepositoryError::NotFound {
                entity_type: "unknown",
                id: "unknown".to_string(),
            },
            sqlx::Error::Database(db_err) => {
                if let Some(code) = db_err.code() {
                    match code.as_ref() {
                        "23505" => RepositoryError::Duplicate {
                            entity_type: "unknown",
                        },
                        "23503" => RepositoryError::ConstraintViolation(
                            db_err.message().to_string()
                        ),
                        _ => RepositoryError::Query(db_err.message().to_string()),
                    }
                } else {
                    RepositoryError::Query(db_err.message().to_string())
                }
            }
            sqlx::Error::PoolTimedOut => {
                RepositoryError::Connection("Pool timed out".to_string())
            }
            _ => RepositoryError::Query(err.to_string()),
        }
    }
}
```

## Service Errors

Combine domain and infrastructure errors at the application layer.

```rust
// src/application/order/error.rs
use thiserror::Error;

use crate::domain::{
    order::error::OrderError,
    common::RepositoryError,
};

#[derive(Debug, Error)]
pub enum OrderServiceError {
    #[error("Order not found: {0}")]
    NotFound(String),

    #[error("Unauthorized access to order")]
    Unauthorized,

    #[error("Order validation failed: {0}")]
    Validation(String),

    #[error(transparent)]
    Domain(#[from] OrderError),

    #[error(transparent)]
    Repository(#[from] RepositoryError),

    #[error("External service error: {0}")]
    ExternalService(String),
}
```

## Application Error (HTTP Layer)

Central error type that converts to HTTP responses.

```rust
// src/error.rs
use axum::{
    http::StatusCode,
    response::{IntoResponse, Response},
    Json,
};
use serde::Serialize;
use thiserror::Error;

use crate::application::order::OrderServiceError;

/// Application-wide result type
pub type Result<T> = std::result::Result<T, AppError>;

/// Application error with HTTP mapping
#[derive(Debug, Error)]
pub enum AppError {
    // Client errors (4xx)
    #[error("Not found: {0}")]
    NotFound(String),

    #[error("Bad request: {0}")]
    BadRequest(String),

    #[error("Validation error: {0}")]
    Validation(String),

    #[error("Unauthorized: {0}")]
    Unauthorized(String),

    #[error("Forbidden: {0}")]
    Forbidden(String),

    #[error("Conflict: {0}")]
    Conflict(String),

    #[error("Unprocessable entity: {0}")]
    UnprocessableEntity(String),

    // Server errors (5xx)
    #[error("Internal server error")]
    Internal(#[source] anyhow::Error),

    #[error("Service unavailable: {0}")]
    ServiceUnavailable(String),
}

/// Error response body
#[derive(Serialize)]
struct ErrorResponse {
    error: ErrorBody,
}

#[derive(Serialize)]
struct ErrorBody {
    code: u16,
    message: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    details: Option<Vec<String>>,
}

impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        let (status, message, details) = match &self {
            // Client errors
            AppError::NotFound(msg) => (StatusCode::NOT_FOUND, msg.clone(), None),
            AppError::BadRequest(msg) => (StatusCode::BAD_REQUEST, msg.clone(), None),
            AppError::Validation(msg) => (
                StatusCode::UNPROCESSABLE_ENTITY,
                "Validation failed".to_string(),
                Some(vec![msg.clone()]),
            ),
            AppError::Unauthorized(msg) => (StatusCode::UNAUTHORIZED, msg.clone(), None),
            AppError::Forbidden(msg) => (StatusCode::FORBIDDEN, msg.clone(), None),
            AppError::Conflict(msg) => (StatusCode::CONFLICT, msg.clone(), None),
            AppError::UnprocessableEntity(msg) => {
                (StatusCode::UNPROCESSABLE_ENTITY, msg.clone(), None)
            }

            // Server errors - log and return generic message
            AppError::Internal(e) => {
                tracing::error!(error = ?e, "Internal server error");
                (
                    StatusCode::INTERNAL_SERVER_ERROR,
                    "Internal server error".to_string(),
                    None,
                )
            }
            AppError::ServiceUnavailable(msg) => {
                tracing::warn!(message = %msg, "Service unavailable");
                (StatusCode::SERVICE_UNAVAILABLE, msg.clone(), None)
            }
        };

        let body = Json(ErrorResponse {
            error: ErrorBody {
                code: status.as_u16(),
                message,
                details,
            },
        });

        (status, body).into_response()
    }
}

// Conversions from service errors
impl From<OrderServiceError> for AppError {
    fn from(err: OrderServiceError) -> Self {
        match err {
            OrderServiceError::NotFound(id) => AppError::NotFound(format!("Order {}", id)),
            OrderServiceError::Unauthorized => {
                AppError::Forbidden("Not authorized to access this order".to_string())
            }
            OrderServiceError::Validation(msg) => AppError::Validation(msg),
            OrderServiceError::Domain(e) => AppError::BadRequest(e.to_string()),
            OrderServiceError::Repository(e) => match e {
                RepositoryError::NotFound { .. } => AppError::NotFound(e.to_string()),
                RepositoryError::Duplicate { .. } => AppError::Conflict(e.to_string()),
                _ => AppError::Internal(e.into()),
            },
            OrderServiceError::ExternalService(msg) => AppError::ServiceUnavailable(msg),
        }
    }
}

// From anyhow for unexpected errors
impl From<anyhow::Error> for AppError {
    fn from(err: anyhow::Error) -> Self {
        AppError::Internal(err)
    }
}
```

## Validation Errors

Structured validation errors with field-level details.

```rust
// src/api/validation.rs
use serde::Serialize;
use validator::ValidationErrors;

use crate::error::AppError;

#[derive(Debug, Serialize)]
pub struct ValidationErrorResponse {
    pub message: String,
    pub errors: Vec<FieldError>,
}

#[derive(Debug, Serialize)]
pub struct FieldError {
    pub field: String,
    pub message: String,
    pub code: String,
}

impl From<ValidationErrors> for AppError {
    fn from(errors: ValidationErrors) -> Self {
        let field_errors: Vec<FieldError> = errors
            .field_errors()
            .iter()
            .flat_map(|(field, errors)| {
                errors.iter().map(move |error| FieldError {
                    field: field.to_string(),
                    message: error.message
                        .clone()
                        .unwrap_or_else(|| "Invalid value".into())
                        .to_string(),
                    code: error.code.to_string(),
                })
            })
            .collect();

        let messages: Vec<String> = field_errors
            .iter()
            .map(|e| format!("{}: {}", e.field, e.message))
            .collect();

        AppError::Validation(messages.join(", "))
    }
}
```

## Error Helpers

Utility functions for common error patterns.

```rust
// src/error/helpers.rs
use crate::error::{AppError, Result};

/// Extension trait for Option to convert to AppError::NotFound
pub trait OptionExt<T> {
    fn ok_or_not_found(self, entity: &str, id: impl ToString) -> Result<T>;
}

impl<T> OptionExt<T> for Option<T> {
    fn ok_or_not_found(self, entity: &str, id: impl ToString) -> Result<T> {
        self.ok_or_else(|| {
            AppError::NotFound(format!("{} with id {} not found", entity, id.to_string()))
        })
    }
}

/// Extension trait for Result to add context
pub trait ResultExt<T, E> {
    fn with_context(self, context: impl FnOnce() -> String) -> Result<T>;
}

impl<T, E: Into<AppError>> ResultExt<T, E> for std::result::Result<T, E> {
    fn with_context(self, context: impl FnOnce() -> String) -> Result<T> {
        self.map_err(|e| {
            let app_error = e.into();
            tracing::debug!(error = ?app_error, context = %context());
            app_error
        })
    }
}
```

## Usage in Handlers

```rust
// src/api/handlers/order_handler.rs
use axum::{
    extract::{Path, State},
    Json,
};
use uuid::Uuid;
use validator::Validate;

use crate::{
    api::extractors::CurrentUser,
    application::order::{CreateOrderDto, OrderResponse},
    error::{AppError, Result},
    startup::AppState,
};

pub async fn create_order(
    State(state): State<AppState>,
    current_user: CurrentUser,
    Json(payload): Json<CreateOrderDto>,
) -> Result<Json<OrderResponse>> {
    // Validation - converts ValidationErrors to AppError
    payload.validate()?;

    // Service call - converts ServiceError to AppError
    let order = state.order_service
        .create_order(current_user.id, payload.into())
        .await?;

    Ok(Json(order.into()))
}

pub async fn get_order(
    State(state): State<AppState>,
    Path(id): Path<Uuid>,
) -> Result<Json<OrderResponse>> {
    let order = state.order_service
        .get_order(id)
        .await?;

    Ok(Json(order.into()))
}
```

## Error Logging with Tracing

```rust
// src/middleware/error_logging.rs
use axum::{
    body::Body,
    http::Request,
    middleware::Next,
    response::Response,
};
use std::time::Instant;

pub async fn error_logging_middleware(
    request: Request<Body>,
    next: Next,
) -> Response {
    let start = Instant::now();
    let method = request.method().clone();
    let uri = request.uri().clone();

    let response = next.run(request).await;

    let status = response.status();
    let duration = start.elapsed();

    if status.is_server_error() {
        tracing::error!(
            method = %method,
            uri = %uri,
            status = %status,
            duration_ms = %duration.as_millis(),
            "Server error"
        );
    } else if status.is_client_error() {
        tracing::warn!(
            method = %method,
            uri = %uri,
            status = %status,
            duration_ms = %duration.as_millis(),
            "Client error"
        );
    }

    response
}
```

## Best Practices

1. **Use `thiserror` for error types**: Provides derive macros for Error trait
2. **Use `anyhow` for unexpected errors**: Wrap errors that shouldn't occur
3. **Layer-specific errors**: Each layer has its own error type
4. **Convert at boundaries**: Transform errors when crossing layer boundaries
5. **Log internal errors**: Log server errors, not client errors
6. **Don't expose internals**: Hide implementation details from API responses
7. **Use extension traits**: Provide ergonomic error conversion methods
