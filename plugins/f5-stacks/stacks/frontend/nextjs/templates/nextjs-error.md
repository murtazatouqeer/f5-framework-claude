---
name: nextjs-error
description: Next.js App Router error handling template
applies_to: nextjs
variables:
  - name: ERROR_TYPE
    description: Type of error component (error, not-found, global)
---

# Next.js Error Handling Template

## Error Boundary

```tsx
// app/{{ROUTE_PATH}}/error.tsx
'use client';

import { useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { AlertCircle, RefreshCw } from 'lucide-react';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log error to error reporting service
    console.error('Error:', error);
  }, [error]);

  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] space-y-6">
      <div className="flex items-center gap-2 text-destructive">
        <AlertCircle className="h-8 w-8" />
        <h2 className="text-2xl font-bold">Something went wrong!</h2>
      </div>

      <p className="text-muted-foreground max-w-md text-center">
        We encountered an error while processing your request.
        Please try again or contact support if the problem persists.
      </p>

      {error.digest && (
        <p className="text-sm text-muted-foreground">
          Error ID: {error.digest}
        </p>
      )}

      <div className="flex gap-4">
        <Button onClick={reset} variant="default">
          <RefreshCw className="h-4 w-4 mr-2" />
          Try Again
        </Button>
        <Button variant="outline" onClick={() => window.location.href = '/'}>
          Go Home
        </Button>
      </div>
    </div>
  );
}
```

## Global Error Handler

```tsx
// app/global-error.tsx
'use client';

import { Button } from '@/components/ui/button';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html>
      <body>
        <div className="flex flex-col items-center justify-center min-h-screen bg-background">
          <div className="max-w-md text-center space-y-6 p-8">
            <h1 className="text-4xl font-bold text-destructive">
              Critical Error
            </h1>

            <p className="text-muted-foreground">
              A critical error occurred. Please refresh the page or try again later.
            </p>

            {error.digest && (
              <p className="text-sm text-muted-foreground font-mono">
                Error ID: {error.digest}
              </p>
            )}

            <div className="flex gap-4 justify-center">
              <Button onClick={reset}>
                Try Again
              </Button>
              <Button
                variant="outline"
                onClick={() => window.location.reload()}
              >
                Refresh Page
              </Button>
            </div>
          </div>
        </div>
      </body>
    </html>
  );
}
```

## Not Found Page

```tsx
// app/not-found.tsx
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Home, ArrowLeft } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[600px] space-y-6">
      <div className="text-center space-y-2">
        <h1 className="text-9xl font-bold text-muted-foreground/20">404</h1>
        <h2 className="text-2xl font-bold">Page Not Found</h2>
        <p className="text-muted-foreground max-w-md">
          The page you're looking for doesn't exist or has been moved.
        </p>
      </div>

      <div className="flex gap-4">
        <Button asChild>
          <Link href="/">
            <Home className="h-4 w-4 mr-2" />
            Go Home
          </Link>
        </Button>
        <Button variant="outline" onClick={() => history.back()}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Go Back
        </Button>
      </div>
    </div>
  );
}
```

## Dynamic Not Found

```tsx
// app/products/[id]/page.tsx
import { notFound } from 'next/navigation';
import { db } from '@/lib/db';

export default async function ProductPage({
  params,
}: {
  params: { id: string };
}) {
  const product = await db.product.findUnique({
    where: { id: params.id },
  });

  if (!product) {
    notFound();
  }

  return <ProductView product={product} />;
}

// app/products/[id]/not-found.tsx
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Package } from 'lucide-react';

export default function ProductNotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] space-y-6">
      <Package className="h-16 w-16 text-muted-foreground" />

      <div className="text-center space-y-2">
        <h2 className="text-2xl font-bold">Product Not Found</h2>
        <p className="text-muted-foreground">
          The product you're looking for doesn't exist or has been removed.
        </p>
      </div>

      <Button asChild>
        <Link href="/products">
          Browse Products
        </Link>
      </Button>
    </div>
  );
}
```

## Unauthorized Page

```tsx
// app/unauthorized/page.tsx
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { ShieldX, LogIn } from 'lucide-react';

export default function UnauthorizedPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[600px] space-y-6">
      <ShieldX className="h-16 w-16 text-destructive" />

      <div className="text-center space-y-2">
        <h1 className="text-2xl font-bold">Access Denied</h1>
        <p className="text-muted-foreground max-w-md">
          You don't have permission to access this page.
          Please log in with an authorized account.
        </p>
      </div>

      <div className="flex gap-4">
        <Button asChild>
          <Link href="/login">
            <LogIn className="h-4 w-4 mr-2" />
            Sign In
          </Link>
        </Button>
        <Button variant="outline" asChild>
          <Link href="/">
            Go Home
          </Link>
        </Button>
      </div>
    </div>
  );
}
```

## Error with Details (Development)

```tsx
// app/{{ROUTE_PATH}}/error.tsx
'use client';

import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertCircle, ChevronDown, ChevronUp, RefreshCw } from 'lucide-react';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const [showDetails, setShowDetails] = useState(false);
  const isDev = process.env.NODE_ENV === 'development';

  useEffect(() => {
    console.error('Error:', error);
  }, [error]);

  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] space-y-6 p-4">
      <Card className="w-full max-w-lg">
        <CardHeader className="text-center">
          <AlertCircle className="h-12 w-12 text-destructive mx-auto mb-4" />
          <CardTitle>Something went wrong</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-center text-muted-foreground">
            {error.message || 'An unexpected error occurred'}
          </p>

          {error.digest && (
            <p className="text-center text-sm text-muted-foreground">
              Error ID: <code className="font-mono">{error.digest}</code>
            </p>
          )}

          {isDev && (
            <div>
              <Button
                variant="ghost"
                size="sm"
                className="w-full"
                onClick={() => setShowDetails(!showDetails)}
              >
                {showDetails ? (
                  <>
                    <ChevronUp className="h-4 w-4 mr-2" />
                    Hide Details
                  </>
                ) : (
                  <>
                    <ChevronDown className="h-4 w-4 mr-2" />
                    Show Details
                  </>
                )}
              </Button>

              {showDetails && (
                <pre className="mt-4 p-4 bg-muted rounded-md text-xs overflow-auto max-h-64">
                  {error.stack}
                </pre>
              )}
            </div>
          )}

          <div className="flex gap-4 justify-center">
            <Button onClick={reset}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Try Again
            </Button>
            <Button variant="outline" asChild>
              <a href="/">Go Home</a>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
```

## Usage

```bash
f5 generate error Dashboard --type error
f5 generate error Products --type not-found
f5 generate error Global --type global-error
```
