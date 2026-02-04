---
name: rust-sea-orm
description: SeaORM patterns for Rust - async ORM
applies_to: rust
---

# SeaORM Patterns

## Overview

SeaORM is an async and dynamic ORM for Rust, inspired by ActiveRecord.
It provides a more Rails-like experience compared to Diesel.

## Entity Definition

```rust
// src/entities/product.rs
use sea_orm::entity::prelude::*;
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, PartialEq, DeriveEntityModel, Serialize, Deserialize)]
#[sea_orm(table_name = "products")]
pub struct Model {
    #[sea_orm(primary_key, auto_increment = false)]
    pub id: Uuid,
    pub name: String,
    #[sea_orm(unique)]
    pub slug: String,
    #[sea_orm(column_type = "Text", nullable)]
    pub description: Option<String>,
    #[sea_orm(column_type = "Decimal(Some((10, 2)))")]
    pub price: Decimal,
    #[sea_orm(column_type = "Decimal(Some((10, 2)))", nullable)]
    pub compare_price: Option<Decimal>,
    pub status: ProductStatus,
    pub category_id: Uuid,
    pub owner_id: Uuid,
    pub stock_quantity: i32,
    pub created_at: DateTimeUtc,
    pub updated_at: DateTimeUtc,
    #[sea_orm(nullable)]
    pub deleted_at: Option<DateTimeUtc>,
}

#[derive(Copy, Clone, Debug, EnumIter, DeriveRelation)]
pub enum Relation {
    #[sea_orm(
        belongs_to = "super::category::Entity",
        from = "Column::CategoryId",
        to = "super::category::Column::Id"
    )]
    Category,
    #[sea_orm(
        belongs_to = "super::user::Entity",
        from = "Column::OwnerId",
        to = "super::user::Column::Id"
    )]
    Owner,
    #[sea_orm(has_many = "super::order_item::Entity")]
    OrderItems,
}

impl Related<super::category::Entity> for Entity {
    fn to() -> RelationDef {
        Relation::Category.def()
    }
}

impl Related<super::user::Entity> for Entity {
    fn to() -> RelationDef {
        Relation::Owner.def()
    }
}

impl ActiveModelBehavior for ActiveModel {}

#[derive(Debug, Clone, PartialEq, Eq, EnumIter, DeriveActiveEnum, Serialize, Deserialize)]
#[sea_orm(rs_type = "String", db_type = "Enum", enum_name = "product_status")]
pub enum ProductStatus {
    #[sea_orm(string_value = "draft")]
    Draft,
    #[sea_orm(string_value = "active")]
    Active,
    #[sea_orm(string_value = "inactive")]
    Inactive,
    #[sea_orm(string_value = "archived")]
    Archived,
}
```

## Database Connection

```rust
// src/infrastructure/database.rs
use sea_orm::{ConnectOptions, Database, DatabaseConnection};
use std::time::Duration;

use crate::config::DatabaseConfig;

pub async fn create_connection(config: &DatabaseConfig) -> DatabaseConnection {
    let mut opt = ConnectOptions::new(&config.url);

    opt.max_connections(config.max_connections)
        .min_connections(config.min_connections.unwrap_or(1))
        .connect_timeout(Duration::from_secs(3))
        .acquire_timeout(Duration::from_secs(3))
        .idle_timeout(Duration::from_secs(600))
        .max_lifetime(Duration::from_secs(1800))
        .sqlx_logging(true)
        .sqlx_logging_level(log::LevelFilter::Debug);

    Database::connect(opt)
        .await
        .expect("Failed to connect to database")
}
```

## Repository Implementation

