---
description: Quality gate management with evidence collection
argument-hint: <check|complete|enforce> <gate>
mcp-servers: sequential-thinking, github
---

# /f5-gate - Quality Gate Management Command

Manage and enforce quality gates (D1-D4, G2-G4) for Japanese outsource workflow with automated validation and evidence collection.

## ARGUMENTS
The user's request is: $ARGUMENTS

## STEP 0: RESOLVE LANGUAGE

```bash
resolve_language() {
  if [ -f ".f5/config.json" ]; then
    PROJECT_LANG=$(jq -r '.language // empty' .f5/config.json 2>/dev/null)
    if [ -n "$PROJECT_LANG" ] && [ "$PROJECT_LANG" != "null" ]; then echo "$PROJECT_LANG"; return; fi
  fi
  if [ -f ~/.f5/preferences.yaml ]; then
    GLOBAL_LANG=$(grep '^language:' ~/.f5/preferences.yaml 2>/dev/null | sed 's/language:[[:space:]]*"\{0,1\}\([^"]*\)"\{0,1\}/\1/')
    if [ -n "$GLOBAL_LANG" ]; then echo "$GLOBAL_LANG"; return; fi
  fi
  echo "en"
}
ACTIVE_LANG=$(resolve_language)
```

### i18n Labels

| Key | en | vi | ja |
|-----|----|----|-----|
| check_title | Gate Check | Kiểm tra Gate | ゲートチェック |
| status_title | Gate Status | Trạng thái Gate | ゲートステータス |
| prerequisites | Prerequisites | Điều kiện tiên quyết | 前提条件 |
| checklist | Checklist Verification | Xác minh danh sách | チェックリスト検証 |
| automated_checks | Automated Checks | Kiểm tra tự động | 自動チェック |
| evidence | Evidence Collected | Bằng chứng đã thu thập | 収集したエビデンス |
| passed | PASSED | ĐẠT | 合格 |
| failed | FAILED | KHÔNG ĐẠT | 不合格 |
| with_warnings | PASSED WITH WARNINGS | ĐẠT VỚI CẢNH BÁO | 警告付き合格 |

### Gate Names by Language

| Gate | en | vi | ja |
|------|----|----|-----|
| D1 | Research Complete | Nghiên cứu hoàn thành | 調査完了 |
| D2 | SRS Approved | SRS được duyệt | SRS承認済 |
| D3 | Basic Design Approved | Thiết kế cơ bản được duyệt | 基本設計承認済 |
| D4 | Detail Design Approved | Thiết kế chi tiết được duyệt | 詳細設計承認済 |
| G2 | Implementation Ready | Triển khai hoàn thành | 実装完了 |
| G2.5 | Verification Complete | Xác minh hoàn thành | 検証完了 |
| G3 | Testing Complete | Kiểm thử hoàn thành | テスト完了 |
| G4 | Deployment Ready | Sẵn sàng triển khai | デプロイ準備完了 |

## STEP 1: PARSE ACTION

| Action | Description |
|--------|-------------|
| `check <gate>` | Run comprehensive automated checks for a gate |
| `start <gate>` | Start gate review process |
| `complete <gate>` | Mark gate as complete |
| `status` | Show all gates status |
| `report <gate>` | Generate comprehensive gate report for stakeholders |
| `enforce <gate>` | Enforce gate requirements - block progress if not met |

## STEP 2: DETECT STACK AND COMMANDS

Before running automated checks, detect stack and use appropriate commands:

### Stack Detection
```bash
STACK=$(jq -r '.stack.backend[0] // .stack.backend // "unknown"' .f5/config.json)
FRONTEND=$(jq -r '.stack.frontend // "unknown"' .f5/config.json)
```

### Stack-Specific Commands

| Check | NestJS | Spring | Django/FastAPI | Go | React/NextJS |
|-------|--------|--------|----------------|-----|--------------|
| Lint | `npm run lint` | `./mvnw checkstyle:check` | `flake8 .` | `golangci-lint run` | `npm run lint` |
| Type | `npm run build` | `./mvnw compile` | `mypy .` | `go build ./...` | `npm run type-check` |
| Test | `npm run test` | `./mvnw test` | `pytest` | `go test ./...` | `npm run test` |
| Coverage | `npm run test:cov` | `./mvnw jacoco:report` | `pytest --cov` | `go test -cover` | `npm run test:cov` |
| Security | `npm audit` | `./mvnw dependency-check:check` | `safety check` | `gosec ./...` | `npm audit` |

### Dynamic Command Resolution

```yaml
# Load from .f5/config/gates.yaml → stack_commands
commands:
  lint: "{{stack_commands[stack].lint}}"
  test: "{{stack_commands[stack].test}}"
  coverage: "{{stack_commands[stack].test_cov}}"
  security: "{{stack_commands[stack].security}}"
```

## GATE OVERVIEW

| Gate | Name | Japanese | Phase | Prerequisites |
|------|------|----------|-------|---------------|
| D1 | Research Complete | 調査完了 | Requirements | - |
| D2 | SRS Approved | SRS承認 | Requirements | D1 |
| D3 | Basic Design Approved | 基本設計承認 | Design | D2 |
| D4 | Detail Design Approved | 詳細設計承認 | Design | D3 |
| G2 | Implementation Ready | 実装完了 | Implementation | D4 |
| G3 | Testing Complete | テスト完了 | Testing | G2 |
| G4 | Deployment Ready | デプロイ準備完了 | Release | G3 |

---

## GATE ENFORCEMENT (G2-G4)

### G2 - Implementation Ready Enforcement

