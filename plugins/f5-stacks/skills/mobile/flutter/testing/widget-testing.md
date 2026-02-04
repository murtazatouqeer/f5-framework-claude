---
name: flutter-widget-testing
description: Widget testing patterns in Flutter
applies_to: flutter
---

# Flutter Widget Testing

## Overview

Widget tests verify that UI components render correctly and respond to user interactions. They run faster than integration tests while testing actual widget behavior.

## Dependencies

```yaml
dev_dependencies:
  flutter_test:
    sdk: flutter
  mocktail: ^1.0.3
  network_image_mock: ^2.1.1
  golden_toolkit: ^0.15.0
```

## Basic Widget Test Structure

```dart
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('CounterWidget', () {
    testWidgets('displays initial count', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: CounterWidget(initialCount: 5),
        ),
      );

      expect(find.text('5'), findsOneWidget);
    });

    testWidgets('increments count when button pressed', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: CounterWidget(initialCount: 0),
        ),
      );

      await tester.tap(find.byIcon(Icons.add));
      await tester.pump();

      expect(find.text('1'), findsOneWidget);
    });

    testWidgets('decrements count when button pressed', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: CounterWidget(initialCount: 5),
        ),
      );

      await tester.tap(find.byIcon(Icons.remove));
      await tester.pump();

      expect(find.text('4'), findsOneWidget);
    });
  });
}
```

## Finding Widgets

```dart
void main() {
  testWidgets('demonstrates various finders', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: Column(
            children: [
              const Text('Hello'),
              const Text('World'),
              ElevatedButton(
                key: const Key('submit_button'),
                onPressed: () {},
                child: const Text('Submit'),
              ),
              TextField(
                decoration: const InputDecoration(
                  labelText: 'Email',
                  hintText: 'Enter email',
                ),
              ),
              const Icon(Icons.star),
              CustomWidget(),
            ],
          ),
        ),
      ),
    );

    // Find by text
    expect(find.text('Hello'), findsOneWidget);
    expect(find.text('World'), findsOneWidget);

    // Find by widget type
    expect(find.byType(ElevatedButton), findsOneWidget);
    expect(find.byType(TextField), findsOneWidget);

    // Find by key
    expect(find.byKey(const Key('submit_button')), findsOneWidget);

    // Find by icon
    expect(find.byIcon(Icons.star), findsOneWidget);

    // Find by predicate
    expect(
      find.byWidgetPredicate(
        (widget) => widget is Text && widget.data!.contains('ello'),
      ),
      findsOneWidget,
    );

    // Find by semantic label
    expect(find.bySemanticsLabel('Email'), findsOneWidget);

    // Find descendant
    expect(
      find.descendant(
        of: find.byType(ElevatedButton),
        matching: find.text('Submit'),
      ),
      findsOneWidget,
    );

    // Find ancestor
    expect(
      find.ancestor(
        of: find.text('Submit'),
        matching: find.byType(ElevatedButton),
      ),
      findsOneWidget,
    );

    // Custom finder for specific widget
    expect(find.byType(CustomWidget), findsOneWidget);
  });
}
```

## User Interactions

