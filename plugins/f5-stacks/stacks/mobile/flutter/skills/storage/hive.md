---
name: flutter-hive
description: Hive NoSQL database for Flutter
applies_to: flutter
---

# Flutter Hive

## Overview

Hive is a lightweight, fast key-value NoSQL database. It's pure Dart and doesn't require native dependencies, making it great for offline-first apps.

## Dependencies

```yaml
dependencies:
  hive: ^2.2.3
  hive_flutter: ^1.1.0

dev_dependencies:
  hive_generator: ^2.0.1
  build_runner: ^2.4.6
```

## Initialization

```dart
import 'package:hive_flutter/hive_flutter.dart';

Future<void> initHive() async {
  await Hive.initFlutter();

  // Register adapters
  Hive.registerAdapter(UserAdapter());
  Hive.registerAdapter(ProductAdapter());
  Hive.registerAdapter(CartItemAdapter());

  // Open boxes
  await Hive.openBox<User>('users');
  await Hive.openBox<Product>('products');
  await Hive.openBox<CartItem>('cart');
  await Hive.openBox('settings');
}

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await initHive();
  runApp(const MyApp());
}
```

## Model with TypeAdapter

```dart
import 'package:hive/hive.dart';

part 'user.g.dart';

@HiveType(typeId: 0)
class User extends HiveObject {
  @HiveField(0)
  final String id;

  @HiveField(1)
  final String email;

  @HiveField(2)
  final String name;

  @HiveField(3)
  final String? avatarUrl;

  @HiveField(4)
  final DateTime createdAt;

  User({
    required this.id,
    required this.email,
    required this.name,
    this.avatarUrl,
    required this.createdAt,
  });

  User copyWith({
    String? id,
    String? email,
    String? name,
    String? avatarUrl,
    DateTime? createdAt,
  }) {
    return User(
      id: id ?? this.id,
      email: email ?? this.email,
      name: name ?? this.name,
      avatarUrl: avatarUrl ?? this.avatarUrl,
      createdAt: createdAt ?? this.createdAt,
    );
  }
}

@HiveType(typeId: 1)
class Product extends HiveObject {
  @HiveField(0)
  final String id;

  @HiveField(1)
  final String name;

  @HiveField(2)
  final String description;

  @HiveField(3)
  final double price;

  @HiveField(4)
  final String? imageUrl;

  @HiveField(5)
  final String categoryId;

  @HiveField(6)
  final DateTime updatedAt;

  Product({
    required this.id,
    required this.name,
    required this.description,
    required this.price,
    this.imageUrl,
    required this.categoryId,
    required this.updatedAt,
  });
}
```

## Basic CRUD Operations

```dart
class ProductLocalDataSource {
  static const _boxName = 'products';

  Box<Product> get _box => Hive.box<Product>(_boxName);

  // Create
  Future<void> saveProduct(Product product) async {
    await _box.put(product.id, product);
  }

  // Read one
  Product? getProduct(String id) {
    return _box.get(id);
  }

  // Read all
  List<Product> getAllProducts() {
    return _box.values.toList();
  }

  // Update
  Future<void> updateProduct(Product product) async {
    await _box.put(product.id, product);
  }

  // Delete
  Future<void> deleteProduct(String id) async {
    await _box.delete(id);
  }

  // Delete all
  Future<void> clearAll() async {
    await _box.clear();
  }

  // Check if exists
  bool hasProduct(String id) {
    return _box.containsKey(id);
  }

  // Get count
  int get count => _box.length;
}
```

## Querying and Filtering

