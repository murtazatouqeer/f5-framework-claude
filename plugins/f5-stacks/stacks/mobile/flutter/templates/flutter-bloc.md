---
name: flutter-bloc
description: Template for Flutter BLoC pattern
applies_to: flutter
variables:
  - name: bloc_name
    description: Name of the BLoC (PascalCase)
  - name: feature_name
    description: Feature folder name (snake_case)
---

# Flutter BLoC Template

## BLoC with Freezed Events and States

### Events

```dart
// lib/features/{{feature_name}}/presentation/bloc/{{feature_name}}_event.dart

part of '{{feature_name}}_bloc.dart';

@freezed
class {{bloc_name}}Event with _${{bloc_name}}Event {
  const factory {{bloc_name}}Event.started() = {{bloc_name}}Started;
  const factory {{bloc_name}}Event.refreshed() = {{bloc_name}}Refreshed;
  const factory {{bloc_name}}Event.itemSelected(String id) = {{bloc_name}}ItemSelected;
  const factory {{bloc_name}}Event.itemDeleted(String id) = {{bloc_name}}ItemDeleted;
  const factory {{bloc_name}}Event.searchQueryChanged(String query) = {{bloc_name}}SearchQueryChanged;
  const factory {{bloc_name}}Event.loadMore() = {{bloc_name}}LoadMore;
}
```

### States

```dart
// lib/features/{{feature_name}}/presentation/bloc/{{feature_name}}_state.dart

part of '{{feature_name}}_bloc.dart';

@freezed
class {{bloc_name}}State with _${{bloc_name}}State {
  const factory {{bloc_name}}State.initial() = {{bloc_name}}Initial;
  const factory {{bloc_name}}State.loading() = {{bloc_name}}Loading;
  const factory {{bloc_name}}State.success({
    required List<{{bloc_name}}Item> items,
    @Default(false) bool hasReachedMax,
    String? selectedId,
  }) = {{bloc_name}}Success;
  const factory {{bloc_name}}State.error({required String message}) = {{bloc_name}}Error;
}
```

### BLoC

```dart
// lib/features/{{feature_name}}/presentation/bloc/{{feature_name}}_bloc.dart

import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:injectable/injectable.dart';

import '../../domain/entities/{{feature_name}}_item.dart';
import '../../domain/repositories/{{feature_name}}_repository.dart';

part '{{feature_name}}_bloc.freezed.dart';
part '{{feature_name}}_event.dart';
part '{{feature_name}}_state.dart';

@injectable
class {{bloc_name}}Bloc extends Bloc<{{bloc_name}}Event, {{bloc_name}}State> {
  final {{bloc_name}}Repository _repository;

  {{bloc_name}}Bloc(this._repository) : super(const {{bloc_name}}Initial()) {
    on<{{bloc_name}}Started>(_onStarted);
    on<{{bloc_name}}Refreshed>(_onRefreshed);
    on<{{bloc_name}}ItemSelected>(_onItemSelected);
    on<{{bloc_name}}ItemDeleted>(_onItemDeleted);
    on<{{bloc_name}}SearchQueryChanged>(
      _onSearchQueryChanged,
      transformer: debounce(const Duration(milliseconds: 300)),
    );
    on<{{bloc_name}}LoadMore>(_onLoadMore);
  }

  Future<void> _onStarted(
    {{bloc_name}}Started event,
    Emitter<{{bloc_name}}State> emit,
  ) async {
    emit(const {{bloc_name}}Loading());

    try {
      final items = await _repository.getAll();
      emit({{bloc_name}}Success(items: items));
    } catch (e) {
      emit({{bloc_name}}Error(message: e.toString()));
    }
  }

  Future<void> _onRefreshed(
    {{bloc_name}}Refreshed event,
    Emitter<{{bloc_name}}State> emit,
  ) async {
    try {
      final items = await _repository.getAll();
      emit({{bloc_name}}Success(items: items));
    } catch (e) {
      emit({{bloc_name}}Error(message: e.toString()));
    }
  }

  void _onItemSelected(
    {{bloc_name}}ItemSelected event,
    Emitter<{{bloc_name}}State> emit,
  ) {
    state.mapOrNull(
      success: (state) {
        emit(state.copyWith(selectedId: event.id));
      },
    );
  }

  Future<void> _onItemDeleted(
    {{bloc_name}}ItemDeleted event,
    Emitter<{{bloc_name}}State> emit,
  ) async {
    await state.mapOrNull(
      success: (state) async {
        try {
          await _repository.delete(event.id);
          final updatedItems = state.items
              .where((item) => item.id != event.id)
              .toList();
          emit(state.copyWith(items: updatedItems));
        } catch (e) {
          // Handle error silently or emit error state
        }
      },
    );
  }

  Future<void> _onSearchQueryChanged(
    {{bloc_name}}SearchQueryChanged event,
    Emitter<{{bloc_name}}State> emit,
  ) async {
    emit(const {{bloc_name}}Loading());

    try {
      final items = await _repository.search(event.query);
      emit({{bloc_name}}Success(items: items));
    } catch (e) {
      emit({{bloc_name}}Error(message: e.toString()));
    }
  }

  Future<void> _onLoadMore(
    {{bloc_name}}LoadMore event,
    Emitter<{{bloc_name}}State> emit,
  ) async {
    await state.mapOrNull(
      success: (state) async {
        if (state.hasReachedMax) return;

        try {
          final moreItems = await _repository.getMore(
            offset: state.items.length,
          );

          emit(state.copyWith(
            items: [...state.items, ...moreItems],
            hasReachedMax: moreItems.isEmpty,
          ));
        } catch (e) {
          // Handle error
        }
      },
    );
  }

  EventTransformer<E> debounce<E>(Duration duration) {
    return (events, mapper) => events.debounceTime(duration).flatMap(mapper);
  }
}
```

