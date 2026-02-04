# Angular Component Testing

## Overview

Component testing verifies that components render correctly, handle user interactions, and communicate properly with their dependencies.

## Test Setup

### Basic Component Test

```typescript
// components/greeting.component.spec.ts
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { GreetingComponent } from './greeting.component';

describe('GreetingComponent', () => {
  let component: GreetingComponent;
  let fixture: ComponentFixture<GreetingComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [GreetingComponent], // Standalone component
    }).compileComponents();

    fixture = TestBed.createComponent(GreetingComponent);
    component = fixture.componentInstance;
    fixture.detectChanges(); // Trigger initial change detection
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should display greeting message', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('h1')?.textContent).toContain('Hello');
  });
});
```

### Component with Dependencies

```typescript
// components/user-profile.component.spec.ts
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { UserProfileComponent } from './user-profile.component';
import { UserService } from '../services/user.service';
import { of } from 'rxjs';

describe('UserProfileComponent', () => {
  let component: UserProfileComponent;
  let fixture: ComponentFixture<UserProfileComponent>;
  let userService: jasmine.SpyObj<UserService>;

  const mockUser = { id: 1, name: 'John', email: 'john@example.com' };

  beforeEach(async () => {
    userService = jasmine.createSpyObj('UserService', ['getUser']);
    userService.getUser.and.returnValue(of(mockUser));

    await TestBed.configureTestingModule({
      imports: [UserProfileComponent],
      providers: [
        { provide: UserService, useValue: userService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(UserProfileComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should load user on init', () => {
    expect(userService.getUser).toHaveBeenCalled();
    expect(component.user()).toEqual(mockUser);
  });

  it('should display user name', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.user-name')?.textContent).toContain('John');
  });
});
```

## Testing Inputs and Outputs

### Testing Inputs

```typescript
// components/button.component.spec.ts
@Component({
  selector: 'app-button',
  standalone: true,
  template: `
    <button [class]="variant()" [disabled]="disabled()">
      {{ label() }}
    </button>
  `,
})
export class ButtonComponent {
  label = input('Click me');
  variant = input<'primary' | 'secondary'>('primary');
  disabled = input(false);
}

describe('ButtonComponent', () => {
  let fixture: ComponentFixture<ButtonComponent>;
  let component: ButtonComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ButtonComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(ButtonComponent);
    component = fixture.componentInstance;
  });

  it('should have default label', () => {
    fixture.detectChanges();
    const button = fixture.nativeElement.querySelector('button');
    expect(button.textContent).toContain('Click me');
  });

  it('should accept custom label', () => {
    fixture.componentRef.setInput('label', 'Submit');
    fixture.detectChanges();

    const button = fixture.nativeElement.querySelector('button');
    expect(button.textContent).toContain('Submit');
  });

  it('should apply variant class', () => {
    fixture.componentRef.setInput('variant', 'secondary');
    fixture.detectChanges();

    const button = fixture.nativeElement.querySelector('button');
    expect(button.classList.contains('secondary')).toBe(true);
  });

  it('should be disabled when disabled input is true', () => {
    fixture.componentRef.setInput('disabled', true);
    fixture.detectChanges();

    const button = fixture.nativeElement.querySelector('button');
    expect(button.disabled).toBe(true);
  });
});
```

### Testing Outputs

```typescript
// components/counter.component.spec.ts
@Component({
  selector: 'app-counter',
  standalone: true,
  template: `
    <button class="decrement" (click)="decrement()">-</button>
    <span>{{ count() }}</span>
    <button class="increment" (click)="increment()">+</button>
  `,
})
export class CounterComponent {
  count = model(0);
  countChange = output<number>();

  increment() {
    this.count.update(c => c + 1);
    this.countChange.emit(this.count());
  }

  decrement() {
    this.count.update(c => c - 1);
    this.countChange.emit(this.count());
  }
}

describe('CounterComponent', () => {
  let fixture: ComponentFixture<CounterComponent>;
  let component: CounterComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CounterComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(CounterComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should emit countChange on increment', () => {
    const spy = jasmine.createSpy('countChange');
    component.countChange.subscribe(spy);

    const incrementBtn = fixture.nativeElement.querySelector('.increment');
    incrementBtn.click();

    expect(spy).toHaveBeenCalledWith(1);
  });

  it('should emit countChange on decrement', () => {
    const spy = jasmine.createSpy('countChange');
    component.countChange.subscribe(spy);

    const decrementBtn = fixture.nativeElement.querySelector('.decrement');
    decrementBtn.click();

    expect(spy).toHaveBeenCalledWith(-1);
  });
});
```