```dart
void main() {
  group('User Interactions', () {
    testWidgets('handles tap', (tester) async {
      var tapped = false;

      await tester.pumpWidget(
        MaterialApp(
          home: ElevatedButton(
            onPressed: () => tapped = true,
            child: const Text('Tap Me'),
          ),
        ),
      );

      await tester.tap(find.text('Tap Me'));
      await tester.pump();

      expect(tapped, isTrue);
    });

    testWidgets('handles long press', (tester) async {
      var longPressed = false;

      await tester.pumpWidget(
        MaterialApp(
          home: GestureDetector(
            onLongPress: () => longPressed = true,
            child: const Text('Long Press Me'),
          ),
        ),
      );

      await tester.longPress(find.text('Long Press Me'));
      await tester.pump();

      expect(longPressed, isTrue);
    });

    testWidgets('handles text input', (tester) async {
      final controller = TextEditingController();

      await tester.pumpWidget(
        MaterialApp(
          home: TextField(controller: controller),
        ),
      );

      await tester.enterText(find.byType(TextField), 'Hello World');
      await tester.pump();

      expect(controller.text, equals('Hello World'));
    });

    testWidgets('handles drag/scroll', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: ListView.builder(
            itemCount: 100,
            itemBuilder: (_, index) => ListTile(title: Text('Item $index')),
          ),
        ),
      );

      expect(find.text('Item 0'), findsOneWidget);
      expect(find.text('Item 50'), findsNothing);

      await tester.drag(find.byType(ListView), const Offset(0, -500));
      await tester.pump();

      expect(find.text('Item 0'), findsNothing);
    });

    testWidgets('handles fling gesture', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: ListView.builder(
            itemCount: 100,
            itemBuilder: (_, index) => ListTile(title: Text('Item $index')),
          ),
        ),
      );

      await tester.fling(
        find.byType(ListView),
        const Offset(0, -500),
        1000,
      );
      await tester.pumpAndSettle();

      // Verify scrolled far
      expect(find.text('Item 0'), findsNothing);
    });

    testWidgets('handles swipe to dismiss', (tester) async {
      final items = List.generate(5, (i) => 'Item $i');

      await tester.pumpWidget(
        MaterialApp(
          home: StatefulBuilder(
            builder: (context, setState) {
              return ListView(
                children: items.map((item) {
                  return Dismissible(
                    key: Key(item),
                    onDismissed: (_) => setState(() => items.remove(item)),
                    child: ListTile(title: Text(item)),
                  );
                }).toList(),
              );
            },
          ),
        ),
      );

      expect(find.text('Item 0'), findsOneWidget);

      await tester.drag(find.text('Item 0'), const Offset(500, 0));
      await tester.pumpAndSettle();

      expect(find.text('Item 0'), findsNothing);
    });
  });
}
```

## Testing with Provider/BLoC

```dart
// With Provider
testWidgets('displays user from provider', (tester) async {
  final user = User(id: '1', name: 'John');

  await tester.pumpWidget(
    ChangeNotifierProvider<UserProvider>.value(
      value: UserProvider()..setUser(user),
      child: const MaterialApp(
        home: UserProfileScreen(),
      ),
    ),
  );

  expect(find.text('John'), findsOneWidget);
});

// With BLoC
testWidgets('displays state from bloc', (tester) async {
  final mockBloc = MockAuthBloc();

  whenListen(
    mockBloc,
    Stream.fromIterable([
      const AuthLoading(),
      AuthAuthenticated(User(id: '1', name: 'John')),
    ]),
    initialState: const AuthInitial(),
  );

  await tester.pumpWidget(
    BlocProvider<AuthBloc>.value(
      value: mockBloc,
      child: const MaterialApp(
        home: AuthScreen(),
      ),
    ),
  );

  // Initially loading
  expect(find.byType(CircularProgressIndicator), findsOneWidget);

  await tester.pump();

  // Then authenticated
  expect(find.text('Welcome, John'), findsOneWidget);
});

// With Riverpod
testWidgets('displays data from riverpod provider', (tester) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        userProvider.overrideWith(
          (ref) => AsyncValue.data(User(id: '1', name: 'John')),
        ),
      ],
      child: const MaterialApp(
        home: UserScreen(),
      ),
    ),
  );

  expect(find.text('John'), findsOneWidget);
});
```

## Testing Async Operations

```dart
void main() {
  testWidgets('shows loading then data', (tester) async {
    final mockRepository = MockUserRepository();
    when(() => mockRepository.getUsers()).thenAnswer(
      (_) async => [User(id: '1', name: 'John')],
    );

    await tester.pumpWidget(
      MaterialApp(
        home: UserListScreen(repository: mockRepository),
      ),
    );

    // Initially shows loading
    expect(find.byType(CircularProgressIndicator), findsOneWidget);

    // Wait for future to complete
    await tester.pumpAndSettle();

    // Now shows data
    expect(find.byType(CircularProgressIndicator), findsNothing);
    expect(find.text('John'), findsOneWidget);
  });

  testWidgets('shows error state', (tester) async {
    final mockRepository = MockUserRepository();
    when(() => mockRepository.getUsers()).thenThrow(Exception('Network error'));

    await tester.pumpWidget(
      MaterialApp(
        home: UserListScreen(repository: mockRepository),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Error: Network error'), findsOneWidget);
    expect(find.byType(ElevatedButton), findsOneWidget); // Retry button
  });

  testWidgets('handles pull to refresh', (tester) async {
    var refreshCount = 0;
    final mockRepository = MockUserRepository();
    when(() => mockRepository.getUsers()).thenAnswer((_) async {
      refreshCount++;
      return [User(id: '1', name: 'User $refreshCount')];
    });

    await tester.pumpWidget(
      MaterialApp(
        home: UserListScreen(repository: mockRepository),
      ),
    );

    await tester.pumpAndSettle();
    expect(find.text('User 1'), findsOneWidget);

    // Pull to refresh
    await tester.fling(find.byType(RefreshIndicator), const Offset(0, 300), 1000);
    await tester.pumpAndSettle();

    expect(find.text('User 2'), findsOneWidget);
    expect(refreshCount, equals(2));
  });
}
```

