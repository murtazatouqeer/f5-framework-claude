# Angular Authentication App Example

Complete authentication flow using Angular 17+ best practices.

## Features

- JWT authentication with refresh tokens
- Route guards (functional)
- HTTP interceptors (functional)
- Signal-based auth state
- Reactive forms with validation
- Protected routes
- Role-based access control

## Project Structure

```
src/
├── app/
│   ├── app.component.ts
│   ├── app.config.ts
│   ├── app.routes.ts
│   ├── core/
│   │   ├── auth/
│   │   │   ├── auth.service.ts
│   │   │   ├── auth.guard.ts
│   │   │   ├── auth.interceptor.ts
│   │   │   └── auth.models.ts
│   │   └── services/
│   │       └── storage.service.ts
│   └── features/
│       ├── auth/
│       │   ├── auth.routes.ts
│       │   └── components/
│       │       ├── login/
│       │       ├── register/
│       │       └── forgot-password/
│       ├── dashboard/
│       │   └── dashboard.component.ts
│       └── profile/
│           └── profile.component.ts
└── environments/
```

## Key Files

### Auth Models

```typescript
// core/auth/auth.models.ts
export interface User {
  id: string;
  email: string;
  name: string;
  roles: string[];
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  name: string;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}

export interface AuthResponse {
  user: User;
  tokens: AuthTokens;
}
```

### Auth Service

```typescript
// core/auth/auth.service.ts
import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, tap, catchError, throwError, BehaviorSubject, switchMap } from 'rxjs';
import { StorageService } from '../services/storage.service';
import { User, LoginCredentials, RegisterData, AuthResponse, AuthTokens } from './auth.models';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private http = inject(HttpClient);
  private router = inject(Router);
  private storage = inject(StorageService);

  private apiUrl = '/api/auth';

  // Signal-based state
  private currentUserSignal = signal<User | null>(null);
  private isAuthenticatedSignal = signal(false);
  private isLoadingSignal = signal(false);

  // Public computed signals
  currentUser = this.currentUserSignal.asReadonly();
  isAuthenticated = this.isAuthenticatedSignal.asReadonly();
  isLoading = this.isLoadingSignal.asReadonly();

  userRoles = computed(() => this.currentUserSignal()?.roles ?? []);

  // For token refresh synchronization
  private refreshTokenSubject = new BehaviorSubject<string | null>(null);
  private isRefreshing = false;

  constructor() {
    this.initializeAuth();
  }

  private initializeAuth() {
    const tokens = this.storage.getTokens();
    if (tokens) {
      this.isAuthenticatedSignal.set(true);
      this.loadCurrentUser();
    }
  }

  login(credentials: LoginCredentials): Observable<AuthResponse> {
    this.isLoadingSignal.set(true);

    return this.http.post<AuthResponse>(`${this.apiUrl}/login`, credentials).pipe(
      tap(response => {
        this.handleAuthSuccess(response);
      }),
      catchError(error => {
        this.isLoadingSignal.set(false);
        return throwError(() => error);
      }),
    );
  }

  register(data: RegisterData): Observable<AuthResponse> {
    this.isLoadingSignal.set(true);

    return this.http.post<AuthResponse>(`${this.apiUrl}/register`, data).pipe(
      tap(response => {
        this.handleAuthSuccess(response);
      }),
      catchError(error => {
        this.isLoadingSignal.set(false);
        return throwError(() => error);
      }),
    );
  }

  logout(): void {
    this.http.post(`${this.apiUrl}/logout`, {}).subscribe();
    this.clearAuth();
    this.router.navigate(['/auth/login']);
  }

  refreshToken(): Observable<AuthTokens> {
    if (this.isRefreshing) {
      return this.refreshTokenSubject.pipe(
        switchMap(token => {
          if (token) {
            return new Observable<AuthTokens>(observer => {
              observer.next({ accessToken: token } as AuthTokens);
              observer.complete();
            });
          }
          return throwError(() => new Error('No token'));
        }),
      );
    }

    this.isRefreshing = true;
    this.refreshTokenSubject.next(null);

    const refreshToken = this.storage.getRefreshToken();

    return this.http.post<AuthTokens>(`${this.apiUrl}/refresh`, { refreshToken }).pipe(
      tap(tokens => {
        this.storage.setTokens(tokens);
        this.isRefreshing = false;
        this.refreshTokenSubject.next(tokens.accessToken);
      }),
      catchError(error => {
        this.isRefreshing = false;
        this.clearAuth();
        return throwError(() => error);
      }),
    );
  }

  getAccessToken(): string | null {
    return this.storage.getAccessToken();
  }

  hasRole(role: string): boolean {
    return this.userRoles().includes(role);
  }

  hasAnyRole(roles: string[]): boolean {
    return roles.some(role => this.hasRole(role));
  }

  private handleAuthSuccess(response: AuthResponse): void {
    this.storage.setTokens(response.tokens);
    this.currentUserSignal.set(response.user);
    this.isAuthenticatedSignal.set(true);
    this.isLoadingSignal.set(false);
  }

  private clearAuth(): void {
    this.storage.clearTokens();
    this.currentUserSignal.set(null);
    this.isAuthenticatedSignal.set(false);
  }

  private loadCurrentUser(): void {
    this.http.get<User>(`${this.apiUrl}/me`).subscribe({
      next: user => this.currentUserSignal.set(user),
      error: () => this.clearAuth(),
    });
  }
}
```

