---
name: rn-hook-generator
description: Generate custom React hooks for React Native applications
triggers:
  - "rn hook"
  - "react native hook"
  - "create hook"
  - "generate hook"
applies_to: react-native
---

# React Native Hook Generator

## Purpose

Generate custom React hooks for common patterns:
- Data fetching with TanStack Query
- Form handling with React Hook Form
- Local storage with AsyncStorage/MMKV
- Device features (camera, location, etc.)
- Animation with Reanimated
- Debounce/throttle utilities

## Input Requirements

```yaml
required:
  - hook_name: string         # e.g., "useAuth", "useProducts"
  - hook_type: query | mutation | state | device | utility

optional:
  - feature: string           # Parent feature module
  - returns: string[]         # Return values description
  - dependencies: string[]    # External dependencies
```

## Generation Templates

### Query Hook Template

```typescript
// src/features/{{feature}}/hooks/use{{Entity}}.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { {{Entity}}, Create{{Entity}}Input, Update{{Entity}}Input } from '../types';

const {{ENTITY}}_KEYS = {
  all: ['{{entities}}'] as const,
  lists: () => [...{{ENTITY}}_KEYS.all, 'list'] as const,
  list: (filters: Record<string, unknown>) =>
    [...{{ENTITY}}_KEYS.lists(), filters] as const,
  details: () => [...{{ENTITY}}_KEYS.all, 'detail'] as const,
  detail: (id: string) => [...{{ENTITY}}_KEYS.details(), id] as const,
};

// Fetch single {{entity}}
export function use{{Entity}}(id: string) {
  return useQuery({
    queryKey: {{ENTITY}}_KEYS.detail(id),
    queryFn: async () => {
      const { data } = await api.get<{{Entity}}>(`/{{entities}}/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

// Fetch {{entities}} list
export function use{{Entities}}(filters?: Record<string, unknown>) {
  return useQuery({
    queryKey: {{ENTITY}}_KEYS.list(filters ?? {}),
    queryFn: async () => {
      const { data } = await api.get<{{Entity}}[]>('/{{entities}}', { params: filters });
      return data;
    },
  });
}

// Create {{entity}}
export function useCreate{{Entity}}() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (input: Create{{Entity}}Input) => {
      const { data } = await api.post<{{Entity}}>('/{{entities}}', input);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: {{ENTITY}}_KEYS.lists() });
    },
  });
}

// Update {{entity}}
export function useUpdate{{Entity}}() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, ...input }: Update{{Entity}}Input & { id: string }) => {
      const { data } = await api.patch<{{Entity}}>(`/{{entities}}/${id}`, input);
      return data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: {{ENTITY}}_KEYS.lists() });
      queryClient.setQueryData({{ENTITY}}_KEYS.detail(data.id), data);
    },
  });
}

// Delete {{entity}}
export function useDelete{{Entity}}() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/{{entities}}/${id}`);
      return id;
    },
    onSuccess: (id) => {
      queryClient.invalidateQueries({ queryKey: {{ENTITY}}_KEYS.lists() });
      queryClient.removeQueries({ queryKey: {{ENTITY}}_KEYS.detail(id) });
    },
  });
}
```

### Auth Hook Template

```typescript
// src/hooks/useAuth.ts
import { useCallback } from 'react';
import { useAuthStore } from '@/stores/useAuthStore';
import type { LoginCredentials, RegisterData } from '@/types/auth';

export function useAuth() {
  const {
    user,
    token,
    isLoading,
    error,
    login: loginAction,
    logout: logoutAction,
    register: registerAction,
    clearError,
  } = useAuthStore();

  const isAuthenticated = !!token;

  const login = useCallback(
    async (credentials: LoginCredentials) => {
      try {
        await loginAction(credentials.email, credentials.password);
        return { success: true };
      } catch (err) {
        return {
          success: false,
          error: err instanceof Error ? err.message : 'Login failed',
        };
      }
    },
    [loginAction]
  );

  const logout = useCallback(async () => {
    await logoutAction();
  }, [logoutAction]);

  const register = useCallback(
    async (data: RegisterData) => {
      try {
        await registerAction(data);
        return { success: true };
      } catch (err) {
        return {
          success: false,
          error: err instanceof Error ? err.message : 'Registration failed',
        };
      }
    },
    [registerAction]
  );

  return {
    user,
    isAuthenticated,
    isLoading,
    error,
    login,
    logout,
    register,
    clearError,
  };
}
```

### Device Hook Template

