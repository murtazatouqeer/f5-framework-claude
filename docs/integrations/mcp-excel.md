# MCP Excel Integration Guide

This guide explains how to set up and use MCP Excel server with F5 Framework for seamless Excel file processing in Claude Desktop.

## Overview

F5 Framework v2.0 uses MCP (Model Context Protocol) Excel server to read and process Excel files directly within Claude Desktop, eliminating the need for CLI-based Excel processing.

### Benefits

- **Direct Integration**: Read Excel files without leaving Claude Desktop
- **No CLI Required**: No need for Node.js scripts or external tools
- **Real-time Processing**: Process files as you work
- **Image Extraction**: Extract embedded images from Excel (if supported)
- **Multi-sheet Support**: Handle workbooks with multiple sheets

## Prerequisites

- Claude Desktop installed
- MCP server support enabled in Claude Desktop
- Node.js 18+ (for MCP server)

## Installation

### Step 1: Install MCP Excel Server

```bash
# Option 1: Global installation
npm install -g @anthropic/mcp-excel

# Option 2: Local installation in project
npm install @anthropic/mcp-excel
```

### Step 2: Configure Claude Desktop

Add MCP Excel server to your Claude Desktop configuration:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "excel": {
      "command": "mcp-excel",
      "args": [],
      "env": {}
    }
  }
}
```

If using local installation:

```json
{
  "mcpServers": {
    "excel": {
      "command": "npx",
      "args": ["@anthropic/mcp-excel"],
      "env": {}
    }
  }
}
```

### Step 3: Restart Claude Desktop

Close and reopen Claude Desktop to load the MCP server.

### Step 4: Verify Installation

In Claude Desktop, the MCP Excel tools should be available:

```
Available MCP tools:
- mcp_excel.list_sheets
- mcp_excel.read_sheet
- mcp_excel.get_workbook_info
```

## Usage with F5 Framework

### Basic Import Workflow

```bash
# 1. Place Excel file in input directory
cp requirements.xlsx .f5/input/requirements/

# 2. Analyze file structure
/f5-import-analyze requirements.xlsx

# 3. Import with auto-detection
/f5-import requirements.xlsx

# 4. Validate imported data
/f5-spec validate
```

### Import Commands

| Command | Description |
|---------|-------------|
| `/f5-import <file>` | Import Excel file with auto-detection |
| `/f5-import-analyze <file>` | Analyze Excel structure before import |
| `/f5-import-schema list` | List available import schemas |
| `/f5-import-schema create <name>` | Create custom import schema |

### Supported File Types

- `.xlsx` - Excel 2007+ (recommended)
- `.xls` - Excel 97-2003
- `.csv` - Comma-separated values (fallback)

## MCP Excel Capabilities

### list_sheets

Get all sheet names in a workbook.

```
mcp_excel.list_sheets("/path/to/file.xlsx")
→ ["Sheet1", "要件一覧", "画面一覧"]
```

### read_sheet

Read data from a specific sheet.

```
mcp_excel.read_sheet("/path/to/file.xlsx", "要件一覧")
→ [
    {"A": "要件ID", "B": "要件名", "C": "説明"},
    {"A": "REQ-001", "B": "ログイン機能", "C": "..."},
    ...
  ]
```

### get_workbook_info

Get workbook metadata.

```
mcp_excel.get_workbook_info("/path/to/file.xlsx")
→ {
    "sheets": 3,
    "author": "User",
    "created": "2024-01-15",
    "modified": "2024-01-20"
  }
```

## Column Mapping

### Auto-Detection

F5 Framework automatically detects column types based on:

1. **Header Names**: Japanese and English patterns
2. **Data Patterns**: ID formats, dates, enums
3. **Value Distribution**: Priority, status values

### Japanese/English Mapping

| Japanese Header | English Header | Field Name |
|----------------|----------------|------------|
| 要件ID | Requirement ID | id |
| 要件名 | Title | title |
| 説明 | Description | description |
| 優先度 | Priority | priority |
| ステータス | Status | status |
| カテゴリ | Category | category |
| 担当者 | Owner | owner |

### Value Mapping

**Priority:**
| Japanese | English |
|----------|---------|
| 最高, 高, 緊急 | High |
| 中, 普通 | Medium |
| 低, 最低 | Low |

**Status:**
| Japanese | English |
|----------|---------|
| 未着手, 新規 | To Do |
| 進行中, 対応中 | In Progress |
| 完了, クローズ | Done |
| 保留 | On Hold |

## Custom Schemas

### Creating a Custom Schema

```bash
/f5-import-schema create my-custom-schema
```

Interactive prompts will guide you through:
1. Document type selection
2. Column definitions
3. Value mappings
4. Validation rules
5. Output settings

### Schema File Format

```yaml
name: "my-custom-schema"
version: "1.0.0"
document_type: "requirements"

