---
name: lint-staged
description: Pre-commit linting with lint-staged and Husky
category: code-quality/linting
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# lint-staged Configuration

## Overview

lint-staged runs linters on staged Git files, ensuring only clean code is committed. Combined with Husky, it provides automated pre-commit checks.

## Setup

### Installation

```bash
# Install lint-staged and Husky
npm install -D lint-staged husky

# Initialize Husky
npx husky init

# Add pre-commit hook
echo "npx lint-staged" > .husky/pre-commit
```

## Configuration

### package.json (Simple)

```json
{
  "lint-staged": {
    "*.{ts,tsx}": [
      "eslint --fix",
      "prettier --write"
    ],
    "*.{css,scss}": [
      "stylelint --fix",
      "prettier --write"
    ],
    "*.{json,md,yaml,yml}": [
      "prettier --write"
    ]
  }
}
```

### lint-staged.config.js (Advanced)

```javascript
/** @type {import('lint-staged').Config} */
export default {
  // TypeScript/JavaScript files
  '*.{ts,tsx}': (filenames) => [
    `eslint --fix ${filenames.join(' ')}`,
    `prettier --write ${filenames.join(' ')}`,
    'tsc --noEmit', // Type check all files (not just staged)
  ],

  // JavaScript files
  '*.{js,jsx}': [
    'eslint --fix',
    'prettier --write',
  ],

  // Style files
  '*.{css,scss}': [
    'stylelint --fix',
    'prettier --write',
  ],

  // JSON files
  '*.json': [
    'prettier --write',
  ],

  // Markdown files
  '*.md': [
    'prettier --write',
    'markdownlint --fix',
  ],

  // Package.json - sort and format
  'package.json': [
    'sort-package-json',
    'prettier --write',
  ],
};
```

### With Test Running

```javascript
// lint-staged.config.js
export default {
  '*.{ts,tsx}': (filenames) => {
    const testFiles = filenames.filter((f) => f.includes('.test.') || f.includes('.spec.'));
    const sourceFiles = filenames.filter((f) => !f.includes('.test.') && !f.includes('.spec.'));

    const commands = [];

    if (sourceFiles.length > 0) {
      commands.push(`eslint --fix ${sourceFiles.join(' ')}`);
      commands.push(`prettier --write ${sourceFiles.join(' ')}`);
    }

    if (testFiles.length > 0) {
      commands.push(`eslint --fix ${testFiles.join(' ')}`);
      commands.push(`jest --bail --findRelatedTests ${testFiles.join(' ')}`);
    }

    // Run related tests for source files
    if (sourceFiles.length > 0) {
      commands.push(`jest --bail --findRelatedTests ${sourceFiles.join(' ')}`);
    }

    return commands;
  },
};
```

## Husky Hooks

### Pre-commit (.husky/pre-commit)

```bash
#!/usr/bin/env sh
. "$(dirname -- "$0")/_/husky.sh"

npx lint-staged
```

### Commit-msg (.husky/commit-msg)

```bash
#!/usr/bin/env sh
. "$(dirname -- "$0")/_/husky.sh"

npx --no -- commitlint --edit ${1}
```

### Pre-push (.husky/pre-push)

```bash
#!/usr/bin/env sh
. "$(dirname -- "$0")/_/husky.sh"

npm run test
npm run build
```

## Commitlint Integration

### Installation

```bash
npm install -D @commitlint/cli @commitlint/config-conventional
```

### commitlint.config.js

```javascript
/** @type {import('@commitlint/types').UserConfig} */
export default {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [
      2,
      'always',
      [
        'feat',     // New feature
        'fix',      // Bug fix
        'docs',     // Documentation
        'style',    // Formatting
        'refactor', // Code change without feature/fix
        'perf',     // Performance improvement
        'test',     // Tests
        'build',    // Build system
        'ci',       // CI configuration
        'chore',    // Maintenance
        'revert',   // Revert commit
      ],
    ],
    'subject-case': [2, 'always', 'lower-case'],
    'subject-max-length': [2, 'always', 72],
    'body-max-line-length': [2, 'always', 100],
  },
};
```

## Advanced Patterns

### Conditional Linting

```javascript
// lint-staged.config.js
export default {
  '*.{ts,tsx}': (filenames) => {
    // Skip linting for generated files
    const filteredFiles = filenames.filter(
      (f) => !f.includes('/generated/') && !f.includes('.generated.')
    );

    if (filteredFiles.length === 0) return [];

    return [
      `eslint --fix ${filteredFiles.join(' ')}`,
      `prettier --write ${filteredFiles.join(' ')}`,
    ];
  },
};
```

### Parallel Execution

```javascript
// lint-staged.config.js
export default {
  // These run in parallel
  '*.ts': 'eslint --fix',
  '*.css': 'stylelint --fix',
  '*.json': 'prettier --write',
};
```

### With Secret Detection

```javascript
// lint-staged.config.js
export default {
  '*': [
    'secretlint',
  ],
  '*.{ts,tsx}': [
    'eslint --fix',
    'prettier --write',
  ],
};
```

## Package.json Scripts

```json
{
  "scripts": {
    "prepare": "husky",
    "lint-staged": "lint-staged",
    "lint-staged:debug": "lint-staged --debug"
  }
}
```

## Troubleshooting

### Skip Hooks Temporarily

```bash
# Skip pre-commit hook
git commit --no-verify -m "WIP: work in progress"

# Skip all hooks
HUSKY=0 git commit -m "message"
```

### Debug lint-staged

```bash
# Run with debug output
npx lint-staged --debug

# Dry run (no changes)
npx lint-staged --dry-run
```

### Common Issues

1. **"Cannot find module" errors**
   - Ensure all dependencies are installed
   - Check that config file uses correct import syntax

2. **Commands not running**
   - Verify file patterns match staged files
   - Check that .husky/pre-commit is executable

3. **Hook not firing**
   - Run `npx husky` to reinstall hooks
   - Check `.git/hooks/pre-commit` exists

## Best Practices

| Practice | Description |
|----------|-------------|
| Fast checks first | Run quick checks before slow ones |
| Fix before check | Use `--fix` flags to auto-correct |
| Fail fast | Use `--bail` for tests |
| Skip generated | Exclude auto-generated files |
| Related tests only | Run tests for changed files only |
