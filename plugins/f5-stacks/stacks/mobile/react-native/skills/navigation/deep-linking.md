---
name: rn-deep-linking
description: Deep linking and universal links in React Native
applies_to: react-native
---

# Deep Linking

## Overview

Deep linking allows opening specific screens from:
- Custom URL schemes (`myapp://`)
- Universal links (`https://myapp.com/`)
- Push notifications
- External apps

## Configuration

### Expo Configuration (app.json)

```json
{
  "expo": {
    "scheme": "myapp",
    "ios": {
      "bundleIdentifier": "com.company.myapp",
      "associatedDomains": ["applinks:myapp.com"]
    },
    "android": {
      "package": "com.company.myapp",
      "intentFilters": [
        {
          "action": "VIEW",
          "autoVerify": true,
          "data": [
            {
              "scheme": "https",
              "host": "myapp.com",
              "pathPrefix": "/"
            }
          ],
          "category": ["BROWSABLE", "DEFAULT"]
        }
      ]
    }
  }
}
```

### React Navigation Linking Config

```typescript
// src/navigation/linking.ts
import { LinkingOptions } from '@react-navigation/native';
import * as Linking from 'expo-linking';
import * as Notifications from 'expo-notifications';
import type { RootStackParamList } from './types';

const prefix = Linking.createURL('/');

export const linking: LinkingOptions<RootStackParamList> = {
  prefixes: [prefix, 'myapp://', 'https://myapp.com'],

  config: {
    screens: {
      Main: {
        screens: {
          Home: {
            screens: {
              HomeScreen: 'home',
              ProductDetail: 'product/:id',
              Category: 'category/:slug',
            },
          },
          Search: 'search',
          Cart: 'cart',
          Profile: {
            screens: {
              ProfileScreen: 'profile',
              Settings: 'settings',
              Orders: 'orders',
              OrderDetail: 'orders/:id',
            },
          },
        },
      },
      Auth: {
        screens: {
          Login: 'login',
          Register: 'register',
          ResetPassword: 'reset-password/:token',
        },
      },
      Modal: 'modal',
    },
  },

  // Custom URL to state mapping
  getStateFromPath: (path, options) => {
    // Handle custom paths
    if (path.startsWith('/share/')) {
      const shareId = path.replace('/share/', '');
      return {
        routes: [
          {
            name: 'Main',
            state: {
              routes: [
                {
                  name: 'Home',
                  state: {
                    routes: [
                      { name: 'HomeScreen' },
                      { name: 'ProductDetail', params: { id: shareId } },
                    ],
                  },
                },
              ],
            },
          },
        ],
      };
    }

    // Use default parsing
    return undefined;
  },

  // Custom state to URL mapping
  getPathFromState: (state, options) => {
    // Use default
    return undefined;
  },

  // Handle notification deep links
  async getInitialURL() {
    // Check if app was opened from a deep link
    const url = await Linking.getInitialURL();
    if (url) return url;

    // Check if app was opened from a push notification
    const response = await Notifications.getLastNotificationResponseAsync();
    return response?.notification.request.content.data?.url;
  },

  // Listen for incoming links
  subscribe(listener) {
    // Listen to URL events
    const urlSubscription = Linking.addEventListener('url', ({ url }) => {
      listener(url);
    });

    // Listen to notification events
    const notificationSubscription =
      Notifications.addNotificationResponseReceivedListener((response) => {
        const url = response.notification.request.content.data?.url;
        if (url) listener(url);
      });

    return () => {
      urlSubscription.remove();
      notificationSubscription.remove();
    };
  },
};
```

### Usage in App

```typescript
// App.tsx
import { NavigationContainer } from '@react-navigation/native';
import { linking } from '@/navigation/linking';

export default function App() {
  return (
    <NavigationContainer
      linking={linking}
      fallback={<LoadingScreen />}
      onStateChange={(state) => {
        // Track screen views
        const currentScreen = getCurrentRouteName(state);
        analytics.logScreenView(currentScreen);
      }}
    >
      <RootNavigator />
    </NavigationContainer>
  );
}
```

## URL Patterns

### Path Parameters

```typescript
// Config
screens: {
  ProductDetail: 'product/:id',
  UserProfile: 'user/:userId/profile',
  Category: 'category/:slug',
}

// URLs
// myapp://product/123 → ProductDetail { id: '123' }
// myapp://user/456/profile → UserProfile { userId: '456' }
// myapp://category/electronics → Category { slug: 'electronics' }
```

### Query Parameters

```typescript
// Config
screens: {
  Search: {
    path: 'search',
    parse: {
      query: (q: string) => q,
      category: (c: string) => c,
    },
  },
}

// URL
// myapp://search?query=phone&category=electronics
// → Search { query: 'phone', category: 'electronics' }
```

