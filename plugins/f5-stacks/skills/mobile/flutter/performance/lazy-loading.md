---
name: flutter-lazy-loading
description: Lazy loading and pagination patterns in Flutter
applies_to: flutter
---

# Flutter Lazy Loading

## Overview

Lazy loading defers the loading of data until it's needed, improving initial load times and reducing memory usage. Essential for lists, images, and large datasets.

## Infinite Scroll with Pagination

### Basic Implementation

```dart
class PaginatedList extends StatefulWidget {
  const PaginatedList({super.key});

  @override
  State<PaginatedList> createState() => _PaginatedListState();
}

class _PaginatedListState extends State<PaginatedList> {
  final List<Product> _products = [];
  final ScrollController _scrollController = ScrollController();
  bool _isLoading = false;
  bool _hasMore = true;
  int _page = 1;
  static const _pageSize = 20;

  @override
  void initState() {
    super.initState();
    _loadProducts();
    _scrollController.addListener(_onScroll);
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  void _onScroll() {
    if (_isLoading || !_hasMore) return;

    final maxScroll = _scrollController.position.maxScrollExtent;
    final currentScroll = _scrollController.position.pixels;
    final threshold = maxScroll * 0.9;

    if (currentScroll >= threshold) {
      _loadProducts();
    }
  }

  Future<void> _loadProducts() async {
    if (_isLoading) return;

    setState(() => _isLoading = true);

    try {
      final newProducts = await ProductRepository().getProducts(
        page: _page,
        pageSize: _pageSize,
      );

      setState(() {
        _products.addAll(newProducts);
        _page++;
        _hasMore = newProducts.length == _pageSize;
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
      // Handle error
    }
  }

  Future<void> _refresh() async {
    setState(() {
      _products.clear();
      _page = 1;
      _hasMore = true;
    });
    await _loadProducts();
  }

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: _refresh,
      child: ListView.builder(
        controller: _scrollController,
        itemCount: _products.length + (_hasMore ? 1 : 0),
        itemBuilder: (context, index) {
          if (index == _products.length) {
            return const Center(
              child: Padding(
                padding: EdgeInsets.all(16),
                child: CircularProgressIndicator(),
              ),
            );
          }
          return ProductTile(product: _products[index]);
        },
      ),
    );
  }
}
```

### With BLoC

```dart
// Events
@freezed
class ProductsEvent with _$ProductsEvent {
  const factory ProductsEvent.loadMore() = LoadMoreProducts;
  const factory ProductsEvent.refresh() = RefreshProducts;
}

// State
@freezed
class ProductsState with _$ProductsState {
  const factory ProductsState({
    @Default([]) List<Product> products,
    @Default(1) int page,
    @Default(true) bool hasMore,
    @Default(false) bool isLoading,
    @Default(false) bool isRefreshing,
    String? error,
  }) = _ProductsState;
}

// BLoC
class ProductsBloc extends Bloc<ProductsEvent, ProductsState> {
  final ProductRepository _repository;
  static const _pageSize = 20;

  ProductsBloc(this._repository) : super(const ProductsState()) {
    on<LoadMoreProducts>(_onLoadMore);
    on<RefreshProducts>(_onRefresh);

    // Load initial data
    add(const LoadMoreProducts());
  }

  Future<void> _onLoadMore(
    LoadMoreProducts event,
    Emitter<ProductsState> emit,
  ) async {
    if (state.isLoading || !state.hasMore) return;

    emit(state.copyWith(isLoading: true, error: null));

    try {
      final products = await _repository.getProducts(
        page: state.page,
        pageSize: _pageSize,
      );

      emit(state.copyWith(
        products: [...state.products, ...products],
        page: state.page + 1,
        hasMore: products.length == _pageSize,
        isLoading: false,
      ));
    } catch (e) {
      emit(state.copyWith(
        isLoading: false,
        error: e.toString(),
      ));
    }
  }

  Future<void> _onRefresh(
    RefreshProducts event,
    Emitter<ProductsState> emit,
  ) async {
    emit(state.copyWith(isRefreshing: true, error: null));

    try {
      final products = await _repository.getProducts(
        page: 1,
        pageSize: _pageSize,
      );

      emit(ProductsState(
        products: products,
        page: 2,
        hasMore: products.length == _pageSize,
        isRefreshing: false,
      ));
    } catch (e) {
      emit(state.copyWith(
        isRefreshing: false,
        error: e.toString(),
      ));
    }
  }
}

// Widget
class ProductsScreen extends StatelessWidget {
  const ProductsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<ProductsBloc, ProductsState>(
      builder: (context, state) {
        return NotificationListener<ScrollNotification>(
          onNotification: (notification) {
            if (notification is ScrollEndNotification &&
                notification.metrics.pixels >=
                    notification.metrics.maxScrollExtent * 0.9) {
              context.read<ProductsBloc>().add(const LoadMoreProducts());
            }
            return false;
          },
          child: RefreshIndicator(
            onRefresh: () async {
              context.read<ProductsBloc>().add(const RefreshProducts());
              await context.read<ProductsBloc>().stream.firstWhere(
                    (s) => !s.isRefreshing,
                  );
            },
            child: _buildList(state),
          ),
        );
      },
    );
  }

  Widget _buildList(ProductsState state) {
    if (state.products.isEmpty && state.isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (state.products.isEmpty && state.error != null) {
      return Center(child: Text('Error: ${state.error}'));
    }

    return ListView.builder(
      itemCount: state.products.length + (state.hasMore ? 1 : 0),
      itemBuilder: (context, index) {
        if (index == state.products.length) {
          return const LoadingIndicator();
        }
        return ProductTile(product: state.products[index]);
      },
    );
  }
}
```

