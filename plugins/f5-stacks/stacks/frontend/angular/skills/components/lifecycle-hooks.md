# Angular Lifecycle Hooks

## Overview

Angular components have a lifecycle managed by Angular. Lifecycle hooks allow you to act at specific moments during creation, change, and destruction.

## Lifecycle Hook Order

```
1. constructor()
2. ngOnChanges()      - When input bindings change
3. ngOnInit()         - After first ngOnChanges
4. ngDoCheck()        - During every change detection
5. ngAfterContentInit()   - After content projection
6. ngAfterContentChecked() - After content check
7. ngAfterViewInit()      - After view initialization
8. ngAfterViewChecked()   - After view check
9. ngOnDestroy()      - Before component destruction
```

## Modern Approach with Signals

With Angular 17+ signals, many lifecycle hooks become unnecessary:

```typescript
@Component({...})
export class ModernComponent {
  // Input signals handle ngOnChanges
  userId = input.required<string>();

  // Effects handle reactions to signal changes
  constructor() {
    effect(() => {
      const id = this.userId();
      // Runs when userId changes
    });
  }

  // DestroyRef handles cleanup
  private destroyRef = inject(DestroyRef);

  ngOnInit() {
    const subscription = someObservable$.subscribe();

    this.destroyRef.onDestroy(() => {
      subscription.unsubscribe();
    });
  }
}
```

## Lifecycle Hooks Detail

### ngOnChanges

Called when input properties change. Receives a `SimpleChanges` object.

```typescript
import { Component, OnChanges, SimpleChanges, input } from '@angular/core';

@Component({...})
export class UserDetailComponent implements OnChanges {
  // Legacy @Input approach
  @Input() userId!: string;
  @Input() refresh = false;

  ngOnChanges(changes: SimpleChanges) {
    // Check specific property
    if (changes['userId']) {
      const change = changes['userId'];
      console.log('Previous:', change.previousValue);
      console.log('Current:', change.currentValue);
      console.log('First change:', change.firstChange);

      this.loadUser(change.currentValue);
    }

    // Check if any change
    if (changes['refresh']?.currentValue === true) {
      this.refresh();
    }
  }
}

// Modern approach with signals - no ngOnChanges needed
@Component({...})
export class ModernUserDetailComponent {
  userId = input.required<string>();

  constructor() {
    // Effect replaces ngOnChanges
    effect(() => {
      this.loadUser(this.userId());
    });
  }
}
```

### ngOnInit

Called once after the first `ngOnChanges`. Best for initialization logic.

```typescript
import { Component, OnInit, inject, DestroyRef } from '@angular/core';

@Component({...})
export class DashboardComponent implements OnInit {
  private dataService = inject(DataService);
  private destroyRef = inject(DestroyRef);

  data = signal<Data | null>(null);
  isLoading = signal(true);

  ngOnInit() {
    // Fetch initial data
    this.loadData();

    // Setup subscriptions with cleanup
    const subscription = interval(30000).subscribe(() => {
      this.loadData();
    });

    this.destroyRef.onDestroy(() => {
      subscription.unsubscribe();
    });
  }

  private loadData() {
    this.isLoading.set(true);
    this.dataService.getData().subscribe({
      next: data => {
        this.data.set(data);
        this.isLoading.set(false);
      },
      error: () => this.isLoading.set(false),
    });
  }
}
```

### ngDoCheck

Called during every change detection run. Use sparingly due to performance.

```typescript
import { Component, DoCheck, IterableDiffers, KeyValueDiffers } from '@angular/core';

@Component({...})
export class ItemListComponent implements DoCheck {
  @Input() items: Item[] = [];

  private iterableDiffer: IterableDiffer<Item>;

  constructor(private differs: IterableDiffers) {
    this.iterableDiffer = differs.find([]).create();
  }

  ngDoCheck() {
    const changes = this.iterableDiffer.diff(this.items);

    if (changes) {
      changes.forEachAddedItem(record => {
        console.log('Added:', record.item);
      });

      changes.forEachRemovedItem(record => {
        console.log('Removed:', record.item);
      });

      changes.forEachMovedItem(record => {
        console.log('Moved:', record.item);
      });
    }
  }
}
```

### ngAfterContentInit / ngAfterContentChecked

Called after content projection is complete.

