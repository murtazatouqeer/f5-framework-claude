---
name: flutter-dio-client
description: Dio HTTP client setup and configuration
applies_to: flutter
---

# Flutter Dio Client

## Overview

Dio is a powerful HTTP client for Flutter with interceptors, FormData, request cancellation, file downloading, and timeout support.

## Dependencies

```yaml
dependencies:
  dio: ^5.4.0
  pretty_dio_logger: ^1.3.1
```

## Basic Setup

```dart
import 'package:dio/dio.dart';

class ApiClient {
  late final Dio _dio;

  ApiClient({
    required String baseUrl,
    Duration? connectTimeout,
    Duration? receiveTimeout,
  }) {
    _dio = Dio(
      BaseOptions(
        baseUrl: baseUrl,
        connectTimeout: connectTimeout ?? const Duration(seconds: 30),
        receiveTimeout: receiveTimeout ?? const Duration(seconds: 30),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      ),
    );
  }

  Dio get dio => _dio;
}
```

## Comprehensive API Client

```dart
import 'package:dio/dio.dart';
import 'package:pretty_dio_logger/pretty_dio_logger.dart';

class ApiClient {
  late final Dio _dio;
  final TokenStorage _tokenStorage;

  ApiClient({
    required String baseUrl,
    required TokenStorage tokenStorage,
  }) : _tokenStorage = tokenStorage {
    _dio = Dio(
      BaseOptions(
        baseUrl: baseUrl,
        connectTimeout: const Duration(seconds: 30),
        receiveTimeout: const Duration(seconds: 30),
        sendTimeout: const Duration(seconds: 30),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      ),
    );

    _setupInterceptors();
  }

  void _setupInterceptors() {
    // Auth interceptor
    _dio.interceptors.add(AuthInterceptor(_tokenStorage, _dio));

    // Retry interceptor
    _dio.interceptors.add(RetryInterceptor(_dio));

    // Logging interceptor (debug only)
    if (kDebugMode) {
      _dio.interceptors.add(
        PrettyDioLogger(
          requestHeader: true,
          requestBody: true,
          responseBody: true,
          responseHeader: false,
          error: true,
          compact: true,
        ),
      );
    }
  }

  // GET request
  Future<Response<T>> get<T>(
    String path, {
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
  }) {
    return _dio.get<T>(
      path,
      queryParameters: queryParameters,
      options: options,
      cancelToken: cancelToken,
    );
  }

  // POST request
  Future<Response<T>> post<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
  }) {
    return _dio.post<T>(
      path,
      data: data,
      queryParameters: queryParameters,
      options: options,
      cancelToken: cancelToken,
    );
  }

  // PUT request
  Future<Response<T>> put<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
  }) {
    return _dio.put<T>(
      path,
      data: data,
      queryParameters: queryParameters,
      options: options,
      cancelToken: cancelToken,
    );
  }

  // PATCH request
  Future<Response<T>> patch<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
  }) {
    return _dio.patch<T>(
      path,
      data: data,
      queryParameters: queryParameters,
      options: options,
      cancelToken: cancelToken,
    );
  }

  // DELETE request
  Future<Response<T>> delete<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
  }) {
    return _dio.delete<T>(
      path,
      data: data,
      queryParameters: queryParameters,
      options: options,
      cancelToken: cancelToken,
    );
  }
}
```

## Auth Interceptor