```yaml
# G2 Automated Enforcement
g2_enforcement:
  # Phase 1: Prerequisites
  prerequisites:
    - gate: "D4"
      status: "passed"
      error: "D4 (Detail Design) must be completed first"

  # Phase 2: Code Quality (via /f5-review)
  code_quality:
    lint:
      command: "npm run lint || yarn lint || eslint ."
      required: true
      threshold: 0  # No lint errors allowed
      error: "Lint errors must be fixed"

    type_check:
      command: "npm run typecheck || tsc --noEmit"
      required: true
      threshold: 0  # No type errors
      error: "Type errors must be fixed"

    complexity:
      tool: "complexity-report"
      threshold: 10  # Cyclomatic complexity
      error: "High complexity code must be refactored"

    duplication:
      tool: "jscpd"
      threshold: 5  # Max 5% duplication
      error: "Duplicated code must be reduced"

  # Phase 3: Architecture Compliance
  architecture:
    clean_architecture:
      check: "Verify layer separation"
      required: true

    traceability:
      pattern: "REQ-|FR-|NFR-|UC-|US-|SPEC-"
      coverage: 100  # All implementations must have traceability comments
      error: "All code must have traceability comments (REQ-XXX)"

  # Phase 4: Security (via /f5-review security)
  security:
    owasp_top10:
      required: true
      checks:
        - injection: "SQL/NoSQL/Command injection"
        - broken_auth: "Authentication vulnerabilities"
        - sensitive_data: "Data exposure risks"
        - xxe: "XML External Entities"
        - access_control: "Broken access control"
        - misconfig: "Security misconfiguration"
        - xss: "Cross-site scripting"
        - deserialization: "Insecure deserialization"
        - components: "Vulnerable components"
        - logging: "Insufficient logging"

  # Phase 5: Test Coverage
  test_coverage:
    unit:
      threshold: 80  # 80% minimum
      error: "Unit test coverage must be >= 80%"

    required_tests:
      - controllers: true
      - services: true
      - repositories: true
      - utils: true
```

### G2 Enforcement Commands

```bash
# Run G2 enforcement
/f5-gate enforce G2

# Output
┌─────────────────────────────────────────────────────────────────┐
│ G2 GATE ENFORCEMENT - Implementation Ready                       │
├─────────────────────────────────────────────────────────────────┤
│ Prerequisites                                                    │
│   ✅ D4 Gate: Passed                                            │
│                                                                  │
│ Code Quality (/f5-review check)                                  │
│   ✅ Lint: 0 errors                                             │
│   ✅ Type Check: 0 errors                                       │
│   ✅ Complexity: Max 8 (threshold: 10)                          │
│   ✅ Duplication: 3.2% (threshold: 5%)                          │
│                                                                  │
│ Architecture Compliance                                          │
│   ✅ Clean Architecture: Layers separated                       │
│   ✅ Traceability: 100% coverage                                │
│                                                                  │
│ Security (/f5-review security)                                   │
│   ✅ OWASP Top 10: No critical issues                           │
│   ⚠️  1 medium issue (review recommended)                       │
│                                                                  │
│ Test Coverage (/f5-test coverage)                                │
│   ✅ Unit Tests: 85% (threshold: 80%)                           │
│   ✅ All required tests present                                 │
│                                                                  │
│ G2 GATE STATUS: ✅ PASSED                                       │
│                                                                  │
│ Run `/f5-gate complete G2` to mark as complete                  │
└─────────────────────────────────────────────────────────────────┘
```

---

### G3 - Testing Complete Enforcement

```yaml
# G3 Automated Enforcement
g3_enforcement:
  # Phase 1: Prerequisites
  prerequisites:
    - gate: "G2"
      status: "passed"
      error: "G2 (Implementation) must be completed first"

  # Phase 2: Unit Tests (via /f5-test run)
  unit_tests:
    command: "npm test || yarn test || pytest || go test"
    required: true
    pass_rate: 100  # All must pass
    coverage:
      threshold: 80
      error: "Unit test coverage must be >= 80%"

  # Phase 3: Integration Tests
  integration_tests:
    command: "npm run test:integration"
    required: true
    pass_rate: 100
    checks:
      - database: "DB integration tests"
      - api: "API endpoint tests"
      - external: "External service mocks"

  # Phase 4: E2E Tests
  e2e_tests:
    command: "npm run test:e2e"
    required: true
    pass_rate: 95  # 95% minimum pass rate
    checks:
      - critical_flows: "Critical user journeys"
      - happy_path: "Happy path scenarios"
      - error_handling: "Error scenarios"

  # Phase 5: Performance Tests
  performance_tests:
    required: true
    checks:
      response_time:
        p95: 500  # 500ms for 95th percentile
        p99: 1000  # 1000ms for 99th percentile
      throughput:
        min_rps: 100  # Minimum requests per second
      memory:
        max_mb: 512  # Max memory usage
      cpu:
        max_percent: 80  # Max CPU usage

  # Phase 6: Security Tests
  security_tests:
    required: true
    checks:
      - vulnerability_scan: "No critical vulnerabilities"
      - dependency_audit: "No known vulnerable dependencies"
      - penetration_test: "Basic pen test passed"
```

### G3 Enforcement Commands

