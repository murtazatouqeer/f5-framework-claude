---
name: flutter-form-builder
description: flutter_form_builder package for complex forms
applies_to: flutter
---

# Flutter Form Builder

## Overview

flutter_form_builder simplifies form creation with built-in field types, validation, and form state management. Great for complex forms with many field types.

## Dependencies

```yaml
dependencies:
  flutter_form_builder: ^9.2.1
  form_builder_validators: ^9.1.0
  # Additional field types
  form_builder_extra_fields: ^10.1.0
  form_builder_file_picker: ^4.1.0
  form_builder_image_picker: ^4.0.0
```

## Basic Form

```dart
import 'package:flutter_form_builder/flutter_form_builder.dart';
import 'package:form_builder_validators/form_builder_validators.dart';

class BasicForm extends StatefulWidget {
  @override
  State<BasicForm> createState() => _BasicFormState();
}

class _BasicFormState extends State<BasicForm> {
  final _formKey = GlobalKey<FormBuilderState>();

  void _onSubmit() {
    if (_formKey.currentState?.saveAndValidate() ?? false) {
      final values = _formKey.currentState!.value;
      print('Form values: $values');
      // Handle form submission
    }
  }

  @override
  Widget build(BuildContext context) {
    return FormBuilder(
      key: _formKey,
      autovalidateMode: AutovalidateMode.onUserInteraction,
      child: Column(
        children: [
          FormBuilderTextField(
            name: 'email',
            decoration: const InputDecoration(labelText: 'Email'),
            validator: FormBuilderValidators.compose([
              FormBuilderValidators.required(),
              FormBuilderValidators.email(),
            ]),
          ),
          FormBuilderTextField(
            name: 'password',
            decoration: const InputDecoration(labelText: 'Password'),
            obscureText: true,
            validator: FormBuilderValidators.compose([
              FormBuilderValidators.required(),
              FormBuilderValidators.minLength(8),
            ]),
          ),
          ElevatedButton(
            onPressed: _onSubmit,
            child: const Text('Submit'),
          ),
        ],
      ),
    );
  }
}
```

## Built-in Field Types

```dart
FormBuilder(
  key: _formKey,
  child: Column(
    children: [
      // Text Field
      FormBuilderTextField(
        name: 'name',
        decoration: const InputDecoration(labelText: 'Name'),
      ),

      // Dropdown
      FormBuilderDropdown<String>(
        name: 'gender',
        decoration: const InputDecoration(labelText: 'Gender'),
        items: ['Male', 'Female', 'Other']
            .map((gender) => DropdownMenuItem(
                  value: gender,
                  child: Text(gender),
                ))
            .toList(),
      ),

      // Radio Group
      FormBuilderRadioGroup<String>(
        name: 'priority',
        decoration: const InputDecoration(labelText: 'Priority'),
        options: ['Low', 'Medium', 'High']
            .map((priority) => FormBuilderFieldOption(
                  value: priority,
                  child: Text(priority),
                ))
            .toList(),
      ),

      // Checkbox Group
      FormBuilderCheckboxGroup<String>(
        name: 'interests',
        decoration: const InputDecoration(labelText: 'Interests'),
        options: ['Sports', 'Music', 'Reading', 'Gaming']
            .map((interest) => FormBuilderFieldOption(
                  value: interest,
                  child: Text(interest),
                ))
            .toList(),
      ),

      // Single Checkbox
      FormBuilderCheckbox(
        name: 'accept_terms',
        title: const Text('I accept the terms and conditions'),
        validator: FormBuilderValidators.required(
          errorText: 'You must accept the terms',
        ),
      ),

      // Switch
      FormBuilderSwitch(
        name: 'notifications',
        title: const Text('Enable notifications'),
        initialValue: true,
      ),

      // Slider
      FormBuilderSlider(
        name: 'age',
        decoration: const InputDecoration(labelText: 'Age'),
        min: 18,
        max: 100,
        initialValue: 25,
        divisions: 82,
        valueTransformer: (value) => value?.round(),
      ),

      // Range Slider
      FormBuilderRangeSlider(
        name: 'price_range',
        decoration: const InputDecoration(labelText: 'Price Range'),
        min: 0,
        max: 1000,
        initialValue: const RangeValues(100, 500),
      ),

      // Date Picker
      FormBuilderDateTimePicker(
        name: 'birth_date',
        decoration: const InputDecoration(labelText: 'Birth Date'),
        inputType: InputType.date,
        format: DateFormat('yyyy-MM-dd'),
        firstDate: DateTime(1900),
        lastDate: DateTime.now(),
      ),

      // Date Range Picker
      FormBuilderDateRangePicker(
        name: 'reservation_dates',
        decoration: const InputDecoration(labelText: 'Reservation Dates'),
        firstDate: DateTime.now(),
        lastDate: DateTime.now().add(const Duration(days: 365)),
      ),

      // Filter Chips
      FormBuilderFilterChip<String>(
        name: 'tags',
        decoration: const InputDecoration(labelText: 'Tags'),
        options: ['Flutter', 'Dart', 'Mobile', 'Web']
            .map((tag) => FormBuilderChipOption(
                  value: tag,
                  child: Text(tag),
                ))
            .toList(),
      ),

      // Choice Chips
      FormBuilderChoiceChip<String>(
        name: 'size',
        decoration: const InputDecoration(labelText: 'Size'),
        options: ['S', 'M', 'L', 'XL']
            .map((size) => FormBuilderChipOption(
                  value: size,
                  child: Text(size),
                ))
            .toList(),
      ),
    ],
  ),
)
```

