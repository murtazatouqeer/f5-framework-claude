---
description: Status dashboard, health checks, and self-diagnostics
argument-hint: [status|doctor|selftest|health] [options]
---

# /f5-status - Unified Status & Diagnostics Command

**Consolidated command** that replaces:
- `/f5-doctor` → `/f5-status doctor`
- `/f5-selftest` → `/f5-status selftest`

## ARGUMENTS
$ARGUMENTS

## MODE DETECTION

| Pattern | Mode | Description |
|---------|------|-------------|
| `doctor` | DOCTOR | Framework health check |
| `selftest [options]` | SELFTEST | Self-diagnostics suite |
| `health` | HEALTH | Health dashboard |
| `<other>` (default) | STATUS | Project status dashboard |

---

## MODE: DOCTOR (from /f5-doctor)

### `/f5-status doctor`

Check F5 Framework health in current project.

**Checks:**
1. F5 Framework installation (.f5/ directory)
2. Config validation (config.json)
3. Version check (local vs global)
4. MCP server connectivity
5. Gate configuration
6. Command availability

**Examples:**
```bash
/f5-status doctor
/f5-status doctor --verbose
/f5-status doctor --fix
```

---

## MODE: SELFTEST (from /f5-selftest)

### `/f5-status selftest [options]`

Run diagnostic tests to verify F5 Framework installation.

| Option | Description |
|--------|-------------|
| `--full` | Run all tests |
| `--suite <name>` | Specific test suite (quick/standard/full/mcp) |
| `--fix` | Auto-fix issues |
| `--category <name>` | Specific category (config/memory/gates/mcp/commands) |

**Examples:**
```bash
/f5-status selftest
/f5-status selftest --full
/f5-status selftest --suite mcp
/f5-status selftest --fix
```

---

## MODE: STATUS (Default)

Display comprehensive project status with per-requirement tracking.

## STEP 0: RESOLVE LANGUAGE

Resolve active language for output labels.

```bash
resolve_language() {
  # 1. Check --lang flag
  if [ -n "$LANG_FLAG" ]; then echo "$LANG_FLAG"; return; fi

  # 2. Check project config
  if [ -f ".f5/config.json" ]; then
    PROJECT_LANG=$(jq -r '.language // empty' .f5/config.json 2>/dev/null)
    if [ -n "$PROJECT_LANG" ] && [ "$PROJECT_LANG" != "null" ]; then
      echo "$PROJECT_LANG"; return
    fi
  fi

  # 3. Check global preference
  if [ -f ~/.f5/preferences.yaml ]; then
    GLOBAL_LANG=$(grep '^language:' ~/.f5/preferences.yaml 2>/dev/null | sed 's/language:[[:space:]]*"\{0,1\}\([^"]*\)"\{0,1\}/\1/')
    if [ -n "$GLOBAL_LANG" ]; then echo "$GLOBAL_LANG"; return; fi
  fi

  # 4. Default
  echo "en"
}

ACTIVE_LANG=$(resolve_language)
```

### i18n Labels Reference

| Key | en | vi | ja |
|-----|----|----|-----|
| title | Project Status Dashboard | Bảng điều khiển dự án | プロジェクトステータスダッシュボード |
| overall_progress | Overall Progress | Tiến độ tổng thể | 全体進捗 |
| gate_matrix | Gate Completion Matrix | Ma trận hoàn thành Gate | ゲート完了マトリックス |
| by_developer | Progress by Developer | Tiến độ theo Developer | 開発者別進捗 |
| by_gate | Requirements by Gate | Yêu cầu theo Gate | ゲート別要件 |
| blocked_reqs | Blocked Requirements | Yêu cầu bị chặn | ブロックされた要件 |
| no_blockers | No blocked requirements | Không có yêu cầu bị chặn | ブロックされた要件はありません |
| summary | Summary | Tóm tắt | サマリー |
| total | Total | Tổng | 合計 |
| completed | Completed | Hoàn thành | 完了 |
| in_progress | In Progress | Đang tiến hành | 進行中 |
| blocked | Blocked | Bị chặn | ブロック中 |
| pending | Pending | Đang chờ | 保留中 |

