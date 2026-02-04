---
name: flutter-network-error-handling
description: Network error handling patterns in Flutter
applies_to: flutter
---

# Flutter Network Error Handling

## Overview

Proper error handling improves user experience and makes debugging easier. Use typed errors and the Either pattern for predictable error flow.

## Dependencies

```yaml
dependencies:
  dartz: ^0.10.1  # For Either type
  dio: ^5.4.0
```

## Failure Classes

```dart
import 'package:freezed_annotation/freezed_annotation.dart';

part 'failure.freezed.dart';

@freezed
class Failure with _$Failure {
  // Network-related failures
  const factory Failure.network({
    @Default('Network error occurred') String message,
  }) = NetworkFailure;

  const factory Failure.timeout({
    @Default('Request timed out') String message,
  }) = TimeoutFailure;

  const factory Failure.noConnection({
    @Default('No internet connection') String message,
  }) = NoConnectionFailure;

  // Server-related failures
  const factory Failure.server({
    required String message,
    String? code,
    int? statusCode,
  }) = ServerFailure;

  const factory Failure.unauthorized({
    @Default('Authentication required') String message,
  }) = UnauthorizedFailure;

  const factory Failure.forbidden({
    @Default('Access denied') String message,
  }) = ForbiddenFailure;

  const factory Failure.notFound({
    @Default('Resource not found') String message,
  }) = NotFoundFailure;

  const factory Failure.validation({
    required String message,
    Map<String, List<String>>? errors,
  }) = ValidationFailure;

  // Client-related failures
  const factory Failure.cache({
    @Default('Cache error') String message,
  }) = CacheFailure;

  const factory Failure.parse({
    @Default('Failed to parse response') String message,
  }) = ParseFailure;

  const factory Failure.unknown({
    @Default('An unknown error occurred') String message,
  }) = UnknownFailure;
}

extension FailureX on Failure {
  String get displayMessage => when(
        network: (m) => m,
        timeout: (m) => m,
        noConnection: (m) => m,
        server: (m, _, __) => m,
        unauthorized: (m) => m,
        forbidden: (m) => m,
        notFound: (m) => m,
        validation: (m, _) => m,
        cache: (m) => m,
        parse: (m) => m,
        unknown: (m) => m,
      );

  bool get isRetryable => maybeWhen(
        network: (_) => true,
        timeout: (_) => true,
        noConnection: (_) => true,
        server: (_, __, statusCode) => statusCode != null && statusCode >= 500,
        orElse: () => false,
      );
}
```

## Error Mapper

```dart
class NetworkErrorMapper {
  static Failure mapDioError(DioException error) {
    switch (error.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        return const Failure.timeout();

      case DioExceptionType.connectionError:
        return const Failure.noConnection();

      case DioExceptionType.badResponse:
        return _mapStatusCode(error.response);

      case DioExceptionType.cancel:
        return const Failure.unknown(message: 'Request cancelled');

      case DioExceptionType.badCertificate:
        return const Failure.network(message: 'Invalid certificate');

      case DioExceptionType.unknown:
      default:
        if (error.error is SocketException) {
          return const Failure.noConnection();
        }
        return const Failure.unknown();
    }
  }

  static Failure _mapStatusCode(Response? response) {
    if (response == null) {
      return const Failure.unknown();
    }

    final statusCode = response.statusCode ?? 0;
    final data = response.data;

    // Try to parse error message from response
    String message = 'Server error';
    Map<String, List<String>>? validationErrors;

    if (data is Map<String, dynamic>) {
      message = data['message'] ?? data['error'] ?? message;

      if (data['errors'] is Map) {
        validationErrors = (data['errors'] as Map).map(
          (key, value) => MapEntry(
            key.toString(),
            (value is List) ? value.map((e) => e.toString()).toList() : [value.toString()],
          ),
        );
      }
    }

    switch (statusCode) {
      case 400:
        return Failure.validation(
          message: message,
          errors: validationErrors,
        );
      case 401:
        return Failure.unauthorized(message: message);
      case 403:
        return Failure.forbidden(message: message);
      case 404:
        return Failure.notFound(message: message);
      case 422:
        return Failure.validation(
          message: message,
          errors: validationErrors,
        );
      case 429:
        return const Failure.server(
          message: 'Too many requests. Please try again later.',
          statusCode: 429,
        );
      case >= 500:
        return Failure.server(
          message: 'Server error. Please try again later.',
          statusCode: statusCode,
        );
      default:
        return Failure.server(
          message: message,
          statusCode: statusCode,
        );
    }
  }
}
```