## Validators

```dart
FormBuilderTextField(
  name: 'username',
  validator: FormBuilderValidators.compose([
    // Required
    FormBuilderValidators.required(errorText: 'Username is required'),

    // Min length
    FormBuilderValidators.minLength(3),

    // Max length
    FormBuilderValidators.maxLength(20),

    // Pattern matching
    FormBuilderValidators.match(
      r'^[a-zA-Z0-9_]+$',
      errorText: 'Only letters, numbers and underscore allowed',
    ),
  ]),
),

FormBuilderTextField(
  name: 'email',
  validator: FormBuilderValidators.compose([
    FormBuilderValidators.required(),
    FormBuilderValidators.email(),
  ]),
),

FormBuilderTextField(
  name: 'phone',
  validator: FormBuilderValidators.compose([
    FormBuilderValidators.required(),
    FormBuilderValidators.numeric(),
    FormBuilderValidators.minLength(10),
  ]),
),

FormBuilderTextField(
  name: 'age',
  validator: FormBuilderValidators.compose([
    FormBuilderValidators.required(),
    FormBuilderValidators.numeric(),
    FormBuilderValidators.min(18),
    FormBuilderValidators.max(120),
  ]),
),

FormBuilderTextField(
  name: 'url',
  validator: FormBuilderValidators.compose([
    FormBuilderValidators.url(),
  ]),
),

FormBuilderTextField(
  name: 'credit_card',
  validator: FormBuilderValidators.compose([
    FormBuilderValidators.creditCard(),
  ]),
),
```

## Custom Validators

```dart
// Custom validator function
String? passwordValidator(String? value) {
  if (value == null || value.isEmpty) {
    return 'Password is required';
  }
  if (value.length < 8) {
    return 'Password must be at least 8 characters';
  }
  if (!value.contains(RegExp(r'[A-Z]'))) {
    return 'Password must contain an uppercase letter';
  }
  if (!value.contains(RegExp(r'[0-9]'))) {
    return 'Password must contain a number';
  }
  return null;
}

// Confirm password validator
String? confirmPasswordValidator(
  String? value,
  GlobalKey<FormBuilderState> formKey,
) {
  if (value != formKey.currentState?.fields['password']?.value) {
    return 'Passwords do not match';
  }
  return null;
}

// Usage
FormBuilderTextField(
  name: 'password',
  validator: passwordValidator,
),
FormBuilderTextField(
  name: 'confirm_password',
  validator: (value) => confirmPasswordValidator(value, _formKey),
),
```

## Form with Initial Values

