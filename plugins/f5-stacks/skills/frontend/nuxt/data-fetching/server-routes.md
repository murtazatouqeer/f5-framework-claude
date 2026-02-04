---
name: nuxt-server-routes
description: Server API routes in Nuxt 3 with Nitro
applies_to: nuxt
---

# Nuxt Server Routes

## Overview

Nuxt 3 uses Nitro for server-side logic. Define API routes in `server/api/` for full-stack applications.

## File Structure

```
server/
├── api/                       # /api/* routes
│   ├── products/
│   │   ├── index.get.ts       # GET /api/products
│   │   ├── index.post.ts      # POST /api/products
│   │   ├── [id].get.ts        # GET /api/products/:id
│   │   ├── [id].put.ts        # PUT /api/products/:id
│   │   └── [id].delete.ts     # DELETE /api/products/:id
│   └── auth/
│       ├── login.post.ts
│       └── logout.post.ts
├── middleware/                # Server middleware
├── plugins/                   # Server plugins
├── routes/                    # Non-API routes
└── utils/                     # Server utilities
```

## Basic API Route

```typescript
// server/api/hello.ts
export default defineEventHandler((event) => {
  return { message: 'Hello World' };
});
```

## HTTP Methods

### Method-Specific Files
```typescript
// server/api/products/index.get.ts
export default defineEventHandler(async () => {
  return await prisma.product.findMany();
});

// server/api/products/index.post.ts
export default defineEventHandler(async (event) => {
  const body = await readBody(event);
  return await prisma.product.create({ data: body });
});
```

### Single File with Method Check
```typescript
// server/api/products.ts
export default defineEventHandler(async (event) => {
  const method = getMethod(event);

  if (method === 'GET') {
    return await prisma.product.findMany();
  }

  if (method === 'POST') {
    const body = await readBody(event);
    return await prisma.product.create({ data: body });
  }
});
```

## Route Parameters

```typescript
// server/api/products/[id].get.ts
export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id');

  const product = await prisma.product.findUnique({
    where: { id },
  });

  if (!product) {
    throw createError({
      statusCode: 404,
      message: 'Product not found',
    });
  }

  return product;
});

// Catch-all: server/api/[...slug].ts
export default defineEventHandler((event) => {
  const slug = getRouterParam(event, 'slug'); // Array of segments
  return { slug };
});
```

## Query Parameters

```typescript
// server/api/products/index.get.ts
export default defineEventHandler(async (event) => {
  const query = getQuery(event);
  const { page = 1, limit = 20, search, status } = query;

  const where = {
    ...(search && {
      name: { contains: String(search), mode: 'insensitive' },
    }),
    ...(status && { status: String(status) }),
  };

  const [items, total] = await Promise.all([
    prisma.product.findMany({
      where,
      skip: (Number(page) - 1) * Number(limit),
      take: Number(limit),
    }),
    prisma.product.count({ where }),
  ]);

  return { items, total, page: Number(page) };
});
```

## Request Body

```typescript
// server/api/products/index.post.ts
export default defineEventHandler(async (event) => {
  // Read JSON body
  const body = await readBody(event);

  // Read form data
  const formData = await readFormData(event);

  // Read raw body
  const rawBody = await readRawBody(event);

  return await prisma.product.create({ data: body });
});
```

## Validation with Zod

```typescript
// server/api/products/index.post.ts
import { z } from 'zod';

const createProductSchema = z.object({
  name: z.string().min(2).max(100),
  description: z.string().max(1000).optional(),
  price: z.number().min(0),
  categoryId: z.string().uuid(),
});

export default defineEventHandler(async (event) => {
  const body = await readBody(event);

  // Validate
  const result = createProductSchema.safeParse(body);

  if (!result.success) {
    throw createError({
      statusCode: 400,
      message: 'Validation failed',
      data: result.error.flatten(),
    });
  }

  return await prisma.product.create({ data: result.data });
});
```

## Validated Body Helper

