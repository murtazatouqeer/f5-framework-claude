# f5 jira - Jira Integration

## Overview

The `f5 jira` command provides seamless integration between F5 Framework and Jira. It supports:

- **Jira Cloud** - Using API v3 with ADF (Atlassian Document Format)
- **Jira Server/Data Center** - Using API v2 with Personal Access Token (PAT)

## Quick Start

```bash
# 1. Setup connection (interactive)
f5 jira setup

# 2. Put Excel/CSV files in .f5/input/

# 3. Convert to issues
f5 jira convert

# 4. Push to Jira
f5 jira push
```

## Folder Structure

After running `f5 jira setup`, the following folders are created:

```
.f5/
├── input/           ← Put your Excel/CSV files here
├── csv/             ← Converted CSV output (auto-generated)
├── issues/          ← F5 JSON format (for sync)
│   ├── local.json   ← Merged issues ready to push
│   └── remote.json  ← Pulled issues from Jira
├── sync/            ← Sync state (auto-generated)
│   ├── jira-sync.json
│   └── conversion-tracking.json
├── attachments/     ← Attachments storage
│   ├── extracted/   ← Images extracted from Excel
│   └── <issueKey>/  ← Downloaded from Jira
└── schemas/         ← Custom schemas (optional)
```

## Commands

### f5 jira setup

Interactive setup wizard for Jira connection.

```bash
f5 jira setup
```

Prompts for:
- Jira URL
- Username/Email
- API Token/Password
- Default Project Key

Auto-detects:
- **Platform**: Jira Cloud vs Jira Server
- **Auth type**: Basic auth (Cloud) vs PAT (Server)
- **API version**: v3 (Cloud with ADF) vs v2 (Server)

### f5 jira config

Configure Jira connection non-interactively.

```bash
# Set configuration
f5 jira config --url https://company.atlassian.net --email user@company.com --token <token> --project MYPROJ

# Show current configuration
f5 jira config --show
```

Options:
| Option | Description |
|--------|-------------|
| `--url <url>` | Jira base URL |
| `--email <email>` | Jira account email/username |
| `--token <token>` | API token or PAT |
| `--project <key>` | Default project key |
| `--auth-type <type>` | Auth type: `basic` or `pat` |
| `--api-version <ver>` | API version: `2` or `3` |
| `--show` | Show current configuration |

### f5 jira convert

Convert Excel/CSV files to F5 issues format.

```bash
# Auto-convert new/changed files
f5 jira convert

# Convert all unconverted files
f5 jira convert --all

# Force re-convert all files
f5 jira convert --force

# Convert specific file
f5 jira convert requirements.xlsx

# Analyze file structure only
f5 jira convert requirements.xlsx --analyze

# Preview without saving
f5 jira convert --dry-run
```

Options:
| Option | Description |
|--------|-------------|
| `--all` | Convert all new/changed files |
| `--force` | Re-convert even if already converted |
| `--analyze` | Analyze file structure only |
| `--dry-run` | Preview without saving |
| `-s, --schema <name>` | Use saved schema |

#### Conversion Tracking

F5 tracks which files have been converted using MD5 hash comparison:

| Status | Icon | Description |
|--------|------|-------------|
| New | ○ | File not yet converted |
| Converted | ✓ | File already converted |
| Changed | ↻ | File modified since last conversion |

Example output:
```
📁 Files in .f5/input/:

  ✓ requirements.xlsx         converted (45 issues)
  ○ new-features.csv          new
  ↻ bugs.xlsx                 changed

  Summary: 1 converted, 1 new, 1 changed
  → Run: f5 jira convert --all
```

### f5 jira push

Push local issues to Jira.

```bash
# Preview what will be pushed
f5 jira push --dry-run

# Push all issues
f5 jira push
```

Options:
| Option | Description |
|--------|-------------|
| `--dry-run` | Preview without pushing |

### f5 jira pull

Pull issues from Jira to local.

```bash
# Preview what will be pulled
f5 jira pull --dry-run

# Pull all project issues
f5 jira pull
```

Options:
| Option | Description |
|--------|-------------|
| `--dry-run` | Preview without saving |

### f5 jira status

Show sync status and file tracking.

```bash
f5 jira status
```

Example output:
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
  Updated: 12/2/2024, 10:30:00 AM

Jira Sync:
  Last sync: 12/2/2024, 10:25:00 AM
  Tracked:   45 issues
  Conflicts: 0
```

### f5 jira test

Test Jira connection.

```bash
f5 jira test
```

### f5 jira list

List issues from Jira.

```bash
# List all issues
f5 jira list

# Filter by status
f5 jira list --status "In Progress"

