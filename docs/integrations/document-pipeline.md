# F5 Document Pipeline

Complete guide for the Excel-to-Markdown document pipeline with version control.

---

## Overview

The F5 Document Pipeline converts Excel requirement files into structured Markdown documents with full version control, change tracking, and conflict resolution.

```
Excel Files (.xlsx)
       │
       ▼
┌─────────────────┐
│ Excel Processor │  Parse & auto-detect columns
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Version Manager │  Version control, diff, merge
└────────┬────────┘
         │
         ▼
┌──────────────────┐
│ Document Converter│  Generate Markdown files
└────────┬─────────┘
         │
         ▼
   Markdown Files
   (.f5/docs/vX.X.X/)
```

---

## Quick Start

```bash
# 1. Import your Excel file
f5 doc import requirements.xlsx

# 2. View versions
f5 doc list

# 3. Make changes and import again
f5 doc import requirements-updated.xlsx

# 4. See what changed
f5 doc diff v1.0.0 v1.1.0

# 5. Export to Markdown
f5 doc export v1.1.0 --output ./docs
```

---

## Commands Reference

### `f5 doc import`

Import Excel file(s) and create a new version.

```bash
f5 doc import <files...> [options]

Options:
  -v, --version <version>  Specify version (e.g., v1.2.0)
  -t, --type <type>        Version bump type: major|minor|patch (default: minor)
  -f, --force              Skip confirmation prompt
```

**Examples:**
```bash
f5 doc import requirements.xlsx
f5 doc import v1.xlsx v2.xlsx feedback.xlsx
f5 doc import --version v2.0.0 major-release.xlsx
f5 doc import --type major breaking-changes.xlsx
```

### `f5 doc list`

List all document versions.

```bash
f5 doc list [options]

Options:
  --json    Output as JSON
```

**Output:**
```
📚 Document Versions

---------+---------------+-------------+--------------+--------
Version  | Created       | Requirements | Changes      | Author
---------+---------------+-------------+--------------+--------
v1.0.0   | Nov 26, 2024  | 10          | +10 ~0 -0    | John
v1.1.0   | Nov 27, 2024  | 13          | +3 ~2 -1     | Jane
---------+---------------+-------------+--------------+--------
```

### `f5 doc show`

Show version details.

```bash
f5 doc show <version> [options]

Options:
  --json    Output as JSON
```

### `f5 doc diff`

Compare two versions.

```bash
f5 doc diff <versionA> [versionB] [options]

Options:
  -f, --format <format>  Output format: text|json|markdown (default: text)
```

**Examples:**
```bash
f5 doc diff v1.0.0 v1.1.0           # Compare specific versions
f5 doc diff v1.1.0                  # Compare with previous version
f5 doc diff v1.0.0 v1.1.0 --json    # JSON output
```

### `f5 doc export`

Export version to Markdown files.

```bash
f5 doc export <version> [options]

Options:
  -o, --output <dir>       Output directory
  --format <formats...>    Specific formats: brs|srs|usecases|changelog
```

**Examples:**
```bash
f5 doc export v1.0.0
f5 doc export v1.0.0 --output ./requirements
f5 doc export v1.0.0 --format brs srs
```

### `f5 doc merge`

Merge two versions.

```bash
f5 doc merge <versionA> <versionB> [options]

Options:
  -s, --strategy <strategy>  Merge strategy: prefer_newer|prefer_older|manual
```

**Strategies:**
- `prefer_newer` (default): Keep newer version on conflicts
- `prefer_older`: Keep older version on conflicts
- `manual`: Create conflicts for manual resolution

### `f5 doc conflicts`

Show unresolved conflicts.

```bash
f5 doc conflicts [options]

Options:
  --json    Output as JSON
```

### `f5 doc resolve`

Interactively resolve a conflict.

```bash
f5 doc resolve <conflict-id>
```

**Interactive options:**
- Use Option A
- Use Option B
- Enter custom value
- Skip for now

### `f5 doc rollback`

Rollback to a previous version.

```bash
f5 doc rollback <version> [options]

Options:
  -f, --force    Skip confirmation prompt
```

---

## Column Mapping Reference

The Excel Processor auto-detects columns using these mappings:

### Requirements Sheet

| Field | English Aliases | Vietnamese Aliases |
|-------|-----------------|-------------------|
| ID | id, code, req id, requirement id, req_id | ma, stt, yeu cau id |
| Description | description, content, details, requirement | mo ta, yeu cau, noi dung, chi tiet |
| Priority | priority, p | uu tien, muc do, do uu tien |
| Status | status, state | trang thai, tinh trang |
| Notes | notes, comments, note, remark | ghi chu, binh luan |
| Category | category, type, group | loai, phan loai, nhom |
| Owner | owner, assignee, responsible | nguoi phu trach, nguoi so huu |

### Use Cases Sheet

| Field | English Aliases | Vietnamese Aliases |
|-------|-----------------|-------------------|
| Actor | actor, user | tac nhan, nguoi dung |
| Precondition | precondition, pre-condition | dieu kien truoc |
| Postcondition | postcondition, post-condition | dieu kien sau |
| Steps | steps, main flow, flow | cac buoc, luong |

### Business Rules Sheet

| Field | English Aliases | Vietnamese Aliases |
|-------|-----------------|-------------------|
| Version | version, ver | phien ban |
| Source | source, from, origin | nguon |

---

## Category Detection

Requirements are automatically categorized based on ID prefix or content:

### ID Prefix Rules

