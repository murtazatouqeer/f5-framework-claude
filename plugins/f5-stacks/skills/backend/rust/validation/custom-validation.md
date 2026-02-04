---
name: rust-custom-validation
description: Custom validation patterns and domain validation
applies_to: rust
---

# Custom Validation Patterns

## Domain Validation

```rust
// src/domain/common/validation.rs
use thiserror::Error;

#[derive(Debug, Error)]
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

pub type ValidationResult<T> = Result<T, Vec<ValidationError>>;
```

## Value Objects with Validation

```rust
// src/domain/common/value_objects.rs
use once_cell::sync::Lazy;
use regex::Regex;
use serde::{Deserialize, Serialize};
use std::fmt;

/// Email address value object
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(try_from = "String")]
pub struct Email(String);

impl Email {
    pub fn new(value: &str) -> Result<Self, ValidationError> {
        let value = value.trim().to_lowercase();

        static EMAIL_REGEX: Lazy<Regex> = Lazy::new(|| {
            Regex::new(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$").unwrap()
        });

        if !EMAIL_REGEX.is_match(&value) {
            return Err(ValidationError::InvalidFormat {
                field: "email".to_string(),
                message: "Invalid email format".to_string(),
            });
        }

        Ok(Self(value))
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }

    pub fn domain(&self) -> &str {
        self.0.split('@').nth(1).unwrap_or("")
    }
}

impl TryFrom<String> for Email {
    type Error = ValidationError;

    fn try_from(value: String) -> Result<Self, Self::Error> {
        Self::new(&value)
    }
}

impl fmt::Display for Email {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.0)
    }
}

/// Phone number value object
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(try_from = "String")]
pub struct PhoneNumber(String);

impl PhoneNumber {
    pub fn new(value: &str) -> Result<Self, ValidationError> {
        // Remove all non-digit characters
        let digits: String = value.chars().filter(|c| c.is_ascii_digit()).collect();

        if digits.len() < 10 || digits.len() > 15 {
            return Err(ValidationError::InvalidFormat {
                field: "phone".to_string(),
                message: "Phone number must have 10-15 digits".to_string(),
            });
        }

        Ok(Self(digits))
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }

    pub fn formatted(&self) -> String {
        if self.0.len() == 10 {
            format!(
                "({}) {}-{}",
                &self.0[0..3],
                &self.0[3..6],
                &self.0[6..10]
            )
        } else {
            self.0.clone()
        }
    }
}

impl TryFrom<String> for PhoneNumber {
    type Error = ValidationError;

    fn try_from(value: String) -> Result<Self, Self::Error> {
        Self::new(&value)
    }
}

/// Money value object
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Money {
    amount: rust_decimal::Decimal,
    currency: Currency,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Currency {
    USD,
    EUR,
    GBP,
    JPY,
}

impl Money {
    pub fn new(amount: rust_decimal::Decimal, currency: Currency) -> Result<Self, ValidationError> {
        if amount < rust_decimal::Decimal::ZERO {
            return Err(ValidationError::BusinessRule(
                "Amount cannot be negative".to_string(),
            ));
        }

        // Check decimal places based on currency
        let max_scale = match currency {
            Currency::JPY => 0,
            _ => 2,
        };

        if amount.scale() > max_scale {
            return Err(ValidationError::InvalidFormat {
                field: "amount".to_string(),
                message: format!("Too many decimal places for {:?}", currency),
            });
        }

        Ok(Self { amount, currency })
    }

    pub fn amount(&self) -> rust_decimal::Decimal {
        self.amount
    }

    pub fn currency(&self) -> Currency {
        self.currency
    }

    pub fn add(&self, other: &Money) -> Result<Money, ValidationError> {
        if self.currency != other.currency {
            return Err(ValidationError::BusinessRule(
                "Cannot add different currencies".to_string(),
            ));
        }

        Money::new(self.amount + other.amount, self.currency)
    }
}

/// Slug value object
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(try_from = "String")]
pub struct Slug(String);

impl Slug {
    pub fn new(value: &str) -> Result<Self, ValidationError> {
        static SLUG_REGEX: Lazy<Regex> = Lazy::new(|| {
            Regex::new(r"^[a-z0-9]+(?:-[a-z0-9]+)*$").unwrap()
        });

        let value = value.trim().to_lowercase();

        if value.is_empty() || value.len() > 200 {
            return Err(ValidationError::OutOfRange {
                field: "slug".to_string(),
                min: "1".to_string(),
                max: "200".to_string(),
            });
        }

        if !SLUG_REGEX.is_match(&value) {
            return Err(ValidationError::InvalidFormat {
                field: "slug".to_string(),
                message: "Slug must contain only lowercase letters, numbers, and hyphens".to_string(),
            });
        }

        Ok(Self(value))
    }

    pub fn from_string(value: &str) -> Self {
        Self(slug::slugify(value))
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }
}

impl TryFrom<String> for Slug {
    type Error = ValidationError;

    fn try_from(value: String) -> Result<Self, Self::Error> {
        Self::new(&value)
    }
}
```

