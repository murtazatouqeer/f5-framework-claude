# Flutter CRUD App Example

Complete Flutter application demonstrating CRUD operations with Clean Architecture.

## Project Structure

```
lib/
├── core/
│   ├── di/
│   │   └── injection.dart
│   ├── error/
│   │   ├── exceptions.dart
│   │   └── failures.dart
│   ├── network/
│   │   ├── dio_client.dart
│   │   └── network_info.dart
│   └── theme/
│       └── app_theme.dart
├── features/
│   └── products/
│       ├── data/
│       │   ├── datasources/
│       │   │   ├── product_local_datasource.dart
│       │   │   └── product_remote_datasource.dart
│       │   ├── models/
│       │   │   └── product_model.dart
│       │   └── repositories/
│       │       └── product_repository_impl.dart
│       ├── domain/
│       │   ├── entities/
│       │   │   └── product.dart
│       │   ├── repositories/
│       │   │   └── product_repository.dart
│       │   └── usecases/
│       │       ├── create_product.dart
│       │       ├── delete_product.dart
│       │       ├── get_products.dart
│       │       └── update_product.dart
│       └── presentation/
│           ├── bloc/
│           │   ├── product_bloc.dart
│           │   ├── product_event.dart
│           │   └── product_state.dart
│           ├── screens/
│           │   ├── product_detail_screen.dart
│           │   ├── product_form_screen.dart
│           │   └── product_list_screen.dart
│           └── widgets/
│               ├── product_card.dart
│               └── product_form.dart
├── app.dart
└── main.dart
```

## Dependencies

```yaml
# pubspec.yaml
name: crud_app
description: Flutter CRUD App Example

environment:
  sdk: '>=3.2.0 <4.0.0'
  flutter: '>=3.16.0'

dependencies:
  flutter:
    sdk: flutter
  flutter_bloc: ^8.1.3
  freezed_annotation: ^2.4.1
  json_annotation: ^4.8.1
  dartz: ^0.10.1
  dio: ^5.4.0
  get_it: ^7.6.4
  injectable: ^2.3.2
  hive_flutter: ^1.1.0
  connectivity_plus: ^5.0.2
  go_router: ^13.0.0
  cached_network_image: ^3.3.1

dev_dependencies:
  flutter_test:
    sdk: flutter
  build_runner: ^2.4.7
  freezed: ^2.4.5
  json_serializable: ^6.7.1
  injectable_generator: ^2.4.1
  hive_generator: ^2.0.1
  bloc_test: ^9.1.5
  mocktail: ^1.0.1
```

## Core Layer

### Dependency Injection

```dart
// lib/core/di/injection.dart
import 'package:get_it/get_it.dart';
import 'package:injectable/injectable.dart';
import 'package:dio/dio.dart';
import 'package:hive_flutter/hive_flutter.dart';

import '../../features/products/data/models/product_model.dart';

final getIt = GetIt.instance;

@InjectableInit()
Future<void> configureDependencies() async {
  // Initialize Hive
  await Hive.initFlutter();
  Hive.registerAdapter(ProductModelAdapter());

  final productBox = await Hive.openBox<ProductModel>('products');
  getIt.registerSingleton<Box<ProductModel>>(productBox);

  // Register Dio
  final dio = Dio(BaseOptions(
    baseUrl: 'https://api.example.com',
    connectTimeout: const Duration(seconds: 10),
    receiveTimeout: const Duration(seconds: 10),
  ));
  getIt.registerSingleton<Dio>(dio);

  // Initialize generated dependencies
  getIt.init();
}
```

### Error Handling

```dart
// lib/core/error/failures.dart
import 'package:freezed_annotation/freezed_annotation.dart';

part 'failures.freezed.dart';

@freezed
class Failure with _$Failure {
  const factory Failure.server({required String message}) = ServerFailure;
  const factory Failure.cache({required String message}) = CacheFailure;
  const factory Failure.network({required String message}) = NetworkFailure;
  const factory Failure.validation({
    required String message,
    @Default({}) Map<String, List<String>> errors,
  }) = ValidationFailure;
}

// lib/core/error/exceptions.dart
import 'package:dio/dio.dart';

class ServerException implements Exception {
  final String message;
  final int? statusCode;

  ServerException({required this.message, this.statusCode});

  factory ServerException.fromDioError(DioException error) {
    return ServerException(
      message: error.response?.data?['message'] ?? 'Server error',
      statusCode: error.response?.statusCode,
    );
  }
}

class CacheException implements Exception {}
```

