---
name: nuxt-shared-state
description: Shared state patterns in Nuxt 3
applies_to: nuxt
---

# Shared State Patterns in Nuxt 3

## Overview

Multiple approaches for sharing state across components in Nuxt 3, each with different trade-offs.

## State Options Comparison

| Feature | useState | Pinia | Provide/Inject | Cookies |
|---------|----------|-------|----------------|---------|
| SSR-safe | ✅ | ✅ | ✅ | ✅ |
| DevTools | ❌ | ✅ | ❌ | ❌ |
| Persistence | ❌ | Plugin | ❌ | ✅ |
| Complexity | Low | Medium | Low | Low |
| Best for | Simple global | Complex apps | Component tree | Auth tokens |

## useState Pattern

```typescript
// composables/useGlobalState.ts
export function useCounter() {
  const count = useState('counter', () => 0);

  function increment() {
    count.value++;
  }

  function decrement() {
    count.value--;
  }

  function reset() {
    count.value = 0;
  }

  return {
    count: readonly(count),
    increment,
    decrement,
    reset,
  };
}
```

## Provide/Inject Pattern

### Layout Provider

```vue
<!-- layouts/default.vue -->
<script setup lang="ts">
import type { InjectionKey, Ref } from 'vue';

// Define injection key
export const SIDEBAR_KEY: InjectionKey<{
  isOpen: Ref<boolean>;
  toggle: () => void;
}> = Symbol('sidebar');

const isOpen = ref(true);
const toggle = () => (isOpen.value = !isOpen.value);

provide(SIDEBAR_KEY, { isOpen, toggle });
</script>

<template>
  <div class="layout">
    <Sidebar v-if="isOpen" />
    <main>
      <slot />
    </main>
  </div>
</template>
```

### Consuming in Components

```vue
<!-- components/SidebarToggle.vue -->
<script setup lang="ts">
import { SIDEBAR_KEY } from '~/layouts/default.vue';

const sidebar = inject(SIDEBAR_KEY);

if (!sidebar) {
  throw new Error('SidebarToggle must be used within default layout');
}
</script>

<template>
  <button @click="sidebar.toggle">
    {{ sidebar.isOpen ? 'Close' : 'Open' }} Sidebar
  </button>
</template>
```

### Composable with Provide/Inject

```typescript
// composables/useModal.ts
import type { InjectionKey, Ref } from 'vue';

interface ModalContext {
  isOpen: Ref<boolean>;
  data: Ref<unknown>;
  open: (payload?: unknown) => void;
  close: () => void;
}

export const MODAL_KEY: InjectionKey<ModalContext> = Symbol('modal');

export function provideModal() {
  const isOpen = ref(false);
  const data = ref<unknown>(null);

  function open(payload?: unknown) {
    data.value = payload;
    isOpen.value = true;
  }

  function close() {
    isOpen.value = false;
    data.value = null;
  }

  const context: ModalContext = {
    isOpen,
    data,
    open,
    close,
  };

  provide(MODAL_KEY, context);

  return context;
}

export function useModal() {
  const context = inject(MODAL_KEY);

  if (!context) {
    throw new Error('useModal must be used within modal provider');
  }

  return context;
}
```

## Cookie-Based State

### Authentication Token

```typescript
// composables/useAuthToken.ts
export function useAuthToken() {
  const token = useCookie('auth-token', {
    maxAge: 60 * 60 * 24 * 7, // 7 days
    secure: true,
    httpOnly: false, // Client needs access
    sameSite: 'lax',
  });

  function setToken(newToken: string) {
    token.value = newToken;
  }

  function clearToken() {
    token.value = null;
  }

  return {
    token: readonly(token),
    setToken,
    clearToken,
  };
}
```

### User Preferences

