---
name: flutter-project-structure
description: Flutter project structure best practices
applies_to: flutter
---

# Flutter Project Structure

## Overview

A well-organized Flutter project structure improves maintainability, scalability, and team collaboration.

## Recommended Structure

```
lib/
├── app/                           # App-level configuration
│   ├── app.dart                   # Main app widget
│   ├── router.dart                # Navigation configuration
│   ├── di.dart                    # Dependency injection setup
│   └── theme/
│       ├── app_theme.dart
│       ├── app_colors.dart
│       └── app_typography.dart
│
├── core/                          # Core utilities (shared across features)
│   ├── constants/
│   │   ├── api_constants.dart
│   │   ├── app_constants.dart
│   │   └── storage_keys.dart
│   ├── errors/
│   │   ├── exceptions.dart
│   │   └── failures.dart
│   ├── extensions/
│   │   ├── context_extensions.dart
│   │   ├── string_extensions.dart
│   │   └── date_extensions.dart
│   ├── network/
│   │   ├── api_client.dart
│   │   ├── interceptors/
│   │   └── network_info.dart
│   ├── storage/
│   │   ├── secure_storage.dart
│   │   └── local_storage.dart
│   ├── usecases/
│   │   └── usecase.dart
│   └── utils/
│       ├── logger.dart
│       ├── validators.dart
│       └── formatters.dart
│
├── features/                      # Feature modules
│   ├── auth/
│   │   ├── data/
│   │   │   ├── datasources/
│   │   │   ├── models/
│   │   │   └── repositories/
│   │   ├── domain/
│   │   │   ├── entities/
│   │   │   ├── repositories/
│   │   │   └── usecases/
│   │   └── presentation/
│   │       ├── bloc/
│   │       ├── pages/
│   │       └── widgets/
│   │
│   └── products/
│       ├── data/
│       ├── domain/
│       └── presentation/
│
├── shared/                        # Shared UI components
│   ├── widgets/
│   │   ├── buttons/
│   │   ├── inputs/
│   │   ├── cards/
│   │   └── dialogs/
│   └── layouts/
│       ├── scaffold_with_nav.dart
│       └── responsive_layout.dart
│
├── l10n/                          # Localization
│   ├── app_en.arb
│   └── app_ja.arb
│
└── main.dart                      # Entry point

test/
├── unit/
│   └── features/
├── widget/
│   └── features/
├── integration/
├── fixtures/
└── helpers/
```

## App Configuration

```dart
// lib/app/app.dart
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'router.dart';
import 'theme/app_theme.dart';
import 'di.dart';

class App extends StatelessWidget {
  const App({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiBlocProvider(
      providers: [
        BlocProvider(create: (_) => getIt<AuthBloc>()),
        BlocProvider(create: (_) => getIt<ThemeBloc>()),
      ],
      child: BlocBuilder<ThemeBloc, ThemeState>(
        builder: (context, state) {
          return MaterialApp.router(
            title: 'My App',
            theme: AppTheme.light,
            darkTheme: AppTheme.dark,
            themeMode: state.themeMode,
            routerConfig: router,
            debugShowCheckedModeBanner: false,
          );
        },
      ),
    );
  }
}
```

## Dependency Injection

```dart
// lib/app/di.dart
import 'package:get_it/get_it.dart';
import 'package:injectable/injectable.dart';
import 'di.config.dart';

final getIt = GetIt.instance;

@InjectableInit(preferRelativeImports: true)
void configureDependencies() => getIt.init();

// Run build_runner to generate di.config.dart
// flutter pub run build_runner build --delete-conflicting-outputs
```

## Entry Point

```dart
// lib/main.dart
import 'package:flutter/material.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'app/app.dart';
import 'app/di.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize Hive
  await Hive.initFlutter();

  // Initialize dependency injection
  configureDependencies();

  // Run app
  runApp(const App());
}
```

## Feature Module Structure

Each feature follows clean architecture:

```dart
// features/products/
├── data/                          # Data layer
│   ├── datasources/
│   │   ├── product_remote_datasource.dart
│   │   └── product_local_datasource.dart
│   ├── models/
│   │   └── product_model.dart     # JSON serialization
│   └── repositories/
│       └── product_repository_impl.dart
│
├── domain/                        # Domain layer (business logic)
│   ├── entities/
│   │   └── product.dart           # Pure business objects
│   ├── repositories/
│   │   └── product_repository.dart # Abstract interface
│   └── usecases/
│       ├── get_products.dart
│       ├── get_product.dart
│       ├── create_product.dart
│       └── delete_product.dart
│
└── presentation/                  # UI layer
    ├── bloc/
    │   ├── products_bloc.dart
    │   ├── products_event.dart
    │   └── products_state.dart
    ├── pages/
    │   ├── products_page.dart
    │   └── product_detail_page.dart
    └── widgets/
        ├── product_card.dart
        ├── product_list.dart
        └── product_form.dart
```

## Best Practices

1. **Feature-first organization** - Group by feature, not layer
2. **Barrel files** - Export related files from index.dart
3. **Consistent naming** - Use snake_case for files
4. **Layer separation** - Domain shouldn't import data/presentation
5. **Shared code** - Put truly reusable code in core/shared
