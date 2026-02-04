---
name: flutter-drift
description: Drift SQL database for Flutter
applies_to: flutter
---

# Flutter Drift

## Overview

Drift (formerly Moor) is a type-safe reactive persistence library for Flutter. It generates Dart code from SQL schema definitions and provides compile-time verification.

## Dependencies

```yaml
dependencies:
  drift: ^2.14.1
  sqlite3_flutter_libs: ^0.5.18
  path_provider: ^2.1.2
  path: ^1.8.3

dev_dependencies:
  drift_dev: ^2.14.1
  build_runner: ^2.4.6
```

## Database Setup

```dart
import 'dart:io';
import 'package:drift/drift.dart';
import 'package:drift/native.dart';
import 'package:path_provider/path_provider.dart';
import 'package:path/path.dart' as p;

part 'database.g.dart';

// Define tables
class Products extends Table {
  IntColumn get id => integer().autoIncrement()();
  TextColumn get name => text().withLength(min: 1, max: 100)();
  TextColumn get description => text().nullable()();
  RealColumn get price => real()();
  TextColumn get imageUrl => text().nullable()();
  IntColumn get categoryId => integer().references(Categories, #id)();
  DateTimeColumn get createdAt => dateTime().withDefault(currentDateAndTime)();
  DateTimeColumn get updatedAt => dateTime().withDefault(currentDateAndTime)();
}

class Categories extends Table {
  IntColumn get id => integer().autoIncrement()();
  TextColumn get name => text().withLength(min: 1, max: 50)();
  TextColumn get slug => text().unique()();
}

class CartItems extends Table {
  IntColumn get id => integer().autoIncrement()();
  IntColumn get productId => integer().references(Products, #id)();
  IntColumn get quantity => integer().withDefault(const Constant(1))();
  DateTimeColumn get addedAt => dateTime().withDefault(currentDateAndTime)();
}

// Database class
@DriftDatabase(tables: [Products, Categories, CartItems])
class AppDatabase extends _$AppDatabase {
  AppDatabase() : super(_openConnection());

  @override
  int get schemaVersion => 1;

  @override
  MigrationStrategy get migration {
    return MigrationStrategy(
      onCreate: (Migrator m) async {
        await m.createAll();
      },
      onUpgrade: (Migrator m, int from, int to) async {
        // Handle migrations
      },
    );
  }
}

LazyDatabase _openConnection() {
  return LazyDatabase(() async {
    final dbFolder = await getApplicationDocumentsDirectory();
    final file = File(p.join(dbFolder.path, 'app.sqlite'));
    return NativeDatabase.createInBackground(file);
  });
}
```

## Data Access Objects (DAOs)

```dart
part 'product_dao.g.dart';

@DriftAccessor(tables: [Products, Categories])
class ProductDao extends DatabaseAccessor<AppDatabase> with _$ProductDaoMixin {
  ProductDao(AppDatabase db) : super(db);

  // Get all products
  Future<List<Product>> getAllProducts() => select(products).get();

  // Get product by ID
  Future<Product?> getProductById(int id) {
    return (select(products)..where((p) => p.id.equals(id))).getSingleOrNull();
  }

  // Get products by category
  Future<List<Product>> getProductsByCategory(int categoryId) {
    return (select(products)..where((p) => p.categoryId.equals(categoryId))).get();
  }

  // Search products
  Future<List<Product>> searchProducts(String query) {
    return (select(products)
          ..where((p) => p.name.like('%$query%') | p.description.like('%$query%')))
        .get();
  }

  // Get products with pagination
  Future<List<Product>> getProductsPaginated(int limit, int offset) {
    return (select(products)
          ..orderBy([(p) => OrderingTerm.desc(p.createdAt)])
          ..limit(limit, offset: offset))
        .get();
  }

  // Insert product
  Future<int> insertProduct(ProductsCompanion product) {
    return into(products).insert(product);
  }

  // Update product
  Future<bool> updateProduct(Product product) {
    return update(products).replace(product);
  }

  // Delete product
  Future<int> deleteProduct(int id) {
    return (delete(products)..where((p) => p.id.equals(id))).go();
  }

  // Watch all products (reactive)
  Stream<List<Product>> watchAllProducts() => select(products).watch();

  // Watch products by category
  Stream<List<Product>> watchProductsByCategory(int categoryId) {
    return (select(products)..where((p) => p.categoryId.equals(categoryId))).watch();
  }
}
```

