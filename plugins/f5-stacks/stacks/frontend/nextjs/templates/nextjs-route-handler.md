---
name: nextjs-route-handler
description: Next.js App Router API route handler template
applies_to: nextjs
variables:
  - name: RESOURCE_NAME
    description: Name of the resource (e.g., users, products)
  - name: HAS_AUTH
    description: Whether route requires authentication
  - name: IS_DYNAMIC
    description: Whether route has dynamic params
---

# Next.js Route Handler Template

## Basic CRUD Route Handler

```ts
// app/api/{{RESOURCE_NAME}}/route.ts
import { NextResponse } from 'next/server';
import { z } from 'zod';
import { db } from '@/lib/db';
import { auth } from '@/lib/auth';

// Validation schema
const create{{RESOURCE_NAME | pascal}}Schema = z.object({
  name: z.string().min(1).max(255),
  description: z.string().optional(),
  // Add more fields as needed
});

// GET - List all {{RESOURCE_NAME}}
export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const page = parseInt(searchParams.get('page') || '1');
    const limit = parseInt(searchParams.get('limit') || '10');
    const search = searchParams.get('search') || '';

    const skip = (page - 1) * limit;

    const [items, total] = await Promise.all([
      db.{{RESOURCE_NAME | singular}}.findMany({
        where: search ? {
          name: { contains: search, mode: 'insensitive' },
        } : undefined,
        skip,
        take: limit,
        orderBy: { createdAt: 'desc' },
      }),
      db.{{RESOURCE_NAME | singular}}.count({
        where: search ? {
          name: { contains: search, mode: 'insensitive' },
        } : undefined,
      }),
    ]);

    return NextResponse.json({
      items,
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit),
      },
    });
  } catch (error) {
    console.error('GET /api/{{RESOURCE_NAME}} error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch {{RESOURCE_NAME}}' },
      { status: 500 }
    );
  }
}

// POST - Create new {{RESOURCE_NAME | singular}}
export async function POST(request: Request) {
  try {
    const session = await auth();
    if (!session?.user) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const body = await request.json();
    const validated = create{{RESOURCE_NAME | pascal}}Schema.safeParse(body);

    if (!validated.success) {
      return NextResponse.json(
        { error: 'Validation failed', details: validated.error.flatten() },
        { status: 400 }
      );
    }

    const item = await db.{{RESOURCE_NAME | singular}}.create({
      data: {
        ...validated.data,
        userId: session.user.id,
      },
    });

    return NextResponse.json(item, { status: 201 });
  } catch (error) {
    console.error('POST /api/{{RESOURCE_NAME}} error:', error);
    return NextResponse.json(
      { error: 'Failed to create {{RESOURCE_NAME | singular}}' },
      { status: 500 }
    );
  }
}
```

## Dynamic Route Handler

