---
name: flutter-form-validation
description: Form validation patterns in Flutter
applies_to: flutter
---

# Flutter Form Validation

## Overview

Flutter provides a Form widget with built-in validation support. Combine with FormField widgets and validators for comprehensive form handling.

## Basic Form Setup

```dart
class LoginForm extends StatefulWidget {
  const LoginForm({super.key});

  @override
  State<LoginForm> createState() => _LoginFormState();
}

class _LoginFormState extends State<LoginForm> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  void _submit() {
    if (_formKey.currentState!.validate()) {
      // Form is valid, process data
      final email = _emailController.text;
      final password = _passwordController.text;
      // Handle login
    }
  }

  @override
  Widget build(BuildContext context) {
    return Form(
      key: _formKey,
      child: Column(
        children: [
          TextFormField(
            controller: _emailController,
            decoration: const InputDecoration(labelText: 'Email'),
            keyboardType: TextInputType.emailAddress,
            validator: (value) {
              if (value == null || value.isEmpty) {
                return 'Email is required';
              }
              if (!value.contains('@')) {
                return 'Enter a valid email';
              }
              return null;
            },
          ),
          TextFormField(
            controller: _passwordController,
            decoration: const InputDecoration(labelText: 'Password'),
            obscureText: true,
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
          ElevatedButton(
            onPressed: _submit,
            child: const Text('Login'),
          ),
        ],
      ),
    );
  }
}
```

## Validator Functions

```dart
class Validators {
  static String? required(String? value, [String? fieldName]) {
    if (value == null || value.trim().isEmpty) {
      return '${fieldName ?? 'This field'} is required';
    }
    return null;
  }

  static String? email(String? value) {
    if (value == null || value.isEmpty) return null;

    final emailRegex = RegExp(r'^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$');
    if (!emailRegex.hasMatch(value)) {
      return 'Enter a valid email address';
    }
    return null;
  }

  static String? minLength(String? value, int min) {
    if (value == null || value.isEmpty) return null;

    if (value.length < min) {
      return 'Must be at least $min characters';
    }
    return null;
  }

  static String? maxLength(String? value, int max) {
    if (value == null || value.isEmpty) return null;

    if (value.length > max) {
      return 'Must be at most $max characters';
    }
    return null;
  }

  static String? phone(String? value) {
    if (value == null || value.isEmpty) return null;

    final phoneRegex = RegExp(r'^\+?[\d\s-]{10,}$');
    if (!phoneRegex.hasMatch(value)) {
      return 'Enter a valid phone number';
    }
    return null;
  }

  static String? password(String? value) {
    if (value == null || value.isEmpty) return null;

    if (value.length < 8) {
      return 'Password must be at least 8 characters';
    }
    if (!value.contains(RegExp(r'[A-Z]'))) {
      return 'Password must contain an uppercase letter';
    }
    if (!value.contains(RegExp(r'[a-z]'))) {
      return 'Password must contain a lowercase letter';
    }
    if (!value.contains(RegExp(r'[0-9]'))) {
      return 'Password must contain a number';
    }
    return null;
  }

  static String? confirmPassword(String? value, String password) {
    if (value == null || value.isEmpty) return null;

    if (value != password) {
      return 'Passwords do not match';
    }
    return null;
  }

  static String? url(String? value) {
    if (value == null || value.isEmpty) return null;

    final urlRegex = RegExp(
      r'^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$',
    );
    if (!urlRegex.hasMatch(value)) {
      return 'Enter a valid URL';
    }
    return null;
  }

  static String? numeric(String? value) {
    if (value == null || value.isEmpty) return null;

    if (double.tryParse(value) == null) {
      return 'Enter a valid number';
    }
    return null;
  }

  static String? range(String? value, {double? min, double? max}) {
    if (value == null || value.isEmpty) return null;

    final number = double.tryParse(value);
    if (number == null) {
      return 'Enter a valid number';
    }
    if (min != null && number < min) {
      return 'Must be at least $min';
    }
    if (max != null && number > max) {
      return 'Must be at most $max';
    }
    return null;
  }

  // Compose multiple validators
  static String? Function(String?) compose(
    List<String? Function(String?)> validators,
  ) {
    return (String? value) {
      for (final validator in validators) {
        final result = validator(value);
        if (result != null) return result;
      }
      return null;
    };
  }
}

// Usage
TextFormField(
  validator: Validators.compose([
    (v) => Validators.required(v, 'Email'),
    Validators.email,
  ]),
)
```