## Cubit (Simpler Alternative)

```dart
// lib/features/{{feature_name}}/presentation/cubit/{{feature_name}}_cubit.dart

import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:injectable/injectable.dart';

import '../../domain/entities/{{feature_name}}_item.dart';
import '../../domain/repositories/{{feature_name}}_repository.dart';

part '{{feature_name}}_cubit.freezed.dart';
part '{{feature_name}}_state.dart';

@injectable
class {{bloc_name}}Cubit extends Cubit<{{bloc_name}}State> {
  final {{bloc_name}}Repository _repository;

  {{bloc_name}}Cubit(this._repository) : super(const {{bloc_name}}State());

  Future<void> load() async {
    emit(state.copyWith(status: {{bloc_name}}Status.loading));

    try {
      final items = await _repository.getAll();
      emit(state.copyWith(
        status: {{bloc_name}}Status.success,
        items: items,
      ));
    } catch (e) {
      emit(state.copyWith(
        status: {{bloc_name}}Status.error,
        errorMessage: e.toString(),
      ));
    }
  }

  Future<void> refresh() async {
    try {
      final items = await _repository.getAll();
      emit(state.copyWith(items: items));
    } catch (e) {
      emit(state.copyWith(
        status: {{bloc_name}}Status.error,
        errorMessage: e.toString(),
      ));
    }
  }

  void selectItem(String id) {
    emit(state.copyWith(selectedId: id));
  }

  Future<void> deleteItem(String id) async {
    try {
      await _repository.delete(id);
      final updatedItems = state.items
          .where((item) => item.id != id)
          .toList();
      emit(state.copyWith(items: updatedItems));
    } catch (e) {
      // Handle error
    }
  }
}

// State
@freezed
class {{bloc_name}}State with _${{bloc_name}}State {
  const factory {{bloc_name}}State({
    @Default({{bloc_name}}Status.initial) {{bloc_name}}Status status,
    @Default([]) List<{{bloc_name}}Item> items,
    String? selectedId,
    String? errorMessage,
  }) = _{{bloc_name}}State;
}

enum {{bloc_name}}Status { initial, loading, success, error }
```

## Form BLoC

