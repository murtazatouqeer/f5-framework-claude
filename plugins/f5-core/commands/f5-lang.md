---
description: Set language preference for F5 Framework output
argument-hint: <en|vi|ja> [--global|--project|--reset]
---

# /f5-lang - Language Preference Command

Set the display language for F5 Framework output.

## ARGUMENTS
The user's request is: $ARGUMENTS

## OVERVIEW

F5 Framework supports 3 languages:
- `en` - English (default)
- `vi` - Tiếng Việt
- `ja` - 日本語

Language can be set at:
1. **Global level** - User preference across all projects (`~/.f5/preferences.yaml`)
2. **Project level** - Override for specific project (`.f5/config.json`)

## STEP 1: PARSE ARGUMENTS

| Pattern | Action |
|---------|--------|
| (no args) | **SHOW_CURRENT** |
| `en` or `vi` or `ja` | **SET_GLOBAL** |
| `<lang> --project` | **SET_PROJECT** |
| `--reset` | **RESET_TO_DEFAULT** |

---

## ACTION: SHOW_CURRENT

### `/f5-lang`

Show current language settings.

**Process:**

1. Read global preference from `~/.f5/preferences.yaml`
2. Read project preference from `.f5/config.json` (if exists)
3. Determine active language

**Check Global Preference:**
```bash
GLOBAL_LANG="en"
GLOBAL_LANG_NAME="English"

if [ -f ~/.f5/preferences.yaml ]; then
  GLOBAL_LANG=$(grep '^language:' ~/.f5/preferences.yaml 2>/dev/null | sed 's/language:[[:space:]]*"\{0,1\}\([^"]*\)"\{0,1\}/\1/')
  if [ -z "$GLOBAL_LANG" ]; then
    GLOBAL_LANG="en"
  fi
fi

case "$GLOBAL_LANG" in
  "vi") GLOBAL_LANG_NAME="Tiếng Việt" ;;
  "ja") GLOBAL_LANG_NAME="日本語" ;;
  *) GLOBAL_LANG_NAME="English" ;;
esac
```

**Check Project Preference:**
```bash
PROJECT_LANG=""
PROJECT_LANG_NAME="(not set)"

if [ -f ".f5/config.json" ]; then
  PROJECT_LANG=$(jq -r '.language // empty' .f5/config.json 2>/dev/null)
  if [ -n "$PROJECT_LANG" ] && [ "$PROJECT_LANG" != "null" ]; then
    case "$PROJECT_LANG" in
      "vi") PROJECT_LANG_NAME="Tiếng Việt" ;;
      "ja") PROJECT_LANG_NAME="日本語" ;;
      "en") PROJECT_LANG_NAME="English" ;;
    esac
  else
    PROJECT_LANG=""
    PROJECT_LANG_NAME="(not set)"
  fi
fi
```

**Determine Active Language:**
```bash
if [ -n "$PROJECT_LANG" ]; then
  ACTIVE_LANG="$PROJECT_LANG"
  ACTIVE_SOURCE="project (.f5/config.json)"
else
  ACTIVE_LANG="$GLOBAL_LANG"
  ACTIVE_SOURCE="global (~/.f5/preferences.yaml)"
fi
```

**Output:**

```markdown
## 🌐 F5 Language Settings

| Scope | Language | Source |
|-------|----------|--------|
| Global | {{GLOBAL_LANG}} ({{GLOBAL_LANG_NAME}}) | ~/.f5/preferences.yaml |
| Project | {{PROJECT_LANG}} ({{PROJECT_LANG_NAME}}) | .f5/config.json |
| **Active** | **{{ACTIVE_LANG}}** | {{ACTIVE_SOURCE}} |

### Available Languages
- `en` - English
- `vi` - Tiếng Việt
- `ja` - 日本語

### Usage
```bash
# Set global language
/f5-lang vi

# Set project language (overrides global)
/f5-lang ja --project

# Reset to default
/f5-lang --reset
```
```

---

## ACTION: SET_GLOBAL

### `/f5-lang <en|vi|ja>`

