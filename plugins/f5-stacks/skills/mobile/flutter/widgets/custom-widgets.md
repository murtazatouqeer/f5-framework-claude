---
name: flutter-custom-widgets
description: Building custom widgets in Flutter
applies_to: flutter
---

# Flutter Custom Widgets

## Overview

Custom widgets encapsulate reusable UI patterns with consistent styling and behavior.

## Custom Card Widget

```dart
import 'package:flutter/material.dart';

/// A customizable card with header, content, and optional actions.
class AppCard extends StatelessWidget {
  const AppCard({
    super.key,
    this.title,
    this.subtitle,
    this.leading,
    this.trailing,
    this.child,
    this.actions,
    this.onTap,
    this.padding,
    this.elevation,
  });

  final String? title;
  final String? subtitle;
  final Widget? leading;
  final Widget? trailing;
  final Widget? child;
  final List<Widget>? actions;
  final VoidCallback? onTap;
  final EdgeInsetsGeometry? padding;
  final double? elevation;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Card(
      elevation: elevation ?? 1,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: padding ?? const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              if (title != null || leading != null || trailing != null)
                _buildHeader(theme),
              if (child != null) ...[
                if (title != null) const SizedBox(height: 12),
                child!,
              ],
              if (actions != null && actions!.isNotEmpty) ...[
                const SizedBox(height: 16),
                _buildActions(),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildHeader(ThemeData theme) {
    return Row(
      children: [
        if (leading != null) ...[
          leading!,
          const SizedBox(width: 12),
        ],
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (title != null)
                Text(
                  title!,
                  style: theme.textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
                ),
              if (subtitle != null) ...[
                const SizedBox(height: 2),
                Text(
                  subtitle!,
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.textTheme.bodySmall?.color?.withOpacity(0.7),
                  ),
                ),
              ],
            ],
          ),
        ),
        if (trailing != null) trailing!,
      ],
    );
  }

  Widget _buildActions() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.end,
      children: actions!
          .expand((action) => [action, const SizedBox(width: 8)])
          .toList()
        ..removeLast(),
    );
  }
}

// Usage
AppCard(
  title: 'Order #12345',
  subtitle: 'Placed on Dec 15, 2024',
  leading: const CircleAvatar(child: Icon(Icons.shopping_bag)),
  trailing: const StatusBadge(status: 'Pending'),
  child: const Text('3 items • \$125.00'),
  actions: [
    TextButton(onPressed: () {}, child: const Text('Details')),
    FilledButton(onPressed: () {}, child: const Text('Track')),
  ],
)
```

## Custom Input Field

```dart
/// A styled text input with label, helper text, and error handling.
class AppTextField extends StatelessWidget {
  const AppTextField({
    super.key,
    this.controller,
    this.label,
    this.hint,
    this.helperText,
    this.errorText,
    this.prefixIcon,
    this.suffixIcon,
    this.obscureText = false,
    this.keyboardType,
    this.textInputAction,
    this.maxLines = 1,
    this.maxLength,
    this.onChanged,
    this.onSubmitted,
    this.validator,
    this.enabled = true,
    this.readOnly = false,
    this.autofocus = false,
  });

  final TextEditingController? controller;
  final String? label;
  final String? hint;
  final String? helperText;
  final String? errorText;
  final Widget? prefixIcon;
  final Widget? suffixIcon;
  final bool obscureText;
  final TextInputType? keyboardType;
  final TextInputAction? textInputAction;
  final int maxLines;
  final int? maxLength;
  final void Function(String)? onChanged;
  final void Function(String)? onSubmitted;
  final String? Function(String?)? validator;
  final bool enabled;
  final bool readOnly;
  final bool autofocus;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        if (label != null) ...[
          Text(
            label!,
            style: theme.textTheme.labelLarge?.copyWith(
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 8),
        ],
        TextFormField(
          controller: controller,
          obscureText: obscureText,
          keyboardType: keyboardType,
          textInputAction: textInputAction,
          maxLines: maxLines,
          maxLength: maxLength,
          onChanged: onChanged,
          onFieldSubmitted: onSubmitted,
          validator: validator,
          enabled: enabled,
          readOnly: readOnly,
          autofocus: autofocus,
          decoration: InputDecoration(
            hintText: hint,
            helperText: helperText,
            errorText: errorText,
            prefixIcon: prefixIcon,
            suffixIcon: suffixIcon,
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
              borderSide: BorderSide(color: theme.dividerColor),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
              borderSide: BorderSide(
                color: theme.colorScheme.primary,
                width: 2,
              ),
            ),
            errorBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
              borderSide: BorderSide(color: theme.colorScheme.error),
            ),
            filled: !enabled,
            fillColor: theme.disabledColor.withOpacity(0.1),
          ),
        ),
      ],
    );
  }
}
```

## Custom Dialog

