---
name: rust-error
description: Error handling template with layered errors
applies_to: rust
variables:
  - name: module_name
    description: Module name (e.g., user, product)
  - name: error_types
    description: List of custom error types
---

# Rust Error Template

## Application Error

```rust
// src/error.rs

use axum::{
    http::StatusCode,
    response::{IntoResponse, Response},
    Json,
};
use serde::Serialize;
use thiserror::Error;
use tracing::error;

/// Main application error type
#[derive(Debug, Error)]
pub enum AppError {
    // Client errors (4xx)
    #[error("Bad request: {0}")]
    BadRequest(String),

    #[error("Validation error: {0}")]
    Validation(String),

    #[error("Unauthorized: {0}")]
    Unauthorized(String),

    #[error("Forbidden: {0}")]
    Forbidden(String),

    #[error("Not found: {0}")]
    NotFound(String),

    #[error("Conflict: {0}")]
    Conflict(String),

    #[error("Unprocessable entity: {0}")]
    UnprocessableEntity(String),

    #[error("Too many requests")]
    TooManyRequests,

    // Server errors (5xx)
    #[error("Internal server error")]
    InternalServerError,

    #[error("Service unavailable: {0}")]
    ServiceUnavailable(String),

    // Wrapped errors
    #[error("Database error: {0}")]
    Database(#[from] sqlx::Error),

    #[error("Repository error: {0}")]
    Repository(#[from] RepositoryError),

    #[error("External service error: {0}")]
    ExternalService(String),
}

/// Result type alias
pub type Result<T> = std::result::Result<T, AppError>;

/// Error response body
#[derive(Debug, Serialize)]
pub struct ErrorResponse {
    pub error: ErrorDetails,
}

#[derive(Debug, Serialize)]
pub struct ErrorDetails {
    pub code: String,
    pub message: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub details: Option<Vec<String>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub request_id: Option<String>,
}

impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        let (status, error_code, message, details) = match &self {
            AppError::BadRequest(msg) => (
                StatusCode::BAD_REQUEST,
                "BAD_REQUEST",
                msg.clone(),
                None,
            ),
            AppError::Validation(msg) => (
                StatusCode::UNPROCESSABLE_ENTITY,
                "VALIDATION_ERROR",
                "Validation failed".to_string(),
                Some(vec![msg.clone()]),
            ),
            AppError::Unauthorized(msg) => (
                StatusCode::UNAUTHORIZED,
                "UNAUTHORIZED",
                msg.clone(),
                None,
            ),
            AppError::Forbidden(msg) => (
                StatusCode::FORBIDDEN,
                "FORBIDDEN",
                msg.clone(),
                None,
            ),
            AppError::NotFound(msg) => (
                StatusCode::NOT_FOUND,
                "NOT_FOUND",
                msg.clone(),
                None,
            ),
            AppError::Conflict(msg) => (
                StatusCode::CONFLICT,
                "CONFLICT",
                msg.clone(),
                None,
            ),
            AppError::UnprocessableEntity(msg) => (
                StatusCode::UNPROCESSABLE_ENTITY,
                "UNPROCESSABLE_ENTITY",
                msg.clone(),
                None,
            ),
            AppError::TooManyRequests => (
                StatusCode::TOO_MANY_REQUESTS,
                "TOO_MANY_REQUESTS",
                "Rate limit exceeded".to_string(),
                None,
            ),
            AppError::InternalServerError => {
                error!("Internal server error occurred");
                (
                    StatusCode::INTERNAL_SERVER_ERROR,
                    "INTERNAL_ERROR",
                    "An unexpected error occurred".to_string(),
                    None,
                )
            }
            AppError::ServiceUnavailable(msg) => (
                StatusCode::SERVICE_UNAVAILABLE,
                "SERVICE_UNAVAILABLE",
                msg.clone(),
                None,
            ),
            AppError::Database(e) => {
                error!(error = %e, "Database error");
                (
                    StatusCode::INTERNAL_SERVER_ERROR,
                    "DATABASE_ERROR",
                    "Database operation failed".to_string(),
                    None,
                )
            }
            AppError::Repository(e) => match e {
                RepositoryError::NotFound => (
                    StatusCode::NOT_FOUND,
                    "NOT_FOUND",
                    "Resource not found".to_string(),
                    None,
                ),
                RepositoryError::Conflict(msg) => (
                    StatusCode::CONFLICT,
                    "CONFLICT",
                    msg.clone(),
                    None,
                ),
                _ => {
                    error!(error = %e, "Repository error");
                    (
                        StatusCode::INTERNAL_SERVER_ERROR,
                        "DATABASE_ERROR",
                        "Database operation failed".to_string(),
                        None,
                    )
                }
            },
            AppError::ExternalService(msg) => {
                error!(error = %msg, "External service error");
                (
                    StatusCode::BAD_GATEWAY,
                    "EXTERNAL_SERVICE_ERROR",
                    "External service error".to_string(),
                    None,
                )
            }
        };

        let body = Json(ErrorResponse {
            error: ErrorDetails {
                code: error_code.to_string(),
                message,
                details,
                request_id: None, // Would be set by middleware
            },
        });

        (status, body).into_response()
    }
}
```

