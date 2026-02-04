# Angular HttpClient

## Overview

Angular's HttpClient provides a modern, streamlined API for HTTP requests with support for typed responses, interceptors, and reactive programming with RxJS.

## Setup

```typescript
// app.config.ts
import { ApplicationConfig } from '@angular/core';
import { provideHttpClient, withInterceptors } from '@angular/common/http';

export const appConfig: ApplicationConfig = {
  providers: [
    provideHttpClient(
      withInterceptors([]),
    ),
  ],
};
```

## Basic Requests

### GET Request

```typescript
import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

interface User {
  id: number;
  name: string;
  email: string;
}

@Injectable({ providedIn: 'root' })
export class UserService {
  private http = inject(HttpClient);
  private apiUrl = '/api/users';

  // Get all users
  getAll(): Observable<User[]> {
    return this.http.get<User[]>(this.apiUrl);
  }

  // Get single user
  getById(id: number): Observable<User> {
    return this.http.get<User>(`${this.apiUrl}/${id}`);
  }

  // Get with query parameters
  search(name: string, page: number = 1): Observable<User[]> {
    return this.http.get<User[]>(this.apiUrl, {
      params: { name, page: page.toString() },
    });
  }
}
```

### POST Request

```typescript
@Injectable({ providedIn: 'root' })
export class UserService {
  private http = inject(HttpClient);
  private apiUrl = '/api/users';

  // Create user
  create(user: Omit<User, 'id'>): Observable<User> {
    return this.http.post<User>(this.apiUrl, user);
  }

  // Create with full response
  createWithResponse(user: Omit<User, 'id'>): Observable<HttpResponse<User>> {
    return this.http.post<User>(this.apiUrl, user, {
      observe: 'response',
    });
  }
}
```

### PUT/PATCH Request

```typescript
@Injectable({ providedIn: 'root' })
export class UserService {
  private http = inject(HttpClient);
  private apiUrl = '/api/users';

  // Full update
  update(id: number, user: User): Observable<User> {
    return this.http.put<User>(`${this.apiUrl}/${id}`, user);
  }

  // Partial update
  patch(id: number, changes: Partial<User>): Observable<User> {
    return this.http.patch<User>(`${this.apiUrl}/${id}`, changes);
  }
}
```

### DELETE Request

```typescript
@Injectable({ providedIn: 'root' })
export class UserService {
  private http = inject(HttpClient);
  private apiUrl = '/api/users';

  // Delete user
  delete(id: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/${id}`);
  }

  // Delete with confirmation
  deleteWithResponse(id: number): Observable<HttpResponse<void>> {
    return this.http.delete<void>(`${this.apiUrl}/${id}`, {
      observe: 'response',
    });
  }
}
```

## Request Options

### Headers

```typescript
import { HttpHeaders } from '@angular/common/http';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private http = inject(HttpClient);

  // Set headers
  getData(): Observable<any> {
    const headers = new HttpHeaders()
      .set('Authorization', 'Bearer token')
      .set('Content-Type', 'application/json')
      .set('X-Custom-Header', 'value');

    return this.http.get('/api/data', { headers });
  }

  // Append headers
  postData(data: any): Observable<any> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    });

    return this.http.post('/api/data', data, { headers });
  }
}
```

### Query Parameters

```typescript
import { HttpParams } from '@angular/common/http';

@Injectable({ providedIn: 'root' })
export class SearchService {
  private http = inject(HttpClient);

  // Using HttpParams
  search(query: string, filters: Record<string, string>): Observable<any[]> {
    let params = new HttpParams()
      .set('q', query)
      .set('page', '1')
      .set('limit', '10');

    // Add dynamic filters
    Object.entries(filters).forEach(([key, value]) => {
      params = params.set(key, value);
    });

    return this.http.get<any[]>('/api/search', { params });
  }

  // Using object syntax
  quickSearch(query: string): Observable<any[]> {
    return this.http.get<any[]>('/api/search', {
      params: { q: query, limit: '10' },
    });
  }

  // Array parameters
  searchWithTags(tags: string[]): Observable<any[]> {
    let params = new HttpParams();
    tags.forEach(tag => {
      params = params.append('tags', tag);
    });

    return this.http.get<any[]>('/api/search', { params });
  }
}
```

### Response Types

```typescript
@Injectable({ providedIn: 'root' })
export class DownloadService {
  private http = inject(HttpClient);

  // JSON response (default)
  getJson(): Observable<any> {
    return this.http.get('/api/data');
  }

  // Text response
  getText(): Observable<string> {
    return this.http.get('/api/text', { responseType: 'text' });
  }

  // Blob response (files)
  downloadFile(fileId: string): Observable<Blob> {
    return this.http.get(`/api/files/${fileId}`, { responseType: 'blob' });
  }

  // ArrayBuffer response
  getBinary(): Observable<ArrayBuffer> {
    return this.http.get('/api/binary', { responseType: 'arraybuffer' });
  }

  // Full response with headers
  getWithHeaders(): Observable<HttpResponse<any>> {
    return this.http.get('/api/data', { observe: 'response' });
  }

  // Events (for progress)
  uploadWithProgress(file: File): Observable<HttpEvent<any>> {
    const formData = new FormData();
    formData.append('file', file);

    return this.http.post('/api/upload', formData, {
      observe: 'events',
      reportProgress: true,
    });
  }
}
```

## File Upload/Download

### File Upload

```typescript
@Injectable({ providedIn: 'root' })
export class FileService {
  private http = inject(HttpClient);

