# Angular Test Generator Agent

## Overview

Specialized agent for generating comprehensive Angular tests using Jasmine/Jest with Angular Testing utilities. Supports component, service, guard, and integration tests.

## Capabilities

- Generate component unit tests with TestBed
- Create service tests with HttpClientTestingModule
- Generate guard and resolver tests
- Create integration tests for complex flows
- Support for signal-based component testing
- Generate test utilities and mocks

## Input Requirements

```yaml
required:
  - target: Path to file being tested
  - type: component | service | guard | pipe | directive | integration

optional:
  - test_cases: Specific scenarios to test
  - mocks: Services/dependencies to mock
  - test_framework: jasmine | jest
  - coverage_target: Minimum coverage percentage
```

## Generation Rules

### Naming Conventions
- Test file: `{name}.spec.ts` (alongside source file)
- Mock file: `{name}.mock.ts` (in __mocks__ folder)
- Test utilities: `testing/` folder

### Test Structure
```
features/{feature}/
├── components/
│   └── {component}/
│       ├── {component}.component.ts
│       └── {component}.component.spec.ts
├── services/
│   ├── {service}.service.ts
│   └── {service}.service.spec.ts
└── testing/
    ├── mocks/
    └── fixtures/
```

### Code Patterns

#### Component Test (Standalone with Signals)
```typescript
// product-card.component.spec.ts
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { ProductCardComponent } from './product-card.component';
import { Product } from '../../../models/product.model';

describe('ProductCardComponent', () => {
  let component: ProductCardComponent;
  let fixture: ComponentFixture<ProductCardComponent>;

  const mockProduct: Product = {
    id: '1',
    name: 'Test Product',
    price: 99.99,
    description: 'Test description',
    imageUrl: 'test.jpg',
    isOnSale: false,
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ProductCardComponent],
      providers: [provideRouter([])],
    }).compileComponents();

    fixture = TestBed.createComponent(ProductCardComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  describe('with product input', () => {
    beforeEach(() => {
      // Set input signal value using fixture.componentRef
      fixture.componentRef.setInput('product', mockProduct);
      fixture.detectChanges();
    });

    it('should display product name', () => {
      const nameEl = fixture.nativeElement.querySelector('h3');
      expect(nameEl.textContent).toContain(mockProduct.name);
    });

    it('should display product price', () => {
      const priceEl = fixture.nativeElement.querySelector('.price');
      expect(priceEl.textContent).toContain('99.99');
    });

    it('should not show sale badge when not on sale', () => {
      const badge = fixture.nativeElement.querySelector('.badge');
      expect(badge).toBeNull();
    });

    it('should show sale badge when on sale', () => {
      fixture.componentRef.setInput('product', { ...mockProduct, isOnSale: true });
      fixture.detectChanges();

      const badge = fixture.nativeElement.querySelector('.badge');
      expect(badge).toBeTruthy();
      expect(badge.textContent).toContain('Sale');
    });
  });

  describe('outputs', () => {
    beforeEach(() => {
      fixture.componentRef.setInput('product', mockProduct);
      fixture.detectChanges();
    });

    it('should emit addToCart when add button clicked', () => {
      const spy = jasmine.createSpy('addToCart');
      component.addToCart.subscribe(spy);

      const button = fixture.nativeElement.querySelector('button');
      button.click();

      expect(spy).toHaveBeenCalledWith(mockProduct);
    });
  });
});
```

#### Service Test with HTTP
```typescript
// product.service.spec.ts
import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { ProductService } from './product.service';
import { Product } from '../models/product.model';

describe('ProductService', () => {
  let service: ProductService;
  let httpMock: HttpTestingController;

  const mockProducts: Product[] = [
    { id: '1', name: 'Product 1', price: 10 },
    { id: '2', name: 'Product 2', price: 20 },
  ];

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [ProductService],
    });

    service = TestBed.inject(ProductService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('loadAll', () => {
    it('should fetch products and update state', async () => {
      const loadPromise = service.loadAll();

      const req = httpMock.expectOne('/api/products');
      expect(req.request.method).toBe('GET');
      req.flush(mockProducts);

      await loadPromise;

      expect(service.items()).toEqual(mockProducts);
      expect(service.isLoading()).toBe(false);
      expect(service.error()).toBeNull();
    });

    it('should handle error', async () => {
      const loadPromise = service.loadAll();

      const req = httpMock.expectOne('/api/products');
      req.error(new ErrorEvent('Network error'));

      await loadPromise;

      expect(service.items()).toEqual([]);
      expect(service.error()).toBeTruthy();
    });

    it('should set loading state', () => {
      service.loadAll();
      expect(service.isLoading()).toBe(true);

      httpMock.expectOne('/api/products').flush([]);
    });
  });

  describe('create', () => {
    const newProduct = { name: 'New Product', price: 30 };

    it('should create product and add to state', async () => {
      const created: Product = { id: '3', ...newProduct };

      const createPromise = service.create(newProduct);

      const req = httpMock.expectOne('/api/products');
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual(newProduct);
      req.flush(created);

      const result = await createPromise;

      expect(result).toEqual(created);
      expect(service.items()).toContain(created);
    });
  });

  describe('computed properties', () => {
    beforeEach(async () => {
      const loadPromise = service.loadAll();
      httpMock.expectOne('/api/products').flush(mockProducts);
      await loadPromise;
    });

    it('should compute isEmpty correctly', () => {
      expect(service.isEmpty()).toBe(false);
    });

    it('should compute count correctly', () => {
      expect(service.count()).toBe(2);
    });
  });
});
```

