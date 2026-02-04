---
name: flutter-bloc-pattern
description: BLoC pattern implementation with flutter_bloc
applies_to: flutter
---

# Flutter BLoC Pattern

## Overview

BLoC (Business Logic Component) separates business logic from UI using streams. Use flutter_bloc with freezed for type-safe, immutable events and states.

## Dependencies

```yaml
dependencies:
  flutter_bloc: ^8.1.3
  freezed_annotation: ^2.4.1

dev_dependencies:
  freezed: ^2.4.5
  build_runner: ^2.4.6
```

## Basic BLoC Structure

### Events

```dart
// products_event.dart
import 'package:freezed_annotation/freezed_annotation.dart';

part 'products_event.freezed.dart';

@freezed
class ProductsEvent with _$ProductsEvent {
  const factory ProductsEvent.started() = _Started;
  const factory ProductsEvent.refreshed() = _Refreshed;
  const factory ProductsEvent.loadMore() = _LoadMore;
  const factory ProductsEvent.searchChanged(String query) = _SearchChanged;
  const factory ProductsEvent.filterChanged(ProductFilter filter) = _FilterChanged;
}
```

### States

```dart
// products_state.dart
import 'package:freezed_annotation/freezed_annotation.dart';

part 'products_state.freezed.dart';

@freezed
class ProductsState with _$ProductsState {
  const factory ProductsState({
    @Default([]) List<Product> products,
    @Default(true) bool isLoading,
    @Default(false) bool isLoadingMore,
    @Default(false) bool hasReachedEnd,
    @Default('') String searchQuery,
    ProductFilter? filter,
    String? errorMessage,
  }) = _ProductsState;

  const ProductsState._();

  bool get hasError => errorMessage != null;
  bool get isEmpty => products.isEmpty && !isLoading;
  bool get canLoadMore => !isLoadingMore && !hasReachedEnd && !isLoading;
}
```

### BLoC Implementation

```dart
// products_bloc.dart
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:injectable/injectable.dart';

part 'products_event.dart';
part 'products_state.dart';

@injectable
class ProductsBloc extends Bloc<ProductsEvent, ProductsState> {
  final GetProductsUseCase _getProducts;
  final SearchProductsUseCase _searchProducts;

  static const _pageSize = 20;

  ProductsBloc({
    required GetProductsUseCase getProducts,
    required SearchProductsUseCase searchProducts,
  })  : _getProducts = getProducts,
        _searchProducts = searchProducts,
        super(const ProductsState()) {
    on<_Started>(_onStarted);
    on<_Refreshed>(_onRefreshed);
    on<_LoadMore>(_onLoadMore);
    on<_SearchChanged>(_onSearchChanged);
    on<_FilterChanged>(_onFilterChanged);
  }

  Future<void> _onStarted(
    _Started event,
    Emitter<ProductsState> emit,
  ) async {
    emit(state.copyWith(isLoading: true, errorMessage: null));

    final result = await _getProducts(
      GetProductsParams(limit: _pageSize, offset: 0),
    );

    result.fold(
      (failure) => emit(state.copyWith(
        isLoading: false,
        errorMessage: failure.message,
      )),
      (products) => emit(state.copyWith(
        isLoading: false,
        products: products,
        hasReachedEnd: products.length < _pageSize,
      )),
    );
  }

  Future<void> _onRefreshed(
    _Refreshed event,
    Emitter<ProductsState> emit,
  ) async {
    emit(state.copyWith(
      isLoading: true,
      errorMessage: null,
      hasReachedEnd: false,
    ));

    final result = await _getProducts(
      GetProductsParams(
        limit: _pageSize,
        offset: 0,
        query: state.searchQuery,
        filter: state.filter,
      ),
    );

    result.fold(
      (failure) => emit(state.copyWith(
        isLoading: false,
        errorMessage: failure.message,
      )),
      (products) => emit(state.copyWith(
        isLoading: false,
        products: products,
        hasReachedEnd: products.length < _pageSize,
      )),
    );
  }

  Future<void> _onLoadMore(
    _LoadMore event,
    Emitter<ProductsState> emit,
  ) async {
    if (!state.canLoadMore) return;

    emit(state.copyWith(isLoadingMore: true));

    final result = await _getProducts(
      GetProductsParams(
        limit: _pageSize,
        offset: state.products.length,
        query: state.searchQuery,
        filter: state.filter,
      ),
    );

    result.fold(
      (failure) => emit(state.copyWith(
        isLoadingMore: false,
        errorMessage: failure.message,
      )),
      (products) => emit(state.copyWith(
        isLoadingMore: false,
        products: [...state.products, ...products],
        hasReachedEnd: products.length < _pageSize,
      )),
    );
  }

  Future<void> _onSearchChanged(
    _SearchChanged event,
    Emitter<ProductsState> emit,
  ) async {
    emit(state.copyWith(
      searchQuery: event.query,
      isLoading: true,
      hasReachedEnd: false,
    ));

    final result = await _searchProducts(event.query);

    result.fold(
      (failure) => emit(state.copyWith(
        isLoading: false,
        errorMessage: failure.message,
      )),
      (products) => emit(state.copyWith(
        isLoading: false,
        products: products,
      )),
    );
  }

  Future<void> _onFilterChanged(
    _FilterChanged event,
    Emitter<ProductsState> emit,
  ) async {
    emit(state.copyWith(filter: event.filter));
    add(const ProductsEvent.refreshed());
  }
}
```