```rust
// src/infrastructure/repositories/product_repository.rs
use sea_orm::{
    ActiveModelTrait, ColumnTrait, DatabaseConnection, EntityTrait,
    PaginatorTrait, QueryFilter, QueryOrder, Set,
};
use uuid::Uuid;

use crate::{
    entities::{prelude::*, product},
    error::RepositoryError,
};

pub struct SeaOrmProductRepository {
    db: DatabaseConnection,
}

impl SeaOrmProductRepository {
    pub fn new(db: DatabaseConnection) -> Self {
        Self { db }
    }

    /// Create a new product
    pub async fn create(&self, input: CreateProductInput) -> Result<product::Model, RepositoryError> {
        let now = chrono::Utc::now();

        let product = product::ActiveModel {
            id: Set(Uuid::new_v4()),
            name: Set(input.name.clone()),
            slug: Set(slug::slugify(&input.name)),
            description: Set(input.description),
            price: Set(input.price),
            compare_price: Set(input.compare_price),
            status: Set(product::ProductStatus::Draft),
            category_id: Set(input.category_id),
            owner_id: Set(input.owner_id),
            stock_quantity: Set(input.stock_quantity.unwrap_or(0)),
            created_at: Set(now),
            updated_at: Set(now),
            deleted_at: Set(None),
        };

        let result = product.insert(&self.db).await?;
        Ok(result)
    }

    /// Get product by ID
    pub async fn get_by_id(&self, id: Uuid) -> Result<Option<product::Model>, RepositoryError> {
        let result = Product::find_by_id(id)
            .filter(product::Column::DeletedAt.is_null())
            .one(&self.db)
            .await?;

        Ok(result)
    }

    /// Get product by slug
    pub async fn get_by_slug(&self, slug: &str) -> Result<Option<product::Model>, RepositoryError> {
        let result = Product::find()
            .filter(product::Column::Slug.eq(slug))
            .filter(product::Column::DeletedAt.is_null())
            .one(&self.db)
            .await?;

        Ok(result)
    }

    /// Update product
    pub async fn update(
        &self,
        id: Uuid,
        input: UpdateProductInput,
    ) -> Result<product::Model, RepositoryError> {
        let product = Product::find_by_id(id)
            .one(&self.db)
            .await?
            .ok_or(RepositoryError::NotFound)?;

        let mut active_model: product::ActiveModel = product.into();

        if let Some(name) = input.name {
            active_model.name = Set(name.clone());
            active_model.slug = Set(slug::slugify(&name));
        }
        if let Some(description) = input.description {
            active_model.description = Set(description);
        }
        if let Some(price) = input.price {
            active_model.price = Set(price);
        }
        if let Some(compare_price) = input.compare_price {
            active_model.compare_price = Set(compare_price);
        }
        if let Some(status) = input.status {
            active_model.status = Set(status);
        }
        if let Some(category_id) = input.category_id {
            active_model.category_id = Set(category_id);
        }
        if let Some(stock) = input.stock_quantity {
            active_model.stock_quantity = Set(stock);
        }

        active_model.updated_at = Set(chrono::Utc::now());

        let result = active_model.update(&self.db).await?;
        Ok(result)
    }

    /// Soft delete product
    pub async fn soft_delete(&self, id: Uuid) -> Result<(), RepositoryError> {
        let product = Product::find_by_id(id)
            .one(&self.db)
            .await?
            .ok_or(RepositoryError::NotFound)?;

        let mut active_model: product::ActiveModel = product.into();
        active_model.deleted_at = Set(Some(chrono::Utc::now()));

        active_model.update(&self.db).await?;
        Ok(())
    }

    /// List products with filtering and pagination
    pub async fn list(
        &self,
        filter: ProductFilter,
        page: u64,
        page_size: u64,
    ) -> Result<(Vec<product::Model>, u64), RepositoryError> {
        let mut query = Product::find()
            .filter(product::Column::DeletedAt.is_null());

        // Apply filters
        if let Some(search) = filter.search {
            query = query.filter(
                product::Column::Name.contains(&search)
                    .or(product::Column::Description.contains(&search))
            );
        }

        if let Some(status) = filter.status {
            query = query.filter(product::Column::Status.eq(status));
        }

        if let Some(category_id) = filter.category_id {
            query = query.filter(product::Column::CategoryId.eq(category_id));
        }

        if let Some(min_price) = filter.min_price {
            query = query.filter(product::Column::Price.gte(min_price));
        }

        if let Some(max_price) = filter.max_price {
            query = query.filter(product::Column::Price.lte(max_price));
        }

        // Order
        query = query.order_by_desc(product::Column::CreatedAt);

        // Paginate
        let paginator = query.paginate(&self.db, page_size);
        let total = paginator.num_items().await?;
        let items = paginator.fetch_page(page - 1).await?;

        Ok((items, total))
    }
}
```

## Eager Loading (Relations)

