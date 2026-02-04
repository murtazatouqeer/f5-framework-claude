---
description: Implement features and fix bugs with traceability
argument-hint: <feature|fix> [--tdd|--with-tests]
mcp-servers: context7, serena
---

# /f5-implement - Unified Implementation Command

**Consolidated command** that replaces:
- `/f5-fix` → `/f5-implement fix`

Implement features and fix bugs with high quality, TDD support, and best practices.

## ARGUMENTS
$ARGUMENTS

## MODE DETECTION

| Pattern | Mode | Description |
|---------|------|-------------|
| `fix <bug-id\|desc>` | FIX | Bug fix workflow |
| `fix list` | FIX_LIST | List all bugs |
| `fix done <id>` | FIX_DONE | Mark bug as fixed |
| `fix verify <id>` | FIX_VERIFY | Re-verify fix |
| `<other>` (default) | IMPLEMENT | Feature implementation |

---

## MODE: FIX (from /f5-fix)

### `/f5-implement fix <bug-id|description>`

Structured workflow for fixing issues with traceability.

| Action | Description |
|--------|-------------|
| `<bug-id>` | Fix specific bug by ID |
| `"<description>"` | Fix by description (creates new bug) |
| `list` | List all bugs |
| `done <bug-id>` | Mark bug as fixed |
| `verify <bug-id>` | Re-verify after fix |
| `list --status open` | Filter open bugs |
| `list --severity high` | Filter by severity |

**Examples:**
```bash
/f5-implement fix BUG-001
/f5-implement fix "Hero image wrong size"
/f5-implement fix list
/f5-implement fix done BUG-001
/f5-implement fix verify BUG-001
```

---

## MODE: IMPLEMENT (Default)

Implement features with high quality and auto-agent support.

## STEP 0: PRE-FLIGHT CHECKS

### 0.1 Load Integration Config

```bash
# Load command integration settings from .f5/config/command-integration.yaml
INTEGRATION_CONFIG=".f5/config/command-integration.yaml"
if [ -f "$INTEGRATION_CONFIG" ]; then
  COMMAND_CONFIG=$(cat "$INTEGRATION_CONFIG" | yq '.command_integration.f5-implement')
fi
```

### 0.2 Check MCP Prerequisites

```markdown
📋 **MCP Pre-flight Check**

Required MCPs:
  - context7: [✅ Available / ⚠️ Not available]

Optional MCPs:
  - serena: [✅ Available / ○ Not configured]

{{#if MISSING_REQUIRED}}
⚠️ Missing required MCP: context7
Run: /f5-mcp install context7
Continuing with reduced capabilities...
{{/if}}
```

### 0.3 Load Developer Role

```bash
# Get developer role from config
ROLE=$(jq -r '.developer_role // "fullstack"' .f5/config.json 2>/dev/null)
echo "Developer Role: $ROLE"

# Get role-specific focus
case "$ROLE" in
  backend)
    FOCUS="API endpoints, services, repositories"
    AGENTS="code_generator, api_designer"
    ;;
  frontend)
    FOCUS="Components, hooks, state"
    AGENTS="code_generator"
    ;;
  fullstack)
    FOCUS="Full feature implementation"
    AGENTS="code_generator, api_designer"
    ;;
  *)
    FOCUS="General implementation"
    AGENTS="code_generator"
    ;;
esac
```

### 0.4 Prepare Auto-Invoke Agents

```markdown
🤖 **Agents to Auto-Invoke**

Based on role ($ROLE) and project settings:

| # | Agent | Purpose | Condition |
|---|-------|---------|-----------|
| 1 | ⚡ code_generator | Generate production-ready code | Always |
| 2 | 🧪 test_writer | Write comprehensive tests | TDD mode OR production |
| 3 | 📝 documenter | Generate documentation | Production only |

Focus: $FOCUS
```

### 0.5 Execute with Auto-Agents

**Step 1: MCP Enhancement (if available)**
```
If context7 available:
  → Fetch relevant documentation for detected stack
  → Apply latest patterns and best practices
  → Check for security advisories
```

**Step 2: Code Generator Agent**
```
⚡ Invoking code_generator...
  - Focus: {{FOCUS}}
  - Patterns: From .f5/memory/
  - Stack: {{DETECTED_STACK}}
  - Traceability: REQ-XXX comments
```

**Step 3: Test Writer Agent (conditional)**
```
{{#if TDD_MODE OR PROJECT_TYPE == 'production'}}
🧪 Invoking test_writer...
  - Coverage target: 80%
  - Include edge cases: true
  - Test naming: descriptive
{{/if}}
```

**Step 4: Documenter Agent (conditional)**
```
{{#if PROJECT_TYPE == 'production'}}
📝 Invoking documenter...
  - Inline documentation
  - API docs if applicable
  - README updates if needed
{{/if}}
```