## Cubit (Simplified BLoC)

```dart
// counter_cubit.dart
import 'package:flutter_bloc/flutter_bloc.dart';

class CounterCubit extends Cubit<int> {
  CounterCubit() : super(0);

  void increment() => emit(state + 1);
  void decrement() => emit(state - 1);
  void reset() => emit(0);
}

// With complex state
@freezed
class AuthState with _$AuthState {
  const factory AuthState.initial() = _Initial;
  const factory AuthState.loading() = _Loading;
  const factory AuthState.authenticated(User user) = _Authenticated;
  const factory AuthState.unauthenticated() = _Unauthenticated;
  const factory AuthState.error(String message) = _Error;
}

class AuthCubit extends Cubit<AuthState> {
  final AuthRepository _authRepository;

  AuthCubit(this._authRepository) : super(const AuthState.initial());

  Future<void> checkAuthStatus() async {
    emit(const AuthState.loading());
    final user = await _authRepository.getCurrentUser();
    if (user != null) {
      emit(AuthState.authenticated(user));
    } else {
      emit(const AuthState.unauthenticated());
    }
  }

  Future<void> signIn(String email, String password) async {
    emit(const AuthState.loading());
    final result = await _authRepository.signIn(email, password);
    result.fold(
      (failure) => emit(AuthState.error(failure.message)),
      (user) => emit(AuthState.authenticated(user)),
    );
  }

  Future<void> signOut() async {
    await _authRepository.signOut();
    emit(const AuthState.unauthenticated());
  }
}
```

## UI Integration

### BlocProvider

```dart
// Providing a BLoC
class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MultiBlocProvider(
      providers: [
        BlocProvider(create: (_) => getIt<AuthCubit>()..checkAuthStatus()),
        BlocProvider(create: (_) => getIt<ThemeCubit>()),
      ],
      child: MaterialApp(
        home: const HomePage(),
      ),
    );
  }
}

// Feature-level provider
class ProductsPage extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => getIt<ProductsBloc>()..add(const ProductsEvent.started()),
      child: const ProductsView(),
    );
  }
}
```

### BlocBuilder

