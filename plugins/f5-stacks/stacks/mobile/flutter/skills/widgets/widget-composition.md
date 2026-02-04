---
name: flutter-widget-composition
description: Widget composition patterns in Flutter
applies_to: flutter
---

# Flutter Widget Composition

## Overview

Widget composition is Flutter's primary pattern for building UIs. Compose small, focused widgets into complex interfaces.

## Composition Over Inheritance

```dart
// BAD: Using inheritance
class StyledButton extends ElevatedButton {
  // This is harder to maintain and customize
}

// GOOD: Using composition
class PrimaryButton extends StatelessWidget {
  const PrimaryButton({
    super.key,
    required this.label,
    required this.onPressed,
    this.icon,
  });

  final String label;
  final VoidCallback? onPressed;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    return ElevatedButton.icon(
      onPressed: onPressed,
      icon: Icon(icon ?? Icons.check),
      label: Text(label),
      style: ElevatedButton.styleFrom(
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
      ),
    );
  }
}
```

## Slot Pattern

```dart
/// A card layout with configurable slots.
class SlottedCard extends StatelessWidget {
  const SlottedCard({
    super.key,
    this.header,
    required this.body,
    this.footer,
    this.actions,
  });

  final Widget? header;
  final Widget body;
  final Widget? footer;
  final List<Widget>? actions;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        mainAxisSize: MainAxisSize.min,
        children: [
          if (header != null)
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 0),
              child: header,
            ),
          Padding(
            padding: const EdgeInsets.all(16),
            child: body,
          ),
          if (footer != null)
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
              child: footer,
            ),
          if (actions != null && actions!.isNotEmpty)
            Padding(
              padding: const EdgeInsets.fromLTRB(8, 0, 8, 8),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: actions!,
              ),
            ),
        ],
      ),
    );
  }
}

// Usage
SlottedCard(
  header: const Text('Product Details', style: TextStyle(fontSize: 18)),
  body: Column(
    children: [
      Image.network(product.imageUrl),
      Text(product.description),
    ],
  ),
  footer: Text('\$${product.price}'),
  actions: [
    TextButton(onPressed: () {}, child: const Text('Cancel')),
    ElevatedButton(onPressed: () {}, child: const Text('Add to Cart')),
  ],
)
```

## Builder Pattern

```dart
/// A list builder with loading, empty, and error states.
class DataListBuilder<T> extends StatelessWidget {
  const DataListBuilder({
    super.key,
    required this.items,
    required this.itemBuilder,
    this.isLoading = false,
    this.error,
    this.emptyWidget,
    this.loadingWidget,
    this.errorBuilder,
    this.separatorBuilder,
    this.padding,
  });

  final List<T> items;
  final Widget Function(BuildContext, T, int) itemBuilder;
  final bool isLoading;
  final String? error;
  final Widget? emptyWidget;
  final Widget? loadingWidget;
  final Widget Function(String)? errorBuilder;
  final Widget Function(BuildContext, int)? separatorBuilder;
  final EdgeInsetsGeometry? padding;

  @override
  Widget build(BuildContext context) {
    if (isLoading && items.isEmpty) {
      return loadingWidget ?? const Center(child: CircularProgressIndicator());
    }

    if (error != null && items.isEmpty) {
      return errorBuilder?.call(error!) ??
          Center(child: Text(error!, style: const TextStyle(color: Colors.red)));
    }

    if (items.isEmpty) {
      return emptyWidget ?? const Center(child: Text('No items'));
    }

    if (separatorBuilder != null) {
      return ListView.separated(
        padding: padding,
        itemCount: items.length,
        separatorBuilder: separatorBuilder!,
        itemBuilder: (context, index) => itemBuilder(context, items[index], index),
      );
    }

    return ListView.builder(
      padding: padding,
      itemCount: items.length,
      itemBuilder: (context, index) => itemBuilder(context, items[index], index),
    );
  }
}

// Usage
DataListBuilder<Product>(
  items: products,
  isLoading: isLoading,
  error: error,
  emptyWidget: const EmptyProductsView(),
  separatorBuilder: (_, __) => const Divider(),
  itemBuilder: (context, product, index) => ProductListTile(product: product),
)
```

## Wrapper Pattern