Set global language preference.

**Process:**

1. Validate language code (en, vi, ja)
2. Create `~/.f5/` directory if not exists
3. Create or update `~/.f5/preferences.yaml`
4. Show confirmation

**Validation:**
```bash
LANG_INPUT="$1"

case "$LANG_INPUT" in
  "en") LANG_NAME="English" ;;
  "vi") LANG_NAME="Tiếng Việt" ;;
  "ja") LANG_NAME="日本語" ;;
  *)
    echo "❌ Invalid language code: $LANG_INPUT"
    echo "Available: en, vi, ja"
    exit 1
    ;;
esac
```

**Create/Update Global Preference:**
```bash
# Ensure ~/.f5 directory exists
mkdir -p ~/.f5

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Check if file exists
if [ -f ~/.f5/preferences.yaml ]; then
  # Update existing file - replace language line
  sed -i.bak "s/^language:.*/language: \"$LANG_INPUT\"/" ~/.f5/preferences.yaml
  sed -i.bak "s/^updated_at:.*/updated_at: \"$TIMESTAMP\"/" ~/.f5/preferences.yaml
  rm -f ~/.f5/preferences.yaml.bak
else
  # Create new file
  cat > ~/.f5/preferences.yaml << EOF
version: "1.0.0"
language: "$LANG_INPUT"
created_at: "$TIMESTAMP"
updated_at: "$TIMESTAMP"
EOF
fi

echo "✅ Language set to: $LANG_NAME (global)"
```

**Output:**

```markdown
## ✅ Language Set

**Language:** {{LANGUAGE}} - {{LANGUAGE_NAME}}
**Scope:** Global (all projects)
**File:** ~/.f5/preferences.yaml

All F5 commands will now display in {{LANGUAGE_NAME}}.

To override for specific project:
```bash
/f5-lang {{OTHER_LANG}} --project
```
```

---

## ACTION: SET_PROJECT

### `/f5-lang <en|vi|ja> --project`

Set project-specific language (overrides global).

**Process:**

1. Check if `.f5/config.json` exists
2. Validate language code
3. Add or update `language` field
4. Show confirmation

**Check Project:**
```bash
if [ ! -f ".f5/config.json" ]; then
  echo "❌ Not in F5 project. Run /f5-init first."
  exit 1
fi
```

**Update Project Config:**
```bash
LANG_INPUT="$1"

case "$LANG_INPUT" in
  "en") LANG_NAME="English" ;;
  "vi") LANG_NAME="Tiếng Việt" ;;
  "ja") LANG_NAME="日本語" ;;
  *)
    echo "❌ Invalid language code: $LANG_INPUT"
    exit 1
    ;;
esac

# Update config.json using jq
jq ".language = \"$LANG_INPUT\"" .f5/config.json > .f5/config.json.tmp
mv .f5/config.json.tmp .f5/config.json

echo "✅ Language set to: $LANG_NAME (project)"
```

**Output:**

```markdown
## ✅ Project Language Set

**Language:** {{LANGUAGE}} - {{LANGUAGE_NAME}}
**Scope:** This project only
**File:** .f5/config.json

This project will use {{LANGUAGE_NAME}}, overriding global preference.

To remove project override:
```bash
# Edit .f5/config.json and remove "language" field
# Or run: /f5-lang --reset
```
```

---

## ACTION: RESET_TO_DEFAULT

### `/f5-lang --reset`

Reset language to default (English).

**Process:**

1. Set language to "en" in `~/.f5/preferences.yaml`
2. Remove language from `.f5/config.json` if exists
3. Show confirmation

**Reset:**
```bash
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Reset global
if [ -f ~/.f5/preferences.yaml ]; then
  sed -i.bak "s/^language:.*/language: \"en\"/" ~/.f5/preferences.yaml
  sed -i.bak "s/^updated_at:.*/updated_at: \"$TIMESTAMP\"/" ~/.f5/preferences.yaml
  rm -f ~/.f5/preferences.yaml.bak
  echo "✅ Global language reset to: en (English)"
fi

# Reset project
if [ -f .f5/config.json ]; then
  jq 'del(.language)' .f5/config.json > .f5/config.json.tmp
  mv .f5/config.json.tmp .f5/config.json
  echo "✅ Project language override removed"
fi

echo "✅ Language reset to default (en)"
```

