# Angular Directive Template

## Attribute Directive

```typescript
// shared/directives/{{name}}.directive.ts
import { Directive, ElementRef, inject, input, effect } from '@angular/core';

@Directive({
  selector: '[app{{PascalName}}]',
  standalone: true,
})
export class {{PascalName}}Directive {
  private el = inject(ElementRef);

  // Input with signal
  color = input<string>('blue');

  constructor() {
    effect(() => {
      this.el.nativeElement.style.color = this.color();
    });
  }
}

// Usage: <p appHighlight [color]="'red'">Text</p>
```

## Highlight Directive

```typescript
// shared/directives/highlight.directive.ts
import {
  Directive,
  ElementRef,
  HostListener,
  inject,
  input,
  signal,
} from '@angular/core';

@Directive({
  selector: '[appHighlight]',
  standalone: true,
})
export class HighlightDirective {
  private el = inject(ElementRef);

  highlightColor = input<string>('yellow');
  defaultColor = input<string>('transparent');

  private isHighlighted = signal(false);

  @HostListener('mouseenter')
  onMouseEnter() {
    this.highlight(this.highlightColor());
    this.isHighlighted.set(true);
  }

  @HostListener('mouseleave')
  onMouseLeave() {
    this.highlight(this.defaultColor());
    this.isHighlighted.set(false);
  }

  private highlight(color: string) {
    this.el.nativeElement.style.backgroundColor = color;
  }
}

// Usage: <div appHighlight [highlightColor]="'lightblue'">Hover me</div>
```

## Tooltip Directive

```typescript
// shared/directives/tooltip.directive.ts
import {
  Directive,
  ElementRef,
  HostListener,
  inject,
  input,
  Renderer2,
  OnDestroy,
} from '@angular/core';

@Directive({
  selector: '[appTooltip]',
  standalone: true,
})
export class TooltipDirective implements OnDestroy {
  private el = inject(ElementRef);
  private renderer = inject(Renderer2);

  appTooltip = input.required<string>();
  position = input<'top' | 'bottom' | 'left' | 'right'>('top');

  private tooltipElement: HTMLElement | null = null;

  @HostListener('mouseenter')
  onMouseEnter() {
    this.showTooltip();
  }

  @HostListener('mouseleave')
  onMouseLeave() {
    this.hideTooltip();
  }

  private showTooltip() {
    if (this.tooltipElement) return;

    this.tooltipElement = this.renderer.createElement('div');
    this.renderer.appendChild(
      this.tooltipElement,
      this.renderer.createText(this.appTooltip())
    );
    this.renderer.addClass(this.tooltipElement, 'tooltip');
    this.renderer.addClass(this.tooltipElement, `tooltip-${this.position()}`);

    this.renderer.appendChild(document.body, this.tooltipElement);
    this.setPosition();
  }

  private hideTooltip() {
    if (this.tooltipElement) {
      this.renderer.removeChild(document.body, this.tooltipElement);
      this.tooltipElement = null;
    }
  }

  private setPosition() {
    if (!this.tooltipElement) return;

    const hostRect = this.el.nativeElement.getBoundingClientRect();
    const tooltipRect = this.tooltipElement.getBoundingClientRect();

    let top: number;
    let left: number;

    switch (this.position()) {
      case 'top':
        top = hostRect.top - tooltipRect.height - 8;
        left = hostRect.left + (hostRect.width - tooltipRect.width) / 2;
        break;
      case 'bottom':
        top = hostRect.bottom + 8;
        left = hostRect.left + (hostRect.width - tooltipRect.width) / 2;
        break;
      case 'left':
        top = hostRect.top + (hostRect.height - tooltipRect.height) / 2;
        left = hostRect.left - tooltipRect.width - 8;
        break;
      case 'right':
        top = hostRect.top + (hostRect.height - tooltipRect.height) / 2;
        left = hostRect.right + 8;
        break;
    }

    this.renderer.setStyle(this.tooltipElement, 'top', `${top}px`);
    this.renderer.setStyle(this.tooltipElement, 'left', `${left}px`);
  }

  ngOnDestroy() {
    this.hideTooltip();
  }
}

// Usage: <button [appTooltip]="'Click to submit'" [position]="'top'">Submit</button>
```

## Click Outside Directive

```typescript
// shared/directives/click-outside.directive.ts
import {
  Directive,
  ElementRef,
  inject,
  output,
  OnInit,
  OnDestroy,
  NgZone,
} from '@angular/core';

@Directive({
  selector: '[appClickOutside]',
  standalone: true,
})
export class ClickOutsideDirective implements OnInit, OnDestroy {
  private el = inject(ElementRef);
  private ngZone = inject(NgZone);

  clickOutside = output<MouseEvent>();

  private listener: ((event: MouseEvent) => void) | null = null;

  ngOnInit() {
    // Run outside Angular zone for performance
    this.ngZone.runOutsideAngular(() => {
      this.listener = (event: MouseEvent) => {
        if (!this.el.nativeElement.contains(event.target)) {
          // Run callback inside Angular zone
          this.ngZone.run(() => {
            this.clickOutside.emit(event);
          });
        }
      };
      document.addEventListener('click', this.listener, true);
    });
  }

  ngOnDestroy() {
    if (this.listener) {
      document.removeEventListener('click', this.listener, true);
    }
  }
}

// Usage: <div appClickOutside (clickOutside)="closeDropdown()">...</div>
```

