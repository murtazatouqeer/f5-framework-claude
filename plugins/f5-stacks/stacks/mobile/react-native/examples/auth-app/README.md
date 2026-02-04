# Auth App Example

Complete React Native authentication application with secure storage, biometrics, and social login.

## Features

- **Email/Password Authentication**: Traditional login and registration
- **Social Login**: Google, Apple, Facebook integration
- **Biometric Authentication**: Face ID / Touch ID / Fingerprint
- **Secure Token Storage**: expo-secure-store for credentials
- **Auto Token Refresh**: Automatic access token renewal
- **Protected Routes**: Navigation guards with auth state
- **Persistent Sessions**: Remember me functionality
- **Password Reset**: Email-based recovery flow
- **Profile Management**: Update user info and avatar

## Tech Stack

- Expo SDK 50+
- React Native 0.73+
- TypeScript 5.0+
- Expo Router (file-based routing)
- Zustand v4 (auth state)
- expo-secure-store (secure storage)
- expo-local-authentication (biometrics)
- expo-auth-session (OAuth)
- TanStack Query v5 (user data)
- react-hook-form v7 (forms)
- Zod (validation)

## Project Structure

```
auth-app/
├── app/
│   ├── _layout.tsx              # Root layout with auth provider
│   ├── index.tsx                # Entry point (redirect logic)
│   ├── (auth)/                  # Auth group (unauthenticated)
│   │   ├── _layout.tsx          # Auth layout
│   │   ├── login.tsx            # Login screen
│   │   ├── register.tsx         # Registration screen
│   │   ├── forgot-password.tsx  # Password reset
│   │   └── verify-email.tsx     # Email verification
│   ├── (app)/                   # App group (authenticated)
│   │   ├── _layout.tsx          # Protected layout
│   │   ├── (tabs)/
│   │   │   ├── _layout.tsx      # Tab navigator
│   │   │   ├── home.tsx         # Home tab
│   │   │   └── profile.tsx      # Profile tab
│   │   └── settings/
│   │       ├── _layout.tsx      # Settings stack
│   │       ├── index.tsx        # Settings main
│   │       ├── security.tsx     # Security settings
│   │       └── notifications.tsx
│   └── +not-found.tsx           # 404 screen
├── src/
│   ├── components/
│   │   ├── ui/
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Avatar.tsx
│   │   │   └── index.ts
│   │   ├── auth/
│   │   │   ├── LoginForm.tsx
│   │   │   ├── RegisterForm.tsx
│   │   │   ├── SocialLoginButtons.tsx
│   │   │   ├── BiometricButton.tsx
│   │   │   └── index.ts
│   │   └── common/
│   │       ├── ErrorBoundary.tsx
│   │       └── LoadingOverlay.tsx
│   ├── features/
│   │   └── auth/
│   │       ├── api/
│   │       │   ├── authService.ts
│   │       │   └── userService.ts
│   │       ├── hooks/
│   │       │   ├── useLogin.ts
│   │       │   ├── useRegister.ts
│   │       │   ├── useLogout.ts
│   │       │   ├── useBiometrics.ts
│   │       │   ├── useSocialLogin.ts
│   │       │   └── useUser.ts
│   │       ├── types/
│   │       │   └── index.ts
│   │       └── index.ts
│   ├── lib/
│   │   ├── api.ts               # Axios with interceptors
│   │   ├── storage.ts           # Secure storage helpers
│   │   ├── biometrics.ts        # Biometric utilities
│   │   └── oauth.ts             # OAuth configuration
│   ├── providers/
│   │   ├── AuthProvider.tsx
│   │   ├── QueryProvider.tsx
│   │   └── index.ts
│   ├── stores/
│   │   ├── useAuthStore.ts      # Auth state management
│   │   └── index.ts
│   └── utils/
│       ├── validation.ts
│       └── tokens.ts
├── __tests__/
│   ├── auth/
│   ├── components/
│   └── stores/
├── app.json
├── package.json
├── tsconfig.json
└── eas.json
```

## Key Implementations

### 1. Auth Store with Secure Storage

