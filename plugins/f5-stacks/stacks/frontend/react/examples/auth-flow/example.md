# Authentication Flow Example

Complete authentication flow example using React with TypeScript, React Hook Form, Zustand, and JWT token management.

## Overview

This example demonstrates a full-featured authentication system with:
- Login and registration forms
- JWT token management with refresh
- Protected routes
- Role-based access control
- Persistent sessions
- Social login integration

## Project Structure

```
src/
├── features/
│   └── auth/
│       ├── api/
│       │   └── auth.api.ts
│       ├── components/
│       │   ├── LoginForm.tsx
│       │   ├── RegisterForm.tsx
│       │   ├── ForgotPasswordForm.tsx
│       │   ├── ResetPasswordForm.tsx
│       │   ├── SocialLoginButtons.tsx
│       │   └── ProtectedRoute.tsx
│       ├── hooks/
│       │   ├── useAuth.ts
│       │   └── usePermissions.ts
│       ├── pages/
│       │   ├── LoginPage.tsx
│       │   ├── RegisterPage.tsx
│       │   ├── ForgotPasswordPage.tsx
│       │   └── ResetPasswordPage.tsx
│       ├── store/
│       │   └── auth.store.ts
│       ├── types/
│       │   └── auth.types.ts
│       ├── utils/
│       │   └── token.utils.ts
│       ├── providers/
│       │   └── AuthProvider.tsx
│       └── index.ts
├── layouts/
│   └── AuthLayout.tsx
└── lib/
    └── api-client.ts
```

## Types

```typescript
// features/auth/types/auth.types.ts

export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  role: UserRole;
  avatar?: string;
  emailVerified: boolean;
  createdAt: string;
}

export type UserRole = 'admin' | 'user' | 'moderator';

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}

export interface LoginCredentials {
  email: string;
  password: string;
  rememberMe?: boolean;
}

export interface RegisterData {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
}

export interface ForgotPasswordData {
  email: string;
}

export interface ResetPasswordData {
  token: string;
  password: string;
  confirmPassword: string;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export interface Permission {
  action: string;
  subject: string;
}

export type PermissionCheck = (user: User | null) => boolean;
```

## Token Utilities

```typescript
// features/auth/utils/token.utils.ts

import { jwtDecode } from 'jwt-decode';
import type { AuthTokens } from '../types/auth.types';

const ACCESS_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

interface JwtPayload {
  sub: string;
  email: string;
  role: string;
  exp: number;
  iat: number;
}

export const tokenUtils = {
  getAccessToken: (): string | null => {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  },

  getRefreshToken: (): string | null => {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  },

  setTokens: (tokens: AuthTokens): void => {
    localStorage.setItem(ACCESS_TOKEN_KEY, tokens.accessToken);
    localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refreshToken);
  },

  clearTokens: (): void => {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  },

  isTokenExpired: (token: string): boolean => {
    try {
      const decoded = jwtDecode<JwtPayload>(token);
      const currentTime = Date.now() / 1000;
      // Consider token expired 30 seconds before actual expiry
      return decoded.exp < currentTime + 30;
    } catch {
      return true;
    }
  },

  decodeToken: (token: string): JwtPayload | null => {
    try {
      return jwtDecode<JwtPayload>(token);
    } catch {
      return null;
    }
  },

  getTokenExpiryTime: (token: string): number | null => {
    const decoded = tokenUtils.decodeToken(token);
    return decoded?.exp ?? null;
  },
};
```

## Auth Store

```typescript
// features/auth/store/auth.store.ts

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { User, AuthTokens, AuthState } from '../types/auth.types';
import { tokenUtils } from '../utils/token.utils';

interface AuthActions {
  setUser: (user: User | null) => void;
  setTokens: (tokens: AuthTokens) => void;
  setLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;
  logout: () => void;
  reset: () => void;
}

type AuthStore = AuthState & AuthActions;

const initialState: AuthState = {
  user: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,
};

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      ...initialState,

      setUser: (user) =>
        set({
          user,
          isAuthenticated: !!user,
          error: null,
        }),

      setTokens: (tokens) => {
        tokenUtils.setTokens(tokens);
        set({ isAuthenticated: true, error: null });
      },

      setLoading: (isLoading) => set({ isLoading }),

      setError: (error) => set({ error, isLoading: false }),

      logout: () => {
        tokenUtils.clearTokens();
        set({
          user: null,
          isAuthenticated: false,
          error: null,
        });
      },

      reset: () => {
        tokenUtils.clearTokens();
        set(initialState);
      },
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
```

