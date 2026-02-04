---
description: Import documents - single, batch, analyze, or schema management
argument-hint: <file|dir> [--batch|--analyze|--schema] [options]
---

# /f5-import - Unified Document Import Command

Import requirements, design documents, or change requests from Excel files using MCP Excel server.

**Consolidated command** that replaces:
- `/f5-import-batch` → `/f5-import <dir> --batch`
- `/f5-import-analyze` → `/f5-import <file> --analyze`
- `/f5-import-schema` → `/f5-import --schema <action>`

## MODE DETECTION

Parse $ARGUMENTS to determine mode:

| Pattern | Mode | Description |
|---------|------|-------------|
| `<dir> --batch` | BATCH | Batch import from folder |
| `<file> --analyze` | ANALYZE | Analyze file structure |
| `--schema <action>` | SCHEMA | Schema management |
| `<file>` (default) | IMPORT | Single file import |

---

## MODE: BATCH

**Usage:**
```bash
/f5-import .f5/input/excel/0203/ --batch
/f5-import .f5/input/excel/ --batch --recursive
/f5-import .f5/input/excel/ --batch --pattern "UI13_*.xlsx"
/f5-import .f5/input/excel/ --batch --dry-run
```

### Batch Flags
| Flag | Description |
|------|-------------|
| `--batch` | Enable batch mode |
| `--recursive` | Include subfolders |
| `--pattern <glob>` | Filter files by pattern |
| `--parallel <n>` | Parallel import count |
| `--stop-on-error` | Stop on first error |

See original batch documentation for full details.

---

## MODE: ANALYZE

**Usage:**
```bash
/f5-import requirements.xlsx --analyze
/f5-import data.xlsx --analyze --verbose
/f5-import data.xlsx --analyze --suggest-schema
```

### Analyze Flags
| Flag | Description |
|------|-------------|
| `--analyze` | Enable analyze mode |
| `--verbose` | Show detailed analysis |
| `--suggest-schema` | Generate schema file |
| `--sheet <name>` | Analyze specific sheet |

See original analyze documentation for full details.

---

## MODE: SCHEMA

**Usage:**
```bash
/f5-import --schema list
/f5-import --schema show <name>
/f5-import --schema create <name>
/f5-import --schema validate <name>
/f5-import --schema delete <name>
```

### Schema Actions
| Action | Description |
|--------|-------------|
| `list` | List all schemas |
| `show <name>` | Display schema details |
| `create <name>` | Create new schema |
| `edit <name>` | Edit existing schema |
| `validate <name>` | Validate schema |
| `delete <name>` | Delete schema |
| `export <name>` | Export schema |
| `import <file>` | Import schema from file |

See original schema documentation for full details.

---

## MODE: IMPORT (Default)

## ARGUMENTS
The user's request is: $ARGUMENTS

## ⚠️ CRITICAL OUTPUT RULES

**KHÔNG ĐƯỢC tạo files ở `docs/`, `output/`, hoặc thư mục khác.**

**BẮT BUỘC tuân theo cấu trúc sau:**

| Document Type | Output Path |
|--------------|-------------|
| Requirements | `.f5/specs/srs/v{VERSION}/requirements.md` |
| Screen List | `.f5/specs/basic-design/v{VERSION}/screens/screen-list.md` |
| API List | `.f5/specs/basic-design/v{VERSION}/api/api-list.md` |
| Table List | `.f5/specs/basic-design/v{VERSION}/database/table-list.md` |
| Screen Detail | `.f5/specs/detail-design/v{VERSION}/screens/` |
| API Detail | `.f5/specs/detail-design/v{VERSION}/api/` |
| Change Request | `.f5/input/change-requests/` |
| Bug Report | `.f5/input/bugs/` |
| Jira CSV | `.f5/csv/{filename}_jira.csv` |

**VERSION format:** `v1.0.0`, `v1.1.0`, `v2.0.0`

**✅ CORRECT paths:**
```
.f5/specs/srs/v1.0.0/requirements.md ✅
.f5/specs/basic-design/v1.0.0/screens/screen-list.md ✅
.f5/specs/basic-design/v1.0.0/database/table-list.md ✅
```