```rust
// Loading with relations
impl SeaOrmProductRepository {
    /// Get product with category
    pub async fn get_with_category(
        &self,
        id: Uuid,
    ) -> Result<Option<(product::Model, Option<category::Model>)>, RepositoryError> {
        let result = Product::find_by_id(id)
            .filter(product::Column::DeletedAt.is_null())
            .find_also_related(Category)
            .one(&self.db)
            .await?;

        Ok(result)
    }

    /// Get products with their categories
    pub async fn list_with_categories(
        &self,
        page: u64,
        page_size: u64,
    ) -> Result<Vec<(product::Model, Option<category::Model>)>, RepositoryError> {
        let result = Product::find()
            .filter(product::Column::DeletedAt.is_null())
            .find_also_related(Category)
            .order_by_desc(product::Column::CreatedAt)
            .paginate(&self.db, page_size)
            .fetch_page(page - 1)
            .await?;

        Ok(result)
    }

    /// Get category with all its products
    pub async fn get_category_with_products(
        &self,
        category_id: Uuid,
    ) -> Result<Option<(category::Model, Vec<product::Model>)>, RepositoryError> {
        let result = Category::find_by_id(category_id)
            .find_with_related(Product)
            .all(&self.db)
            .await?;

        if result.is_empty() {
            return Ok(None);
        }

        Ok(Some(result.into_iter().next().unwrap()))
    }
}
```

## Transactions

```rust
use sea_orm::{TransactionTrait, DbErr};

impl SeaOrmProductRepository {
    /// Create order with items in a transaction
    pub async fn create_order_with_items(
        &self,
        order_input: CreateOrderInput,
        items: Vec<CreateOrderItemInput>,
    ) -> Result<order::Model, RepositoryError> {
        let result = self.db.transaction::<_, order::Model, DbErr>(|txn| {
            Box::pin(async move {
                // Create order
                let order = order::ActiveModel {
                    id: Set(Uuid::new_v4()),
                    customer_id: Set(order_input.customer_id),
                    status: Set(order::OrderStatus::Pending),
                    total: Set(order_input.total),
                    created_at: Set(chrono::Utc::now()),
                    updated_at: Set(chrono::Utc::now()),
                };

                let order = order.insert(txn).await?;

                // Create order items and update stock
                for item in items {
                    // Insert item
                    let order_item = order_item::ActiveModel {
                        id: Set(Uuid::new_v4()),
                        order_id: Set(order.id),
                        product_id: Set(item.product_id),
                        quantity: Set(item.quantity),
                        unit_price: Set(item.unit_price),
                    };
                    order_item.insert(txn).await?;

                    // Update product stock
                    let product = Product::find_by_id(item.product_id)
                        .one(txn)
                        .await?
                        .ok_or(DbErr::RecordNotFound("Product not found".into()))?;

                    let mut active_product: product::ActiveModel = product.into();
                    let current_stock: i32 = active_product.stock_quantity.clone().unwrap();
                    active_product.stock_quantity = Set(current_stock - item.quantity);
                    active_product.update(txn).await?;
                }

                Ok(order)
            })
        }).await?;

        Ok(result)
    }
}
```

## Batch Operations

```rust
impl SeaOrmProductRepository {
    /// Batch update status
    pub async fn batch_update_status(
        &self,
        ids: Vec<Uuid>,
        status: product::ProductStatus,
    ) -> Result<u64, RepositoryError> {
        let result = Product::update_many()
            .col_expr(product::Column::Status, Expr::value(status))
            .col_expr(product::Column::UpdatedAt, Expr::value(chrono::Utc::now()))
            .filter(product::Column::Id.is_in(ids))
            .exec(&self.db)
            .await?;

        Ok(result.rows_affected)
    }

    /// Batch insert
    pub async fn batch_insert(
        &self,
        products: Vec<CreateProductInput>,
    ) -> Result<InsertResult<product::ActiveModel>, RepositoryError> {
        let now = chrono::Utc::now();

        let models: Vec<product::ActiveModel> = products
            .into_iter()
            .map(|input| product::ActiveModel {
                id: Set(Uuid::new_v4()),
                name: Set(input.name.clone()),
                slug: Set(slug::slugify(&input.name)),
                description: Set(input.description),
                price: Set(input.price),
                compare_price: Set(input.compare_price),
                status: Set(product::ProductStatus::Draft),
                category_id: Set(input.category_id),
                owner_id: Set(input.owner_id),
                stock_quantity: Set(input.stock_quantity.unwrap_or(0)),
                created_at: Set(now),
                updated_at: Set(now),
                deleted_at: Set(None),
            })
            .collect();

        let result = Product::insert_many(models)
            .exec(&self.db)
            .await?;

        Ok(result)
    }
}
```

