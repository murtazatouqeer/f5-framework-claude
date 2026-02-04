# Angular Reactive Forms

## Overview

Reactive forms provide a model-driven approach to handling form inputs. They offer explicit, immutable form state, synchronous access to data, and powerful validation capabilities.

## Setup

```typescript
// app.config.ts
import { ApplicationConfig } from '@angular/core';
import { provideRouter } from '@angular/router';

export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(routes),
    // ReactiveFormsModule is imported per-component in standalone
  ],
};
```

## Basic Form

```typescript
import { Component, inject } from '@angular/core';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';

@Component({
  selector: 'app-login-form',
  standalone: true,
  imports: [ReactiveFormsModule],
  template: `
    <form [formGroup]="form" (ngSubmit)="onSubmit()">
      <div class="field">
        <label for="email">Email</label>
        <input
          id="email"
          type="email"
          formControlName="email"
          [class.error]="form.controls.email.invalid && form.controls.email.touched"
        >
        @if (form.controls.email.errors?.['required'] && form.controls.email.touched) {
          <span class="error">Email is required</span>
        }
        @if (form.controls.email.errors?.['email'] && form.controls.email.touched) {
          <span class="error">Invalid email format</span>
        }
      </div>

      <div class="field">
        <label for="password">Password</label>
        <input
          id="password"
          type="password"
          formControlName="password"
        >
        @if (form.controls.password.errors?.['required'] && form.controls.password.touched) {
          <span class="error">Password is required</span>
        }
        @if (form.controls.password.errors?.['minlength'] && form.controls.password.touched) {
          <span class="error">
            Password must be at least
            {{ form.controls.password.errors?.['minlength'].requiredLength }} characters
          </span>
        }
      </div>

      <button type="submit" [disabled]="form.invalid || isSubmitting()">
        {{ isSubmitting() ? 'Logging in...' : 'Login' }}
      </button>
    </form>
  `,
})
export class LoginFormComponent {
  private fb = inject(FormBuilder);

  isSubmitting = signal(false);

  form = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(8)]],
  });

  onSubmit() {
    if (this.form.valid) {
      this.isSubmitting.set(true);
      const { email, password } = this.form.value;
      // Submit logic here
    }
  }
}
```

## FormGroup and FormControl

```typescript
import { FormGroup, FormControl, Validators } from '@angular/forms';

// Using FormGroup directly
const form = new FormGroup({
  firstName: new FormControl('', Validators.required),
  lastName: new FormControl('', Validators.required),
  email: new FormControl('', [Validators.required, Validators.email]),
});

// Using FormBuilder (recommended)
@Component({...})
export class UserFormComponent {
  private fb = inject(FormBuilder);

  form = this.fb.group({
    firstName: ['', Validators.required],
    lastName: ['', Validators.required],
    email: ['', [Validators.required, Validators.email]],
    age: [null as number | null, [Validators.min(0), Validators.max(120)]],
  });
}
```

## Nested FormGroups

```typescript
@Component({
  template: `
    <form [formGroup]="form">
      <div formGroupName="personal">
        <input formControlName="firstName" placeholder="First Name">
        <input formControlName="lastName" placeholder="Last Name">
      </div>

      <div formGroupName="address">
        <input formControlName="street" placeholder="Street">
        <input formControlName="city" placeholder="City">
        <input formControlName="zipCode" placeholder="Zip Code">
      </div>
    </form>
  `,
})
export class ProfileFormComponent {
  private fb = inject(FormBuilder);

  form = this.fb.group({
    personal: this.fb.group({
      firstName: ['', Validators.required],
      lastName: ['', Validators.required],
    }),
    address: this.fb.group({
      street: [''],
      city: [''],
      zipCode: ['', Validators.pattern(/^\d{5}(-\d{4})?$/)],
    }),
  });

  // Access nested controls
  get firstName() {
    return this.form.get('personal.firstName');
  }
}
```

## FormArray

