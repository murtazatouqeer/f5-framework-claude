---
name: rn-stack-navigator
description: Stack Navigator patterns and configurations
applies_to: react-native
---

# Stack Navigator

## Installation

```bash
# Recommended: Native Stack (better performance)
npm install @react-navigation/native-stack

# Alternative: JS Stack (more customizable)
npm install @react-navigation/stack react-native-gesture-handler
```

## Native Stack Navigator

```typescript
// src/navigation/ProductsNavigator.tsx
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import {
  ProductListScreen,
  ProductDetailScreen,
  ProductCreateScreen,
  ProductEditScreen,
} from '@/features/products/screens';
import type { ProductsStackParamList } from './types';

const Stack = createNativeStackNavigator<ProductsStackParamList>();

export function ProductsNavigator() {
  return (
    <Stack.Navigator
      initialRouteName="ProductList"
      screenOptions={{
        headerShown: true,
        headerBackTitleVisible: false,
        animation: 'slide_from_right',
        headerStyle: {
          backgroundColor: '#fff',
        },
        headerTintColor: '#007AFF',
        contentStyle: {
          backgroundColor: '#f5f5f5',
        },
      }}
    >
      <Stack.Screen
        name="ProductList"
        component={ProductListScreen}
        options={{
          title: 'Products',
          headerLargeTitle: true,
          headerSearchBarOptions: {
            placeholder: 'Search products',
            onChangeText: (event) => {
              // Handle search
            },
          },
        }}
      />

      <Stack.Screen
        name="ProductDetail"
        component={ProductDetailScreen}
        options={({ route }) => ({
          title: 'Product Details',
          headerRight: () => <ShareButton id={route.params.id} />,
        })}
      />

      <Stack.Screen
        name="ProductCreate"
        component={ProductCreateScreen}
        options={{
          title: 'New Product',
          presentation: 'modal',
          headerLeft: () => <CancelButton />,
          headerRight: () => <SaveButton />,
        }}
      />

      <Stack.Screen
        name="ProductEdit"
        component={ProductEditScreen}
        options={{
          title: 'Edit Product',
          presentation: 'modal',
        }}
      />
    </Stack.Navigator>
  );
}
```

## Screen Presentations

```typescript
// Modal presentation
<Stack.Screen
  name="Modal"
  component={ModalScreen}
  options={{
    presentation: 'modal',               // iOS: card slides up
    animation: 'slide_from_bottom',      // Android animation
    gestureEnabled: true,
    gestureDirection: 'vertical',
  }}
/>

// Transparent modal (overlay)
<Stack.Screen
  name="Overlay"
  component={OverlayScreen}
  options={{
    presentation: 'transparentModal',
    animation: 'fade',
    contentStyle: {
      backgroundColor: 'rgba(0,0,0,0.5)',
    },
  }}
/>

// Full screen modal (no card style)
<Stack.Screen
  name="FullScreen"
  component={FullScreenScreen}
  options={{
    presentation: 'fullScreenModal',
    headerShown: false,
  }}
/>

// Contained modal (with navigation bar)
<Stack.Screen
  name="ContainedModal"
  component={ContainedModalScreen}
  options={{
    presentation: 'containedModal',
  }}
/>

// Form sheet (iPad style)
<Stack.Screen
  name="FormSheet"
  component={FormSheetScreen}
  options={{
    presentation: 'formSheet',
  }}
/>
```

## Animation Options

```typescript
// Native Stack animations
const animations = {
  'default': 'Platform default',
  'fade': 'Fade in/out',
  'fade_from_bottom': 'Fade + slide from bottom',
  'flip': 'Flip transition',
  'simple_push': 'Simple push (no spring)',
  'slide_from_bottom': 'Slide from bottom',
  'slide_from_right': 'Slide from right',
  'slide_from_left': 'Slide from left',
  'none': 'No animation',
};

<Stack.Screen
  name="Screen"
  component={Screen}
  options={{
    animation: 'slide_from_right',
    animationDuration: 350,
    // iOS specific
    animationTypeForReplace: 'push',
  }}
/>

// Conditional animation
options={({ route }) => ({
  animation: route.params?.animate === false ? 'none' : 'slide_from_right',
})}
```

## Header Configuration

