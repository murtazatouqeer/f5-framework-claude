# Angular HTTP Error Handling

## Overview

Proper error handling in HTTP requests ensures a good user experience and helps with debugging. This guide covers strategies for handling errors at service, component, and global levels.

## Error Types

```typescript
import { HttpErrorResponse } from '@angular/common/http';

// Client-side errors (network issues, browser errors)
if (error.error instanceof ErrorEvent) {
  console.error('Client error:', error.error.message);
}

// Server-side errors (HTTP status codes)
if (error instanceof HttpErrorResponse) {
  console.error('Server error:', error.status, error.message);
}
```

## Service-Level Error Handling

### Basic Error Handling

```typescript
import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError, catchError } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class UserService {
  private http = inject(HttpClient);

  getUser(id: number): Observable<User> {
    return this.http.get<User>(`/api/users/${id}`).pipe(
      catchError(this.handleError),
    );
  }

  private handleError(error: HttpErrorResponse): Observable<never> {
    let errorMessage: string;

    if (error.error instanceof ErrorEvent) {
      // Client-side error
      errorMessage = `Network error: ${error.error.message}`;
    } else {
      // Server-side error
      errorMessage = `Server error: ${error.status} - ${error.message}`;

      if (error.error?.message) {
        errorMessage = error.error.message;
      }
    }

    console.error('HTTP Error:', errorMessage);
    return throwError(() => new Error(errorMessage));
  }
}
```

### Typed Error Handling

```typescript
// models/api-error.model.ts
export interface ApiError {
  status: number;
  code: string;
  message: string;
  details?: Record<string, string[]>;
  timestamp?: string;
}

// services/user.service.ts
@Injectable({ providedIn: 'root' })
export class UserService {
  private http = inject(HttpClient);

  getUser(id: number): Observable<User> {
    return this.http.get<User>(`/api/users/${id}`).pipe(
      catchError((error: HttpErrorResponse) => {
        const apiError: ApiError = {
          status: error.status,
          code: error.error?.code || 'UNKNOWN_ERROR',
          message: error.error?.message || this.getDefaultMessage(error.status),
          details: error.error?.details,
          timestamp: new Date().toISOString(),
        };

        return throwError(() => apiError);
      }),
    );
  }

  private getDefaultMessage(status: number): string {
    const messages: Record<number, string> = {
      400: 'Bad request',
      401: 'Unauthorized',
      403: 'Forbidden',
      404: 'Not found',
      422: 'Validation error',
      500: 'Internal server error',
    };
    return messages[status] || 'An error occurred';
  }
}
```

### Retry with Error Handling

```typescript
import { retry, catchError, timer, throwError } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class ResilientService {
  private http = inject(HttpClient);

  getData(): Observable<Data> {
    return this.http.get<Data>('/api/data').pipe(
      retry({
        count: 3,
        delay: (error, retryCount) => {
          // Only retry on network errors or 5xx
          if (this.isRetryable(error)) {
            console.log(`Retry attempt ${retryCount}`);
            return timer(1000 * retryCount); // Exponential backoff
          }
          return throwError(() => error);
        },
      }),
      catchError(this.handleError),
    );
  }

  private isRetryable(error: HttpErrorResponse): boolean {
    return error.status === 0 || error.status >= 500;
  }

  private handleError(error: HttpErrorResponse): Observable<never> {
    return throwError(() => ({
      message: 'Request failed after multiple attempts',
      originalError: error,
    }));
  }
}
```

## Component-Level Error Handling

### With Signals

```typescript
@Component({
  template: `
    @if (isLoading()) {
      <div class="loading">Loading...</div>
    }

    @if (error(); as err) {
      <div class="error-card">
        <h3>{{ err.message }}</h3>
        @if (err.details) {
          <ul>
            @for (detail of err.details | keyvalue; track detail.key) {
              <li>{{ detail.key }}: {{ detail.value }}</li>
            }
          </ul>
        }
        <button (click)="retry()">Try Again</button>
      </div>
    }

    @if (user(); as u) {
      <div class="user-card">
        <h2>{{ u.name }}</h2>
        <p>{{ u.email }}</p>
      </div>
    }
  `,
})
export class UserDetailComponent {
  private userService = inject(UserService);
  private route = inject(ActivatedRoute);

  user = signal<User | null>(null);
  error = signal<ApiError | null>(null);
  isLoading = signal(false);

  userId = input.required<string>();

  constructor() {
    effect(() => {
      this.loadUser(this.userId());
    });
  }

  loadUser(id: string) {
    this.isLoading.set(true);
    this.error.set(null);

    this.userService.getUser(Number(id)).subscribe({
      next: user => {
        this.user.set(user);
        this.isLoading.set(false);
      },
      error: (err: ApiError) => {
        this.error.set(err);
        this.isLoading.set(false);
      },
    });
  }

  retry() {
    this.loadUser(this.userId());
  }
}
```

