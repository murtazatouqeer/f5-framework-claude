---
name: prettier-config
description: Prettier code formatting configuration
category: code-quality/linting
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Prettier Configuration

## Overview

Prettier is an opinionated code formatter that enforces consistent style across your codebase. It supports JavaScript, TypeScript, CSS, JSON, and more.

## Configuration

### .prettierrc

```json
{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2,
  "useTabs": false,
  "trailingComma": "es5",
  "printWidth": 100,
  "bracketSpacing": true,
  "bracketSameLine": false,
  "arrowParens": "always",
  "endOfLine": "lf",
  "quoteProps": "as-needed",
  "jsxSingleQuote": false,
  "proseWrap": "preserve"
}
```

### prettier.config.js (with comments)

```javascript
/** @type {import("prettier").Config} */
const config = {
  // Add semicolons at the end of statements
  semi: true,

  // Use single quotes instead of double quotes
  singleQuote: true,

  // Specify the number of spaces per indentation level
  tabWidth: 2,

  // Use spaces instead of tabs
  useTabs: false,

  // Print trailing commas wherever possible in ES5 (objects, arrays, etc.)
  trailingComma: 'es5',

  // Specify the line length that the printer will wrap on
  printWidth: 100,

  // Print spaces between brackets in object literals
  bracketSpacing: true,

  // Put > of multi-line HTML elements on new line
  bracketSameLine: false,

  // Include parentheses around a sole arrow function parameter
  arrowParens: 'always',

  // Line endings (lf for Unix, crlf for Windows)
  endOfLine: 'lf',

  // Change when properties in objects are quoted
  quoteProps: 'as-needed',

  // Use single quotes in JSX
  jsxSingleQuote: false,

  // How to wrap prose (markdown)
  proseWrap: 'preserve',

  // HTML whitespace sensitivity
  htmlWhitespaceSensitivity: 'css',

  // Indent script and style tags in Vue files
  vueIndentScriptAndStyle: false,

  // Enforce single attribute per line in HTML, Vue and JSX
  singleAttributePerLine: false,
};

export default config;
```

## Ignore Files

### .prettierignore

```gitignore
# Dependencies
node_modules/
package-lock.json
yarn.lock
pnpm-lock.yaml

# Build outputs
dist/
build/
.next/
out/

# Generated files
coverage/
*.min.js
*.min.css

# Configuration files (may need specific formatting)
*.config.js
*.config.ts

# Documentation
docs/
*.md

# IDE
.idea/
.vscode/

# Other
.git/
*.log
```

## ESLint Integration

### eslint-config-prettier

Disables ESLint rules that conflict with Prettier:

```bash
npm install -D eslint-config-prettier
```

```typescript
// eslint.config.js
import prettierConfig from 'eslint-config-prettier';

export default [
  // ... other configs
  prettierConfig,
];
```

### eslint-plugin-prettier (optional)

Runs Prettier as an ESLint rule:

```bash
npm install -D eslint-plugin-prettier
```

```typescript
// eslint.config.js
import prettierPlugin from 'eslint-plugin-prettier';
import prettierConfig from 'eslint-config-prettier';

export default [
  {
    plugins: {
      prettier: prettierPlugin,
    },
    rules: {
      'prettier/prettier': 'error',
    },
  },
  prettierConfig,
];
```

## Package.json Scripts

```json
{
  "scripts": {
    "format": "prettier --write .",
    "format:check": "prettier --check .",
    "format:staged": "prettier --write --staged"
  }
}
```

## IDE Integration

### VS Code Settings

```json
// .vscode/settings.json
{
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.formatOnSave": true,
  "editor.formatOnPaste": false,
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[javascript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[json]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[css]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[scss]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

### VS Code Extensions

```json
// .vscode/extensions.json
{
  "recommendations": [
    "esbenp.prettier-vscode"
  ]
}
```

## Pre-commit Hook with lint-staged

```json
// package.json
{
  "lint-staged": {
    "*.{ts,tsx,js,jsx}": [
      "eslint --fix",
      "prettier --write"
    ],
    "*.{json,css,scss,md}": [
      "prettier --write"
    ]
  }
}
```

## Language-Specific Overrides

```json
// .prettierrc
{
  "semi": true,
  "singleQuote": true,
  "overrides": [
    {
      "files": "*.json",
      "options": {
        "tabWidth": 2
      }
    },
    {
      "files": "*.md",
      "options": {
        "proseWrap": "always",
        "printWidth": 80
      }
    },
    {
      "files": "*.yaml",
      "options": {
        "tabWidth": 2,
        "singleQuote": false
      }
    },
    {
      "files": ["*.html", "*.vue"],
      "options": {
        "printWidth": 120,
        "singleAttributePerLine": true
      }
    }
  ]
}
```

## Installation

```bash
# Core Prettier
npm install -D prettier

# ESLint integration
npm install -D eslint-config-prettier

# Optional: Run as ESLint rule
npm install -D eslint-plugin-prettier
```

## Common Configuration Patterns

### Strict Mode (Team Consistency)

```json
{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "all",
  "printWidth": 80,
  "arrowParens": "always",
  "endOfLine": "lf"
}
```

### Relaxed Mode (Less Opinionated)

```json
{
  "semi": true,
  "singleQuote": false,
  "tabWidth": 4,
  "trailingComma": "es5",
  "printWidth": 120
}
```

### Airbnb Style Compatible

```json
{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "all",
  "printWidth": 100,
  "arrowParens": "always"
}
```

## Troubleshooting

### Common Issues

1. **Conflicts with ESLint**
   - Always include `eslint-config-prettier` last
   - Do not use `eslint-plugin-prettier` if it causes issues

2. **Different formatting on different machines**
   - Use `.editorconfig` for editor consistency
   - Ensure same Prettier version (use `package-lock.json`)

3. **Slow formatting**
   - Use `.prettierignore` to skip large files
   - Format only staged files with lint-staged

### EditorConfig Compatibility

```ini
# .editorconfig
root = true

[*]
indent_style = space
indent_size = 2
end_of_line = lf
charset = utf-8
trim_trailing_whitespace = true
insert_final_newline = true

[*.md]
trim_trailing_whitespace = false
```
