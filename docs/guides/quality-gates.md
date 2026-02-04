# Requirement Quality Guide

Complete guide for analyzing and improving requirement quality using F5 Req commands.

## Overview

The F5 Requirement Quality system provides comprehensive analysis of requirements:
- **Ambiguity Detection**: Find vague and unclear terms
- **Gap Analysis**: Identify missing requirements
- **Quality Scoring**: Grade requirements A-F
- **Prioritization**: MoSCoW, WSJF, Value-Effort methods
- **Dependency Analysis**: Find circular dependencies
- **Test Generation**: Create BDD and unit test specs

## Quick Start

```bash
# Comprehensive analysis
/f5-req analyze docs/requirements.md

# Check quality score
/f5-req score docs/requirements.md

# Generate improvement suggestions
/f5-req improve docs/requirements.md

# Generate test cases
/f5-req tests docs/requirements.md --format bdd
```

## Quality Dimensions

### 1. Clarity (25%)

Requirements must be unambiguous and clearly understood.

**Good:**
> The system shall respond to search queries within 200 milliseconds for 95% of requests.

**Bad:**
> The system should respond quickly to search queries.

### 2. Completeness (25%)

Requirements must include all necessary information.

**Good:**
> REQ-001: User Authentication
> - Actor: Registered User
> - Trigger: User clicks "Login"
> - Precondition: User has valid account
> - Success: JWT token issued, valid for 24 hours
> - Failure: Error message displayed, attempt logged

**Bad:**
> REQ-001: User can login to the system.

### 3. Consistency (20%)

Requirements must not contradict each other.

**Issue Example:**
> REQ-001: Session timeout after 30 minutes of inactivity
> REQ-015: Sessions never expire for premium users

**Resolution:** Clarify relationship between requirements.

### 4. Testability (15%)

Requirements must have measurable acceptance criteria.

**Good:**
> The login page shall load within 2 seconds on a 3G connection (minimum 384 kbps).

**Bad:**
> The login page should load reasonably fast.

### 5. Traceability (15%)

Requirements must link to source and implementation.

**Good:**
> REQ-001: User Authentication
> - Source: BR-005 (Security Requirements)
> - Implements: UC-001 (Login Flow)
> - Tests: TC-001, TC-002, TC-003

**Bad:**
> REQ-001: User Authentication (no links)

## Scoring System

### Grade Scale

| Grade | Score | Description | Action |
|-------|-------|-------------|--------|
| A | 90-100 | Excellent | Ready for implementation |
| B | 80-89 | Good | Minor improvements needed |
| C | 70-79 | Average | Several issues to address |
| D | 60-69 | Poor | Significant rewrite needed |
| F | <60 | Failing | Not ready for development |

### Score Calculation

```
Clarity Score = 100 - (ambiguous_terms × 5) - (vague_quantifiers × 3)
Completeness Score = (present_fields / required_fields) × 100
Consistency Score = 100 - (contradictions × 10) - (format_variations × 2)
Testability Score = (measurable_criteria / total_criteria) × 100
Traceability Score = (linked_items / total_items) × 100

OVERALL = (Clarity × 0.25) + (Completeness × 0.25) +
          (Consistency × 0.20) + (Testability × 0.15) +
          (Traceability × 0.15)
```

## Ambiguity Detection

### Command

```bash
/f5-req ambiguity docs/requirements.md
/f5-req ambiguity docs/requirements.md --lang ja
/f5-req ambiguity docs/requirements.md --strict
```

### Ambiguous Terms Database

#### English

| Category | Terms to Avoid | Better Alternative |
|----------|----------------|-------------------|
| Vague Quantity | few, many, some, several | specific numbers |
| Vague Quality | fast, slow, good, efficient | measurable metrics |
| Vague Time | quickly, soon, real-time | specific time limits |
| Incomplete | etc, and so on, such as | complete lists |
| Subjective | easy, simple, intuitive | defined criteria |
| Uncertain | may, might, could, possibly | shall/must |

