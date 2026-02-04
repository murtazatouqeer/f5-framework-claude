---
description: Context and session management - save, restore, optimize
argument-hint: [status|save|restore|list|checkpoint|optimize|analyze|clear|files]
---

# /f5-ctx - Unified Context & Session Management

**Consolidated command** that replaces:
- `/f5-checkpoint` → `/f5-ctx checkpoint`
- `/f5-context` → `/f5-ctx` (context operations)
- `/f5-session` → `/f5-ctx` (session operations)

## ARGUMENTS
$ARGUMENTS

## SUBCOMMANDS

| Command | Description |
|---------|-------------|
| `status` | Show session and context status (default) |
| `save [name]` | Save current session state |
| `restore [id]` | Restore previous session |
| `list` | List saved sessions/checkpoints |
| `checkpoint <name>` | Create named checkpoint |
| `optimize` | Optimize context usage |
| `analyze` | Analyze context composition |
| `clear` | Clear context (with checkpoint) |
| `files` | Manage file context |
| `clean` | Remove old checkpoints |

---

## ACTION: STATUS (default)

### `/f5-ctx` or `/f5-ctx status`

Display comprehensive session and context status.

```markdown
## 📊 Session & Context Status

### Current Session
| Field | Value |
|-------|-------|
| Session ID | sess_[timestamp] |
| Started | [datetime] |
| Duration | [minutes] |
| Last Save | [time ago] |

### State
| Component | Value |
|-----------|-------|
| Gate | [current gate] |
| Persona | [active persona] |
| Mode | [current mode] |
| Skills | [loaded skills count] |

### Context Usage
| Component | Tokens | % |
|-----------|--------|---|
| system | ~8k | 6% |
| project | ~3k | 2% |
| conversation | ~40k | 31% |
| files | ~15k | 12% |
| tools | ~5k | 4% |
| **Total** | **~71k** | **55%** |

### Recent Checkpoints
| # | Name | Created |
|---|------|---------|
| 1 | [name] | [time ago] |

**Quick Commands:**
- `/f5-ctx save` - Save session
- `/f5-ctx checkpoint "name"` - Create checkpoint
- `/f5-ctx optimize` - Optimize context
```

---

## ACTION: SAVE

### `/f5-ctx save [name]`

Save current session state.

**Options:**
- `name` - Optional name for the save (default: auto timestamp)
- `--description "<desc>"` - Add description
- `--tag <tag>` - Tag for categorization
- `--auto` - Auto-save without confirmation

**Saved Contents:**
| Component | Description |
|-----------|-------------|
| `gate_progress` | Current quality gate status |
| `current_tasks` | Active TodoWrite items |
| `memory_state` | Session memory snapshot |
| `context_files` | Recently accessed files |
| `decisions` | Architectural decisions |
| `persona_mode` | Active persona and mode |

---

## ACTION: RESTORE

### `/f5-ctx restore [id]`

Restore session from save/checkpoint.

**Options:**
- `id` - Session/checkpoint ID (default: most recent)
- `--preview` - Preview contents without restoring
- `--merge` - Merge with current context

---

## ACTION: LIST

### `/f5-ctx list`

List saved sessions and checkpoints.

**Options:**
- `--limit <n>` - Maximum items to show (default: 10)
- `--tag <tag>` - Filter by tag
- `--sessions` - Show only sessions
- `--checkpoints` - Show only checkpoints

---

## ACTION: CHECKPOINT

### `/f5-ctx checkpoint <name>`

Create named checkpoint (milestone marker).

**Options:**
- `name` - Required checkpoint name
- `--description "<desc>"` - Add description
- `--tag <tag>` - Tag (e.g., milestone, backup, feature)

**Example:**
```bash
/f5-ctx checkpoint pre-refactor --description "Before auth rewrite" --tag milestone
```

---

## ACTION: OPTIMIZE

### `/f5-ctx optimize`

Optimize context by compressing or archiving old content.

**Options:**
- `--aggressive` - Maximum compression
- `--keep-recent <n>` - Keep N most recent items uncompressed (default: 10)

**Strategy:**
1. Summarize old conversation chunks
2. Archive unused file contents
3. Compress tool call history
4. Report space recovered

---

## ACTION: ANALYZE

### `/f5-ctx analyze`

Analyze context composition and usage patterns.

**Options:**
- `--recommendations` - Include optimization recommendations
- `--detailed` - Show detailed breakdown

**Output:**
```markdown
## 🔍 Context Analysis

### Composition
| Category | Tokens | % | Notes |
|----------|--------|---|-------|
| System | 8,500 | 7% | Normal |
| Project | 3,200 | 2% | Normal |
| Conversation | 45,000 | 35% | High |
| Files | 18,000 | 14% | Normal |
| Tools | 6,500 | 5% | Normal |

### Recommendations
- Consider optimizing conversation (35% usage)
- Archive files not accessed in 30+ minutes
- Checkpoint before major operations
```

---

## ACTION: CLEAR

### `/f5-ctx clear`

Clear context with optional checkpoint.

**Options:**
- `--no-checkpoint` - Don't save checkpoint before clearing
- `--keep-system` - Keep system instructions and project context
- `--confirm` - Skip confirmation prompt

---

## ACTION: FILES

### `/f5-ctx files`

Manage file context.

**Options:**
- `--list` - List files in context
- `--prune` - Remove stale file references
- `--add <path>` - Add file to context
- `--remove <path>` - Remove file from context

---

## ACTION: CLEAN

### `/f5-ctx clean`

Remove old checkpoints and sessions.

**Options:**
- `--keep <n>` - Keep N recent checkpoints (default: 5)
- `--older-than <days>` - Delete older than N days
- `--force` - Skip confirmation

---

## EXAMPLES

```bash
# Check status
/f5-ctx

# Save session with name
/f5-ctx save after-auth-implementation

# Create milestone checkpoint
/f5-ctx checkpoint v1.0-complete --tag milestone

# Restore most recent
/f5-ctx restore

# Optimize when context is high
/f5-ctx optimize --keep-recent 5

# Analyze context composition
/f5-ctx analyze --recommendations

# List all saves
/f5-ctx list --limit 20

# Clean old checkpoints
/f5-ctx clean --keep 3
```

---

## STORAGE

All session data stored in `.f5/sessions/`:

```
.f5/sessions/
├── current.yaml          # Current session state
├── sessions/             # Saved sessions
│   └── sess_[timestamp].yaml
└── checkpoints/          # Named checkpoints
    └── [name].yaml
```