## Entity Validation

```rust
// src/domain/product/entity.rs
use crate::domain::common::{Money, Slug, ValidationError};

#[derive(Debug)]
pub struct Product {
    id: ProductId,
    name: String,
    slug: Slug,
    price: Money,
    stock: i32,
    // ...
}

impl Product {
    pub fn new(
        name: String,
        price: Money,
        initial_stock: i32,
    ) -> Result<Self, Vec<ValidationError>> {
        let mut errors = Vec::new();

        // Validate name
        if name.trim().is_empty() {
            errors.push(ValidationError::MissingField("name".to_string()));
        } else if name.len() > 200 {
            errors.push(ValidationError::OutOfRange {
                field: "name".to_string(),
                min: "1".to_string(),
                max: "200".to_string(),
            });
        }

        // Validate stock
        if initial_stock < 0 {
            errors.push(ValidationError::InvalidField {
                field: "stock".to_string(),
                message: "Stock cannot be negative".to_string(),
            });
        }

        if !errors.is_empty() {
            return Err(errors);
        }

        let slug = Slug::from_string(&name);

        Ok(Self {
            id: ProductId::new(),
            name,
            slug,
            price,
            stock: initial_stock,
        })
    }

    /// Update stock with business rule validation
    pub fn adjust_stock(&mut self, delta: i32) -> Result<(), ValidationError> {
        let new_stock = self.stock + delta;

        if new_stock < 0 {
            return Err(ValidationError::BusinessRule(
                "Cannot reduce stock below zero".to_string(),
            ));
        }

        self.stock = new_stock;
        Ok(())
    }

    /// Set price with validation
    pub fn set_price(&mut self, new_price: Money) -> Result<(), ValidationError> {
        if new_price.currency() != self.price.currency() {
            return Err(ValidationError::BusinessRule(
                "Cannot change product currency".to_string(),
            ));
        }

        self.price = new_price;
        Ok(())
    }
}
```

## Aggregate Validation

```rust
// src/domain/order/entity.rs
use crate::domain::common::{Money, ValidationError};

pub struct Order {
    id: OrderId,
    customer_id: CustomerId,
    items: Vec<OrderItem>,
    status: OrderStatus,
    total: Money,
}

impl Order {
    pub fn new(
        customer_id: CustomerId,
        items: Vec<OrderItem>,
    ) -> Result<Self, Vec<ValidationError>> {
        let mut errors = Vec::new();

        // Validate items
        if items.is_empty() {
            errors.push(ValidationError::BusinessRule(
                "Order must have at least one item".to_string(),
            ));
        }

        // Validate each item
        for (i, item) in items.iter().enumerate() {
            if let Err(item_errors) = item.validate() {
                for err in item_errors {
                    errors.push(ValidationError::InvalidField {
                        field: format!("items[{}]", i),
                        message: err.to_string(),
                    });
                }
            }
        }

        // Check for duplicate products
        let product_ids: Vec<_> = items.iter().map(|i| i.product_id).collect();
        let unique_ids: std::collections::HashSet<_> = product_ids.iter().collect();
        if unique_ids.len() != product_ids.len() {
            errors.push(ValidationError::BusinessRule(
                "Order cannot contain duplicate products".to_string(),
            ));
        }

        if !errors.is_empty() {
            return Err(errors);
        }

        // Calculate total
        let total = items.iter()
            .try_fold(Money::zero(Currency::USD), |acc, item| {
                acc.add(&item.subtotal())
            })
            .map_err(|e| vec![e])?;

        Ok(Self {
            id: OrderId::new(),
            customer_id,
            items,
            status: OrderStatus::Pending,
            total,
        })
    }

    /// Add item with validation
    pub fn add_item(&mut self, item: OrderItem) -> Result<(), ValidationError> {
        if self.status != OrderStatus::Pending {
            return Err(ValidationError::BusinessRule(
                "Cannot modify non-pending order".to_string(),
            ));
        }

        // Check for duplicate
        if self.items.iter().any(|i| i.product_id == item.product_id) {
            return Err(ValidationError::BusinessRule(
                "Product already in order".to_string(),
            ));
        }

        // Validate max items
        if self.items.len() >= 100 {
            return Err(ValidationError::BusinessRule(
                "Order cannot have more than 100 items".to_string(),
            ));
        }

        self.total = self.total.add(&item.subtotal())?;
        self.items.push(item);

        Ok(())
    }
}

pub struct OrderItem {
    product_id: ProductId,
    product_name: String,
    quantity: i32,
    unit_price: Money,
}

impl OrderItem {
    pub fn new(
        product_id: ProductId,
        product_name: String,
        quantity: i32,
        unit_price: Money,
    ) -> Result<Self, Vec<ValidationError>> {
        let mut errors = Vec::new();

        if quantity < 1 {
            errors.push(ValidationError::OutOfRange {
                field: "quantity".to_string(),
                min: "1".to_string(),
                max: "1000".to_string(),
            });
        }

        if quantity > 1000 {
            errors.push(ValidationError::OutOfRange {
                field: "quantity".to_string(),
                min: "1".to_string(),
                max: "1000".to_string(),
            });
        }

        if !errors.is_empty() {
            return Err(errors);
        }

        Ok(Self {
            product_id,
            product_name,
            quantity,
            unit_price,
        })
    }

    pub fn validate(&self) -> Result<(), Vec<ValidationError>> {
        let mut errors = Vec::new();

        if self.quantity < 1 || self.quantity > 1000 {
            errors.push(ValidationError::OutOfRange {
                field: "quantity".to_string(),
                min: "1".to_string(),
                max: "1000".to_string(),
            });
        }

        if errors.is_empty() {
            Ok(())
        } else {
            Err(errors)
        }
    }

    pub fn subtotal(&self) -> Money {
        Money::new(
            self.unit_price.amount() * rust_decimal::Decimal::from(self.quantity),
            self.unit_price.currency(),
        ).unwrap()
    }
}
```