```dart
class EditProfileForm extends StatefulWidget {
  final User user;

  const EditProfileForm({required this.user});

  @override
  State<EditProfileForm> createState() => _EditProfileFormState();
}

class _EditProfileFormState extends State<EditProfileForm> {
  final _formKey = GlobalKey<FormBuilderState>();

  @override
  Widget build(BuildContext context) {
    return FormBuilder(
      key: _formKey,
      initialValue: {
        'name': widget.user.name,
        'email': widget.user.email,
        'bio': widget.user.bio,
        'birth_date': widget.user.birthDate,
        'notifications': widget.user.notificationsEnabled,
      },
      child: Column(
        children: [
          FormBuilderTextField(
            name: 'name',
            decoration: const InputDecoration(labelText: 'Name'),
          ),
          FormBuilderTextField(
            name: 'email',
            decoration: const InputDecoration(labelText: 'Email'),
          ),
          FormBuilderTextField(
            name: 'bio',
            decoration: const InputDecoration(labelText: 'Bio'),
            maxLines: 3,
          ),
          FormBuilderDateTimePicker(
            name: 'birth_date',
            decoration: const InputDecoration(labelText: 'Birth Date'),
            inputType: InputType.date,
          ),
          FormBuilderSwitch(
            name: 'notifications',
            title: const Text('Enable notifications'),
          ),
        ],
      ),
    );
  }
}
```

## Dynamic Fields

```dart
class DynamicForm extends StatefulWidget {
  @override
  State<DynamicForm> createState() => _DynamicFormState();
}

class _DynamicFormState extends State<DynamicForm> {
  final _formKey = GlobalKey<FormBuilderState>();
  List<int> _phoneFields = [0];
  int _nextFieldId = 1;

  void _addPhoneField() {
    setState(() {
      _phoneFields.add(_nextFieldId++);
    });
  }

  void _removePhoneField(int id) {
    setState(() {
      _phoneFields.remove(id);
    });
  }

  @override
  Widget build(BuildContext context) {
    return FormBuilder(
      key: _formKey,
      child: Column(
        children: [
          FormBuilderTextField(
            name: 'name',
            decoration: const InputDecoration(labelText: 'Name'),
          ),
          const SizedBox(height: 16),
          const Text('Phone Numbers'),
          ..._phoneFields.map((id) => Row(
                children: [
                  Expanded(
                    child: FormBuilderTextField(
                      name: 'phone_$id',
                      decoration: InputDecoration(
                        labelText: 'Phone ${_phoneFields.indexOf(id) + 1}',
                      ),
                      validator: FormBuilderValidators.compose([
                        FormBuilderValidators.required(),
                        FormBuilderValidators.numeric(),
                      ]),
                    ),
                  ),
                  if (_phoneFields.length > 1)
                    IconButton(
                      icon: const Icon(Icons.remove_circle),
                      onPressed: () => _removePhoneField(id),
                    ),
                ],
              )),
          TextButton.icon(
            onPressed: _addPhoneField,
            icon: const Icon(Icons.add),
            label: const Text('Add Phone'),
          ),
        ],
      ),
    );
  }
}
```

## Conditional Fields

```dart
class ConditionalForm extends StatefulWidget {
  @override
  State<ConditionalForm> createState() => _ConditionalFormState();
}

class _ConditionalFormState extends State<ConditionalForm> {
  final _formKey = GlobalKey<FormBuilderState>();
  bool _showCompanyFields = false;

  @override
  Widget build(BuildContext context) {
    return FormBuilder(
      key: _formKey,
      child: Column(
        children: [
          FormBuilderTextField(
            name: 'name',
            decoration: const InputDecoration(labelText: 'Name'),
          ),
          FormBuilderRadioGroup<String>(
            name: 'account_type',
            decoration: const InputDecoration(labelText: 'Account Type'),
            onChanged: (value) {
              setState(() {
                _showCompanyFields = value == 'Business';
              });
            },
            options: ['Personal', 'Business']
                .map((type) => FormBuilderFieldOption(
                      value: type,
                      child: Text(type),
                    ))
                .toList(),
          ),
          if (_showCompanyFields) ...[
            FormBuilderTextField(
              name: 'company_name',
              decoration: const InputDecoration(labelText: 'Company Name'),
              validator: FormBuilderValidators.required(),
            ),
            FormBuilderTextField(
              name: 'tax_id',
              decoration: const InputDecoration(labelText: 'Tax ID'),
              validator: FormBuilderValidators.required(),
            ),
          ],
        ],
      ),
    );
  }
}
```

