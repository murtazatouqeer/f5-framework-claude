---
name: rn-flashlist
description: FlashList high-performance list component for React Native
applies_to: react-native
---

# FlashList

## Overview

FlashList by Shopify is a high-performance replacement for FlatList. It uses cell recycling like native lists, achieving up to 10x better performance.

## Installation

```bash
npm install @shopify/flash-list
```

## Basic Usage

```typescript
import { FlashList } from '@shopify/flash-list';

interface Product {
  id: string;
  name: string;
  price: number;
}

function ProductList({ products }: { products: Product[] }) {
  return (
    <FlashList
      data={products}
      renderItem={({ item }) => <ProductCard product={item} />}
      estimatedItemSize={100} // Required: estimated height of items
      keyExtractor={(item) => item.id}
    />
  );
}
```

## Estimated Item Size

The `estimatedItemSize` prop is required and crucial for performance:

```typescript
// Fixed height items - use exact height
<FlashList
  data={data}
  renderItem={renderItem}
  estimatedItemSize={80} // Exact item height
/>

// Variable height items - use average
<FlashList
  data={data}
  renderItem={renderItem}
  estimatedItemSize={150} // Average height
/>

// Calculate from data
const averageItemSize = useMemo(() => {
  if (data.length === 0) return 100;
  // Calculate based on content length
  const totalEstimated = data.reduce((sum, item) => {
    const baseHeight = 80;
    const descriptionLines = Math.ceil(item.description.length / 40);
    return sum + baseHeight + descriptionLines * 20;
  }, 0);
  return totalEstimated / data.length;
}, [data]);

<FlashList
  data={data}
  renderItem={renderItem}
  estimatedItemSize={averageItemSize}
/>
```

## Item Types for Better Performance

When you have different item types, specify them:

```typescript
interface ListItem {
  id: string;
  type: 'header' | 'product' | 'separator';
  data?: any;
}

function MixedList({ items }: { items: ListItem[] }) {
  const renderItem = ({ item }: { item: ListItem }) => {
    switch (item.type) {
      case 'header':
        return <SectionHeader title={item.data.title} />;
      case 'product':
        return <ProductCard product={item.data} />;
      case 'separator':
        return <Separator />;
    }
  };

  // Tell FlashList about item types for better recycling
  const getItemType = (item: ListItem) => item.type;

  return (
    <FlashList
      data={items}
      renderItem={renderItem}
      getItemType={getItemType}
      estimatedItemSize={100}
    />
  );
}
```

## Horizontal List

```typescript
function HorizontalProductList({ products }: { products: Product[] }) {
  return (
    <FlashList
      data={products}
      renderItem={({ item }) => <ProductCard product={item} />}
      horizontal
      estimatedItemSize={150} // Width for horizontal
      showsHorizontalScrollIndicator={false}
    />
  );
}
```

## Grid Layout

```typescript
function ProductGrid({ products }: { products: Product[] }) {
  return (
    <FlashList
      data={products}
      renderItem={({ item }) => (
        <View style={styles.gridItem}>
          <ProductCard product={item} />
        </View>
      )}
      numColumns={2}
      estimatedItemSize={200} // Height of grid row
    />
  );
}

const styles = StyleSheet.create({
  gridItem: {
    flex: 1,
    padding: 8,
  },
});
```

## Pull to Refresh

```typescript
function RefreshableList({ products, onRefresh }) {
  const [refreshing, setRefreshing] = useState(false);

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    await onRefresh();
    setRefreshing(false);
  }, [onRefresh]);

  return (
    <FlashList
      data={products}
      renderItem={({ item }) => <ProductCard product={item} />}
      estimatedItemSize={100}
      refreshing={refreshing}
      onRefresh={handleRefresh}
    />
  );
}
```

## Infinite Scroll / Load More

```typescript
function InfiniteList() {
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteProducts();

  const products = data?.pages.flatMap((page) => page.items) ?? [];

  const handleEndReached = () => {
    if (hasNextPage && !isFetchingNextPage) {
      fetchNextPage();
    }
  };

  return (
    <FlashList
      data={products}
      renderItem={({ item }) => <ProductCard product={item} />}
      estimatedItemSize={100}
      onEndReached={handleEndReached}
      onEndReachedThreshold={0.5}
      ListFooterComponent={
        isFetchingNextPage ? <ActivityIndicator /> : null
      }
    />
  );
}
```

## Headers, Footers, and Empty State