```bash
# Run G3 enforcement
/f5-gate enforce G3

# Output
┌─────────────────────────────────────────────────────────────────┐
│ G3 GATE ENFORCEMENT - Testing Complete                           │
├─────────────────────────────────────────────────────────────────┤
│ Prerequisites                                                    │
│   ✅ G2 Gate: Passed                                            │
│                                                                  │
│ Unit Tests (/f5-test run --type unit)                            │
│   ✅ Tests: 245/245 passed (100%)                               │
│   ✅ Coverage: 87% (threshold: 80%)                             │
│                                                                  │
│ Integration Tests (/f5-test run --type integration)              │
│   ✅ Database: 45/45 passed                                     │
│   ✅ API: 78/78 passed                                          │
│   ✅ External: 23/23 passed                                     │
│                                                                  │
│ E2E Tests (/f5-test run --type e2e)                              │
│   ✅ Critical Flows: 15/15 passed                               │
│   ✅ Happy Path: 32/32 passed                                   │
│   ✅ Error Handling: 18/18 passed                               │
│   ✅ Pass Rate: 100% (threshold: 95%)                           │
│                                                                  │
│ Performance Tests                                                │
│   ✅ Response Time p95: 320ms (threshold: 500ms)                │
│   ✅ Response Time p99: 780ms (threshold: 1000ms)               │
│   ✅ Throughput: 250 rps (threshold: 100 rps)                   │
│   ✅ Memory: 384MB (threshold: 512MB)                           │
│   ✅ CPU: 45% (threshold: 80%)                                  │
│                                                                  │
│ Security Tests                                                   │
│   ✅ Vulnerability Scan: No critical issues                     │
│   ✅ Dependency Audit: All dependencies secure                  │
│   ✅ Basic Pen Test: Passed                                     │
│                                                                  │
│ G3 GATE STATUS: ✅ PASSED                                       │
│                                                                  │
│ Run `/f5-gate complete G3` to mark as complete                  │
└─────────────────────────────────────────────────────────────────┘
```

---

### Test Evidence Archiving

When G3 gate passes, test evidence is automatically archived for compliance and audit purposes.

```yaml
# Evidence archiving configuration
evidence_archive:
  trigger: "on_g3_pass"

  artifacts:
    - test-results/
    - coverage-reports/
    - screenshots/
    - logs/

  metadata:
    timestamp: "2024-01-15T10:30:00Z"
    git_commit: "abc123"
    git_branch: "feature/user-auth"
    coverage_summary:
      statements: 85%
      branches: 78%
      functions: 82%
      lines: 84%
    test_summary:
      total: 150
      passed: 150
      failed: 0
      skipped: 2
```

### Evidence Commands

```bash
# Archive evidence for G3
/f5-gate evidence archive G3

# List archived evidence
/f5-gate evidence list

# Restore evidence for audit
/f5-gate evidence restore [archive-id]

# View evidence details
/f5-gate evidence show [archive-id]
```

### Evidence Structure

```
.f5/quality/evidence/
├── G3-2024-01-15-abc123/
│   ├── metadata.json
│   ├── test-results/
│   │   ├── unit-tests.json
│   │   ├── integration-tests.json
│   │   └── e2e-tests.json
│   ├── coverage-reports/
│   │   ├── lcov-report/
│   │   └── summary.json
│   ├── screenshots/
│   │   └── e2e/
│   └── logs/
│       └── test-run.log
└── G3-2024-01-10-def456/
    └── ...
```

---

### G4 - Deployment Ready Enforcement

```yaml
# G4 Automated Enforcement
g4_enforcement:
  # Phase 1: Prerequisites
  prerequisites:
    - gate: "G2"
      status: "passed"
      error: "G2 (Implementation) must be completed first"
    - gate: "G3"
      status: "passed"
      error: "G3 (Testing) must be completed first"

  # Phase 2: Build Verification (via /f5-deploy prepare)
  build:
    command: "npm run build || yarn build"
    required: true
    checks:
      - successful: "Build completed without errors"
      - artifacts: "All artifacts generated"
      - size: "Bundle size within limits"

  # Phase 3: Docker/Container
  container:
    required: true  # If using containers
    checks:
      - image_built: "Docker image built successfully"
      - image_scanned: "No critical vulnerabilities"
      - image_pushed: "Image pushed to registry"

  # Phase 4: Database
  database:
    required: true
    checks:
      - migrations_ready: "All migrations prepared"
      - rollback_tested: "Rollback scripts tested"
      - backup_created: "Database backup completed"

  # Phase 5: Environment
  environment:
    staging:
      deployed: true
      verified: true
      smoke_tests: "passed"

    production_config:
      validated: true
      secrets_configured: true
      resources_allocated: true

  # Phase 6: Documentation
  documentation:
    required: true
    checks:
      - release_notes: "Release notes updated"
      - changelog: "Changelog updated"
      - api_docs: "API documentation current"
      - runbook: "Runbook available"

  # Phase 7: Approvals
  approvals:
    required:
      - tech_lead: true
      - qa_lead: true
      - product_owner: false  # Optional based on project
    customer_approval:
      required: true
      for_gates: ["D2", "D3", "D4", "G4"]
```

### G4 Enforcement Commands

```bash
# Run G4 enforcement
/f5-gate enforce G4

# Output
┌─────────────────────────────────────────────────────────────────┐
│ G4 GATE ENFORCEMENT - Deployment Ready                           │
├─────────────────────────────────────────────────────────────────┤
│ Prerequisites                                                    │
│   ✅ G2 Gate: Passed                                            │
│   ✅ G3 Gate: Passed                                            │
│                                                                  │
│ Build Verification (/f5-deploy prepare)                          │
│   ✅ Build: Successful                                          │
│   ✅ Artifacts: All generated                                   │
│   ✅ Bundle Size: 420KB (limit: 500KB)                          │
│                                                                  │
│ Container                                                        │
│   ✅ Docker Image: Built (v1.2.3)                               │
│   ✅ Vulnerability Scan: No critical issues                     │
│   ✅ Image Pushed: registry/app:v1.2.3                          │
│                                                                  │
│ Database                                                         │
│   ✅ Migrations: Ready (3 new migrations)                       │
│   ✅ Rollback: Scripts tested                                   │
│   ✅ Backup: Completed                                          │
│                                                                  │
│ Environment                                                      │
│   ✅ Staging: Deployed & Verified                               │
│   ✅ Staging Smoke Tests: Passed                                │
│   ✅ Production Config: Validated                               │
│   ✅ Secrets: Configured                                        │
│   ✅ Resources: Allocated                                       │
│                                                                  │
│ Documentation                                                    │
│   ✅ Release Notes: Updated                                     │
│   ✅ Changelog: Updated                                         │
│   ✅ API Docs: Current                                          │
│   ✅ Runbook: Available                                         │
│                                                                  │
│ Approvals                                                        │
│   ✅ Tech Lead: @john.doe (2024-01-15)                          │
│   ✅ QA Lead: @jane.smith (2024-01-15)                          │
│   ⏳ Customer: Pending                                          │
│                                                                  │
│ G4 GATE STATUS: ⏳ PENDING CUSTOMER APPROVAL                    │
│                                                                  │
│ Action Required: Obtain customer approval to proceed             │
└─────────────────────────────────────────────────────────────────┘
```

