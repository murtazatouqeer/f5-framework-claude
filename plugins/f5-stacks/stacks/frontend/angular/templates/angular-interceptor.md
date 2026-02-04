# Angular Interceptor Template

## Authentication Interceptor

```typescript
// core/interceptors/auth.interceptor.ts
import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, switchMap, throwError } from 'rxjs';
import { AuthService } from '../services/auth.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);

  // Skip auth for certain URLs
  const skipUrls = ['/auth/login', '/auth/register', '/auth/refresh'];
  if (skipUrls.some(url => req.url.includes(url))) {
    return next(req);
  }

  // Add token if available
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
        // Attempt token refresh
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

## Error Handling Interceptor

```typescript
// core/interceptors/error.interceptor.ts
import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, throwError } from 'rxjs';
import { Router } from '@angular/router';
import { NotificationService } from '../services/notification.service';
import { LoggingService } from '../services/logging.service';

export interface ApiError {
  status: number;
  code: string;
  message: string;
  details?: Record<string, string[]>;
}

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const router = inject(Router);
  const notificationService = inject(NotificationService);
  const loggingService = inject(LoggingService);

  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      const apiError = parseError(error);

      // Log error
      loggingService.logError({
        type: 'HTTP',
        url: req.url,
        method: req.method,
        status: error.status,
        message: apiError.message,
      });

      // Handle specific status codes
      switch (error.status) {
        case 401:
          notificationService.showError('Session expired. Please log in again.');
          router.navigate(['/auth/login']);
          break;
        case 403:
          notificationService.showError('You do not have permission to access this resource.');
          router.navigate(['/forbidden']);
          break;
        case 404:
          notificationService.showError('The requested resource was not found.');
          break;
        case 422:
          // Validation errors - don't show generic message
          break;
        case 500:
        case 502:
        case 503:
          notificationService.showError('Server error. Please try again later.');
          break;
        default:
          if (error.status === 0) {
            notificationService.showError('Network error. Please check your connection.');
          } else {
            notificationService.showError(apiError.message);
          }
      }

      return throwError(() => apiError);
    }),
  );
};

function parseError(error: HttpErrorResponse): ApiError {
  return {
    status: error.status,
    code: error.error?.code || 'UNKNOWN_ERROR',
    message: error.error?.message || getDefaultMessage(error.status),
    details: error.error?.details,
  };
}

function getDefaultMessage(status: number): string {
  const messages: Record<number, string> = {
    0: 'Network error',
    400: 'Bad request',
    401: 'Unauthorized',
    403: 'Forbidden',
    404: 'Not found',
    422: 'Validation error',
    500: 'Internal server error',
  };
  return messages[status] || 'An error occurred';
}
```

## Loading Interceptor

```typescript
// core/interceptors/loading.interceptor.ts
import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { finalize } from 'rxjs';
import { LoadingService } from '../services/loading.service';

