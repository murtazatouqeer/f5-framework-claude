# Angular Test Template

## Component Test Setup

```typescript
// features/{{feature}}/components/{{name}}/{{name}}.component.spec.ts
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { signal } from '@angular/core';
import { {{PascalName}}Component } from './{{name}}.component';

describe('{{PascalName}}Component', () => {
  let component: {{PascalName}}Component;
  let fixture: ComponentFixture<{{PascalName}}Component>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [{{PascalName}}Component],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    }).compileComponents();

    fixture = TestBed.createComponent({{PascalName}}Component);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
```

## Testing Signal Inputs

```typescript
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Component, signal } from '@angular/core';
import { UserCardComponent } from './user-card.component';
import { User } from '../../models/user.model';

describe('UserCardComponent', () => {
  let fixture: ComponentFixture<UserCardComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [UserCardComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(UserCardComponent);
  });

  it('should display user name', () => {
    const user: User = { id: '1', name: 'John Doe', email: 'john@example.com' };

    // Set signal input using componentRef
    fixture.componentRef.setInput('user', user);
    fixture.detectChanges();

    const nameElement = fixture.nativeElement.querySelector('.user-name');
    expect(nameElement.textContent).toContain('John Doe');
  });

  it('should handle null user', () => {
    fixture.componentRef.setInput('user', null);
    fixture.detectChanges();

    const emptyState = fixture.nativeElement.querySelector('.empty-state');
    expect(emptyState).toBeTruthy();
  });
});
```

## Testing Signal Outputs

```typescript
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ButtonComponent } from './button.component';

describe('ButtonComponent', () => {
  let fixture: ComponentFixture<ButtonComponent>;
  let component: ButtonComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ButtonComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(ButtonComponent);
    component = fixture.componentInstance;
  });

  it('should emit clicked event', () => {
    const clickSpy = jest.fn();

    // Subscribe to output
    component.clicked.subscribe(clickSpy);

    const button = fixture.nativeElement.querySelector('button');
    button.click();

    expect(clickSpy).toHaveBeenCalledTimes(1);
  });

  it('should emit with payload', () => {
    const selectSpy = jest.fn();
    component.selected.subscribe(selectSpy);

    fixture.componentRef.setInput('item', { id: '1', name: 'Test' });
    fixture.detectChanges();

    const selectButton = fixture.nativeElement.querySelector('.select-btn');
    selectButton.click();

    expect(selectSpy).toHaveBeenCalledWith({ id: '1', name: 'Test' });
  });
});
```

## Testing with Host Component

```typescript
import { Component, signal } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ItemListComponent } from './item-list.component';

@Component({
  standalone: true,
  imports: [ItemListComponent],
  template: `
    <app-item-list
      [items]="items()"
      [selectedId]="selectedId()"
      (selected)="onSelect($event)"
    />
  `,
})
class TestHostComponent {
  items = signal([
    { id: '1', name: 'Item 1' },
    { id: '2', name: 'Item 2' },
  ]);
  selectedId = signal<string | null>(null);
  selectedItem: any = null;

  onSelect(item: any) {
    this.selectedItem = item;
    this.selectedId.set(item.id);
  }
}

describe('ItemListComponent with Host', () => {
  let fixture: ComponentFixture<TestHostComponent>;
  let host: TestHostComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TestHostComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(TestHostComponent);
    host = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should render all items', () => {
    const items = fixture.nativeElement.querySelectorAll('.list-item');
    expect(items.length).toBe(2);
  });

  it('should emit selection to host', () => {
    const firstItem = fixture.nativeElement.querySelector('.list-item');
    firstItem.click();

    expect(host.selectedItem).toEqual({ id: '1', name: 'Item 1' });
    expect(host.selectedId()).toBe('1');
  });
});
```

## Service Test Template

