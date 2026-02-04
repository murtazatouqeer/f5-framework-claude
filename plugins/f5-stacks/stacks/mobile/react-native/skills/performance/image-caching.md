---
name: rn-image-caching
description: Image caching and optimization with expo-image
applies_to: react-native
---

# Image Caching with expo-image

## Installation

```bash
npx expo install expo-image
```

## Basic Usage

```typescript
import { Image } from 'expo-image';
import { StyleSheet } from 'react-native';

function ProductImage({ uri }: { uri: string }) {
  return (
    <Image
      source={{ uri }}
      style={styles.image}
      contentFit="cover"
    />
  );
}

const styles = StyleSheet.create({
  image: {
    width: '100%',
    height: 200,
  },
});
```

## Content Fit Options

```typescript
import { Image, ImageContentFit } from 'expo-image';

// cover - Scales to fill, may crop
<Image source={{ uri }} contentFit="cover" />

// contain - Scales to fit, may have letterboxing
<Image source={{ uri }} contentFit="contain" />

// fill - Stretches to fill (may distort)
<Image source={{ uri }} contentFit="fill" />

// none - No scaling
<Image source={{ uri }} contentFit="none" />

// scale-down - Like contain but never scales up
<Image source={{ uri }} contentFit="scale-down" />
```

## Placeholder and Transitions

```typescript
import { Image } from 'expo-image';

// Blurhash placeholder (recommended)
const blurhash = 'L6PZfSi_.AyE_3t7t7R**0o#DgR4';

function ProductImage({ uri }: { uri: string }) {
  return (
    <Image
      source={{ uri }}
      placeholder={blurhash}
      contentFit="cover"
      transition={300} // Fade transition duration in ms
      style={styles.image}
    />
  );
}

// Color placeholder
<Image
  source={{ uri }}
  placeholder="#E5E5EA"
  contentFit="cover"
  style={styles.image}
/>

// Image placeholder
<Image
  source={{ uri }}
  placeholder={require('@/assets/placeholder.png')}
  contentFit="cover"
  style={styles.image}
/>
```

## Caching Strategies

```typescript
import { Image, ImageCacheType } from 'expo-image';

// Memory only - fastest, cleared on app close
<Image source={{ uri }} cachePolicy="memory" />

// Disk only - persists between sessions
<Image source={{ uri }} cachePolicy="disk" />

// Memory and disk (default) - best of both
<Image source={{ uri }} cachePolicy="memory-disk" />

// No caching
<Image source={{ uri }} cachePolicy="none" />
```

## Prefetching Images

```typescript
import { Image } from 'expo-image';

// Prefetch single image
async function prefetchImage(uri: string) {
  await Image.prefetch(uri);
}

// Prefetch multiple images
async function prefetchImages(uris: string[]) {
  await Promise.all(uris.map((uri) => Image.prefetch(uri)));
}

// Usage in component
function ProductList({ products }: { products: Product[] }) {
  useEffect(() => {
    // Prefetch first 10 product images
    const imageUrls = products.slice(0, 10).map((p) => p.imageUrl);
    prefetchImages(imageUrls);
  }, [products]);

  return (
    <FlashList
      data={products}
      renderItem={({ item }) => <ProductCard product={item} />}
      estimatedItemSize={100}
    />
  );
}
```

## Cache Management

```typescript
import { Image } from 'expo-image';

// Get cache size
async function getCacheSize() {
  const size = await Image.getCachePathAsync();
  console.log('Cache path:', size);
}

// Clear all cache
async function clearImageCache() {
  await Image.clearDiskCache();
  await Image.clearMemoryCache();
}

// Clear specific image from cache
// Not directly supported, but you can use a cache-busting URL
function getCacheBustedUrl(url: string): string {
  const separator = url.includes('?') ? '&' : '?';
  return `${url}${separator}v=${Date.now()}`;
}
```

## Responsive Images

```typescript
import { Image } from 'expo-image';
import { useWindowDimensions } from 'react-native';

function ResponsiveImage({ baseUrl }: { baseUrl: string }) {
  const { width } = useWindowDimensions();

  // Select appropriate image size based on screen width
  const imageUrl = useMemo(() => {
    if (width <= 375) return `${baseUrl}?w=375`;
    if (width <= 768) return `${baseUrl}?w=768`;
    return `${baseUrl}?w=1024`;
  }, [baseUrl, width]);

  return (
    <Image
      source={{ uri: imageUrl }}
      contentFit="cover"
      style={styles.image}
    />
  );
}
```

## Loading and Error States