## Domain Error

```rust
// src/domain/{{module_name}}/error.rs

use thiserror::Error;

/// Domain-specific error for {{module_name}}
#[derive(Debug, Error)]
pub enum {{module_name | pascal_case}}Error {
    #[error("Invalid {field}: {message}")]
    InvalidField { field: String, message: String },

    #[error("Missing required field: {0}")]
    MissingField(String),

    #[error("Value out of range: {field} must be between {min} and {max}")]
    OutOfRange {
        field: String,
        min: String,
        max: String,
    },

    #[error("Business rule violation: {0}")]
    BusinessRule(String),

    #[error("{0} not found")]
    NotFound(String),

    #[error("{0} already exists")]
    AlreadyExists(String),

    #[error("Invalid state transition from {from} to {to}")]
    InvalidStateTransition { from: String, to: String },
}

impl From<{{module_name | pascal_case}}Error> for crate::error::AppError {
    fn from(error: {{module_name | pascal_case}}Error) -> Self {
        match error {
            {{module_name | pascal_case}}Error::InvalidField { field, message } => {
                Self::Validation(format!("{}: {}", field, message))
            }
            {{module_name | pascal_case}}Error::MissingField(field) => {
                Self::Validation(format!("Missing required field: {}", field))
            }
            {{module_name | pascal_case}}Error::OutOfRange { field, min, max } => {
                Self::Validation(format!("{} must be between {} and {}", field, min, max))
            }
            {{module_name | pascal_case}}Error::BusinessRule(msg) => {
                Self::UnprocessableEntity(msg)
            }
            {{module_name | pascal_case}}Error::NotFound(entity) => {
                Self::NotFound(format!("{} not found", entity))
            }
            {{module_name | pascal_case}}Error::AlreadyExists(entity) => {
                Self::Conflict(format!("{} already exists", entity))
            }
            {{module_name | pascal_case}}Error::InvalidStateTransition { from, to } => {
                Self::UnprocessableEntity(format!(
                    "Cannot transition from {} to {}",
                    from, to
                ))
            }
        }
    }
}
```

## Repository Error

```rust
// src/domain/common/error.rs

use thiserror::Error;

/// Repository layer error
#[derive(Debug, Error)]
pub enum RepositoryError {
    #[error("Entity not found")]
    NotFound,

    #[error("Conflict: {0}")]
    Conflict(String),

    #[error("Database error: {0}")]
    Database(String),

    #[error("Connection error: {0}")]
    Connection(String),

    #[error("Transaction error: {0}")]
    Transaction(String),
}

pub type RepositoryResult<T> = std::result::Result<T, RepositoryError>;

impl From<sqlx::Error> for RepositoryError {
    fn from(error: sqlx::Error) -> Self {
        match error {
            sqlx::Error::RowNotFound => Self::NotFound,
            sqlx::Error::Database(ref db_err) => {
                if db_err.is_unique_violation() {
                    Self::Conflict("Unique constraint violation".to_string())
                } else if db_err.is_foreign_key_violation() {
                    Self::Conflict("Foreign key constraint violation".to_string())
                } else {
                    Self::Database(error.to_string())
                }
            }
            _ => Self::Database(error.to_string()),
        }
    }
}
```

