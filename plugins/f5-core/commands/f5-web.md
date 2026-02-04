---
description: Frontend/web development commands
argument-hint: <generate|scaffold> <type> [name]
---

# /f5-web - Frontend/Web Development Assistant

Hỗ trợ phát triển frontend theo stack đã chọn trong project.

## ARGUMENTS
The user's request is: $ARGUMENTS

## DETECT FRONTEND STACK

```bash
# Auto-detect from .f5/config.json
STACK=$(jq -r '.stack.frontend // "nextjs"' .f5/config.json 2>/dev/null)
```

## STACK-SPECIFIC COMMANDS

### Next.js (Default)

| Command | Description |
|---------|-------------|
| `page <path>` | Generate page component (App Router) |
| `layout <path>` | Generate layout component |
| `component <name>` | Generate React component |
| `api <path>` | Generate API route handler |
| `hook <name>` | Generate custom hook |
| `context <name>` | Generate React context |
| `server-action <name>` | Generate server action |

### React (Vite)

| Command | Description |
|---------|-------------|
| `component <name>` | Generate React component |
| `hook <name>` | Generate custom hook |
| `context <name>` | Generate context provider |
| `page <name>` | Generate page component |
| `store <name>` | Generate Zustand store |

### Nuxt (Vue 3)

| Command | Description |
|---------|-------------|
| `page <path>` | Generate Nuxt page |
| `component <name>` | Generate Vue component |
| `composable <name>` | Generate Vue composable |
| `layout <name>` | Generate layout |
| `middleware <name>` | Generate middleware |
| `plugin <name>` | Generate plugin |

### Vue 3 (Vite)

| Command | Description |
|---------|-------------|
| `component <name>` | Generate Vue SFC |
| `composable <name>` | Generate composable |
| `store <name>` | Generate Pinia store |
| `view <name>` | Generate view component |

### Angular

| Command | Description |
|---------|-------------|
| `component <name>` | Generate component |
| `service <name>` | Generate service |
| `module <name>` | Generate feature module |
| `guard <name>` | Generate route guard |
| `pipe <name>` | Generate pipe |
| `directive <name>` | Generate directive |

## EXECUTION

Based on detected stack and user request:

```markdown
## Frontend: {{STACK}}

### Generated Files:
{{list of generated files}}

### Component Structure:
{{component tree}}

### Next Steps:
{{stack-specific recommendations}}

### Related Commands:
- /f5-test-unit     - Run component tests
- /f5-test-e2e      - Run E2E tests
- /f5-design ui     - Generate UI mockups
```

## EXAMPLES

```bash
# Next.js
/f5-web page dashboard
/f5-web component Button
/f5-web api auth/login
/f5-web server-action submitForm

# React
/f5-web component UserCard
/f5-web hook useAuth
/f5-web store authStore

# Nuxt
/f5-web page users/[id]
/f5-web composable useAuth
/f5-web middleware auth

# Vue
/f5-web component UserList
/f5-web store userStore

# Angular
/f5-web component user-list
/f5-web service auth
/f5-web guard auth
```

## STYLING

Claude sẽ detect styling solution:

| Detection | Applied |
|-----------|---------|
| Tailwind CSS | Utility classes |
| CSS Modules | Scoped styles |
| Styled Components | CSS-in-JS |
| SCSS/Sass | Nested styles |
| shadcn/ui | Component library |

## BEST PRACTICES

| Stack | Patterns Applied |
|-------|-----------------|
| Next.js | Server Components, Route Groups, Parallel Routes |
| React | Custom hooks, Context, Suspense |
| Nuxt | Auto-imports, Composables, Middleware |
| Vue | Composition API, Pinia, Script Setup |
| Angular | Standalone Components, Signals, RxJS |

## ACCESSIBILITY

Claude automatically ensures:
- ARIA labels and roles
- Keyboard navigation
- Focus management
- Screen reader support
- Color contrast
