---
name: flutter-unit-testing
description: Unit testing patterns in Flutter
applies_to: flutter
---

# Flutter Unit Testing

## Overview

Unit tests verify individual functions, methods, and classes in isolation. They're fast, don't require the Flutter SDK widgets, and form the foundation of a solid test suite.

## Dependencies

```yaml
dev_dependencies:
  flutter_test:
    sdk: flutter
  test: ^1.24.9
  mocktail: ^1.0.3
  bloc_test: ^9.1.5
  fake_async: ^1.3.1
```

## Basic Unit Test Structure

```dart
import 'package:test/test.dart';

void main() {
  group('Calculator', () {
    late Calculator calculator;

    setUp(() {
      calculator = Calculator();
    });

    tearDown(() {
      // Clean up resources if needed
    });

    test('adds two numbers correctly', () {
      expect(calculator.add(2, 3), equals(5));
    });

    test('subtracts two numbers correctly', () {
      expect(calculator.subtract(5, 3), equals(2));
    });

    test('throws on division by zero', () {
      expect(
        () => calculator.divide(10, 0),
        throwsA(isA<ArgumentError>()),
      );
    });
  });
}
```

## Testing with Mocks (Mocktail)

```dart
import 'package:mocktail/mocktail.dart';
import 'package:test/test.dart';

// Create mock class
class MockUserRepository extends Mock implements UserRepository {}
class MockAuthService extends Mock implements AuthService {}

// Register fallback values for custom types
class FakeUser extends Fake implements User {}

void main() {
  late UserService userService;
  late MockUserRepository mockRepository;
  late MockAuthService mockAuthService;

  setUpAll(() {
    // Register fallback values for custom types
    registerFallbackValue(FakeUser());
  });

  setUp(() {
    mockRepository = MockUserRepository();
    mockAuthService = MockAuthService();
    userService = UserService(
      repository: mockRepository,
      authService: mockAuthService,
    );
  });

  group('UserService', () {
    test('getUser returns user from repository', () async {
      // Arrange
      final user = User(id: '1', name: 'John');
      when(() => mockRepository.getUser('1')).thenAnswer((_) async => user);

      // Act
      final result = await userService.getUser('1');

      // Assert
      expect(result, equals(user));
      verify(() => mockRepository.getUser('1')).called(1);
    });

    test('getUser throws when user not found', () async {
      // Arrange
      when(() => mockRepository.getUser(any()))
          .thenThrow(UserNotFoundException());

      // Act & Assert
      expect(
        () => userService.getUser('unknown'),
        throwsA(isA<UserNotFoundException>()),
      );
    });

    test('createUser validates and saves user', () async {
      // Arrange
      final user = User(id: '1', name: 'John');
      when(() => mockRepository.saveUser(any())).thenAnswer((_) async => user);

      // Act
      final result = await userService.createUser(name: 'John');

      // Assert
      expect(result.name, equals('John'));
      verify(() => mockRepository.saveUser(any())).called(1);
    });
  });
}
```

## Testing Async Code

```dart
import 'package:fake_async/fake_async.dart';
import 'package:test/test.dart';

void main() {
  group('AsyncService', () {
    test('fetches data with timeout', () async {
      final service = DataService();

      final future = service.fetchData();

      await expectLater(
        future,
        completion(isA<Data>()),
      );
    });

    test('handles timeout correctly', () {
      fakeAsync((async) {
        final service = DataService(timeout: const Duration(seconds: 5));
        var completed = false;
        var timedOut = false;

        service.fetchWithTimeout().then((_) {
          completed = true;
        }).catchError((e) {
          timedOut = e is TimeoutException;
        });

        // Advance time past timeout
        async.elapse(const Duration(seconds: 6));

        expect(timedOut, isTrue);
        expect(completed, isFalse);
      });
    });

    test('debounces rapid calls', () {
      fakeAsync((async) {
        final service = SearchService();
        final results = <String>[];

        service.searchStream.listen(results.add);

        // Rapid fire searches
        service.search('a');
        service.search('ab');
        service.search('abc');

        // Advance past debounce duration
        async.elapse(const Duration(milliseconds: 500));

        // Only last search should be executed
        expect(results, hasLength(1));
        expect(results.first, contains('abc'));
      });
    });
  });
}
```

