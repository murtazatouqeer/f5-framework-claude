# Flutter Authentication App Example

Complete Flutter application demonstrating authentication with Clean Architecture.

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
│   │   ├── auth_interceptor.dart
│   │   └── network_info.dart
│   ├── storage/
│   │   └── secure_storage.dart
│   └── router/
│       └── app_router.dart
├── features/
│   ├── auth/
│   │   ├── data/
│   │   │   ├── datasources/
│   │   │   │   └── auth_remote_datasource.dart
│   │   │   ├── models/
│   │   │   │   ├── user_model.dart
│   │   │   │   └── auth_response.dart
│   │   │   └── repositories/
│   │   │       └── auth_repository_impl.dart
│   │   ├── domain/
│   │   │   ├── entities/
│   │   │   │   └── user.dart
│   │   │   ├── repositories/
│   │   │   │   └── auth_repository.dart
│   │   │   └── usecases/
│   │   │       ├── login.dart
│   │   │       ├── register.dart
│   │   │       ├── logout.dart
│   │   │       └── get_current_user.dart
│   │   └── presentation/
│   │       ├── bloc/
│   │       │   ├── auth_bloc.dart
│   │       │   ├── auth_event.dart
│   │       │   └── auth_state.dart
│   │       ├── screens/
│   │       │   ├── login_screen.dart
│   │       │   ├── register_screen.dart
│   │       │   └── splash_screen.dart
│   │       └── widgets/
│   │           ├── auth_form.dart
│   │           └── social_login_buttons.dart
│   └── home/
│       └── presentation/
│           └── screens/
│               └── home_screen.dart
├── app.dart
└── main.dart
```

## Dependencies

```yaml
# pubspec.yaml
name: auth_app
description: Flutter Authentication App Example

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
  flutter_secure_storage: ^9.0.0
  go_router: ^13.0.0
  google_sign_in: ^6.2.1
  sign_in_with_apple: ^5.0.0
  local_auth: ^2.1.8
  flutter_form_builder: ^9.1.1
  form_builder_validators: ^9.1.0

dev_dependencies:
  flutter_test:
    sdk: flutter
  build_runner: ^2.4.7
  freezed: ^2.4.5
  json_serializable: ^6.7.1
  injectable_generator: ^2.4.1
  bloc_test: ^9.1.5
  mocktail: ^1.0.1
```

## Core Layer

### Secure Storage

```dart
// lib/core/storage/secure_storage.dart
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:injectable/injectable.dart';

abstract class SecureStorage {
  Future<void> saveTokens({
    required String accessToken,
    required String refreshToken,
  });
  Future<String?> getAccessToken();
  Future<String?> getRefreshToken();
  Future<void> deleteTokens();
  Future<bool> hasTokens();
}

@LazySingleton(as: SecureStorage)
class SecureStorageImpl implements SecureStorage {
  final FlutterSecureStorage _storage;

  static const _accessTokenKey = 'access_token';
  static const _refreshTokenKey = 'refresh_token';

  SecureStorageImpl() : _storage = const FlutterSecureStorage(
    aOptions: AndroidOptions(encryptedSharedPreferences: true),
    iOptions: IOSOptions(accessibility: KeychainAccessibility.first_unlock),
  );

  @override
  Future<void> saveTokens({
    required String accessToken,
    required String refreshToken,
  }) async {
    await Future.wait([
      _storage.write(key: _accessTokenKey, value: accessToken),
      _storage.write(key: _refreshTokenKey, value: refreshToken),
    ]);
  }

  @override
  Future<String?> getAccessToken() => _storage.read(key: _accessTokenKey);

  @override
  Future<String?> getRefreshToken() => _storage.read(key: _refreshTokenKey);

  @override
  Future<void> deleteTokens() async {
    await Future.wait([
      _storage.delete(key: _accessTokenKey),
      _storage.delete(key: _refreshTokenKey),
    ]);
  }

  @override
  Future<bool> hasTokens() async {
    final token = await getAccessToken();
    return token != null && token.isNotEmpty;
  }
}
```

### Auth Interceptor

```dart
// lib/core/network/auth_interceptor.dart
import 'dart:io';

import 'package:dio/dio.dart';
import 'package:injectable/injectable.dart';

import '../storage/secure_storage.dart';

@injectable
class AuthInterceptor extends Interceptor {
  final SecureStorage _storage;
  final Dio _dio;

  AuthInterceptor(this._storage, this._dio);

