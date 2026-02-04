---
name: rn-optimization
description: Performance optimization techniques for React Native
applies_to: react-native
---

# React Native Performance Optimization

## Rendering Optimization

### Memoization

```typescript
// src/components/ProductCard.tsx
import { memo, useCallback, useMemo } from 'react';
import { View, Text, Pressable, StyleSheet } from 'react-native';

interface ProductCardProps {
  product: Product;
  onPress: (id: string) => void;
  isFavorite: boolean;
}

// Memo the component
export const ProductCard = memo(function ProductCard({
  product,
  onPress,
  isFavorite,
}: ProductCardProps) {
  // Memoize callback
  const handlePress = useCallback(() => {
    onPress(product.id);
  }, [product.id, onPress]);

  // Memoize computed values
  const formattedPrice = useMemo(() => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(product.price);
  }, [product.price]);

  return (
    <Pressable onPress={handlePress} style={styles.card}>
      <Text style={styles.name}>{product.name}</Text>
      <Text style={styles.price}>{formattedPrice}</Text>
    </Pressable>
  );
});

// Parent component
function ProductList({ products }: { products: Product[] }) {
  // Stable callback reference
  const handleProductPress = useCallback((id: string) => {
    navigation.navigate('ProductDetail', { id });
  }, []);

  return (
    <FlatList
      data={products}
      renderItem={({ item }) => (
        <ProductCard
          product={item}
          onPress={handleProductPress}
          isFavorite={favorites.includes(item.id)}
        />
      )}
      keyExtractor={(item) => item.id}
    />
  );
}
```

### Avoid Inline Functions

```typescript
// ❌ Bad - creates new function every render
<Pressable onPress={() => handlePress(item.id)}>

// ✅ Good - stable function reference
const handlePress = useCallback((id: string) => {
  // handle press
}, []);

// In FlatList renderItem
renderItem={({ item }) => (
  <Pressable onPress={() => handlePress(item.id)}>
    {/* Better: pass id via data attribute or closure */}
  </Pressable>
)}
```

### Avoid Inline Styles

```typescript
// ❌ Bad - creates new style object every render
<View style={{ padding: 16, backgroundColor: '#fff' }}>

// ✅ Good - static stylesheet
const styles = StyleSheet.create({
  container: {
    padding: 16,
    backgroundColor: '#fff',
  },
});

<View style={styles.container}>

// ✅ Good - memoized dynamic styles
const dynamicStyle = useMemo(() => ({
  backgroundColor: isActive ? '#007AFF' : '#E5E5EA',
}), [isActive]);

<View style={[styles.container, dynamicStyle]}>
```

## List Optimization

### Use FlashList

```typescript
// Replace FlatList with FlashList for better performance
import { FlashList } from '@shopify/flash-list';

function ProductList({ products }: { products: Product[] }) {
  return (
    <FlashList
      data={products}
      renderItem={({ item }) => <ProductCard product={item} />}
      estimatedItemSize={100} // Required: estimate item height
      keyExtractor={(item) => item.id}
    />
  );
}
```

### FlatList Optimization

```typescript
import { FlatList } from 'react-native';

function OptimizedList({ data }) {
  // Stable keyExtractor
  const keyExtractor = useCallback((item: Item) => item.id, []);

  // Memoized renderItem
  const renderItem = useCallback(
    ({ item }: { item: Item }) => <ListItem item={item} />,
    []
  );

  // Item layout for fixed-height items
  const getItemLayout = useCallback(
    (data: Item[] | null, index: number) => ({
      length: ITEM_HEIGHT,
      offset: ITEM_HEIGHT * index,
      index,
    }),
    []
  );

  return (
    <FlatList
      data={data}
      renderItem={renderItem}
      keyExtractor={keyExtractor}
      getItemLayout={getItemLayout}
      // Performance props
      removeClippedSubviews={true}
      maxToRenderPerBatch={10}
      updateCellsBatchingPeriod={50}
      windowSize={5}
      initialNumToRender={10}
    />
  );
}
```

### Virtualization Settings

```typescript
<FlatList
  // Clip items outside viewport
  removeClippedSubviews={true}

  // Items rendered per batch
  maxToRenderPerBatch={10}

  // Time between batch renders (ms)
  updateCellsBatchingPeriod={50}

  // Viewports to render (5 = 2 above + current + 2 below)
  windowSize={5}

  // Initial items to render
  initialNumToRender={10}

  // Items to keep rendered when scrolling away
  // Lower = less memory, but more re-renders
  maxToRenderPerBatch={5}
/>
```

## Image Optimization

### Use expo-image

```typescript
import { Image } from 'expo-image';

function ProductImage({ uri }: { uri: string }) {
  return (
    <Image
      source={{ uri }}
      style={styles.image}
      contentFit="cover"
      placeholder={blurhash}
      transition={200}
      cachePolicy="memory-disk" // Cache aggressively
    />
  );
}

// Blurhash placeholder
const blurhash = 'L6PZfSi_.AyE_3t7t7R**0o#DgR4';
```

### Image Caching Strategy

```typescript
// Preload images
import { Image } from 'expo-image';

async function preloadImages(urls: string[]) {
  await Promise.all(
    urls.map((url) => Image.prefetch(url))
  );
}

// Use in component
useEffect(() => {
  const imageUrls = products.map((p) => p.imageUrl);
  preloadImages(imageUrls);
}, [products]);
```

