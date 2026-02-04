---
name: flutter-repository-generator
description: Generates Flutter repository with data sources
applies_to: flutter
---

# Flutter Repository Generator Agent

## Purpose

Generates repository implementations following clean architecture with remote and local data sources.

## Capabilities

- Generate repository interface (domain layer)
- Create repository implementation (data layer)
- Generate remote data source
- Generate local data source for caching
- Add proper error handling

## Input Requirements

| Field | Required | Description |
|-------|----------|-------------|
| `feature_name` | Yes | Feature/module name |
| `entity_name` | Yes | Domain entity name |
| `endpoints` | No | API endpoints configuration |
| `has_cache` | No | Whether to cache data locally |

## Generated Files

```
features/{feature}/
├── domain/
│   └── repositories/
│       └── {entity}_repository.dart
└── data/
    ├── datasources/
    │   ├── {entity}_remote_datasource.dart
    │   └── {entity}_local_datasource.dart
    └── repositories/
        └── {entity}_repository_impl.dart
```

## Example Usage

```yaml
feature_name: products
entity_name: product
endpoints:
  list: GET /products
  detail: GET /products/{id}
  create: POST /products
  update: PATCH /products/{id}
  delete: DELETE /products/{id}
has_cache: true
```

## Output Pattern

### Repository Interface (Domain)

```dart
// features/products/domain/repositories/product_repository.dart
import 'package:dartz/dartz.dart';
import '../../../../core/errors/failures.dart';
import '../../../../core/utils/paginated_list.dart';
import '../entities/product.dart';

abstract class ProductRepository {
  Future<Either<Failure, PaginatedList<Product>>> getProducts({
    int page = 1,
    int limit = 20,
    String? search,
    String? categoryId,
  });

  Future<Either<Failure, Product>> getProduct(String id);

  Future<Either<Failure, Product>> createProduct(CreateProductInput input);

  Future<Either<Failure, Product>> updateProduct(
    String id,
    UpdateProductInput input,
  );

  Future<Either<Failure, void>> deleteProduct(String id);
}
```

### Remote Data Source

```dart
// features/products/data/datasources/product_remote_datasource.dart
import 'package:injectable/injectable.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/utils/paginated_response.dart';
import '../models/product_model.dart';

abstract class ProductRemoteDataSource {
  Future<PaginatedResponse<ProductModel>> getProducts({
    int page = 1,
    int limit = 20,
    String? search,
    String? categoryId,
  });

  Future<ProductModel> getProduct(String id);
  Future<ProductModel> createProduct(Map<String, dynamic> data);
  Future<ProductModel> updateProduct(String id, Map<String, dynamic> data);
  Future<void> deleteProduct(String id);
}

@Injectable(as: ProductRemoteDataSource)
class ProductRemoteDataSourceImpl implements ProductRemoteDataSource {
  final ApiClient _client;

  ProductRemoteDataSourceImpl(this._client);

  @override
  Future<PaginatedResponse<ProductModel>> getProducts({
    int page = 1,
    int limit = 20,
    String? search,
    String? categoryId,
  }) async {
    final response = await _client.get(
      '/products',
      queryParameters: {
        'page': page,
        'limit': limit,
        if (search != null && search.isNotEmpty) 'search': search,
        if (categoryId != null) 'category_id': categoryId,
      },
    );

    return PaginatedResponse.fromJson(
      response.data,
      (json) => ProductModel.fromJson(json as Map<String, dynamic>),
    );
  }

  @override
  Future<ProductModel> getProduct(String id) async {
    final response = await _client.get('/products/$id');
    return ProductModel.fromJson(response.data);
  }

  @override
  Future<ProductModel> createProduct(Map<String, dynamic> data) async {
    final response = await _client.post('/products', data: data);
    return ProductModel.fromJson(response.data);
  }

  @override
  Future<ProductModel> updateProduct(
    String id,
    Map<String, dynamic> data,
  ) async {
    final response = await _client.patch('/products/$id', data: data);
    return ProductModel.fromJson(response.data);
  }

  @override
  Future<void> deleteProduct(String id) async {
    await _client.delete('/products/$id');
  }
}
```

### Local Data Source

