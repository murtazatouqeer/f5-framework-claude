---
name: rn-navigation
description: React Navigation setup templates for React Native
applies_to: react-native
variables:
  - name: useExpoRouter
    description: Use Expo Router (file-based) or React Navigation (manual)
---

# Navigation Templates

## Expo Router (File-Based) - Recommended

### Project Structure

```
app/
├── _layout.tsx          # Root layout
├── index.tsx            # Home screen
├── (tabs)/              # Tab group
│   ├── _layout.tsx      # Tab navigator
│   ├── index.tsx        # Home tab
│   ├── search.tsx       # Search tab
│   ├── cart.tsx         # Cart tab
│   └── profile.tsx      # Profile tab
├── (auth)/              # Auth group
│   ├── _layout.tsx      # Auth layout
│   ├── login.tsx        # Login screen
│   └── register.tsx     # Register screen
├── product/
│   └── [id].tsx         # Product detail
├── settings/
│   ├── _layout.tsx      # Settings stack
│   ├── index.tsx        # Settings main
│   └── notifications.tsx
└── +not-found.tsx       # 404 screen
```

### Root Layout

```typescript
// app/_layout.tsx
import { Stack } from 'expo-router';
import { useEffect } from 'react';
import { useAuthStore } from '@/stores/useAuthStore';
import { SplashScreen } from 'expo-router';
import { useFonts } from 'expo-font';
import { QueryProvider } from '@/providers/QueryProvider';
import { ThemeProvider } from '@/providers/ThemeProvider';

SplashScreen.preventAutoHideAsync();

export default function RootLayout() {
  const [fontsLoaded] = useFonts({
    // Custom fonts
  });

  useEffect(() => {
    if (fontsLoaded) {
      SplashScreen.hideAsync();
    }
  }, [fontsLoaded]);

  if (!fontsLoaded) {
    return null;
  }

  return (
    <QueryProvider>
      <ThemeProvider>
        <Stack screenOptions={{ headerShown: false }}>
          <Stack.Screen name="(tabs)" />
          <Stack.Screen name="(auth)" />
          <Stack.Screen
            name="product/[id]"
            options={{
              headerShown: true,
              title: '',
              presentation: 'card',
            }}
          />
          <Stack.Screen
            name="settings"
            options={{
              headerShown: true,
              title: 'Settings',
            }}
          />
        </Stack>
      </ThemeProvider>
    </QueryProvider>
  );
}
```

### Tab Layout

```typescript
// app/(tabs)/_layout.tsx
import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '@/hooks/useTheme';

export default function TabLayout() {
  const { colors } = useTheme();

  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.textSecondary,
        tabBarStyle: {
          backgroundColor: colors.background,
          borderTopColor: colors.border,
        },
        headerStyle: {
          backgroundColor: colors.background,
        },
        headerTintColor: colors.text,
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: 'Home',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="home" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="search"
        options={{
          title: 'Search',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="search" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="cart"
        options={{
          title: 'Cart',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="cart" size={size} color={color} />
          ),
          tabBarBadge: 3, // Dynamic badge
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: 'Profile',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="person" size={size} color={color} />
          ),
        }}
      />
    </Tabs>
  );
}
```

### Auth Layout with Protection

```typescript
// app/(auth)/_layout.tsx
import { Stack, Redirect } from 'expo-router';
import { useAuthStore } from '@/stores/useAuthStore';

export default function AuthLayout() {
  const { isAuthenticated } = useAuthStore();

  // Redirect to home if already authenticated
  if (isAuthenticated) {
    return <Redirect href="/(tabs)" />;
  }

  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="login" />
      <Stack.Screen name="register" />
    </Stack>
  );
}
```

### Protected Route

```typescript
// app/(tabs)/_layout.tsx
import { Tabs, Redirect } from 'expo-router';
import { useAuthStore } from '@/stores/useAuthStore';

export default function TabLayout() {
  const { isAuthenticated, isLoading } = useAuthStore();

  if (isLoading) {
    return <LoadingScreen />;
  }

  if (!isAuthenticated) {
    return <Redirect href="/(auth)/login" />;
  }

  return (
    <Tabs>
      {/* Tab screens */}
    </Tabs>
  );
}
```

## React Navigation (Manual Setup)

### Navigator Types

```typescript
// src/navigation/types.ts
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { BottomTabScreenProps } from '@react-navigation/bottom-tabs';
import type { CompositeScreenProps } from '@react-navigation/native';

// Root stack params
export type RootStackParamList = {
  Main: undefined;
  Auth: undefined;
  ProductDetail: { id: string };
  Settings: undefined;
};

// Tab params
export type TabParamList = {
  Home: undefined;
  Search: { query?: string };
  Cart: undefined;
  Profile: undefined;
};

// Auth stack params
export type AuthStackParamList = {
  Login: undefined;
  Register: undefined;
  ForgotPassword: { email?: string };
};

// Screen props helpers
export type RootStackScreenProps<T extends keyof RootStackParamList> =
  NativeStackScreenProps<RootStackParamList, T>;

export type TabScreenProps<T extends keyof TabParamList> = CompositeScreenProps<
  BottomTabScreenProps<TabParamList, T>,
  RootStackScreenProps<keyof RootStackParamList>
>;

declare global {
  namespace ReactNavigation {
    interface RootParamList extends RootStackParamList {}
  }
}
```