## Validation Error

```rust
// src/domain/common/validation.rs

use serde::Serialize;
use thiserror::Error;

#[derive(Debug, Error, Clone)]
pub enum ValidationError {
    #[error("Invalid {field}: {message}")]
    InvalidField { field: String, message: String },

    #[error("Missing required field: {0}")]
    MissingField(String),

    #[error("Value out of range: {field} must be between {min} and {max}")]
    OutOfRange {
        field: String,
        min: String,
        max: String,
    },

    #[error("Invalid format: {field} - {message}")]
    InvalidFormat { field: String, message: String },

    #[error("Business rule violation: {0}")]
    BusinessRule(String),
}

pub type ValidationResult<T> = std::result::Result<T, Vec<ValidationError>>;

/// Conversion from validator crate errors
impl From<validator::ValidationErrors> for crate::error::AppError {
    fn from(errors: validator::ValidationErrors) -> Self {
        let messages: Vec<String> = errors
            .field_errors()
            .iter()
            .flat_map(|(field, errs)| {
                errs.iter().map(move |e| {
                    format!(
                        "{}: {}",
                        field,
                        e.message.clone().unwrap_or_default()
                    )
                })
            })
            .collect();

        Self::Validation(messages.join("; "))
    }
}
```

## Error Extensions

```rust
// src/error/extensions.rs

use crate::error::{AppError, Result};

/// Extension trait for Option to convert to AppError
pub trait OptionExt<T> {
    fn ok_or_not_found(self, message: impl Into<String>) -> Result<T>;
}

impl<T> OptionExt<T> for Option<T> {
    fn ok_or_not_found(self, message: impl Into<String>) -> Result<T> {
        self.ok_or_else(|| AppError::NotFound(message.into()))
    }
}

/// Extension trait for Result to add context
pub trait ResultExt<T, E> {
    fn context(self, message: impl Into<String>) -> Result<T>;
    fn with_context<F>(self, f: F) -> Result<T>
    where
        F: FnOnce() -> String;
}

impl<T, E: std::error::Error> ResultExt<T, E> for std::result::Result<T, E> {
    fn context(self, message: impl Into<String>) -> Result<T> {
        self.map_err(|e| {
            tracing::error!(error = %e, context = %message.into(), "Error with context");
            AppError::InternalServerError
        })
    }

    fn with_context<F>(self, f: F) -> Result<T>
    where
        F: FnOnce() -> String,
    {
        self.map_err(|e| {
            let context = f();
            tracing::error!(error = %e, context = %context, "Error with context");
            AppError::InternalServerError
        })
    }
}

// Usage examples:
// let user = repo.find_by_id(id).await?.ok_or_not_found("User not found")?;
// let result = external_service.call().await.context("External service failed")?;
```

## Error Middleware

```rust
// src/api/middleware/error_handler.rs

use axum::{
    http::StatusCode,
    response::{IntoResponse, Response},
    Json,
};
use tower::ServiceBuilder;

/// Panic handler middleware
pub fn panic_handler() -> tower_http::catch_panic::CatchPanicLayer<fn(Box<dyn std::any::Any + Send>) -> Response> {
    tower_http::catch_panic::CatchPanicLayer::custom(handle_panic)
}

fn handle_panic(_: Box<dyn std::any::Any + Send>) -> Response {
    tracing::error!("Handler panicked");

    (
        StatusCode::INTERNAL_SERVER_ERROR,
        Json(crate::error::ErrorResponse {
            error: crate::error::ErrorDetails {
                code: "INTERNAL_ERROR".to_string(),
                message: "An unexpected error occurred".to_string(),
                details: None,
                request_id: None,
            },
        }),
    )
        .into_response()
}
```
