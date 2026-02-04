---
name: flutter-state-notifier
description: StateNotifier pattern with freezed for immutable state
applies_to: flutter
---

# Flutter StateNotifier

## Overview

StateNotifier provides a simple way to manage immutable state. Often used with freezed for type-safe state classes and Riverpod for dependency injection.

## Dependencies

```yaml
dependencies:
  state_notifier: ^1.0.0
  flutter_state_notifier: ^1.0.0
  freezed_annotation: ^2.4.1

dev_dependencies:
  freezed: ^2.4.5
  build_runner: ^2.4.6
```

## Basic StateNotifier

### State Definition

```dart
import 'package:freezed_annotation/freezed_annotation.dart';

part 'counter_state.freezed.dart';

@freezed
class CounterState with _$CounterState {
  const factory CounterState({
    @Default(0) int count,
    @Default(false) bool isLoading,
  }) = _CounterState;
}
```

### StateNotifier Implementation

```dart
import 'package:state_notifier/state_notifier.dart';

class CounterNotifier extends StateNotifier<CounterState> {
  CounterNotifier() : super(const CounterState());

  void increment() {
    state = state.copyWith(count: state.count + 1);
  }

  void decrement() {
    state = state.copyWith(count: state.count - 1);
  }

  void reset() {
    state = const CounterState();
  }
}
```

## Complex State Management

### Products State

```dart
@freezed
class ProductsState with _$ProductsState {
  const factory ProductsState({
    @Default([]) List<Product> products,
    @Default(true) bool isLoading,
    @Default(false) bool isLoadingMore,
    @Default(false) bool hasReachedEnd,
    @Default(1) int currentPage,
    String? error,
  }) = _ProductsState;

  const ProductsState._();

  bool get hasError => error != null;
  bool get isEmpty => products.isEmpty && !isLoading;
  bool get canLoadMore => !isLoadingMore && !hasReachedEnd && !isLoading;
}
```

### Products StateNotifier

```dart
class ProductsNotifier extends StateNotifier<ProductsState> {
  final ProductRepository _repository;
  static const _pageSize = 20;

  ProductsNotifier(this._repository) : super(const ProductsState()) {
    loadProducts();
  }

  Future<void> loadProducts() async {
    state = state.copyWith(isLoading: true, error: null);

    try {
      final products = await _repository.getProducts(
        page: 1,
        limit: _pageSize,
      );
      state = state.copyWith(
        isLoading: false,
        products: products,
        currentPage: 1,
        hasReachedEnd: products.length < _pageSize,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
    }
  }

  Future<void> refresh() async {
    state = state.copyWith(
      isLoading: true,
      error: null,
      hasReachedEnd: false,
    );

    try {
      final products = await _repository.getProducts(
        page: 1,
        limit: _pageSize,
      );
      state = state.copyWith(
        isLoading: false,
        products: products,
        currentPage: 1,
        hasReachedEnd: products.length < _pageSize,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
    }
  }

  Future<void> loadMore() async {
    if (!state.canLoadMore) return;

    state = state.copyWith(isLoadingMore: true);

    try {
      final nextPage = state.currentPage + 1;
      final products = await _repository.getProducts(
        page: nextPage,
        limit: _pageSize,
      );
      state = state.copyWith(
        isLoadingMore: false,
        products: [...state.products, ...products],
        currentPage: nextPage,
        hasReachedEnd: products.length < _pageSize,
      );
    } catch (e) {
      state = state.copyWith(
        isLoadingMore: false,
        error: e.toString(),
      );
    }
  }
}
```

### Auth State with Union Types

```dart
@freezed
class AuthState with _$AuthState {
  const factory AuthState.initial() = AuthInitial;
  const factory AuthState.loading() = AuthLoading;
  const factory AuthState.authenticated(User user) = AuthAuthenticated;
  const factory AuthState.unauthenticated() = AuthUnauthenticated;
  const factory AuthState.error(String message) = AuthError;
}

class AuthNotifier extends StateNotifier<AuthState> {
  final AuthRepository _repository;

  AuthNotifier(this._repository) : super(const AuthState.initial()) {
    checkAuthStatus();
  }

  Future<void> checkAuthStatus() async {
    state = const AuthState.loading();

    try {
      final user = await _repository.getCurrentUser();
      state = user != null
          ? AuthState.authenticated(user)
          : const AuthState.unauthenticated();
    } catch (e) {
      state = AuthState.error(e.toString());
    }
  }

  Future<void> signIn(String email, String password) async {
    state = const AuthState.loading();

    try {
      final user = await _repository.signIn(email, password);
      state = AuthState.authenticated(user);
    } catch (e) {
      state = AuthState.error(e.toString());
    }
  }

  Future<void> signOut() async {
    await _repository.signOut();
    state = const AuthState.unauthenticated();
  }
}
```

## With Riverpod

### Provider Setup

```dart
// Repository provider
@riverpod
ProductRepository productRepository(ProductRepositoryRef ref) {
  return ProductRepositoryImpl(ref.watch(apiClientProvider));
}

// StateNotifier provider
@riverpod
class Products extends _$Products {
  @override
  ProductsState build() {
    _loadProducts();
    return const ProductsState();
  }

  Future<void> _loadProducts() async {
    state = state.copyWith(isLoading: true);
    try {
      final products = await ref.read(productRepositoryProvider).getProducts();
      state = state.copyWith(isLoading: false, products: products);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  Future<void> refresh() => _loadProducts();
}
```

### UI Integration

