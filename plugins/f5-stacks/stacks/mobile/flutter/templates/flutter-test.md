---
name: flutter-test
description: Template for Flutter tests
applies_to: flutter
variables:
  - name: test_name
    description: Name of the test subject (PascalCase)
  - name: feature_name
    description: Feature folder name (snake_case)
---

# Flutter Test Template

## Unit Test

```dart
// test/features/{{feature_name}}/domain/usecases/get_{{feature_name}}_test.dart

import 'package:dartz/dartz.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:app/features/{{feature_name}}/domain/entities/{{feature_name}}.dart';
import 'package:app/features/{{feature_name}}/domain/repositories/{{feature_name}}_repository.dart';
import 'package:app/features/{{feature_name}}/domain/usecases/get_{{feature_name}}.dart';

class Mock{{test_name}}Repository extends Mock implements {{test_name}}Repository {}

void main() {
  late Get{{test_name}} useCase;
  late Mock{{test_name}}Repository mockRepository;

  setUp(() {
    mockRepository = Mock{{test_name}}Repository();
    useCase = Get{{test_name}}(mockRepository);
  });

  group('Get{{test_name}}', () {
    final t{{test_name}} = {{test_name}}(
      id: '1',
      name: 'Test {{test_name}}',
      createdAt: DateTime.now(),
    );

    test('should get {{feature_name}} from repository', () async {
      // Arrange
      when(() => mockRepository.getById(any()))
          .thenAnswer((_) async => Right(t{{test_name}}));

      // Act
      final result = await useCase(const Params(id: '1'));

      // Assert
      expect(result, Right(t{{test_name}}));
      verify(() => mockRepository.getById('1')).called(1);
      verifyNoMoreInteractions(mockRepository);
    });

    test('should return failure when repository fails', () async {
      // Arrange
      when(() => mockRepository.getById(any()))
          .thenAnswer((_) async => const Left(ServerFailure(message: 'Error')));

      // Act
      final result = await useCase(const Params(id: '1'));

      // Assert
      expect(result, const Left(ServerFailure(message: 'Error')));
    });
  });
}
```

## BLoC Test

```dart
// test/features/{{feature_name}}/presentation/bloc/{{feature_name}}_bloc_test.dart

import 'package:bloc_test/bloc_test.dart';
import 'package:dartz/dartz.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:app/features/{{feature_name}}/domain/entities/{{feature_name}}.dart';
import 'package:app/features/{{feature_name}}/domain/repositories/{{feature_name}}_repository.dart';
import 'package:app/features/{{feature_name}}/presentation/bloc/{{feature_name}}_bloc.dart';

class Mock{{test_name}}Repository extends Mock implements {{test_name}}Repository {}

void main() {
  late {{test_name}}Bloc bloc;
  late Mock{{test_name}}Repository mockRepository;

  setUp(() {
    mockRepository = Mock{{test_name}}Repository();
    bloc = {{test_name}}Bloc(mockRepository);
  });

  tearDown(() {
    bloc.close();
  });

  final t{{test_name}}List = [
    {{test_name}}(id: '1', name: 'Test 1', createdAt: DateTime.now()),
    {{test_name}}(id: '2', name: 'Test 2', createdAt: DateTime.now()),
  ];

  group('{{test_name}}Bloc', () {
    test('initial state is {{test_name}}Initial', () {
      expect(bloc.state, const {{test_name}}Initial());
    });

    blocTest<{{test_name}}Bloc, {{test_name}}State>(
      'emits [Loading, Success] when Started is added and getAll succeeds',
      build: () {
        when(() => mockRepository.getAll())
            .thenAnswer((_) async => Right(t{{test_name}}List));
        return bloc;
      },
      act: (bloc) => bloc.add(const {{test_name}}Started()),
      expect: () => [
        const {{test_name}}Loading(),
        {{test_name}}Success(items: t{{test_name}}List),
      ],
      verify: (_) {
        verify(() => mockRepository.getAll()).called(1);
      },
    );

    blocTest<{{test_name}}Bloc, {{test_name}}State>(
      'emits [Loading, Error] when Started is added and getAll fails',
      build: () {
        when(() => mockRepository.getAll())
            .thenAnswer((_) async => const Left(ServerFailure(message: 'Error')));
        return bloc;
      },
      act: (bloc) => bloc.add(const {{test_name}}Started()),
      expect: () => [
        const {{test_name}}Loading(),
        const {{test_name}}Error(message: 'Error'),
      ],
    );

    blocTest<{{test_name}}Bloc, {{test_name}}State>(
      'emits updated state when ItemSelected is added',
      build: () => bloc,
      seed: () => {{test_name}}Success(items: t{{test_name}}List),
      act: (bloc) => bloc.add(const {{test_name}}ItemSelected('1')),
      expect: () => [
        {{test_name}}Success(items: t{{test_name}}List, selectedId: '1'),
      ],
    );

    blocTest<{{test_name}}Bloc, {{test_name}}State>(
      'emits state with item removed when ItemDeleted is added',
      build: () {
        when(() => mockRepository.delete(any()))
            .thenAnswer((_) async => const Right(null));
        return bloc;
      },
      seed: () => {{test_name}}Success(items: t{{test_name}}List),
      act: (bloc) => bloc.add(const {{test_name}}ItemDeleted('1')),
      expect: () => [
        {{test_name}}Success(items: [t{{test_name}}List[1]]),
      ],
      verify: (_) {
        verify(() => mockRepository.delete('1')).called(1);
      },
    );
  });
}
```

