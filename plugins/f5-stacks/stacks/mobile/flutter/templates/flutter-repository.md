---
name: flutter-repository
description: Template for Flutter repository pattern
applies_to: flutter
variables:
  - name: entity_name
    description: Name of the entity (PascalCase)
  - name: feature_name
    description: Feature folder name (snake_case)
---

# Flutter Repository Template

## Domain Layer - Abstract Repository

```dart
// lib/features/{{feature_name}}/domain/repositories/{{feature_name}}_repository.dart

import 'package:dartz/dartz.dart';

import '../../../../core/error/failures.dart';
import '../entities/{{feature_name}}.dart';

abstract class {{entity_name}}Repository {
  Future<Either<Failure, List<{{entity_name}}>>> getAll();
  Future<Either<Failure, {{entity_name}}>> getById(String id);
  Future<Either<Failure, {{entity_name}}>> create({{entity_name}} entity);
  Future<Either<Failure, {{entity_name}}>> update({{entity_name}} entity);
  Future<Either<Failure, void>> delete(String id);
  Future<Either<Failure, List<{{entity_name}}>>> search(String query);
}
```

## Data Layer - Repository Implementation

```dart
// lib/features/{{feature_name}}/data/repositories/{{feature_name}}_repository_impl.dart

import 'package:dartz/dartz.dart';
import 'package:injectable/injectable.dart';

import '../../../../core/error/exceptions.dart';
import '../../../../core/error/failures.dart';
import '../../../../core/network/network_info.dart';
import '../../domain/entities/{{feature_name}}.dart';
import '../../domain/repositories/{{feature_name}}_repository.dart';
import '../datasources/{{feature_name}}_local_datasource.dart';
import '../datasources/{{feature_name}}_remote_datasource.dart';

@LazySingleton(as: {{entity_name}}Repository)
class {{entity_name}}RepositoryImpl implements {{entity_name}}Repository {
  final {{entity_name}}RemoteDataSource _remoteDataSource;
  final {{entity_name}}LocalDataSource _localDataSource;
  final NetworkInfo _networkInfo;

  {{entity_name}}RepositoryImpl({
    required {{entity_name}}RemoteDataSource remoteDataSource,
    required {{entity_name}}LocalDataSource localDataSource,
    required NetworkInfo networkInfo,
  })  : _remoteDataSource = remoteDataSource,
        _localDataSource = localDataSource,
        _networkInfo = networkInfo;

  @override
  Future<Either<Failure, List<{{entity_name}}>>> getAll() async {
    if (await _networkInfo.isConnected) {
      try {
        final remoteData = await _remoteDataSource.getAll();
        await _localDataSource.cacheAll(remoteData);
        return Right(remoteData.map((m) => m.toEntity()).toList());
      } on ServerException catch (e) {
        return Left(ServerFailure(message: e.message));
      }
    } else {
      try {
        final localData = await _localDataSource.getAll();
        return Right(localData.map((m) => m.toEntity()).toList());
      } on CacheException {
        return const Left(CacheFailure(message: 'No cached data available'));
      }
    }
  }

  @override
  Future<Either<Failure, {{entity_name}}>> getById(String id) async {
    if (await _networkInfo.isConnected) {
      try {
        final remoteData = await _remoteDataSource.getById(id);
        await _localDataSource.cache(remoteData);
        return Right(remoteData.toEntity());
      } on ServerException catch (e) {
        return Left(ServerFailure(message: e.message));
      } on NotFoundException {
        return const Left(NotFoundFailure(message: 'Item not found'));
      }
    } else {
      try {
        final localData = await _localDataSource.getById(id);
        return Right(localData.toEntity());
      } on CacheException {
        return const Left(CacheFailure(message: 'Item not found in cache'));
      }
    }
  }

  @override
  Future<Either<Failure, {{entity_name}}>> create({{entity_name}} entity) async {
    try {
      final model = {{entity_name}}Model.fromEntity(entity);
      final result = await _remoteDataSource.create(model);
      await _localDataSource.cache(result);
      return Right(result.toEntity());
    } on ServerException catch (e) {
      return Left(ServerFailure(message: e.message));
    } on ValidationException catch (e) {
      return Left(ValidationFailure(message: e.message, errors: e.errors));
    }
  }

  @override
  Future<Either<Failure, {{entity_name}}>> update({{entity_name}} entity) async {
    try {
      final model = {{entity_name}}Model.fromEntity(entity);
      final result = await _remoteDataSource.update(model);
      await _localDataSource.cache(result);
      return Right(result.toEntity());
    } on ServerException catch (e) {
      return Left(ServerFailure(message: e.message));
    } on NotFoundException {
      return const Left(NotFoundFailure(message: 'Item not found'));
    }
  }

  @override
  Future<Either<Failure, void>> delete(String id) async {
    try {
      await _remoteDataSource.delete(id);
      await _localDataSource.delete(id);
      return const Right(null);
    } on ServerException catch (e) {
      return Left(ServerFailure(message: e.message));
    } on NotFoundException {
      return const Left(NotFoundFailure(message: 'Item not found'));
    }
  }

  @override
  Future<Either<Failure, List<{{entity_name}}>>> search(String query) async {
    try {
      final results = await _remoteDataSource.search(query);
      return Right(results.map((m) => m.toEntity()).toList());
    } on ServerException catch (e) {
      return Left(ServerFailure(message: e.message));
    }
  }
}
```

