---
name: rust-model-generator
description: Generates domain entities and database models
applies_to: rust
inputs:
  - name: entity_name
    description: Entity name (e.g., User, Product)
    required: true
  - name: fields
    description: List of fields with types and validations
    required: true
  - name: table_name
    description: Database table name
    required: false
  - name: orm
    description: ORM to use (sqlx, diesel, sea-orm)
    required: false
    default: sqlx
---

# Rust Model Generator Agent

## Purpose

Generate domain entities with:
- Strongly-typed IDs
- Validation logic
- Database model mappings
- Conversion traits
- Unit tests

## Generation Process

### 1. Parse Field Specifications

```yaml
field_spec:
  name: string          # Field name
  type: string          # Rust type
  required: boolean     # Is required
  validation: string    # Validation rules
  db_type: string       # Database type override
  mutable: boolean      # Can be updated
```

### 2. Generate Domain Entity

```rust
// src/domain/{{entity_name | snake_case}}/entity.rs

use chrono::{DateTime, Utc};
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

/// Strongly-typed ID
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
    /// Create new {{entity_name}} with validation
    pub fn new(
        {% for field in fields %}
        {{field.name}}: {{field.type}},
        {% endfor %}
    ) -> ValidationResult<Self> {
        let mut errors = Vec::new();

        {% for field in fields %}
        {% if field.validation %}
        // Validate {{field.name}}
        {{field.validation_code}}
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

    /// Reconstruct from persistence
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
    pub fn {{field.name}}(&self) -> {% if field.type == "String" %}&str{% else %}&{{field.type}}{% endif %} {
        {% if field.type == "String" %}&self.{{field.name}}{% else %}&self.{{field.name}}{% endif %}
    }
    {% endfor %}

    pub fn created_at(&self) -> DateTime<Utc> {
        self.created_at
    }

    pub fn updated_at(&self) -> DateTime<Utc> {
        self.updated_at
    }

    // Mutators
    {% for field in fields %}
    {% if field.mutable %}
    pub fn set_{{field.name}}(&mut self, value: {{field.type}}) -> Result<(), ValidationError> {
        {% if field.validation %}
        // Validation
        {{field.validation_code}}
        {% endif %}
        self.{{field.name}} = value;
        self.updated_at = Utc::now();
        Ok(())
    }
    {% endif %}
    {% endfor %}
}

#[cfg(test)]
mod tests {
    use super::*;

    fn valid_{{entity_name | snake_case}}_params() -> ({% for field in fields %}{{field.type}},{% endfor %}) {
        (
            {% for field in fields %}
            {{field.test_value}},
            {% endfor %}
        )
    }

    #[test]
    fn test_create_valid_{{entity_name | snake_case}}() {
        let ({% for field in fields %}{{field.name}},{% endfor %}) = valid_{{entity_name | snake_case}}_params();

        let result = {{entity_name}}::new(
            {% for field in fields %}
            {{field.name}},
            {% endfor %}
        );

        assert!(result.is_ok());
    }

    {% for field in fields %}
    {% if field.required %}
    #[test]
    fn test_{{field.name}}_required() {
        // Test that empty/missing {{field.name}} fails validation
    }
    {% endif %}
    {% endfor %}

    #[test]
    fn test_id_uniqueness() {
        let id1 = {{entity_name}}Id::new();
        let id2 = {{entity_name}}Id::new();
        assert_ne!(id1, id2);
    }
}
```

### 3. Generate Database Model (SQLx)

```rust
// src/infrastructure/persistence/models/{{entity_name | snake_case}}.rs

use chrono::{DateTime, Utc};
use sqlx::FromRow;
use uuid::Uuid;

use crate::domain::{{entity_name | snake_case}}::{{entity_name}};

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
            {{field.name}}: entity.{{field.name}}(){% if field.type == "String" %}.to_string(){% else %}.clone(){% endif %},
            {% endfor %}
            created_at: entity.created_at(),
            updated_at: entity.updated_at(),
        }
    }
}
```

### 4. Generate Migration

```sql
-- migrations/{{timestamp}}_create_{{table_name}}.sql

CREATE TABLE {{table_name}} (
    id UUID PRIMARY KEY,
    {% for field in fields %}
    {{field.name}} {{field.sql_type}} {% if field.required %}NOT NULL{% endif %},
    {% endfor %}
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
{% for field in fields %}
{% if field.indexed %}
CREATE INDEX idx_{{table_name}}_{{field.name}} ON {{table_name}} ({{field.name}});
{% endif %}
{% endfor %}

-- Triggers
CREATE OR REPLACE FUNCTION update_{{table_name}}_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_{{table_name}}_updated_at
    BEFORE UPDATE ON {{table_name}}
    FOR EACH ROW
    EXECUTE FUNCTION update_{{table_name}}_updated_at();
```

## Usage

```bash
# Generate model from specification
f5 generate model User \
  --fields "name:String:required,email:String:required:unique,role:String"

# Generate with custom table name
f5 generate model Product \
  --table products \
  --fields "name:String:required,price:Decimal:required,stock:i32"

# Generate for specific ORM
f5 generate model Order \
  --orm diesel \
  --fields "user_id:Uuid:required,total:Decimal:required,status:OrderStatus"
```

## Output Files

```
src/domain/{{entity_name | snake_case}}/
├── mod.rs
├── entity.rs
└── error.rs

src/infrastructure/persistence/models/
├── mod.rs (updated)
└── {{entity_name | snake_case}}.rs

migrations/
└── {{timestamp}}_create_{{table_name}}.sql
```