## API Layer

```typescript
// features/auth/api/auth.api.ts

import { apiClient } from '@/lib/api-client';
import type {
  User,
  AuthTokens,
  LoginCredentials,
  RegisterData,
  ForgotPasswordData,
  ResetPasswordData,
} from '../types/auth.types';

export const authApi = {
  login: async (credentials: LoginCredentials): Promise<{ user: User; tokens: AuthTokens }> => {
    const response = await apiClient.post('/auth/login', credentials);
    return response.data;
  },

  register: async (data: RegisterData): Promise<{ user: User; tokens: AuthTokens }> => {
    const response = await apiClient.post('/auth/register', data);
    return response.data;
  },

  logout: async (): Promise<void> => {
    await apiClient.post('/auth/logout');
  },

  refreshToken: async (refreshToken: string): Promise<AuthTokens> => {
    const response = await apiClient.post('/auth/refresh', { refreshToken });
    return response.data;
  },

  getMe: async (): Promise<User> => {
    const response = await apiClient.get('/auth/me');
    return response.data;
  },

  forgotPassword: async (data: ForgotPasswordData): Promise<void> => {
    await apiClient.post('/auth/forgot-password', data);
  },

  resetPassword: async (data: ResetPasswordData): Promise<void> => {
    await apiClient.post('/auth/reset-password', data);
  },

  verifyEmail: async (token: string): Promise<void> => {
    await apiClient.post('/auth/verify-email', { token });
  },

  resendVerificationEmail: async (): Promise<void> => {
    await apiClient.post('/auth/resend-verification');
  },

  // Social login
  socialLogin: async (
    provider: 'google' | 'github' | 'facebook',
    token: string
  ): Promise<{ user: User; tokens: AuthTokens }> => {
    const response = await apiClient.post(`/auth/social/${provider}`, { token });
    return response.data;
  },
};
```

## API Client with Token Refresh

```typescript
// lib/api-client.ts

import axios, { type AxiosInstance, type AxiosError, type InternalAxiosRequestConfig } from 'axios';
import { tokenUtils } from '@/features/auth/utils/token.utils';
import { useAuthStore } from '@/features/auth/store/auth.store';

interface QueueItem {
  resolve: (token: string) => void;
  reject: (error: Error) => void;
}

let isRefreshing = false;
let failedQueue: QueueItem[] = [];

const processQueue = (error: Error | null, token: string | null = null) => {
  failedQueue.forEach((item) => {
    if (error) {
      item.reject(error);
    } else if (token) {
      item.resolve(token);
    }
  });
  failedQueue = [];
};

const createApiClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: import.meta.env.VITE_API_URL ?? '/api',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Request interceptor
  client.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
      const token = tokenUtils.getAccessToken();
      if (token && !config.headers.Authorization) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => Promise.reject(error)
  );

  // Response interceptor with token refresh
  client.interceptors.response.use(
    (response) => response,
    async (error: AxiosError) => {
      const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

      // If error is not 401 or request was already retried, reject
      if (error.response?.status !== 401 || originalRequest._retry) {
        return Promise.reject(error);
      }

      // Skip refresh for auth endpoints
      if (originalRequest.url?.includes('/auth/')) {
        return Promise.reject(error);
      }

      if (isRefreshing) {
        // Queue this request while refreshing
        return new Promise<string>((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return client(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = tokenUtils.getRefreshToken();

      if (!refreshToken) {
        useAuthStore.getState().logout();
        window.location.href = '/login';
        return Promise.reject(error);
      }

      try {
        const response = await axios.post(
          `${import.meta.env.VITE_API_URL}/auth/refresh`,
          { refreshToken }
        );

        const { accessToken, refreshToken: newRefreshToken, expiresIn } = response.data;
        tokenUtils.setTokens({ accessToken, refreshToken: newRefreshToken, expiresIn });

        processQueue(null, accessToken);

        originalRequest.headers.Authorization = `Bearer ${accessToken}`;
        return client(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError as Error, null);
        useAuthStore.getState().logout();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }
  );

  return client;
};

export const apiClient = createApiClient();
```

## Auth Hook

