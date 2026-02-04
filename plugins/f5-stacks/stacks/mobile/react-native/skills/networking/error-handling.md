---
name: rn-error-handling
description: API error handling patterns in React Native
applies_to: react-native
---

# API Error Handling

## Error Types

```typescript
// src/types/errors.ts
export interface ApiError {
  message: string;
  code: string;
  statusCode: number;
  details?: Record<string, any>;
  timestamp?: string;
}

export interface ValidationError {
  field: string;
  message: string;
}

export interface ApiValidationError extends ApiError {
  errors: ValidationError[];
}

// Error type guards
export function isApiError(error: unknown): error is ApiError {
  return (
    typeof error === 'object' &&
    error !== null &&
    'message' in error &&
    'code' in error &&
    'statusCode' in error
  );
}

export function isValidationError(error: unknown): error is ApiValidationError {
  return isApiError(error) && 'errors' in error && Array.isArray(error.errors);
}
```

## Error Parser

```typescript
// src/lib/errorParser.ts
import { AxiosError } from 'axios';
import { ApiError } from '@/types/errors';

const ERROR_MESSAGES: Record<string, string> = {
  NETWORK_ERROR: 'Network connection failed. Please check your internet.',
  TIMEOUT: 'Request timed out. Please try again.',
  UNAUTHORIZED: 'Please log in to continue.',
  FORBIDDEN: 'You do not have permission to perform this action.',
  NOT_FOUND: 'The requested resource was not found.',
  VALIDATION_ERROR: 'Please check your input and try again.',
  SERVER_ERROR: 'Something went wrong. Please try again later.',
  UNKNOWN: 'An unexpected error occurred.',
};

export function parseApiError(error: unknown): ApiError {
  // Handle Axios errors
  if (error instanceof AxiosError) {
    // Network error (no response)
    if (!error.response) {
      if (error.code === 'ECONNABORTED') {
        return {
          message: ERROR_MESSAGES.TIMEOUT,
          code: 'TIMEOUT',
          statusCode: 0,
        };
      }
      return {
        message: ERROR_MESSAGES.NETWORK_ERROR,
        code: 'NETWORK_ERROR',
        statusCode: 0,
      };
    }

    const { status, data } = error.response;

    // Server returned error response
    if (data && typeof data === 'object') {
      return {
        message: data.message ?? ERROR_MESSAGES[getErrorCode(status)],
        code: data.code ?? getErrorCode(status),
        statusCode: status,
        details: data.details,
      };
    }

    // Generic HTTP error
    return {
      message: ERROR_MESSAGES[getErrorCode(status)] ?? ERROR_MESSAGES.UNKNOWN,
      code: getErrorCode(status),
      statusCode: status,
    };
  }

  // Handle Error instances
  if (error instanceof Error) {
    return {
      message: error.message,
      code: 'UNKNOWN',
      statusCode: 0,
    };
  }

  // Unknown error type
  return {
    message: ERROR_MESSAGES.UNKNOWN,
    code: 'UNKNOWN',
    statusCode: 0,
  };
}

function getErrorCode(status: number): string {
  switch (status) {
    case 401:
      return 'UNAUTHORIZED';
    case 403:
      return 'FORBIDDEN';
    case 404:
      return 'NOT_FOUND';
    case 422:
      return 'VALIDATION_ERROR';
    default:
      if (status >= 500) return 'SERVER_ERROR';
      return 'UNKNOWN';
  }
}
```

## Global Error Handler

```typescript
// src/lib/api.ts
import { api } from './apiClient';
import { parseApiError } from './errorParser';
import { showToast } from '@/components/Toast';
import { router } from 'expo-router';

// Response interceptor for global error handling
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const parsedError = parseApiError(error);

    // Handle specific error codes
    switch (parsedError.code) {
      case 'UNAUTHORIZED':
        // Clear auth state and redirect to login
        await clearAuthTokens();
        router.replace('/login');
        break;

      case 'NETWORK_ERROR':
        showToast({
          type: 'error',
          message: parsedError.message,
          action: {
            label: 'Retry',
            onPress: () => api.request(error.config),
          },
        });
        break;

      case 'SERVER_ERROR':
        showToast({
          type: 'error',
          message: parsedError.message,
        });
        // Log to error tracking service
        logError(error);
        break;
    }

    // Re-throw with parsed error for component handling
    return Promise.reject(parsedError);
  }
);
```

## Error Boundary

