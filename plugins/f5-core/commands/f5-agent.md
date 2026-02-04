---
description: Manage AI agents, personas, and get smart suggestions
argument-hint: <list|invoke|persona|suggest> [options]
---

# /f5-agent - Unified AI Agent Command

**Consolidated command** that replaces:
- `/f5-persona` → `/f5-agent persona`
- `/f5-suggest` → `/f5-agent suggest`

## ARGUMENTS
$ARGUMENTS

## MODE DETECTION

| Pattern | Mode | Description |
|---------|------|-------------|
| `persona <action>` | PERSONA | Persona management |
| `suggest [topic]` | SUGGEST | Smart suggestions |
| `<other>` (default) | AGENT | Agent invocation |

---

## MODE: PERSONA (from /f5-persona)

### `/f5-agent persona <action>`

Manage and activate specialized personas.

| Action | Description |
|--------|-------------|
| `list` | List all available personas |
| `show <name>` | Show persona details |
| `activate <name>` | Activate a persona |
| `deactivate` | Return to default |
| `auto [on\|off]` | Toggle auto-activation |
| `chain <task>` | Chain personas for task |
| `status` | Show current status |

**Available Personas:**
| Persona | Emoji | Focus |
|---------|-------|-------|
| architect | 🏗️ | System design |
| backend | ⚙️ | APIs, services |
| frontend | 🎨 | UI/UX, components |
| database | 🗄️ | Schema, queries |
| security | 🔒 | OWASP, auth |
| qa | 🧪 | Testing, coverage |
| performance | ⚡ | Optimization |
| reviewer | 👀 | Code review |
| devops | 🚀 | CI/CD, infra |
| analyst | 📊 | Requirements |
| developer | 💻 | General dev (default) |

**Examples:**
```bash
/f5-agent persona list
/f5-agent persona activate security
/f5-agent persona chain "build auth system"
```

---

## MODE: SUGGEST (from /f5-suggest)

### `/f5-agent suggest [topic]`

Get context-aware command suggestions.

| Action | Description |
|--------|-------------|
| (default) | Suggestions for current phase |
| `<topic>` | Suggestions for specific topic |
| `next` | Suggest next action |
| `chains` | Show command chains |

**Options:**
- `--all` - Show all command levels
- `--v{1-5}` - Verbosity level

**Examples:**
```bash
/f5-agent suggest
/f5-agent suggest api
/f5-agent suggest next
/f5-agent suggest chains
```

---

## MODE: AGENT (Default)

Invoke specialized agents for specific tasks.

## OVERVIEW

```
SPECIALIZED AGENTS
═══════════════════════════════════════════════════════════════════

  Agents are task-specific AI assistants:

  ⚡ code_generator     │ 🧪 test_writer      │ 👀 code_reviewer
  🔧 refactorer         │ 📝 documenter       │ 🐛 debugger
  🔄 migrator           │ 🛡️ security_scanner │ 📊 performance_analyzer
  🌐 api_designer       │ 🏗️ system_architect

═══════════════════════════════════════════════════════════════════
```

## SUBCOMMANDS

| Command | Description |
|---------|-------------|
| `list` | List all agents |
| `invoke <agent> [input]` | Invoke an agent |
| `pipeline <name>` | Run agent pipeline |
| `status` | Show active agents |
| `help <agent>` | Show agent details |

---

## QUICK INVOCATION

Instead of using the full command, you can invoke agents directly using the `@f5:` pattern:

### Direct Pattern
```
@f5:security "review authentication flow"
@f5:architect "design payment system"
@f5:qa "generate tests for PaymentService"
@f5:debug "fix TypeError in OrderController"
```

### Multi-Agent
```
@f5:security @f5:architect "review and redesign auth system"
```

### With Options
```
@f5:qa --coverage 90 "test all services"
@f5:security --deep "full security audit"
```

### Available Aliases

| Short | Full | Agent |
|-------|------|-------|
| @f5:sec | @f5:security | security_scanner |
| @f5:arch | @f5:architect | system_architect |
| @f5:be | @f5:backend | code_generator |
| @f5:fe | @f5:frontend | code_generator |
| @f5:qa | @f5:test | test_writer |
| @f5:bug | @f5:debug | debugger |
| @f5:doc | @f5:docs | documenter |
| @f5:perf | @f5:performance | performance_analyzer |
| @f5:ref | @f5:refactor | refactorer |
| @f5:api | - | api_designer |

