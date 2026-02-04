# Angular Change Detection

## Overview

Angular's change detection system determines when to update the DOM based on changes in component data. Understanding and optimizing change detection is crucial for application performance.

## Change Detection Strategies

### Default Strategy

```typescript
// Default: checks all bindings on every change detection cycle
@Component({
  selector: 'app-default',
  template: `<p>{{ value }}</p>`,
  changeDetection: ChangeDetectionStrategy.Default,
})
export class DefaultComponent {
  value = 'Hello';
}
```

### OnPush Strategy

```typescript
// OnPush: only checks when inputs change, events fire, or explicitly triggered
@Component({
  selector: 'app-on-push',
  template: `
    <p>{{ data().name }}</p>
    <button (click)="onClick()">Click</button>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class OnPushComponent {
  data = input<{ name: string }>({ name: 'Default' });

  onClick() {
    // Events in OnPush components trigger change detection
    console.log('Clicked');
  }
}
```

## OnPush Triggers

OnPush change detection runs when:

1. **Input reference changes**
2. **DOM events from the component or children**
3. **Async pipe receives new value**
4. **Signals update**
5. **markForCheck() or detectChanges() called**

### Input Changes

```typescript
// Parent component
@Component({
  template: `
    <app-child [user]="user()" />
    <button (click)="updateUser()">Update</button>
  `,
})
export class ParentComponent {
  user = signal({ name: 'John', age: 30 });

  updateUser() {
    // This triggers change detection in child
    this.user.set({ name: 'Jane', age: 25 });
  }

  // This won't trigger child change detection (same reference)
  updateUserWrong() {
    this.user().name = 'Jane'; // Mutation - won't work with OnPush
  }
}

// Child with OnPush
@Component({
  selector: 'app-child',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `<p>{{ user().name }}</p>`,
})
export class ChildComponent {
  user = input.required<{ name: string; age: number }>();
}
```

### DOM Events

```typescript
@Component({
  selector: 'app-counter',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <p>Count: {{ count }}</p>
    <button (click)="increment()">+</button>
  `,
})
export class CounterComponent {
  count = 0;

  increment() {
    // Event binding triggers change detection automatically
    this.count++;
  }
}
```

### Async Pipe

```typescript
@Component({
  selector: 'app-user-list',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (users$ | async; as users) {
      @for (user of users; track user.id) {
        <div>{{ user.name }}</div>
      }
    }
  `,
})
export class UserListComponent {
  private http = inject(HttpClient);

