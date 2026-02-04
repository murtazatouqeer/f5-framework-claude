# Angular Unit Testing

## Overview

Angular uses Jasmine as the default testing framework and Karma as the test runner. Tests are typically located alongside source files with `.spec.ts` extension.

## Test Configuration

```typescript
// angular.json (test configuration)
{
  "test": {
    "builder": "@angular-devkit/build-angular:karma",
    "options": {
      "main": "src/test.ts",
      "polyfills": "src/polyfills.ts",
      "tsConfig": "tsconfig.spec.json",
      "karmaConfig": "karma.conf.js",
      "codeCoverage": true,
      "codeCoverageExclude": [
        "src/test.ts",
        "src/**/*.spec.ts"
      ]
    }
  }
}
```

## Testing Services

### Basic Service Test

```typescript
// services/calculator.service.spec.ts
import { TestBed } from '@angular/core/testing';
import { CalculatorService } from './calculator.service';

describe('CalculatorService', () => {
  let service: CalculatorService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(CalculatorService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should add two numbers', () => {
    expect(service.add(2, 3)).toBe(5);
  });

  it('should subtract two numbers', () => {
    expect(service.subtract(5, 3)).toBe(2);
  });

  it('should multiply two numbers', () => {
    expect(service.multiply(4, 3)).toBe(12);
  });

  it('should throw error on division by zero', () => {
    expect(() => service.divide(10, 0)).toThrowError('Cannot divide by zero');
  });
});
```

### Service with Dependencies

```typescript
// services/user.service.spec.ts
import { TestBed } from '@angular/core/testing';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { UserService } from './user.service';

describe('UserService', () => {
  let service: UserService;
  let httpTesting: HttpTestingController;

  const mockUsers = [
    { id: 1, name: 'Alice', email: 'alice@example.com' },
    { id: 2, name: 'Bob', email: 'bob@example.com' },
  ];

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });

    service = TestBed.inject(UserService);
    httpTesting = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTesting.verify(); // Verify no outstanding requests
  });

  it('should fetch all users', () => {
    service.getAll().subscribe(users => {
      expect(users).toEqual(mockUsers);
      expect(users.length).toBe(2);
    });

    const req = httpTesting.expectOne('/api/users');
    expect(req.request.method).toBe('GET');
    req.flush(mockUsers);
  });

  it('should fetch user by id', () => {
    service.getById(1).subscribe(user => {
      expect(user).toEqual(mockUsers[0]);
    });

    const req = httpTesting.expectOne('/api/users/1');
    expect(req.request.method).toBe('GET');
    req.flush(mockUsers[0]);
  });

  it('should create user', () => {
    const newUser = { name: 'Charlie', email: 'charlie@example.com' };
    const createdUser = { id: 3, ...newUser };

    service.create(newUser).subscribe(user => {
      expect(user).toEqual(createdUser);
    });

    const req = httpTesting.expectOne('/api/users');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(newUser);
    req.flush(createdUser);
  });

  it('should handle error response', () => {
    service.getById(999).subscribe({
      next: () => fail('should have failed'),
      error: error => {
        expect(error.status).toBe(404);
      },
    });

    const req = httpTesting.expectOne('/api/users/999');
    req.flush('Not Found', { status: 404, statusText: 'Not Found' });
  });
});
```

### Service with Signal State

```typescript
// services/counter.service.spec.ts
import { TestBed } from '@angular/core/testing';
import { CounterService } from './counter.service';

describe('CounterService', () => {
  let service: CounterService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(CounterService);
  });

  it('should have initial count of 0', () => {
    expect(service.count()).toBe(0);
  });

  it('should increment count', () => {
    service.increment();
    expect(service.count()).toBe(1);

    service.increment();
    expect(service.count()).toBe(2);
  });

  it('should decrement count', () => {
    service.increment();
    service.increment();
    service.decrement();
    expect(service.count()).toBe(1);
  });

  it('should reset count', () => {
    service.increment();
    service.increment();
    service.reset();
    expect(service.count()).toBe(0);
  });

  it('should compute double count', () => {
    service.increment();
    service.increment();
    expect(service.doubleCount()).toBe(4);
  });
});
```