## FLAGS

| Flag | Description |
|------|-------------|
| `--tdd` | Use TDD workflow (red-green-refactor) |
| `--with-tests` | Generate unit tests alongside implementation |
| `--with-it` | Generate integration tests alongside implementation |
| `--with-all-tests` | Generate UT + IT + E2E stubs |
| `--security` | Security-focused implementation with extra guards |
| `--performance` | Performance-focused implementation with optimization |
| `--scaffold` | Generate module structure only (no implementation) |
| `--dry-run` | Preview changes without writing files |

### Flag Examples

```bash
# Standard implementation
/f5-implement user-registration

# With TDD workflow
/f5-implement user-registration --tdd

# Security-focused (auth, encryption, guards)
/f5-implement authentication --security

# Performance-focused (caching, optimization)
/f5-implement product-listing --performance

# Generate structure only
/f5-implement order-management --scaffold

# Generate with unit tests
/f5-implement payment-processing --with-tests

# Generate with integration tests
/f5-implement order-api --with-it

# Generate all test types (UT + IT + E2E stubs)
/f5-implement checkout-flow --with-all-tests
```

### IT Auto-Detection Rules

When using `--with-it` or `--with-all-tests`, Claude auto-detects the appropriate integration test type:

| Implementation Type | IT Type Needed | Auto-trigger |
|---------------------|----------------|--------------|
| API Controller/Route | `api` | Yes |
| Repository/DAO | `database` | Yes |
| External Service Client | `service` | Yes |
| MCP Integration | `mcp` | Yes |
| Multi-component Feature | `flow` | Yes |

**Detection Logic:**
```yaml
it_auto_detection:
  api:
    triggers:
      - "*.controller.ts"
      - "*.router.ts"
      - "*.route.ts"
      - "*.handler.ts"
    test_command: "/f5-test-it api"

  database:
    triggers:
      - "*.repository.ts"
      - "*.dao.ts"
      - "*.entity.ts"
    test_command: "/f5-test-it database"

  service:
    triggers:
      - "*-client.ts"
      - "*-adapter.ts"
      - "integrations/*.ts"
    test_command: "/f5-test-it service"

  mcp:
    triggers:
      - "mcp/*.ts"
      - "*-mcp.ts"
    test_command: "/f5-test-it mcp"

  flow:
    triggers:
      - Multiple components detected
      - Cross-module dependencies
    test_command: "/f5-test-it flow"
```

---

## WORKFLOW OVERVIEW

```
┌─────────────────────────────────────────────────────────────────────┐
│                    IMPLEMENTATION WORKFLOW                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. PREFLIGHT          2. CONTEXT          3. IMPLEMENT              │
│  ───────────           ───────             ─────────                 │
│  • Check SIP           • Load stack        • Apply patterns          │
│  • Check gate D4       • Load skills       • Generate code           │
│  • Check design docs   • Load templates    • Add error handling      │
│                        • Load examples     • Add validation          │
│         ↓                    ↓                    ↓                   │
│  4. TEST               5. REVIEW           6. COMMIT                 │
│  ────                  ──────              ──────                    │
│  • Generate tests      • Self-review       • Add traceability        │
│  • Run tests           • Quality check     • Update progress         │
│  • Check coverage      • Security check    • Push to branch          │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## TDD WORKFLOW (--tdd flag)

When using `--tdd` flag, follow Red-Green-Refactor cycle.

> **💡 For comprehensive TDD session management, use `/f5-tdd`**
> The `/f5-tdd` command provides full TDD session tracking, metrics, and reporting.
> See: `/f5-tdd help` for all options.

**Quick Start:**
```bash
# Full TDD session with tracking
/f5-tdd start user-registration --for REQ-001

# Or simple TDD with --tdd flag
/f5-implement user-registration --tdd
```

```
TDD CYCLE
═══════════════════════════════════════════════════════════════════════

  🔴 RED PHASE
  └── Write failing tests first
  └── Define expected behavior
  └── Run tests → MUST FAIL
         ↓
  🟢 GREEN PHASE
  └── Write minimal code to pass
  └── No optimization yet
  └── Run tests → MUST PASS
         ↓
  🔵 REFACTOR PHASE
  └── Improve code quality
  └── Apply design patterns
  └── Run tests → STILL PASS
         ↓
  🔄 REPEAT for next requirement

