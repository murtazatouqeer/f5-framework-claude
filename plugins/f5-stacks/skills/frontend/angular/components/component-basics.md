# Angular Component Basics

## Overview

Components are the main building blocks of Angular applications. They control a patch of screen called a view.

## Component Structure

### Basic Component

```typescript
import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-greeting',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="greeting">
      <h1>Hello, {{ name }}!</h1>
      <p>Welcome to Angular</p>
    </div>
  `,
  styles: [`
    .greeting {
      padding: 1rem;
      background-color: #f5f5f5;
      border-radius: 8px;
    }
    h1 {
      color: #333;
      margin-bottom: 0.5rem;
    }
  `],
})
export class GreetingComponent {
  name = 'World';
}
```

### Component Metadata

```typescript
@Component({
  // Required
  selector: 'app-my-component',  // HTML tag name
  template: `<p>Inline template</p>`,  // OR
  templateUrl: './my.component.html',  // External template

  // Optional
  standalone: true,  // Standalone component (recommended)
  imports: [],       // Dependencies for standalone components
  styles: [],        // Inline styles
  styleUrl: './my.component.scss',  // External styles
  styleUrls: ['./my.component.scss'],  // Multiple style files
  encapsulation: ViewEncapsulation.Emulated,  // Style encapsulation
  changeDetection: ChangeDetectionStrategy.OnPush,  // Change detection
  providers: [],     // Component-level providers
  host: {},          // Host element bindings
  animations: [],    // Animation triggers
})
```

## Component with Properties

```typescript
import { Component, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';

interface Task {
  id: number;
  title: string;
  completed: boolean;
}

@Component({
  selector: 'app-task-list',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="task-list">
      <h2>Tasks ({{ completedCount() }}/{{ tasks().length }})</h2>

      @for (task of tasks(); track task.id) {
        <div class="task" [class.completed]="task.completed">
          <input
            type="checkbox"
            [checked]="task.completed"
            (change)="toggleTask(task.id)"
          >
          <span>{{ task.title }}</span>
        </div>
      } @empty {
        <p>No tasks yet</p>
      }

      <button (click)="addTask()">Add Task</button>
    </div>
  `,
})
export class TaskListComponent {
  // State with signals
  tasks = signal<Task[]>([
    { id: 1, title: 'Learn Angular', completed: false },
    { id: 2, title: 'Build an app', completed: false },
  ]);

  // Computed value
  completedCount = computed(() =>
    this.tasks().filter(t => t.completed).length
  );

  toggleTask(id: number) {
    this.tasks.update(tasks =>
      tasks.map(t =>
        t.id === id ? { ...t, completed: !t.completed } : t
      )
    );
  }

  addTask() {
    const newTask: Task = {
      id: Date.now(),
      title: `Task ${this.tasks().length + 1}`,
      completed: false,
    };
    this.tasks.update(tasks => [...tasks, newTask]);
  }
}
```

## Smart vs Dumb Components

### Smart Component (Container)

```typescript
// Handles business logic, service injection, state management
@Component({
  selector: 'app-product-page',
  standalone: true,
  imports: [CommonModule, ProductListComponent, ProductFiltersComponent],
  template: `
    <div class="product-page">
      <app-product-filters
        [categories]="categories()"
        (filterChange)="onFilterChange($event)"
      />

      @if (isLoading()) {
        <div class="loading">Loading...</div>
      } @else {
        <app-product-list
          [products]="filteredProducts()"
          (productSelect)="onProductSelect($event)"
        />
      }
    </div>
  `,
})
export class ProductPageComponent {
  private productService = inject(ProductService);
  private router = inject(Router);

  // State from service
  products = this.productService.products;
  categories = this.productService.categories;
  isLoading = this.productService.isLoading;

  // Local state
  filters = signal<ProductFilters>({});

  // Derived state
  filteredProducts = computed(() =>
    applyFilters(this.products(), this.filters())
  );

  constructor() {
    this.productService.loadProducts();
  }

  onFilterChange(filters: ProductFilters) {
    this.filters.set(filters);
  }

  onProductSelect(product: Product) {
    this.router.navigate(['/products', product.id]);
  }
}
```

### Dumb Component (Presentational)

```typescript
// Pure UI component, receives data via inputs, emits events via outputs
@Component({
  selector: 'app-product-list',
  standalone: true,
  imports: [CommonModule, ProductCardComponent],
  template: `
    <div class="product-grid">
      @for (product of products(); track product.id) {
        <app-product-card
          [product]="product"
          (click)="productSelect.emit(product)"
        />
      }
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ProductListComponent {
  products = input<Product[]>([]);
  productSelect = output<Product>();
}
```

## Component Templates

### Template Expressions

```html
<!-- Property binding -->
<img [src]="imageUrl" [alt]="imageAlt">

<!-- Event binding -->
<button (click)="onClick()">Click me</button>

<!-- Two-way binding -->
<input [(ngModel)]="name">

<!-- Interpolation -->
<p>Hello, {{ name }}!</p>

<!-- Attribute binding -->
<button [attr.aria-label]="label">...</button>

<!-- Class binding -->
<div [class.active]="isActive">...</div>
<div [class]="classObject">...</div>

<!-- Style binding -->
<div [style.color]="textColor">...</div>
<div [style.font-size.px]="fontSize">...</div>

<!-- Template reference variable -->
<input #nameInput type="text">
<button (click)="greet(nameInput.value)">Greet</button>
```

### Template Statements

```html
<!-- Method calls -->
<button (click)="save()">Save</button>
<button (click)="delete(item.id)">Delete</button>

<!-- Property assignment -->
<button (click)="isOpen = !isOpen">Toggle</button>

<!-- Multiple statements -->
<button (click)="save(); close()">Save and Close</button>

<!-- Event object -->
<input (input)="onInput($event)">
<form (submit)="onSubmit($event)">
```

## Component Communication

### Parent to Child

```typescript
// Parent
@Component({
  template: `
    <app-child
      [message]="parentMessage"
      [config]="config"
    />
  `,
})
export class ParentComponent {
  parentMessage = 'Hello from parent';
  config = { theme: 'dark' };
}

// Child
@Component({
  selector: 'app-child',
  template: `<p>{{ message() }}</p>`,
})
export class ChildComponent {
  message = input.required<string>();
  config = input<Config>({ theme: 'light' });
}
```

### Child to Parent

```typescript
// Child
@Component({
  selector: 'app-child',
  template: `
    <button (click)="notify.emit('Hello!')">Notify Parent</button>
  `,
})
export class ChildComponent {
  notify = output<string>();
}

// Parent
@Component({
  template: `
    <app-child (notify)="onNotify($event)" />
    <p>Message: {{ message }}</p>
  `,
})
export class ParentComponent {
  message = '';

  onNotify(event: string) {
    this.message = event;
  }
}
```

## Component Styles

### Encapsulation Modes

```typescript
import { ViewEncapsulation } from '@angular/core';

@Component({
  // Emulated (default) - styles scoped to component
  encapsulation: ViewEncapsulation.Emulated,

  // None - styles apply globally
  encapsulation: ViewEncapsulation.None,

  // ShadowDom - native shadow DOM
  encapsulation: ViewEncapsulation.ShadowDom,
})
```

### Special Selectors

```scss
// :host - targets the host element
:host {
  display: block;
  padding: 1rem;
}

:host(.active) {
  border: 2px solid blue;
}

:host-context(.dark-theme) {
  background: #333;
}

// ::ng-deep - pierce encapsulation (use sparingly)
:host ::ng-deep .third-party-widget {
  color: red;
}
```

## Best Practices

1. **Keep components small and focused**: Single responsibility
2. **Use OnPush change detection**: For presentational components
3. **Prefer standalone components**: Modern Angular approach
4. **Use signals for state**: Cleaner than Subject/BehaviorSubject
5. **Separate smart and dumb components**: Better testability
6. **Use input signals**: `input()` instead of `@Input()`
7. **Component naming**: Suffix with `Component`, use PascalCase
