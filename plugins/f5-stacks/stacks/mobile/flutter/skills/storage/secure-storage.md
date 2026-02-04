---
name: flutter-secure-storage
description: Secure storage for sensitive data in Flutter
applies_to: flutter
---

# Flutter Secure Storage

## Overview

flutter_secure_storage provides secure storage for sensitive data using platform-specific encryption (Keychain on iOS, EncryptedSharedPreferences on Android).

## Dependencies

```yaml
dependencies:
  flutter_secure_storage: ^9.0.0
```

## Android Configuration

```xml
<!-- android/app/src/main/AndroidManifest.xml -->
<manifest>
  <application
    android:allowBackup="false"
    ...>
    <!-- Required for API level < 23 -->
  </application>
</manifest>
```

For Android API level below 18, add:
```groovy
// android/app/build.gradle
android {
  defaultConfig {
    minSdkVersion 18
  }
}
```

## Basic Usage

```dart
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class SecureStorageService {
  final FlutterSecureStorage _storage = const FlutterSecureStorage(
    aOptions: AndroidOptions(
      encryptedSharedPreferences: true,
    ),
    iOptions: IOSOptions(
      accessibility: KeychainAccessibility.first_unlock_this_device,
    ),
  );

  // Write
  Future<void> write(String key, String value) async {
    await _storage.write(key: key, value: value);
  }

  // Read
  Future<String?> read(String key) async {
    return _storage.read(key: key);
  }

  // Delete
  Future<void> delete(String key) async {
    await _storage.delete(key: key);
  }

  // Delete all
  Future<void> deleteAll() async {
    await _storage.deleteAll();
  }

  // Check if key exists
  Future<bool> containsKey(String key) async {
    return _storage.containsKey(key: key);
  }

  // Read all
  Future<Map<String, String>> readAll() async {
    return _storage.readAll();
  }
}
```

## Token Storage Service

```dart
abstract class TokenStorage {
  Future<String?> getAccessToken();
  Future<String?> getRefreshToken();
  Future<void> saveTokens({required String accessToken, required String refreshToken});
  Future<void> clear();
  Future<bool> hasTokens();
}

class SecureTokenStorage implements TokenStorage {
  final FlutterSecureStorage _storage;

  static const _accessTokenKey = 'access_token';
  static const _refreshTokenKey = 'refresh_token';
  static const _tokenExpiryKey = 'token_expiry';

  SecureTokenStorage({FlutterSecureStorage? storage})
      : _storage = storage ??
            const FlutterSecureStorage(
              aOptions: AndroidOptions(encryptedSharedPreferences: true),
              iOptions: IOSOptions(
                accessibility: KeychainAccessibility.first_unlock_this_device,
              ),
            );

  @override
  Future<String?> getAccessToken() async {
    // Check if token is expired
    final expiry = await _storage.read(key: _tokenExpiryKey);
    if (expiry != null) {
      final expiryTime = DateTime.parse(expiry);
      if (DateTime.now().isAfter(expiryTime)) {
        return null; // Token expired
      }
    }
    return _storage.read(key: _accessTokenKey);
  }

  @override
  Future<String?> getRefreshToken() {
    return _storage.read(key: _refreshTokenKey);
  }

  @override
  Future<void> saveTokens({
    required String accessToken,
    required String refreshToken,
    Duration? expiresIn,
  }) async {
    await Future.wait([
      _storage.write(key: _accessTokenKey, value: accessToken),
      _storage.write(key: _refreshTokenKey, value: refreshToken),
      if (expiresIn != null)
        _storage.write(
          key: _tokenExpiryKey,
          value: DateTime.now().add(expiresIn).toIso8601String(),
        ),
    ]);
  }

  @override
  Future<void> clear() async {
    await Future.wait([
      _storage.delete(key: _accessTokenKey),
      _storage.delete(key: _refreshTokenKey),
      _storage.delete(key: _tokenExpiryKey),
    ]);
  }

  @override
  Future<bool> hasTokens() async {
    final accessToken = await getAccessToken();
    return accessToken != null;
  }
}
```

## Credential Storage

