---
name: nuxt-project-structure
description: Nuxt 3 project organization and directory structure
applies_to: nuxt
---

# Nuxt 3 Project Structure

## Overview

Nuxt 3 uses a convention-based directory structure with auto-imports and file-based routing.

## Standard Directory Structure

```
project/
├── .nuxt/                     # Build directory (gitignore)
├── .output/                   # Production build (gitignore)
├── app/                       # Application source (Nuxt 3.8+)
│   ├── components/            # Auto-imported components
│   ├── composables/           # Auto-imported composables
│   ├── layouts/               # Page layouts
│   ├── middleware/            # Route middleware
│   ├── pages/                 # File-based routes
│   ├── plugins/               # Nuxt plugins
│   └── utils/                 # Auto-imported utilities
├── assets/                    # Build-processed assets
├── content/                   # Content files (with @nuxt/content)
├── layers/                    # Nuxt layers
├── modules/                   # Local modules
├── public/                    # Static files
├── server/                    # Server-side code
│   ├── api/                   # API routes
│   ├── middleware/            # Server middleware
│   ├── plugins/               # Server plugins
│   ├── routes/                # Custom server routes
│   └── utils/                 # Server utilities
├── app.config.ts              # Runtime config
├── app.vue                    # Root component
├── error.vue                  # Error page
├── nuxt.config.ts             # Nuxt configuration
├── package.json
└── tsconfig.json
```

## Directory Purposes

### app/ Directory (Recommended)

The `app/` directory contains all application code. Nuxt 3.8+ recommends this structure.

```typescript
// nuxt.config.ts - Enable app/ directory
export default defineNuxtConfig({
  // Automatically enabled in Nuxt 3.8+
  future: {
    compatibilityVersion: 4,
  },
});
```

### components/

Auto-imported Vue components.

```
components/
├── ui/                        # Base UI components
│   ├── Button.vue
│   ├── Input.vue
│   └── Modal.vue
├── forms/                     # Form components
│   ├── LoginForm.vue
│   └── SearchForm.vue
├── layouts/                   # Layout components
│   ├── Header.vue
│   └── Footer.vue
└── features/                  # Feature components
    └── products/
        ├── ProductCard.vue
        └── ProductList.vue
```

Component naming and import:
```vue
<!-- Auto-import paths -->
<UiButton />           <!-- components/ui/Button.vue -->
<FormsLoginForm />     <!-- components/forms/LoginForm.vue -->
<ProductCard />        <!-- components/features/products/ProductCard.vue -->
```

### composables/

Auto-imported composables.

```
composables/
├── useAuth.ts
├── useProducts.ts
├── useAsync.ts
└── api/
    ├── useProductsApi.ts
    └── useUsersApi.ts
```

### pages/

File-based routing pages.

```
pages/
├── index.vue                  # /
├── about.vue                  # /about
├── products/
│   ├── index.vue              # /products
│   └── [id].vue               # /products/:id
├── [...slug].vue              # Catch-all route
└── users/
    └── [id]/
        ├── index.vue          # /users/:id
        └── settings.vue       # /users/:id/settings
```

### server/

Server-side code with Nitro.

```
server/
├── api/                       # /api/* routes
│   ├── products/
│   │   ├── index.get.ts       # GET /api/products
│   │   ├── index.post.ts      # POST /api/products
│   │   └── [id].get.ts        # GET /api/products/:id
│   └── auth/
│       └── login.post.ts      # POST /api/auth/login
├── middleware/                # Server middleware
│   └── auth.ts
├── plugins/                   # Server plugins
│   └── database.ts
└── utils/                     # Server utilities
    ├── db.ts
    └── auth.ts
```

## Feature-Based Organization

For larger applications, organize by feature:

```
app/
├── features/
│   ├── products/
│   │   ├── components/
│   │   │   ├── ProductCard.vue
│   │   │   └── ProductList.vue
│   │   ├── composables/
│   │   │   └── useProducts.ts
│   │   ├── types/
│   │   │   └── index.ts
│   │   └── index.ts
│   └── auth/
│       ├── components/
│       ├── composables/
│       └── middleware/
├── components/                # Shared components
├── composables/               # Shared composables
└── utils/                     # Shared utilities
```

## Configuration Files

### nuxt.config.ts
```typescript
export default defineNuxtConfig({
  // App configuration
  app: {
    head: {
      title: 'My App',
      meta: [
        { name: 'description', content: 'My Nuxt app' },
      ],
    },
  },

  // Modules
  modules: [
    '@nuxt/ui',
    '@pinia/nuxt',
  ],

  // Runtime config
  runtimeConfig: {
    // Server-only
    apiSecret: '',
    // Public (exposed to client)
    public: {
      apiBase: '/api',
    },
  },

  // TypeScript
  typescript: {
    strict: true,
  },

  // DevTools
  devtools: { enabled: true },
});
```

### app.config.ts
```typescript
export default defineAppConfig({
  ui: {
    primary: 'blue',
    gray: 'slate',
  },
  // App-level configuration
  title: 'My App',
});
```

## Best Practices

1. **Use app/ directory** - Clean separation of concerns
2. **Feature-based organization** - For large applications
3. **Auto-imports** - Let Nuxt handle imports
4. **Server utilities** - Keep server code in server/
5. **Type safety** - Define types in dedicated files
6. **Environment config** - Use runtimeConfig for env vars
