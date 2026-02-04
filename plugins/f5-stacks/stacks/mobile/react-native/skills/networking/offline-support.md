---
name: rn-offline-support
description: Offline-first patterns for React Native apps
applies_to: react-native
---

# Offline Support

## Network Status Detection

```typescript
// src/hooks/useNetworkStatus.ts
import { useState, useEffect } from 'react';
import NetInfo, { NetInfoState } from '@react-native-community/netinfo';

interface NetworkStatus {
  isConnected: boolean;
  isInternetReachable: boolean | null;
  type: string;
}

export function useNetworkStatus(): NetworkStatus {
  const [status, setStatus] = useState<NetworkStatus>({
    isConnected: true,
    isInternetReachable: true,
    type: 'unknown',
  });

  useEffect(() => {
    const unsubscribe = NetInfo.addEventListener((state: NetInfoState) => {
      setStatus({
        isConnected: state.isConnected ?? false,
        isInternetReachable: state.isInternetReachable,
        type: state.type,
      });
    });

    return () => unsubscribe();
  }, []);

  return status;
}

// Usage
function App() {
  const { isConnected } = useNetworkStatus();

  return (
    <View>
      {!isConnected && <OfflineBanner />}
      {/* App content */}
    </View>
  );
}
```

## Offline Banner Component

```typescript
// src/components/OfflineBanner.tsx
import { View, Text, StyleSheet, Animated } from 'react-native';
import { useEffect, useRef } from 'react';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

export function OfflineBanner() {
  const insets = useSafeAreaInsets();
  const slideAnim = useRef(new Animated.Value(-60)).current;

  useEffect(() => {
    Animated.spring(slideAnim, {
      toValue: 0,
      useNativeDriver: true,
    }).start();
  }, []);

  return (
    <Animated.View
      style={[
        styles.container,
        { paddingTop: insets.top, transform: [{ translateY: slideAnim }] },
      ]}
    >
      <Ionicons name="cloud-offline" size={18} color="#fff" />
      <Text style={styles.text}>No internet connection</Text>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    backgroundColor: '#FF3B30',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingBottom: 8,
    gap: 8,
    zIndex: 1000,
  },
  text: {
    color: '#fff',
    fontWeight: '500',
  },
});
```

## TanStack Query Offline Configuration

```typescript
// src/lib/queryClient.ts
import { QueryClient, onlineManager } from '@tanstack/react-query';
import NetInfo from '@react-native-community/netinfo';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { createAsyncStoragePersister } from '@tanstack/query-async-storage-persister';
import { PersistQueryClientProvider } from '@tanstack/react-query-persist-client';

// Configure online manager
onlineManager.setEventListener((setOnline) => {
  return NetInfo.addEventListener((state) => {
    setOnline(!!state.isConnected);
  });
});

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      gcTime: 1000 * 60 * 60 * 24, // 24 hours
      retry: 3,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      networkMode: 'offlineFirst', // Use cache when offline
    },
    mutations: {
      networkMode: 'offlineFirst',
      retry: 3,
    },
  },
});

// Async storage persister for query cache
export const asyncStoragePersister = createAsyncStoragePersister({
  storage: AsyncStorage,
  key: 'REACT_QUERY_CACHE',
});

// App wrapper with persistence
export function QueryProvider({ children }: { children: React.ReactNode }) {
  return (
    <PersistQueryClientProvider
      client={queryClient}
      persistOptions={{ persister: asyncStoragePersister }}
    >
      {children}
    </PersistQueryClientProvider>
  );
}
```

## Offline-First Data Fetching

```typescript
// src/features/products/hooks/useProducts.ts
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import AsyncStorage from '@react-native-async-storage/async-storage';

const CACHE_KEY = 'products_cache';

export function useProducts() {
  return useQuery({
    queryKey: ['products'],
    queryFn: async () => {
      const { data } = await api.get('/products');

      // Cache for offline use
      await AsyncStorage.setItem(CACHE_KEY, JSON.stringify(data));

      return data;
    },
    // Use cached data as placeholder while fetching
    placeholderData: async () => {
      const cached = await AsyncStorage.getItem(CACHE_KEY);
      return cached ? JSON.parse(cached) : undefined;
    },
    staleTime: 1000 * 60 * 5, // Consider data fresh for 5 minutes
  });
}
```

## Offline Mutation Queue

