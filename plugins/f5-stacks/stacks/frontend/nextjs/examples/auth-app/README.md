# Authentication App Example

A complete authentication system built with Next.js 14+ App Router and NextAuth.js v5.

## Features

- Email/Password authentication
- OAuth providers (Google, GitHub)
- Protected routes with middleware
- Server-side session handling
- Role-based access control
- Password reset flow
- Email verification

## Project Structure

```
app/
├── (auth)/
│   ├── layout.tsx            # Auth layout (centered)
│   ├── login/
│   │   └── page.tsx          # Login page
│   ├── register/
│   │   └── page.tsx          # Registration page
│   ├── forgot-password/
│   │   └── page.tsx          # Password reset request
│   ├── reset-password/
│   │   └── page.tsx          # Password reset form
│   └── verify-email/
│       └── page.tsx          # Email verification
├── (dashboard)/
│   ├── layout.tsx            # Dashboard layout
│   ├── dashboard/
│   │   └── page.tsx          # Main dashboard
│   ├── settings/
│   │   ├── page.tsx          # Profile settings
│   │   └── security/
│   │       └── page.tsx      # Security settings
│   └── admin/
│       └── page.tsx          # Admin only page
├── api/
│   └── auth/
│       └── [...nextauth]/
│           └── route.ts      # NextAuth route handler
lib/
├── auth.ts                   # NextAuth configuration
├── auth-utils.ts             # Auth helper functions
└── actions/
    └── auth.ts               # Auth server actions
middleware.ts                 # Route protection
components/
├── auth/
│   ├── login-form.tsx
│   ├── register-form.tsx
│   ├── forgot-password-form.tsx
│   ├── reset-password-form.tsx
│   └── oauth-buttons.tsx
└── providers/
    └── session-provider.tsx
```

## Key Patterns

### NextAuth Configuration

```ts
// lib/auth.ts
import NextAuth from 'next-auth';
import { PrismaAdapter } from '@auth/prisma-adapter';
import Credentials from 'next-auth/providers/credentials';
import Google from 'next-auth/providers/google';
import GitHub from 'next-auth/providers/github';
import bcrypt from 'bcryptjs';

export const { handlers, auth, signIn, signOut } = NextAuth({
  adapter: PrismaAdapter(prisma),
  session: { strategy: 'jwt' },
  pages: {
    signIn: '/login',
    error: '/login',
  },
  providers: [
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET,
    }),
    GitHub({
      clientId: process.env.GITHUB_CLIENT_ID,
      clientSecret: process.env.GITHUB_CLIENT_SECRET,
    }),
    Credentials({
      async authorize(credentials) {
        const user = await prisma.user.findUnique({
          where: { email: credentials.email },
        });

        if (!user || !user.password) return null;

        const isValid = await bcrypt.compare(
          credentials.password,
          user.password
        );

        if (!isValid) return null;

        return user;
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.role = user.role;
      }
      return token;
    },
    async session({ session, token }) {
      if (token) {
        session.user.id = token.sub;
        session.user.role = token.role;
      }
      return session;
    },
  },
});
```

### Middleware Protection

```ts
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { getToken } from 'next-auth/jwt';

const publicRoutes = ['/', '/login', '/register', '/forgot-password'];
const authRoutes = ['/login', '/register'];
const adminRoutes = ['/admin'];

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  const token = await getToken({
    req: request,
    secret: process.env.NEXTAUTH_SECRET,
  });

  // Redirect authenticated users from auth pages
  if (token && authRoutes.includes(pathname)) {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }

  // Protect non-public routes
  if (!token && !publicRoutes.includes(pathname)) {
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('callbackUrl', pathname);
    return NextResponse.redirect(loginUrl);
  }

  // Check admin routes
  if (adminRoutes.some((route) => pathname.startsWith(route))) {
    if (token?.role !== 'admin') {
      return NextResponse.redirect(new URL('/unauthorized', request.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
};
```

### Server-Side Session