  users$ = this.http.get<User[]>('/api/users');
}
```

### Signals (Angular 17+)

```typescript
@Component({
  selector: 'app-signal-demo',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <p>Count: {{ count() }}</p>
    <p>Double: {{ doubleCount() }}</p>
  `,
})
export class SignalDemoComponent {
  count = signal(0);
  doubleCount = computed(() => this.count() * 2);

  increment() {
    // Signal updates automatically trigger change detection
    this.count.update(c => c + 1);
  }
}
```

## Manual Change Detection

### ChangeDetectorRef

```typescript
@Component({
  selector: 'app-manual-detection',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `<p>{{ value }}</p>`,
})
export class ManualDetectionComponent {
  private cdr = inject(ChangeDetectorRef);

  value = 'initial';

  updateValue() {
    this.value = 'updated';
    // Manually trigger change detection
    this.cdr.markForCheck();
  }

  // Or detect changes immediately
  updateValueImmediate() {
    this.value = 'updated';
    this.cdr.detectChanges();
  }

  // Detach from change detection tree
  detach() {
    this.cdr.detach();
  }

  // Reattach to change detection tree
  reattach() {
    this.cdr.reattach();
  }
}
```

### markForCheck vs detectChanges

```typescript
@Component({
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ChangeDetectionComponent {
  private cdr = inject(ChangeDetectorRef);

  // markForCheck: marks component and ancestors for check in next cycle
  useMarkForCheck() {
    this.data = newData;
    this.cdr.markForCheck(); // Checked in next tick
  }

  // detectChanges: runs change detection immediately
  useDetectChanges() {
    this.data = newData;
    this.cdr.detectChanges(); // Checked immediately, synchronous
  }
}
```

## Zone.js and NgZone

### Running Outside Zone

```typescript
@Component({...})
export class AnimationComponent {
  private ngZone = inject(NgZone);

  startAnimation() {
    // Run outside Angular zone to avoid change detection
    this.ngZone.runOutsideAngular(() => {
      requestAnimationFrame(this.animate.bind(this));
    });
  }

  private animate() {
    // Animation logic here - no change detection triggered
    if (this.isAnimating) {
      requestAnimationFrame(this.animate.bind(this));
    }
  }

  finishAnimation() {
    // Run inside zone when you need to update the view
    this.ngZone.run(() => {
      this.animationComplete = true;
    });
  }
}
```

### Heavy Operations Outside Zone

```typescript
@Injectable({ providedIn: 'root' })
export class HeavyComputationService {
  private ngZone = inject(NgZone);

  computeData(data: number[]): Promise<number> {
    return new Promise(resolve => {
      this.ngZone.runOutsideAngular(() => {
        // Heavy computation without triggering change detection
        const result = data.reduce((sum, n) => sum + Math.sqrt(n), 0);
        resolve(result);
      });
    });
  }
}
```

## Zoneless Applications (Angular 18+)

```typescript
// app.config.ts
import { ApplicationConfig } from '@angular/core';
import { provideExperimentalZonelessChangeDetection } from '@angular/core';

export const appConfig: ApplicationConfig = {
  providers: [
    provideExperimentalZonelessChangeDetection(),
  ],
};

// Components must use signals or explicit change detection
@Component({
  selector: 'app-zoneless',
  template: `
    <p>Count: {{ count() }}</p>
    <button (click)="increment()">+</button>
  `,
})
export class ZonelessComponent {
  count = signal(0);

  increment() {
    // Signals work automatically in zoneless mode
    this.count.update(c => c + 1);
  }
}
```

## Performance Patterns

### Immutable Data

```typescript
@Component({
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ImmutableComponent {
  items = signal<Item[]>([]);

  // Good: Create new array reference
  addItem(item: Item) {
    this.items.update(current => [...current, item]);
  }

  // Good: Create new object reference
  updateItem(id: number, changes: Partial<Item>) {
    this.items.update(current =>
      current.map(item =>
        item.id === id ? { ...item, ...changes } : item
      )
    );
  }

  // Bad: Mutation (won't trigger OnPush change detection)
  addItemWrong(item: Item) {
    this.items().push(item); // Don't do this!
  }
}
```

### trackBy in @for

```typescript
@Component({
  template: `
    @for (item of items(); track item.id) {
      <app-item [item]="item" />
    }
  `,
})
export class TrackByComponent {
  items = signal<Item[]>([]);
}

// Or with index
@Component({
  template: `
    @for (item of items(); track $index) {
      <app-item [item]="item" />
    }
  `,
})
export class TrackByIndexComponent {}
```

### Reducing Bindings

```typescript
// Bad: Multiple bindings to same expression
@Component({
  template: `
    <p>{{ expensiveCalculation() }}</p>
    <span>{{ expensiveCalculation() }}</span>
  `,
})
export class MultipleBadComponent {}

// Good: Use computed signal
@Component({
  template: `
    <p>{{ result() }}</p>
    <span>{{ result() }}</span>
  `,
})
export class ComputedGoodComponent {
  result = computed(() => this.expensiveCalculation());

  private expensiveCalculation() {
    // Called only once per change
    return /* expensive operation */;
  }
}
```

### Pure Pipes

```typescript
// Pure pipes are cached by input
@Pipe({
  name: 'expensive',
  standalone: true,
  pure: true, // Default - cached by input
})
export class ExpensivePipe implements PipeTransform {
  transform(value: number): number {
    return /* expensive calculation */;
  }
}

// Impure pipes run on every change detection
@Pipe({
  name: 'impure',
  standalone: true,
  pure: false, // Runs every cycle - use sparingly
})
export class ImpurePipe implements PipeTransform {
  transform(value: any): any {
    return /* always recalculated */;
  }
}
```

## Debugging Change Detection

```typescript
// Enable debugging in development
import { enableDebugTools } from '@angular/platform-browser';

platformBrowserDynamic().bootstrapModule(AppModule)
  .then(moduleRef => {
    const appRef = moduleRef.injector.get(ApplicationRef);
    const componentRef = appRef.components[0];
    enableDebugTools(componentRef);
  });

// In browser console:
// ng.profiler.timeChangeDetection()
```

### Component Lifecycle Logging

```typescript
@Component({...})
export class DebugComponent implements DoCheck {
  private checkCount = 0;

  ngDoCheck() {
    this.checkCount++;
    console.log(`Change detection run: ${this.checkCount}`);
  }
}
```

## Best Practices

1. **Use OnPush by default**: Better performance, clearer data flow
2. **Prefer signals over mutable state**: Automatic change detection
3. **Use immutable data patterns**: Create new references
4. **Run heavy operations outside zone**: Use ngZone.runOutsideAngular
5. **Use trackBy in loops**: Minimize DOM updates
6. **Cache computed values**: Use computed signals or memoization
7. **Use pure pipes**: For deterministic transformations
8. **Consider zoneless**: For maximum performance control