## Widget Test

```dart
// test/features/{{feature_name}}/presentation/widgets/{{feature_name}}_card_test.dart

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:app/features/{{feature_name}}/domain/entities/{{feature_name}}.dart';
import 'package:app/features/{{feature_name}}/presentation/widgets/{{feature_name}}_card.dart';

void main() {
  final t{{test_name}} = {{test_name}}(
    id: '1',
    name: 'Test {{test_name}}',
    description: 'Test description',
    price: 19.99,
    createdAt: DateTime.now(),
  );

  group('{{test_name}}Card', () {
    testWidgets('displays {{feature_name}} information', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: {{test_name}}Card(item: t{{test_name}}),
          ),
        ),
      );

      expect(find.text('Test {{test_name}}'), findsOneWidget);
      expect(find.text('Test description'), findsOneWidget);
      expect(find.text('\$19.99'), findsOneWidget);
    });

    testWidgets('calls onTap when tapped', (tester) async {
      var tapped = false;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: {{test_name}}Card(
              item: t{{test_name}},
              onTap: () => tapped = true,
            ),
          ),
        ),
      );

      await tester.tap(find.byType({{test_name}}Card));
      await tester.pump();

      expect(tapped, isTrue);
    });

    testWidgets('shows placeholder when no image', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: {{test_name}}Card(item: t{{test_name}}),
          ),
        ),
      );

      expect(find.byIcon(Icons.image), findsOneWidget);
    });
  });
}
```

## Screen Test

```dart
// test/features/{{feature_name}}/presentation/screens/{{feature_name}}_screen_test.dart

import 'package:bloc_test/bloc_test.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:app/features/{{feature_name}}/domain/entities/{{feature_name}}.dart';
import 'package:app/features/{{feature_name}}/presentation/bloc/{{feature_name}}_bloc.dart';
import 'package:app/features/{{feature_name}}/presentation/screens/{{feature_name}}_screen.dart';

class Mock{{test_name}}Bloc extends MockBloc<{{test_name}}Event, {{test_name}}State>
    implements {{test_name}}Bloc {}

void main() {
  late Mock{{test_name}}Bloc mockBloc;

  setUp(() {
    mockBloc = Mock{{test_name}}Bloc();
  });

  final t{{test_name}}List = [
    {{test_name}}(id: '1', name: 'Test 1', createdAt: DateTime.now()),
    {{test_name}}(id: '2', name: 'Test 2', createdAt: DateTime.now()),
  ];

  Widget buildSubject() {
    return MaterialApp(
      home: BlocProvider<{{test_name}}Bloc>.value(
        value: mockBloc,
        child: const {{test_name}}Screen(),
      ),
    );
  }

  group('{{test_name}}Screen', () {
    testWidgets('shows loading indicator when state is Loading', (tester) async {
      when(() => mockBloc.state).thenReturn(const {{test_name}}Loading());

      await tester.pumpWidget(buildSubject());

      expect(find.byType(CircularProgressIndicator), findsOneWidget);
    });

    testWidgets('shows list when state is Success', (tester) async {
      when(() => mockBloc.state)
          .thenReturn({{test_name}}Success(items: t{{test_name}}List));

      await tester.pumpWidget(buildSubject());

      expect(find.text('Test 1'), findsOneWidget);
      expect(find.text('Test 2'), findsOneWidget);
    });

    testWidgets('shows error message when state is Error', (tester) async {
      when(() => mockBloc.state)
          .thenReturn(const {{test_name}}Error(message: 'Error occurred'));

      await tester.pumpWidget(buildSubject());

      expect(find.text('Error occurred'), findsOneWidget);
      expect(find.text('Retry'), findsOneWidget);
    });

    testWidgets('adds Started event when retry is tapped', (tester) async {
      when(() => mockBloc.state)
          .thenReturn(const {{test_name}}Error(message: 'Error'));

      await tester.pumpWidget(buildSubject());
      await tester.tap(find.text('Retry'));

      verify(() => mockBloc.add(const {{test_name}}Started())).called(1);
    });

    testWidgets('refreshes when pull to refresh', (tester) async {
      when(() => mockBloc.state)
          .thenReturn({{test_name}}Success(items: t{{test_name}}List));

      await tester.pumpWidget(buildSubject());
      await tester.fling(find.byType(RefreshIndicator), const Offset(0, 300), 1000);
      await tester.pumpAndSettle();

      verify(() => mockBloc.add(const {{test_name}}Refreshed())).called(1);
    });
  });
}
```

## Repository Test

