---
name: rn-tab-navigator
description: Bottom Tab Navigator patterns and configurations
applies_to: react-native
---

# Tab Navigator

## Installation

```bash
npm install @react-navigation/bottom-tabs
```

## Basic Tab Navigator

```typescript
// src/navigation/MainNavigator.tsx
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import { HomeNavigator } from './HomeNavigator';
import { SearchScreen } from '@/screens/SearchScreen';
import { CartScreen } from '@/screens/CartScreen';
import { ProfileScreen } from '@/screens/ProfileScreen';
import { useCartStore } from '@/stores/useCartStore';
import type { MainTabParamList } from './types';

const Tab = createBottomTabNavigator<MainTabParamList>();

export function MainNavigator() {
  const cartItemCount = useCartStore((state) =>
    state.items.reduce((sum, item) => sum + item.quantity, 0)
  );

  return (
    <Tab.Navigator
      initialRouteName="Home"
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
              iconName = 'ellipse';
          }

          return <Ionicons name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: '#007AFF',
        tabBarInactiveTintColor: '#8E8E93',
        headerShown: false,
      })}
    >
      <Tab.Screen
        name="Home"
        component={HomeNavigator}
        options={{ tabBarLabel: 'Home' }}
      />
      <Tab.Screen
        name="Search"
        component={SearchScreen}
        options={{ tabBarLabel: 'Search' }}
      />
      <Tab.Screen
        name="Cart"
        component={CartScreen}
        options={{
          tabBarLabel: 'Cart',
          tabBarBadge: cartItemCount > 0 ? cartItemCount : undefined,
          tabBarBadgeStyle: {
            backgroundColor: '#FF3B30',
            fontSize: 12,
          },
        }}
      />
      <Tab.Screen
        name="Profile"
        component={ProfileScreen}
        options={{ tabBarLabel: 'Profile' }}
      />
    </Tab.Navigator>
  );
}
```

## Tab Bar Styling

```typescript
<Tab.Navigator
  screenOptions={{
    // Tab bar container
    tabBarStyle: {
      backgroundColor: '#fff',
      borderTopWidth: 0,
      elevation: 10,
      shadowColor: '#000',
      shadowOffset: { width: 0, height: -2 },
      shadowOpacity: 0.1,
      shadowRadius: 4,
      height: 80,
      paddingBottom: 20,
      paddingTop: 10,
    },

    // Active/inactive colors
    tabBarActiveTintColor: '#007AFF',
    tabBarInactiveTintColor: '#8E8E93',

    // Label styling
    tabBarLabelStyle: {
      fontSize: 12,
      fontWeight: '500',
    },
    tabBarLabelPosition: 'below-icon', // or 'beside-icon'

    // Icon styling
    tabBarIconStyle: {
      marginTop: 4,
    },

    // Hide labels
    tabBarShowLabel: true,

    // Hide tab bar on specific screens
    tabBarHideOnKeyboard: true,

    // Allow label pressing
    tabBarAllowFontScaling: false,
  }}
>
```

## Custom Tab Bar

```typescript
// src/components/CustomTabBar.tsx
import { View, Text, Pressable, StyleSheet } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import type { BottomTabBarProps } from '@react-navigation/bottom-tabs';
import Animated, {
  useAnimatedStyle,
  withSpring,
} from 'react-native-reanimated';

export function CustomTabBar({
  state,
  descriptors,
  navigation,
}: BottomTabBarProps) {
  const insets = useSafeAreaInsets();

  return (
    <View style={[styles.container, { paddingBottom: insets.bottom }]}>
      {state.routes.map((route, index) => {
        const { options } = descriptors[route.key];
        const label = options.tabBarLabel ?? options.title ?? route.name;
        const isFocused = state.index === index;

        const onPress = () => {
          const event = navigation.emit({
            type: 'tabPress',
            target: route.key,
            canPreventDefault: true,
          });

          if (!isFocused && !event.defaultPrevented) {
            navigation.navigate(route.name);
          }
        };

        const onLongPress = () => {
          navigation.emit({
            type: 'tabLongPress',
            target: route.key,
          });
        };

        return (
          <TabBarButton
            key={route.key}
            label={label as string}
            isFocused={isFocused}
            onPress={onPress}
            onLongPress={onLongPress}
            icon={options.tabBarIcon}
          />
        );
      })}
    </View>
  );
}

function TabBarButton({
  label,
  isFocused,
  onPress,
  onLongPress,
  icon,
}: {
  label: string;
  isFocused: boolean;
  onPress: () => void;
  onLongPress: () => void;
  icon?: (props: { focused: boolean; color: string; size: number }) => React.ReactNode;
}) {
  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: withSpring(isFocused ? 1.1 : 1) }],
  }));

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={isFocused ? { selected: true } : {}}
      onPress={onPress}
      onLongPress={onLongPress}
      style={styles.tab}
    >
      <Animated.View style={animatedStyle}>
        {icon?.({
          focused: isFocused,
          color: isFocused ? '#007AFF' : '#8E8E93',
          size: 24,
        })}
      </Animated.View>
      <Text
        style={[
          styles.label,
          { color: isFocused ? '#007AFF' : '#8E8E93' },
        ]}
      >
        {label}
      </Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: '#E0E0E0',
    paddingTop: 8,
  },
  tab: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 8,
  },
  label: {
    fontSize: 11,
    marginTop: 4,
    fontWeight: '500',
  },
});

// Usage
<Tab.Navigator tabBar={(props) => <CustomTabBar {...props} />}>
  {/* Screens */}
</Tab.Navigator>
```