## Complex Queries with Joins

```dart
@DriftAccessor(tables: [Products, Categories, CartItems])
class CartDao extends DatabaseAccessor<AppDatabase> with _$CartDaoMixin {
  CartDao(AppDatabase db) : super(db);

  // Get cart items with product details
  Future<List<CartItemWithProduct>> getCartItemsWithProducts() async {
    final query = select(cartItems).join([
      innerJoin(products, products.id.equalsExp(cartItems.productId)),
    ]);

    return query.map((row) {
      return CartItemWithProduct(
        cartItem: row.readTable(cartItems),
        product: row.readTable(products),
      );
    }).get();
  }

  // Watch cart items with product details
  Stream<List<CartItemWithProduct>> watchCartItemsWithProducts() {
    final query = select(cartItems).join([
      innerJoin(products, products.id.equalsExp(cartItems.productId)),
    ]);

    return query.map((row) {
      return CartItemWithProduct(
        cartItem: row.readTable(cartItems),
        product: row.readTable(products),
      );
    }).watch();
  }

  // Get cart total
  Future<double> getCartTotal() async {
    final query = selectOnly(cartItems).join([
      innerJoin(products, products.id.equalsExp(cartItems.productId)),
    ])
      ..addColumns([
        cartItems.quantity * products.price,
      ]);

    final result = await query
        .map((row) => row.read(cartItems.quantity * products.price))
        .get();

    return result.fold<double>(0, (sum, price) => sum + (price ?? 0));
  }

  // Add to cart
  Future<void> addToCart(int productId, {int quantity = 1}) async {
    final existing = await (select(cartItems)
          ..where((c) => c.productId.equals(productId)))
        .getSingleOrNull();

    if (existing != null) {
      await (update(cartItems)..where((c) => c.id.equals(existing.id))).write(
        CartItemsCompanion(quantity: Value(existing.quantity + quantity)),
      );
    } else {
      await into(cartItems).insert(
        CartItemsCompanion.insert(productId: productId, quantity: Value(quantity)),
      );
    }
  }

  // Update quantity
  Future<void> updateQuantity(int cartItemId, int quantity) async {
    if (quantity <= 0) {
      await (delete(cartItems)..where((c) => c.id.equals(cartItemId))).go();
    } else {
      await (update(cartItems)..where((c) => c.id.equals(cartItemId))).write(
        CartItemsCompanion(quantity: Value(quantity)),
      );
    }
  }

  // Remove from cart
  Future<void> removeFromCart(int cartItemId) {
    return (delete(cartItems)..where((c) => c.id.equals(cartItemId))).go();
  }

  // Clear cart
  Future<void> clearCart() => delete(cartItems).go();

  // Get cart item count
  Stream<int> watchCartItemCount() {
    final countExp = cartItems.id.count();
    final query = selectOnly(cartItems)..addColumns([countExp]);
    return query.map((row) => row.read(countExp) ?? 0).watchSingle();
  }
}

class CartItemWithProduct {
  final CartItem cartItem;
  final Product product;

  CartItemWithProduct({required this.cartItem, required this.product});

  double get totalPrice => product.price * cartItem.quantity;
}
```

## Transactions

```dart
class OrderDao extends DatabaseAccessor<AppDatabase> with _$OrderDaoMixin {
  OrderDao(AppDatabase db) : super(db);

  Future<int> createOrder(List<CartItemWithProduct> items) async {
    return transaction(() async {
      // Create order
      final orderId = await into(orders).insert(
        OrdersCompanion.insert(
          status: 'pending',
          total: items.fold(0, (sum, item) => sum + item.totalPrice),
        ),
      );

      // Create order items
      for (final item in items) {
        await into(orderItems).insert(
          OrderItemsCompanion.insert(
            orderId: orderId,
            productId: item.product.id,
            quantity: item.cartItem.quantity,
            price: item.product.price,
          ),
        );
      }

      // Clear cart
      await delete(cartItems).go();

      return orderId;
    });
  }
}
```

