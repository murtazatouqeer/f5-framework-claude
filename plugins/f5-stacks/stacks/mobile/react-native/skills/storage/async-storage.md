---
name: rn-async-storage
description: AsyncStorage for persistent key-value storage in React Native
applies_to: react-native
---

# AsyncStorage

## Installation

```bash
npx expo install @react-native-async-storage/async-storage
```

## Basic Usage

```typescript
import AsyncStorage from '@react-native-async-storage/async-storage';

// Store string value
await AsyncStorage.setItem('username', 'john_doe');

// Get string value
const username = await AsyncStorage.getItem('username');

// Remove item
await AsyncStorage.removeItem('username');

// Clear all
await AsyncStorage.clear();
```

## JSON Data Storage

```typescript
// src/lib/storage.ts
import AsyncStorage from '@react-native-async-storage/async-storage';

export const storage = {
  // Store object/array
  set: async <T>(key: string, value: T): Promise<void> => {
    try {
      await AsyncStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
      console.error(`Storage set error for key "${key}":`, error);
      throw error;
    }
  },

  // Get object/array
  get: async <T>(key: string): Promise<T | null> => {
    try {
      const value = await AsyncStorage.getItem(key);
      return value ? JSON.parse(value) : null;
    } catch (error) {
      console.error(`Storage get error for key "${key}":`, error);
      return null;
    }
  },

  // Remove item
  remove: async (key: string): Promise<void> => {
    try {
      await AsyncStorage.removeItem(key);
    } catch (error) {
      console.error(`Storage remove error for key "${key}":`, error);
    }
  },

  // Get multiple items
  getMultiple: async <T>(keys: string[]): Promise<Record<string, T | null>> => {
    try {
      const pairs = await AsyncStorage.multiGet(keys);
      return pairs.reduce(
        (acc, [key, value]) => {
          acc[key] = value ? JSON.parse(value) : null;
          return acc;
        },
        {} as Record<string, T | null>
      );
    } catch (error) {
      console.error('Storage multiGet error:', error);
      return {};
    }
  },

  // Set multiple items
  setMultiple: async (items: Record<string, any>): Promise<void> => {
    try {
      const pairs = Object.entries(items).map(([key, value]) => [
        key,
        JSON.stringify(value),
      ]);
      await AsyncStorage.multiSet(pairs as [string, string][]);
    } catch (error) {
      console.error('Storage multiSet error:', error);
    }
  },

  // Get all keys
  getAllKeys: async (): Promise<string[]> => {
    try {
      return await AsyncStorage.getAllKeys();
    } catch (error) {
      console.error('Storage getAllKeys error:', error);
      return [];
    }
  },

  // Clear all storage
  clear: async (): Promise<void> => {
    try {
      await AsyncStorage.clear();
    } catch (error) {
      console.error('Storage clear error:', error);
    }
  },
};
```

## Typed Storage Keys

```typescript
// src/lib/storageKeys.ts
export const STORAGE_KEYS = {
  AUTH_TOKEN: 'auth_token',
  USER_PROFILE: 'user_profile',
  ONBOARDING_COMPLETE: 'onboarding_complete',
  THEME_MODE: 'theme_mode',
  LANGUAGE: 'language',
  FAVORITES: 'favorites',
  CART_ITEMS: 'cart_items',
  RECENT_SEARCHES: 'recent_searches',
  NOTIFICATION_SETTINGS: 'notification_settings',
} as const;

export type StorageKey = (typeof STORAGE_KEYS)[keyof typeof STORAGE_KEYS];
```

## Storage Hook

```typescript
// src/hooks/useStorage.ts
import { useState, useEffect, useCallback } from 'react';
import { storage } from '@/lib/storage';

export function useStorage<T>(key: string, initialValue: T) {
  const [storedValue, setStoredValue] = useState<T>(initialValue);
  const [isLoading, setIsLoading] = useState(true);

  // Load initial value
  useEffect(() => {
    const loadValue = async () => {
      try {
        const value = await storage.get<T>(key);
        if (value !== null) {
          setStoredValue(value);
        }
      } catch (error) {
        console.error('useStorage load error:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadValue();
  }, [key]);

  // Set value
  const setValue = useCallback(
    async (value: T | ((prev: T) => T)) => {
      try {
        const newValue =
          value instanceof Function ? value(storedValue) : value;
        setStoredValue(newValue);
        await storage.set(key, newValue);
      } catch (error) {
        console.error('useStorage set error:', error);
      }
    },
    [key, storedValue]
  );

  // Remove value
  const removeValue = useCallback(async () => {
    try {
      setStoredValue(initialValue);
      await storage.remove(key);
    } catch (error) {
      console.error('useStorage remove error:', error);
    }
  }, [key, initialValue]);

  return { value: storedValue, setValue, removeValue, isLoading };
}

// Usage
function SettingsScreen() {
  const { value: theme, setValue: setTheme, isLoading } = useStorage<'light' | 'dark'>(
    STORAGE_KEYS.THEME_MODE,
    'light'
  );

  if (isLoading) return <LoadingSpinner />;

  return (
    <View>
      <Switch
        value={theme === 'dark'}
        onValueChange={(isDark) => setTheme(isDark ? 'dark' : 'light')}
      />
    </View>
  );
}
```

## Storage with Expiry