## Testing Streams

```dart
import 'package:test/test.dart';

void main() {
  group('StreamService', () {
    test('emits values in order', () {
      final service = CounterService();

      expect(
        service.countStream,
        emitsInOrder([1, 2, 3]),
      );

      service.increment();
      service.increment();
      service.increment();
    });

    test('emits error and continues', () {
      final service = DataStreamService();

      expect(
        service.dataStream,
        emitsInOrder([
          emits(isA<Data>()),
          emitsError(isA<DataException>()),
          emits(isA<Data>()),
        ]),
      );
    });

    test('completes after all items', () {
      final service = FiniteStreamService();

      expect(
        service.items,
        emitsInOrder([
          'first',
          'second',
          'third',
          emitsDone,
        ]),
      );
    });

    test('stream closes on dispose', () async {
      final service = StreamService();

      expectLater(
        service.dataStream,
        emitsThrough(emitsDone),
      );

      await service.dispose();
    });
  });
}
```

## Testing BLoC/Cubit

```dart
import 'package:bloc_test/bloc_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:test/test.dart';

class MockAuthRepository extends Mock implements AuthRepository {}

void main() {
  group('AuthBloc', () {
    late MockAuthRepository mockRepository;

    setUp(() {
      mockRepository = MockAuthRepository();
    });

    test('initial state is AuthInitial', () {
      final bloc = AuthBloc(repository: mockRepository);
      expect(bloc.state, equals(const AuthInitial()));
    });

    blocTest<AuthBloc, AuthState>(
      'emits [AuthLoading, AuthAuthenticated] when login succeeds',
      build: () {
        when(() => mockRepository.login(any(), any()))
            .thenAnswer((_) async => User(id: '1', name: 'John'));
        return AuthBloc(repository: mockRepository);
      },
      act: (bloc) => bloc.add(const LoginRequested(
        email: 'test@test.com',
        password: 'password',
      )),
      expect: () => [
        const AuthLoading(),
        isA<AuthAuthenticated>()
            .having((s) => s.user.name, 'user name', 'John'),
      ],
      verify: (_) {
        verify(() => mockRepository.login('test@test.com', 'password'))
            .called(1);
      },
    );

    blocTest<AuthBloc, AuthState>(
      'emits [AuthLoading, AuthError] when login fails',
      build: () {
        when(() => mockRepository.login(any(), any()))
            .thenThrow(AuthException('Invalid credentials'));
        return AuthBloc(repository: mockRepository);
      },
      act: (bloc) => bloc.add(const LoginRequested(
        email: 'test@test.com',
        password: 'wrong',
      )),
      expect: () => [
        const AuthLoading(),
        const AuthError('Invalid credentials'),
      ],
    );

    blocTest<AuthBloc, AuthState>(
      'emits [AuthInitial] when logout is requested',
      build: () {
        when(() => mockRepository.logout()).thenAnswer((_) async {});
        return AuthBloc(repository: mockRepository);
      },
      seed: () => AuthAuthenticated(User(id: '1', name: 'John')),
      act: (bloc) => bloc.add(const LogoutRequested()),
      expect: () => [const AuthInitial()],
      verify: (_) {
        verify(() => mockRepository.logout()).called(1);
      },
    );
  });
}
```

## Testing Riverpod Providers

```dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mocktail/mocktail.dart';
import 'package:test/test.dart';

class MockUserRepository extends Mock implements UserRepository {}

void main() {
  group('UserNotifier', () {
    late ProviderContainer container;
    late MockUserRepository mockRepository;

    setUp(() {
      mockRepository = MockUserRepository();
      container = ProviderContainer(
        overrides: [
          userRepositoryProvider.overrideWithValue(mockRepository),
        ],
      );
    });

    tearDown(() {
      container.dispose();
    });

    test('initial state is loading', () {
      expect(
        container.read(userProvider),
        const AsyncValue<User>.loading(),
      );
    });

    test('fetches user on initialization', () async {
      final user = User(id: '1', name: 'John');
      when(() => mockRepository.getCurrentUser())
          .thenAnswer((_) async => user);

      // Allow provider to initialize
      await container.read(userProvider.future);

      expect(
        container.read(userProvider),
        AsyncValue.data(user),
      );
    });

    test('handles error during fetch', () async {
      when(() => mockRepository.getCurrentUser())
          .thenThrow(Exception('Network error'));

      try {
        await container.read(userProvider.future);
      } catch (_) {}

      expect(
        container.read(userProvider),
        isA<AsyncError<User>>(),
      );
    });

    test('updateUser updates state', () async {
      final user = User(id: '1', name: 'John');
      final updatedUser = User(id: '1', name: 'Jane');

      when(() => mockRepository.getCurrentUser())
          .thenAnswer((_) async => user);
      when(() => mockRepository.updateUser(any()))
          .thenAnswer((_) async => updatedUser);

      await container.read(userProvider.future);

      await container.read(userProvider.notifier).updateName('Jane');

      expect(
        container.read(userProvider).value?.name,
        equals('Jane'),
      );
    });
  });
}
```

