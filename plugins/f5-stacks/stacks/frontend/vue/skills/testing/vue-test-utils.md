---
name: vue-test-utils
description: Vue Test Utils for component testing
applies_to: vue
---

# Vue Test Utils

## Overview

Vue Test Utils is the official testing utility library for Vue.js.
It provides methods to mount and interact with Vue components.

## Basic Mounting

### Mount vs ShallowMount

```typescript
import { mount, shallowMount } from '@vue/test-utils';
import MyComponent from './MyComponent.vue';

// mount: Renders full component tree including child components
const fullWrapper = mount(MyComponent);

// shallowMount: Stubs child components
const shallowWrapper = shallowMount(MyComponent);
```

### With Props

```typescript
import { mount } from '@vue/test-utils';
import Button from './Button.vue';

const wrapper = mount(Button, {
  props: {
    label: 'Click me',
    variant: 'primary',
    disabled: false,
  },
});

expect(wrapper.text()).toBe('Click me');
```

### With Slots

```typescript
import { mount } from '@vue/test-utils';
import Card from './Card.vue';

const wrapper = mount(Card, {
  slots: {
    default: '<p>Card content</p>',
    header: '<h1>Card Title</h1>',
    footer: '<button>Action</button>',
  },
});

expect(wrapper.find('h1').text()).toBe('Card Title');
```

## Finding Elements

### Query Methods

```typescript
import { mount } from '@vue/test-utils';

const wrapper = mount(MyComponent);

// Find by CSS selector
const button = wrapper.find('button');
const input = wrapper.find('input[type="email"]');
const div = wrapper.find('.my-class');
const element = wrapper.find('#my-id');

// Find all matching elements
const items = wrapper.findAll('li');

// Find by component
import ChildComponent from './ChildComponent.vue';
const child = wrapper.findComponent(ChildComponent);
const children = wrapper.findAllComponents(ChildComponent);

// Check existence
expect(wrapper.find('.error').exists()).toBe(false);
```

### Data Test ID Pattern

```vue
<!-- Component -->
<template>
  <div>
    <input data-testid="email-input" type="email" />
    <button data-testid="submit-button">Submit</button>
    <span data-testid="error-message" v-if="error">{{ error }}</span>
  </div>
</template>
```

```typescript
// Test
const wrapper = mount(MyComponent);

const emailInput = wrapper.find('[data-testid="email-input"]');
const submitButton = wrapper.find('[data-testid="submit-button"]');

expect(emailInput.exists()).toBe(true);
expect(submitButton.text()).toBe('Submit');
```

## Interacting with Components

### Triggering Events

```typescript
import { mount } from '@vue/test-utils';

const wrapper = mount(MyComponent);

// Click
await wrapper.find('button').trigger('click');

// Double click
await wrapper.find('button').trigger('dblclick');

// Keyboard events
await wrapper.find('input').trigger('keydown', { key: 'Enter' });
await wrapper.find('input').trigger('keyup.enter');

// Focus/Blur
await wrapper.find('input').trigger('focus');
await wrapper.find('input').trigger('blur');

// Custom events
await wrapper.find('.draggable').trigger('dragstart');
```

### Setting Values

```typescript
import { mount } from '@vue/test-utils';

const wrapper = mount(MyForm);

// Text input
await wrapper.find('input[type="text"]').setValue('John Doe');

// Checkbox
await wrapper.find('input[type="checkbox"]').setValue(true);

// Select
await wrapper.find('select').setValue('option2');

// Multiple values for multi-select
await wrapper.find('select').setValue(['opt1', 'opt2']);

// Radio
await wrapper.find('input[value="yes"]').setValue();
```

## Testing Emitted Events

```vue
<!-- ConfirmDialog.vue -->
<script setup lang="ts">
const emit = defineEmits<{
  (e: 'confirm'): void;
  (e: 'cancel'): void;
  (e: 'update', value: string): void;
}>();
</script>
```

```typescript
import { mount } from '@vue/test-utils';
import ConfirmDialog from './ConfirmDialog.vue';

describe('ConfirmDialog', () => {
  it('emits confirm on confirm button click', async () => {
    const wrapper = mount(ConfirmDialog);

    await wrapper.find('[data-testid="confirm-btn"]').trigger('click');

    expect(wrapper.emitted()).toHaveProperty('confirm');
    expect(wrapper.emitted('confirm')).toHaveLength(1);
  });

  it('emits update with payload', async () => {
    const wrapper = mount(ConfirmDialog);

    await wrapper.find('input').setValue('new value');
    await wrapper.find('form').trigger('submit');

    expect(wrapper.emitted('update')).toBeTruthy();
    expect(wrapper.emitted('update')![0]).toEqual(['new value']);
  });

  it('emits multiple events in order', async () => {
    const wrapper = mount(ConfirmDialog);

    await wrapper.find('[data-testid="confirm-btn"]').trigger('click');
    await wrapper.find('[data-testid="cancel-btn"]').trigger('click');

    const emitted = wrapper.emitted();
    expect(Object.keys(emitted)).toEqual(['confirm', 'cancel']);
  });
});
```

## Testing v-model