### Supported Options

| Option | Description |
|--------|-------------|
| `--deep` | Thorough analysis |
| `--quick` | Fast check |
| `--coverage <n>` | Target coverage percentage |
| `--fix` | Auto-fix issues if possible |
| `--verbose` | Detailed output |

---

## ACTION: LIST_AGENTS

### `/f5-agent list`

```markdown
## 🤖 Available Agents

### Code Agents
| Agent | Emoji | Purpose |
|-------|-------|---------|
| code_generator | ⚡ | Generate production code |
| refactorer | 🔧 | Improve code quality |
| migrator | 🔄 | Handle migrations |

### Quality Agents
| Agent | Emoji | Purpose |
|-------|-------|---------|
| test_writer | 🧪 | Generate test suites |
| code_reviewer | 👀 | Review code quality |
| security_scanner | 🛡️ | Find vulnerabilities |
| performance_analyzer | 📊 | Analyze performance |

### Support Agents
| Agent | Emoji | Purpose |
|-------|-------|---------|
| debugger | 🐛 | Diagnose and fix bugs |
| documenter | 📝 | Generate documentation |
| api_designer | 🌐 | Design APIs |

### Quick Invoke
```bash
/f5-agent invoke code_generator "user registration service"
```
```

---

## ACTION: INVOKE_AGENT

### `/f5-agent invoke <agent> [input]`

Invoke a specific agent with input:

```markdown
## ⚡ Agent Invoked: code_generator

### Input
> "user registration service"

### Agent Processing

```
1. Analyzing requirements...
2. Loading project patterns...
3. Generating code...
```

### Output

```typescript
// src/user/user-registration.service.ts
import { Injectable, ConflictException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { User } from './entities/user.entity';
import { RegisterDto } from './dto/register.dto';
import * as bcrypt from 'bcrypt';

@Injectable()
export class UserRegistrationService {
  constructor(
    @InjectRepository(User)
    private readonly userRepo: Repository<User>,
  ) {}

  async register(dto: RegisterDto): Promise<User> {
    // Check duplicate
    const existing = await this.userRepo.findOne({
      where: { email: dto.email }
    });
    if (existing) {
      throw new ConflictException('Email already registered');
    }

    // Hash password
    const passwordHash = await bcrypt.hash(dto.password, 10);

    // Create user
    const user = this.userRepo.create({
      ...dto,
      password: passwordHash,
    });

    return this.userRepo.save(user);
  }
}
```

### Agent Notes
- Included duplicate email check
- Password hashing with bcrypt
- Follows NestJS patterns
- Includes proper error handling

### Follow-up Actions
```bash
/f5-agent invoke test_writer "for UserRegistrationService"
/f5-agent invoke documenter "for UserRegistrationService"
```
```

---

## ACTION: RUN_PIPELINE

### `/f5-agent pipeline <name>`

Run a predefined agent pipeline:

```markdown
## 🔗 Running Pipeline: feature_development

### Pipeline Steps

| Step | Agent | Status |
|------|-------|--------|
| 1 | 🌐 api_designer | ⏳ Running |
| 2 | ⚡ code_generator | ⏸️ Waiting |
| 3 | 🧪 test_writer | ⏸️ Waiting |
| 4 | 👀 code_reviewer | ⏸️ Waiting |
| 5 | 📝 documenter | ⏸️ Waiting |

### Step 1: API Designer

Designing API endpoints...

```yaml
# Generated API Design
paths:
  /users/register:
    post:
      summary: Register new user
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/RegisterDto'
      responses:
        201:
          description: User created
        409:
          description: Email already exists
```

✅ Step 1 Complete

### Step 2: Code Generator

Generating implementation...

[continues for each step]
```

---

## AVAILABLE PIPELINES

### `/f5-agent pipeline list`

| Pipeline | Description | Agents |
|----------|-------------|--------|
| `feature_development` | Full feature development | api_designer → code_generator → test_writer → code_reviewer → documenter |
| `bug_fix` | Bug fixing | debugger → code_generator → test_writer → code_reviewer |
| `code_quality` | Code quality improvement | code_reviewer → refactorer → security_scanner → performance_analyzer |
| `security_audit` | Security audit | security_scanner → code_reviewer → code_generator → test_writer |
| `api_design` | API design and docs | api_designer → documenter → code_reviewer |
| `refactoring` | Code refactoring | code_reviewer → refactorer → test_writer → documenter |
| `migration` | Migration | migrator → test_writer → code_reviewer → documenter |

---

## ACTION: SHOW_STATUS

### `/f5-agent status`

```markdown
## 📊 Agent Status

### Active Agents
| Agent | Task | Progress |
|-------|------|----------|
| code_generator | Generate payment service | 75% |

### Recent Activity
| Time | Agent | Task | Result |
|------|-------|------|--------|
| 5m ago | 🧪 test_writer | Generate tests for UserService | ✅ Complete |
| 15m ago | ⚡ code_generator | Generate UserService | ✅ Complete |
| 30m ago | 🌐 api_designer | Design User API | ✅ Complete |

### Running Pipelines
| Pipeline | Status | Current Step |
|----------|--------|--------------|
| feature_development | 🔄 Running | 4/5 (code_reviewer) |
```

---

## AGENT DETAILS

### ⚡ code_generator
**Purpose:** Generates production-ready code from specifications

**Capabilities:**
- Generate code from description
- Follow project patterns
- Apply best practices
- Include error handling
- Type-safe implementations

**Usage:**
```bash
/f5-agent invoke code_generator "payment service"
/f5-agent invoke code_generator --spec ./specs/order.yaml
```

---

### 🧪 test_writer
**Purpose:** Generates comprehensive test suites

**Capabilities:**
- Generate unit tests
- Generate integration tests
- Identify edge cases
- Create mocks and fixtures
- Achieve coverage targets (80%)

**Usage:**
```bash
/f5-agent invoke test_writer "for payment.service.ts"
/f5-agent invoke test_writer --coverage 90
```

---

### 👀 code_reviewer
**Purpose:** Reviews code for quality, security, and best practices

**Capabilities:**
- Identify code issues
- Security vulnerability detection
- Performance analysis
- Best practice enforcement
- Constructive feedback

**Usage:**
```bash
/f5-agent invoke code_reviewer src/payment/
/f5-agent invoke code_reviewer --pr 123
```

---

### 🔧 refactorer
**Purpose:** Improves code quality through refactoring

**Capabilities:**
- Identify code smells
- Apply design patterns
- Reduce complexity
- Extract methods/classes
- Improve naming

**Usage:**
```bash
/f5-agent invoke refactorer src/services/
/f5-agent invoke refactorer "OrderService class"
```

---

### 📝 documenter
**Purpose:** Generates and maintains documentation

**Capabilities:**
- Generate API documentation
- Create README files
- Write inline comments
- Generate JSDoc/TSDoc
- Create architecture docs

**Usage:**
```bash
/f5-agent invoke documenter "for UserService"
/f5-agent invoke documenter --type api
```

---

### 🐛 debugger
**Purpose:** Diagnoses and fixes bugs systematically

**Capabilities:**
- Root cause analysis
- Error interpretation
- Fix suggestion
- Regression prevention
- Debug logging

**Methodology:**
1. Reproduce the issue
2. Isolate the problem
3. Identify root cause
4. Implement fix
5. Verify fix
6. Add regression test

**Usage:**
```bash
/f5-agent invoke debugger "TypeError: Cannot read property 'id' of undefined"
/f5-agent invoke debugger --stack-trace ./error.log
```

---

### 🔄 migrator
**Purpose:** Handles code and data migrations

**Capabilities:**
- Version upgrade assistance
- Breaking change handling
- Data migration scripts
- Dependency updates
- API migration

**Usage:**
```bash
/f5-agent invoke migrator "upgrade React 17 to 18"
/f5-agent invoke migrator --from v1 --to v2
```

---

### 🛡️ security_scanner
**Purpose:** Scans for security vulnerabilities

**Capabilities:**
- OWASP Top 10 check
- Dependency vulnerability scan
- Code security analysis
- Secret detection
- Security recommendations

**Checks:**
- SQL Injection
- XSS
- CSRF
- Authentication issues
- Sensitive data exposure
- Dependency vulnerabilities

**Usage:**
```bash
/f5-agent invoke security_scanner src/auth/
/f5-agent invoke security_scanner --full
```

---

### 📊 performance_analyzer
**Purpose:** Analyzes and optimizes performance

**Capabilities:**
- Identify bottlenecks
- Complexity analysis (Big O)
- Query optimization
- Caching recommendations
- Memory analysis

**Analysis Types:**
- Time complexity
- Space complexity
- N+1 queries
- Memory leaks
- Slow queries

**Usage:**
```bash
/f5-agent invoke performance_analyzer src/services/
/f5-agent invoke performance_analyzer --profile ./metrics.json
```

---

### 🌐 api_designer
**Purpose:** Designs RESTful and GraphQL APIs

**Capabilities:**
- RESTful API design
- GraphQL schema design
- OpenAPI specification
- Versioning strategy
- Error handling design

**Principles:**
- Consistent naming
- Proper HTTP methods
- Meaningful status codes
- Pagination support
- Filtering/sorting

**Usage:**
```bash
/f5-agent invoke api_designer "user management endpoints"
/f5-agent invoke api_designer --graphql "order schema"
```

---

### 🏗️ system_architect
**Purpose:** High-level system design, architecture patterns, scalability

**Capabilities:**
- Design system architecture
- Evaluate architectural trade-offs
- Recommend design patterns
- Plan for scalability
- Create architecture diagrams
- Document architecture decisions

**Core Mindset:**
- Primary Question: "How will this scale and evolve?"
- Core Belief: Systems must be designed for change
- Approach: Think in diagrams, patterns, and trade-offs

**Usage:**
```bash
/f5-agent invoke system_architect "design user authentication system"
/f5-agent invoke system_architect "evaluate microservices vs monolith"
@f5:architect "design payment system"
@f5:arch --diagram "payment processing flow"
```

---

## EXAMPLES

```bash
# List agents
/f5-agent list

# Generate code
/f5-agent invoke code_generator "payment service"

# Write tests
/f5-agent invoke test_writer "for payment.service.ts"

# Review code
/f5-agent invoke code_reviewer src/payment/

# Run full pipeline
/f5-agent pipeline feature_development

# Security scan
/f5-agent invoke security_scanner src/auth/

# Debug error
/f5-agent invoke debugger "TypeError: Cannot read property 'id' of undefined"

# Run bug fix pipeline
/f5-agent pipeline bug_fix

# Performance analysis
/f5-agent invoke performance_analyzer --profile ./metrics.json
```

---

## AUTO-SELECTION RULES

Agents can be auto-selected based on task keywords:

| Keywords | Agent |
|----------|-------|
| generate, implement, create, write code | code_generator |
| test, unit test, integration test | test_writer |
| review, check code, pr review | code_reviewer |
| refactor, improve, clean up | refactorer |
| document, readme, api docs | documenter |
| debug, fix bug, error, troubleshoot | debugger |
| migrate, upgrade, update version | migrator |
| security, vulnerability, audit | security_scanner |
| performance, optimize, slow | performance_analyzer |
| api, endpoint, rest, graphql | api_designer |
| architecture, system design, scalability, trade-off | system_architect |

---

## AGENTS VS PERSONAS

| Aspect | Agents | Personas |
|--------|--------|----------|
| Focus | Task-specific | Role-based |
| Question | "What do I do?" | "Who am I?" |
| Scope | Single task | Entire session |
| Output | Specific artifact | General guidance |
| Example | test_writer | qa engineer |

Use agents for specific tasks, personas for overall mindset.

---

## GATE-AGENT RECOMMENDATIONS

| Gate | Recommended Agents |
|------|-------------------|
| D2-D4 | api_designer, documenter |
| G2 | code_generator, test_writer, code_reviewer |
| G3 | test_writer, security_scanner, performance_analyzer |
| G4 | security_scanner, documenter |

---

## SEE ALSO

- `.f5/config/agents.yaml` - Agent configuration
- `/f5-persona` - Role-based personas
- `/f5-mode` - Behavioral modes
- `/f5-gate` - Quality gates