## Remote Data Source

```dart
// lib/features/{{feature_name}}/data/datasources/{{feature_name}}_remote_datasource.dart

import 'package:dio/dio.dart';
import 'package:injectable/injectable.dart';

import '../../../../core/error/exceptions.dart';
import '../models/{{feature_name}}_model.dart';

abstract class {{entity_name}}RemoteDataSource {
  Future<List<{{entity_name}}Model>> getAll();
  Future<{{entity_name}}Model> getById(String id);
  Future<{{entity_name}}Model> create({{entity_name}}Model model);
  Future<{{entity_name}}Model> update({{entity_name}}Model model);
  Future<void> delete(String id);
  Future<List<{{entity_name}}Model>> search(String query);
}

@LazySingleton(as: {{entity_name}}RemoteDataSource)
class {{entity_name}}RemoteDataSourceImpl implements {{entity_name}}RemoteDataSource {
  final Dio _dio;
  static const _basePath = '/{{feature_name}}s';

  {{entity_name}}RemoteDataSourceImpl(this._dio);

  @override
  Future<List<{{entity_name}}Model>> getAll() async {
    try {
      final response = await _dio.get(_basePath);
      return (response.data['data'] as List)
          .map((json) => {{entity_name}}Model.fromJson(json))
          .toList();
    } on DioException catch (e) {
      throw ServerException.fromDioError(e);
    }
  }

  @override
  Future<{{entity_name}}Model> getById(String id) async {
    try {
      final response = await _dio.get('$_basePath/$id');
      return {{entity_name}}Model.fromJson(response.data['data']);
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) {
        throw NotFoundException();
      }
      throw ServerException.fromDioError(e);
    }
  }

  @override
  Future<{{entity_name}}Model> create({{entity_name}}Model model) async {
    try {
      final response = await _dio.post(
        _basePath,
        data: model.toJson(),
      );
      return {{entity_name}}Model.fromJson(response.data['data']);
    } on DioException catch (e) {
      if (e.response?.statusCode == 422) {
        throw ValidationException.fromResponse(e.response?.data);
      }
      throw ServerException.fromDioError(e);
    }
  }

  @override
  Future<{{entity_name}}Model> update({{entity_name}}Model model) async {
    try {
      final response = await _dio.put(
        '$_basePath/${model.id}',
        data: model.toJson(),
      );
      return {{entity_name}}Model.fromJson(response.data['data']);
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) {
        throw NotFoundException();
      }
      if (e.response?.statusCode == 422) {
        throw ValidationException.fromResponse(e.response?.data);
      }
      throw ServerException.fromDioError(e);
    }
  }

  @override
  Future<void> delete(String id) async {
    try {
      await _dio.delete('$_basePath/$id');
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) {
        throw NotFoundException();
      }
      throw ServerException.fromDioError(e);
    }
  }

  @override
  Future<List<{{entity_name}}Model>> search(String query) async {
    try {
      final response = await _dio.get(
        '$_basePath/search',
        queryParameters: {'q': query},
      );
      return (response.data['data'] as List)
          .map((json) => {{entity_name}}Model.fromJson(json))
          .toList();
    } on DioException catch (e) {
      throw ServerException.fromDioError(e);
    }
  }
}
```