```typescript
// core/services/{{name}}.service.spec.ts
import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { {{PascalName}}Service } from './{{name}}.service';

describe('{{PascalName}}Service', () => {
  let service: {{PascalName}}Service;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        {{PascalName}}Service,
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });

    service = TestBed.inject({{PascalName}}Service);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  describe('getAll', () => {
    it('should fetch all items', () => {
      const mockData = [{ id: '1', name: 'Test' }];

      service.getAll().subscribe(data => {
        expect(data).toEqual(mockData);
      });

      const req = httpMock.expectOne('/api/items');
      expect(req.request.method).toBe('GET');
      req.flush(mockData);
    });

    it('should handle error', () => {
      service.getAll().subscribe({
        error: err => {
          expect(err.message).toContain('error');
        },
      });

      const req = httpMock.expectOne('/api/items');
      req.flush('Error', { status: 500, statusText: 'Server Error' });
    });
  });

  describe('create', () => {
    it('should create item', () => {
      const newItem = { name: 'New Item' };
      const createdItem = { id: '1', ...newItem };

      service.create(newItem).subscribe(data => {
        expect(data).toEqual(createdItem);
      });

      const req = httpMock.expectOne('/api/items');
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual(newItem);
      req.flush(createdItem);
    });
  });
});
```

## Testing Service with Signals

```typescript
import { TestBed } from '@angular/core/testing';
import { UserService } from './user.service';

describe('UserService with Signals', () => {
  let service: UserService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [UserService],
    });
    service = TestBed.inject(UserService);
  });

  it('should have initial empty state', () => {
    expect(service.users()).toEqual([]);
    expect(service.selectedUser()).toBeNull();
    expect(service.isLoading()).toBeFalse();
  });

  it('should update users signal', () => {
    const users = [{ id: '1', name: 'John' }];
    service.setUsers(users);
    expect(service.users()).toEqual(users);
  });

  it('should compute filtered users', () => {
    service.setUsers([
      { id: '1', name: 'John', active: true },
      { id: '2', name: 'Jane', active: false },
    ]);
    service.setFilter('active');

    expect(service.filteredUsers()).toEqual([
      { id: '1', name: 'John', active: true },
    ]);
  });
});
```

## Guard Test Template

```typescript
// core/guards/auth.guard.spec.ts
import { TestBed } from '@angular/core/testing';
import { Router, ActivatedRouteSnapshot, RouterStateSnapshot } from '@angular/router';
import { authGuard } from './auth.guard';
import { AuthService } from '../services/auth.service';

describe('authGuard', () => {
  let authService: jest.Mocked<AuthService>;
  let router: jest.Mocked<Router>;

  beforeEach(() => {
    authService = {
      isAuthenticated: jest.fn(),
    } as any;

    router = {
      createUrlTree: jest.fn().mockReturnValue('/login'),
    } as any;

    TestBed.configureTestingModule({
      providers: [
        { provide: AuthService, useValue: authService },
        { provide: Router, useValue: router },
      ],
    });
  });

  it('should allow access when authenticated', () => {
    authService.isAuthenticated.mockReturnValue(true);

    const result = TestBed.runInInjectionContext(() =>
      authGuard({} as ActivatedRouteSnapshot, { url: '/dashboard' } as RouterStateSnapshot)
    );

    expect(result).toBe(true);
  });

  it('should redirect to login when not authenticated', () => {
    authService.isAuthenticated.mockReturnValue(false);

    const result = TestBed.runInInjectionContext(() =>
      authGuard({} as ActivatedRouteSnapshot, { url: '/dashboard' } as RouterStateSnapshot)
    );

    expect(router.createUrlTree).toHaveBeenCalledWith(['/auth/login'], {
      queryParams: { returnUrl: '/dashboard' },
    });
  });
});
```

## Interceptor Test Template

```typescript
// core/interceptors/auth.interceptor.spec.ts
import { TestBed } from '@angular/core/testing';
import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { authInterceptor } from './auth.interceptor';
import { AuthService } from '../services/auth.service';

describe('authInterceptor', () => {
  let httpClient: HttpClient;
  let httpMock: HttpTestingController;
  let authService: jest.Mocked<AuthService>;

  beforeEach(() => {
    authService = {
      getAccessToken: jest.fn(),
      refreshToken: jest.fn(),
      logout: jest.fn(),
    } as any;

    TestBed.configureTestingModule({
      providers: [
        { provide: AuthService, useValue: authService },
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
      ],
    });

    httpClient = TestBed.inject(HttpClient);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should add auth header when token exists', () => {
    authService.getAccessToken.mockReturnValue('test-token');

    httpClient.get('/api/data').subscribe();

    const req = httpMock.expectOne('/api/data');
    expect(req.request.headers.get('Authorization')).toBe('Bearer test-token');
    req.flush({});
  });

  it('should not add auth header for login endpoint', () => {
    httpClient.get('/auth/login').subscribe();

    const req = httpMock.expectOne('/auth/login');
    expect(req.request.headers.has('Authorization')).toBeFalse();
    req.flush({});
  });
});
```

