---
name: rust-security-extractors
description: Security-focused extractors for Rust web frameworks
applies_to: rust
---

# Security Extractors

## Overview

Extractors are used to extract and validate data from HTTP requests.
Security extractors handle authentication, authorization, and input sanitization.

## Current User Extractor

```rust
// src/api/extractors/current_user.rs
use axum::{
    async_trait,
    extract::FromRequestParts,
    http::request::Parts,
    RequestPartsExt,
};
use axum_extra::{
    headers::{authorization::Bearer, Authorization},
    TypedHeader,
};
use uuid::Uuid;

use crate::{
    domain::auth::claims::AccessTokenClaims,
    error::AppError,
    startup::AppState,
};

/// Authenticated user extracted from JWT token
#[derive(Debug, Clone)]
pub struct CurrentUser {
    pub id: Uuid,
    pub email: String,
    pub role: String,
    pub is_admin: bool,
}

impl CurrentUser {
    pub fn has_role(&self, role: &str) -> bool {
        self.role == role || self.is_admin
    }

    pub fn can_access_resource(&self, owner_id: Uuid) -> bool {
        self.id == owner_id || self.is_admin
    }
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
        let token_data = state.jwt_service
            .verify_access_token(bearer.token())
            .map_err(|e| {
                tracing::debug!(error = ?e, "Token verification failed");
                AppError::Unauthorized("Invalid or expired token".into())
            })?;

        let claims = token_data.claims;

        // Check if user still exists and is active
        let user = state.user_repo
            .get_by_id(claims.sub)
            .await
            .map_err(|_| AppError::Internal(anyhow::anyhow!("Database error")))?
            .ok_or_else(|| AppError::Unauthorized("User not found".into()))?;

        if !user.is_active {
            return Err(AppError::Forbidden("Account is disabled".into()));
        }

        Ok(CurrentUser {
            id: claims.sub,
            email: claims.email,
            role: claims.role,
            is_admin: claims.is_admin,
        })
    }
}
```

## Optional User Extractor

```rust
// src/api/extractors/maybe_user.rs
use axum::{
    async_trait,
    extract::FromRequestParts,
    http::request::Parts,
};

use super::CurrentUser;
use crate::startup::AppState;

/// Optional authentication - returns None if not authenticated
pub struct MaybeUser(pub Option<CurrentUser>);

#[async_trait]
impl FromRequestParts<AppState> for MaybeUser {
    type Rejection = std::convert::Infallible;

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

impl MaybeUser {
    pub fn user(&self) -> Option<&CurrentUser> {
        self.0.as_ref()
    }

    pub fn is_authenticated(&self) -> bool {
        self.0.is_some()
    }
}
```

## Admin User Extractor

```rust
// src/api/extractors/admin_user.rs
use axum::{
    async_trait,
    extract::FromRequestParts,
    http::request::Parts,
};

use super::CurrentUser;
use crate::{error::AppError, startup::AppState};

/// Requires admin role
pub struct AdminUser(pub CurrentUser);

#[async_trait]
impl FromRequestParts<AppState> for AdminUser {
    type Rejection = AppError;

    async fn from_request_parts(
        parts: &mut Parts,
        state: &AppState,
    ) -> Result<Self, Self::Rejection> {
        let user = CurrentUser::from_request_parts(parts, state).await?;

        if !user.is_admin {
            return Err(AppError::Forbidden("Admin access required".into()));
        }

        Ok(AdminUser(user))
    }
}

impl std::ops::Deref for AdminUser {
    type Target = CurrentUser;

    fn deref(&self) -> &Self::Target {
        &self.0
    }
}
```

## Role-Based Extractor