## Raw SQL

```rust
use sea_orm::{FromQueryResult, Statement};

#[derive(Debug, FromQueryResult)]
pub struct CategoryStats {
    pub category_id: Uuid,
    pub product_count: i64,
    pub avg_price: Decimal,
}

impl SeaOrmProductRepository {
    pub async fn get_category_stats(&self) -> Result<Vec<CategoryStats>, RepositoryError> {
        let result = CategoryStats::find_by_statement(Statement::from_sql_and_values(
            sea_orm::DatabaseBackend::Postgres,
            r#"
            SELECT
                category_id,
                COUNT(*) as product_count,
                AVG(price) as avg_price
            FROM products
            WHERE deleted_at IS NULL
            GROUP BY category_id
            "#,
            vec![],
        ))
        .all(&self.db)
        .await?;

        Ok(result)
    }
}
```

## Migrations

```rust
// migration/src/m20240101_000001_create_products.rs
use sea_orm_migration::prelude::*;

#[derive(DeriveMigrationName)]
pub struct Migration;

#[async_trait::async_trait]
impl MigrationTrait for Migration {
    async fn up(&self, manager: &SchemaManager) -> Result<(), DbErr> {
        // Create enum type
        manager
            .create_type(
                Type::create()
                    .as_enum(ProductStatus::Table)
                    .values([
                        ProductStatus::Draft,
                        ProductStatus::Active,
                        ProductStatus::Inactive,
                        ProductStatus::Archived,
                    ])
                    .to_owned(),
            )
            .await?;

        // Create table
        manager
            .create_table(
                Table::create()
                    .table(Products::Table)
                    .if_not_exists()
                    .col(ColumnDef::new(Products::Id).uuid().not_null().primary_key())
                    .col(ColumnDef::new(Products::Name).string().not_null())
                    .col(ColumnDef::new(Products::Slug).string().not_null().unique_key())
                    .col(ColumnDef::new(Products::Description).text())
                    .col(ColumnDef::new(Products::Price).decimal().not_null())
                    .col(ColumnDef::new(Products::ComparePrice).decimal())
                    .col(
                        ColumnDef::new(Products::Status)
                            .enumeration(ProductStatus::Table, [
                                ProductStatus::Draft,
                                ProductStatus::Active,
                                ProductStatus::Inactive,
                                ProductStatus::Archived,
                            ])
                            .not_null()
                            .default("draft"),
                    )
                    .col(ColumnDef::new(Products::CategoryId).uuid().not_null())
                    .col(ColumnDef::new(Products::OwnerId).uuid().not_null())
                    .col(ColumnDef::new(Products::StockQuantity).integer().not_null().default(0))
                    .col(ColumnDef::new(Products::CreatedAt).timestamp_with_time_zone().not_null())
                    .col(ColumnDef::new(Products::UpdatedAt).timestamp_with_time_zone().not_null())
                    .col(ColumnDef::new(Products::DeletedAt).timestamp_with_time_zone())
                    .foreign_key(
                        ForeignKey::create()
                            .from(Products::Table, Products::CategoryId)
                            .to(Categories::Table, Categories::Id),
                    )
                    .foreign_key(
                        ForeignKey::create()
                            .from(Products::Table, Products::OwnerId)
                            .to(Users::Table, Users::Id),
                    )
                    .to_owned(),
            )
            .await?;

        // Create indexes
        manager
            .create_index(
                Index::create()
                    .table(Products::Table)
                    .name("idx_products_category")
                    .col(Products::CategoryId)
                    .to_owned(),
            )
            .await?;

        Ok(())
    }

    async fn down(&self, manager: &SchemaManager) -> Result<(), DbErr> {
        manager.drop_table(Table::drop().table(Products::Table).to_owned()).await?;
        manager.drop_type(Type::drop().name(ProductStatus::Table).to_owned()).await?;
        Ok(())
    }
}
```

## Best Practices

1. **Use ActiveModel**: For inserts and updates with partial fields
2. **Define Relations**: Use DeriveRelation for associations
3. **Paginate queries**: Use built-in paginator for large datasets
4. **Transactions**: Use `transaction()` for atomic operations
5. **Soft deletes**: Handle with filter conditions
6. **Eager loading**: Use `find_with_related` to avoid N+1 queries
7. **Migrations**: Use sea-orm-cli for schema management
