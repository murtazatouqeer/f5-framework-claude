# Angular Template Syntax

## Overview

Angular templates are HTML enhanced with Angular-specific syntax for data binding, event handling, and DOM manipulation.

## Interpolation

```html
<!-- Basic interpolation -->
<h1>{{ title }}</h1>
<p>Hello, {{ user.name }}!</p>

<!-- With expressions -->
<p>Total: {{ price * quantity }}</p>
<p>{{ isActive ? 'Active' : 'Inactive' }}</p>

<!-- Method calls -->
<p>{{ getFullName() }}</p>
<p>{{ items.length }}</p>

<!-- Pipes -->
<p>{{ date | date:'long' }}</p>
<p>{{ price | currency:'USD' }}</p>
<p>{{ name | uppercase }}</p>
```

## Property Binding

```html
<!-- DOM property binding -->
<img [src]="imageUrl" [alt]="imageAlt">
<button [disabled]="isDisabled">Submit</button>
<input [value]="inputValue">

<!-- Component input binding -->
<app-user-card [user]="currentUser" [showActions]="true" />

<!-- Boolean properties -->
<input [disabled]="isDisabled">
<div [hidden]="!isVisible"></div>

<!-- Object binding -->
<app-config [config]="{ theme: 'dark', language: 'en' }" />
```

## Attribute Binding

```html
<!-- Standard attributes -->
<button [attr.aria-label]="buttonLabel">Click</button>
<table [attr.colspan]="columnSpan"></table>
<a [attr.href]="linkUrl">Link</a>

<!-- Data attributes -->
<div [attr.data-id]="itemId"></div>
<div [attr.data-testid]="'user-' + userId"></div>

<!-- ARIA attributes -->
<button
  [attr.aria-expanded]="isExpanded"
  [attr.aria-controls]="panelId"
>
  Toggle
</button>
```

## Class Binding

```html
<!-- Single class toggle -->
<div [class.active]="isActive"></div>
<div [class.error]="hasError"></div>
<div [class.highlighted]="item.isHighlighted"></div>

<!-- Multiple classes with object -->
<div [class]="{ active: isActive, disabled: isDisabled }"></div>

<!-- Class with ngClass directive -->
<div [ngClass]="{
  'btn': true,
  'btn-primary': variant === 'primary',
  'btn-disabled': disabled
}"></div>

<!-- Dynamic class string -->
<div [class]="getClassNames()"></div>
```

## Style Binding

```html
<!-- Single style property -->
<div [style.color]="textColor"></div>
<div [style.background-color]="bgColor"></div>

<!-- With units -->
<div [style.width.px]="width"></div>
<div [style.height.%]="heightPercent"></div>
<div [style.font-size.rem]="fontSize"></div>

<!-- Multiple styles with object -->
<div [style]="{
  'color': textColor,
  'font-size.px': fontSize,
  'background-color': bgColor
}"></div>

<!-- With ngStyle directive -->
<div [ngStyle]="getStyles()"></div>
```

## Event Binding

```html
<!-- Basic events -->
<button (click)="onClick()">Click me</button>
<input (input)="onInput($event)">
<form (submit)="onSubmit($event)">

<!-- Keyboard events -->
<input (keyup)="onKeyUp($event)">
<input (keyup.enter)="onEnter()">
<input (keydown.escape)="onEscape()">
<input (keydown.control.s)="onSave($event)">

<!-- Mouse events -->
<div (mouseenter)="onMouseEnter()"></div>
<div (mouseleave)="onMouseLeave()"></div>
<div (mousedown)="onMouseDown($event)"></div>

<!-- Focus events -->
<input (focus)="onFocus()" (blur)="onBlur()">

<!-- Custom component events -->
<app-search (search)="onSearch($event)" />
<app-dialog (close)="onDialogClose()" />

<!-- Event with local reference -->
<input #inputRef (keyup.enter)="search(inputRef.value)">
```

### Event Object

```typescript
// In component
onInput(event: Event) {
  const input = event.target as HTMLInputElement;
  console.log(input.value);
}

onClick(event: MouseEvent) {
  console.log(event.clientX, event.clientY);
}

onKeyUp(event: KeyboardEvent) {
  console.log(event.key);
}
```

## Two-Way Binding

```html
<!-- With ngModel (requires FormsModule) -->
<input [(ngModel)]="name">
<textarea [(ngModel)]="description"></textarea>
<select [(ngModel)]="selectedOption">...</select>

<!-- Custom two-way binding (banana-in-a-box) -->
<app-counter [(count)]="counterValue" />
<app-slider [(value)]="sliderValue" />

<!-- Expanded form -->
<input [ngModel]="name" (ngModelChange)="name = $event">
```

## Template Reference Variables

```html
<!-- Reference to DOM element -->
<input #nameInput type="text">
<button (click)="greet(nameInput.value)">Greet</button>

<!-- Reference to directive -->
<form #myForm="ngForm" (submit)="onSubmit(myForm)">
  ...
</form>

<!-- Reference to component -->
<app-player #player></app-player>
<button (click)="player.play()">Play</button>

<!-- Multiple references -->
<input #input1>
<input #input2>
<button (click)="swap(input1, input2)">Swap</button>
```

## Safe Navigation Operator

```html
<!-- Prevent null/undefined errors -->
<p>{{ user?.name }}</p>
<p>{{ user?.address?.city }}</p>
<img [src]="user?.avatar?.url">

<!-- Method calls -->
<p>{{ user?.getDisplayName?.() }}</p>

<!-- In expressions -->
<p>{{ items?.length || 0 }} items</p>
```

## Non-Null Assertion

```html
<!-- Assert non-null (use carefully) -->
<p>{{ user!.name }}</p>
<img [src]="user!.avatar!.url">
```

## Template Expressions Best Practices

```html
<!-- DO: Simple expressions -->
<p>{{ user.name }}</p>
<p>{{ isActive ? 'Active' : 'Inactive' }}</p>

<!-- DON'T: Complex expressions -->
<!-- <p>{{ items.filter(i => i.active).map(i => i.name).join(', ') }}</p> -->

<!-- DO: Use computed signals or methods -->
<p>{{ activeItemNames() }}</p>
```

```typescript
// In component
activeItemNames = computed(() =>
  this.items()
    .filter(i => i.active)
    .map(i => i.name)
    .join(', ')
);
```

## Template Statements

```html
<!-- Single statement -->
<button (click)="save()">Save</button>

<!-- Multiple statements (avoid if possible) -->
<button (click)="save(); close()">Save & Close</button>

<!-- Assignment -->
<button (click)="isOpen = false">Close</button>

<!-- With event data -->
<input (input)="value = $any($event.target).value">
```

## Template Context

```html
<!-- Template input variables -->
@for (item of items; track item.id; let idx = $index, first = $first) {
  <div [class.first]="first">
    {{ idx + 1 }}. {{ item.name }}
  </div>
}

<!-- ng-template context -->
<ng-template #itemTemplate let-item let-index="index">
  <div>{{ index }}: {{ item.name }}</div>
</ng-template>
```

## Best Practices

1. **Keep templates simple**: Move complex logic to component
2. **Use computed signals**: For derived values
3. **Avoid function calls**: Unless memoized or pure
4. **Use safe navigation**: Prevent null errors
5. **Prefer property binding**: Over attribute binding when possible
6. **Use semantic events**: `(click)` over `onclick`
7. **Type event handlers**: For better IDE support