═══════════════════════════════════════════════════════════════════════
```

### TDD Example

```bash
# Start TDD session
/f5-implement user-registration --tdd
```

**Phase 1: RED - Write Failing Tests**
```typescript
// user.service.spec.ts
describe('UserService', () => {
  describe('createUser', () => {
    it('should create user with valid data', async () => {
      const dto = { name: 'John', email: 'john@test.com', password: 'Pass123!' };
      const result = await service.createUser(dto);

      expect(result.id).toBeDefined();
      expect(result.email).toBe(dto.email);
    });

    it('should throw if email already exists', async () => {
      const dto = { name: 'John', email: 'existing@test.com', password: 'Pass123!' };

      await expect(service.createUser(dto))
        .rejects.toThrow(EmailAlreadyExistsException);
    });

    it('should hash password before saving', async () => {
      const dto = { name: 'John', email: 'john@test.com', password: 'Pass123!' };
      await service.createUser(dto);

      expect(repository.create).toHaveBeenCalledWith(
        expect.objectContaining({
          password: expect.not.stringMatching(/Pass123!/),
        })
      );
    });
  });
});
```

```bash
# Run tests - should fail
npm run test -- user.service.spec.ts
# Expected: 3 tests FAILED (no implementation yet)
```

**Phase 2: GREEN - Write Minimal Code**
```typescript
// user.service.ts - Minimal implementation to pass tests
@Injectable()
export class UserService {
  constructor(
    private readonly userRepository: UserRepository,
    private readonly hashService: HashService,
  ) {}

  async createUser(dto: CreateUserDto): Promise<User> {
    const existing = await this.userRepository.findByEmail(dto.email);
    if (existing) {
      throw new EmailAlreadyExistsException(dto.email);
    }

    const hashedPassword = await this.hashService.hash(dto.password);
    return this.userRepository.create({
      ...dto,
      password: hashedPassword,
    });
  }
}
```

```bash
# Run tests - should pass
npm run test -- user.service.spec.ts
# Expected: 3 tests PASSED
```

**Phase 3: REFACTOR - Improve Quality**
```typescript
// user.service.ts - Refactored with logging, error handling
@Injectable()
export class UserService {
  private readonly logger = new Logger(UserService.name);

  constructor(
    private readonly userRepository: UserRepository,
    private readonly hashService: HashService,
  ) {}

  async createUser(dto: CreateUserDto): Promise<User> {
    this.logger.log(`Creating user: ${dto.email}`);

    await this.validateEmailUnique(dto.email);
    const hashedPassword = await this.hashPassword(dto.password);

    try {
      const user = await this.userRepository.create({
        ...dto,
        password: hashedPassword,
      });
      this.logger.log(`User created: ${user.id}`);
      return user;
    } catch (error) {
      this.logger.error(`Failed to create user: ${error.message}`, error.stack);
      throw new HttpException('Failed to create user', HttpStatus.INTERNAL_SERVER_ERROR);
    }
  }

  private async validateEmailUnique(email: string): Promise<void> {
    const existing = await this.userRepository.findByEmail(email);
    if (existing) {
      throw new EmailAlreadyExistsException(email);
    }
  }

  private async hashPassword(password: string): Promise<string> {
    return this.hashService.hash(password);
  }
}
```

```bash
# Run tests - should still pass
npm run test -- user.service.spec.ts
# Expected: 3 tests PASSED
```

---

## STEP 1: PREFLIGHT CHECKS (MANDATORY)

### 1.1 Check SIP Status

```bash
# Check strict implementation session
f5 strict check --json
```

**If NO_SESSION or NOT_APPROVED:**
```
⛔ Cannot implement without approved requirements.

Run:
/f5-strict start <requirements.md>
/f5-strict approve
```

### 1.2 Check Gate D4 Passed

```bash
# Verify D4 (Detail Design) is complete
f5 gate check D4
```

**If D4 NOT passed:**
```
⛔ Cannot implement without Detail Design approval.

Complete D4 first:
/f5-design generate screen-detail <module>
/f5-design generate api-detail <module>
/f5-gate complete D4
```

### 1.3 Check Design Documents Exist

```bash
# Verify design docs exist
ls .f5/specs/detail-design/
```

Required files:
- [ ] API specifications
- [ ] Screen specifications
- [ ] Database schema
- [ ] Test cases identified

---

## STEP 2: LOAD CONTEXT

### 2.1 Detect Stack

```bash
BACKEND=$(jq -r '.stack.backend // "unknown"' .f5/config.json)
FRONTEND=$(jq -r '.stack.frontend // "unknown"' .f5/config.json)
MOBILE=$(jq -r '.stack.mobile // "unknown"' .f5/config.json)
DATABASE=$(jq -r '.stack.database // "unknown"' .f5/config.json)
```

### 2.2 Load Stack Skills

Based on detected stack, load relevant skills from `stacks/`:

| Stack | Skills Path | Key Skills |
|-------|-------------|------------|
| `nestjs` | `stacks/backend/nestjs/skills/` | architecture, database, security, testing, validation, error-handling |
| `spring` | `stacks/backend/spring/skills/` | architecture, database, security, testing, validation |
| `fastapi` | `stacks/backend/fastapi/skills/` | architecture, database, security, testing, validation |
| `go` | `stacks/backend/go/skills/` | architecture, database, security, testing, validation |
| `django` | `stacks/backend/django/skills/` | architecture, database, security, testing, validation |
| `react` | `stacks/frontend/react/skills/` | architecture, components, state, testing, hooks |
| `nextjs` | `stacks/frontend/nextjs/skills/` | architecture, data-fetching, routing, testing, server-components |
| `vue` | `stacks/frontend/vue/skills/` | architecture, components, state, testing, composables |
| `angular` | `stacks/frontend/angular/skills/` | architecture, components, state, testing, services |
| `flutter` | `stacks/mobile/flutter/skills/` | architecture, state-management, testing, widgets |
| `react-native` | `stacks/mobile/react-native/skills/` | architecture, navigation, state, testing |

**Output:**
```markdown
## 📚 Loaded Context

