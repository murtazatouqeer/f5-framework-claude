---
name: rn-mmkv
description: MMKV high-performance storage for React Native
applies_to: react-native
---

# MMKV Storage

## Overview

MMKV is a high-performance key-value storage framework by WeChat. It's significantly faster than AsyncStorage due to memory mapping and uses Protocol Buffers for encoding.

## Installation

```bash
npm install react-native-mmkv
npx pod-install # iOS only
```

For Expo managed projects (requires development build):

```bash
npx expo install react-native-mmkv
npx expo prebuild
```

## Basic Setup

```typescript
// src/lib/mmkv.ts
import { MMKV } from 'react-native-mmkv';

// Default instance
export const storage = new MMKV();

// Named instance (isolated storage)
export const userStorage = new MMKV({ id: 'user-storage' });

// Encrypted instance
export const secureStorage = new MMKV({
  id: 'secure-storage',
  encryptionKey: 'your-encryption-key-here',
});
```

## Basic Operations

```typescript
import { storage } from '@/lib/mmkv';

// Strings
storage.set('username', 'john_doe');
const username = storage.getString('username');

// Numbers
storage.set('count', 42);
const count = storage.getNumber('count');

// Booleans
storage.set('isLoggedIn', true);
const isLoggedIn = storage.getBoolean('isLoggedIn');

// Check existence
const exists = storage.contains('username');

// Delete
storage.delete('username');

// Get all keys
const keys = storage.getAllKeys();

// Clear all
storage.clearAll();
```

## JSON Storage Wrapper

```typescript
// src/lib/mmkvStorage.ts
import { MMKV } from 'react-native-mmkv';

const storage = new MMKV();

export const mmkvStorage = {
  set: <T>(key: string, value: T): void => {
    storage.set(key, JSON.stringify(value));
  },

  get: <T>(key: string): T | null => {
    const value = storage.getString(key);
    return value ? JSON.parse(value) : null;
  },

  delete: (key: string): void => {
    storage.delete(key);
  },

  contains: (key: string): boolean => {
    return storage.contains(key);
  },

  getAllKeys: (): string[] => {
    return storage.getAllKeys();
  },

  clearAll: (): void => {
    storage.clearAll();
  },
};

// Usage
interface User {
  id: string;
  name: string;
  email: string;
}

mmkvStorage.set<User>('user', { id: '1', name: 'John', email: 'john@example.com' });
const user = mmkvStorage.get<User>('user');
```

## Zustand Persistence with MMKV

```typescript
// src/stores/useAuthStore.ts
import { create } from 'zustand';
import { persist, createJSONStorage, StateStorage } from 'zustand/middleware';
import { MMKV } from 'react-native-mmkv';

const storage = new MMKV({ id: 'auth-storage' });

// Create Zustand-compatible storage adapter
const mmkvStateStorage: StateStorage = {
  getItem: (name) => {
    const value = storage.getString(name);
    return value ?? null;
  },
  setItem: (name, value) => {
    storage.set(name, value);
  },
  removeItem: (name) => {
    storage.delete(name);
  },
};

interface AuthState {
  token: string | null;
  user: User | null;
  setAuth: (token: string, user: User) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      setAuth: (token, user) => set({ token, user }),
      logout: () => set({ token: null, user: null }),
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => mmkvStateStorage),
    }
  )
);
```

## TanStack Query Persistence with MMKV

```typescript
// src/lib/queryClient.ts
import { QueryClient } from '@tanstack/react-query';
import { createSyncStoragePersister } from '@tanstack/query-sync-storage-persister';
import { persistQueryClient } from '@tanstack/react-query-persist-client';
import { MMKV } from 'react-native-mmkv';

const storage = new MMKV({ id: 'query-cache' });

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      gcTime: 1000 * 60 * 60 * 24, // 24 hours
    },
  },
});

// MMKV is synchronous, so use sync persister
const mmkvPersister = createSyncStoragePersister({
  storage: {
    getItem: (key) => storage.getString(key) ?? null,
    setItem: (key, value) => storage.set(key, value),
    removeItem: (key) => storage.delete(key),
  },
});

persistQueryClient({
  queryClient,
  persister: mmkvPersister,
  maxAge: 1000 * 60 * 60 * 24, // 24 hours
});
```

## Hook for MMKV

