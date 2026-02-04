# CSS Modules

## Overview

Locally scoped CSS that prevents class name collisions and provides modularity.

## Basic Usage

```css
/* Button.module.css */
.button {
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  font-weight: 500;
  transition: all 0.2s;
}

.primary {
  background-color: #3b82f6;
  color: white;
}

.primary:hover {
  background-color: #2563eb;
}

.secondary {
  background-color: #f3f4f6;
  color: #1f2937;
}

.secondary:hover {
  background-color: #e5e7eb;
}

.small {
  padding: 0.25rem 0.5rem;
  font-size: 0.875rem;
}

.large {
  padding: 0.75rem 1.5rem;
  font-size: 1.125rem;
}
```

```tsx
// Button.tsx
import styles from './Button.module.css';
import { cn } from '@/lib/utils';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary';
  size?: 'small' | 'medium' | 'large';
}

export function Button({
  variant = 'primary',
  size = 'medium',
  className,
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        styles.button,
        styles[variant],
        size !== 'medium' && styles[size],
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}
```

## Composition

```css
/* Card.module.css */
.card {
  background: white;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.header {
  padding: 1rem;
  border-bottom: 1px solid #e5e7eb;
}

.title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #111827;
}

.content {
  padding: 1rem;
}

.footer {
  padding: 1rem;
  border-top: 1px solid #e5e7eb;
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}
```

```tsx
// Card.tsx
import styles from './Card.module.css';

interface CardProps {
  title?: string;
  footer?: React.ReactNode;
  children: React.ReactNode;
}

export function Card({ title, footer, children }: CardProps) {
  return (
    <div className={styles.card}>
      {title && (
        <div className={styles.header}>
          <h3 className={styles.title}>{title}</h3>
        </div>
      )}
      <div className={styles.content}>{children}</div>
      {footer && <div className={styles.footer}>{footer}</div>}
    </div>
  );
}
```

## Global Styles with CSS Modules

```css
/* globals.module.css */
:global(.container) {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
}

/* Local + Global */
.wrapper :global(.third-party-class) {
  color: red;
}
```

## CSS Variables Integration

```css
/* variables.css */
:root {
  --color-primary: #3b82f6;
  --color-primary-dark: #2563eb;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;
  --radius-md: 0.375rem;
}

/* Button.module.css */
.button {
  background-color: var(--color-primary);
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-md);
}

.button:hover {
  background-color: var(--color-primary-dark);
}
```

## Theming with CSS Variables

```css
/* themes.css */
:root {
  --bg-primary: #ffffff;
  --text-primary: #111827;
  --border-color: #e5e7eb;
}

:root.dark {
  --bg-primary: #1f2937;
  --text-primary: #f9fafb;
  --border-color: #374151;
}
```

```tsx
// Theme toggle
function useTheme() {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
  }, [theme]);

  return { theme, setTheme };
}
```

## Responsive Styles

```css
/* Responsive.module.css */
.grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
}

@media (min-width: 640px) {
  .grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1024px) {
  .grid {
    grid-template-columns: repeat(3, 1fr);
    gap: 1.5rem;
  }
}
```

## Animation

```css
/* Animation.module.css */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.fadeIn {
  animation: fadeIn 0.3s ease-out;
}

.spin {
  animation: spin 1s linear infinite;
}

/* Transition */
.button {
  transition: all 0.2s ease-in-out;
}

.button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
```

## TypeScript Support

```tsx
// types/css-modules.d.ts
declare module '*.module.css' {
  const classes: { readonly [key: string]: string };
  export default classes;
}

declare module '*.module.scss' {
  const classes: { readonly [key: string]: string };
  export default classes;
}
```

## Best Practices

1. **One module per component** - Colocate styles with components
2. **Use composition** - Compose classes with cn/clsx utility
3. **Keep it flat** - Avoid deep nesting, use BEM-like naming
4. **Use CSS variables** - Share values across modules
5. **Scope carefully** - Use :global sparingly
6. **Name clearly** - Use descriptive class names within module scope