```typescript
// src/stores/useAuthStore.ts
import { create } from 'zustand';
import { persist, createJSONStorage, StateStorage } from 'zustand/middleware';
import * as SecureStore from 'expo-secure-store';
import { api } from '@/lib/api';
import type { User, AuthTokens } from '@/features/auth/types';

const secureStorage: StateStorage = {
  getItem: async (name) => {
    return await SecureStore.getItemAsync(name);
  },
  setItem: async (name, value) => {
    await SecureStore.setItemAsync(name, value);
  },
  removeItem: async (name) => {
    await SecureStore.deleteItemAsync(name);
  },
};

interface AuthState {
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isBiometricEnabled: boolean;

  setAuth: (user: User, tokens: AuthTokens) => void;
  setTokens: (tokens: AuthTokens) => void;
  setUser: (user: User) => void;
  setBiometricEnabled: (enabled: boolean) => void;
  logout: () => void;
  reset: () => void;
}

const initialState = {
  user: null,
  tokens: null,
  isAuthenticated: false,
  isLoading: true,
  isBiometricEnabled: false,
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      ...initialState,

      setAuth: (user, tokens) => {
        api.defaults.headers.common.Authorization = `Bearer ${tokens.accessToken}`;
        set({
          user,
          tokens,
          isAuthenticated: true,
          isLoading: false,
        });
      },

      setTokens: (tokens) => {
        api.defaults.headers.common.Authorization = `Bearer ${tokens.accessToken}`;
        set({ tokens });
      },

      setUser: (user) => set({ user }),

      setBiometricEnabled: (isBiometricEnabled) => set({ isBiometricEnabled }),

      logout: async () => {
        delete api.defaults.headers.common.Authorization;
        set({ ...initialState, isLoading: false });
      },

      reset: () => set(initialState),
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => secureStorage),
      partialize: (state) => ({
        user: state.user,
        tokens: state.tokens,
        isAuthenticated: state.isAuthenticated,
        isBiometricEnabled: state.isBiometricEnabled,
      }),
      onRehydrateStorage: () => (state) => {
        if (state?.tokens?.accessToken) {
          api.defaults.headers.common.Authorization = `Bearer ${state.tokens.accessToken}`;
        }
        useAuthStore.setState({ isLoading: false });
      },
    }
  )
);
```

### 2. API Client with Token Refresh

```typescript
// src/lib/api.ts
import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import { useAuthStore } from '@/stores/useAuthStore';
import { authService } from '@/features/auth/api/authService';

export const api = axios.create({
  baseURL: process.env.EXPO_PUBLIC_API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (error: Error) => void;
}> = [];

const processQueue = (error: Error | null, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token!);
    }
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({
            resolve: (token) => {
              originalRequest.headers.Authorization = `Bearer ${token}`;
              resolve(api(originalRequest));
            },
            reject: (err) => reject(err),
          });
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const { tokens, logout, setTokens } = useAuthStore.getState();

      if (!tokens?.refreshToken) {
        logout();
        return Promise.reject(error);
      }

      try {
        const newTokens = await authService.refreshToken(tokens.refreshToken);
        setTokens(newTokens);
        processQueue(null, newTokens.accessToken);
        originalRequest.headers.Authorization = `Bearer ${newTokens.accessToken}`;
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError as Error, null);
        logout();
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);
```

### 3. Auth Service

```typescript
// src/features/auth/api/authService.ts
import { api } from '@/lib/api';
import type {
  LoginInput,
  RegisterInput,
  AuthResponse,
  AuthTokens,
  User,
} from '../types';

export const authService = {
  login: async (input: LoginInput): Promise<AuthResponse> => {
    const { data } = await api.post<AuthResponse>('/auth/login', input);
    return data;
  },

  register: async (input: RegisterInput): Promise<AuthResponse> => {
    const { data } = await api.post<AuthResponse>('/auth/register', input);
    return data;
  },

  logout: async (): Promise<void> => {
    await api.post('/auth/logout');
  },

  refreshToken: async (refreshToken: string): Promise<AuthTokens> => {
    const { data } = await api.post<AuthTokens>('/auth/refresh', {
      refreshToken,
    });
    return data;
  },

  forgotPassword: async (email: string): Promise<void> => {
    await api.post('/auth/forgot-password', { email });
  },

  resetPassword: async (token: string, password: string): Promise<void> => {
    await api.post('/auth/reset-password', { token, password });
  },

  verifyEmail: async (token: string): Promise<void> => {
    await api.post('/auth/verify-email', { token });
  },

  getMe: async (): Promise<User> => {
    const { data } = await api.get<User>('/auth/me');
    return data;
  },

  updateProfile: async (input: Partial<User>): Promise<User> => {
    const { data } = await api.patch<User>('/auth/profile', input);
    return data;
  },

  socialLogin: async (
    provider: 'google' | 'apple' | 'facebook',
    token: string
  ): Promise<AuthResponse> => {
    const { data } = await api.post<AuthResponse>(`/auth/${provider}`, {
      token,
    });
    return data;
  },
};
```