## Testing Pipes

```typescript
// pipes/truncate.pipe.spec.ts
import { TruncatePipe } from './truncate.pipe';

describe('TruncatePipe', () => {
  let pipe: TruncatePipe;

  beforeEach(() => {
    pipe = new TruncatePipe();
  });

  it('should create', () => {
    expect(pipe).toBeTruthy();
  });

  it('should return original string if shorter than limit', () => {
    expect(pipe.transform('Hello', 10)).toBe('Hello');
  });

  it('should truncate string longer than limit', () => {
    expect(pipe.transform('Hello World', 5)).toBe('Hello...');
  });

  it('should use custom suffix', () => {
    expect(pipe.transform('Hello World', 5, '---')).toBe('Hello---');
  });

  it('should handle null value', () => {
    expect(pipe.transform(null as any, 10)).toBe('');
  });

  it('should handle empty string', () => {
    expect(pipe.transform('', 10)).toBe('');
  });
});
```

## Testing Guards

```typescript
// guards/auth.guard.spec.ts
import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { authGuard } from './auth.guard';
import { AuthService } from '../services/auth.service';

describe('authGuard', () => {
  let authService: jasmine.SpyObj<AuthService>;
  let router: jasmine.SpyObj<Router>;

  beforeEach(() => {
    authService = jasmine.createSpyObj('AuthService', ['isAuthenticated']);
    router = jasmine.createSpyObj('Router', ['createUrlTree']);

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
      authGuard({} as any, { url: '/dashboard' } as any)
    );

    expect(result).toBe(true);
  });

  it('should redirect to login when not authenticated', () => {
    authService.isAuthenticated.and.returnValue(false);
    const urlTree = {} as any;
    router.createUrlTree.and.returnValue(urlTree);

    const result = TestBed.runInInjectionContext(() =>
      authGuard({} as any, { url: '/dashboard' } as any)
    );

    expect(result).toBe(urlTree);
    expect(router.createUrlTree).toHaveBeenCalledWith(
      ['/auth/login'],
      { queryParams: { returnUrl: '/dashboard' } }
    );
  });
});
```

## Testing Interceptors

```typescript
// interceptors/auth.interceptor.spec.ts
import { TestBed } from '@angular/core/testing';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient, withInterceptors, HttpClient } from '@angular/common/http';
import { authInterceptor } from './auth.interceptor';
import { AuthService } from '../services/auth.service';

describe('authInterceptor', () => {
  let httpClient: HttpClient;
  let httpTesting: HttpTestingController;
  let authService: jasmine.SpyObj<AuthService>;

  beforeEach(() => {
    authService = jasmine.createSpyObj('AuthService', ['getAccessToken']);

    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
        { provide: AuthService, useValue: authService },
      ],
    });

    httpClient = TestBed.inject(HttpClient);
    httpTesting = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTesting.verify();
  });

  it('should add authorization header when token exists', () => {
    authService.getAccessToken.and.returnValue('test-token');

    httpClient.get('/api/data').subscribe();

    const req = httpTesting.expectOne('/api/data');
    expect(req.request.headers.get('Authorization')).toBe('Bearer test-token');
    req.flush({});
  });

  it('should not add authorization header when no token', () => {
    authService.getAccessToken.and.returnValue(null);

    httpClient.get('/api/data').subscribe();

    const req = httpTesting.expectOne('/api/data');
    expect(req.request.headers.has('Authorization')).toBe(false);
    req.flush({});
  });

  it('should skip auth for login endpoint', () => {
    authService.getAccessToken.and.returnValue('test-token');

    httpClient.post('/auth/login', {}).subscribe();

    const req = httpTesting.expectOne('/auth/login');
    expect(req.request.headers.has('Authorization')).toBe(false);
    req.flush({});
  });
});
```

## Mocking and Spies

### Creating Spies