## Auto Focus Directive

```typescript
// shared/directives/auto-focus.directive.ts
import {
  Directive,
  ElementRef,
  inject,
  input,
  AfterViewInit,
} from '@angular/core';

@Directive({
  selector: '[appAutoFocus]',
  standalone: true,
})
export class AutoFocusDirective implements AfterViewInit {
  private el = inject(ElementRef);

  appAutoFocus = input<boolean>(true);
  delay = input<number>(0);

  ngAfterViewInit() {
    if (this.appAutoFocus()) {
      setTimeout(() => {
        this.el.nativeElement.focus();
      }, this.delay());
    }
  }
}

// Usage: <input appAutoFocus />
// Usage: <input [appAutoFocus]="shouldFocus" [delay]="100" />
```

## Debounce Click Directive

```typescript
// shared/directives/debounce-click.directive.ts
import {
  Directive,
  HostListener,
  input,
  output,
  OnDestroy,
} from '@angular/core';
import { Subject, debounceTime, Subscription } from 'rxjs';

@Directive({
  selector: '[appDebounceClick]',
  standalone: true,
})
export class DebounceClickDirective implements OnDestroy {
  debounceTime = input<number>(300);
  debounceClick = output<MouseEvent>();

  private clicks$ = new Subject<MouseEvent>();
  private subscription: Subscription;

  constructor() {
    this.subscription = this.clicks$
      .pipe(debounceTime(this.debounceTime()))
      .subscribe(event => this.debounceClick.emit(event));
  }

  @HostListener('click', ['$event'])
  onClick(event: MouseEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.clicks$.next(event);
  }

  ngOnDestroy() {
    this.subscription.unsubscribe();
  }
}

// Usage: <button appDebounceClick (debounceClick)="submit()">Submit</button>
```

## Copy to Clipboard Directive

```typescript
// shared/directives/copy-clipboard.directive.ts
import { Directive, HostListener, input, output } from '@angular/core';

@Directive({
  selector: '[appCopyClipboard]',
  standalone: true,
})
export class CopyClipboardDirective {
  appCopyClipboard = input.required<string>();

  copied = output<boolean>();

  @HostListener('click')
  async onClick() {
    try {
      await navigator.clipboard.writeText(this.appCopyClipboard());
      this.copied.emit(true);
    } catch (err) {
      console.error('Failed to copy:', err);
      this.copied.emit(false);
    }
  }
}

// Usage: <button [appCopyClipboard]="textToCopy" (copied)="onCopied($event)">Copy</button>
```

## Lazy Load Image Directive

```typescript
// shared/directives/lazy-load.directive.ts
import {
  Directive,
  ElementRef,
  inject,
  input,
  OnInit,
  OnDestroy,
  Renderer2,
} from '@angular/core';

@Directive({
  selector: '[appLazyLoad]',
  standalone: true,
})
export class LazyLoadDirective implements OnInit, OnDestroy {
  private el = inject(ElementRef);
  private renderer = inject(Renderer2);

  appLazyLoad = input.required<string>();
  placeholder = input<string>('assets/placeholder.png');

  private observer: IntersectionObserver | null = null;

  ngOnInit() {
    // Set placeholder
    this.renderer.setAttribute(
      this.el.nativeElement,
      'src',
      this.placeholder()
    );

    this.observer = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            this.loadImage();
          }
        });
      },
      { threshold: 0.1 }
    );

    this.observer.observe(this.el.nativeElement);
  }

  private loadImage() {
    this.renderer.setAttribute(
      this.el.nativeElement,
      'src',
      this.appLazyLoad()
    );
    this.observer?.unobserve(this.el.nativeElement);
  }

  ngOnDestroy() {
    this.observer?.disconnect();
  }
}

// Usage: <img [appLazyLoad]="imageUrl" [placeholder]="'loading.gif'" />
```

## Permission Directive

```typescript
// shared/directives/permission.directive.ts
import {
  Directive,
  inject,
  input,
  TemplateRef,
  ViewContainerRef,
  effect,
} from '@angular/core';
import { PermissionService } from '../../core/services/permission.service';

@Directive({
  selector: '[appHasPermission]',
  standalone: true,
})
export class HasPermissionDirective {
  private templateRef = inject(TemplateRef<any>);
  private viewContainer = inject(ViewContainerRef);
  private permissionService = inject(PermissionService);

  appHasPermission = input.required<string | string[]>();

  private hasView = false;

  constructor() {
    effect(() => {
      const permissions = this.appHasPermission();
      const hasPermission = Array.isArray(permissions)
        ? permissions.some(p => this.permissionService.hasPermission(p))
        : this.permissionService.hasPermission(permissions);

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

// Usage: <button *appHasPermission="'users.delete'">Delete User</button>
// Usage: <div *appHasPermission="['admin', 'moderator']">Admin Panel</div>
```

