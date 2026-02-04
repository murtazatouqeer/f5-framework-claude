---
name: nuxt-layouts
description: Page layouts in Nuxt 3
applies_to: nuxt
---

# Layouts in Nuxt 3

## Overview

Layouts provide common UI structures (headers, sidebars, footers) that wrap page content.

## Default Layout

```vue
<!-- layouts/default.vue -->
<template>
  <div class="layout">
    <AppHeader />

    <main class="main-content">
      <slot />
    </main>

    <AppFooter />
  </div>
</template>

<style scoped>
.layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
}
</style>
```

## Custom Layouts

### Admin Layout

```vue
<!-- layouts/admin.vue -->
<template>
  <div class="admin-layout">
    <AdminSidebar />

    <div class="admin-main">
      <AdminHeader />

      <div class="admin-content">
        <slot />
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin-layout {
  display: flex;
  min-height: 100vh;
}

.admin-main {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.admin-content {
  flex: 1;
  padding: 1.5rem;
}
</style>
```

### Auth Layout

```vue
<!-- layouts/auth.vue -->
<template>
  <div class="auth-layout">
    <div class="auth-card">
      <div class="auth-logo">
        <Logo />
      </div>

      <slot />
    </div>
  </div>
</template>

<style scoped>
.auth-layout {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.auth-card {
  background: white;
  padding: 2rem;
  border-radius: 0.5rem;
  width: 100%;
  max-width: 400px;
}
</style>
```

### Blank Layout

```vue
<!-- layouts/blank.vue -->
<template>
  <div class="blank-layout">
    <slot />
  </div>
</template>

<style scoped>
.blank-layout {
  min-height: 100vh;
}
</style>
```

## Using Layouts in Pages

### definePageMeta

```vue
<!-- pages/admin/dashboard.vue -->
<script setup lang="ts">
definePageMeta({
  layout: 'admin',
});
</script>

<template>
  <div>
    <h1>Admin Dashboard</h1>
  </div>
</template>
```

### Dynamic Layout

```vue
<script setup lang="ts">
const route = useRoute();

// Change layout based on condition
definePageMeta({
  layout: false, // Disable default layout
});

const layout = computed(() => {
  return route.query.embedded ? 'blank' : 'default';
});
</script>

<template>
  <NuxtLayout :name="layout">
    <div>Page Content</div>
  </NuxtLayout>
</template>
```

### setPageLayout

```vue
<script setup lang="ts">
// Change layout programmatically
function switchToAdmin() {
  setPageLayout('admin');
}
</script>
```

## Layout with Props

```vue
<!-- layouts/dashboard.vue -->
<script setup lang="ts">
interface Props {
  title?: string;
  showSidebar?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  title: 'Dashboard',
  showSidebar: true,
});
</script>

<template>
  <div class="dashboard-layout">
    <DashboardSidebar v-if="showSidebar" />

    <div class="dashboard-main">
      <header class="dashboard-header">
        <h1>{{ title }}</h1>
      </header>

      <main>
        <slot />
      </main>
    </div>
  </div>
</template>
```

## Named Slots in Layouts

```vue
<!-- layouts/with-sidebar.vue -->
<template>
  <div class="layout">
    <header>
      <slot name="header">
        <DefaultHeader />
      </slot>
    </header>

    <div class="content-wrapper">
      <aside>
        <slot name="sidebar">
          <DefaultSidebar />
        </slot>
      </aside>

      <main>
        <slot />
      </main>
    </div>

    <footer>
      <slot name="footer">
        <DefaultFooter />
      </slot>
    </footer>
  </div>
</template>
```

Using named slots:

```vue
<!-- pages/products/index.vue -->
<script setup lang="ts">
definePageMeta({
  layout: 'with-sidebar',
});
</script>

<template>
  <template #header>
    <ProductsHeader />
  </template>

  <template #sidebar>
    <ProductFilters />
  </template>

  <!-- Default slot - main content -->
  <ProductList />

  <template #footer>
    <ProductsFooter />
  </template>
</template>
```

## Layout Transitions

```vue
<!-- layouts/default.vue -->
<template>
  <div>
    <AppHeader />

    <Transition name="page" mode="out-in">
      <slot />
    </Transition>

    <AppFooter />
  </div>
</template>

<style>
.page-enter-active,
.page-leave-active {
  transition: all 0.3s ease;
}

.page-enter-from,
.page-leave-to {
  opacity: 0;
  transform: translateY(10px);
}
</style>
```

## Nested Layouts

```vue
<!-- layouts/admin.vue -->
<template>
  <div class="admin-layout">
    <AdminSidebar />
    <div class="admin-content">
      <slot />
    </div>
  </div>
</template>
```

```vue
<!-- layouts/admin-settings.vue -->
<script setup lang="ts">
// Extend admin layout
definePageMeta({
  layout: 'admin',
});
</script>

<template>
  <div class="settings-layout">
    <SettingsTabs />
    <div class="settings-content">
      <slot />
    </div>
  </div>
</template>
```

## Conditional Layouts

```vue
<!-- layouts/default.vue -->
<script setup lang="ts">
const { user } = useAuth();
</script>

<template>
  <div>
    <!-- Show different header based on auth -->
    <AuthenticatedHeader v-if="user" />
    <GuestHeader v-else />

    <slot />

    <Footer />
  </div>
</template>
```

## Layout State

```vue
<!-- layouts/default.vue -->
<script setup lang="ts">
// Layout-level state
const sidebarOpen = ref(true);

// Provide to children
provide('sidebarOpen', sidebarOpen);
provide('toggleSidebar', () => {
  sidebarOpen.value = !sidebarOpen.value;
});
</script>

<template>
  <div class="layout" :class="{ 'sidebar-open': sidebarOpen }">
    <Sidebar v-if="sidebarOpen" />
    <main>
      <slot />
    </main>
  </div>
</template>
```

Using in page:

```vue
<script setup lang="ts">
const sidebarOpen = inject<Ref<boolean>>('sidebarOpen');
const toggleSidebar = inject<() => void>('toggleSidebar');
</script>

<template>
  <button @click="toggleSidebar">Toggle Sidebar</button>
</template>
```

## Error Layout

```vue
<!-- layouts/error.vue -->
<template>
  <div class="error-layout">
    <div class="error-content">
      <slot />
    </div>

    <NuxtLink to="/" class="home-link">
      Go Home
    </NuxtLink>
  </div>
</template>
```

```vue
<!-- error.vue -->
<script setup lang="ts">
definePageMeta({
  layout: 'error',
});
</script>

<template>
  <div>
    <h1>{{ error.statusCode }}</h1>
    <p>{{ error.message }}</p>
  </div>
</template>
```

## Best Practices

1. **Keep layouts simple** - Focus on structure, not business logic
2. **Use slots wisely** - Named slots for flexible customization
3. **Consistent structure** - Similar layouts across the app
4. **Responsive design** - Handle mobile/desktop in layouts
5. **Loading states** - Show loading in layout while page loads
6. **Transitions** - Add smooth page transitions