```typescript
// src/hooks/useLocation.ts
import { useState, useEffect, useCallback } from 'react';
import * as Location from 'expo-location';

interface LocationState {
  latitude: number | null;
  longitude: number | null;
  accuracy: number | null;
  isLoading: boolean;
  error: string | null;
}

interface UseLocationOptions {
  enableHighAccuracy?: boolean;
  watchPosition?: boolean;
}

export function useLocation(options: UseLocationOptions = {}) {
  const { enableHighAccuracy = true, watchPosition = false } = options;

  const [state, setState] = useState<LocationState>({
    latitude: null,
    longitude: null,
    accuracy: null,
    isLoading: true,
    error: null,
  });

  const [permissionStatus, setPermissionStatus] =
    useState<Location.PermissionStatus | null>(null);

  const requestPermission = useCallback(async () => {
    const { status } = await Location.requestForegroundPermissionsAsync();
    setPermissionStatus(status);
    return status === 'granted';
  }, []);

  const getCurrentLocation = useCallback(async () => {
    setState((prev) => ({ ...prev, isLoading: true, error: null }));

    try {
      const hasPermission = await requestPermission();
      if (!hasPermission) {
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: 'Location permission denied',
        }));
        return null;
      }

      const location = await Location.getCurrentPositionAsync({
        accuracy: enableHighAccuracy
          ? Location.Accuracy.High
          : Location.Accuracy.Balanced,
      });

      const newState = {
        latitude: location.coords.latitude,
        longitude: location.coords.longitude,
        accuracy: location.coords.accuracy,
        isLoading: false,
        error: null,
      };

      setState(newState);
      return newState;
    } catch (err) {
      const error = err instanceof Error ? err.message : 'Failed to get location';
      setState((prev) => ({ ...prev, isLoading: false, error }));
      return null;
    }
  }, [enableHighAccuracy, requestPermission]);

  useEffect(() => {
    getCurrentLocation();
  }, [getCurrentLocation]);

  useEffect(() => {
    if (!watchPosition) return;

    let subscription: Location.LocationSubscription | null = null;

    const startWatching = async () => {
      const hasPermission = await requestPermission();
      if (!hasPermission) return;

      subscription = await Location.watchPositionAsync(
        {
          accuracy: enableHighAccuracy
            ? Location.Accuracy.High
            : Location.Accuracy.Balanced,
          distanceInterval: 10,
        },
        (location) => {
          setState({
            latitude: location.coords.latitude,
            longitude: location.coords.longitude,
            accuracy: location.coords.accuracy,
            isLoading: false,
            error: null,
          });
        }
      );
    };

    startWatching();

    return () => {
      subscription?.remove();
    };
  }, [watchPosition, enableHighAccuracy, requestPermission]);

  return {
    ...state,
    permissionStatus,
    requestPermission,
    refresh: getCurrentLocation,
  };
}
```

### Utility Hook Template

```typescript
// src/hooks/useDebounce.ts
import { useState, useEffect } from 'react';

export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(timer);
    };
  }, [value, delay]);

  return debouncedValue;
}

// Usage example:
// const debouncedSearch = useDebounce(searchQuery, 300);
```

```typescript
// src/hooks/useKeyboard.ts
import { useState, useEffect } from 'react';
import { Keyboard, KeyboardEvent, Platform } from 'react-native';

export function useKeyboard() {
  const [isVisible, setIsVisible] = useState(false);
  const [keyboardHeight, setKeyboardHeight] = useState(0);

  useEffect(() => {
    const showEvent = Platform.OS === 'ios' ? 'keyboardWillShow' : 'keyboardDidShow';
    const hideEvent = Platform.OS === 'ios' ? 'keyboardWillHide' : 'keyboardDidHide';

    const handleShow = (event: KeyboardEvent) => {
      setIsVisible(true);
      setKeyboardHeight(event.endCoordinates.height);
    };

    const handleHide = () => {
      setIsVisible(false);
      setKeyboardHeight(0);
    };

    const showSubscription = Keyboard.addListener(showEvent, handleShow);
    const hideSubscription = Keyboard.addListener(hideEvent, handleHide);

    return () => {
      showSubscription.remove();
      hideSubscription.remove();
    };
  }, []);

  return {
    isVisible,
    keyboardHeight,
    dismiss: Keyboard.dismiss,
  };
}
```

## Output Structure

```
src/
├── hooks/                    # Shared hooks
│   ├── useAuth.ts
│   ├── useDebounce.ts
│   ├── useKeyboard.ts
│   └── useLocation.ts
└── features/
    └── {{feature}}/
        └── hooks/
            └── use{{Entity}}.ts
```

## Best Practices

1. **Naming**: Always prefix with "use" (useAuth, useProducts)
2. **Single Purpose**: Each hook should do one thing well
3. **Return Object**: Return named values for clarity
4. **Memoization**: Use useCallback for returned functions
5. **Error Handling**: Always return error state
6. **Loading State**: Include isLoading for async operations
7. **TypeScript**: Strong typing for params and returns