## Structural Directive (Custom *ngIf)

```typescript
// shared/directives/let.directive.ts
import {
  Directive,
  inject,
  input,
  TemplateRef,
  ViewContainerRef,
  effect,
} from '@angular/core';

interface LetContext<T> {
  appLet: T;
  $implicit: T;
}

@Directive({
  selector: '[appLet]',
  standalone: true,
})
export class LetDirective<T> {
  private templateRef = inject(TemplateRef<LetContext<T>>);
  private viewContainer = inject(ViewContainerRef);

  appLet = input.required<T>();

  private viewRef: any = null;

  constructor() {
    effect(() => {
      const value = this.appLet();

      if (!this.viewRef) {
        this.viewRef = this.viewContainer.createEmbeddedView(this.templateRef, {
          appLet: value,
          $implicit: value,
        });
      } else {
        this.viewRef.context.appLet = value;
        this.viewRef.context.$implicit = value;
      }
    });
  }

  static ngTemplateContextGuard<T>(
    dir: LetDirective<T>,
    ctx: unknown
  ): ctx is LetContext<T> {
    return true;
  }
}

// Usage: <ng-container *appLet="user$ | async as user">{{ user.name }}</ng-container>
```

## Resize Observer Directive

```typescript
// shared/directives/resize-observer.directive.ts
import {
  Directive,
  ElementRef,
  inject,
  output,
  OnInit,
  OnDestroy,
  NgZone,
} from '@angular/core';

export interface ResizeEvent {
  width: number;
  height: number;
  entry: ResizeObserverEntry;
}

@Directive({
  selector: '[appResizeObserver]',
  standalone: true,
})
export class ResizeObserverDirective implements OnInit, OnDestroy {
  private el = inject(ElementRef);
  private ngZone = inject(NgZone);

  resized = output<ResizeEvent>();

  private observer: ResizeObserver | null = null;

  ngOnInit() {
    this.ngZone.runOutsideAngular(() => {
      this.observer = new ResizeObserver((entries) => {
        const entry = entries[0];
        if (entry) {
          this.ngZone.run(() => {
            this.resized.emit({
              width: entry.contentRect.width,
              height: entry.contentRect.height,
              entry,
            });
          });
        }
      });

      this.observer.observe(this.el.nativeElement);
    });
  }

  ngOnDestroy() {
    this.observer?.disconnect();
  }
}

// Usage: <div appResizeObserver (resized)="onResize($event)">...</div>
```

## Input Mask Directive

```typescript
// shared/directives/input-mask.directive.ts
import {
  Directive,
  ElementRef,
  HostListener,
  inject,
  input,
  forwardRef,
} from '@angular/core';
import { NG_VALUE_ACCESSOR, ControlValueAccessor } from '@angular/forms';

@Directive({
  selector: '[appInputMask]',
  standalone: true,
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => InputMaskDirective),
      multi: true,
    },
  ],
})
export class InputMaskDirective implements ControlValueAccessor {
  private el = inject(ElementRef);

  // Mask pattern: 9 = digit, A = letter, * = alphanumeric
  appInputMask = input.required<string>();

  private onChange: (value: string) => void = () => {};
  private onTouched: () => void = () => {};

  @HostListener('input', ['$event.target.value'])
  onInput(value: string) {
    const masked = this.applyMask(value);
    this.el.nativeElement.value = masked;
    this.onChange(this.unmask(masked));
  }

  @HostListener('blur')
  onBlur() {
    this.onTouched();
  }

  writeValue(value: string): void {
    this.el.nativeElement.value = value ? this.applyMask(value) : '';
  }

  registerOnChange(fn: (value: string) => void): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }

  private applyMask(value: string): string {
    const mask = this.appInputMask();
    const rawValue = value.replace(/\D/g, '');
    let result = '';
    let valueIndex = 0;

    for (let i = 0; i < mask.length && valueIndex < rawValue.length; i++) {
      if (mask[i] === '9') {
        result += rawValue[valueIndex++];
      } else {
        result += mask[i];
        if (rawValue[valueIndex] === mask[i]) {
          valueIndex++;
        }
      }
    }

    return result;
  }

  private unmask(value: string): string {
    return value.replace(/\D/g, '');
  }
}

// Usage: <input [appInputMask]="'(999) 999-9999'" formControlName="phone" />
```

## Directive Barrel Export

```typescript
// shared/directives/index.ts
export * from './highlight.directive';
export * from './tooltip.directive';
export * from './click-outside.directive';
export * from './auto-focus.directive';
export * from './debounce-click.directive';
export * from './copy-clipboard.directive';
export * from './lazy-load.directive';
export * from './permission.directive';
export * from './let.directive';
export * from './resize-observer.directive';
export * from './input-mask.directive';
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{name}}` | kebab-case name | `click-outside` |
| `{{PascalName}}` | PascalCase name | `ClickOutside` |
