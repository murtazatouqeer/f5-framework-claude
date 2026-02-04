---
name: rust-integration-tests
description: Integration testing patterns for Rust web APIs
applies_to: rust
---

# Integration Testing in Rust

## Overview

Integration tests verify that multiple components work together correctly.
In Rust, integration tests are placed in the `tests/` directory.

## Test Project Structure

```
project/
├── src/
│   └── ...
├── tests/
│   ├── common/
│   │   └── mod.rs         # Shared test utilities
│   ├── api/
│   │   ├── mod.rs
│   │   ├── health_test.rs
│   │   ├── user_test.rs
│   │   └── product_test.rs
│   └── integration_test.rs # Main test file
└── Cargo.toml
```

## Test Application Setup

```rust
// tests/common/mod.rs
use once_cell::sync::Lazy;
use sqlx::{PgPool, postgres::PgPoolOptions};
use std::net::SocketAddr;
use uuid::Uuid;

use myapp::{
    config::Config,
    startup::Application,
};

static TRACING: Lazy<()> = Lazy::new(|| {
    if std::env::var("TEST_LOG").is_ok() {
        tracing_subscriber::fmt()
            .with_max_level(tracing::Level::DEBUG)
            .init();
    }
});

pub struct TestApp {
    pub address: String,
    pub port: u16,
    pub pool: PgPool,
    pub client: reqwest::Client,
    pub test_user: TestUser,
}

pub struct TestUser {
    pub id: Uuid,
    pub email: String,
    pub token: String,
}

impl TestApp {
    /// Make authenticated request
    pub fn auth_header(&self) -> (&'static str, String) {
        ("Authorization", format!("Bearer {}", self.test_user.token))
    }

    /// GET request
    pub async fn get(&self, path: &str) -> reqwest::Response {
        self.client
            .get(format!("{}{}", self.address, path))
            .send()
            .await
            .expect("Failed to execute request")
    }

    /// GET request with auth
    pub async fn get_auth(&self, path: &str) -> reqwest::Response {
        let (key, value) = self.auth_header();
        self.client
            .get(format!("{}{}", self.address, path))
            .header(key, value)
            .send()
            .await
            .expect("Failed to execute request")
    }

    /// POST request with JSON body
    pub async fn post<T: serde::Serialize>(&self, path: &str, body: &T) -> reqwest::Response {
        self.client
            .post(format!("{}{}", self.address, path))
            .json(body)
            .send()
            .await
            .expect("Failed to execute request")
    }

    /// POST request with auth
    pub async fn post_auth<T: serde::Serialize>(&self, path: &str, body: &T) -> reqwest::Response {
        let (key, value) = self.auth_header();
        self.client
            .post(format!("{}{}", self.address, path))
            .header(key, value)
            .json(body)
            .send()
            .await
            .expect("Failed to execute request")
    }

    /// PUT request with auth
    pub async fn put_auth<T: serde::Serialize>(&self, path: &str, body: &T) -> reqwest::Response {
        let (key, value) = self.auth_header();
        self.client
            .put(format!("{}{}", self.address, path))
            .header(key, value)
            .json(body)
            .send()
            .await
            .expect("Failed to execute request")
    }

    /// DELETE request with auth
    pub async fn delete_auth(&self, path: &str) -> reqwest::Response {
        let (key, value) = self.auth_header();
        self.client
            .delete(format!("{}{}", self.address, path))
            .header(key, value)
            .send()
            .await
            .expect("Failed to execute request")
    }
}

pub async fn spawn_app() -> TestApp {
    Lazy::force(&TRACING);

    // Create test database
    let db_name = format!("test_{}", Uuid::new_v4().to_string().replace("-", ""));
    let db_url = create_test_database(&db_name).await;

    // Load config with test database
    let mut config = Config::load().expect("Failed to load config");
    config.database.url = db_url;

    // Create database pool
    let pool = PgPoolOptions::new()
        .max_connections(5)
        .connect(&config.database.url)
        .await
        .expect("Failed to connect to database");

    // Run migrations
    sqlx::migrate!("./migrations")
        .run(&pool)
        .await
        .expect("Failed to run migrations");

    // Build application
    let app = Application::build(&config)
        .await
        .expect("Failed to build app");

    // Bind to random port
    let listener = tokio::net::TcpListener::bind("127.0.0.1:0")
        .await
        .expect("Failed to bind");
    let port = listener.local_addr().unwrap().port();
    let address = format!("http://127.0.0.1:{}", port);

    // Spawn server
    tokio::spawn(async move {
        axum::serve(listener, app.router()).await.unwrap();
    });

    // Create HTTP client
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(30))
        .build()
        .expect("Failed to build client");

    // Create test user
    let test_user = create_test_user(&pool, &config).await;

    TestApp {
        address,
        port,
        pool,
        client,
        test_user,
    }
}

async fn create_test_database(db_name: &str) -> String {
    let base_url = std::env::var("DATABASE_URL")
        .unwrap_or_else(|_| "postgres://postgres:postgres@localhost".to_string());

    // Connect to postgres database
    let pool = PgPool::connect(&format!("{}/postgres", base_url))
        .await
        .expect("Failed to connect to postgres");

    // Create test database
    sqlx::query(&format!("CREATE DATABASE {}", db_name))
        .execute(&pool)
        .await
        .expect("Failed to create test database");

    format!("{}/{}", base_url, db_name)
}

async fn create_test_user(pool: &PgPool, config: &Config) -> TestUser {
    let user_id = Uuid::new_v4();
    let email = format!("test_{}@example.com", Uuid::new_v4());
    let password_hash = hash_password("password123");

    sqlx::query!(
        r#"
        INSERT INTO users (id, email, password_hash, name, role, is_active)
        VALUES ($1, $2, $3, 'Test User', 'user', true)
        "#,
        user_id,
        email,
        password_hash,
    )
    .execute(pool)
    .await
    .expect("Failed to create test user");

    // Generate token
    let token = generate_test_token(user_id, &email, config);

    TestUser {
        id: user_id,
        email,
        token,
    }
}
```