```typescript
// features/auth/hooks/useAuth.ts

import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { authApi } from '../api/auth.api';
import { useAuthStore } from '../store/auth.store';
import { tokenUtils } from '../utils/token.utils';
import type {
  LoginCredentials,
  RegisterData,
  ForgotPasswordData,
  ResetPasswordData,
} from '../types/auth.types';

export function useAuth() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const {
    user,
    isAuthenticated,
    isLoading,
    error,
    setUser,
    setTokens,
    setLoading,
    setError,
    logout: logoutStore,
  } = useAuthStore();

  // Fetch current user on mount
  const { refetch: fetchUser } = useQuery({
    queryKey: ['auth', 'me'],
    queryFn: authApi.getMe,
    enabled: !!tokenUtils.getAccessToken() && isAuthenticated,
    retry: false,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });

  // Login mutation
  const loginMutation = useMutation({
    mutationFn: authApi.login,
    onSuccess: ({ user, tokens }) => {
      setTokens(tokens);
      setUser(user);
      queryClient.invalidateQueries({ queryKey: ['auth'] });
      navigate('/dashboard');
    },
    onError: (error: Error) => {
      setError(error.message);
    },
  });

  // Register mutation
  const registerMutation = useMutation({
    mutationFn: authApi.register,
    onSuccess: ({ user, tokens }) => {
      setTokens(tokens);
      setUser(user);
      queryClient.invalidateQueries({ queryKey: ['auth'] });
      navigate('/dashboard');
    },
    onError: (error: Error) => {
      setError(error.message);
    },
  });

  // Logout mutation
  const logoutMutation = useMutation({
    mutationFn: authApi.logout,
    onSuccess: () => {
      logoutStore();
      queryClient.clear();
      navigate('/login');
    },
    onError: () => {
      // Logout locally even if API call fails
      logoutStore();
      queryClient.clear();
      navigate('/login');
    },
  });

  // Forgot password mutation
  const forgotPasswordMutation = useMutation({
    mutationFn: authApi.forgotPassword,
  });

  // Reset password mutation
  const resetPasswordMutation = useMutation({
    mutationFn: authApi.resetPassword,
    onSuccess: () => {
      navigate('/login', { state: { message: 'Password reset successful' } });
    },
  });

  // Social login
  const socialLoginMutation = useMutation({
    mutationFn: ({ provider, token }: { provider: 'google' | 'github' | 'facebook'; token: string }) =>
      authApi.socialLogin(provider, token),
    onSuccess: ({ user, tokens }) => {
      setTokens(tokens);
      setUser(user);
      queryClient.invalidateQueries({ queryKey: ['auth'] });
      navigate('/dashboard');
    },
    onError: (error: Error) => {
      setError(error.message);
    },
  });

  const login = useCallback(
    (credentials: LoginCredentials) => loginMutation.mutate(credentials),
    [loginMutation]
  );

  const register = useCallback(
    (data: RegisterData) => registerMutation.mutate(data),
    [registerMutation]
  );

  const logout = useCallback(() => logoutMutation.mutate(), [logoutMutation]);

  const forgotPassword = useCallback(
    (data: ForgotPasswordData) => forgotPasswordMutation.mutateAsync(data),
    [forgotPasswordMutation]
  );

  const resetPassword = useCallback(
    (data: ResetPasswordData) => resetPasswordMutation.mutate(data),
    [resetPasswordMutation]
  );

  const socialLogin = useCallback(
    (provider: 'google' | 'github' | 'facebook', token: string) =>
      socialLoginMutation.mutate({ provider, token }),
    [socialLoginMutation]
  );

  return {
    user,
    isAuthenticated,
    isLoading: isLoading || loginMutation.isPending || registerMutation.isPending,
    error,
    login,
    register,
    logout,
    forgotPassword,
    resetPassword,
    socialLogin,
    isLoginLoading: loginMutation.isPending,
    isRegisterLoading: registerMutation.isPending,
    isForgotPasswordLoading: forgotPasswordMutation.isPending,
    isResetPasswordLoading: resetPasswordMutation.isPending,
    forgotPasswordSuccess: forgotPasswordMutation.isSuccess,
  };
}
```

## Permissions Hook

