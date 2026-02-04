---
description: Generate design documents and specifications (D1-D4)
argument-hint: <generate|validate|spec> <type> [module]
---

# /f5-design - Unified Design & Specification Command

**Consolidated command** that replaces:
- `/f5-spec` → `/f5-design spec`

Manage and generate design documents (Basic Design 基本設計, Detail Design 詳細設計) and specifications (SRS, Use Cases, Business Rules).

## ARGUMENTS
The user's request is: $ARGUMENTS

## MODE DETECTION

| Pattern | Mode | Description |
|---------|------|-------------|
| `spec <action>` | SPEC | SRS, Use Cases, Business Rules (D1-D2) |
| `<other>` (default) | DESIGN | Architecture, DB, API, Screens (D3-D4) |

---

## ⚠️ CRITICAL OUTPUT RULES

**KHÔNG ĐƯỢC tạo files ở `docs/`, `output/`, hoặc thư mục khác.**

**BẮT BUỘC tuân theo cấu trúc sau:**

### Basic Design (D3)
| Command | Document Type | Output Path |
|---------|--------------|-------------|
| `generate architecture` | Architecture | `.f5/specs/basic-design/v{VERSION}/system-architecture.md` |
| `generate tables` | Database (all) | `.f5/specs/basic-design/v{VERSION}/database/database-design.md` |
| `generate table <name>` | Database (single) | `.f5/specs/basic-design/v{VERSION}/database/{table-name}.md` |
| `generate api-list` | API (all) | `.f5/specs/basic-design/v{VERSION}/api/api-design.md` |
| `generate api <endpoint>` | API (single) | `.f5/specs/basic-design/v{VERSION}/api/{METHOD}-{endpoint}.md` |
| `generate screen-list` | Screens (all) | `.f5/specs/basic-design/v{VERSION}/screens/screen-list.md` |
| `generate screen <name>` | Screens (single) | `.f5/specs/basic-design/v{VERSION}/screens/{screen-name}.md` |
| `generate batch <name>` | Batch Specs | `.f5/specs/basic-design/v{VERSION}/batch/{batch-name}.md` |
| `generate erd` | ERD Diagram | `.f5/specs/basic-design/v{VERSION}/diagrams/erd.md` |

### Detail Design (D4)
| Command | Document Type | Output Path |
|---------|--------------|-------------|
| `generate screen-detail <name>` | Screen Details | `.f5/specs/detail-design/v{VERSION}/screens/{screen-name}.md` |
| `generate api-detail <endpoint>` | API Details | `.f5/specs/detail-design/v{VERSION}/api/{endpoint}.md` |
| `generate batch-detail <name>` | Batch Details | `.f5/specs/detail-design/v{VERSION}/batch/{batch-name}.md` |
| `generate component <name>` | Component Specs | `.f5/specs/detail-design/v{VERSION}/components/{component}.md` |

### Export
| Document Type | Output Path |
|--------------|-------------|
| Basic Design Export | `.f5/output/basic-design-v{VERSION}.{FORMAT}` |
| Detail Design Export | `.f5/output/detail-design-v{VERSION}.{FORMAT}` |

**VERSION format:** `v1.0.0`, `v1.1.0`, `v2.0.0`

**Ví dụ paths đúng:**
```
.f5/specs/basic-design/v1.0.0/system-architecture.md ✅
.f5/specs/basic-design/v1.0.0/database/database-design.md ✅
.f5/specs/basic-design/v1.0.0/api/api-design.md ✅
.f5/specs/basic-design/v1.0.0/screens/screen-list.md ✅
.f5/specs/detail-design/v1.0.0/screens/login.md ✅
```

**Ví dụ paths SAI:**
```
docs/Database-Design-v1.0.md ❌
.f5/specs/basic-design/v1.0.0/screen-list.md ❌  (missing screens/ folder!)
.f5/specs/basic-design/v1.0.0/api-design.md ❌  (missing api/ folder!)
basic-design.md ❌
```

## STEP 1: PARSE ACTION

| Action | Description |
|--------|-------------|
| `generate <type>` | Generate design document |
| `validate` | Validate design completeness |
| `trace` | Check traceability |
| `export` | Export to different formats |
| `status` | Show design status |