### Root Navigator

```typescript
// src/navigation/RootNavigator.tsx
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { useAuthStore } from '@/stores/useAuthStore';
import { MainNavigator } from './MainNavigator';
import { AuthNavigator } from './AuthNavigator';
import { ProductDetailScreen } from '@/screens/ProductDetailScreen';
import { SettingsScreen } from '@/screens/SettingsScreen';
import type { RootStackParamList } from './types';

const Stack = createNativeStackNavigator<RootStackParamList>();

export function RootNavigator() {
  const { isAuthenticated, isLoading } = useAuthStore();

  if (isLoading) {
    return <LoadingScreen />;
  }

  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      {isAuthenticated ? (
        <>
          <Stack.Screen name="Main" component={MainNavigator} />
          <Stack.Screen
            name="ProductDetail"
            component={ProductDetailScreen}
            options={{ headerShown: true, title: '' }}
          />
          <Stack.Screen
            name="Settings"
            component={SettingsScreen}
            options={{ headerShown: true, title: 'Settings' }}
          />
        </>
      ) : (
        <Stack.Screen name="Auth" component={AuthNavigator} />
      )}
    </Stack.Navigator>
  );
}
```

### Tab Navigator

```typescript
// src/navigation/MainNavigator.tsx
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import { HomeScreen } from '@/screens/HomeScreen';
import { SearchScreen } from '@/screens/SearchScreen';
import { CartScreen } from '@/screens/CartScreen';
import { ProfileScreen } from '@/screens/ProfileScreen';
import { useCartItemCount } from '@/stores/useCartStore';
import type { TabParamList } from './types';

const Tab = createBottomTabNavigator<TabParamList>();

export function MainNavigator() {
  const cartCount = useCartItemCount();

  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName: keyof typeof Ionicons.glyphMap;

          switch (route.name) {
            case 'Home':
              iconName = focused ? 'home' : 'home-outline';
              break;
            case 'Search':
              iconName = focused ? 'search' : 'search-outline';
              break;
            case 'Cart':
              iconName = focused ? 'cart' : 'cart-outline';
              break;
            case 'Profile':
              iconName = focused ? 'person' : 'person-outline';
              break;
            default:
              iconName = 'help-outline';
          }

          return <Ionicons name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: '#007AFF',
        tabBarInactiveTintColor: '#8E8E93',
      })}
    >
      <Tab.Screen name="Home" component={HomeScreen} />
      <Tab.Screen name="Search" component={SearchScreen} />
      <Tab.Screen
        name="Cart"
        component={CartScreen}
        options={{ tabBarBadge: cartCount > 0 ? cartCount : undefined }}
      />
      <Tab.Screen name="Profile" component={ProfileScreen} />
    </Tab.Navigator>
  );
}
```

### Navigation Usage

```typescript
// In any screen or component
import { useNavigation, useRoute } from '@react-navigation/native';
import type { TabScreenProps } from '@/navigation/types';

// Type-safe navigation
type Props = TabScreenProps<'Home'>;

function HomeScreen({ navigation }: Props) {
  const handleProductPress = (id: string) => {
    navigation.navigate('ProductDetail', { id });
  };

  return (/* ... */);
}

// Or with hooks
function ProductCard({ product }) {
  const navigation = useNavigation();

  const handlePress = () => {
    navigation.navigate('ProductDetail', { id: product.id });
  };
}
```

## Deep Linking Configuration

```typescript
// src/navigation/linking.ts
import { LinkingOptions } from '@react-navigation/native';
import * as Linking from 'expo-linking';
import type { RootStackParamList } from './types';

const prefix = Linking.createURL('/');

export const linking: LinkingOptions<RootStackParamList> = {
  prefixes: [prefix, 'myapp://', 'https://myapp.com'],
  config: {
    screens: {
      Main: {
        screens: {
          Home: '',
          Search: 'search',
          Cart: 'cart',
          Profile: 'profile',
        },
      },
      ProductDetail: 'product/:id',
      Settings: 'settings',
      Auth: {
        screens: {
          Login: 'login',
          Register: 'register',
        },
      },
    },
  },
};
```

## Usage

1. Choose Expo Router (recommended) or React Navigation
2. Set up navigation structure based on app requirements
3. Add type definitions for type-safe navigation
4. Configure deep linking as needed
5. Add auth protection where required
