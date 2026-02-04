---
description: Quản lý Q&A tracking trong workflow
argument-hint: <raise|list|resolve|show> [options]
---

# /f5-question - Q&A Tracking Command

Quản lý câu hỏi và clarification requests trong workflow.

## Usage

```bash
/f5-question raise --from <source> --severity <level> --tag <tag>
/f5-question list [--status open|resolved|all] [--tag <tag>]
/f5-question show <Q-ID>
/f5-question resolve <Q-ID> --answer "<answer>"
```

## Arguments

- `raise`: Tạo câu hỏi mới
- `list`: Xem danh sách Q&A
- `show`: Xem chi tiết một Q&A
- `resolve`: Đánh dấu đã giải đáp

---

## STEP 1: PARSE SUBCOMMAND

| Pattern | Action |
|---------|--------|
| `raise` | Go to [ACTION: RAISE] |
| `list` | Go to [ACTION: LIST] |
| `show <Q-ID>` | Go to [ACTION: SHOW] |
| `resolve <Q-ID>` | Go to [ACTION: RESOLVE] |
| (default) | Go to [ACTION: HELP] |

---

## ACTION: RAISE

### Tạo câu hỏi mới

**Parameters:**
- `--from <source>`: Nguồn của câu hỏi (required)
  - `input`, `classification`, `DI-SCR-xxx` (Phase 1)
  - `specs`, `srs`, `use-cases` (Phase 2)
  - `design`, `basic-design`, `detail-design` (Phase 3)
  - `technical-design`, `api-contract`, `data-model` (Phase 4)
- `--severity <level>`: Mức độ nghiêm trọng (required)
  - `blocking`: Không thể tiếp tục implement
  - `non-blocking`: Có thể implement với assumption
- `--tag <tag>`: Nhãn phân loại (required)
  - `DESIGN-GAP`, `MISSING-STATE`, `MISSING-ERROR`, `MISSING-VALIDATION`
  - `MISSING-EDGE-CASE`, `BUSINESS-RULE`, `REQUIREMENT-UNCLEAR`
  - `CONSTRAINT`, `DATA-FORMAT`, `INTEGRATION`, `PERFORMANCE`, `SECURITY`
- `--source <file>`: File/artifact cụ thể (optional)
- `--assignee <role>`: Người cần trả lời (optional, default: BA)

### Process:

1. **Đọc _index.yaml để lấy next ID:**
   ```bash
   # Check .f5/questions/_index.yaml
   # Get last Q-ID, increment by 1
   ```

2. **Tạo file Q&A mới:**
   ```
   .f5/questions/open/Q-{ID}.md
   ```

3. **Update _index.yaml**

4. **Hiển thị kết quả**

### Output Format:

```
╔═══════════════════════════════════════════════════════════════════════════╗
║  📝 TẠO CÂU HỎI MỚI                                                       ║
╠═══════════════════════════════════════════════════════════════════════════╣

ID: Q-{ID}
Trạng thái: 🟡 OPEN

Metadata:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| Field | Value |
|-------|-------|
| **From** | {source} |
| **Source File** | {source_file} |
| **Severity** | {severity} |
| **Tag** | {tag} |
| **Assignee** | {assignee} |
| **Created** | {date} |

NỘI DUNG CÂU HỎI:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Claude sẽ prompt user nhập nội dung câu hỏi]

FILE ĐÃ TẠO:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

→ .f5/questions/open/Q-{ID}.md
→ .f5/questions/_index.yaml (updated)

BƯỚC TIẾP THEO:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Chờ BA/Customer trả lời trong file Q-{ID}.md
2. Sau khi có answer, chạy: /f5-question resolve Q-{ID}

╚═══════════════════════════════════════════════════════════════════════════╝
```

### Q&A File Template:

```markdown
# Question: Q-{ID}

## Metadata

| Field | Value |
|-------|-------|
| **ID** | Q-{ID} |
| **Created** | {date} |
| **From** | {from} |
| **Source** | {source_file} |
| **Severity** | {severity} |
| **Tag** | {tag} |
| **Status** | 🟡 OPEN |
| **Assignee** | {assignee} |

## Câu hỏi

{question_content}

## Bối cảnh

- Phase hiện tại: {current_phase}
- File liên quan: {related_files}
- Gaps detected: {gaps}

## Options (nếu có)

1. Option A: ...
2. Option B: ...
3. Option C: ...

---

## Trả lời

_(Chờ BA/Customer trả lời)_

## Resolved Info

| Field | Value |
|-------|-------|
| **Resolved By** | - |
| **Resolved Date** | - |
| **Decision** | - |
```