```typescript
import { Image, ImageLoadEventData, ImageErrorEventData } from 'expo-image';
import { useState } from 'react';

function ProductImage({ uri }: { uri: string }) {
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);

  const handleLoad = (event: ImageLoadEventData) => {
    setIsLoading(false);
    console.log('Image dimensions:', event.source);
  };

  const handleError = (event: ImageErrorEventData) => {
    setIsLoading(false);
    setHasError(true);
    console.error('Image failed to load:', event.error);
  };

  if (hasError) {
    return (
      <View style={[styles.image, styles.errorContainer]}>
        <Ionicons name="image-outline" size={48} color="#999" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Image
        source={{ uri }}
        style={styles.image}
        contentFit="cover"
        onLoad={handleLoad}
        onError={handleError}
      />
      {isLoading && (
        <ActivityIndicator style={styles.loader} />
      )}
    </View>
  );
}
```

## Avatar Component

```typescript
import { Image } from 'expo-image';
import { View, Text, StyleSheet } from 'react-native';

interface AvatarProps {
  uri?: string;
  name: string;
  size?: number;
}

export function Avatar({ uri, name, size = 40 }: AvatarProps) {
  const initials = name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);

  const containerStyle = {
    width: size,
    height: size,
    borderRadius: size / 2,
  };

  if (!uri) {
    return (
      <View style={[styles.placeholder, containerStyle]}>
        <Text style={[styles.initials, { fontSize: size * 0.4 }]}>
          {initials}
        </Text>
      </View>
    );
  }

  return (
    <Image
      source={{ uri }}
      style={containerStyle}
      contentFit="cover"
      placeholder="#E5E5EA"
      transition={200}
    />
  );
}

const styles = StyleSheet.create({
  placeholder: {
    backgroundColor: '#007AFF',
    alignItems: 'center',
    justifyContent: 'center',
  },
  initials: {
    color: '#fff',
    fontWeight: '600',
  },
});
```

## Gallery with Zoom

```typescript
import { Image } from 'expo-image';
import { Modal, Pressable, View, Dimensions } from 'react-native';
import { GestureDetector, Gesture } from 'react-native-gesture-handler';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
} from 'react-native-reanimated';

const { width, height } = Dimensions.get('window');

function ZoomableImage({ uri }: { uri: string }) {
  const scale = useSharedValue(1);
  const savedScale = useSharedValue(1);

  const pinchGesture = Gesture.Pinch()
    .onUpdate((e) => {
      scale.value = savedScale.value * e.scale;
    })
    .onEnd(() => {
      if (scale.value < 1) {
        scale.value = 1;
      }
      savedScale.value = scale.value;
    });

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
  }));

  return (
    <GestureDetector gesture={pinchGesture}>
      <Animated.View style={animatedStyle}>
        <Image
          source={{ uri }}
          style={{ width, height: height * 0.8 }}
          contentFit="contain"
        />
      </Animated.View>
    </GestureDetector>
  );
}
```

## Blurhash Generation

Generate blurhash for your images server-side:

```typescript
// Server-side (Node.js)
import { encode } from 'blurhash';
import sharp from 'sharp';

async function generateBlurhash(imagePath: string): Promise<string> {
  const { data, info } = await sharp(imagePath)
    .raw()
    .ensureAlpha()
    .resize(32, 32, { fit: 'inside' })
    .toBuffer({ resolveWithObject: true });

  return encode(
    new Uint8ClampedArray(data),
    info.width,
    info.height,
    4, // x components
    3  // y components
  );
}
```

## Performance Tips

```typescript
// 1. Use appropriate image sizes
// Don't load 4K images for thumbnails
const thumbnailUrl = `${baseUrl}?w=150&q=80`;
const fullUrl = `${baseUrl}?w=1024&q=90`;

// 2. Use WebP format when possible
// WebP provides better compression

// 3. Lazy load off-screen images
// FlashList handles this automatically

// 4. Set explicit dimensions
// Avoids layout shifts
<Image
  source={{ uri }}
  style={{ width: 200, height: 200 }} // Explicit dimensions
/>

// 5. Use priority for important images
<Image
  source={{ uri }}
  priority="high" // 'low' | 'normal' | 'high'
/>
```

## Best Practices

1. **Blurhash**: Use for smooth placeholder transitions
2. **Prefetch**: Preload images user is likely to view
3. **Right Size**: Request appropriately sized images
4. **Cache Strategy**: Use memory-disk for most cases
5. **Error Handling**: Always handle image load failures
6. **Explicit Dimensions**: Set width/height to avoid layout shifts
7. **WebP Format**: Use WebP for better compression
8. **Clear Cache**: Provide option to clear cache in settings
