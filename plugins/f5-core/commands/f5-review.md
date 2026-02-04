---
description: Code review and quality checks
argument-hint: <check|full|security|pr> [path]
---

# F5 Code Review Command

Code review toàn diện với security focus, OWASP compliance, và quality metrics.

---

## USAGE

```bash
/f5-review <subcommand> [path] [options]
```

### Subcommands

| Command | Description |
|---------|-------------|
| `check [path]` | Quick review (lint, types, complexity) |
| `full [path]` | Full review với 6 categories |
| `security [path]` | Security-focused OWASP review |
| `pr` | Review PR/branch changes |
| `report` | Generate G2 review report |
| `status` | Show review history |

### Options

| Option | Description |
|--------|-------------|
| `--fix` | Auto-fix issues where possible |
| `--strict` | Fail on warnings |
| `--output <format>` | Output format: markdown, json, html |
| `--save` | Save report to `.f5/reviews/` |
| `--ci` | CI mode (non-interactive, exit codes) |

---

## WORKFLOW

```
┌───────────────────────────────────────────────────────────────────────┐
│                        CODE REVIEW WORKFLOW                            │
├───────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  1. DETECT STACK       2. LOAD RULES        3. ANALYZE                │
│  ──────────────        ──────────           ────────                  │
│  • Read config.json    • Load lint config   • Run lint/type checks    │
│  • Identify stack      • Load security      • Check complexity        │
│  • Load tools          • Load patterns      • Scan for issues         │
│        ↓                     ↓                    ↓                    │
│  4. CATEGORIZE         5. SCORE             6. REPORT                 │
│  ───────────           ─────                ──────                    │
│  • Architecture        • Calculate scores   • Generate report         │
│  • Quality             • Weight by priority • Prioritize actions      │
│  • Security            • Determine grade    • Save to .f5/reviews/    │
│  • Performance                                                         │
│                                                                        │
└───────────────────────────────────────────────────────────────────────┘
```

---

## STEP 1: DETECT STACK & TOOLS

Tự động detect từ `.f5/config.json`:

| Stack | Lint Tool | Type Check | Format | Complexity | Security |
|-------|-----------|------------|--------|------------|----------|
| nestjs | ESLint | tsc | Prettier | complexity-report | npm audit |
| spring | Checkstyle | javac | google-java-format | PMD | OWASP DC |
| fastapi | Ruff/Flake8 | mypy | Black | radon | bandit |
| go | golint | go vet | gofmt | gocyclo | gosec |
| django | Ruff/Flake8 | mypy | Black | radon | bandit |
| laravel | PHP_CodeSniffer | PHPStan | PHP-CS-Fixer | PHPMD | phpstan |
| rails | Rubocop | Sorbet | Rubocop | flog | brakeman |
| react | ESLint | tsc | Prettier | complexity-report | npm audit |
| nextjs | ESLint | tsc | Prettier | complexity-report | npm audit |
| vue | ESLint | vue-tsc | Prettier | complexity-report | npm audit |
| angular | ESLint | tsc | Prettier | complexity-report | npm audit |
| flutter | flutter_lints | dart analyze | dart format | - | - |

---

## REVIEW TYPES

### 1. `/f5-review check [path]` - Quick Check

Kiểm tra nhanh các vấn đề cơ bản:

| Category | Checks | Tool |
|----------|--------|------|
| Lint | ESLint/TSLint rules | eslint |
| Types | TypeScript errors | tsc |
| Format | Prettier compliance | prettier |
| Complexity | Cyclomatic complexity | complexity-report |
| Duplication | Code duplication | jscpd |

#### Commands by Stack

**NestJS/TypeScript:**
```bash
# Lint
npm run lint

# Type check
npx tsc --noEmit

# Format check
npx prettier --check "src/**/*.ts"

# Complexity
npx complexity-report src/
```

**FastAPI/Python:**
```bash
# Lint
ruff check .

# Type check
mypy app/

# Format check
black --check app/
isort --check-only app/

# Complexity
radon cc app/ -a
```

**Go:**
```bash
# Lint
golangci-lint run

# Vet
go vet ./...

# Format check
gofmt -l .

# Complexity
gocyclo -over 10 .
```

#### Output Format

