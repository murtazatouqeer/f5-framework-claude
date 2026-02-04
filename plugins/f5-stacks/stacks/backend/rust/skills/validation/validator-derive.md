---
name: rust-validator-derive
description: Input validation with validator derive macros
applies_to: rust
---

# Validator Derive Patterns

## Overview

The `validator` crate provides derive macros for declarative input validation.
It integrates well with serde for JSON deserialization.

## Dependencies

```toml
[dependencies]
validator = { version = "0.16", features = ["derive"] }
serde = { version = "1", features = ["derive"] }
```

## Basic Validation

```rust
// src/application/user/dto.rs
use serde::{Deserialize, Serialize};
use validator::Validate;

#[derive(Debug, Deserialize, Validate)]
pub struct CreateUserDto {
    #[validate(email(message = "Invalid email format"))]
    pub email: String,

    #[validate(length(min = 8, max = 128, message = "Password must be 8-128 characters"))]
    pub password: String,

    #[validate(length(min = 2, max = 100, message = "Name must be 2-100 characters"))]
    pub name: String,

    #[validate(phone(message = "Invalid phone number"))]
    #[serde(default)]
    pub phone: Option<String>,
}

#[derive(Debug, Deserialize, Validate)]
pub struct UpdateUserDto {
    #[validate(length(min = 2, max = 100, message = "Name must be 2-100 characters"))]
    pub name: Option<String>,

    #[validate(phone(message = "Invalid phone number"))]
    pub phone: Option<String>,

    #[validate(url(message = "Invalid avatar URL"))]
    pub avatar_url: Option<String>,
}
```

## Available Validators

```rust
use validator::Validate;

#[derive(Debug, Validate)]
pub struct AllValidators {
    // Length validation
    #[validate(length(min = 1, max = 100))]
    pub text: String,

    #[validate(length(equal = 10))]
    pub fixed_length: String,

    // Email validation
    #[validate(email)]
    pub email: String,

    // URL validation
    #[validate(url)]
    pub website: String,

    // Phone validation
    #[validate(phone)]
    pub phone: String,

    // Range validation (numbers)
    #[validate(range(min = 0, max = 100))]
    pub percentage: i32,

    #[validate(range(min = 0.0, max = 1.0))]
    pub ratio: f64,

    // Regex validation
    #[validate(regex(path = "SLUG_REGEX"))]
    pub slug: String,

    // Must match another field
    #[validate(must_match(other = "password"))]
    pub password_confirmation: String,

    // Credit card
    #[validate(credit_card)]
    pub card_number: String,

    // Contains/Does not contain
    #[validate(contains(pattern = "keyword"))]
    pub must_contain: String,

    #[validate(does_not_contain(pattern = "banned"))]
    pub clean_text: String,

    // Required (for Option types)
    #[validate(required)]
    pub required_field: Option<String>,

    // Nested validation
    #[validate(nested)]
    pub address: Address,

    // Custom validation
    #[validate(custom(function = "validate_username"))]
    pub username: String,
}

// Regex patterns
use once_cell::sync::Lazy;
use regex::Regex;

static SLUG_REGEX: Lazy<Regex> = Lazy::new(|| {
    Regex::new(r"^[a-z0-9]+(?:-[a-z0-9]+)*$").unwrap()
});
```

## Nested Validation

```rust
#[derive(Debug, Deserialize, Validate)]
pub struct CreateOrderDto {
    #[validate(nested)]
    pub shipping_address: AddressDto,

    #[validate(nested)]
    pub billing_address: Option<AddressDto>,

    #[validate(length(min = 1, message = "Order must have at least one item"))]
    #[validate(nested)]
    pub items: Vec<OrderItemDto>,
}

#[derive(Debug, Deserialize, Validate)]
pub struct AddressDto {
    #[validate(length(min = 2, max = 100))]
    pub street: String,

    #[validate(length(min = 2, max = 50))]
    pub city: String,

    #[validate(length(min = 2, max = 50))]
    pub state: String,

    #[validate(length(min = 5, max = 10))]
    pub postal_code: String,

    #[validate(length(equal = 2))]
    pub country_code: String,
}

#[derive(Debug, Deserialize, Validate)]
pub struct OrderItemDto {
    pub product_id: Uuid,

    #[validate(range(min = 1, max = 100, message = "Quantity must be 1-100"))]
    pub quantity: i32,
}
```

## Custom Validators

```rust
use validator::{Validate, ValidationError};

#[derive(Debug, Deserialize, Validate)]
pub struct CreateProductDto {
    #[validate(length(min = 2, max = 200))]
    pub name: String,

    #[validate(custom(function = "validate_price"))]
    pub price: rust_decimal::Decimal,

    #[validate(custom(function = "validate_sku"))]
    pub sku: Option<String>,

    #[validate(custom(function = "validate_future_date"))]
    pub launch_date: Option<chrono::NaiveDate>,
}

/// Price must be positive and have at most 2 decimal places
fn validate_price(price: &rust_decimal::Decimal) -> Result<(), ValidationError> {
    use rust_decimal::Decimal;

    if *price < Decimal::ZERO {
        return Err(ValidationError::new("price_negative")
            .with_message("Price must be non-negative".into()));
    }

    if price.scale() > 2 {
        return Err(ValidationError::new("price_precision")
            .with_message("Price can have at most 2 decimal places".into()));
    }

    Ok(())
}

/// SKU format: ABC-12345
fn validate_sku(sku: &Option<String>) -> Result<(), ValidationError> {
    if let Some(sku) = sku {
        let sku_regex = regex::Regex::new(r"^[A-Z]{3}-\d{5}$").unwrap();
        if !sku_regex.is_match(sku) {
            return Err(ValidationError::new("invalid_sku")
                .with_message("SKU must be in format ABC-12345".into()));
        }
    }
    Ok(())
}

/// Date must be in the future
fn validate_future_date(date: &Option<chrono::NaiveDate>) -> Result<(), ValidationError> {
    if let Some(date) = date {
        let today = chrono::Utc::now().date_naive();
        if *date <= today {
            return Err(ValidationError::new("date_not_future")
                .with_message("Date must be in the future".into()));
        }
    }
    Ok(())
}
```