```tsx
// app/(dashboard)/dashboard/page.tsx
import { auth } from '@/lib/auth';
import { redirect } from 'next/navigation';

export default async function DashboardPage() {
  const session = await auth();

  if (!session?.user) {
    redirect('/login');
  }

  return (
    <div>
      <h1>Welcome, {session.user.name}</h1>
      <p>Email: {session.user.email}</p>
      <p>Role: {session.user.role}</p>
    </div>
  );
}
```

### Login Form with Server Action

```tsx
// components/auth/login-form.tsx
"use client";

import { useFormState, useFormStatus } from 'react-dom';
import { login } from '@/lib/actions/auth';

export function LoginForm() {
  const [state, formAction] = useFormState(login, {});

  return (
    <form action={formAction} className="space-y-4">
      {state.error && (
        <div className="p-3 bg-red-100 text-red-600 rounded">
          {state.error}
        </div>
      )}

      <div>
        <label htmlFor="email">Email</label>
        <input id="email" name="email" type="email" required />
      </div>

      <div>
        <label htmlFor="password">Password</label>
        <input id="password" name="password" type="password" required />
      </div>

      <SubmitButton />
    </form>
  );
}

function SubmitButton() {
  const { pending } = useFormStatus();
  return (
    <button type="submit" disabled={pending}>
      {pending ? 'Signing in...' : 'Sign In'}
    </button>
  );
}
```

### Auth Server Actions

```ts
// lib/actions/auth.ts
"use server";

import { signIn, signOut } from '@/lib/auth';
import { redirect } from 'next/navigation';
import bcrypt from 'bcryptjs';
import { z } from 'zod';

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
});

export async function login(prevState: any, formData: FormData) {
  const validated = loginSchema.safeParse({
    email: formData.get('email'),
    password: formData.get('password'),
  });

  if (!validated.success) {
    return { error: 'Invalid credentials' };
  }

  try {
    await signIn('credentials', {
      ...validated.data,
      redirect: false,
    });
  } catch (error) {
    return { error: 'Invalid credentials' };
  }

  redirect('/dashboard');
}

export async function logout() {
  await signOut({ redirect: false });
  redirect('/');
}

export async function register(prevState: any, formData: FormData) {
  const email = formData.get('email') as string;
  const password = formData.get('password') as string;
  const name = formData.get('name') as string;

  const existingUser = await prisma.user.findUnique({ where: { email } });

  if (existingUser) {
    return { error: 'Email already registered' };
  }

  const hashedPassword = await bcrypt.hash(password, 12);

  await prisma.user.create({
    data: {
      email,
      name,
      password: hashedPassword,
    },
  });

  redirect('/login?registered=true');
}
```

## Database Schema (Prisma)

```prisma
model User {
  id            String    @id @default(cuid())
  name          String?
  email         String    @unique
  emailVerified DateTime?
  image         String?
  password      String?
  role          String    @default("user")
  accounts      Account[]
  sessions      Session[]
  createdAt     DateTime  @default(now())
  updatedAt     DateTime  @updatedAt
}

model Account {
  id                String  @id @default(cuid())
  userId            String
  type              String
  provider          String
  providerAccountId String
  refresh_token     String?
  access_token      String?
  expires_at        Int?
  token_type        String?
  scope             String?
  id_token          String?
  session_state     String?
  user              User    @relation(fields: [userId], references: [id], onDelete: Cascade)

  @@unique([provider, providerAccountId])
}

model Session {
  id           String   @id @default(cuid())
  sessionToken String   @unique
  userId       String
  expires      DateTime
  user         User     @relation(fields: [userId], references: [id], onDelete: Cascade)
}

model VerificationToken {
  identifier String
  token      String   @unique
  expires    DateTime

  @@unique([identifier, token])
}
```

## Getting Started

```bash
# Clone the example
npx create-next-app --example f5-auth-app my-auth-app

# Install dependencies
npm install

# Set up database
npx prisma db push

# Run development server
npm run dev
```

## Environment Variables

```env
DATABASE_URL="postgresql://..."
NEXTAUTH_SECRET="your-secret-key"
NEXTAUTH_URL="http://localhost:3000"

# OAuth Providers (optional)
GOOGLE_CLIENT_ID="..."
GOOGLE_CLIENT_SECRET="..."
GITHUB_CLIENT_ID="..."
GITHUB_CLIENT_SECRET="..."
```
