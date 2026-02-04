---
name: rust-jwt-auth
description: JWT authentication patterns for Rust
applies_to: rust
---

# JWT Authentication in Rust

## Overview

JSON Web Tokens (JWT) provide stateless authentication for APIs.
The `jsonwebtoken` crate is the standard choice for Rust.

## Dependencies

```toml
[dependencies]
jsonwebtoken = "9"
serde = { version = "1", features = ["derive"] }
chrono = { version = "0.4", features = ["serde"] }
uuid = { version = "1", features = ["v4", "serde"] }
```

## JWT Claims Structure

```rust
// src/domain/auth/claims.rs
use chrono::{DateTime, Duration, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// Access token claims
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AccessTokenClaims {
    /// Subject (user ID)
    pub sub: Uuid,
    /// User email
    pub email: String,
    /// User role
    pub role: String,
    /// Is admin flag
    pub is_admin: bool,
    /// Issued at (Unix timestamp)
    pub iat: i64,
    /// Expiration time (Unix timestamp)
    pub exp: i64,
    /// Not before (Unix timestamp)
    pub nbf: i64,
    /// JWT ID (unique identifier for this token)
    pub jti: String,
    /// Issuer
    pub iss: String,
    /// Audience
    pub aud: Vec<String>,
}

impl AccessTokenClaims {
    pub fn new(
        user_id: Uuid,
        email: String,
        role: String,
        is_admin: bool,
        expiration_hours: i64,
        issuer: &str,
        audience: &[&str],
    ) -> Self {
        let now = Utc::now();
        let exp = now + Duration::hours(expiration_hours);

        Self {
            sub: user_id,
            email,
            role,
            is_admin,
            iat: now.timestamp(),
            exp: exp.timestamp(),
            nbf: now.timestamp(),
            jti: Uuid::new_v4().to_string(),
            iss: issuer.to_string(),
            aud: audience.iter().map(|s| s.to_string()).collect(),
        }
    }

    pub fn is_expired(&self) -> bool {
        Utc::now().timestamp() >= self.exp
    }
}

/// Refresh token claims
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RefreshTokenClaims {
    pub sub: Uuid,
    pub jti: String,
    pub iat: i64,
    pub exp: i64,
    pub iss: String,
}

impl RefreshTokenClaims {
    pub fn new(
        user_id: Uuid,
        expiration_days: i64,
        issuer: &str,
    ) -> Self {
        let now = Utc::now();
        let exp = now + Duration::days(expiration_days);

        Self {
            sub: user_id,
            jti: Uuid::new_v4().to_string(),
            iat: now.timestamp(),
            exp: exp.timestamp(),
            iss: issuer.to_string(),
        }
    }
}
```

## JWT Service