## Pipe Test Template

```typescript
// shared/pipes/truncate.pipe.spec.ts
import { TruncatePipe } from './truncate.pipe';

describe('TruncatePipe', () => {
  let pipe: TruncatePipe;

  beforeEach(() => {
    pipe = new TruncatePipe();
  });

  it('should create', () => {
    expect(pipe).toBeTruthy();
  });

  it('should return empty string for null', () => {
    expect(pipe.transform(null)).toBe('');
  });

  it('should return empty string for undefined', () => {
    expect(pipe.transform(undefined)).toBe('');
  });

  it('should not truncate short text', () => {
    expect(pipe.transform('Hello', 10)).toBe('Hello');
  });

  it('should truncate long text with default ellipsis', () => {
    const text = 'This is a long text that should be truncated';
    expect(pipe.transform(text, 10)).toBe('This is a ...');
  });

  it('should use custom ellipsis', () => {
    expect(pipe.transform('Hello World', 5, '---')).toBe('Hello---');
  });
});
```

## Directive Test Template

```typescript
// shared/directives/highlight.directive.spec.ts
import { Component } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HighlightDirective } from './highlight.directive';

@Component({
  standalone: true,
  imports: [HighlightDirective],
  template: `
    <p appHighlight [highlightColor]="color">Test Text</p>
  `,
})
class TestHostComponent {
  color = 'yellow';
}

describe('HighlightDirective', () => {
  let fixture: ComponentFixture<TestHostComponent>;
  let host: TestHostComponent;
  let element: HTMLElement;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TestHostComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(TestHostComponent);
    host = fixture.componentInstance;
    element = fixture.nativeElement.querySelector('p');
    fixture.detectChanges();
  });

  it('should highlight on mouseenter', () => {
    element.dispatchEvent(new MouseEvent('mouseenter'));
    expect(element.style.backgroundColor).toBe('yellow');
  });

  it('should remove highlight on mouseleave', () => {
    element.dispatchEvent(new MouseEvent('mouseenter'));
    element.dispatchEvent(new MouseEvent('mouseleave'));
    expect(element.style.backgroundColor).toBe('transparent');
  });

  it('should use custom highlight color', () => {
    host.color = 'red';
    fixture.detectChanges();

    element.dispatchEvent(new MouseEvent('mouseenter'));
    expect(element.style.backgroundColor).toBe('red');
  });
});
```

## Form Testing

```typescript
import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { ReactiveFormsModule } from '@angular/forms';
import { LoginFormComponent } from './login-form.component';

describe('LoginFormComponent', () => {
  let fixture: ComponentFixture<LoginFormComponent>;
  let component: LoginFormComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LoginFormComponent, ReactiveFormsModule],
    }).compileComponents();

    fixture = TestBed.createComponent(LoginFormComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should be invalid initially', () => {
    expect(component.form.valid).toBeFalse();
  });

  it('should validate email format', () => {
    const emailControl = component.form.controls.email;

    emailControl.setValue('invalid');
    expect(emailControl.errors?.['email']).toBeTruthy();

    emailControl.setValue('valid@example.com');
    expect(emailControl.errors).toBeNull();
  });

  it('should validate required fields', () => {
    const passwordControl = component.form.controls.password;

    expect(passwordControl.errors?.['required']).toBeTruthy();

    passwordControl.setValue('password123');
    expect(passwordControl.errors).toBeNull();
  });

  it('should emit submit with form values', () => {
    const submitSpy = jest.fn();
    component.submitted.subscribe(submitSpy);

    component.form.patchValue({
      email: 'test@example.com',
      password: 'password123',
    });

    const form = fixture.nativeElement.querySelector('form');
    form.dispatchEvent(new Event('submit'));

    expect(submitSpy).toHaveBeenCalledWith({
      email: 'test@example.com',
      password: 'password123',
    });
  });

  it('should show validation errors after touch', () => {
    const emailInput = fixture.nativeElement.querySelector('#email');
    emailInput.dispatchEvent(new Event('blur'));
    fixture.detectChanges();

    const errorMessage = fixture.nativeElement.querySelector('.error');
    expect(errorMessage.textContent).toContain('required');
  });
});
```