## OVERVIEW

Quick status view of entire F5 Framework state with health scoring.

---

## HEALTH DASHBOARD

### `/f5-status health`

```
═══════════════════════════════════════════════════════════════
                    F5 HEALTH DASHBOARD
═══════════════════════════════════════════════════════════════

🏥 OVERALL HEALTH SCORE
───────────────────────────────────────────────────────────────
   [████████████████████░░░░] 82/100 ✅ Good

📊 CATEGORY BREAKDOWN
───────────────────────────────────────────────────────────────
   🏥 System         [██████████████████░░] 92% ✅
   ⚙️ Configuration  [████████████████░░░░] 85% ✅
   🔄 Workflow       [██████████████░░░░░░] 72% 🔶
   ✨ Quality        [████████████████░░░░] 80% ✅
   🔗 Integration    [██████████████░░░░░░] 78% ✅

📋 KEY METRICS
───────────────────────────────────────────────────────────────
   ✅ Configuration Valid
   ✅ Memory System Initialized
   ✅ Commands Available (15)
   ⚠️ Gate Progress: 1 day behind schedule
   ✅ Traceability: 92%
   ✅ Error Rate: 3.2%
   ⚠️ MCP Fallback Rate: 12%
   ✅ Test Coverage: 84%

🚨 ACTIVE ISSUES (2)
───────────────────────────────────────────────────────────────
   • ⚠️ Gate D4 behind schedule (Priority: 2)
   • ⚠️ Serena MCP fallback rate high (Priority: 3)

💡 RECOMMENDATIONS
───────────────────────────────────────────────────────────────
   1. Review Gate D4 blockers - consider escalation
   2. Check Serena MCP configuration
   3. Continue using TDD for new features

═══════════════════════════════════════════════════════════════
Last Updated: 2024-01-15 10:30:00 | Next Check: Auto on /f5-load
═══════════════════════════════════════════════════════════════
```

### Health Score Ranges

| Score | Label | Icon | Meaning |
|-------|-------|------|---------|
| 90-100 | Excellent | 🌟 | All systems optimal |
| 75-89 | Good | ✅ | Minor issues only |
| 60-74 | Fair | 🔶 | Attention needed |
| 40-59 | Poor | ⚠️ | Multiple issues |
| 0-39 | Critical | 🔴 | Immediate action required |

### Health Categories

| Category | Icon | What it Measures |
|----------|------|------------------|
| System | 🏥 | Core framework components |
| Configuration | ⚙️ | Project settings |
| Workflow | 🔄 | Gate progress, blockers |
| Quality | ✨ | Error rate, test coverage |
| Integration | 🔗 | MCP availability |

---

## ACTION: DEFAULT

### `/f5-status`