```typescript
@Component({
  template: `
    <form [formGroup]="form">
      <div formArrayName="skills">
        @for (skill of skills.controls; track $index) {
          <div class="skill-row">
            <input [formControlName]="$index" placeholder="Skill">
            <button type="button" (click)="removeSkill($index)">Remove</button>
          </div>
        }
      </div>
      <button type="button" (click)="addSkill()">Add Skill</button>
    </form>
  `,
})
export class SkillsFormComponent {
  private fb = inject(FormBuilder);

  form = this.fb.group({
    skills: this.fb.array([
      this.fb.control('', Validators.required),
    ]),
  });

  get skills() {
    return this.form.controls.skills;
  }

  addSkill() {
    this.skills.push(this.fb.control('', Validators.required));
  }

  removeSkill(index: number) {
    this.skills.removeAt(index);
  }
}
```

## Complex FormArray with FormGroups

```typescript
interface Experience {
  company: string;
  position: string;
  startDate: string;
  endDate: string | null;
  current: boolean;
}

@Component({
  template: `
    <form [formGroup]="form">
      <div formArrayName="experiences">
        @for (exp of experiences.controls; track $index) {
          <div [formGroupName]="$index" class="experience-card">
            <input formControlName="company" placeholder="Company">
            <input formControlName="position" placeholder="Position">
            <input formControlName="startDate" type="date">

            <label>
              <input type="checkbox" formControlName="current">
              Current position
            </label>

            @if (!exp.get('current')?.value) {
              <input formControlName="endDate" type="date">
            }

            <button type="button" (click)="removeExperience($index)">
              Remove
            </button>
          </div>
        }
      </div>
      <button type="button" (click)="addExperience()">Add Experience</button>
    </form>
  `,
})
export class ExperienceFormComponent {
  private fb = inject(FormBuilder);

  form = this.fb.group({
    experiences: this.fb.array<FormGroup>([]),
  });

  get experiences() {
    return this.form.controls.experiences;
  }

  addExperience() {
    const experienceGroup = this.fb.group({
      company: ['', Validators.required],
      position: ['', Validators.required],
      startDate: ['', Validators.required],
      endDate: [''],
      current: [false],
    });

    this.experiences.push(experienceGroup);
  }

  removeExperience(index: number) {
    this.experiences.removeAt(index);
  }
}
```

## Typed Forms

```typescript
// Strongly typed forms (Angular 14+)
interface LoginForm {
  email: FormControl<string>;
  password: FormControl<string>;
  rememberMe: FormControl<boolean>;
}

@Component({...})
export class TypedLoginFormComponent {
  private fb = inject(FormBuilder);

  // NonNullable form builder
  form = this.fb.nonNullable.group<LoginForm>({
    email: this.fb.nonNullable.control('', [Validators.required, Validators.email]),
    password: this.fb.nonNullable.control('', [Validators.required]),
    rememberMe: this.fb.nonNullable.control(false),
  });

  onSubmit() {
    // Values are properly typed
    const { email, password, rememberMe } = this.form.getRawValue();
    // email: string, password: string, rememberMe: boolean
  }
}
```

## Form State and Updates

```typescript
@Component({...})
export class FormStateComponent {
  private fb = inject(FormBuilder);

  form = this.fb.group({
    name: [''],
    email: [''],
  });

  // Check form state
  checkState() {
    console.log('Valid:', this.form.valid);
    console.log('Invalid:', this.form.invalid);
    console.log('Dirty:', this.form.dirty);
    console.log('Pristine:', this.form.pristine);
    console.log('Touched:', this.form.touched);
    console.log('Untouched:', this.form.untouched);
    console.log('Pending:', this.form.pending); // async validation
  }

  // Update form values
  updateForm() {
    // Set single value
    this.form.controls.name.setValue('John');

    // Patch multiple values
    this.form.patchValue({
      name: 'John',
      email: 'john@example.com',
    });

    // Reset form
    this.form.reset();

    // Reset with values
    this.form.reset({
      name: 'Default',
      email: '',
    });
  }

  // Disable/Enable
  toggleDisabled() {
    if (this.form.disabled) {
      this.form.enable();
    } else {
      this.form.disable();
    }

    // Single control
    this.form.controls.email.disable();
    this.form.controls.email.enable();
  }
}
```

## Value Changes Observable

