---
name: rust-argon2-passwords
description: Password hashing with Argon2 in Rust
applies_to: rust
---

# Password Hashing with Argon2

## Overview

Argon2 is the winner of the Password Hashing Competition and is recommended
for password hashing. The `argon2` crate provides a safe implementation.

## Dependencies

```toml
[dependencies]
argon2 = "0.5"
password-hash = "0.5"
rand_core = { version = "0.6", features = ["std"] }
```

## Password Hasher Trait

```rust
// src/domain/auth/password.rs
use crate::error::Result;

pub trait PasswordHasher: Send + Sync {
    /// Hash a plaintext password
    fn hash(&self, password: &str) -> Result<String>;

    /// Verify a password against a hash
    fn verify(&self, password: &str, hash: &str) -> Result<bool>;
}
```

## Argon2 Implementation

```rust
// src/infrastructure/security/argon2_hasher.rs
use argon2::{
    password_hash::{rand_core::OsRng, PasswordHash, PasswordHasher as ArgonHasher, PasswordVerifier, SaltString},
    Algorithm, Argon2, Params, Version,
};

use crate::{
    domain::auth::password::PasswordHasher,
    error::{AppError, Result},
};

pub struct Argon2PasswordHasher {
    argon2: Argon2<'static>,
}

impl Argon2PasswordHasher {
    /// Create with default parameters (recommended for most cases)
    pub fn new() -> Self {
        Self {
            argon2: Argon2::default(),
        }
    }

    /// Create with custom parameters
    pub fn with_params(
        memory_cost: u32,
        time_cost: u32,
        parallelism: u32,
    ) -> Result<Self> {
        let params = Params::new(memory_cost, time_cost, parallelism, None)
            .map_err(|e| AppError::Internal(anyhow::anyhow!("Invalid Argon2 params: {}", e)))?;

        let argon2 = Argon2::new(Algorithm::Argon2id, Version::V0x13, params);

        Ok(Self { argon2 })
    }

    /// Create with high security parameters (for sensitive applications)
    pub fn high_security() -> Result<Self> {
        Self::with_params(
            65536,  // 64 MiB memory
            4,      // 4 iterations
            4,      // 4 parallelism
        )
    }
}

impl Default for Argon2PasswordHasher {
    fn default() -> Self {
        Self::new()
    }
}

impl PasswordHasher for Argon2PasswordHasher {
    fn hash(&self, password: &str) -> Result<String> {
        let salt = SaltString::generate(&mut OsRng);

        let hash = self.argon2
            .hash_password(password.as_bytes(), &salt)
            .map_err(|e| AppError::Internal(anyhow::anyhow!("Failed to hash password: {}", e)))?;

        Ok(hash.to_string())
    }

    fn verify(&self, password: &str, hash: &str) -> Result<bool> {
        let parsed_hash = PasswordHash::new(hash)
            .map_err(|e| AppError::Internal(anyhow::anyhow!("Invalid password hash format: {}", e)))?;

        Ok(self.argon2
            .verify_password(password.as_bytes(), &parsed_hash)
            .is_ok())
    }
}
```

## Password Policy

```rust
// src/domain/auth/password_policy.rs
use serde::Deserialize;
use validator::Validate;

#[derive(Debug, Clone, Deserialize)]
pub struct PasswordPolicy {
    pub min_length: usize,
    pub max_length: usize,
    pub require_uppercase: bool,
    pub require_lowercase: bool,
    pub require_digit: bool,
    pub require_special: bool,
    pub special_characters: String,
}

impl Default for PasswordPolicy {
    fn default() -> Self {
        Self {
            min_length: 8,
            max_length: 128,
            require_uppercase: true,
            require_lowercase: true,
            require_digit: true,
            require_special: false,
            special_characters: "!@#$%^&*()_+-=[]{}|;:,.<>?".to_string(),
        }
    }
}

impl PasswordPolicy {
    pub fn validate_password(&self, password: &str) -> Result<(), Vec<String>> {
        let mut errors = Vec::new();

        if password.len() < self.min_length {
            errors.push(format!(
                "Password must be at least {} characters",
                self.min_length
            ));
        }

        if password.len() > self.max_length {
            errors.push(format!(
                "Password must be at most {} characters",
                self.max_length
            ));
        }

        if self.require_uppercase && !password.chars().any(|c| c.is_uppercase()) {
            errors.push("Password must contain at least one uppercase letter".to_string());
        }

        if self.require_lowercase && !password.chars().any(|c| c.is_lowercase()) {
            errors.push("Password must contain at least one lowercase letter".to_string());
        }

        if self.require_digit && !password.chars().any(|c| c.is_ascii_digit()) {
            errors.push("Password must contain at least one digit".to_string());
        }

        if self.require_special {
            let has_special = password
                .chars()
                .any(|c| self.special_characters.contains(c));
            if !has_special {
                errors.push(format!(
                    "Password must contain at least one special character: {}",
                    self.special_characters
                ));
            }
        }

        if errors.is_empty() {
            Ok(())
        } else {
            Err(errors)
        }
    }
}

/// Custom validator for use with `validator` crate
pub fn validate_password_strength(password: &str) -> Result<(), validator::ValidationError> {
    let policy = PasswordPolicy::default();

    if let Err(errors) = policy.validate_password(password) {
        let mut error = validator::ValidationError::new("password_policy");
        error.message = Some(errors.join("; ").into());
        return Err(error);
    }

    Ok(())
}
```

## Password Service