```dart
class CredentialStorage {
  final FlutterSecureStorage _storage;

  static const _usernameKey = 'saved_username';
  static const _passwordKey = 'saved_password';
  static const _biometricEnabledKey = 'biometric_enabled';

  CredentialStorage({FlutterSecureStorage? storage})
      : _storage = storage ?? const FlutterSecureStorage();

  Future<Credentials?> getSavedCredentials() async {
    final username = await _storage.read(key: _usernameKey);
    final password = await _storage.read(key: _passwordKey);

    if (username != null && password != null) {
      return Credentials(username: username, password: password);
    }
    return null;
  }

  Future<void> saveCredentials(Credentials credentials) async {
    await Future.wait([
      _storage.write(key: _usernameKey, value: credentials.username),
      _storage.write(key: _passwordKey, value: credentials.password),
    ]);
  }

  Future<void> clearCredentials() async {
    await Future.wait([
      _storage.delete(key: _usernameKey),
      _storage.delete(key: _passwordKey),
    ]);
  }

  Future<bool> isBiometricEnabled() async {
    final value = await _storage.read(key: _biometricEnabledKey);
    return value == 'true';
  }

  Future<void> setBiometricEnabled(bool enabled) async {
    await _storage.write(
      key: _biometricEnabledKey,
      value: enabled.toString(),
    );
  }
}

class Credentials {
  final String username;
  final String password;

  Credentials({required this.username, required this.password});
}
```

## Biometric Authentication Integration

```dart
import 'package:local_auth/local_auth.dart';

class BiometricAuthService {
  final LocalAuthentication _localAuth = LocalAuthentication();
  final CredentialStorage _credentialStorage;

  BiometricAuthService(this._credentialStorage);

  Future<bool> isBiometricAvailable() async {
    try {
      final canCheckBiometrics = await _localAuth.canCheckBiometrics;
      final isDeviceSupported = await _localAuth.isDeviceSupported();
      return canCheckBiometrics && isDeviceSupported;
    } catch (e) {
      return false;
    }
  }

  Future<List<BiometricType>> getAvailableBiometrics() async {
    try {
      return await _localAuth.getAvailableBiometrics();
    } catch (e) {
      return [];
    }
  }

  Future<Credentials?> authenticateAndGetCredentials() async {
    final isEnabled = await _credentialStorage.isBiometricEnabled();
    if (!isEnabled) return null;

    try {
      final authenticated = await _localAuth.authenticate(
        localizedReason: 'Authenticate to access your account',
        options: const AuthenticationOptions(
          stickyAuth: true,
          biometricOnly: true,
        ),
      );

      if (authenticated) {
        return _credentialStorage.getSavedCredentials();
      }
    } catch (e) {
      // Handle error
    }
    return null;
  }

  Future<void> enableBiometricLogin(Credentials credentials) async {
    await _credentialStorage.saveCredentials(credentials);
    await _credentialStorage.setBiometricEnabled(true);
  }

  Future<void> disableBiometricLogin() async {
    await _credentialStorage.clearCredentials();
    await _credentialStorage.setBiometricEnabled(false);
  }
}
```

## API Key Storage

```dart
class ApiKeyStorage {
  final FlutterSecureStorage _storage;

  static const _apiKeyPrefix = 'api_key_';

  ApiKeyStorage({FlutterSecureStorage? storage})
      : _storage = storage ?? const FlutterSecureStorage();

  Future<void> saveApiKey(String service, String apiKey) async {
    await _storage.write(key: '$_apiKeyPrefix$service', value: apiKey);
  }

  Future<String?> getApiKey(String service) async {
    return _storage.read(key: '$_apiKeyPrefix$service');
  }

  Future<void> deleteApiKey(String service) async {
    await _storage.delete(key: '$_apiKeyPrefix$service');
  }

  Future<Map<String, String>> getAllApiKeys() async {
    final all = await _storage.readAll();
    return Map.fromEntries(
      all.entries
          .where((e) => e.key.startsWith(_apiKeyPrefix))
          .map((e) => MapEntry(e.key.substring(_apiKeyPrefix.length), e.value)),
    );
  }
}
```

## Encryption Key Management

