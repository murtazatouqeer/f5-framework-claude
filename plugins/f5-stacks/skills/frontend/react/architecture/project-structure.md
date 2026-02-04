# React Project Structure

## Overview

Feature-based project organization for scalable React applications.

## Recommended Structure

```
src/
├── app/                       # App setup and configuration
│   ├── App.tsx               # Root component
│   ├── routes.tsx            # Route definitions
│   └── providers.tsx         # Provider composition
│
├── components/                # Shared components
│   ├── ui/                   # Base UI components
│   │   ├── Button/
│   │   ├── Input/
│   │   ├── Modal/
│   │   └── index.ts
│   ├── forms/                # Form components
│   │   ├── FormField/
│   │   ├── Select/
│   │   └── index.ts
│   └── layouts/              # Layout components
│       ├── PageLayout/
│       ├── DashboardLayout/
│       └── index.ts
│
├── features/                  # Feature modules
│   └── {feature}/
│       ├── components/       # Feature-specific components
│       ├── hooks/            # Feature-specific hooks
│       ├── api/              # API layer
│       ├── stores/           # Feature state
│       ├── types.ts          # Feature types
│       └── index.ts          # Public exports
│
├── hooks/                     # Shared hooks
│   ├── useAuth.ts
│   ├── useDebounce.ts
│   └── index.ts
│
├── lib/                       # Utilities and helpers
│   ├── api.ts                # API client
│   ├── utils.ts              # Utility functions
│   └── constants.ts          # App constants
│
├── stores/                    # Global state
│   ├── auth.store.ts
│   └── ui.store.ts
│
├── types/                     # Global types
│   ├── api.types.ts
│   └── common.types.ts
│
└── styles/                    # Global styles
    ├── globals.css
    └── variables.css
```

## Component Structure

### Feature Module Example

```
src/features/products/
├── components/
│   ├── ProductCard/
│   │   ├── ProductCard.tsx
│   │   ├── ProductCard.test.tsx
│   │   └── index.ts
│   ├── ProductList/
│   │   ├── ProductList.tsx
│   │   ├── ProductList.test.tsx
│   │   └── index.ts
│   └── ProductForm/
│       ├── ProductForm.tsx
│       ├── ProductForm.test.tsx
│       └── index.ts
├── hooks/
│   ├── useProducts.ts
│   └── useProductMutation.ts
├── api/
│   └── products.api.ts
├── stores/
│   └── products.store.ts
├── schemas/
│   └── product.schema.ts
├── types.ts
└── index.ts
```

### Component Folder Structure

```
ComponentName/
├── ComponentName.tsx         # Main component
├── ComponentName.test.tsx    # Tests
├── ComponentName.stories.tsx # Storybook (optional)
└── index.ts                  # Export
```

## Barrel Exports

### Component Index

```tsx
// src/components/ui/index.ts
export { Button } from './Button';
export { Input } from './Input';
export { Modal } from './Modal';
export { Card } from './Card';
```

### Feature Index

```tsx
// src/features/products/index.ts
// Components
export { ProductCard } from './components/ProductCard';
export { ProductList } from './components/ProductList';
export { ProductForm } from './components/ProductForm';

// Hooks
export { useProducts } from './hooks/useProducts';
export { useProductMutation } from './hooks/useProductMutation';

// Types
export type { Product, CreateProductInput } from './types';
```

## Import Patterns

### Path Aliases

```json
// tsconfig.json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"],
      "@/components/*": ["src/components/*"],
      "@/features/*": ["src/features/*"],
      "@/hooks/*": ["src/hooks/*"],
      "@/lib/*": ["src/lib/*"],
      "@/stores/*": ["src/stores/*"],
      "@/types/*": ["src/types/*"]
    }
  }
}
```

### Import Order

```tsx
// 1. React and external libraries
import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';

// 2. Internal modules (absolute imports)
import { Button } from '@/components/ui';
import { useAuth } from '@/hooks';

// 3. Feature imports
import { ProductCard } from '../components/ProductCard';

// 4. Types
import type { Product } from '../types';

// 5. Styles (if using CSS modules)
import styles from './Component.module.css';
```

## Configuration Files

### Essential Config

```
project-root/
├── .env                      # Environment variables
├── .env.example              # Example env file
├── .eslintrc.cjs             # ESLint config
├── .prettierrc               # Prettier config
├── tsconfig.json             # TypeScript config
├── vite.config.ts            # Vite config
├── vitest.config.ts          # Vitest config
└── tailwind.config.js        # Tailwind config
```

## Best Practices

### Do's

- Keep feature modules self-contained
- Use barrel exports for clean imports
- Colocate tests with components
- Use path aliases for cleaner imports
- Keep shared components truly generic

### Don'ts

- Avoid deep nesting (max 3-4 levels)
- Don't import across features directly
- Don't put business logic in components
- Avoid circular dependencies
- Don't mix concerns in single files