  @override
  void onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final token = await _storage.getAccessToken();
    if (token != null) {
      options.headers[HttpHeaders.authorizationHeader] = 'Bearer $token';
    }
    handler.next(options);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    if (err.response?.statusCode == 401) {
      // Try to refresh token
      final refreshToken = await _storage.getRefreshToken();
      if (refreshToken != null) {
        try {
          final response = await _dio.post(
            '/auth/refresh',
            data: {'refresh_token': refreshToken},
          );

          await _storage.saveTokens(
            accessToken: response.data['access_token'],
            refreshToken: response.data['refresh_token'],
          );

          // Retry original request
          final opts = err.requestOptions;
          opts.headers[HttpHeaders.authorizationHeader] =
              'Bearer ${response.data['access_token']}';

          final cloneReq = await _dio.request(
            opts.path,
            options: Options(
              method: opts.method,
              headers: opts.headers,
            ),
            data: opts.data,
            queryParameters: opts.queryParameters,
          );

          return handler.resolve(cloneReq);
        } catch (_) {
          await _storage.deleteTokens();
        }
      }
    }
    handler.next(err);
  }
}
```

### App Router

```dart
// lib/core/router/app_router.dart
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../features/auth/presentation/bloc/auth_bloc.dart';
import '../../features/auth/presentation/screens/login_screen.dart';
import '../../features/auth/presentation/screens/register_screen.dart';
import '../../features/auth/presentation/screens/splash_screen.dart';
import '../../features/home/presentation/screens/home_screen.dart';

class AppRouter {
  final AuthBloc authBloc;

  AppRouter(this.authBloc);

  late final router = GoRouter(
    initialLocation: '/splash',
    refreshListenable: GoRouterRefreshStream(authBloc.stream),
    redirect: (context, state) {
      final authState = authBloc.state;
      final isLoggingIn = state.matchedLocation == '/login' ||
          state.matchedLocation == '/register';
      final isSplash = state.matchedLocation == '/splash';

      // Still checking auth status
      if (authState is AuthLoading || authState is AuthInitial) {
        return isSplash ? null : '/splash';
      }

      // Not authenticated
      if (authState is AuthUnauthenticated) {
        return isLoggingIn ? null : '/login';
      }

      // Authenticated
      if (authState is AuthAuthenticated) {
        return isLoggingIn || isSplash ? '/home' : null;
      }

      return null;
    },
    routes: [
      GoRoute(
        path: '/splash',
        builder: (context, state) => const SplashScreen(),
      ),
      GoRoute(
        path: '/login',
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/register',
        builder: (context, state) => const RegisterScreen(),
      ),
      GoRoute(
        path: '/home',
        builder: (context, state) => const HomeScreen(),
      ),
    ],
  );
}

class GoRouterRefreshStream extends ChangeNotifier {
  GoRouterRefreshStream(Stream<dynamic> stream) {
    stream.listen((_) => notifyListeners());
  }
}
```

## Domain Layer

### User Entity

```dart
// lib/features/auth/domain/entities/user.dart
import 'package:freezed_annotation/freezed_annotation.dart';

part 'user.freezed.dart';

@freezed
class User with _$User {
  const factory User({
    required String id,
    required String email,
    required String name,
    String? avatarUrl,
    required DateTime createdAt,
  }) = _User;

  const User._();

  String get initials {
    final parts = name.split(' ');
    if (parts.length >= 2) {
      return '${parts[0][0]}${parts[1][0]}'.toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
  }
}
```

### Auth Repository Interface

```dart
// lib/features/auth/domain/repositories/auth_repository.dart
import 'package:dartz/dartz.dart';

import '../../../../core/error/failures.dart';
import '../entities/user.dart';

abstract class AuthRepository {
  Future<Either<Failure, User>> login({
    required String email,
    required String password,
  });
  Future<Either<Failure, User>> register({
    required String name,
    required String email,
    required String password,
  });
  Future<Either<Failure, void>> logout();
  Future<Either<Failure, User>> getCurrentUser();
  Future<Either<Failure, User>> loginWithGoogle();
  Future<Either<Failure, User>> loginWithApple();
  Future<bool> isAuthenticated();
}
```

### Use Cases

```dart
// lib/features/auth/domain/usecases/login.dart
import 'package:dartz/dartz.dart';
import 'package:injectable/injectable.dart';

import '../../../../core/error/failures.dart';
import '../entities/user.dart';
import '../repositories/auth_repository.dart';

@injectable
class Login {
  final AuthRepository _repository;

  Login(this._repository);

  Future<Either<Failure, User>> call({
    required String email,
    required String password,
  }) =>
      _repository.login(email: email, password: password);
}

// lib/features/auth/domain/usecases/register.dart
@injectable
class Register {
  final AuthRepository _repository;

  Register(this._repository);

  Future<Either<Failure, User>> call({
    required String name,
    required String email,
    required String password,
  }) =>
      _repository.register(name: name, email: email, password: password);
}

// lib/features/auth/domain/usecases/logout.dart
@injectable
class Logout {
  final AuthRepository _repository;

  Logout(this._repository);

  Future<Either<Failure, void>> call() => _repository.logout();
}

// lib/features/auth/domain/usecases/get_current_user.dart
@injectable
class GetCurrentUser {
  final AuthRepository _repository;

  GetCurrentUser(this._repository);

