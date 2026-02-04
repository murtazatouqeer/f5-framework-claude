---
name: rust-unit-tests
description: Unit testing patterns for Rust
applies_to: rust
---

# Unit Testing in Rust

## Overview

Rust has built-in support for unit tests. Tests are placed in the same file
as the code they test, within a `#[cfg(test)]` module.

## Basic Test Structure

```rust
// src/domain/product/entity.rs

pub struct Product {
    id: Uuid,
    name: String,
    price: Decimal,
    stock: i32,
}

impl Product {
    pub fn new(name: String, price: Decimal) -> Result<Self, ProductError> {
        if name.trim().is_empty() {
            return Err(ProductError::InvalidName("Name cannot be empty".into()));
        }
        if price < Decimal::ZERO {
            return Err(ProductError::InvalidPrice("Price cannot be negative".into()));
        }

        Ok(Self {
            id: Uuid::new_v4(),
            name,
            price,
            stock: 0,
        })
    }

    pub fn adjust_stock(&mut self, delta: i32) -> Result<(), ProductError> {
        let new_stock = self.stock + delta;
        if new_stock < 0 {
            return Err(ProductError::InsufficientStock);
        }
        self.stock = new_stock;
        Ok(())
    }

    pub fn is_available(&self) -> bool {
        self.stock > 0
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use rust_decimal_macros::dec;

    #[test]
    fn test_create_product_success() {
        let product = Product::new("Test Product".to_string(), dec!(99.99));

        assert!(product.is_ok());
        let product = product.unwrap();
        assert_eq!(product.name, "Test Product");
        assert_eq!(product.price, dec!(99.99));
        assert_eq!(product.stock, 0);
    }

    #[test]
    fn test_create_product_empty_name_fails() {
        let product = Product::new("".to_string(), dec!(99.99));

        assert!(product.is_err());
        assert!(matches!(product, Err(ProductError::InvalidName(_))));
    }

    #[test]
    fn test_create_product_negative_price_fails() {
        let product = Product::new("Test".to_string(), dec!(-10.00));

        assert!(product.is_err());
        assert!(matches!(product, Err(ProductError::InvalidPrice(_))));
    }

    #[test]
    fn test_adjust_stock_increase() {
        let mut product = Product::new("Test".to_string(), dec!(10.00)).unwrap();

        let result = product.adjust_stock(10);

        assert!(result.is_ok());
        assert_eq!(product.stock, 10);
    }

    #[test]
    fn test_adjust_stock_decrease() {
        let mut product = Product::new("Test".to_string(), dec!(10.00)).unwrap();
        product.adjust_stock(10).unwrap();

        let result = product.adjust_stock(-5);

        assert!(result.is_ok());
        assert_eq!(product.stock, 5);
    }

    #[test]
    fn test_adjust_stock_insufficient() {
        let mut product = Product::new("Test".to_string(), dec!(10.00)).unwrap();

        let result = product.adjust_stock(-5);

        assert!(result.is_err());
        assert!(matches!(result, Err(ProductError::InsufficientStock)));
    }

    #[test]
    fn test_is_available() {
        let mut product = Product::new("Test".to_string(), dec!(10.00)).unwrap();

        assert!(!product.is_available());

        product.adjust_stock(5).unwrap();
        assert!(product.is_available());

        product.adjust_stock(-5).unwrap();
        assert!(!product.is_available());
    }
}
```

## Test Organization

```rust
#[cfg(test)]
mod tests {
    use super::*;

    // Group related tests in submodules
    mod creation {
        use super::*;

        #[test]
        fn test_valid_creation() { /* ... */ }

        #[test]
        fn test_invalid_name() { /* ... */ }

        #[test]
        fn test_invalid_price() { /* ... */ }
    }

    mod stock_management {
        use super::*;

        #[test]
        fn test_increase_stock() { /* ... */ }

        #[test]
        fn test_decrease_stock() { /* ... */ }

        #[test]
        fn test_insufficient_stock() { /* ... */ }
    }

    mod business_rules {
        use super::*;

        #[test]
        fn test_availability() { /* ... */ }

        #[test]
        fn test_pricing_rules() { /* ... */ }
    }
}
```

## Test Helpers and Fixtures

```rust
#[cfg(test)]
mod tests {
    use super::*;

    // Test fixtures
    fn create_test_product() -> Product {
        Product::new("Test Product".to_string(), dec!(99.99)).unwrap()
    }

    fn create_product_with_stock(stock: i32) -> Product {
        let mut product = create_test_product();
        product.adjust_stock(stock).unwrap();
        product
    }

    // Builder for complex test data
    struct TestProductBuilder {
        name: String,
        price: Decimal,
        stock: i32,
    }

    impl TestProductBuilder {
        fn new() -> Self {
            Self {
                name: "Default Product".to_string(),
                price: dec!(10.00),
                stock: 0,
            }
        }

        fn with_name(mut self, name: &str) -> Self {
            self.name = name.to_string();
            self
        }

        fn with_price(mut self, price: Decimal) -> Self {
            self.price = price;
            self
        }

        fn with_stock(mut self, stock: i32) -> Self {
            self.stock = stock;
            self
        }

        fn build(self) -> Product {
            let mut product = Product::new(self.name, self.price).unwrap();
            if self.stock > 0 {
                product.adjust_stock(self.stock).unwrap();
            }
            product
        }
    }

    #[test]
    fn test_with_builder() {
        let product = TestProductBuilder::new()
            .with_name("Custom Product")
            .with_price(dec!(49.99))
            .with_stock(100)
            .build();

        assert_eq!(product.name, "Custom Product");
        assert_eq!(product.stock, 100);
    }
}
```

