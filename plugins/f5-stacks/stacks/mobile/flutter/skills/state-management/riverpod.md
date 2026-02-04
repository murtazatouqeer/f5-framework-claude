---
name: flutter-riverpod
description: Riverpod state management in Flutter
applies_to: flutter
---

# Flutter Riverpod

## Overview

Riverpod is a reactive caching and data-binding framework. It provides compile-time safety, testability, and flexibility for state management.

## Dependencies

```yaml
dependencies:
  flutter_riverpod: ^2.4.9
  riverpod_annotation: ^2.3.3

dev_dependencies:
  riverpod_generator: ^2.3.9
  build_runner: ^2.4.6
```

## Provider Types

### Provider (Read-only)

```dart
// Simple computed value
@riverpod
String greeting(GreetingRef ref) {
  return 'Hello, World!';
}

// Computed from other providers
@riverpod
double cartTotal(CartTotalRef ref) {
  final items = ref.watch(cartItemsProvider);
  return items.fold(0.0, (sum, item) => sum + item.price * item.quantity);
}

// Usage
class TotalDisplay extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final total = ref.watch(cartTotalProvider);
    return Text('Total: \$${total.toStringAsFixed(2)}');
  }
}
```

### StateProvider (Simple mutable state)

```dart
// Counter
@riverpod
class Counter extends _$Counter {
  @override
  int build() => 0;

  void increment() => state++;
  void decrement() => state--;
  void reset() => state = 0;
}

// Filter selection
@riverpod
class SelectedFilter extends _$SelectedFilter {
  @override
  ProductFilter build() => ProductFilter.all;

  void select(ProductFilter filter) => state = filter;
}
```

### FutureProvider (Async data)

```dart
@riverpod
Future<List<Product>> products(ProductsRef ref) async {
  final repository = ref.watch(productRepositoryProvider);
  return repository.getProducts();
}

// With parameters
@riverpod
Future<Product> product(ProductRef ref, String id) async {
  final repository = ref.watch(productRepositoryProvider);
  return repository.getProduct(id);
}

// Usage
class ProductsList extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final productsAsync = ref.watch(productsProvider);

    return productsAsync.when(
      data: (products) => ListView.builder(
        itemCount: products.length,
        itemBuilder: (_, index) => ProductTile(product: products[index]),
      ),
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (error, stack) => ErrorView(
        message: error.toString(),
        onRetry: () => ref.invalidate(productsProvider),
      ),
    );
  }
}
```

### StreamProvider (Real-time data)

```dart
@riverpod
Stream<List<Message>> messages(MessagesRef ref, String chatId) {
  final repository = ref.watch(chatRepositoryProvider);
  return repository.watchMessages(chatId);
}

// Auth state stream
@riverpod
Stream<User?> authStateChanges(AuthStateChangesRef ref) {
  final auth = ref.watch(firebaseAuthProvider);
  return auth.authStateChanges();
}
```

### NotifierProvider (Complex state)

```dart
@riverpod
class Cart extends _$Cart {
  @override
  CartState build() => const CartState();

  void addItem(Product product, {int quantity = 1}) {
    final existingIndex = state.items.indexWhere(
      (item) => item.productId == product.id,
    );

    if (existingIndex >= 0) {
      final items = [...state.items];
      items[existingIndex] = items[existingIndex].copyWith(
        quantity: items[existingIndex].quantity + quantity,
      );
      state = state.copyWith(items: items);
    } else {
      state = state.copyWith(
        items: [
          ...state.items,
          CartItem(
            productId: product.id,
            name: product.name,
            price: product.price,
            quantity: quantity,
          ),
        ],
      );
    }
  }

  void removeItem(String productId) {
    state = state.copyWith(
      items: state.items.where((item) => item.productId != productId).toList(),
    );
  }

  void updateQuantity(String productId, int quantity) {
    if (quantity <= 0) {
      removeItem(productId);
      return;
    }

    state = state.copyWith(
      items: state.items.map((item) {
        if (item.productId == productId) {
          return item.copyWith(quantity: quantity);
        }
        return item;
      }).toList(),
    );
  }

  void clear() => state = const CartState();
}
```

### AsyncNotifierProvider (Async operations)

```dart
@riverpod
class ProductList extends _$ProductList {
  @override
  Future<List<Product>> build() async {
    return _fetchProducts();
  }

  Future<List<Product>> _fetchProducts({int page = 1}) async {
    final repository = ref.read(productRepositoryProvider);
    return repository.getProducts(page: page);
  }

  Future<void> refresh() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() => _fetchProducts());
  }

  Future<void> loadMore() async {
    final currentProducts = state.valueOrNull ?? [];
    final nextPage = (currentProducts.length ~/ 20) + 1;

    state = await AsyncValue.guard(() async {
      final newProducts = await _fetchProducts(page: nextPage);
      return [...currentProducts, ...newProducts];
    });
  }

  Future<void> addProduct(CreateProductDto dto) async {
    final repository = ref.read(productRepositoryProvider);
    final newProduct = await repository.createProduct(dto);

    state = AsyncValue.data([
      newProduct,
      ...state.valueOrNull ?? [],
    ]);
  }
}
```

## App Setup

```dart
void main() {
  runApp(
    ProviderScope(
      overrides: [
        // Override for testing or environment-specific providers
        apiClientProvider.overrideWithValue(ApiClient(baseUrl: 'https://api.example.com')),
      ],
      child: const MyApp(),
    ),
  );
}

class MyApp extends ConsumerWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final themeMode = ref.watch(themeModeProvider);

    return MaterialApp(
      themeMode: themeMode,
      theme: AppTheme.light,
      darkTheme: AppTheme.dark,
      home: const HomePage(),
    );
  }
}
```

