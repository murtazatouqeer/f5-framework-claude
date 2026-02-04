---
name: rn-react-navigation
description: React Navigation setup and patterns
applies_to: react-native
---

# React Navigation

## Installation

```bash
# Core packages
npm install @react-navigation/native

# Required dependencies
npm install react-native-screens react-native-safe-area-context

# Navigator types
npm install @react-navigation/stack                # Stack navigator
npm install @react-navigation/bottom-tabs          # Bottom tabs
npm install @react-navigation/drawer               # Drawer navigator
npm install @react-navigation/native-stack         # Native stack (recommended)

# Additional dependencies for gestures
npm install react-native-gesture-handler
```

## Basic Setup

```typescript
// App.tsx
import { NavigationContainer } from '@react-navigation/native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { RootNavigator } from '@/navigation';

export default function App() {
  return (
    <SafeAreaProvider>
      <NavigationContainer>
        <RootNavigator />
      </NavigationContainer>
    </SafeAreaProvider>
  );
}
```

## Navigation Types

```typescript
// src/navigation/types.ts
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { BottomTabNavigationProp } from '@react-navigation/bottom-tabs';
import type { CompositeNavigationProp, RouteProp } from '@react-navigation/native';

// Root Stack
export type RootStackParamList = {
  Auth: undefined;
  Main: undefined;
  Modal: { title: string };
};

// Auth Stack
export type AuthStackParamList = {
  Login: undefined;
  Register: undefined;
  ForgotPassword: { email?: string };
};

// Main Tab
export type MainTabParamList = {
  Home: undefined;
  Search: undefined;
  Profile: undefined;
};

// Home Stack (nested in tab)
export type HomeStackParamList = {
  HomeScreen: undefined;
  Details: { id: string };
  Settings: undefined;
};

// Navigation prop types
export type RootStackNavigationProp = NativeStackNavigationProp<RootStackParamList>;
export type AuthStackNavigationProp = NativeStackNavigationProp<AuthStackParamList>;
export type MainTabNavigationProp = BottomTabNavigationProp<MainTabParamList>;

// Composite navigation (nested navigators)
export type HomeScreenNavigationProp = CompositeNavigationProp<
  NativeStackNavigationProp<HomeStackParamList>,
  CompositeNavigationProp<
    BottomTabNavigationProp<MainTabParamList>,
    NativeStackNavigationProp<RootStackParamList>
  >
>;

// Route prop types
export type DetailsRouteProp = RouteProp<HomeStackParamList, 'Details'>;
export type ForgotPasswordRouteProp = RouteProp<AuthStackParamList, 'ForgotPassword'>;
```

## Root Navigator

```typescript
// src/navigation/RootNavigator.tsx
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { useAuth } from '@/hooks/useAuth';
import { AuthNavigator } from './AuthNavigator';
import { MainNavigator } from './MainNavigator';
import { ModalScreen } from '@/screens/ModalScreen';
import { LoadingScreen } from '@/screens/LoadingScreen';
import type { RootStackParamList } from './types';

const Stack = createNativeStackNavigator<RootStackParamList>();

export function RootNavigator() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingScreen />;
  }

  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      {isAuthenticated ? (
        <>
          <Stack.Screen name="Main" component={MainNavigator} />
          <Stack.Screen
            name="Modal"
            component={ModalScreen}
            options={{
              presentation: 'modal',
              animation: 'slide_from_bottom',
            }}
          />
        </>
      ) : (
        <Stack.Screen name="Auth" component={AuthNavigator} />
      )}
    </Stack.Navigator>
  );
}
```

## Auth Navigator

```typescript
// src/navigation/AuthNavigator.tsx
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { LoginScreen } from '@/screens/auth/LoginScreen';
import { RegisterScreen } from '@/screens/auth/RegisterScreen';
import { ForgotPasswordScreen } from '@/screens/auth/ForgotPasswordScreen';
import type { AuthStackParamList } from './types';

const Stack = createNativeStackNavigator<AuthStackParamList>();

export function AuthNavigator() {
  return (
    <Stack.Navigator
      screenOptions={{
        headerShown: false,
        animation: 'slide_from_right',
      }}
    >
      <Stack.Screen name="Login" component={LoginScreen} />
      <Stack.Screen name="Register" component={RegisterScreen} />
      <Stack.Screen name="ForgotPassword" component={ForgotPasswordScreen} />
    </Stack.Navigator>
  );
}
```

