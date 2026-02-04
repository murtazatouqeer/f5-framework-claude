---
name: flutter-provider
description: Provider package for state management in Flutter
applies_to: flutter
---

# Flutter Provider

## Overview

Provider is a wrapper around InheritedWidget for simple dependency injection and state management. Good for small to medium apps.

## Dependencies

```yaml
dependencies:
  provider: ^6.1.1
```

## Basic Provider Types

### Provider (Read-only dependency)

```dart
// Providing a service
class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Provider<ApiService>(
      create: (_) => ApiService(),
      child: const MaterialApp(home: HomePage()),
    );
  }
}

// Consuming
class HomePage extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final apiService = context.read<ApiService>();
    // or
    final apiService = Provider.of<ApiService>(context, listen: false);

    return ElevatedButton(
      onPressed: () => apiService.fetchData(),
      child: const Text('Fetch'),
    );
  }
}
```

### ChangeNotifierProvider (Mutable state)

```dart
class CounterNotifier extends ChangeNotifier {
  int _count = 0;

  int get count => _count;

  void increment() {
    _count++;
    notifyListeners();
  }

  void decrement() {
    _count--;
    notifyListeners();
  }

  void reset() {
    _count = 0;
    notifyListeners();
  }
}

// Providing
ChangeNotifierProvider(
  create: (_) => CounterNotifier(),
  child: const CounterPage(),
)

// Consuming with rebuild
class CounterDisplay extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final count = context.watch<CounterNotifier>().count;
    return Text('Count: $count');
  }
}

// Consuming without rebuild
class CounterButtons extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        IconButton(
          onPressed: () => context.read<CounterNotifier>().decrement(),
          icon: const Icon(Icons.remove),
        ),
        IconButton(
          onPressed: () => context.read<CounterNotifier>().increment(),
          icon: const Icon(Icons.add),
        ),
      ],
    );
  }
}
```

### ValueNotifier with ValueListenableProvider

```dart
// Simple value state
ValueListenableProvider<int>(
  create: (_) => ValueNotifier<int>(0),
  child: const MyApp(),
)

// Consuming
class Counter extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final count = context.watch<ValueNotifier<int>>().value;
    return Text('$count');
  }
}

// Updating
context.read<ValueNotifier<int>>().value++;
```

### FutureProvider (Async data)

```dart
FutureProvider<List<Product>>(
  create: (context) {
    final repository = context.read<ProductRepository>();
    return repository.getProducts();
  },
  initialData: const [],
  catchError: (context, error) {
    debugPrint('Error: $error');
    return [];
  },
  child: const ProductsPage(),
)

// Consuming
class ProductsPage extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final products = context.watch<List<Product>>();
    return ListView.builder(
      itemCount: products.length,
      itemBuilder: (_, index) => ProductTile(product: products[index]),
    );
  }
}
```

### StreamProvider (Real-time data)

```dart
StreamProvider<User?>(
  create: (context) {
    final auth = context.read<AuthService>();
    return auth.userChanges;
  },
  initialData: null,
  child: const MyApp(),
)

// Consuming
class UserAvatar extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final user = context.watch<User?>();
    if (user == null) return const LoginButton();
    return CircleAvatar(
      backgroundImage: NetworkImage(user.photoUrl),
    );
  }
}
```

## Complex State Management

### Cart Example

```dart
class CartNotifier extends ChangeNotifier {
  final List<CartItem> _items = [];

  List<CartItem> get items => List.unmodifiable(_items);

  int get itemCount => _items.fold(0, (sum, item) => sum + item.quantity);

  double get total => _items.fold(
    0.0,
    (sum, item) => sum + item.price * item.quantity,
  );

  void addItem(Product product, {int quantity = 1}) {
    final existingIndex = _items.indexWhere(
      (item) => item.productId == product.id,
    );

    if (existingIndex >= 0) {
      _items[existingIndex] = _items[existingIndex].copyWith(
        quantity: _items[existingIndex].quantity + quantity,
      );
    } else {
      _items.add(CartItem(
        productId: product.id,
        name: product.name,
        price: product.price,
        quantity: quantity,
        imageUrl: product.imageUrl,
      ));
    }
    notifyListeners();
  }

  void removeItem(String productId) {
    _items.removeWhere((item) => item.productId == productId);
    notifyListeners();
  }

  void updateQuantity(String productId, int quantity) {
    if (quantity <= 0) {
      removeItem(productId);
      return;
    }

    final index = _items.indexWhere((item) => item.productId == productId);
    if (index >= 0) {
      _items[index] = _items[index].copyWith(quantity: quantity);
      notifyListeners();
    }
  }

  void clear() {
    _items.clear();
    notifyListeners();
  }
}
```

### Auth Example

