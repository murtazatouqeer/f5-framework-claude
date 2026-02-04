---
name: flutter-widget
description: Template for Flutter custom widgets
applies_to: flutter
variables:
  - name: widget_name
    description: Name of the widget (PascalCase)
---

# Flutter Widget Template

## StatelessWidget

```dart
// lib/shared/widgets/{{widget_name}}.dart

import 'package:flutter/material.dart';

class {{widget_name}} extends StatelessWidget {
  final String title;
  final String? subtitle;
  final VoidCallback? onTap;

  const {{widget_name}}({
    required this.title,
    this.subtitle,
    this.onTap,
    super.key,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Card(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: theme.textTheme.titleMedium,
              ),
              if (subtitle != null) ...[
                const SizedBox(height: 4),
                Text(
                  subtitle!,
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
```

## StatefulWidget

```dart
// lib/shared/widgets/{{widget_name}}.dart

import 'package:flutter/material.dart';

class {{widget_name}} extends StatefulWidget {
  final String initialValue;
  final ValueChanged<String>? onChanged;
  final bool enabled;

  const {{widget_name}}({
    required this.initialValue,
    this.onChanged,
    this.enabled = true,
    super.key,
  });

  @override
  State<{{widget_name}}> createState() => _{{widget_name}}State();
}

class _{{widget_name}}State extends State<{{widget_name}}> {
  late String _value;

  @override
  void initState() {
    super.initState();
    _value = widget.initialValue;
  }

  @override
  void didUpdateWidget(covariant {{widget_name}} oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.initialValue != widget.initialValue) {
      _value = widget.initialValue;
    }
  }

  void _handleChange(String newValue) {
    setState(() => _value = newValue);
    widget.onChanged?.call(newValue);
  }

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: TextEditingController(text: _value),
      enabled: widget.enabled,
      onChanged: _handleChange,
      decoration: const InputDecoration(
        border: OutlineInputBorder(),
        labelText: 'Enter value',
      ),
    );
  }
}
```

## Widget with Animation

```dart
// lib/shared/widgets/{{widget_name}}.dart

import 'package:flutter/material.dart';

class Animated{{widget_name}} extends StatefulWidget {
  final Widget child;
  final Duration duration;
  final Curve curve;

  const Animated{{widget_name}}({
    required this.child,
    this.duration = const Duration(milliseconds: 300),
    this.curve = Curves.easeInOut,
    super.key,
  });

  @override
  State<Animated{{widget_name}}> createState() => _Animated{{widget_name}}State();
}

class _Animated{{widget_name}}State extends State<Animated{{widget_name}}>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _animation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: widget.duration,
      vsync: this,
    );
    _animation = CurvedAnimation(
      parent: _controller,
      curve: widget.curve,
    );
    _controller.forward();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return FadeTransition(
      opacity: _animation,
      child: SlideTransition(
        position: Tween<Offset>(
          begin: const Offset(0, 0.1),
          end: Offset.zero,
        ).animate(_animation),
        child: widget.child,
      ),
    );
  }
}
```

## List Item Widget

```dart
// lib/shared/widgets/{{widget_name}}_list_item.dart

import 'package:flutter/material.dart';

class {{widget_name}}ListItem extends StatelessWidget {
  final String title;
  final String? subtitle;
  final String? imageUrl;
  final Widget? trailing;
  final VoidCallback? onTap;
  final VoidCallback? onLongPress;

  const {{widget_name}}ListItem({
    required this.title,
    this.subtitle,
    this.imageUrl,
    this.trailing,
    this.onTap,
    this.onLongPress,
    super.key,
  });

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: imageUrl != null
          ? CircleAvatar(
              backgroundImage: NetworkImage(imageUrl!),
            )
          : const CircleAvatar(
              child: Icon(Icons.image),
            ),
      title: Text(title),
      subtitle: subtitle != null ? Text(subtitle!) : null,
      trailing: trailing ?? const Icon(Icons.chevron_right),
      onTap: onTap,
      onLongPress: onLongPress,
    );
  }
}
```

## Card Widget