```dart
class EncryptionKeyManager {
  final FlutterSecureStorage _storage;
  static const _encryptionKeyKey = 'app_encryption_key';

  EncryptionKeyManager({FlutterSecureStorage? storage})
      : _storage = storage ?? const FlutterSecureStorage();

  Future<Uint8List> getOrCreateEncryptionKey() async {
    final existingKey = await _storage.read(key: _encryptionKeyKey);

    if (existingKey != null) {
      return base64Decode(existingKey);
    }

    // Generate new 256-bit key
    final random = Random.secure();
    final key = Uint8List.fromList(
      List.generate(32, (_) => random.nextInt(256)),
    );

    await _storage.write(
      key: _encryptionKeyKey,
      value: base64Encode(key),
    );

    return key;
  }

  Future<void> rotateEncryptionKey(
    Future<void> Function(Uint8List oldKey, Uint8List newKey) onRotate,
  ) async {
    final oldKey = await getOrCreateEncryptionKey();

    // Generate new key
    final random = Random.secure();
    final newKey = Uint8List.fromList(
      List.generate(32, (_) => random.nextInt(256)),
    );

    // Allow caller to re-encrypt data
    await onRotate(oldKey, newKey);

    // Save new key
    await _storage.write(
      key: _encryptionKeyKey,
      value: base64Encode(newKey),
    );
  }
}
```

## Platform-Specific Options

```dart
class PlatformSecureStorage {
  static FlutterSecureStorage create() {
    return const FlutterSecureStorage(
      aOptions: AndroidOptions(
        encryptedSharedPreferences: true,
        keyCipherAlgorithm: KeyCipherAlgorithm.RSA_ECB_OAEPwithSHA_256andMGF1Padding,
        storageCipherAlgorithm: StorageCipherAlgorithm.AES_GCM_NoPadding,
      ),
      iOptions: IOSOptions(
        accessibility: KeychainAccessibility.first_unlock_this_device,
        accountName: 'MyApp',
      ),
      webOptions: WebOptions(
        dbName: 'MyAppSecureStorage',
        publicKey: 'MyAppPublicKey',
      ),
      mOptions: MacOsOptions(
        accessibility: KeychainAccessibility.first_unlock_this_device,
        accountName: 'MyApp',
      ),
    );
  }
}

// iOS Accessibility Options:
// - passcode: Available after first unlock, even after restart
// - unlocked: Only available when device is unlocked
// - unlocked_this_device: Only on this device when unlocked
// - first_unlock: After first unlock, persists across restarts
// - first_unlock_this_device: After first unlock, only this device
```

## Riverpod Integration

```dart
@riverpod
FlutterSecureStorage secureStorage(SecureStorageRef ref) {
  return PlatformSecureStorage.create();
}

@riverpod
TokenStorage tokenStorage(TokenStorageRef ref) {
  return SecureTokenStorage(storage: ref.watch(secureStorageProvider));
}

@riverpod
class AuthState extends _$AuthState {
  @override
  Future<bool> build() async {
    final tokenStorage = ref.watch(tokenStorageProvider);
    return tokenStorage.hasTokens();
  }

  Future<void> logout() async {
    final tokenStorage = ref.read(tokenStorageProvider);
    await tokenStorage.clear();
    ref.invalidateSelf();
  }
}
```

## Testing

```dart
class MockSecureStorage implements FlutterSecureStorage {
  final Map<String, String> _storage = {};

  @override
  Future<void> write({required String key, required String? value, ...}) async {
    if (value != null) {
      _storage[key] = value;
    } else {
      _storage.remove(key);
    }
  }

  @override
  Future<String?> read({required String key, ...}) async {
    return _storage[key];
  }

  @override
  Future<void> delete({required String key, ...}) async {
    _storage.remove(key);
  }

  @override
  Future<void> deleteAll({...}) async {
    _storage.clear();
  }

  @override
  Future<bool> containsKey({required String key, ...}) async {
    return _storage.containsKey(key);
  }

  @override
  Future<Map<String, String>> readAll({...}) async {
    return Map.from(_storage);
  }
}

void main() {
  test('saves and retrieves token', () async {
    final storage = SecureTokenStorage(storage: MockSecureStorage());

    await storage.saveTokens(
      accessToken: 'test_access',
      refreshToken: 'test_refresh',
    );

    expect(await storage.getAccessToken(), 'test_access');
    expect(await storage.getRefreshToken(), 'test_refresh');
  });
}
```

## Best Practices

1. **Use for sensitive data only** - Tokens, credentials, encryption keys
2. **Clear on logout** - Remove all sensitive data when user logs out
3. **Handle platform differences** - Configure platform-specific options
4. **Use appropriate accessibility** - iOS Keychain accessibility level
5. **Enable encrypted preferences** - Android EncryptedSharedPreferences
6. **Test with mocks** - Create mock implementation for testing