---

## ACTION: CHECK_GATE (ENHANCED)

### `/f5-gate check <gate_id> [--ci]`

Run comprehensive automated checks for a gate.

### Process

```
┌─────────────────────────────────────────────────────────────────┐
│                    GATE CHECK WORKFLOW                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. PREREQUISITES          2. CHECKLIST          3. AUTOMATED   │
│  ──────────────           ─────────             ─────────────   │
│  • Check previous         • Verify docs         • Run lint      │
│    gates passed           • Verify code         • Run tests     │
│  • Load gate config       • Verify PRs          • Check coverage│
│                                                 • Security scan │
│         ↓                       ↓                      ↓        │
│  4. EVIDENCE               5. REPORT            6. DECISION     │
│  ────────                 ──────                ────────        │
│  • Collect proofs         • Generate report     • PASS/FAIL     │
│  • Store artifacts        • Show summary        • Block/Allow   │
│  • Link to checks         • List failures       • Next steps    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Output Format (Standard)

```markdown
## 🚦 Gate Check: G2 (Implementation Ready)

### Prerequisites
| Gate | Required | Status |
|------|----------|--------|
| D4 | ✅ Passed | ✅ Met |

### Checklist Verification
| Item | Required | Status | Evidence |
|------|----------|--------|----------|
| Code Complete | ✅ | ✅ Pass | src/** |
| Unit Tests | ✅ | ✅ Pass | **/*.spec.ts |
| Code Review | ✅ | ✅ Pass | PR #123 |
| Documentation | ✅ | ✅ Pass | README.md |

### Automated Checks

#### 1. Lint Check ✅
```bash
$ npm run lint
✔ No lint errors
```
| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Errors | 0 | 0 | ✅ |
| Warnings | ≤10 | 3 | ✅ |

#### 2. Type Check ✅
```bash
$ npm run type-check
✔ No type errors
```

#### 3. Unit Tests ✅
```bash
$ npm run test
Test Suites: 25 passed, 25 total
Tests: 150 passed, 150 total
```
| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Pass Rate | 100% | 100% | ✅ |

#### 4. Code Coverage ⚠️
```bash
$ npm run test:cov
```
| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Statements | ≥80% | 85% | ✅ |
| Branches | ≥75% | 72% | ⚠️ |
| Functions | ≥80% | 88% | ✅ |
| Lines | ≥80% | 84% | ✅ |

**Warning:** Branch coverage below threshold (72% < 75%)

#### 5. Security Audit ✅
```bash
$ npm audit --audit-level=high
found 0 vulnerabilities
```

#### 6. Traceability ✅
```bash
$ f5 strict validate
Coverage: 100% (45/45 requirements traced)
```

### Summary

| Category | Checks | Passed | Failed | Warnings |
|----------|--------|--------|--------|----------|
| Prerequisites | 1 | 1 | 0 | 0 |
| Checklist | 4 | 4 | 0 | 0 |
| Automated | 6 | 5 | 0 | 1 |
| **Total** | **11** | **10** | **0** | **1** |

### Gate Status: ⚠️ PASSED WITH WARNINGS

**Warnings (1):**
1. Branch coverage (72%) below target (75%)

### Evidence Collected
- Report: `.f5/gates/G2-check-{{TIMESTAMP}}.md`
- Coverage: `coverage/lcov-report/index.html`
- Test Results: `test-results/junit.xml`

### Next Steps
1. ⚠️ Improve branch coverage to meet 75% threshold
2. Get approvals:
   - [ ] dev_lead
   - [ ] tech_lead
3. Proceed to G3:
```bash
/f5-gate complete G2
/f5-gate start G3
```
```

### CI/CD Friendly Output (--ci flag)

```
/f5-gate check <gate_id> --ci
```

#### Exit Codes
| Code | Meaning |
|------|---------|
| 0 | Gate passed |
| 1 | Gate failed |
| 2 | Gate passed with warnings |

#### JSON Output Format
```json
{
  "gate": "G2",
  "status": "passed",
  "timestamp": "2024-01-15T10:30:00Z",
  "checks": {
    "total": 11,
    "passed": 10,
    "failed": 0,
    "warnings": 1
  },
  "metrics": {
    "coverage": 85,
    "test_pass_rate": 100,
    "lint_errors": 0
  },
  "evidence_path": ".f5/gates/G2-check-2024-01-15.json"
}
```

### GitHub Actions Integration

```yaml
# .github/workflows/gate-check.yml
name: Gate Check
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  gate-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check G2 Gate
        run: |
          # Run gate check with CI flag
          f5 gate check G2 --ci > gate-result.json
          exit_code=$?

          if [ $exit_code -eq 1 ]; then
            echo "::error::Gate G2 FAILED"
            cat gate-result.json
            exit 1
          elif [ $exit_code -eq 2 ]; then
            echo "::warning::Gate G2 passed with warnings"
          fi

      - name: Upload Evidence
        uses: actions/upload-artifact@v4
        with:
          name: gate-evidence
          path: .f5/gates/
