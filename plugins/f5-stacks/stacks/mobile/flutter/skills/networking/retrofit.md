---
name: flutter-retrofit
description: Retrofit type-safe REST API client
applies_to: flutter
---

# Flutter Retrofit

## Overview

Retrofit is a type-safe HTTP client generator for Dart. It generates boilerplate code for API calls using annotations.

## Dependencies

```yaml
dependencies:
  dio: ^5.4.0
  retrofit: ^4.1.0
  json_annotation: ^4.8.1

dev_dependencies:
  retrofit_generator: ^8.1.0
  json_serializable: ^6.7.1
  build_runner: ^2.4.6
```

## Basic API Service

```dart
import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';

part 'product_api_service.g.dart';

@RestApi(baseUrl: 'https://api.example.com')
abstract class ProductApiService {
  factory ProductApiService(Dio dio, {String baseUrl}) = _ProductApiService;

  @GET('/products')
  Future<List<ProductModel>> getProducts();

  @GET('/products/{id}')
  Future<ProductModel> getProduct(@Path('id') String id);

  @POST('/products')
  Future<ProductModel> createProduct(@Body() CreateProductDto dto);

  @PUT('/products/{id}')
  Future<ProductModel> updateProduct(
    @Path('id') String id,
    @Body() UpdateProductDto dto,
  );

  @DELETE('/products/{id}')
  Future<void> deleteProduct(@Path('id') String id);
}
```

## Query Parameters

```dart
@RestApi()
abstract class ProductApiService {
  factory ProductApiService(Dio dio, {String baseUrl}) = _ProductApiService;

  // Single query parameter
  @GET('/products')
  Future<List<ProductModel>> searchProducts(@Query('q') String query);

  // Multiple query parameters
  @GET('/products')
  Future<PaginatedResponse<ProductModel>> getProducts({
    @Query('page') int page = 1,
    @Query('limit') int limit = 20,
    @Query('sort') String? sort,
    @Query('category') String? category,
  });

  // Query map for dynamic parameters
  @GET('/products')
  Future<List<ProductModel>> filterProducts(
    @Queries() Map<String, dynamic> filters,
  );
}
```

## Headers

```dart
@RestApi()
abstract class AuthApiService {
  factory AuthApiService(Dio dio, {String baseUrl}) = _AuthApiService;

  // Static headers
  @GET('/user')
  @Headers(<String, dynamic>{
    'Accept': 'application/json',
    'Cache-Control': 'no-cache',
  })
  Future<UserModel> getUser();

  // Dynamic header
  @GET('/protected-resource')
  Future<ResourceModel> getProtectedResource(
    @Header('Authorization') String token,
  );
}
```

## File Upload

```dart
@RestApi()
abstract class UploadApiService {
  factory UploadApiService(Dio dio, {String baseUrl}) = _UploadApiService;

  // Single file upload
  @POST('/upload')
  @MultiPart()
  Future<UploadResponse> uploadFile(
    @Part(name: 'file') File file,
  );

  // Multiple files upload
  @POST('/upload/multiple')
  @MultiPart()
  Future<UploadResponse> uploadFiles(
    @Part(name: 'files') List<File> files,
  );

  // File with additional data
  @POST('/upload/avatar')
  @MultiPart()
  Future<UploadResponse> uploadAvatar(
    @Part(name: 'avatar') File file,
    @Part(name: 'user_id') String userId,
    @Part(name: 'description') String? description,
  );
}
```

## Response Types

```dart
@RestApi()
abstract class ApiService {
  factory ApiService(Dio dio, {String baseUrl}) = _ApiService;

  // Direct model response
  @GET('/product/{id}')
  Future<ProductModel> getProduct(@Path('id') String id);

  // List response
  @GET('/products')
  Future<List<ProductModel>> getProducts();

  // Wrapped response
  @GET('/products')
  Future<ApiResponse<List<ProductModel>>> getProductsWrapped();

  // Raw response with headers
  @GET('/products')
  Future<HttpResponse<List<ProductModel>>> getProductsWithHeaders();

  // Void response
  @DELETE('/products/{id}')
  Future<void> deleteProduct(@Path('id') String id);

  // Stream response
  @GET('/download/{id}')
  @DioResponseType(ResponseType.stream)
  Future<HttpResponse<ResponseBody>> downloadFile(@Path('id') String id);
}
```

## Paginated Response

```dart
// Model
@JsonSerializable(genericArgumentFactories: true)
class PaginatedResponse<T> {
  final List<T> data;
  final int page;
  final int totalPages;
  final int totalItems;

  PaginatedResponse({
    required this.data,
    required this.page,
    required this.totalPages,
    required this.totalItems,
  });

  factory PaginatedResponse.fromJson(
    Map<String, dynamic> json,
    T Function(Object? json) fromJsonT,
  ) =>
      _$PaginatedResponseFromJson(json, fromJsonT);

  Map<String, dynamic> toJson(Object? Function(T value) toJsonT) =>
      _$PaginatedResponseToJson(this, toJsonT);
}

// API Service
@RestApi()
abstract class ProductApiService {
  factory ProductApiService(Dio dio, {String baseUrl}) = _ProductApiService;

  @GET('/products')
  Future<PaginatedResponse<ProductModel>> getProducts(
    @Query('page') int page,
    @Query('limit') int limit,
  );
}
```

## Error Handling

