---
name: rn-project-structure
description: React Native project structure and organization patterns
applies_to: react-native
---

# React Native Project Structure

## Expo Router Project Structure (Recommended)

```
my-app/
├── app/                           # File-based routing (Expo Router)
│   ├── (tabs)/                   # Tab navigator group
│   │   ├── _layout.tsx           # Tab layout configuration
│   │   ├── index.tsx             # Home tab (/)
│   │   ├── explore.tsx           # Explore tab (/explore)
│   │   └── profile.tsx           # Profile tab (/profile)
│   ├── (auth)/                   # Auth group (no tabs)
│   │   ├── _layout.tsx           # Auth stack layout
│   │   ├── login.tsx             # Login screen
│   │   ├── register.tsx          # Register screen
│   │   └── forgot-password.tsx   # Forgot password
│   ├── [id].tsx                  # Dynamic route (/123)
│   ├── [...slug].tsx             # Catch-all route
│   ├── _layout.tsx               # Root layout
│   ├── +not-found.tsx            # 404 page
│   └── +html.tsx                 # Custom HTML (web)
├── src/
│   ├── components/               # Shared components
│   │   ├── ui/                   # Basic UI components
│   │   │   ├── Button.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Input.tsx
│   │   │   └── index.ts
│   │   ├── forms/                # Form components
│   │   │   ├── FormField.tsx
│   │   │   └── index.ts
│   │   └── layout/               # Layout components
│   │       ├── Container.tsx
│   │       ├── SafeArea.tsx
│   │       └── index.ts
│   ├── features/                 # Feature modules
│   │   ├── auth/
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   ├── api/
│   │   │   └── types.ts
│   │   ├── products/
│   │   │   ├── components/
│   │   │   │   ├── ProductCard.tsx
│   │   │   │   └── ProductList.tsx
│   │   │   ├── hooks/
│   │   │   │   └── useProducts.ts
│   │   │   ├── api/
│   │   │   │   └── productApi.ts
│   │   │   └── types.ts
│   │   └── cart/
│   │       ├── components/
│   │       ├── hooks/
│   │       └── types.ts
│   ├── hooks/                    # Shared hooks
│   │   ├── useAuth.ts
│   │   ├── useDebounce.ts
│   │   └── index.ts
│   ├── lib/                      # Utilities and config
│   │   ├── api.ts                # Axios instance
│   │   ├── storage.ts            # Storage utilities
│   │   ├── utils.ts              # Helper functions
│   │   └── constants.ts          # App constants
│   ├── stores/                   # Zustand stores
│   │   ├── useAuthStore.ts
│   │   ├── useCartStore.ts
│   │   └── index.ts
│   ├── types/                    # Global TypeScript types
│   │   ├── api.ts
│   │   ├── navigation.ts
│   │   └── index.ts
│   └── theme/                    # Theme configuration
│       ├── colors.ts
│       ├── spacing.ts
│       ├── typography.ts
│       └── index.ts
├── assets/                       # Static assets
│   ├── images/
│   ├── fonts/
│   └── icons/
├── __tests__/                    # Test files
│   └── setup.ts
├── .expo/                        # Expo cache (gitignored)
├── app.json                      # Expo config
├── babel.config.js               # Babel config
├── metro.config.js               # Metro bundler config
├── tsconfig.json                 # TypeScript config
├── package.json
└── README.md
```

## React Navigation Project Structure (Classic)

```
my-app/
├── src/
│   ├── navigation/               # Navigation configuration
│   │   ├── RootNavigator.tsx     # Root navigator
│   │   ├── AuthNavigator.tsx     # Auth stack
│   │   ├── MainNavigator.tsx     # Main tabs/stack
│   │   ├── types.ts              # Navigation types
│   │   └── index.ts
│   ├── screens/                  # Screen components
│   │   ├── auth/
│   │   │   ├── LoginScreen.tsx
│   │   │   ├── RegisterScreen.tsx
│   │   │   └── index.ts
│   │   ├── home/
│   │   │   ├── HomeScreen.tsx
│   │   │   └── index.ts
│   │   └── profile/
│   │       ├── ProfileScreen.tsx
│   │       └── index.ts
│   ├── components/               # Shared components
│   ├── hooks/                    # Custom hooks
│   ├── services/                 # API services
│   ├── stores/                   # State management
│   ├── utils/                    # Utilities
│   └── types/                    # TypeScript types
├── App.tsx                       # App entry point
└── index.js                      # Metro entry point
```