#### Japanese (日本語)

| Category | Terms to Avoid | Better Alternative |
|----------|----------------|-------------------|
| 曖昧な量 | 少し, 多少, いくつか | 具体的な数値 |
| 曖昧な品質 | 速い, 遅い, 良い | 測定可能な指標 |
| 曖昧な時間 | すぐに, 即座に | 具体的な時間制限 |
| 不完全 | など, 等, その他 | 完全なリスト |
| 主観的 | 簡単, シンプル, 直感的 | 定義された基準 |
| 不確実 | かもしれない, 可能性がある | するものとする |

#### Vietnamese (Tiếng Việt)

| Category | Terms to Avoid | Better Alternative |
|----------|----------------|-------------------|
| Số lượng mơ hồ | một số, vài, nhiều | số cụ thể |
| Chất lượng mơ hồ | nhanh, chậm, tốt | chỉ số đo lường |
| Thời gian mơ hồ | ngay, sớm | giới hạn thời gian cụ thể |
| Không đầy đủ | v.v., vân vân | danh sách đầy đủ |
| Chủ quan | dễ, đơn giản | tiêu chí xác định |
| Không chắc chắn | có thể, có lẽ | phải, sẽ |

### Severity Levels

| Level | Description | Action |
|-------|-------------|--------|
| 🔴 Critical | Blocks implementation | Must fix before development |
| 🟠 High | Causes confusion | Fix before approval |
| 🟡 Medium | Needs clarification | Address during review |
| 🟢 Low | Minor issue | Can defer |

### Example Output

```markdown
## Ambiguity Detection Report

🔴 Critical:
**REQ-005**: "System should respond quickly to user requests"
- Ambiguous term: "quickly"
- Problem: No measurable criteria
- Suggestion: Define specific response time
- Rewrite: "System shall respond within 200ms for 95% of requests"
```

## Gap Analysis

### Command

```bash
/f5-req gaps docs/requirements.md
/f5-req gaps docs/requirements.md --suggest
```

### Gap Categories

| Category | Checks |
|----------|--------|
| CRUD Coverage | Create, Read, Update, Delete operations |
| Error Handling | Error scenarios, edge cases |
| Security | Authentication, authorization, data protection |
| Performance | Response time, throughput, scalability |
| Accessibility | WCAG compliance, i18n, l10n |
| Data | Validation, format, constraints |
| Integration | External systems, APIs |
| Audit | Logging, traceability, compliance |

### CRUD Analysis Example

For an entity "User":

| Operation | Found? | Requirement |
|-----------|--------|-------------|
| Create | ✅ | REQ-001: User registration |
| Read | ✅ | REQ-002: User profile view |
| Update | ✅ | REQ-003: User profile edit |
| Delete | ❌ | MISSING |
| List | ✅ | REQ-010: User listing |
| Search | ❌ | MISSING |

### Suggested Requirements

When gaps are found, suggestions are generated:

```markdown
## Suggested Requirements

**REQ-NEW-001**: User Account Deletion
- Category: CRUD Coverage
- Priority: Medium
- Rationale: CRUD coverage incomplete - Delete operation missing

**REQ-NEW-002**: User Search
- Category: CRUD Coverage
- Priority: High
- Rationale: Listed entities need search capability
```

## Prioritization Methods

### MoSCoW

```bash
/f5-req prioritize docs/requirements.md --method moscow
```

| Category | Definition | Example |
|----------|------------|---------|
| **Must Have** | Critical for MVP | User authentication |
| **Should Have** | Important but not vital | Password recovery |
| **Could Have** | Nice to have | Social login |
| **Won't Have** | Out of scope | Biometric auth |

### WSJF (Weighted Shortest Job First)

```bash
/f5-req prioritize docs/requirements.md --method wsjf
```

Formula:
```
WSJF = (Business Value + Time Criticality + Risk Reduction) / Job Size
```