## Repository with Either Pattern

```dart
import 'package:dartz/dartz.dart';

abstract class ProductRepository {
  Future<Either<Failure, List<Product>>> getProducts();
  Future<Either<Failure, Product>> getProduct(String id);
  Future<Either<Failure, Product>> createProduct(CreateProductDto dto);
  Future<Either<Failure, Product>> updateProduct(String id, UpdateProductDto dto);
  Future<Either<Failure, Unit>> deleteProduct(String id);
}

class ProductRepositoryImpl implements ProductRepository {
  final ProductApiService _apiService;

  ProductRepositoryImpl(this._apiService);

  @override
  Future<Either<Failure, List<Product>>> getProducts() async {
    return _safeApiCall(
      () async {
        final models = await _apiService.getProducts();
        return models.map((m) => m.toEntity()).toList();
      },
    );
  }

  @override
  Future<Either<Failure, Product>> getProduct(String id) async {
    return _safeApiCall(
      () async {
        final model = await _apiService.getProduct(id);
        return model.toEntity();
      },
    );
  }

  @override
  Future<Either<Failure, Product>> createProduct(CreateProductDto dto) async {
    return _safeApiCall(
      () async {
        final model = await _apiService.createProduct(dto);
        return model.toEntity();
      },
    );
  }

  @override
  Future<Either<Failure, Product>> updateProduct(
    String id,
    UpdateProductDto dto,
  ) async {
    return _safeApiCall(
      () async {
        final model = await _apiService.updateProduct(id, dto);
        return model.toEntity();
      },
    );
  }

  @override
  Future<Either<Failure, Unit>> deleteProduct(String id) async {
    return _safeApiCall(
      () async {
        await _apiService.deleteProduct(id);
        return unit;
      },
    );
  }

  Future<Either<Failure, T>> _safeApiCall<T>(
    Future<T> Function() apiCall,
  ) async {
    try {
      final result = await apiCall();
      return Right(result);
    } on DioException catch (e) {
      return Left(NetworkErrorMapper.mapDioError(e));
    } on FormatException catch (e) {
      return Left(Failure.parse(message: e.message));
    } catch (e) {
      return Left(Failure.unknown(message: e.toString()));
    }
  }
}
```

## Use Case with Error Handling

```dart
class GetProductsUseCase {
  final ProductRepository _repository;

  GetProductsUseCase(this._repository);

  Future<Either<Failure, List<Product>>> call() async {
    return _repository.getProducts();
  }
}

// Usage in BLoC
class ProductsBloc extends Bloc<ProductsEvent, ProductsState> {
  final GetProductsUseCase _getProducts;

  ProductsBloc(this._getProducts) : super(const ProductsState()) {
    on<ProductsStarted>(_onStarted);
  }

  Future<void> _onStarted(
    ProductsStarted event,
    Emitter<ProductsState> emit,
  ) async {
    emit(state.copyWith(isLoading: true, failure: null));

    final result = await _getProducts();

    result.fold(
      (failure) => emit(state.copyWith(
        isLoading: false,
        failure: failure,
      )),
      (products) => emit(state.copyWith(
        isLoading: false,
        products: products,
      )),
    );
  }
}
```

## UI Error Display

