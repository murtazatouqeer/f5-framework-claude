# Angular Component Generator Agent

## Overview

Specialized agent for generating Angular standalone components following Angular 17+ best practices with signals, new control flow syntax, and proper TypeScript typing.

## Capabilities

- Generate standalone components with proper imports
- Create smart (container) and dumb (presentational) components
- Implement signal-based inputs/outputs (Angular 17.1+)
- Apply new control flow syntax (@if, @for, @switch)
- Generate component tests alongside components
- Support for Angular Material and PrimeNG integrations

## Input Requirements

```yaml
required:
  - name: Component name (PascalCase)
  - feature: Feature module name
  - type: smart | dumb | layout | page

optional:
  - inputs: Array of input signal definitions
  - outputs: Array of output definitions
  - services: Services to inject
  - route: Route path if page component
  - ui_library: material | primeng | tailwind
```

## Generation Rules

### Naming Conventions
- Component class: `{Name}Component`
- Selector: `app-{kebab-case-name}`
- File: `{kebab-case-name}.component.ts`
- Test file: `{kebab-case-name}.component.spec.ts`

### Component Structure
```
features/{feature}/
├── components/
│   └── {component}/
│       ├── {component}.component.ts
│       └── {component}.component.spec.ts
└── pages/
    └── {page}/
        ├── {page}.component.ts
        └── {page}.component.spec.ts
```

### Code Patterns

#### Smart Component (Container)
```typescript
@Component({
  selector: 'app-{name}',
  standalone: true,
  imports: [CommonModule, ...childComponents],
  template: `...`,
})
export class {Name}Component {
  private service = inject({Service});

  // State from service
  items = this.service.items;
  isLoading = this.service.isLoading;

  // Event handlers delegate to service
  onAction(item: Item) {
    this.service.doAction(item);
  }
}
```

#### Dumb Component (Presentational)
```typescript
@Component({
  selector: 'app-{name}',
  standalone: true,
  imports: [CommonModule],
  template: `...`,
})
export class {Name}Component {
  // Input signals
  data = input.required<DataType>();
  isActive = input(false);

  // Output signals
  action = output<ActionType>();

  // Computed values
  displayValue = computed(() => transform(this.data()));
}
```

## Template Patterns

### New Control Flow (Angular 17+)
```html
@if (condition()) {
  <div>Truthy content</div>
} @else if (otherCondition()) {
  <div>Other content</div>
} @else {
  <div>Fallback content</div>
}

@for (item of items(); track item.id) {
  <app-item [item]="item" />
} @empty {
  <p>No items found</p>
}

@switch (status()) {
  @case ('loading') { <spinner /> }
  @case ('error') { <error-message /> }
  @default { <content /> }
}
```

## Integration

- Works with: service-generator, test-generator
- Uses templates: angular-component.md
- Follows skills: standalone-components, signals, component-basics

## Examples

### Generate Product Card Component
```
Input:
  name: ProductCard
  feature: products
  type: dumb
  inputs:
    - name: product, type: Product, required: true
    - name: showActions, type: boolean, default: true
  outputs:
    - name: addToCart, type: Product
    - name: viewDetails, type: string

Output: Standalone presentational component with signal inputs/outputs
```

### Generate Dashboard Page Component
```
Input:
  name: Dashboard
  feature: dashboard
  type: page
  services: [DashboardService, AuthService]
  route: /dashboard

Output: Smart component with service injection and routing
```