```typescript
// server/api/products/index.post.ts
import { z } from 'zod';

const schema = z.object({
  name: z.string(),
  price: z.number(),
});

export default defineEventHandler(async (event) => {
  // Throws 400 if validation fails
  const body = await readValidatedBody(event, schema.parse);

  return await prisma.product.create({ data: body });
});
```

## Headers and Cookies

```typescript
export default defineEventHandler(async (event) => {
  // Read headers
  const authHeader = getHeader(event, 'authorization');
  const allHeaders = getHeaders(event);

  // Read cookies
  const token = getCookie(event, 'auth-token');
  const allCookies = parseCookies(event);

  // Set headers
  setHeader(event, 'X-Custom-Header', 'value');
  setHeaders(event, { 'X-One': '1', 'X-Two': '2' });

  // Set cookies
  setCookie(event, 'session', 'value', {
    httpOnly: true,
    secure: true,
    maxAge: 60 * 60 * 24, // 1 day
  });

  // Delete cookie
  deleteCookie(event, 'old-cookie');

  return { success: true };
});
```

## Response Handling

```typescript
export default defineEventHandler(async (event) => {
  // Set status code
  setResponseStatus(event, 201);

  // Redirect
  await sendRedirect(event, '/new-location', 302);

  // Send file
  await sendStream(event, fileStream);

  // No content
  return null; // 204 No Content

  // Custom response
  return send(event, 'Plain text', 'text/plain');
});
```

## Error Handling

```typescript
export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id');

  // Not found
  if (!id) {
    throw createError({
      statusCode: 400,
      message: 'ID is required',
    });
  }

  const product = await prisma.product.findUnique({ where: { id } });

  if (!product) {
    throw createError({
      statusCode: 404,
      statusMessage: 'Not Found',
      message: 'Product not found',
      data: { id },
    });
  }

  // Auth error
  const user = event.context.user;
  if (!user) {
    throw createError({
      statusCode: 401,
      message: 'Unauthorized',
    });
  }

  // Forbidden
  if (product.userId !== user.id) {
    throw createError({
      statusCode: 403,
      message: 'Forbidden',
    });
  }

  return product;
});
```

## Server Middleware

```typescript
// server/middleware/auth.ts
export default defineEventHandler(async (event) => {
  // Skip public routes
  const path = getRequestURL(event).pathname;
  if (path.startsWith('/api/public')) return;

  // Get token
  const token = getHeader(event, 'authorization')?.replace('Bearer ', '');

  if (!token) {
    throw createError({ statusCode: 401 });
  }

  // Verify and attach user
  const user = await verifyToken(token);
  event.context.user = user;
});

// server/middleware/log.ts
export default defineEventHandler((event) => {
  console.log(`${event.method} ${event.path}`);
});
```

## Server Utilities

```typescript
// server/utils/auth.ts
export async function requireAuth(event: H3Event) {
  const user = event.context.user;

  if (!user) {
    throw createError({ statusCode: 401, message: 'Unauthorized' });
  }

  return user;
}

export async function requireRole(event: H3Event, role: string) {
  const user = await requireAuth(event);

  if (user.role !== role) {
    throw createError({ statusCode: 403, message: 'Forbidden' });
  }

  return user;
}

// Usage in API route - auto-imported
export default defineEventHandler(async (event) => {
  const user = await requireAuth(event);
  // ...
});
```

## Database Setup

```typescript
// server/utils/db.ts
import { PrismaClient } from '@prisma/client';

const globalForPrisma = globalThis as { prisma?: PrismaClient };

export const prisma =
  globalForPrisma.prisma ??
  new PrismaClient({
    log: process.env.NODE_ENV === 'development' ? ['query'] : [],
  });

if (process.env.NODE_ENV !== 'production') {
  globalForPrisma.prisma = prisma;
}

// Auto-imported in server code
// const products = await prisma.product.findMany();
```

## Best Practices

1. **Validate inputs** - Always validate request data
2. **Handle errors** - Use createError for consistent errors
3. **Auth middleware** - Centralize authentication
4. **Type safety** - Use TypeScript throughout
5. **Auto-import utils** - Put reusable logic in server/utils
6. **Method-specific files** - Cleaner than conditionals