  // Simple upload
  upload(file: File): Observable<any> {
    const formData = new FormData();
    formData.append('file', file, file.name);

    return this.http.post('/api/upload', formData);
  }

  // Multiple files
  uploadMultiple(files: File[]): Observable<any> {
    const formData = new FormData();
    files.forEach((file, index) => {
      formData.append(`file${index}`, file, file.name);
    });

    return this.http.post('/api/upload-multiple', formData);
  }

  // Upload with progress
  uploadWithProgress(file: File): Observable<number | string> {
    const formData = new FormData();
    formData.append('file', file, file.name);

    return this.http.post('/api/upload', formData, {
      observe: 'events',
      reportProgress: true,
    }).pipe(
      map(event => {
        switch (event.type) {
          case HttpEventType.UploadProgress:
            if (event.total) {
              return Math.round((100 * event.loaded) / event.total);
            }
            return 0;
          case HttpEventType.Response:
            return 'complete';
          default:
            return 0;
        }
      }),
      filter(result => result !== 0),
    );
  }
}
```

### File Download

```typescript
@Injectable({ providedIn: 'root' })
export class DownloadService {
  private http = inject(HttpClient);

  download(fileId: string, filename: string): Observable<void> {
    return this.http.get(`/api/files/${fileId}`, {
      responseType: 'blob',
    }).pipe(
      map(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        window.URL.revokeObjectURL(url);
      }),
    );
  }

  downloadWithProgress(fileId: string): Observable<number | Blob> {
    return this.http.get(`/api/files/${fileId}`, {
      responseType: 'blob',
      observe: 'events',
      reportProgress: true,
    }).pipe(
      map(event => {
        switch (event.type) {
          case HttpEventType.DownloadProgress:
            if (event.total) {
              return Math.round((100 * event.loaded) / event.total);
            }
            return 0;
          case HttpEventType.Response:
            return event.body as Blob;
          default:
            return 0;
        }
      }),
    );
  }
}
```

## Using HttpClient with Signals

```typescript
@Injectable({ providedIn: 'root' })
export class ProductService {
  private http = inject(HttpClient);

  // Signal-based data fetching
  products = signal<Product[]>([]);
  isLoading = signal(false);
  error = signal<string | null>(null);

  loadProducts(): void {
    this.isLoading.set(true);
    this.error.set(null);

    this.http.get<Product[]>('/api/products').pipe(
      finalize(() => this.isLoading.set(false)),
    ).subscribe({
      next: products => this.products.set(products),
      error: err => this.error.set(err.message),
    });
  }
}

// Component usage
@Component({
  template: `
    @if (productService.isLoading()) {
      <div>Loading...</div>
    }

    @if (productService.error(); as error) {
      <div class="error">{{ error }}</div>
    }

    @for (product of productService.products(); track product.id) {
      <div>{{ product.name }}</div>
    }
  `,
})
export class ProductListComponent {
  productService = inject(ProductService);

  constructor() {
    this.productService.loadProducts();
  }
}
```

## Resource API (Angular 19+)

```typescript
import { resource, signal } from '@angular/core';

@Component({...})
export class UserComponent {
  userId = signal<number>(1);

  // Reactive data fetching
  userResource = resource({
    request: () => ({ id: this.userId() }),
    loader: async ({ request, abortSignal }) => {
      const response = await fetch(`/api/users/${request.id}`, {
        signal: abortSignal,
      });
      return response.json() as Promise<User>;
    },
  });

  // Access resource state
  user = this.userResource.value;
  isLoading = this.userResource.isLoading;
  error = this.userResource.error;
}
```

## Cancellation

```typescript
import { Subject, takeUntil, switchMap } from 'rxjs';

@Component({...})
export class SearchComponent implements OnDestroy {
  private http = inject(HttpClient);
  private destroy$ = new Subject<void>();
  private searchTerms$ = new Subject<string>();

  results = signal<any[]>([]);

  constructor() {
    // Auto-cancel previous requests
    this.searchTerms$.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      switchMap(term => this.http.get<any[]>(`/api/search?q=${term}`)),
      takeUntil(this.destroy$),
    ).subscribe(results => {
      this.results.set(results);
    });
  }

  search(term: string) {
    this.searchTerms$.next(term);
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }
}
```

## Retry and Timeout

```typescript
import { retry, timeout, catchError } from 'rxjs/operators';

@Injectable({ providedIn: 'root' })
export class ResilientService {
  private http = inject(HttpClient);

  getData(): Observable<any> {
    return this.http.get('/api/data').pipe(
      timeout(10000), // 10 seconds
      retry({
        count: 3,
        delay: (error, retryCount) => {
          console.log(`Retry attempt ${retryCount}`);
          return timer(1000 * retryCount); // Exponential backoff
        },
      }),
      catchError(error => {
        console.error('Request failed after retries:', error);
        return throwError(() => error);
      }),
    );
  }
}
```

## Best Practices

1. **Type your responses**: Use interfaces for type safety
2. **Handle errors properly**: Use interceptors or catchError
3. **Cancel unused requests**: Use switchMap or takeUntil
4. **Use services**: Don't call HttpClient directly in components
5. **Set appropriate timeouts**: Prevent hanging requests
6. **Implement retry logic**: For transient failures
7. **Report progress**: For file uploads/downloads
