---
description: Automatic code improvement and optimization
argument-hint: [path] [--type quality|performance|security|all] [--preview|--safe|--auto]
---

# /f5-improve - Code Improvement & Optimization

> **Purpose**: Analyze code and apply systematic improvements
> **Version**: 1.0.0
> **Category**: Quality
> **Inspiration**: SuperClaude /sc:improve

---

## Command Syntax

```bash
# Basic - analyze and preview improvements
/f5-improve [path]

# With improvement type
/f5-improve [path] --type <quality|performance|security|maintainability|all>

# With apply mode
/f5-improve [path] --preview       # Preview only (default)
/f5-improve [path] --safe          # Apply low-risk changes only
/f5-improve [path] --interactive   # Confirm each change
/f5-improve [path] --auto          # Apply all automatically

# With validation
/f5-improve [path] --validate      # Run tests after applying

# Combined
/f5-improve src/services/ --type performance --preview
/f5-improve auth-module --type security --safe --validate
```

## ARGUMENTS
The user's request is: $ARGUMENTS

---

## STEP 1: PARSE ARGUMENTS

Parse from $ARGUMENTS:

```yaml
parsed:
  path: "[extracted path or 'src/' default]"
  type: "[quality|performance|security|maintainability|all]"
  mode: "[preview|safe|interactive|auto]"
  validate: "[true|false]"
```

**Default values:**
- path: `src/` or current directory
- type: `all`
- mode: `preview`
- validate: `false`

---

## STEP 2: DETECT STACK & LOAD CONFIG

Read stack from project files (`package.json`, `pom.xml`, `pyproject.toml`, etc.):

| Indicator | Stack | Language |
|-----------|-------|----------|
| `@nestjs/core` | NestJS | TypeScript |
| `spring-boot` | Spring | Java |
| `fastapi` | FastAPI | Python |
| `go.mod` | Go | Go |
| `flutter` | Flutter | Dart |
| `next` | Next.js | TypeScript |
| `vue` | Vue | TypeScript/JS |
| `angular` | Angular | TypeScript |
| `laravel` | Laravel | PHP |

Load improve config from `.f5/config/improve.yaml` if exists.

### Output

```
## Configuration

| Setting | Value |
|---------|-------|
| Stack | NestJS (TypeScript) |
| Path | src/services/ |
| Type | performance |
| Mode | preview |
| Validate | false |

Excluded:
- **/*.spec.ts
- **/node_modules/**
- **/dist/**
```

---

## STEP 3: RUN ANALYSIS

Based on `--type`, run appropriate analyzers:

### Type: quality

| Analyzer | What it checks | Tool |
|----------|----------------|------|
| Lint | ESLint rules, warnings | eslint |
| Types | TypeScript strict | tsc |
| Format | Prettier compliance | prettier |
| Complexity | Cyclomatic complexity | complexity-report |
| Duplication | Code duplication | jscpd |
| Naming | Naming conventions | custom |
| Structure | Function length, SRP | custom |

**Commands by Stack:**

**NestJS/TypeScript:**
```bash
npm run lint -- --format json
npx tsc --noEmit
npx prettier --check "src/**/*.ts"
npx jscpd src/ --reporters json
```

**FastAPI/Python:**
```bash
ruff check . --format json
mypy app/ --json
black --check app/
radon cc app/ -j
```

**Go:**
```bash
golangci-lint run --out-format json
go vet ./...
gofmt -l .
gocyclo -over 10 .
```

### Type: performance

| Analyzer | What it checks | Tool |
|----------|----------------|------|
| N+1 Queries | ORM query patterns | custom |
| Caching | Uncached repeated calls | custom |
| Async | Sequential async operations | custom |
| Memory | Potential memory leaks | custom |
| Indexing | Missing database indexes | custom |

**Patterns to Detect:**

```yaml
n_plus_1:
  - "for.*await.*findOne"
  - "for.*await.*findBy"
  - "map.*async.*repository"

missing_cache:
  - "getCategories|getSettings|getConfig"
  - "findAll.*without.*@Cacheable"

sequential_async:
  - "await.*\n.*await.*\n.*await"
  - "for.*await"
```

### Type: security

| Analyzer | What it checks | Tool |
|----------|----------------|------|
| Auth Guards | Missing @UseGuards | custom |
| Role Checks | Missing @Roles | custom |
| Input Validation | Missing validators | custom |
| SQL Injection | Raw queries | custom |
| Dependencies | Vulnerable packages | npm audit |
| Secrets | Hardcoded credentials | custom |

