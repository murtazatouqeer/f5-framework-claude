# MSW (Mock Service Worker)

## Overview

API mocking library that intercepts requests at the network level for realistic testing.

## Setup

```bash
npm install -D msw
```

```ts
// src/test/mocks/handlers.ts
import { http, HttpResponse } from 'msw';

interface User {
  id: string;
  name: string;
  email: string;
}

interface Product {
  id: string;
  name: string;
  price: number;
}

// Mock data
const users: User[] = [
  { id: '1', name: 'John Doe', email: 'john@example.com' },
  { id: '2', name: 'Jane Smith', email: 'jane@example.com' },
];

const products: Product[] = [
  { id: '1', name: 'Product 1', price: 29.99 },
  { id: '2', name: 'Product 2', price: 49.99 },
];

export const handlers = [
  // GET /api/users
  http.get('/api/users', () => {
    return HttpResponse.json(users);
  }),

  // GET /api/users/:id
  http.get('/api/users/:id', ({ params }) => {
    const user = users.find((u) => u.id === params.id);
    if (!user) {
      return new HttpResponse(null, { status: 404 });
    }
    return HttpResponse.json(user);
  }),

  // POST /api/users
  http.post('/api/users', async ({ request }) => {
    const body = await request.json() as Omit<User, 'id'>;
    const newUser: User = {
      id: String(users.length + 1),
      ...body,
    };
    return HttpResponse.json(newUser, { status: 201 });
  }),

  // PUT /api/users/:id
  http.put('/api/users/:id', async ({ params, request }) => {
    const body = await request.json() as Partial<User>;
    const user = users.find((u) => u.id === params.id);
    if (!user) {
      return new HttpResponse(null, { status: 404 });
    }
    const updatedUser = { ...user, ...body };
    return HttpResponse.json(updatedUser);
  }),

  // DELETE /api/users/:id
  http.delete('/api/users/:id', ({ params }) => {
    const index = users.findIndex((u) => u.id === params.id);
    if (index === -1) {
      return new HttpResponse(null, { status: 404 });
    }
    return new HttpResponse(null, { status: 204 });
  }),

  // GET /api/products
  http.get('/api/products', ({ request }) => {
    const url = new URL(request.url);
    const category = url.searchParams.get('category');
    const minPrice = url.searchParams.get('minPrice');

    let filtered = products;

    if (category) {
      filtered = filtered.filter((p) => p.category === category);
    }
    if (minPrice) {
      filtered = filtered.filter((p) => p.price >= Number(minPrice));
    }

    return HttpResponse.json(filtered);
  }),
];
```

## Server Setup

```ts
// src/test/mocks/server.ts
import { setupServer } from 'msw/node';
import { handlers } from './handlers';

export const server = setupServer(...handlers);
```

```ts
// src/test/setup.ts
import '@testing-library/jest-dom';
import { afterAll, afterEach, beforeAll } from 'vitest';
import { server } from './mocks/server';

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

## Testing with MSW

```tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { server } from '../test/mocks/server';
import { UserList } from './UserList';

describe('UserList', () => {
  it('displays users', async () => {
    render(<UserList />);

    expect(screen.getByText('Loading...')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('Jane Smith')).toBeInTheDocument();
    });
  });

  it('handles empty list', async () => {
    // Override handler for this test
    server.use(
      http.get('/api/users', () => {
        return HttpResponse.json([]);
      })
    );

    render(<UserList />);

    await waitFor(() => {
      expect(screen.getByText('No users found')).toBeInTheDocument();
    });
  });

  it('handles error state', async () => {
    server.use(
      http.get('/api/users', () => {
        return HttpResponse.json(
          { message: 'Internal server error' },
          { status: 500 }
        );
      })
    );

    render(<UserList />);

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument();
    });
  });

  it('handles network error', async () => {
    server.use(
      http.get('/api/users', () => {
        return HttpResponse.error();
      })
    );

    render(<UserList />);

    await waitFor(() => {
      expect(screen.getByText(/failed to fetch/i)).toBeInTheDocument();
    });
  });
});
```

## Testing Mutations

```tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { server } from '../test/mocks/server';
import { CreateUserForm } from './CreateUserForm';

describe('CreateUserForm', () => {
  it('creates a new user', async () => {
    const user = userEvent.setup();
    const onSuccess = vi.fn();

    render(<CreateUserForm onSuccess={onSuccess} />);

    await user.type(screen.getByLabelText('Name'), 'New User');
    await user.type(screen.getByLabelText('Email'), 'new@example.com');
    await user.click(screen.getByRole('button', { name: 'Create' }));

    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalled();
    });
  });

  it('shows error on failure', async () => {
    server.use(
      http.post('/api/users', () => {
        return HttpResponse.json(
          { message: 'Email already exists' },
          { status: 400 }
        );
      })
    );

    const user = userEvent.setup();

    render(<CreateUserForm onSuccess={vi.fn()} />);

    await user.type(screen.getByLabelText('Name'), 'New User');
    await user.type(screen.getByLabelText('Email'), 'existing@example.com');
    await user.click(screen.getByRole('button', { name: 'Create' }));

    await waitFor(() => {
      expect(screen.getByText('Email already exists')).toBeInTheDocument();
    });
  });
});
```

## Response Delays

```ts
import { http, HttpResponse, delay } from 'msw';

export const handlers = [
  http.get('/api/users', async () => {
    // Simulate network delay
    await delay(1000);
    return HttpResponse.json(users);
  }),

  http.get('/api/slow-endpoint', async () => {
    // Simulate slow API
    await delay(3000);
    return HttpResponse.json({ data: 'slow response' });
  }),
];
```

## Dynamic Responses

```ts
import { http, HttpResponse } from 'msw';

let requestCount = 0;

export const handlers = [
  // Fail first request, succeed on retry
  http.get('/api/flaky', () => {
    requestCount++;
    if (requestCount === 1) {
      return HttpResponse.json(
        { error: 'Temporary failure' },
        { status: 503 }
      );
    }
    return HttpResponse.json({ success: true });
  }),

  // Return different data based on auth
  http.get('/api/profile', ({ request }) => {
    const authHeader = request.headers.get('Authorization');

    if (!authHeader) {
      return new HttpResponse(null, { status: 401 });
    }

    const token = authHeader.replace('Bearer ', '');

    if (token === 'admin-token') {
      return HttpResponse.json({ role: 'admin', name: 'Admin User' });
    }

    return HttpResponse.json({ role: 'user', name: 'Regular User' });
  }),
];
```

## Browser Integration (Storybook/Development)

```ts
// src/mocks/browser.ts
import { setupWorker } from 'msw/browser';
import { handlers } from './handlers';

export const worker = setupWorker(...handlers);
```

```tsx
// main.tsx (development only)
async function enableMocking() {
  if (process.env.NODE_ENV !== 'development') {
    return;
  }

  const { worker } = await import('./mocks/browser');
  return worker.start();
}

enableMocking().then(() => {
  createRoot(document.getElementById('root')!).render(<App />);
});
```

## Best Practices

1. **Reset handlers** - afterEach to prevent test pollution
2. **Centralize handlers** - Single source of truth for mock data
3. **Test error states** - Override handlers per test for errors
4. **Simulate delays** - Test loading states realistically
5. **Use realistic data** - Match actual API response shapes
6. **Handle unhandled requests** - Set onUnhandledRequest: 'error'