  Future<Either<Failure, User>> call() => _repository.getCurrentUser();
}
```

## Data Layer

### Models

```dart
// lib/features/auth/data/models/user_model.dart
import 'package:freezed_annotation/freezed_annotation.dart';

import '../../domain/entities/user.dart';

part 'user_model.freezed.dart';
part 'user_model.g.dart';

@freezed
class UserModel with _$UserModel {
  const factory UserModel({
    required String id,
    required String email,
    required String name,
    @JsonKey(name: 'avatar_url') String? avatarUrl,
    @JsonKey(name: 'created_at') required DateTime createdAt,
  }) = _UserModel;

  const UserModel._();

  factory UserModel.fromJson(Map<String, dynamic> json) =>
      _$UserModelFromJson(json);

  User toEntity() => User(
        id: id,
        email: email,
        name: name,
        avatarUrl: avatarUrl,
        createdAt: createdAt,
      );
}

// lib/features/auth/data/models/auth_response.dart
import 'package:freezed_annotation/freezed_annotation.dart';

import 'user_model.dart';

part 'auth_response.freezed.dart';
part 'auth_response.g.dart';

@freezed
class AuthResponse with _$AuthResponse {
  const factory AuthResponse({
    @JsonKey(name: 'access_token') required String accessToken,
    @JsonKey(name: 'refresh_token') required String refreshToken,
    required UserModel user,
  }) = _AuthResponse;

  factory AuthResponse.fromJson(Map<String, dynamic> json) =>
      _$AuthResponseFromJson(json);
}
```

### Data Source

```dart
// lib/features/auth/data/datasources/auth_remote_datasource.dart
import 'package:dio/dio.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:injectable/injectable.dart';
import 'package:sign_in_with_apple/sign_in_with_apple.dart';

import '../../../../core/error/exceptions.dart';
import '../models/auth_response.dart';
import '../models/user_model.dart';

abstract class AuthRemoteDataSource {
  Future<AuthResponse> login({
    required String email,
    required String password,
  });
  Future<AuthResponse> register({
    required String name,
    required String email,
    required String password,
  });
  Future<void> logout();
  Future<UserModel> getCurrentUser();
  Future<AuthResponse> loginWithGoogle();
  Future<AuthResponse> loginWithApple();
}

@LazySingleton(as: AuthRemoteDataSource)
class AuthRemoteDataSourceImpl implements AuthRemoteDataSource {
  final Dio _dio;
  final GoogleSignIn _googleSignIn;

  AuthRemoteDataSourceImpl(this._dio)
      : _googleSignIn = GoogleSignIn(scopes: ['email', 'profile']);

  @override
  Future<AuthResponse> login({
    required String email,
    required String password,
  }) async {
    try {
      final response = await _dio.post(
        '/auth/login',
        data: {'email': email, 'password': password},
      );
      return AuthResponse.fromJson(response.data);
    } on DioException catch (e) {
      if (e.response?.statusCode == 401) {
        throw InvalidCredentialsException();
      }
      throw ServerException.fromDioError(e);
    }
  }

  @override
  Future<AuthResponse> register({
    required String name,
    required String email,
    required String password,
  }) async {
    try {
      final response = await _dio.post(
        '/auth/register',
        data: {
          'name': name,
          'email': email,
          'password': password,
        },
      );
      return AuthResponse.fromJson(response.data);
    } on DioException catch (e) {
      if (e.response?.statusCode == 422) {
        throw ValidationException.fromResponse(e.response?.data);
      }
      throw ServerException.fromDioError(e);
    }
  }

  @override
  Future<void> logout() async {
    try {
      await _dio.post('/auth/logout');
    } on DioException catch (e) {
      throw ServerException.fromDioError(e);
    }
  }

  @override
  Future<UserModel> getCurrentUser() async {
    try {
      final response = await _dio.get('/auth/me');
      return UserModel.fromJson(response.data['data']);
    } on DioException catch (e) {
      if (e.response?.statusCode == 401) {
        throw UnauthorizedException();
      }
      throw ServerException.fromDioError(e);
    }
  }

  @override
  Future<AuthResponse> loginWithGoogle() async {
    try {
      final account = await _googleSignIn.signIn();
      if (account == null) throw SocialLoginCancelledException();

      final auth = await account.authentication;
      final response = await _dio.post(
        '/auth/google',
        data: {'id_token': auth.idToken},
      );
      return AuthResponse.fromJson(response.data);
    } on DioException catch (e) {
      throw ServerException.fromDioError(e);
    }
  }