```

### Gate-Specific Checks

#### D1 - Research Complete
- [ ] All requirements reviewed
- [ ] Ambiguous requirements clarified
- [ ] Requirements imported to `.f5/`
- [ ] Domain glossary created
- [ ] Technical feasibility confirmed

#### D2 - SRS Approved
- [ ] SRS document generated
- [ ] All requirements traced
- [ ] Use cases documented
- [ ] Business rules defined
- [ ] Customer review completed

#### D3 - Basic Design Approved
- [ ] System architecture documented
- [ ] Database design complete
- [ ] API specifications done
- [ ] Screen specifications done
- [ ] Customer approval obtained

#### D4 - Detail Design Approved
- [ ] Screen details documented
- [ ] API details documented
- [ ] Test cases identified
- [ ] Customer approval obtained

#### G2 - Implementation Ready (Enforced)
- [ ] All code reviewed → `/f5-review full`
- [ ] Coding standards followed → `/f5-review check`
- [ ] Unit tests written (>=80%) → `/f5-test coverage`
- [ ] Traceability comments added → `/f5-review check`
- [ ] Security review passed → `/f5-review security`

#### G3 - Testing Complete (Enforced)
- [ ] Unit tests passing → `/f5-test run --type unit`
- [ ] Integration tests passing → `/f5-test run --type integration`
- [ ] E2E tests passing → `/f5-test run --type e2e`
- [ ] Performance validated → `/f5-test run --type performance`
- [ ] Security tested → `/f5-review security`

#### G4 - Deployment Ready (Enforced)
- [ ] All gates passed → `/f5-gate status`
- [ ] Release notes prepared → `/f5-deploy prepare`
- [ ] Deployment plan documented → `/f5-deploy prepare`
- [ ] Staging verified → `/f5-deploy staging`
- [ ] Customer approval obtained

---

## ACTION: START

```
/f5-gate start <gate-id>
```

### Process
1. Check prerequisites (previous gate must be passed)
2. Create gate checklist from template
3. Initialize metrics tracking
4. Update `gates-status.yaml`
5. Record start date

### Output

```markdown
## Gate {{GATE}} Started

**Gate:** {{GATE}} - {{GATE_NAME}}
**Started:** {{TIMESTAMP}}

### Prerequisites
{{PREREQUISITES_STATUS}}

### Checklist Created
- `.f5/quality/{{GATE}}-{{GATE_SLUG}}.md`

### Focus Areas
{{FOCUS_AREAS}}

### Actions Required
1. {{ACTION_1}}
2. {{ACTION_2}}
3. {{ACTION_3}}
```

---

## ACTION: COMPLETE

```
/f5-gate complete <gate-id> [--force]
```

### Pre-completion Checks

For G2-G4 gates, enforcement is **automatically run**:

```bash
# Completing G2 automatically runs:
1. /f5-review check
2. /f5-review security
3. /f5-test coverage

# Completing G3 automatically runs:
1. /f5-test run --type unit
2. /f5-test run --type integration
3. /f5-test run --type e2e
4. /f5-test report

# Completing G4 automatically runs:
1. /f5-deploy prepare
2. /f5-deploy verify --env staging
```

### Completion Requirements

```yaml
# Gate completion requirements
completion_rules:
  D1_D4:
    - all_checklist_items: "completed"
    - no_blockers: true
    - customer_approval: "D2, D3, D4 only"

  G2:
    - enforcement: "passed"
    - code_review: "approved"
    - test_coverage: ">= 80%"
    - security_review: "no critical issues"

  G3:
    - enforcement: "passed"
    - all_tests: "passing"
    - coverage: ">= 80%"
    - performance: "within thresholds"

  G4:
    - enforcement: "passed"
    - staging: "verified"
    - documentation: "complete"
    - approvals: "all required"
```

### Output

```markdown
## Gate {{GATE}} Completed

**Gate:** {{GATE}} - {{GATE_NAME}}
**Completed:** {{TIMESTAMP}}
**Duration:** {{DURATION}}

### Final Metrics
| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| {{METRIC}} | {{TARGET}} | {{ACTUAL}} | |

### Sign-off
| Role | Name | Date | Status |
|------|------|------|--------|
| Tech Lead | {{NAME}} | {{DATE}} | |
| Customer | {{NAME}} | {{DATE}} | |

### Evidence Location
- `.f5/specs/{{PHASE}}/v{{VERSION}}/`

### Next Gate
{{NEXT_GATE}} - {{NEXT_GATE_NAME}}

Run `/f5-gate start {{NEXT_GATE}}` to continue.
```

---

## ACTION: ENFORCE_GATE (BLOCKING)

### `/f5-gate enforce <gate_id> [--fix] [--strict] [--ci]`

Enforce gate requirements - **block progress if not met**.

### Process
1. Run all checks from `/f5-gate check`
2. If **FAILED**: Block and show blockers
3. If **WARNINGS**: Allow with acknowledgment (unless --strict)
4. If **PASSED**: Allow to proceed

### Options
| Option | Description |
|--------|-------------|
| `--fix` | Attempt to auto-fix issues where possible |
| `--report` | Generate detailed enforcement report |
| `--strict` | Fail on warnings (not just errors) |
| `--ci` | CI/CD friendly JSON output with exit codes |

### Enforcement Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    ENFORCEMENT WORKFLOW                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  /f5-gate enforce G2                                             │
│         │                                                        │
│         ├──→ /f5-review check (lint, type, complexity)          │
│         ├──→ /f5-review security (OWASP Top 10)                 │
│         ├──→ /f5-test coverage (check >= 80%)                   │
│         └──→ Verify traceability comments                       │
│                                                                  │
│  /f5-gate enforce G3                                             │
│         │                                                        │
│         ├──→ /f5-test run --type unit                           │
│         ├──→ /f5-test run --type integration                    │
│         ├──→ /f5-test run --type e2e                            │
│         ├──→ /f5-test run --type performance                    │
│         └──→ /f5-test report (generate G3 report)               │
│                                                                  │
│  /f5-gate enforce G4                                             │
│         │                                                        │
│         ├──→ /f5-deploy prepare (check all requirements)        │
│         ├──→ /f5-deploy staging (verify staging)                │
│         ├──→ Check documentation                                 │
│         └──→ Check approvals                                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Output (BLOCKED)

```markdown
## 🛑 Gate Enforcement: G2 BLOCKED

