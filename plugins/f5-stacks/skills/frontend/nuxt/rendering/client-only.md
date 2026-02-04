---
name: nuxt-client-only
description: Client-side only rendering in Nuxt 3
applies_to: nuxt
---

# Client-Only Rendering in Nuxt 3

## Overview

Some components or pages need to render only on the client, typically for browser-specific features, third-party libraries, or admin panels.

## ClientOnly Component

### Basic Usage
```vue
<template>
  <div>
    <!-- Server-rendered content -->
    <h1>Page Title</h1>

    <!-- Client-only content -->
    <ClientOnly>
      <BrowserOnlyComponent />
    </ClientOnly>
  </div>
</template>
```

### With Fallback
```vue
<template>
  <ClientOnly>
    <HeavyChart :data="chartData" />

    <!-- Shown during SSR and hydration -->
    <template #fallback>
      <div class="skeleton-chart">
        <USkeleton class="h-64 w-full" />
        <p class="text-gray-500">Loading chart...</p>
      </div>
    </template>
  </ClientOnly>
</template>
```

## Client-Only Pages

### Route Rules
```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  routeRules: {
    // Entire section as SPA
    '/admin/**': { ssr: false },
    '/dashboard/**': { ssr: false },
  },
});
```

### Page Meta
```vue
<!-- pages/admin/index.vue -->
<script setup lang="ts">
definePageMeta({
  ssr: false, // This page won't SSR
});
</script>

<template>
  <AdminDashboard />
</template>
```

## .client.vue Components

Components ending in `.client.vue` auto-wrap in ClientOnly.

```
components/
├── ThirdPartyMap.client.vue    # Auto client-only
├── AnalyticsTracker.client.vue
└── Button.vue                   # Normal SSR
```

```vue
<!-- components/ThirdPartyMap.client.vue -->
<script setup lang="ts">
import { Map } from 'third-party-map-library';

const mapContainer = ref<HTMLElement>();

onMounted(() => {
  const map = new Map(mapContainer.value);
  // Initialize map...
});
</script>

<template>
  <div ref="mapContainer" class="map-container" />
</template>
```

Usage (automatically client-only):
```vue
<template>
  <!-- No ClientOnly wrapper needed -->
  <ThirdPartyMap :center="coordinates" />
</template>
```

## Client-Only Logic

### Conditional Execution
```vue
<script setup lang="ts">
// Check environment
if (import.meta.client) {
  // Browser-only code
  window.addEventListener('resize', handleResize);
}

if (import.meta.server) {
  // Server-only code
  console.log('Running on server');
}

// Lifecycle hooks (client only)
onMounted(() => {
  // Safe to use browser APIs
  const width = window.innerWidth;
  document.title = 'Custom Title';
});
</script>
```

### Lazy Client Components
```vue
<script setup lang="ts">
// Import client-only with lazy loading
const LazyEditor = defineAsyncComponent(() =>
  import('~/components/Editor.vue')
);

const showEditor = ref(false);
</script>

<template>
  <button @click="showEditor = true">Open Editor</button>

  <ClientOnly v-if="showEditor">
    <Suspense>
      <LazyEditor />
      <template #fallback>
        <p>Loading editor...</p>
      </template>
    </Suspense>
  </ClientOnly>
</template>
```

## Common Use Cases

### Third-Party Libraries
```vue
<!-- components/GoogleMap.client.vue -->
<script setup lang="ts">
import { Loader } from '@googlemaps/js-api-loader';

const mapContainer = ref<HTMLElement>();

onMounted(async () => {
  const loader = new Loader({
    apiKey: 'YOUR_API_KEY',
    version: 'weekly',
  });

  const google = await loader.load();
  new google.maps.Map(mapContainer.value!, {
    center: { lat: -34.397, lng: 150.644 },
    zoom: 8,
  });
});
</script>

<template>
  <div ref="mapContainer" class="h-96 w-full" />
</template>
```

### Browser Storage
```vue
<script setup lang="ts">
// Safe client-only storage access
const theme = ref('light');

onMounted(() => {
  theme.value = localStorage.getItem('theme') || 'light';
});

watch(theme, (newTheme) => {
  localStorage.setItem('theme', newTheme);
});
</script>
```

### Canvas/WebGL
```vue
<!-- components/Canvas3D.client.vue -->
<script setup lang="ts">
import * as THREE from 'three';

const container = ref<HTMLElement>();

onMounted(() => {
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(75, 1, 0.1, 1000);
  const renderer = new THREE.WebGLRenderer();

  container.value?.appendChild(renderer.domElement);

  // Animation loop...
});
</script>

<template>
  <div ref="container" class="canvas-container" />
</template>
```

### Authentication UI
```vue
<!-- components/UserMenu.client.vue -->
<script setup lang="ts">
const { user, logout } = useAuth();
</script>

<template>
  <div v-if="user" class="user-menu">
    <span>{{ user.name }}</span>
    <button @click="logout">Logout</button>
  </div>
  <NuxtLink v-else to="/login">Login</NuxtLink>
</template>
```

## Handling Hydration

### Prevent Mismatch
```vue
<script setup lang="ts">
// Bad - different on server/client
const timestamp = Date.now();

// Good - use useAsyncData for consistent data
const { data: serverTime } = await useAsyncData('time', () =>
  Promise.resolve(Date.now())
);

// Good - client-only for dynamic values
const clientTime = ref<number>();
onMounted(() => {
  clientTime.value = Date.now();
});
</script>

<template>
  <div>
    <!-- Safe - same on both -->
    <p>Server time: {{ serverTime }}</p>

    <!-- Safe - only renders on client -->
    <ClientOnly>
      <p>Client time: {{ clientTime }}</p>
    </ClientOnly>
  </div>
</template>
```

## Performance Considerations

1. **Minimize ClientOnly** - Use sparingly, prefer SSR
2. **Lazy load heavy components** - Reduce initial bundle
3. **Provide meaningful fallbacks** - Better UX during hydration
4. **Group client components** - Reduce wrapper overhead

```vue
<!-- Good - grouped client-only -->
<ClientOnly>
  <div class="client-widgets">
    <AnalyticsTracker />
    <ChatWidget />
    <NotificationBell />
  </div>
  <template #fallback>
    <div class="skeleton-widgets" />
  </template>
</ClientOnly>
```