**❌ WRONG paths:**
```
docs/requirements.md ❌
output/requirements.md ❌
requirements.md ❌ (in root)
.f5/specs/basic-design/v1.0.0/screen-list.md ❌ (missing screens/ folder!)
```

## STEP 1: CHECK MCP EXCEL SERVER

### 1.1 Verify MCP Excel Availability

```
Check if MCP Excel server is available:
- Server: @anthropic/mcp-excel (or configured Excel MCP)
- Required capabilities: read_workbook, list_sheets, read_sheet
```

**If MCP Excel NOT available:**
```markdown
## ⚠️ MCP Excel Server Not Available

The MCP Excel server is required for importing Excel files.

### Setup Instructions

1. **Install MCP Excel server:**
   ```bash
   npm install -g @anthropic/mcp-excel
   ```

2. **Configure in Claude Desktop settings:**
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

3. **Restart Claude Desktop** and try again.

### Alternative: Manual Import
Place a CSV export in `.f5/input/` and use `/f5-import <file.csv>`
```

**If MCP Excel available:** Continue to Step 2.

## STEP 2: PARSE USER REQUEST

| Pattern | Action |
|---------|--------|
| `<filename>.xlsx` or `<filename>.xls` | **IMPORT_EXCEL** |
| `<filename>.csv` | **IMPORT_CSV** |
| `--type <type>` | Specify document type |
| `--version <version>` | Specify version label |
| `--schema <schema>` | Use custom schema |
| `--sheet <name>` | Import specific sheet |
| `--dry-run` | Preview without writing |

## STEP 3: LOCATE AND READ FILE

### 3.1 Search Order

```bash
# Priority search paths
1. Current directory: ./<filename>
2. Input requirements: .f5/input/requirements/<filename>
3. Input basic-design: .f5/input/basic-design/<filename>
4. Input detail-design: .f5/input/detail-design/<filename>
5. Input change-requests: .f5/input/change-requests/<filename>
```

### 3.2 Read Excel with MCP

```
Use MCP Excel to:
1. mcp_excel.list_sheets(file_path) → Get available sheets
2. mcp_excel.read_sheet(file_path, sheet_name) → Read data
3. Extract headers from first row
4. Extract data rows
```

### 3.3 Extract Embedded Images (if supported)

```
If MCP Excel supports image extraction:
1. mcp_excel.extract_images(file_path) → Get embedded images
2. Save to: .f5/output/images/{REQ_ID}_{INDEX}.png
3. Create markdown references
```

## STEP 4: AUTO-DETECT DOCUMENT TYPE

### 4.1 Header Pattern Detection

| Headers Detected (Japanese/English) | Document Type |
|-------------------------------------|---------------|
| 要件ID, Requirement ID, REQ- | `requirements` |
| 画面一覧, Screen List, SCR- | `basic-design/screens` |
| API一覧, API List, API- | `basic-design/api` |
| テーブル一覧, Table List, TBL- | `basic-design/tables` |
| 画面詳細, Screen Detail | `detail-design/screens` |
| API詳細, API Detail | `detail-design/api` |
| CR番号, Change Request, CR- | `change-request` |
| バグID, Bug ID, BUG- | `bug-report` |
| チケット, Ticket, Issue | `issue` |

### 4.2 Multi-Sheet Detection

```
For workbooks with multiple sheets:
1. List all sheet names
2. Detect type for each sheet
3. Import each sheet to appropriate location
4. Generate combined traceability
```

## STEP 5: LOAD COLUMN SCHEMA

### 5.1 Check Custom Schema

```bash
# Check for project-specific schema
if [ -f ".f5/schemas/import-schema.yaml" ]; then
  SCHEMA=".f5/schemas/import-schema.yaml"
elif [ -f ".f5-templates/excel-formats.yaml" ]; then
  SCHEMA=".f5-templates/excel-formats.yaml"
fi
```

### 5.2 Default Column Mappings