## Local Data Source

```dart
// lib/features/{{feature_name}}/data/datasources/{{feature_name}}_local_datasource.dart

import 'package:hive/hive.dart';
import 'package:injectable/injectable.dart';

import '../../../../core/error/exceptions.dart';
import '../models/{{feature_name}}_model.dart';

abstract class {{entity_name}}LocalDataSource {
  Future<List<{{entity_name}}Model>> getAll();
  Future<{{entity_name}}Model> getById(String id);
  Future<void> cache({{entity_name}}Model model);
  Future<void> cacheAll(List<{{entity_name}}Model> models);
  Future<void> delete(String id);
  Future<void> clear();
}

@LazySingleton(as: {{entity_name}}LocalDataSource)
class {{entity_name}}LocalDataSourceImpl implements {{entity_name}}LocalDataSource {
  final Box<{{entity_name}}Model> _box;

  {{entity_name}}LocalDataSourceImpl(this._box);

  @override
  Future<List<{{entity_name}}Model>> getAll() async {
    if (_box.isEmpty) {
      throw CacheException();
    }
    return _box.values.toList();
  }

  @override
  Future<{{entity_name}}Model> getById(String id) async {
    final model = _box.get(id);
    if (model == null) {
      throw CacheException();
    }
    return model;
  }

  @override
  Future<void> cache({{entity_name}}Model model) async {
    await _box.put(model.id, model);
  }

  @override
  Future<void> cacheAll(List<{{entity_name}}Model> models) async {
    final entries = {for (var m in models) m.id: m};
    await _box.putAll(entries);
  }

  @override
  Future<void> delete(String id) async {
    await _box.delete(id);
  }

  @override
  Future<void> clear() async {
    await _box.clear();
  }
}
```

## Failures

```dart
// lib/core/error/failures.dart

import 'package:freezed_annotation/freezed_annotation.dart';

part 'failures.freezed.dart';

@freezed
class Failure with _$Failure {
  const factory Failure.server({required String message}) = ServerFailure;
  const factory Failure.cache({required String message}) = CacheFailure;
  const factory Failure.network({required String message}) = NetworkFailure;
  const factory Failure.notFound({required String message}) = NotFoundFailure;
  const factory Failure.validation({
    required String message,
    @Default({}) Map<String, List<String>> errors,
  }) = ValidationFailure;
  const factory Failure.unauthorized({required String message}) = UnauthorizedFailure;
}
```

## Exceptions

```dart
// lib/core/error/exceptions.dart

import 'package:dio/dio.dart';

class ServerException implements Exception {
  final String message;
  final int? statusCode;

  ServerException({required this.message, this.statusCode});

  factory ServerException.fromDioError(DioException error) {
    return ServerException(
      message: error.response?.data['message'] ?? error.message ?? 'Server error',
      statusCode: error.response?.statusCode,
    );
  }
}

class CacheException implements Exception {}

class NotFoundException implements Exception {}

class ValidationException implements Exception {
  final String message;
  final Map<String, List<String>> errors;

  ValidationException({required this.message, this.errors = const {}});

  factory ValidationException.fromResponse(Map<String, dynamic>? data) {
    return ValidationException(
      message: data?['message'] ?? 'Validation error',
      errors: (data?['errors'] as Map<String, dynamic>?)?.map(
            (key, value) => MapEntry(key, List<String>.from(value)),
          ) ??
          {},
    );
  }
}
```

## Usage

Replace `{{entity_name}}` with actual entity name (e.g., `Product`, `User`, `Order`)
Replace `{{feature_name}}` with feature folder name (e.g., `product`, `user`, `order`)
