---
name: flutter-go-router
description: go_router declarative routing package
applies_to: flutter
---

# Flutter go_router

## Overview

go_router is a declarative routing package built on Navigator 2.0. It provides type-safe routing, deep linking, and nested navigation with a simple API.

## Dependencies

```yaml
dependencies:
  go_router: ^13.2.0
```

## Basic Setup

```dart
import 'package:go_router/go_router.dart';

final router = GoRouter(
  initialLocation: '/',
  routes: [
    GoRoute(
      path: '/',
      name: 'home',
      builder: (context, state) => const HomePage(),
    ),
    GoRoute(
      path: '/products',
      name: 'products',
      builder: (context, state) => const ProductsPage(),
    ),
    GoRoute(
      path: '/products/:id',
      name: 'product-detail',
      builder: (context, state) {
        final id = state.pathParameters['id']!;
        return ProductDetailPage(productId: id);
      },
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

## Navigation Methods

### Basic Navigation

```dart
// Push by path
context.go('/products');

// Push by name with parameters
context.goNamed(
  'product-detail',
  pathParameters: {'id': '123'},
);

// Push without replacing
context.push('/products/123');
context.pushNamed('product-detail', pathParameters: {'id': '123'});

// Pop
context.pop();

// Pop with result
context.pop(result);

// Replace current route
context.pushReplacement('/home');
context.pushReplacementNamed('home');
```

### Query Parameters

```dart
// Route definition
GoRoute(
  path: '/search',
  name: 'search',
  builder: (context, state) {
    final query = state.uri.queryParameters['q'] ?? '';
    final category = state.uri.queryParameters['category'];
    return SearchPage(query: query, category: category);
  },
),

// Navigation with query parameters
context.goNamed(
  'search',
  queryParameters: {
    'q': 'flutter',
    'category': 'tutorials',
  },
);
// Results in: /search?q=flutter&category=tutorials
```

### Extra Data

```dart
// Pass complex objects
context.go('/product-detail', extra: product);

// Access in route
GoRoute(
  path: '/product-detail',
  builder: (context, state) {
    final product = state.extra as Product?;
    return ProductDetailPage(product: product);
  },
),
```

## Nested Routes

```dart
GoRoute(
  path: '/products',
  name: 'products',
  builder: (context, state) => const ProductsPage(),
  routes: [
    GoRoute(
      path: 'create',
      name: 'product-create',
      builder: (context, state) => const ProductCreatePage(),
    ),
    GoRoute(
      path: ':id',
      name: 'product-detail',
      builder: (context, state) {
        final id = state.pathParameters['id']!;
        return ProductDetailPage(productId: id);
      },
      routes: [
        GoRoute(
          path: 'edit',
          name: 'product-edit',
          builder: (context, state) {
            final id = state.pathParameters['id']!;
            return ProductEditPage(productId: id);
          },
        ),
        GoRoute(
          path: 'reviews',
          name: 'product-reviews',
          builder: (context, state) {
            final id = state.pathParameters['id']!;
            return ProductReviewsPage(productId: id);
          },
        ),
      ],
    ),
  ],
),
```

## Shell Routes (Nested Navigation with Shell)

```dart
final router = GoRouter(
  initialLocation: '/home',
  routes: [
    ShellRoute(
      builder: (context, state, child) {
        return ScaffoldWithNavBar(child: child);
      },
      routes: [
        GoRoute(
          path: '/home',
          name: 'home',
          pageBuilder: (context, state) => const NoTransitionPage(
            child: HomePage(),
          ),
        ),
        GoRoute(
          path: '/search',
          name: 'search',
          pageBuilder: (context, state) => const NoTransitionPage(
            child: SearchPage(),
          ),
        ),
        GoRoute(
          path: '/profile',
          name: 'profile',
          pageBuilder: (context, state) => const NoTransitionPage(
            child: ProfilePage(),
          ),
        ),
      ],
    ),
    // Routes outside the shell
    GoRoute(
      path: '/login',
      name: 'login',
      builder: (context, state) => const LoginPage(),
    ),
  ],
);

class ScaffoldWithNavBar extends StatelessWidget {
  final Widget child;

  const ScaffoldWithNavBar({required this.child});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: child,
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _calculateSelectedIndex(context),
        onTap: (index) => _onItemTapped(index, context),
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.home), label: 'Home'),
          BottomNavigationBarItem(icon: Icon(Icons.search), label: 'Search'),
          BottomNavigationBarItem(icon: Icon(Icons.person), label: 'Profile'),
        ],
      ),
    );
  }

  int _calculateSelectedIndex(BuildContext context) {
    final location = GoRouterState.of(context).uri.path;
    if (location.startsWith('/home')) return 0;
    if (location.startsWith('/search')) return 1;
    if (location.startsWith('/profile')) return 2;
    return 0;
  }

  void _onItemTapped(int index, BuildContext context) {
    switch (index) {
      case 0:
        context.go('/home');
        break;
      case 1:
        context.go('/search');
        break;
      case 2:
        context.go('/profile');
        break;
    }
  }
}
```

## StatefulShellRoute (Preserves State)

```dart
final router = GoRouter(
  initialLocation: '/home',
  routes: [
    StatefulShellRoute.indexedStack(
      builder: (context, state, navigationShell) {
        return ScaffoldWithNavBar(navigationShell: navigationShell);
      },
      branches: [
        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/home',
              name: 'home',
              builder: (context, state) => const HomePage(),
              routes: [
                GoRoute(
                  path: 'details/:id',
                  name: 'home-details',
                  builder: (context, state) {
                    final id = state.pathParameters['id']!;
                    return DetailsPage(id: id);
                  },
                ),
              ],
            ),
          ],
        ),
        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/search',
              name: 'search',
              builder: (context, state) => const SearchPage(),
            ),
          ],
        ),
        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/profile',
              name: 'profile',
              builder: (context, state) => const ProfilePage(),
            ),
          ],
        ),
      ],
    ),
  ],
);