### Auth Guard (Functional)

```typescript
// core/auth/auth.guard.ts
import { inject } from '@angular/core';
import { Router, CanActivateFn, CanMatchFn } from '@angular/router';
import { AuthService } from './auth.service';

export const authGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (authService.isAuthenticated()) {
    return true;
  }

  return router.createUrlTree(['/auth/login'], {
    queryParams: { returnUrl: state.url },
  });
};

export const guestGuard: CanActivateFn = () => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (!authService.isAuthenticated()) {
    return true;
  }

  return router.createUrlTree(['/dashboard']);
};

export const roleGuard: CanActivateFn = (route) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  const requiredRoles = route.data['roles'] as string[] | undefined;

  if (!requiredRoles?.length) {
    return true;
  }

  if (authService.hasAnyRole(requiredRoles)) {
    return true;
  }

  return router.createUrlTree(['/unauthorized']);
};

// Factory for specific role requirements
export function requireRole(...roles: string[]): CanMatchFn {
  return () => {
    const authService = inject(AuthService);
    const router = inject(Router);

    if (authService.hasAnyRole(roles)) {
      return true;
    }

    return router.createUrlTree(['/unauthorized']);
  };
}
```

### Auth Interceptor (Functional)

```typescript
// core/auth/auth.interceptor.ts
import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, switchMap, throwError } from 'rxjs';
import { AuthService } from './auth.service';

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
          switchMap(tokens => {
            const newReq = req.clone({
              setHeaders: {
                Authorization: `Bearer ${tokens.accessToken}`,
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

### Routes Configuration

```typescript
// app.routes.ts
import { Routes } from '@angular/router';
import { authGuard, guestGuard, roleGuard, requireRole } from './core/auth/auth.guard';

export const routes: Routes = [
  { path: '', redirectTo: 'dashboard', pathMatch: 'full' },

  // Public routes (guest only)
  {
    path: 'auth',
    canMatch: [guestGuard],
    loadChildren: () => import('./features/auth/auth.routes'),
  },

  // Protected routes
  {
    path: 'dashboard',
    loadComponent: () => import('./features/dashboard/dashboard.component'),
    canActivate: [authGuard],
  },

  {
    path: 'profile',
    loadComponent: () => import('./features/profile/profile.component'),
    canActivate: [authGuard],
  },

  // Role-protected routes
  {
    path: 'admin',
    loadChildren: () => import('./features/admin/admin.routes'),
    canActivate: [authGuard, roleGuard],
    data: { roles: ['admin'] },
  },

  // Alternative: Using factory guard
  {
    path: 'moderator',
    loadComponent: () => import('./features/moderator/moderator.component'),
    canMatch: [requireRole('admin', 'moderator')],
  },

  // Error pages
  {
    path: 'unauthorized',
    loadComponent: () => import('./features/errors/unauthorized.component'),
  },

  { path: '**', redirectTo: 'dashboard' },
];

