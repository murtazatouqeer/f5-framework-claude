# React Layout Template

Production-ready layout templates for React applications with TypeScript.

## Main Layout Template

```tsx
// components/layouts/MainLayout.tsx
import { type FC, type ReactNode, useState } from 'react';
import { Outlet } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { Footer } from './Footer';

interface MainLayoutProps {
  children?: ReactNode;
}

export const MainLayout: FC<MainLayoutProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <div className="min-h-screen bg-background">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <Sidebar
        isOpen={sidebarOpen}
        isCollapsed={sidebarCollapsed}
        onClose={() => setSidebarOpen(false)}
        onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
      />

      {/* Main content area */}
      <div
        className={cn(
          'flex flex-col transition-all duration-300',
          sidebarCollapsed ? 'lg:pl-16' : 'lg:pl-64'
        )}
      >
        {/* Header */}
        <Header onMenuClick={() => setSidebarOpen(true)} />

        {/* Page content */}
        <main className="flex-1">
          {children || <Outlet />}
        </main>

        {/* Footer */}
        <Footer />
      </div>
    </div>
  );
};
```

## Sidebar Component

```tsx
// components/layouts/Sidebar.tsx
import { type FC } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  Home,
  Users,
  Settings,
  ShoppingCart,
  BarChart,
  FileText,
  ChevronLeft,
  ChevronRight,
  X,
  type LucideIcon,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/Button';
import { ScrollArea } from '@/components/ui/ScrollArea';
import { Tooltip } from '@/components/ui/Tooltip';

interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
  badge?: string | number;
}

interface NavGroup {
  title?: string;
  items: NavItem[];
}

const navigation: NavGroup[] = [
  {
    items: [
      { label: 'Dashboard', href: '/', icon: Home },
      { label: 'Analytics', href: '/analytics', icon: BarChart },
    ],
  },
  {
    title: 'Management',
    items: [
      { label: 'Users', href: '/users', icon: Users, badge: 12 },
      { label: 'Orders', href: '/orders', icon: ShoppingCart },
      { label: 'Reports', href: '/reports', icon: FileText },
    ],
  },
  {
    title: 'Settings',
    items: [
      { label: 'Settings', href: '/settings', icon: Settings },
    ],
  },
];

interface SidebarProps {
  isOpen: boolean;
  isCollapsed: boolean;
  onClose: () => void;
  onToggleCollapse: () => void;
}

export const Sidebar: FC<SidebarProps> = ({
  isOpen,
  isCollapsed,
  onClose,
  onToggleCollapse,
}) => {
  const location = useLocation();

  return (
    <>
      {/* Mobile sidebar */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 w-64 bg-card border-r transform transition-transform duration-300 lg:hidden',
          isOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex items-center justify-between h-16 px-4 border-b">
          <Link to="/" className="flex items-center gap-2 font-bold text-lg">
            <span className="text-primary">App</span>
          </Link>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-5 w-5" />
          </Button>
        </div>
        <SidebarContent
          navigation={navigation}
          currentPath={location.pathname}
          isCollapsed={false}
        />
      </aside>

      {/* Desktop sidebar */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-30 hidden lg:flex flex-col bg-card border-r transition-all duration-300',
          isCollapsed ? 'w-16' : 'w-64'
        )}
      >
        {/* Logo */}
        <div className="flex items-center h-16 px-4 border-b">
          {!isCollapsed && (
            <Link to="/" className="flex items-center gap-2 font-bold text-lg">
              <span className="text-primary">App</span>
            </Link>
          )}
          <Button
            variant="ghost"
            size="icon"
            className={cn('ml-auto', isCollapsed && 'mx-auto')}
            onClick={onToggleCollapse}
          >
            {isCollapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <ChevronLeft className="h-4 w-4" />
            )}
          </Button>
        </div>

        <SidebarContent
          navigation={navigation}
          currentPath={location.pathname}
          isCollapsed={isCollapsed}
        />
      </aside>
    </>
  );
};

interface SidebarContentProps {
  navigation: NavGroup[];
  currentPath: string;
  isCollapsed: boolean;
}

const SidebarContent: FC<SidebarContentProps> = ({
  navigation,
  currentPath,
  isCollapsed,
}) => {
  return (
    <ScrollArea className="flex-1 py-4">
      <nav className="space-y-6 px-2">
        {navigation.map((group, groupIndex) => (
          <div key={groupIndex}>
            {group.title && !isCollapsed && (
              <h3 className="px-3 mb-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                {group.title}
              </h3>
            )}
            <ul className="space-y-1">
              {group.items.map((item) => {
                const isActive = currentPath === item.href;
                const Icon = item.icon;

                const linkContent = (
                  <Link
                    to={item.href}
                    className={cn(
                      'flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                      isActive
                        ? 'bg-primary text-primary-foreground'
                        : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground',
                      isCollapsed && 'justify-center px-2'
                    )}
                  >
                    <Icon className="h-5 w-5 shrink-0" />
                    {!isCollapsed && (
                      <>
                        <span className="flex-1">{item.label}</span>
                        {item.badge && (
                          <span className="px-2 py-0.5 text-xs rounded-full bg-primary/10 text-primary">
                            {item.badge}
                          </span>
                        )}
                      </>
                    )}
                  </Link>
                );

                return (
                  <li key={item.href}>
                    {isCollapsed ? (
                      <Tooltip content={item.label} side="right">
                        {linkContent}
                      </Tooltip>
                    ) : (
                      linkContent
                    )}
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>
    </ScrollArea>
  );
};
```

