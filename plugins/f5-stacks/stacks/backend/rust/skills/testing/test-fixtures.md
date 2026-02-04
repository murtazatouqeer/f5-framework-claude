---
name: rust-test-fixtures
description: Test fixtures and data generation for Rust
applies_to: rust
---

# Test Fixtures in Rust

## Overview

Test fixtures provide consistent, reusable test data.
They help create isolated, reproducible test environments.

## Fake Data Generation

```toml
# Cargo.toml
[dev-dependencies]
fake = { version = "2", features = ["derive", "chrono", "uuid"] }
rand = "0.8"
```

```rust
// tests/common/fake_data.rs
use fake::{
    faker::{
        internet::en::{FreeEmail, Password, Username},
        name::en::{FirstName, LastName, Name},
        lorem::en::{Sentence, Words},
        company::en::CompanyName,
        address::en::{StreetName, CityName, StateAbbr, ZipCode},
    },
    Fake,
};
use rust_decimal::Decimal;
use uuid::Uuid;

pub struct FakeUser {
    pub id: Uuid,
    pub email: String,
    pub password: String,
    pub name: String,
}

impl FakeUser {
    pub fn generate() -> Self {
        Self {
            id: Uuid::new_v4(),
            email: FreeEmail().fake(),
            password: Password(8..16).fake(),
            name: Name().fake(),
        }
    }
}

pub struct FakeProduct {
    pub id: Uuid,
    pub name: String,
    pub description: String,
    pub price: Decimal,
    pub stock: i32,
}

impl FakeProduct {
    pub fn generate() -> Self {
        let words: Vec<String> = Words(2..5).fake();
        Self {
            id: Uuid::new_v4(),
            name: words.join(" "),
            description: Sentence(5..15).fake(),
            price: Decimal::new(rand::random::<i64>() % 10000 + 100, 2),
            stock: rand::random::<i32>() % 1000,
        }
    }

    pub fn generate_many(count: usize) -> Vec<Self> {
        (0..count).map(|_| Self::generate()).collect()
    }
}

pub struct FakeAddress {
    pub street: String,
    pub city: String,
    pub state: String,
    pub zip: String,
}

impl FakeAddress {
    pub fn generate() -> Self {
        Self {
            street: StreetName().fake(),
            city: CityName().fake(),
            state: StateAbbr().fake(),
            zip: ZipCode().fake(),
        }
    }
}

// Derive Fake for custom structs
use fake::Dummy;

#[derive(Debug, Dummy)]
pub struct FakeOrder {
    #[dummy(faker = "fake::uuid::UUIDv4")]
    pub id: Uuid,
    #[dummy(faker = "1..100")]
    pub quantity: i32,
    #[dummy(faker = "100..10000")]
    pub total_cents: i64,
}
```

## Test Data Builder Pattern