```markdown
## 🔍 Quick Review: {{PATH}}

### Lint Issues
| Severity | Count |
|----------|-------|
| 🔴 Error | 2 |
| 🟡 Warning | 5 |
| 🔵 Info | 3 |

**Errors:**
1. `src/user/user.service.ts:45` - 'userId' is defined but never used (@typescript-eslint/no-unused-vars)
2. `src/auth/auth.controller.ts:23` - Unexpected any type (@typescript-eslint/no-explicit-any)

**Warnings:**
1. `src/order/order.service.ts:12` - Missing return type on function (@typescript-eslint/explicit-function-return-type)
2. `src/product/product.service.ts:78` - Prefer const over let (@typescript-eslint/prefer-const)

### Type Check
| Status | Count |
|--------|-------|
| ✅ Pass | - |
| ❌ Errors | 0 |

### Format Check
| Status | Files |
|--------|-------|
| ✅ Formatted | 45 |
| ⚠️ Need Format | 3 |

**Files needing format:**
- `src/user/user.service.ts`
- `src/auth/dto/login.dto.ts`
- `src/order/order.controller.ts`

### Complexity Analysis
| File | Function | Complexity | Status |
|------|----------|------------|--------|
| user.service.ts | processOrder | 15 | ⚠️ High (>10) |
| order.service.ts | calculateTotal | 12 | ⚠️ High (>10) |
| auth.service.ts | validateToken | 5 | ✅ OK |

### Code Duplication
| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Duplication | 3.5% | <5% | ✅ |

**Duplicated Blocks:**
1. `user.service.ts:20-35` ↔ `admin.service.ts:15-30` (80% similar)

### Summary
| Check | Status |
|-------|--------|
| Lint | ⚠️ 2 errors, 5 warnings |
| Types | ✅ Pass |
| Format | ⚠️ 3 files need formatting |
| Complexity | ⚠️ 2 high complexity functions |
| Duplication | ✅ Pass |

### Action Required
1. 🔴 **Fix lint errors** before committing
2. 🟡 Run `npm run format` to fix formatting
3. 🟡 Consider refactoring high complexity functions

### Quick Fix Commands
```bash
# Fix lint issues
npm run lint:fix

# Fix formatting
npm run format

# Check again
/f5-review check
```
```

---

### 2. `/f5-review full [path]` - Full Review

Review toàn diện với 6 categories:

#### Review Categories

**1. Architecture Compliance**
- Layer separation (Controller → Service → Repository)
- Dependency injection patterns
- Module structure và organization
- API design patterns (RESTful, GraphQL)
- Single Responsibility Principle
- Separation of Concerns

**2. Code Quality**
- Naming conventions (camelCase, PascalCase)
- Code duplication (target: <5%)
- Cyclomatic complexity (target: <10)
- Function length (target: <20 lines)
- Comments và documentation
- Magic numbers và hardcoded values
- DRY principle compliance

**3. Error Handling**
- Try-catch coverage
- Custom exception classes
- Error logging với stack traces
- User-friendly error messages
- No sensitive data in errors
- Proper HTTP status codes
- Graceful degradation

**4. Security (OWASP Top 10)**
- A01: Broken Access Control
- A02: Cryptographic Failures
- A03: Injection (SQL, XSS, Command)
- A04: Insecure Design
- A05: Security Misconfiguration
- A06: Vulnerable Components
- A07: Authentication Failures
- A08: Data Integrity Failures
- A09: Logging Failures
- A10: SSRF

**5. Testing**
- Test coverage (target: ≥80%)
- Test quality và readability
- Edge cases coverage
- Mocking strategy
- Test naming conventions
- Integration tests

**6. Performance**
- N+1 queries detection
- Memory leak potential
- Async/await patterns
- Caching opportunities
- Database indexing suggestions
- Lazy loading

#### Output Format

```markdown
## 📋 Full Code Review

**Path:** {{PATH}}
**Date:** {{DATE}}
**Reviewer:** F5 Automated Review

---

### 1. Architecture Compliance - Score: 90/100 ✅

| Check | Status | Details |
|-------|--------|---------|
| Layer separation | ✅ | Controller → Service → Repository properly implemented |
| Dependency injection | ✅ | Using NestJS DI container correctly |
| Module structure | ✅ | Feature-based modules with clear boundaries |
| API design | ⚠️ | Missing pagination on list endpoints |
| Single Responsibility | ✅ | Services have focused responsibilities |

**Issues Found:**
1. **Missing pagination** - `GET /users` returns all records
   - Location: `user.controller.ts:25`
   - Recommendation: Add `@Query()` params for page/limit
   ```typescript
   @Get()
   async findAll(
     @Query('page') page: number = 1,
     @Query('limit') limit: number = 10,
   ) {
     return this.userService.findAll({ page, limit });
   }
   ```

---

### 2. Code Quality - Score: 75/100 ⚠️

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Cyclomatic Complexity (avg) | 6.2 | <10 | ✅ |
| Max Complexity | 15 | <10 | ⚠️ |
| Code Duplication | 3.5% | <5% | ✅ |
| Functions >20 lines | 4 | 0 | ⚠️ |
| Magic Numbers | 3 | 0 | ⚠️ |
| TODO Comments | 2 | 0 | ⚠️ |

**Issues Found:**
1. **High complexity function**
   - Location: `user.service.ts:processOrder()` - 45 lines, complexity 15
   - Recommendation: Split into smaller functions
   ```typescript
   // Before
   async processOrder(dto: OrderDto): Promise<Order> {
     // 45 lines of mixed logic
   }

   // After
   async processOrder(dto: OrderDto): Promise<Order> {
     this.validateOrder(dto);
     const total = this.calculateTotal(dto);
     const order = await this.createOrder(dto, total);
     await this.sendNotification(order);
     return order;
   }
   ```

2. **Magic numbers**
   - Location: `order.service.ts:78` - `if (total > 1000)`
   - Recommendation: Use named constant
   ```typescript
   const MAX_ORDER_WITHOUT_APPROVAL = 1000;
   if (total > MAX_ORDER_WITHOUT_APPROVAL) { }
   ```

3. **TODO remaining**
   - `auth.service.ts:45` - `// TODO: implement refresh token`
   - `user.service.ts:120` - `// TODO: add validation`

