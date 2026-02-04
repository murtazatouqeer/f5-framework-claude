# Reverse Engineering Documentation Workflow

> **Purpose**: Generate comprehensive documentation from existing codebase
> **Use Case**: Legacy projects, undocumented systems, onboarding acceleration
> **Output**: `.f5/docs/` directory in your project repository

---

## Overview

Workflow này sử dụng Claude Code để phân tích code và tự động generate documentation theo cấu trúc chuẩn của F5 Framework.

```
┌─────────────────────────────────────────────────────────────────┐
│                 REVERSE ENGINEERING WORKFLOW                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [1] DISCOVERY          [2] EXTRACTION        [3] DOCUMENTATION │
│                                                                  │
│  • Git History          • Entities            • System Overview │
│  • Database Schema      • APIs                • Database Design │
│  • Code Structure       • Business Rules      • Entity States   │
│                         • Screens             • Business Rules  │
│                                               • Module Docs     │
│                         ↓                     • API Catalog     │
│                                                                  │
│                    [4] VALIDATION                                │
│                    • Review với stakeholders                     │
│                    • Update based on feedback                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### CLI Commands

```bash
# Initialize documentation structure in your project
f5 docs init

# Run reverse engineering analysis
f5 docs analyze

# Generate version changelog
f5 docs version <phase>
```

### Manual Workflow

1. Copy prompts from `workflows/reverse-engineering/prompts/`
2. Run with Claude Code at project root
3. Output to `.f5/docs/` in your project

---

## Prerequisites

### Required Access
- Source code repository
- Running application (for observation)
- Database access (read-only)
- Stakeholder interviews (optional but recommended)

### Tools
- Claude Code or Claude with computer use
- IDE with search capabilities
- Database client

---

## Phase 1: Discovery

### 1.1 Git Analysis

**Use prompt:** `prompts/analyze-git-history.md`

```bash
# List all tags/versions
git tag -l

# View branch history
git branch -a

# View commit history by date range
git log --since="2024-01-01" --oneline

# Find changes between versions
git diff v1.0..v2.0 --stat
```

### 1.2 Database Discovery

**For Laravel/Eloquent:**
```bash
# List migrations
ls -la database/migrations/

# Check current schema
php artisan migrate:status
```

### 1.3 Code Structure Analysis

**Prompt for Claude:**
```
Analyze the directory structure of [PROJECT_PATH] and identify:
1. Architecture pattern used (MVC, Clean Architecture, etc.)
2. Main modules/features
3. Key entry points (routes, controllers)
4. Business logic location (services, models)
5. Data layer (repositories, ORMs)
```

---

## Phase 2: Extraction

### 2.1 Entity Extraction

**Use prompts:**
- `prompts/extract-entities.md` - Multi-framework entity extraction
- `prompts/analyze-models.md` - Laravel-specific model analysis

Extract from:
- Model files (e.g., `app/Models/`, `src/entities/`)
- Migration files (e.g., `database/migrations/`)
- ORM schemas (Prisma, TypeORM, etc.)

Output:
- Entity list with attributes
- Relationships
- Constraints
- State definitions

### 2.2 API Extraction

Extract from:
- Route files (e.g., `routes/web.php`, `routes/api.php`)
- Controller files
- Request validators

Output:
- Endpoint catalog
- Request/Response formats
- Authentication requirements

### 2.3 Business Rules Extraction

**Use prompt:** `prompts/extract-business-rules.md`

Extract from:
- Model methods
- Service classes
- Validation rules
- Event handlers

Output:
- Validation rules
- Calculation rules
- Workflow rules
- Access control rules

### 2.4 Screen Extraction

Extract from:
- View templates
- Livewire/Vue/React components
- Form definitions

Output:
- Screen inventory
- UI element mapping
- Navigation flow

---

## Phase 3: Documentation Generation

### 3.1 Output Structure

All documentation is generated in your **project repository** at `.f5/docs/`:

```
your-project/
├── .f5/
│   └── docs/
│       ├── README.md                    # Project overview & navigation
│       ├── 01-system-overview.md        # Architecture & context
│       ├── 02-database-design.md        # ERD & data dictionary
│       ├── 03-entity-states.md          # State machines
│       ├── 04-business-rules.md         # All business logic
│       ├── entities/
│       │   ├── user.md
│       │   ├── order.md
│       │   └── ...
│       ├── modules/
│       │   ├── auth.md
│       │   ├── [module-name].md
│       │   └── ...
│       ├── api/
│       │   └── api-catalog.md           # Routes & endpoints
│       ├── screens/
│       │   └── screen-catalog.md        # UI screens
│       └── versions/
│           ├── v1.0.md
│           ├── v2.0.md
│           └── ...
└── ... (your code)
```

### 3.2 Templates

Use templates from `f5-framework/workflows/reverse-engineering/templates/`:

| Template | Purpose |
|----------|---------|
| `docs-readme.md` | Main README for `.f5/docs/` |
| `entity-template.md` | Individual entity documentation |
| `workflow-template.md` | Business workflow documentation |
| `version-template.md` | Version changelog |

### 3.3 Diagram Standards

Use Mermaid for diagrams:
- ERD: `erDiagram`
- State machines: `stateDiagram-v2`
- Sequences: `sequenceDiagram`
- Flowcharts: `flowchart TB/LR`

---

## Phase 4: Validation

### 4.1 Technical Review

- [ ] All entities documented
- [ ] All routes covered
- [ ] State transitions accurate
- [ ] Business rules verified against code

### 4.2 Stakeholder Review

- [ ] Business flow matches reality
- [ ] Missing features identified
- [ ] Incorrect assumptions corrected

### 4.3 Update Loop

```
Generate → Review → Feedback → Update → Re-review
```

---

## Claude Code Prompts

### Master Prompt

```
You are analyzing the codebase at [PROJECT_PATH] to generate documentation.