## ACTION: GENERATE

### Basic Design (基本設計) Documents

> ⚠️ **OUTPUT PATH REMINDER**: All files MUST be created in `.f5/specs/basic-design/v1.0.0/`
> - Architecture: `.f5/specs/basic-design/v1.0.0/system-architecture.md`
> - Database: `.f5/specs/basic-design/v1.0.0/database/`
> - API: `.f5/specs/basic-design/v1.0.0/api/`
> - Screens: `.f5/specs/basic-design/v1.0.0/screens/`
>
> **NEVER create files in `docs/` folder!**

#### System Architecture
```
/f5-design generate architecture [--type <type>]
```

Types: `system`, `network`, `deployment`, `security`

**Output:** `.f5/specs/basic-design/v{VERSION}/system-architecture.md`

#### Database Design

**Available Commands:**
```
/f5-design generate table <table-name>    # Single table definition
/f5-design generate tables                # ALL tables (comprehensive document)
/f5-design generate database              # Alias for 'tables'
```

**⚠️ MANDATORY OUTPUT PATHS:**

| Command | Output Path |
|---------|-------------|
| `generate table users` | `.f5/specs/basic-design/v1.0.0/database/users.md` |
| `generate tables` | `.f5/specs/basic-design/v1.0.0/database/database-design.md` |
| `generate database` | `.f5/specs/basic-design/v1.0.0/database/database-design.md` |

**✅ CORRECT paths:**
```
.f5/specs/basic-design/v1.0.0/database/database-design.md ✅
.f5/specs/basic-design/v1.0.0/database/users.md ✅
.f5/specs/basic-design/v1.0.0/database/orders.md ✅
```

**❌ WRONG paths (NEVER use):**
```
docs/Database-Design-v1.0.md ❌
.f5/specs/basic-design/v1.0.0/database-design.md ❌  (missing database/ folder!)
database.md ❌
```

**Template:**
```markdown
# Table Definition: {{TABLE_NAME}}

## Overview
| Property | Value |
|----------|-------|
| Table Name | {{TABLE_NAME}} |
| Schema | {{SCHEMA}} |
| Related Requirements | {{REQ_IDS}} |

## Columns
| # | Column | Type | Nullable | Default | Description |
|---|--------|------|----------|---------|-------------|
| 1 | id | BIGINT | NO | AUTO | Primary key |

## Indexes
| Name | Columns | Type | Description |
|------|---------|------|-------------|

## Foreign Keys
| Name | Column | References | On Delete |
|------|--------|------------|-----------|

## DDL
\`\`\`sql
CREATE TABLE {{TABLE_NAME}} (
  ...
);
\`\`\`
```

#### API Design

**Available Commands:**
```
/f5-design generate api <endpoint>        # Single API endpoint
/f5-design generate api-list              # ALL APIs (comprehensive document)
/f5-design generate apis                  # Alias for 'api-list'
```

**⚠️ MANDATORY OUTPUT PATHS:**

| Command | Output Path |
|---------|-------------|
| `generate api /users` | `.f5/specs/basic-design/v1.0.0/api/GET-users.md` |
| `generate api-list` | `.f5/specs/basic-design/v1.0.0/api/api-design.md` |
| `generate apis` | `.f5/specs/basic-design/v1.0.0/api/api-design.md` |

**✅ CORRECT paths:**
```
.f5/specs/basic-design/v1.0.0/api/api-design.md ✅
.f5/specs/basic-design/v1.0.0/api/GET-users.md ✅
.f5/specs/basic-design/v1.0.0/api/POST-auth-login.md ✅
```

**❌ WRONG paths (NEVER use):**
```
docs/API-Design-v1.0.md ❌
.f5/specs/basic-design/v1.0.0/api-design.md ❌  (missing api/ folder!)
api.md ❌
```

**Template:**
```markdown
# API: {{METHOD}} {{ENDPOINT}}

## Overview
| Property | Value |
|----------|-------|
| Method | {{METHOD}} |
| Endpoint | {{ENDPOINT}} |
| Related Requirements | {{REQ_IDS}} |

## Request
### Headers
| Name | Required | Description |
|------|----------|-------------|

### Parameters
| Name | Type | Required | Description |
|------|------|----------|-------------|

### Body
\`\`\`json
{
  "field": "value"
}
\`\`\`

## Response
### Success (200)
\`\`\`json
{
  "data": {}
}
\`\`\`

### Errors
| Code | Message | Description |
|------|---------|-------------|
| 400 | Bad Request | Invalid input |
| 401 | Unauthorized | Authentication required |
```