---

### 3. Error Handling - Score: 80/100 ⚠️

| Check | Status | Coverage |
|-------|--------|----------|
| Try-catch blocks | ✅ | 85% of async operations |
| Custom exceptions | ✅ | Using HttpException properly |
| Error logging | ⚠️ | Missing stack traces in some places |
| User-friendly messages | ✅ | Proper error responses |
| No sensitive data | ✅ | No credentials in errors |

**Issues Found:**
1. **Missing error logging**
   - Location: `payment.service.ts:56`
   - Issue: Catch block without logging
   ```typescript
   // Current
   catch (error) {
     throw new BadRequestException('Payment failed');
   }

   // Recommended
   catch (error) {
     this.logger.error('Payment failed', error.stack);
     throw new BadRequestException('Payment failed');
   }
   ```

2. **Missing try-catch**
   - Location: `user.service.ts:92`
   - Issue: Database operation without error handling
   ```typescript
   // Current
   const user = await this.userRepository.save(dto);

   // Recommended
   try {
     const user = await this.userRepository.save(dto);
     return user;
   } catch (error) {
     if (error.code === '23505') {
       throw new ConflictException('Email already exists');
     }
     throw error;
   }
   ```

---

### 4. Security - Score: 85/100 ⚠️

| OWASP | Vulnerability | Status | Severity |
|-------|---------------|--------|----------|
| A01 | Broken Access Control | ⚠️ Found | Medium |
| A02 | Cryptographic Failures | ✅ Safe | - |
| A03 | Injection | ✅ Safe | - |
| A04 | Insecure Design | ✅ Safe | - |
| A05 | Security Misconfiguration | ✅ Safe | - |
| A06 | Vulnerable Components | ⚠️ Found | Low |
| A07 | Authentication Failures | ✅ Safe | - |
| A08 | Data Integrity | ✅ Safe | - |
| A09 | Logging Failures | ⚠️ Found | Low |
| A10 | SSRF | ✅ Safe | - |

**Security Issues:**
1. **Missing Authorization Check** (Medium)
   - Location: `order.controller.ts:55`
   - Issue: DELETE endpoint accessible without role check
   - Fix: Add `@Roles('admin')` decorator
   ```typescript
   @Roles('admin')
   @UseGuards(RolesGuard)
   @Delete(':id')
   async deleteOrder(@Param('id') id: string) {}
   ```

2. **Outdated Dependencies** (Low)
   - `lodash@4.17.20` - Known vulnerabilities (CVE-2021-23337)
   - Fix: `npm audit fix`

---

### 5. Testing - Score: 82/100 ⚠️

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Statement Coverage | 85% | ≥80% | ✅ |
| Branch Coverage | 72% | ≥75% | ⚠️ |
| Function Coverage | 90% | ≥80% | ✅ |
| Line Coverage | 84% | ≥80% | ✅ |

**Uncovered Areas:**
1. `auth.service.ts:45-52` - Error handling block not tested
2. `order.service.ts:78-85` - Edge case for large orders

**Test Quality Issues:**
1. Missing negative test cases in `user.service.spec.ts`
2. Mocking strategy inconsistent in `order.service.spec.ts`

**Recommended Additional Tests:**
```typescript
it('should throw BadRequestException for invalid email', async () => {
  await expect(service.createUser({ email: 'invalid' }))
    .rejects.toThrow(BadRequestException);
});

it('should throw ConflictException for duplicate email', async () => {
  mockRepo.findOne.mockResolvedValue(existingUser);
  await expect(service.createUser(dto))
    .rejects.toThrow(ConflictException);
});
```

---

### 6. Performance - Score: 80/100 ⚠️