### Critical Failures

**You cannot proceed until these are resolved:**

| # | Check | Target | Actual | Action Required |
|---|-------|--------|--------|-----------------|
| 1 | Unit Tests | 100% pass | 95% pass | Fix 5 failing tests |
| 2 | Security | 0 high | 2 high | Fix vulnerabilities |
| 3 | Coverage | ≥80% | 65% | Add more tests |

### Failed Tests
```
FAIL src/auth/auth.service.spec.ts
  ✕ should validate JWT token (15ms)
  ✕ should handle expired token (8ms)

FAIL src/user/user.service.spec.ts
  ✕ should create user with valid data (12ms)
```

### Security Vulnerabilities
```
high severity: prototype pollution in lodash < 4.17.21
high severity: SQL injection in typeorm < 0.3.0
```

### Blocking Reason
Gate G2 requires ALL automated checks to pass.
Current: 3 checks failed.

### How to Proceed
1. Fix failing tests in auth.service.spec.ts
2. Fix failing tests in user.service.spec.ts
3. Run `npm audit fix` to fix vulnerabilities
4. Add tests to increase coverage
5. Re-run: `/f5-gate enforce G2`
```

### Output (PASSED)

```markdown
## ✅ Gate Enforcement: G2 PASSED

All requirements met. You may proceed to G3.

### Summary
| Category | Status |
|----------|--------|
| Prerequisites | ✅ All met |
| Checklist | ✅ 4/4 complete |
| Automated Checks | ✅ 6/6 passed |

### Evidence Collected
- Report: `.f5/gates/G2-enforce-{{TIMESTAMP}}.md`
- Coverage: `coverage/lcov-report/index.html`
- Test Results: `test-results/junit.xml`
- Security Scan: `.f5/gates/G2-security.json`

### Proceed
```bash
/f5-gate complete G2
/f5-gate start G3
```
```

### Output (WARNINGS)

```markdown
## ⚠️ Gate Enforcement: G2 PASSED WITH WARNINGS

Gate passed but has non-critical warnings.

### Warnings (2)
| # | Check | Target | Actual | Recommendation |
|---|-------|--------|--------|----------------|
| 1 | Branch Coverage | ≥75% | 72% | Improve branch coverage |
| 2 | Complexity | <10 | 8 | Consider refactoring high complexity areas |

### Summary
| Category | Passed | Warnings |
|----------|--------|----------|
| Prerequisites | 1/1 | 0 |
| Checklist | 4/4 | 0 |
| Automated | 4/6 | 2 |

### Options
1. **Proceed anyway**: `/f5-gate complete G2`
2. **Fix warnings first**: Address issues then re-run `/f5-gate enforce G2`
3. **Block on warnings**: Re-run with `--strict` flag
```

### CI/CD Output (--ci flag)

```json
{
  "gate": "G2",
  "status": "blocked",
  "timestamp": "2024-01-15T10:30:00Z",
  "blockers": [
    {
      "check": "unit_tests",
      "target": "100%",
      "actual": "95%",
      "failures": [
        "src/auth/auth.service.spec.ts",
        "src/user/user.service.spec.ts"
      ]
    },
    {
      "check": "security",
      "target": "0 high",
      "actual": "2 high",
      "vulnerabilities": [
        "lodash < 4.17.21",
        "typeorm < 0.3.0"
      ]
    }
  ],
  "evidence_path": ".f5/gates/G2-enforce-2024-01-15.json",
  "exit_code": 1
}

---

## ACTION: STATUS

```
/f5-gate status
```

### Output

```markdown
## Quality Gates Status

**Project:** {{PROJECT_NAME}}
**Current Gate:** {{CURRENT_GATE}}

### Progress Overview

```
D1  → D2  → D3  → D4  → G2  → G3  → G4
```

### Gate Details

| Gate | Name | Status | Started | Completed | Enforcement |
|------|------|--------|---------|-----------|-------------|
| D1 | Research Complete | Passed | {{DATE}} | {{DATE}} | N/A |
| D2 | SRS Approved | Passed | {{DATE}} | {{DATE}} | N/A |
| D3 | Basic Design | Passed | {{DATE}} | {{DATE}} | N/A |
| D4 | Detail Design | Passed | {{DATE}} | {{DATE}} | N/A |
| G2 | Implementation | In Progress | {{DATE}} | - | Pending |
| G3 | Testing | Pending | - | - | Pending |
| G4 | Deployment | Pending | - | - | Pending |

### Current Gate Progress
- Gate: {{CURRENT_GATE}} - {{GATE_NAME}}
- Progress: {{PERCENT}}%
- Remaining: {{REMAINING_ITEMS}} items

### Active Blockers
{{BLOCKERS}}

### Timeline
| Milestone | Planned | Actual | Status |
|-----------|---------|--------|--------|
| D3 Complete | {{DATE}} | - | {{STATUS}} |
| G4 Complete | {{DATE}} | - | {{STATUS}} |
```

---

## ACTION: GENERATE_REPORT (COMPREHENSIVE)

### `/f5-gate report <gate_id> [--format <format>]`

Generate comprehensive gate report for stakeholders.