#### Screen Design

**Available Commands:**
```
/f5-design generate screen <screen-name>  # Single screen specification
/f5-design generate screen-list           # ALL screens (comprehensive document)
/f5-design generate screens               # Alias for 'screen-list'
```

Types for single screen: `list`, `detail`, `form`, `dashboard`

**⚠️ MANDATORY OUTPUT PATHS:**

| Command | Output Path |
|---------|-------------|
| `generate screen login` | `.f5/specs/basic-design/v1.0.0/screens/login.md` |
| `generate screen-list` | `.f5/specs/basic-design/v1.0.0/screens/screen-list.md` |
| `generate screens` | `.f5/specs/basic-design/v1.0.0/screens/screen-list.md` |

**✅ CORRECT paths:**
```
.f5/specs/basic-design/v1.0.0/screens/screen-list.md ✅
.f5/specs/basic-design/v1.0.0/screens/login.md ✅
.f5/specs/basic-design/v1.0.0/screens/dashboard.md ✅
```

**❌ WRONG paths (NEVER use):**
```
docs/Screen-List-v1.0.md ❌
.f5/specs/basic-design/v1.0.0/screen-list.md ❌  (missing screens/ folder!)
screens.md ❌
```

#### Batch Specification
```
/f5-design generate batch <batch-name>
```

**Output:** `.f5/specs/basic-design/v{VERSION}/batch/{batch-name}.md`

### Detail Design (詳細設計) Documents

> ⚠️ **OUTPUT PATH REMINDER**: All Detail Design files MUST be in `.f5/specs/detail-design/v1.0.0/`
> - Screen Details: `.f5/specs/detail-design/v1.0.0/screens/`
> - API Details: `.f5/specs/detail-design/v1.0.0/api/`
> - Batch Details: `.f5/specs/detail-design/v1.0.0/batch/`
> - Components: `.f5/specs/detail-design/v1.0.0/components/`
>
> **NEVER create files in `docs/` or root of `v1.0.0/`!**

#### Screen Detail

**Available Commands:**
```
/f5-design generate screen-detail <screen-name>   # Single screen detail
/f5-design generate screen-detail auth            # All auth screens
/f5-design generate screen-detail listing         # All listing screens
/f5-design generate screen-detail auction         # All auction screens
```

**⚠️ MANDATORY OUTPUT PATHS:**

| Command | Output Path |
|---------|-------------|
| `generate screen-detail login` | `.f5/specs/detail-design/v1.0.0/screens/login.md` |
| `generate screen-detail auth` | `.f5/specs/detail-design/v1.0.0/screens/auth/` (folder) |

**✅ CORRECT paths:**
```
.f5/specs/detail-design/v1.0.0/screens/login.md ✅
.f5/specs/detail-design/v1.0.0/screens/auth/login.md ✅
.f5/specs/detail-design/v1.0.0/screens/listing/create-listing.md ✅
```

**❌ WRONG paths:**
```
docs/screen-detail-login.md ❌
.f5/specs/detail-design/v1.0.0/login.md ❌  (missing screens/ folder!)
screen-detail.md ❌
```

**Output:** `.f5/specs/detail-design/v{VERSION}/screens/{screen-name}.md`

**Includes:**
- Component structure
- State management (React hooks, Zustand, etc.)
- Validation schema (Zod)
- Event handlers
- TypeScript interfaces

#### API Detail

**Available Commands:**
```
/f5-design generate api-detail <endpoint>         # Single API detail
/f5-design generate api-detail auth               # All auth APIs
/f5-design generate api-detail listing            # All listing APIs
```

**⚠️ MANDATORY OUTPUT PATHS:**

| Command | Output Path |
|---------|-------------|
| `generate api-detail POST-auth-login` | `.f5/specs/detail-design/v1.0.0/api/POST-auth-login.md` |
| `generate api-detail auth` | `.f5/specs/detail-design/v1.0.0/api/auth/` (folder) |