**Stack:** {{BACKEND}} + {{FRONTEND}} + {{DATABASE}}

**Skills Loaded:**
- `stacks/backend/{{BACKEND}}/skills/architecture/`
- `stacks/backend/{{BACKEND}}/skills/database/`
- `stacks/backend/{{BACKEND}}/skills/testing/`
- `stacks/backend/{{BACKEND}}/skills/security/`
- `stacks/backend/{{BACKEND}}/skills/validation/`
- `stacks/backend/{{BACKEND}}/skills/error-handling/`

**Templates Available:**
- `stacks/backend/{{BACKEND}}/templates/`

**Examples Available:**
- `stacks/backend/{{BACKEND}}/examples/`
```

### 2.3 Load Design Specifications

```bash
# Load relevant design docs
DESIGN_PATH=".f5/specs/detail-design/"
```

Read:
- API spec for the feature
- Screen spec for the feature
- Database schema changes
- Test cases

---

## STEP 3: IMPLEMENT WITH QUALITY

### 3.1 Apply Architecture Patterns

Based on stack, apply correct patterns:

**NestJS:**
```typescript
// REQ-XXX: Feature description
// Pattern: Clean Architecture with NestJS modules

// 1. Module structure
src/modules/{feature}/
├── {feature}.module.ts       // Module definition
├── {feature}.controller.ts   // HTTP layer
├── {feature}.service.ts      // Business logic
├── {feature}.repository.ts   // Data access
├── dto/                      // Request/Response DTOs
│   ├── create-{feature}.dto.ts
│   ├── update-{feature}.dto.ts
│   └── {feature}-response.dto.ts
├── entities/                 // Database entities
│   └── {feature}.entity.ts
├── exceptions/               // Custom exceptions
│   └── {feature}-not-found.exception.ts
└── __tests__/               // Tests
    ├── {feature}.service.spec.ts
    └── {feature}.controller.spec.ts
```

**Spring Boot:**
```java
// REQ-XXX: Feature description
// Pattern: Layered Architecture

src/main/java/com/app/{feature}/
├── controller/
│   └── {Feature}Controller.java
├── service/
│   ├── {Feature}Service.java
│   └── impl/{Feature}ServiceImpl.java
├── repository/
│   └── {Feature}Repository.java
├── dto/
│   ├── Create{Feature}Request.java
│   ├── Update{Feature}Request.java
│   └── {Feature}Response.java
├── entity/
│   └── {Feature}.java
├── exception/
│   └── {Feature}NotFoundException.java
└── mapper/
    └── {Feature}Mapper.java
```

**FastAPI:**
```python
# REQ-XXX: Feature description
# Pattern: Clean Architecture

src/{feature}/
├── __init__.py
├── router.py              # API endpoints
├── service.py             # Business logic
├── repository.py          # Data access
├── schemas.py             # Pydantic models
├── models.py              # SQLAlchemy models
├── exceptions.py          # Custom exceptions
└── tests/
    ├── test_router.py
    └── test_service.py
```

**Go:**
```go
// REQ-XXX: Feature description
// Pattern: Clean Architecture

internal/{feature}/
├── handler.go             // HTTP handlers
├── service.go             // Business logic
├── repository.go          // Data access
├── dto.go                 // Request/Response types
├── entity.go              // Domain entities
├── errors.go              // Custom errors
└── {feature}_test.go      // Tests
```

### 3.2 Apply Validation (REQUIRED)

**ALWAYS validate input:**

```typescript
// NestJS example
import { IsString, IsNotEmpty, MinLength, MaxLength, IsEmail, Matches, IsOptional, IsEnum } from 'class-validator';
import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';

export class CreateUserDto {
  @ApiProperty({ description: 'User full name', example: 'John Doe' })
  @IsString()
  @IsNotEmpty()
  @MinLength(2)
  @MaxLength(50)
  name: string;

  @ApiProperty({ description: 'User email address', example: 'john@example.com' })
  @IsEmail()
  email: string;