### Exact Paths

```typescript
// Config
screens: {
  Home: {
    path: '',           // Root path
    exact: true,        // Must match exactly
  },
  About: {
    path: 'about',
    exact: true,
  },
}
```

## Programmatic Navigation

### Using Linking API

```typescript
import * as Linking from 'expo-linking';

// Open internal deep link
Linking.openURL('myapp://product/123');

// Open external URL
Linking.openURL('https://google.com');

// Check if URL can be opened
const canOpen = await Linking.canOpenURL('myapp://');

// Get current URL
const url = await Linking.getInitialURL();

// Create deep link URL
const deepLink = Linking.createURL('product/123', {
  queryParams: { ref: 'share' },
});
// Result: exp://127.0.0.1:19000/--/product/123?ref=share (dev)
// Result: myapp://product/123?ref=share (production)
```

### Using Navigation

```typescript
import { useNavigation, CommonActions } from '@react-navigation/native';

function ShareButton({ productId }: { productId: string }) {
  const navigation = useNavigation();

  const handleDeepLink = () => {
    // Navigate as if coming from deep link
    navigation.dispatch(
      CommonActions.navigate({
        name: 'ProductDetail',
        params: { id: productId },
      })
    );
  };

  const handleResetToDeepLink = () => {
    // Reset navigation state
    navigation.dispatch(
      CommonActions.reset({
        index: 1,
        routes: [
          { name: 'Home' },
          { name: 'ProductDetail', params: { id: productId } },
        ],
      })
    );
  };
}
```

## Push Notification Deep Links

```typescript
// src/lib/notifications.ts
import * as Notifications from 'expo-notifications';
import { router } from 'expo-router'; // or useNavigation

export async function setupNotificationHandler() {
  // Handle notification when app is foregrounded
  Notifications.setNotificationHandler({
    handleNotification: async () => ({
      shouldShowAlert: true,
      shouldPlaySound: true,
      shouldSetBadge: true,
    }),
  });

  // Handle notification tap
  const subscription = Notifications.addNotificationResponseReceivedListener(
    (response) => {
      const { data } = response.notification.request.content;

      if (data?.type === 'order') {
        router.push(`/orders/${data.orderId}`);
      } else if (data?.type === 'product') {
        router.push(`/product/${data.productId}`);
      } else if (data?.url) {
        router.push(data.url);
      }
    }
  );

  return () => subscription.remove();
}

// Send notification with deep link
async function sendLocalNotification(orderId: string) {
  await Notifications.scheduleNotificationAsync({
    content: {
      title: 'Order Updated',
      body: 'Your order has been shipped!',
      data: {
        type: 'order',
        orderId,
        url: `/orders/${orderId}`,
      },
    },
    trigger: null, // immediate
  });
}
```

## Testing Deep Links

```bash
# iOS Simulator
xcrun simctl openurl booted "myapp://product/123"

# Android Emulator
adb shell am start -W -a android.intent.action.VIEW -d "myapp://product/123"

# Expo Go
npx uri-scheme open "exp://127.0.0.1:19000/--/product/123" --ios
```

```typescript
// Test in development
import * as Linking from 'expo-linking';

function DevTools() {
  return (
    <View>
      <Button
        title="Test Product Link"
        onPress={() => Linking.openURL('myapp://product/123')}
      />
      <Button
        title="Test Order Link"
        onPress={() => Linking.openURL('myapp://orders/456')}
      />
    </View>
  );
}
```

## Universal Links (iOS) / App Links (Android)

### Apple App Site Association

```json
// https://myapp.com/.well-known/apple-app-site-association
{
  "applinks": {
    "apps": [],
    "details": [
      {
        "appID": "TEAM_ID.com.company.myapp",
        "paths": ["/product/*", "/orders/*", "/share/*"]
      }
    ]
  }
}
```

### Android Asset Links

```json
// https://myapp.com/.well-known/assetlinks.json
[
  {
    "relation": ["delegate_permission/common.handle_all_urls"],
    "target": {
      "namespace": "android_app",
      "package_name": "com.company.myapp",
      "sha256_cert_fingerprints": ["YOUR_CERT_FINGERPRINT"]
    }
  }
]
```

## Best Practices

1. **Test All Paths**: Test each deep link path thoroughly
2. **Fallback Handling**: Handle cases where screen doesn't exist
3. **Auth Guards**: Check auth state before navigating to protected screens
4. **Analytics**: Track deep link opens for marketing
5. **URL Validation**: Validate and sanitize URL parameters
6. **User Experience**: Show loading states during navigation
