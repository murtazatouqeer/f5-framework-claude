---
description: Interactive F5 tutorials
argument-hint: [topic]
---

# /f5-tutorial - F5 Framework Interactive Tutorial

> **Purpose**: Interactive learning experience for F5 Framework features
> **Version**: 2.0.0
> **Category**: Education

---

## Command Syntax

```bash
# Start tutorial from beginning
/f5-tutorial

# Start specific chapter
/f5-tutorial --chapter <number>

# Start specific topic
/f5-tutorial --topic <name>

# Quick tips mode
/f5-tutorial tips

# Show progress
/f5-tutorial progress

# Reset progress
/f5-tutorial reset

# List all chapters
/f5-tutorial list

# Verbosity (tutorial always uses level 5)
/f5-tutorial --v5
```

---

## Input Processing

### 1. Parse Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--chapter` | Start specific chapter | 1 |
| `--topic` | Start specific topic | - |
| `tips` | Show random tips | - |
| `progress` | Show completion status | - |
| `reset` | Reset tutorial progress | - |
| `list` | List all chapters | - |

### 2. Tutorial Structure

| Chapter | Title | Topics |
|---------|-------|--------|
| 1 | Getting Started | 5 |
| 2 | Project Configuration | 4 |
| 3 | Quality Gates | 6 |
| 4 | Memory System | 4 |
| 5 | Personas & Modes | 5 |
| 6 | TDD Workflow | 4 |
| 7 | Advanced Features | 5 |
| 8 | Best Practices | 4 |

---

## Chapter Content

### Chapter 1: Getting Started

```
═══════════════════════════════════════════════════════════════
           📚 F5 TUTORIAL - CHAPTER 1: GETTING STARTED
═══════════════════════════════════════════════════════════════

Welcome to F5 Framework! Let's learn the basics.

TOPICS IN THIS CHAPTER:
───────────────────────────────────────────────────────────────
1.1 What is F5 Framework?
1.2 Installing F5
1.3 Your First Project
1.4 Essential Commands
1.5 Getting Help

───────────────────────────────────────────────────────────────
Type 'next' to continue, 'skip' to skip, or topic number (1.1)
═══════════════════════════════════════════════════════════════
```

#### Topic 1.1: What is F5 Framework?

```
═══════════════════════════════════════════════════════════════
           📖 TOPIC 1.1: WHAT IS F5 FRAMEWORK?
═══════════════════════════════════════════════════════════════

F5 Framework is an Enterprise Spec-Driven Development Toolkit
designed for Japanese outsource workflows.

KEY FEATURES:
───────────────────────────────────────────────────────────────
🎯 Quality Gates     - D1 → D2 → D3 → D4 → G2 → G3 → G4
🧠 Memory System     - Constitution, Session, Decisions, Learnings
👤 Personas          - Specialized roles for different tasks
📊 Analytics         - Track usage and get insights
🔧 Traceability      - Link code to requirements

SUPPORTED WORKFLOWS:
───────────────────────────────────────────────────────────────
• Full project from requirements → deployment
• Basic design starting point (customer provides SRS)
• Detail design starting point (customer provides design)
• Change request / maintenance mode

───────────────────────────────────────────────────────────────
💡 TIP: F5 works best with clear requirements and defined gates

Type 'next' to continue or 'back' to go back
═══════════════════════════════════════════════════════════════
```

#### Topic 1.2: Installing F5

```
═══════════════════════════════════════════════════════════════
           📖 TOPIC 1.2: INSTALLING F5
═══════════════════════════════════════════════════════════════

F5 Framework is installed via slash commands in Claude Code.

REQUIREMENTS:
───────────────────────────────────────────────────────────────
✅ Claude Code or Claude with Projects
✅ Workspace with write permissions
✅ (Optional) MCP servers for enhanced features

INSTALLATION STEPS:
───────────────────────────────────────────────────────────────
1. Create a new project directory

2. Initialize F5 Framework:
   /f5-init my-project

3. Verify installation:
   /f5-selftest

4. Load project context:
   /f5-load

VERIFICATION:
───────────────────────────────────────────────────────────────
After running /f5-init, you should see:

  .f5/
  ├── config.json
  ├── profile.yaml
  ├── memory/
  └── quality/

───────────────────────────────────────────────────────────────
🎯 TRY IT: Run /f5-init test-project to create a test project

Type 'next' to continue or 'try' to practice
═══════════════════════════════════════════════════════════════
```