```typescript
// src/components/ErrorBoundary.tsx
import { Component, ErrorInfo, ReactNode } from 'react';
import { View, Text, StyleSheet, Pressable } from 'react-native';
import { router } from 'expo-router';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error to tracking service
    console.error('ErrorBoundary caught:', error, errorInfo);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  handleGoHome = () => {
    this.setState({ hasError: false, error: null });
    router.replace('/');
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <View style={styles.container}>
          <Text style={styles.title}>Something went wrong</Text>
          <Text style={styles.message}>
            {this.state.error?.message ?? 'An unexpected error occurred'}
          </Text>
          <View style={styles.buttons}>
            <Pressable style={styles.button} onPress={this.handleRetry}>
              <Text style={styles.buttonText}>Try Again</Text>
            </Pressable>
            <Pressable
              style={[styles.button, styles.secondaryButton]}
              onPress={this.handleGoHome}
            >
              <Text style={[styles.buttonText, styles.secondaryText]}>
                Go Home
              </Text>
            </Pressable>
          </View>
        </View>
      );
    }

    return this.props.children;
  }
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  title: {
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 8,
  },
  message: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    marginBottom: 24,
  },
  buttons: {
    flexDirection: 'row',
    gap: 12,
  },
  button: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  buttonText: {
    color: '#fff',
    fontWeight: '500',
  },
  secondaryButton: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: '#007AFF',
  },
  secondaryText: {
    color: '#007AFF',
  },
});
```

## Query Error Handling

```typescript
// src/features/products/hooks/useProducts.ts
import { useQuery } from '@tanstack/react-query';
import { parseApiError } from '@/lib/errorParser';
import type { ApiError } from '@/types/errors';

export function useProducts() {
  return useQuery<Product[], ApiError>({
    queryKey: ['products'],
    queryFn: async () => {
      try {
        const { data } = await api.get('/products');
        return data;
      } catch (error) {
        throw parseApiError(error);
      }
    },
    retry: (failureCount, error) => {
      // Don't retry on client errors
      if (error.statusCode >= 400 && error.statusCode < 500) {
        return false;
      }
      return failureCount < 3;
    },
  });
}

// Usage in component
function ProductList() {
  const { data, error, isLoading, refetch } = useProducts();

  if (isLoading) return <LoadingSpinner />;

  if (error) {
    return (
      <ErrorView
        message={error.message}
        code={error.code}
        onRetry={refetch}
      />
    );
  }

  return <FlatList data={data} renderItem={/* ... */} />;
}
```

## Mutation Error Handling

```typescript
// src/features/auth/hooks/useLogin.ts
import { useMutation } from '@tanstack/react-query';
import { parseApiError } from '@/lib/errorParser';
import { isValidationError } from '@/types/errors';

export function useLogin() {
  return useMutation({
    mutationFn: async (credentials: { email: string; password: string }) => {
      const { data } = await api.post('/auth/login', credentials);
      return data;
    },
    onError: (error) => {
      const parsedError = parseApiError(error);

      // Handle validation errors
      if (isValidationError(parsedError)) {
        // Return field-level errors to form
        return parsedError.errors;
      }

      // Show toast for other errors
      showToast({
        type: 'error',
        message: parsedError.message,
      });
    },
  });
}

// Usage
function LoginForm() {
  const { mutate, isPending, error } = useLogin();
  const { control, handleSubmit, setError } = useForm();

  const onSubmit = (values) => {
    mutate(values, {
      onError: (error) => {
        const parsed = parseApiError(error);
        if (isValidationError(parsed)) {
          parsed.errors.forEach((e) => {
            setError(e.field, { message: e.message });
          });
        }
      },
    });
  };

  return (/* ... */);
}
```

## Error Display Components

```typescript
// src/components/ErrorView.tsx
import { View, Text, StyleSheet, Pressable } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface ErrorViewProps {
  message: string;
  code?: string;
  onRetry?: () => void;
  fullScreen?: boolean;
}

export function ErrorView({
  message,
  code,
  onRetry,
  fullScreen = false,
}: ErrorViewProps) {
  const icon = getErrorIcon(code);

  return (
    <View style={[styles.container, fullScreen && styles.fullScreen]}>
      <Ionicons name={icon} size={48} color="#FF3B30" />
      <Text style={styles.message}>{message}</Text>
      {onRetry && (
        <Pressable style={styles.retryButton} onPress={onRetry}>
          <Ionicons name="refresh" size={20} color="#fff" />
          <Text style={styles.retryText}>Retry</Text>
        </Pressable>
      )}
    </View>
  );
}

function getErrorIcon(code?: string): keyof typeof Ionicons.glyphMap {
  switch (code) {
    case 'NETWORK_ERROR':
      return 'cloud-offline';
    case 'UNAUTHORIZED':
      return 'lock-closed';
    case 'FORBIDDEN':
      return 'ban';
    case 'NOT_FOUND':
      return 'search';
    default:
      return 'alert-circle';
  }
}

// Inline error for form fields
export function InlineError({ message }: { message: string }) {
  return (
    <View style={styles.inline}>
      <Ionicons name="alert-circle" size={14} color="#FF3B30" />
      <Text style={styles.inlineText}>{message}</Text>
    </View>
  );
}
```

## Best Practices

1. **Parse All Errors**: Use consistent error parser for all API calls
2. **Type Errors**: Define proper TypeScript types for error responses
3. **User-Friendly Messages**: Map error codes to readable messages
4. **Error Boundaries**: Wrap screens/features in ErrorBoundary
5. **Retry Logic**: Allow users to retry failed operations
6. **Log Errors**: Send errors to tracking service (Sentry, etc.)
7. **Validation Errors**: Display field-level errors in forms
8. **Global Handling**: Handle auth errors (401) globally