| Check | Status | Impact |
|-------|--------|--------|
| N+1 Queries | ⚠️ Found | High |
| Memory Leaks | ✅ Safe | - |
| Async Patterns | ✅ OK | - |
| Caching | ⚠️ Missing | Medium |
| Indexing | ⚠️ Suggested | Medium |

**Performance Issues:**
1. **N+1 Query Detected**
   - Location: `order.service.ts:getOrdersWithProducts()`
   - Issue: Loading products in loop
   ```typescript
   // Current (N+1)
   const orders = await this.orderRepo.find();
   for (const order of orders) {
     order.products = await this.productRepo.findByOrderId(order.id);
   }

   // Recommended (JOIN)
   const orders = await this.orderRepo.find({
     relations: ['products']
   });
   ```

2. **Missing Cache**
   - Location: `product.service.ts:getCategories()`
   - Recommendation: Add caching for rarely changing data
   ```typescript
   @Cacheable({ ttl: 3600 })
   async getCategories() {
     return this.categoryRepo.find();
   }
   ```

3. **Missing Database Index**
   - Column `orders.user_id` is frequently queried but not indexed
   - Add migration: `CREATE INDEX idx_orders_user_id ON orders(user_id);`

---

### Overall Score: 82/100 ⚠️

| Category | Score | Weight | Weighted |
|----------|-------|--------|----------|
| Architecture | 90 | 20% | 18.0 |
| Code Quality | 75 | 20% | 15.0 |
| Error Handling | 80 | 15% | 12.0 |
| Security | 85 | 25% | 21.25 |
| Testing | 82 | 10% | 8.2 |
| Performance | 80 | 10% | 8.0 |
| **Total** | - | 100% | **82.45** |

### Grade: B+

---

### Action Items

| Priority | Issue | Location | Action | Effort |
|----------|-------|----------|--------|--------|
| 🔴 High | Missing auth | order.controller.ts:55 | Add @Roles guard | 5min |
| 🔴 High | N+1 query | order.service.ts:120 | Use JOIN/relations | 15min |
| 🟡 Medium | Long function | user.service.ts:80 | Split into smaller | 30min |
| 🟡 Medium | Missing cache | product.service.ts:45 | Add caching | 20min |
| 🟡 Medium | Low branch coverage | tests/ | Add edge case tests | 1hr |
| 🟢 Low | Magic numbers | order.service.ts:78 | Extract constants | 5min |
| 🟢 Low | Outdated deps | package.json | npm audit fix | 10min |
| 🟢 Low | TODO comments | multiple | Implement or remove | 30min |

### Recommended Next Steps
1. Fix all 🔴 High priority issues before merging
2. Address 🟡 Medium issues in current sprint
3. Schedule 🟢 Low issues for tech debt sprint

### Quick Fix Commands
```bash
# Fix lint issues
npm run lint:fix

# Fix formatting
npm run format

# Update dependencies
npm audit fix

# Run tests with coverage
npm run test:cov
```
```

---

### 3. `/f5-review security [path]` - Security-Focused Review

OWASP Top 10 deep check với detailed analysis:

#### OWASP Top 10 2021 Checklist

| # | Category | Description | Checks |
|---|----------|-------------|--------|
| A01 | Broken Access Control | Access control enforcement | Role checks, RBAC, resource authorization, IDOR |
| A02 | Cryptographic Failures | Sensitive data protection | Password hashing, encryption, TLS, secrets |
| A03 | Injection | User input handling | SQL, XSS, Command, LDAP injection |
| A04 | Insecure Design | Security by design | Threat modeling, secure patterns |
| A05 | Security Misconfiguration | Hardening | Default configs, error messages, headers |
| A06 | Vulnerable Components | Dependencies | Dependency scanning, CVE checking |
| A07 | Authentication Failures | Identity verification | Brute force, session management, MFA |
| A08 | Data Integrity | Data validation | CSRF, code signing, CI/CD security |
| A09 | Logging Failures | Security monitoring | Audit logs, log injection, alerting |
| A10 | SSRF | Server-side requests | URL validation, allow lists, DNS rebinding |

#### Output Format

```markdown
## 🔒 Security Review

**Path:** {{PATH}}
**Date:** {{DATE}}
**Standard:** OWASP Top 10 2021

---

### Executive Summary

| Severity | Count |
|----------|-------|
| 🔴 Critical | 0 |
| 🟠 High | 1 |
| 🟡 Medium | 2 |
| 🔵 Low | 3 |
| ✅ Info | 2 |

**Security Score: 85/100** ⚠️

---

### OWASP Top 10 Analysis

#### A01: Broken Access Control ⚠️ FOUND

**Status:** Issues Found
**Severity:** High

