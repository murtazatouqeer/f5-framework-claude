---
name: rust-clean-architecture
description: Clean Architecture implementation in Rust
applies_to: rust
---

# Clean Architecture in Rust

## Overview

Clean Architecture separates concerns into concentric layers, with dependencies pointing inward.
Rust's trait system provides excellent support for dependency inversion.

## Layer Structure

```
┌─────────────────────────────────────────┐
│           API / Handlers                │  ← Frameworks & Drivers
├─────────────────────────────────────────┤
│         Application Services            │  ← Interface Adapters
├─────────────────────────────────────────┤
│         Domain / Use Cases              │  ← Business Rules
├─────────────────────────────────────────┤
│              Entities                   │  ← Enterprise Business Rules
└─────────────────────────────────────────┘
```

## Domain Layer (Entities)

The innermost layer contains pure business logic with no external dependencies.

```rust
// src/domain/order/entity.rs
use chrono::{DateTime, Utc};
use rust_decimal::Decimal;
use uuid::Uuid;

#[derive(Debug, Clone)]
pub struct Order {
    id: OrderId,
    customer_id: CustomerId,
    items: Vec<OrderItem>,
    status: OrderStatus,
    total: Decimal,
    created_at: DateTime<Utc>,
    updated_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct OrderId(Uuid);

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct CustomerId(Uuid);

#[derive(Debug, Clone)]
pub struct OrderItem {
    pub product_id: Uuid,
    pub quantity: u32,
    pub unit_price: Decimal,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum OrderStatus {
    Pending,
    Confirmed,
    Processing,
    Shipped,
    Delivered,
    Cancelled,
}

impl Order {
    /// Create a new order - domain logic
    pub fn new(customer_id: CustomerId, items: Vec<OrderItem>) -> Result<Self, OrderError> {
        if items.is_empty() {
            return Err(OrderError::EmptyOrder);
        }

        let total = items.iter()
            .map(|item| item.unit_price * Decimal::from(item.quantity))
            .sum();

        let now = Utc::now();

        Ok(Self {
            id: OrderId(Uuid::new_v4()),
            customer_id,
            items,
            status: OrderStatus::Pending,
            total,
            created_at: now,
            updated_at: now,
        })
    }

    /// Confirm order - state transition with business rules
    pub fn confirm(&mut self) -> Result<(), OrderError> {
        match self.status {
            OrderStatus::Pending => {
                self.status = OrderStatus::Confirmed;
                self.updated_at = Utc::now();
                Ok(())
            }
            _ => Err(OrderError::InvalidStateTransition {
                from: self.status,
                to: OrderStatus::Confirmed,
            }),
        }
    }

    /// Cancel order - business rules for cancellation
    pub fn cancel(&mut self) -> Result<(), OrderError> {
        match self.status {
            OrderStatus::Pending | OrderStatus::Confirmed => {
                self.status = OrderStatus::Cancelled;
                self.updated_at = Utc::now();
                Ok(())
            }
            OrderStatus::Shipped | OrderStatus::Delivered => {
                Err(OrderError::CannotCancelShippedOrder)
            }
            _ => Err(OrderError::InvalidStateTransition {
                from: self.status,
                to: OrderStatus::Cancelled,
            }),
        }
    }

    // Getters
    pub fn id(&self) -> OrderId { self.id }
    pub fn customer_id(&self) -> CustomerId { self.customer_id }
    pub fn status(&self) -> OrderStatus { self.status }
    pub fn total(&self) -> Decimal { self.total }
    pub fn items(&self) -> &[OrderItem] { &self.items }
}

#[derive(Debug, thiserror::Error)]
pub enum OrderError {
    #[error("Order cannot be empty")]
    EmptyOrder,

    #[error("Invalid state transition from {from:?} to {to:?}")]
    InvalidStateTransition {
        from: OrderStatus,
        to: OrderStatus,
    },

    #[error("Cannot cancel shipped or delivered orders")]
    CannotCancelShippedOrder,
}
```

## Repository Trait (Port)

Define traits in the domain layer for infrastructure dependencies.