```dart
class AuthInterceptor extends Interceptor {
  final TokenStorage _tokenStorage;
  final Dio _dio;
  bool _isRefreshing = false;
  final List<RequestOptions> _pendingRequests = [];

  AuthInterceptor(this._tokenStorage, this._dio);

  @override
  void onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final token = await _tokenStorage.getAccessToken();
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    if (err.response?.statusCode == 401) {
      if (_isRefreshing) {
        // Queue request while refreshing
        _pendingRequests.add(err.requestOptions);
        return;
      }

      _isRefreshing = true;

      try {
        final refreshToken = await _tokenStorage.getRefreshToken();
        if (refreshToken == null) {
          await _tokenStorage.clear();
          handler.reject(err);
          return;
        }

        // Refresh token
        final response = await _dio.post(
          '/auth/refresh',
          data: {'refresh_token': refreshToken},
          options: Options(
            headers: {'Authorization': null},
          ),
        );

        final newAccessToken = response.data['access_token'];
        final newRefreshToken = response.data['refresh_token'];

        await _tokenStorage.saveTokens(
          accessToken: newAccessToken,
          refreshToken: newRefreshToken,
        );

        // Retry original request
        final retryResponse = await _retryRequest(err.requestOptions);
        handler.resolve(retryResponse);

        // Retry pending requests
        for (final request in _pendingRequests) {
          _retryRequest(request);
        }
        _pendingRequests.clear();
      } catch (e) {
        await _tokenStorage.clear();
        handler.reject(err);
      } finally {
        _isRefreshing = false;
      }
    } else {
      handler.next(err);
    }
  }

  Future<Response> _retryRequest(RequestOptions requestOptions) {
    return _dio.fetch(requestOptions);
  }
}
```

## Retry Interceptor

```dart
class RetryInterceptor extends Interceptor {
  final Dio _dio;
  final int maxRetries;
  final Duration retryDelay;

  RetryInterceptor(
    this._dio, {
    this.maxRetries = 3,
    this.retryDelay = const Duration(seconds: 1),
  });

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    if (_shouldRetry(err)) {
      final retryCount = err.requestOptions.extra['retryCount'] ?? 0;

      if (retryCount < maxRetries) {
        await Future.delayed(retryDelay * (retryCount + 1));

        try {
          err.requestOptions.extra['retryCount'] = retryCount + 1;
          final response = await _dio.fetch(err.requestOptions);
          handler.resolve(response);
          return;
        } catch (e) {
          // Fall through to handler.next(err)
        }
      }
    }
    handler.next(err);
  }

  bool _shouldRetry(DioException err) {
    return err.type == DioExceptionType.connectionTimeout ||
        err.type == DioExceptionType.receiveTimeout ||
        err.type == DioExceptionType.sendTimeout ||
        (err.response?.statusCode ?? 0) >= 500;
  }
}
```

## File Upload

```dart
class FileUploadService {
  final ApiClient _apiClient;

  FileUploadService(this._apiClient);

  Future<String> uploadFile(
    File file, {
    void Function(int sent, int total)? onProgress,
    CancelToken? cancelToken,
  }) async {
    final fileName = file.path.split('/').last;
    final formData = FormData.fromMap({
      'file': await MultipartFile.fromFile(
        file.path,
        filename: fileName,
      ),
    });

    final response = await _apiClient.post<Map<String, dynamic>>(
      '/upload',
      data: formData,
      options: Options(
        headers: {'Content-Type': 'multipart/form-data'},
      ),
      cancelToken: cancelToken,
    );

    return response.data!['url'];
  }

  Future<List<String>> uploadMultipleFiles(
    List<File> files, {
    void Function(int sent, int total)? onProgress,
    CancelToken? cancelToken,
  }) async {
    final formData = FormData();

    for (final file in files) {
      final fileName = file.path.split('/').last;
      formData.files.add(
        MapEntry(
          'files',
          await MultipartFile.fromFile(file.path, filename: fileName),
        ),
      );
    }

    final response = await _apiClient.post<Map<String, dynamic>>(
      '/upload/multiple',
      data: formData,
      cancelToken: cancelToken,
    );

    return List<String>.from(response.data!['urls']);
  }
}
```

## File Download

```dart
class FileDownloadService {
  final Dio _dio;

  FileDownloadService(this._dio);

  Future<String> downloadFile(
    String url,
    String savePath, {
    void Function(int received, int total)? onProgress,
    CancelToken? cancelToken,
  }) async {
    await _dio.download(
      url,
      savePath,
      onReceiveProgress: onProgress,
      cancelToken: cancelToken,
    );
    return savePath;
  }

  Future<Uint8List> downloadToMemory(
    String url, {
    CancelToken? cancelToken,
  }) async {
    final response = await _dio.get<List<int>>(
      url,
      options: Options(responseType: ResponseType.bytes),
      cancelToken: cancelToken,
    );
    return Uint8List.fromList(response.data!);
  }
}
```

