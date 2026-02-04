# Next.js API Route Generator Agent

## Role
Generate Next.js Route Handlers (API routes) with proper patterns and validation.

## Triggers
- "create api"
- "api route"
- "route handler"
- "nextjs api"

## Capabilities
- Generate route.ts files with HTTP methods
- Implement request/response handling
- Add Zod validation
- Handle authentication
- Generate typed responses
- Create OpenAPI documentation

## Input Requirements
```yaml
required:
  - route: string          # API route path
  - methods: array         # HTTP methods (GET, POST, etc.)

optional:
  - entity: string         # Entity name for CRUD
  - auth_required: boolean # Requires authentication
  - validation: object     # Zod schema definition
  - response_type: string  # Response format
```

## Output Structure
```
app/api/{route}/
├── route.ts              # Route handler
└── types.ts              # Request/Response types (if complex)
```

## Generation Rules

### 1. Basic Route Handler
```tsx
// app/api/products/route.ts
import { NextResponse } from 'next/server';
import { z } from 'zod';
import { db } from '@/lib/db';

// GET /api/products
export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const page = Number(searchParams.get('page')) || 1;
    const limit = Number(searchParams.get('limit')) || 10;
    const skip = (page - 1) * limit;

    const [products, total] = await Promise.all([
      db.product.findMany({
        skip,
        take: limit,
        orderBy: { createdAt: 'desc' },
      }),
      db.product.count(),
    ]);

    return NextResponse.json({
      data: products,
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit),
      },
    });
  } catch (error) {
    console.error('GET /api/products error:', error);
    return NextResponse.json(
      { error: 'Internal Server Error' },
      { status: 500 }
    );
  }
}

// POST /api/products
const createProductSchema = z.object({
  name: z.string().min(2).max(100),
  description: z.string().max(1000).optional(),
  price: z.number().min(0),
  categoryId: z.string().uuid(),
});

export async function POST(request: Request) {
  try {
    const body = await request.json();

    const validatedData = createProductSchema.safeParse(body);

    if (!validatedData.success) {
      return NextResponse.json(
        { error: 'Validation failed', details: validatedData.error.flatten() },
        { status: 400 }
      );
    }

    const product = await db.product.create({
      data: validatedData.data,
    });

    return NextResponse.json(product, { status: 201 });
  } catch (error) {
    console.error('POST /api/products error:', error);
    return NextResponse.json(
      { error: 'Internal Server Error' },
      { status: 500 }
    );
  }
}
```

### 2. Dynamic Route Handler
```tsx
// app/api/products/[id]/route.ts
import { NextResponse } from 'next/server';
import { z } from 'zod';
import { db } from '@/lib/db';

interface RouteParams {
  params: { id: string };
}

// GET /api/products/[id]
export async function GET(request: Request, { params }: RouteParams) {
  try {
    const product = await db.product.findUnique({
      where: { id: params.id },
      include: { category: true },
    });

    if (!product) {
      return NextResponse.json(
        { error: 'Product not found' },
        { status: 404 }
      );
    }

    return NextResponse.json(product);
  } catch (error) {
    console.error(`GET /api/products/${params.id} error:`, error);
    return NextResponse.json(
      { error: 'Internal Server Error' },
      { status: 500 }
    );
  }
}

// PATCH /api/products/[id]
const updateProductSchema = z.object({
  name: z.string().min(2).max(100).optional(),
  description: z.string().max(1000).optional(),
  price: z.number().min(0).optional(),
  categoryId: z.string().uuid().optional(),
});

export async function PATCH(request: Request, { params }: RouteParams) {
  try {
    const body = await request.json();

    const validatedData = updateProductSchema.safeParse(body);

    if (!validatedData.success) {
      return NextResponse.json(
        { error: 'Validation failed', details: validatedData.error.flatten() },
        { status: 400 }
      );
    }

    const product = await db.product.update({
      where: { id: params.id },
      data: validatedData.data,
    });

    return NextResponse.json(product);
  } catch (error) {
    if ((error as any).code === 'P2025') {
      return NextResponse.json(
        { error: 'Product not found' },
        { status: 404 }
      );
    }
    console.error(`PATCH /api/products/${params.id} error:`, error);
    return NextResponse.json(
      { error: 'Internal Server Error' },
      { status: 500 }
    );
  }
}

// DELETE /api/products/[id]
export async function DELETE(request: Request, { params }: RouteParams) {
  try {
    await db.product.delete({
      where: { id: params.id },
    });

    return new NextResponse(null, { status: 204 });
  } catch (error) {
    if ((error as any).code === 'P2025') {
      return NextResponse.json(
        { error: 'Product not found' },
        { status: 404 }
      );
    }
    console.error(`DELETE /api/products/${params.id} error:`, error);
    return NextResponse.json(
      { error: 'Internal Server Error' },
      { status: 500 }
    );
  }
}
```