```dart
// features/products/data/datasources/product_local_datasource.dart
import 'package:hive/hive.dart';
import 'package:injectable/injectable.dart';
import '../models/product_model.dart';

abstract class ProductLocalDataSource {
  Future<List<ProductModel>> getCachedProducts();
  Future<void> cacheProducts(List<ProductModel> products);
  Future<ProductModel?> getCachedProduct(String id);
  Future<void> cacheProduct(ProductModel product);
  Future<void> clearCache();
}

@Injectable(as: ProductLocalDataSource)
class ProductLocalDataSourceImpl implements ProductLocalDataSource {
  static const String _boxName = 'products_cache';

  Future<Box<Map>> get _box async => Hive.openBox<Map>(_boxName);

  @override
  Future<List<ProductModel>> getCachedProducts() async {
    final box = await _box;
    return box.values
        .map((json) => ProductModel.fromJson(Map<String, dynamic>.from(json)))
        .toList();
  }

  @override
  Future<void> cacheProducts(List<ProductModel> products) async {
    final box = await _box;
    await box.clear();
    for (final product in products) {
      await box.put(product.id, product.toJson());
    }
  }

  @override
  Future<ProductModel?> getCachedProduct(String id) async {
    final box = await _box;
    final json = box.get(id);
    if (json == null) return null;
    return ProductModel.fromJson(Map<String, dynamic>.from(json));
  }

  @override
  Future<void> cacheProduct(ProductModel product) async {
    final box = await _box;
    await box.put(product.id, product.toJson());
  }

  @override
  Future<void> clearCache() async {
    final box = await _box;
    await box.clear();
  }
}
```

### Repository Implementation

```dart
// features/products/data/repositories/product_repository_impl.dart
import 'package:dartz/dartz.dart';
import 'package:injectable/injectable.dart';
import '../../../../core/errors/exceptions.dart';
import '../../../../core/errors/failures.dart';
import '../../../../core/network/network_info.dart';
import '../../../../core/utils/paginated_list.dart';
import '../../domain/entities/product.dart';
import '../../domain/repositories/product_repository.dart';
import '../datasources/product_local_datasource.dart';
import '../datasources/product_remote_datasource.dart';

@Injectable(as: ProductRepository)
class ProductRepositoryImpl implements ProductRepository {
  final ProductRemoteDataSource _remoteDataSource;
  final ProductLocalDataSource _localDataSource;
  final NetworkInfo _networkInfo;

  ProductRepositoryImpl({
    required ProductRemoteDataSource remoteDataSource,
    required ProductLocalDataSource localDataSource,
    required NetworkInfo networkInfo,
  })  : _remoteDataSource = remoteDataSource,
        _localDataSource = localDataSource,
        _networkInfo = networkInfo;

  @override
  Future<Either<Failure, PaginatedList<Product>>> getProducts({
    int page = 1,
    int limit = 20,
    String? search,
    String? categoryId,
  }) async {
    if (await _networkInfo.isConnected) {
      try {
        final response = await _remoteDataSource.getProducts(
          page: page,
          limit: limit,
          search: search,
          categoryId: categoryId,
        );

        final products = response.items.map((m) => m.toEntity()).toList();

        // Cache first page
        if (page == 1 && search == null && categoryId == null) {
          await _localDataSource.cacheProducts(response.items);
        }

        return Right(PaginatedList(
          items: products,
          total: response.total,
          page: response.page,
          totalPages: response.totalPages,
        ));
      } on ServerException catch (e) {
        return Left(ServerFailure(e.message));
      } on UnauthorizedException {
        return const Left(UnauthorizedFailure());
      }
    } else {
      try {
        final cached = await _localDataSource.getCachedProducts();
        return Right(PaginatedList(
          items: cached.map((m) => m.toEntity()).toList(),
          total: cached.length,
          page: 1,
          totalPages: 1,
        ));
      } on CacheException {
        return const Left(CacheFailure('No cached data available'));
      }
    }
  }

  @override
  Future<Either<Failure, Product>> getProduct(String id) async {
    try {
      final model = await _remoteDataSource.getProduct(id);
      await _localDataSource.cacheProduct(model);
      return Right(model.toEntity());
    } on ServerException catch (e) {
      // Try cache fallback
      final cached = await _localDataSource.getCachedProduct(id);
      if (cached != null) {
        return Right(cached.toEntity());
      }
      return Left(ServerFailure(e.message));
    }
  }

  @override
  Future<Either<Failure, Product>> createProduct(
    CreateProductInput input,
  ) async {
    try {
      final model = await _remoteDataSource.createProduct(input.toJson());
      return Right(model.toEntity());
    } on ServerException catch (e) {
      return Left(ServerFailure(e.message));
    } on ValidationException catch (e) {
      return Left(ValidationFailure(e.errors));
    }
  }

  @override
  Future<Either<Failure, Product>> updateProduct(
    String id,
    UpdateProductInput input,
  ) async {
    try {
      final model = await _remoteDataSource.updateProduct(id, input.toJson());
      await _localDataSource.cacheProduct(model);
      return Right(model.toEntity());
    } on ServerException catch (e) {
      return Left(ServerFailure(e.message));
    }
  }

  @override
  Future<Either<Failure, void>> deleteProduct(String id) async {
    try {
      await _remoteDataSource.deleteProduct(id);
      return const Right(null);
    } on ServerException catch (e) {
      return Left(ServerFailure(e.message));
    }
  }
}
```

## Best Practices

1. **Either type** - Use dartz for functional error handling
2. **Network check** - Check connectivity before remote calls
3. **Cache fallback** - Return cached data when offline
4. **Specific exceptions** - Map to specific failures
5. **Injectable** - Use dependency injection