## Animation Optimization

### Use Reanimated

```typescript
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withTiming,
} from 'react-native-reanimated';

function AnimatedCard() {
  const scale = useSharedValue(1);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
  }));

  const handlePressIn = () => {
    scale.value = withSpring(0.95);
  };

  const handlePressOut = () => {
    scale.value = withSpring(1);
  };

  return (
    <Pressable onPressIn={handlePressIn} onPressOut={handlePressOut}>
      <Animated.View style={[styles.card, animatedStyle]}>
        {/* Content */}
      </Animated.View>
    </Pressable>
  );
}
```

### Avoid Layout Animations

```typescript
// ❌ Slow - animating layout properties
const animatedStyle = useAnimatedStyle(() => ({
  width: width.value,
  height: height.value,
  margin: margin.value,
}));

// ✅ Fast - animating transform and opacity
const animatedStyle = useAnimatedStyle(() => ({
  transform: [
    { translateX: x.value },
    { translateY: y.value },
    { scale: scale.value },
  ],
  opacity: opacity.value,
}));
```

## State Management Optimization

### Zustand Selectors

```typescript
import { useShallow } from 'zustand/react/shallow';

// ❌ Bad - subscribes to entire store
const { items, addItem, removeItem } = useCartStore();

// ✅ Good - only subscribes to items
const items = useCartStore((state) => state.items);

// ✅ Good - multiple selectors with shallow compare
const { items, total } = useCartStore(
  useShallow((state) => ({
    items: state.items,
    total: state.total,
  }))
);
```

### React Query Optimization

```typescript
import { useQuery } from '@tanstack/react-query';

function useProducts() {
  return useQuery({
    queryKey: ['products'],
    queryFn: fetchProducts,
    // Only re-render when data changes
    notifyOnChangeProps: ['data', 'error'],
    // Select specific data
    select: (data) => data.filter((p) => p.isActive),
    // Stale time to reduce refetches
    staleTime: 1000 * 60 * 5,
  });
}
```

## Bundle Size Optimization

### Tree Shaking Imports

```typescript
// ❌ Bad - imports entire library
import { Button, Text, View } from 'react-native';
import _ from 'lodash';

// ✅ Good - specific imports
import { Button, Text, View } from 'react-native';
import debounce from 'lodash/debounce';
```

### Lazy Loading Screens

```typescript
// src/navigation/MainNavigator.tsx
import { lazy, Suspense } from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';

// Lazy load heavy screens
const ProductDetail = lazy(() => import('@/screens/ProductDetail'));
const Checkout = lazy(() => import('@/screens/Checkout'));

const Stack = createNativeStackNavigator();

function MainNavigator() {
  return (
    <Stack.Navigator>
      <Stack.Screen name="Home" component={HomeScreen} />
      <Stack.Screen
        name="ProductDetail"
        component={(props) => (
          <Suspense fallback={<LoadingScreen />}>
            <ProductDetail {...props} />
          </Suspense>
        )}
      />
    </Stack.Navigator>
  );
}
```

## Memory Management

### Clean Up Effects

```typescript
function useWebSocket(url: string) {
  const [messages, setMessages] = useState<Message[]>([]);

  useEffect(() => {
    const ws = new WebSocket(url);

    ws.onmessage = (event) => {
      setMessages((prev) => [...prev, JSON.parse(event.data)]);
    };

    // Clean up on unmount
    return () => {
      ws.close();
    };
  }, [url]);

  return messages;
}
```

### Avoid Memory Leaks

```typescript
function useAsyncData(id: string) {
  const [data, setData] = useState(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;

    fetchData(id).then((result) => {
      // Only update if still mounted
      if (mountedRef.current) {
        setData(result);
      }
    });

    return () => {
      mountedRef.current = false;
    };
  }, [id]);

  return data;
}
```

## Profiling Tools

### React DevTools Profiler

```bash
# Enable profiler in development
# Use React DevTools Chrome extension
```

### Flipper

```typescript
// Enable Flipper for debugging
// Already configured in React Native 0.62+
```

### Performance Monitoring

```typescript
// src/lib/performance.ts
import * as Sentry from '@sentry/react-native';

// Track slow renders
export function measureRender(name: string) {
  const start = performance.now();

  return () => {
    const duration = performance.now() - start;
    if (duration > 16) {
      // Longer than one frame
      console.warn(`Slow render: ${name} took ${duration.toFixed(2)}ms`);
      Sentry.addBreadcrumb({
        category: 'performance',
        message: `Slow render: ${name}`,
        data: { duration },
      });
    }
  };
}

// Usage
function ExpensiveComponent() {
  const endMeasure = measureRender('ExpensiveComponent');

  // ... render logic

  useEffect(() => {
    endMeasure();
  });
}
```

## Best Practices Summary

1. **Memoize**: Use memo, useMemo, useCallback appropriately
2. **Lists**: Use FlashList, optimize FlatList props
3. **Images**: Use expo-image with caching and placeholders
4. **Animations**: Use Reanimated, animate only transform/opacity
5. **State**: Use selectors, avoid unnecessary subscriptions
6. **Bundle**: Tree shake imports, lazy load screens
7. **Memory**: Clean up effects, check for leaks
8. **Profile**: Use DevTools and Flipper regularly
