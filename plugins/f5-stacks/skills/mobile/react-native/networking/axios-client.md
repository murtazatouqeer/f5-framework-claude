---
name: rn-axios-client
description: Axios HTTP client setup for React Native
applies_to: react-native
---

# Axios Client Setup

## Installation

```bash
npm install axios
```

## Base Client Configuration

```typescript
// src/lib/api.ts
import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';
import Constants from 'expo-constants';

// Environment-based URL
const getBaseUrl = () => {
  if (__DEV__) {
    // Android emulator uses 10.0.2.2 for localhost
    return Platform.OS === 'android'
      ? 'http://10.0.2.2:3000/api'
      : 'http://localhost:3000/api';
  }
  return Constants.expoConfig?.extra?.apiUrl ?? 'https://api.example.com';
};

// Create instance
export const api: AxiosInstance = axios.create({
  baseURL: getBaseUrl(),
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    // Add auth token
    const token = await SecureStore.getItemAsync('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Add device info
    config.headers['X-Platform'] = Platform.OS;
    config.headers['X-App-Version'] = Constants.expoConfig?.version ?? '1.0.0';

    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config;

    // Handle 401 - Token expired
    if (error.response?.status === 401 && originalRequest) {
      try {
        const refreshToken = await SecureStore.getItemAsync('refreshToken');
        if (refreshToken) {
          const response = await axios.post(`${getBaseUrl()}/auth/refresh`, {
            refreshToken,
          });

          const { accessToken } = response.data;
          await SecureStore.setItemAsync('authToken', accessToken);

          originalRequest.headers.Authorization = `Bearer ${accessToken}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed, clear tokens and redirect to login
        await SecureStore.deleteItemAsync('authToken');
        await SecureStore.deleteItemAsync('refreshToken');
        // Emit event or navigate to login
      }
    }

    return Promise.reject(error);
  }
);
```

## API Service Pattern

```typescript
// src/services/api/userService.ts
import { api } from '@/lib/api';
import type { User, UpdateUserInput, PaginatedResponse } from '@/types';

export const userService = {
  getProfile: async (): Promise<User> => {
    const { data } = await api.get('/users/me');
    return data;
  },

  updateProfile: async (input: UpdateUserInput): Promise<User> => {
    const { data } = await api.patch('/users/me', input);
    return data;
  },

  getUsers: async (params?: {
    page?: number;
    limit?: number;
    search?: string;
  }): Promise<PaginatedResponse<User>> => {
    const { data } = await api.get('/users', { params });
    return data;
  },

  getUserById: async (id: string): Promise<User> => {
    const { data } = await api.get(`/users/${id}`);
    return data;
  },

  deleteUser: async (id: string): Promise<void> => {
    await api.delete(`/users/${id}`);
  },
};
```

## File Upload

```typescript
// src/services/api/uploadService.ts
import { api } from '@/lib/api';
import * as FileSystem from 'expo-file-system';
import * as ImagePicker from 'expo-image-picker';

interface UploadResult {
  url: string;
  key: string;
}

export const uploadService = {
  uploadImage: async (uri: string): Promise<UploadResult> => {
    const formData = new FormData();

    // Get file info
    const fileInfo = await FileSystem.getInfoAsync(uri);
    const filename = uri.split('/').pop() ?? 'image.jpg';
    const match = /\.(\w+)$/.exec(filename);
    const type = match ? `image/${match[1]}` : 'image/jpeg';

    formData.append('file', {
      uri,
      name: filename,
      type,
    } as any);

    const { data } = await api.post<UploadResult>('/upload/image', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        const percentCompleted = Math.round(
          (progressEvent.loaded * 100) / (progressEvent.total ?? 1)
        );
        console.log(`Upload progress: ${percentCompleted}%`);
      },
    });

    return data;
  },

  pickAndUploadImage: async (): Promise<UploadResult | null> => {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      quality: 0.8,
    });

    if (!result.canceled && result.assets[0]) {
      return uploadService.uploadImage(result.assets[0].uri);
    }

    return null;
  },
};
```

## Request Cancellation

```typescript
// src/hooks/useCancellableRequest.ts
import { useEffect, useRef } from 'react';
import axios, { CancelTokenSource } from 'axios';

export function useCancellableRequest() {
  const cancelTokenRef = useRef<CancelTokenSource | null>(null);

  useEffect(() => {
    return () => {
      // Cancel any pending request on unmount
      cancelTokenRef.current?.cancel('Component unmounted');
    };
  }, []);

  const getCancelToken = () => {
    // Cancel previous request if exists
    cancelTokenRef.current?.cancel('New request initiated');
    cancelTokenRef.current = axios.CancelToken.source();
    return cancelTokenRef.current.token;
  };

  return { getCancelToken };
}

// Usage
function SearchScreen() {
  const { getCancelToken } = useCancellableRequest();
  const [results, setResults] = useState([]);

  const handleSearch = async (query: string) => {
    try {
      const { data } = await api.get('/search', {
        params: { q: query },
        cancelToken: getCancelToken(),
      });
      setResults(data);
    } catch (error) {
      if (!axios.isCancel(error)) {
        console.error('Search failed:', error);
      }
    }
  };

  return (/* ... */);
}
```

## Request Retry

```typescript
// src/lib/apiWithRetry.ts
import axios, { AxiosInstance, AxiosError } from 'axios';

interface RetryConfig {
  retries: number;
  retryDelay: number;
  retryCondition?: (error: AxiosError) => boolean;
}

const defaultRetryCondition = (error: AxiosError): boolean => {
  // Retry on network errors or 5xx responses
  return (
    !error.response ||
    (error.response.status >= 500 && error.response.status <= 599)
  );
};

export function setupRetryInterceptor(
  instance: AxiosInstance,
  config: RetryConfig = { retries: 3, retryDelay: 1000 }
) {
  instance.interceptors.response.use(undefined, async (error: AxiosError) => {
    const { config: requestConfig } = error;
    if (!requestConfig) return Promise.reject(error);

    const retryCount = (requestConfig as any).__retryCount ?? 0;
    const shouldRetry =
      retryCount < config.retries &&
      (config.retryCondition ?? defaultRetryCondition)(error);

    if (shouldRetry) {
      (requestConfig as any).__retryCount = retryCount + 1;

      // Exponential backoff
      const delay = config.retryDelay * Math.pow(2, retryCount);
      await new Promise((resolve) => setTimeout(resolve, delay));

      return instance(requestConfig);
    }

    return Promise.reject(error);
  });
}

// Usage
setupRetryInterceptor(api, { retries: 3, retryDelay: 1000 });
```

## Integration with TanStack Query

```typescript
// src/features/users/hooks/useUsers.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { userService } from '@/services/api/userService';

export function useProfile() {
  return useQuery({
    queryKey: ['profile'],
    queryFn: userService.getProfile,
  });
}

export function useUpdateProfile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: userService.updateProfile,
    onSuccess: (updatedUser) => {
      queryClient.setQueryData(['profile'], updatedUser);
    },
  });
}
```

## Best Practices

1. **Environment Config**: Use different base URLs for dev/prod
2. **Token Management**: Store tokens securely with expo-secure-store
3. **Request Interceptors**: Add auth headers and device info automatically
4. **Response Interceptors**: Handle token refresh and global errors
5. **Type Safety**: Define types for all API responses
6. **Service Pattern**: Organize API calls by domain
7. **Cancellation**: Cancel requests on component unmount
8. **Retry Logic**: Implement exponential backoff for failed requests