#### Topic 1.3: Your First Project

```
═══════════════════════════════════════════════════════════════
           📖 TOPIC 1.3: YOUR FIRST PROJECT
═══════════════════════════════════════════════════════════════

Let's create your first F5 project step by step.

STEP 1: INITIALIZE
───────────────────────────────────────────────────────────────
/f5-init my-first-project --starting-point requirements

This creates:
• Project configuration
• Memory system structure
• Quality gate templates
• Initial checklist files

STEP 2: CONFIGURE
───────────────────────────────────────────────────────────────
Edit .f5/config.json:
{
  "name": "my-first-project",
  "domain": { "name": "e-commerce" },
  "stack": { "backend": ["nestjs"], "frontend": "react" }
}

STEP 3: LOAD CONTEXT
───────────────────────────────────────────────────────────────
/f5-load

This loads:
• Project configuration
• Memory system
• Quality gates status
• Domain knowledge

STEP 4: CHECK STATUS
───────────────────────────────────────────────────────────────
/f5-status

See your project state and next recommended actions.

───────────────────────────────────────────────────────────────
🎯 TRY IT: Create a test project and explore its structure

Type 'next' to continue or 'try' to practice
═══════════════════════════════════════════════════════════════
```

#### Topic 1.4: Essential Commands

```
═══════════════════════════════════════════════════════════════
           📖 TOPIC 1.4: ESSENTIAL COMMANDS
═══════════════════════════════════════════════════════════════

Here are the commands you'll use most often:

SESSION COMMANDS:
───────────────────────────────────────────────────────────────
/f5-load          Load project context (RUN FIRST!)
/f5-status        View project status
/f5-init          Initialize new project

QUALITY COMMANDS:
───────────────────────────────────────────────────────────────
/f5-gate check    Check gate status
/f5-gate start    Start gate review
/f5-gate complete Complete gate

DOCUMENT COMMANDS:
───────────────────────────────────────────────────────────────
/f5-import        Import Excel documents
/f5-spec          Generate specifications
/f5-design        Generate design documents

DEVELOPMENT COMMANDS:
───────────────────────────────────────────────────────────────
/f5-implement     Implement with traceability
/f5-test          Run tests
/f5-tdd           TDD workflow

DIAGNOSTIC COMMANDS:
───────────────────────────────────────────────────────────────
/f5-selftest      System diagnostics
/f5-analytics     Usage metrics

───────────────────────────────────────────────────────────────
💡 TIP: Always run /f5-load at the start of each session!

Type 'next' to continue
═══════════════════════════════════════════════════════════════
```

#### Topic 1.5: Getting Help

```
═══════════════════════════════════════════════════════════════
           📖 TOPIC 1.5: GETTING HELP
═══════════════════════════════════════════════════════════════

F5 Framework provides multiple ways to get help:

BUILT-IN HELP:
───────────────────────────────────────────────────────────────
/f5-tutorial              This interactive tutorial
/f5-tutorial tips         Quick tips
/f5-status --help         Command-specific help

SELF-DIAGNOSTICS:
───────────────────────────────────────────────────────────────
/f5-selftest              Check system health
/f5-selftest --fix        Auto-fix issues
/f5-analytics insights    Get usage insights

DOCUMENTATION:
───────────────────────────────────────────────────────────────
• CLAUDE.md in project root
• .f5/memory/decisions.md for architecture decisions
• .f5/memory/learnings.md for best practices

ERROR RECOVERY:
───────────────────────────────────────────────────────────────
Errors include:
• Clear error codes (CFG001, MCP001, etc.)
• Suggestions for resolution
• Auto-recovery when available

───────────────────────────────────────────────────────────────
🎉 CHAPTER 1 COMPLETE!

You've learned:
✅ What F5 Framework is
✅ How to install it
✅ Creating your first project
✅ Essential commands
✅ Getting help

Type 'next' to start Chapter 2: Project Configuration
═══════════════════════════════════════════════════════════════
```

---

