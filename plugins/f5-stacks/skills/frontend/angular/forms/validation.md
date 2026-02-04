# Angular Form Validation

## Overview

Angular provides built-in validators and supports custom synchronous and asynchronous validation for both reactive and template-driven forms.

## Built-in Validators

### Reactive Forms

```typescript
import { Component, inject } from '@angular/core';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';

@Component({
  selector: 'app-validation-demo',
  standalone: true,
  imports: [ReactiveFormsModule],
  template: `
    <form [formGroup]="form" (ngSubmit)="onSubmit()">
      <input formControlName="username" placeholder="Username">
      <input formControlName="email" type="email" placeholder="Email">
      <input formControlName="age" type="number" placeholder="Age">
      <input formControlName="website" placeholder="Website URL">

      <button type="submit" [disabled]="form.invalid">Submit</button>
    </form>
  `,
})
export class ValidationDemoComponent {
  private fb = inject(FormBuilder);

  form = this.fb.group({
    // Required field
    username: ['', [Validators.required]],

    // Multiple validators
    email: ['', [Validators.required, Validators.email]],

    // Numeric validators
    age: [null, [Validators.required, Validators.min(0), Validators.max(120)]],

    // Length validators
    bio: ['', [Validators.minLength(10), Validators.maxLength(500)]],

    // Pattern validator
    phone: ['', [Validators.pattern(/^\+?[\d\s-]{10,}$/)]],

    // URL pattern
    website: ['', [Validators.pattern(/^https?:\/\/.+/)]],

    // Required true (for checkboxes)
    acceptTerms: [false, [Validators.requiredTrue]],
  });
}
```

### Template-Driven Forms

```html
<!-- Required -->
<input name="username" [(ngModel)]="username" required>

<!-- Email -->
<input name="email" [(ngModel)]="email" required email>

<!-- Min/Max length -->
<input name="bio" [(ngModel)]="bio" minlength="10" maxlength="500">

<!-- Min/Max (numbers) -->
<input type="number" name="age" [(ngModel)]="age" min="0" max="120">

<!-- Pattern -->
<input name="phone" [(ngModel)]="phone" pattern="^\+?[\d\s-]{10,}$">
```

## Displaying Validation Errors

### Reactive Forms Error Display

```typescript
@Component({
  template: `
    <form [formGroup]="form">
      <div class="field">
        <label>Email</label>
        <input formControlName="email" type="email">

        @if (form.controls.email.invalid && form.controls.email.touched) {
          <div class="errors">
            @if (form.controls.email.errors?.['required']) {
              <span>Email is required</span>
            }
            @if (form.controls.email.errors?.['email']) {
              <span>Please enter a valid email</span>
            }
          </div>
        }
      </div>

      <div class="field">
        <label>Password</label>
        <input formControlName="password" type="password">

        @if (form.controls.password.invalid && form.controls.password.touched) {
          <div class="errors">
            @if (form.controls.password.errors?.['required']) {
              <span>Password is required</span>
            }
            @if (form.controls.password.errors?.['minlength']; as error) {
              <span>
                Password must be at least {{ error.requiredLength }} characters
                (currently {{ error.actualLength }})
              </span>
            }
          </div>
        }
      </div>
    </form>
  `,
})
export class ErrorDisplayComponent {
  private fb = inject(FormBuilder);

  form = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(8)]],
  });
}
```

### Reusable Error Component

```typescript
// shared/components/validation-errors.component.ts
@Component({
  selector: 'app-validation-errors',
  standalone: true,
  template: `
    @if (control()?.invalid && control()?.touched) {
      <div class="validation-errors">
        @for (error of errors(); track error.key) {
          <span class="error">{{ error.message }}</span>
        }
      </div>
    }
  `,
  styles: `
    .validation-errors {
      color: #dc3545;
      font-size: 0.875rem;
      margin-top: 0.25rem;
    }
  `,
})
export class ValidationErrorsComponent {
  control = input<AbstractControl | null>(null);

  private errorMessages: Record<string, (params: any) => string> = {
    required: () => 'This field is required',
    email: () => 'Please enter a valid email address',
    minlength: (p) => `Minimum ${p.requiredLength} characters required`,
    maxlength: (p) => `Maximum ${p.requiredLength} characters allowed`,
    min: (p) => `Value must be at least ${p.min}`,
    max: (p) => `Value must not exceed ${p.max}`,
    pattern: () => 'Invalid format',
  };

  errors = computed(() => {
    const ctrl = this.control();
    if (!ctrl?.errors) return [];

    return Object.entries(ctrl.errors).map(([key, value]) => ({
      key,
      message: this.errorMessages[key]?.(value) ?? `Validation error: ${key}`,
    }));
  });
}

// Usage
@Component({
  imports: [ReactiveFormsModule, ValidationErrorsComponent],
  template: `
    <input formControlName="email">
    <app-validation-errors [control]="form.controls.email" />
  `,
})
export class FormComponent {}
```

## Custom Validators

### Synchronous Validator

