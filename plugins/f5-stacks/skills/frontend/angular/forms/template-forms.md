# Angular Template-Driven Forms

## Overview

Template-driven forms use directives to create and manipulate the form model in the template. They are simpler for basic forms but offer less control than reactive forms.

## Setup

```typescript
// Import FormsModule in standalone component
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-simple-form',
  standalone: true,
  imports: [FormsModule],
  template: `...`,
})
export class SimpleFormComponent {}
```

## Basic Form

```typescript
@Component({
  selector: 'app-contact-form',
  standalone: true,
  imports: [FormsModule],
  template: `
    <form #contactForm="ngForm" (ngSubmit)="onSubmit(contactForm)">
      <div class="field">
        <label for="name">Name</label>
        <input
          id="name"
          name="name"
          [(ngModel)]="model.name"
          required
          minlength="2"
          #name="ngModel"
        >
        @if (name.invalid && name.touched) {
          <div class="errors">
            @if (name.errors?.['required']) {
              <span>Name is required</span>
            }
            @if (name.errors?.['minlength']) {
              <span>Name must be at least 2 characters</span>
            }
          </div>
        }
      </div>

      <div class="field">
        <label for="email">Email</label>
        <input
          id="email"
          name="email"
          type="email"
          [(ngModel)]="model.email"
          required
          email
          #email="ngModel"
        >
        @if (email.invalid && email.touched) {
          <div class="errors">
            @if (email.errors?.['required']) {
              <span>Email is required</span>
            }
            @if (email.errors?.['email']) {
              <span>Invalid email format</span>
            }
          </div>
        }
      </div>

      <div class="field">
        <label for="message">Message</label>
        <textarea
          id="message"
          name="message"
          [(ngModel)]="model.message"
          required
          #message="ngModel"
        ></textarea>
        @if (message.invalid && message.touched) {
          <span class="error">Message is required</span>
        }
      </div>

      <button type="submit" [disabled]="contactForm.invalid">
        Send Message
      </button>
    </form>
  `,
})
export class ContactFormComponent {
  model = {
    name: '',
    email: '',
    message: '',
  };

  onSubmit(form: NgForm) {
    if (form.valid) {
      console.log('Form submitted:', this.model);
      form.resetForm();
    }
  }
}
```

## Two-Way Binding with ngModel

```typescript
@Component({
  selector: 'app-user-profile',
  standalone: true,
  imports: [FormsModule],
  template: `
    <form>
      <!-- Basic binding -->
      <input [(ngModel)]="user.firstName" name="firstName">

      <!-- Separate property and event binding -->
      <input
        [ngModel]="user.lastName"
        (ngModelChange)="onLastNameChange($event)"
        name="lastName"
      >

      <!-- With options -->
      <input
        [(ngModel)]="user.email"
        name="email"
        [ngModelOptions]="{ updateOn: 'blur' }"
      >

      <!-- Display bound values -->
      <p>Full name: {{ user.firstName }} {{ user.lastName }}</p>
    </form>
  `,
})
export class UserProfileComponent {
  user = {
    firstName: '',
    lastName: '',
    email: '',
  };

  onLastNameChange(value: string) {
    console.log('Last name changed:', value);
    this.user.lastName = value.toUpperCase();
  }
}
```

## Form Controls

### Text Input

```html
<input
  type="text"
  name="username"
  [(ngModel)]="username"
  required
  minlength="3"
  maxlength="20"
  pattern="[a-zA-Z0-9]+"
  #usernameRef="ngModel"
>
```

### Checkbox

```html
<label>
  <input
    type="checkbox"
    name="acceptTerms"
    [(ngModel)]="acceptTerms"
    required
  >
  I accept the terms and conditions
</label>
```

### Radio Buttons

```html
<div>
  <label>
    <input type="radio" name="gender" [(ngModel)]="gender" value="male">
    Male
  </label>
  <label>
    <input type="radio" name="gender" [(ngModel)]="gender" value="female">
    Female
  </label>
  <label>
    <input type="radio" name="gender" [(ngModel)]="gender" value="other">
    Other
  </label>
</div>
```

### Select Dropdown