### Error Boundary Component

```typescript
// shared/components/error-boundary.component.ts
@Component({
  selector: 'app-error-boundary',
  standalone: true,
  template: `
    @if (hasError()) {
      <div class="error-boundary">
        <h2>Something went wrong</h2>
        <p>{{ errorMessage() }}</p>
        <button (click)="reset()">Try Again</button>
      </div>
    } @else {
      <ng-content />
    }
  `,
})
export class ErrorBoundaryComponent {
  hasError = signal(false);
  errorMessage = signal('');

  private errorHandler = inject(ErrorHandler);

  handleError(error: any) {
    this.hasError.set(true);
    this.errorMessage.set(error?.message || 'An unexpected error occurred');
    this.errorHandler.handleError(error);
  }

  reset() {
    this.hasError.set(false);
    this.errorMessage.set('');
  }
}
```

## Global Error Handling

### Custom ErrorHandler

```typescript
// core/services/global-error-handler.service.ts
import { ErrorHandler, Injectable, inject, NgZone } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';

@Injectable()
export class GlobalErrorHandler implements ErrorHandler {
  private notificationService = inject(NotificationService);
  private loggingService = inject(LoggingService);
  private zone = inject(NgZone);

  handleError(error: Error | HttpErrorResponse): void {
    // Run inside NgZone to ensure change detection
    this.zone.run(() => {
      if (error instanceof HttpErrorResponse) {
        // HTTP errors are typically handled by interceptors
        this.handleHttpError(error);
      } else {
        // Runtime errors
        this.handleRuntimeError(error);
      }
    });
  }

  private handleHttpError(error: HttpErrorResponse): void {
    this.loggingService.logError({
      type: 'HTTP',
      status: error.status,
      message: error.message,
      url: error.url,
    });
  }

  private handleRuntimeError(error: Error): void {
    this.loggingService.logError({
      type: 'Runtime',
      message: error.message,
      stack: error.stack,
    });

    this.notificationService.showError(
      'An unexpected error occurred. Please try again.'
    );

    console.error('Runtime error:', error);
  }
}

// app.config.ts
export const appConfig: ApplicationConfig = {
  providers: [
    { provide: ErrorHandler, useClass: GlobalErrorHandler },
  ],
};
```

### Error Logging Service

```typescript
// core/services/logging.service.ts
@Injectable({ providedIn: 'root' })
export class LoggingService {
  private http = inject(HttpClient);
  private environment = inject(ENVIRONMENT);

  logError(error: LogEntry): void {
    const enrichedError = {
      ...error,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
      userId: this.getCurrentUserId(),
    };

    // Log to console in development
    if (!this.environment.production) {
      console.error('Logged error:', enrichedError);
    }

    // Send to error tracking service
    this.http.post('/api/logs/error', enrichedError, {
      headers: { 'X-Skip-Loading': 'true' },
    }).subscribe({
      error: () => {
        // Silently fail - don't create infinite loop
        console.error('Failed to send error log');
      },
    });
  }

  private getCurrentUserId(): string | null {
    // Get from auth service
    return null;
  }
}

interface LogEntry {
  type: string;
  message: string;
  status?: number;
  url?: string;
  stack?: string;
  [key: string]: any;
}
```

## Error Display Components

### Toast Notification Service

```typescript
// core/services/notification.service.ts
@Injectable({ providedIn: 'root' })
export class NotificationService {
  private notifications = signal<Notification[]>([]);

  readonly activeNotifications = this.notifications.asReadonly();

  showError(message: string, duration = 5000): void {
    this.show({ type: 'error', message, duration });
  }

  showWarning(message: string, duration = 4000): void {
    this.show({ type: 'warning', message, duration });
  }

  showSuccess(message: string, duration = 3000): void {
    this.show({ type: 'success', message, duration });
  }

  private show(notification: Omit<Notification, 'id'>): void {
    const id = crypto.randomUUID();
    const newNotification = { ...notification, id };

    this.notifications.update(list => [...list, newNotification]);

    setTimeout(() => {
      this.dismiss(id);
    }, notification.duration);
  }

  dismiss(id: string): void {
    this.notifications.update(list => list.filter(n => n.id !== id));
  }
}

interface Notification {
  id: string;
  type: 'error' | 'warning' | 'success' | 'info';
  message: string;
  duration: number;
}

// Toast container component
@Component({
  selector: 'app-toast-container',
  standalone: true,
  template: `
    <div class="toast-container">
      @for (notification of notificationService.activeNotifications(); track notification.id) {
        <div
          class="toast"
          [class]="notification.type"
          (click)="notificationService.dismiss(notification.id)"
        >
          <span class="icon">{{ getIcon(notification.type) }}</span>
          <span class="message">{{ notification.message }}</span>
          <button class="close">×</button>
        </div>
      }
    </div>
  `,
})
export class ToastContainerComponent {
  notificationService = inject(NotificationService);

  getIcon(type: string): string {
    const icons: Record<string, string> = {
      error: '❌',
      warning: '⚠️',
      success: '✅',
      info: 'ℹ️',
    };
    return icons[type] || '';
  }
}
```