**Commands:**
```bash
npm audit --json
npx secretlint "**/*"
```

### Type: maintainability

| Analyzer | What it checks | Tool |
|----------|----------------|------|
| Documentation | Missing JSDoc/TSDoc | custom |
| Types | 'any' usage, missing types | tsc |
| Test Coverage | Missing tests | jest --coverage |
| Comments | Outdated/TODO comments | custom |

### Analysis Output

```markdown
## Analysis Results

### Summary
| Category | Issues | Auto-fixable |
|----------|--------|--------------|
| Lint | 5 | 4 |
| Types | 2 | 0 |
| Format | 8 | 8 |
| Complexity | 2 | 0 |
| Performance | 3 | 2 |
| **Total** | **20** | **14** |
```

---

## STEP 4: GENERATE IMPROVEMENTS

For each issue found, generate improvement suggestion:

```yaml
improvement:
  id: "IMP-001"
  file: "order.service.ts"
  line: 120
  type: "performance"
  category: "n_plus_1"
  severity: "high"

  issue:
    title: "N+1 Query Detected"
    description: "Loading products in loop causes N+1 queries"

  current_code: |
    const orders = await this.orderRepo.find();
    for (const order of orders) {
      order.products = await this.productRepo.findByOrderId(order.id);
    }

  improved_code: |
    const orders = await this.orderRepo.find({
      relations: ['products']
    });

  risk: "low"       # low|medium|high
  impact: "high"    # low|medium|high
  auto_fixable: true
  requires_test: true
```

---

## STEP 5: OUTPUT BY MODE

### Mode: preview (default)

```markdown
## /f5-improve [path] --type [type] --preview

### Analysis Summary
| Metric | Current | After | Improvement |
|--------|---------|-------|-------------|
| N+1 Queries | 3 | 0 | -100% |
| Uncached Calls | 5 | 1 | -80% |
| Sync Operations | 2 | 0 | -100% |

### Proposed Changes

#### 1. Fix N+1 Query [IMP-001]
**File:** `order.service.ts:120`
**Risk:** Low | **Impact:** High

```diff
- const orders = await this.orderRepo.find();
- for (const order of orders) {
-   order.products = await this.productRepo.findByOrderId(order.id);
- }
+ const orders = await this.orderRepo.find({
+   relations: ['products']
+ });
```

#### 2. Add Caching [IMP-002]
**File:** `product.service.ts:45`
**Risk:** Low | **Impact:** Medium

```diff
+ @Cacheable({ ttl: 3600 })
  async getCategories() {
    return this.categoryRepo.find();
  }
```

#### 3. Parallelize Operations [IMP-003]
**File:** `notification.service.ts:78`
**Risk:** Medium | **Impact:** Low

```diff
- await this.sendEmail(user);
- await this.sendSms(user);
- await this.sendPush(user);
+ await Promise.all([
+   this.sendEmail(user),
+   this.sendSms(user),
+   this.sendPush(user),
+ ]);
```

---

### Summary
| Risk Level | Changes | Auto-Apply |
|------------|---------|------------|
| Low | 2 | Yes |
| Medium | 1 | Review needed |
| High | 0 | Manual only |

### Next Steps
```bash
# Apply safe changes only
/f5-improve [path] --type [type] --safe

# Apply with confirmation
/f5-improve [path] --type [type] --interactive

# Apply all changes
/f5-improve [path] --type [type] --auto
```
```

### Mode: safe

Apply only improvements with `risk: "low"`:

```markdown
## /f5-improve [path] --type [type] --safe

### Applied Changes (Safe Mode)

| # | ID | File | Change | Risk | Status |
|---|-----|------|--------|------|--------|
| 1 | IMP-001 | order.service.ts:120 | Fix N+1 query | Low | Applied |
| 2 | IMP-002 | product.service.ts:45 | Add caching | Low | Applied |

### Skipped Changes (Require Review)

| # | ID | File | Change | Risk | Reason |
|---|-----|------|--------|------|--------|
| 1 | IMP-003 | notification.service.ts:78 | Parallelize | Medium | Behavior change |

### Verification
```bash
# Run tests to verify changes
npm run test

# Review remaining changes
/f5-improve [path] --type [type] --interactive
```

### Summary
- Applied: 2 changes
- Skipped: 1 change
- Files modified: 2
```

### Mode: interactive

