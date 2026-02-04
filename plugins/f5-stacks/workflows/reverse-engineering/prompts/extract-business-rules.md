# Prompt: Extract Business Rules

> **Purpose**: Extract all business rules from codebase
> **Input**: Models, Controllers, Services, Requests
> **Output**: Categorized business rules documentation

---

## Prompt Template

```
Analyze the codebase at [PROJECT_PATH] and extract ALL business rules.

Look in these locations:
1. app/Models/ - Model methods, boot(), constants
2. app/Http/Controllers/ - Action logic, conditions
3. app/Services/ - Business logic services
4. app/Http/Requests/ - Validation rules
5. app/Traits/ - Reusable business logic
6. app/Observers/ - Model lifecycle rules
7. app/Events/ & app/Listeners/ - Event-driven rules

---

## Categories to Extract

### 1. Validation Rules
From FormRequest classes and inline validation:
- Field-level validation (required, max, min, etc.)
- Cross-field validation
- Custom validation rules
- Conditional validation

Format:
| Rule ID | Entity | Field | Rule | Source File |
|---------|--------|-------|------|-------------|

### 2. Calculation Rules
How values are computed:
- Totals, subtotals
- Tax calculations
- Currency conversions
- Aggregations

Format:
| Rule ID | Description | Formula | Source |
|---------|-------------|---------|--------|

### 3. State Transition Rules
When entities can change state:
- Current state → New state
- Who can trigger
- Conditions required
- Side effects

Format:
| Rule ID | Entity | From | To | Condition | Actor |
|---------|--------|------|-----|-----------|-------|

### 4. Access Control Rules
Who can do what:
- Role-based permissions
- Ownership checks
- Status-based access
- Time-based access

Format:
| Rule ID | Action | Entity | Condition | Roles |
|---------|--------|--------|-----------|-------|

### 5. Workflow Rules
Sequential processes:
- Step dependencies
- Approval flows
- Notification triggers

Format:
| Rule ID | Trigger | Condition | Action | Next Step |
|---------|---------|-----------|--------|-----------|

### 6. Data Integrity Rules
Maintaining consistent data:
- Cascade behaviors
- Referential integrity
- Unique constraints
- Business-level constraints

Format:
| Rule ID | Description | Enforcement |
|---------|-------------|-------------|

### 7. Notification Rules
When to send notifications:
- Email triggers
- In-app notifications
- Recipients logic

Format:
| Rule ID | Event | Recipients | Template |
|---------|-------|------------|----------|

---

## Output Format

```markdown
# Business Rules Registry

## 1. Validation Rules

### VR-001: [Rule Name]
- **Entity**: [Entity name]
- **Field**: [Field name]
- **Rule**: [Description]
- **Source**: `[file:line]`

### VR-002: ...

## 2. Calculation Rules

### CR-001: [Rule Name]
- **Description**: [What is calculated]
- **Formula**: `[formula or pseudo-code]`
- **Source**: `[file:method]`

### CR-002: ...

## 3. State Transition Rules

### STR-001: [Transition Name]
- **Entity**: [Entity name]
- **From State**: [state]
- **To State**: [state]
- **Condition**: [when allowed]
- **Actor**: [who can trigger]
- **Side Effects**: [what else happens]
- **Source**: `[file:method]`

... [continue for all categories]
```

---

## Example Extraction

From `Quotation.php`:

```php
public function isDeletable()
{
    $isAdmin = checkUserIsAdmin();
    $deletable = ($this->creator_id == working_company_id()
        && $this->status == self::STATUS_DRAFT || ($user && ($this->status == self::STATUS_ACCEPTED || $this->status == self::STATUS_POSTED)));
    // ...
}
```

Extracted Rule:
```markdown
### ACR-001: Quotation Delete Permission
- **Action**: Delete
- **Entity**: Quotation
- **Conditions**:
  - Creator can delete if status = draft
  - Admin can delete if status = accepted OR posted
  - Seller can delete if status = draft OR cancelled
- **Source**: `app/Models/Quotation.php:isDeletable()`
```

---

## Code Pattern Recognition

### Laravel Validation Patterns
```php
// In FormRequest
public function rules() {
    return [
        'field' => 'required|max:255',  // Extract this
    ];
}

// Inline validation
$request->validate([
    'field' => 'required',  // Extract this
]);
```

### State Check Patterns
```php
// Status checks
if ($this->status == 'draft') { }
if (in_array($this->status, ['draft', 'posted'])) { }

// Permission checks  
if ($this->creator_id == working_company_id()) { }
```

### Calculation Patterns
```php
// Direct calculation
$total = $subtotal + $tax;

// Aggregation
$sum = $this->items->sum('amount');

// Computed attribute
public function getTotalAttribute() {
    return $this->amount + $this->tax;
}
```

---

## Checklist

- [ ] All FormRequest classes checked
- [ ] All model methods reviewed
- [ ] All service classes analyzed
- [ ] All controller actions examined
- [ ] All observers checked
- [ ] All event listeners reviewed
- [ ] Rules categorized correctly
- [ ] Source references included
- [ ] Edge cases documented
```