```markdown
╔══════════════════════════════════════════════════════════════════╗
║                     F5 FRAMEWORK STATUS                           ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                   ║
║  ┌─ PROJECT ──────────────────────────────────────────────────┐  ║
║  │  Name: {{project_name}}                                     │  ║
║  │  Stack: {{stack_backend}} + {{stack_db}} + {{stack_cache}}  │  ║
║  │  Path: {{project_path}}                                     │  ║
║  └────────────────────────────────────────────────────────────┘  ║
║                                                                   ║
║  ┌─ WORKFLOW ─────────────────────────────────────────────────┐  ║
║  │  Gate: {{gate}} ({{gate_name}})                             │  ║
║  │  Progress: {{progress_bar}} {{progress}}%                   │  ║
║  │  Blockers: {{blocker_count}} ({{blocker_details}})          │  ║
║  └────────────────────────────────────────────────────────────┘  ║
║                                                                   ║
║  ┌─ AI STATE ─────────────────────────────────────────────────┐  ║
║  │  Mode: {{mode_emoji}} {{mode}} ({{mode_source}})            │  ║
║  │  Persona: {{persona_emoji}} {{persona}} ({{persona_source}})│  ║
║  │  Verbosity: {{verbosity}}/5 ({{verbosity_label}})           │  ║
║  │  Agent: {{active_agent}}                                    │  ║
║  └────────────────────────────────────────────────────────────┘  ║
║                                                                   ║
║  ┌─ SESSION ──────────────────────────────────────────────────┐  ║
║  │  ID: {{session_id}}    Duration: {{session_duration}}       │  ║
║  │  Checkpoints: {{checkpoint_count}}  Last save: {{last_save}}│  ║
║  └────────────────────────────────────────────────────────────┘  ║
║                                                                   ║
║  ┌─ CONNECTIONS ──────────────────────────────────────────────┐  ║
║  │  MCP: {{mcp_status_list}}                                   │  ║
║  │  Skills: {{skills_count}} loaded   Agents: {{agents_count}} │  ║
║  └────────────────────────────────────────────────────────────┘  ║
║                                                                   ║
╠══════════════════════════════════════════════════════════════════╣
║  /f5-gate status | /f5-mode list | /f5-session status            ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## SUBCOMMANDS

| Command | Description |
|---------|-------------|
| (default) | Full status |
| `health` | Health dashboard |
| `--compact` | One-line status |
| `--json` | JSON output |
| `project` | Project details only |
| `workflow` | Gate/progress only |
| `ai` | Mode/persona/agent only |
| `agents` | **Auto-activated agents status** |
| `session` | Session details only |
| `--health-only` | Health score only |
| `--recommendations` | Show recommendations |
| `--by-dev` | **Per-requirement status by developer** |
| `--by-gate` | **Per-requirement status by gate** |
| `--blockers` | **Show blocked requirements** |
| `report [--weekly\|--daily]` | **Generate status report** |
| `export --format <fmt>` | **Export status data** |

---

## ACTION: COMPACT

### `/f5-status --compact`

```
F5: {{project}} | {{stack}} | {{gate}} {{progress}}% | {{mode_emoji}} {{mode}} | {{persona_emoji}} {{persona}} | {{session_duration}}
```

---

## ACTION: PROJECT

### `/f5-status project`

```markdown
## 📦 Project Status

### Configuration
| Field | Value |
|-------|-------|
| Name | {{project_name}} |
| Version | {{project_version}} |
| Path | {{project_path}} |

### Stack
| Layer | Technology |
|-------|------------|
| Backend | {{stack_backend}} |
| Frontend | {{stack_frontend}} |
| Mobile | {{stack_mobile}} |
| Database | {{stack_db}} |
| Cache | {{stack_cache}} |
| Queue | {{stack_queue}} |

### Architecture
| Setting | Value |
|---------|-------|
| Type | {{architecture_type}} |
| Scale | {{architecture_scale}} |
| Domain | {{domain}} / {{subdomain}} |
```

---

## ACTION: WORKFLOW

### `/f5-status workflow`

```markdown
## 🚦 Workflow Status

### Quality Gates
| Gate | Name | Status | Progress |
|------|------|--------|----------|
| D1 | Research Complete | {{d1_status}} | {{d1_progress}} |
| D2 | SRS Approved | {{d2_status}} | {{d2_progress}} |
| D3 | Basic Design | {{d3_status}} | {{d3_progress}} |
| D4 | Detail Design | {{d4_status}} | {{d4_progress}} |
| G2 | Implementation Ready | {{g2_status}} | {{g2_progress}} |
| G3 | Testing Complete | {{g3_status}} | {{g3_progress}} |
| G4 | Deployment Ready | {{g4_status}} | {{g4_progress}} |