```rust
// src/application/auth/jwt_service.rs
use jsonwebtoken::{
    decode, encode, errors::Error as JwtError, Algorithm, DecodingKey, EncodingKey, Header,
    TokenData, Validation,
};
use uuid::Uuid;

use crate::{
    config::JwtConfig,
    domain::auth::claims::{AccessTokenClaims, RefreshTokenClaims},
};

pub struct JwtService {
    config: JwtConfig,
    encoding_key: EncodingKey,
    decoding_key: DecodingKey,
}

impl JwtService {
    pub fn new(config: JwtConfig) -> Self {
        let encoding_key = EncodingKey::from_secret(config.secret.as_bytes());
        let decoding_key = DecodingKey::from_secret(config.secret.as_bytes());

        Self {
            config,
            encoding_key,
            decoding_key,
        }
    }

    /// Generate access token
    pub fn generate_access_token(
        &self,
        user_id: Uuid,
        email: &str,
        role: &str,
        is_admin: bool,
    ) -> Result<String, JwtError> {
        let claims = AccessTokenClaims::new(
            user_id,
            email.to_string(),
            role.to_string(),
            is_admin,
            self.config.access_token_expiration_hours,
            &self.config.issuer,
            &self.config.audience.iter().map(|s| s.as_str()).collect::<Vec<_>>(),
        );

        encode(&Header::default(), &claims, &self.encoding_key)
    }

    /// Generate refresh token
    pub fn generate_refresh_token(&self, user_id: Uuid) -> Result<String, JwtError> {
        let claims = RefreshTokenClaims::new(
            user_id,
            self.config.refresh_token_expiration_days,
            &self.config.issuer,
        );

        encode(&Header::default(), &claims, &self.encoding_key)
    }

    /// Verify and decode access token
    pub fn verify_access_token(&self, token: &str) -> Result<TokenData<AccessTokenClaims>, JwtError> {
        let mut validation = Validation::new(Algorithm::HS256);
        validation.set_issuer(&[&self.config.issuer]);
        validation.set_audience(&self.config.audience);
        validation.validate_exp = true;
        validation.validate_nbf = true;

        decode::<AccessTokenClaims>(token, &self.decoding_key, &validation)
    }

    /// Verify and decode refresh token
    pub fn verify_refresh_token(&self, token: &str) -> Result<TokenData<RefreshTokenClaims>, JwtError> {
        let mut validation = Validation::new(Algorithm::HS256);
        validation.set_issuer(&[&self.config.issuer]);
        validation.validate_exp = true;

        decode::<RefreshTokenClaims>(token, &self.decoding_key, &validation)
    }

    /// Generate token pair
    pub fn generate_token_pair(
        &self,
        user_id: Uuid,
        email: &str,
        role: &str,
        is_admin: bool,
    ) -> Result<TokenPair, JwtError> {
        let access_token = self.generate_access_token(user_id, email, role, is_admin)?;
        let refresh_token = self.generate_refresh_token(user_id)?;

        Ok(TokenPair {
            access_token,
            refresh_token,
            token_type: "Bearer".to_string(),
            expires_in: self.config.access_token_expiration_hours * 3600,
        })
    }
}

#[derive(Debug, Serialize)]
pub struct TokenPair {
    pub access_token: String,
    pub refresh_token: String,
    pub token_type: String,
    pub expires_in: i64,
}
```

## Configuration

```rust
// src/config.rs
#[derive(Debug, Deserialize, Clone)]
pub struct JwtConfig {
    pub secret: String,
    pub issuer: String,
    pub audience: Vec<String>,
    pub access_token_expiration_hours: i64,
    pub refresh_token_expiration_days: i64,
}

impl Default for JwtConfig {
    fn default() -> Self {
        Self {
            secret: "change-this-secret-in-production".to_string(),
            issuer: "myapp".to_string(),
            audience: vec!["myapp".to_string()],
            access_token_expiration_hours: 1,
            refresh_token_expiration_days: 30,
        }
    }
}
```

## Auth Handlers

```rust
// src/api/handlers/auth_handler.rs
use axum::{extract::State, http::StatusCode, Json};
use serde::{Deserialize, Serialize};
use validator::Validate;

use crate::{
    application::auth::{AuthService, TokenPair},
    error::{AppError, Result},
    startup::AppState,
};

#[derive(Debug, Deserialize, Validate)]
pub struct LoginRequest {
    #[validate(email(message = "Invalid email format"))]
    pub email: String,
    #[validate(length(min = 8, message = "Password must be at least 8 characters"))]
    pub password: String,
}

#[derive(Debug, Deserialize, Validate)]
pub struct RegisterRequest {
    #[validate(email(message = "Invalid email format"))]
    pub email: String,
    #[validate(length(min = 8, message = "Password must be at least 8 characters"))]
    pub password: String,
    #[validate(length(min = 2, max = 100, message = "Name must be 2-100 characters"))]
    pub name: String,
}

#[derive(Debug, Deserialize)]
pub struct RefreshRequest {
    pub refresh_token: String,
}

#[derive(Debug, Serialize)]
pub struct AuthResponse {
    pub user: UserResponse,
    pub tokens: TokenPair,
}

/// Login handler
pub async fn login(
    State(state): State<AppState>,
    Json(payload): Json<LoginRequest>,
) -> Result<Json<AuthResponse>> {
    payload.validate()
        .map_err(|e| AppError::Validation(e.to_string()))?;

    let (user, tokens) = state.auth_service
        .login(&payload.email, &payload.password)
        .await?;

    Ok(Json(AuthResponse {
        user: user.into(),
        tokens,
    }))
}

/// Register handler
pub async fn register(
    State(state): State<AppState>,
    Json(payload): Json<RegisterRequest>,
) -> Result<(StatusCode, Json<AuthResponse>)> {
    payload.validate()
        .map_err(|e| AppError::Validation(e.to_string()))?;

    let (user, tokens) = state.auth_service
        .register(&payload.email, &payload.password, &payload.name)
        .await?;

    Ok((StatusCode::CREATED, Json(AuthResponse {
        user: user.into(),
        tokens,
    })))
}

/// Refresh token handler
pub async fn refresh_token(
    State(state): State<AppState>,
    Json(payload): Json<RefreshRequest>,
) -> Result<Json<TokenPair>> {
    let tokens = state.auth_service
        .refresh_tokens(&payload.refresh_token)
        .await?;

    Ok(Json(tokens))
}

/// Logout handler (invalidate refresh token)
pub async fn logout(
    State(state): State<AppState>,
    current_user: CurrentUser,
    Json(payload): Json<RefreshRequest>,
) -> Result<StatusCode> {
    state.auth_service
        .logout(current_user.id, &payload.refresh_token)
        .await?;

    Ok(StatusCode::NO_CONTENT)
}
```

