# Linting Reference

## ESLint Configuration (Flat Config)

### Base TypeScript

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
      '@typescript-eslint/no-explicit-any': 'warn',
      '@typescript-eslint/prefer-nullish-coalescing': 'error',
      '@typescript-eslint/prefer-optional-chain': 'error',
      '@typescript-eslint/strict-boolean-expressions': 'error',
      '@typescript-eslint/no-floating-promises': 'error',
      '@typescript-eslint/await-thenable': 'error',

      // General
      'no-console': ['warn', { allow: ['warn', 'error'] }],
      'prefer-const': 'error',
      'eqeqeq': ['error', 'always'],

      // Complexity
      'complexity': ['warn', 10],
      'max-depth': ['warn', 3],
      'max-lines-per-function': ['warn', { max: 50, skipBlankLines: true, skipComments: true }],
      'max-params': ['warn', 4],
    },
  },
  {
    files: ['**/*.test.ts', '**/*.spec.ts'],
    rules: {
      '@typescript-eslint/no-explicit-any': 'off',
      'max-lines-per-function': 'off',
    },
  },
  {
    ignores: ['dist/', 'build/', 'node_modules/', 'coverage/'],
  }
);
```

### React Configuration

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
    rules: {
      // React
      'react/react-in-jsx-scope': 'off',
      'react/jsx-key': ['error', { checkFragmentShorthand: true }],
      'react/no-array-index-key': 'warn',
      'react/self-closing-comp': 'error',
      'react/jsx-curly-brace-presence': ['error', { props: 'never', children: 'never' }],
      'react/no-unstable-nested-components': 'error',

      // Hooks
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'warn',

      // Accessibility
      'jsx-a11y/alt-text': 'error',
      'jsx-a11y/anchor-is-valid': 'error',
    },
    settings: {
      react: { version: 'detect' },
    },
  }
);
```

### NestJS Configuration

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
      parserOptions: { project: './tsconfig.json' },
    },
    rules: {
      '@typescript-eslint/explicit-function-return-type': 'off',
      '@typescript-eslint/no-extraneous-class': 'off', // Decorators
      '@typescript-eslint/no-floating-promises': 'error',
    },
  }
);
```

## Prettier Configuration

```json
// .prettierrc
{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100,
  "arrowParens": "always",
  "endOfLine": "lf"
}
```

```json
// .prettierignore
dist
build
node_modules
coverage
*.min.js
```

## Import Sorting

```typescript
// eslint.config.js
import importPlugin from 'eslint-plugin-import';

export default [
  {
    plugins: { import: importPlugin },
    rules: {
      'import/order': ['error', {
        groups: ['builtin', 'external', 'internal', 'parent', 'sibling', 'index', 'type'],
        'newlines-between': 'always',
        alphabetize: { order: 'asc', caseInsensitive: true },
        pathGroups: [{ pattern: '@/**', group: 'internal', position: 'before' }],
      }],
      'import/no-duplicates': 'error',
      'import/no-cycle': ['error', { maxDepth: 10 }],
      'import/first': 'error',
      'import/newline-after-import': 'error',
    },
  },
];
```

## lint-staged Configuration

```json
// package.json
{
  "lint-staged": {
    "*.{ts,tsx}": ["eslint --fix", "prettier --write"],
    "*.{css,scss}": ["stylelint --fix", "prettier --write"],
    "*.{json,md}": ["prettier --write"]
  }
}
```

## Husky Git Hooks

```bash
# .husky/pre-commit
npx lint-staged

# .husky/commit-msg
npx commitlint --edit $1
```

## Stylelint Configuration

```javascript
// stylelint.config.js
export default {
  extends: ['stylelint-config-standard', 'stylelint-config-recess-order'],
  plugins: ['stylelint-scss'],
  rules: {
    'selector-class-pattern': '^[a-z][a-zA-Z0-9]*$', // camelCase
    'color-hex-length': 'short',
    'declaration-block-no-duplicate-properties': true,
  },
};
```

## VS Code Integration

```json
// .vscode/settings.json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": "explicit"
  },
  "eslint.useFlatConfig": true,
  "eslint.validate": ["javascript", "typescript", "typescriptreact"]
}
```

## Installation Commands

```bash
# Core ESLint
npm install -D eslint @eslint/js typescript-eslint

# React
npm install -D eslint-plugin-react eslint-plugin-react-hooks eslint-plugin-jsx-a11y

# Import sorting
npm install -D eslint-plugin-import

# Prettier
npm install -D prettier eslint-config-prettier

# Git hooks
npm install -D husky lint-staged
npx husky init

# Stylelint
npm install -D stylelint stylelint-config-standard stylelint-config-recess-order
```

## Package.json Scripts

```json
{
  "scripts": {
    "lint": "eslint .",
    "lint:fix": "eslint . --fix",
    "lint:strict": "eslint . --max-warnings 0",
    "format": "prettier --write .",
    "format:check": "prettier --check ."
  }
}
```

## Common Rules Reference

| Rule | Description | Value |
|------|-------------|-------|
| `no-unused-vars` | Disallow unused variables | error |
| `no-console` | Warn on console statements | warn |
| `eqeqeq` | Require === and !== | error |
| `complexity` | Limit cyclomatic complexity | 10 |
| `max-depth` | Limit nesting depth | 3 |
| `max-lines-per-function` | Limit function length | 50 |
