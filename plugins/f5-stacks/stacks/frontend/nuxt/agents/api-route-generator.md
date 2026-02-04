---
name: nuxt-api-route-generator
description: Generates Nuxt 3 server API routes with Nitro
applies_to: nuxt
---

# Nuxt API Route Generator Agent

## Purpose
Generate production-ready Nitro server API routes with proper validation, error handling, and TypeScript types.

## Capabilities
- RESTful API endpoints
- Request validation with Zod
- Error handling
- Authentication middleware
- Database integration patterns

## Input Requirements
- Resource name
- HTTP methods needed
- Data schema
- Auth requirements

## Output Deliverables
1. API route files (server/api/)
2. Validation schemas
3. Type definitions
4. Server utilities

## Generation Process

### 1. Analyze Requirements
```yaml
api_analysis:
  - resource: "products"
  - methods: ["GET", "POST", "PUT", "DELETE"]
  - auth_required: true
  - validation: "zod"
  - database: "prisma"
```

### 2. Generate API Routes

#### GET List - server/api/{{resources}}/index.get.ts
```typescript
import { z } from 'zod';

const querySchema = z.object({
  page: z.coerce.number().min(1).default(1),
  limit: z.coerce.number().min(1).max(100).default(20),
  search: z.string().optional(),
  status: z.enum(['active', 'inactive', 'all']).default('all'),
  sortBy: z.enum(['createdAt', 'name', 'price']).default('createdAt'),
  sortOrder: z.enum(['asc', 'desc']).default('desc'),
});

export default defineEventHandler(async (event) => {
  // Parse and validate query
  const query = await getValidatedQuery(event, querySchema.parse);
  const { page, limit, search, status, sortBy, sortOrder } = query;

  // Build where clause
  const where = {
    ...(search && {
      OR: [
        { name: { contains: search, mode: 'insensitive' } },
        { description: { contains: search, mode: 'insensitive' } },
      ],
    }),
    ...(status !== 'all' && { status }),
  };

  // Execute queries
  const [items, total] = await Promise.all([
    prisma.{{resource}}.findMany({
      where,
      skip: (page - 1) * limit,
      take: limit,
      orderBy: { [sortBy]: sortOrder },
      include: { category: true },
    }),
    prisma.{{resource}}.count({ where }),
  ]);

  return {
    items,
    total,
    page,
    limit,
    totalPages: Math.ceil(total / limit),
  };
});
```

#### GET Single - server/api/{{resources}}/[id].get.ts
```typescript
export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id');

  if (!id) {
    throw createError({
      statusCode: 400,
      message: 'ID is required',
    });
  }

  const item = await prisma.{{resource}}.findUnique({
    where: { id },
    include: {
      category: true,
      reviews: {
        take: 10,
        orderBy: { createdAt: 'desc' },
      },
    },
  });

  if (!item) {
    throw createError({
      statusCode: 404,
      message: '{{Resource}} not found',
    });
  }

  return item;
});
```

#### POST Create - server/api/{{resources}}/index.post.ts
```typescript
import { z } from 'zod';

const createSchema = z.object({
  name: z.string().min(2).max(100),
  description: z.string().max(1000).optional(),
  price: z.number().min(0),
  categoryId: z.string().uuid(),
  status: z.enum(['active', 'inactive']).default('active'),
});

export default defineEventHandler(async (event) => {
  // Auth check
  const session = await requireAuth(event);

  // Validate body
  const body = await readValidatedBody(event, createSchema.parse);

  // Create resource
  const item = await prisma.{{resource}}.create({
    data: {
      ...body,
      userId: session.user.id,
      slug: slugify(body.name),
    },
    include: { category: true },
  });

  setResponseStatus(event, 201);
  return item;
});
```

#### PUT Update - server/api/{{resources}}/[id].put.ts
```typescript
import { z } from 'zod';

const updateSchema = z.object({
  name: z.string().min(2).max(100).optional(),
  description: z.string().max(1000).optional(),
  price: z.number().min(0).optional(),
  categoryId: z.string().uuid().optional(),
  status: z.enum(['active', 'inactive']).optional(),
});

export default defineEventHandler(async (event) => {
  const session = await requireAuth(event);
  const id = getRouterParam(event, 'id');

  // Check existence and ownership
  const existing = await prisma.{{resource}}.findUnique({
    where: { id },
    select: { userId: true },
  });

  if (!existing) {
    throw createError({ statusCode: 404, message: 'Not found' });
  }

  if (existing.userId !== session.user.id) {
    throw createError({ statusCode: 403, message: 'Forbidden' });
  }

  // Validate and update
  const body = await readValidatedBody(event, updateSchema.parse);

  const updated = await prisma.{{resource}}.update({
    where: { id },
    data: body,
    include: { category: true },
  });

  return updated;
});
```

#### DELETE - server/api/{{resources}}/[id].delete.ts
```typescript
export default defineEventHandler(async (event) => {
  const session = await requireAuth(event);
  const id = getRouterParam(event, 'id');

  // Check existence and ownership
  const existing = await prisma.{{resource}}.findUnique({
    where: { id },
    select: { userId: true },
  });

  if (!existing) {
    throw createError({ statusCode: 404, message: 'Not found' });
  }

  if (existing.userId !== session.user.id) {
    throw createError({ statusCode: 403, message: 'Forbidden' });
  }

  await prisma.{{resource}}.delete({ where: { id } });

  return { success: true };
});
```

### 3. Server Utilities

#### server/utils/auth.ts
```typescript
export async function requireAuth(event: H3Event) {
  const session = await getServerSession(event);

  if (!session?.user) {
    throw createError({
      statusCode: 401,
      message: 'Unauthorized',
    });
  }

  return session;
}

export async function requireRole(event: H3Event, role: string) {
  const session = await requireAuth(event);

  if (session.user.role !== role) {
    throw createError({
      statusCode: 403,
      message: 'Insufficient permissions',
    });
  }

  return session;
}
```

## Directory Structure
```
server/
├── api/
│   └── {{resources}}/
│       ├── index.get.ts
│       ├── index.post.ts
│       ├── [id].get.ts
│       ├── [id].put.ts
│       └── [id].delete.ts
├── middleware/
│   └── auth.ts
└── utils/
    ├── auth.ts
    ├── db.ts
    └── validation.ts
```

## Quality Checklist
- [ ] Input validation with Zod
- [ ] Proper error handling
- [ ] Authentication checks
- [ ] Authorization checks
- [ ] TypeScript types
- [ ] Response formatting