# Filter by type
f5 jira list --type Bug

# Custom JQL
f5 jira list --jql "assignee = currentUser()"
```

Options:
| Option | Description |
|--------|-------------|
| `-p, --project <key>` | Project key |
| `-s, --status <status>` | Filter by status |
| `-t, --type <type>` | Filter by issue type |
| `-a, --assignee <user>` | Filter by assignee |
| `-l, --limit <n>` | Max results (default: 20) |
| `--jql <query>` | Custom JQL query |

### f5 jira show

Show issue details.

```bash
f5 jira show PROJ-123
```

### f5 jira create

Create a new issue.

```bash
f5 jira create -s "Issue summary" -d "Description" -t Task -p High
```

Options:
| Option | Description |
|--------|-------------|
| `-s, --summary <text>` | Issue summary (required) |
| `-d, --description <text>` | Issue description |
| `-t, --type <type>` | Issue type (default: Task) |
| `-p, --priority <priority>` | Priority (default: Medium) |
| `-a, --assignee <user>` | Assignee account ID |
| `-l, --labels <labels>` | Labels (comma-separated) |

### f5 jira update

Update an existing issue.

```bash
# Update summary
f5 jira update PROJ-123 --summary "New summary"

# Update multiple fields
f5 jira update PROJ-123 --priority High --labels "urgent,bug"
```

Options:
| Option | Description |
|--------|-------------|
| `-s, --summary <text>` | New summary |
| `-d, --description <text>` | New description |
| `-p, --priority <priority>` | New priority |
| `-t, --status <status>` | Transition to new status |
| `-a, --assignee <accountId>` | Assignee account ID |
| `-l, --labels <labels>` | Labels (comma-separated) |

### f5 jira delete

Delete a Jira issue.

```bash
# Preview (requires --force to execute)
f5 jira delete PROJ-123

# Confirm deletion
f5 jira delete PROJ-123 --force
```

Options:
| Option | Description |
|--------|-------------|
| `--force` | Skip confirmation |
| `--delete-subtasks` | Also delete subtasks |

### f5 jira sync

Bi-directional sync with Jira.

```bash
# Bi-directional sync
f5 jira sync

# Push only
f5 jira sync --push

# Pull only
f5 jira sync --pull

# Dry run
f5 jira sync --dry-run
```

Options:
| Option | Description |
|--------|-------------|
| `--push` | Push local changes to Jira |
| `--pull` | Pull changes from Jira |
| `--bidirectional` | Bi-directional sync (default) |
| `--dry-run` | Preview without changes |
| `--conflict <strategy>` | Conflict resolution strategy |

### f5 jira conflicts

Show and resolve sync conflicts.

```bash
# List conflicts
f5 jira conflicts

# Resolve specific conflict
f5 jira conflicts --resolve <id> --strategy local-wins
```

Options:
| Option | Description |
|--------|-------------|
| `--resolve <id>` | Resolve specific conflict |
| `--strategy <strategy>` | Resolution: `local-wins`, `remote-wins`, `newest-wins` |

### f5 jira import

Import issues from CSV file directly to Jira.

```bash
# Preview import
f5 jira import file.csv --dry-run

# Import with limit
f5 jira import file.csv --limit 10

# Import all
f5 jira import file.csv
```

Options:
| Option | Description |
|--------|-------------|
| `--dry-run` | Preview without creating issues |
| `--limit <n>` | Limit number of issues to import |

### f5 jira projects

List available Jira projects.

```bash
f5 jira projects
```

## Attachment Commands

### f5 jira attachments

List attachments for an issue.

```bash
f5 jira attachments PROJ-123
```

Example output:
```
📎 Attachments for PROJ-123: 3 file(s)

  🖼️ screenshot.png
     ID: 10001 | Size: 245.3 KB | Date: 12/2/2024
     Author: John Doe
     Thumbnail: https://jira.example.com/...

  📄 requirements.pdf
     ID: 10002 | Size: 1.2 MB | Date: 12/1/2024
     Author: Jane Smith
```

### f5 jira upload

Upload attachment to an issue.

```bash
# Upload file
f5 jira upload PROJ-123 ./screenshot.png

# Upload with different filename
f5 jira upload PROJ-123 ./file.png --name "new-name.png"
```

Options:
| Option | Description |
|--------|-------------|
| `-n, --name <filename>` | Override filename |

### f5 jira download

Download attachments from an issue.

```bash
# List attachments (no download)
f5 jira download PROJ-123

# Download specific attachment
f5 jira download PROJ-123 10001

# Download all attachments
f5 jira download PROJ-123 --all