### 4. Biometric Authentication

```typescript
// src/lib/biometrics.ts
import * as LocalAuthentication from 'expo-local-authentication';
import * as SecureStore from 'expo-secure-store';

const BIOMETRIC_CREDENTIALS_KEY = 'biometric_credentials';

interface BiometricCredentials {
  email: string;
  password: string;
}

export const biometrics = {
  isAvailable: async (): Promise<boolean> => {
    const compatible = await LocalAuthentication.hasHardwareAsync();
    const enrolled = await LocalAuthentication.isEnrolledAsync();
    return compatible && enrolled;
  },

  getSupportedTypes: async (): Promise<LocalAuthentication.AuthenticationType[]> => {
    return await LocalAuthentication.supportedAuthenticationTypesAsync();
  },

  authenticate: async (
    promptMessage: string = 'Authenticate to continue'
  ): Promise<boolean> => {
    const result = await LocalAuthentication.authenticateAsync({
      promptMessage,
      fallbackLabel: 'Use passcode',
      disableDeviceFallback: false,
    });
    return result.success;
  },

  saveCredentials: async (credentials: BiometricCredentials): Promise<void> => {
    await SecureStore.setItemAsync(
      BIOMETRIC_CREDENTIALS_KEY,
      JSON.stringify(credentials)
    );
  },

  getCredentials: async (): Promise<BiometricCredentials | null> => {
    const stored = await SecureStore.getItemAsync(BIOMETRIC_CREDENTIALS_KEY);
    return stored ? JSON.parse(stored) : null;
  },

  clearCredentials: async (): Promise<void> => {
    await SecureStore.deleteItemAsync(BIOMETRIC_CREDENTIALS_KEY);
  },
};

// src/features/auth/hooks/useBiometrics.ts
import { useState, useCallback } from 'react';
import { biometrics } from '@/lib/biometrics';
import { useAuthStore } from '@/stores/useAuthStore';
import { authService } from '../api/authService';

export function useBiometrics() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { setAuth, setBiometricEnabled, isBiometricEnabled } = useAuthStore();

  const checkAvailability = useCallback(async () => {
    return await biometrics.isAvailable();
  }, []);

  const enableBiometrics = useCallback(
    async (email: string, password: string) => {
      try {
        setIsLoading(true);
        setError(null);

        const isAvailable = await biometrics.isAvailable();
        if (!isAvailable) {
          throw new Error('Biometrics not available on this device');
        }

        const authenticated = await biometrics.authenticate(
          'Enable biometric login'
        );
        if (!authenticated) {
          throw new Error('Biometric authentication failed');
        }

        await biometrics.saveCredentials({ email, password });
        setBiometricEnabled(true);

        return true;
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to enable biometrics');
        return false;
      } finally {
        setIsLoading(false);
      }
    },
    [setBiometricEnabled]
  );

  const loginWithBiometrics = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const authenticated = await biometrics.authenticate('Login with biometrics');
      if (!authenticated) {
        throw new Error('Biometric authentication failed');
      }

      const credentials = await biometrics.getCredentials();
      if (!credentials) {
        throw new Error('No saved credentials found');
      }

      const response = await authService.login(credentials);
      setAuth(response.user, response.tokens);

      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Biometric login failed');
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [setAuth]);

  const disableBiometrics = useCallback(async () => {
    await biometrics.clearCredentials();
    setBiometricEnabled(false);
  }, [setBiometricEnabled]);

  return {
    isLoading,
    error,
    isBiometricEnabled,
    checkAvailability,
    enableBiometrics,
    loginWithBiometrics,
    disableBiometrics,
  };
}
```

### 5. Social Login (Google)