```typescript
// features/auth/hooks/usePermissions.ts

import { useMemo } from 'react';
import { useAuthStore } from '../store/auth.store';
import type { UserRole, PermissionCheck } from '../types/auth.types';

// Define role hierarchy
const roleHierarchy: Record<UserRole, number> = {
  user: 1,
  moderator: 2,
  admin: 3,
};

// Define permissions by role
const rolePermissions: Record<UserRole, string[]> = {
  user: ['read:own-profile', 'update:own-profile'],
  moderator: [
    'read:own-profile',
    'update:own-profile',
    'read:users',
    'update:users',
    'read:content',
    'update:content',
    'delete:content',
  ],
  admin: [
    'read:own-profile',
    'update:own-profile',
    'read:users',
    'create:users',
    'update:users',
    'delete:users',
    'read:content',
    'create:content',
    'update:content',
    'delete:content',
    'read:settings',
    'update:settings',
  ],
};

export function usePermissions() {
  const { user } = useAuthStore();

  const permissions = useMemo(() => {
    if (!user) return [];
    return rolePermissions[user.role] ?? [];
  }, [user]);

  const hasPermission = (permission: string): boolean => {
    return permissions.includes(permission);
  };

  const hasAnyPermission = (perms: string[]): boolean => {
    return perms.some((p) => permissions.includes(p));
  };

  const hasAllPermissions = (perms: string[]): boolean => {
    return perms.every((p) => permissions.includes(p));
  };

  const hasRole = (role: UserRole): boolean => {
    if (!user) return false;
    return roleHierarchy[user.role] >= roleHierarchy[role];
  };

  const hasExactRole = (role: UserRole): boolean => {
    return user?.role === role;
  };

  const can: PermissionCheck = (checkUser) => {
    return !!checkUser;
  };

  return {
    permissions,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    hasRole,
    hasExactRole,
    isAdmin: user?.role === 'admin',
    isModerator: user?.role === 'moderator' || user?.role === 'admin',
    can,
  };
}
```

## Auth Provider

```typescript
// features/auth/providers/AuthProvider.tsx

import { useEffect, type ReactNode } from 'react';
import { useQuery } from '@tanstack/react-query';
import { authApi } from '../api/auth.api';
import { useAuthStore } from '../store/auth.store';
import { tokenUtils } from '../utils/token.utils';

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const { setUser, setLoading, logout, isAuthenticated } = useAuthStore();

  // Check authentication on mount
  const { data: user, isLoading } = useQuery({
    queryKey: ['auth', 'me'],
    queryFn: authApi.getMe,
    enabled: !!tokenUtils.getAccessToken(),
    retry: false,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });

  useEffect(() => {
    const accessToken = tokenUtils.getAccessToken();

    if (!accessToken) {
      setLoading(false);
      return;
    }

    // Check if token is expired
    if (tokenUtils.isTokenExpired(accessToken)) {
      const refreshToken = tokenUtils.getRefreshToken();

      if (refreshToken && !tokenUtils.isTokenExpired(refreshToken)) {
        // Token will be refreshed by the API client interceptor
        setLoading(false);
      } else {
        logout();
      }
    } else {
      setLoading(false);
    }
  }, [setLoading, logout]);

  useEffect(() => {
    if (user) {
      setUser(user);
    }
    setLoading(isLoading);
  }, [user, isLoading, setUser, setLoading]);

  // Set up token refresh timer
  useEffect(() => {
    if (!isAuthenticated) return;

    const accessToken = tokenUtils.getAccessToken();
    if (!accessToken) return;

    const expiryTime = tokenUtils.getTokenExpiryTime(accessToken);
    if (!expiryTime) return;

    // Refresh 1 minute before expiry
    const refreshTime = (expiryTime - 60) * 1000 - Date.now();

    if (refreshTime <= 0) return;

    const timeoutId = setTimeout(async () => {
      const refreshToken = tokenUtils.getRefreshToken();
      if (refreshToken) {
        try {
          const tokens = await authApi.refreshToken(refreshToken);
          useAuthStore.getState().setTokens(tokens);
        } catch {
          logout();
        }
      }
    }, refreshTime);

    return () => clearTimeout(timeoutId);
  }, [isAuthenticated, logout]);

  return <>{children}</>;
}
```

## Components