## Header Component

```tsx
// components/layouts/Header.tsx
import { type FC } from 'react';
import { Link } from 'react-router-dom';
import { Menu, Bell, Search, User } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/DropdownMenu';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/Avatar';
import { useAuth } from '@/contexts/AuthContext';
import { ThemeToggle } from '@/components/ThemeToggle';

interface HeaderProps {
  onMenuClick: () => void;
  className?: string;
}

export const Header: FC<HeaderProps> = ({ onMenuClick, className }) => {
  const { user, logout } = useAuth();

  return (
    <header
      className={cn(
        'sticky top-0 z-20 flex items-center h-16 px-4 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60',
        className
      )}
    >
      {/* Mobile menu button */}
      <Button
        variant="ghost"
        size="icon"
        className="lg:hidden mr-2"
        onClick={onMenuClick}
      >
        <Menu className="h-5 w-5" />
        <span className="sr-only">Toggle menu</span>
      </Button>

      {/* Search */}
      <div className="flex-1 max-w-md">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            type="search"
            placeholder="Search..."
            className="pl-9 w-full"
          />
        </div>
      </div>

      {/* Right side actions */}
      <div className="flex items-center gap-2 ml-4">
        <ThemeToggle />

        {/* Notifications */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="relative">
              <Bell className="h-5 w-5" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-destructive rounded-full" />
              <span className="sr-only">Notifications</span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-80">
            <DropdownMenuLabel>Notifications</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <div className="max-h-64 overflow-y-auto">
              <NotificationItem
                title="New order received"
                description="Order #12345 needs processing"
                time="5 min ago"
              />
              <NotificationItem
                title="System update"
                description="New features available"
                time="1 hour ago"
              />
            </div>
            <DropdownMenuSeparator />
            <DropdownMenuItem asChild>
              <Link to="/notifications" className="w-full text-center">
                View all notifications
              </Link>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>

        {/* User menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="relative h-8 w-8 rounded-full">
              <Avatar className="h-8 w-8">
                <AvatarImage src={user?.avatar} alt={user?.name} />
                <AvatarFallback>
                  {user?.name?.charAt(0).toUpperCase() || 'U'}
                </AvatarFallback>
              </Avatar>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel className="font-normal">
              <div className="flex flex-col space-y-1">
                <p className="text-sm font-medium">{user?.name}</p>
                <p className="text-xs text-muted-foreground">{user?.email}</p>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem asChild>
              <Link to="/profile">
                <User className="mr-2 h-4 w-4" />
                Profile
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem asChild>
              <Link to="/settings">Settings</Link>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={logout} className="text-destructive">
              Log out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
};

// Notification item component
interface NotificationItemProps {
  title: string;
  description: string;
  time: string;
}

const NotificationItem: FC<NotificationItemProps> = ({
  title,
  description,
  time,
}) => (
  <div className="px-4 py-3 hover:bg-accent cursor-pointer">
    <p className="text-sm font-medium">{title}</p>
    <p className="text-xs text-muted-foreground">{description}</p>
    <p className="text-xs text-muted-foreground mt-1">{time}</p>
  </div>
);
```