**Requirements (要件定義):**
| Japanese | English | Field | Required |
|----------|---------|-------|----------|
| 要件ID | Requirement ID | id | Yes |
| 要件名 | Title | title | Yes |
| 説明 | Description | description | Yes |
| 優先度 | Priority | priority | No |
| ステータス | Status | status | No |
| カテゴリ | Category | category | No |
| 担当者 | Owner | owner | No |
| 受入基準 | Acceptance Criteria | acceptance_criteria | No |
| 備考 | Notes | notes | No |

**Screens (画面一覧):**
| Japanese | English | Field | Required |
|----------|---------|-------|----------|
| 画面ID | Screen ID | id | Yes |
| 画面名 | Screen Name | name | Yes |
| 画面種別 | Screen Type | type | No |
| 関連要件 | Related Requirements | related_reqs | No |
| 説明 | Description | description | No |

**API (API一覧):**
| Japanese | English | Field | Required |
|----------|---------|-------|----------|
| API ID | API ID | id | Yes |
| メソッド | Method | method | Yes |
| エンドポイント | Endpoint | endpoint | Yes |
| 説明 | Description | description | No |
| 関連要件 | Related Requirements | related_reqs | No |

**Tables (テーブル一覧):**
| Japanese | English | Field | Required |
|----------|---------|-------|----------|
| テーブルID | Table ID | id | Yes |
| テーブル名 | Table Name | name | Yes |
| 説明 | Description | description | No |
| 関連要件 | Related Requirements | related_reqs | No |

**Change Requests (変更要求):**
| Japanese | English | Field | Required |
|----------|---------|-------|----------|
| CR番号 | CR Number | id | Yes |
| タイトル | Title | title | Yes |
| 説明 | Description | description | Yes |
| 影響範囲 | Impact Scope | impact | No |
| 優先度 | Priority | priority | No |
| ステータス | Status | status | No |

## STEP 6: VALUE MAPPINGS

### 6.1 Issue Type Mapping

| Japanese | English |
|----------|---------|
| 異常 | Bug |
| バグ | Bug |
| 不具合 | Bug |
| 機能 | Story |
| 要望 | Story |
| 機能要件 | Story |
| タスク | Task |
| 作業 | Task |
| 改善 | Improvement |
| エンハンス | Improvement |

### 6.2 Priority Mapping

| Japanese | English |
|----------|---------|
| 最高 | Highest |
| 高 | High |
| 中 | Medium |
| 低 | Low |
| 最低 | Lowest |
| 緊急 | Highest |
| 重要 | High |
| 普通 | Medium |

### 6.3 Status Mapping

| Japanese | English |
|----------|---------|
| 未着手 | To Do |
| 新規 | To Do |
| オープン | To Do |
| 進行中 | In Progress |
| 対応中 | In Progress |
| 作業中 | In Progress |
| レビュー中 | In Review |
| 確認中 | In Review |
| 完了 | Done |
| クローズ | Done |
| 解決済み | Done |
| 保留 | On Hold |
| 中断 | On Hold |
| 却下 | Rejected |
| 対応不要 | Won't Do |

## STEP 7: TRANSFORM DATA

### 7.1 Apply Column Mapping

```python
# Pseudocode for transformation
for row in excel_data:
    mapped_row = {}
    for excel_col, field in column_mapping.items():
        if excel_col in row:
            mapped_row[field] = row[excel_col]

    # Apply value mappings
    if 'priority' in mapped_row:
        mapped_row['priority'] = priority_mapping.get(
            mapped_row['priority'],
            mapped_row['priority']
        )
    if 'status' in mapped_row:
        mapped_row['status'] = status_mapping.get(
            mapped_row['status'],
            mapped_row['status']
        )

    transformed_data.append(mapped_row)
```

### 7.2 Generate IDs if Missing

```
If ID column is empty:
- Requirements: REQ-001, REQ-002, ...
- Screens: SCR-001, SCR-002, ...
- APIs: API-001, API-002, ...
- Tables: TBL-001, TBL-002, ...
- Change Requests: CR-001, CR-002, ...
```

### 7.3 Validate Required Fields

```
For each row:
1. Check required fields are present
2. Log warning for missing optional fields
3. Error if required field missing
```