```typescript
@Component({...})
export class ValueChangesComponent implements OnInit {
  private fb = inject(FormBuilder);
  private destroyRef = inject(DestroyRef);

  form = this.fb.group({
    search: [''],
    filters: this.fb.group({
      category: [''],
      sortBy: ['name'],
    }),
  });

  ngOnInit() {
    // Listen to single control
    this.form.controls.search.valueChanges
      .pipe(
        debounceTime(300),
        distinctUntilChanged(),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe(value => {
        console.log('Search:', value);
      });

    // Listen to entire form
    this.form.valueChanges
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(value => {
        console.log('Form value:', value);
      });

    // Listen to status changes
    this.form.statusChanges
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(status => {
        console.log('Form status:', status);
      });
  }
}
```

## Dynamic Form Fields

```typescript
@Component({
  template: `
    <form [formGroup]="form">
      @for (field of fields(); track field.name) {
        <div class="field">
          <label>{{ field.label }}</label>

          @switch (field.type) {
            @case ('text') {
              <input type="text" [formControlName]="field.name">
            }
            @case ('number') {
              <input type="number" [formControlName]="field.name">
            }
            @case ('select') {
              <select [formControlName]="field.name">
                @for (option of field.options; track option.value) {
                  <option [value]="option.value">{{ option.label }}</option>
                }
              </select>
            }
            @case ('checkbox') {
              <input type="checkbox" [formControlName]="field.name">
            }
          }
        </div>
      }
    </form>
  `,
})
export class DynamicFormComponent {
  private fb = inject(FormBuilder);

  fields = input<FormFieldConfig[]>([]);
  form = new FormGroup({});

  constructor() {
    effect(() => {
      this.buildForm(this.fields());
    });
  }

  private buildForm(fields: FormFieldConfig[]) {
    const group: Record<string, FormControl> = {};

    for (const field of fields) {
      const validators = [];
      if (field.required) validators.push(Validators.required);
      if (field.minLength) validators.push(Validators.minLength(field.minLength));
      if (field.maxLength) validators.push(Validators.maxLength(field.maxLength));

      group[field.name] = new FormControl(field.defaultValue ?? '', validators);
    }

    this.form = new FormGroup(group);
  }
}

interface FormFieldConfig {
  name: string;
  label: string;
  type: 'text' | 'number' | 'select' | 'checkbox';
  required?: boolean;
  minLength?: number;
  maxLength?: number;
  defaultValue?: any;
  options?: { value: string; label: string }[];
}
```

## Form with Signals

```typescript
@Component({
  template: `
    <form [formGroup]="form" (ngSubmit)="onSubmit()">
      <input formControlName="email" placeholder="Email">
      <input formControlName="password" type="password" placeholder="Password">

      @if (formErrors().length > 0) {
        <ul class="errors">
          @for (error of formErrors(); track error) {
            <li>{{ error }}</li>
          }
        </ul>
      }

      <button [disabled]="!isValid()">Submit</button>
    </form>
  `,
})
export class SignalFormComponent {
  private fb = inject(FormBuilder);

  form = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(8)]],
  });

  // Convert form state to signals
  isValid = toSignal(
    this.form.statusChanges.pipe(map(() => this.form.valid)),
    { initialValue: this.form.valid }
  );

  formValue = toSignal(this.form.valueChanges, {
    initialValue: this.form.value,
  });

  formErrors = computed(() => {
    const errors: string[] = [];
    const controls = this.form.controls;

    if (controls.email.errors?.['required']) {
      errors.push('Email is required');
    }
    if (controls.email.errors?.['email']) {
      errors.push('Invalid email format');
    }
    if (controls.password.errors?.['required']) {
      errors.push('Password is required');
    }
    if (controls.password.errors?.['minlength']) {
      errors.push('Password must be at least 8 characters');
    }

    return errors;
  });

  onSubmit() {
    if (this.form.valid) {
      console.log(this.formValue());
    }
  }
}
```

## Best Practices

1. **Use FormBuilder**: Cleaner syntax than direct instantiation
2. **Use NonNullable**: For strict typing with no null values
3. **Type your forms**: Use interfaces for form structure
4. **Handle validation errors**: Show clear error messages
5. **Clean up subscriptions**: Use takeUntilDestroyed
6. **Use computed for derived state**: Form errors, validity checks
7. **Disable submit when invalid**: Prevent invalid submissions
