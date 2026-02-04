---
name: flutter-service
description: Template for Flutter service classes
applies_to: flutter
variables:
  - name: service_name
    description: Name of the service (PascalCase)
---

# Flutter Service Template

## API Service

```dart
// lib/core/services/api_service.dart

import 'package:dio/dio.dart';
import 'package:injectable/injectable.dart';

import '../error/exceptions.dart';

@lazySingleton
class ApiService {
  final Dio _dio;

  ApiService(this._dio);

  Future<T> get<T>(
    String path, {
    Map<String, dynamic>? queryParameters,
    T Function(dynamic)? fromJson,
  }) async {
    try {
      final response = await _dio.get(
        path,
        queryParameters: queryParameters,
      );
      return fromJson != null ? fromJson(response.data) : response.data as T;
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  Future<T> post<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    T Function(dynamic)? fromJson,
  }) async {
    try {
      final response = await _dio.post(
        path,
        data: data,
        queryParameters: queryParameters,
      );
      return fromJson != null ? fromJson(response.data) : response.data as T;
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  Future<T> put<T>(
    String path, {
    dynamic data,
    T Function(dynamic)? fromJson,
  }) async {
    try {
      final response = await _dio.put(path, data: data);
      return fromJson != null ? fromJson(response.data) : response.data as T;
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  Future<T> patch<T>(
    String path, {
    dynamic data,
    T Function(dynamic)? fromJson,
  }) async {
    try {
      final response = await _dio.patch(path, data: data);
      return fromJson != null ? fromJson(response.data) : response.data as T;
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  Future<void> delete(String path) async {
    try {
      await _dio.delete(path);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  Exception _handleError(DioException error) {
    switch (error.response?.statusCode) {
      case 401:
        return UnauthorizedException();
      case 404:
        return NotFoundException();
      case 422:
        return ValidationException.fromResponse(error.response?.data);
      default:
        return ServerException(
          message: error.response?.data?['message'] ?? 'Server error',
          statusCode: error.response?.statusCode,
        );
    }
  }
}
```

## Authentication Service

```dart
// lib/features/auth/services/auth_service.dart

import 'package:injectable/injectable.dart';

import '../../../core/services/api_service.dart';
import '../../../core/storage/secure_storage.dart';
import '../data/models/auth_models.dart';
import '../domain/entities/user.dart';

abstract class AuthService {
  Future<User> login(String email, String password);
  Future<User> register(RegisterRequest request);
  Future<void> logout();
  Future<User?> getCurrentUser();
  Future<void> refreshToken();
  Stream<User?> get userStream;
}

@LazySingleton(as: AuthService)
class AuthServiceImpl implements AuthService {
  final ApiService _api;
  final SecureStorage _storage;
  final _userController = StreamController<User?>.broadcast();

  AuthServiceImpl(this._api, this._storage);

  @override
  Stream<User?> get userStream => _userController.stream;

  @override
  Future<User> login(String email, String password) async {
    final response = await _api.post<Map<String, dynamic>>(
      '/auth/login',
      data: {'email': email, 'password': password},
    );

    final authResponse = AuthResponse.fromJson(response);
    await _saveTokens(authResponse);

    final user = authResponse.user.toEntity();
    _userController.add(user);

    return user;
  }

  @override
  Future<User> register(RegisterRequest request) async {
    final response = await _api.post<Map<String, dynamic>>(
      '/auth/register',
      data: request.toJson(),
    );

    final authResponse = AuthResponse.fromJson(response);
    await _saveTokens(authResponse);

    final user = authResponse.user.toEntity();
    _userController.add(user);

    return user;
  }

  @override
  Future<void> logout() async {
    try {
      await _api.post('/auth/logout');
    } finally {
      await _storage.deleteTokens();
      _userController.add(null);
    }
  }

  @override
  Future<User?> getCurrentUser() async {
    final token = await _storage.getAccessToken();
    if (token == null) return null;

    try {
      final response = await _api.get<Map<String, dynamic>>('/auth/me');
      final user = UserModel.fromJson(response['data']).toEntity();
      _userController.add(user);
      return user;
    } catch (e) {
      return null;
    }
  }

  @override
  Future<void> refreshToken() async {
    final refreshToken = await _storage.getRefreshToken();
    if (refreshToken == null) throw UnauthorizedException();

    final response = await _api.post<Map<String, dynamic>>(
      '/auth/refresh',
      data: {'refresh_token': refreshToken},
    );

    await _storage.saveTokens(
      accessToken: response['access_token'],
      refreshToken: response['refresh_token'],
    );
  }

  Future<void> _saveTokens(AuthResponse response) async {
    await _storage.saveTokens(
      accessToken: response.accessToken,
      refreshToken: response.refreshToken,
    );
  }

  void dispose() {
    _userController.close();
  }
}
```

## Storage Service

```dart
// lib/core/services/storage_service.dart

import 'package:hive_flutter/hive_flutter.dart';
import 'package:injectable/injectable.dart';

abstract class StorageService {
  Future<void> init();
  Future<void> put<T>(String key, T value);
  T? get<T>(String key);
  Future<void> delete(String key);
  Future<void> clear();
  bool containsKey(String key);
}

@LazySingleton(as: StorageService)
class HiveStorageService implements StorageService {
  static const _boxName = 'app_storage';
  late Box _box;

  @override
  Future<void> init() async {
    await Hive.initFlutter();
    _box = await Hive.openBox(_boxName);
  }

  @override
  Future<void> put<T>(String key, T value) async {
    await _box.put(key, value);
  }

  @override
  T? get<T>(String key) {
    return _box.get(key) as T?;
  }

  @override
  Future<void> delete(String key) async {
    await _box.delete(key);
  }

  @override
  Future<void> clear() async {
    await _box.clear();
  }

  @override
  bool containsKey(String key) {
    return _box.containsKey(key);
  }
}
```