## STEP 8: GENERATE OUTPUT FILES

### 8.1 Output Paths by Type

| Type | Output Path |
|------|-------------|
| requirements | `.f5/specs/srs/v{VERSION}/requirements.md` |
| basic-design/screens | `.f5/specs/basic-design/v{VERSION}/screens/` |
| basic-design/api | `.f5/specs/basic-design/v{VERSION}/api/` |
| basic-design/tables | `.f5/specs/basic-design/v{VERSION}/database/` |
| detail-design/* | `.f5/specs/detail-design/v{VERSION}/` |
| change-request | `.f5/input/change-requests/` |
| bug-report | `.f5/input/bugs/` |

### 8.2 Generate Requirements Markdown

```markdown
# Requirements (要件一覧)

**Imported:** {{TIMESTAMP}}
**Source:** {{SOURCE_FILE}}
**Version:** {{VERSION}}
**Total:** {{COUNT}} requirements

---

## REQ-001: {{TITLE}}

**ID:** REQ-001
**Priority:** {{PRIORITY}}
**Status:** {{STATUS}}
**Category:** {{CATEGORY}}
**Owner:** {{OWNER}}

### Description (説明)
{{DESCRIPTION}}

### Acceptance Criteria (受入基準)
{{ACCEPTANCE_CRITERIA}}

### Attachments (添付)
{{#if IMAGES}}
![Screenshot](../images/REQ-001_1.png)
{{/if}}

### Traceability (トレーサビリティ)
- Design: {{DESIGN_REFS}}
- Test Cases: {{TEST_REFS}}
- Code: {{CODE_REFS}}

---
```

### 8.3 Generate Screen List Markdown

```markdown
# Screen List (画面一覧)

**Imported:** {{TIMESTAMP}}
**Source:** {{SOURCE_FILE}}
**Version:** {{VERSION}}

| ID | Name | Type | Related Requirements |
|----|------|------|---------------------|
| SCR-001 | {{NAME}} | {{TYPE}} | {{RELATED_REQS}} |
```

### 8.4 Generate API List Markdown

```markdown
# API List (API一覧)

**Imported:** {{TIMESTAMP}}
**Source:** {{SOURCE_FILE}}
**Version:** {{VERSION}}

| ID | Method | Endpoint | Description | Related Requirements |
|----|--------|----------|-------------|---------------------|
| API-001 | {{METHOD}} | {{ENDPOINT}} | {{DESCRIPTION}} | {{RELATED_REQS}} |
```

### 8.5 Generate Traceability Entry

```markdown
# Traceability Matrix (トレーサビリティマトリクス)

| REQ ID | Screens | APIs | Tables | Test Cases |
|--------|---------|------|--------|------------|
| REQ-001 | | | | |
| REQ-002 | | | | |
```

## STEP 9: UPDATE SESSION

### 9.1 Write to Session Memory

```markdown
## Import History

### {{TIMESTAMP}}
- **File:** {{FILENAME}}
- **Type:** {{DOCUMENT_TYPE}}
- **Version:** {{VERSION}}
- **Count:** {{ITEM_COUNT}} items
- **Images:** {{IMAGE_COUNT}} extracted
- **Warnings:** {{WARNING_COUNT}}
- **Output:** {{OUTPUT_PATH}}
```

### 9.2 Update Gates Status

```yaml
# Update .f5/quality/gates-status.yaml
imports:
  - file: {{FILENAME}}
    type: {{TYPE}}
    date: {{TIMESTAMP}}
    count: {{COUNT}}

gates:
  D1:
    requirements_imported: true
    import_date: {{TIMESTAMP}}
```

## STEP 10: OUTPUT SUMMARY

```markdown
## 📥 Import Complete

**File:** {{FILENAME}}
**Type:** {{DOCUMENT_TYPE}}
**Version:** {{VERSION}}
**MCP Server:** {{MCP_SERVER_NAME}}

### Summary
| Category | Count |
|----------|-------|
| Total Items | {{COUNT}} |
| New | {{NEW}} |
| Updated | {{UPDATED}} |
| Skipped | {{SKIPPED}} |
| Images Extracted | {{IMAGES}} |

### Column Mapping Used
| Excel Column | Mapped To | Sample Value |
|--------------|-----------|--------------|
| {{COL_1}} | {{FIELD_1}} | {{SAMPLE_1}} |
| {{COL_2}} | {{FIELD_2}} | {{SAMPLE_2}} |

### Value Transformations
| Original | Transformed | Count |
|----------|-------------|-------|
| 高 | High | {{COUNT}} |
| 未着手 | To Do | {{COUNT}} |

### Output Files
- `{{OUTPUT_PATH_1}}`
- `{{OUTPUT_PATH_2}}`

### ⚠️ Warnings
{{#if WARNINGS}}
{{#each WARNINGS}}
- {{this}}
{{/each}}
{{else}}
No warnings.
{{/if}}

### ❌ Errors
{{#if ERRORS}}
{{#each ERRORS}}
- Row {{row}}: {{message}}
{{/each}}
{{else}}
No errors.
{{/if}}

### Next Steps
1. Review imported content at `{{OUTPUT_PATH}}`
2. Run `/f5-spec validate` to check consistency
3. Complete any missing fields manually
4. Run `/f5-gate check D1` to verify gate progress
```

## STEP 11: JIRA OUTPUT (Optional)

### 11.1 Enable Jira Output

Add `--jira` flag to generate Jira-compatible output:

```
/f5-import issues.xlsx --jira
```

Or use with `--type issues`:

```
/f5-import data.xlsx --type issues --jira
```

### 11.2 Jira Column Mapping

When `--jira` flag is set, apply additional Jira-specific mappings:

| Japanese Column | Jira Field |
|-----------------|------------|
| No, No. | External ID |
| 問題内容, 指摘内容 | Summary |
| 詳細, 内容, 説明 | Description |
| 判定, 判定結果, 種別 | Issue Type |
| 優先度, 重要度 | Priority |
| 状況, 状態, ステータス | Status |
| 担当者 | Assignee |
| 期限, 期日 | Due Date |
| カテゴリ, ラベル | Labels |
| 対応内容, コメント | Comment |

### 11.3 Jira Issue Type Mapping

| Japanese | Jira Type |
|----------|-----------|
| 異常, バグ, 不具合 | Bug |
| 改善, 改善要望 | Improvement |
| 確認, タスク | Task |
| 機能, ストーリー | Story |
| 正常 | (Skipped by default) |

### 11.4 Jira Output Files

```
.f5/
├── csv/
│   └── {filename}_jira.csv      ← Jira-importable CSV
├── issues/
│   ├── {filename}.json          ← F5 internal format
│   └── local.json               ← Merged for sync
└── sync/
    └── conversion-tracking.json  ← Track conversion state
```

### 11.5 Jira CSV Format

```csv
Summary,Issue Type,Priority,Description,Labels,External ID,Due Date
"Login fails on mobile",Bug,High,"Steps to reproduce...",testing,PROJECT-001,2024-02-15
"Add dark mode",Improvement,Medium,"User requested...",ui,PROJECT-002,
```

### 11.6 Jira Output Summary

When `--jira` flag is used, add to output:

```markdown
### Jira Output
- **CSV:** `.f5/csv/{filename}_jira.csv`
- **JSON:** `.f5/issues/{filename}.json`
- **Issues converted:** {{JIRA_COUNT}}
- **Skipped (正常):** {{SKIPPED_COUNT}}

### By Issue Type
| Type | Count |
|------|-------|
| Bug | {{BUG_COUNT}} |
| Improvement | {{IMPROVEMENT_COUNT}} |
| Task | {{TASK_COUNT}} |

### Next Steps (Jira)
1. Preview sync: `/f5-jira-sync --dry-run`
2. Push to Jira: `f5 jira push`
3. Check status: `/f5-jira-status`
```

## EXCEL NOTE PARSING

### Note Pattern Support

F5 automatically detects and preserves notes/annotations in Excel files:

| Pattern | Style | Example |
|---------|-------|---------|
| `※1`, `※2` | Japanese Kome | 必須項目です※1 |
| `*1`, `*2` | Asterisk | Required*1 |
| `(注1)`, `(注2)` | Japanese Note | 登録時(注1) |
| `[1]`, `[2]` | Bracketed | Submit[1] |
| `→1`, `→2` | Arrow | 参照→1 |
| `**1`, `**2` | Double Asterisk | Important**1 |
| `¹`, `²`, `³` | Superscript | Value¹ |

### Note Definition Detection

Notes are automatically extracted from:
- Bottom rows of sheet (last 30 rows scanned)
- Columns A, B, C
- Separate "Notes", "注釈", or "備考" sheets
- Cell comments (if supported by MCP)

### Configuration

Configure note handling in `.f5/config/excel-notes.yaml`:

```yaml
reference_patterns:
  - pattern: "※(\\d+)"
    name: "japanese_kome"
    priority: 1

output:
  format: "footnote"  # footnote | inline | section
  preserve_original_marker: false

auto_detect:
  enabled: true
  bottom_rows_count: 30
```

### Note Parsing Options

| Flag | Description |
|------|-------------|
| `--notes` | Enable note parsing (default: enabled) |
| `--no-notes` | Disable note parsing |
| `--notes-format <format>` | Output format: `footnote`, `inline`, `section` |

### Example Output

**Input Excel:**
```
| 項目名 | 説明 |
|--------|------|
| ユーザー名 | 必須項目※1 |
| メール | 形式チェックあり※2 |

※1: 半角英数字のみ
※2: RFC 5322準拠
```

**Output Markdown (footnote format):**
```markdown
| 項目名 | 説明 |
|--------|------|
| ユーザー名 | 必須項目[^1] |
| メール | 形式チェックあり[^2] |

---
## 注釈 (Notes)

[^1]: 半角英数字のみ
[^2]: RFC 5322準拠
```

## FLAGS

| Flag | Description |
|------|-------------|
| `--type <type>` | Force document type (requirements, basic-design, detail-design, change-request, issues) |
| `--version <version>` | Version label (default: v1.0.0) |
| `--schema <file>` | Custom schema file path |
| `--sheet <name>` | Import specific sheet only |
| `--no-images` | Skip image extraction |
| `--dry-run` | Preview without writing files |
| `--force` | Overwrite existing files |
| `--append` | Append to existing files |
| `--jira` | Generate Jira-compatible CSV and JSON output |
| `--project <key>` | Jira project key for External ID prefix (with --jira) |
| `--include-normal` | Include 正常 (OK) records (with --jira) |
| `--lang <code>` | Translate output to specified language. Codes: `en` (English), `vn` (Vietnamese), `ja` (Japanese). Adds `_{lang}` suffix to filename (e.g., `requirements_vn.md`) |
| `--notes` | Enable note parsing (default: enabled) |
| `--no-notes` | Disable note parsing |
| `--notes-format <format>` | Note output format: `footnote` (default), `inline`, `section` |

## EXAMPLES

### Example 1: Import requirements with auto-detection
```
/f5-import requirements.xlsx
```

### Example 2: Import specific document type
```
/f5-import screens.xlsx --type basic-design
```

### Example 3: Import with custom version
```
/f5-import api-v2.xlsx --version v2.0.0
```

### Example 4: Import specific sheet
```
/f5-import project-docs.xlsx --sheet "要件一覧"
```

### Example 5: Dry run to preview
```
/f5-import requirements.xlsx --dry-run
```

### Example 6: Import with custom schema
```
/f5-import custom-format.xlsx --schema ./my-schema.yaml
```

### Example 7: Import as Jira issues
```
/f5-import issues.xlsx --jira
```

### Example 8: Import with Jira project key
```
/f5-import 問題管理表.xlsx --jira --project MYPROJ
```

### Example 9: Import including OK results
```
/f5-import test_results.xlsx --jira --include-normal
```

### Example 10: Full Jira workflow
```
/f5-import issues.xlsx --jira --project PROJ
/f5-jira-sync --dry-run
# Then in terminal: f5 jira push
```

### Example 11: Import with Vietnamese translation
```
/f5-import requirements.xlsx --lang vn
```
Output: `.f5/specs/srs/v1.0.0/requirements_vn.md`

### Example 12: Import with multiple languages
```
/f5-import requirements.xlsx
/f5-import requirements.xlsx --lang vn
/f5-import requirements.xlsx --lang ja
```
Creates: `requirements.md`, `requirements_vn.md`, `requirements_ja.md`

### Example 13: Import with note preservation
```
/f5-import requirements.xlsx --notes
```
Preserves ※1, *1, (注1) patterns as markdown footnotes.

### Example 14: Import without note parsing
```
/f5-import requirements.xlsx --no-notes
```
Keeps original note markers without conversion.

### Example 15: Import with inline notes format
```
/f5-import requirements.xlsx --notes-format inline
```
Converts notes to inline format instead of footnotes.

## ERROR HANDLING

| Error | Cause | Action |
|-------|-------|--------|
| MCP Excel not available | Server not installed | Show setup instructions |
| File not found | Wrong path | Check .f5/input/ directories |
| Unknown column | Column not in schema | Log warning, skip column |
| Missing required field | Empty required cell | Log error, skip row |
| Invalid value | Value not in mapping | Keep original, log warning |
| Sheet not found | Wrong sheet name | List available sheets |
| Permission denied | File locked | Ask user to close Excel |

## FALLBACK: CSV IMPORT

If MCP Excel is not available, users can export to CSV:

1. Export Excel to CSV (UTF-8)
2. Place in `.f5/input/requirements/`
3. Run `/f5-import requirements.csv`

CSV import uses native file reading without MCP.

---

## MANDATORY: VERIFY OUTPUT AFTER IMPORT

After ANY import command, Claude MUST verify:

### Step 1: Create subfolders FIRST (MANDATORY)
```bash
mkdir -p .f5/specs/srs/v1.0.0/{use-cases,business-rules,images}
mkdir -p .f5/specs/basic-design/v1.0.0/{database,api,screens,batch,diagrams}
mkdir -p .f5/specs/detail-design/v1.0.0/{screens,api,batch,components}
mkdir -p .f5/{csv,issues,input/{requirements,basic-design,detail-design,change-requests,bugs}}
```

### Step 2: Check file location
```bash
ls -la .f5/specs/srs/v1.0.0/
ls -la .f5/specs/basic-design/v1.0.0/
```

### Step 3: If files in wrong location, FIX IMMEDIATELY
```bash
# Fix 1: Files in docs/
if [ -d "docs" ]; then
  mv docs/*.md .f5/specs/srs/v1.0.0/ 2>/dev/null
  rmdir docs 2>/dev/null
fi

# Fix 2: Files in root of specs folder instead of subfolder
if [ -f ".f5/specs/basic-design/v1.0.0/screen-list.md" ]; then
  mv .f5/specs/basic-design/v1.0.0/screen-list.md .f5/specs/basic-design/v1.0.0/screens/
fi
if [ -f ".f5/specs/basic-design/v1.0.0/api-list.md" ]; then
  mv .f5/specs/basic-design/v1.0.0/api-list.md .f5/specs/basic-design/v1.0.0/api/
fi
if [ -f ".f5/specs/basic-design/v1.0.0/table-list.md" ]; then
  mv .f5/specs/basic-design/v1.0.0/table-list.md .f5/specs/basic-design/v1.0.0/database/
fi
```

### Step 4: Report final location
**Correct file locations by import type:**
| Import Type | Correct Location |
|-------------|------------------|
| requirements | `.f5/specs/srs/v1.0.0/requirements.md` |
| screens | `.f5/specs/basic-design/v1.0.0/screens/screen-list.md` |
| api | `.f5/specs/basic-design/v1.0.0/api/api-list.md` |
| tables | `.f5/specs/basic-design/v1.0.0/database/table-list.md` |
| jira | `.f5/csv/{filename}_jira.csv` |

**⛔ Claude MUST NOT report success until files are in correct subfolder!**

---
**Remember:** Always validate imported data with `/f5-spec validate`!