## AutovalidateMode

```dart
Form(
  key: _formKey,
  // Options:
  // - disabled: Only validate when validate() is called
  // - always: Validate on every change
  // - onUserInteraction: Validate after first interaction
  autovalidateMode: AutovalidateMode.onUserInteraction,
  child: Column(
    children: [
      TextFormField(
        validator: Validators.email,
        // Override form's autovalidateMode for individual field
        autovalidateMode: AutovalidateMode.disabled,
      ),
    ],
  ),
)
```

## Real-time Validation

```dart
class RealTimeValidationForm extends StatefulWidget {
  @override
  State<RealTimeValidationForm> createState() => _RealTimeValidationFormState();
}

class _RealTimeValidationFormState extends State<RealTimeValidationForm> {
  final _emailController = TextEditingController();
  String? _emailError;
  bool _isEmailValid = false;

  @override
  void initState() {
    super.initState();
    _emailController.addListener(_validateEmail);
  }

  void _validateEmail() {
    final value = _emailController.text;
    setState(() {
      if (value.isEmpty) {
        _emailError = null;
        _isEmailValid = false;
      } else if (!value.contains('@')) {
        _emailError = 'Enter a valid email';
        _isEmailValid = false;
      } else {
        _emailError = null;
        _isEmailValid = true;
      }
    });
  }

  @override
  void dispose() {
    _emailController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        TextField(
          controller: _emailController,
          decoration: InputDecoration(
            labelText: 'Email',
            errorText: _emailError,
            suffixIcon: _isEmailValid
                ? const Icon(Icons.check_circle, color: Colors.green)
                : null,
          ),
        ),
      ],
    );
  }
}
```

## Async Validation

```dart
class UsernameField extends StatefulWidget {
  final void Function(String) onUsernameChanged;

  const UsernameField({required this.onUsernameChanged});

  @override
  State<UsernameField> createState() => _UsernameFieldState();
}

class _UsernameFieldState extends State<UsernameField> {
  final _controller = TextEditingController();
  String? _error;
  bool _isChecking = false;
  Timer? _debounceTimer;

  @override
  void initState() {
    super.initState();
    _controller.addListener(_onChanged);
  }

  void _onChanged() {
    _debounceTimer?.cancel();
    _debounceTimer = Timer(const Duration(milliseconds: 500), () {
      _checkUsername(_controller.text);
    });
  }

  Future<void> _checkUsername(String username) async {
    if (username.isEmpty) {
      setState(() {
        _error = null;
        _isChecking = false;
      });
      return;
    }

    // Basic validation first
    if (username.length < 3) {
      setState(() {
        _error = 'Username must be at least 3 characters';
        _isChecking = false;
      });
      return;
    }

    setState(() => _isChecking = true);

    try {
      // Async check (e.g., API call)
      final isAvailable = await checkUsernameAvailability(username);
      setState(() {
        _error = isAvailable ? null : 'Username is already taken';
        _isChecking = false;
      });
      if (isAvailable) {
        widget.onUsernameChanged(username);
      }
    } catch (e) {
      setState(() {
        _error = 'Error checking username';
        _isChecking = false;
      });
    }
  }

  @override
  void dispose() {
    _debounceTimer?.cancel();
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return TextFormField(
      controller: _controller,
      decoration: InputDecoration(
        labelText: 'Username',
        errorText: _error,
        suffixIcon: _isChecking
            ? const SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(strokeWidth: 2),
              )
            : _error == null && _controller.text.isNotEmpty
                ? const Icon(Icons.check_circle, color: Colors.green)
                : null,
      ),
    );
  }
}
```

## Form State Management with BLoC

