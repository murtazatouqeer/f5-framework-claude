---
name: flutter-clean-architecture
description: Clean Architecture implementation in Flutter
applies_to: flutter
---

# Flutter Clean Architecture

## Overview

Clean Architecture separates code into layers with clear dependencies flowing inward. Inner layers don't know about outer layers.

## Layer Diagram

```
┌─────────────────────────────────────────┐
│           Presentation Layer            │
│  (BLoC, Pages, Widgets)                 │
├─────────────────────────────────────────┤
│             Domain Layer                │
│  (Entities, Use Cases, Repositories)    │
├─────────────────────────────────────────┤
│              Data Layer                 │
│  (Models, Data Sources, Repo Impl)      │
└─────────────────────────────────────────┘
```

## Domain Layer

The innermost layer containing business logic. No dependencies on other layers.

### Entities

```dart
// features/products/domain/entities/product.dart
import 'package:freezed_annotation/freezed_annotation.dart';

part 'product.freezed.dart';

@freezed
class Product with _$Product {
  const Product._();

  const factory Product({
    required String id,
    required String name,
    required String description,
    required double price,
    required String categoryId,
    String? imageUrl,
    @Default(true) bool isActive,
    DateTime? createdAt,
  }) = _Product;

  String get formattedPrice => '\$${price.toStringAsFixed(2)}';

  bool get hasImage => imageUrl != null && imageUrl!.isNotEmpty;
}
```

### Repository Interface

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

// Input DTOs for domain layer
class CreateProductInput {
  final String name;
  final String description;
  final double price;
  final String categoryId;
  final String? imageUrl;

  const CreateProductInput({
    required this.name,
    required this.description,
    required this.price,
    required this.categoryId,
    this.imageUrl,
  });

  Map<String, dynamic> toJson() => {
        'name': name,
        'description': description,
        'price': price,
        'category_id': categoryId,
        if (imageUrl != null) 'image_url': imageUrl,
      };
}

class UpdateProductInput {
  final String? name;
  final String? description;
  final double? price;
  final String? categoryId;
  final String? imageUrl;
  final bool? isActive;

  const UpdateProductInput({
    this.name,
    this.description,
    this.price,
    this.categoryId,
    this.imageUrl,
    this.isActive,
  });

  Map<String, dynamic> toJson() => {
        if (name != null) 'name': name,
        if (description != null) 'description': description,
        if (price != null) 'price': price,
        if (categoryId != null) 'category_id': categoryId,
        if (imageUrl != null) 'image_url': imageUrl,
        if (isActive != null) 'is_active': isActive,
      };
}
```

### Use Cases

```dart
// core/usecases/usecase.dart
import 'package:dartz/dartz.dart';
import '../errors/failures.dart';

abstract class UseCase<Type, Params> {
  Future<Either<Failure, Type>> call(Params params);
}

class NoParams {
  const NoParams();
}

// features/products/domain/usecases/get_products.dart
import 'package:dartz/dartz.dart';
import 'package:injectable/injectable.dart';
import '../../../../core/errors/failures.dart';
import '../../../../core/usecases/usecase.dart';
import '../../../../core/utils/paginated_list.dart';
import '../entities/product.dart';
import '../repositories/product_repository.dart';

@injectable
class GetProducts
    implements UseCase<PaginatedList<Product>, GetProductsParams> {
  final ProductRepository _repository;

  GetProducts(this._repository);

  @override
  Future<Either<Failure, PaginatedList<Product>>> call(
    GetProductsParams params,
  ) {
    return _repository.getProducts(
      page: params.page,
      limit: params.limit,
      search: params.search,
      categoryId: params.categoryId,
    );
  }
}

class GetProductsParams {
  final int page;
  final int limit;
  final String? search;
  final String? categoryId;

  const GetProductsParams({
    this.page = 1,
    this.limit = 20,
    this.search,
    this.categoryId,
  });
}

// features/products/domain/usecases/create_product.dart
@injectable
class CreateProduct implements UseCase<Product, CreateProductInput> {
  final ProductRepository _repository;

  CreateProduct(this._repository);

  @override
  Future<Either<Failure, Product>> call(CreateProductInput input) {
    return _repository.createProduct(input);
  }
}
```

## Data Layer

Implements domain interfaces. Handles data sources and transformations.

### Models

```dart
// features/products/data/models/product_model.dart
import 'package:freezed_annotation/freezed_annotation.dart';
import '../../domain/entities/product.dart';

part 'product_model.freezed.dart';
part 'product_model.g.dart';

