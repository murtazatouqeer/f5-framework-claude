# Excel Import Schema System

F5 Framework provides a flexible, schema-based system for importing Excel files to Jira-compatible CSV format.

## Overview

The Excel Import Schema System:
- **Auto-detects** Excel structure and suggests column mappings
- **Saves mappings** as reusable YAML schema files
- **Warns users** about complex files
- **Supports team-specific** configurations

## Quick Start

```bash
# Auto-detect and convert (first time)
f5 import excel issues.xlsx

# Use saved schema (subsequent imports)
f5 import excel issues.xlsx --schema issues

# Analyze without converting
f5 import excel issues.xlsx --analyze
```

## Commands

### Import Excel

```bash
f5 import excel <file.xlsx> [options]

Options:
  -s, --schema <name>    Use existing schema
  -c, --configure        Configure mapping interactively
  -a, --analyze          Analyze only, do not convert
  --claude-code          Generate prompt for Claude Code
  -t, --target <format>  Target format (jira)
  -o, --output <file>    Output file path
  -v, --verbose          Show detailed output
```

### Manage Schemas

```bash
# List all schemas
f5 import schema list

# Show schema details
f5 import schema show <name>

# Delete a schema
f5 import schema delete <name>

# Create template
f5 import schema template
```

## Schema Format

Schemas are stored in `.f5/schemas/excel-import-{name}.yaml`:

```yaml
schema_version: "1.0"
name: "issues"
description: "Issue tracking Excel format"

source:
  main_sheet: "動作確認一覧"    # Main data sheet name
  header_row: 3                 # Header row (1-based)
  data_start_row: 4             # First data row

column_mapping:
  - excel: "No"                 # Column name or letter (A, B, C)
    jira: "External ID"
    transform: "prefix:ISSUE-"
    required: true

  - excel: "指摘内容/結果"
    jira: "Summary"
    required: true
    max_length: 255

  - excel: "動作正誤"
    jira: "Issue Type"
    value_mapping:
      "異常": "Bug"
      "改修提案": "Improvement"
    default: "Task"

  - excel: "重要度"
    jira: "Priority"
    value_mapping:
      "高": "High"
      "中": "Medium"
      "低": "Low"
    default: "Medium"

validation:
  skip_empty_rows: true
  required_fields: ["Summary"]
  unique_fields: ["External ID"]

output:
  format: "csv"
  encoding: "utf-8"
  filename_template: "{source_name}_jira_{date}.csv"
  include_headers: true
```

## Column Mapping Options

| Option | Description | Example |
|--------|-------------|---------|
| `excel` | Column reference (letter, name, or index) | `"A"`, `"Title"`, `0` |
| `jira` | Target Jira field | `"Summary"`, `"Issue Type"` |
| `transform` | Transformation rule | `"prefix:ISSUE-"`, `"truncate:255"` |
| `value_mapping` | Value translations | `{"異常": "Bug"}` |
| `required` | Fail if empty | `true` |
| `default` | Default value | `"Task"` |
| `max_length` | Truncate if longer | `255` |
| `multiline` | Allow newlines | `true` |
| `format` | Data format | `"date"`, `"number"` |
| `date_format` | Date format | `"YYYY-MM-DD"` |

## Transformations

| Transform | Description | Example |
|-----------|-------------|---------|
| `prefix:{text}` | Add prefix | `"prefix:ISSUE-"` → `ISSUE-123` |
| `suffix:{text}` | Add suffix | `"suffix:-v1"` → `123-v1` |
| `truncate:{n}` | Truncate to length | `"truncate:100"` |
| `lowercase` | Convert to lowercase | `"lowercase"` |
| `uppercase` | Convert to uppercase | `"uppercase"` |
| `replace:{a}\|{b}` | Replace text | `"replace:foo\|bar"` |

## Jira Fields

Supported target fields:

| Field | Description |
|-------|-------------|
| `Summary` | Issue title (required, max 255 chars) |
| `Description` | Detailed description |
| `Issue Type` | Bug, Story, Task, Improvement |
| `Priority` | Highest, High, Medium, Low, Lowest |
| `Status` | To Do, In Progress, Done |
| `Assignee` | User to assign |
| `Reporter` | Who reported |
| `Due Date` | Target date |
| `Labels` | Tags (space-separated) |
| `Component` | Component name |
| `External ID` | External reference |

## Auto-Detection

The analyzer auto-detects:

1. **Main sheet** - Largest data sheet or known names (動作確認一覧, Issues, etc.)
2. **Header row** - Row with most non-empty cells matching known patterns
3. **Column mappings** - Headers matched against known patterns
4. **Data types** - Text, number, date, enum

### Detection Patterns

Japanese patterns are built-in:

| Jira Field | Japanese Patterns |
|------------|-------------------|
| External ID | No, 番号, ID |
| Summary | 件名, タイトル, 概要, 指摘内容 |
| Description | 内容, 説明, 詳細, 修正内容 |
| Issue Type | 動作正誤, 種別, カテゴリ |
| Priority | 優先度, 重要度 |
| Reporter | 報告者, 記入者 |

## Complex Files

For complex Excel files (many sheets, images, formulas), the system:

1. Shows analysis with warnings
2. Offers options:
   - Generate Claude Code prompt
   - Configure manually
   - Continue with auto-detection
3. Recommends manual review for low confidence

### Complexity Indicators