**Checks Performed:**
- [x] Role-based access control
- [x] Resource ownership validation
- [x] Horizontal privilege escalation
- [x] Vertical privilege escalation
- [ ] IDOR protection

**Findings:**
1. **Missing Role Check on DELETE Endpoint**
   - Location: `order.controller.ts:55`
   - Description: DELETE endpoint accessible to all authenticated users
   - Impact: Any user can delete any order
   - CVSS Score: 7.5 (High)

   **Vulnerable Code:**
   ```typescript
   @Delete(':id')
   async deleteOrder(@Param('id') id: string) {
     return this.orderService.delete(id);
   }
   ```

   **Remediation:**
   ```typescript
   @Roles('admin')
   @UseGuards(RolesGuard)
   @Delete(':id')
   async deleteOrder(@Param('id') id: string) {
     return this.orderService.delete(id);
   }
   ```

2. **Missing Resource Ownership Check**
   - Location: `user.controller.ts:42`
   - Description: Users can access other users' profiles
   - CVSS Score: 6.5 (Medium)

   **Remediation:**
   ```typescript
   @Get(':id')
   async findOne(@Param('id') id: string, @Req() req) {
     if (req.user.id !== id && !req.user.roles.includes('admin')) {
       throw new ForbiddenException();
     }
     return this.userService.findOne(id);
   }
   ```

---

#### A02: Cryptographic Failures ✅ SECURE

**Status:** Secure
**Checks Passed:**
- [x] Passwords hashed with bcrypt (cost factor 12)
- [x] Sensitive data encrypted at rest (AES-256)
- [x] TLS 1.2+ enforced
- [x] No hardcoded secrets
- [x] Secure random number generation
- [x] No weak algorithms (MD5, SHA1)

**Evidence:**
```typescript
// Password hashing
const hash = await bcrypt.hash(password, 12);

// Environment variables for secrets
const jwtSecret = this.configService.get('JWT_SECRET');
```

---

#### A03: Injection ✅ SECURE

**Status:** Secure
**Checks Passed:**
- [x] Parameterized queries (TypeORM)
- [x] Input validation with class-validator
- [x] Output encoding for XSS prevention
- [x] No shell command execution
- [x] No LDAP queries
- [x] No dynamic SQL construction

**Evidence:**
```typescript
// Safe - Using TypeORM parameterized queries
const user = await this.userRepo.findOne({ where: { email } });

// Safe - Using class-validator
@IsEmail()
@IsNotEmpty()
email: string;

// Safe - Sanitizing output
import * as sanitizeHtml from 'sanitize-html';
const clean = sanitizeHtml(userInput);
```

---

#### A04: Insecure Design ✅ SECURE

**Status:** Secure
**Checks Passed:**
- [x] Input validation at boundaries
- [x] Rate limiting implemented
- [x] Business logic protected
- [x] Fail-secure defaults
- [x] Defense in depth applied

---

#### A05: Security Misconfiguration ⚠️ FOUND

**Status:** Issues Found
**Severity:** Low

**Findings:**
1. **Verbose Error Messages in Production**
   - Location: `main.ts`
   - Issue: Stack traces exposed in error responses
   - **Remediation:**
   ```typescript
   if (process.env.NODE_ENV === 'production') {
     app.useGlobalFilters(new ProductionExceptionFilter());
   }
   ```

2. **Missing Security Headers**
   - Missing: `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`
   - **Remediation:** Use helmet middleware
   ```typescript
   import helmet from 'helmet';
   app.use(helmet());
   ```

**Security Headers Check:**
| Header | Status | Recommendation |
|--------|--------|----------------|
| X-Content-Type-Options | ❌ Missing | Add `nosniff` |
| X-Frame-Options | ❌ Missing | Add `DENY` |
| Strict-Transport-Security | ✅ Present | - |
| Content-Security-Policy | ⚠️ Weak | Strengthen policy |
| X-XSS-Protection | ❌ Missing | Add `1; mode=block` |

---

#### A06: Vulnerable Components ⚠️ FOUND

**Status:** Issues Found
**Severity:** Medium

**Vulnerable Dependencies:**
| Package | Current | Vulnerable | CVE | Severity |
|---------|---------|------------|-----|----------|
| lodash | 4.17.20 | <4.17.21 | CVE-2021-23337 | High |
| axios | 0.21.1 | <0.21.2 | CVE-2021-3749 | Medium |
| node-fetch | 2.6.1 | <2.6.7 | CVE-2022-0235 | High |

**Remediation:**
```bash
# Check vulnerabilities
npm audit

# Fix vulnerabilities
npm audit fix

# Update specific packages
npm update lodash axios node-fetch
```

---

#### A07: Authentication Failures ✅ SECURE