  @override
  Future<AuthResponse> loginWithApple() async {
    try {
      final credential = await SignInWithApple.getAppleIDCredential(
        scopes: [
          AppleIDAuthorizationScopes.email,
          AppleIDAuthorizationScopes.fullName,
        ],
      );

      final response = await _dio.post(
        '/auth/apple',
        data: {
          'identity_token': credential.identityToken,
          'authorization_code': credential.authorizationCode,
        },
      );
      return AuthResponse.fromJson(response.data);
    } on SignInWithAppleAuthorizationException {
      throw SocialLoginCancelledException();
    } on DioException catch (e) {
      throw ServerException.fromDioError(e);
    }
  }
}

// Additional exceptions
class InvalidCredentialsException implements Exception {}
class UnauthorizedException implements Exception {}
class SocialLoginCancelledException implements Exception {}
```

### Repository Implementation

```dart
// lib/features/auth/data/repositories/auth_repository_impl.dart
import 'package:dartz/dartz.dart';
import 'package:injectable/injectable.dart';

import '../../../../core/error/exceptions.dart';
import '../../../../core/error/failures.dart';
import '../../../../core/storage/secure_storage.dart';
import '../../domain/entities/user.dart';
import '../../domain/repositories/auth_repository.dart';
import '../datasources/auth_remote_datasource.dart';

@LazySingleton(as: AuthRepository)
class AuthRepositoryImpl implements AuthRepository {
  final AuthRemoteDataSource _remoteDataSource;
  final SecureStorage _secureStorage;

  AuthRepositoryImpl({
    required AuthRemoteDataSource remoteDataSource,
    required SecureStorage secureStorage,
  })  : _remoteDataSource = remoteDataSource,
        _secureStorage = secureStorage;

  @override
  Future<Either<Failure, User>> login({
    required String email,
    required String password,
  }) async {
    try {
      final response = await _remoteDataSource.login(
        email: email,
        password: password,
      );
      await _secureStorage.saveTokens(
        accessToken: response.accessToken,
        refreshToken: response.refreshToken,
      );
      return Right(response.user.toEntity());
    } on InvalidCredentialsException {
      return const Left(AuthFailure(message: 'Invalid email or password'));
    } on ServerException catch (e) {
      return Left(ServerFailure(message: e.message));
    }
  }

  @override
  Future<Either<Failure, User>> register({
    required String name,
    required String email,
    required String password,
  }) async {
    try {
      final response = await _remoteDataSource.register(
        name: name,
        email: email,
        password: password,
      );
      await _secureStorage.saveTokens(
        accessToken: response.accessToken,
        refreshToken: response.refreshToken,
      );
      return Right(response.user.toEntity());
    } on ValidationException catch (e) {
      return Left(ValidationFailure(message: e.message, errors: e.errors));
    } on ServerException catch (e) {
      return Left(ServerFailure(message: e.message));
    }
  }

  @override
  Future<Either<Failure, void>> logout() async {
    try {
      await _remoteDataSource.logout();
      await _secureStorage.deleteTokens();
      return const Right(null);
    } catch (_) {
      await _secureStorage.deleteTokens();
      return const Right(null);
    }
  }

  @override
  Future<Either<Failure, User>> getCurrentUser() async {
    try {
      final user = await _remoteDataSource.getCurrentUser();
      return Right(user.toEntity());
    } on UnauthorizedException {
      await _secureStorage.deleteTokens();
      return const Left(AuthFailure(message: 'Session expired'));
    } on ServerException catch (e) {
      return Left(ServerFailure(message: e.message));
    }
  }

  @override
  Future<Either<Failure, User>> loginWithGoogle() async {
    try {
      final response = await _remoteDataSource.loginWithGoogle();
      await _secureStorage.saveTokens(
        accessToken: response.accessToken,
        refreshToken: response.refreshToken,
      );
      return Right(response.user.toEntity());
    } on SocialLoginCancelledException {
      return const Left(AuthFailure(message: 'Login cancelled'));
    } on ServerException catch (e) {
      return Left(ServerFailure(message: e.message));
    }
  }

  @override
  Future<Either<Failure, User>> loginWithApple() async {
    try {
      final response = await _remoteDataSource.loginWithApple();
      await _secureStorage.saveTokens(
        accessToken: response.accessToken,
        refreshToken: response.refreshToken,
      );
      return Right(response.user.toEntity());
    } on SocialLoginCancelledException {
      return const Left(AuthFailure(message: 'Login cancelled'));
    } on ServerException catch (e) {
      return Left(ServerFailure(message: e.message));
    }
  }

  @override
  Future<bool> isAuthenticated() => _secureStorage.hasTokens();
}
```

## Presentation Layer

### Auth BLoC

```dart
// lib/features/auth/presentation/bloc/auth_bloc.dart
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:injectable/injectable.dart';

import '../../domain/entities/user.dart';
import '../../domain/repositories/auth_repository.dart';
import '../../domain/usecases/get_current_user.dart';
import '../../domain/usecases/login.dart';
import '../../domain/usecases/logout.dart';
import '../../domain/usecases/register.dart';

part 'auth_bloc.freezed.dart';
part 'auth_event.dart';
part 'auth_state.dart';

@injectable
class AuthBloc extends Bloc<AuthEvent, AuthState> {
  final Login _login;
  final Register _register;
  final Logout _logout;
  final GetCurrentUser _getCurrentUser;
  final AuthRepository _repository;