export const loadingInterceptor: HttpInterceptorFn = (req, next) => {
  const loadingService = inject(LoadingService);

  // Skip loading for specific requests
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
```

## Caching Interceptor

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

  // Skip cache if header is present
  if (req.headers.has('X-No-Cache')) {
    const newReq = req.clone({
      headers: req.headers.delete('X-No-Cache'),
    });
    return next(newReq);
  }

  // Check cache
  const cachedResponse = cacheService.get(req.url);
  if (cachedResponse) {
    return of(cachedResponse);
  }

  // Make request and cache response
  return next(req).pipe(
    tap(event => {
      if (event instanceof HttpResponse) {
        cacheService.set(req.url, event);
      }
    }),
  );
};
```

## Retry Interceptor

```typescript
// core/interceptors/retry.interceptor.ts
import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { retry, timer, throwError } from 'rxjs';

export const retryInterceptor: HttpInterceptorFn = (req, next) => {
  // Only retry GET requests and idempotent operations
  const retryableMethods = ['GET', 'HEAD', 'OPTIONS'];

  if (!retryableMethods.includes(req.method)) {
    return next(req);
  }

  return next(req).pipe(
    retry({
      count: 3,
      delay: (error: HttpErrorResponse, retryCount: number) => {
        // Only retry on network errors or 5xx
        if (error.status === 0 || error.status >= 500) {
          const delayMs = Math.min(1000 * Math.pow(2, retryCount - 1), 10000);
          console.log(`Retrying ${req.url} in ${delayMs}ms (attempt ${retryCount})`);
          return timer(delayMs);
        }
        return throwError(() => error);
      },
    }),
  );
};
```

## Logging Interceptor

```typescript
// core/interceptors/logging.interceptor.ts
import { HttpInterceptorFn, HttpResponse, HttpErrorResponse } from '@angular/common/http';
import { tap, catchError, throwError } from 'rxjs';
import { environment } from '../../../environments/environment';

export const loggingInterceptor: HttpInterceptorFn = (req, next) => {
  if (environment.production) {
    return next(req);
  }

  const started = Date.now();
  const requestId = Math.random().toString(36).substring(7);

  console.log(`[${requestId}] ${req.method} ${req.url}`);

  return next(req).pipe(
    tap(event => {
      if (event instanceof HttpResponse) {
        const elapsed = Date.now() - started;
        console.log(`[${requestId}] ${req.method} ${req.url} - ${event.status} (${elapsed}ms)`);
      }
    }),
    catchError((error: HttpErrorResponse) => {
      const elapsed = Date.now() - started;
      console.error(`[${requestId}] ${req.method} ${req.url} - ${error.status} (${elapsed}ms)`, error);
      return throwError(() => error);
    }),
  );
};
```

## Base URL Interceptor

```typescript
// core/interceptors/base-url.interceptor.ts
import { HttpInterceptorFn } from '@angular/common/http';
import { environment } from '../../../environments/environment';

export const baseUrlInterceptor: HttpInterceptorFn = (req, next) => {
  // Skip absolute URLs
  if (req.url.startsWith('http://') || req.url.startsWith('https://')) {
    return next(req);
  }

  // Prepend API base URL
  const modifiedReq = req.clone({
    url: `${environment.apiUrl}${req.url}`,
  });

  return next(modifiedReq);
};
```

## Headers Interceptor

```typescript
// core/interceptors/headers.interceptor.ts
import { HttpInterceptorFn } from '@angular/common/http';

export const headersInterceptor: HttpInterceptorFn = (req, next) => {
  // Skip if Content-Type is already set (e.g., multipart/form-data)
  if (req.headers.has('Content-Type')) {
    return next(req);
  }

  // Skip for FormData (file uploads)
  if (req.body instanceof FormData) {
    return next(req);
  }

  // Add default headers
  const modifiedReq = req.clone({
    setHeaders: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'X-Requested-With': 'XMLHttpRequest',
    },
  });

  return next(modifiedReq);
};
```

## App Configuration

```typescript
// app.config.ts
import { ApplicationConfig } from '@angular/core';
import { provideHttpClient, withInterceptors } from '@angular/common/http';

import { baseUrlInterceptor } from './core/interceptors/base-url.interceptor';
import { headersInterceptor } from './core/interceptors/headers.interceptor';
import { authInterceptor } from './core/interceptors/auth.interceptor';
import { loadingInterceptor } from './core/interceptors/loading.interceptor';
import { cacheInterceptor } from './core/interceptors/cache.interceptor';
import { retryInterceptor } from './core/interceptors/retry.interceptor';
import { loggingInterceptor } from './core/interceptors/logging.interceptor';
import { errorInterceptor } from './core/interceptors/error.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    provideHttpClient(
      withInterceptors([
        // Order matters: first in chain for request, last for response
        baseUrlInterceptor,
        headersInterceptor,
        authInterceptor,
        loadingInterceptor,
        cacheInterceptor,
        retryInterceptor,
        loggingInterceptor,
        errorInterceptor,
      ]),
    ),
  ],
};
```
