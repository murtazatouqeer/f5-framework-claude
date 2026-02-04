---
name: flutter-integration-testing
description: Integration and E2E testing patterns in Flutter
applies_to: flutter
---

# Flutter Integration Testing

## Overview

Integration tests verify complete user flows across multiple screens and components. They run on real devices or emulators and test the full app behavior.

## Dependencies

```yaml
dev_dependencies:
  integration_test:
    sdk: flutter
  flutter_test:
    sdk: flutter
```

## Project Structure

```
test_driver/
├── integration_test.dart    # Entry point for driver
integration_test/
├── app_test.dart            # Main test file
├── robots/                  # Page object pattern
│   ├── login_robot.dart
│   ├── home_robot.dart
│   └── cart_robot.dart
├── helpers/
│   ├── test_helpers.dart
│   └── mock_data.dart
└── flows/
    ├── auth_flow_test.dart
    ├── purchase_flow_test.dart
    └── onboarding_flow_test.dart
```

## Basic Integration Test

```dart
// integration_test/app_test.dart
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:my_app/main.dart' as app;

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  group('App Integration Tests', () {
    testWidgets('complete login flow', (tester) async {
      // Launch app
      app.main();
      await tester.pumpAndSettle();

      // Verify login screen
      expect(find.text('Login'), findsOneWidget);

      // Enter credentials
      await tester.enterText(
        find.byKey(const Key('email_field')),
        'test@test.com',
      );
      await tester.enterText(
        find.byKey(const Key('password_field')),
        'password123',
      );

      // Submit login
      await tester.tap(find.byKey(const Key('login_button')));
      await tester.pumpAndSettle();

      // Verify home screen
      expect(find.text('Welcome'), findsOneWidget);
      expect(find.byType(HomeScreen), findsOneWidget);
    });
  });
}
```

## Test Driver

```dart
// test_driver/integration_test.dart
import 'package:integration_test/integration_test_driver.dart';

Future<void> main() => integrationDriver();
```

## Robot Pattern (Page Objects)

