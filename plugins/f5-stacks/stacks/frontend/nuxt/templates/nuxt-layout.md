---
name: nuxt-layout
description: Template for Nuxt 3 layouts
applies_to: nuxt
---

# Nuxt Layout Template

## Default Layout

```vue
<!-- layouts/default.vue -->
<script setup lang="ts">
const route = useRoute();
</script>

<template>
  <div class="layout-default">
    <AppHeader />

    <main class="layout-default__main">
      <slot />
    </main>

    <AppFooter />
  </div>
</template>

<style scoped>
.layout-default {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.layout-default__main {
  flex: 1;
  padding: 1rem;
}
</style>
```

## Admin Layout

```vue
<!-- layouts/admin.vue -->
<script setup lang="ts">
definePageMeta({
  middleware: 'auth',
});

const sidebarOpen = ref(true);

const toggleSidebar = () => {
  sidebarOpen.value = !sidebarOpen.value;
};
</script>

<template>
  <div class="layout-admin">
    <AdminHeader @toggle-sidebar="toggleSidebar" />

    <div class="layout-admin__container">
      <AdminSidebar :open="sidebarOpen" />

      <main class="layout-admin__main">
        <slot />
      </main>
    </div>
  </div>
</template>

<style scoped>
.layout-admin {
  min-height: 100vh;
}

.layout-admin__container {
  display: flex;
}

.layout-admin__main {
  flex: 1;
  padding: 1.5rem;
  background: var(--bg-secondary);
}
</style>
```

## Auth Layout

```vue
<!-- layouts/auth.vue -->
<script setup lang="ts">
// Redirect if already authenticated
const { user } = useAuth();

watch(user, (newUser) => {
  if (newUser) {
    navigateTo('/dashboard');
  }
});
</script>

<template>
  <div class="layout-auth">
    <div class="layout-auth__container">
      <div class="layout-auth__brand">
        <NuxtLink to="/">
          <AppLogo />
        </NuxtLink>
      </div>

      <div class="layout-auth__content">
        <slot />
      </div>

      <div class="layout-auth__footer">
        <p>&copy; {{ new Date().getFullYear() }} {{APP_NAME}}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.layout-auth {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-gradient);
}

.layout-auth__container {
  width: 100%;
  max-width: 400px;
  padding: 2rem;
}

.layout-auth__brand {
  text-align: center;
  margin-bottom: 2rem;
}

.layout-auth__content {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  box-shadow: var(--shadow-lg);
}
</style>
```

## Blank Layout

```vue
<!-- layouts/blank.vue -->
<template>
  <div class="layout-blank">
    <slot />
  </div>
</template>

<style scoped>
.layout-blank {
  min-height: 100vh;
}
</style>
```

## Layout with Transitions

```vue
<!-- layouts/default.vue -->
<script setup lang="ts">
const route = useRoute();
</script>

<template>
  <div class="layout-default">
    <AppHeader />

    <main class="layout-default__main">
      <slot />
    </main>

    <AppFooter />
  </div>
</template>

<style>
/* Page transition styles */
.page-enter-active,
.page-leave-active {
  transition: all 0.3s;
}

.page-enter-from,
.page-leave-to {
  opacity: 0;
  filter: blur(1rem);
}

/* Layout transition styles */
.layout-enter-active,
.layout-leave-active {
  transition: all 0.4s;
}

.layout-enter-from,
.layout-leave-to {
  opacity: 0;
}
</style>
```

## Dynamic Layout Selection

```vue
<!-- pages/[...slug].vue -->
<script setup lang="ts">
const route = useRoute();

// Dynamic layout based on route
const layout = computed(() => {
  if (route.path.startsWith('/admin')) return 'admin';
  if (route.path.startsWith('/auth')) return 'auth';
  return 'default';
});

definePageMeta({
  layout: false, // Disable automatic layout
});
</script>

<template>
  <NuxtLayout :name="layout">
    <NuxtPage />
  </NuxtLayout>
</template>
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{APP_NAME}}` | Application name | `My App` |
