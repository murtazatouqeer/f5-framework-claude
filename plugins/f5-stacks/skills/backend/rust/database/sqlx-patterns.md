---
name: rust-sqlx-patterns
description: SQLx patterns for Rust - compile-time checked SQL
applies_to: rust
---

# SQLx Patterns in Rust

## Overview

SQLx is an async SQL toolkit for Rust with compile-time checked queries.
It supports PostgreSQL, MySQL, SQLite, and MSSQL.

## Database Connection

```rust
// src/infrastructure/database.rs
use sqlx::{postgres::PgPoolOptions, PgPool};
use std::time::Duration;

use crate::config::DatabaseConfig;

pub struct Database;

impl Database {
    pub async fn connect(config: &DatabaseConfig) -> anyhow::Result<PgPool> {
        let pool = PgPoolOptions::new()
            .max_connections(config.max_connections)
            .min_connections(config.min_connections.unwrap_or(1))
            .acquire_timeout(Duration::from_secs(3))
            .idle_timeout(Duration::from_secs(600))
            .max_lifetime(Duration::from_secs(1800))
            .connect(&config.url)
            .await?;

        // Run migrations
        sqlx::migrate!("./migrations")
            .run(&pool)
            .await?;

        Ok(pool)
    }

    /// Health check
    pub async fn ping(pool: &PgPool) -> bool {
        sqlx::query("SELECT 1")
            .execute(pool)
            .await
            .is_ok()
    }
}
```

## Entity Models

```rust
// src/domain/product/entity.rs
use chrono::{DateTime, Utc};
use rust_decimal::Decimal;
use serde::{Deserialize, Serialize};
use sqlx::FromRow;
use uuid::Uuid;

/// Product entity mapped from database
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct Product {
    pub id: Uuid,
    pub name: String,
    pub slug: String,
    pub description: Option<String>,
    pub price: Decimal,
    pub compare_price: Option<Decimal>,
    pub status: ProductStatus,
    pub category_id: Uuid,
    pub owner_id: Uuid,
    pub stock_quantity: i32,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub deleted_at: Option<DateTime<Utc>>,
}

/// Custom enum type mapped to PostgreSQL
#[derive(Debug, Clone, Copy, Serialize, Deserialize, sqlx::Type, PartialEq, Eq)]
#[sqlx(type_name = "product_status", rename_all = "lowercase")]
pub enum ProductStatus {
    Draft,
    Active,
    Inactive,
    Archived,
}

impl Product {
    pub fn new(
        name: String,
        price: Decimal,
        category_id: Uuid,
        owner_id: Uuid,
    ) -> Self {
        let now = Utc::now();
        Self {
            id: Uuid::new_v4(),
            name: name.clone(),
            slug: slug::slugify(&name),
            description: None,
            price,
            compare_price: None,
            status: ProductStatus::Draft,
            category_id,
            owner_id,
            stock_quantity: 0,
            created_at: now,
            updated_at: now,
            deleted_at: None,
        }
    }

    pub fn is_available(&self) -> bool {
        self.status == ProductStatus::Active && self.stock_quantity > 0
    }
}
```

## Repository Implementation

