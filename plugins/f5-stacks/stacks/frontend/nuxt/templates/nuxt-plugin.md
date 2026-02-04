---
name: nuxt-plugin
description: Template for Nuxt 3 plugins
applies_to: nuxt
---

# Nuxt Plugin Template

## Basic Plugin

```typescript
// plugins/{{PLUGIN_NAME}}.ts
export default defineNuxtPlugin((nuxtApp) => {
  // Plugin logic here

  // Provide helper
  return {
    provide: {
      {{PLUGIN_NAME}}: {
        hello: (name: string) => `Hello, ${name}!`,
      },
    },
  };
});
```

Usage:

```vue
<script setup lang="ts">
const { ${{PLUGIN_NAME}} } = useNuxtApp();
console.log(${{PLUGIN_NAME}}.hello('World'));
</script>
```

## Client-Only Plugin

```typescript
// plugins/{{PLUGIN_NAME}}.client.ts
export default defineNuxtPlugin((nuxtApp) => {
  // Only runs on client

  // Access browser APIs
  const storage = window.localStorage;

  return {
    provide: {
      storage: {
        get: (key: string) => storage.getItem(key),
        set: (key: string, value: string) => storage.setItem(key, value),
        remove: (key: string) => storage.removeItem(key),
      },
    },
  };
});
```

## Server-Only Plugin

```typescript
// plugins/{{PLUGIN_NAME}}.server.ts
export default defineNuxtPlugin((nuxtApp) => {
  // Only runs on server

  return {
    provide: {
      serverInfo: {
        nodeVersion: process.version,
        env: process.env.NODE_ENV,
      },
    },
  };
});
```

## Third-Party Integration Plugin

```typescript
// plugins/analytics.client.ts
export default defineNuxtPlugin((nuxtApp) => {
  const config = useRuntimeConfig();

  // Initialize analytics
  if (config.public.analyticsId) {
    // Example: Google Analytics
    window.gtag?.('config', config.public.analyticsId);
  }

  // Track page views
  nuxtApp.hook('page:finish', () => {
    window.gtag?.('event', 'page_view', {
      page_path: useRoute().fullPath,
    });
  });

  return {
    provide: {
      trackEvent: (name: string, params?: Record<string, unknown>) => {
        window.gtag?.('event', name, params);
      },
    },
  };
});
```

## Error Handling Plugin

```typescript
// plugins/error-handler.ts
export default defineNuxtPlugin((nuxtApp) => {
  nuxtApp.vueApp.config.errorHandler = (error, instance, info) => {
    console.error('Vue Error:', error);
    console.error('Component:', instance);
    console.error('Info:', info);

    // Report to error tracking service
    if (import.meta.client) {
      // Example: Sentry
      // Sentry.captureException(error);
    }
  };

  // Handle unhandled rejections
  if (import.meta.client) {
    window.addEventListener('unhandledrejection', (event) => {
      console.error('Unhandled Promise Rejection:', event.reason);
    });
  }
});
```

## Authentication Plugin

```typescript
// plugins/auth.ts
export default defineNuxtPlugin(async (nuxtApp) => {
  const auth = useAuth();

  // Initialize auth state
  if (import.meta.server) {
    const token = useCookie('auth-token');
    if (token.value) {
      await auth.initialize(token.value);
    }
  }

  // Add auth headers to fetch
  nuxtApp.hook('app:created', () => {
    const originalFetch = globalThis.$fetch;

    globalThis.$fetch = ((url: string, options: any = {}) => {
      const token = useCookie('auth-token');

      if (token.value) {
        options.headers = {
          ...options.headers,
          Authorization: `Bearer ${token.value}`,
        };
      }

      return originalFetch(url, options);
    }) as typeof globalThis.$fetch;
  });
});
```

## Toast/Notification Plugin

```typescript
// plugins/toast.client.ts
interface ToastOptions {
  message: string;
  type?: 'success' | 'error' | 'warning' | 'info';
  duration?: number;
}

export default defineNuxtPlugin((nuxtApp) => {
  const toasts = useState<ToastOptions[]>('toasts', () => []);

  function show(options: ToastOptions) {
    const toast = {
      ...options,
      type: options.type || 'info',
      duration: options.duration || 3000,
    };

    toasts.value.push(toast);

    setTimeout(() => {
      const index = toasts.value.indexOf(toast);
      if (index > -1) {
        toasts.value.splice(index, 1);
      }
    }, toast.duration);
  }

  return {
    provide: {
      toast: {
        show,
        success: (message: string) => show({ message, type: 'success' }),
        error: (message: string) => show({ message, type: 'error' }),
        warning: (message: string) => show({ message, type: 'warning' }),
        info: (message: string) => show({ message, type: 'info' }),
      },
    },
  };
});
```

## Directive Plugin

```typescript
// plugins/directives.ts
export default defineNuxtPlugin((nuxtApp) => {
  // v-focus directive
  nuxtApp.vueApp.directive('focus', {
    mounted(el) {
      el.focus();
    },
  });

  // v-click-outside directive
  nuxtApp.vueApp.directive('click-outside', {
    mounted(el, binding) {
      el._clickOutside = (event: MouseEvent) => {
        if (!(el === event.target || el.contains(event.target as Node))) {
          binding.value(event);
        }
      };
      document.addEventListener('click', el._clickOutside);
    },
    unmounted(el) {
      document.removeEventListener('click', el._clickOutside);
    },
  });

  // v-tooltip directive
  nuxtApp.vueApp.directive('tooltip', {
    mounted(el, binding) {
      el.setAttribute('title', binding.value);
      // Add tooltip styling
    },
  });
});
```

## WebSocket Plugin

```typescript
// plugins/websocket.client.ts
export default defineNuxtPlugin((nuxtApp) => {
  const config = useRuntimeConfig();

  let ws: WebSocket | null = null;
  const isConnected = ref(false);
  const messages = ref<unknown[]>([]);

  function connect() {
    ws = new WebSocket(config.public.wsUrl);

    ws.onopen = () => {
      isConnected.value = true;
    };

    ws.onclose = () => {
      isConnected.value = false;
      // Reconnect after delay
      setTimeout(connect, 5000);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      messages.value.push(data);
    };
  }

  function send(data: unknown) {
    if (ws && isConnected.value) {
      ws.send(JSON.stringify(data));
    }
  }

  function disconnect() {
    ws?.close();
  }

  // Auto-connect
  connect();

  // Cleanup on app unmount
  nuxtApp.hook('app:beforeMount', () => {
    window.addEventListener('beforeunload', disconnect);
  });

  return {
    provide: {
      ws: {
        isConnected: readonly(isConnected),
        messages: readonly(messages),
        send,
        connect,
        disconnect,
      },
    },
  };
});
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{PLUGIN_NAME}}` | Plugin identifier | `myPlugin`, `analytics` |
