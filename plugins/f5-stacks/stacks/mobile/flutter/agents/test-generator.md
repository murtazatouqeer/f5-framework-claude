---
name: flutter-test-generator
description: Generates Flutter tests for BLoC, widgets, and integration
applies_to: flutter
---

# Flutter Test Generator Agent

## Purpose

Generates comprehensive tests for Flutter applications including BLoC tests, widget tests, and integration tests.

## Capabilities

- Generate BLoC/Cubit unit tests
- Create widget tests with mocked dependencies
- Generate integration tests
- Add golden tests for visual regression
- Include test utilities and fixtures

## Input Requirements

| Field | Required | Description |
|-------|----------|-------------|
| `feature_name` | Yes | Feature/module name |
| `test_type` | Yes | `bloc`, `widget`, `integration` |
| `target` | Yes | Class/widget to test |
| `scenarios` | No | List of test scenarios |

## Generated Files

```
test/
├── features/{feature}/
│   ├── presentation/
│   │   ├── bloc/
│   │   │   └── {bloc}_bloc_test.dart
│   │   └── pages/
│   │       └── {page}_page_test.dart
│   └── domain/
│       └── usecases/
│           └── {usecase}_test.dart
├── fixtures/
│   └── {feature}_fixtures.dart
└── helpers/
    └── pump_app.dart
```

## Example Usage

```yaml
feature_name: products
test_type: bloc
target: ProductsBloc
scenarios:
  - load_success
  - load_failure
  - load_more
  - delete
```

## Output Pattern

### BLoC Test

```dart
// test/features/products/presentation/bloc/products_bloc_test.dart
import 'package:bloc_test/bloc_test.dart';
import 'package:dartz/dartz.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:app/core/errors/failures.dart';
import 'package:app/features/products/domain/entities/product.dart';
import 'package:app/features/products/domain/usecases/get_products.dart';
import 'package:app/features/products/domain/usecases/delete_product.dart';
import 'package:app/features/products/presentation/bloc/products_bloc.dart';

class MockGetProducts extends Mock implements GetProducts {}
class MockDeleteProduct extends Mock implements DeleteProduct {}

void main() {
  late ProductsBloc bloc;
  late MockGetProducts mockGetProducts;
  late MockDeleteProduct mockDeleteProduct;

  setUp(() {
    mockGetProducts = MockGetProducts();
    mockDeleteProduct = MockDeleteProduct();
    bloc = ProductsBloc(
      getProducts: mockGetProducts,
      deleteProduct: mockDeleteProduct,
    );
  });

  setUpAll(() {
    registerFallbackValue(const GetProductsParams());
  });

  tearDown(() {
    bloc.close();
  });

  group('ProductsBloc', () {
    final testProducts = [
      const Product(id: '1', name: 'Product 1', price: 10.0),
      const Product(id: '2', name: 'Product 2', price: 20.0),
    ];

    final testPaginated = PaginatedList(
      items: testProducts,
      total: 2,
      page: 1,
      totalPages: 1,
    );

    test('initial state is ProductsState()', () {
      expect(bloc.state, const ProductsState());
    });

    group('LoadProducts', () {
      blocTest<ProductsBloc, ProductsState>(
        'emits [loading, loaded] when getProducts succeeds',
        build: () {
          when(() => mockGetProducts(any()))
              .thenAnswer((_) async => Right(testPaginated));
          return bloc;
        },
        act: (bloc) => bloc.add(const ProductsEvent.load()),
        expect: () => [
          const ProductsState(isLoading: true),
          ProductsState(
            products: testProducts,
            hasReachedMax: true,
          ),
        ],
        verify: (_) {
          verify(() => mockGetProducts(any())).called(1);
        },
      );

      blocTest<ProductsBloc, ProductsState>(
        'emits [loading, error] when getProducts fails',
        build: () {
          when(() => mockGetProducts(any())).thenAnswer(
            (_) async => const Left(ServerFailure('Server error')),
          );
          return bloc;
        },
        act: (bloc) => bloc.add(const ProductsEvent.load()),
        expect: () => [
          const ProductsState(isLoading: true),
          const ProductsState(error: 'Server error'),
        ],
      );
    });

    group('LoadMoreProducts', () {
      blocTest<ProductsBloc, ProductsState>(
        'emits [loadingMore, loaded with more items] on success',
        build: () {
          when(() => mockGetProducts(any()))
              .thenAnswer((_) async => Right(testPaginated));
          return bloc;
        },
        seed: () => ProductsState(
          products: testProducts,
          currentPage: 1,
        ),
        act: (bloc) => bloc.add(const ProductsEvent.loadMore()),
        expect: () => [
          ProductsState(
            products: testProducts,
            currentPage: 1,
            isLoadingMore: true,
          ),
          ProductsState(
            products: [...testProducts, ...testProducts],
            currentPage: 2,
            hasReachedMax: true,
          ),
        ],
      );

      blocTest<ProductsBloc, ProductsState>(
        'does nothing when hasReachedMax is true',
        build: () => bloc,
        seed: () => ProductsState(
          products: testProducts,
          hasReachedMax: true,
        ),
        act: (bloc) => bloc.add(const ProductsEvent.loadMore()),
        expect: () => [],
        verify: (_) {
          verifyNever(() => mockGetProducts(any()));
        },
      );
    });

    group('DeleteProduct', () {
      blocTest<ProductsBloc, ProductsState>(
        'removes product from list on success',
        build: () {
          when(() => mockDeleteProduct(any()))
              .thenAnswer((_) async => const Right(null));
          return bloc;
        },
        seed: () => ProductsState(products: testProducts),
        act: (bloc) => bloc.add(const ProductsEvent.delete('1')),
        expect: () => [
          ProductsState(products: [testProducts[1]]),
        ],
        verify: (_) {
          verify(() => mockDeleteProduct('1')).called(1);
        },
      );

      blocTest<ProductsBloc, ProductsState>(
        'emits error when delete fails',
        build: () {
          when(() => mockDeleteProduct(any())).thenAnswer(
            (_) async => const Left(ServerFailure('Delete failed')),
          );
          return bloc;
        },
        seed: () => ProductsState(products: testProducts),
        act: (bloc) => bloc.add(const ProductsEvent.delete('1')),
        expect: () => [
          ProductsState(
            products: testProducts,
            error: 'Delete failed',
          ),
        ],
      );
    });
  });
}
```