```typescript
@Component({
  template: `
    <!-- Basic select -->
    <select name="country" [(ngModel)]="selectedCountry" required>
      <option value="">Select a country</option>
      @for (country of countries; track country.code) {
        <option [value]="country.code">{{ country.name }}</option>
      }
    </select>

    <!-- Object binding with compareWith -->
    <select
      name="selectedUser"
      [(ngModel)]="selectedUser"
      [compareWith]="compareUsers"
    >
      @for (user of users; track user.id) {
        <option [ngValue]="user">{{ user.name }}</option>
      }
    </select>

    <!-- Multiple select -->
    <select name="skills" [(ngModel)]="selectedSkills" multiple>
      @for (skill of skills; track skill) {
        <option [value]="skill">{{ skill }}</option>
      }
    </select>
  `,
})
export class SelectFormComponent {
  countries = [
    { code: 'US', name: 'United States' },
    { code: 'UK', name: 'United Kingdom' },
    { code: 'JP', name: 'Japan' },
  ];
  selectedCountry = '';

  users = [
    { id: 1, name: 'Alice' },
    { id: 2, name: 'Bob' },
  ];
  selectedUser: User | null = null;

  skills = ['JavaScript', 'TypeScript', 'Angular', 'React'];
  selectedSkills: string[] = [];

  compareUsers(u1: User, u2: User): boolean {
    return u1?.id === u2?.id;
  }
}
```

### Textarea

```html
<textarea
  name="description"
  [(ngModel)]="description"
  required
  minlength="10"
  maxlength="500"
  rows="5"
  #desc="ngModel"
></textarea>
<small>{{ description.length }}/500 characters</small>
```

## Grouping Controls with ngModelGroup

```typescript
@Component({
  template: `
    <form #profileForm="ngForm" (ngSubmit)="onSubmit(profileForm)">
      <!-- Personal info group -->
      <fieldset ngModelGroup="personal" #personal="ngModelGroup">
        <legend>Personal Information</legend>

        <input name="firstName" [(ngModel)]="model.personal.firstName" required>
        <input name="lastName" [(ngModel)]="model.personal.lastName" required>

        @if (personal.invalid && personal.touched) {
          <span class="error">Please complete personal information</span>
        }
      </fieldset>

      <!-- Address group -->
      <fieldset ngModelGroup="address" #address="ngModelGroup">
        <legend>Address</legend>

        <input name="street" [(ngModel)]="model.address.street" required>
        <input name="city" [(ngModel)]="model.address.city" required>
        <input name="zipCode" [(ngModel)]="model.address.zipCode" required>
      </fieldset>

      <button type="submit" [disabled]="profileForm.invalid">Save</button>
    </form>
  `,
})
export class ProfileFormComponent {
  model = {
    personal: {
      firstName: '',
      lastName: '',
    },
    address: {
      street: '',
      city: '',
      zipCode: '',
    },
  };

  onSubmit(form: NgForm) {
    if (form.valid) {
      console.log('Model:', this.model);
      console.log('Form value:', form.value);
    }
  }
}
```

## Form State Classes

Angular automatically adds CSS classes based on control state:

```css
/* Untouched/Touched */
.ng-untouched { }
.ng-touched { }

/* Pristine/Dirty */
.ng-pristine { }
.ng-dirty { }

/* Valid/Invalid */
.ng-valid { }
.ng-invalid { }

/* Pending (async validation) */
.ng-pending { }

/* Example styling */
input.ng-invalid.ng-touched {
  border-color: red;
}

input.ng-valid.ng-touched {
  border-color: green;
}
```

## Accessing Form State

```typescript
@Component({
  template: `
    <form #myForm="ngForm">
      <input name="email" [(ngModel)]="email" required #emailRef="ngModel">

      <!-- Control state -->
      <p>Valid: {{ emailRef.valid }}</p>
      <p>Invalid: {{ emailRef.invalid }}</p>
      <p>Touched: {{ emailRef.touched }}</p>
      <p>Dirty: {{ emailRef.dirty }}</p>
      <p>Errors: {{ emailRef.errors | json }}</p>

      <!-- Form state -->
      <p>Form valid: {{ myForm.valid }}</p>
      <p>Form value: {{ myForm.value | json }}</p>
    </form>
  `,
})
export class FormStateComponent {
  email = '';
}
```

## Programmatic Form Control