**Status:** Secure
**Checks Passed:**
- [x] JWT with proper expiration (15min access, 7d refresh)
- [x] Password complexity requirements
- [x] Account lockout after 5 failed attempts
- [x] Secure password reset flow
- [x] No credentials in logs
- [x] HTTPS only cookies

**Evidence:**
```typescript
// JWT configuration
{
  expiresIn: '15m',
  algorithm: 'RS256'
}

// Password validation
@Matches(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/)
password: string;
```

---

#### A08: Data Integrity Failures ✅ SECURE

**Status:** Secure
**Checks Passed:**
- [x] CSRF protection enabled
- [x] Digital signatures on critical data
- [x] CI/CD pipeline secured
- [x] Input validation for deserialization

---

#### A09: Logging Failures ⚠️ FOUND

**Status:** Issues Found
**Severity:** Low

**Findings:**
1. **Missing Audit Logs for Sensitive Operations**
   - Location: `user.service.ts`
   - Missing logs for: Login attempts, password changes, role modifications

   **Remediation:**
   ```typescript
   async changePassword(userId: string, newPassword: string): Promise<void> {
     await this.auditLogger.log({
       action: 'PASSWORD_CHANGE',
       userId,
       timestamp: new Date(),
       ip: this.request.ip
     });
     // ... implementation
   }
   ```

2. **No Log Injection Prevention**
   - Location: `logger.service.ts`
   - **Remediation:** Sanitize log inputs

---

#### A10: SSRF ✅ SECURE

**Status:** Secure
**Checks Passed:**
- [x] No user-controlled URLs in server requests
- [x] URL validation if external requests needed
- [x] DNS rebinding protection
- [x] Private IP blocking

---

### Security Score by Category

| Category | Score |
|----------|-------|
| Authentication | 95/100 |
| Authorization | 70/100 |
| Data Protection | 90/100 |
| Input Validation | 95/100 |
| Dependencies | 75/100 |
| Configuration | 80/100 |
| Logging | 70/100 |
| **Overall** | **85/100** |

---

### Recommendations

#### Immediate Actions (Do Now)
1. Add role-based access control to DELETE endpoints
2. Add ownership validation for user resources
3. Run `npm audit fix`

#### Short-term (This Sprint)
1. Configure helmet for security headers
2. Implement audit logging for sensitive operations
3. Configure production error handling

#### Long-term (Backlog)
1. Implement comprehensive audit trail
2. Set up security monitoring and alerting
3. Schedule regular dependency updates
4. Add automated security scanning to CI/CD

---

### Compliance Check

| Standard | Status |
|----------|--------|
| OWASP Top 10 2021 | ⚠️ 4 issues found |
| PCI-DSS (if applicable) | ⚠️ Audit logs needed |
| GDPR (if applicable) | ✅ Data protection OK |
| HIPAA (if applicable) | ⚠️ Logging needed |

---

### Security Commands
```bash
# Run dependency audit
npm audit

# Fix vulnerabilities
npm audit fix

# Check for secrets in code
npx secretlint "**/*"

# Run security linter
npm run lint:security

# SAST scan
npx snyk test
```
```

---

### 4. `/f5-review pr` - PR/Branch Review

Review changes trong current branch so với base:

```bash
# Get changed files
git diff --name-only main...HEAD

# Get detailed diff
git diff main...HEAD
```

#### Output Format

```markdown
## 📝 Pull Request Review

**Branch:** feature/user-registration
**Base:** main
**Author:** developer@example.com
**Date:** {{DATE}}

---

### Change Summary

| Metric | Value |
|--------|-------|
| Files Changed | 12 |
| Lines Added | +450 |
| Lines Removed | -23 |
| Net Change | +427 |

### Changed Files

| File | Changes | Type | Status |
|------|---------|------|--------|
| user.module.ts | +15/-2 | Module | ✅ LGTM |
| user.service.ts | +120/-5 | Service | ⚠️ Review |
| user.controller.ts | +80/-3 | Controller | ✅ LGTM |
| user.entity.ts | +45/-0 | Entity | ✅ LGTM |
| create-user.dto.ts | +35/-0 | DTO | ✅ LGTM |
| user.service.spec.ts | +85/-0 | Test | ⚠️ Review |

---

### Review Comments

#### user.service.ts ⚠️

**Line 45-60: Consider extracting validation logic**
```typescript
// Current
async createUser(dto: CreateUserDto): Promise<User> {
  if (dto.email && dto.email.includes('@') && dto.email.length > 5) {
    if (dto.password && dto.password.length >= 8) {
      // ... more validation
    }
  }
}

// Suggested
async createUser(dto: CreateUserDto): Promise<User> {
  this.validateCreateUserDto(dto);
  // ... clean business logic
}

private validateCreateUserDto(dto: CreateUserDto): void {
  // Validation logic here
}
```

