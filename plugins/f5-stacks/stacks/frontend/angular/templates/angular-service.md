# Angular Service Template

## Basic Service

```typescript
// core/services/{{name}}.service.ts
import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, catchError, throwError, tap } from 'rxjs';

export interface {{PascalName}} {
  id: string;
  // Add properties
}

export interface Create{{PascalName}}Dto {
  // Add properties without id
}

export interface Update{{PascalName}}Dto {
  // Add updatable properties
}

@Injectable({ providedIn: 'root' })
export class {{PascalName}}Service {
  private http = inject(HttpClient);
  private apiUrl = '/api/{{pluralName}}';

  // State signals
  items = signal<{{PascalName}}[]>([]);
  selectedItem = signal<{{PascalName}} | null>(null);
  isLoading = signal(false);
  error = signal<string | null>(null);

  // Computed values
  itemCount = computed(() => this.items().length);
  hasItems = computed(() => this.items().length > 0);

  // CRUD Operations
  getAll(): Observable<{{PascalName}}[]> {
    this.isLoading.set(true);
    this.error.set(null);

    return this.http.get<{{PascalName}}[]>(this.apiUrl).pipe(
      tap(items => {
        this.items.set(items);
        this.isLoading.set(false);
      }),
      catchError(this.handleError.bind(this)),
    );
  }

  getById(id: string): Observable<{{PascalName}}> {
    return this.http.get<{{PascalName}}>(`${this.apiUrl}/${id}`).pipe(
      tap(item => this.selectedItem.set(item)),
      catchError(this.handleError.bind(this)),
    );
  }

  create(dto: Create{{PascalName}}Dto): Observable<{{PascalName}}> {
    return this.http.post<{{PascalName}}>(this.apiUrl, dto).pipe(
      tap(created => {
        this.items.update(items => [...items, created]);
      }),
      catchError(this.handleError.bind(this)),
    );
  }

  update(id: string, dto: Update{{PascalName}}Dto): Observable<{{PascalName}}> {
    return this.http.patch<{{PascalName}}>(`${this.apiUrl}/${id}`, dto).pipe(
      tap(updated => {
        this.items.update(items =>
          items.map(item => item.id === id ? updated : item)
        );
        if (this.selectedItem()?.id === id) {
          this.selectedItem.set(updated);
        }
      }),
      catchError(this.handleError.bind(this)),
    );
  }

  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/${id}`).pipe(
      tap(() => {
        this.items.update(items => items.filter(item => item.id !== id));
        if (this.selectedItem()?.id === id) {
          this.selectedItem.set(null);
        }
      }),
      catchError(this.handleError.bind(this)),
    );
  }

  // Selection
  select(id: string | null) {
    if (id) {
      const item = this.items().find(i => i.id === id);
      this.selectedItem.set(item ?? null);
    } else {
      this.selectedItem.set(null);
    }
  }

  // Error handling
  private handleError(error: any): Observable<never> {
    const message = error?.error?.message || error?.message || 'An error occurred';
    this.error.set(message);
    this.isLoading.set(false);
    return throwError(() => new Error(message));
  }
}
```

## Service with RxJS State

```typescript
// core/services/{{name}}.service.ts
import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, catchError, map, tap, throwError } from 'rxjs';

interface {{PascalName}}State {
  items: {{PascalName}}[];
  selectedId: string | null;
  isLoading: boolean;
  error: string | null;
}

const initialState: {{PascalName}}State = {
  items: [],
  selectedId: null,
  isLoading: false,
  error: null,
};

@Injectable({ providedIn: 'root' })
export class {{PascalName}}Service {
  private http = inject(HttpClient);
  private apiUrl = '/api/{{pluralName}}';

  private state$ = new BehaviorSubject<{{PascalName}}State>(initialState);

  // Selectors
  readonly items$ = this.state$.pipe(map(s => s.items));
  readonly selectedItem$ = this.state$.pipe(
    map(s => s.items.find(i => i.id === s.selectedId) ?? null)
  );
  readonly isLoading$ = this.state$.pipe(map(s => s.isLoading));
  readonly error$ = this.state$.pipe(map(s => s.error));

  // Actions
  loadAll(): Observable<{{PascalName}}[]> {
    this.updateState({ isLoading: true, error: null });

    return this.http.get<{{PascalName}}[]>(this.apiUrl).pipe(
      tap(items => this.updateState({ items, isLoading: false })),
      catchError(error => {
        this.updateState({ error: error.message, isLoading: false });
        return throwError(() => error);
      }),
    );
  }

  select(id: string | null) {
    this.updateState({ selectedId: id });
  }