## Testing Async Code

```rust
// src/application/product/service.rs
use tokio;

impl ProductService {
    pub async fn get_product(&self, id: Uuid) -> Result<Product, ServiceError> {
        self.repository.find_by_id(id).await
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_get_product_success() {
        let mock_repo = MockProductRepository::new();
        let service = ProductService::new(Arc::new(mock_repo));

        let result = service.get_product(Uuid::new_v4()).await;

        assert!(result.is_ok());
    }

    #[tokio::test]
    async fn test_get_product_not_found() {
        let mock_repo = MockProductRepository::returning_none();
        let service = ProductService::new(Arc::new(mock_repo));

        let result = service.get_product(Uuid::new_v4()).await;

        assert!(matches!(result, Err(ServiceError::NotFound)));
    }
}
```

## Mocking with mockall

```rust
// Cargo.toml
// [dev-dependencies]
// mockall = "0.11"

use async_trait::async_trait;
use mockall::{automock, predicate::*};

#[async_trait]
#[automock]
pub trait ProductRepository: Send + Sync {
    async fn find_by_id(&self, id: Uuid) -> Result<Option<Product>, RepositoryError>;
    async fn save(&self, product: &Product) -> Result<(), RepositoryError>;
    async fn delete(&self, id: Uuid) -> Result<(), RepositoryError>;
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_service_with_mock() {
        let mut mock_repo = MockProductRepository::new();

        // Set up expectations
        mock_repo
            .expect_find_by_id()
            .with(eq(test_id))
            .times(1)
            .returning(|_| Ok(Some(create_test_product())));

        let service = ProductService::new(Arc::new(mock_repo));
        let result = service.get_product(test_id).await;

        assert!(result.is_ok());
    }

    #[tokio::test]
    async fn test_save_product() {
        let mut mock_repo = MockProductRepository::new();

        mock_repo
            .expect_save()
            .times(1)
            .returning(|_| Ok(()));

        let service = ProductService::new(Arc::new(mock_repo));
        let product = create_test_product();

        let result = service.create_product(product).await;

        assert!(result.is_ok());
    }
}
```

## Property-Based Testing

```rust
// Cargo.toml
// [dev-dependencies]
// proptest = "1"

use proptest::prelude::*;

proptest! {
    #[test]
    fn test_product_name_not_empty(name in "[a-zA-Z0-9 ]{1,100}") {
        let product = Product::new(name, dec!(10.00));
        assert!(product.is_ok());
    }

    #[test]
    fn test_stock_never_negative(
        initial in 0i32..1000,
        delta in -1000i32..1000
    ) {
        let mut product = create_test_product();
        product.adjust_stock(initial).unwrap();

        let result = product.adjust_stock(delta);

        if initial + delta >= 0 {
            assert!(result.is_ok());
            assert_eq!(product.stock, initial + delta);
        } else {
            assert!(result.is_err());
            assert_eq!(product.stock, initial); // Stock unchanged
        }
    }

    #[test]
    fn test_price_always_positive(price in 0.01f64..10000.0) {
        let decimal_price = Decimal::from_f64_retain(price).unwrap();
        let product = Product::new("Test".to_string(), decimal_price);

        assert!(product.is_ok());
        assert!(product.unwrap().price > Decimal::ZERO);
    }
}
```

## Test Utilities

```rust
// tests/common/mod.rs
use std::sync::Once;

static INIT: Once = Once::new();

pub fn setup() {
    INIT.call_once(|| {
        // One-time setup code
        env_logger::init();
    });
}

// Macro for creating test products
#[macro_export]
macro_rules! test_product {
    ($name:expr, $price:expr) => {
        Product::new($name.to_string(), rust_decimal_macros::dec!($price)).unwrap()
    };
    ($name:expr, $price:expr, $stock:expr) => {{
        let mut p = Product::new($name.to_string(), rust_decimal_macros::dec!($price)).unwrap();
        p.adjust_stock($stock).unwrap();
        p
    }};
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_with_macro() {
        let product = test_product!("Test", 99.99, 10);
        assert_eq!(product.stock, 10);
    }
}
```

## Testing Error Conditions

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_error_message() {
        let result = Product::new("".to_string(), dec!(10.00));

        let err = result.unwrap_err();
        assert_eq!(err.to_string(), "Invalid name: Name cannot be empty");
    }

    #[test]
    #[should_panic(expected = "assertion failed")]
    fn test_panic_condition() {
        // Test that code panics as expected
        panic!("assertion failed");
    }

    #[test]
    fn test_error_chain() {
        let result: Result<(), ServiceError> = Err(ServiceError::Repository(
            RepositoryError::NotFound,
        ));

        assert!(matches!(
            result,
            Err(ServiceError::Repository(RepositoryError::NotFound))
        ));
    }
}
```

## Running Tests

```bash
# Run all tests
cargo test

# Run tests with output
cargo test -- --nocapture

# Run specific test
cargo test test_create_product_success

# Run tests in specific module
cargo test domain::product

# Run tests with specific threads
cargo test -- --test-threads=1

# Run only ignored tests
cargo test -- --ignored

# Run tests and show which ones ran
cargo test -- --show-output
```

## Best Practices

1. **Test behavior, not implementation**: Focus on what, not how
2. **One assertion per test**: Makes failures easier to diagnose
3. **Descriptive test names**: `test_create_product_with_empty_name_fails`
4. **Use fixtures**: Create reusable test data
5. **Mock external dependencies**: Isolate unit under test
6. **Test edge cases**: Boundaries, empty inputs, invalid states
7. **Keep tests fast**: Unit tests should run in milliseconds