## Validation Builder Pattern

```rust
// src/domain/common/validator.rs
pub struct Validator {
    errors: Vec<ValidationError>,
}

impl Validator {
    pub fn new() -> Self {
        Self { errors: Vec::new() }
    }

    pub fn required<T>(mut self, field: &str, value: &Option<T>) -> Self {
        if value.is_none() {
            self.errors.push(ValidationError::MissingField(field.to_string()));
        }
        self
    }

    pub fn not_empty(mut self, field: &str, value: &str) -> Self {
        if value.trim().is_empty() {
            self.errors.push(ValidationError::InvalidField {
                field: field.to_string(),
                message: "Cannot be empty".to_string(),
            });
        }
        self
    }

    pub fn length(mut self, field: &str, value: &str, min: usize, max: usize) -> Self {
        let len = value.len();
        if len < min || len > max {
            self.errors.push(ValidationError::OutOfRange {
                field: field.to_string(),
                min: min.to_string(),
                max: max.to_string(),
            });
        }
        self
    }

    pub fn range<T: PartialOrd + std::fmt::Display>(
        mut self,
        field: &str,
        value: T,
        min: T,
        max: T,
    ) -> Self {
        if value < min || value > max {
            self.errors.push(ValidationError::OutOfRange {
                field: field.to_string(),
                min: min.to_string(),
                max: max.to_string(),
            });
        }
        self
    }

    pub fn custom<F>(mut self, f: F) -> Self
    where
        F: FnOnce() -> Option<ValidationError>,
    {
        if let Some(error) = f() {
            self.errors.push(error);
        }
        self
    }

    pub fn finish(self) -> Result<(), Vec<ValidationError>> {
        if self.errors.is_empty() {
            Ok(())
        } else {
            Err(self.errors)
        }
    }
}

// Usage
impl Product {
    pub fn validate_update(&self, dto: &UpdateProductDto) -> Result<(), Vec<ValidationError>> {
        Validator::new()
            .not_empty("name", dto.name.as_deref().unwrap_or("placeholder"))
            .length("name", dto.name.as_deref().unwrap_or(""), 2, 200)
            .custom(|| {
                if let Some(ref price) = dto.price {
                    if *price < rust_decimal::Decimal::ZERO {
                        return Some(ValidationError::InvalidField {
                            field: "price".to_string(),
                            message: "Price cannot be negative".to_string(),
                        });
                    }
                }
                None
            })
            .finish()
    }
}
```

## Best Practices

1. **Validate at boundaries**: Validate input at API/service boundaries
2. **Use value objects**: Encapsulate validation in domain types
3. **Collect all errors**: Return all validation errors, not just the first
4. **Domain-specific rules**: Encode business rules in domain entities
5. **Immutable validation**: Value objects should be immutable after creation
6. **Clear error messages**: Provide actionable error messages
7. **Test edge cases**: Test boundary conditions and invalid inputs
