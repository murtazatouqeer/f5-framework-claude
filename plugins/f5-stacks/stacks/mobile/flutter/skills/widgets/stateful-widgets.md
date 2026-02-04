---
name: flutter-stateful-widgets
description: Building StatefulWidget in Flutter
applies_to: flutter
---

# Flutter StatefulWidget

## Overview

StatefulWidget holds mutable state that can change during the widget's lifetime. Use when the widget needs to respond to user interaction or data changes.

## Basic StatefulWidget

```dart
import 'package:flutter/material.dart';

class Counter extends StatefulWidget {
  const Counter({
    super.key,
    this.initialValue = 0,
    this.onChanged,
  });

  final int initialValue;
  final void Function(int)? onChanged;

  @override
  State<Counter> createState() => _CounterState();
}

class _CounterState extends State<Counter> {
  late int _count;

  @override
  void initState() {
    super.initState();
    _count = widget.initialValue;
  }

  void _increment() {
    setState(() {
      _count++;
    });
    widget.onChanged?.call(_count);
  }

  void _decrement() {
    setState(() {
      _count--;
    });
    widget.onChanged?.call(_count);
  }

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        IconButton(
          onPressed: _decrement,
          icon: const Icon(Icons.remove),
        ),
        Text(
          '$_count',
          style: Theme.of(context).textTheme.headlineMedium,
        ),
        IconButton(
          onPressed: _increment,
          icon: const Icon(Icons.add),
        ),
      ],
    );
  }
}
```

## With Animations

```dart
class AnimatedFavoriteButton extends StatefulWidget {
  const AnimatedFavoriteButton({
    super.key,
    required this.isFavorite,
    required this.onToggle,
  });

  final bool isFavorite;
  final void Function(bool) onToggle;

  @override
  State<AnimatedFavoriteButton> createState() => _AnimatedFavoriteButtonState();
}

class _AnimatedFavoriteButtonState extends State<AnimatedFavoriteButton>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  late final Animation<double> _scaleAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 200),
      vsync: this,
    );
    _scaleAnimation = Tween<double>(begin: 1.0, end: 1.3).animate(
      CurvedAnimation(parent: _controller, curve: Curves.elasticOut),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _handleTap() {
    _controller.forward().then((_) => _controller.reverse());
    widget.onToggle(!widget.isFavorite);
  }

  @override
  Widget build(BuildContext context) {
    return ScaleTransition(
      scale: _scaleAnimation,
      child: IconButton(
        onPressed: _handleTap,
        icon: Icon(
          widget.isFavorite ? Icons.favorite : Icons.favorite_border,
          color: widget.isFavorite ? Colors.red : null,
        ),
      ),
    );
  }
}
```

## With TextEditingController

```dart
class SearchField extends StatefulWidget {
  const SearchField({
    super.key,
    this.initialValue,
    this.onSearch,
    this.debounceMs = 300,
  });

  final String? initialValue;
  final void Function(String)? onSearch;
  final int debounceMs;

  @override
  State<SearchField> createState() => _SearchFieldState();
}

class _SearchFieldState extends State<SearchField> {
  late final TextEditingController _controller;
  Timer? _debounceTimer;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController(text: widget.initialValue);
    _controller.addListener(_onTextChanged);
  }

  @override
  void dispose() {
    _debounceTimer?.cancel();
    _controller.dispose();
    super.dispose();
  }

  void _onTextChanged() {
    _debounceTimer?.cancel();
    _debounceTimer = Timer(
      Duration(milliseconds: widget.debounceMs),
      () => widget.onSearch?.call(_controller.text),
    );
  }

  void _clearSearch() {
    _controller.clear();
    widget.onSearch?.call('');
  }

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: _controller,
      decoration: InputDecoration(
        hintText: 'Search...',
        prefixIcon: const Icon(Icons.search),
        suffixIcon: ValueListenableBuilder<TextEditingValue>(
          valueListenable: _controller,
          builder: (_, value, __) {
            if (value.text.isEmpty) return const SizedBox.shrink();
            return IconButton(
              onPressed: _clearSearch,
              icon: const Icon(Icons.clear),
            );
          },
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
        ),
      ),
    );
  }
}
```

## With Form State

