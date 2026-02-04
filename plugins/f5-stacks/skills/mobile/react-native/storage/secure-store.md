---
name: rn-secure-store
description: Secure storage for sensitive data in React Native
applies_to: react-native
---

# Expo SecureStore

## Overview

SecureStore provides encrypted key-value storage using the device's secure enclave:
- **iOS**: Uses Keychain Services
- **Android**: Uses SharedPreferences encrypted with Android Keystore

## Installation

```bash
npx expo install expo-secure-store
```

## Basic Usage

```typescript
import * as SecureStore from 'expo-secure-store';

// Store value
await SecureStore.setItemAsync('authToken', 'your-jwt-token');

// Get value
const token = await SecureStore.getItemAsync('authToken');

// Delete value
await SecureStore.deleteItemAsync('authToken');

// Check if available (always true on real devices, may be false in some simulators)
const isAvailable = await SecureStore.isAvailableAsync();
```

## Secure Token Management

```typescript
// src/lib/secureStorage.ts
import * as SecureStore from 'expo-secure-store';

const KEYS = {
  AUTH_TOKEN: 'auth_token',
  REFRESH_TOKEN: 'refresh_token',
  USER_PIN: 'user_pin',
  BIOMETRIC_KEY: 'biometric_key',
} as const;

export const secureStorage = {
  // Auth tokens
  setAuthToken: async (token: string): Promise<void> => {
    await SecureStore.setItemAsync(KEYS.AUTH_TOKEN, token);
  },

  getAuthToken: async (): Promise<string | null> => {
    return SecureStore.getItemAsync(KEYS.AUTH_TOKEN);
  },

  setRefreshToken: async (token: string): Promise<void> => {
    await SecureStore.setItemAsync(KEYS.REFRESH_TOKEN, token);
  },

  getRefreshToken: async (): Promise<string | null> => {
    return SecureStore.getItemAsync(KEYS.REFRESH_TOKEN);
  },

  // Clear all auth data
  clearAuth: async (): Promise<void> => {
    await Promise.all([
      SecureStore.deleteItemAsync(KEYS.AUTH_TOKEN),
      SecureStore.deleteItemAsync(KEYS.REFRESH_TOKEN),
    ]);
  },

  // PIN management
  setPin: async (pin: string): Promise<void> => {
    await SecureStore.setItemAsync(KEYS.USER_PIN, pin);
  },

  verifyPin: async (pin: string): Promise<boolean> => {
    const storedPin = await SecureStore.getItemAsync(KEYS.USER_PIN);
    return storedPin === pin;
  },

  hasPin: async (): Promise<boolean> => {
    const pin = await SecureStore.getItemAsync(KEYS.USER_PIN);
    return pin !== null;
  },

  clearPin: async (): Promise<void> => {
    await SecureStore.deleteItemAsync(KEYS.USER_PIN);
  },
};
```

## Auth Context with SecureStore

```typescript
// src/contexts/AuthContext.tsx
import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import * as SecureStore from 'expo-secure-store';
import { api } from '@/lib/api';
import type { User } from '@/types';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Restore session on app start
  useEffect(() => {
    const restoreSession = async () => {
      try {
        const storedToken = await SecureStore.getItemAsync('authToken');

        if (storedToken) {
          // Set token in API client
          api.defaults.headers.common.Authorization = `Bearer ${storedToken}`;

          // Fetch user profile
          const { data } = await api.get('/auth/me');
          setUser(data);
          setToken(storedToken);
        }
      } catch (error) {
        // Token invalid or expired
        await SecureStore.deleteItemAsync('authToken');
        await SecureStore.deleteItemAsync('refreshToken');
      } finally {
        setIsLoading(false);
      }
    };

    restoreSession();
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const { data } = await api.post('/auth/login', { email, password });

    // Store tokens securely
    await SecureStore.setItemAsync('authToken', data.accessToken);
    await SecureStore.setItemAsync('refreshToken', data.refreshToken);

    // Update API client
    api.defaults.headers.common.Authorization = `Bearer ${data.accessToken}`;

    setUser(data.user);
    setToken(data.accessToken);
  }, []);

  const logout = useCallback(async () => {
    try {
      await api.post('/auth/logout');
    } finally {
      // Clear secure storage
      await SecureStore.deleteItemAsync('authToken');
      await SecureStore.deleteItemAsync('refreshToken');

      // Clear API header
      delete api.defaults.headers.common.Authorization;

      setUser(null);
      setToken(null);
    }
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        isAuthenticated: !!user,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
```

## Biometric Authentication