```rust
// src/domain/order/repository.rs
use async_trait::async_trait;

use super::entity::{Order, OrderId, CustomerId};

#[async_trait]
pub trait OrderRepository: Send + Sync {
    async fn save(&self, order: &Order) -> Result<(), RepositoryError>;
    async fn find_by_id(&self, id: OrderId) -> Result<Option<Order>, RepositoryError>;
    async fn find_by_customer(&self, customer_id: CustomerId) -> Result<Vec<Order>, RepositoryError>;
    async fn update(&self, order: &Order) -> Result<(), RepositoryError>;
    async fn delete(&self, id: OrderId) -> Result<(), RepositoryError>;
}

#[derive(Debug, thiserror::Error)]
pub enum RepositoryError {
    #[error("Entity not found")]
    NotFound,

    #[error("Duplicate entity")]
    Duplicate,

    #[error("Database error: {0}")]
    Database(String),
}
```

## Application Layer (Use Cases)

Application services orchestrate domain entities and depend on trait abstractions.

```rust
// src/application/order/service.rs
use std::sync::Arc;
use async_trait::async_trait;

use crate::domain::order::{
    entity::{Order, OrderId, CustomerId, OrderItem, OrderError},
    repository::{OrderRepository, RepositoryError},
};

pub struct OrderService<R: OrderRepository> {
    repository: Arc<R>,
}

impl<R: OrderRepository> OrderService<R> {
    pub fn new(repository: Arc<R>) -> Self {
        Self { repository }
    }

    /// Create a new order
    pub async fn create_order(
        &self,
        customer_id: CustomerId,
        items: Vec<OrderItem>,
    ) -> Result<Order, OrderServiceError> {
        // Domain logic
        let order = Order::new(customer_id, items)?;

        // Persistence
        self.repository.save(&order).await?;

        Ok(order)
    }

    /// Get order by ID
    pub async fn get_order(&self, id: OrderId) -> Result<Order, OrderServiceError> {
        self.repository
            .find_by_id(id)
            .await?
            .ok_or(OrderServiceError::NotFound)
    }

    /// Confirm an order
    pub async fn confirm_order(&self, id: OrderId) -> Result<Order, OrderServiceError> {
        let mut order = self.get_order(id).await?;

        // Domain logic
        order.confirm()?;

        // Persistence
        self.repository.update(&order).await?;

        Ok(order)
    }

    /// Cancel an order
    pub async fn cancel_order(&self, id: OrderId) -> Result<Order, OrderServiceError> {
        let mut order = self.get_order(id).await?;

        // Domain logic
        order.cancel()?;

        // Persistence
        self.repository.update(&order).await?;

        Ok(order)
    }

    /// Get customer orders
    pub async fn get_customer_orders(
        &self,
        customer_id: CustomerId,
    ) -> Result<Vec<Order>, OrderServiceError> {
        Ok(self.repository.find_by_customer(customer_id).await?)
    }
}

#[derive(Debug, thiserror::Error)]
pub enum OrderServiceError {
    #[error("Order not found")]
    NotFound,

    #[error("Domain error: {0}")]
    Domain(#[from] OrderError),

    #[error("Repository error: {0}")]
    Repository(#[from] RepositoryError),
}
```

## Infrastructure Layer (Adapters)

Implement repository traits with concrete database access.