## Conditional Validation

```rust
use validator::{Validate, ValidationError, ValidationErrors};

#[derive(Debug, Deserialize)]
pub struct PaymentDto {
    pub method: PaymentMethod,
    pub card_number: Option<String>,
    pub card_expiry: Option<String>,
    pub card_cvv: Option<String>,
    pub bank_account: Option<String>,
    pub routing_number: Option<String>,
}

#[derive(Debug, Deserialize, PartialEq)]
#[serde(rename_all = "snake_case")]
pub enum PaymentMethod {
    CreditCard,
    BankTransfer,
    Cash,
}

impl Validate for PaymentDto {
    fn validate(&self) -> Result<(), ValidationErrors> {
        let mut errors = ValidationErrors::new();

        match self.method {
            PaymentMethod::CreditCard => {
                if self.card_number.is_none() {
                    errors.add("card_number", ValidationError::new("required"));
                }
                if self.card_expiry.is_none() {
                    errors.add("card_expiry", ValidationError::new("required"));
                }
                if self.card_cvv.is_none() {
                    errors.add("card_cvv", ValidationError::new("required"));
                }

                // Validate card number format
                if let Some(ref card) = self.card_number {
                    if card.len() < 13 || card.len() > 19 {
                        errors.add("card_number",
                            ValidationError::new("length")
                                .with_message("Card number must be 13-19 digits".into()));
                    }
                }
            }
            PaymentMethod::BankTransfer => {
                if self.bank_account.is_none() {
                    errors.add("bank_account", ValidationError::new("required"));
                }
                if self.routing_number.is_none() {
                    errors.add("routing_number", ValidationError::new("required"));
                }
            }
            PaymentMethod::Cash => {
                // No additional validation needed
            }
        }

        if errors.is_empty() {
            Ok(())
        } else {
            Err(errors)
        }
    }
}
```

## Error Handling

```rust
// src/api/validation.rs
use axum::{
    http::StatusCode,
    response::{IntoResponse, Response},
    Json,
};
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
            .flat_map(|(field, errs)| {
                errs.iter().map(move |e| FieldError {
                    field: field.to_string(),
                    message: e.message
                        .clone()
                        .map(|m| m.to_string())
                        .unwrap_or_else(|| format!("Validation failed: {}", e.code)),
                    code: e.code.to_string(),
                })
            })
            .collect();

        let messages: Vec<String> = field_errors
            .iter()
            .map(|e| format!("{}: {}", e.field, e.message))
            .collect();

        AppError::Validation(messages.join("; "))
    }
}
```

## Handler Usage

```rust
// src/api/handlers/user_handler.rs
use axum::{extract::State, http::StatusCode, Json};
use validator::Validate;

use crate::{
    application::user::CreateUserDto,
    error::{AppError, Result},
    startup::AppState,
};

pub async fn create_user(
    State(state): State<AppState>,
    Json(payload): Json<CreateUserDto>,
) -> Result<(StatusCode, Json<UserResponse>)> {
    // Validate input
    payload.validate()?;

    // Process valid input
    let user = state.user_service.create(payload).await?;

    Ok((StatusCode::CREATED, Json(user.into())))
}

// Or use ValidatedJson extractor
use crate::api::extractors::ValidatedJson;

pub async fn create_user_v2(
    State(state): State<AppState>,
    ValidatedJson(payload): ValidatedJson<CreateUserDto>,
) -> Result<(StatusCode, Json<UserResponse>)> {
    // Validation already done by extractor
    let user = state.user_service.create(payload).await?;

    Ok((StatusCode::CREATED, Json(user.into())))
}
```

## Testing Validation

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use validator::Validate;

    #[test]
    fn test_valid_create_user_dto() {
        let dto = CreateUserDto {
            email: "test@example.com".to_string(),
            password: "password123".to_string(),
            name: "John Doe".to_string(),
            phone: None,
        };

        assert!(dto.validate().is_ok());
    }

    #[test]
    fn test_invalid_email() {
        let dto = CreateUserDto {
            email: "not-an-email".to_string(),
            password: "password123".to_string(),
            name: "John Doe".to_string(),
            phone: None,
        };

        let result = dto.validate();
        assert!(result.is_err());

        let errors = result.unwrap_err();
        assert!(errors.field_errors().contains_key("email"));
    }

    #[test]
    fn test_password_too_short() {
        let dto = CreateUserDto {
            email: "test@example.com".to_string(),
            password: "short".to_string(),
            name: "John Doe".to_string(),
            phone: None,
        };

        let result = dto.validate();
        assert!(result.is_err());

        let errors = result.unwrap_err();
        assert!(errors.field_errors().contains_key("password"));
    }
}
```

## Best Practices

1. **Validate early**: Validate at the API boundary
2. **Clear messages**: Provide helpful error messages
3. **Nested validation**: Use `#[validate(nested)]` for complex structures
4. **Custom validators**: Create reusable validation functions
5. **Test validation**: Write unit tests for validation rules
6. **Conditional logic**: Implement `Validate` trait manually when needed
7. **Field-level errors**: Return specific field errors to clients