## Analytics Service

```dart
// lib/core/services/analytics_service.dart

import 'package:firebase_analytics/firebase_analytics.dart';
import 'package:injectable/injectable.dart';

abstract class AnalyticsService {
  Future<void> logEvent(String name, {Map<String, dynamic>? parameters});
  Future<void> logScreenView(String screenName);
  Future<void> setUserId(String? userId);
  Future<void> setUserProperty(String name, String value);
  Future<void> logLogin(String method);
  Future<void> logPurchase({
    required double value,
    required String currency,
    String? transactionId,
  });
}

@LazySingleton(as: AnalyticsService)
class FirebaseAnalyticsService implements AnalyticsService {
  final FirebaseAnalytics _analytics = FirebaseAnalytics.instance;

  @override
  Future<void> logEvent(String name, {Map<String, dynamic>? parameters}) async {
    await _analytics.logEvent(
      name: name,
      parameters: parameters?.map(
        (key, value) => MapEntry(key, value?.toString()),
      ),
    );
  }

  @override
  Future<void> logScreenView(String screenName) async {
    await _analytics.logScreenView(screenName: screenName);
  }

  @override
  Future<void> setUserId(String? userId) async {
    await _analytics.setUserId(id: userId);
  }

  @override
  Future<void> setUserProperty(String name, String value) async {
    await _analytics.setUserProperty(name: name, value: value);
  }

  @override
  Future<void> logLogin(String method) async {
    await _analytics.logLogin(loginMethod: method);
  }

  @override
  Future<void> logPurchase({
    required double value,
    required String currency,
    String? transactionId,
  }) async {
    await _analytics.logPurchase(
      value: value,
      currency: currency,
      transactionId: transactionId,
    );
  }
}
```

## Notification Service

```dart
// lib/core/services/notification_service.dart

import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:injectable/injectable.dart';

abstract class NotificationService {
  Future<void> init();
  Future<String?> getToken();
  Stream<RemoteMessage> get onMessage;
  Future<void> showLocalNotification({
    required String title,
    required String body,
    String? payload,
  });
}

@LazySingleton(as: NotificationService)
class NotificationServiceImpl implements NotificationService {
  final FirebaseMessaging _messaging = FirebaseMessaging.instance;
  final FlutterLocalNotificationsPlugin _localNotifications =
      FlutterLocalNotificationsPlugin();

  @override
  Future<void> init() async {
    // Request permission
    await _messaging.requestPermission(
      alert: true,
      badge: true,
      sound: true,
    );

    // Initialize local notifications
    const androidSettings = AndroidInitializationSettings('@mipmap/ic_launcher');
    const iosSettings = DarwinInitializationSettings();
    const settings = InitializationSettings(
      android: androidSettings,
      iOS: iosSettings,
    );

    await _localNotifications.initialize(
      settings,
      onDidReceiveNotificationResponse: _onNotificationTap,
    );

    // Handle background messages
    FirebaseMessaging.onBackgroundMessage(_backgroundHandler);

    // Handle foreground messages
    FirebaseMessaging.onMessage.listen(_handleForegroundMessage);
  }

  @override
  Future<String?> getToken() => _messaging.getToken();

  @override
  Stream<RemoteMessage> get onMessage => FirebaseMessaging.onMessage;

  @override
  Future<void> showLocalNotification({
    required String title,
    required String body,
    String? payload,
  }) async {
    const androidDetails = AndroidNotificationDetails(
      'default_channel',
      'Default Channel',
      importance: Importance.high,
      priority: Priority.high,
    );

    const iosDetails = DarwinNotificationDetails();

    const details = NotificationDetails(
      android: androidDetails,
      iOS: iosDetails,
    );

    await _localNotifications.show(
      DateTime.now().millisecondsSinceEpoch ~/ 1000,
      title,
      body,
      details,
      payload: payload,
    );
  }

  void _handleForegroundMessage(RemoteMessage message) {
    if (message.notification != null) {
      showLocalNotification(
        title: message.notification!.title ?? '',
        body: message.notification!.body ?? '',
        payload: message.data.toString(),
      );
    }
  }

  void _onNotificationTap(NotificationResponse response) {
    // Handle notification tap
  }

  static Future<void> _backgroundHandler(RemoteMessage message) async {
    // Handle background message
  }
}
```

## Connectivity Service

```dart
// lib/core/services/connectivity_service.dart

import 'dart:async';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:injectable/injectable.dart';

abstract class ConnectivityService {
  Future<bool> get isConnected;
  Stream<bool> get connectivityStream;
}

@LazySingleton(as: ConnectivityService)
class ConnectivityServiceImpl implements ConnectivityService {
  final Connectivity _connectivity = Connectivity();
  final _streamController = StreamController<bool>.broadcast();

  ConnectivityServiceImpl() {
    _connectivity.onConnectivityChanged.listen((results) {
      _streamController.add(_isConnected(results));
    });
  }

  @override
  Future<bool> get isConnected async {
    final results = await _connectivity.checkConnectivity();
    return _isConnected(results);
  }

  @override
  Stream<bool> get connectivityStream => _streamController.stream;

  bool _isConnected(List<ConnectivityResult> results) {
    return results.any((result) =>
        result == ConnectivityResult.wifi ||
        result == ConnectivityResult.mobile ||
        result == ConnectivityResult.ethernet);
  }

  void dispose() {
    _streamController.close();
  }
}
```

## Usage

Replace `{{service_name}}` with actual service name

Register services with dependency injection:
```dart
@module
abstract class ServiceModule {
  @lazySingleton
  Dio get dio => Dio(BaseOptions(baseUrl: 'https://api.example.com'));
}
```