# Specify output directory
f5 jira download PROJ-123 --all -o ./downloads
```

Options:
| Option | Description |
|--------|-------------|
| `-o, --output <dir>` | Output directory (default: `.f5/attachments`) |
| `--all` | Download all attachments |

### f5 jira pull-attachments

Pull attachments for multiple issues.

```bash
# Pull attachments for specific issue
f5 jira pull-attachments -i PROJ-123

# Pull attachments for project issues (limited)
f5 jira pull-attachments --limit 50

# Specify output directory
f5 jira pull-attachments -o ./all-attachments
```

Options:
| Option | Description |
|--------|-------------|
| `-i, --issue <key>` | Pull for specific issue |
| `-o, --output <dir>` | Output directory (default: `.f5/attachments`) |
| `--limit <n>` | Limit number of issues (default: 20) |

Example output:
```
📥 Pulling attachments for 5 issue(s)...

PROJ-123: 2 attachment(s)
  ✓ screenshot.png
  ✓ document.pdf
PROJ-124: 1 attachment(s)
  ✓ image.jpg

📊 Summary:
  Files downloaded: 3
  Total size: 1.5 MB
  Location: .f5/attachments
```

## Japanese Excel Commands (問題管理表)

Special commands for Japanese issue management Excel files with embedded images.

### f5 jira convert-mondai

Convert Japanese 問題管理表 (Mondai Kanri Hyou) Excel files with image extraction.

```bash
# Convert with image extraction
f5 jira convert-mondai ./問題管理表.xlsx

# Analyze file structure only
f5 jira convert-mondai ./問題管理表.xlsx --analyze

# Preview without saving
f5 jira convert-mondai ./問題管理表.xlsx --dry-run

# Specify output directory
f5 jira convert-mondai ./file.xlsx -o ./output
```

Options:
| Option | Description |
|--------|-------------|
| `--analyze` | Analyze file structure only |
| `--dry-run` | Preview without saving |
| `-o, --output <dir>` | Output directory (default: `.f5`) |

Example output:
```
📊 Mondai Converter

📁 File: 問題管理表.xlsx
  Sheets: 74
  Main sheet: 動作確認一覧
  Detail sheets: 73 (No.1 - No.449)

📝 Conversion Results:
  Issues converted: 481
  Attachments extracted: 116

📊 Statistics:
  By Type: Bug: 245, Task: 180, Improvement: 56
  By Priority: High: 89, Medium: 312, Low: 80

📂 Output:
  Issues: .f5/issues/local.json
  Attachments: .f5/attachments/extracted/
```

#### Expected Excel Structure

The converter expects:

1. **Main sheet** (`動作確認一覧`): Issue list with columns:
   - B: No (Issue number)
   - C: 記入日 (Date)
   - D: 記入者 (Author)
   - E: 動作正誤 (Status: 異常/正常/改修提案)
   - F: 区分 (Category)
   - H: 顧客スプレッドシート (Screen)
   - I: 操作内容 (Operation)
   - J: 指摘内容/結果 (Issue content)
   - K: 修正内容 (Fix content)
   - L: 重要度 (Importance)
   - M: 優先度 (Priority)
   - N: 検証用AWS適用予定日 (Scheduled date)
   - O: 検証用AWS適用完了日 (Completed date)
   - P: コメント (Comment)

2. **Detail sheets** (`No.XXX`): Per-issue details with embedded screenshots

#### Status/Priority Mappings

| Japanese | F5 Status |
|----------|-----------|
| 異常 | Open |
| 正常 | Done |
| 改修提案 | Open |
| 対応中 | In Progress |
| 完了 | Done |
| 保留 | Blocked |

| Japanese | F5 Priority |
|----------|-------------|
| 高 | High |
| 中 | Medium |
| 低 | Low |
| α版でやる | High |
| 9月末まで | Medium |
| 余裕があったらやる | Low |

### f5 jira push-attachments

Upload extracted attachments to corresponding Jira issues.

```bash
# Upload attachments for specific issue number
f5 jira push-attachments -i 1

# Upload attachments for all issues
f5 jira push-attachments --all

# Preview without uploading
f5 jira push-attachments --all --dry-run

# Specify attachments directory
f5 jira push-attachments --all -d ./attachments
```

Options:
| Option | Description |
|--------|-------------|
| `-i, --issue <no>` | Issue number (e.g., 1, 449) |
| `--all` | Upload for all issues with attachments |
| `--dry-run` | Preview without uploading |
| `-d, --dir <path>` | Attachments directory (default: `.f5/attachments/extracted`) |

Example output:
```
📤 Uploading attachments for issue No.1 → TIMESHEET-141

  ✓ No1_image1.png (245.3 KB)
  ✓ No1_image2.png (189.7 KB)

