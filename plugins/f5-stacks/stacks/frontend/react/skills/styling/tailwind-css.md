# Tailwind CSS in React

## Overview

Utility-first CSS framework for rapid UI development in React applications.

## Setup

```bash
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

```js
// tailwind.config.js
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        },
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
```

## Class Variance Authority (CVA)

```tsx
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const buttonVariants = cva(
  // Base styles
  'inline-flex items-center justify-center rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default: 'bg-primary-600 text-white hover:bg-primary-700',
        secondary: 'bg-gray-100 text-gray-900 hover:bg-gray-200',
        outline: 'border border-gray-300 bg-transparent hover:bg-gray-100',
        ghost: 'hover:bg-gray-100',
        destructive: 'bg-red-600 text-white hover:bg-red-700',
        link: 'text-primary-600 underline-offset-4 hover:underline',
      },
      size: {
        sm: 'h-8 px-3 text-sm',
        md: 'h-10 px-4 text-sm',
        lg: 'h-12 px-6 text-base',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'md',
    },
  }
);

interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  isLoading?: boolean;
}

export function Button({
  className,
  variant,
  size,
  isLoading,
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(buttonVariants({ variant, size }), className)}
      disabled={isLoading}
      {...props}
    >
      {isLoading && <Spinner className="mr-2 h-4 w-4" />}
      {children}
    </button>
  );
}
```

## Utility Function (cn)

```tsx
// lib/utils.ts
import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Usage
<div className={cn(
  'px-4 py-2 rounded',
  isActive && 'bg-blue-500 text-white',
  isDisabled && 'opacity-50 cursor-not-allowed',
  className
)} />
```

## Responsive Design

```tsx
function ResponsiveCard() {
  return (
    <div
      className={cn(
        // Mobile first
        'p-4 rounded-lg',
        // Small screens
        'sm:p-6',
        // Medium screens
        'md:flex md:gap-6',
        // Large screens
        'lg:p-8 lg:gap-8',
        // Extra large
        'xl:max-w-6xl xl:mx-auto'
      )}
    >
      <div className="md:w-1/3">
        <img
          className="w-full h-48 object-cover rounded md:h-auto"
          src={image}
          alt=""
        />
      </div>
      <div className="mt-4 md:mt-0 md:w-2/3">
        <h2 className="text-xl font-bold md:text-2xl lg:text-3xl">{title}</h2>
        <p className="mt-2 text-gray-600 text-sm md:text-base">{description}</p>
      </div>
    </div>
  );
}
```

## Dark Mode

```js
// tailwind.config.js
export default {
  darkMode: 'class', // or 'media'
  // ...
};
```

```tsx
// Toggle dark mode
function DarkModeToggle() {
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    document.documentElement.classList.toggle('dark', isDark);
  }, [isDark]);

  return (
    <button onClick={() => setIsDark(!isDark)}>
      {isDark ? <SunIcon /> : <MoonIcon />}
    </button>
  );
}

// Using dark mode classes
<div className="bg-white dark:bg-gray-900">
  <h1 className="text-gray-900 dark:text-white">Title</h1>
  <p className="text-gray-600 dark:text-gray-300">Description</p>
</div>
```

## Animation

```tsx
// Tailwind animations
<div className="animate-spin" />
<div className="animate-pulse" />
<div className="animate-bounce" />

// Custom animation
// tailwind.config.js
export default {
  theme: {
    extend: {
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
};

// Usage
<div className="animate-fade-in" />
```

## Layout Patterns

```tsx
// Flexbox
<div className="flex items-center justify-between gap-4">
  <div className="flex-1">{/* Takes remaining space */}</div>
  <div className="flex-shrink-0">{/* Fixed size */}</div>
</div>

// Grid
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
  {items.map(item => <Card key={item.id} item={item} />)}
</div>

// Container
<div className="container mx-auto px-4 sm:px-6 lg:px-8">
  {/* Centered content */}
</div>

// Sticky header
<header className="sticky top-0 z-50 bg-white/80 backdrop-blur-sm border-b">
  <nav className="container mx-auto px-4 h-16 flex items-center">
    {/* Navigation */}
  </nav>
</header>
```

## Form Styling

```tsx
function StyledForm() {
  return (
    <form className="space-y-6">
      <div className="space-y-2">
        <label className="text-sm font-medium text-gray-700">
          Email
        </label>
        <input
          type="email"
          className={cn(
            'w-full px-3 py-2 border rounded-md',
            'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
            'placeholder:text-gray-400',
            error && 'border-red-500 focus:ring-red-500'
          )}
          placeholder="Enter your email"
        />
        {error && <p className="text-sm text-red-500">{error}</p>}
      </div>

      <button
        type="submit"
        className={cn(
          'w-full py-2 px-4 rounded-md font-medium',
          'bg-primary-600 text-white',
          'hover:bg-primary-700',
          'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
          'disabled:opacity-50 disabled:cursor-not-allowed'
        )}
      >
        Submit
      </button>
    </form>
  );
}
```

## Best Practices

1. **Use CVA** - Manage component variants systematically
2. **Use cn utility** - Merge classes safely with tailwind-merge
3. **Mobile first** - Start with mobile styles, add breakpoints
4. **Extract components** - Reusable components over repeated classes
5. **Use design tokens** - Extend theme for consistent design system
6. **Purge unused CSS** - Configure content paths correctly