  private updateState(partial: Partial<{{PascalName}}State>) {
    this.state$.next({ ...this.state$.value, ...partial });
  }
}
```

## SignalStore Service

```typescript
// features/{{feature}}/store/{{name}}.store.ts
import {
  signalStore,
  withState,
  withComputed,
  withMethods,
  withHooks,
  patchState,
} from '@ngrx/signals';
import { withEntities, addEntity, removeEntity, updateEntity, setAllEntities } from '@ngrx/signals/entities';
import { rxMethod } from '@ngrx/signals/rxjs-interop';
import { computed, inject } from '@angular/core';
import { pipe, switchMap, tap } from 'rxjs';
import { tapResponse } from '@ngrx/operators';
import { {{PascalName}}ApiService } from '../services/{{name}}-api.service';

interface {{PascalName}} {
  id: string;
  name: string;
  // Add properties
}

interface {{PascalName}}State {
  selectedId: string | null;
  isLoading: boolean;
  error: string | null;
  filter: string;
}

const initialState: {{PascalName}}State = {
  selectedId: null,
  isLoading: false,
  error: null,
  filter: '',
};

export const {{PascalName}}Store = signalStore(
  { providedIn: 'root' },

  withEntities<{{PascalName}}>(),
  withState(initialState),

  withComputed(({ entities, selectedId, filter }) => ({
    selectedItem: computed(() => {
      const id = selectedId();
      return entities().find(e => e.id === id) ?? null;
    }),

    filteredItems: computed(() => {
      const f = filter().toLowerCase();
      if (!f) return entities();
      return entities().filter(e => e.name.toLowerCase().includes(f));
    }),

    itemCount: computed(() => entities().length),
  })),

  withMethods((store, api = inject({{PascalName}}ApiService)) => ({
    // Sync methods
    select(id: string | null) {
      patchState(store, { selectedId: id });
    },

    setFilter(filter: string) {
      patchState(store, { filter });
    },

    // Async methods
    loadAll: rxMethod<void>(
      pipe(
        tap(() => patchState(store, { isLoading: true, error: null })),
        switchMap(() =>
          api.getAll().pipe(
            tapResponse({
              next: items => {
                patchState(store, setAllEntities(items), { isLoading: false });
              },
              error: (error: Error) => {
                patchState(store, { error: error.message, isLoading: false });
              },
            })
          )
        )
      )
    ),

    create: rxMethod<Omit<{{PascalName}}, 'id'>>(
      pipe(
        switchMap(data =>
          api.create(data).pipe(
            tapResponse({
              next: created => patchState(store, addEntity(created)),
              error: (error: Error) => patchState(store, { error: error.message }),
            })
          )
        )
      )
    ),

    delete: rxMethod<string>(
      pipe(
        switchMap(id =>
          api.delete(id).pipe(
            tapResponse({
              next: () => patchState(store, removeEntity(id)),
              error: (error: Error) => patchState(store, { error: error.message }),
            })
          )
        )
      )
    ),
  })),

  withHooks({
    onInit(store) {
      store.loadAll();
    },
  }),
);
```

## API Service (HTTP Only)

```typescript
// core/api/{{name}}-api.service.ts
import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface {{PascalName}} {
  id: string;
  // Properties
}

export interface {{PascalName}}QueryParams {
  page?: number;
  limit?: number;
  sort?: string;
  search?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
}

@Injectable({ providedIn: 'root' })
export class {{PascalName}}ApiService {
  private http = inject(HttpClient);
  private baseUrl = `${environment.apiUrl}/{{pluralName}}`;

  getAll(params?: {{PascalName}}QueryParams): Observable<{{PascalName}}[]> {
    const httpParams = this.buildParams(params);
    return this.http.get<{{PascalName}}[]>(this.baseUrl, { params: httpParams });
  }

  getPaginated(params: {{PascalName}}QueryParams): Observable<PaginatedResponse<{{PascalName}}>> {
    const httpParams = this.buildParams(params);
    return this.http.get<PaginatedResponse<{{PascalName}}>>(this.baseUrl, { params: httpParams });
  }

  getById(id: string): Observable<{{PascalName}}> {
    return this.http.get<{{PascalName}}>(`${this.baseUrl}/${id}`);
  }

  create(data: Omit<{{PascalName}}, 'id'>): Observable<{{PascalName}}> {
    return this.http.post<{{PascalName}}>(this.baseUrl, data);
  }

  update(id: string, data: Partial<{{PascalName}}>): Observable<{{PascalName}}> {
    return this.http.patch<{{PascalName}}>(`${this.baseUrl}/${id}`, data);
  }

  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/${id}`);
  }

  private buildParams(params?: Record<string, any>): HttpParams {
    let httpParams = new HttpParams();

    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          httpParams = httpParams.set(key, String(value));
        }
      });
    }

    return httpParams;
  }
}
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{name}}` | kebab-case name | `user` |
| `{{PascalName}}` | PascalCase name | `User` |
| `{{pluralName}}` | Plural name | `users` |
| `{{feature}}` | Feature folder | `users` |