## Domain Layer

### Entity

```dart
// lib/features/products/domain/entities/product.dart
import 'package:freezed_annotation/freezed_annotation.dart';

part 'product.freezed.dart';

@freezed
class Product with _$Product {
  const factory Product({
    required String id,
    required String name,
    String? description,
    required double price,
    String? imageUrl,
    required DateTime createdAt,
    DateTime? updatedAt,
  }) = _Product;

  const Product._();

  String get formattedPrice => '\$${price.toStringAsFixed(2)}';
}
```

### Repository Interface

```dart
// lib/features/products/domain/repositories/product_repository.dart
import 'package:dartz/dartz.dart';

import '../../../../core/error/failures.dart';
import '../entities/product.dart';

abstract class ProductRepository {
  Future<Either<Failure, List<Product>>> getProducts();
  Future<Either<Failure, Product>> getProductById(String id);
  Future<Either<Failure, Product>> createProduct(Product product);
  Future<Either<Failure, Product>> updateProduct(Product product);
  Future<Either<Failure, void>> deleteProduct(String id);
}
```

### Use Cases

```dart
// lib/features/products/domain/usecases/get_products.dart
import 'package:dartz/dartz.dart';
import 'package:injectable/injectable.dart';

import '../../../../core/error/failures.dart';
import '../entities/product.dart';
import '../repositories/product_repository.dart';

@injectable
class GetProducts {
  final ProductRepository _repository;

  GetProducts(this._repository);

  Future<Either<Failure, List<Product>>> call() => _repository.getProducts();
}

// lib/features/products/domain/usecases/create_product.dart
@injectable
class CreateProduct {
  final ProductRepository _repository;

  CreateProduct(this._repository);

  Future<Either<Failure, Product>> call(Product product) =>
      _repository.createProduct(product);
}

// lib/features/products/domain/usecases/update_product.dart
@injectable
class UpdateProduct {
  final ProductRepository _repository;

  UpdateProduct(this._repository);

  Future<Either<Failure, Product>> call(Product product) =>
      _repository.updateProduct(product);
}

// lib/features/products/domain/usecases/delete_product.dart
@injectable
class DeleteProduct {
  final ProductRepository _repository;

  DeleteProduct(this._repository);

  Future<Either<Failure, void>> call(String id) =>
      _repository.deleteProduct(id);
}
```

## Data Layer

### Model

```dart
// lib/features/products/data/models/product_model.dart
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:hive/hive.dart';

import '../../domain/entities/product.dart';

part 'product_model.freezed.dart';
part 'product_model.g.dart';

@freezed
@HiveType(typeId: 1)
class ProductModel with _$ProductModel {
  const factory ProductModel({
    @HiveField(0) required String id,
    @HiveField(1) required String name,
    @HiveField(2) String? description,
    @HiveField(3) required double price,
    @HiveField(4) @JsonKey(name: 'image_url') String? imageUrl,
    @HiveField(5) @JsonKey(name: 'created_at') required DateTime createdAt,
    @HiveField(6) @JsonKey(name: 'updated_at') DateTime? updatedAt,
  }) = _ProductModel;

  const ProductModel._();

  factory ProductModel.fromJson(Map<String, dynamic> json) =>
      _$ProductModelFromJson(json);

  Product toEntity() => Product(
        id: id,
        name: name,
        description: description,
        price: price,
        imageUrl: imageUrl,
        createdAt: createdAt,
        updatedAt: updatedAt,
      );

  factory ProductModel.fromEntity(Product entity) => ProductModel(
        id: entity.id,
        name: entity.name,
        description: entity.description,
        price: entity.price,
        imageUrl: entity.imageUrl,
        createdAt: entity.createdAt,
        updatedAt: entity.updatedAt,
      );
}
```

### Data Sources