### With Riverpod

```dart
// State class
@freezed
class PaginatedData<T> with _$PaginatedData<T> {
  const factory PaginatedData({
    @Default([]) List<T> items,
    @Default(1) int page,
    @Default(true) bool hasMore,
    @Default(false) bool isLoading,
  }) = _PaginatedData<T>;
}

// Notifier
@riverpod
class ProductsNotifier extends _$ProductsNotifier {
  static const _pageSize = 20;

  @override
  PaginatedData<Product> build() {
    _loadInitial();
    return const PaginatedData();
  }

  Future<void> _loadInitial() async {
    state = state.copyWith(isLoading: true);

    try {
      final products = await ref.read(productRepositoryProvider).getProducts(
            page: 1,
            pageSize: _pageSize,
          );

      state = state.copyWith(
        items: products,
        page: 2,
        hasMore: products.length == _pageSize,
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(isLoading: false);
      rethrow;
    }
  }

  Future<void> loadMore() async {
    if (state.isLoading || !state.hasMore) return;

    state = state.copyWith(isLoading: true);

    try {
      final products = await ref.read(productRepositoryProvider).getProducts(
            page: state.page,
            pageSize: _pageSize,
          );

      state = state.copyWith(
        items: [...state.items, ...products],
        page: state.page + 1,
        hasMore: products.length == _pageSize,
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(isLoading: false);
      rethrow;
    }
  }

  Future<void> refresh() async {
    state = const PaginatedData();
    await _loadInitial();
  }
}

// Widget
class ProductsScreen extends ConsumerWidget {
  const ProductsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final data = ref.watch(productsNotifierProvider);

    return NotificationListener<ScrollNotification>(
      onNotification: (notification) {
        if (notification is ScrollEndNotification &&
            notification.metrics.pixels >=
                notification.metrics.maxScrollExtent * 0.9) {
          ref.read(productsNotifierProvider.notifier).loadMore();
        }
        return false;
      },
      child: RefreshIndicator(
        onRefresh: () => ref.read(productsNotifierProvider.notifier).refresh(),
        child: ListView.builder(
          itemCount: data.items.length + (data.hasMore ? 1 : 0),
          itemBuilder: (context, index) {
            if (index == data.items.length) {
              return const LoadingIndicator();
            }
            return ProductTile(product: data.items[index]);
          },
        ),
      ),
    );
  }
}
```

## Infinite Scroll with Sliver