## Testing Navigation

```dart
void main() {
  testWidgets('navigates to detail screen', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: const UserListScreen(),
        routes: {
          '/user-detail': (context) => const UserDetailScreen(),
        },
      ),
    );

    await tester.tap(find.text('View Details'));
    await tester.pumpAndSettle();

    expect(find.byType(UserDetailScreen), findsOneWidget);
  });

  testWidgets('navigates back', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Builder(
          builder: (context) => ElevatedButton(
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const SecondScreen()),
            ),
            child: const Text('Go'),
          ),
        ),
      ),
    );

    await tester.tap(find.text('Go'));
    await tester.pumpAndSettle();

    expect(find.byType(SecondScreen), findsOneWidget);

    await tester.tap(find.byIcon(Icons.arrow_back));
    await tester.pumpAndSettle();

    expect(find.byType(SecondScreen), findsNothing);
  });

  testWidgets('shows dialog', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Builder(
          builder: (context) => ElevatedButton(
            onPressed: () => showDialog(
              context: context,
              builder: (_) => const AlertDialog(
                title: Text('Confirm'),
                content: Text('Are you sure?'),
              ),
            ),
            child: const Text('Show Dialog'),
          ),
        ),
      ),
    );

    await tester.tap(find.text('Show Dialog'));
    await tester.pumpAndSettle();

    expect(find.text('Confirm'), findsOneWidget);
    expect(find.text('Are you sure?'), findsOneWidget);
  });

  testWidgets('shows bottom sheet', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Builder(
          builder: (context) => ElevatedButton(
            onPressed: () => showModalBottomSheet(
              context: context,
              builder: (_) => const SizedBox(
                height: 200,
                child: Center(child: Text('Bottom Sheet')),
              ),
            ),
            child: const Text('Show Sheet'),
          ),
        ),
      ),
    );

    await tester.tap(find.text('Show Sheet'));
    await tester.pumpAndSettle();

    expect(find.text('Bottom Sheet'), findsOneWidget);
  });
}
```

## Testing with GoRouter

```dart
void main() {
  testWidgets('navigates with go_router', (tester) async {
    final router = GoRouter(
      routes: [
        GoRoute(
          path: '/',
          builder: (_, __) => const HomeScreen(),
          routes: [
            GoRoute(
              path: 'details/:id',
              builder: (_, state) => DetailScreen(
                id: state.pathParameters['id']!,
              ),
            ),
          ],
        ),
      ],
    );

    await tester.pumpWidget(
      MaterialApp.router(
        routerConfig: router,
      ),
    );

    expect(find.byType(HomeScreen), findsOneWidget);

    await tester.tap(find.text('Go to Details'));
    await tester.pumpAndSettle();

    expect(find.byType(DetailScreen), findsOneWidget);
  });
}
```

## Testing Forms

```dart
void main() {
  testWidgets('validates form fields', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: LoginForm(),
      ),
    );

    // Submit empty form
    await tester.tap(find.text('Login'));
    await tester.pump();

    expect(find.text('Email is required'), findsOneWidget);
    expect(find.text('Password is required'), findsOneWidget);

    // Enter invalid email
    await tester.enterText(
      find.byKey(const Key('email_field')),
      'invalid-email',
    );
    await tester.tap(find.text('Login'));
    await tester.pump();

    expect(find.text('Enter a valid email'), findsOneWidget);

    // Enter valid data
    await tester.enterText(
      find.byKey(const Key('email_field')),
      'test@test.com',
    );
    await tester.enterText(
      find.byKey(const Key('password_field')),
      'password123',
    );
    await tester.tap(find.text('Login'));
    await tester.pump();

    expect(find.text('Email is required'), findsNothing);
    expect(find.text('Password is required'), findsNothing);
  });

  testWidgets('shows password visibility toggle', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: LoginForm(),
      ),
    );

    // Password is hidden by default
    final passwordField = tester.widget<TextField>(
      find.byKey(const Key('password_field')),
    );
    expect(passwordField.obscureText, isTrue);

    // Toggle visibility
    await tester.tap(find.byIcon(Icons.visibility_off));
    await tester.pump();

    final visiblePasswordField = tester.widget<TextField>(
      find.byKey(const Key('password_field')),
    );
    expect(visiblePasswordField.obscureText, isFalse);
  });
}
```

