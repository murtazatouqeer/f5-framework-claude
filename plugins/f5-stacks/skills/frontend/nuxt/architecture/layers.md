---
name: nuxt-layers
description: Nuxt 3 layers for code sharing and extension
applies_to: nuxt
---

# Nuxt Layers

## Overview

Nuxt Layers allow you to extend and share Nuxt configurations, components, composables, and more between projects.

## Layer Types

### 1. Local Layers
Extend from local directories.

### 2. npm Packages
Install as dependencies.

### 3. Git Repositories
Extend from remote git repos.

## Creating a Layer

### Basic Layer Structure
```
layers/
└── base/
    ├── components/
    │   └── BaseButton.vue
    ├── composables/
    │   └── useLogger.ts
    ├── layouts/
    │   └── admin.vue
    ├── plugins/
    │   └── logger.ts
    ├── server/
    │   └── utils/
    │       └── db.ts
    ├── nuxt.config.ts
    └── package.json
```

### Layer nuxt.config.ts
```typescript
// layers/base/nuxt.config.ts
export default defineNuxtConfig({
  // Layer-specific configuration
  components: [
    { path: './components', prefix: 'Base' },
  ],

  // Modules the layer provides
  modules: [
    '@nuxtjs/tailwindcss',
  ],

  // Runtime config defaults
  runtimeConfig: {
    public: {
      apiBase: '/api',
    },
  },
});
```

### Layer package.json
```json
{
  "name": "@company/nuxt-layer-base",
  "version": "1.0.0",
  "main": "./nuxt.config.ts",
  "dependencies": {
    "@nuxtjs/tailwindcss": "^6.0.0"
  }
}
```

## Using Layers

### In nuxt.config.ts
```typescript
export default defineNuxtConfig({
  extends: [
    // Local layer
    './layers/base',

    // npm package
    '@company/nuxt-layer-base',

    // Git repository
    'github:user/repo',
    'github:user/repo#branch',
    'github:user/repo/path/to/layer',

    // GitLab
    'gitlab:user/repo',
  ],
});
```

### With Authentication
```typescript
export default defineNuxtConfig({
  extends: [
    ['github:org/private-layer', { auth: process.env.GITHUB_TOKEN }],
  ],
});
```

## Layer Features

### Components
```
layers/base/components/
├── BaseButton.vue
├── BaseCard.vue
└── forms/
    └── BaseInput.vue
```

```vue
<!-- App can use layer components -->
<template>
  <BaseButton>Click</BaseButton>
  <FormsBaseInput v-model="value" />
</template>
```

### Composables
```typescript
// layers/base/composables/useLogger.ts
export function useLogger(prefix: string) {
  const log = (message: string) => {
    console.log(`[${prefix}] ${message}`);
  };

  const error = (message: string) => {
    console.error(`[${prefix}] ${message}`);
  };

  return { log, error };
}

// Available in extending app
const logger = useLogger('MyApp');
logger.log('Hello');
```

### Layouts
```vue
<!-- layers/base/layouts/admin.vue -->
<template>
  <div class="admin-layout">
    <aside>
      <slot name="sidebar" />
    </aside>
    <main>
      <slot />
    </main>
  </div>
</template>

<!-- App can use: -->
<script setup>
definePageMeta({
  layout: 'admin',
});
</script>
```

### Server Utilities
```typescript
// layers/base/server/utils/db.ts
import { PrismaClient } from '@prisma/client';

const globalForPrisma = globalThis as { prisma?: PrismaClient };

export const prisma = globalForPrisma.prisma ?? new PrismaClient();

if (process.env.NODE_ENV !== 'production') {
  globalForPrisma.prisma = prisma;
}

// Available in app's server code
export default defineEventHandler(async () => {
  const users = await prisma.user.findMany();
  return users;
});
```

## Common Layer Patterns

### UI Layer
```
layers/ui/
├── components/
│   ├── Button.vue
│   ├── Card.vue
│   ├── Modal.vue
│   └── ...
├── composables/
│   └── useModal.ts
├── assets/
│   └── css/
│       └── base.css
├── nuxt.config.ts
└── package.json
```

### Auth Layer
```
layers/auth/
├── components/
│   ├── LoginForm.vue
│   └── UserMenu.vue
├── composables/
│   └── useAuth.ts
├── middleware/
│   └── auth.ts
├── server/
│   ├── api/
│   │   └── auth/
│   │       ├── login.post.ts
│   │       ├── logout.post.ts
│   │       └── me.get.ts
│   └── utils/
│       └── auth.ts
├── nuxt.config.ts
└── package.json
```

### Admin Layer
```
layers/admin/
├── layouts/
│   └── admin.vue
├── pages/
│   └── admin/
│       ├── index.vue
│       └── users/
│           └── index.vue
├── middleware/
│   └── admin.ts
└── nuxt.config.ts
```

## Layer Configuration Merging

Configurations are merged with the app's config:

```typescript
// Layer: layers/base/nuxt.config.ts
export default defineNuxtConfig({
  modules: ['@nuxtjs/tailwindcss'],
  runtimeConfig: {
    public: {
      apiBase: '/api',
    },
  },
});

// App: nuxt.config.ts
export default defineNuxtConfig({
  extends: ['./layers/base'],
  modules: ['@pinia/nuxt'],  // Added to layer modules
  runtimeConfig: {
    public: {
      apiBase: '/api/v2',    // Overrides layer config
      appName: 'My App',     // Extends layer config
    },
  },
});
```

## Multi-Layer Architecture

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  extends: [
    // Order matters - later layers override earlier ones
    './layers/base',        // Base configuration
    './layers/ui',          // UI components
    './layers/auth',        // Authentication
    './layers/admin',       // Admin features
  ],
});
```

## Best Practices

1. **Single responsibility** - Each layer has one clear purpose
2. **Minimal dependencies** - Keep layers lightweight
3. **Proper versioning** - Use semantic versioning for npm layers
4. **Documentation** - Document what each layer provides
5. **Type exports** - Export types for consuming apps
6. **Override points** - Design for customization
