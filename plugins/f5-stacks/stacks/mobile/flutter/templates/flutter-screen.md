---
name: flutter-screen
description: Template for Flutter screen with BLoC
applies_to: flutter
variables:
  - name: screen_name
    description: Name of the screen (PascalCase)
  - name: feature_name
    description: Feature folder name (snake_case)
---

# Flutter Screen Template

## Screen with BLoC

```dart
// lib/features/{{feature_name}}/presentation/screens/{{feature_name}}_screen.dart

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../bloc/{{feature_name}}_bloc.dart';
import '../widgets/{{feature_name}}_content.dart';
import '../widgets/{{feature_name}}_error.dart';
import '../widgets/{{feature_name}}_loading.dart';

class {{screen_name}}Screen extends StatelessWidget {
  const {{screen_name}}Screen({super.key});

  static const routeName = '/{{feature_name}}';

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (context) => context.read<{{screen_name}}Bloc>()
        ..add(const {{screen_name}}Started()),
      child: const {{screen_name}}View(),
    );
  }
}

class {{screen_name}}View extends StatelessWidget {
  const {{screen_name}}View({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('{{screen_name}}'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              context.read<{{screen_name}}Bloc>().add(const {{screen_name}}Refreshed());
            },
          ),
        ],
      ),
      body: BlocBuilder<{{screen_name}}Bloc, {{screen_name}}State>(
        builder: (context, state) {
          return switch (state) {
            {{screen_name}}Initial() => const {{screen_name}}Loading(),
            {{screen_name}}Loading() => const {{screen_name}}Loading(),
            {{screen_name}}Success(:final data) => {{screen_name}}Content(data: data),
            {{screen_name}}Error(:final message) => {{screen_name}}Error(
                message: message,
                onRetry: () {
                  context.read<{{screen_name}}Bloc>().add(const {{screen_name}}Started());
                },
              ),
          };
        },
      ),
    );
  }
}
```

## Screen with Riverpod

```dart
// lib/features/{{feature_name}}/presentation/screens/{{feature_name}}_screen.dart

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../providers/{{feature_name}}_provider.dart';
import '../widgets/{{feature_name}}_content.dart';
import '../widgets/{{feature_name}}_error.dart';
import '../widgets/{{feature_name}}_loading.dart';

class {{screen_name}}Screen extends ConsumerWidget {
  const {{screen_name}}Screen({super.key});

  static const routeName = '/{{feature_name}}';

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch({{feature_name}}Provider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('{{screen_name}}'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              ref.invalidate({{feature_name}}Provider);
            },
          ),
        ],
      ),
      body: state.when(
        data: (data) => {{screen_name}}Content(data: data),
        loading: () => const {{screen_name}}Loading(),
        error: (error, stack) => {{screen_name}}Error(
          message: error.toString(),
          onRetry: () => ref.invalidate({{feature_name}}Provider),
        ),
      ),
    );
  }
}
```

## Screen with Form

```dart
// lib/features/{{feature_name}}/presentation/screens/{{feature_name}}_form_screen.dart

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../bloc/{{feature_name}}_form_bloc.dart';

class {{screen_name}}FormScreen extends StatelessWidget {
  const {{screen_name}}FormScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (context) => {{screen_name}}FormBloc(
        repository: context.read(),
      ),
      child: const {{screen_name}}FormView(),
    );
  }
}

class {{screen_name}}FormView extends StatefulWidget {
  const {{screen_name}}FormView({super.key});

  @override
  State<{{screen_name}}FormView> createState() => _{{screen_name}}FormViewState();
}

class _{{screen_name}}FormViewState extends State<{{screen_name}}FormView> {
  final _formKey = GlobalKey<FormState>();

  @override
  Widget build(BuildContext context) {
    return BlocConsumer<{{screen_name}}FormBloc, {{screen_name}}FormState>(
      listenWhen: (previous, current) => previous.status != current.status,
      listener: (context, state) {
        if (state.status == FormStatus.success) {
          Navigator.of(context).pop(true);
        } else if (state.status == FormStatus.failure) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(state.errorMessage ?? 'An error occurred')),
          );
        }
      },
      builder: (context, state) {
        return Scaffold(
          appBar: AppBar(
            title: const Text('{{screen_name}}'),
          ),
          body: Form(
            key: _formKey,
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                // Form fields here
                TextFormField(
                  decoration: const InputDecoration(
                    labelText: 'Name',
                    border: OutlineInputBorder(),
                  ),
                  onChanged: (value) {
                    context.read<{{screen_name}}FormBloc>().add(
                          NameChanged(value),
                        );
                  },
                  validator: (value) {
                    if (value == null || value.isEmpty) {
                      return 'Name is required';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 24),
                FilledButton(
                  onPressed: state.status == FormStatus.submitting
                      ? null
                      : () {
                          if (_formKey.currentState!.validate()) {
                            context.read<{{screen_name}}FormBloc>().add(
                                  const FormSubmitted(),
                                );
                          }
                        },
                  child: state.status == FormStatus.submitting
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Text('Submit'),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}
```

## Screen with Tabs

```dart
// lib/features/{{feature_name}}/presentation/screens/{{feature_name}}_tabs_screen.dart

import 'package:flutter/material.dart';

class {{screen_name}}TabsScreen extends StatelessWidget {
  const {{screen_name}}TabsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 3,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('{{screen_name}}'),
          bottom: const TabBar(
            tabs: [
              Tab(text: 'Tab 1', icon: Icon(Icons.home)),
              Tab(text: 'Tab 2', icon: Icon(Icons.search)),
              Tab(text: 'Tab 3', icon: Icon(Icons.settings)),
            ],
          ),
        ),
        body: const TabBarView(
          children: [
            Tab1Content(),
            Tab2Content(),
            Tab3Content(),
          ],
        ),
      ),
    );
  }
}
```

## Screen with Bottom Navigation

```dart
// lib/features/{{feature_name}}/presentation/screens/{{feature_name}}_nav_screen.dart

import 'package:flutter/material.dart';

class {{screen_name}}NavScreen extends StatefulWidget {
  const {{screen_name}}NavScreen({super.key});

  @override
  State<{{screen_name}}NavScreen> createState() => _{{screen_name}}NavScreenState();
}

class _{{screen_name}}NavScreenState extends State<{{screen_name}}NavScreen> {
  int _currentIndex = 0;

  final _pages = const [
    HomePage(),
    SearchPage(),
    ProfilePage(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: _pages,
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: (index) {
          setState(() => _currentIndex = index);
        },
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.home_outlined),
            selectedIcon: Icon(Icons.home),
            label: 'Home',
          ),
          NavigationDestination(
            icon: Icon(Icons.search_outlined),
            selectedIcon: Icon(Icons.search),
            label: 'Search',
          ),
          NavigationDestination(
            icon: Icon(Icons.person_outlined),
            selectedIcon: Icon(Icons.person),
            label: 'Profile',
          ),
        ],
      ),
    );
  }
}
```

## Usage

Replace `{{screen_name}}` with actual screen name (e.g., `Products`, `Users`)
Replace `{{feature_name}}` with feature folder name (e.g., `products`, `users`)