### 3. Authenticated Route
```tsx
// app/api/user/profile/route.ts
import { NextResponse } from 'next/server';
import { auth } from '@/lib/auth';
import { db } from '@/lib/db';

export async function GET() {
  const session = await auth();

  if (!session?.user) {
    return NextResponse.json(
      { error: 'Unauthorized' },
      { status: 401 }
    );
  }

  const user = await db.user.findUnique({
    where: { id: session.user.id },
    select: {
      id: true,
      name: true,
      email: true,
      image: true,
      createdAt: true,
    },
  });

  return NextResponse.json(user);
}

export async function PATCH(request: Request) {
  const session = await auth();

  if (!session?.user) {
    return NextResponse.json(
      { error: 'Unauthorized' },
      { status: 401 }
    );
  }

  const body = await request.json();

  const user = await db.user.update({
    where: { id: session.user.id },
    data: {
      name: body.name,
    },
    select: {
      id: true,
      name: true,
      email: true,
      image: true,
    },
  });

  return NextResponse.json(user);
}
```

### 4. File Upload Handler
```tsx
// app/api/upload/route.ts
import { NextResponse } from 'next/server';
import { writeFile } from 'fs/promises';
import { join } from 'path';
import { auth } from '@/lib/auth';

export async function POST(request: Request) {
  const session = await auth();

  if (!session?.user) {
    return NextResponse.json(
      { error: 'Unauthorized' },
      { status: 401 }
    );
  }

  const formData = await request.formData();
  const file = formData.get('file') as File;

  if (!file) {
    return NextResponse.json(
      { error: 'No file provided' },
      { status: 400 }
    );
  }

  // Validate file type
  const allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];
  if (!allowedTypes.includes(file.type)) {
    return NextResponse.json(
      { error: 'Invalid file type' },
      { status: 400 }
    );
  }

  // Validate file size (5MB)
  if (file.size > 5 * 1024 * 1024) {
    return NextResponse.json(
      { error: 'File too large' },
      { status: 400 }
    );
  }

  const bytes = await file.arrayBuffer();
  const buffer = Buffer.from(bytes);

  const uniqueName = `${Date.now()}-${file.name}`;
  const path = join(process.cwd(), 'public/uploads', uniqueName);

  await writeFile(path, buffer);

  return NextResponse.json({
    url: `/uploads/${uniqueName}`,
    name: file.name,
    size: file.size,
  });
}
```

### 5. Streaming Response
```tsx
// app/api/stream/route.ts
import { NextResponse } from 'next/server';

export async function GET() {
  const encoder = new TextEncoder();

  const stream = new ReadableStream({
    async start(controller) {
      for (let i = 0; i < 10; i++) {
        const data = encoder.encode(`data: ${JSON.stringify({ count: i })}\n\n`);
        controller.enqueue(data);
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
      controller.close();
    },
  });

  return new NextResponse(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    },
  });
}
```

## Response Helpers
```tsx
// lib/api-response.ts
import { NextResponse } from 'next/server';

export function successResponse<T>(data: T, status = 200) {
  return NextResponse.json({ success: true, data }, { status });
}

export function errorResponse(message: string, status = 400) {
  return NextResponse.json({ success: false, error: message }, { status });
}

export function validationError(errors: Record<string, string[]>) {
  return NextResponse.json(
    { success: false, error: 'Validation failed', details: errors },
    { status: 400 }
  );
}
```

## Validation Checklist
- [ ] Proper HTTP method handlers (GET, POST, etc.)
- [ ] Request body validation with Zod
- [ ] Proper error handling with try/catch
- [ ] Appropriate HTTP status codes
- [ ] Authentication checks where needed
- [ ] TypeScript types for params and body
- [ ] Console logging for debugging
- [ ] Prisma error code handling (P2025, etc.)
