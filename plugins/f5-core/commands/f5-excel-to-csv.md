---
description: Convert Excel files to CSV for AI processing
argument-hint: [input-path] [--all-sheets] [--force]
---

# /f5-excel-to-csv

## ARGUMENTS: $ARGUMENTS

---

# EXCEL TO CSV CONVERTER

Chuyển đổi Excel files sang CSV để AI có thể đọc nội dung.

## VÌ SAO CẦN CONVERT?

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         EXCEL BINARY LIMITATION                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  EXCEL (.xlsx)                     CSV (.csv)                                   │
│  ┌─────────────┐                   ┌─────────────┐                              │
│  │ Binary ZIP  │    Convert →      │ Plain Text  │                              │
│  │ XML inside  │                   │ AI readable │                              │
│  └─────────────┘                   └─────────────┘                              │
│                                                                                  │
│  AI Access:                        AI Access:                                   │
│  ❌ Cannot read                    ✅ Full read                                 │
│     cell content                      all content                               │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## USAGE

### Option 1: PowerShell (yêu cầu Excel installed)

```powershell
# Convert tất cả Excel files (sheet đầu tiên)
.\scripts\excel-to-csv.ps1

# Convert tất cả sheets
.\scripts\excel-to-csv.ps1 -AllSheets

# Custom input/output paths
.\scripts\excel-to-csv.ps1 -InputPath ".f5\input\raw\excel\0203" -OutputPath ".f5\input\raw\csv"

# Overwrite existing files
.\scripts\excel-to-csv.ps1 -Force
```

### Option 2: Python (không cần Excel)

```bash
# Install dependencies (chỉ lần đầu)
pip install openpyxl pandas

# Convert tất cả Excel files
python scripts/excel-to-csv.py

# Convert tất cả sheets
python scripts/excel-to-csv.py --all-sheets

# Custom paths
python scripts/excel-to-csv.py .f5/input/raw/excel .f5/input/raw/csv

# Overwrite
python scripts/excel-to-csv.py --force
```

## WORKFLOW INTEGRATION

```
BEFORE CLASSIFY:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Step 1: Convert Excel → CSV
  python scripts/excel-to-csv.py .f5/input/raw/excel .f5/input/raw/csv --all-sheets

Step 2: Classify với CSV path
  /f5-classify .f5/input/raw/csv/

Step 3: AI có thể đọc 100% content
  → Extraction rate: HIGH
  → Classification: COMPLETE
```

## OUTPUT STRUCTURE

```
.f5/input/raw/
├── excel/                          # Original Excel files
│   └── 0203/
│       ├── 画面設計書_0203.xlsx
│       └── 詳細設計書_0203.xlsx
│
└── csv/                            # Converted CSV files
    ├── 画面設計書_0203.csv         # First sheet
    ├── 画面設計書_0203_Sheet2.csv  # (with --all-sheets)
    ├── 詳細設計書_0203.csv
    └── ...
```

## TROUBLESHOOTING

| Issue | Solution |
|-------|----------|
| PowerShell fails "Excel not found" | Use Python script instead |
| Python "ModuleNotFoundError" | Run `pip install openpyxl pandas` |
| Japanese characters corrupted | CSV uses UTF-8-BOM, open with proper encoding |
| Large file timeout | Split into smaller ranges or sheets |

## COMPARISON

| Aspect | PowerShell | Python |
|--------|------------|--------|
| Requires Excel | ✅ Yes | ❌ No |
| Speed | 🟢 Fast | 🟢 Fast |
| Japanese support | ✅ Yes | ✅ Yes |
| Dependencies | Excel COM | openpyxl, pandas |
| Recommended | Windows with Excel | Cross-platform |
