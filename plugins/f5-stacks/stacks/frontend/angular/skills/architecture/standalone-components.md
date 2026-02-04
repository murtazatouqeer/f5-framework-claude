# Angular Standalone Components

## Overview

Standalone components are self-contained Angular components that declare their dependencies directly, without requiring NgModules.

## Basic Standalone Component

```typescript
import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-hello',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="hello">
      <h1>Hello, {{ name }}!</h1>
    </div>
  `,
  styles: [`
    .hello {
      padding: 1rem;
      background: #f0f0f0;
    }
  `],
})
export class HelloComponent {
  name = 'Angular';
}
```

## Component with Dependencies

```typescript
import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, RouterOutlet } from '@angular/router';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';

// Custom components
import { ButtonComponent } from '@shared/components/button/button.component';
import { CardComponent } from '@shared/components/card/card.component';

// Services
import { ProductService } from './services/product.service';

@Component({
  selector: 'app-product-list',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    FormsModule,
    ButtonComponent,
    CardComponent,
  ],
  template: `
    <div class="product-list">
      @for (product of products(); track product.id) {
        <app-card>
          <h3>{{ product.name }}</h3>
          <p>{{ product.price | currency }}</p>
          <app-button (click)="addToCart(product)">
            Add to Cart
          </app-button>
        </app-card>
      }
    </div>
  `,
})
export class ProductListComponent {
  private productService = inject(ProductService);

  products = this.productService.products;

  constructor() {
    this.productService.loadProducts();
  }

  addToCart(product: Product) {
    // Handle add to cart
  }
}
```

## Input and Output Signals

### Angular 17.1+ Input Signals

```typescript
import { Component, input, output, computed } from '@angular/core';
import { CommonModule } from '@angular/common';

interface User {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  avatar: string;
}

@Component({
  selector: 'app-user-card',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="user-card" [class.selected]="isSelected()">
      <img [src]="user().avatar" [alt]="fullName()">
      <div class="info">
        <h3>{{ fullName() }}</h3>
        <p>{{ user().email }}</p>
      </div>
      <div class="actions">
        <button (click)="edit.emit(user())">Edit</button>
        <button (click)="delete.emit(user().id)">Delete</button>
      </div>
    </div>
  `,
})
export class UserCardComponent {
  // Required input - must be provided
  user = input.required<User>();

  // Optional input with default value
  isSelected = input(false);

  // Optional input with transform
  size = input('medium', {
    transform: (v: string) => v.toLowerCase() as 'small' | 'medium' | 'large',
  });

  // Computed value from inputs
  fullName = computed(() =>
    `${this.user().firstName} ${this.user().lastName}`
  );

  // Output signals
  edit = output<User>();
  delete = output<string>();
}
```

### Model Signals (Two-Way Binding)

```typescript
import { Component, model } from '@angular/core';

@Component({
  selector: 'app-toggle',
  standalone: true,
  template: `
    <button
      [class.active]="value()"
      (click)="value.set(!value())"
    >
      {{ value() ? 'ON' : 'OFF' }}
    </button>
  `,
})
export class ToggleComponent {
  // Two-way binding with model()
  value = model(false);
}

// Parent usage
@Component({
  template: `
    <app-toggle [(value)]="darkMode" />
    <p>Dark mode is {{ darkMode() ? 'enabled' : 'disabled' }}</p>
  `,
})
export class SettingsComponent {
  darkMode = signal(false);
}
```

## Content Projection

```typescript
import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-card',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="card">
      <div class="card-header">
        <ng-content select="[card-header]" />
      </div>
      <div class="card-body">
        <ng-content />
      </div>
      <div class="card-footer">
        <ng-content select="[card-footer]" />
      </div>
    </div>
  `,
})
export class CardComponent {}