```dart
class ProductLocalDataSource {
  Box<Product> get _box => Hive.box<Product>('products');

  // Filter by category
  List<Product> getByCategory(String categoryId) {
    return _box.values.where((p) => p.categoryId == categoryId).toList();
  }

  // Search by name
  List<Product> searchByName(String query) {
    final lowerQuery = query.toLowerCase();
    return _box.values
        .where((p) => p.name.toLowerCase().contains(lowerQuery))
        .toList();
  }

  // Get products in price range
  List<Product> getByPriceRange(double min, double max) {
    return _box.values
        .where((p) => p.price >= min && p.price <= max)
        .toList();
  }

  // Get sorted by price
  List<Product> getSortedByPrice({bool ascending = true}) {
    final products = _box.values.toList();
    products.sort((a, b) =>
        ascending ? a.price.compareTo(b.price) : b.price.compareTo(a.price));
    return products;
  }

  // Get recently updated
  List<Product> getRecentlyUpdated(int limit) {
    final products = _box.values.toList();
    products.sort((a, b) => b.updatedAt.compareTo(a.updatedAt));
    return products.take(limit).toList();
  }
}
```

## Reactive Updates with ValueListenable

```dart
class ProductsPage extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<Box<Product>>(
      valueListenable: Hive.box<Product>('products').listenable(),
      builder: (context, box, _) {
        final products = box.values.toList();

        if (products.isEmpty) {
          return const Center(child: Text('No products'));
        }

        return ListView.builder(
          itemCount: products.length,
          itemBuilder: (context, index) {
            final product = products[index];
            return ProductListTile(
              product: product,
              onDelete: () => box.delete(product.id),
            );
          },
        );
      },
    );
  }
}

// Listen to specific keys
ValueListenableBuilder<Box<Product>>(
  valueListenable: Hive.box<Product>('products').listenable(keys: ['featured']),
  builder: (context, box, _) {
    final featured = box.get('featured');
    return FeaturedProductCard(product: featured);
  },
)
```

## Lazy Box for Large Data

```dart
class LargeDataSource {
  LazyBox<LargeObject>? _lazyBox;

  Future<void> init() async {
    _lazyBox = await Hive.openLazyBox<LargeObject>('large_objects');
  }

  Future<LargeObject?> get(String key) async {
    return _lazyBox?.get(key);
  }

  Future<void> put(String key, LargeObject value) async {
    await _lazyBox?.put(key, value);
  }

  Future<void> delete(String key) async {
    await _lazyBox?.delete(key);
  }
}
```

## Encrypted Box

```dart
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class SecureHiveStorage {
  static const _encryptionKeyKey = 'hive_encryption_key';
  final FlutterSecureStorage _secureStorage = const FlutterSecureStorage();

  Future<Box<T>> openEncryptedBox<T>(String name) async {
    final encryptionKey = await _getOrCreateEncryptionKey();
    return Hive.openBox<T>(
      name,
      encryptionCipher: HiveAesCipher(encryptionKey),
    );
  }

  Future<Uint8List> _getOrCreateEncryptionKey() async {
    final existingKey = await _secureStorage.read(key: _encryptionKeyKey);

    if (existingKey != null) {
      return base64Url.decode(existingKey);
    }

    final newKey = Hive.generateSecureKey();
    await _secureStorage.write(
      key: _encryptionKeyKey,
      value: base64UrlEncode(newKey),
    );
    return newKey;
  }
}

// Usage
final secureStorage = SecureHiveStorage();
final sensitiveBox = await secureStorage.openEncryptedBox<SensitiveData>('sensitive');
```

## Cache with Expiration

```dart
@HiveType(typeId: 10)
class CacheEntry<T> extends HiveObject {
  @HiveField(0)
  final T data;

  @HiveField(1)
  final DateTime expiresAt;

  CacheEntry({
    required this.data,
    required this.expiresAt,
  });

  bool get isExpired => DateTime.now().isAfter(expiresAt);
}

class HiveCache {
  final Box _box;

  HiveCache(this._box);

  Future<void> put<T>(
    String key,
    T data, {
    Duration expiry = const Duration(hours: 1),
  }) async {
    final entry = CacheEntry(
      data: data,
      expiresAt: DateTime.now().add(expiry),
    );
    await _box.put(key, entry);
  }

  T? get<T>(String key) {
    final entry = _box.get(key) as CacheEntry<T>?;
    if (entry == null || entry.isExpired) {
      _box.delete(key);
      return null;
    }
    return entry.data;
  }

  Future<void> invalidate(String key) => _box.delete(key);

  Future<void> clearExpired() async {
    final expiredKeys = _box.keys.where((key) {
      final entry = _box.get(key) as CacheEntry?;
      return entry?.isExpired ?? true;
    }).toList();

    for (final key in expiredKeys) {
      await _box.delete(key);
    }
  }
}
```

