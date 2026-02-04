# Angular Runtime Performance

## Overview

Runtime performance optimization ensures smooth user experience through efficient rendering, memory management, and responsive interactions.

## Virtual Scrolling

### Basic Virtual Scroll

```typescript
import { Component, signal } from '@angular/core';
import { ScrollingModule } from '@angular/cdk/scrolling';

@Component({
  selector: 'app-virtual-list',
  standalone: true,
  imports: [ScrollingModule],
  template: `
    <cdk-virtual-scroll-viewport itemSize="50" class="viewport">
      <div *cdkVirtualFor="let item of items(); trackBy: trackById" class="item">
        {{ item.name }}
      </div>
    </cdk-virtual-scroll-viewport>
  `,
  styles: `
    .viewport {
      height: 400px;
      width: 100%;
    }
    .item {
      height: 50px;
      display: flex;
      align-items: center;
      padding: 0 16px;
    }
  `,
})
export class VirtualListComponent {
  items = signal<Item[]>(Array.from({ length: 10000 }, (_, i) => ({
    id: i,
    name: `Item ${i}`,
  })));

  trackById(index: number, item: Item): number {
    return item.id;
  }
}
```

### Auto-Size Virtual Scroll

```typescript
import { CdkVirtualScrollViewport, ScrollingModule } from '@angular/cdk/scrolling';

@Component({
  selector: 'app-auto-size-list',
  standalone: true,
  imports: [ScrollingModule],
  template: `
    <cdk-virtual-scroll-viewport autosize class="viewport">
      <div
        *cdkVirtualFor="let item of items(); trackBy: trackById"
        class="item"
        [style.height.px]="item.height"
      >
        {{ item.content }}
      </div>
    </cdk-virtual-scroll-viewport>
  `,
})
export class AutoSizeListComponent {
  items = signal<VariableHeightItem[]>([]);
}
```

## Memory Management

### Subscription Cleanup

```typescript
import { DestroyRef, inject } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

@Component({...})
export class AutoCleanupComponent {
  private destroyRef = inject(DestroyRef);

  constructor() {
    // Automatically cleaned up on destroy
    this.dataService.getData()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(data => {
        this.data.set(data);
      });
  }
}

// Alternative: Using toSignal
@Component({...})
export class SignalComponent {
  private dataService = inject(DataService);

  // Automatically cleaned up, no manual subscription
  data = toSignal(this.dataService.getData(), {
    initialValue: null,
  });
}
```

### Event Listener Cleanup

```typescript
@Component({...})
export class EventCleanupComponent implements OnDestroy {
  private resizeHandler = () => this.onResize();

  constructor() {
    window.addEventListener('resize', this.resizeHandler);
  }

  ngOnDestroy() {
    window.removeEventListener('resize', this.resizeHandler);
  }

  private onResize() {
    // Handle resize
  }
}

// Better: Using fromEvent with takeUntilDestroyed
@Component({...})
export class ReactiveEventComponent {
  private destroyRef = inject(DestroyRef);

  constructor() {
    fromEvent(window, 'resize')
      .pipe(
        debounceTime(200),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe(() => this.onResize());
  }
}
```

### Memory Leak Prevention

```typescript
@Component({...})
export class MemorySafeComponent {
  // Avoid storing large data in component state
  private cache = new Map<string, WeakRef<Data>>();

  getData(id: string): Data | null {
    const ref = this.cache.get(id);
    if (ref) {
      const data = ref.deref();
      if (data) return data;
      this.cache.delete(id);
    }
    return null;
  }

  setData(id: string, data: Data): void {
    this.cache.set(id, new WeakRef(data));
  }
}
```

## Rendering Optimization

### Track By Function

```typescript
@Component({
  template: `
    @for (item of items(); track item.id) {
      <app-item [item]="item" />
    }
  `,
})
export class OptimizedListComponent {
  items = signal<Item[]>([]);
}
```

### Avoid Expensive Template Expressions