```typescript
function ProductList({ products, isLoading }) {
  return (
    <FlashList
      data={products}
      renderItem={({ item }) => <ProductCard product={item} />}
      estimatedItemSize={100}
      ListHeaderComponent={
        <View style={styles.header}>
          <Text style={styles.title}>Products</Text>
          <FilterBar />
        </View>
      }
      ListFooterComponent={
        isLoading ? <LoadingFooter /> : <View style={styles.footer} />
      }
      ListEmptyComponent={
        <EmptyState
          icon="cube-outline"
          title="No products found"
          description="Try adjusting your filters"
        />
      }
    />
  );
}
```

## Sticky Headers

```typescript
interface Section {
  title: string;
  data: Product[];
}

function SectionedList({ sections }: { sections: Section[] }) {
  // Flatten sections with headers
  const flatData = sections.flatMap((section) => [
    { type: 'header', title: section.title },
    ...section.data.map((item) => ({ type: 'item', ...item })),
  ]);

  // Track sticky header indices
  const stickyHeaderIndices = flatData
    .map((item, index) => (item.type === 'header' ? index : null))
    .filter((index) => index !== null) as number[];

  return (
    <FlashList
      data={flatData}
      renderItem={({ item }) =>
        item.type === 'header' ? (
          <SectionHeader title={item.title} />
        ) : (
          <ProductCard product={item} />
        )
      }
      getItemType={(item) => item.type}
      estimatedItemSize={100}
      stickyHeaderIndices={stickyHeaderIndices}
    />
  );
}
```

## Scroll to Item

```typescript
function SearchableList({ products }) {
  const listRef = useRef<FlashList<Product>>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const handleSearch = (query: string) => {
    setSearchQuery(query);

    // Find and scroll to matching item
    const index = products.findIndex((p) =>
      p.name.toLowerCase().includes(query.toLowerCase())
    );

    if (index !== -1) {
      listRef.current?.scrollToIndex({
        index,
        animated: true,
        viewPosition: 0, // 0 = top, 0.5 = center, 1 = bottom
      });
    }
  };

  return (
    <View style={styles.container}>
      <SearchInput onSearch={handleSearch} />
      <FlashList
        ref={listRef}
        data={products}
        renderItem={({ item }) => <ProductCard product={item} />}
        estimatedItemSize={100}
      />
    </View>
  );
}
```

## Performance Optimization

```typescript
function OptimizedList({ products }) {
  // Stable renderItem function
  const renderItem = useCallback(
    ({ item }: { item: Product }) => <ProductCard product={item} />,
    []
  );

  // Stable keyExtractor
  const keyExtractor = useCallback((item: Product) => item.id, []);

  return (
    <FlashList
      data={products}
      renderItem={renderItem}
      keyExtractor={keyExtractor}
      estimatedItemSize={100}
      // Performance props
      drawDistance={250} // Pixels to render beyond visible area
      overrideItemLayout={(layout, item, index, maxColumns) => {
        // Override for specific items if needed
        if (item.type === 'header') {
          layout.size = 50;
        }
      }}
    />
  );
}
```

## Debugging Performance

```typescript
// Check blank area metrics
<FlashList
  data={products}
  renderItem={renderItem}
  estimatedItemSize={100}
  onBlankArea={(blankArea) => {
    if (blankArea > 0) {
      console.warn(`Blank area detected: ${blankArea}px`);
      // Consider:
      // 1. Increase estimatedItemSize
      // 2. Increase drawDistance
      // 3. Simplify renderItem
    }
  }}
/>
```

## Migration from FlatList

```typescript
// FlatList
<FlatList
  data={products}
  renderItem={({ item }) => <ProductCard product={item} />}
  keyExtractor={(item) => item.id}
  removeClippedSubviews
  maxToRenderPerBatch={10}
  windowSize={5}
/>

// FlashList - simpler props, better performance
<FlashList
  data={products}
  renderItem={({ item }) => <ProductCard product={item} />}
  keyExtractor={(item) => item.id}
  estimatedItemSize={100} // Add this
/>
```

## Best Practices

1. **estimatedItemSize**: Always provide accurate estimate
2. **getItemType**: Use when mixing different item types
3. **Stable Functions**: Memoize renderItem and keyExtractor
4. **Simple Items**: Keep renderItem components lean
5. **Avoid Inline Styles**: Use StyleSheet for item styles
6. **Key Extraction**: Use unique, stable keys
7. **Monitor Blanks**: Check onBlankArea in development
8. **Test on Device**: Always test performance on real devices