| Prefix | Category |
|--------|----------|
| FR-, FR_ | Functional |
| NFR-, NFR_ | Non-Functional |
| BR-, BR_ | Business Rule |
| UC-, UC_ | Use Case |

### Content Detection

If no ID prefix, keywords in description trigger categories:
- **Non-Functional:** performance, security, scalability, availability
- **Functional:** Default for most requirements

---

## Version Strategy

F5 uses semantic versioning (vX.Y.Z):

| Bump Type | When to Use | Example |
|-----------|-------------|---------|
| `major` | Breaking changes, major restructuring | v1.0.0 → v2.0.0 |
| `minor` | New requirements added (default) | v1.0.0 → v1.1.0 |
| `patch` | Minor fixes, clarifications | v1.0.0 → v1.0.1 |

---

## Generated Documents

### BRS (Business Requirements Specification)

High-level business requirements document:
- Executive summary
- Category distribution
- Requirements grouped by category
- Priority statistics

### SRS (Software Requirements Specification)

Detailed software requirements:
- Document metadata
- Complete requirement details
- Technical specifications
- Traceability information

### Use Cases Document

Use case specifications:
- Actor information
- Pre/post conditions
- Main flow steps
- Alternative flows

### Changelog

Version-to-version changes:
- New requirements added
- Modified requirements (with old/new values)
- Deleted requirements
- Statistics

### Traceability Matrix

Requirements traceability:
- ID to source file mapping
- Category distribution
- Hash values for change detection

### Summary

Executive summary:
- Total requirements
- Category breakdown
- Priority distribution
- Source files

---

## Storage Structure

```
.f5/
├── versions/
│   ├── metadata.json          # Version registry
│   ├── v1.0.0/
│   │   ├── data.json          # Requirements data
│   │   └── sources/           # Source file backups
│   │       └── requirements.xlsx
│   └── v1.1.0/
│       ├── data.json
│       └── sources/
│
└── docs/
    ├── v1.0.0/
    │   ├── brs.md
    │   ├── srs.md
    │   ├── use-cases.md
    │   ├── traceability.md
    │   └── summary.md
    └── v1.1.0/
        ├── brs.md
        ├── srs.md
        ├── changelog.md
        └── ...
```

---

## Conflict Resolution Guide

### When Conflicts Occur

Conflicts occur when merging two versions that have different changes to the same requirement.

### Conflict Structure

```json
{
  "id": "conflict-123456",
  "requirement_id": "REQ-001",
  "version_a": {
    "version": "v1.1.0",
    "value": { "description": "Version A text..." }
  },
  "version_b": {
    "version": "v1.2.0",
    "value": { "description": "Version B text..." }
  },
  "status": "pending"
}
```

### Resolution Options

1. **Use A**: Keep version A's value
2. **Use B**: Keep version B's value
3. **Custom**: Enter merged/custom value
4. **Skip**: Leave for later resolution

### Best Practices

1. Review both versions carefully before resolving
2. Consider the context and intent of each change
3. Document the reason for your resolution
4. Run `f5 doc conflicts` regularly to check pending items

---

## Best Practices

### Excel File Organization

1. **One sheet per type**: Requirements, Use Cases, Business Rules
2. **Consistent naming**: Use clear column headers
3. **Unique IDs**: Ensure each requirement has a unique ID
4. **Complete descriptions**: Detailed descriptions help with tracking

### Version Management

1. **Import regularly**: Don't accumulate too many changes
2. **Use appropriate bump types**: Major for breaking changes
3. **Review diffs**: Always check changes before import
4. **Backup source files**: Keep original Excel files

### Conflict Prevention

1. **Single source of truth**: Avoid parallel edits
2. **Clear ownership**: Assign requirement owners
3. **Regular syncs**: Import changes frequently
4. **Communication**: Coordinate with team on major changes

---

## Troubleshooting

### Column Not Detected

**Problem:** A column in your Excel isn't being detected.

**Solution:** Check if the column header matches any alias in the mapping reference. You can add custom aliases by configuring the ExcelProcessor.

### Missing Requirements

**Problem:** Some rows are being skipped.

**Solution:** Ensure rows have a description. Empty rows are skipped by default.

### Version Conflicts

**Problem:** Too many conflicts when merging.

**Solution:** Consider using `prefer_newer` strategy, or break down changes into smaller versions.

### Export Issues

**Problem:** Exported files are empty or missing.

**Solution:** Check that the version exists with `f5 doc show <version>`.

---

## API Reference

For programmatic access, import the modules directly:

```typescript
import { ExcelProcessor } from '@f5/cli/core/excel-processor';
import { VersionManager } from '@f5/cli/core/version-manager';
import { DocumentConverter } from '@f5/cli/core/document-converter';

// Parse Excel
const processor = new ExcelProcessor();
const result = processor.parseFiles(['requirements.xlsx']);

// Manage versions
const manager = new VersionManager();
const version = manager.createVersion({
  sourceFiles: ['requirements.xlsx'],
  requirements: result.allRequirements,
});

// Generate documents
const converter = new DocumentConverter();
const docs = converter.generate(result, version.id, null);
```

---

## Integration with F5 Workflow

The Document Pipeline integrates with the F5 spec-driven workflow:

```
1. Gather requirements in Excel
2. f5 doc import → Creates versioned requirements
3. /f5-spec --from-doc → Generate SRS from imported data
4. /f5-design → Create design documents
5. f5 doc export → Export for review
6. f5 doc import → Import feedback/updates
7. f5 doc diff → Review changes
```

---

**F5 Framework** | **Document Pipeline** | **v1.0.0**
