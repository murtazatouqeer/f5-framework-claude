# Styled Components

## Overview

CSS-in-JS library using tagged template literals for component styling.

## Basic Usage

```tsx
import styled from 'styled-components';

const Button = styled.button`
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  font-weight: 500;
  background-color: #3b82f6;
  color: white;
  border: none;
  cursor: pointer;
  transition: background-color 0.2s;

  &:hover {
    background-color: #2563eb;
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

// Usage
<Button>Click me</Button>
<Button disabled>Disabled</Button>
```

## Props-Based Styling

```tsx
interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  fullWidth?: boolean;
}

const Button = styled.button<ButtonProps>`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 0.375rem;
  font-weight: 500;
  transition: all 0.2s;

  /* Size variants */
  padding: ${({ size }) => {
    switch (size) {
      case 'sm': return '0.25rem 0.5rem';
      case 'lg': return '0.75rem 1.5rem';
      default: return '0.5rem 1rem';
    }
  }};

  font-size: ${({ size }) => {
    switch (size) {
      case 'sm': return '0.875rem';
      case 'lg': return '1.125rem';
      default: return '1rem';
    }
  }};

  /* Color variants */
  ${({ variant }) => {
    switch (variant) {
      case 'secondary':
        return `
          background-color: #f3f4f6;
          color: #1f2937;
          border: none;
          &:hover { background-color: #e5e7eb; }
        `;
      case 'outline':
        return `
          background-color: transparent;
          color: #3b82f6;
          border: 1px solid #3b82f6;
          &:hover { background-color: #eff6ff; }
        `;
      default:
        return `
          background-color: #3b82f6;
          color: white;
          border: none;
          &:hover { background-color: #2563eb; }
        `;
    }
  }}

  /* Full width */
  width: ${({ fullWidth }) => fullWidth ? '100%' : 'auto'};
`;

// Usage
<Button variant="primary" size="lg">Large Primary</Button>
<Button variant="outline" fullWidth>Full Width Outline</Button>
```

## Extending Styles

```tsx
const Button = styled.button`
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  font-weight: 500;
`;

const PrimaryButton = styled(Button)`
  background-color: #3b82f6;
  color: white;

  &:hover {
    background-color: #2563eb;
  }
`;

const IconButton = styled(Button)`
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;

  svg {
    width: 1rem;
    height: 1rem;
  }
`;
```

## Theming

```tsx
// theme.ts
export const lightTheme = {
  colors: {
    primary: '#3b82f6',
    primaryDark: '#2563eb',
    background: '#ffffff',
    text: '#111827',
    textMuted: '#6b7280',
    border: '#e5e7eb',
  },
  spacing: {
    xs: '0.25rem',
    sm: '0.5rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem',
  },
  borderRadius: {
    sm: '0.25rem',
    md: '0.375rem',
    lg: '0.5rem',
    full: '9999px',
  },
};

export const darkTheme = {
  ...lightTheme,
  colors: {
    ...lightTheme.colors,
    background: '#1f2937',
    text: '#f9fafb',
    textMuted: '#9ca3af',
    border: '#374151',
  },
};

export type Theme = typeof lightTheme;

// styled.d.ts
import 'styled-components';
import { Theme } from './theme';

declare module 'styled-components' {
  export interface DefaultTheme extends Theme {}
}
```

```tsx
// App.tsx
import { ThemeProvider } from 'styled-components';
import { lightTheme, darkTheme } from './theme';

function App() {
  const [isDark, setIsDark] = useState(false);

  return (
    <ThemeProvider theme={isDark ? darkTheme : lightTheme}>
      <GlobalStyles />
      <AppContent />
    </ThemeProvider>
  );
}

// Using theme in components
const Card = styled.div`
  background-color: ${({ theme }) => theme.colors.background};
  color: ${({ theme }) => theme.colors.text};
  padding: ${({ theme }) => theme.spacing.md};
  border-radius: ${({ theme }) => theme.borderRadius.md};
  border: 1px solid ${({ theme }) => theme.colors.border};
`;
```

## Global Styles

```tsx
import { createGlobalStyle } from 'styled-components';

const GlobalStyles = createGlobalStyle`
  *,
  *::before,
  *::after {
    box-sizing: border-box;
  }

  body {
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background-color: ${({ theme }) => theme.colors.background};
    color: ${({ theme }) => theme.colors.text};
  }

  a {
    color: ${({ theme }) => theme.colors.primary};
    text-decoration: none;

    &:hover {
      text-decoration: underline;
    }
  }
`;

// App.tsx
function App() {
  return (
    <ThemeProvider theme={theme}>
      <GlobalStyles />
      <Router />
    </ThemeProvider>
  );
}
```

## Animations

```tsx
import styled, { keyframes } from 'styled-components';

const fadeIn = keyframes`
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
`;

const spin = keyframes`
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
`;

const FadeInDiv = styled.div`
  animation: ${fadeIn} 0.3s ease-out;
`;

const Spinner = styled.div`
  width: 24px;
  height: 24px;
  border: 2px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: ${spin} 1s linear infinite;
`;
```

## Responsive Styles

```tsx
const breakpoints = {
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
};

const media = {
  sm: `@media (min-width: ${breakpoints.sm})`,
  md: `@media (min-width: ${breakpoints.md})`,
  lg: `@media (min-width: ${breakpoints.lg})`,
  xl: `@media (min-width: ${breakpoints.xl})`,
};

const Grid = styled.div`
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;

  ${media.sm} {
    grid-template-columns: repeat(2, 1fr);
  }

  ${media.lg} {
    grid-template-columns: repeat(3, 1fr);
  }
`;
```

## as Prop (Polymorphic)

```tsx
const Text = styled.p`
  color: ${({ theme }) => theme.colors.text};
`;

// Render as different elements
<Text>Paragraph</Text>
<Text as="span">Span</Text>
<Text as="h1">Heading</Text>
<Text as="label">Label</Text>
```

## Best Practices

1. **Use TypeScript** - Define prop interfaces for type safety
2. **Create theme** - Centralize design tokens
3. **Extract utils** - Create helper functions for common patterns
4. **Use css helper** - For conditional style blocks
5. **Colocate styles** - Keep styled components near usage
6. **Avoid deep nesting** - Keep selectors simple
