# Angular Service Generator Agent

## Overview

Specialized agent for generating Angular services with signals-based state management, proper dependency injection, and HTTP integration.

## Capabilities

- Generate injectable services with providedIn: 'root'
- Implement signal-based state management
- Create typed HTTP methods with error handling
- Generate reactive computed properties
- Support for feature-scoped services
- Create corresponding unit tests

## Input Requirements

```yaml
required:
  - name: Service name (PascalCase)
  - entity: Entity/model name
  - feature: Feature module name

optional:
  - scope: root | feature | component
  - http_methods: Array of CRUD operations
  - state_properties: Array of state fields
  - computed_properties: Array of derived values
  - dependencies: Other services to inject
```

## Generation Rules

### Naming Conventions
- Service class: `{Name}Service`
- File: `{kebab-case-name}.service.ts`
- Test file: `{kebab-case-name}.service.spec.ts`

### Service Structure
```
core/services/           # Global services (providedIn: 'root')
features/{feature}/
└── services/            # Feature-scoped services
    ├── {name}.service.ts
    └── {name}.service.spec.ts
```

### Code Patterns

#### Basic Service with Signals
```typescript
@Injectable({ providedIn: 'root' })
export class {Name}Service {
  private http = inject(HttpClient);
  private baseUrl = `${environment.apiUrl}/{entities}`;

  // Private state
  private readonly _items = signal<{Entity}[]>([]);
  private readonly _isLoading = signal(false);
  private readonly _error = signal<string | null>(null);

  // Public read-only selectors
  readonly items = this._items.asReadonly();
  readonly isLoading = this._isLoading.asReadonly();
  readonly error = this._error.asReadonly();

  // Computed values
  readonly isEmpty = computed(() => this._items().length === 0);
  readonly count = computed(() => this._items().length);
}
```

#### HTTP Methods Pattern
```typescript
async loadAll(): Promise<void> {
  this._isLoading.set(true);
  this._error.set(null);

  try {
    const items = await firstValueFrom(
      this.http.get<{Entity}[]>(this.baseUrl)
    );
    this._items.set(items);
  } catch (error) {
    this._error.set('Failed to load items');
    console.error('Load error:', error);
  } finally {
    this._isLoading.set(false);
  }
}

async create(input: Create{Entity}Input): Promise<{Entity} | null> {
  try {
    const item = await firstValueFrom(
      this.http.post<{Entity}>(this.baseUrl, input)
    );
    this._items.update(items => [item, ...items]);
    return item;
  } catch (error) {
    this._error.set('Failed to create item');
    return null;
  }
}
```

#### State Update Patterns
```typescript
// Immutable updates
this._items.update(items => items.filter(i => i.id !== id));
this._items.update(items => items.map(i => i.id === id ? updated : i));
this._items.update(items => [...items, newItem]);

// Replace entire state
this._items.set(newItems);
```

## State Management Patterns

### Feature Store Pattern
```typescript
interface {Feature}State {
  items: {Entity}[];
  selectedId: string | null;
  filters: {Filter}State;
  pagination: PaginationState;
  isLoading: boolean;
  error: string | null;
}

@Injectable({ providedIn: 'root' })
export class {Feature}Service {
  private state = signal<{Feature}State>(initialState);

  // Slice selectors
  readonly items = computed(() => this.state().items);
  readonly selectedId = computed(() => this.state().selectedId);
  readonly selected = computed(() => {
    const id = this.selectedId();
    return this.items().find(item => item.id === id);
  });

  // Filtered/derived data
  readonly filteredItems = computed(() => {
    const items = this.items();
    const filters = this.state().filters;
    return applyFilters(items, filters);
  });
}
```

## Integration

- Works with: component-generator, test-generator
- Uses templates: angular-service.md
- Follows skills: services, signals-state

## Examples

### Generate Product Service
```
Input:
  name: Product
  entity: Product
  feature: products
  http_methods: [getAll, getById, create, update, delete]
  state_properties:
    - items: Product[]
    - selectedId: string | null
  computed_properties:
    - selected: Product | undefined
    - isEmpty: boolean

Output: Full CRUD service with signal-based state
```

### Generate Auth Service
```
Input:
  name: Auth
  entity: User
  scope: root
  dependencies: [StorageService, RouterService]
  state_properties:
    - currentUser: User | null
    - isAuthenticated: boolean
    - token: string | null

Output: Authentication service with token management
```
