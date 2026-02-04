---
name: nuxt-api-route
description: Template for Nuxt 3 server API routes
applies_to: nuxt
---

# Nuxt API Route Template

## Basic GET Route

```typescript
// server/api/{{RESOURCE}}/index.get.ts
export default defineEventHandler(async (event) => {
  const query = getQuery(event);

  const page = Number(query.page) || 1;
  const limit = Number(query.limit) || 20;
  const offset = (page - 1) * limit;

  const items = await prisma.{{RESOURCE}}.findMany({
    skip: offset,
    take: limit,
    orderBy: { createdAt: 'desc' },
  });

  const total = await prisma.{{RESOURCE}}.count();

  return {
    items,
    pagination: {
      page,
      limit,
      total,
      totalPages: Math.ceil(total / limit),
    },
  };
});
```

## GET by ID Route

```typescript
// server/api/{{RESOURCE}}/[id].get.ts
export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id');

  if (!id) {
    throw createError({
      statusCode: 400,
      statusMessage: 'ID is required',
    });
  }

  const item = await prisma.{{RESOURCE}}.findUnique({
    where: { id },
    include: {
      // Related models
    },
  });

  if (!item) {
    throw createError({
      statusCode: 404,
      statusMessage: '{{RESOURCE_NAME}} not found',
    });
  }

  return item;
});
```

## POST Route

```typescript
// server/api/{{RESOURCE}}/index.post.ts
import { z } from 'zod';

const schema = z.object({
  name: z.string().min(1).max(255),
  description: z.string().optional(),
  // Add more fields
});

export default defineEventHandler(async (event) => {
  const body = await readBody(event);

  // Validate
  const result = schema.safeParse(body);
  if (!result.success) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Validation failed',
      data: result.error.flatten(),
    });
  }

  // Create
  const item = await prisma.{{RESOURCE}}.create({
    data: result.data,
  });

  setResponseStatus(event, 201);
  return item;
});
```

## PUT Route

```typescript
// server/api/{{RESOURCE}}/[id].put.ts
import { z } from 'zod';

const schema = z.object({
  name: z.string().min(1).max(255).optional(),
  description: z.string().optional(),
});

export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id');
  const body = await readBody(event);

  // Validate
  const result = schema.safeParse(body);
  if (!result.success) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Validation failed',
      data: result.error.flatten(),
    });
  }

  // Check exists
  const existing = await prisma.{{RESOURCE}}.findUnique({ where: { id } });
  if (!existing) {
    throw createError({
      statusCode: 404,
      statusMessage: '{{RESOURCE_NAME}} not found',
    });
  }

  // Update
  const item = await prisma.{{RESOURCE}}.update({
    where: { id },
    data: result.data,
  });

  return item;
});
```

## DELETE Route

```typescript
// server/api/{{RESOURCE}}/[id].delete.ts
export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id');

  // Check exists
  const existing = await prisma.{{RESOURCE}}.findUnique({ where: { id } });
  if (!existing) {
    throw createError({
      statusCode: 404,
      statusMessage: '{{RESOURCE_NAME}} not found',
    });
  }

  await prisma.{{RESOURCE}}.delete({ where: { id } });

  setResponseStatus(event, 204);
  return null;
});
```

## Authenticated Route

```typescript
// server/api/{{RESOURCE}}/index.get.ts
export default defineEventHandler(async (event) => {
  // Get session/user from auth
  const session = await requireAuth(event);

  const items = await prisma.{{RESOURCE}}.findMany({
    where: { userId: session.user.id },
  });

  return items;
});
```

## File Upload Route

```typescript
// server/api/upload.post.ts
import { writeFile } from 'fs/promises';
import { join } from 'path';

export default defineEventHandler(async (event) => {
  const form = await readMultipartFormData(event);

  if (!form) {
    throw createError({
      statusCode: 400,
      statusMessage: 'No file uploaded',
    });
  }

  const file = form.find((f) => f.name === 'file');
  if (!file || !file.data) {
    throw createError({
      statusCode: 400,
      statusMessage: 'File is required',
    });
  }

  // Validate file type
  const allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];
  if (!allowedTypes.includes(file.type || '')) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Invalid file type',
    });
  }

  // Save file
  const filename = `${Date.now()}-${file.filename}`;
  const uploadPath = join(process.cwd(), 'public', 'uploads', filename);

  await writeFile(uploadPath, file.data);

  return {
    url: `/uploads/${filename}`,
  };
});
```

## Cached Route

```typescript
// server/api/{{RESOURCE}}/index.get.ts
export default defineCachedEventHandler(
  async (event) => {
    const items = await prisma.{{RESOURCE}}.findMany();
    return items;
  },
  {
    maxAge: 60 * 5, // 5 minutes
    staleMaxAge: 60 * 60, // 1 hour stale
    swr: true,
    name: '{{RESOURCE}}-list',
    getKey: (event) => {
      const query = getQuery(event);
      return `{{RESOURCE}}-${query.page || 1}`;
    },
  }
);
```

## Error Handler

```typescript
// server/utils/errors.ts
export function handlePrismaError(error: unknown) {
  if (error instanceof Prisma.PrismaClientKnownRequestError) {
    if (error.code === 'P2002') {
      throw createError({
        statusCode: 409,
        statusMessage: 'Resource already exists',
      });
    }
    if (error.code === 'P2025') {
      throw createError({
        statusCode: 404,
        statusMessage: 'Resource not found',
      });
    }
  }
  throw error;
}
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{RESOURCE}}` | Resource model name (lowercase) | `product`, `user` |
| `{{RESOURCE_NAME}}` | Human-readable name | `Product`, `User` |