```typescript
// features/auth/components/LoginForm.tsx

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { SocialLoginButtons } from './SocialLoginButtons';

const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(1, 'Password is required'),
  rememberMe: z.boolean().optional(),
});

type LoginFormData = z.infer<typeof loginSchema>;

export function LoginForm() {
  const { login, isLoginLoading, error } = useAuth();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      rememberMe: false,
    },
  });

  const onSubmit = (data: LoginFormData) => {
    login(data);
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h1 className="text-2xl font-bold">Welcome back</h1>
        <p className="text-gray-600 mt-2">Sign in to your account</p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <label htmlFor="email" className="block text-sm font-medium">
            Email
          </label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            {...register('email')}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
          {errors.email && (
            <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>
          )}
        </div>

        <div>
          <label htmlFor="password" className="block text-sm font-medium">
            Password
          </label>
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            {...register('password')}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
          {errors.password && (
            <p className="mt-1 text-sm text-red-600">{errors.password.message}</p>
          )}
        </div>

        <div className="flex items-center justify-between">
          <label className="flex items-center">
            <input
              type="checkbox"
              {...register('rememberMe')}
              className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="ml-2 text-sm text-gray-600">Remember me</span>
          </label>
          <Link
            to="/forgot-password"
            className="text-sm text-blue-600 hover:underline"
          >
            Forgot password?
          </Link>
        </div>

        <button
          type="submit"
          disabled={isLoginLoading}
          className="w-full py-2 px-4 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoginLoading ? 'Signing in...' : 'Sign in'}
        </button>
      </form>

      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-gray-300" />
        </div>
        <div className="relative flex justify-center text-sm">
          <span className="px-2 bg-white text-gray-500">Or continue with</span>
        </div>
      </div>

      <SocialLoginButtons />

      <p className="text-center text-sm text-gray-600">
        Don't have an account?{' '}
        <Link to="/register" className="text-blue-600 hover:underline">
          Sign up
        </Link>
      </p>
    </div>
  );
}
```

```typescript
// features/auth/components/RegisterForm.tsx

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { SocialLoginButtons } from './SocialLoginButtons';

const registerSchema = z
  .object({
    firstName: z.string().min(1, 'First name is required'),
    lastName: z.string().min(1, 'Last name is required'),
    email: z.string().email('Invalid email address'),
    password: z
      .string()
      .min(8, 'Password must be at least 8 characters')
      .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
      .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
      .regex(/[0-9]/, 'Password must contain at least one number'),
    confirmPassword: z.string(),
    acceptTerms: z.boolean().refine((val) => val === true, {
      message: 'You must accept the terms and conditions',
    }),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  });

type RegisterFormData = z.infer<typeof registerSchema>;

export function RegisterForm() {
  const { register: registerUser, isRegisterLoading, error } = useAuth();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = (data: RegisterFormData) => {
    const { confirmPassword, acceptTerms, ...registerData } = data;
    registerUser(registerData);
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h1 className="text-2xl font-bold">Create an account</h1>
        <p className="text-gray-600 mt-2">Get started with your free account</p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="firstName" className="block text-sm font-medium">
              First name
            </label>
            <input
              id="firstName"
              type="text"
              autoComplete="given-name"
              {...register('firstName')}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            {errors.firstName && (
              <p className="mt-1 text-sm text-red-600">{errors.firstName.message}</p>
            )}
          </div>
          <div>
            <label htmlFor="lastName" className="block text-sm font-medium">
              Last name
            </label>
            <input
              id="lastName"
              type="text"
              autoComplete="family-name"
              {...register('lastName')}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            {errors.lastName && (
              <p className="mt-1 text-sm text-red-600">{errors.lastName.message}</p>
            )}
          </div>
        </div>

        <div>
          <label htmlFor="email" className="block text-sm font-medium">
            Email
          </label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            {...register('email')}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
          {errors.email && (
            <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>
          )}
        </div>

        <div>
          <label htmlFor="password" className="block text-sm font-medium">
            Password
          </label>
          <input
            id="password"
            type="password"
            autoComplete="new-password"
            {...register('password')}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
          {errors.password && (
            <p className="mt-1 text-sm text-red-600">{errors.password.message}</p>
          )}
        </div>

        <div>
          <label htmlFor="confirmPassword" className="block text-sm font-medium">
            Confirm password
          </label>
          <input
            id="confirmPassword"
            type="password"
            autoComplete="new-password"
            {...register('confirmPassword')}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
          {errors.confirmPassword && (
            <p className="mt-1 text-sm text-red-600">{errors.confirmPassword.message}</p>
          )}
        </div>

        <div>
          <label className="flex items-start">
            <input
              type="checkbox"
              {...register('acceptTerms')}
              className="h-4 w-4 mt-1 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="ml-2 text-sm text-gray-600">
              I agree to the{' '}
              <Link to="/terms" className="text-blue-600 hover:underline">
                Terms of Service
              </Link>{' '}
              and{' '}
              <Link to="/privacy" className="text-blue-600 hover:underline">
                Privacy Policy
              </Link>
            </span>
          </label>
          {errors.acceptTerms && (
            <p className="mt-1 text-sm text-red-600">{errors.acceptTerms.message}</p>
          )}
        </div>

        <button
          type="submit"
          disabled={isRegisterLoading}
          className="w-full py-2 px-4 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isRegisterLoading ? 'Creating account...' : 'Create account'}
        </button>
      </form>

      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-gray-300" />
        </div>
        <div className="relative flex justify-center text-sm">
          <span className="px-2 bg-white text-gray-500">Or continue with</span>
        </div>
      </div>

      <SocialLoginButtons />

      <p className="text-center text-sm text-gray-600">
        Already have an account?{' '}
        <Link to="/login" className="text-blue-600 hover:underline">
          Sign in
        </Link>
      </p>
    </div>
  );
}
```

