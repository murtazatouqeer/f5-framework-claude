---
name: flutter-optimization
description: Flutter performance optimization techniques
applies_to: flutter
---

# Flutter Performance Optimization

## Overview

Flutter apps can achieve 60fps or even 120fps with proper optimization. Understanding the render pipeline and common performance pitfalls is key to building smooth apps.

## Build Optimization

### const Constructors

```dart
// ❌ Bad - Creates new instance every build
class MyWidget extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.blue,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Text('Hello'),
    );
  }
}

// ✅ Good - Uses const where possible
class MyWidget extends StatelessWidget {
  const MyWidget({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: Colors.blue,
        borderRadius: BorderRadius.all(Radius.circular(8)),
      ),
      child: const Text('Hello'),
    );
  }
}
```

### Widget Splitting

```dart
// ❌ Bad - Entire tree rebuilds on animation
class AnimatedScreen extends StatefulWidget {
  @override
  State<AnimatedScreen> createState() => _AnimatedScreenState();
}

class _AnimatedScreenState extends State<AnimatedScreen>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 1),
    )..repeat();
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // This rebuilds on every animation frame
        ExpensiveWidget(),
        AnimatedBuilder(
          animation: _controller,
          builder: (context, child) {
            return Transform.rotate(
              angle: _controller.value * 2 * pi,
              child: child,
            );
          },
          child: const Icon(Icons.refresh),
        ),
      ],
    );
  }
}

// ✅ Good - Only animated widget rebuilds
class AnimatedScreen extends StatelessWidget {
  const AnimatedScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Static - doesn't rebuild
        const ExpensiveWidget(),
        // Animated - has its own state
        const SpinningIcon(),
      ],
    );
  }
}

class SpinningIcon extends StatefulWidget {
  const SpinningIcon({super.key});

  @override
  State<SpinningIcon> createState() => _SpinningIconState();
}

class _SpinningIconState extends State<SpinningIcon>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 1),
    )..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return Transform.rotate(
          angle: _controller.value * 2 * pi,
          child: child,
        );
      },
      child: const Icon(Icons.refresh),
    );
  }
}
```

### RepaintBoundary

```dart
// Use RepaintBoundary to isolate expensive paint operations
class OptimizedList extends StatelessWidget {
  final List<Item> items;

  const OptimizedList({required this.items, super.key});

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      itemCount: items.length,
      itemBuilder: (context, index) {
        return RepaintBoundary(
          child: ComplexListItem(item: items[index]),
        );
      },
    );
  }
}

// Use for expensive custom painters
class ExpensiveChart extends StatelessWidget {
  final List<DataPoint> data;

  const ExpensiveChart({required this.data, super.key});

  @override
  Widget build(BuildContext context) {
    return RepaintBoundary(
      child: CustomPaint(
        painter: ChartPainter(data),
        size: const Size(300, 200),
      ),
    );
  }
}
```

## List Optimization

### ListView.builder

```dart
// ❌ Bad - Creates all items at once
ListView(
  children: items.map((item) => ItemWidget(item: item)).toList(),
)

// ✅ Good - Creates items lazily
ListView.builder(
  itemCount: items.length,
  itemBuilder: (context, index) => ItemWidget(item: items[index]),
)
```

### itemExtent for Fixed Height Items

```dart
// ❌ Bad - Calculates height for each item
ListView.builder(
  itemCount: items.length,
  itemBuilder: (context, index) => SizedBox(
    height: 60,
    child: ItemWidget(item: items[index]),
  ),
)

// ✅ Good - Uses known height for calculations
ListView.builder(
  itemCount: items.length,
  itemExtent: 60, // Fixed height known upfront
  itemBuilder: (context, index) => ItemWidget(item: items[index]),
)
```

### Sliver-based Lists

```dart
class OptimizedScrollView extends StatelessWidget {
  final List<Product> products;
  final List<Category> categories;

  const OptimizedScrollView({
    required this.products,
    required this.categories,
    super.key,
  });

  @override
  Widget build(BuildContext context) {
    return CustomScrollView(
      slivers: [
        // App bar
        const SliverAppBar(
          title: Text('Products'),
          floating: true,
        ),

        // Horizontal category list
        SliverToBoxAdapter(
          child: SizedBox(
            height: 50,
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              itemCount: categories.length,
              itemBuilder: (context, index) =>
                  CategoryChip(category: categories[index]),
            ),
          ),
        ),

        // Grid of products
        SliverGrid(
          delegate: SliverChildBuilderDelegate(
            (context, index) => ProductCard(product: products[index]),
            childCount: products.length,
          ),
          gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: 2,
            childAspectRatio: 0.75,
          ),
        ),
      ],
    );
  }
}
```