Project type: [Laravel/React/Next.js/etc.]
Documentation output: [PROJECT_PATH]/.f5/docs/

Tasks:
1. Read and understand the code structure
2. Extract entities, relationships, and business rules
3. Generate documentation following F5 Framework standards
4. Use Mermaid diagrams for visual representations
5. Include code references for traceability

Output format: Markdown files following the structure defined in
f5-framework/workflows/reverse-engineering/templates/

Templates to use:
- docs-readme.md → .f5/docs/README.md
- entity-template.md → .f5/docs/entities/[entity].md
- workflow-template.md → .f5/docs/modules/[module].md
- version-template.md → .f5/docs/versions/[version].md
```

### Available Prompts

Located in `prompts/` directory:

| Prompt | Purpose |
|--------|---------|
| `extract-entities.md` | Multi-framework entity extraction |
| `extract-business-rules.md` | Rules extraction |
| `analyze-models.md` | Laravel model analysis |
| `analyze-laravel.md` | Full Laravel project analysis |
| `analyze-git-history.md` | Version history extraction |

---

## CLI Integration

### `f5 docs init`

Initialize `.f5/docs/` structure in your project:

```bash
f5 docs init

# Creates:
# .f5/docs/
# ├── README.md          (from docs-readme template)
# ├── entities/
# ├── modules/
# ├── api/
# ├── screens/
# └── versions/
```

### `f5 docs analyze`

Run reverse engineering analysis:

```bash
# Analyze entire project
f5 docs analyze

# Analyze specific module
f5 docs analyze --module auth

# Analyze specific entity
f5 docs analyze --entity User

# Specify framework
f5 docs analyze --framework laravel
```

### `f5 docs version <phase>`

Generate version changelog:

```bash
# Generate changelog for current phase
f5 docs version v2.0

# Compare between versions
f5 docs version v2.0 --from v1.0

# Include git diff analysis
f5 docs version v2.0 --git-analysis
```

---

## Best Practices

### DO:
- ✅ Start with high-level overview before details
- ✅ Cross-reference code locations
- ✅ Use diagrams for complex flows
- ✅ Document "why" not just "what"
- ✅ Include phase/version context
- ✅ Keep documentation in project repo (`.f5/docs/`)
- ✅ Commit docs with related code changes

### DON'T:
- ❌ Document implementation details that change often
- ❌ Copy-paste entire code blocks
- ❌ Make assumptions without verification
- ❌ Skip state machines for stateful entities
- ❌ Ignore edge cases and error handling
- ❌ Store project-specific docs in f5-framework

---

## Multi-Framework Support

| Framework | Analysis Prompt | Key Files |
|-----------|----------------|-----------|
| Laravel/PHP | `analyze-laravel.md` | `app/Models/`, `database/migrations/` |
| Node.js/TypeScript | `extract-entities.md` | `src/entities/`, `prisma/schema.prisma` |
| Python/Django | `extract-entities.md` | `*/models.py` |
| Java/Spring | `extract-entities.md` | `**/entity/*.java` |
| Go | `extract-entities.md` | `**/models/*.go` |

---

## Integration with F5 Framework

### For New Projects
1. Generate baseline documentation using this workflow
2. Use as input for F5 BA workflow (`/f5-ba`)
3. Create TO-BE documentation for improvements

### For Maintenance
1. Re-run extraction when code changes
2. Diff documentation to identify gaps
3. Update documentation as part of PR process

### Workflow Chain
```
Reverse Engineering → BA Analysis → Design → Implementation
     (AS-IS)           (GAP)       (TO-BE)     (Code)
```

---

## Metrics

Track documentation quality:
- **Coverage**: % of code paths documented
- **Accuracy**: Feedback from stakeholders
- **Usability**: Time to onboard new developer
- **Freshness**: Last update date vs last code change

---

*Created by F5 Framework Team*