| Factor | Scale | Description |
|--------|-------|-------------|
| Business Value | 1-10 | Revenue/customer impact |
| Time Criticality | 1-10 | Time-sensitive value decay |
| Risk Reduction | 1-10 | Risk/opportunity enablement |
| Job Size | 1-10 | Implementation effort |

### Value-Effort Matrix

```bash
/f5-req prioritize docs/requirements.md --method value-effort
```

```
         VALUE
    High ┃ Quick Wins │ Big Bets
         ┃ (Do First) │ (Plan Carefully)
    ─────╋────────────┼────────────────
    Low  ┃ Fill-ins   │ Money Pits
         ┃ (Do If Time)│ (Avoid)
         ┗━━━━━━━━━━━━┷━━━━━━━━━━━━━━━━
              Low           High
                    EFFORT
```

| Quadrant | Strategy |
|----------|----------|
| Quick Wins | Do first - high ROI |
| Big Bets | Plan carefully - break into smaller pieces |
| Fill-ins | Do if time permits |
| Money Pits | Avoid or defer |

## Dependency Analysis

### Command

```bash
/f5-req dependencies docs/requirements.md
```

### Dependency Issues

| Issue | Risk | Solution |
|-------|------|----------|
| Circular Dependency | Blocks implementation | Break the cycle |
| Deep Chain | Change propagation | Modularize |
| Single Point of Failure | High risk | Add redundancy |
| Orphan Requirement | Lost context | Link to parent |

### Circular Dependency Example

```
REQ-001 → REQ-002 → REQ-003 → REQ-001
    ↑__________________________|

Problem: Cannot determine implementation order
Solution: Review and break the cycle
```

### Implementation Order

Based on dependencies, requirements are ordered:

```
Level 0 (No dependencies):
- REQ-010: Database connection
- REQ-011: Configuration loading

Level 1 (Depends on Level 0):
- REQ-001: User model
- REQ-002: Authentication service

Level 2 (Depends on Level 1):
- REQ-003: Login endpoint
- REQ-004: Registration endpoint
```

## Test Generation

### Command

```bash
/f5-req tests docs/requirements.md --format bdd
/f5-req tests docs/requirements.md --format unit --framework jest
```

### BDD Format (Gherkin)

```gherkin
Feature: User Authentication
  As a registered user
  I want to log in to my account
  So that I can access protected features

  Background:
    Given the system is running
    And the database is connected

  Scenario: Successful login with valid credentials
    Given I am on the login page
    And I have a valid account
    When I enter my email "user@example.com"
    And I enter my password "SecurePass123!"
    And I click the "Login" button
    Then I should be redirected to the dashboard
    And I should see a welcome message

  Scenario: Failed login with invalid password
    Given I am on the login page
    When I enter my email "user@example.com"
    And I enter an incorrect password
    And I click the "Login" button
    Then I should see an error message "Invalid credentials"
    And I should remain on the login page
```

### Unit Test Format (Jest)

```typescript
describe('AuthService', () => {
  describe('REQ-001: User authentication with JWT', () => {
    it('should return JWT token for valid credentials', async () => {
      // Arrange
      const credentials = { email: 'user@example.com', password: 'SecurePass123!' };

      // Act
      const result = await authService.authenticate(credentials);

      // Assert
      expect(result.token).toBeDefined();
      expect(result.expiresIn).toBe(86400);
    });

    it('should throw UnauthorizedException for invalid password', async () => {
      // Arrange
      const credentials = { email: 'user@example.com', password: 'wrong' };

      // Act & Assert
      await expect(authService.authenticate(credentials))
        .rejects.toThrow(UnauthorizedException);
    });
  });
});
```

## Improvement Suggestions

### Command

```bash
/f5-req improve docs/requirements.md
/f5-req improve docs/requirements.md --apply
```

### Example Improvements

**Original:**
> REQ-005: System should load pages quickly and handle errors appropriately.