```dart
// lib/shared/widgets/{{widget_name}}_card.dart

import 'package:flutter/material.dart';

class {{widget_name}}Card extends StatelessWidget {
  final String title;
  final String? description;
  final String? imageUrl;
  final String? price;
  final VoidCallback? onTap;
  final VoidCallback? onAddToCart;

  const {{widget_name}}Card({
    required this.title,
    this.description,
    this.imageUrl,
    this.price,
    this.onTap,
    this.onAddToCart,
    super.key,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Card(
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (imageUrl != null)
              AspectRatio(
                aspectRatio: 16 / 9,
                child: Image.network(
                  imageUrl!,
                  fit: BoxFit.cover,
                  errorBuilder: (_, __, ___) => Container(
                    color: Colors.grey[200],
                    child: const Icon(Icons.image, size: 48),
                  ),
                ),
              ),
            Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: theme.textTheme.titleMedium,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  if (description != null) ...[
                    const SizedBox(height: 4),
                    Text(
                      description!,
                      style: theme.textTheme.bodySmall,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                  if (price != null || onAddToCart != null) ...[
                    const SizedBox(height: 8),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        if (price != null)
                          Text(
                            price!,
                            style: theme.textTheme.titleSmall?.copyWith(
                              color: theme.colorScheme.primary,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        if (onAddToCart != null)
                          IconButton(
                            icon: const Icon(Icons.add_shopping_cart),
                            onPressed: onAddToCart,
                          ),
                      ],
                    ),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
```

## Input Widget

```dart
// lib/shared/widgets/{{widget_name}}_input.dart

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

class {{widget_name}}Input extends StatelessWidget {
  final TextEditingController? controller;
  final String label;
  final String? hint;
  final String? errorText;
  final bool obscureText;
  final TextInputType? keyboardType;
  final List<TextInputFormatter>? inputFormatters;
  final Widget? prefixIcon;
  final Widget? suffixIcon;
  final ValueChanged<String>? onChanged;
  final FormFieldValidator<String>? validator;
  final int? maxLines;
  final bool enabled;

  const {{widget_name}}Input({
    this.controller,
    required this.label,
    this.hint,
    this.errorText,
    this.obscureText = false,
    this.keyboardType,
    this.inputFormatters,
    this.prefixIcon,
    this.suffixIcon,
    this.onChanged,
    this.validator,
    this.maxLines = 1,
    this.enabled = true,
    super.key,
  });

  @override
  Widget build(BuildContext context) {
    return TextFormField(
      controller: controller,
      obscureText: obscureText,
      keyboardType: keyboardType,
      inputFormatters: inputFormatters,
      maxLines: maxLines,
      enabled: enabled,
      onChanged: onChanged,
      validator: validator,
      decoration: InputDecoration(
        labelText: label,
        hintText: hint,
        errorText: errorText,
        prefixIcon: prefixIcon,
        suffixIcon: suffixIcon,
        border: const OutlineInputBorder(),
        filled: true,
      ),
    );
  }
}
```

## Button Widget

```dart
// lib/shared/widgets/{{widget_name}}_button.dart

import 'package:flutter/material.dart';

enum {{widget_name}}ButtonType { primary, secondary, text }

class {{widget_name}}Button extends StatelessWidget {
  final String label;
  final VoidCallback? onPressed;
  final {{widget_name}}ButtonType type;
  final bool isLoading;
  final IconData? icon;
  final bool fullWidth;

  const {{widget_name}}Button({
    required this.label,
    this.onPressed,
    this.type = {{widget_name}}ButtonType.primary,
    this.isLoading = false,
    this.icon,
    this.fullWidth = false,
    super.key,
  });

  @override
  Widget build(BuildContext context) {
    final child = isLoading
        ? const SizedBox(
            height: 20,
            width: 20,
            child: CircularProgressIndicator(strokeWidth: 2),
          )
        : icon != null
            ? Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(icon, size: 18),
                  const SizedBox(width: 8),
                  Text(label),
                ],
              )
            : Text(label);

    Widget button;
    switch (type) {
      case {{widget_name}}ButtonType.primary:
        button = FilledButton(
          onPressed: isLoading ? null : onPressed,
          child: child,
        );
      case {{widget_name}}ButtonType.secondary:
        button = OutlinedButton(
          onPressed: isLoading ? null : onPressed,
          child: child,
        );
      case {{widget_name}}ButtonType.text:
        button = TextButton(
          onPressed: isLoading ? null : onPressed,
          child: child,
        );
    }

    if (fullWidth) {
      return SizedBox(
        width: double.infinity,
        child: button,
      );
    }

    return button;
  }
}
```

## Usage

Replace `{{widget_name}}` with actual widget name (e.g., `Product`, `User`, `Order`)
