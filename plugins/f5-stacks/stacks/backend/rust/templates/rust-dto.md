---
name: rust-dto
description: Data Transfer Object template with validation
applies_to: rust
variables:
  - name: entity_name
    description: Entity name (e.g., User, Product)
  - name: fields
    description: List of DTO fields with validation rules
---

# Rust DTO Template

## Request DTOs

```rust
// src/application/{{entity_name | snake_case}}/dto.rs

use serde::{Deserialize, Serialize};
use uuid::Uuid;
use validator::Validate;

/// DTO for creating a new {{entity_name}}
#[derive(Debug, Clone, Deserialize, Validate)]
pub struct Create{{entity_name}}Dto {
    {% for field in fields %}
    {% if field.create %}
    #[validate({{field.validation}})]
    pub {{field.name}}: {{field.type}},
    {% endif %}
    {% endfor %}
}

/// DTO for updating an existing {{entity_name}}
#[derive(Debug, Clone, Deserialize, Validate)]
pub struct Update{{entity_name}}Dto {
    {% for field in fields %}
    {% if field.update %}
    #[validate({{field.validation}})]
    #[serde(skip_serializing_if = "Option::is_none")]
    pub {{field.name}}: Option<{{field.type}}>,
    {% endif %}
    {% endfor %}
}

/// Query parameters for listing {{entity_name}}s
#[derive(Debug, Clone, Deserialize, Default)]
pub struct {{entity_name}}ListQuery {
    /// Page number (1-indexed)
    pub page: Option<u32>,

    /// Items per page (max 100)
    pub per_page: Option<u32>,

    /// Sort field
    pub sort_by: Option<{{entity_name}}SortField>,

    /// Sort direction
    pub sort_order: Option<SortOrder>,

    /// Search query
    pub search: Option<String>,

    /// Filter by status
    pub status: Option<String>,

    // Add more filter fields as needed
}

#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum {{entity_name}}SortField {
    Name,
    CreatedAt,
    UpdatedAt,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum SortOrder {
    Asc,
    Desc,
}

impl Default for SortOrder {
    fn default() -> Self {
        Self::Desc
    }
}
```

## Response DTOs

```rust
// src/application/{{entity_name | snake_case}}/dto.rs

use chrono::{DateTime, Utc};
use serde::Serialize;
use uuid::Uuid;

use crate::domain::{{entity_name | snake_case}}::entity::{{entity_name}};

/// Response DTO for {{entity_name}}
#[derive(Debug, Clone, Serialize)]
pub struct {{entity_name}}Response {
    pub id: Uuid,
    {% for field in fields %}
    pub {{field.name}}: {{field.response_type | default: field.type}},
    {% endfor %}
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

impl From<{{entity_name}}> for {{entity_name}}Response {
    fn from(entity: {{entity_name}}) -> Self {
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

impl From<&{{entity_name}}> for {{entity_name}}Response {
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

/// Summary response (for lists)
#[derive(Debug, Clone, Serialize)]
pub struct {{entity_name}}SummaryResponse {
    pub id: Uuid,
    pub name: String,
    pub created_at: DateTime<Utc>,
}

impl From<{{entity_name}}> for {{entity_name}}SummaryResponse {
    fn from(entity: {{entity_name}}) -> Self {
        Self {
            id: *entity.id().as_uuid(),
            name: entity.name().to_string(),
            created_at: entity.created_at(),
        }
    }
}

/// Paginated list response
#[derive(Debug, Clone, Serialize)]
pub struct {{entity_name}}ListResponse {
    pub items: Vec<{{entity_name}}Response>,
    pub total: i64,
    pub page: u32,
    pub per_page: u32,
    pub total_pages: u32,
}

impl {{entity_name}}ListResponse {
    pub fn new(items: Vec<{{entity_name}}>, total: i64, page: u32, per_page: u32) -> Self {
        let total_pages = ((total as f64) / (per_page as f64)).ceil() as u32;
        Self {
            items: items.into_iter().map({{entity_name}}Response::from).collect(),
            total,
            page,
            per_page,
            total_pages,
        }
    }
}

/// Response with embedded relations
#[derive(Debug, Clone, Serialize)]
pub struct {{entity_name}}DetailResponse {
    #[serde(flatten)]
    pub {{entity_name | snake_case}}: {{entity_name}}Response,

    // Embedded relations
    // pub related_items: Vec<RelatedItemResponse>,
    // pub owner: UserSummaryResponse,
}
```