```rust
// src/infrastructure/repositories/postgres_order_repo.rs
use async_trait::async_trait;
use sqlx::PgPool;

use crate::domain::order::{
    entity::{Order, OrderId, CustomerId, OrderItem, OrderStatus},
    repository::{OrderRepository, RepositoryError},
};

pub struct PostgresOrderRepository {
    pool: PgPool,
}

impl PostgresOrderRepository {
    pub fn new(pool: PgPool) -> Self {
        Self { pool }
    }
}

#[async_trait]
impl OrderRepository for PostgresOrderRepository {
    async fn save(&self, order: &Order) -> Result<(), RepositoryError> {
        // Start transaction
        let mut tx = self.pool.begin().await
            .map_err(|e| RepositoryError::Database(e.to_string()))?;

        // Insert order
        sqlx::query!(
            r#"
            INSERT INTO orders (id, customer_id, status, total, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6)
            "#,
            order.id().0,
            order.customer_id().0,
            order.status() as i16,
            order.total(),
            order.created_at,
            order.updated_at,
        )
        .execute(&mut *tx)
        .await
        .map_err(|e| RepositoryError::Database(e.to_string()))?;

        // Insert order items
        for item in order.items() {
            sqlx::query!(
                r#"
                INSERT INTO order_items (order_id, product_id, quantity, unit_price)
                VALUES ($1, $2, $3, $4)
                "#,
                order.id().0,
                item.product_id,
                item.quantity as i32,
                item.unit_price,
            )
            .execute(&mut *tx)
            .await
            .map_err(|e| RepositoryError::Database(e.to_string()))?;
        }

        // Commit
        tx.commit().await
            .map_err(|e| RepositoryError::Database(e.to_string()))?;

        Ok(())
    }

    async fn find_by_id(&self, id: OrderId) -> Result<Option<Order>, RepositoryError> {
        // Implementation details...
        todo!()
    }

    async fn find_by_customer(&self, customer_id: CustomerId) -> Result<Vec<Order>, RepositoryError> {
        // Implementation details...
        todo!()
    }

    async fn update(&self, order: &Order) -> Result<(), RepositoryError> {
        sqlx::query!(
            r#"
            UPDATE orders
            SET status = $2, updated_at = $3
            WHERE id = $1
            "#,
            order.id().0,
            order.status() as i16,
            order.updated_at,
        )
        .execute(&self.pool)
        .await
        .map_err(|e| RepositoryError::Database(e.to_string()))?;

        Ok(())
    }

    async fn delete(&self, id: OrderId) -> Result<(), RepositoryError> {
        sqlx::query!("DELETE FROM orders WHERE id = $1", id.0)
            .execute(&self.pool)
            .await
            .map_err(|e| RepositoryError::Database(e.to_string()))?;

        Ok(())
    }
}
```

## Dependency Injection

Wire everything together in the startup module.

```rust
// src/startup.rs
use std::sync::Arc;
use axum::Router;

use crate::{
    api::router::create_router,
    application::order::OrderService,
    config::Config,
    infrastructure::{
        database::Database,
        repositories::PostgresOrderRepository,
    },
};

pub struct Application {
    router: Router,
}

impl Application {
    pub async fn build(config: &Config) -> anyhow::Result<Self> {
        // Infrastructure
        let pool = Database::connect(&config.database).await?;

        // Repositories (implement traits)
        let order_repo = Arc::new(PostgresOrderRepository::new(pool.clone()));

        // Application services (depend on trait abstractions)
        let order_service = Arc::new(OrderService::new(order_repo));

        // Application state
        let state = AppState {
            config: config.clone(),
            order_service,
        };

        let router = create_router(state);

        Ok(Self { router })
    }
}

#[derive(Clone)]
pub struct AppState {
    pub config: Config,
    pub order_service: Arc<OrderService<PostgresOrderRepository>>,
}
```

## Testing with Mock Repositories

```rust
// tests/order_service_test.rs
use std::sync::Arc;
use async_trait::async_trait;
use std::collections::HashMap;
use std::sync::RwLock;

use myapp::domain::order::{
    entity::{Order, OrderId, CustomerId},
    repository::{OrderRepository, RepositoryError},
};
use myapp::application::order::OrderService;

/// Mock repository for testing
struct MockOrderRepository {
    orders: RwLock<HashMap<Uuid, Order>>,
}

impl MockOrderRepository {
    fn new() -> Self {
        Self {
            orders: RwLock::new(HashMap::new()),
        }
    }
}

#[async_trait]
impl OrderRepository for MockOrderRepository {
    async fn save(&self, order: &Order) -> Result<(), RepositoryError> {
        self.orders.write().unwrap().insert(order.id().0, order.clone());
        Ok(())
    }

    async fn find_by_id(&self, id: OrderId) -> Result<Option<Order>, RepositoryError> {
        Ok(self.orders.read().unwrap().get(&id.0).cloned())
    }

    // ... other methods
}

#[tokio::test]
async fn test_create_order() {
    let repo = Arc::new(MockOrderRepository::new());
    let service = OrderService::new(repo);

    let items = vec![/* ... */];
    let result = service.create_order(CustomerId(Uuid::new_v4()), items).await;

    assert!(result.is_ok());
}
```

## Benefits of Clean Architecture in Rust

1. **Type Safety**: Compile-time guarantees for dependency direction
2. **Testability**: Easy to mock dependencies via traits
3. **Maintainability**: Clear separation of concerns
4. **Flexibility**: Infrastructure can change without affecting domain
5. **Domain Focus**: Business logic isolated and pure