#### Guard Test
```typescript
// auth.guard.spec.ts
import { TestBed } from '@angular/core/testing';
import { Router, ActivatedRouteSnapshot, RouterStateSnapshot } from '@angular/router';
import { authGuard } from './auth.guard';
import { AuthService } from '../services/auth.service';

describe('authGuard', () => {
  let authService: jasmine.SpyObj<AuthService>;
  let router: jasmine.SpyObj<Router>;

  const mockRoute = {} as ActivatedRouteSnapshot;
  const mockState = { url: '/protected' } as RouterStateSnapshot;

  beforeEach(() => {
    authService = jasmine.createSpyObj('AuthService', ['isAuthenticated']);
    router = jasmine.createSpyObj('Router', ['navigate']);

    TestBed.configureTestingModule({
      providers: [
        { provide: AuthService, useValue: authService },
        { provide: Router, useValue: router },
      ],
    });
  });

  it('should allow access when authenticated', () => {
    authService.isAuthenticated.and.returnValue(true);

    const result = TestBed.runInInjectionContext(() =>
      authGuard(mockRoute, mockState)
    );

    expect(result).toBe(true);
    expect(router.navigate).not.toHaveBeenCalled();
  });

  it('should redirect to login when not authenticated', () => {
    authService.isAuthenticated.and.returnValue(false);

    const result = TestBed.runInInjectionContext(() =>
      authGuard(mockRoute, mockState)
    );

    expect(result).toBe(false);
    expect(router.navigate).toHaveBeenCalledWith(['/auth/login'], {
      queryParams: { returnUrl: '/protected' },
    });
  });
});
```

#### Integration Test
```typescript
// product-list.integration.spec.ts
import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { ProductListComponent } from './product-list.component';
import { ProductService } from '../../services/product.service';

describe('ProductList Integration', () => {
  let fixture: ComponentFixture<ProductListComponent>;
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ProductListComponent, HttpClientTestingModule],
      providers: [ProductService, provideRouter([])],
    }).compileComponents();

    fixture = TestBed.createComponent(ProductListComponent);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should load and display products', fakeAsync(() => {
    fixture.detectChanges();

    const req = httpMock.expectOne('/api/products');
    req.flush([
      { id: '1', name: 'Product 1', price: 10 },
      { id: '2', name: 'Product 2', price: 20 },
    ]);

    tick();
    fixture.detectChanges();

    const items = fixture.nativeElement.querySelectorAll('.item');
    expect(items.length).toBe(2);
  }));

  it('should show loading state', () => {
    fixture.detectChanges();

    const loading = fixture.nativeElement.querySelector('.loading');
    expect(loading).toBeTruthy();

    httpMock.expectOne('/api/products').flush([]);
  });
});
```

## Test Utilities

```typescript
// testing/component-harness.ts
import { ComponentFixture } from '@angular/core/testing';

export function setSignalInput<T, K extends keyof T>(
  fixture: ComponentFixture<T>,
  inputName: K,
  value: T[K]
): void {
  (fixture.componentRef as any).setInput(inputName, value);
  fixture.detectChanges();
}

// testing/mock-providers.ts
export function provideMockAuthService(overrides?: Partial<AuthService>) {
  return {
    provide: AuthService,
    useValue: {
      isAuthenticated: jasmine.createSpy().and.returnValue(false),
      currentUser: jasmine.createSpy().and.returnValue(null),
      login: jasmine.createSpy(),
      logout: jasmine.createSpy(),
      ...overrides,
    },
  };
}
```

## Integration

- Works with: component-generator, service-generator, guard-generator
- Uses templates: angular-test.md
- Follows skills: unit-testing, component-testing

## Examples

### Generate Component Test
```
Input:
  target: features/products/components/product-card/product-card.component.ts
  type: component
  test_cases:
    - renders product information
    - emits events on user actions
    - handles conditional display

Output: Comprehensive component spec with signal input testing
```

### Generate Service Test
```
Input:
  target: core/services/product.service.ts
  type: service
  mocks: [HttpClient]
  test_cases:
    - CRUD operations
    - error handling
    - state updates

Output: Service spec with HTTP mocking
```