  @ApiProperty({ description: 'User password (min 8 chars, must include uppercase, lowercase, number)' })
  @IsString()
  @MinLength(8)
  @Matches(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/, {
    message: 'Password must contain uppercase, lowercase, and number',
  })
  password: string;

  @ApiPropertyOptional({ description: 'User role', enum: ['user', 'admin'], default: 'user' })
  @IsOptional()
  @IsEnum(['user', 'admin'])
  role?: string;
}
```

```python
# FastAPI example
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from enum import Enum

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"

class CreateUserRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=50, description="User full name")
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    role: Optional[UserRole] = Field(default=UserRole.USER, description="User role")

    @validator('password')
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain lowercase')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain digit')
        return v

    class Config:
        schema_extra = {
            "example": {
                "name": "John Doe",
                "email": "john@example.com",
                "password": "SecurePass123",
                "role": "user"
            }
        }
```

### 3.3 Apply Error Handling (REQUIRED)

**ALWAYS handle errors properly:**

```typescript
// NestJS example
import { HttpException, HttpStatus, Logger } from '@nestjs/common';

// Custom exceptions
export class UserNotFoundException extends HttpException {
  constructor(userId: string) {
    super(`User with ID ${userId} not found`, HttpStatus.NOT_FOUND);
  }
}

export class EmailAlreadyExistsException extends HttpException {
  constructor(email: string) {
    super(`Email ${email} is already registered`, HttpStatus.CONFLICT);
  }
}

export class InvalidCredentialsException extends HttpException {
  constructor() {
    super('Invalid credentials', HttpStatus.UNAUTHORIZED);
  }
}

// Service usage
@Injectable()
export class UserService {
  private readonly logger = new Logger(UserService.name);

  async createUser(dto: CreateUserDto): Promise<User> {
    this.logger.log(`Creating user: ${dto.email}`);

    const existingUser = await this.userRepository.findByEmail(dto.email);
    if (existingUser) {
      throw new EmailAlreadyExistsException(dto.email);
    }

    try {
      const hashedPassword = await bcrypt.hash(dto.password, 12);
      const user = await this.userRepository.create({
        ...dto,
        password: hashedPassword,
      });
      this.logger.log(`User created successfully: ${user.id}`);
      return user;
    } catch (error) {
      this.logger.error(`Failed to create user: ${error.message}`, error.stack);
      throw new HttpException('Failed to create user', HttpStatus.INTERNAL_SERVER_ERROR);
    }
  }

  async findById(id: string): Promise<User> {
    const user = await this.userRepository.findById(id);
    if (!user) {
      throw new UserNotFoundException(id);
    }
    return user;
  }
}
```

### 3.4 Apply Security Patterns (REQUIRED)

**ALWAYS consider security:**

```typescript
// Authentication guard
@UseGuards(JwtAuthGuard)
@Controller('users')
export class UserController {}

// Role-based access
@Roles('admin')
@UseGuards(RolesGuard)
@Delete(':id')
async deleteUser(@Param('id') id: string) {}

// Input sanitization
import * as sanitizeHtml from 'sanitize-html';
const cleanInput = sanitizeHtml(userInput, {
  allowedTags: [],
  allowedAttributes: {},
});

// SQL injection prevention (use parameterized queries)
const user = await this.userRepository
  .createQueryBuilder('user')
  .where('user.email = :email', { email })
  .getOne();

// Rate limiting
@UseGuards(ThrottlerGuard)
@Throttle(10, 60) // 10 requests per 60 seconds
@Post('login')
async login(@Body() dto: LoginDto) {}

// CORS configuration
app.enableCors({
  origin: process.env.ALLOWED_ORIGINS?.split(',') || [],
  credentials: true,
});

// Helmet for security headers
import helmet from 'helmet';
app.use(helmet());
```

### 3.5 Apply Logging (REQUIRED)

**ALWAYS add proper logging:**

```typescript
import { Logger } from '@nestjs/common';

@Injectable()
export class UserService {
  private readonly logger = new Logger(UserService.name);

  async createUser(dto: CreateUserDto): Promise<User> {
    this.logger.log(`Creating user with email: ${dto.email}`);

    try {
      const user = await this.userRepository.create(dto);
      this.logger.log(`User created successfully: ${user.id}`);
      return user;
    } catch (error) {
      this.logger.error(`Failed to create user: ${error.message}`, error.stack);
      throw error;
    }
  }