```dart
class SliverPaginatedList extends StatefulWidget {
  const SliverPaginatedList({super.key});

  @override
  State<SliverPaginatedList> createState() => _SliverPaginatedListState();
}

class _SliverPaginatedListState extends State<SliverPaginatedList> {
  final List<Product> _products = [];
  bool _isLoading = false;
  bool _hasMore = true;
  int _page = 1;

  @override
  void initState() {
    super.initState();
    _loadProducts();
  }

  Future<void> _loadProducts() async {
    if (_isLoading || !_hasMore) return;

    setState(() => _isLoading = true);

    final products = await ProductRepository().getProducts(
      page: _page,
      pageSize: 20,
    );

    setState(() {
      _products.addAll(products);
      _page++;
      _hasMore = products.length == 20;
      _isLoading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return CustomScrollView(
      slivers: [
        const SliverAppBar(
          title: Text('Products'),
          floating: true,
        ),
        SliverList(
          delegate: SliverChildBuilderDelegate(
            (context, index) {
              if (index == _products.length) {
                if (_hasMore) {
                  _loadProducts();
                  return const LoadingIndicator();
                }
                return const SizedBox.shrink();
              }
              return ProductTile(product: _products[index]);
            },
            childCount: _products.length + 1,
          ),
        ),
      ],
    );
  }
}
```

## Lazy Loading Tabs

```dart
class LazyTabView extends StatefulWidget {
  const LazyTabView({super.key});

  @override
  State<LazyTabView> createState() => _LazyTabViewState();
}

class _LazyTabViewState extends State<LazyTabView>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final Set<int> _loadedTabs = {0}; // First tab loaded by default

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
    _tabController.addListener(_onTabChanged);
  }

  void _onTabChanged() {
    if (!_tabController.indexIsChanging) {
      final index = _tabController.index;
      if (!_loadedTabs.contains(index)) {
        setState(() {
          _loadedTabs.add(index);
        });
      }
    }
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Lazy Tabs'),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: 'Home'),
            Tab(text: 'Products'),
            Tab(text: 'Orders'),
            Tab(text: 'Profile'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          const HomeTab(),
          _loadedTabs.contains(1)
              ? const ProductsTab()
              : const LoadingPlaceholder(),
          _loadedTabs.contains(2)
              ? const OrdersTab()
              : const LoadingPlaceholder(),
          _loadedTabs.contains(3)
              ? const ProfileTab()
              : const LoadingPlaceholder(),
        ],
      ),
    );
  }
}

class LoadingPlaceholder extends StatelessWidget {
  const LoadingPlaceholder({super.key});

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: CircularProgressIndicator(),
    );
  }
}
```

## Lazy Loading with Visibility Detection

```dart
import 'package:visibility_detector/visibility_detector.dart';

class LazyLoadWidget extends StatefulWidget {
  final String id;
  final Widget Function() builder;

  const LazyLoadWidget({
    required this.id,
    required this.builder,
    super.key,
  });

  @override
  State<LazyLoadWidget> createState() => _LazyLoadWidgetState();
}

class _LazyLoadWidgetState extends State<LazyLoadWidget> {
  bool _isLoaded = false;

  @override
  Widget build(BuildContext context) {
    if (_isLoaded) {
      return widget.builder();
    }

    return VisibilityDetector(
      key: Key(widget.id),
      onVisibilityChanged: (info) {
        if (info.visibleFraction > 0 && !_isLoaded) {
          setState(() => _isLoaded = true);
        }
      },
      child: const SizedBox(
        height: 200,
        child: Center(child: CircularProgressIndicator()),
      ),
    );
  }
}

// Usage
ListView.builder(
  itemCount: sections.length,
  itemBuilder: (context, index) {
    return LazyLoadWidget(
      id: 'section_$index',
      builder: () => ExpensiveSection(data: sections[index]),
    );
  },
)
```

## Skeleton Loading

```dart
import 'package:shimmer/shimmer.dart';

class ProductListSkeleton extends StatelessWidget {
  const ProductListSkeleton({super.key});

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      itemCount: 10,
      itemBuilder: (context, index) => const ProductTileSkeleton(),
    );
  }
}

class ProductTileSkeleton extends StatelessWidget {
  const ProductTileSkeleton({super.key});

  @override
  Widget build(BuildContext context) {
    return Shimmer.fromColors(
      baseColor: Colors.grey[300]!,
      highlightColor: Colors.grey[100]!,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            // Image placeholder
            Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(8),
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Title placeholder
                  Container(
                    height: 16,
                    width: double.infinity,
                    color: Colors.white,
                  ),
                  const SizedBox(height: 8),
                  // Subtitle placeholder
                  Container(
                    height: 12,
                    width: 150,
                    color: Colors.white,
                  ),
                  const SizedBox(height: 8),
                  // Price placeholder
                  Container(
                    height: 14,
                    width: 80,
                    color: Colors.white,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// Usage with state
class ProductList extends StatelessWidget {
  const ProductList({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<ProductsBloc, ProductsState>(
      builder: (context, state) {
        if (state.isInitialLoading) {
          return const ProductListSkeleton();
        }

        return ListView.builder(
          itemCount: state.products.length,
          itemBuilder: (context, index) {
            return ProductTile(product: state.products[index]);
          },
        );
      },
    );
  }
}
```

