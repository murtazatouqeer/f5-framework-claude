# F5 Framework - Pre-commit Hooks for Testing

> **Version:** 1.0.0
> **Purpose:** Enforce testing standards before commits

---

## Overview

F5 Framework supports pre-commit hooks to ensure code quality and test coverage before allowing commits.

---

## Quick Setup

### Using Husky (Recommended)

```bash
# Install husky
npm install --save-dev husky

# Initialize husky
npx husky init

# Add pre-commit hook
echo "npm run test:staged" > .husky/pre-commit
```

### Manual .git/hooks Setup

```bash
# Create pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/sh

# F5 Framework Pre-commit Hook
echo "🧪 Running pre-commit tests..."

# Run staged tests
npm run test:staged

# Check exit code
if [ $? -ne 0 ]; then
  echo "❌ Tests failed. Commit blocked."
  exit 1
fi

echo "✅ All tests passed. Proceeding with commit."
EOF

chmod +x .git/hooks/pre-commit
```

---

## Configuration

### package.json Scripts

```json
{
  "scripts": {
    "test:staged": "jest --findRelatedTests --passWithNoTests",
    "test:coverage": "jest --coverage --coverageThreshold='{\"global\":{\"branches\":75,\"functions\":80,\"lines\":80,\"statements\":80}}'",
    "lint": "eslint . --ext .ts,.tsx",
    "typecheck": "tsc --noEmit",
    "pre-commit": "npm run lint && npm run typecheck && npm run test:staged"
  }
}
```

### lint-staged Configuration

```json
{
  "lint-staged": {
    "*.{ts,tsx}": [
      "eslint --fix",
      "jest --findRelatedTests --passWithNoTests"
    ],
    "*.{json,md}": [
      "prettier --write"
    ]
  }
}
```

---

## Pre-commit Hook Levels

### Level 1: Quick (Default)

```yaml
pre_commit_level_1:
  name: "Quick Check"
  time: "~5 seconds"
  checks:
    - lint: "Staged files only"
    - typecheck: "Changed files"
  skip_if: "WIP commit message"
```

### Level 2: Standard

```yaml
pre_commit_level_2:
  name: "Standard Check"
  time: "~30 seconds"
  checks:
    - lint: "Staged files"
    - typecheck: "Full project"
    - unit_tests: "Related to changes"
  enable: "--standard flag"
```

### Level 3: Thorough (G3 Gate)

```yaml
pre_commit_level_3:
  name: "Thorough Check"
  time: "~2 minutes"
  checks:
    - lint: "Full project"
    - typecheck: "Full project"
    - unit_tests: "Full suite"
    - coverage: "Check threshold"
  enable: "--thorough flag or G3 gate"
```

---

## Integration with F5 Commands

### Automatic Hook Management

```bash
# Enable pre-commit hooks
/f5-test hooks enable

# Set hook level
/f5-test hooks level standard

# Disable temporarily
/f5-test hooks disable

# Check hook status
/f5-test hooks status
```

### Hook Configuration (.f5/testing/config.yaml)

```yaml
testing:
  pre_commit:
    enabled: true
    level: "standard"  # quick | standard | thorough

    # Skip conditions
    skip_patterns:
      - "WIP:"
      - "[skip ci]"
      - "[no-test]"

    # Checks by level
    levels:
      quick:
        lint: true
        typecheck: false
        tests: false

      standard:
        lint: true
        typecheck: true
        tests: "related"  # Only tests related to changed files

      thorough:
        lint: true
        typecheck: true
        tests: "all"
        coverage: 80
```

---

## Workflow Integration

### Recommended Workflow

```
┌─────────────────────────────────────────────────────────────┐
│              PRE-COMMIT WORKFLOW                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  git add <files>                                            │
│       │                                                      │
│       ▼                                                      │
│  git commit -m "message"                                    │
│       │                                                      │
│       ▼                                                      │
│  ┌─────────────────────────────────────────────┐            │
│  │ PRE-COMMIT HOOK                             │            │
│  │ 1. Lint staged files                        │            │
│  │ 2. Type check                               │            │
│  │ 3. Run related tests                        │            │
│  └─────────────────────────────────────────────┘            │
│       │                                                      │
│       ├── ✅ Pass → Commit proceeds                         │
│       │                                                      │
│       └── ❌ Fail → Commit blocked                          │
│                    │                                         │
│                    ▼                                         │
│              Fix issues → Try commit again                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Skip Hook (Emergency)

```bash
# Skip pre-commit hook (use sparingly!)
git commit --no-verify -m "hotfix: emergency fix"

# Or with skip pattern in message
git commit -m "WIP: work in progress [skip ci]"
```

---

## G3 Gate Integration

When working toward G3 (Testing Complete) gate:

```yaml
g3_pre_commit:
  # Automatically upgrade to thorough level
  auto_upgrade_to_thorough: true

  # Block commits if coverage drops
  block_coverage_regression: true

  # Require all tests pass
  require_all_pass: true
```

### Check Before G3 Gate

```bash
# Check if ready for G3
/f5-gate check G3 --pre-commit

# This runs:
# 1. Full lint check
# 2. Full type check
# 3. All unit tests
# 4. Coverage verification (≥80%)
```

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Hook not running | Check `.husky/` or `.git/hooks/` permissions |
| Tests too slow | Use `test:staged` instead of full suite |
| False positives | Update test patterns in jest config |
| Coverage drops | Add tests for new code before commit |

### Debug Mode

```bash
# Run hook manually with debug
DEBUG=1 .husky/pre-commit

# Or with F5
/f5-test hooks run --debug
```

---

## Best Practices

1. **Keep hooks fast** - Use related tests only for standard workflow
2. **Don't skip often** - `--no-verify` should be rare exception
3. **Fix immediately** - Don't let failing tests accumulate
4. **Use skip patterns wisely** - WIP commits should be rebased before PR
5. **Upgrade before G3** - Switch to thorough level for final testing

---

## See Also

- `/f5-test` - Main test command
- `/f5-gate` - Quality gates
- `/f5-test-unit` - Unit testing
- `docs/testing/README.md` - Testing overview

---

*F5 Framework - Pre-commit Testing Documentation v1.0.0*
