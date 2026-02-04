---
description: Team management, sessions, handoffs, and multi-agent collaboration
argument-hint: <list|session|agents|handoff|...> [options]
---

# /f5-team - Unified Team & Collaboration Command

**Consolidated command** that replaces:
- `/f5-collab` → `/f5-team session`
- `/f5-collaborate` → `/f5-team agents`
- `/f5-handoff` → `/f5-team handoff`

## ARGUMENTS
$ARGUMENTS

## MODE DETECTION

| Pattern | Mode | Description |
|---------|------|-------------|
| `session <action>` | SESSION | Collaboration session management |
| `agents <pattern>` | AGENTS | Multi-agent collaboration |
| `handoff <action>` | HANDOFF | Task handoff between members |
| `<other>` (default) | TEAM | Team member management |

---

## MODE: SESSION (from /f5-collab)

### `/f5-team session <action>`

Manage collaboration sessions for team development.

| Action | Description |
|--------|-------------|
| `start` | Start new collaboration session |
| `join <id>` | Join existing session |
| `leave` | Leave current session |
| `end` | End session (owner only) |
| `list` | List active sessions |
| `status` | Show current session status |
| `share` | Share context with participants |
| `sync` | Sync with latest session context |
| `checkpoint` | Create session checkpoint |
| `decision <text>` | Record a team decision |
| `blocker <text>` | Report a blocker |
| `update <text>` | Send status update |

**Examples:**
```bash
/f5-team session start --project my-project
/f5-team session join sess_123
/f5-team session share
/f5-team session decision "Using PostgreSQL for database"
```

---

## MODE: AGENTS (from /f5-collaborate)

### `/f5-team agents <pattern> [agents] "task"`

Execute multiple agents using collaboration patterns.

| Pattern | Description |
|---------|-------------|
| `--chain` | Execute agents sequentially |
| `--parallel` | Execute agents simultaneously |
| `--consult` | Get recommendations from multiple agents |
| `--review` | Add review steps between agents |

**Auto-Chains:**
| Keywords | Agents |
|----------|--------|
| "implement feature" | architect → api → code → test → review |
| "fix bug" | debug → code → test → review |
| "security audit" | security → review → code → test |
| "optimize" | perf → refactor → test → review |

**Examples:**
```bash
/f5-team agents --chain "implement user authentication"
/f5-team agents --parallel @f5:frontend @f5:backend "dashboard"
/f5-team agents --consult "microservices vs monolith?"
```

---

## MODE: HANDOFF (from /f5-handoff)

### `/f5-team handoff <action>`

Transfer tasks between members with full context preservation.

| Action | Description |
|--------|-------------|
| `create` | Create new handoff |
| `accept <id>` | Accept a pending handoff |
| `reject <id>` | Reject a pending handoff |
| `complete <id>` | Mark handoff as completed |
| `list` | List handoffs (sent/received) |
| `show <id>` | Show handoff details |
| `prepare` | Prepare handoff with current context |
| `restore <id>` | Restore context from handoff |

**Options:**
- `--to <member>` - Target member
- `--req <id>` - Requirement being handed off
- `--checkpoint` - Include current checkpoint
- `--urgent` - Mark as urgent

**Examples:**
```bash
/f5-team handoff create --to junior-a --req REQ-001
/f5-team handoff accept handoff_123
/f5-team handoff list --status pending
```

---

## MODE: TEAM (Default)

Manage team configuration, members, and workload.

## ACTIONS

### Member Management
- `list` - List all team members
- `show <member_id>` - Show member details
- `status <member_id> <availability>` - Update member status
- `add` - Add new team member
- `update <member_id>` - Update member info
- `skills <member_id>` - Manage member skills

### Team Operations
- `stats` - Show team statistics
- `workload` - View workload distribution
- `available` - List available members
- `mentors` - Show mentorship relationships
- `assign` - Assign task to member

### Configuration
- `config` - View team configuration
- `sync` - Sync team from config file
- `export` - Export team data

## OPTIONS
- `--role <role>` - Filter by role
- `--skill <skill>` - Filter by skill
- `--availability <status>` - Filter by availability
- `--project <id>` - Filter by project

## EXECUTION