## Migrations

```dart
@DriftDatabase(tables: [Products, Categories, CartItems, Orders, OrderItems])
class AppDatabase extends _$AppDatabase {
  AppDatabase() : super(_openConnection());

  @override
  int get schemaVersion => 3;

  @override
  MigrationStrategy get migration {
    return MigrationStrategy(
      onCreate: (Migrator m) async {
        await m.createAll();
      },
      onUpgrade: (Migrator m, int from, int to) async {
        if (from < 2) {
          // Add new column
          await m.addColumn(products, products.imageUrl);
        }
        if (from < 3) {
          // Create new table
          await m.createTable(orders);
          await m.createTable(orderItems);
        }
      },
      beforeOpen: (details) async {
        // Enable foreign keys
        await customStatement('PRAGMA foreign_keys = ON');
      },
    );
  }
}
```

## Custom Types and Converters

```dart
// Enum converter
class OrderStatusConverter extends TypeConverter<OrderStatus, String> {
  const OrderStatusConverter();

  @override
  OrderStatus fromSql(String fromDb) {
    return OrderStatus.values.firstWhere(
      (e) => e.name == fromDb,
      orElse: () => OrderStatus.pending,
    );
  }

  @override
  String toSql(OrderStatus value) => value.name;
}

enum OrderStatus { pending, processing, shipped, delivered, cancelled }

class Orders extends Table {
  IntColumn get id => integer().autoIncrement()();
  TextColumn get status => text().map(const OrderStatusConverter())();
  RealColumn get total => real()();
  DateTimeColumn get createdAt => dateTime().withDefault(currentDateAndTime)();
}

// JSON converter for complex objects
class AddressConverter extends TypeConverter<Address, String> {
  const AddressConverter();

  @override
  Address fromSql(String fromDb) {
    return Address.fromJson(jsonDecode(fromDb));
  }

  @override
  String toSql(Address value) => jsonEncode(value.toJson());
}
```

## Riverpod Integration

```dart
@riverpod
AppDatabase database(DatabaseRef ref) {
  final db = AppDatabase();
  ref.onDispose(db.close);
  return db;
}

@riverpod
ProductDao productDao(ProductDaoRef ref) {
  return ProductDao(ref.watch(databaseProvider));
}

@riverpod
Stream<List<Product>> allProducts(AllProductsRef ref) {
  return ref.watch(productDaoProvider).watchAllProducts();
}

@riverpod
Stream<List<CartItemWithProduct>> cartItems(CartItemsRef ref) {
  return ref.watch(cartDaoProvider).watchCartItemsWithProducts();
}

// Usage in widget
class ProductsPage extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final productsAsync = ref.watch(allProductsProvider);

    return productsAsync.when(
      data: (products) => ListView.builder(
        itemCount: products.length,
        itemBuilder: (_, index) => ProductTile(product: products[index]),
      ),
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (error, _) => Center(child: Text('Error: $error')),
    );
  }
}
```

## Testing

```dart
void main() {
  late AppDatabase database;
  late ProductDao productDao;

  setUp(() {
    database = AppDatabase.forTesting(NativeDatabase.memory());
    productDao = ProductDao(database);
  });

  tearDown(() async {
    await database.close();
  });

  test('inserts and retrieves product', () async {
    final id = await productDao.insertProduct(
      ProductsCompanion.insert(
        name: 'Test Product',
        price: 9.99,
        categoryId: 1,
      ),
    );

    final product = await productDao.getProductById(id);
    expect(product?.name, 'Test Product');
  });

  test('watches products reactively', () async {
    final stream = productDao.watchAllProducts();

    await productDao.insertProduct(
      ProductsCompanion.insert(name: 'Product 1', price: 9.99, categoryId: 1),
    );

    await expectLater(
      stream,
      emits(hasLength(1)),
    );
  });
}
```

## Best Practices

1. **Use DAOs** - Separate data access logic from database definition
2. **Use streams** - Leverage reactive queries for real-time updates
3. **Use transactions** - For operations that must be atomic
4. **Plan migrations** - Always increment schemaVersion with changes
5. **Use type converters** - For enums and complex types
6. **Close database** - Call `close()` when app terminates