// Usage
@Component({
  template: `
    <app-card>
      <h3 card-header>Card Title</h3>
      <p>This is the card body content.</p>
      <button card-footer>Action</button>
    </app-card>
  `,
})
export class ParentComponent {}
```

## Component with ViewChild/ViewChildren

```typescript
import { Component, ViewChild, ViewChildren, QueryList, ElementRef, afterNextRender } from '@angular/core';

@Component({
  selector: 'app-form',
  standalone: true,
  template: `
    <form #formRef>
      <input #firstInput type="text">
      <input type="email">
      <button type="submit">Submit</button>
    </form>

    @for (item of items; track item) {
      <div #itemRef>{{ item }}</div>
    }
  `,
})
export class FormComponent {
  @ViewChild('formRef') formRef!: ElementRef<HTMLFormElement>;
  @ViewChild('firstInput') firstInput!: ElementRef<HTMLInputElement>;
  @ViewChildren('itemRef') itemRefs!: QueryList<ElementRef>;

  items = ['Item 1', 'Item 2', 'Item 3'];

  constructor() {
    // Use afterNextRender for DOM access
    afterNextRender(() => {
      this.firstInput.nativeElement.focus();
    });
  }
}
```

## Host Element Binding

```typescript
import { Component, HostBinding, HostListener, input } from '@angular/core';

@Component({
  selector: 'app-tooltip',
  standalone: true,
  template: `<ng-content />`,
  host: {
    '[class.visible]': 'isVisible',
    '[attr.role]': '"tooltip"',
    '(mouseenter)': 'show()',
    '(mouseleave)': 'hide()',
  },
})
export class TooltipComponent {
  position = input<'top' | 'bottom'>('top');

  isVisible = false;

  @HostBinding('class')
  get hostClass() {
    return `tooltip tooltip-${this.position()}`;
  }

  show() {
    this.isVisible = true;
  }

  hide() {
    this.isVisible = false;
  }
}

// Alternative using decorators
@Component({...})
export class TooltipComponent {
  @HostBinding('class.visible') isVisible = false;

  @HostListener('mouseenter')
  onMouseEnter() {
    this.isVisible = true;
  }

  @HostListener('mouseleave')
  onMouseLeave() {
    this.isVisible = false;
  }
}
```

## Providers in Standalone Components

```typescript
// Feature-scoped service
@Injectable()
export class FeatureService {
  // Not providedIn: 'root' - must be provided explicitly
}

@Component({
  selector: 'app-feature-container',
  standalone: true,
  providers: [FeatureService], // Provides for this component and children
  template: `
    <app-feature-child />
  `,
})
export class FeatureContainerComponent {
  private featureService = inject(FeatureService);
}

// Using injection tokens
const FEATURE_CONFIG = new InjectionToken<FeatureConfig>('feature.config');

@Component({
  selector: 'app-feature',
  standalone: true,
  providers: [
    { provide: FEATURE_CONFIG, useValue: { theme: 'dark' } },
  ],
  template: `...`,
})
export class FeatureComponent {
  private config = inject(FEATURE_CONFIG);
}
```

## Bootstrapping Standalone Application

```typescript
// main.ts
import { bootstrapApplication } from '@angular/platform-browser';
import { appConfig } from './app/app.config';
import { AppComponent } from './app/app.component';

bootstrapApplication(AppComponent, appConfig)
  .catch(err => console.error(err));

// app.config.ts
import { ApplicationConfig, provideZoneChangeDetection } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';

import { routes } from './app.routes';
import { authInterceptor } from './core/interceptors/auth.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(routes),
    provideHttpClient(withInterceptors([authInterceptor])),
  ],
};
```

## Best Practices

1. **Always use standalone**: Default to standalone components in Angular 17+
2. **Import only what you need**: Keep imports minimal and specific
3. **Use input signals**: Prefer `input()` over `@Input()` for new code
4. **Lazy load features**: Use `loadComponent` and `loadChildren` in routes
5. **Component-scoped styles**: Use component styles instead of global styles
6. **Typed inputs**: Always specify types for input signals