```dart
/// A customizable dialog with title, content, and actions.
class AppDialog extends StatelessWidget {
  const AppDialog({
    super.key,
    required this.title,
    this.content,
    this.contentWidget,
    this.primaryAction,
    this.primaryActionLabel = 'OK',
    this.secondaryAction,
    this.secondaryActionLabel = 'Cancel',
    this.icon,
    this.iconColor,
    this.isDangerous = false,
  });

  final String title;
  final String? content;
  final Widget? contentWidget;
  final VoidCallback? primaryAction;
  final String primaryActionLabel;
  final VoidCallback? secondaryAction;
  final String secondaryActionLabel;
  final IconData? icon;
  final Color? iconColor;
  final bool isDangerous;

  static Future<bool?> show(
    BuildContext context, {
    required String title,
    String? content,
    Widget? contentWidget,
    VoidCallback? primaryAction,
    String primaryActionLabel = 'OK',
    VoidCallback? secondaryAction,
    String secondaryActionLabel = 'Cancel',
    IconData? icon,
    Color? iconColor,
    bool isDangerous = false,
  }) {
    return showDialog<bool>(
      context: context,
      builder: (context) => AppDialog(
        title: title,
        content: content,
        contentWidget: contentWidget,
        primaryAction: primaryAction,
        primaryActionLabel: primaryActionLabel,
        secondaryAction: secondaryAction,
        secondaryActionLabel: secondaryActionLabel,
        icon: icon,
        iconColor: iconColor,
        isDangerous: isDangerous,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final effectiveIconColor = iconColor ??
        (isDangerous ? theme.colorScheme.error : theme.colorScheme.primary);

    return AlertDialog(
      icon: icon != null
          ? Icon(icon, color: effectiveIconColor, size: 32)
          : null,
      title: Text(title, textAlign: TextAlign.center),
      content: contentWidget ??
          (content != null
              ? Text(content!, textAlign: TextAlign.center)
              : null),
      actionsAlignment: MainAxisAlignment.center,
      actions: [
        if (secondaryAction != null)
          TextButton(
            onPressed: () {
              Navigator.of(context).pop(false);
              secondaryAction?.call();
            },
            child: Text(secondaryActionLabel),
          ),
        FilledButton(
          onPressed: () {
            Navigator.of(context).pop(true);
            primaryAction?.call();
          },
          style: isDangerous
              ? FilledButton.styleFrom(
                  backgroundColor: theme.colorScheme.error,
                )
              : null,
          child: Text(primaryActionLabel),
        ),
      ],
    );
  }
}

// Usage
final confirmed = await AppDialog.show(
  context,
  title: 'Delete Product?',
  content: 'This action cannot be undone.',
  icon: Icons.delete,
  isDangerous: true,
  primaryActionLabel: 'Delete',
  secondaryAction: () {},
);
```

## Custom List Tile

```dart
/// An enhanced list tile with more customization options.
class AppListTile extends StatelessWidget {
  const AppListTile({
    super.key,
    required this.title,
    this.subtitle,
    this.leading,
    this.trailing,
    this.onTap,
    this.onLongPress,
    this.selected = false,
    this.enabled = true,
    this.dense = false,
    this.contentPadding,
    this.badge,
  });

  final String title;
  final String? subtitle;
  final Widget? leading;
  final Widget? trailing;
  final VoidCallback? onTap;
  final VoidCallback? onLongPress;
  final bool selected;
  final bool enabled;
  final bool dense;
  final EdgeInsetsGeometry? contentPadding;
  final String? badge;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Material(
      color: selected
          ? theme.colorScheme.primaryContainer.withOpacity(0.5)
          : Colors.transparent,
      child: InkWell(
        onTap: enabled ? onTap : null,
        onLongPress: enabled ? onLongPress : null,
        child: Padding(
          padding: contentPadding ??
              EdgeInsets.symmetric(
                horizontal: 16,
                vertical: dense ? 8 : 12,
              ),
          child: Row(
            children: [
              if (leading != null) ...[
                _buildLeading(theme),
                const SizedBox(width: 16),
              ],
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            title,
                            style: theme.textTheme.bodyLarge?.copyWith(
                              fontWeight: selected ? FontWeight.w600 : null,
                              color: enabled
                                  ? null
                                  : theme.disabledColor,
                            ),
                          ),
                        ),
                        if (badge != null) ...[
                          const SizedBox(width: 8),
                          _buildBadge(theme),
                        ],
                      ],
                    ),
                    if (subtitle != null) ...[
                      const SizedBox(height: 2),
                      Text(
                        subtitle!,
                        style: theme.textTheme.bodySmall?.copyWith(
                          color: enabled
                              ? theme.textTheme.bodySmall?.color
                              : theme.disabledColor,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              if (trailing != null) ...[
                const SizedBox(width: 16),
                trailing!,
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildLeading(ThemeData theme) {
    if (leading == null) return const SizedBox.shrink();

    return SizedBox(
      width: 40,
      height: 40,
      child: Center(child: leading),
    );
  }

  Widget _buildBadge(ThemeData theme) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: theme.colorScheme.primary,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        badge!,
        style: theme.textTheme.labelSmall?.copyWith(
          color: theme.colorScheme.onPrimary,
        ),
      ),
    );
  }
}
```

## Best Practices

1. **Composable** - Build complex widgets from simple ones
2. **Configurable** - Expose useful parameters
3. **Default values** - Provide sensible defaults
4. **Theme integration** - Use theme colors and typography
5. **Documentation** - Add dartdoc comments
6. **Static helpers** - Add static show() methods for dialogs
