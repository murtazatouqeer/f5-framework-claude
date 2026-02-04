---
name: rn-screen
description: React Native screen template with common patterns
applies_to: react-native
variables:
  - name: screenName
    description: Name of the screen (e.g., ProductDetail)
  - name: hasQuery
    description: Include TanStack Query data fetching
  - name: hasForm
    description: Include form with react-hook-form
  - name: hasInfiniteList
    description: Include infinite scroll list
---

# React Native Screen Template

## Basic Screen

```typescript
// src/features/{{feature}}/screens/{{screenName}}Screen.tsx
import { View, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Stack } from 'expo-router';

export function {{screenName}}Screen() {
  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <Stack.Screen options={{ title: '{{screenName}}' }} />
      <View style={styles.content}>
        {/* Screen content */}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  content: {
    flex: 1,
    padding: 16,
  },
});
```

## Screen with Data Fetching

```typescript
// src/features/{{feature}}/screens/{{screenName}}Screen.tsx
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Stack, useLocalSearchParams } from 'expo-router';
import { use{{screenName}} } from '../hooks/use{{screenName}}';
import { ErrorView } from '@/components/ErrorView';

export function {{screenName}}Screen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { data, isLoading, isError, error, refetch } = use{{screenName}}(id);

  if (isLoading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#007AFF" />
      </View>
    );
  }

  if (isError) {
    return (
      <ErrorView
        message={error?.message ?? 'Failed to load data'}
        onRetry={refetch}
      />
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <Stack.Screen options={{ title: data?.title ?? '{{screenName}}' }} />
      <View style={styles.content}>
        <Text style={styles.title}>{data?.title}</Text>
        {/* Additional content */}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  centered: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  content: {
    flex: 1,
    padding: 16,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    marginBottom: 16,
  },
});
```

## Screen with Infinite List

```typescript
// src/features/{{feature}}/screens/{{screenName}}ListScreen.tsx
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { FlashList } from '@shopify/flash-list';
import { use{{screenName}}List } from '../hooks/use{{screenName}}List';
import { {{screenName}}Card } from '../components/{{screenName}}Card';
import { EmptyState } from '@/components/EmptyState';
import { ErrorView } from '@/components/ErrorView';

export function {{screenName}}ListScreen() {
  const {
    data,
    isLoading,
    isError,
    error,
    refetch,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = use{{screenName}}List();

  const items = data?.pages.flatMap((page) => page.items) ?? [];

  if (isLoading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#007AFF" />
      </View>
    );
  }

  if (isError) {
    return (
      <ErrorView
        message={error?.message ?? 'Failed to load data'}
        onRetry={refetch}
      />
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <FlashList
        data={items}
        renderItem={({ item }) => <{{screenName}}Card item={item} />}
        keyExtractor={(item) => item.id}
        estimatedItemSize={100}
        onEndReached={() => hasNextPage && fetchNextPage()}
        onEndReachedThreshold={0.5}
        refreshing={false}
        onRefresh={refetch}
        ListEmptyComponent={
          <EmptyState
            icon="folder-open-outline"
            title="No items found"
            description="Try adjusting your filters"
          />
        }
        ListFooterComponent={
          isFetchingNextPage ? (
            <View style={styles.footer}>
              <ActivityIndicator />
            </View>
          ) : null
        }
        contentContainerStyle={styles.listContent}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  centered: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  listContent: {
    padding: 16,
  },
  footer: {
    padding: 16,
    alignItems: 'center',
  },
});
```

## Screen with Form

```typescript
// src/features/{{feature}}/screens/{{screenName}}FormScreen.tsx
import { View, Text, StyleSheet, ScrollView, Pressable } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Stack, useRouter } from 'expo-router';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { {{screenName}}Schema, {{screenName}}FormData } from '../schemas/{{camelCase screenName}}Schema';
import { useCreate{{screenName}} } from '../hooks/useCreate{{screenName}}';
import { FormInput } from '@/components/form/FormInput';
import { FormPicker } from '@/components/form/FormPicker';

export function {{screenName}}FormScreen() {
  const router = useRouter();
  const mutation = useCreate{{screenName}}();

  const {
    control,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<{{screenName}}FormData>({
    resolver: zodResolver({{screenName}}Schema),
    defaultValues: {
      name: '',
      description: '',
    },
  });

  const onSubmit = async (data: {{screenName}}FormData) => {
    try {
      await mutation.mutateAsync(data);
      router.back();
    } catch (error) {
      // Error handled by mutation
    }
  };

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <Stack.Screen options={{ title: 'Create {{screenName}}' }} />
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.content}
        keyboardShouldPersistTaps="handled"
      >
        <FormInput
          control={control}
          name="name"
          label="Name"
          placeholder="Enter name"
          rules={{ required: 'Name is required' }}
        />

        <FormInput
          control={control}
          name="description"
          label="Description"
          placeholder="Enter description"
          multiline
          numberOfLines={4}
          textAlignVertical="top"
        />

        {mutation.error && (
          <Text style={styles.error}>{mutation.error.message}</Text>
        )}

        <Pressable
          style={[styles.button, isSubmitting && styles.buttonDisabled]}
          onPress={handleSubmit(onSubmit)}
          disabled={isSubmitting}
        >
          <Text style={styles.buttonText}>
            {isSubmitting ? 'Creating...' : 'Create'}
          </Text>
        </Pressable>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  scrollView: {
    flex: 1,
  },
  content: {
    padding: 16,
    gap: 16,
  },
  error: {
    color: '#FF3B30',
    fontSize: 14,
    textAlign: 'center',
  },
  button: {
    backgroundColor: '#007AFF',
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 8,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
```

## Screen with Tabs

```typescript
// src/features/{{feature}}/screens/{{screenName}}TabScreen.tsx
import { View, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { createMaterialTopTabNavigator } from '@react-navigation/material-top-tabs';
import { Tab1Screen } from './Tab1Screen';
import { Tab2Screen } from './Tab2Screen';

const Tab = createMaterialTopTabNavigator();

export function {{screenName}}TabScreen() {
  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <Tab.Navigator
        screenOptions={{
          tabBarLabelStyle: styles.tabLabel,
          tabBarIndicatorStyle: styles.tabIndicator,
          tabBarStyle: styles.tabBar,
        }}
      >
        <Tab.Screen name="Tab1" component={Tab1Screen} />
        <Tab.Screen name="Tab2" component={Tab2Screen} />
      </Tab.Navigator>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  tabBar: {
    backgroundColor: '#fff',
    elevation: 0,
    shadowOpacity: 0,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  tabLabel: {
    fontSize: 14,
    fontWeight: '600',
    textTransform: 'none',
  },
  tabIndicator: {
    backgroundColor: '#007AFF',
    height: 3,
  },
});
```

## Usage

1. Replace `{{feature}}` with feature name (e.g., `products`)
2. Replace `{{screenName}}` with screen name (e.g., `ProductDetail`)
3. Create corresponding hooks and components
4. Add route in navigation configuration
