---
name: flutter-model
description: Template for Flutter data models with Freezed
applies_to: flutter
variables:
  - name: model_name
    description: Name of the model (PascalCase)
  - name: feature_name
    description: Feature folder name (snake_case)
---

# Flutter Model Template

## Domain Entity

```dart
// lib/features/{{feature_name}}/domain/entities/{{feature_name}}.dart

import 'package:freezed_annotation/freezed_annotation.dart';

part '{{feature_name}}.freezed.dart';

@freezed
class {{model_name}} with _${{model_name}} {
  const factory {{model_name}}({
    required String id,
    required String name,
    String? description,
    required double price,
    String? imageUrl,
    required DateTime createdAt,
    DateTime? updatedAt,
  }) = _{{model_name}};

  const {{model_name}}._();

  // Computed properties
  bool get hasImage => imageUrl != null && imageUrl!.isNotEmpty;

  String get formattedPrice => '\$${price.toStringAsFixed(2)}';

  bool get isNew {
    final now = DateTime.now();
    return now.difference(createdAt).inDays < 7;
  }
}
```

## Data Model (with JSON serialization)

```dart
// lib/features/{{feature_name}}/data/models/{{feature_name}}_model.dart

import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:hive/hive.dart';

import '../../domain/entities/{{feature_name}}.dart';

part '{{feature_name}}_model.freezed.dart';
part '{{feature_name}}_model.g.dart';

@freezed
@HiveType(typeId: 1) // Unique type ID for Hive
class {{model_name}}Model with _${{model_name}}Model {
  const factory {{model_name}}Model({
    @HiveField(0) required String id,
    @HiveField(1) required String name,
    @HiveField(2) String? description,
    @HiveField(3) required double price,
    @HiveField(4) @JsonKey(name: 'image_url') String? imageUrl,
    @HiveField(5) @JsonKey(name: 'created_at') required DateTime createdAt,
    @HiveField(6) @JsonKey(name: 'updated_at') DateTime? updatedAt,
  }) = _{{model_name}}Model;

  const {{model_name}}Model._();

  factory {{model_name}}Model.fromJson(Map<String, dynamic> json) =>
      _${{model_name}}ModelFromJson(json);

  // Convert to domain entity
  {{model_name}} toEntity() => {{model_name}}(
        id: id,
        name: name,
        description: description,
        price: price,
        imageUrl: imageUrl,
        createdAt: createdAt,
        updatedAt: updatedAt,
      );

  // Create from domain entity
  factory {{model_name}}Model.fromEntity({{model_name}} entity) => {{model_name}}Model(
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

## Model with Nested Objects

```dart
// lib/features/{{feature_name}}/data/models/{{feature_name}}_detail_model.dart

import 'package:freezed_annotation/freezed_annotation.dart';

part '{{feature_name}}_detail_model.freezed.dart';
part '{{feature_name}}_detail_model.g.dart';

@freezed
class {{model_name}}DetailModel with _${{model_name}}DetailModel {
  const factory {{model_name}}DetailModel({
    required String id,
    required String name,
    String? description,
    required double price,
    @JsonKey(name: 'image_url') String? imageUrl,
    required CategoryModel category,
    @Default([]) List<TagModel> tags,
    @Default([]) List<ReviewModel> reviews,
    @JsonKey(name: 'created_at') required DateTime createdAt,
    @JsonKey(name: 'updated_at') DateTime? updatedAt,
  }) = _{{model_name}}DetailModel;

  factory {{model_name}}DetailModel.fromJson(Map<String, dynamic> json) =>
      _${{model_name}}DetailModelFromJson(json);
}

@freezed
class CategoryModel with _$CategoryModel {
  const factory CategoryModel({
    required String id,
    required String name,
    String? slug,
  }) = _CategoryModel;

  factory CategoryModel.fromJson(Map<String, dynamic> json) =>
      _$CategoryModelFromJson(json);
}

@freezed
class TagModel with _$TagModel {
  const factory TagModel({
    required String id,
    required String name,
  }) = _TagModel;

  factory TagModel.fromJson(Map<String, dynamic> json) =>
      _$TagModelFromJson(json);
}

@freezed
class ReviewModel with _$ReviewModel {
  const factory ReviewModel({
    required String id,
    required String userId,
    @JsonKey(name: 'user_name') required String userName,
    required int rating,
    String? comment,
    @JsonKey(name: 'created_at') required DateTime createdAt,
  }) = _ReviewModel;

  factory ReviewModel.fromJson(Map<String, dynamic> json) =>
      _$ReviewModelFromJson(json);
}
```

## Model with Enums

```dart
// lib/features/{{feature_name}}/data/models/{{feature_name}}_status_model.dart

import 'package:freezed_annotation/freezed_annotation.dart';

part '{{feature_name}}_status_model.freezed.dart';
part '{{feature_name}}_status_model.g.dart';

@freezed
class OrderModel with _$OrderModel {
  const factory OrderModel({
    required String id,
    @JsonKey(name: 'order_number') required String orderNumber,
    required OrderStatus status,
    required double total,
    @Default([]) List<OrderItemModel> items,
    @JsonKey(name: 'shipping_address') ShippingAddressModel? shippingAddress,
    @JsonKey(name: 'created_at') required DateTime createdAt,
  }) = _OrderModel;