### Widget Test

```dart
// test/features/products/presentation/pages/products_page_test.dart
import 'package:bloc_test/bloc_test.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:app/features/products/presentation/bloc/products_bloc.dart';
import 'package:app/features/products/presentation/pages/products_page.dart';
import 'package:app/features/products/presentation/widgets/products_list.dart';
import 'package:app/features/products/presentation/widgets/products_empty.dart';

import '../../../../helpers/pump_app.dart';
import '../../../../fixtures/product_fixtures.dart';

class MockProductsBloc extends MockBloc<ProductsEvent, ProductsState>
    implements ProductsBloc {}

void main() {
  late MockProductsBloc mockBloc;

  setUp(() {
    mockBloc = MockProductsBloc();
  });

  Widget buildSubject() {
    return BlocProvider<ProductsBloc>.value(
      value: mockBloc,
      child: const ProductsView(),
    );
  }

  group('ProductsPage', () {
    testWidgets('shows loading indicator when loading', (tester) async {
      when(() => mockBloc.state).thenReturn(
        const ProductsState(isLoading: true),
      );

      await tester.pumpApp(buildSubject());

      expect(find.byType(CircularProgressIndicator), findsOneWidget);
    });

    testWidgets('shows ProductsList when products loaded', (tester) async {
      when(() => mockBloc.state).thenReturn(
        ProductsState(products: ProductFixtures.products),
      );

      await tester.pumpApp(buildSubject());

      expect(find.byType(ProductsList), findsOneWidget);
      expect(find.text('Product 1'), findsOneWidget);
      expect(find.text('Product 2'), findsOneWidget);
    });

    testWidgets('shows ProductsEmpty when no products', (tester) async {
      when(() => mockBloc.state).thenReturn(
        const ProductsState(products: []),
      );

      await tester.pumpApp(buildSubject());

      expect(find.byType(ProductsEmpty), findsOneWidget);
    });

    testWidgets('shows snackbar when error occurs', (tester) async {
      whenListen(
        mockBloc,
        Stream.fromIterable([
          const ProductsState(),
          const ProductsState(error: 'Something went wrong'),
        ]),
        initialState: const ProductsState(),
      );

      await tester.pumpApp(buildSubject());
      await tester.pump();

      expect(find.text('Something went wrong'), findsOneWidget);
    });

    testWidgets('triggers refresh on pull to refresh', (tester) async {
      when(() => mockBloc.state).thenReturn(
        ProductsState(products: ProductFixtures.products),
      );

      await tester.pumpApp(buildSubject());

      await tester.drag(
        find.byType(RefreshIndicator),
        const Offset(0, 300),
      );
      await tester.pumpAndSettle();

      verify(() => mockBloc.add(const ProductsEvent.refresh())).called(1);
    });
  });
}
```

### Test Helper

```dart
// test/helpers/pump_app.dart
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

extension PumpApp on WidgetTester {
  Future<void> pumpApp(Widget widget) async {
    await pumpWidget(
      MaterialApp(
        home: Scaffold(body: widget),
      ),
    );
  }

  Future<void> pumpAppWithRouter(Widget widget) async {
    await pumpWidget(
      MaterialApp.router(
        routerConfig: testRouter,
      ),
    );
  }
}
```

### Test Fixtures

```dart
// test/fixtures/product_fixtures.dart
import 'package:app/features/products/domain/entities/product.dart';

class ProductFixtures {
  static const products = [
    Product(id: '1', name: 'Product 1', price: 10.0),
    Product(id: '2', name: 'Product 2', price: 20.0),
  ];

  static const singleProduct = Product(
    id: '1',
    name: 'Test Product',
    description: 'Test description',
    price: 99.99,
    categoryId: 'cat-1',
  );
}
```

## Best Practices

1. **Use mocktail** - For cleaner mocking syntax
2. **bloc_test** - For testing BLoC state changes
3. **Test fixtures** - Centralize test data
4. **Pump helpers** - Simplify widget test setup
5. **Register fallbacks** - For nullable parameters
6. **Group tests** - Organize by feature/action