  async deleteUser(id: string, performedBy: string): Promise<void> {
    this.logger.warn(`User deletion requested: ${id} by ${performedBy}`);

    // Audit log for sensitive operations
    await this.auditService.log({
      action: 'USER_DELETE',
      targetId: id,
      performedBy,
      timestamp: new Date(),
      ip: this.request.ip,
    });

    await this.userRepository.delete(id);
    this.logger.log(`User deleted: ${id}`);
  }
}
```

---

## STEP 4: GENERATE TESTS

### 4.1 Unit Tests (Required)

**Coverage target: ≥80%**

```typescript
// {feature}.service.spec.ts
import { Test, TestingModule } from '@nestjs/testing';
import { UserService } from './user.service';
import { UserRepository } from './user.repository';
import { EmailAlreadyExistsException, UserNotFoundException } from './exceptions';

describe('UserService', () => {
  let service: UserService;
  let repository: jest.Mocked<UserRepository>;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        UserService,
        {
          provide: UserRepository,
          useValue: {
            findByEmail: jest.fn(),
            findById: jest.fn(),
            create: jest.fn(),
            update: jest.fn(),
            delete: jest.fn(),
          },
        },
      ],
    }).compile();

    service = module.get(UserService);
    repository = module.get(UserRepository);
  });

  describe('createUser', () => {
    const dto = { name: 'John', email: 'john@example.com', password: 'Pass123!' };

    it('should create user successfully', async () => {
      // Arrange
      const expected = { id: '1', ...dto, password: 'hashed' };
      repository.findByEmail.mockResolvedValue(null);
      repository.create.mockResolvedValue(expected);

      // Act
      const result = await service.createUser(dto);

      // Assert
      expect(result).toEqual(expected);
      expect(repository.create).toHaveBeenCalled();
    });

    it('should throw EmailAlreadyExistsException if email exists', async () => {
      // Arrange
      repository.findByEmail.mockResolvedValue({ id: '1', email: dto.email });

      // Act & Assert
      await expect(service.createUser(dto)).rejects.toThrow(EmailAlreadyExistsException);
    });

    it('should handle repository errors', async () => {
      // Arrange
      repository.findByEmail.mockResolvedValue(null);
      repository.create.mockRejectedValue(new Error('Database error'));

      // Act & Assert
      await expect(service.createUser(dto)).rejects.toThrow(HttpException);
    });
  });

  describe('findById', () => {
    it('should return user if found', async () => {
      // Arrange
      const expected = { id: '1', name: 'John', email: 'john@example.com' };
      repository.findById.mockResolvedValue(expected);

      // Act
      const result = await service.findById('1');

      // Assert
      expect(result).toEqual(expected);
    });

    it('should throw UserNotFoundException if not found', async () => {
      // Arrange
      repository.findById.mockResolvedValue(null);

      // Act & Assert
      await expect(service.findById('1')).rejects.toThrow(UserNotFoundException);
    });
  });
});
```

### 4.2 Integration Tests (--with-it flag)

When `--with-it` or `--with-all-tests` is used, auto-generate appropriate IT:

```yaml
# Auto-detection and generation
it_generation:
  detect_type:
    - Check file patterns (controller, repository, client)
    - Analyze dependencies
    - Determine IT type needed

  generate:
    api: "/f5-test-it api [endpoint]"
    database: "/f5-test-it database [table]"
    service: "/f5-test-it service [service-name]"
    flow: "/f5-test-it flow [flow-name]"
```

**Example Output (API Controller detected):**
```markdown
## 🔗 Integration Tests Auto-Generated

**Detected:** user.controller.ts → API Integration Test
**Command:** /f5-test-it api /users

### Test Cases Generated:
| Method | Endpoint | Scenario |
|--------|----------|----------|
| POST | /users | Create user success |
| POST | /users | Validation error |
| GET | /users/:id | User found |
| GET | /users/:id | User not found (404) |
```

### 4.3 E2E Integration Tests

```typescript
// {feature}.e2e-spec.ts
import { Test, TestingModule } from '@nestjs/testing';
import { INestApplication, ValidationPipe } from '@nestjs/common';
import * as request from 'supertest';
import { AppModule } from '../app.module';

