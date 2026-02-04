---
name: nuxt-modules
description: Nuxt 3 module system and ecosystem
applies_to: nuxt
---

# Nuxt Modules

## Overview

Nuxt modules extend Nuxt functionality with auto-configuration, components, composables, and server utilities.

## Installing Modules

```bash
# Using nuxi
npx nuxi@latest module add @nuxt/ui

# Or npm
npm install @nuxt/ui
```

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  modules: [
    '@nuxt/ui',
    '@pinia/nuxt',
    '@nuxtjs/tailwindcss',
  ],
});
```

## Essential Modules

### @nuxt/ui
```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  modules: ['@nuxt/ui'],

  ui: {
    global: true,
    icons: ['heroicons', 'lucide'],
  },
});
```

### @nuxt/content
```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  modules: ['@nuxt/content'],

  content: {
    highlight: {
      theme: 'github-dark',
    },
    markdown: {
      toc: { depth: 3 },
    },
  },
});
```

### @nuxt/image
```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  modules: ['@nuxt/image'],

  image: {
    quality: 80,
    format: ['webp', 'avif'],
    screens: {
      xs: 320,
      sm: 640,
      md: 768,
      lg: 1024,
      xl: 1280,
    },
  },
});
```

### @pinia/nuxt
```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  modules: ['@pinia/nuxt'],

  pinia: {
    autoImports: ['defineStore', 'storeToRefs'],
  },
});
```

### @nuxtjs/tailwindcss
```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  modules: ['@nuxtjs/tailwindcss'],

  tailwindcss: {
    cssPath: '~/assets/css/tailwind.css',
    configPath: 'tailwind.config.ts',
    exposeConfig: true,
  },
});
```

### @sidebase/nuxt-auth
```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  modules: ['@sidebase/nuxt-auth'],

  auth: {
    baseURL: '/api/auth',
    provider: {
      type: 'authjs',
    },
  },
});
```

### @nuxtjs/i18n
```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  modules: ['@nuxtjs/i18n'],

  i18n: {
    locales: [
      { code: 'en', file: 'en.json' },
      { code: 'ja', file: 'ja.json' },
    ],
    defaultLocale: 'en',
    lazy: true,
    langDir: 'locales',
  },
});
```

## Module Configuration

### Runtime Config
```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  modules: ['@nuxtjs/supabase'],

  supabase: {
    url: process.env.SUPABASE_URL,
    key: process.env.SUPABASE_KEY,
    redirect: true,
  },
});
```

### Module Options
```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  modules: [
    // Simple
    '@nuxt/ui',

    // With inline options
    ['@nuxtjs/google-fonts', {
      families: {
        'Inter': [400, 500, 600, 700],
      },
    }],
  ],

  // Or top-level config
  googleFonts: {
    families: {
      'Inter': [400, 500, 600, 700],
    },
  },
});
```

## Creating Custom Modules

### Local Module
```typescript
// modules/analytics/index.ts
import { defineNuxtModule, addPlugin, createResolver } from '@nuxt/kit';

export interface ModuleOptions {
  id: string;
  debug?: boolean;
}

export default defineNuxtModule<ModuleOptions>({
  meta: {
    name: 'analytics',
    configKey: 'analytics',
  },

  defaults: {
    debug: false,
  },

  setup(options, nuxt) {
    const resolver = createResolver(import.meta.url);

    // Add plugin
    addPlugin(resolver.resolve('./runtime/plugin'));

    // Add composables
    addImportsDir(resolver.resolve('./runtime/composables'));

    // Add components
    addComponentsDir({
      path: resolver.resolve('./runtime/components'),
    });

    // Inject runtime config
    nuxt.options.runtimeConfig.public.analytics = {
      id: options.id,
      debug: options.debug,
    };
  },
});
```

### Module Plugin
```typescript
// modules/analytics/runtime/plugin.ts
export default defineNuxtPlugin(() => {
  const config = useRuntimeConfig();
  const { id, debug } = config.public.analytics;

  // Initialize analytics
  if (import.meta.client) {
    initAnalytics(id, { debug });
  }

  return {
    provide: {
      analytics: {
        track: (event: string, data?: object) => {
          trackEvent(event, data);
        },
      },
    },
  };
});
```

### Module Composable
```typescript
// modules/analytics/runtime/composables/useAnalytics.ts
export function useAnalytics() {
  const { $analytics } = useNuxtApp();

  function trackPageView(path: string) {
    $analytics.track('page_view', { path });
  }

  function trackEvent(name: string, properties?: object) {
    $analytics.track(name, properties);
  }

  return {
    trackPageView,
    trackEvent,
  };
}
```

## Module Best Practices

### Directory Structure
```
modules/
└── my-module/
    ├── index.ts           # Module definition
    └── runtime/
        ├── plugin.ts      # Client/server plugin
        ├── composables/   # Auto-imported composables
        ├── components/    # Auto-imported components
        └── utils/         # Shared utilities
```

### Type Augmentation
```typescript
// modules/analytics/index.ts
declare module '#app' {
  interface NuxtApp {
    $analytics: {
      track: (event: string, data?: object) => void;
    };
  }
}

declare module '@nuxt/schema' {
  interface PublicRuntimeConfig {
    analytics: {
      id: string;
      debug: boolean;
    };
  }
}
```

## Common Module Patterns

### Add Route Middleware
```typescript
setup(options, nuxt) {
  addRouteMiddleware('analytics', () => {
    const { trackPageView } = useAnalytics();
    trackPageView(useRoute().path);
  }, { global: true });
}
```

### Add Server Handler
```typescript
setup(options, nuxt) {
  addServerHandler({
    route: '/api/_analytics',
    handler: resolver.resolve('./runtime/server/api/analytics'),
  });
}
```

### Extend Vite Config
```typescript
setup(options, nuxt) {
  nuxt.hook('vite:extend', ({ config }) => {
    config.optimizeDeps?.include?.push('my-dependency');
  });
}
```

## Best Practices

1. **Use official modules** - Well-maintained, tested
2. **Check compatibility** - Nuxt 3 vs Nuxt 2
3. **Configure properly** - Use runtimeConfig for secrets
4. **Avoid module bloat** - Only install what you need
5. **Create local modules** - For app-specific functionality
6. **Type your modules** - Full TypeScript support