```typescript
import {
  Component,
  AfterContentInit,
  AfterContentChecked,
  ContentChildren,
  QueryList,
} from '@angular/core';

@Component({
  selector: 'app-tab-group',
  template: `
    <div class="tabs">
      <ng-content />
    </div>
  `,
})
export class TabGroupComponent implements AfterContentInit, AfterContentChecked {
  @ContentChildren(TabComponent) tabs!: QueryList<TabComponent>;

  ngAfterContentInit() {
    // Content is now available
    console.log('Number of tabs:', this.tabs.length);

    // Initialize first tab as active
    if (this.tabs.length > 0) {
      this.tabs.first.activate();
    }

    // Watch for tab changes
    this.tabs.changes.subscribe(() => {
      console.log('Tabs changed:', this.tabs.length);
    });
  }

  ngAfterContentChecked() {
    // Called after every content check
    // Use sparingly - runs frequently
  }
}
```

### ngAfterViewInit / ngAfterViewChecked

Called after the component's view and child views are initialized.

```typescript
import {
  Component,
  AfterViewInit,
  ViewChild,
  ElementRef,
  afterNextRender,
  afterRender,
} from '@angular/core';

@Component({
  selector: 'app-chart',
  template: `
    <div #chartContainer class="chart"></div>
  `,
})
export class ChartComponent implements AfterViewInit {
  @ViewChild('chartContainer') container!: ElementRef;

  private chart?: Chart;

  ngAfterViewInit() {
    // DOM is ready, initialize chart
    this.initChart();
  }

  private initChart() {
    this.chart = new Chart(this.container.nativeElement, {
      // chart config
    });
  }
}

// Modern approach with afterNextRender (Angular 16+)
@Component({...})
export class ModernChartComponent {
  @ViewChild('chartContainer') container!: ElementRef;

  constructor() {
    // Runs once after next render
    afterNextRender(() => {
      this.initChart();
    });

    // Runs after every render
    afterRender(() => {
      // Update chart
    });
  }
}
```

### ngOnDestroy

Called just before Angular destroys the component. Use for cleanup.

```typescript
import { Component, OnDestroy, inject, DestroyRef } from '@angular/core';
import { Subscription } from 'rxjs';

// Traditional approach
@Component({...})
export class TraditionalComponent implements OnDestroy {
  private subscriptions: Subscription[] = [];

  ngOnInit() {
    this.subscriptions.push(
      this.service.data$.subscribe(),
      this.service.events$.subscribe()
    );
  }

  ngOnDestroy() {
    // Clean up subscriptions
    this.subscriptions.forEach(sub => sub.unsubscribe());

    // Clean up other resources
    this.cleanup();
  }
}

// Modern approach with DestroyRef
@Component({...})
export class ModernComponent {
  private destroyRef = inject(DestroyRef);

  ngOnInit() {
    const sub1 = this.service.data$.subscribe();
    const sub2 = this.service.events$.subscribe();

    // Register cleanup callbacks
    this.destroyRef.onDestroy(() => {
      sub1.unsubscribe();
      sub2.unsubscribe();
      this.cleanup();
    });
  }
}

// With takeUntilDestroyed
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

@Component({...})
export class BestPracticeComponent {
  private destroyRef = inject(DestroyRef);

  ngOnInit() {
    this.service.data$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(data => {
        // Handle data
      });
  }
}
```

## afterRender and afterNextRender

Angular 16+ provides new hooks for DOM manipulation:

```typescript
import { Component, afterNextRender, afterRender, ElementRef, ViewChild } from '@angular/core';

@Component({
  selector: 'app-animation',
  template: `<div #animated class="box"></div>`,
})
export class AnimationComponent {
  @ViewChild('animated') animatedElement!: ElementRef;

  constructor() {
    // Run once after next render
    afterNextRender(() => {
      // Safe to access DOM
      this.animatedElement.nativeElement.animate([
        { opacity: 0 },
        { opacity: 1 },
      ], { duration: 500 });
    });

    // Run after every render
    afterRender(() => {
      // Update based on current state
    });
  }
}

// With phases for performance
afterRender(() => {
  // Read DOM
}, { phase: AfterRenderPhase.Read });

afterRender(() => {
  // Write to DOM
}, { phase: AfterRenderPhase.Write });
```

## Best Practices

1. **Prefer signals over ngOnChanges**: Use `effect()` for reacting to changes
2. **Use DestroyRef over ngOnDestroy**: Cleaner cleanup registration
3. **Use afterNextRender for DOM access**: SSR-safe DOM manipulation
4. **Avoid heavy work in checked hooks**: `ngDoCheck`, `ngAfterViewChecked`, etc.
5. **Use takeUntilDestroyed**: Automatic subscription cleanup
6. **Keep ngOnInit light**: Move heavy initialization to afterNextRender
7. **Don't modify state in checked hooks**: Causes change detection issues