```typescript
import { AbstractControl, ValidationErrors, ValidatorFn } from '@angular/forms';

// Validator function
export function forbiddenNameValidator(forbiddenName: RegExp): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    const forbidden = forbiddenName.test(control.value);
    return forbidden ? { forbiddenName: { value: control.value } } : null;
  };
}

// No spaces validator
export function noWhitespaceValidator(): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    const hasWhitespace = /\s/.test(control.value);
    return hasWhitespace ? { whitespace: true } : null;
  };
}

// Strong password validator
export function strongPasswordValidator(): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    const value = control.value;
    if (!value) return null;

    const errors: ValidationErrors = {};

    if (!/[A-Z]/.test(value)) {
      errors['uppercase'] = 'Password must contain uppercase letter';
    }
    if (!/[a-z]/.test(value)) {
      errors['lowercase'] = 'Password must contain lowercase letter';
    }
    if (!/[0-9]/.test(value)) {
      errors['number'] = 'Password must contain number';
    }
    if (!/[!@#$%^&*]/.test(value)) {
      errors['special'] = 'Password must contain special character';
    }

    return Object.keys(errors).length ? errors : null;
  };
}

// Usage
@Component({...})
export class RegistrationComponent {
  private fb = inject(FormBuilder);

  form = this.fb.group({
    username: ['', [
      Validators.required,
      forbiddenNameValidator(/admin/i),
      noWhitespaceValidator(),
    ]],
    password: ['', [
      Validators.required,
      Validators.minLength(8),
      strongPasswordValidator(),
    ]],
  });
}
```

### Cross-Field Validator

```typescript
import { AbstractControl, ValidationErrors, ValidatorFn } from '@angular/forms';

// Password match validator
export function passwordMatchValidator(): ValidatorFn {
  return (group: AbstractControl): ValidationErrors | null => {
    const password = group.get('password')?.value;
    const confirmPassword = group.get('confirmPassword')?.value;

    if (password !== confirmPassword) {
      return { passwordMismatch: true };
    }
    return null;
  };
}

// Date range validator
export function dateRangeValidator(): ValidatorFn {
  return (group: AbstractControl): ValidationErrors | null => {
    const start = group.get('startDate')?.value;
    const end = group.get('endDate')?.value;

    if (start && end && new Date(start) > new Date(end)) {
      return { dateRange: 'Start date must be before end date' };
    }
    return null;
  };
}

// Usage
@Component({
  template: `
    <form [formGroup]="form">
      <input formControlName="password" type="password" placeholder="Password">
      <input formControlName="confirmPassword" type="password" placeholder="Confirm">

      @if (form.errors?.['passwordMismatch']) {
        <span class="error">Passwords do not match</span>
      }
    </form>
  `,
})
export class PasswordFormComponent {
  private fb = inject(FormBuilder);

  form = this.fb.group({
    password: ['', [Validators.required, Validators.minLength(8)]],
    confirmPassword: ['', [Validators.required]],
  }, {
    validators: [passwordMatchValidator()],
  });
}
```

## Async Validators

```typescript
import { Injectable, inject } from '@angular/core';
import { AbstractControl, AsyncValidatorFn, ValidationErrors } from '@angular/forms';
import { Observable, of, timer } from 'rxjs';
import { map, switchMap, catchError } from 'rxjs/operators';

@Injectable({ providedIn: 'root' })
export class ValidationService {
  private http = inject(HttpClient);

  // Check if username is taken
  checkUsernameAvailability(): AsyncValidatorFn {
    return (control: AbstractControl): Observable<ValidationErrors | null> => {
      if (!control.value) {
        return of(null);
      }

      // Debounce the validation
      return timer(500).pipe(
        switchMap(() =>
          this.http.get<{ available: boolean }>(
            `/api/users/check-username?username=${control.value}`
          )
        ),
        map(response =>
          response.available ? null : { usernameTaken: true }
        ),
        catchError(() => of(null)),
      );
    };
  }

  // Check if email exists
  checkEmailExists(): AsyncValidatorFn {
    return (control: AbstractControl): Observable<ValidationErrors | null> => {
      if (!control.value) {
        return of(null);
      }

      return timer(500).pipe(
        switchMap(() =>
          this.http.get<{ exists: boolean }>(
            `/api/users/check-email?email=${control.value}`
          )
        ),
        map(response =>
          response.exists ? { emailExists: true } : null
        ),
        catchError(() => of(null)),
      );
    };
  }
}

// Usage in component
@Component({
  template: `
    <form [formGroup]="form">
      <div class="field">
        <input formControlName="username" placeholder="Username">

        @if (form.controls.username.pending) {
          <span class="checking">Checking availability...</span>
        }
        @if (form.controls.username.errors?.['usernameTaken']) {
          <span class="error">Username is already taken</span>
        }
      </div>
    </form>
  `,
})
export class RegistrationComponent {
  private fb = inject(FormBuilder);
  private validationService = inject(ValidationService);

  form = this.fb.group({
    username: ['',
      [Validators.required, Validators.minLength(3)],
      [this.validationService.checkUsernameAvailability()],
    ],
    email: ['',
      [Validators.required, Validators.email],
      [this.validationService.checkEmailExists()],
    ],
  });
}
```