```rust
// src/infrastructure/repositories/product_repository.rs
use async_trait::async_trait;
use sqlx::PgPool;
use uuid::Uuid;

use crate::{
    domain::product::{
        entity::{Product, ProductStatus},
        repository::{ProductFilter, ProductRepository},
    },
    error::RepositoryError,
};

pub struct PostgresProductRepository {
    pool: PgPool,
}

impl PostgresProductRepository {
    pub fn new(pool: PgPool) -> Self {
        Self { pool }
    }
}

#[async_trait]
impl ProductRepository for PostgresProductRepository {
    /// Create a new product
    async fn create(&self, product: &Product) -> Result<Product, RepositoryError> {
        let created = sqlx::query_as!(
            Product,
            r#"
            INSERT INTO products (
                id, name, slug, description, price, compare_price,
                status, category_id, owner_id, stock_quantity,
                created_at, updated_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            RETURNING
                id, name, slug, description, price, compare_price,
                status as "status: ProductStatus",
                category_id, owner_id, stock_quantity,
                created_at, updated_at, deleted_at
            "#,
            product.id,
            product.name,
            product.slug,
            product.description,
            product.price,
            product.compare_price,
            product.status as ProductStatus,
            product.category_id,
            product.owner_id,
            product.stock_quantity,
            product.created_at,
            product.updated_at,
        )
        .fetch_one(&self.pool)
        .await?;

        Ok(created)
    }

    /// Get product by ID
    async fn get_by_id(&self, id: Uuid) -> Result<Option<Product>, RepositoryError> {
        let product = sqlx::query_as!(
            Product,
            r#"
            SELECT
                id, name, slug, description, price, compare_price,
                status as "status: ProductStatus",
                category_id, owner_id, stock_quantity,
                created_at, updated_at, deleted_at
            FROM products
            WHERE id = $1 AND deleted_at IS NULL
            "#,
            id
        )
        .fetch_optional(&self.pool)
        .await?;

        Ok(product)
    }

    /// Get product by slug
    async fn get_by_slug(&self, slug: &str) -> Result<Option<Product>, RepositoryError> {
        let product = sqlx::query_as!(
            Product,
            r#"
            SELECT
                id, name, slug, description, price, compare_price,
                status as "status: ProductStatus",
                category_id, owner_id, stock_quantity,
                created_at, updated_at, deleted_at
            FROM products
            WHERE slug = $1 AND deleted_at IS NULL
            "#,
            slug
        )
        .fetch_optional(&self.pool)
        .await?;

        Ok(product)
    }

    /// Update product
    async fn update(&self, product: &Product) -> Result<Product, RepositoryError> {
        let updated = sqlx::query_as!(
            Product,
            r#"
            UPDATE products
            SET
                name = $2,
                slug = $3,
                description = $4,
                price = $5,
                compare_price = $6,
                status = $7,
                category_id = $8,
                stock_quantity = $9,
                updated_at = NOW()
            WHERE id = $1 AND deleted_at IS NULL
            RETURNING
                id, name, slug, description, price, compare_price,
                status as "status: ProductStatus",
                category_id, owner_id, stock_quantity,
                created_at, updated_at, deleted_at
            "#,
            product.id,
            product.name,
            product.slug,
            product.description,
            product.price,
            product.compare_price,
            product.status as ProductStatus,
            product.category_id,
            product.stock_quantity,
        )
        .fetch_one(&self.pool)
        .await?;

        Ok(updated)
    }

    /// Soft delete product
    async fn soft_delete(&self, id: Uuid) -> Result<(), RepositoryError> {
        sqlx::query!(
            "UPDATE products SET deleted_at = NOW() WHERE id = $1",
            id
        )
        .execute(&self.pool)
        .await?;

        Ok(())
    }

    /// List products with filtering and pagination
    async fn list(
        &self,
        filter: &ProductFilter,
        offset: i64,
        limit: i64,
    ) -> Result<(Vec<Product>, i64), RepositoryError> {
        // Note: For complex dynamic queries, consider using query builder or raw SQL

        // Count total
        let count = sqlx::query_scalar!(
            r#"
            SELECT COUNT(*) as "count!"
            FROM products
            WHERE deleted_at IS NULL
              AND ($1::text IS NULL OR name ILIKE '%' || $1 || '%')
              AND ($2::product_status IS NULL OR status = $2)
              AND ($3::uuid IS NULL OR category_id = $3)
            "#,
            filter.search,
            filter.status as Option<ProductStatus>,
            filter.category_id,
        )
        .fetch_one(&self.pool)
        .await?;

        // Fetch items
        let products = sqlx::query_as!(
            Product,
            r#"
            SELECT
                id, name, slug, description, price, compare_price,
                status as "status: ProductStatus",
                category_id, owner_id, stock_quantity,
                created_at, updated_at, deleted_at
            FROM products
            WHERE deleted_at IS NULL
              AND ($1::text IS NULL OR name ILIKE '%' || $1 || '%')
              AND ($2::product_status IS NULL OR status = $2)
              AND ($3::uuid IS NULL OR category_id = $3)
            ORDER BY created_at DESC
            OFFSET $4 LIMIT $5
            "#,
            filter.search,
            filter.status as Option<ProductStatus>,
            filter.category_id,
            offset,
            limit,
        )
        .fetch_all(&self.pool)
        .await?;

        Ok((products, count))
    }
}
```

## Transactions

```rust
// src/infrastructure/repositories/order_repository.rs
use sqlx::PgPool;

impl PostgresOrderRepository {
    /// Create order with items in a transaction
    pub async fn create_with_items(
        &self,
        order: &Order,
        items: &[OrderItem],
    ) -> Result<Order, RepositoryError> {
        // Begin transaction
        let mut tx = self.pool.begin().await?;

        // Insert order
        let created_order = sqlx::query_as!(
            Order,
            r#"
            INSERT INTO orders (id, customer_id, status, total, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id, customer_id, status as "status: OrderStatus",
                      total, created_at, updated_at
            "#,
            order.id,
            order.customer_id,
            order.status as OrderStatus,
            order.total,
            order.created_at,
            order.updated_at,
        )
        .fetch_one(&mut *tx)
        .await?;

        // Insert items
        for item in items {
            sqlx::query!(
                r#"
                INSERT INTO order_items (id, order_id, product_id, quantity, unit_price)
                VALUES ($1, $2, $3, $4, $5)
                "#,
                Uuid::new_v4(),
                order.id,
                item.product_id,
                item.quantity,
                item.unit_price,
            )
            .execute(&mut *tx)
            .await?;

            // Update product stock
            sqlx::query!(
                "UPDATE products SET stock_quantity = stock_quantity - $1 WHERE id = $2",
                item.quantity,
                item.product_id,
            )
            .execute(&mut *tx)
            .await?;
        }

        // Commit transaction
        tx.commit().await?;

        Ok(created_order)
    }
}
```