```vue
<!-- TextInput.vue -->
<script setup lang="ts">
const model = defineModel<string>();
</script>

<template>
  <input :value="model" @input="model = ($event.target as HTMLInputElement).value" />
</template>
```

```typescript
import { mount } from '@vue/test-utils';
import TextInput from './TextInput.vue';

describe('TextInput', () => {
  it('updates v-model on input', async () => {
    const wrapper = mount(TextInput, {
      props: {
        modelValue: '',
        'onUpdate:modelValue': (e: string) => wrapper.setProps({ modelValue: e }),
      },
    });

    await wrapper.find('input').setValue('Hello');

    expect(wrapper.emitted('update:modelValue')).toBeTruthy();
    expect(wrapper.emitted('update:modelValue')![0]).toEqual(['Hello']);
  });
});
```

## Providing Dependencies

### Provide/Inject

```typescript
import { mount } from '@vue/test-utils';
import ChildComponent from './ChildComponent.vue';

const wrapper = mount(ChildComponent, {
  global: {
    provide: {
      theme: 'dark',
      user: { id: 1, name: 'John' },
    },
  },
});
```

### Plugins

```typescript
import { mount } from '@vue/test-utils';
import { createPinia } from 'pinia';
import { createI18n } from 'vue-i18n';
import { createRouter, createWebHistory } from 'vue-router';

const pinia = createPinia();
const i18n = createI18n({ /* config */ });
const router = createRouter({
  history: createWebHistory(),
  routes: [],
});

const wrapper = mount(MyComponent, {
  global: {
    plugins: [pinia, i18n, router],
  },
});
```

### Stubs and Mocks

```typescript
import { mount } from '@vue/test-utils';

const wrapper = mount(MyComponent, {
  global: {
    // Stub child components
    stubs: {
      ChildComponent: true, // Renders as <child-component-stub>
      AnotherChild: {
        template: '<div class="mock-child"><slot /></div>',
      },
      // Stub teleport
      teleport: true,
    },
    // Mock global properties
    mocks: {
      $t: (key: string) => key, // Mock i18n
      $route: { params: { id: '1' } },
      $router: { push: vi.fn() },
    },
  },
});
```

## Testing Async Behavior

### Waiting for Updates

```typescript
import { mount, flushPromises } from '@vue/test-utils';

describe('AsyncComponent', () => {
  it('loads data on mount', async () => {
    const wrapper = mount(AsyncComponent);

    // Wait for all promises to resolve
    await flushPromises();

    expect(wrapper.find('.data-loaded').exists()).toBe(true);
  });

  it('shows loading state', async () => {
    const wrapper = mount(AsyncComponent);

    // Initial state - loading
    expect(wrapper.find('.loading').exists()).toBe(true);

    await flushPromises();

    // After load
    expect(wrapper.find('.loading').exists()).toBe(false);
  });
});
```

### Testing Watchers

```typescript
import { mount } from '@vue/test-utils';
import { nextTick } from 'vue';

describe('Component with watchers', () => {
  it('reacts to prop changes', async () => {
    const wrapper = mount(MyComponent, {
      props: { count: 0 },
    });

    await wrapper.setProps({ count: 5 });
    await nextTick();

    expect(wrapper.find('.doubled').text()).toBe('10');
  });
});
```

## Testing with Pinia

```typescript
import { mount } from '@vue/test-utils';
import { setActivePinia, createPinia } from 'pinia';
import { useUserStore } from '@/stores/useUserStore';
import UserProfile from './UserProfile.vue';

describe('UserProfile', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it('displays user from store', () => {
    const store = useUserStore();
    store.currentUser = { id: 1, name: 'John', email: 'john@test.com' };

    const wrapper = mount(UserProfile);

    expect(wrapper.find('.user-name').text()).toBe('John');
    expect(wrapper.find('.user-email').text()).toBe('john@test.com');
  });

  it('calls store action on button click', async () => {
    const store = useUserStore();
    const logoutSpy = vi.spyOn(store, 'logout');

    const wrapper = mount(UserProfile);
    await wrapper.find('[data-testid="logout-btn"]').trigger('click');

    expect(logoutSpy).toHaveBeenCalled();
  });
});
```

## Testing with Vue Router

```typescript
import { mount, flushPromises } from '@vue/test-utils';
import { createRouter, createWebHistory } from 'vue-router';

const routes = [
  { path: '/', component: { template: '<div>Home</div>' } },
  { path: '/about', component: { template: '<div>About</div>' } },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

describe('Navigation', () => {
  it('navigates to about page', async () => {
    const wrapper = mount(App, {
      global: {
        plugins: [router],
      },
    });

    await router.push('/about');
    await flushPromises();

    expect(wrapper.html()).toContain('About');
  });
});
```

## Best Practices

1. **Use data-testid** - Decouple tests from implementation
2. **Test behavior, not implementation** - Focus on what users see
3. **Await async operations** - Use flushPromises() or nextTick()
4. **Isolate tests** - Reset state between tests
5. **Mock external dependencies** - Don't rely on real APIs
6. **Use shallow mounting** - When testing parent component in isolation