```dart
// lib/features/products/data/datasources/product_remote_datasource.dart
import 'package:dio/dio.dart';
import 'package:injectable/injectable.dart';

import '../../../../core/error/exceptions.dart';
import '../models/product_model.dart';

abstract class ProductRemoteDataSource {
  Future<List<ProductModel>> getProducts();
  Future<ProductModel> getProductById(String id);
  Future<ProductModel> createProduct(ProductModel model);
  Future<ProductModel> updateProduct(ProductModel model);
  Future<void> deleteProduct(String id);
}

@LazySingleton(as: ProductRemoteDataSource)
class ProductRemoteDataSourceImpl implements ProductRemoteDataSource {
  final Dio _dio;
  static const _basePath = '/products';

  ProductRemoteDataSourceImpl(this._dio);

  @override
  Future<List<ProductModel>> getProducts() async {
    try {
      final response = await _dio.get(_basePath);
      return (response.data['data'] as List)
          .map((json) => ProductModel.fromJson(json))
          .toList();
    } on DioException catch (e) {
      throw ServerException.fromDioError(e);
    }
  }

  @override
  Future<ProductModel> getProductById(String id) async {
    try {
      final response = await _dio.get('$_basePath/$id');
      return ProductModel.fromJson(response.data['data']);
    } on DioException catch (e) {
      throw ServerException.fromDioError(e);
    }
  }

  @override
  Future<ProductModel> createProduct(ProductModel model) async {
    try {
      final response = await _dio.post(_basePath, data: model.toJson());
      return ProductModel.fromJson(response.data['data']);
    } on DioException catch (e) {
      throw ServerException.fromDioError(e);
    }
  }

  @override
  Future<ProductModel> updateProduct(ProductModel model) async {
    try {
      final response = await _dio.put(
        '$_basePath/${model.id}',
        data: model.toJson(),
      );
      return ProductModel.fromJson(response.data['data']);
    } on DioException catch (e) {
      throw ServerException.fromDioError(e);
    }
  }

  @override
  Future<void> deleteProduct(String id) async {
    try {
      await _dio.delete('$_basePath/$id');
    } on DioException catch (e) {
      throw ServerException.fromDioError(e);
    }
  }
}

// lib/features/products/data/datasources/product_local_datasource.dart
import 'package:hive/hive.dart';
import 'package:injectable/injectable.dart';

import '../../../../core/error/exceptions.dart';
import '../models/product_model.dart';

abstract class ProductLocalDataSource {
  Future<List<ProductModel>> getProducts();
  Future<ProductModel> getProductById(String id);
  Future<void> cacheProducts(List<ProductModel> models);
  Future<void> cacheProduct(ProductModel model);
  Future<void> deleteProduct(String id);
}

@LazySingleton(as: ProductLocalDataSource)
class ProductLocalDataSourceImpl implements ProductLocalDataSource {
  final Box<ProductModel> _box;

  ProductLocalDataSourceImpl(this._box);

  @override
  Future<List<ProductModel>> getProducts() async {
    if (_box.isEmpty) throw CacheException();
    return _box.values.toList();
  }

  @override
  Future<ProductModel> getProductById(String id) async {
    final model = _box.get(id);
    if (model == null) throw CacheException();
    return model;
  }

  @override
  Future<void> cacheProducts(List<ProductModel> models) async {
    final entries = {for (var m in models) m.id: m};
    await _box.putAll(entries);
  }

  @override
  Future<void> cacheProduct(ProductModel model) async {
    await _box.put(model.id, model);
  }

  @override
  Future<void> deleteProduct(String id) async {
    await _box.delete(id);
  }
}
```

### Repository Implementation