### Chapter 2: Project Configuration

#### Topic 2.1: config.json

```
═══════════════════════════════════════════════════════════════
           📖 TOPIC 2.1: CONFIG.JSON
═══════════════════════════════════════════════════════════════

The config.json file is the heart of your F5 project.

LOCATION: .f5/config.json

STRUCTURE:
───────────────────────────────────────────────────────────────
{
  "version": "2.0.0",
  "name": "my-project",
  "startingPoint": "requirements",
  "architecture": "microservices",
  "scale": "growth",
  "domain": {
    "name": "fintech",
    "subDomain": "stock-trading"
  },
  "stack": {
    "backend": ["nestjs"],
    "frontend": "react",
    "database": ["postgresql"]
  },
  "qualityGates": {
    "enabled": true,
    "targets": {
      "testCoverage": 80,
      "lintErrors": 0
    }
  }
}

KEY FIELDS:
───────────────────────────────────────────────────────────────
• version        - F5 Framework version
• startingPoint  - Where workflow begins
• architecture   - System architecture type
• domain         - Business domain for knowledge loading
• stack          - Technology stack
• qualityGates   - Gate configuration

───────────────────────────────────────────────────────────────
💡 TIP: Domain affects which knowledge is auto-loaded

Type 'next' to continue
═══════════════════════════════════════════════════════════════
```

#### Topic 2.2: profile.yaml

```
═══════════════════════════════════════════════════════════════
           📖 TOPIC 2.2: PROFILE.YAML
═══════════════════════════════════════════════════════════════

The profile.yaml configures team and customer settings.

LOCATION: .f5/profile.yaml

STRUCTURE:
───────────────────────────────────────────────────────────────
project_type: "mvp"

team:
  size: "6-10"
  has_qa: true
  has_brse: true

customer:
  language: "japanese"
  timezone: "Asia/Tokyo"
  review_style: "async"

preferences:
  documentation_format: "markdown"
  code_style: "strict"

KEY SETTINGS:
───────────────────────────────────────────────────────────────
• project_type   - mvp, growth, enterprise
• team.has_brse  - Bridge SE for Japanese clients
• customer.language - Affects gate documentation
• review_style   - sync or async reviews

CUSTOMER LANGUAGE IMPACT:
───────────────────────────────────────────────────────────────
When customer.language is "japanese":
• Gate names shown in Japanese (D2 = SRS承認)
• Priority values support Japanese (高, 中, 低)
• Excel imports auto-detect Japanese columns

───────────────────────────────────────────────────────────────
💡 TIP: Set customer.language to match your client's preference

Type 'next' to continue
═══════════════════════════════════════════════════════════════
```

---

### Chapter 3: Quality Gates

#### Topic 3.1: Understanding Gates

```
═══════════════════════════════════════════════════════════════
           📖 TOPIC 3.1: UNDERSTANDING QUALITY GATES
═══════════════════════════════════════════════════════════════

Quality Gates ensure work quality before proceeding.

GATE FLOW:
───────────────────────────────────────────────────────────────
D1 → D2 → D3 → D4 → G2 → G3 → G4

DESIGN GATES (D):
───────────────────────────────────────────────────────────────
D1 │ 調査完了      │ Research Complete
D2 │ SRS承認       │ SRS Approved (Customer Sign-off)
D3 │ 基本設計承認  │ Basic Design Approved (Customer Sign-off)
D4 │ 詳細設計承認  │ Detail Design Approved (Customer Sign-off)

IMPLEMENTATION GATES (G):
───────────────────────────────────────────────────────────────
G2 │ 実装完了      │ Implementation Ready
G3 │ テスト完了    │ Testing Complete
G4 │ デプロイ準備  │ Deployment Ready (Customer Sign-off)

CUSTOMER APPROVAL REQUIRED:
───────────────────────────────────────────────────────────────
• D2, D3, D4, G4 require customer sign-off
• D1, G2, G3 are internal checkpoints

───────────────────────────────────────────────────────────────
💡 TIP: Gates with customer approval need documentation review

Type 'next' to continue
═══════════════════════════════════════════════════════════════
```

#### Topic 3.2: Gate Commands