```typescript
// Bad: Expensive function called on every change detection
@Component({
  template: `
    <div>{{ getFilteredItems().length }} items</div>
    @for (item of getFilteredItems(); track item.id) {
      <app-item [item]="item" />
    }
  `,
})
export class BadComponent {
  getFilteredItems() {
    return this.items().filter(/* expensive filter */);
  }
}

// Good: Use computed signal
@Component({
  template: `
    <div>{{ filteredItems().length }} items</div>
    @for (item of filteredItems(); track item.id) {
      <app-item [item]="item" />
    }
  `,
})
export class GoodComponent {
  items = signal<Item[]>([]);
  filter = signal('');

  filteredItems = computed(() =>
    this.items().filter(item =>
      item.name.includes(this.filter())
    )
  );
}
```

### Deferred Views

```typescript
@Component({
  template: `
    <!-- Critical content loads immediately -->
    <header>
      <h1>Dashboard</h1>
    </header>

    <!-- Non-critical content deferred -->
    @defer (on viewport) {
      <app-analytics-widget />
    } @placeholder {
      <div class="skeleton"></div>
    }

    @defer (on idle) {
      <app-recommendations />
    }

    @defer (on interaction) {
      <app-advanced-filters />
    } @placeholder {
      <button>Show Filters</button>
    }
  `,
})
export class DashboardComponent {}
```

## Web Workers

### Creating a Worker

```typescript
// heavy-computation.worker.ts
/// <reference lib="webworker" />

addEventListener('message', ({ data }) => {
  const result = heavyComputation(data);
  postMessage(result);
});

function heavyComputation(data: number[]): number {
  return data.reduce((sum, n) => sum + Math.sqrt(n), 0);
}
```

### Using Workers in Angular

```typescript
@Injectable({ providedIn: 'root' })
export class ComputationService {
  private worker: Worker | null = null;

  constructor() {
    if (typeof Worker !== 'undefined') {
      this.worker = new Worker(
        new URL('./heavy-computation.worker', import.meta.url)
      );
    }
  }

  compute(data: number[]): Observable<number> {
    return new Observable(observer => {
      if (this.worker) {
        this.worker.onmessage = ({ data }) => {
          observer.next(data);
          observer.complete();
        };

        this.worker.onerror = (error) => {
          observer.error(error);
        };

        this.worker.postMessage(data);
      } else {
        // Fallback for environments without Worker support
        const result = this.computeSync(data);
        observer.next(result);
        observer.complete();
      }
    });
  }

  private computeSync(data: number[]): number {
    return data.reduce((sum, n) => sum + Math.sqrt(n), 0);
  }
}
```

## Animation Performance

### CSS vs JavaScript Animations

```typescript
// Prefer CSS animations for simple cases
@Component({
  template: `
    <div
      class="card"
      [class.expanded]="isExpanded()"
      (click)="toggle()"
    >
      Content
    </div>
  `,
  styles: `
    .card {
      height: 100px;
      transition: height 0.3s ease-out;
    }
    .card.expanded {
      height: 300px;
    }
  `,
})
export class CssAnimationComponent {
  isExpanded = signal(false);
  toggle() {
    this.isExpanded.update(v => !v);
  }
}
```

### Angular Animations Outside Zone

```typescript
import { AnimationBuilder, style, animate } from '@angular/animations';

@Component({...})
export class OptimizedAnimationComponent {
  private animationBuilder = inject(AnimationBuilder);
  private ngZone = inject(NgZone);
  private element = inject(ElementRef);

  animate() {
    const animation = this.animationBuilder.build([
      style({ opacity: 0, transform: 'translateY(20px)' }),
      animate('300ms ease-out', style({ opacity: 1, transform: 'translateY(0)' })),
    ]);

    // Run animation outside Angular zone
    this.ngZone.runOutsideAngular(() => {
      const player = animation.create(this.element.nativeElement);
      player.play();
    });
  }
}
```

### Request Animation Frame