## Async Testing

```typescript
import { ComponentFixture, TestBed, fakeAsync, tick, waitForAsync } from '@angular/core/testing';
import { of, delay } from 'rxjs';
import { DataComponent } from './data.component';
import { DataService } from '../../services/data.service';

describe('DataComponent async', () => {
  let fixture: ComponentFixture<DataComponent>;
  let dataService: jest.Mocked<DataService>;

  beforeEach(async () => {
    dataService = {
      getData: jest.fn(),
    } as any;

    await TestBed.configureTestingModule({
      imports: [DataComponent],
      providers: [{ provide: DataService, useValue: dataService }],
    }).compileComponents();

    fixture = TestBed.createComponent(DataComponent);
  });

  it('should load data with fakeAsync', fakeAsync(() => {
    dataService.getData.mockReturnValue(of({ name: 'Test' }).pipe(delay(1000)));

    fixture.detectChanges();
    expect(fixture.componentInstance.isLoading()).toBeTrue();

    tick(1000);
    fixture.detectChanges();

    expect(fixture.componentInstance.isLoading()).toBeFalse();
    expect(fixture.componentInstance.data()).toEqual({ name: 'Test' });
  }));

  it('should load data with waitForAsync', waitForAsync(() => {
    dataService.getData.mockReturnValue(of({ name: 'Test' }));

    fixture.detectChanges();

    fixture.whenStable().then(() => {
      fixture.detectChanges();
      expect(fixture.componentInstance.data()).toEqual({ name: 'Test' });
    });
  }));
});
```

## NgRx SignalStore Testing

```typescript
import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { UserStore } from './user.store';

describe('UserStore', () => {
  let store: InstanceType<typeof UserStore>;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        UserStore,
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });

    store = TestBed.inject(UserStore);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should have initial state', () => {
    expect(store.entities()).toEqual([]);
    expect(store.isLoading()).toBeFalse();
    expect(store.error()).toBeNull();
  });

  it('should load users', () => {
    const users = [{ id: '1', name: 'John' }];

    store.loadAll();

    const req = httpMock.expectOne('/api/users');
    req.flush(users);

    expect(store.entities()).toEqual(users);
    expect(store.isLoading()).toBeFalse();
  });

  it('should handle load error', () => {
    store.loadAll();

    const req = httpMock.expectOne('/api/users');
    req.flush('Error', { status: 500, statusText: 'Server Error' });

    expect(store.error()).toBeTruthy();
    expect(store.entities()).toEqual([]);
  });

  it('should select user', () => {
    store.loadAll();
    httpMock.expectOne('/api/users').flush([{ id: '1', name: 'John' }]);

    store.select('1');

    expect(store.selectedItem()).toEqual({ id: '1', name: 'John' });
  });

  it('should filter users', () => {
    store.loadAll();
    httpMock.expectOne('/api/users').flush([
      { id: '1', name: 'John' },
      { id: '2', name: 'Jane' },
    ]);

    store.setFilter('ja');

    expect(store.filteredItems()).toEqual([{ id: '2', name: 'Jane' }]);
  });
});
```

## E2E Test Template (Playwright)

```typescript
// e2e/{{name}}.spec.ts
import { test, expect } from '@playwright/test';

test.describe('{{PascalName}} Feature', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/{{route}}');
  });

  test('should display page title', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('{{Title}}');
  });

  test('should load data', async ({ page }) => {
    await expect(page.locator('.data-list')).toBeVisible();
    await expect(page.locator('.list-item')).toHaveCount(10);
  });

  test('should filter items', async ({ page }) => {
    await page.fill('[data-testid="search-input"]', 'test');
    await expect(page.locator('.list-item')).toHaveCount(2);
  });

  test('should navigate to detail', async ({ page }) => {
    await page.click('.list-item:first-child');
    await expect(page).toHaveURL(/\/{{route}}\/\d+/);
  });
});
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{name}}` | kebab-case name | `user-list` |
| `{{PascalName}}` | PascalCase name | `UserList` |
| `{{feature}}` | Feature folder | `users` |
| `{{route}}` | Route path | `users` |
| `{{Title}}` | Page title | `User List` |