## Golden Tests

```dart
import 'package:golden_toolkit/golden_toolkit.dart';

void main() {
  group('Golden Tests', () {
    testGoldens('UserCard renders correctly', (tester) async {
      final builder = GoldenBuilder.column()
        ..addScenario(
          'default',
          UserCard(user: User(id: '1', name: 'John Doe')),
        )
        ..addScenario(
          'with avatar',
          UserCard(
            user: User(id: '2', name: 'Jane Doe', avatarUrl: 'url'),
          ),
        )
        ..addScenario(
          'long name',
          UserCard(
            user: User(id: '3', name: 'Very Long Name That Might Overflow'),
          ),
        );

      await tester.pumpWidgetBuilder(
        builder.build(),
        surfaceSize: const Size(400, 600),
      );

      await screenMatchesGolden(tester, 'user_card_variants');
    });

    testGoldens('responsive layout', (tester) async {
      await tester.pumpWidgetBuilder(
        const ResponsiveScreen(),
        wrapper: materialAppWrapper(),
      );

      await multiScreenGolden(
        tester,
        'responsive_screen',
        devices: [
          Device.phone,
          Device.iphone11,
          Device.tabletPortrait,
          Device.tabletLandscape,
        ],
      );
    });
  });
}
```

## Testing Animations

```dart
void main() {
  testWidgets('animates opacity correctly', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: FadeInWidget(),
      ),
    );

    // Start of animation
    final opacityStart = tester.widget<FadeTransition>(
      find.byType(FadeTransition),
    );
    expect(opacityStart.opacity.value, equals(0.0));

    // Midway through animation
    await tester.pump(const Duration(milliseconds: 250));
    final opacityMid = tester.widget<FadeTransition>(
      find.byType(FadeTransition),
    );
    expect(opacityMid.opacity.value, closeTo(0.5, 0.1));

    // End of animation
    await tester.pumpAndSettle();
    final opacityEnd = tester.widget<FadeTransition>(
      find.byType(FadeTransition),
    );
    expect(opacityEnd.opacity.value, equals(1.0));
  });

  testWidgets('hero animation transitions', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: HeroSourceScreen(),
        routes: {
          '/detail': (_) => HeroDestinationScreen(),
        },
      ),
    );

    await tester.tap(find.byType(HeroImage));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 150));

    // Hero is mid-flight
    expect(find.byType(Hero), findsNWidgets(2));

    await tester.pumpAndSettle();

    // Animation complete
    expect(find.byType(HeroDestinationScreen), findsOneWidget);
  });
}
```

## Pump Methods Reference

```dart
// pump() - Triggers a single frame
await tester.pump();

// pump(duration) - Triggers frame after duration
await tester.pump(const Duration(milliseconds: 100));

// pumpAndSettle() - Pumps until no pending frames
await tester.pumpAndSettle();

// pumpAndSettle with timeout
await tester.pumpAndSettle(const Duration(seconds: 5));

// pumpWidget() - Pumps with a new widget
await tester.pumpWidget(const MyWidget());
```

## Test Wrapper Helper

```dart
// test/helpers/pump_app.dart
extension PumpApp on WidgetTester {
  Future<void> pumpApp(
    Widget widget, {
    List<Override>? providerOverrides,
    NavigatorObserver? navigatorObserver,
  }) async {
    await pumpWidget(
      ProviderScope(
        overrides: providerOverrides ?? [],
        child: MaterialApp(
          navigatorObservers: [
            if (navigatorObserver != null) navigatorObserver,
          ],
          home: widget,
        ),
      ),
    );
  }
}

// Usage
testWidgets('test with helper', (tester) async {
  await tester.pumpApp(
    const MyScreen(),
    providerOverrides: [
      userProvider.overrideWithValue(mockUser),
    ],
  );

  expect(find.text('Hello'), findsOneWidget);
});
```

## Best Practices

1. **Use pumpAndSettle for async** - Wait for all animations and futures
2. **Use specific finders** - byKey > byType for unique identification
3. **Test user flows** - Focus on what users actually do
4. **Mock external dependencies** - Network, storage, etc.
5. **Use golden tests** - For visual regression testing
6. **Test accessibility** - Ensure semantic labels are present
