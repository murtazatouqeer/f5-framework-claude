# Angular Component Template

## Basic Standalone Component

```typescript
// features/{{feature}}/components/{{name}}/{{name}}.component.ts
import { Component, inject, signal, computed, input, output } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-{{name}}',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './{{name}}.component.html',
  styleUrl: './{{name}}.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class {{PascalName}}Component {
  // Inputs
  data = input<{{DataType}} | null>(null);
  title = input.required<string>();

  // Outputs
  action = output<{{ActionType}}>();

  // Internal state
  isLoading = signal(false);
  error = signal<string | null>(null);

  // Computed values
  displayData = computed(() => {
    const d = this.data();
    if (!d) return null;
    return this.transformData(d);
  });

  // Methods
  onAction(value: {{ActionType}}) {
    this.action.emit(value);
  }

  private transformData(data: {{DataType}}): {{TransformedType}} {
    // Transform logic
    return data;
  }
}
```

## Component Template

```html
<!-- features/{{feature}}/components/{{name}}/{{name}}.component.html -->
<div class="{{name}}-container">
  @if (isLoading()) {
    <div class="loading">
      <span class="spinner"></span>
      <span>Loading...</span>
    </div>
  } @else if (error(); as err) {
    <div class="error">
      <span class="error-icon">⚠️</span>
      <span>{{ err }}</span>
    </div>
  } @else if (displayData(); as data) {
    <h2>{{ title() }}</h2>
    <div class="content">
      <!-- Content here -->
    </div>
    <button (click)="onAction(data)">Action</button>
  } @else {
    <div class="empty">
      <span>No data available</span>
    </div>
  }
</div>
```

## Component Styles

```scss
// features/{{feature}}/components/{{name}}/{{name}}.component.scss
.{{name}}-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1rem;

  .loading {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: var(--color-text-secondary);
  }

  .error {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem;
    background: var(--color-error-bg);
    color: var(--color-error);
    border-radius: 4px;
  }

  .content {
    flex: 1;
  }

  .empty {
    text-align: center;
    padding: 2rem;
    color: var(--color-text-muted);
  }
}
```

## Component with Form

```typescript
import { Component, inject, signal, output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';

@Component({
  selector: 'app-{{name}}-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <form [formGroup]="form" (ngSubmit)="onSubmit()">
      <div class="field">
        <label for="name">Name</label>
        <input id="name" formControlName="name" type="text">
        @if (form.controls.name.errors?.['required'] && form.controls.name.touched) {
          <span class="error">Name is required</span>
        }
      </div>

      <div class="field">
        <label for="email">Email</label>
        <input id="email" formControlName="email" type="email">
        @if (form.controls.email.errors?.['email'] && form.controls.email.touched) {
          <span class="error">Invalid email</span>
        }
      </div>

      <div class="actions">
        <button type="button" (click)="onCancel()">Cancel</button>
        <button type="submit" [disabled]="form.invalid || isSubmitting()">
          {{ isSubmitting() ? 'Saving...' : 'Save' }}
        </button>
      </div>
    </form>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class {{PascalName}}FormComponent {
  private fb = inject(FormBuilder);

  submitted = output<FormData>();
  cancelled = output<void>();

  isSubmitting = signal(false);

  form = this.fb.nonNullable.group({
    name: ['', [Validators.required, Validators.minLength(2)]],
    email: ['', [Validators.required, Validators.email]],
  });

  onSubmit() {
    if (this.form.valid) {
      this.isSubmitting.set(true);
      this.submitted.emit(this.form.getRawValue());
    }
  }

  onCancel() {
    this.cancelled.emit();
  }
}
```

## Component with List

```typescript
import { Component, input, output, computed } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-{{name}}-list',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="list-container">
      <div class="list-header">
        <h3>{{ title() }}</h3>
        <span class="count">{{ items().length }} items</span>
      </div>

      @if (items().length === 0) {
        <div class="empty-state">
          <p>{{ emptyMessage() }}</p>
        </div>
      } @else {
        <ul class="list">
          @for (item of items(); track item.id) {
            <li class="list-item" [class.selected]="item.id === selectedId()">
              <span class="item-name">{{ item.name }}</span>
              <div class="item-actions">
                <button (click)="onSelect(item)">Select</button>
                <button (click)="onDelete(item.id)">Delete</button>
              </div>
            </li>
          }
        </ul>
      }
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class {{PascalName}}ListComponent {
  items = input<Item[]>([]);
  selectedId = input<string | null>(null);
  title = input('Items');
  emptyMessage = input('No items found');

  selected = output<Item>();
  deleted = output<string>();

  onSelect(item: Item) {
    this.selected.emit(item);
  }

  onDelete(id: string) {
    this.deleted.emit(id);
  }
}
```

## Page Component

```typescript
import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { {{PascalName}}Service } from '../../services/{{name}}.service';

@Component({
  selector: 'app-{{name}}-page',
  standalone: true,
  imports: [CommonModule, RouterLink],
  template: `
    <div class="page">
      <header class="page-header">
        <h1>{{ pageTitle }}</h1>
        <nav class="breadcrumb">
          <a routerLink="/">Home</a>
          <span>/</span>
          <span>{{ pageTitle }}</span>
        </nav>
      </header>

      <main class="page-content">
        @if (isLoading()) {
          <div class="loading-overlay">
            <app-spinner />
          </div>
        }

        @if (error(); as err) {
          <app-error-display [message]="err" (retry)="loadData()" />
        }

        @if (data(); as d) {
          <app-{{name}}-content [data]="d" />
        }
      </main>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class {{PascalName}}PageComponent {
  private service = inject({{PascalName}}Service);

  pageTitle = '{{Title}}';

  data = signal<{{DataType}} | null>(null);
  isLoading = signal(false);
  error = signal<string | null>(null);

  constructor() {
    this.loadData();
  }

  loadData() {
    this.isLoading.set(true);
    this.error.set(null);

    this.service.getData().subscribe({
      next: data => {
        this.data.set(data);
        this.isLoading.set(false);
      },
      error: err => {
        this.error.set(err.message);
        this.isLoading.set(false);
      },
    });
  }
}
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{name}}` | kebab-case name | `user-profile` |
| `{{PascalName}}` | PascalCase name | `UserProfile` |
| `{{feature}}` | Feature folder | `users` |
| `{{DataType}}` | Data interface | `User` |
| `{{ActionType}}` | Action payload type | `UserAction` |
| `{{Title}}` | Page title | `User Profile` |