### Formats
| Format | Output | Use Case |
|--------|--------|----------|
| `markdown` | `.f5/output/{{GATE}}-report.md` | Default, GitHub |
| `html` | `.f5/output/{{GATE}}-report.html` | Web viewing |
| `pdf` | `.f5/output/{{GATE}}-report.pdf` | Customer delivery |
| `json` | `.f5/output/{{GATE}}-report.json` | CI/CD integration |

### Output Format

```markdown
## 📋 Gate Report: G2 - Implementation Ready

**Project:** User Management System
**Version:** 1.2.0
**Date:** {{TIMESTAMP}}
**Author:** Development Team

---

### Executive Summary

| Metric | Value |
|--------|-------|
| Gate Status | ✅ PASSED |
| Checks Passed | 11/11 (100%) |
| Code Coverage | 85% |
| Security Score | A |
| Quality Score | 92/100 |

---

### 1. Prerequisites

| Gate | Status | Completed |
|------|--------|-----------|
| D4 - Detail Design | ✅ Passed | 2024-01-10 |

---

### 2. Code Quality

#### 2.1 Static Analysis
| Tool | Status | Details |
|------|--------|---------|
| ESLint | ✅ Pass | 0 errors, 3 warnings |
| TypeScript | ✅ Pass | 0 errors |
| Prettier | ✅ Pass | All files formatted |

#### 2.2 Complexity
| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Avg Complexity | 4.2 | <10 | ✅ |
| Max Complexity | 8 | <15 | ✅ |
| Duplication | 2.1% | <5% | ✅ |

---

### 3. Test Results

#### 3.1 Unit Tests
| Metric | Value |
|--------|-------|
| Total Tests | 150 |
| Passed | 150 |
| Failed | 0 |
| Skipped | 0 |
| Duration | 12.5s |

#### 3.2 Coverage
| Type | Coverage | Target | Status |
|------|----------|--------|--------|
| Statements | 85% | 80% | ✅ |
| Branches | 78% | 75% | ✅ |
| Functions | 88% | 80% | ✅ |
| Lines | 84% | 80% | ✅ |

---

### 4. Security

#### 4.1 Dependency Audit
| Severity | Count |
|----------|-------|
| Critical | 0 |
| High | 0 |
| Medium | 2 |
| Low | 5 |

#### 4.2 Code Security
| Check | Status |
|-------|--------|
| SQL Injection | ✅ Safe |
| XSS | ✅ Safe |
| CSRF | ✅ Protected |
| Auth | ✅ Implemented |

---

### 5. Traceability

| Metric | Value |
|--------|-------|
| Total Requirements | 45 |
| Traced to Code | 45 |
| Coverage | 100% |

---

### 6. Approvals

| Role | Approver | Status | Date |
|------|----------|--------|------|
| Dev Lead | @dev_lead | ✅ Approved | 2024-01-15 |
| Tech Lead | @tech_lead | ✅ Approved | 2024-01-15 |

---

### 7. Artifacts

| Artifact | Location |
|----------|----------|
| Coverage Report | coverage/lcov-report/index.html |
| Test Results | test-results/junit.xml |
| Gate Evidence | .f5/gates/G2-report.md |

---

### 8. Conclusion

Gate G2 has **PASSED** all requirements. The implementation is ready to proceed to G3 (Testing Complete).

**Generated by:** F5 Framework
**Timestamp:** {{TIMESTAMP}}
```

### Report Contents
1. Executive summary with key metrics
2. Prerequisites verification
3. Code quality analysis
4. Test results and coverage
5. Security audit results
6. Traceability verification
7. Approvals status
8. Artifacts and evidence links
9. Conclusion and next steps

---

## FLAGS

| Flag | Description | Applies To |
|------|-------------|------------|
| `--force` | Complete gate even with warnings | `complete` |
| `--format <format>` | Report format (markdown, html, pdf, json) | `report` |
| `--detailed` | Show detailed checklist | `check`, `status` |
| `--fix` | Auto-fix issues where possible | `enforce` |
| `--strict` | Fail on warnings (not just errors) | `enforce`, `check` |
| `--ci` | CI/CD friendly JSON output with exit codes | `check`, `enforce` |
| `--report` | Generate detailed enforcement report | `enforce` |

### CI/CD Integration

#### Exit Codes (--ci flag)
| Code | Meaning | Action |
|------|---------|--------|
| 0 | Gate passed | Continue pipeline |
| 1 | Gate failed | Block pipeline |
| 2 | Gate passed with warnings | Warning in pipeline |

#### Environment Variables
```bash
# Set in CI/CD environment
F5_GATE_STRICT=true       # Treat warnings as failures
F5_GATE_AUTO_FIX=true     # Attempt auto-fix
F5_GATE_OUTPUT_DIR=./reports  # Custom output directory
```

---

## EXAMPLES

### Check current gate
```
/f5-gate check D3
```

### Start next gate
```
/f5-gate start D4
```

### Run enforcement
```
/f5-gate enforce G2
/f5-gate enforce G3 --strict
/f5-gate enforce G4 --report
```

### Complete gate
```
/f5-gate complete D3
/f5-gate complete G2  # Runs enforcement automatically
```

### View all gates
```
/f5-gate status
```

### Generate report
```
/f5-gate report D2 --format pdf
/f5-gate report G3 --format html
```

---

## SUGGESTED COMMANDS PER GATE

**CRITICAL: Always suggest commands with `-` NOT `:`**

### D1 - Research Complete
```bash
# Import requirements
/f5-import requirements.xlsx
/f5-ba init
/f5-ba elicit --import feedback.xlsx

# Validate
/f5-gate check D1
```

### D2 - SRS Approved
```bash
# Generate SRS
/f5-spec generate srs
/f5-spec generate use-cases
/f5-spec generate business-rules

# Validate
/f5-spec validate
/f5-gate check D2
```