```typescript
// src/lib/offlineMutationQueue.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';
import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-community/netinfo';

const PENDING_MUTATIONS_KEY = 'pending_mutations';

interface PendingMutation {
  id: string;
  endpoint: string;
  method: 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  data: any;
  timestamp: number;
}

// Store mutation for later execution
async function queueMutation(mutation: Omit<PendingMutation, 'id' | 'timestamp'>) {
  const pending = await getPendingMutations();
  const newMutation: PendingMutation = {
    ...mutation,
    id: Date.now().toString(),
    timestamp: Date.now(),
  };
  await AsyncStorage.setItem(
    PENDING_MUTATIONS_KEY,
    JSON.stringify([...pending, newMutation])
  );
  return newMutation;
}

async function getPendingMutations(): Promise<PendingMutation[]> {
  const data = await AsyncStorage.getItem(PENDING_MUTATIONS_KEY);
  return data ? JSON.parse(data) : [];
}

async function removePendingMutation(id: string) {
  const pending = await getPendingMutations();
  await AsyncStorage.setItem(
    PENDING_MUTATIONS_KEY,
    JSON.stringify(pending.filter((m) => m.id !== id))
  );
}

// Hook to create offline-capable mutations
export function useOfflineMutation<TData, TVariables>({
  mutationFn,
  endpoint,
  method,
  onSuccess,
  onError,
}: {
  mutationFn: (variables: TVariables) => Promise<TData>;
  endpoint: string;
  method: 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  onSuccess?: (data: TData) => void;
  onError?: (error: Error) => void;
}) {
  return useMutation({
    mutationFn: async (variables: TVariables) => {
      const state = await NetInfo.fetch();

      if (!state.isConnected) {
        // Queue for later
        await queueMutation({ endpoint, method, data: variables });
        throw new Error('OFFLINE_QUEUED');
      }

      return mutationFn(variables);
    },
    onSuccess,
    onError: (error) => {
      if (error.message === 'OFFLINE_QUEUED') {
        // Show success with "will sync" message
        return;
      }
      onError?.(error);
    },
  });
}

// Sync pending mutations when online
export async function syncPendingMutations() {
  const state = await NetInfo.fetch();
  if (!state.isConnected) return;

  const pending = await getPendingMutations();

  for (const mutation of pending) {
    try {
      await api.request({
        method: mutation.method,
        url: mutation.endpoint,
        data: mutation.data,
      });
      await removePendingMutation(mutation.id);
    } catch (error) {
      console.error('Failed to sync mutation:', mutation.id, error);
    }
  }
}
```

## Sync Manager

```typescript
// src/lib/syncManager.ts
import NetInfo from '@react-native-community/netinfo';
import { syncPendingMutations } from './offlineMutationQueue';
import { queryClient } from './queryClient';

class SyncManager {
  private isInitialized = false;

  initialize() {
    if (this.isInitialized) return;

    NetInfo.addEventListener((state) => {
      if (state.isConnected) {
        this.syncAll();
      }
    });

    this.isInitialized = true;
  }

  async syncAll() {
    try {
      // Sync pending mutations first
      await syncPendingMutations();

      // Then refresh critical queries
      await queryClient.invalidateQueries({
        queryKey: ['products'],
        refetchType: 'all',
      });
      await queryClient.invalidateQueries({
        queryKey: ['user'],
        refetchType: 'all',
      });
    } catch (error) {
      console.error('Sync failed:', error);
    }
  }
}

export const syncManager = new SyncManager();

// Initialize in App.tsx
useEffect(() => {
  syncManager.initialize();
}, []);
```

## Optimistic Updates with Rollback

```typescript
// src/features/todos/hooks/useToggleTodo.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useNetworkStatus } from '@/hooks/useNetworkStatus';

export function useToggleTodo() {
  const queryClient = useQueryClient();
  const { isConnected } = useNetworkStatus();

  return useMutation({
    mutationFn: async (todoId: string) => {
      if (!isConnected) {
        // Queue for later but don't fail
        await queueMutation({
          endpoint: `/todos/${todoId}/toggle`,
          method: 'PATCH',
          data: {},
        });
        return { queued: true };
      }

      const { data } = await api.patch(`/todos/${todoId}/toggle`);
      return data;
    },

    // Optimistic update
    onMutate: async (todoId) => {
      await queryClient.cancelQueries({ queryKey: ['todos'] });

      const previousTodos = queryClient.getQueryData<Todo[]>(['todos']);

      queryClient.setQueryData<Todo[]>(['todos'], (old) =>
        old?.map((todo) =>
          todo.id === todoId
            ? { ...todo, completed: !todo.completed, pending: !isConnected }
            : todo
        )
      );

      return { previousTodos };
    },

    // Rollback on error
    onError: (err, todoId, context) => {
      if (context?.previousTodos) {
        queryClient.setQueryData(['todos'], context.previousTodos);
      }
    },

    onSettled: () => {
      if (isConnected) {
        queryClient.invalidateQueries({ queryKey: ['todos'] });
      }
    },
  });
}
```

## Offline Storage with MMKV

```typescript
// src/lib/offlineStorage.ts
import { MMKV } from 'react-native-mmkv';

const storage = new MMKV({ id: 'offline-storage' });

export const offlineStorage = {
  set: <T>(key: string, value: T) => {
    storage.set(key, JSON.stringify(value));
  },

  get: <T>(key: string): T | null => {
    const value = storage.getString(key);
    return value ? JSON.parse(value) : null;
  },

  delete: (key: string) => {
    storage.delete(key);
  },

  // Store with timestamp for freshness check
  setWithTimestamp: <T>(key: string, value: T) => {
    storage.set(
      key,
      JSON.stringify({
        data: value,
        timestamp: Date.now(),
      })
    );
  },

  getIfFresh: <T>(key: string, maxAgeMs: number): T | null => {
    const raw = storage.getString(key);
    if (!raw) return null;

    const { data, timestamp } = JSON.parse(raw);
    if (Date.now() - timestamp > maxAgeMs) return null;

    return data;
  },
};
```

## Best Practices

1. **Detect Network Status**: Use @react-native-community/netinfo
2. **Visual Feedback**: Show offline banner/indicator
3. **Cache Critical Data**: Persist important queries with TanStack Query
4. **Queue Mutations**: Store failed mutations for retry
5. **Sync on Reconnect**: Process queue when connection restores
6. **Optimistic Updates**: Update UI immediately, rollback on error
7. **Freshness Checks**: Don't show stale data without indication
8. **User Communication**: Inform users about sync status
