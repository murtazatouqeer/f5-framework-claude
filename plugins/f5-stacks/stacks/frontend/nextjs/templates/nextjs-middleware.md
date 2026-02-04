---
name: nextjs-middleware
description: Next.js middleware template
applies_to: nextjs
variables:
  - name: AUTH_REQUIRED
    description: Whether authentication is required
  - name: HAS_RATE_LIMIT
    description: Whether rate limiting is enabled
  - name: HAS_MULTI_TENANT
    description: Whether multi-tenant support is needed
---

# Next.js Middleware Template

## Basic Authentication Middleware

```ts
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { getToken } from 'next-auth/jwt';

// Routes that don't require authentication
const publicRoutes = [
  '/',
  '/login',
  '/register',
  '/forgot-password',
  '/reset-password',
  '/verify-email',
];

// Routes that authenticated users shouldn't access
const authRoutes = ['/login', '/register'];

// API routes that don't require authentication
const publicApiRoutes = [
  '/api/auth',
  '/api/webhooks',
  '/api/health',
];

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Skip public API routes
  if (publicApiRoutes.some((route) => pathname.startsWith(route))) {
    return NextResponse.next();
  }

  // Get the token
  const token = await getToken({
    req: request,
    secret: process.env.NEXTAUTH_SECRET,
  });

  const isPublicRoute = publicRoutes.includes(pathname);
  const isAuthRoute = authRoutes.includes(pathname);
  const isApiRoute = pathname.startsWith('/api');

  // Redirect authenticated users away from auth pages
  if (token && isAuthRoute) {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }

  // Protect non-public routes
  if (!token && !isPublicRoute) {
    if (isApiRoute) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('callbackUrl', pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico|public).*)',
  ],
};
```

## Role-Based Access Middleware

```ts
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { getToken } from 'next-auth/jwt';

type Role = 'user' | 'admin' | 'moderator';

interface RouteConfig {
  pattern: string;
  roles: Role[];
}

const protectedRoutes: RouteConfig[] = [
  { pattern: '/admin', roles: ['admin'] },
  { pattern: '/mod', roles: ['admin', 'moderator'] },
  { pattern: '/dashboard', roles: ['user', 'admin', 'moderator'] },
];

function matchRoute(pathname: string, pattern: string): boolean {
  if (pattern.endsWith('*')) {
    return pathname.startsWith(pattern.slice(0, -1));
  }
  return pathname === pattern || pathname.startsWith(`${pattern}/`);
}

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  const token = await getToken({
    req: request,
    secret: process.env.NEXTAUTH_SECRET,
  });

  // Check protected routes
  for (const route of protectedRoutes) {
    if (matchRoute(pathname, route.pattern)) {
      if (!token) {
        return NextResponse.redirect(new URL('/login', request.url));
      }

      const userRole = (token.role as Role) || 'user';

      if (!route.roles.includes(userRole)) {
        return NextResponse.redirect(new URL('/unauthorized', request.url));
      }
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/admin/:path*', '/mod/:path*', '/dashboard/:path*'],
};
```

## Multi-Tenant Middleware

```ts
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export async function middleware(request: NextRequest) {
  const hostname = request.headers.get('host') || '';
  const { pathname } = request.nextUrl;

  // Extract subdomain
  const subdomain = hostname.split('.')[0];

  // Main domains (not tenant)
  const mainDomains = ['www', 'app', 'localhost:3000'];
  const isTenantDomain = !mainDomains.includes(subdomain);

  if (isTenantDomain) {
    // Rewrite to tenant-specific routes
    const url = request.nextUrl.clone();
    url.pathname = `/tenant/${subdomain}${pathname}`;

    return NextResponse.rewrite(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!api|_next|_static|_vercel|[\\w-]+\\.\\w+).*)'],
};
```

## Rate Limiting Middleware