📊 Summary:
  Files uploaded: 2
  Total size: 435 KB
  Target: TIMESHEET-141
```

## Standard Workflow

### 1. Initial Setup

```bash
# One-time setup
f5 jira setup
```

### 2. Prepare Data

Put your Excel/CSV files in `.f5/input/`:

```bash
cp requirements.xlsx .f5/input/
```

Supported formats:
- Excel (.xlsx, .xls)
- CSV (.csv)

### 3. Convert Files

```bash
# Convert new/changed files
f5 jira convert

# Or convert all
f5 jira convert --all
```

### 4. Push to Jira

```bash
# Preview first
f5 jira push --dry-run

# Then push
f5 jira push
```

### 5. Check Status

```bash
f5 jira status
```

## Excel Format

F5 auto-detects common column headers:

| Column | Aliases |
|--------|---------|
| Summary | Title, Name, Issue |
| Description | Details, Desc |
| Issue Type | Type, issuetype |
| Priority | Pri |
| Status | State |
| Labels | Tags |

Vietnamese headers are also supported:
- Mô tả → Description
- Ưu tiên → Priority
- Trạng thái → Status

## Authentication

### Jira Cloud

Use Basic Auth with email + API token:

```bash
f5 jira config \
  --url https://company.atlassian.net \
  --email user@company.com \
  --token <api-token> \
  --project MYPROJ
```

Get API token from: https://id.atlassian.com/manage-profile/security/api-tokens

### Jira Server/Data Center

Use Personal Access Token (PAT):

```bash
f5 jira config \
  --url http://jira.company.com \
  --email username \
  --token <personal-access-token> \
  --project MYPROJ
```

Create PAT in: Jira → Profile → Personal Access Tokens

## Configuration File

Configuration is stored in `.f5/integrations.json`:

```json
{
  "jira": {
    "baseUrl": "https://company.atlassian.net",
    "apiVersion": "3",
    "auth": {
      "type": "basic",
      "email": "user@company.com",
      "apiToken": "***"
    },
    "project": "MYPROJ"
  },
  "sync": {
    "enabled": true,
    "direction": "bidirectional",
    "autoSync": false,
    "conflictStrategy": "newest-wins"
  }
}
```

## Troubleshooting

### Connection Failed

```bash
# Test connection
f5 jira test

# Check configuration
f5 jira config --show
```

Common issues:
- Invalid API token
- Wrong auth type (basic vs pat)
- Firewall/VPN blocking connection

### Convert Failed

```bash
# Analyze file structure
f5 jira convert file.xlsx --analyze
```

Common issues:
- Invalid Excel format
- Missing required columns
- Encoding issues

### Push Failed

Check error messages for:
- Missing required fields
- Invalid issue type
- Permission denied

## Examples

### Complete Workflow

```bash
# 1. Setup
f5 jira setup

# 2. Prepare data
cp ~/Downloads/requirements.xlsx .f5/input/

# 3. Check status
f5 jira status

# 4. Convert
f5 jira convert

# 5. Preview
f5 jira push --dry-run

# 6. Push
f5 jira push

# 7. Verify
f5 jira list
```

### Multiple Files Workflow

```bash
# Copy multiple files
cp requirements.xlsx features.xlsx bugs.csv .f5/input/

# Check status
f5 jira status

# Convert all at once
f5 jira convert --all

# Push merged issues
f5 jira push
```

### Update Existing Issues

```bash
# Pull current state
f5 jira pull

# Make changes to local issues
# ...

# Push updates
f5 jira push
```

### Japanese Excel Workflow (問題管理表)

Complete workflow for Japanese issue management Excel files with embedded screenshots:

```bash
# 1. Setup Jira connection
f5 jira setup

# 2. Analyze Excel structure
f5 jira convert-mondai ./問題管理表.xlsx --analyze

# 3. Convert issues and extract images
f5 jira convert-mondai ./問題管理表.xlsx

# 4. Preview issues to push
f5 jira push --dry-run

# 5. Push issues to Jira
f5 jira push

# 6. Upload attachments for specific issue
f5 jira push-attachments -i 1

# 7. Or upload all attachments at once
f5 jira push-attachments --all

# 8. Verify attachments
f5 jira attachments PROJ-123
```

Output structure:
```
.f5/
├── issues/
│   └── local.json          # Converted issues
├── attachments/
│   └── extracted/
│       ├── No1/
│       │   ├── No1_image1.png
│       │   └── No1_image2.png
│       ├── No449/
│       │   └── No449_image1.png
│       └── ...
└── sync/
    └── jira-sync.json      # Issue mappings (externalId → Jira key)
```
