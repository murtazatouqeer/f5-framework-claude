---
name: vue-component-testing
description: Component testing patterns and best practices
applies_to: vue
---

# Component Testing

## Overview

Component testing verifies that Vue components render correctly
and respond to user interactions as expected.

## Testing Structure

### AAA Pattern (Arrange, Act, Assert)

```typescript
import { mount } from '@vue/test-utils';
import Counter from './Counter.vue';

describe('Counter', () => {
  it('increments count when button is clicked', async () => {
    // Arrange
    const wrapper = mount(Counter, {
      props: { initialCount: 0 },
    });

    // Act
    await wrapper.find('[data-testid="increment-btn"]').trigger('click');

    // Assert
    expect(wrapper.find('[data-testid="count"]').text()).toBe('1');
  });
});
```

## Testing Rendering

### Conditional Rendering

```vue
<!-- Alert.vue -->
<script setup lang="ts">
defineProps<{
  type: 'success' | 'error' | 'warning';
  message: string;
  dismissible?: boolean;
}>();

const emit = defineEmits<{
  (e: 'dismiss'): void;
}>();
</script>

<template>
  <div :class="['alert', `alert-${type}`]" role="alert">
    <span class="alert-message">{{ message }}</span>
    <button
      v-if="dismissible"
      class="alert-dismiss"
      @click="emit('dismiss')"
    >
      ×
    </button>
  </div>
</template>
```

```typescript
import { mount } from '@vue/test-utils';
import Alert from './Alert.vue';

describe('Alert', () => {
  it('renders message', () => {
    const wrapper = mount(Alert, {
      props: { type: 'success', message: 'Operation successful' },
    });

    expect(wrapper.find('.alert-message').text()).toBe('Operation successful');
  });

  it('applies correct type class', () => {
    const wrapper = mount(Alert, {
      props: { type: 'error', message: 'Error occurred' },
    });

    expect(wrapper.find('.alert').classes()).toContain('alert-error');
  });

  it('shows dismiss button when dismissible', () => {
    const wrapper = mount(Alert, {
      props: { type: 'success', message: 'Test', dismissible: true },
    });

    expect(wrapper.find('.alert-dismiss').exists()).toBe(true);
  });

  it('hides dismiss button when not dismissible', () => {
    const wrapper = mount(Alert, {
      props: { type: 'success', message: 'Test', dismissible: false },
    });

    expect(wrapper.find('.alert-dismiss').exists()).toBe(false);
  });

  it('emits dismiss when dismiss button clicked', async () => {
    const wrapper = mount(Alert, {
      props: { type: 'success', message: 'Test', dismissible: true },
    });

    await wrapper.find('.alert-dismiss').trigger('click');

    expect(wrapper.emitted('dismiss')).toHaveLength(1);
  });
});
```

### List Rendering

```vue
<!-- TodoList.vue -->
<script setup lang="ts">
interface Todo {
  id: number;
  text: string;
  completed: boolean;
}

defineProps<{
  todos: Todo[];
}>();

const emit = defineEmits<{
  (e: 'toggle', id: number): void;
  (e: 'delete', id: number): void;
}>();
</script>

<template>
  <ul class="todo-list">
    <li
      v-for="todo in todos"
      :key="todo.id"
      :class="{ completed: todo.completed }"
      data-testid="todo-item"
    >
      <input
        type="checkbox"
        :checked="todo.completed"
        @change="emit('toggle', todo.id)"
        data-testid="todo-checkbox"
      />
      <span data-testid="todo-text">{{ todo.text }}</span>
      <button
        @click="emit('delete', todo.id)"
        data-testid="todo-delete"
      >
        Delete
      </button>
    </li>
  </ul>
  <p v-if="todos.length === 0" data-testid="empty-message">
    No todos yet
  </p>
</template>
```

