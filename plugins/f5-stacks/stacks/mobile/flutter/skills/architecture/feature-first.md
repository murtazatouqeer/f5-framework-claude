---
name: flutter-feature-first
description: Feature-first architecture organization in Flutter
applies_to: flutter
---

# Feature-First Architecture

## Overview

Feature-first architecture organizes code by business features rather than technical layers, improving modularity and team scalability.

## Structure

```
lib/
├── features/
│   ├── auth/                      # Authentication feature
│   │   ├── auth.dart              # Barrel file
│   │   ├── data/
│   │   ├── domain/
│   │   └── presentation/
│   │
│   ├── products/                  # Products feature
│   │   ├── products.dart
│   │   ├── data/
│   │   ├── domain/
│   │   └── presentation/
│   │
│   ├── cart/                      # Cart feature
│   │   ├── cart.dart
│   │   ├── data/
│   │   ├── domain/
│   │   └── presentation/
│   │
│   └── orders/                    # Orders feature
│       ├── orders.dart
│       ├── data/
│       ├── domain/
│       └── presentation/
│
├── core/                          # Shared infrastructure
│   ├── network/
│   ├── storage/
│   └── utils/
│
└── shared/                        # Shared UI components
    ├── widgets/
    └── theme/
```

## Feature Module Structure

```dart
// features/products/
├── products.dart                  # Barrel export file
│
├── data/
│   ├── datasources/
│   │   ├── product_remote_datasource.dart
│   │   └── product_local_datasource.dart
│   ├── models/
│   │   ├── product_model.dart
│   │   └── category_model.dart
│   └── repositories/
│       └── product_repository_impl.dart
│
├── domain/
│   ├── entities/
│   │   ├── product.dart
│   │   └── category.dart
│   ├── repositories/
│   │   └── product_repository.dart
│   └── usecases/
│       ├── get_products.dart
│       ├── get_product.dart
│       ├── create_product.dart
│       ├── update_product.dart
│       └── delete_product.dart
│
└── presentation/
    ├── bloc/
    │   ├── products/
    │   │   ├── products_bloc.dart
    │   │   ├── products_event.dart
    │   │   └── products_state.dart
    │   └── product_detail/
    │       ├── product_detail_bloc.dart
    │       ├── product_detail_event.dart
    │       └── product_detail_state.dart
    ├── pages/
    │   ├── products_page.dart
    │   ├── product_detail_page.dart
    │   └── product_create_page.dart
    └── widgets/
        ├── product_card.dart
        ├── product_list.dart
        ├── product_form.dart
        └── category_filter.dart
```

## Barrel File Pattern

```dart
// features/products/products.dart
// Domain
export 'domain/entities/product.dart';
export 'domain/entities/category.dart';
export 'domain/repositories/product_repository.dart';
export 'domain/usecases/get_products.dart';
export 'domain/usecases/get_product.dart';
export 'domain/usecases/create_product.dart';

// Presentation
export 'presentation/bloc/products/products_bloc.dart';
export 'presentation/bloc/product_detail/product_detail_bloc.dart';
export 'presentation/pages/products_page.dart';
export 'presentation/pages/product_detail_page.dart';
export 'presentation/widgets/product_card.dart';
export 'presentation/widgets/product_list.dart';
```

## Feature Registration

```dart
// features/products/di/products_module.dart
import 'package:injectable/injectable.dart';

@module
abstract class ProductsModule {
  // Register feature-specific dependencies here
  // Most registrations are automatic via @injectable
}

// app/di.dart
import 'package:get_it/get_it.dart';
import 'package:injectable/injectable.dart';
import 'di.config.dart';

final getIt = GetIt.instance;

@InjectableInit(preferRelativeImports: true)
void configureDependencies() => getIt.init();
```

## Feature Routes