| Indicator | Threshold |
|-----------|-----------|
| Many sheets | >10 sheets |
| Low confidence | <60% |
| Detail sheets | Sheet names like "No.123" |
| Special content | Images, formulas, merged cells |

## Examples

### Example 1: Japanese Issue Tracker

```bash
# First import - auto-detect and save schema
f5 import excel 問題管理表.xlsx

# Analysis shows:
# - Sheet: 動作確認一覧 (484 rows)
# - Header Row: 3
# - Mappings detected with 85% confidence

# Save schema as "issues"
# Future imports:
f5 import excel 問題管理表.xlsx --schema issues
```

### Example 2: Custom Configuration

```bash
# Start interactive configuration
f5 import excel data.xlsx --configure

# Review each column mapping
# Save as custom schema
# Use for future imports
```

### Example 3: Generate Claude Code Prompt

```bash
# For complex files, generate prompt
f5 import excel complex.xlsx --claude-code

# Copy prompt to Claude Code for manual review
```

## MCP Excel Integration (v2.0)

Starting with F5 Framework v2.0, Excel import can be performed directly in Claude Desktop using MCP (Model Context Protocol) Excel server.

### Setup MCP Excel

1. Install MCP Excel server:
   ```bash
   npm install -g @anthropic/mcp-excel
   ```

2. Configure Claude Desktop (`claude_desktop_config.json`):
   ```json
   {
     "mcpServers": {
       "excel": {
         "command": "mcp-excel",
         "args": []
       }
     }
   }
   ```

3. Restart Claude Desktop.

### MCP Excel Commands

| Command | Description |
|---------|-------------|
| `/f5-import <file>` | Import with MCP Excel auto-detection |
| `/f5-import-analyze <file>` | Analyze Excel structure |
| `/f5-import-schema list` | List available schemas |
| `/f5-import-schema create <name>` | Create new schema |

### MCP vs CLI Import

| Feature | CLI (`f5 import excel`) | MCP (`/f5-import`) |
|---------|-------------------------|---------------------|
| Requires Node.js | Yes | No (uses MCP server) |
| Interactive | Terminal-based | Claude Desktop UI |
| Schema format | Same YAML format | Same YAML format |
| Auto-detection | Built-in | Built-in |
| Japanese support | Full | Full |

### Schema Compatibility

Schemas created with CLI are compatible with MCP import and vice versa. Both use the same `.f5/schemas/` directory.

For detailed MCP setup and usage, see [MCP Excel Integration Guide](./mcp-excel-integration.md).

## Excel Note Parsing

F5 Framework can automatically detect and preserve notes/annotations in Excel files when converting to Markdown.

### Supported Note Patterns

| Pattern | Style | Example |
|---------|-------|---------|
| `※1`, `※2` | Japanese Kome | 必須項目※1 |
| `*1`, `*2` | Asterisk | Required*1 |
| `(注1)`, `(注2)` | Japanese Note | 登録時(注1) |
| `[1]`, `[2]` | Bracketed | Submit[1] |
| `→1`, `→2` | Arrow | 参照→1 |
| `**1`, `**2` | Double Asterisk | Important**1 |
| `¹`, `²`, `³` | Superscript | Value¹ |

### Note Parsing Options

```bash
# Enable note parsing (default)
/f5-import requirements.xlsx --notes

# Disable note parsing
/f5-import requirements.xlsx --no-notes

# Change output format
/f5-import requirements.xlsx --notes-format inline
```

### Output Formats

| Format | Description |
|--------|-------------|
| `footnote` | Markdown footnotes `[^1]` (default) |
| `inline` | Inline note text |
| `section` | Notes in separate section |

### Configuration

Configure note handling in `.f5/config/excel-notes.yaml`:

```yaml
reference_patterns:
  - pattern: "※(\\d+)"
    name: "japanese_kome"
    priority: 1

output:
  format: "footnote"
  preserve_original_marker: false

auto_detect:
  enabled: true
  bottom_rows_count: 30
```

### Example

**Input Excel:**
```
| 項目名 | 説明 |
|--------|------|
| ユーザー名 | 必須項目※1 |
| メール | 形式チェック※2 |

※1: 半角英数字のみ
※2: RFC 5322準拠
```

**Output Markdown:**
```markdown
| 項目名 | 説明 |
|--------|------|
| ユーザー名 | 必須項目[^1] |
| メール | 形式チェック[^2] |

---
## 注釈 (Notes)

[^1]: 半角英数字のみ
[^2]: RFC 5322準拠
```

## Best Practices

1. **Save schemas** for recurring imports
2. **Review mappings** for first-time files
3. **Use Claude Code** for complex files
4. **Document schemas** with descriptions
5. **Share schemas** with team via version control
6. **Use MCP Excel** in Claude Desktop for interactive imports
7. **Enable note parsing** to preserve Japanese annotations

## File Locations

```
project/
├── .f5/
│   └── schemas/
│       ├── excel-import-issues.yaml
│       └── excel-import-requirements.yaml
└── output_jira.csv
```

## Troubleshooting

### Low Confidence Warning

If confidence is <60%:
- Review detected mappings
- Use `--configure` for manual mapping
- Use `--claude-code` for AI assistance

### Missing Required Fields

Ensure your Excel has columns that map to:
- `Summary` (required)
- `External ID` (recommended)

### Wrong Sheet Selected

Specify sheet in schema:
```yaml
source:
  main_sheet: "Correct Sheet Name"
```

### Value Mapping Issues

Add explicit mappings:
```yaml
value_mapping:
  "Your Value": "Jira Value"
```