**✅ CORRECT paths:**
```
.f5/specs/detail-design/v1.0.0/api/POST-auth-login.md ✅
.f5/specs/detail-design/v1.0.0/api/auth/login.md ✅
```

**❌ WRONG paths:**
```
docs/api-detail-login.md ❌
.f5/specs/detail-design/v1.0.0/POST-auth-login.md ❌  (missing api/ folder!)
```

**Output:** `.f5/specs/detail-design/v{VERSION}/api/{endpoint}.md`

**Includes:**
- Controller implementation
- Service layer
- Repository layer
- DTO definitions
- Validation rules

#### Batch Detail
```
/f5-design generate batch-detail <batch-name>
```

**Output:** `.f5/specs/detail-design/v{VERSION}/batch/{batch-name}.md`

## ACTION: VALIDATE

```
/f5-design validate [--level basic|detail|all]
```

### Validation Checks

| Level | Checks |
|-------|--------|
| basic | Architecture, tables, APIs, screens complete |
| detail | Implementation specs, validation rules |
| all | Both levels |

### Output

```markdown
## 📋 Design Validation

**Level:** {{LEVEL}}
**Version:** {{VERSION}}

### Basic Design (基本設計)

#### ✅ Architecture
- [x] System architecture documented
- [x] Network architecture defined
- [x] Deployment architecture planned

#### ✅ Database Design
- [x] All tables defined: {{COUNT}}/{{TOTAL}}
- [x] Foreign keys documented
- [x] Indexes defined

#### ⚠️ API Design
- [x] API list complete: {{COUNT}}/{{TOTAL}}
- [ ] OpenAPI not generated
- [x] Auth flow defined

#### 🔄 Screen Design
- [x] Screen list: {{COUNT}}/{{TOTAL}}
- [ ] 2 screens missing layouts

### Detail Design (詳細設計)

#### Screen Details
| Screen | Status | Missing |
|--------|--------|---------|
| user-list | ✅ Complete | - |
| user-form | ⚠️ Partial | Validation |

#### API Details
| API | Status | Missing |
|-----|--------|---------|
| POST /users | ✅ Complete | - |
| GET /users | 🔄 Pending | - |

### Summary
| Category | Complete | Pending | Blocked |
|----------|----------|---------|---------|
| Tables | {{C}} | {{P}} | {{B}} |
| APIs | {{C}} | {{P}} | {{B}} |
| Screens | {{C}} | {{P}} | {{B}} |
```

## ACTION: TRACE

```
/f5-design trace [--type req-to-design|design-to-code|full]
```

### Output

```markdown
## 🔗 Traceability Matrix

### Requirements → Design

| REQ ID | Screens | APIs | Tables |
|--------|---------|------|--------|
| REQ-001 | SCR-001 | API-001, API-002 | TBL-001 |
| REQ-002 | SCR-002 | API-003 | TBL-002 |

### Coverage Summary
| From | To | Coverage |
|------|-----|----------|
| Requirements | Screens | {{PERCENT}}% |
| Requirements | APIs | {{PERCENT}}% |
| Requirements | Tables | {{PERCENT}}% |

### ⚠️ Orphan Items (Not Traced)
- SCR-010: No requirement reference
- API-020: Missing traceability

### ❌ Missing Coverage
- REQ-045: No design items found
- REQ-048: Only partial coverage
```

## ACTION: EXPORT

```
/f5-design export [--format <format>] [--level basic|detail|all]
```

### Formats
`markdown`, `html`, `pdf`, `docx`, `confluence`

### Output
```
.f5/output/basic-design-v{VERSION}.{FORMAT}
.f5/output/detail-design-v{VERSION}.{FORMAT}
```

## ACTION: STATUS

```
/f5-design status
```

### Output