**Output:**

```markdown
## ✅ Language Reset

Language has been reset to default (English).

| Scope | Language |
|-------|----------|
| Global | en (English) |
| Project | (uses global) |
```

---

## LANGUAGE RESOLUTION

Priority (highest to lowest):

1. Command flag: `--lang <code>` (one-time override)
2. Project config: `.f5/config.json` → `language`
3. Global preference: `~/.f5/preferences.yaml` → `language`
4. Default: `en`

```bash
resolve_language() {
  # 1. Check command flag
  if [ -n "$LANG_FLAG" ]; then
    echo "$LANG_FLAG"
    return
  fi

  # 2. Check project config
  if [ -f ".f5/config.json" ]; then
    PROJECT_LANG=$(jq -r '.language // empty' .f5/config.json 2>/dev/null)
    if [ -n "$PROJECT_LANG" ] && [ "$PROJECT_LANG" != "null" ]; then
      echo "$PROJECT_LANG"
      return
    fi
  fi

  # 3. Check global preference
  if [ -f ~/.f5/preferences.yaml ]; then
    GLOBAL_LANG=$(grep '^language:' ~/.f5/preferences.yaml 2>/dev/null | sed 's/language:[[:space:]]*"\{0,1\}\([^"]*\)"\{0,1\}/\1/')
    if [ -n "$GLOBAL_LANG" ]; then
      echo "$GLOBAL_LANG"
      return
    fi
  fi

  # 4. Default
  echo "en"
}
```

---

## VALIDATION

Valid language codes:
- `en` - English
- `vi` - Tiếng Việt
- `ja` - 日本語

If invalid code provided:

```markdown
## ❌ Invalid Language

"{{INPUT}}" is not a valid language code.

Available languages:
- `en` - English
- `vi` - Tiếng Việt
- `ja` - 日本語

Usage:
```bash
/f5-lang vi
/f5-lang ja --project
```
```

---

## EXAMPLES

```bash
# View current settings
/f5-lang

# Set global to Vietnamese
/f5-lang vi

# Set project to Japanese
/f5-lang ja --project

# Reset to English
/f5-lang --reset

# One-time override in other commands
/f5-status --lang ja
```

---

## INTEGRATION WITH OTHER COMMANDS

After setting language, these commands will use the selected language:

| Command | Affected Output |
|---------|-----------------|
| `/f5-load` | Project summary, gate names, status |
| `/f5-status` | Dashboard, metrics, labels |
| `/f5-req` | List, show, messages |
| `/f5-gate` | Check results, status |
| `/f5-init` | Prompts, messages |

**Note:** Technical content (stack traces, config files) remains in English.

---

## TRANSLATION REFERENCE

### Gate Names

| Gate | en | vi | ja |
|------|----|----|-----|
| D1 | Research Complete | Nghiên cứu hoàn thành | 調査完了 |
| D2 | SRS Approved | SRS được duyệt | SRS承認済 |
| D3 | Basic Design Approved | Thiết kế cơ bản được duyệt | 基本設計承認済 |
| D4 | Detail Design Approved | Thiết kế chi tiết được duyệt | 詳細設計承認済 |
| G2 | Implementation Ready | Triển khai hoàn thành | 実装完了 |
| G3 | Testing Complete | Kiểm thử hoàn thành | テスト完了 |
| G4 | Deployment Ready | Sẵn sàng triển khai | デプロイ準備完了 |

### Status Labels

| Status | en | vi | ja |
|--------|----|----|-----|
| pending | Pending | Đang chờ | 保留中 |
| in_progress | In Progress | Đang tiến hành | 進行中 |
| completed | Completed | Hoàn thành | 完了 |
| blocked | Blocked | Bị chặn | ブロック中 |