```typescript
// composables/usePreferences.ts
interface Preferences {
  theme: 'light' | 'dark' | 'system';
  language: string;
  notifications: boolean;
}

export function usePreferences() {
  const prefs = useCookie<Preferences>('preferences', {
    default: () => ({
      theme: 'system',
      language: 'en',
      notifications: true,
    }),
    maxAge: 60 * 60 * 24 * 365, // 1 year
  });

  function updatePreference<K extends keyof Preferences>(
    key: K,
    value: Preferences[K]
  ) {
    prefs.value = {
      ...prefs.value,
      [key]: value,
    };
  }

  return {
    preferences: readonly(prefs),
    updatePreference,
  };
}
```

## Event Bus Pattern

```typescript
// composables/useEventBus.ts
type EventCallback = (...args: any[]) => void;

const events = new Map<string, Set<EventCallback>>();

export function useEventBus() {
  function on(event: string, callback: EventCallback) {
    if (!events.has(event)) {
      events.set(event, new Set());
    }
    events.get(event)!.add(callback);

    // Return cleanup function
    return () => {
      events.get(event)?.delete(callback);
    };
  }

  function emit(event: string, ...args: any[]) {
    events.get(event)?.forEach((callback) => callback(...args));
  }

  function off(event: string, callback?: EventCallback) {
    if (callback) {
      events.get(event)?.delete(callback);
    } else {
      events.delete(event);
    }
  }

  return { on, emit, off };
}

// Usage
const bus = useEventBus();

// Component A - emit
bus.emit('product:added', { id: '123', name: 'Product' });

// Component B - listen
onMounted(() => {
  const cleanup = bus.on('product:added', (product) => {
    console.log('Product added:', product);
  });

  onUnmounted(cleanup);
});
```

## Shared Composables

```typescript
// composables/useNotifications.ts
interface Notification {
  id: string;
  type: 'success' | 'error' | 'info' | 'warning';
  message: string;
  timeout?: number;
}

export function useNotifications() {
  const notifications = useState<Notification[]>('notifications', () => []);

  function add(notification: Omit<Notification, 'id'>) {
    const id = crypto.randomUUID();
    const newNotification = { ...notification, id };

    notifications.value.push(newNotification);

    // Auto-remove after timeout
    if (notification.timeout !== 0) {
      setTimeout(() => {
        remove(id);
      }, notification.timeout ?? 5000);
    }
  }

  function remove(id: string) {
    notifications.value = notifications.value.filter((n) => n.id !== id);
  }

  function clear() {
    notifications.value = [];
  }

  // Convenience methods
  function success(message: string, timeout?: number) {
    add({ type: 'success', message, timeout });
  }

  function error(message: string, timeout?: number) {
    add({ type: 'error', message, timeout });
  }

  function info(message: string, timeout?: number) {
    add({ type: 'info', message, timeout });
  }

  function warning(message: string, timeout?: number) {
    add({ type: 'warning', message, timeout });
  }

  return {
    notifications: readonly(notifications),
    add,
    remove,
    clear,
    success,
    error,
    info,
    warning,
  };
}
```

## Combined State Pattern

```typescript
// composables/useAppState.ts
export function useAppState() {
  // Use different state mechanisms for different needs
  const auth = useAuth();              // useState for user
  const cart = useCartStore();         // Pinia for complex cart
  const prefs = usePreferences();      // Cookie for persistence
  const notifications = useNotifications(); // useState for UI

  // Computed convenience getters
  const isReady = computed(() =>
    auth.isAuthenticated && !auth.isLoading
  );

  // Combined actions
  async function logout() {
    await auth.logout();
    cart.$reset();
    notifications.success('Logged out successfully');
  }

  return {
    auth,
    cart,
    prefs,
    notifications,
    isReady,
    logout,
  };
}
```

## Best Practices

1. **Choose appropriately** - useState for simple, Pinia for complex
2. **Avoid prop drilling** - Use provide/inject for deep trees
3. **Cookies for persistence** - Auth tokens, preferences
4. **Keep state close** - Component state when possible
5. **Composables for abstraction** - Wrap state in reusable functions
6. **Type everything** - Full TypeScript support