### Current Gate: {{current_gate}}
Progress: {{progress_bar}} {{progress}}%
Checklist: {{checklist_done}}/{{checklist_total}}

### Blockers
{{blockers_list}}

### Commands
```bash
/f5-gate check {{current_gate}}
/f5-gate complete {{current_gate}}
```
```

---

## ACTION: AI_STATE

### `/f5-status ai`

```markdown
## 🤖 AI State

### Mode
| Field | Value |
|-------|-------|
| Current | {{mode_emoji}} {{mode}} |
| Source | {{mode_source}} |
| Auto-detected | {{mode_auto}} |
| Locked | {{mode_locked}} |

### Persona
| Field | Value |
|-------|-------|
| Current | {{persona_emoji}} {{persona}} |
| Source | {{persona_source}} |
| Auto-detected | {{persona_auto}} |
| Locked | {{persona_locked}} |

### Verbosity
| Field | Value |
|-------|-------|
| Level | {{verbosity}}/5 |
| Label | {{verbosity_label}} |
| Source | {{verbosity_source}} |

### Active Agent
| Field | Value |
|-------|-------|
| Agent | {{active_agent}} |
| Pipeline | {{active_pipeline}} |

### Commands
```bash
/f5-mode set <mode>
/f5-persona <persona>
/f5-agent list
```
```

---

## ACTION: AGENTS_STATUS

### `/f5-status agents`

Show currently active agents from auto-activation:

```
Active Agents
===============================================================

  security_scanner
     Trigger: keyword "security vulnerability"
     Context: Security analysis requested

  test_writer
     Trigger: file "*.spec.ts"
     Context: Test file

  Gate: G2 Implementation
     Agents: code_generator, code_reviewer, test_writer

===============================================================
```

### Active Agent Details

```markdown
## Active Agents

### Auto-Activated
| Agent | Trigger | Context | Priority |
|-------|---------|---------|----------|
| security_scanner | keyword: "security" | Security analysis | 100 |
| test_writer | file: "*.spec.ts" | Test file | 70 |
| code_generator | gate: G2 | Implementation | 50 |

### Gate-Based Agents
**Current Gate:** G2 (Implementation)
**Gate Agents:** code_generator, code_reviewer, test_writer
**Message:** G2 Implementation - development agents active

### Priority Order
1. security_scanner (100)
2. debugger (90)
3. code_reviewer (80)
4. test_writer (70)
5. performance_analyzer (60)
```

### Disable/Enable Agents

```bash
# Disable specific agent for this session
/f5-config disable-agent security_scanner

# Disable auto-activation entirely
/f5-config set auto_activation.enabled false

# Re-enable
/f5-config set auto_activation.enabled true

# Check config
cat .f5/config/automation.yaml
```

---

## ACTION: SESSION_STATUS

### `/f5-status session`

```markdown
## 📊 Session Status

### Current Session
| Field | Value |
|-------|-------|
| ID | {{session_id}} |
| Started | {{session_started}} |
| Duration | {{session_duration}} |
| Last Save | {{last_save}} |

### Checkpoints
| # | Name | Time |
|---|------|------|
{{checkpoints_table}}

### Context
| Item | Count |
|------|-------|
| Recent Files | {{recent_files_count}} |
| Recent Commands | {{recent_commands_count}} |
| Decisions | {{decisions_count}} |

### Commands
```bash
/f5-session save
/f5-session checkpoint "name"
/f5-session restore
```
```

---

## ACTION: JSON

### `/f5-status --json`

```json
{
  "project": {
    "name": "{{project_name}}",
    "stack": "{{stack}}"
  },
  "workflow": {
    "gate": "{{gate}}",
    "progress": {{progress}}
  },
  "ai": {
    "mode": "{{mode}}",
    "persona": "{{persona}}",
    "verbosity": {{verbosity}}
  },
  "session": {
    "id": "{{session_id}}",
    "duration": "{{session_duration}}"
  },
  "connections": {
    "mcp": {{mcp_connected}},
    "skills": {{skills_count}},
    "agents": {{agents_count}}
  }
}
```

---

# ═══════════════════════════════════════════════════════════════
# DETAILED STATUS (Legacy Format)
# ═══════════════════════════════════════════════════════════════

## PURPOSE

Show the current state of the F5 project to:
- Help Claude understand project context
- Show user what's configured
- Display progress on workflows
- Highlight recommendations

## LEGACY OUTPUT FORMAT

```
📊 F5 Project Status
═══════════════════════════════════════════════════════════════