  factory OrderModel.fromJson(Map<String, dynamic> json) =>
      _$OrderModelFromJson(json);
}

@JsonEnum(valueField: 'value')
enum OrderStatus {
  @JsonValue('pending')
  pending('pending'),
  @JsonValue('processing')
  processing('processing'),
  @JsonValue('shipped')
  shipped('shipped'),
  @JsonValue('delivered')
  delivered('delivered'),
  @JsonValue('cancelled')
  cancelled('cancelled');

  final String value;
  const OrderStatus(this.value);
}

@freezed
class OrderItemModel with _$OrderItemModel {
  const factory OrderItemModel({
    required String id,
    @JsonKey(name: 'product_id') required String productId,
    @JsonKey(name: 'product_name') required String productName,
    required int quantity,
    required double price,
  }) = _OrderItemModel;

  factory OrderItemModel.fromJson(Map<String, dynamic> json) =>
      _$OrderItemModelFromJson(json);
}

@freezed
class ShippingAddressModel with _$ShippingAddressModel {
  const factory ShippingAddressModel({
    required String name,
    required String street,
    required String city,
    required String state,
    @JsonKey(name: 'postal_code') required String postalCode,
    required String country,
    String? phone,
  }) = _ShippingAddressModel;

  factory ShippingAddressModel.fromJson(Map<String, dynamic> json) =>
      _$ShippingAddressModelFromJson(json);
}
```

## Request/Response Models

```dart
// lib/features/{{feature_name}}/data/models/{{feature_name}}_request.dart

import 'package:freezed_annotation/freezed_annotation.dart';

part '{{feature_name}}_request.freezed.dart';
part '{{feature_name}}_request.g.dart';

@freezed
class Create{{model_name}}Request with _$Create{{model_name}}Request {
  const factory Create{{model_name}}Request({
    required String name,
    String? description,
    required double price,
    @JsonKey(name: 'category_id') required String categoryId,
    @JsonKey(name: 'image_url') String? imageUrl,
    @Default([]) List<String> tags,
  }) = _Create{{model_name}}Request;

  factory Create{{model_name}}Request.fromJson(Map<String, dynamic> json) =>
      _$Create{{model_name}}RequestFromJson(json);
}

@freezed
class Update{{model_name}}Request with _$Update{{model_name}}Request {
  const factory Update{{model_name}}Request({
    String? name,
    String? description,
    double? price,
    @JsonKey(name: 'category_id') String? categoryId,
    @JsonKey(name: 'image_url') String? imageUrl,
    List<String>? tags,
  }) = _Update{{model_name}}Request;

  factory Update{{model_name}}Request.fromJson(Map<String, dynamic> json) =>
      _$Update{{model_name}}RequestFromJson(json);
}

// lib/features/{{feature_name}}/data/models/{{feature_name}}_response.dart

@freezed
class PaginatedResponse<T> with _$PaginatedResponse<T> {
  const factory PaginatedResponse({
    required List<T> data,
    required PaginationMeta meta,
  }) = _PaginatedResponse<T>;

  factory PaginatedResponse.fromJson(
    Map<String, dynamic> json,
    T Function(Object?) fromJsonT,
  ) =>
      _$PaginatedResponseFromJson(json, fromJsonT);
}

@freezed
class PaginationMeta with _$PaginationMeta {
  const factory PaginationMeta({
    @JsonKey(name: 'current_page') required int currentPage,
    @JsonKey(name: 'last_page') required int lastPage,
    @JsonKey(name: 'per_page') required int perPage,
    required int total,
  }) = _PaginationMeta;

  const PaginationMeta._();

  bool get hasMorePages => currentPage < lastPage;

  factory PaginationMeta.fromJson(Map<String, dynamic> json) =>
      _$PaginationMetaFromJson(json);
}
```

## Custom JSON Converters

```dart
// lib/core/utils/json_converters.dart

import 'package:freezed_annotation/freezed_annotation.dart';

class DateTimeConverter implements JsonConverter<DateTime, String> {
  const DateTimeConverter();

  @override
  DateTime fromJson(String json) => DateTime.parse(json);

  @override
  String toJson(DateTime object) => object.toIso8601String();
}

class NullableDateTimeConverter implements JsonConverter<DateTime?, String?> {
  const NullableDateTimeConverter();

  @override
  DateTime? fromJson(String? json) => json != null ? DateTime.parse(json) : null;

  @override
  String? toJson(DateTime? object) => object?.toIso8601String();
}

class DurationConverter implements JsonConverter<Duration, int> {
  const DurationConverter();

  @override
  Duration fromJson(int json) => Duration(seconds: json);

  @override
  int toJson(Duration object) => object.inSeconds;
}

// Usage
@freezed
class EventModel with _$EventModel {
  const factory EventModel({
    required String id,
    required String title,
    @DateTimeConverter() required DateTime startTime,
    @DateTimeConverter() required DateTime endTime,
    @DurationConverter() required Duration duration,
  }) = _EventModel;

  factory EventModel.fromJson(Map<String, dynamic> json) =>
      _$EventModelFromJson(json);
}
```

## Usage

Replace `{{model_name}}` with actual model name (e.g., `Product`, `User`, `Order`)
Replace `{{feature_name}}` with feature folder name (e.g., `product`, `user`, `order`)

Run code generation:
```bash
dart run build_runner build --delete-conflicting-outputs
```