```
═══════════════════════════════════════════════════════════════
           📖 TOPIC 3.2: GATE COMMANDS
═══════════════════════════════════════════════════════════════

Commands for managing quality gates:

CHECK GATE STATUS:
───────────────────────────────────────────────────────────────
/f5-gate check D3

Shows:
• Current checklist progress
• Completed items
• Pending items
• Blockers

START GATE REVIEW:
───────────────────────────────────────────────────────────────
/f5-gate start D3

Creates:
• Gate checklist
• Review documentation
• Approval request (if customer gate)

COMPLETE GATE:
───────────────────────────────────────────────────────────────
/f5-gate complete D3

Requires:
• All checklist items checked
• Prerequisites met (previous gates)
• Customer approval (if required)

VIEW ALL GATES:
───────────────────────────────────────────────────────────────
/f5-gate status

Shows progress across all gates.

───────────────────────────────────────────────────────────────
🎯 TRY IT: Run /f5-gate status to see your gate progress

Type 'next' to continue
═══════════════════════════════════════════════════════════════
```

---

### Chapter 4: Memory System

#### Topic 4.1: Constitution

```
═══════════════════════════════════════════════════════════════
           📖 TOPIC 4.1: CONSTITUTION.MD
═══════════════════════════════════════════════════════════════

The constitution contains NON-NEGOTIABLE project rules.

LOCATION: .f5/memory/constitution.md

PURPOSE:
───────────────────────────────────────────────────────────────
• Define absolute requirements
• Set quality standards
• Document constraints
• Establish Definition of Done

EXAMPLE CONTENT:
───────────────────────────────────────────────────────────────
# Project Constitution

## Non-Negotiable Rules

1. All code MUST pass lint checks
2. Test coverage MUST be >= 80%
3. ALL features MUST have REQ-ID traceability
4. Security review REQUIRED for auth changes
5. Documentation MUST be in Japanese for customer

## Definition of Done

- [ ] Code reviewed by 2 team members
- [ ] Tests passing in CI
- [ ] Documentation updated
- [ ] Customer sign-off (if applicable)

IMPORTANCE:
───────────────────────────────────────────────────────────────
⚠️ ALWAYS read constitution.md at session start
⚠️ These rules OVERRIDE default behaviors
⚠️ Non-compliance = gate failure

───────────────────────────────────────────────────────────────
💡 TIP: Add project-specific constraints to constitution.md

Type 'next' to continue
═══════════════════════════════════════════════════════════════
```

---

### Chapter 5: Personas & Modes

#### Topic 5.1: Available Personas

```
═══════════════════════════════════════════════════════════════
           📖 TOPIC 5.1: AVAILABLE PERSONAS
═══════════════════════════════════════════════════════════════

Personas provide specialized expertise for different tasks.

AVAILABLE PERSONAS:
───────────────────────────────────────────────────────────────
🏗️ architect    │ System design, patterns, scalability
⚙️ backend      │ APIs, services, database logic
🎨 frontend     │ UI/UX, components, accessibility
🔒 security     │ OWASP, authentication, encryption
🧪 qa           │ Testing, coverage, quality
⚡ performance  │ Optimization, caching, profiling
🚀 devops       │ CI/CD, infrastructure, deployment
🗄️ database     │ Schema, queries, migrations
📊 analyst      │ Requirements, use cases, specs
👀 reviewer     │ Code review, best practices
💻 developer    │ Default general development

AUTO-ACTIVATION:
───────────────────────────────────────────────────────────────
Personas auto-activate based on:
• Keywords: "implement auth" → 🔒 security
• File types: *.tsx → 🎨 frontend
• Current gate: G3 → 🧪 qa

MANUAL ACTIVATION:
───────────────────────────────────────────────────────────────
/f5-persona activate security
/f5-implement user-auth --persona security

───────────────────────────────────────────────────────────────
💡 TIP: Let auto-activation work, override only when needed

Type 'next' to continue
═══════════════════════════════════════════════════════════════
```

---

### Chapter 6: TDD Workflow

#### Topic 6.1: TDD Basics