### Inline Error Display

```typescript
@Component({
  selector: 'app-error-display',
  standalone: true,
  template: `
    @if (error()) {
      <div class="error-display" [class]="variant()">
        <div class="error-icon">
          @switch (error()!.status) {
            @case (404) { 🔍 }
            @case (403) { 🔒 }
            @case (500) { 💥 }
            @default { ⚠️ }
          }
        </div>

        <div class="error-content">
          <h3>{{ getTitle() }}</h3>
          <p>{{ error()!.message }}</p>

          @if (error()!.details) {
            <ul class="error-details">
              @for (item of error()!.details | keyvalue; track item.key) {
                <li>
                  <strong>{{ item.key }}:</strong>
                  @for (msg of item.value; track msg) {
                    <span>{{ msg }}</span>
                  }
                </li>
              }
            </ul>
          }
        </div>

        @if (retryable()) {
          <button class="retry-button" (click)="onRetry.emit()">
            Try Again
          </button>
        }
      </div>
    }
  `,
})
export class ErrorDisplayComponent {
  error = input<ApiError | null>(null);
  variant = input<'inline' | 'card' | 'fullpage'>('card');
  retryable = input(true);
  onRetry = output<void>();

  getTitle(): string {
    const titles: Record<number, string> = {
      400: 'Invalid Request',
      401: 'Authentication Required',
      403: 'Access Denied',
      404: 'Not Found',
      422: 'Validation Error',
      500: 'Server Error',
    };
    return titles[this.error()?.status || 0] || 'Error';
  }
}
```

## HTTP Error Patterns

### Empty State vs Error

```typescript
@Component({
  template: `
    @if (isLoading()) {
      <app-skeleton-loader />
    } @else if (error()) {
      <app-error-display [error]="error()" (onRetry)="loadData()" />
    } @else if (items().length === 0) {
      <app-empty-state
        title="No items found"
        description="Try adjusting your search or filters"
      />
    } @else {
      @for (item of items(); track item.id) {
        <app-item-card [item]="item" />
      }
    }
  `,
})
export class ItemListComponent {
  private itemService = inject(ItemService);

  items = signal<Item[]>([]);
  isLoading = signal(false);
  error = signal<ApiError | null>(null);

  loadData() {
    this.isLoading.set(true);
    this.error.set(null);

    this.itemService.getAll().subscribe({
      next: items => {
        this.items.set(items);
        this.isLoading.set(false);
      },
      error: err => {
        this.error.set(err);
        this.isLoading.set(false);
      },
    });
  }
}
```

### Optimistic Updates with Rollback

```typescript
@Injectable({ providedIn: 'root' })
export class TodoService {
  private http = inject(HttpClient);
  private notificationService = inject(NotificationService);

  todos = signal<Todo[]>([]);

  deleteTodo(id: number): void {
    // Store current state for rollback
    const previousTodos = this.todos();

    // Optimistic update
    this.todos.update(list => list.filter(t => t.id !== id));

    this.http.delete(`/api/todos/${id}`).subscribe({
      next: () => {
        this.notificationService.showSuccess('Todo deleted');
      },
      error: (error: ApiError) => {
        // Rollback on error
        this.todos.set(previousTodos);
        this.notificationService.showError(`Failed to delete: ${error.message}`);
      },
    });
  }

  updateTodo(id: number, changes: Partial<Todo>): void {
    const previousTodos = this.todos();
    const todoIndex = previousTodos.findIndex(t => t.id === id);

    if (todoIndex === -1) return;

    // Optimistic update
    const updatedTodo = { ...previousTodos[todoIndex], ...changes };
    this.todos.update(list => {
      const newList = [...list];
      newList[todoIndex] = updatedTodo;
      return newList;
    });

    this.http.patch<Todo>(`/api/todos/${id}`, changes).subscribe({
      next: serverTodo => {
        // Update with server response
        this.todos.update(list => {
          const newList = [...list];
          newList[todoIndex] = serverTodo;
          return newList;
        });
      },
      error: (error: ApiError) => {
        // Rollback on error
        this.todos.set(previousTodos);
        this.notificationService.showError(`Failed to update: ${error.message}`);
      },
    });
  }
}
```

## Best Practices

1. **Handle all error types**: Network, server, and client errors
2. **Provide user-friendly messages**: Don't expose technical details
3. **Log errors for debugging**: Send to monitoring service
4. **Allow retry for recoverable errors**: Network issues, timeouts
5. **Use optimistic updates carefully**: With proper rollback
6. **Centralize error handling**: Use interceptors for consistency
7. **Test error scenarios**: Cover all error paths in tests
8. **Consider offline scenarios**: Queue actions for retry
