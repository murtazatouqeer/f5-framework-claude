---
name: rust-project-structure
description: Rust web API project structure and organization
applies_to: rust
---

# Rust Project Structure

## Overview

A well-organized Rust project separates concerns into modules:
domain, application, infrastructure, and API layers.

## Directory Structure

```
project/
├── src/
│   ├── main.rs                    # Entry point
│   ├── lib.rs                     # Library root
│   ├── config.rs                  # Configuration
│   ├── error.rs                   # Error types
│   ├── startup.rs                 # App initialization
│   │
│   ├── domain/                    # Business domain
│   │   ├── mod.rs
│   │   ├── user/
│   │   │   ├── mod.rs
│   │   │   ├── entity.rs
│   │   │   └── repository.rs
│   │   └── product/
│   │       └── ...
│   │
│   ├── application/               # Use cases
│   │   ├── mod.rs
│   │   └── user/
│   │       ├── mod.rs
│   │       ├── service.rs
│   │       └── dto.rs
│   │
│   ├── infrastructure/            # External adapters
│   │   ├── mod.rs
│   │   ├── database.rs
│   │   └── repositories/
│   │       └── postgres_user_repo.rs
│   │
│   ├── api/                       # HTTP layer
│   │   ├── mod.rs
│   │   ├── router.rs
│   │   ├── extractors.rs
│   │   └── handlers/
│   │       ├── mod.rs
│   │       ├── user_handler.rs
│   │       └── health.rs
│   │
│   └── middleware/
│       ├── mod.rs
│       └── auth.rs
│
├── migrations/                    # SQL migrations
│   └── 20240101_init.sql
│
├── tests/                         # Integration tests
│   ├── common/
│   │   └── mod.rs
│   └── api/
│       └── user_tests.rs
│
├── .env.example
├── Cargo.toml
└── docker-compose.yml
```

## Main Entry Point

```rust
// src/main.rs
use std::net::SocketAddr;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

use myapp::{config::Config, startup::Application};

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Initialize tracing
    tracing_subscriber::registry()
        .with(tracing_subscriber::EnvFilter::try_from_default_env()
            .unwrap_or_else(|_| "myapp=debug,tower_http=debug".into()))
        .with(tracing_subscriber::fmt::layer())
        .init();

    // Load configuration
    let config = Config::load()?;

    // Build application
    let app = Application::build(&config).await?;

    // Run server
    let addr = SocketAddr::from(([0, 0, 0, 0], config.server.port));
    tracing::info!("Starting server on {}", addr);

    let listener = tokio::net::TcpListener::bind(addr).await?;
    axum::serve(listener, app.router()).await?;

    Ok(())
}
```

## Library Root

```rust
// src/lib.rs
pub mod api;
pub mod application;
pub mod config;
pub mod domain;
pub mod error;
pub mod infrastructure;
pub mod middleware;
pub mod startup;

pub use error::{AppError, Result};
```

## Configuration

```rust
// src/config.rs
use serde::Deserialize;
use config::{Config as ConfigLoader, Environment, File};

#[derive(Debug, Deserialize, Clone)]
pub struct Config {
    pub server: ServerConfig,
    pub database: DatabaseConfig,
    pub jwt: JwtConfig,
}

#[derive(Debug, Deserialize, Clone)]
pub struct ServerConfig {
    pub port: u16,
    pub host: String,
}

#[derive(Debug, Deserialize, Clone)]
pub struct DatabaseConfig {
    pub url: String,
    pub max_connections: u32,
}

#[derive(Debug, Deserialize, Clone)]
pub struct JwtConfig {
    pub secret: String,
    pub expiration_hours: i64,
}

impl Config {
    pub fn load() -> anyhow::Result<Self> {
        dotenvy::dotenv().ok();

        let config = ConfigLoader::builder()
            .add_source(File::with_name("config/default").required(false))
            .add_source(File::with_name("config/local").required(false))
            .add_source(Environment::with_prefix("APP").separator("__"))
            .build()?;

        Ok(config.try_deserialize()?)
    }
}
```

## Application Startup

```rust
// src/startup.rs
use std::sync::Arc;
use axum::Router;
use sqlx::PgPool;

use crate::{
    api::router::create_router,
    application::user::UserService,
    config::Config,
    infrastructure::{database::Database, repositories::PostgresUserRepository},
};

pub struct Application {
    router: Router,
}

impl Application {
    pub async fn build(config: &Config) -> anyhow::Result<Self> {
        // Database connection
        let pool = Database::connect(&config.database).await?;

        // Repositories
        let user_repo = Arc::new(PostgresUserRepository::new(pool.clone()));

        // Services
        let user_service = Arc::new(UserService::new(user_repo));

        // Application state
        let state = AppState {
            config: config.clone(),
            pool,
            user_service,
        };

        // Router
        let router = create_router(state);

        Ok(Self { router })
    }

    pub fn router(self) -> Router {
        self.router
    }
}

#[derive(Clone)]
pub struct AppState {
    pub config: Config,
    pub pool: PgPool,
    pub user_service: Arc<UserService>,
}
```

## Module Organization Best Practices

### Domain Module

```rust
// src/domain/mod.rs
pub mod user;
pub mod product;
pub mod order;

// Re-export commonly used types
pub use user::entity::User;
pub use product::entity::Product;
```

### Entity Module

```rust
// src/domain/user/mod.rs
pub mod entity;
pub mod repository;

pub use entity::User;
pub use repository::UserRepository;
```

### Prelude Pattern

```rust
// src/prelude.rs
//! Commonly used imports for internal use

pub use crate::error::{AppError, Result};
pub use crate::domain::{User, Product};
pub use uuid::Uuid;
pub use chrono::{DateTime, Utc};
```

## Cargo.toml Example

```toml
[package]
name = "myapp"
version = "0.1.0"
edition = "2021"

[dependencies]
# Async runtime
tokio = { version = "1", features = ["full"] }

# Web framework
axum = { version = "0.7", features = ["macros"] }
tower = "0.4"
tower-http = { version = "0.5", features = ["trace", "cors"] }

# Database
sqlx = { version = "0.7", features = ["runtime-tokio", "postgres", "uuid", "chrono", "rust_decimal"] }

# Serialization
serde = { version = "1", features = ["derive"] }
serde_json = "1"

# Auth
jsonwebtoken = "9"
argon2 = "0.5"

# Validation
validator = { version = "0.16", features = ["derive"] }

# Error handling
thiserror = "1"
anyhow = "1"

# Config
config = "0.14"
dotenvy = "0.15"

# Logging
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter"] }

# Utils
uuid = { version = "1", features = ["v4", "serde"] }
chrono = { version = "0.4", features = ["serde"] }
rust_decimal = { version = "1", features = ["serde"] }
slug = "0.1"
async-trait = "0.1"

[dev-dependencies]
tokio-test = "0.4"
reqwest = { version = "0.11", features = ["json"] }
once_cell = "1"
fake = { version = "2", features = ["derive"] }
```