@freezed
class ProductModel with _$ProductModel {
  const ProductModel._();

  const factory ProductModel({
    required String id,
    required String name,
    required String description,
    required double price,
    @JsonKey(name: 'category_id') required String categoryId,
    @JsonKey(name: 'image_url') String? imageUrl,
    @JsonKey(name: 'is_active') @Default(true) bool isActive,
    @JsonKey(name: 'created_at') DateTime? createdAt,
  }) = _ProductModel;

  factory ProductModel.fromJson(Map<String, dynamic> json) =>
      _$ProductModelFromJson(json);

  // Convert to domain entity
  Product toEntity() => Product(
        id: id,
        name: name,
        description: description,
        price: price,
        categoryId: categoryId,
        imageUrl: imageUrl,
        isActive: isActive,
        createdAt: createdAt,
      );

  // Create from domain entity
  factory ProductModel.fromEntity(Product entity) => ProductModel(
        id: entity.id,
        name: entity.name,
        description: entity.description,
        price: entity.price,
        categoryId: entity.categoryId,
        imageUrl: entity.imageUrl,
        isActive: entity.isActive,
        createdAt: entity.createdAt,
      );
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
      return _getRemoteProducts(page, limit, search, categoryId);
    } else {
      return _getCachedProducts();
    }
  }

  Future<Either<Failure, PaginatedList<Product>>> _getRemoteProducts(
    int page,
    int limit,
    String? search,
    String? categoryId,
  ) async {
    try {
      final response = await _remoteDataSource.getProducts(
        page: page,
        limit: limit,
        search: search,
        categoryId: categoryId,
      );

      final products = response.items.map((m) => m.toEntity()).toList();

      // Cache first page of unfiltered results
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
  }

  Future<Either<Failure, PaginatedList<Product>>> _getCachedProducts() async {
    try {
      final cached = await _localDataSource.getCachedProducts();
      return Right(PaginatedList(
        items: cached.map((m) => m.toEntity()).toList(),
        total: cached.length,
        page: 1,
        totalPages: 1,
      ));
    } on CacheException {
      return const Left(
        CacheFailure('No internet connection and no cached data'),
      );
    }
  }

  // ... other methods
}
```

## Presentation Layer

Handles UI and state management. Depends on domain layer only.

### BLoC

```dart
// features/products/presentation/bloc/products_bloc.dart
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:injectable/injectable.dart';
import '../../domain/usecases/get_products.dart';
import 'products_event.dart';
import 'products_state.dart';

@injectable
class ProductsBloc extends Bloc<ProductsEvent, ProductsState> {
  final GetProducts _getProducts;

  ProductsBloc({required GetProducts getProducts})
      : _getProducts = getProducts,
        super(const ProductsState()) {
    on<LoadProducts>(_onLoad);
  }

  Future<void> _onLoad(
    LoadProducts event,
    Emitter<ProductsState> emit,
  ) async {
    emit(state.copyWith(isLoading: true, error: null));

    final result = await _getProducts(GetProductsParams(page: event.page));

    result.fold(
      (failure) => emit(state.copyWith(
        isLoading: false,
        error: failure.message,
      )),
      (paginated) => emit(state.copyWith(
        isLoading: false,
        products: paginated.items,
      )),
    );
  }
}
```

## Error Handling

```dart
// core/errors/failures.dart
abstract class Failure {
  final String message;
  const Failure(this.message);
}

class ServerFailure extends Failure {
  const ServerFailure(super.message);
}

class CacheFailure extends Failure {
  const CacheFailure(super.message);
}

class NetworkFailure extends Failure {
  const NetworkFailure() : super('No internet connection');
}

class UnauthorizedFailure extends Failure {
  const UnauthorizedFailure() : super('Unauthorized');
}

class ValidationFailure extends Failure {
  final Map<String, List<String>> errors;
  const ValidationFailure(this.errors) : super('Validation failed');
}

// core/errors/exceptions.dart
class ServerException implements Exception {
  final String message;
  final int? statusCode;
  const ServerException(this.message, {this.statusCode});
}

class CacheException implements Exception {}

class UnauthorizedException implements Exception {}

class ValidationException implements Exception {
  final Map<String, List<String>> errors;
  const ValidationException(this.errors);
}
```

## Best Practices

1. **Dependency Rule** - Dependencies flow inward only
2. **Interface Segregation** - Define repository interfaces in domain
3. **Either Type** - Use dartz for functional error handling
4. **Freezed** - Use for immutable entities and models
5. **Injectable** - Use for automatic DI registration
6. **Separation** - Keep layers strictly separated