## Footer Component

```tsx
// components/layouts/Footer.tsx
import { type FC } from 'react';
import { Link } from 'react-router-dom';
import { cn } from '@/lib/utils';

interface FooterProps {
  className?: string;
}

export const Footer: FC<FooterProps> = ({ className }) => {
  const currentYear = new Date().getFullYear();

  return (
    <footer
      className={cn(
        'border-t bg-background',
        className
      )}
    >
      <div className="container py-6">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-sm text-muted-foreground">
            &copy; {currentYear} Company Name. All rights reserved.
          </p>
          <nav className="flex items-center gap-4">
            <Link
              to="/privacy"
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              Privacy Policy
            </Link>
            <Link
              to="/terms"
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              Terms of Service
            </Link>
            <Link
              to="/contact"
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              Contact
            </Link>
          </nav>
        </div>
      </div>
    </footer>
  );
};
```

## Auth Layout

```tsx
// components/layouts/AuthLayout.tsx
import { type FC, type ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { cn } from '@/lib/utils';

interface AuthLayoutProps {
  children: ReactNode;
  title: string;
  description?: string;
  showBackLink?: boolean;
}

export const AuthLayout: FC<AuthLayoutProps> = ({
  children,
  title,
  description,
  showBackLink = false,
}) => {
  return (
    <div className="min-h-screen flex">
      {/* Left side - Branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-primary relative">
        <div className="absolute inset-0 bg-gradient-to-br from-primary to-primary-foreground/10" />
        <div className="relative z-10 flex flex-col justify-between w-full p-12 text-primary-foreground">
          <Link to="/" className="flex items-center gap-2 text-2xl font-bold">
            <span>App</span>
          </Link>
          <div>
            <blockquote className="space-y-2">
              <p className="text-lg">
                "This platform has transformed how we manage our business.
                The intuitive interface and powerful features are unmatched."
              </p>
              <footer className="text-sm">
                <cite className="not-italic font-semibold">John Doe</cite>
                {' — '}
                <span className="opacity-80">CEO, Example Corp</span>
              </footer>
            </blockquote>
          </div>
        </div>
      </div>

      {/* Right side - Form */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-md space-y-8">
          {/* Mobile logo */}
          <div className="lg:hidden text-center">
            <Link to="/" className="inline-flex items-center gap-2 text-2xl font-bold">
              <span className="text-primary">App</span>
            </Link>
          </div>

          {/* Header */}
          <div className="text-center lg:text-left">
            {showBackLink && (
              <Link
                to="/"
                className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground mb-4"
              >
                ← Back to home
              </Link>
            )}
            <h1 className="text-2xl font-bold tracking-tight">{title}</h1>
            {description && (
              <p className="mt-2 text-muted-foreground">{description}</p>
            )}
          </div>

          {/* Form content */}
          {children}
        </div>
      </div>
    </div>
  );
};
```

## Dashboard Layout