```dart
// Custom error response model
@JsonSerializable()
class ApiError {
  final String message;
  final String? code;
  final Map<String, List<String>>? errors;

  ApiError({
    required this.message,
    this.code,
    this.errors,
  });

  factory ApiError.fromJson(Map<String, dynamic> json) =>
      _$ApiErrorFromJson(json);
}

// Repository with error handling
class ProductRepository {
  final ProductApiService _apiService;

  ProductRepository(this._apiService);

  Future<Either<Failure, List<Product>>> getProducts() async {
    try {
      final models = await _apiService.getProducts();
      return Right(models.map((m) => m.toEntity()).toList());
    } on DioException catch (e) {
      return Left(_mapError(e));
    }
  }

  Failure _mapError(DioException e) {
    if (e.response != null) {
      try {
        final apiError = ApiError.fromJson(e.response!.data);
        return ServerFailure(apiError.message, code: apiError.code);
      } catch (_) {
        return ServerFailure('Unknown error occurred');
      }
    }

    switch (e.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        return NetworkFailure('Connection timeout');
      case DioExceptionType.connectionError:
        return NetworkFailure('No internet connection');
      default:
        return ServerFailure('Unknown error occurred');
    }
  }
}
```

## Complete API Service Example

```dart
import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';

part 'api_service.g.dart';

@RestApi()
abstract class ApiService {
  factory ApiService(Dio dio, {String baseUrl}) = _ApiService;

  // Auth
  @POST('/auth/login')
  Future<AuthResponse> login(@Body() LoginRequest request);

  @POST('/auth/register')
  Future<AuthResponse> register(@Body() RegisterRequest request);

  @POST('/auth/refresh')
  Future<AuthResponse> refreshToken(@Body() RefreshTokenRequest request);

  @POST('/auth/logout')
  Future<void> logout();

  // User
  @GET('/user')
  Future<UserModel> getCurrentUser();

  @PUT('/user')
  Future<UserModel> updateUser(@Body() UpdateUserRequest request);

  @POST('/user/avatar')
  @MultiPart()
  Future<UserModel> updateAvatar(@Part(name: 'avatar') File file);

  // Products
  @GET('/products')
  Future<PaginatedResponse<ProductModel>> getProducts({
    @Query('page') int page = 1,
    @Query('limit') int limit = 20,
    @Query('category') String? category,
    @Query('sort') String? sort,
  });

  @GET('/products/{id}')
  Future<ProductModel> getProduct(@Path('id') String id);

  @POST('/products')
  Future<ProductModel> createProduct(@Body() CreateProductRequest request);

  @PUT('/products/{id}')
  Future<ProductModel> updateProduct(
    @Path('id') String id,
    @Body() UpdateProductRequest request,
  );

  @DELETE('/products/{id}')
  Future<void> deleteProduct(@Path('id') String id);

  // Orders
  @GET('/orders')
  Future<PaginatedResponse<OrderModel>> getOrders({
    @Query('page') int page = 1,
    @Query('status') String? status,
  });

  @GET('/orders/{id}')
  Future<OrderModel> getOrder(@Path('id') String id);

  @POST('/orders')
  Future<OrderModel> createOrder(@Body() CreateOrderRequest request);

  @PUT('/orders/{id}/cancel')
  Future<OrderModel> cancelOrder(@Path('id') String id);
}
```

## Dependency Injection

```dart
// Using injectable
@module
abstract class ApiModule {
  @lazySingleton
  Dio dio(TokenStorage tokenStorage) {
    final dio = Dio(
      BaseOptions(
        baseUrl: Environment.apiBaseUrl,
        connectTimeout: const Duration(seconds: 30),
        receiveTimeout: const Duration(seconds: 30),
      ),
    );
    dio.interceptors.add(AuthInterceptor(tokenStorage, dio));
    return dio;
  }

  @lazySingleton
  ApiService apiService(Dio dio) => ApiService(dio);

  @lazySingleton
  ProductApiService productApiService(Dio dio) => ProductApiService(dio);
}

// Using Riverpod
@riverpod
ApiService apiService(ApiServiceRef ref) {
  final dio = ref.watch(dioProvider);
  return ApiService(dio);
}

@riverpod
ProductRepository productRepository(ProductRepositoryRef ref) {
  final apiService = ref.watch(apiServiceProvider);
  return ProductRepositoryImpl(apiService);
}
```

## Code Generation

Run build_runner to generate implementation:

```bash
# One-time generation
dart run build_runner build --delete-conflicting-outputs

# Watch for changes
dart run build_runner watch --delete-conflicting-outputs
```

## Testing

```dart
import 'package:mocktail/mocktail.dart';

class MockApiService extends Mock implements ApiService {}

void main() {
  late MockApiService mockApiService;
  late ProductRepository repository;

  setUp(() {
    mockApiService = MockApiService();
    repository = ProductRepositoryImpl(mockApiService);
  });

  test('getProducts returns products', () async {
    when(() => mockApiService.getProducts())
        .thenAnswer((_) async => [ProductModel.fixture()]);

    final result = await repository.getProducts();

    expect(result.isRight(), true);
    result.fold(
      (l) => fail('Expected Right'),
      (r) => expect(r.length, 1),
    );
  });

  test('getProducts returns failure on error', () async {
    when(() => mockApiService.getProducts()).thenThrow(
      DioException(
        requestOptions: RequestOptions(path: '/products'),
        type: DioExceptionType.connectionError,
      ),
    );

    final result = await repository.getProducts();

    expect(result.isLeft(), true);
  });
}
```

## Best Practices

1. **Use code generation** - Run build_runner after changes
2. **Type-safe responses** - Define models for all responses
3. **Centralized error handling** - Map errors in repository layer
4. **Proper annotations** - Use correct HTTP method annotations
5. **Document APIs** - Add comments to API methods
6. **Test with mocks** - Mock the API service for unit tests