```markdown
## /f5-improve [path] --type [type] --interactive

### Change 1 of 3: Fix N+1 Query [IMP-001]

**File:** `order.service.ts:120`
**Type:** Performance - N+1 Query
**Risk:** Low | **Impact:** High

**Current Code:**
```typescript
const orders = await this.orderRepo.find();
for (const order of orders) {
  order.products = await this.productRepo.findByOrderId(order.id);
}
```

**Proposed Change:**
```typescript
const orders = await this.orderRepo.find({
  relations: ['products']
});
```

**Explanation:**
This change uses eager loading to fetch products in a single query,
eliminating the N+1 query problem. This can significantly improve
performance when loading multiple orders.

---

**Options:**
- **[Y]es** - Apply this change
- **[N]o** - Skip this change
- **[E]dit** - Modify the change before applying
- **[A]ll** - Apply all remaining changes
- **[S]afe** - Apply only low-risk changes
- **[Q]uit** - Stop and save progress

Your choice: _
```

### Mode: auto

```markdown
## /f5-improve [path] --type [type] --auto

### Applying All Changes...

| # | ID | File | Change | Status |
|---|-----|------|--------|--------|
| 1 | IMP-001 | order.service.ts:120 | Fix N+1 query | Applied |
| 2 | IMP-002 | product.service.ts:45 | Add caching | Applied |
| 3 | IMP-003 | notification.service.ts:78 | Parallelize | Applied |

### Summary
- Total applied: 3 changes
- Files modified: 3
- Time: 2.3s

### Post-Apply Verification
```bash
# Running lint check...
ESLint: No errors

# Running type check...
TypeScript: No errors

# Running tests...
Tests: 45 passed
```

### Git Status
```bash
git status
# Modified: src/services/order.service.ts
# Modified: src/services/product.service.ts
# Modified: src/services/notification.service.ts
```

### Suggested Commit Message
```
perf: optimize query performance and add caching

- Fix N+1 query in order service (IMP-001)
- Add caching to product categories (IMP-002)
- Parallelize notification sending (IMP-003)

Improvements applied by /f5-improve
```
```

---

## STEP 6: SAVE HISTORY

Save improvement history to `.f5/improvements/`:

```yaml
# .f5/improvements/2024-12-23-performance.yaml
session:
  id: "IMP-SESSION-001"
  date: "2024-12-23T10:30:00Z"
  type: "performance"
  path: "src/services/"
  mode: "auto"

improvements:
  - id: "IMP-001"
    status: "applied"
    file: "order.service.ts"
    line: 120
    type: "n_plus_1"
    risk: "low"

  - id: "IMP-002"
    status: "applied"
    file: "product.service.ts"
    line: 45
    type: "caching"
    risk: "low"

  - id: "IMP-003"
    status: "applied"
    file: "notification.service.ts"
    line: 78
    type: "async"
    risk: "medium"

summary:
  total: 3
  applied: 3
  skipped: 0

verification:
  lint: "pass"
  types: "pass"
  tests: "pass"
```

---

## IMPROVEMENT RULES BY TYPE

### Quality Rules

```yaml
quality_rules:
  # Function length
  - id: "QUAL-001"
    name: "long_function"
    check: "function_lines > 20"
    action: "suggest_extract"
    risk: "medium"

  # Cyclomatic complexity
  - id: "QUAL-002"
    name: "high_complexity"
    check: "complexity > 10"
    action: "suggest_refactor"
    risk: "medium"

  # Code duplication
  - id: "QUAL-003"
    name: "duplication"
    check: "duplication > 5%"
    action: "suggest_extract_common"
    risk: "medium"

  # Magic numbers
  - id: "QUAL-004"
    name: "magic_number"
    check: "literal_number_in_condition"
    action: "extract_constant"
    risk: "low"

  # Unused imports
  - id: "QUAL-005"
    name: "unused_import"
    check: "import_not_used"
    action: "remove_import"
    risk: "low"
    auto_fix: true

  # Import order
  - id: "QUAL-006"
    name: "import_order"
    check: "imports_not_sorted"
    action: "sort_imports"
    risk: "low"
    auto_fix: true
```

### Performance Rules

```yaml
performance_rules:
  # N+1 queries
  - id: "PERF-001"
    name: "n_plus_1"
    patterns:
      - "for.*await.*find"
      - "map.*async.*repository"
    action: "use_eager_loading"
    risk: "low"

  # Missing cache
  - id: "PERF-002"
    name: "missing_cache"
    patterns:
      - "getCategories|getSettings|getConfig"
    action: "add_cache_decorator"
    risk: "low"

  # Sequential async
  - id: "PERF-003"
    name: "sequential_async"
    patterns:
      - "await.*\\n.*await.*\\n.*await"
    action: "use_promise_all"
    risk: "medium"

  # Unnecessary await
  - id: "PERF-004"
    name: "return_await"
    patterns:
      - "return await"
    action: "remove_unnecessary_await"
    risk: "low"
    auto_fix: true
```

