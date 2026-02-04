---
name: flutter-deep-linking
description: Deep linking and universal links in Flutter
applies_to: flutter
---

# Flutter Deep Linking

## Overview

Deep linking allows users to navigate directly to specific content in your app via URLs. Supports both URL schemes (custom protocols) and universal/app links (HTTP URLs).

## Types of Deep Links

| Type | Format | Platform | Verification |
|------|--------|----------|--------------|
| URL Scheme | `myapp://products/123` | iOS, Android | None |
| Universal Links | `https://myapp.com/products/123` | iOS | Apple verification |
| App Links | `https://myapp.com/products/123` | Android | Google verification |

## Dependencies

```yaml
dependencies:
  go_router: ^13.2.0
  # For handling incoming links
  app_links: ^4.0.1
```

## Android Configuration

### AndroidManifest.xml

```xml
<!-- android/app/src/main/AndroidManifest.xml -->
<manifest>
  <application>
    <activity
      android:name=".MainActivity"
      android:launchMode="singleTop">

      <!-- URL Scheme -->
      <intent-filter>
        <action android:name="android.intent.action.VIEW" />
        <category android:name="android.intent.category.DEFAULT" />
        <category android:name="android.intent.category.BROWSABLE" />
        <data android:scheme="myapp" />
      </intent-filter>

      <!-- App Links (verified) -->
      <intent-filter android:autoVerify="true">
        <action android:name="android.intent.action.VIEW" />
        <category android:name="android.intent.category.DEFAULT" />
        <category android:name="android.intent.category.BROWSABLE" />
        <data
          android:scheme="https"
          android:host="myapp.com"
          android:pathPrefix="/products" />
        <data
          android:scheme="https"
          android:host="myapp.com"
          android:pathPrefix="/orders" />
      </intent-filter>
    </activity>
  </application>
</manifest>
```

### assetlinks.json (App Links Verification)

Host at `https://myapp.com/.well-known/assetlinks.json`:

```json
[{
  "relation": ["delegate_permission/common.handle_all_urls"],
  "target": {
    "namespace": "android_app",
    "package_name": "com.myapp.app",
    "sha256_cert_fingerprints": [
      "AB:CD:EF:12:34:56:78:90:AB:CD:EF:12:34:56:78:90:AB:CD:EF:12:34:56:78:90:AB:CD:EF:12:34:56:78:90"
    ]
  }
}]
```

Get SHA256 fingerprint:
```bash
keytool -list -v -keystore ~/.android/debug.keystore -alias androiddebugkey -storepass android -keypass android
```

## iOS Configuration

### Info.plist

```xml
<!-- ios/Runner/Info.plist -->
<dict>
  <!-- URL Scheme -->
  <key>CFBundleURLTypes</key>
  <array>
    <dict>
      <key>CFBundleURLName</key>
      <string>com.myapp.app</string>
      <key>CFBundleURLSchemes</key>
      <array>
        <string>myapp</string>
      </array>
    </dict>
  </array>

  <!-- Universal Links -->
  <key>FlutterDeepLinkingEnabled</key>
  <true/>
</dict>
```

### Associated Domains (Universal Links)

In Xcode: Runner > Signing & Capabilities > Associated Domains:
```
applinks:myapp.com
```

### apple-app-site-association

Host at `https://myapp.com/.well-known/apple-app-site-association`:

```json
{
  "applinks": {
    "apps": [],
    "details": [
      {
        "appID": "TEAM_ID.com.myapp.app",
        "paths": [
          "/products/*",
          "/orders/*",
          "/profile"
        ]
      }
    ]
  }
}
```

## go_router Deep Link Setup

```dart
final router = GoRouter(
  initialLocation: '/',
  routes: [
    GoRoute(
      path: '/',
      name: 'home',
      builder: (context, state) => const HomePage(),
    ),
    GoRoute(
      path: '/products/:id',
      name: 'product-detail',
      builder: (context, state) {
        final id = state.pathParameters['id']!;
        return ProductDetailPage(productId: id);
      },
    ),
    GoRoute(
      path: '/orders/:id',
      name: 'order-detail',
      builder: (context, state) {
        final id = state.pathParameters['id']!;
        return OrderDetailPage(orderId: id);
      },
    ),
    GoRoute(
      path: '/profile',
      name: 'profile',
      builder: (context, state) => const ProfilePage(),
    ),
  ],
);

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      routerConfig: router,
    );
  }
}
```

## Handling Deep Links with app_links

```dart
import 'package:app_links/app_links.dart';

class DeepLinkHandler {
  late final AppLinks _appLinks;
  StreamSubscription<Uri>? _linkSubscription;

  DeepLinkHandler() {
    _appLinks = AppLinks();
  }

  Future<void> initialize(GoRouter router) async {
    // Handle initial deep link (app opened via link)
    final initialLink = await _appLinks.getInitialAppLink();
    if (initialLink != null) {
      _handleDeepLink(initialLink, router);
    }

    // Handle deep links when app is running
    _linkSubscription = _appLinks.uriLinkStream.listen((uri) {
      _handleDeepLink(uri, router);
    });
  }

  void _handleDeepLink(Uri uri, GoRouter router) {
    // Convert custom scheme to path
    String path;
    if (uri.scheme == 'myapp') {
      // myapp://products/123 -> /products/123
      path = '/${uri.host}${uri.path}';
    } else {
      // https://myapp.com/products/123 -> /products/123
      path = uri.path;
    }

    // Add query parameters if present
    if (uri.queryParameters.isNotEmpty) {
      path = '$path?${uri.query}';
    }

    router.go(path);
  }

  void dispose() {
    _linkSubscription?.cancel();
  }
}

// In main.dart
void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  final deepLinkHandler = DeepLinkHandler();
  await deepLinkHandler.initialize(router);

  runApp(const MyApp());
}
```