```typescript
// features/auth/components/ForgotPasswordForm.tsx

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link } from 'react-router-dom';
import { ArrowLeft, Mail } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

const forgotPasswordSchema = z.object({
  email: z.string().email('Invalid email address'),
});

type ForgotPasswordFormData = z.infer<typeof forgotPasswordSchema>;

export function ForgotPasswordForm() {
  const { forgotPassword, isForgotPasswordLoading, forgotPasswordSuccess } = useAuth();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotPasswordFormData>({
    resolver: zodResolver(forgotPasswordSchema),
  });

  const onSubmit = async (data: ForgotPasswordFormData) => {
    await forgotPassword(data);
  };

  if (forgotPasswordSuccess) {
    return (
      <div className="text-center space-y-4">
        <div className="mx-auto w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
          <Mail className="h-6 w-6 text-green-600" />
        </div>
        <h1 className="text-2xl font-bold">Check your email</h1>
        <p className="text-gray-600">
          We've sent you a link to reset your password. Please check your inbox.
        </p>
        <Link
          to="/login"
          className="inline-flex items-center text-blue-600 hover:underline"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to login
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h1 className="text-2xl font-bold">Forgot password?</h1>
        <p className="text-gray-600 mt-2">
          Enter your email and we'll send you a reset link
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <label htmlFor="email" className="block text-sm font-medium">
            Email
          </label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            {...register('email')}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
          {errors.email && (
            <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>
          )}
        </div>

        <button
          type="submit"
          disabled={isForgotPasswordLoading}
          className="w-full py-2 px-4 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isForgotPasswordLoading ? 'Sending...' : 'Send reset link'}
        </button>
      </form>

      <Link
        to="/login"
        className="flex items-center justify-center text-sm text-gray-600 hover:text-gray-900"
      >
        <ArrowLeft className="h-4 w-4 mr-2" />
        Back to login
      </Link>
    </div>
  );
}
```

```typescript
// features/auth/components/SocialLoginButtons.tsx

import { useAuth } from '../hooks/useAuth';

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: GoogleConfig) => void;
          renderButton: (element: HTMLElement, options: GoogleButtonOptions) => void;
        };
      };
    };
  }
}

interface GoogleConfig {
  client_id: string;
  callback: (response: { credential: string }) => void;
}

interface GoogleButtonOptions {
  theme: 'outline' | 'filled_blue' | 'filled_black';
  size: 'large' | 'medium' | 'small';
  width: string;
}

export function SocialLoginButtons() {
  const { socialLogin } = useAuth();

  const handleGoogleLogin = () => {
    // Google Sign-In implementation
    // This would typically use @react-oauth/google or similar
    console.log('Google login clicked');
  };

  const handleGitHubLogin = () => {
    // Redirect to GitHub OAuth
    const clientId = import.meta.env.VITE_GITHUB_CLIENT_ID;
    const redirectUri = `${window.location.origin}/auth/github/callback`;
    window.location.href = `https://github.com/login/oauth/authorize?client_id=${clientId}&redirect_uri=${redirectUri}&scope=user:email`;
  };

  return (
    <div className="grid grid-cols-2 gap-4">
      <button
        type="button"
        onClick={handleGoogleLogin}
        className="flex items-center justify-center gap-2 px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
      >
        <svg className="h-5 w-5" viewBox="0 0 24 24">
          <path
            fill="#4285F4"
            d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
          />
          <path
            fill="#34A853"
            d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
          />
          <path
            fill="#FBBC05"
            d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
          />
          <path
            fill="#EA4335"
            d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
          />
        </svg>
        Google
      </button>

      <button
        type="button"
        onClick={handleGitHubLogin}
        className="flex items-center justify-center gap-2 px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
      >
        <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
          <path
            fillRule="evenodd"
            d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
            clipRule="evenodd"
          />
        </svg>
        GitHub
      </button>
    </div>
  );
}
```

```typescript
// features/auth/components/ProtectedRoute.tsx

