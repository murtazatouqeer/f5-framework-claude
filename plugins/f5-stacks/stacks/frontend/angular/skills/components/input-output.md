# Angular Input and Output

## Overview

Input and Output are the primary mechanisms for component communication in Angular. Angular 17+ introduces signal-based inputs and outputs for improved reactivity.

## Signal-Based Inputs (Angular 17.1+)

### Required Inputs

```typescript
import { Component, input } from '@angular/core';

@Component({
  selector: 'app-user-card',
  standalone: true,
  template: `
    <div class="user-card">
      <h3>{{ user().name }}</h3>
      <p>{{ user().email }}</p>
    </div>
  `,
})
export class UserCardComponent {
  // Required input - must be provided by parent
  user = input.required<User>();
}

// Usage - will error if user is not provided
// <app-user-card [user]="currentUser" />
```

### Optional Inputs with Defaults

```typescript
@Component({
  selector: 'app-button',
  standalone: true,
  template: `
    <button
      [class]="variant()"
      [disabled]="disabled()"
      [attr.aria-label]="ariaLabel()"
    >
      <ng-content />
    </button>
  `,
})
export class ButtonComponent {
  // Optional with default value
  variant = input<'primary' | 'secondary' | 'danger'>('primary');
  disabled = input(false);
  ariaLabel = input<string | undefined>(undefined);
  size = input<'sm' | 'md' | 'lg'>('md');
}

// Usage
// <app-button>Click me</app-button>
// <app-button variant="danger" [disabled]="true">Delete</app-button>
```

### Input Transform

```typescript
@Component({
  selector: 'app-thumbnail',
  standalone: true,
  template: `<img [src]="imageUrl()" [width]="size()">`,
})
export class ThumbnailComponent {
  imageUrl = input.required<string>();

  // Transform string to number
  size = input(100, {
    transform: (value: string | number) =>
      typeof value === 'string' ? parseInt(value, 10) : value,
  });
}

// Transform boolean attribute
@Component({
  selector: 'app-toggle',
  template: `...`,
})
export class ToggleComponent {
  // Supports <app-toggle disabled> (no value)
  disabled = input(false, {
    transform: (value: boolean | string) =>
      value === '' || value === true || value === 'true',
  });
}
```

### Input Alias

```typescript
@Component({
  selector: 'app-custom-input',
  template: `<input [value]="value()">`,
})
export class CustomInputComponent {
  // Internal name: value, External name: ngModel
  value = input('', { alias: 'ngModel' });
}

// Usage
// <app-custom-input ngModel="Hello" />
```

## Signal-Based Outputs

### Basic Output

```typescript
import { Component, output } from '@angular/core';

@Component({
  selector: 'app-search-box',
  standalone: true,
  template: `
    <div class="search-box">
      <input
        type="text"
        [value]="query"
        (input)="onInput($event)"
        (keyup.enter)="onSearch()"
      >
      <button (click)="onSearch()">Search</button>
    </div>
  `,
})
export class SearchBoxComponent {
  query = '';

  // Output signals
  search = output<string>();
  clear = output<void>();

  onInput(event: Event) {
    this.query = (event.target as HTMLInputElement).value;
  }

  onSearch() {
    this.search.emit(this.query);
  }

  onClear() {
    this.query = '';
    this.clear.emit();
  }
}

// Parent usage
@Component({
  template: `
    <app-search-box
      (search)="handleSearch($event)"
      (clear)="handleClear()"
    />
  `,
})
export class ParentComponent {
  handleSearch(query: string) {
    console.log('Searching for:', query);
  }

  handleClear() {
    console.log('Search cleared');
  }
}
```

### Output with Complex Data

```typescript
interface SelectionEvent {
  item: Product;
  action: 'select' | 'deselect';
}

@Component({
  selector: 'app-product-item',
  template: `
    <div class="product" [class.selected]="isSelected()">
      <span>{{ product().name }}</span>
      <button (click)="toggleSelection()">
        {{ isSelected() ? 'Deselect' : 'Select' }}
      </button>
    </div>
  `,
})
export class ProductItemComponent {
  product = input.required<Product>();
  isSelected = input(false);

  selectionChange = output<SelectionEvent>();

  toggleSelection() {
    this.selectionChange.emit({
      item: this.product(),
      action: this.isSelected() ? 'deselect' : 'select',
    });
  }
}
```

### Output Alias

```typescript
@Component({
  selector: 'app-slider',
  template: `...`,
})
export class SliderComponent {
  // Internal: change, External: valueChange
  change = output<number>({ alias: 'valueChange' });
}

// Usage
// <app-slider (valueChange)="onValueChange($event)" />
```