## Consumer Widgets

### ConsumerWidget

```dart
class ProductCard extends ConsumerWidget {
  const ProductCard({super.key, required this.product});

  final Product product;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isInCart = ref.watch(
      cartProvider.select(
        (cart) => cart.items.any((item) => item.productId == product.id),
      ),
    );

    return Card(
      child: ListTile(
        title: Text(product.name),
        subtitle: Text('\$${product.price}'),
        trailing: IconButton(
          icon: Icon(isInCart ? Icons.check : Icons.add_shopping_cart),
          onPressed: () {
            if (!isInCart) {
              ref.read(cartProvider.notifier).addItem(product);
            }
          },
        ),
      ),
    );
  }
}
```

### ConsumerStatefulWidget

```dart
class ProductDetailPage extends ConsumerStatefulWidget {
  const ProductDetailPage({super.key, required this.productId});

  final String productId;

  @override
  ConsumerState<ProductDetailPage> createState() => _ProductDetailPageState();
}

class _ProductDetailPageState extends ConsumerState<ProductDetailPage> {
  int _quantity = 1;

  @override
  Widget build(BuildContext context) {
    final productAsync = ref.watch(productProvider(widget.productId));

    return Scaffold(
      appBar: AppBar(title: const Text('Product Detail')),
      body: productAsync.when(
        data: (product) => Column(
          children: [
            Image.network(product.imageUrl),
            Text(product.name),
            Text('\$${product.price}'),
            QuantitySelector(
              quantity: _quantity,
              onChanged: (value) => setState(() => _quantity = value),
            ),
            ElevatedButton(
              onPressed: () {
                ref.read(cartProvider.notifier).addItem(
                  product,
                  quantity: _quantity,
                );
                Navigator.pop(context);
              },
              child: const Text('Add to Cart'),
            ),
          ],
        ),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => Center(child: Text('Error: $error')),
      ),
    );
  }
}
```

### Consumer Builder

```dart
class HomePage extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        actions: [
          Consumer(
            builder: (context, ref, child) {
              final itemCount = ref.watch(
                cartProvider.select((cart) => cart.items.length),
              );
              return Badge(
                label: Text('$itemCount'),
                child: IconButton(
                  icon: const Icon(Icons.shopping_cart),
                  onPressed: () => context.push('/cart'),
                ),
              );
            },
          ),
        ],
      ),
      body: const ProductsView(),
    );
  }
}
```

## Ref Methods

```dart
// Watch - rebuilds when provider changes
final products = ref.watch(productsProvider);

// Read - one-time read, doesn't rebuild
final cart = ref.read(cartProvider.notifier);

// Listen - side effects on changes
ref.listen(authProvider, (previous, next) {
  if (next == null) {
    context.go('/login');
  }
});

// Invalidate - force refresh
ref.invalidate(productsProvider);

// Refresh - invalidate and immediately rebuild
final freshData = await ref.refresh(productsProvider.future);
```

## Provider Modifiers

### Family (Parameterized providers)

```dart
@riverpod
Future<Product> product(ProductRef ref, String id) async {
  final repository = ref.watch(productRepositoryProvider);
  return repository.getProduct(id);
}

// Usage
final product = ref.watch(productProvider('product-123'));
```

### AutoDispose

```dart
@riverpod
Future<ProductDetail> productDetail(ProductDetailRef ref, String id) async {
  // Auto-disposed when no longer watched
  ref.onDispose(() {
    print('Disposing product detail for $id');
  });

  final repository = ref.watch(productRepositoryProvider);
  return repository.getProductDetail(id);
}

// Keep alive temporarily
@riverpod
Future<UserProfile> userProfile(UserProfileRef ref) async {
  final link = ref.keepAlive();

  // Dispose after 5 minutes of not being used
  final timer = Timer(const Duration(minutes: 5), link.close);
  ref.onDispose(timer.cancel);

  return ref.watch(userRepositoryProvider).getProfile();
}
```

## Dependency Injection

```dart
// Repository provider
@riverpod
ProductRepository productRepository(ProductRepositoryRef ref) {
  final apiClient = ref.watch(apiClientProvider);
  final localDb = ref.watch(localDatabaseProvider);
  return ProductRepositoryImpl(apiClient, localDb);
}

// API client provider
@riverpod
ApiClient apiClient(ApiClientRef ref) {
  return ApiClient(
    baseUrl: Environment.apiBaseUrl,
    interceptors: [
      AuthInterceptor(ref.watch(tokenProvider)),
      LoggingInterceptor(),
    ],
  );
}
```

## Testing

```dart
void main() {
  group('CartNotifier', () {
    test('addItem adds product to cart', () async {
      final container = ProviderContainer();
      addTearDown(container.dispose);

      final cart = container.read(cartProvider);
      expect(cart.items, isEmpty);

      container.read(cartProvider.notifier).addItem(Product.fixture());

      expect(container.read(cartProvider).items.length, 1);
    });

    test('with mock repository', () async {
      final mockRepo = MockProductRepository();
      when(() => mockRepo.getProducts()).thenAnswer(
        (_) async => [Product.fixture()],
      );

      final container = ProviderContainer(
        overrides: [
          productRepositoryProvider.overrideWithValue(mockRepo),
        ],
      );
      addTearDown(container.dispose);

      final products = await container.read(productsProvider.future);
      expect(products.length, 1);
    });
  });
}
```

## Best Practices

1. **Use code generation** - riverpod_generator for type safety
2. **Keep providers small** - Single responsibility
3. **Use select** - Optimize rebuilds with selector
4. **AutoDispose by default** - Let Riverpod manage lifecycle
5. **Family for parameters** - Avoid creating providers dynamically
6. **Test with ProviderContainer** - Easy to mock and override