```rust
// tests/common/builders.rs
use chrono::{DateTime, Utc};
use rust_decimal::Decimal;
use uuid::Uuid;

use myapp::domain::user::User;
use myapp::domain::product::Product;

/// Builder for User test data
pub struct UserBuilder {
    id: Uuid,
    email: String,
    password_hash: String,
    name: String,
    role: String,
    is_active: bool,
    created_at: DateTime<Utc>,
}

impl UserBuilder {
    pub fn new() -> Self {
        Self {
            id: Uuid::new_v4(),
            email: format!("user_{}@test.com", Uuid::new_v4()),
            password_hash: "$argon2id$...".to_string(),
            name: "Test User".to_string(),
            role: "user".to_string(),
            is_active: true,
            created_at: Utc::now(),
        }
    }

    pub fn id(mut self, id: Uuid) -> Self {
        self.id = id;
        self
    }

    pub fn email(mut self, email: &str) -> Self {
        self.email = email.to_string();
        self
    }

    pub fn name(mut self, name: &str) -> Self {
        self.name = name.to_string();
        self
    }

    pub fn role(mut self, role: &str) -> Self {
        self.role = role.to_string();
        self
    }

    pub fn admin(mut self) -> Self {
        self.role = "admin".to_string();
        self
    }

    pub fn inactive(mut self) -> Self {
        self.is_active = false;
        self
    }

    pub fn build(self) -> User {
        User {
            id: self.id,
            email: self.email,
            password_hash: self.password_hash,
            name: self.name,
            role: self.role,
            is_active: self.is_active,
            created_at: self.created_at,
            updated_at: self.created_at,
        }
    }
}

/// Builder for Product test data
pub struct ProductBuilder {
    id: Uuid,
    name: String,
    slug: String,
    description: Option<String>,
    price: Decimal,
    status: ProductStatus,
    category_id: Uuid,
    owner_id: Uuid,
    stock: i32,
}

impl ProductBuilder {
    pub fn new() -> Self {
        let id = Uuid::new_v4();
        Self {
            id,
            name: "Test Product".to_string(),
            slug: format!("test-product-{}", id),
            description: None,
            price: Decimal::new(9999, 2),
            status: ProductStatus::Active,
            category_id: Uuid::new_v4(),
            owner_id: Uuid::new_v4(),
            stock: 100,
        }
    }

    pub fn name(mut self, name: &str) -> Self {
        self.name = name.to_string();
        self.slug = slug::slugify(name);
        self
    }

    pub fn price(mut self, price: Decimal) -> Self {
        self.price = price;
        self
    }

    pub fn category(mut self, category_id: Uuid) -> Self {
        self.category_id = category_id;
        self
    }

    pub fn owner(mut self, owner_id: Uuid) -> Self {
        self.owner_id = owner_id;
        self
    }

    pub fn stock(mut self, stock: i32) -> Self {
        self.stock = stock;
        self
    }

    pub fn out_of_stock(mut self) -> Self {
        self.stock = 0;
        self
    }

    pub fn draft(mut self) -> Self {
        self.status = ProductStatus::Draft;
        self
    }

    pub fn build(self) -> Product {
        Product {
            id: self.id,
            name: self.name,
            slug: self.slug,
            description: self.description,
            price: self.price,
            compare_price: None,
            status: self.status,
            category_id: self.category_id,
            owner_id: self.owner_id,
            stock_quantity: self.stock,
            created_at: Utc::now(),
            updated_at: Utc::now(),
            deleted_at: None,
        }
    }
}

// Usage
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_with_builder() {
        let user = UserBuilder::new()
            .email("admin@test.com")
            .name("Admin User")
            .admin()
            .build();

        assert_eq!(user.role, "admin");
        assert_eq!(user.email, "admin@test.com");
    }
}
```

## Database Fixtures

```rust
// tests/common/fixtures.rs
use sqlx::PgPool;
use uuid::Uuid;

use crate::builders::{UserBuilder, ProductBuilder};

pub struct DatabaseFixtures {
    pool: PgPool,
}

impl DatabaseFixtures {
    pub fn new(pool: PgPool) -> Self {
        Self { pool }
    }

    /// Insert a user and return their ID
    pub async fn create_user(&self) -> Uuid {
        let user = UserBuilder::new().build();

        sqlx::query!(
            r#"
            INSERT INTO users (id, email, password_hash, name, role, is_active, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            "#,
            user.id,
            user.email,
            user.password_hash,
            user.name,
            user.role,
            user.is_active,
            user.created_at,
            user.updated_at,
        )
        .execute(&self.pool)
        .await
        .expect("Failed to create user");

        user.id
    }

    /// Insert an admin user
    pub async fn create_admin(&self) -> Uuid {
        let user = UserBuilder::new().admin().build();

        sqlx::query!(
            r#"
            INSERT INTO users (id, email, password_hash, name, role, is_active, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            "#,
            user.id,
            user.email,
            user.password_hash,
            user.name,
            user.role,
            user.is_active,
            user.created_at,
            user.updated_at,
        )
        .execute(&self.pool)
        .await
        .expect("Failed to create admin");

        user.id
    }

    /// Insert a category
    pub async fn create_category(&self, name: &str) -> Uuid {
        let id = Uuid::new_v4();
        let slug = slug::slugify(name);

        sqlx::query!(
            "INSERT INTO categories (id, name, slug) VALUES ($1, $2, $3)",
            id,
            name,
            slug
        )
        .execute(&self.pool)
        .await
        .expect("Failed to create category");

        id
    }

    /// Insert a product
    pub async fn create_product(&self, owner_id: Uuid, category_id: Uuid) -> Uuid {
        let product = ProductBuilder::new()
            .owner(owner_id)
            .category(category_id)
            .build();

        sqlx::query!(
            r#"
            INSERT INTO products (
                id, name, slug, description, price, status,
                category_id, owner_id, stock_quantity, created_at, updated_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            "#,
            product.id,
            product.name,
            product.slug,
            product.description,
            product.price,
            product.status as _,
            product.category_id,
            product.owner_id,
            product.stock_quantity,
            product.created_at,
            product.updated_at,
        )
        .execute(&self.pool)
        .await
        .expect("Failed to create product");

        product.id
    }

    /// Create a complete test scenario
    pub async fn create_scenario(&self) -> TestScenario {
        let admin_id = self.create_admin().await;
        let user_id = self.create_user().await;
        let category_id = self.create_category("Electronics").await;
        let product_id = self.create_product(user_id, category_id).await;

        TestScenario {
            admin_id,
            user_id,
            category_id,
            product_id,
        }
    }
}

pub struct TestScenario {
    pub admin_id: Uuid,
    pub user_id: Uuid,
    pub category_id: Uuid,
    pub product_id: Uuid,
}

// Usage
#[tokio::test]
async fn test_with_fixtures() {
    let app = spawn_app().await;
    let fixtures = DatabaseFixtures::new(app.pool.clone());

    let scenario = fixtures.create_scenario().await;

    // Test with the scenario data
    let response = app.get(&format!("/api/v1/products/{}", scenario.product_id)).await;
    assert_eq!(response.status(), 200);
}
```

