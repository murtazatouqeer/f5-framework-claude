---
name: flutter-navigator-2
description: Navigator 2.0 declarative routing in Flutter
applies_to: flutter
---

# Flutter Navigator 2.0

## Overview

Navigator 2.0 provides declarative routing with full control over the navigation stack. It's complex but powerful for apps requiring deep linking and web support.

## Core Components

### RouterDelegate

```dart
class AppRouterDelegate extends RouterDelegate<AppRoutePath>
    with ChangeNotifier, PopNavigatorRouterDelegateMixin<AppRoutePath> {

  @override
  final GlobalKey<NavigatorState> navigatorKey = GlobalKey<NavigatorState>();

  final AppState _appState;

  AppRouterDelegate(this._appState) {
    _appState.addListener(notifyListeners);
  }

  @override
  AppRoutePath get currentConfiguration {
    if (_appState.selectedProduct != null) {
      return AppRoutePath.product(_appState.selectedProduct!.id);
    }
    if (_appState.showCategories) {
      return AppRoutePath.categories();
    }
    return AppRoutePath.home();
  }

  @override
  Widget build(BuildContext context) {
    return Navigator(
      key: navigatorKey,
      pages: [
        MaterialPage(
          key: const ValueKey('HomePage'),
          child: HomePage(
            onProductSelected: _handleProductSelected,
            onCategoriesPressed: _handleCategoriesPressed,
          ),
        ),
        if (_appState.showCategories)
          const MaterialPage(
            key: ValueKey('CategoriesPage'),
            child: CategoriesPage(),
          ),
        if (_appState.selectedProduct != null)
          MaterialPage(
            key: ValueKey(_appState.selectedProduct),
            child: ProductDetailPage(
              product: _appState.selectedProduct!,
            ),
          ),
      ],
      onPopPage: (route, result) {
        if (!route.didPop(result)) return false;

        if (_appState.selectedProduct != null) {
          _appState.selectedProduct = null;
        } else if (_appState.showCategories) {
          _appState.showCategories = false;
        }
        return true;
      },
    );
  }

  @override
  Future<void> setNewRoutePath(AppRoutePath configuration) async {
    if (configuration.isProductPage) {
      _appState.selectedProduct = await _fetchProduct(configuration.productId!);
    } else if (configuration.isCategoriesPage) {
      _appState.showCategories = true;
    } else {
      _appState.selectedProduct = null;
      _appState.showCategories = false;
    }
  }

  void _handleProductSelected(Product product) {
    _appState.selectedProduct = product;
  }

  void _handleCategoriesPressed() {
    _appState.showCategories = true;
  }

  Future<Product> _fetchProduct(String id) async {
    // Fetch product from repository
    return Product(id: id, name: 'Product $id');
  }
}
```

### RouteInformationParser

```dart
class AppRouteInformationParser extends RouteInformationParser<AppRoutePath> {
  @override
  Future<AppRoutePath> parseRouteInformation(
    RouteInformation routeInformation,
  ) async {
    final uri = Uri.parse(routeInformation.location ?? '/');

    // Handle '/'
    if (uri.pathSegments.isEmpty) {
      return AppRoutePath.home();
    }

    // Handle '/categories'
    if (uri.pathSegments.length == 1 && uri.pathSegments[0] == 'categories') {
      return AppRoutePath.categories();
    }

    // Handle '/products/:id'
    if (uri.pathSegments.length == 2 && uri.pathSegments[0] == 'products') {
      final productId = uri.pathSegments[1];
      return AppRoutePath.product(productId);
    }

    // Handle unknown routes
    return AppRoutePath.unknown();
  }

  @override
  RouteInformation? restoreRouteInformation(AppRoutePath configuration) {
    if (configuration.isUnknown) {
      return const RouteInformation(location: '/404');
    }
    if (configuration.isHomePage) {
      return const RouteInformation(location: '/');
    }
    if (configuration.isCategoriesPage) {
      return const RouteInformation(location: '/categories');
    }
    if (configuration.isProductPage) {
      return RouteInformation(location: '/products/${configuration.productId}');
    }
    return null;
  }
}
```

