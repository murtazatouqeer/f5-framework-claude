# Angular HTTP Interceptors

## Overview

Interceptors allow you to intercept HTTP requests and responses to transform, log, cache, or handle errors globally. Angular 17+ uses functional interceptors.

## Setup

```typescript
// app.config.ts
import { ApplicationConfig } from '@angular/core';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { authInterceptor } from './core/interceptors/auth.interceptor';
import { loggingInterceptor } from './core/interceptors/logging.interceptor';
import { errorInterceptor } from './core/interceptors/error.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    provideHttpClient(
      withInterceptors([
        authInterceptor,
        loggingInterceptor,
        errorInterceptor,
      ]),
    ),
  ],
};
```

## Functional Interceptors

### Basic Interceptor

```typescript
// core/interceptors/logging.interceptor.ts
import { HttpInterceptorFn } from '@angular/common/http';
import { tap } from 'rxjs';

export const loggingInterceptor: HttpInterceptorFn = (req, next) => {
  const started = Date.now();

  return next(req).pipe(
    tap({
      next: (event) => {
        if (event.type === HttpEventType.Response) {
          const elapsed = Date.now() - started;
          console.log(`${req.method} ${req.url} - ${elapsed}ms`);
        }
      },
      error: (error) => {
        const elapsed = Date.now() - started;
        console.error(`${req.method} ${req.url} failed after ${elapsed}ms`, error);
      },
    }),
  );
};
```

### Authentication Interceptor

```typescript
// core/interceptors/auth.interceptor.ts
import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, switchMap, throwError } from 'rxjs';
import { AuthService } from '../services/auth.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);

  // Skip auth for certain URLs
  if (req.url.includes('/auth/login') || req.url.includes('/auth/refresh')) {
    return next(req);
  }

  const token = authService.getAccessToken();

  if (token) {
    req = req.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`,
      },
    });
  }

  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      if (error.status === 401) {
        // Token expired, try to refresh
        return authService.refreshToken().pipe(
          switchMap(newToken => {
            const newReq = req.clone({
              setHeaders: {
                Authorization: `Bearer ${newToken}`,
              },
            });
            return next(newReq);
          }),
          catchError(refreshError => {
            // Refresh failed, logout
            authService.logout();
            return throwError(() => refreshError);
          }),
        );
      }
      return throwError(() => error);
    }),
  );
};
```

### Error Handling Interceptor

```typescript
// core/interceptors/error.interceptor.ts
import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, throwError } from 'rxjs';
import { NotificationService } from '../services/notification.service';
import { Router } from '@angular/router';

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const notificationService = inject(NotificationService);
  const router = inject(Router);

  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      let errorMessage = 'An error occurred';

      if (error.error instanceof ErrorEvent) {
        // Client-side error
        errorMessage = `Error: ${error.error.message}`;
      } else {
        // Server-side error
        switch (error.status) {
          case 400:
            errorMessage = error.error?.message || 'Bad request';
            break;
          case 401:
            errorMessage = 'Unauthorized. Please log in again.';
            router.navigate(['/login']);
            break;
          case 403:
            errorMessage = 'You do not have permission to access this resource';
            router.navigate(['/forbidden']);
            break;
          case 404:
            errorMessage = 'Resource not found';
            break;
          case 422:
            errorMessage = 'Validation error';
            break;
          case 500:
            errorMessage = 'Internal server error. Please try again later.';
            break;
          case 503:
            errorMessage = 'Service unavailable. Please try again later.';
            break;
          default:
            errorMessage = `Error Code: ${error.status}`;
        }
      }

      notificationService.showError(errorMessage);

      return throwError(() => ({
        status: error.status,
        message: errorMessage,
        originalError: error,
      }));
    }),
  );
};
```

### Loading Interceptor

```typescript
// core/interceptors/loading.interceptor.ts
import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { finalize } from 'rxjs';
import { LoadingService } from '../services/loading.service';

