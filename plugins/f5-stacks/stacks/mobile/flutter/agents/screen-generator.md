---
name: flutter-screen-generator
description: Generates Flutter screens/pages with BLoC pattern
applies_to: flutter
---

# Flutter Screen Generator Agent

## Purpose

Generates complete Flutter screen implementations following clean architecture with BLoC state management.

## Capabilities

- Generate screen pages with BLoC integration
- Create corresponding BLoC/Cubit files
- Generate screen-specific widgets
- Add proper navigation setup
- Include loading, error, and empty states

## Input Requirements

| Field | Required | Description |
|-------|----------|-------------|
| `feature_name` | Yes | Feature/module name |
| `screen_name` | Yes | Screen name |
| `has_list` | No | Whether screen displays a list |
| `has_form` | No | Whether screen has form input |
| `has_detail` | No | Whether it's a detail screen |

## Generated Files

```
features/{feature}/presentation/
├── bloc/
│   ├── {screen}_bloc.dart
│   ├── {screen}_event.dart
│   └── {screen}_state.dart
├── pages/
│   └── {screen}_page.dart
└── widgets/
    ├── {screen}_list.dart (if has_list)
    ├── {screen}_form.dart (if has_form)
    └── {screen}_empty.dart
```

## Example Usage

```yaml
feature_name: products
screen_name: products
has_list: true
has_form: false
```

## Output Pattern

### Page Structure

```dart
class ProductsPage extends StatelessWidget {
  const ProductsPage({super.key});

  static const routeName = '/products';

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => getIt<ProductsBloc>()
        ..add(const ProductsEvent.load()),
      child: const ProductsView(),
    );
  }
}

class ProductsView extends StatelessWidget {
  const ProductsView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Products')),
      body: BlocConsumer<ProductsBloc, ProductsState>(
        listener: _handleStateChanges,
        builder: _buildContent,
      ),
    );
  }
}
```

## Best Practices

1. **Separation of concerns** - Page creates BLoC, View consumes it
2. **Named routes** - Use static routeName constant
3. **Dependency injection** - Use getIt for BLoC creation
4. **State handling** - Always handle loading, error, empty states
5. **Pull to refresh** - Include RefreshIndicator for list screens
6. **Infinite scroll** - Add pagination for large lists