```tsx
// components/layouts/DashboardLayout.tsx
import { type FC, type ReactNode, useState } from 'react';
import { Outlet } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { useMediaQuery } from '@/hooks/useMediaQuery';

interface DashboardLayoutProps {
  children?: ReactNode;
}

export const DashboardLayout: FC<DashboardLayoutProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const isDesktop = useMediaQuery('(min-width: 1024px)');

  // Auto-collapse sidebar on tablet
  const isMedium = useMediaQuery('(min-width: 768px) and (max-width: 1023px)');

  return (
    <div className="relative min-h-screen bg-muted/30">
      {/* Sidebar */}
      <Sidebar
        isOpen={sidebarOpen}
        isCollapsed={sidebarCollapsed || isMedium}
        onClose={() => setSidebarOpen(false)}
        onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
      />

      {/* Overlay for mobile */}
      {sidebarOpen && !isDesktop && (
        <div
          className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm"
          onClick={() => setSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Main content */}
      <div
        className={cn(
          'flex flex-col min-h-screen transition-all duration-300',
          isDesktop && (sidebarCollapsed ? 'lg:pl-16' : 'lg:pl-64'),
          isMedium && 'md:pl-16'
        )}
      >
        <Header onMenuClick={() => setSidebarOpen(true)} />
        <main className="flex-1 p-4 md:p-6 lg:p-8">
          {children || <Outlet />}
        </main>
      </div>
    </div>
  );
};
```

## Centered Layout

```tsx
// components/layouts/CenteredLayout.tsx
import { type FC, type ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface CenteredLayoutProps {
  children: ReactNode;
  className?: string;
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl';
}

const maxWidthClasses = {
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-lg',
  xl: 'max-w-xl',
  '2xl': 'max-w-2xl',
};

export const CenteredLayout: FC<CenteredLayoutProps> = ({
  children,
  className,
  maxWidth = 'md',
}) => {
  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-background">
      <div className={cn('w-full', maxWidthClasses[maxWidth], className)}>
        {children}
      </div>
    </div>
  );
};
```

## Two-Column Layout

```tsx
// components/layouts/TwoColumnLayout.tsx
import { type FC, type ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface TwoColumnLayoutProps {
  sidebar: ReactNode;
  main: ReactNode;
  sidebarPosition?: 'left' | 'right';
  sidebarWidth?: 'narrow' | 'medium' | 'wide';
  className?: string;
}

const sidebarWidthClasses = {
  narrow: 'md:w-64',
  medium: 'md:w-80',
  wide: 'md:w-96',
};

export const TwoColumnLayout: FC<TwoColumnLayoutProps> = ({
  sidebar,
  main,
  sidebarPosition = 'left',
  sidebarWidth = 'medium',
  className,
}) => {
  return (
    <div className={cn('flex flex-col md:flex-row gap-6', className)}>
      {sidebarPosition === 'left' && (
        <aside className={cn('shrink-0', sidebarWidthClasses[sidebarWidth])}>
          {sidebar}
        </aside>
      )}
      <main className="flex-1 min-w-0">{main}</main>
      {sidebarPosition === 'right' && (
        <aside className={cn('shrink-0', sidebarWidthClasses[sidebarWidth])}>
          {sidebar}
        </aside>
      )}
    </div>
  );
};
```

## Usage Examples

### Main App Layout
```tsx
// App.tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { MainLayout } from '@/components/layouts/MainLayout';
import { AuthLayout } from '@/components/layouts/AuthLayout';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Auth routes */}
        <Route path="/login" element={
          <AuthLayout title="Welcome back" description="Sign in to your account">
            <LoginForm />
          </AuthLayout>
        } />

        {/* App routes with sidebar */}
        <Route element={<MainLayout />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/users" element={<UsersPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
```

### Page with Two Columns
```tsx
// pages/Settings/SettingsPage.tsx
import { TwoColumnLayout } from '@/components/layouts/TwoColumnLayout';
import { SettingsNav } from './SettingsNav';
import { SettingsContent } from './SettingsContent';

export function SettingsPage() {
  return (
    <TwoColumnLayout
      sidebar={<SettingsNav />}
      main={<SettingsContent />}
      sidebarWidth="narrow"
    />
  );
}
```

## Best Practices

1. **Use composition** - Build layouts from smaller components
2. **Handle responsive** - Mobile-first with breakpoints
3. **Accessibility** - Proper ARIA landmarks and navigation
4. **Performance** - Lazy load heavy components
5. **Consistent spacing** - Use design tokens
6. **Flexible structure** - Support different content needs
7. **State management** - Sidebar collapse, mobile menu state