**Line 78: Potential N+1 Query**
```typescript
// Current - N+1 query
for (const user of users) {
  user.orders = await this.orderRepo.findByUserId(user.id);
}

// Suggested - Use JOIN
const users = await this.userRepo.find({
  relations: ['orders']
});
```

**Line 95: Missing error handling**
```typescript
// Current
const result = await this.externalService.call();
return result;

// Suggested
try {
  const result = await this.externalService.call();
  return result;
} catch (error) {
  this.logger.error('External service failed', error.stack);
  throw new ServiceUnavailableException('External service unavailable');
}
```

---

#### user.service.spec.ts ⚠️

**Missing negative test cases**
```typescript
// Add these tests
it('should throw BadRequestException for invalid email', async () => {
  await expect(service.createUser({ email: 'invalid' }))
    .rejects.toThrow(BadRequestException);
});

it('should throw ConflictException for duplicate email', async () => {
  mockRepo.findOne.mockResolvedValue(existingUser);
  await expect(service.createUser(dto))
    .rejects.toThrow(ConflictException);
});

it('should handle database failure gracefully', async () => {
  mockRepo.save.mockRejectedValue(new Error('Connection lost'));
  await expect(service.createUser(dto))
    .rejects.toThrow(HttpException);
});
```

---

### Checklist

#### Code Quality
- [x] Follows project conventions
- [x] No linting errors
- [ ] No TODO comments left
- [x] Proper error handling
- [ ] Functions <20 lines

#### Testing
- [x] Unit tests added
- [ ] Negative test cases
- [x] Coverage maintained (>80%)
- [ ] Integration tests if needed

#### Security
- [x] Input validation present
- [x] No hardcoded secrets
- [x] Proper authorization
- [x] No SQL injection risk

#### Documentation
- [x] Code comments where needed
- [ ] API documentation updated
- [x] CHANGELOG updated
- [x] Traceability comments added

---

### Automated Checks

| Check | Status |
|-------|--------|
| Build | ✅ Passed |
| Unit Tests | ✅ 87 passed |
| Lint | ✅ No errors |
| Type Check | ✅ No errors |
| Coverage | ⚠️ 78% (target: 80%) |
| Security Scan | ✅ No vulnerabilities |

---

### Verdict: **Request Changes** 🔄

**Blockers (Must Fix):**
1. Add negative test cases to reach 80% coverage
2. Fix potential N+1 query in user.service.ts:78

**Suggestions (Nice to Have):**
1. Extract validation logic for readability
2. Add error handling for external service call

---

### Actions
```bash
# Address review comments
# Then re-request review:
git add .
git commit -m "fix: address PR review comments"
git push

# Re-run review
/f5-review pr
```
```

---

### 5. `/f5-review report` - Generate G2 Report

Generate comprehensive review report for G2 gate documentation:

```markdown
## 📋 Code Review Report

**Project:** {{PROJECT_NAME}}
**Date:** {{DATE}}
**Reviewer:** F5 Automated Review
**Version:** {{VERSION}}

---

### Executive Summary

| Metric | Value | Status |
|--------|-------|--------|
| Files Reviewed | 45 | - |
| Total Issues | 12 | - |
| Critical | 0 | ✅ |
| High | 2 | ⚠️ |
| Medium | 5 | - |
| Low | 5 | - |

### Quality Scores

| Category | Score | Status |
|----------|-------|--------|
| Architecture | 90/100 | ✅ |
| Code Quality | 82/100 | ⚠️ |
| Error Handling | 85/100 | ✅ |
| Security | 88/100 | ⚠️ |
| Testing | 85/100 | ✅ |
| Performance | 80/100 | ⚠️ |
| **Overall** | **85/100** | **⚠️** |

### Grade: B+

---

### Issues Summary

#### By Severity

| Severity | Count | Fixed | Remaining |
|----------|-------|-------|-----------|
| 🔴 Critical | 0 | 0 | 0 |
| 🟠 High | 2 | 0 | 2 |
| 🟡 Medium | 5 | 2 | 3 |
| 🔵 Low | 5 | 3 | 2 |

#### By Category

| Category | Issues |
|----------|--------|
| Architecture | 2 |
| Code Quality | 4 |
| Error Handling | 2 |
| Security | 2 |
| Testing | 1 |
| Performance | 1 |

---

### Blocking Issues (Must Fix)

1. **Missing Authorization** - `order.controller.ts:55`
   - Severity: High
   - Category: Security (A01)
   - Action: Add @Roles guard

2. **N+1 Query** - `order.service.ts:120`
   - Severity: High
   - Category: Performance
   - Action: Use eager loading

---

### G2 Gate Status