### D3 - Basic Design Approved
```bash
# Generate Basic Design documents
/f5-design generate architecture
/f5-design generate tables
/f5-design generate api-list
/f5-design generate screen-list

# Validate
/f5-design validate --level basic
/f5-gate check D3
```

### D4 - Detail Design Approved
```bash
# Generate Detail Design documents
/f5-design generate screen-detail <screen-name>
/f5-design generate api-detail <endpoint>

# Generate by module
/f5-design generate screen-detail auth
/f5-design generate screen-detail listing
/f5-design generate screen-detail auction
/f5-design generate screen-detail order

# Validate
/f5-design validate --level detail
/f5-gate check D4
```

### G2 - Implementation Ready (ENFORCED)
```bash
# Implementation workflow
/f5-implement <feature>

# Quality checks (required for enforcement)
/f5-review check          # Lint, type check
/f5-review full           # Full code review
/f5-review security       # OWASP Top 10

# Test coverage
/f5-test coverage

# Run enforcement
/f5-gate enforce G2

# Complete gate
/f5-gate complete G2
```

### G3 - Testing Complete (ENFORCED)
```bash
# Run tests
/f5-test run --type unit
/f5-test run --type integration
/f5-test run --type e2e

# Generate report
/f5-test report

# Run enforcement
/f5-gate enforce G3

# Complete gate
/f5-gate complete G3
```

### G4 - Deployment Ready (ENFORCED)
```bash
# Prepare deployment
/f5-deploy prepare

# Deploy to staging
/f5-deploy staging

# Verify staging
/f5-deploy verify --env staging

# Run enforcement
/f5-gate enforce G4

# Complete gate (requires customer approval)
/f5-gate complete G4
```

**WRONG command format (NEVER use):**
```
/f5-spec detail-design
/f5-design generate
/f5-gate check
```

**CORRECT command format (ALWAYS use):**
```
/f5-spec generate srs
/f5-design generate screen-detail
/f5-gate check D4
/f5-gate enforce G2
```

---

## GATE FLOW

```
┌─────────────────────────────────────────────────────────────────────┐
│                    F5 Quality Gate Flow (v2.0)                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Requirements Phase          Design Phase          Execution Phase   │
│  ┌─────┐    ┌─────┐        ┌─────┐    ┌─────┐    ┌─────────────┐   │
│  │ D1  │ → │ D2  │   →   │ D3  │ → │ D4  │ →  │ G2 → G3 → G4│   │
│  │調査 │    │SRS │        │基本 │    │詳細 │    │実装→テスト→  │   │
│  │     │    │    │        │設計 │    │設計 │    │デプロイ      │   │
│  └─────┘    └─────┘        └─────┘    └─────┘    └─────────────┘   │
│  manual     manual         manual     manual      ENFORCED          │
│                                                                      │
│  Customer Approval Points: D2  D3  D4  G4                          │
│                                                                      │
│  Enforcement Points:                                                 │
│    G2: /f5-review + /f5-test coverage                               │
│    G3: /f5-test (all types)                                         │
│    G4: /f5-deploy prepare + staging verify                          │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## ENFORCEMENT FAILURE HANDLING

### When Enforcement Fails

```yaml
# Enforcement failure actions
failure_handling:
  G2_failures:
    lint_errors:
      action: "Run /f5-review check --fix"
      auto_fix: true

    type_errors:
      action: "Fix type errors manually"
      auto_fix: false

    low_coverage:
      action: "Generate more tests with /f5-test generate"
      auto_fix: false

    security_issues:
      action: "Review /f5-review security output"
      auto_fix: false
      block_gate: true  # Critical issues block gate

  G3_failures:
    test_failures:
      action: "Fix failing tests"
      auto_fix: false
      show_details: true

    low_coverage:
      action: "Add more tests"
      auto_fix: false

    performance_issues:
      action: "Optimize code"
      auto_fix: false

  G4_failures:
    build_failure:
      action: "Fix build errors"
      auto_fix: false

    staging_verification:
      action: "Fix staging issues"
      auto_fix: false

    missing_documentation:
      action: "Update documentation"
      auto_fix: false

    missing_approvals:
      action: "Obtain required approvals"
      auto_fix: false
```

### Failure Output Example

```bash
/f5-gate enforce G2

┌─────────────────────────────────────────────────────────────────┐
│ G2 GATE ENFORCEMENT - FAILED                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ 3 ISSUES FOUND                                                  │
│                                                                  │
│ Code Quality                                                     │
│   ❌ Lint: 5 errors                                             │
│      → Run `/f5-review check --fix` to auto-fix                 │
│                                                                  │
│ Test Coverage                                                    │
│   ❌ Coverage: 72% (threshold: 80%)                             │
│      → Run `/f5-test generate <file>` to add tests              │
│                                                                  │
│ Security                                                         │
│   ⚠️  1 medium issue found                                      │
│      → Run `/f5-review security` for details                    │
│                                                                  │
│ Fix these issues and run `/f5-gate enforce G2` again            │
└─────────────────────────────────────────────────────────────────┘
```

---

## STARTING POINT VARIATIONS

| Starting Point | Initial Gate | Skipped |
|----------------|--------------|---------|
| requirements | D1 | None |
| basic-design | D3 | D1, D2 |
| detail-design | D4 | D1-D3 |
| change-request | G2 | D1-D4 |

---

## INTEGRATION

### With Other F5 Commands

```yaml
# Command integration
integration:
  f5-implement:
    - Checks D4 passed before starting
    - Runs /f5-review after implementation

  f5-test:
    - Generates tests during implementation
    - Reports to G3 gate

  f5-review:
    - Code quality for G2
    - Security review for G2

  f5-deploy:
    - Prepare checks G4 requirements
    - Staging verifies deployment
```

---

**Remember:** Quality gates ensure project success. G2-G4 gates now have **automated enforcement** - not just manual checklists!
