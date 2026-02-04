---
name: rn-styling
description: Styling approaches in React Native
applies_to: react-native
---

# Styling in React Native

## StyleSheet API (Default)

### Basic Usage

```typescript
import { View, Text, StyleSheet } from 'react-native';

function Component() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Hello</Text>
      <Text style={[styles.text, styles.bold]}>World</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
    backgroundColor: '#fff',
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    marginBottom: 8,
  },
  text: {
    fontSize: 16,
    color: '#333',
  },
  bold: {
    fontWeight: '600',
  },
});
```

### Dynamic Styles

```typescript
interface Props {
  isActive: boolean;
  size: 'small' | 'medium' | 'large';
}

function DynamicComponent({ isActive, size }: Props) {
  return (
    <View
      style={[
        styles.base,
        isActive && styles.active,
        styles[size], // size must match key in styles
      ]}
    />
  );
}

const styles = StyleSheet.create({
  base: {
    borderRadius: 8,
    backgroundColor: '#e0e0e0',
  },
  active: {
    backgroundColor: '#007AFF',
  },
  small: {
    width: 32,
    height: 32,
  },
  medium: {
    width: 48,
    height: 48,
  },
  large: {
    width: 64,
    height: 64,
  },
});
```

### Style Composition

```typescript
// Merge multiple style objects
const mergedStyle = StyleSheet.compose(styles.base, styles.override);

// Flatten nested styles
const flattenedStyle = StyleSheet.flatten([styles.base, { color: 'red' }]);

// Get absolute value for hairline width
const borderWidth = StyleSheet.hairlineWidth;
```

## NativeWind (Tailwind CSS)

### Setup

```bash
npm install nativewind
npm install --save-dev tailwindcss@3.3.2
npx tailwindcss init
```

```javascript
// tailwind.config.js
module.exports = {
  content: [
    "./App.{js,jsx,ts,tsx}",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  presets: [require("nativewind/preset")],
  theme: {
    extend: {},
  },
  plugins: [],
};
```

```javascript
// babel.config.js
module.exports = function (api) {
  api.cache(true);
  return {
    presets: ['babel-preset-expo'],
    plugins: ['nativewind/babel'],
  };
};
```

### Usage

```typescript
import { View, Text, Pressable } from 'react-native';

function TailwindComponent() {
  return (
    <View className="flex-1 items-center justify-center bg-white p-4">
      <Text className="text-2xl font-bold text-gray-900 mb-4">
        Hello NativeWind
      </Text>
      <Pressable className="bg-blue-500 px-6 py-3 rounded-lg active:opacity-80">
        <Text className="text-white font-semibold">Press Me</Text>
      </Pressable>
    </View>
  );
}
```

### Conditional Classes

```typescript
import { View, Text } from 'react-native';
import clsx from 'clsx';

interface Props {
  variant: 'primary' | 'secondary';
  isDisabled?: boolean;
}

function Button({ variant, isDisabled }: Props) {
  return (
    <View
      className={clsx(
        'px-4 py-2 rounded-lg',
        {
          'bg-blue-500': variant === 'primary',
          'bg-gray-200': variant === 'secondary',
          'opacity-50': isDisabled,
        }
      )}
    >
      <Text className={clsx(
        'font-medium',
        variant === 'primary' ? 'text-white' : 'text-gray-900'
      )}>
        Button
      </Text>
    </View>
  );
}
```

## Theme System

### Creating a Theme

```typescript
// src/theme/index.ts
export const theme = {
  colors: {
    primary: '#007AFF',
    secondary: '#5856D6',
    success: '#34C759',
    warning: '#FF9500',
    error: '#FF3B30',

    background: '#FFFFFF',
    surface: '#F2F2F7',
    text: {
      primary: '#000000',
      secondary: '#3C3C43',
      tertiary: '#8E8E93',
    },
    border: '#C6C6C8',
  },

  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
    xxl: 48,
  },

  borderRadius: {
    sm: 4,
    md: 8,
    lg: 12,
    xl: 16,
    full: 9999,
  },

  typography: {
    heading1: {
      fontSize: 34,
      fontWeight: '700' as const,
      lineHeight: 41,
    },
    heading2: {
      fontSize: 28,
      fontWeight: '700' as const,
      lineHeight: 34,
    },
    heading3: {
      fontSize: 22,
      fontWeight: '600' as const,
      lineHeight: 28,
    },
    body: {
      fontSize: 17,
      fontWeight: '400' as const,
      lineHeight: 22,
    },
    caption: {
      fontSize: 13,
      fontWeight: '400' as const,
      lineHeight: 18,
    },
  },

  shadow: {
    sm: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 1 },
      shadowOpacity: 0.1,
      shadowRadius: 2,
      elevation: 2,
    },
    md: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.15,
      shadowRadius: 4,
      elevation: 4,
    },
    lg: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.2,
      shadowRadius: 8,
      elevation: 8,
    },
  },
} as const;

export type Theme = typeof theme;
```

