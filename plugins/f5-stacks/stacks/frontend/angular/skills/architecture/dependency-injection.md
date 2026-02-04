# Angular Dependency Injection

## Overview

Angular's Dependency Injection (DI) system is a hierarchical injector that provides dependencies to components, services, and other Angular constructs.

## Basic Injection

### Using inject() Function (Recommended)

```typescript
import { Component, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router, ActivatedRoute } from '@angular/router';
import { ProductService } from './services/product.service';

@Component({
  selector: 'app-product-list',
  standalone: true,
  template: `...`,
})
export class ProductListComponent {
  // Modern approach - inject() function
  private http = inject(HttpClient);
  private router = inject(Router);
  private route = inject(ActivatedRoute);
  private productService = inject(ProductService);

  // Can be used directly
  products = this.productService.products;
}
```

### Constructor Injection (Legacy)

```typescript
@Component({...})
export class ProductListComponent {
  // Legacy approach - still valid but less preferred
  constructor(
    private http: HttpClient,
    private router: Router,
    private productService: ProductService,
  ) {}
}
```

## Injectable Services

### Root-Level Service (Singleton)

```typescript
import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root', // Singleton across the entire app
})
export class AuthService {
  private _isAuthenticated = signal(false);
  readonly isAuthenticated = this._isAuthenticated.asReadonly();

  login(credentials: Credentials) {
    // Login logic
  }

  logout() {
    this._isAuthenticated.set(false);
  }
}
```

### Feature-Scoped Service

```typescript
// Not using providedIn - must be provided explicitly
@Injectable()
export class FeatureDataService {
  private data = signal<FeatureData | null>(null);
  // ...
}

// Provided at feature level
@Component({
  selector: 'app-feature-container',
  standalone: true,
  providers: [FeatureDataService], // New instance for this component tree
  template: `<router-outlet />`,
})
export class FeatureContainerComponent {}
```

### Component-Scoped Service

```typescript
@Injectable()
export class FormStateService {
  private formData = signal({});
  // ...
}

@Component({
  selector: 'app-multi-step-form',
  standalone: true,
  providers: [FormStateService], // New instance for each component
  template: `...`,
})
export class MultiStepFormComponent {
  private formState = inject(FormStateService);
}
```

## Injection Tokens

### Creating Tokens

```typescript
import { InjectionToken } from '@angular/core';

// Simple value token
export const API_URL = new InjectionToken<string>('api.url');

// Complex object token
export interface AppConfig {
  apiUrl: string;
  features: {
    darkMode: boolean;
    analytics: boolean;
  };
}

export const APP_CONFIG = new InjectionToken<AppConfig>('app.config');

// Token with factory
export const STORAGE = new InjectionToken<Storage>('storage', {
  providedIn: 'root',
  factory: () => localStorage,
});
```

### Providing Token Values

```typescript
// In app.config.ts
export const appConfig: ApplicationConfig = {
  providers: [
    { provide: API_URL, useValue: 'https://api.example.com' },
    {
      provide: APP_CONFIG,
      useValue: {
        apiUrl: 'https://api.example.com',
        features: {
          darkMode: true,
          analytics: false,
        },
      },
    },
  ],
};

// Using the token
@Component({...})
export class ApiService {
  private apiUrl = inject(API_URL);
  private config = inject(APP_CONFIG);
}
```

## Provider Types

### useClass

```typescript
// Interface
export abstract class LoggerService {
  abstract log(message: string): void;
}

// Implementation
@Injectable()
export class ConsoleLoggerService extends LoggerService {
  log(message: string) {
    console.log(message);
  }
}

// Production implementation
@Injectable()
export class ProductionLoggerService extends LoggerService {
  log(message: string) {
    // Send to logging service
  }
}

// Provider configuration
providers: [
  {
    provide: LoggerService,
    useClass: environment.production
      ? ProductionLoggerService
      : ConsoleLoggerService,
  },
];
```

### useFactory

```typescript
// Factory function
function httpClientFactory(auth: AuthService) {
  return new HttpClient(/* ... */);
}

providers: [
  {
    provide: HttpClient,
    useFactory: (auth: AuthService) => {
      // Create and configure HttpClient
      return new HttpClient(/* config */);
    },
    deps: [AuthService], // Dependencies for factory
  },
];

// With injection token
const WINDOW = new InjectionToken<Window>('window');

providers: [
  {
    provide: WINDOW,
    useFactory: () => window,
  },
];
```