```dart
// Form state
@freezed
class RegistrationFormState with _$RegistrationFormState {
  const factory RegistrationFormState({
    @Default('') String email,
    @Default('') String password,
    @Default('') String confirmPassword,
    @Default(false) bool showErrors,
    @Default(false) bool isSubmitting,
    String? emailError,
    String? passwordError,
    String? confirmPasswordError,
    String? submitError,
  }) = _RegistrationFormState;

  const RegistrationFormState._();

  bool get isValid =>
      emailError == null &&
      passwordError == null &&
      confirmPasswordError == null &&
      email.isNotEmpty &&
      password.isNotEmpty &&
      confirmPassword.isNotEmpty;
}

// Form cubit
class RegistrationFormCubit extends Cubit<RegistrationFormState> {
  final AuthRepository _authRepository;

  RegistrationFormCubit(this._authRepository)
      : super(const RegistrationFormState());

  void emailChanged(String value) {
    emit(state.copyWith(
      email: value,
      emailError: _validateEmail(value),
    ));
  }

  void passwordChanged(String value) {
    emit(state.copyWith(
      password: value,
      passwordError: _validatePassword(value),
      confirmPasswordError: _validateConfirmPassword(state.confirmPassword, value),
    ));
  }

  void confirmPasswordChanged(String value) {
    emit(state.copyWith(
      confirmPassword: value,
      confirmPasswordError: _validateConfirmPassword(value, state.password),
    ));
  }

  String? _validateEmail(String value) {
    if (value.isEmpty) return 'Email is required';
    if (!value.contains('@')) return 'Enter a valid email';
    return null;
  }

  String? _validatePassword(String value) {
    if (value.isEmpty) return 'Password is required';
    if (value.length < 8) return 'Password must be at least 8 characters';
    return null;
  }

  String? _validateConfirmPassword(String value, String password) {
    if (value.isEmpty) return 'Confirm your password';
    if (value != password) return 'Passwords do not match';
    return null;
  }

  Future<bool> submit() async {
    emit(state.copyWith(showErrors: true));

    if (!state.isValid) return false;

    emit(state.copyWith(isSubmitting: true, submitError: null));

    try {
      await _authRepository.register(state.email, state.password);
      return true;
    } catch (e) {
      emit(state.copyWith(
        isSubmitting: false,
        submitError: e.toString(),
      ));
      return false;
    }
  }
}

// Form widget
class RegistrationFormWidget extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return BlocBuilder<RegistrationFormCubit, RegistrationFormState>(
      builder: (context, state) {
        return Column(
          children: [
            TextFormField(
              decoration: InputDecoration(
                labelText: 'Email',
                errorText: state.showErrors ? state.emailError : null,
              ),
              onChanged: context.read<RegistrationFormCubit>().emailChanged,
            ),
            TextFormField(
              decoration: InputDecoration(
                labelText: 'Password',
                errorText: state.showErrors ? state.passwordError : null,
              ),
              obscureText: true,
              onChanged: context.read<RegistrationFormCubit>().passwordChanged,
            ),
            TextFormField(
              decoration: InputDecoration(
                labelText: 'Confirm Password',
                errorText: state.showErrors ? state.confirmPasswordError : null,
              ),
              obscureText: true,
              onChanged:
                  context.read<RegistrationFormCubit>().confirmPasswordChanged,
            ),
            if (state.submitError != null)
              Text(
                state.submitError!,
                style: const TextStyle(color: Colors.red),
              ),
            ElevatedButton(
              onPressed: state.isSubmitting
                  ? null
                  : () => context.read<RegistrationFormCubit>().submit(),
              child: state.isSubmitting
                  ? const CircularProgressIndicator()
                  : const Text('Register'),
            ),
          ],
        );
      },
    );
  }
}
```

## Custom FormField

```dart
class RatingFormField extends FormField<int> {
  RatingFormField({
    super.key,
    super.initialValue,
    super.validator,
    super.onSaved,
    super.autovalidateMode,
    int maxRating = 5,
  }) : super(
          builder: (FormFieldState<int> state) {
            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: List.generate(maxRating, (index) {
                    final rating = index + 1;
                    return IconButton(
                      icon: Icon(
                        rating <= (state.value ?? 0)
                            ? Icons.star
                            : Icons.star_border,
                        color: rating <= (state.value ?? 0)
                            ? Colors.amber
                            : Colors.grey,
                      ),
                      onPressed: () {
                        state.didChange(rating);
                      },
                    );
                  }),
                ),
                if (state.hasError)
                  Text(
                    state.errorText!,
                    style: const TextStyle(color: Colors.red, fontSize: 12),
                  ),
              ],
            );
          },
        );
}

// Usage
RatingFormField(
  initialValue: 0,
  validator: (value) {
    if (value == null || value == 0) {
      return 'Please select a rating';
    }
    return null;
  },
  onSaved: (value) {
    // Save the rating
  },
)
```

## Best Practices

1. **Use GlobalKey<FormState>** - Access form state for validation
2. **Dispose controllers** - Prevent memory leaks
3. **Use AutovalidateMode** - Choose appropriate validation timing
4. **Debounce async validation** - Avoid excessive API calls
5. **Compose validators** - Build complex validation from simple functions
6. **Show errors appropriately** - Consider when to display errors