## Custom Validator Directive (Template-Driven)

```typescript
import { Directive, input } from '@angular/core';
import { NG_VALIDATORS, Validator, AbstractControl, ValidationErrors } from '@angular/forms';

@Directive({
  selector: '[appForbiddenName]',
  standalone: true,
  providers: [{
    provide: NG_VALIDATORS,
    useExisting: ForbiddenNameDirective,
    multi: true,
  }],
})
export class ForbiddenNameDirective implements Validator {
  appForbiddenName = input<string>('');

  validate(control: AbstractControl): ValidationErrors | null {
    const forbidden = new RegExp(this.appForbiddenName(), 'i');
    const isForbidden = forbidden.test(control.value);
    return isForbidden ? { forbiddenName: { value: control.value } } : null;
  }
}

// Usage in template
// <input name="username" [(ngModel)]="username" appForbiddenName="admin">
```

## Conditional Validation

```typescript
@Component({...})
export class ConditionalValidationComponent {
  private fb = inject(FormBuilder);

  form = this.fb.group({
    contactMethod: ['email'],
    email: [''],
    phone: [''],
  });

  constructor() {
    // React to contact method changes
    this.form.controls.contactMethod.valueChanges.subscribe(method => {
      const emailControl = this.form.controls.email;
      const phoneControl = this.form.controls.phone;

      if (method === 'email') {
        emailControl.setValidators([Validators.required, Validators.email]);
        phoneControl.clearValidators();
      } else {
        phoneControl.setValidators([Validators.required, Validators.pattern(/^\d{10}$/)]);
        emailControl.clearValidators();
      }

      emailControl.updateValueAndValidity();
      phoneControl.updateValueAndValidity();
    });
  }
}
```

## Form-Level Validation State

```typescript
@Component({
  template: `
    <form [formGroup]="form" (ngSubmit)="onSubmit()">
      <!-- Fields here -->

      <!-- Form-level error summary -->
      @if (form.invalid && submitted()) {
        <div class="error-summary">
          <h4>Please correct the following errors:</h4>
          <ul>
            @for (error of getAllErrors(); track error.field) {
              <li>{{ error.field }}: {{ error.message }}</li>
            }
          </ul>
        </div>
      }

      <button type="submit">Submit</button>
    </form>
  `,
})
export class ErrorSummaryComponent {
  private fb = inject(FormBuilder);

  submitted = signal(false);

  form = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(8)]],
  });

  onSubmit() {
    this.submitted.set(true);

    if (this.form.valid) {
      // Submit form
    } else {
      // Mark all as touched to show errors
      this.form.markAllAsTouched();
    }
  }

  getAllErrors(): { field: string; message: string }[] {
    const errors: { field: string; message: string }[] = [];

    Object.keys(this.form.controls).forEach(key => {
      const control = this.form.get(key);
      if (control?.errors) {
        Object.keys(control.errors).forEach(errorKey => {
          errors.push({
            field: key,
            message: this.getErrorMessage(errorKey, control.errors![errorKey]),
          });
        });
      }
    });

    return errors;
  }

  private getErrorMessage(errorKey: string, errorValue: any): string {
    const messages: Record<string, string> = {
      required: 'This field is required',
      email: 'Invalid email format',
      minlength: `Minimum ${errorValue.requiredLength} characters`,
      maxlength: `Maximum ${errorValue.requiredLength} characters`,
    };
    return messages[errorKey] || 'Invalid value';
  }
}
```

## Validation with Signals

```typescript
@Component({
  template: `
    <form [formGroup]="form">
      <input formControlName="email" placeholder="Email">

      @if (emailErrors().length > 0 && form.controls.email.touched) {
        <ul class="errors">
          @for (error of emailErrors(); track error) {
            <li>{{ error }}</li>
          }
        </ul>
      }

      <div class="status">
        Form is {{ formStatus() }}
      </div>
    </form>
  `,
})
export class SignalValidationComponent {
  private fb = inject(FormBuilder);

  form = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(8)]],
  });

  // Convert validation state to signals
  formStatus = toSignal(
    this.form.statusChanges,
    { initialValue: this.form.status }
  );

  emailErrors = computed(() => {
    const errors = this.form.controls.email.errors;
    if (!errors) return [];

    const messages: string[] = [];
    if (errors['required']) messages.push('Email is required');
    if (errors['email']) messages.push('Invalid email format');
    return messages;
  });
}
```

## Best Practices

1. **Show errors after touch**: Don't show errors immediately
2. **Provide clear messages**: Explain what's wrong and how to fix
3. **Use async validators wisely**: Debounce to reduce server calls
4. **Validate on appropriate events**: Consider updateOn: 'blur' for performance
5. **Create reusable validators**: Extract common patterns
6. **Handle pending state**: Show loading indicator for async validation
7. **Summarize errors**: Provide form-level error summary for accessibility
8. **Test validators**: Write unit tests for custom validators