---

## ACTION: LIST

### Xem danh sách Q&A

**Parameters:**
- `--status <status>`: Filter theo status (optional)
  - `open`: Chỉ câu hỏi đang mở (default)
  - `resolved`: Chỉ câu hỏi đã giải đáp
  - `all`: Tất cả
- `--tag <tag>`: Filter theo tag (optional)
- `--severity <level>`: Filter theo severity (optional)
- `--from <source>`: Filter theo source (optional)

### Process:

1. **Đọc _index.yaml**
2. **Apply filters**
3. **Hiển thị danh sách**

### Output Format:

```
╔═══════════════════════════════════════════════════════════════════════════╗
║  📋 DANH SÁCH Q&A                                                         ║
╠═══════════════════════════════════════════════════════════════════════════╣

Filter: status={status}, tag={tag}

TÓM TẮT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| Metric | Count |
|--------|-------|
| Tổng số | {total} |
| 🟡 Open | {open} |
| ✅ Resolved | {resolved} |
| 🔴 Blocking | {blocking} |

DANH SÁCH:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| ID | Status | Severity | From | Tag | Summary |
|----|--------|----------|------|-----|---------|
| Q-001 | 🟡 Open | blocking | DI-SCR-0203 | MISSING-STATE | State transitions? |
| Q-002 | 🟡 Open | non-blocking | DI-SCR-0203 | MISSING-ERROR | Error handling? |
| Q-003 | ✅ Resolved | blocking | srs | BUSINESS-RULE | Session timeout |

COMMANDS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/f5-question show Q-001      # Xem chi tiết
/f5-question resolve Q-001   # Đánh dấu đã giải đáp

╚═══════════════════════════════════════════════════════════════════════════╝
```

---

## ACTION: SHOW

### Xem chi tiết một Q&A

**Parameters:**
- `<Q-ID>`: ID của câu hỏi (required)

### Process:

1. **Tìm file Q&A:**
   - Check `.f5/questions/open/Q-{ID}.md`
   - Nếu không có, check `.f5/questions/resolved/Q-{ID}.md`
2. **Đọc và hiển thị nội dung**

### Output Format:

```
╔═══════════════════════════════════════════════════════════════════════════╗
║  📝 CHI TIẾT Q&A: Q-{ID}                                                  ║
╠═══════════════════════════════════════════════════════════════════════════╣

METADATA:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| Field | Value |
|-------|-------|
| **ID** | Q-{ID} |
| **Status** | 🟡 OPEN / ✅ RESOLVED |
| **Created** | {date} |
| **From** | {from} |
| **Source** | {source_file} |
| **Severity** | {severity} |
| **Tag** | {tag} |
| **Assignee** | {assignee} |

CÂU HỎI:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{question_content}

BỐI CẢNH:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{context}

TRẢ LỜI:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{answer or "Chờ BA/Customer trả lời"}

FILE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

→ .f5/questions/{open|resolved}/Q-{ID}.md

╚═══════════════════════════════════════════════════════════════════════════╝
```

---

## ACTION: RESOLVE

### Đánh dấu Q&A đã giải đáp

**Parameters:**
- `<Q-ID>`: ID của câu hỏi (required)
- `--answer "<answer>"`: Câu trả lời (optional - có thể nhập sau)
- `--by "<name>"`: Người trả lời (optional)

### Process:

