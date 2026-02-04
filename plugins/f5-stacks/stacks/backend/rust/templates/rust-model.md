---
name: rust-model
description: Domain model/entity template
applies_to: rust
variables:
  - name: entity_name
    description: Entity name (e.g., User, Product, Order)
  - name: table_name
    description: Database table name (e.g., users, products)
  - name: fields
    description: List of fields with types
---

# Rust Model Template

## Domain Entity

```rust
// src/domain/{{entity_name | snake_case}}/entity.rs

use chrono::{DateTime, Utc};
use rust_decimal::Decimal;
use serde::{Deserialize, Serialize};
use uuid::Uuid;

use crate::domain::common::{ValidationError, ValidationResult};

/// {{entity_name}} domain entity
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct {{entity_name}} {
    id: {{entity_name}}Id,
    {% for field in fields %}
    {{field.name}}: {{field.type}},
    {% endfor %}
    created_at: DateTime<Utc>,
    updated_at: DateTime<Utc>,
}

/// Strongly-typed ID for {{entity_name}}
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(transparent)]
pub struct {{entity_name}}Id(Uuid);

impl {{entity_name}}Id {
    pub fn new() -> Self {
        Self(Uuid::new_v4())
    }

    pub fn from_uuid(uuid: Uuid) -> Self {
        Self(uuid)
    }

    pub fn as_uuid(&self) -> &Uuid {
        &self.0
    }
}

impl Default for {{entity_name}}Id {
    fn default() -> Self {
        Self::new()
    }
}

impl std::fmt::Display for {{entity_name}}Id {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.0)
    }
}

impl From<Uuid> for {{entity_name}}Id {
    fn from(uuid: Uuid) -> Self {
        Self(uuid)
    }
}

impl From<{{entity_name}}Id> for Uuid {
    fn from(id: {{entity_name}}Id) -> Self {
        id.0
    }
}

impl {{entity_name}} {
    /// Create a new {{entity_name}} with validation
    pub fn new(
        {% for field in fields %}
        {{field.name}}: {{field.type}},
        {% endfor %}
    ) -> ValidationResult<Self> {
        let mut errors = Vec::new();

        // Validate required fields
        {% for field in fields %}
        {% if field.required %}
        if {{field.name}}.is_empty() {
            errors.push(ValidationError::MissingField("{{field.name}}".to_string()));
        }
        {% endif %}
        {% endfor %}

        if !errors.is_empty() {
            return Err(errors);
        }

        let now = Utc::now();
        Ok(Self {
            id: {{entity_name}}Id::new(),
            {% for field in fields %}
            {{field.name}},
            {% endfor %}
            created_at: now,
            updated_at: now,
        })
    }

    /// Reconstruct from persistence layer
    pub fn from_persistence(
        id: Uuid,
        {% for field in fields %}
        {{field.name}}: {{field.type}},
        {% endfor %}
        created_at: DateTime<Utc>,
        updated_at: DateTime<Utc>,
    ) -> Self {
        Self {
            id: {{entity_name}}Id::from_uuid(id),
            {% for field in fields %}
            {{field.name}},
            {% endfor %}
            created_at,
            updated_at,
        }
    }

    // Getters
    pub fn id(&self) -> {{entity_name}}Id {
        self.id
    }

    {% for field in fields %}
    pub fn {{field.name}}(&self) -> &{{field.type}} {
        &self.{{field.name}}
    }
    {% endfor %}

    pub fn created_at(&self) -> DateTime<Utc> {
        self.created_at
    }

    pub fn updated_at(&self) -> DateTime<Utc> {
        self.updated_at
    }

    // Mutators with validation
    {% for field in fields %}
    {% if field.mutable %}
    pub fn set_{{field.name}}(&mut self, {{field.name}}: {{field.type}}) -> Result<(), ValidationError> {
        {% if field.validation %}
        // Validation logic for {{field.name}}
        {{field.validation}}
        {% endif %}
        self.{{field.name}} = {{field.name}};
        self.updated_at = Utc::now();
        Ok(())
    }
    {% endif %}
    {% endfor %}
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_create_{{entity_name | snake_case}}_success() {
        let result = {{entity_name}}::new(
            {% for field in fields %}
            /* {{field.name}} */ test_value(),
            {% endfor %}
        );

        assert!(result.is_ok());
        let entity = result.unwrap();
        assert!(entity.id().as_uuid().version_num() == 4);
    }

    #[test]
    fn test_{{entity_name | snake_case}}_id_equality() {
        let uuid = Uuid::new_v4();
        let id1 = {{entity_name}}Id::from_uuid(uuid);
        let id2 = {{entity_name}}Id::from_uuid(uuid);

        assert_eq!(id1, id2);
    }
}
```

