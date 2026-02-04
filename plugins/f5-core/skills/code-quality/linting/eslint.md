---
name: eslint-config
description: ESLint configuration for JavaScript/TypeScript
category: code-quality/linting
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# ESLint Configuration

## Overview

ESLint is the standard linting tool for JavaScript and TypeScript projects. Modern ESLint uses flat config format (eslint.config.js).

## Modern ESLint Setup (Flat Config)

### Base TypeScript Configuration

```typescript
// eslint.config.js
import eslint from '@eslint/js';
import tseslint from 'typescript-eslint';
import prettierConfig from 'eslint-config-prettier';

export default tseslint.config(
  eslint.configs.recommended,
  ...tseslint.configs.strictTypeChecked,
  ...tseslint.configs.stylisticTypeChecked,
  prettierConfig,
  {
    languageOptions: {
      parserOptions: {
        project: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
    rules: {
      // TypeScript
      '@typescript-eslint/no-unused-vars': ['error', {
        argsIgnorePattern: '^_',
        varsIgnorePattern: '^_',
      }],
      '@typescript-eslint/explicit-function-return-type': 'off',
      '@typescript-eslint/explicit-module-boundary-types': 'off',
      '@typescript-eslint/no-explicit-any': 'warn',
      '@typescript-eslint/prefer-nullish-coalescing': 'error',
      '@typescript-eslint/prefer-optional-chain': 'error',
      '@typescript-eslint/strict-boolean-expressions': 'error',
      '@typescript-eslint/no-floating-promises': 'error',
      '@typescript-eslint/await-thenable': 'error',
      '@typescript-eslint/no-misused-promises': 'error',
      '@typescript-eslint/require-await': 'error',

      // General
      'no-console': ['warn', { allow: ['warn', 'error'] }],
      'no-debugger': 'error',
      'no-duplicate-imports': 'error',
      'no-unused-expressions': 'error',
      'prefer-const': 'error',
      'no-var': 'error',

      // Best practices
      'eqeqeq': ['error', 'always'],
      'no-eval': 'error',
      'no-implied-eval': 'error',
      'no-new-func': 'error',
      'no-return-await': 'error',

      // Complexity
      'complexity': ['warn', 10],
      'max-depth': ['warn', 3],
      'max-lines-per-function': ['warn', { max: 50, skipBlankLines: true, skipComments: true }],
      'max-params': ['warn', 4],
      'max-nested-callbacks': ['warn', 3],
    },
  },
  {
    // Test files - relaxed rules
    files: ['**/*.test.ts', '**/*.spec.ts', '**/__tests__/**'],
    rules: {
      '@typescript-eslint/no-explicit-any': 'off',
      '@typescript-eslint/no-non-null-assertion': 'off',
      '@typescript-eslint/no-unsafe-assignment': 'off',
      'max-lines-per-function': 'off',
      'max-nested-callbacks': 'off',
    },
  },
  {
    ignores: ['dist/', 'build/', 'node_modules/', 'coverage/', '*.js'],
  }
);
```

## React ESLint Config

```typescript
// eslint.config.js
import eslint from '@eslint/js';
import tseslint from 'typescript-eslint';
import reactPlugin from 'eslint-plugin-react';
import reactHooksPlugin from 'eslint-plugin-react-hooks';
import jsxA11yPlugin from 'eslint-plugin-jsx-a11y';
import prettierConfig from 'eslint-config-prettier';

export default tseslint.config(
  eslint.configs.recommended,
  ...tseslint.configs.recommended,
  prettierConfig,
  {
    files: ['**/*.{ts,tsx}'],
    plugins: {
      react: reactPlugin,
      'react-hooks': reactHooksPlugin,
      'jsx-a11y': jsxA11yPlugin,
    },
    languageOptions: {
      parserOptions: {
        ecmaFeatures: {
          jsx: true,
        },
      },
    },
    rules: {
      // React
      'react/react-in-jsx-scope': 'off',
      'react/prop-types': 'off',
      'react/jsx-no-target-blank': 'error',
      'react/jsx-key': ['error', { checkFragmentShorthand: true }],
      'react/no-array-index-key': 'warn',
      'react/self-closing-comp': 'error',
      'react/jsx-curly-brace-presence': ['error', { props: 'never', children: 'never' }],
      'react/jsx-boolean-value': ['error', 'never'],
      'react/no-unstable-nested-components': 'error',
      'react/jsx-no-useless-fragment': 'error',

      // Hooks
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'warn',

      // Accessibility
      'jsx-a11y/alt-text': 'error',
      'jsx-a11y/anchor-is-valid': 'error',
      'jsx-a11y/click-events-have-key-events': 'warn',
      'jsx-a11y/no-autofocus': 'warn',
      'jsx-a11y/no-noninteractive-element-interactions': 'warn',
      'jsx-a11y/role-has-required-aria-props': 'error',
    },
    settings: {
      react: {
        version: 'detect',
      },
    },
  },
  {
    ignores: ['dist/', 'build/', 'node_modules/'],
  }
);
```