```dart
// features/products/presentation/routes.dart
import 'package:go_router/go_router.dart';
import 'pages/products_page.dart';
import 'pages/product_detail_page.dart';
import 'pages/product_create_page.dart';

final productsRoutes = [
  GoRoute(
    path: '/products',
    name: 'products',
    builder: (context, state) => const ProductsPage(),
    routes: [
      GoRoute(
        path: 'create',
        name: 'product-create',
        builder: (context, state) => const ProductCreatePage(),
      ),
      GoRoute(
        path: ':id',
        name: 'product-detail',
        builder: (context, state) {
          final id = state.pathParameters['id']!;
          return ProductDetailPage(productId: id);
        },
        routes: [
          GoRoute(
            path: 'edit',
            name: 'product-edit',
            builder: (context, state) {
              final id = state.pathParameters['id']!;
              return ProductEditPage(productId: id);
            },
          ),
        ],
      ),
    ],
  ),
];

// app/router.dart
import 'package:go_router/go_router.dart';
import '../features/auth/presentation/routes.dart';
import '../features/products/presentation/routes.dart';
import '../features/cart/presentation/routes.dart';
import '../features/orders/presentation/routes.dart';

final router = GoRouter(
  initialLocation: '/products',
  routes: [
    ...authRoutes,
    ...productsRoutes,
    ...cartRoutes,
    ...ordersRoutes,
  ],
);
```

## Feature Communication

### Using BLoC-to-BLoC

```dart
// Listening to another feature's BLoC
class CartBloc extends Bloc<CartEvent, CartState> {
  final ProductsBloc _productsBloc;
  late final StreamSubscription _productsSub;

  CartBloc({required ProductsBloc productsBloc})
      : _productsBloc = productsBloc,
        super(const CartState()) {
    // Listen to product updates
    _productsSub = _productsBloc.stream.listen((state) {
      // Update cart if product prices changed
      if (state.products.isNotEmpty) {
        add(const CartEvent.syncPrices());
      }
    });
  }

  @override
  Future<void> close() {
    _productsSub.cancel();
    return super.close();
  }
}
```

### Using Shared Domain Events

```dart
// core/events/domain_events.dart
import 'dart:async';

class DomainEventBus {
  static final _controller = StreamController<DomainEvent>.broadcast();

  static Stream<DomainEvent> get stream => _controller.stream;

  static void emit(DomainEvent event) {
    _controller.add(event);
  }
}

abstract class DomainEvent {}

class ProductAddedToCart extends DomainEvent {
  final String productId;
  final int quantity;
  ProductAddedToCart(this.productId, this.quantity);
}

class OrderCompleted extends DomainEvent {
  final String orderId;
  OrderCompleted(this.orderId);
}

// Usage in BLoC
class CartBloc extends Bloc<CartEvent, CartState> {
  CartBloc() : super(const CartState()) {
    on<AddToCart>(_onAddToCart);
  }

  Future<void> _onAddToCart(
    AddToCart event,
    Emitter<CartState> emit,
  ) async {
    // Add to cart logic...

    // Emit domain event
    DomainEventBus.emit(
      ProductAddedToCart(event.productId, event.quantity),
    );
  }
}
```

## Feature Isolation Rules

1. **No direct imports** - Features import only from their barrel file
2. **Shared via core** - Cross-feature code goes in core/
3. **Domain independence** - Domain layer has no external dependencies
4. **Presentation isolation** - Pages don't import other features' pages
5. **Route composition** - Routes are composed at app level

## Testing Features

```dart
// test/features/products/
├── data/
│   ├── datasources/
│   │   └── product_remote_datasource_test.dart
│   └── repositories/
│       └── product_repository_impl_test.dart
├── domain/
│   └── usecases/
│       ├── get_products_test.dart
│       └── create_product_test.dart
└── presentation/
    ├── bloc/
    │   └── products_bloc_test.dart
    └── pages/
        └── products_page_test.dart
```

## Best Practices

1. **Self-contained features** - Each feature is independently testable
2. **Barrel exports** - Use barrel files for clean imports
3. **Feature routes** - Define routes within each feature
4. **Minimal coupling** - Communicate via events or shared domain
5. **Team ownership** - Assign feature ownership to teams