### STEP 1: Load Team Configuration
```yaml
config_path: .f5/team/shared/team-config.yaml
load:
  - Team name and settings
  - Member list
  - Role hierarchy
  - Permissions
  - Escalation paths
```

### STEP 2: Execute Action

#### LIST MEMBERS
```yaml
mcp_call:
  tool: collab_list_members
  args:
    role: ${role_filter}
    availability: ${availability_filter}

output:
  table:
    - ID
    - Name
    - Role
    - Availability
    - Current Task
    - Skills (top 3)

  grouping:
    - By role (default)
    - By availability
    - By skill
```

#### SHOW MEMBER
```yaml
calls:
  - tool: collab_get_member
    args:
      id: ${member_id}

  - tool: collab_member_stats
    args:
      member_id: ${member_id}

output:
  - Basic Info (name, role, skills)
  - Availability & Current Task
  - Mentor/Mentees
  - Statistics:
    - Total tasks
    - Completed tasks
    - Handoffs sent/received
    - Knowledge contributed
  - Recent Activity (last 10)
```

#### UPDATE STATUS
```yaml
mcp_call:
  tool: collab_update_status
  args:
    member_id: ${member_id}
    availability: ${availability}
    current_task: ${task_id}

valid_statuses:
  - available: Ready for new tasks
  - busy: Working on task
  - away: Temporarily unavailable
  - offline: Not working

auto_triggers:
  busy: When accepting handoff or starting task
  available: When completing task
```

#### ADD MEMBER
```yaml
prompts:
  - id: Unique member ID (e.g., "junior-e")
  - name: Display name
  - role: [senior|middle|junior|fresher|tester|lead|pm]
  - skills: Comma-separated skills
  - mentor_id: (for junior/fresher) Mentor's ID

mcp_call:
  tool: collab_add_member
  args:
    id: ${id}
    name: ${name}
    role: ${role}
    skills: ${skills_array}
    mentor_id: ${mentor_id}

post_actions:
  - Update team.yaml config
  - Notify mentor (if assigned)
  - Log activity
```

#### TEAM STATS
```yaml
mcp_call:
  tool: collab_team_stats
  args:
    project_id: ${project_id}

output:
  overview:
    - Total Members
    - By Role breakdown
    - By Availability breakdown

  activity:
    - Active Sessions
    - Pending Handoffs
    - Active Conflicts

  metrics:
    - Tasks completed (week)
    - Average completion time
    - Handoff success rate
    - Knowledge items added
```

#### WORKLOAD VIEW
```yaml
collect:
  for_each_member:
    - Get assignments
    - Count pending handoffs
    - Check availability

calculate:
  workload_score:
    - assigned_tasks * weight
    - pending_handoffs * weight
    - meetings/reviews * weight

output:
  table:
    - Member
    - Role
    - Assigned Tasks
    - Pending Handoffs
    - Workload Score
    - Status

  recommendations:
    - Overloaded members
    - Available capacity
    - Suggested redistribution
```

#### AVAILABLE MEMBERS
```yaml
mcp_call:
  tool: collab_list_members
  args:
    availability: available

enrich:
  for_each:
    - Get current workload
    - Get skills
    - Get recent activity

output:
  table:
    - Member
    - Role
    - Skills
    - Workload
    - Last Task

  filter_options:
    - By role
    - By skill
    - By experience level
```

#### MENTORSHIP VIEW
```yaml
source: team.yaml config

build_tree:
  for_each_mentor:
    - List mentees
    - Show relationship status
    - Show interaction stats

output:
  tree_view:
    senior-a
    ├── middle-dev
    │   └── junior-a
    └── junior-a

    senior-b
    ├── junior-b
    └── junior-c

    senior-c
    ├── junior-d
    └── fresher-dev

  stats:
    - Handoffs between mentor-mentee
    - Review requests
    - Escalations
```