🎯 Project: {project-name}
   Version: {version}
   Created: {date}
   F5 Version: {f5-version}

📍 Current Context:
   Phase: {RESEARCH | DESIGN | IMPLEMENTATION | TESTING | DEPLOYMENT}
   Mode: {current-mode} {(auto-detected) if auto}
   Focus: {what user is working on}

🏗️ Architecture:
   Type: {monolith | modular-monolith | microservices | serverless}
   Scale: {starter | growth | enterprise}
   Domain: {domain} / {sub-domain}

🔧 Tech Stack:
   Backend:  {backend}
   Frontend: {frontend}
   Mobile:   {mobile}
   Database: {database}
   Cache:    {cache}
   Queue:    {queue}

📦 Active Modules:
   • {module-1} ({type})
   • {module-2} ({type})
   • ...

🎯 Installed Skills:
   • {skill-1}
   • {skill-2}
   • ...

🔌 MCP Servers:
   ✓ {server-1}    - {description}
   ✓ {server-2}    - {description}
   ○ {server-3}    - Not installed
   ○ {server-4}    - Not installed

🚦 Quality Gates:
   ┌───────┬────────────┬───────┐
   │ Gate  │ Status     │ Score │
   ├───────┼────────────┼───────┤
   │ D1    │ ✅ PASSED  │ {%}   │
   │ D2    │ ✅ PASSED  │ {%}   │
   │ D3    │ 🔄 PENDING │ -     │
   │ D4    │ ⏳ WAITING │ -     │
   │ G2    │ ⏳ WAITING │ -     │
   │ G3    │ ⏳ WAITING │ -     │
   │ G4    │ ⏳ WAITING │ -     │
   └───────┴────────────┴───────┘

📄 Documents:
   Features: {count} documented
   Latest: {feature-name} (v{version})

📋 BA Workflow:
   Phase: {1-5} - {phase-name}
   Gate {n}: {status}

🔒 Strict Mode:
   Status: {ACTIVE | INACTIVE | PAUSED}
   Session: {session-id}
   Progress: {done}/{total} ({%})

💡 Recommendations:
   • {recommendation-1}
   • {recommendation-2}
   • {recommendation-3}

═══════════════════════════════════════════════════════════════
```

## SECTIONS EXPLAINED

### Project Info
- Basic metadata from .claude/f5/config.json
- F5 version for compatibility checking

### Current Context
- **Phase**: Current development phase
  - RESEARCH: Gathering information
  - DESIGN: Architecture & planning
  - IMPLEMENTATION: Writing code
  - TESTING: QA & validation
  - DEPLOYMENT: Release & ops
- **Mode**: Current behavioral mode
- **Focus**: What user is currently working on

### Architecture & Stack
- From config.json
- Helps Claude suggest appropriate patterns

### Active Modules
- Tech stack modules (NestJS, Go, etc.)
- Business domain modules (fintech, e-commerce)
- Provides domain-specific knowledge

### Installed Skills
- Skills in .claude/skills/
- Claude reads these for specialized knowledge

### MCP Servers
- ✓ = Installed and available
- ○ = Not installed
- Recommendations based on project needs

### Quality Gates
- F5 quality gate status (D1-D4, G2-G4)
- Scores from validation runs

### Integration Status
- BA Workflow progress
- Strict Mode status
- Document pipeline status

### Recommendations
- Based on project state
- Missing tools/skills
- Suggested next actions

## OPTIONS

| Option | Description |
|--------|-------------|
| `--brief` | Short summary only |
| `--full` | Include all details |
| `--json` | Output as JSON |
| `--context` | Focus on current context |
| `--gates` | Show only quality gates |
| `--stack` | Show only tech stack |

## ACTION: BRIEF STATUS

### `/f5-status --brief`

```
📊 F5: online-shop (growth)
   Stack: NestJS + Next.js + PostgreSQL
   Mode: development
   Gates: D1 ✓ D2 ✓ D3 🔄 D4 ⏳
   Strict: INACTIVE