```dart
// lib/features/{{feature_name}}/presentation/bloc/{{feature_name}}_form_bloc.dart

import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:freezed_annotation/freezed_annotation.dart';

part '{{feature_name}}_form_bloc.freezed.dart';
part '{{feature_name}}_form_event.dart';
part '{{feature_name}}_form_state.dart';

class {{bloc_name}}FormBloc extends Bloc<{{bloc_name}}FormEvent, {{bloc_name}}FormState> {
  final {{bloc_name}}Repository _repository;

  {{bloc_name}}FormBloc(this._repository) : super(const {{bloc_name}}FormState()) {
    on<{{bloc_name}}NameChanged>(_onNameChanged);
    on<{{bloc_name}}DescriptionChanged>(_onDescriptionChanged);
    on<{{bloc_name}}FormSubmitted>(_onFormSubmitted);
  }

  void _onNameChanged(
    {{bloc_name}}NameChanged event,
    Emitter<{{bloc_name}}FormState> emit,
  ) {
    final nameError = _validateName(event.name);
    emit(state.copyWith(
      name: event.name,
      nameError: nameError,
    ));
  }

  void _onDescriptionChanged(
    {{bloc_name}}DescriptionChanged event,
    Emitter<{{bloc_name}}FormState> emit,
  ) {
    emit(state.copyWith(description: event.description));
  }

  Future<void> _onFormSubmitted(
    {{bloc_name}}FormSubmitted event,
    Emitter<{{bloc_name}}FormState> emit,
  ) async {
    // Validate all fields
    final nameError = _validateName(state.name);

    if (nameError != null) {
      emit(state.copyWith(nameError: nameError));
      return;
    }

    emit(state.copyWith(status: FormStatus.submitting));

    try {
      await _repository.create(
        name: state.name,
        description: state.description,
      );
      emit(state.copyWith(status: FormStatus.success));
    } catch (e) {
      emit(state.copyWith(
        status: FormStatus.failure,
        errorMessage: e.toString(),
      ));
    }
  }

  String? _validateName(String name) {
    if (name.isEmpty) return 'Name is required';
    if (name.length < 3) return 'Name must be at least 3 characters';
    return null;
  }
}

// Events
@freezed
class {{bloc_name}}FormEvent with _${{bloc_name}}FormEvent {
  const factory {{bloc_name}}FormEvent.nameChanged(String name) = {{bloc_name}}NameChanged;
  const factory {{bloc_name}}FormEvent.descriptionChanged(String description) = {{bloc_name}}DescriptionChanged;
  const factory {{bloc_name}}FormEvent.submitted() = {{bloc_name}}FormSubmitted;
}

// State
@freezed
class {{bloc_name}}FormState with _${{bloc_name}}FormState {
  const factory {{bloc_name}}FormState({
    @Default('') String name,
    @Default('') String description,
    String? nameError,
    @Default(FormStatus.initial) FormStatus status,
    String? errorMessage,
  }) = _{{bloc_name}}FormState;

  const {{bloc_name}}FormState._();

  bool get isValid => name.isNotEmpty && nameError == null;
}

enum FormStatus { initial, submitting, success, failure }
```

## BLoC Provider Setup

```dart
// lib/features/{{feature_name}}/di/{{feature_name}}_providers.dart

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:get_it/get_it.dart';

import '../presentation/bloc/{{feature_name}}_bloc.dart';

class {{bloc_name}}Providers extends StatelessWidget {
  final Widget child;

  const {{bloc_name}}Providers({required this.child, super.key});

  @override
  Widget build(BuildContext context) {
    return MultiBlocProvider(
      providers: [
        BlocProvider(
          create: (_) => GetIt.I<{{bloc_name}}Bloc>()
            ..add(const {{bloc_name}}Started()),
        ),
      ],
      child: child,
    );
  }
}
```

## Usage

Replace `{{bloc_name}}` with actual BLoC name (e.g., `Products`, `Users`, `Auth`)
Replace `{{feature_name}}` with feature folder name (e.g., `products`, `users`, `auth`)

Run code generation:
```bash
dart run build_runner build --delete-conflicting-outputs
```