```typescript
@Component({...})
export class SmoothScrollComponent {
  private ngZone = inject(NgZone);

  scrollToTop() {
    this.ngZone.runOutsideAngular(() => {
      const scrollStep = () => {
        const currentScroll = window.pageYOffset;
        if (currentScroll > 0) {
          window.scrollTo(0, currentScroll - currentScroll / 8);
          requestAnimationFrame(scrollStep);
        }
      };
      requestAnimationFrame(scrollStep);
    });
  }
}
```

## Lazy Initialization

### Lazy Services

```typescript
@Injectable({ providedIn: 'root' })
export class HeavyService {
  private _data: ExpensiveData | null = null;

  get data(): ExpensiveData {
    if (!this._data) {
      this._data = this.initializeExpensiveData();
    }
    return this._data;
  }

  private initializeExpensiveData(): ExpensiveData {
    // Expensive initialization
    return new ExpensiveData();
  }
}
```

### Lazy Computed Values

```typescript
@Component({...})
export class LazyComputedComponent {
  rawData = signal<RawData[]>([]);

  // Only computed when accessed
  processedData = computed(() => {
    console.log('Processing data...');
    return this.rawData().map(item => this.expensiveProcess(item));
  });

  private expensiveProcess(item: RawData): ProcessedData {
    // Expensive transformation
    return { ...item, processed: true };
  }
}
```

## Profiling and Debugging

### Chrome DevTools

```typescript
// Enable profiling in development
import { enableDebugTools } from '@angular/platform-browser';
import { ApplicationRef } from '@angular/core';

bootstrapApplication(AppComponent).then(appRef => {
  if (!environment.production) {
    const componentRef = appRef.injector.get(ApplicationRef).components[0];
    enableDebugTools(componentRef);
  }
});

// In console:
// ng.profiler.timeChangeDetection()
// ng.profiler.timeChangeDetection({ record: true })
```

### Performance Marks

```typescript
@Injectable({ providedIn: 'root' })
export class PerformanceService {
  mark(name: string) {
    performance.mark(name);
  }

  measure(name: string, startMark: string, endMark: string) {
    performance.measure(name, startMark, endMark);
    const entries = performance.getEntriesByName(name);
    console.log(`${name}: ${entries[0]?.duration.toFixed(2)}ms`);
  }
}

// Usage
@Component({...})
export class MeasuredComponent {
  private perf = inject(PerformanceService);

  loadData() {
    this.perf.mark('loadData-start');

    this.dataService.getData().subscribe(data => {
      this.perf.mark('loadData-end');
      this.perf.measure('loadData', 'loadData-start', 'loadData-end');
    });
  }
}
```

## Intersection Observer

### Lazy Load on Visibility

```typescript
@Directive({
  selector: '[appLazyLoad]',
  standalone: true,
})
export class LazyLoadDirective implements OnInit, OnDestroy {
  private element = inject(ElementRef);
  private observer: IntersectionObserver | null = null;

  isVisible = output<boolean>();

  ngOnInit() {
    this.observer = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            this.isVisible.emit(true);
            this.observer?.unobserve(this.element.nativeElement);
          }
        });
      },
      { threshold: 0.1 }
    );

    this.observer.observe(this.element.nativeElement);
  }

  ngOnDestroy() {
    this.observer?.disconnect();
  }
}

// Usage
@Component({
  template: `
    <div appLazyLoad (isVisible)="loadContent()">
      @if (contentLoaded()) {
        <app-heavy-content />
      } @else {
        <div class="placeholder">Loading...</div>
      }
    </div>
  `,
})
export class LazyContentComponent {
  contentLoaded = signal(false);

  loadContent() {
    this.contentLoaded.set(true);
  }
}
```

## Best Practices

1. **Use OnPush change detection**: Reduce change detection cycles
2. **Implement virtual scrolling**: For large lists
3. **Clean up subscriptions**: Use takeUntilDestroyed
4. **Use Web Workers**: For heavy computations
5. **Defer non-critical content**: Use @defer blocks
6. **Profile regularly**: Catch performance regressions
7. **Use trackBy**: For efficient list rendering
8. **Prefer signals**: Over observables for local state
9. **Lazy load routes**: Split code by feature
10. **Optimize images**: Use NgOptimizedImage