## Repository Pattern

```dart
class ProductRepository {
  final ProductApiService _apiService;
  final ProductLocalDataSource _localDataSource;

  ProductRepository(this._apiService, this._localDataSource);

  Future<List<Product>> getProducts({bool forceRefresh = false}) async {
    // Return cached if available and not forcing refresh
    if (!forceRefresh) {
      final cached = _localDataSource.getAllProducts();
      if (cached.isNotEmpty) {
        return cached;
      }
    }

    // Fetch from API
    try {
      final products = await _apiService.getProducts();
      // Cache locally
      for (final product in products) {
        await _localDataSource.saveProduct(product);
      }
      return products;
    } catch (e) {
      // Return cached on error
      final cached = _localDataSource.getAllProducts();
      if (cached.isNotEmpty) {
        return cached;
      }
      rethrow;
    }
  }

  Future<Product?> getProduct(String id) async {
    // Check local first
    final local = _localDataSource.getProduct(id);
    if (local != null) {
      return local;
    }

    // Fetch from API
    try {
      final product = await _apiService.getProduct(id);
      await _localDataSource.saveProduct(product);
      return product;
    } catch (e) {
      return null;
    }
  }
}
```

## Migration

```dart
class HiveMigrationService {
  static const _versionKey = 'hive_version';
  static const _currentVersion = 2;

  final Box _settingsBox;

  HiveMigrationService(this._settingsBox);

  Future<void> migrate() async {
    final currentVersion = _settingsBox.get(_versionKey, defaultValue: 0) as int;

    if (currentVersion < _currentVersion) {
      if (currentVersion < 1) {
        await _migrateV0ToV1();
      }
      if (currentVersion < 2) {
        await _migrateV1ToV2();
      }

      await _settingsBox.put(_versionKey, _currentVersion);
    }
  }

  Future<void> _migrateV0ToV1() async {
    // Migration logic for v0 to v1
    final oldBox = await Hive.openBox('old_products');
    final newBox = Hive.box<Product>('products');

    for (final key in oldBox.keys) {
      final oldData = oldBox.get(key) as Map?;
      if (oldData != null) {
        final product = Product(
          id: oldData['id'],
          name: oldData['name'],
          description: oldData['description'] ?? '',
          price: (oldData['price'] as num).toDouble(),
          categoryId: oldData['category'] ?? 'uncategorized',
          updatedAt: DateTime.now(),
        );
        await newBox.put(product.id, product);
      }
    }

    await oldBox.deleteFromDisk();
  }

  Future<void> _migrateV1ToV2() async {
    // Migration logic for v1 to v2
  }
}
```

## Testing

```dart
void main() {
  late Box<Product> box;

  setUpAll(() async {
    await Hive.initFlutter();
    Hive.registerAdapter(ProductAdapter());
  });

  setUp(() async {
    box = await Hive.openBox<Product>('test_products');
  });

  tearDown(() async {
    await box.clear();
  });

  test('saves and retrieves product', () async {
    final product = Product(
      id: '1',
      name: 'Test Product',
      description: 'Description',
      price: 9.99,
      categoryId: 'cat1',
      updatedAt: DateTime.now(),
    );

    await box.put(product.id, product);

    final retrieved = box.get(product.id);
    expect(retrieved?.name, 'Test Product');
  });

  test('deletes product', () async {
    await box.put('1', Product(...));
    await box.delete('1');

    expect(box.get('1'), isNull);
  });
}
```

## Best Practices

1. **Register adapters early** - Before opening boxes
2. **Use typeId carefully** - Never change or reuse typeIds
3. **Close boxes on dispose** - `Hive.close()` on app exit
4. **Use lazy boxes for large data** - Prevents loading all data into memory
5. **Encrypt sensitive data** - Use encrypted boxes for PII
6. **Handle migrations** - Plan for schema changes