```rust
// src/api/extractors/role_user.rs
use axum::{
    async_trait,
    extract::FromRequestParts,
    http::request::Parts,
};
use std::marker::PhantomData;

use super::CurrentUser;
use crate::{error::AppError, startup::AppState};

/// Trait for defining required roles
pub trait RequiredRole: Send + Sync {
    fn role() -> &'static str;
}

/// Requires specific role
pub struct RoleUser<R: RequiredRole> {
    pub user: CurrentUser,
    _marker: PhantomData<R>,
}

#[async_trait]
impl<R: RequiredRole> FromRequestParts<AppState> for RoleUser<R> {
    type Rejection = AppError;

    async fn from_request_parts(
        parts: &mut Parts,
        state: &AppState,
    ) -> Result<Self, Self::Rejection> {
        let user = CurrentUser::from_request_parts(parts, state).await?;

        if !user.has_role(R::role()) {
            return Err(AppError::Forbidden(format!(
                "Role '{}' required",
                R::role()
            )));
        }

        Ok(RoleUser {
            user,
            _marker: PhantomData,
        })
    }
}

// Define role types
pub struct ManagerRole;
impl RequiredRole for ManagerRole {
    fn role() -> &'static str { "manager" }
}

pub struct ModeratorRole;
impl RequiredRole for ModeratorRole {
    fn role() -> &'static str { "moderator" }
}

// Usage: RoleUser<ManagerRole>
```

## API Key Extractor

```rust
// src/api/extractors/api_key.rs
use axum::{
    async_trait,
    extract::FromRequestParts,
    http::{header::HeaderName, request::Parts},
};

use crate::{error::AppError, startup::AppState};

static X_API_KEY: HeaderName = HeaderName::from_static("x-api-key");

#[derive(Debug, Clone)]
pub struct ApiKey {
    pub key: String,
    pub client_id: String,
    pub permissions: Vec<String>,
}

#[async_trait]
impl FromRequestParts<AppState> for ApiKey {
    type Rejection = AppError;

    async fn from_request_parts(
        parts: &mut Parts,
        state: &AppState,
    ) -> Result<Self, Self::Rejection> {
        // Extract API key from header
        let api_key = parts
            .headers
            .get(&X_API_KEY)
            .and_then(|v| v.to_str().ok())
            .ok_or_else(|| AppError::Unauthorized("Missing API key".into()))?;

        // Validate API key
        let key_data = state.api_key_repo
            .validate(api_key)
            .await
            .map_err(|_| AppError::Internal(anyhow::anyhow!("Database error")))?
            .ok_or_else(|| AppError::Unauthorized("Invalid API key".into()))?;

        if !key_data.is_active {
            return Err(AppError::Forbidden("API key is disabled".into()));
        }

        Ok(ApiKey {
            key: api_key.to_string(),
            client_id: key_data.client_id,
            permissions: key_data.permissions,
        })
    }
}

impl ApiKey {
    pub fn has_permission(&self, permission: &str) -> bool {
        self.permissions.contains(&permission.to_string())
            || self.permissions.contains(&"*".to_string())
    }
}
```

## Request ID Extractor

```rust
// src/api/extractors/request_id.rs
use axum::{
    async_trait,
    extract::FromRequestParts,
    http::{header::HeaderName, request::Parts},
};
use uuid::Uuid;

static X_REQUEST_ID: HeaderName = HeaderName::from_static("x-request-id");

#[derive(Debug, Clone)]
pub struct RequestId(pub String);

#[async_trait]
impl<S> FromRequestParts<S> for RequestId
where
    S: Send + Sync,
{
    type Rejection = std::convert::Infallible;

    async fn from_request_parts(
        parts: &mut Parts,
        _state: &S,
    ) -> Result<Self, Self::Rejection> {
        let request_id = parts
            .headers
            .get(&X_REQUEST_ID)
            .and_then(|v| v.to_str().ok())
            .map(String::from)
            .unwrap_or_else(|| Uuid::new_v4().to_string());

        // Store in extensions for other extractors
        parts.extensions.insert(RequestId(request_id.clone()));

        Ok(RequestId(request_id))
    }
}
```

## Client IP Extractor

