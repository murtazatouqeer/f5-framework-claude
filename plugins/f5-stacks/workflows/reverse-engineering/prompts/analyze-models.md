# Prompt: Analyze Laravel Models

> **Purpose**: Extract entity information from Laravel Eloquent models
> **Input**: Model files directory
> **Output**: Entity catalog with relationships and business logic

---

## Prompt Template

```
Analyze all Eloquent models in [PROJECT_PATH]/app/Models/

For each model, extract:

## 1. Basic Information
- Model name
- Table name (if different from convention)
- Primary key
- Timestamps (created_at, updated_at)
- Soft deletes (deleted_at)

## 2. Fillable/Guarded Fields
List all $fillable or $guarded fields with their types and purposes.

## 3. Casts
Document all $casts definitions:
- Field name → Cast type
- Custom cast classes if any

## 4. Relationships
For each relationship method:
- Type (hasOne, hasMany, belongsTo, belongsToMany, morphTo, morphMany, etc.)
- Related model
- Foreign key
- Local key
- Pivot table (for many-to-many)

## 5. Scopes
List all query scopes:
- Scope name
- Parameters
- Purpose/filter logic

## 6. Accessors/Mutators
List all attribute accessors and mutators:
- Attribute name
- Logic/transformation

## 7. Business Methods
Identify methods that contain business logic:
- Method name
- Purpose
- Key conditions/rules

## 8. Constants
List all class constants:
- Constant name
- Value
- Usage

## 9. Traits Used
List all traits and their purposes:
- Trait name
- What it provides

## 10. Events/Observers
Document model events:
- boot() method logic
- Observer methods

---

## Output Format

Create a markdown file for each major entity with:

```markdown
# Entity: [ModelName]

## Overview
[Brief description of what this entity represents]

## Database Table
- Table: `[table_name]`
- Primary Key: `id`
- Soft Deletes: Yes/No

## Attributes
| Attribute | Type | Nullable | Default | Description |
|-----------|------|----------|---------|-------------|
| ... | ... | ... | ... | ... |

## Relationships
| Relationship | Type | Related Model | Keys |
|--------------|------|---------------|------|
| ... | ... | ... | ... |

## Business Rules
### [Rule Category]
- Rule 1
- Rule 2

## Status/State
| Status | Value | Description |
|--------|-------|-------------|
| ... | ... | ... |
```

---

## Example Analysis

Input: `app/Models/Quotation.php`

Output:
```markdown
# Entity: Quotation

## Overview
Represents a price quotation for software development services.

## Constants (States)
| Constant | Value | Description |
|----------|-------|-------------|
| STATUS_DRAFT | 'draft' | Initial state |
| STATUS_POSTED | 'posted' | Sent to other party |
| STATUS_ACCEPTED | 'accepted' | Approved |
| STATUS_FEEDBACKED | 'feedbacked' | Needs revision |
| STATUS_CANCELLED | 'cancelled' | Cancelled |
| STATUS_EXPIRED | 'expired' | Past expiry date |

## Key Relationships
| Relationship | Type | Model | Foreign Key |
|--------------|------|-------|-------------|
| buyer | belongsTo | Company | buyer_id |
| seller | belongsTo | Company | seller_id |
| items | hasMany | QuotationItem | quotation_id |
| milestones | hasMany | Payment | payable_id |
| project | belongsTo | Project | project_id |

## Business Methods
### isDeletable()
Returns true if:
- Creator can delete draft quotations
- Admin can delete posted/accepted quotations
- Seller can delete draft/cancelled quotations

### isEditable()
Returns true if:
- Creator can edit draft quotations
- Seller can edit posted/feedbacked quotations
```
```

---

## Checklist

- [ ] All models in app/Models/ analyzed
- [ ] Relationships mapped correctly
- [ ] Business methods documented
- [ ] State/status constants identified
- [ ] Traits and their effects documented
- [ ] Observer/event logic captured