```markdown
## 📊 Design Status

**Project:** {{PROJECT_NAME}}
**Version:** {{VERSION}}

### Basic Design (基本設計) - Gate D3
| Category | Total | Complete | Pending | Status |
|----------|-------|----------|---------|--------|
| Architecture | 4 | 4 | 0 | ✅ |
| Tables | 15 | 15 | 0 | ✅ |
| APIs | 23 | 20 | 3 | 🔄 |
| Screens | 12 | 10 | 2 | 🔄 |
| Batches | 3 | 3 | 0 | ✅ |

### Detail Design (詳細設計) - Gate D4
| Category | Total | Complete | Pending | Status |
|----------|-------|----------|---------|--------|
| Screen Details | 12 | 5 | 7 | ⏳ |
| API Details | 23 | 10 | 13 | ⏳ |
| Batch Details | 3 | 1 | 2 | ⏳ |

### Gate Progress
- D3 Basic Design: {{PERCENT}}% complete
- D4 Detail Design: {{PERCENT}}% complete

### Next Actions
1. Complete API specs: API-021, API-022, API-023
2. Complete screen specs: SCR-011, SCR-012
3. Start detail design for completed items
```

## MANDATORY: VERIFY OUTPUT AFTER GENERATE

After ANY generate command, Claude MUST verify:

### Step 1: Create subfolders FIRST (MANDATORY)
```bash
# ALWAYS run this before creating any file
mkdir -p .f5/specs/basic-design/v1.0.0/{database,api,screens,batch,diagrams}
mkdir -p .f5/specs/detail-design/v1.0.0/{screens,api,batch,components}
```

### Step 2: Check file location
```bash
ls -la .f5/specs/basic-design/v1.0.0/
ls -la .f5/specs/basic-design/v1.0.0/database/
ls -la .f5/specs/basic-design/v1.0.0/api/
ls -la .f5/specs/basic-design/v1.0.0/screens/
```

### Step 3: If files in wrong location, FIX IMMEDIATELY
```bash
# Fix 1: Files in docs/ folder
if [ -d "docs" ]; then
  mv docs/*Database*.md .f5/specs/basic-design/v1.0.0/database/ 2>/dev/null
  mv docs/*API*.md .f5/specs/basic-design/v1.0.0/api/ 2>/dev/null
  mv docs/*Screen*.md .f5/specs/basic-design/v1.0.0/screens/ 2>/dev/null
  mv docs/*Architecture*.md .f5/specs/basic-design/v1.0.0/ 2>/dev/null
  rmdir docs 2>/dev/null
fi

# Fix 2: Files in v1.0.0/ root instead of subfolder (COMMON MISTAKE!)
if [ -f ".f5/specs/basic-design/v1.0.0/database-design.md" ]; then
  mv .f5/specs/basic-design/v1.0.0/database-design.md .f5/specs/basic-design/v1.0.0/database/
fi
if [ -f ".f5/specs/basic-design/v1.0.0/api-design.md" ]; then
  mv .f5/specs/basic-design/v1.0.0/api-design.md .f5/specs/basic-design/v1.0.0/api/
fi
if [ -f ".f5/specs/basic-design/v1.0.0/screen-list.md" ]; then
  mv .f5/specs/basic-design/v1.0.0/screen-list.md .f5/specs/basic-design/v1.0.0/screens/
fi
```

### Step 4: Report final location
**Correct file locations:**
| File | Correct Location |
|------|------------------|
| database-design.md | `.f5/specs/basic-design/v1.0.0/database/database-design.md` |
| api-design.md | `.f5/specs/basic-design/v1.0.0/api/api-design.md` |
| screen-list.md | `.f5/specs/basic-design/v1.0.0/screens/screen-list.md` |
| system-architecture.md | `.f5/specs/basic-design/v1.0.0/system-architecture.md` |

**⛔ Claude MUST NOT report success until files are in correct subfolder!**

## FLAGS

| Flag | Description |
|------|-------------|
| `--type <type>` | Document type |
| `--framework <fw>` | Target framework |
| `--level <level>` | Validation level |
| `--format <format>` | Export format |
| `--version <version>` | Target version |
| `--lang <code>` | Translate output to specified language. Codes: `en` (English), `vn` (Vietnamese), `ja` (Japanese). Adds `_{lang}` suffix to filename (e.g., `database-design_vn.md`, `api-design_ja.md`) |

## EXAMPLES

### Basic Design Workflow
```
/f5-design generate architecture
/f5-design generate table users
/f5-design generate api /users --method GET
/f5-design generate screen user-list --type list
/f5-design validate --level basic
/f5-gate check D3
```