import { Navigate, useLocation, type ReactNode } from 'react-router-dom';
import { useAuthStore } from '../store/auth.store';
import { usePermissions } from '../hooks/usePermissions';
import type { UserRole } from '../types/auth.types';

interface ProtectedRouteProps {
  children: ReactNode;
  requiredRole?: UserRole;
  requiredPermissions?: string[];
  requireAll?: boolean;
  fallback?: ReactNode;
}

export function ProtectedRoute({
  children,
  requiredRole,
  requiredPermissions,
  requireAll = true,
  fallback,
}: ProtectedRouteProps) {
  const location = useLocation();
  const { isAuthenticated, isLoading } = useAuthStore();
  const { hasRole, hasPermission, hasAllPermissions, hasAnyPermission } = usePermissions();

  // Show loading state while checking auth
  if (isLoading) {
    return (
      fallback ?? (
        <div className="min-h-screen flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        </div>
      )
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check role requirement
  if (requiredRole && !hasRole(requiredRole)) {
    return <Navigate to="/unauthorized" replace />;
  }

  // Check permission requirements
  if (requiredPermissions && requiredPermissions.length > 0) {
    const hasRequiredPermissions = requireAll
      ? hasAllPermissions(requiredPermissions)
      : hasAnyPermission(requiredPermissions);

    if (!hasRequiredPermissions) {
      return <Navigate to="/unauthorized" replace />;
    }
  }

  return <>{children}</>;
}
```

## Pages

```typescript
// features/auth/pages/LoginPage.tsx

import { AuthLayout } from '@/layouts/AuthLayout';
import { LoginForm } from '../components/LoginForm';

export function LoginPage() {
  return (
    <AuthLayout>
      <LoginForm />
    </AuthLayout>
  );
}
```

```typescript
// features/auth/pages/RegisterPage.tsx

import { AuthLayout } from '@/layouts/AuthLayout';
import { RegisterForm } from '../components/RegisterForm';

export function RegisterPage() {
  return (
    <AuthLayout>
      <RegisterForm />
    </AuthLayout>
  );
}
```

```typescript
// features/auth/pages/ForgotPasswordPage.tsx

import { AuthLayout } from '@/layouts/AuthLayout';
import { ForgotPasswordForm } from '../components/ForgotPasswordForm';

export function ForgotPasswordPage() {
  return (
    <AuthLayout>
      <ForgotPasswordForm />
    </AuthLayout>
  );
}
```

## Auth Layout

```typescript
// layouts/AuthLayout.tsx

import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';

interface AuthLayoutProps {
  children: ReactNode;
}

export function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="min-h-screen flex">
      {/* Left side - Form */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-md">{children}</div>
      </div>

      {/* Right side - Branding */}
      <div className="hidden lg:flex flex-1 bg-gradient-to-br from-blue-600 to-blue-800 items-center justify-center p-8">
        <div className="text-white text-center">
          <h2 className="text-4xl font-bold mb-4">Welcome</h2>
          <p className="text-blue-100 text-lg">
            Sign in to access your account and start exploring.
          </p>
        </div>
      </div>
    </div>
  );
}
```

## Route Configuration

```typescript
// app/routes.tsx

import { createBrowserRouter, Navigate } from 'react-router-dom';
import { MainLayout } from '@/layouts/MainLayout';
import { LoginPage, RegisterPage, ForgotPasswordPage } from '@/features/auth';
import { ProtectedRoute } from '@/features/auth/components/ProtectedRoute';
import { DashboardPage } from '@/features/dashboard/pages/DashboardPage';
import { UnauthorizedPage } from '@/pages/UnauthorizedPage';

export const router = createBrowserRouter([
  // Public routes
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/register',
    element: <RegisterPage />,
  },
  {
    path: '/forgot-password',
    element: <ForgotPasswordPage />,
  },

  // Protected routes
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <MainLayout />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: <Navigate to="/dashboard" replace />,
      },
      {
        path: 'dashboard',
        element: <DashboardPage />,
      },
      // Admin only routes
      {
        path: 'admin',
        element: (
          <ProtectedRoute requiredRole="admin">
            <AdminPage />
          </ProtectedRoute>
        ),
      },
      // Routes requiring specific permissions
      {
        path: 'settings',
        element: (
          <ProtectedRoute requiredPermissions={['read:settings']}>
            <SettingsPage />
          </ProtectedRoute>
        ),
      },
    ],
  },

  // Error routes
  {
    path: '/unauthorized',
    element: <UnauthorizedPage />,
  },
]);
```

## App Setup

```typescript
// app/App.tsx

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { RouterProvider } from 'react-router-dom';
import { AuthProvider } from '@/features/auth/providers/AuthProvider';
import { router } from './routes';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 1000 * 60 * 5, // 5 minutes
      refetchOnWindowFocus: false,
    },
  },
});

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <RouterProvider router={router} />
      </AuthProvider>
    </QueryClientProvider>
  );
}
```

## Testing

```typescript
// features/auth/__tests__/useAuth.test.tsx

