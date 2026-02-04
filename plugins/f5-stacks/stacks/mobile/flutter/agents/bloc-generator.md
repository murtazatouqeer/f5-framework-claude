---
name: flutter-bloc-generator
description: Generates Flutter BLoC/Cubit with events and states
applies_to: flutter
---

# Flutter BLoC Generator Agent

## Purpose

Generates complete BLoC implementation with events, states, and proper error handling using freezed for immutable classes.

## Capabilities

- Generate BLoC or Cubit based on complexity
- Create freezed events and states
- Add use case integration
- Include error handling patterns
- Generate corresponding tests

## Input Requirements

| Field | Required | Description |
|-------|----------|-------------|
| `feature_name` | Yes | Feature/module name |
| `bloc_name` | Yes | BLoC name |
| `type` | No | `bloc` or `cubit` |
| `use_cases` | No | List of use cases to inject |
| `has_pagination` | No | Whether to include pagination |

## Generated Files

```
features/{feature}/presentation/bloc/
├── {bloc}_bloc.dart
├── {bloc}_event.dart (for BLoC)
└── {bloc}_state.dart
test/features/{feature}/presentation/bloc/
└── {bloc}_bloc_test.dart
```

## Example Usage

```yaml
feature_name: products
bloc_name: products
type: bloc
use_cases:
  - GetProducts
  - DeleteProduct
has_pagination: true
```

## Output Pattern

### Event (with freezed)

```dart
// features/products/presentation/bloc/products_event.dart
import 'package:freezed_annotation/freezed_annotation.dart';

part 'products_event.freezed.dart';

@freezed
class ProductsEvent with _$ProductsEvent {
  const factory ProductsEvent.load({
    @Default(1) int page,
    String? search,
    String? categoryId,
  }) = LoadProducts;

  const factory ProductsEvent.refresh() = RefreshProducts;

  const factory ProductsEvent.loadMore() = LoadMoreProducts;

  const factory ProductsEvent.search(String query) = SearchProducts;

  const factory ProductsEvent.delete(String id) = DeleteProduct;

  const factory ProductsEvent.clearError() = ClearError;
}
```

### State (with freezed)

```dart
// features/products/presentation/bloc/products_state.dart
import 'package:freezed_annotation/freezed_annotation.dart';
import '../../domain/entities/product.dart';

part 'products_state.freezed.dart';

@freezed
class ProductsState with _$ProductsState {
  const factory ProductsState({
    @Default([]) List<Product> products,
    @Default(false) bool isLoading,
    @Default(false) bool isLoadingMore,
    @Default(false) bool hasReachedMax,
    @Default(1) int currentPage,
    @Default('') String searchQuery,
    String? error,
    Product? selectedProduct,
  }) = _ProductsState;

  const ProductsState._();

  bool get isEmpty => products.isEmpty && !isLoading;
  bool get hasProducts => products.isNotEmpty;
  bool get canLoadMore => !hasReachedMax && !isLoadingMore && !isLoading;
  bool get hasError => error != null;
}
```

### BLoC Implementation

```dart
// features/products/presentation/bloc/products_bloc.dart
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:injectable/injectable.dart';
import '../../domain/usecases/get_products.dart';
import '../../domain/usecases/delete_product.dart';
import 'products_event.dart';
import 'products_state.dart';

@injectable
class ProductsBloc extends Bloc<ProductsEvent, ProductsState> {
  final GetProducts _getProducts;
  final DeleteProduct _deleteProduct;

  ProductsBloc({
    required GetProducts getProducts,
    required DeleteProduct deleteProduct,
  })  : _getProducts = getProducts,
        _deleteProduct = deleteProduct,
        super(const ProductsState()) {
    on<LoadProducts>(_onLoad);
    on<RefreshProducts>(_onRefresh);
    on<LoadMoreProducts>(_onLoadMore);
    on<SearchProducts>(_onSearch);
    on<DeleteProduct>(_onDelete);
    on<ClearError>(_onClearError);
  }

  Future<void> _onLoad(
    LoadProducts event,
    Emitter<ProductsState> emit,
  ) async {
    emit(state.copyWith(isLoading: true, error: null));

    final result = await _getProducts(
      GetProductsParams(
        page: event.page,
        search: event.search ?? state.searchQuery,
        categoryId: event.categoryId,
      ),
    );

    result.fold(
      (failure) => emit(state.copyWith(
        isLoading: false,
        error: failure.message,
      )),
      (paginated) => emit(state.copyWith(
        isLoading: false,
        products: paginated.items,
        currentPage: event.page,
        hasReachedMax: paginated.items.length < 20,
      )),
    );
  }

  Future<void> _onRefresh(
    RefreshProducts event,
    Emitter<ProductsState> emit,
  ) async {
    emit(state.copyWith(
      currentPage: 1,
      hasReachedMax: false,
    ));
    add(const ProductsEvent.load());
  }

  Future<void> _onLoadMore(
    LoadMoreProducts event,
    Emitter<ProductsState> emit,
  ) async {
    if (!state.canLoadMore) return;

    emit(state.copyWith(isLoadingMore: true));

    final result = await _getProducts(
      GetProductsParams(
        page: state.currentPage + 1,
        search: state.searchQuery.isNotEmpty ? state.searchQuery : null,
      ),
    );

    result.fold(
      (failure) => emit(state.copyWith(
        isLoadingMore: false,
        error: failure.message,
      )),
      (paginated) => emit(state.copyWith(
        isLoadingMore: false,
        products: [...state.products, ...paginated.items],
        currentPage: state.currentPage + 1,
        hasReachedMax: paginated.items.length < 20,
      )),
    );
  }

  Future<void> _onSearch(
    SearchProducts event,
    Emitter<ProductsState> emit,
  ) async {
    emit(state.copyWith(
      searchQuery: event.query,
      currentPage: 1,
      hasReachedMax: false,
    ));
    add(const ProductsEvent.load());
  }

  Future<void> _onDelete(
    DeleteProduct event,
    Emitter<ProductsState> emit,
  ) async {
    final result = await _deleteProduct(event.id);

    result.fold(
      (failure) => emit(state.copyWith(error: failure.message)),
      (_) => emit(state.copyWith(
        products: state.products.where((p) => p.id != event.id).toList(),
      )),
    );
  }

  void _onClearError(
    ClearError event,
    Emitter<ProductsState> emit,
  ) {
    emit(state.copyWith(error: null));
  }
}
```

## Best Practices

1. **Use freezed** - For immutable events and states
2. **Injectable** - Use dependency injection
3. **Named constructors** - For clear event naming
4. **Computed properties** - Add getters to state
5. **Error handling** - Always handle failures from use cases
6. **Clear error action** - Allow clearing error state
