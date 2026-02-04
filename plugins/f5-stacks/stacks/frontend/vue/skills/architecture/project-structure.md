---
name: vue-project-structure
description: Vue 3 project structure and organization patterns
applies_to: vue
---

# Vue Project Structure

## Overview

Well-organized project structure is essential for maintainability.
Vue 3 projects should follow consistent patterns that scale.

## Recommended Structure

```
src/
├── App.vue                     # Root component
├── main.ts                     # Application entry point
├── vite-env.d.ts              # Vite type declarations
│
├── assets/                     # Static assets
│   ├── styles/
│   │   ├── main.css           # Global styles
│   │   ├── variables.css      # CSS variables
│   │   └── utilities.css      # Utility classes
│   ├── images/
│   └── fonts/
│
├── components/                 # Shared components
│   ├── ui/                    # Base UI components
│   │   ├── Button/
│   │   │   ├── Button.vue
│   │   │   ├── Button.test.ts
│   │   │   └── index.ts
│   │   ├── Input/
│   │   ├── Modal/
│   │   ├── Card/
│   │   └── index.ts           # Barrel export
│   ├── forms/                 # Form components
│   │   ├── FormField/
│   │   ├── FormSelect/
│   │   └── index.ts
│   └── layouts/               # Layout components
│       ├── MainLayout.vue
│       ├── AuthLayout.vue
│       └── index.ts
│
├── composables/               # Shared composables
│   ├── useAuth.ts
│   ├── useApi.ts
│   ├── useForm.ts
│   ├── useLocalStorage.ts
│   └── index.ts
│
├── features/                  # Feature modules
│   ├── auth/
│   │   ├── components/
│   │   │   ├── LoginForm.vue
│   │   │   └── RegisterForm.vue
│   │   ├── composables/
│   │   │   └── useLogin.ts
│   │   ├── api/
│   │   │   └── authApi.ts
│   │   ├── types.ts
│   │   └── index.ts
│   │
│   └── products/
│       ├── components/
│       │   ├── ProductCard.vue
│       │   ├── ProductList.vue
│       │   └── ProductForm.vue
│       ├── composables/
│       │   └── useProducts.ts
│       ├── api/
│       │   └── productApi.ts
│       ├── types.ts
│       └── index.ts
│
├── lib/                       # Utilities and configs
│   ├── api.ts                 # Axios instance
│   ├── utils.ts               # Helper functions
│   ├── constants.ts           # App constants
│   └── validators.ts          # Validation schemas
│
├── pages/                     # Route page components
│   ├── HomePage.vue
│   ├── auth/
│   │   ├── LoginPage.vue
│   │   └── RegisterPage.vue
│   └── products/
│       ├── ProductsPage.vue
│       ├── ProductDetailPage.vue
│       └── ProductFormPage.vue
│
├── router/                    # Vue Router config
│   ├── index.ts               # Router instance
│   ├── guards.ts              # Navigation guards
│   └── routes.ts              # Route definitions
│
├── stores/                    # Pinia stores
│   ├── useAuthStore.ts
│   ├── useProductStore.ts
│   ├── useUIStore.ts
│   └── index.ts
│
└── types/                     # Global TypeScript types
    ├── index.ts               # Main type exports
    ├── api.ts                 # API response types
    └── env.d.ts               # Environment types
```

## Directory Patterns

### Component Directory Pattern

```
components/ui/Button/
├── Button.vue           # Main component
├── Button.test.ts       # Tests
├── Button.stories.ts    # Storybook (optional)
└── index.ts            # Export
```

```typescript
// components/ui/Button/index.ts
export { default as Button } from './Button.vue';
export type { ButtonProps } from './Button.vue';
```

### Feature Module Pattern

```
features/products/
├── components/          # Feature-specific components
│   ├── ProductCard.vue
│   ├── ProductList.vue
│   └── ProductFilters.vue
├── composables/         # Feature-specific composables
│   ├── useProducts.ts
│   └── useProductFilters.ts
├── api/                 # API functions
│   └── productApi.ts
├── types.ts            # Feature types
└── index.ts            # Public exports
```

```typescript
// features/products/index.ts
// Components
export { default as ProductCard } from './components/ProductCard.vue';
export { default as ProductList } from './components/ProductList.vue';

// Composables
export { useProducts } from './composables/useProducts';

// Types
export type { Product, ProductFilters } from './types';
```

## File Naming Conventions

### Components
- PascalCase: `ProductCard.vue`, `UserProfile.vue`
- Prefix with feature context: `AuthLoginForm.vue`

### Composables
- camelCase with `use` prefix: `useAuth.ts`, `useProducts.ts`

### Stores
- camelCase with `use` prefix: `useAuthStore.ts`

### Types
- PascalCase for interfaces/types: `User`, `Product`
- camelCase for files: `types.ts`, `api.ts`

### Pages
- PascalCase with `Page` suffix: `HomePage.vue`, `ProductDetailPage.vue`

## Configuration Files

### vite.config.ts

```typescript
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import { fileURLToPath, URL } from 'node:url';

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 3000,
  },
});
```

### tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "module": "ESNext",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "preserve",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src/**/*.ts", "src/**/*.tsx", "src/**/*.vue"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

## Barrel Exports

### Component Barrel

```typescript
// components/ui/index.ts
export { Button } from './Button';
export { Input } from './Input';
export { Modal } from './Modal';
export { Card } from './Card';
export { Spinner } from './Spinner';

// Usage
import { Button, Input, Modal } from '@/components/ui';
```

### Composable Barrel

```typescript
// composables/index.ts
export { useAuth } from './useAuth';
export { useApi } from './useApi';
export { useForm } from './useForm';
export { useLocalStorage } from './useLocalStorage';
export { useDebounce } from './useDebounce';

// Usage
import { useAuth, useApi } from '@/composables';
```

## Import Order Convention

```vue
<script setup lang="ts">
// 1. Vue core
import { ref, computed, watch, onMounted } from 'vue';

// 2. Vue ecosystem
import { useRoute, useRouter } from 'vue-router';
import { storeToRefs } from 'pinia';

// 3. Third-party libraries
import { useForm } from 'vee-validate';
import { z } from 'zod';

// 4. Internal - stores
import { useAuthStore } from '@/stores/useAuthStore';

// 5. Internal - composables
import { useApi } from '@/composables/useApi';

// 6. Internal - components
import { Button, Input } from '@/components/ui';

// 7. Internal - types
import type { User } from '@/types';

// 8. Relative imports
import ProductCard from './ProductCard.vue';
</script>
```

## Best Practices

1. **Flat is better** - Avoid deep nesting
2. **Feature isolation** - Keep related code together
3. **Barrel exports** - Use index.ts for clean imports
4. **Type co-location** - Keep types near usage
5. **Test co-location** - Tests next to source files
