---
description: "Smart contextual help - shows what to do next based on current state"
argument-hint: "[topic] or \"task description\""
---

# F5 Help - Smart Contextual Assistant

## Usage
```
/f5-help                      # Show status + next actions
/f5-help --quickstart         # 5-minute getting started
/f5-help --next               # Single next action
/f5-help --resume             # Resume previous session
/f5-help --stuck              # Troubleshooting help
/f5-help "task description"   # Specific task guidance
/f5-help <topic>              # Topic help (gates, workflow, commands, agents)
```

## Context Detection

First, analyze current state by checking:

### 1. Project Initialization
```bash
# Check if F5 is initialized
ls -la .f5/ 2>/dev/null
```
If .f5/ doesn't exist → Project not initialized

### 2. Current Gate & Workflow
```bash
# Read current state
cat .f5/manifest.yaml 2>/dev/null
cat .f5/gates-status.yaml 2>/dev/null
cat .f5/session.yaml 2>/dev/null
```

### 3. Recent Activity
```bash
# Check recent file changes
git status --short 2>/dev/null | head -10
# Check session file if exists
cat .f5/session.json 2>/dev/null
```

## Response Format

### For No Arguments (Default)
```
📍 Current Status:
   Project: [initialized/not initialized]
   Workflow: [workflow name or "none"]
   Phase: [X/Y (phase name)]
   Gate: [gate ID (gate name)]
   Mode: [mode] | Persona: [persona]

✅ Completed (this phase):
   • [completed item 1]
   • [completed item 2]

📋 Next Actions:
   1. [action 1 with command]
   2. [action 2 with command]
   3. [action 3 with command]

🎯 Suggested Command:
   [most appropriate next command with example]

💡 Tips:
   • [relevant tip 1]
   • [relevant tip 2]
```

### For --quickstart
Provide 5-minute getting started guide:

```
🚀 F5 Framework - 5 Minute Quickstart

F5 Framework is an AI-powered development toolkit that guides you through
documentation-first development with quality gates (D1-D4, G2-G4).

📋 Step 1: Initialize (30 seconds)
   /f5-init

   This creates .f5/ configuration and sets up quality gates.

📋 Step 2: Load Workflow (30 seconds)
   /f5-load

   Auto-detects your stack and asks 2 questions:
   • Starting point (requirements/basic-design/detail-design)
   • Project type (poc/mvp/production)

📋 Step 3: Check Status (10 seconds)
   /f5-status

   Shows current gate, pending items, and progress.

📋 Step 4: Start Working
   Based on your gate:
   • D1-D2: /f5-research, /f5-ba
   • D3-D4: /f5-design, /f5-spec
   • G2: /f5-implement
   • G3: /f5-test

📋 Step 5: Get Help Anytime
   /f5-help              # What to do next
   /f5-help --stuck      # Troubleshooting
   /f5-help "your task"  # Task-specific guidance

⏱️ Total setup time: ~2 minutes
🎯 You're ready to go!
```

### For --next
Single most important next action:
```
🎯 Next Action:
   [command with full example]

   Why: [brief explanation]
```

### For --resume
```
🔄 Session Resume

📍 Last Session:
   Date: [timestamp from .f5/session.json]
   Task: [what was being worked on]
   Progress: [X% or description]

📁 Uncommitted Changes:
   [list from git status]

🎯 Continue With:
   [suggested command to continue]

💡 Or: /f5-help --next for fresh start
```

### For --stuck
```
🔧 Troubleshooting

📍 Current State:
   [detected state]

❓ Common Issues at This Stage:
   1. [issue 1] → [solution]
   2. [issue 2] → [solution]

🔍 Diagnostics:
   • Gate status: [status]
   • Recent errors: [if any]
   • Missing requirements: [if any]

💡 Try:
   [specific command to resolve]

📞 Still stuck?
   Describe your issue: /f5-help "your problem description"
```

### For Specific Task ("task description")
```
📋 Task: [parsed task]

🎯 Recommended Approach:

[Step-by-step with commands]

📍 Current Context:
   Gate: [relevant gate]
   Fits: [yes/no with explanation]

💡 Related Commands:
   [related commands]
```

### For Topics
Topics: gates, workflow, commands, agents, skills, modes

#### Topic: gates
```
📊 F5 Quality Gates

Design Gates (Documentation):
   D1 - Research & Discovery  : Evidence ≥3, Quality ≥80%
   D2 - Requirements (SRS)    : SRS exists + Customer approval
   D3 - Basic Design          : Architecture + Customer approval
   D4 - Detail Design         : All docs + Confidence ≥90%

Implementation Gates:
   G2   - Implementation Ready : Code complete + Review passed
   G2.5 - Verification Complete: Assets + Integration + Visual QA
   G3   - Testing Complete     : Coverage ≥80% + Visual regression
   G4   - Deployment Ready     : All gates passed

Commands:
   /f5-gate status       # Check current gate
   /f5-gate check D3     # Check specific gate
   /f5-gate advance      # Move to next gate
```