## Testing User Interactions

### Click Events

```typescript
describe('UserInteractionComponent', () => {
  let fixture: ComponentFixture<UserInteractionComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [UserInteractionComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(UserInteractionComponent);
    fixture.detectChanges();
  });

  it('should handle button click', () => {
    const button = fixture.nativeElement.querySelector('button');
    button.click();
    fixture.detectChanges();

    expect(fixture.componentInstance.clicked()).toBe(true);
  });

  it('should toggle visibility on click', () => {
    const toggleBtn = fixture.nativeElement.querySelector('.toggle');
    const content = () => fixture.nativeElement.querySelector('.content');

    expect(content()).toBeNull();

    toggleBtn.click();
    fixture.detectChanges();
    expect(content()).toBeTruthy();

    toggleBtn.click();
    fixture.detectChanges();
    expect(content()).toBeNull();
  });
});
```

### Form Interactions

```typescript
describe('LoginFormComponent', () => {
  let fixture: ComponentFixture<LoginFormComponent>;
  let component: LoginFormComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LoginFormComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(LoginFormComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should update form values', () => {
    const emailInput = fixture.nativeElement.querySelector('input[name="email"]');
    const passwordInput = fixture.nativeElement.querySelector('input[name="password"]');

    emailInput.value = 'test@example.com';
    emailInput.dispatchEvent(new Event('input'));

    passwordInput.value = 'password123';
    passwordInput.dispatchEvent(new Event('input'));

    fixture.detectChanges();

    expect(component.form.value.email).toBe('test@example.com');
    expect(component.form.value.password).toBe('password123');
  });

  it('should submit form with valid data', () => {
    const submitSpy = spyOn(component, 'onSubmit');

    component.form.setValue({
      email: 'test@example.com',
      password: 'password123',
    });

    const form = fixture.nativeElement.querySelector('form');
    form.dispatchEvent(new Event('submit'));

    expect(submitSpy).toHaveBeenCalled();
  });

  it('should show validation errors', () => {
    component.form.controls.email.markAsTouched();
    fixture.detectChanges();

    const errorMessage = fixture.nativeElement.querySelector('.error-message');
    expect(errorMessage?.textContent).toContain('Email is required');
  });
});
```

## Testing Conditional Rendering

```typescript
@Component({
  template: `
    @if (isLoading()) {
      <div class="loading">Loading...</div>
    } @else if (error()) {
      <div class="error">{{ error() }}</div>
    } @else {
      <div class="content">{{ data() }}</div>
    }
  `,
})
export class DataDisplayComponent {
  isLoading = signal(false);
  error = signal<string | null>(null);
  data = signal<string | null>(null);
}

describe('DataDisplayComponent', () => {
  let fixture: ComponentFixture<DataDisplayComponent>;
  let component: DataDisplayComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DataDisplayComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(DataDisplayComponent);
    component = fixture.componentInstance;
  });

  it('should show loading state', () => {
    component.isLoading.set(true);
    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector('.loading')).toBeTruthy();
    expect(fixture.nativeElement.querySelector('.content')).toBeNull();
  });

  it('should show error state', () => {
    component.error.set('Something went wrong');
    fixture.detectChanges();

    const errorEl = fixture.nativeElement.querySelector('.error');
    expect(errorEl?.textContent).toContain('Something went wrong');
  });

  it('should show content when data loaded', () => {
    component.data.set('Hello World');
    fixture.detectChanges();

    const contentEl = fixture.nativeElement.querySelector('.content');
    expect(contentEl?.textContent).toContain('Hello World');
  });
});
```

## Testing Lists