## SQL Fixture Files

```sql
-- tests/fixtures/base.sql
-- Common data for all tests

-- Categories
INSERT INTO categories (id, name, slug, created_at, updated_at)
VALUES
    ('10000000-0000-0000-0000-000000000001', 'Electronics', 'electronics', NOW(), NOW()),
    ('10000000-0000-0000-0000-000000000002', 'Clothing', 'clothing', NOW(), NOW()),
    ('10000000-0000-0000-0000-000000000003', 'Books', 'books', NOW(), NOW());

-- Users
INSERT INTO users (id, email, password_hash, name, role, is_active, created_at, updated_at)
VALUES
    ('20000000-0000-0000-0000-000000000001', 'admin@test.com', '$argon2id$v=19$m=65536,t=3,p=4$...', 'Admin', 'admin', true, NOW(), NOW()),
    ('20000000-0000-0000-0000-000000000002', 'user@test.com', '$argon2id$v=19$m=65536,t=3,p=4$...', 'User', 'user', true, NOW(), NOW());
```

```sql
-- tests/fixtures/products.sql
-- Products for product-related tests

INSERT INTO products (id, name, slug, price, status, category_id, owner_id, stock_quantity, created_at, updated_at)
VALUES
    ('30000000-0000-0000-0000-000000000001', 'Laptop', 'laptop', 999.99, 'active', '10000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000002', 50, NOW(), NOW()),
    ('30000000-0000-0000-0000-000000000002', 'Phone', 'phone', 699.99, 'active', '10000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000002', 100, NOW(), NOW()),
    ('30000000-0000-0000-0000-000000000003', 'Draft Product', 'draft-product', 49.99, 'draft', '10000000-0000-0000-0000-000000000002', '20000000-0000-0000-0000-000000000002', 0, NOW(), NOW());
```

```rust
// Load fixtures in tests
use sqlx::Executor;

async fn load_fixtures(pool: &PgPool, fixtures: &[&str]) {
    for fixture in fixtures {
        let sql = std::fs::read_to_string(format!("tests/fixtures/{}.sql", fixture))
            .expect("Failed to read fixture file");

        pool.execute(sql.as_str())
            .await
            .expect("Failed to execute fixture");
    }
}

#[tokio::test]
async fn test_with_sql_fixtures() {
    let app = spawn_app().await;

    load_fixtures(&app.pool, &["base", "products"]).await;

    // Run tests with fixture data
    let response = app.get("/api/v1/products").await;
    let body: serde_json::Value = response.json().await.unwrap();

    assert_eq!(body["total"], 3);
}
```

## Fixture Traits

```rust
// tests/common/traits.rs
use async_trait::async_trait;
use sqlx::PgPool;
use uuid::Uuid;

#[async_trait]
pub trait TestData: Sized {
    async fn insert(&self, pool: &PgPool) -> Uuid;
    async fn insert_many(pool: &PgPool, count: usize) -> Vec<Uuid>;
}

#[async_trait]
impl TestData for UserBuilder {
    async fn insert(&self, pool: &PgPool) -> Uuid {
        let user = self.clone().build();
        // Insert logic...
        user.id
    }

    async fn insert_many(pool: &PgPool, count: usize) -> Vec<Uuid> {
        let mut ids = Vec::with_capacity(count);
        for _ in 0..count {
            let id = Self::new().insert(pool).await;
            ids.push(id);
        }
        ids
    }
}
```

## Best Practices

1. **Isolation**: Each test should start with a clean state
2. **Builders**: Use builder pattern for flexible test data
3. **Fake data**: Use fake crate for realistic random data
4. **SQL fixtures**: Use for complex initial states
5. **Cleanup**: Drop test databases or use transactions
6. **Determinism**: Avoid random data in assertions
7. **Reusability**: Create fixtures for common scenarios