## NestJS ESLint Config

```typescript
// eslint.config.js
import eslint from '@eslint/js';
import tseslint from 'typescript-eslint';
import prettierConfig from 'eslint-config-prettier';

export default tseslint.config(
  eslint.configs.recommended,
  ...tseslint.configs.strictTypeChecked,
  prettierConfig,
  {
    languageOptions: {
      parserOptions: {
        project: './tsconfig.json',
      },
    },
    rules: {
      // NestJS specific
      '@typescript-eslint/interface-name-prefix': 'off',
      '@typescript-eslint/explicit-function-return-type': 'off',
      '@typescript-eslint/explicit-module-boundary-types': 'off',
      '@typescript-eslint/no-explicit-any': 'warn',
      '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],

      // Decorators support
      '@typescript-eslint/no-extraneous-class': 'off',

      // Async
      '@typescript-eslint/no-floating-promises': 'error',
      '@typescript-eslint/await-thenable': 'error',
    },
  },
  {
    files: ['**/*.spec.ts', '**/*.e2e-spec.ts'],
    rules: {
      '@typescript-eslint/no-explicit-any': 'off',
      '@typescript-eslint/no-unsafe-assignment': 'off',
    },
  },
  {
    ignores: ['dist/', 'node_modules/'],
  }
);
```

## Import Sorting

```typescript
// eslint.config.js
import importPlugin from 'eslint-plugin-import';

export default [
  {
    plugins: {
      import: importPlugin,
    },
    rules: {
      'import/order': ['error', {
        groups: [
          'builtin',      // Node.js built-in modules
          'external',     // npm packages
          'internal',     // Aliased modules (@/)
          'parent',       // Parent imports (../)
          'sibling',      // Sibling imports (./)
          'index',        // Index imports
          'type',         // Type imports
        ],
        'newlines-between': 'always',
        alphabetize: {
          order: 'asc',
          caseInsensitive: true,
        },
        pathGroups: [
          {
            pattern: '@/**',
            group: 'internal',
            position: 'before',
          },
        ],
        pathGroupsExcludedImportTypes: ['builtin'],
      }],
      'import/no-duplicates': 'error',
      'import/no-cycle': ['error', { maxDepth: 10 }],
      'import/no-self-import': 'error',
      'import/no-useless-path-segments': 'error',
      'import/first': 'error',
      'import/newline-after-import': 'error',
    },
  },
];
```

## Package.json Scripts

```json
{
  "scripts": {
    "lint": "eslint .",
    "lint:fix": "eslint . --fix",
    "lint:strict": "eslint . --max-warnings 0",
    "lint:report": "eslint . --format json --output-file reports/eslint.json"
  }
}
```

## Installation

```bash
# Core ESLint
npm install -D eslint @eslint/js

# TypeScript support
npm install -D typescript-eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin

# React support
npm install -D eslint-plugin-react eslint-plugin-react-hooks eslint-plugin-jsx-a11y

# Import sorting
npm install -D eslint-plugin-import

# Prettier integration
npm install -D eslint-config-prettier eslint-plugin-prettier
```

## Common Rules Reference

| Rule | Description | Recommended |
|------|-------------|-------------|
| `no-unused-vars` | Disallow unused variables | error |
| `no-console` | Warn on console statements | warn |
| `eqeqeq` | Require === and !== | error |
| `complexity` | Limit cyclomatic complexity | warn, 10 |
| `max-depth` | Limit nesting depth | warn, 3 |
| `max-lines-per-function` | Limit function length | warn, 50 |

## IDE Integration

### VS Code Settings

```json
// .vscode/settings.json
{
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": "explicit"
  },
  "eslint.validate": [
    "javascript",
    "javascriptreact",
    "typescript",
    "typescriptreact"
  ],
  "eslint.useFlatConfig": true
}
```

## Troubleshooting

### Common Issues

1. **Parser errors with TypeScript**
   - Ensure `tsconfig.json` includes all files
   - Check `parserOptions.project` path

2. **Rules not working**
   - Verify plugin is installed and imported
   - Check rule name matches plugin prefix

3. **Flat config migration**
   - Use `@eslint/migrate-config` for automatic conversion
   - Replace `extends` with spread operators
