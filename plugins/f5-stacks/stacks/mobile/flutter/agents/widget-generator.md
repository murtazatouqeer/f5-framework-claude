---
name: flutter-widget-generator
description: Generates reusable Flutter widgets
applies_to: flutter
---

# Flutter Widget Generator Agent

## Purpose

Generates reusable, well-documented Flutter widgets following best practices for composition and performance.

## Capabilities

- Generate StatelessWidget or StatefulWidget
- Create custom painters for complex UIs
- Generate animated widgets
- Add proper documentation and examples
- Include widget tests

## Input Requirements

| Field | Required | Description |
|-------|----------|-------------|
| `widget_name` | Yes | Widget name (PascalCase) |
| `type` | No | `stateless`, `stateful`, `animated` |
| `props` | No | List of widget properties |
| `has_callbacks` | No | Whether widget emits events |
| `location` | No | `shared` or feature-specific |

## Generated Files

```
{location}/widgets/
├── {widget_name}.dart
└── {widget_name}_test.dart (in test folder)
```

## Example Usage

```yaml
widget_name: ProductCard
type: stateless
props:
  - name: product
    type: Product
    required: true
  - name: onTap
    type: VoidCallback
    required: false
  - name: onFavorite
    type: Function(bool)
    required: false
location: features/products/presentation
```

## Output Pattern

### StatelessWidget

```dart
import 'package:flutter/material.dart';

/// A card widget displaying product information.
///
/// Example:
/// ```dart
/// ProductCard(
///   product: product,
///   onTap: () => navigateToDetail(product.id),
///   onFavorite: (isFavorite) => toggleFavorite(product.id),
/// )
/// ```
class ProductCard extends StatelessWidget {
  const ProductCard({
    super.key,
    required this.product,
    this.onTap,
    this.onFavorite,
  });

  final Product product;
  final VoidCallback? onTap;
  final void Function(bool)? onFavorite;

  @override
  Widget build(BuildContext context) {
    return Card(
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildImage(),
            _buildContent(context),
          ],
        ),
      ),
    );
  }

  Widget _buildImage() {
    return AspectRatio(
      aspectRatio: 16 / 9,
      child: product.imageUrl != null
          ? CachedNetworkImage(
              imageUrl: product.imageUrl!,
              fit: BoxFit.cover,
              placeholder: (_, __) => const ShimmerPlaceholder(),
              errorWidget: (_, __, ___) => const Icon(Icons.error),
            )
          : const PlaceholderImage(),
    );
  }

  Widget _buildContent(BuildContext context) {
    final theme = Theme.of(context);

    return Padding(
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            product.name,
            style: theme.textTheme.titleMedium,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
          const SizedBox(height: 4),
          Text(
            product.formattedPrice,
            style: theme.textTheme.titleLarge?.copyWith(
              color: theme.colorScheme.primary,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }
}
```

### StatefulWidget

```dart
class AnimatedProductCard extends StatefulWidget {
  const AnimatedProductCard({
    super.key,
    required this.product,
    this.onTap,
  });

  final Product product;
  final VoidCallback? onTap;

  @override
  State<AnimatedProductCard> createState() => _AnimatedProductCardState();
}

class _AnimatedProductCardState extends State<AnimatedProductCard>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  late final Animation<double> _scaleAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 150),
      vsync: this,
    );
    _scaleAnimation = Tween<double>(begin: 1.0, end: 0.95).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTapDown: (_) => _controller.forward(),
      onTapUp: (_) => _controller.reverse(),
      onTapCancel: () => _controller.reverse(),
      onTap: widget.onTap,
      child: ScaleTransition(
        scale: _scaleAnimation,
        child: ProductCard(product: widget.product),
      ),
    );
  }
}
```

## Best Practices

1. **Const constructors** - Always use const when possible
2. **Required vs optional** - Make essential props required
3. **Documentation** - Add dartdoc comments with examples
4. **Private methods** - Extract complex build logic
5. **Theme usage** - Use Theme.of(context) for styling
6. **Accessibility** - Include Semantics widgets