```typescript
// Creating spy objects
const userService = jasmine.createSpyObj('UserService', ['getAll', 'getById', 'create']);

// Setting return values
userService.getAll.and.returnValue(of(mockUsers));
userService.getById.and.returnValue(of(mockUser));
userService.create.and.returnValue(of(newUser));

// Setting return values for different calls
userService.getById.and.returnValues(of(user1), of(user2));

// Throwing errors
userService.getById.and.throwError('Error');
userService.getById.and.returnValue(throwError(() => new Error('Not found')));

// Checking calls
expect(userService.getAll).toHaveBeenCalled();
expect(userService.getById).toHaveBeenCalledWith(1);
expect(userService.create).toHaveBeenCalledTimes(2);
```

### Spying on Methods

```typescript
// Spy on existing service method
const service = TestBed.inject(UserService);
spyOn(service, 'getAll').and.returnValue(of(mockUsers));

// Spy and call through
spyOn(service, 'processData').and.callThrough();

// Spy and call fake
spyOn(service, 'calculate').and.callFake((a, b) => a * b);
```

## Async Testing

### fakeAsync and tick

```typescript
import { fakeAsync, tick, flush } from '@angular/core/testing';

it('should debounce search', fakeAsync(() => {
  const searchService = TestBed.inject(SearchService);
  spyOn(searchService, 'search').and.returnValue(of([]));

  component.onSearchInput('test');
  expect(searchService.search).not.toHaveBeenCalled();

  tick(300); // Advance time by debounce delay
  expect(searchService.search).toHaveBeenCalledWith('test');
}));

it('should handle multiple async operations', fakeAsync(() => {
  component.loadData();

  tick(1000); // Wait for first operation
  tick(500);  // Wait for second operation

  // Or flush all pending async operations
  flush();

  expect(component.data()).toBeTruthy();
}));
```

### waitForAsync

```typescript
import { waitForAsync } from '@angular/core/testing';

it('should load data on init', waitForAsync(() => {
  const service = TestBed.inject(DataService);
  spyOn(service, 'getData').and.returnValue(
    of(mockData).pipe(delay(100))
  );

  component.ngOnInit();

  fixture.whenStable().then(() => {
    expect(component.data()).toEqual(mockData);
  });
}));
```

### done Callback

```typescript
it('should emit value', (done) => {
  service.getData().subscribe(data => {
    expect(data).toBeTruthy();
    done();
  });
});
```

## Test Utilities

### Custom Matchers

```typescript
// test/custom-matchers.ts
beforeEach(() => {
  jasmine.addMatchers({
    toBeValidEmail: () => ({
      compare: (actual: string) => {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        const pass = emailRegex.test(actual);
        return {
          pass,
          message: pass
            ? `Expected ${actual} not to be a valid email`
            : `Expected ${actual} to be a valid email`,
        };
      },
    }),
  });
});

// Usage
expect('test@example.com').toBeValidEmail();
```

### Test Data Builders

```typescript
// test/builders/user.builder.ts
export class UserBuilder {
  private user: User = {
    id: 1,
    name: 'Default Name',
    email: 'default@example.com',
    role: 'user',
  };

  withId(id: number): UserBuilder {
    this.user.id = id;
    return this;
  }

  withName(name: string): UserBuilder {
    this.user.name = name;
    return this;
  }

  withEmail(email: string): UserBuilder {
    this.user.email = email;
    return this;
  }

  withRole(role: string): UserBuilder {
    this.user.role = role;
    return this;
  }

  build(): User {
    return { ...this.user };
  }

  static aUser(): UserBuilder {
    return new UserBuilder();
  }
}

// Usage
const user = UserBuilder.aUser()
  .withName('John')
  .withRole('admin')
  .build();
```

## Best Practices

1. **Test behavior, not implementation**: Focus on what code does, not how
2. **Use descriptive test names**: Describe expected behavior clearly
3. **Follow AAA pattern**: Arrange, Act, Assert
4. **Isolate tests**: Each test should be independent
5. **Mock dependencies**: Don't test dependencies, mock them
6. **Test edge cases**: Empty arrays, null values, errors
7. **Keep tests fast**: Mock HTTP calls, use fakeAsync
8. **Maintain test coverage**: Aim for 80%+ coverage