```dart
class ProductsView extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return BlocBuilder<ProductsBloc, ProductsState>(
      builder: (context, state) {
        if (state.isLoading) {
          return const Center(child: CircularProgressIndicator());
        }

        if (state.hasError) {
          return ErrorView(
            message: state.errorMessage!,
            onRetry: () => context.read<ProductsBloc>().add(
              const ProductsEvent.refreshed(),
            ),
          );
        }

        if (state.isEmpty) {
          return const EmptyView(message: 'No products found');
        }

        return ProductsList(
          products: state.products,
          isLoadingMore: state.isLoadingMore,
          onLoadMore: () => context.read<ProductsBloc>().add(
            const ProductsEvent.loadMore(),
          ),
        );
      },
    );
  }
}

// With buildWhen for optimization
BlocBuilder<ProductsBloc, ProductsState>(
  buildWhen: (previous, current) =>
      previous.products != current.products ||
      previous.isLoading != current.isLoading,
  builder: (context, state) {
    // Only rebuilds when products or isLoading changes
  },
)
```

### BlocListener

```dart
BlocListener<AuthCubit, AuthState>(
  listener: (context, state) {
    state.maybeWhen(
      error: (message) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(message)),
        );
      },
      authenticated: (_) {
        context.go('/home');
      },
      unauthenticated: () {
        context.go('/login');
      },
      orElse: () {},
    );
  },
  child: const AuthView(),
)
```

### BlocConsumer

```dart
BlocConsumer<ProductsBloc, ProductsState>(
  listenWhen: (previous, current) =>
      previous.errorMessage != current.errorMessage,
  listener: (context, state) {
    if (state.hasError) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(state.errorMessage!)),
      );
    }
  },
  buildWhen: (previous, current) =>
      previous.products != current.products ||
      previous.isLoading != current.isLoading,
  builder: (context, state) {
    return ProductsList(products: state.products);
  },
)
```

### BlocSelector

```dart
// Select specific parts of state
BlocSelector<ProductsBloc, ProductsState, bool>(
  selector: (state) => state.isLoading,
  builder: (context, isLoading) {
    return isLoading
        ? const CircularProgressIndicator()
        : const SizedBox.shrink();
  },
)

// Select computed values
BlocSelector<CartBloc, CartState, double>(
  selector: (state) => state.items.fold(
    0.0,
    (total, item) => total + item.price * item.quantity,
  ),
  builder: (context, total) {
    return Text('Total: \$${total.toStringAsFixed(2)}');
  },
)
```

## Event Transformers

```dart
// Debounce search events
on<_SearchChanged>(
  _onSearchChanged,
  transformer: debounce(const Duration(milliseconds: 300)),
);

// Sequential processing
on<_LoadMore>(
  _onLoadMore,
  transformer: droppable(),
);

// Custom transformer
EventTransformer<E> debounce<E>(Duration duration) {
  return (events, mapper) => events.debounceTime(duration).flatMap(mapper);
}

EventTransformer<E> droppable<E>() {
  return (events, mapper) => events.exhaustMap(mapper);
}
```

## Testing

```dart
import 'package:bloc_test/bloc_test.dart';
import 'package:mocktail/mocktail.dart';

class MockGetProductsUseCase extends Mock implements GetProductsUseCase {}

void main() {
  late ProductsBloc bloc;
  late MockGetProductsUseCase mockGetProducts;

  setUp(() {
    mockGetProducts = MockGetProductsUseCase();
    bloc = ProductsBloc(getProducts: mockGetProducts);
  });

  tearDown(() => bloc.close());

  blocTest<ProductsBloc, ProductsState>(
    'emits [loading, loaded] when started successfully',
    build: () {
      when(() => mockGetProducts(any())).thenAnswer(
        (_) async => Right([Product.fixture()]),
      );
      return bloc;
    },
    act: (bloc) => bloc.add(const ProductsEvent.started()),
    expect: () => [
      const ProductsState(isLoading: true),
      ProductsState(
        isLoading: false,
        products: [Product.fixture()],
      ),
    ],
    verify: (_) {
      verify(() => mockGetProducts(any())).called(1);
    },
  );
}
```

## Best Practices

1. **Use freezed** - Type-safe events and states
2. **Single responsibility** - One BLoC per feature
3. **Use Cubit for simple state** - When events aren't needed
4. **Optimize with buildWhen** - Prevent unnecessary rebuilds
5. **Transform events** - Debounce, throttle, drop as needed
6. **Test thoroughly** - Use bloc_test for predictable testing