#### ASSIGN TASK
```yaml
workflow:
  1. Select requirement
  2. Find suitable member:
     - Match skills
     - Check availability
     - Consider workload
     - Respect role hierarchy

  3. Create assignment:
     mcp_call:
       tool: collab_assign_task
       args:
         project_id: ${project_id}
         requirement_id: ${requirement_id}
         assignee: ${member_id}
         assigned_by: ${current_member}
         priority: ${priority}
         estimated_hours: ${estimate}

  4. Notify:
     - Assignee
     - Mentor (if junior/fresher)
     - Session participants

smart_assign:
  factors:
    - skill_match: 40%
    - availability: 25%
    - workload: 20%
    - experience: 15%

  algorithm:
    1. Filter by required skills
    2. Filter by availability
    3. Score remaining by workload
    4. Prefer mentee for learning opportunities
```

### STEP 3: Team Configuration

#### SYNC FROM CONFIG
```yaml
source: .f5/team/shared/team-config.yaml

actions:
  1. Load config file
  2. Compare with database
  3. Add new members
  4. Update changed members
  5. Report differences

output:
  - Members added
  - Members updated
  - Members unchanged
  - Config validation warnings
```

#### EXPORT TEAM DATA
```yaml
formats:
  - yaml: team.yaml format
  - json: Full export with stats
  - csv: Simple member list

includes:
  - Member info
  - Current status
  - Assignment history
  - Activity summary
```

## OUTPUT FORMAT

### Team List
```
╔══════════════════════════════════════════════════════════════════╗
║  👥 TEAM MEMBERS                                                 ║
╚══════════════════════════════════════════════════════════════════╝

📊 Summary: 11 members (3 senior, 1 middle, 4 junior, 1 fresher, 2 tester)

👔 SENIORS (3)
┌─────────────┬────────────┬─────────────┬──────────────────────────┐
│ ID          │ Name       │ Status      │ Skills                   │
├─────────────┼────────────┼─────────────┼──────────────────────────┤
│ senior-a    │ Senior A   │ 🟢 available│ backend, architecture    │
│ senior-b    │ Senior B   │ 🟡 busy     │ frontend, react          │
│ senior-c    │ Senior C   │ 🟢 available│ fullstack, devops        │
└─────────────┴────────────┴─────────────┴──────────────────────────┘

👨‍💼 MIDDLE (1)
┌─────────────┬────────────┬─────────────┬──────────────────────────┐
│ middle-dev  │ Middle Dev │ 🟡 busy     │ backend, frontend        │
└─────────────┴────────────┴─────────────┴──────────────────────────┘

👨‍💻 JUNIORS (4)
┌─────────────┬────────────┬─────────────┬──────────────────────────┐
│ junior-a    │ Junior A   │ 🟢 available│ backend, java            │
│ junior-b    │ Junior B   │ 🟡 busy     │ frontend, react          │
│ junior-c    │ Junior C   │ 🔴 away     │ frontend, css            │
│ junior-d    │ Junior D   │ 🟢 available│ backend, database        │
└─────────────┴────────────┴─────────────┴──────────────────────────┘

🌱 FRESHERS (1)
┌─────────────┬────────────┬─────────────┬──────────────────────────┐
│ fresher-dev │ Fresher Dev│ 🟢 available│ basic-programming        │
└─────────────┴────────────┴─────────────┴──────────────────────────┘

🧪 TESTERS (2)
┌─────────────┬────────────┬─────────────┬──────────────────────────┐
│ tester-a    │ Tester A   │ 🟢 available│ manual-testing           │
│ tester-b    │ Tester B   │ 🟡 busy     │ automation, playwright   │
└─────────────┴────────────┴─────────────┴──────────────────────────┘
```

### Member Details
```
╔══════════════════════════════════════════════════════════════════╗
║  👤 MEMBER: senior-a                                             ║
╚══════════════════════════════════════════════════════════════════╝

📋 Basic Info:
  • Name: Senior A
  • Role: Senior Developer
  • Status: 🟢 Available

🛠️ Skills:
  backend, architecture, review, java, spring

👥 Mentorship:
  • Mentoring: middle-dev, junior-a

📊 Statistics:
  ┌─────────────────────┬───────┐
  │ Total Tasks         │ 45    │
  │ Completed Tasks     │ 42    │
  │ Handoffs Sent       │ 12    │
  │ Handoffs Received   │ 3     │
  │ Knowledge Items     │ 8     │
  │ Reviews Done        │ 28    │
  └─────────────────────┴───────┘

📈 Recent Activity:
  • 2h ago - Completed REQ-015
  • 4h ago - Reviewed junior-a's PR
  • Yesterday - Created handoff to junior-a
  • Yesterday - Added knowledge: "API Design Conventions"
```