describe('UserController (e2e)', () => {
  let app: INestApplication;

  beforeAll(async () => {
    const moduleFixture: TestingModule = await Test.createTestingModule({
      imports: [AppModule],
    }).compile();

    app = moduleFixture.createNestApplication();
    app.useGlobalPipes(new ValidationPipe({ whitelist: true, transform: true }));
    await app.init();
  });

  afterAll(async () => {
    await app.close();
  });

  describe('POST /users', () => {
    it('should create user with valid data', () => {
      return request(app.getHttpServer())
        .post('/users')
        .send({ name: 'John', email: 'john@test.com', password: 'Pass123!' })
        .expect(201)
        .expect((res) => {
          expect(res.body.id).toBeDefined();
          expect(res.body.email).toBe('john@test.com');
          expect(res.body.password).toBeUndefined(); // Should not expose password
        });
    });

    it('should return 400 for invalid input', () => {
      return request(app.getHttpServer())
        .post('/users')
        .send({ name: '', email: 'invalid' })
        .expect(400)
        .expect((res) => {
          expect(res.body.message).toContain('email must be an email');
        });
    });

    it('should return 409 for duplicate email', async () => {
      // First create
      await request(app.getHttpServer())
        .post('/users')
        .send({ name: 'John', email: 'duplicate@test.com', password: 'Pass123!' });

      // Second create with same email
      return request(app.getHttpServer())
        .post('/users')
        .send({ name: 'Jane', email: 'duplicate@test.com', password: 'Pass123!' })
        .expect(409);
    });
  });

  describe('GET /users/:id', () => {
    it('should return user if exists', async () => {
      const createRes = await request(app.getHttpServer())
        .post('/users')
        .send({ name: 'John', email: 'gettest@test.com', password: 'Pass123!' });

      return request(app.getHttpServer())
        .get(`/users/${createRes.body.id}`)
        .expect(200)
        .expect((res) => {
          expect(res.body.email).toBe('gettest@test.com');
        });
    });

    it('should return 404 if not found', () => {
      return request(app.getHttpServer())
        .get('/users/non-existent-id')
        .expect(404);
    });
  });
});
```

### 4.4 Run Tests & Check Coverage

```bash
# Run unit tests
npm run test

# Run e2e tests
npm run test:e2e

# Check coverage
npm run test:cov

# Coverage requirements
# - Statements: ≥80%
# - Branches: ≥75%
# - Functions: ≥80%
# - Lines: ≥80%
```

### 4.5 Integration with /f5-test

```bash
# Generate tests automatically
/f5-test generate src/modules/user/

# Run tests with coverage
/f5-test run --type unit --coverage

# TDD mode
/f5-test tdd start user-registration
/f5-test tdd red    # Write failing tests
/f5-test tdd green  # Write passing code
/f5-test tdd refactor # Improve code
```

---

## STEP 5: SELF-REVIEW

### 5.1 Quality Checklist

Before committing, verify:

**Code Quality:**
- [ ] Follows stack architecture patterns
- [ ] No hardcoded values (use config/env)
- [ ] No console.log (use proper logger)
- [ ] No commented-out code
- [ ] Proper naming conventions
- [ ] DRY - no code duplication
- [ ] Functions < 20 lines
- [ ] Cyclomatic complexity < 10

**Error Handling:**
- [ ] All errors are caught and handled
- [ ] Proper error messages returned
- [ ] Errors are logged with stack trace
- [ ] No sensitive data in error messages
- [ ] Custom exceptions for domain errors

**Validation:**
- [ ] All inputs are validated
- [ ] Proper validation messages
- [ ] Edge cases handled
- [ ] SQL injection prevented
- [ ] XSS prevented

**Security:**
- [ ] No SQL injection vulnerabilities
- [ ] No XSS vulnerabilities
- [ ] Authentication/Authorization applied
- [ ] Sensitive data encrypted
- [ ] No secrets in code
- [ ] Rate limiting applied (if applicable)

**Testing:**
- [ ] Unit tests written (≥80% coverage)
- [ ] Integration tests for APIs
- [ ] Edge cases tested
- [ ] Error scenarios tested
- [ ] Mocking done properly

**Documentation:**
- [ ] Traceability comments added (REQ-XXX)
- [ ] API documented (Swagger/OpenAPI)
- [ ] Complex logic commented

### 5.2 Run Quality Checks

```bash
# Lint
npm run lint

# Type check
npm run type-check

# Security scan
npm audit

# Test with coverage
npm run test:cov

# Or use /f5-review
/f5-review check src/modules/user/
```

### 5.3 Integration with /f5-review

```bash
# Quick check before commit
/f5-review check src/modules/user/

# Full review with security
/f5-review full src/modules/user/

# Security-focused review
/f5-review security src/modules/user/
```

---

## STEP 6: COMMIT & PROGRESS

### 6.1 Add Traceability

```typescript
// At the top of each file implementing a requirement
// REQ-001: User registration with email verification
// REQ-002: Password strength validation

@Injectable()
export class UserService {
  // Implementation...
}
```

### 6.2 Update SIP Progress

```bash
# Mark requirement as done
/f5-strict mark REQ-001 done src/modules/user/user.service.ts:10-80

# Validate implementation
/f5-strict validate
```

### 6.3 Commit with Convention

```bash
git add .
git commit -m "feat(user): implement user registration

- Add CreateUserDto with validation
- Implement UserService.createUser()
- Add error handling for duplicate email
- Add unit tests (85% coverage)
- Add e2e tests for POST /users

Implements: REQ-001, REQ-002
"
```

---

## OUTPUT FORMAT

When implementing, structure response as:

```markdown
## 📋 Implementation: REQ-XXX - {{Description}}