```dart
class ErrorDisplay extends StatelessWidget {
  final Failure failure;
  final VoidCallback? onRetry;

  const ErrorDisplay({
    required this.failure,
    this.onRetry,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              _getIcon(),
              size: 64,
              color: _getColor(context),
            ),
            const SizedBox(height: 16),
            Text(
              _getTitle(),
              style: Theme.of(context).textTheme.titleLarge,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              failure.displayMessage,
              style: Theme.of(context).textTheme.bodyMedium,
              textAlign: TextAlign.center,
            ),
            if (failure.isRetryable && onRetry != null) ...[
              const SizedBox(height: 24),
              FilledButton.icon(
                onPressed: onRetry,
                icon: const Icon(Icons.refresh),
                label: const Text('Try Again'),
              ),
            ],
          ],
        ),
      ),
    );
  }

  IconData _getIcon() {
    return failure.when(
      network: (_) => Icons.wifi_off,
      timeout: (_) => Icons.timer_off,
      noConnection: (_) => Icons.signal_wifi_off,
      server: (_, __, ___) => Icons.cloud_off,
      unauthorized: (_) => Icons.lock,
      forbidden: (_) => Icons.block,
      notFound: (_) => Icons.search_off,
      validation: (_, __) => Icons.error,
      cache: (_) => Icons.storage,
      parse: (_) => Icons.code_off,
      unknown: (_) => Icons.error_outline,
    );
  }

  String _getTitle() {
    return failure.when(
      network: (_) => 'Network Error',
      timeout: (_) => 'Request Timeout',
      noConnection: (_) => 'No Connection',
      server: (_, __, ___) => 'Server Error',
      unauthorized: (_) => 'Not Authorized',
      forbidden: (_) => 'Access Denied',
      notFound: (_) => 'Not Found',
      validation: (_, __) => 'Validation Error',
      cache: (_) => 'Cache Error',
      parse: (_) => 'Data Error',
      unknown: (_) => 'Error',
    );
  }

  Color _getColor(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    return failure.maybeWhen(
      unauthorized: (_) => colorScheme.tertiary,
      forbidden: (_) => colorScheme.tertiary,
      orElse: () => colorScheme.error,
    );
  }
}
```

## Validation Error Display

```dart
class ValidationErrorDisplay extends StatelessWidget {
  final ValidationFailure failure;

  const ValidationErrorDisplay({required this.failure});

  @override
  Widget build(BuildContext context) {
    final errors = failure.errors;
    if (errors == null || errors.isEmpty) {
      return Text(failure.message);
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          failure.message,
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
            color: Theme.of(context).colorScheme.error,
          ),
        ),
        const SizedBox(height: 8),
        ...errors.entries.map((entry) => Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              entry.key,
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
            ...entry.value.map((error) => Padding(
              padding: const EdgeInsets.only(left: 16),
              child: Text('• $error'),
            )),
          ],
        )),
      ],
    );
  }
}
```

## Snackbar Error Display

```dart
void showErrorSnackbar(BuildContext context, Failure failure) {
  ScaffoldMessenger.of(context).showSnackBar(
    SnackBar(
      content: Text(failure.displayMessage),
      backgroundColor: Theme.of(context).colorScheme.error,
      action: failure.isRetryable
          ? SnackBarAction(
              label: 'Retry',
              textColor: Colors.white,
              onPressed: () {
                // Trigger retry
              },
            )
          : null,
    ),
  );
}

// BlocListener for error handling
BlocListener<ProductsBloc, ProductsState>(
  listenWhen: (previous, current) =>
      previous.failure != current.failure && current.failure != null,
  listener: (context, state) {
    if (state.failure != null) {
      showErrorSnackbar(context, state.failure!);
    }
  },
  child: const ProductsView(),
)
```

## Connectivity Check

```dart
import 'package:connectivity_plus/connectivity_plus.dart';

class ConnectivityService {
  final Connectivity _connectivity = Connectivity();

  Stream<bool> get onConnectivityChanged {
    return _connectivity.onConnectivityChanged.map((result) {
      return result != ConnectivityResult.none;
    });
  }

  Future<bool> get isConnected async {
    final result = await _connectivity.checkConnectivity();
    return result != ConnectivityResult.none;
  }
}

// Pre-check connectivity before API calls
class ProductRepository {
  final ProductApiService _apiService;
  final ConnectivityService _connectivity;

  ProductRepository(this._apiService, this._connectivity);

  Future<Either<Failure, List<Product>>> getProducts() async {
    if (!await _connectivity.isConnected) {
      return const Left(Failure.noConnection());
    }

    return _safeApiCall(() => _apiService.getProducts());
  }
}
```

## Best Practices

1. **Use typed failures** - Avoid generic Exception types
2. **Centralize mapping** - Single place for error conversion
3. **Either pattern** - Explicit success/failure handling
4. **User-friendly messages** - Translate technical errors
5. **Retryable errors** - Enable retry for transient failures
6. **Connectivity awareness** - Check connection before requests