```typescript
// src/lib/biometric.ts
import * as SecureStore from 'expo-secure-store';
import * as LocalAuthentication from 'expo-local-authentication';

const BIOMETRIC_KEY = 'biometric_enabled';
const BIOMETRIC_SECRET = 'biometric_secret';

export const biometric = {
  // Check if biometric is available
  isAvailable: async (): Promise<boolean> => {
    const compatible = await LocalAuthentication.hasHardwareAsync();
    const enrolled = await LocalAuthentication.isEnrolledAsync();
    return compatible && enrolled;
  },

  // Get available types
  getTypes: async (): Promise<string[]> => {
    const types = await LocalAuthentication.supportedAuthenticationTypesAsync();
    return types.map((type) => {
      switch (type) {
        case LocalAuthentication.AuthenticationType.FACIAL_RECOGNITION:
          return 'Face ID';
        case LocalAuthentication.AuthenticationType.FINGERPRINT:
          return 'Touch ID';
        case LocalAuthentication.AuthenticationType.IRIS:
          return 'Iris';
        default:
          return 'Unknown';
      }
    });
  },

  // Authenticate with biometric
  authenticate: async (reason: string = 'Authenticate'): Promise<boolean> => {
    const result = await LocalAuthentication.authenticateAsync({
      promptMessage: reason,
      cancelLabel: 'Cancel',
      fallbackLabel: 'Use Passcode',
      disableDeviceFallback: false,
    });

    return result.success;
  },

  // Enable biometric login
  enable: async (secret: string): Promise<void> => {
    // Require biometric to enable
    const authenticated = await biometric.authenticate(
      'Enable biometric login'
    );

    if (!authenticated) {
      throw new Error('Biometric authentication failed');
    }

    // Store with biometric requirement
    await SecureStore.setItemAsync(BIOMETRIC_SECRET, secret, {
      requireAuthentication: true,
    });
    await SecureStore.setItemAsync(BIOMETRIC_ENABLED, 'true');
  },

  // Check if enabled
  isEnabled: async (): Promise<boolean> => {
    const enabled = await SecureStore.getItemAsync(BIOMETRIC_KEY);
    return enabled === 'true';
  },

  // Get secret with biometric
  getSecret: async (): Promise<string | null> => {
    const enabled = await biometric.isEnabled();
    if (!enabled) return null;

    try {
      return await SecureStore.getItemAsync(BIOMETRIC_SECRET, {
        requireAuthentication: true,
      });
    } catch {
      return null;
    }
  },

  // Disable biometric
  disable: async (): Promise<void> => {
    await SecureStore.deleteItemAsync(BIOMETRIC_SECRET);
    await SecureStore.deleteItemAsync(BIOMETRIC_KEY);
  },
};
```

## Options and Security Levels

```typescript
// src/lib/secureStoreOptions.ts
import * as SecureStore from 'expo-secure-store';

// Store with biometric requirement (iOS 12+, Android)
await SecureStore.setItemAsync('sensitive_data', 'value', {
  requireAuthentication: true, // Requires biometric/passcode to access
});

// Keychain accessibility options (iOS only)
await SecureStore.setItemAsync('token', 'value', {
  keychainAccessible: SecureStore.WHEN_UNLOCKED, // Default
});

// Available options:
// AFTER_FIRST_UNLOCK - Available after first unlock
// AFTER_FIRST_UNLOCK_THIS_DEVICE_ONLY - Same, but not transferred to new device
// ALWAYS - Always available (least secure)
// ALWAYS_THIS_DEVICE_ONLY - Same, but not transferred
// WHEN_PASSCODE_SET_THIS_DEVICE_ONLY - Only when passcode is set
// WHEN_UNLOCKED - When device is unlocked (default)
// WHEN_UNLOCKED_THIS_DEVICE_ONLY - Same, but not transferred
```

## Credential Storage Pattern

```typescript
// src/lib/credentials.ts
import * as SecureStore from 'expo-secure-store';

interface Credentials {
  username: string;
  password: string;
}

const CREDENTIALS_KEY = 'user_credentials';

export const credentialStorage = {
  save: async (credentials: Credentials): Promise<void> => {
    await SecureStore.setItemAsync(
      CREDENTIALS_KEY,
      JSON.stringify(credentials)
    );
  },

  get: async (): Promise<Credentials | null> => {
    const stored = await SecureStore.getItemAsync(CREDENTIALS_KEY);
    return stored ? JSON.parse(stored) : null;
  },

  clear: async (): Promise<void> => {
    await SecureStore.deleteItemAsync(CREDENTIALS_KEY);
  },

  // Auto-login with stored credentials
  autoLogin: async (
    loginFn: (credentials: Credentials) => Promise<void>
  ): Promise<boolean> => {
    const credentials = await credentialStorage.get();
    if (!credentials) return false;

    try {
      await loginFn(credentials);
      return true;
    } catch {
      // Credentials invalid, clear them
      await credentialStorage.clear();
      return false;
    }
  },
};
```

## Key Limits and Considerations

```typescript
// SecureStore limitations
const LIMITS = {
  KEY_LENGTH: 2048, // Max key length in bytes
  VALUE_SIZE: 2048, // Recommended max value size in bytes
};

// For larger data, encrypt and store elsewhere
import * as Crypto from 'expo-crypto';

async function storeEncrypted(key: string, data: string) {
  // Generate encryption key
  const encryptionKey = await Crypto.getRandomBytesAsync(32);
  const keyHex = Array.from(encryptionKey)
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');

  // Store encryption key in SecureStore
  await SecureStore.setItemAsync(`${key}_encryption_key`, keyHex);

  // Encrypt data (implement your encryption logic)
  const encrypted = await encryptData(data, keyHex);

  // Store encrypted data in AsyncStorage or MMKV
  await AsyncStorage.setItem(key, encrypted);
}
```

## Best Practices

1. **Tokens Only**: Use SecureStore for auth tokens, not large data
2. **Size Limits**: Keep values under 2KB for best performance
3. **Error Handling**: Always handle SecureStore failures gracefully
4. **Biometric Protection**: Use requireAuthentication for sensitive data
5. **Clear on Logout**: Remove all secure data when user logs out
6. **Backup Exclusion**: Data is excluded from iCloud/Google backups by default
7. **Device Migration**: Consider THIS_DEVICE_ONLY for non-transferable data