💡 Run /f5-status for full details
```

## ACTION: CONTEXT STATUS

### `/f5-status --context`

```
📍 Current Context

Project: online-shop
Phase: IMPLEMENTATION
Mode: development (auto-detected)

Working On:
  Feature: user-authentication
  Requirements: 15 total, 8 completed
  Current: REQ-009 (JWT refresh tokens)

Recent Activity:
  • Completed REQ-008: Login endpoint
  • Started REQ-009: JWT refresh
  • Blocked: REQ-012 (waiting for API keys)

Strict Mode:
  Session: strict-2024-01-15-abc123
  Progress: 8/15 (53%)

Next Up:
  • REQ-009: JWT refresh (in progress)
  • REQ-010: Password reset
  • REQ-011: Session management
```

## ACTION: GATES STATUS

### `/f5-status --gates`

```
🚦 Quality Gates Status

════════════════════════════════════════════════════════════════

Design Gates:
  D1 │ Research Complete    │ ✅ PASSED │ 92% │ 2024-01-10
  D2 │ SRS Approved         │ ✅ PASSED │ 88% │ 2024-01-12
  D3 │ Basic Design         │ 🔄 PENDING│ -   │ In review
  D4 │ Detail Design        │ ⏳ WAITING│ -   │ Blocked by D3

Implementation Gates:
  G2 │ Implementation Ready │ ⏳ WAITING│ -   │ Blocked by D4
  G3 │ Testing Complete     │ ⏳ WAITING│ -   │ Not started
  G4 │ Deployment Ready     │ ⏳ WAITING│ -   │ Not started

Current Focus: D3 (Basic Design)
  Checklist: 8/12 items complete
  Blockers: Architecture review pending

Commands:
  /f5-gate check D3    # Check D3 status
  /f5-gate complete D3 # Mark D3 complete
```

## ACTION: JSON OUTPUT

### `/f5-status --json`

```json
{
  "project": {
    "name": "online-shop",
    "version": "1.0.0",
    "created": "2024-01-15T09:00:00Z",
    "f5Version": "1.2.0"
  },
  "context": {
    "phase": "IMPLEMENTATION",
    "mode": "development",
    "modeAutoDetected": true,
    "focus": "user-authentication"
  },
  "architecture": {
    "type": "modular-monolith",
    "scale": "growth",
    "domain": "e-commerce",
    "subDomain": "b2c-retail"
  },
  "stack": {
    "backend": ["nestjs"],
    "frontend": "nextjs",
    "database": ["postgresql"],
    "cache": "redis"
  },
  "modules": ["nestjs", "e-commerce"],
  "skills": ["api-design", "testing-strategy", "security-basics"],
  "mcp": {
    "installed": ["tavily", "context7"],
    "available": ["playwright", "serena", "magic"]
  },
  "gates": {
    "D1": { "status": "passed", "score": 92 },
    "D2": { "status": "passed", "score": 88 },
    "D3": { "status": "pending", "score": null },
    "D4": { "status": "waiting", "score": null }
  },
  "strict": {
    "status": "active",
    "sessionId": "strict-2024-01-15-abc123",
    "progress": { "done": 8, "total": 15 }
  },
  "recommendations": [
    "Install playwright for E2E testing",
    "Complete Gate D3 before implementation",
    "Consider security-advanced skill for auth module"
  ]
}
```

## INTEGRATION WITH CLAUDE

```
HOW CLAUDE USES STATUS:

1. Understanding Context
   → Adjust responses based on current phase
   → Apply appropriate mode behavior
   → Use relevant skills

2. Tool Selection
   → Use available MCP servers
   → Recommend missing tools
   → Work within constraints

3. Progress Tracking
   → Reference gate status
   → Continue from strict mode progress
   → Track BA workflow phase

4. Recommendations
   → Suggest next actions
   → Identify blockers
   → Prioritize work

EXAMPLE:
User: "Help me with the checkout feature"

Claude checks /f5-status:
  - Phase: IMPLEMENTATION
  - Mode: development
  - Domain: e-commerce
  - Strict: ACTIVE on auth module

Claude responds:
  "I see you're in the implementation phase with strict mode
   active on the auth module. Let me help with checkout, but
   first - should we finish the auth requirements or start a
   new strict session for checkout?"
```

## NO F5 PROJECT DETECTED

```
If .claude/f5/config.json doesn't exist:

📊 F5 Project Status
═══════════════════════════════════════════════════════════════

⚠️  No F5 project detected in current directory.

Options:
  /f5-init    Create NEW project with F5
  /f5-load    Add F5 to EXISTING project

Current directory: /path/to/directory
```

## EXAMPLES

```bash
# Full status (default)
/f5-status

# Brief summary
/f5-status --brief

# JSON format
/f5-status --json

# Context focus
/f5-status --context

# Quality gates only
/f5-status --gates

# Tech stack only
/f5-status --stack
```

---

# ═══════════════════════════════════════════════════════════════
# PER-REQUIREMENT TRACKING (Issue 5)
# ═══════════════════════════════════════════════════════════════

## ACTION: REQUIREMENTS_SUMMARY

### `/f5-status` (with requirements index)

When `.f5/requirements/index.yaml` exists, show requirements summary in the default status:

```markdown
### 📋 Requirements Tracking

**Source:** .f5/requirements/index.yaml

| Metric | Value |
|--------|-------|
| Total Requirements | {{TOTAL}} |
| Overall Progress | {{PROGRESS}}% |
| Completed | {{COMPLETED}} |
| In Progress | {{IN_PROGRESS}} |
| Blocked | {{BLOCKED}} |

#### Gate Matrix
| Gate | ✅ Done | 🔄 WIP | ⏳ Pending | 🚫 Blocked |
|------|---------|--------|-----------|------------|
| D1-D4 | {{DESIGN_DONE}} | {{DESIGN_WIP}} | {{DESIGN_PENDING}} | {{DESIGN_BLOCKED}} |
| G2-G4 | {{EXEC_DONE}} | {{EXEC_WIP}} | {{EXEC_PENDING}} | {{EXEC_BLOCKED}} |