## Auth Service

```rust
// src/application/auth/service.rs
use std::sync::Arc;
use uuid::Uuid;

use crate::{
    application::auth::{JwtService, TokenPair},
    domain::user::{User, UserRepository},
    error::{AppError, Result},
};

pub struct AuthService {
    jwt_service: Arc<JwtService>,
    user_repo: Arc<dyn UserRepository>,
    password_hasher: Arc<dyn PasswordHasher>,
    refresh_token_repo: Arc<dyn RefreshTokenRepository>,
}

impl AuthService {
    pub fn new(
        jwt_service: Arc<JwtService>,
        user_repo: Arc<dyn UserRepository>,
        password_hasher: Arc<dyn PasswordHasher>,
        refresh_token_repo: Arc<dyn RefreshTokenRepository>,
    ) -> Self {
        Self {
            jwt_service,
            user_repo,
            password_hasher,
            refresh_token_repo,
        }
    }

    pub async fn login(&self, email: &str, password: &str) -> Result<(User, TokenPair)> {
        // Find user by email
        let user = self.user_repo
            .get_by_email(email)
            .await?
            .ok_or_else(|| AppError::Unauthorized("Invalid credentials".into()))?;

        // Verify password
        if !self.password_hasher.verify(password, &user.password_hash)? {
            return Err(AppError::Unauthorized("Invalid credentials".into()));
        }

        // Check if user is active
        if !user.is_active {
            return Err(AppError::Forbidden("Account is disabled".into()));
        }

        // Generate tokens
        let tokens = self.jwt_service.generate_token_pair(
            user.id,
            &user.email,
            &user.role,
            user.is_admin(),
        )?;

        // Store refresh token
        self.refresh_token_repo
            .store(user.id, &tokens.refresh_token)
            .await?;

        Ok((user, tokens))
    }

    pub async fn register(
        &self,
        email: &str,
        password: &str,
        name: &str,
    ) -> Result<(User, TokenPair)> {
        // Check if email already exists
        if self.user_repo.get_by_email(email).await?.is_some() {
            return Err(AppError::Conflict("Email already registered".into()));
        }

        // Hash password
        let password_hash = self.password_hasher.hash(password)?;

        // Create user
        let user = User::new(email.to_string(), password_hash, name.to_string());
        let user = self.user_repo.create(&user).await?;

        // Generate tokens
        let tokens = self.jwt_service.generate_token_pair(
            user.id,
            &user.email,
            &user.role,
            user.is_admin(),
        )?;

        // Store refresh token
        self.refresh_token_repo
            .store(user.id, &tokens.refresh_token)
            .await?;

        Ok((user, tokens))
    }

    pub async fn refresh_tokens(&self, refresh_token: &str) -> Result<TokenPair> {
        // Verify refresh token
        let claims = self.jwt_service
            .verify_refresh_token(refresh_token)
            .map_err(|_| AppError::Unauthorized("Invalid refresh token".into()))?
            .claims;

        // Check if refresh token is valid in database
        let is_valid = self.refresh_token_repo
            .is_valid(claims.sub, refresh_token)
            .await?;

        if !is_valid {
            return Err(AppError::Unauthorized("Refresh token revoked".into()));
        }

        // Get user
        let user = self.user_repo
            .get_by_id(claims.sub)
            .await?
            .ok_or_else(|| AppError::Unauthorized("User not found".into()))?;

        // Revoke old refresh token
        self.refresh_token_repo
            .revoke(claims.sub, refresh_token)
            .await?;

        // Generate new tokens
        let tokens = self.jwt_service.generate_token_pair(
            user.id,
            &user.email,
            &user.role,
            user.is_admin(),
        )?;

        // Store new refresh token
        self.refresh_token_repo
            .store(user.id, &tokens.refresh_token)
            .await?;

        Ok(tokens)
    }

    pub async fn logout(&self, user_id: Uuid, refresh_token: &str) -> Result<()> {
        self.refresh_token_repo
            .revoke(user_id, refresh_token)
            .await?;
        Ok(())
    }
}
```