### Route Path Configuration

```dart
class AppRoutePath {
  final String? productId;
  final bool isCategoriesPage;
  final bool isUnknown;

  AppRoutePath.home()
      : productId = null,
        isCategoriesPage = false,
        isUnknown = false;

  AppRoutePath.categories()
      : productId = null,
        isCategoriesPage = true,
        isUnknown = false;

  AppRoutePath.product(this.productId)
      : isCategoriesPage = false,
        isUnknown = false;

  AppRoutePath.unknown()
      : productId = null,
        isCategoriesPage = false,
        isUnknown = true;

  bool get isHomePage => productId == null && !isCategoriesPage && !isUnknown;
  bool get isProductPage => productId != null;
}
```

### App State

```dart
class AppState extends ChangeNotifier {
  Product? _selectedProduct;
  bool _showCategories = false;

  Product? get selectedProduct => _selectedProduct;
  set selectedProduct(Product? value) {
    _selectedProduct = value;
    notifyListeners();
  }

  bool get showCategories => _showCategories;
  set showCategories(bool value) {
    _showCategories = value;
    notifyListeners();
  }
}
```

## App Setup

```dart
class MyApp extends StatefulWidget {
  @override
  State<MyApp> createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> {
  final AppState _appState = AppState();
  late final AppRouterDelegate _routerDelegate;
  final AppRouteInformationParser _routeInformationParser =
      AppRouteInformationParser();

  @override
  void initState() {
    super.initState();
    _routerDelegate = AppRouterDelegate(_appState);
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'Navigator 2.0 Demo',
      routerDelegate: _routerDelegate,
      routeInformationParser: _routeInformationParser,
    );
  }
}
```

## Nested Navigation

```dart
class ShellRouterDelegate extends RouterDelegate<ShellRoutePath>
    with ChangeNotifier, PopNavigatorRouterDelegateMixin<ShellRoutePath> {

  @override
  final GlobalKey<NavigatorState> navigatorKey = GlobalKey<NavigatorState>();

  int _selectedIndex = 0;
  final List<GlobalKey<NavigatorState>> _navigatorKeys = [
    GlobalKey<NavigatorState>(),
    GlobalKey<NavigatorState>(),
    GlobalKey<NavigatorState>(),
  ];

  int get selectedIndex => _selectedIndex;
  set selectedIndex(int value) {
    _selectedIndex = value;
    notifyListeners();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _selectedIndex,
        children: [
          _buildNavigator(0, const HomePage()),
          _buildNavigator(1, const SearchPage()),
          _buildNavigator(2, const ProfilePage()),
        ],
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _selectedIndex,
        onTap: (index) => selectedIndex = index,
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.home), label: 'Home'),
          BottomNavigationBarItem(icon: Icon(Icons.search), label: 'Search'),
          BottomNavigationBarItem(icon: Icon(Icons.person), label: 'Profile'),
        ],
      ),
    );
  }

  Widget _buildNavigator(int index, Widget child) {
    return Navigator(
      key: _navigatorKeys[index],
      onGenerateRoute: (settings) {
        return MaterialPageRoute(
          builder: (_) => child,
          settings: settings,
        );
      },
    );
  }

  @override
  ShellRoutePath get currentConfiguration => ShellRoutePath(_selectedIndex);

  @override
  Future<void> setNewRoutePath(ShellRoutePath configuration) async {
    _selectedIndex = configuration.tabIndex;
  }
}
```

## Custom Page Transitions