{{#if BLOCKERS}}
#### ⚠️ Active Blockers
{{#each BLOCKERS}}
- **{{this.id}}**: {{this.reason}} ({{this.assignee}})
{{/each}}
{{/if}}

Quick: `/f5-req list` | `/f5-status --by-dev` | `/f5-status --blockers`
```

---

## ACTION: BY_DEVELOPER

### `/f5-status --by-dev`

Show progress grouped by developer from requirements index.

**Process:**
1. Read `.f5/requirements/index.yaml`
2. Group by `by_developer` section
3. Display workload and progress per developer

**Output:**
```markdown
## 👥 Progress by Developer

═══════════════════════════════════════════════════════════════

{{#each DEVELOPERS}}
### {{this.name}} ({{this.id}})

**Assigned:** {{this.assigned}} | **Avg Progress:** {{this.avg_progress}}%

| REQ | Name | Gate | Progress | Status |
|-----|------|------|----------|--------|
{{#each this.requirements}}
| {{this.id}} | {{this.name}} | {{this.gate}} | {{this.progress}}% | {{this.status_emoji}} |
{{/each}}

---
{{/each}}

### Unassigned Requirements

{{#if UNASSIGNED}}
| REQ | Name | Gate |
|-----|------|------|
{{#each UNASSIGNED}}
| {{this.id}} | {{this.name}} | {{this.gate}} |
{{/each}}

⚠️ {{UNASSIGNED_COUNT}} requirements need assignment!
{{else}}
✅ All requirements are assigned.
{{/if}}

═══════════════════════════════════════════════════════════════
```

---

## ACTION: BY_GATE

### `/f5-status --by-gate [gate]`

Show requirements grouped by gate status.

**Output:**
```markdown
## 🚦 Requirements by Gate

═══════════════════════════════════════════════════════════════

### D1 - Requirements Analysis ({{D1_TOTAL}})

**Completed:** {{D1_DONE}} | **In Progress:** {{D1_WIP}} | **Pending:** {{D1_PENDING}}

{{#each D1_REQUIREMENTS}}
- {{#if completed}}✅{{else if in_progress}}🔄{{else}}⏳{{/if}} **{{this.id}}**: {{this.name}} ({{this.assignee}})
{{/each}}

---

### D2 - SRS Creation ({{D2_TOTAL}})
...

### D3 - Basic Design ({{D3_TOTAL}})
...

### D4 - Detail Design ({{D4_TOTAL}})
...

### G2 - Implementation ({{G2_TOTAL}})

**Completed:** {{G2_DONE}} | **In Progress:** {{G2_WIP}} | **Pending:** {{G2_PENDING}}

{{#each G2_REQUIREMENTS}}
- {{this.status_emoji}} **{{this.id}}**: {{this.name}}
  - Assignee: {{this.assignee}}
  - Progress: {{this.progress}}%
{{/each}}

---

### G3 - Testing ({{G3_TOTAL}})
...

### G4 - Deployment ({{G4_TOTAL}})
...

═══════════════════════════════════════════════════════════════
```

---

## ACTION: BLOCKERS

### `/f5-status --blockers`

Show all blocked requirements with details.

**Output:**
```markdown
## 🚫 Blocked Requirements

{{#if BLOCKERS}}
═══════════════════════════════════════════════════════════════

{{#each BLOCKERS}}
### {{this.id}}: {{this.name}}

| Property | Value |
|----------|-------|
| Assigned To | {{this.assignee}} |
| Blocked Gate | {{this.gate}} |
| Blocked Since | {{this.since}} ({{this.days}} days) |

**Blocker:**
> {{this.reason}}

**Actions:**
- Resolve: `/f5-req gate {{this.id}} {{this.gate}} --unblock`
- View details: `/f5-req show {{this.id}}`

---
{{/each}}

**Summary:** {{BLOCKER_COUNT}} requirements blocked, averaging {{AVG_BLOCKED_DAYS}} days.

{{else}}
✅ No blocked requirements! All clear.
{{/if}}

═══════════════════════════════════════════════════════════════
```

---

## ACTION: GENERATE_REPORT

### `/f5-status report [--weekly|--daily]`

Generate status report for stakeholders.

**Output location:** `.f5/dashboard/reports/{{TYPE}}-{{DATE}}.md`

**Report content includes:**
- Executive summary
- Progress metrics
- Gate completion status
- Developer workload
- Blockers and risks
- Action items

---

## ACTION: EXPORT_STATUS

### `/f5-status export --format <md|html|pdf|json>`

Export status for external use.

**Formats:**
- `md` - Markdown for documentation
- `html` - HTML for web viewing
- `json` - JSON for integrations

**Output location:** `.f5/dashboard/exports/status-{{DATE}}.{{FORMAT}}`

---

**Tip:** Run `/f5-status` at the start of each session to give Claude full context!