```typescript
// src/lib/oauth.ts
import * as AuthSession from 'expo-auth-session';
import * as Google from 'expo-auth-session/providers/google';
import * as AppleAuthentication from 'expo-apple-authentication';

export const googleConfig = {
  expoClientId: process.env.EXPO_PUBLIC_GOOGLE_CLIENT_ID,
  iosClientId: process.env.EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID,
  androidClientId: process.env.EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID,
  webClientId: process.env.EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID,
};

// src/features/auth/hooks/useSocialLogin.ts
import { useState, useEffect } from 'react';
import * as Google from 'expo-auth-session/providers/google';
import * as AppleAuthentication from 'expo-apple-authentication';
import { googleConfig } from '@/lib/oauth';
import { useAuthStore } from '@/stores/useAuthStore';
import { authService } from '../api/authService';

export function useGoogleLogin() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { setAuth } = useAuthStore();

  const [request, response, promptAsync] = Google.useAuthRequest({
    ...googleConfig,
    scopes: ['profile', 'email'],
  });

  useEffect(() => {
    if (response?.type === 'success') {
      handleGoogleResponse(response.authentication?.accessToken);
    }
  }, [response]);

  const handleGoogleResponse = async (token?: string) => {
    if (!token) return;

    try {
      setIsLoading(true);
      setError(null);
      const authResponse = await authService.socialLogin('google', token);
      setAuth(authResponse.user, authResponse.tokens);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Google login failed');
    } finally {
      setIsLoading(false);
    }
  };

  const login = async () => {
    try {
      setError(null);
      await promptAsync();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start Google login');
    }
  };

  return {
    login,
    isLoading,
    error,
    isReady: !!request,
  };
}

export function useAppleLogin() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { setAuth } = useAuthStore();

  const login = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const credential = await AppleAuthentication.signInAsync({
        requestedScopes: [
          AppleAuthentication.AppleAuthenticationScope.FULL_NAME,
          AppleAuthentication.AppleAuthenticationScope.EMAIL,
        ],
      });

      if (credential.identityToken) {
        const authResponse = await authService.socialLogin(
          'apple',
          credential.identityToken
        );
        setAuth(authResponse.user, authResponse.tokens);
      }
    } catch (err: any) {
      if (err.code !== 'ERR_CANCELED') {
        setError(err.message || 'Apple login failed');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return {
    login,
    isLoading,
    error,
  };
}
```

### 6. Protected Route Layout

```typescript
// app/(app)/_layout.tsx
import { Redirect, Stack } from 'expo-router';
import { useAuthStore } from '@/stores/useAuthStore';
import { LoadingOverlay } from '@/components/common';

export default function AppLayout() {
  const { isAuthenticated, isLoading } = useAuthStore();

  if (isLoading) {
    return <LoadingOverlay message="Loading..." />;
  }

  if (!isAuthenticated) {
    return <Redirect href="/(auth)/login" />;
  }

  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="(tabs)" />
      <Stack.Screen
        name="settings"
        options={{
          headerShown: true,
          title: 'Settings',
          presentation: 'card',
        }}
      />
    </Stack>
  );
}

// app/(auth)/_layout.tsx
import { Redirect, Stack } from 'expo-router';
import { useAuthStore } from '@/stores/useAuthStore';
import { LoadingOverlay } from '@/components/common';

export default function AuthLayout() {
  const { isAuthenticated, isLoading } = useAuthStore();

  if (isLoading) {
    return <LoadingOverlay message="Loading..." />;
  }

  if (isAuthenticated) {
    return <Redirect href="/(app)/(tabs)/home" />;
  }

  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="login" />
      <Stack.Screen name="register" />
      <Stack.Screen
        name="forgot-password"
        options={{
          headerShown: true,
          title: 'Reset Password',
          presentation: 'modal',
        }}
      />
    </Stack>
  );
}
```

### 7. Login Screen