```dart
enum AuthStatus { initial, loading, authenticated, unauthenticated, error }

class AuthNotifier extends ChangeNotifier {
  final AuthRepository _repository;

  AuthNotifier(this._repository);

  AuthStatus _status = AuthStatus.initial;
  User? _user;
  String? _errorMessage;

  AuthStatus get status => _status;
  User? get user => _user;
  String? get errorMessage => _errorMessage;
  bool get isAuthenticated => _status == AuthStatus.authenticated;

  Future<void> checkAuthStatus() async {
    _status = AuthStatus.loading;
    notifyListeners();

    try {
      _user = await _repository.getCurrentUser();
      _status = _user != null
          ? AuthStatus.authenticated
          : AuthStatus.unauthenticated;
    } catch (e) {
      _status = AuthStatus.error;
      _errorMessage = e.toString();
    }
    notifyListeners();
  }

  Future<void> signIn(String email, String password) async {
    _status = AuthStatus.loading;
    _errorMessage = null;
    notifyListeners();

    try {
      _user = await _repository.signIn(email, password);
      _status = AuthStatus.authenticated;
    } catch (e) {
      _status = AuthStatus.error;
      _errorMessage = e.toString();
    }
    notifyListeners();
  }

  Future<void> signOut() async {
    await _repository.signOut();
    _user = null;
    _status = AuthStatus.unauthenticated;
    notifyListeners();
  }
}
```

## MultiProvider Setup

```dart
class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        // Services (read-only)
        Provider<ApiService>(create: (_) => ApiService()),
        Provider<StorageService>(create: (_) => StorageService()),

        // Repositories (dependent on services)
        ProxyProvider<ApiService, ProductRepository>(
          update: (_, api, __) => ProductRepositoryImpl(api),
        ),
        ProxyProvider2<ApiService, StorageService, AuthRepository>(
          update: (_, api, storage, __) => AuthRepositoryImpl(api, storage),
        ),

        // State (dependent on repositories)
        ChangeNotifierProxyProvider<AuthRepository, AuthNotifier>(
          create: (context) => AuthNotifier(context.read<AuthRepository>()),
          update: (_, repo, notifier) => notifier!..updateRepository(repo),
        ),
        ChangeNotifierProvider(create: (_) => CartNotifier()),
        ChangeNotifierProvider(create: (_) => ThemeNotifier()),
      ],
      child: const AppRoot(),
    );
  }
}
```

## Selector for Performance

```dart
// Only rebuilds when specific value changes
class CartBadge extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    // Only rebuilds when itemCount changes
    final itemCount = context.select<CartNotifier, int>(
      (cart) => cart.itemCount,
    );

    return Badge(
      label: Text('$itemCount'),
      child: const Icon(Icons.shopping_cart),
    );
  }
}

// Multiple selectors
class CartSummary extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final itemCount = context.select<CartNotifier, int>((c) => c.itemCount);
    final total = context.select<CartNotifier, double>((c) => c.total);

    return Text('$itemCount items - \$${total.toStringAsFixed(2)}');
  }
}
```

## Consumer Widget

```dart
class ProductCard extends StatelessWidget {
  final Product product;

  const ProductCard({required this.product});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Column(
        children: [
          Image.network(product.imageUrl),
          Text(product.name),
          Text('\$${product.price}'),

          // Only this part rebuilds when cart changes
          Consumer<CartNotifier>(
            builder: (context, cart, child) {
              final isInCart = cart.items.any(
                (item) => item.productId == product.id,
              );

              return IconButton(
                icon: Icon(
                  isInCart ? Icons.check : Icons.add_shopping_cart,
                ),
                onPressed: isInCart
                    ? null
                    : () => cart.addItem(product),
              );
            },
          ),
        ],
      ),
    );
  }
}

// Consumer2 for multiple providers
Consumer2<CartNotifier, AuthNotifier>(
  builder: (context, cart, auth, child) {
    if (!auth.isAuthenticated) {
      return const LoginPrompt();
    }
    return CartView(items: cart.items);
  },
)
```

## Lazy Loading

```dart
// Provider is created lazily by default
Provider<ExpensiveService>(
  create: (_) => ExpensiveService(), // Called only when first accessed
  lazy: true, // Default
  child: const MyApp(),
)

// Eager creation
Provider<CriticalService>(
  create: (_) => CriticalService(),
  lazy: false, // Created immediately
  child: const MyApp(),
)
```

## Dispose Pattern

```dart
ChangeNotifierProvider(
  create: (_) => MyNotifier(),
  // Automatically disposes the notifier
  child: const MyApp(),
)

// Manual dispose control
Provider<StreamController<int>>(
  create: (_) => StreamController<int>(),
  dispose: (_, controller) => controller.close(),
  child: const MyApp(),
)
```

## Testing

```dart
void main() {
  testWidgets('CartPage shows items', (tester) async {
    final cart = CartNotifier();
    cart.addItem(Product.fixture());

    await tester.pumpWidget(
      ChangeNotifierProvider.value(
        value: cart,
        child: const MaterialApp(home: CartPage()),
      ),
    );

    expect(find.text('Test Product'), findsOneWidget);
  });

  testWidgets('with mock', (tester) async {
    final mockAuth = MockAuthNotifier();
    when(() => mockAuth.isAuthenticated).thenReturn(true);
    when(() => mockAuth.user).thenReturn(User.fixture());

    await tester.pumpWidget(
      ChangeNotifierProvider<AuthNotifier>.value(
        value: mockAuth,
        child: const MaterialApp(home: ProfilePage()),
      ),
    );

    expect(find.text('Test User'), findsOneWidget);
  });
}
```

## Best Practices

1. **Use context.read for callbacks** - Avoid unnecessary rebuilds
2. **Use context.watch in build** - For reactive updates
3. **Use Selector** - Optimize rebuilds for specific values
4. **Use Consumer** - For partial widget rebuilds
5. **Dispose properly** - Use dispose callback for cleanup
6. **Keep notifiers simple** - Single responsibility per notifier