## Testing Repository Layer

```dart
import 'package:mocktail/mocktail.dart';
import 'package:test/test.dart';

class MockApiClient extends Mock implements ApiClient {}
class MockLocalStorage extends Mock implements LocalStorage {}

void main() {
  group('ProductRepository', () {
    late ProductRepository repository;
    late MockApiClient mockApiClient;
    late MockLocalStorage mockLocalStorage;

    setUp(() {
      mockApiClient = MockApiClient();
      mockLocalStorage = MockLocalStorage();
      repository = ProductRepository(
        apiClient: mockApiClient,
        localStorage: mockLocalStorage,
      );
    });

    group('getProducts', () {
      test('returns products from API when online', () async {
        final products = [
          Product(id: '1', name: 'Product 1'),
          Product(id: '2', name: 'Product 2'),
        ];

        when(() => mockApiClient.getProducts())
            .thenAnswer((_) async => products);
        when(() => mockLocalStorage.saveProducts(any()))
            .thenAnswer((_) async {});

        final result = await repository.getProducts();

        expect(result, equals(products));
        verify(() => mockLocalStorage.saveProducts(products)).called(1);
      });

      test('returns cached products when API fails', () async {
        final cachedProducts = [
          Product(id: '1', name: 'Cached Product'),
        ];

        when(() => mockApiClient.getProducts())
            .thenThrow(NetworkException());
        when(() => mockLocalStorage.getProducts())
            .thenAnswer((_) async => cachedProducts);

        final result = await repository.getProducts();

        expect(result, equals(cachedProducts));
      });

      test('throws when API fails and no cache available', () async {
        when(() => mockApiClient.getProducts())
            .thenThrow(NetworkException());
        when(() => mockLocalStorage.getProducts())
            .thenAnswer((_) async => null);

        expect(
          () => repository.getProducts(),
          throwsA(isA<DataUnavailableException>()),
        );
      });
    });
  });
}
```

## Testing Use Cases

```dart
import 'package:dartz/dartz.dart';
import 'package:mocktail/mocktail.dart';
import 'package:test/test.dart';

class MockOrderRepository extends Mock implements OrderRepository {}
class MockPaymentService extends Mock implements PaymentService {}
class MockInventoryService extends Mock implements InventoryService {}

void main() {
  group('PlaceOrderUseCase', () {
    late PlaceOrderUseCase useCase;
    late MockOrderRepository mockOrderRepository;
    late MockPaymentService mockPaymentService;
    late MockInventoryService mockInventoryService;

    setUp(() {
      mockOrderRepository = MockOrderRepository();
      mockPaymentService = MockPaymentService();
      mockInventoryService = MockInventoryService();
      useCase = PlaceOrderUseCase(
        orderRepository: mockOrderRepository,
        paymentService: mockPaymentService,
        inventoryService: mockInventoryService,
      );
    });

    test('places order successfully when all checks pass', () async {
      // Arrange
      final params = PlaceOrderParams(
        userId: '1',
        items: [OrderItem(productId: 'p1', quantity: 2)],
        paymentMethod: PaymentMethod.card,
      );

      when(() => mockInventoryService.checkAvailability(any()))
          .thenAnswer((_) async => true);
      when(() => mockPaymentService.processPayment(any()))
          .thenAnswer((_) async => PaymentResult.success);
      when(() => mockOrderRepository.createOrder(any()))
          .thenAnswer((_) async => Order(id: 'order-1', status: OrderStatus.placed));

      // Act
      final result = await useCase(params);

      // Assert
      expect(result, isA<Right<Failure, Order>>());
      result.fold(
        (failure) => fail('Expected success'),
        (order) => expect(order.id, equals('order-1')),
      );
    });

    test('returns failure when inventory check fails', () async {
      final params = PlaceOrderParams(
        userId: '1',
        items: [OrderItem(productId: 'p1', quantity: 100)],
        paymentMethod: PaymentMethod.card,
      );

      when(() => mockInventoryService.checkAvailability(any()))
          .thenAnswer((_) async => false);

      final result = await useCase(params);

      expect(result, isA<Left<Failure, Order>>());
      result.fold(
        (failure) => expect(failure, isA<InsufficientInventoryFailure>()),
        (order) => fail('Expected failure'),
      );
      verifyNever(() => mockPaymentService.processPayment(any()));
    });
  });
}
```