## Custom Validation

```rust
// src/application/{{entity_name | snake_case}}/dto.rs

use validator::{Validate, ValidationError};

impl Create{{entity_name}}Dto {
    /// Additional business rule validation
    pub fn validate_business_rules(&self) -> Result<(), Vec<ValidationError>> {
        let mut errors = Vec::new();

        // Example: Custom validation logic
        // if self.start_date > self.end_date {
        //     errors.push(ValidationError::new("date_order")
        //         .with_message("Start date must be before end date".into()));
        // }

        if errors.is_empty() {
            Ok(())
        } else {
            Err(errors)
        }
    }

    /// Full validation including standard and business rules
    pub fn validate_full(&self) -> Result<(), Vec<String>> {
        let mut all_errors = Vec::new();

        // Standard validation
        if let Err(errors) = self.validate() {
            for (field, field_errors) in errors.field_errors() {
                for error in field_errors {
                    all_errors.push(format!(
                        "{}: {}",
                        field,
                        error.message.clone().unwrap_or_default()
                    ));
                }
            }
        }

        // Business rule validation
        if let Err(errors) = self.validate_business_rules() {
            for error in errors {
                all_errors.push(
                    error.message.map(|m| m.to_string()).unwrap_or_default()
                );
            }
        }

        if all_errors.is_empty() {
            Ok(())
        } else {
            Err(all_errors)
        }
    }
}
```

## Nested DTOs

```rust
// src/application/{{entity_name | snake_case}}/dto.rs

/// DTO with nested objects
#[derive(Debug, Clone, Deserialize, Validate)]
pub struct Create{{entity_name}}WithRelatedDto {
    #[validate(length(min = 2, max = 200))]
    pub name: String,

    #[validate(nested)]
    pub address: Option<AddressDto>,

    #[validate(length(min = 1, message = "At least one item is required"))]
    #[validate(nested)]
    pub items: Vec<ItemDto>,
}

#[derive(Debug, Clone, Deserialize, Validate)]
pub struct AddressDto {
    #[validate(length(min = 2, max = 100))]
    pub street: String,

    #[validate(length(min = 2, max = 50))]
    pub city: String,

    #[validate(length(equal = 2))]
    pub country_code: String,

    #[validate(length(min = 5, max = 10))]
    pub postal_code: String,
}

#[derive(Debug, Clone, Deserialize, Validate)]
pub struct ItemDto {
    pub product_id: Uuid,

    #[validate(range(min = 1, max = 1000))]
    pub quantity: i32,
}
```

## DTO Builders (for testing)

```rust
#[cfg(test)]
pub mod builders {
    use super::*;

    pub struct Create{{entity_name}}DtoBuilder {
        dto: Create{{entity_name}}Dto,
    }

    impl Create{{entity_name}}DtoBuilder {
        pub fn new() -> Self {
            Self {
                dto: Create{{entity_name}}Dto {
                    name: "Test {{entity_name}}".to_string(),
                    // ... default values for all fields
                },
            }
        }

        pub fn with_name(mut self, name: &str) -> Self {
            self.dto.name = name.to_string();
            self
        }

        // Add more builder methods...

        pub fn build(self) -> Create{{entity_name}}Dto {
            self.dto
        }
    }

    impl Default for Create{{entity_name}}DtoBuilder {
        fn default() -> Self {
            Self::new()
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use super::builders::*;

    #[test]
    fn test_valid_create_dto() {
        let dto = Create{{entity_name}}DtoBuilder::new()
            .with_name("Valid Name")
            .build();

        assert!(dto.validate().is_ok());
    }

    #[test]
    fn test_invalid_name_too_short() {
        let dto = Create{{entity_name}}DtoBuilder::new()
            .with_name("A")
            .build();

        assert!(dto.validate().is_err());
    }
}
```