```typescript
// src/hooks/useMMKV.ts
import { useState, useCallback, useEffect } from 'react';
import { MMKV, useMMKVString, useMMKVNumber, useMMKVBoolean } from 'react-native-mmkv';

const storage = new MMKV();

// Built-in hooks from react-native-mmkv
export function useUsername() {
  const [username, setUsername] = useMMKVString('username', storage);
  return { username, setUsername };
}

export function useCount() {
  const [count, setCount] = useMMKVNumber('count', storage);
  return { count, setCount };
}

export function useIsLoggedIn() {
  const [isLoggedIn, setIsLoggedIn] = useMMKVBoolean('isLoggedIn', storage);
  return { isLoggedIn, setIsLoggedIn };
}

// Custom hook for JSON objects
export function useMMKVObject<T>(key: string, initialValue: T) {
  const [value, setValue] = useState<T>(initialValue);

  useEffect(() => {
    const stored = storage.getString(key);
    if (stored) {
      setValue(JSON.parse(stored));
    }
  }, [key]);

  const setStoredValue = useCallback(
    (newValue: T | ((prev: T) => T)) => {
      setValue((prev) => {
        const finalValue =
          newValue instanceof Function ? newValue(prev) : newValue;
        storage.set(key, JSON.stringify(finalValue));
        return finalValue;
      });
    },
    [key]
  );

  return [value, setStoredValue] as const;
}

// Usage
function ProfileScreen() {
  const [user, setUser] = useMMKVObject<User>('user', { id: '', name: '', email: '' });

  return (
    <View>
      <Text>{user.name}</Text>
      <Button
        title="Update Name"
        onPress={() => setUser((prev) => ({ ...prev, name: 'New Name' }))}
      />
    </View>
  );
}
```

## Storage with Listeners

```typescript
// src/lib/mmkvListeners.ts
import { MMKV } from 'react-native-mmkv';

const storage = new MMKV();

// Add listener for changes
const listener = storage.addOnValueChangedListener((key) => {
  console.log(`Value for "${key}" changed!`);

  // React to specific key changes
  if (key === 'authToken') {
    const token = storage.getString('authToken');
    if (!token) {
      // Token was removed, handle logout
      console.log('User logged out');
    }
  }
});

// Remove listener when done
listener.remove();
```

## Multiple Storage Instances

```typescript
// src/lib/storageInstances.ts
import { MMKV } from 'react-native-mmkv';

// User data (cleared on logout)
export const userStorage = new MMKV({ id: 'user' });

// App settings (persists across sessions)
export const settingsStorage = new MMKV({ id: 'settings' });

// Cache (can be cleared without affecting user data)
export const cacheStorage = new MMKV({ id: 'cache' });

// Secure data (encrypted)
export const secureStorage = new MMKV({
  id: 'secure',
  encryptionKey: 'your-32-character-encryption-key',
});

// Clear user data on logout
export function clearUserData() {
  userStorage.clearAll();
}

// Clear cache
export function clearCache() {
  cacheStorage.clearAll();
}
```

## Performance Comparison

| Operation | AsyncStorage | MMKV |
|-----------|-------------|------|
| Write 1KB | ~8ms | ~0.1ms |
| Read 1KB | ~4ms | ~0.05ms |
| Write 10KB | ~40ms | ~0.3ms |
| Read 10KB | ~10ms | ~0.1ms |

MMKV is typically 30-100x faster than AsyncStorage.

## Best Practices

1. **Use MMKV for Frequent Access**: Ideal for state that changes often
2. **Separate Instances**: Use different instances for different purposes
3. **Encrypt Sensitive Data**: Use encryptionKey for sensitive storage
4. **Synchronous API**: Take advantage of sync operations for simpler code
5. **Built-in Hooks**: Use useMMKV* hooks for reactive state
6. **Listeners**: React to storage changes across the app
7. **Development Build**: Requires expo prebuild for Expo projects

## Migration from AsyncStorage

```typescript
// src/lib/migration.ts
import AsyncStorage from '@react-native-async-storage/async-storage';
import { MMKV } from 'react-native-mmkv';

const mmkv = new MMKV();

export async function migrateFromAsyncStorage() {
  const alreadyMigrated = mmkv.getBoolean('hasMigratedFromAsyncStorage');
  if (alreadyMigrated) return;

  try {
    const keys = await AsyncStorage.getAllKeys();
    const items = await AsyncStorage.multiGet(keys);

    for (const [key, value] of items) {
      if (value !== null) {
        mmkv.set(key, value);
      }
    }

    mmkv.set('hasMigratedFromAsyncStorage', true);
    console.log('Migration complete');
  } catch (error) {
    console.error('Migration failed:', error);
  }
}
```