1. **Tìm file Q&A trong open/**
2. **Update nội dung với answer**
3. **Move file từ open/ → resolved/**
4. **Update _index.yaml**
5. **Hiển thị kết quả**

### Output Format:

```
╔═══════════════════════════════════════════════════════════════════════════╗
║  ✅ Q&A ĐÃ GIẢI QUYẾT                                                     ║
╠═══════════════════════════════════════════════════════════════════════════╣

ID: Q-{ID}
Trạng thái: ✅ RESOLVED

TRẢ LỜI:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{answer}

RESOLVED INFO:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| Field | Value |
|-------|-------|
| **Resolved By** | {by} |
| **Resolved Date** | {date} |

FILE ĐÃ CHUYỂN:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

.f5/questions/open/Q-{ID}.md → .f5/questions/resolved/Q-{ID}.md

BƯỚC TIẾP THEO:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Áp dụng Q&A vào specs (nếu ở Phase 4):
/f5-design apply-qa Q-{ID}

╚═══════════════════════════════════════════════════════════════════════════╝
```

---

## ACTION: HELP

### Hiển thị help

```
╔═══════════════════════════════════════════════════════════════════════════╗
║  ❓ F5-QUESTION - Q&A TRACKING                                            ║
╠═══════════════════════════════════════════════════════════════════════════╣

COMMANDS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/f5-question raise --from <source> --severity <level> --tag <tag>
  Tạo câu hỏi mới

/f5-question list [--status open|resolved|all]
  Xem danh sách Q&A

/f5-question show <Q-ID>
  Xem chi tiết một Q&A

/f5-question resolve <Q-ID> --answer "<answer>"
  Đánh dấu đã giải đáp

PARAMETERS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

--from <source>:
  • input, classification, DI-SCR-xxx (Phase 1)
  • specs, srs, use-cases (Phase 2)
  • design, basic-design, detail-design (Phase 3)
  • technical-design, api-contract, data-model (Phase 4)

--severity <level>:
  • blocking: Không thể tiếp tục implement
  • non-blocking: Có thể implement với assumption

--tag <tag>:
  • DESIGN-GAP, MISSING-STATE, MISSING-ERROR
  • MISSING-VALIDATION, MISSING-EDGE-CASE
  • BUSINESS-RULE, REQUIREMENT-UNCLEAR
  • CONSTRAINT, DATA-FORMAT, INTEGRATION
  • PERFORMANCE, SECURITY

EXAMPLES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Tạo Q&A từ classification
/f5-question raise --from classification --severity blocking --tag MISSING-STATE

# Tạo Q&A từ specific file
/f5-question raise --from DI-SCR-0203 --severity blocking --tag MISSING-STATE

# Xem danh sách Q&A đang open
/f5-question list --status open

# Xem Q&A theo tag
/f5-question list --tag MISSING-STATE

# Xem chi tiết
/f5-question show Q-001

# Giải đáp Q&A
/f5-question resolve Q-001 --answer "Session timeout là 30 phút"

╚═══════════════════════════════════════════════════════════════════════════╝
```

---

## INTEGRATION

### Với Workflow

```bash
# Phase 1: Input
/f5-classify .f5/input/raw/excel/0203/
/f5-question raise --from DI-SCR-0203 --severity blocking --tag MISSING-STATE
/f5-gate check D1

# Phase 4: Technical Design
/f5-design generate technical-design
/f5-question raise --from technical-design --severity blocking --tag BUSINESS-RULE
# ... wait for answer ...
/f5-question resolve Q-001 --answer "..."
/f5-design apply-qa Q-001
/f5-gate check D5
```

### Với Gates

- **D1 Gate:** Cảnh báo nếu có Q&A chưa resolved từ classification
- **D5 Gate:** Block nếu có blocking Q&A chưa resolved

---

## FILES

### _index.yaml Structure

```yaml
# .f5/questions/_index.yaml
questions:
  last_id: 3
  
  summary:
    total: 3
    open: 2
    resolved: 1
    blocking: 1
    non_blocking: 1
    
  open:
    - id: Q-002
      severity: blocking
      from: DI-SCR-0203
      tag: MISSING-STATE
      created: 2025-12-23
      assignee: BA
      summary: "State transitions cho màn hình?"
      
    - id: Q-003
      severity: non-blocking
      from: DI-SCR-0203
      tag: MISSING-ERROR
      created: 2025-12-23
      assignee: BA
      summary: "Error handling scenarios?"

  resolved:
    - id: Q-001
      severity: blocking
      from: srs
      tag: BUSINESS-RULE
      created: 2025-12-22
      resolved_date: 2025-12-23
      resolved_by: BA - Hiền
      summary: "Session timeout?"
      answer: "30 phút"

  by_tag:
    MISSING-STATE: [Q-002]
    MISSING-ERROR: [Q-003]
    BUSINESS-RULE: [Q-001]
    
  by_severity:
    blocking: [Q-001, Q-002]
    non_blocking: [Q-003]
```