// features/auth/auth.routes.ts
import { Routes } from '@angular/router';

export default [
  {
    path: 'login',
    loadComponent: () => import('./components/login/login.component'),
  },
  {
    path: 'register',
    loadComponent: () => import('./components/register/register.component'),
  },
  {
    path: 'forgot-password',
    loadComponent: () => import('./components/forgot-password/forgot-password.component'),
  },
] satisfies Routes;
```

### Login Component

```typescript
// features/auth/components/login/login.component.ts
import { Component, inject, signal } from '@angular/core';
import { Router, RouterLink, ActivatedRoute } from '@angular/router';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { AuthService } from '../../../../core/auth/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink],
  template: `
    <div class="auth-container">
      <h1>Login</h1>

      @if (error()) {
        <div class="error-banner">{{ error() }}</div>
      }

      <form [formGroup]="form" (ngSubmit)="onSubmit()">
        <div class="field">
          <label for="email">Email</label>
          <input
            id="email"
            type="email"
            formControlName="email"
            autocomplete="email"
          />
          @if (form.controls.email.errors?.['email'] && form.controls.email.touched) {
            <span class="error">Invalid email format</span>
          }
        </div>

        <div class="field">
          <label for="password">Password</label>
          <input
            id="password"
            type="password"
            formControlName="password"
            autocomplete="current-password"
          />
          @if (form.controls.password.errors?.['required'] && form.controls.password.touched) {
            <span class="error">Password is required</span>
          }
        </div>

        <button type="submit" [disabled]="form.invalid || authService.isLoading()">
          {{ authService.isLoading() ? 'Logging in...' : 'Login' }}
        </button>
      </form>

      <div class="links">
        <a routerLink="/auth/forgot-password">Forgot password?</a>
        <a routerLink="/auth/register">Create account</a>
      </div>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export default class LoginComponent {
  private fb = inject(FormBuilder);
  private router = inject(Router);
  private route = inject(ActivatedRoute);
  protected authService = inject(AuthService);

  error = signal<string | null>(null);

  form = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(6)]],
  });

  onSubmit() {
    if (this.form.invalid) return;

    this.error.set(null);

    this.authService.login(this.form.getRawValue()).subscribe({
      next: () => {
        const returnUrl = this.route.snapshot.queryParams['returnUrl'] || '/dashboard';
        this.router.navigateByUrl(returnUrl);
      },
      error: (err) => {
        this.error.set(err.error?.message || 'Login failed. Please try again.');
      },
    });
  }
}
```

### Register Component