### Security Rules

```yaml
security_rules:
  # Missing auth guard
  - id: "SEC-001"
    name: "missing_auth"
    check: "endpoint_without_guard"
    action: "add_auth_guard"
    risk: "low"

  # Missing role check
  - id: "SEC-002"
    name: "missing_role"
    check: "sensitive_endpoint_without_role"
    action: "add_role_guard"
    risk: "low"

  # Missing input validation
  - id: "SEC-003"
    name: "missing_validation"
    check: "body_param_without_validation"
    action: "add_validation_pipe"
    risk: "low"

  # Vulnerable dependency
  - id: "SEC-004"
    name: "vulnerable_dep"
    check: "npm_audit_high"
    action: "update_dependency"
    risk: "medium"

  # Hardcoded secret
  - id: "SEC-005"
    name: "hardcoded_secret"
    patterns:
      - "password.*=.*['\"]"
      - "apiKey.*=.*['\"]"
      - "secret.*=.*['\"]"
    action: "use_env_variable"
    risk: "high"
```

### Maintainability Rules

```yaml
maintainability_rules:
  # Missing documentation
  - id: "MAINT-001"
    name: "missing_jsdoc"
    check: "exported_function_without_jsdoc"
    action: "add_jsdoc"
    risk: "low"

  # Any type usage
  - id: "MAINT-002"
    name: "any_type"
    check: "explicit_any"
    action: "add_proper_type"
    risk: "low"

  # Missing tests
  - id: "MAINT-003"
    name: "missing_tests"
    check: "file_without_test"
    action: "create_test_file"
    risk: "low"

  # TODO comments
  - id: "MAINT-004"
    name: "todo_comment"
    check: "TODO|FIXME|HACK"
    action: "resolve_or_track"
    risk: "low"
```

---

## INTEGRATION

### With /f5-review

```bash
# Review first to see issues
/f5-review check src/

# Then improve based on findings
/f5-improve src/ --type quality --safe
```

### With /f5-gate

```bash
# Before G2 gate
/f5-improve src/ --type all --safe --validate
/f5-gate check G2
```

### With /f5-fix

```bash
# /f5-improve - Proactive improvements
# /f5-fix - Reactive bug fixes

# Use improve for general optimization
/f5-improve src/ --type performance

# Use fix for specific bugs
/f5-fix BUG-005
```

---

## ROLLBACK

If issues found after applying:

```bash
# Git-based rollback
git checkout -- src/services/

# Or restore from backup (if created)
# Backup created automatically before applying changes
```

---

## EXAMPLES

### Basic Preview
```bash
/f5-improve src/
```

### Performance Optimization
```bash
/f5-improve src/services/ --type performance --safe
```

### Security Hardening
```bash
/f5-improve src/ --type security --interactive --validate
```

### Full Improvement (Before Gate)
```bash
/f5-improve src/ --type all --safe --validate
/f5-gate check G2
```

### Specific Module
```bash
/f5-improve src/modules/auth/ --type security --auto
```

---

## CONFIGURATION

Configure in `.f5/config/improve.yaml`:

```yaml
improve:
  enabled: true
  default_mode: "preview"
  default_type: "all"
  auto_apply_risk: "low"
  create_backup: true
  run_tests_after: false

  types:
    quality:
      enabled: true
      max_function_length: 20
      max_complexity: 10
      max_duplication: 5

    performance:
      enabled: true
      detect_n_plus_1: true
      suggest_caching: true
      detect_sequential_async: true

    security:
      enabled: true
      check_auth_guards: true
      check_input_validation: true
      check_dependencies: true

    maintainability:
      enabled: true
      require_jsdoc: true
      forbid_any: true
      check_todos: true

  exclude:
    - "**/*.spec.ts"
    - "**/*.test.ts"
    - "**/node_modules/**"
    - "**/dist/**"
    - "**/*.d.ts"
```

---

## SEE ALSO

- `/f5-review` - Code review (read-only analysis)
- `/f5-fix` - Fix specific bugs
- `/f5-gate` - Gate checks
- `/f5-suggest` - Get suggestions
- `/f5-tdd` - Test-driven development

---

## TRACEABILITY

Improvements are tracked and linked to requirements when applicable.
History saved to `.f5/improvements/` for audit and rollback.

---

*F5 Framework - Code Improvement Command v1.0.0*
*Inspired by SuperClaude /sc:improve*
