---
name: flutter-shared-preferences
description: SharedPreferences for simple key-value storage
applies_to: flutter
---

# Flutter SharedPreferences

## Overview

SharedPreferences provides simple persistent key-value storage. Best for small amounts of primitive data like user settings, flags, and tokens.

## Dependencies

```yaml
dependencies:
  shared_preferences: ^2.2.2
```

## Basic Usage

```dart
import 'package:shared_preferences/shared_preferences.dart';

// Save data
Future<void> saveData() async {
  final prefs = await SharedPreferences.getInstance();

  // String
  await prefs.setString('username', 'john_doe');

  // Int
  await prefs.setInt('age', 25);

  // Double
  await prefs.setDouble('rating', 4.5);

  // Bool
  await prefs.setBool('isLoggedIn', true);

  // String list
  await prefs.setStringList('tags', ['flutter', 'dart', 'mobile']);
}

// Read data
Future<void> readData() async {
  final prefs = await SharedPreferences.getInstance();

  final username = prefs.getString('username'); // nullable
  final age = prefs.getInt('age') ?? 0; // with default
  final rating = prefs.getDouble('rating') ?? 0.0;
  final isLoggedIn = prefs.getBool('isLoggedIn') ?? false;
  final tags = prefs.getStringList('tags') ?? [];
}

// Remove data
Future<void> removeData() async {
  final prefs = await SharedPreferences.getInstance();
  await prefs.remove('username');
}

// Clear all data
Future<void> clearAll() async {
  final prefs = await SharedPreferences.getInstance();
  await prefs.clear();
}
```

## Storage Service Wrapper

```dart
abstract class LocalStorage {
  Future<String?> getString(String key);
  Future<void> setString(String key, String value);
  Future<int?> getInt(String key);
  Future<void> setInt(String key, int value);
  Future<bool?> getBool(String key);
  Future<void> setBool(String key, bool value);
  Future<void> remove(String key);
  Future<void> clear();
}

class SharedPreferencesStorage implements LocalStorage {
  SharedPreferences? _prefs;

  Future<SharedPreferences> get _instance async {
    _prefs ??= await SharedPreferences.getInstance();
    return _prefs!;
  }

  @override
  Future<String?> getString(String key) async {
    final prefs = await _instance;
    return prefs.getString(key);
  }

  @override
  Future<void> setString(String key, String value) async {
    final prefs = await _instance;
    await prefs.setString(key, value);
  }

  @override
  Future<int?> getInt(String key) async {
    final prefs = await _instance;
    return prefs.getInt(key);
  }

  @override
  Future<void> setInt(String key, int value) async {
    final prefs = await _instance;
    await prefs.setInt(key, value);
  }

  @override
  Future<bool?> getBool(String key) async {
    final prefs = await _instance;
    return prefs.getBool(key);
  }

  @override
  Future<void> setBool(String key, bool value) async {
    final prefs = await _instance;
    await prefs.setBool(key, value);
  }

  @override
  Future<void> remove(String key) async {
    final prefs = await _instance;
    await prefs.remove(key);
  }

  @override
  Future<void> clear() async {
    final prefs = await _instance;
    await prefs.clear();
  }
}
```

## Type-Safe Storage Keys