### Preflight ✓
- [x] SIP Session: Active
- [x] Gate D4: Passed
- [x] Design docs: Found

### Context Loaded
- **Stack:** NestJS + PostgreSQL
- **Skills:** architecture, database, testing, validation, security, error-handling
- **Domain:** {{domain}} (if applicable)

### Implementation

#### 1. Entity
```typescript
// REQ-XXX: Entity for feature
// Code here
```

#### 2. DTO with Validation
```typescript
// REQ-XXX: Input validation
// Code here
```

#### 3. Service with Error Handling
```typescript
// REQ-XXX: Business logic
// Code here
```

#### 4. Controller with Guards
```typescript
// REQ-XXX: HTTP layer
// Code here
```

#### 5. Custom Exceptions
```typescript
// REQ-XXX: Domain exceptions
// Code here
```

### Tests Generated

#### Unit Tests
```typescript
// Test code here
```

#### Integration Tests
```typescript
// Test code here
```

### Quality Checklist
- [x] Architecture patterns applied
- [x] Validation implemented
- [x] Error handling complete
- [x] Security guards added
- [x] Logging implemented
- [x] Tests written (85% coverage)
- [x] Traceability comments added

### Next Steps
```bash
# Mark requirement done
/f5-strict mark REQ-XXX done src/modules/user/user.service.ts:10-80

# Validate implementation
/f5-strict validate

# Run tests
/f5-test run --type unit

# Review code
/f5-review check src/modules/user/

# Commit changes
git add . && git commit -m "feat(user): implement feature - REQ-XXX"
```
```

---

## SUBCOMMANDS

| Command | Description |
|---------|-------------|
| `/f5-implement <module>` | Implement a module |
| `/f5-implement feature <name>` | Implement a feature |
| `/f5-implement api <endpoint>` | Implement an API endpoint |
| `/f5-implement screen <name>` | Implement a screen |
| `/f5-implement --check` | Run quality checks only |
| `/f5-implement --scaffold <module>` | Generate module structure only |
| `/f5-implement --tdd <feature>` | TDD workflow |
| `/f5-implement --with-tests <feature>` | Generate with tests |
| `/f5-implement --security <feature>` | Security-focused |
| `/f5-implement --performance <feature>` | Performance-focused |

---

## STACK-SPECIFIC COMMANDS

Based on detected stacks, use appropriate commands:

| Stack | Command | Description |
|-------|---------|-------------|
| `nestjs` | `/f5-implement module <name>` | NestJS module implementation |
| `spring` | `/f5-implement module <name>` | Spring Boot module implementation |
| `fastapi` | `/f5-implement module <name>` | FastAPI router implementation |
| `go` | `/f5-implement module <name>` | Go handler implementation |
| `django` | `/f5-implement module <name>` | Django app implementation |
| `nextjs` | `/f5-implement feature <name>` | NextJS feature implementation |
| `react` | `/f5-implement feature <name>` | React feature implementation |
| `vue` | `/f5-implement feature <name>` | Vue feature implementation |
| `angular` | `/f5-implement feature <name>` | Angular feature implementation |
| `flutter` | `/f5-implement feature <name>` | Flutter feature implementation |
| `react-native` | `/f5-implement feature <name>` | React Native feature implementation |

---

## INTEGRATION WITH OTHER COMMANDS

### With /f5-test
```bash
# Generate tests for implementation
/f5-test generate src/modules/user/

# Run TDD workflow
/f5-test tdd start user-registration

# Check coverage after implementation
/f5-test coverage
```

### With /f5-review
```bash
# Quick quality check
/f5-review check src/modules/user/

# Full review before commit
/f5-review full src/modules/user/

# Security review for sensitive features
/f5-review security src/modules/user/
```

### With /f5-gate
```bash
# Check G2 gate before starting
/f5-gate check G2

# Complete G2 after implementation
/f5-gate complete G2
```

---

## IMPORTANT RULES

1. **NEVER implement without checking SIP status first**
2. **NEVER implement features not in the checklist**
3. **NEVER skip validation or error handling**
4. **ALWAYS apply stack-specific patterns**
5. **ALWAYS add traceability comments (REQ-XXX)**
6. **ALWAYS write tests (≥80% coverage)**
7. **ALWAYS run quality checks before commit**
8. **ALWAYS mark progress after each requirement**
9. **ALWAYS use proper logging (no console.log)**
10. **ALWAYS consider security implications**

---

## SEE ALSO

- `/f5-test` - Master test command
- `/f5-test-unit` - Unit testing
- `/f5-test-it` - Integration testing
- `/f5-test-e2e` - E2E testing
- `/f5-tdd` - TDD workflow
- `/f5-gate` - Quality gates (G2, G3)
- `/f5-review` - Code review
- `/f5-strict` - SIP workflow

---

*F5 Framework - Implementation Command*