### AutomaticKeepAlive

```dart
// Keep tab contents alive to prevent rebuilding
class TabContent extends StatefulWidget {
  final Widget child;

  const TabContent({required this.child, super.key});

  @override
  State<TabContent> createState() => _TabContentState();
}

class _TabContentState extends State<TabContent>
    with AutomaticKeepAliveClientMixin {
  @override
  bool get wantKeepAlive => true;

  @override
  Widget build(BuildContext context) {
    super.build(context); // Required
    return widget.child;
  }
}
```

## State Management Optimization

### Selective Rebuilds with Provider

```dart
// ❌ Bad - Entire consumer rebuilds
Consumer<CartProvider>(
  builder: (context, cart, child) {
    return Column(
      children: [
        Text('Items: ${cart.itemCount}'),
        Text('Total: ${cart.total}'),
        CartItemList(items: cart.items),
      ],
    );
  },
)

// ✅ Good - Selective rebuilds with Selector
Column(
  children: [
    Selector<CartProvider, int>(
      selector: (_, cart) => cart.itemCount,
      builder: (_, count, __) => Text('Items: $count'),
    ),
    Selector<CartProvider, double>(
      selector: (_, cart) => cart.total,
      builder: (_, total, __) => Text('Total: $total'),
    ),
    Consumer<CartProvider>(
      builder: (_, cart, __) => CartItemList(items: cart.items),
    ),
  ],
)
```

### Selective Rebuilds with Riverpod

```dart
// ❌ Bad - Rebuilds on any state change
class CartScreen extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final cart = ref.watch(cartProvider);

    return Column(
      children: [
        Text('Items: ${cart.itemCount}'),
        Text('Total: ${cart.total}'),
      ],
    );
  }
}

// ✅ Good - Only rebuilds on specific changes
class CartScreen extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final itemCount = ref.watch(cartProvider.select((c) => c.itemCount));
    final total = ref.watch(cartProvider.select((c) => c.total));

    return Column(
      children: [
        Text('Items: $itemCount'),
        Text('Total: $total'),
      ],
    );
  }
}
```

### BLoC buildWhen

```dart
// Only rebuild when relevant state changes
BlocBuilder<CartBloc, CartState>(
  buildWhen: (previous, current) {
    return previous.total != current.total;
  },
  builder: (context, state) {
    return Text('Total: \$${state.total}');
  },
)
```

## Memory Optimization

### Dispose Resources

```dart
class ResourcefulWidget extends StatefulWidget {
  @override
  State<ResourcefulWidget> createState() => _ResourcefulWidgetState();
}

class _ResourcefulWidgetState extends State<ResourcefulWidget> {
  late StreamSubscription<int> _subscription;
  late AnimationController _animationController;
  late TextEditingController _textController;
  late ScrollController _scrollController;

  @override
  void initState() {
    super.initState();
    _subscription = stream.listen((data) {});
    _animationController = AnimationController(vsync: this);
    _textController = TextEditingController();
    _scrollController = ScrollController();
  }

  @override
  void dispose() {
    // Always dispose resources
    _subscription.cancel();
    _animationController.dispose();
    _textController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Container();
  }
}
```

### Avoid Large Objects in State

```dart
// ❌ Bad - Stores full image in state
class ImageViewerState extends State<ImageViewer> {
  Uint8List? imageBytes; // Large object in memory

  Future<void> loadImage() async {
    imageBytes = await File(widget.path).readAsBytes();
    setState(() {});
  }
}

// ✅ Good - Use ImageProvider caching
class ImageViewer extends StatelessWidget {
  final String path;

  const ImageViewer({required this.path, super.key});

  @override
  Widget build(BuildContext context) {
    return Image.file(
      File(path),
      cacheWidth: 800, // Resize for memory efficiency
      cacheHeight: 800,
    );
  }
}
```

## Async Optimization

### Compute for Heavy Operations

```dart
import 'dart:isolate';
import 'package:flutter/foundation.dart';

// ❌ Bad - Blocks UI thread
Future<List<Product>> parseProducts(String json) async {
  final data = jsonDecode(json) as List;
  return data.map((e) => Product.fromJson(e)).toList();
}

// ✅ Good - Runs in separate isolate
Future<List<Product>> parseProducts(String json) async {
  return compute(_parseProducts, json);
}

List<Product> _parseProducts(String json) {
  final data = jsonDecode(json) as List;
  return data.map((e) => Product.fromJson(e)).toList();
}
```