## Custom Matchers

```dart
import 'package:test/test.dart';

// Custom matcher for User
class IsValidUser extends Matcher {
  @override
  bool matches(dynamic item, Map matchState) {
    if (item is! User) return false;
    return item.id.isNotEmpty &&
        item.email.contains('@') &&
        item.name.length >= 2;
  }

  @override
  Description describe(Description description) {
    return description.add('a valid user with non-empty id, valid email, and name >= 2 chars');
  }
}

Matcher isValidUser = IsValidUser();

// Usage
test('creates valid user', () async {
  final user = await userService.createUser(
    email: 'test@test.com',
    name: 'John',
  );

  expect(user, isValidUser);
});

// Matcher with parameter
Matcher hasStatus(OrderStatus status) => _HasStatus(status);

class _HasStatus extends Matcher {
  final OrderStatus expected;

  _HasStatus(this.expected);

  @override
  bool matches(dynamic item, Map matchState) {
    return item is Order && item.status == expected;
  }

  @override
  Description describe(Description description) {
    return description.add('an order with status $expected');
  }
}

// Usage
test('order has pending status', () {
  expect(order, hasStatus(OrderStatus.pending));
});
```

## Test Helpers and Fixtures

```dart
// test/helpers/test_helpers.dart
import 'package:mocktail/mocktail.dart';

class MockUserRepository extends Mock implements UserRepository {}
class MockAuthService extends Mock implements AuthService {}

// Fallback values
class FakeUser extends Fake implements User {}
class FakeCredentials extends Fake implements Credentials {}

void registerFallbackValues() {
  registerFallbackValue(FakeUser());
  registerFallbackValue(FakeCredentials());
}

// test/fixtures/user_fixtures.dart
class UserFixtures {
  static User get validUser => User(
        id: 'user-1',
        email: 'test@test.com',
        name: 'Test User',
        createdAt: DateTime(2024, 1, 1),
      );

  static User get adminUser => User(
        id: 'admin-1',
        email: 'admin@test.com',
        name: 'Admin User',
        role: UserRole.admin,
        createdAt: DateTime(2024, 1, 1),
      );

  static List<User> get userList => [
        validUser,
        adminUser,
        User(id: 'user-2', email: 'user2@test.com', name: 'User 2'),
      ];
}

// test/helpers/json_fixtures.dart
class JsonFixtures {
  static Map<String, dynamic> get userJson => {
        'id': 'user-1',
        'email': 'test@test.com',
        'name': 'Test User',
        'created_at': '2024-01-01T00:00:00.000Z',
      };

  static String get userJsonString => jsonEncode(userJson);
}
```

## Running Tests

```bash
# Run all tests
flutter test

# Run specific test file
flutter test test/unit/services/auth_service_test.dart

# Run with coverage
flutter test --coverage

# Run with verbose output
flutter test --reporter expanded

# Run tests matching name
flutter test --name "AuthBloc"

# Run tests with tags
flutter test --tags unit
```

## Best Practices

1. **Arrange-Act-Assert** - Structure tests clearly with setup, action, and verification
2. **One assertion per test** - Keep tests focused on single behavior
3. **Use descriptive names** - Test names should describe the scenario
4. **Mock external dependencies** - Isolate unit under test
5. **Test edge cases** - Include boundary conditions and error scenarios
6. **Use fixtures** - Create reusable test data for consistency