```
═══════════════════════════════════════════════════════════════
           📖 TOPIC 6.1: TDD BASICS
═══════════════════════════════════════════════════════════════

Test-Driven Development with F5 Framework.

TDD CYCLE:
───────────────────────────────────────────────────────────────
  🔴 RED        Write failing tests first
       ↓
  🟢 GREEN      Write minimal code to pass
       ↓
  🔵 REFACTOR   Improve code quality
       ↓
  🔄 REPEAT     Continue for next requirement

BASIC COMMANDS:
───────────────────────────────────────────────────────────────
/f5-tdd start user-registration --for REQ-001
/f5-tdd red        # Write failing tests
/f5-tdd green      # Make tests pass
/f5-tdd refactor   # Improve code
/f5-tdd complete   # Finish session

BENEFITS:
───────────────────────────────────────────────────────────────
• Requirements traced to tests
• High test coverage
• G3 gate evidence auto-generated
• Metrics tracking

───────────────────────────────────────────────────────────────
💡 TIP: TDD sessions generate evidence for Gate G3

Type 'next' to continue
═══════════════════════════════════════════════════════════════
```

---

## Quick Tips Mode

```bash
/f5-tutorial tips
```

```
═══════════════════════════════════════════════════════════════
                    💡 F5 QUICK TIP
═══════════════════════════════════════════════════════════════

TIP #42: Traceability Comments

Always add traceability comments to your code:

// REQ-001: User authentication with JWT tokens
export async function authenticate(credentials) {
  // implementation
}

Supported prefixes:
• REQ-XXX  - Requirements
• FR-XXX   - Functional Requirements
• NFR-XXX  - Non-functional Requirements
• UC-XXX   - Use Cases
• US-XXX   - User Stories

This helps with:
✅ Gate G2 verification
✅ Change impact analysis
✅ Customer reporting

───────────────────────────────────────────────────────────────
Type 'more' for another tip, or 'exit' to close
═══════════════════════════════════════════════════════════════
```

---

## Progress Tracking

```bash
/f5-tutorial progress
```

```
═══════════════════════════════════════════════════════════════
                    📊 TUTORIAL PROGRESS
═══════════════════════════════════════════════════════════════

OVERALL: 45% Complete (15/33 topics)

CHAPTER PROGRESS:
───────────────────────────────────────────────────────────────
Chapter 1: Getting Started      │ ██████████████████░░ │ 100%
Chapter 2: Project Configuration│ ██████████████░░░░░░ │ 75%
Chapter 3: Quality Gates        │ ██████████░░░░░░░░░░ │ 50%
Chapter 4: Memory System        │ ████░░░░░░░░░░░░░░░░ │ 25%
Chapter 5: Personas & Modes     │ ░░░░░░░░░░░░░░░░░░░░ │ 0%
Chapter 6: TDD Workflow         │ ░░░░░░░░░░░░░░░░░░░░ │ 0%
Chapter 7: Advanced Features    │ ░░░░░░░░░░░░░░░░░░░░ │ 0%
Chapter 8: Best Practices       │ ░░░░░░░░░░░░░░░░░░░░ │ 0%

ACHIEVEMENTS:
───────────────────────────────────────────────────────────────
🏆 First Steps - Completed Chapter 1
🏆 Configurator - Learned config.json

NEXT UP:
───────────────────────────────────────────────────────────────
📖 Topic 2.3: Starting Points

───────────────────────────────────────────────────────────────
Type '/f5-tutorial' to continue from where you left off
═══════════════════════════════════════════════════════════════
```

---

## Tutorial Data Storage

Progress stored in `.f5/tutorial/progress.json`:
```json
{
  "completed_topics": ["1.1", "1.2", "1.3", "1.4", "1.5", "2.1", "2.2"],
  "current_chapter": 2,
  "current_topic": "2.3",
  "achievements": ["first_steps", "configurator"],
  "tips_viewed": 42,
  "started_at": "2024-01-10",
  "last_activity": "2024-01-15"
}
```

---

## Verbosity

Tutorial always runs at verbosity level 5 (comprehensive) for maximum learning value.

---

## Related Commands

| Command | Description |
|---------|-------------|
| `/f5-status` | View project status |
| `/f5-selftest` | System diagnostics |
| `/f5-analytics` | Usage insights |
| `/f5-load` | Load project context |

---

*F5 Framework Interactive Tutorial v2.0.0*