class ScaffoldWithNavBar extends StatelessWidget {
  final StatefulNavigationShell navigationShell;

  const ScaffoldWithNavBar({required this.navigationShell});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: navigationShell,
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: navigationShell.currentIndex,
        onTap: (index) => navigationShell.goBranch(
          index,
          initialLocation: index == navigationShell.currentIndex,
        ),
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.home), label: 'Home'),
          BottomNavigationBarItem(icon: Icon(Icons.search), label: 'Search'),
          BottomNavigationBarItem(icon: Icon(Icons.person), label: 'Profile'),
        ],
      ),
    );
  }
}
```

## Redirect and Guards

```dart
final router = GoRouter(
  initialLocation: '/',
  redirect: (context, state) {
    final isLoggedIn = authNotifier.isAuthenticated;
    final isLoggingIn = state.matchedLocation == '/login';
    final isOnboarding = state.matchedLocation == '/onboarding';

    // If not logged in and not on login page, redirect to login
    if (!isLoggedIn && !isLoggingIn && !isOnboarding) {
      return '/login';
    }

    // If logged in and on login page, redirect to home
    if (isLoggedIn && isLoggingIn) {
      return '/';
    }

    // No redirect needed
    return null;
  },
  refreshListenable: authNotifier, // Refresh routes when auth changes
  routes: [...],
);

// Route-level redirect
GoRoute(
  path: '/admin',
  redirect: (context, state) {
    final user = context.read<AuthNotifier>().user;
    if (user?.role != 'admin') {
      return '/unauthorized';
    }
    return null;
  },
  builder: (context, state) => const AdminPage(),
),
```

## Custom Page Transitions

```dart
GoRoute(
  path: '/product/:id',
  pageBuilder: (context, state) {
    final id = state.pathParameters['id']!;
    return CustomTransitionPage(
      key: state.pageKey,
      child: ProductDetailPage(productId: id),
      transitionsBuilder: (context, animation, secondaryAnimation, child) {
        return FadeTransition(
          opacity: animation,
          child: child,
        );
      },
    );
  },
),

// Slide transition
pageBuilder: (context, state) => CustomTransitionPage(
  key: state.pageKey,
  child: const SettingsPage(),
  transitionsBuilder: (context, animation, secondaryAnimation, child) {
    const begin = Offset(1.0, 0.0);
    const end = Offset.zero;
    const curve = Curves.easeInOut;
    var tween = Tween(begin: begin, end: end).chain(CurveTween(curve: curve));
    return SlideTransition(
      position: animation.drive(tween),
      child: child,
    );
  },
),

// No transition (for tabs)
pageBuilder: (context, state) => const NoTransitionPage(
  child: HomePage(),
),
```

## Error Handling

```dart
final router = GoRouter(
  errorBuilder: (context, state) => ErrorPage(
    error: state.error,
  ),
  // Or use errorPageBuilder for custom transitions
  errorPageBuilder: (context, state) => MaterialPage(
    child: ErrorPage(error: state.error),
  ),
  routes: [...],
);

class ErrorPage extends StatelessWidget {
  final Exception? error;

  const ErrorPage({this.error});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Error')),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error, size: 64, color: Colors.red),
            const SizedBox(height: 16),
            Text('Page not found'),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () => context.go('/'),
              child: const Text('Go Home'),
            ),
          ],
        ),
      ),
    );
  }
}
```

## Type-Safe Routes with go_router_builder

```dart
// pubspec.yaml
dev_dependencies:
  go_router_builder: ^2.4.1
  build_runner: ^2.4.6

// routes.dart
part 'routes.g.dart';

@TypedGoRoute<HomeRoute>(
  path: '/',
  routes: [
    TypedGoRoute<ProductsRoute>(
      path: 'products',
      routes: [
        TypedGoRoute<ProductDetailRoute>(path: ':id'),
      ],
    ),
  ],
)
class HomeRoute extends GoRouteData {
  @override
  Widget build(BuildContext context, GoRouterState state) => const HomePage();
}

class ProductsRoute extends GoRouteData {
  @override
  Widget build(BuildContext context, GoRouterState state) => const ProductsPage();
}

class ProductDetailRoute extends GoRouteData {
  final String id;

  const ProductDetailRoute({required this.id});

  @override
  Widget build(BuildContext context, GoRouterState state) {
    return ProductDetailPage(productId: id);
  }
}

// Usage
const ProductDetailRoute(id: '123').go(context);
const HomeRoute().push(context);
```

## With Riverpod

```dart
@riverpod
GoRouter router(RouterRef ref) {
  final authState = ref.watch(authProvider);

  return GoRouter(
    initialLocation: '/',
    redirect: (context, state) {
      final isLoggedIn = authState.maybeWhen(
        authenticated: (_) => true,
        orElse: () => false,
      );

      if (!isLoggedIn && !state.matchedLocation.startsWith('/login')) {
        return '/login';
      }
      if (isLoggedIn && state.matchedLocation == '/login') {
        return '/';
      }
      return null;
    },
    routes: [...],
  );
}

class MyApp extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(routerProvider);
    return MaterialApp.router(routerConfig: router);
  }
}
```

## Best Practices

1. **Use named routes** - Easier refactoring and type-safety
2. **Organize routes by feature** - Define routes in feature modules
3. **Use ShellRoute for bottom nav** - Keeps navigation state
4. **Implement redirects** - Handle auth and permissions
5. **Handle errors** - Custom 404 and error pages
6. **Use go_router_builder** - Type-safe route generation