```typescript
// app/(auth)/login.tsx
import { View, Text, ScrollView, KeyboardAvoidingView, Platform } from 'react-native';
import { Link } from 'expo-router';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button, Input } from '@/components/ui';
import { SocialLoginButtons, BiometricButton } from '@/components/auth';
import { useLogin } from '@/features/auth/hooks/useLogin';
import { useBiometrics } from '@/features/auth/hooks/useBiometrics';

const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
});

type LoginForm = z.infer<typeof loginSchema>;

export default function LoginScreen() {
  const { mutate: login, isPending, error } = useLogin();
  const { isBiometricEnabled, loginWithBiometrics, isLoading: biometricLoading } = useBiometrics();

  const {
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
    },
  });

  const onSubmit = (data: LoginForm) => {
    login(data);
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      className="flex-1 bg-white"
    >
      <ScrollView
        contentContainerStyle={{ flexGrow: 1 }}
        keyboardShouldPersistTaps="handled"
      >
        <View className="flex-1 justify-center p-6">
          <Text className="text-3xl font-bold text-center mb-2">Welcome Back</Text>
          <Text className="text-gray-500 text-center mb-8">
            Sign in to continue
          </Text>

          {error && (
            <View className="bg-red-50 p-4 rounded-lg mb-4">
              <Text className="text-red-600">{error.message}</Text>
            </View>
          )}

          <Controller
            control={control}
            name="email"
            render={({ field: { onChange, onBlur, value } }) => (
              <Input
                label="Email"
                placeholder="your@email.com"
                value={value}
                onChangeText={onChange}
                onBlur={onBlur}
                keyboardType="email-address"
                autoCapitalize="none"
                autoComplete="email"
                error={errors.email?.message}
              />
            )}
          />

          <Controller
            control={control}
            name="password"
            render={({ field: { onChange, onBlur, value } }) => (
              <Input
                label="Password"
                placeholder="Enter your password"
                value={value}
                onChangeText={onChange}
                onBlur={onBlur}
                secureTextEntry
                autoComplete="password"
                error={errors.password?.message}
              />
            )}
          />

          <Link href="/(auth)/forgot-password" asChild>
            <Text className="text-primary text-right mb-6">Forgot Password?</Text>
          </Link>

          <Button
            title={isPending ? 'Signing in...' : 'Sign In'}
            onPress={handleSubmit(onSubmit)}
            disabled={isPending}
            className="mb-4"
          />

          {isBiometricEnabled && (
            <BiometricButton
              onPress={loginWithBiometrics}
              isLoading={biometricLoading}
              className="mb-4"
            />
          )}

          <View className="flex-row items-center my-6">
            <View className="flex-1 h-px bg-gray-200" />
            <Text className="mx-4 text-gray-400">or continue with</Text>
            <View className="flex-1 h-px bg-gray-200" />
          </View>

          <SocialLoginButtons />

          <View className="flex-row justify-center mt-6">
            <Text className="text-gray-500">Don't have an account? </Text>
            <Link href="/(auth)/register" asChild>
              <Text className="text-primary font-semibold">Sign Up</Text>
            </Link>
          </View>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
```

## Getting Started

### Prerequisites

- Node.js 18+
- Expo CLI
- iOS Simulator or Android Emulator
- Google Cloud Console project (for Google login)
- Apple Developer account (for Apple login)

### Installation

```bash
# Install dependencies
npm install

# Start development server
npx expo start

# Run on iOS
npx expo run:ios

# Run on Android
npx expo run:android
```

### Environment Setup

Create `.env` file:

```env
EXPO_PUBLIC_API_URL=https://api.example.com
EXPO_PUBLIC_GOOGLE_CLIENT_ID=your-google-client-id
EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID=your-ios-client-id
EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID=your-android-client-id
EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID=your-web-client-id
```

### EAS Build Configuration

```json
// eas.json
{
  "build": {
    "development": {
      "developmentClient": true,
      "distribution": "internal"
    },
    "preview": {
      "distribution": "internal"
    },
    "production": {}
  }
}
```

## Testing

```bash
# Run unit tests
npm test

# Run tests with coverage
npm test -- --coverage

# Run E2E tests
npm run test:e2e
```

## Security Best Practices Demonstrated

1. **Secure Token Storage**: Using expo-secure-store with encryption
2. **Token Refresh**: Automatic access token renewal with queue
3. **Biometric Authentication**: Face ID / Touch ID integration
4. **Password Security**: Minimum length, complexity validation
5. **OAuth 2.0**: Proper implementation with PKCE
6. **Session Management**: Secure logout with token invalidation
7. **Protected Routes**: Navigation guards preventing unauthorized access
8. **Input Validation**: Zod schemas for all forms

## Related Templates

- [rn-store.md](../../templates/rn-store.md) - Auth store patterns
- [rn-api.md](../../templates/rn-api.md) - API interceptor patterns
- [rn-navigation.md](../../templates/rn-navigation.md) - Protected routes
- [rn-screen.md](../../templates/rn-screen.md) - Form screen patterns
