---
name: vue-layout
description: Vue layout component template
applies_to: vue
variables:
  - name: layoutName
    description: Layout component name
---

# Vue Layout Template

## Basic Layout

```vue
<script setup lang="ts">
// ============================================================
// layouts/{{layoutName}}Layout.vue
// ============================================================

import { ref } from 'vue';

// ------------------------------------------------------------
// State
// ------------------------------------------------------------
const isSidebarOpen = ref(true);

// ------------------------------------------------------------
// Methods
// ------------------------------------------------------------
function toggleSidebar() {
  isSidebarOpen.value = !isSidebarOpen.value;
}
</script>

<template>
  <div class="layout layout--{{layoutName | kebab}}">
    <!-- Header -->
    <header class="layout__header">
      <slot name="header">
        <div class="header__content">
          <button class="header__toggle" @click="toggleSidebar">
            ☰
          </button>
          <div class="header__logo">
            <slot name="logo">Logo</slot>
          </div>
          <nav class="header__nav">
            <slot name="nav" />
          </nav>
          <div class="header__actions">
            <slot name="header-actions" />
          </div>
        </div>
      </slot>
    </header>

    <div class="layout__body">
      <!-- Sidebar -->
      <aside
        v-if="$slots.sidebar"
        class="layout__sidebar"
        :class="{ 'is-open': isSidebarOpen }"
      >
        <slot name="sidebar" />
      </aside>

      <!-- Main Content -->
      <main class="layout__main">
        <slot />
      </main>
    </div>

    <!-- Footer -->
    <footer v-if="$slots.footer" class="layout__footer">
      <slot name="footer" />
    </footer>
  </div>
</template>

<style scoped>
.layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.layout__header {
  position: sticky;
  top: 0;
  z-index: 100;
  background-color: white;
  border-bottom: 1px solid #e5e7eb;
}

.header__content {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0 1rem;
  height: 64px;
  max-width: 1440px;
  margin: 0 auto;
}

.header__toggle {
  display: none;
  padding: 0.5rem;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.25rem;
}

.header__logo {
  font-weight: 600;
  font-size: 1.25rem;
}

.header__nav {
  flex: 1;
  display: flex;
  gap: 1rem;
}

.header__actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.layout__body {
  display: flex;
  flex: 1;
}

.layout__sidebar {
  width: 256px;
  flex-shrink: 0;
  background-color: #f9fafb;
  border-right: 1px solid #e5e7eb;
  overflow-y: auto;
  transition: transform 0.3s ease;
}

.layout__main {
  flex: 1;
  padding: 1.5rem;
  overflow-x: hidden;
}

.layout__footer {
  background-color: #f9fafb;
  border-top: 1px solid #e5e7eb;
  padding: 1rem;
  text-align: center;
}

/* Responsive */
@media (max-width: 768px) {
  .header__toggle {
    display: block;
  }

  .layout__sidebar {
    position: fixed;
    top: 64px;
    left: 0;
    bottom: 0;
    z-index: 50;
    transform: translateX(-100%);
  }

  .layout__sidebar.is-open {
    transform: translateX(0);
  }
}
</style>
```

## Dashboard Layout