## Raw Queries

```rust
// For truly dynamic queries
impl PostgresProductRepository {
    pub async fn search_dynamic(
        &self,
        filter: &ProductFilter,
        sort_by: &str,
        sort_order: &str,
        offset: i64,
        limit: i64,
    ) -> Result<Vec<Product>, RepositoryError> {
        // Build query dynamically
        let mut conditions = vec!["deleted_at IS NULL".to_string()];
        let mut params: Vec<Box<dyn sqlx::Encode<'_, sqlx::Postgres> + Send + Sync>> = vec![];

        if let Some(ref search) = filter.search {
            conditions.push(format!("(name ILIKE ${})", params.len() + 1));
            params.push(Box::new(format!("%{}%", search)));
        }

        // Validate sort field (prevent SQL injection)
        let valid_sort_fields = ["name", "price", "created_at", "updated_at"];
        let sort_field = if valid_sort_fields.contains(&sort_by) {
            sort_by
        } else {
            "created_at"
        };

        let sort_dir = if sort_order.to_uppercase() == "ASC" { "ASC" } else { "DESC" };

        let query = format!(
            r#"
            SELECT id, name, slug, description, price, compare_price,
                   status, category_id, owner_id, stock_quantity,
                   created_at, updated_at, deleted_at
            FROM products
            WHERE {}
            ORDER BY {} {}
            OFFSET {} LIMIT {}
            "#,
            conditions.join(" AND "),
            sort_field,
            sort_dir,
            offset,
            limit
        );

        let products: Vec<Product> = sqlx::query_as(&query)
            .fetch_all(&self.pool)
            .await?;

        Ok(products)
    }
}
```

## Connection Pool Management

```rust
// src/config.rs
#[derive(Debug, Deserialize, Clone)]
pub struct DatabaseConfig {
    pub url: String,
    pub max_connections: u32,
    pub min_connections: Option<u32>,
    pub connect_timeout_secs: Option<u64>,
    pub idle_timeout_secs: Option<u64>,
    pub max_lifetime_secs: Option<u64>,
}

// src/infrastructure/database.rs
use sqlx::postgres::{PgConnectOptions, PgPoolOptions, PgSslMode};
use std::str::FromStr;

impl Database {
    pub async fn connect_with_options(config: &DatabaseConfig) -> anyhow::Result<PgPool> {
        let connect_options = PgConnectOptions::from_str(&config.url)?
            .ssl_mode(PgSslMode::Prefer)
            .application_name("myapp");

        let pool = PgPoolOptions::new()
            .max_connections(config.max_connections)
            .min_connections(config.min_connections.unwrap_or(1))
            .acquire_timeout(Duration::from_secs(config.connect_timeout_secs.unwrap_or(3)))
            .idle_timeout(Duration::from_secs(config.idle_timeout_secs.unwrap_or(600)))
            .max_lifetime(Duration::from_secs(config.max_lifetime_secs.unwrap_or(1800)))
            .connect_with(connect_options)
            .await?;

        Ok(pool)
    }
}
```

## Testing with SQLx

```rust
// tests/repository_tests.rs
use sqlx::PgPool;

#[sqlx::test]
async fn test_create_product(pool: PgPool) {
    let repo = PostgresProductRepository::new(pool);

    let product = Product::new(
        "Test Product".to_string(),
        Decimal::from(99),
        Uuid::new_v4(),
        Uuid::new_v4(),
    );

    let created = repo.create(&product).await.unwrap();

    assert_eq!(created.name, "Test Product");
    assert_eq!(created.status, ProductStatus::Draft);
}

#[sqlx::test(fixtures("products"))]
async fn test_get_product(pool: PgPool) {
    // Uses fixture from tests/fixtures/products.sql
    let repo = PostgresProductRepository::new(pool);

    let product = repo.get_by_slug("test-product").await.unwrap();

    assert!(product.is_some());
}
```

## Best Practices

1. **Use `query_as!` macro**: Get compile-time SQL validation
2. **Use transactions**: For operations that need atomicity
3. **Handle NULL properly**: Use `Option<T>` for nullable columns
4. **Pool configuration**: Set appropriate connection limits
5. **Migrations**: Use SQLx CLI for migration management
6. **Type annotations**: Use explicit type casts in complex queries
7. **Connection health**: Implement health checks for the pool