**Issues:**
- "quickly" is ambiguous
- "appropriately" is subjective
- Multiple concerns in one requirement

**Suggested Rewrite:**
> REQ-005a: Page Loading Performance
> The system shall load all pages within 2 seconds on broadband connections (minimum 10 Mbps).
>
> REQ-005b: Error Handling
> The system shall display user-friendly error messages for all failure scenarios, including:
> - Network timeout: "Please check your connection"
> - Server error: "Something went wrong. Please try again."
> - Validation error: Specific field-level messages

## Integration

### With BA Workflow

```bash
# After BA documentation
/f5-ba document --srs

# Check quality
/f5-req analyze ba-workflow/phase-4-documentation/documents/srs.md

# Improve if needed
/f5-req improve ba-workflow/phase-4-documentation/documents/srs.md

# Prioritize for implementation
/f5-req prioritize ba-workflow/phase-4-documentation/documents/srs.md --method moscow
```

### With Strict Mode

```bash
# Ensure quality before strict implementation
/f5-req score requirements.md

# Only proceed if Grade A or B
# Grade C or lower: improve first
/f5-req improve requirements.md --apply

# Then start strict mode
/f5-strict start requirements.md
```

### With Import

```bash
# Import from Excel
/f5-import requirements.xlsx

# Analyze imported requirements
/f5-req analyze .f5/input/requirements/parsed-data.json

# Fix issues before using
```

## Best Practices

### Writing Good Requirements

1. **Use "shall" for mandatory requirements**
   - Good: "The system shall..."
   - Bad: "The system should..."

2. **One requirement, one concern**
   - Good: Separate performance and functionality
   - Bad: "System shall be fast and secure"

3. **Include acceptance criteria**
   - Good: "Response time < 200ms for 95% of requests"
   - Bad: "System responds quickly"

4. **Reference sources**
   - Good: "Source: BR-005, Stakeholder: Product Owner"
   - Bad: No traceability

5. **Use consistent terminology**
   - Good: Define terms in glossary, use consistently
   - Bad: "user", "customer", "client" interchangeably

### Review Checklist

Before finalizing requirements:

- [ ] All ambiguous terms replaced with specific values
- [ ] All CRUD operations covered for each entity
- [ ] Error handling defined for all scenarios
- [ ] Security requirements explicit
- [ ] Performance criteria measurable
- [ ] Accessibility requirements included
- [ ] Dependencies documented
- [ ] Acceptance criteria testable
- [ ] Traceability to source complete

## Troubleshooting

### Low Quality Score

1. Run analysis to identify issues:
   ```bash
   /f5-req analyze requirements.md
   ```

2. Address issues by category:
   ```bash
   /f5-req ambiguity requirements.md
   /f5-req gaps requirements.md
   ```

3. Apply improvements:
   ```bash
   /f5-req improve requirements.md --apply
   ```

### Circular Dependencies

1. Identify cycles:
   ```bash
   /f5-req dependencies requirements.md
   ```

2. Review each cycle
3. Break by:
   - Merging requirements
   - Introducing interface/abstraction
   - Redefining scope

### Missing Test Cases

1. Generate tests:
   ```bash
   /f5-req tests requirements.md --coverage full
   ```

2. Review generated tests
3. Add manual edge cases
4. Link tests to requirements

## Metrics

### Quality Metrics

| Metric | Target | Description |
|--------|--------|-------------|
| Ambiguity Score | <10 | Lower is better |
| Completeness | >90% | All fields present |
| Consistency | 100% | No contradictions |
| Testability | >95% | Measurable criteria |
| Traceability | 100% | All items linked |

### Process Metrics

| Metric | Target | Description |
|--------|--------|-------------|
| First-pass Grade | B+ | Initial quality |
| Improvement Rate | >20% | Score improvement |
| Gap Resolution | 100% | All gaps addressed |

---

*F5 Framework - Requirement Quality Guide v1.0*