```rust
// src/api/extractors/client_ip.rs
use axum::{
    async_trait,
    extract::{ConnectInfo, FromRequestParts},
    http::request::Parts,
};
use std::net::{IpAddr, SocketAddr};

#[derive(Debug, Clone)]
pub struct ClientIp(pub IpAddr);

#[async_trait]
impl<S> FromRequestParts<S> for ClientIp
where
    S: Send + Sync,
{
    type Rejection = std::convert::Infallible;

    async fn from_request_parts(
        parts: &mut Parts,
        _state: &S,
    ) -> Result<Self, Self::Rejection> {
        // Check X-Forwarded-For header (for proxied requests)
        if let Some(forwarded) = parts
            .headers
            .get("x-forwarded-for")
            .and_then(|v| v.to_str().ok())
        {
            // Get first IP (original client)
            if let Some(ip) = forwarded.split(',').next() {
                if let Ok(ip) = ip.trim().parse::<IpAddr>() {
                    return Ok(ClientIp(ip));
                }
            }
        }

        // Check X-Real-IP header
        if let Some(real_ip) = parts
            .headers
            .get("x-real-ip")
            .and_then(|v| v.to_str().ok())
        {
            if let Ok(ip) = real_ip.parse::<IpAddr>() {
                return Ok(ClientIp(ip));
            }
        }

        // Fall back to connection info
        if let Some(connect_info) = parts.extensions.get::<ConnectInfo<SocketAddr>>() {
            return Ok(ClientIp(connect_info.0.ip()));
        }

        // Default to localhost
        Ok(ClientIp(IpAddr::from([127, 0, 0, 1])))
    }
}
```

## Validated JSON Extractor

```rust
// src/api/extractors/validated_json.rs
use axum::{
    async_trait,
    extract::{rejection::JsonRejection, FromRequest, Request},
    Json,
};
use serde::de::DeserializeOwned;
use validator::Validate;

use crate::error::AppError;

/// JSON extractor with automatic validation
pub struct ValidatedJson<T>(pub T);

#[async_trait]
impl<S, T> FromRequest<S> for ValidatedJson<T>
where
    S: Send + Sync,
    T: DeserializeOwned + Validate,
{
    type Rejection = AppError;

    async fn from_request(req: Request, state: &S) -> Result<Self, Self::Rejection> {
        // Extract JSON
        let Json(value) = Json::<T>::from_request(req, state)
            .await
            .map_err(|e: JsonRejection| {
                AppError::BadRequest(format!("Invalid JSON: {}", e))
            })?;

        // Validate
        value.validate()
            .map_err(|e| AppError::Validation(e.to_string()))?;

        Ok(ValidatedJson(value))
    }
}

impl<T> std::ops::Deref for ValidatedJson<T> {
    type Target = T;

    fn deref(&self) -> &Self::Target {
        &self.0
    }
}
```

## Combined Extractors Usage

```rust
// src/api/handlers/product_handler.rs
use crate::api::extractors::{
    AdminUser, ClientIp, CurrentUser, MaybeUser, RequestId, ValidatedJson,
};

/// Public endpoint - optional authentication
pub async fn list_products(
    maybe_user: MaybeUser,
    Query(filter): Query<ProductFilter>,
) -> Result<Json<Vec<Product>>, AppError> {
    // Can customize response based on authentication
    let show_hidden = maybe_user.user().map(|u| u.is_admin).unwrap_or(false);
    // ...
}

/// Protected endpoint - requires authentication
pub async fn create_product(
    current_user: CurrentUser,
    request_id: RequestId,
    ValidatedJson(payload): ValidatedJson<CreateProductDto>,
) -> Result<(StatusCode, Json<Product>), AppError> {
    tracing::info!(
        request_id = %request_id.0,
        user_id = %current_user.id,
        "Creating product"
    );
    // ...
}

/// Admin only endpoint
pub async fn delete_all_products(
    admin: AdminUser,
    client_ip: ClientIp,
) -> Result<StatusCode, AppError> {
    tracing::warn!(
        admin_id = %admin.id,
        client_ip = %client_ip.0,
        "Deleting all products"
    );
    // ...
}

/// API key authenticated endpoint
pub async fn webhook(
    api_key: ApiKey,
    Json(payload): Json<WebhookPayload>,
) -> Result<StatusCode, AppError> {
    if !api_key.has_permission("webhooks:receive") {
        return Err(AppError::Forbidden("Insufficient permissions".into()));
    }
    // ...
}
```

## Best Practices

1. **Fail securely**: Return generic errors for authentication failures
2. **Validate early**: Use extractors for input validation
3. **Log security events**: Track authentication attempts
4. **Rate limit**: Combine with rate limiting middleware
5. **Use typed extractors**: Leverage type system for authorization
6. **Cache user lookups**: Consider caching for frequently accessed users
7. **Clear error messages**: Internal, not external