  AuthBloc({
    required Login login,
    required Register register,
    required Logout logout,
    required GetCurrentUser getCurrentUser,
    required AuthRepository repository,
  })  : _login = login,
        _register = register,
        _logout = logout,
        _getCurrentUser = getCurrentUser,
        _repository = repository,
        super(const AuthInitial()) {
    on<AuthCheckRequested>(_onCheckRequested);
    on<AuthLoginRequested>(_onLoginRequested);
    on<AuthRegisterRequested>(_onRegisterRequested);
    on<AuthLogoutRequested>(_onLogoutRequested);
    on<AuthGoogleLoginRequested>(_onGoogleLoginRequested);
    on<AuthAppleLoginRequested>(_onAppleLoginRequested);
  }

  Future<void> _onCheckRequested(
    AuthCheckRequested event,
    Emitter<AuthState> emit,
  ) async {
    emit(const AuthLoading());

    final isAuthenticated = await _repository.isAuthenticated();
    if (!isAuthenticated) {
      emit(const AuthUnauthenticated());
      return;
    }

    final result = await _getCurrentUser();
    result.fold(
      (failure) => emit(const AuthUnauthenticated()),
      (user) => emit(AuthAuthenticated(user)),
    );
  }

  Future<void> _onLoginRequested(
    AuthLoginRequested event,
    Emitter<AuthState> emit,
  ) async {
    emit(const AuthLoading());

    final result = await _login(
      email: event.email,
      password: event.password,
    );

    result.fold(
      (failure) => emit(AuthError(failure.toString())),
      (user) => emit(AuthAuthenticated(user)),
    );
  }

  Future<void> _onRegisterRequested(
    AuthRegisterRequested event,
    Emitter<AuthState> emit,
  ) async {
    emit(const AuthLoading());

    final result = await _register(
      name: event.name,
      email: event.email,
      password: event.password,
    );

    result.fold(
      (failure) => emit(AuthError(failure.toString())),
      (user) => emit(AuthAuthenticated(user)),
    );
  }

  Future<void> _onLogoutRequested(
    AuthLogoutRequested event,
    Emitter<AuthState> emit,
  ) async {
    emit(const AuthLoading());
    await _logout();
    emit(const AuthUnauthenticated());
  }

  Future<void> _onGoogleLoginRequested(
    AuthGoogleLoginRequested event,
    Emitter<AuthState> emit,
  ) async {
    emit(const AuthLoading());

    final result = await _repository.loginWithGoogle();
    result.fold(
      (failure) => emit(AuthError(failure.toString())),
      (user) => emit(AuthAuthenticated(user)),
    );
  }

  Future<void> _onAppleLoginRequested(
    AuthAppleLoginRequested event,
    Emitter<AuthState> emit,
  ) async {
    emit(const AuthLoading());

    final result = await _repository.loginWithApple();
    result.fold(
      (failure) => emit(AuthError(failure.toString())),
      (user) => emit(AuthAuthenticated(user)),
    );
  }
}

// lib/features/auth/presentation/bloc/auth_event.dart
part of 'auth_bloc.dart';

@freezed
class AuthEvent with _$AuthEvent {
  const factory AuthEvent.checkRequested() = AuthCheckRequested;
  const factory AuthEvent.loginRequested({
    required String email,
    required String password,
  }) = AuthLoginRequested;
  const factory AuthEvent.registerRequested({
    required String name,
    required String email,
    required String password,
  }) = AuthRegisterRequested;
  const factory AuthEvent.logoutRequested() = AuthLogoutRequested;
  const factory AuthEvent.googleLoginRequested() = AuthGoogleLoginRequested;
  const factory AuthEvent.appleLoginRequested() = AuthAppleLoginRequested;
}

// lib/features/auth/presentation/bloc/auth_state.dart
part of 'auth_bloc.dart';

@freezed
class AuthState with _$AuthState {
  const factory AuthState.initial() = AuthInitial;
  const factory AuthState.loading() = AuthLoading;
  const factory AuthState.authenticated(User user) = AuthAuthenticated;
  const factory AuthState.unauthenticated() = AuthUnauthenticated;
  const factory AuthState.error(String message) = AuthError;
}
```

### Screens

```dart
// lib/features/auth/presentation/screens/splash_screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../bloc/auth_bloc.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  @override
  void initState() {
    super.initState();
    context.read<AuthBloc>().add(const AuthCheckRequested());
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.lock_outline,
              size: 80,
              color: Theme.of(context).colorScheme.primary,
            ),
            const SizedBox(height: 24),
            const CircularProgressIndicator(),
          ],
        ),
      ),
    );
  }
}

// lib/features/auth/presentation/screens/login_screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_form_builder/flutter_form_builder.dart';
import 'package:form_builder_validators/form_builder_validators.dart';
import 'package:go_router/go_router.dart';