```dart
// lib/features/products/data/repositories/product_repository_impl.dart
import 'package:dartz/dartz.dart';
import 'package:injectable/injectable.dart';

import '../../../../core/error/exceptions.dart';
import '../../../../core/error/failures.dart';
import '../../../../core/network/network_info.dart';
import '../../domain/entities/product.dart';
import '../../domain/repositories/product_repository.dart';
import '../datasources/product_local_datasource.dart';
import '../datasources/product_remote_datasource.dart';
import '../models/product_model.dart';

@LazySingleton(as: ProductRepository)
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
  Future<Either<Failure, List<Product>>> getProducts() async {
    if (await _networkInfo.isConnected) {
      try {
        final models = await _remoteDataSource.getProducts();
        await _localDataSource.cacheProducts(models);
        return Right(models.map((m) => m.toEntity()).toList());
      } on ServerException catch (e) {
        return Left(ServerFailure(message: e.message));
      }
    } else {
      try {
        final models = await _localDataSource.getProducts();
        return Right(models.map((m) => m.toEntity()).toList());
      } on CacheException {
        return const Left(CacheFailure(message: 'No cached data'));
      }
    }
  }

  @override
  Future<Either<Failure, Product>> getProductById(String id) async {
    try {
      final model = await _remoteDataSource.getProductById(id);
      await _localDataSource.cacheProduct(model);
      return Right(model.toEntity());
    } on ServerException catch (e) {
      return Left(ServerFailure(message: e.message));
    }
  }

  @override
  Future<Either<Failure, Product>> createProduct(Product product) async {
    try {
      final model = ProductModel.fromEntity(product);
      final result = await _remoteDataSource.createProduct(model);
      await _localDataSource.cacheProduct(result);
      return Right(result.toEntity());
    } on ServerException catch (e) {
      return Left(ServerFailure(message: e.message));
    }
  }

  @override
  Future<Either<Failure, Product>> updateProduct(Product product) async {
    try {
      final model = ProductModel.fromEntity(product);
      final result = await _remoteDataSource.updateProduct(model);
      await _localDataSource.cacheProduct(result);
      return Right(result.toEntity());
    } on ServerException catch (e) {
      return Left(ServerFailure(message: e.message));
    }
  }

  @override
  Future<Either<Failure, void>> deleteProduct(String id) async {
    try {
      await _remoteDataSource.deleteProduct(id);
      await _localDataSource.deleteProduct(id);
      return const Right(null);
    } on ServerException catch (e) {
      return Left(ServerFailure(message: e.message));
    }
  }
}
```

## Presentation Layer

### BLoC

```dart
// lib/features/products/presentation/bloc/product_bloc.dart
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:injectable/injectable.dart';

import '../../domain/entities/product.dart';
import '../../domain/usecases/create_product.dart';
import '../../domain/usecases/delete_product.dart';
import '../../domain/usecases/get_products.dart';
import '../../domain/usecases/update_product.dart';

part 'product_bloc.freezed.dart';
part 'product_event.dart';
part 'product_state.dart';

@injectable
class ProductBloc extends Bloc<ProductEvent, ProductState> {
  final GetProducts _getProducts;
  final CreateProduct _createProduct;
  final UpdateProduct _updateProduct;
  final DeleteProduct _deleteProduct;

  ProductBloc({
    required GetProducts getProducts,
    required CreateProduct createProduct,
    required UpdateProduct updateProduct,
    required DeleteProduct deleteProduct,
  })  : _getProducts = getProducts,
        _createProduct = createProduct,
        _updateProduct = updateProduct,
        _deleteProduct = deleteProduct,
        super(const ProductState.initial()) {
    on<ProductFetched>(_onFetched);
    on<ProductCreated>(_onCreated);
    on<ProductUpdated>(_onUpdated);
    on<ProductDeleted>(_onDeleted);
  }

  Future<void> _onFetched(
    ProductFetched event,
    Emitter<ProductState> emit,
  ) async {
    emit(const ProductState.loading());
    final result = await _getProducts();
    result.fold(
      (failure) => emit(ProductState.error(failure.toString())),
      (products) => emit(ProductState.loaded(products)),
    );
  }

  Future<void> _onCreated(
    ProductCreated event,
    Emitter<ProductState> emit,
  ) async {
    final currentState = state;
    emit(const ProductState.loading());
    final result = await _createProduct(event.product);
    result.fold(
      (failure) => emit(ProductState.error(failure.toString())),
      (product) {
        if (currentState is ProductLoaded) {
          emit(ProductState.loaded([...currentState.products, product]));
        } else {
          emit(ProductState.loaded([product]));
        }
      },
    );
  }

  Future<void> _onUpdated(
    ProductUpdated event,
    Emitter<ProductState> emit,
  ) async {
    final currentState = state;
    emit(const ProductState.loading());
    final result = await _updateProduct(event.product);
    result.fold(
      (failure) => emit(ProductState.error(failure.toString())),
      (updatedProduct) {
        if (currentState is ProductLoaded) {
          final products = currentState.products.map((p) {
            return p.id == updatedProduct.id ? updatedProduct : p;
          }).toList();
          emit(ProductState.loaded(products));
        }
      },
    );
  }

  Future<void> _onDeleted(
    ProductDeleted event,
    Emitter<ProductState> emit,
  ) async {
    final currentState = state;
    final result = await _deleteProduct(event.id);
    result.fold(
      (failure) => emit(ProductState.error(failure.toString())),
      (_) {
        if (currentState is ProductLoaded) {
          final products =
              currentState.products.where((p) => p.id != event.id).toList();
          emit(ProductState.loaded(products));
        }
      },
    );
  }
}

// lib/features/products/presentation/bloc/product_event.dart
part of 'product_bloc.dart';

@freezed
class ProductEvent with _$ProductEvent {
  const factory ProductEvent.fetched() = ProductFetched;
  const factory ProductEvent.created(Product product) = ProductCreated;
  const factory ProductEvent.updated(Product product) = ProductUpdated;
  const factory ProductEvent.deleted(String id) = ProductDeleted;
}

// lib/features/products/presentation/bloc/product_state.dart
part of 'product_bloc.dart';

@freezed
class ProductState with _$ProductState {
  const factory ProductState.initial() = ProductInitial;
  const factory ProductState.loading() = ProductLoading;
  const factory ProductState.loaded(List<Product> products) = ProductLoaded;
  const factory ProductState.error(String message) = ProductError;
}
```