## API Tests

```rust
// tests/api/health_test.rs
use crate::common::spawn_app;

#[tokio::test]
async fn test_health_check() {
    let app = spawn_app().await;

    let response = app.get("/health").await;

    assert_eq!(response.status(), 200);

    let body: serde_json::Value = response.json().await.unwrap();
    assert_eq!(body["status"], "healthy");
}

#[tokio::test]
async fn test_readiness_check() {
    let app = spawn_app().await;

    let response = app.get("/health/ready").await;

    assert_eq!(response.status(), 200);

    let body: serde_json::Value = response.json().await.unwrap();
    assert_eq!(body["status"], "ready");
    assert_eq!(body["database"], "connected");
}
```

```rust
// tests/api/user_test.rs
use crate::common::spawn_app;
use serde_json::json;

#[tokio::test]
async fn test_get_current_user() {
    let app = spawn_app().await;

    let response = app.get_auth("/api/v1/users/me").await;

    assert_eq!(response.status(), 200);

    let body: serde_json::Value = response.json().await.unwrap();
    assert_eq!(body["email"], app.test_user.email);
}

#[tokio::test]
async fn test_get_user_unauthorized() {
    let app = spawn_app().await;

    let response = app.get("/api/v1/users/me").await;

    assert_eq!(response.status(), 401);
}

#[tokio::test]
async fn test_register_user() {
    let app = spawn_app().await;

    let payload = json!({
        "email": "new@example.com",
        "password": "password123",
        "name": "New User"
    });

    let response = app.post("/api/v1/auth/register", &payload).await;

    assert_eq!(response.status(), 201);

    let body: serde_json::Value = response.json().await.unwrap();
    assert_eq!(body["user"]["email"], "new@example.com");
    assert!(body["tokens"]["access_token"].is_string());
}

#[tokio::test]
async fn test_register_duplicate_email() {
    let app = spawn_app().await;

    let payload = json!({
        "email": app.test_user.email,
        "password": "password123",
        "name": "Duplicate User"
    });

    let response = app.post("/api/v1/auth/register", &payload).await;

    assert_eq!(response.status(), 409);
}

#[tokio::test]
async fn test_login_success() {
    let app = spawn_app().await;

    // First register a user
    let register_payload = json!({
        "email": "login@example.com",
        "password": "password123",
        "name": "Login User"
    });
    app.post("/api/v1/auth/register", &register_payload).await;

    // Then login
    let login_payload = json!({
        "email": "login@example.com",
        "password": "password123"
    });

    let response = app.post("/api/v1/auth/login", &login_payload).await;

    assert_eq!(response.status(), 200);

    let body: serde_json::Value = response.json().await.unwrap();
    assert!(body["tokens"]["access_token"].is_string());
}

#[tokio::test]
async fn test_login_wrong_password() {
    let app = spawn_app().await;

    let payload = json!({
        "email": app.test_user.email,
        "password": "wrongpassword"
    });

    let response = app.post("/api/v1/auth/login", &payload).await;

    assert_eq!(response.status(), 401);
}
```