## Refresh Token Storage

```rust
// src/domain/auth/refresh_token_repository.rs
use async_trait::async_trait;
use uuid::Uuid;

#[async_trait]
pub trait RefreshTokenRepository: Send + Sync {
    async fn store(&self, user_id: Uuid, token: &str) -> Result<(), RepositoryError>;
    async fn is_valid(&self, user_id: Uuid, token: &str) -> Result<bool, RepositoryError>;
    async fn revoke(&self, user_id: Uuid, token: &str) -> Result<(), RepositoryError>;
    async fn revoke_all(&self, user_id: Uuid) -> Result<(), RepositoryError>;
}

// src/infrastructure/repositories/redis_refresh_token_repo.rs
use async_trait::async_trait;
use redis::AsyncCommands;
use uuid::Uuid;

pub struct RedisRefreshTokenRepository {
    client: redis::Client,
    ttl_days: i64,
}

#[async_trait]
impl RefreshTokenRepository for RedisRefreshTokenRepository {
    async fn store(&self, user_id: Uuid, token: &str) -> Result<(), RepositoryError> {
        let mut conn = self.client.get_async_connection().await?;
        let key = format!("refresh_token:{}:{}", user_id, token);
        let ttl = self.ttl_days * 24 * 60 * 60;

        conn.set_ex(&key, "valid", ttl as u64).await?;
        Ok(())
    }

    async fn is_valid(&self, user_id: Uuid, token: &str) -> Result<bool, RepositoryError> {
        let mut conn = self.client.get_async_connection().await?;
        let key = format!("refresh_token:{}:{}", user_id, token);

        let exists: bool = conn.exists(&key).await?;
        Ok(exists)
    }

    async fn revoke(&self, user_id: Uuid, token: &str) -> Result<(), RepositoryError> {
        let mut conn = self.client.get_async_connection().await?;
        let key = format!("refresh_token:{}:{}", user_id, token);

        conn.del(&key).await?;
        Ok(())
    }

    async fn revoke_all(&self, user_id: Uuid) -> Result<(), RepositoryError> {
        let mut conn = self.client.get_async_connection().await?;
        let pattern = format!("refresh_token:{}:*", user_id);

        let keys: Vec<String> = conn.keys(&pattern).await?;
        if !keys.is_empty() {
            conn.del(keys).await?;
        }
        Ok(())
    }
}
```

## Best Practices

1. **Short-lived access tokens**: 15-60 minutes
2. **Long-lived refresh tokens**: 7-30 days
3. **Store refresh tokens**: Use database or Redis
4. **Revoke on logout**: Invalidate refresh tokens
5. **Rotate refresh tokens**: Issue new one on use
6. **Use secure secrets**: Strong, random secrets in production
7. **Validate claims**: Check issuer, audience, expiration
8. **HTTPS only**: Never transmit tokens over HTTP