**Status: ⚠️ CONDITIONAL PASS**

| Requirement | Target | Actual | Status |
|-------------|--------|--------|--------|
| Critical Issues | 0 | 0 | ✅ |
| High Issues | 0 | 2 | ❌ |
| Lint Errors | 0 | 0 | ✅ |
| Type Errors | 0 | 0 | ✅ |
| Security Vulnerabilities | 0 critical | 0 | ✅ |
| Test Coverage | ≥80% | 85% | ✅ |

**Action Required:** Fix 2 high severity issues before G2 approval.

---

### Recommendations

1. **Before G2 Completion:**
   - Fix authorization issue
   - Fix N+1 query issue
   - Update vulnerable dependencies

2. **Technical Debt to Track:**
   - Refactor long functions (4 instances)
   - Improve test coverage for edge cases
   - Add pagination to list endpoints

---

### Sign-off

- [ ] Development Lead Approval
- [ ] Security Review (if required)
- [ ] Architecture Review (if required)

**Report Generated:** {{TIMESTAMP}}
**Report Location:** `.f5/quality/G2-review-report.md`
```

---

## INTEGRATION

### với Stack Skills

Load security và quality patterns từ:
```
stacks/
├── backend/
│   ├── nestjs/skills/security/
│   ├── spring/skills/security/
│   ├── fastapi/skills/security/
│   └── go/skills/security/
├── frontend/
│   ├── react/skills/security/
│   ├── nextjs/skills/security/
│   └── vue/skills/security/
└── mobile/
    └── flutter/skills/security/
```

### với G2 Gate

Khi `/f5-gate check G2`, tự động:

1. Run `/f5-review check` - Quick lint/type check
2. Run `/f5-review security` - Security review
3. Verify no critical/high issues
4. Run `/f5-review report` - Generate report
5. Save report to `.f5/quality/`

#### G2 Gate Requirements

| Requirement | Threshold | Description |
|-------------|-----------|-------------|
| Critical Issues | 0 | No critical security/quality issues |
| High Issues | 0 | All high issues must be resolved |
| Lint Errors | 0 | No lint errors |
| Type Errors | 0 | No TypeScript errors |
| Security Vulns | 0 critical/high | No critical/high CVEs |
| Code Duplication | <5% | Acceptable duplication level |
| Complexity (max) | <15 | Maximum cyclomatic complexity |

---

## CONFIGURATION

### Review Settings

Configure trong `.f5/config.json`:

```json
{
  "review": {
    "enabled": true,
    "autoRun": {
      "onCommit": true,
      "onPR": true
    },
    "thresholds": {
      "complexity": {
        "max": 10,
        "warning": 8
      },
      "duplication": {
        "max": 5,
        "warning": 3
      },
      "coverage": {
        "min": 80,
        "warning": 85
      },
      "functionLength": {
        "max": 20,
        "warning": 15
      }
    },
    "security": {
      "failOnCritical": true,
      "failOnHigh": true,
      "failOnMedium": false
    },
    "exclude": [
      "**/*.spec.ts",
      "**/*.test.ts",
      "**/node_modules/**",
      "**/dist/**",
      "**/*.d.ts"
    ]
  }
}
```

---

## OUTPUT FORMATS

### Markdown (Default)
```bash
/f5-review full src/ --output markdown
```

### JSON
```bash
/f5-review full src/ --output json --save
```

### HTML Report
```bash
/f5-review full src/ --output html --save
```

Saves to `.f5/reviews/review-{{DATE}}.{md|json|html}`

---

## EXAMPLES

### Quick Check Before Commit
```bash
/f5-review check src/modules/user/
```

### Full Review for PR
```bash
/f5-review full src/ --save
```

### Security Audit
```bash
/f5-review security src/ --strict
```

### PR Review
```bash
/f5-review pr
```

### Generate G2 Report
```bash
/f5-review report --format md --save
```

### Fix and Re-check
```bash
# Fix lint issues
npm run lint:fix

# Fix formatting
npm run format

# Update dependencies
npm audit fix

# Re-check
/f5-review check src/
```

---

## IMPORTANT RULES

1. **Fix all lint errors** - No exceptions, lint errors block commits
2. **Fix all type errors** - TypeScript strict mode required
3. **Address security issues** - Critical/High must be fixed immediately
4. **Code review before merge** - All PRs must be reviewed
5. **Document exceptions** - If skipping a rule, document why in ADR

---

## NEXT STEPS

After review completion:

```bash
# If issues found
1. Fix critical/high issues
2. Run /f5-review check again
3. Proceed when all checks pass

# If all passed
1. /f5-gate check G2
2. Generate report: /f5-review report --save
3. Proceed to implementation or testing
```

---

*F5 Framework - Code Review Command*