```typescript
// Full header customization
<Stack.Screen
  name="CustomHeader"
  component={CustomHeaderScreen}
  options={{
    // Title
    title: 'Custom Header',
    headerTitle: (props) => <CustomTitle {...props} />,
    headerTitleAlign: 'center',
    headerTitleStyle: {
      fontWeight: '700',
      fontSize: 18,
    },

    // Back button
    headerBackVisible: true,
    headerBackTitle: 'Back',
    headerBackTitleVisible: true,
    headerBackTitleStyle: {
      fontSize: 14,
    },

    // Custom back button
    headerLeft: (props) => (
      <Pressable onPress={props.onPress}>
        <Icon name="arrow-left" />
      </Pressable>
    ),

    // Right buttons
    headerRight: () => (
      <View style={{ flexDirection: 'row', gap: 16 }}>
        <Pressable onPress={handleSearch}>
          <Icon name="search" />
        </Pressable>
        <Pressable onPress={handleMore}>
          <Icon name="more" />
        </Pressable>
      </View>
    ),

    // Styling
    headerStyle: {
      backgroundColor: '#007AFF',
    },
    headerTintColor: '#fff',
    headerShadowVisible: false,
    headerBlurEffect: 'regular', // iOS blur

    // Large title (iOS)
    headerLargeTitle: true,
    headerLargeTitleStyle: {
      fontWeight: '700',
    },
    headerLargeStyle: {
      backgroundColor: '#f5f5f5',
    },

    // Search bar (iOS)
    headerSearchBarOptions: {
      placeholder: 'Search',
      onChangeText: handleSearch,
      onCancelButtonPress: handleCancel,
      hideWhenScrolling: true,
    },

    // Transparent header
    headerTransparent: true,
  }}
/>
```

## Custom Header Component

```typescript
// Replace entire header
<Stack.Screen
  name="CustomHeaderScreen"
  component={Screen}
  options={{
    header: ({ navigation, route, options }) => (
      <CustomHeader
        title={options.title ?? route.name}
        onBack={() => navigation.goBack()}
      />
    ),
  }}
/>

// Custom header component
function CustomHeader({ title, onBack }: { title: string; onBack: () => void }) {
  const insets = useSafeAreaInsets();

  return (
    <View style={[styles.header, { paddingTop: insets.top }]}>
      <Pressable onPress={onBack} style={styles.backButton}>
        <Icon name="chevron-left" size={24} color="#007AFF" />
      </Pressable>
      <Text style={styles.title}>{title}</Text>
      <View style={styles.rightPlaceholder} />
    </View>
  );
}
```

## Navigation Guards

```typescript
// Prevent navigation with unsaved changes
function EditScreen() {
  const navigation = useNavigation();
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    const unsubscribe = navigation.addListener('beforeRemove', (e) => {
      if (!hasChanges) return;

      e.preventDefault();

      Alert.alert(
        'Discard changes?',
        'You have unsaved changes. Are you sure you want to discard them?',
        [
          { text: "Don't leave", style: 'cancel' },
          {
            text: 'Discard',
            style: 'destructive',
            onPress: () => navigation.dispatch(e.data.action),
          },
        ]
      );
    });

    return unsubscribe;
  }, [navigation, hasChanges]);

  return (/* ... */);
}
```

## Nested Stacks

```typescript
// Parent stack
function RootNavigator() {
  return (
    <RootStack.Navigator>
      <RootStack.Screen name="Main" component={MainTabs} />
      <RootStack.Screen name="Auth" component={AuthNavigator} />
    </RootStack.Navigator>
  );
}

// Tab navigator with nested stack
function MainTabs() {
  return (
    <Tab.Navigator>
      <Tab.Screen
        name="HomeTab"
        component={HomeNavigator}
        options={{ headerShown: false }}
      />
      <Tab.Screen
        name="ProfileTab"
        component={ProfileNavigator}
        options={{ headerShown: false }}
      />
    </Tab.Navigator>
  );
}

// Nested stack in tab
function HomeNavigator() {
  return (
    <HomeStack.Navigator>
      <HomeStack.Screen name="Home" component={HomeScreen} />
      <HomeStack.Screen name="Details" component={DetailsScreen} />
    </HomeStack.Navigator>
  );
}

// Navigate from nested stack to root
const navigation = useNavigation();
navigation.getParent()?.navigate('Auth'); // Navigate to Auth stack
```

## Best Practices

1. **Use Native Stack**: Better performance for most use cases
2. **Type Param Lists**: Define all screen params with TypeScript
3. **Consistent Animations**: Use same animation across similar screens
4. **Header Customization**: Use options over custom header when possible
5. **Navigation Guards**: Protect screens with unsaved data
6. **Deep Nesting**: Avoid more than 3 levels of nesting
