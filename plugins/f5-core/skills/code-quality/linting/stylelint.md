---
name: stylelint-config
description: Stylelint configuration for CSS/SCSS
category: code-quality/linting
applies_to: frontend
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Stylelint Configuration

## Overview

Stylelint is a modern linter for CSS, SCSS, Less, and other style languages. It helps enforce consistent conventions and catch errors.

## Configuration

### stylelint.config.js

```javascript
/** @type {import('stylelint').Config} */
export default {
  extends: [
    'stylelint-config-standard',
    'stylelint-config-recommended-scss',
    'stylelint-config-prettier-scss',
  ],
  plugins: [
    'stylelint-scss',
    'stylelint-order',
  ],
  rules: {
    // General
    'color-hex-length': 'short',
    'color-named': 'never',
    'color-no-invalid-hex': true,

    // Font
    'font-family-name-quotes': 'always-where-recommended',
    'font-weight-notation': 'numeric',

    // Selectors
    'selector-class-pattern': [
      '^[a-z][a-zA-Z0-9]*$',
      {
        message: 'Expected class selector to be camelCase',
      },
    ],
    'selector-max-id': 0,
    'selector-max-class': 3,
    'selector-max-compound-selectors': 3,
    'selector-no-qualifying-type': [true, { ignore: ['attribute'] }],

    // Properties
    'declaration-no-important': true,
    'declaration-block-no-duplicate-properties': true,
    'declaration-property-value-disallowed-list': {
      '/^border/': ['none'],
    },

    // Units
    'unit-disallowed-list': ['pt', 'cm', 'mm', 'in', 'pc'],
    'length-zero-no-unit': true,

    // Nesting
    'max-nesting-depth': 3,

    // Order
    'order/order': [
      'custom-properties',
      'dollar-variables',
      'declarations',
      'at-rules',
      'rules',
    ],
    'order/properties-order': [
      // Positioning
      'position',
      'top',
      'right',
      'bottom',
      'left',
      'z-index',

      // Box model
      'display',
      'flex',
      'flex-direction',
      'flex-wrap',
      'justify-content',
      'align-items',
      'gap',
      'grid',
      'grid-template-columns',
      'grid-template-rows',

      // Sizing
      'width',
      'min-width',
      'max-width',
      'height',
      'min-height',
      'max-height',

      // Spacing
      'margin',
      'margin-top',
      'margin-right',
      'margin-bottom',
      'margin-left',
      'padding',
      'padding-top',
      'padding-right',
      'padding-bottom',
      'padding-left',

      // Typography
      'font',
      'font-family',
      'font-size',
      'font-weight',
      'line-height',
      'text-align',
      'color',

      // Visual
      'background',
      'background-color',
      'border',
      'border-radius',
      'box-shadow',
      'opacity',

      // Animation
      'transition',
      'transform',
      'animation',
    ],

    // SCSS specific
    'scss/at-rule-no-unknown': true,
    'scss/selector-no-redundant-nesting-selector': true,
    'scss/dollar-variable-pattern': '^[a-z][a-zA-Z0-9]*$',
    'scss/percent-placeholder-pattern': '^[a-z][a-zA-Z0-9]*$',
    'scss/no-duplicate-mixins': true,
    'scss/no-global-function-names': true,
  },
  ignoreFiles: [
    'node_modules/**',
    'dist/**',
    'build/**',
    'coverage/**',
    '**/*.min.css',
  ],
};
```

## CSS Modules Configuration

```javascript
// stylelint.config.js
export default {
  extends: ['stylelint-config-standard'],
  rules: {
    // Allow :global and :local pseudo-classes
    'selector-pseudo-class-no-unknown': [
      true,
      {
        ignorePseudoClasses: ['global', 'local'],
      },
    ],
    // Allow composes property
    'property-no-unknown': [
      true,
      {
        ignoreProperties: ['composes'],
      },
    ],
    // Camel case for CSS Modules
    'selector-class-pattern': '^[a-z][a-zA-Z0-9]*$',
  },
};
```

## Tailwind CSS Configuration

```javascript
// stylelint.config.js
export default {
  extends: ['stylelint-config-standard', 'stylelint-config-tailwindcss'],
  rules: {
    // Allow Tailwind directives
    'at-rule-no-unknown': [
      true,
      {
        ignoreAtRules: ['tailwind', 'apply', 'variants', 'responsive', 'screen', 'layer'],
      },
    ],
    // Allow Tailwind functions
    'function-no-unknown': [
      true,
      {
        ignoreFunctions: ['theme', 'screen'],
      },
    ],
  },
};
```

## Package.json Scripts

```json
{
  "scripts": {
    "lint:css": "stylelint \"**/*.{css,scss}\"",
    "lint:css:fix": "stylelint \"**/*.{css,scss}\" --fix"
  }
}
```

## Installation

```bash
# Core Stylelint
npm install -D stylelint

# Standard config
npm install -D stylelint-config-standard

# SCSS support
npm install -D stylelint-config-recommended-scss stylelint-scss

# Prettier integration
npm install -D stylelint-config-prettier-scss

# Property ordering
npm install -D stylelint-order

# Tailwind support (if using Tailwind)
npm install -D stylelint-config-tailwindcss
```

## VS Code Integration

```json
// .vscode/settings.json
{
  "stylelint.validate": ["css", "scss", "less"],
  "css.validate": false,
  "scss.validate": false,
  "less.validate": false,
  "editor.codeActionsOnSave": {
    "source.fixAll.stylelint": "explicit"
  }
}
```

## lint-staged Integration

```json
// package.json
{
  "lint-staged": {
    "*.{css,scss}": [
      "stylelint --fix",
      "prettier --write"
    ]
  }
}
```

## Common Rules Reference

| Rule | Description | Value |
|------|-------------|-------|
| `color-hex-length` | Hex color format | short |
| `selector-max-id` | Max ID selectors | 0 |
| `max-nesting-depth` | Max nesting levels | 3 |
| `declaration-no-important` | Ban !important | true |
| `length-zero-no-unit` | No units for zero | true |

## Disable Rules

```scss
/* stylelint-disable declaration-no-important */
.override {
  color: red !important;
}
/* stylelint-enable declaration-no-important */

// Single line disable
.exception {
  color: red !important; /* stylelint-disable-line declaration-no-important */
}

// Next line disable
/* stylelint-disable-next-line max-nesting-depth */
.deep {
  .nesting {
    .levels {
      .four {
        color: blue;
      }
    }
  }
}
```

## BEM Naming Convention

```javascript
// stylelint.config.js
export default {
  rules: {
    'selector-class-pattern': [
      // Block__Element--Modifier
      '^[a-z][a-zA-Z0-9]*(__[a-z][a-zA-Z0-9]*)?(--[a-z][a-zA-Z0-9]*)?$',
      {
        message: 'Expected class selector to be BEM format (block__element--modifier)',
      },
    ],
  },
};
```
