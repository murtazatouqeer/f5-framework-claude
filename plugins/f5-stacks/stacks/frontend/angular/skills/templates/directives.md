# Angular Directives

## Overview

Directives add behavior to DOM elements. There are three types: components (with templates), structural directives (change DOM structure), and attribute directives (change appearance/behavior).

## Built-in Attribute Directives

### NgClass

```html
<!-- Single class toggle -->
<div [ngClass]="{'active': isActive}"></div>

<!-- Multiple classes -->
<div [ngClass]="{
  'active': isActive,
  'disabled': isDisabled,
  'highlighted': isHighlighted
}"></div>

<!-- Class array -->
<div [ngClass]="['btn', 'btn-primary']"></div>

<!-- Dynamic class string -->
<div [ngClass]="currentClasses"></div>

<!-- Combined with class binding -->
<div class="base-class" [ngClass]="additionalClasses"></div>
```

### NgStyle

```html
<!-- Single style -->
<div [ngStyle]="{'color': textColor}"></div>

<!-- Multiple styles -->
<div [ngStyle]="{
  'color': textColor,
  'font-size.px': fontSize,
  'background-color': bgColor
}"></div>

<!-- Dynamic styles object -->
<div [ngStyle]="currentStyles"></div>
```

### NgModel (FormsModule)

```html
<!-- Two-way binding -->
<input [(ngModel)]="name">
<select [(ngModel)]="selectedValue">
  <option value="a">Option A</option>
  <option value="b">Option B</option>
</select>

<!-- With events -->
<input
  [ngModel]="name"
  (ngModelChange)="onNameChange($event)"
>
```

## Custom Attribute Directives

### Basic Directive

```typescript
import { Directive, ElementRef, inject } from '@angular/core';

@Directive({
  selector: '[appHighlight]',
  standalone: true,
})
export class HighlightDirective {
  private el = inject(ElementRef);

  constructor() {
    this.el.nativeElement.style.backgroundColor = 'yellow';
  }
}

// Usage
// <p appHighlight>This text is highlighted</p>
```

### Directive with Inputs

```typescript
import { Directive, ElementRef, HostListener, input, effect } from '@angular/core';

@Directive({
  selector: '[appHighlight]',
  standalone: true,
})
export class HighlightDirective {
  private el = inject(ElementRef);

  // Input with directive selector
  appHighlight = input<string>('yellow');
  highlightColor = input<string>('');

  constructor() {
    effect(() => {
      this.el.nativeElement.style.backgroundColor =
        this.appHighlight() || this.highlightColor() || 'yellow';
    });
  }

  @HostListener('mouseenter')
  onMouseEnter() {
    this.el.nativeElement.style.backgroundColor =
      this.appHighlight() || this.highlightColor() || 'yellow';
  }

  @HostListener('mouseleave')
  onMouseLeave() {
    this.el.nativeElement.style.backgroundColor = '';
  }
}

// Usage
// <p appHighlight>Yellow highlight</p>
// <p appHighlight="cyan">Cyan highlight</p>
// <p appHighlight [highlightColor]="color">Dynamic color</p>
```

### Host Binding and Listening

```typescript
import { Directive, HostBinding, HostListener, input, signal } from '@angular/core';

@Directive({
  selector: '[appDropdown]',
  standalone: true,
})
export class DropdownDirective {
  isOpen = signal(false);

  @HostBinding('class.open')
  get openClass() {
    return this.isOpen();
  }

  @HostBinding('attr.aria-expanded')
  get ariaExpanded() {
    return this.isOpen();
  }

  @HostListener('click')
  toggle() {
    this.isOpen.update(v => !v);
  }

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: Event) {
    // Close when clicking outside
    if (!this.el.nativeElement.contains(event.target)) {
      this.isOpen.set(false);
    }
  }

  private el = inject(ElementRef);
}

// Usage
// <div appDropdown>
//   <button>Toggle Dropdown</button>
//   <div class="dropdown-menu">...</div>
// </div>
```

### Directive with host Property

```typescript
@Directive({
  selector: '[appButton]',
  standalone: true,
  host: {
    '[class.btn]': 'true',
    '[class.btn-primary]': 'variant() === "primary"',
    '[class.btn-secondary]': 'variant() === "secondary"',
    '[disabled]': 'disabled()',
    '(click)': 'onClick($event)',
  },
})
export class ButtonDirective {
  variant = input<'primary' | 'secondary'>('primary');
  disabled = input(false);

  onClick(event: Event) {
    if (this.disabled()) {
      event.preventDefault();
      event.stopPropagation();
    }
  }
}
```

### Click Outside Directive

```typescript
import { Directive, ElementRef, output, inject } from '@angular/core';
import { DOCUMENT } from '@angular/common';
import { fromEvent, filter } from 'rxjs';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

@Directive({
  selector: '[appClickOutside]',
  standalone: true,
})
export class ClickOutsideDirective {
  private el = inject(ElementRef);
  private document = inject(DOCUMENT);

  clickOutside = output<Event>();

  constructor() {
    fromEvent<MouseEvent>(this.document, 'click')
      .pipe(
        filter(event => !this.el.nativeElement.contains(event.target)),
        takeUntilDestroyed()
      )
      .subscribe(event => {
        this.clickOutside.emit(event);
      });
  }
}

// Usage
// <div appClickOutside (clickOutside)="close()">
//   <div class="modal">...</div>
// </div>
```