```dart
// test/features/{{feature_name}}/data/repositories/{{feature_name}}_repository_impl_test.dart

import 'package:dartz/dartz.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:app/core/error/exceptions.dart';
import 'package:app/core/error/failures.dart';
import 'package:app/core/network/network_info.dart';
import 'package:app/features/{{feature_name}}/data/datasources/{{feature_name}}_local_datasource.dart';
import 'package:app/features/{{feature_name}}/data/datasources/{{feature_name}}_remote_datasource.dart';
import 'package:app/features/{{feature_name}}/data/models/{{feature_name}}_model.dart';
import 'package:app/features/{{feature_name}}/data/repositories/{{feature_name}}_repository_impl.dart';

class Mock{{test_name}}RemoteDataSource extends Mock
    implements {{test_name}}RemoteDataSource {}

class Mock{{test_name}}LocalDataSource extends Mock
    implements {{test_name}}LocalDataSource {}

class MockNetworkInfo extends Mock implements NetworkInfo {}

void main() {
  late {{test_name}}RepositoryImpl repository;
  late Mock{{test_name}}RemoteDataSource mockRemoteDataSource;
  late Mock{{test_name}}LocalDataSource mockLocalDataSource;
  late MockNetworkInfo mockNetworkInfo;

  setUp(() {
    mockRemoteDataSource = Mock{{test_name}}RemoteDataSource();
    mockLocalDataSource = Mock{{test_name}}LocalDataSource();
    mockNetworkInfo = MockNetworkInfo();
    repository = {{test_name}}RepositoryImpl(
      remoteDataSource: mockRemoteDataSource,
      localDataSource: mockLocalDataSource,
      networkInfo: mockNetworkInfo,
    );
  });

  final t{{test_name}}Model = {{test_name}}Model(
    id: '1',
    name: 'Test',
    createdAt: DateTime.now(),
  );

  final t{{test_name}} = t{{test_name}}Model.toEntity();

  group('getAll', () {
    test('should return remote data when online', () async {
      // Arrange
      when(() => mockNetworkInfo.isConnected).thenAnswer((_) async => true);
      when(() => mockRemoteDataSource.getAll())
          .thenAnswer((_) async => [t{{test_name}}Model]);
      when(() => mockLocalDataSource.cacheAll(any()))
          .thenAnswer((_) async {});

      // Act
      final result = await repository.getAll();

      // Assert
      verify(() => mockRemoteDataSource.getAll());
      verify(() => mockLocalDataSource.cacheAll([t{{test_name}}Model]));
      expect(result, Right([t{{test_name}}]));
    });

    test('should return cached data when offline', () async {
      // Arrange
      when(() => mockNetworkInfo.isConnected).thenAnswer((_) async => false);
      when(() => mockLocalDataSource.getAll())
          .thenAnswer((_) async => [t{{test_name}}Model]);

      // Act
      final result = await repository.getAll();

      // Assert
      verifyNever(() => mockRemoteDataSource.getAll());
      verify(() => mockLocalDataSource.getAll());
      expect(result, Right([t{{test_name}}]));
    });

    test('should return CacheFailure when offline and no cache', () async {
      // Arrange
      when(() => mockNetworkInfo.isConnected).thenAnswer((_) async => false);
      when(() => mockLocalDataSource.getAll()).thenThrow(CacheException());

      // Act
      final result = await repository.getAll();

      // Assert
      expect(result, const Left(CacheFailure(message: 'No cached data available')));
    });

    test('should return ServerFailure when remote call fails', () async {
      // Arrange
      when(() => mockNetworkInfo.isConnected).thenAnswer((_) async => true);
      when(() => mockRemoteDataSource.getAll())
          .thenThrow(ServerException(message: 'Server error'));

      // Act
      final result = await repository.getAll();

      // Assert
      expect(result, const Left(ServerFailure(message: 'Server error')));
    });
  });
}
```

## Test Helpers

```dart
// test/helpers/pump_app.dart

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

extension PumpApp on WidgetTester {
  Future<void> pumpApp(
    Widget widget, {
    List<Override>? overrides,
  }) async {
    await pumpWidget(
      ProviderScope(
        overrides: overrides ?? [],
        child: MaterialApp(
          home: widget,
        ),
      ),
    );
  }

  Future<void> pumpRoute(
    Route<dynamic> route, {
    List<Override>? overrides,
  }) async {
    await pumpWidget(
      ProviderScope(
        overrides: overrides ?? [],
        child: MaterialApp(
          onGenerateRoute: (_) => route,
        ),
      ),
    );
  }
}

// test/helpers/mock_helpers.dart

import 'package:mocktail/mocktail.dart';

class FakeRoute extends Fake implements Route<dynamic> {}

void registerFallbackValues() {
  registerFallbackValue(FakeRoute());
}
```

## Usage

Replace `{{test_name}}` with actual test subject name (e.g., `Product`, `User`)
Replace `{{feature_name}}` with feature folder name (e.g., `product`, `user`)

Run tests:
```bash
# All tests
flutter test

# Specific file
flutter test test/features/{{feature_name}}/

# With coverage
flutter test --coverage
```