columns:
  - excel_column: "ID"
    field: "id"
    type: "string"
    required: true
    pattern: "^REQ-\\d{3}$"

  - excel_column: "Name"
    field: "title"
    type: "string"
    required: true

  - excel_column: "Priority"
    field: "priority"
    type: "enum"
    values:
      - source: ["High", "高"]
        target: "High"
      - source: ["Medium", "中"]
        target: "Medium"
      - source: ["Low", "低"]
        target: "Low"

validation:
  unique_fields: ["id"]
  required_fields: ["id", "title"]

output:
  path: ".f5/specs/srs/v{VERSION}/"
  format: "markdown"
```

### Using Custom Schema

```bash
/f5-import data.xlsx --schema my-custom-schema
```

## Troubleshooting

### MCP Excel Not Available

**Symptom:** Error message "MCP Excel server not available"

**Solutions:**
1. Verify installation: `which mcp-excel` or `npx mcp-excel --version`
2. Check Claude Desktop config file syntax
3. Restart Claude Desktop
4. Check MCP server logs

### File Not Found

**Symptom:** Error message "File not found"

**Solutions:**
1. Use absolute path: `/Users/user/project/.f5/input/file.xlsx`
2. Place file in `.f5/input/` directory
3. Check file permissions

### Column Not Recognized

**Symptom:** Columns mapped to "unknown"

**Solutions:**
1. Check header spelling (exact match required)
2. Add column aliases to schema
3. Create custom schema with your column names

### Japanese Characters Not Displaying

**Symptom:** Garbled text or ???

**Solutions:**
1. Ensure Excel file is saved with UTF-8 encoding
2. Use `.xlsx` format (better Unicode support)
3. Check Claude Desktop encoding settings

## Best Practices

### File Organization

```
.f5/
├── input/
│   ├── requirements/      # Place requirements Excel here
│   ├── basic-design/      # Place design documents here
│   ├── detail-design/     # Place detail specs here
│   └── change-requests/   # Place CRs here
├── schemas/               # Custom schemas
└── specs/                 # Generated output
```

### Workflow Recommendations

1. **Always analyze first**: Run `/f5-import-analyze` before importing
2. **Use version control**: Specify `--version` for each import
3. **Validate after import**: Run `/f5-spec validate`
4. **Keep schemas versioned**: Track schema changes in git

### Performance Tips

- Keep Excel files under 10,000 rows
- Use `.xlsx` format for better performance
- Close Excel before importing (avoid file locks)
- Split large files into multiple sheets

## Fallback: CSV Import

If MCP Excel is not available, you can use CSV fallback:

1. Export Excel to CSV (UTF-8 encoding)
2. Place in `.f5/input/requirements/`
3. Run `/f5-import file.csv`

CSV import uses native file reading without MCP.

## Security Considerations

- MCP Excel server runs locally on your machine
- No data is sent to external servers
- File access is limited to specified paths
- Review imported data before committing

## Integration with F5 Workflow

### Gate D1: Research Complete

After importing requirements:

```bash
/f5-import requirements.xlsx
/f5-gate check D1
```

### Gate D2: SRS Approved

After generating SRS:

```bash
/f5-spec generate srs --from requirements
/f5-gate check D2
```

### Full Workflow

```
/f5-init my-project
/f5-load
/f5-import requirements.xlsx
/f5-spec generate srs
/f5-gate check D1
/f5-gate check D2
/f5-design generate architecture
/f5-gate check D3
```

## Additional Resources

- [F5 Framework Documentation](./README.md)
- [Excel Import Schema Reference](./excel-schema.md)
- [Quality Gates Guide](../guides/quality-gates.md)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)

---

*Last updated: 2024-01*
*F5 Framework v2.0*
