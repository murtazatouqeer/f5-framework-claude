---
name: react-skills
description: React patterns, hooks, and best practices for modern frontend development
category: stacks/frontend/react
applies_to: react
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: true
context: inject
---

# React Skills

A JavaScript library for building user interfaces.

## Sub-Skills

### Architecture
- [project-structure.md](architecture/project-structure.md) - Project organization
- [component-patterns.md](architecture/component-patterns.md) - Component design
- [state-management.md](architecture/state-management.md) - State patterns

### Hooks
- [use-state.md](hooks/use-state.md) - useState patterns
- [use-effect.md](hooks/use-effect.md) - useEffect patterns
- [use-memo.md](hooks/use-memo.md) - useMemo optimization
- [use-callback.md](hooks/use-callback.md) - useCallback patterns
- [custom-hooks.md](hooks/custom-hooks.md) - Custom hook patterns

### Performance
- [memoization.md](performance/memoization.md) - Memoization strategies
- [lazy-loading.md](performance/lazy-loading.md) - Code splitting
- [virtualization.md](performance/virtualization.md) - List virtualization

### Testing
- [testing-library.md](testing/testing-library.md) - React Testing Library
- [component-testing.md](testing/component-testing.md) - Component tests
- [hook-testing.md](testing/hook-testing.md) - Hook testing

### Forms
- [form-handling.md](forms/form-handling.md) - Form patterns
- [validation.md](forms/validation.md) - Form validation

### Styling
- [css-modules.md](styling/css-modules.md) - CSS Modules
- [styled-components.md](styling/styled-components.md) - Styled Components
- [tailwind.md](styling/tailwind.md) - Tailwind CSS

## Detection
Auto-detected when project contains:
- `react` or `react-dom` packages
- `import React` or `from 'react'` imports