```ts
// app/api/{{RESOURCE_NAME}}/[id]/route.ts
import { NextResponse } from 'next/server';
import { z } from 'zod';
import { db } from '@/lib/db';
import { auth } from '@/lib/auth';

const update{{RESOURCE_NAME | pascal}}Schema = z.object({
  name: z.string().min(1).max(255).optional(),
  description: z.string().optional(),
});

interface RouteParams {
  params: { id: string };
}

// GET - Get single {{RESOURCE_NAME | singular}}
export async function GET(
  request: Request,
  { params }: RouteParams
) {
  try {
    const item = await db.{{RESOURCE_NAME | singular}}.findUnique({
      where: { id: params.id },
      include: {
        user: {
          select: { id: true, name: true, email: true },
        },
      },
    });

    if (!item) {
      return NextResponse.json(
        { error: '{{RESOURCE_NAME | pascal}} not found' },
        { status: 404 }
      );
    }

    return NextResponse.json(item);
  } catch (error) {
    console.error(`GET /api/{{RESOURCE_NAME}}/${params.id} error:`, error);
    return NextResponse.json(
      { error: 'Failed to fetch {{RESOURCE_NAME | singular}}' },
      { status: 500 }
    );
  }
}

// PATCH - Update {{RESOURCE_NAME | singular}}
export async function PATCH(
  request: Request,
  { params }: RouteParams
) {
  try {
    const session = await auth();
    if (!session?.user) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const item = await db.{{RESOURCE_NAME | singular}}.findUnique({
      where: { id: params.id },
    });

    if (!item) {
      return NextResponse.json(
        { error: '{{RESOURCE_NAME | pascal}} not found' },
        { status: 404 }
      );
    }

    // Check ownership
    if (item.userId !== session.user.id) {
      return NextResponse.json(
        { error: 'Forbidden' },
        { status: 403 }
      );
    }

    const body = await request.json();
    const validated = update{{RESOURCE_NAME | pascal}}Schema.safeParse(body);

    if (!validated.success) {
      return NextResponse.json(
        { error: 'Validation failed', details: validated.error.flatten() },
        { status: 400 }
      );
    }

    const updated = await db.{{RESOURCE_NAME | singular}}.update({
      where: { id: params.id },
      data: validated.data,
    });

    return NextResponse.json(updated);
  } catch (error) {
    console.error(`PATCH /api/{{RESOURCE_NAME}}/${params.id} error:`, error);
    return NextResponse.json(
      { error: 'Failed to update {{RESOURCE_NAME | singular}}' },
      { status: 500 }
    );
  }
}

// DELETE - Delete {{RESOURCE_NAME | singular}}
export async function DELETE(
  request: Request,
  { params }: RouteParams
) {
  try {
    const session = await auth();
    if (!session?.user) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const item = await db.{{RESOURCE_NAME | singular}}.findUnique({
      where: { id: params.id },
    });

    if (!item) {
      return NextResponse.json(
        { error: '{{RESOURCE_NAME | pascal}} not found' },
        { status: 404 }
      );
    }

    // Check ownership
    if (item.userId !== session.user.id) {
      return NextResponse.json(
        { error: 'Forbidden' },
        { status: 403 }
      );
    }

    await db.{{RESOURCE_NAME | singular}}.delete({
      where: { id: params.id },
    });

    return new NextResponse(null, { status: 204 });
  } catch (error) {
    console.error(`DELETE /api/{{RESOURCE_NAME}}/${params.id} error:`, error);
    return NextResponse.json(
      { error: 'Failed to delete {{RESOURCE_NAME | singular}}' },
      { status: 500 }
    );
  }
}
```

## File Upload Route

```ts
// app/api/upload/route.ts
import { NextResponse } from 'next/server';
import { auth } from '@/lib/auth';
import { put } from '@vercel/blob';

export async function POST(request: Request) {
  try {
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

    const blob = await put(file.name, file, {
      access: 'public',
    });

    return NextResponse.json({ url: blob.url });
  } catch (error) {
    console.error('POST /api/upload error:', error);
    return NextResponse.json(
      { error: 'Upload failed' },
      { status: 500 }
    );
  }
}
```

## Edge Runtime Route

```ts
// app/api/edge/route.ts
export const runtime = 'edge';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const query = searchParams.get('q');

  // Edge-compatible operations
  const response = await fetch(`https://api.example.com/search?q=${query}`);
  const data = await response.json();

  return Response.json(data, {
    headers: {
      'Cache-Control': 's-maxage=60, stale-while-revalidate',
    },
  });
}
```

## Webhook Handler

```ts
// app/api/webhooks/stripe/route.ts
import { NextResponse } from 'next/server';
import { headers } from 'next/headers';
import Stripe from 'stripe';
import { db } from '@/lib/db';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: '2023-10-16',
});

export async function POST(request: Request) {
  const body = await request.text();
  const signature = headers().get('stripe-signature')!;

  let event: Stripe.Event;

  try {
    event = stripe.webhooks.constructEvent(
      body,
      signature,
      process.env.STRIPE_WEBHOOK_SECRET!
    );
  } catch (error) {
    console.error('Webhook signature verification failed:', error);
    return NextResponse.json(
      { error: 'Invalid signature' },
      { status: 400 }
    );
  }

  switch (event.type) {
    case 'checkout.session.completed':
      const session = event.data.object as Stripe.Checkout.Session;
      await handleCheckoutComplete(session);
      break;

    case 'invoice.payment_succeeded':
      const invoice = event.data.object as Stripe.Invoice;
      await handlePaymentSucceeded(invoice);
      break;

    default:
      console.log(`Unhandled event type: ${event.type}`);
  }

  return NextResponse.json({ received: true });
}

async function handleCheckoutComplete(session: Stripe.Checkout.Session) {
  // Handle checkout completion
}

async function handlePaymentSucceeded(invoice: Stripe.Invoice) {
  // Handle payment success
}
```

## Usage

```bash
f5 generate api users --crud
f5 generate api products --crud --auth
f5 generate api upload --type file
f5 generate api webhooks/stripe --type webhook
```