## Floating Action Button Tab

```typescript
// Custom tab bar with center FAB
function TabBarWithFAB({ state, descriptors, navigation }: BottomTabBarProps) {
  const insets = useSafeAreaInsets();

  return (
    <View style={[styles.container, { paddingBottom: insets.bottom }]}>
      <View style={styles.tabBar}>
        {state.routes.map((route, index) => {
          // Render FAB in the middle
          if (index === Math.floor(state.routes.length / 2)) {
            return (
              <View key="fab" style={styles.fabContainer}>
                <Pressable
                  style={styles.fab}
                  onPress={() => navigation.navigate('Create')}
                >
                  <Ionicons name="add" size={28} color="#fff" />
                </Pressable>
              </View>
            );
          }

          // Regular tab button
          const { options } = descriptors[route.key];
          const isFocused = state.index === index;

          return (
            <TabButton
              key={route.key}
              {...{ route, options, isFocused, navigation }}
            />
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
  },
  tabBar: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 10,
    paddingTop: 12,
    paddingHorizontal: 20,
  },
  fabContainer: {
    flex: 1,
    alignItems: 'center',
  },
  fab: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#007AFF',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: -28,
    shadowColor: '#007AFF',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
});
```

## Tab Navigation Events

```typescript
function HomeScreen() {
  const navigation = useNavigation();

  // Listen to tab press
  useEffect(() => {
    const unsubscribe = navigation.addListener('tabPress', (e) => {
      // Scroll to top or refresh on re-tap
      if (navigation.isFocused()) {
        scrollViewRef.current?.scrollTo({ y: 0, animated: true });
        // Or refresh data
        refetch();
      }
    });

    return unsubscribe;
  }, [navigation]);

  return (/* ... */);
}
```

## Hiding Tab Bar

```typescript
// Hide on specific screens
<Tab.Screen
  name="Details"
  component={DetailsScreen}
  options={{ tabBarStyle: { display: 'none' } }}
/>

// Hide in nested navigator
function ProductsNavigator() {
  return (
    <Stack.Navigator>
      <Stack.Screen name="List" component={ListScreen} />
      <Stack.Screen
        name="Detail"
        component={DetailScreen}
        options={{
          tabBarStyle: { display: 'none' },
        }}
      />
    </Stack.Navigator>
  );
}

// Or use navigation options
useLayoutEffect(() => {
  navigation.getParent()?.setOptions({
    tabBarStyle: { display: 'none' },
  });

  return () => {
    navigation.getParent()?.setOptions({
      tabBarStyle: undefined,
    });
  };
}, [navigation]);
```

## Tab with Badge

```typescript
<Tab.Screen
  name="Notifications"
  component={NotificationsScreen}
  options={{
    tabBarBadge: 3,
    tabBarBadgeStyle: {
      backgroundColor: '#FF3B30',
      color: '#fff',
      fontSize: 10,
      minWidth: 18,
      height: 18,
      borderRadius: 9,
    },
  }}
/>

// Dynamic badge
function MainNavigator() {
  const unreadCount = useNotificationStore((s) => s.unreadCount);

  return (
    <Tab.Navigator>
      <Tab.Screen
        name="Notifications"
        component={NotificationsScreen}
        options={{
          tabBarBadge: unreadCount > 0 ? unreadCount : undefined,
        }}
      />
    </Tab.Navigator>
  );
}
```

## Best Practices

1. **Limit Tabs**: 3-5 tabs is optimal for UX
2. **Consistent Icons**: Use same icon family throughout
3. **Clear Labels**: Short, descriptive labels
4. **Badge Sparingly**: Only for important notifications
5. **Hide Thoughtfully**: Hide tab bar only when necessary
6. **Keyboard Handling**: Auto-hide on keyboard with `tabBarHideOnKeyboard`
