# CLI Commands - F5 Framework v1.2.0

## Quick Reference

| Command | Description |
|---------|-------------|
| `f5 init` | Initialize F5 project |
| `f5 doctor` | Check installation health |
| `f5 status` | Show workflow status |
| `f5 jira` | Jira integration commands |
| `f5 gate` | Check quality gates |
| `f5 module` | Manage domain modules |
| `f5 agent` | Manage AI agents |

## Project Commands

### f5 init

Initialize F5 project. Smart detection for existing vs new projects.

```bash
# Existing project (current directory)
f5 init
f5 init .

# New project (creates folder)
f5 init my-project
```

Options:
- `--here` - Force init in current directory
- `-a, --architecture <type>` - Architecture pattern
- `-s, --scale <level>` - Scale template
- `-d, --domain <name>` - Business domain
- `--no-git` - Skip git initialization

See [Init Command](./init.md) for details.

### f5 doctor

Check F5 Framework health status.

```bash
f5 doctor
```

Output:
```
🏥 F5 Health Check
  ✓ F5 CLI              v1.2.0
  ✓ Slash Commands      25 installed
  ✓ Agents              20 loaded
  ✓ MCP Servers         3 active
  ✓ Project Config      Found
  ✓ CLAUDE.md           Found

📊 Health: 100% (6/6)
```

### f5 status

Show current workflow status.

```bash
f5 status
f5 status --json
```

## Jira Commands

### f5 jira setup

Interactive Jira configuration.

```bash
f5 jira setup
```

Creates:
- `.f5/integrations.json` - Connection config
- `.f5/input/` - Put Excel/CSV files here
- `.f5/issues/` - Converted issues
- `.f5/sync/` - Sync state tracking

### f5 jira convert

Convert Excel/CSV files to F5 issues format.

```bash
f5 jira convert              # Auto-convert new/changed files
f5 jira convert --all        # Convert all unconverted files
f5 jira convert --force      # Re-convert even if already done
f5 jira convert file.xlsx    # Convert specific file
```

Features:
- Auto-detects files in `.f5/input/`
- Tracks which files are converted
- Detects changed files (hash comparison)
- Merges all issues into `local.json`

### f5 jira push

Push issues to Jira.

```bash
f5 jira push                 # Push all issues
f5 jira push --dry-run       # Preview without pushing
```

### f5 jira pull

Pull issues from Jira.

```bash
f5 jira pull                 # Pull all project issues
f5 jira pull --dry-run       # Preview without saving
```

### f5 jira status

Show sync status and file tracking.

```bash
f5 jira status
```

Output:
```
📊 F5 Jira Status

Connection:
  URL:      http://jira.example.com
  Project:  MYPROJECT
  Platform: Jira Server

Input Files:
  ✓ requirements.xlsx         45 issues
  ○ new-features.csv          new
  ↻ bugs.xlsx                 changed

  Summary: 1 converted, 1 new, 1 changed
  → Run: f5 jira convert --all

Ready to Push:
  ✓ 45 issues in local.json
```

### f5 jira attachments

List and manage issue attachments.

```bash
f5 jira attachments PROJ-123       # List attachments
f5 jira upload PROJ-123 file.png   # Upload attachment
f5 jira download PROJ-123 --all    # Download all attachments
f5 jira pull-attachments           # Pull attachments from all issues
```

See [Jira Integration](./jira.md) for complete documentation.

## Quality Gates

### f5 gate

Check quality gate status.

```bash
f5 gate D1                   # Check specific gate
f5 gate --all                # Check all gates
```

Gates:
| Gate | Checkpoint |
|------|------------|
| D1 | Research Complete |
| D2 | SRS Approved |
| D3 | Design Approved |
| D4 | Implementation Ready |
| G2 | Code Complete |
| G3 | Tests Pass |
| G4 | Deploy Ready |

## Module Commands

### f5 module

Manage business domain modules.

```bash
f5 module list               # List all modules
f5 module show fintech       # Show module details
```

## Agent Commands

### f5 agent

Manage AI agents.

```bash
f5 agent list                # List all agents
f5 agent show <name>         # Show agent details
f5 agent activate <name>     # Activate agent
```

## MCP Commands

### f5 mcp

Manage MCP servers.

```bash
f5 mcp list                  # List available servers
f5 mcp install --all         # Install all servers
f5 mcp status                # Show server status
```

## Document Commands

### f5 doc

Document pipeline commands.

```bash
f5 doc import file.xlsx      # Import requirements
f5 doc list                  # List versions
f5 doc diff v1.0 v2.0        # Compare versions
f5 doc export v1.0           # Export to Markdown
```

See [Document Pipeline](../document-pipeline.md) for details.

## Strict Implementation Protocol

### f5 strict

Manage strict implementation sessions.

```bash
f5 strict start req.md       # Start session
f5 strict checklist          # View checklist
f5 strict approve            # Approve pre-flight
f5 strict mark REQ-001 done  # Mark requirement done
f5 strict validate           # Validate coverage
f5 strict end                # End session
```

See [Strict Implementation Rules](../guides/strict-mode.md) for details.