### Tooltip Directive

```typescript
@Directive({
  selector: '[appTooltip]',
  standalone: true,
})
export class TooltipDirective implements OnDestroy {
  private el = inject(ElementRef);
  private renderer = inject(Renderer2);

  appTooltip = input<string>('');
  tooltipPosition = input<'top' | 'bottom' | 'left' | 'right'>('top');

  private tooltipElement?: HTMLElement;

  @HostListener('mouseenter')
  onMouseEnter() {
    this.show();
  }

  @HostListener('mouseleave')
  onMouseLeave() {
    this.hide();
  }

  private show() {
    this.tooltipElement = this.renderer.createElement('div');
    this.renderer.addClass(this.tooltipElement, 'tooltip');
    this.renderer.addClass(this.tooltipElement, `tooltip-${this.tooltipPosition()}`);
    this.renderer.appendChild(
      this.tooltipElement,
      this.renderer.createText(this.appTooltip())
    );
    this.renderer.appendChild(document.body, this.tooltipElement);
    this.setPosition();
  }

  private hide() {
    if (this.tooltipElement) {
      this.renderer.removeChild(document.body, this.tooltipElement);
      this.tooltipElement = undefined;
    }
  }

  private setPosition() {
    // Calculate and set tooltip position
  }

  ngOnDestroy() {
    this.hide();
  }
}

// Usage
// <button appTooltip="Click to save" tooltipPosition="top">Save</button>
```

## Custom Structural Directives

### Basic Structural Directive

```typescript
import { Directive, TemplateRef, ViewContainerRef, input, effect } from '@angular/core';

@Directive({
  selector: '[appIf]',
  standalone: true,
})
export class IfDirective {
  private templateRef = inject(TemplateRef<unknown>);
  private viewContainer = inject(ViewContainerRef);
  private hasView = false;

  appIf = input<boolean>(false);

  constructor() {
    effect(() => {
      if (this.appIf() && !this.hasView) {
        this.viewContainer.createEmbeddedView(this.templateRef);
        this.hasView = true;
      } else if (!this.appIf() && this.hasView) {
        this.viewContainer.clear();
        this.hasView = false;
      }
    });
  }
}

// Usage
// <div *appIf="isVisible">Visible content</div>
```

### Repeat Directive

```typescript
@Directive({
  selector: '[appRepeat]',
  standalone: true,
})
export class RepeatDirective {
  private templateRef = inject(TemplateRef<{ $implicit: number; index: number }>);
  private viewContainer = inject(ViewContainerRef);

  appRepeat = input<number>(0);

  constructor() {
    effect(() => {
      this.viewContainer.clear();

      for (let i = 0; i < this.appRepeat(); i++) {
        this.viewContainer.createEmbeddedView(this.templateRef, {
          $implicit: i + 1,
          index: i,
        });
      }
    });
  }
}

// Usage
// <div *appRepeat="5; let num; let i = index">
//   Item {{ num }} (index: {{ i }})
// </div>
```

### Permission Directive

```typescript
@Directive({
  selector: '[appHasPermission]',
  standalone: true,
})
export class HasPermissionDirective {
  private templateRef = inject(TemplateRef<unknown>);
  private viewContainer = inject(ViewContainerRef);
  private authService = inject(AuthService);
  private hasView = false;

  appHasPermission = input<string | string[]>([]);

  constructor() {
    effect(() => {
      const permissions = this.appHasPermission();
      const permArray = Array.isArray(permissions) ? permissions : [permissions];
      const hasPermission = permArray.every(p =>
        this.authService.hasPermission(p)
      );

      if (hasPermission && !this.hasView) {
        this.viewContainer.createEmbeddedView(this.templateRef);
        this.hasView = true;
      } else if (!hasPermission && this.hasView) {
        this.viewContainer.clear();
        this.hasView = false;
      }
    });
  }
}

// Usage
// <button *appHasPermission="'admin'">Admin Only</button>
// <button *appHasPermission="['edit', 'delete']">Edit/Delete</button>
```

## Directive Composition

```typescript
// Combine multiple directives
@Directive({
  selector: '[appCard]',
  standalone: true,
  hostDirectives: [
    { directive: HoverDirective, inputs: ['hoverClass'] },
    { directive: FocusDirective, outputs: ['focusChange'] },
  ],
})
export class CardDirective {
  // Card-specific logic
}

// Usage
// <div appCard [hoverClass]="'elevated'" (focusChange)="onFocus($event)">
//   Card content
// </div>
```

## Best Practices

1. **Prefer modern Angular syntax**: Use `@if`, `@for` over structural directives
2. **Use host property**: For cleaner host bindings
3. **Inject with inject()**: Modern approach over constructor injection
4. **Use signals**: For reactive directive state
5. **Clean up**: Implement OnDestroy for event listeners
6. **Use Renderer2**: For DOM manipulation (SSR compatible)
7. **Keep directives focused**: Single responsibility
8. **Export directive classes**: For testing