```dart
enum StorageKey {
  accessToken('access_token'),
  refreshToken('refresh_token'),
  userId('user_id'),
  username('username'),
  isOnboarded('is_onboarded'),
  themeMode('theme_mode'),
  locale('locale'),
  notificationsEnabled('notifications_enabled');

  const StorageKey(this.key);
  final String key;
}

class TypedStorage {
  final SharedPreferencesStorage _storage;

  TypedStorage(this._storage);

  // Token management
  Future<String?> getAccessToken() => _storage.getString(StorageKey.accessToken.key);
  Future<void> setAccessToken(String token) =>
      _storage.setString(StorageKey.accessToken.key, token);

  Future<String?> getRefreshToken() => _storage.getString(StorageKey.refreshToken.key);
  Future<void> setRefreshToken(String token) =>
      _storage.setString(StorageKey.refreshToken.key, token);

  // User preferences
  Future<bool> isOnboarded() async =>
      await _storage.getBool(StorageKey.isOnboarded.key) ?? false;
  Future<void> setOnboarded(bool value) =>
      _storage.setBool(StorageKey.isOnboarded.key, value);

  Future<String> getThemeMode() async =>
      await _storage.getString(StorageKey.themeMode.key) ?? 'system';
  Future<void> setThemeMode(String mode) =>
      _storage.setString(StorageKey.themeMode.key, mode);

  Future<bool> areNotificationsEnabled() async =>
      await _storage.getBool(StorageKey.notificationsEnabled.key) ?? true;
  Future<void> setNotificationsEnabled(bool enabled) =>
      _storage.setBool(StorageKey.notificationsEnabled.key, enabled);

  // Clear auth data
  Future<void> clearAuth() async {
    await _storage.remove(StorageKey.accessToken.key);
    await _storage.remove(StorageKey.refreshToken.key);
    await _storage.remove(StorageKey.userId.key);
  }
}
```

## JSON Object Storage

```dart
import 'dart:convert';

class UserPreferencesStorage {
  final SharedPreferencesStorage _storage;
  static const _key = 'user_preferences';

  UserPreferencesStorage(this._storage);

  Future<UserPreferences?> get() async {
    final json = await _storage.getString(_key);
    if (json == null) return null;

    try {
      final map = jsonDecode(json) as Map<String, dynamic>;
      return UserPreferences.fromJson(map);
    } catch (e) {
      return null;
    }
  }

  Future<void> save(UserPreferences preferences) async {
    final json = jsonEncode(preferences.toJson());
    await _storage.setString(_key, json);
  }

  Future<void> clear() => _storage.remove(_key);
}

@JsonSerializable()
class UserPreferences {
  final String theme;
  final String locale;
  final bool notificationsEnabled;
  final bool soundEnabled;
  final int fontSize;

  UserPreferences({
    this.theme = 'system',
    this.locale = 'en',
    this.notificationsEnabled = true,
    this.soundEnabled = true,
    this.fontSize = 14,
  });

  factory UserPreferences.fromJson(Map<String, dynamic> json) =>
      _$UserPreferencesFromJson(json);
  Map<String, dynamic> toJson() => _$UserPreferencesToJson(this);
}
```

## Settings Management

```dart
class SettingsService {
  final TypedStorage _storage;
  final _settingsController = BehaviorSubject<AppSettings>.seeded(AppSettings());

  SettingsService(this._storage) {
    _loadSettings();
  }

  Stream<AppSettings> get settingsStream => _settingsController.stream;
  AppSettings get currentSettings => _settingsController.value;

  Future<void> _loadSettings() async {
    final settings = AppSettings(
      themeMode: await _storage.getThemeMode(),
      notificationsEnabled: await _storage.areNotificationsEnabled(),
      isOnboarded: await _storage.isOnboarded(),
    );
    _settingsController.add(settings);
  }

  Future<void> setThemeMode(String mode) async {
    await _storage.setThemeMode(mode);
    _settingsController.add(currentSettings.copyWith(themeMode: mode));
  }

  Future<void> setNotificationsEnabled(bool enabled) async {
    await _storage.setNotificationsEnabled(enabled);
    _settingsController.add(currentSettings.copyWith(notificationsEnabled: enabled));
  }

  Future<void> setOnboarded(bool value) async {
    await _storage.setOnboarded(value);
    _settingsController.add(currentSettings.copyWith(isOnboarded: value));
  }

  void dispose() {
    _settingsController.close();
  }
}

class AppSettings {
  final String themeMode;
  final bool notificationsEnabled;
  final bool isOnboarded;

  AppSettings({
    this.themeMode = 'system',
    this.notificationsEnabled = true,
    this.isOnboarded = false,
  });

  AppSettings copyWith({
    String? themeMode,
    bool? notificationsEnabled,
    bool? isOnboarded,
  }) {
    return AppSettings(
      themeMode: themeMode ?? this.themeMode,
      notificationsEnabled: notificationsEnabled ?? this.notificationsEnabled,
      isOnboarded: isOnboarded ?? this.isOnboarded,
    );
  }
}
```