```rust
// tests/api/product_test.rs
use crate::common::spawn_app;
use serde_json::json;
use uuid::Uuid;

#[tokio::test]
async fn test_list_products() {
    let app = spawn_app().await;

    let response = app.get("/api/v1/products").await;

    assert_eq!(response.status(), 200);

    let body: serde_json::Value = response.json().await.unwrap();
    assert!(body["items"].is_array());
    assert!(body["total"].is_number());
}

#[tokio::test]
async fn test_create_product() {
    let app = spawn_app().await;

    // Create category first
    let category_id = create_test_category(&app.pool).await;

    let payload = json!({
        "name": "Test Product",
        "description": "A test product",
        "price": 99.99,
        "category_id": category_id
    });

    let response = app.post_auth("/api/v1/products", &payload).await;

    assert_eq!(response.status(), 201);

    let body: serde_json::Value = response.json().await.unwrap();
    assert_eq!(body["name"], "Test Product");
    assert_eq!(body["price"], "99.99");
    assert!(body["id"].is_string());
}

#[tokio::test]
async fn test_create_product_validation_error() {
    let app = spawn_app().await;

    let payload = json!({
        "name": "",  // Invalid: empty name
        "price": -10.00  // Invalid: negative price
    });

    let response = app.post_auth("/api/v1/products", &payload).await;

    assert_eq!(response.status(), 422);
}

#[tokio::test]
async fn test_get_product() {
    let app = spawn_app().await;
    let product_id = create_test_product(&app.pool, app.test_user.id).await;

    let response = app.get(&format!("/api/v1/products/{}", product_id)).await;

    assert_eq!(response.status(), 200);

    let body: serde_json::Value = response.json().await.unwrap();
    assert_eq!(body["id"], product_id.to_string());
}

#[tokio::test]
async fn test_get_product_not_found() {
    let app = spawn_app().await;
    let random_id = Uuid::new_v4();

    let response = app.get(&format!("/api/v1/products/{}", random_id)).await;

    assert_eq!(response.status(), 404);
}

#[tokio::test]
async fn test_update_product() {
    let app = spawn_app().await;
    let product_id = create_test_product(&app.pool, app.test_user.id).await;

    let payload = json!({
        "name": "Updated Product",
        "price": 149.99
    });

    let response = app
        .put_auth(&format!("/api/v1/products/{}", product_id), &payload)
        .await;

    assert_eq!(response.status(), 200);

    let body: serde_json::Value = response.json().await.unwrap();
    assert_eq!(body["name"], "Updated Product");
}

#[tokio::test]
async fn test_delete_product() {
    let app = spawn_app().await;
    let product_id = create_test_product(&app.pool, app.test_user.id).await;

    let response = app
        .delete_auth(&format!("/api/v1/products/{}", product_id))
        .await;

    assert_eq!(response.status(), 204);

    // Verify it's deleted
    let get_response = app.get(&format!("/api/v1/products/{}", product_id)).await;
    assert_eq!(get_response.status(), 404);
}

#[tokio::test]
async fn test_delete_product_unauthorized() {
    let app = spawn_app().await;

    // Create product owned by different user
    let other_user_id = Uuid::new_v4();
    let product_id = create_test_product(&app.pool, other_user_id).await;

    let response = app
        .delete_auth(&format!("/api/v1/products/{}", product_id))
        .await;

    assert_eq!(response.status(), 403);
}

// Helper functions
async fn create_test_category(pool: &PgPool) -> Uuid {
    let id = Uuid::new_v4();
    sqlx::query!(
        "INSERT INTO categories (id, name, slug) VALUES ($1, $2, $3)",
        id,
        "Test Category",
        "test-category"
    )
    .execute(pool)
    .await
    .unwrap();
    id
}

async fn create_test_product(pool: &PgPool, owner_id: Uuid) -> Uuid {
    let id = Uuid::new_v4();
    let category_id = create_test_category(pool).await;

    sqlx::query!(
        r#"
        INSERT INTO products (id, name, slug, price, category_id, owner_id, status)
        VALUES ($1, $2, $3, $4, $5, $6, 'active')
        "#,
        id,
        "Test Product",
        format!("test-product-{}", id),
        rust_decimal::Decimal::from(100),
        category_id,
        owner_id
    )
    .execute(pool)
    .await
    .unwrap();

    id
}
```

## Database Fixtures

```sql
-- tests/fixtures/users.sql
INSERT INTO users (id, email, password_hash, name, role, is_active)
VALUES
    ('550e8400-e29b-41d4-a716-446655440001', 'admin@example.com', '$argon2...', 'Admin User', 'admin', true),
    ('550e8400-e29b-41d4-a716-446655440002', 'user@example.com', '$argon2...', 'Regular User', 'user', true);
```

```rust
// Using sqlx test fixtures
#[sqlx::test(fixtures("users", "products"))]
async fn test_with_fixtures(pool: PgPool) {
    // Fixtures are automatically loaded
    let user = sqlx::query_as!(User, "SELECT * FROM users WHERE email = 'admin@example.com'")
        .fetch_one(&pool)
        .await
        .unwrap();

    assert_eq!(user.role, "admin");
}
```

## Running Integration Tests

```bash
# Run all integration tests
cargo test --test '*'

# Run specific test file
cargo test --test integration_test

# Run with test database URL
DATABASE_URL=postgres://test:test@localhost/test cargo test

# Run with logging enabled
TEST_LOG=1 cargo test -- --nocapture

# Run tests sequentially (if they share state)
cargo test -- --test-threads=1
```

## Best Practices

1. **Isolated tests**: Each test should have its own database
2. **Clean up**: Use transactions or drop databases after tests
3. **Realistic data**: Use fixtures that mirror production data
4. **Test the API**: Focus on HTTP layer, not internals
5. **Async handling**: Use `tokio::test` for async tests
6. **Helper functions**: Create utilities for common operations
7. **CI/CD integration**: Run tests in isolated containers