## Preloading Data

```dart
class PreloadingList extends StatefulWidget {
  const PreloadingList({super.key});

  @override
  State<PreloadingList> createState() => _PreloadingListState();
}

class _PreloadingListState extends State<PreloadingList> {
  final List<Product> _products = [];
  final Map<int, Product?> _cache = {};
  int _currentPage = 1;
  bool _hasMore = true;

  @override
  void initState() {
    super.initState();
    _loadPage(1);
    _preloadPage(2); // Preload next page
  }

  Future<void> _loadPage(int page) async {
    final products = await ProductRepository().getProducts(page: page);
    setState(() {
      _products.addAll(products);
      _hasMore = products.isNotEmpty;
    });
  }

  Future<void> _preloadPage(int page) async {
    final products = await ProductRepository().getProducts(page: page);
    for (var i = 0; i < products.length; i++) {
      _cache[(page - 1) * 20 + i] = products[i];
    }
  }

  void _onScroll(int visibleIndex) {
    final totalLoaded = _products.length;
    final threshold = totalLoaded - 5;

    if (visibleIndex >= threshold && _hasMore) {
      _currentPage++;
      _loadPage(_currentPage);
      _preloadPage(_currentPage + 1);
    }
  }

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      itemCount: _products.length,
      itemBuilder: (context, index) {
        _onScroll(index);
        return ProductTile(product: _products[index]);
      },
    );
  }
}
```

## Cursor-Based Pagination

```dart
class CursorPaginatedList extends StatefulWidget {
  const CursorPaginatedList({super.key});

  @override
  State<CursorPaginatedList> createState() => _CursorPaginatedListState();
}

class _CursorPaginatedListState extends State<CursorPaginatedList> {
  final List<Message> _messages = [];
  String? _cursor;
  bool _isLoading = false;
  bool _hasMore = true;

  @override
  void initState() {
    super.initState();
    _loadMessages();
  }

  Future<void> _loadMessages() async {
    if (_isLoading || !_hasMore) return;

    setState(() => _isLoading = true);

    try {
      final result = await MessageRepository().getMessages(
        cursor: _cursor,
        limit: 20,
      );

      setState(() {
        _messages.addAll(result.messages);
        _cursor = result.nextCursor;
        _hasMore = result.hasMore;
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return NotificationListener<ScrollNotification>(
      onNotification: (notification) {
        if (notification is ScrollEndNotification &&
            notification.metrics.pixels >=
                notification.metrics.maxScrollExtent * 0.9) {
          _loadMessages();
        }
        return false;
      },
      child: ListView.builder(
        itemCount: _messages.length + (_hasMore ? 1 : 0),
        itemBuilder: (context, index) {
          if (index == _messages.length) {
            return const LoadingIndicator();
          }
          return MessageTile(message: _messages[index]);
        },
      ),
    );
  }
}

class PaginatedResult<T> {
  final List<T> messages;
  final String? nextCursor;
  final bool hasMore;

  PaginatedResult({
    required this.messages,
    this.nextCursor,
    required this.hasMore,
  });
}
```

## Best Practices

1. **Use ScrollController wisely** - Dispose and manage scroll listeners
2. **Show loading states** - Use skeletons or spinners for better UX
3. **Handle errors gracefully** - Show retry options on failure
4. **Preload when possible** - Anticipate user scroll behavior
5. **Use proper thresholds** - Load before reaching the end (80-90%)
6. **Cache loaded data** - Avoid reloading on back navigation
7. **Support pull-to-refresh** - Let users manually refresh data