```dart
class ProductsPage extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(productsProvider);

    if (state.isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (state.hasError) {
      return ErrorView(
        message: state.error!,
        onRetry: () => ref.read(productsProvider.notifier).refresh(),
      );
    }

    if (state.isEmpty) {
      return const EmptyView(message: 'No products found');
    }

    return RefreshIndicator(
      onRefresh: () => ref.read(productsProvider.notifier).refresh(),
      child: ListView.builder(
        itemCount: state.products.length,
        itemBuilder: (_, index) => ProductTile(
          product: state.products[index],
        ),
      ),
    );
  }
}
```

### Union State Handling

```dart
class AuthWrapper extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authProvider);

    return authState.when(
      initial: () => const SplashScreen(),
      loading: () => const LoadingScreen(),
      authenticated: (user) => HomePage(user: user),
      unauthenticated: () => const LoginPage(),
      error: (message) => ErrorPage(
        message: message,
        onRetry: () => ref.read(authProvider.notifier).checkAuthStatus(),
      ),
    );
  }
}

// With maybeWhen for partial handling
Widget build(BuildContext context, WidgetRef ref) {
  final authState = ref.watch(authProvider);

  return authState.maybeWhen(
    authenticated: (user) => UserAvatar(user: user),
    orElse: () => const LoginButton(),
  );
}

// With map for explicit handling
Widget build(BuildContext context, WidgetRef ref) {
  final authState = ref.watch(authProvider);

  return authState.map(
    initial: (_) => const SplashScreen(),
    loading: (_) => const LoadingScreen(),
    authenticated: (state) => HomePage(user: state.user),
    unauthenticated: (_) => const LoginPage(),
    error: (state) => ErrorPage(message: state.message),
  );
}
```

## Form State Management

```dart
@freezed
class LoginFormState with _$LoginFormState {
  const factory LoginFormState({
    @Default('') String email,
    @Default('') String password,
    @Default(false) bool isSubmitting,
    @Default(false) bool showErrors,
    String? emailError,
    String? passwordError,
    String? submitError,
  }) = _LoginFormState;

  const LoginFormState._();

  bool get isValid => emailError == null && passwordError == null;
  bool get canSubmit => isValid && !isSubmitting && email.isNotEmpty && password.isNotEmpty;
}

class LoginFormNotifier extends StateNotifier<LoginFormState> {
  final AuthRepository _authRepository;

  LoginFormNotifier(this._authRepository) : super(const LoginFormState());

  void setEmail(String email) {
    state = state.copyWith(
      email: email,
      emailError: _validateEmail(email),
    );
  }

  void setPassword(String password) {
    state = state.copyWith(
      password: password,
      passwordError: _validatePassword(password),
    );
  }

  String? _validateEmail(String email) {
    if (email.isEmpty) return 'Email is required';
    if (!email.contains('@')) return 'Invalid email format';
    return null;
  }

  String? _validatePassword(String password) {
    if (password.isEmpty) return 'Password is required';
    if (password.length < 8) return 'Password must be at least 8 characters';
    return null;
  }

  Future<bool> submit() async {
    state = state.copyWith(showErrors: true);

    if (!state.canSubmit) return false;

    state = state.copyWith(isSubmitting: true, submitError: null);

    try {
      await _authRepository.signIn(state.email, state.password);
      return true;
    } catch (e) {
      state = state.copyWith(
        isSubmitting: false,
        submitError: e.toString(),
      );
      return false;
    }
  }
}
```

## LocatorMixin for Dependencies

```dart
class ProductsNotifier extends StateNotifier<ProductsState> with LocatorMixin {
  ProductsNotifier() : super(const ProductsState());

  // Access dependencies via read
  ProductRepository get _repository => read<ProductRepository>();

  @override
  void initState() {
    // Called after dependencies are available
    loadProducts();
  }

  Future<void> loadProducts() async {
    state = state.copyWith(isLoading: true);
    try {
      final products = await _repository.getProducts();
      state = state.copyWith(isLoading: false, products: products);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }
}

// Provider setup
StateNotifierProvider<ProductsNotifier, ProductsState>(
  create: (ref) => ProductsNotifier()
    ..read = ref.read, // Inject locator
  child: const ProductsPage(),
)
```

## Testing

```dart
void main() {
  group('ProductsNotifier', () {
    late ProductsNotifier notifier;
    late MockProductRepository mockRepository;

    setUp(() {
      mockRepository = MockProductRepository();
      notifier = ProductsNotifier(mockRepository);
    });

    tearDown(() => notifier.dispose());

    test('initial state is loading', () {
      expect(notifier.state.isLoading, isTrue);
    });

    test('loadProducts updates state with products', () async {
      when(() => mockRepository.getProducts(page: 1, limit: 20))
          .thenAnswer((_) async => [Product.fixture()]);

      await notifier.loadProducts();

      expect(notifier.state.isLoading, isFalse);
      expect(notifier.state.products.length, 1);
    });

    test('loadProducts sets error on failure', () async {
      when(() => mockRepository.getProducts(page: 1, limit: 20))
          .thenThrow(Exception('Network error'));

      await notifier.loadProducts();

      expect(notifier.state.isLoading, isFalse);
      expect(notifier.state.error, isNotNull);
    });
  });

  group('AuthNotifier', () {
    test('signIn transitions to authenticated', () async {
      final mockRepo = MockAuthRepository();
      when(() => mockRepo.signIn(any(), any()))
          .thenAnswer((_) async => User.fixture());

      final notifier = AuthNotifier(mockRepo);
      await notifier.signIn('test@example.com', 'password123');

      expect(
        notifier.state,
        isA<AuthAuthenticated>(),
      );
    });
  });
}
```

## Best Practices

1. **Use freezed** - Immutable, copyWith, union types
2. **Keep state flat** - Avoid deeply nested structures
3. **Computed properties** - Add getters for derived state
4. **Error handling** - Include error state in your model
5. **Union types** - Use for mutually exclusive states (loading/success/error)
6. **Test state transitions** - Verify state changes for each action