import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';
import { useAuth } from '../hooks/useAuth';
import { useAuthStore } from '../store/auth.store';
import type { ReactNode } from 'react';

const mockUser = {
  id: '1',
  email: 'test@example.com',
  firstName: 'Test',
  lastName: 'User',
  role: 'user',
  emailVerified: true,
  createdAt: '2024-01-01T00:00:00Z',
};

const mockTokens = {
  accessToken: 'mock-access-token',
  refreshToken: 'mock-refresh-token',
  expiresIn: 3600,
};

const server = setupServer(
  http.post('/api/auth/login', () => {
    return HttpResponse.json({ user: mockUser, tokens: mockTokens });
  }),
  http.post('/api/auth/register', () => {
    return HttpResponse.json({ user: mockUser, tokens: mockTokens });
  }),
  http.post('/api/auth/logout', () => {
    return new HttpResponse(null, { status: 204 });
  }),
  http.get('/api/auth/me', () => {
    return HttpResponse.json(mockUser);
  })
);

beforeAll(() => server.listen());
afterEach(() => {
  server.resetHandlers();
  useAuthStore.getState().reset();
});
afterAll(() => server.close());

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{children}</BrowserRouter>
    </QueryClientProvider>
  );
}

describe('useAuth', () => {
  it('should login successfully', async () => {
    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(),
    });

    act(() => {
      result.current.login({
        email: 'test@example.com',
        password: 'password123',
      });
    });

    await waitFor(() => {
      expect(result.current.isAuthenticated).toBe(true);
    });

    expect(result.current.user?.email).toBe('test@example.com');
  });

  it('should handle login error', async () => {
    server.use(
      http.post('/api/auth/login', () => {
        return HttpResponse.json(
          { message: 'Invalid credentials' },
          { status: 401 }
        );
      })
    );

    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(),
    });

    act(() => {
      result.current.login({
        email: 'test@example.com',
        password: 'wrongpassword',
      });
    });

    await waitFor(() => {
      expect(result.current.error).toBeTruthy();
    });
  });

  it('should logout successfully', async () => {
    // First login
    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(),
    });

    act(() => {
      result.current.login({
        email: 'test@example.com',
        password: 'password123',
      });
    });

    await waitFor(() => {
      expect(result.current.isAuthenticated).toBe(true);
    });

    // Then logout
    act(() => {
      result.current.logout();
    });

    await waitFor(() => {
      expect(result.current.isAuthenticated).toBe(false);
    });
  });
});
```

## Usage

1. Install dependencies:
```bash
npm install @tanstack/react-query zustand react-hook-form @hookform/resolvers zod axios jwt-decode lucide-react
```

2. Set up environment variables:
```env
VITE_API_URL=http://localhost:3001/api
VITE_GITHUB_CLIENT_ID=your_github_client_id
VITE_GOOGLE_CLIENT_ID=your_google_client_id
```

3. Wrap your app with providers
4. Configure routes with ProtectedRoute
5. Use the useAuth hook in your components

## Key Patterns Demonstrated

- **JWT Token Management**: Secure storage and automatic refresh
- **Optimistic Auth State**: Immediate UI feedback
- **Role-Based Access Control**: Hierarchical permissions
- **Protected Routes**: Route-level authorization
- **Social Login Integration**: OAuth 2.0 flow
- **Form Validation**: Comprehensive with Zod schemas
- **Error Handling**: Graceful error states and recovery
- **Session Persistence**: Zustand persist middleware
- **Token Refresh**: Automatic silent refresh with queue
