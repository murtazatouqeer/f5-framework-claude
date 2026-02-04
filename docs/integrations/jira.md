# F5 Jira Integration Guide

This guide explains how to use F5 Framework's Jira integration with Claude Desktop slash commands and CLI for bidirectional issue synchronization.

## Overview

F5 Framework provides two-way integration with Jira:

- **Convert**: Excel/CSV files to Jira-ready format using MCP Excel
- **Sync**: Push/Pull issues between local F5 project and Jira server
- **Track**: Monitor conversion and sync state with comprehensive status

### Architecture

```
Excel/CSV Files → [MCP Excel] → F5 JSON → [CLI] → Jira Server
     ↑                                         ↓
     └──────────── Slash Commands ─────────────┘
                   (Prepare Data)
                        +
                   CLI Commands
                   (Execute API)
```

### Two-Layer Design

| Layer | Purpose | Environment |
|-------|---------|-------------|
| **Slash Commands** | Prepare, preview, analyze data | Claude Desktop |
| **CLI Commands** | Execute Jira API calls | Terminal |

This separation ensures:
- Safe data preparation and preview
- Explicit API execution control
- Full backward compatibility with existing CLI

## Prerequisites

- F5 Framework v1.2.0+ installed
- Claude Desktop with MCP Excel server (recommended)
- Jira Cloud or Jira Server account with API access
- API token (Cloud) or Personal Access Token (Server)

## Quick Start

### 1. Setup Jira Connection

```bash
# In terminal
f5 jira setup
```

This creates `.f5/integrations.json` with your Jira configuration.

### 2. Prepare Input Files

Place Excel/CSV files in `.f5/input/`:

```bash
cp issues.xlsx .f5/input/
```

### 3. Convert to Jira Format

In Claude Desktop:

```
/f5-jira-convert issues.xlsx
```

### 4. Preview and Sync

```
/f5-jira-sync --dry-run
```

### 5. Push to Jira

```bash
# In terminal
f5 jira push
```

## Slash Commands Reference

### /f5-jira-convert

Convert Excel/CSV files to Jira-ready format.

| Usage | Description |
|-------|-------------|
| `/f5-jira-convert <filename>` | Convert specific file |
| `/f5-jira-convert --all` | Convert all files in .f5/input/ |
| `/f5-jira-convert <file> --dry-run` | Preview without saving |
| `/f5-jira-convert <file> --force` | Re-convert even if unchanged |

**Output Files:**
- `.f5/csv/{filename}_jira.csv` - Jira-importable CSV
- `.f5/issues/{filename}.json` - F5 internal JSON
- `.f5/issues/local.json` - Merged issues for sync

**Example:**
```
/f5-jira-convert 問題管理表.xlsx

## Output:
📊 Conversion Complete

File: 問題管理表.xlsx
Sheet: 動作確認一覧
Format: 問題管理表 (Issue Tracking)

Statistics:
| Category | Count |
|----------|-------|
| Total Rows | 150 |
| Converted | 45 |
| Skipped (正常) | 105 |

By Issue Type:
| Type | Count |
|------|-------|
| Bug | 25 |
| Improvement | 15 |
| Task | 5 |
```

### /f5-jira-sync

Sync issues between local F5 project and Jira.

| Usage | Description |
|-------|-------------|
| `/f5-jira-sync --dry-run` | Preview sync changes |
| `/f5-jira-sync --push` | Prepare push to Jira |
| `/f5-jira-sync --pull` | Prepare pull from Jira |
| `/f5-jira-sync --conflict <strategy>` | Set conflict resolution |

**Conflict Strategies:**
- `local-wins` - Keep local changes
- `remote-wins` - Keep Jira changes
- `newest-wins` - Use newest timestamp (default)

**Important:** This command prepares data for sync. Execute actual sync with:
```bash
f5 jira push   # Push to Jira
f5 jira pull   # Pull from Jira
```

### /f5-jira-status

Display comprehensive status of Jira integration.

| Usage | Description |
|-------|-------------|
| `/f5-jira-status` | Full status overview |
| `/f5-jira-status --verbose` | Detailed file and mapping info |
| `/f5-jira-status --json` | Output as JSON |
| `/f5-jira-status --mappings` | Show all local↔remote mappings |
| `/f5-jira-status diagnose` | Full diagnostic check |

**Example Output:**
```
📊 F5 Jira Status
════════════════════════════════════════

🔧 Configuration
────────────────────────────────────────
  Jira URL:     https://company.atlassian.net
  Project:      PROJECT
  Auth:         ✓ Configured (Basic)

📁 Input Files (.f5/input/)
────────────────────────────────────────
  ○ file1.xlsx                 new
  ✓ file2.xlsx                 45 issues
  ↻ file3.xlsx                 changed

  Summary: 1 new, 1 converted, 1 changed

📋 Local Issues (.f5/issues/local.json)
────────────────────────────────────────
  Total:    87 issues
  Updated:  2024-01-15 10:30 JST

🔄 Sync State
────────────────────────────────────────
  Last Sync:  2024-01-14 15:00 JST
  Tracked:    45 issues
  Pending:    5 new issues

💡 Recommended Actions
────────────────────────────────────────
  /f5-jira-convert --all      # Convert new files
  /f5-jira-sync --dry-run     # Preview sync
  f5 jira push                # Push to Jira
```