## Request Cancellation

```dart
class ProductRepository {
  final ApiClient _apiClient;
  CancelToken? _searchCancelToken;

  ProductRepository(this._apiClient);

  Future<List<Product>> searchProducts(String query) async {
    // Cancel previous search
    _searchCancelToken?.cancel('New search initiated');
    _searchCancelToken = CancelToken();

    try {
      final response = await _apiClient.get<List<dynamic>>(
        '/products/search',
        queryParameters: {'q': query},
        cancelToken: _searchCancelToken,
      );

      return response.data!.map((json) => Product.fromJson(json)).toList();
    } on DioException catch (e) {
      if (CancelToken.isCancel(e)) {
        // Request was cancelled, return empty list
        return [];
      }
      rethrow;
    }
  }

  void cancelSearch() {
    _searchCancelToken?.cancel('Search cancelled by user');
  }
}
```

## Dependency Injection

```dart
// Using injectable
@module
abstract class NetworkModule {
  @lazySingleton
  Dio dio(TokenStorage tokenStorage) {
    final dio = Dio(
      BaseOptions(
        baseUrl: Environment.apiBaseUrl,
        connectTimeout: const Duration(seconds: 30),
        receiveTimeout: const Duration(seconds: 30),
      ),
    );

    dio.interceptors.addAll([
      AuthInterceptor(tokenStorage, dio),
      if (kDebugMode) PrettyDioLogger(),
    ]);

    return dio;
  }

  @lazySingleton
  ApiClient apiClient(Dio dio) => ApiClient(dio);
}

// Using Riverpod
@riverpod
Dio dio(DioRef ref) {
  final tokenStorage = ref.watch(tokenStorageProvider);
  final dio = Dio(
    BaseOptions(
      baseUrl: Environment.apiBaseUrl,
      connectTimeout: const Duration(seconds: 30),
      receiveTimeout: const Duration(seconds: 30),
    ),
  );

  dio.interceptors.addAll([
    AuthInterceptor(tokenStorage, dio),
    if (kDebugMode) PrettyDioLogger(),
  ]);

  return dio;
}

@riverpod
ApiClient apiClient(ApiClientRef ref) {
  return ApiClient(ref.watch(dioProvider));
}
```

## Testing

```dart
import 'package:dio/dio.dart';
import 'package:http_mock_adapter/http_mock_adapter.dart';

void main() {
  late Dio dio;
  late DioAdapter dioAdapter;
  late ProductRepository repository;

  setUp(() {
    dio = Dio(BaseOptions(baseUrl: 'https://api.example.com'));
    dioAdapter = DioAdapter(dio: dio);
    repository = ProductRepository(ApiClient(dio));
  });

  test('getProducts returns list of products', () async {
    dioAdapter.onGet(
      '/products',
      (server) => server.reply(200, [
        {'id': '1', 'name': 'Product 1'},
        {'id': '2', 'name': 'Product 2'},
      ]),
    );

    final products = await repository.getProducts();

    expect(products.length, 2);
    expect(products[0].name, 'Product 1');
  });

  test('getProducts handles error', () async {
    dioAdapter.onGet(
      '/products',
      (server) => server.reply(500, {'message': 'Server error'}),
    );

    expect(
      () => repository.getProducts(),
      throwsA(isA<ServerException>()),
    );
  });
}
```

## Best Practices

1. **Use interceptors** - Centralize auth, logging, retry logic
2. **Handle timeouts** - Set appropriate timeout values
3. **Cancel requests** - Cancel outdated requests to save resources
4. **Error handling** - Map DioException to domain errors
5. **Type safety** - Use generic response types
6. **Test with mocks** - Use http_mock_adapter for testing