```typescript
import { mount } from '@vue/test-utils';
import TodoList from './TodoList.vue';

describe('TodoList', () => {
  const mockTodos = [
    { id: 1, text: 'Learn Vue', completed: false },
    { id: 2, text: 'Write tests', completed: true },
    { id: 3, text: 'Build app', completed: false },
  ];

  it('renders all todos', () => {
    const wrapper = mount(TodoList, {
      props: { todos: mockTodos },
    });

    const items = wrapper.findAll('[data-testid="todo-item"]');
    expect(items).toHaveLength(3);
  });

  it('displays todo text correctly', () => {
    const wrapper = mount(TodoList, {
      props: { todos: mockTodos },
    });

    const texts = wrapper.findAll('[data-testid="todo-text"]');
    expect(texts[0].text()).toBe('Learn Vue');
    expect(texts[1].text()).toBe('Write tests');
  });

  it('marks completed todos with class', () => {
    const wrapper = mount(TodoList, {
      props: { todos: mockTodos },
    });

    const items = wrapper.findAll('[data-testid="todo-item"]');
    expect(items[0].classes()).not.toContain('completed');
    expect(items[1].classes()).toContain('completed');
  });

  it('shows empty message when no todos', () => {
    const wrapper = mount(TodoList, {
      props: { todos: [] },
    });

    expect(wrapper.find('[data-testid="empty-message"]').exists()).toBe(true);
    expect(wrapper.findAll('[data-testid="todo-item"]')).toHaveLength(0);
  });

  it('emits toggle with correct id', async () => {
    const wrapper = mount(TodoList, {
      props: { todos: mockTodos },
    });

    const checkboxes = wrapper.findAll('[data-testid="todo-checkbox"]');
    await checkboxes[0].setValue(true);

    expect(wrapper.emitted('toggle')).toBeTruthy();
    expect(wrapper.emitted('toggle')![0]).toEqual([1]);
  });

  it('emits delete with correct id', async () => {
    const wrapper = mount(TodoList, {
      props: { todos: mockTodos },
    });

    const deleteButtons = wrapper.findAll('[data-testid="todo-delete"]');
    await deleteButtons[2].trigger('click');

    expect(wrapper.emitted('delete')).toBeTruthy();
    expect(wrapper.emitted('delete')![0]).toEqual([3]);
  });
});
```

## Testing Forms

### Form Component

```vue
<!-- LoginForm.vue -->
<script setup lang="ts">
import { ref } from 'vue';

const emit = defineEmits<{
  (e: 'submit', data: { email: string; password: string }): void;
}>();

const email = ref('');
const password = ref('');
const errors = ref<Record<string, string>>({});

function validate(): boolean {
  errors.value = {};

  if (!email.value) {
    errors.value.email = 'Email is required';
  } else if (!/\S+@\S+\.\S+/.test(email.value)) {
    errors.value.email = 'Invalid email format';
  }

  if (!password.value) {
    errors.value.password = 'Password is required';
  } else if (password.value.length < 8) {
    errors.value.password = 'Password must be at least 8 characters';
  }

  return Object.keys(errors.value).length === 0;
}

function handleSubmit() {
  if (validate()) {
    emit('submit', {
      email: email.value,
      password: password.value,
    });
  }
}
</script>

<template>
  <form @submit.prevent="handleSubmit" data-testid="login-form">
    <div class="form-field">
      <label for="email">Email</label>
      <input
        id="email"
        v-model="email"
        type="email"
        data-testid="email-input"
      />
      <span v-if="errors.email" class="error" data-testid="email-error">
        {{ errors.email }}
      </span>
    </div>

    <div class="form-field">
      <label for="password">Password</label>
      <input
        id="password"
        v-model="password"
        type="password"
        data-testid="password-input"
      />
      <span v-if="errors.password" class="error" data-testid="password-error">
        {{ errors.password }}
      </span>
    </div>

    <button type="submit" data-testid="submit-btn">
      Login
    </button>
  </form>
</template>
```

```typescript
import { mount } from '@vue/test-utils';
import LoginForm from './LoginForm.vue';

describe('LoginForm', () => {
  it('renders form fields', () => {
    const wrapper = mount(LoginForm);

    expect(wrapper.find('[data-testid="email-input"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="password-input"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="submit-btn"]').exists()).toBe(true);
  });

  it('shows error when email is empty', async () => {
    const wrapper = mount(LoginForm);

    await wrapper.find('[data-testid="submit-btn"]').trigger('click');

    expect(wrapper.find('[data-testid="email-error"]').text())
      .toBe('Email is required');
  });

  it('shows error when email format is invalid', async () => {
    const wrapper = mount(LoginForm);

    await wrapper.find('[data-testid="email-input"]').setValue('invalid');
    await wrapper.find('[data-testid="submit-btn"]').trigger('click');

    expect(wrapper.find('[data-testid="email-error"]').text())
      .toBe('Invalid email format');
  });

  it('shows error when password is too short', async () => {
    const wrapper = mount(LoginForm);

    await wrapper.find('[data-testid="email-input"]').setValue('test@test.com');
    await wrapper.find('[data-testid="password-input"]').setValue('short');
    await wrapper.find('[data-testid="submit-btn"]').trigger('click');

    expect(wrapper.find('[data-testid="password-error"]').text())
      .toBe('Password must be at least 8 characters');
  });

  it('emits submit with form data when valid', async () => {
    const wrapper = mount(LoginForm);

    await wrapper.find('[data-testid="email-input"]').setValue('test@test.com');
    await wrapper.find('[data-testid="password-input"]').setValue('password123');
    await wrapper.find('[data-testid="submit-btn"]').trigger('click');

    expect(wrapper.emitted('submit')).toBeTruthy();
    expect(wrapper.emitted('submit')![0]).toEqual([{
      email: 'test@test.com',
      password: 'password123',
    }]);
  });

  it('does not emit submit when invalid', async () => {
    const wrapper = mount(LoginForm);

    await wrapper.find('[data-testid="submit-btn"]').trigger('click');

    expect(wrapper.emitted('submit')).toBeFalsy();
  });
});
```