## Model Signal (Two-Way Binding)

### Basic Two-Way Binding

```typescript
import { Component, model } from '@angular/core';

@Component({
  selector: 'app-counter',
  standalone: true,
  template: `
    <div class="counter">
      <button (click)="decrement()">-</button>
      <span>{{ count() }}</span>
      <button (click)="increment()">+</button>
    </div>
  `,
})
export class CounterComponent {
  // Two-way bindable model
  count = model(0);

  increment() {
    this.count.update(c => c + 1);
  }

  decrement() {
    this.count.update(c => c - 1);
  }
}

// Parent usage
@Component({
  template: `
    <app-counter [(count)]="myCount" />
    <p>Parent count: {{ myCount() }}</p>
  `,
})
export class ParentComponent {
  myCount = signal(10);
}
```

### Required Model

```typescript
@Component({
  selector: 'app-toggle-switch',
  template: `
    <button
      [class.on]="checked()"
      (click)="checked.set(!checked())"
    >
      {{ checked() ? 'ON' : 'OFF' }}
    </button>
  `,
})
export class ToggleSwitchComponent {
  // Required two-way binding
  checked = model.required<boolean>();
}

// Parent must provide initial value
// <app-toggle-switch [(checked)]="isEnabled" />
```

### Custom Form Control with Model

```typescript
@Component({
  selector: 'app-rating',
  standalone: true,
  template: `
    <div class="rating">
      @for (star of stars; track star) {
        <span
          class="star"
          [class.filled]="star <= value()"
          (click)="value.set(star)"
          (keydown.enter)="value.set(star)"
          tabindex="0"
        >
          ★
        </span>
      }
    </div>
  `,
})
export class RatingComponent {
  value = model(0);
  maxStars = input(5);

  get stars() {
    return Array.from({ length: this.maxStars() }, (_, i) => i + 1);
  }
}

// Usage with two-way binding
// <app-rating [(value)]="productRating" />
```

## Computed from Inputs

```typescript
@Component({
  selector: 'app-full-name',
  template: `<span>{{ fullName() }}</span>`,
})
export class FullNameComponent {
  firstName = input('');
  lastName = input('');

  // Computed from input signals
  fullName = computed(() =>
    `${this.firstName()} ${this.lastName()}`.trim()
  );
}

// More complex example
@Component({
  selector: 'app-price-display',
  template: `
    <div class="price">
      <span class="amount">{{ formattedPrice() }}</span>
      @if (discount() > 0) {
        <span class="original">{{ formattedOriginal() }}</span>
        <span class="discount">-{{ discount() }}%</span>
      }
    </div>
  `,
})
export class PriceDisplayComponent {
  price = input.required<number>();
  discount = input(0);
  currency = input('USD');

  discountedPrice = computed(() =>
    this.price() * (1 - this.discount() / 100)
  );

  formattedPrice = computed(() =>
    new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: this.currency(),
    }).format(this.discountedPrice())
  );

  formattedOriginal = computed(() =>
    new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: this.currency(),
    }).format(this.price())
  );
}
```

## Effect with Inputs

```typescript
@Component({
  selector: 'app-user-profile',
  template: `...`,
})
export class UserProfileComponent {
  userId = input.required<string>();

  private userService = inject(UserService);

  constructor() {
    // Effect runs when userId changes
    effect(() => {
      const id = this.userId();
      this.userService.loadUser(id);
    });
  }
}
```

## Legacy Decorator Approach (Reference)

```typescript
import { Component, Input, Output, EventEmitter } from '@angular/core';

@Component({...})
export class LegacyComponent {
  // Legacy approach - still works
  @Input() name: string = '';
  @Input({ required: true }) id!: string;
  @Input({ transform: booleanAttribute }) disabled = false;
  @Input({ alias: 'user-name' }) userName = '';

  @Output() nameChange = new EventEmitter<string>();
  @Output('user-selected') selected = new EventEmitter<User>();
}
```

## Best Practices

1. **Use signal inputs**: Prefer `input()` over `@Input()`
2. **Mark required inputs**: Use `input.required()` for mandatory data
3. **Provide defaults**: Give sensible defaults for optional inputs
4. **Use transforms**: For type coercion (string to number, etc.)
5. **Use model for two-way**: Prefer `model()` over input + output pairs
6. **Computed over effects**: Derive values with `computed()` when possible
7. **Type your inputs/outputs**: Always specify generic types