### Screens

```dart
// lib/features/products/presentation/screens/product_list_screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../bloc/product_bloc.dart';
import '../widgets/product_card.dart';

class ProductListScreen extends StatelessWidget {
  const ProductListScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Products'),
        actions: [
          IconButton(
            icon: const Icon(Icons.add),
            onPressed: () => context.push('/products/create'),
          ),
        ],
      ),
      body: BlocBuilder<ProductBloc, ProductState>(
        builder: (context, state) {
          return state.when(
            initial: () {
              context.read<ProductBloc>().add(const ProductFetched());
              return const SizedBox.shrink();
            },
            loading: () => const Center(
              child: CircularProgressIndicator(),
            ),
            loaded: (products) {
              if (products.isEmpty) {
                return const Center(
                  child: Text('No products found'),
                );
              }
              return RefreshIndicator(
                onRefresh: () async {
                  context.read<ProductBloc>().add(const ProductFetched());
                },
                child: ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: products.length,
                  itemBuilder: (context, index) {
                    return ProductCard(
                      product: products[index],
                      onTap: () => context.push(
                        '/products/${products[index].id}',
                      ),
                      onDelete: () {
                        context.read<ProductBloc>().add(
                              ProductDeleted(products[index].id),
                            );
                      },
                    );
                  },
                ),
              );
            },
            error: (message) => Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(message),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () {
                      context.read<ProductBloc>().add(const ProductFetched());
                    },
                    child: const Text('Retry'),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}

// lib/features/products/presentation/screens/product_form_screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:uuid/uuid.dart';

import '../../domain/entities/product.dart';
import '../bloc/product_bloc.dart';

class ProductFormScreen extends StatefulWidget {
  final Product? product;

  const ProductFormScreen({super.key, this.product});

  @override
  State<ProductFormScreen> createState() => _ProductFormScreenState();
}

class _ProductFormScreenState extends State<ProductFormScreen> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _nameController;
  late final TextEditingController _descriptionController;
  late final TextEditingController _priceController;

  bool get isEditing => widget.product != null;

  @override
  void initState() {
    super.initState();
    _nameController = TextEditingController(text: widget.product?.name);
    _descriptionController = TextEditingController(
      text: widget.product?.description,
    );
    _priceController = TextEditingController(
      text: widget.product?.price.toString(),
    );
  }

  @override
  void dispose() {
    _nameController.dispose();
    _descriptionController.dispose();
    _priceController.dispose();
    super.dispose();
  }

  void _submit() {
    if (!_formKey.currentState!.validate()) return;

    final product = Product(
      id: widget.product?.id ?? const Uuid().v4(),
      name: _nameController.text,
      description: _descriptionController.text,
      price: double.parse(_priceController.text),
      createdAt: widget.product?.createdAt ?? DateTime.now(),
      updatedAt: isEditing ? DateTime.now() : null,
    );

    if (isEditing) {
      context.read<ProductBloc>().add(ProductUpdated(product));
    } else {
      context.read<ProductBloc>().add(ProductCreated(product));
    }

    context.pop();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(isEditing ? 'Edit Product' : 'Create Product'),
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            TextFormField(
              controller: _nameController,
              decoration: const InputDecoration(
                labelText: 'Name',
                border: OutlineInputBorder(),
              ),
              validator: (value) {
                if (value == null || value.isEmpty) {
                  return 'Name is required';
                }
                return null;
              },
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _descriptionController,
              decoration: const InputDecoration(
                labelText: 'Description',
                border: OutlineInputBorder(),
              ),
              maxLines: 3,
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _priceController,
              decoration: const InputDecoration(
                labelText: 'Price',
                border: OutlineInputBorder(),
                prefixText: '\$ ',
              ),
              keyboardType: TextInputType.number,
              validator: (value) {
                if (value == null || value.isEmpty) {
                  return 'Price is required';
                }
                if (double.tryParse(value) == null) {
                  return 'Enter a valid number';
                }
                return null;
              },
            ),
            const SizedBox(height: 24),
            FilledButton(
              onPressed: _submit,
              child: Text(isEditing ? 'Update' : 'Create'),
            ),
          ],
        ),
      ),
    );
  }
}
```