#### Topic: workflow
```
📋 F5 Workflows

Available Workflows:
   mvp         - Fast startup (1-3 months)    D1→G3
   greenfield  - New enterprise (3-6 months)  D1→G4
   poc         - Quick prototype (2-4 weeks)  D1→G2
   feature     - Adding features (1-4 weeks)  D3→G3
   maintenance - Bug fixes (1-5 days)         G2→G3

Commands:
   /f5-load              # Auto-detect + load
   /f5-workflow load mvp # Load specific workflow
   /f5-workflow help     # Workflow guidance
```

#### Topic: commands
```
📋 F5 Commands (48 Active)

Core:
   /f5-init      Initialize project
   /f5-load      Load workflow + detect stack
   /f5-status    Show current state
   /f5-help      Contextual help (this command)

Development:
   /f5-implement Feature implementation
   /f5-design    Generate designs
   /f5-test      Run tests
   /f5-review    Code review

Stack:
   /f5-backend   Backend development
   /f5-web       Frontend development
   /f5-db        Database management
   /f5-infra     Infrastructure

Management:
   /f5-gate      Quality gates
   /f5-agent     AI agents
   /f5-ctx       Context management
   /f5-team      Team collaboration

Full list: /f5-status commands
```

#### Topic: agents
```
🤖 F5 AI Agents (16 Specialists)

Architecture:
   @f5:architect   System design, patterns
   @f5:uiarch      Frontend architecture
   @f5:api         API design

Development:
   @f5:backend     Backend code generation
   @f5:frontend    Frontend code generation
   @f5:db          Database expert

Quality:
   @f5:qa          Test writer
   @f5:review      Code reviewer
   @f5:security    Security scanner
   @f5:perf        Performance analyzer

Support:
   @f5:debug       Debugger
   @f5:rca         Root cause analyst
   @f5:refactor    Refactorer
   @f5:docs        Documenter
   @f5:mentor      Teacher/explainer

Usage:
   @f5:security "audit auth module"
   @f5:architect "design user service"
```

#### Topic: skills
```
📚 F5 Skills System

Categories:
   api-design     REST/GraphQL patterns
   architecture   DDD, Clean, Hexagonal
   database       Schema, optimization
   security       OWASP, auth (split: -auth, -infra)
   testing        Unit, integration (split: -advanced)
   devops         CI/CD, containers
   performance    Optimization patterns

Commands:
   /f5-skill list           # Show all skills
   /f5-skill load security  # Load skill
   /f5-skill unload testing # Free tokens

Auto-Detection:
   Skills load automatically based on your stack.
```

#### Topic: modes
```
🎭 F5 Modes & Personas

Modes (how Claude thinks):
   /f5-mode analytical  - Analysis, requirements
   /f5-mode planning    - Architecture, design
   /f5-mode coding      - Implementation
   /f5-mode debugging   - Bug fixing

Personas (domain expertise):
   /f5-agent persona architect  - System design
   /f5-agent persona backend    - APIs, databases
   /f5-agent persona frontend   - UI/UX
   /f5-agent persona qa         - Testing
   /f5-agent persona security   - Security
```

## State-Based Suggestions

### If Project Not Initialized
```
🆕 Getting Started

Your project is not yet initialized with F5 Framework.

🚀 Start Here:
   /f5-init

This will:
   • Create .f5/ configuration
   • Set up quality gates
   • Configure agents

Then: /f5-help for next steps
```

### If Initialized but No Workflow
```
📍 Project Ready

F5 is initialized but no workflow is loaded.

🚀 Load a Workflow:
   /f5-load              # Smart recommendation
   /f5-load greenfield   # New project
   /f5-load feature      # Feature development
   /f5-load maintenance  # Bug fixes

Then: /f5-help for next steps
```

### If Workflow Active
Show current phase, completed items, and next actions based on:
- Current gate requirements
- Workflow phase activities
- Uncompleted checklist items

### Gate-Specific Suggestions

#### At D1 (Research)
```
📋 D1 - Research & Discovery

You're gathering requirements and understanding the problem.

🎯 Focus:
   • Stakeholder interviews
   • Market research
   • Technical feasibility

📋 Commands:
   /f5-research "topic"
   /f5-ba stakeholder "identify stakeholders"

✅ Gate Criteria:
   • Evidence ≥3 sources
   • Quality ≥80%
```

#### At G2 (Implementation)
```
📋 G2 - Implementation

You're writing production code.

🎯 Focus:
   • Feature implementation
   • Code quality
   • Test coverage

📋 Commands:
   /f5-implement "feature"
   /f5-strict on
   /f5-test unit

✅ Gate Criteria:
   • Code complete
   • Review passed
```

## Arguments

$ARGUMENTS - Can be:
- Empty: Show contextual status
- --quickstart: 5-minute guide
- --next: Single next action
- --resume: Resume session
- --stuck: Troubleshooting
- "text": Task-specific help
- topic: Topic reference (gates, workflow, commands, agents, skills, modes)

Process $ARGUMENTS to determine response type and provide appropriate help.