## Dynamic Links with Firebase

```yaml
dependencies:
  firebase_dynamic_links: ^5.4.6
```

```dart
class FirebaseDynamicLinkHandler {
  Future<void> initialize(GoRouter router) async {
    // Handle initial dynamic link
    final initialLink = await FirebaseDynamicLinks.instance.getInitialLink();
    if (initialLink != null) {
      _handleDynamicLink(initialLink, router);
    }

    // Handle dynamic links when app is running
    FirebaseDynamicLinks.instance.onLink.listen((dynamicLinkData) {
      _handleDynamicLink(dynamicLinkData, router);
    });
  }

  void _handleDynamicLink(PendingDynamicLinkData data, GoRouter router) {
    final deepLink = data.link;
    final path = deepLink.path;
    final queryParams = deepLink.queryParameters;

    // Navigate based on path
    if (path.startsWith('/products/')) {
      final productId = path.split('/').last;
      router.goNamed('product-detail', pathParameters: {'id': productId});
    } else if (path.startsWith('/invite/')) {
      final inviteCode = queryParams['code'];
      router.goNamed('invite', queryParameters: {'code': inviteCode ?? ''});
    }
  }

  // Create a dynamic link
  Future<String> createProductLink(String productId) async {
    final parameters = DynamicLinkParameters(
      uriPrefix: 'https://myapp.page.link',
      link: Uri.parse('https://myapp.com/products/$productId'),
      androidParameters: const AndroidParameters(
        packageName: 'com.myapp.app',
        minimumVersion: 1,
      ),
      iosParameters: const IOSParameters(
        bundleId: 'com.myapp.app',
        minimumVersion: '1.0.0',
        appStoreId: '123456789',
      ),
      socialMetaTagParameters: SocialMetaTagParameters(
        title: 'Check out this product!',
        description: 'Amazing product on MyApp',
        imageUrl: Uri.parse('https://myapp.com/images/product.png'),
      ),
    );

    final shortLink = await FirebaseDynamicLinks.instance.buildShortLink(
      parameters,
      shortLinkType: ShortDynamicLinkType.unguessable,
    );

    return shortLink.shortUrl.toString();
  }
}
```

## Authentication and Deep Links

```dart
final router = GoRouter(
  initialLocation: '/',
  redirect: (context, state) async {
    final isLoggedIn = authNotifier.isAuthenticated;
    final isGoingToProtectedRoute = state.matchedLocation.startsWith('/orders') ||
        state.matchedLocation.startsWith('/profile');

    if (!isLoggedIn && isGoingToProtectedRoute) {
      // Store the intended destination
      final redirectTo = state.matchedLocation;
      return '/login?redirect=$redirectTo';
    }

    return null;
  },
  routes: [
    GoRoute(
      path: '/login',
      builder: (context, state) {
        final redirectTo = state.uri.queryParameters['redirect'];
        return LoginPage(redirectTo: redirectTo);
      },
    ),
    // ... other routes
  ],
);

// In LoginPage
class LoginPage extends StatelessWidget {
  final String? redirectTo;

  const LoginPage({this.redirectTo});

  Future<void> _handleLogin(BuildContext context) async {
    await authService.login();

    if (redirectTo != null) {
      context.go(redirectTo!);
    } else {
      context.go('/');
    }
  }
}
```

## Testing Deep Links

### Android

```bash
# URL Scheme
adb shell am start -a android.intent.action.VIEW \
  -d "myapp://products/123" com.myapp.app

# App Link
adb shell am start -a android.intent.action.VIEW \
  -d "https://myapp.com/products/123" com.myapp.app
```

### iOS

```bash
# URL Scheme (Simulator)
xcrun simctl openurl booted "myapp://products/123"

# Universal Link (requires device with proper configuration)
xcrun simctl openurl booted "https://myapp.com/products/123"
```

### Flutter Integration Test

```dart
void main() {
  testWidgets('Deep link to product navigates correctly', (tester) async {
    await tester.pumpWidget(MaterialApp.router(routerConfig: router));

    // Simulate deep link
    router.go('/products/123');
    await tester.pumpAndSettle();

    expect(find.byType(ProductDetailPage), findsOneWidget);
  });
}
```

## Best Practices

1. **Verify domains** - Set up App Links and Universal Links properly
2. **Handle both schemes** - Support URL scheme and HTTPS
3. **Graceful fallback** - Handle invalid deep links gracefully
4. **Test thoroughly** - Test on both platforms and cold/warm start
5. **Authentication flow** - Preserve deep link destination through login
6. **Analytics** - Track deep link opens for attribution