### Widgets

```dart
// lib/features/products/presentation/widgets/product_card.dart
import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';

import '../../domain/entities/product.dart';

class ProductCard extends StatelessWidget {
  final Product product;
  final VoidCallback? onTap;
  final VoidCallback? onDelete;

  const ProductCard({
    super.key,
    required this.product,
    this.onTap,
    this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Row(
            children: [
              ClipRRect(
                borderRadius: BorderRadius.circular(8),
                child: product.imageUrl != null
                    ? CachedNetworkImage(
                        imageUrl: product.imageUrl!,
                        width: 80,
                        height: 80,
                        fit: BoxFit.cover,
                        placeholder: (_, __) => Container(
                          width: 80,
                          height: 80,
                          color: Colors.grey[200],
                          child: const Icon(Icons.image),
                        ),
                      )
                    : Container(
                        width: 80,
                        height: 80,
                        color: Colors.grey[200],
                        child: const Icon(Icons.image),
                      ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      product.name,
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    if (product.description != null) ...[
                      const SizedBox(height: 4),
                      Text(
                        product.description!,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ],
                    const SizedBox(height: 8),
                    Text(
                      product.formattedPrice,
                      style: Theme.of(context).textTheme.titleSmall?.copyWith(
                            color: Theme.of(context).colorScheme.primary,
                            fontWeight: FontWeight.bold,
                          ),
                    ),
                  ],
                ),
              ),
              IconButton(
                icon: const Icon(Icons.delete_outline),
                onPressed: () {
                  showDialog(
                    context: context,
                    builder: (context) => AlertDialog(
                      title: const Text('Delete Product'),
                      content: const Text(
                        'Are you sure you want to delete this product?',
                      ),
                      actions: [
                        TextButton(
                          onPressed: () => Navigator.pop(context),
                          child: const Text('Cancel'),
                        ),
                        TextButton(
                          onPressed: () {
                            Navigator.pop(context);
                            onDelete?.call();
                          },
                          child: const Text('Delete'),
                        ),
                      ],
                    ),
                  );
                },
              ),
            ],
          ),
        ),
      ),
    );
  }
}
```

## Router Configuration

```dart
// lib/app.dart
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import 'core/di/injection.dart';
import 'features/products/presentation/bloc/product_bloc.dart';
import 'features/products/presentation/screens/product_form_screen.dart';
import 'features/products/presentation/screens/product_list_screen.dart';

final _router = GoRouter(
  routes: [
    GoRoute(
      path: '/',
      redirect: (_, __) => '/products',
    ),
    GoRoute(
      path: '/products',
      builder: (context, state) => const ProductListScreen(),
      routes: [
        GoRoute(
          path: 'create',
          builder: (context, state) => const ProductFormScreen(),
        ),
        GoRoute(
          path: ':id',
          builder: (context, state) {
            final id = state.pathParameters['id']!;
            // Fetch product by id for editing
            return ProductFormScreen(product: null); // Pass actual product
          },
        ),
      ],
    ),
  ],
);

class App extends StatelessWidget {
  const App({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiBlocProvider(
      providers: [
        BlocProvider(
          create: (_) => getIt<ProductBloc>()..add(const ProductFetched()),
        ),
      ],
      child: MaterialApp.router(
        title: 'CRUD App',
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
          useMaterial3: true,
        ),
        routerConfig: _router,
      ),
    );
  }
}
```