```dart
class FadeTransitionPage<T> extends Page<T> {
  final Widget child;

  const FadeTransitionPage({
    required this.child,
    super.key,
    super.name,
  });

  @override
  Route<T> createRoute(BuildContext context) {
    return PageRouteBuilder<T>(
      settings: this,
      pageBuilder: (context, animation, secondaryAnimation) => child,
      transitionsBuilder: (context, animation, secondaryAnimation, child) {
        return FadeTransition(
          opacity: animation,
          child: child,
        );
      },
    );
  }
}

class SlideTransitionPage<T> extends Page<T> {
  final Widget child;
  final AxisDirection direction;

  const SlideTransitionPage({
    required this.child,
    this.direction = AxisDirection.left,
    super.key,
    super.name,
  });

  @override
  Route<T> createRoute(BuildContext context) {
    return PageRouteBuilder<T>(
      settings: this,
      pageBuilder: (context, animation, secondaryAnimation) => child,
      transitionsBuilder: (context, animation, secondaryAnimation, child) {
        final begin = _getBeginOffset();
        const end = Offset.zero;
        final tween = Tween(begin: begin, end: end).chain(
          CurveTween(curve: Curves.easeInOut),
        );

        return SlideTransition(
          position: animation.drive(tween),
          child: child,
        );
      },
    );
  }

  Offset _getBeginOffset() {
    switch (direction) {
      case AxisDirection.up:
        return const Offset(0, 1);
      case AxisDirection.down:
        return const Offset(0, -1);
      case AxisDirection.right:
        return const Offset(-1, 0);
      case AxisDirection.left:
      default:
        return const Offset(1, 0);
    }
  }
}
```

## Back Button Handling

```dart
class AppRouterDelegate extends RouterDelegate<AppRoutePath>
    with ChangeNotifier, PopNavigatorRouterDelegateMixin<AppRoutePath> {

  @override
  Future<bool> popRoute() async {
    // Handle Android back button
    if (_appState.selectedProduct != null) {
      _appState.selectedProduct = null;
      return true;
    }
    if (_appState.showCategories) {
      _appState.showCategories = false;
      return true;
    }
    // Return false to let the system handle it (exit app)
    return false;
  }
}

// Alternative: BackButtonDispatcher
class MyBackButtonDispatcher extends RootBackButtonDispatcher {
  final AppState _appState;

  MyBackButtonDispatcher(this._appState);

  @override
  Future<bool> didPopRoute() async {
    // Custom back button logic
    return super.didPopRoute();
  }
}
```

## Query Parameters

```dart
class AppRouteInformationParser extends RouteInformationParser<AppRoutePath> {
  @override
  Future<AppRoutePath> parseRouteInformation(
    RouteInformation routeInformation,
  ) async {
    final uri = Uri.parse(routeInformation.location ?? '/');

    // Handle '/search?q=query&category=electronics'
    if (uri.pathSegments.length == 1 && uri.pathSegments[0] == 'search') {
      final query = uri.queryParameters['q'];
      final category = uri.queryParameters['category'];
      return AppRoutePath.search(query: query, category: category);
    }

    return AppRoutePath.home();
  }

  @override
  RouteInformation? restoreRouteInformation(AppRoutePath configuration) {
    if (configuration.isSearchPage) {
      final params = <String, String>{};
      if (configuration.searchQuery != null) {
        params['q'] = configuration.searchQuery!;
      }
      if (configuration.category != null) {
        params['category'] = configuration.category!;
      }
      final uri = Uri(path: '/search', queryParameters: params);
      return RouteInformation(location: uri.toString());
    }
    return const RouteInformation(location: '/');
  }
}
```

## When to Use Navigator 2.0

### Use Navigator 2.0 When:
- Full deep linking support required
- Web app with browser navigation
- Complex nested navigation
- Complete control over navigation stack
- URL sync with app state

### Consider go_router Instead:
- Simpler API required
- Faster development time
- Type-safe routing
- Most common use cases

## Best Practices

1. **Use with go_router** - go_router wraps Navigator 2.0 with simpler API
2. **State-based navigation** - Pages reflect app state
3. **Handle all routes** - Include unknown/404 handling
4. **Restore state** - Implement state restoration for web
5. **Test deep links** - Verify URL parsing and restoration
6. **Keep state separate** - Navigation state vs business state