```dart
// integration_test/robots/login_robot.dart
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

class LoginRobot {
  final WidgetTester tester;

  LoginRobot(this.tester);

  // Finders
  Finder get emailField => find.byKey(const Key('email_field'));
  Finder get passwordField => find.byKey(const Key('password_field'));
  Finder get loginButton => find.byKey(const Key('login_button'));
  Finder get forgotPasswordLink => find.text('Forgot Password?');
  Finder get registerLink => find.text('Create Account');
  Finder get errorMessage => find.byKey(const Key('error_message'));

  // Actions
  Future<void> enterEmail(String email) async {
    await tester.enterText(emailField, email);
    await tester.pumpAndSettle();
  }

  Future<void> enterPassword(String password) async {
    await tester.enterText(passwordField, password);
    await tester.pumpAndSettle();
  }

  Future<void> tapLogin() async {
    await tester.tap(loginButton);
    await tester.pumpAndSettle();
  }

  Future<void> login({
    required String email,
    required String password,
  }) async {
    await enterEmail(email);
    await enterPassword(password);
    await tapLogin();
  }

  Future<void> tapForgotPassword() async {
    await tester.tap(forgotPasswordLink);
    await tester.pumpAndSettle();
  }

  Future<void> tapRegister() async {
    await tester.tap(registerLink);
    await tester.pumpAndSettle();
  }

  // Assertions
  void verifyLoginScreen() {
    expect(emailField, findsOneWidget);
    expect(passwordField, findsOneWidget);
    expect(loginButton, findsOneWidget);
  }

  void verifyErrorDisplayed(String message) {
    expect(errorMessage, findsOneWidget);
    expect(find.text(message), findsOneWidget);
  }

  void verifyNoError() {
    expect(errorMessage, findsNothing);
  }
}

// integration_test/robots/home_robot.dart
class HomeRobot {
  final WidgetTester tester;

  HomeRobot(this.tester);

  Finder get welcomeText => find.textContaining('Welcome');
  Finder get profileButton => find.byKey(const Key('profile_button'));
  Finder get cartButton => find.byKey(const Key('cart_button'));
  Finder get productList => find.byType(ProductListView);
  Finder get bottomNav => find.byType(BottomNavigationBar);

  Future<void> tapProduct(String name) async {
    await tester.tap(find.text(name));
    await tester.pumpAndSettle();
  }

  Future<void> tapCart() async {
    await tester.tap(cartButton);
    await tester.pumpAndSettle();
  }

  Future<void> tapProfile() async {
    await tester.tap(profileButton);
    await tester.pumpAndSettle();
  }

  Future<void> navigateToTab(int index) async {
    await tester.tap(find.byType(BottomNavigationBarItem).at(index));
    await tester.pumpAndSettle();
  }

  Future<void> scrollToProduct(String name) async {
    await tester.scrollUntilVisible(
      find.text(name),
      100,
      scrollable: find.byType(Scrollable).first,
    );
    await tester.pumpAndSettle();
  }

  void verifyHomeScreen() {
    expect(welcomeText, findsOneWidget);
    expect(productList, findsOneWidget);
    expect(bottomNav, findsOneWidget);
  }

  void verifyProductVisible(String name) {
    expect(find.text(name), findsOneWidget);
  }
}

// integration_test/robots/cart_robot.dart
class CartRobot {
  final WidgetTester tester;

  CartRobot(this.tester);

  Finder get cartItems => find.byType(CartItemTile);
  Finder get emptyCartMessage => find.text('Your cart is empty');
  Finder get checkoutButton => find.byKey(const Key('checkout_button'));
  Finder get totalPrice => find.byKey(const Key('total_price'));

  Future<void> increaseQuantity(int itemIndex) async {
    await tester.tap(
      find.descendant(
        of: cartItems.at(itemIndex),
        matching: find.byIcon(Icons.add),
      ),
    );
    await tester.pumpAndSettle();
  }

  Future<void> decreaseQuantity(int itemIndex) async {
    await tester.tap(
      find.descendant(
        of: cartItems.at(itemIndex),
        matching: find.byIcon(Icons.remove),
      ),
    );
    await tester.pumpAndSettle();
  }

  Future<void> removeItem(int itemIndex) async {
    await tester.drag(cartItems.at(itemIndex), const Offset(-500, 0));
    await tester.pumpAndSettle();
  }

  Future<void> tapCheckout() async {
    await tester.tap(checkoutButton);
    await tester.pumpAndSettle();
  }

  void verifyCartHasItems(int count) {
    expect(cartItems, findsNWidgets(count));
  }

  void verifyEmptyCart() {
    expect(emptyCartMessage, findsOneWidget);
    expect(cartItems, findsNothing);
  }

  void verifyTotalPrice(String price) {
    expect(find.text(price), findsOneWidget);
  }
}
```

## Using Robots in Tests

```dart
// integration_test/flows/auth_flow_test.dart
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:my_app/main.dart' as app;

import '../robots/login_robot.dart';
import '../robots/home_robot.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  late LoginRobot loginRobot;
  late HomeRobot homeRobot;

  group('Authentication Flow', () {
    testWidgets('successful login navigates to home', (tester) async {
      app.main();
      await tester.pumpAndSettle();

      loginRobot = LoginRobot(tester);
      homeRobot = HomeRobot(tester);

      // Verify login screen
      loginRobot.verifyLoginScreen();

      // Perform login
      await loginRobot.login(
        email: 'test@test.com',
        password: 'password123',
      );

      // Verify home screen
      homeRobot.verifyHomeScreen();
    });

    testWidgets('invalid credentials shows error', (tester) async {
      app.main();
      await tester.pumpAndSettle();

      loginRobot = LoginRobot(tester);

      await loginRobot.login(
        email: 'wrong@test.com',
        password: 'wrongpassword',
      );

      loginRobot.verifyErrorDisplayed('Invalid credentials');
    });

    testWidgets('empty fields shows validation errors', (tester) async {
      app.main();
      await tester.pumpAndSettle();

      loginRobot = LoginRobot(tester);

      await loginRobot.tapLogin();

      expect(find.text('Email is required'), findsOneWidget);
      expect(find.text('Password is required'), findsOneWidget);
    });
  });
}
```

## Complete User Flow Test