```typescript
// features/auth/components/register/register.component.ts
import { Component, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { ReactiveFormsModule, FormBuilder, Validators, AbstractControl } from '@angular/forms';
import { AuthService } from '../../../../core/auth/auth.service';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink],
  template: `
    <div class="auth-container">
      <h1>Create Account</h1>

      @if (error()) {
        <div class="error-banner">{{ error() }}</div>
      }

      <form [formGroup]="form" (ngSubmit)="onSubmit()">
        <div class="field">
          <label for="name">Name</label>
          <input id="name" formControlName="name" autocomplete="name" />
        </div>

        <div class="field">
          <label for="email">Email</label>
          <input id="email" type="email" formControlName="email" autocomplete="email" />
        </div>

        <div class="field">
          <label for="password">Password</label>
          <input id="password" type="password" formControlName="password" autocomplete="new-password" />
          @if (form.controls.password.errors?.['minlength']) {
            <span class="error">Password must be at least 8 characters</span>
          }
        </div>

        <div class="field">
          <label for="confirmPassword">Confirm Password</label>
          <input id="confirmPassword" type="password" formControlName="confirmPassword" />
          @if (form.errors?.['passwordMismatch']) {
            <span class="error">Passwords do not match</span>
          }
        </div>

        <button type="submit" [disabled]="form.invalid || authService.isLoading()">
          {{ authService.isLoading() ? 'Creating...' : 'Create Account' }}
        </button>
      </form>

      <div class="links">
        <a routerLink="/auth/login">Already have an account? Login</a>
      </div>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export default class RegisterComponent {
  private fb = inject(FormBuilder);
  private router = inject(Router);
  protected authService = inject(AuthService);

  error = signal<string | null>(null);

  form = this.fb.nonNullable.group({
    name: ['', [Validators.required, Validators.minLength(2)]],
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(8)]],
    confirmPassword: ['', [Validators.required]],
  }, {
    validators: [this.passwordMatchValidator],
  });

  passwordMatchValidator(control: AbstractControl) {
    const password = control.get('password')?.value;
    const confirmPassword = control.get('confirmPassword')?.value;

    if (password !== confirmPassword) {
      return { passwordMismatch: true };
    }
    return null;
  }

  onSubmit() {
    if (this.form.invalid) return;

    this.error.set(null);
    const { confirmPassword, ...data } = this.form.getRawValue();

    this.authService.register(data).subscribe({
      next: () => {
        this.router.navigate(['/dashboard']);
      },
      error: (err) => {
        this.error.set(err.error?.message || 'Registration failed. Please try again.');
      },
    });
  }
}
```

### Storage Service

```typescript
// core/services/storage.service.ts
import { Injectable } from '@angular/core';
import { AuthTokens } from '../auth/auth.models';

const ACCESS_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

@Injectable({ providedIn: 'root' })
export class StorageService {
  setTokens(tokens: AuthTokens): void {
    localStorage.setItem(ACCESS_TOKEN_KEY, tokens.accessToken);
    localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refreshToken);
  }

  getTokens(): AuthTokens | null {
    const accessToken = localStorage.getItem(ACCESS_TOKEN_KEY);
    const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);

    if (!accessToken || !refreshToken) {
      return null;
    }

    return { accessToken, refreshToken, expiresIn: 0 };
  }

  getAccessToken(): string | null {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  }

  getRefreshToken(): string | null {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  }

  clearTokens(): void {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  }
}
```

## App Configuration

```typescript
// app.config.ts
import { ApplicationConfig, provideZoneChangeDetection } from '@angular/core';
import { provideRouter, withComponentInputBinding } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { routes } from './app.routes';
import { authInterceptor } from './core/auth/auth.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(routes, withComponentInputBinding()),
    provideHttpClient(withInterceptors([authInterceptor])),
  ],
};
```

## Running the Example

```bash
# Create new Angular project
ng new auth-app --standalone --style=scss

# Copy example files to project
# Start development server
ng serve
```

## API Endpoints Expected

```
POST   /api/auth/login      - Login with credentials
POST   /api/auth/register   - Register new user
POST   /api/auth/logout     - Logout (invalidate tokens)
POST   /api/auth/refresh    - Refresh access token
GET    /api/auth/me         - Get current user
POST   /api/auth/forgot-password - Request password reset
POST   /api/auth/reset-password  - Reset password with token
```

## Security Best Practices

1. **Store tokens securely** - Consider using HttpOnly cookies for refresh tokens
2. **Short-lived access tokens** - 15 minutes recommended
3. **Longer refresh tokens** - 7-30 days with rotation
4. **CSRF protection** - Use SameSite cookies or CSRF tokens
5. **Rate limiting** - Implement on auth endpoints
6. **Password requirements** - Enforce strong passwords
7. **Account lockout** - After multiple failed attempts