```typescript
@Component({
  template: `
    <ul>
      @for (item of items(); track item.id) {
        <li class="item">{{ item.name }}</li>
      } @empty {
        <li class="empty">No items</li>
      }
    </ul>
  `,
})
export class ItemListComponent {
  items = input<Item[]>([]);
}

describe('ItemListComponent', () => {
  let fixture: ComponentFixture<ItemListComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ItemListComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(ItemListComponent);
  });

  it('should display items', () => {
    const items = [
      { id: 1, name: 'Item 1' },
      { id: 2, name: 'Item 2' },
      { id: 3, name: 'Item 3' },
    ];

    fixture.componentRef.setInput('items', items);
    fixture.detectChanges();

    const listItems = fixture.nativeElement.querySelectorAll('.item');
    expect(listItems.length).toBe(3);
    expect(listItems[0].textContent).toContain('Item 1');
  });

  it('should show empty state when no items', () => {
    fixture.componentRef.setInput('items', []);
    fixture.detectChanges();

    const emptyEl = fixture.nativeElement.querySelector('.empty');
    expect(emptyEl?.textContent).toContain('No items');
  });
});
```

## Testing with Router

```typescript
// components/navigation.component.spec.ts
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { Router } from '@angular/router';
import { NavigationComponent } from './navigation.component';

describe('NavigationComponent', () => {
  let fixture: ComponentFixture<NavigationComponent>;
  let router: Router;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        NavigationComponent,
        RouterTestingModule.withRoutes([
          { path: 'home', component: {} as any },
          { path: 'about', component: {} as any },
        ]),
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(NavigationComponent);
    router = TestBed.inject(Router);
    fixture.detectChanges();
  });

  it('should navigate to home', async () => {
    const homeLink = fixture.nativeElement.querySelector('a[routerLink="/home"]');
    homeLink.click();

    await fixture.whenStable();

    expect(router.url).toBe('/home');
  });

  it('should have active class on current route', async () => {
    await router.navigate(['/about']);
    fixture.detectChanges();

    const aboutLink = fixture.nativeElement.querySelector('a[routerLink="/about"]');
    expect(aboutLink.classList.contains('active')).toBe(true);
  });
});
```

## Testing Child Components

### With Component Stubs

```typescript
// Create stub component
@Component({
  selector: 'app-child',
  standalone: true,
  template: '<div>Stub Child</div>',
})
class ChildComponentStub {
  data = input<any>();
  onAction = output<void>();
}

describe('ParentComponent', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ParentComponent],
    })
      .overrideComponent(ParentComponent, {
        remove: { imports: [ChildComponent] },
        add: { imports: [ChildComponentStub] },
      })
      .compileComponents();
  });

  it('should render child component', () => {
    const fixture = TestBed.createComponent(ParentComponent);
    fixture.detectChanges();

    const childEl = fixture.nativeElement.querySelector('app-child');
    expect(childEl).toBeTruthy();
  });
});
```

### Testing Child Component Interactions

```typescript
describe('ParentComponent with real child', () => {
  let fixture: ComponentFixture<ParentComponent>;
  let childDebugEl: DebugElement;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ParentComponent, ChildComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(ParentComponent);
    fixture.detectChanges();

    childDebugEl = fixture.debugElement.query(By.directive(ChildComponent));
  });

  it('should pass data to child', () => {
    const childComponent = childDebugEl.componentInstance as ChildComponent;
    expect(childComponent.data()).toBeTruthy();
  });

  it('should handle child output', () => {
    const parentComponent = fixture.componentInstance;
    spyOn(parentComponent, 'handleChildAction');

    const childComponent = childDebugEl.componentInstance as ChildComponent;
    childComponent.onAction.emit();

    expect(parentComponent.handleChildAction).toHaveBeenCalled();
  });
});
```

## Debugging Tests

```typescript
describe('Debugging', () => {
  it('should help with debugging', () => {
    fixture.detectChanges();

    // Print HTML
    console.log(fixture.nativeElement.innerHTML);

    // Query with DebugElement
    const debugEl = fixture.debugElement.query(By.css('.my-class'));
    console.log(debugEl.nativeElement);

    // Check component state
    console.log(component.someSignal());

    // Use fixture.debugElement for better debugging
    const allButtons = fixture.debugElement.queryAll(By.css('button'));
    console.log('Button count:', allButtons.length);
  });
});
```

## Best Practices

1. **Test component behavior**: Not implementation details
2. **Use fixture.detectChanges()**: After changes that affect the view
3. **Query by role/test-id**: Not by CSS classes that might change
4. **Mock dependencies**: Keep tests focused on the component
5. **Test user interactions**: Click, input, form submission
6. **Test all states**: Loading, error, empty, success
7. **Use async utilities**: fakeAsync, waitForAsync for async code
8. **Keep tests isolated**: Each test should be independent