```dart
// integration_test/flows/purchase_flow_test.dart
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:my_app/main.dart' as app;

import '../robots/login_robot.dart';
import '../robots/home_robot.dart';
import '../robots/cart_robot.dart';
import '../robots/checkout_robot.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  group('Purchase Flow', () {
    testWidgets('complete purchase from login to order confirmation',
        (tester) async {
      app.main();
      await tester.pumpAndSettle();

      final loginRobot = LoginRobot(tester);
      final homeRobot = HomeRobot(tester);
      final cartRobot = CartRobot(tester);
      final checkoutRobot = CheckoutRobot(tester);

      // Step 1: Login
      await loginRobot.login(
        email: 'test@test.com',
        password: 'password123',
      );
      homeRobot.verifyHomeScreen();

      // Step 2: Browse and add products
      await homeRobot.scrollToProduct('Premium Widget');
      await homeRobot.tapProduct('Premium Widget');
      await tester.tap(find.text('Add to Cart'));
      await tester.pumpAndSettle();

      // Step 3: Go back and add another product
      await tester.tap(find.byIcon(Icons.arrow_back));
      await tester.pumpAndSettle();

      await homeRobot.tapProduct('Basic Widget');
      await tester.tap(find.text('Add to Cart'));
      await tester.pumpAndSettle();

      // Step 4: Go to cart
      await homeRobot.tapCart();
      cartRobot.verifyCartHasItems(2);

      // Step 5: Modify cart
      await cartRobot.increaseQuantity(0);
      await cartRobot.removeItem(1);
      cartRobot.verifyCartHasItems(1);

      // Step 6: Checkout
      await cartRobot.tapCheckout();
      checkoutRobot.verifyCheckoutScreen();

      // Step 7: Enter shipping info
      await checkoutRobot.enterShippingInfo(
        name: 'John Doe',
        address: '123 Main St',
        city: 'New York',
        zip: '10001',
      );
      await checkoutRobot.tapContinue();

      // Step 8: Enter payment
      await checkoutRobot.selectPaymentMethod('Credit Card');
      await checkoutRobot.enterCardInfo(
        number: '4242424242424242',
        expiry: '12/25',
        cvv: '123',
      );
      await checkoutRobot.tapPlaceOrder();

      // Step 9: Verify order confirmation
      checkoutRobot.verifyOrderConfirmation();
      expect(find.text('Order Confirmed'), findsOneWidget);
    });
  });
}
```

## Testing with Backend Mock

```dart
// integration_test/helpers/mock_server.dart
import 'dart:io';

class MockServer {
  late HttpServer server;
  final Map<String, dynamic Function(HttpRequest)> routes = {};

  Future<void> start() async {
    server = await HttpServer.bind(InternetAddress.loopbackIPv4, 8080);

    server.listen((request) async {
      final handler = routes['${request.method} ${request.uri.path}'];

      if (handler != null) {
        final response = handler(request);
        request.response
          ..statusCode = HttpStatus.ok
          ..headers.contentType = ContentType.json
          ..write(jsonEncode(response))
          ..close();
      } else {
        request.response
          ..statusCode = HttpStatus.notFound
          ..close();
      }
    });
  }

  void addRoute(String method, String path, dynamic Function(HttpRequest) handler) {
    routes['$method $path'] = handler;
  }

  Future<void> stop() async {
    await server.close();
  }
}

// Usage in tests
void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  late MockServer mockServer;

  setUpAll(() async {
    mockServer = MockServer();

    mockServer.addRoute('POST', '/auth/login', (request) {
      return {'token': 'mock_token', 'user': {'id': '1', 'name': 'John'}};
    });

    mockServer.addRoute('GET', '/products', (request) {
      return {
        'products': [
          {'id': '1', 'name': 'Product 1', 'price': 9.99},
          {'id': '2', 'name': 'Product 2', 'price': 19.99},
        ]
      };
    });

    await mockServer.start();
  });

  tearDownAll(() async {
    await mockServer.stop();
  });

  testWidgets('loads products from mock server', (tester) async {
    // Configure app to use mock server URL
    app.main(baseUrl: 'http://localhost:8080');
    await tester.pumpAndSettle();

    // Test with mock data
    expect(find.text('Product 1'), findsOneWidget);
    expect(find.text('Product 2'), findsOneWidget);
  });
}
```