## SQLx Model

```rust
// src/infrastructure/persistence/models/{{entity_name | snake_case}}.rs

use chrono::{DateTime, Utc};
use sqlx::FromRow;
use uuid::Uuid;

use crate::domain::{{entity_name | snake_case}}::{{entity_name}};

/// Database model for {{entity_name}}
#[derive(Debug, Clone, FromRow)]
pub struct {{entity_name}}Model {
    pub id: Uuid,
    {% for field in fields %}
    pub {{field.name}}: {{field.db_type | default: field.type}},
    {% endfor %}
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

impl From<{{entity_name}}Model> for {{entity_name}} {
    fn from(model: {{entity_name}}Model) -> Self {
        {{entity_name}}::from_persistence(
            model.id,
            {% for field in fields %}
            model.{{field.name}},
            {% endfor %}
            model.created_at,
            model.updated_at,
        )
    }
}

impl From<&{{entity_name}}> for {{entity_name}}Model {
    fn from(entity: &{{entity_name}}) -> Self {
        Self {
            id: *entity.id().as_uuid(),
            {% for field in fields %}
            {{field.name}}: entity.{{field.name}}().clone(),
            {% endfor %}
            created_at: entity.created_at(),
            updated_at: entity.updated_at(),
        }
    }
}
```

## Diesel Model

```rust
// src/infrastructure/persistence/models/{{entity_name | snake_case}}.rs

use chrono::{DateTime, Utc};
use diesel::prelude::*;
use uuid::Uuid;

use crate::schema::{{table_name}};

/// Queryable model for reading from database
#[derive(Debug, Clone, Queryable, Selectable, Identifiable)]
#[diesel(table_name = {{table_name}})]
#[diesel(check_for_backend(diesel::pg::Pg))]
pub struct {{entity_name}}Model {
    pub id: Uuid,
    {% for field in fields %}
    pub {{field.name}}: {{field.db_type | default: field.type}},
    {% endfor %}
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

/// Insertable model for creating new records
#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = {{table_name}})]
pub struct New{{entity_name}} {
    pub id: Uuid,
    {% for field in fields %}
    pub {{field.name}}: {{field.db_type | default: field.type}},
    {% endfor %}
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

/// Changeset for updating records
#[derive(Debug, Clone, AsChangeset)]
#[diesel(table_name = {{table_name}})]
pub struct {{entity_name}}Changeset {
    {% for field in fields %}
    {% if field.mutable %}
    pub {{field.name}}: Option<{{field.db_type | default: field.type}}>,
    {% endif %}
    {% endfor %}
    pub updated_at: DateTime<Utc>,
}
```

## SeaORM Entity

```rust
// src/infrastructure/persistence/entities/{{entity_name | snake_case}}.rs

use sea_orm::entity::prelude::*;
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, PartialEq, Eq, DeriveEntityModel, Serialize, Deserialize)]
#[sea_orm(table_name = "{{table_name}}")]
pub struct Model {
    #[sea_orm(primary_key, auto_increment = false)]
    pub id: Uuid,
    {% for field in fields %}
    pub {{field.name}}: {{field.sea_orm_type | default: field.type}},
    {% endfor %}
    pub created_at: DateTimeUtc,
    pub updated_at: DateTimeUtc,
}

#[derive(Copy, Clone, Debug, EnumIter, DeriveRelation)]
pub enum Relation {
    // Define relations here
    // #[sea_orm(has_many = "super::order::Entity")]
    // Orders,
}

impl ActiveModelBehavior for ActiveModel {}
```