```dart
/// A wrapper that adds tap feedback and loading state.
class TappableWrapper extends StatelessWidget {
  const TappableWrapper({
    super.key,
    required this.child,
    this.onTap,
    this.isLoading = false,
    this.borderRadius = 8.0,
  });

  final Widget child;
  final VoidCallback? onTap;
  final bool isLoading;
  final double borderRadius;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: isLoading ? null : onTap,
        borderRadius: BorderRadius.circular(borderRadius),
        child: Stack(
          children: [
            child,
            if (isLoading)
              Positioned.fill(
                child: Container(
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.7),
                    borderRadius: BorderRadius.circular(borderRadius),
                  ),
                  child: const Center(
                    child: SizedBox(
                      width: 24,
                      height: 24,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    ),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

// Usage
TappableWrapper(
  isLoading: isSubmitting,
  onTap: handleSubmit,
  child: const ProductCard(product: product),
)
```

## Decorator Pattern

```dart
/// A decorator that adds a badge to any widget.
class BadgeDecorator extends StatelessWidget {
  const BadgeDecorator({
    super.key,
    required this.child,
    this.count,
    this.showBadge = true,
    this.badgeColor,
    this.position = BadgePosition.topRight,
  });

  final Widget child;
  final int? count;
  final bool showBadge;
  final Color? badgeColor;
  final BadgePosition position;

  @override
  Widget build(BuildContext context) {
    if (!showBadge || (count != null && count! <= 0)) {
      return child;
    }

    return Stack(
      clipBehavior: Clip.none,
      children: [
        child,
        Positioned(
          top: position.isTop ? -4 : null,
          bottom: position.isTop ? null : -4,
          right: position.isRight ? -4 : null,
          left: position.isRight ? null : -4,
          child: _buildBadge(context),
        ),
      ],
    );
  }

  Widget _buildBadge(BuildContext context) {
    final theme = Theme.of(context);
    final color = badgeColor ?? theme.colorScheme.error;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      constraints: const BoxConstraints(minWidth: 18),
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(9),
      ),
      child: count != null
          ? Text(
              count! > 99 ? '99+' : '$count',
              style: theme.textTheme.labelSmall?.copyWith(
                color: Colors.white,
                fontWeight: FontWeight.bold,
              ),
              textAlign: TextAlign.center,
            )
          : const SizedBox(width: 8, height: 8),
    );
  }
}

enum BadgePosition {
  topRight,
  topLeft,
  bottomRight,
  bottomLeft;

  bool get isTop => this == topRight || this == topLeft;
  bool get isRight => this == topRight || this == bottomRight;
}

// Usage
BadgeDecorator(
  count: cartItemCount,
  child: IconButton(
    icon: const Icon(Icons.shopping_cart),
    onPressed: () {},
  ),
)
```

## Provider Pattern (Composition)

```dart
/// A provider widget that manages and provides data to children.
class DataProvider<T> extends StatefulWidget {
  const DataProvider({
    super.key,
    required this.create,
    required this.child,
    this.onDispose,
  });

  final T Function() create;
  final Widget child;
  final void Function(T)? onDispose;

  static T of<T>(BuildContext context) {
    final provider = context.dependOnInheritedWidgetOfExactType<_DataInherited<T>>();
    assert(provider != null, 'No DataProvider<$T> found in context');
    return provider!.data;
  }

  @override
  State<DataProvider<T>> createState() => _DataProviderState<T>();
}

class _DataProviderState<T> extends State<DataProvider<T>> {
  late final T _data;

  @override
  void initState() {
    super.initState();
    _data = widget.create();
  }

  @override
  void dispose() {
    widget.onDispose?.call(_data);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return _DataInherited<T>(
      data: _data,
      child: widget.child,
    );
  }
}

class _DataInherited<T> extends InheritedWidget {
  const _DataInherited({
    required this.data,
    required super.child,
  });

  final T data;

  @override
  bool updateShouldNotify(_DataInherited<T> oldWidget) => data != oldWidget.data;
}
```

## Best Practices

1. **Single responsibility** - Each widget does one thing well
2. **Composition over inheritance** - Combine widgets, don't extend
3. **Slot pattern** - Allow customization through widget slots
4. **Builder pattern** - Handle different states elegantly
5. **Keep widgets small** - Extract complex widgets into smaller ones
6. **Reusable primitives** - Build a library of composable widgets