### useValue

```typescript
providers: [
  { provide: API_URL, useValue: 'https://api.example.com' },
  { provide: LOCALE_ID, useValue: 'en-US' },
];
```

### useExisting

```typescript
// Alias one service to another
providers: [
  OldService,
  { provide: NewService, useExisting: OldService },
];
```

## Injection Modifiers

### Optional Injection

```typescript
import { inject } from '@angular/core';

@Component({...})
export class MyComponent {
  // Returns null if not provided
  private optionalService = inject(OptionalService, { optional: true });

  // With default value
  private config = inject(CONFIG_TOKEN, { optional: true }) ?? defaultConfig;
}
```

### Self, SkipSelf, Host

```typescript
import { inject, SkipSelf, Self, Host } from '@angular/core';

@Component({...})
export class ChildComponent {
  // Only from this component's injector
  private selfService = inject(MyService, { self: true });

  // Only from parent injectors
  private parentService = inject(MyService, { skipSelf: true });

  // Only from host component's injector
  private hostService = inject(MyService, { host: true });
}
```

## Multi Providers

```typescript
// Token for multi-provider
export const HTTP_INTERCEPTORS = new InjectionToken<HttpInterceptorFn[]>(
  'http.interceptors'
);

// Multiple providers for same token
providers: [
  {
    provide: HTTP_INTERCEPTORS,
    useValue: authInterceptor,
    multi: true,
  },
  {
    provide: HTTP_INTERCEPTORS,
    useValue: loggingInterceptor,
    multi: true,
  },
  {
    provide: HTTP_INTERCEPTORS,
    useValue: errorInterceptor,
    multi: true,
  },
];

// Using multi providers
@Injectable({ providedIn: 'root' })
export class InterceptorManager {
  private interceptors = inject(HTTP_INTERCEPTORS);
  // interceptors is an array of all provided interceptors
}
```

## Hierarchical Injection

```typescript
// Root level - singleton
@Injectable({ providedIn: 'root' })
export class GlobalService {}

// Route level
const routes: Routes = [
  {
    path: 'feature',
    providers: [FeatureService], // New instance for this route
    children: [...],
  },
];

// Component level
@Component({
  providers: [ComponentService], // New instance for this component tree
})
export class ParentComponent {}

// Injection resolution order:
// 1. Component's own providers
// 2. Parent component's providers
// 3. Route providers
// 4. Root providers
```

## Advanced Patterns

### Forward Reference

```typescript
import { forwardRef, inject } from '@angular/core';

// When service depends on a later-defined class
@Injectable({ providedIn: 'root' })
export class ServiceA {
  private serviceB = inject(forwardRef(() => ServiceB));
}

@Injectable({ providedIn: 'root' })
export class ServiceB {
  private serviceA = inject(ServiceA);
}
```

### Injection Context

```typescript
import { inject, runInInjectionContext, Injector } from '@angular/core';

@Component({...})
export class MyComponent {
  private injector = inject(Injector);

  ngOnInit() {
    // Run code with injection context outside constructor
    runInInjectionContext(this.injector, () => {
      const service = inject(MyService);
      // Use service
    });
  }

  // Or assert injection context
  someMethod() {
    assertInInjectionContext(this.someMethod);
    const service = inject(MyService);
  }
}
```

### Environment Injector

```typescript
import { createEnvironmentInjector, EnvironmentInjector } from '@angular/core';

// Create a child injector
const childInjector = createEnvironmentInjector(
  [
    { provide: MyService, useClass: MockMyService },
  ],
  parentInjector
);

// Use in dynamic component creation
const componentRef = createComponent(MyComponent, {
  environmentInjector: childInjector,
});
```

## Best Practices

1. **Prefer inject() over constructor injection**: Cleaner and more flexible
2. **Use providedIn: 'root' for singletons**: Tree-shakable and easy to use
3. **Scope services appropriately**: Don't make everything a singleton
4. **Use injection tokens for configuration**: Better than string-based keys
5. **Avoid circular dependencies**: Use `forwardRef` only when necessary
6. **Keep services focused**: Single responsibility principle applies