### Debounce Expensive Operations

```dart
class SearchField extends StatefulWidget {
  final Future<void> Function(String) onSearch;

  const SearchField({required this.onSearch, super.key});

  @override
  State<SearchField> createState() => _SearchFieldState();
}

class _SearchFieldState extends State<SearchField> {
  final _controller = TextEditingController();
  Timer? _debounceTimer;

  void _onChanged(String value) {
    _debounceTimer?.cancel();
    _debounceTimer = Timer(const Duration(milliseconds: 500), () {
      widget.onSearch(value);
    });
  }

  @override
  void dispose() {
    _debounceTimer?.cancel();
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: _controller,
      onChanged: _onChanged,
      decoration: const InputDecoration(
        hintText: 'Search...',
        prefixIcon: Icon(Icons.search),
      ),
    );
  }
}
```

## Rendering Optimization

### Avoid Opacity Widget

```dart
// ❌ Bad - Causes offscreen buffer allocation
Opacity(
  opacity: 0.5,
  child: Container(
    color: Colors.blue,
    child: const Text('Hello'),
  ),
)

// ✅ Good - Use color opacity directly
Container(
  color: Colors.blue.withOpacity(0.5),
  child: const Text('Hello'),
)

// ✅ Good - Use AnimatedOpacity for transitions
AnimatedOpacity(
  opacity: _isVisible ? 1.0 : 0.0,
  duration: const Duration(milliseconds: 300),
  child: const ExpensiveWidget(),
)
```

### Avoid ClipRRect for Simple Cases

```dart
// ❌ Bad - Expensive clipping operation
ClipRRect(
  borderRadius: BorderRadius.circular(8),
  child: Container(
    color: Colors.blue,
  ),
)

// ✅ Good - Use decoration instead
Container(
  decoration: BoxDecoration(
    color: Colors.blue,
    borderRadius: BorderRadius.circular(8),
  ),
)

// ✅ Good - Use ClipRRect only for images
ClipRRect(
  borderRadius: BorderRadius.circular(8),
  child: Image.network(imageUrl),
)
```

## Profiling Tools

### DevTools Performance View

```dart
// Enable performance overlay
MaterialApp(
  showPerformanceOverlay: true,
  home: MyApp(),
)

// Enable checkerboard for layer optimization
MaterialApp(
  checkerboardRasterCacheImages: true,
  checkerboardOffscreenLayers: true,
  home: MyApp(),
)
```

### Timeline Events

```dart
import 'dart:developer';

Future<void> loadData() async {
  Timeline.startSync('loadData');

  Timeline.startSync('fetchFromNetwork');
  final data = await api.fetchData();
  Timeline.finishSync();

  Timeline.startSync('parseData');
  final parsed = parseData(data);
  Timeline.finishSync();

  Timeline.startSync('updateUI');
  setState(() => _data = parsed);
  Timeline.finishSync();

  Timeline.finishSync();
}
```

### Memory Profiling

```dart
// Track widget rebuilds
class MyWidget extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    debugPrint('MyWidget build');
    return Container();
  }
}

// Use Flutter DevTools Memory tab to:
// - Track object allocations
// - Identify memory leaks
// - Analyze garbage collection
```

## Build Configuration

### Release Mode Optimization

```bash
# Build with optimization flags
flutter build apk --release --split-per-abi

# Build with tree shaking
flutter build apk --release --split-debug-info=./debug-info

# Analyze bundle size
flutter build appbundle --analyze-size
```

### Deferred Components (Android)

```dart
// pubspec.yaml
flutter:
  deferred-components:
    - name: premium_features
      libraries:
        - package:my_app/premium/premium_library.dart

// Load deferred component
import 'package:my_app/premium/premium_library.dart' deferred as premium;

Future<void> loadPremiumFeatures() async {
  await premium.loadLibrary();
  // Use premium features
}
```

## Best Practices Summary

1. **Use const constructors** - Prevents unnecessary rebuilds
2. **Split widgets** - Isolate frequently rebuilding parts
3. **Use ListView.builder** - Lazy loading for long lists
4. **Avoid expensive widgets** - Opacity, ClipPath when possible
5. **Use compute()** - For heavy computations
6. **Dispose resources** - Always clean up subscriptions, controllers
7. **Profile regularly** - Use DevTools to identify bottlenecks
8. **Build in release mode** - Test performance in release builds