## Main Entry Point

```dart
// lib/main.dart
import 'package:flutter/material.dart';

import 'app.dart';
import 'core/di/injection.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await configureDependencies();
  runApp(const App());
}
```

## Testing

```dart
// test/features/products/presentation/bloc/product_bloc_test.dart
import 'package:bloc_test/bloc_test.dart';
import 'package:dartz/dartz.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:crud_app/core/error/failures.dart';
import 'package:crud_app/features/products/domain/entities/product.dart';
import 'package:crud_app/features/products/domain/usecases/create_product.dart';
import 'package:crud_app/features/products/domain/usecases/delete_product.dart';
import 'package:crud_app/features/products/domain/usecases/get_products.dart';
import 'package:crud_app/features/products/domain/usecases/update_product.dart';
import 'package:crud_app/features/products/presentation/bloc/product_bloc.dart';

class MockGetProducts extends Mock implements GetProducts {}
class MockCreateProduct extends Mock implements CreateProduct {}
class MockUpdateProduct extends Mock implements UpdateProduct {}
class MockDeleteProduct extends Mock implements DeleteProduct {}

void main() {
  late ProductBloc bloc;
  late MockGetProducts mockGetProducts;
  late MockCreateProduct mockCreateProduct;
  late MockUpdateProduct mockUpdateProduct;
  late MockDeleteProduct mockDeleteProduct;

  setUp(() {
    mockGetProducts = MockGetProducts();
    mockCreateProduct = MockCreateProduct();
    mockUpdateProduct = MockUpdateProduct();
    mockDeleteProduct = MockDeleteProduct();
    bloc = ProductBloc(
      getProducts: mockGetProducts,
      createProduct: mockCreateProduct,
      updateProduct: mockUpdateProduct,
      deleteProduct: mockDeleteProduct,
    );
  });

  tearDown(() => bloc.close());

  final tProduct = Product(
    id: '1',
    name: 'Test Product',
    price: 9.99,
    createdAt: DateTime.now(),
  );

  group('ProductFetched', () {
    blocTest<ProductBloc, ProductState>(
      'emits [loading, loaded] when fetch succeeds',
      build: () {
        when(() => mockGetProducts())
            .thenAnswer((_) async => Right([tProduct]));
        return bloc;
      },
      act: (bloc) => bloc.add(const ProductFetched()),
      expect: () => [
        const ProductLoading(),
        ProductLoaded([tProduct]),
      ],
      verify: (_) => verify(() => mockGetProducts()).called(1),
    );

    blocTest<ProductBloc, ProductState>(
      'emits [loading, error] when fetch fails',
      build: () {
        when(() => mockGetProducts()).thenAnswer(
          (_) async => const Left(ServerFailure(message: 'Server error')),
        );
        return bloc;
      },
      act: (bloc) => bloc.add(const ProductFetched()),
      expect: () => [
        const ProductLoading(),
        isA<ProductError>(),
      ],
    );
  });

  group('ProductCreated', () {
    blocTest<ProductBloc, ProductState>(
      'emits [loading, loaded] when create succeeds',
      build: () {
        when(() => mockCreateProduct(tProduct))
            .thenAnswer((_) async => Right(tProduct));
        return bloc;
      },
      act: (bloc) => bloc.add(ProductCreated(tProduct)),
      expect: () => [
        const ProductLoading(),
        ProductLoaded([tProduct]),
      ],
    );
  });

  group('ProductDeleted', () {
    blocTest<ProductBloc, ProductState>(
      'removes product from list when delete succeeds',
      build: () {
        when(() => mockDeleteProduct('1'))
            .thenAnswer((_) async => const Right(null));
        return bloc;
      },
      seed: () => ProductLoaded([tProduct]),
      act: (bloc) => bloc.add(const ProductDeleted('1')),
      expect: () => [const ProductLoaded([])],
    );
  });
}
```

## Running the App

```bash
# Generate code
dart run build_runner build --delete-conflicting-outputs

# Run app
flutter run

# Run tests
flutter test

# Run with coverage
flutter test --coverage
```