```typescript
@Component({
  template: `
    <form #myForm="ngForm">
      <input name="username" [(ngModel)]="username" required>
      <input name="password" [(ngModel)]="password" required>

      <button type="button" (click)="resetForm()">Reset</button>
      <button type="button" (click)="setValues()">Set Default</button>
    </form>
  `,
})
export class FormControlComponent {
  @ViewChild('myForm') form!: NgForm;

  username = '';
  password = '';

  resetForm() {
    this.form.resetForm();
  }

  setValues() {
    // Using setValue (requires all fields)
    this.form.setValue({
      username: 'defaultUser',
      password: 'defaultPass',
    });

    // Or update model directly
    this.username = 'defaultUser';
    this.password = 'defaultPass';
  }

  markAllTouched() {
    Object.values(this.form.controls).forEach(control => {
      control.markAsTouched();
    });
  }
}
```

## Update Strategies

```html
<!-- Update on every change (default) -->
<input [(ngModel)]="value" name="default">

<!-- Update on blur -->
<input
  [(ngModel)]="value"
  name="onBlur"
  [ngModelOptions]="{ updateOn: 'blur' }"
>

<!-- Update on submit -->
<input
  [(ngModel)]="value"
  name="onSubmit"
  [ngModelOptions]="{ updateOn: 'submit' }"
>

<!-- Standalone control (not part of form) -->
<input
  [(ngModel)]="value"
  [ngModelOptions]="{ standalone: true }"
>
```

## Form with Signals

```typescript
@Component({
  selector: 'app-signal-form',
  standalone: true,
  imports: [FormsModule],
  template: `
    <form #form="ngForm" (ngSubmit)="onSubmit()">
      <input
        name="name"
        [ngModel]="name()"
        (ngModelChange)="name.set($event)"
        required
      >

      <input
        name="email"
        [ngModel]="email()"
        (ngModelChange)="email.set($event)"
        required
        email
      >

      <p>Full data: {{ formData() | json }}</p>

      <button [disabled]="form.invalid">Submit</button>
    </form>
  `,
})
export class SignalFormComponent {
  name = signal('');
  email = signal('');

  // Computed value combining form data
  formData = computed(() => ({
    name: this.name(),
    email: this.email(),
  }));

  onSubmit() {
    console.log('Submitted:', this.formData());
  }
}
```

## Dynamic Form Fields

```typescript
@Component({
  template: `
    <form #dynamicForm="ngForm" (ngSubmit)="onSubmit(dynamicForm)">
      @for (field of fields; track field.name) {
        <div class="field">
          <label>{{ field.label }}</label>

          @switch (field.type) {
            @case ('text') {
              <input
                [type]="field.type"
                [name]="field.name"
                [(ngModel)]="formData[field.name]"
                [required]="field.required"
              >
            }
            @case ('select') {
              <select
                [name]="field.name"
                [(ngModel)]="formData[field.name]"
                [required]="field.required"
              >
                @for (option of field.options; track option.value) {
                  <option [value]="option.value">{{ option.label }}</option>
                }
              </select>
            }
            @case ('checkbox') {
              <input
                type="checkbox"
                [name]="field.name"
                [(ngModel)]="formData[field.name]"
              >
            }
          }
        </div>
      }

      <button type="submit" [disabled]="dynamicForm.invalid">Submit</button>
    </form>
  `,
})
export class DynamicFormComponent {
  fields = [
    { name: 'firstName', label: 'First Name', type: 'text', required: true },
    { name: 'lastName', label: 'Last Name', type: 'text', required: true },
    {
      name: 'country',
      label: 'Country',
      type: 'select',
      required: true,
      options: [
        { value: 'us', label: 'United States' },
        { value: 'uk', label: 'United Kingdom' },
      ],
    },
    { name: 'newsletter', label: 'Subscribe', type: 'checkbox', required: false },
  ];

  formData: Record<string, any> = {};

  onSubmit(form: NgForm) {
    if (form.valid) {
      console.log('Form data:', this.formData);
    }
  }
}
```

## When to Use Template-Driven Forms

**Use Template-Driven Forms when:**
- Simple forms with basic validation
- Quick prototyping
- Forms with static structure
- Team prefers template-based approach

**Use Reactive Forms when:**
- Complex validation logic
- Dynamic form fields
- Need to test form logic
- Forms with complex data transformations

## Best Practices

1. **Use unique names**: Every ngModel needs a unique name attribute
2. **Export references**: Use #ref="ngModel" to access control state
3. **Group related fields**: Use ngModelGroup for organization
4. **Handle async**: Consider updateOn option for performance
5. **Reset properly**: Use form.resetForm() to reset state and values
6. **Style validation states**: Use Angular's CSS classes for feedback
7. **Consider Reactive Forms**: For complex scenarios