import '../bloc/auth_bloc.dart';
import '../widgets/social_login_buttons.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormBuilderState>();
  bool _obscurePassword = true;

  void _login() {
    if (!_formKey.currentState!.saveAndValidate()) return;

    final values = _formKey.currentState!.value;
    context.read<AuthBloc>().add(
          AuthLoginRequested(
            email: values['email'],
            password: values['password'],
          ),
        );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: BlocListener<AuthBloc, AuthState>(
        listener: (context, state) {
          if (state is AuthError) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text(state.message),
                backgroundColor: Theme.of(context).colorScheme.error,
              ),
            );
          }
        },
        child: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: FormBuilder(
                key: _formKey,
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Icon(
                      Icons.lock_outline,
                      size: 64,
                      color: Theme.of(context).colorScheme.primary,
                    ),
                    const SizedBox(height: 24),
                    Text(
                      'Welcome Back',
                      style: Theme.of(context).textTheme.headlineMedium,
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Sign in to continue',
                      style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                            color: Theme.of(context).colorScheme.outline,
                          ),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 32),
                    FormBuilderTextField(
                      name: 'email',
                      decoration: const InputDecoration(
                        labelText: 'Email',
                        prefixIcon: Icon(Icons.email_outlined),
                        border: OutlineInputBorder(),
                      ),
                      keyboardType: TextInputType.emailAddress,
                      textInputAction: TextInputAction.next,
                      validator: FormBuilderValidators.compose([
                        FormBuilderValidators.required(),
                        FormBuilderValidators.email(),
                      ]),
                    ),
                    const SizedBox(height: 16),
                    FormBuilderTextField(
                      name: 'password',
                      decoration: InputDecoration(
                        labelText: 'Password',
                        prefixIcon: const Icon(Icons.lock_outlined),
                        border: const OutlineInputBorder(),
                        suffixIcon: IconButton(
                          icon: Icon(
                            _obscurePassword
                                ? Icons.visibility_outlined
                                : Icons.visibility_off_outlined,
                          ),
                          onPressed: () {
                            setState(() {
                              _obscurePassword = !_obscurePassword;
                            });
                          },
                        ),
                      ),
                      obscureText: _obscurePassword,
                      textInputAction: TextInputAction.done,
                      onSubmitted: (_) => _login(),
                      validator: FormBuilderValidators.compose([
                        FormBuilderValidators.required(),
                        FormBuilderValidators.minLength(6),
                      ]),
                    ),
                    const SizedBox(height: 8),
                    Align(
                      alignment: Alignment.centerRight,
                      child: TextButton(
                        onPressed: () {
                          // Navigate to forgot password
                        },
                        child: const Text('Forgot Password?'),
                      ),
                    ),
                    const SizedBox(height: 16),
                    BlocBuilder<AuthBloc, AuthState>(
                      builder: (context, state) {
                        final isLoading = state is AuthLoading;
                        return FilledButton(
                          onPressed: isLoading ? null : _login,
                          child: isLoading
                              ? const SizedBox(
                                  height: 20,
                                  width: 20,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                  ),
                                )
                              : const Text('Sign In'),
                        );
                      },
                    ),
                    const SizedBox(height: 24),
                    Row(
                      children: [
                        const Expanded(child: Divider()),
                        Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 16),
                          child: Text(
                            'Or continue with',
                            style: Theme.of(context).textTheme.bodySmall,
                          ),
                        ),
                        const Expanded(child: Divider()),
                      ],
                    ),
                    const SizedBox(height: 24),
                    const SocialLoginButtons(),
                    const SizedBox(height: 24),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Text("Don't have an account?"),
                        TextButton(
                          onPressed: () => context.push('/register'),
                          child: const Text('Sign Up'),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

// lib/features/auth/presentation/screens/register_screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_form_builder/flutter_form_builder.dart';
import 'package:form_builder_validators/form_builder_validators.dart';
import 'package:go_router/go_router.dart';

import '../bloc/auth_bloc.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _formKey = GlobalKey<FormBuilderState>();
  bool _obscurePassword = true;

  void _register() {
    if (!_formKey.currentState!.saveAndValidate()) return;

    final values = _formKey.currentState!.value;
    context.read<AuthBloc>().add(
          AuthRegisterRequested(
            name: values['name'],
            email: values['email'],
            password: values['password'],
          ),
        );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(),
      body: BlocListener<AuthBloc, AuthState>(
        listener: (context, state) {
          if (state is AuthError) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text(state.message),
                backgroundColor: Theme.of(context).colorScheme.error,
              ),
            );
          }
        },
        child: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: FormBuilder(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Text(
                      'Create Account',
                      style: Theme.of(context).textTheme.headlineMedium,
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Sign up to get started',
                      style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                            color: Theme.of(context).colorScheme.outline,
                          ),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 32),
                    FormBuilderTextField(
                      name: 'name',
                      decoration: const InputDecoration(
                        labelText: 'Full Name',
                        prefixIcon: Icon(Icons.person_outlined),
                        border: OutlineInputBorder(),
                      ),
                      textInputAction: TextInputAction.next,
                      validator: FormBuilderValidators.compose([
                        FormBuilderValidators.required(),
                        FormBuilderValidators.minLength(2),
                      ]),
                    ),
                    const SizedBox(height: 16),
                    FormBuilderTextField(
                      name: 'email',
                      decoration: const InputDecoration(
                        labelText: 'Email',
                        prefixIcon: Icon(Icons.email_outlined),
                        border: OutlineInputBorder(),
                      ),
                      keyboardType: TextInputType.emailAddress,
                      textInputAction: TextInputAction.next,
                      validator: FormBuilderValidators.compose([
                        FormBuilderValidators.required(),
                        FormBuilderValidators.email(),
                      ]),
                    ),
                    const SizedBox(height: 16),
                    FormBuilderTextField(
                      name: 'password',
                      decoration: InputDecoration(
                        labelText: 'Password',
                        prefixIcon: const Icon(Icons.lock_outlined),
                        border: const OutlineInputBorder(),
                        suffixIcon: IconButton(
                          icon: Icon(
                            _obscurePassword
                                ? Icons.visibility_outlined
                                : Icons.visibility_off_outlined,
                          ),
                          onPressed: () {
                            setState(() {
                              _obscurePassword = !_obscurePassword;
                            });
                          },
                        ),
                      ),
                      obscureText: _obscurePassword,
                      textInputAction: TextInputAction.done,
                      onSubmitted: (_) => _register(),
                      validator: FormBuilderValidators.compose([
                        FormBuilderValidators.required(),
                        FormBuilderValidators.minLength(8),
                      ]),
                    ),
                    const SizedBox(height: 24),
                    BlocBuilder<AuthBloc, AuthState>(
                      builder: (context, state) {
                        final isLoading = state is AuthLoading;
                        return FilledButton(
                          onPressed: isLoading ? null : _register,
                          child: isLoading
                              ? const SizedBox(
                                  height: 20,
                                  width: 20,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                  ),
                                )
                              : const Text('Create Account'),
                        );
                      },
                    ),
                    const SizedBox(height: 24),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Text('Already have an account?'),
                        TextButton(
                          onPressed: () => context.pop(),
                          child: const Text('Sign In'),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
```

### Widgets

```dart
// lib/features/auth/presentation/widgets/social_login_buttons.dart
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../bloc/auth_bloc.dart';

class SocialLoginButtons extends StatelessWidget {
  const SocialLoginButtons({super.key});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        OutlinedButton.icon(
          onPressed: () {
            context.read<AuthBloc>().add(const AuthGoogleLoginRequested());
          },
          icon: Image.asset(
            'assets/icons/google.png',
            height: 24,
          ),
          label: const Text('Continue with Google'),
        ),
        if (Platform.isIOS) ...[
          const SizedBox(height: 12),
          OutlinedButton.icon(
            onPressed: () {
              context.read<AuthBloc>().add(const AuthAppleLoginRequested());
            },
            icon: const Icon(Icons.apple, size: 24),
            label: const Text('Continue with Apple'),
          ),
        ],
      ],
    );
  }
}
```

### Home Screen

```dart
// lib/features/home/presentation/screens/home_screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../auth/presentation/bloc/auth_bloc.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<AuthBloc, AuthState>(
      builder: (context, state) {
        final user = state is AuthAuthenticated ? state.user : null;

        return Scaffold(
          appBar: AppBar(
            title: const Text('Home'),
            actions: [
              IconButton(
                icon: const Icon(Icons.logout),
                onPressed: () {
                  showDialog(
                    context: context,
                    builder: (context) => AlertDialog(
                      title: const Text('Logout'),
                      content: const Text('Are you sure you want to logout?'),
                      actions: [
                        TextButton(
                          onPressed: () => Navigator.pop(context),
                          child: const Text('Cancel'),
                        ),
                        TextButton(
                          onPressed: () {
                            Navigator.pop(context);
                            context.read<AuthBloc>().add(
                                  const AuthLogoutRequested(),
                                );
                          },
                          child: const Text('Logout'),
                        ),
                      ],
                    ),
                  );
                },
              ),
            ],
          ),
          body: Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                CircleAvatar(
                  radius: 50,
                  backgroundImage: user?.avatarUrl != null
                      ? NetworkImage(user!.avatarUrl!)
                      : null,
                  child: user?.avatarUrl == null
                      ? Text(
                          user?.initials ?? '?',
                          style: Theme.of(context).textTheme.headlineMedium,
                        )
                      : null,
                ),
                const SizedBox(height: 16),
                Text(
                  'Welcome, ${user?.name ?? 'User'}!',
                  style: Theme.of(context).textTheme.headlineSmall,
                ),
                const SizedBox(height: 8),
                Text(
                  user?.email ?? '',
                  style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                        color: Theme.of(context).colorScheme.outline,
                      ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}
```

## App Entry Point

```dart
// lib/app.dart
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import 'core/di/injection.dart';
import 'core/router/app_router.dart';
import 'features/auth/presentation/bloc/auth_bloc.dart';

class App extends StatelessWidget {
  const App({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => getIt<AuthBloc>(),
      child: Builder(
        builder: (context) {
          final router = AppRouter(context.read<AuthBloc>()).router;
          return MaterialApp.router(
            title: 'Auth App',
            theme: ThemeData(
              colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
              useMaterial3: true,
            ),
            routerConfig: router,
          );
        },
      ),
    );
  }
}

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
// test/features/auth/presentation/bloc/auth_bloc_test.dart
import 'package:bloc_test/bloc_test.dart';
import 'package:dartz/dartz.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:auth_app/core/error/failures.dart';
import 'package:auth_app/features/auth/domain/entities/user.dart';
import 'package:auth_app/features/auth/domain/repositories/auth_repository.dart';
import 'package:auth_app/features/auth/domain/usecases/get_current_user.dart';
import 'package:auth_app/features/auth/domain/usecases/login.dart';
import 'package:auth_app/features/auth/domain/usecases/logout.dart';
import 'package:auth_app/features/auth/domain/usecases/register.dart';
import 'package:auth_app/features/auth/presentation/bloc/auth_bloc.dart';

class MockLogin extends Mock implements Login {}
class MockRegister extends Mock implements Register {}
class MockLogout extends Mock implements Logout {}
class MockGetCurrentUser extends Mock implements GetCurrentUser {}
class MockAuthRepository extends Mock implements AuthRepository {}

void main() {
  late AuthBloc bloc;
  late MockLogin mockLogin;
  late MockRegister mockRegister;
  late MockLogout mockLogout;
  late MockGetCurrentUser mockGetCurrentUser;
  late MockAuthRepository mockRepository;

  setUp(() {
    mockLogin = MockLogin();
    mockRegister = MockRegister();
    mockLogout = MockLogout();
    mockGetCurrentUser = MockGetCurrentUser();
    mockRepository = MockAuthRepository();
    bloc = AuthBloc(
      login: mockLogin,
      register: mockRegister,
      logout: mockLogout,
      getCurrentUser: mockGetCurrentUser,
      repository: mockRepository,
    );
  });

  tearDown(() => bloc.close());

  final tUser = User(
    id: '1',
    email: 'test@example.com',
    name: 'Test User',
    createdAt: DateTime.now(),
  );

  group('AuthCheckRequested', () {
    blocTest<AuthBloc, AuthState>(
      'emits [loading, authenticated] when user is logged in',
      build: () {
        when(() => mockRepository.isAuthenticated())
            .thenAnswer((_) async => true);
        when(() => mockGetCurrentUser())
            .thenAnswer((_) async => Right(tUser));
        return bloc;
      },
      act: (bloc) => bloc.add(const AuthCheckRequested()),
      expect: () => [
        const AuthLoading(),
        AuthAuthenticated(tUser),
      ],
    );

    blocTest<AuthBloc, AuthState>(
      'emits [loading, unauthenticated] when no token',
      build: () {
        when(() => mockRepository.isAuthenticated())
            .thenAnswer((_) async => false);
        return bloc;
      },
      act: (bloc) => bloc.add(const AuthCheckRequested()),
      expect: () => [
        const AuthLoading(),
        const AuthUnauthenticated(),
      ],
    );
  });

  group('AuthLoginRequested', () {
    blocTest<AuthBloc, AuthState>(
      'emits [loading, authenticated] when login succeeds',
      build: () {
        when(() => mockLogin(email: any(named: 'email'), password: any(named: 'password')))
            .thenAnswer((_) async => Right(tUser));
        return bloc;
      },
      act: (bloc) => bloc.add(const AuthLoginRequested(
        email: 'test@example.com',
        password: 'password123',
      )),
      expect: () => [
        const AuthLoading(),
        AuthAuthenticated(tUser),
      ],
    );

    blocTest<AuthBloc, AuthState>(
      'emits [loading, error] when login fails',
      build: () {
        when(() => mockLogin(email: any(named: 'email'), password: any(named: 'password')))
            .thenAnswer((_) async => const Left(AuthFailure(message: 'Invalid credentials')));
        return bloc;
      },
      act: (bloc) => bloc.add(const AuthLoginRequested(
        email: 'test@example.com',
        password: 'wrong',
      )),
      expect: () => [
        const AuthLoading(),
        isA<AuthError>(),
      ],
    );
  });

  group('AuthLogoutRequested', () {
    blocTest<AuthBloc, AuthState>(
      'emits [loading, unauthenticated] when logout',
      build: () {
        when(() => mockLogout())
            .thenAnswer((_) async => const Right(null));
        return bloc;
      },
      act: (bloc) => bloc.add(const AuthLogoutRequested()),
      expect: () => [
        const AuthLoading(),
        const AuthUnauthenticated(),
      ],
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

## Security Considerations

1. **Token Storage**: Uses flutter_secure_storage with encrypted shared preferences
2. **Token Refresh**: Automatic token refresh on 401 responses
3. **Biometric Auth**: Can be added using local_auth package
4. **SSL Pinning**: Add certificate pinning for production
5. **Input Validation**: Server-side validation + client-side using form_builder_validators