export const loadingInterceptor: HttpInterceptorFn = (req, next) => {
  const loadingService = inject(LoadingService);

  // Skip loading for certain requests
  if (req.headers.has('X-Skip-Loading')) {
    const newReq = req.clone({
      headers: req.headers.delete('X-Skip-Loading'),
    });
    return next(newReq);
  }

  loadingService.show();

  return next(req).pipe(
    finalize(() => loadingService.hide()),
  );
};

// Loading service
@Injectable({ providedIn: 'root' })
export class LoadingService {
  private activeRequests = signal(0);

  isLoading = computed(() => this.activeRequests() > 0);

  show() {
    this.activeRequests.update(count => count + 1);
  }

  hide() {
    this.activeRequests.update(count => Math.max(0, count - 1));
  }
}
```

### Caching Interceptor

```typescript
// core/interceptors/cache.interceptor.ts
import { HttpInterceptorFn, HttpResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { of, tap } from 'rxjs';
import { CacheService } from '../services/cache.service';

export const cacheInterceptor: HttpInterceptorFn = (req, next) => {
  const cacheService = inject(CacheService);

  // Only cache GET requests
  if (req.method !== 'GET') {
    return next(req);
  }

  // Check for no-cache header
  if (req.headers.has('X-No-Cache')) {
    const newReq = req.clone({
      headers: req.headers.delete('X-No-Cache'),
    });
    return next(newReq);
  }

  const cachedResponse = cacheService.get(req.url);

  if (cachedResponse) {
    return of(cachedResponse);
  }

  return next(req).pipe(
    tap(event => {
      if (event instanceof HttpResponse) {
        cacheService.set(req.url, event);
      }
    }),
  );
};

// Cache service
@Injectable({ providedIn: 'root' })
export class CacheService {
  private cache = new Map<string, { response: HttpResponse<any>; timestamp: number }>();
  private ttl = 5 * 60 * 1000; // 5 minutes

  get(url: string): HttpResponse<any> | null {
    const cached = this.cache.get(url);

    if (cached) {
      const isExpired = Date.now() - cached.timestamp > this.ttl;
      if (!isExpired) {
        return cached.response.clone();
      }
      this.cache.delete(url);
    }

    return null;
  }

  set(url: string, response: HttpResponse<any>): void {
    this.cache.set(url, {
      response: response.clone(),
      timestamp: Date.now(),
    });
  }

  invalidate(url?: string): void {
    if (url) {
      this.cache.delete(url);
    } else {
      this.cache.clear();
    }
  }
}
```

### Retry Interceptor

```typescript
// core/interceptors/retry.interceptor.ts
import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { retry, timer } from 'rxjs';

export const retryInterceptor: HttpInterceptorFn = (req, next) => {
  // Only retry GET requests
  if (req.method !== 'GET') {
    return next(req);
  }

  return next(req).pipe(
    retry({
      count: 3,
      delay: (error: HttpErrorResponse, retryCount: number) => {
        // Only retry on network errors or 5xx
        if (error.status === 0 || error.status >= 500) {
          const delayMs = Math.pow(2, retryCount) * 1000; // Exponential backoff
          console.log(`Retrying request to ${req.url} in ${delayMs}ms (attempt ${retryCount})`);
          return timer(delayMs);
        }
        throw error;
      },
    }),
  );
};
```

### Request Transform Interceptor

```typescript
// core/interceptors/transform.interceptor.ts
import { HttpInterceptorFn } from '@angular/common/http';
import { map } from 'rxjs';

export const transformInterceptor: HttpInterceptorFn = (req, next) => {
  // Add timestamp to all requests
  const modifiedReq = req.clone({
    setHeaders: {
      'X-Request-Timestamp': new Date().toISOString(),
    },
  });

  return next(modifiedReq).pipe(
    map(event => {
      if (event instanceof HttpResponse && event.body) {
        // Transform response (e.g., unwrap data property)
        if (event.body.data) {
          return event.clone({ body: event.body.data });
        }
      }
      return event;
    }),
  );
};
```

### Content Type Interceptor

```typescript
// core/interceptors/content-type.interceptor.ts
import { HttpInterceptorFn } from '@angular/common/http';

export const contentTypeInterceptor: HttpInterceptorFn = (req, next) => {
  // Skip if content type is already set or it's a FormData request
  if (req.headers.has('Content-Type') || req.body instanceof FormData) {
    return next(req);
  }

  // Add JSON content type for requests with body
  if (req.body !== null && req.body !== undefined) {
    const modifiedReq = req.clone({
      setHeaders: {
        'Content-Type': 'application/json',
      },
    });
    return next(modifiedReq);
  }

  return next(req);
};
```

### API Versioning Interceptor

```typescript
// core/interceptors/api-version.interceptor.ts
import { HttpInterceptorFn } from '@angular/common/http';
import { environment } from '../../../environments/environment';

export const apiVersionInterceptor: HttpInterceptorFn = (req, next) => {
  // Only modify API requests
  if (!req.url.startsWith('/api') && !req.url.includes(environment.apiUrl)) {
    return next(req);
  }

  const modifiedReq = req.clone({
    setHeaders: {
      'Accept': 'application/json',
      'X-API-Version': '2.0',
    },
  });

  return next(modifiedReq);
};
```

### Base URL Interceptor

```typescript
// core/interceptors/base-url.interceptor.ts
import { HttpInterceptorFn } from '@angular/common/http';
import { environment } from '../../../environments/environment';

export const baseUrlInterceptor: HttpInterceptorFn = (req, next) => {
  // Skip absolute URLs
  if (req.url.startsWith('http://') || req.url.startsWith('https://')) {
    return next(req);
  }

  // Prepend base URL
  const modifiedReq = req.clone({
    url: `${environment.apiUrl}${req.url}`,
  });

  return next(modifiedReq);
};
```

## Interceptor Order

Interceptors execute in order for requests and reverse order for responses:

```typescript
// Request flow: auth → logging → error → cache
// Response flow: cache → error → logging → auth

provideHttpClient(
  withInterceptors([
    authInterceptor,      // 1st request, 4th response
    loggingInterceptor,   // 2nd request, 3rd response
    errorInterceptor,     // 3rd request, 2nd response
    cacheInterceptor,     // 4th request, 1st response
  ]),
)
```

## Conditional Interceptors

```typescript
// Using withInterceptorsFromDi for conditional interceptors
import { HTTP_INTERCEPTORS } from '@angular/common/http';

@Injectable()
export class ConditionalInterceptor implements HttpInterceptor {
  intercept(req: HttpRequest<any>, next: HttpHandler) {
    // Logic here
    return next.handle(req);
  }
}

// In providers
{
  provide: HTTP_INTERCEPTORS,
  useClass: ConditionalInterceptor,
  multi: true,
}
```

## Testing Interceptors

```typescript
import { TestBed } from '@angular/core/testing';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient, withInterceptors, HttpClient } from '@angular/common/http';

describe('authInterceptor', () => {
  let httpClient: HttpClient;
  let httpTesting: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
        { provide: AuthService, useValue: { getAccessToken: () => 'test-token' } },
      ],
    });

    httpClient = TestBed.inject(HttpClient);
    httpTesting = TestBed.inject(HttpTestingController);
  });

  it('should add authorization header', () => {
    httpClient.get('/api/data').subscribe();

    const req = httpTesting.expectOne('/api/data');
    expect(req.request.headers.get('Authorization')).toBe('Bearer test-token');

    req.flush({ data: 'test' });
  });

  afterEach(() => {
    httpTesting.verify();
  });
});
```

## Best Practices

1. **Order matters**: Place auth interceptor first, error handling last
2. **Keep focused**: Each interceptor should do one thing
3. **Handle errors properly**: Don't swallow errors silently
4. **Clone requests**: Always clone before modifying
5. **Consider performance**: Caching and retry logic affects UX
6. **Test thoroughly**: Interceptors affect all HTTP calls
7. **Use injection**: Inject services with inject() in functional interceptors