## Performance Testing

```dart
// integration_test/performance_test.dart
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:my_app/main.dart' as app;

void main() {
  final binding = IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('scrolling performance', (tester) async {
    app.main();
    await tester.pumpAndSettle();

    // Navigate to list screen
    await tester.tap(find.text('Products'));
    await tester.pumpAndSettle();

    // Record performance
    await binding.traceAction(
      () async {
        for (var i = 0; i < 10; i++) {
          await tester.fling(
            find.byType(ListView),
            const Offset(0, -500),
            1000,
          );
          await tester.pumpAndSettle();
        }
      },
      reportKey: 'scrolling_performance',
    );
  });

  testWidgets('app startup time', (tester) async {
    await binding.traceAction(
      () async {
        app.main();
        await tester.pumpAndSettle();
      },
      reportKey: 'startup_time',
    );

    expect(find.byType(HomeScreen), findsOneWidget);
  });
}
```

## Screenshot Testing

```dart
void main() {
  final binding = IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('capture screenshots for different states', (tester) async {
    app.main();
    await tester.pumpAndSettle();

    // Capture login screen
    await binding.takeScreenshot('login_screen');

    // Login
    await tester.enterText(find.byKey(const Key('email_field')), 'test@test.com');
    await tester.enterText(find.byKey(const Key('password_field')), 'password');
    await tester.tap(find.text('Login'));
    await tester.pumpAndSettle();

    // Capture home screen
    await binding.takeScreenshot('home_screen');

    // Navigate to profile
    await tester.tap(find.byIcon(Icons.person));
    await tester.pumpAndSettle();

    // Capture profile screen
    await binding.takeScreenshot('profile_screen');
  });
}
```

## Accessibility Testing

```dart
void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('accessibility test', (tester) async {
    app.main();
    await tester.pumpAndSettle();

    // Test semantic labels
    expect(
      find.bySemanticsLabel('Login button'),
      findsOneWidget,
    );

    // Test focus order
    final focusableElements = tester.widgetList(
      find.byWidgetPredicate((widget) => widget is Focus),
    );
    expect(focusableElements.length, greaterThan(0));

    // Test text scaling
    await tester.pumpWidget(
      MediaQuery(
        data: const MediaQueryData(textScaleFactor: 2.0),
        child: const MyApp(),
      ),
    );
    await tester.pumpAndSettle();

    // Verify UI still works with larger text
    expect(find.text('Login'), findsOneWidget);
  });
}
```

## Running Integration Tests

```bash
# Run on connected device
flutter test integration_test/app_test.dart

# Run on specific device
flutter test integration_test/app_test.dart -d <device_id>

# Run with performance profiling
flutter drive \
  --driver=test_driver/integration_test.dart \
  --target=integration_test/app_test.dart \
  --profile

# Run on Firebase Test Lab
gcloud firebase test android run \
  --type instrumentation \
  --app build/app/outputs/apk/debug/app-debug.apk \
  --test build/app/outputs/apk/androidTest/debug/app-debug-androidTest.apk

# Run multiple test files
flutter test integration_test/
```

## CI/CD Integration

```yaml
# .github/workflows/integration_tests.yml
name: Integration Tests

on: [push, pull_request]

jobs:
  integration_test:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4

      - uses: subosito/flutter-action@v2
        with:
          flutter-version: '3.16.0'
          channel: 'stable'

      - name: Install dependencies
        run: flutter pub get

      - name: Run integration tests on iOS
        run: |
          flutter test integration_test/app_test.dart \
            -d 'iPhone 15'

      - name: Run integration tests on Android
        uses: reactivecircus/android-emulator-runner@v2
        with:
          api-level: 33
          script: flutter test integration_test/app_test.dart
```

## Best Practices

1. **Use Robot pattern** - Encapsulate page interactions for reusability
2. **Test complete flows** - Verify end-to-end user journeys
3. **Mock external services** - Use mock servers for API dependencies
4. **Keep tests independent** - Each test should start from clean state
5. **Add meaningful waits** - Use pumpAndSettle, not arbitrary delays
6. **Capture screenshots** - For debugging and documentation