```dart
class LoginForm extends StatefulWidget {
  const LoginForm({
    super.key,
    required this.onSubmit,
  });

  final Future<void> Function(String email, String password) onSubmit;

  @override
  State<LoginForm> createState() => _LoginFormState();
}

class _LoginFormState extends State<LoginForm> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();

  bool _isSubmitting = false;
  bool _obscurePassword = true;
  String? _errorMessage;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _handleSubmit() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _isSubmitting = true;
      _errorMessage = null;
    });

    try {
      await widget.onSubmit(
        _emailController.text,
        _passwordController.text,
      );
    } catch (e) {
      setState(() {
        _errorMessage = e.toString();
      });
    } finally {
      if (mounted) {
        setState(() {
          _isSubmitting = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Form(
      key: _formKey,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          if (_errorMessage != null)
            Container(
              padding: const EdgeInsets.all(12),
              margin: const EdgeInsets.only(bottom: 16),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.errorContainer,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                _errorMessage!,
                style: TextStyle(
                  color: Theme.of(context).colorScheme.error,
                ),
              ),
            ),
          TextFormField(
            controller: _emailController,
            keyboardType: TextInputType.emailAddress,
            textInputAction: TextInputAction.next,
            decoration: const InputDecoration(
              labelText: 'Email',
              prefixIcon: Icon(Icons.email),
            ),
            validator: (value) {
              if (value == null || value.isEmpty) {
                return 'Email is required';
              }
              if (!value.contains('@')) {
                return 'Invalid email address';
              }
              return null;
            },
          ),
          const SizedBox(height: 16),
          TextFormField(
            controller: _passwordController,
            obscureText: _obscurePassword,
            textInputAction: TextInputAction.done,
            onFieldSubmitted: (_) => _handleSubmit(),
            decoration: InputDecoration(
              labelText: 'Password',
              prefixIcon: const Icon(Icons.lock),
              suffixIcon: IconButton(
                onPressed: () {
                  setState(() {
                    _obscurePassword = !_obscurePassword;
                  });
                },
                icon: Icon(
                  _obscurePassword ? Icons.visibility : Icons.visibility_off,
                ),
              ),
            ),
            validator: (value) {
              if (value == null || value.isEmpty) {
                return 'Password is required';
              }
              if (value.length < 8) {
                return 'Password must be at least 8 characters';
              }
              return null;
            },
          ),
          const SizedBox(height: 24),
          FilledButton(
            onPressed: _isSubmitting ? null : _handleSubmit,
            child: _isSubmitting
                ? const SizedBox(
                    height: 20,
                    width: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Text('Sign In'),
          ),
        ],
      ),
    );
  }
}
```

## didUpdateWidget Example

```dart
class TimerDisplay extends StatefulWidget {
  const TimerDisplay({
    super.key,
    required this.seconds,
    this.onComplete,
  });

  final int seconds;
  final VoidCallback? onComplete;

  @override
  State<TimerDisplay> createState() => _TimerDisplayState();
}

class _TimerDisplayState extends State<TimerDisplay> {
  late int _remainingSeconds;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _remainingSeconds = widget.seconds;
    _startTimer();
  }

  @override
  void didUpdateWidget(TimerDisplay oldWidget) {
    super.didUpdateWidget(oldWidget);
    // Reset timer if seconds changed
    if (widget.seconds != oldWidget.seconds) {
      _timer?.cancel();
      _remainingSeconds = widget.seconds;
      _startTimer();
    }
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  void _startTimer() {
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (_remainingSeconds > 0) {
        setState(() {
          _remainingSeconds--;
        });
      } else {
        timer.cancel();
        widget.onComplete?.call();
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Text(
      '${_remainingSeconds}s',
      style: Theme.of(context).textTheme.headlineLarge,
    );
  }
}
```

## Best Practices

1. **Minimal state** - Only store what's necessary in state
2. **initState** - Initialize controllers and subscriptions
3. **dispose** - Clean up controllers, subscriptions, timers
4. **mounted check** - Check `mounted` before setState in async callbacks
5. **didUpdateWidget** - React to widget property changes
6. **Private state class** - Prefix with underscore
7. **Late initialization** - Use `late` for non-nullable fields initialized in initState