## File and Image Pickers

```dart
// pubspec.yaml: form_builder_file_picker, form_builder_image_picker

FormBuilder(
  key: _formKey,
  child: Column(
    children: [
      // File picker
      FormBuilderFilePicker(
        name: 'documents',
        decoration: const InputDecoration(labelText: 'Documents'),
        maxFiles: 5,
        previewImages: false,
        allowMultiple: true,
        type: FileType.custom,
        allowedExtensions: ['pdf', 'doc', 'docx'],
        onChanged: (files) {
          // Handle file selection
        },
      ),

      // Image picker
      FormBuilderImagePicker(
        name: 'photos',
        decoration: const InputDecoration(labelText: 'Photos'),
        maxImages: 3,
        imageQuality: 80,
        availableImageSources: const [ImageSourceOption.gallery, ImageSourceOption.camera],
      ),
    ],
  ),
)
```

## Form with Steps (Stepper)

```dart
class StepperForm extends StatefulWidget {
  @override
  State<StepperForm> createState() => _StepperFormState();
}

class _StepperFormState extends State<StepperForm> {
  final _formKeys = [
    GlobalKey<FormBuilderState>(),
    GlobalKey<FormBuilderState>(),
    GlobalKey<FormBuilderState>(),
  ];
  int _currentStep = 0;

  bool _validateCurrentStep() {
    return _formKeys[_currentStep].currentState?.saveAndValidate() ?? false;
  }

  void _onStepContinue() {
    if (_validateCurrentStep()) {
      if (_currentStep < _formKeys.length - 1) {
        setState(() => _currentStep++);
      } else {
        _submitForm();
      }
    }
  }

  void _onStepCancel() {
    if (_currentStep > 0) {
      setState(() => _currentStep--);
    }
  }

  void _submitForm() {
    final allValues = <String, dynamic>{};
    for (final key in _formKeys) {
      allValues.addAll(key.currentState?.value ?? {});
    }
    print('All form values: $allValues');
  }

  @override
  Widget build(BuildContext context) {
    return Stepper(
      currentStep: _currentStep,
      onStepContinue: _onStepContinue,
      onStepCancel: _onStepCancel,
      steps: [
        Step(
          title: const Text('Personal Info'),
          content: FormBuilder(
            key: _formKeys[0],
            child: Column(
              children: [
                FormBuilderTextField(
                  name: 'first_name',
                  decoration: const InputDecoration(labelText: 'First Name'),
                  validator: FormBuilderValidators.required(),
                ),
                FormBuilderTextField(
                  name: 'last_name',
                  decoration: const InputDecoration(labelText: 'Last Name'),
                  validator: FormBuilderValidators.required(),
                ),
              ],
            ),
          ),
        ),
        Step(
          title: const Text('Contact Info'),
          content: FormBuilder(
            key: _formKeys[1],
            child: Column(
              children: [
                FormBuilderTextField(
                  name: 'email',
                  decoration: const InputDecoration(labelText: 'Email'),
                  validator: FormBuilderValidators.compose([
                    FormBuilderValidators.required(),
                    FormBuilderValidators.email(),
                  ]),
                ),
                FormBuilderTextField(
                  name: 'phone',
                  decoration: const InputDecoration(labelText: 'Phone'),
                  validator: FormBuilderValidators.required(),
                ),
              ],
            ),
          ),
        ),
        Step(
          title: const Text('Preferences'),
          content: FormBuilder(
            key: _formKeys[2],
            child: Column(
              children: [
                FormBuilderSwitch(
                  name: 'newsletter',
                  title: const Text('Subscribe to newsletter'),
                ),
                FormBuilderCheckbox(
                  name: 'terms',
                  title: const Text('Accept terms and conditions'),
                  validator: FormBuilderValidators.required(),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}
```

## Best Practices

1. **Use saveAndValidate()** - Saves and validates in one call
2. **Access values via .value** - `_formKey.currentState!.value['field_name']`
3. **Use valueTransformer** - Transform values before saving
4. **Compose validators** - Build complex validation rules
5. **Handle conditional fields** - Show/hide based on other field values
6. **Use initialValue** - For edit forms with existing data
