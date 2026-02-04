---
name: rn-screen-generator
description: Generate React Native screens with navigation, data fetching, and proper TypeScript types
triggers:
  - "rn screen"
  - "react native screen"
  - "create screen"
  - "generate screen"
applies_to: react-native
---

# React Native Screen Generator

## Purpose

Generate production-ready React Native screens following best practices with:
- TypeScript types for navigation params
- TanStack Query for data fetching
- FlashList for performant lists
- Proper loading, error, and empty states
- Pull-to-refresh and infinite scroll
- Accessibility support

## Input Requirements

```yaml
required:
  - screen_name: string       # e.g., "ProductList", "UserProfile"
  - feature: string           # e.g., "products", "users"

optional:
  - screen_type: list | detail | form | dashboard
  - data_source: api | local | hybrid
  - navigation_type: stack | tab | modal
  - has_search: boolean
  - has_filters: boolean
  - has_infinite_scroll: boolean
```

## Generation Process

### Step 1: Analyze Requirements

```typescript
// Determine screen structure based on type
const screenConfig = {
  list: {
    components: ['FlashList', 'SearchBar', 'FilterSheet', 'EmptyState'],
    hooks: ['useInfiniteQuery', 'useState', 'useCallback'],
    features: ['pull-to-refresh', 'infinite-scroll', 'search'],
  },
  detail: {
    components: ['ScrollView', 'LoadingOverlay', 'ActionButtons'],
    hooks: ['useQuery', 'useMutation'],
    features: ['loading-state', 'error-boundary', 'actions'],
  },
  form: {
    components: ['KeyboardAvoidingView', 'FormFields', 'SubmitButton'],
    hooks: ['useForm', 'useMutation'],
    features: ['validation', 'keyboard-handling', 'submission'],
  },
};
```

### Step 2: Generate Screen

```typescript
// src/features/{{feature}}/screens/{{ScreenName}}Screen.tsx
import { useCallback, useState } from 'react';
import {
  View,
  StyleSheet,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { FlashList } from '@shopify/flash-list';
import { useNavigation } from '@react-navigation/native';
import { useInfiniteQuery } from '@tanstack/react-query';

import { get{{Items}} } from '../api/{{feature}}Api';
import { {{Item}}Card } from '../components/{{Item}}Card';
import { {{ScreenName}}Header } from '../components/{{ScreenName}}Header';
import { EmptyState } from '@/components/ui/EmptyState';
import { ErrorState } from '@/components/ui/ErrorState';
import type { {{Item}} } from '../types';
import type { {{Feature}}NavigationProp } from '@/navigation/types';

export function {{ScreenName}}Screen() {
  const navigation = useNavigation<{{Feature}}NavigationProp>();
  const [searchQuery, setSearchQuery] = useState('');
  const [refreshing, setRefreshing] = useState(false);

  const {
    data,
    isLoading,
    isError,
    error,
    refetch,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteQuery({
    queryKey: ['{{items}}', { search: searchQuery }],
    queryFn: ({ pageParam = 1 }) =>
      get{{Items}}({ page: pageParam, search: searchQuery }),
    getNextPageParam: (lastPage) =>
      lastPage.page < lastPage.totalPages ? lastPage.page + 1 : undefined,
  });

  const items = data?.pages.flatMap((page) => page.items) ?? [];

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    await refetch();
    setRefreshing(false);
  }, [refetch]);

  const handleLoadMore = useCallback(() => {
    if (hasNextPage && !isFetchingNextPage) {
      fetchNextPage();
    }
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);

  const handleItemPress = useCallback(
    (item: {{Item}}) => {
      navigation.navigate('{{Item}}Detail', { id: item.id });
    },
    [navigation]
  );

  const renderItem = useCallback(
    ({ item }: { item: {{Item}} }) => (
      <{{Item}}Card
        item={item}
        onPress={() => handleItemPress(item)}
        testID={`{{item}}-card-${item.id}`}
      />
    ),
    [handleItemPress]
  );

  const renderFooter = useCallback(() => {
    if (!isFetchingNextPage) return null;
    return (
      <View style={styles.footer}>
        <ActivityIndicator size="small" />
      </View>
    );
  }, [isFetchingNextPage]);

  if (isLoading && items.length === 0) {
    return (
      <View style={styles.centered} testID="loading-state">
        <ActivityIndicator size="large" />
      </View>
    );
  }

  if (isError && items.length === 0) {
    return (
      <ErrorState
        message={error?.message ?? 'Something went wrong'}
        onRetry={refetch}
        testID="error-state"
      />
    );
  }

  return (
    <View style={styles.container} testID="{{screen-name}}-screen">
      <{{ScreenName}}Header
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
      />

      <FlashList
        data={items}
        renderItem={renderItem}
        keyExtractor={(item) => item.id}
        estimatedItemSize={100}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
        }
        onEndReached={handleLoadMore}
        onEndReachedThreshold={0.5}
        ListFooterComponent={renderFooter}
        ListEmptyComponent={
          <EmptyState
            title="No {{items}} found"
            description={
              searchQuery
                ? 'Try a different search term'
                : 'No {{items}} available'
            }
            testID="empty-state"
          />
        }
        testID="{{items}}-list"
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  list: {
    padding: 16,
  },
  footer: {
    paddingVertical: 20,
    alignItems: 'center',
  },
});
```

### Step 3: Generate Navigation Types

```typescript
// src/features/{{feature}}/navigation/types.ts
import type { StackNavigationProp } from '@react-navigation/stack';
import type { RouteProp } from '@react-navigation/native';

export type {{Feature}}StackParamList = {
  {{Item}}List: undefined;
  {{Item}}Detail: { id: string };
  {{Item}}Create: undefined;
  {{Item}}Edit: { id: string };
};

export type {{Feature}}NavigationProp = StackNavigationProp<{{Feature}}StackParamList>;

export type {{Item}}DetailRouteProp = RouteProp<{{Feature}}StackParamList, '{{Item}}Detail'>;
export type {{Item}}EditRouteProp = RouteProp<{{Feature}}StackParamList, '{{Item}}Edit'>;
```

## Output Structure

```
src/features/{{feature}}/
├── screens/
│   ├── {{ScreenName}}Screen.tsx
│   └── __tests__/
│       └── {{ScreenName}}Screen.test.tsx
├── components/
│   ├── {{ScreenName}}Header.tsx
│   └── {{Item}}Card.tsx
├── api/
│   └── {{feature}}Api.ts
├── hooks/
│   └── use{{Feature}}.ts
├── navigation/
│   └── types.ts
└── types.ts
```

## Best Practices

1. **Performance**: Use FlashList for lists, memoize callbacks
2. **Accessibility**: Add testID props, accessible labels
3. **Error Handling**: Always show error states with retry
4. **Loading States**: Show skeleton or spinner during load
5. **Empty States**: Provide helpful empty state messages
6. **TypeScript**: Strong typing for navigation and data