### Detail Design Workflow
```
/f5-design generate screen-detail user-form --framework react
/f5-design generate api-detail POST-users --framework nestjs
/f5-design validate --level detail
/f5-gate check D4
```

### Translation Examples
```
# Generate database design in Vietnamese
/f5-design generate tables --lang vn
# Output: .f5/specs/basic-design/v1.0.0/database/database-design_vn.md

# Generate API design in Japanese
/f5-design generate api-list --lang ja
# Output: .f5/specs/basic-design/v1.0.0/api/api-design_ja.md

# Generate screen detail in English
/f5-design generate screen-detail login --lang en
# Output: .f5/specs/detail-design/v1.0.0/screens/login_en.md

# Generate all designs in multiple languages
/f5-design generate architecture
/f5-design generate architecture --lang vn
/f5-design generate architecture --lang ja
```

---

## MODE: SPEC (from /f5-spec)

### `/f5-design spec <action>`

Manage and generate specification documents (SRS, Use Cases, Business Rules) for D1-D2 gates.

### Spec Output Paths

| Command | Document Type | Output Path |
|---------|--------------|-------------|
| `spec generate srs` | SRS Document | `.f5/specs/srs/v{VERSION}/srs.md` |
| `spec generate use-case UC-XXX` | Use Case | `.f5/specs/srs/v{VERSION}/use-cases/UC-XXX.md` |
| `spec generate use-cases` | All Use Cases | `.f5/specs/srs/v{VERSION}/use-cases/use-cases.md` |
| `spec generate business-rule BR-XXX` | Business Rule | `.f5/specs/srs/v{VERSION}/business-rules/BR-XXX.md` |
| `spec generate business-rules` | All BRs | `.f5/specs/srs/v{VERSION}/business-rules/business-rules.md` |
| `spec generate traceability` | Traceability | `.f5/specs/srs/v{VERSION}/traceability.md` |
| `spec export` | Export files | `.f5/output/srs-v{VERSION}.{FORMAT}` |

### Spec Actions

| Action | Description |
|--------|-------------|
| `spec generate <type>` | Generate spec from template |
| `spec validate` | Validate spec completeness |
| `spec export` | Export to different formats |
| `spec diff <v1> <v2>` | Compare versions |
| `spec status` | Show spec status |

### Generate SRS
```bash
/f5-design spec generate srs [--from <source>]
```

**Sources:** `requirements` (default), `template`, `existing`

**Output:** `.f5/specs/srs/v{VERSION}/srs.md`

### Generate Use Case
```bash
/f5-design spec generate use-case <uc-id> [--actor <actor>]
```

**Output:** `.f5/specs/srs/v{VERSION}/use-cases/{UC-ID}.md`

### Generate Business Rule
```bash
/f5-design spec generate business-rule <br-id>
```

**Output:** `.f5/specs/srs/v{VERSION}/business-rules/{BR-ID}.md`

### Spec Validate
```bash
/f5-design spec validate [--type <type>] [--version <version>]
```

**Validation Checks:** Unique IDs, Required Fields, Traceability, Priority, Status, No Orphans, Use Case Coverage, Terminology

### Spec Export
```bash
/f5-design spec export [--format <format>] [--version <version>]
```

**Formats:** `markdown`, `html`, `pdf`, `docx`, `confluence`

### Spec Diff
```bash
/f5-design spec diff <version1> <version2>
```

### Spec Status
```bash
/f5-design spec status
```

### Spec Examples
```bash
# Generate SRS from imported requirements
/f5-design spec generate srs --from requirements

# Generate use case
/f5-design spec generate use-case UC-001 --actor "Customer"

# Validate specifications
/f5-design spec validate --version v1.0.0

# Export to PDF
/f5-design spec export --format pdf

# Compare versions
/f5-design spec diff v1.0.0 v2.0.0

# Generate SRS with Vietnamese translation
/f5-design spec generate srs --lang vn
```

### Spec Workflow
```
1. /f5-import requirements.xlsx
2. /f5-design spec generate srs --from requirements
3. /f5-design spec generate use-case UC-001
4. /f5-design spec validate
5. /f5-gate check D2
6. /f5-design spec export --format pdf
```

---
**Remember:** Complete specifications (D1-D2) before basic design (D3), and basic design before detail design (D4)!