## Riverpod Integration

```dart
@riverpod
SharedPreferencesStorage localStorage(LocalStorageRef ref) {
  return SharedPreferencesStorage();
}

@riverpod
TypedStorage typedStorage(TypedStorageRef ref) {
  return TypedStorage(ref.watch(localStorageProvider));
}

@riverpod
class ThemeMode extends _$ThemeMode {
  @override
  Future<String> build() async {
    final storage = ref.watch(typedStorageProvider);
    return storage.getThemeMode();
  }

  Future<void> setThemeMode(String mode) async {
    final storage = ref.read(typedStorageProvider);
    await storage.setThemeMode(mode);
    state = AsyncData(mode);
  }
}

// Usage in widget
class ThemeSelector extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final themeModeAsync = ref.watch(themeModeProvider);

    return themeModeAsync.when(
      data: (mode) => SegmentedButton<String>(
        selected: {mode},
        onSelectionChanged: (selected) {
          ref.read(themeModeProvider.notifier).setThemeMode(selected.first);
        },
        segments: const [
          ButtonSegment(value: 'light', label: Text('Light')),
          ButtonSegment(value: 'dark', label: Text('Dark')),
          ButtonSegment(value: 'system', label: Text('System')),
        ],
      ),
      loading: () => const CircularProgressIndicator(),
      error: (_, __) => const Text('Error loading theme'),
    );
  }
}
```

## Caching with Expiration

```dart
class CacheStorage {
  final SharedPreferencesStorage _storage;

  CacheStorage(this._storage);

  Future<void> setWithExpiry(
    String key,
    String value, {
    required Duration expiry,
  }) async {
    final expiryTime = DateTime.now().add(expiry).millisecondsSinceEpoch;
    await _storage.setString('${key}_value', value);
    await _storage.setInt('${key}_expiry', expiryTime);
  }

  Future<String?> getIfNotExpired(String key) async {
    final expiryTime = await _storage.getInt('${key}_expiry');
    if (expiryTime == null) return null;

    if (DateTime.now().millisecondsSinceEpoch > expiryTime) {
      // Expired, remove and return null
      await _storage.remove('${key}_value');
      await _storage.remove('${key}_expiry');
      return null;
    }

    return _storage.getString('${key}_value');
  }
}
```

## Testing

```dart
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  group('TypedStorage', () {
    late SharedPreferencesStorage storage;
    late TypedStorage typedStorage;

    setUp(() {
      SharedPreferences.setMockInitialValues({});
      storage = SharedPreferencesStorage();
      typedStorage = TypedStorage(storage);
    });

    test('saves and retrieves access token', () async {
      await typedStorage.setAccessToken('test_token');
      final token = await typedStorage.getAccessToken();
      expect(token, 'test_token');
    });

    test('returns default theme mode', () async {
      final mode = await typedStorage.getThemeMode();
      expect(mode, 'system');
    });

    test('clears auth data', () async {
      await typedStorage.setAccessToken('token');
      await typedStorage.setRefreshToken('refresh');

      await typedStorage.clearAuth();

      expect(await typedStorage.getAccessToken(), isNull);
      expect(await typedStorage.getRefreshToken(), isNull);
    });
  });
}
```

## Best Practices

1. **Use for simple data** - Not for complex objects or large datasets
2. **Wrap with service** - Don't use SharedPreferences directly in UI
3. **Type-safe keys** - Use enums for storage keys
4. **Handle null** - Always provide defaults for nullable reads
5. **Async initialization** - Initialize in app startup if needed frequently
6. **Clear on logout** - Remove sensitive data when user logs out