### Workload Distribution
```
╔══════════════════════════════════════════════════════════════════╗
║  📊 TEAM WORKLOAD                                                ║
╚══════════════════════════════════════════════════════════════════╝

┌─────────────┬────────┬───────────┬──────────────┬──────────┬────────┐
│ Member      │ Role   │ Tasks     │ Handoffs     │ Workload │ Status │
├─────────────┼────────┼───────────┼──────────────┼──────────┼────────┤
│ senior-b    │ senior │ 3         │ 1 pending    │ ████████ │ 80%    │
│ middle-dev  │ middle │ 2         │ 0            │ ██████   │ 60%    │
│ junior-b    │ junior │ 2         │ 1 pending    │ ███████  │ 70%    │
│ tester-b    │ tester │ 1         │ 0            │ ████     │ 40%    │
├─────────────┼────────┼───────────┼──────────────┼──────────┼────────┤
│ senior-a    │ senior │ 0         │ 0            │          │ 0%     │
│ senior-c    │ senior │ 1         │ 0            │ ██       │ 20%    │
│ junior-a    │ junior │ 1         │ 0            │ ███      │ 30%    │
│ junior-d    │ junior │ 0         │ 1 pending    │ █        │ 10%    │
│ fresher-dev │ fresher│ 0         │ 0            │          │ 0%     │
│ tester-a    │ tester │ 0         │ 0            │          │ 0%     │
└─────────────┴────────┴───────────┴──────────────┴──────────┴────────┘

⚠️ Recommendations:
  • senior-b is overloaded - consider redistribution
  • junior-d has pending handoff - needs attention
  • fresher-dev has capacity - assign learning task
  • tester-a is available - can start test planning
```

### Team Stats
```
╔══════════════════════════════════════════════════════════════════╗
║  📈 TEAM STATISTICS                                              ║
╚══════════════════════════════════════════════════════════════════╝

👥 Team Composition:
  • Total: 11 members
  • Seniors: 3 (27%)
  • Middle: 1 (9%)
  • Juniors: 4 (36%)
  • Freshers: 1 (9%)
  • Testers: 2 (18%)

🟢 Availability:
  • Available: 6 (55%)
  • Busy: 4 (36%)
  • Away: 1 (9%)
  • Offline: 0 (0%)

📊 Current Activity:
  • Active Sessions: 2
  • Pending Handoffs: 3
  • Active Conflicts: 0
  • Open Assignments: 8

📈 This Week:
  • Tasks Completed: 12
  • Handoffs Completed: 5
  • Knowledge Items Added: 4
  • Reviews Done: 15
  • Gates Passed: 3

🎯 Performance:
  • Avg Task Completion: 2.3 days
  • Handoff Accept Rate: 92%
  • Review Turnaround: 4 hours
```

## MCP TOOLS USED
- `collab_add_member`
- `collab_get_member`
- `collab_list_members`
- `collab_update_status`
- `collab_team_stats`
- `collab_member_stats`
- `collab_assign_task`
- `collab_list_assignments`
- `collab_get_activities`

## PERMISSIONS
```yaml
actions_by_role:
  senior:
    - all actions
  middle:
    - list, show, status (self), stats, workload, available, mentors
    - assign (to juniors)
  junior:
    - list, show, status (self), available, mentors
  fresher:
    - list, show, status (self), mentors
  tester:
    - list, show, status (self), available
  lead:
    - all actions
  pm:
    - all actions
```

## EXAMPLES

```bash
# List all team members
/f5-team list

# List available members
/f5-team available

# List members by role
/f5-team list --role junior

# List members by skill
/f5-team list --skill backend

# Show member details
/f5-team show senior-a

# Update own status
/f5-team status me available

# Update member status (if permitted)
/f5-team status junior-a busy

# View team stats
/f5-team stats

# View workload distribution
/f5-team workload

# View mentorship tree
/f5-team mentors

# Assign task to member
/f5-team assign --to junior-a --req REQ-001 --priority high

# Add new team member
/f5-team add

# Sync from config file
/f5-team sync

# Export team data
/f5-team export --format yaml
```
