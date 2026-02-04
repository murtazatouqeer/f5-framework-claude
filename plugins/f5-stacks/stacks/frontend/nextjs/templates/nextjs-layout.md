---
name: nextjs-layout
description: Next.js App Router layout template
applies_to: nextjs
variables:
  - name: LAYOUT_NAME
    description: Name of the layout section
  - name: HAS_SIDEBAR
    description: Whether layout includes sidebar
  - name: HAS_HEADER
    description: Whether layout includes header
---

# Next.js Layout Template

## Root Layout

```tsx
// app/layout.tsx
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { ThemeProvider } from '@/components/theme-provider';
import { Toaster } from '@/components/ui/toaster';
import './globals.css';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-sans',
});

export const metadata: Metadata = {
  title: {
    default: 'My App',
    template: '%s | My App',
  },
  description: 'My application description',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} font-sans antialiased`}>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          {children}
          <Toaster />
        </ThemeProvider>
      </body>
    </html>
  );
}
```

## Dashboard Layout with Sidebar

```tsx
// app/(dashboard)/layout.tsx
import { redirect } from 'next/navigation';
import { auth } from '@/lib/auth';
import { Sidebar } from './_components/sidebar';
import { Header } from './_components/header';

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await auth();

  if (!session?.user) {
    redirect('/login');
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar user={session.user} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header user={session.user} />
        <main className="flex-1 overflow-auto p-6 bg-muted/30">
          {children}
        </main>
      </div>
    </div>
  );
}
```

## Marketing Layout

```tsx
// app/(marketing)/layout.tsx
import { Header } from '@/components/marketing/header';
import { Footer } from '@/components/marketing/footer';

export default function MarketingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1">{children}</main>
      <Footer />
    </div>
  );
}
```

## Auth Layout

```tsx
// app/(auth)/layout.tsx
import Image from 'next/image';

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen grid lg:grid-cols-2">
      {/* Left side - Form */}
      <div className="flex items-center justify-center p-8">
        <div className="w-full max-w-md space-y-8">
          {children}
        </div>
      </div>

      {/* Right side - Image */}
      <div className="hidden lg:block relative bg-muted">
        <Image
          src="/auth-background.jpg"
          alt="Authentication"
          fill
          className="object-cover"
          priority
        />
        <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
          <blockquote className="text-white text-center max-w-md px-8">
            <p className="text-2xl font-medium mb-4">
              "This app has transformed the way we work."
            </p>
            <footer className="text-sm opacity-80">
              Sofia Davis, CEO at Company
            </footer>
          </blockquote>
        </div>
      </div>
    </div>
  );
}
```

## Section Layout with Tabs

```tsx
// app/settings/layout.tsx
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import Link from 'next/link';

const tabs = [
  { value: 'profile', label: 'Profile', href: '/settings' },
  { value: 'account', label: 'Account', href: '/settings/account' },
  { value: 'billing', label: 'Billing', href: '/settings/billing' },
  { value: 'notifications', label: 'Notifications', href: '/settings/notifications' },
];

export default function SettingsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Settings</h1>
        <p className="text-muted-foreground">
          Manage your account settings and preferences.
        </p>
      </div>

      <nav className="border-b">
        <div className="flex space-x-8">
          {tabs.map((tab) => (
            <Link
              key={tab.value}
              href={tab.href}
              className="border-b-2 border-transparent pb-4 text-sm font-medium hover:border-primary hover:text-primary transition-colors"
            >
              {tab.label}
            </Link>
          ))}
        </div>
      </nav>

      <div>{children}</div>
    </div>
  );
}
```

## Nested Layout with Parallel Routes

```tsx
// app/@modal/(.)photos/[id]/page.tsx
import { Modal } from '@/components/ui/modal';
import { PhotoView } from '@/components/photos/photo-view';

export default function PhotoModal({
  params,
}: {
  params: { id: string };
}) {
  return (
    <Modal>
      <PhotoView id={params.id} />
    </Modal>
  );
}

// app/layout.tsx (with parallel routes)
export default function RootLayout({
  children,
  modal,
}: {
  children: React.ReactNode;
  modal: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        {children}
        {modal}
      </body>
    </html>
  );
}
```

## Sidebar Component

```tsx
// app/(dashboard)/_components/sidebar.tsx
'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import {
  Home,
  Users,
  Settings,
  BarChart,
  FileText,
} from 'lucide-react';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: Home },
  { name: 'Users', href: '/dashboard/users', icon: Users },
  { name: 'Analytics', href: '/dashboard/analytics', icon: BarChart },
  { name: 'Reports', href: '/dashboard/reports', icon: FileText },
  { name: 'Settings', href: '/dashboard/settings', icon: Settings },
];

interface SidebarProps {
  user: { name: string; email: string; image?: string };
}

export function Sidebar({ user }: SidebarProps) {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-card border-r flex flex-col">
      {/* Logo */}
      <div className="h-16 flex items-center px-6 border-b">
        <Link href="/dashboard" className="text-xl font-bold">
          MyApp
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        {navigation.map((item) => {
          const isActive = pathname === item.href ||
            pathname.startsWith(`${item.href}/`);

          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:bg-muted hover:text-foreground'
              )}
            >
              <item.icon className="h-5 w-5" />
              {item.name}
            </Link>
          );
        })}
      </nav>

      {/* User */}
      <div className="p-4 border-t">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-full bg-muted flex items-center justify-center">
            {user.name[0]}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{user.name}</p>
            <p className="text-xs text-muted-foreground truncate">
              {user.email}
            </p>
          </div>
        </div>
      </div>
    </aside>
  );
}
```

## Usage

```bash
f5 generate layout Dashboard --sidebar --header
f5 generate layout Auth --centered
f5 generate layout Marketing --header --footer
```