## Testing Async Components

```vue
<!-- UserProfile.vue -->
<script setup lang="ts">
import { ref, onMounted } from 'vue';

interface User {
  id: number;
  name: string;
  email: string;
}

const props = defineProps<{
  userId: number;
}>();

const user = ref<User | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);

async function fetchUser() {
  loading.value = true;
  error.value = null;

  try {
    const response = await fetch(`/api/users/${props.userId}`);
    if (!response.ok) throw new Error('User not found');
    user.value = await response.json();
  } catch (e) {
    error.value = (e as Error).message;
  } finally {
    loading.value = false;
  }
}

onMounted(fetchUser);
</script>

<template>
  <div class="user-profile">
    <div v-if="loading" data-testid="loading">Loading...</div>
    <div v-else-if="error" data-testid="error">{{ error }}</div>
    <div v-else-if="user" data-testid="user-info">
      <h2 data-testid="user-name">{{ user.name }}</h2>
      <p data-testid="user-email">{{ user.email }}</p>
    </div>
  </div>
</template>
```

```typescript
import { mount, flushPromises } from '@vue/test-utils';
import { vi } from 'vitest';
import UserProfile from './UserProfile.vue';

describe('UserProfile', () => {
  const mockUser = {
    id: 1,
    name: 'John Doe',
    email: 'john@example.com',
  };

  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('shows loading state initially', () => {
    vi.mocked(fetch).mockImplementation(() => new Promise(() => {}));

    const wrapper = mount(UserProfile, {
      props: { userId: 1 },
    });

    expect(wrapper.find('[data-testid="loading"]').exists()).toBe(true);
  });

  it('displays user data after fetch', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockUser),
    } as Response);

    const wrapper = mount(UserProfile, {
      props: { userId: 1 },
    });

    await flushPromises();

    expect(wrapper.find('[data-testid="loading"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="user-name"]').text()).toBe('John Doe');
    expect(wrapper.find('[data-testid="user-email"]').text()).toBe('john@example.com');
  });

  it('shows error message on fetch failure', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: false,
    } as Response);

    const wrapper = mount(UserProfile, {
      props: { userId: 999 },
    });

    await flushPromises();

    expect(wrapper.find('[data-testid="error"]').text()).toBe('User not found');
  });
});
```

## Test Organization

### Factory Functions

```typescript
// tests/factories.ts
import type { User, Todo } from '@/types';

export function createUser(overrides: Partial<User> = {}): User {
  return {
    id: 1,
    name: 'Test User',
    email: 'test@example.com',
    ...overrides,
  };
}

export function createTodo(overrides: Partial<Todo> = {}): Todo {
  return {
    id: 1,
    text: 'Test Todo',
    completed: false,
    ...overrides,
  };
}
```

### Mount Helper

```typescript
// tests/helpers.ts
import { mount, MountingOptions } from '@vue/test-utils';
import { createPinia } from 'pinia';
import { Component } from 'vue';

export function mountWithPlugins<T extends Component>(
  component: T,
  options: MountingOptions<T> = {}
) {
  return mount(component, {
    global: {
      plugins: [createPinia()],
      ...options.global,
    },
    ...options,
  });
}
```

## Best Practices

1. **Test user interactions** - Verify component responds correctly
2. **Use data-testid** - Stable selectors for testing
3. **Test edge cases** - Empty states, errors, loading
4. **Mock external dependencies** - API calls, timers
5. **Keep tests focused** - One concept per test
6. **Arrange-Act-Assert** - Clear test structure