```typescript
// src/lib/expiringStorage.ts
import { storage } from './storage';

interface StoredWithExpiry<T> {
  value: T;
  expiry: number;
}

export const expiringStorage = {
  set: async <T>(key: string, value: T, ttlMs: number): Promise<void> => {
    const item: StoredWithExpiry<T> = {
      value,
      expiry: Date.now() + ttlMs,
    };
    await storage.set(key, item);
  },

  get: async <T>(key: string): Promise<T | null> => {
    const item = await storage.get<StoredWithExpiry<T>>(key);

    if (!item) return null;

    if (Date.now() > item.expiry) {
      await storage.remove(key);
      return null;
    }

    return item.value;
  },

  isExpired: async (key: string): Promise<boolean> => {
    const item = await storage.get<StoredWithExpiry<any>>(key);
    if (!item) return true;
    return Date.now() > item.expiry;
  },
};

// Usage
// Store for 1 hour
await expiringStorage.set('session_data', sessionData, 60 * 60 * 1000);

// Get if not expired
const session = await expiringStorage.get('session_data');
```

## Favorites/Bookmarks Pattern

```typescript
// src/hooks/useFavorites.ts
import { useState, useEffect, useCallback } from 'react';
import { storage } from '@/lib/storage';
import { STORAGE_KEYS } from '@/lib/storageKeys';

export function useFavorites() {
  const [favorites, setFavorites] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Load favorites on mount
  useEffect(() => {
    const load = async () => {
      const stored = await storage.get<string[]>(STORAGE_KEYS.FAVORITES);
      setFavorites(stored ?? []);
      setIsLoading(false);
    };
    load();
  }, []);

  // Add favorite
  const addFavorite = useCallback(async (id: string) => {
    setFavorites((prev) => {
      if (prev.includes(id)) return prev;
      const updated = [...prev, id];
      storage.set(STORAGE_KEYS.FAVORITES, updated);
      return updated;
    });
  }, []);

  // Remove favorite
  const removeFavorite = useCallback(async (id: string) => {
    setFavorites((prev) => {
      const updated = prev.filter((fav) => fav !== id);
      storage.set(STORAGE_KEYS.FAVORITES, updated);
      return updated;
    });
  }, []);

  // Toggle favorite
  const toggleFavorite = useCallback(
    (id: string) => {
      if (favorites.includes(id)) {
        removeFavorite(id);
      } else {
        addFavorite(id);
      }
    },
    [favorites, addFavorite, removeFavorite]
  );

  // Check if favorited
  const isFavorite = useCallback(
    (id: string) => favorites.includes(id),
    [favorites]
  );

  return {
    favorites,
    isLoading,
    addFavorite,
    removeFavorite,
    toggleFavorite,
    isFavorite,
  };
}

// Usage
function ProductCard({ product }) {
  const { isFavorite, toggleFavorite } = useFavorites();

  return (
    <Pressable onPress={() => toggleFavorite(product.id)}>
      <Ionicons
        name={isFavorite(product.id) ? 'heart' : 'heart-outline'}
        color={isFavorite(product.id) ? 'red' : 'gray'}
      />
    </Pressable>
  );
}
```

## Recent Searches

```typescript
// src/hooks/useRecentSearches.ts
import { useState, useEffect, useCallback } from 'react';
import { storage } from '@/lib/storage';
import { STORAGE_KEYS } from '@/lib/storageKeys';

const MAX_RECENT_SEARCHES = 10;

export function useRecentSearches() {
  const [searches, setSearches] = useState<string[]>([]);

  useEffect(() => {
    const load = async () => {
      const stored = await storage.get<string[]>(STORAGE_KEYS.RECENT_SEARCHES);
      setSearches(stored ?? []);
    };
    load();
  }, []);

  const addSearch = useCallback(async (query: string) => {
    const trimmed = query.trim();
    if (!trimmed) return;

    setSearches((prev) => {
      // Remove if exists, add to front, limit size
      const filtered = prev.filter(
        (s) => s.toLowerCase() !== trimmed.toLowerCase()
      );
      const updated = [trimmed, ...filtered].slice(0, MAX_RECENT_SEARCHES);
      storage.set(STORAGE_KEYS.RECENT_SEARCHES, updated);
      return updated;
    });
  }, []);

  const removeSearch = useCallback(async (query: string) => {
    setSearches((prev) => {
      const updated = prev.filter((s) => s !== query);
      storage.set(STORAGE_KEYS.RECENT_SEARCHES, updated);
      return updated;
    });
  }, []);

  const clearSearches = useCallback(async () => {
    setSearches([]);
    await storage.remove(STORAGE_KEYS.RECENT_SEARCHES);
  }, []);

  return { searches, addSearch, removeSearch, clearSearches };
}
```

## Best Practices

1. **Use JSON Wrapper**: Always stringify/parse for non-string values
2. **Handle Errors**: Wrap in try-catch, don't crash on storage failure
3. **Typed Keys**: Use constants for storage keys
4. **Expiry Support**: Implement TTL for cached data
5. **Batch Operations**: Use multiGet/multiSet for multiple items
6. **Size Limits**: AsyncStorage has ~6MB limit on some platforms
7. **Sensitive Data**: Use SecureStore for tokens/credentials instead

## Limitations

- **Async Only**: All operations are asynchronous
- **Size Limit**: ~6MB on Android, varies on iOS
- **No Encryption**: Data stored in plain text
- **Performance**: Slower than MMKV for frequent operations
- **No Queries**: Simple key-value only, no filtering