## Typed Navigation Hooks

```typescript
// src/hooks/useAppNavigation.ts
import { useNavigation, useRoute } from '@react-navigation/native';
import type {
  HomeScreenNavigationProp,
  DetailsRouteProp,
  AuthStackNavigationProp,
} from '@/navigation/types';

// Type-safe navigation hook
export function useHomeNavigation() {
  return useNavigation<HomeScreenNavigationProp>();
}

export function useAuthNavigation() {
  return useNavigation<AuthStackNavigationProp>();
}

// Type-safe route hook
export function useDetailsRoute() {
  return useRoute<DetailsRouteProp>();
}

// Usage in component
function DetailsScreen() {
  const navigation = useHomeNavigation();
  const route = useDetailsRoute();

  const { id } = route.params;

  const handleBack = () => {
    navigation.goBack();
  };

  const handleNavigateToSettings = () => {
    navigation.navigate('Settings');
  };

  // Navigate to parent stack
  const handleOpenModal = () => {
    navigation.getParent()?.navigate('Modal', { title: 'Hello' });
  };

  return (/* ... */);
}
```

## Screen Options

```typescript
// Common screen options
const screenOptions = {
  // Header
  headerShown: true,
  headerTitle: 'Screen Title',
  headerTitleAlign: 'center' as const,
  headerBackTitle: 'Back',
  headerBackTitleVisible: false,

  // Styling
  headerStyle: {
    backgroundColor: '#fff',
  },
  headerTintColor: '#007AFF',
  headerTitleStyle: {
    fontWeight: '600' as const,
  },

  // Animation
  animation: 'slide_from_right' as const,
  animationDuration: 250,

  // Gestures
  gestureEnabled: true,
  fullScreenGestureEnabled: true,

  // Content
  contentStyle: {
    backgroundColor: '#f5f5f5',
  },
};

// Per-screen options
<Stack.Screen
  name="Details"
  component={DetailsScreen}
  options={({ route }) => ({
    title: `Item ${route.params.id}`,
    headerRight: () => (
      <Pressable onPress={handleShare}>
        <Icon name="share" />
      </Pressable>
    ),
  })}
/>
```

## Navigation Events

```typescript
import { useNavigation, useFocusEffect } from '@react-navigation/native';
import { useCallback } from 'react';

function MyScreen() {
  const navigation = useNavigation();

  // Run effect when screen is focused
  useFocusEffect(
    useCallback(() => {
      // Fetch data when screen comes into focus
      fetchData();

      return () => {
        // Cleanup when screen loses focus
        cleanup();
      };
    }, [])
  );

  // Listen to navigation events
  useEffect(() => {
    const unsubscribe = navigation.addListener('beforeRemove', (e) => {
      // Prevent going back
      if (hasUnsavedChanges) {
        e.preventDefault();
        Alert.alert('Unsaved changes', 'Save before leaving?');
      }
    });

    return unsubscribe;
  }, [navigation, hasUnsavedChanges]);

  return (/* ... */);
}
```

## Navigation Params

```typescript
// Passing params
navigation.navigate('Details', { id: '123', title: 'Hello' });

// Passing params to nested navigator
navigation.navigate('Main', {
  screen: 'Home',
  params: {
    screen: 'Details',
    params: { id: '123' },
  },
});

// Update params
navigation.setParams({ title: 'Updated Title' });

// Get params with type safety
const route = useRoute<DetailsRouteProp>();
const { id, title } = route.params;

// Optional params with defaults
const title = route.params?.title ?? 'Default Title';
```

## Reset Navigation State

```typescript
import { CommonActions } from '@react-navigation/native';

// Reset to specific state
navigation.dispatch(
  CommonActions.reset({
    index: 0,
    routes: [{ name: 'Home' }],
  })
);

// Reset after logout
const handleLogout = () => {
  logout();
  navigation.dispatch(
    CommonActions.reset({
      index: 0,
      routes: [{ name: 'Auth' }],
    })
  );
};
```

## Best Practices

1. **Type Everything**: Use TypeScript for all navigation types
2. **Centralize Types**: Keep all param lists in one file
3. **Custom Hooks**: Create typed navigation hooks
4. **Avoid Prop Drilling**: Use navigation hooks instead
5. **Handle Deep Links**: Configure linking for external navigation
6. **Persist State**: Save navigation state for app resume