### Theme Context

```typescript
// src/theme/ThemeContext.tsx
import { createContext, useContext, useState, useMemo } from 'react';
import { useColorScheme } from 'react-native';
import { theme as lightTheme } from './index';

const darkTheme = {
  ...lightTheme,
  colors: {
    ...lightTheme.colors,
    background: '#000000',
    surface: '#1C1C1E',
    text: {
      primary: '#FFFFFF',
      secondary: '#EBEBF5',
      tertiary: '#8E8E93',
    },
    border: '#38383A',
  },
};

type ThemeMode = 'light' | 'dark' | 'system';

interface ThemeContextType {
  theme: typeof lightTheme;
  mode: ThemeMode;
  setMode: (mode: ThemeMode) => void;
  isDark: boolean;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const systemColorScheme = useColorScheme();
  const [mode, setMode] = useState<ThemeMode>('system');

  const { theme, isDark } = useMemo(() => {
    const isDark =
      mode === 'dark' || (mode === 'system' && systemColorScheme === 'dark');
    return {
      theme: isDark ? darkTheme : lightTheme,
      isDark,
    };
  }, [mode, systemColorScheme]);

  return (
    <ThemeContext.Provider value={{ theme, mode, setMode, isDark }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
}
```

### Using Theme

```typescript
import { View, Text, StyleSheet } from 'react-native';
import { useTheme } from '@/theme/ThemeContext';

function ThemedComponent() {
  const { theme, isDark } = useTheme();

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <Text style={[styles.title, { color: theme.colors.text.primary }]}>
        {isDark ? 'Dark Mode' : 'Light Mode'}
      </Text>
    </View>
  );
}

// Or create themed styles
function createStyles(theme: Theme) {
  return StyleSheet.create({
    container: {
      flex: 1,
      padding: theme.spacing.md,
      backgroundColor: theme.colors.background,
    },
    title: {
      ...theme.typography.heading1,
      color: theme.colors.text.primary,
    },
  });
}
```

## Responsive Design

### Using Dimensions

```typescript
import { Dimensions, StyleSheet } from 'react-native';

const { width, height } = Dimensions.get('window');

const isSmallDevice = width < 375;
const isLargeDevice = width >= 768;

const styles = StyleSheet.create({
  container: {
    padding: isSmallDevice ? 12 : 16,
    maxWidth: isLargeDevice ? 600 : '100%',
  },
});
```

### Using useWindowDimensions

```typescript
import { useWindowDimensions, View, StyleSheet } from 'react-native';

function ResponsiveGrid() {
  const { width } = useWindowDimensions();
  const numColumns = width >= 768 ? 3 : width >= 375 ? 2 : 1;

  return (
    <View style={[styles.grid, { flexDirection: numColumns > 1 ? 'row' : 'column' }]}>
      {/* Grid items */}
    </View>
  );
}
```

### Responsive Hook

```typescript
// src/hooks/useResponsive.ts
import { useWindowDimensions } from 'react-native';

type Breakpoint = 'sm' | 'md' | 'lg' | 'xl';

const BREAKPOINTS = {
  sm: 375,
  md: 768,
  lg: 1024,
  xl: 1280,
};

export function useResponsive() {
  const { width, height } = useWindowDimensions();

  const breakpoint: Breakpoint =
    width >= BREAKPOINTS.xl ? 'xl' :
    width >= BREAKPOINTS.lg ? 'lg' :
    width >= BREAKPOINTS.md ? 'md' : 'sm';

  return {
    width,
    height,
    breakpoint,
    isSmall: breakpoint === 'sm',
    isMedium: breakpoint === 'md',
    isLarge: breakpoint === 'lg' || breakpoint === 'xl',
    isPortrait: height > width,
    isLandscape: width > height,
  };
}
```

## Best Practices

1. **Use StyleSheet.create**: Optimizes styles at creation time
2. **Avoid Inline Styles**: Except for dynamic values
3. **Theme Consistency**: Use theme tokens, not hardcoded values
4. **Responsive Design**: Test on multiple screen sizes
5. **Platform Styles**: Handle iOS/Android differences
6. **Type Safety**: Use TypeScript for style props
7. **Style Organization**: Colocate styles with components
8. **Reusable Styles**: Extract common patterns to shared styles