```vue
<script setup lang="ts">
// ============================================================
// layouts/DashboardLayout.vue
// ============================================================

import { ref, computed } from 'vue';
import { useRoute } from 'vue-router';

// ------------------------------------------------------------
// Types
// ------------------------------------------------------------
interface NavItem {
  name: string;
  path: string;
  icon: string;
  children?: NavItem[];
}

// ------------------------------------------------------------
// Props
// ------------------------------------------------------------
interface Props {
  navItems?: NavItem[];
}

const props = withDefaults(defineProps<Props>(), {
  navItems: () => [],
});

// ------------------------------------------------------------
// State
// ------------------------------------------------------------
const route = useRoute();
const isSidebarCollapsed = ref(false);
const isMobileSidebarOpen = ref(false);

// ------------------------------------------------------------
// Computed
// ------------------------------------------------------------
const currentPath = computed(() => route.path);

// ------------------------------------------------------------
// Methods
// ------------------------------------------------------------
function toggleSidebar() {
  isSidebarCollapsed.value = !isSidebarCollapsed.value;
}

function toggleMobileSidebar() {
  isMobileSidebarOpen.value = !isMobileSidebarOpen.value;
}

function isActive(path: string): boolean {
  return currentPath.value === path || currentPath.value.startsWith(path + '/');
}
</script>

<template>
  <div
    class="dashboard-layout"
    :class="{ 'sidebar-collapsed': isSidebarCollapsed }"
  >
    <!-- Sidebar -->
    <aside
      class="sidebar"
      :class="{ 'is-mobile-open': isMobileSidebarOpen }"
    >
      <div class="sidebar__header">
        <slot name="logo">
          <span class="logo">App</span>
        </slot>
        <button class="sidebar__collapse" @click="toggleSidebar">
          {{ isSidebarCollapsed ? '→' : '←' }}
        </button>
      </div>

      <nav class="sidebar__nav">
        <ul class="nav-list">
          <li
            v-for="item in navItems"
            :key="item.path"
            class="nav-item"
          >
            <RouterLink
              :to="item.path"
              class="nav-link"
              :class="{ 'is-active': isActive(item.path) }"
            >
              <span class="nav-link__icon">{{ item.icon }}</span>
              <span class="nav-link__text">{{ item.name }}</span>
            </RouterLink>
          </li>
        </ul>
      </nav>

      <div class="sidebar__footer">
        <slot name="sidebar-footer" />
      </div>
    </aside>

    <!-- Main Area -->
    <div class="main-area">
      <!-- Header -->
      <header class="main-header">
        <button class="mobile-menu-btn" @click="toggleMobileSidebar">
          ☰
        </button>

        <div class="header-content">
          <slot name="header" />
        </div>

        <div class="header-actions">
          <slot name="header-actions" />
        </div>
      </header>

      <!-- Page Content -->
      <main class="main-content">
        <slot />
      </main>
    </div>

    <!-- Mobile Overlay -->
    <div
      v-if="isMobileSidebarOpen"
      class="mobile-overlay"
      @click="toggleMobileSidebar"
    />
  </div>
</template>

<style scoped>
.dashboard-layout {
  display: flex;
  min-height: 100vh;
}

/* Sidebar */
.sidebar {
  width: 256px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background-color: #1f2937;
  color: white;
  transition: width 0.3s ease;
}

.sidebar-collapsed .sidebar {
  width: 64px;
}

.sidebar__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  border-bottom: 1px solid #374151;
}

.logo {
  font-weight: 600;
  font-size: 1.25rem;
}

.sidebar-collapsed .logo {
  display: none;
}

.sidebar__collapse {
  padding: 0.25rem;
  background: none;
  border: none;
  color: #9ca3af;
  cursor: pointer;
}

.sidebar__nav {
  flex: 1;
  padding: 1rem 0;
  overflow-y: auto;
}

.nav-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  color: #9ca3af;
  text-decoration: none;
  transition: background-color 0.2s, color 0.2s;
}

.nav-link:hover {
  background-color: #374151;
  color: white;
}

.nav-link.is-active {
  background-color: #3b82f6;
  color: white;
}

.nav-link__icon {
  width: 24px;
  text-align: center;
}

.sidebar-collapsed .nav-link__text {
  display: none;
}

.sidebar__footer {
  padding: 1rem;
  border-top: 1px solid #374151;
}

/* Main Area */
.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.main-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0 1.5rem;
  height: 64px;
  background-color: white;
  border-bottom: 1px solid #e5e7eb;
}

.mobile-menu-btn {
  display: none;
  padding: 0.5rem;
  background: none;
  border: none;
  font-size: 1.25rem;
  cursor: pointer;
}

.header-content {
  flex: 1;
}

.main-content {
  flex: 1;
  padding: 1.5rem;
  background-color: #f3f4f6;
  overflow-y: auto;
}

/* Mobile */
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    z-index: 200;
    transform: translateX(-100%);
  }

  .sidebar.is-mobile-open {
    transform: translateX(0);
  }

  .sidebar-collapsed .sidebar {
    width: 256px;
  }

  .mobile-menu-btn {
    display: block;
  }

  .mobile-overlay {
    position: fixed;
    inset: 0;
    z-index: 100;
    background-color: rgba(0, 0, 0, 0.5);
  }
}
</style>
```

## Usage

```vue
<!-- App.vue or router view -->
<script setup lang="ts">
import DashboardLayout from '@/layouts/DashboardLayout.vue';

const navItems = [
  { name: 'Dashboard', path: '/dashboard', icon: '📊' },
  { name: 'Users', path: '/users', icon: '👥' },
  { name: 'Settings', path: '/settings', icon: '⚙️' },
];
</script>

<template>
  <DashboardLayout :nav-items="navItems">
    <template #logo>
      <img src="/logo.svg" alt="Logo" />
    </template>

    <template #header>
      <h1>Page Title</h1>
    </template>

    <template #header-actions>
      <button>Profile</button>
    </template>

    <!-- Page content via router-view -->
    <RouterView />

    <template #sidebar-footer>
      <button>Logout</button>
    </template>
  </DashboardLayout>
</template>
```