```ts
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { Ratelimit } from '@upstash/ratelimit';
import { Redis } from '@upstash/redis';

const redis = new Redis({
  url: process.env.UPSTASH_REDIS_REST_URL!,
  token: process.env.UPSTASH_REDIS_REST_TOKEN!,
});

const ratelimit = new Ratelimit({
  redis,
  limiter: Ratelimit.slidingWindow(10, '10 s'),
  analytics: true,
});

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Only rate limit API routes
  if (pathname.startsWith('/api')) {
    const ip = request.ip ?? '127.0.0.1';
    const { success, limit, reset, remaining } = await ratelimit.limit(
      `ratelimit_${ip}`
    );

    if (!success) {
      return NextResponse.json(
        { error: 'Too many requests' },
        {
          status: 429,
          headers: {
            'X-RateLimit-Limit': limit.toString(),
            'X-RateLimit-Remaining': remaining.toString(),
            'X-RateLimit-Reset': reset.toString(),
          },
        }
      );
    }

    const response = NextResponse.next();
    response.headers.set('X-RateLimit-Limit', limit.toString());
    response.headers.set('X-RateLimit-Remaining', remaining.toString());
    response.headers.set('X-RateLimit-Reset', reset.toString());

    return response;
  }

  return NextResponse.next();
}

export const config = {
  matcher: '/api/:path*',
};
```

## Geolocation Middleware

```ts
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const SUPPORTED_LOCALES = ['en', 'ja', 'ko', 'zh'];
const DEFAULT_LOCALE = 'en';

const COUNTRY_LOCALE_MAP: Record<string, string> = {
  JP: 'ja',
  KR: 'ko',
  CN: 'zh',
  TW: 'zh',
};

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Skip if already has locale prefix
  const hasLocale = SUPPORTED_LOCALES.some(
    (locale) => pathname.startsWith(`/${locale}/`) || pathname === `/${locale}`
  );

  if (hasLocale) {
    return NextResponse.next();
  }

  // Get locale from geo or accept-language
  const country = request.geo?.country || '';
  const acceptLanguage = request.headers.get('accept-language') || '';

  let locale = COUNTRY_LOCALE_MAP[country] ||
    acceptLanguage.split(',')[0]?.split('-')[0] ||
    DEFAULT_LOCALE;

  if (!SUPPORTED_LOCALES.includes(locale)) {
    locale = DEFAULT_LOCALE;
  }

  // Redirect to localized path
  const url = request.nextUrl.clone();
  url.pathname = `/${locale}${pathname}`;

  return NextResponse.redirect(url);
}

export const config = {
  matcher: ['/((?!api|_next|_static|_vercel|favicon.ico|.*\\.).*)'],
};
```

## Combined Middleware

```ts
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { getToken } from 'next-auth/jwt';

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const response = NextResponse.next();

  // 1. Security headers
  response.headers.set('X-Frame-Options', 'DENY');
  response.headers.set('X-Content-Type-Options', 'nosniff');
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');

  // 2. Skip public assets
  if (
    pathname.startsWith('/_next') ||
    pathname.startsWith('/api/auth') ||
    pathname.includes('.')
  ) {
    return response;
  }

  // 3. Authentication check
  const token = await getToken({
    req: request,
    secret: process.env.NEXTAUTH_SECRET,
  });

  const isProtected = pathname.startsWith('/dashboard') ||
    pathname.startsWith('/settings') ||
    pathname.startsWith('/api/protected');

  if (isProtected && !token) {
    if (pathname.startsWith('/api')) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }
    return NextResponse.redirect(new URL('/login', request.url));
  }

  // 4. Add user info to headers (for API routes)
  if (token) {
    response.headers.set('x-user-id', token.sub || '');
    response.headers.set('x-user-role', (token.role as string) || 'user');
  }

  return response;
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};
```

## Usage

```bash
f5 generate middleware auth
f5 generate middleware rate-limit
f5 generate middleware multi-tenant
f5 generate middleware i18n
```