## Feature-Based Structure (Recommended for Large Apps)

```
src/features/
├── auth/
│   ├── components/
│   │   ├── LoginForm.tsx
│   │   ├── RegisterForm.tsx
│   │   └── index.ts
│   ├── screens/
│   │   ├── LoginScreen.tsx
│   │   ├── RegisterScreen.tsx
│   │   └── index.ts
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   └── index.ts
│   ├── api/
│   │   ├── authApi.ts
│   │   └── index.ts
│   ├── store/
│   │   └── useAuthStore.ts
│   ├── types.ts
│   └── index.ts                  # Public exports
```

## Configuration Files

### app.json (Expo)

```json
{
  "expo": {
    "name": "MyApp",
    "slug": "my-app",
    "version": "1.0.0",
    "orientation": "portrait",
    "icon": "./assets/icon.png",
    "userInterfaceStyle": "automatic",
    "splash": {
      "image": "./assets/splash.png",
      "resizeMode": "contain",
      "backgroundColor": "#ffffff"
    },
    "assetBundlePatterns": ["**/*"],
    "ios": {
      "supportsTablet": true,
      "bundleIdentifier": "com.company.myapp"
    },
    "android": {
      "adaptiveIcon": {
        "foregroundImage": "./assets/adaptive-icon.png",
        "backgroundColor": "#ffffff"
      },
      "package": "com.company.myapp"
    },
    "plugins": [
      "expo-router",
      "expo-secure-store"
    ],
    "experiments": {
      "typedRoutes": true
    }
  }
}
```

### tsconfig.json

```json
{
  "extends": "expo/tsconfig.base",
  "compilerOptions": {
    "strict": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"],
      "@/components/*": ["src/components/*"],
      "@/features/*": ["src/features/*"],
      "@/hooks/*": ["src/hooks/*"],
      "@/lib/*": ["src/lib/*"],
      "@/stores/*": ["src/stores/*"],
      "@/types/*": ["src/types/*"]
    }
  },
  "include": [
    "**/*.ts",
    "**/*.tsx",
    ".expo/types/**/*.ts",
    "expo-env.d.ts"
  ]
}
```

### babel.config.js

```javascript
module.exports = function (api) {
  api.cache(true);
  return {
    presets: ['babel-preset-expo'],
    plugins: [
      'nativewind/babel',
      'react-native-reanimated/plugin',
      [
        'module-resolver',
        {
          root: ['./'],
          alias: {
            '@': './src',
          },
        },
      ],
    ],
  };
};
```

## Best Practices

### File Naming

```typescript
// Components: PascalCase
Button.tsx
ProductCard.tsx

// Hooks: camelCase with "use" prefix
useAuth.ts
useProducts.ts

// Stores: camelCase with "use" prefix and "Store" suffix
useAuthStore.ts
useCartStore.ts

// Utils/Lib: camelCase
api.ts
storage.ts
utils.ts

// Types: PascalCase or camelCase
types.ts
User.ts
```

### Barrel Exports

```typescript
// src/components/ui/index.ts
export { Button } from './Button';
export { Card } from './Card';
export { Input } from './Input';
export type { ButtonProps } from './Button';
export type { CardProps } from './Card';
export type { InputProps } from './Input';

// Usage
import { Button, Card, Input } from '@/components/ui';
```

### Feature Module Exports

```typescript
// src/features/products/index.ts
// Components
export { ProductCard } from './components/ProductCard';
export { ProductList } from './components/ProductList';

// Hooks
export { useProducts, useProduct } from './hooks/useProducts';

// Types
export type { Product, CreateProductInput } from './types';

// Keep API and store internal unless needed externally
```

## Code Organization Guidelines

1. **Colocation**: Keep related code together (component + styles + tests)
2. **Single Responsibility**: One component per file
3. **Index Exports**: Use barrel exports for cleaner imports
4. **Feature Isolation**: Features should be self-contained
5. **Shared Code**: Only extract to shared when used 3+ times
6. **Type Location**: Feature types in feature, global types in `/types`