## Japanese Excel Support (問題管理表)

F5 Framework provides comprehensive support for Japanese issue tracking Excel files.

### Auto-Detection

The framework automatically detects Japanese formats:

| Format | Sheet Patterns | Header Row |
|--------|---------------|------------|
| 問題管理表 | 動作確認一覧, 問題管理 | 3 |
| Test Results | テスト結果, Test Results | 1 |
| Bug Report | Bugs, Bug Report | 1 |

### Column Mappings

| Japanese Column | English Column | Jira Field |
|-----------------|---------------|------------|
| No, No. | ID | External ID |
| 問題内容 | Issue Content | Summary |
| 判定, 判定結果 | Result, Type | Issue Type |
| 優先度 | Priority | Priority |
| 状況, 状態 | Status | Status |
| 担当者 | Assignee | Assignee |
| カテゴリ | Category | Labels |

### Issue Type Mappings

| Japanese | Jira Type |
|----------|-----------|
| 異常, バグ, 不具合 | Bug |
| 改善, 改善要望 | Improvement |
| 確認, タスク | Task |
| 機能 | Story |
| 正常 | (Skipped by default) |

### Priority Mappings

| Japanese | Jira Priority |
|----------|---------------|
| 緊急, 最高 | Highest |
| 高 | High |
| 中, 普通 | Medium |
| 低 | Low |
| 最低 | Lowest |

### Status Mappings

| Japanese | Jira Status |
|----------|-------------|
| 未着手, 新規 | To Do |
| 対応中, 作業中 | In Progress |
| 完了, 解決済み | Done |
| 保留 | On Hold |

## Workflow Examples

### Basic Workflow

```
┌─────────────────────────────────────────┐
│  Claude Desktop                         │
├─────────────────────────────────────────┤
│  1. /f5-jira-status                     │
│     → Check current state               │
│                                         │
│  2. /f5-jira-convert issues.xlsx        │
│     → Convert Excel to JSON/CSV         │
│                                         │
│  3. /f5-jira-sync --dry-run             │
│     → Preview what will be synced       │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  Terminal                               │
├─────────────────────────────────────────┤
│  4. f5 jira push                        │
│     → Execute push to Jira              │
│                                         │
│  5. f5 jira status                      │
│     → Verify sync completed             │
└─────────────────────────────────────────┘
```

### Multiple Files Workflow

```
# 1. Copy files to input directory
cp requirements.xlsx bugs.xlsx features.csv .f5/input/

# 2. In Claude Desktop
/f5-jira-status                    # Check file status
/f5-jira-convert --all             # Convert all files
/f5-jira-sync --dry-run            # Preview changes

# 3. In Terminal
f5 jira push                       # Push to Jira
```

### Bidirectional Sync Workflow

```
# 1. Pull remote changes first
f5 jira pull

# 2. Check for conflicts
/f5-jira-sync --dry-run

# 3. Resolve conflicts if any
/f5-jira-sync --conflict newest-wins

# 4. Push local changes
f5 jira push
```

### Japanese Issue Tracking Workflow (問題管理表)

```
# 1. Analyze file structure
/f5-jira-convert 問題管理表.xlsx --dry-run

# 2. Convert with image extraction
/f5-jira-convert 問題管理表.xlsx

# 3. Preview sync
/f5-jira-sync --dry-run

# 4. Push issues
f5 jira push

# 5. Upload attachments
f5 jira push-attachments --all
```

## File Tracking System

### Conversion Tracking

F5 tracks file conversion status in `.f5/sync/conversion-tracking.json`:

| Symbol | Status | Meaning |
|--------|--------|---------|
| ○ | new | File not yet converted |
| ✓ | converted | File converted, up to date |
| ↻ | changed | File modified since conversion |

### Sync State Management

Sync state is stored in `.f5/sync/jira-sync.json`:

```json
{
  "lastSyncAt": "2024-01-15T10:30:00Z",
  "direction": "push",
  "project": "PROJECT",
  "states": {
    "local-ISSUE-001": {
      "localId": "local-ISSUE-001",
      "remoteId": "PROJECT-123",
      "localHash": "abc123",
      "remoteHash": "def456",
      "status": "synced"
    }
  }
}
```

### Change Detection

Changes are detected using content hash comparison:

| Condition | Category | Action |
|-----------|----------|--------|
| In local, not in sync | NEW | Create on Jira |
| Local hash changed | UPDATED | Update on Jira |
| Both hashes changed | CONFLICT | Requires resolution |
| Hashes unchanged | SYNCED | Skip |

## Configuration

### Jira Configuration File

`.f5/integrations.json`:

```json
{
  "jira": {
    "baseUrl": "https://company.atlassian.net",
    "apiVersion": "3",
    "auth": {
      "type": "basic",
      "email": "user@company.com",
      "apiToken": "your-api-token"
    },
    "project": "PROJECT"
  },
  "sync": {
    "enabled": true,
    "direction": "bidirectional",
    "conflictStrategy": "newest-wins"
  }
}
```

### Platform Detection

| Platform | API Version | Auth Type |
|----------|-------------|-----------|
| Jira Cloud | v3 (ADF) | Basic (email + API token) |
| Jira Server | v2 | PAT (Personal Access Token) |

### Getting API Credentials

**Jira Cloud:**
1. Go to https://id.atlassian.com/manage/api-tokens
2. Create API token
3. Use email + token for authentication

**Jira Server:**
1. Go to Profile → Personal Access Tokens
2. Create token with required permissions
3. Use username + PAT for authentication

## Custom Mappings

### Creating Custom Schema

Create `.f5/schemas/excel-import-jira.yaml`:

```yaml
schema_version: "1.0"
name: "custom-jira-mapping"

source:
  main_sheet: "Issues"
  header_row: 1

column_mapping:
  - excel: "ID"
    jira: "External ID"
    transform: "prefix:PROJ-"
    required: true

  - excel: "Title"
    jira: "Summary"
    required: true
    max_length: 255

  - excel: "Type"
    jira: "Issue Type"
    value_mapping:
      "バグ": "Bug"
      "機能": "Story"
      "タスク": "Task"
    default: "Task"

  - excel: "Priority"
    jira: "Priority"
    value_mapping:
      "High": "High"
      "高": "High"
      "Medium": "Medium"
      "中": "Medium"
      "Low": "Low"
      "低": "Low"
    default: "Medium"

validation:
  skip_empty_rows: true
  required_fields: ["Summary"]
```

### Using Custom Schema

```
/f5-jira-convert issues.xlsx --schema custom-jira-mapping
```

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| "Jira not configured" | Run `f5 jira setup` in terminal |
| "No local issues found" | Run `/f5-jira-convert` first |
| "MCP Excel not available" | Use CLI: `f5 jira convert` |
| "Authentication failed" | Check API token in integrations.json |
| "Low confidence detection" | Use `--sheet` and `--header-row` flags |

### Diagnostic Check

```
/f5-jira-status diagnose
```

This checks:
- Configuration file exists
- Connection to Jira works
- Input files are accessible
- Local issues are valid
- Sync state is consistent

### Reset Sync State

If sync state becomes corrupted:

```bash
# WARNING: This will clear all mappings
rm .f5/sync/jira-sync.json

# Next sync will create NEW issues on Jira
# This may cause duplicates!
```

## Best Practices

### Before Converting

1. **Analyze first**: Use `--dry-run` to preview
2. **Check format**: Verify Japanese columns are detected
3. **Backup files**: Keep original Excel files

### Before Syncing

1. **Preview changes**: Always use `--dry-run` first
2. **Check conflicts**: Resolve before pushing
3. **Small batches**: Use `--limit` for large datasets

### General Tips

1. **Use CLI for API calls**: Slash commands prepare data only
2. **Check status regularly**: Run `/f5-jira-status` before operations
3. **Keep files organized**: Use `.f5/input/` directory
4. **Document schemas**: Save custom mappings in `.f5/schemas/`

## CLI Commands Reference

For complete CLI documentation, see [CLI Jira Commands](./cli/jira.md).

Quick reference:

| CLI Command | Description |
|-------------|-------------|
| `f5 jira setup` | Interactive setup wizard |
| `f5 jira convert` | Convert Excel files |
| `f5 jira push` | Push to Jira |
| `f5 jira pull` | Pull from Jira |
| `f5 jira sync` | Bidirectional sync |
| `f5 jira status` | Show status |
| `f5 jira test` | Test connection |
| `f5 jira push-attachments` | Upload images |

## Integration with F5 Workflow

### Quality Gates

Jira integration works with F5 quality gates:

```
D1 (Research Complete)
  ↓
/f5-jira-convert requirements.xlsx
  ↓
D2 (SRS Approved)
  ↓
/f5-jira-sync --push
f5 jira push
  ↓
G2 (Implementation Ready)
  ↓
f5 jira pull  # Get updates
  ↓
G3 (Testing Complete)
```

### Memory Integration

Jira sync state is tracked in F5 memory:
- `.f5/sync/jira-sync.json` - Issue mappings
- `.f5/sync/conversion-tracking.json` - File tracking
- `.f5/issues/local.json` - Local issues

## Additional Resources

- [CLI Jira Commands](./cli/jira.md)
- [Excel Import Schema](./excel-schema.md)
- [MCP Excel Integration](./mcp-excel-integration.md)
- [Quality Gates Guide](../guides/quality-gates.md)

---

*Last updated: 2024-01*
*F5 Framework v1.2.0*