```rust
// src/application/auth/password_service.rs
use std::sync::Arc;
use uuid::Uuid;

use crate::{
    domain::auth::{
        password::PasswordHasher,
        password_policy::PasswordPolicy,
    },
    domain::user::UserRepository,
    error::{AppError, Result},
};

pub struct PasswordService {
    hasher: Arc<dyn PasswordHasher>,
    policy: PasswordPolicy,
    user_repo: Arc<dyn UserRepository>,
}

impl PasswordService {
    pub fn new(
        hasher: Arc<dyn PasswordHasher>,
        policy: PasswordPolicy,
        user_repo: Arc<dyn UserRepository>,
    ) -> Self {
        Self {
            hasher,
            policy,
            user_repo,
        }
    }

    /// Change user password
    pub async fn change_password(
        &self,
        user_id: Uuid,
        current_password: &str,
        new_password: &str,
    ) -> Result<()> {
        // Get user
        let user = self.user_repo
            .get_by_id(user_id)
            .await?
            .ok_or_else(|| AppError::NotFound("User not found".into()))?;

        // Verify current password
        if !self.hasher.verify(current_password, &user.password_hash)? {
            return Err(AppError::BadRequest("Current password is incorrect".into()));
        }

        // Check if new password is same as current
        if self.hasher.verify(new_password, &user.password_hash)? {
            return Err(AppError::BadRequest(
                "New password must be different from current password".into()
            ));
        }

        // Validate new password against policy
        self.policy
            .validate_password(new_password)
            .map_err(|errors| AppError::Validation(errors.join("; ")))?;

        // Hash new password
        let new_hash = self.hasher.hash(new_password)?;

        // Update password
        self.user_repo.update_password(user_id, &new_hash).await?;

        Ok(())
    }

    /// Reset password with token
    pub async fn reset_password(
        &self,
        reset_token: &str,
        new_password: &str,
    ) -> Result<()> {
        // Validate token and get user
        let user_id = self.validate_reset_token(reset_token).await?;

        // Validate new password against policy
        self.policy
            .validate_password(new_password)
            .map_err(|errors| AppError::Validation(errors.join("; ")))?;

        // Hash new password
        let new_hash = self.hasher.hash(new_password)?;

        // Update password
        self.user_repo.update_password(user_id, &new_hash).await?;

        // Invalidate reset token
        self.invalidate_reset_token(reset_token).await?;

        Ok(())
    }

    async fn validate_reset_token(&self, _token: &str) -> Result<Uuid> {
        // Implementation for token validation
        todo!()
    }

    async fn invalidate_reset_token(&self, _token: &str) -> Result<()> {
        // Implementation for token invalidation
        todo!()
    }
}
```

## Password Reset Flow

```rust
// src/application/auth/password_reset_service.rs
use chrono::{Duration, Utc};
use uuid::Uuid;

pub struct PasswordResetService {
    user_repo: Arc<dyn UserRepository>,
    reset_token_repo: Arc<dyn ResetTokenRepository>,
    email_service: Arc<dyn EmailService>,
}

impl PasswordResetService {
    /// Request password reset
    pub async fn request_reset(&self, email: &str) -> Result<()> {
        // Find user (don't reveal if email exists)
        let user = match self.user_repo.get_by_email(email).await? {
            Some(user) => user,
            None => {
                // Don't reveal that email doesn't exist
                tracing::warn!("Password reset requested for unknown email: {}", email);
                return Ok(());
            }
        };

        // Generate reset token
        let token = Uuid::new_v4().to_string();
        let expires_at = Utc::now() + Duration::hours(1);

        // Store token
        self.reset_token_repo
            .store(user.id, &token, expires_at)
            .await?;

        // Send email
        self.email_service
            .send_password_reset(&user.email, &user.name, &token)
            .await?;

        Ok(())
    }

    /// Validate reset token
    pub async fn validate_token(&self, token: &str) -> Result<bool> {
        let reset_token = self.reset_token_repo.get(token).await?;

        match reset_token {
            Some(rt) => Ok(rt.expires_at > Utc::now()),
            None => Ok(false),
        }
    }
}
```

## Testing

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_hash_and_verify() {
        let hasher = Argon2PasswordHasher::new();
        let password = "secure_password_123";

        let hash = hasher.hash(password).unwrap();

        assert!(hasher.verify(password, &hash).unwrap());
        assert!(!hasher.verify("wrong_password", &hash).unwrap());
    }

    #[test]
    fn test_different_hashes_for_same_password() {
        let hasher = Argon2PasswordHasher::new();
        let password = "secure_password_123";

        let hash1 = hasher.hash(password).unwrap();
        let hash2 = hasher.hash(password).unwrap();

        // Same password should produce different hashes (due to salt)
        assert_ne!(hash1, hash2);

        // But both should verify correctly
        assert!(hasher.verify(password, &hash1).unwrap());
        assert!(hasher.verify(password, &hash2).unwrap());
    }

    #[test]
    fn test_password_policy() {
        let policy = PasswordPolicy::default();

        // Valid password
        assert!(policy.validate_password("Passw0rd!").is_ok());

        // Too short
        assert!(policy.validate_password("Pass1").is_err());

        // No uppercase
        assert!(policy.validate_password("password123").is_err());

        // No lowercase
        assert!(policy.validate_password("PASSWORD123").is_err());

        // No digit
        assert!(policy.validate_password("Password!").is_err());
    }
}
```

## Best Practices

1. **Use Argon2id**: The hybrid variant resistant to both side-channel and GPU attacks
2. **Default parameters**: Use library defaults unless you have specific requirements
3. **Salt handling**: Let the library handle salt generation
4. **Timing attacks**: Use constant-time comparison (handled by library)
5. **Password policy**: Enforce minimum complexity requirements
6. **Rate limiting**: Limit login attempts to prevent brute force
7. **Secure storage**: Store hashes, never plaintext passwords
8. **Memory clearing**: Clear password from memory after use (Rust handles this)
