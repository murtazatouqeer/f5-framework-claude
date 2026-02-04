---
name: flutter-stateless-widgets
description: Building StatelessWidget in Flutter
applies_to: flutter
---

# Flutter StatelessWidget

## Overview

StatelessWidget is immutable and doesn't hold any mutable state. Use when the widget doesn't need to change after being built.

## Basic StatelessWidget

```dart
import 'package:flutter/material.dart';

/// A simple greeting widget.
class GreetingText extends StatelessWidget {
  const GreetingText({
    super.key,
    required this.name,
  });

  final String name;

  @override
  Widget build(BuildContext context) {
    return Text(
      'Hello, $name!',
      style: Theme.of(context).textTheme.headlineMedium,
    );
  }
}

// Usage
GreetingText(name: 'Flutter')
```

## With Multiple Properties

```dart
/// A customizable button widget.
class PrimaryButton extends StatelessWidget {
  const PrimaryButton({
    super.key,
    required this.label,
    required this.onPressed,
    this.icon,
    this.isLoading = false,
    this.isDisabled = false,
  });

  final String label;
  final VoidCallback? onPressed;
  final IconData? icon;
  final bool isLoading;
  final bool isDisabled;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return ElevatedButton(
      onPressed: isDisabled || isLoading ? null : onPressed,
      style: ElevatedButton.styleFrom(
        backgroundColor: theme.colorScheme.primary,
        foregroundColor: theme.colorScheme.onPrimary,
        padding: const EdgeInsets.symmetric(
          horizontal: 24,
          vertical: 12,
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (isLoading)
            const SizedBox(
              width: 16,
              height: 16,
              child: CircularProgressIndicator(
                strokeWidth: 2,
                color: Colors.white,
              ),
            )
          else if (icon != null)
            Icon(icon, size: 18),
          if (icon != null || isLoading) const SizedBox(width: 8),
          Text(label),
        ],
      ),
    );
  }
}

// Usage
PrimaryButton(
  label: 'Save',
  icon: Icons.save,
  onPressed: () => saveData(),
  isLoading: isSaving,
)
```

## With Callbacks

```dart
/// A product card widget with actions.
class ProductCard extends StatelessWidget {
  const ProductCard({
    super.key,
    required this.product,
    this.onTap,
    this.onAddToCart,
    this.onFavorite,
  });

  final Product product;
  final VoidCallback? onTap;
  final void Function(Product)? onAddToCart;
  final void Function(Product, bool)? onFavorite;

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
            _buildActions(context),
          ],
        ),
      ),
    );
  }

  Widget _buildImage() {
    return AspectRatio(
      aspectRatio: 16 / 9,
      child: product.imageUrl != null
          ? Image.network(
              product.imageUrl!,
              fit: BoxFit.cover,
              errorBuilder: (_, __, ___) => _buildPlaceholder(),
            )
          : _buildPlaceholder(),
    );
  }

  Widget _buildPlaceholder() {
    return Container(
      color: Colors.grey[200],
      child: const Icon(Icons.image, size: 48),
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

  Widget _buildActions(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(12, 0, 12, 12),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          IconButton(
            icon: Icon(
              product.isFavorite ? Icons.favorite : Icons.favorite_border,
              color: product.isFavorite ? Colors.red : null,
            ),
            onPressed: () => onFavorite?.call(product, !product.isFavorite),
          ),
          FilledButton.icon(
            onPressed: () => onAddToCart?.call(product),
            icon: const Icon(Icons.add_shopping_cart, size: 18),
            label: const Text('Add'),
          ),
        ],
      ),
    );
  }
}
```

## Using Generics

```dart
/// A generic list item widget.
class ListItem<T> extends StatelessWidget {
  const ListItem({
    super.key,
    required this.item,
    required this.titleBuilder,
    this.subtitleBuilder,
    this.leadingBuilder,
    this.onTap,
  });

  final T item;
  final String Function(T) titleBuilder;
  final String Function(T)? subtitleBuilder;
  final Widget Function(T)? leadingBuilder;
  final void Function(T)? onTap;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: leadingBuilder?.call(item),
      title: Text(titleBuilder(item)),
      subtitle: subtitleBuilder != null
          ? Text(subtitleBuilder!(item))
          : null,
      trailing: const Icon(Icons.chevron_right),
      onTap: () => onTap?.call(item),
    );
  }
}

// Usage
ListItem<Product>(
  item: product,
  titleBuilder: (p) => p.name,
  subtitleBuilder: (p) => p.formattedPrice,
  leadingBuilder: (p) => CircleAvatar(
    backgroundImage: NetworkImage(p.imageUrl ?? ''),
  ),
  onTap: (p) => navigateToDetail(p.id),
)
```

## With Theme Extensions

```dart
/// A styled status badge.
class StatusBadge extends StatelessWidget {
  const StatusBadge({
    super.key,
    required this.status,
    this.size = StatusBadgeSize.medium,
  });

  final String status;
  final StatusBadgeSize size;

  @override
  Widget build(BuildContext context) {
    final colors = _getColors(context);
    final padding = _getPadding();
    final textStyle = _getTextStyle(context);

    return Container(
      padding: padding,
      decoration: BoxDecoration(
        color: colors.background,
        borderRadius: BorderRadius.circular(4),
      ),
      child: Text(
        status,
        style: textStyle.copyWith(color: colors.foreground),
      ),
    );
  }

  _StatusColors _getColors(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return switch (status.toLowerCase()) {
      'active' || 'success' => _StatusColors(
          Colors.green[50]!,
          Colors.green[700]!,
        ),
      'pending' || 'warning' => _StatusColors(
          Colors.orange[50]!,
          Colors.orange[700]!,
        ),
      'error' || 'failed' => _StatusColors(
          colorScheme.errorContainer,
          colorScheme.error,
        ),
      _ => _StatusColors(
          Colors.grey[100]!,
          Colors.grey[700]!,
        ),
    };
  }

  EdgeInsets _getPadding() {
    return switch (size) {
      StatusBadgeSize.small => const EdgeInsets.symmetric(
          horizontal: 6,
          vertical: 2,
        ),
      StatusBadgeSize.medium => const EdgeInsets.symmetric(
          horizontal: 8,
          vertical: 4,
        ),
      StatusBadgeSize.large => const EdgeInsets.symmetric(
          horizontal: 12,
          vertical: 6,
        ),
    };
  }

  TextStyle _getTextStyle(BuildContext context) {
    final theme = Theme.of(context);

    return switch (size) {
      StatusBadgeSize.small => theme.textTheme.labelSmall!,
      StatusBadgeSize.medium => theme.textTheme.labelMedium!,
      StatusBadgeSize.large => theme.textTheme.labelLarge!,
    };
  }
}

enum StatusBadgeSize { small, medium, large }

class _StatusColors {
  final Color background;
  final Color foreground;
  const _StatusColors(this.background, this.foreground);
}
```

## Best Practices

1. **Const constructors** - Always use const when possible
2. **Required parameters** - Mark essential props as required
3. **Final fields** - All fields should be final
4. **Private methods** - Extract complex build logic to private methods
5. **Theme usage** - Access theme from context, don't hardcode styles
6. **Documentation** - Add dartdoc comments for public widgets
7. **Key parameter** - Always include super.key in constructor
